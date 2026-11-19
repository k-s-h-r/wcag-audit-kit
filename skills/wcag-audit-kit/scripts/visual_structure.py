"""Collect 1.3.1 review candidates from a declared region in Chromium."""
import asyncio
import json
from pathlib import Path
import re


EVIDENCE_FILE = 'visual-structure.json'
CHECKPOINT = '1.3.1-02'


def validate_scope(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('visual_structure_scopeには対象範囲のCSSセレクターを指定する。')
    return value


PARAGRAPHS = r"""
(selector) => {
    const scopes = document.querySelectorAll(selector);
    if (scopes.length !== 1) throw new Error('対象範囲を一つに絞れない。');
    const root = scopes[0];
    if (root.children.length > 250) throw new Error('対象範囲の直下を250要素以内に絞る。');

    function path(element) {
        if (element.id) {
            const id = '#' + CSS.escape(element.id);
            if (document.querySelectorAll(id).length === 1) return id;
        }
        const parts = [];
        for (let node = element; node.parentElement; node = node.parentElement) {
            const pos = Array.prototype.indexOf.call(node.parentElement.children, node) + 1;
            parts.unshift(':nth-child(' + pos + ')');
        }
        return ':root > ' + parts.join(' > ');
    }

    // Require compatible text styles and a visible midpoint inside the viewport.
    // This records candidate geometry, without interpreting paint or meaning.
    function paragraph(element) {
        if (element.localName !== 'p' || element.querySelector('a, button, input, select, textarea, img, svg, br')) {
            return null;
        }
        if (element.textContent.length > 2000) return null;
        const style = getComputedStyle(element);
        if (style.display !== 'block' || !element.checkVisibility({opacityProperty: true, visibilityProperty: true})) {
            return null;
        }
        for (const pseudo of ['::before', '::after']) {
            const generated = getComputedStyle(element, pseudo).content;
            if (!['none', 'normal'].includes(generated)) return null;
        }
        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
        const text = [];
        const rects = [];
        let font;
        for (let node = walker.nextNode(); node; node = walker.nextNode()) {
            if (!node.data.trim()) continue;
            const nodeStyle = getComputedStyle(node.parentElement);
            const signature = [nodeStyle.fontFamily, parseFloat(nodeStyle.fontSize), parseFloat(nodeStyle.fontWeight),
                parseFloat(nodeStyle.lineHeight) || parseFloat(nodeStyle.fontSize) * 1.3];
            const range = document.createRange();
            range.selectNodeContents(node);
            const areas = Array.from(range.getClientRects());
            if (font && JSON.stringify(signature) !== JSON.stringify(font)) return null;
            if (nodeStyle.visibility !== 'visible' || !areas.length || rects.length + areas.length > 32) return null;
            font = signature;
            text.push(node.data);
            rects.push(...areas);
        }
        if (!font) return null;
        const [left, top, right, bottom] = [
            Math.min(...rects.map(rect => rect.left)), Math.min(...rects.map(rect => rect.top)),
            Math.max(...rects.map(rect => rect.right)), Math.max(...rects.map(rect => rect.bottom)),
        ];
        if (left < 0 || top < 0 || right > document.documentElement.clientWidth ||
                bottom > document.documentElement.clientHeight || right <= left || bottom <= top ||
                !element.contains(document.elementFromPoint((left + right) / 2, (top + bottom) / 2))) return null;
        return {
            selector: path(element), text: text.join('').replace(/\s+/g, ' ').trim().slice(0, 200),
            rect: {left, top, right, bottom}, font,
            authored_role: element.getAttribute('role'), aria_hidden: element.getAttribute('aria-hidden'),
            single_line: rects.every(rect => Math.abs(rect.top - top) < 2),
        };
    }

    const scopeContext = [];
    for (let node = root; node; node = node.parentElement) {
        scopeContext.push([node.localName, node.getAttribute('role'), node.getAttribute('aria-hidden')]);
    }
    return {paragraphs: Array.from(root.children, paragraph), url: location.href,
        document_start: performance.timeOrigin, scopeContext,
        viewport: {width: document.documentElement.clientWidth, height: document.documentElement.clientHeight}};
}
"""
BULLET = re.compile(r'^([・•])\s*\S{2}')


def heading_pairs(paragraphs):
    for title, body in zip(paragraphs, paragraphs[1:]):
        if title is None or body is None:
            continue
        _, title_size, title_weight, title_line_height = title['font']
        _, body_size, body_weight, _ = body['font']
        gap = body['rect']['top'] - title['rect']['bottom']
        if (title['single_line'] and 3 <= len(title['text']) <= 50 and len(body['text']) >= 24
                and not BULLET.match(title['text']) and not BULLET.match(body['text'])
                and title_size >= 1.2 * body_size and title_weight >= body_weight + 150
                and abs(title['rect']['left'] - body['rect']['left']) <= 3 and 0 <= gap <= 2 * title_line_height):
            yield title, body


def bullet_runs(paragraphs):
    run = []
    marker = ''
    for paragraph in [*paragraphs, None]:
        bullet = BULLET.match(paragraph['text']) if paragraph and paragraph['single_line'] else None
        current_marker = bullet[1] if bullet else ''
        previous = run[-1] if run else None
        same_run = (previous is not None and current_marker == marker and paragraph['font'] == previous['font']
                    and abs(paragraph['rect']['left'] - previous['rect']['left']) <= 3
                    and 0 <= paragraph['rect']['top'] - previous['rect']['bottom'] <= 2 * previous['font'][3])
        if same_run:
            run.append(paragraph)
            continue
        if len(run) >= 3:
            yield marker, run
        run = [paragraph] if bullet else []
        marker = current_marker


async def accessible_semantics(session, root, selector):
    found = await session.send('DOM.querySelector', {'nodeId': root, 'selector': selector})
    if not found['nodeId']:
        return {'role': None, 'ignored': None, 'inside_list': None}
    tree = await session.send('Accessibility.getPartialAXTree', {'nodeId': found['nodeId']})
    node, *relatives = tree['nodes']
    by_id = {n['nodeId']: n for n in relatives}
    role = node.get('role', {}).get('value')
    parent = by_id.get(node.get('parentId'))
    while parent is not None and parent.get('role', {}).get('value') != 'list':
        parent = by_id.get(parent.get('parentId'))
    return {'role': role, 'ignored': node['ignored'], 'inside_list': parent is not None}


async def collect(page, scope_selector):
    """Suggest visible paragraph structures for review without assigning a verdict."""
    validate_scope(scope_selector)
    snapshot = await page.evaluate(PARAGRAPHS, scope_selector)
    candidates = []
    session = await page.context.new_cdp_session(page)
    try:
        root = (await session.send('DOM.getDocument', {'depth': 0}))['root']['nodeId']
        for title, body in heading_pairs(snapshot['paragraphs']):
            semantics = await accessible_semantics(session, root, title['selector'])
            if semantics['role'] != 'heading' or semantics['ignored']:
                candidates.append({'kind': 'heading', 'target': title, 'following_paragraph': body['selector'],
                                   'accessibility': semantics})
        for marker, run in bullet_runs(snapshot['paragraphs']):
            semantics = [await accessible_semantics(session, root, paragraph['selector']) for paragraph in run]
            if not all(s['role'] == 'listitem' and s['inside_list'] and not s['ignored'] for s in semantics):
                candidates.append({'kind': 'list', 'marker': marker, 'targets': run, 'accessibility': semantics})
    finally:
        await session.detach()
    if snapshot != await page.evaluate(PARAGRAPHS, scope_selector):
        raise ValueError('候補とアクセシビリティ情報の取得中にページ又は対象範囲が変わった。')
    return {'scope': scope_selector, 'url': snapshot['url'], 'viewport': snapshot['viewport'],
            'candidates': candidates}


def not_observed(scope, reason):
    return {'scope': scope, 'status': 'not_observed', 'reason': reason, 'candidates': []}


async def observe(page, scope):
    from playwright.async_api import Error as PlaywrightError

    try:
        result = await asyncio.wait_for(collect(page, scope), timeout=5)
    except TimeoutError:
        return not_observed(scope, '対象範囲の観察が5秒以内に完了しなかった。')
    except (PlaywrightError, ValueError) as error:
        return not_observed(scope, str(error).partition('\n')[0] or '対象範囲を観察できなかった。')
    return dict(result, status='collected')


def report_evidence(run, graph):
    """Read candidate observations attached to initial captures in a verified graph."""
    run = Path(run)
    proof = {item['path'] for item in graph.get('proof', [])}
    observed = []
    for node in graph.get('nodes', []):
        if node['route']:
            continue
        path = Path(node['evidence_dir']) / EVIDENCE_FILE
        if path.as_posix() not in proof:
            continue
        value = json.loads((run / path).read_text())
        observed.append(dict(value, criterion='1.3.1', checkpoint=CHECKPOINT, capture=node['capture'],
                             environment=node['environment'], evidence=path.as_posix()))
    return observed
