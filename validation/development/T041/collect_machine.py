"""Collect the calendar initial states with the unmodified page-audit command."""

import argparse
from collections import Counter
from pathlib import Path
import subprocess
import sys

from measure_calendar import REPO, digest, load, save, serve


def collect(output):
    output.mkdir(parents=True, exist_ok=False)
    cli = REPO / 'skills/wcag-audit-kit/scripts/audit.py'
    results = {}
    with serve() as origin:
        for case in ('m8d', 'c4p'):
            area = output / case
            url = f'{origin}/{case}/'
            command = [sys.executable, str(cli.relative_to(REPO)), 'page-audit', '--url', url,
                       '--out', str(area), '--level', 'AA', '--mode', 'machine',
                       '--screenshots', 'initial', '--initial-only']
            with (output / f'{case}.log').open('w', encoding='utf-8') as log:
                subprocess.run(command, cwd=REPO, stdout=log, stderr=subprocess.STDOUT, check=True)
            paths = ['data/report.json', 'reports/report.html', 'reports/report.xlsx',
                     'reports/details/issues.md']
            report = load(area / paths[0])
            scope = report['scope_conformance']
            if report['url'] != url or report['level'] != 'AA':
                raise ValueError(f'{case}: 帳票の対象ページまたはレベルが一致しない')
            results[case] = {'url': url, 'command': command,
                             'audit_complete': report['audit_complete'],
                             'scope_status': scope['status'], 'scope_label': scope['label'],
                             'case_outcomes': dict(Counter(row['outcome'] for row in report['cases'])),
                             'files_sha256': {path: digest(area / path) for path in paths}}
            save(output / 'machine.json', results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    collect(parser.parse_args().out.resolve())
