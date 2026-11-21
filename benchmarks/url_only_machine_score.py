"""Match emitted verdicts to the frozen URL-only benchmark, without new browser actions."""
from collections import Counter, defaultdict

from benchmarks import core, url_only
import target_spacing


AXE_RULES = {
    '1.1.1-01': 'image-alt',
    '1.4.3-01': 'color-contrast',
    '1.4.6-01': 'color-contrast-enhanced',
    '2.4.2-01': 'document-title',
    '3.1.1-01': 'html-has-lang',
}
GROUPS = {**url_only.RULE_GROUPS, 'inapplicable': 'inapplicable'}
EXPECTED_ENVIRONMENTS = ('desktop', 'narrow')
ACTIVATION_KEYS = url_only.ACTIVATION_KEYS


def target_visible(state, target):
    return any(item['selector'] == target or (target == 'html' and item['tag'] == 'html')
               for item in state['state'])


def activated(route, selector):
    return any(action.get('selector') == selector
               and (action['type'] == 'click'
                    or (action['type'] == 'key' and action.get('key') in ACTIVATION_KEYS))
               for action in route)


def key_used(route, selector, keys):
    return any(action['type'] == 'key' and action.get('selector') == selector
               and action.get('key') in keys for action in route)


def reached_state(edge, state, row):
    """Require evidence of the state or route, independently of the expected verdict."""
    route = edge['route']
    target = row['target']
    name = row['state']
    if name == 'initial':
        return not route and target_visible(state, target)
    if name == 'after-load':
        return activated(route, '#load') and target_visible(state, target)
    if name == 'enabled':
        return activated(route, '#enable') and any(
            item['selector'] == target and item.get('disabled') is False for item in state['state'])
    if name == 'after-open':
        return activated(route, target) and target_visible(state, '#panel')
    if name == 'after-select':
        return activated(route, '#describe') and target_visible(state, target)
    if name == 'opened':
        return activated(route, '#open') and target_visible(state, target)
    if name == 'inner-dialog':
        return activated(route, '#inner-opener') and target_visible(state, target)
    if name == 'combo-open':
        return key_used(route, target, {'ArrowDown'}) and target_visible(state, '#options')
    if name in {'third-level', 'third-level-open', 'keyboard-route'}:
        if any(action['type'] not in {'key', 'press'} for action in route):
            return False
        if not all(key_used(route, selector, ACTIVATION_KEYS) for selector in ('#level1', '#level2')):
            return False
        if name == 'keyboard-route':
            return key_used(route, '#leaf', {'Enter'})
        return target_visible(state, target)
    if name == 'shadow-open':
        return key_used(route, target, ACTIVATION_KEYS)
    if name == 'second-tab':
        return key_used(route, '#tab-a', {'ArrowRight'}) and key_used(route, target, ACTIVATION_KEYS)
    if name == 'after-focus':
        return (all(action['type'] in {'key', 'press'} for action in route)
                and bool(route) and edge.get('focus_after') == target)
    # Media playback, timers, and focus inside a frame require their own evidence.
    return False


def matching_axe(row, checks, work, output, captures):
    rule_id = AXE_RULES[row['checkpoint']]
    for check in checks:
        if check['checkpoint'] != f'axe / {rule_id}':
            continue
        if check['outcome'] in {'failed', 'cant_tell'} and check['target'] != str([row['target']]):
            continue
        path = work / check['evidence']
        if path not in captures:
            continue
        for group, outcome in GROUPS.items():
            if outcome != check['outcome']:
                continue
            for rule in core.load(path).get(group, []):
                if rule['id'] == rule_id and any(
                        node['target'] == [row['target']] for node in rule['nodes']):
                    yield dict(outcome=outcome, evidence=path.relative_to(output).as_posix(),
                               report_check=check['checkpoint'], observed=check['observed'])


def matches_key_dispatch(edge, target):
    route = edge['route']
    return (len(route) == 1 and route[0]['type'] == 'key'
            and route[0]['selector'] == target and route[0].get('key') in ACTIVATION_KEYS)


def initial_transitions(work, edges):
    for edge in edges:
        if edge['route'] or edge.get('error'):
            continue
        directory = work / edge['evidence_dir']
        path = directory / 'state.json'
        if path.is_file() and (directory / 'axe.json').is_file():
            yield edge, directory, core.load(path)


