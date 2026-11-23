"""Regression checks for attribution of machine dialog-focus benchmark scores."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from benchmarks.suite import core
from benchmarks.measurements import dialog_focus_evidence as focus


class DialogFocusEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.url = 'http://127.0.0.1:8000/2.4.3/example.html'
        self.start = 1700000000000.125
        self.plan = dict(opener='#launch', dialog='#notice', button='#close', activation='Enter')
        self.state = dict(id='button-close-enter', dialog_focus=self.plan)
        self.route = focus.plans('2.4.3', [focus.CHECKPOINT], [self.state])[self.state['id']][1]
        self.transition = dict(route=self.route, dialog_focus='tab', environment='desktop',
                               blocked_requests=[], native_events=[], error=None, settling=[{'status':'quiet'}]*4)
        self.record = dict(phase='tab', status='closed', reason='', opener='#launch', close_action=self.route[1],
                           opener_event_index=1, close_event_index=2, tab_event_index=3,
                           before_close=self.snapshot('#close', ['#notice']),
                           after_close=self.snapshot('#launch', []),
                           after_tab=self.snapshot('#next', []),
                           opener_restored=True, tab_moved_focus=True)
        base = dict(url=self.url, documentId=f'{self.start}-input-id', isTrusted=True, is_main_frame=True)
        modifiers = dict(control=False, alt=False, shift=False, meta=False)
        self.inputs = dict(truncated=False, dropped=0, events=[
            dict(base, type='click', pointerType='mouse', expectedTargetMatched=True),
            dict(base, type='keydown', key='Enter', modifiers=modifiers, expectedTargetMatched=True),
            dict(base, type='keydown', key='Tab', modifiers=modifiers),
        ])

    def snapshot(self, focus, modals, *, root=False):
        return dict(focus=focus, modals=modals, root_focus=root, supported=True,
                    document_start=self.start, url=self.url)

    def observation(self):
        return focus.observed_row(self.record, self.transition, self.inputs, self.plan, self.route, self.url)

    def test_normal_wrong_and_unconfirmed_focus(self):
        self.assertEqual(self.observation()['outcome'], 'passed')
        self.record['after_tab'] = self.snapshot('body', [], root=True)
        self.assertEqual(self.observation()['outcome'], 'cant_tell')
        self.record.update(after_close=self.snapshot('body', [], root=True), after_tab=self.snapshot('#earlier', []),
                           opener_restored=False, tab_moved_before_opener=True)
        self.assertEqual(self.observation()['outcome'], 'failed')
        self.record.pop('tab_moved_before_opener')
        self.assertEqual(self.observation()['outcome'], 'cant_tell')

    def test_requires_sustained_closure_and_trusted_ordered_input(self):
        self.assertEqual(self.observation()['outcome'], 'passed')
        mutations = [
            (self.inputs, 'truncated', True),
            (self.inputs['events'][0], 'expectedTargetMatched', False),
            (self.inputs['events'][1], 'isTrusted', False),
            (self.inputs['events'][2], 'is_main_frame', False),
            (self.inputs['events'][2], 'documentId', 'different-document'),
            (self.record, 'tab_event_index', 2),
            (self.record['after_tab'], 'modals', ['#notice']),
            (self.record['after_tab'], 'document_start', self.start + 1),
            (self.record['after_close'], 'focus', '#other'),
            (self.record['before_close'], 'modals', ['#other']),
            (self.transition, 'blocked_requests', [{'method':'POST'}]),
            (self.transition, 'settling', [{'status':'timeout'}]*4),
        ]
        for source, field, value in mutations:
            with self.subTest(field=field, value=value):
                previous = source[field]
                source[field] = value
                self.assertIsNone(self.observation())
                source[field] = previous

    def test_public_plan_rejects_outcome_and_duplicate_route(self):
        for plan in (dict(self.plan, expected='failed'), dict(self.plan, dialog='#launch')):
            with self.assertRaises(ValueError):
                focus.plans('2.4.3',[focus.CHECKPOINT],[dict(self.state, dialog_focus=plan)])
        with self.assertRaises(ValueError):
            focus.plans('2.4.3',[focus.CHECKPOINT],[self.state,dict(self.state,id='other')])

    def test_frozen_evidence_is_bound_to_the_original_attempt(self):
        with TemporaryDirectory() as temporary:
            run = Path(temporary)
            job = dict(id='machine--2.4.3--c01', mode='machine', criterion='2.4.3',
                       checkpoints=[focus.CHECKPOINT], states=[self.state], urls={'example.html':self.url})
            attempt = run/'audit-runs'/job['id']/'example'/'attempt-01'/'run'
            ledger = core.audit.run_layout.ledger(attempt)
            directory = ledger/'evidence'/'route-capture'
            files = {
                attempt.parent/'receipt.json': dict(job_id=job['id'], page='example.html',
                    mode=job['mode'], url=self.url, status='completed', exit_code=0),
                ledger/'exploration.json': dict(edges=[dict(self.transition,evidence_dir='evidence/route-capture')]),
                directory/'transition.json': self.transition,
                directory/'dialog-focus.json': self.record,
                directory/'input-events.json': self.inputs,
            }
            for path, data in files.items():
                core.save(path,data)
            progress = {'jobs':{job['id']:{'example.html':dict(status='completed', exit_code=0,
                                                              directory=attempt.relative_to(run).as_posix())}}}
            frozen = {p.relative_to(run).as_posix():core.file_hash(p) for p in files}
            result, = focus.predictions(run,job,progress,frozen).values()
            self.assertEqual((result['target'],result['state'],result['outcome']),('#launch','button-close-enter','passed'))
            self.assertEqual(set(result['evidence']),set(frozen))
            for required in frozen:
                with self.subTest(required=required):
                    partial = {key:value for key,value in frozen.items() if key != required}
                    self.assertEqual(focus.predictions(run,job,progress,partial),{})
