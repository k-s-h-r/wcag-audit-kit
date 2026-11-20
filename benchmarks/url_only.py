#!/usr/bin/env python3
"""Measure the unaided wcag-page entry point on selected dynamic fixtures."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmarks import core, runner


# Scoring targets are read after collection. The production CLI receives only the URL
# and the ordinary workflow switches. Keep the normal and faulty case in each pair.
CASES = {
    '1.1.1': {'c09': 'image', 'c10': 'image'},
    '2.4.3': {'c03': 'menu', 'c04': 'menu', 'c09': 'dialog', 'c10': 'dialog'},
    '4.1.2': {'c07': 'combobox', 'c08': 'combobox'},
}
PROFILES = {
    'quick': ['--quick-explore'],
    'full': ['--explore', '--max-steps', '24', '--max-states', '16', '--max-depth', '3'],
}
ACTIVATION_KEYS = {'Enter', 'Space'}
MENU_KEYS = (('#level1', ACTIVATION_KEYS), ('#level2', ACTIVATION_KEYS))
COMBO_KEYS = (('#subject', {'ArrowDown'}),)
DIALOG_ACTIONS = {'button-close-click': ('click', None), 'button-close-enter': ('key', 'Enter'),
                  'button-close-space': ('key', 'Space')}
RULE_GROUPS = {'passes': 'passed', 'violations': 'failed', 'incomplete': 'cant_tell'}


def collect_page(url, output, profile_args):
    command = [sys.executable, str(core.RUNTIME / 'scripts/audit.py'), 'page-audit',
               '--url', url, '--out', str(output / 'page')]
    output.mkdir(parents=True, exist_ok=False)
    commands = (command + ['--level', 'AA', '--mode', 'machine', '--screenshots', 'initial', '--initial-only'],
                command + ['--resume', *profile_args])
    for index, args in enumerate(commands, 1):
        with (output / f'command-{index}.log').open('w') as stream:
            print(json.dumps(args, ensure_ascii=False), file=stream, flush=True)
            result = subprocess.run(args, stdout=stream, stderr=subprocess.STDOUT, check=False)
        if result.returncode:
            return False
    return True


def key_route(route, actions):
    return len(route) == len(actions) and all(step['type'] == 'key' and step['selector'] == target
                                              and step.get('key') in keys
                                              for step, (target, keys) in zip(route, actions))


def observed_transitions(root, graph, environment):
    for edge in graph['edges']:
        if edge['environment'] != environment or not edge['route']:
            continue
        directory = root / edge['evidence_dir']
        transition = core.load(directory / 'transition.json')
        waits = transition['settling']
        if (transition['route'] != edge['route'] or transition['error'] or transition['blocked_requests'] or transition['native_events'] or
                len(waits) != 1 + len(edge['route']) or any(wait['status'] != 'quiet' for wait in waits)):
            continue
        yield edge, directory, core.load(directory / 'state.json')


def grade(expected, observed):
    if {'failed', 'passed'} <= observed:
        return 'conflicting_verdict'
    if not observed or 'cant_tell' in observed:
        return 'no_verdict'
    actual = next(iter(observed))
    if expected == actual:
        return 'matched'
    return 'missed_problem' if expected == 'failed' else 'false_positive'


def visible(state, target):
    return any(item['selector'] == target for item in state['state'])


def score_image(captures, edges, output, row, results):
    visited_captures = set()
    for edge, directory, state in edges:
        if not visible(state, row['target']):
            continue
        results['reached'].append((directory / 'state.json').relative_to(output).as_posix())
        # The same rendered state can be reached via different input paths.
        path = captures.get(edge['fingerprint'])
        if path is None or path in visited_captures:
            continue
        visited_captures.add(path)
        raw = core.load(path)
        for category, outcome in RULE_GROUPS.items():
            for rule in raw[category]:
                if rule['id'] == 'image-alt' and any(node['target'] == [row['target']] for node in rule['nodes']):
                    results['verdicts'].append(dict(outcome=outcome, evidence=path.relative_to(output).as_posix()))


def score_dialog(edges, reports, root, output, row, results):
    action = DIALOG_ACTIONS[row['state']]
    closed = set()
    for edge, directory, state in edges:
        if visible(state, '#notice'):
            results['intermediate'] = 'dialog_opened'
        route = edge['route']
        if len(route) != 3 or visible(state, '#notice'):
            continue
        opener, close, followup = route
        if (opener['selector'] != row['target'] or close['selector'] != '#dismiss' or
                (close['type'], close.get('key')) != action or
                (followup['type'], followup.get('key')) != ('press', 'Tab')):
            continue
        closed.add(directory)
        results['reached'].append((directory / 'transition.json').relative_to(output).as_posix())

    for entry in reports:
        record = entry.get('dialog_focus', {})
        path = root / entry['evidence']
        if (path.parent in closed and entry['criterion'] == row['checkpoint'].rsplit('-', 1)[0] and
                entry['target'] == row['target'] and record.get('phase') == 'tab' and record.get('status') == 'closed'):
            results['verdicts'].append(dict(outcome=entry['outcome'], evidence=path.relative_to(output).as_posix()))


def score_page(result_root, location, group, expectations, *, completed):
    root = core.audit.run_layout.ledger(location / 'page')
    if not completed:
        return [dict(checkpoint=row['checkpoint'], state=row['state'], target=row['target'],
                     expected=row['expected'], status='collection_error')
                for row in expectations]
    graph = core.load(root / 'exploration.json')
    report = core.load(core.audit.run_layout.report_files(root, single=True).json)
    rows = []
    for environment in core.audit.run_meta(root)['config']['environments']:
        env = environment['id']
        transitions = list(observed_transitions(root, graph, env))
        captures = {node['fingerprint']: root / node['evidence_dir'] / 'axe.json'
                    for node in graph['nodes'] if node['environment'] == env}
        checks = [entry for entry in report['machine_checks'] if entry['environment'] == env]
        for row in expectations:
            result = dict(environment=env, checkpoint=row['checkpoint'], state=row['state'], target=row['target'],
                          expected=row['expected'], reached=[], verdicts=[])
            if group == 'image':
                score_image(captures, transitions, result_root, row, result)
            elif group == 'dialog':
                score_dialog(transitions, checks, root, result_root, row, result)
            else:
                actions = MENU_KEYS if group == 'menu' else COMBO_KEYS
                target = '#leaf' if group == 'menu' else '#options'
                for edge, directory, state in transitions:
                    if not visible(state, target):
                        continue
                    if key_route(edge['route'], actions):
                        result['reached'].append((directory / 'state.json').relative_to(result_root).as_posix())
                    else:
                        result['intermediate'] = 'visible_on_other_route'
            if result['reached']:
                result['status'] = grade(row['expected'], {item['outcome'] for item in result['verdicts']})
            else:
                result['status'] = 'route_not_observed'
            rows.append(result)
    return rows


def run(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    corpus = core.corpus()
    public = output / 'public'
    cases = [(suite['criterion'], case, CASES[suite['criterion']][case['id']])
             for suite in corpus['suites'] if suite['criterion'] in CASES
             for case in suite['cases'] if case['id'] in CASES[suite['criterion']]]
    if len(cases) != sum(map(len, CASES.values())) or any(len(case['pages']) != 1 for _, case, _ in cases):
        raise ValueError('URL単独測定の対象ページが変更された')
    for criterion in CASES:
        shutil.copytree(core.ROOT / 'benchmarks/cases' / criterion / 'public', public / criterion)
    http = runner.server(public)
    def inspect(criterion, case, group, profile):
        page, = case['pages']
        url = f'http://127.0.0.1:{http.server_port}/{criterion}/{page}'
        location = output / profile / criterion / case['id']
        completed = collect_page(url, location, PROFILES[profile])
        scored = score_page(output, location, group, case['expectations'], completed=completed)
        print(f'{profile} {criterion}/{page}: {"collected" if completed else "collection error"}', flush=True)
        return [dict(profile=profile, criterion=criterion, case=case['id'], page=page, group=group, **row)
                for row in scored]

    rows = []
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(inspect, criterion, case, group, profile)
                    for criterion, case, group in cases for profile in PROFILES]
            for job in jobs:
                rows.extend(job.result())
    finally:
        http.shutdown()
        http.server_close()
    summary = {profile: dict(Counter(row['status'] for row in rows if row['profile'] == profile)) for profile in PROFILES}
    core.save(output / 'result.json', dict(environment=runner.environment(), corpus_digest=corpus['digest'],
              implementation_digest=runner.implementation_digest(), profiles=PROFILES, summary=summary, rows=rows))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    summary = run(parser.parse_args().out)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    sys.exit(any('collection_error' in counts for counts in summary.values()))
