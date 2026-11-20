import unittest

from benchmarks import residual_structure


class ResidualStructureTest(unittest.TestCase):
    def test_plan_accepts_only_public_observation_fields(self):
        for criterion, plan in (
            ('1.3.1', {'target': '#example', 'axes': ['row']}),
            ('1.3.5', {'target': '#example', 'purpose': 'name'}),
            ('4.1.2', {'target': '#example', 'controlled': '#panel'}),
        ):
            residual_structure.validate_plan(criterion, plan)
            with self.assertRaises(ValueError):
                residual_structure.validate_plan(criterion, {**plan, 'expected': 'passed'})
            with self.assertRaises(ValueError):
                residual_structure.validate_plan(criterion, {**plan, 'target': 'button > a'})
            result, = residual_structure.evaluate(criterion, plan, {})
            self.assertEqual(result['outcome'], 'cant_tell')

    def test_input_purpose_uses_browser_interpretation(self):
        plan = {'target': '#input', 'purpose': 'name'}
        for parsed, attribute, expected in (
            ('section-user shipping name', 'section-user shipping name', 'passed'),
            ('', 'unexpected name', 'failed'),
            ('family-name', 'family-name', 'failed'),
        ):
            result, = residual_structure.evaluate('1.3.5', plan, {
                'input': {'autocomplete': parsed, 'attribute': attribute},
            })
            self.assertEqual(result['outcome'], expected)

    def test_disclosure_requires_state_to_match_visibility_change(self):
        plan = {'target': '#control', 'controlled': '#panel'}
        button = {'exposed': True, 'role': 'button', 'name': '詳細'}
        evidence = {'before': {'visible': False, 'ax': {**button, 'expanded': False}},
                    'after': {'visible': True, 'ax': {**button, 'expanded': True}}}
        result, = residual_structure.evaluate('4.1.2', plan, evidence)
        self.assertEqual(result['outcome'], 'passed')
        evidence['after']['ax']['expanded'] = False
        result, = residual_structure.evaluate('4.1.2', plan, evidence)
        self.assertEqual(result['outcome'], 'failed')
        evidence['after']['visible'] = False
        result, = residual_structure.evaluate('4.1.2', plan, evidence)
        self.assertEqual(result['outcome'], 'cant_tell')
