"""Check generated targets and keyboard evidence against a local Chromium fixture."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from threading import Thread

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
</main>
<footer><a href="/other#footer">受付</a></footer>
<script>
const shadow = document.getElementById('component').attachShadow({mode:'open'});
shadow.innerHTML = `<div id="group">
  <button type="button" onclick="this.textContent='第1ボタン操作後'">第1ボタン</button>
  <div><button type="button">第2ボタン</button></div>
</div>`;
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
    config_path = out / 'config.json'
    target = out / 'run'
    audit.save(config_path, config)
    try:
        assert audit.main(['page-audit', '--mode', 'machine', '--url', url, '--out', str(target),
                           '--config', str(config_path), '--max-depth', '1', '--max-steps', '50']) == 0
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

        report, = target.glob('page-*-report.json')
        rows = [row for row in audit.load(report)['machine_checks'] if row['criterion'] == '2.1.1']
        assert all(row['target'] not in {'#main', '#passive'} for row in rows)
        assert any(row['target'] == link and row['outcome'] == 'passed' for row in rows)
        assert any(row['target'] == '#event' and row['outcome'] == 'failed' for row in rows)
        print('Real skip-link input, open shadow input and passive destination exclusion verified.')
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out.resolve())
