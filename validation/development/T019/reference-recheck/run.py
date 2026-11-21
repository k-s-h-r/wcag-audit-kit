#!/usr/bin/env python3
"""Replay a hidden ARIA reference change through quick and whole-page page-audit."""
import argparse
from collections import Counter
from functools import partial
from hashlib import sha256
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests'))
from operation_impact_browser import Handler, LIMITS, audit, page_explorer, signatures

CLI = ROOT / 'skills/wcag-page/scripts/audit.py'
RULE = 'aria-valid-attr-value'
WIDTHS = ('desktop', 'narrow')
ROUTE = [{'type': 'click', 'selector': '#act'}]
CASES = {'add': (0, 1), 'remove': (1, 0), 'move': (1, 1)}
EXPECTED = {0: 'violations', 1: 'passes'}


def create_fixture(path, before, after):
    stable = ''.join(f'<div id="stable-{i}" aria-hidden="false" tabindex="-1">Note {i}</div>'
                     for i in range(8))
    reference = '<span id="reference" hidden>Related content</span>'
    if before == after:
        action = "document.getElementById('next-area').append(document.getElementById('reference'));"
    elif after:
        action = "document.getElementById('far').insertAdjacentHTML('beforeend', " + json.dumps(reference) + ");"
    else:
        action = "document.getElementById('reference').remove();"
    path.write_text(f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>Reference check</title>
<main><h1>Reference check</h1><button id="act" type="button">Update reference</button>
<button id="subject" type="button" aria-controls="reference" aria-expanded="true">Related guidance</button>
{stable}</main><div id="far" style="margin-top:1600px;padding:1em">Remote area{reference if before else ''}</div>
<div id="next-area">Adjacent area</div>
<script>document.getElementById('act').onclick = () => {{ {action} }};</script></html>
""", encoding='utf-8')


def run_cli(output, url, settings, command, *, quick):
    output.mkdir()
    args = [sys.executable, str(CLI), 'page-audit', '--url', url, '--out', str(output / 'page'),
            '--config', str(settings), '--mode', 'machine', '--screenshots', 'off']
    for key, value in LIMITS.items():
        args.extend(['--' + key.replace('_', '-'), str(value)])
    phases = (('initial', ['--initial-only']), ('explore', ['--resume', '--quick-explore'])) if quick \
        else (('explore', ['--explore']),)
    requests = Handler.requests['/' + url.rsplit('/', 1)[-1]]
    for phase, extra in phases:
        with (output / (phase + '.log')).open('w') as log:
            print(json.dumps(args + extra), file=log, flush=True)
            result = subprocess.run(args + extra, stdout=log, stderr=subprocess.STDOUT, timeout=240)
        assert result.returncode == 0, (output, phase, result.returncode)
    work = audit.run_layout.ledger(output / 'page')
    graph = page_explorer.status(work)
    print(command, url, len(graph['nodes']), 'states', flush=True)
    return work, graph, Handler.requests['/' + url.rsplit('/', 1)[-1]] - requests


def receipt(work, graph, env, route):
    edge, = [edge for edge in graph['edges'] if edge['environment'] == env and edge['route'] == route
             and not edge.get('initial_input')]
    assert edge['error'] is None and not edge['blocked_requests'] and not edge['native_events'], edge
    directory = work / edge['evidence_dir']
    state = audit.load(directory / 'state.json')
    inventory = audit.load(directory / 'inventory.json')
    if route:
        events = audit.load(directory / 'input-events.json')
        assert not events['truncated'] and any(event['type'] == 'click' and event['isTrusted']
            and event['is_main_frame'] and event['target']['id'] == 'act' for event in events['events']), events
    return directory, state, inventory


def corresponding_outcome(results):
    matches = [(kind, node) for kind in ('passes', 'violations', 'incomplete')
               for rule in results[kind] if rule['id'] == RULE
               for node in rule['nodes'] if node['target'] == ['#subject']]
    assert len(matches) == 1, matches
    return matches[0]


def compare(out, inputs, quick, whole, expected):
    quick_work, quick_graph, quick_requests = quick
    full_work, full_graph, full_requests = whole
    before_count, after_count = inputs
    comparisons = {}
    for env in WIDTHS:
        base_dir, before, before_inventory = receipt(quick_work, quick_graph, env, [])
        quick_dir, after, after_inventory = receipt(quick_work, quick_graph, env, ROUTE)
        full_dir, full, _ = receipt(full_work, full_graph, env, ROUTE)
        assert before['state'] == after['state'] == full['state']
        assert before['operation_inputs']['#subject'] == after['operation_inputs']['#subject']
        counts = [sum(node['id'] == 'reference' for node in inventory['nodes'])
                  for inventory in (before_inventory, after_inventory)]
        assert counts == [before_count, after_count], counts
        if expected == 'fixed':
            observed = [data.get('operation_aria_controls_resolved', []) for data in (before, after, full)]
            assert observed == [[['#subject', 'reference']] * count
                                for count in [before_count, after_count, after_count]], observed
        assert full['state_labels'][0]['matched']
        full_results = audit.load(full_dir / 'axe.json')
        base_results = audit.load(base_dir / 'axe.json')
        cases_outcomes = [corresponding_outcome(results) for results in (base_results, full_results)]
        assert [item[0] for item in cases_outcomes] == [EXPECTED[before_count], EXPECTED[after_count]], cases_outcomes
        assert cases_outcomes[0][1]['html'] == cases_outcomes[1][1]['html']
        scope = audit.load(quick_dir / 'operation-impact.json')['axe']
        if (quick_dir / 'axe.json').is_file():
            results = audit.load(quick_dir / 'axe.json')
        else:
            assert scope['mode'] == 'same_state'
            results = audit.load(quick_work / scope['baseline'])
        match = signatures(results) == signatures(full_results)
        must_recheck = before_count != after_count and expected == 'fixed'
        assert match == (must_recheck or before_count == after_count), (env, match, scope)
        assert (quick_dir / 'axe.json').is_file() == must_recheck, (env, scope)
        assert RULE not in scope.get('reused', {}), scope
        full_counts = Counter({kind: sum(len(rule['nodes']) for rule in full_results[kind] if rule['id'] == RULE)
                               for kind in ('passes', 'violations', 'incomplete', 'inapplicable')})
        comparisons[env] = dict(same_axe_categories_and_targets=match, before=cases_outcomes[0][0],
            quick_after=corresponding_outcome(results)[0], whole_after=cases_outcomes[1][0], reference_counts=counts,
            value_rule_recorded_targets=sum(full_counts.values()), whole_value_rule=full_counts, mode=scope['mode'],
            value_rule_quick_rechecked=sum(full_counts.values()) if must_recheck else 0,
            reuse={rule: len(nodes) for rule, nodes in scope.get('reused', {}).items()},
            rechecked={rule: len(nodes) for rule, nodes in scope.get('rechecked', {}).items()},
            quick_fingerprints=[page_explorer.fingerprint(data) for data in (before, after)],
            quick_evidence=str(quick_dir.relative_to(out)), initial_evidence=str(base_dir.relative_to(out)),
            whole_evidence=str(full_dir.relative_to(out)))
    return dict(environments=comparisons, quick_states=len(quick_graph['nodes']), whole_states=len(full_graph['nodes']),
                quick_document_gets=quick_requests, whole_document_gets=full_requests)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expect', choices=('baseline', 'fixed'), default='fixed')
    args = parser.parse_args()
    out = args.out.resolve()
    public = out / 'public'
    public.mkdir(parents=True)
    for case, inputs in CASES.items():
        create_fixture(public / (case + '.html'), *inputs)
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=public)) as server:
        port = server.server_port
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            measurements = []
            for case, inputs in CASES.items():
                page = case + '.html'
                url = f'http://127.0.0.1:{port}/{page}'
                config = audit.init_config(url)
                config['environments'] = config['environments'][:2]
                config['keyboard_steps'] = 2
                quick_settings, full_settings = out / (case + '-quick.json'), out / (case + '-whole.json')
                audit.save(quick_settings, config)
                check = {'selector': '#reference', 'count': inputs[1], 'visible': False}
                if case == 'move':
                    check['selector'] = '#next-area > #reference'
                label = {'id': 'after-reference-edit', 'actions': ROUTE, 'assert': [check]}
                audit.save(full_settings, dict(config, exploration_labels=[label]))
                measurements.append((case, inputs, url, quick_settings, full_settings))
            fixed_paths = [*sorted(public.iterdir()), *sorted(out.glob('*.json'))]
            receipt = dict(limits=LIMITS, expected=args.expect, reference_counts=CASES,
                           sha256={p.name: sha256(p.read_bytes()).hexdigest() for p in fixed_paths})
            audit.save(out / 'plan.json', receipt)
            results = {}
            for case, inputs, url, quick_settings, full_settings in measurements:
                quick = run_cli(out / (case + '-quick'), url, quick_settings, 'quick', quick=True)
                whole = run_cli(out / (case + '-whole'), url, full_settings, 'whole', quick=False)
                results[case] = compare(out, inputs, quick, whole, args.expect)
                audit.save(out / 'results.json', results)
        finally:
            server.shutdown()
            thread.join()


if __name__ == '__main__':
    main()
