"""Reproduce apparent paragraphs and lists with different semantics in Chromium."""
import argparse
import asyncio
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
from threading import Thread

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/wcag-audit-kit/scripts'
sys.path.insert(0, str(SCRIPTS))
import audit
import page_explorer
from visual_structure import REPORT_COLUMNS, REPORT_TITLE, STRUCTURES, candidate_shape, collect, report_evidence


BODY = '営業時間中にお越しの方は、最初に入口の受付までお進みください。'
ITEMS = ['受付でお名前をお伝えください。', '入館証をお受け取りください。', '廊下の案内を確認してください。']
LABEL = '来訪時のご案内'
STYLE = """
body { font: 16px/1.5 sans-serif; }
main { width: min(36rem, 100%); }
.heading { font-size: 24px; font-weight: 700; margin: 0 0 8px; }
.lead { font-weight: 700; margin: 0 0 8px; }
.group { list-style: none; margin: 0; padding: 0; }
.group p, .group li { margin: 0 0 3px; }
#generated-list p::before { content: "・"; }
.line-list p, .line-list li { margin: 0; }
#break-wrap p { width: 7rem; }
#break-clipped p { height: 3em; overflow: hidden; }
#break-indent p { text-indent: 2em; }
.matrix { display: table; table-layout: fixed; width: 21rem; border-spacing: 0; }
.matrix-row { display: table-row; }
.matrix-cell { display: table-cell; border: 1px solid #888; padding: 3px 8px; text-align: left; }
.matrix-head .matrix-cell { font-weight: 700; }
.cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.cards article { border: 1px solid #888; padding: 4px; }
"""


def heading_case(ident, tag='p', aria=False, emphasis='heading', label=LABEL):
    attributes = 'role="heading" aria-level="2"' if aria else ''
    return (f'<section id="{ident}"><{tag} id="{ident}-title" class="{emphasis}" {attributes}>{label}</{tag}>'
            f'<p>{BODY}</p></section>')


def list_case(ident, kind='plain', marker='・', items=ITEMS):
    wrapper = 'ul' if kind == 'native' else 'section'
    item = 'li' if kind == 'native' else 'p'
    group_role = 'role="list"' if kind == 'aria' else ''
    item_role = 'role="listitem"' if kind == 'aria' else ''
    prefix = marker if callable(marker) else lambda _index: marker
    contents = ''.join(f'<{item} id="{ident}-{i}" {item_role}>{prefix(i)}{text}</{item}>'
                       for i, text in enumerate(items, 1))
    return f'<{wrapper} class="group" id="{ident}" {group_role}>{contents}</{wrapper}>'


def line_list_case(ident, kind='plain', marker='・', items=ITEMS):
    if kind == 'native':
        contents = ''.join(f'<li>{marker}{text}</li>' for text in items)
        return f'<ul class="group line-list" id="{ident}">{contents}</ul>'
    contents = '<br>'.join(marker + text for text in items)
    group_role = 'role="list"' if kind == 'aria' else ''
    item_role = 'role="listitem"' if kind == 'aria' else ''
    return (f'<section class="line-list" id="{ident}" {group_role}>'
            f'<p id="{ident}-items" {item_role}>{contents}</p></section>')


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def table_case(ident, kind='plain'):
    wrapper, row_tag = ('table', 'tr') if kind == 'native' else ('div', 'div')
    semantic = kind in {'aria', 'incomplete'}
    role = ' role="table"' if semantic else ''
    row_role = ' role="row"' if semantic else ''
    rows = []
    for index, values in enumerate((('利用区分', '受付状況'), ('一般', '受付中'), ('学生', '受付終了'))):
        head = index == 0 and kind != 'no-header'
        row_class = 'matrix-head' if head else ''
        cell_tag = ('th' if head else 'td') if kind == 'native' else 'div'
        cells = []
        for col, text in enumerate(values):
            cell_role = 'columnheader' if head and (kind != 'incomplete' or col == 0) else 'cell'
            attributes = f' role="{cell_role}"' if semantic else (' scope="col"' if cell_tag == 'th' else '')
            cells.append(f'<{cell_tag} id="{ident}-{index}-{col}" class="matrix-cell"{attributes}>{text}</{cell_tag}>')
        rows.append(f'<{row_tag} class="matrix-row {row_class}"{row_role}>{"".join(cells)}</{row_tag}>')
    content = '<tbody>' + ''.join(rows) + '</tbody>' if kind == 'native' else ''.join(rows)
    return f'<{wrapper} id="{ident}" class="matrix"{role}>{content}</{wrapper}>'


