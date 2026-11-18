"""Focus screenshots and their receipts are linked without adding verdicts."""
from pathlib import Path
import unittest
from unittest.mock import patch

from openpyxl import load_workbook

import test_page_workflow as fixture

audit = fixture.audit
page_workflow = fixture.page_workflow
workbook = fixture.workbook


class FocusEvidenceReportsTest(unittest.TestCase):
    def setUp(self):
        fixture.WorkflowTest.setUp(self)

    def tearDown(self):
        fixture.WorkflowTest.tearDown(self)

    def test_links_to_paired_images_and_partial_receipt(self):
        base = 'evidence/example/'
        before = base + 'focus before.png'
        after = base + 'focus#after.png'
        receipt = base + 'keyboard-check.json'
        for relative in (before, after, receipt):
            audit.save(self.run / relative, {})
        outside = self.run / 'outside.png'
        outside.touch()
        escape_path = base + '../../outside.png'
        linked_path = self.run / base / 'linked.png'
        linked_path.symlink_to(outside)
        row = dict(criterion='2.4.7', name='キーボードで保存ボタンに移動', target='#save<script>',
                   environment='desktop', status='captured', reason='実キーで入力前後を取得',
                   before_image=before, after_image=after, evidence=receipt)
        rows = [
            row,
            dict(row, status='skipped', reason='画像の設定で省略', before_image='', after_image=''),
            dict(row, status='incomparable', reason='証拠パスが範囲外', before_image=escape_path,
                 after_image=base + 'linked.png'),
        ]
        original = page_workflow.page_result

        def with_focus_evidence(*args, **kwargs):
            return dict(original(*args, **kwargs), focus_evidence=rows)

        with patch.object(page_workflow, 'page_result', side_effect=with_focus_evidence):
            files = audit.write_page_reports(self.run, self.config['url'])
            migrated = self.run / 'exported' / 'moved.xlsx'
            workbook.export(self.run, migrated, page_exact=self.config['url'], page_view=True)
        saved = audit.load(files['json'])
        self.assertEqual(saved['focus_evidence'], rows)
        self.assertEqual(saved['counts'], {'not_run': 55})
        html = Path(files['html']).read_text()
        self.assertIn('href="#focus-image-evidence"', html)
        self.assertIn('aria-labelledby="focus-image-evidence"', html)
        self.assertIn('#save&lt;script&gt;', html)
        self.assertIn('href="evidence/example/focus%20before.png"', html)
        self.assertIn('href="evidence/example/focus%23after.png"', html)
        self.assertNotIn(f'href="{escape_path}"', html)
        self.assertNotIn('href="evidence/example/linked.png"', html)

        for filename, prefix in ((files['excel'], ''), (migrated, '../')):
            with self.subTest(filename=filename):
                book = load_workbook(filename)
                try:
                    sheet = book['フォーカスの画像証拠']
                    self.assertEqual(tuple(cell.value for cell in sheet[1]),
                                     tuple(name for _, name in workbook.FOCUS_EVIDENCE_COLUMNS))
                    self.assertEqual(sheet['E2'].value, '取得済み')
                    self.assertEqual(sheet['G2'].value, before)
                    self.assertEqual(sheet['G2'].hyperlink.target, prefix + base + 'focus%20before.png')
                    self.assertEqual(sheet['H2'].hyperlink.target, prefix + base + 'focus%23after.png')
                    self.assertEqual(sheet['E3'].value, '取得省略')
                    self.assertIsNone(sheet['G3'].hyperlink)
                    self.assertEqual(sheet['I3'].hyperlink.target, prefix + receipt)
                    self.assertEqual(sheet['E4'].value, '比較不可')
                    self.assertIsNone(sheet['G4'].hyperlink)
                    self.assertIsNone(sheet['H4'].hyperlink)
                finally:
                    book.close()


if __name__ == '__main__':
    unittest.main()
