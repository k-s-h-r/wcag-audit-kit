"""Observe pointer transfer, Escape and optional duration for configured additional content."""
import asyncio
import math
import re

from browser_capture import OPEN_FOCUS_PATH
from keyboard_checks import matching_keydown


ASPECTS = ('hoverable', 'dismissible')
MAX_TRANSFER_SAMPLES = 64
SAMPLE_INTERVAL = 0.05
INITIAL_DISPLAY_LIMIT = 1.5
ACTIVE_ELEMENT = '() => (' + OPEN_FOCUS_PATH + ')(document).element'
TARGET_STATE = r'''(element, {excluded, at, near}) => {
    const {left, right, top, bottom} = element.getBoundingClientRect();
    const rect = {left, right, top, bottom};
    const state = (status, points = []) => ({status, rect, points});
    const parent = node => node.assignedSlot || node.parentElement || node.getRootNode().host;
    for (let node = element; node; node = parent(node)) {
        if (node.getAnimations().some(animation => animation.pending || animation.playState === 'running')) {
            return state('unstable');
        }
    }
    const {display, visibility} = getComputedStyle(element);
    if (display === 'contents') return state('unsupported');
    if (!element.checkVisibility({opacityProperty: true})) {
        return state('hidden');
    }
    if (visibility !== 'visible') {
        // A descendant can override inherited visibility.
        return state(element.childElementCount || element.shadowRoot?.childElementCount ? 'unsupported' : 'hidden');
    }
    const x0 = Math.max(0, left), x1 = Math.min(document.documentElement.clientWidth, right);
    const y0 = Math.max(0, top), y1 = Math.min(document.documentElement.clientHeight, bottom);
    if (x0 >= x1 || y0 >= y1) return state('outside');

    const fractions = [0.5, 0.2, 0.8];
    const candidates = at ? [at] : fractions.flatMap(dx => fractions.map(dy => ({
        x: Math.floor(x0 + (x1 - x0) * dx), y: Math.floor(y0 + (y1 - y0) * dy)
    })));
    if (near) {
        // A wide block can have a close edge even when its center is far away.
        const lowX = Math.ceil(x0), highX = Math.ceil(x1) - 1;
        const lowY = Math.ceil(y0), highY = Math.ceil(y1) - 1;
        const xs = [Math.max(lowX, Math.min(highX, near.x)), lowX, highX];
        const ys = [Math.max(lowY, Math.min(highY, near.y)), lowY, highY];
        candidates.push(...xs.flatMap(x => ys.map(y => ({x, y}))));
        const distance = ({x, y}) => Math.hypot(x - near.x, y - near.y);
        candidates.sort((left, right) => distance(left) - distance(right));
    }
    const points = [];
    for (const {x, y} of candidates) {
        if (x < x0 || x >= x1 || y < y0 || y >= y1) continue;
        if (points.some(point => point.x === x && point.y === y)) continue;
        if (excluded && x >= excluded.left && x < excluded.right && y >= excluded.top && y < excluded.bottom) continue;
        let hit = document.elementFromPoint(x, y);
        while (hit?.shadowRoot) {
            const next = hit.shadowRoot.elementFromPoint(x, y);
            if (!next || next === hit) break;
            hit = next;
        }
        let node = hit;
        while (node && node !== element) node = parent(node);
        points.push({x, y, target: hit && {tag: hit.localName, id: hit.id}, hits_target: node === element});
    }
    return state('visible', points);
}'''


HOLD_STATE = '''({anchor, content, focus}) => {
    const {left, top, right, bottom} = anchor.getBoundingClientRect();
    return {
        hover: anchor.isConnected && anchor.matches(':hover'),
        rect: {left, top, right, bottom},
        geometry: [innerWidth, innerHeight, scrollX, scrollY],
        focus_unchanged: document.hasFocus() && (''' + OPEN_FOCUS_PATH + ''')(document).element === focus,
        content_connected: content.isConnected,
        text: content.textContent,
    };
}'''


