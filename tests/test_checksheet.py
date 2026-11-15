import copy
from pathlib import Path
import sys
import unittest

from openpyxl import load_workbook

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit
import checksheet
import workbook
import test_ledger as fixture


class ChecksheetTest(unittest.TestCase):
    def setUp(self):fixture.LedgerTest.setUp(self)
    def tearDown(self):fixture.LedgerTest.tearDown(self)

    def model(self, result=None, **kwargs):
        return checksheet.build(result or audit.outcomes(self.run),audit.CATALOG,manifest=self.manifest,**kwargs)

    def criterion(self, model, ident):
        return next(r for r in model['rows'] if r['criterion']==ident and r['kind']=='criterion')

    def record_images(self, partial=False):
        case=next(c for c in self.plan['cases'] if c['criterion']=='1.1.1')
        judgment=copy.deepcopy(self.judgment)
        judgment.update(case_id=case['case_id'],normative_sha256=audit.CRITERIA['1.1.1']['normative_sha256'],
            outcome='failed',observed='合成試験。図の説明はあるが、購入ボタンの名前が空だった。',
            coverage_complete=not partial,remaining=['ダイアログの画像を調べる'] if partial else [],
            targets=[dict(target='main img.chart',expected='情報画像に同等の説明がある',
                          observed='図の値を説明する文章へ到達できた',outcome='passed',evidence=['evidence/abc/inventory.json']),
                     dict(target='button.buy > svg',expected='操作部品に目的を表す名前がある',
                          observed='購入ボタンの名前が空だった',outcome='failed',evidence=['evidence/abc/inventory.json'])])
        audit.record(self.run,judgment)

    def test_all_criteria_have_a_row_and_unexecuted_is_not_inapplicable(self):
        model=self.model();rows=[r for r in model['rows'] if r['kind']=='criterion']
        self.assertEqual(len(rows),86)
        self.assertEqual([r['criterion'] for r in rows],[c['id'] for c in audit.CATALOG['criteria']])
        self.assertEqual(self.criterion(model,'1.1.1')['judgment'],'未確認')
        self.assertEqual(self.criterion(model,'1.1.1')['applicability'],'未確認')
        self.assertEqual(self.criterion(model,'1.2.6')['judgment'],'目標レベル外')
        self.assertNotIn('他の記録',checksheet.html_table(checksheet.COLUMNS,[rows[0]]))

    def test_multiple_viewpoints_have_independent_rows_and_failure_locations(self):
        self.record_images();model=self.model()
        points=[r for r in model['rows'] if r['criterion']=='1.1.1' and r['kind']=='checkpoint']
        self.assertEqual([r['judgment'] for r in points],['○ 適合','× 不適合'])
        self.assertEqual(self.criterion(model,'1.1.1')['judgment'],'× 不適合\n未確認あり')
        self.assertEqual(len(model['failures']),1)
        failure=model['failures'][0]
        self.assertEqual(failure['target'],'button.buy > svg')
        self.assertEqual(failure['page_url'],self.config['url'])
        self.assertEqual(failure['state'],'initial');self.assertEqual(failure['environment'],'desktop')
        self.assertIn('evidence/abc/inventory.json',failure['evidence'])
        self.assertIn('F00001',points[1]['locations']);self.assertNotIn('main img.chart',points[1]['locations'])

    def test_partial_failure_keeps_both_failure_and_remaining_checks(self):
        self.record_images(partial=True);row=self.criterion(self.model(),'1.1.1')
        self.assertEqual(row['judgment'],'× 不適合\n未確認あり')
        self.assertIn('未確認あり',row['notes']);self.assertIn('ダイアログの画像',row['remaining'])

    def test_known_pass_does_not_cover_missing_captures_cases_or_unvisited(self):
        audit.record(self.run,self.judgment);result=audit.outcomes(self.run)
        self.assertEqual(self.criterion(self.model(result),'2.4.2')['judgment'],'未確認')
        result['missing_captures']=[]
        self.assertEqual(self.criterion(self.model(result),'2.4.2')['judgment'],'○ 適合')
        for field,value in [('missing_cases',[self.case['case_id']]),('unvisited',[{'url':self.config['url']+'/other'}]),
                            ('collection_complete',False)]:
            changed=copy.deepcopy(result);changed[field]=value
            self.assertEqual(self.criterion(self.model(changed),'2.4.2')['judgment'],'未確認')

    def test_inapplicable_requires_recorded_reason_and_remains_distinct(self):
        judgment=copy.deepcopy(self.judgment)
        judgment.update(outcome='inapplicable',targets=[],observed='合成試験。適用対象が存在しない条件を調べた。')
        audit.record(self.run,judgment);result=audit.outcomes(self.run);result['missing_captures']=[]
        row=self.criterion(self.model(result),'2.4.2')
        self.assertEqual((row['applicability'],row['judgment']),('なし','— 非適用'))
        self.assertIn('適用対象が存在しない',row['notes'])

    def test_failed_and_unverified_cases_are_not_hidden_by_passed_cases(self):
        self.record_images();result=audit.outcomes(self.run)
        passed=copy.deepcopy(next(c for c in result['cases'] if c['criterion']=='1.1.1'))
        passed.update(case_id='other--1.1.1',page_url=self.config['url']+'/other',outcome='not_run',assessment_data=None)
        result['cases'].append(passed)
        row=self.criterion(self.model(result),'1.1.1')
        self.assertEqual(row['judgment'],'× 不適合\n未確認あり');self.assertIn('/other',row['remaining'])

    def test_filter_scopes_do_not_include_other_pages_failures(self):
        self.record_images();result=audit.outcomes(self.run)
        passed=copy.deepcopy(next(c for c in result['cases'] if c['criterion']=='1.1.1'))
        passed.update(case_id='other--1.1.1',page_url=self.config['url']+'/other',capture='other',outcome='passed')
        passed['assessment_data'].update(outcome='passed',targets=[passed['assessment_data']['targets'][0]])
        result['cases'].append(passed)
        model=self.model(result,cases=[passed],filters={'page_exact':passed['page_url']})
        self.assertEqual(model['failures'],[])
        self.assertEqual(self.criterion(model,'1.1.1')['judgment'],'○ 適合')
        self.assertEqual(len([r for r in model['rows'] if r['kind']=='criterion']),86)
        task_model=self.model(result,cases=[passed],filters={'task':'task-example'})
        self.assertEqual({r['criterion'] for r in task_model['rows']},{'1.1.1'})
        self.assertIn('選択した検査票のみ',task_model['scope'])

    def test_many_locations_are_all_retained_in_the_failure_list(self):
        self.record_images();result=audit.outcomes(self.run)
        case=next(c for c in result['cases'] if c['criterion']=='1.1.1')
        target=case['assessment_data']['targets'][1]
        case['assessment_data']['targets']=[dict(target,target=f'button.item-{i}') for i in range(12)]
        model=self.model(result);row=self.criterion(model,'1.1.1')
        self.assertEqual(len(model['failures']),12)
        self.assertIn('ほか9件',row['locations']);self.assertEqual(len(row['failure_ids']),12)
        self.assertEqual(model['failures'][-1]['target'],'button.item-11')

    def test_html_escapes_page_content_and_links_to_every_failure(self):
        self.record_images();result=audit.outcomes(self.run)
        case=next(c for c in result['cases'] if c['criterion']=='1.1.1')
        case['assessment_data']['targets'][1]['observed']='<script>alert(1)</script>'
        body=checksheet.render_html(self.model(result))
        self.assertNotIn('<script>',body);self.assertIn('&lt;script&gt;',body)
        self.assertIn('href="#failure-F00001"',body);self.assertIn('id="failure-F00001"',body)
        cell=checksheet.html_table([('evidence','証拠')],[dict(kind='checkpoint',status='failed',
            evidence='javascript:example#fragment',evidence_paths=['javascript:example#fragment'])])
        self.assertIn('href="./javascript%3Aexample%23fragment"',cell)
        audit.report(self.run);report=(self.run/'report.html').read_text()
        self.assertIn('達成基準チェックシート',report);self.assertIn('button.buy &gt; svg',report)
        self.assertEqual(audit.load(self.run/'report.json')['counts'],{'not_run':54,'failed':1})

    def test_excel_human_view_is_active_printable_and_same_as_html_model(self):
        self.record_images();path=self.run/'report.xlsx';workbook.export(self.run,path)
        model=self.model();book=load_workbook(path)
        try:
            self.assertEqual(book.sheetnames[:2],['チェックシート','不適合箇所'])
            ws=book.active;self.assertEqual(ws.title,'チェックシート')
            self.assertEqual(ws.freeze_panes,'D7');self.assertTrue(ws.protection.sheet)
            self.assertEqual(ws.print_title_rows,'$1:$6')
            self.assertEqual([c.value for c in ws[6]],[label for _,label in checksheet.COLUMNS])
            self.assertEqual(ws.max_row,len(model['rows'])+6)
            for index,row in enumerate(model['rows'],7):
                self.assertEqual([c.value or '' for c in ws[index]],[row.get(key,'') for key,_ in checksheet.COLUMNS])
            self.assertEqual(book['不適合箇所'].cell(7,7).value,'button.buy > svg')
            failure_row=next(row for row in ws.iter_rows(min_row=7) if row[0].value=='1.1.1')
            self.assertEqual(failure_row[6].hyperlink.location,"'不適合箇所'!A7")
            self.assertIsNone(failure_row[6].hyperlink.target)
            self.assertEqual(book['達成基準'].max_row,87)
        finally:book.close()

    def test_human_sheet_edits_do_not_change_ledger_work_round_trip(self):
        self.record_images();path=self.run/'work.xlsx';workbook.export(self.run,path,mode='work',criterion='1.1.1')
        book=load_workbook(path);book['チェックシート']['F7']='○ 適合';book.save(path);book.close()
        before=(self.run/'plan.json').read_bytes()
        self.assertEqual(workbook.import_book(self.run,path)['changed_cases'],0)
        self.assertEqual((self.run/'plan.json').read_bytes(),before)
        self.assertEqual(audit.outcomes(self.run)['counts'],{'not_run':54,'failed':1})

    def test_formula_like_text_is_literal_in_new_sheets(self):
        self.record_images();result=audit.outcomes(self.run)
        case=next(c for c in result['cases'] if c['criterion']=='1.1.1')
        case['assessment_data']['targets'][1]['observed']='=HYPERLINK("https://example.invalid")'
        from openpyxl import Workbook
        book=Workbook();book.remove(book.active);workbook.human_sheets(book,self.model(result))
        path=self.run/'literal.xlsx';book.save(path);book.close();book=load_workbook(path)
        try:
            cell=book['不適合箇所'].cell(7,8)
            self.assertTrue(cell.value.startswith('='));self.assertEqual(cell.data_type,'s')
            self.assertFalse(any(c.data_type=='f' for ws in book for row in ws for c in row))
        finally:book.close()

    def test_long_scope_is_rejected_before_excel_can_truncate_it(self):
        from openpyxl import Workbook
        model=self.model();model['scope']='x'*32768
        book=Workbook();book.remove(book.active)
        try:
            with self.assertRaisesRegex(ValueError,'文字数'):workbook.human_sheets(book,model)
        finally:book.close()


if __name__=='__main__':unittest.main()
