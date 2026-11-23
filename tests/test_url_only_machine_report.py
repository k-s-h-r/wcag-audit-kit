from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benchmarks import core, url_only_machine, url_only_machine_report as reporting, url_only_machine_score


def archive(path):
    return core.load(core.ROOT / 'validation/development' / path / 'machine-score.json')


class URLOnlyMachineReportTest(unittest.TestCase):
    def test_archived_scores_show_improvements_and_reverse_regressions(self):
        baseline = archive('vision/run-001')
        current = archive('vision-follow-up/run-002')
        self.assertEqual(reporting.summary(current)['correct'], 31)
        self.assertEqual(reporting.summary(current)['evaluated'], 31)
        comparison = reporting.compare(baseline, current)
        self.assertEqual(comparison['scorer_match'], 'unrecorded')
        self.assertEqual(comparison['regressions'], [])
        self.assertEqual([row['page_id'] for row in comparison['improvements']], ['039', '040', '068', '068', '069', '069'])
        self.assertEqual(len(reporting.compare(current, baseline)['regressions']), 6)

    def test_same_total_can_hide_a_regression(self):
        baseline = archive('vision-follow-up/run-002')
        current = deepcopy(baseline)
        correct = next(row for row in current['rows'] if row['status'] == 'detected')
        ungraded = next(row for row in current['rows']
                        if row['expected'] == 'failed' and row['status'] == 'observed_no_verdict')
        correct['status'], ungraded['status'] = ungraded['status'], correct['status']
        current['rows'].reverse()
        self.assertEqual(reporting.summary(baseline), reporting.summary(current))
        comparison = reporting.compare(baseline, current)
        self.assertEqual([row['target'] for row in comparison['regressions']], [correct['target']])
        self.assertEqual([row['target'] for row in comparison['improvements']], [ungraded['target']])

    def test_comparison_rejects_different_conditions_and_rows(self):
        baseline = archive('vision-follow-up/run-002')
        baseline['scorer_digest'] = 'baseline-scorer'
        for field, value in [('workers', 1), ('corpus_digest', 'different-corpus'),
                             ('environment', {'chromium': 'different'}), ('scorer_digest', 'different-scorer')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                reporting.compare(baseline, dict(baseline, **{field: value}))
        different_rows = deepcopy(baseline)
        different_rows['rows'][0]['expected'] = 'inapplicable'
        with self.assertRaisesRegex(ValueError, '比較対象の採点行'):
            reporting.compare(baseline, different_rows)
        different_rows['rows'][0] = different_rows['rows'][1]
        with self.assertRaisesRegex(ValueError, '重複'):
            reporting.compare(baseline, different_rows)

    def test_report_explains_detection_and_pages_outside_the_score(self):
        score = archive('vision-follow-up/run-002')
        with TemporaryDirectory() as directory:
            root = Path(directory)
            html = reporting.render(score, root, root / 'score.html', 'score.json')
        self.assertIn('既知の問題39件のうち12件を検出', html)
        self.assertIn('全87件のうち56件は確定判定が出ませんでした', html)
        self.assertIn('30.8%', html)
        self.assertIn('問題なしと正しく判定', html)
        self.assertEqual(reporting.status_label({'expected': 'inapplicable'}, 'matched'), '該当なしと正しく判定')
        self.assertIn('正解と照合できない指摘 14件', html)
        scope = reporting.corpus_scope(score['corpus_digest'])['1.1.1']
        self.assertEqual(set(scope), {f'p{i:02}.html' for i in range(1, 12)})
        self.assertIn(('1.1.1-04', 'content_review'), scope['p02.html'])
        self.assertIn(('1.1.1-04', 'content_review'), scope['p05.html'])
        self.assertIn(('1.1.1-02', 'acquisition'), scope['p05.html'])
        self.assertIn(('1.1.1-03', 'screen-reader'), scope['p07.html'])
        self.assertIn('<th scope="row">p03.html</th><td>採点対象の行なし</td>', html)

    def test_report_does_not_guess_excluded_pages_when_corpus_changed(self):
        score = archive('vision-follow-up/run-002')
        score['corpus_digest'] = 'different-corpus'
        with TemporaryDirectory() as directory:
            root = Path(directory)
            html = reporting.render(score, root, root / 'score.html', 'score.json')
        self.assertIn('収集時と同じ版の問題集を参照できない', html)
        self.assertIn('1.1.1 の採点行', html)
        self.assertNotIn('1.1.1 のページ別採点範囲', html)

    def test_cli_writes_report_and_returns_nonzero_on_regression(self):
        baseline = archive('vision-follow-up/run-002')
        current = deepcopy(baseline)
        row = current['rows'][0]
        row['status'] = 'observed_no_verdict'
        with TemporaryDirectory() as directory, redirect_stdout(StringIO()):
            root = Path(directory).resolve()
            baseline_path = root / 'baseline.json'
            core.save(baseline_path, baseline)
            run = root / 'run'
            proof = run / row['environments']['desktop']['verdicts'][0]['evidence']

            def collect(output, workers):
                self.assertEqual(output, run)
                self.assertEqual(workers, baseline['workers'])
                proof.parent.mkdir(parents=True)
                proof.write_text('{}')

            with patch.object(url_only_machine, 'collect', side_effect=collect) as collection, \
                    patch.object(url_only_machine_score, 'score', return_value=current):
                code = url_only_machine.main(['--out', str(run), '--workers', str(baseline['workers']),
                                              '--report', '--baseline', str(baseline_path)])
            collection.assert_called_once()
            self.assertEqual(code, 1)
            html = (run / 'score.html').read_text()
            self.assertIn('回帰 1行', html)
            self.assertIn(f'href="{proof.relative_to(run).as_posix()}"', html)
            self.assertIn('全採点行', html)
            self.assertEqual(core.load(run / 'score.json')['comparison']['regressions'][0]['page_id'], '001')
            self.assertEqual(core.load(baseline_path), baseline)
