"""Keyboard functional scoring must follow the measured effect and input."""

import copy
import unittest

from benchmarks import residual_keyboard as keyboard


class ResidualKeyboardTest(unittest.TestCase):
    url = 'http://127.0.0.1/2.1.1/control.html'

    def setUp(self):
        self.plan = {
            'target': '#feature',
            'keyboard': [{'selector': '#control', 'keys': ['Enter', 'Space'], 'reach': 'tab'}],
            'pointer': ['#alternative'],
            'result': {'kind': 'increase', 'selector': '#counter'},
        }
        self.measurement = {
            'initial_url': self.url,
            'pointer': self.trial('#alternative', None, 1),
            'keyboard': [self.trial('#control', key, 0) for key in ('Enter', 'Space')],
        }

    def trial(self, selector, key, result):
        action = {'selector': selector}
        if key:
            action.update(key=key, reach='tab')
        return {
            'actions': [action], 'before': {'url': self.url, 'number': 0}, 'after': {'url': self.url, 'number': result},
            'steps': [{'status': 'delivered', 'tabs': int(key is not None), 'event': {
                'type': 'keydown' if key else 'click', 'key': ' ' if key == 'Space' else key,
                'trusted': True, 'target_match': True,
            }}],
        }

    def outcome(self):
        return keyboard.evaluate('2.1.1', self.plan, self.measurement)[0]['outcome']

    def test_passing_alternative_does_not_require_every_key(self):
        self.assertEqual(self.outcome(), 'failed')
        self.measurement['keyboard'][1]['after']['number'] = 1
        self.assertEqual(self.outcome(), 'passed')

    def test_failure_requires_all_routes_and_a_working_pointer_control(self):
        self.measurement['keyboard'][0]['steps'][0]['event']['target_match'] = False
        self.assertEqual(self.outcome(), 'cant_tell')
        self.measurement['pointer']['after']['number'] = 0
        self.assertEqual(self.outcome(), 'cant_tell')

    def test_arbitrary_navigation_or_undelivered_input_cannot_pass(self):
        trial = self.measurement['keyboard'][0]
        trial['after'] = {'url': self.url + '?changed', 'number': 1}
        self.assertEqual(self.outcome(), 'cant_tell')
        trial['after']['url'] = self.url
        trial['steps'][0]['event']['trusted'] = False
        self.assertEqual(self.outcome(), 'cant_tell')

    def test_plans_cannot_encode_verdicts_or_unbounded_routes(self):
        for invalid in (dict(self.plan, expected='failed'), dict(self.plan, target='main button')):
            with self.subTest(plan=invalid), self.assertRaises(ValueError):
                keyboard.validate_plan('2.1.1', invalid)
        unbounded = copy.deepcopy(self.plan)
        unbounded['keyboard'] *= 4
        with self.assertRaises(ValueError):
            keyboard.validate_plan('2.1.1', unbounded)


if __name__ == '__main__':
    unittest.main()
