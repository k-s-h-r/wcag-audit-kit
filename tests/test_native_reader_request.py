from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from screen_reader_native import validate, origin, transcript_assertion


class NativeReaderRequestTest(unittest.TestCase):
    def setUp(self):
        self.request = {'url': 'https://example.com/page', 'case_id': 'case',
                        'actions': [{'type': 'reader.nextHeading'}]}

    def test_actual_reader_commands_are_accepted_and_other_functions_rejected(self):
        self.assertEqual(validate(self.request), ['https://example.com'])
        for kind in ['reader.stop', 'virtual.next', 'browser.evaluate']:
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validate({**self.request, 'actions': [{'type': kind}]})

    def test_invalid_origins_and_credentials_are_rejected(self):
        for url in ['file:///tmp/page.html', 'https://user:secret@example.com', None]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate({**self.request, 'url': url})
        with self.assertRaises(ValueError):
            validate({**self.request, 'allowed_origins': ['https://other.example']})
        self.assertEqual(origin('HTTPS://EXAMPLE.com:443/a'), 'https://example.com')

    def test_boolean_timeouts_empty_expectations_and_invalid_actions_do_not_run(self):
        for request in [[], {**self.request, 'settle_ms': True},
                {**self.request, 'actions': ['reader.nextHeading']},
                {**self.request, 'actions': [{'type': 'reader.press', 'keys': []}]},
                {**self.request, 'actions': [{'type': 'reader.nextHeading', 'expect_not_contains': ['']}]},
                {**self.request, 'actions': [{'type': 'reader.nextHeading', 'expect_contains': ''}]}]:
            with self.subTest(request=request), self.assertRaises(ValueError):
                validate(request)

    def test_negative_state_word_is_not_accepted_as_the_positive_state(self):
        action = {'expect_contains': 'checked', 'expect_not_contains': ['not checked', 'unchecked']}
        for phrase, expected in [('checked', 'matched'), ('not checked', 'not_matched'),
                                 ('unchecked', 'not_matched'), ('', 'not_matched')]:
            self.assertEqual(transcript_assertion(action, [{'phrase': phrase}]), expected)
        self.assertEqual(transcript_assertion({}, [{'phrase': 'checked'}]), 'not_requested')


if __name__ == '__main__':
    unittest.main()
