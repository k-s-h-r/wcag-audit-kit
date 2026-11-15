import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit
import test_ledger as ledger_fixture
from handoff import validate_handoff


class HandoffTest(unittest.TestCase):
    def setUp(self):
        ledger_fixture.LedgerTest.setUp(self)
        self.handoff={
            'reason_kind':'specialist_judgement',
            'reason':'単体試験用。業務の目的を特定する資料が不足し、タイトルの適切さを確定できない。',
            'reviewer':'対象業務を理解するアクセシビリティ検査担当',
            'required_environment':'実ページと業務の仕様書',
            'attempts':[{'method':'semantic','observed':'タイトルの文字列は取得したが、試験用に業務の目的を未確定とした。',
                         'evidence':['evidence/abc/inventory.json']}],
            'checks':[{'target':'document.title とページ全体の業務内容',
                       'steps':['対象ページの業務内容を確認する','タイトルがそのページの主題又は目的を説明するか比較する'],
                       'expected':'実際の主題又は目的を、タイトルから識別できること。',
                       'evidence':['evidence/abc/inventory.json']}],
            'resume':'比較した内容と証拠を受け取り、このcaseへ新しい判定を記録する。'}
        self.blocked=copy.deepcopy(self.judgment)
        self.blocked.update(outcome='cant_tell',execution='blocked',coverage_complete=False,
                            remaining=['業務の目的とタイトルの内容の比較'],human_handoff=self.handoff)
        self.blocked['targets'][0]['outcome']='cant_tell'

    def tearDown(self):
        ledger_fixture.LedgerTest.tearDown(self)

    def test_handoff_remains_pending_and_has_concrete_report(self):
        audit.record(self.run,self.blocked)
        result=audit.report(self.run)
        self.assertEqual(result['counts'],{'not_run':54,'cant_tell':1})
        self.assertEqual(result['human_review_cases'],[self.case['case_id']])
        self.assertEqual(result['unassigned_remaining_cases'],[])
        self.assertFalse(result['audit_complete'])
        text=(self.run/'human-review.md').read_text()
        self.assertIn('document.title とページ全体の業務内容',text)
        self.assertIn('タイトルがそのページの主題又は目的を説明するか比較する',text)
        self.assertIn('人による確認が必要',(self.run/'report.html').read_text())

    def test_handoff_cannot_coexist_with_a_pass(self):
        value=copy.deepcopy(self.judgment);value['human_handoff']=self.handoff
        with self.assertRaisesRegex(ValueError,'引き継ぎ'):
            audit.record(self.run,value)

    def test_missing_attempts_or_executable_checks_are_rejected(self):
        for key,replacement in [('attempts',[]),('checks',[]),('reason_kind','tool_failed')]:
            value=copy.deepcopy(self.handoff);value[key]=replacement
            with self.assertRaises(ValueError):validate_handoff(value)
        value=copy.deepcopy(self.handoff);value['checks'][0]['steps']=[]
        with self.assertRaises(ValueError):validate_handoff(value)

    def test_deep_handoff_evidence_is_verified(self):
        value=copy.deepcopy(self.blocked)
        value['human_handoff']['attempts'][0]['evidence']=['absent.png']
        with self.assertRaisesRegex(ValueError,'証拠'):
            audit.record(self.run,value)

    def test_resolution_keeps_history_and_removes_active_handoff(self):
        audit.record(self.run,self.blocked)
        old=next((self.run/'assessments').glob('*.json'));before=old.read_bytes()
        audit.record(self.run,self.judgment)
        result=audit.report(self.run)
        self.assertEqual(result['human_review_cases'],[])
        self.assertEqual(len(list((self.run/'assessments').glob('*.json'))),2)
        self.assertEqual(old.read_bytes(),before)
        self.assertIn('引き継ぎが記録されたcaseはありません',(self.run/'human-review.md').read_text())

    def test_confirmed_failure_and_human_work_both_remain_visible(self):
        value=copy.deepcopy(self.blocked)
        value.update(outcome='failed',execution='completed')
        failed=copy.deepcopy(value['targets'][0]);failed.update(target='another title',outcome='failed')
        value['targets'].append(failed)
        audit.record(self.run,value)
        result=audit.report(self.run)
        self.assertEqual(result['counts'],{'not_run':54,'failed':1})
        self.assertEqual(result['human_review_cases'],[self.case['case_id']])
        self.assertFalse(result['audit_complete'])
        self.assertIn('another title',(self.run/'issues.md').read_text())

    def test_editing_handoff_cannot_drop_verified_proof(self):
        audit.record(self.run,self.blocked)
        plan=audit.run_plan(self.run);case=next(c for c in plan['cases'] if c['case_id']==self.case['case_id'])
        value=audit.load(self.run/case['assessment'])
        value['human_handoff']['checks'][0]['evidence']=['evidence/unverified.txt']
        audit.save(self.run/case['assessment'],value)
        with self.assertRaisesRegex(ValueError,'引き継ぎの証拠'):
            audit.outcomes(self.run)


if __name__=='__main__':unittest.main()
