"""Observe rectangular pointer targets in a narrowly scoped initial page state."""
import math

from measure import spacing


EVIDENCE_FILE = 'target-spacing.json'
CHECKPOINT = 'ポインター対象の寸法と間隔'
CRITERION = '2.5.8'
COORDINATES = ('x', 'y', 'width', 'height')

TARGET_RECTS = r"""(selectors, recordPoints = false) => {
    const viewport = document.documentElement;
    const candidates = 'a[href],button,select,textarea,input:not([type="hidden"]),summary,'
        + '[role="button"],[role="link"],[role="checkbox"],[role="radio"],[role="switch"],'
        + '[role="tab"],[role="menuitem"],[role="option"],[role="slider"],[role="combobox"],'
        + '[onclick],[onmousedown],[onpointerdown]';
    const selected = selectors.map(selector => Array.from(document.querySelectorAll(selector)));
    const nodes = Array.from(document.querySelectorAll(candidates));
    for (const matches of selected)
        if (matches.length === 1 && !nodes.includes(matches[0])) nodes.push(matches[0]);
    if (nodes.length > 100 || document.querySelector('script,iframe,frame,object,embed,canvas,video,audio')
            || Array.from(document.getElementsByTagName('*')).some(node => node.shadowRoot))
        return {reason: '静的な主文書の操作対象を列挙できない。'};

    function inlineText(node, box, style) {
        if (!node.matches('a[href]') || style.display !== 'inline' || !node.parentElement?.matches('p'))
            return false;
        return [node.previousSibling, node.nextSibling].every(text => {
            if (text?.nodeType !== Node.TEXT_NODE || !text.textContent.trim()) return false;
            const range = document.createRange();
            range.selectNodeContents(text);
            return Array.from(range.getClientRects()).some(rect =>
                rect.width > 0 && rect.top < box.bottom && rect.bottom > box.top);
        });
    }

    function untransformed(node) {
        for (let ancestor = node; ancestor; ancestor = ancestor.parentElement) {
            const style = getComputedStyle(ancestor);
            if (style.transform !== 'none' || style.translate !== 'none' || style.rotate !== 'none'
                    || style.scale !== 'none' || style.zoom !== '1') return false;
        }
        return true;
    }

    const items = [];
    let unresolved = false;
    for (const [index, node] of nodes.entries()) {
        if (node.matches(':disabled') || !node.checkVisibility?.({opacityProperty: true, visibilityProperty: true}))
            continue;
        const style = getComputedStyle(node);
        if (style.pointerEvents === 'none') continue;
        const rects = node.getClientRects();
        const box = node.getBoundingClientRect();
        if (box.width <= 0 || box.height <= 0) continue;
        const selectorIndex = selected.findIndex(matches => matches.length === 1 && matches[0] === node);
        const id = selectorIndex >= 0 ? selectors[selectorIndex] : 'nearby-' + index;
        const tags = 'a[href],button';
        const simple = node.matches(tags) && !node.children.length && rects.length === 1
            && style.clipPath === 'none' && style.maskImage === 'none'
            && style.borderRadius === '0px' && box.left >= 0 && box.top >= 0
            && box.right <= viewport.clientWidth && box.bottom <= viewport.clientHeight;
        // Chromium snaps hit-test coordinates. Sample one CSS pixel inside each edge.
        const x = [box.left + 1, (box.left + box.right) / 2, box.right - 1];
        const y = [box.top + 1, (box.top + box.bottom) / 2, box.bottom - 1];
        const points = x.flatMap(h => y.map(v => [h, v]));
        const supported = simple && box.width > 2 && box.height > 2 && untransformed(node)
            && points.every(([h, v]) => document.elementFromPoint(h, v) === node);
        if (!supported) {
            unresolved = true;
            continue;
        }
        items.push({id, x:box.left, y:box.top, width:box.width, height:box.height,
            inline_text: inlineText(node, box, style),
            explicit_size: node.matches('button') && !!node.style.width && !!node.style.height,
            ...(recordPoints ? {hit_points: points} : {})});
    }
    return {items, unresolved};
}"""

INITIAL_PAIR = r"""selectors => {
    const inspect = """ + TARGET_RECTS + r""";
    const buttons = Array.from(document.querySelectorAll('button'));
    const elements = Array.from(document.querySelectorAll('*'));
    if (buttons.length !== 2 || buttons[0].parentElement !== buttons[1].parentElement
            || buttons.some(node => node.form || node.hasAttribute('role')) || document.getAnimations().length
            || document.querySelector('meta[http-equiv="refresh" i],label,svg,math,[contenteditable],[tabindex],'
                + '[usemap],[popover],[popovertarget],[commandfor]')
            || elements.length > 300 || elements.some(node => node.getAttributeNames().some(name => name.startsWith('on'))))
        return null;

    const ancestors = new Set(buttons);
    for (let node = buttons[0].parentElement; node; node = node.parentElement) ancestors.add(node);
    for (const node of ancestors) {
        const style = getComputedStyle(node);
        if (style.overflowX !== 'visible' || style.overflowY !== 'visible' || style.clip !== 'auto'
                || style.clipPath !== 'none' || style.maskImage !== 'none' || style.contain !== 'none') return null;
    }

    const bounds = buttons.map(node => node.getBoundingClientRect());
    const overlaps = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
    for (const node of elements) {
        if (['::before', '::after'].some(pseudo => !['none', 'normal'].includes(getComputedStyle(node, pseudo).content)))
            return null;
        if (ancestors.has(node) || !node.checkVisibility?.({visibilityProperty: true})
                || getComputedStyle(node).pointerEvents === 'none') continue;
        if (Array.from(node.getClientRects()).some(box => box.width > 0 && box.height > 0
                && bounds.some(button => overlaps(box, button)))) return null;
    }

    const evidence = inspect(selectors, true);
    if (evidence.items?.length !== 2 || !evidence.items.every(item => {
        const button = document.querySelector(item.id);
        const pixels = /^\d+(?:\.\d+)?px$/;
        return button && ['width', 'height'].every(key => pixels.test(button.style[key])
            && parseFloat(button.style[key]) === item[key]);
    })) return null;
    return {url:location.href, ...evidence};
}"""


