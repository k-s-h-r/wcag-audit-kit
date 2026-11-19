import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/wcag-audit-kit/scripts'))
from orca_log import speech_in_window


class OrcaSpeechWindowTests(unittest.TestCase):
    def test_buffered_prior_output_and_event_text_are_not_current_speech(self):
        text = "\n".join([
            "18:19:36.084166 - SPEECH OUTPUT: 'Save button.' {}",
            "18:19:40.332886 - EVENT: Record two saved.",
            "18:19:40.442601 - SPEECH OUTPUT: 'Record two saved.' {}",
            "18:19:40.442607 - SPEECH DISPATCHER: Speaking 'Record two saved.' as string",
            "18:19:42.554122 - SPEECH OUTPUT: 'Record three saved.' {}",
        ])
        rows = speech_in_window(text, '2026-11-14T18:19:40+00:00', '2026-11-14T18:19:42+00:00')
        self.assertEqual([row['phrase'] for row in rows], ['Record two saved.'])
        self.assertEqual(rows[0]['line'], 3)

    def test_voice_metadata_can_follow_the_phrase_without_a_space(self):
        line = "04:50:21.777830 - SPEECH OUTPUT: '保存しました'{'established': 'False'}"
        malformed = "04:50:21.778000 - SPEECH OUTPUT: 'not an utterance'suffix"
        rows = speech_in_window(
            f'{line}\n{malformed}', '2026-11-19T04:50:21+00:00', '2026-11-19T04:50:22+00:00',
        )
        self.assertEqual([row['phrase'] for row in rows], ['保存しました'])
        self.assertEqual(rows[0]['raw'], line)

    def test_midnight_and_escaped_phrase(self):
        text = "23:59:59.900000 - SPEECH OUTPUT: 'Before.' {}\n00:00:00.100000 - SPEECH OUTPUT: 'It\\'s saved.' {}"
        rows = speech_in_window(text, '2026-11-14T23:59:59.950000+00:00', '2026-11-15T00:00:01+00:00')
        self.assertEqual([row['phrase'] for row in rows], ["It's saved."])
        self.assertTrue(rows[0]['at'].startswith('2026-11-15'))

    def test_time_zone_or_invalid_window_is_not_silently_guessed(self):
        for start, end in [('2026-11-14T12:00:00', '2026-11-14T12:00:01'),
                           ('2026-11-14T12:00:00+09:00', '2026-11-14T12:00:01+09:00'),
                           ('2026-11-14T12:00:00Z', '2026-11-15T12:00:00Z'),
                           ('2026-11-14T12:00:01Z', '2026-11-14T12:00:00Z')]:
            with self.subTest(start=start), self.assertRaises(ValueError):
                speech_in_window('', start, end)


if __name__ == '__main__':
    unittest.main()
