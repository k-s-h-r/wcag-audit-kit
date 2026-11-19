"""Exercise a finite site-selection packet against an owned loopback fixture."""

import argparse
import asyncio
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from playwright.async_api import async_playwright, expect

from fixtures import audit_site_server as site
from url_selection_browser import ROOT, start_server, stop_server, write_json


SKILL = ROOT / 'skills/wcag-audit-kit'
VIEWPORT = {'width': 1280, 'height': 900}
COMPLETION = '/procedure-done?flow=selected#receipt'
HISTORY = '/account/history'
EXCLUDED = '/excluded/page'
MISSING = '/missing'
PUBLIC = ('/', '/profile', '/media', '/help', '/login', '/unlinked', MISSING)


class SelectionFixture(site.Handler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in {'/procedure-done', HISTORY, '/unlinked'}:
            if path == HISTORY and not self.session():
                self.send(401, {'error': 'sign-in required'})
                return
            messages = {
                '/procedure-done': 'Procedure complete',
                HISTORY: 'Account history',
                '/unlinked': 'Known but unlinked page',
            }
            content = f'<h1 id="receipt">{messages[path]}</h1><a href="/">Return to Home</a>'
            body = f'<!doctype html><html lang="en"><title>Selection fixture</title>{content}</html>'
            self.send(200, body.encode(), 'text/html; charset=utf-8')
            return
        super().do_GET()

    def send(self, status, body, content_type='application/json; charset=utf-8', cookie=None):
        path = urlsplit(self.path).path
        self.server.observed_requests.append((self.command, path, status))
        if status == 200 and content_type.startswith('text/html'):
            if path == '/':
                account = f'<a href="{HISTORY}">Account history</a>' if self.session() else ''
                content = f"""
                <a href="{MISSING}">Missing page</a><a href="{EXCLUDED}">Excluded page</a>
                {account}<button id="details" type="button" aria-expanded="false">Show completion link</button>
                <div id="completion-link"></div><script>
                const details = document.querySelector('#details');
                details.addEventListener('click', event => {{
                    if (!event.isTrusted) throw Error('Expected browser input');
                    details.setAttribute('aria-expanded', 'true');
                    document.querySelector('#completion-link').innerHTML =
                        '<a href="{COMPLETION}">Complete procedure</a>';
                }});
                </script>
                """
                body = body.replace(b'</main>', content.encode() + b'</main>')
            elif path == '/help':
                css = b'<style>body.help-page footer a {color: #ddd}</style>'
                body = body.replace(b'</head>', css + b'</head>').replace(b'<body>', b'<body class="help-page">')
        super().send(status, body, content_type, cookie)


def config(base, budget=20):
    return {
        'schema_version': '1', 'url': base, 'level': 'AA',
        'scope': {'mode': 'discover', 'include': ['/**'], 'seeds': ['/'], 'known_pages': ['/unlinked'],
                  'max_pages': budget, 'exclude': [{'path': '/excluded/**', 'reason': 'Owned fixture boundary'}],
                  'same_document_fragments': ['main'], 'same_document_fragment_reason':
                      'The shared skip link moves to main within the current document.'},
        'environments': [{'id': 'desktop', 'viewport': VIEWPORT, 'zoom': 1}],
    }


def run_selection(out, name, settings, private_config=None):
    config_file = private_config or out / f'{name}-config.json'
    result_file = out / f'{name}.json'
    write_json(config_file, settings)
    process = subprocess.run([sys.executable, str(SKILL / 'scripts/audit.py'), 'pages',
                              '--config', str(config_file), '--out', str(result_file)],
                             capture_output=True, text=True, timeout=60, check=True)
    assert json.loads(process.stdout)['wcag_inspection_executed'] is False
    result = json.loads(result_file.read_text())
    assert result['inventory_complete'] is False
    return result


async def compare_shared_footer(page, base):
    results = {}
    for path in ('/', '/media', '/help'):
        await page.goto(base + path)
        footer = page.locator('footer')
        link = footer.get_by_role('link', name='Help')
        color = await link.evaluate('(node) => getComputedStyle(node).color')
        proof = {
            'markup_sha256': sha256((await footer.evaluate('(node) => node.outerHTML')).encode()).hexdigest(),
            'aria_snapshot': await footer.aria_snapshot(),
            'link_color': color,
            'current_navigation': await page.locator('header nav a[aria-current="page"]').get_attribute('href'),
        }
        await page.add_script_tag(path=str(SKILL / 'vendor/axe.min.js'))
        proof['contrast'] = await page.evaluate("""async () => {
            const evidence = await axe.run(document.querySelector('footer a'), {runOnly: ['color-contrast']});
            return {
                violations: evidence.violations.map(rule => rule.nodes.map(node => node.target)),
                passes: evidence.passes.map(rule => rule.nodes.map(node => node.target)),
            };
        }""")
        results[path] = proof
    assert len({sample['markup_sha256'] for sample in results.values()}) == 1
    assert len({sample['aria_snapshot'] for sample in results.values()}) == 1
    assert set(sample['current_navigation'] for sample in results.values()) == set(results)
    assert results['/']['link_color'] == results['/media']['link_color'] != results['/help']['link_color']
    assert all(results[path]['contrast']['passes'] and not results[path]['contrast']['violations'] for path in ('/', '/media'))
    assert results['/help']['contrast']['violations'] and not results['/help']['contrast']['passes']
    return results


async def observe(base, storage_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=shutil.which('chromium'))
        context = await browser.new_context(viewport=VIEWPORT, service_workers='block')
        try:
            async def guard(route):
                request = route.request
                url = urlsplit(request.url)
                allowed = (url.scheme, url.netloc) == ('http', urlsplit(base).netloc) and (
                    request.method == 'GET' or (request.method == 'POST' and url.path == '/api/login'))
                await (route.continue_() if allowed else route.abort())

            await context.route('**/*', guard)
            await context.route_web_socket('**/*', lambda ws: ws.close())
            page = await context.new_page()
            await page.goto(base + '/profile')
            await expect(page.locator('#signed-out')).to_be_visible()
            assert await page.locator('#profile-form').count() == 0
            profile_states = [{'state': 'signed-out', 'url': page.url, 'target': '#signed-out'}]
            await page.goto(base)
            complete_link = page.get_by_role('link', name='Complete procedure')
            assert await complete_link.count() == 0 and await page.get_by_role('link', name='Account history').count() == 0
            procedure = [{'state': 'initial', 'url': page.url}]
            await page.get_by_role('button', name='Show completion link').click()
            await expect(complete_link).to_be_visible()
            assert await complete_link.get_attribute('href') == COMPLETION
            procedure.append({'state': 'revealed', 'url': page.url, 'target': base + COMPLETION})
            await complete_link.click()
            await expect(page.get_by_role('heading', name='Procedure complete')).to_be_visible()
            assert page.url == base + COMPLETION
            procedure.append({'state': 'completed', 'url': page.url})
            await page.get_by_role('link', name='Return to Home').click()
            assert page.url == base + '/' and await complete_link.count() == 0
            procedure.append({'state': 'returned', 'url': page.url})
            components = await compare_shared_footer(page, base)

            email = await page.locator('#demo-email').inner_text()
            password = await page.locator('#demo-password').inner_text()
            await page.goto(base + '/login')
            await page.locator('#login-email').fill(email)
            await page.locator('#password').fill(password)
            await page.get_by_role('button', name='Sign in').click()
            await expect(page.locator('#login-status')).to_have_text('Signed in. Continue to profile.')
            await page.get_by_role('link', name='Continue to profile').click()
            await expect(page.locator('#profile-form')).to_be_visible()
            profile_states.append({'state': 'signed-in', 'url': page.url, 'target': '#profile-form'})
            assert profile_states[0]['url'] == profile_states[1]['url'] == base + '/profile'
            await page.goto(base)
            history = page.get_by_role('link', name='Account history')
            await expect(history).to_be_visible()
            await history.click()
            await expect(page.get_by_role('heading', name='Account history')).to_be_visible()
            assert page.url == base + HISTORY
            await context.storage_state(path=storage_file)
            return procedure, profile_states, components, browser.version
        finally:
            await context.close()
            await browser.close()


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    server, worker = start_server(SelectionFixture)
    server.observed_requests = []
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        limited = run_selection(out, 'limited', config(base, budget=1))
        anonymous = run_selection(out, 'anonymous', config(base))
        assert set(limited['unvisited']) == {base + path for path in PUBLIC if path != '/'}
        assert {row['url'] for row in anonymous['pages']} == {base + path for path in PUBLIC}
        assert anonymous['errors'] == [{'url': base + MISSING, 'error': 'HTTP 404'}]
        assert not anonymous['unvisited']

        with TemporaryDirectory() as scratch:
            auth_file = Path(scratch) / 'auth.json'
            procedure, profile_states, components, browser = asyncio.run(observe(base, auth_file))
            authenticated_config = config(base)
            authenticated_config['auth_state'] = str(auth_file)
            authenticated = run_selection(out, 'authenticated', authenticated_config, Path(scratch) / 'config.json')
        auth_pages = {row['url']: row for row in authenticated['pages']}
        assert set(auth_pages) == {base + path for path in (*PUBLIC, HISTORY)}
        assert auth_pages[base + HISTORY]['source'] == base + '/'
        assert authenticated['errors'] == anonymous['errors'] and not authenticated['unvisited']

        selected = [dict(url=row['url'], access='failed_http_404' if row['url'] == base + MISSING else 'visited',
                         source=row['source'], reason='finite in-scope fixture census',
                         states=['initial', 'revealed', 'returned'] if row['url'] == base + '/' else ['initial'],
                         session='authenticated' if row['url'] == base + HISTORY else 'anonymous',
                         audit='not_run') for row in anonymous['pages'] + [auth_pages[base + HISTORY]]]
        profile = next(row for row in selected if row['url'] == base + '/profile')
        profile['states'] = [sample['state'] for sample in profile_states]
        selected.append(dict(url=base + COMPLETION, source='observed operation', access='reached_after_operation',
                             reason='completion target of the observed procedure', states=['completed'],
                             session='anonymous', audit='not_run'))
        excluded = [{'url': base + EXCLUDED, 'reason': 'outside fixture scope'}]
        assert not any(path == EXCLUDED for _, path, _ in server.observed_requests)
        assert sum(method == 'POST' for method, _, _ in server.observed_requests) == 1

        handoff = config(base)
        handoff['scope'].update(mode='configured', pages_file='selected-urls.json')
        write_json(out / 'selected-urls.json', {'pages': [row['url'] for row in selected]})
        before = len(server.observed_requests)
        configured = run_selection(out, 'handoff', handoff)
        assert len(server.observed_requests) == before
        assert [row['url'] for row in configured['pages']] == [row['url'] for row in selected]
        assert all(row == {'url': row['url'], 'source': 'configured', 'visited': False} for row in configured['pages'])
        assert {state['url'] for state in procedure} <= {row['url'] for row in selected}

        report = {
            'scope': config(base), 'browser': browser, 'selection_policy': 'all known fixture URLs within scope',
            'pages': selected, 'excluded': excluded, 'procedure': procedure, 'shared_footer': components,
            'profile_states': profile_states,
            'anonymous_candidates': len(anonymous['pages']), 'authenticated_candidates': len(auth_pages),
            'not_yet_visited': limited['unvisited'], 'configured_pages': len(configured['pages']),
            'site_conformance': None,
        }
        write_json(out / 'selection-packet.json', report)
        print(json.dumps({key: report[key] for key in ('anonymous_candidates', 'authenticated_candidates',
                                                      'configured_pages', 'site_conformance')}))
    finally:
        stop_server(server, worker)
        site.SESSIONS.clear()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
