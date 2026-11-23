"""Measure bounded keyboard exits and focus transitions in real fixture pages."""
from __future__ import annotations

import re

CHECKPOINTS = {'2.1.2': '2.1.2-02', '2.4.3': '2.4.3-02'}
KEYS = ('Tab', 'Shift+Tab', 'Enter', 'Space', 'Escape', 'ArrowDown')
ACTIVATIONS = ('Escape', 'Enter', 'Space')
LIMIT = 8
ID = re.compile(r'#[A-Za-z][A-Za-z0-9_-]*')
INPUT_BINDING = '__wcagBenchmarkFocusInput'
INPUT_SCRIPT = """() => {
    if (window.__wcagBenchmarkFocusListener) return;
    window.__wcagBenchmarkFocusListener = true;
    for (const type of ['keydown', 'click']) window.addEventListener(type, event => {
        const path = event.composedPath().filter(element => element instanceof Element);
        window.__wcagBenchmarkFocusInput({
            type, key: event.key === ' ' ? 'Space' : event.key,
            shift: event.shiftKey, ctrl: event.ctrlKey, alt: event.altKey, meta: event.metaKey,
            trusted: event.isTrusted, time: performance.timeOrigin, url: location.href,
            frame: window.frameElement?.id ?? null,
            ids: path.map(element => element.id).filter(Boolean).slice(0, 32)
        }).catch(() => {});
    }, {capture: true});
}"""
SNAPSHOT = """({region, member, outer, watch}) => {
    const visible = element => Boolean(element?.checkVisibility({
        opacityProperty: true, visibilityProperty: true
    }) && element.getClientRects().length);
    const named = root => root.id && root.ownerDocument.querySelectorAll('#' + CSS.escape(root.id)).length === 1
        ? '#' + root.id : root.localName + ':' + [...root.ownerDocument.querySelectorAll(root.localName)].indexOf(root);
    const find = id => {
        if (!id) return null;
        const nodes = document.querySelectorAll(id);
        return nodes.length === 1 ? nodes[0] : null;
    };
    const scope = find(region), additional = find(member);
    const inScope = scope?.contains(document.activeElement) || additional?.contains(document.activeElement);
    const outerElement = find(outer);
    let element = document.activeElement, leaf = element, frame = null;
    if (element?.localName === 'iframe') {
        frame = named(element);
        leaf = element.contentDocument?.activeElement;
    }
    const meaningful = leaf && !['body', 'html'].includes(leaf.localName);
    return {
        page: location.href, document: performance.timeOrigin,
        focus_document: leaf?.ownerDocument.defaultView.performance.timeOrigin ?? null,
        focus_url: leaf?.ownerDocument.URL ?? null,
        focus: meaningful ? (frame ? frame + ' > ' : '') + named(leaf) : '',
        region_visible: visible(scope), within: Boolean(inScope),
        outer_visible: visible(outerElement), outer_within: Boolean(outerElement?.contains(element)),
        watched: Object.fromEntries((watch || []).map(selector => {
            const node = find(selector);
            return [selector, node ? {visible: visible(node), expanded: node.getAttribute('aria-expanded')} : null];
        }))
    };
}"""


def selector(value):
    return isinstance(value, str) and ID.fullmatch(value) is not None


def click_spec(action):
    return (isinstance(action, dict) and set(action) in ({'click'}, {'click', 'frame'})
            and all(selector(value) for value in action.values()))


