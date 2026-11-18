from importlib.util import find_spec
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/wcag-audit-kit/scripts'))
from border_contrast import border_definition, pixel_result, strip_pairs


class SolidBorderTest(unittest.TestCase):
    def test_computed_border_requires_opaque_solid_and_matching_sides(self):
        clean = ['2px', 'solid', 'rgb(85, 85, 85)']
        self.assertEqual(border_definition({'border': [clean] * 4}), (2, (85, 85, 85)))
        for mismatch in (['2px', 'double', clean[2]], ['1.5px', 'solid', clean[2]],
                         ['2px', 'solid', 'rgba(85, 85, 85, .5)'], ['2px', 'solid', 'rgb(70, 70, 70)']):
            with self.subTest(mismatch=mismatch), self.assertRaises(ValueError):
                border_definition({'border': [clean] * 3 + [mismatch]})

    def test_sampling_uses_chromium_rounded_css_edges(self):
        bounds = [15.5, 21.5, 70.5, 57.5]
        strips = {side: list(pairs) for side, pairs in strip_pairs(bounds, 1).items()}
        self.assertEqual(strips['top'][0], ((20, 22), (20, 21)))
        self.assertEqual(strips['bottom'][-1], ((66, 57), (66, 58)))
        self.assertEqual(strips['left'][0], ((16, 26), (15, 26)))
        self.assertEqual(strips['right'][-1], ((70, 53), (71, 53)))

    @unittest.skipUnless(find_spec('PIL'), 'Pillow from requirements-analysis.txt is needed')
    def test_numeric_ratio_requires_uniform_rendered_and_adjacent_pixels(self):
        from PIL import Image, ImageDraw

        bounds = [10, 12, 50, 44]
        border = (221, 221, 221)
        frame = Image.new('RGB', (64, 64), 'white')
        ImageDraw.Draw(frame).rectangle((10, 12, 49, 43), fill='white', outline=border)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'viewport.png'

            def sample():
                frame.save(path)
                data = {'viewport': [64, 64]}
                return pixel_result(path, data, 1, border, strip_pairs(bounds, 1))

            observed = sample()
            self.assertEqual(observed['status'], 'measured')
            self.assertAlmostEqual(observed['ratio'], 1.3582472461753565)
            self.assertFalse(observed['meets_3'])
            self.assertEqual(len(observed['samples']), 4)
            self.assertNotIn('outcome', observed)

            frame.putpixel((20, 12), (255, 255, 255))
            self.assertEqual(sample()['status'], 'cant_tell')
            frame.putpixel((20, 12), border)
            frame.putpixel((20, 11), (100, 100, 100))
            self.assertEqual(sample()['status'], 'cant_tell')
