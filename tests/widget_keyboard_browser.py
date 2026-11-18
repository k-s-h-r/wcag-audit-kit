"""Run keyboard and DOM-state checks on existing combobox, tab and switch fixtures."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from html import unescape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading

from openpyxl import load_workbook

from keyboard_checks_browser import ROOT, audit, execute, route


def attr(selector, name, equals):
    return {'selector': selector, 'name': name, 'equals': equals}


def expanded_candidate(candidate):
    return [attr('#subject', 'aria-expanded', 'true'), attr('#subject', 'aria-activedescendant', candidate)]


PICK_CANDIDATES = [
    {'key': 'Tab', 'focus': '#subject', 'hidden': '#options'},
    {'key': 'ArrowDown', 'focus': '#subject', 'visible': '#osaka', 'attributes': expanded_candidate('osaka')},
    {'key': 'ArrowDown', 'focus': '#subject', 'visible': '#tokyo', 'attributes': expanded_candidate('tokyo')},
]
CLOSED = [attr('#subject', 'aria-expanded', 'false'), attr('#subject', 'aria-activedescendant', None)]


def combobox_paths():
    yield route('2.1.2', 'browse', '入力欄にフォーカスを置いたまま候補を移動する', PICK_CANDIDATES)
    yield route('2.1.2', 'select', 'Enterで候補を選択する', PICK_CANDIDATES + [
        {'key': 'Enter', 'focus': '#subject', 'hidden': '#options', 'attributes': CLOSED,
         'value': {'selector': '#subject', 'equals': '東京'}}])
    yield route('2.1.2', 'cancel', 'Escapeで候補を閉じる', PICK_CANDIDATES[:2] + [
        {'key': 'Escape', 'focus': '#subject', 'hidden': '#options', 'attributes': CLOSED,
         'value': {'selector': '#subject', 'equals': ''}}])
    yield route('2.1.2', 'leave', 'Tabで候補から次の操作へ進む', PICK_CANDIDATES[:2] + [
        {'key': 'Tab', 'focus': '#after', 'hidden': '#options', 'attributes': CLOSED}])


def cases():
    combo = list(combobox_paths())
    yield '2.1.2', 'p09.html', combo, {'select': (4, '東京'), 'cancel': (3, '#options'), 'leave': (3, '#after')}
    yield '2.1.2', 'p10.html', combo, {}

    state = route('4.1.2', 'combobox-state', '候補位置を属性へ反映する', PICK_CANDIDATES)
    yield '4.1.2', 'p07.html', [state], {'combobox-state': (2, 'aria-activedescendant')}
    yield '4.1.2', 'p08.html', [state], {}

    tab_attributes = [attr('#tab-a', 'aria-selected', 'false'), attr('#tab-b', 'aria-selected', 'true')]
    tab_entry = {'key': 'Tab', 'focus': '#tab-a', 'visible': '#panel-a'}
    manual = route('2.1.1', 'manual-tab', '矢印で料金タブへ移りEnterでパネルを確認する', [
        tab_entry, {'key': 'ArrowRight', 'focus': '#tab-b'},
        {'key': 'Enter', 'focus': '#tab-b', 'visible': '#panel-b', 'hidden': '#panel-a',
         'attributes': tab_attributes}])
    yield '2.1.1', 'p08.html', [manual], {'manual-tab': (3, '#panel-b')}
    yield '2.1.1', 'p09.html', [manual], {}

    automatic = route('4.1.2', 'automatic-tab', '自動選択で選択属性とパネルを切り替える', [
        tab_entry, {'key': 'ArrowRight', 'focus': '#tab-b', 'visible': '#panel-b', 'hidden': '#panel-a',
                    'attributes': tab_attributes}])
    yield '4.1.2', 'p09.html', [automatic], {'automatic-tab': (2, 'aria-selected')}
    yield '4.1.2', 'p10.html', [automatic], {}

    switch = route('4.1.2', 'switch', 'スイッチの表示とチェック状態を更新する', [
        {'key': 'Tab', 'focus': '#subject'},
        {'key': 'Space', 'focus': '#subject', 'visible': '#state:text-is("有効")',
         'attributes': [attr('#subject', 'aria-checked', 'true')]},
        {'key': 'Space', 'focus': '#subject', 'visible': '#state:text-is("無効")',
         'attributes': [attr('#subject', 'aria-checked', 'false')]}])
    yield '4.1.2', 'p03.html', [switch], {'switch': (2, 'aria-checked')}
    yield '4.1.2', 'p04.html', [switch], {}

    disclosure = route('4.1.2', 'shadow-state', '公開Shadow DOM内の展開状態を更新する', [
        {'key': 'Tab', 'focus': '#before'}, {'key': 'Tab', 'focus': '#inner-action'},
        {'key': 'Enter', 'focus': '#inner-action', 'visible': '#inner-panel',
         'attributes': [attr('#inner-action', 'aria-expanded', 'true')]},
        {'key': 'Enter', 'focus': '#inner-action', 'hidden': '#inner-panel',
         'attributes': [attr('#inner-action', 'aria-expanded', 'false')]}])
    yield '4.1.2', 'p05.html', [disclosure], {'shadow-state': (3, 'aria-expanded')}
    yield '4.1.2', 'p06.html', [disclosure], {}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def assert_formats(run, report, issues):
    html = report.with_suffix('.html').read_text()
    workbook = load_workbook(next(run.glob('page-*-report*.xlsx')), read_only=True, data_only=True)
    try:
        rows = list(workbook['自動検出した問題'].values)
        for issue in issues:
            tag = f'href="{issue["evidence"]}"'
            matches = [unescape(row) for row in re.findall(r'<tr>(.*?)</tr>', html, re.S) if tag in row]
            assert len(matches) == 1 and issue['observed'] in matches[0] and issue['target'] in matches[0], issue
            assert any(issue['observed'] in row and issue['target'] in row and issue['evidence'] in row for row in rows), issue
    finally:
        workbook.close()


def inspect_report(run, plans, expected_failures):
    report = next(run.glob('page-*-report.json'))
    result = json.loads(report.read_text())
    rows = {row['checkpoint'].split(' / ')[1]: row for row in result['machine_checks']
            if row['checkpoint'].startswith('キーボード経路 / ')}
    assert set(rows) == {plan['id'] for plan in plans}, rows
    assert not result['audit_complete'] and all(case['outcome'] == 'not_run' for case in result['cases'])
    issues = []
    for plan in plans:
        row = rows[plan['id']]
        proof = audit.load(run / row['evidence'])
        assert row['criterion'] == plan['criterion'] and row['outcome'] == proof['outcome']
        keys = [step['key'] for step in plan['steps']]
        events = audit.load((run / row['evidence']).with_name('input-events.json'))['events']
        assert all(events[step['input_event_index'] - 1]['isTrusted'] for step in proof['steps']), proof
        if plan['id'] in expected_failures:
            index, detail = expected_failures[plan['id']]
            assert row['outcome'] == 'failed' and len(proof['steps']) == index, row
            assert detail in row['observed'] and f'{index}手順目の {keys[index - 1]}' in row['observed'], row
            final_conditions = proof['steps'][-1]['conditions']
            assert any(not observation['matched'] for observation in final_conditions)
            if plan['criterion'] == '4.1.2':
                assert all(observation['matched'] for observation in final_conditions
                           if observation['kind'] in {'focus', 'visible', 'hidden'}), proof
            issues.append(row)
        else:
            assert row['outcome'] == 'passed' and len(proof['steps']) == len(keys), row
            assert all(observation['matched'] for step in proof['steps'] for observation in step['conditions']), proof
    if issues:
        assert_formats(run, report, issues)
    return dict(passed=len(plans)-len(issues), failed=len(issues))


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    public = ROOT / 'benchmarks' / 'cases'
    # Serve only fixture pages. The URL is mapped to a criterion's public root.
    class PublicOnly(Handler):
        def translate_path(self, path):
            local = Path(super().translate_path(path)).relative_to(public)
            if len(local.parts) < 3 or local.parts[1] != 'public':
                return str(out / 'not-found')
            return str(public / local)

    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(PublicOnly, directory=public))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'

    def check_case(args):
        criterion, page, plans, expected_failures = args
        run = execute(out / f'{criterion}-{page}', f'{base}/{criterion}/public/{page}', plans)
        return dict(criterion=criterion, page=page, **inspect_report(run, plans, expected_failures))

    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(check_case, cases()))
        audit.save(out / 'observed.json', {'cases': results})
        print(json.dumps(results, ensure_ascii=False))
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
