"""Check real Codex skill dispatch offline using a disposable Docker container.

Run with python3 tests/codex_skill_dispatch.py. The default Debian 13 slim
image must already be loaded. Use --codex and --python-prefix to select the
locally installed CLI and a standalone Python runtime. See --help.
"""
import argparse
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from queue import Empty, Queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time


SKILLS = ('wcag-audit-kit', 'wcag-page', 'wcag-pages', 'wcag-report')
PROJECT = '/project'
SKILLS_ROOT = Path(PROJECT) / '.agents' / 'skills'
PROMPT = 'HTMLのmain要素の役割を一文で教えて。'
CLI = '/usr/local/bin/codex'
TIMEOUT = 20


class ResponsesSink(BaseHTTPRequestHandler):
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.received.put((self.path, payload['input']))
        body = b'{"error":{"message":"Offline fixture captured input.","type":"invalid_request_error"}}'
        self.send_response(400)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@contextmanager
def responses_sink():
    with ThreadingHTTPServer(('127.0.0.1', 0), ResponsesSink) as server:
        server.received = Queue()
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            yield server
        finally:
            server.shutdown()
            worker.join()


class AppServer:
    def __init__(self, arguments):
        self.process = subprocess.Popen(
            [CLI, 'app-server', '--stdio', *arguments],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
        )
        self.messages = Queue()
        self.request_id = 0
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        try:
            for line in self.process.stdout:
                self.messages.put(json.loads(line))
        finally:
            self.messages.put(None)

    def receive(self, matches):
        deadline = time.monotonic() + TIMEOUT
        while time.monotonic() < deadline:
            try:
                item = self.messages.get(timeout=max(0, deadline - time.monotonic()))
            except Empty as error:
                raise TimeoutError('No matching Codex app-server response') from error
            if item is None:
                raise RuntimeError('Codex app-server closed its output')
            if matches(item):
                return item
        raise TimeoutError('No matching Codex app-server response')

    def call(self, method, params=None):
        self.request_id += 1
        request_id = self.request_id
        request = {'method': method, 'id': request_id}
        if params is not None:
            request['params'] = params
        self._send(request)
        reply = self.receive(lambda item: item.get('id') == request_id)
        if 'error' in reply:
            raise RuntimeError(f'Codex app-server rejected {method}')
        return reply['result']

    def notify(self, method):
        self._send({'method': method})

    def _send(self, item):
        self.process.stdin.write(json.dumps(item, ensure_ascii=False) + '\n')
        self.process.stdin.flush()

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        self.process.stdout.close()


