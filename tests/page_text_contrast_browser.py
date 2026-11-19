"""Verify configured 1.4.3 pixel measurements in the normal machine workflow."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread

from openpyxl import load_workbook
from PIL import Image

from border_contrast_paths_browser import QuietHandler
from keyboard_checks_browser import ROOT, audit
from text_paint import CAPTURE_STAGES


class Handler(QuietHandler):
    def do_GET(self):
        if self.path == '/measurement-request':
            self.server.measurement_requests.append(self.path)
            self.send_response(204)
            self.end_headers()
        else:
            super().do_GET()


def collect(out, url, expected, ratio=None, threshold=4.5, resume=False):
    out.mkdir()
    config = audit.init_config(url)
    config['environments'] = config['environments'][:1]
    config['keyboard_steps'] = 0
    config['text_contrast_checks'] = [{'id': 'notice', 'name': '予約状況の文字', 'target': '#subject'}]
    settings, run = out/'config.json', out/'run'
    audit.save(settings, config)
    command = [sys.executable, str(ROOT/'skills/wcag-audit-kit/scripts/audit.py'),
               'page-audit', '--url', url, '--config', str(settings), '--out', str(run), '--mode', 'machine',
               '--screenshots', 'off', '--max-states', '1']

    def run_cli(*args):
        collected = subprocess.run([*command, *args], capture_output=True, text=True, timeout=60)
        with (out/'command.log').open('a') as log:
            log.write(collected.stdout + collected.stderr)
        assert collected.returncode == 0, collected.stdout + collected.stderr
        return json.loads(collected.stdout.strip().splitlines()[-1])

    original_proof = []
    if resume:
        run_cli('--max-steps', '1')
        saved = audit.load(audit.run_layout.ledger(run)/'exploration.json')
        assert saved['queue'][0]['text_check'] == 'notice'
        original_proof = saved['proof']
    files = run_cli('--max-steps', '2', *(['--resume'] if resume else []))
    run = audit.run_layout.ledger(run)
    report = audit.load(files['json'])
    graph = audit.load(run/'exploration.json')
    assert all(audit.evidence_item(run, item['path']) == item and item in graph['proof'] for item in original_proof)
    row, = [row for row in report['machine_checks'] if row['checkpoint'] == '文字色の測定 / notice']
    assert row['criterion'] == '1.4.3' and row['target'] == '#subject'
    assert next(entry for entry in report['criteria'] if entry['id'] == '1.4.3')['status'] == 'unverified'
    record = audit.load(run/row['evidence'])
    assert audit.evidence_item(run, row['evidence']) in graph['proof']
    html = Path(files['html']).read_text()
    assert '1.4.3 文字のコントラスト' in html and row['observed'] in html and f'href="{audit.run_layout.href(Path(files["html"]), run / row["evidence"])}"' in html
    book = load_workbook(files['excel'], read_only=True, data_only=True)
    try:
        assert any(row['target'] in cells and row['observed'] in cells and row['evidence'] in cells
                   for cells in book['機械検査'].values)
    finally:
        book.close()
    frame_dir = (run/row['evidence']).parent
    assert set(run.glob('evidence/*/*.png')) == {frame_dir/frame['path'] for frame in record.get('frames', {}).values()}
    if ratio is None:
        assert row['outcome'] == 'cant_tell' and record['status'] == 'hold' and record['reason'] == expected, record
        assert 'ratio' not in record and 'ratio' not in row['text_contrast']
        return record['reason']

    assert row['outcome'] == expected and record['status'] == 'measured', record
    assert abs(record['ratio'] - ratio) < 0.00001 and record['threshold'] == threshold
    assert row['text_contrast']['ratio'] == record['ratio']
    assert set(record['frames']) == set(CAPTURE_STAGES)
    assert len({record['frames'][stage]['sha256'] for stage in ('original', 'original-repeat', 'restored', 'restored-repeat')}) == 1
    for frame in record['frames'].values():
        frame_path = frame_dir/frame['path']
        proof = audit.evidence_item(run, frame_path.relative_to(run).as_posix())
        assert proof in graph['proof'] and proof['sha256'] == frame['sha256']
        with Image.open(frame_path) as image:
            left, top, right, bottom = record['frame_crop_css_px']
            assert image.size == (right - left, bottom - top) and image.size != tuple(record['viewport_css_px'])
    assert f'href="{audit.run_layout.href(Path(files["html"]), run / row["text_contrast"]["source"])}"' in html
    return record['ratio']


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    public = out/'public'
    public.mkdir()
    fixtures = ROOT/'benchmarks/cases/1.4.3/public'
    low, high = ((fixtures/f'p0{index}.html').read_text() for index in (1, 2))
    (public/'low.html').write_text(low)
    (public/'high.html').write_text(high)
    (public/'large.html').write_text(low.replace('16px;color:#aaa', '20px;font-weight:700;color:#777'))
    overlay = '<span style="position:fixed;top:0;left:0;width:160px;height:360px;background:#fff8"></span>'
    (public/'overlay.html').write_text(high.replace('</body>', overlay+'</body>'))
    for name, reaction in [('mutation', 'document.body.dataset.reacted = "yes"'),
                           ('network', 'fetch("/measurement-request").catch(() => {})')]:
        script = f'''<script>
          new MutationObserver(() => {{ {reaction}; }})
            .observe(document.querySelector("#subject"), {{ attributes: true, attributeFilter: ["style"] }});
        </script>'''
        (public/f'{name}.html').write_text(high.replace('</body>', script+'</body>'))
    cases = {
        'low': dict(expected='failed', ratio=2.323123), 'high': dict(expected='passed', ratio=18.883061, resume=True),
        'large': dict(expected='passed', ratio=4.478089, threshold=3),
        'overlay': dict(expected='complex_paint_overlap_or_clipping'),
        'mutation': dict(expected='layout_or_state_changed'),
        'network': dict(expected='resource_request_blocked'),
    }
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(public))) as server:
        server.measurement_requests = []
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                jobs = {name: pool.submit(collect, out/name, f'http://127.0.0.1:{server.server_port}/{name}.html', **options)
                        for name, options in cases.items()}
                result = {name: job.result() for name, job in jobs.items()}
            assert not server.measurement_requests
        finally:
            server.shutdown()
            thread.join()
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
