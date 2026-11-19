"""Compare one shared footer link using evidence from real page-batch captures."""

import argparse
from hashlib import sha256
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

from url_selection_browser import AUDIT, start_server, stop_server, write_json


sys.path.insert(0, str(AUDIT.parent))
from shared_contrast import compare


TARGET = '#shared-help'
ENVIRONMENT = 'desktop'
PATHS = ('/first', '/second', '/changed', '/missing', '/pending')


def file_hashes(root):
    return {file.relative_to(root): sha256(file.read_bytes()).hexdigest()
            for file in root.rglob('*') if file.is_file()}


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    visits = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/favicon.ico':
                self.send_error(404)
                return
            visits.append(path)
            if path == '/missing':
                self.send_error(404)
                return
            color = '#dddddd' if path == '/changed' else '#004a99'
            body = (f'<!doctype html><html lang="en"><title>Shared contrast fixture</title>'
                    f'<style>body {{background:#fff}} footer a {{color:{color}}}</style>'
                    '<main><h1>Local page</h1></main><footer><a id="shared-help" href="/help">Help</a></footer>'
                    '</html>').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server, worker = start_server(Handler)
    base = f'http://127.0.0.1:{server.server_port}'
    urls = [base + path for path in PATHS]
    config = out / 'config.json'
    batch = out / 'batch'
    write_json(config, {'schema_version': '1', 'url': base, 'level': 'AA', 'keyboard_steps': 1,
                        'scope': {'mode': 'configured', 'pages': urls},
                        'environments': [{'id': ENVIRONMENT, 'viewport': {'width': 1280, 'height': 900}, 'zoom': 1}]})
    try:
        job = subprocess.run([sys.executable, str(AUDIT), 'page-batch', '--config', str(config), '--out', str(batch),
                              '--max-pages-this-run', '4'], capture_output=True, text=True, timeout=90)
        assert job.returncode == 0, (job.stdout, job.stderr)
        assert json.loads(job.stdout)['counts'] == {'completed': 3, 'failed': 1, 'pending': 1, 'interrupted': 0}
        assert visits == list(PATHS[:4]), visits
    finally:
        stop_server(server, worker)

    before = file_hashes(batch)
    comparison = compare(batch, target=TARGET, environment=ENVIRONMENT)
    first, changed = comparison['groups']
    assert [row['url'] for row in first['pages']] == urls[:2] and [row['url'] for row in changed['pages']] == urls[2:3]
    assert first['observation']['node']['html'] == changed['observation']['node']['html']
    assert [group['observation']['bucket'] for group in (first, changed)] == ['passes', 'violations']
    assert [group['observation']['node']['any'][0]['data']['contrastRatio'] for group in (first, changed)] == [8.6, 1.35]
    assert [(row['url'], row['status']) for row in comparison['unavailable']] == list(zip(urls[3:], ('failed', 'pending')))
    assert 'HTTP 404' in comparison['unavailable'][0]['reason']
    for group in comparison['groups']:
        for row in group['pages']:
            assert before[Path(row['evidence'])] == row['sha256']
            assert json.loads((batch / row['evidence']).read_text())['url'] == row['url']
    absent = compare(batch, target='#absent', environment=ENVIRONMENT)
    assert not absent['groups'] and [row['url'] for row in absent['unavailable']] == urls
    assert [row['evidence'] for row in absent['unavailable'][:2]] == [row['evidence'] for row in first['pages']]
    other = compare(batch, target=TARGET, environment='unmeasured')
    assert not other['groups'] and [row['url'] for row in other['unavailable']] == urls
    assert file_hashes(batch) == before

    altered = shutil.copytree(batch, out / 'altered-copy')
    changed_file = altered / first['pages'][0]['evidence']
    changed_file.write_bytes(changed_file.read_bytes() + b'\n')
    result = compare(altered, target=TARGET, environment=ENVIRONMENT)
    assert [row['url'] for group in result['groups'] for row in group['pages']] == urls[1:3]
    assert result['unavailable'][0]['url'] == urls[0] and 'ハッシュ' in result['unavailable'][0]['reason']
    print(json.dumps(comparison, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
