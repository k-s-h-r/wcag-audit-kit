"""Exercise the initial-only report and an opt-in exploration on the same local page."""
import argparse
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/wcag-audit-kit/scripts'))
import audit
import page_explorer
import page_workflow


class Fixture(BaseHTTPRequestHandler):
    hits = Counter()
    image = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'

    def do_GET(self):
        self.hits[self.path] += 1
        self.send_response(200 if self.path in ('/', '/dense', '/impact') else 404)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        if self.path == '/impact':
            stable = ''.join(f'<div id="stable-{i}" tabindex="-1" aria-hidden="false">Note {i}</div>'
                             for i in range(8))
            self.wfile.write(f"""<!doctype html><html lang="en"><head><title>Accordion</title>
<style>[aria-expanded=false] + #panel {{ display: none; }}</style></head><body><main><h1>Accordion</h1>
{stable}<div id="stable-group"><div id="stable-error" aria-mistyped="true" tabindex="-1">Existing issue</div></div>
<button id="toggle" type="button" aria-expanded="false" aria-controls="panel">Details</button>
<section id="panel"><button id="inside" type="button" aria-mistp="true" tabindex="0">Inside</button></section>
<button id="labelled" type="button" aria-labelledby="label"></button>
<span id="label" hidden>External name</span>
<button id="name-only" type="button">Change name</button>
<button id="aria-hide" type="button">Hide semantics</button>
<button id="make-inert" type="button">Disable region</button>
<script>
document.querySelector('#toggle').onclick = event => {{
  const open = event.currentTarget.getAttribute('aria-expanded') === 'false';
  event.currentTarget.setAttribute('aria-expanded', String(open));
}};
let label = document.querySelector('#label');
document.querySelector('#name-only').onclick = () => label.textContent = label.textContent ? '' : 'External name';
const stableGroup = document.querySelector('#stable-group');
document.querySelector('#aria-hide').onclick = () => stableGroup.setAttribute('aria-hidden', 'true');
document.querySelector('#make-inert').onclick = () => stableGroup.inert = true;
</script></main></body></html>""".encode())
            return
        if self.path == '/dense':
            controls = ''.join(f'<button id="item-{i}" onclick="this.hidden=true">Option {i}</button>'
                               for i in range(40))
            self.wfile.write(f'''<!doctype html><html lang="en"><head><title>Dense page</title></head>
<body><main><h1>Dense page</h1>{controls}<details><summary id="outer">Show menu</summary>
<details><summary id="inner">More options</summary><img id="nested-image" src="{self.image}"></details>
</details></main></body></html>'''.encode())
            return
        if self.path != '/':
            return
        spans = ''.join(f'<span id="link-text-{i}"> Section</span>' for i in range(30))
        self.wfile.write(f'''<!DOCTYPE html><html lang="en"><head><title>Local audit test</title>
<style>summary, a, #standalone, #child-handler, #delegate, [role=button] {{ cursor:pointer; }}</style></head>
<body><main><h1 id="content">Audit test</h1><img id="initial-image" src="{self.image}">
<details><summary id="toggle"><span id="summary-text">Open section</span></summary>
<p>Expanded content below.</p><img id="operation-image" src="{self.image}"></details>
<a id="link" href="/other">{spans}</a>
<div id="custom" role="button" tabindex="0"><span id="passive">Label</span>
<span id="child-handler">Child with its own handler</span></div>
<div id="standalone">Pointer-only fallback</div>
<div id="delegate"><span id="delegate-target">Delegated target</span></div></main>
<script>
document.querySelector('#child-handler').addEventListener('click', e => e.stopPropagation());
document.querySelector('#delegate').addEventListener('click', e => {{
  if (e.target.id === 'delegate-target') e.target.textContent = 'Delegated click handled';
}});
</script>
</body></html>'''.encode())

    def log_message(self, *args):
        pass


def invoke(args, expected=0):
    output, errors = io.StringIO(), io.StringIO()
    with redirect_stdout(output), redirect_stderr(errors):
        code = audit.main(args)
    assert code == expected, (args, code, errors.getvalue(), output.getvalue())
    return errors.getvalue() if expected else json.loads(output.getvalue().strip().splitlines()[-1])


def machine_alt(value):
    return [row['target'] for row in value['machine_checks']
            if row['checkpoint'] == 'axe / image-alt' and row['outcome'] == 'failed']


