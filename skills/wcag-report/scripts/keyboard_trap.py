"""Observe ordinary exit keys in a narrowly identifiable modal dialog."""
from pathlib import PurePosixPath

from keyboard_checks import matching_keydown


CHECKPOINT = 'ダイアログからのキー操作による離脱'
KEYS = ('Escape', 'Tab', 'Tab', 'Shift+Tab', 'Shift+Tab', 'ArrowDown', 'ArrowUp',
        'ArrowLeft', 'ArrowRight', 'Enter', 'Space', 'Backspace')
SNAPSHOT = r'''modal => {
    const observation = window.__wcagDialogFocus();
    const active = document.activeElement;
    const within = modal.contains(active);
    const visible = window.__wcagDialogElementVisible;
    const shown = visible(modal);
    const controls = [...modal.querySelectorAll(
      'a[href], button, input, select, textarea, summary, iframe, [contenteditable], [tabindex], [role]'
    )].filter(visible);
    const close = controls.find(node => node !== active);
    const textInput = active instanceof HTMLInputElement && active.type === 'text' &&
       !active.form && !active.disabled && !active.matches('[role], [list], [aria-haspopup]');
    const closeButton = close instanceof HTMLButtonElement && close.type === 'button' &&
       !close.form && !close.disabled && close.tabIndex < 0 &&
       /^(閉じる|キャンセル|close|cancel|dismiss)$/i.test((close.getAttribute('aria-label') || close.innerText).trim());
    const namedText = [document.body.innerText, active?.getAttribute('placeholder'), active?.getAttribute('aria-label'),
                       modal.getAttribute('aria-label')].join(' ');
    const labels = 'h1,h2,h3,h4,h5,h6,button,label,script,style';
    const text = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let unexplainedText = false;
    for (let node = text.nextNode(); node; node = text.nextNode()) {
      const parent = node.parentElement;
      if (node.textContent.trim() && parent && !parent.closest(labels) && visible(parent)) {
        unexplainedText = true;
        break;
      }
    }
    const guidance = unexplainedText ||
        Boolean(document.querySelector('[accesskey], [aria-keyshortcuts], [aria-describedby], [aria-description], [title]')) ||
        /\b([a-z0-9]|key(?:board)?|esc(?:ape)?|tab|shift|alt|ctrl|control|enter|space|arrow|f\d{1,2}|press)\b|キー|矢印|押す|閉じます|閉じるには/i.test(namedText);
    const custom = [...modal.querySelectorAll('*')].some(node => node.shadowRoot || node.localName.includes('-'));
    return {
      ...observation, within, shown,
      simple: shown && within && controls.length === 2 && controls.includes(active) &&
        textInput && closeButton && !guidance && !custom,
      blank: textInput && active.value === '',
      only_space: textInput && active.value === ' ',
      // Keep the private comparison in memory, outside the saved evidence.
      markup: shown ? modal.outerHTML : null
    };
}'''


def public(snapshot):
    return {key: value for key, value in snapshot.items() if key != 'markup'}


def same_document(before, after):
    return all(before[key] == after[key] for key in ('document_start', 'url'))


def stays(before, after):
    return (after['supported'] and after['within'] and after['shown']
            and all(before[key] == after[key] for key in ('focus', 'modals', 'markup'))
            and same_document(before, after))


def left(before, after):
    return (after['supported'] and not after['root_focus'] and not after['within'] and not after['shown']
            and not after['modals'] and same_document(before, after))


