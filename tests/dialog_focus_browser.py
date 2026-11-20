"""Trace modal dismissal and the next Tab without configuring a keyboard path."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from html import escape
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

from openpyxl import load_workbook
from initial_page_audit_browser import invoke
from visual_structure_probe_browser import QuietHandler, audit, run_page_audit


PAGE = '''<!doctype html><html lang="ja"><meta charset="utf-8"><title>ダイアログの試験</title>
<button type="button" id="open">案内を開く</button><button type="button" id="next">次の案内</button>
<button type="button" id="other">別の案内</button><button type="button" id="end">最後の案内</button>
<dialog id="notice" aria-label="案内"><p>受付のご案内</p><button type="button" id="dismiss">閉じる</button></dialog>
<script>
const mode = new URLSearchParams(location.search).get('mode');
const openButton = document.getElementById('open');
const dialog = document.getElementById('notice');
openButton.onclick = () => dialog.showModal();
document.getElementById('dismiss').onclick = () => dialog.close();
const dismiss = document.getElementById('dismiss');
if (mode === 'reset') {
    openButton.insertAdjacentHTML('beforebegin', '<button type="button" id="start">先頭</button><button type="button" id="earlier">前の案内</button>');
    dialog.addEventListener('close', () => {
        const start = document.getElementById('start');
        start.focus();
        start.blur();
    });
}
if (mode === 'not-dismissing') dismiss.onclick = () => dismiss.textContent = '続き';
if (mode === 'still-visible') dismiss.onclick = () => { dialog.close(); dialog.show(); dismiss.focus(); };
if (mode === 'stayed') dialog.addEventListener('cancel', event => event.preventDefault());
if (mode === 'other') dialog.addEventListener('close', () => document.getElementById('other').focus());
if (mode === 'tab-stays') openButton.addEventListener('keydown', event => {
    if (event.key === 'Tab') event.preventDefault();
});
if (mode === 'bounded') setTimeout(() => {}, 60000);
if (mode === 'replacement') dialog.addEventListener('close', () => {
    const replacement = openButton.cloneNode(true);
    openButton.replaceWith(replacement);
    replacement.focus();
});
</script>'''


def verify(out, url, variant):
    run, files = run_page_audit(out, url, None, max_states=10, max_steps=32 if variant in {'return', 'other'} else 24)
    graph = audit.load(run/'exploration.json')
    result = audit.load(files['json'])
    assert next(row for row in result['criteria'] if row['id'] == '2.4.3')['status'] == 'unverified'
    origin = [{'type': 'click', 'selector': '#open'}]
    receipts = [edge for edge in graph['edges'] if edge.get('dialog_focus') and edge['route'][:1] == origin
                and edge['route'][1].get('key') == 'Escape']
    assert [edge['dialog_focus'] for edge in receipts] == (
        ['escape'] if variant in {'stayed', 'bounded'} else ['escape', 'tab'])
    html = Path(files['html']).read_text()
    observed = {}
    book = load_workbook(files['excel'], read_only=True, data_only=True)
    try:
        sheet = list(book['機械検査'].values)
        for edge in receipts:
            proof = edge['evidence_dir'] + '/dialog-focus.json'
            row, = [row for row in result['machine_checks'] if row['evidence'] == proof]
            receipt = row['dialog_focus']
            assert receipt == audit.load(run/proof)
            assert receipt['opener'] == '#open' and receipt['before_escape']['focus'] == '#dismiss'
            assert audit.evidence_item(run, proof) in graph['proof']
            events = audit.load(run/edge['evidence_dir']/'input-events.json')['events']
            opener = events[receipt['opener_event_index'] - 1]
            assert opener['type'] == 'click' and opener['target']['id'] == 'open' and opener['isTrusted']
            event = events[receipt['escape_event_index'] - 1]
            assert event['key'] == 'Escape' and event['isTrusted']
            assert escape(row['observed']) in html and f'href="{audit.run_layout.href(Path(files["html"]), run / proof)}"' in html
            assert any(proof in cells and row['observed'] in cells for cells in sheet)
            if variant == 'stayed':
                assert receipt['after_escape']['modals'] == ['#notice'] and row['outcome'] == 'cant_tell'
                continue
            if variant == 'bounded':
                assert receipt['status'] == 'unconfirmed' and row['outcome'] == 'cant_tell'
                assert '表示更新が観察範囲に収まらない' in row['observed']
                assert not receipt['after_escape']['modals']
                observed['escape_attempted'] = True
                continue
            assert receipt['status'] == 'closed' and not receipt['after_escape']['modals']
            assert receipt['opener_restored'] is (variant in {'return', 'tab-stays'})
            passes = variant == 'return' or (variant == 'tab-stays' and edge['dialog_focus'] == 'escape')
            assert row['outcome'] == ('passed' if passes else 'cant_tell')
            assert receipt['after_escape']['focus'] == ('#other' if variant == 'other' else '#open')
            if edge['dialog_focus'] == 'tab':
                assert receipt['after_tab']['focus'] == {'other': '#end', 'tab-stays': '#open'}.get(variant, '#next')
                assert receipt['tab_moved_focus'] is (variant != 'tab-stays')
                event = events[receipt['tab_event_index'] - 1]
                assert event['key'] == 'Tab' and event['isTrusted']
            observed[receipt['phase']] = {'escape': receipt['after_escape']['focus'],
                                        'tab': receipt.get('after_tab', {}).get('focus')}
    finally:
        book.close()
    if variant in {'return', 'other'}:
        observed['buttons'] = verify_button_receipts(run, graph, result, origin, variant)
    return observed or {'stayed_open': True}


def verify_button_receipts(run, graph, result, origin, variant):
    candidates = [edge for edge in graph['edges'] if edge.get('dialog_focus') and edge['route'][:1] == origin
                  and len(edge['route']) == 2 + (edge['dialog_focus'] == 'tab')
                  and edge['route'][1]['selector'] == '#dismiss']
    assert candidates
    checked = {}
    for edge in candidates:
        proof = edge['evidence_dir'] + '/dialog-focus.json'
        receipt = audit.load(run/proof)
        rows = [row for row in result['machine_checks'] if row['evidence'] == proof]
        operation = receipt['close_action'].get('key', 'click')
        phase = receipt['phase']
        assert receipt['close_action'] == edge['route'][1]
        assert receipt['opener'] == '#open' and receipt['before_close']['modals'] == ['#notice']
        events = audit.load(run/edge['evidence_dir']/'input-events.json')['events']
        event = events[receipt['close_event_index'] - 1]
        assert event['isTrusted'] and event['expectedTargetMatched'] and event['is_main_frame']
        assert event['target']['id'] == 'dismiss'
        if operation == 'click':
            assert event['type'] == 'click' and event['pointerType'] == 'mouse'
        else:
            assert event['type'] == 'keydown' and event['key'] == ('[character]' if operation == 'Space' else operation)
        if variant == 'not-dismissing':
            assert receipt['status'] == 'not_dismissed' and not rows
            assert receipt['after_close']['modals'] == ['#notice']
            checked[operation] = 'not_dismissed'
            continue
        row, = rows
        assert row['dialog_focus'] == receipt
        assert '#dismiss' in row['observed']
        if variant == 'still-visible':
            assert receipt['status'] == 'unconfirmed' and row['outcome'] == 'cant_tell'
            assert 'ダイアログは表示されている' in row['observed']
        else:
            assert receipt['status'] == 'closed' and not receipt['after_close']['modals']
            if variant in {'return', 'other', 'quick'}:
                assert receipt['after_close']['focus'] == ('#other' if variant == 'other' else '#open')
                assert row['outcome'] == ('cant_tell' if variant == 'other' else 'passed')
            elif variant == 'reset':
                assert receipt['after_close']['root_focus'] and not receipt['opener_restored']
                assert row['outcome'] == ('failed' if phase == 'tab' else 'cant_tell')
                if phase == 'tab':
                    assert receipt['tab_moved_before_opener'] and receipt['after_tab']['focus'] == '#earlier'
        if phase == 'tab':
            event = events[receipt['tab_event_index'] - 1]
            assert event['key'] == 'Tab' and event['isTrusted']
            if variant in {'return', 'other', 'quick'}:
                assert receipt['after_tab']['focus'] == ('#end' if variant == 'other' else '#next')
        checked[operation] = row['outcome']
    assert {'click', 'Enter'} <= checked.keys()
    if variant in {'return', 'other', 'quick'}:
        if variant != 'quick':
            assert 'Space' in checked
        assert {edge['route'][1].get('key','click') for edge in candidates if edge['dialog_focus'] == 'tab'} == set(checked)
    return checked


def verify_additional_button_patterns(out, url, variant):
    run, files = run_page_audit(out, url, None, max_states=12, max_steps=36)
    graph = audit.load(run/'exploration.json')
    result = audit.load(files['json'])
    origin = [{'type': 'click', 'selector': '#open'}]
    assert next(row for row in result['criteria'] if row['id'] == '2.4.3')['status'] == 'unverified'
    outcomes = verify_button_receipts(run, graph, result, origin, variant)
    if variant == 'reset':
        assert outcomes['click'] == outcomes['Enter'] == 'failed'
    else:
        assert not any(edge.get('dialog_focus') == 'tab' and len(edge['route']) == 3
                       and edge['route'][:1] == origin and edge['route'][1]['selector'] == '#dismiss'
                       for edge in graph['edges'])
    html = Path(files['html']).read_text()
    book = load_workbook(files['excel'], read_only=True, data_only=True)
    try:
        sheet = list(book['機械検査'].values)
        for row in result['machine_checks']:
            if row.get('dialog_focus', {}).get('close_action', {}).get('selector') != '#dismiss':
                continue
            assert escape(row['observed']) in html and any(row['evidence'] in cells and row['observed'] in cells for cells in sheet)
    finally:
        book.close()
    return outcomes


def verify_quick(out, url):
    config = audit.init_config(url)
    config.update(environments=config['environments'][:1], keyboard_steps=0)
    config_path = out.with_suffix('.json')
    audit.save(config_path, config)
    command = ['page-audit', '--url', url, '--out', str(out), '--config', str(config_path), '--mode',
               'machine', '--screenshots', 'off']
    initial = invoke(command + ['--initial-only'])
    assert initial['operation_exploration_deferred']
    explored = invoke(command + ['--resume', '--quick-explore'])
    run = audit.run_layout.ledger(out)
    graph = audit.load(run/'exploration.json')
    assert graph['quick_explore'] and graph['steps'] <= 24
    assert max(len(edge['route']) for edge in graph['edges']) == 3
    result = audit.load(explored['json'])
    return verify_button_receipts(run, graph, result, [{'type': 'click', 'selector': '#open'}], 'quick')


def main(out):
    out.mkdir(exist_ok=False)
    (out/'index.html').write_text(PAGE)
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(out))) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                jobs = {name: pool.submit(verify, out/name, f'http://127.0.0.1:{server.server_port}/index.html?mode={name}', name)
                        for name in ('return', 'other', 'stayed', 'replacement', 'tab-stays', 'bounded')}
                jobs.update({name: pool.submit(verify_additional_button_patterns, out/name,
                    f'http://127.0.0.1:{server.server_port}/index.html?mode={name}', name)
                    for name in ('reset', 'not-dismissing', 'still-visible')})
                result = {name: job.result() for name, job in jobs.items()}
            result['quick'] = verify_quick(out/'quick', f'http://127.0.0.1:{server.server_port}/index.html?mode=quick')
        finally:
            server.shutdown()
            thread.join()
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
