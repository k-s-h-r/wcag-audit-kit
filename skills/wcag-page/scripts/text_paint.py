"""Measure rendered text using a controlled fill in a disposable Chromium context."""
from collections import Counter
from contextlib import suppress
from hashlib import sha256
from importlib.util import find_spec
from io import BytesIO
import math
import re

from measure import contrast


CAPTURE_STAGES = {
    'original': None, 'original-repeat': None, 'transparent': 'rgba(0, 0, 0, 0)',
    'black': 'rgb(0, 0, 0)', 'white': 'rgb(255, 255, 255)', 'restored': None, 'restored-repeat': None,
}
FILL = '-webkit-text-fill-color'
RGB = re.compile(r'rgb\((\d+), (\d+), (\d+)\)')
LOAD_OBSERVER = """() => {
    window.__probeViolations = [];
    document.addEventListener('securitypolicyviolation', event => {
        window.__probeViolations.push(event.violatedDirective);
    });
}"""
RESTORE = """(e, value) => {
    if (value === null) e.removeAttribute('style');
    else e.setAttribute('style', value);
}"""
WATCH_CHANGES = """target => {
    const watcher = new MutationObserver(records => { if (records.length) watcher.changed = true; });
    watcher.observe(document, {subtree:true, childList:true, attributes:true, characterData:true});
    watcher.changed = false;
    watcher.write = ([property, fill, original]) => {
        if (watcher.changed || watcher.takeRecords().length) {
            watcher.changed = true;
            return null;
        }
        if (fill !== null) target.style.setProperty(property, fill, 'important');
        else if (original === null) target.removeAttribute('style');
        else target.setAttribute('style', original);
        const records = watcher.takeRecords();
        if (records.length > 1 || records.some(record =>
            record.target !== target || record.type !== 'attributes' || record.attributeName !== 'style'
        )) watcher.changed = true;
        return target.getAttribute('style');
    };
    return watcher;
}"""

