"""Check generated targets and keyboard evidence against a local Chromium fixture."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import sys
from threading import Thread

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/wcag-audit-kit/scripts'))

import audit
from page_explorer import status


HTML = '''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><title>探索対象</title></head>
<body>
<a href="#main">本文へ移動</a>
<nav aria-label="主な案内"><a href="/other">案内</a></nav>
<main id="main" tabindex="-1">
  <h1>探索対象</h1>
  <p id="passive" tabindex="-1">プログラムでのみフォーカスする段落</p>
  <div id="ordinary-tabstop" tabindex="0">通常のTab停止位置</div>
  <button id="native" tabindex="-1" type="button">ネイティブ</button>
  <div id="aria" tabindex="-1" role="button">ARIA</div>
  <div id="event" tabindex="-1" onpointerup="this.textContent='操作後'">ポインター操作</div>
  <div id="cursor" tabindex="-1" style="cursor:pointer">ポインターの見た目</div>
  <div id="component"></div>
  <div id="overlap-host"><div id="lookalike"><button type="button">ライト側</button></div></div>
</main>
<footer><a href="/other#footer">受付</a></footer>
<script>
const shadow = document.getElementById('component').attachShadow({mode:'open'});
shadow.innerHTML = `<div id="group">
  <button type="button" onclick="this.textContent='第1ボタン操作後'">第1ボタン</button>
  <div><button type="button">第2ボタン</button></div>
</div>`;
document.getElementById('overlap-host').attachShadow({mode:'open'}).innerHTML =
  '<div id="lookalike"><button type="button">シャドウの同形ボタン</button></div>';
</script>
</body></html>'''.encode()


def enter_evidence(run, graph, selector):
    route = [{'selector': selector, 'type': 'key', 'key': 'Enter'}]
    edge, = [edge for edge in graph['edges'] if edge['route'] == route]
    assert edge['error'] is None, edge
    evidence = run / edge['evidence_dir']
    events = audit.load(evidence / 'input-events.json')['events']
    assert any(event['type'] == 'keydown' and event['key'] == 'Enter'
               and event['isTrusted'] for event in events), events
    return audit.load(evidence / 'state.json')


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            requests.append(self.path)
            if self.path != '/':
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    url = f'http://127.0.0.1:{server.server_port}/'
    config = audit.init_config(url)
    config.update(environments=config['environments'][:1], keyboard_steps=8)
    config['keyboard_checks'] = [{'id': 'missing-result', 'name': '操作後の表示を確認', 'criterion': '2.1.1',
        'steps': [{'key': 'Tab', 'focus': 'a[href="#main"]'}, {'key': 'Enter', 'visible': '#missing-panel'}]}]
    config_path = out / 'config.json'
    target = out / 'run'
    audit.save(config_path, config)
    try:
        assert audit.main(['page-audit', '--mode', 'machine', '--url', url, '--out', str(target),
                           '--config', str(config_path), '--max-depth', '1', '--max-steps', '50']) == 0
        target = audit.run_layout.ledger(target)
        files = audit.run_layout.report_files(target, single=True)
        graph = status(target)
        initial, = [node for node in graph['nodes'] if not node['route']]
        controls = {control['selector']: control for control in initial['controls']}
        labels = {control['label']: selector for selector, control in controls.items()}

        link = labels['本文へ移動']
        destination = enter_evidence(target, graph, link)
        assert destination['url'] == url + '#main' and destination['focus']['selector'] == '#main'
        assert {'#main', '#passive'}.isdisjoint(controls)
        assert {'#ordinary-tabstop', '#native', '#aria', '#event', '#cursor'} <= controls.keys()

        changed = enter_evidence(target, graph, labels['第1ボタン'])
        assert any(c['label'] == '第1ボタン操作後' for c in changed['controls']), changed
        assert labels['第1ボタン'] != labels['第2ボタン']
        enter_evidence(target, graph, labels['第2ボタン'])
        assert '/other' not in requests

        report = files.json
        rows = [row for row in audit.load(report)['machine_checks'] if row['criterion'] == '2.1.1']
        assert all(row['target'] not in {'#main', '#passive'} for row in rows)
        assert any(row['target'] == link and row['outcome'] == 'passed' for row in rows)
        ambiguous = labels['シャドウの同形ボタン']
        observed = {}
        for selector, expected in ((ambiguous, 'cant_tell'), ('#event', 'failed')):
            row, = [item for item in rows if item['target'] == selector and item['checkpoint'] == '実入力 / Enter']
            transition = target / row['evidence']
            record = audit.load(transition)
            events = audit.load(transition.with_name('input-events.json'))['events']
            keys = {event['key'] for event in events if event['type'] == 'keydown' and event['isTrusted']}
            if selector == ambiguous:
                assert 'strict mode violation' in record['error'] and not keys, (row, keys)
            else:
                assert 'Tab' in keys and 'Enter' not in keys and record['keyboard_unreachable_step'] == 1, (row, keys)
            observed[selector] = (row, expected)
        assert all(row['outcome'] == expected for row, expected in observed.values()), observed

        mismatch, = [row for row in rows if row['checkpoint'] == 'キーボード経路 / missing-result']
        receipt = audit.load(target / mismatch['evidence'])
        assert mismatch['outcome'] == 'failed' and receipt['steps'][-1]['input_event_index']
        assert any(not item['matched'] for item in receipt['steps'][-1]['conditions'])

        report_html = files.html
        html_rows = re.findall(r'<tr>.*?</tr>', report_html.read_text(), re.DOTALL)
        findings = ((ambiguous, '機械判定不能'), ('#event', '問題あり（機械）'),
                    ('#missing-panel', '問題あり（機械）'))
        for marker, label in findings:
            assert any(escape(marker) in row and label in row for row in html_rows), (marker, label)
        report_excel = files.excel
        workbook = load_workbook(report_excel, read_only=True)
        try:
            issue_rows = list(workbook['自動検出した問題'].values)
            for marker, label in findings:
                assert any(label in row and any(marker in str(cell) for cell in row) for row in issue_rows), (marker, label)
        finally:
            workbook.close()
        print('Real keyboard input, unreachable target, pre-input locator error and report formats verified.')
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out.resolve())
