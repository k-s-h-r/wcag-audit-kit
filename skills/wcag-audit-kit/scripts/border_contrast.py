"""Measure a declared exterior border against the pixels immediately outside it."""

from contextlib import suppress
from importlib.util import find_spec
from math import floor
from pathlib import Path
import re

from measure import contrast


DETAILS = r"""
(element) => {
    const hold = reason => ({reason});
    if (window !== window.top || element.getRootNode() !== document || !element.isConnected
            || element.childElementCount || element.shadowRoot
            || element.localName.includes('-') || !element.checkVisibility?.({
                opacityProperty: true, visibilityProperty: true
            })) return hold('主文書内の表示されている単一の部品を確認できない。');

    const rect = element.getBoundingClientRect();
    const viewport = window.visualViewport;
    if (!viewport || viewport.scale !== 1 || viewport.offsetTop !== 0 || viewport.offsetLeft !== 0
            || element.getClientRects().length !== 1) return hold('表示範囲と対象の座標を対応付けられない。');
    const outer = {left: rect.left - 2, top: rect.top - 2, right: rect.right + 2, bottom: rect.bottom + 2};
    if (outer.left < 0 || outer.top < 0 || outer.right > document.documentElement.clientWidth
            || outer.bottom > document.documentElement.clientHeight)
        return hold('外枠とその外側の画素が画面内に収まらない。');

    const topLayer = document.querySelector(':modal, :popover-open, :fullscreen')
        || CSS.supports('selector(select:open)') && document.querySelector('select:open');
    const all = document.getElementsByTagName('*');
    if (topLayer || all.length > 2000 || document.getAnimations().some(
        animation => animation.pending || animation.playState === 'running'
    )) return hold('最前面レイヤー、動作中の描画、又は観測範囲の上限がある。');

    const generated = node => ['::before', '::after'].some(pseudo => {
        const style = getComputedStyle(node, pseudo);
        return !['none', 'normal'].includes(style.content) && style.display !== 'none';
    });
    const outsidePaint = style => style.boxShadow !== 'none' || style.textShadow !== 'none'
        || style.filter !== 'none' || style.backdropFilter !== 'none'
        || style.outlineStyle !== 'none'
        || style.borderImageSource !== 'none'
            && style.borderImageOutset.split(/\s+/).some(value => parseFloat(value) > 0);
    const parents = new Set(), ancestry = [];
    for (let node = element; node; node = node.parentElement) {
        parents.add(node);
        const style = getComputedStyle(node);
        if (style.visibility !== 'visible' || style.opacity !== '1' || style.clip !== 'auto'
                || style.clipPath !== 'none' || style.maskImage !== 'none'
                || style.backgroundImage !== 'none' || style.backgroundBlendMode !== 'normal'
                || style.transform !== 'none' || style.translate !== 'none' || style.rotate !== 'none'
                || style.scale !== 'none' || style.perspective !== 'none' || style.zoom !== '1'
                || style.mixBlendMode !== 'normal' || style.contain !== 'none'
                || style.contentVisibility !== 'visible' || outsidePaint(style) || generated(node))
            return hold('同じ条件で不透明な単色の枠と外側を確認できない。');
        const area = node.getBoundingClientRect();
        ancestry.push([node.localName, style.backgroundColor, style.color,
            area.left, area.top, area.right, area.bottom, style.backgroundClip, style.overflowX, style.overflowY]);
        if (node !== element && node !== document.documentElement && node !== document.body) {
            const left = area.left + node.clientLeft, top = area.top + node.clientTop;
            if ((style.overflowX !== 'visible' && (left > outer.left || left + node.clientWidth < outer.right))
                    || (style.overflowY !== 'visible' && (top > outer.top || top + node.clientHeight < outer.bottom)))
                return hold('祖先による切り取りが枠とその外側にかかる。');
        }
    }

    for (const node of all) {
        if (parents.has(node)) continue;
        const style = getComputedStyle(node);
        if (style.display === 'none' || style.opacity === '0' || style.visibility !== 'visible') continue;
        if (outsidePaint(style) || generated(node)) return hold('別の描画が要素の箱の外に重なる可能性がある。');
        const overlaps = Array.from(node.getClientRects()).some(box =>
            box.left < outer.right && box.right > outer.left && box.top < outer.bottom && box.bottom > outer.top);
        if (overlaps) return hold('別の要素が対象とその外側に重なる。');
    }

    const style = getComputedStyle(element);
    if (style.borderImageSource !== 'none'
            || ['TopLeft', 'TopRight', 'BottomLeft', 'BottomRight']
                .some(corner => style['border' + corner + 'Radius'] !== '0px'))
        return hold('角の形や枠の画像が単色の直線枠の条件に合わない。');
    const borders = ['Top', 'Right', 'Bottom', 'Left'].map(side =>
        ['Width', 'Style', 'Color'].map(property => style['border' + side + property]));
    return {
        rect: [rect.left, rect.top, rect.right, rect.bottom],
        viewport: [window.innerWidth, window.innerHeight],
        scroll: [window.scrollX, window.scrollY],
        dpr: window.devicePixelRatio,
        url: location.href,
        document_start: performance.timeOrigin,
        border: borders, ancestry
    };
}
"""

WATCH_CHANGES = """() => {
    const watcher = new MutationObserver(() => { watcher.changed = true; });
    watcher.observe(document, {subtree: true, childList: true, attributes: true, characterData: true});
    return watcher;
}"""