STATE = r"""(e) => {
  if (!e.isConnected || e.ownerDocument !== document || e.getRootNode() !== document ||
      typeof e.checkVisibility !== 'function') return null;
  const selection = getSelection();
  const v = window.visualViewport;
  if (!v) return null;
  const range = document.createRange();
  range.selectNodeContents(e);
  const s = getComputedStyle(e);
  const copy = (style, exclude = []) => Array.from(style).filter(name => !exclude.includes(name))
      .map(name => [name, style.getPropertyValue(name)]);
  const rect = r => [r.x,r.y,r.width,r.height];
  const ancestors = [];
  for (let node = e.parentElement; node; node = node.parentElement) {
    ancestors.push(copy(getComputedStyle(node)));
  }
  const fill = s.getPropertyValue('-webkit-text-fill-color');
  const usesUniformFontAndFill = ['::first-letter', '::first-line'].every(pseudo => {
    const style = getComputedStyle(e, pseudo);
    return ['font-size', 'font-weight', 'font-family', 'font-style', 'font-size-adjust', 'font-variation-settings',
      'opacity', 'text-shadow',
      'text-decoration-line', '-webkit-text-fill-color', '-webkit-text-stroke-width']
      .every(property => style.getPropertyValue(property) === s.getPropertyValue(property));
  });
  const focus = document.activeElement;
  const chain = [e];
  for (let node = e.parentElement; node; node = node.parentElement) chain.push(node);
  const nonplain = chain.flatMap((node, i) => {
    const c = getComputedStyle(node);
    const reasons = [];
    for (const name of ['filter', 'backdrop-filter', 'transform', 'mask-image', 'clip-path', 'perspective',
                        'text-shadow', 'translate', 'scale', 'rotate', 'mask-border-source']) {
      const value = c.getPropertyValue(name);
      if (value && value !== 'none') reasons.push(name);
    }
    for (const [name, expected] of [['opacity', '1'], ['mix-blend-mode', 'normal'], ['zoom', '1']]) {
      if (c.getPropertyValue(name) && c.getPropertyValue(name) !== expected) reasons.push(name);
    }
    if (c.getPropertyValue('clip') !== 'auto') reasons.push('clip');
    if (c.backgroundClip.includes('text')) reasons.push('background-clip');
    if (c.backgroundImage !== 'none') reasons.push('background-image');
    if (c.contentVisibility !== 'visible' || c.willChange !== 'auto') reasons.push('composited-content');
    if (c.getPropertyValue('text-decoration-line') !== 'none') reasons.push('text-decoration');
    if (!i) {
      for (const [property, initial] of [['font-size-adjust', 'none'], ['font-variation-settings', 'normal']]) {
        if (c.getPropertyValue(property) !== initial) reasons.push(property);
      }
      if (c.getPropertyValue('-webkit-text-stroke-width') !== '0px') reasons.push('text-stroke');
      if (c.textOverflow !== 'clip') reasons.push('text-overflow');
      if (node.getClientRects().length !== 1) reasons.push('fragmentation');
    }
    return reasons.map(reason => node.localName + ':' + reason);
  });
  // Reject independently painted layers that could hide some tested glyphs.
  const region = range.getBoundingClientRect();
  const overlaps = rect => rect.left < region.right + 1 && rect.right > region.left - 1 &&
                           rect.top < region.bottom + 1 && rect.bottom > region.top - 1;
  const textOverlaps = node => [...node.childNodes].some(child => {
    if (child.nodeType !== Node.TEXT_NODE || !child.textContent.trim()) return false;
    const siblingRange = document.createRange();
    siblingRange.selectNode(child);
    return [...siblingRange.getClientRects()].some(overlaps);
  });
  const clips = c => c.overflowX !== 'visible' || c.overflowY !== 'visible';
  const safeArea = (node, c) => {
    const r = node.getBoundingClientRect();
    if (!clips(c)) return true;
    if (['TopLeft','TopRight','BottomLeft','BottomRight'].some(k => c['border'+k+'Radius'] !== '0px')) return false;
    const left=r.left+node.clientLeft, top=r.top+node.clientTop;
    return region.left >= left && region.top >= top &&
           region.right <= left+node.clientWidth && region.bottom <= top+node.clientHeight;
  };
  const generated = node => ['::before','::after'].some(which => {
    const s = getComputedStyle(node,which);
    return s.content !== 'none' && s.content !== 'normal' && s.display !== 'none';
  });
  const scene = [...document.querySelectorAll('*')];
  const possibleOverlaps = [];
  if (scene.length > 2000) possibleOverlaps.push('too_many_elements');
  if (scene.some(node => node.shadowRoot || node.localName.includes('-') || node.matches('iframe,frame,[is]')))
    possibleOverlaps.push('embedded_or_shadow_content');
  if (document.fullscreenElement || document.querySelector(':modal,:popover-open')
      || CSS.supports('selector(select:open)') && document.querySelector('select:open'))
    possibleOverlaps.push('top_layer_content');
  for (const node of chain) {
    if (generated(node) || getComputedStyle(node).display === 'list-item') possibleOverlaps.push('generated:'+node.localName);
    if (!safeArea(node, getComputedStyle(node))) possibleOverlaps.push('clipped:' + node.localName);
    if (node !== e && textOverlaps(node)) possibleOverlaps.push('overlap:' + node.localName);
  }
  if (scene.length <= 2000) for (const node of scene) {
    if (chain.includes(node) || !node.checkVisibility({opacityProperty:true,visibilityProperty:true,contentVisibilityAuto:true})) continue;
    const s = getComputedStyle(node);
    if (generated(node) || ['box-shadow','text-shadow','filter','backdrop-filter','border-image-source']
        .some(property => s.getPropertyValue(property) !== 'none') || s.outlineStyle !== 'none' ||
        [...node.getClientRects()].some(overlaps) || textOverlaps(node)) possibleOverlaps.push(node.id || node.localName);
  }
  return {
    nonplain, possibleOverlaps, fill, usesUniformFontAndFill, style:e.getAttribute('style'),
    styleFingerprint:[copy(s, ['-webkit-text-fill-color']), ancestors],
    tag:e.localName, childTypes:[...e.childNodes].map(n => n.nodeType),
    text:e.textContent, elementRect:rect(e.getBoundingClientRect()), rangeRects:[...range.getClientRects()].map(rect),
    viewport:[innerWidth,innerHeight,devicePixelRatio, v.width,v.height,v.offsetLeft,v.offsetTop,v.scale],
    scroll:[scrollX,scrollY], location:location.href, documentId:performance.timeOrigin,
    visible:e.checkVisibility({opacityProperty:true,visibilityProperty:true,contentVisibilityAuto:true}),
    font:[s.fontSize,s.fontWeight], fonts:document.fonts.status, blocked:window.__probeViolations?.length ?? 0,
    busy:document.getAnimations().some(a => a.pending || a.playState==='running'),
    focused:[document.hasFocus(),focus?.localName,focus?.id], selection:selection?.isCollapsed
  };
}"""

