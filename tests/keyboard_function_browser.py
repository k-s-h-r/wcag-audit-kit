"""Exercise all three numeric-output cases through the ordinary page audit."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmarks import core, runner, url_only_machine
from keyboard_function import CHECKPOINT


def verify(output):
    expectations = {
        1: ('#control', 'passed', ['#control']),
        2: ('#control', 'failed', ['#control', '#control']),
        3: ('#pointer', 'passed', ['#control']),
    }
    for index, (pointer, outcome, keyboard) in expectations.items():
        location = output / str(index) / 'page'
        work = core.audit.run_layout.ledger(location)
        report = core.load(location / 'data/report.json')
        checks = [row for row in report['machine_checks']
                  if row['checkpoint'] == CHECKPOINT and row['target'] == pointer]
        assert {row['environment'] for row in checks} == {'desktop', 'narrow'}, checks
        for row in checks:
            assert row['outcome'] == outcome and row['function_result']['keyboard_targets'] == keyboard, row
            transitions = [core.load(work / path) for path in [row['evidence'], *row['proof']]]
            receipts = [transition['function_result'] for transition in transitions]
            assert all(receipt['confirmed'] and receipt['before']['value'] == '0' for receipt in receipts), receipts
            assert receipts[0]['after']['value'] == '1', receipts
            assert all(receipt['after']['value'] == ('0' if outcome == 'failed' else '1')
                       for receipt in receipts[1:]), receipts


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    http = runner.server(core.ROOT / 'benchmarks/cases/2.1.1/public')
    try:
        for index in range(1, 4):
            url = f'http://127.0.0.1:{http.server_port}/p0{index}.html'
            url_only_machine.collect_page(url, output / str(index))
    finally:
        http.shutdown()
        http.server_close()
    verify(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out.resolve())
