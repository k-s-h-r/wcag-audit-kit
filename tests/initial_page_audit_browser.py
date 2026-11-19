"""Exercise the initial-only report and an opt-in exploration on the same local page."""
import argparse
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/wcag-audit-kit/scripts'))
import audit
import page_explorer
import page_workflow


class Fixture(BaseHTTPRequestHandler):
    hits = Counter()
    image = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'

    def do_GET(self):
        self.hits[self.path] += 1
        self.send_response(200 if self.path == '/' else 404)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        if self.path != '/':
            return
        spans = ''.join(f'<span id="link-text-{i}"> Section</span>' for i in range(30))
        self.wfile.write(f'''<!DOCTYPE html><html lang="en"><head><title>Local audit test</title>
<style>summary, a, #standalone, #child-handler, #delegate, [role=button] {{ cursor:pointer; }}</style></head>
<body><main><h1 id="content">Audit test</h1><img id="initial-image" src="{self.image}">
<details><summary id="toggle"><span id="summary-text">Open section</span></summary>
<p>Expanded content below.</p><img id="operation-image" src="{self.image}"></details>
<a id="link" href="/other">{spans}</a>
<div id="custom" role="button" tabindex="0"><span id="passive">Label</span>
<span id="child-handler">Child with its own handler</span></div>
<div id="standalone">Pointer-only fallback</div>
<div id="delegate"><span id="delegate-target">Delegated target</span></div></main>
<script>
document.querySelector('#child-handler').addEventListener('click', e => e.stopPropagation());
document.querySelector('#delegate').addEventListener('click', e => {{
  if (e.target.id === 'delegate-target') e.target.textContent = 'Delegated click handled';
}});
</script>
</body></html>'''.encode())

    def log_message(self, *args):
        pass


def invoke(args, expected=0):
    output, errors = io.StringIO(), io.StringIO()
    with redirect_stdout(output), redirect_stderr(errors):
        code = audit.main(args)
    assert code == expected, (args, code, errors.getvalue(), output.getvalue())
    return errors.getvalue() if expected else json.loads(output.getvalue().strip().splitlines()[-1])


def machine_alt(value):
    return [row['target'] for row in value['machine_checks']
            if row['checkpoint'] == 'axe / image-alt' and row['outcome'] == 'failed']


def main(out):
    with ThreadingHTTPServer(('127.0.0.1', 0), Fixture) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}/'
            command = ['page-audit', '--url', url, '--out', str(out)]
            baseline = invoke(command + ['--mode', 'machine', '--screenshots', 'all', '--initial-only'])
            run = audit.run_layout.ledger(out)
            files = audit.run_layout.report_files(run, single=True)
            graph = page_explorer.status(run)
            assert graph['deferred'] and graph['steps'] == 2 and not graph['queue']
            assert Fixture.hits['/'] == 2 and not Fixture.hits['/other']
            assert baseline['operation_exploration_deferred'] and baseline['pending_routes'] == 0
            assert baseline['explore_command'].endswith('--resume --explore')
            assert len(graph['nodes']) == 2
            assert len(list(run.rglob('*.png'))) == 2
            for node in graph['nodes']:
                dest = run / node['evidence_dir']
                assert (dest/'page.png').exists()
                assert not (dest/'keyboard.json').exists() and not (dest/'tiles.json').exists()
                selectors = {item['selector'] for item in node['controls']}
                assert selectors == {'#toggle', '#link', '#custom', '#child-handler', '#standalone',
                                     '#delegate', '#delegate-target'}, selectors
                assert node['controls'][-1]['selector'] == '#delegate-target'
            value = audit.load(files.json)
            assert value['exploration']['deferred'] and not value['audit_complete']
            assert machine_alt(value) and all('#initial-image' in row for row in machine_alt(value))
            assert '操作探索は未実施です。' in files.html.read_text()
            packet = page_workflow.next_work(run, url, limit=1)
            assert packet['exploration']['deferred'] and packet['exploration']['next'].endswith('--explore')

            immutable = [run/'run.json', *(run / row['path'] for row in graph['proof'])]
            hashes = [sha256(path.read_bytes()).digest() for path in immutable]
            assert '--explore' in invoke(command + ['--resume'], expected=1)
            assert not page_explorer.status(run)['queue'] and Fixture.hits['/'] == 2

            explored = invoke(command + ['--resume', '--explore', '--max-steps', '6'])
            updated = page_explorer.status(run)
            assert not updated['deferred'] and updated['steps'] == 6
            assert [sha256(path.read_bytes()).digest() for path in immutable] == hashes
            assert sum(edge.get('initial_input', False) for edge in updated['edges']) == 2
            assert all((run/edge['evidence_dir']/'keyboard.json').is_file()
                       for edge in updated['edges'] if edge.get('initial_input'))
            assert explored['html'] == baseline['html'] and not explored['operation_exploration_deferred']
            value = audit.load(files.json)
            assert not value['exploration']['deferred'] and not value['audit_complete']
            assert any('#operation-image' in row for row in machine_alt(value))
            assert '操作探索は未実施です。' not in files.html.read_text()
            assert not Fixture.hits['/other']

            interrupted_out = out / 'partial'
            partial = ['page-audit', '--url', url, '--out', str(interrupted_out), '--initial-only']
            invoke(partial + ['--max-steps', '1'])
            partial_run = audit.run_layout.ledger(interrupted_out)
            first = page_explorer.status(partial_run)
            assert first['deferred'] and first['steps'] == 1 and len(first['queue']) == 1
            partial_packet = page_workflow.next_work(partial_run, url, limit=1)
            assert partial_packet['exploration']['next'].endswith('--initial-only')
            invoke(partial + ['--resume'])
            finished = page_explorer.status(partial_run)
            assert finished['deferred'] and finished['steps'] == 2 and not finished['queue']
            assert all(item in finished['proof'] for item in first['proof'])
        finally:
            server.shutdown()
            worker.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
