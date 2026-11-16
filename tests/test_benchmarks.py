import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from benchmarks import core


class CorpusTest(unittest.TestCase):
    def test_registered_cases_have_positive_negative_and_local_assets(self):
        data=core.corpus()
        self.assertEqual(len(data['suites']),86)
        self.assertEqual(sum(len(s['cases']) for s in data['suites']),182)
        self.assertEqual(sum(len(c['pages']) for s in data['suites'] for c in s['cases']),190)
        for suite in data['suites']:
            outcomes={e['expected'] for c in suite['cases'] for e in c['expectations']}
            self.assertIn('failed',outcomes)
            self.assertTrue('passed' in outcomes or ('inapplicable' in outcomes and suite.get('limitations')))
        self.assertTrue(any(p.endswith('.webm') for p in data['public_files']))
        self.assertTrue(any(p.endswith('.wav') for p in data['public_files']))
        self.assertTrue(any(p.endswith('.svg') for p in data['public_files']))

    def test_page_bytes_cannot_change_without_changing_corpus_digest(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory);shutil.copytree(ROOT/'benchmarks/cases/2.4.2',target/'2.4.2')
            before=core.corpus(target)['digest'];p=target/'2.4.2/public/p01.html'
            p.write_text(p.read_text().replace('<title></title>','<title>お問い合わせ</title>'))
            self.assertNotEqual(before,core.corpus(target)['digest'])

    def test_oracle_and_missing_media_cannot_be_linked_from_public_html(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory);shutil.copytree(ROOT/'benchmarks/cases/2.4.2',target/'2.4.2')
            p=target/'2.4.2/public/p01.html';p.write_text(p.read_text()+'<a href="../suite.json">資料</a>')
            with self.assertRaises(ValueError):core.corpus(target)
            p.write_text('<html><img src="assets/absent.png"></html>')
            with self.assertRaises(ValueError):core.corpus(target)

    def test_blank_suites_do_not_count_as_prepared(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory);shutil.copytree(ROOT/'benchmarks/cases/2.4.2',target/'2.4.2')
            p=target/'2.4.2/suite.json';v=core.load(p);v['cases']=[];core.save(p,v)
            with self.assertRaises(ValueError):core.corpus(target)

    def test_verification_instruction_changes_require_a_new_implementation(self):
        from benchmarks import runner
        paths=runner.source_files()
        self.assertIn(ROOT/'skills/wcag-page/SKILL.md',paths)
        self.assertIn(ROOT/'references/tests/1.1.1.md',paths)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'SKILL.md';path.write_text('First verification instructions')
            with patch('benchmarks.runner.source_files',return_value=[path]),patch('benchmarks.core.ROOT',Path(temp)):
                before=runner.implementation_digest();path.write_text('Changed verification instructions')
                self.assertNotEqual(before,runner.implementation_digest())

    def test_all_criteria_have_negative_cases_and_unavailable_controls_are_explicit(self):
        suites={s['criterion']:s for s in core.corpus()['suites']}
        self.assertEqual(set(suites),set(core.audit.CRITERIA))
        for sc in ['1.2.5','1.2.6','1.2.7']:
            suite=suites[sc]
            self.assertTrue(suite['limitations'])
            outcomes={e['expected'] for c in suite['cases'] for e in c['expectations']}
            self.assertEqual(outcomes,{'failed','inapplicable'})