def run_page_audit(area, url, selector, *, states=None, max_states=1, max_steps=1):
    area.mkdir()
    config = audit.init_config(url)
    config['environments'] = config['environments'][:1]
    config['keyboard_steps'] = 0
    if selector is not None:
        config['visual_structure_scope'] = selector
    if states is not None:
        config['visual_structure_states'] = states
    config_path = area/'config.json'
    audit.save(config_path, config)
    run = area/'run'
    command = subprocess.run([sys.executable, str(SCRIPTS/'audit.py'), 'page-audit', '--url', url,
        '--config', str(config_path), '--out', str(run), '--mode', 'machine', '--screenshots', 'off',
        '--max-states', str(max_states), '--max-steps', str(max_steps)], capture_output=True, text=True, timeout=90)
    (area/'command.log').write_text(command.stdout + command.stderr)
    assert command.returncode == 0, command.stdout + command.stderr
    assert not list(run.glob('evidence/*/*.png'))
    return run, json.loads(command.stdout.strip().splitlines()[-1])


def page_audit_case(area, url, selector, expected):
    from openpyxl import load_workbook

    run, files = run_page_audit(area, url, selector)
    graph = page_explorer.status(run)
    rows = report_evidence(run, graph)
    report = audit.load(files['json'])
    rendered = Path(files['html']).read_text()
    workbook = load_workbook(files['excel'])
    assert next(row for row in report['criteria'] if row['id'] == '1.3.1')['status'] == 'unverified'
    assert all(row['outcome'] == 'not_run' for row in report['cases'] if row['criterion'] == '1.3.1')
    if selector is None:
        assert rows == []
        assert 'visual_structure_evidence' not in report
        assert REPORT_TITLE not in rendered and REPORT_TITLE not in workbook.sheetnames
        workbook.close()
        return {'status': 'disabled'}
    assert report['visual_structure_evidence'] == rows
    row, = rows
    assert row['criterion'] == '1.3.1' and row['checkpoint'] == '1.3.1-02'
    assert row['scope'] == selector and row['status'] == expected
    node, = graph['nodes']
    assert node['route'] == [] and row['capture'] == node['capture']
    assert audit.evidence_item(run, row['evidence']) in graph['proof']
    assert report_evidence(run, dict(graph, proof=[])) == []
    assert 'outcome' not in row
    assert not any(item['evidence'] == row['evidence'] for item in report['machine_checks'])
    assert REPORT_TITLE in rendered and f'href="{row["evidence"]}"' in rendered
    assert 'href="#visual-structure-evidence"' in rendered and 'id="visual-structure-evidence"' in rendered
    worksheet = workbook[REPORT_TITLE]
    expected_rows = max(len(row['candidates']), 1)
    assert worksheet.max_row == expected_rows + 1
    assert all(worksheet.cell(index, len(REPORT_COLUMNS)).hyperlink.target == row['evidence'] for index in range(2, 2 + expected_rows))
    if selector == '#break-list':
        target_column = [key for key, _ in REPORT_COLUMNS].index('target') + 1
        text_column = [key for key, _ in REPORT_COLUMNS].index('observed') + 1
        assert worksheet.cell(2, target_column).value == '#break-list-items'
        assert all(item in worksheet.cell(2, text_column).value and item in rendered for item in ITEMS)
    if selector == '#scope':
        role_column = [key for key, _ in REPORT_COLUMNS].index('roles') + 1
        assert worksheet.cell(2, role_column).value == '段落（paragraph）'
        assert '先頭行のセル' in worksheet.cell(4, role_column).value
    workbook.close()
    from page_workflow import next_work

    packets = next_work(run, url, limit=55)['next_cases']
    packet, = [item for item in packets if item['criterion'] == '1.3.1']
    assert packet['visual_structure_evidence'] == rows
    if selector == '#scope':
        heading, bullets, table = row['candidates']
        assert heading['kind'] == 'heading' and heading['target']['selector'] == '#scope-title'
        assert bullets['kind'] == 'list' and bullets['marker'] == '・'
        assert [item['selector'] for item in bullets['targets']] == ['#bullet-1', '#bullet-2', '#bullet-3']
        assert table['kind'] == 'table' and table['target'] == '#scope-table'
        assert '認識された役割' in rendered and '表候補' in rendered and '先頭行のセル' in rendered
    elif selector == '#break-list':
        assert_broken_list(row, '#break-list-items', 'paragraph')
    elif expected == 'not_observed':
        assert row['candidates'] == []
        assert '対象範囲を一つに絞れない' in row['reason'], row
    else:
        assert row['candidates'] == []
    return {'status': row['status'], 'candidates': [item['kind'] for item in row['candidates']]}


