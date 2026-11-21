"""Compare quick and whole-page axe results after the same browser operation."""
import argparse
import asyncio
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from time import perf_counter

from playwright.async_api import async_playwright

from initial_page_audit_browser import ROOT, audit, invoke, page_explorer
import operation_impact
from operation_impact import LOCAL_SELECTORS, RESULT_TYPES, target_lists


LIMITS = {'max_steps': 24, 'max_states': 16, 'max_depth': 1}

# Each page also has unchanged targets that the narrow scan can otherwise reuse.
FIXTURES = {
    'css': (
        'html:not(.shown) #panel{display:none}',
        '<button type="button" id="act" aria-expanded="false" aria-controls="panel">Reveal section</button>'
        '<section id="panel"><button type="button" id="new-button" tabindex="2" '
        'aria-mistyped="true">New button</button></section>',
        '', "document.documentElement.classList.add('shown'); act.setAttribute('aria-expanded','true');",
    ),
    'external-label': (
        '', '<button type="button" id="act" aria-pressed="false">Replace label</button>'
        '<button type="button" id="labelled" aria-labelledby="label"></button>',
        '<div id="far-end" style="margin-top:1500px"><span hidden id="label">External label</span></div>',
        "document.querySelector('#label').textContent=''; act.setAttribute('aria-pressed','true');",
    ),
    'remote-popup': (
        'html:not(.shown) #portal{display:none}',
        '<button type="button" id="act" aria-expanded="false" aria-controls="portal">Reveal remote panel</button>',
        '<div id="far-end" style="margin-top:1500px"><aside id="portal" aria-mistyped="true">'
        '<button type="button" id="popup-entry" tabindex="2" aria-mistyped="true">Popup item</button>'
        '</aside></div>', "document.documentElement.classList.add('shown'); act.setAttribute('aria-expanded','true');",
    ),
    'native-modal': (
        '', '<button type="button" id="act" aria-haspopup="dialog" aria-controls="modal">Open native dialog</button>',
        '<dialog id="modal"><h2>New dialog</h2><button type="button" id="popup-entry" tabindex="2" '
        'aria-mistyped="true" autofocus>Close</button></dialog>', "document.querySelector('#modal').showModal();",
    ),
}


class Handler(SimpleHTTPRequestHandler):
    requests = Counter()

    def do_GET(self):
        self.requests[self.path] += 1
        super().do_GET()

    def log_message(self, *_):
        pass


def write_fixtures(directory):
    directory.mkdir()
    stable = ''.join(f'<div id="stable-{i}" tabindex="-1" aria-hidden="false">Note {i}</div>'
                     for i in range(8))
    stable += '<button id="stable-error" type="button" aria-mistyped="true" tabindex="2">Known previous issue</button>'
    for name, (styles, content, outside, action) in FIXTURES.items():
        (directory/f'{name}.html').write_text(f'''<!doctype html><html lang="en"><head><title>Operation recheck | {name}</title><style>{styles}</style></head><body>
<main><h1>Operation recheck</h1>{content}{stable}</main>{outside}
<script>const act=document.querySelector('#act');act.onclick=()=>{{{action}}};</script></body></html>''')


def signatures(results):
    return {category: {rule['id']: sorted((tuple(node['target']), node['impact']) for node in rule['nodes'])
                       for rule in results[category]} for category in RESULT_TYPES}


