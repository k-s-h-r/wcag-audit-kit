"""Compare direct pointer and keyboard routes to a visible numeric HTML output."""
from collections import defaultdict
from pathlib import Path
import re


ACTIVATION_KEYS = {'Enter', 'Space'}
CHECKPOINT = 'キー操作後の機能の結果'


def activation(action):
    return action['type'] == 'click' or action['type'] == 'key' and action['key'] in ACTIVATION_KEYS


def numeric_output(data):
    if not data.get('operation_scope_supported'):
        return None
    outputs = [item for item in data['state'] if item['tag'] == 'output']
    if len(outputs) == 1 and re.fullmatch(r'-?[0-9]+', (outputs[0].get('value') or '').strip()):
        return outputs[0]
    return None


def matches_input(event, action, before):
    from keyboard_checks import matching_keydown

    if event.get('expectedTargetMatched') is not True:
        return False
    if action['type'] == 'key':
        return matching_keydown(event, action['key'])
    return (event['type'] == 'click' and event['isTrusted'] and event['is_main_frame']
            and event['pointerType'] == 'mouse' and event['button'] == 0
            and event.get('functionValueAtClick') == before['value'])


def finish(record, action, key_effect, observer, settling, interruption):
    first_event = record.pop('first_event')
    before, after = record.get('before'), record.get('after')
    index = key_effect.get('event_index') if action['type'] == 'key' else next((
        index for index in range(first_event, len(observer.events))
        if before and matches_input(observer.events[index], action, before)
    ), None)
    record['event_index'] = index
    record['activation_click'] = bool(action['type'] == 'key' and index is not None and any(
        event['type'] == 'click' and event['isTrusted'] and event['expectedTargetMatched'] is True
        for event in observer.events[index + 1:]
    ))
    record['confirmed'] = bool(
        not interruption and not observer.dropped and index is not None
        and all(wait['status'] == 'quiet' for wait in settling)
        and before and after and before['value'] == record['initial_value']
        and all(before[key] == after[key] for key in ('target', 'url'))
    )


def transition_path(edge):
    return (Path(edge['evidence_dir']) / 'transition.json').as_posix()


def comparable(pointer, keyboard):
    click = pointer['function_result']
    key = keyboard['function_result']
    return (key['confirmed'] and click['start'] == key['start']
            and click['before']['target'] == key['before']['target']
            and click['before']['value'] == key['before']['value'])


def verdict(pointer, keys, controls, states):
    control = pointer['route'][0]['selector']
    receipt = pointer['function_result']
    eligible = [
        edge for edge in keys if comparable(pointer, edge)
        and (target := edge['route'][0]['selector']) in controls
        and (target == control or controls[control]['label']
             and controls[control]['label'] == controls[target]['label'])
    ]
    before, after = receipt['before'], receipt['after']
    observed = f"クリックで {before['target']} が {before['value']} から {after['value']} に変わった。"
    for edge in eligible:
        action = edge['route'][0]
        value = edge['function_result']['after']['value']
        if value == after['value'] and (action['selector'] == control
                                        or pointer['fingerprint'] == edge['fingerprint']):
            return ('passed', observed + f" {action['selector']} で {action['key']} を押すと同じ値になった。",
                    [edge])
    own_keys = [edge for edge in eligible if edge['route'][0]['selector'] == control]
    unchanged = {edge['route'][0]['key'] for edge in own_keys
                 if edge['function_result']['after']['value'] == before['value']
                 and not edge['function_result']['activation_click']}
    button = controls[control]['tag'] == 'button' or controls[control]['role'] == 'button'
    custom_keys = any(edge['function_result'][phase]['custom_keys']
                      for edge in [pointer, *own_keys] for phase in ('before', 'after'))
    unchanged_controls = all(states.get((edge['environment'], edge['fingerprint'])) == {control}
                             for edge in [pointer, *own_keys])
    if button and len(controls) == 1 and unchanged == ACTIVATION_KEYS and not custom_keys and unchanged_controls:
        return 'failed', observed + f" EnterとSpaceでは {before['value']} のままだった。", own_keys
    return 'cant_tell', observed + ' キー操作で同じ結果を得られる経路は追加確認が必要。', own_keys


def report_rows(graph, scene, url):
    keys = defaultdict(list)
    clicks = []
    for index, edge in enumerate(graph.get('edges', []), 1):
        receipt = edge.get('function_result')
        if not receipt or not receipt['confirmed']:
            continue
        action = edge['route'][0]
        if action['type'] == 'key':
            keys[edge['environment']].append(edge)
        elif receipt['before']['value'] != receipt['after']['value']:
            clicks.append((index, edge))
    if not clicks:
        return
    initial = {node['environment']: {control['selector']: control for control in node['controls']}
               for node in graph['nodes'] if not node['route']}
    states = {(node['environment'], node['fingerprint']): {control['selector'] for control in node['controls']}
              for node in graph['nodes']}
    for index, edge in clicks:
        environment = edge['environment']
        target = edge['route'][0]['selector']
        controls = initial.get(environment, {})
        if target not in controls:
            continue
        outcome, observed, keyboard = verdict(edge, keys[environment], controls, states)
        before = edge['function_result']['before']
        yield dict(
            criterion='2.1.1', checkpoint=CHECKPOINT, expected='キー操作でクリックと同じ表示値に変えられる',
            outcome=outcome, environment=environment, capture=f'操作経路 {index}', state_label=scene(edge['route']),
            page_url=url, target=target, observed=observed, evidence=transition_path(edge), source='',
            proof=[transition_path(item) for item in keyboard],
            function_result={'output': before['target'], 'control_ancestors': before['control_ancestors'],
                             'keyboard_targets': [item['route'][0]['selector'] for item in keyboard]},
            note='初期表示から試した操作と、観測時間内の表示値の比較。ほかの機能や経路は追加確認する。',
        )