def page_audit_cases(out):
    public = out/'public'
    public.mkdir()
    items = ''.join(f'<p id="bullet-{i}">・{text}</p>' for i, text in enumerate(ITEMS, 1))
    (public/'index.html').write_text(f'''<!doctype html><html lang="ja"><head><meta charset="utf-8">
        <title>1.3.1 構造候補の対照</title><style>{STYLE}</style></head><body><main>
        <section id="scope" class="group"><p id="scope-title" class="heading">{LABEL}</p><p>{BODY}</p>
        <hr>{items}{table_case('scope-table')}</section>
        {line_list_case('break-list')}
        {heading_case('aria-heading', aria=True)}{list_case('aria-list', 'aria')}
        </main></body></html>''')
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(public))) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}/index.html'
        try:
            cases = [('declared', '#scope', 'collected'), ('break-list', '#break-list', 'collected'),
                     ('semantic-control', '#aria-heading', 'collected'),
                     ('ambiguous', 'section', 'not_observed'),
                     ('disabled', None, 'disabled')]
            return {name: page_audit_case(out/name, url, selector, expected)
                    for name, selector, expected in cases}
        finally:
            server.shutdown()
            thread.join()


def operation_cases(out):
    import re
    from openpyxl import load_workbook
    from page_workflow import next_work

    out.mkdir()
    public = out/'public'
    public.mkdir()
    items = ''.join(f'<p id="item-{i}">・{text}</p>' for i, text in enumerate(ITEMS, 1))
    (public/'index.html').write_text(f'''<!doctype html><html lang="ja"><head><meta charset="utf-8">
        <title>1.3.1 操作後の構造候補</title><style>{STYLE}</style></head><body><main>
        <div id="open" onclick="document.getElementById('scope').hidden=false">詳細を表示</div>
        <section id="scope" class="group" hidden>
        <p id="title" class="heading">{LABEL}</p><p>{BODY}</p><hr>{items}
        <p id="semantic-title" class="heading" role="heading" aria-level="2">問い合わせ窓口</p>
        <p>{BODY}</p></section></main></body></html>''')
    # On-mouse markup reveals the same target as the usual one-page explorer.
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(public))) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}/index.html'
        try:
            cases = [('explored', '#scope', 'explored', 2), ('default-initial', '#scope', None, 2),
                     ('budget-initial', '#scope', 'explored', 1), ('disabled', None, None, 2)]
            summary = {}
            for name, selector, setting, max_states in cases:
                run, files = run_page_audit(out/name, url, selector, states=setting,
                                            max_states=max_states, max_steps=5)
                graph = page_explorer.status(run)
                report = audit.load(files['json'])
                rows = report_evidence(run, graph)
                summary[name] = {'nodes': len(graph['nodes']), 'steps': graph['steps'],
                                 'candidate_kinds': [[candidate['kind'] for candidate in row['candidates']] for row in rows]}
                audit.save(out/'operation-observed.json', summary)
                assert len(graph['nodes']) == max_states, graph
                assert all(row['outcome'] == 'not_run' for row in report['cases'] if row['criterion'] == '1.3.1')
                if not selector:
                    assert rows == [] and 'visual_structure_evidence' not in report
                    continue
                assert report['visual_structure_evidence'] == rows
                assert rows[0]['capture'] == graph['nodes'][0]['capture']
                assert rows[0]['status'] == 'collected' and not rows[0]['candidates']
                if name != 'explored':
                    assert len(rows) == 1
                    continue
                initial, opened = rows
                trigger_route = [{'type': 'click', 'selector': '#open'}]
                node = graph['nodes'][1]
                assert initial['route'] == [] and opened['route'] == trigger_route == node['route']
                assert opened['capture'] == node['capture'] and opened['status'] == 'collected'
                assert audit.evidence_item(run, opened['evidence']) in graph['proof']
                events_path = Path(node['evidence_dir'])/'input-events.json'
                assert audit.evidence_item(run, events_path.as_posix()) in graph['proof']
                events = audit.load(run/events_path)['events']
                assert any(event['type'] == 'click' and event['isTrusted'] and event['is_main_frame']
                           and event['target']['id'] == 'open' for event in events)
                heading, bullets = opened['candidates']
                assert heading['kind'] == 'heading' and heading['target']['selector'] == '#title'
                assert bullets['kind'] == 'list'
                assert [item['selector'] for item in bullets['targets']] == ['#item-1', '#item-2', '#item-3']
                assert not any(item['evidence'] == opened['evidence'] for item in report['machine_checks'])
                assert all('outcome' not in item for item in opened['candidates'])
                packets = next_work(run, url, limit=200)['next_cases']
                matching = [packet for packet in packets if packet['criterion'] == '1.3.1'
                            and packet['capture'] == opened['capture']]
                assert [packet['visual_structure_evidence'] for packet in matching] == [[opened]]
                rendered = Path(files['html']).read_text()
                table_rows = re.findall(r'<tr>(.*?)</tr>', rendered, re.S)
                assert any('クリック #open' in text and '#title' in text and f'href="{opened["evidence"]}"' in text
                           for text in table_rows)
                workbook = load_workbook(files['excel'])
                try:
                    worksheet = workbook[REPORT_TITLE]
                    state_column = [key for key, _ in REPORT_COLUMNS].index('state') + 1
                    assert worksheet.cell(2, state_column).value == '初期表示'
                    for index in [3, 4]:
                        assert worksheet.cell(index, state_column).value == 'クリック #open'
                        assert worksheet.cell(index, len(REPORT_COLUMNS)).hyperlink.target == opened['evidence']
                finally:
                    workbook.close()
            return summary
        finally:
            server.shutdown()
            thread.join()


