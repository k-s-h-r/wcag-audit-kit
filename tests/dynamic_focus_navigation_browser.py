"""Check that a blocked focus-triggered navigation keeps the captured page report."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import threading
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills' / 'wcag-audit-kit' / 'scripts'
PUBLIC = ROOT / 'benchmarks' / 'cases' / '3.2.1' / 'public'
sys.path.insert(0, str(SCRIPTS))
import audit


class FixtureHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.server.paths.append(urlsplit(self.path).path)
        super().do_GET()

    def log_message(self, *args):
        pass


def explore_case(out, base, name):
    area = out / name
    area.mkdir()
    url = f'{base}/{name}'
    config = audit.init_config(url)
    config['environments'] = config['environments'][:1]
    config['keyboard_steps'] = 2
    audit.save(area / 'config.json', config)
    run = area / 'run'
    command = [sys.executable, str(SCRIPTS / 'audit.py'), 'page-audit',
               '--url', url, '--out', str(run), '--config', str(area / 'config.json'),
               '--mode', 'machine', '--screenshots', 'off', '--max-steps', '1', '--max-states', '1']
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (area / 'log.txt').write_text(result.stdout + result.stderr)
    assert result.returncode == 0, (name, result.stdout, result.stderr)
    report_path = next(run.glob('page-*-report.json'))
    assert report_path.with_suffix('.html').is_file() and next(run.glob('page-*-report.xlsx')).is_file()
    report = audit.load(report_path)
    assert not report['audit_complete'] and all(case['outcome'] == 'not_run' for case in report['cases'])
    graph = audit.load(run / 'exploration.json')
    node, = graph['nodes']
    assert node['route'] == []
    proof = run / node['evidence_dir']
    assert audit.load(proof / 'state.json')['url'] == url
    assert (proof / 'axe.json').is_file()
    trace = audit.load(proof / 'keyboard.json')
    stop_path = proof / 'keyboard-trace-stop.json'
    if name == 'p03.html':
        assert not trace
        stop = audit.load(stop_path)
        assert stop['step'] == 1 and stop['key'] == 'Tab'
        assert stop['blocked_requests'] == [{'method': 'GET', 'url': f'{base}/details.html'}]
        evidence_path = stop_path.relative_to(run).as_posix()
        reason = next(text for text in report['exploration']['remaining'] if evidence_path in text)
        assert '補助のTab観察は1回目で中断' in reason
        assert evidence_path in report_path.with_suffix('.html').read_text()
        assert audit.evidence_item(run, evidence_path) in graph['proof']
        inputs = audit.load(proof / 'input-events.json')['events']
        assert any(event.get('key') == 'Tab' and event['type'] == 'keydown' and event['isTrusted']
                   and event['url'] == url for event in inputs)
        return {'page': name, 'initial_state': True, 'trace_stop': stop, 'reports': True}
    assert not stop_path.exists()
    assert len(trace) == 2 and trace[0]['id'] == 'subject'
    assert graph['edges'][0]['blocked_requests'] == []
    return {'page': name, 'initial_state': True, 'trace_samples': len(trace), 'reports': True}


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(FixtureHandler, directory=str(PUBLIC))) as server:
        server.paths = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            cases = [explore_case(out, base, name) for name in ('p03.html', 'p04.html')]
            assert '/details.html' not in server.paths, server.paths
            (out / 'observed.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2))
            print(json.dumps(cases, ensure_ascii=False))
        finally:
            server.shutdown()
            thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
