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
from visual_structure import collect, report_evidence


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
    contents = ''.join(f'<{item} id="{ident}-{i}" {item_role}>{marker}{text}</{item}>'
                       for i, text in enumerate(items, 1))
    return f'<{wrapper} class="group" id="{ident}" {group_role}>{contents}</{wrapper}>'


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def page_audit_case(area, url, selector, expected):
    area.mkdir()
    config = audit.init_config(url)
    config['environments'] = config['environments'][:1]
    config['keyboard_steps'] = 0
    if selector is not None:
        config['visual_structure_scope'] = selector
    config_path = area/'config.json'
    audit.save(config_path, config)
    run = area/'run'
    command = subprocess.run([sys.executable, str(SCRIPTS/'audit.py'), 'page-audit', '--url', url,
        '--config', str(config_path), '--out', str(run), '--mode', 'machine', '--screenshots', 'off',
        '--max-states', '1', '--max-steps', '1'], capture_output=True, text=True, timeout=90)
    (area/'command.log').write_text(command.stdout + command.stderr)
    assert command.returncode == 0, command.stdout + command.stderr
    graph = page_explorer.status(run)
    rows = report_evidence(run, graph)
    assert not list(run.glob('evidence/*/*.png'))
    from openpyxl import load_workbook
    from visual_structure import REPORT_TITLE

    files = json.loads(command.stdout.strip().splitlines()[-1])
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
    assert all(worksheet.cell(index, 7).hyperlink.target == row['evidence'] for index in range(2, 2 + expected_rows))
    workbook.close()
    from page_workflow import next_work

    packets = next_work(run, url, limit=55)['next_cases']
    packet, = [item for item in packets if item['criterion'] == '1.3.1']
    assert packet['visual_structure_evidence'] == rows
    if selector == '#scope':
        heading, bullets = row['candidates']
        assert heading['kind'] == 'heading' and heading['target']['selector'] == '#scope-title'
        assert bullets['kind'] == 'list' and bullets['marker'] == '・'
        assert [item['selector'] for item in bullets['targets']] == ['#bullet-1', '#bullet-2', '#bullet-3']
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
        <hr>{items}</section>
        {heading_case('aria-heading', aria=True)}{list_case('aria-list', 'aria')}
        </main></body></html>''')
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(public))) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}/index.html'
        try:
            cases = [('declared', '#scope', 'collected'), ('semantic-control', '#aria-heading', 'collected'),
                     ('ambiguous', 'section', 'not_observed'),
                     ('disabled', None, 'disabled')]
            return {name: page_audit_case(out/name, url, selector, expected)
                    for name, selector, expected in cases}
        finally:
            server.shutdown()
            thread.join()


async def main(out):
    if out.exists():
        raise ValueError('試験結果には新しい保存先を指定する。')
    cases = [
        (heading_case('paragraph-heading'), '#paragraph-heading', ['heading']),
        (heading_case('html-heading', 'h2'), '#html-heading', []),
        (heading_case('aria-heading', aria=True), '#aria-heading', []),
        (heading_case('ordinary-emphasis', emphasis='lead'), '#ordinary-emphasis', []),
        (heading_case('styled-intro', label='はじめにお読みください'), '#styled-intro', ['heading']),
        (list_case('paragraph-list'), '#paragraph-list', ['list']),
        (list_case('html-list', 'native'), '#html-list', []),
        (list_case('aria-list', 'aria'), '#aria-list', []),
        (list_case('generated-list', marker=''), '#generated-list', []),
        (list_case('dot-in-prose', marker='', items=['フランス・ドイツの入国案内'] * 3), '#dot-in-prose', []),
        (list_case('too-short', items=ITEMS[:2]), '#too-short', []),
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
                for candidate in result['candidates']:
                    assert 'outcome' not in candidate
                observed.append(result)
            for first, second in (('#paragraph-heading', '#html-heading'), ('#paragraph-heading', '#aria-heading'),
                                  ('#paragraph-list', '#html-list'), ('#paragraph-list', '#aria-list')):
                assert appearances[first] == appearances[second], (first, second)
        finally:
            await browser.close()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'observed.json').write_text(json.dumps(observed, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({row['scope']: [c['kind'] for c in row['candidates']] for row in observed}, ensure_ascii=False))
    results = page_audit_cases(out)
    audit.save(out/'page-audit-observed.json', results)
    print(json.dumps(results, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    asyncio.run(main(parser.parse_args().out))
