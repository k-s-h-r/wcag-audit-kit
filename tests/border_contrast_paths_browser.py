"""Check declared 1.4.11 boundary readings and their report evidence."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
from threading import Thread

from openpyxl import load_workbook

from keyboard_checks_browser import ROOT, audit


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run_check(area, url, *, mode, expected, ratio=None):
    area.mkdir()
    config = audit.init_config(url)
    config['border_checks'] = [{'id': 'form-boundary', 'name': '入力欄の外枠', 'target': '#subject'}]
    config['keyboard_steps'] = 0
    config_file = area / 'config.json'
    audit.save(config_file, config)
    run = area / 'run'
    result = subprocess.run([sys.executable, str(ROOT/'skills/wcag-audit-kit/scripts/audit.py'),
        'page-audit', '--config', str(config_file), '--out', str(run), '--mode', mode,
        '--screenshots', 'all' if mode == 'ai' else 'off', '--max-states', '1', '--max-steps', '2'],
        capture_output=True, text=True, timeout=90)
    (area/'command.log').write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    files = json.loads(result.stdout)['files']
    report = audit.load(files['json'])
    row, = [row for row in report['machine_checks'] if row['checkpoint'] == '境界の測定 / form-boundary']
    assert row['criterion'] == '1.4.11' and row['target'] == '#subject' and row['outcome'] == expected, row
    assert next(entry for entry in report['criteria'] if entry['id'] == '1.4.11')['status'] == 'unverified'
    proof = audit.load(run/row['evidence'])
    graph = audit.load(run/'exploration.json')
    assert audit.evidence_item(run, row['evidence']) in graph['proof']
    if ratio is not None:
        assert proof['status'] == 'measured' and proof['minimum'] == 3, proof
        assert abs(proof['ratio'] - ratio) < 0.0001 and audit.evidence_item(run, proof['source']) in graph['proof']
    elif mode == 'machine':
        assert proof['status'] == 'skipped' and not list(run.glob('evidence/*/*.png')), proof
    else:
        assert proof['status'] == 'cant_tell', proof
    html = Path(files['html']).read_text()
    assert f'href="./{row["evidence"]}"' in html
    book = load_workbook(files['excel'], read_only=True, data_only=True)
    try:
        assert any(row['evidence'] in cells and row['observed'] in cells and row['target'] in cells
                   for cells in book['機械検査'].values)
    finally:
        book.close()
    return {'status': proof['status'], 'outcome': expected, 'ratio': proof.get('ratio')}


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    public = out/'public'
    shutil.copytree(ROOT/'benchmarks/cases/1.4.11/public', public)
    hidden = (public/'p02.html').read_text().replace('</body>', '''<aside style="position:fixed;inset:0;
        pointer-events:none;background:rgba(255,255,255,.6);z-index:9"></aside></body>''')
    (public/'overlapping.html').write_text(hidden)
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(public))) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        cases = [('low', 'p01.html', 'ai', 'failed', 1.358247), ('high', 'p02.html', 'ai', 'passed', 7.455178),
                 ('overlapping', 'overlapping.html', 'ai', 'cant_tell', None),
                 ('without-images', 'p02.html', 'machine', 'cant_tell', None)]
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                jobs = {name: pool.submit(run_check, out/name, f'{base}/{page}',
                    mode=mode, expected=outcome, ratio=ratio) for name, page, mode, outcome, ratio in cases}
                results = {name: job.result() for name, job in jobs.items()}
            audit.save(out/'observed.json', results)
            print(json.dumps(results, ensure_ascii=False))
        finally:
            server.shutdown()
            thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
