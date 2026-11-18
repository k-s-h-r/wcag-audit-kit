"""Measure configured and discovered URLs against an owned Chromium fixture."""

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

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    return server, worker, requests


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
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    write_json(out / 'observed.json', observations)
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
