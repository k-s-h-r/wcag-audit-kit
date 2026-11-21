"""Measure declared focus outlines and pointer targets on benchmark pages."""

import base64
from io import BytesIO
import math
import re

from border_contrast import DETAILS, as_hex, solid_line
from measure import contrast
from target_spacing import TARGET_RECTS, rect_is_valid, spacing_conflicts


FOCUS = '2.4.13'
SIZE = '2.5.8'
SELECTOR = re.compile(r'#[a-zA-Z][a-zA-Z0-9_-]*\Z')
REGISTER_TAB = r"""() => {
    const events = [];
    window.addEventListener('keydown', event => {
        if (event.key === 'Tab' && event.isTrusted) events.push(performance.timeOrigin);
    }, {capture: true});
    return events;
}"""


def validate_plan(criterion, plan):
    if criterion == FOCUS and isinstance(plan, dict) and set(plan) == {'target'}:
        targets = [plan['target']]
    elif criterion == SIZE and isinstance(plan, dict) and set(plan) == {'targets'}:
        targets = plan['targets']
    else:
        raise ValueError('対象のセレクターを指定する。')
    if (not isinstance(targets, list) or not 1 <= len(targets) <= 20
            or any(not isinstance(target, str) or not SELECTOR.fullmatch(target) for target in targets)
            or len(targets) != len(set(targets))):
        raise ValueError('20個以下の重複しないIDセレクターを指定する。')


def png_image(png, expected_size):
    from PIL import Image

    with Image.open(BytesIO(png), formats=['PNG']) as image:
        if (image.mode not in {'RGB', 'RGBA'} or png[24:25] != b'\x08'
                or image.size != expected_size or image.info.get('icc_profile')):
            raise ValueError('画面に対応する8ビットsRGBのPNGを確認できない。')
        if image.mode == 'RGBA' and image.getchannel('A').getextrema() != (255, 255):
            raise ValueError('画面の不透明な色を確認できない。')
        return image.convert('RGB')


def encode_crop(image, bounds):
    data = BytesIO()
    image.crop(bounds).save(data, format='PNG')
    return base64.b64encode(data.getvalue()).decode('ascii')


def focus_geometry(before, focused):
    if any(before[key] != focused[key] for key in ('viewport', 'scroll', 'url', 'document_start', 'dpr', 'border', 'ancestry')):
        raise ValueError('フォーカスの前後で文書・見える範囲・対象の寸法又は外枠が変わった。')
    if before['dpr'] != 1:
        raise ValueError('CSSピクセルと画面の画素が一対一で対応しない。')
    viewport = before['viewport']
    if not (0 < viewport[0] <= 1920 and 0 < viewport[1] <= 1200):
        raise ValueError('画面の画素数が観察範囲を超えた。')
    width, style, color, offset = focused['outline']
    width, rgb = solid_line(width, style, color)
    offset = int(offset[:-2])
    if not 0 <= offset <= 32:
        raise ValueError('外側の枠のオフセットを確定できない。')
    rect = before['rect']
    extent = width + offset
    outer = [rect[0] - extent, rect[1] - extent, rect[2] + extent, rect[3] + extent]
    if focused['rect'] != outer:
        raise ValueError('フォーカスの前後で対象の位置や寸法が変わった。')
    left, top, right, bottom = (math.floor(edge + .5) for edge in outer)
    if not (0 <= left < right <= viewport[0] and 0 <= top < bottom <= viewport[1]
            and 2 * width < min(right - left, bottom - top) <= max(right - left, bottom - top) <= 512):
        raise ValueError('外枠の全画素を観察できない。')
    return (left, top, right, bottom), width, rgb


async def capture_focus(page, selector):
    from PIL import ImageChops
    from playwright.async_api import Error as BrowserError

    locator = page.locator(selector)
    if await locator.count() != 1:
        return {'reason': '対象の部品を一意に特定できない。'}
    target = await locator.element_handle()
    events = await page.evaluate_handle(REGISTER_TAB)
    try:
        before = await target.evaluate(DETAILS, False)
        if before.get('reason'):
            return before
        if await target.evaluate('e => e === document.activeElement'):
            return {'reason': 'キーを押す前に対象へフォーカスが当たっていた。'}
        if not (0 < before['viewport'][0] <= 1920 and 0 < before['viewport'][1] <= 1200):
            return {'reason': '画面の画素数が観察範囲を超えた。'}
        source = await page.screenshot(type='png', scale='css', caret='initial', timeout=5000)
        for _ in range(12):
            await page.keyboard.press('Tab')
            if await target.evaluate('e => e === document.activeElement'):
                break
        focused = await target.evaluate(DETAILS, True)
        if focused.get('reason'):
            return focused
        tab_events = await events.json_value()
        bounds, _, _ = focus_geometry(before, focused)
        view = await page.screenshot(type='png', scale='css', caret='initial', timeout=5000)
        if await target.evaluate(DETAILS, True) != focused:
            return {'reason': 'フォーカスの撮影中に状態が変わった。'}
        viewport = tuple(before['viewport'])
        first, second = png_image(source, viewport), png_image(view, viewport)
        return dict(target=selector, before=before, focused=focused, bounds=list(bounds), tab_events=tab_events,
                    difference=ImageChops.difference(first, second).getbbox(),
                    frames=[encode_crop(first, bounds), encode_crop(second, bounds)])
    except (BrowserError, OSError, ValueError) as error:
        return {'reason': str(error)}
    finally:
        await events.dispose()
        await target.dispose()


