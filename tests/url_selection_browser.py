"""Measure configured and discovered URLs, including redirect boundaries, in Chromium."""

import argparse
import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
from threading import Thread
from urllib.parse import urlsplit

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'skills/wcag-audit-kit/scripts/audit.py'
START = ('/', '/unlinked')
LINKED = ('/a', '/query?view=one', '/query?view=two', '/app#one', '/app#two', '/missing', '/dynamic')
CONFIGURED = ('/a', './a', '/query?view=one', '/query?view=two', '/app#one', '/app#two', '/missing')


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')


def start_server(handler):
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    return server, worker


def stop_server(server, worker):
    server.shutdown()
    server.server_close()
    worker.join(timeout=5)


def serve():
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            path = urlsplit(self.path).path
            requests.append(self.path)
            if path == '/':
                body = ''.join(f'<a href="{url}">{index}</a>' for index, url in enumerate(LINKED))
                body += ('<a href="./a">duplicate</a><a href="/excluded/path">excluded</a>'
                         '<a href="http://127.0.0.1:9/foreign">other origin</a>')
            elif path == '/dynamic':
                body = ('<button onclick="this.insertAdjacentHTML(\'afterend\','
                        '\'<a href=/hidden>Added link</a>\')">Show</button>')
            else:
                body = '<p>Local fixture page</p>'
            data = f'<!doctype html><title>Local URL fixture</title><main>{body}</main>'.encode()
            self.send_response(404 if path == '/missing' else 200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return (*start_server(Handler), requests)


def redirect_observations(out):
    requests = []
    foreign_requests = []
    received_session_cookie = {}

    class ForeignHandler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            foreign_requests.append(self.path)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'<title>Other origin</title>')

    foreign, foreign_worker = start_server(ForeignHandler)
    foreign_url = f'http://127.0.0.1:{foreign.server_port}/cross-port?probe=one'

    class RedirectHandler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            requests.append(self.path)
            path = urlsplit(self.path).path
            redirects = {
                '/redirect/start': (302, 'step?hop=one'),
                '/redirect/step': (307, 'nested/final?from=step#details'),
                '/redirect/out': (302, '/excluded/never?probe=one'),
                '/redirect/cross': (302, 'cross-step'),
                '/redirect/cross-step': (307, foreign_url),
                '/loop': (302, '/loop'),
            }
            if path in redirects:
                status, target = redirects[path]
                self.send_response(status)
                self.send_header('Location', target)
                if path == '/redirect/start':
                    self.send_header('Set-Cookie', 'redirect_fixture=accepted; Path=/redirect/; HttpOnly')
                self.end_headers()
                return
            if path in ('/redirect/nested/final', '/redirect/nested/result'):
                cookies = self.headers.get('Cookie', '').split('; ')
                received_session_cookie[path] = 'redirect_fixture=accepted' in cookies
            if path == '/':
                body = ('<a href="/redirect/start">Allowed redirect</a>'
                        '<a href="/redirect/out">Excluded redirect</a>'
                        '<a href="/redirect/cross">Other origin after a hop</a>'
                        '<a href="/client">Client redirect</a>'
                        '<a href="/loop">Redirect loop</a>')
            elif path == '/redirect/nested/final':
                body = '<a href="result?source=final#one">Relative link after a redirect</a>'
            elif path == '/client':
                body = '<script>location.replace("/excluded/client")</script>'
            elif path == '/redirect/nested/result':
                body = '<a href="/after-recovery?ready=1">Link after browser recovery</a>'
            else:
                body = '<p>Local redirect fixture</p>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(f'<!doctype html><title>Local redirect fixture</title>{body}'.encode())

    primary, primary_worker = start_server(RedirectHandler)
    base = f'http://127.0.0.1:{primary.server_port}'
    try:
        value = execute(out, base, 'discover', 20)
    finally:
        stop_server(primary, primary_worker)
        stop_server(foreign, foreign_worker)
    return {
        'base': base,
        'foreign_url': foreign_url,
        'pages': value['pages'],
        'errors': value['errors'],
        'unvisited': value['unvisited'],
        'requests': requests,
        'foreign_requests': foreign_requests,
        'received_session_cookie': received_session_cookie,
    }


