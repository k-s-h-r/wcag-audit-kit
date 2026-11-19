"""Measure a declared exterior border or focus outline against its adjacent pixels."""

from contextlib import suppress
from importlib.util import find_spec
from math import ceil, floor
from pathlib import Path
import re

from measure import contrast


DETAILS = r"""
(element, focused) => {
    const hold = reason => ({reason});
    if (window !== window.top || element.getRootNode() !== document || !element.isConnected
            || element.childElementCount || element.shadowRoot
            || element.localName.includes('-') || !element.checkVisibility?.({
                opacityProperty: true, visibilityProperty: true
            })) return hold('主文書内の表示されている単一の部品を確認できない。');

    const style = getComputedStyle(element);
    if (focused && (!document.hasFocus() || document.activeElement !== element
            || !element.matches(':focus-visible')))
        return hold('実キー操作を受けた対象がフォーカス表示の状態にない。');
    const offset = focused ? parseFloat(style.outlineOffset) : 0;
    if (!Number.isInteger(offset) || offset < 0 || offset > 32)
        return hold('外側にあるフォーカス枠の間隔を確定できない。');
    const extent = focused ? offset + parseFloat(style.outlineWidth) : 0;
    const rect = element.getBoundingClientRect();
    const edges = [rect.left - extent, rect.top - extent, rect.right + extent, rect.bottom + extent];
    const viewport = window.visualViewport;
    if (!viewport || viewport.scale !== 1 || viewport.offsetTop !== 0 || viewport.offsetLeft !== 0
            || element.getClientRects().length !== 1) return hold('表示範囲と対象の座標を対応付けられない。');
    const outer = {left: edges[0] - 2, top: edges[1] - 2, right: edges[2] + 2, bottom: edges[3] + 2};
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
    const outsidePaint = (style, allowOutline = false) => style.boxShadow !== 'none' || style.textShadow !== 'none'
        || style.filter !== 'none' || style.backdropFilter !== 'none'
        || !allowOutline && style.outlineStyle !== 'none'
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
                || style.contentVisibility !== 'visible' || outsidePaint(style, focused && node === element) || generated(node))
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

    if (style.borderImageSource !== 'none'
            || ['TopLeft', 'TopRight', 'BottomLeft', 'BottomRight']
                .some(corner => style['border' + corner + 'Radius'] !== '0px'))
        return hold('角の形や枠の画像が単色の直線枠の条件に合わない。');
    const borders = ['Top', 'Right', 'Bottom', 'Left'].map(side =>
        ['Width', 'Style', 'Color'].map(property => style['border' + side + property]));
    return {
        rect: edges,
        viewport: [window.innerWidth, window.innerHeight],
        scroll: [window.scrollX, window.scrollY],
        dpr: window.devicePixelRatio,
        url: location.href,
        document_start: performance.timeOrigin,
        border: borders, ancestry,
        ...(focused ? {outline: [style.outlineWidth, style.outlineStyle, style.outlineColor, style.outlineOffset]} : {})
    };
}
"""

WATCH_CHANGES = """() => {
    const watcher = new MutationObserver(() => { watcher.changed = true; });
    watcher.observe(document, {subtree: true, childList: true, attributes: true, characterData: true});
    return watcher;
}"""

BEFORE_FOCUS = """element => {
    const style = getComputedStyle(element);
    return {focused: document.activeElement === element, url: location.href,
        document_start: performance.timeOrigin,
        outline: [style.outlineWidth, style.outlineStyle, style.outlineColor, style.outlineOffset]};
}"""


def as_hex(channels):
    return '#%02x%02x%02x' % channels


def border_definition(data):
    width, style, color = data['border'][0]
    if any(side != [width, style, color] for side in data['border']):
        raise ValueError('四辺で同じ幅の不透明な単色の実線枠を確認できない。')
    return solid_line(width, style, color)


def solid_line(width, style, color):
    channels = re.fullmatch(r'rgb\((\d+), (\d+), (\d+)\)', color)
    if style != 'solid' or not re.fullmatch(r'[1-9]\d*px', width) or not channels:
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


def validate(checks):
    if not isinstance(checks, list) or len(checks) > 20:
        raise ValueError('border_checksには20対象まで指定できる')
    seen = set()
    for check in checks:
        if not isinstance(check, dict) or set(check) != {'id', 'name', 'target'}:
            raise ValueError('外枠の測定にはid、name、targetを指定する')
        identifier = check['id']
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-z0-9-]{1,64}', identifier) or identifier in seen:
            raise ValueError('外枠の測定には重複のない英小文字・数字・ハイフンのidを指定する')
        if any(not isinstance(check[key], str) or not check[key].strip() for key in ('name', 'target')):
            raise ValueError('外枠の測定には名前と対象を一つに絞るセレクターを指定する')
        seen.add(identifier)


