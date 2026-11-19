"""Verify text paint measurements and held counterexamples in fresh Chromium contexts."""
import argparse
from functools import partial
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmarks.text_paint_probe import CAPTURE_STAGES, probe


class Observer(BaseHTTPRequestHandler):
    visits = []

    def do_GET(self):
        self.visits.append(self.path)
        self.send_response(204)
        self.end_headers()

    def log_message(self, *_):
        pass


def check_source(out, label, source, budget=7, selector='#subject'):
    original = source.read_bytes()
    run = out / label
    result = probe(source, selector, run, budget)
    assert source.read_bytes() == original
    assert result['source_sha256'] == sha256(original).hexdigest()
    assert len(result['frames']) <= budget
    for frame in result['frames'].values():
        assert sha256((run / frame['path']).read_bytes()).hexdigest() == frame['sha256']
    assert json.loads((run / 'result.json').read_text())['status'] == result['status']
    return result


def fixture(out, name, css, inner='<p id="subject">Available to reserve</p>'):
    source = out / f'{name}.html'
    source.write_text(f'<!doctype html><style>{css}</style><main>{inner}</main>', encoding='utf-8')
    return source


def check_measurement(result, ratio, threshold, meets):
    assert result['status'] == 'measured', result
    assert abs(result['ratio'] - ratio) < 0.000001 and result['threshold'] == threshold
    assert result['threshold_met'] is meets
    frames = result['frames']
    assert set(frames) == set(CAPTURE_STAGES)
    assert len({frames[stage]['sha256'] for stage in ('original', 'original-repeat', 'restored', 'restored-repeat')}) == 1
    assert result['blocked_requests'] == []


def main(out):
    out.mkdir(exist_ok=False)
    fixtures = ROOT / 'benchmarks/cases/1.4.3/public'
    measured = {}
    for name, ratio, meets in (('p01', 2.323123, False), ('p02', 18.883061, True)):
        result = check_source(out, name, fixtures / f'{name}.html')
        check_measurement(result, ratio, 4.5, meets)
        measured[name] = result['ratio']
    bold = fixture(out, 'bold', 'main {background: white} p {font:700 20px sans-serif;color:#777}')
    result = check_source(out, 'bold-evidence', bold)
    check_measurement(result, 4.478089, 3, True)
    measured['bold'] = result['ratio']

    held = {}
    plain = 'main{background:white}p{font:16px sans-serif;color:#111}'
    examples = {
        'alpha': (plain + 'p{opacity:.5}', None),
        'gradient': (plain + 'p{background:linear-gradient(90deg,white,#aaa)}', None),
        'overlay': (plain + 'span{position:absolute;inset:0 auto 0 0;width:100px;background:white;pointer-events:none}',
                    '<p id="subject">Available to reserve</p><span aria-hidden="true"></span>'),
        'fill-changes-layout': (plain + 'p[style]{margin-left:15px}', None),
        'mixed-font': (plain + 'p::first-letter{font-size:18px}', None),
        'font-size-adjust': ('main{background:white}p{font:400 24px sans-serif;color:#777;font-size-adjust:.25}', None),
        'font-weight-variation': ('main{background:white}p{font:700 20px sans-serif;color:#777;font-variation-settings:"wght" 400}', None),
        'fractional-font-weight': ('main{background:white}p{font:699.5 20px sans-serif;color:#777}', None),
        'script': (plain, '<p id="subject">Available to reserve</p><script>document.body.remove()</script>'),
        'duplicate': (plain, '<p id="subject">Available</p><p id="subject">To reserve</p>'),
    }
    for label, (css, inner) in examples.items():
        source = fixture(out, label, css, inner) if inner else fixture(out, label, css)
        result = check_source(out, f'{label}-evidence', source)
        assert result['status'] == 'hold' and 'ratio' not in result, result
        held[label] = result['reason']
    budget = check_source(out, 'budget', fixtures / 'p02.html', 6)
    assert budget['status'] == 'hold' and budget['frames'] == {}
    held['budget'] = budget['reason']

    with ThreadingHTTPServer(('127.0.0.1', 0), partial(Observer)) as observer:
        thread = Thread(target=observer.serve_forever, daemon=True)
        thread.start()
        try:
            external = fixture(out, 'external', plain +
                f'p{{background-image:url("http://127.0.0.1:{observer.server_port}/outside")}}')
            result = check_source(out, 'external-evidence', external)
            assert result['status'] == 'hold' and 'ratio' not in result and not Observer.visits, result
            held['external'] = result['reason']
        finally:
            observer.shutdown()
            thread.join()
    print(json.dumps({'measured': measured, 'held': held, 'external_visits': Observer.visits}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    main(parser.parse_args().out)
