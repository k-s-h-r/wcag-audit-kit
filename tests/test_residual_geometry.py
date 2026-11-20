from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/wcag-audit-kit/scripts'))

from benchmarks import residual_geometry as geometry


class ResidualGeometryTest(unittest.TestCase):
    def test_small_long_neighbor_intersects_circle_even_with_distant_center(self):
        current = dict(id='#target', x=0, y=0, width=16, height=16, explicit_size=True)
        neighbor = dict(id='#nearby', x=19, y=0, width=60, height=16, explicit_size=True)
        rows = geometry.evaluate(geometry.SIZE, {'targets': ['#target']},
                                 {'items': [current, neighbor], 'unresolved': False})
        self.assertEqual(rows[0]['outcome'], 'failed')
        self.assertIn('#nearby', rows[0]['observed'])

    def test_ambiguous_neighbor_preserves_uncertainty(self):
        current = dict(id='#target', x=0, y=0, width=16, height=16, explicit_size=True)
        rows = geometry.evaluate(geometry.SIZE, {'targets': ['#target']},
                                 {'items': [current], 'unresolved': True})
        self.assertEqual(rows[0]['outcome'], 'cant_tell')

    def test_focus_refuses_measurement_without_real_tab(self):
        plan = {'target': '#target'}
        rows = geometry.evaluate(geometry.FOCUS, plan, {'target': '#target', 'tab_events': []})
        self.assertEqual(rows[0]['outcome'], 'cant_tell')