def validate_plan(criterion, plan):
    common = {'kind', 'target', 'region', 'setup'}
    kinds = {'trap'} if criterion == '2.1.2' else {'menu-order', 'dialog-order'} if criterion == '2.4.3' else set()
    if not isinstance(plan, dict) or not isinstance(plan.get('kind'), str) or plan['kind'] not in kinds:
        raise ValueError('キーボードの採点手順の種類が不正')
    trap = plan['kind'] == 'trap'
    mandatory = common | ({'pointer_exit'} if trap else {'outer', 'opener'})
    optional = {'member', 'watch'} if trap else {'outer_opener'} if plan['kind'] == 'dialog-order' else {'watch'}
    if not mandatory <= plan.keys() or set(plan) - mandatory - optional:
        raise ValueError('キーボードの採点手順の項目が不正')
    if not all(selector(plan[key]) for key in plan.keys() - {'kind', 'setup', 'pointer_exit', 'watch'}):
        raise ValueError('検証用の対象にはIDセレクターが必要')
    if 'watch' in plan:
        watch = plan['watch']
        if (not isinstance(watch, list) or not 1 <= len(watch) <= 8
                or not all(selector(target) for target in watch) or len(set(watch)) != len(watch)):
            raise ValueError('各手順で記録する対象には異なるIDを指定する')
    setup = plan['setup']
    if not isinstance(setup, list) or not 1 <= len(setup) <= 8:
        raise ValueError('検証状態に到達する操作が必要')
    if any(not (action in KEYS if isinstance(action, str) else click_spec(action)) for action in setup):
        raise ValueError('状態に到達する操作が不正')
    if trap and not click_spec(plan['pointer_exit']):
        raise ValueError('ポインターによる閉じる操作の対象が必要')
    if not trap and plan['kind']=='menu-order' and setup[-1] not in ('Enter', 'Space'):
        raise ValueError('メニューの最後の展開操作には実キーを使う')
    if not trap and plan['kind']=='dialog-order' and 'outer_opener' not in plan:
        raise ValueError('外側のダイアログの起点が必要')


async def observe_inputs(page):
    events = []

    def record(source, event):
        if len(events) < 1000 and isinstance(event, dict):
            events.append(event)

    await page.expose_binding(INPUT_BINDING, record)
    await page.add_init_script(f'({INPUT_SCRIPT})()')
    await page.evaluate(INPUT_SCRIPT)
    return events


async def snapshot(page, plan):
    return await page.evaluate(SNAPSHOT, {key: plan.get(key) for key in ('region', 'member', 'outer', 'watch')})


async def perform(page, plan, action, inputs):
    before = await snapshot(page, plan)
    start = len(inputs)
    if isinstance(action, str):
        await page.keyboard.press(action)
    else:
        context = page.frame_locator(action['frame']) if 'frame' in action else page
        await context.locator(action['click']).click(timeout=1500)
    # Allow focus/visibility and iframe message handlers to settle before sampling.
    await page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
    after = await snapshot(page, plan)
    observed = [event for event in inputs[start:] if matching_input(action, before, event)]
    return {'action': action, 'before': before, 'after': after, 'input': observed[0] if observed else None}


def matching_input(action, before, item):
    if not isinstance(item, dict) or item.get('trusted') is not True:
        return False
    if isinstance(action, str):
        key = 'Tab' if action == 'Shift+Tab' else action
        return (item.get('type') == 'keydown' and item.get('key') == key
                and item.get('shift') is (action == 'Shift+Tab')
                and all(item.get(modifier) is False for modifier in ('alt', 'ctrl', 'meta'))
                and item.get('url') == before['focus_url'] and item.get('time') == before['focus_document'])
    same_target_document = (item.get('frame') == action['frame'][1:] if 'frame' in action
                            else item.get('frame') is None and item.get('time') == before['document']
                            and item.get('url') == before['page'])
    return (item.get('type') == 'click' and same_target_document and isinstance(item.get('ids'), list)
            and action['click'][1:] in item['ids'])


def inside(state):
    return state['region_visible'] and state['within'] and bool(state['focus'])


def exit_observed(state):
    return bool(state['focus'] and (not state['region_visible'] or not state['within']))