def scan(out, url, config_path, request_path, *, quick):
    args = ['page-audit', '--url', url, '--out', str(out), '--config', str(config_path),
            '--mode', 'machine', '--screenshots', 'off']
    for limit, value in LIMITS.items():
        args.extend(['--'+limit.replace('_','-'), str(value)])
    start = perf_counter()
    requests = Handler.requests[request_path]
    if quick:
        invoke(args + ['--initial-only'])
        invoke(args + ['--resume', '--quick-explore'])
    else:
        invoke(args + ['--explore'])
    ledger = audit.run_layout.ledger(out)
    graph = page_explorer.status(ledger)
    directories = {edge['environment']: ledger/edge['evidence_dir'] for edge in graph['edges']
                   if edge['route'] == [{'type':'click','selector':'#act'}] and edge['error'] is None}
    assert directories.keys() == {'desktop', 'narrow'}, directories
    counts = dict(states=len(graph['nodes']), steps=graph['steps'],
                  completed_routes=sum(bool(edge['route']) and edge['error'] is None for edge in graph['edges']),
                  document_requests=Handler.requests[request_path]-requests, seconds=round(perf_counter()-start, 3))
    return directories, counts


def compare(out, origin):
    results = []
    for name in FIXTURES:
        url = f'{origin}/{name}.html'
        config = audit.init_config(url)
        config['environments'] = config['environments'][:2]
        config['keyboard_steps'] = 2
        path = out/f'{name}-config.json'
        audit.save(path, config)
        quick, quick_counts = scan(out/f'{name}-quick', url, path, f'/{name}.html', quick=True)
        whole, whole_counts = scan(out/f'{name}-whole', url, path, f'/{name}.html', quick=False)
        comparisons = []
        for environment in quick:
            quick_results = audit.load(quick[environment]/'axe.json')
            whole_results = audit.load(whole[environment]/'axe.json')
            scope = audit.load(quick[environment]/'operation-impact.json')['axe']
            assert signatures(quick_results) == signatures(whole_results), (name, environment, scope)
            if name == 'native-modal':
                assert scope == {'mode':'whole_page', 'reason':'native_modal'}, scope
                violations = target_lists({'violations': quick_results['violations'], 'passes':[], 'incomplete':[]},
                                          LOCAL_SELECTORS)
                assert all(nodes == [['#popup-entry']] for nodes in violations.values()), violations
            else:
                assert scope['mode'] == 'mixed', scope
                assert all('#stable-error' in reused for reused in scope['reused'].values()), scope
            full_counts = {rule:len(nodes) for rule, nodes in target_lists(whole_results, LOCAL_SELECTORS).items()}
            comparisons.append(dict(environment=environment, mode=scope['mode'], reason=scope.get('reason'),
                rechecked={rule:len(scope['rechecked'][rule]) for rule in scope.get('rechecked',{})} or full_counts,
                reused={rule:len(nodes) for rule,nodes in scope.get('reused',{}).items()}, whole_counts=full_counts,
                quick=str(quick[environment].relative_to(out)), whole=str(whole[environment].relative_to(out))))
        results.append(dict(case=name, quick=quick_counts, whole=whole_counts, comparisons=comparisons))
    audit.save(out/'result.json', dict(limits=LIMITS, cases=results))


async def expect_modal_change(page, data, reused):
    try:
        await operation_impact.run_axe(page, data, reused)
    except ValueError as error:
        assert str(error) == operation_impact.MODAL_STATE_CHANGED
    else:
        raise AssertionError('Axe results were published against a different modal state')


