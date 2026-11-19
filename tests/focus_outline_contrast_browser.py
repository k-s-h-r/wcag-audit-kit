"""Measure the same focus outline across backgrounds with real keyboard input."""
import argparse
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


PAGE = '''<!doctype html><html lang="ja"><meta charset="utf-8"><title>フォーカス枠の測定例</title>
<style>
body { margin: 40px; background: white; color: black; }
body.dark { background: #222; }
body.mixed { background: #222; }
body.mixed main { background: white; width: 200px; padding-bottom: 14px; }
button { display: block; margin-bottom: 28px; width: 160px; height: 44px; border: 0; border-radius: 0; }
#subject:focus-visible, #steady { outline: 3px solid #000; outline-offset: 2px; }
#steady { visibility: hidden; }
body.entries #steady { visibility: visible; }
</style>
<button id="dark">暗い背景</button><button id="mixed">境界のある背景</button>
<button id="entries">常時表示の枠</button><main><button id="subject">対象</button></main>
<button id="steady">常時表示の枠の対象</button>
<script>
for (const name of ['dark', 'mixed', 'entries']) {
    document.getElementById(name).addEventListener('click', () => { document.body.className = name; });
}
</script>'''


def tab(selector):
    return {'key': 'Tab', 'focus': selector}


def focus_route(identifier, name, *steps):
    return dict(id=identifier, name=name, criterion='1.4.11', steps=[*steps[:-1], dict(steps[-1], focus_contrast=True)])


def run_check(out, url):
    config = audit.init_config(url)
    config['environments'] = config['environments'][:1]
    config['keyboard_steps'] = 0
    tabs = [tab(selector) for selector in ('#dark', '#mixed', '#entries', '#subject')]
    config['keyboard_checks'] = [
        focus_route('light', '白い背景', *tabs),
        focus_route('dark', '暗い背景', tabs[0], dict(key='Enter', focus='#dark'), *tabs[1:]),
        focus_route('mixed', '境界のある背景', *tabs[:2], dict(key='Enter', focus='#mixed'), *tabs[2:]),
        focus_route('steady', '常時表示の枠', *tabs[:3], dict(key='Enter', focus='#entries'), tabs[3], tab('#steady')),
        focus_route('missed', '対象へ届かない', tab('#subject')),
    ]
    config_file, run = out/'config.json', out/'run'
    audit.save(config_file, config)
    result = subprocess.run([sys.executable, str(ROOT/'skills/wcag-audit-kit/scripts/audit.py'),
        'page-audit', '--url', url, '--config', str(config_file), '--out', str(run), '--mode', 'machine',
        '--screenshots', 'off', '--max-states', '1', '--max-steps', '6'], capture_output=True, text=True, timeout=90)
    (out/'command.log').write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    files = json.loads(result.stdout.strip().splitlines()[-1])
    report = audit.load(files['json'])
    graph = audit.load(run/'exploration.json')
    assert next(entry for entry in report['criteria'] if entry['id'] == '1.4.11')['status'] == 'unverified'
    assert len(list(run.glob('evidence/*/*.png'))) == 3
    measured = {'light': ('passed', '#ffffff', 21), 'dark': ('failed', '#222222', 1.3199259)}
    held = {'mixed': '単色でそろわない', 'steady': 'キー入力で現れる', 'missed': '到達条件が一致せず'}
    html = Path(files['html']).read_text()
    book = load_workbook(files['excel'], read_only=True, data_only=True)
    try:
        worksheet = list(book['機械検査'].values)
        for identifier in [*measured, *held]:
            row, = [row for row in report['machine_checks'] if row['checkpoint'] == 'キーボード経路 / '+identifier]
            assert row['criterion'] == '1.4.11' and row['target'] == ('#steady' if identifier == 'steady' else '#subject')
            assert row['observed'] in html and f'href="./{row["evidence"]}"' in html
            assert any(row['evidence'] in cells and row['observed'] in cells and row['target'] in cells for cells in worksheet)
            assert audit.evidence_item(run, row['evidence']) in graph['proof']
            record = audit.load(run/row['evidence'])
            last = record['steps'][-1]
            assert last['input_event_index'] > 0
            measurement = row['focus_outline']
            assert last.get('outline', {}) == measurement
            if identifier in held:
                assert row['outcome'] == 'cant_tell' and held[identifier] in row['observed'], row
                continue
            outcome, background, ratio = measured[identifier]
            assert row['outcome'] == outcome and measurement['status'] == 'measured', row
            assert measurement['border'] == '#000000' and measurement['outside'] == background
            assert measurement['minimum'] == 3 and abs(measurement['ratio'] - ratio) < 0.0001
            assert audit.evidence_item(run, measurement['source']) in graph['proof']
            assert f'href="{measurement["source"]}"' in html
            with Image.open(run / measurement['source']) as image:
                assert image.size == (172, 56), image.size
    finally:
        book.close()


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    (out/'index.html').write_text(PAGE)
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(out))) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            run_check(out, f'http://127.0.0.1:{server.server_port}/index.html')
        finally:
            server.shutdown()
            thread.join()
    print('Verified two ratios and three held results in machine mode.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
