"""Run the configured batch CLI against an owned site and interrupt it with SIGINT."""
import argparse
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
from threading import Event, Thread
from urllib.parse import urlsplit

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT/'skills/wcag-audit-kit/scripts/audit.py'
PATHS = ['/first', '/slow?state=one', '/missing', '/tail?state=two#detail']


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def load(path):
    return json.loads(path.read_text())


def manifest(batch):
    value = load(batch/'page-batch.json')
    return value, {row['url']: row for row in value['pages']}


def proof(run):
    return {item.relative_to(run).as_posix(): sha256(item.read_bytes()).hexdigest()
            for item in (run/'evidence').rglob('*') if item.is_file()}


def verify_reports(out, row):
    assert set(row['reports']) == {'html', 'json', 'excel'}
    assert all((out/path).is_file() for path in row['reports'].values())
    report = load(out/row['reports']['json'])
    assert report['url'] == row['url'] and report['verification']['mode'] == 'machine'
    assert row['wcag_counts'] == report['counts'] == {'not_run': 55}
    assert row['collection_complete'] is report['collection_complete'] is True
    assert row['exploration_complete'] is report['exploration']['complete'] is False
    assert row['audit_complete'] is report['audit_complete'] is False
    assert row['scope_confirmed'] is report['scope_confirmed'] is False
    assert all(case['page_url'] == row['url'] for case in report['cases'])
    book = load_workbook(out/row['reports']['excel'], read_only=True, data_only=True)
    try:
        assert book['機械検査'].max_row == len(report['machine_checks']) + 1
    finally:
        book.close()


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    requests = []
    active, release = Event(), Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            requests.append(self.path)
            path = urlsplit(self.path).path
            if path == '/slow' and not active.is_set():
                active.set()
                release.wait(25)
            if path == '/favicon.ico':
                self.send_error(404)
                return
            body = ('<!doctype html><html lang="en"><title>Owned URL</title><main>'
                    '<h1>Owned URL</h1><a href="/outside-list">Another page</a></main></html>').encode()
            self.send_response(404 if path == '/missing' else 200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f'http://127.0.0.1:{server.server_port}'
    urls = [base + path for path in PATHS]
    settings, listed, batch = [out/name for name in ('config.json', 'urls.json', 'batch')]
    config = {'schema_version': '1', 'url': base, 'level': 'AA', 'keyboard_steps': 1,
              'scope': {'mode': 'configured', 'pages_file': 'urls.json'},
              'environments': [{'id': 'desktop', 'viewport': {'width': 1280, 'height': 900}}]}
    inputs = [PATHS[0], './first', *PATHS[1:]]
    write(settings, config)
    write(listed, inputs)

    args = [sys.executable, str(AUDIT), 'page-batch', '--config', str(settings), '--out', str(batch)]

    def call(label, *options, expected=0, audit_script=AUDIT):
        ran = subprocess.run([args[0], str(audit_script), *args[2:], *options],
                             capture_output=True, text=True, timeout=90)
        (out/f'{label}.stdout.txt').write_text(ran.stdout)
        (out/f'{label}.stderr.txt').write_text(ran.stderr)
        assert ran.returncode == expected, (label, ran.stdout, ran.stderr)
        return json.loads(ran.stdout) if ran.stdout else None

    try:
        first = call('first', '--max-pages-this-run', '1')
        assert first['counts'] == {'pending': 3, 'interrupted': 0, 'completed': 1, 'failed': 0}
        value, rows = manifest(batch)
        assert list(rows) == urls and first['counts'] == value['counts']
        first_run = batch/rows[urls[0]]['run']
        first_proof = proof(first_run)
        assert first_proof
        before = requests.count('/first')
        assert not any(urlsplit(path).path in {'/slow', '/missing', '/tail'} for path in requests)
        frozen = (batch/'page-batch.json').read_bytes()
        seen = list(requests)
        call('existing-output', expected=1)
        assert (batch/'page-batch.json').read_bytes() == frozen and requests == seen

        write(listed, list(reversed(inputs)))
        call('changed-list', '--resume', expected=1)
        assert (batch/'page-batch.json').read_bytes() == frozen and requests == seen
        write(listed, inputs)
        write(settings, {**config, 'verification': {'mode': 'ai'}})
        call('changed-mode', '--resume', expected=1)
        assert (batch/'page-batch.json').read_bytes() == frozen and requests == seen
        write(settings, {**config, 'keyboard_steps': 2})
        call('changed-config', '--resume', expected=1)
        assert (batch/'page-batch.json').read_bytes() == frozen and requests == seen
        write(settings, config)
        altered_runtime = shutil.copytree(AUDIT.parent.parent, out/'altered-runtime',
                                          ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        with (altered_runtime/'scripts/page_batch.py').open('a') as changed:
            changed.write('\n# Test a different implementation fingerprint.\n')
        call('changed-implementation', '--resume', expected=1, audit_script=altered_runtime/'scripts/audit.py')
        assert (batch/'page-batch.json').read_bytes() == frozen and requests == seen

        with (out/'interrupted.stdout.txt').open('w') as stdout, (out/'interrupted.stderr.txt').open('w') as stderr:
            child = subprocess.Popen([*args, '--resume', '--max-pages-this-run', '1'], stdout=stdout, stderr=stderr)
            try:
                assert active.wait(25), 'second URL did not start'
                child.send_signal(signal.SIGINT)
                assert child.wait(timeout=20) == 130
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait()
                release.set()
        value, rows = manifest(batch)
        assert value['counts'] == {'pending': 2, 'interrupted': 1, 'completed': 1, 'failed': 0}
        interrupted_run = batch/rows[urls[1]]['run']
        interrupted_proof = proof(interrupted_run)
        assert interrupted_proof and rows[urls[1]]['reason']
        assert proof(first_run) == first_proof and requests.count('/first') == before

        resumed = call('resume', '--resume', '--max-pages-this-run', '2')
        assert resumed['counts'] == {'pending': 1, 'interrupted': 0, 'completed': 2, 'failed': 1}
        value, rows = manifest(batch)
        assert batch/rows[urls[1]]['run'] == interrupted_run
        assert interrupted_proof.items() <= proof(interrupted_run).items()
        assert rows[urls[2]]['status'] == 'failed' and '404' in rows[urls[2]]['reason']
        assert not any(urlsplit(path).path == '/tail' for path in requests)
        before_final = list(requests)
        final = call('last', '--resume')
        assert final['counts'] == {'pending': 0, 'interrupted': 0, 'completed': 3, 'failed': 1}
        assert final['all_pages_attempted']
        suffix = requests[len(before_final):]
        assert suffix and all(urlsplit(path).path in {'/tail', '/favicon.ico'} for path in suffix)
        seen = list(requests)
        assert call('finished', '--resume') == final and requests == seen
        value, rows = manifest(batch)
        for row in rows.values():
            if row['status'] == 'completed':
                verify_reports(batch, row)
        assert proof(first_run) == first_proof and requests.count('/first') == before
        assert not any(urlsplit(path).path == '/outside-list' for path in requests)
        write(out/'observed.json', {'counts': value['counts'], 'urls': list(rows), 'requests': requests,
              'completed_proof_preserved': len(first_proof), 'interrupted_proof_preserved': len(interrupted_proof),
              'unchanged_input_resume': True, 'reports_bound_to_urls': True})
        print(json.dumps(final, ensure_ascii=False))
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    main(parser.parse_args().out.resolve())
