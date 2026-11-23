"""Reproduce each authored trap and focus-order contrast against Chromium."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import asyncio
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmarks.measurements import residual_traps_order


class FixtureHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


async def check_criterion(browser, criterion, base):
    suite = ROOT / 'benchmarks' / 'cases' / criterion / 'suite.json'
    confirmed = 0
    for case in json.loads(suite.read_text())['cases']:
        for state in case['states']:
            plan = state.get('residual_probe')
            if not plan:
                continue
            page_name, = case['pages']
            context = await browser.new_context()
            try:
                page = await context.new_page()
                await page.goto(f'{base}/{criterion}/public/{page_name}')
                evidence = await residual_traps_order.capture(criterion, page, plan)
                result, = residual_traps_order.evaluate(criterion, plan, evidence)
            finally:
                await context.close()
            expected, = [row for row in case['expectations'] if row['state'] == state['id']]
            assert (result['checkpoint'], result['target'], result['outcome']) == (
                expected['checkpoint'], expected['target'], expected['expected']), (criterion, case['id'], result)
            invalid = deepcopy(evidence)
            for route in invalid['routes']:
                route['steps'][-1]['input']['trusted'] = False
            rejected, = residual_traps_order.evaluate(criterion, plan, invalid)
            assert rejected['outcome'] == 'cant_tell', (criterion, case['id'], rejected)
            print(criterion, case['id'], result['outcome'], result['observed'])
            confirmed += 1
    return confirmed


async def run(base):
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        try:
            results = await asyncio.gather(*(check_criterion(browser, criterion, base) for criterion in ('2.1.2', '2.4.3')))
        finally:
            await browser.close()
    assert results == [12, 6], results


if __name__ == '__main__':
    handler = partial(FixtureHandler, directory=ROOT / 'benchmarks' / 'cases')
    with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server, ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(server.serve_forever)
        try:
            asyncio.run(run(f'http://127.0.0.1:{server.server_port}'))
        finally:
            server.shutdown()
            future.result()
