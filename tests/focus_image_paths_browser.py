"""Check paired 2.4.7 image evidence across page-audit reports in Chromium."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from math import ceil, floor
from pathlib import Path
import shutil
import subprocess
import sys
import threading

from openpyxl import load_workbook
from PIL import Image

from dynamic_visual_paths_browser import load_proof, trusted_input
from keyboard_checks_browser import ROOT, audit, route


CRITERION = '2.4.7'
EVIDENCE_LABEL = 'フォーカスの画像証拠'
STATUS_LABELS = {'captured': '取得済み', 'incomparable': '比較不可', 'skipped': '取得省略'}
DEFAULT_SIZE = (800, 600)
PHONE_SIZE = (320, 720)


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def execute(area, url, plan, size, screenshots, max_images=None, pause=False):
    area.mkdir()
    run = area / 'run'
    config = audit.init_config(url)
    config['keyboard_checks'] = [plan]
    environment = dict(config['environments'][0], viewport=dict(zip(('width', 'height'), size)))
    config['environments'] = [environment]
    config['keyboard_steps'] = 1
    audit.save(area / 'config.json', config)
    mode = 'machine' if screenshots == 'off' else 'ai'
    command = [sys.executable, str(ROOT / 'skills/wcag-audit-kit/scripts/audit.py'), 'page-audit',
               '--url', url, '--out', str(run), '--config', str(area / 'config.json'),
               '--mode', mode, '--screenshots', screenshots, '--max-states', '1', '--max-depth', '1']
    if max_images is not None:
        command += ['--max-images', str(max_images)]

    def invoke(label, *arguments):
        result = subprocess.run(command + list(arguments), capture_output=True, text=True, timeout=90)
        (area / f'{label}.log').write_text(result.stdout + result.stderr)
        assert result.returncode == 0, (url, result.stdout, result.stderr)
        return json.loads(result.stdout.splitlines()[-1])

    if pause:
        paused = invoke('paused', '--max-steps', '1')
        pending, = audit.load(Path(paused['json']))['focus_evidence']
        assert pending['status'] == 'not_run' and pending['target'] == plan['steps'][-1]['focus'], pending
        assert not any(pending[column] for column in ('before_image', 'after_image', 'evidence')), pending
        graph = audit.load(run / 'exploration.json')
        assert any(job.get('keyboard_check') == plan['id'] for job in graph['queue']), graph
        assert not any(edge.get('keyboard_check') for edge in graph['edges']), graph
        assert not list(run.glob('evidence/*/focus-*.png'))
    reports = invoke('resumed' if pause else 'first', '--max-steps', '2', *(['--resume'] if pause else []))
    return run, {name: Path(reports[name]) for name in ('html', 'json', 'excel')}


def assert_report_formats(report, row):
    html = report['html'].read_text()
    assert EVIDENCE_LABEL in html and 'id="focus-image-evidence"' in html
    for text in (row['target'], row['reason'], STATUS_LABELS[row['status']]):
        assert escape(text) in html, row
    links = [row[key] for key in ('before_image', 'after_image', 'evidence') if row[key]]
    for path in links:
        assert f'href="{escape(path)}"' in html or f'href="./{escape(path)}"' in html, row

    book = load_workbook(report['excel'], data_only=True)
    try:
        sheet = book[EVIDENCE_LABEL]
        header, record = sheet.values
        values = dict(zip(header, record, strict=True))
        assert values == {'達成基準': CRITERION, '操作経路': row['name'], '対象': row['target'],
                          '環境': row['environment'], '取得状態': STATUS_LABELS[row['status']],
                          '理由': row['reason'], '入力前の画像': row['before_image'] or None,
                          '入力後の画像': row['after_image'] or None, '操作の証拠': row['evidence']}, values
        for column in ('入力前の画像', '入力後の画像', '操作の証拠'):
            cell = sheet.cell(row=2, column=header.index(column) + 1)
            if cell.value:
                assert cell.hyperlink is not None and cell.hyperlink.target == cell.value, cell
            else:
                assert cell.hyperlink is None, cell
    finally:
        book.close()


def count_near_target_differences(before_image, after_image, rect, size):
    x, y, width, height = (rect[key] for key in ('left', 'top', 'width', 'height'))
    margin = 10
    bounds = (max(0, floor(x) - margin), max(0, floor(y) - margin),
              min(size[0], ceil(x + width) + margin), min(size[1], ceil(y + height) + margin))
    with Image.open(before_image) as before, Image.open(after_image) as after:
        pixels_before = before.convert('RGB').crop(bounds).get_flattened_data()
        pixels_after = after.convert('RGB').crop(bounds).get_flattened_data()
        return sum(first != second for first, second in zip(pixels_before, pixels_after, strict=True))


def inspect(run, report, plan, size, expected_status, expected_reason, expected_difference, screenshots):
    result = audit.load(report['json'])
    assert not result['audit_complete']
    assert next(item for item in result['criteria'] if item['id'] == CRITERION)['status'] == 'unverified'
    assert {item['outcome'] for item in result['cases'] if item['criterion'] == CRITERION} == {'not_run'}
    assert not any(item['criterion'] == CRITERION for item in result['machine_checks'])
    row, = result['focus_evidence']
    expected_step = plan['steps'][-1]
    assert row['criterion'] == CRITERION and row['target'] == expected_step['focus'] and row['name'] == plan['name'], row
    assert Path(row['evidence']).name == 'keyboard-check.json', row
    proof, events = load_proof(run, row['evidence'])
    assert proof['id'] == plan['id'] and len(proof['steps']) == len(plan['steps']), proof
    for step, config_step in zip(proof['steps'], plan['steps'], strict=True):
        event = trusted_input(step, events)
        assert event['type'] == 'keydown' and event['key'] == config_step['key'], event
    last = proof['steps'][-1]
    assert last['after']['id'] == expected_step['focus'][1:], last
    pair = last['focus_images']
    assert row['status'] == pair['status'] == expected_status, pair
    assert row['reason'] == pair['reason'] and row['reason'], row
    if expected_reason is not None:
        assert pair['reason_code'] == expected_reason, pair
    assert_report_formats(report, row)

    paths = [row['before_image'], row['after_image']]
    assert paths == [pair.get(phase, {}).get('image', '') for phase in ('before', 'after')], pair
    if expected_status == 'skipped':
        assert not any(paths), pair
        assert not list(run.glob('evidence/*/focus-*.png')), pair
        manifest = audit.load(run / 'capture-manifest.json')
        total = sum(item['status'] == 'captured' for item in manifest['inspection']['screenshots'])
        assert total == (0 if screenshots == 'off' else 2), manifest['inspection']
        return {'status': expected_status, 'reason': expected_reason}

    assert all(paths), pair
    before, after = pair['before'], pair['after']
    assert pair['selector'] == expected_step['focus'] and before['focused'] is False and after['focused'] is True, pair
    assert before['url'] == after['url'] == result['url'] and before['time_origin'] == after['time_origin'], pair
    graph = audit.load(run / 'exploration.json')
    for path, snapshot in zip(paths, (before, after), strict=True):
        assert Path(path).parent == Path(row['evidence']).parent, (row, path)
        assert audit.evidence_item(run, path) in graph['proof'], path
        viewport = snapshot['viewport']
        assert (viewport['width'], viewport['height'], viewport['dpr']) == (*size, 1), viewport
        with Image.open(run / path) as image:
            assert image.size == size, image.size
    if expected_reason == 'target_offscreen':
        assert not before['in_viewport'] and not after['in_viewport'], pair
    if expected_reason == 'geometry_changed':
        assert before['rect'] != after['rect'], pair
    if expected_difference is None:
        return {'status': expected_status, 'reason': expected_reason}
    assert before['rect'] == after['rect'] and before['scroll'] == after['scroll'], pair
    assert before['in_viewport'] and after['in_viewport'], pair
    changed = count_near_target_differences(run / paths[0], run / paths[1], after['rect'], size)
    assert bool(changed) == expected_difference, (expected_step, changed)
    return {'status': expected_status, 'changed_target_pixels': changed}


def trials():
    for index in range(1, 5):
        yield (f'p{index:02d}', f'p{index:02d}.html', '#subject', [], DEFAULT_SIZE, 'all',
               None, index == 2, 'captured', None, index % 2 == 0)
    focus_toggle = [dict(key='Tab', focus='#toggle')]
    yield ('p05-offscreen', 'p05.html', '#subject', focus_toggle, PHONE_SIZE, 'all',
           None, False, 'incomparable', 'target_offscreen', None)
    yield ('p06-visible', 'p06.html', '#after', focus_toggle, PHONE_SIZE, 'all',
           None, False, 'captured', None, True)
    yield ('visible-caret', 'visible-caret.html', '#subject', [], DEFAULT_SIZE, 'all',
           None, False, 'captured', None, True)
    yield ('page-moved', 'layout-shift.html', '#subject', [], DEFAULT_SIZE, 'all',
           None, False, 'incomparable', 'geometry_changed', None)
    yield ('without-images', 'p02.html', '#subject', [], DEFAULT_SIZE, 'off',
           None, False, 'skipped', 'screenshots_off', None)
    yield ('states-only', 'p02.html', '#subject', [], DEFAULT_SIZE, 'states',
           None, False, 'skipped', 'states_only', None)
    yield ('one-image-left', 'p02.html', '#subject', [], DEFAULT_SIZE, 'all',
           3, True, 'skipped', 'image_limit', None)


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    public = out / 'public'
    shutil.copytree(ROOT / 'benchmarks' / 'cases' / CRITERION / 'public', public)
    (public / 'layout-shift.html').write_text('''<!doctype html><title>フォーカスで移動するボタン</title>
        <style>#subject:focus { margin-left: 40px; outline: 3px solid black }</style>
        <button id="subject">保存</button>''')
    (public / 'visible-caret.html').write_text('''<!doctype html><title>入力欄のフォーカス</title>
        <label>氏名 <input id="subject" autocomplete="off"></label>
        <style>#subject { outline: none; border: 2px solid #333; background: white;
            caret-animation: manual; caret-color: red; }</style>''')
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(public))) as server:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f'http://127.0.0.1:{server.server_port}'

        def run_trial(trial):
            name, page, target, prefix, size, screenshots, max_images, pause, status, reason, difference = trial
            plan = route(CRITERION, 'focus-photo', 'キー入力前後のフォーカスを確認する',
                         [*prefix, dict(key='Tab', focus=target, focus_images=True)])
            run, reports = execute(out / name, f'{base}/{page}', plan, size, screenshots, max_images, pause)
            observed = inspect(run, reports, plan, size, status, reason, difference, screenshots)
            return dict(trial=name, **observed)

        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                observations = list(pool.map(run_trial, trials()))
            audit.save(out / 'observed.json', observations)
            print(json.dumps(observations, ensure_ascii=False))
        finally:
            server.shutdown()
            worker.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
