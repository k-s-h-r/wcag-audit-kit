"""Exercise the owned Profile demo from readiness to logout and teardown."""
import argparse
import asyncio
import hashlib
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import socket
import threading
from urllib.parse import urlsplit
from urllib.request import urlopen

from fixtures import audit_site_server as site


ROOT = Path(__file__).resolve().parents[1]
TEST_NAME = 'Procedure Example'
TEST_EMAIL = 'procedure@example.test'
WRITES = ['/api/login', '/api/profile', '/api/logout']


async def exercise(base, output, stages, inputs):
    from playwright.async_api import async_playwright, expect

    origin = urlsplit(base).netloc
    expected_keys = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=shutil.which('chromium'))
        context = await browser.new_context(viewport={'width': 1280, 'height': 900}, service_workers='block')
        context.set_default_timeout(5000)
        try:
            async def guard(route):
                request = route.request
                url = urlsplit(request.url)
                if (url.scheme == 'http' and url.netloc == origin and
                        (request.method == 'GET' or (request.method == 'POST' and url.path in WRITES))):
                    await route.continue_()
                else:
                    await route.abort()

            await context.route('**/*', guard)
            await context.route_web_socket('**/*', lambda ws: ws.close())
            await context.expose_binding('__routeInput', lambda _, event: inputs.append(event))
            await context.add_init_script("""addEventListener('keydown', event => {
                if (event.key === 'Tab' || event.key === 'Enter')
                    void window.__routeInput({
                        key: event.key, trusted: event.isTrusted,
                        target: event.target.id, path: location.pathname
                    });
            }, {capture: true});""")
            page = await context.new_page()

            async def press(key):
                expected_keys.append(key)
                await page.keyboard.press(key)

            async def tab_to(selector):
                for _ in range(20):
                    if await page.evaluate('(selector) => document.activeElement.matches(selector)', selector):
                        return
                    await press('Tab')
                raise AssertionError(f'Tabで対象に到達できない: {selector}')

            async def replace_text(selector, value):
                await tab_to(selector)
                await page.keyboard.press('Control+a')
                await page.keyboard.insert_text(value)

            async def record(name, selector):
                locator = page.locator(selector)
                await expect(locator).to_be_visible()
                stages.append(dict(stage=name, path=await page.evaluate('location.pathname'),
                                   text=await locator.inner_text(),
                                   focus=await page.evaluate('document.activeElement.id')))

            await page.goto(base + '/profile')
            await record('signed-out', '#signed-out')
            await expect(page.locator('#profile-form')).to_have_count(0)
            await page.goto(base + '/help')
            email = await page.locator('#demo-email').inner_text()
            password = await page.locator('#demo-password').inner_text()
            await page.goto(base + '/login')
            await replace_text('#login-email', email)
            await replace_text('#password', password)
            await tab_to('#sign-in')
            await press('Enter')
            await expect(page.locator('#login-status')).to_have_text('Signed in. Continue to profile.')
            await record('signed-in', '#login-status')
            await tab_to('#main a[href="/profile"]')
            await press('Enter')
            await expect(page.locator('#profile-form')).to_be_visible()

            await replace_text('#name', TEST_NAME)
            await replace_text('#email', TEST_EMAIL)
            await tab_to('#review')
            await press('Enter')
            await expect(page.locator('#review-name')).to_have_text(TEST_NAME)
            await expect(page.locator('#review-email')).to_have_text(TEST_EMAIL)
            await record('review', '#review-panel')
            await expect(page.locator('#review-title')).to_be_focused()

            await tab_to('#back')
            await press('Enter')
            await expect(page.locator('#name')).to_have_value(TEST_NAME)
            await expect(page.locator('#email')).to_have_value(TEST_EMAIL)
            await record('back-to-edit', '#editor')
            await expect(page.locator('#name')).to_be_focused()

            await tab_to('#review')
            await press('Enter')
            await tab_to('#confirm')
            await press('Enter')
            await expect(page.locator('#saved-name')).to_have_text(TEST_NAME)
            await expect(page.locator('#saved-email')).to_have_text(TEST_EMAIL)
            await record('saved', '#completion')
            await expect(page.locator('#saved-title')).to_be_focused()
            await page.screenshot(path=str(output / 'saved.png'))

            await tab_to('#sign-out')
            await press('Enter')
            await record('signed-out-again', '#signed-out')
            await expect(page.locator('#profile-form')).to_have_count(0)
            await page.screenshot(path=str(output / 'signed-out.png'))
            assert [event['key'] for event in inputs] == expected_keys and all(event['trusted'] for event in inputs)
            return browser.version
        finally:
            await context.close()
            await browser.close()


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    requests, stages, inputs = [], [], []

    class Handler(site.Handler):
        def log_message(self, *_):
            pass

        def send(self, status, body, *args, **kwargs):
            requests.append(dict(method=self.command, path=urlsplit(self.path).path, status=status))
            return super().send(status, body, *args, **kwargs)

    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        host, port = server.server_address
        base = f'http://{host}:{port}'
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with urlopen(base + '/login', timeout=5) as response:
                assert response.status == 200 and b'id="login-form"' in response.read()
            browser = asyncio.run(exercise(base, output, stages, inputs))
        finally:
            server.shutdown()
            worker.join(timeout=5)
            site.SESSIONS.clear()
    assert not worker.is_alive() and not site.SESSIONS
    with socket.socket() as connection:
        connection.settimeout(2)
        assert connection.connect_ex((host, port)) != 0
    assert [(item['path'], item['status']) for item in requests if item['method'] == 'POST'] == [
        (path, 200) for path in WRITES
    ], requests
    evidence = {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                for name in ('saved.png', 'signed-out.png')}
    files = [Path(site.__file__), *sorted(site.ROOT.iterdir())]
    source = {file.relative_to(ROOT).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
              for file in files if file.is_file()}
    printout = dict(browser=browser, base_url=base, stages=stages, trusted_inputs=inputs, requests=requests,
                    server_closed=True, sessions_after_cleanup=len(site.SESSIONS),
                    evidence_after_cleanup=evidence, source_sha256=source)
    report = output / 'observed.json'
    report.write_text(json.dumps(printout, ensure_ascii=False, indent=2) + '\n')
    assert json.loads(report.read_text()) == printout
    print(json.dumps(dict(report=str(report), stages=len(stages), trusted_inputs=len(inputs), requests=len(requests))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
