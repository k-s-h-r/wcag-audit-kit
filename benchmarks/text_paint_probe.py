"""Measure a specified plain text target in a self-contained static benchmark fixture."""
import argparse
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
from io import BytesIO
import json
import math
from pathlib import Path
import re
import shutil
import sys

from PIL import Image, ImageChops
from playwright.sync_api import Error as BrowserError, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/wcag-audit-kit/scripts'))
from measure import contrast


DOCUMENT_URL = 'https://text-paint-fixture.invalid/source.html'
RESULT_SCOPE = '1.4.3-02 text-paint measurement on the specified static fixture'
POLICY = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; sandbox allow-same-origin"
CAPTURE_STAGES = {
    'original': None, 'original-repeat': None, 'transparent': 'rgba(0, 0, 0, 0)',
    'black': 'rgb(0, 0, 0)', 'white': 'rgb(255, 255, 255)', 'restored': None, 'restored-repeat': None,
}
VIEWPORT = {'width': 1280, 'height': 900}
ALLOWED_ELEMENTS = {
    'html', 'head', 'meta', 'title', 'style', 'body', 'main', 'section', 'article', 'header', 'footer',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span', 'label', 'strong', 'em', 'b', 'i', 'br',
}
FILL = '-webkit-text-fill-color'
RGB = re.compile(r'rgb\((\d+), (\d+), (\d+)\)')
LOAD_OBSERVER = """() => {
    window.__probeViolations = [];
    document.addEventListener('securitypolicyviolation', event => {
        window.__probeViolations.push(event.violatedDirective);
    });
}"""
CHANGE = "(e, [property, value]) => e.style.setProperty(property, value, 'important')"
RESTORE = """(e, value) => {
    if (value === null) e.removeAttribute('style');
    else e.setAttribute('style', value);
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
  if (document.fullscreenElement || document.querySelector(':modal,:popover-open'))
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
    font:[s.fontSize,s.fontWeight], fonts:document.fonts.status, blocked:window.__probeViolations.length,
    busy:document.getAnimations().some(a => a.pending || a.playState==='running'),
    focused:[document.hasFocus(),focus?.localName,focus?.id], selection:selection?.isCollapsed
  };
}"""

class Held(ValueError):
    """Record that the evidence is outside the measurement's scope."""