class Uncertain(ValueError):
    """The configured route lacks evidence to establish its result."""


def validate_check(check):
    required = {'id', 'name', 'trigger', 'popup'}
    if not isinstance(check, dict) or not required <= check.keys() or check.keys() - required - {'persistence_ms'}:
        raise ValueError('表示の確認経路にはid、name、trigger、popupを指定する')
    if 'persistence_ms' in check and (type(check['persistence_ms']) is not int or not 100 <= check['persistence_ms'] <= 3000):
        raise ValueError('persistence_msは100〜3000の整数を指定する')
    if not isinstance(check['id'], str) or not re.fullmatch(r'[a-z0-9-]{1,64}', check['id']):
        raise ValueError('表示の確認経路のidは小文字の英数字とハイフンを使う（64文字まで）')
    if any(not isinstance(check[field], str) or not check[field].strip() for field in ('name', 'trigger', 'popup')):
        raise ValueError('nameと、対象を一つに絞れるtrigger・popupを指定する')
    if check['trigger'] == check['popup']:
        raise ValueError('triggerとpopupには別の対象を指定する')
    return check


def observation(check, aspect, outcome, observed):
    return dict(aspect=aspect, outcome=outcome, observed=observed, target=check['popup'])


def invalidate(record, check, reason):
    aspects = (*ASPECTS, 'persistent') if 'persistence_ms' in check else ASPECTS
    record.update(outcome='cant_tell', reason=reason,
                  observations=[observation(check, aspect, 'cant_tell', reason) for aspect in aspects])


async def target_state(locator, excluded=None, at=None, near=None):
    count = await locator.count()
    if count > 1:
        raise Uncertain('セレクターに一致する対象を一つに絞れない。')
    if not count:
        return {'status': 'absent', 'rect': None, 'points': []}
    return await locator.evaluate(TARGET_STATE, {'excluded': excluded, 'at': at, 'near': near}, timeout=1200)


def hit_point(state):
    point = next((point for point in state['points'] if point['hits_target']), None)
    return {axis: point[axis] for axis in ('x', 'y')} if point else None


def hidden(state):
    return state['status'] in {'absent', 'hidden'}


def transfer_points(start, end):
    dx, dy = (end[axis] - start[axis] for axis in ('x', 'y'))
    # CSS integer rounding can add distance between sampled points.
    count = math.ceil(math.hypot(dx, dy) / 2.8)
    if not 1 <= count <= MAX_TRANSFER_SAMPLES:
        raise Uncertain('表示までのポインター経路を観察上限内で測定できない。')
    points = []
    previous = start
    for sample in range(1, count + 1):
        point = {'x': start['x'] + round(dx * sample / count), 'y': start['y'] + round(dy * sample / count)}
        if point != previous:
            points.append(point)
            previous = point
    return points


async def require_continuity(page, interrupted, origin):
    if interrupted() or await page.evaluate('() => [location.href, performance.timeOrigin]') != origin:
        raise Uncertain('通信・ページ移動の制限又はブラウザーの分岐で操作を中断した。')


async def settle(page, step, interrupted, origin):
    step['settling'] = await page.evaluate('() => window.__wcagWaitForUpdates()')
    await require_continuity(page, interrupted, origin)
    if step['settling']['status'] != 'quiet':
        raise Uncertain('操作後の更新が観察範囲に収まらない。')


async def find_event(page, observer, first, matches):
    deadline = asyncio.get_running_loop().time() + 1
    while not observer.dropped:
        observer.changed.clear()
        for index in range(first, len(observer.events)):
            event = observer.events[index]
            if observer.event_frames[index] == page.main_frame and event['isTrusted'] and matches(event):
                return index + 1, event
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            break
        try:
            await asyncio.wait_for(observer.changed.wait(), remaining)
        except TimeoutError:
            break
    raise Uncertain('指定した実ブラウザーの入力イベントを確認できない。')