async def verify_modal_context():
    assets = ROOT/'skills/wcag-audit-kit'
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path='/usr/bin/chromium')
        context = await browser.new_context()
        await context.add_init_script(path=assets/'scripts/page_explorer.js')
        page = await context.new_page()
        await page.goto('about:blank')
        await page.set_content('''<!doctype html><html lang="en"><head><title>Late modal</title></head><body>
<main><button id="stable" aria-mistyped="true" tabindex="2">Outside</button></main>
<dialog><p>New dialog</p><button autofocus>Close</button></dialog></body></html>''')
        non_modal, native = await page.evaluate('''() => {
          const dialog = document.querySelector('dialog');
          dialog.show();
          const nonModal = window.__wcagExplore(true);
          dialog.close();
          dialog.showModal();
          const native = window.__wcagExplore(true);
          dialog.close();
          return [nonModal, native];
        }''')
        assert not non_modal.get('native_modals') and len(native['native_modals']) == 1
        without_mode = {key:value for key, value in native.items() if key != 'native_modals'}
        assert page_explorer.fingerprint(non_modal) == page_explorer.fingerprint(without_mode)
        assert page_explorer.fingerprint(non_modal) != page_explorer.fingerprint(native)
        await page.evaluate((assets/'vendor/axe.min.js').read_text())
        before = await page.evaluate("() => window.__wcagExplore(true)")
        operation_impact.compact(before)
        baseline, _ = await operation_impact.run_axe(page, before, {})
        impact = operation_impact.difference(before, before, {'selector':'body','type':'click'},
                                             {'targets':[],'truncated':False})
        reused = operation_impact.reusable_nodes(before, before, before, baseline, impact)
        assert reused.keys() == LOCAL_SELECTORS.keys(), reused
        await page.evaluate('''() => {
          const run = axe.run.bind(axe);
          axe.run = async (...args) => {
            const result = await run(...args);
            const dialog = document.querySelector('dialog');
            if (!dialog.open) dialog.showModal();
            return result;
          };
        }''')
        await expect_modal_change(page, before, reused)
        after = await page.evaluate("() => window.__wcagExplore('inputs')")
        operation_impact.compact(after)
        assert before['operation_inputs'] == after['operation_inputs']
        await page.close()

        page = await context.new_page()
        await page.goto('about:blank')
        await page.set_content('''<!doctype html><html lang="en"><head><title>Stacked modals</title></head><body>
<dialog id="a"><button id="a-item" aria-mistyped="true" tabindex="2">First</button></dialog>
<dialog id="b"><button id="b-item" aria-mistyped="true" tabindex="2">Second</button></dialog></body></html>''')
        await page.evaluate((assets/'vendor/axe.min.js').read_text())
        snapshots = []
        for first, last in (('a','b'), ('b','a')):
            await page.evaluate('''([first, last]) => {
              document.getElementById(first).showModal();
              document.getElementById(last).showModal();
            }''', [first,last])
            data = await page.evaluate("() => window.__wcagExplore(true)")
            assert data['native_modals'] == ['#a', '#b']
            result, _ = await operation_impact.run_axe(page, data, {})
            violations = {rule['id']: [node['target'] for node in rule['nodes']] for rule in result['violations']}
            assert all(violations[rule] == [[f'#{last}-item']] for rule in LOCAL_SELECTORS), violations
            snapshots.append(data)
            await page.evaluate("() => document.querySelectorAll('dialog').forEach(dialog => dialog.close())")
        assert page_explorer.fingerprint(snapshots[0]) == page_explorer.fingerprint(snapshots[1])
        first, second = (dict(data, native_modal_observation=f'observation-{i}') for i, data in enumerate(snapshots))
        assert page_explorer.fingerprint(first) != page_explorer.fingerprint(second)

        await page.evaluate("() => document.querySelectorAll('dialog').forEach(dialog => dialog.showModal())")
        stacked = await page.evaluate("() => window.__wcagExplore(true)")
        await page.evaluate('''() => {
          const run = axe.run.bind(axe);
          axe.run = async (...args) => {
            const result = await run(...args);
            const dialog = document.querySelector('#a');
            dialog.close();
            dialog.showModal();
            return result;
          };
        }''')
        await expect_modal_change(page, stacked, {})
        reordered = await page.evaluate("() => window.__wcagExplore(true)")
        assert stacked['native_modals'] == reordered['native_modals']
        assert stacked['dialog_generation'] < reordered['dialog_generation']
        await browser.close()


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    fixtures = out/'fixture'
    write_fixtures(fixtures)
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=fixtures)) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            compare(out, f'http://127.0.0.1:{server.server_port}')
        finally:
            server.shutdown()
            thread.join()
    asyncio.run(verify_modal_context())
    print('Quick and whole-page results match for four operations at both widths.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    main(parser.parse_args().out)
