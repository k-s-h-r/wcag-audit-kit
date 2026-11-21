#!/usr/bin/env python3
"""Repeat URL-only page-audit on the frozen corpus and loopback controls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import threading

HERE = Path(__file__).resolve().parent
WIDTHS = ('desktop', 'narrow')
FOCUS_DOCUMENT = {'focus-c01', '073'}


def competing_frame(name, navigation_action):
    return f"""
        <label>氏名<input id="subject" onfocus="location.href='{name}-target.html'"></label>
        <iframe id="inner" title="追加案内" hidden
          sandbox="allow-scripts allow-top-navigation"
          srcdoc="<script>onmessage=event=>top.location.href=event.data</script>"></iframe>
        <script>
        navigation.addEventListener('navigate', event => {navigation_action}, {{once: true}});
        addEventListener('keyup', event => {{
            if (event.key === 'Tab') {{
                document.getElementById('inner').contentWindow.postMessage(
                    new URL('{name}-target.html', location.href).href, '*');
            }}
        }}, {{once: true}});
        </script>"""


CONTROLS = {
    'activation': '<button type="button" id="subject" onclick="location.href=\'activation-target.html\'">案内を見る</button>',
    'timer': """
        <label>氏名<input id="subject"></label><script>
        addEventListener('keydown', event => {
            if (event.key === 'Tab') setTimeout(() => location.href='timer-target.html', 0);
        }, {once: true});
        </script>""",
    'cancel-keyup': """
        <label>氏名<input id="subject" onfocus="tryOnFocus()"></label><script>
        let tabDown = false, attempted = false, retryOnKeyup = false;
        addEventListener('keydown', event => { tabDown = event.key === 'Tab'; });
        function tryOnFocus() {
            if (!tabDown || attempted) return;
            attempted = retryOnKeyup = true;
            location.href = 'cancel-keyup-target.html';
        }
        navigation.addEventListener('navigate', event => event.preventDefault(), {once: true});
        addEventListener('keyup', event => {
            tabDown = false;
            if (event.key !== 'Tab' || !retryOnKeyup) return;
            retryOnKeyup = false;
            location.href = 'cancel-keyup-target.html';
        });
        </script>""",
    'hash': '<label>氏名<input id="subject" onfocus="location.hash=\'more\'"></label><p id="more">次の案内</p>',
    'cancel-frame': competing_frame('cancel-frame', 'event.preventDefault()'),
    'intercept-frame': competing_frame('intercept-frame', 'event.intercept({handler: () => new Promise(() => {})})'),
    'iframe': """
        <label>氏名<input id="subject" onfocus="document.getElementById('inner').src='iframe-target.html'"></label>
        <iframe title="追加案内" id="inner" tabindex="-1" hidden></iframe>""",
    'background': '<label>氏名<input id="subject" onfocus="fetch(\'background-target.html\', {method: \'POST\'})"></label>',
}
CASES = {
    '071': '3.1.1/p01.html',
    '072': '3.1.1/p02.html',
    '073': '3.2.1/p03.html',
    '074': '3.2.1/p04.html',
    'focus-c01': '3.2.1/p01.html',
    'focus-c02': '3.2.1/p02.html',
    **{name: f'controls/{name}.html' for name in CONTROLS},
}


def read(path):
    return json.loads(path.read_text())


def collect_evidence(output, name, expected):
    run = output / 'pages' / name
    assert read(run / 'collection.json')['phases'] == {'initial': 0, 'explore': 0}, name
    work = run / 'page/work'
    graph = read(work / 'exploration.json')
    report = read(run / 'page/data/report.json')
    assert next(criterion['status'] for criterion in report['criteria'] if criterion['id'] == '3.2.1') == 'unverified'
    assert not any(check['criterion'] == '3.2.1' and check['outcome'] in {'passed', 'failed', 'inapplicable'}
                   for check in report['machine_checks']), name
    if name in {'071', '072'}:
        expected_outcome = 'failed' if name == '071' else 'passed'
        for env in WIDTHS:
            assert {row['outcome'] for row in report['machine_checks']
                    if row['checkpoint'] == 'axe / html-has-lang' and row['environment'] == env} == {expected_outcome}, name
    summary = {}
    for env in WIDTHS:
        edges = [edge for edge in graph['edges'] if edge['environment'] == env]
        trace_stops, all_blocks, matched, nav_attempts = [], [], [], []
        enter_blocked = False
        for edge in edges:
            directory = work / edge['evidence_dir']
            path = directory / 'keyboard-trace-stop.json'
            input_path = directory / 'input-events.json'
            all_blocks.extend(edge['blocked_requests'])
            if input_path.is_file():
                log = read(input_path)
                nav_attempts.extend(row for row in log['events'] if row['type'] == 'navigate')
                if name == 'activation' and edge['route'] and edge['route'][-1].get('key') == 'Enter':
                    enter_blocked |= (any(row['url'].endswith('/activation-target.html') for row in edge['blocked_requests'])
                                      and any(row['type'] == 'keydown' and row.get('key') == 'Enter' and row['isTrusted']
                                              for row in log['events']))
            if not path.is_file():
                continue
            stop = read(path)
            trace_stops.append(path.relative_to(output).as_posix())
            if not (receipt := stop.get('focus_navigation')):
                continue
            assert not edge['route'] and stop['step'] == 1 and receipt['status'] == 'blocked'
            assert not log['truncated'] and not stop['native_events'] and not stop['child_frame_observed']
            key, focus, nav, keyup = (log['events'][receipt[field]] for field in
                                      ('keydown_event_index', 'focus_event_index',
                                       'navigation_event_index', 'keyup_event_index'))
            block = stop['blocked_requests'][receipt['blocked_request_index']]
            assert [key['type'], focus['type'], nav['type'], keyup['type']] == ['keydown', 'focus', 'navigate', 'keyup']
            assert key['key'] == keyup['key'] == 'Tab' and not any(key['modifiers'].values())
            assert all(event['isTrusted'] and event['is_main_frame'] and event['url'] == receipt['source_url']
                       and event['documentId'] == key['documentId'] for event in (key, focus, nav, keyup))
            assert keyup['navigationAtKeyup'] == {'id': nav['navigationId'], 'dispatchEnded': True,
                                                  'canceled': False, 'aborted': False}
            assert focus['target'] == nav['target'] == receipt['target'] == {'tag': 'input', 'id': 'subject'}
            assert nav['focusDispatchPhase'] == 2 and not nav['sameDocument'] and not nav['hashChange']
            assert receipt['destination'] == nav['destination'] == block['url']
            assert block['method'] == 'GET' and block['reason'] == 'navigation_out_of_scope'
            assert block['resource_type'] == 'document' and block['is_main_frame']
            assert receipt['input_evidence'] == input_path.name
            assert any(path.relative_to(work).as_posix() in note and '#subject' in note and '通信を遮断' in note
                       for note in report['exploration']['remaining'])
            html = (run / 'page/reports/report.html').read_text()
            assert '通信を遮断したため移動先の表示は未確認' in html and path.relative_to(work).as_posix() in html
            matched.append(receipt)
        assert bool(matched) == (expected == 'after' and name in FOCUS_DOCUMENT), (name, env, matched)
        if name in FOCUS_DOCUMENT:
            assert any(row['url'].endswith('/details.html') for row in all_blocks), (name, env)
        if expected == 'after' and name in {'activation', 'timer', 'cancel-keyup', 'iframe',
                                            'background', 'cancel-frame', 'intercept-frame'}:
            relevant = [row for row in all_blocks if row['url'].endswith(f'/{name}-target.html')]
            assert relevant, (name, env)
            if name == 'iframe':
                assert all(row.get('is_main_frame') is False and row['resource_type'] == 'document'
                           for row in relevant), relevant
            elif name == 'background':
                assert all('is_main_frame' not in row and row['resource_type'] == 'fetch'
                           and row['method'] == 'POST' for row in relevant), relevant
            else:
                assert all(row.get('is_main_frame') is True for row in relevant), relevant
            if name == 'iframe' or name.endswith('-frame'):
                assert any(read(output / path)['child_frame_observed'] for path in trace_stops), name
        if expected == 'after' and name == 'hash':
            assert any(row['sameDocument'] and row['hashChange'] and row['destination'].endswith('#more')
                       for row in nav_attempts), env
        if expected == 'after' and name == 'activation':
            assert enter_blocked, env
        if expected == 'after' and name == 'cancel-keyup':
            phases = [row['focusDispatchPhase'] for row in nav_attempts
                      if row['destination'].endswith('/cancel-keyup-target.html')]
            assert phases and len(phases) % 2 == 0 and phases == [2, 0] * (len(phases) // 2), (env, phases)
        summary[env] = dict(matched=matched, trace_stops=trace_stops, blocked_requests=all_blocks,
                            navigation_events=nav_attempts)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=HERE.parents[2])
    parser.add_argument('--expect', choices=('before', 'after'), default='after')
    parser.add_argument('--case', action='append', choices=CASES)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo.resolve()))
    from benchmarks import core, runner, url_only_machine

    output = args.out.resolve()
    pages = output / 'pages'
    pages.mkdir(parents=True)
    public = output / 'public'
    for criterion in ('3.1.1', '3.2.1'):
        shutil.copytree(args.repo / f'benchmarks/cases/{criterion}/public', public / criterion)
    controls = public / 'controls'
    controls.mkdir()
    for name, body in CONTROLS.items():
        markup = '<!doctype html><html lang="ja"><meta charset="utf-8"><title>利用案内</title><main><h1>利用案内</h1>'
        (controls / f'{name}.html').write_text(markup + body + '</main>', encoding='utf-8')
        if name != 'hash':
            (controls / f'{name}-target.html').write_text(markup + '<p>移動先</p></main>', encoding='utf-8')

    received = []
    class LoggedFixtures(runner.PublicFiles):
        def log_request(self, status, size=None):
            received.append(dict(method=self.command, path=self.path, status=str(status)))

        def do_POST(self):
            self.send_error(405)

    with ThreadingHTTPServer(('127.0.0.1', 0), partial(LoggedFixtures, directory=str(public))) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            selected = args.case or list(CASES)
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                jobs = [pool.submit(url_only_machine.collect_page,
                                    f'http://127.0.0.1:{server.server_port}/{CASES[name]}', pages / name)
                        for name in selected]
                for job in jobs:
                    job.result()
        finally:
            server.shutdown()
            thread.join()
    core.save(output / 'server-requests.json', received)
    assert not any(row['path'].endswith(('/details.html', '-target.html')) for row in received), received
    summary = {name: collect_evidence(output, name, args.expect) for name in selected}
    core.save(output / 'summary.json', dict(environment=runner.environment(), cases=summary))
    print('Verified:', ', '.join(summary))


if __name__ == '__main__':
    main()