class Held(ValueError):
    """Record that the evidence is outside the measurement's scope."""


def rgb_pixels(image):
    samples = iter(image.tobytes())
    return zip(samples, samples, samples, strict=True)


def comparable(snapshot):
    return {key: value for key, value in snapshot.items() if key not in {'style', 'fill'}}


def validate_snapshot(snapshot, first, expected_style, expected_fill):
    if not snapshot or snapshot['location'] != first['location']:
        raise Held('target_or_document_changed')
    if snapshot['blocked']:
        raise Held('resource_request_blocked')
    if snapshot['busy'] or snapshot['fonts'] != 'loaded':
        raise Held('active_animation_or_loading_font')
    if not snapshot['usesUniformFontAndFill']:
        raise Held('multiple_glyph_styles')
    if snapshot['style'] != expected_style or snapshot['fill'] != expected_fill:
        raise Held('controlled_fill_not_observed')
    if comparable(snapshot) != comparable(first):
        raise Held('layout_or_state_changed')


def validate_target(first):
    if not first or first['tag'] not in {'p', 'span', 'div', 'label'} or first['childTypes'] != [3]:
        raise Held('requires_one_plain_text_node')
    if len(first['rangeRects']) != 1 or not first['text'].strip():
        raise Held('requires_one_rendered_text_range')
    if first['nonplain'] or first['possibleOverlaps']:
        raise Held('complex_paint_overlap_or_clipping')
    if not first['visible'] or not first['selection'] or not first['focused'][0]:
        raise Held('unsupported_visibility_or_focus')
    if not RGB.fullmatch(first['fill']):
        raise Held('target_fill_is_not_opaque_rgb')
    if not re.fullmatch(r'(?:[1-9][0-9]{0,2}|1000)', first['font'][1]):
        raise Held('requires_plain_font_weight')
    if first['viewport'][2] != 1 or first['viewport'][5:] != [0, 0, 1]:
        raise Held('requires_fixed_dpr1_viewport')
    x, y, width, height = first['rangeRects'][0]
    if min(width, height) <= 0 or min(x, y) < 2 or x + width + 2 > first['viewport'][3] or y + height + 2 > first['viewport'][4]:
        raise Held('range_not_wholly_inside_viewport')


def paint_region(rect):
    x, y, width, height = rect
    return math.floor(x) - 1, math.floor(y) - 1, math.ceil(x + width) + 1, math.ceil(y + height) + 1


