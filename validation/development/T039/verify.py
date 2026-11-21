"""Check dialog-exit scoring with the published captures and disposable copies."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from benchmarks import core
from benchmarks.url_only_machine_score import score
from keyboard_trap import CHECKPOINT


T030 = ROOT / 'validation/development/T030/run-003'
ARCHIVE = T030 / 'dialog-evidence.zip'
VISION_SCORE = ROOT / 'validation/development/vision/run-001/machine-score.json'


def previous_score(worktree, run):
    result = run.parent / f'{run.name}-previous-score.json'
    subprocess.run([sys.executable, str(worktree / 'benchmarks/url_only_machine.py'),
                    '--out', str(run), '--score', str(result)], check=True, capture_output=True)
    return core.load(result)


def outcomes(data, page):
    row, = (row for row in data['rows'] if row['page_id'] == page and row['checkpoint'] == '2.1.2-02')
    return {
        'status': row['status'],
        'verdicts': {env: [verdict['outcome'] for verdict in evidence['verdicts']]
                     for env, evidence in row['environments'].items()},
        'reached': {env: evidence['reached'] for env, evidence in row['environments'].items()},
    }


def change_evidence(run, authentic, name, environments, adjustment):
    work = run / 'pages/040/page/work'
    graph_path = work / 'exploration.json'
    graph = core.load(graph_path)
    row, = (row for row in authentic['rows'] if row['page_id'] == '040' and row['checkpoint'] == '2.1.2-02')
    changed = []
    for env in environments:
        verdict, = row['environments'][env]['verdicts']
        path = (run / verdict['evidence']).with_name(name)
        relative = path.relative_to(work).as_posix()
        entry, = (entry for entry in graph['proof'] if entry['path'] == relative)
        original_hash = core.file_hash(path)
        assert original_hash == entry['sha256']
        if adjustment == 'unregister':
            graph['proof'].remove(entry)
        elif adjustment == 'truncate':
            path.write_bytes(b'{')
        elif adjustment == 'remove':
            path.unlink()
        else:
            content = core.load(path)
            with path.open('ab') as stream:
                stream.write(b' ')
            assert core.load(path) == content and core.file_hash(path) != original_hash
        changed.append({'environment': env, 'path': path.relative_to(run).as_posix(),
                        'registered_sha256_before': original_hash,
                        'registered_sha256_after': None if adjustment == 'unregister' else original_hash,
                        'file_sha256_after': core.file_hash(path) if path.is_file() else None})
    if adjustment == 'unregister':
        core.save(graph_path, graph)
    return changed


def verify(output, before, t030_run, vision_run):
    output.mkdir(parents=True)
    original = output / 'original'
    with ZipFile(ARCHIVE) as bundle:
        bundle.extractall(original)
    authentic = score(original)
    assert authentic == previous_score(before, original)
    public_score = core.load(T030 / 'score.json')
    page_ids = {receipt['page_id'] for receipt in authentic['receipts'] if receipt['completed']}
    assert page_ids == {'039', '040', '064', '065'}
    assert [row for row in authentic['rows'] if row['page_id'] in page_ids] == [
        row for row in public_score['rows'] if row['page_id'] in page_ids]
    normal = outcomes(authentic, '039')
    problem = outcomes(authentic, '040')
    assert normal['status'] == 'matched' and normal['verdicts'] == {'desktop': ['passed'], 'narrow': ['passed']}
    assert problem['status'] == 'detected' and problem['verdicts'] == {'desktop': ['failed'], 'narrow': ['failed']}

    scenarios = (
        ('desktop-input', 'input-events.json', ('desktop',), 'whitespace'),
        ('desktop-receipt', 'dialog-focus.json', ('desktop',), 'whitespace'),
        ('desktop-transition', 'transition.json', ('desktop',), 'whitespace'),
        ('both-inputs', 'input-events.json', ('desktop', 'narrow'), 'whitespace'),
        ('desktop-input-unregistered', 'input-events.json', ('desktop',), 'unregister'),
        ('desktop-transition-truncated', 'transition.json', ('desktop',), 'truncate'),
        ('desktop-transition-missing', 'transition.json', ('desktop',), 'remove'),
    )
    changes = []
    for label, filename, environments, adjustment in scenarios:
        variant = output / label
        shutil.copytree(original, variant)
        changed = change_evidence(variant, authentic, filename, environments, adjustment)
        if adjustment in {'truncate', 'remove'}:
            try:
                previous_score(before, variant)
            except subprocess.CalledProcessError as error:
                expected_error = 'JSONDecodeError' if adjustment == 'truncate' else 'FileNotFoundError'
                assert expected_error in error.stderr.decode()
                old = {'error': expected_error}
            else:
                raise AssertionError(f'変更前の採点で {label} のエラーが起きなかった。')
        else:
            old = outcomes(previous_score(before, variant), '040')
            assert old == problem
        revised_score = score(variant)
        revised = outcomes(revised_score, '040')
        reached = problem['reached'].copy()
        if filename == 'transition.json':
            for item in changed:
                env = item['environment']
                dropped = Path(item['path']).with_name('state.json').as_posix()
                reached[env] = [path for path in reached[env] if path != dropped]
        assert revised['reached'] == reached and all(reached.values())
        assert revised['verdicts'] == {env: [] if env in environments else ['failed']
                                       for env in problem['verdicts']}
        assert revised['status'] == ('observed_no_verdict' if len(environments) == 2 else 'detected')
        assert outcomes(revised_score, '039') == normal
        unmatched = [finding['environment'] for finding in revised_score['unmatched_findings']
                     if finding['page_id'] == '040' and finding['checkpoint'] == CHECKPOINT]
        assert sorted(unmatched) == sorted(environments)
        changes.append({'name': label, 'changes': changed, 'before': old, 'after': revised,
                        'unmatched_report_candidates': unmatched})

    full_checks = []
    for run, saved in ((t030_run, T030 / 'score.json'), (vision_run, VISION_SCORE)):
        if run is None:
            continue
        current = score(run)
        assert current == core.load(saved)
        full_checks.append({'score': saved.relative_to(ROOT).as_posix(), 'sha256': core.file_hash(saved),
                            'pages': current['completed_pages'], 'rows': len(current['rows']), 'equal': True})
    core.save(output / 'results.json', {
        'implementation': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'previous_implementation': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=before, text=True).strip(),
        'source_archive': ARCHIVE.relative_to(ROOT).as_posix(), 'source_archive_sha256': core.file_hash(ARCHIVE),
        'authentic_equal': True, 'authentic': {'039': normal, '040': problem}, 'copies': changes,
        'saved_full_runs': full_checks,
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--t030-run', type=Path)
    parser.add_argument('--vision-run', type=Path)
    args = parser.parse_args()
    verify(args.out.resolve(), args.baseline.resolve(), args.t030_run, args.vision_run)