async def observe(page, selector, images, path):
    """Run in the requested state. The caller identifies the required boundary."""
    from playwright.async_api import Error as BrowserError

    output = {'target': selector}
    path = Path(path)
    target = None
    if images.policy['screenshots'] != 'all':
        return dict(output, status='skipped', observed='画像設定がall以外のため外枠の画像を取得しなかった。')
    if not find_spec('PIL'):
        return dict(output, status='cant_tell', observed='PNGの画素を調べるにはrequirements-analysis.txtのPillowが必要。')
    try:
        locator = page.locator(selector)
        if await locator.count() != 1 or await locator.is_disabled(timeout=1500):
            raise ValueError('無効な部品、又は対象を一つに特定できない。')
        target = await locator.element_handle(timeout=1500)
        async def capture(_):
            return await images.capture_with(path, 'detail', lambda: page.screenshot(
                path=str(path), scale='css', caret='initial', timeout=5000))

        return await measure_target(page, locator, target, path, images.run, capture, output)
    except (BrowserError, OSError, ValueError) as problem:
        return dict(output, status='cant_tell', observed=str(problem))
    finally:
        if target:
            with suppress(BrowserError):
                await target.dispose()


async def measure_target(page, locator, target, path, run, capture, output, *, before=None):
    from playwright.async_api import Error as BrowserError

    watcher = await page.evaluate_handle(WATCH_CHANGES)
    focused = before is not None
    try:
        first = await target.evaluate(DETAILS, focused)
        if 'reason' in first:
            raise ValueError(first['reason'])
        rect = first['rect']
        geometry = first
        clip = None
        if focused:
            if any(before[key] != first[key] for key in ('document_start', 'url')):
                raise ValueError('キー入力前後で同じ文書を確認できない。')
            if before['focused'] or before['outline'] == first['outline']:
                raise ValueError('キー入力で現れるフォーカス枠を確認できない。')
            width, expected = solid_line(*first['outline'][:3])
            left, top = floor(rect[0]) - 1, floor(rect[1]) - 1
            size = [ceil(rect[2]) + 1 - left, ceil(rect[3]) + 1 - top]
            clip = dict(x=left, y=top, width=size[0], height=size[1])
            geometry = dict(first, clip=clip)
            data = {'viewport': size}
            rect = [edge - origin for edge, origin in zip(rect, (left, top, left, top))]
        else:
            width, expected = border_definition(first)
            data = first
        pairs = strip_pairs(rect, width)
        if not await capture(clip):
            return dict(output, status='skipped', observed='画像の設定又は取得上限により外枠の画像を取得しなかった。')
        output['source'] = path.relative_to(run).as_posix()
        output['geometry'] = geometry
        second = await target.evaluate(DETAILS, focused)
        changed = await watcher.evaluate(
            'watcher => {const changed = watcher.changed || watcher.takeRecords().length > 0; watcher.disconnect(); return changed;}'
        )
        if changed or first != second or await locator.count() != 1 or not await locator.evaluate(
                '(selected, original) => selected === original', target, timeout=1500):
            raise ValueError('画像取得の前後で部品、画面、又はDOMの状態が変わった。')
        return dict(output, **pixel_result(path, data, width, expected, pairs))
    finally:
        with suppress(BrowserError):
            await watcher.evaluate('watcher => watcher.disconnect()')
            await watcher.dispose()


class FocusOutline:
    def __init__(self, page, selector, run, path):
        self.page = page
        self.selector = selector
        self.run = run
        self.path = path
        self.target = None
        self.baseline = None
        self.reason = None

    async def before(self):
        from playwright.async_api import Error as BrowserError

        if not find_spec('PIL'):
            self.reason = 'PNGの画素を調べるにはrequirements-analysis.txtのPillowが必要。'
            return
        try:
            locator = self.page.locator(self.selector)
            if await locator.count() != 1 or await locator.is_disabled(timeout=1500):
                raise ValueError('無効な部品、又はキー入力前の対象を一つに特定できない。')
            self.target = await locator.element_handle(timeout=1500)
            self.baseline = await self.target.evaluate(BEFORE_FOCUS)
        except (BrowserError, ValueError) as problem:
            self.reason = str(problem)

    async def measure(self):
        from playwright.async_api import Error as BrowserError

        output = dict(target=self.selector, before=self.baseline)
        if self.reason:
            return dict(output, status='cant_tell', observed=self.reason)

        async def capture(clip):
            await self.page.screenshot(path=str(self.path), clip=clip, scale='css', caret='initial', timeout=5000)
            return True

        try:
            return await measure_target(self.page, self.page.locator(self.selector), self.target,
                                        self.path, self.run, capture, output, before=self.baseline)
        except (BrowserError, OSError, ValueError) as problem:
            return dict(output, status='cant_tell', observed=str(problem))

    async def close(self):
        from playwright.async_api import Error as BrowserError

        if self.target:
            with suppress(BrowserError):
                await self.target.dispose()
