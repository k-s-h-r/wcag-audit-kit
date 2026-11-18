"""Exercise declared hover and focus-visibility routes on the public WCAG fixtures."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading

from openpyxl import load_workbook

from keyboard_checks_browser import ROOT, audit, route


HOVER_CRITERION = '1.4.13'
FOCUS_CRITERION = '2.4.11'
HOVER_PLAN = {'id': 'price-tip', 'name': '料金の追加表示へ移動しEscapeで閉じる',
              'trigger': '#subject', 'popup': '#tip'}
FOCUS_TARGET = {'key': 'Tab', 'focus': '#subject', 'unobscured': True}
SHOW_BANNER = [{'key': 'Tab', 'focus': '#show'},
               {'key': 'Enter', 'focus': '#show', 'visible': '#banner'}]
AMBIGUOUS_OVERLAYS = {
    'no-pointer-events.html': ('pointer-events:none', 'paint_outside_hit_test'),
    'translucent-banner.html': ('opacity:.5', 'insufficient_paint_evidence'),
}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def execute(area, url, *, hover=None, keyboard=None, pause=False):
    area.mkdir()
    run = area / 'run'
    config = audit.init_config(url)
    config['environments'] = config['environments'][:1]
    config['keyboard_steps'] = 1
    if hover:
        config['hover_checks'] = [hover]
    if keyboard:
        config['keyboard_checks'] = [keyboard]
    audit.save(area / 'config.json', config)
    command = [sys.executable, str(ROOT / 'skills/wcag-audit-kit/scripts/audit.py'), 'page-audit',
               '--url', url, '--out', str(run), '--config', str(area / 'config.json'),
               '--mode', 'machine', '--screenshots', 'off', '--max-states', '1', '--max-depth', '1']

    def run_command(name, *arguments):
        result = subprocess.run(command + list(arguments), capture_output=True, text=True, timeout=90)
        (area / f'{name}.log').write_text(result.stdout + result.stderr)
        assert result.returncode == 0, (url, result.stdout, result.stderr)
        return json.loads(result.stdout.splitlines()[-1])

    if pause:
        run_command('paused', '--max-steps', '1')
        graph = audit.load(run / 'exploration.json')
        assert any(job.get('hover_check') == hover['id'] for job in graph['queue']), graph
        assert not any(edge.get('hover_check') for edge in graph['edges']), graph
    remaining = ['--resume'] if pause else []
    produced = run_command('resumed' if pause else 'first', '--max-steps', '2', *remaining)
    return run, Path(produced['excel'])


def report(run):
    path = next(run.glob('page-*-report.json'))
    value = audit.load(path)
    assert not value['audit_complete']
    assert all(case['outcome'] == 'not_run' for case in value['cases'])
    assert all(criterion['status'] == 'unverified' for criterion in value['criteria']
               if criterion['id'] in {HOVER_CRITERION, FOCUS_CRITERION})
    return path, value


def assert_report_formats(workbook, path, rows):
    html = path.with_suffix('.html').read_text()
    book = load_workbook(workbook, read_only=True, data_only=True)
    try:
        machine_rows = {tuple('' if value is None else value for value in cells)
                        for cells in book['機械検査'].values}
        issue_rows = list(book['自動検出した問題'].values)
        grouped_html = re.findall(r'<tr>(.*?)</tr>', html, re.S)
        for row in rows:
            assert tuple(row[key] for key in ('criterion', 'checkpoint', 'expected', 'outcome', 'environment',
                                              'capture', 'target', 'observed', 'evidence', 'note')) in machine_rows, row
            assert f'href="./{row["evidence"]}"' in html, row
            matching_issue_rows = [cells for cells in issue_rows if row['evidence'] in cells
                                   and row['target'] in cells and row['observed'] in cells]
            matching_html = [cells for cells in grouped_html if f'href="{row["evidence"]}"' in cells
                             and escape(row['target']) in cells and escape(row['observed']) in cells]
            if row['outcome'] in {'failed', 'cant_tell'}:
                assert len(matching_html) == len(matching_issue_rows) == 1, row
            else:
                assert not matching_html and not matching_issue_rows, row
    finally:
        book.close()


def load_proof(run, relative_path):
    graph = audit.load(run / 'exploration.json')
    assert audit.evidence_item(run, relative_path) in graph['proof'], relative_path
    path = run / relative_path
    events = audit.load(path.with_name('input-events.json'))
    assert not events['truncated']
    return audit.load(path), events['events']


def trusted_input(step, events):
    index = step['input_event_index']
    assert isinstance(index, int) and 1 <= index <= len(events), step
    event = events[index - 1]
    assert event['isTrusted'] and event['is_main_frame'], event
    return event


def inspect_hover(run, workbook, plan, expected):
    path, value = report(run)
    prefix = f'ホバー経路 / {plan["id"]} / '
    rows = {row['checkpoint'].removeprefix(prefix): row for row in value['machine_checks']
            if row['criterion'] == HOVER_CRITERION and row['checkpoint'].startswith(prefix)}
    assert {aspect: row['outcome'] for aspect, row in rows.items()} == expected, rows
    evidence, = {row['evidence'] for row in rows.values()}
    assert Path(evidence).name == 'hover-check.json'
    proof, events = load_proof(run, evidence)
    assert {item['aspect']: item['outcome'] for item in proof['observations']} == expected, proof
    assert all(row['target'] == plan['popup'] for row in rows.values()), rows
    if 'cant_tell' not in expected.values():
        steps = {step['action']: step for step in proof['steps']}
        for name in ('hover-trigger', 'move-to-popup', 'hover-trigger-for-escape'):
            assert trusted_input(steps[name], events)['type'] in {'pointermove', 'mousemove'}, steps[name]
            assert steps[name]['point'], steps[name]
        escape_event = trusted_input(steps['press-escape'], events)
        assert escape_event['type'] == 'keydown' and escape_event['key'] == 'Escape', escape_event
    assert_report_formats(workbook, path, list(rows.values()))
    return expected


def inspect_focus(run, workbook, plan, expected, status):
    path, value = report(run)
    row, = [row for row in value['machine_checks'] if row['criterion'] == FOCUS_CRITERION
            and row['checkpoint'] == f'キーボード経路 / {plan["id"]}']
    assert row['outcome'] == expected and row['target'] == '#subject', row
    assert Path(row['evidence']).name == 'keyboard-check.json'
    proof, events = load_proof(run, row['evidence'])
    assert proof['id'] == plan['id'] and proof['outcome'] == expected
    for step, condition in zip(proof['steps'], plan['steps'], strict=True):
        event = trusted_input(step, events)
        assert event['type'] == 'keydown' and event['key'] == condition['key'], event
    step = proof['steps'][-1]
    assert step['after']['id'] == 'subject', step
    receipt = step['occlusion']
    assert receipt['outcome'] == expected and receipt['observed'], step
    assert receipt['status'] == status and receipt['rect'] and receipt['viewport'], receipt
    assert len(receipt['samples']) == 9, receipt
    if expected == 'failed':
        assert receipt['overlay']['solidCore'] and receipt['overlay']['background'], receipt
    if expected == 'passed':
        assert receipt['exposed'] and receipt['targetCore'], receipt
    assert_report_formats(workbook, path, [row])
    return {'outcome': expected, 'measurement': status}


def cases():
    for number in range(1, 5):
        outcome = 'failed' if number % 2 else 'passed'
        page = f'p{number:02d}.html'
        expectation = {'hoverable': outcome, 'dismissible': outcome}
        yield HOVER_CRITERION, page, HOVER_PLAN, expectation
        steps = [*SHOW_BANNER, FOCUS_TARGET] if number > 2 else [FOCUS_TARGET]
        keyboard = route(FOCUS_CRITERION, 'focused-button', 'キーボードで保存ボタンを表示する', steps)
        status = 'entirely_covered' if outcome == 'failed' else 'partly_visible'
        yield FOCUS_CRITERION, page, keyboard, (outcome, status)
    for page, (_, status) in AMBIGUOUS_OVERLAYS.items():
        keyboard = route(FOCUS_CRITERION, 'ambiguous-cover', '前面バナーの重なりを確認する',
                         [*SHOW_BANNER, FOCUS_TARGET])
        yield FOCUS_CRITERION, page, keyboard, ('cant_tell', status)
    missing = dict(HOVER_PLAN, id='missing-popup', popup='#missing')
    yield HOVER_CRITERION, 'p04.html', missing, {'hoverable': 'cant_tell', 'dismissible': 'cant_tell'}


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    public = out / 'public'
    for criterion in (HOVER_CRITERION, FOCUS_CRITERION):
        shutil.copytree(ROOT / 'benchmarks' / 'cases' / criterion / 'public', public / criterion)
    focus_public = public / FOCUS_CRITERION
    covered = (focus_public / 'p03.html').read_text()
    marker = 'background:#eee;z-index:4'
    assert covered.count(marker) == 1
    for filename, (style, _) in AMBIGUOUS_OVERLAYS.items():
        (focus_public / filename).write_text(covered.replace(marker, f'{marker};{style}'))
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(public))) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'

        def run_case(case):
            criterion, page, plan, expected = case
            name = f'{criterion}-{page}-{plan["id"]}'
            url = f'{base}/{criterion}/{page}'
            if criterion == HOVER_CRITERION:
                run, workbook = execute(out / name, url, hover=plan, pause=page == 'p03.html')
                outcome = inspect_hover(run, workbook, plan, expected)
            else:
                run, workbook = execute(out / name, url, keyboard=plan)
                outcome = inspect_focus(run, workbook, plan, *expected)
            return {'criterion': criterion, 'page': page, 'outcome': outcome}

        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(run_case, cases()))
            audit.save(out / 'observed.json', results)
            print(json.dumps(results, ensure_ascii=False))
        finally:
            server.shutdown()
            thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
