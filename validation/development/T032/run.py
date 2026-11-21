"""Observe the frozen reservation pair with native Orca and produce audit reports."""

import argparse
from datetime import datetime
from functools import partial
from hashlib import sha256
from html import unescape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import shutil
import subprocess
import sys
from threading import Thread
from urllib.parse import urljoin, urlsplit
from zipfile import ZipFile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CLI = REPO / 'skills/wcag-audit-kit/scripts/audit.py'
sys.path.insert(0, str(REPO))
from benchmarks.native_status import capture
from validation.development.T026.score import ErrorMarkup, digest, focused, load, text, words
from orca_log import speech_in_window


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def save(path, value):
    path.write_text(canonical(value), encoding='utf-8')


def check_freeze():
    fixture = HERE / 'fixture'
    pages = {p.relative_to(fixture).as_posix(): p.read_text(encoding='utf-8')
             for p in fixture.rglob('*') if p.is_file()}
    frozen = load(HERE / 'blind-start.json')
    actual = {'fixture_sha256': sha256(canonical(pages).encode()).hexdigest(),
              'oracle_sha256': digest(HERE / 'oracle.json'),
              'scenario_sha256': digest(HERE / 'scenario.json')}
    if any(frozen[key] != checksum for key, checksum in actual.items()):
        raise ValueError('盲検操作前に固定した試験資料のハッシュと一致しない。')
    return actual


def cli(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)], check=True,
                          text=True, capture_output=True).stdout.strip()


def speech(row):
    return [item['phrase'] for item in row['speech']]


def observe(area, request, urls, oracle):
    speech_dir = area / 'speech'
    receipt = speech_dir / 'screen-reader.json'
    result = {'outcome': 'cant_tell', 'valid': False, 'reason': '実Orcaの起動、固定した入力または発話ログの確認が不足。'}
    if not receipt.is_file():
        return result
    raw = load(receipt)
    env, rows = raw['environment'], raw['observations']
    result.update(environment=env, adapter_status=raw['status'], adapter_error=raw.get('error'))
    log = speech_dir / 'orca-debug.log'
    if (raw['status'] != 'collected' or env.get('simulation') is not False
            or env.get('installation_verified') is not True or env.get('reader') != 'Orca'
            or env.get('browser') != 'Chromium' or raw['scenario'] != request
            or raw['request_sha256'] != digest(area / 'request.json') or not log.is_file()
            or raw['cleanup']['debug_log_sha256'] != digest(log) or raw['cleanup']['pty_error'] is not None
            or len(rows) != len(request['actions'])):
        return result

    log_text = log.read_text(errors='replace')
    last = datetime.fromisoformat(raw['started_at'])
    for index, (row, action) in enumerate(zip(rows, request['actions'], strict=True), 1):
        start, finish = (datetime.fromisoformat(row[key]) for key in ('started_at', 'finished_at'))
        if (row['index'] != index or row['action'] != action or not last <= start < finish
                or (finish - start).total_seconds() < request['settle_ms'] / 1000
                or row['speech'] != speech_in_window(log_text, row['started_at'], row['finished_at'])):
            result['reason'] = '元の発話ログと操作、観察窓を照合できなかった。'
            return result
        last = finish

    steps = {name: rows[index - 1] for name, index in oracle['steps'].items()}
    labels = oracle['labels']
    error, review = steps['error'], steps['review_focused']
    correction = steps['returned_to_input']
    recovery_speech = words(' '.join(speech(correction)))
    name = request['case_id']
    attributes = ErrorMarkup((HERE / 'fixture' / name / urlsplit(urls[2]).path.rsplit('/', 1)[-1]).read_text()).attributes
    role = attributes.get('role', 'paragraph')
    starts = [1, oracle['steps']['calendar'], oracle['steps']['form'], oracle['steps']['confirmation']]
    ends = [*starts[1:], len(rows) + 1]
    expected_route = [url for url, start, end in zip(urls, starts, ends, strict=True) for _ in range(end - start)]
    result.update(
        visited=list(dict.fromkeys(row['url'] for row in rows)),
        calendar=text(steps['calendar'], 'main'), confirmation=text(steps['confirmation'], 'main'),
        error_visible=labels['error'] in text(error, 'main'), error_role=role,
        review_speech=speech(review), error_speech=speech(error), correction_speech=speech(correction),
        error_window=[error['started_at'], error['finished_at']],
        announcement=words(labels['error']) in [words(phrase) for phrase in speech(error)],
        silence=all(not any(fragment in words(phrase) for fragment in ('見学人数', '2名以上', '入力してください'))
                    for phrase in speech(error)),
        error_screen_sha256=digest(speech_dir / f"step-{oracle['steps']['error']}.png"),
        speech_log_sha256=digest(log),
    )
    result['valid'] = (
        [row['url'] for row in rows] == expected_route and
        steps['menu_focused']['focus_after']['id'] == 'menu' and
        labels['start'] not in text(steps['menu_focused'], 'main') and
        labels['start'] in text(steps['menu_open'], 'main') and
        steps['start_focused']['focus_after']['id'] == 'schedule' and
        all(labels[name] in result['calendar'] for name in ('full', 'available')) and
        steps['available_focused']['focus_after']['id'] == 'slot-day' and
        labels['date'] in text(steps['form'], 'main') and
        focused(steps['invalid_input'], 'people') and focused(review, 'review') and
        labels['error'] not in text(review, 'main') and result['error_visible'] and focused(error, 'review') and
        correction['focus_after']['id'] == 'people' and focused(steps['corrected_input'], 'people') and
        labels['confirmation'] in result['confirmation'] and
        words(labels['review']) in words(' '.join(result['review_speech'])) and
        words(labels['input']) in recovery_speech and words(labels['error']) in recovery_speech and
        role == oracle['cases'][name]['role'] and 'aria-live' not in attributes
    )
    result['reason'] = ('閉じたメニューから日付選択、エラー、入力修正、日付と人数の確認までを照合した。'
                        if result['valid'] else '画面経路、フォーカス、表示、同じ対象への発話の照合が不足。')
    return result