def verify_quick_exploration(out, origin):
    url = origin + '/dense'
    command = ['page-audit', '--url', url, '--out', str(out)]
    baseline = invoke(command + ['--initial-only'])
    assert Fixture.hits['/dense'] == 2
    explored = invoke(command + ['--resume', '--quick-explore'])
    run = audit.run_layout.ledger(out)
    graph = page_explorer.status(run)
    routes = [edge for edge in graph['edges'] if edge['route']]
    assert graph['quick_explore'] and graph['limits'] == {'max_states': 16, 'max_steps': 24, 'max_depth': 3}
    assert graph['steps'] <= 24 and set(edge['environment'] for edge in routes) == {'desktop', 'narrow'}
    assert len(routes) > 4 and len([e for e in routes[:4] if e['environment'] == 'desktop']) == 2
    assert any([action['selector'] for action in edge['route']] == ['#outer', '#inner']
               and edge['error'] is None for edge in routes), routes
    assert all(edge['route'][0]['selector'] != '#inner' for edge in routes)
    assert max(len(edge['route']) for edge in routes) <= 3
    pending = Counter(job['environment'] for job in graph['queue'] if job['route'])
    assert all(count <= page_explorer.QUICK_PENDING_PER_ENVIRONMENT for count in pending.values()), pending
    omissions = explored['omitted_candidates']
    assert all(omissions[kind] > 0 for kind in ('frontier', 'unchanged_control', 'input_variations')), omissions
    assert baseline['html'] == explored['html']
    report = audit.load(Path(explored['json']))
    assert not report['audit_complete']
    assert any('#nested-image' in row for row in machine_alt(report))
    assert report['exploration']['omitted_candidates'] == omissions
    assert '未確認の操作' in Path(explored['html']).read_text()



def verify_operation_impact(out, origin):
    out.mkdir()
    url = origin + '/impact'
    config = audit.init_config(url)
    config['environments'] = config['environments'][:1]
    config['keyboard_steps'] = 1
    config_path = out / 'config.json'
    audit.save(config_path, config)

    def run(name, quick):
        path = out / name
        command = ['page-audit', '--url', url, '--out', str(path), '--config', str(config_path),
                   '--mode', 'machine', '--screenshots', 'off', '--max-steps', '24']
        if quick:
            invoke(command + ['--initial-only'])
            invoke(command + ['--resume', '--quick-explore'])
        else:
            invoke(command + ['--explore'])
        return audit.run_layout.ledger(path)

    quick = run('quick', True)
    full = run('full', False)

    def evidence(run, selector, depth=1):
        edges = page_explorer.status(run)['edges']
        edge = next(edge for edge in edges if len(edge['route']) == depth and all(
            step['type'] == 'click' and step['selector'] == selector for step in edge['route']))
        assert edge['error'] is None, edge
        return run / edge['evidence_dir']

    def axe_results(path):
        results = audit.load(path / 'axe.json')
        return {category: {rule['id']: sorted(tuple(node['target']) for node in rule['nodes'])
                           for rule in results[category]}
                for category in ('violations', 'incomplete', 'passes', 'inapplicable')}

    opened = evidence(quick, '#toggle')
    impact = audit.load(opened / 'operation-impact.json')
    assert impact['focus']['after'] == '#toggle', impact
    assert {'#panel', '#inside'} <= set(impact['appeared']), impact
    assert '#toggle' in impact['changed'] and '#toggle' in impact['mutated'], impact
    assert impact['axe']['mode'] == 'mixed', impact
    assert len(impact['axe']['reused']['aria-valid-attr']) == 10, impact
    assert len(impact['axe']['reused']['tabindex']) == 9, impact
    assert {tuple(target) for target in impact['axe']['rechecked']['aria-valid-attr']} == {
        ('#toggle',), ('#inside',)}, impact
    assert impact['axe']['rechecked']['tabindex'] == [['#inside']], impact
    results = axe_results(opened)
    assert results == axe_results(evidence(full, '#toggle')), results
    assert ('#inside',) in results['violations']['aria-valid-attr']
    assert ('#stable-error',) in results['violations']['aria-valid-attr']
    tab = audit.load(opened / 'keyboard.json')
    assert tab[0]['id'] == 'inside', tab

    closed = evidence(quick, '#toggle', depth=2)
    impact = audit.load(closed / 'operation-impact.json')
    assert {'#panel', '#inside'} <= set(impact['disappeared']), impact
    assert impact['focus']['after'] == '#toggle', impact
    assert impact['axe']['mode'] == 'same_state', impact
    assert ('#inside',) not in axe_results((quick / impact['axe']['baseline']).parent)['violations']['aria-valid-attr']

    changed = evidence(quick, '#name-only')
    impact = audit.load(changed / 'operation-impact.json')
    assert '#label' in impact['changed'] and '#labelled' in impact['related'], impact
    assert ('#labelled',) in axe_results(changed)['violations']['button-name'], impact
    assert axe_results(changed) == axe_results(evidence(full, '#name-only'))

    for selector in ('#aria-hide', '#make-inert'):
        changed = evidence(quick, selector)
        impact = audit.load(changed / 'operation-impact.json')
        assert '#stable-group' in impact['mutated'], impact
        assert impact['axe']['mode'] == 'mixed', impact
        for rule in ('aria-valid-attr', 'tabindex'):
            assert '#stable-error' not in impact['axe']['reused'][rule], impact
        assert axe_results(changed) == axe_results(evidence(full, selector)), impact