async def capture(criterion, page, plan):
    validate_plan(criterion, plan)
    inputs = await observe_inputs(page)
    start_url = page.url
    routes = []

    async def replay(kind):
        if routes:
            await page.goto(start_url, wait_until='domcontentloaded')
        inputs.clear()
        setup = [await perform(page, plan, action, inputs) for action in plan['setup']]
        route = {'kind': kind, 'setup': setup, 'steps': []}
        routes.append(route)
        return route

    async def step(route, action):
        entry = await perform(page, plan, action, inputs)
        route['steps'].append(entry)
        return entry['after']

    if plan['kind'] != 'trap':
        route = await replay('order')
        sequence = ('Tab', 'Escape') if plan['kind'] == 'menu-order' else ('Escape', 'Escape')
        for key in sequence:
            await step(route, key)
        return {'routes': routes}

    route = await replay('escape')
    if not inside(route['setup'][-1]['after']):
        return {'routes': routes}
    last = await step(route, 'Escape')
    if exit_observed(last):
        return {'routes': routes}

    # Find the reachable keyboard positions in both traversal directions.
    reached = {}
    for kind, key in (('forward', 'Tab'), ('backward', 'Shift+Tab')):
        route = await replay(kind)
        initial = route['setup'][-1]['after']
        positions = {initial['focus']}
        for index in range(LIMIT):
            last = await step(route, key)
            if exit_observed(last):
                return {'routes': routes}
            if last['focus'] in positions or not inside(last):
                break
            positions.add(last['focus'])
            reached.setdefault(last['focus'], [key] * (index + 1))

    # Try the standard dismissal and activation keys on each observed focus.
    # The very first Escape was already observed on its own route.
    for prefix in [[], *reached.values()]:
        for key in ACTIVATIONS:
            if not prefix and key == 'Escape':
                continue
            route = await replay('activation')
            for action in [*prefix, key]:
                last = await step(route, action)
                if exit_observed(last):
                    return {'routes': routes}
    route = await replay('pointer')
    await step(route, plan['pointer_exit'])
    return {'routes': routes}


def trusted_route(route, plan):
    if not isinstance(route, dict) or not isinstance(route.get('setup'), list) or not isinstance(route.get('steps'), list):
        return False
    try:
        setup, steps = route['setup'], route['steps']
        if [entry['action'] for entry in setup] != plan['setup'] or not steps:
            return False
        # A transition to another document is a separate observation; the fixture
        # observation here covers in-page dismissal and focus only.
        start = setup[0]['before']
        entries = [*setup, *steps]
        if any(previous['after'] != current['before'] for previous, current in zip(entries, entries[1:])):
            return False
        return all(matching_input(entry['action'], entry['before'], entry['input'])
                   and all(entry[phase]['document'] == start['document'] and entry[phase]['page'] == start['page']
                           and all(type(entry[phase][key]) is bool
                                   for key in ('region_visible', 'within', 'outer_visible', 'outer_within'))
                           and isinstance(entry[phase]['focus'], str)
                           for phase in ('before', 'after'))
                   for entry in entries)
    except (KeyError, TypeError, AttributeError):
        return False


def actions(route):
    return [entry['action'] for entry in route['steps']]


def focus_paths(route):
    return ' → '.join([route['setup'][-1]['after']['focus'],
                       *(entry['after']['focus'] or '文書' for entry in route['steps'])])


def walk_cycle(route, key):
    if not route['steps'] or any(action != key for action in actions(route)):
        return set()
    states = [route['setup'][-1]['after'], *(entry['after'] for entry in route['steps'])]
    if all(inside(state) for state in states) and states[-1]['focus'] in {state['focus'] for state in states[:-1]}:
        return {state['focus'] for state in states}
    return set()


