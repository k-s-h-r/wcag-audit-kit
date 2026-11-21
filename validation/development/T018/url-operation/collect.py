"""Collect headless browser evidence from the public accordion URLs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread


PUBLIC = Path(__file__).resolve().with_name('public')
CLI = PUBLIC.parents[4] / 'skills/wcag-page/scripts/audit.py'
PROFILES = {
    'quick': ['--quick-explore'],
    'full': ['--explore', '--max-depth', '4', '--max-steps', '48', '--max-states', '16'],
}


class QuietHTTP(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def collect(out, url, profile):
    out.mkdir()
    page = str(out / 'page')
    audit = [sys.executable, str(CLI), 'page-audit', '--url', url, '--out', page]
    commands = {
        'initial.log': audit + ['--level', 'AA', '--mode', 'machine', '--screenshots', 'initial', '--initial-only'],
        'explore.log': audit + ['--resume', *profile],
    }
    for name, command in commands.items():
        with (out / name).open('w') as log:
            print(json.dumps(command), file=log, flush=True)
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=900)


def main(out, profile):
    out.mkdir(parents=True)
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHTTP, directory=str(PUBLIC))) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                jobs = [pool.submit(collect, out / fixture.stem, f'http://127.0.0.1:{server.server_port}/{fixture.name}',
                                    PROFILES[profile]) for fixture in sorted(PUBLIC.glob('*.html'))]
                for job in jobs:
                    job.result()
        finally:
            server.shutdown()
            thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--profile', choices=PROFILES, required=True)
    args = parser.parse_args()
    main(args.out.resolve(), args.profile)