def function_observation(path, allowed_paths, environment, probe, *, pointer):
    from keyboard_function import matches_input

    if path not in allowed_paths or not path.is_file():
        return None
    transition = core.load(path)
    route = transition['route']
    receipt = transition.get('function_result')
    if (len(route) != 1 or transition['environment'] != environment
            or not receipt or not receipt['confirmed']
            or receipt['before']['target'] != probe['result']['selector']):
        return None
    action = route[0]
    if pointer:
        if action['type'] != 'click' or action['selector'] not in probe['pointer']:
            return None
    elif action['type'] != 'key' or not any(action['selector'] == entry['selector']
                                           and action['key'] in entry['keys'] for entry in probe['keyboard']):
        return None
    log_path = path.with_name('input-events.json')
    if not log_path.is_file():
        return None
    log = core.load(log_path)
    index = receipt['event_index']
    if (log['truncated'] or type(index) is not int or not 0 <= index < len(log['events'])
            or not matches_input(log['events'][index], action, receipt['before'])):
        return None
    return action, receipt


def matching_function(row, checks, edges, work, output):
    from keyboard_function import CHECKPOINT

    probe = row.get('function_probe')
    if not probe or probe['target'] != row['target'] or probe['result']['kind'] != 'increase':
        return
    paths = {work / edge['evidence_dir'] / 'transition.json' for edge in edges}
    for check in checks:
        if check['checkpoint'] != CHECKPOINT:
            continue
        evidence = work / check['evidence']
        pointer = function_observation(evidence, paths, check['environment'], probe, pointer=True)
        if not pointer or pointer[0]['selector'] != check['target']:
            continue
        _, click = pointer
        start, end = (int(click[phase]['value']) for phase in ('before', 'after'))
        if end <= start:
            continue
        proof = [work / path for path in check.get('proof', [])]
        keys = [function_observation(path, paths, check['environment'], probe, pointer=False) for path in proof]
        if not all(keys) or any(receipt['start'] != click['start'] or int(receipt['before']['value']) != start
                                for _, receipt in keys):
            continue
        outcome = check['outcome']
        if outcome == 'passed' and not any(int(receipt['after']['value']) == end for _, receipt in keys):
            continue
        if outcome == 'failed' and {action['key'] for action, receipt in keys
                                    if int(receipt['after']['value']) == start} != ACTIVATION_KEYS:
            continue
        yield dict(outcome=outcome, evidence=evidence.relative_to(output).as_posix(),
                   proof=[path.relative_to(output).as_posix() for path in proof],
                   target=check['target'], report_check=check['checkpoint'], observed=check['observed'])


def matching_trap(row, checks, transitions, work, output):
    from dialog_focus import EVIDENCE_FILE
    from keyboard_checks import matching_keydown
    from keyboard_trap import CHECKPOINT, KEYS, left

    by_evidence = {str((directory / EVIDENCE_FILE).relative_to(work)): edge
                   for edge, directory, _ in transitions if edge.get('dialog_focus') == 'escape'}
    opened = [edge['route'] for edge, _, state in transitions if reached_state(edge, state, row)]
    last = {'type': 'press', 'selector': 'body', 'key': 'Escape'}
    for check in checks:
        edge = by_evidence.get(check['evidence'])
        if (check['checkpoint'] != CHECKPOINT or check['target'] != row['target'] or not edge
                or edge['route'][-1] != last or edge['route'][:-1] not in opened):
            continue
        path = work / check['evidence']
        log_path = path.with_name('input-events.json')
        if not path.is_file() or not log_path.is_file():
            continue
        receipt = core.load(path).get('keyboard_trap')
        if not receipt or receipt['target'] != row['target'] or receipt['outcome'] != check['outcome']:
            continue
        before = receipt['before']
        log = core.load(log_path)
        opener = next((action for action in edge['route'][:-1]
                       if action['type'] == 'key' and action['selector'] == receipt['opener']
                       and action.get('key') in ACTIVATION_KEYS), None)
        if not opener or any(action['type'] not in {'key', 'press'} for action in edge['route']):
            continue
        keys = [('Escape', receipt['escape_event_index']),
                *((step['key'], step['event_index']) for step in receipt['steps'])]
        keys.insert(0, (opener['key'], receipt['opener_event_index']))
        indices = [index for _, index in keys]
        if (log['truncated'] or any(type(index) is not int or not 0 <= index < len(log['events']) for index in indices)
                or indices != sorted(set(indices)) or not before['within'] or before['modals'] != [row['target']]
                or any(step['settling']['status'] != 'quiet' for step in receipt['steps'])):
            continue
        events = [log['events'][index] for index in indices]
        if any(not event.get('expectedTargetMatched') or not matching_keydown(event, key)
               or event['url'] != before['url'] or event['documentId'] != events[0]['documentId']
               for (key, _), event in zip(keys, events)):
            continue
        outcome = receipt['outcome']
        if outcome == 'passed':
            after = receipt['steps'][-1]['after'] if receipt['steps'] else receipt['after_escape']
            if not left(before, after):
                continue
        elif outcome == 'failed':
            pointer = receipt.get('pointer', {})
            index = pointer.get('event_index')
            compared = [receipt['after_escape'], *(step['after'] for step in receipt['steps'])]
            if (tuple(key for key, _ in keys[1:]) != ('Escape', *KEYS) or type(index) is not int
                    or not receipt.get('escape_retained') or not all(step.get('retained') for step in receipt['steps'])
                    or any(not state['simple'] or state['modals'] != before['modals']
                           or state['focus'] != before['focus'] for state in compared)
                    or receipt.get('before_pointer') != compared[-1] or not compared[-1]['blank']
                    or pointer['settling']['status'] != 'quiet'
                    or not indices[-1] < index < len(log['events']) or not left(before, pointer['after'])):
                continue
            event = log['events'][index]
            if (not event.get('expectedTargetMatched') or not event['isTrusted'] or not event['is_main_frame']
                    or event['type'] != 'click' or event['pointerType'] != 'mouse'
                    or event['documentId'] != events[0]['documentId']):
                continue
        else:
            continue
        yield dict(outcome=outcome, evidence=path.relative_to(output).as_posix(),
                   proof=[log_path.relative_to(output).as_posix()], target=check['target'],
                   report_check=check['checkpoint'], observed=check['observed'])