def error_ax_role(nodes, message):
    by_id = {node['nodeId']: node for node in nodes}
    node = next(node for node in nodes if node['role']['value'] == 'StaticText'
                and node.get('name', {}).get('value') == message)
    while parent_id := node.get('parentId'):
        node = by_id[parent_id]
        role = node['role']['value']
        if role in {'alert', 'status', 'paragraph'}:
            return role
    raise ValueError('公開アクセシビリティツリーからエラーのロールを特定できない。')


def report(area, urls, verdict, oracle):
    config = area / 'config.json'
    run = area / 'audit'
    message = oracle['labels']['error']
    cli('init', '--url', urls[0], '--mode', 'screen-reader', '--config', config)
    settings = load(config)
    settings['scope'].update(mode='configured', pages=urls, known_pages=[], max_pages=len(urls))
    settings['environments'] = [env for env in settings['environments'] if env['id'] == 'desktop']
    settings['keyboard_steps'] = 0
    settings['inspection'].update(screenshots='initial', max_images=8)
    settings['states'] = [{
        'id': 'input-error', 'paths': [urlsplit(urls[2]).path],
        'actions': [{'type': 'fill', 'selector': '#people', 'value': '1'},
                    {'type': 'press', 'key': 'Tab'}, {'type': 'press', 'key': 'Space'}],
        'assert': [{'selector': '#error', 'text': message, 'visible': True}],
    }]
    save(config, settings)
    cli('start', '--config', config, '--out', run)
    plan = load(run / 'work/plan.json')
    case = next(case for case in plan['cases'] if case['criterion'] == oracle['criterion']
                and case['state'] == 'input-error' and case['page_url'] == urls[2])
    case_id = case['case_id']
    packet = json.loads(cli('case', '--run', run, '--id', case_id))
    ax = Path(case['evidence_dir']) / 'accessibility-tree.json'
    role = error_ax_role(load(run / 'work' / ax)['nodes'], message)
    if verdict['valid'] and role != verdict['error_role']:
        raise ValueError('発話を観察した状態と、CLIが取得した公開ロールが一致しない。')
    native = area / 'speech'
    sources = [area / 'request.json', native / 'screen-reader.json', native / 'orca-debug.log']
    for name in ('menu_open', 'calendar', 'review_focused', 'error', 'returned_to_input', 'confirmation'):
        sources.extend(native / f"step-{oracle['steps'][name]}.{ext}" for ext in ('png', 'json'))
    evidence = [ax.as_posix(), *(cli('attach', '--run', run, '--case', case_id, '--file', file)
                                 for file in sources if file.is_file())]
    outcome = verdict['outcome']
    utterance = '、'.join(f'「{phrase}」' for phrase in verdict.get('error_speech', [])) or '記録なし'
    observed = (f'1名で確認すると「{message}」と表示され、ボタンにフォーカスが残った。'
                f'公開ロールは {role}。操作後3秒間のOrca発話は{utterance}。'
                '入力欄へ戻って2名に修正し、12月20日・2名の確認画面へ進んだ。'
                if verdict['valid'] else verdict['reason'])
    expected = '確認ボタンにフォーカスを保ったまま、入力エラーの内容を支援技術で取得できる。'
    record = dict(case_id=case_id, config_digest=packet['config_digest'],
                  normative_sha256=packet['criterion']['normative_sha256'], execution='completed',
                  outcome=outcome, coverage_complete=outcome == 'passed', conditions_reviewed=verdict['valid'],
                  exceptions_reviewed=verdict['valid'], observed=observed, evidence=evidence,
                  steps_executed=[
                      'トップの「来館案内を開く」から版画室の見学日を調べる。',
                      '空きありと表示された12月20日を選ぶ。',
                      '見学人数に1を入力し、確認ボタンでSpaceを押して表示とOrca発話を照合する。',
                      'Shift+Tabで人数へ戻り、2に修正して確認画面へ進む。',
                  ], tests_applied=['4.1.3-01', '4.1.3-02'],
                  targets=[dict(target='見学人数の入力エラー（#error）', observed=observed, expected=expected,
                                outcome=outcome, evidence=evidence)],
                  remaining=[] if outcome == 'passed' else ['ほかの支援技術と全達成基準の検査が残る。'])
    if outcome == 'passed':
        record['method_coverage'] = [
            {'method': 'flow', 'status': 'executed', 'reason': '起点から確認画面までを専用環境で実キー操作した。'},
            {'method': 'dom', 'status': 'executed', 'reason': 'エラーの公開ロールを状態キャプチャーで確認した。'},
            {'method': 'screen-reader', 'status': 'executed', 'reason': 'Orcaの発話を元のログと操作の時間窓で照合した。'},
        ]
    judgment = area / 'judgment.json'
    save(judgment, record)
    cli('record', '--run', run, '--file', judgment)
    cli('report', '--run', run)
    workbook = run / 'reports/report.xlsx'
    cli('excel', 'export', '--run', run, '--mode', 'report', '--out', workbook)
    result = load(run / 'data/report.json')
    scope = result['scope_conformance']
    row = next(item for item in result['cases'] if item['case_id'] == case_id)
    issues, html = run / 'reports/details/issues.md', run / 'reports/report.html'
    with ZipFile(workbook) as payload:
        sheets = unescape('\n'.join(payload.read(name).decode() for name in payload.namelist()
                                     if name.startswith('xl/worksheets/') or name == 'xl/sharedStrings.xml'))
    expected_scope = 'does_not_conform' if outcome == 'failed' else 'unverified'
    heading = f'{oracle["level"]} の結論　{scope["label"]}'
    if (scope['status'] != expected_scope or result['audit_complete'] or row['outcome'] != outcome
            or not scope['remaining'] or any(case_id not in value or heading not in value
                                            for value in (html.read_text(), sheets))
            or (case_id in issues.read_text()) != (outcome == 'failed')
            or not all((run / 'work' / path).is_file() for path in evidence)):
        raise ValueError('検査票・不適合箇所一覧・HTML・JSON・Excelの照合に失敗した。')
    return {'case_id': case_id, 'outcome': outcome, 'scope_status': scope['status'], 'public_error_role': role,
            'evidence': evidence, 'files': {item.relative_to(area).as_posix(): digest(item)
                                           for item in (run / 'data/report.json', html, issues, workbook)}}