def rect_is_valid(rect):
    return (isinstance(rect, dict) and isinstance(rect.get('id'), str)
            and all(type(rect.get(key)) in {float, int} and math.isfinite(rect[key]) for key in COORDINATES)
            and rect['width'] > 0 and rect['height'] > 0)


def aligned_gap(first, second):
    """Return the edge gap and orientation for distinct aligned rectangles."""
    for axis, span, cross, cross_span in (
        ('x', 'width', 'y', 'height'), ('y', 'height', 'x', 'width'),
    ):
        if first[cross] != second[cross] or first[cross_span] != second[cross_span]:
            continue
        start, end = sorted((first, second), key=lambda rect: rect[axis])
        gap = end[axis] - (start[axis] + start[span])
        if gap >= 0:
            return gap, '水平' if axis == 'x' else '垂直'
    return None

def spacing_conflicts(items, rect):
    result = next(row for row in spacing(items)['targets'] if row['id'] == rect['id'])
    conflicts = set(result['conflicts'])
    center_x = rect['x'] + rect['width'] / 2
    center_y = rect['y'] + rect['height'] / 2
    for other in items:
        if other['id'] == rect['id']:
            continue
        # A circle may hit a long undersized rectangle without hitting its circle.
        nearest_x = min(max(center_x, other['x']), other['x'] + other['width'])
        nearest_y = min(max(center_y, other['y']), other['y'] + other['height'])
        if math.hypot(center_x - nearest_x, center_y - nearest_y) < 12:
            conflicts.add(other['id'])
    return sorted(conflicts)


def hit_points(rect):
    x, y, width, height = (rect[key] for key in COORDINATES)
    return [[h, v] for h in (x + 1, x + width / 2, x + width - 1)
            for v in (y + 1, y + height / 2, y + height - 1)]


def initial_rectangles(state):
    controls = state.get('controls')
    if (isinstance(controls, list) and len(controls) == 2 and all(control.get('tag') == 'button'
            and control.get('formAssociated') is False and control.get('events') == [] for control in controls)):
        return {control['selector']: control['rect'] for control in controls}
    return {}


def verified_pair(record, state):
    if (not isinstance(record, dict) or record.get('unresolved') is not False
            or not record.get('url') or record['url'] != state.get('url')):
        return None
    items = record.get('items')
    if (not isinstance(items, list) or len(items) != 2 or any(not rect_is_valid(item)
            or item.get('explicit_size') is not True or min(item['width'], item['height']) <= 2
            or item.get('hit_points') != hit_points(item) for item in items)):
        return None
    expected = initial_rectangles(state)
    observed = {item['id']: {key: item[key] for key in COORDINATES} for item in items}
    if len(expected) == 2 and expected == observed and aligned_gap(*items) is not None:
        return items
    return None


async def observe(page, state, environment):
    targets = initial_rectangles(state)
    if len(targets) != 2:
        return None
    record = await page.evaluate(INITIAL_PAIR, list(targets))
    if verified_pair(record, state):
        return dict(record, environment=environment)
    return None


def report_rows(record, state, capture, evidence, state_path):
    items = verified_pair(record, state)
    if (not items or record.get('environment') != capture['environment']
            or record['url'] != capture.get('final_url')):
        return
    gap, direction = aligned_gap(*items)
    for rect in items:
        dimensions = f'{rect["width"]:g} × {rect["height"]:g} CSS px。{direction}の辺間隔は {gap:g} CSS px。'
        if min(rect['width'], rect['height']) >= 24:
            outcome, observed = 'passed', dimensions + '測定した対象は24 × 24 CSS px以上。'
        elif spacing_conflicts(items, rect):
            outcome = 'failed'
            observed = dimensions + '対象の中央に置いた直径24 CSS pxの円は、隣接対象又はその円と重なる。'
        else:
            outcome = 'passed'
            observed = dimensions + '対象の中央に置いた直径24 CSS pxの円は、隣接対象やその円と重ならない。'
        yield dict(criterion=CRITERION, checkpoint=CHECKPOINT, target=rect['id'], outcome=outcome,
                   expected='測定した対象の寸法又は間隔が2.5.8の該当条件を満たす。', observed=observed,
                   environment=capture['environment'], capture=capture['key'], state_label='初期表示',
                   page_url=capture['url'], evidence=evidence, proof=[state_path], source='',
                   note='静的なネイティブボタン2個の初期表示で、内側9点の当たり判定、寸法と間隔を測定。ほかの例外と達成基準全体は別に確認する。')
