"""Build the checksheet and issue list from actual process observations."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit


def command(cli, *args):
    process = subprocess.run([sys.executable, str(cli), *map(str, args)], check=True,
                             text=True, capture_output=True)
    return process.stdout.strip()


def build_run(cli, destination, case_log, proof):
    destination.mkdir(parents=True, exist_ok=False)
    report = destination / 'report'
    config = destination / 'config.json'
    entry = case_log['start_url']
    command(cli, 'init', '--url', entry, '--mode', 'ai', '--config', config)
    setup = json.loads(config.read_text())
    scope = setup['scope']
    urls = list(dict.fromkeys(case_log['urls']))
    scope.update(mode='configured', pages=urls, known_pages=[], max_pages=len(urls))
    setup['environments'] = [env for env in setup['environments'] if env['id'] == 'desktop']
    setup['inspection']['screenshots'] = 'initial'
    config.write_text(json.dumps(setup, ensure_ascii=False, indent=2) + '\n')
    command(cli, 'start', '--config', config, '--out', report)
    work = report / 'work'
    plan = json.loads((work / 'plan.json').read_text())
    grouped = defaultdict(list)
    for observation in case_log['findings']:
        if observation['criterion'] != 'process':
            grouped[observation['page_url'], observation['criterion']].append(observation)
    for (page_url, criterion), observations in grouped.items():
        case = next(case for case in plan['cases']
                    if case['criterion'] == criterion
                    and case['state'] == 'initial'
                    and urlsplit(case['page_url']).path == urlsplit(page_url).path)
        packet = json.loads(command(cli, 'case', '--run', report, '--id', case['case_id']))
        trace = command(cli, 'attach', '--run', report, '--case', case['case_id'], '--file', proof)
        targets = []
        for observation in observations:
            files = dict.fromkeys(
                name for action in case_log['actions'] for name in action['evidence'].values()
                if name in observation['observed']
            )
            evidence = [trace, *(command(cli, 'attach', '--run', report, '--case', case['case_id'],
                                         '--file', proof.parent / name) for name in files)]
            targets.append(dict(target=observation['target'], observed=observation['observed'],
                                expected=observation['expected'], outcome=observation['outcome'], evidence=evidence))
        failed = any(target['outcome'] == 'failed' for target in targets)
        record = dict(
            case_id=case['case_id'], config_digest=packet['config_digest'],
            normative_sha256=packet['criterion']['normative_sha256'], execution='completed',
            outcome='failed' if failed else 'cant_tell', coverage_complete=False,
            conditions_reviewed=True, exceptions_reviewed=True,
            observed='\n'.join(observation['observed'] for observation in observations),
            steps_executed=list(dict.fromkeys(step for observation in observations for step in observation['steps'])),
            tests_applied=['T022-process-' + criterion], targets=targets,
            evidence=[trace], remaining=['試した手続き以外の機能・表示環境は未確認。'],
        )
        record_path = destination / (case['case_id'] + '.json')
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        command(cli, 'record', '--run', report, '--file', record_path)
    command(cli, 'report', '--run', report)
    command(cli, 'excel', 'export', '--run', report, '--mode', 'report', '--out', report / 'reports/report.xlsx')
    result = json.loads((report / 'data/report.json').read_text())
    print(entry, result['scope_conformance']['status'], result['audit_complete'], flush=True)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cli', type=Path, required=True)
parser.add_argument('--observations', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
data = json.loads(args.observations.read_text())
for index, case in enumerate(data['cases'], 1):
    build_run(args.cli, args.out / str(index), case, args.observations)
