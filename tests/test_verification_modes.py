import copy
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'))
import audit
import verification_modes as modes
import page_workflow
import test_ledger as ledger_fixture


class ModeSelectionTest(unittest.TestCase):
    def test_mode_chooses_ai_and_reader_independently(self):
        for name,ai,sr in [('machine',False,False),('ai',True,False),('screen-reader',False,True),('full',True,True)]:
            with self.subTest(mode=name):
                c=modes.select(audit.init_config('http://example.test'),name)
                self.assertEqual(c['inspection']['screen_reader'],'required' if sr else 'off')
                self.assertEqual(c['inspection']['screenshots']!='off',ai)
                self.assertEqual(c['verification']['mode'],name)

    def test_conflicting_explicit_options_are_rejected(self):
        for name,options in [('machine',{'screenshots':'states'}),('ai',{'screen_reader':'required'}),
                             ('screen-reader',{'screen_reader':'off'}),('full',{'max_images':0})]:
            with self.subTest(mode=name),self.assertRaises(ValueError):
                modes.select(audit.init_config('http://example.test'),name,**options)
        with self.assertRaises(ValueError):modes.policy({'mode':'ai','ai':False})

    def test_image_depth_does_not_silently_enable_screen_reader(self):
        c=modes.select(audit.init_config('http://example.test'),'ai',profile='thorough',max_images=30)
        self.assertEqual(c['inspection']['screenshots'],'all')
        self.assertEqual(c['inspection']['screen_reader'],'off')

    def test_mode_can_be_configured_without_inspection_defaults(self):
        c=audit.init_config('http://example.test');c['verification']={'mode':'screen-reader'}
        c=audit.validate_config(c)
        self.assertEqual(c['inspection']['screenshots'],'off')
        self.assertEqual(c['inspection']['screen_reader'],'required')

    def test_partial_image_settings_use_selected_modes_defaults(self):
        c=audit.init_config('http://example.test');c['verification']={'mode':'full'}
        c['inspection']={'max_images':5}
        c=audit.validate_config(c)
        self.assertEqual(c['inspection']['screenshots'],'all')
        self.assertEqual(c['inspection']['screen_reader'],'required')
        self.assertEqual(c['inspection']['max_images'],5)

    def test_alt_existence_semantics_and_actual_speech_are_distinct(self):
        rows={r['id']:r for r in modes.validate_catalog(modes.catalog())['checkpoints']}
        self.assertEqual(rows['1.1.1-01']['support']['machine'],'yes')
        self.assertEqual(rows['1.1.1-04']['support']['machine'],'partial')
        self.assertEqual(rows['1.1.1-04']['support']['ai'],'yes')
        self.assertEqual(rows['1.1.1-03']['support']['ai'],'no')
        self.assertEqual(rows['1.1.1-03']['support']['screen-reader'],'yes')
        for ident in ['1.2.6-02','2.3.1-02','3.1.5-02']:
            self.assertEqual(set(rows[ident]['support'].values()),{'no'})

    def test_generated_matrix_and_details_match_the_shared_definition(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        import build_mode_matrix
        value=modes.validate_catalog(modes.catalog())
        self.assertIn(build_mode_matrix.render(value),(ROOT/'README.md').read_text())
        self.assertEqual(build_mode_matrix.details(value),(ROOT/'skills/wcag-audit-kit/references/verification-checkpoints.md').read_text())
        self.assertEqual(len(value['checkpoints']),131)
        self.assertEqual(len({r['criterion'] for r in value['checkpoints']}),86)

    def test_new_page_audit_defaults_to_machine_without_calling_an_ai_service(self):
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp)/'new-run'
            with patch.object(audit,'run_page_audit',return_value=0):
                self.assertEqual(audit.main(['page-audit','--url','http://example.test','--out',str(run)]),0)
            meta=audit.run_meta(run)
            self.assertEqual(meta['config']['verification'],{'mode':'machine'})
            self.assertEqual(meta['config']['inspection']['max_images'],0)
            self.assertTrue((run/'verification.snapshot.json').exists())

    def test_generated_config_can_change_image_depth_without_changing_capabilities(self):
        with tempfile.TemporaryDirectory() as temp,contextlib.redirect_stdout(io.StringIO()):
            config=Path(temp)/'config.json';run=Path(temp)/'run'
            self.assertEqual(audit.main(['init','--url','http://example.test','--config',str(config),'--mode','ai']),0)
            self.assertTrue(all(e['zoom']==1 for e in audit.load(config)['environments']))
            with patch.object(audit,'run_page_audit',return_value=0):
                self.assertEqual(audit.main(['page-audit','--url','http://example.test','--config',str(config),
                    '--out',str(run),'--profile','thorough']),0)
            selected=audit.run_meta(run)['config']
            self.assertEqual(selected['verification']['mode'],'ai')
            self.assertEqual(selected['inspection']['screenshots'],'all')
            self.assertEqual(selected['inspection']['screen_reader'],'off')


