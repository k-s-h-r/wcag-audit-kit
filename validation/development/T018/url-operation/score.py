"""Compare saved URL-only observations with the fixed accordion controls."""
import argparse
from hashlib import sha256
import json
from pathlib import Path


CHECKPOINT = 'キー操作後の領域の表示とフォーカス'


def load(path):
    return json.loads(path.read_text())


def read_evidence(run, proof, path):
    data = (run / path).read_bytes()
    assert sha256(data).hexdigest() == proof[path], path
    return data


def state_evidence(run, graph, proof, edge, expected):
    state_path = edge['evidence_dir'] + '/state.json'
    state = json.loads(read_evidence(run, proof, state_path))
    by_selector = {node['selector']: node for node in state['state']}
    target = by_selector[expected['target']]
    nodes = [node for node in graph['nodes'] if node['environment'] == edge['environment']
             and node['fingerprint'] == edge['fingerprint']]
    assert len(nodes) == 1, nodes
    ax_path = nodes[0]['evidence_dir'] + '/accessibility-tree.json'
    ax = json.loads(read_evidence(run, proof, ax_path))
    button, = (node for node in ax['nodes'] if node.get('role', {}).get('value') == 'button'
               and node.get('name', {}).get('value') == expected['target_name'])
    expanded, = (prop['value']['value'] for prop in button['properties'] if prop['name'] == 'expanded')
    visible = expected['panel'] in by_selector
    assert target['expanded'] == str(visible).lower() and expanded is visible, (state_path, visible, expanded)
    return dict(visible=visible, aria_expanded=target['expanded'], ax_expanded=expanded,
                focus=state.get('deep_focus') or state['focus']['selector'], proof=[state_path, ax_path])


def actions(route):
    return [(step['type'], step['selector'], step.get('key')) for step in route]


def observation(run, graph, proof, report, environment, route, expected):
    candidates = [edge for edge in graph['edges'] if edge['environment'] == environment and actions(edge['route']) == route]
    if not candidates:
        return {'status': 'not_observed'}
    if not route:
        initial, = [node for node in graph['nodes'] if node['environment'] == environment and not node['route']]
        candidates = [edge for edge in candidates if edge['evidence_dir'] == initial['evidence_dir']]
    edge, = candidates
    transition_path = edge['evidence_dir'] + '/transition.json'
    transition = json.loads(read_evidence(run, proof, transition_path))
    assert transition['environment'] == environment and actions(transition['route']) == route
    if (transition['error'] or transition['blocked_requests'] or transition['native_events']
            or len(transition['settling']) != len(route) + 1
            or any(wait['status'] != 'quiet' for wait in transition['settling'])):
        return {'status': 'unconfirmed', 'proof': [transition_path]}
    state = state_evidence(run, graph, proof, edge, expected)
    log_path = edge['evidence_dir'] + '/input-events.json'
    log = json.loads(read_evidence(run, proof, log_path))
    assert not log['truncated']
    opener = expected['target'].split('#')[-1]
    inner = expected['inner'].split('#')[-1]
    mouse_event_indices = [index for index, event in enumerate(log['events']) if event['isTrusted']
                           and event['is_main_frame'] and event['type'] == 'click' and event['pointerType'] == 'mouse']
    click_count = sum(step[0] == 'click' for step in route)
    assert [log['events'][index]['target']['id'] for index in mouse_event_indices] == [opener] * click_count, log_path
    expected_to = {'Enter': opener, 'Space': opener, 'Tab': opener, 'Shift+Tab': inner}
    required_inputs = [step[2] for step in route if step[2] is not None]
    event_indices = []
    start = 0
    for position, key in enumerate(required_inputs, 1):
        event_index = next(index for index in range(start, len(log['events']))
                           if (event := log['events'][index])['isTrusted'] and event['is_main_frame']
                           and event['type'] == 'keydown'
                           and event['target']['id'] == expected_to[key]
                           and event['key'] == ('[character]' if key == 'Space' else key.split('+')[-1])
                           and event['modifiers']['shift'] == (key == 'Shift+Tab')
                           and not any(event['modifiers'][name] for name in ('control', 'alt', 'meta'))
                           and (position < len(required_inputs) or key in ('Tab', 'Shift+Tab')
                                or event['expectedTargetMatched'] is True))
        event_indices.append(event_index)
        start = event_index + 1
    assert len({log['events'][index]['documentId'] for index in event_indices}) <= 1, log_path
    if route and route[-1][0] == 'key':
        assert transition['key_effect']['event_index'] == event_indices[-1], log_path
    machine = [row['outcome'] for row in report['machine_checks']
               if row['evidence'] == transition_path and row['checkpoint'] == CHECKPOINT and row['environment'] == environment]
    state['proof'] += [transition_path, log_path]
    return dict(status='observed', **state, machine=machine, key_event_indices=event_indices,
                mouse_event_indices=mouse_event_indices)


def score(run_dir):
    expected = load(Path(__file__).with_name('expected.json'))
    summary = []
    for case in expected['tests']:
        root = run_dir / Path(case['file']).stem / 'page'
        run = root / 'work'
        graph = load(run / 'exploration.json')
        assert not graph['running'] and not graph['deferred'], root
        proof = {item['path']: item['sha256'] for item in graph['proof']}
        report = load(root / 'data/report.json')
        assert not report['audit_complete'], root
        page = dict(file=case['file'], profile='quick' if graph['quick_explore'] else 'full',
                    steps=graph['steps'], pending=len(graph['queue']),
                    omitted=graph.get('omitted_candidates', {}), audit_complete=report['audit_complete'], viewports={})
        for environment in expected['environments']:
            target = expected['target']
            enter = [('key', target, 'Enter')]
            tab = enter + [('press', 'body', 'Tab')]
            returned = tab + [('press', 'body', 'Shift+Tab')]
            click = [('click', target, None)]
            routes = {'initial': [], 'pointer': click, 'pointer_close': click + click, 'enter': enter,
                      'space': [('key', target, 'Space')], 'tab': tab, 'return': returned, 'close': returned + enter}
            results = {name: observation(run, graph, proof, report, environment, route, expected)
                       for name, route in routes.items()}
            assert results['initial'].get('visible') is False, results
            for name in ('pointer', 'enter', 'space'):
                if results[name]['status'] == 'observed':
                    assert results[name]['visible'] is case[f'{name}_opens'], results[name]
            assert all(results[name]['status'] == 'observed' for name in ('pointer', 'pointer_close', 'enter')), results
            assert results['pointer_close']['visible'] is False, results['pointer_close']
            if not graph['quick_explore']:
                assert results['space']['status'] == 'observed', results['space']
            if case['enter_opens']:
                assert results['tab']['status'] == 'observed', results['tab']
            for name, focus in [('tab', expected['inner']), ('return', target), ('close', target)]:
                if results[name]['status'] == 'observed':
                    assert results[name]['focus'] == focus and results[name]['visible'] is (name != 'close'), results[name]
            initial, = [node for node in graph['nodes'] if node['environment'] == environment and not node['route']]
            image = initial['evidence_dir'] + '/page.png'
            results['initial']['proof'].append(image)
            results['initial']['image_sha256'] = sha256(read_evidence(run, proof, image)).hexdigest()
            page['viewports'][environment] = results
        summary.append(page)
    for environment in expected['environments']:
        hashes = {page['viewports'][environment]['initial']['image_sha256'] for page in summary}
        assert len(hashes) == 1, (environment, hashes)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(score(args.run), ensure_ascii=False, indent=2))