async def pointer_move(page, locator, point, observer, step):
    from playwright.async_api import Error as BrowserError

    step['point'] = point
    step.pop('input_event_index', None)
    step.pop('input_target_matched', None)
    await locator.evaluate('''element => {
        window.__wcagExpectedPointerTarget = element;
        window.__wcagObservePointerMove = true;
    }''', timeout=1200)
    first = len(observer.events)
    try:
        await page.mouse.move(point['x'], point['y'])
        index, event = await find_event(page, observer, first, lambda event: (
            event['type'] == 'pointermove' and event['pointerType'] == 'mouse' and event['buttons'] == 0
            and all(event[axis] == value for axis, value in point.items())))
        step['input_event_index'] = index
        step['input_target_matched'] = event['expectedTargetMatched']
    finally:
        try:
            await page.evaluate('''() => {
                window.__wcagExpectedPointerTarget = null;
                window.__wcagObservePointerMove = false;
            }''')
        except BrowserError:
            # An interrupted document will be reported by the route or its caller.
            pass


async def open_popup(page, trigger, popup, observer, record, interrupted, origin, action, *, sample_open=False):
    step = {'action': action, 'trigger': await target_state(trigger)}
    record['steps'].append(step)
    point = hit_point(step['trigger'])
    if not point:
        raise Uncertain('トリガーのポインター入力位置を表示範囲内で確認できない。')
    await pointer_move(page, trigger, point, observer, step)
    if not step['input_target_matched']:
        raise Uncertain('ポインター移動をトリガーが受け取ったことを確認できない。')
    if sample_open:
        clock = asyncio.get_running_loop().time
        deadline = clock() + INITIAL_DISPLAY_LIMIT
        while True:
            await require_continuity(page, interrupted, origin)
            step['popup'] = await target_state(popup)
            if hit_point(step['popup']) or clock() >= deadline:
                break
            await asyncio.sleep(SAMPLE_INTERVAL)
    else:
        await settle(page, step, interrupted, origin)
        step['popup'] = await target_state(popup)
    if not hit_point(step['popup']):
        raise Uncertain('ポインターを重ねた状態で追加表示を確認できない。')
    return step


async def observe_persistence(page, trigger, popup, opened, focus, observer, record, interrupted, origin, duration_ms):
    from playwright.async_api import Error as BrowserError

    step = dict(action='hold-trigger', point=opened['point'], input_event_index=opened['input_event_index'],
                duration_ms=duration_ms, samples=[])
    record['steps'].append(step)
    anchor = content = None
    try:
        anchor = await trigger.element_handle(timeout=1200)
        content = await popup.element_handle(timeout=1200)
        if anchor is None or content is None:
            raise Uncertain('持続時間の観察に必要な要素を特定できない。')
        if await focus.evaluate("element => !element || ['iframe', 'frame'].includes(element.localName)"):
            raise Uncertain('表示時のフォーカスを確認できない。')
        handles = {'anchor': anchor, 'content': content, 'focus': focus}
        first = await page.evaluate(HOLD_STATE, handles)
        step['initial'] = {key: value for key, value in first.items() if key != 'text'}
        # Keep observing real pointer movement during the wait interval, with
        # no input of our own after the trusted move that opened the popup.
        await page.evaluate('() => { window.__wcagObservePointerMove = true }')
        start_event_count = len(observer.events)
        clock = asyncio.get_running_loop().time
        start = clock()
        while True:
            await require_continuity(page, interrupted, origin)
            state = await page.evaluate(HOLD_STATE, handles)
            if await trigger.count() != 1:
                raise Uncertain('観察中に同じトリガーと追加表示を確認できなくなった。')
            target = await target_state(popup)
            elapsed = (clock() - start) * 1000
            changed = [field for field in ('rect', 'geometry', 'text') if state[field] != first[field]]
            intervening_input = observer.dropped or any(e['isTrusted'] for e in observer.events[start_event_count:])
            step['samples'].append(dict(elapsed_ms=round(elapsed, 1), popup_status=target['status'],
                                        trigger_hovered=state['hover'], focus_unchanged=state['focus_unchanged'],
                                        changed=changed, intervening_input=bool(intervening_input)))
            if not state['hover'] or not state['focus_unchanged'] or changed or intervening_input:
                raise Uncertain('観察中にトリガー、表示内容、画面位置、フォーカス又は入力の条件が変わった。')
            if (not state['content_connected'] and target['status'] != 'absent') or (
                    not hidden(target) and target['rect'] != opened['popup']['rect']):
                raise Uncertain('観察中に別の追加表示又は表示位置への変化があった。')
            if hidden(target):
                step['visibility_lost_ms'] = round(elapsed, 1)
                if elapsed > duration_ms:
                    raise Uncertain('指定時間の境界をまたいで表示が消え、期間内の表示を確定できない。')
                return 'failed', f'トリガーにポインターを置いたまま、最初の計測から約{elapsed:.0f}ミリ秒で表示が消えた。'
            if not hit_point(target):
                raise Uncertain('観察中に追加表示を確認できなくなった。')
            if elapsed >= duration_ms:
                return 'passed', f'トリガーにポインターを置いたまま、指定した{duration_ms}ミリ秒の観察中に表示を確認した。'
            await asyncio.sleep(SAMPLE_INTERVAL)
    except BrowserError as error:
        raise Uncertain('持続時間の観察を完了できない。') from error
    finally:
        try:
            await page.evaluate('() => { window.__wcagObservePointerMove = false }')
        except BrowserError:
            # The document or context may already be gone.
            pass
        for element in (anchor, content):
            if element is not None:
                await element.dispose()


