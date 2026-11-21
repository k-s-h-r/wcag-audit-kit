"""Observe a real Escape from the third level of a discovered menu."""
import argparse
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmarks import core, runner, url_only


def verify_case(output, url, status, focus, returned=None):
    assert url_only.collect_page(url, output, ['--quick-explore', '--max-depth', '4', '--max-steps', '32'])
    root = core.audit.run_layout.ledger(output / 'page')
    graph = core.load(root / 'exploration.json')
    report = core.load(core.audit.run_layout.report_files(root, single=True).json)
    edges = [edge for edge in graph['edges'] if edge.get('disclosure_opener') == '#level2']
    assert {edge['environment'] for edge in edges} == {'desktop', 'narrow'}, graph['queue']
    assert len(edges) == 2, edges
    for edge in edges:
        assert edge['error'] is None, edge
        assert [(action['type'], action['selector'], action['key']) for action in edge['route']] == [
            ('key', '#level1', 'Enter'), ('key', '#level2', 'Enter'), ('press', 'body', 'Tab'),
            ('press', 'body', 'Escape'),
        ]
        record = edge['disclosure_close']
        assert record['before']['focus'] == '#leaf' and record['before']['visible'], record
        assert (record['status'], record['after']['focus'], record.get('focus_returned')) == (status, focus, returned)
        directory = root / edge['evidence_dir']
        assert core.load(directory / 'transition.json')['disclosure_close'] == record
        events = core.load(directory / 'input-events.json')['events']
        assert any(event['type'] == 'keydown' and event['key'] == 'Escape' and event['isTrusted']
                   and event['expectedTargetMatched'] and event['target']['id'] == 'leaf' for event in events)
        check, = [row for row in report['machine_checks']
                  if row['criterion'] == '2.4.3' and row['evidence'] == edge['evidence_dir'] + '/transition.json']
        assert check['outcome'] == ('passed' if returned else 'cant_tell'), check
        assert focus in check['observed']


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    public = out / 'public'
    shutil.copytree(core.ROOT / 'benchmarks/cases/2.1.2/public', public)
    original = (public / 'p03.html').read_text()
    (public / 'closing-focus-jump.html').write_text(original.replace('</body>', '''<script>
document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && event.target.closest('#level3-panel')) {
        document.querySelector('#after').focus();
    }
});
</script></body>'''))
    http = runner.server(public)
    try:
        origin = f'http://127.0.0.1:{http.server_port}'
        verify_case(out / 'closed', origin + '/p03.html', 'closed', '#level2', True)
        verify_case(out / 'stayed', origin + '/p04.html', 'stayed_open', '#leaf')
        verify_case(out / 'focus-jump', origin + '/closing-focus-jump.html', 'closed', '#after', False)
    finally:
        http.shutdown()
        http.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
