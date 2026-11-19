"""Keep generated reports separate from the ledger and its run-relative evidence."""
from dataclasses import dataclass
from os.path import relpath
from pathlib import Path
from urllib.parse import quote


WORK = 'work'
MARKER = '.audit-work'


def ledger(path):
    path = Path(path)
    internal = path / WORK
    return internal if not (path / 'run.json').is_file() and (internal / MARKER).is_file() else path


def create(path):
    path = Path(path)
    if path.exists() and any(path.iterdir()):
        raise ValueError('出力先は空にする。既存結果はpending/reportで再開する')
    internal = path / WORK
    internal.mkdir(parents=True, exist_ok=False)
    (internal / MARKER).touch()
    return internal


def organized(run):
    return run.name == WORK and (run / MARKER).is_file()


def href(file, target):
    return quote(Path(relpath(target, file.parent)).as_posix(), safe='/')


@dataclass(frozen=True)
class ReportFiles:
    html: Path
    json: Path
    excel: Path
    issues: Path
    handoff: Path
    interactions: Path


def report_files(run, page_id=None, *, single=False):
    if organized(run):
        relative = Path('pages') / page_id if page_id and not single else Path()
        reports = run.parent / 'reports' / relative
        data = run.parent / 'data' / relative
        details = reports / 'details'
        return ReportFiles(reports / 'report.html', data / 'report.json',
                           reports / 'report.xlsx', details / 'issues.md',
                           details / 'human-review.md', details / 'interaction-review.md')
    prefix = f'page-{page_id}-' if page_id else ''
    return ReportFiles(*(run / (prefix + name) for name in (
        'report.html', 'report.json', 'report.xlsx', 'issues.md',
        'human-review.md', 'interaction-review.md')))
