"""Run explicitly configured keyboard paths and record observed results."""
import json
import re
from urllib.parse import urldefrag

from browser_capture import FOCUS, OPEN_FOCUS_PATH, in_scope, normalize


CRITERIA = {'2.1.1', '2.1.2', '2.4.3', '4.1.2'}
KEYS = ('Tab', 'Shift+Tab', 'Enter', 'Space', 'Escape', 'ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight')
SELECTOR_CONDITIONS = {'focus', 'visible', 'hidden'}
MATCH_FOCUS = '(e) => e.ownerDocument.hasFocus() && (' + OPEN_FOCUS_PATH + ')(e.ownerDocument).element === e'
TEXT_INPUT_VALUE = "(e) => e instanceof HTMLInputElement && ['text', 'search'].includes(e.type) ? e.value : null"


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_step(step):
    if not isinstance(step, dict) or set(step) - {'key', 'attributes', 'value'} - SELECTOR_CONDITIONS:
        raise ValueError('手順にはkeyとfocus、visible、hidden、attributes、valueのうち少なくともいずれかの条件を指定する')
    if step.get('key') not in KEYS:
        raise ValueError('使用できるキーは' + '、'.join(KEYS))
    if len(step) < 2:
        raise ValueError('各キー操作には少なくとも一つの到達条件を指定する')
    if any(not nonempty(step[field]) for field in SELECTOR_CONDITIONS & step.keys()):
        raise ValueError('focus、visible、hiddenにはセレクターを指定する')

    if 'attributes' in step:
        attributes = step['attributes']
        if not isinstance(attributes, list) or not attributes:
            raise ValueError('attributesには一つ以上の属性条件を指定する')
        for condition in attributes:
            if (not isinstance(condition, dict) or condition.keys() != {'selector', 'name', 'equals'}
                    or not nonempty(condition['selector']) or not isinstance(condition['name'], str)
                    or not re.fullmatch(r'aria-[a-z][a-z0-9-]*', condition['name'])
                    or condition['equals'] is not None and not isinstance(condition['equals'], str)):
                raise ValueError('属性条件にはselector、aria-*のname、文字列又はnullのequalsを指定する')

    if 'value' in step:
        condition = step['value']
        if (not isinstance(condition, dict) or condition.keys() != {'selector', 'equals'}
                or not nonempty(condition['selector']) or not isinstance(condition['equals'], str)):
            raise ValueError('入力値条件にはselectorと文字列のequalsを指定する')


def validate(config):
    checks = config.get('keyboard_checks', [])
    if not isinstance(checks, list) or len(checks) > 20:
        raise ValueError('keyboard_checksには20経路まで指定できる')
    seen = set()
    for check in checks:
        if not isinstance(check, dict) or set(check) - {'id', 'name', 'criterion', 'steps', 'destination'}:
            raise ValueError('キー操作の経路はid、name、criterion、steps、任意のdestinationを指定する')
        identifier = check.get('id')
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-z0-9-]{1,64}', identifier) or identifier in seen:
            raise ValueError('キー操作の経路には重複のないidが必要')
        seen.add(identifier)
        criterion = check.get('criterion')
        if not nonempty(check.get('name')) or not isinstance(criterion, str) or criterion not in CRITERIA:
            raise ValueError('キー操作の経路名と対象基準（2.1.1、2.1.2、2.4.3、4.1.2）を指定する')
        steps = check.get('steps')
        if not isinstance(steps, list) or not 1 <= len(steps) <= 40:
            raise ValueError('各キー操作経路は1〜40手順')
        for step in steps:
            validate_step(step)
        if criterion == '4.1.2' and not any('attributes' in step for step in steps):
            raise ValueError('4.1.2の経路にはDOMの状態を照合するattributes条件を指定する')
        if 'destination' in check:
            destination = check['destination']
            if not nonempty(destination) or not in_scope(destination, config):
                raise ValueError('リンク先は同じオリジンの対象範囲にある絶対URLを指定する')
            if steps[-1]['key'] not in {'Enter', 'Space'}:
                raise ValueError('リンク先を確認する最後の手順にはEnter又はSpaceを指定する')
    return checks


