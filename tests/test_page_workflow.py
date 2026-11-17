import copy
import asyncio
import json
from pathlib import Path
import sys
import unittest

from openpyxl import load_workbook

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'skills/wcag-audit-kit/scripts')]
import audit
import checksheet
import page_explorer
import page_workflow
import workbook
import test_ledger as fixture


class WorkflowTest(unittest.TestCase):
    def setUp(self):fixture.LedgerTest.setUp(self)
    def tearDown(self):fixture.LedgerTest.tearDown(self)

    def graph(self):
        path=self.run/'evidence/abc/axe.json'
        audit.save(path,{'violations':[{'id':'image-alt','help':'Images have alternatives','tags':['wcag111'],
            'nodes':[{'target':['img.chart'],'html':'<img src="chart.png">','failureSummary':'Missing alt'}]}],
            'passes':[{'id':'document-title','help':'Document has a title','tags':['wcag242'],'nodes':[]}],
            'incomplete':[],'inapplicable':[]})
        graph={'schema_version':'1','config_digest':audit.digest(self.config),'queue':[],'remaining':[],
            'nodes':[{'environment':'desktop','fingerprint':'fixture','capture':'abc--initial--desktop','evidence_dir':'evidence/abc','route':[]}],
            'edges':[],'running':False,'proof':[audit.evidence_item(self.run,'evidence/abc/axe.json')],'steps':1}
        audit.save(self.run/'exploration.json',graph);return graph

    def test_machine_pass_never_becomes_criterion_pass(self):
        self.graph();result=audit.outcomes(self.run)
        self.assertEqual(result['counts'],{'not_run':55})
        self.assertEqual(len(result['machine_checks']),2)
        model=checksheet.build(result,audit.CATALOG)
        title=[r for r in model['rows'] if r['criterion']=='2.4.2']
        self.assertEqual(title[0]['judgment'],'未確認');self.assertEqual(title[1]['judgment'],'○ 通過（機械）')
        image=[r for r in model['rows'] if r['criterion']=='1.1.1']
        self.assertEqual(image[0]['judgment'],'未確認');self.assertEqual(image[1]['judgment'],'× 問題あり（機械）')
        self.assertIn('img.chart',image[1]['locations'])

    def test_machine_issue_summary_keeps_all_affected_states_and_proof(self):
        self.graph();checks=page_workflow.machine_checks(self.run)
        extra=dict(checks[0],capture='another-state',evidence='evidence/abc/another.json')
        grouped=page_workflow.grouped_machine_issues(checks+[extra])
        self.assertEqual(len(grouped),1);self.assertEqual(grouped[0]['count'],2)
        self.assertIn('another-state',grouped[0]['capture_ids']);self.assertEqual(len(grouped[0]['proof']),2)

    def test_html_and_excel_keep_identical_extra_level_machine_observations(self):
        graph=self.graph();path=self.run/'evidence/abc/axe.json';value=audit.load(path)
        value['passes'].append({'id':'scrollable-region-focusable','help':'Scrollable region must have keyboard access',
            'tags':['wcag211','wcag213'],'nodes':[]})
        audit.save(path,value);graph['proof']=[audit.evidence_item(self.run,'evidence/abc/axe.json')];audit.save(self.run/'exploration.json',graph)
        files=audit.write_page_reports(self.run,self.config['url'])
        result=page_workflow.page_result(self.run,self.config['url'])
        model=checksheet.build(result,audit.CATALOG,manifest=self.manifest)
        book=load_workbook(files['excel'])
        try:
            self.assertEqual(book['チェックシート'].max_row,len(model['rows'])+6)
            for i,row in enumerate(model['rows'],7):
                self.assertEqual([c.value or '' for c in book['チェックシート'][i]],[row.get(k,'') for k,_ in checksheet.COLUMNS])
            self.assertEqual(book['機械検査'].max_row,len(result['machine_checks'])+1)
        finally:book.close()

    def test_changed_machine_proof_is_rejected(self):
        self.graph();(self.run/'evidence/abc/axe.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'探索の証拠'):audit.outcomes(self.run)

    def test_resume_rejects_different_explorer_implementation(self):
        self.config['scope'].update(mode='configured',pages=[self.config['url']],max_pages=1)
        self.config['environments']=self.config['environments'][:1]
        meta=audit.load(self.run/'run.json');meta.update(config=self.config,config_digest=audit.digest(self.config));audit.save(self.run/'run.json',meta)
        plan=audit.load(self.run/'plan.json');plan['config_digest']=meta['config_digest'];audit.save(self.run/'plan.json',plan)
        graph=self.graph();graph['implementation_digest']='older implementation';audit.save(self.run/'exploration.json',graph)
        with self.assertRaisesRegex(ValueError,'実装が変わった'):asyncio.run(page_explorer.explore(self.run))

    def test_pending_exploration_prevents_false_completion(self):
        graph=self.graph();graph['queue']=[{'route':[{'type':'click','selector':'#nested'}],'environment':'desktop'}]
        audit.save(self.run/'exploration.json',graph)
        result=audit.outcomes(self.run)
        self.assertFalse(result['exploration']['complete']);self.assertIn('探索待ち',result['exploration']['remaining'][0])
        self.assertFalse(result['audit_complete'])

    def test_resolution_requires_current_graph_and_verified_evidence(self):
        graph=self.graph();graph['remaining']=['iframe内部の追加検査'];audit.save(self.run/'exploration.json',graph)
        value={'graph_digest':audit.digest(graph),'resolutions':[{'item':graph['remaining'][0],
            'observed':'合成試験で追加検査の保存形式を確認する。','evidence':['evidence/abc/axe.json']}]}
        page_workflow.resolve(self.run,value);self.assertTrue(page_explorer.status(self.run)['complete'])
        graph['steps']=2;audit.save(self.run/'exploration.json',graph)
        self.assertFalse(page_explorer.status(self.run)['complete'])
        with self.assertRaisesRegex(ValueError,'更新済み'):page_workflow.resolve(self.run,value)

    def test_resolution_cannot_hide_queued_routes(self):
        graph=self.graph();graph['queue']=[{'route':[],'environment':'desktop'}];audit.save(self.run/'exploration.json',graph)
        page_workflow.resolve(self.run,{'graph_digest':audit.digest(graph),'resolutions':[]})
        self.assertFalse(page_explorer.status(self.run)['complete'])

    def test_resolution_rejects_missing_evidence(self):
        graph=self.graph();graph['remaining']=['未確認'];audit.save(self.run/'exploration.json',graph)
        for evidence in [[],['missing.json']]:
            with self.assertRaises(ValueError):page_workflow.resolve(self.run,{'graph_digest':audit.digest(graph),
                'resolutions':[{'item':'未確認','observed':'合成試験で追加検査の形式を確認する。','evidence':evidence}]})

    def test_separate_resolutions_accumulate_without_rewriting_history(self):
        graph=self.graph();graph['remaining']=['gap A','gap B'];audit.save(self.run/'exploration.json',graph)
        def value(item):return {'graph_digest':audit.digest(graph),'resolutions':[{'item':item,
            'observed':'合成試験で対象ごとの追加検査と証拠の保持を確認する。','evidence':['evidence/abc/axe.json']}]}
        first=page_workflow.resolve(self.run,value('gap A'));path=Path(first['file']);before=path.read_bytes()
        self.assertEqual(page_explorer.status(self.run)['remaining'],['gap B'])
        page_workflow.resolve(self.run,value('gap B'))
        self.assertTrue(page_explorer.status(self.run)['complete'])
        saved=audit.load(self.run/audit.run_plan(self.run)['exploration_review'])
        self.assertEqual([r['item'] for r in saved['resolutions']],['gap A','gap B'])
        self.assertEqual(path.read_bytes(),before)

    def test_resolution_on_a_new_graph_does_not_reuse_previous_items(self):
        graph=self.graph();graph['remaining']=['gap A','gap B'];audit.save(self.run/'exploration.json',graph)
        def value(item):return {'graph_digest':audit.digest(graph),'resolutions':[{'item':item,
            'observed':'合成試験で探索の版ごとに追加検査を区別する。','evidence':['evidence/abc/axe.json']}]}
        page_workflow.resolve(self.run,value('gap A'))
        graph['steps']+=1;audit.save(self.run/'exploration.json',graph)
        page_workflow.resolve(self.run,value('gap B'))
        self.assertEqual(page_explorer.status(self.run)['remaining'],['gap A'])

    def test_recording_one_resolution_again_keeps_other_items(self):
        graph=self.graph();graph['remaining']=['gap A','gap B'];audit.save(self.run/'exploration.json',graph)
        items=[{'item':name,'observed':'合成試験の最初の追加検査を記録する。','evidence':['evidence/abc/axe.json']} for name in graph['remaining']]
        page_workflow.resolve(self.run,{'graph_digest':audit.digest(graph),'resolutions':items})
        evidence=self.run/'evidence/abc/follow-up.json';audit.save(evidence,{'observed':'second observation'})
        replacement=dict(items[0],observed='合成試験で対象Aだけの追加検査を更新する。',evidence=['evidence/abc/follow-up.json'])
        page_workflow.resolve(self.run,{'graph_digest':audit.digest(graph),'resolutions':[replacement]})
        saved=audit.load(self.run/audit.run_plan(self.run)['exploration_review'])
        self.assertEqual(saved['resolutions'],[replacement,items[1]])
        self.assertTrue(page_explorer.status(self.run)['complete'])
        self.assertEqual({p['path'] for p in saved['verified_evidence']},{'evidence/abc/axe.json','evidence/abc/follow-up.json'})

    def test_changed_inherited_proof_blocks_an_additional_resolution(self):
        graph=self.graph();graph['remaining']=['gap A','gap B'];audit.save(self.run/'exploration.json',graph)
        proof=self.run/'evidence/abc/follow-up.json';audit.save(proof,{'observed':'original'})
        def value(item):return {'graph_digest':audit.digest(graph),'resolutions':[{'item':item,
            'observed':'合成試験で過去の解消に使用した証拠を保持する。','evidence':['evidence/abc/follow-up.json']}]}
        page_workflow.resolve(self.run,value('gap A'));before=(self.run/'plan.json').read_bytes()
        audit.save(proof,{'observed':'changed'})
        with self.assertRaisesRegex(ValueError,'追加検査の証拠'):page_workflow.resolve(self.run,value('gap B'))
        self.assertEqual((self.run/'plan.json').read_bytes(),before)

    def test_legacy_empty_resolution_snapshot_does_not_block_new_items(self):
        graph=self.graph();graph['remaining']=['gap A'];audit.save(self.run/'exploration.json',graph)
        audit.save(self.run/'exploration-reviews/legacy.json',{'graph_digest':audit.digest(graph),'verified_evidence':[]})
        plan=audit.run_plan(self.run);plan['exploration_review']='exploration-reviews/legacy.json';audit.save(self.run/'plan.json',plan)
        self.assertEqual(page_explorer.status(self.run)['remaining'],['gap A'])
        page_workflow.resolve(self.run,{'graph_digest':audit.digest(graph),'resolutions':[{'item':'gap A',
            'observed':'合成試験で空の旧記録から追加検査を記録する。','evidence':['evidence/abc/axe.json']}]})
        self.assertTrue(page_explorer.status(self.run)['complete'])

    def test_page_reports_isolate_another_pages_failed_cases(self):
        audit.record(self.run,self.judgment)
        other=copy.deepcopy(self.manifest['captures'][0]);other.update(key='other--initial--desktop',page_id='other',url=self.config['url']+'/other')
        self.manifest['captures'].append(other);self.manifest['pages'].append({'id':'other','url':other['url']})
        audit.save(self.run/'capture-manifest.json',self.manifest);audit.make_plan(self.run,self.manifest)
        bad=copy.deepcopy(self.judgment);bad.update(case_id='other--initial--desktop--2.4.2',outcome='failed',observed='別ページのタイトルが本文の目的を説明していない。')
        bad['targets'][0]['outcome']='failed';audit.record(self.run,bad)
        result=page_workflow.page_result(self.run,self.config['url'])
        self.assertNotIn('failed',result['counts']);self.assertEqual(len(result['cases']),55)
        files=audit.write_page_reports(self.run,self.config['url'])
        self.assertTrue(Path(files['html']).exists());self.assertNotIn('別ページのタイトル',Path(files['html']).read_text())
        book=load_workbook(files['excel'])
        try:
            summary={r[0]:r[1] for r in book['概要'].iter_rows(min_row=2,values_only=True)}
            self.assertEqual(summary['全検査票'],55)
            self.assertEqual(book['検査票'].max_row,56)
            self.assertNotIn(other['url'],''.join(str(c.value) for row in book['チェックシート'] for c in row))
        finally:book.close()

    def test_next_packet_includes_source_and_machine_results(self):
        self.graph();value=page_workflow.next_work(self.run,self.config['url'],limit=1)
        self.assertEqual(value['remaining_cases'],55);self.assertEqual(len(value['next_cases']),1)
        self.assertIn('normative_sha256',value['next_cases'][0]['definition'])
        self.assertEqual(value['next_cases'][0]['machine_results'][0]['outcome'],'failed')

    def test_page_interaction_status_does_not_inherit_other_pages_gaps(self):
        original=audit.outcomes(self.run)
        original.update(collection_complete=False,collector_status='interrupted',missing_captures=[])
        original['interaction_review'].update(required=True,complete=False,status='partial',remaining=['other'],
            pages={'abc':{'complete':True,'remaining':[]},'other':{'complete':False,'remaining':['other']}})
        page=page_workflow.page_result(self.run,self.config['url'],original);review=page['interaction_review']
        self.assertTrue(page['collection_complete']);self.assertEqual(page['collector_status'],'completed')
        self.assertTrue(review['complete']);self.assertEqual(review['status'],'reviewed');self.assertEqual(review['remaining'],[])
        original['interaction_review']['required']=False
        original['interaction_review']['pages']['abc'].update(complete=False,remaining=['未確認'])
        review=page_workflow.page_result(self.run,self.config['url'],original)['interaction_review']
        self.assertFalse(review['complete']);self.assertEqual(review['status'],'partial')

    def test_partial_failed_case_never_makes_page_complete(self):
        self.config['environments']=self.config['environments'][:1]
        meta=audit.load(self.run/'run.json');meta.update(config=self.config,config_digest=audit.digest(self.config));audit.save(self.run/'run.json',meta)
        (self.run/'plan.json').unlink();plan=audit.make_plan(self.run,self.manifest)
        for case in plan['cases']:
            value=copy.deepcopy(self.judgment);value.update(case_id=case['case_id'],config_digest=meta['config_digest'],
                normative_sha256=audit.CRITERIA[case['criterion']]['normative_sha256'],outcome='inapplicable',targets=[])
            if case['criterion']=='2.4.2':
                value.update(outcome='failed',coverage_complete=False,remaining=['合成試験の別の対象を未確認とする'],targets=copy.deepcopy(self.judgment['targets']))
                value['targets'][0]['outcome']='failed'
            audit.record(self.run,value)
        scope={key:True for key in ['complete','processes_reviewed','full_pages_reviewed','accessibility_support_reviewed','non_interference_reviewed']}
        scope.update(config_digest=meta['config_digest'],sources=['synthetic test'],observed='保存形式の合成試験で、未網羅の不適合を完了にしない確認。',evidence=['evidence/abc/inventory.json'],remaining=[])
        audit.save(self.run/'scope-review.json',audit.validate_scope_review(self.run,scope))
        self.assertFalse(page_workflow.page_result(self.run,self.config['url'])['audit_complete'])

    def test_actions_include_keyboard_and_combobox_navigation(self):
        result,reason=page_explorer.actions({'selector':'#combo','tag':'button','type':'button','role':'combobox','label':'Delivery'})
        self.assertIsNone(reason)
        self.assertIn('ArrowDown',[a.get('key') for a in result]);self.assertIn('click',[a['type'] for a in result])

    def test_persistent_and_navigation_actions_are_deferred(self):
        for c in [{'tag':'button','type':'submit','label':'Proceed'},{'tag':'button','type':'button','label':'削除'},
                  {'tag':'a','label':'Next','href':'/next'},{'tag':'input','type':'password','label':'Password'}]:
            actions,reason=page_explorer.actions(dict(c,selector='#control'))
            self.assertEqual(actions,[]);self.assertTrue(reason)

    def test_formless_default_submit_is_explored_but_form_owners_are_deferred(self):
        control={'selector':'#details','tag':'button','type':'submit','label':'Show details','formAssociated':False}
        actions,reason=page_explorer.actions(control)
        self.assertIsNone(reason);self.assertTrue(actions)
        for associated in [True,None]:
            changed=dict(control,formAssociated=associated)
            self.assertTrue(page_explorer.actions(changed)[1])
        self.assertTrue(page_explorer.actions(dict(control,label='Save changes'))[1])

    def test_changed_form_association_changes_the_exploration_fingerprint(self):
        original={'state':[],'controls':[{'selector':'#details','tag':'button','type':'submit','formAssociated':False}]}
        changed=copy.deepcopy(original);changed['controls'][0]['formAssociated']=True
        self.assertNotEqual(page_explorer.fingerprint(original),page_explorer.fingerprint(changed))

    def test_formless_submit_inputs_receive_activation_keys_instead_of_fill(self):
        for kind in ['submit','image']:
            control={'selector':'#open','tag':'input','type':kind,'label':'Open details','formAssociated':False}
            actions,reason=page_explorer.actions(control)
            self.assertIsNone(reason)
            self.assertFalse(any(a['type']=='fill' for a in actions))
            self.assertEqual({a['key'] for a in actions if a['type']=='key'},{'Enter','Space'})
            self.assertTrue(page_explorer.actions(dict(control,formAssociated=True))[1])

    def test_budgets_reject_invalid_values(self):
        for values in [(True,10,2),(0,10,2),(10,10001,2),(10,10,31)]:
            with self.assertRaises(ValueError):page_explorer.validate_budget(*values)

    def test_fingerprint_detects_style_and_content_but_not_scroll_focus_only(self):
        original={'state':[{'text':'Hello','styles':['blue']}],'focus':'one'}
        other=copy.deepcopy(original);other['focus']='two'
        self.assertEqual(page_explorer.fingerprint(original),page_explorer.fingerprint(other))
        other['state'][0]['styles']=['red']
        self.assertNotEqual(page_explorer.fingerprint(original),page_explorer.fingerprint(other))

    def test_fingerprint_includes_newly_available_controls(self):
        original={'state':[{'selector':'#button','text':'Open'}],'controls':[]}
        enabled=dict(original,controls=[{'selector':'#button','tag':'button','type':'button','events':['click']}])
        self.assertNotEqual(page_explorer.fingerprint(original),page_explorer.fingerprint(enabled))

    def test_fingerprint_ignores_control_coordinates_and_event_registration_order(self):
        original={'state':[],'controls':[{'selector':'#button','tag':'button','events':['click','keydown'],
            'rect':{'x':0,'y':0}}]}
        changed=copy.deepcopy(original);changed['controls'][0].update(rect={'x':10,'y':90},events=['keydown','click','click'])
        self.assertEqual(page_explorer.fingerprint(original),page_explorer.fingerprint(changed))


if __name__=='__main__':unittest.main()