def analyze_frames(images, first, viewport):
    from PIL import ImageChops

    actual, transparent, black, white = (images[key] for key in ('original','transparent','black','white'))
    if any(
        image.size != tuple(viewport) or image.mode != 'RGB' or 'icc_profile' in image.info
        for image in images.values()
    ):
        raise Held('image_dimensions_or_alpha_changed')
    for key in ('original-repeat','restored','restored-repeat'):
        if ImageChops.difference(actual, images[key]).getbbox():
            raise Held('original_or_restored_appearance_changed')
    region = paint_region(first['rangeRects'][0])
    for sample in (transparent, black, white):
        bounds = ImageChops.difference(actual, sample).getbbox()
        if bounds and (bounds[0] < region[0] or bounds[1] < region[1] or bounds[2] > region[2] or bounds[3] > region[3]):
            raise Held('paint_changed_outside_target_range')
    source_color = tuple(int(v) for v in RGB.fullmatch(first['fill']).groups())
    bg_colors, fg_colors = Counter(), Counter()
    opaque_count, affected_count = 0, 0
    maximum = 0
    consistent = True
    colors = [rgb_pixels(image.crop(region)) for image in (actual, transparent, black, white)]
    for rendered, background, darkest, lightest in zip(*colors, strict=True):
        if rendered == background == darkest == lightest:
            continue
        affected_count += 1
        coverage = [high - low for low, high in zip(darkest, lightest, strict=True)]
        if min(coverage) <= 0:
            raise Held('non_glyph_or_inverted_reference_change')
        bg_colors[background] += 1
        maximum = max(maximum, min(coverage))
        if min(coverage) == 255:
            fg_colors[rendered] += 1
            opaque_count += 1
        for channel, lo, alpha in zip(rendered, darkest, coverage, strict=True):
            # Glyph antialiasing is color-dependent in Chromium. Require
            # ordering at soft edges and exact values on fully covered pixels.
            if not lo <= channel <= lo + alpha:
                consistent = False
    detail = {'affected_pixels':affected_count,'maximum_reference_separation':maximum,'opaque_pixels':opaque_count,
              'background_count':len(bg_colors),'background_examples':bg_colors.most_common(3),
              'foreground_examples':fg_colors.most_common(3),'reference_channels_ordered':consistent,'paint_region':region}
    if len(bg_colors)!=1:
        return {'status':'hold','reason':'background_not_uniform_or_glyphs_missing', **detail}
    if list(fg_colors) != [source_color]:
        return {'status':'hold','reason':'opaque_foreground_not_observed_or_does_not_match', **detail}
    if not consistent:
        return {'status':'hold','reason':'color_channels_outside_reference_range', **detail}
    background, = bg_colors
    foreground_color = '#%02x%02x%02x' % source_color
    background_color = '#%02x%02x%02x' % background
    ratio = contrast(foreground_color, background_color)['ratio']
    # Use published size thresholds only for the plain CSS size and weight observed.
    size = float(first['font'][0].removesuffix('px'))
    weight = int(first['font'][1])
    threshold = 3 if size >= 24 or (size >= 14*96/72 and weight >= 700) else 4.5
    return {'status':'measured','ratio':ratio,'threshold':threshold,'threshold_met': ratio >= threshold,
            'foreground': foreground_color, 'background': background_color, 'font_css_px': size, 'font_weight': weight, **detail}


async def capture(page, selector, output, result, *, interrupted, crop_frames=False):
    """Capture the seven stages, comparing the whole viewport before storing a cropped copy."""
    from PIL import Image
    from playwright.async_api import Error as BrowserError

    locator = page.locator(selector)
    if await locator.count() != 1:
        raise Held('target_not_unique')
    target = await locator.element_handle(timeout=2500)
    watcher = None
    changed_by_probe = False
    try:
        watcher = await target.evaluate_handle(WATCH_CHANGES)
        first = await target.evaluate(STATE)
        validate_target(first)
        original_style = first['style']
        expected_style = original_style
        frames = {}
        viewport = first['viewport'][:2]
        if viewport[0] * viewport[1] > 4_000_000:
            raise Held('viewport_area_too_large')
        region = paint_region(first['rangeRects'][0])
        result.update(range_css_px=first['rangeRects'][0], viewport_css_px=viewport, scroll_css_px=first['scroll'])
        if crop_frames:
            result['frame_crop_css_px'] = region

        async def check(expected_fill):
            if interrupted():
                raise Held('resource_request_blocked')
            if await watcher.evaluate('w => w.changed || w.takeRecords().length > 0'):
                raise Held('layout_or_state_changed')
            validate_snapshot(await target.evaluate(STATE), first, expected_style, expected_fill)

        for stage, color in CAPTURE_STAGES.items():
            if color is not None or stage == 'restored':
                changed_by_probe = True
                expected_style = await watcher.evaluate('(w, args) => w.write(args)', [FILL, color, original_style])
            expected_fill = color or first['fill']
            await check(expected_fill)
            image_bytes = await page.screenshot(type='png', scale='css', caret='initial', timeout=4000)
            await check(expected_fill)
            with Image.open(BytesIO(image_bytes)) as image:
                if image.format != 'PNG':
                    raise Held('screenshot_is_not_png')
                frames[stage] = image.copy()
            filename = f'{stage}.png'
            if crop_frames:
                buffer = BytesIO()
                frames[stage].crop(region).save(buffer, 'PNG')
                image_bytes = buffer.getvalue()
            (output / filename).write_bytes(image_bytes)
            result['frames'][stage] = {'path': filename, 'sha256': sha256(image_bytes).hexdigest(), 'fill': expected_fill}
        if await locator.count() != 1 or not await locator.evaluate('(element, original) => element === original', target):
            raise Held('target_or_document_changed')
        await check(first['fill'])
        return analyze_frames(frames, first, viewport)
    finally:
        if watcher:
            with suppress(BrowserError):
                await watcher.evaluate('w => w.disconnect()')
                await watcher.dispose()
        with suppress(BrowserError):
            if changed_by_probe and await target.get_attribute('style') != original_style:
                await target.evaluate(RESTORE, original_style)
            await target.dispose()


