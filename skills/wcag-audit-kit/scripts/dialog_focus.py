"""Observe Escape and a subsequent Tab on a replayed automatic route."""
from keyboard_checks import matching_keydown


EVIDENCE_FILE = 'dialog-focus.json'
SNAPSHOT = '() => window.__wcagDialogFocus()'


def same_document(before, after):
    return all(before[key] == after[key] for key in ('document_start', 'url'))


def opening_event(event, action):
    if not event.get('expectedTargetMatched'):
        return False
    if action['type'] == 'click':
        return event['type'] == 'click' and event['isTrusted'] and event['is_main_frame']
    return matching_keydown(event, action['key'])


class DialogFocus:
    def __init__(self, page, observer, close_step, phase):
        self.page = page
        self.observer = observer
        self.close_step = close_step
        self.opener = None
        self.opener_handle = None
        self.opener_event_index = None
        self.record = dict(phase=phase, status='unconfirmed', reason='閉じる操作まで到達していない。')

    async def before(self, index, action):
        self.initial = await self.page.evaluate(SNAPSHOT)
        self.input_start = len(self.observer.events)
        self.opening = None
        if index > self.close_step:
            if self.record['status'] != 'closed' or self.initial != self.record['after_escape']:
                raise ValueError('再生時に閉じた直後の状態を確認できず、次のTabは未実施。')
        elif index < self.close_step and not self.initial['modals'] and (
            action['type'] == 'click' or (action['type'] == 'key' and action.get('key') in {'Enter', 'Space'})
        ):
            target = self.page.locator(action['selector'])
            if await target.count() == 1:
                handle = await target.element_handle(timeout=1500)
                await handle.evaluate('e => { window.__wcagExpectedPointerTarget = e; }')
                self.opening = (action, handle)

    async def after(self, index):
        current = await self.page.evaluate(SNAPSHOT)
        if index < self.close_step:
            opening = self.opening
            if opening:
                await self.page.evaluate('() => { window.__wcagExpectedPointerTarget = null; }')
            if self.initial['modals'] != current['modals']:
                self.opener = self.opener_handle = self.opener_event_index = None
                if opening and not self.initial['modals'] and same_document(self.initial, current):
                    action, handle = opening
                    events = enumerate(self.observer.events[self.input_start:], self.input_start + 1)
                    match = next((i for i, event in events if opening_event(event, action)), None)
                    if not self.observer.dropped and match is not None:
                        self.opener, self.opener_handle = action['selector'], handle
                        self.opener_event_index = match
            return
        key = 'Escape' if index == self.close_step else 'Tab'
        event_index = next((i for i, event in enumerate(self.observer.events[self.input_start:], self.input_start + 1)
                            if matching_keydown(event, key)), None)
        if index == self.close_step:
            self.record.update(opener=self.opener, before_escape=self.initial, after_escape=current,
                               opener_event_index=self.opener_event_index, escape_event_index=event_index)
        else:
            self.record.update(after_tab=current, tab_event_index=event_index)
        if not self.initial['supported'] or not current['supported'] or not same_document(self.initial, current):
            self.invalidate('入力前後の同じ主文書とフォーカスを確認できない。')
        elif self.observer.dropped or event_index is None:
            self.invalidate(f'{key}が文書に届いた記録を確認できない。')
        elif index == self.close_step and len(self.initial['modals']) != 1:
            self.invalidate('閉じる前のモーダルダイアログを一つに特定できない。')
        elif current['modals']:
            self.invalidate('入力後も同じダイアログが開いている。' if self.initial['modals'] == current['modals']
                            else '入力後に別のダイアログが表示された。')
        else:
            self.record.update(status='closed', reason='')
            if index == self.close_step:
                self.record['opener_restored'] = (
                    await self.opener_handle.evaluate('(e) => e.isConnected && document.activeElement === e')
                    if self.opener_handle else None)

    def invalidate(self, reason):
        self.record.update(status='unconfirmed', reason=reason)


def report_row(record, environment, evidence, route, capture):
    after = record.get('after_escape', {}).get('focus')
    next_focus = record.get('after_tab', {}).get('focus')
    if record['status'] == 'closed' and record.get('opener_restored') is True:
        observed = f'閉じた後、開く操作の対象 {record["opener"]} にフォーカスが戻った。'
    elif after:
        observed = f'Escape後のフォーカス先は {after}。'
    else:
        observed = ''
    if next_focus:
        observed += f'次のTab後は {next_focus}。'
    if record['reason']:
        observed += record['reason']
    elif record.get('opener_restored') is False:
        observed += '開く操作の対象と同じ要素への復帰は確認できなかった。'
    elif not record.get('opener'):
        observed += '開く操作の対象を特定できなかった。'
    verified = (record['status'] == 'closed' and record.get('opener_restored') is True
                and (record['phase'] == 'escape' or record.get('tab_event_index') is not None))
    return dict(criterion='2.4.3', checkpoint='ダイアログを閉じた後のフォーカス',
                expected='閉じた後のフォーカスと、その後の操作を確認する',
                environment=environment, capture=capture, state_label=route, target=record.get('opener') or '',
                outcome='passed' if verified else 'cant_tell', observed=observed, evidence=evidence, source='',
                dialog_focus=record, note='観測した経路の結果。別のフォーカス先が操作上適切かは追加確認。')
