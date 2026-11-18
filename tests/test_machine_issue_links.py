"""A machine finding links to the right report section without changing its verdict."""
from pathlib import Path
import unittest

from openpyxl import load_workbook

import test_checksheet as checksheet_fixture
import test_page_workflow as workflow_fixture


audit = checksheet_fixture.audit


class MachineIssueLinksTest(unittest.TestCase):
    def setUp(self):
        checksheet_fixture.ChecksheetTest.setUp(self)

    def tearDown(self):
        checksheet_fixture.ChecksheetTest.tearDown(self)

    def test_report_links_machine_issues_and_preserves_human_failure_link(self):
        workflow_fixture.WorkflowTest.graph(self)
        checksheet_fixture.ChecksheetTest.record_images(self)
        files = audit.write_page_reports(self.run, self.config['url'])
        html = Path(files['html']).read_text()
        self.assertIn('href="#failure-F00001"', html)
        self.assertIn('id="failure-F00001"', html)
        self.assertEqual(html.count('href="#machine-results">自動検出した問題の詳細'), 1)
        self.assertIn('id="machine-results"', html)
        self.assertEqual(audit.load(files['json'])['counts'], {'not_run': 54, 'failed': 1})
        book = load_workbook(files['excel'])
        self.addCleanup(book.close)
        by_label = {row[3].value: row for row in book['チェックシート'].iter_rows(min_row=7) if row[3].value}
        failed_machine = by_label['機械検査 / Images have alternatives']
        self.assertIn('img.chart', failed_machine[6].value)
        self.assertEqual(failed_machine[6].hyperlink.location, "'自動検出した問題'!A1")
        self.assertIsNone(failed_machine[6].hyperlink.target)
        self.assertEqual(failed_machine[5].value, '× 問題あり（機械）')
        self.assertIsNone(by_label['機械検査 / Document has a title'][6].hyperlink)
        failed_human = by_label['操作部品に目的を表す名前がある']
        self.assertEqual(failed_human[6].hyperlink.location, "'不適合箇所'!A7")
        self.assertIn('img.chart', book['自動検出した問題']['C2'].value)


if __name__ == '__main__':
    unittest.main()
