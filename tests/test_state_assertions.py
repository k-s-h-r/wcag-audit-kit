from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock,Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/wcag-audit-kit/scripts'))
from browser_capture import check_state


class StateAssertionTest(unittest.IsolatedAsyncioTestCase):
    def page(self,visible,text=''):
        locator=Mock(is_visible=AsyncMock(return_value=visible),inner_text=AsyncMock(return_value=text))
        return Mock(locator=Mock(return_value=locator))

    async def test_false_requires_actual_invisibility(self):
        with self.assertRaises(ValueError):
            await check_state(self.page(True),[{'selector':'#download','visible':False}])
        await check_state(self.page(False),[{'selector':'#download','visible':False}])

    async def test_text_must_match_actual_state(self):
        with self.assertRaises(ValueError):
            await check_state(self.page(True,'Not submitted'),[{'selector':'#status','text':'Saved'}])

    async def test_strings_do_not_substitute_for_boolean_assertions(self):
        with self.assertRaises(ValueError):
            await check_state(self.page(True),[{'selector':'#download','visible':'false'}])
