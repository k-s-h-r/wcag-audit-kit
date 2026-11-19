"""Collect 1.3.1 review candidates from a declared region in Chromium."""
import asyncio
import json
from pathlib import Path
import re


EVIDENCE_FILE = 'visual-structure.json'
CHECKPOINT = '1.3.1-02'
OBSERVATION_SECONDS = 5
REPORT_TITLE = '見出し・リストの確認候補'
REPORT_COLUMNS = (
    ('criterion', '達成基準'), ('environment', '環境'), ('state', '表示状態・操作'),
    ('scope', '指定範囲'),
    ('status', '観察結果'), ('target', '対象要素'), ('observed', '表示された文言・理由'),
    ('evidence', '元の証拠'),
)


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

    function fontSignature(style) {
        const size = parseFloat(style.fontSize);
        return [style.fontFamily, size, parseFloat(style.fontWeight), parseFloat(style.lineHeight) || size * 1.3];
    }

    // Record text geometry with a visible midpoint inside the viewport.
    function textGeometry(element, text, rects, font, selector) {
        if (!rects.length || rects.length > 32) return null;
        const [left, top, right, bottom] = [
            Math.min(...rects.map(rect => rect.left)), Math.min(...rects.map(rect => rect.top)),
            Math.max(...rects.map(rect => rect.right)), Math.max(...rects.map(rect => rect.bottom)),
        ];
        if (left < 0 || top < 0 || right > document.documentElement.clientWidth ||
                bottom > document.documentElement.clientHeight || right <= left || bottom <= top ||
                !element.contains(document.elementFromPoint((left + right) / 2, (top + bottom) / 2))) return null;
        return {
            selector, text: text.replace(/\s+/g, ' ').trim().slice(0, 200),
            rect: {left, top, right, bottom}, font,
            authored_role: element.getAttribute('role'), aria_hidden: element.getAttribute('aria-hidden'),
            single_line: rects.every(rect => Math.abs(rect.top - top) < 2),
        };
    }

    function brokenParagraph(element, style) {
        if (element.childNodes.length > 63) return null;
        const chunks = [[]];
        for (const child of element.childNodes) {
            if (child.nodeType === Node.TEXT_NODE) chunks.at(-1).push(child);
            else if (child.localName === 'br') chunks.push([]);
            else return null;
        }
        if (chunks.length < 3) return null;
        const selector = path(element);
        const font = fontSignature(style);
        const lines = chunks.map((nodes, index) => {
            const text = nodes.map(node => node.data).join('');
            if (!text.trim()) return null;
            const range = document.createRange();
            range.setStartBefore(nodes[0]);
            range.setEndAfter(nodes.at(-1));
            const observed = textGeometry(element, text, Array.from(range.getClientRects()), font, selector);
            return observed ? {...observed, line: index + 1} : null;
        });
        return {selector, lines};
    }

    function paragraph(element) {
        if (element.localName !== 'p' || element.querySelector('a, button, input, select, textarea, img, svg')) {
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
        if (element.querySelector('br')) return brokenParagraph(element, style);
        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
        const text = [];
        const rects = [];
        let font;
        for (let node = walker.nextNode(); node; node = walker.nextNode()) {
            if (!node.data.trim()) continue;
            const nodeStyle = getComputedStyle(node.parentElement);
            const signature = fontSignature(nodeStyle);
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
        return textGeometry(element, text.join(''), rects, font, path(element));
    }

    const scopeContext = [];
    for (let node = root; node; node = node.parentElement) {
        scopeContext.push([node.localName, node.getAttribute('role'), node.getAttribute('aria-hidden')]);
    }
    const entries = Array.from(root.children, paragraph);
    return {paragraphs: entries.map(entry => entry?.lines ? null : entry),
        line_lists: entries.filter(entry => entry?.lines), url: location.href,
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


def candidate_shape(snapshot):
    """Identify changes in likely structures without comparing entire layouts."""
    paragraphs = snapshot.get('paragraphs', []) if snapshot is not None else []
    shapes = [['heading', title['selector'], body['selector']] for title, body in heading_pairs(paragraphs)]
    shapes.extend(['list', marker, *[item['selector'] for item in run]] for marker, run in bullet_runs(paragraphs))
    for paragraph in (snapshot or {}).get('line_lists', []):
        shapes.extend(['list-lines', marker, paragraph['selector'], *[item['line'] for item in run]]
                      for marker, run in bullet_runs(paragraph['lines']))
    return shapes


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


async def collect(page, scope_selector, snapshot=None):
    """Suggest visible paragraph structures for review without assigning a verdict."""
    validate_scope(scope_selector)
    if snapshot is None:
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
        for paragraph in snapshot['line_lists']:
            runs = list(bullet_runs(paragraph['lines']))
            if not runs:
                continue
            # Text separated by BRs shares one accessible element even if the paragraph is a listitem.
            semantics = await accessible_semantics(session, root, paragraph['selector'])
            candidates.extend({'kind': 'list', 'marker': marker, 'targets': run, 'accessibility': [semantics]}
                              for marker, run in runs)
    finally:
        await session.detach()
    if snapshot != await page.evaluate(PARAGRAPHS, scope_selector):
        raise ValueError('候補とアクセシビリティ情報の取得中にページ又は対象範囲が変わった。')
    return {'scope': scope_selector, 'url': snapshot['url'], 'viewport': snapshot['viewport'],
            'candidates': candidates}


def not_observed(scope, reason):
    return {'scope': scope, 'status': 'not_observed', 'reason': reason, 'candidates': []}


async def bounded_observation(scope, operation, *, deadline=None):
    from playwright.async_api import Error as PlaywrightError

    timeout = OBSERVATION_SECONDS if deadline is None else max(0, deadline - asyncio.get_running_loop().time())
    try:
        return await asyncio.wait_for(operation, timeout=timeout)
    except TimeoutError:
        return not_observed(scope, '対象範囲の観察が5秒以内に完了しなかった。')
    except (PlaywrightError, ValueError) as error:
        return not_observed(scope, str(error).partition('\n')[0] or '対象範囲を観察できなかった。')


async def snapshot(page, scope, *, deadline=None):
    """Prepare the configured region before deduplication, without querying the AX tree."""
    return await bounded_observation(scope, page.evaluate(PARAGRAPHS, scope), deadline=deadline)


async def observe(page, scope, prepared=None, *, deadline=None):
    if prepared is not None and prepared.get('status') == 'not_observed':
        return prepared
    result = await bounded_observation(scope, collect(page, scope, snapshot=prepared), deadline=deadline)
    result.setdefault('status', 'collected')
    return result


def state_description(route):
    names = {'click': 'クリック', 'hover': 'ホバー', 'key': 'キー', 'press': 'キー',
             'fill': '入力', 'scroll': 'スクロール'}
    if not route:
        return '初期表示'
    steps = []
    for action in route:
        kind = action['type']
        if kind == 'scroll':
            steps.append(f"{names[kind]} ({action['x']}, {action['y']})")
        else:
            steps.append(' '.join([names[kind], action.get('selector', ''), action.get('key', '')]).strip())
    return ' → '.join(steps)


def report_evidence(run, graph):
    """Read candidate observations attached to exported captures in a verified graph."""
    run = Path(run)
    proof = {item['path'] for item in graph.get('proof', [])}
    observed = []
    for node in graph.get('nodes', []):
        path = Path(node['evidence_dir']) / EVIDENCE_FILE
        if path.as_posix() not in proof:
            continue
        value = json.loads((run / path).read_text())
        observed.append(dict(value, criterion='1.3.1', checkpoint=CHECKPOINT, capture=node['capture'],
                             environment=node['environment'], route=node['route'],
                             state=state_description(node['route']), evidence=path.as_posix()))
    return observed


def display_text(value):
    return re.sub(r'[\x00-\x1f\x7f]', ' ', value)[:240]


def display_rows(observations):
    for row in observations:
        context = {key: display_text(row[key]) for key in ('criterion', 'environment', 'state', 'scope')}
        context['evidence'] = row['evidence']
        if not row['candidates']:
            if row['status'] == 'not_observed':
                yield dict(context, status='観察できず', observed=display_text(row['reason']))
            else:
                yield dict(context, status='候補なし', observed='今回の表示範囲と検出条件で確認。')
        for candidate in row['candidates']:
            heading = candidate['kind'] == 'heading'
            targets = [candidate['target']] if heading else candidate['targets']
            selectors = list(dict.fromkeys(item['selector'] for item in targets))
            summary = ' / '.join(display_text(selector) for selector in selectors[:3])
            if len(selectors) > 3:
                summary += f'（先頭3件 / 全{len(selectors)}件）'
            yield dict(context, status='見出し候補' if heading else 'リスト候補', target=summary,
                       observed=' / '.join(display_text(item['text']) for item in targets[:3]))
