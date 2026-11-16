import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'))
import audit


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.run=Path(self.temp.name)
        self.config=audit.init_config('http://127.0.0.1:4317')
        audit.save(self.run/'run.json',{'config':self.config,'config_digest':audit.digest(self.config),'catalog_digest':audit.digest(audit.CATALOG)})
        capture={'key':'abc--initial--desktop','page_id':'abc','url':self.config['url'],'state':'initial',
                 'environment':'desktop','execution':'completed','evidence_dir':'evidence/abc'}
        self.manifest={'captures':[capture],'pages':[{'id':'abc','url':self.config['url']}],
                       'unvisited':[],'declared_states_without_page':[]}
        audit.save(self.run/'capture-manifest.json',self.manifest)
        self.plan=audit.make_plan(self.run,self.manifest)
        p=self.run/'evidence/abc/inventory.json';p.parent.mkdir(parents=True);p.write_text('{"title":"問い合わせ"}')
        self.case=next(c for c in self.plan['cases'] if c['criterion']=='2.4.2')
        self.judgment={'case_id':self.case['case_id'],'config_digest':audit.digest(self.config),
                       'normative_sha256':audit.CRITERIA['2.4.2']['normative_sha256'],
                       'outcome':'passed','execution':'completed','observed':'問い合わせフォームの目的をタイトルが説明している。',
                       'conditions_reviewed':True,'exceptions_reviewed':True,'coverage_complete':True,
                       'remaining':[],'tests_applied':['2.4.2-purpose'], 'steps_executed':['タイトルを取得し本文の目的と比較した'],
                       'evidence':['evidence/abc/inventory.json'],
                       'method_coverage':[{'method':'dom','status':'executed','reason':'DOMからタイトル文字列を取得した。'},
                                          {'method':'semantic','status':'executed','reason':'本文の目的とタイトルの内容を比較した。'}],
                       'targets':[{'target':'document.title','observed':'問い合わせ','expected':'ページの目的を説明する',
                                   'outcome':'passed','evidence':['evidence/abc/inventory.json']}]}

    def tearDown(self):
        self.temp.cleanup()

    def test_all_target_criteria_are_pending(self):
        self.assertEqual(len(self.plan['cases']),55)
        r=audit.outcomes(self.run)
        self.assertEqual(r['counts'],{'not_run':55})
        self.assertFalse(r['audit_complete'])
        self.assertEqual(len(r['criteria']),86)

    def test_blocked_cannot_pass(self):
        j=copy.deepcopy(self.judgment);j['execution']='blocked'
        with self.assertRaises(ValueError):audit.record(self.run,j)

    def test_missing_proof_cannot_pass(self):
        j=copy.deepcopy(self.judgment);j['targets'][0]['evidence']=['absent.png']
        with self.assertRaises(ValueError):audit.record(self.run,j)

    def test_mixed_targets_cannot_pass(self):
        j=copy.deepcopy(self.judgment);j['targets'][0]['outcome']='cant_tell'
        with self.assertRaises(ValueError):audit.record(self.run,j)

    def test_unavailable_observation_cannot_pass(self):
        j=copy.deepcopy(self.judgment);j['method_coverage'][0]['status']='unavailable'
        with self.assertRaises(ValueError):audit.record(self.run,j)

    def test_remaining_work_cannot_pass(self):
        j=copy.deepcopy(self.judgment);j['remaining']=['エラー状態は未確認']
        with self.assertRaises(ValueError):audit.record(self.run,j)

    def test_changed_evidence_rejected(self):
        audit.record(self.run,self.judgment)
        (self.run/'evidence/abc/inventory.json').write_text('changed')
        with self.assertRaises(ValueError):audit.outcomes(self.run)

    def test_wrong_criterion_or_config_rejected(self):
        for key in ['normative_sha256','config_digest']:
            j=copy.deepcopy(self.judgment);j[key]='wrong'
            with self.assertRaises(ValueError):audit.record(self.run,j)

    def test_failure_does_not_hide_unverified(self):
        j=copy.deepcopy(self.judgment);j['outcome']='failed';j['targets'][0]['outcome']='failed'
        audit.record(self.run,j)
        r=audit.outcomes(self.run)
        self.assertEqual(r['counts'],{'not_run':54,'failed':1})
        self.assertFalse(r['audit_complete'])

    def test_no_capture_is_not_a_completed_audit(self):
        audit.save(self.run/'plan.json',{'config_digest':audit.digest(self.config),'cases':[]})
        r=audit.outcomes(self.run)
        self.assertFalse(r['audit_complete'])
        self.assertEqual(sum(c['status']=='unverified' for c in r['criteria']),55)

    def test_valid_record_keeps_history(self):
        audit.record(self.run,self.judgment);audit.record(self.run,self.judgment)
        self.assertEqual(len(list((self.run/'assessments').glob('*.json'))),2)

    def test_strings_are_not_completion_flags(self):
        j=copy.deepcopy(self.judgment);j['outcome']='failed';j['targets'][0]['outcome']='failed';j['coverage_complete']='false'
        with self.assertRaises(ValueError):audit.record(self.run,j)
        scope={key:'false' for key in ['complete','processes_reviewed','full_pages_reviewed','accessibility_support_reviewed','non_interference_reviewed']}
        scope.update(config_digest=audit.digest(self.config),sources=['fixture sitemap'],observed='全ページの資料を調査したという試験データ。',evidence=['evidence/abc/inventory.json'])
        with self.assertRaises(ValueError):audit.validate_scope_review(self.run,scope)
        audit.save(self.run/'scope-review.json',scope)
        with self.assertRaises(ValueError):audit.outcomes(self.run)

    def test_failure_does_not_make_unknown_target_complete(self):
        j=copy.deepcopy(self.judgment);j['outcome']='failed';j['targets'][0]['outcome']='failed'
        unknown=copy.deepcopy(j['targets'][0]);unknown['outcome']='cant_tell';j['targets'].append(unknown)
        with self.assertRaises(ValueError):audit.record(self.run,j)

    def test_remaining_scope_cannot_be_complete(self):
        scope={key:True for key in ['complete','processes_reviewed','full_pages_reviewed','accessibility_support_reviewed','non_interference_reviewed']}
        scope.update(config_digest=audit.digest(self.config),sources=['fixture sitemap'],observed='全ページの資料を調査したという試験データ。',evidence=['evidence/abc/inventory.json'],remaining=['ログイン後のページが未確認'])
        with self.assertRaises(ValueError):audit.validate_scope_review(self.run,scope)

    def test_old_snapshot_can_report_but_cannot_accept_new_judgments(self):
        audit.snapshot_catalog(self.run)
        audit.record(self.run,self.judgment)
        changed=copy.deepcopy(audit.CATALOG);changed['criteria'][0]['steps']=['変更後の検査手順']
        with patch.object(audit,'CATALOG',changed):
            result=audit.report(self.run)
            self.assertFalse(result['definitions_match_installed'])
            self.assertEqual(result['counts'],{'not_run':54,'passed':1})
            with self.assertRaises(ValueError):audit.record(self.run,self.judgment)

    def test_catalog_snapshot_corruption_is_rejected(self):
        audit.snapshot_catalog(self.run)
        catalog=audit.load(self.run/'catalog.snapshot.json');catalog['criteria'].pop()
        audit.save(self.run/'catalog.snapshot.json',catalog)
        with self.assertRaises(ValueError):audit.outcomes(self.run)

    def test_changed_saved_config_and_plan_are_rejected(self):
        meta=audit.load(self.run/'run.json');meta['config']['level']='AAA';audit.save(self.run/'run.json',meta)
        with self.assertRaises(ValueError):audit.outcomes(self.run)
        meta['config']=self.config;audit.save(self.run/'run.json',meta)
        plan=audit.load(self.run/'plan.json');plan['config_digest']='other';audit.save(self.run/'plan.json',plan)
        with self.assertRaises(ValueError):audit.outcomes(self.run)

    def test_another_case_assessment_cannot_be_reused(self):
        audit.record(self.run,self.judgment)
        plan=audit.load(self.run/'plan.json');source=next(c for c in plan['cases'] if c['case_id']==self.case['case_id'])
        target=next(c for c in plan['cases'] if c['criterion']=='1.1.1');target['assessment']=source['assessment'];audit.save(self.run/'plan.json',plan)
        with self.assertRaises(ValueError):audit.outcomes(self.run)

    def test_missing_capture_and_case_are_reported_as_unverified(self):
        audit.record(self.run,self.judgment)
        plan=audit.load(self.run/'plan.json');plan['cases']=[c for c in plan['cases'] if c['criterion']!='1.1.1'];audit.save(self.run/'plan.json',plan)
        result=audit.outcomes(self.run)
        self.assertEqual(len(result['missing_captures']),3)
        self.assertEqual(result['missing_cases'],['abc--initial--desktop--1.1.1'])
        self.assertFalse(result['audit_complete'])
        self.assertEqual(next(c for c in result['criteria'] if c['id']=='2.4.2')['status'],'unverified')

    def test_legacy_run_requires_matching_installed_definitions(self):
        self.assertEqual(audit.outcomes(self.run)['counts'],{'not_run':55})
        changed=copy.deepcopy(audit.CATALOG);changed['criteria'][0]['steps']=['変更後の検査手順']
        with patch.object(audit,'CATALOG',changed):
            with self.assertRaises(ValueError):audit.outcomes(self.run)

    def test_additional_methods_do_not_replace_missing_required_methods(self):
        j=copy.deepcopy(self.judgment)
        j['method_coverage'].append({'method':'document-metadata','status':'executed','reason':'対象文書の情報辞書も別の方法で実際に取得した。'})
        audit.record(self.run,j)
        j['method_coverage']=[m for m in j['method_coverage'] if m['method']!='semantic']
        with self.assertRaises(ValueError):audit.record(self.run,j)

    def test_scope_cannot_claim_completion_without_verified_evidence(self):
        scope={key:True for key in ['complete','processes_reviewed','full_pages_reviewed','accessibility_support_reviewed','non_interference_reviewed']}
        scope.update(config_digest=audit.digest(self.config),sources=['fixture sitemap'],observed='全ページの資料を調査したという試験データ。',evidence=['evidence/abc/inventory.json'],remaining=[])
        audit.save(self.run/'scope-review.json',scope)
        with self.assertRaises(ValueError):audit.outcomes(self.run)

    def test_stopped_collector_cannot_report_a_complete_audit(self):
        config=copy.deepcopy(self.config);config['environments']=config['environments'][:1]
        (self.run/'plan.json').unlink()  # Build a separate synthetic single-environment fixture.
        audit.save(self.run/'run.json',{'config':config,'config_digest':audit.digest(config),
                                       'catalog_digest':audit.digest(audit.CATALOG)})
        plan=audit.make_plan(self.run,self.manifest)
        for case in plan['cases']:
            judgment=copy.deepcopy(self.judgment)
            judgment.update(case_id=case['case_id'],config_digest=audit.digest(config),
                normative_sha256=audit.CRITERIA[case['criterion']]['normative_sha256'],
                outcome='inapplicable',targets=[])
            audit.record(self.run,judgment)
        scope={key:True for key in ['complete','processes_reviewed','full_pages_reviewed',
                                    'accessibility_support_reviewed','non_interference_reviewed']}
        scope.update(config_digest=audit.digest(config),sources=['synthetic fixture inventory'],
                     observed='単体試験用の全範囲確認。実サイトの監査ではない。',
                     evidence=['evidence/abc/inventory.json'],remaining=[])
        audit.save(self.run/'scope-review.json',audit.validate_scope_review(self.run,scope))
        manifest=copy.deepcopy(self.manifest);manifest['collector_status']='completed'
        audit.save(self.run/'capture-manifest.json',manifest)
        self.assertTrue(audit.outcomes(self.run)['audit_complete'])
        manifest['collector_status']='running';audit.save(self.run/'capture-manifest.json',manifest)
        result=audit.outcomes(self.run)
        self.assertFalse(result['audit_complete'])
        self.assertFalse(result['collection_complete'])

    def test_media_record_requires_full_intervals_and_verifies_their_evidence(self):
        case=next(case for case in self.plan['cases'] if case['criterion']=='1.2.2')
        judgment=copy.deepcopy(self.judgment)
        judgment.update(case_id=case['case_id'],normative_sha256=audit.CRITERIA['1.2.2']['normative_sha256'],
            observed='単体試験用の媒体の比較記録。実際の音声を確認した記録ではない。',
            method_coverage=[{'method':'media','status':'executed','reason':'単体試験のための実施を表す仮の記録。'},
                             {'method':'semantic','status':'executed','reason':'単体試験のための意味の比較を表す記録。'}])
        with self.assertRaises(ValueError):audit.record(self.run,judgment)
        review={'source':'synthetic fixture video','timeline':'prerecorded','duration':1,
            'comparison':'単体試験用の音声情報と字幕の比較を表す記録。','intervals':[{
                'start':0,'end':.5,'status':'reviewed','observed':'単体試験用の前半の観察を表す記録。',
                'expected':'この区間の情報が字幕で対応すること。','evidence':['evidence/abc/inventory.json']} ]}
        judgment['targets'][0]['media_review']=review
        with self.assertRaises(ValueError):audit.record(self.run,judgment)
        review['intervals'][0]['end']=1
        audit.record(self.run,judgment)
        review['intervals'][0]['evidence']=['absent.json']
        with self.assertRaises(ValueError):audit.record(self.run,judgment)


if __name__=='__main__':unittest.main()