class ModeLedgerTest(unittest.TestCase):
    def setUp(self):ledger_fixture.LedgerTest.setUp(self)
    def tearDown(self):ledger_fixture.LedgerTest.tearDown(self)

    def enable(self,name):
        c=copy.deepcopy(self.config)
        c['scope'].update(mode='configured',pages=[c['url']],max_pages=1)
        c['environments']=c['environments'][:1]
        self.config=modes.select(c,name)
        meta=audit.run_meta(self.run);meta.update(config=self.config,config_digest=audit.digest(self.config))
        modes.snapshot(self.run,meta);audit.save(self.run/'run.json',meta)
        self.plan['config_digest']=meta['config_digest'];audit.save(self.run/'plan.json',self.plan)

    def test_legacy_run_is_not_assigned_a_mode_or_new_snapshot(self):
        before=(self.run/'run.json').read_bytes()
        self.assertIsNone(audit.outcomes(self.run)['verification'])
        self.assertFalse((self.run/'verification.snapshot.json').exists())
        self.assertEqual((self.run/'run.json').read_bytes(),before)

    def test_mode_yes_does_not_pass_an_unexecuted_wcag_case(self):
        self.enable('ai');result=audit.outcomes(self.run)
        self.assertEqual(result['counts'],{'not_run':55})
        self.assertFalse(result['audit_complete'])
        self.assertEqual(result['verification']['ai_usage'],'not_inferred_from_mode')
        self.assertTrue(all(r['verification_status']=='not_evaluated' for r in result['verification']['checkpoints']))

    def test_machine_work_packet_omits_ai_instructions_and_skips_real_reader(self):
        self.enable('machine');packet=page_workflow.next_work(self.run,self.config['url'],limit=1)
        self.assertEqual(packet['verification']['mode'],'machine')
        self.assertNotIn('checkpoints',packet['verification'])
        alt=packet['next_cases'][0]
        self.assertEqual(alt['criterion'],'1.1.1')
        self.assertIn('1.1.1-03',{r['id'] for r in alt['skipped_checkpoints']})
        for row in alt['verification_checkpoints']:
            self.assertIsNone(row['ai_instruction'])
            self.assertFalse(row['screen_reader_allowed'])
        self.assertEqual(audit.outcomes(self.run)['counts'],{'not_run':55})

    def test_selected_reader_is_not_reported_as_executed(self):
        self.enable('screen-reader');result=audit.outcomes(self.run)
        self.assertEqual(result['verification']['screen_reader_status'],'not_run')
        self.assertFalse(result['interaction_review']['complete'])
        self.assertFalse(result['audit_complete'])

    def test_one_pages_speech_does_not_complete_other_pages(self):
        self.enable('full')
        result={'cases':[{'page_id':'one'},{'page_id':'two'}],
                'interaction_review':{'pages':{'one':{'screen_reader':{'status':'reviewed'}}}}}
        self.assertEqual(modes.summary(self.run,result)['screen_reader_status'],'partial')

    def test_saved_mode_definition_is_not_replaced_by_new_installed_availability(self):
        self.enable('ai');saved=(self.run/'verification.snapshot.json').read_bytes()
        with patch.object(modes,'catalog',side_effect=AssertionError('must read saved definition')):
            summary=modes.summary(self.run)
        self.assertEqual(summary['mode'],'ai')
        self.assertEqual((self.run/'verification.snapshot.json').read_bytes(),saved)

    def test_snapshot_tamper_is_rejected_before_any_new_report(self):
        self.enable('machine');value=audit.load(self.run/'verification.snapshot.json')
        value['checkpoints'][0]['support']['machine']='no';audit.save(self.run/'verification.snapshot.json',value)
        with self.assertRaisesRegex(ValueError,'スナップショットが変更'):audit.report(self.run)
        self.assertFalse((self.run/'report.json').exists())

    def test_changed_mode_snapshot_cannot_accept_a_new_judgment(self):
        self.enable('ai');value=audit.load(self.run/'verification.snapshot.json')
        value['checkpoints'][0]['support']['machine']='no';audit.save(self.run/'verification.snapshot.json',value)
        judgment=copy.deepcopy(self.judgment);judgment['config_digest']=audit.digest(self.config)
        with self.assertRaisesRegex(ValueError,'スナップショットが変更'):audit.record(self.run,judgment)
        self.assertFalse((self.run/'assessments').exists())

    def test_resume_cannot_switch_modes_or_modify_saved_configuration(self):
        self.enable('machine');before=(self.run/'run.json').read_bytes()
        with patch('page_explorer.explore') as explore,contextlib.redirect_stderr(io.StringIO()):
            code=audit.main(['page-audit','--url',self.config['url'],'--out',str(self.run),'--resume','--mode','ai'])
        self.assertEqual(code,1);explore.assert_not_called()
        self.assertEqual((self.run/'run.json').read_bytes(),before)

    def test_html_json_excel_show_same_availability_without_fabricating_results(self):
        from openpyxl import load_workbook
        self.enable('full')
        with contextlib.redirect_stdout(io.StringIO()):files=audit.write_page_reports(self.run,self.config['url'])
        result=audit.load(files['json']);html=Path(files['html']).read_text()
        self.assertIn('選択した検証モード：AI＋スクリーンリーダー',html)
        self.assertIn('実スクリーンリーダーの記録：未実施',html)
        self.assertEqual(result['verification']['screen_reader_status'],'not_run')
        self.assertEqual(result['counts'],{'not_run':55})
        book=load_workbook(files['excel'])
        try:
            self.assertEqual(book.sheetnames[:2],['チェックシート','不適合箇所'])
            ws=book['モード別の確認範囲'];self.assertTrue(ws.protection.sheet)
            headers=[c.value for c in ws[1]]
            rows=[dict(zip(headers,r)) for r in ws.iter_rows(min_row=2,values_only=True)]
            self.assertEqual(len(rows),131)
            for actual,expected in zip(rows,result['verification']['checkpoints']):
                self.assertEqual(actual['基準'],expected['criterion'])
                self.assertEqual(actual['選択モードの対応'],expected['symbol'])
        finally:book.close()

if __name__=='__main__':unittest.main()
