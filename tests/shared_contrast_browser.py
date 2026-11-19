"""Compare one shared footer link using evidence from real page-batch captures."""

import argparse
from functools import partial
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import quote, unquote, urljoin, urlsplit

from url_selection_browser import AUDIT, start_server, stop_server, write_json


sys.path.insert(0, str(AUDIT.parent))
from shared_contrast import compare


TARGET = '#shared-help'
ENVIRONMENT = 'desktop'
PATHS = ('/first', '/second', '/changed', '/missing', '/pending')


def file_hashes(root):
    return {file.relative_to(root): sha256(file.read_bytes()).hexdigest()
            for file in root.rglob('*') if file.is_file()}


def export_command(batch, *args):
    return subprocess.run([sys.executable, str(AUDIT), 'shared-contrast', '--batch', str(batch),
                           '--target', TARGET, '--environment', ENVIRONMENT, *args],
                          capture_output=True, text=True, timeout=30)


def verify_page_exports(out, batch, altered, urls, expected):
    assert json.loads(export_command(batch).stdout) == expected
    destination = out / 'page references'
    destination.mkdir()

    def export(source, label, url):
        file = destination / (label + '.html')
        result = export_command(source, '--page-exact', url, '--out', str(file))
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert json.loads(result.stdout) == {'html': str(file)}
        return file, file.read_text()

    first_file, first = export(batch, 'first page', urls[0])
    assert f'<th scope="row">{urls[0]}</th><td>このページ</td><td>通過（axe） 8.6:1' in first
    assert f'<th scope="row">{urls[1]}</th><td>同じ測定</td><td>通過（axe） 8.6:1' in first
    assert f'<th scope="row">{urls[2]}</th><td>異なる測定</td><td>問題あり（axe） 1.35:1' in first
    missing_row = next(row for row in first.split('<tr>') if f'<th scope="row">{urls[3]}</th>' in row)
    assert '<td>比較できず</td><td>収集失敗。' in missing_row and 'HTTP 404' in missing_row
    assert f'<th scope="row">{urls[4]}</th><td>比較できず</td><td>未着手' in first
    relative = re.findall(r'<a href="([^"]+)">axeの証拠</a><br><code>([a-f0-9]{64})</code>', first)
    proof = {(first_file.parent / unquote(link)).resolve(): checksum for link, checksum in relative}
    assert proof == {batch / row['evidence']: row['sha256'] for group in expected['groups'] for row in group['pages']}
    assert all(sha256(file.read_bytes()).hexdigest() == checksum for file, checksum in proof.items())
    assert first.index(urls[0], first.index('<tbody>')) < first.index(urls[1]) < first.index(urls[2])

    _, missing = export(batch, 'absent initial measurement', urls[3])
    assert f'<th scope="row">{urls[3]}</th><td>このページ</td><td>収集失敗' in missing
    assert f'<th scope="row">{urls[0]}</th><td>別のページで測定</td>' in missing
    assert '異なる測定' not in missing and '同じ測定' not in missing

    _, tampered = export(altered, 'failed evidence verification', urls[0])
    assert f'<th scope="row">{urls[0]}</th><td>このページ</td><td>測定を確認できず。' in tampered
    assert 'ハッシュを照合できない' in tampered
    assert expected['groups'][0]['pages'][0]['sha256'] not in tampered

    for options in (('--page-exact', urls[0]),
                    ('--page-exact', urls[0], '--out', str(first_file)),
                    ('--page-exact', urls[0], '--out', str(batch / 'unexpected.html')),
                    ('--page-exact', urls[0] + '/unknown', '--out', str(destination / 'unknown.html'))):
        error = export_command(batch, *options)
        assert error.returncode == 1, (error.stdout, error.stderr)
    assert first_file.read_text() == first
    assert not (destination / 'unknown.html').exists()
    assert not (batch / 'unexpected.html').exists()

    from playwright.sync_api import sync_playwright

    class QuietFiles(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server, worker = start_server(partial(QuietFiles, directory=str(out)))
    url = f'http://127.0.0.1:{server.server_port}/' + quote(first_file.relative_to(out).as_posix())
    try:
        with sync_playwright() as automation:
            browser = automation.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
            try:
                page = browser.new_page(viewport={'width': 320, 'height': 900})
                page.goto(url)
                assert page.get_by_role('heading', name='共通部品の文字コントラスト測定').is_visible()
                links = page.get_by_role('link', name='axeの証拠')
                assert links.count() == 3
                assert page.evaluate('document.documentElement.scrollWidth') <= 320
                for index, (link, checksum) in enumerate(relative):
                    assert links.nth(index).get_attribute('href') == link
                    receipt = page.request.get(urljoin(url, link))
                    assert receipt.ok and sha256(receipt.body()).hexdigest() == checksum
            finally:
                browser.close()
    finally:
        stop_server(server, worker)


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
    compare_input = file_hashes(altered)
    verify_page_exports(out, batch, altered, urls, comparison)
    assert file_hashes(batch) == before and file_hashes(altered) == compare_input
    assert visits == list(PATHS[:4]), visits
    print(json.dumps(comparison, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
