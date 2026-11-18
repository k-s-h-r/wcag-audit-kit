"""Measure one focused component in a bounded set of ordinary CSS layouts."""

OBSERVE = r"""
(target) => {
    const box = ({left, top, right, bottom}) => ({left, top, right, bottom});
    const rect = element => box(element.getBoundingClientRect());
    const contains = (outer, inner) => outer.left <= inner.left && outer.top <= inner.top
        && outer.right >= inner.right && outer.bottom >= inner.bottom;
    const includes = (area, x, y) => area.left < x && x < area.right && area.top < y && y < area.bottom;
    const nonempty = area => area.left < area.right && area.top < area.bottom;
    const label = element => ({tag: element.localName, id: element.id});
    const squareCorners = style => ['TopLeft', 'TopRight', 'BottomLeft', 'BottomRight']
        .every(corner => style['border' + corner + 'Radius'] === '0px');
    const generated = element => ['::before', '::after'].some(pseudo => {
        const style = getComputedStyle(element, pseudo);
        return style.content !== 'none' && style.content !== 'normal' && style.display !== 'none';
    });
    const css = new Map();
    const computed = element => {
        if (!css.has(element)) css.set(element, getComputedStyle(element));
        return css.get(element);
    };
    const result = {target: label(target), rect: rect(target), samples: []};
    const finish = (status, extra = {}) => ({...result, status, ...extra});

    if (window !== window.top || target.getRootNode() !== document || !(target instanceof HTMLElement)
            || target.shadowRoot || target.localName.includes('-')
            || ['iframe', 'frame', 'object', 'embed', 'video', 'canvas'].includes(target.localName)) {
        return finish('unsupported_target');
    }
    if (!document.hasFocus() || document.activeElement !== target) return finish('focus_unconfirmed');
    const viewport = window.visualViewport;
    if (!viewport || viewport.scale !== 1 || viewport.offsetTop !== 0 || viewport.offsetLeft !== 0) {
        return finish('viewport_unconfirmed');
    }
    result.viewport = {
        left: 0, top: 0,
        right: Math.min(viewport.width, document.documentElement.clientWidth),
        bottom: Math.min(viewport.height, document.documentElement.clientHeight),
    };
    if (!nonempty(result.rect) || !contains(result.viewport, result.rect) || target.getClientRects().length !== 1) {
        return finish('geometry_unconfirmed');
    }

    function simplePaint(element, area) {
        for (let ancestor = element; ancestor; ancestor = ancestor.parentElement) {
            const style = computed(ancestor);
            if (style.visibility !== 'visible' || style.opacity !== '1'
                    || style.clip !== 'auto' || style.clipPath !== 'none' || style.maskImage !== 'none'
                    || style.filter !== 'none' || style.backdropFilter !== 'none'
                    || style.transform !== 'none' || style.translate !== 'none'
                    || style.rotate !== 'none' || style.scale !== 'none'
                    || style.perspective !== 'none' || style.mixBlendMode !== 'normal'
                    || style.contentVisibility !== 'visible' || style.contain !== 'none'
                    || style.zoom !== '1') return false;
            if (ancestor !== element && ancestor !== document.documentElement
                    && (style.overflowX !== 'visible' || style.overflowY !== 'visible')) {
                const outer = rect(ancestor);
                const left = outer.left + ancestor.clientLeft;
                const top = outer.top + ancestor.clientTop;
                const clip = {left, top, right: left + ancestor.clientWidth, bottom: top + ancestor.clientHeight};
                if (!squareCorners(style) || !contains(clip, area)) return false;
            }
        }
        return Boolean(element.checkVisibility?.({opacityProperty: true, visibilityProperty: true}));
    }

    // Use only the inner rectangle where a solid background can be established
    // without relying on a border, antialiasing, or a pointer hit to imply paint.
    function solidCore(element) {
        const style = computed(element);
        if (!(element instanceof HTMLElement) || element.getClientRects().length !== 1
                || !/^rgb\(\d+, \d+, \d+\)$/.test(style.backgroundColor) || style.backgroundImage !== 'none'
                || style.borderImageSource !== 'none'
                || !['border-box', 'padding-box', 'content-box'].includes(style.backgroundClip)
                || !squareCorners(style)) return null;
        const inset = side => parseFloat(style['border' + side + 'Width']) +
            (style.backgroundClip === 'content-box' ? parseFloat(style['padding' + side]) : 0);
        const area = rect(element);
        const core = {
            left: area.left + inset('Left'), top: area.top + inset('Top'),
            right: area.right - inset('Right'), bottom: area.bottom - inset('Bottom'),
        };
        return nonempty(core) && simplePaint(element, core) ? core : null;
    }

    if (!simplePaint(target, result.rect)) return finish('target_paint_unconfirmed');
    const documentElements = document.getElementsByTagName('*');
    if (documentElements.length > 2000 || document.getAnimations().some(item => item.playState === 'running')) {
        return finish('insufficient_paint_evidence');
    }
    const openSelect = CSS.supports('selector(select:open)') && document.querySelector('select:open');
    if (document.querySelector(':modal, :popover-open, :fullscreen') || openSelect) {
        return finish('top_layer_unconfirmed');
    }

    const ratios = [1 / 6, 1 / 2, 5 / 6];
    const width = result.rect.right - result.rect.left, height = result.rect.bottom - result.rect.top;
    const points = ratios.flatMap(across => ratios.map(down => {
        const x = result.rect.left + width * across, y = result.rect.top + height * down;
        const stack = document.elementsFromPoint(x, y);
        const targetIndex = stack.findIndex(element => target.contains(element));
        const ahead = targetIndex >= 0 ? stack.slice(0, targetIndex) : [];
        result.samples.push({x, y, targetHit: targetIndex >= 0,
            top: stack.slice(0, 5).map(label)});
        return {x, y, ahead, targetFirst: targetIndex === 0};
    }));

    // Fail only for one demonstrably opaque, positioned rectangle that covers
    // the entire measured component. The samples establish order, not coverage.
    // Complex descendants or overflowing target content need a separate review.
    const targetStyle = computed(target);
    const textRange = document.createRange();
    textRange.selectNodeContents(target);
    const textContained = Array.from(textRange.getClientRects()).every(area => contains(result.rect, area));
    if (!target.childElementCount && textContained && !generated(target) && targetStyle.boxShadow === 'none'
            && targetStyle.textShadow === 'none' && !targetStyle.textDecorationLine.includes('underline')) {
        for (const element of points[0].ahead) {
            const style = computed(element);
            if (element.contains(target) || !['fixed', 'sticky', 'absolute'].includes(style.position)
                    || !points.every(point => point.ahead.includes(element))) continue;
            const cover = solidCore(element);
            if (cover && contains(cover, result.rect)) {
                return finish('entirely_covered', {overlay: {
                    ...label(element), rect: rect(element), solidCore: cover,
                    position: style.position, background: style.backgroundColor,
                }});
            }
        }
    }

    const targetCore = solidCore(target);
    const clearPoints = targetCore && points.filter(point =>
        point.targetFirst && includes(targetCore, point.x, point.y));
    if (!clearPoints?.length) return finish('insufficient_paint_evidence');

    // Top of hit-testing omits paint with pointer-events:none and paint that
    // extends outside its hit box. Leave those ambiguous unless the point
    // falls outside the possible painted area.
    const hitExclusions = [];
    for (const element of documentElements) {
        if (target.contains(element)) continue;
        const style = computed(element);
        if (style.display === 'none' || style.visibility !== 'visible' || style.opacity === '0') continue;
        const borderPaintOutside = style.borderImageSource !== 'none'
            && style.borderImageOutset.split(/\s+/).some(value => parseFloat(value) > 0);
        if (generated(element) || style.boxShadow !== 'none' || style.textShadow !== 'none'
                || style.filter !== 'none' || style.backdropFilter !== 'none' || borderPaintOutside) {
            return finish('paint_outside_hit_test', {unmeasured: label(element)});
        }
        if (!element.getClientRects().length) continue;
        if (style.pointerEvents === 'none' || element.shadowRoot || element.localName.includes('-')
                || !(element instanceof HTMLElement) || style.outlineStyle !== 'none') {
            const area = rect(element);
            const outline = style.outlineStyle === 'none' ? 0 :
                Math.max(0, parseFloat(style.outlineWidth) + parseFloat(style.outlineOffset));
            hitExclusions.push({element: label(element), area: {
                left: area.left - outline, right: area.right + outline,
                top: area.top - outline, bottom: area.bottom + outline,
            }});
        }
    }
    const atPoint = ({x, y}) => hitExclusions.filter(entry => includes(entry.area, x, y));
    const exposed = clearPoints.find(point => !atPoint(point).length);
    if (exposed) return finish('partly_visible', {exposed: {x: exposed.x, y: exposed.y}, targetCore});
    return finish('paint_outside_hit_test', {unmeasured: atPoint(clearPoints[0]).map(entry => entry.element)});
}
"""

