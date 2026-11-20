from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from urllib.parse import urlsplit
import unittest

from benchmarks import core, residual_evidence
from benchmarks.residual_focus_context import evaluate


class ResidualEvidenceTest(unittest.TestCase):
    def test_request_scope_is_the_frozen_path_set_and_origin(self):
        origin = urlsplit('http://127.0.0.1:12345/3.2.1/p03.html')
        files = {'/3.2.1/p03.html', '/3.2.1/details.html'}
        for method, url, expected in [
            ('GET', origin.geturl(), True),
            ('HEAD', 'http://127.0.0.1:12345/3.2.1/details.html?q=a', True),
            ('POST', origin.geturl(), False),
            ('GET', 'http://127.0.0.1:12345/2.1.1/details.html', False),
            ('GET', 'http://127.0.0.1:12346/3.2.1/details.html', False),
            ('GET', 'http://127.0.0.1:12345/3.2.1/%2e%2e/oracle.snapshot.json', False),
        ]:
            with self.subTest(method=method, url=url):
                request = SimpleNamespace(method=method, url=url)
                self.assertEqual(residual_evidence.allowed_request(request, origin, files), expected)

    def test_frozen_media_support_range_requests(self):
        response = residual_evidence.file_response('/track.webm',b'012345','GET','bytes=2-3')
        self.assertEqual(response['status'],206)
        self.assertEqual(response['body'],b'23')
        self.assertEqual(response['headers']['content-range'],'bytes 2-3/6')
        self.assertEqual(residual_evidence.file_response('/track.webm',b'012345','GET','bytes=-2')['body'],b'45')
        self.assertEqual(residual_evidence.file_response('/track.webm',b'012345','GET','bytes=9-')['status'],416)
        self.assertEqual(residual_evidence.file_response('/track.webm',b'012345','HEAD',None)['body'],b'')

    def test_coverage_keeps_other_checkpoints_out_of_the_probe_scope(self):
        job = dict(criterion='3.2.1', states=[dict(id='after-focus', residual_probe={'target':'#field'})])
        expectation = dict(state='after-focus', checkpoint='3.2.1-02')
        self.assertTrue(residual_evidence.selected(job, expectation))
        self.assertFalse(residual_evidence.selected(job, dict(expectation, checkpoint='3.2.1-01')))
        self.assertFalse(residual_evidence.selected(job, dict(expectation, state='initial')))
        with self.assertRaises(ValueError):
            core.compare({'residual_probes_only':True}, {})

    def test_predictions_require_the_same_frozen_page_and_attempt(self):
        with TemporaryDirectory() as output:
            run = Path(output)
            page = 'p03.html'
            state = 'after-focus'
            job = dict(id='machine--3.2.1--c03', mode='machine', criterion='3.2.1', pages=[page],
                urls={page:'http://127.0.0.1:8000/3.2.1/p03.html'}, checkpoints=['3.2.1-02'],
                states=[dict(id=state,residual_probe={'target':'#field'})])
            attempt = run/'audit-runs'/job['id']/state/'attempt-01'/'run'
            receipt = attempt.parent/'receipt.json'
            path = attempt.parent/'residual-after-focus.json'
            core.save(receipt,dict(job_id=job['id'],mode='machine',page=page,url=job['urls'][page],
                                   status='completed',exit_code=0))
            progress = {'jobs':{job['id']:{page:dict(status='completed',exit_code=0,
                                                     directory=attempt.relative_to(run).as_posix())}}}
            frozen = {'worker/public/3.2.1/p03.html':'file-hash',
                      receipt.relative_to(run).as_posix():core.file_hash(receipt)}
            _, digest = residual_evidence.fixture_set(frozen,'3.2.1')
            record = dict(binding=residual_evidence.binding(job,page,state,digest),
                          status='unconfirmed',reason='入力が観測できなかった。')
            core.save(path,record)
            self.assertFalse(residual_evidence.predictions(run,job,progress,frozen))
            frozen[path.relative_to(run).as_posix()] = core.file_hash(path)
            result, = residual_evidence.predictions(run,job,progress,frozen).values()
            self.assertEqual(result['outcome'],'cant_tell')
            record['binding']['page'] = 'p04.html'
            core.save(path,record)
            self.assertFalse(residual_evidence.predictions(run,job,progress,frozen))

    def test_requires_real_sequential_focus_before_attributing_navigation(self):
        plan = {'target':'#field'}
        url = 'http://127.0.0.1:8000/3.2.1/p03.html'
        event = dict(trusted=True,url=url,start=42.5)
        events = [dict(event,type='keydown',key='Tab'),dict(event,type='focusin',id='field')]
        measured = dict(before_url=url,after_url=url,before={'start':42.5},after={'start':42.5,'id':'field'},events=events)
        self.assertEqual(evaluate('3.2.1',plan,measured)[0]['outcome'],'passed')
        measured.update(after_url=url+'/next',after={'start':43,'id':''})
        self.assertEqual(evaluate('3.2.1',plan,measured)[0]['outcome'],'failed')
        events[1]['trusted'] = False
        self.assertEqual(evaluate('3.2.1',plan,measured)[0]['outcome'],'cant_tell')
