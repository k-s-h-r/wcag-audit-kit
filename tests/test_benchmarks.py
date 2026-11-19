import copy
from importlib.util import find_spec
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from benchmarks import core


class CorpusTest(unittest.TestCase):
    def test_registered_cases_have_positive_negative_and_local_assets(self):
        data=core.corpus()
        self.assertEqual(len(data['suites']),86)
        self.assertEqual(core.case_contracts.coverage(data,core.modes.catalog()['checkpoints'])['missing'],[])
        self.assertTrue(all(len(s['cases'])>=2 for s in data['suites']))
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

    def test_verification_instructions_and_invocation_policy_affect_implementation_digest(self):
        from benchmarks import runner
        paths=runner.source_files()
        self.assertIn(ROOT/'skills/wcag-page/SKILL.md',paths)
        self.assertIn(core.RUNTIME/'references/tests/1.1.1.md',paths)
        changes=[('SKILL.md','First verification instructions','Changed verification instructions'),
                 ('agents/openai.yaml','policy:\n  allow_implicit_invocation: false\n',
                  'policy:\n  allow_implicit_invocation: true\n')]
        for relative,before_text,after_text in changes:
            with self.subTest(file=relative),tempfile.TemporaryDirectory() as temp:
                path=Path(temp)/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(before_text)
                with patch('benchmarks.runner.source_files',return_value=[path]),patch('benchmarks.core.ROOT',Path(temp)):
                    before=runner.implementation_digest();path.write_text(after_text)
                    self.assertNotEqual(before,runner.implementation_digest())

    def test_snapshot_contains_the_complete_canonical_runtime_and_entry_points(self):
        from benchmarks import runner
        from scripts.skill_layout import resource_files,SKILLS
        paths=runner.source_files()
        self.assertTrue(all(p.is_file() for p in paths))
        self.assertTrue({core.RUNTIME/p for p in resource_files()}<=set(paths))
        self.assertTrue({ROOT/'skills'/name/'SKILL.md' for name in SKILLS}<=set(paths))
        self.assertTrue({ROOT/'skills'/name/'agents/openai.yaml' for name in SKILLS}<=set(paths))
        self.assertNotIn(ROOT/'SKILL.md',paths)
        self.assertNotIn(ROOT/'vendor/axe.min.js',paths)

    def test_benchmark_cli_imports_runtime_in_a_fresh_process(self):
        import subprocess
        result=subprocess.run([sys.executable,str(ROOT/'benchmarks/run.py'),'inventory'],
            cwd=self._temporary_working_directory(),capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(len(json.loads(result.stdout)['criteria']),86)

    def _temporary_working_directory(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        return directory.name

    def test_all_criteria_have_negative_and_real_passing_controls(self):
        suites={s['criterion']:s for s in core.corpus()['suites']}
        self.assertEqual(set(suites),set(core.audit.CRITERIA))
        for sc in ['1.2.5','1.2.6','1.2.7']:
            suite=suites[sc]
            self.assertNotIn('limitations',suite)
            outcomes={e['expected'] for c in suite['cases'] for e in c['expectations']}
            self.assertTrue({'failed','passed','inapplicable'}<=outcomes)
    def test_inline_script_navigation_cannot_reference_a_missing_page(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory);shutil.copytree(ROOT/'benchmarks/cases/2.4.2',target/'2.4.2')
            page=target/'2.4.2/public/p01.html'
            page.write_text('<html><button onclick="location.href=\'missing.html\'">次へ</button></html>')
            with self.assertRaisesRegex(ValueError,'missing.html'):core.corpus(target)
            page.write_text('<html><script>setTimeout(()=>location.replace("absent.html"),10)</script></html>')
            with self.assertRaisesRegex(ValueError,'absent.html'):core.corpus(target)

    def test_acquisition_contracts_cannot_contain_verdicts_or_silent_empty_lists(self):
        from benchmarks import case_contracts
        case=dict(pages=['p01.html'],states=[{'id':'initial'}],checkpoints=['1.1.1-02'])
        item=dict(page='p01.html',state='initial',checkpoint='1.1.1-02',kind='inventory',targets=[],rationale='画像がない対照例。')
        case['evidence_expectations']=[item]
        with self.assertRaises(ValueError):case_contracts.validate(case)
        item['empty_is_expected']=True;case_contracts.validate(case)
        item['expected']='passed'
        with self.assertRaises(ValueError):case_contracts.validate(case)
    def test_all_required_families_and_generated_index_are_present(self):
        from benchmarks.build_fixture_index import build
        outputs,index=build()
        self.assertEqual(len(index['checkpoints']),131)
        self.assertFalse(index['missing_checkpoints']);self.assertFalse(index['missing_families'])
        for name,content in outputs.items():self.assertEqual((ROOT/'benchmarks'/name).read_text(),content,name)
        self.assertTrue(all(p['cases'] for p in index['checkpoints']))

    def test_sign_language_control_has_licensed_media_and_known_utterances(self):
        suite=core.load(ROOT/'benchmarks/cases/1.2.6/suite.json')
        self.assertEqual(suite['material_sources'][0]['license'],'CC BY-SA 3.0')
        self.assertTrue((ROOT/'benchmarks/cases/1.2.6/public/assets/sign.webm').is_file())
        self.assertTrue((ROOT/'benchmarks/cases/1.2.6/materials/Hello1.ogv').is_file())
        meanings=[c for c in suite['cases'] if c.get('pattern')=='1.2.6.sign-meaning']
        self.assertEqual({c['expectations'][0]['expected'] for c in meanings},{'passed','failed'})


class ScoringTest(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.counter=0
    def tearDown(self):self.temp.cleanup()

    def make_run(self,mode='ai',point='1.1.1-01',kind='program',defer=False,pages=None,aliases=None,contract=None):
        self.counter+=1;run=Path(self.temp.name)/str(self.counter);run.mkdir()
        sc='.'.join(point.split('.')[:2])+'.'+point.split('.')[2].split('-')[0]
        pages=pages or ['p01.html'];ident=f'{mode}--{sc}--c01'
        expected=[dict(page=pages[-1],state='initial',target=t,checkpoint=point,expected=o,rationale='対照例の期待結果を固定する。',
                       modes={m:'defer' if defer else 'evaluate' for m in core.modes.MODES},evidence_kind=kind) for t,o in [('#one','failed'),('#two','passed')]]
        case=dict(id='c01',pages=pages,checkpoints=[point],states=[{'id':'initial','instructions':['実際の対象を比較する。']}],expectations=expected)
        if contract:
            case['evidence_expectations']=[contract]
            if contract['checkpoint'] not in case['checkpoints']:case['checkpoints'].append(contract['checkpoint'])
        oracle=dict(suites=[dict(criterion=sc,cases=[case])])
        job=dict(id=ident,mode=mode,criterion=sc,case='c01',pages=pages,urls={p:f'http://127.0.0.1:8000/{sc}/{p}' for p in pages},
                 states=case['states'],checkpoints=case['checkpoints'],acquisition_checkpoints=[contract['checkpoint']] if contract else [],target_aliases={point:aliases or {}},evidence_requirements={point:{'image':kind=='visual-semantic','speech':kind=='screen-reader','comparison':kind=='cross-page'}})
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

    def test_relative_review_keeps_absolute_evidence_paths_inside_the_run(self):
        import os
        run,meta,job,p=self.make_run()
        result=self.submit(Path(os.path.relpath(run,Path.cwd())),meta,job,[self.observation(job,p)])
        self.assertTrue((run/result['review']).is_file())
        self.assertEqual(core.score(run)['counts']['correct'],1)
        self.assertTrue(all('..' not in name for name in core.load(run/'integrity.json')['files']))

    def test_relative_run_decodes_axe_and_keyboard_evidence(self):
        import os
        run,_,job,progress=self.make_run(mode='machine')
        progress['jobs'][job['id']]['p01.html']['status']='completed'
        location=run/progress['jobs'][job['id']]['p01.html']['directory']
        core.save(location/'initial/axe.json',{'violations':[{'id':'image-alt','nodes':[{'target':['#one'],'html':'<img>'}]}]})
        core.save(location/'key/transition.json',{'unit':True})
        core.save(location/'exploration.json',{'nodes':[{'route':[],'evidence_dir':'initial'}],
            'edges':[{'route':[{'type':'key','selector':'#two'}],'evidence_dir':'key'}]})
        job['checkpoints']+=['2.1.1-01']
        relative=Path(os.path.relpath(run,Path.cwd()))
        result=core.program_predictions(relative,job,progress)
        self.assertEqual(len(result),2)
        self.assertTrue(all(not Path(row['evidence'][0]).is_absolute() for row in result.values()))

    def test_acquisition_expectations_cannot_become_a_conformance_pass(self):
        from benchmarks import reporting
        contract=dict(checkpoint='1.1.1-02',page='p01.html',state='initial',kind='inventory',targets=['#one'],rationale='背景画像を見落とさず取得する。')
        run,meta,job,p=self.make_run(contract=contract)
        self.submit(run,meta,job,[self.observation(job,p),self.observation(job,p,target='#two',outcome='passed')])
        r=core.score(run)
        self.assertEqual(r['counts'],{'correct':2});self.assertEqual(r['selected_checks_status'],'incomplete')
        self.assertEqual(r['pending_evidence_contracts'][0]['status'],'not_evaluated')
        row=self.observation(job,p);row['checkpoint']='1.1.1-02'
        with self.assertRaisesRegex(ValueError,'取得期待を適合・不適合として取り込まない'):self.submit(run,meta,job,[row])
        paths=reporting.write(run,r)
        from openpyxl import load_workbook
        book=load_workbook(paths['excel'],read_only=True)
        try:self.assertIn('取得期待の未確認',book.sheetnames)
        finally:book.close()
        self.assertIn('判定の適否に含めない取得確認',Path(paths['html']).read_text())

    def make_inventory_run(self, *, alter=None, freeze_inventory=True, point='1.1.1-01', contract=None):
        page = 'p01.html'
        contract = contract or dict(
            checkpoint='1.1.1-02',page=page,state='initial',kind='inventory',
            targets=['#art','#vector','#plot'],formats=['css-background','inline-svg','canvas'],rationale='画像形式を照合する。')
        run,meta,job,progress = self.make_run(mode='machine', point=point, contract=contract)
        entry = progress['jobs'][job['id']][page]
        entry.update(status='completed',exit_code=0)
        core.save(run/'progress.json',progress)
        attempt = run/entry['directory']
        env = 'desktop'
        url = job['urls'][page]
        folder = attempt/'evidence'/'initial'
        html = 'http://www.w3.org/1999/xhtml'
        svg = 'http://www.w3.org/2000/svg'
        files = {
            attempt.parent/'receipt.json': dict(job_id=job['id'],page=page,mode=job['mode'],url=url,status='completed',exit_code=0),
            attempt/'capture-manifest.json': {'captures':[dict(url=url,state='initial',execution='completed',collection_state='finished',
                                                              environment=env,evidence_dir='evidence/initial')]},
            attempt/'exploration.json': {'nodes': [], 'edges': []},
            folder/'transition.json': dict(environment=env,route=[],error=None,blocked_requests=[],native_events=[],
                                          settling=[{'status':'quiet'}]),
            folder/'inventory.json': dict(url=url,nodeCount=3,truncated=False,nodes=[
                dict(selector='#art',tag='p',namespace=html,visible=True,backgroundImage='url("http://127.0.0.1/image.png")'),
                dict(selector='#vector',tag='svg',namespace=svg,visible=True),
                dict(selector='#plot',tag='canvas',namespace=html,visible=True)]),
        }
        if alter:
            alter(files,attempt,folder)
        for path,value in files.items():
            core.save(path,value)
        core.freeze(run,[path for path in files if freeze_inventory or path.name!='inventory.json'])
        return run,meta,job,progress,folder/'inventory.json'

    def test_acquisition_matches_complete_initial_inventory_without_adding_a_verdict(self):
        from benchmarks import reporting
        from openpyxl import load_workbook
        run,meta,job,progress,_ = self.make_inventory_run()
        result = core.score(run)
        self.assertEqual(result['counts'],{'not_evaluated':2})
        self.assertEqual(result['pending_evidence_contracts'],[])
        self.assertEqual(result['selected_checks_status'],'incomplete')
        (match,) = result['matched_evidence_contracts']
        self.assertEqual(match['status'],'matched')
        self.assertEqual([r['format'] for r in match['targets']],['css-background','inline-svg','canvas'])
        self.assertEqual({Path(path).name for path in match['evidence']},
                         {'inventory.json','transition.json','capture-manifest.json','receipt.json'})
        self.submit(run,meta,job,[self.observation(job,progress),self.observation(job,progress,target='#two',outcome='passed')])
        result = core.score(run)
        self.assertEqual(result['counts'],{'correct':2})
        self.assertEqual(result['selected_checks_status'],'clear_for_selected_checks')
        files = reporting.write(run,result)
        book = load_workbook(files['excel'],read_only=True)
        try:
            row = tuple(next(book['取得期待の一致'].values))  # Header precedes the acquisition-only values.
            self.assertIn('取得した対象',row)
            values = list(book['取得期待の一致'].values)[1]
            self.assertIn('#vector (inline-svg)', values[row.index('取得した対象')])
            self.assertIn(match['evidence'][0], values[row.index('証拠')])
        finally:
            book.close()
        self.assertIn('href="../../'+match['evidence'][0]+'"',Path(files['html']).read_text())

    def test_acquisition_leaves_partial_or_unbound_inventory_unconfirmed(self):
        def edit_inventory(edit):
            return lambda files,attempt,folder: edit(files[folder/'inventory.json'])

        edits = {
            'truncated':edit_inventory(lambda inv:inv.update(truncated=True)),
            'missing':edit_inventory(lambda inv:(inv['nodes'].pop(),inv.update(nodeCount=2))),
            'duplicate':edit_inventory(lambda inv:(inv['nodes'].append(inv['nodes'][0]),inv.update(nodeCount=4))),
            'wrong format':edit_inventory(lambda inv:inv['nodes'][0].update(backgroundImage='none')),
            'wrong namespace':edit_inventory(lambda inv:inv['nodes'][1].update(namespace='http://www.w3.org/1999/xhtml')),
            'old evidence':edit_inventory(lambda inv:inv['nodes'][1].pop('namespace')),
            'hidden':edit_inventory(lambda inv:inv['nodes'][2].update(visible=False)),
            'wrong url':edit_inventory(lambda inv:inv.update(url='http://127.0.0.1:8000/1.1.1/p02.html')),
            'wrong state':lambda files,attempt,folder:files[attempt/'capture-manifest.json']['captures'][0].update(state='after'),
            'wrong transition':lambda files,attempt,folder:files[folder/'transition.json'].update(route=[{'type':'click'}]),
            'different environment':lambda files,attempt,folder:files[folder/'transition.json'].update(environment='mobile'),
            'settling limit':lambda files,attempt,folder:files[folder/'transition.json'].update(settling=[{'status':'timeout'}]),
            'foreign receipt':lambda files,attempt,folder:files[attempt.parent/'receipt.json'].update(job_id='other'),
        }
        for case,edit in [*edits.items(),('unfrozen',None)]:
            with self.subTest(case=case):
                run,*_ = self.make_inventory_run(alter=edit,freeze_inventory=case!='unfrozen')
                result = core.score(run)
                self.assertEqual(result['matched_evidence_contracts'],[])
                (pending,) = result['pending_evidence_contracts']
                self.assertEqual(pending['status'],'not_evaluated')
                self.assertTrue(pending['observed'])

    def test_acquisition_integrity_and_comparison_are_independent_of_verdicts(self):
        run,*_,inventory = self.make_inventory_run()
        matched = core.score(run)
        partial_run,*_ = self.make_inventory_run(freeze_inventory=False)
        partial = core.score(partial_run)
        self.assertEqual(matched['counts'],partial['counts'])
        regression = core.compare(matched,partial)
        self.assertEqual(regression['status'],'regressions')
        self.assertEqual(regression['regressions'][0]['kind'],'acquisition')
        self.assertEqual(core.compare(partial,matched)['improvements'][0]['after'],'matched')
        inventory.write_text('{}')
        with self.assertRaisesRegex(ValueError,'変更された'):
            core.score(run)

    def make_status_run(self, role_attribute, *, edit=None, freeze_capture=True):
        page, state = 'p01.html', 'after-save'
        contract = dict(checkpoint='4.1.3-01', page=page, state=state, kind='state-capture',
                        targets=['#subject'], captures=['待機中', '保存しました'], role_attribute=role_attribute,
                        rationale='保存後の表示と役割を取得する。')
        run, _, job, progress = self.make_run(mode='machine', point='4.1.3-02', kind='screen-reader',
                                              defer=True, contract=contract)
        # Rebuild the synthetic input snapshots before freezing this specific job.
        spec = dict(action={'type': 'click', 'selector': '#save'}, target='#subject')
        job['states'].append(dict(id=state, status_capture=spec))
        oracle = core.load(run/'oracle.snapshot.json')
        oracle['suites'][0]['cases'][0]['states'] = job['states']
        meta = core.load(run/'run.json')
        meta.update(oracle_digest=core.digest(oracle), corpus_digest=core.digest(oracle))
        core.save(run/'run.json', meta)
        core.save(run/'oracle.snapshot.json', oracle)
        core.save(run/'worker/tasks.json', {'jobs': [job]})
        (run/'integrity.json').unlink()

        entry = progress['jobs'][job['id']][page]
        entry.update(status='completed', exit_code=0)
        core.save(run/'progress.json', progress)
        attempt = run/entry['directory']
        url = job['urls'][page]
        source = run/'worker/public/4.1.3'/page
        source.parent.mkdir(parents=True)
        source.write_text('<!doctype html><title>Fixture</title>')
        core.save(attempt/'exploration.json', {'nodes': [], 'edges': []})
        core.save(attempt.parent/'receipt.json', dict(job_id=job['id'], page=page, mode=job['mode'], url=url,
                                                      status='completed', exit_code=0))
        proof = attempt.parent/f'status-capture-{state}.json'
        snapshot = dict(visible=True, backend_node_id=72, time_origin='123', url=url,
                        role_attribute=role_attribute, ax_role=role_attribute or 'paragraph')
        observed = dict(job_id=job['id'], page=page, state=state, spec=spec, mode=job['mode'], url=url,
                        fixture_sha256=core.file_hash(source), not_a_screen_reader_test=True,
                        requests_blocked=[], native_events=[], status='observed',
                        before=dict(snapshot, text='待機中', sampled_at=15),
                        after=dict(snapshot, text='保存しました', sampled_at=540),
                        event=dict(type='click', isTrusted=True, is_main_frame=True, expectedTargetMatched=True,
                                   url=url, target={'id': 'save'}, documentId='123-abc', timestamp=38))
        if edit:
            edit(observed)
        core.save(proof, observed)
        core.freeze(run, [path for path in run.rglob('*') if path.is_file() and path.name != '.audit.lock'
                          and (freeze_capture or path != proof)])
        return run, proof

    def make_inactive_control_run(self, *, alter=None, declared=True, freeze_proof=True):
        from benchmarks import inactive_control_probe as method

        run, meta, job, progress = self.make_run(mode='machine', point=method.CHECKPOINT)
        page = job['pages'][0]
        oracle = core.load(run/'oracle.snapshot.json')
        case = oracle['suites'][0]['cases'][0]
        if declared:
            job['states'][0]['inactive_control_target'] = '#one'
        case['states'] = job['states']
        case['expectations'] = [dict(case['expectations'][0], expected='inapplicable')]
        meta.update(oracle_digest=core.digest(oracle), corpus_digest=core.digest(oracle))
        core.save(run/'run.json', meta)
        core.save(run/'oracle.snapshot.json', oracle)
        core.save(run/'worker/tasks.json', {'jobs': [job]})
        (run/'integrity.json').unlink()

        source = run/'worker/public/1.4.3'/page
        source.parent.mkdir(parents=True)
        source.write_text('<!doctype html><button id="one" disabled>Save</button>')
        entry = progress['jobs'][job['id']][page]
        entry.update(status='completed', exit_code=0)
        core.save(run/'progress.json', progress)
        attempt = run/entry['directory']
        core.save(attempt/'exploration.json', {'nodes': [], 'edges': []})
        core.save(attempt.parent/'receipt.json', dict(job_id=job['id'], page=page, mode=job['mode'], url=job['urls'][page],
                                                      status='completed', exit_code=0))
        receipt = method.binding(meta, job, page, '#one', core.file_hash(source))
        fingerprint = 'f' * 64
        dom = dict(stableTarget=True, nativeButton=True, nativeDisabled=True, displayed=True, hitTested=True,
                   focused=False, animated=False, unsupported=[], policyViolations=[], url=method.DOCUMENT_URL,
                   viewport=list(method.VIEWPORT.values()), point=[50, 60], documentId=12,
                   render_state_sha256=fingerprint)
        captured = dict(scope=method.SCOPE, status='inactive_observed', source=source.name,
                        source_sha256=core.file_hash(source), target='#one', blocked_requests=[], browser='unit fixture',
                        dom=dom, accessibility={'node': 4, 'role': 'button', 'disabled': True},
                        step_state_hashes=dict.fromkeys(method.STEPS, fingerprint),
                        events=[dict(type='keydown', key='Tab', trusted=True, target=''),
                                dict(type='pointerdown', pointer='mouse', trusted=True, target='one'),
                                dict(type='pointerup', pointer='mouse', trusted=True, target='one')])
        if alter:
            alter(receipt, captured)
        proof = attempt.parent/'inactive-control.json'
        core.save(proof, dict(receipt, observation=captured))
        core.freeze(run, [path for path in run.rglob('*') if path.is_file() and path.name != '.audit.lock'
                          and (freeze_proof or path != proof)])
        return run, proof

    def test_inactive_control_scores_only_valid_frozen_initial_receipt(self):
        valid, proof = self.make_inactive_control_run()
        row, = core.score(valid)['rows']
        self.assertEqual((row['actual'], row['grade']), ('inapplicable', 'correct'))
        self.assertIn(proof.relative_to(valid).as_posix(), row['evidence'])
        for changes in ({'declared': False}, {'freeze_proof': False}):
            with self.subTest(changes=changes):
                run, _ = self.make_inactive_control_run(**changes)
                self.assertEqual(core.score(run)['rows'][0]['actual'], 'not_run')

        edits = (
            lambda receipt, proof: receipt.update(run_id='foreign'),
            lambda receipt, proof: receipt.update(state='other'),
            lambda receipt, proof: proof.update(target='#two'),
            lambda receipt, proof: proof.update(source_sha256='wrong'),
            lambda receipt, proof: proof['accessibility'].update(disabled=False),
            lambda receipt, proof: proof['events'][1].update(trusted=False),
            lambda receipt, proof: proof['events'].append(dict(type='click', trusted=True, target='one')),
            lambda receipt, proof: proof['step_state_hashes'].update(hover='changed'),
            lambda receipt, proof: proof['dom'].update(displayed=False),
            lambda receipt, proof: proof['dom'].update(point=[2000, 0]),
        )
        for index, edit in enumerate(edits):
            with self.subTest(mutation=index):
                run, _ = self.make_inactive_control_run(alter=edit)
                self.assertEqual(core.score(run)['rows'][0]['grade'], 'not_evaluated')
        proof.write_text('{}')
        with self.assertRaisesRegex(ValueError, '変更された'):
            core.score(valid)

    def test_inactive_control_holds_when_exact_axe_result_disagrees(self):
        run, _ = self.make_inactive_control_run()
        previous = dict(page='p01.html', state='initial', checkpoint='1.4.3-01', target='#one',
                        outcome='failed', evidence=['axe.json'])
        with patch('benchmarks.core.program_predictions', return_value={core.observation_key(previous): previous}):
            row, = core.score(run)['rows']
        self.assertEqual(row['actual'], 'cant_tell')
        self.assertIn('axe.json', row['evidence'])

    def make_text_paint_run(self, *, mode='ai', enabled=True, weight=400, change=None):
        from PIL import Image
        from measure import contrast
        from benchmarks import text_paint_evidence as method, text_paint_probe as probe

        run, meta, job, progress = self.make_run(mode=mode, point=method.CHECKPOINT)
        page = job['pages'][0]
        job['states'][0]['text_paint_target'] = '#one'
        oracle = core.load(run/'oracle.snapshot.json')
        oracle['suites'][0]['cases'][0]['states'] = job['states']
        meta.update(oracle_digest=core.digest(oracle), corpus_digest=core.digest(oracle))
        if enabled:
            meta['configuration']['text_paint_images'] = method.IMAGE_BUDGET
        core.save(run/'run.json', meta)
        core.save(run/'oracle.snapshot.json', oracle)
        core.save(run/'worker/tasks.json', {'jobs': [job]})
        (run/'integrity.json').unlink()

        source = run/'worker/public/1.4.3'/page
        source.parent.mkdir(parents=True)
        source.write_text('<!doctype html><p id="one">Pink</p>')
        entry = progress['jobs'][job['id']][page]
        entry.update(status='completed', exit_code=0)
        core.save(run/'progress.json', progress)
        attempt = run/entry['directory']
        core.save(attempt/'exploration.json', {'nodes': [], 'edges': []})
        core.save(attempt.parent/'receipt.json', dict(job_id=job['id'], page=page, mode=mode, url=job['urls'][page],
                                                      status='completed', exit_code=0))
        output = attempt.parent/method.DIRECTORY
        output.mkdir()
        receipt = method.binding(meta, job, page, '#one', core.file_hash(source))
        fill = 'rgb(119, 119, 119)'
        frame_colors = {'transparent': (255, 255, 255), 'black': (0, 0, 0), 'white': (255, 255, 255)}
        frames = {}
        for stage, color in probe.CAPTURE_STAGES.items():
            path = output/f'{stage}.png'
            with Image.new('RGB', tuple(probe.VIEWPORT.values()), 'white') as image:
                image.putpixel((20, 20), frame_colors.get(stage, (119, 119, 119)))
                image.save(path)
            frames[stage] = dict(path=path.name, fill=color or fill, sha256=core.file_hash(path))
        ratio = contrast('#777777', '#ffffff')['ratio']
        threshold = 3 if weight >= 700 else 4.5
        measurement = dict(status='measured', scope=probe.RESULT_SCOPE, target='#one', source=source.name,
                           source_sha256=core.file_hash(source), blocked_requests=[], frames=frames,
                           image_limit=method.IMAGE_BUDGET, range_css_px=[18, 18, 8, 8],
                           viewport_css_px=list(probe.VIEWPORT.values()), scroll_css_px=[0, 0],
                           browser='unit fixture', foreground='#777777', background='#ffffff',
                           font_css_px=20, font_weight=weight, ratio=ratio, threshold=threshold,
                           threshold_met=ratio >= threshold)
        if change is not None:
            change(receipt, measurement, output)
        core.save(output/'receipt.json', receipt)
        core.save(output/'result.json', measurement)
        core.freeze(run, [run/'run.json', run/'oracle.snapshot.json', run/'worker/tasks.json', source,
                          *[p for p in (run/'audit-runs').rglob('*') if p.is_file()]])
        return run, output

    @unittest.skipUnless(find_spec('PIL'), 'Pillow is optional')
    def test_text_paint_recomputes_unrounded_ratio_and_font_threshold(self):
        normal, _ = self.make_text_paint_run()
        row = core.score(normal)['rows'][0]
        self.assertEqual((row['actual'], row['grade'], row['method']), ('failed', 'correct', 'program'))
        self.assertIn('4.478089', row['observed'])
        self.assertEqual(sum(path.endswith('.png') for path in row['evidence']), 7)
        bold, _ = self.make_text_paint_run(weight=700)
        self.assertEqual(core.score(bold)['rows'][0]['actual'], 'passed')

    @unittest.skipUnless(find_spec('PIL'), 'Pillow is optional')
    def test_text_paint_binds_result_and_frame_provenance(self):
        mutations = [
            lambda receipt, data, out: receipt.update(run_id='foreign'),
            lambda receipt, data, out: receipt.update(state='after-click'),
            lambda receipt, data, out: data.update(target='#two'),
            lambda receipt, data, out: data.update(viewport_css_px=[1280, 800]),
            lambda receipt, data, out: data.update(source_sha256='foreign'),
            lambda receipt, data, out: data.update(ratio=4.5, threshold_met=True),
            lambda receipt, data, out: data.update(font_css_px=float('nan')),
            lambda receipt, data, out: data.update(status='hold', reason={'unexpected': 'type'}),
            lambda receipt, data, out: data['frames'].pop('restored'),
            lambda receipt, data, out: data['frames']['black'].update(sha256='wrong'),
            lambda receipt, data, out: (out/'restored.png').unlink(),
            lambda receipt, data, out: data['frames']['restored'].update(path='original.png'),
        ]
        for i, mutation in enumerate(mutations):
            with self.subTest(mutation=i):
                run, _ = self.make_text_paint_run(change=mutation)
                self.assertEqual(core.score(run)['rows'][0]['grade'], 'not_evaluated')

    @unittest.skipUnless(find_spec('PIL'), 'Pillow is optional')
    def test_text_paint_does_not_grade_without_image_mode_or_opt_in(self):
        for mode, enabled in [('machine', True), ('screen-reader', True), ('ai', False)]:
            with self.subTest(mode=mode, enabled=enabled):
                run, _ = self.make_text_paint_run(mode=mode, enabled=enabled)
                self.assertEqual(core.score(run)['rows'][0]['grade'], 'not_evaluated')

    @unittest.skipUnless(find_spec('PIL'), 'Pillow is optional')
    def test_text_paint_frozen_image_tampering_is_rejected(self):
        run, output = self.make_text_paint_run()
        (output/'black.png').write_bytes(b'modified')
        with self.assertRaisesRegex(ValueError, '変更された'):
            core.score(run)

    def test_text_paint_opt_in_cannot_be_added_to_resume_or_machine(self):
        from benchmarks import runner

        with self.assertRaisesRegex(ValueError, 'ai又はfull'), patch('benchmarks.runner.server') as server:
            runner.collect(Path(self.temp.name)/'machine', criterion=['1.4.3'], selected_modes=['machine'], text_paint=True)
        server.assert_not_called()
        run, meta, _, _ = self.make_run(mode='ai', point='1.4.3-02')
        meta.update(implementation_digest=runner.implementation_digest(), environment={'unit': 'environment'})
        core.save(run/'run.json', meta)
        integrity = core.load(run/'integrity.json')
        integrity['files']['run.json'] = core.file_hash(run/'run.json')
        core.save(run/'integrity.json', integrity)
        with patch('benchmarks.runner.environment', return_value=meta['environment']), patch('benchmarks.runner.server') as server:
            with self.assertRaisesRegex(ValueError, '--text-paint'):
                runner.collect(run, resume=True, text_paint=True)
        server.assert_not_called()

    def test_status_acquisition_matches_same_document_visible_states_without_speech(self):
        for role in ('status', None):
            with self.subTest(role=role):
                run, _ = self.make_status_run(role)
                result = core.score(run)
                self.assertEqual(result['pending_evidence_contracts'], [])
                match, = result['matched_evidence_contracts']
                self.assertIn('待機中 → 保存しました', match['observed'])
                self.assertIn(role or 'paragraph', match['observed'])
                self.assertEqual(result['counts'], {'deferred': 2})
                self.assertEqual(result['overall_status'], 'incomplete')
                self.assertTrue(all(row['actual'] == 'not_run' for row in result['rows']))

    def test_status_acquisition_leaves_unverified_click_or_change_unconfirmed(self):
        edits = [
            lambda r: r['event'].update(isTrusted=False),
            lambda r: r['event'].update(documentId='234-other'),
            lambda r: r['event'].update(timestamp=600),
            lambda r: r['event'].update(target={'id': 'other'}),
            lambda r: r['after'].update(backend_node_id=73),
            lambda r: r['after'].update(visible=False),
            lambda r: r['after'].update(text='待機中'),
            lambda r: r['after'].update(ax_role='paragraph'),
            lambda r: r.update(fixture_sha256='different'),
            lambda r: r.update(requests_blocked=[{'url': 'http://127.0.0.1/other'}]),
        ]
        for edit in [None, *edits]:
            with self.subTest(edit=edit):
                run, _ = self.make_status_run('status', edit=edit, freeze_capture=edit is not None)
                result = core.score(run)
                self.assertEqual(result['matched_evidence_contracts'], [])
                pending, = result['pending_evidence_contracts']
                self.assertEqual(pending['status'], 'not_evaluated')
                self.assertEqual(result['counts'], {'deferred': 2})

    def test_status_acquisition_checks_frozen_receipt_integrity(self):
        run, proof = self.make_status_run('status')
        proof.write_text('{}')
        with self.assertRaisesRegex(ValueError, '変更された'):
            core.score(run)

    def make_geometry_run(self, size, *, edit=None, contract=None):
        contract = contract or dict(
            checkpoint='2.5.8-01', page='p01.html', state='initial', kind='geometry',
            targets=['#a', '#b'], width=size, height=size, gap=2, rationale='矩形の寸法と辺間隔を照合する。')

        def geometry(files, attempt, folder):
            inventory = files[folder/'inventory.json']
            inventory.update(nodeCount=2, nodes=[
                dict(selector='#a', visible=True, rect=dict(x=30, y=113.703125, width=size, height=size)),
                dict(selector='#b', visible=True, rect=dict(x=32+size, y=113.703125, width=size, height=size)),
            ])
            if edit:
                edit(inventory)

        return self.make_inventory_run(point='2.5.8-02', contract=contract, alter=geometry)

    def test_geometry_records_actual_dimensions_without_a_size_verdict(self):
        from benchmarks import reporting
        from openpyxl import load_workbook

        for size in (16, 28):
            with self.subTest(size=size):
                run,*_ = self.make_geometry_run(size)
                result = core.score(run)
                self.assertEqual(result['counts'], {'not_evaluated': 2})
                self.assertEqual(result['pending_evidence_contracts'], [])
                (matched,) = result['matched_evidence_contracts']
                self.assertEqual(matched['gap'], 2)
                self.assertEqual(matched['targets'], [
                    dict(target='#a', format='css-rect', rect=dict(x=30, y=113.703125, width=size, height=size)),
                    dict(target='#b', format='css-rect', rect=dict(x=32+size, y=113.703125, width=size, height=size)),
                ])
                paths = reporting.write(run, result)
                html = Path(paths['html']).read_text()
                self.assertIn('辺間隔 2 CSS px', html)
                self.assertIn('href="../../'+matched['evidence'][0]+'"', html)
                book = load_workbook(paths['excel'], read_only=True)
                try:
                    headers, observations = book['取得期待の一致'].values
                    self.assertIn(f'#a {size} × {size}', observations[headers.index('観察')])
                    self.assertIn(matched['evidence'][0], observations[headers.index('証拠')])
                finally:
                    book.close()

    def test_geometry_measures_a_reversed_vertical_gap(self):
        def vertical(inventory):
            first, second = inventory['nodes']
            first['rect'].update(y=38)
            second['rect'].update(x=30, y=20)

        run,*_ = self.make_geometry_run(16, edit=vertical)
        (matched,) = core.score(run)['matched_evidence_contracts']
        self.assertEqual(matched['gap'], 2)
        self.assertIn('垂直の辺間隔', matched['observed'])

    def test_geometry_requires_unique_well_formed_aligned_expected_rectangles(self):
        edits = {
            'wrong gap': lambda inv: inv['nodes'][1]['rect'].update(x=49),
            'wrong size': lambda inv: inv['nodes'][1]['rect'].update(width=17),
            'overlap': lambda inv: inv['nodes'][1]['rect'].update(x=45),
            'staggered': lambda inv: inv['nodes'][1]['rect'].update(y=114.703125),
            'non-finite': lambda inv: inv['nodes'][1]['rect'].update(x=float('nan')),
            'boolean': lambda inv: inv['nodes'][1]['rect'].update(width=True),
            'zero-size': lambda inv: inv['nodes'][1]['rect'].update(width=0),
            'duplicate': lambda inv: inv.update(nodes=[*inv['nodes'], inv['nodes'][1]], nodeCount=3),
            'hidden': lambda inv: inv['nodes'][1].update(visible=False),
            'truncated': lambda inv: inv.update(truncated=True),
        }
        for label,edit in edits.items():
            with self.subTest(label=label):
                run,*_ = self.make_geometry_run(16, edit=edit)
                result = core.score(run)
                self.assertEqual(result['matched_evidence_contracts'], [])
                (pending,) = result['pending_evidence_contracts']
                self.assertEqual(pending['status'], 'not_evaluated')
                self.assertTrue(pending['observed'])
                self.assertTrue(pending['evidence'])

    def test_geometry_leaves_inline_context_for_review(self):
        inline = dict(checkpoint='2.5.8-01', page='p01.html', state='initial', kind='geometry',
                      targets=['#a'], context='inline-in-paragraph', expected_height_below=24, rationale='文中のリンクを確認する。')
        run,*_ = self.make_geometry_run(16, contract=inline)
        result = core.score(run)
        self.assertEqual(result['matched_evidence_contracts'], [])
        (pending,) = result['pending_evidence_contracts']
        self.assertEqual(pending['status'], 'not_evaluated')

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

    def test_native_worker_keeps_new_status_patterns_unverified(self):
        from benchmarks.native_status import work
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp);jobs=[]
            for i in range(1,4):
                page=f'p0{i}.html'
                jobs.append(dict(id=f'full--4.1.3--c0{i}',mode='full',criterion='4.1.3',pages=[page],urls={page:f'http://127.0.0.1:8000/4.1.3/{page}'}))
            core.save(run/'worker/tasks.json',dict(run_id='unit',corpus_digest='unit',jobs=jobs))
            core.freeze(run,[run/'worker/tasks.json'])
            def blocked(root,area):core.save(area/'speech/screen-reader.json',{'status':'blocked','unit_mock':True})
            with patch('benchmarks.native_status.runner.server'),patch('benchmarks.native_status.capture',side_effect=blocked) as capture:
                result=work(run,'/unit/root')
            self.assertEqual(capture.call_count,2)
            self.assertEqual({r['job_id'] for r in result},{j['id'] for j in jobs[:2]})
            self.assertEqual({r['outcome'] for r in result},{'cant_tell'})

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