OUTCOMES = {
    'entirely_covered': ('failed', '前面にある不透明な要素が、このフォーカス部品の矩形全体を覆った。'),
    'partly_visible': ('passed', 'このフォーカス部品の一部が、前面に表示されていることを確認した。'),
    'unsupported_target': ('cant_tell', '主文書の通常のDOMにある部品を対象に測定する。'),
    'focus_unconfirmed': ('cant_tell', '測定時に対象へのフォーカスを確認できない。'),
    'viewport_unconfirmed': ('cant_tell', 'この表示領域の座標で測定できない。'),
    'geometry_unconfirmed': ('cant_tell', '表示領域内で対象の矩形全体を確認できない。'),
    'target_paint_unconfirmed': ('cant_tell', '部品の表示条件、変形、又は祖先による切り取りを判定できない。'),
    'top_layer_unconfirmed': ('cant_tell', 'ブラウザーの最前面レイヤーを含む状態のため、重なりの判定を保留した。'),
    'paint_outside_hit_test': ('cant_tell', 'ポインターの当たり判定に現れない描画があり、前後関係を確定できない。'),
    'insufficient_paint_evidence': ('cant_tell', '部品の表示又は不透明な要素による全体の覆いを確定できない。'),
}


async def observe(scope, selector):
    """Observe component occlusion after the caller has verified real key input."""
    locator = scope.locator(selector)
    if await locator.count() != 1:
        return {'outcome': 'cant_tell', 'observed': 'フォーカス部品の対象を一つに絞れない。', 'selector': selector}
    measured = await locator.evaluate(OBSERVE, timeout=2500)
    outcome, observed = OUTCOMES[measured['status']]
    if covered_by := measured.get('overlay'):
        label = '#' + covered_by['id'] if covered_by['id'] else covered_by['tag']
        observed += f'覆っている要素は {label}。'
    return {'outcome': outcome, 'observed': observed, 'selector': selector, **measured}
