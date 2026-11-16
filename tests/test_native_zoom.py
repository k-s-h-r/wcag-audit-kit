import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/wcag-audit-kit/scripts'))
from native_zoom import zoom_verified


class ZoomEvidenceTest(unittest.TestCase):
    baseline={'devicePixelRatio':1,'innerWidth':1280,'outerWidth':1280,'visualScale':1}

    def test_browser_zoom_with_stable_native_window(self):
        self.assertTrue(zoom_verified(self.baseline,{'devicePixelRatio':2,'innerWidth':640,'outerWidth':1280,'visualScale':1},2))
        self.assertTrue(zoom_verified(self.baseline,{'devicePixelRatio':4,'innerWidth':320,'outerWidth':1280,'visualScale':1},4))
        self.assertTrue(zoom_verified(self.baseline,{'devicePixelRatio':1.25,'innerWidth':1024,'outerWidth':1280,'visualScale':1},1.25))

    def test_viewport_change_is_not_zoom(self):
        self.assertFalse(zoom_verified(self.baseline,{'devicePixelRatio':1,'innerWidth':640,'outerWidth':640,'visualScale':1},2))

    def test_pinch_and_window_resize_are_not_accepted_as_browser_zoom(self):
        self.assertFalse(zoom_verified(self.baseline,{'devicePixelRatio':2,'innerWidth':640,'outerWidth':1280,'visualScale':2},2))
        self.assertFalse(zoom_verified(self.baseline,{'devicePixelRatio':2,'innerWidth':640,'outerWidth':1000,'visualScale':1},2))


if __name__=='__main__':unittest.main()
