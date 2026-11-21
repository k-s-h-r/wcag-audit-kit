"""Check the trusted Escape results and compare the 24-step route budgets."""
import argparse
from pathlib import Path
import sys
from urllib.parse import unquote

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from benchmarks import core, url_only_machine
from benchmarks.url_only_machine_score import score_page
from keyboard_checks import matching_keydown


NESTED = {
    '045': ('child_open', 'child', '#inner-name'),
    '046': ('child_closed', 'parent', '#inner-opener'),
    '062': ('child_closed', 'outside', '#outside'),
    '063': ('child_closed', 'parent', '#inner-opener'),
}
WIDTHS = ('desktop', 'narrow')
PARENT = {'type': 'click', 'selector': '#launch'}
CHILD = {'type': 'click', 'selector': '#inner-opener'}
CHILD_ENTER = {'type': 'key', 'selector': '#inner-opener', 'key': 'Enter'}
INPUT_CLICK = {'type': 'click', 'selector': '#outer-name'}
INPUT_FILL = {'type': 'fill', 'selector': '#outer-name', 'value': 'Accessibility audit'}
ESCAPE = {'type': 'press', 'selector': 'body', 'key': 'Escape'}


def evidence(run, case):
    page = run / 'pages' / case / 'page'
    work = page / 'work'
    return work, core.load(work/'exploration.json'), core.load(page/'data/report.json')


def routes(graph):
    return [[edge['environment'], edge['route']] for edge in graph['edges']]


def following_tab(work, graph):
    records = []
    for edge in graph['edges']:
        if edge.get('dialog_focus') != 'tab':
            continue
        entry = core.load(work / edge['evidence_dir'] / 'dialog-focus.json')
        records.append(dict(environment=edge['environment'], route=edge['route'], status=entry['status'],
                            focus=entry['after_tab']['focus']))
    return records


def nested(run, case, expected):
    work, graph, report = evidence(run, case)
    observed = {}
    proof = {item['path']: item['sha256'] for item in graph['proof']}
    for step, edge in enumerate(graph['edges'], 1):
        if not edge.get('prioritized_nested_escape'):
            continue
        env = edge['environment']
        assert env not in observed and (step, env) in {(14, 'desktop'), (16, 'narrow')}
        assert edge['route'] == [PARENT, CHILD, ESCAPE]
        assert not edge['error'] and not edge['blocked_requests'] and not edge['native_events']
        path = edge['nested_dialog_evidence']
        receipt = core.load(work / path)
        log_path = edge['evidence_dir'] + '/input-events.json'
        log = core.load(work / log_path)
        assert not log['truncated']
        assert 0 <= receipt['event_index'] < len(log['events'])
        event = log['events'][receipt['event_index']]
        assert matching_keydown(event, 'Escape') and event['expectedTargetMatched'] is True
        assert event['target']['id'] == 'inner-name' and event['url'] == receipt['before']['url']
        click_targets = [entry['target']['id'] for entry in log['events'][:receipt['event_index']]
                         if entry['type'] == 'click' and entry['pointerType'] == 'mouse'
                         and entry['isTrusted'] and entry['is_main_frame'] and entry['documentId'] == event['documentId']]
        assert click_targets == ['launch', 'inner-opener']
        assert receipt['before']['modals'] == ['#outer', '#subject']
        assert (receipt['status'], receipt['focus_layer'], receipt['after']['focus']) == expected
        assert {key: receipt['before'][key] for key in ('url', 'document_start')} == {
            key: receipt['after'][key] for key in ('url', 'document_start')}
        assert all(core.file_hash(work / item) == proof[item] for item in (path, log_path))
        shown, = (row for row in report['exploration']['dialog_observations'] if row['environment'] == env)
        assert shown['route'] == edge['route'] and shown['evidence'] == path and shown['input_evidence'] == log_path
        assert (shown['status'], shown['focus_layer'], shown['focus']) == expected
        assert 'outcome' not in shown and not any(row['evidence'] == path for row in report['machine_checks'])
        observed[env] = {'step': step, 'status': receipt['status'], 'focus_layer': receipt['focus_layer'],
                         'focus': receipt['after']['focus'], 'evidence': path, 'input_evidence': log_path}
    assert set(observed) == set(WIDTHS)
    report_dir = work.parent / 'reports'
    html = (report_dir/'report.html').read_text()
    assert all(value[key] in html for value in observed.values() for key in ('evidence', 'input_evidence'))
    book = load_workbook(report_dir/'report.xlsx')
    try:
        links = {(report_dir / unquote(row[10].hyperlink.target)).resolve()
                 for row in list(book['操作調査'].rows)[1:] if row[10].hyperlink}
        assert links == {(work / value['evidence']).resolve() for value in observed.values()}
    finally:
        book.close()
    return observed


