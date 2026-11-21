"""Observe an Escape after Tab enters an explicitly controlled region."""
from contextlib import suppress


async def observe(page, opener, *, expect_input=False):
    from playwright.async_api import Error as BrowserError

    with suppress(BrowserError):
        return await page.locator(opener).evaluate(
            '(element, bindFocus) => window.__wcagDisclosure(element, bindFocus)', expect_input, timeout=750)
    return None


def ready(observation):
    return bool(observation and observation['expanded'] == 'true' and observation['visible']
                and observation['focus_within'])


def same_panel(before, after):
    return bool(before and after and
                all(before[key] == after[key] for key in ('document', 'opener', 'panel', 'url')))


def content_open(observation):
    return bool(observation and observation['content_toggle']
                and observation['expanded'] == 'true' and observation['content_visible'] is True)


def content_closed(observation):
    return observation['expanded'] == 'false' and observation['content_visible'] is False


def returned_to_opener(record, target):
    before, after = record['before'], record['after']
    return (record['event_index'] is not None and same_panel(before, after)
            and content_open(before) and content_open(after)
            and before['panel'] == target['panel'] and before['focus'] == target['focus']
            and after['focus'] == target['opener'])


def toggle_result(before, after, confirmed):
    record = {'before': before, 'after': after, 'status': 'cant_tell'}
    if not confirmed or not same_panel(before, after) or not after['content_toggle']:
        return record
    was_open = content_open(before)
    was_closed = content_closed(before)
    if was_closed and content_open(after):
        record['status'] = 'opened'
    elif was_open and content_closed(after):
        record['status'] = 'closed'
    elif was_closed and content_closed(after):
        record['status'] = 'stayed_closed'
    elif was_open and content_open(after):
        record['status'] = 'stayed_open'
    return record


def finish(record, confirmed):
    before, after = record['before'], record['after']
    record['status'] = 'cant_tell'
    if not (confirmed and ready(before) and same_panel(before, after)):
        return
    if after['expanded'] == 'false' and not after['visible']:
        record['status'] = 'closed'
        record['focus_returned'] = after['focus'] == before['opener']
    elif after['expanded'] == 'true' and after['visible']:
        record['status'] = 'stayed_open'


def report_row(record, edge, state_label, capture):
    outcome = 'cant_tell'
    observed = '同じ領域の表示とフォーカスを操作前後で確認できなかった。'
    if record['status'] == 'closed':
        target = record['after']['focus']
        if record['focus_returned']:
            outcome = 'passed'
            observed = f'Escapeで閉じ、開閉ボタン {target} へフォーカスが戻った。'
        else:
            observed = f'Escapeで閉じた後のフォーカス先は {target}。移動先が適切かを確認する。'
    elif record['status'] == 'stayed_open':
        observed = f"Escapeの後も領域は開いていた。フォーカス先は {record['after']['focus']}。"

    return dict(
        criterion='2.4.3', checkpoint='展開した領域を閉じた後のフォーカス',
        expected='領域が閉じたかとフォーカスの戻り先を確認する', outcome=outcome,
        environment=edge['environment'], capture=capture, state_label=state_label,
        target=edge['disclosure_opener'], observed=observed,
        evidence=edge['evidence_dir'] + '/transition.json', source='',
        note='観察したEscape経路の結果。別の閉じ方と、適切なフォーカス先は部品の目的に応じて確認する。',
    )


def toggle_row(record, edge, state_label, capture):
    status = record['status']
    before = record['before']
    key = edge['route'][-1]['key']
    expected = 'このキーで領域を閉じ、開閉ボタンのフォーカスを保つ' if content_open(before) else 'このキーで領域を開く'
    outcome = 'cant_tell'
    observed = 'キー入力の前後で同じ領域の開閉を確認できなかった。'
    if status == 'opened':
        outcome = 'passed'
        observed = f"{key}で領域を開いた。入力後のフォーカスは {record['after']['focus']}。"
    elif status == 'closed':
        after = record['after']
        outcome = 'passed' if after['focus'] == before['opener'] else 'cant_tell'
        observed = f"{key}で領域を閉じた。入力後のフォーカスは {after['focus']}。"
    elif status in {'stayed_closed', 'stayed_open'}:
        state = '閉じた' if status == 'stayed_closed' else '開いた'
        observed = f'{key}が開閉ボタンに届いた後も領域は{state}ままだった。'
    return dict(
        criterion='2.4.3' if status == 'closed' else '2.1.1',
        checkpoint='キー操作後の領域の表示とフォーカス', expected=expected,
        outcome=outcome, environment=edge['environment'], capture=capture, state_label=state_label,
        target=before['opener'], observed=observed,
        evidence=edge['evidence_dir'] + '/transition.json', source='',
        note='このキー経路の開閉とフォーカスを確認した記録。ほかのキーや代替経路は追加確認する。',
    )
