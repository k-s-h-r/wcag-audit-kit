"""Compare direct and proxy-routed HTTPS using two loopback audit fixtures."""

import argparse
import base64
from collections import Counter
from hashlib import sha256
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
from selectors import DefaultSelector, EVENT_READ
import shlex
import shutil
from socket import create_connection
import ssl
import subprocess
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from measure import Fixture, HOST, fixture_page, origin, run_audit, save, send, server, summarize


class ConnectProxy(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def reject(self):
        self.server.record.append({'method': self.command, 'url': self.path, 'forwarded': False})
        send(self, 403, b'Outside fixture policy')

    do_GET = do_HEAD = do_OPTIONS = do_POST = reject

    def do_CONNECT(self):
        if self.path != f'{HOST}:{self.server.fixture_port}':
            self.reject()
            return
        receipt = {'method': self.command, 'url': self.path, 'forwarded': False}
        self.server.record.append(receipt)
        try:
            with create_connection((HOST, self.server.fixture_port), timeout=8) as upstream:
                self.connection.settimeout(8)
                self.send_response_only(200, 'Connection Established')
                self.end_headers()
                receipt['forwarded'] = True
                self.relay(upstream)
        except OSError:
            self.close_connection = True

    def relay(self, upstream):
        with DefaultSelector() as selector:
            selector.register(self.connection, EVENT_READ, upstream)
            selector.register(upstream, EVENT_READ, self.connection)
            while ready := selector.select(timeout=8):
                for connection, _ in ready:
                    chunk = connection.fileobj.recv(16384)
                    if not chunk:
                        return
                    connection.data.sendall(chunk)


def certificate(directory):
    pem = directory / 'certificate.pem'
    key = directory / 'key.pem'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-noenc', '-sha256', '-days', '1',
                    '-subj', f'/CN={HOST}', '-addext', f'subjectAltName=IP:{HOST}',
                    '-keyout', str(key), '-out', str(pem)], check=True, capture_output=True)
    public_key = subprocess.check_output(['openssl', 'x509', '-in', str(pem), '-pubkey', '-noout'])
    spki = subprocess.run(['openssl', 'pkey', '-pubin', '-outform', 'DER'], input=public_key,
                          capture_output=True, check=True).stdout
    pin = base64.b64encode(sha256(spki).digest()).decode()
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(pem, key)
    return tls, pem, pin


def chromium_environment(output, pin, proxy):
    chromium = shutil.which('chromium')
    if not chromium:
        raise FileNotFoundError('chromium')
    args = [chromium, f'--ignore-certificate-errors-spki-list={pin}', '--disable-background-networking']
    if proxy is not None:
        args.extend([f'--proxy-server={origin(proxy)}', '--proxy-bypass-list=<-loopback>'])
    wrapper = output / 'chromium'
    wrapper.write_text(f'#!/bin/sh\nexec {shlex.join(args)} "$@"\n')
    wrapper.chmod(0o700)
    environment = dict(os.environ, PATH=str(output) + os.pathsep + os.environ['PATH'])
    return environment, args


def measure(output, tls, pin, *, protected):
    output.mkdir()
    with server(Fixture, tls=tls) as primary, server(Fixture, tls=tls) as other, server(ConnectProxy) as proxy:
        other.page = None
        primary.other_origin = f'https://{HOST}:{other.server_port}'
        primary.page = fixture_page(primary.other_origin)
        url = f'https://{HOST}:{primary.server_port}/'
        proxy.fixture_port = primary.server_port
        environment, args = chromium_environment(output, pin, proxy if protected else None)
        save(output / 'settings.json', {'url': url, 'other_origin': primary.other_origin,
                                        'proxy': origin(proxy) if protected else None, 'browser_arguments': args})
        try:
            run_audit(output, url, environment)
        finally:
            save(output / 'primary-received.json', primary.record)
            save(output / 'other-received.json', other.record)
            save(output / 'proxy.json', proxy.record)
        summarize(output)


def compare(output):
    direct, guarded = (json.loads((output / f'{name}.json').read_text()) for name in ('direct', 'guarded'))
    baseline = Counter(row['path'] for row in direct['other'])
    assert set(baseline) == {'/initial-other.svg', '/action-get', '/action-image.svg', '/after-redirect'}, baseline
    assert all(row['method'] == 'GET' and not row['upgrade'] for row in direct['other'])
    assert guarded['other'] == [], guarded['other']
    allowed = urlsplit(guarded['settings']['url']).netloc
    denied = urlsplit(guarded['settings']['other_origin']).netloc
    wanted = Counter((row['url'], row['forwarded']) for row in guarded['proxy'] if row['method'] == 'CONNECT')
    assert wanted[allowed, True] > 0 and wanted[denied, False] > 0
    assert all(row['method'] == 'CONNECT' and row['url'] == allowed for row in guarded['proxy'] if row['forwarded'])
    assert all('日時を取得できません' not in row['observed_text'] and '日時を取得' in row['observed_text']
               for row in direct['operations'].values())
    assert all('日時を取得できません' in row['observed_text'] for row in guarded['operations'].values())
    same_origin = {name: sum(row['path'] == '/action-same' and row['method'] == 'GET' for row in log['primary'])
                   for name, log in (('direct', direct), ('guarded', guarded))}
    assert same_origin['direct'] == same_origin['guarded'] > 0, same_origin
    save(output / 'comparison.json', {'direct_other_GET': dict(baseline), 'guarded_other_requests': 0,
                                      'same_origin_action_GET': same_origin,
                                      'allowed_CONNECT': wanted[allowed, True], 'denied_CONNECT': wanted[denied, False]})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    output = parser.parse_args().out.resolve()
    output.mkdir(parents=True)
    with TemporaryDirectory(prefix='wcag-loopback-tls-') as temporary:
        tls, pem, pin = certificate(Path(temporary))
        shutil.copyfile(pem, output / 'certificate.pem')
        measure(output / 'direct', tls, pin, protected=False)
        measure(output / 'guarded', tls, pin, protected=True)
    compare(output)
