import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/wcag-audit-kit/scripts'))
from measure import contrast,spacing


class MeasureTest(unittest.TestCase):
    def test_contrast(self):
        self.assertEqual(contrast('#000','#fff')['ratio'],21)
        self.assertFalse(contrast('#aaa','#fff')['meets_4_5'])
        self.assertTrue(contrast('#222','#fff')['meets_7'])

    def test_spacing_circles_not_just_rectangles(self):
        a={'id':'a','x':0,'y':0,'width':10,'height':10}
        b={'id':'b','x':20,'y':0,'width':10,'height':10}
        self.assertFalse(spacing([a,b])['targets'][0]['spacing_geometry_ok'])
        b['x']=24
        self.assertTrue(spacing([a,b])['targets'][0]['spacing_geometry_ok'])

    def test_spacing_against_large_target(self):
        a={'id':'a','x':0,'y':0,'width':10,'height':10}
        b={'id':'b','x':16,'y':0,'width':30,'height':30}
        self.assertFalse(spacing([a,b])['targets'][0]['spacing_geometry_ok'])
        b['x']=17
        self.assertTrue(spacing([a,b])['targets'][0]['spacing_geometry_ok'])


if __name__=='__main__':unittest.main()
