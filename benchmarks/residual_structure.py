"""Observe simple table relationships, HTML input purpose, and disclosure state."""
import re


SELECTOR = re.compile(r'#[A-Za-z][A-Za-z0-9_-]*')
PLAN_KEYS = {
    '1.3.1': {'target', 'axes'},
    '1.3.5': {'target', 'purpose'},
    '4.1.2': {'target', 'controlled'},
}
HEADER_ROLES = {'row': 'rowheader', 'column': 'columnheader'}
PURPOSES = frozenset("""
    name honorific-prefix given-name additional-name family-name honorific-suffix nickname
    username new-password current-password organization-title organization street-address
    address-line1 address-line2 address-line3 address-level4 address-level3 address-level2
    address-level1 country country-name postal-code cc-name cc-given-name cc-additional-name
    cc-family-name cc-number cc-exp cc-exp-month cc-exp-year cc-csc cc-type transaction-currency
    transaction-amount language bday bday-day bday-month bday-year sex url photo
    tel tel-country-code tel-national tel-area-code tel-local tel-local-prefix tel-local-suffix
    tel-extension email impp
""".split())

TABLE = """table => {
    if (!(table instanceof HTMLTableElement) || table.querySelector('table') ||
        table.rows.length < 2 || table.rows.length > 10) return null;
    const rows = [...table.rows].map(row => [...row.cells]);
    const width = rows[0].length;
    if (width < 2 || width > 10 || rows.some(row => row.length !== width)) return null;
    const domOrder = table.querySelectorAll('th,td');
    if (rows.flat().some((cell, i) => cell !== domOrder[i] || cell.colSpan !== 1 || cell.rowSpan !== 1 ||
        !cell.checkVisibility({visibilityProperty: true, opacityProperty: true}))) return null;
    return rows.map(row => row.map(cell => ({
        id: cell.id, tag: cell.tagName, scope: cell.scope,
        headers: cell.getAttribute('headers'),
        uniqueId: cell.id !== '' && table.ownerDocument.querySelectorAll('#' + CSS.escape(cell.id)).length === 1
    })));
}"""


def validate_plan(criterion, plan):
    if not isinstance(plan, dict) or criterion not in PLAN_KEYS or set(plan) != PLAN_KEYS[criterion]:
        raise ValueError('構造の検証計画に必要なキーがありません')
    selectors = [plan['target']]
    if criterion == '4.1.2':
        selectors.append(plan['controlled'])
    if any(not isinstance(value, str) or not SELECTOR.fullmatch(value) for value in selectors):
        raise ValueError('構造の検証対象はIDセレクターで指定します')
    if criterion == '1.3.1':
        axes = plan['axes']
        if (not isinstance(axes, list) or not 1 <= len(axes) <= 2
                or any(axis not in ('row', 'column') for axis in axes)
                or len(set(axes)) != len(axes)):
            raise ValueError('表の見出しは行または列の関係を指定します')
    if criterion == '1.3.5':
        purpose = plan['purpose']
        if not isinstance(purpose, str) or purpose not in PURPOSES:
            raise ValueError('入力目的は標準のautocompleteトークンで指定します')
    if criterion == '4.1.2' and plan['target'] == plan['controlled']:
        raise ValueError('展開ボタンと展開領域の対象を分けて指定します')


async def accessibility_nodes(session, selector):
    document = await session.send('DOM.getDocument')
    result = await session.send('DOM.querySelectorAll', {'nodeId': document['root']['nodeId'], 'selector': selector})
    nodes = []
    for node_id in result['nodeIds']:
        node = await session.send('DOM.describeNode', {'nodeId': node_id})
        backend = node['node']['backendNodeId']
        tree = await session.send('Accessibility.getPartialAXTree', {'backendNodeId': backend, 'fetchRelatives': False})
        ax = next((item for item in tree['nodes'] if item.get('backendDOMNodeId') == backend), {})
        nodes.append({
            'observed': bool(ax), 'exposed': ax.get('ignored') is False,
            'role': ax.get('role', {}).get('value'),
            'name': ax.get('name', {}).get('value'),
            'expanded': next((prop['value']['value'] for prop in ax.get('properties', [])
                              if prop['name'] == 'expanded'), None),
        })
    return nodes


async def table_evidence(session, locator, target):
    rows = await locator.evaluate(TABLE)
    if rows is None:
        return {}
    ax = await accessibility_nodes(session, f'{target} :is(th, td)')
    cells = [cell for row in rows for cell in row]
    if len(ax) != len(cells) or not all(node['observed'] for node in ax):
        return {}
    for cell, node in zip(cells, ax):
        cell.update(node)
    return {'rows': rows}


async def disclosure_state(session, target, controlled):
    ax = await accessibility_nodes(session, target)
    if len(ax) != 1 or not ax[0]['observed'] or await controlled.count() != 1:
        return {}
    return {'visible': await controlled.is_visible(), 'ax': ax[0]}


