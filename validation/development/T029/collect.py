"""Find the calendars from both entry URLs and collect a separate audit run for each."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urljoin, urlsplit


def run_cli(cli, log_path, *args):
    cmd = [sys.executable, str(cli), *map(str, args)]
    with log_path.open('x') as log:
        subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)


def collect(cli, out, entries, mode):
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for entry in entries:
        prefix = urlsplit(entry).path.rstrip('/')
        site = out / prefix.rsplit('/', 1)[-1]
        site.mkdir()
        config = site/'config.json'
        run_cli(cli, site/'init.log', 'init', '--url', entry, '--config', config, '--mode', mode)
        settings = json.loads(config.read_text())
        settings['scope'].update(include=[prefix+'/**'], seeds=[prefix+'/'], max_pages=3)
        settings['environments'] = settings['environments'][:1]
        config.write_text(json.dumps(settings, ensure_ascii=False, indent=2)+'\n')
        listing = site/'pages.json'
        run_cli(cli, site/'pages.log', 'pages', '--config', config, '--out', listing)
        pages = json.loads(listing.read_text())
        calendar = urljoin(entry, 'calendar.html')
        assert any(row['url'] == calendar and row['visited'] for row in pages['pages']), pages

        ledger = site/'calendar'
        args = ('page-audit', '--url', calendar, '--out', ledger, '--config', config,
                '--mode', mode, '--level', 'AA', '--screenshots', 'initial',
                '--max-states', 8, '--max-steps', 10, '--max-depth', 1)
        run_cli(cli, site/'initial.log', *args, '--initial-only')
        if mode == 'machine':
            run_cli(cli, site/'exploration.log', *args, '--resume', '--quick-explore')
        report_path = ledger/'data/report.json'
        report = json.loads(report_path.read_text())
        criterion = next(row for row in report['criteria'] if row['id'] == '1.4.1')
        results.append({'entry_url': entry, 'calendar_url': calendar, 'report': str(report_path.relative_to(out)),
                        'mode': mode, 'status': criterion['status'], 'counts': criterion['counts'],
                        'machine_checks': [row for row in report['machine_checks'] if row['criterion'] == '1.4.1']})
    (out/'summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--mode', default='machine', choices=('machine', 'ai'))
    parser.add_argument('entries', nargs=2)
    args = parser.parse_args()
    collect(args.cli, args.out, args.entries, args.mode)
