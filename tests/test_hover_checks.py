from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/wcag-audit-kit/scripts'))
import hover_checks


CHECK = {'id': 'price', 'name': '料金表示', 'trigger': '#subject', 'popup': '#tip'}


class HoverChecksTest(unittest.IsolatedAsyncioTestCase):
    def test_invalid_paths_are_rejected_at_validation(self):
        self.assertEqual(hover_checks.validate_check(CHECK), CHECK)
        for override in ({'id': 'space here'}, {'popup': ' '}, {'trigger': '#tip'}, {'steps': []}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                hover_checks.validate_check(dict(CHECK, **override))

    async def test_popup_reposition_is_unknown_when_it_no_longer_contains_the_pointer(self):
        point = {'x': 30, 'y': 54}
        hit = dict(point, hits_target=True)
        previous = {'status': 'visible', 'points': [hit]}
        after = {'status': 'visible', 'points': []}
        opened = {'trigger': {'rect': {'right': 21}}}
        record = {'steps': []}

        async def move(page, popup, point, observer, step):
            step['input_target_matched'] = True

        with (patch.object(hover_checks, 'target_state', new=AsyncMock(side_effect=[previous, after])) as state,
              patch.object(hover_checks, 'pointer_move', new=move),
              patch.object(hover_checks, 'settle', new=AsyncMock())):
            with self.assertRaises(hover_checks.Uncertain):
                await hover_checks.transfer(Mock(), '#tip', opened, Mock(), record, Mock(), [])
        state.assert_awaited_with('#tip', at=point)

    def test_interrupted_path_invalidates_results_and_keeps_raw_steps(self):
        record = {'steps': [{'input_event_index': 2}], 'outcome': 'passed', 'observations': []}
        hover_checks.invalidate(record, CHECK, 'Page changed')
        self.assertEqual(record['outcome'], 'cant_tell')
        self.assertEqual(record['steps'][0]['input_event_index'], 2)
        self.assertEqual([item['outcome'] for item in record['observations']], ['cant_tell', 'cant_tell'])