async def capture(criterion, page, plan):
    validate_plan(criterion, plan)
    target = plan['target']
    locator = page.locator(target)
    if await locator.count() != 1 or not await locator.is_visible():
        return {}
    if criterion == '1.3.5':
        value = await locator.evaluate("""field => {
            if (!(field instanceof HTMLInputElement) ||
                !['text', 'search', 'email', 'tel', 'url', 'password', 'date', 'month', 'number'].includes(field.type) ||
                field.matches(':disabled') || field.readOnly) return null;
            return {autocomplete: field.autocomplete, attribute: field.getAttribute('autocomplete')};
        }""")
        return {'input': value}
    session = await page.context.new_cdp_session(page)
    try:
        if criterion == '1.3.1':
            return await table_evidence(session, locator, target)
        controlled = page.locator(plan['controlled'])
        before = await disclosure_state(session, target, controlled)
        if before.get('visible') is not False:
            return {'before': before}
        url = page.url
        element = await locator.element_handle(timeout=1500)
        await locator.click(timeout=1500)
        if page.url != url or await locator.count() != 1:
            return {'before': before}
        if not await locator.evaluate('(current, previous) => current === previous', element):
            return {'before': before}
        after = await disclosure_state(session, target, controlled)
        return {'before': before, 'after': after}
    finally:
        await session.detach()


def header_axis(cell):
    if not cell['exposed'] or not isinstance(cell['name'], str) or not cell['name'].strip():
        return None
    return next((axis for axis, role in HEADER_ROLES.items() if cell['role'] == role), None)


def table_result(plan, evidence):
    rows = evidence.get('rows')
    if not rows:
        return 'cant_tell', '単純な矩形の表と表示されたセルを確認できませんでした。'
    cells = [(r, c, cell) for r, row in enumerate(rows) for c, cell in enumerate(row)]
    if any(cell['scope'] in {'rowgroup', 'colgroup'} for _, _, cell in cells):
        return 'cant_tell', '行グループまたは列グループの見出しには別の照合が必要です。'
    headings = [(r, c, cell, header_axis(cell)) for r, c, cell in cells if header_axis(cell)]
    data = [(r, c, cell) for r, c, cell in cells if cell['tag'] == 'TD' and not header_axis(cell)]
    if not data:
        return 'cant_tell', '見出しと照合できるデータセルを確認できませんでした。'
    missing = 0
    for row, column, cell in data:
        if cell['headers'] is not None:
            references = set(cell['headers'].split())
            if any(head['id'] in references and not head['uniqueId'] for _, _, head, _ in headings):
                return 'cant_tell', '見出しの参照先を一意に確認できませんでした。'
            available = {axis for _, _, head, axis in headings if head['id'] in references}
        else:
            available = {
                axis for r, c, head, axis in headings
                if (axis == 'row' and r == row and c < column and head['scope'] in {'', 'row'})
                or (axis == 'column' and c == column and r < row and head['scope'] in {'', 'col'})
            }
        if not set(plan['axes']) <= available:
            missing += 1
    if missing:
        return 'failed', f'データセル{len(data)}個のうち{missing}個で、指定した方向の見出しを確認できませんでした。'
    return 'passed', f'データセル{len(data)}個すべてで、指定した方向の見出しを確認しました。'


def purpose_result(plan, evidence):
    field = evidence.get('input')
    if not isinstance(field, dict):
        return 'cant_tell', '表示されている編集可能なHTML入力欄を確認できませんでした。'
    parsed = field['autocomplete'].split()
    if parsed and parsed[-1] == 'webauthn':
        parsed.pop()
    purpose = parsed[-1] if parsed else ''
    if purpose == plan['purpose']:
        return 'passed', f'ブラウザーが解釈したautocompleteの入力目的は{purpose}です。'
    return 'failed', f'指定された入力目的{plan["purpose"]}を確認できませんでした。ブラウザーの解釈値は{field["autocomplete"] or "空"}です。'


def disclosure_result(evidence):
    before = evidence.get('before', {})
    after = evidence.get('after', {})
    if before.get('visible') is not False or after.get('visible') is not True:
        return 'cant_tell', 'ボタン操作前の非表示から操作後の表示への変化を確認できませんでした。'
    for state, expanded in ((before, False), (after, True)):
        ax = state['ax']
        if not ax['exposed'] or ax['role'] != 'button' or not (ax['name'] or '').strip():
            return 'failed', '実際に領域を展開した部品に、ボタンの役割と空でないアクセシブルな名前を確認できませんでした。'
        if ax['expanded'] is not expanded:
            return 'failed', '領域の表示変化に対応する展開状態をアクセシビリティツリーで確認できませんでした。'
    return 'passed', '領域の表示変化と、ボタンの名前・役割・展開状態をアクセシビリティツリーで確認しました。'


def evaluate(criterion, plan, evidence):
    validate_plan(criterion, plan)
    if criterion == '1.3.1':
        outcome, observed = table_result(plan, evidence)
    elif criterion == '1.3.5':
        outcome, observed = purpose_result(plan, evidence)
    else:
        outcome, observed = disclosure_result(evidence)
    return [{'target': plan['target'], 'checkpoint': f'{criterion}-01', 'outcome': outcome, 'observed': observed}]
