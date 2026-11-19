"""Check machine-only screenshot choices and report links in Chromium."""
import argparse
import asyncio
import contextlib
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
from struct import unpack
import sys
from threading import Thread
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/wcag-audit-kit/scripts'))
import audit
import page_explorer


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        filler = '<p style="margin-top:1800px">Below the first viewport</p>' if self.path == '/long' else ''
        page = f"""<!doctype html>
<html lang="en"><head><title>Image evidence</title></head><body><main>
<h1>Image evidence</h1>
<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7">
<button onclick="document.querySelector('#result').hidden=false">Open details</button>
<p id="result" hidden>Details are open.</p>{filler}
</main></body></html>""".encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(page)))
        self.end_headers()
        self.wfile.write(page)


def invoke(out, label, command, expected=0):
    with (out / f'{label}.stdout.txt').open('w') as stdout, (out / f'{label}.stderr.txt').open('w') as stderr:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = audit.main(command)
    assert code == expected, (command, (out / f'{label}.stderr.txt').read_text())


def result(root):
    run = audit.run_layout.ledger(root)
    files = audit.run_layout.report_files(run, single=True)
    value = audit.load(files.json)
    assert value['verification']['mode'] == 'machine'
    assert not value['audit_complete']
    assert any(check['checkpoint'] == 'axe / image-alt' and check['outcome'] == 'failed' for check in value['machine_checks'])
    images = [item for item in value['observation_usage']['screenshots'] if item['status'] == 'captured']
    assert {run / item['path'] for item in images} == set(run.rglob('*.png'))
    return run, files, images


async def check_report(files, paths):
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        try:
            page = await browser.new_page(viewport={'width': 320, 'height': 900})
            await page.goto(files.html.as_uri())
            await page.get_by_role('link', name='画面の証拠画像', exact=True).click()
            section = page.locator('#evidence-images')
            if await section.get_attribute('open') is None:
                await section.locator('summary').click()
            links = section.get_by_role('link')
            assert await links.count() == len(paths)
            hrefs = await links.evaluate_all('(links) => links.map(link => link.href)')
            assert {Path(unquote(urlsplit(href).path)).resolve() for href in hrefs} == paths
            for href in hrefs:
                await page.goto(href)
                assert await page.locator('img').evaluate('(image) => image.complete && image.naturalWidth > 0')
        finally:
            await browser.close()


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    origin = f'http://127.0.0.1:{server.server_port}'
    try:
        url = origin + '/long'
        config = audit.init_config(url)
        config['environments'] = config['environments'][:2]
        config['keyboard_steps'] = 2
        config_path = out / 'config.json'
        audit.save(config_path, config)
        initial = ['page-audit', '--url', url, '--config', str(config_path), '--out', str(out / 'initial')]
        common = ['--mode', 'machine', '--level', 'A', '--screenshots', 'initial']
        invoke(out, 'initial', initial + common + ['--max-steps', '4', '--max-states', '6', '--max-depth', '1'])
        run, files, images = result(out / 'initial')
        assert audit.run_meta(run)['config']['level'] == 'A'
        assert len(images) == 2 and all(item['kind'] == 'initial' for item in images)
        dimensions = {item['environment']: unpack('>II', (run / item['path']).read_bytes()[16:24]) for item in images}
        assert dimensions == {'desktop': (1280, 900), 'narrow': (320, 900)}, dimensions
        assert page_explorer.status(run)['steps'] > 2
        paths = {(run / item['path']).resolve() for item in images}
        asyncio.run(check_report(files, paths))

        protected = [run / 'run.json', run / 'capture-manifest.json', *sorted(paths)]
        before = [sha256(path.read_bytes()).digest() for path in protected]
        resume = ['page-audit', '--url', url, '--out', str(out / 'initial'), '--resume']
        invoke(out, 'changed-level', resume + ['--level', 'AAA'], expected=1)
        invoke(out, 'changed-screenshots', resume + ['--screenshots', 'all'], expected=1)
        assert before == [sha256(path.read_bytes()).digest() for path in protected]
        invoke(out, 'resume', resume + ['--max-steps', '6', '--max-states', '8', '--max-depth', '1'])
        continued, _, images = result(out / 'initial')
        assert {(continued / item['path']).resolve() for item in images} == paths
        assert before[0] == sha256((run / 'run.json').read_bytes()).digest()
        assert before[2:] == [sha256(path.read_bytes()).digest() for path in sorted(paths)]

        short_url = origin + '/short'
        config = audit.init_config(short_url)
        config['environments'] = config['environments'][:1]
        config['keyboard_steps'] = 2
        config['verification'] = {'mode': 'machine'}
        config['inspection'] = {'profile': 'quick', 'screenshots': 'off', 'max_images': 0}
        short_config = out / 'short-config.json'
        audit.save(short_config, config)
        for choice in ('states', 'all'):
            invoke(out, choice, ['page-audit', '--url', short_url, '--config', str(short_config),
                                 '--out', str(out / choice), '--screenshots', choice,
                                 '--max-states', '4', '--max-steps', '4', '--max-depth', '1'])
            run, _, images = result(out / choice)
            assert audit.run_meta(run)['config']['inspection']['screenshots'] == choice
            kinds = {item['kind'] for item in images}
            assert kinds >= {'initial', 'state'}, kinds
            if choice == 'all':
                assert kinds >= {'action-before', 'action-after'}, kinds
                assert any(item.get('label', '').startswith('クリック')
                           for item in images if item['kind'] == 'action-before')
                pairs = {}
                for item in images:
                    pairs.setdefault((run / item['path']).parent, set()).add(item['kind'])
                assert any({'action-before', 'action-after'} <= captured for captured in pairs.values())
            else:
                assert kinds == {'initial', 'state'}, kinds

        config['states'] = [{'id': 'opened', 'paths': ['/short'],
                             'actions': [{'type': 'click', 'selector': 'button'}],
                             'assert': [{'selector': '#result', 'visible': True}]}]
        audit.save(short_config, config)
        invoke(out, 'declared', ['page', '--url', short_url, '--config', str(short_config),
                                 '--out', str(out / 'declared')] + common)
        run, _, images = result(out / 'declared')
        assert len(images) == 1 and images[0]['kind'] == 'initial'
        assert {item['state'] for item in audit.load(run / 'capture-manifest.json')['captures']} == {'initial', 'opened'}
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
