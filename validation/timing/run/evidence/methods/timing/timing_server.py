"""Owned local timing calibration service; no real accounts or stored form data."""
import argparse
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import time
from urllib.parse import parse_qs, urlsplit

SESSIONS = {}
SOURCE = Path(__file__).with_name('timing.html')


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, value, cookie=None):
        data = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        if cookie:
            self.send_header('Set-Cookie', 'calibration_session='+cookie+'; HttpOnly; SameSite=Strict; Path=/')
        self.end_headers()
        self.wfile.write(data)

    def session(self):
        cookies = SimpleCookie(self.headers.get('Cookie', ''))
        token = cookies.get('calibration_session')
        return SESSIONS.get(token.value) if token else None

    def status(self, session):
        remaining = None if session['off'] else max(0, (session['expires']-time.monotonic())*1000)
        return {'active': remaining is None or remaining > 0, 'remaining_ms': remaining,
                'duration_ms': session['duration']*1000, 'extension_count': session['extensions'],
                'extension_limit': 10 if session['variant']=='good' else 1,
                'warning_at_remaining_ms': 23000 if session['variant']=='good' else 2000}

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/timing.html':
            data = SOURCE.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)
        elif path == '/status' and self.session():
            self.reply(200, self.status(self.session()))
        else:
            self.reply(404, {'error': 'not found'})

    def do_POST(self):
        path = urlsplit(self.path).path
        length = int(self.headers.get('Content-Length', 0))
        if length > 10000:
            self.reply(413, {'error': 'fixture payload too large'})
            return
        body = json.loads(self.rfile.read(length) or '{}')
        if path == '/start':
            variant = body.get('variant')
            if variant not in {'good', 'bad'}:
                self.reply(400, {'error': 'unknown variant'})
                return
            token = secrets.token_hex(16)
            duration = 26 if variant=='good' else 6
            SESSIONS[token] = {'variant':variant, 'duration':duration, 'off':bool(body.get('off')) and variant=='good',
                               'expires':time.monotonic()+duration, 'extensions':0}
            self.reply(200, self.status(SESSIONS[token]), token)
            return
        session = self.session()
        if not session or not self.status(session)['active']:
            self.reply(401, {'error':'session expired'})
            return
        if path == '/activity':
            session['expires'] = time.monotonic()+session['duration']
            self.reply(200, self.status(session))
        elif path == '/extend':
            limit = 10 if session['variant']=='good' else 1
            if session['extensions'] >= limit:
                self.reply(409, {'error':'no more extensions'})
                return
            session['extensions'] += 1
            session['expires'] = time.monotonic()+session['duration']
            self.reply(200, self.status(session))
        elif path == '/save':
            # Echo only. No account or form data is written to disk or retained in sessions.
            self.reply(200, {'saved':body.get('data')})
        else:
            self.reply(404, {'error':'not found'})


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=4326)
    args=parser.parse_args()
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
