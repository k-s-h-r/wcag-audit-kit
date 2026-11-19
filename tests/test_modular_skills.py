import asyncio
import base64
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'))
import audit
import inspection
import page_catalog
import test_ledger as fixture
import work_queue


class SelectionTest(unittest.TestCase):
    def test_exact_page_filter_does_not_include_prefixes_or_other_queries(self):
        cases=[{'page_url':'https://example.test/contact?a=1'},
               {'page_url':'https://example.test/contact?a=2'}, {'page_url':'https://example.test/contact-extra'}]
        self.assertEqual(work_queue.select(cases,{'cases':[]},page_exact=cases[0]['page_url']),[cases[0]])
        self.assertEqual(len(work_queue.select(cases,{'cases':[]},page='/contact')),3)

    def test_configured_list_keeps_query_and_fragment_and_does_not_browse(self):
        config=audit.init_config('http://127.0.0.1:9')
        config['scope'].update(mode='configured',pages=['/page?a=1#state','/page?a=2#state'])
        audit.validate_config(config)
        with patch('playwright.async_api.async_playwright',side_effect=AssertionError('configured must not browse')):
            result=asyncio.run(page_catalog.select_pages(config))
        self.assertEqual(len(result['pages']),2);self.assertFalse(result['inventory_complete'])
        self.assertTrue(all(not p['visited'] for p in result['pages']))

    def test_foreign_or_excluded_urls_and_empty_configured_are_rejected(self):
        for pages in [[],['https://outside.example/'],['http://user:secret@127.0.0.1:9/']]:
            config=audit.init_config('http://127.0.0.1:9');config['scope'].update(mode='configured',pages=pages)
            with self.assertRaises(ValueError):audit.validate_config(config)

    def test_relative_file_and_generated_pages_manifest_are_resolved(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'pages.json';source.write_text(json.dumps({'pages':[{'url':'http://127.0.0.1:9/a'},{'url':'http://127.0.0.1:9/b'}]}))
            config=audit.init_config('http://127.0.0.1:9');config['scope'].update(mode='configured',pages_file='pages.json')
            path=root/'config.json';audit.save(path,config);resolved=page_catalog.read_config(path)
            self.assertEqual(page_catalog.configured_urls(resolved),['http://127.0.0.1:9/a','http://127.0.0.1:9/b'])
            self.assertNotIn('pages_file',resolved['scope']);self.assertEqual(len(resolved['scope']['pages_source']['sha256']),64)

    def test_page_cli_uses_only_the_given_url_and_has_unverified_results(self):
        with tempfile.TemporaryDirectory() as directory:
            run=Path(directory)/'run';seen=[]
            async def collect(config,target):
                seen.append(config)
                p=target/'evidence/abc';p.mkdir(parents=True);(p/'inventory.json').write_text('{}')
                manifest={'pages':[{'id':'abc','url':config['scope']['pages'][0]}],
                    'captures':[{'key':'abc--initial--desktop','page_id':'abc','url':config['scope']['pages'][0],
                    'state':'initial','environment':'desktop','execution':'completed','evidence_dir':'evidence/abc'}],
                    'unvisited':[],'declared_states_without_page':[]}
                audit.save(target/'capture-manifest.json',manifest);return manifest
            with patch('browser_capture.collect',collect),patch('sys.stdout'):
                self.assertEqual(audit.main(['page','--url','http://127.0.0.1:9/contact?a=1#open','--out',str(run),'--profile','quick']),0)
            self.assertEqual(seen[0]['scope']['mode'],'configured');self.assertEqual(seen[0]['scope']['max_pages'],1)
            self.assertEqual(seen[0]['scope']['pages'],['http://127.0.0.1:9/contact?a=1#open'])
            result=audit.outcomes(audit.run_layout.ledger(run))
            self.assertEqual(result['counts'],{'not_run':55});self.assertFalse(result['audit_complete'])
            self.assertFalse(result['interaction_review']['complete']);self.assertEqual(result['inspection_policy']['screenshots'],'off')


class BudgetTest(unittest.TestCase):
    def test_modes_and_per_page_limit_skip_the_actual_capture(self):
        async def scenario(root,choice):
            calls=[];manifest={}
            async def capture(page,path,**kwargs):calls.append(path.name);path.write_bytes(b'unit fixture')
            budget=inspection.ImageBudget({'inspection':choice},root,manifest,capture);budget.page='one'
            await budget.capture(None,root/'before.png')
            await budget.capture(None,root/'state.png',kind='state')
            await budget.capture(None,root/'another.png',kind='state')
            budget.page='two';await budget.capture(None,root/'page-two.png',kind='state')
            return calls,manifest
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            calls,manifest=asyncio.run(scenario(root,{'profile':'standard','max_images':1}))
            self.assertEqual(calls,['state.png','page-two.png'])
            self.assertEqual([x.get('reason') for x in manifest['inspection']['screenshots']],['states_only',None,'image_limit',None])
            calls,_=asyncio.run(scenario(root,{'profile':'quick'}));self.assertEqual(calls,[])

    def test_policy_rejects_typos_and_boolean_budgets(self):
        for value in [{'profile':'unknown'},{'screen_reader':'yes'},{'screenshots':'maybe'},{'max_images':True},{'token_budget':1000}]:
            with self.assertRaises(ValueError):inspection.policy(value)


class InteractionReviewTest(unittest.TestCase):
    def setUp(self):
        fixture.LedgerTest.setUp(self)
        self.config['inspection']=inspection.policy({'profile':'standard'})
        self.config['environments']=self.config['environments'][:1]
        meta=audit.load(self.run/'run.json');meta.update(config=self.config,config_digest=audit.digest(self.config));audit.save(self.run/'run.json',meta)
        (self.run/'plan.json').unlink();self.plan=audit.make_plan(self.run,self.manifest)
        self.judgment['config_digest']=meta['config_digest']
        image=self.run/'evidence/abc/page.png'
        image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jEucAAAAASUVORK5CYII='))
        self.review={'config_digest':meta['config_digest'],'page_id':'abc','base_review':None,
            'captures':[{'key':'abc--initial--desktop','visual':{'status':'reviewed','observed':'合成試験の画像を照合したとする調査票の構造試験。','evidence':['evidence/abc/page.png']},
              'controls':[{'id':'title','label':'合成試験の対象','location':'合成画像の位置に対応する構造試験',
               'status':'tested','observed':'実サイトの検証ではなく保存形式の合成試験。','steps':['合成試験の観察を記録する'],'evidence':['evidence/abc/page.png']}],
              'states_complete':True,'remaining':[]}],
            'screen_reader':{'status':'skipped','observed':'この合成試験では実スクリーンリーダーを使用していない。','evidence':[]}}

    def tearDown(self):fixture.LedgerTest.tearDown(self)

    def test_new_inspection_stays_incomplete_until_visual_survey_is_recorded(self):
        for case in self.plan['cases']:
            value=copy.deepcopy(self.judgment);value.update(case_id=case['case_id'],normative_sha256=audit.CRITERIA[case['criterion']]['normative_sha256'])
            if case['criterion']!='2.4.2':value.update(outcome='inapplicable',targets=[])
            audit.record(self.run,value)
        scope={key:True for key in ['complete','processes_reviewed','full_pages_reviewed','accessibility_support_reviewed','non_interference_reviewed']}
        scope.update(config_digest=audit.digest(self.config),sources=['synthetic unit test'],observed='合成試験の全体確認を完了とした、判定条件の単体試験。',evidence=['evidence/abc/inventory.json'],remaining=[])
        audit.save(self.run/'scope-review.json',audit.validate_scope_review(self.run,scope))
        self.assertFalse(audit.outcomes(self.run)['audit_complete'])
        audit.record_interactions(self.run,self.review)
        self.assertTrue(audit.outcomes(self.run)['audit_complete'])

    def test_missing_images_or_untested_controls_cannot_mean_complete(self):
        for change in ['image','control','remaining']:
            value=copy.deepcopy(self.review)
            if change=='image':value['captures'][0]['visual']['evidence']=[]
            elif change=='control':value['captures'][0]['controls'][0].update(status='unverified',remaining=['キーでの開始を未検証'])
            else:value['captures'][0]['controls'][0]['remaining']=['試していない分岐が残っている']
            with self.assertRaises(ValueError):audit.record_interactions(self.run,value)

    def test_skipped_images_remain_visible_and_incomplete(self):
        value=copy.deepcopy(self.review)
        value['captures'][0].update(visual={'status':'skipped','observed':'画像なしの設定のため画面の内容を確認していない。','evidence':[]},controls=[],states_complete=False,remaining=['画面と開いた後の状態を調べる'])
        self.assertFalse(audit.record_interactions(self.run,value)['complete'])
        self.assertEqual(inspection.review_status(self.run)['status'],'partial')

    def test_required_reader_and_accessibility_tree_are_not_real_sr_review(self):
        self.config['inspection']['screen_reader']='required'
        meta=audit.load(self.run/'run.json');meta.update(config=self.config,config_digest=audit.digest(self.config));audit.save(self.run/'run.json',meta)
        plan=audit.load(self.run/'plan.json');plan['config_digest']=meta['config_digest'];audit.save(self.run/'plan.json',plan)
        self.review['config_digest']=meta['config_digest']
        self.assertIn('screen_reader',inspection.validate_review(self.run,self.review)['remaining'])
        value=copy.deepcopy(self.review);value['screen_reader'].update(status='reviewed',source='accessibility-tree',evidence=['evidence/abc/inventory.json'])
        with self.assertRaisesRegex(ValueError,'実際の読み上げ'):inspection.validate_review(self.run,value)

    def test_old_review_rejected_and_immutable_history_kept(self):
        audit.record_interactions(self.run,self.review)
        first=audit.run_plan(self.run)['interaction_reviews']['abc'];before=(self.run/first).read_bytes()
        with self.assertRaisesRegex(ValueError,'最新'):audit.record_interactions(self.run,self.review)
        value=copy.deepcopy(self.review);value['base_review']=first
        audit.record_interactions(self.run,value)
        self.assertEqual((self.run/first).read_bytes(),before);self.assertEqual(len(list((self.run/'interaction-reviews').glob('*.json'))),2)

    def test_changed_image_stops_reporting(self):
        audit.record_interactions(self.run,self.review);(self.run/'evidence/abc/page.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'変更'):audit.outcomes(self.run)

    def test_page_reviews_keep_each_others_pointers(self):
        audit.record_interactions(self.run,self.review)
        first=audit.run_plan(self.run)['interaction_reviews']['abc']
        capture=copy.deepcopy(self.manifest['captures'][0]);capture.update(key='def--initial--desktop',page_id='def',url=self.config['url']+'/second',evidence_dir='evidence/def')
        self.manifest['captures'].append(capture);self.manifest['pages'].append({'id':'def','url':capture['url']})
        audit.save(self.run/'capture-manifest.json',self.manifest);audit.make_plan(self.run,self.manifest)
        image=self.run/'evidence/def/page.png';image.parent.mkdir();image.write_bytes((self.run/'evidence/abc/page.png').read_bytes())
        value=copy.deepcopy(self.review);value['page_id']='def';value['captures'][0]['key']=capture['key']
        value['captures'][0]['visual']['evidence']=['evidence/def/page.png']
        value['captures'][0]['controls'][0]['evidence']=['evidence/def/page.png']
        audit.record_interactions(self.run,value)
        self.assertEqual(audit.run_plan(self.run)['interaction_reviews']['abc'],first)
        self.assertEqual(len(inspection.review_status(self.run)['pages']),2)


if __name__=='__main__':unittest.main()
