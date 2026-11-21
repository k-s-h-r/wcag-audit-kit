"""Exercise editable combobox operations through URL-only exploration."""
import argparse
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmarks import core, runner, url_only
from combobox import EXPANSION_CHECK


def verify_case(output, url, expected):
    assert url_only.collect_page(url, output, url_only.PROFILES['quick'])
    root = core.audit.run_layout.ledger(output / 'page')
    graph = core.load(root / 'exploration.json')
    report = core.load(core.audit.run_layout.report_files(root, single=True).json)
    for environment in ('desktop', 'narrow'):
        records = {}
        for edge in graph['edges']:
            receipt = edge.get('combobox')
            if edge['environment'] != environment or not receipt:
                continue
            keys = tuple(step['key'] for step in edge['route'])
            assert all(step['type'] == 'key' and step['selector'] == '#subject' for step in edge['route']), edge
            assert receipt['status'] == 'observed', edge
            records[keys] = receipt
            directory = root / edge['evidence_dir']
            assert receipt == core.load(directory / 'transition.json')['combobox']
            event = core.load(directory / 'input-events.json')['events'][edge['key_effect']['event_index']]
            assert event['key'] == keys[-1] and event['isTrusted'] and event['expectedTargetMatched']
            assert event['target']['id'] == 'subject'
        opened = records[('ArrowDown',)]
        assert not opened['before']['visible'] and opened['after']['visible']
        assert opened['after']['expanded'] == ('true' if expected == 'passed' else 'false')
        moved = records[('ArrowDown', 'ArrowDown')]
        assert moved['after']['visible']
        if expected == 'passed':
            assert opened['after']['active_option'] == '#osaka'
            assert moved['after']['active_option'] == '#tokyo'
        else:
            assert not opened['after']['active_option'] and not moved['after']['active_option']
        for path in (('ArrowDown', 'Enter'), ('ArrowDown', 'ArrowDown', 'Enter'), ('ArrowDown', 'Escape')):
            receipt = records[path]
            assert not receipt['after']['visible'] and receipt['after']['focused']
            assert receipt['value_changed'] is (path[-1] == 'Enter')
        check, = [row for row in report['machine_checks']
                  if row['checkpoint'] == EXPANSION_CHECK and row['environment'] == environment]
        assert check['outcome'] == expected, check
    assert graph['steps'] <= 24


def verify_transparent_popup(output, url):
    assert url_only.collect_page(url, output, url_only.PROFILES['quick'])
    root = core.audit.run_layout.ledger(output / 'page')
    graph = core.load(root / 'exploration.json')
    openings = [edge for edge in graph['edges']
                if edge.get('combobox', {}).get('key') == 'ArrowDown' and len(edge['route']) == 1]
    assert {edge['environment'] for edge in openings} == {'desktop', 'narrow'}
    assert all(edge['combobox']['status'] == 'observed' and not edge['combobox']['after']['visible']
               and not edge['combobox'].get('followups') for edge in openings), openings
    report = core.load(core.audit.run_layout.report_files(root, single=True).json)
    assert not any(row['checkpoint'] == EXPANSION_CHECK for row in report['machine_checks'])


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    public = out / 'public'
    shutil.copytree(core.ROOT / 'benchmarks/cases/4.1.2/public', public)
    original = (public / 'p07.html').read_text()
    (public / 'transparent.html').write_text(original.replace('</head>', '<style>#options{opacity:0}</style></head>'))
    http = runner.server(public)
    try:
        origin = f'http://127.0.0.1:{http.server_port}'
        verify_case(out / 'missing-expansion', origin + '/p07.html', 'failed')
        verify_case(out / 'valid', origin + '/p08.html', 'passed')
        verify_transparent_popup(out / 'transparent', origin + '/transparent.html')
    finally:
        http.shutdown()
        http.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
