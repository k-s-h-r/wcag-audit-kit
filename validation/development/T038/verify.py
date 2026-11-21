"""Check the records and report links from the normal nested and single-dialog runs."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import unquote

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from benchmarks import core
from keyboard_checks import matching_keydown

WIDTHS = {'desktop', 'narrow'}
PATH = [{'type': 'click', 'selector': '#launch'}, {'type': 'click', 'selector': '#inner-opener'},
        {'type': 'press', 'selector': 'body', 'key': 'Escape'}]
EXPECTED = {'045': ('child_open', ['#outer', '#subject'], '#inner-name', 'child', '子が表示されたまま'),
            '046': ('child_closed', ['#outer'], '#inner-opener', 'parent', '子だけ閉じた')}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()

    def handle_starttag(self, tag, attributes):
        if tag == 'a':
            href = dict(attributes).get('href')
            if href:
                self.paths.add(href)


def trusted_escape(work, edge, index):
    raw = core.load(work / edge['evidence_dir'] / 'input-events.json')
    assert not raw['truncated'] and 0 <= index < len(raw['events'])
    event = raw['events'][index]
    assert matching_keydown(event, 'Escape') and event['target']['id'] == 'inner-name', event
    return event


def check_nested(output, case, updated):
    page = output / 'pages' / case / 'page'
    work = page / 'work'
    phase = core.load(page.parent / 'collection.json')
    expected_phases = {'initial': 0, 'explore': 0}
    if not updated and phase['phases'] == {'initial': 0, 'explore': 'timeout'}:
        assert core.load(page.parent / 'report-regeneration.json')['exit'] == 0
    else:
        assert phase['phases'] == expected_phases
    graph = core.load(work / 'exploration.json')
    assert graph['limits'] == dict(max_steps=64, max_states=16, max_depth=3)
    report = core.load(page / 'data/report.json')
    assert report['exploration']['deferred'] is False
    assert {r['id']: r['status'] for r in report['criteria'] if r['id'] in {'2.1.2', '2.4.3'}} == {
        '2.1.2': 'unverified', '2.4.3': 'unverified'}
    results = {}
    paths = set()
    expected_status, modals, focus, layer, display = EXPECTED[case]
    for i, edge in enumerate(graph['edges'], 1):
        if edge['route'] != PATH:
            assert not edge.get('nested_dialog_evidence'), edge
            continue
        assert not edge['error'] and not edge['blocked_requests'] and not edge['native_events']
        directory = work / edge['evidence_dir']
        original = core.load(directory / 'dialog-focus.json')
        before, after = original['before_escape'], original['after_escape']
        assert before['modals'] == ['#outer', '#subject'] and before['focus'] == '#inner-name'
        assert after['modals'] == modals and after['focus'] == focus
        assert before['document_start'] == after['document_start'] and before['url'] == after['url']
        assert original['status'] == 'unconfirmed'
        event = trusted_escape(work, edge, original['escape_event_index'] - 1)
        assert event['url'] == before['url']
        outcome = dict(step=i, target=event['target']['id'], legacy_status=original['status'],
                       observed_modals=after['modals'], focus=focus)
        if updated:
            path = work / edge['nested_dialog_evidence']
            receipt = core.load(path)
            assert path == directory / 'nested-dialog.json' and receipt['key'] == 'Escape'
            assert receipt['before'] == before and receipt['after'] == after
            assert receipt['parent'] == '#outer' and receipt['child'] == '#subject'
            assert receipt['focus_layer'] == layer and receipt['status'] == expected_status
            assert receipt['event_index'] == original['escape_event_index'] - 1
            assert receipt['input_evidence'] == 'input-events.json' and event['expectedTargetMatched'] is True
            row, = [row for row in report['exploration']['dialog_observations']
                    if row['environment'] == edge['environment']]
            assert row['route'] == PATH and row['status'] == expected_status and row['focus_layer'] == layer
            assert (work / row['evidence']) == path and (work / row['input_evidence']) == directory/'input-events.json'
            assert row['focus'] == focus and row['event_index'] == receipt['event_index']
            assert 'criterion' not in row and 'outcome' not in row and not any(
                m['evidence'] == row['evidence'] for m in report['machine_checks'])
            paths.add(path.resolve())
            paths.add((directory/'input-events.json').resolve())
            outcome.update(receipt=row['evidence'], input_evidence=row['input_evidence'], status=expected_status,
                           focus_layer=layer)
        else:
            assert not edge.get('nested_dialog_evidence')
            assert 'dialog_observations' not in report['exploration']
        results[edge['environment']] = outcome
    assert set(results) == WIDTHS
    if updated:
        report_dir = page/'reports'
        html = (report_dir/'report.html').read_text()
        parser = Links()
        parser.feed(html)
        targets = {(report_dir / unquote(link)).resolve() for link in parser.paths if link.startswith('../')}
        assert paths <= targets and html.count('開閉とフォーカスの記録') == 2
        book = load_workbook(report_dir/'report.xlsx')
        try:
            observations = book['操作調査']
            rows = [row for row in list(observations.rows)[1:] if row[10].hyperlink]
            assert len(rows) == 2
            assert all(row[5].value == display and focus in row[6].value for row in rows)
            assert {(report_dir / unquote(row[10].hyperlink.target)).resolve() for row in rows} == {
                path for path in paths if path.name == 'nested-dialog.json'}
        finally:
            book.close()
    return dict(ran=graph['steps'], pending=len(graph['queue']), environments=results)


def check_single(output, case):
    page = output/'pages'/case/'page'
    assert core.load(page.parent/'collection.json')['phases'] == {'initial': 0, 'explore': 0}
    work = page/'work'
    graph = core.load(work/'exploration.json')
    report = core.load(page/'data/report.json')
    assert 'dialog_observations' not in report['exploration']
    assert not any('nested_dialog_evidence' in e for e in graph['edges'])
    expected = 'passed' if case == '039' else 'failed'
    rows = {(r['environment'], r['outcome']) for r in report['machine_checks']
            if r['checkpoint'] == 'ダイアログからのキー操作による離脱'}
    assert rows == {(width, expected) for width in WIDTHS}, rows
    return dict(ran=graph['steps'], outcome={width: expected for width in WIDTHS})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--version', required=True, choices=('baseline', 'updated', 'single'))
    args = parser.parse_args()
    found = ({case: check_single(args.output, case) for case in ('039', '040')} if args.version == 'single'
             else {case: check_nested(args.output, case, args.version == 'updated') for case in EXPECTED})
    core.save(args.output / 'observed.json', found)
    print('Verified:', ', '.join(found))
