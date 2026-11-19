import math
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

    def test_persistence_is_opt_in_and_duration_is_bounded(self):
        check = dict(CHECK, persistence_ms=600)
        self.assertEqual(hover_checks.validate_check(check), check)
        for value in (None, False, 99, 3001, 600.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                hover_checks.validate_check(dict(CHECK, persistence_ms=value))
        record = {}
        hover_checks.invalidate(record, check, 'Browser changed')
        self.assertEqual([item['aspect'] for item in record['observations']],
                         ['hoverable', 'dismissible', 'persistent'])

    async def test_popup_reposition_is_unknown_when_it_no_longer_contains_the_pointer(self):
        point = {'x': 30, 'y': 54}
        hit = dict(point, hits_target=True)
        previous = {'status': 'visible', 'points': [hit]}
        after = {'status': 'visible', 'points': []}
        opened = {'trigger': {'rect': {'right': 21}}, 'point': {'x': 29, 'y': 54}}
        record = {'steps': []}

        async def move(page, popup, point, observer, step):
            step['input_event_index'] = 2
            step['input_target_matched'] = True

        with (patch.object(hover_checks, 'target_state', new=AsyncMock(side_effect=[previous, after, after])) as state,
              patch.object(hover_checks, 'pointer_move', new=move),
              patch.object(hover_checks, 'require_continuity', new=AsyncMock()),
              patch.object(hover_checks, 'settle', new=AsyncMock())):
            with self.assertRaises(hover_checks.Uncertain):
                await hover_checks.transfer(Mock(), '#tip', opened, Mock(), record, Mock(), [])
        state.assert_awaited_with('#tip', at=point)

    def test_transfer_points_are_bounded_and_end_at_the_configured_target(self):
        start, end = {'x': 3, 'y': 9}, {'x': 76, 'y': 71}
        points = hover_checks.transfer_points(start, end)
        self.assertEqual(points[-1], end)
        self.assertLessEqual(len(points), hover_checks.MAX_TRANSFER_SAMPLES)
        for left, right in zip([start, *points], points):
            self.assertLessEqual(math.dist(tuple(left.values()), tuple(right.values())), 4)
        with self.assertRaises(hover_checks.Uncertain):
            hover_checks.transfer_points(start, {'x': 1000, 'y': 90})

    def test_interrupted_path_invalidates_results_and_keeps_raw_steps(self):
        record = {'steps': [{'input_event_index': 2}], 'outcome': 'passed', 'observations': []}
        hover_checks.invalidate(record, CHECK, 'Page changed')
        self.assertEqual(record['outcome'], 'cant_tell')
        self.assertEqual(record['steps'][0]['input_event_index'], 2)
        self.assertEqual([item['outcome'] for item in record['observations']], ['cant_tell', 'cant_tell'])
