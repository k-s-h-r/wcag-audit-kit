"""Collect 1.3.1 review candidates from a declared region in Chromium."""
import asyncio
import json
from pathlib import Path
import re


EVIDENCE_FILE = 'visual-structure.json'
CHECKPOINT = '1.3.1-02'
OBSERVATION_SECONDS = 5
REPORT_TITLE = '見た目の構造の確認候補'
REPORT_COLUMNS = (
    ('criterion', '達成基準'), ('environment', '環境'), ('state', '表示状態・操作'),
    ('scope', '指定範囲'),
    ('status', '観察結果'), ('target', '対象要素'), ('observed', '表示された文言・理由'),
    ('roles', '認識された役割'),
    ('evidence', '元の証拠'),
)


def validate_scope(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('visual_structure_scopeには対象範囲のCSSセレクターを指定する。')
    return value


STRUCTURES = r"""
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
        if (!['p', 'div'].includes(element.localName) ||
                element.querySelector('a, button, input, select, textarea, img, svg, p, div, section, ul, ol, dl, table')) {
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

    function tableCell(element) {
        if (element.childNodes.length !== 1 || element.firstChild.nodeType !== Node.TEXT_NODE) return null;
        const style = getComputedStyle(element);
        const text = element.textContent.trim();
        if (!text || text.length > 80 || !element.checkVisibility({opacityProperty:true, visibilityProperty:true})) return null;
        const range = document.createRange();
        range.selectNodeContents(element);
        const item = textGeometry(element, text, Array.from(range.getClientRects()), fontSignature(style), path(element));
        if (!item?.single_line) return null;
        const {left, right, top, bottom} = element.getBoundingClientRect();
        return {...item, box: {left, right, top, bottom}};
    }

    function separateCards(group, elements) {
        if (group.matches('table, [role="table"], [role="grid"], [role="treegrid"]')) return false;
        // Require both an independent article and visible separation in each data row.
        return elements.slice(1).every((row, index) => {
            if (!row.matches('article, [role="article"]')) return false;
            const style = getComputedStyle(row);
            const rounded = ['TopLeft', 'TopRight', 'BottomLeft', 'BottomRight']
                .every(corner => parseFloat(style['border' + corner + 'Radius']) >= 4);
            const outlined = ['Top', 'Right', 'Bottom', 'Left']
                .every(side => parseFloat(style['border' + side + 'Width']) >= 1 &&
                    style['border' + side + 'Style'] === 'solid' &&
                    style['border' + side + 'Color'].startsWith('rgb('));
            return rounded && outlined &&
                row.getBoundingClientRect().top - elements[index].getBoundingClientRect().bottom >= 8;
        });
    }

    function tableGroup(group) {
        const rowGroup = 'thead, tbody, tfoot, [role="rowgroup"]';
        if (group.children.length > 8 || group.matches(rowGroup)) return null;
        const elements = [];
        for (const child of group.children) {
            if (child.matches(rowGroup)) {
                if (elements.length + child.children.length > 8) return null;
                elements.push(...child.children);
            } else elements.push(child);
        }
        if (elements.length < 3 || elements.length > 8) return null;
        const columns = elements[0].children.length;
        if (columns < 2 || columns > 6 || elements.some(row => row.children.length !== columns)) return null;
        const rows = [];
        for (const row of elements) {
            const cells = Array.from(row.children, tableCell);
            if (cells.some(cell => !cell)) return null;
            cells.sort((a, b) => a.box.left - b.box.left);
            const first = cells[0].box;
            if (cells.some(({box}, index) => Math.abs(box.top - first.top) > 3 ||
                    Math.abs(box.bottom - first.bottom) > 3 || (index > 0 && cells[index - 1].box.right > box.left + 1)))
                return null;
            const previous = rows.at(-1)?.cells[0].box;
            if (previous && (previous.bottom > first.top + 1 || first.top - previous.bottom > 32)) return null;
            rows.push({selector: path(row), cells});
        }
        const header = rows[0].cells;
        if (rows.slice(1).some(({cells}) => cells.some((cell, index) => {
            const title = header[index];
            return Math.abs(cell.box.left - title.box.left) > 3 || Math.abs(cell.box.right - title.box.right) > 3 ||
                   title.font[2] < cell.font[2] + 150;
        }))) return null;
        return {selector: path(group), rows, separate_cards: separateCards(group, elements)};
    }

    const scopeContext = [];
    for (let node = root; node; node = node.parentElement) {
        scopeContext.push([node.localName, node.getAttribute('role'), node.getAttribute('aria-hidden')]);
    }
    const entries = Array.from(root.children, paragraph);
    return {paragraphs: entries.map(entry => entry?.lines ? null : entry),
        line_lists: entries.filter(entry => entry?.lines),
        tables: [root, ...root.children].map(tableGroup).filter(Boolean), url: location.href,
        document_start: performance.timeOrigin, scopeContext,
        viewport: {width: document.documentElement.clientWidth, height: document.documentElement.clientHeight}};
}
"""
LIST_PREFIX = re.compile(r'^(?:([・•●○▪◦])\s*|([-*])\s+|([1-9][0-9]{0,2})([.)])\s+)\S{2}')


def list_prefix(text):
    match = LIST_PREFIX.match(text)
    if not match:
        return '', None
    bullet, spaced_bullet, number, delimiter = match.groups()
    return (f'連番（{delimiter}）', int(number)) if number else (bullet or spaced_bullet, None)


def heading_pairs(paragraphs):
    for title, body in zip(paragraphs, paragraphs[1:]):
        if title is None or body is None:
            continue
        _, title_size, title_weight, title_line_height = title['font']
        _, body_size, body_weight, _ = body['font']
        title_marker, title_number = list_prefix(title['text'])
        gap = body['rect']['top'] - title['rect']['bottom']
        if (title['single_line'] and 3 <= len(title['text']) <= 50 and len(body['text']) >= 24
                and (not title_marker or title_number is not None) and not list_prefix(body['text'])[0]
                and title_size >= 1.2 * body_size and title_weight >= body_weight + 150
                and abs(title['rect']['left'] - body['rect']['left']) <= 3 and 0 <= gap <= 2 * title_line_height):
            yield title, body


def bullet_runs(paragraphs):
    run = []
    marker = ''
    number = None
    for paragraph in [*paragraphs, None]:
        current_marker, current_number = list_prefix(paragraph['text']) if paragraph and paragraph['single_line'] else ('', None)
        previous = run[-1] if run else None
        same_run = (previous is not None and current_marker == marker and paragraph['font'] == previous['font']
                    and (number is None or current_number == number + 1)
                    and abs(paragraph['rect']['left'] - previous['rect']['left']) <= 3
                    and 0 <= paragraph['rect']['top'] - previous['rect']['bottom'] <= 2 * previous['font'][3])
        if same_run:
            run.append(paragraph)
            number = current_number
            continue
        if len(run) >= 3:
            yield marker, run
        run = [paragraph] if current_marker else []
        marker = current_marker
        number = current_number


def candidate_shape(snapshot):
    """Identify changes in likely structures without comparing entire layouts."""
    paragraphs = snapshot.get('paragraphs', []) if snapshot is not None else []
    shapes = [['heading', title['selector'], body['selector']] for title, body in heading_pairs(paragraphs)]
    shapes.extend(['list', marker, *[item['selector'] for item in run]] for marker, run in bullet_runs(paragraphs))
    for paragraph in (snapshot or {}).get('line_lists', []):
        shapes.extend(['list-lines', marker, paragraph['selector'], *[item['line'] for item in run]]
                      for marker, run in bullet_runs(paragraph['lines']))
    shapes.extend(['table', table['selector'],
                   *[cell['selector'] for row in table['rows'] for cell in row['cells']],
                   bool(table.get('separate_cards'))]
                  for table in (snapshot or {}).get('tables', []))
    return shapes


async def accessible_semantics(session, root, selector, *, ancestry=False):
    found = await session.send('DOM.querySelector', {'nodeId': root, 'selector': selector})
    if not found['nodeId']:
        return {'role': None, 'ignored': None, 'inside_list': None}
    tree = await session.send('Accessibility.getPartialAXTree', {'nodeId': found['nodeId']})
    node, *relatives = tree['nodes']
    by_id = {n['nodeId']: n for n in relatives}
    role = node.get('role', {}).get('value')
    ancestors = []
    parent = by_id.get(node.get('parentId'))
    while parent is not None:
        ancestors.append(dict(backend_node_id=parent.get('backendDOMNodeId'), role=parent.get('role', {}).get('value')))
        parent = by_id.get(parent.get('parentId'))
    semantics = {'role': role, 'ignored': node['ignored'], 'inside_list': any(item['role'] == 'list' for item in ancestors)}
    if ancestry:
        semantics.update(backend_node_id=node.get('backendDOMNodeId'), ancestors=ancestors)
    return semantics


TABLE_ROLES = {'table', 'grid', 'treegrid'}


async def table_candidate(session, root, table):
    async def semantics(selector):
        return await accessible_semantics(session, root, selector, ancestry=True)

    group = await semantics(table['selector'])
    missing = []
    if group['role'] not in TABLE_ROLES or group['ignored'] or group.get('backend_node_id') is None:
        missing.append(table['selector'])
    observed_rows = []
    for index, row in enumerate(table['rows']):
        owner = await semantics(row['selector'])
        if not has_table_role(owner, {'row'}, group):
            missing.append(row['selector'])
        observed_cells = []
        roles = {'columnheader'} if index == 0 else {'cell', 'gridcell', 'rowheader'}
        for cell in row['cells']:
            actual = await semantics(cell['selector'])
            if not has_table_role(actual, roles, owner):
                missing.append(cell['selector'])
            observed_cells.append(dict(cell, accessibility=actual))
        observed_rows.append(dict(row, accessibility=owner, cells=observed_cells))
    card_articles = table.get('separate_cards') and all(
        row['accessibility']['role'] == 'article' and not row['accessibility']['ignored']
        for row in observed_rows[1:]
    )
    if missing and not card_articles:
        return {'kind': 'table', 'target': table['selector'], 'accessibility': group, 'rows': observed_rows,
                'unmatched_roles': missing}


def has_table_role(actual, roles, owner):
    owner_id = owner.get('backend_node_id')
    return (actual['role'] in roles and actual['ignored'] is False and owner_id is not None
            and any(parent['backend_node_id'] == owner_id for parent in actual.get('ancestors', [])))


async def collect(page, scope_selector, snapshot=None):
    """Suggest visible structures for review without assigning a verdict."""
    validate_scope(scope_selector)
    if snapshot is None:
        snapshot = await page.evaluate(STRUCTURES, scope_selector)
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
        for table in snapshot.get('tables', []):
            if candidate := await table_candidate(session, root, table):
                candidates.append(candidate)
    finally:
        await session.detach()
    if snapshot != await page.evaluate(STRUCTURES, scope_selector):
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
    return await bounded_observation(scope, page.evaluate(STRUCTURES, scope), deadline=deadline)


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


ROLE_LABELS = {
    'paragraph': '段落（paragraph）', 'generic': '汎用（generic）',
    'heading': '見出し（heading）', 'list': 'リスト（list）', 'listitem': 'リスト項目（listitem）',
    'table': 'データ表（table）', 'row': '行（row）', 'columnheader': '列見出し（columnheader）',
    'rowheader': '行見出し（rowheader）', 'cell': 'データセル（cell）', 'none': '役割なし（none）',
    'LayoutTable': 'レイアウト用の表（LayoutTable）',
    'LayoutTableRow': 'レイアウト用の行（LayoutTableRow）',
    'LayoutTableCell': 'レイアウト用のセル（LayoutTableCell）',
}


def displayed_roles(semantics):
    values = []
    for item in semantics:
        if item['ignored'] is None:
            values.append('役割を取得できず')
            continue
        role = item['role']
        label = ROLE_LABELS.get(role, display_text(role or '役割なし'))
        values.append(label + ('（ツリーから除外）' if item['ignored'] else ''))
    return ' / '.join(dict.fromkeys(values))


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
            if candidate['kind'] == 'table':
                header, *body = candidate['rows']
                labels = ' / '.join(display_text(cell['text']) for cell in header['cells'])
                roles = [
                    ('表', [candidate['accessibility']]),
                    ('行', [entry['accessibility'] for entry in candidate['rows']]),
                    ('先頭行のセル', [cell['accessibility'] for cell in header['cells']]),
                    ('後続行のセル', [cell['accessibility'] for entry in body for cell in entry['cells']]),
                ]
                selectors = list(dict.fromkeys([candidate['target'], *candidate['unmatched_roles']]))
                yield dict(context, status='表候補', target=target_summary(selectors),
                           observed=f'先頭行 {labels}（全{len(body) + 1}行、{len(header["cells"])}列）',
                           roles=' / '.join(f'{label} {displayed_roles(values)}' for label, values in roles))
                continue
            heading = candidate['kind'] == 'heading'
            targets = [candidate['target']] if heading else candidate['targets']
            selectors = list(dict.fromkeys(item['selector'] for item in targets))
            yield dict(context, status='見出し候補' if heading else 'リスト候補', target=target_summary(selectors),
                       observed=' / '.join(display_text(item['text']) for item in targets[:3]),
                       roles=displayed_roles([candidate['accessibility']] if heading else candidate['accessibility']))


def target_summary(selectors):
    summary = ' / '.join(display_text(selector) for selector in selectors[:3])
    if len(selectors) > 3:
        summary += f'（先頭3件 / 全{len(selectors)}件）'
    return summary
