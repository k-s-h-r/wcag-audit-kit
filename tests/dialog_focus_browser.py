"""Trace Escape and the next Tab without configuring a keyboard path."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

from openpyxl import load_workbook
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
    run, files = run_page_audit(out, url, None, max_states=10, max_steps=24)
    graph = audit.load(run/'exploration.json')
    result = audit.load(files['json'])
    assert next(row for row in result['criteria'] if row['id'] == '2.4.3')['status'] == 'unverified'
    origin = [{'type': 'click', 'selector': '#open'}]
    receipts = [edge for edge in graph['edges'] if edge.get('dialog_focus') and edge['route'][:1] == origin]
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
            assert row['observed'] in html and f'href="{audit.run_layout.href(Path(files["html"]), run / proof)}"' in html
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
    return observed or {'stayed_open': True}


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
                result = {name: job.result() for name, job in jobs.items()}
        finally:
            server.shutdown()
            thread.join()
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
