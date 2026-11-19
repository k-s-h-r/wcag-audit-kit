"""Exercise same-origin iframe routes through the page-audit CLI in Chromium."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import shutil
import threading

from openpyxl import load_workbook

from keyboard_checks_browser import ROOT, audit, execute, route


FRAME = '#subject'


def exit_plan(base, document):
    return route('2.1.2', 'iframe-escape', 'iframe内からEscapeで起点へ戻る', [
        dict(key='Tab', focus='#launch'),
        dict(key='Enter', focus='#launch', visible=FRAME),
        dict(key='Tab', frame=FRAME, focus='#frame-first'),
        dict(key='Tab', input_frame=FRAME, frame=FRAME, focus='#frame-last'),
        dict(key='Escape', input_frame=FRAME, focus='#launch', hidden=FRAME),
        dict(key='Tab', focus='#after'),
    ], frame={'selector': FRAME, 'url': f'{base}/{document}'})


def read_result(run):
    report = audit.run_layout.report_files(audit.run_layout.ledger(run), single=True).json
    value = audit.load(report)
    row, = [r for r in value['machine_checks'] if r['checkpoint'] == 'キーボード経路 / iframe-escape']
    evidence = run / row['evidence']
    proof = audit.load(evidence)
    events = audit.load(evidence.with_name('input-events.json'))['events']
    blocked = audit.load(evidence.with_name('transition.json'))['blocked_requests']
    assert not value['audit_complete']
    assert all(case['outcome'] == 'not_run' for case in value['cases'])
    return report, row, proof, events, blocked


class Handler(SimpleHTTPRequestHandler):
    requests = Counter()

    def log_message(self, *args):
        pass

    def do_GET(self):
        type(self).requests[('GET', self.path)] += 1
        super().do_GET()

    def do_POST(self):
        type(self).requests[('POST', self.path)] += 1
        self.send_error(500)


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    public = out / 'public'
    shutil.copytree(ROOT / 'benchmarks/cases/2.1.2/public', public)
    source = (public / 'p12.html').read_text()
    for name, document, injection in (
        ('undeclared', 'unlisted.html', ''),
        ('duplicate', 'duplicate-target.html', ''),
        ('sandbox', 'sandbox-target.html', 'f.setAttribute("sandbox","allow-scripts");'),
    ):
        trial = source.replace('frame-content-b.html', document).replace('f.src=', injection + 'f.src=')
        if name == 'duplicate':
            trial = trial.replace('slot.replaceChildren(f)',
                                  'slot.replaceChildren(f,Object.assign(document.createElement("iframe"),{id:"subject"}))')
        (public / f'{name}.html').write_text(trial)
        shutil.copyfile(public / 'frame-content-b.html', public / document)
    (public / 'write-source.html').write_text(source.replace('frame-content-b.html', 'write-target.html'))
    (public / 'write-target.html').write_text((public / 'frame-content-b.html').read_text().replace(
        'e.preventDefault();parent.postMessage', "e.preventDefault();fetch('/unexpected-write',{method:'POST'}).catch(()=>{});return;parent.postMessage"))

    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(public)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    foreign_server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(public)))
    foreign_thread = threading.Thread(target=foreign_server.serve_forever, daemon=True)
    foreign_thread.start()
    foreign_url = f'http://127.0.0.1:{foreign_server.server_port}/cross-target.html'
    (public / 'cross-source.html').write_text(source.replace('frame-content-b.html', foreign_url))
    shutil.copyfile(public / 'frame-content-b.html', public / 'cross-target.html')
    base = f'http://127.0.0.1:{server.server_port}'

    def fixture(name, page, target, expected):
        run = execute(out / name, f'{base}/{page}', [exit_plan(base, target)])
        report, row, proof, events, blocked = read_result(run)
        assert row['outcome'] == proof['outcome'] == expected, (page, row, proof, blocked)
        if expected in {'failed', 'passed'}:
            assert not blocked
            step = proof['steps'][4]
            event = events[step['input_event_index'] - 1]
            assert event['type'] == 'keydown' and event['key'] == 'Escape' and event['isTrusted']
            assert event['url'] == step['before']['frameUrl'] == f'{base}/{target}'
            assert not event['is_main_frame'] and event['target']['id'] == 'frame-last'
            assert step['before']['frame'] == FRAME and step['before']['id'] == 'frame-last'
            if expected == 'passed':
                assert step['after']['id'] == 'launch' and 'frame' not in step['after']
                assert proof['steps'][-1]['after']['id'] == 'after'
            else:
                assert step['after']['frame'] == FRAME and step['after']['id'] == 'frame-last'
                assert row['target'] == '#subject → #frame-last'
                assert '5手順目の Escape' in row['observed']
                html = audit.run_layout.report_files(audit.run_layout.ledger(run), single=True).html.read_text()
                matches = [part for part in re.findall(r'<tr>(.*?)</tr>', html, re.S)
                           if f'href="{audit.run_layout.href(audit.run_layout.report_files(run, single=True).html, run / row["evidence"])}"' in part]
                assert len(matches) == 1 and row['target'] in matches[0]
                book = load_workbook(audit.run_layout.report_files(audit.run_layout.ledger(run), single=True).excel, read_only=True, data_only=True)
                try:
                    assert any(row['evidence'] in cells and row['target'] in cells and row['observed'] in cells
                               for cells in book['自動検出した問題'].values)
                finally:
                    book.close()
        return dict(name=name, outcome=expected, blocked=blocked)

    try:
        cases = [
            ('trap', 'p11.html', 'frame-content-a.html', 'failed'),
            ('return', 'p12.html', 'frame-content-b.html', 'passed'),
            ('undeclared-document', 'undeclared.html', 'frame-content-b.html', 'cant_tell'),
            ('ambiguous-selector', 'duplicate.html', 'duplicate-target.html', 'cant_tell'),
            ('opaque-origin', 'sandbox.html', 'sandbox-target.html', 'cant_tell'),
            ('foreign-origin', 'cross-source.html', 'frame-content-b.html', 'cant_tell'),
            ('blocked-write', 'write-source.html', 'write-target.html', 'cant_tell'),
        ]
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda case: fixture(*case), cases))
        host_plan = exit_plan(base, 'frame-content-b.html')
        host_plan['steps'] = host_plan['steps'][:2] + [dict(key='Tab', focus=FRAME)]
        host_run = execute(out / 'host-focus', f'{base}/p12.html', [host_plan])
        _, host_row, host_proof, _, _ = read_result(host_run)
        assert host_row['outcome'] == 'failed' and host_proof['steps'][2]['after']['id'] == 'frame-first'
        assert '#subject → #frame-first' in host_row['observed']
        assert Handler.requests['GET', '/unlisted.html'] == 0
        assert Handler.requests['GET', '/cross-target.html'] == 0
        assert Handler.requests['GET', '/duplicate-target.html'] == 0
        assert Handler.requests['GET', '/sandbox-target.html'] == 1
        assert Handler.requests['POST', '/unexpected-write'] == 0
        assert any(r['method'] == 'POST' for r in outcomes[-1]['blocked'])
        audit.save(out / 'observed.json', {'outcomes': outcomes, 'host_focus_does_not_match_child': True})
        print(f'Completed {len(outcomes)} iframe route checks and verified the parent focus boundary.')
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        foreign_server.shutdown()
        foreign_server.server_close()
        foreign_thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
