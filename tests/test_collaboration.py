import copy
import json
import multiprocessing
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

from openpyxl import load_workbook

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit
from ledger_lock import run_lock
import work_queue
import workbook
import test_ledger as fixture


def claim_worker(run, task, owner, barrier, result):
    barrier.wait(timeout=10)
    try:
        work_queue.claim(Path(run),task,owner);result.put('claimed')
    except ValueError:
        result.put('conflict')


def record_worker(run, judgment, barrier):
    barrier.wait(timeout=10)
    audit.record(Path(run),judgment)


def lock_worker(run, ready):
    with run_lock(Path(run)):
        ready.set()
        time.sleep(30)


class CollaborationTest(unittest.TestCase):
    def setUp(self):fixture.LedgerTest.setUp(self)
    def tearDown(self):fixture.LedgerTest.tearDown(self)

    def export(self, name='work', **kwargs):
        path=self.run/(name+'.xlsx')
        workbook.export(self.run,path,mode='work',**kwargs)
        return path

    def edit(self,path,edits):
        book=load_workbook(path)
        for sheet,label,row,value in edits:
            headers=[c.value for c in book[sheet][1]]
            book[sheet].cell(row,headers.index(label)+1,value)
        book.save(path);book.close()

    def fill_judgment(self,path, judgment, row=2):
        edits=[]
        for key,label in workbook.CASE_COLUMNS:
            if key in {'outcome','execution','observed'}|workbook.FLAGS:
                edits.append(('検査票',label,row,judgment[key]))
            if key in workbook.LISTS:
                edits.append(('検査票',label,row,'\n'.join(judgment.get(key,[]))))
        for i,target in enumerate(judgment['targets'],2):
            for key,label in workbook.TARGET_COLUMNS:
                if key in {'target','expected','observed','outcome','evidence'}:
                    edits.append(('対象',label,i,'\n'.join(target[key]) if key=='evidence' else target[key]))
        for i,method in enumerate(judgment['method_coverage'],2):
            for key,label in workbook.METHOD_COLUMNS:
                if key!='case_id':edits.append(('観察方法',label,i,method[key]))
        self.edit(path,edits)

    def test_partition_is_stable_nonoverlapping_and_survives_recovery(self):
        tasks=work_queue.create_tasks(self.run,size=10)
        ids=[i for t in tasks for i in t['case_ids']]
        self.assertEqual(len(ids),55);self.assertEqual(len(set(ids)),55)
        self.assertTrue(all(len(t['case_ids'])<=10 for t in tasks))
        work_queue.claim(self.run,tasks[0]['id'],'担当A')
        audit.make_plan(self.run,self.manifest)
        self.assertEqual(work_queue.assignment(audit.run_plan(self.run),ids[0])['owner'],'担当A')
        self.assertEqual(work_queue.create_tasks(self.run),[])
        self.assertFalse(work_queue.status(self.run)['audit_complete'])

    def test_claim_requires_explicit_reassignment(self):
        task=work_queue.create_tasks(self.run,size=10)[0]
        work_queue.claim(self.run,task['id'],'A')
        with self.assertRaisesRegex(ValueError,'取得済み'):work_queue.claim(self.run,task['id'],'B')
        work_queue.claim(self.run,task['id'],'B',True)
        self.assertEqual(work_queue.status(self.run,'B')['total_tasks'],1)

    def test_pending_task_owner_filters_and_resume_after_a_verdict(self):
        task=work_queue.create_tasks(self.run,criterion='2.4.2',owner='A')[0]
        with patch('sys.stdout') as output:
            self.assertEqual(audit.main(['pending','--run',str(self.run),'--task',task['id'],'--owner','A']),0)
        self.assertIn('"total": 1',''.join(x.args[0] for x in output.write.call_args_list))
        audit.record(self.run,self.judgment)
        status=work_queue.status(self.run)
        self.assertEqual(status['tasks'][0]['remaining'],0)
        self.assertEqual(status['tasks'][0]['work_states'],{'done':1})
        self.assertFalse(status['audit_complete'])

    def test_two_processes_cannot_both_claim_a_task(self):
        task=work_queue.create_tasks(self.run,size=1)[0]
        ctx=multiprocessing.get_context('spawn');barrier=ctx.Barrier(3);result=ctx.Queue()
        processes=[ctx.Process(target=claim_worker,args=(str(self.run),task['id'],owner,barrier,result)) for owner in ['A','B']]
        try:
            for p in processes:p.start()
            barrier.wait(timeout=10)
            for p in processes:p.join(10);self.assertEqual(p.exitcode,0)
            self.assertEqual(sorted(result.get(timeout=2) for _ in processes),['claimed','conflict'])
        finally:
            for p in processes:
                if p.is_alive():p.terminate();p.join(2)
            result.close()

    def test_parallel_records_do_not_lose_another_case(self):
        ctx=multiprocessing.get_context('spawn');barrier=ctx.Barrier(3)
        judgments=[]
        for case in [self.case,next(c for c in self.plan['cases'] if c['criterion']=='1.1.1')]:
            value=copy.deepcopy(self.judgment)
            value.update(case_id=case['case_id'],normative_sha256=audit.CRITERIA[case['criterion']]['normative_sha256'],
                         outcome='cant_tell',execution='blocked',coverage_complete=False,remaining=['並行記録の合成試験で未検証'],targets=[])
            judgments.append(value)
        processes=[ctx.Process(target=record_worker,args=(str(self.run),j,barrier)) for j in judgments]
        try:
            for p in processes:p.start()
            barrier.wait(timeout=10)
            for p in processes:p.join(10);self.assertEqual(p.exitcode,0)
            self.assertEqual(audit.outcomes(self.run)['counts'],{'not_run':53,'cant_tell':2})
        finally:
            for p in processes:
                if p.is_alive():p.terminate();p.join(2)

    def test_stopped_worker_releases_lock_without_losing_progress(self):
        audit.record(self.run,self.judgment)
        before=(self.run/'plan.json').read_bytes()
        ctx=multiprocessing.get_context('spawn');ready=ctx.Event();p=ctx.Process(target=lock_worker,args=(str(self.run),ready))
        try:
            p.start();self.assertTrue(ready.wait(10));p.terminate();p.join(5)
            self.assertEqual((self.run/'plan.json').read_bytes(),before)
            audit.record(self.run,self.judgment)
            self.assertEqual(len(list((self.run/'assessments').glob('*.json'))),2)
        finally:
            if p.is_alive():p.terminate();p.join(2)

    def test_report_has_all_criteria_and_cannot_be_imported(self):
        path=self.run/'report.xlsx';workbook.export(self.run,path)
        book=load_workbook(path);self.assertEqual(book['達成基準'].max_row,87);book.close()
        with self.assertRaisesRegex(ValueError,'work'):workbook.import_book(self.run,path)

    def test_unchanged_round_trip_creates_no_assessment(self):
        path=self.export()
        before=(self.run/'plan.json').read_bytes()
        self.assertEqual(workbook.import_book(self.run,path)['changed_cases'],0)
        self.assertEqual((self.run/'plan.json').read_bytes(),before)
        self.assertFalse((self.run/'assessments').exists())

    def test_edit_assignment_and_note_does_not_create_a_verdict(self):
        path=self.export(criterion='2.4.2')
        self.edit(path,[('検査票','担当',2,'担当A'),('検査票','作業状態',2,'in_progress'),('検査票','作業メモ',2,'次回は目的を照合する')])
        self.assertEqual(workbook.import_book(self.run,path)['new_assessments'],0)
        self.assertEqual(audit.outcomes(self.run)['counts'],{'not_run':55})
        self.assertEqual(work_queue.assignment(audit.run_plan(self.run),self.case['case_id'])['owner'],'担当A')

    def test_done_alone_cannot_mean_passed_or_finished(self):
        path=self.export(criterion='2.4.2');self.edit(path,[('検査票','作業状態',2,'done')])
        with self.assertRaisesRegex(ValueError,'done'):workbook.import_book(self.run,path)
        self.assertEqual(audit.outcomes(self.run)['counts'],{'not_run':55})

    def test_evidence_backed_judgment_import_and_check_only(self):
        path=self.export(criterion='2.4.2');self.fill_judgment(path,self.judgment)
        self.assertEqual(workbook.import_book(self.run,path,check=True)['new_assessments'],1)
        self.assertEqual(audit.outcomes(self.run)['counts'],{'not_run':55})
        self.assertEqual(workbook.import_book(self.run,path)['new_assessments'],1)
        self.assertEqual(audit.outcomes(self.run)['counts'],{'not_run':54,'passed':1})
        self.assertEqual(work_queue.assignment(audit.run_plan(self.run),self.case['case_id'])['state'],'done')

    def test_missing_evidence_does_not_import_even_a_metadata_change(self):
        path=self.export(criterion='2.4.2');value=copy.deepcopy(self.judgment);value['evidence']=['missing.png']
        self.fill_judgment(path,value);self.edit(path,[('検査票','担当',2,'A')])
        before=(self.run/'plan.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'証拠'):workbook.import_book(self.run,path)
        self.assertEqual((self.run/'plan.json').read_bytes(),before)
        self.assertFalse((self.run/'assessments').exists())

    def test_invalid_second_judgment_does_not_publish_the_first(self):
        capture=copy.deepcopy(self.manifest['captures'][0])
        capture.update(key='abc--initial--narrow',environment='narrow',evidence_dir='evidence/narrow')
        self.manifest['captures'].append(capture)
        audit.save(self.run/'capture-manifest.json',self.manifest);audit.make_plan(self.run,self.manifest)
        path=self.export(criterion='2.4.2');self.fill_judgment(path,self.judgment)
        self.edit(path,[('検査票','判定',3,'passed'),('検査票','実施状況',3,'completed')])
        before=(self.run/'plan.json').read_bytes()
        with self.assertRaises(ValueError):workbook.import_book(self.run,path)
        self.assertEqual((self.run/'plan.json').read_bytes(),before)
        self.assertFalse((self.run/'assessments').exists())

    def test_other_run_cannot_accept_the_workbook(self):
        path=self.export(criterion='2.4.2');other=fixture.LedgerTest()
        try:
            other.setUp()
            with self.assertRaisesRegex(ValueError,'配布記録'):workbook.import_book(other.run,path)
        finally:other.tearDown()

    def test_human_handoff_remains_unverified_after_excel_edit(self):
        value=copy.deepcopy(self.judgment)
        value.update(outcome='cant_tell',execution='blocked',coverage_complete=False,remaining=['業務の目的を担当者へ確認する'])
        value['targets'][0]['outcome']='cant_tell'
        value['human_handoff']={
            'reason_kind':'specialist_judgement','reason':'合成試験。業務資料が不足して目的を確定できない。',
            'reviewer':'業務内容を把握している検証担当者','required_environment':'対象ページと業務内容の説明資料',
            'attempts':[{'method':'semantic','observed':'文字列は取得したが、業務上の目的を未確認とした。','evidence':['evidence/abc/inventory.json']}],
            'checks':[{'target':'document.title','steps':['業務の目的とページのタイトルを実際に比較する'],
                       'expected':'タイトルがページの主題又は目的を説明すること。','evidence':['evidence/abc/inventory.json']}],
            'resume':'比較した結果と証拠を受け取り、このcaseに新しい判定を記録する。'}
        audit.record(self.run,value);path=self.export(criterion='2.4.2')
        self.edit(path,[('検査票','観察',2,'比較を試みたが業務資料の不足は解消していない。')])
        self.assertEqual(workbook.import_book(self.run,path)['new_assessments'],1)
        result=audit.outcomes(self.run)
        self.assertEqual(result['human_review_cases'],[self.case['case_id']]);self.assertFalse(result['audit_complete'])

    def test_conflict_rejects_the_entire_import(self):
        path=self.export();self.edit(path,[('検査票','担当',2,'A'),('検査票','担当',3,'A')])
        plan=audit.run_plan(self.run);ident=plan['cases'][1]['case_id']
        plan['work']['cases'][ident]={'owner':'B','state':'in_progress','note':'先に担当を変更'}
        audit.save(self.run/'plan.json',plan);before=(self.run/'plan.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'更新競合'):workbook.import_book(self.run,path)
        self.assertEqual((self.run/'plan.json').read_bytes(),before)

    def test_disjoint_changes_merge_despite_unchanged_stale_rows(self):
        a=self.export('A');b=self.export('B')
        self.edit(a,[('検査票','担当',2,'A')]);self.edit(b,[('検査票','担当',3,'B')])
        workbook.import_book(self.run,a);workbook.import_book(self.run,b)
        plan=audit.run_plan(self.run)
        self.assertEqual(work_queue.assignment(plan,plan['cases'][0]['case_id'])['owner'],'A')
        self.assertEqual(work_queue.assignment(plan,plan['cases'][1]['case_id'])['owner'],'B')

    def test_repeated_import_is_idempotent_and_new_rows_can_follow(self):
        path=self.export();self.edit(path,[('検査票','担当',2,'A')])
        self.assertEqual(workbook.import_book(self.run,path)['changed_cases'],1)
        self.assertEqual(workbook.import_book(self.run,path)['changed_cases'],0)
        self.edit(path,[('検査票','担当',3,'B')])
        self.assertEqual(workbook.import_book(self.run,path)['changed_cases'],1)
        self.edit(path,[('検査票','作業メモ',2,'同じ票を古い版からさらに変更')])
        with self.assertRaisesRegex(ValueError,'更新競合'):workbook.import_book(self.run,path)

    def test_stopped_import_before_plan_publish_can_be_retried(self):
        path=self.export(criterion='2.4.2');self.fill_judgment(path,self.judgment)
        before=(self.run/'plan.json').read_bytes();save=audit.save
        def interrupted(path,value):
            if Path(path).name=='plan.json':raise OSError('simulated stop before plan publish')
            return save(path,value)
        with patch.object(audit,'save',side_effect=interrupted):
            with self.assertRaises(OSError):workbook.import_book(self.run,path)
        self.assertEqual((self.run/'plan.json').read_bytes(),before)
        self.assertEqual(audit.outcomes(self.run)['counts'],{'not_run':55})
        self.assertEqual(workbook.import_book(self.run,path)['new_assessments'],1)
        self.assertEqual(audit.outcomes(self.run)['counts'],{'not_run':54,'passed':1})
        self.assertEqual(len(list((self.run/'assessments').glob('*.json'))),2)

    def test_changed_verdict_rejects_a_stale_excel_edit(self):
        path=self.export(criterion='2.4.2');self.edit(path,[('検査票','作業メモ',2,'古い表示を基にしたメモ')])
        audit.record(self.run,self.judgment)
        with self.assertRaisesRegex(ValueError,'更新競合'):workbook.import_book(self.run,path)

    def test_formulas_are_literal_on_export_and_rejected_on_import(self):
        value=copy.deepcopy(self.judgment);value['observed']='=HYPERLINK("https://example.test/", "untrusted")'
        audit.record(self.run,value);path=self.export(criterion='2.4.2')
        book=load_workbook(path);column=[c.value for c in book['検査票'][1]].index('観察')+1
        self.assertEqual(book['検査票'].cell(2,column).data_type,'s');book.close()
        self.edit(path,[('検査票','作業メモ',2,'=1+1')])
        with self.assertRaisesRegex(ValueError,'数式'):workbook.import_book(self.run,path)

    def test_context_changes_duplicate_ids_and_missing_rows_are_rejected(self):
        for name,edit in [('context',('検査票','ページURL',2,'https://other.test/')),
                          ('duplicate',('検査票','検査票ID',3,self.plan['cases'][0]['case_id']))]:
            path=self.export(name);self.edit(path,[edit])
            with self.assertRaises(ValueError):workbook.import_book(self.run,path)
        path=self.export('deleted');book=load_workbook(path);book['検査票'].delete_rows(2);book.save(path);book.close()
        with self.assertRaisesRegex(ValueError,'削除'):workbook.import_book(self.run,path)

    def test_record_optional_base_revision_prevents_stale_overwrite(self):
        value=dict(self.judgment,base_assessment=None);audit.record(self.run,value)
        with self.assertRaisesRegex(ValueError,'更新済み'):audit.record(self.run,value)
        self.assertEqual(len(list((self.run/'assessments').glob('*.json'))),1)

    def test_long_excel_text_is_not_silently_truncated(self):
        value=copy.deepcopy(self.judgment);value['observed']='長'*32768;audit.record(self.run,value)
        with self.assertRaisesRegex(ValueError,'文字数'):self.export(criterion='2.4.2')


if __name__=='__main__':unittest.main()
