"""Exercise configured URL selection, independent page runs and interrupted collection."""
import argparse
from collections import Counter
from hashlib import sha256
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import signal
import subprocess
import sys
from threading import Event, Thread
from urllib.parse import urlsplit

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/wcag-audit-kit/scripts'
sys.path.insert(0, str(SCRIPTS))
import audit
from browser_capture import page_id


PATHS = ('/a', '/a-extra', '/query?view=one', '/query?view=two', '/app#one', '/app#two', '/missing')
RULES = ('image-alt', 'document-title')


def fixture():
    requests = []
    entered, release = Event(), Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            requests.append(self.path)
            path = urlsplit(self.path).path
            if path == '/a-extra' and not entered.is_set():
                entered.set()
                release.wait(25)
            if path == '/mark.svg':
                body = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect width="16" height="16"/></svg>'
                content_type = 'image/svg+xml'
            else:
                title = '' if self.path == '/query?view=two' else '<title>Owned URL</title>'
                alt = '' if path == '/a-extra' else ' alt="Square"'
                fragment = ('<script>if (location.hash === "#two") '
                            'document.querySelector("img").removeAttribute("alt");</script>') if path == '/app' else ''
                body = (f'<!doctype html><html lang="en"><head>{title}</head><body>'
                        f'<main><h1>Owned URL</h1><img src="/mark.svg"{alt}>'
                        f'<a href="/outside-list">Another page</a></main>{fragment}</body></html>')
                content_type = 'text/html; charset=utf-8'
            data = body.encode()
            self.send_response(404 if path == '/missing' else 200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    return server, worker, requests, entered, release


def hashes(run):
    run = audit.run_layout.ledger(run)
    return {path.relative_to(run).as_posix(): sha256(path.read_bytes()).hexdigest()
            for path in (run/'evidence').rglob('*') if path.is_file()}


def invoke(command, out, label):
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    (out/f'{label}.stdout.txt').write_text(result.stdout)
    (out/f'{label}.stderr.txt').write_text(result.stderr)
    return result


def interrupt(command, out, entered, release):
    with (out/'interrupted.stdout.txt').open('w') as stdout, (out/'interrupted.stderr.txt').open('w') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        try:
            assert entered.wait(25), 'second URL did not start'
            child.send_signal(signal.SIGINT)
            assert child.wait(timeout=20) != 0, 'interrupted page unexpectedly completed'
        finally:
            if child.poll() is None:
                child.kill()
                child.wait()
            release.set()


def configured_urls(command, out, base, config, requests):
    path = out/'configured.json'
    settings = out/'selection-config.json'
    audit.save(out/'urls.json', [PATHS[0], './a', *PATHS[1:]])
    config['scope'].update(mode='configured', pages=[], pages_file='urls.json')
    audit.save(settings, config)
    result = invoke([*command, 'pages', '--config', str(settings), '--out', str(path)], out, 'selection')
    urls = [base + path for path in PATHS]
    assert result.returncode == 0, result.stderr
    assert not requests, requests
    selection = audit.load(path)
    assert [(row['url'], row['source'], row['visited']) for row in selection['pages']] == [
        (url, 'configured', False) for url in urls], selection
    assert len(set(map(page_id, urls))) == len(urls)
    return urls


def check_reports(run, url, path, result):
    assert result.returncode == 0, result.stderr
    files = {k: Path(v) for k, v in json.loads(result.stdout.splitlines()[-1]).items() if k in {'html', 'json', 'excel'}}
    assert files.keys() == {'html', 'json', 'excel'}
    report = audit.load(files['json'])
    assert report['url'] == url and not report['audit_complete']
    assert report['counts'] == {'not_run': 55}
    assert all(case['page_url'] == url and case['page_id'] == page_id(url) for case in report['cases'])
    assert escape(url) in files['html'].read_text()
    run = audit.run_layout.ledger(run)
    graph = audit.load(run/'exploration.json')
    assert len(graph['nodes']) == 1
    node = graph['nodes'][0]
    axe = audit.load(run/node['evidence_dir']/'axe.json')
    expected = {'image-alt': 'failed' if path in {'/a-extra', '/app#two'} else 'passed',
                'document-title': 'failed' if path == '/query?view=two' else 'passed'}
    raw = {item['id']: outcome for group, outcome in [('violations', 'failed'), ('passes', 'passed')]
           for item in axe[group] if item['id'] in RULES}
    assert raw == expected, (url, raw)
    machine = report['machine_checks']
    assert {row['checkpoint'].removeprefix('axe / '): row['outcome'] for row in machine
            if row['checkpoint'] in {f'axe / {rule}' for rule in RULES}} == expected
    assert all((run/row['evidence']).is_file() for row in machine)
    book = load_workbook(files['excel'], read_only=True, data_only=True)
    try:
        cells = list(book['機械検査'].values)[1:]
        assert len(cells) == len(machine)
        assert [(row[1], row[3], row[8]) for row in cells] == [
            (row['checkpoint'], row['outcome'], row['evidence']) for row in machine]
    finally:
        book.close()
    return {'url': url, 'status': 'collected', 'rules': raw, 'criteria': report['counts'],
            'reports': {key: value.name for key, value in files.items()}}


def main(out):
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    server, worker, requests, entered, release = fixture()
    base = f'http://127.0.0.1:{server.server_port}'
    command = [sys.executable, str(SCRIPTS/'audit.py')]
    before_resume = None
    reports = []
    try:
        config = audit.init_config(base)
        config.update(environments=config['environments'][:1], keyboard_steps=2)
        urls = configured_urls(command, out, base, config, requests)
        for index, (url, path) in enumerate(zip(urls, PATHS, strict=True)):
            run = out/f'page-{index+1:02d}'
            settings = out/f'config-{index+1:02d}.json'
            page_config = audit.init_config(url)
            page_config.update(environments=page_config['environments'][:1], keyboard_steps=2)
            audit.save(settings, page_config)
            args = [*command, 'page-audit', '--url', url, '--config', str(settings), '--out', str(run),
                    '--mode', 'machine', '--max-states', '1', '--max-steps', '1', '--max-depth', '1']
            if index == 1:
                first = hashes(out/'page-01')
                interrupt(args, out, entered, release)
                graph = audit.load(audit.run_layout.ledger(run)/'exploration.json')
                assert first and not graph['nodes'] and graph['queue']
                partial = hashes(run)
                assert partial, 'interruption should preserve evidence'
                before_resume = {'collected': 1, 'interrupted': 1, 'unattempted': len(urls)-2}
                audit.save(out/'interruption.json', {'counts': before_resume, 'completed_hashes': first,
                           'interrupted_hashes': partial, 'requests': requests.copy()})
                result = invoke([*args, '--resume'], out, 'resumed')
                assert hashes(out/'page-01') == first
                assert partial.items() <= hashes(run).items()
            else:
                result = invoke(args, out, run.name)
            if path == '/missing':
                assert result.returncode == 2, result.stderr
                graph = audit.load(audit.run_layout.ledger(run)/'exploration.json')
                assert not graph['nodes'] and any('404' in item for item in graph['remaining']), graph
                assert not (run/'data/report.json').exists()
                reports.append({'url': url, 'status': 'navigation_failed', 'reason': 'HTTP 404'})
            else:
                reports.append(check_reports(run, url, path, result))
        assert [row['url'] for row in reports] == urls
        allowed = {urlsplit(path).path for path in PATHS} | {'/mark.svg', '/favicon.ico'}
        assert all(urlsplit(path).path in allowed for path in requests)
        assert requests.count('/a') == 1 and requests.count('/a-extra') == 2
        counts = dict(Counter(row['status'] for row in reports))
        assert counts == {'collected': 6, 'navigation_failed': 1}
        audit.save(out/'observed.json', {'before_resume': before_resume, 'counts': {**counts, 'unattempted': 0},
                   'pages': reports, 'criteria': {'not_run': sum(row.get('criteria', {}).get('not_run', 0) for row in reports)},
                   'prior_completed_evidence': len(first), 'prior_interrupted_evidence': len(partial),
                   'requests': requests, 'audit_complete': False})
        print(json.dumps({'pages': len(reports), **counts, 'resumed': True}, ensure_ascii=False))
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    main(parser.parse_args().out)
