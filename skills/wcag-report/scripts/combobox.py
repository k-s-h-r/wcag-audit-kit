"""Observe a keyboard-operated editable combobox and its controlled listbox."""
from contextlib import suppress

EXPANSION_CHECK = 'コンボボックスの表示と展開状態'


def editable(control):
    return (control['role'] == 'combobox' and control['tag'] in {'input', 'textarea'}
            and control['type'] not in {'checkbox', 'radio', 'button', 'reset', 'submit', 'image'})


async def observe(page, target):
    from playwright.async_api import Error as BrowserError

    with suppress(BrowserError):
        return await page.locator(target).evaluate('element => window.__wcagCombobox(element)', timeout=750)
    return None


def finish(record, confirmed):
    before, after = record['before'], record['after']
    prior_value = before.pop('value') if before is not None else None
    next_value = after.pop('value') if after is not None else None
    record['status'] = 'cant_tell'
    if not (confirmed and before and after and
            all(before[key] == after[key] for key in ('document', 'url', 'panel_id'))):
        return
    record.update(status='observed', value_changed=prior_value != next_value)
    if record['key'] == 'ArrowDown' and after['visible'] and after['focused']:
        record['followups'] = ('Enter',) if before['visible'] else ('ArrowDown', 'Enter', 'Escape')


def report_row(record, edge, state_label, capture):
    if record['status'] != 'observed':
        return None
    before, after = record['before'], record['after']
    key = record['key']
    outcome = 'cant_tell'
    if key == 'ArrowDown' and not before['visible'] and after['visible'] and after['focused']:
        checkpoint = EXPANSION_CHECK
        criterion = '4.1.2'
        expected = '表示された候補の展開状態が aria-expanded に反映される'
        expanded = after['expanded']
        if expanded in (None, 'false'):
            outcome = 'failed'
        elif expanded == 'true':
            outcome = 'passed'
        observed = f"候補が表示され、aria-expanded は {expanded if expanded is not None else '未指定'}。"
        if after['active_option']:
            observed += f"参照された候補は {after['active_option']}。"
    else:
        checkpoint = f'コンボボックスの操作 / {key}'
        criterion = '2.1.1'
        expected = '候補の表示、候補の参照先、入力値の変化を確認する'
        visibility = '表示された' if after['visible'] else '表示されていない'
        value = '変わった' if record['value_changed'] else '同じだった'
        focus = '入力欄にある' if after['focused'] else '入力欄の外にある'
        observed = f'{key}の後、候補は{visibility}。入力値は{value}。フォーカスは{focus}。'
        if key == 'ArrowDown' and before['visible'] and after['visible']:
            old = before['active_option'] or 'なし'
            new = after['active_option'] or 'なし'
            observed += f'aria-activedescendant が参照する候補は {old} → {new}。'
    return dict(criterion=criterion, checkpoint=checkpoint, expected=expected, outcome=outcome,
                environment=edge['environment'], capture=capture, state_label=state_label,
                target=edge['route'][-1]['selector'], observed=observed,
                evidence=edge['evidence_dir'] + '/transition.json', source='',
                note='観察したコンボボックスの状態。候補の選択や取消の適否は部品の目的に応じて確認する。')