async def transfer(page, popup, opened, observer, record, interrupted, origin):
    before = await target_state(popup, excluded=opened['trigger']['rect'], near=opened['point'])
    step = {'action': 'move-to-popup', 'before': before, 'samples': []}
    record['steps'].append(step)
    point = hit_point(step['before'])
    if not point:
        raise Uncertain('トリガーの外にあり、追加表示に届くポインター位置を確認できない。')
    step['planned_point'] = point
    for position in transfer_points(opened['point'], point):
        await require_continuity(page, interrupted, origin)
        await pointer_move(page, popup, position, observer, step)
        result = await target_state(popup, at=position)
        step['samples'].append(dict(point=position, input_event_index=step['input_event_index'],
                                    input_target_matched=step['input_target_matched'], popup_status=result['status']))
        step['after'] = result
        if hidden(result):
            await settle(page, step, interrupted, origin)
            return 'failed', '追加表示に向けてポインターを移す途中で、追加表示が消えた。'
        if result['status'] != 'visible':
            raise Uncertain('ポインターを移す途中の追加表示の有無を確認できない。')
    await settle(page, step, interrupted, origin)
    step['after'] = await target_state(popup, at=point)
    if hidden(step['after']):
        return 'failed', '追加表示があった位置へポインターを移したあとに、追加表示が消えた。'
    if not step['input_target_matched'] or not hit_point(step['after']):
        raise Uncertain('追加表示へのポインター到達又は移動後の表示を確認できない。')
    return 'passed', 'ポインターの経路上で表示を確認し、追加表示に到達したあとも表示が残った。'