async def load_document(route, page, blocked):
    from playwright.async_api import Error as BrowserError

    request = route.request
    failure = {'method': request.method, 'url': request.url}
    if request.method != 'GET' or request.frame != page.main_frame:
        failure['reason'] = '指定経路ではメイン文書のGET移動だけを許可する'
    else:
        try:
            response = await route.fetch(max_redirects=0, timeout=5000)
        except BrowserError:
            failure['reason'] = '指定した文書への接続に失敗した'
        else:
            try:
                if not (300 <= response.status < 400 and response.headers.get('location')):
                    await route.fulfill(response=response)
                    return
                failure['reason'] = '指定した文書からのリダイレクトを保留した'
            finally:
                await response.dispose()
    blocked.append(failure)
    await route.abort()


def describe_focus(focus):
    if not focus or not focus.get('documentHasFocus'):
        return 'ページ外又は確認できない位置'
    parts = ['#' + host['id'] if host['id'] else host['tag'] for host in focus.get('shadowHosts', [])]
    if focus['id']:
        parts.append('#' + focus['id'])
    else:
        parts.append(focus['tag'] + (f"（{focus['text']}）" if focus.get('text') else ''))
    return ' → '.join(parts)


async def condition_target(page, selector):
    locator = page.locator(selector)
    count = await locator.count()
    if count > 1:
        raise ValueError('条件の対象を一つに絞れない: ' + selector)
    return locator if count else None


async def observe_condition(page, kind, condition):
    if kind in SELECTOR_CONDITIONS:
        selector = condition
        locator = await condition_target(page, selector)
        if kind == 'focus':
            actual = locator is not None and await locator.evaluate(MATCH_FOCUS)
        else:
            actual = locator is not None and await locator.is_visible()
        return {'kind': kind, 'selector': selector, 'actual': actual, 'matched': actual == (kind != 'hidden')}

    selector = condition['selector']
    locator = await condition_target(page, selector)
    if kind == 'attribute':
        name = condition['name']
        actual = await locator.get_attribute(name) if locator is not None else None
        details = {'name': name}
    else:
        actual = await locator.evaluate(TEXT_INPUT_VALUE) if locator is not None else None
        if locator is not None and actual is None:
            raise ValueError('value条件にはtext又はsearchの入力欄を指定する: ' + selector)
        details = {}
    expected = condition['equals']
    return {'kind': kind, 'selector': selector, **details, 'expected': expected, 'actual': actual,
            'found': locator is not None, 'matched': locator is not None and actual == expected}


async def observe_conditions(page, step, destination):
    observations = []
    for kind, condition in step.items():
        if kind == 'key':
            continue
        if kind == 'attributes':
            observations.extend([await observe_condition(page, 'attribute', entry) for entry in condition])
        else:
            observations.append(await observe_condition(page, kind, condition))
    if destination:
        observations.append({'kind': 'destination', 'selector': destination, 'actual': page.url,
                             'matched': normalize(page.url) == normalize(destination)})
    return observations


def matching_keydown(event, key):
    if event['type'] != 'keydown' or not event['isTrusted'] or not event['is_main_frame']:
        return False
    expected = '[character]' if key == 'Space' else key.split('+')[-1]
    modifiers = event['modifiers']
    return (event['key'] == expected and modifiers['shift'] == (key == 'Shift+Tab')
            and not any(modifiers[modifier] for modifier in ('control', 'alt', 'meta')))


