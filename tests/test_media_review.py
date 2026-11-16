import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/wcag-audit-kit/scripts'))
from media_review import validate_review


class MediaReviewTest(unittest.TestCase):
    def setUp(self):
        self.review = {'source': 'video#clip, original English audio and English captions',
            'timeline': 'prerecorded', 'duration': 7.008,
            'comparison': '単体試験用の全区間の情報と代替の比較。実媒体を見た記録ではない。',
            'intervals': [{'start': 0, 'end': 3.5, 'status': 'reviewed',
                'observed': '単体試験の前半の観察を表すテキスト。', 'expected': '前半の情報と代替が対応すること。',
                'evidence': ['first.json']}, {'start': 3.5, 'end': 7.008, 'status': 'reviewed',
                'observed': '単体試験の後半の観察を表すテキスト。', 'expected': '後半の情報と代替が対応すること。',
                'evidence': ['second.json']}]}

    def test_full_intervals_pass_and_missing_middle_or_tail_do_not(self):
        self.assertEqual(validate_review(self.review, True), ['first.json', 'second.json'])
        for where in ['middle', 'tail']:
            value = copy.deepcopy(self.review)
            if where == 'middle':value['intervals'][1]['start'] = 4
            else:value['intervals'][1]['end'] = 7
            with self.subTest(where=where), self.assertRaises(ValueError):
                validate_review(value, True)

    def test_covered_union_does_not_hide_an_explicitly_unreviewed_aspect(self):
        value = copy.deepcopy(self.review)
        value['intervals'].append({'start': 0, 'end': 7.008, 'status': 'not_reviewed',
                                  'reason': '音声を聴取する方法がなく、この区間の音の意味は未確認。'})
        with self.assertRaises(ValueError):validate_review(value, True)
        self.assertEqual(validate_review(value, False), ['first.json', 'second.json'])

    def test_bool_nonfinite_negative_and_outside_times_are_rejected(self):
        for key, number in [('duration', True), ('duration', float('inf')), ('start', -1),
                            ('start', float('nan')), ('end', 20)]:
            value = copy.deepcopy(self.review)
            if key == 'duration':value[key] = number
            else:value['intervals'][0][key] = number
            with self.subTest(key=key, number=number), self.assertRaises(ValueError):
                validate_review(value, False)

    def test_live_review_requires_the_actual_observation_window(self):
        value = copy.deepcopy(self.review);value['timeline'] = 'live_window'
        with self.assertRaises(ValueError):validate_review(value, True)
        value['window_description'] = '単体試験の仮の観察窓。実配信を確認した記録ではない。'
        self.assertEqual(validate_review(value, True), ['first.json', 'second.json'])
