from pathlib import Path
import math
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    import numpy as np
    from focus_measure import analyse_arrays, reference_area
except ModuleNotFoundError:
    np=None


@unittest.skipIf(np is None,'Install requirements-analysis.txt for pixel measurement tests')
class FocusMeasureTest(unittest.TestCase):
    def pixels(self, rgb, size=4):
        return np.full((size,size,3),rgb,dtype=np.uint8)

    def test_adjacent_contrast_does_not_replace_same_pixel_contrast(self):
        # Both blues have strong contrast with white; their change is not 3:1.
        before=self.pixels([0,91,186]);after=self.pixels([0,92,187])
        r=analyse_arrays(before,after,np.ones((4,4),dtype=bool),1,{'width':90,'height':30})
        self.assertEqual(r['pixels_with_contrast_at_least_3'],0)
        self.assertLess(r['same_pixel_contrast_max'],3)
        self.assertIsNone(r['wcag_judgement'])

    def test_device_pixels_are_converted_to_css_area(self):
        r=analyse_arrays(self.pixels([255,255,255]),self.pixels([0,91,186]),
                         np.ones((4,4),dtype=bool),2,{'width':90,'height':30})
        self.assertEqual(r['pixels_with_contrast_at_least_3'],16)
        self.assertEqual(r['qualifying_area_css_px2'],4)
        self.assertEqual(r['reference_area_css_px2'],480)  # W3C's 90×30 example.

    def test_values_below_three_are_not_rounded_up(self):
        before=self.pixels([0,0,0])
        mask=np.ones((4,4),dtype=bool)
        low=analyse_arrays(before,self.pixels([89,89,89]),mask,1,{'width':90,'height':30})
        high=analyse_arrays(before,self.pixels([90,90,90]),mask,1,{'width':90,'height':30})
        self.assertEqual(low['pixels_with_contrast_at_least_3'],0)
        self.assertEqual(high['pixels_with_contrast_at_least_3'],16)

    def test_only_identified_indicator_pixels_are_counted(self):
        mask=np.zeros((4,4),dtype=bool);mask[0,0]=True
        r=analyse_arrays(self.pixels([255,255,255]),self.pixels([0,0,0]),mask,1,
                         {'width':90,'height':30})
        self.assertEqual(r['candidate_device_pixels'],1)
        self.assertEqual(r['qualifying_area_css_px2'],1)

    def test_invalid_density_or_unmatched_frames_are_not_measurements(self):
        a=self.pixels([255,255,255]);mask=np.ones((4,4),dtype=bool)
        for dpr in [True,0,float('nan'),1e308]:
            with self.assertRaises(ValueError):
                analyse_arrays(a,a,mask,dpr,{'width':90,'height':30})
        with self.assertRaises(ValueError):
            analyse_arrays(a,self.pixels([0,0,0],2),mask,1,{'width':90,'height':30})

    def test_shape_geometry_and_dimensions_are_checked(self):
        self.assertAlmostEqual(reference_area({'width':20,'height':20},'circle',10),40*math.pi)
        with self.assertRaises(ValueError):
            reference_area({'width':30,'height':20},'circle',10)
        with self.assertRaises(ValueError):
            reference_area({'width':90,'height':30},'rounded_rectangle',16)


if __name__=='__main__':
    unittest.main()
