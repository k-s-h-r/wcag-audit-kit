"""Check that the experimental layouts preserve scoped conclusions and gaps."""
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import unquote, urlsplit

from test_report_output_layout import Links
from test_scope_conformance import FIRST, SECOND, fixture


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'validation/development/T045/render.py'


class ReportPrototypesTest(unittest.TestCase):
    def render(self, source, out):
        return subprocess.run([sys.executable, str(CLI), '--run', str(source), '--out', str(out),
                               '--title', '予約 <試作>'], capture_output=True, text=True)

    def test_layouts_reuse_the_same_records_and_keep_the_source(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / 'run'
            fixture(source, pages=[FIRST, SECOND], title={FIRST: 'passed', SECOND: 'failed'},
                    scope_complete=False, leave_other_cases_pending=True)
            original = {p: p.read_bytes() for p in source.rglob('*') if p.is_file()}
            out = Path(tmp) / 'preview'
            result = self.render(source, out)
            self.assertEqual(result.returncode, 0, result.stderr)

            overview = (out / 'index.html').read_text()
            first = (out / 'page-1.html').read_text()
            second = (out / 'page-2.html').read_text()
            acr = (out / 'acr.html').read_text()
            self.assertIn('予約 &lt;試作&gt;', overview)
            self.assertIn('未確認</span>', first)
            self.assertIn('不適合</span>', second)
            self.assertNotIn(FIRST, second)
            for report in (second, acr):
                self.assertIn('2.4.2', report)
                self.assertIn('タイトルなし', report)
                self.assertIn('検査は未実施', report)
                self.assertIn('残る確認', report)
                self.assertIn('2.4.2 の記録 1', report)
            for file in out.glob('*.html'):
                for link in Links(file.read_text()).links:
                    url = urlsplit(link)
                    if url.path and not url.scheme:
                        self.assertTrue((file.parent / unquote(url.path)).is_file(), link)

            self.assertNotEqual(self.render(source, out).returncode, 0)
            self.assertNotEqual(self.render(source, source / 'preview').returncode, 0)
            self.assertEqual(original, {p: p.read_bytes() for p in source.rglob('*') if p.is_file()})

    def test_machine_candidate_remains_unverified(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / 'run'
            fixture(source, pages=[FIRST], title={FIRST: 'candidate'}, scope_complete=False)
            out = Path(tmp) / 'preview'
            result = self.render(source, out)
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ('index.html', 'page-1.html', 'acr.html'):
                html = (out / name).read_text()
                self.assertIn('未確認', html)
                self.assertNotIn('class="status failed"', html)
                self.assertNotIn('class="status passed"', html)
