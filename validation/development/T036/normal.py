"""Collect the two nested-dialog corpus pages through ordinary page-audit."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from benchmarks import core, runner, url_only_machine
from benchmarks.url_only_machine_score import score
from keyboard_checks import matching_keydown

EXPECTED = {
    '045': ('p07.html', ['building', 'inner-name']),
    '046': ('p08.html', ['building', 'inner-close', 'inner-name']),
}
OPEN_BY_CLICK = [{'type': 'click', 'selector': '#launch'}, {'type': 'click', 'selector': '#inner-opener'}]
OPEN_BY_ENTER = [OPEN_BY_CLICK[0], {'type': 'key', 'selector': '#inner-opener', 'key': 'Enter'}]
ESCAPE = {'type': 'press', 'selector': 'body', 'key': 'Escape'}
WIDTHS = ('desktop', 'narrow')


def path_for(output, case):
    return output / 'pages' / case / 'page/work'


def check_normal(output, case):
    work = path_for(output, case)
    graph = core.load(work / 'exploration.json')
    assert graph['steps'] == 24 and graph['limits'] == dict(max_steps=24, max_states=16, max_depth=3)
    pattern = EXPECTED[case][1]
    results = {}
    for env in WIDTHS:
        edges = [edge for edge in graph['edges'] if edge['environment'] == env]
        clicked, = [edge for edge in edges if edge['route'] == OPEN_BY_CLICK]
        keyboard, = [edge for edge in edges if edge['route'] == OPEN_BY_ENTER]
        assert clicked['error'] is keyboard['error'] is None
        assert not any(edge['route'] == OPEN_BY_CLICK + [ESCAPE] for edge in edges)
        assert any(row['route'] == OPEN_BY_CLICK + [ESCAPE] and row['environment'] == env for row in graph['queue'])

        clicked_dir = work / clicked['evidence_dir']
        keyboard_dir = work / keyboard['evidence_dir']
        focus = [item['id'] for item in core.load(clicked_dir / 'keyboard.json')]
        assert focus == pattern * (30 // len(pattern)), focus
        events = core.load(clicked_dir / 'input-events.json')
        assert not events['truncated']
        tabs = [(i, e) for i, e in enumerate(events['events']) if matching_keydown(e, 'Tab')]
        assert len(tabs) == 30
        assert [e['target']['id'] for _, e in tabs] == ['inner-name', *focus[:-1]]

        key_log = core.load(keyboard_dir / 'input-events.json')
        assert not key_log['truncated']
        enter = next(i for i, e in enumerate(key_log['events'])
                     if matching_keydown(e, 'Enter') and e['target']['id'] == 'inner-opener')

        results[env] = dict(click_route=clicked['route'], click_evidence=clicked['evidence_dir'],
                            mixed_route=keyboard['route'], mixed_evidence=keyboard['evidence_dir'],
                            inner_enter_event_index=enter, tab_focus=focus,
                            tab_event_indices=[i for i, _ in tabs], escape_waiting=True)
    return dict(steps=graph['steps'], pending=len(graph['queue']), environments=results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    public = output / 'public'
    public.mkdir(parents=True)
    for page, _ in EXPECTED.values():
        shutil.copyfile(ROOT / 'benchmarks/cases/2.1.2/public' / page, public / page)
    (output / 'pages').mkdir()
    corpus = core.corpus()
    pages = [page for page in url_only_machine.inventory(corpus) if page['id'] in EXPECTED]
    assert {page['id']: page['page'] for page in pages} == {case: value[0] for case, value in EXPECTED.items()}
    core.save(output / 'inventory.json', dict(
        commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        corpus_digest=corpus['digest'], pages=pages, workers=1,
        totals=dict(Counter(row['expected'] for page in pages for row in page['rows'])),
        initial_args=url_only_machine.INITIAL, explore_args=url_only_machine.EXPLORE,
        environment=runner.environment(),
        public_sha256={p.name: core.file_hash(p) for p in sorted(public.iterdir())},
    ))
    server = runner.server(public)
    try:
        for page in pages:
            url_only_machine.collect_page(f'http://127.0.0.1:{server.server_port}/{page["page"]}',
                                          output / 'pages' / page['id'])
    finally:
        server.shutdown()
        server.server_close()
    result = score(output)
    core.save(output / 'score.json', result)
    assert result['completed_pages'] == 2
    assert {item['status'] for item in result['rows']} == {'observed_no_verdict'}
    core.save(output / 'observed.json', {case: check_normal(output, case) for case in EXPECTED})


if __name__ == '__main__':
    main()
