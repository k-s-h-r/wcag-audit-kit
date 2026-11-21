"""Observe modal dismissal and the next Tab on an automatic exploration route."""
from contextlib import suppress

from keyboard_checks import matching_keydown
import keyboard_trap


EVIDENCE_FILE = 'dialog-focus.json'
NESTED_EVIDENCE_FILE = 'nested-dialog.json'
NESTED_PAIR = r'''snapshot => {
    const unique = selector => {
        const matches = document.querySelectorAll(selector);
        return matches.length === 1 ? matches[0] : null;
    };
    const [parent, child] = snapshot.modals.map(unique);
    const focus = unique(snapshot.focus);
    const visible = window.__wcagDialogElementVisible;
    const possibleDialogs = () => {
        // Keep the scope in the document tree when shadow content may contain another dialog.
        if ([...document.querySelectorAll('*')].some(element => element.shadowRoot)) return null;
        const mayBeDisplayed = element => {
            // Dialog containers can expose displayed content without generating a box.
            for (let node = element; node; node = node.parentElement) {
                if (getComputedStyle(node).display === 'none') return false;
            }
            return true;
        };
        return [...document.querySelectorAll(
            'dialog, [role~="dialog" i], [role~="alertdialog" i]'
        )].filter(mayBeDisplayed);
    };
    const dialogs = possibleDialogs();
    if (!dialogs || !parent || !child || parent === child || !parent.contains(child) ||
        dialogs.length !== 2 || !dialogs.includes(parent) || !dialogs.includes(child) ||
        !visible(parent) || !visible(child) || !focus || focus !== document.activeElement ||
        !child.contains(focus)) return null;
    if (snapshot.mark_input !== false) window.__wcagExpectedInputTarget = focus;
    return {parent, child, possibleDialogs};
}'''
NESTED_STATE = r'''pair => {
    if (!pair?.parent.isConnected || !pair.child.isConnected || !pair.parent.contains(pair.child) ||
        !window.__wcagDialogElementVisible(pair.parent)) return null;
    const childVisible = window.__wcagDialogElementVisible(pair.child);
    const dialogs = pair.possibleDialogs();
    if (!dialogs || dialogs.length !== (childVisible ? 2 : 1) || !dialogs.includes(pair.parent) ||
        childVisible !== dialogs.includes(pair.child)) return null;
    const snapshot = window.__wcagDialogFocus();
    const focus = document.activeElement;
    const layer = pair.child.contains(focus) ? 'child' : pair.parent.contains(focus) ? 'parent' :
        snapshot.root_focus ? 'document' : 'outside';
    return {snapshot, child_visible: childVisible, layer};
}'''
SNAPSHOT = '() => window.__wcagDialogFocus()'
EXPECT_TARGET = 'e => { window.__wcagExpectedInputTarget = e; }'
CLEAR_TARGET = '() => { window.__wcagExpectedInputTarget = null; }'


def same_document(before, after):
    return all(before[key] == after[key] for key in ('document_start', 'url'))


def activation(action):
    return action['type'] == 'click' or (action['type'] == 'key' and action['key'] in {'Enter', 'Space'})


def activation_event(event, action):
    if event.get('expectedTargetMatched') is not True:
        return False
    if action['type'] == 'click':
        return event['type'] == 'click' and event['isTrusted'] and event['is_main_frame'] and event['pointerType'] == 'mouse'
    return matching_keydown(event, action['key'])