def main(out):
    with ThreadingHTTPServer(('127.0.0.1', 0), Fixture) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}/'
            command = ['page-audit', '--url', url, '--out', str(out)]
            baseline = invoke(command + ['--mode', 'machine', '--screenshots', 'all', '--initial-only'])
            run = audit.run_layout.ledger(out)
            files = audit.run_layout.report_files(run, single=True)
            graph = page_explorer.status(run)
            assert graph['deferred'] and graph['steps'] == 2 and not graph['queue']
            assert Fixture.hits['/'] == 2 and not Fixture.hits['/other']
            assert baseline['operation_exploration_deferred'] and baseline['pending_routes'] == 0
            assert baseline['explore_command'].endswith('--resume --quick-explore')
            assert len(graph['nodes']) == 2
            assert len(list(run.rglob('*.png'))) == 2
            for node in graph['nodes']:
                dest = run / node['evidence_dir']
                assert (dest/'page.png').exists()
                assert not (dest/'keyboard.json').exists() and not (dest/'tiles.json').exists()
                selectors = {item['selector'] for item in node['controls']}
                assert selectors == {'#toggle', '#link', '#custom', '#child-handler', '#standalone',
                                     '#delegate', '#delegate-target'}, selectors
                assert node['controls'][-1]['selector'] == '#delegate-target'
            value = audit.load(files.json)
            assert value['exploration']['deferred'] and not value['audit_complete']
            assert machine_alt(value) and all('#initial-image' in row for row in machine_alt(value))
            assert '操作探索は未実施です。' in files.html.read_text()
            packet = page_workflow.next_work(run, url, limit=1)
            assert packet['exploration']['deferred'] and packet['exploration']['next'].endswith('--quick-explore')

            immutable = [run/'run.json', *(run / row['path'] for row in graph['proof'])]
            hashes = [sha256(path.read_bytes()).digest() for path in immutable]
            assert '--explore' in invoke(command + ['--resume'], expected=1)
            assert not page_explorer.status(run)['queue'] and Fixture.hits['/'] == 2

            explored = invoke(command + ['--resume', '--explore', '--max-steps', '6'])
            updated = page_explorer.status(run)
            assert not updated['deferred'] and updated['steps'] == 6
            assert [sha256(path.read_bytes()).digest() for path in immutable] == hashes
            assert sum(edge.get('initial_input', False) for edge in updated['edges']) == 2
            assert all((run/edge['evidence_dir']/'keyboard.json').is_file()
                       for edge in updated['edges'] if edge.get('initial_input'))
            assert explored['html'] == baseline['html'] and not explored['operation_exploration_deferred']
            value = audit.load(files.json)
            assert not value['exploration']['deferred'] and not value['audit_complete']
            assert any('#operation-image' in row for row in machine_alt(value))
            assert '操作探索は未実施です。' not in files.html.read_text()
            assert not Fixture.hits['/other']

            interrupted_out = out / 'partial'
            partial = ['page-audit', '--url', url, '--out', str(interrupted_out), '--initial-only']
            invoke(partial + ['--max-steps', '1'])
            partial_run = audit.run_layout.ledger(interrupted_out)
            first = page_explorer.status(partial_run)
            assert first['deferred'] and first['steps'] == 1 and len(first['queue']) == 1
            partial_packet = page_workflow.next_work(partial_run, url, limit=1)
            assert partial_packet['exploration']['next'].endswith('--initial-only')
            invoke(partial + ['--resume'])
            finished = page_explorer.status(partial_run)
            assert finished['deferred'] and finished['steps'] == 2 and not finished['queue']
            assert all(item in finished['proof'] for item in first['proof'])

            verify_quick_exploration(out / 'quick', url.rstrip('/'))
            verify_operation_impact(out / 'impact', url.rstrip('/'))
        finally:
            server.shutdown()
            worker.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
