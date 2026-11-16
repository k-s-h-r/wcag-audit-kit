from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/wcag-audit-kit/scripts'))
from input_observation import InputObserver


class InputObservationTest(unittest.IsolatedAsyncioTestCase):
    def source(self):
        frame=object();return {'frame':frame,'page':SimpleNamespace(main_frame=frame)}

    async def test_synthetic_or_wrong_target_is_not_accepted_as_pointer_input(self):
        for trusted,matched in [(False,True),(True,False)]:
            observer=InputObserver();observer.accept(self.source(),{'type':'pointerdown','isTrusted':trusted,'expectedTargetMatched':matched})
            with self.assertRaises(ValueError):await observer.pointer_down_after(0)

    async def test_trusted_input_is_retained_and_truncation_explicit(self):
        observer=InputObserver(limit=1);event={'type':'pointerdown','isTrusted':True,'expectedTargetMatched':True}
        observer.accept(self.source(),event);self.assertTrue((await observer.pointer_down_after(0))['isTrusted'])
        observer.accept(self.source(),event)
        self.assertTrue(observer.export()['truncated']);self.assertEqual(observer.export()['dropped'],1)
