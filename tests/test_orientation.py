import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/wcag-audit-kit/scripts'))
from orientation_probe import rotation_verified, valid_geometry


class OrientationObservationTest(unittest.TestCase):
    def setUp(self):
        self.viewport = {'width': 600, 'height': 900}
        self.metrics = {'width': 600, 'height': 900, 'dpr': 1, 'screenWidth': 600,
            'screenHeight': 900, 'type': 'portrait-primary', 'angle': 0,
            'portrait': True, 'landscape': False, 'scale': 1}

    def test_css_portrait_alone_is_not_a_verified_screen_orientation(self):
        self.assertTrue(rotation_verified(self.metrics, self.viewport, 'portrait-primary'))
        wrong = copy.deepcopy(self.metrics)
        wrong.update(screenWidth=900, screenHeight=600, type='landscape-primary', angle=90)
        self.assertFalse(rotation_verified(wrong, self.viewport, 'portrait-primary'))
        wrong = {**self.metrics, 'scale': 2}
        self.assertFalse(rotation_verified(wrong, self.viewport, 'portrait-primary'))

    def test_secondary_orientation_requires_the_corresponding_angle(self):
        self.assertFalse(rotation_verified(self.metrics, self.viewport, 'portrait-secondary'))
        metrics = {**self.metrics, 'type': 'portrait-secondary', 'angle': 180}
        self.assertTrue(rotation_verified(metrics, self.viewport, 'portrait-secondary'))

    def test_wrong_geometry_is_rejected_before_the_probe(self):
        for viewport, orientation in [({'width': True, 'height': 900}, 'portrait-primary'),
                ({'width': 900, 'height': 600}, 'portrait-primary'),
                ({'width': 600, 'height': 600}, 'portrait-primary'),
                (self.viewport, 'portrait'), (self.viewport, 'landscape-primary')]:
            with self.subTest(viewport=viewport, orientation=orientation), self.assertRaises(ValueError):
                valid_geometry(viewport, orientation)


if __name__ == '__main__':
    unittest.main()
