import copy
from pathlib import Path
import struct
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, Mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/wcag-audit-kit/scripts'))
from focus_image_pair import FocusImagePair
from inspection import ImageBudget


def state(*, focused=False, x=0, in_viewport=True, time_origin=1):
    return {
        'connected': True, 'same_target': True,
        'url': 'https://example.invalid', 'time_origin': time_origin,
        'rect': {'left': x}, 'viewport': {'width': 40, 'height': 30}, 'scroll': {'x': 0, 'y': 0},
        'document_focused': True, 'focused': focused, 'focus_visible': focused, 'in_viewport': in_viewport,
    }


class FocusImagePairTests(unittest.IsolatedAsyncioTestCase):
    def initialize(self, screenshots='all', limit=2):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.images = ImageBudget({'inspection': {'screenshots': screenshots, 'max_images': limit}},
                                  self.root, {}, None)
        self.images.page = 'example'
        self.page = Mock()
        self.scope = self.page.main_frame
        self.scope.page = self.page
        self.page.screenshot = AsyncMock(return_value=b'\x89PNG\r\n\x1a\n' + bytes(8) + struct.pack('>II', 40, 30))
        self.pair = FocusImagePair(self.scope, '#subject', self.images, self.root)

    def mock_states(self, before, after, *, same_target=True):
        first = Mock(evaluate=AsyncMock(side_effect=[copy.deepcopy(before), copy.deepcopy(before)]), dispose=AsyncMock())
        second = Mock(evaluate=AsyncMock(side_effect=[copy.deepcopy(after), same_target, copy.deepcopy(after)]),
                      dispose=AsyncMock())
        locator = Mock(count=AsyncMock(return_value=1), element_handle=AsyncMock(side_effect=[first, second]))
        self.scope.locator.return_value = locator

    async def capture(self):
        await self.pair.before()
        await self.pair.after()
        await self.pair.close()
        return self.pair.receipt

    async def test_mode_and_total_budget_skip_both_images(self):
        for config, reason in [(('off', 0), 'screenshots_off'), (('states', 2), 'states_only'),
                               (('all', 1), 'image_limit')]:
            self.initialize(*config)
            receipt = await self.capture()
            self.assertEqual((receipt['status'], receipt['reason_code']), ('skipped', reason))
            self.page.screenshot.assert_not_awaited()
            self.assertEqual(self.images.counts, {})

    async def test_before_after_proof_records_matching_conditions(self):
        self.initialize()
        self.mock_states(state(), state(focused=True))
        receipt = await self.capture()
        self.assertEqual(receipt['status'], 'captured')
        self.assertFalse(receipt['before']['focused'])
        self.assertTrue(receipt['after']['focused'])
        for phase in ('before', 'after'):
            self.assertTrue((self.root / receipt[phase]['image']).is_file())
            self.assertEqual(receipt[phase]['pixels'], {'width': 40, 'height': 30})

    async def test_offscreen_or_changed_geometry_retains_both_images(self):
        for after, reason in [(state(focused=True, in_viewport=False), 'target_offscreen'),
                              (state(focused=True, x=25), 'geometry_changed')]:
            self.initialize()
            self.mock_states(state(), after)
            receipt = await self.capture()
            self.assertEqual((receipt['status'], receipt['reason_code']), ('incomparable', reason))
            self.assertEqual(set(self.root.glob('*.png')),
                             {self.root / receipt[stage]['image'] for stage in ('before', 'after')})

    async def test_replacement_reloads_are_partial(self):
        for snapshot, same_target, reason in [(state(focused=True), False, 'target_changed'),
                                              (state(focused=True, time_origin=2), True, 'document_changed')]:
            self.initialize()
            self.mock_states(state(), snapshot, same_target=same_target)
            receipt = await self.capture()
            self.assertEqual((receipt['status'], receipt['reason_code']), ('partial', reason))
            self.assertNotIn('image', receipt['after'])
            self.page.screenshot.assert_awaited_once()

    async def test_second_image_error_keeps_first_image_and_manifest(self):
        self.initialize()
        self.mock_states(state(), state(focused=True))
        self.page.screenshot.side_effect = [self.page.screenshot.return_value, RuntimeError('capture failed')]
        receipt = await self.capture()
        self.assertEqual((receipt['status'], receipt['reason_code']), ('partial', 'capture_error'))
        self.assertTrue((self.root / receipt['before']['image']).is_file())
        self.assertNotIn('image', receipt['after'])
        self.assertEqual([row['status'] for row in self.images.summary['screenshots']], ['captured', 'error'])


if __name__ == '__main__':
    unittest.main()
