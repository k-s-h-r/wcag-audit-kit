"""Exercise URL-only continuation of a keyboard route through a three-level menu."""
import argparse
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmarks import core, runner, url_only


def route_signature(edge):
    return [(step['type'], step['selector'], step.get('key')) for step in edge['route']]


def verify_case(output, origin, page, expected_open_focus):
    assert url_only.collect_page(origin + '/' + page, output, url_only.PROFILES['quick'])
    root = core.audit.run_layout.ledger(output / 'page')
    graph = core.load(root / 'exploration.json')
    first_click = [('click', '#level1', None)]
    first_key = [('key', '#level1', 'Enter')]
    second_key = first_key + [('key', '#level2', 'Enter')]
    after_tab = second_key + [('press', 'body', 'Tab')]

    for environment in ('desktop', 'narrow'):
        observations = list(url_only.observed_transitions(root, graph, environment))
        signed = {tuple(route_signature(edge)): (edge, folder, state) for edge, folder, state in observations}
        pointer, _, _ = signed[tuple(first_click)]
        opener, _, _ = signed[tuple(first_key)]
        opened, directory, state = signed[tuple(second_key)]
        tabbed, _, _ = signed[tuple(after_tab)]
        assert pointer['fingerprint'] == opener['fingerprint']
        assert graph['edges'].index(pointer) < graph['edges'].index(opener)
        assert opener['continued_keyboard_opening'] and opened['continued_keyboard_opening']
        assert sum(node['environment'] == environment and node['fingerprint'] == opener['fingerprint']
                   for node in graph['nodes']) == 1
        assert url_only.visible(state, '#leaf')
        assert opened['focus_after'] == expected_open_focus, opened
        events = core.load(directory / 'input-events.json')['events']
        enter_targets = [event['target']['id'] for event in events
                         if event['isTrusted'] and event['type'] == 'keydown' and event['key'] == 'Enter']
        assert enter_targets == ['level1', 'level2'], enter_targets
        if expected_open_focus == '#level2':
            assert tabbed['focus_after'] == '#leaf', tabbed
        else:
            assert tabbed['focus_after'] != '#leaf', tabbed
        assert sum(job['environment'] == environment and bool(job['route']) for job in graph['queue']) <= 12
    assert graph['steps'] <= 24, graph['steps']


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    public = out / 'public'
    shutil.copytree(core.ROOT / 'benchmarks/cases/2.4.3/public', public)
    http = runner.server(public)
    try:
        origin = f'http://127.0.0.1:{http.server_port}'
        verify_case(out / 'valid', origin, 'p03.html', '#level2')
        verify_case(out / 'focus-jump', origin, 'p04.html', '#after')
    finally:
        http.shutdown()
        http.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
