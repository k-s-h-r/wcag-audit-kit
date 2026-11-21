"""Replay the recorded chart assessment into copies of the two saved page audits."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


def invoke(cli, *args):
    result = subprocess.run([sys.executable, str(cli), *map(str, args)], check=True,
                            text=True, capture_output=True)
    return result.stdout.strip()


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def chart_readings(path):
    readings = {}
    for line in path.read_text().splitlines():
        if not line.startswith('| `http'):
            continue
        url, _, unit, april, may, june, trend = [cell.strip() for cell in line.strip('|').split('|')]
        assert unit == 'Count of visits（訪問回数）' and trend.startswith('毎月減少。')
        readings[url.strip('`')] = {
            'Apr': int(april), 'May': int(may), 'Jun': int(june),
            'unit': 'visits', 'unit_direction': 'decreases',
        }
    return readings


def check_keyboard(page):
    before, focus, opened = (page[key] for key in ('before', 'afterTab', 'afterEnter'))
    assert (before['activeTag'], before['detailsOpen']) == ('body', [False])
    assert (focus['activeTag'], focus['detailsOpen']) == ('summary', [False])
    assert (opened['activeTag'], opened['detailsOpen']) == ('summary', [True])
    assert focus['focusedName'] == opened['focusedName'] == 'Show data table'
    assert all(key['isTrusted'] for key in page['keys'])
    assert [(key['type'], key['key'], key['target']) for key in page['keys']] == [
        ('keydown', 'Tab', 'body'), ('keyup', 'Tab', 'summary'),
        ('keydown', 'Enter', 'summary'), ('keyup', 'Enter', 'summary'),
    ]


def check_machine_capture(original, case, viewport, browser, initial_image):
    run = json.loads((original / 'work' / 'run.json').read_text())
    config = run['config']
    desktop = next(env for env in config['environments'] if env['id'] == case['environment'])
    assert desktop['viewport'] == viewport and desktop['zoom'] == 1
    capture = original / 'work' / case['evidence_dir']
    inventory = json.loads((capture / 'inventory.json').read_text())
    axe = json.loads((capture / 'axe.json').read_text())
    assert inventory['viewport'] == viewport
    assert inventory['url'] == axe['url'] == config['url'] == case['page_url']
    assert digest(capture / 'page.png') == digest(initial_image)
    user_agent = axe['testEnvironment']['userAgent']
    assert re.search(rf'\b(?:Headless)?Chrome/{re.escape(browser.split(".")[0])}\.', user_agent)
    assert any(rule['id'] == 'image-alt' for rule in axe['passes'])


def record(cli, source, output, evidence, expected):
    output.mkdir(parents=True, exist_ok=False)
    observations = json.loads((evidence / 'observations.json').read_text())
    reply = json.loads((evidence / 'agent-results.json').read_text())
    captures = json.loads((evidence / 'image-captures.json').read_text())
    assert captures['viewport'] == observations['viewport']
    assert captures['browser'] == observations['browser']
    assert digest(evidence / 'visual-reading.md') == observations['visualReadingSha256']
    assert digest(evidence / 'response.txt') == reply['response_sha256']
    readings = chart_readings(evidence / 'visual-reading.md')
    assert {page['origin'] for page in observations['pages']} == set(readings)
    receipts = []
    for page in observations['pages']:
        url = page['origin']
        name = url.rstrip('/').rsplit('/', 1)[-1]
        measured = readings[url]
        assert measured == expected['chart']
        images = next(row['images'] for row in captures['pages'] if row['url'] == url)
        chart, marker = [item['file'] for item in images]
        assert all(digest(evidence / item['file']) == item['sha256'] for item in images)
        control = expected['expectations'][name]
        result = reply['pages'][name]
        assert result['chart'] == control['chart'] and result['decoration'] == control['decoration']
        original = source / name
        copied = output / name
        shutil.copytree(original, copied)
        hashes = {path.relative_to(original): digest(path) for path in original.rglob('*') if path.is_file()}
        plan = json.loads((copied / 'work' / 'plan.json').read_text())
        case = next(row for row in plan['cases']
                    if row['criterion'] == '1.1.1' and row['page_url'] == url
                    and row['environment'] == 'desktop' and row['state'] == 'initial')
        check_machine_capture(copied, case, observations['viewport'], observations['browser'],
                              evidence / page['before']['image'])
        case_id = case['case_id']
        info = json.loads(invoke(cli, 'case', '--run', copied, '--id', case_id))
        assert case['assessment'] is None
        check_keyboard(page)
        rows = page['visibleTables'][0]['rows']
        assert rows[0] == ['Month', 'Visits'] and [row[0] for row in rows[1:]] == ['Apr', 'May', 'Jun']
        table = {month: int(value) for month, value in rows[1:]}
        assert table == {key: measured[key] if key != 'May' else control['detailMay'] for key in ('Apr', 'May', 'Jun')}
        assert all(table[key] == measured[key] for key in table) == (result['chart'] == 'passed')
        common = ['observations.json', 'agent-results.json', 'response.txt', 'image-captures.json']
        chart_files = ['visual-reading.md', chart, page['before']['image'], page['before']['tree'],
                       page['afterEnter']['image'], page['afterEnter']['tree']]
        decoration_files = [marker, page['afterTab']['image'], page['afterTab']['tree'], page['afterEnter']['tree']]
        proof = {item: invoke(cli, 'attach', '--run', copied, '--case', case_id, '--file', evidence / item)
                 for item in dict.fromkeys(common + chart_files + decoration_files)}
        numbers = (
            f"グラフは訪問回数で4月{measured['Apr']}、5月{measured['May']}、6月{measured['Jun']}。"
            f"代替文が案内する表の値は4月{table['Apr']}、5月{table['May']}、6月{table['Jun']}。"
        )
        decoration = '青い図形は文字で名前が付く開閉部品の装飾。空のaltがあり、図形自体は公開AXに現れない。'
        judgment = dict(
            case_id=case_id, config_digest=info['config_digest'], normative_sha256=info['criterion']['normative_sha256'],
            execution='completed', outcome='failed' if result['chart'] == 'failed' else 'cant_tell',
            conditions_reviewed=True, exceptions_reviewed=True, coverage_complete=False,
            observed=numbers + decoration,
            steps_executed=['グラフの値・単位・傾向を画像から読む。',
                            'TabとEnterで表を開き、代替文を含む情報と各月の値を照合する。'],
            tests_applied=['T011-chart-alternative', 'T011-decoration'],
            targets=[
                dict(target='figure img', observed=numbers, expected='画像と同じ訪問回数と月別の値が得られる。',
                     outcome=result['chart'], evidence=[proof[item] for item in common + chart_files]),
                dict(target='summary img', observed=decoration, expected='装飾は操作名を重複させない。',
                     outcome=result['decoration'], evidence=[proof[item] for item in common + decoration_files]),
            ],
            evidence=list(proof.values()), remaining=['観察した表示幅と対象以外の1.1.1の確認が残る。'],
        )
        record_path = output / f'{name}-record.json'
        record_path.write_text(json.dumps(judgment, ensure_ascii=False, indent=2) + '\n')
        invoke(cli, 'record', '--run', copied, '--file', record_path)
        invoke(cli, 'page-report', '--run', copied, '--page-exact', case['page_url'])
        report_path = copied / 'data' / 'report.json'
        report = json.loads(report_path.read_text())
        row = next(item for item in report['cases'] if item['case_id'] == case_id)
        assert row['outcome'] == judgment['outcome']
        assert all(digest(original / path) == sha for path, sha in hashes.items())
        receipts.append(dict(site=name, case=case_id, selected_outcome=result['chart'], report_outcome=row['outcome'],
                             original_files_unchanged=len(hashes), report_sha256=digest(report_path)))
    (output / 'receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    options=parser.parse_args()
    expected = json.loads((options.evidence / 'oracle.json').read_text())
    record(options.cli, options.source, options.out, options.evidence, expected)