class DialogFocus:
    def __init__(self, page, observer, route, phase):
        self.page = page
        self.observer = observer
        self.close_step = len(route) - (phase == 'tab')
        self.close_action = route[self.close_step - 1]
        self.button = activation(self.close_action)
        self.opener = None
        self.opener_handle = None
        self.opener_event_index = None
        self.modal = None
        self.keyboard_only = phase == 'escape' and all(step['type'] in {'key', 'press'} for step in route)
        self.trap_start = None
        self.nested_pair = None
        self.nested_observation = None
        self.record = dict(phase=phase, close_action=self.close_action, status='unconfirmed',
                           reason='閉じる操作まで到達していない。')

    async def mark_target(self, action):
        target = self.page.locator(action['selector'])
        if await target.count() != 1:
            return None
        handle = await target.element_handle(timeout=1500)
        await handle.evaluate(EXPECT_TARGET)
        return handle

    async def before(self, index, action):
        self.initial = await self.page.evaluate(SNAPSHOT)
        self.input_start = len(self.observer.events)
        self.marked = None
        if index > self.close_step:
            if self.record['status'] != 'closed' or self.initial != self.record['after_close']:
                raise ValueError('再生時に閉じた直後の状態を確認できず、次のTabは未実施。')
        elif index < self.close_step and not self.initial['modals'] and activation(action):
            self.marked = await self.mark_target(action)
        elif index == self.close_step and len(self.initial['modals']) == 1:
            self.modal = await self.page.locator(self.initial['modals'][0]).element_handle(timeout=1500)
            if self.button:
                self.marked = await self.mark_target(action)
                if self.marked and not await self.modal.evaluate('(modal, button) => modal !== button && modal.contains(button)', self.marked):
                    await self.page.evaluate(CLEAR_TARGET)
                    self.marked = None
            elif self.keyboard_only and self.opener and self.initial['supported'] and not self.initial['root_focus']:
                start = await self.modal.evaluate(keyboard_trap.SNAPSHOT)
                if start['within']:
                    self.marked = await self.mark_target({'selector': self.initial['focus']})
                    if self.marked:
                        self.trap_start = start
        elif (index == self.close_step and self.record['phase'] == 'escape'
              and action['type'] == 'press' and action['key'] == 'Escape'
              and len(self.initial['modals']) == 2 and self.initial['supported'] and not self.initial['root_focus']):
            from playwright.async_api import Error as BrowserError

            with suppress(BrowserError):
                self.nested_pair = await self.page.evaluate_handle(NESTED_PAIR, self.initial)

    def event_index(self, matches):
        events = enumerate(self.observer.events[self.input_start:], self.input_start + 1)
        return next((i for i, event in events if matches(event)), None)

    async def after(self, index, action):
        current = await self.page.evaluate(SNAPSHOT)
        if self.marked or self.nested_pair:
            await self.page.evaluate(CLEAR_TARGET)
        if index < self.close_step:
            if self.initial['modals'] != current['modals']:
                self.opener = self.opener_handle = self.opener_event_index = None
                if self.marked and not self.initial['modals'] and same_document(self.initial, current):
                    match = self.event_index(lambda event: activation_event(event, action))
                    if not self.observer.dropped and match is not None:
                        self.opener, self.opener_handle = action['selector'], self.marked
                        self.opener_event_index = match
            return

        closing = index == self.close_step
        operation = action.get('key', 'クリック')
        if closing and self.button:
            event_index = self.event_index(lambda event: self.marked and activation_event(event, action))
        else:
            event_index = self.event_index(lambda event: matching_keydown(event, action['key']))
        if closing:
            self.record.update(opener=self.opener, before_close=self.initial, after_close=current,
                               opener_event_index=self.opener_event_index, close_event_index=event_index)
            if not self.button:
                # Keep the evidence keys read by previous Escape consumers.
                self.record.update(before_escape=self.initial, after_escape=current, escape_event_index=event_index)
            if self.nested_pair:
                self.nested_observation = await self.observe_nested_escape(current, event_index)
        else:
            self.record.update(after_tab=current, tab_event_index=event_index)

        if not self.initial['supported'] or not current['supported'] or not same_document(self.initial, current):
            self.invalidate('入力前後の同じ主文書とフォーカスを確認できない。')
        elif self.observer.dropped or event_index is None:
            self.invalidate(f'{operation}の実入力が対象に届いた記録を確認できない。')
        elif closing and self.modal is None:
            self.invalidate('閉じる前のモーダルダイアログを一つに特定できない。')
        elif current['modals']:
            if closing and self.button and self.initial['modals'] == current['modals']:
                self.record.update(status='not_dismissed', reason='入力後も同じダイアログが開いている。')
            else:
                self.invalidate('入力後も同じダイアログが開いている。' if self.initial['modals'] == current['modals']
                                else '入力後に別のダイアログが表示された。')
        elif closing and await self.modal.evaluate('e => window.__wcagDialogElementVisible(e)'):
            self.invalidate('モーダルの指定が変わった後もダイアログは表示されている。')
        else:
            self.record.update(status='closed', reason='')
            if closing:
                self.record['opener_restored'] = (
                    await self.opener_handle.evaluate('(e) => e.isConnected && document.activeElement === e')
                    if self.opener_handle else None)
            else:
                self.record['tab_moved_focus'] = self.initial['focus'] != current['focus']
                if self.opener_handle and self.initial['root_focus'] and not current['root_focus']:
                    self.record['tab_moved_before_opener'] = await self.opener_handle.evaluate("""e =>
                        window.__wcagDialogElementVisible(e) && e.tabIndex === 0 && !e.matches(':disabled') &&
                        !e.closest('[inert],[aria-disabled="true"]') && document.activeElement?.tabIndex === 0 &&
                        !!(e.compareDocumentPosition(document.activeElement) & Node.DOCUMENT_POSITION_PRECEDING)
                    """)

    async def observe_nested_escape(self, current, event_index):
        from playwright.async_api import Error as BrowserError

        before = self.initial
        if (self.observer.dropped or event_index is None or not current['supported']
                or not same_document(before, current)):
            return None
        event = self.observer.events[event_index - 1]
        if event.get('expectedTargetMatched') is not True or event['url'] != before['url']:
            return None
        parent, child = before['modals']
        try:
            observed = await self.nested_pair.evaluate(NESTED_STATE)
        except BrowserError:
            return None
        if not observed or observed['snapshot'] != current:
            return None
        if current['modals'] == [parent] and not observed['child_visible'] and observed['layer'] != 'child':
            status = 'child_closed'
        elif current['modals'] == [parent, child] and observed['child_visible']:
            status = 'child_open'
        else:
            return None
        return dict(parent=parent, child=child, status=status, before=before, after=current,
                    focus_layer=observed['layer'], key='Escape', event_index=event_index - 1,
                    input_evidence='input-events.json')

    async def opened_expected_child(self, parent, child):
        before, after = (self.record.get(name) for name in ('before_close', 'after_close'))
        if (self.observer.dropped or not self.record.get('opener_event_index') or not self.record.get('close_event_index')
                or not before or not after or not before['supported'] or not after['supported']
                or not same_document(before, after) or before['modals'] != [parent] or after['modals'] != [parent, child]):
            return False
        return await self.page.evaluate(f'snapshot => !!({NESTED_PAIR})(snapshot)', dict(after, mark_input=False))

    def invalidate(self, reason):
        self.record.update(status='unconfirmed', reason=reason)

    async def observe_keyboard_trap(self):
        from playwright.async_api import Error as BrowserError

        if self.trap_start is None:
            return False
        try:
            receipt = await keyboard_trap.probe(self.page, self.modal, self.marked, self.observer, self.trap_start,
                                                self.record, self.opener)
        except BrowserError:
            return True
        if receipt:
            self.record['keyboard_trap'] = receipt
        return bool(receipt and receipt['steps'])