def matching_target_spacing(row, checks, transitions, work, output, graph):
    proof = {item['path']: item['sha256'] for item in graph.get('proof', [])}
    for edge, directory, state in transitions:
        if edge['route'] or not target_visible(state, row['target']):
            continue
        paths = [directory / name for name in (target_spacing.EVIDENCE_FILE, 'state.json', 'transition.json')]
        if any(not path.is_file() or proof.get(path.relative_to(work).as_posix()) != core.file_hash(path)
               for path in paths):
            continue
        evidence, state_file, transition_file = paths
        transition = core.load(transition_file)
        if (transition['route'] != edge['route'] or transition['environment'] != edge['environment']
                or transition['error'] or transition['blocked_requests'] or transition['native_events']
                or len(transition['settling']) != 1 or transition['settling'][0]['status'] != 'quiet'):
            continue
        nodes = [node for node in graph['nodes'] if not node['route'] and node['environment'] == edge['environment']
                 and node['evidence_dir'] == edge['evidence_dir']]
        if len(nodes) != 1:
            continue
        capture = dict(key=nodes[0]['capture'], environment=edge['environment'], url=state['url'], final_url=state['url'])
        verified = target_spacing.report_rows(core.load(evidence), state, capture,
                                              evidence.relative_to(work).as_posix(), state_file.relative_to(work).as_posix())
        for check in verified:
            if check['target'] == row['target'] and check in checks:
                yield dict(outcome=check['outcome'], evidence=evidence.relative_to(output).as_posix(),
                           proof=[path.relative_to(output).as_posix() for path in (state_file, transition_file)],
                           report_check=check['checkpoint'], target=check['target'], observed=check['observed'])


def score_environment(row, checks, edges, transitions, work, output, graph=None):
    reached = [
        (directory / 'state.json').relative_to(output).as_posix()
        for edge, directory, state in transitions if reached_state(edge, state, row)
    ]
    verdicts = []
    point = row['checkpoint']
    key_evidence = {edge['evidence_dir'] + '/transition.json' for edge in edges
                    if matches_key_dispatch(edge, row['target'])}
    key_results = [
        dict(outcome=check['outcome'], evidence=(work / check['evidence']).relative_to(output).as_posix(),
             report_check=check['checkpoint'], observed=check['observed'])
        for check in checks if check['checkpoint'].startswith('実入力 / ')
        and check['target'] == row['target'] and check['evidence'] in key_evidence
    ] if row['criterion'] == '2.1.1' else []
    if point in AXE_RULES:
        captures = {
            work / edge['evidence_dir'] / 'axe.json'
            for edge, _, state in transitions if reached_state(edge, state, row)
        }
        verdicts.extend(matching_axe(row, checks, work, output, captures))
    elif point == '2.1.1-01':
        verdicts.extend(key_results)
    elif point == '2.1.1-02' and row['state'] == 'initial' and reached:
        verdicts.extend(matching_function(row, checks, edges, work, output))
    elif point == '2.1.2-02' and reached:
        verdicts.extend(matching_trap(row, checks, transitions, work, output))
    elif point == '2.5.8-02' and row['state'] == 'initial' and reached and graph:
        verdicts.extend(matching_target_spacing(row, checks, transitions, work, output, graph))
    elif row['state'] in url_only.DIALOG_ACTIONS:
        result = dict(reached=[], verdicts=[])
        url_only.score_dialog(transitions, checks, work, output, row, result)
        reached.extend(result['reached'])
        verdicts.extend({**check, 'report_check': 'ダイアログを閉じた後のフォーカス'}
                        for check in result['verdicts'])
    return dict(reached=sorted(set(reached)), key_dispatch=key_results, verdicts=verdicts)