class StaticFixture(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_ELEMENTS or any(name.startswith('on') or name == 'http-equiv' for name, _ in attrs):
            raise Held('requires_self_contained_static_text_html')


def rgb_pixels(image):
    samples = iter(image.tobytes())
    return zip(samples, samples, samples, strict=True)


def comparable(snapshot):
    return {key: value for key, value in snapshot.items() if key not in {'style', 'fill'}}


def validate_snapshot(snapshot, first, expected_style, expected_fill):
    if not snapshot or snapshot['location'] != DOCUMENT_URL:
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


def analyze_frames(images, first):
    actual, transparent, black, white = (images[key] for key in ('original','transparent','black','white'))
    if any(
        image.size != (VIEWPORT['width'], VIEWPORT['height']) or image.mode != 'RGB' or 'icc_profile' in image.info
        for image in images.values()
    ):
        raise Held('image_dimensions_or_alpha_changed')
    for key in ('original-repeat','restored','restored-repeat'):
        if ImageChops.difference(actual, images[key]).getbbox():
            raise Held('original_or_restored_appearance_changed')
    x, y, width, height = first['rangeRects'][0]
    region = (math.floor(x) - 1, math.floor(y) - 1, math.ceil(x + width) + 1, math.ceil(y + height) + 1)
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



def capture(page, selector, output, result):
    locator = page.locator(selector)
    if locator.count() != 1:
        raise Held('target_not_unique')
    target = locator.element_handle(timeout=2500)
    first = target.evaluate(STATE)
    validate_target(first)
    expected_style = first['style']
    original_style = first['style']
    images = {}
    result['range_css_px'] = first['rangeRects'][0]
    result['viewport_css_px'] = first['viewport'][:2]
    result['scroll_css_px'] = first['scroll']
    try:
        for stage, color in CAPTURE_STAGES.items():
            if color is not None:
                target.evaluate(CHANGE, [FILL, color])
                expected_style = target.get_attribute('style')
            elif stage == 'restored':
                target.evaluate(RESTORE, original_style)
                expected_style = original_style
            expected_fill = color or first['fill']
            validate_snapshot(target.evaluate(STATE), first, expected_style, expected_fill)
            data = page.screenshot(type='png', scale='css', caret='initial', timeout=4000)
            validate_snapshot(target.evaluate(STATE), first, expected_style, expected_fill)
            with Image.open(BytesIO(data)) as image:
                if image.format != 'PNG':
                    raise Held('screenshot_is_not_png')
                images[stage] = image.copy()
            filename = f'{stage}.png'
            (output / filename).write_bytes(data)
            result['frames'][stage] = {'path': filename, 'sha256': sha256(data).hexdigest(), 'fill': expected_fill}
        return analyze_frames(images, first)
    finally:
        # Changes only affect this disposable browser document.
        if expected_style != original_style:
            target.evaluate(RESTORE, original_style)


def probe(source, selector, output, max_images):
    raw = source.read_bytes()
    result = {
        'source': source.name, 'source_sha256': sha256(raw).hexdigest(), 'target': selector, 'frames': {},
        'image_limit': max_images, 'blocked_requests': [],
        'scope': RESULT_SCOPE,
    }
    output.mkdir(exist_ok=False)
    try:
        if max_images < len(CAPTURE_STAGES):
            raise Held('image_budget_below_seven')
        try:
            validator = StaticFixture()
            validator.feed(raw.decode('utf-8-sig'))
            validator.close()
        except UnicodeDecodeError as error:
            raise Held('requires_utf8_html') from error
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=shutil.which('chromium'), args=[
                '--disable-background-networking', '--disable-component-update', '--force-color-profile=srgb',
            ])
            result['browser'] = browser.version
            context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1, locale='ja-JP', service_workers='block',
                                          accept_downloads=False)
            page = context.new_page()
            served = False
            blocked = []

            def route_fixture(route):
                nonlocal served
                request = route.request
                if (not served and request.url == DOCUMENT_URL and request.method == 'GET'
                        and request.is_navigation_request() and request.frame == page.main_frame):
                    served = True
                    route.fulfill(status=200, headers={
                        'content-type': 'text/html; charset=utf-8',
                        'content-security-policy': POLICY,
                    }, body=raw)
                else:
                    blocked.append(request.resource_type)
                    route.abort()

            context.route('**/*', route_fixture)
            context.route_web_socket('**/*', lambda websocket: websocket.close())
            page.add_init_script(f'({LOAD_OBSERVER})()')
            try:
                page.goto(DOCUMENT_URL, wait_until='load', timeout=5000)
                measurement = capture(page, selector, output, result)
                if blocked:
                    raise Held('resource_request_blocked')
                result.update(measurement)
            finally:
                result['blocked_requests'] = blocked
                browser.close()
    except Held as error:
        result.update(status='hold', reason=str(error))
    except BrowserError:
        result.update(status='hold', reason='chromium_session_or_target_unavailable')
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', required=True, type=Path, help='self-contained static UTF-8 fixture')
    parser.add_argument('--target', required=True, help='selector matching one direct text element')
    parser.add_argument('--out', required=True, type=Path, help='new evidence directory')
    parser.add_argument('--max-images', type=int, default=len(CAPTURE_STAGES))
    args = parser.parse_args()
    if not args.html.is_file() or args.html.suffix.lower() not in {'.html', '.htm'}:
        parser.error('--html must name an existing local HTML file')
    if args.out.exists() or not args.out.parent.is_dir():
        parser.error('--out must name a new directory with an existing parent')
    if not args.target.strip() or args.max_images < 0:
        parser.error('--target must not be empty and --max-images must be nonnegative')
    print(json.dumps(probe(args.html, args.target, args.out, args.max_images), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