async def dismiss(page, trigger, popup, opened, observer, record, interrupted, origin):
    step = {'action': 'press-escape', 'before': await target_state(popup), 'point': opened['point']}
    record['steps'].append(step)
    if not hit_point(step['before']):
        raise Uncertain('Escapeを送る前に追加表示を確認できない。')
    if not await trigger.evaluate('element => element.matches(":hover")', timeout=1200):
        raise Uncertain('Escapeを送る前にポインターがトリガーにあることを確認できない。')
    focus = await page.evaluate_handle(ACTIVE_ELEMENT)
    try:
        step['focus_before'] = await focus.evaluate('''element => !document.hasFocus() || !element
            ? null : {tag: element.localName, id: element.id}''')
        if not step['focus_before'] or step['focus_before']['tag'] in {'frame', 'iframe'}:
            raise Uncertain('Escapeを送る文書のフォーカスを確認できない。')
        first = len(observer.events)
        await page.keyboard.press('Escape')
        step['input_event_index'], _ = await find_event(page, observer, first, lambda event: matching_keydown(event, 'Escape'))
        await settle(page, step, interrupted, origin)
        step['focus_unchanged'] = await focus.evaluate(
            'element => document.hasFocus() && (' + OPEN_FOCUS_PATH + ')(document).element === element')
    finally:
        await focus.dispose()
    step['trigger_hovered'] = await trigger.evaluate('element => element.matches(":hover")', timeout=1200)
    step['after'] = await target_state(popup)
    if not step['focus_unchanged'] or not step['trigger_hovered']:
        raise Uncertain('Escapeの前後でポインターを重ねたトリガーとフォーカスを維持できたか確認できない。')
    if hidden(step['after']):
        return 'passed', 'ポインターとフォーカスを維持し、Escapeで追加表示が消えた。'
    if hit_point(step['after']):
        return 'failed', 'ポインターとフォーカスを維持してEscapeを押したあとも、追加表示が残った。'
    raise Uncertain('Escape後の表示状態を確定できない。')


async def run_path(page, check, observer, interrupted, record):
    """Record observations for only the configured paths and displayed targets."""
    trigger, popup = (page.locator(check[field]) for field in ('trigger', 'popup'))
    record['steps'] = []
    record['observations'] = []
    origin = await page.evaluate('() => [location.href, performance.timeOrigin]')
    try:
        await require_continuity(page, interrupted, origin)
        record['initial'] = await target_state(popup)
        if not hidden(record['initial']):
            raise Uncertain('開始時に追加表示が隠れていることを確認できない。')
        duration_ms = check.get('persistence_ms')
        if duration_ms is None:
            opened = await open_popup(page, trigger, popup, observer, record, interrupted, origin, 'hover-trigger')
        else:
            focus = await page.evaluate_handle(ACTIVE_ELEMENT)
            try:
                opened = await open_popup(page, trigger, popup, observer, record, interrupted, origin,
                                          'hover-trigger', sample_open=True)
                try:
                    outcome, details = await observe_persistence(page, trigger, popup, opened, focus, observer,
                                                                 record, interrupted, origin, duration_ms)
                except Uncertain as error:
                    outcome, details = 'cant_tell', str(error)
                record['observations'].append(observation(check, 'persistent', outcome, details))
            finally:
                await focus.dispose()
    except Uncertain as error:
        invalidate(record, check, str(error))
        return

    try:
        outcome, details = await transfer(page, popup, opened, observer, record, interrupted, origin)
    except Uncertain as error:
        outcome, details = 'cant_tell', str(error)
    record['observations'].append(observation(check, 'hoverable', outcome, details))

    try:
        await require_continuity(page, interrupted, origin)
        if record['steps'][-1].get('point'):
            opened = await open_popup(page, trigger, popup, observer, record, interrupted, origin, 'hover-trigger-for-escape')
        outcome, details = await dismiss(page, trigger, popup, opened, observer, record, interrupted, origin)
    except Uncertain as error:
        outcome, details = 'cant_tell', str(error)
    record['observations'].append(observation(check, 'dismissible', outcome, details))

    try:
        await require_continuity(page, interrupted, origin)
    except Uncertain as error:
        invalidate(record, check, str(error))
        return
    unknown = [item['observed'] for item in record['observations'] if item['outcome'] == 'cant_tell']
    if unknown:
        record.update(outcome='cant_tell', reason=' '.join(unknown))
    else:
        record['outcome'] = 'failed' if any(item['outcome'] == 'failed' for item in record['observations']) else 'passed'