REASONS = {
    'target_not_unique': '対象を一つに特定できない。',
    'target_or_document_changed': '測定中に対象又は文書が変わった。',
    'resource_request_blocked': '測定中に通信又はページの分岐が発生した。',
    'active_animation_or_loading_font': 'アニメーション又はフォントの読み込みが続いている。',
    'multiple_glyph_styles': '文字列内に表示スタイルの違いがある。',
    'controlled_fill_not_observed': '指定した測定用の文字色が反映されなかった。',
    'layout_or_state_changed': '測定中にページの構造・表示位置・スタイルが変わった。',
    'requires_one_plain_text_node': '要素直下にある1つのテキストノードを対象にする。',
    'requires_one_rendered_text_range': '文字列が画面上の1行に収まる対象を測定する。',
    'complex_paint_overlap_or_clipping': '重なり・切り取り・複雑な色の合成・埋め込みの可能性がある。',
    'unsupported_visibility_or_focus': '文字の表示・選択・ウィンドウの状態を確認できない。',
    'target_fill_is_not_opaque_rgb': '文字色を不透明なRGB値で確認できない。',
    'requires_plain_font_weight': '文字の太さを対応する数値で確認できない。',
    'requires_fixed_dpr1_viewport': '1 CSS pxを1画素に対応付けられない。',
    'range_not_wholly_inside_viewport': '文字列と周辺が表示範囲に収まらない。',
    'viewport_area_too_large': '表示範囲が400万画素を超えている。',
    'image_dimensions_or_alpha_changed': '画像の大きさ・色形式が測定条件と一致しない。',
    'original_or_restored_appearance_changed': '元の描画と復元後、又はそれぞれの再取得画像が一致しない。',
    'paint_changed_outside_target_range': '文字色の変更で対象の外側も変化した。',
    'non_glyph_or_inverted_reference_change': '画素の変化を文字の描画に対応付けられない。',
    'background_not_uniform_or_glyphs_missing': '文字の下にある背景色が単色でそろわないか、文字の画素を確認できない。',
    'opaque_foreground_not_observed_or_does_not_match': '文字の不透明な画素が、計算済みの文字色と一致しない。',
    'color_channels_outside_reference_range': '描画された画素の値が黒と白で比較した範囲に収まらない。',
}


async def observe(page, check, output, interrupted):
    from playwright.async_api import Error as BrowserError

    record = dict(check, frames={}, state='initial')
    if not find_spec('PIL'):
        return dict(record, status='hold', reason='pillow_unavailable',
                    observed='PNGの画素を調べるにはrequirements-analysis.txtのPillowが必要。')
    try:
        if await page.evaluate('() => window.__wcagExplore().closedRoots'):
            raise Held('complex_paint_overlap_or_clipping')
        record.update(await capture(page, check['target'], output, record, interrupted=interrupted, crop_frames=True))
    except Held as problem:
        record.update(status='hold', reason=str(problem))
    except (BrowserError, OSError, ValueError):
        record.update(status='hold', reason='capture_unavailable')
    if record['status'] == 'hold':
        record['observed'] = REASONS.get(record['reason'], 'Chromiumから測定に必要な画像又は対象の状態を取得できない。')
    return record