def report_row(record, environment, evidence, route, capture):
    after = record.get('after_close', record.get('after_escape', {})).get('focus')
    next_focus = record.get('after_tab', {}).get('focus')
    action = record.get('close_action', {})
    operation = action.get('key', 'クリック') if action else 'Escape'
    if action.get('type') in {'click', 'key'}:
        operation = f'{action["selector"]} の{operation}'
    if record['status'] == 'closed' and record.get('opener_restored') is True:
        observed = f'{operation}で閉じた後、開く操作の対象 {record["opener"]} にフォーカスが戻った。'
    elif after:
        observed = f'{operation}後のフォーカス先は {after}。'
    else:
        observed = ''
    if next_focus:
        observed += f'次のTab後は {next_focus}。'
        if record.get('tab_moved_focus') is False:
            observed += 'Tabでフォーカス先が変わらなかった。'
    if record['reason']:
        observed += record['reason']
    elif record.get('opener_restored') is False:
        observed += '開く操作の対象と同じ要素への復帰は確認できなかった。'
    elif not record.get('opener'):
        observed += '開く操作の対象を特定できなかった。'

    outcome = 'cant_tell'
    if record['status'] == 'closed':
        if record.get('tab_moved_before_opener') is True:
            outcome = 'failed'
            observed += '閉じた直後にフォーカスが文書へ戻り、次のTabで開く操作の対象より前へ移動した。'
        elif record.get('opener_restored') is True and (
            record['phase'] != 'tab' or record.get('tab_moved_focus') is True
        ):
            outcome = 'passed'
    return dict(criterion='2.4.3', checkpoint='ダイアログを閉じた後のフォーカス',
                expected='閉じた後のフォーカスと、その後の操作を確認する',
                environment=environment, capture=capture, state_label=route, target=record.get('opener') or '',
                outcome=outcome, observed=observed, evidence=evidence, source='',
                dialog_focus=record, note='観測した経路の結果。別のフォーカス先が操作上適切かは追加確認。')
