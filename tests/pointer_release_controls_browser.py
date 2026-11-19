"""Explore a visible pointer-release control and its nested state in Chromium."""
import argparse
import functools
import json
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'skills/wcag-audit-kit/scripts'))
import audit
from browser_capture import page_id


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def verify(out, url):
    config = audit.init_config(url)
    config['environments'] = config['environments'][:1]
    config['keyboard_steps'] = 4
    settings = out/'config.json'
    run = out/'run'
    audit.save(settings, config)
    assert audit.main(['page-audit', '--url', url, '--config', str(settings), '--mode', 'machine',
                       '--out', str(run), '--max-states', '10', '--max-steps', '18', '--max-depth', '2']) == 0
    run = audit.run_layout.ledger(run)
    graph = audit.load(run/'exploration.json')
    initial = next(node for node in graph['nodes'] if not node['route'])
    controls = {control['selector']: control for control in initial['controls']}
    assert set(controls) == {'#release', '#registered'}, controls
    assert controls['#release']['events'] == ['onpointerup'], controls['#release']
    assert controls['#registered']['events'] == ['pointerup'], controls['#registered']

    release = {'selector': '#release', 'type': 'click'}
    registered = [{'selector': '#registered', 'type': 'click'}]
    nested = [release, {'selector': '#nested', 'type': 'click'}]
    opened = next(node for node in graph['nodes'] if node['route'] == [release])
    assert '#nested' in {control['selector'] for control in opened['controls']}, opened
    assert any(node['route'] == registered for node in graph['nodes']), graph['nodes']

    release_keyboard = [edge for edge in graph['edges'] if len(edge['route']) == 1 and
                        edge['route'][0]['selector'] == '#release' and edge['route'][0]['type'] == 'key']
    assert {edge['route'][0]['key'] for edge in release_keyboard} == {'Enter', 'Space'}, release_keyboard
    assert all(edge['error'] and 'Tab' in edge['error'] and not edge.get('fingerprint')
               for edge in release_keyboard), release_keyboard

    image_findings = []
    for node in graph['nodes']:
        raw = audit.load(run/node['evidence_dir']/'axe.json')
        if any(rule['id'] == 'image-alt' and any(match['target'] == ['#nested-image'] for match in rule['nodes'])
               for rule in raw['violations']):
            image_findings.append(node)
    assert [node['route'] for node in image_findings] == [nested], image_findings
    image_node, = image_findings
    report = audit.load(audit.run_layout.report_files(run, single=True).json)
    image_row, = [row for row in report['machine_checks']
                  if row['checkpoint'] == 'axe / image-alt' and row['outcome'] == 'failed']
    assert image_row['criterion'] == '1.1.1' and image_row['target'] == "['#nested-image']", image_row
    assert image_row['capture'] == image_node['capture'], image_row
    assert image_row['evidence'] == f"{image_node['evidence_dir']}/axe.json", image_row
    assert audit.evidence_item(run, image_row['evidence']) in graph['proof'], image_row
    outcomes = audit.outcomes(run)['counts']
    assert set(outcomes) == {'not_run'}, outcomes
    result = {'nested_image_alt_route': nested, 'report_capture': image_row['capture'],
              'report_evidence': image_row['evidence'], 'registered_pointer_route': registered,
              'keyboard_unreachable': [edge['route'][0]['key'] for edge in release_keyboard]}
    audit.save(out/'observed.json', result)
    print(json.dumps(result, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    out = parser.parse_args().out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    handler = functools.partial(Handler, directory=str(ROOT/'tests/fixtures'))
    with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            verify(out, f'http://127.0.0.1:{server.server_port}/pointer-release-controls.html')
        finally:
            server.shutdown()


if __name__ == '__main__':
    main()