def typography_cases(out):
    out.mkdir()
    public = out/'public'
    public.mkdir()
    (public/'index.html').write_text(f'''<!doctype html><html lang="ja"><head><meta charset="utf-8">
        <title>1.3.1 操作後の文字装飾</title><style>{STYLE}</style></head><body><main>
        <button type="button" id="enlarge"
                onclick="document.styleSheets[0].insertRule('#title {{ font: bold 24px/1.5 sans-serif; }}')">表示変更</button>
        <section id="scope"><p id="title">{LABEL}</p><p>{BODY}</p></section>
        <section id="unaffected"><p>補足の説明</p><p>{BODY}</p></section>
        </main></body></html>''')
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(public))) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}/index.html'
        try:
            cases = [('explored', '#scope', 'explored', 8), ('outside-scope', '#unaffected', 'explored', 8),
                     ('initial', '#scope', None, 8), ('disabled', None, None, 8),
                     ('budget-initial', '#scope', 'explored', 1)]
            summary = {}
            for name, scope, setting, max_states in cases:
                run, files = run_page_audit(out/name, url, scope, states=setting, max_states=max_states, max_steps=5)
                graph = page_explorer.status(run)
                report = audit.load(files['json'])
                trigger_route = [{'type': 'click', 'selector': '#enlarge'}]
                initial = graph['nodes'][0]
                triggered = next((edge for edge in graph['edges'] if edge['route'] == trigger_route), None)
                nodes = [initial] + ([triggered] if triggered else [])
                candidates = [c['target']['selector'] for row in report.get('visual_structure_evidence', [])
                              for c in row['candidates']]
                variants = [audit.load(run/entry['evidence_dir']/'state.json') for entry in nodes]
                assert len({page_explorer.fingerprint(dict(data, visual_structure_shape=[])) for data in variants}) == 1
                text_styles = [next((item['fontSize'], item['fontWeight']) for item in inventory['nodes']
                                    if item['id'] == 'title')
                               for inventory in (audit.load(run/entry['evidence_dir']/'inventory.json') for entry in nodes)]
                assert text_styles == ([('16px', '400'), ('24px', '700')] if triggered else [('16px', '400')])
                summary[name] = {'nodes': len(graph['nodes']), 'steps': graph['steps'],
                                 'candidates': candidates, 'text_styles': text_styles}
                audit.save(out/'typography-observed.json', summary)
                assert all(item['outcome'] == 'not_run' for item in report['cases'] if item['criterion'] == '1.3.1')
                if name == 'explored':
                    assert len(graph['nodes']) == 2 and graph['nodes'][1]['route'] == trigger_route
                    variant = graph['nodes'][1]
                    assert variant['fingerprint'] == page_explorer.fingerprint(variants[1])
                    assert variant['fingerprint'] != initial['fingerprint']
                    assert candidates == ['#title']
                    _, candidate_state = report['visual_structure_evidence']
                    assert candidate_state['capture'] == variant['capture']
                    assert audit.evidence_item(run, candidate_state['evidence']) in graph['proof']
                    events = audit.load(run/triggered['evidence_dir']/'input-events.json')['events']
                    assert any(event['isTrusted'] and event['type'] == 'click' and event['target']['id'] == 'enlarge'
                               for event in events)
                    assert f'href="{candidate_state["evidence"]}"' in Path(files['html']).read_text()
                else:
                    assert len(graph['nodes']) == 1 and candidates == []
                assert graph['steps'] == (1 if name == 'budget-initial' else 5)
            return summary
        finally:
            server.shutdown()
            thread.join()