async def probe(page, modal, focus, observer, before, record, opened_by):
    """Use actual keys after the audited state has been captured."""
    from playwright.async_api import Error as BrowserError

    index = record['escape_event_index']
    if index is None or observer.dropped or not observer.events[index - 1].get('expectedTargetMatched'):
        return None
    receipt = dict(target=before['modals'][0], opener=opened_by, before=public(before),
                   opener_event_index=record['opener_event_index'] - 1,
                   escape_event_index=index - 1, outcome='cant_tell', steps=[])
    current = await modal.evaluate(SNAPSHOT)
    receipt['after_escape'] = public(current)
    if left(before, current):
        receipt.update(outcome='passed', reason='Escapeで閉じ、ダイアログの外へフォーカスが移った。')
        return receipt
    same_focus = '(e) => e.isConnected && document.activeElement === e'
    if not (before['simple'] and before['blank'] and stays(before, current) and current['simple'] and current['blank']
            and await focus.evaluate(same_focus)):
        receipt['reason'] = 'Escape後の離脱又は、追加のキー操作を確かめる条件がそろわない。'
        return receipt
    receipt['escape_retained'] = True

    for key in KEYS:
        await page.evaluate('() => { window.__wcagExpectedInputTarget = document.activeElement; }')
        start = len(observer.events)
        await page.keyboard.press(key)
        wait = await page.evaluate('() => window.__wcagWaitForUpdates()')
        await page.evaluate('() => { window.__wcagExpectedInputTarget = null; }')
        after = await modal.evaluate(SNAPSHOT)
        event_index = next((i for i in range(start, len(observer.events))
                            if observer.events[i].get('expectedTargetMatched') is True
                            and matching_keydown(observer.events[i], key)), None)
        step = dict(key=key, event_index=event_index, after=public(after), settling=wait)
        receipt['steps'].append(step)
        if observer.dropped or event_index is None or wait['status'] != 'quiet':
            receipt['reason'] = '入力の到達又は更新後の状態を確認できない。'
            return receipt
        if left(before, after):
            if key == 'Backspace':
                receipt['reason'] = 'Backspaceで離脱した。離脱方法の案内を追加確認する。'
                return receipt
            receipt.update(outcome='passed', reason=f'{key}で閉じ、ダイアログの外へフォーカスが移った。')
            return receipt
        if not (stays(before, after) and after['simple'] and (after['blank'] or key == 'Space' and after['only_space'])
                and await focus.evaluate(same_focus)):
            receipt['reason'] = 'フォーカス、表示、又は操作対象が変わった。離脱経路を追加で確認する。'
            return receipt
        step['retained'] = True
    receipt['before_pointer'] = public(after)

    candidates = page.locator(receipt['target']).locator('button:visible')
    try:
        if await candidates.count() != 1:
            receipt['reason'] = 'マウスと比較する閉じるボタンを一つに特定できない。'
            return receipt
        await candidates.evaluate('e => { window.__wcagExpectedInputTarget = e; }', timeout=1500)
        start = len(observer.events)
        await candidates.click(timeout=1500)
        wait = await page.evaluate('() => window.__wcagWaitForUpdates()')
        after = await modal.evaluate(SNAPSHOT)
    except BrowserError:
        receipt['reason'] = '比較用のマウス操作で表示とフォーカスを確認できない。'
        return receipt
    finally:
        await page.evaluate('() => { window.__wcagExpectedInputTarget = null; }')
    event_index = next((i for i in range(start, len(observer.events))
                        if (e := observer.events[i])['type'] == 'click' and e['isTrusted'] and e['is_main_frame']
                        and e['pointerType'] == 'mouse' and e.get('expectedTargetMatched') is True), None)
    receipt['pointer'] = dict(event_index=event_index, after=public(after), settling=wait)
    if event_index is not None and not observer.dropped and wait['status'] == 'quiet' and left(before, after):
        receipt.update(outcome='failed', reason='試したキーでは同じ入力欄に留まった。閉じるボタンをマウスで操作すると離脱した。')
    else:
        receipt['reason'] = '比較用のマウス操作で離脱を確認できない。'
    return receipt


def report_row(receipt, environment, evidence, route, capture):
    return dict(criterion='2.1.2', checkpoint=CHECKPOINT, target=receipt['target'],
                expected='開いたダイアログからキーボード操作で離脱できる', outcome=receipt['outcome'],
                observed=receipt['reason'], environment=environment, evidence=evidence,
                proof=[PurePosixPath(evidence).with_name('input-events.json').as_posix()],
                state_label=route, capture=capture, source='',
                note='実際に試した離脱操作の結果。ほかの操作方法や案内は追加確認。')
