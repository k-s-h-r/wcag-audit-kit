"""Collect guarded page reports and the actual handoff to a follow-up check."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
from threading import Thread
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CLI = REPO / 'skills/wcag-audit-kit/scripts/audit.py'
PLAN = HERE / 'plan.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
                    encoding='utf-8')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify_fixtures(directory, plan):
    actual = {p.name: digest(p) for p in directory.iterdir() if p.is_file()}
    if actual != plan['fixture_sha256']:
        raise ValueError('事前に固定した対照のファイルと一致しない')


class CellServer(ThreadingHTTPServer):
    def __init__(self, public, port):
        self.public = public
        self.received = []
        super().__init__(('127.0.0.1', port), FixtureHandler)


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        name = self.path.removeprefix('/')
        if name not in self.server.public:
            self.reply(404)
            return
        self.reply(200, self.server.public[name])

    def do_POST(self):
        self.reply(405)

    def reply(self, status, body=b''):
        self.server.received.append({'at': now(), 'method': self.command, 'path': self.path,
                                     'host': self.headers.get('Host'), 'status': status,
                                     'body_sha256': sha256(body).hexdigest()})
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def log_message(self, *_message):
        pass


@contextmanager
def serve(fixtures, port=0):
    files = {p.name: p.read_bytes() for p in fixtures.iterdir() if p.is_file()}
    with CellServer(files, port) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f'http://127.0.0.1:{server.server_port}', server.received
        finally:
            server.shutdown()
            thread.join()


def cli(*args, destination):
    command = [sys.executable, str(CLI.relative_to(REPO)), *map(str, args)]
    completed = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=300)
    destination.write_text(completed.stdout, encoding='utf-8')
    if completed.returncode or completed.stderr:
        destination.with_suffix('.stderr').write_text(completed.stderr, encoding='utf-8')
    completed.check_returncode()


def select_work(area, url, plan):
    ledger = area / 'page'
    initial = area / 'before'
    initial.mkdir()
    for path in ('data/report.json', 'reports/report.html', 'reports/report.xlsx',
                 'reports/details/issues.md', 'work/plan.json'):
        target = initial / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ledger / path, target)
    next_file = initial / 'next.json'
    cli('page-next', '--run', ledger, '--page-exact', url, destination=next_file)
    next_work = load(next_file)
    pending = initial / 'pending.json'
    cli('pending', '--run', ledger, '--page-exact', url, '--criterion', plan['criterion'],
        destination=pending)
    open_cases = [row for row in load(pending)['cases'] if row['state'] == plan['state']]
    if {case['environment'] for case in open_cases} != set(plan['environments']) or len(open_cases) != 2:
        raise ValueError('両画面幅に対応する初期状態の検査票がない')
    if any(row['url'] != url or row['status'] != 'not_run' for row in open_cases):
        raise ValueError('対象の初期検査票が未実施であることを確認できない')
    items = {}
    for row in open_cases:
        case_id, env = row['case_id'], row['environment']
        cli('case', '--run', ledger, '--id', case_id, destination=initial / f'case-{env}.json')
        notes = [note for note in next_work['exploration']['remaining']
                 if f'--{env}：補助のTab観察' in note and '通信を遮断したため移動先の表示は未確認' in note]
        if len(notes) > 1:
            raise ValueError('移動先の確認が残る観察を一意に照合できない')
        items[env] = {'case_id': case_id, 'item': notes[0] if notes else None}
    return {'origin': f'{urlsplit(url).scheme}://{urlsplit(url).netloc}', 'url': url,
            'graph_digest': next_work['exploration']['graph_digest'], 'environments': items}


def collect(output):
    output.mkdir(parents=True, exist_ok=False)
    plan = load(PLAN)
    assets = output / 'fixtures'
    assets.mkdir()
    for name in plan['fixture_sha256']:
        shutil.copyfile(REPO / plan['source_directory'] / name, assets / name)
    verify_fixtures(assets, plan)
    shutil.copyfile(PLAN, output / 'plan.json')
    rows = {}
    with serve(assets) as (origin, received):
        for case, path in plan['cases'].items():
            area = output / case
            area.mkdir()
            url = f'{origin}/{path}'
            args = ('page-audit', '--url', url, '--out', area / 'page')
            cli(*args, *plan['initial_args'], destination=area / 'initial.log')
            cli(*args, *plan['explore_args'], destination=area / 'explore.log')
            rows[case] = select_work(area, url, plan)
            print(case, 'page-next collected', flush=True)
    save(output / 'guarded-requests.json', received)
    if any(row['path'] == '/' + plan['destination'] for row in received):
        raise ValueError('通常探索の制限中に移動先への要求がサーバーへ届いた')
    for case, row in rows.items():
        if any(bool(item['item']) != (case == '073') for item in row['environments'].values()):
            raise ValueError('通常ガード内の移動先未確認項目が事前条件と異なる')
    save(output / 'handoff.json', rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    collect(parser.parse_args().out.resolve())
