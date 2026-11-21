"""Run ordinary page-audit with a larger step limit on fixed loopback fixtures."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from benchmarks import core, runner, url_only_machine

CASES = {'039': 'p01.html', '040': 'p02.html', '045': 'p07.html', '046': 'p08.html'}


def collect_page(url, output, explore_args):
    output.mkdir()
    base = [sys.executable, str(url_only_machine.CLI), 'page-audit', '--url', url, '--out', str(output/'page')]
    phases = {}
    for phase, flags in [('initial', url_only_machine.INITIAL), ('explore', explore_args)]:
        command = base + list(flags)
        with (output/(phase+'.log')).open('w') as log:
            print(json.dumps(command), file=log, flush=True)
            try:
                phases[phase] = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                               timeout=600, check=False).returncode
            except subprocess.TimeoutExpired:
                phases[phase] = 'timeout'
        if phases[phase] != 0:
            break
    core.save(output/'collection.json', dict(url=url, phases=phases))
    print(output.name, phases, flush=True)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--steps', type=int, default=64)
parser.add_argument('--case', choices=CASES, action='append')
args = parser.parse_args()
selected = args.case or ['045', '046']
out = args.out.resolve()
public = out/'public'
public.mkdir(parents=True)
(out/'pages').mkdir()
for case in selected:
    shutil.copyfile(core.ROOT/'benchmarks/cases/2.1.2/public'/CASES[case],public/CASES[case])
explore_args = url_only_machine.EXPLORE + ('--max-steps', str(args.steps))
core.save(out/'plan.json',dict(
    revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    fixtures={case: dict(page=CASES[case],sha256=core.file_hash(public/CASES[case])) for case in selected},
    initial_args=url_only_machine.INITIAL, explore_args=explore_args, process_timeout_seconds=600,
    environment=runner.environment(),
))
server=runner.server(public)
try:
    for case in selected:
        collect_page(f'http://127.0.0.1:{server.server_port}/{CASES[case]}',out/'pages'/case,explore_args)
finally:
    server.shutdown()
    server.server_close()