def as_hex(channels):
    return '#%02x%02x%02x' % channels


def border_definition(data):
    width, style, color = data['border'][0]
    channels = re.fullmatch(r'rgb\((\d+), (\d+), (\d+)\)', color)
    if (any(side != [width, style, color] for side in data['border'])
            or style != 'solid' or not re.fullmatch(r'[1-9]\d*px', width) or not channels):
        raise ValueError('四辺で同じ幅の不透明な単色の実線枠を確認できない。')
    width = int(width[:-2])
    if width > 32:
        raise ValueError('枠が観察範囲より太い。')
    return width, tuple(map(int, channels.groups()))


def strip_pairs(rect, width):
    left, top, right, bottom = [floor(edge + .5) for edge in rect]
    if min(right - left, bottom - top) <= 4 * width + 8:
        raise ValueError('角の影響を除いた枠の中央を測る領域が足りない。')
    margin = width + 3
    across, down = range(left + margin, right - margin), range(top + margin, bottom - margin)
    return {
        'top': (((x, top + width // 2), (x, top - 1)) for x in across),
        'right': (((right - 1 - width // 2, y), (right, y)) for y in down),
        'bottom': (((x, bottom - 1 - width // 2), (x, bottom)) for x in across),
        'left': (((left + width // 2, y), (left - 1, y)) for y in down),
    }


def pixel_result(path, data, width, expected, pairs):
    from PIL import Image

    with path.open('rb') as capture:
        header = capture.read(25)
        capture.seek(0)
        with Image.open(capture) as image:
            if (image.format != 'PNG' or image.mode not in {'RGB', 'RGBA'} or header[24:25] != b'\x08'
                    or image.size != tuple(data['viewport']) or image.info.get('icc_profile')):
                raise ValueError('表示範囲に対応する8ビットsRGBのPNGを確認できない。')
            if image.mode == 'RGBA' and image.getchannel('A').getextrema() != (255, 255):
                raise ValueError('透過する画像は表示色の測定に使えない。')
            pixels = image.load()
            by_side = {}
            for side, points in pairs.items():
                count = 0
                border, outside = set(), set()
                for a, b in points:
                    count += 1
                    border.add(pixels[a][:3])
                    outside.add(pixels[b][:3])
                by_side[side] = (count, border, outside)

    samples = {side: {'count': count, 'border': sorted(border)[:5], 'outside': sorted(outside)[:5]}
               for side, (count, border, outside) in by_side.items()}
    if any(border != {expected} for _, border, _ in by_side.values()):
        return dict(status='cant_tell', observed='枠の実際の画素が計算済みの単色と一致しない。', samples=samples)
    outside_colors = set().union(*(outside for _, _, outside in by_side.values()))
    if len(outside_colors) != 1:
        return dict(status='cant_tell', observed='枠の外側の画素が単色でそろわない。', samples=samples)
    border_color, outside_color = as_hex(expected), as_hex(outside_colors.pop())
    result = contrast(border_color, outside_color)
    return dict(status='measured', observed='指定した外枠と隣接する画素の比を測定した。',
                border=border_color, outside=outside_color, width=width, minimum=3,
                ratio=result['ratio'], meets_3=result['meets_3'], samples=samples)


async def observe(page, selector, images, path):
    """Run in the requested state. The caller identifies the required boundary."""
    from playwright.async_api import Error as BrowserError

    output = {'target': selector}
    path = Path(path)
    watcher = target = None
    if images.policy['screenshots'] != 'all':
        return dict(output, status='skipped', observed='画像設定がall以外のため外枠の画像を取得しなかった。')
    if not find_spec('PIL'):
        return dict(output, status='cant_tell', observed='PNGの画素を調べるにはrequirements-analysis.txtのPillowが必要。')
    try:
        locator = page.locator(selector)
        if await locator.count() != 1 or await locator.is_disabled(timeout=1500):
            raise ValueError('無効な部品、又は対象を一つに特定できない。')
        target = await locator.element_handle(timeout=1500)
        watcher = await page.evaluate_handle(WATCH_CHANGES)
        first = await target.evaluate(DETAILS)
        if 'reason' in first:
            raise ValueError(first['reason'])
        width, expected = border_definition(first)
        pairs = strip_pairs(first['rect'], width)
        if not await images.capture_with(path, 'detail', lambda: page.screenshot(
                path=str(path), scale='css', caret='initial', timeout=5000)):
            return dict(output, status='skipped', observed='画像の設定又は取得上限により外枠の画像を取得しなかった。')
        output['source'] = path.relative_to(images.run).as_posix()
        output['geometry'] = first
        second = await target.evaluate(DETAILS)
        changed = await watcher.evaluate(
            'watcher => {const changed = watcher.changed || watcher.takeRecords().length > 0; watcher.disconnect(); return changed;}'
        )
        if changed or first != second or await locator.count() != 1 or not await locator.evaluate(
                '(selected, original) => selected === original', target, timeout=1500):
            raise ValueError('画像取得の前後で部品、画面、又はDOMの状態が変わった。')
        return dict(output, **pixel_result(path, first, width, expected, pairs))
    except (BrowserError, OSError, ValueError) as problem:
        return dict(output, status='cant_tell', observed=str(problem))
    finally:
        if watcher:
            with suppress(BrowserError):
                await watcher.evaluate('watcher => watcher.disconnect()')
                await watcher.dispose()
        if target:
            with suppress(BrowserError):
                await target.dispose()
