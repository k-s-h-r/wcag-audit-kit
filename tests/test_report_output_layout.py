"""Read-only report outputs include actual configured-state evidence."""
import contextlib
from html.parser import HTMLParser
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from openpyxl import load_workbook

from test_ledger import audit
from browser_capture import page_id


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs)['href'])


class OutputLayoutTest(unittest.TestCase):
    def test_configured_page_reports_are_readable_and_refresh_in_place(self):
        url = 'https://example.test/'
        pid = page_id(url)
        raw = dict(
            url=url,
            passes=[dict(id='color-contrast', help='Minimum contrast', tags=['wcag143'],
                         nodes=[dict(target=['#title'], any=[dict(data={'contrastRatio': 5.45})])])],
            inapplicable=[dict(id='image-alt', help='Text alternatives', tags=['wcag111'], nodes=[])],
            incomplete=[], violations=[],
        )

        async def collect(config, work):
            capture = dict(key=f'{pid}--initial--desktop', page_id=pid, url=url, state='initial',
                           environment='desktop', execution='completed', http_status=200,
                           evidence_dir='evidence/example # node')
            audit.save(work / capture['evidence_dir'] / 'axe.json', raw)
            manifest = dict(captures=[capture], pages=[dict(id=pid, url=url)], unvisited=[],
                            declared_states_without_page=[])
            audit.save(work / 'capture-manifest.json', manifest)
            return manifest

        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            out = Path(directory) / 'audit run'
            with patch('browser_capture.collect', side_effect=collect) as browser:
                self.assertEqual(audit.main(['page', '--url', url, '--out', str(out), '--mode', 'machine']), 0)
                self.assertEqual(browser.call_count, 1)
            self.assertEqual({p.name for p in out.iterdir()}, {'reports', 'data', 'work'})
            work = audit.run_layout.ledger(out)
            files = audit.run_layout.report_files(work, single=True)
            original = {p: p.read_bytes() for p in [work / 'plan.json', work / 'catalog.snapshot.json',
                                                     *work.rglob('axe.json')]}
            for command in (['page-report', '--page-exact', url], ['report']):
                with patch('browser_capture.collect', side_effect=AssertionError('report opened a browser')):
                    self.assertEqual(audit.main([*command, '--run', str(out)]), 0)
            self.assertEqual({p.name for p in files.html.parent.iterdir()}, {'report.html', 'report.xlsx', 'details'})
            self.assertEqual(list(files.json.parent.iterdir()), [files.json])
            self.assertEqual({p: p.read_bytes() for p in original}, original)

            data = audit.load(files.json)
            self.assertEqual(data['evidence_base'], '../work')
            self.assertEqual(data['counts'], {'not_run': 55})
            self.assertFalse(data['audit_complete'])
            self.assertEqual(len(data['machine_checks']), 2)
            html = files.html.read_text()
            self.assertLess(html.index('id="failures"'), html.index('id="performed"'))
            self.assertLess(html.index('id="performed"'), html.index('id="remaining"'))
            self.assertLess(html.index('id="details"'), html.index('モード別の確認範囲'))
            self.assertIn('5.45:1', html)
            self.assertNotIn('未実施 1票', html)
            self.assertNotIn('目的に相当する代替があるか。', html)
            for link in Links(html).links:
                url_parts = urlsplit(link)
                if url_parts.path and not url_parts.scheme:
                    self.assertTrue((files.html.parent / unquote(url_parts.path)).is_file(), link)

            workbook = load_workbook(files.excel)
            try:
                rows = list(workbook['チェックシート'].values)
                columns = rows[5]
                contrast = next(row for row in rows[6:] if row[0] == '1.4.3')
                images = next(row for row in rows[6:] if row[0] == '1.1.1')
                self.assertEqual(contrast[columns.index('適用')], 'あり')
                self.assertEqual(contrast[columns.index('適合')], '未確認')
                self.assertEqual(images[columns.index('適用')], '未確認')
                self.assertIn('対象なし', images[columns.index('確認結果')])
                self.assertEqual(workbook['機械検査'].max_row, 3)
            finally:
                workbook.close()

    def test_a_page_report_does_not_include_another_pages_axe_result(self):
        first = 'https://example.test/'
        second = first + 'other'
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            config = audit.init_config(first)
            config['environments'] = config['environments'][:1]
            config['scope'].update(mode='configured', pages=[first, second])
            audit.save(run / 'run.json', dict(config=config, config_digest=audit.digest(config),
                                              catalog_digest=audit.digest(audit.CATALOG)))
            pages, captures = [], []
            for index, url in enumerate([first, second]):
                pid = page_id(url)
                pages.append(dict(id=pid, url=url))
                path = f'evidence/page-{index}'
                captures.append(dict(key=f'{pid}--initial--desktop', page_id=pid, url=url, state='initial',
                                     environment='desktop', execution='completed', evidence_dir=path))
                audit.save(run / path / 'axe.json',
                           dict(violations=[dict(id='image-alt', help='画像に代替テキストがある',
                                tags=['wcag111'], nodes=[dict(target=[f'#image-{index}'])])]))
            manifest = dict(pages=pages, captures=captures, unvisited=[], declared_states_without_page=[])
            audit.save(run / 'capture-manifest.json', manifest)
            audit.make_plan(run, manifest)
            from page_workflow import page_result

            self.assertEqual(len(audit.outcomes(run)['machine_checks']), 2)
            result = page_result(run, second)
            self.assertEqual([row['target'] for row in result['machine_checks']], ["['#image-1']"])
