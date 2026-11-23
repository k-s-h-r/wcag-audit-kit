"""Score a planned 2.4.3 route from production dialog-focus evidence."""
import re

import dialog_focus
from keyboard_checks import matching_keydown


CHECKPOINT = '2.4.3-02'
SELECTOR = re.compile(r'#[a-zA-Z][\w-]*', re.ASCII)


def plans(criterion, checkpoints, states):
    result = {}
    for state in states:
        if 'dialog_focus' not in state:
            continue
        plan = state['dialog_focus']
        if (criterion != '2.4.3' or CHECKPOINT not in checkpoints or not isinstance(plan, dict)
                or set(plan) != {'opener', 'dialog', 'button', 'activation'}
                or not isinstance(state.get('id'), str)
                or state['id'] == 'initial' or not re.fullmatch(r'[a-z0-9-]+', state['id'])
                or plan['activation'] not in ('click', 'Enter', 'Space')):
            raise ValueError('ダイアログのフォーカス計測は2.4.3-02の操作後の状態に指定する')
        selectors = [plan[key] for key in ('opener', 'dialog', 'button')]
        if (not all(isinstance(selector, str) and SELECTOR.fullmatch(selector) for selector in selectors)
                or len(set(selectors)) != 3):
            raise ValueError('ダイアログの計測には開き元・ダイアログ・閉じるボタンの異なるIDを指定する')
        close = dict(type='click', selector=plan['button'])
        if plan['activation'] != 'click':
            close.update(type='key', key=plan['activation'])
        route = [dict(type='click', selector=plan['opener']), close,
                 dict(type='press', selector='body', key='Tab')]
        if any(existing_route == route for _, existing_route in result.values()):
            raise ValueError('ダイアログの計測経路が同じケース内に重複している')
        result[state['id']] = (plan, route)
    return result


def confirmed_inputs(inputs, record, route, url, document_start):
    events = inputs.get('events')
    if inputs.get('truncated') is not False or inputs.get('dropped') != 0 or not isinstance(events, list):
        return False
    indices = [record.get(key) for key in ('opener_event_index', 'close_event_index', 'tab_event_index')]
    if not all(type(index) is int and 1 <= index <= len(events) for index in indices):
        return False
    if not indices[0] < indices[1] < indices[2]:
        return False
    opening, closing, tab = (events[index - 1] for index in indices)
    selected = [opening, closing, tab]
    if not all(isinstance(event, dict) and event.get('url') == url and event.get('isTrusted') is True
               and event.get('is_main_frame') is True for event in selected):
        return False
    document = opening.get('documentId')
    if not isinstance(document, str) or not all(event.get('documentId') == document for event in selected):
        return False
    try:
        return (float(document.partition('-')[0]) == document_start
                and dialog_focus.activation_event(opening, route[0])
                and dialog_focus.activation_event(closing, route[1])
                and matching_keydown(tab, 'Tab'))
    except (KeyError, TypeError, ValueError):
        return False


def observed_row(record, transition, inputs, plan, route, url):
    settling = transition.get('settling')
    if (transition.get('route') != route or transition.get('dialog_focus') != 'tab'
            or transition.get('error') is not None or transition.get('blocked_requests') != []
            or transition.get('native_events') != [] or not isinstance(settling, list)
            or len(settling) != len(route) + 1
            or any(not isinstance(wait, dict) or wait.get('status') != 'quiet' for wait in settling)):
        return None
    if (record.get('phase') != 'tab' or record.get('status') != 'closed' or record.get('reason') != ''
            or record.get('close_action') != route[1] or record.get('opener') != plan['opener']):
        return None
    before, after, following = (record.get(key) for key in ('before_close', 'after_close', 'after_tab'))
    snapshots = [before, after, following]
    if not all(isinstance(snap, dict) and snap.get('url') == url and snap.get('supported') is True
               and isinstance(snap.get('focus'), str) and snap['focus']
               and type(snap.get('root_focus')) is bool for snap in snapshots):
        return None
    document_start = before.get('document_start')
    if (type(document_start) not in (int, float) or document_start <= 0
            or any(snap.get('document_start') != document_start for snap in snapshots)
            or before.get('modals') != [plan['dialog']] or after.get('modals') != [] or following.get('modals') != []
            or not confirmed_inputs(inputs, record, route, url, document_start)):
        return None
    restored = record.get('opener_restored')
    if (type(restored) is not bool or (restored and (after['focus'] != plan['opener'] or after['root_focus']))
            or record.get('tab_moved_focus') is not (after['focus'] != following['focus'])):
        return None
    if record.get('tab_moved_before_opener') is True and (restored or not after['root_focus'] or following['root_focus']):
        return None
    row = dialog_focus.report_row(record, transition.get('environment'), '', '', '')
    if following['root_focus']:
        row.update(outcome='cant_tell', observed=row['observed']+'次のTab後の要素を確認できない。')
    return row


def predictions(run, job, progress, frozen):
    from ..suite import core

    declared = plans(job['criterion'], job['checkpoints'], job.get('states', []))
    if not declared:
        return {}
    results = {}
    for page, url in job['urls'].items():
        try:
            attempt, receipt = core.completed_attempt(run, job, progress, page, frozen)
        except (TypeError, ValueError):
            continue
        if attempt is None:
            continue
        ledger = core.audit.run_layout.ledger(attempt)
        graph_path = ledger / 'exploration.json'
        graph = core.read_frozen(run, graph_path, frozen) or {}
        edges = graph.get('edges', [])
        if not isinstance(edges, list):
            continue
        for state, (plan, route) in declared.items():
            matches = [edge for edge in edges if isinstance(edge, dict)
                       and edge.get('route') == route and edge.get('dialog_focus') == 'tab']
            if len(matches) != 1:
                continue
            try:
                directory = core.local(ledger, matches[0]['evidence_dir'])
            except (KeyError, ValueError):
                continue
            if directory.parent != ledger / 'evidence':
                continue
            files = [directory/name for name in (dialog_focus.EVIDENCE_FILE, 'transition.json', 'input-events.json')]
            try:
                record, transition, inputs = [core.read_frozen(run, item, frozen) for item in files]
            except ValueError:
                continue
            environment = matches[0].get('environment')
            if (record is None or transition is None or inputs is None or not environment
                    or transition.get('environment') != environment):
                continue
            row = observed_row(record, transition, inputs, plan, route, url)
            if row is None:
                continue
            observation = dict(page=page, state=state, target=plan['opener'], checkpoint=CHECKPOINT,
                               outcome=row['outcome'], observed=row['observed'], method='program',
                               source='production dialog focus',
                               evidence=[p.relative_to(run).as_posix() for p in [receipt, graph_path, *files]])
            results[core.observation_key(observation)] = observation
    return results