def run(runtime, output):
    frozen = check_freeze()
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(HERE / 'fixture', output / 'fixture')
    save(output / 'inputs.json', frozen)
    scenario, oracle = load(HERE / 'scenario.json'), load(HERE / 'oracle.json')
    handler = partial(SimpleHTTPRequestHandler, directory=output / 'fixture')
    with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            all_urls, cases, locations = {}, {}, {}
            control, = [name for name, case in oracle['cases'].items() if case['role'] == 'alert']
            for name in (control, *(name for name in oracle['cases'] if name != control)):
                area = output / name
                area.mkdir()
                entry = f'http://127.0.0.1:{server.server_port}/{name}/'
                all_urls[name] = [urljoin(entry, path) for path in oracle['paths']]
                request = dict(scenario, case_id=name, url=entry)
                save(area / 'request.json', request)
                capture(runtime, area)
                cases[name] = observe(area, request, all_urls[name], oracle)
                if cases[name].get('adapter_error') == '起動したOrcaのログから版を確認できない':
                    first = area
                    area = output / f'{name}-startup-retry'
                    area.mkdir()
                    save(area / 'request.json', request)
                    capture(runtime, area)
                    cases[name] = observe(area, request, all_urls[name], oracle)
                    cases[name]['previous_startup_failure'] = first.name
                cases[name]['artifact_directory'] = area.name
                locations[name] = area
                save(output / 'native-observations.json', cases)
                print(name, 'route_observed=' + str(cases[name]['valid']), flush=True)
            candidate = cases[control]
            if candidate['valid'] and candidate['announcement']:
                candidate['outcome'] = 'passed'
                for name, case in cases.items():
                    if (name != control and case['valid'] and case['silence']
                            and case['environment'] == candidate['environment']
                            and case['error_screen_sha256'] == candidate['error_screen_sha256']):
                        case['outcome'] = 'failed'
            save(output / 'native-observations.json', cases)
            reports = {name: report(locations[name], all_urls[name], case, oracle) for name, case in cases.items()}
            save(output / 'reports.json', reports)
        finally:
            server.shutdown()
            thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.out.resolve())
