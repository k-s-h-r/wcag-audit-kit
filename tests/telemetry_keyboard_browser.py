"""Exercise verified keyboard effects while blocking local telemetry and functional POSTs."""
import argparse
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys
from threading import Thread
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/wcag-audit-kit/scripts'))
import audit
import page_explorer


class Fixture(BaseHTTPRequestHandler):
    posts = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        self.posts.append(self.path)
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        variant = urlsplit(self.path).path
        if variant not in {'/disclosure', '/expanded', '/no-effect', '/functional'}:
            self.send_error(404)
            return
        target = {
            '/disclosure': '<details><summary id="menu">Menu</summary><p>Menu contents</p></details>',
            '/expanded': '<button id="menu" type="button" aria-expanded="false">Menu</button>',
            '/no-effect': '<button id="menu" type="button">No effect</button>',
            '/functional': '<button id="menu" type="button" aria-expanded="false">Menu</button>',
        }[variant]
        update = "menu.setAttribute('aria-expanded', 'true');" if variant in ('/expanded', '/functional') else ''
        if variant == '/functional':
            update += "fetch('/submit', {method:'POST', body:'update'}).catch(() => {});"
        content = f'''<!doctype html><html lang="en"><head><title>Keyboard receipt</title></head>
<body><main><h1>Keyboard receipt</h1>{target}</main><script>
navigator.sendBeacon('/cdn-cgi/rum', 'page-read');
const menu = document.querySelector('#menu');
menu.addEventListener('keydown', event => {{
  if (event.key !== 'Enter') return;
  navigator.sendBeacon('/cdn-cgi/rum', 'key-read');
  {update}
}});
</script></body></html>'''.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def trial(out, url, name, expected_pass):
    config = audit.init_config(url)
    config['environments'] = config['environments'][:1]
    config['keyboard_steps'] = 0
    config_path = out / f'{name}.json'
    audit.save(config_path, config)
    run_root = out / name
    command = ['page-audit', '--url', url, '--config', str(config_path), '--out', str(run_root),
               '--mode', 'machine', '--quick-explore', '--max-steps', '3']
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        assert audit.main(command) == 0
    files = json.loads(stdout.getvalue().splitlines()[-1])
    run = audit.run_layout.ledger(run_root)
    graph = page_explorer.status(run)
    edge, = [item for item in graph['edges'] if item['route'] and item['route'][-1]['type'] == 'key']
    assert not edge['error'] and not edge['native_events']
    assert len(edge['blocked_requests']) >= 2
    telemetry = {urlsplit(item['url']).path: item['telemetry'] for item in edge['blocked_requests']}
    assert telemetry.get('/cdn-cgi/rum') is True
    assert ('/submit' in telemetry) == (name == 'functional')
    if name == 'functional':
        assert telemetry['/submit'] is False
    effect = edge['key_effect']
    evidence = audit.load(run / edge['evidence_dir'] / 'input-events.json')
    key = evidence['events'][effect['event_index']]
    assert key['type'] == 'keydown' and key['key'] == 'Enter'
    assert key['isTrusted'] and key['expectedTargetMatched']
    if name == 'disclosure':
        assert effect['before']['open'] is False and effect['after']['open'] is True
    elif name in ('expanded', 'functional'):
        assert effect['before']['expanded'] == 'false' and effect['after']['expanded'] == 'true'
    else:
        assert effect['before'] == effect['after']
    report = audit.load(Path(files['json']))
    matches = [row for row in report['machine_checks'] if row['checkpoint'] == '実入力 / Enter']
    row, = matches
    assert row['outcome'] == ('passed' if expected_pass else 'cant_tell'), row
    assert not report['audit_complete']
    if expected_pass:
        assert '操作前後の状態が変わった' in row['observed']
        assert '操作前後の状態が変わった' in Path(files['html']).read_text()
    print(name, row['outcome'])


def main(out):
    out.mkdir(exist_ok=False, parents=True)
    with ThreadingHTTPServer(('127.0.0.1', 0), Fixture) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            for name, expected in [('disclosure', True), ('expanded', True), ('no-effect', False), ('functional', False)]:
                trial(out, f'http://127.0.0.1:{server.server_port}/{name}', name, expected)
            assert not Fixture.posts, Fixture.posts
        finally:
            server.shutdown()
            worker.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
