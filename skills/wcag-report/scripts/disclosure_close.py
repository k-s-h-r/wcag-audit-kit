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


def finish(record, confirmed):
    before, after = record['before'], record['after']
    record['status'] = 'cant_tell'
    if not (confirmed and ready(before) and after and
            all(before[key] == after[key] for key in ('document', 'opener', 'panel', 'url'))):
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