def assert_broken_list(row, selector, role):
    candidate, = row['candidates']
    assert candidate['kind'] == 'list' and candidate['marker'] == '・'
    assert [(item['selector'], item['line'], item['text']) for item in candidate['targets']] == [
        (selector, index, '・' + text) for index, text in enumerate(ITEMS, 1)]
    assert all(item['single_line'] for item in candidate['targets'])
    assert candidate['accessibility'] == [{'role': role, 'ignored': False, 'inside_list': role == 'listitem'}]


async def main(out):
    if out.exists():
        raise ValueError('試験結果には新しい保存先を指定する。')
    cases = [
        (heading_case('paragraph-heading'), '#paragraph-heading', ['heading']),
        (heading_case('division-heading', 'div'), '#division-heading', ['heading']),
        (heading_case('numbered-heading', label='1. 来訪時のご案内'), '#numbered-heading', ['heading']),
        (heading_case('html-heading', 'h2'), '#html-heading', []),
        (heading_case('aria-heading', aria=True), '#aria-heading', []),
        (heading_case('ordinary-emphasis', emphasis='lead'), '#ordinary-emphasis', []),
        (heading_case('styled-intro', label='はじめにお読みください'), '#styled-intro', ['heading']),
        (list_case('paragraph-list'), '#paragraph-list', ['list']),
        (list_case('numbered-list', marker=lambda index: f'{index}. '), '#numbered-list', ['list']),
        (list_case('dash-list', marker='- '), '#dash-list', ['list']),
        (list_case('repeated-number', marker='1. '), '#repeated-number', []),
        (list_case('html-list', 'native'), '#html-list', []),
        (list_case('aria-list', 'aria'), '#aria-list', []),
        (list_case('generated-list', marker=''), '#generated-list', []),
        (list_case('dot-in-prose', marker='', items=['フランス・ドイツの入国案内'] * 3), '#dot-in-prose', []),
        (list_case('too-short', items=ITEMS[:2]), '#too-short', []),
        (line_list_case('break-list'), '#break-list', ['list']),
        (line_list_case('break-native', kind='native'), '#break-native', []),
        (line_list_case('break-aria', kind='aria'), '#break-aria', ['list']),
        (line_list_case('break-prose', marker='', items=['フランス・ドイツの入国案内'] * 3), '#break-prose', []),
        (line_list_case('break-short', items=ITEMS[:2]), '#break-short', []),
        (line_list_case('break-wrap'), '#break-wrap', []),
        (line_list_case('break-clipped'), '#break-clipped', []),
        (line_list_case('break-indent'), '#break-indent', []),
        (table_case('visual-table'), '#visual-table', ['table']),
        (table_case('native-table', 'native'), '#native-table', []),
        (table_case('aria-table', 'aria'), '#aria-table', []),
        (table_case('partial-aria', 'incomplete'), '#partial-aria', ['table']),
        (table_case('no-header', 'no-header'), '#no-header', []),
        ('<div id="cards" class="cards">' + ''.join(f'<article><h2>{text}</h2><p>受付中</p></article>'
            for text in ('一般利用', '学生利用', '団体利用')) + '</div>', '#cards', []),
    ]
    observed = []
    appearances = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        try:
            page = await browser.new_page(viewport={'width': 900, 'height': 540})
            for html, selector, kinds in cases:
                await page.set_content(f'<!doctype html><html lang="ja"><style>{STYLE}</style><main>{html}</main></html>')
                appearance = await page.locator(selector).screenshot(animations='allow', caret='initial')
                appearances[selector] = appearance
                result = await collect(page, selector)
                assert [candidate['kind'] for candidate in result['candidates']] == kinds, result
                if selector in {'#visual-table', '#native-table', '#aria-table', '#partial-aria'}:
                    shapes = candidate_shape(await page.evaluate(STRUCTURES, selector))
                    assert [shape[0] for shape in shapes] == ['table'], shapes
                if selector in {'#break-list', '#break-aria'}:
                    role = 'listitem' if selector == '#break-aria' else 'paragraph'
                    assert_broken_list(result, selector + '-items', role)
                if selector == '#partial-aria':
                    table, = result['candidates']
                    assert table['accessibility']['role'] == 'table'
                    assert [cell['accessibility']['role'] for cell in table['rows'][0]['cells']] == ['columnheader', 'cell']
                    assert table['unmatched_roles'] == ['#partial-aria-0-1']
                if selector == '#visual-table':
                    table, = result['candidates']
                    assert table['target'] == selector
                    assert [cell['text'] for cell in table['rows'][0]['cells']] == ['利用区分', '受付状況']
                    assert table['accessibility']['role'] not in {'table', 'grid'}
                for candidate in result['candidates']:
                    assert 'outcome' not in candidate
                observed.append(result)
            for first, second in (('#paragraph-heading', '#html-heading'), ('#paragraph-heading', '#aria-heading'),
                                  ('#paragraph-list', '#html-list'), ('#paragraph-list', '#aria-list'),
                                  ('#break-list', '#break-native'), ('#break-list', '#break-aria'),
                                  ('#visual-table', '#native-table'), ('#visual-table', '#aria-table')):
                assert appearances[first] == appearances[second], (first, second)
        finally:
            await browser.close()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'observed.json').write_text(json.dumps(observed, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({row['scope']: [c['kind'] for c in row['candidates']] for row in observed}, ensure_ascii=False))
    results = page_audit_cases(out)
    audit.save(out/'page-audit-observed.json', results)
    print(json.dumps(results, ensure_ascii=False))
    print(json.dumps(operation_cases(out/'operations'), ensure_ascii=False))
    print(json.dumps(typography_cases(out/'typography'), ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    asyncio.run(main(parser.parse_args().out))
