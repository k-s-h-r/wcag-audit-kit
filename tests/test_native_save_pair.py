"""Uncertainty checks for a bounded native notification comparison."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from benchmarks import native_save_pair as pair
from orca_log import speech_in_window


class NativeSavePairTest(unittest.TestCase):
    def artefacts(self, *, status=True, record_pair=False):
        job = {'id': 'screen-reader--4.1.3--case', 'urls': {'trial.html': 'http://127.0.0.1:8000/4.1.3/trial.html'}}
        plan = {'action': {'type': 'click', 'selector': '#submit-widget'}, 'target': '#message'}
        request = pair.request_for(job, 'trial.html', plan, record_pair=record_pair)
        focus = {'tag': 'button', 'id': 'submit-widget', 'documentHasFocus': True}
        body = {'tag': 'body', 'id': '', 'documentHasFocus': True}
        log = "04:00:00.100000 - SPEECH OUTPUT: 'tab'\n04:00:00.200000 - SPEECH OUTPUT: '更新する button.'\n"
        windows = [('00', '03'), ('04', '07')]
        focuses = [focus, focus]
        messages = ('待っています', '更新しました')
        if record_pair:
            log = "04:00:04.100000 - SPEECH OUTPUT: 'escape'\n"
            log += "04:00:08.100000 - SPEECH OUTPUT: '更新する'\n04:00:08.200000 - SPEECH OUTPUT: 'button'\n"
            log += "04:00:12.100000 - SPEECH OUTPUT: 'enter'\n"
            log += "04:00:12.200000 - SPEECH OUTPUT: '更新する'\n04:00:12.300000 - SPEECH OUTPUT: 'button'\n"
            windows += [('08', '11'), ('12', '15'), ('16', '19')]
            focuses = [body, body, focus, focus, focus]
            messages = ('', '', '', '', '更新しました')
        activation = windows[-1][0]
        log += f"04:00:{activation}.100000 - SPEECH OUTPUT: 'space'\n"
        if status:
            log += f"04:00:{activation}.600000 - SPEECH OUTPUT: '更新しました'\n"
        log_hash = sha256(log.encode()).hexdigest()
        request_hash = sha256(json.dumps(request).encode()).hexdigest()
        observations = []
        for index, (action, (begin, end), message) in enumerate(
                zip(request['actions'], windows, messages, strict=True), 1):
            started = '2026-11-19T04:00:' + begin + '+00:00'
            finished = '2026-11-19T04:00:' + end + '+00:00'
            trigger, target = request['observe']
            observations.append(dict(index=index, action=action, url=request['url'],
                                     focus_before=focuses[max(0, index-2)], focus_after=focuses[index-1],
                                     started_at=started, finished_at=finished,
                                     speech=speech_in_window(log, started, finished), observations=[
                                         dict(target=trigger, text='更新する'),
                                         dict(target=target, text=message, attributes={
                                             'role': 'status' if status else None, 'aria-live': None, 'aria-atomic': None,
                                         }),
                                     ]))
        environment = dict.fromkeys(pair.ENVIRONMENT, 'unit fixture')
        environment.update(reader='Orca', browser='Chromium', simulation=False, installation_verified=True)
        receipt = dict(status='collected', case_id=request['case_id'], scenario=request, request_sha256=request_hash,
                       cleanup={'debug_log_sha256': log_hash, 'pty_error': None}, environment=environment,
                       started_at='2026-11-19T03:59:59+00:00', finished_at='2026-11-19T04:00:20+00:00',
                       observations=observations)
        return request, request_hash, receipt, log, log_hash

    def test_uses_observed_text_and_real_window_entries(self):
        arguments = self.artefacts()
        request = arguments[0]
        self.assertFalse(any('expect_contains' in step for step in request['actions']))
        normal = pair.check_receipt(*arguments)
        silent = pair.check_receipt(*self.artefacts(status=False))
        self.assertEqual(pair.calibrate([silent, normal]), ['failed', 'passed'])
        self.assertEqual(pair.calibrate([normal, silent]), ['passed', 'failed'])

    def test_cannot_certify_silence_without_matching_positive_control(self):
        normal = pair.check_receipt(*self.artefacts())
        silent = pair.check_receipt(*self.artefacts(status=False))
        for changes in [
            {'activation_speech': []},
            {'activation_speech': ['space', 'unrelated']},
            {'environment': dict(silent['environment'], browser_version='different')},
            {'after': 'another message'},
            {'role': 'alert'},
        ]:
            with self.subTest(changes=changes):
                self.assertEqual(pair.calibrate([normal, dict(silent, **changes)]), ['cant_tell'] * 2)
        self.assertEqual(pair.calibrate([dict(normal, activation_speech=['space']), silent]), ['cant_tell'] * 2)
        self.assertEqual(pair.calibrate([None, silent]), ['cant_tell'] * 2)

    def test_incomplete_capture_holds_on_missing_or_malformed_output(self):
        request = self.artefacts()[0]
        with tempfile.TemporaryDirectory() as temporary:
            area = Path(temporary)
            (area/'request.json').write_text(json.dumps(request))
            self.assertIsNone(pair.read_observation(request, area))
            speech = area/'speech'
            speech.mkdir()
            (speech/'screen-reader.json').write_text('{truncated')
            (speech/'orca-debug.log').write_text('partial log')
            self.assertIsNone(pair.read_observation(request, area))

    def test_record_pair_requires_both_activation_echoes_and_the_notification(self):
        normal = pair.check_receipt(*self.artefacts(record_pair=True), record_pair=True)
        silent = pair.check_receipt(*self.artefacts(record_pair=True, status=False), record_pair=True)
        self.assertEqual(pair.calibrate([normal, silent], record_pair=True), ['passed', 'failed'])
        for positive, negative in (
            (dict(normal, activation_speech=[normal['after']]), silent),
            (normal, dict(silent, activation_speech=[])),
            (normal, dict(silent, activation_speech=['space', 'unrelated'])),
        ):
            self.assertEqual(pair.calibrate([positive, negative], record_pair=True), ['cant_tell'] * 2)

    def test_record_pair_requires_empty_notice_and_focused_native_button_control(self):
        request, request_hash, receipt, log, log_hash = self.artefacts(record_pair=True)
        premature = deepcopy(receipt)
        premature['observations'][1]['observations'][1]['text'] = 'something already there'
        moved = deepcopy(receipt)
        moved['observations'][-2]['focus_after'] = moved['observations'][0]['focus_after']
        for invalid in (premature, moved):
            self.assertIsNone(pair.check_receipt(request, request_hash, invalid, log, log_hash, record_pair=True))

        no_control = deepcopy(receipt)
        log = '\n'.join(line for line in log.splitlines() if '04:00:12.2' not in line) + '\n'
        log_hash = sha256(log.encode()).hexdigest()
        no_control['cleanup']['debug_log_sha256'] = log_hash
        for row in no_control['observations']:
            row['speech'] = speech_in_window(log, row['started_at'], row['finished_at'])
        self.assertIsNone(pair.check_receipt(request, request_hash, no_control, log, log_hash, record_pair=True))

    def test_missing_or_modified_provenance_does_not_become_speech(self):
        def mismatch_receipt(original):
            result = deepcopy(original)
            result['observations'][1]['speech'][1]['phrase'] = 'made-up'
            return result

        arguments = self.artefacts()
        request, request_hash, receipt, log, log_hash = arguments
        self.assertIsNone(pair.check_receipt(request, request_hash, mismatch_receipt(receipt), log, log_hash))
        self.assertIsNone(pair.check_receipt(request, request_hash, receipt, log, 'incorrect digest'))
        self.assertIsNone(pair.check_receipt(request, 'wrong-request', receipt, log, log_hash))
        changed = deepcopy(receipt)
        changed['observations'][1]['focus_before']['id'] = 'elsewhere'
        self.assertIsNone(pair.check_receipt(request, request_hash, changed, log, log_hash))
        changed = deepcopy(receipt)
        changed['observations'][1]['url'] += '?elsewhere'
        self.assertIsNone(pair.check_receipt(request, request_hash, changed, log, log_hash))


if __name__ == '__main__':
    unittest.main()
