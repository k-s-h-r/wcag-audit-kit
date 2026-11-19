"""Exercise page-audit on real keyboard paths through menus and disclosure controls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from html import unescape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
from urllib.parse import urlsplit

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/wcag-audit-kit/scripts'))
import audit


ROOT_OPEN = [dict(key='Tab', focus='#before'), dict(key='Tab', focus='#level1'),
             dict(key='Enter', focus='#level1', visible='#level2-panel'), dict(key='Tab', focus='#level2')]
THIRD_OPEN = ROOT_OPEN + [dict(key='Enter', focus='#level2', visible='#level3-panel')]
LEAF = THIRD_OPEN + [dict(key='Tab', focus='#leaf')]


def route(criterion, identifier, name, steps, **extra):
    return dict(id=identifier, name=name, criterion=criterion, steps=steps, **extra)


def fixtures(base):
    criterion = '2.1.1'
    activate = route(criterion, 'activate', '製品から見積管理へ進む', LEAF + [dict(key='Enter', visible='h1')],
                     destination=f'{base}/{criterion}/destination.html')
    space = route(criterion, 'open-with-space', '業務支援をSpaceで開く', ROOT_OPEN +
                  [dict(key='Space', focus='#level2', visible='#level3-panel')])
    yield criterion, 'p04.html', [activate, space], 'passed'
    yield criterion, 'p05.html', [activate, space], 'failed'

    criterion = '2.1.2'
    close = route(criterion, 'close-levels', 'Escapeで閉じて親へ戻る', LEAF + [
        dict(key='Escape', focus='#level2', hidden='#level3-panel'),
        dict(key='Escape', focus='#level1', hidden='#level2-panel'),
        dict(key='Tab', focus='#help'), dict(key='Tab', focus='#after')])
    tab_out = route(criterion, 'tab-out', 'Tabで第3階層を離れる', LEAF + [
        dict(key='Tab', focus='#other-leaf'), dict(key='Tab', focus='#help')])
    reverse_out = route(criterion, 'reverse-out', 'Shift+Tabで第3階層を離れる', LEAF + [
        dict(key='Shift+Tab', focus='#level2')])
    yield criterion, 'p03.html', [close, tab_out, reverse_out], 'passed'
    yield criterion, 'p04.html', [close, tab_out, reverse_out], 'failed'

    criterion = '2.4.3'
    order = route(criterion, 'focus-order', '開いた階層へ順に移動する', LEAF)
    yield criterion, 'p03.html', [order], 'passed'
    yield criterion, 'p04.html', [order], 'failed'


def disclosure_dialog_fixtures():
    accordion = route('2.1.1', 'accordion', '詳細を開閉し、次の項目へ進む', [
        dict(key='Tab', focus='#accordion'), dict(key='Enter', focus='#accordion', visible='#panel'),
        dict(key='Tab', focus='#nested'), dict(key='Space', focus='#nested', visible='#nested-panel'),
        dict(key='Space', focus='#nested', hidden='#nested-panel'), dict(key='Shift+Tab', focus='#accordion'),
        dict(key='Space', focus='#accordion', hidden='#panel'), dict(key='Tab', focus='#combo')])
    native_dialog = route('2.4.3', 'native-dialog', 'ネイティブダイアログを閉じて起点へ戻る', [
        dict(key='Tab', focus='#accordion'), dict(key='Tab', focus='#combo'),
        dict(key='Tab', focus='#open-dialog'), dict(key='Enter', focus='#close-dialog', visible='#dialog'),
        dict(key='Escape', focus='#open-dialog', hidden='#dialog')])
    yield '2.4.3', 'page-workflow.html', [accordion, native_dialog], 'passed'

    enter_focus = [dict(key='Tab', focus='#before'), dict(key='Tab', focus='#inner-action')]
    shadow_enter = route('2.1.1', 'shadow-enter', 'Shadow DOM内の詳細をEnterで開閉する', enter_focus + [
        dict(key='Enter', focus='#inner-action', visible='#inner-panel'),
        dict(key='Enter', focus='#inner-action', hidden='#inner-panel'), dict(key='Tab', focus='#after')])
    shadow_space = route('2.1.1', 'shadow-space', 'Shadow DOM内の詳細をSpaceで開閉する', enter_focus + [
        dict(key='Space', focus='#inner-action', visible='#inner-panel'),
        dict(key='Space', focus='#inner-action', hidden='#inner-panel'), dict(key='Tab', focus='#after')])
    yield '2.1.1', 'p06.html', [shadow_enter, shadow_space], 'failed'
    yield '2.1.1', 'p07.html', [shadow_enter, shadow_space], 'passed'

    open_dialogs = [dict(key='Tab', focus='#launch'), dict(key='Enter', focus='#outer-name', visible='#outer'),
                    dict(key='Tab', focus='#inner-opener'), dict(key='Enter', focus='#inner-name', visible='#subject')]
    escape = route('2.1.2', 'escape-inner', 'Escapeで2つのダイアログを順に閉じる', open_dialogs + [
        dict(key='Escape', focus='#inner-opener', hidden='#subject', visible='#outer'),
        dict(key='Escape', focus='#launch', hidden='#outer'), dict(key='Tab', focus='#outside')])
    close_button = route('2.1.2', 'dialog-close-button', '内側の閉じるボタンにTabで進み、親へ戻る', open_dialogs + [
        dict(key='Tab', focus='#building'), dict(key='Tab', focus='#inner-close'),
        dict(key='Enter', focus='#inner-opener', hidden='#subject', visible='#outer')])
    yield '2.1.2', 'p07.html', [escape, close_button], 'failed'
    yield '2.1.2', 'p08.html', [escape, close_button], 'passed'

    restore = route('2.4.3', 'dialog-restore', '内側を閉じたあと外側の起点へ戻る', open_dialogs + [
        dict(key='Escape', focus='#inner-opener', hidden='#subject', visible='#outer')])
    yield '2.4.3', 'p07.html', [restore], 'failed'
    yield '2.4.3', 'p08.html', [restore], 'passed'


FAILURES = {
    'activate': ('#level2', 5, 'Enter', '#level2', '#level3-panel'),
    'open-with-space': ('#level2', 5, 'Space', '#level2', '#level3-panel'),
    'close-levels': ('#leaf', 7, 'Escape', '#leaf', '#level3-panel'),
    'tab-out': ('#other-leaf', 8, 'Tab', '#leaf', '#help'),
    'reverse-out': ('#leaf', 7, 'Shift+Tab', '#other-leaf', '#level2'),
    'focus-order': ('#level2', 5, 'Enter', '#after', '#level2'),
    'shadow-enter': ('#subject → #inner-action', 3, 'Enter', '#inner-action', '#inner-panel'),
    'shadow-space': ('#subject → #inner-action', 3, 'Space', '#inner-action', '#inner-panel'),
    'escape-inner': ('#inner-name', 5, 'Escape', '#inner-name', '#subject'),
    'dialog-close-button': ('#building', 6, 'Tab', '#inner-name', '#inner-close'),
    'dialog-restore': ('#inner-name', 5, 'Escape', '#outside', '#inner-opener'),
    'shadow-host-only': ('#before', 2, 'Tab', '#inner-action', '#subject'),
}


class Handler(SimpleHTTPRequestHandler):
    requests = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        type(self).requests.append(self.path)
        if urlsplit(self.path).path.endswith('/redirect.html'):
            self.send_response(302)
            self.send_header('Location', '/unexpected.html')
            self.end_headers()
        elif self.path.endswith('/redirect-source.html'):
            data = b'<!doctype html><title>Redirect check</title><a id="link" href="redirect.html">Continue</a>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            super().do_GET()


def execute(area, url, checks, resume_trial=False):
    area.mkdir()
    run = area / 'run'
    config = audit.init_config(url)
    config['environments'] = config['environments'][:1]
    config['keyboard_steps'] = 2
    config['keyboard_checks'] = checks
    audit.save(area / 'config.json', config)
    command = [sys.executable, str(ROOT / 'skills/wcag-audit-kit/scripts/audit.py'), 'page-audit',
               '--url', url, '--out', str(run), '--max-depth', '1', '--max-states', '1', '--mode', 'machine',
               '--screenshots', 'off', '--config', str(area / 'config.json')]

    def run_command(args, name):
        result = subprocess.run(command + args, capture_output=True, text=True, timeout=70)
        (area / (name + '.log')).write_text(result.stdout + result.stderr)
        assert result.returncode == 0, (url, result.stdout, result.stderr)

    if resume_trial:
        run_command(['--max-steps', '1'], 'paused')
        graph = audit.load(audit.run_layout.ledger(run) / 'exploration.json')
        assert not any(edge.get('keyboard_check') for edge in graph['edges'])
        assert any(job.get('keyboard_check') for job in graph['queue'])
        run_command(['--resume', '--max-steps', str(1 + len(checks))], 'resumed')
    else:
        run_command(['--max-steps', str(1 + len(checks))], 'first')
    return audit.run_layout.ledger(run)


def read_results(run, criterion, page, checks, expected):
    report = audit.run_layout.report_files(audit.run_layout.ledger(run), single=True).json
    value = audit.load(report)
    rows = [row for row in value['machine_checks'] if row['checkpoint'].startswith('キーボード経路 / ')]
    assert len(rows) == len(checks) and all(row['outcome'] == expected for row in rows), (criterion, page, rows)
    assert not value['audit_complete'] and all(case['outcome'] == 'not_run' for case in value['cases'])
    for row, plan in zip(rows, checks):
        proof = audit.load(run / row['evidence'])
        assert proof['id'] == plan['id'] and proof['outcome'] == expected and row['criterion'] == plan['criterion']
        steps = proof['steps']
        events = audit.load((run / row['evidence']).with_name('input-events.json'))['events']
        assert all(events[step['input_event_index'] - 1]['isTrusted'] for step in steps)
        if plan['id'].startswith('shadow-'):
            assert steps[1]['after']['id'] == 'inner-action'
            assert steps[1]['after']['shadowHosts'] == [{'tag': 'div', 'id': 'subject'}]
        if expected == 'passed':
            assert len(steps) == len(plan['steps']) and all(c['matched'] for step in steps for c in step['conditions'])
            if 'destination' in plan:
                assert steps[-1]['url'] == plan['destination']
        else:
            target, index, key, focus, missed = FAILURES[plan['id']]
            assert row['target'] == target and f'{index}手順目の {key}' in row['observed'] and missed in row['observed']
            assert steps[-1]['after']['id'] == focus[1:]
            assert steps[-1]['index'] == index and steps[-1]['key'] == key
            if plan['id'] == 'dialog-restore':
                assert [c['matched'] for c in steps[-1]['conditions']] == [False, True, True]
            if plan['id'] == 'shadow-host-only':
                assert '#subject → #inner-action' in row['observed']
    if expected == 'failed':
        html = audit.run_layout.report_files(audit.run_layout.ledger(run), single=True).html.read_text()
        xlsx = audit.run_layout.report_files(audit.run_layout.ledger(run), single=True).excel
        book = load_workbook(xlsx, read_only=True, data_only=True)
        try:
            worksheet = list(book['自動検出した問題'].values)
            for row in rows:
                matches = [part for part in re.findall(r'<tr>(.*?)</tr>', html, re.S)
                           if f'href="{audit.run_layout.href(xlsx.with_suffix(".html"), run / row["evidence"])}"' in part]
                assert len(matches) == 1 and row['target'] in unescape(matches[0]) and row['observed'] in unescape(matches[0])
                assert any(row['evidence'] in sheet_row and row['target'] in sheet_row and row['observed'] in sheet_row
                           for sheet_row in worksheet)
        finally:
            book.close()
    return {'criterion': criterion, 'page': page, 'outcome': expected, 'route_count': len(rows)}


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    public = out / 'public'
    for criterion in ['2.1.1', '2.1.2', '2.4.3']:
        shutil.copytree(ROOT / 'benchmarks/cases' / criterion / 'public', public / criterion)
    shutil.copyfile(ROOT / 'tests/fixtures/page-workflow.html', public / '2.4.3/page-workflow.html')
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(public)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'

    def check_case(args):
        criterion, page, checks, expected = args
        run = execute(out / f'{criterion}-{page}', f'{base}/{criterion}/{page}', checks,
                      resume_trial=criterion == '2.1.2' and page == 'p03.html')
        return read_results(run, criterion, page, checks, expected)

    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(check_case, [*fixtures(base), *disclosure_dialog_fixtures()]))
        host_only = route('2.1.1', 'shadow-host-only', 'ホストと内側の実フォーカスを区別する',
                          [dict(key='Tab', focus='#before'), dict(key='Tab', focus='#subject')])
        host_run = execute(out / 'shadow-host-only', f'{base}/2.1.1/p07.html', [host_only])
        read_results(host_run, '2.1.1', 'p07.html', [host_only], 'failed')
        redirect = route('2.1.1', 'redirect', '制限したリンク移動',
                         [dict(key='Tab', focus='#link'), dict(key='Enter', visible='h1')],
                         destination=f'{base}/redirect.html')
        run = execute(out / 'redirect', f'{base}/redirect-source.html', [redirect])
        value = audit.load(audit.run_layout.report_files(audit.run_layout.ledger(run), single=True).json)
        row, = [r for r in value['machine_checks'] if r['checkpoint'] == 'キーボード経路 / redirect']
        assert row['outcome'] == 'cant_tell' and '/redirect.html' in Handler.requests
        assert '/unexpected.html' not in Handler.requests
        assert 'リダイレクト' in (run / row['evidence']).with_name('transition.json').read_text()
        audit.save(out / 'observed.json', {'cases': results, 'host_focus_distinguished': True, 'blocked_redirect': True, 'resume_verified': True})
        print(json.dumps(results, ensure_ascii=False))
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
