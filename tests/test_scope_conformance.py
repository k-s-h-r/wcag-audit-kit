"""Exercise the report commands against fixed synthetic assessment ledgers."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from openpyxl import load_workbook

from test_ledger import audit
from browser_capture import page_id
from test_report_output_layout import Links


FIRST = 'http://127.0.0.1:49321/start'
SECOND = 'http://127.0.0.1:49321/confirm'


def fixture(out, *, pages, title, scope_complete, leave_other_cases_pending=False):
    run = audit.run_layout.create(out)
    config = audit.init_config(pages[0])
    config.update(level='A', environments=config['environments'][:1])
    config['scope'].update(mode='configured', pages=pages)
    if SECOND in pages:
        config['states'].append({'id': 'confirmation', 'paths': ['/confirm']})
    meta = dict(config=config, config_digest=audit.digest(config), catalog_digest=audit.digest(audit.CATALOG))
    audit.save(run / 'run.json', meta)
    audit.snapshot_catalog(run)
    captures = []
    for url in pages:
        pid = page_id(url)
        for state in (['initial', 'confirmation'] if url == SECOND else ['initial']):
            path = f'evidence/{pid}/{state}'
            captures.append(dict(key=f'{pid}--{state}--desktop', page_id=pid, url=url, state=state,
                                 environment='desktop', execution='completed', http_status=200,
                                 evidence_dir=path))
            audit.save(run / path / 'inventory.json', dict(fixture=True, title=title.get(url, '未確認')))
            if title.get(url) == 'candidate':
                audit.save(run / path / 'axe.json', dict(violations=[dict(id='document-title',
                    help='ページタイトルがある', tags=['wcag242'], nodes=[dict(target=['html'])])]))
    manifest = dict(pages=[dict(id=page_id(url), url=url) for url in pages], captures=captures,
                    collector_status='completed', unvisited=[], declared_states_without_page=[])
    audit.save(run / 'capture-manifest.json', manifest)
    plan = audit.make_plan(run, manifest)
    records = []
    for case in plan['cases']:
        url = case['page_url']
        title_outcome = title.get(url)
        if title_outcome == 'candidate' or (leave_other_cases_pending and title_outcome == 'failed' and
                                             case['criterion'] != '2.4.2'):
            continue
        outcome = title_outcome if case['criterion'] == '2.4.2' else 'inapplicable'
        proof = case['evidence_dir'] + '/inventory.json'
        targets = [] if outcome == 'inapplicable' else [dict(target='document.title', outcome=outcome,
            observed='タイトルは本文の目的を示す' if outcome == 'passed' else 'タイトルなし',
            expected='タイトルでページの目的を示す', evidence=[proof])]
        judgment = dict(case_id=case['case_id'], config_digest=meta['config_digest'],
            normative_sha256=audit.CRITERIA[case['criterion']]['normative_sha256'],
            outcome=outcome, execution='completed', observed='結論の集計を確かめるために固定した試験記録。',
            conditions_reviewed=True, exceptions_reviewed=True, coverage_complete=True,
            remaining=[], tests_applied=['fixture'], steps_executed=['固定URLの画面と文書のタイトルを比較した。'],
            evidence=[proof], targets=targets, method_coverage=[
                dict(method=method, status='executed', reason='保存済み試験用の観察方法を固定した。')
                for method in audit.CRITERIA[case['criterion']]['methods']])
        records.append(audit.prepare_record(run, judgment, plan))
    audit.commit_records(run, plan, records)
    scope = dict(config_digest=meta['config_digest'], complete=scope_complete, processes_reviewed=scope_complete,
        full_pages_reviewed=True, accessibility_support_reviewed=True, non_interference_reviewed=True,
        sources=['合成試験のページ・手続き一覧'], observed='合成試験の範囲と手続きの確認結果を固定した。',
        remaining=[] if scope_complete else ['確認画面までの手続きを追加確認する。'],
        evidence=[captures[0]['evidence_dir'] + '/inventory.json'])
    audit.save(run / 'scope-review.json', audit.validate_scope_review(run, scope))
    return run


def report(out, *, strict_code, page=None):
    run = audit.run_layout.ledger(out)
    args = ['report', '--strict'] if page is None else ['page-report', '--page-exact', page]
    files = audit.report_paths(run, page)
    with redirect_stdout(io.StringIO()), patch('browser_capture.collect', side_effect=AssertionError('report opened a browser')):
        status = audit.main([*args, '--run', str(out)])
        if status == strict_code and page is None and not files.excel.exists():
            assert audit.main(['excel', 'export', '--run', str(out), '--mode', 'report', '--out', str(files.excel)]) == 0
    assert status == strict_code, status
    return files


class ScopeConformanceTest(unittest.TestCase):
    def assert_outputs(self, files, expected, label):
        data = audit.load(files.json)
        value = data['scope_conformance']
        self.assertEqual(value['status'], expected)
        self.assertEqual(value['standard'], 'WCAG-2.2')
        self.assertEqual(value['level'], 'A')
        self.assertEqual(value['label'], label)
        html = files.html.read_text()
        self.assertIn(f'<strong>WCAG 2.2 A の結論　{label}</strong>', html)
        self.assertIn('範囲と適合要件の確認記録', html)
        self.assertIn(f'WCAG 2.2 A の結論　{label}', files.issues.read_text())
        book = load_workbook(files.excel)
        try:
            self.assertIn(f'WCAG 2.2 A の結論　{label}', book['チェックシート']['A2'].value)
            self.assertIn(f'WCAG 2.2 A の結論　{label}', book['不適合箇所']['A2'].value)
            overview = dict(book['概要'].iter_rows(min_row=2, values_only=True))
            self.assertEqual(overview['結論に残る確認'] or '', '\n'.join(value['remaining']))
            self.assertEqual(overview['検証完了'], data['audit_complete'])
            urls = [row[0] for row in book['結論の対象URL'].iter_rows(min_row=2, values_only=True)]
            self.assertEqual(urls, value['scope']['urls'])
        finally:
            book.close()
        return value

    def test_single_page_conforms_and_report_keeps_the_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'scope'
            run = fixture(out, pages=[FIRST], title={FIRST: 'passed'}, scope_complete=True)
            originals = {p: p.read_bytes() for p in run.rglob('*') if p.is_file()}
            files = report(out, strict_code=0)
            value = self.assert_outputs(files, 'conforms', '適合')
            self.assertEqual(value['scope']['urls'], [FIRST])
            self.assertTrue(value['scope']['covers_reviewed_run'])
            self.assertFalse(value['remaining'])
            self.assertTrue(audit.load(files.json)['audit_complete'])
            report(out, strict_code=0, page=FIRST)
            self.assertEqual(value, audit.load(files.json)['scope_conformance'])
            self.assertEqual(originals, {p: p.read_bytes() for p in originals})

    def test_multi_page_failure_preserves_unknown_and_reaches_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'scope'
            run = fixture(out, pages=[FIRST, SECOND], title={FIRST: 'passed', SECOND: 'failed'},
                          scope_complete=False, leave_other_cases_pending=True)
            files = report(out, strict_code=2)
            value = self.assert_outputs(files, 'does_not_conform', '不適合')
            self.assertFalse(audit.load(files.json)['audit_complete'])
            self.assertFalse(value['scope_requirements']['processes_reviewed'])
            self.assertIn('確認画面までの手続きを追加確認する。', value['remaining'])
            self.assertEqual(value['scope']['urls'], [FIRST, SECOND])
            self.assertEqual({f['criterion'] for f in value['failed_cases']}, {'2.4.2'})
            self.assertEqual({f['url'] for f in value['failed_cases']}, {SECOND})
            self.assertEqual({f['state'] for f in value['failed_cases']}, {'initial', 'confirmation'})
            for item in value['failed_cases']:
                self.assertTrue((run / item['record']).is_file())
                self.assertTrue(all((run / proof).is_file() for proof in item['evidence']))
            self.assertIn('#failures', Links(files.html.read_text()).links)
            self.assertIn('固定URLの画面と文書のタイトルを比較した。', files.issues.read_text())
            self.assert_outputs(report(out, strict_code=0, page=FIRST), 'unverified', '未確認')
            self.assert_outputs(report(out, strict_code=0, page=SECOND), 'does_not_conform', '不適合')

    def test_machine_candidate_does_not_make_scope_nonconforming(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'scope'
            fixture(out, pages=[FIRST], title={FIRST: 'candidate'}, scope_complete=False)
            files = report(out, strict_code=2)
            value = self.assert_outputs(files, 'unverified', '未確認')
            self.assertFalse(value['failed_cases'])
            self.assertTrue(value['pending_cases'])
            self.assertTrue(audit.load(files.json)['machine_checks'])

    def test_completed_audit_with_failure_preserves_strict_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'scope'
            fixture(out, pages=[FIRST], title={FIRST: 'failed'}, scope_complete=True)
            files = report(out, strict_code=0)
            value = self.assert_outputs(files, 'does_not_conform', '不適合')
            self.assertTrue(audit.load(files.json)['audit_complete'])
            self.assertFalse(value['remaining'])

    def test_single_page_report_keeps_declared_states_without_a_page(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'scope'
            run = fixture(out, pages=[FIRST], title={FIRST: 'passed'}, scope_complete=True)
            manifest = audit.load(run / 'capture-manifest.json')
            manifest['declared_states_without_page'] = ['confirmation']
            audit.save(run / 'capture-manifest.json', manifest)
            files = report(out, strict_code=0, page=FIRST)
            value = self.assert_outputs(files, 'unverified', '未確認')
            self.assertEqual(value['declared_states_without_page'], ['confirmation'])
            excel = Path(directory) / 'run.xlsx'
            with redirect_stdout(io.StringIO()):
                self.assertEqual(audit.main(['excel', 'export', '--run', str(out), '--mode', 'report', '--out', str(excel)]), 0)
            book = load_workbook(excel)
            try:
                self.assertIn('WCAG 2.2 A の結論　未確認', book['チェックシート']['A2'].value)
            finally:
                book.close()

    def test_excel_references_the_report_for_oversized_scope_notes(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'scope'
            run = fixture(out, pages=[FIRST], title={FIRST: 'candidate'}, scope_complete=False)
            scope = audit.load(run / 'scope-review.json')
            scope['remaining'] = [f'確認事項 {n} ' * 255 for n in range(180)]
            audit.save(run / 'scope-review.json', scope)
            files = report(out, strict_code=2)
            book = load_workbook(files.excel)
            try:
                overview = dict(book['概要'].iter_rows(min_row=2, values_only=True))
                self.assertIn('全文を確認', overview['結論に残る確認'])
                value = audit.load(files.json)['scope_conformance']
                self.assertTrue(all(reason in value['remaining'] for reason in scope['remaining']))
            finally:
                book.close()


if __name__ == '__main__':
    unittest.main()
