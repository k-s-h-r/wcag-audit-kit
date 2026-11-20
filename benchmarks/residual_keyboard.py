"""Compare real keyboard and pointer routes for a declared 2.1.1 function."""

import asyncio
from itertools import product
import math
import re
from urllib.parse import urljoin
from uuid import uuid4


POINT = '2.1.1-02'
KEYS = {'Enter', 'Space', 'ArrowRight', 'ArrowLeft'}
SELECTOR = re.compile(r'#[A-Za-z][A-Za-z0-9_-]*')
LOCAL_PAGE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]*\.html(?:#[A-Za-z0-9_-]+)?')
TAB_LIMIT = 16
MAX_TRIALS = 8
FOCUSED = """element => {
    let active = element.ownerDocument.activeElement;
    while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
    return active === element;
}"""
WATCH = """(element, {binding, token, kind, key}) => {
    element.ownerDocument.addEventListener(kind, event => {
        if (!event.isTrusted || (key !== null && event.key !== key)) return;
        window[binding]({
            token, type: event.type, key: event.key ?? null, trusted: event.isTrusted,
            target_match: event.composedPath().includes(element)
        }).catch(() => {});
    }, {capture: true, once: true});
}"""


def _selector(value):
    return isinstance(value, str) and SELECTOR.fullmatch(value) is not None


def _keyboard_routes(plan):
    options = [
        [dict(selector=step['selector'], key=key, reach=step['reach']) for key in step['keys']]
        for step in plan['keyboard']
    ]
    return [list(route) for route in product(*options)]


def validate_plan(criterion, plan):
    if (criterion != '2.1.1' or not isinstance(plan, dict)
            or set(plan) != {'target', 'keyboard', 'pointer', 'result'}
            or not _selector(plan['target'])):
        raise ValueError('2.1.1の機能確認には対象、キーボード経路、ポインター経路、観測条件が必要')
    keyboard, pointer = plan['keyboard'], plan['pointer']
    if (not isinstance(keyboard, list) or not 1 <= len(keyboard) <= 4
            or not isinstance(pointer, list) or not 1 <= len(pointer) <= 4
            or not all(_selector(target) for target in pointer)):
        raise ValueError('操作経路に1〜4個の操作を指定する')
    for step in keyboard:
        if (not isinstance(step, dict) or set(step) != {'selector', 'keys', 'reach'}
                or not _selector(step['selector']) or step['reach'] not in ('tab', 'current')
                or not isinstance(step['keys'], list) or not 1 <= len(step['keys']) <= 2
                or not all(isinstance(key, str) and key in KEYS for key in step['keys'])
                or len(set(step['keys'])) != len(step['keys'])):
            raise ValueError('キーボード操作には要素のID、実キー、到達方法を指定する')
    if math.prod(len(step['keys']) for step in keyboard) > MAX_TRIALS:
        raise ValueError('キーボード経路の組み合わせは8件以内')
    result = plan['result']
    if not isinstance(result, dict):
        raise ValueError('機能の観測条件を指定する')
    kind = result.get('kind')
    if kind == 'increase' and set(result) == {'kind', 'selector'} and _selector(result['selector']):
        return
    if (kind == 'reveal' and set(result) == {'kind', 'selector', 'control', 'attribute'}
            and _selector(result['selector']) and _selector(result['control'])
            and result['attribute'] in ('aria-expanded', 'aria-selected')):
        return
    if (kind == 'navigate' and set(result) == {'kind', 'resource', 'heading'}
            and isinstance(result['resource'], str) and LOCAL_PAGE.fullmatch(result['resource'])
            and isinstance(result['heading'], str) and 0 < len(result['heading']) <= 100):
        return
    raise ValueError('観測条件に数量の増加、表示の切替、同じ基準内の移動を指定する')


async def _snapshot(page, spec):
    kind = spec['kind']
    if kind == 'navigate':
        headings = await page.get_by_role('heading', level=1).all_text_contents()
        return {'url': page.url, 'headings': [heading.strip() for heading in headings]}
    target = page.locator(spec['selector'])
    if await target.count() != 1:
        return None
    if kind == 'increase':
        value = (await target.inner_text(timeout=1000)).strip()
        try:
            number = float(value)
        except ValueError:
            return None
        return {'url': page.url, 'number': number} if math.isfinite(number) else None
    control = page.locator(spec['control'])
    if await control.count() != 1:
        return None
    return {'url': page.url, 'visible': await target.is_visible(),
            'state': await control.get_attribute(spec['attribute'], timeout=1000)}


async def _perform(page, action, binding, inputs, initial_url):
    target = page.locator(action['selector'])
    if page.url != initial_url or await target.count() != 1:
        return {'status': 'unconfirmed'}
    key = action.get('key')
    traversed = 0
    if key is not None:
        focused = await target.evaluate(FOCUSED, timeout=1000)
        if action['reach'] == 'tab':
            while not focused and traversed < TAB_LIMIT:
                await page.keyboard.press('Tab')
                traversed += 1
                if page.url != initial_url or await target.count() != 1:
                    return {'status': 'unconfirmed', 'tabs': traversed}
                focused = await target.evaluate(FOCUSED, timeout=1000)
        if not focused:
            return {'status': 'unreached', 'tabs': traversed}
    token = uuid4().hex
    await target.evaluate(WATCH, {'binding': binding, 'token': token,
                                 'kind': 'click' if key is None else 'keydown',
                                 'key': ' ' if key == 'Space' else key}, timeout=1000)
    if key is None:
        await target.click(timeout=1500)
    else:
        await page.keyboard.press(key)
    for _ in range(10):
        if token in inputs:
            break
        await asyncio.sleep(.02)
    event = inputs.pop(token, None)
    if event is None or event['trusted'] is not True or event['target_match'] is not True:
        return {'status': 'unconfirmed', 'tabs': traversed, 'event': event}
    return {'status': 'delivered', 'tabs': traversed, 'event': event}


async def _trial(page, initial_url, actions, spec, binding, inputs):
    from playwright.async_api import Error, TimeoutError

    proof = {'actions': actions, 'steps': [], 'before': None, 'after': None}
    try:
        await page.goto(initial_url, wait_until='domcontentloaded', timeout=3000)
        if page.url != initial_url:
            return proof
        proof['before'] = await _snapshot(page, spec)
        for action in actions:
            step = await _perform(page, action, binding, inputs, initial_url)
            proof['steps'].append(step)
            if step['status'] != 'delivered':
                break
        if spec['kind'] == 'navigate' and proof['steps'] and proof['steps'][-1]['status'] == 'delivered':
            try:
                await page.wait_for_url(urljoin(initial_url, spec['resource']),
                                        wait_until='domcontentloaded', timeout=900)
            except TimeoutError:
                pass
        proof['after'] = await _snapshot(page, spec)
    except Error:
        proof['interrupted'] = True
    return proof


async def capture(criterion, page, plan):
    validate_plan(criterion, plan)
    initial_url = page.url
    binding = '__wcagKeyboardEvidence_' + uuid4().hex
    inputs = {}

    def input_received(source, event):
        if source['frame'] == page.main_frame and isinstance(event, dict):
            token = event.pop('token', None)
            if isinstance(token, str):
                inputs[token] = event

    await page.expose_binding(binding, input_received)
    spec = plan['result']
    pointer = await _trial(page, initial_url, [dict(selector=target) for target in plan['pointer']],
                           spec, binding, inputs)
    keyboard = [await _trial(page, initial_url, actions, spec, binding, inputs)
                for actions in _keyboard_routes(plan)]
    return {'initial_url': initial_url, 'pointer': pointer, 'keyboard': keyboard}


def _achieved(spec, before, after, url):
    if not isinstance(before, dict) or not isinstance(after, dict):
        return None
    kind = spec['kind']
    if before.get('url') != url or (kind != 'navigate' and after.get('url') != url):
        return None
    if kind == 'increase':
        first, last = before.get('number'), after.get('number')
        if all(type(value) in (int, float) and math.isfinite(value) for value in (first, last)):
            return last > first
        return None
    if kind == 'reveal':
        if before.get('visible') is False and type(after.get('visible')) is bool:
            return after['visible'] and after.get('state') == 'true'
        return None
    headings = after.get('headings')
    destination = urljoin(url, spec['resource'])
    if destination != url and isinstance(headings, list):
        return after.get('url') == destination and spec['heading'] in headings
    return None


def _trial_result(trial, actions, spec, url):
    if not isinstance(trial, dict) or trial.get('actions') != actions or trial.get('interrupted'):
        return None
    steps = trial.get('steps')
    if not isinstance(steps, list) or not 1 <= len(steps) <= len(actions):
        return None
    for action, step in zip(actions, steps):
        if not isinstance(step, dict):
            return None
        key = action.get('key')
        tabs = step.get('tabs')
        if type(tabs) is not int or not 0 <= tabs <= (TAB_LIMIT if action.get('reach') == 'tab' else 0):
            return None
        if step.get('status') == 'unreached' and key is not None:
            exhausted = tabs == (TAB_LIMIT if action['reach'] == 'tab' else 0)
            return False if exhausted else None
        event = step.get('event')
        if (step.get('status') != 'delivered' or not isinstance(event, dict)
                or event.get('trusted') is not True or event.get('target_match') is not True
                or event.get('type') != ('keydown' if key is not None else 'click')
                or event.get('key') != (' ' if key == 'Space' else key)):
            return None
    if len(steps) != len(actions):
        return None
    return _achieved(spec, trial.get('before'), trial.get('after'), url)


def evaluate(criterion, plan, evidence):
    validate_plan(criterion, plan)
    outcome = 'cant_tell'
    observed = '同じ機能をポインターで実行できた証拠を確認できない。'
    if not isinstance(evidence, dict) or not isinstance(evidence.get('initial_url'), str):
        return []
    url = evidence['initial_url']
    spec = plan['result']
    pointer = _trial_result(evidence.get('pointer'), [dict(selector=target) for target in plan['pointer']], spec, url)
    keyboard = evidence.get('keyboard')
    routes = _keyboard_routes(plan)
    if pointer is True and isinstance(keyboard, list) and len(keyboard) == len(routes):
        results = [_trial_result(trial, actions, spec, url) for trial, actions in zip(keyboard, routes)]
        result_label = {'increase': '数量の増加', 'reveal': '表示と部品の状態の切替', 'navigate': '目的のページへの到達'}[spec['kind']]
        if True in results:
            outcome = 'passed'
            observed = f'ポインターと実キー操作の両方で、{result_label}を確認した。'
        elif all(result is False for result in results):
            outcome = 'failed'
            observed = f'ポインターでは{result_label}を確認したが、指定した実キー経路ではその結果を得られなかった。'
        else:
            observed = 'ポインターでは機能を実行できた。確認できないキー操作又は機能の観測が残る。'
    return [dict(target=plan['target'], checkpoint=POINT, outcome=outcome, observed=observed)]