async def capture(criterion, page, plan):
    validate_plan(criterion, plan)
    if criterion == FOCUS:
        try:
            return await capture_focus(page, plan['target'])
        except ImportError:
            return {'reason': 'フォーカス前後の画素計測には分析用依存関係のPillowが必要。'}
    return await page.evaluate(TARGET_RECTS, plan['targets'])


def focus_result(evidence, selector):
    if evidence.get('target') != selector or not evidence.get('tab_events'):
        raise ValueError('同じ対象へTabで移動した証拠がない。')
    before, focused = evidence['before'], evidence['focused']
    if any(event != before['document_start'] for event in evidence['tab_events']):
        raise ValueError('Tabが同じ文書で受け取られたことを確認できない。')
    bounds, width, rgb = focus_geometry(before, focused)
    if evidence['bounds'] != list(bounds):
        raise ValueError('枠の画像と座標が対応しない。')
    large = evidence['difference']
    if large and not (bounds[0] <= large[0] <= large[2] <= bounds[2]
                      and bounds[1] <= large[1] <= large[3] <= bounds[3]):
        raise ValueError('外枠の範囲以外でもフォーカス前後の画素が変わった。')
    size = bounds[2] - bounds[0], bounds[3] - bounds[1]
    frames = evidence['frames']
    if len(frames) != 2 or any(len(frame) > 1_500_000 for frame in frames):
        raise ValueError('画素比較の画像がそろわないか上限を超えた。')
    first, second = (png_image(base64.b64decode(frame, validate=True), size).load() for frame in frames)
    changed = qualifying = 0
    ratios = {}
    for y in range(size[1]):
        for x in range(size[0]):
            original, final = first[x, y], second[x, y]
            if original == final:
                continue
            if final != rgb or width <= x < size[0] - width and width <= y < size[1] - width:
                raise ValueError('画素の変化が単色の外枠だけに対応しない。')
            changed += 1
            if original not in ratios:
                ratios[original] = contrast(as_hex(rgb), as_hex(original))['ratio']
            qualifying += ratios[original] >= 3
    # Area of the two CSS pixel perimeter of an unchanged rectangular component.
    left, top, right, bottom = before['rect']
    reference = 4 * (right - left + bottom - top)
    note = (f'Tab前後の同じ座標で3:1以上変化した領域は {qualifying} CSS px²。'
            f'比較する2 CSS px外周の面積は {reference:.2f} CSS px²。'
            f'指定した単色外枠の変化は {changed} 画素。')
    return ('passed' if qualifying >= reference else 'failed'), note


def size_result(evidence, selector):
    items = evidence.get('items', [])
    if (not isinstance(items, list) or len(items) > 100 or any(not rect_is_valid(rect) for rect in items)
            or len({item['id'] for item in items}) != len(items)):
        raise ValueError('対象の実際の矩形と当たり判定の記録がそろわない。')
    rect = next((item for item in items if item['id'] == selector), None)
    if rect is None:
        raise ValueError('対象の実際の矩形と当たり判定を確認できない。')
    dimensions = f'実際の当たり判定を矩形内で確認した。寸法は {rect["width"]:.2f}×{rect["height"]:.2f} CSS px。'
    if min(rect['width'], rect['height']) >= 24:
        return 'passed', dimensions
    if rect.get('inline_text') is True:
        return 'passed', dimensions + '同じ行の前後に通常の文章があるインラインリンク。'
    if evidence.get('unresolved') is not False:
        raise ValueError('周囲の別の操作対象の形状を確認できない。')
    conflicts = spacing_conflicts(items, rect)
    if not conflicts:
        return 'passed', dimensions + '中央の直径24 CSS pxの円は他の対象や小型対象の円と重ならない。'
    if rect.get('explicit_size') is not True:
        raise ValueError('小さい対象に著者が寸法を指定したことを確認できない。')
    return 'failed', dimensions + '中央の直径24 CSS pxの円と重なる対象は ' + '、'.join(conflicts) + '。'


def evaluate(criterion, plan, evidence):
    validate_plan(criterion, plan)
    targets = [plan['target']] if criterion == FOCUS else plan['targets']
    measure = focus_result if criterion == FOCUS else size_result
    checkpoint = '2.4.13-01' if criterion == FOCUS else '2.5.8-02'
    results = []
    for target in targets:
        try:
            if not isinstance(evidence, dict):
                raise ValueError('実ブラウザーの観察結果がない。')
            if evidence.get('reason'):
                raise ValueError(evidence['reason'])
            outcome, observed = measure(evidence, target)
        except (ImportError, IndexError, KeyError, OSError, TypeError, ValueError) as error:
            outcome, observed = 'cant_tell', str(error)
        results.append(dict(target=target, checkpoint=checkpoint, outcome=outcome, observed=observed))
    return results
