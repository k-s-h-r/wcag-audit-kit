"""Run explicitly configured keyboard paths and record observed results."""
import re
from urllib.parse import urldefrag

from browser_capture import FOCUS, OPEN_FOCUS_PATH, in_scope, normalize


CRITERIA = {'2.1.1', '2.1.2', '2.4.3'}
KEYS = {'Tab', 'Shift+Tab', 'Enter', 'Space', 'Escape'}
MATCH_FOCUS = '(e) => e.ownerDocument.hasFocus() && (' + OPEN_FOCUS_PATH + ')(e.ownerDocument).element === e'


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


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
            raise ValueError('キー操作の経路名と対象基準（2.1.1、2.1.2、2.4.3）を指定する')
        steps = check.get('steps')
        if not isinstance(steps, list) or not 1 <= len(steps) <= 40:
            raise ValueError('各キー操作経路は1〜40手順')
        for step in steps:
            if not isinstance(step, dict) or set(step) - {'key', 'focus', 'visible', 'hidden'}:
                raise ValueError('手順にはkeyとfocus、visible、hiddenのうち少なくともいずれかの条件を指定する')
            key = step.get('key')
            if not isinstance(key, str) or key not in KEYS:
                raise ValueError('使用できるキーはTab、Shift+Tab、Enter、Space、Escape')
            if len(step) < 2 or any(not nonempty(value) for field, value in step.items() if field != 'key'):
                raise ValueError('各キー操作にはフォーカス又は表示状態のセレクターを指定する')
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


async def observe_conditions(page, step, destination):
    observations = []
    for kind, selector in step.items():
        if kind == 'key':
            continue
        locator = page.locator(selector)
        count = await locator.count()
        if count > 1:
            raise ValueError('条件の対象を一つに絞れない: ' + selector)
        if kind == 'focus':
            actual = count == 1 and await locator.evaluate(MATCH_FOCUS)
        else:
            actual = count == 1 and await locator.is_visible()
        observations.append({'kind': kind, 'selector': selector, 'actual': actual, 'matched': actual == (kind != 'hidden')})
    if destination:
        observations.append({'kind': 'destination', 'selector': destination, 'actual': page.url,
                             'matched': normalize(page.url) == normalize(destination)})
    return observations


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
        key = step['key'].split('+')[-1]
        if key == 'Space':
            key = '[character]'
        delivered = next((position for position, event in enumerate(observer.events[start:], start=start + 1)
                          if event['type'] == 'keydown' and event['isTrusted'] and event['is_main_frame']
                          and event['key'] == key and event['modifiers']['shift'] == (step['key'] == 'Shift+Tab')), None)
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
        labels = {'focus': 'フォーカス', 'visible': '表示', 'hidden': '非表示', 'destination': '移動先'}
        missed = '、'.join(f'{labels[c["kind"]]} {c["selector"]}' for c in entry['conditions'] if not c['matched'])
        observed = (f'{entry["index"]}手順目の {entry["key"]} 後に期待した{missed}を確認できない。'
                    f'実際のフォーカスは{describe_focus(entry.get("after"))}。')
    return dict(criterion=record['criterion'], checkpoint='キーボード経路 / '+record['id'], expected=name,
                outcome=record['outcome'], environment=environment, capture='キーボード経路 '+record['id'],
                state_label=f'{name} / {route}' if route else name, target=target, observed=observed,
                evidence=evidence, source='', note='指定したキー操作と到達条件の結果。達成基準全体の適否は別に確認する。')