async def run_path(page, check, allow_navigation, record, observer, interrupted):
    from playwright.async_api import TimeoutError as BrowserTimeout

    navigation_status = []

    def record_navigation(response):
        request = response.request
        if request.is_navigation_request() and request.frame == page.main_frame:
            navigation_status.append({'url': response.url, 'status': response.status})

    page.on('response', record_navigation)
    for index, step in enumerate(check['steps'], 1):
        if interrupted():
            raise ValueError('通信・ページ移動の制限又はブラウザーの分岐で操作を中断した')
        destination = check.get('destination') if index == len(check['steps']) else None
        if destination:
            allow_navigation.add(urldefrag(normalize(destination))[0])
        before = await page.evaluate(FOCUS, True)
        entry = {'index': index, 'key': step['key'], 'before': before, 'expected': step}
        record['steps'].append(entry)
        if not before or not before.get('documentHasFocus'):
            raise ValueError('操作前に文書内のフォーカスを確認できない')
        start = len(observer.events)
        await page.keyboard.press(step['key'])
        if destination:
            try:
                await page.wait_for_url(lambda url: normalize(url) == normalize(destination),
                                        wait_until='domcontentloaded', timeout=2200)
            except BrowserTimeout:
                pass
        entry['settling'] = await page.evaluate('() => window.__wcagWaitForUpdates()')
        entry['after'] = await page.evaluate(FOCUS, True)
        entry['url'] = page.url
        entry['conditions'] = await observe_conditions(page, step, destination)
        entry['navigation'] = navigation_status.copy()
        delivered = next((position for position, event in enumerate(observer.events[start:], start=start + 1)
                          if matching_keydown(event, step['key'])), None)
        if observer.dropped or delivered is None:
            raise ValueError('キー入力を文書に届けた証拠を確認できない')
        entry['input_event_index'] = delivered
        if entry['settling']['status'] != 'quiet':
            raise ValueError('キー操作後の更新が観察範囲に収まらない')
        if any(item['status'] >= 400 for item in navigation_status):
            raise ValueError('移動先のページを正常に読み込めない')
        if not all(condition['matched'] for condition in entry['conditions']):
            record['outcome'] = 'failed'
            return
    record['outcome'] = 'passed'


def display_value(value):
    if value is None:
        return 'なし'
    if len(value) > 120:
        value = value[:120] + '…'
    return json.dumps(value, ensure_ascii=False)


def describe_mismatch(condition):
    kind, selector = condition['kind'], condition['selector']
    if kind in {'attribute', 'value'}:
        label = condition['name'] if kind == 'attribute' else '入力値'
        actual = display_value(condition['actual']) if condition['found'] else '対象なし'
        return f'{selector} の {label} が {display_value(condition["expected"])}（実際: {actual}）'
    labels = {'focus': 'フォーカス', 'visible': '表示', 'hidden': '非表示', 'destination': '移動先'}
    return f'{labels[kind]} {selector}'


def report_row(record, environment, evidence):
    entry = record['steps'][-1] if record['steps'] else None
    stop = record['outcome'] != 'passed' and entry is not None
    name = record['name']
    route = ' → '.join(step['key'] for step in record['steps'])
    target = describe_focus(entry.get('before')) if stop else ''
    if record['outcome'] == 'passed':
        observed = f'{len(record["steps"])}手順の到達条件を確認した。'
    elif record.get('reason'):
        observed = record['reason']
    else:
        missed = '、'.join(describe_mismatch(c) for c in entry['conditions'] if not c['matched'])
        observed = (f'{entry["index"]}手順目の {entry["key"]} 後に期待した{missed}を確認できない。'
                    f'実際のフォーカスは{describe_focus(entry.get("after"))}。')
    if record['criterion'] == '4.1.2':
        note = '指定したDOMの状態を照合した結果。アクセシブル名・役割・支援技術での通知は追加確認。'
    else:
        note = '指定したキー操作と到達条件の結果。達成基準全体の適否は別に確認する。'
    return dict(criterion=record['criterion'], checkpoint='キーボード経路 / '+record['id'], expected=name,
                outcome=record['outcome'], environment=environment, capture='キーボード経路 '+record['id'],
                state_label=f'{name} / {route}' if route else name, target=target, observed=observed,
                evidence=evidence, source='', note=note)