class ScoringTest(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.counter=0
    def tearDown(self):self.temp.cleanup()

    def make_run(self,mode='ai',point='1.1.1-01',kind='program',defer=False,pages=None,aliases=None):
        self.counter+=1;run=Path(self.temp.name)/str(self.counter);run.mkdir()
        sc='.'.join(point.split('.')[:2])+'.'+point.split('.')[2].split('-')[0]
        pages=pages or ['p01.html'];ident=f'{mode}--{sc}--c01'
        expected=[dict(page=pages[-1],state='initial',target=t,checkpoint=point,expected=o,rationale='対照例の期待結果を固定する。',
                       modes={m:'defer' if defer else 'evaluate' for m in core.modes.MODES},evidence_kind=kind) for t,o in [('#one','failed'),('#two','passed')]]
        case=dict(id='c01',pages=pages,checkpoints=[point],states=[{'id':'initial','instructions':['実際の対象を比較する。']}],expectations=expected)
        oracle=dict(suites=[dict(criterion=sc,cases=[case])])
        job=dict(id=ident,mode=mode,criterion=sc,case='c01',pages=pages,urls={p:f'http://127.0.0.1:8000/{sc}/{p}' for p in pages},
                 states=case['states'],checkpoints=[point],target_aliases={point:aliases or {}},evidence_requirements={point:{'image':kind=='visual-semantic','speech':kind=='screen-reader','comparison':kind=='cross-page'}})
        core.save(run/'oracle.snapshot.json',oracle)
        core.save(run/'worker/tasks.json',{'jobs':[job]})
        meta=dict(schema_version='1',run_id='unit-run',corpus_digest=core.digest(oracle),oracle_digest=core.digest(oracle),modes=[mode],selection=[sc],configuration={'fixture':'unit'},
                  implementation_digest='unit-implementation',mode_catalog=core.modes.catalog(),criteria_catalog=[{k:c[k] for k in ['id','title','level']} for c in core.audit.CATALOG['criteria']])
        core.save(run/'run.json',meta)
        progress={'jobs':{ident:{}},'collection':'completed'}
        for page in pages:
            location=f'audit-runs/{ident}/{Path(page).stem}/attempt/run';p=run/location/'evidence/observed.json';core.save(p,{'observed':'synthetic unit evidence, not a browser or speech result'})
            progress['jobs'][ident][page]={'directory':location,'status':'error'}
        core.save(run/'progress.json',progress)
        core.freeze(run,[run/'run.json',run/'oracle.snapshot.json',run/'worker/tasks.json',*[p for p in (run/'audit-runs').rglob('*') if p.is_file()]])
        return run,meta,job,progress

    def observation(self,job,progress,target='#one',outcome='failed',method='program'):
        page=job['pages'][-1];path=progress['jobs'][job['id']][page]['directory']+'/evidence/observed.json'
        return dict(page=page,state='initial',target=target,checkpoint=job['checkpoints'][0],outcome=outcome,method=method,
                    observed='単体試験で観察の保存と採点を確認する。',evidence=[path])

    def submit(self,run,meta,job,observations):
        return core.record_review(run,dict(schema_version='1',run_id=meta['run_id'],corpus_digest=meta['corpus_digest'],job_id=job['id'],observations=observations))

    def test_unknown_and_disabled_checks_are_not_true_negatives(self):
        for defer in [False,True]:
            run,_,_,_=self.make_run(defer=defer);r=core.score(run)
            self.assertEqual(r['overall_status'],'incomplete');self.assertEqual(r['confusion'].get('TN',0),0)
            self.assertIsNone(r['precision_on_evaluated']);self.assertEqual(r['undetected_known_failures'],1)
            self.assertEqual(r['counts'],{'deferred' if defer else 'not_evaluated':2})

    def test_false_positives_and_false_negatives_are_both_detected(self):
        run,meta,job,p=self.make_run()
        self.submit(run,meta,job,[self.observation(job,p,outcome='passed'),self.observation(job,p,target='#two',outcome='failed')])
        r=core.score(run)
        self.assertEqual(r['selected_checks_status'],'failed')
        self.assertEqual(r['confusion'].get('FN'),1);self.assertEqual(r['confusion'].get('FP'),1)
        self.assertEqual(r['detected_known_failures'],0)

    def test_partial_unverified_results_do_not_hide_a_wrong_verdict(self):
        run,meta,job,p=self.make_run();self.submit(run,meta,job,[self.observation(job,p,outcome='passed')])
        r=core.score(run);self.assertEqual(r['overall_status'],'failed');self.assertEqual(r['counts']['not_evaluated'],1)

    def test_all_correct_means_only_the_registered_checkpoint_scope(self):
        run,meta,job,p=self.make_run()
        self.submit(run,meta,job,[self.observation(job,p),self.observation(job,p,target='#two',outcome='passed')])
        r=core.score(run);self.assertEqual(r['selected_checks_status'],'clear_for_selected_checks')
        self.assertEqual(r['confusion']['TP'],1);self.assertEqual(r['confusion']['TN'],1)
        self.assertEqual(sum(c['status']=='unprepared' for c in r['criteria']),85)

    def test_extra_unexpected_failures_count_as_false_positives(self):
        run,meta,job,p=self.make_run();self.submit(run,meta,job,[self.observation(job,p,target='#third')])
        r=core.score(run);self.assertEqual(len(r['unexpected_findings']),1);self.assertEqual(r['confusion']['FP'],1)

    def test_split_reviews_accumulate_and_keep_immutable_history(self):
        run,meta,job,p=self.make_run();first=self.submit(run,meta,job,[self.observation(job,p)])
        old=(run/first['review']).read_bytes();self.submit(run,meta,job,[self.observation(job,p,target='#two',outcome='passed')])
        self.assertEqual(core.score(run)['counts'],{'correct':2});self.assertEqual((run/first['review']).read_bytes(),old)
        self.assertEqual(len(core.load(run/'review-index.json')['entries']),2)

    def test_duplicate_rows_and_foreign_run_are_rejected_atomically(self):
        run,meta,job,p=self.make_run();row=self.observation(job,p)
        with self.assertRaises(ValueError):self.submit(run,meta,job,[row,copy.deepcopy(row)])
        wrong=dict(meta,run_id='another')
        with self.assertRaises(ValueError):self.submit(run,wrong,job,[row])
        self.assertFalse((run/'review-index.json').exists())

    def test_declared_ai_cannot_be_used_in_machine_mode(self):
        run,meta,job,p=self.make_run(mode='machine')
        with self.assertRaises(ValueError):self.submit(run,meta,job,[self.observation(job,p,method='ai')])

    def test_foreign_job_and_path_traversal_cannot_supply_evidence(self):
        run,meta,job,p=self.make_run();outside=run/'attachments/another-job/data.json';core.save(outside,{'observed':'other case'})
        row=self.observation(job,p);row['evidence']=[f'audit-runs/{job["id"]}/../../attachments/another-job/data.json']
        with self.assertRaises(ValueError):self.submit(run,meta,job,[row])
        with self.assertRaises(ValueError):core.local(run,'../outside.json')

    def test_image_comparison_requires_image_evidence(self):
        run,meta,job,p=self.make_run(point='1.1.1-04',kind='visual-semantic')
        with self.assertRaisesRegex(ValueError,'画像'):self.submit(run,meta,job,[self.observation(job,p,method='ai')])

    def test_sr_evidence_cannot_be_an_ax_tree_or_a_silent_environment(self):
        run,meta,job,p=self.make_run(mode='full',point='4.1.3-02',kind='screen-reader')
        row=self.observation(job,p,method='screen-reader')
        with self.assertRaisesRegex(ValueError,'実SR'):self.submit(run,meta,job,[row])
        path=run/f'attachments/{job["id"]}/speech.json'
        receipt=dict(case_id=job['id'],status='collected',scenario={'url':job['urls'][job['pages'][0]]},
                     environment={'reader':'Orca','simulation':False,'installation_verified':True},observations=[{'speech':[]}])
        core.save(path,receipt);row['evidence']=[path.relative_to(run).as_posix()]
        with self.assertRaisesRegex(ValueError,'対照'):self.submit(run,meta,job,[row])
        receipt['observations'][0]['speech']=[{'phrase':'対照のボタン名'}];core.save(path,receipt)
        self.submit(run,meta,job,[row]);self.assertEqual(core.score(run)['counts']['correct'],1)

    def test_cross_page_review_needs_both_pages_evidence(self):
        run,meta,job,p=self.make_run(point='3.2.3-01',kind='cross-page',pages=['p01.html','p02.html'])
        row=self.observation(job,p,method='ai')
        with self.assertRaisesRegex(ValueError,'全ページ'):self.submit(run,meta,job,[row])
        row['evidence'].append(p['jobs'][job['id']]['p01.html']['directory']+'/evidence/observed.json')
        self.submit(run,meta,job,[row]);self.assertEqual(core.score(run)['counts']['correct'],1)

    def test_changing_oracle_or_prior_evidence_is_rejected(self):
        run,meta,job,p=self.make_run();self.submit(run,meta,job,[self.observation(job,p)])
        path=run/self.observation(job,p)['evidence'][0];path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'変更された'):core.score(run)
        run,_,_,_=self.make_run();o=core.load(run/'oracle.snapshot.json');o['suites'][0]['cases'][0]['expectations'][0]['expected']='passed';core.save(run/'oracle.snapshot.json',o)
        with self.assertRaises(ValueError):core.score(run)

    def test_regression_detects_loss_to_unverified_and_new_false_positive(self):
        run,meta,job,p=self.make_run();self.submit(run,meta,job,[self.observation(job,p)])
        baseline=core.score(run);current=copy.deepcopy(baseline)
        current['rows'][0].update(grade='not_evaluated',actual='not_run')
        self.assertEqual(core.compare(baseline,current)['status'],'regressions')
        current=copy.deepcopy(baseline);current['rows'][1].update(grade='incorrect',actual='failed')
        self.assertEqual(core.compare(baseline,current)['status'],'regressions')
        unchanged=core.compare(baseline,baseline)
        self.assertEqual(unchanged['status'],'no_regressions');self.assertEqual(unchanged['current_quality'],'incomplete')

    def test_different_oracle_mode_or_budget_is_not_a_regression_comparison(self):
        run,_,_,_=self.make_run();baseline=core.score(run)
        for key,value in [('corpus_digest','changed'),('modes',['full']),('configuration',{'changed':True})]:
            current=copy.deepcopy(baseline);current[key]=value
            with self.assertRaises(ValueError):core.compare(baseline,current)

    def test_public_target_aliases_merge_observations_of_one_component(self):
        run,meta,job,p=self.make_run(aliases={'#child':'#one'})
        self.submit(run,meta,job,[self.observation(job,p,target='#child')])
        result=core.score(run)
        self.assertEqual(result['rows'][0]['grade'],'correct')
        self.assertFalse(result['unexpected_findings'])

    def test_concurrent_evidence_appends_keep_all_integrity_entries(self):
        from concurrent.futures import ThreadPoolExecutor
        run,_,_,_=self.make_run();files=[]
        for i in range(10):
            path=run/f'attachments/thread-{i}.txt';path.parent.mkdir(exist_ok=True);path.write_text(str(i));files.append(path)
        with ThreadPoolExecutor(max_workers=5) as workers:
            list(workers.map(lambda path:core.freeze(run,[path]),files))
        core.verify(run)
        saved=core.load(run/'integrity.json')['files']
        self.assertTrue(all(path.relative_to(run).as_posix() in saved for path in files))

    def test_resume_skips_completed_and_retains_incomplete_attempts(self):
        from benchmarks import runner
        run,meta,job,p=self.make_run(mode='machine');http=unittest.mock.Mock()
        # An incomplete attempt is never overwritten, even after retry succeeds.
        original=run/self.observation(job,p)['evidence'][0];old=original.read_bytes()
        meta['implementation_digest']=runner.implementation_digest();meta['configuration']={'max_states':2,'max_steps':3,'max_depth':1,'max_images':0}
        meta['port']=8000;meta['environment']={'unit':'environment'}
        core.save(run/'run.json',meta)
        integrity=core.load(run/'integrity.json');integrity['files']['run.json']=core.file_hash(run/'run.json');core.save(run/'integrity.json',integrity)
        attempted=[]
        def audit(args):
            target=Path(args[args.index('--out')+1]);core.save(target/'completion.json',{'synthetic_unit_test':True});attempted.append(target);return 0
        with patch('benchmarks.runner.environment',return_value=meta['environment']),patch('benchmarks.runner.server',return_value=http),patch('benchmarks.runner.core.audit.main',side_effect=audit),patch('benchmarks.runner.core.score',return_value={}):
            runner.collect(run,resume=True)
            self.assertEqual(len(attempted),1)
            self.assertNotEqual(attempted[0],original.parents[1])
            self.assertEqual(original.read_bytes(),old)
            runner.collect(run,resume=True)
            self.assertEqual(len(attempted),1)
        self.assertEqual(core.load(run/'progress.json')['collection'],'completed')

    def test_resume_rejects_a_changed_browser_environment(self):
        from benchmarks import runner
        run,meta,_,_=self.make_run(mode='machine')
        meta.update(implementation_digest=runner.implementation_digest(),environment={'chromium':'old'})
        core.save(run/'run.json',meta)
        proof=core.load(run/'integrity.json');proof['files']['run.json']=core.file_hash(run/'run.json');core.save(run/'integrity.json',proof)
        with patch('benchmarks.runner.environment',return_value={'chromium':'new'}),patch('benchmarks.runner.server') as server:
            with self.assertRaisesRegex(ValueError,'実行環境'):runner.collect(run,resume=True)
        server.assert_not_called()

    def test_interrupted_collection_keeps_original_attempt_and_can_resume(self):
        from benchmarks import runner
        run,meta,job,p=self.make_run(mode='machine')
        meta.update(implementation_digest=runner.implementation_digest(),environment={'unit':'environment'},port=8000,
                    configuration={'max_states':2,'max_steps':3,'max_depth':1,'max_images':0})
        core.save(run/'run.json',meta)
        proof=core.load(run/'integrity.json');proof['files']['run.json']=core.file_hash(run/'run.json');core.save(run/'integrity.json',proof)
        original=run/self.observation(job,p)['evidence'][0];old=original.read_bytes()
        def interrupt(args):
            target=Path(args[args.index('--out')+1]);core.save(target/'partial.json',{'synthetic_unit_test':True});raise KeyboardInterrupt
        with patch('benchmarks.runner.environment',return_value=meta['environment']),patch('benchmarks.runner.server'),patch('benchmarks.runner.core.audit.main',side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):runner.collect(run,resume=True)
        state=core.load(run/'progress.json')
        self.assertEqual(state['collection'],'interrupted')
        self.assertEqual(state['jobs'][job['id']]['p01.html']['status'],'interrupted')
        self.assertEqual(original.read_bytes(),old)
        self.assertEqual(len(list((run/'audit-runs'/job['id']).rglob('partial.json'))),1)
        core.verify(run)

    def test_always_reporting_success_is_not_an_accuracy_pass(self):
        run,meta,job,p=self.make_run()
        self.submit(run,meta,job,[self.observation(job,p,outcome='passed'),self.observation(job,p,target='#two',outcome='passed')])
        r=core.score(run);self.assertEqual(r['confusion']['FN'],1);self.assertEqual(r['overall_status'],'failed')

