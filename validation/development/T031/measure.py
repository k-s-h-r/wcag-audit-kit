"""Measure browser requests with two local origins and an optional local HTTP proxy."""

import argparse
from collections import Counter
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from threading import Thread
from urllib.parse import urlsplit


REPO = Path(__file__).resolve().parents[3]
CLI = REPO / 'skills' / 'wcag-audit-kit' / 'scripts' / 'audit.py'
HOST = '127.0.0.1'
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"><rect width="8" height="8"/></svg>'


def send(handler, status, body=b'', headers=None):
    handler.send_response(status)
    for name, value in (headers or {}).items():
        handler.send_header(name, value)
    handler.send_header('Content-Length', str(len(body)))
    handler.end_headers()
    if handler.command != 'HEAD':
        handler.wfile.write(body)


class Fixture(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def handle_request(self):
        path = urlsplit(self.path).path
        self.server.record.append({'method': self.command, 'path': path,
                                   'upgrade': self.headers.get('Upgrade')})
        headers = {'Cache-Control': 'no-store', 'Access-Control-Allow-Origin': '*'}
        if self.server.page and path == '/':
            headers['Content-Type'] = 'text/html; charset=utf-8'
            send(self, 200, self.server.page, headers)
        elif self.server.page and path == '/redirect':
            headers['Location'] = self.server.other_origin + '/after-redirect'
            send(self, 302, headers=headers)
        elif path.endswith('.svg'):
            headers['Content-Type'] = 'image/svg+xml'
            send(self, 200, SVG, headers)
        else:
            send(self, 200, b'fixture', headers)

    do_GET = do_HEAD = do_OPTIONS = do_POST = handle_request


class Proxy(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def handle_request(self):
        url = urlsplit(self.path)
        allowed = (self.command in {'GET', 'HEAD', 'OPTIONS'} and url.scheme == 'http'
                   and url.netloc == self.server.allowed and not self.headers.get('Upgrade'))
        self.server.record.append({'method': self.command, 'url': self.path, 'forwarded': allowed})
        if not allowed:
            send(self, 403, b'Outside fixture policy')
            return
        path = url.path or '/'
        if url.query:
            path += '?' + url.query
        connection = HTTPConnection(HOST, self.server.fixture_port, timeout=5)
        try:
            connection.request(self.command, path)
            response = connection.getresponse()
            headers = {key: value for key, value in response.getheaders()
                       if key.lower() in {'location', 'content-type', 'cache-control',
                                          'access-control-allow-origin'}}
            send(self, response.status, response.read(), headers)
        finally:
            connection.close()

    do_GET = do_HEAD = do_OPTIONS = do_POST = do_CONNECT = handle_request


@contextmanager
def server(handler, *, tls=None):
    with ThreadingHTTPServer((HOST, 0), handler) as endpoint:
        endpoint.record = []
        if tls is not None:
            endpoint.socket = tls.wrap_socket(endpoint.socket, server_side=True)
        thread = Thread(target=endpoint.serve_forever, daemon=True)
        thread.start()
        try:
            yield endpoint
        finally:
            endpoint.shutdown()
            thread.join()


def origin(endpoint):
    return f'http://{HOST}:{endpoint.server_port}'


def fixture_page(other):
    websocket_origin = other.replace('https:', 'wss:', 1).replace('http:', 'ws:', 1)
    return f'''<!doctype html><html lang="ja"><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>通信を記録する対照</title>
<main><h1>見学予定</h1><img src="/initial-same.svg" alt="">
<img src="{other}/initial-other.svg" alt="">
<button id="open" type="button">候補を開く</button><p id="state">閉じています</p>
<p id="result"></p></main>
<script>
document.querySelector('#open').addEventListener('click', () => {{
  if (document.querySelector('#state').textContent === '候補を表示しました') return;
  document.querySelector('#state').textContent = '候補を表示しました';
  fetch('/action-same').catch(() => {{}});
  fetch('{other}/action-get').then(r => {{
    document.querySelector('#result').textContent = r.ok ? '日時を取得' : '日時を取得できません';
  }}).catch(() => {{ document.querySelector('#result').textContent = '日時を取得できません'; }});
  const img = document.createElement('img');
  img.src = '{other}/action-image.svg';
  img.alt = '';
  document.querySelector('main').append(img);
  fetch('/redirect').catch(() => {{}});
  fetch('{other}/action-post', {{method: 'POST', body: 'local-fixture'}}).catch(() => {{}});
  new WebSocket('{websocket_origin}/action-websocket');
}});
</script></html>'''.encode()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run_audit(output, url, environment):
    common = [sys.executable, str(CLI), 'page-audit', '--url', url, '--out', str(output / 'audit')]
    phases = {
        'initial': ['--mode', 'machine', '--screenshots', 'initial', '--initial-only'],
        'explore': ['--resume', '--quick-explore', '--max-steps', '10'],
    }
    save(output / 'commands.json', {label: common + flags for label, flags in phases.items()})
    for label, flags in phases.items():
        with (output / f'{label}.log').open('w') as log:
            subprocess.run(common + flags, env=environment, cwd=REPO, stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=180)


def measure(output, *, protected):
    output.mkdir()
    with server(Fixture) as primary, server(Fixture) as other, server(Proxy) as proxy:
        other.page = None
        primary.other_origin = origin(other)
        primary.page = fixture_page(primary.other_origin)
        url = origin(primary) + '/'
        proxy.fixture_port = primary.server_port
        proxy.allowed = urlsplit(url).netloc
        environment = dict(os.environ)
        wrapper = None
        if protected:
            chromium = shutil.which('chromium')
            if not chromium:
                raise FileNotFoundError('chromium')
            wrapper = output / 'chromium'
            args = [chromium, f'--proxy-server={origin(proxy)}', '--proxy-bypass-list=<-loopback>']
            wrapper.write_text(f'#!/bin/sh\nexec {shlex.join(args)} "$@"\n')
            wrapper.chmod(0o700)
            environment['PATH'] = str(output) + os.pathsep + environment['PATH']
        save(output / 'settings.json', {'url': url, 'other_origin': primary.other_origin,
                                        'proxy': origin(proxy) if protected else None,
                                        'chromium_wrapper': wrapper.name if wrapper else None})
        try:
            run_audit(output, url, environment)
        finally:
            save(output / 'primary-received.json', primary.record)
            save(output / 'other-received.json', other.record)
            save(output / 'proxy.json', proxy.record)


def summarize(output):
    read = lambda name: json.loads((output / name).read_text())
    work = output / 'audit' / 'work'
    graph = read('audit/work/exploration.json')
    button_edges = [edge for edge in graph['edges']
                    if edge['route'] and edge['route'][-1]['selector'] == '#open'
                    and edge['route'][-1]['type'] in {'click', 'key'}]
    records = {}
    for edge in button_edges:
        if edge['route'] != [{'selector': '#open', 'type': 'key', 'key': 'Enter'}]:
            continue
        path = work / edge['evidence_dir']
        event = json.loads((path / 'input-events.json').read_text())['events'][edge['key_effect']['event_index']]
        assert event['type'] == 'keydown' and event['key'] == 'Enter'
        assert event['isTrusted'] and event['expectedTargetMatched'] and event['target']['id'] == 'open'
        inventory = json.loads((path / 'inventory.json').read_text())
        assert '候補を表示しました' in inventory['text']
        assert any(item['method'] == 'POST' and urlsplit(item['url']).path == '/action-post'
                   for item in edge['blocked_requests'])
        records[edge['environment']] = {'viewport': inventory['viewport'], 'route': edge['route'],
                                        'event': event, 'blocked_requests': edge['blocked_requests'],
                                        'observed_text': inventory['text'], 'evidence': edge['evidence_dir']}
    assert set(records) == {'desktop', 'narrow'}, records
    report = read('audit/data/report.json')
    assert report['scope_conformance']['status'] == 'unverified' and not report['audit_complete']
    primary_log = read('primary-received.json')
    other_log = read('other-received.json')
    proxy_log = read('proxy.json')
    save(output.parent / f'{output.name}.json', {'settings': read('settings.json'),
                                                 'commands': read('commands.json'),
                                                 'operations': records, 'primary': primary_log,
                                                 'other': other_log, 'proxy': proxy_log,
                                                 'scope_status': report['scope_conformance']['status']})
    counts = lambda requests: dict(Counter(f"{item['method']} {item['path']}" for item in requests))
    denied = Counter(urlsplit(item['url']).path for item in proxy_log
                     if not item['forwarded'] and urlsplit(item['url']).hostname == HOST)
    return {'primary_received': counts(primary_log), 'other_received': counts(other_log),
            'proxy_denied_fixture_paths': dict(denied), 'blocked_by_explorer': ['/action-post'],
            'observed_result_text': sorted({record['observed_text'].splitlines()[-1]
                                            for record in records.values()}),
            'environments_with_operation': sorted(records), 'scope_status': report['scope_conformance']['status']}


def main(output):
    output.mkdir(parents=True)
    measure(output / 'standard', protected=False)
    measure(output / 'proxy', protected=True)
    standard = summarize(output / 'standard')
    proxy = summarize(output / 'proxy')
    expected_other = {'GET /initial-other.svg', 'GET /action-get', 'GET /action-image.svg', 'GET /after-redirect'}
    assert expected_other <= standard['other_received'].keys(), standard
    assert not {'POST /action-post', 'GET /action-websocket'} & standard['other_received'].keys(), standard
    assert not proxy['other_received'], proxy
    assert {request.split()[1] for request in expected_other} <= set(proxy['proxy_denied_fixture_paths']), proxy
    assert all('GET /action-same' in run['primary_received'] for run in (standard, proxy))
    assert '日時を取得' in standard['observed_result_text'], standard
    assert '日時を取得できません' in proxy['observed_result_text'], proxy
    result = {'standard': standard, 'proxy': proxy}
    save(output / 'summary.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out.resolve())