def trap_result(plan, routes):
    # Distinguish scope exit through keyboard from closing through pointer.
    for route in routes:
        steps = route['steps']
        if (route.get('kind') in {'escape', 'forward', 'backward', 'activation'}
                and inside(route['setup'][-1]['after'])
                and all(isinstance(action, str) and action in KEYS for action in actions(route))
                and exit_observed(steps[-1]['after'])):
            return 'passed', f'実際のキー操作（{"、".join(actions(route))}）で領域から離脱した。フォーカス {focus_paths(route)}。'

    by_kind = {route['kind']: route for route in routes if route.get('kind') in {'forward', 'backward', 'pointer'}}
    if set(by_kind) != {'forward', 'backward', 'pointer'}:
        return 'cant_tell', '両方向のキー移動と対照となるポインター操作の証拠がそろっていない。'
    forward, backward, pointer = (by_kind[key] for key in ('forward', 'backward', 'pointer'))
    forward_members = walk_cycle(forward, 'Tab')
    backward_members = walk_cycle(backward, 'Shift+Tab')
    if not (forward_members and backward_members and inside(pointer['setup'][-1]['after'])
            and actions(pointer) == [plan['pointer_exit']] and exit_observed(pointer['steps'][-1]['after'])):
        return 'cant_tell', '両方向での循環とポインターでの離脱を同じ領域で確認できない。'
    observed_activations = {
        (route['steps'][-1]['before']['focus'], route['steps'][-1]['action'])
        for route in routes if route.get('kind') in {'escape', 'activation'}
        and inside(route['setup'][-1]['after'])
        and isinstance(route['steps'][-1]['action'], str)
        and all(inside(entry['before']) and inside(entry['after']) for entry in route['steps'])
    }
    if any((member, key) not in observed_activations for member in forward_members | backward_members for key in ACTIVATIONS):
        return 'cant_tell', 'すべての到達位置でEsc・Enter・Spaceの離脱を試した記録がない。'
    return 'failed', (f'TabとShift+Tabで領域内を循環し、各到達位置でEsc・Enter・Spaceでも離脱できず、'
                      f'指定のポインター操作では離脱した。Tab {focus_paths(forward)}。Shift+Tab {focus_paths(backward)}。')


def order_result(plan, routes):
    if len(routes) != 1 or routes[0].get('kind') != 'order':
        return 'cant_tell', '指定した展開とフォーカス移動の証拠がない。'
    route = routes[0]
    opened = route['setup'][-1]
    initial = opened['after']
    if opened['before']['region_visible'] or not initial['region_visible'] or not initial['outer_visible']:
        return 'cant_tell', '対象を展開したことと外側の領域を確認できない。'
    if plan['kind'] == 'menu-order':
        if actions(route) != ['Tab', 'Escape'] or opened['before']['focus'] != plan['opener']:
            return 'cant_tell', '開くボタンからのキー入力と次のTabを確認できない。'
        entered, dismissed = (entry['after'] for entry in route['steps'])
        for state in (initial, entered):
            if state['region_visible'] and state['outer_visible'] and state['focus'] and not state['outer_within']:
                return 'failed', f'階層を展開した状態でフォーカスがメニューの外の {state["focus"]} へ移った。'
        if (initial['focus'] == plan['opener'] and inside(entered)
                and not dismissed['region_visible'] and dismissed['focus'] == plan['opener']):
            return 'passed', f'開く操作の後、次のTabで階層内の {entered["focus"]} へ入り、Escで {dismissed["focus"]} へ戻った。'
    elif actions(route) == ['Escape', 'Escape'] and inside(initial):
        inner, outer = (entry['after'] for entry in route['steps'])
        if not inner['region_visible'] and inner['outer_visible'] and inner['focus'] and not inner['outer_within']:
            return 'failed', f'内側を閉じると、開いている外側のダイアログを飛び越え、{inner["focus"]} に移った。'
        if (not inner['region_visible'] and inner['outer_visible'] and inner['focus'] == plan['opener']
                and not outer['outer_visible'] and outer['focus'] == plan['outer_opener']):
            return 'passed', f'内側を閉じて {inner["focus"]} へ、外側を閉じて {outer["focus"]} へ順に戻った。'
    return 'cant_tell', f'観察した経路で期待する移動を確定できない。フォーカス {focus_paths(route)}。'


def evaluate(criterion, plan, evidence):
    validate_plan(criterion, plan)
    routes = evidence.get('routes') if isinstance(evidence, dict) else None
    trusted = [route for route in routes if trusted_route(route, plan)] if isinstance(routes, list) else []
    method = trap_result if plan['kind'] == 'trap' else order_result
    outcome, explanation = method(plan, trusted)
    return [{'target': plan['target'], 'checkpoint': CHECKPOINTS[criterion],
             'outcome': outcome, 'observed': explanation}]