def child_enter(work, graph):
    observed = []
    for step, edge in enumerate(graph['edges'], 1):
        if edge['route'] != [PARENT, CHILD_ENTER]:
            continue
        directory = work / edge['evidence_dir']
        record = core.load(directory/'dialog-focus.json')
        log = core.load(directory/'input-events.json')
        index = record['close_event_index'] - 1
        assert not log['truncated'] and 0 <= index < len(log['events'])
        event = log['events'][index]
        assert matching_keydown(event, 'Enter') and event['expectedTargetMatched'] is True
        assert event['target']['id'] == 'inner-opener' and record['after_close']['modals'] == ['#outer', '#subject']
        observed.append((step,edge['environment']))
    assert observed == [(17, 'desktop'), (18, 'narrow')]


def executed_default(run, baseline):
    results = {}
    for case, old in baseline.items():
        work, graph, report = evidence(run, case)
        assert graph['limits'] == {'max_steps': 24, 'max_states': 16, 'max_depth': 3} and graph['steps'] == 24
        assert following_tab(work, graph) == old['following_tab']
        assert report['scope_conformance']['status'] == 'unverified'
        observed = routes(graph)
        pending = [[job['environment'], job['route']] for job in graph['queue']]
        changes = {}
        if case in NESTED:
            deferred = [[env, [PARENT, INPUT_CLICK]] for env in WIDTHS]
            additional = [[env, [PARENT, CHILD, ESCAPE]] for env in WIDTHS]
            assert [route for route in old['routes'] if route not in deferred] == [
                route for route in observed if route not in additional]
            assert all(route in [[job['environment'], job['route']] for job in graph['queue']
                                 if job.get('nested_escape_deferred_click')] for route in deferred)
            queued_now = [route for route in pending if route not in old['queue']]
            queued_before = [route for route in old['queue'] if route not in pending]
            omitted = [[env, [PARENT, INPUT_FILL, INPUT_FILL]] for env in WIDTHS]
            assert queued_now == deferred and all(route in queued_before for route in additional + omitted)
            assert len(queued_before) == len(additional + omitted)
            assert graph['omitted_candidates']['frontier'] == old['omitted_candidates']['frontier'] + 2
            child_enter(work, graph)
            changes = nested(run, case, NESTED[case])
        else:
            assert observed == old['routes']
            assert pending == old['queue'] and graph['omitted_candidates'] == old['omitted_candidates']
            assert not any(edge.get('prioritized_nested_escape') for edge in graph['edges'])
        results[case] = {'implementation_digest': graph['implementation_digest'], 'steps': graph['steps'],
                         'observations': changes, 'following_tab': following_tab(work, graph),
                         'pending_before': len(old['queue']), 'pending_after': len(pending),
                         'added_to_pending': [route for route in pending if route not in old['queue']],
                         'removed_from_pending': [route for route in old['queue'] if route not in pending],
                         'omitted_candidates': graph['omitted_candidates']}
    return results


def controls(run, supplemental, baseline):
    _, uninterrupted, _ = evidence(run, '045')
    work, resumed, _ = evidence(supplemental, 'resumed')
    partial = core.load(supplemental/'pages/resumed/exploration-at-6.json')
    assert partial['steps'] == 6 and partial['limits']['max_steps'] == 6
    slots = [(node['environment'], node['nested_escape_slot']) for node in partial['nodes'] if 'nested_escape_slot' in node]
    assert len(slots) == 2 and {width for width, _ in slots} == set(WIDTHS)
    assert all(not slot.get('used') for _, slot in slots)
    assert resumed['proof'][:len(partial['proof'])] == partial['proof']
    assert all(core.audit.evidence_item(work, item['path']) == item for item in partial['proof'])
    assert routes(resumed) == routes(uninterrupted) and resumed['limits'] == uninterrupted['limits']
    results = nested(supplemental, 'resumed', NESTED['045'])
    _, listener, _ = evidence(supplemental, 'pointer-listener')
    assert routes(listener) == baseline['045']['routes']
    assert [[job['environment'], job['route']] for job in listener['queue']] == baseline['045']['queue']
    assert not any(node.get('nested_escape_slot') for node in listener['nodes'])
    return {'resumed': results, 'partial_steps': partial['steps'], 'partial_proof_count': len(partial['proof']),
            'same_routes_after_resume': True, 'pointer_listener_same_routes': True}


def scores(run, baseline):
    recorded = core.load(ROOT/'validation/development/T030/run-003/score.json')
    expected = [row for row in recorded['rows'] if row['page_id'] in baseline]
    current = []
    for page in url_only_machine.inventory(core.corpus()):
        if page['id'] in baseline:
            rows, unmatched, receipt = score_page(run, page)
            assert receipt['completed'] and not unmatched, (page['id'], unmatched)
            current.extend(rows)
    def verdict(row):
        return (row['page_id'], row['target'], row['state'], row['checkpoint'], row['status'],
                {env:[check['outcome'] for check in data['verdicts']] for env,data in row['environments'].items()})
    assert list(map(verdict, current)) == list(map(verdict, expected)), (list(map(verdict, current)), list(map(verdict, expected)))
    return current


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--supplemental', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    baseline = core.load(Path(__file__).with_name('run-001')/'default-routes.json')
    results = executed_default(args.run, baseline)
    results['controls'] = controls(args.run, args.supplemental or args.run, baseline)
    results['score_rows'] = scores(args.run, baseline)
    core.save(args.out, results)
