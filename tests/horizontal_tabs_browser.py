"""Compare horizontal tab navigation and its page reports in Chromium."""
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

from border_contrast_paths_browser import QuietHandler
from keyboard_checks_browser import ROOT, audit


def key(target, name, **conditions):
    return dict(type='key', selector=target, key=name, **conditions)


def collect_and_verify(out, url, variant, baseline):
    out.mkdir()
    config = audit.init_config(url)
    config['environments'] = config['environments'][:1]
    config['keyboard_steps'] = 0
    settings, run = out/'config.json', out/'run'
    audit.save(settings, config)
    result = subprocess.run([sys.executable, str(ROOT/'skills/wcag-audit-kit/scripts/audit.py'),
        'page-audit', '--url', url, '--config', str(settings), '--out', str(run), '--mode', 'machine',
        '--max-depth', '2', '--max-states', '30', '--max-steps', '72'],
        capture_output=True, text=True, timeout=150)
    (out/'command.log').write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    files = json.loads(result.stdout.strip().splitlines()[-1])
    return verify(audit.run_layout.ledger(run), files, variant, baseline)


def verify(run, files, variant, baseline):
    graph = audit.load(run/'exploration.json')
    edges = graph['edges']
    assert any(edge['route'] == [{'type': 'click', 'selector': '#after'}] and edge.get('fingerprint')
               for edge in edges)
    if baseline or variant == 'vertical':
        directions = [job for job in edges + graph['queue']
                      if any(step.get('key') in {'ArrowLeft', 'ArrowRight'} for step in job['route'])]
        assert not directions, directions
        return {'arrows': 0}

    report = audit.load(files['json'])
    rows = report['machine_checks']
    assert all(criterion['status'] == 'unverified'
               for criterion in report['criteria'] if criterion['id'] in {'1.1.1', '2.1.1'})
    assert not any(row['criterion'] == '2.1.1' and row['target'] in {'#before', '#after'}
                   and row['outcome'] == 'failed' for row in rows)

    def verify_state(route, focused, selected):
        edge, = [edge for edge in edges if edge['route'] == route]
        assert not edge['error'], edge
        evidence = run/edge['evidence_dir']
        events = audit.load(evidence/'input-events.json')['events']
        for step in route:
            assert any(event['type'] == 'keydown'
                       and event['key'] == ('[character]' if step['key'] == 'Space' else step['key'])
                       and event['isTrusted'] and event['target']['id'] == step['selector'][1:]
                       for event in events), events
        state = audit.load(evidence/'state.json')
        assert state['focus']['selector'] == focused, state['focus']
        assert [node['selector'] for node in state['state'] if node['role'] == 'tab' and node['selected'] == 'true'] == [selected]
        assert [node['selector'] for node in state['state'] if node['role'] == 'tabpanel'] == [selected+'-panel']
        if route[-1]['key'] in {'ArrowLeft', 'ArrowRight'}:
            assert edge['focus_after'] == focused
            row, = [row for row in rows if row['evidence'] == edge['evidence_dir']+'/transition.json']
            assert '入力後のフォーカスは '+focused in row['observed']
        return edge

    right, left = key('#start', 'ArrowRight'), key('#start', 'ArrowLeft')
    if variant == 'click-only':
        for arrow in (right, left):
            edge = verify_state([arrow], '#start', '#start')
            assert not any(row['checkpoint'] == 'axe / image-alt' and row['outcome'] == 'failed' and
                           row['evidence'] == edge['evidence_dir']+'/axe.json' for row in rows)
        return {'arrows_without_panel_change': 2}

    if variant == 'manual':
        pending = verify_state([right], '#after', '#start')
        assert any(node['evidence_dir'] == pending['evidence_dir'] for node in graph['nodes'])
        enter = verify_state([right, key('#after', 'Enter', focused_only=True)], '#after', '#after')
        space = verify_state([right, key('#after', 'Space', focused_only=True)], '#after', '#after')
        assert enter['fingerprint'] == space['fingerprint']
        found = [(enter, '#after-image')]
    else:
        found = [(verify_state([arrow], target, target), target+'-image')
                 for arrow, target in ((right, '#after'), (left, '#before'))]

    html = Path(files['html']).read_text()
    book = load_workbook(files['excel'], read_only=True, data_only=True)
    try:
        sheet = list(book['機械検査'].values)
        for edge, image in found:
            node = next(node for node in graph['nodes'] if node['evidence_dir'] == edge['evidence_dir'])
            row, = [row for row in rows if row['capture'] == node['capture']
                    and row['checkpoint'] == 'axe / image-alt' and row['outcome'] == 'failed']
            assert row['target'] == str([image]), row
            assert all(step['key'] in row['state_label'] for step in edge['route']), row
            assert audit.evidence_item(run, row['evidence']) in graph['proof']
            assert image in html and f'href="{audit.run_layout.href(Path(files["html"]), run / row["evidence"])}"' in html
            assert any(row['target'] in cells and row['evidence'] in cells for cells in sheet)
    finally:
        book.close()
    return {'arrow_routes_reaching_panels': len(found)}


def main(out, baseline):
    out.mkdir(parents=True, exist_ok=False)
    handler = partial(QuietHandler, directory=str(ROOT/'tests/fixtures'))
    variants = ('auto', 'manual', 'click-only', 'vertical')
    with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                jobs = {variant: pool.submit(collect_and_verify, out/variant,
                    f'http://127.0.0.1:{server.server_port}/horizontal-tabs.html?variant={variant}',
                    variant, baseline) for variant in variants}
                results = {variant: job.result() for variant, job in jobs.items()}
        finally:
            server.shutdown()
            thread.join()
    audit.save(out/'observed.json', results)
    print(json.dumps(results, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    main(args.out, args.baseline)