def check_redirects(observed):
    base = observed['base']
    by_url = {page['url']: page for page in observed['pages']}
    result_url = base + '/redirect/nested/result?source=final#one'
    assert by_url[result_url]['source'] == base + '/redirect/start', observed
    assert by_url[result_url]['visited'] is True and not observed['unvisited'], observed
    assert by_url[base + '/after-recovery?ready=1']['source'] == result_url, observed
    assert '/after-recovery?ready=1' in observed['requests'], observed
    assert observed['received_session_cookie'] == {'/redirect/nested/final': True, '/redirect/nested/result': True}, observed
    assert [path for path in observed['requests'] if path.startswith('/redirect/')] == [
        '/redirect/start', '/redirect/step?hop=one', '/redirect/nested/final?from=step',
        '/redirect/out', '/redirect/cross', '/redirect/cross-step', '/redirect/nested/result?source=final',
    ], observed
    assert observed['foreign_url'] not in by_url and not observed['foreign_requests'], observed
    assert not any(path.startswith('/excluded/') for path in observed['requests']), observed
    assert not any(urlsplit(url).path.startswith('/excluded/') for url in by_url), observed
    errors = {row['url']: row['error'] for row in observed['errors']}
    for path in ('/redirect/out', '/redirect/cross', '/client'):
        assert '範囲外' in errors.get(base + path, ''), observed
    assert by_url[base + '/client']['visited'] is True and '/client' in observed['requests'], observed
    assert base + '/loop' in errors and 2 <= observed['requests'].count('/loop') <= 25, observed
    assert set(errors) == {base + path for path in ('/redirect/out', '/redirect/cross', '/client', '/loop')}, observed


def execute(out, base, mode, budget):
    config = dict(schema_version='1', level='AA', url=base, scope=dict(mode=mode, include=['/**'], seeds=['/'], known_pages=['/unlinked'],
                                     max_pages=budget, exclude=[dict(path='/excluded/**', reason='Fixture boundary')]))
    if mode == 'configured':
        config['scope']['pages_file'] = 'configured-urls.json'
    name = f'{mode}-{budget}'
    config_file = out / f'{name}-config.json'
    manifest = out / f'{name}.json'
    write_json(config_file, config)
    completed = subprocess.run([sys.executable, str(AUDIT), 'pages', '--config', str(config_file),
                                '--out', str(manifest)], capture_output=True, text=True, timeout=90)
    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary['wcag_inspection_executed'] is False
    return json.loads(manifest.read_text())


async def prove_dynamic_link(base):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        try:
            page = await browser.new_page()
            await page.goto(base + '/dynamic', wait_until='domcontentloaded')
            link = page.get_by_role('link', name='Added link')
            assert await link.count() == 0
            await page.get_by_role('button', name='Show').click()
            assert await link.get_attribute('href') == '/hidden'
        finally:
            await browser.close()


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    server, worker, requests = serve()
    base = f'http://127.0.0.1:{server.server_port}'
    expected = [base + path for path in START + LINKED]
    write_json(out / 'plan.json', dict(base=base, expected_candidates=expected, operation_only=base + '/hidden',
                                      expected_limit=2, configuration=list(CONFIGURED)))
    write_json(out / 'configured-urls.json', list(CONFIGURED))
    observations = {}
    try:
        for mode, budget in (('configured', 20), ('discover', 20), ('discover', 2)):
            before = len(requests)
            value = execute(out, base, mode, budget)
            observed = {page['url']: page for page in value['pages']}
            visited = [url for url, page in observed.items() if page['visited']]
            assert value['inventory_complete'] is False and len(observed) == len(value['pages'])
            if mode == 'configured':
                assert list(observed) == [base + path for path in LINKED[:-1]]
                assert len(requests) == before and not visited and not value['errors'] and not value['unvisited']
                assert all(page['source'] == 'configured' for page in observed.values())
            else:
                assert set(observed) == set(expected) and sources_are_recorded(observed, base)
                if budget == 2:
                    assert visited == [base + path for path in START] and set(value['unvisited']) == set(expected) - set(visited)
                    assert not value['errors']
                else:
                    assert set(visited) == set(expected) and not value['unvisited']
                    assert value['errors'] == [dict(url=base + '/missing', error='HTTP 404')]
            observations[f'{mode}-{budget}'] = dict(candidates=len(observed), visited=len(visited),
                                                  queued=len(value['unvisited']), errors=len(value['errors']),
                                                  requests=requests[before:])
        asyncio.run(prove_dynamic_link(base))
        observations['operation_only_link'] = '/hidden'
    finally:
        stop_server(server, worker)
    redirect_out = out / 'redirects'
    redirect_out.mkdir()
    observations['redirects'] = redirect_observations(redirect_out)
    write_json(out / 'observed.json', observations)
    check_redirects(observations['redirects'])
    print(json.dumps(observations, ensure_ascii=False))


def sources_are_recorded(observed, base):
    return (all(observed[base + path]['source'] == 'configured_start' for path in START)
            and all(observed[base + path]['source'] == base + '/' for path in LINKED)
            and not any(path.startswith('/excluded/') or path == '/foreign'
                        for path in (urlsplit(url).path for url in observed)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
