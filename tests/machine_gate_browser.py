"""Reproduce the ten fixed machine checks that gate the next audit stage."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from time import monotonic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks import core


# T001 selected these rows before collection. The rest of each criterion is
# still evaluated and retained by the ordinary benchmark report.
FIELDS = ('checkpoint', 'case', 'page', 'state', 'target')
SELECTED = {
    ('1.1.1-01', 'c01', 'p01.html', 'initial', '#figure'): 'failed',
    ('1.1.1-01', 'c01', 'p01.html', 'initial', '#summary'): 'passed',
    ('1.1.1-01', 'c01', 'p01.html', 'initial', '#marker'): 'passed',
    ('1.1.1-01', 'c02', 'p02.html', 'initial', '#figure'): 'passed',
    ('1.1.1-01', 'c02', 'p02.html', 'initial', '#summary'): 'passed',
    ('1.1.1-01', 'c09', 'p09.html', 'after-load', '#subject'): 'failed',
    ('1.1.1-01', 'c10', 'p10.html', 'after-load', '#subject'): 'passed',
    ('2.4.2-01', 'c01', 'p01.html', 'initial', 'html'): 'failed',
    ('2.4.2-01', 'c02', 'p02.html', 'initial', 'html'): 'passed',
    ('2.4.2-01', 'c03', 'p03.html', 'initial', 'html'): 'passed',
}
RULES = {'1.1.1-01': 'image-alt', '2.4.2-01': 'document-title'}


def row_key(row):
    return tuple(row[name] for name in FIELDS)


def collect(run):
    started = monotonic()
    result = subprocess.run([sys.executable, str(ROOT/'benchmarks/run.py'), 'collect',
                             '--mode', 'machine', '--criterion', '1.1.1', '--criterion', '2.4.2',
                             '--out', str(run)], cwd=ROOT, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    paths = json.loads(result.stdout)['files']
    report_path = Path(paths['json'])
    report = core.load(report_path)
    meta, _ = core.verify(run)
    frozen = core.load(run/'integrity.json')['files']
    selected_rows = [row for row in report['rows'] if row['checkpoint'] in RULES and row['mode'] == 'machine']
    matched = {row_key(row): row for row in selected_rows}
    assert len(matched) == len(selected_rows) and set(matched) == SELECTED.keys(), list(matched)
    assert not any(row['checkpoint'] in RULES for row in report['unexpected_findings'])
    for key, expected in SELECTED.items():
        row = matched[key]
        assert row['actual'] == row['expected'] == expected and row['grade'] == 'correct', row
        assert row['method'] == 'program' and row['source'] == 'production axe / ' + RULES[key[0]], row
        assert row['evidence'] and all(path in frozen for path in row['evidence']), row
        if row['state'] != 'initial':
            assert {Path(path).name for path in row['evidence']} >= {'axe.json', 'state.json', 'transition.json'}, row
    assert report['overall_status'] == 'incomplete'
    assert any(row['checkpoint'] not in RULES and row['actual'] in {'not_run', 'cant_tell'}
               for row in report['rows'])
    return {
        'run': str(run), 'report': str(report_path), 'selected': selected_rows,
        'report_counts': report['counts'], 'overall_status': report['overall_status'],
        'matched_acquisition': len(report['matched_evidence_contracts']),
        'open_acquisition': len(report['pending_evidence_contracts']),
        'implementation_digest': meta['implementation_digest'], 'corpus_digest': meta['corpus_digest'],
        'environment': meta['environment'], 'seconds': round(monotonic() - started, 2),
    }


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    with ThreadPoolExecutor(max_workers=2) as executor:
        repetitions = list(executor.map(collect, [out/'first', out/'second']))
    for key in ('implementation_digest', 'corpus_digest', 'environment'):
        assert repetitions[0][key] == repetitions[1][key], key
    for run in repetitions:
        data = run['selected']
        assert sum(row['actual'] == 'failed' for row in data) == 3
    core.save(out/'observed.json', {'selected_matches': len(SELECTED), 'repetitions': repetitions})
    print(json.dumps({'evidence': str(out/'observed.json'), 'selected_matches': len(SELECTED),
                      'repetitions': len(repetitions)}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=lambda path: Path(path).resolve())
    main(parser.parse_args().out)
