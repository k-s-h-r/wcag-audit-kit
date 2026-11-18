from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/wcag-audit-kit/scripts'))
import keyboard_checks


class WidgetConditionTest(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def config(criterion, *steps):
        return {'keyboard_checks': [{'id': 'widget', 'name': 'Widget route',
                                     'criterion': criterion, 'steps': list(steps)}]}

    def test_aria_route_requires_an_attribute_condition(self):
        with self.assertRaisesRegex(ValueError, 'attributes'):
            keyboard_checks.validate(self.config('4.1.2', {'key': 'ArrowRight', 'focus': '#second'}))
        config = self.config('4.1.2', {'key': 'ArrowRight', 'attributes': [
            {'selector': '#second', 'name': 'aria-selected', 'equals': 'true'}]})
        self.assertEqual(keyboard_checks.validate(config), config['keyboard_checks'])

    async def test_only_explicit_null_matches_a_missing_attribute(self):
        element = Mock(count=AsyncMock(return_value=1), get_attribute=AsyncMock(return_value=None))
        missing = Mock(count=AsyncMock(return_value=0))
        page = Mock(locator=Mock(side_effect={'#widget': element, '#missing': missing}.__getitem__))
        step = {'key': 'Escape', 'attributes': [
            {'selector': '#widget', 'name': 'aria-activedescendant', 'equals': None},
            {'selector': '#widget', 'name': 'aria-activedescendant', 'equals': ''},
            {'selector': '#missing', 'name': 'aria-activedescendant', 'equals': None},
        ]}
        observed = await keyboard_checks.observe_conditions(page, step, None)
        self.assertEqual([item['matched'] for item in observed], [True, False, False])
        self.assertEqual([item['found'] for item in observed], [True, True, False])
        self.assertEqual([item['actual'] for item in observed], [None, None, None])

    def test_invalid_state_conditions_are_rejected_before_the_route_runs(self):
        for step in [
            {'key': 'Escape', 'attributes': []},
            {'key': 'Escape', 'attributes': [{'selector': '#widget', 'name': 'aria-expanded'}]},
            {'key': 'Escape', 'attributes': [{'selector': '#widget', 'name': 'aria-expanded', 'equals': True}]},
            {'key': 'Escape', 'attributes': [{'selector': '#widget', 'name': 'style', 'equals': 'display:none'}]},
            {'key': 'Enter', 'value': {'selector': '#widget', 'equals': None}},
        ]:
            with self.subTest(step=step), self.assertRaises(ValueError):
                keyboard_checks.validate(self.config('2.1.1', step))

    async def test_live_text_value_distinguishes_blank_field_from_wrong_target_type(self):
        field = Mock(count=AsyncMock(return_value=1), evaluate=AsyncMock(return_value=''))
        page = Mock(locator=Mock(return_value=field))
        step = {'key': 'Escape', 'value': {'selector': '#widget', 'equals': ''}}
        observed, = await keyboard_checks.observe_conditions(page, step, None)
        self.assertTrue(observed['matched'])
        self.assertEqual(observed['actual'], '')
        field.evaluate.return_value = None
        with self.assertRaisesRegex(ValueError, '入力欄'):
            await keyboard_checks.observe_conditions(page, step, None)

    def test_report_cites_wrong_dom_state_separately_from_focus(self):
        focus = {'id': 'widget', 'documentHasFocus': True}
        result = {'criterion': '4.1.2', 'id': 'widget', 'name': 'Widget route', 'outcome': 'failed',
                  'steps': [{'index': 2, 'key': 'ArrowDown', 'before': focus, 'after': focus, 'conditions': [
                      {'kind': 'attribute', 'selector': '#widget', 'name': 'aria-expanded',
                       'actual': 'false', 'expected': 'true', 'found': True, 'matched': False},
                  ]}]}
        row = keyboard_checks.report_row(result, 'desktop', 'evidence/keyboard-check.json')
        self.assertIn('aria-expanded が "true"（実際: "false"）', row['observed'])
        self.assertIn('実際のフォーカスは#widget', row['observed'])
        self.assertIn('支援技術での通知は追加確認', row['note'])

    def test_only_matching_trusted_arrow_key_can_certify_delivery(self):
        event = {'type': 'keydown', 'isTrusted': True, 'is_main_frame': True, 'key': 'ArrowDown',
                 'modifiers': {'control': False, 'shift': False, 'alt': False, 'meta': False}}
        self.assertTrue(keyboard_checks.matching_keydown(event, 'ArrowDown'))
        self.assertFalse(keyboard_checks.matching_keydown(event, 'ArrowUp'))
        self.assertFalse(keyboard_checks.matching_keydown(dict(event, isTrusted=False), 'ArrowDown'))
        modified = dict(event, modifiers=dict(event['modifiers'], control=True))
        self.assertFalse(keyboard_checks.matching_keydown(modified, 'ArrowDown'))