def text_fields(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for member in value.values():
            yield from text_fields(member)
    elif isinstance(value, list):
        for member in value:
            yield from text_fields(member)


def expect_request(sink, bodies, selected):
    address, inputs = sink.received.get(timeout=TIMEOUT)
    assert address == '/v1/responses', address
    fields = list(text_fields(inputs))
    included = [name for name, body in bodies.items() if any(body in field for field in fields)]
    assert included == ([selected] if selected else []), (selected, included)
    for name, body in bodies.items():
        if name != selected:
            assert not any(body.splitlines()[0] in field for field in fields), (selected, name)
    return included


def check_dispatch():
    paths = {name: SKILLS_ROOT / name / 'SKILL.md' for name in SKILLS}
    bodies = {name: path.read_text(encoding='utf-8').split('---', 2)[2].strip() for name, path in paths.items()}
    with responses_sink() as sink:
        provider = (f'{{name="Offline fixture",base_url="http://127.0.0.1:{sink.server_port}/v1",'
                    'wire_api="responses",requires_openai_auth=false}')
        config = ['-c', 'model_provider="wcag_fixture"', '-c', f'model_providers.wcag_fixture={provider}',
                  '-c', 'model="gpt-5.4"']
        rpc = AppServer(config)
        try:
            host = rpc.call('initialize', {'clientInfo': {'name': 'wcag-fixture', 'version': '1'}})
            rpc.notify('initialized')
            entry, = rpc.call('skills/list', {'cwds': [PROJECT], 'forceReload': True})['data']
            assert not entry['errors'], [item.get('path') for item in entry['errors']]
            discovered = {skill['name']: skill for skill in entry['skills'] if skill['scope'] == 'repo'}
            assert set(discovered) == set(SKILLS), sorted(discovered)
            for name, path in paths.items():
                assert discovered[name]['enabled'] is True and discovered[name]['path'] == str(path), name

            results = {}
            for selected in (None, *SKILLS):
                thread = rpc.call('thread/start', {'cwd': PROJECT, 'ephemeral': True, 'sandbox': 'read-only'})
                items = [{'type': 'text', 'text': PROMPT, 'textElements': []}]
                if selected:
                    items.append({'type': 'skill', 'name': selected, 'path': str(paths[selected])})
                turn = rpc.call('turn/start', {'threadId': thread['thread']['id'], 'input': items})
                results[selected or 'ordinary'] = expect_request(sink, bodies, selected)
                event = rpc.receive(lambda item: item.get('method') == 'turn/completed'
                                    and item['params']['turn']['id'] == turn['turn']['id'])
                assert event['params']['turn']['status'] == 'failed', selected
        finally:
            rpc.close()

        direct = subprocess.run(
            [CLI, 'exec', '--ephemeral', '--json', '--skip-git-repo-check', '-C', PROJECT,
             '-s', 'read-only', *config, '$wcag-page 試験用のHTMLを確認してください。'],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=TIMEOUT,
        )
        assert direct.returncode == 1, direct.returncode
        results['literal_cli'] = expect_request(sink, bodies, 'wcag-page')
        assert sink.received.empty(), 'Unexpected duplicate request'
    print(json.dumps({'host': host['userAgent'], 'discovered': list(SKILLS), 'included_skill_bodies': results,
                      'responses_status': 400, 'model_executed': False}, ensure_ascii=False))


def mount(source, destination):
    return ['--mount', f'type=bind,src={source},dst={destination},readonly']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default='debian:13-slim', help='locally cached Docker image, never pulled')
    parser.add_argument('--codex', type=Path, help='Codex binary (defaults to codex on PATH)')
    parser.add_argument('--python-prefix', type=Path, default=Path(sys.base_prefix),
                        help='standalone Python runtime prefix with bin/python3 and stdlib')
    args = parser.parse_args()
    cli = args.codex or shutil.which('codex')
    if not cli or not Path(cli).is_file():
        parser.error('Codex CLI is required')
    cli = Path(cli).resolve()
    runtime = args.python_prefix.resolve()
    if runtime in {Path('/'), Path('/usr'), Path('/usr/local')} or not (runtime / 'bin' / 'python3').is_file():
        parser.error('--python-prefix must select a standalone Python runtime')
    source = Path(__file__).resolve()
    root = source.parents[1]
    with tempfile.TemporaryDirectory(prefix='wcag-codex-test-', dir=root.parent) as directory:
        scratch = Path(directory)
        project = scratch / 'project'
        skill_root = project / '.agents' / 'skills'
        skill_root.mkdir(parents=True)
        for name in SKILLS:
            package = root / 'skills' / name
            destination = skill_root / name
            (destination / 'agents').mkdir(parents=True)
            for relative in ('SKILL.md', 'agents/openai.yaml'):
                shutil.copyfile(package / relative, destination / relative)
        for entry in [project, *project.rglob('*')]:
            entry.chmod(0o755 if entry.is_dir() else 0o444)
        harness = scratch / source.name
        shutil.copyfile(source, harness)
        harness.chmod(0o444)
        config = scratch / 'docker'
        config.mkdir()
        subprocess.run(
            ['docker', '--config', str(config), '--host', 'unix:///var/run/docker.sock',
             'run', '--rm', '--pull', 'never', '--network', 'none',
             '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--read-only',
             '--tmpfs', '/tmp', '--tmpfs', '/root', '--workdir', PROJECT,
             *mount(cli, CLI), *mount(runtime, '/python'), *mount(project, PROJECT),
             *mount(harness, '/wcag_skill_dispatch.py'),
             args.image, '/python/bin/python3', '-I', '/wcag_skill_dispatch.py', '--inside-container'],
            check=True, timeout=150,
        )


if __name__ == '__main__':
    if sys.argv[1:] == ['--inside-container'] and Path('/.dockerenv').is_file():
        check_dispatch()
    else:
        main()
