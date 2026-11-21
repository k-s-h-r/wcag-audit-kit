"""Serve the fixed process pair and capture real Orca output in a fresh run."""

import argparse
from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
from threading import Thread


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
from benchmarks.native_status import capture


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run(runtime, output):
    output.mkdir(parents=True, exist_ok=False)
    fixture = output / 'fixture'
    shutil.copytree(HERE / 'fixture', fixture)
    scenario_path = output / 'scenario.json'
    shutil.copyfile(HERE / 'scenario.json', scenario_path)
    scenario = json.loads(scenario_path.read_text())
    files = sorted([scenario_path, *[path for path in fixture.rglob('*') if path.is_file()]])
    fingerprints = {path.relative_to(output).as_posix(): sha256(path.read_bytes()).hexdigest() for path in files}
    (output / 'input-sha256.json').write_text(json.dumps(fingerprints, indent=2) + '\n')

    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=fixture)) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for case in sorted(path.name for path in fixture.iterdir() if path.is_dir()):
                area = output / case
                area.mkdir()
                url = f'http://127.0.0.1:{server.server_port}/{case}/'
                request = {**scenario, 'case_id': case, 'url': url}
                (area / 'request.json').write_text(json.dumps(request, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                capture(runtime, area)
                print(area / 'speech/screen-reader.json', flush=True)
        finally:
            server.shutdown()
            thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    run(args.root, args.out)