class NativeWorkerInterpretationTest(unittest.TestCase):
    def receipt(self,announced=True):
        return {'status':'collected','environment':{'simulation':False,'installation_verified':True,'reader':'Orca'},
                'observations':[{'speech':[{'phrase':'記録する ボタン'}]},
                    {'speech':[{'phrase':'記録しました。'}] if announced else [],
                     'focus_after':{'id':'record','documentHasFocus':True},
                     'observations':[{'target':{'selector':'#notice'},'text':'記録しました。'}]}]}

    def test_actual_ui_and_control_speech_are_both_needed(self):
        from benchmarks.native_status import interpret
        r=self.receipt();self.assertTrue(interpret(r)['valid']);self.assertTrue(interpret(r)['announced'])
        r['observations'][0]['speech']=[];self.assertFalse(interpret(r)['valid'])
        r=self.receipt();r['observations'][1]['focus_after']['documentHasFocus']=False;self.assertFalse(interpret(r)['valid'])
        r=self.receipt();r['observations'][1]['observations'][0]['text']='';self.assertFalse(interpret(r)['valid'])

    def test_silence_is_not_automatically_a_negative_without_contrast_calibration(self):
        from benchmarks.native_status import interpret
        result=interpret(self.receipt(False));self.assertTrue(result['valid']);self.assertFalse(result['announced'])
        r=self.receipt();r['status']='blocked';self.assertFalse(interpret(r)['valid'])

    def test_worker_request_uses_the_production_adapters_schema(self):
        from benchmarks.native_status import make_request
        from screen_reader_native import validate
        job={'id':'screen-reader--4.1.3--c01','pages':['p01.html'],'urls':{'p01.html':'http://127.0.0.1:8000/4.1.3/p01.html'}}
        request=make_request(job);validate(request)
        self.assertIsInstance(request['actions'][0]['expect_contains'],str)

    def test_long_archive_path_uses_short_live_unix_socket_directory(self):
        from benchmarks.native_status import capture
        with tempfile.TemporaryDirectory() as temp:
            area=Path(temp)/('long-'*35);area.mkdir();core.save(area/'request.json',{})
            outputs=[]
            def backend(args,**kwargs):
                path=Path(args[args.index('--out')+1]);outputs.append(path)
                self.assertLess(len(str(path/'speechd.sock').encode()),100)
                core.save(path/'screen-reader.json',{'status':'blocked','unit_fixture':True})
            with patch('benchmarks.native_status.subprocess.run',side_effect=backend):capture('/unit/root',area)
            self.assertTrue((area/'speech/screen-reader.json').exists());self.assertFalse(outputs[0].exists())

if __name__=='__main__':unittest.main()