def environment_outcome(verdicts):
    definite = {item['outcome'] for item in verdicts} - {'cant_tell'}
    return next(iter(definite)) if len(definite) == 1 else None


def classify(expected, environments, completed):
    if not completed:
        return 'collection_error'
    outcomes = [environment_outcome(env['verdicts']) for env in environments.values()]
    if 'failed' in outcomes:
        return 'detected' if expected == 'failed' else 'false_positive'
    if outcomes and all(outcome in {'passed', 'inapplicable'} for outcome in outcomes):
        if expected == 'failed':
            return 'wrong_pass'
        return 'matched' if set(outcomes) == {expected} else 'wrong_control_outcome'
    if any(env['reached'] or env['verdicts'] for env in environments.values()):
        return 'observed_no_verdict'
    return 'state_or_route_unobserved'


def score_page(output, page):
    location = output / 'pages' / page['id']
    receipt = location / 'collection.json'
    report_path = location / 'page/data/report.json'
    work = core.audit.run_layout.ledger(location / 'page')
    graph_path = work / 'exploration.json'
    completed = (receipt.is_file() and core.load(receipt)['phases'] == {'initial': 0, 'explore': 0}
                 and report_path.is_file() and graph_path.is_file())
    collection = dict(page_id=page['id'], completed=completed,
                      collection=core.load(receipt) if receipt.is_file() else None)
    findings = []
    edges_by_env = defaultdict(list)
    transitions_by_env = {}
    checks_by_env = defaultdict(list)
    graph = None
    if completed:
        report = core.load(report_path)
        graph = core.load(graph_path)
        collection.update(
            report=report_path.relative_to(output).as_posix(),
            report_sha256=core.file_hash(report_path),
            exploration=graph_path.relative_to(output).as_posix(),
            limits=graph['limits'], steps=graph['steps'],
            omitted_candidates=graph['omitted_candidates'], queued=len(graph['queue']),
        )
        for edge in graph['edges']:
            edges_by_env[edge['environment']].append(edge)
        for env in EXPECTED_ENVIRONMENTS:
            transitions_by_env[env] = [
                *initial_transitions(work, edges_by_env[env]),
                *url_only.observed_transitions(work, graph, env),
            ]
        for check in report['machine_checks']:
            checks_by_env[check['environment']].append(check)
            if check['outcome'] == 'failed':
                findings.append(dict(
                    environment=check['environment'], criterion=check['criterion'],
                    checkpoint=check['checkpoint'], target=check['target'], state=check['state_label'],
                    evidence=(work / check['evidence']).relative_to(output).as_posix(),
                    observed=check['observed'],
                ))
    rows = []
    matched_findings = set()
    for row in page['rows']:
        environments = {
            env: score_environment(row, checks_by_env[env], edges_by_env[env],
                                   transitions_by_env.get(env, []), work, output, graph)
            for env in EXPECTED_ENVIRONMENTS
        }
        for env, observations in environments.items():
            for check in observations['verdicts']:
                if check['outcome'] == 'failed':
                    target = (str([row['target']]) if check['report_check'].startswith('axe / ')
                              else check.get('target', row['target']))
                    matched_findings.add((env, row['criterion'], check['report_check'],
                                          target, check['evidence']))
        rows.append(dict(
            page_id=page['id'], criterion=row['criterion'], case=row['case'], page=row['page'],
            state=row['state'], target=row['target'], checkpoint=row['checkpoint'], expected=row['expected'],
            status=classify(row['expected'], environments, completed), environments=environments,
        ))
    keys = ('environment', 'criterion', 'checkpoint', 'target', 'evidence')
    extra = [dict(page_id=page['id'], **finding) for finding in findings
             if tuple(finding[key] for key in keys) not in matched_findings]
    return rows, extra, collection


def score(output):
    inventory = core.load(output / 'inventory.json')
    rows, extra, receipts = [], [], []
    for page in inventory['pages']:
        page_rows, page_extra, collection = score_page(output, page)
        rows.extend(page_rows)
        extra.extend(page_extra)
        receipts.append(collection)
    totals = Counter(row['expected'] for row in rows)
    if dict(totals) != inventory['totals']:
        raise ValueError('採点行が事前に固定した分母と一致しない')
    problems = Counter(row['status'] for row in rows if row['expected'] == 'failed')
    controls = Counter(row['status'] for row in rows if row['expected'] != 'failed')
    return dict(
        commit=inventory['commit'], corpus_digest=inventory['corpus_digest'],
        environment=inventory['environment'], initial_args=inventory['initial_args'],
        explore_args=inventory['explore_args'], workers=inventory['workers'],
        pages=len(receipts), completed_pages=sum(receipt['completed'] for receipt in receipts),
        totals=dict(totals), problems=dict(problems), controls=dict(controls),
        unmatched_findings=extra, receipts=receipts, rows=rows,
    )
