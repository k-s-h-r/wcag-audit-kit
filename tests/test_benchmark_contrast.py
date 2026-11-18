from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from benchmarks import core


class ContrastPredictionTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.run = Path(temp.name)
        self.root = self.run / 'evidence'
        self.job = {'id': 'contrast', 'checkpoints': ['1.4.3-01'], 'states': [{'id': 'initial'}]}
        self.progress = {'jobs': {'contrast': {'p.html': {'status': 'completed', 'directory': 'evidence'}}}}

    def predict(self, group, data, target=None, route=None, transition=None, records=None):
        route = route or []
        node = {'target': target or ['#text'], 'any': [{'id': 'color-contrast', 'data': data}]}
        core.save(self.root / 'one/axe.json', {group: [{'id': 'color-contrast', 'nodes': [node]}]})
        core.save(self.root / 'one/transition.json', transition or {'route': route})
        core.save(self.root / 'one/state.json', {'state_labels': records or []})
        core.save(self.root / 'exploration.json', {'nodes': [{'route': route, 'evidence_dir': 'one'}]})
        return core.program_predictions(self.run, self.job, self.progress)

    def data(self, ratio, minimum, size='12.0pt (16px)', weight='normal'):
        return {'contrastRatio': ratio, 'expectedContrastRatio': minimum, 'fontSize': size,
                'fontWeight': weight, 'fgColor': '#aaaaaa', 'bgColor': '#ffffff'}

    def test_preserves_measured_ratio_and_threshold_for_exact_target(self):
        normal = self.predict('violations', self.data(2.32, '4.5:1'))
        key = ('p.html', 'initial', '#text', '1.4.3-01')
        self.assertEqual(list(normal), [key])
        self.assertEqual(normal[key]['outcome'], 'failed')
        self.assertIn('2.32:1', normal[key]['observed'])
        self.assertIn('4.5:1', normal[key]['observed'])
        self.assertEqual(normal[key]['evidence'], ['evidence/one/axe.json'])

        large = self.predict('passes', self.data(3.8, '3:1', '14.0pt (18.667px)', 'bold'))
        self.assertEqual(large[key]['outcome'], 'passed')
        self.assertIn('比較基準は3:1', large[key]['observed'])
        self.assertIn('bold', large[key]['observed'])

    def test_uncertain_and_inapplicable_targets_do_not_become_passes(self):
        key = ('p.html', 'initial', '#text', '1.4.3-01')
        self.assertEqual(self.predict('incomplete', None)[key]['outcome'], 'cant_tell')
        self.assertEqual(self.predict('passes', None)[key]['outcome'], 'cant_tell')
        self.assertEqual(self.predict('inapplicable', None), {})
        self.assertEqual(self.predict('passes', self.data(18, '4.5:1'), target=['iframe', '#text']), {})
        self.job['checkpoints'] = ['1.4.3-02']
        self.assertEqual(self.predict('violations', self.data(2.32, '4.5:1')), {})

    def test_enabled_state_requires_matching_route_condition_and_evidence(self):
        route = [{'type': 'click', 'selector': '#enable'}]
        self.job['states'] = [{'id': 'enabled', 'actions': route,
                               'assert': [{'selector': '#text:enabled', 'count': 1, 'visible': True}]}]
        data = self.data(2.32, '4.5:1')
        self.assertEqual(self.predict('violations', data), {})
        self.assertEqual(self.predict('violations', data, route=route), {})

        evidence = {'id': 'enabled', 'actions': route, 'matched': True,
                    'assertions': [{'selector': '#text:enabled', 'count': 1, 'visible': True}]}
        key = ('p.html', 'enabled', '#text', '1.4.3-01')
        result = self.predict('violations', data, route=route, records=[evidence])
        self.assertEqual(result[key]['outcome'], 'failed')
        self.assertIn('evidence/one/transition.json', result[key]['evidence'])
        self.assertIn('evidence/one/state.json', result[key]['evidence'])
        self.assertEqual(self.predict('violations', data, route=route, records=[evidence],
                                      transition={'route': route, 'blocked_requests': [{'url': '/write'}]}), {})
