"""Continue two local page audits from their initial work packets."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / 'skills/wcag-page/scripts/audit.py'
FIXTURES = ROOT / 'benchmarks/cases/2.1.2/public'
CHECKPOINT = 'ダイアログからのキー操作による離脱'


class QuietHTTP(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def invoke(cli, output, *arguments):
    with output.open('w') as log:
        subprocess.run([sys.executable, str(cli), *map(str, arguments)], stdout=log,
                       stderr=subprocess.STDOUT, timeout=180, check=True)
    if arguments[0] == 'page-next':
        return json.loads(output.read_text())


def trap_packets(packet):
    return [(case, row) for case in packet['next_cases'] for row in case['machine_results']
            if row['checkpoint'] == CHECKPOINT]


def verify(out, baseline_cli, port, filename, expected):
    location = out / filename
    location.mkdir()
    run = location / 'page'
    url = f'http://127.0.0.1:{port}/{filename}'
    audit = ['page-audit', '--url', url, '--out', run]
    next_work = ['page-next', '--run', run, '--page-exact', url]
    invoke(CLI, location / 'initial.log', *audit, '--initial-only', '--mode', 'machine',
           '--screenshots', 'initial')
    initial = invoke(CLI, location / 'next-initial.json', *next_work)
    assert not trap_packets(initial), filename
    assert initial['exploration']['next'] == 'page-audit --resume --quick-explore', filename
    invoke(CLI, location / 'explore.log', *audit, '--resume', '--quick-explore')
    resumed = invoke(CLI, location / 'next-explored.json', *next_work)
    baseline = None
    if baseline_cli:
        baseline = invoke(baseline_cli, location / 'next-older-reader.json', *next_work)
        assert not trap_packets(baseline), filename
        for key in ('machine_checks', 'remaining_cases', 'mode_actionable_cases', 'mode_unavailable_count'):
            assert resumed[key] == baseline[key], (filename, key)
    assert len(resumed['next_cases']) == 5 and not resumed['audit_complete'], filename

    captured = []
    for case, row in trap_packets(resumed):
        assert case['criterion'] == '2.1.2' and case['page_url'] == url and case['state'] != 'initial', case
        assert case['outcome'] == 'not_run' and case['assessment_data'] is None, case
        assert row['outcome'] == expected and row['case_capture'] == case['capture'], row
        assert row['environment'] == case['environment'] and row['page_url'] == case['page_url'], row
        assert [action['key'] for action in row['operation_route']] == ['Enter', 'Escape'], row
        work = Path(resumed['evidence_base'])
        assert all((work / evidence).is_file() for evidence in [row['evidence'], *row['proof']]), row
        assert (work / case['evidence_dir'] / 'state.json').relative_to(work).as_posix() in row['proof'], row
        captured.append({'case_id': case['case_id'], 'capture': case['capture'], 'case_outcome': case['outcome'],
                         'row': row})
    assert [row['row']['environment'] for row in captured] == ['desktop', 'narrow'], captured
    return {'fixture': filename, 'url': url, 'initial_next': initial['exploration']['next'],
            'before_exploring_rows': len(trap_packets(initial)),
            'older_reader_rows': len(trap_packets(baseline)) if baseline is not None else None,
            'machine_counts': resumed['machine_checks'], 'audit_complete': resumed['audit_complete'],
            'packets': captured}


def main(out, baseline_cli):
    out.mkdir(parents=True)
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHTTP, directory=str(FIXTURES))) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            results = [verify(out, baseline_cli, server.server_port, filename, expected)
                       for filename, expected in [('p01.html', 'passed'), ('p02.html', 'failed')]]
        finally:
            server.shutdown()
            thread.join()
    (out / 'summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--baseline-cli', type=Path, help='optional T030 audit.py for an older-reader comparison')
    args = parser.parse_args()
    main(args.out.resolve(), args.baseline_cli.resolve() if args.baseline_cli else None)
