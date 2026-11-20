"""Observe a context change on a real sequential focus move."""
import re

CHECKPOINT = '3.2.1-02'


def validate_plan(criterion, plan):
    if (criterion != '3.2.1' or not isinstance(plan, dict) or set(plan) != {'target'}
            or not isinstance(plan['target'], str) or not re.fullmatch(r'#[A-Za-z][\w-]*', plan['target'], re.ASCII)):
        raise ValueError('フォーカス移動の対象にはIDを指定する')


async def capture(criterion, page, plan):
    url = page.url
    target = page.locator(plan['target'])
    before = await page.evaluate('''() => ({
        atStart: [document.body, document.documentElement].includes(document.activeElement),
        start: performance.timeOrigin
    })''')
    events = []
    if not before['atStart'] or await target.count() != 1 or not await target.is_visible():
        return {'before_url': url, 'events': events}

    def record(source, event):
        if source['frame'] == page.main_frame:
            events.append(event)

    await page.expose_binding('__recordBenchmarkFocus', record)
    await page.evaluate('''() => {
        for (const type of ['keydown', 'focusin']) {
            addEventListener(type, event => {
                window.__recordBenchmarkFocus({
                    type, key: event.key, trusted: event.isTrusted, url: location.href,
                    start: performance.timeOrigin, id: event.target?.id
                }).catch(() => {});
            }, true);
        }
    }''')
    await page.keyboard.press('Tab')
    await page.wait_for_timeout(300)
    current = await page.evaluate('() => ({start: performance.timeOrigin, id: document.activeElement?.id})')
    return {'before_url': url, 'before': before, 'after_url': page.url, 'after': current, 'events': events}


def evaluate(criterion, plan, evidence):
    events = evidence.get('events', [])
    before_url = evidence.get('before_url')
    before = evidence.get('before', {})
    after = evidence.get('after', {})
    target_id = plan['target'][1:]
    confirmed = (
        len(events) == 2
        and all(event.get('trusted') is True and event.get('url') == before_url
                and event.get('start') == before.get('start') for event in events)
        and events[0].get('type') == 'keydown' and events[0].get('key') == 'Tab'
        and events[1].get('type') == 'focusin' and events[1].get('id') == target_id
    )
    outcome = 'cant_tell'
    observed = '最初の実Tabが指定対象へ届いた記録を確認できませんでした。'
    if confirmed and evidence['after_url'] != before_url and before['start'] != after['start']:
        outcome, observed = 'failed', '実Tabで対象にフォーカスが移った直後に、別の文書へ移動しました。'
    elif confirmed and evidence['after_url'] == before_url and before['start'] == after['start'] and after['id'] == target_id:
        outcome, observed = 'passed', '実Tabで対象にフォーカスが移り、観測中は同じ文書に留まりました。'
    return [dict(target=plan['target'], checkpoint=CHECKPOINT, outcome=outcome, observed=observed)]
