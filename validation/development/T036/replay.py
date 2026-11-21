"""Record the explicit, real-browser exit routes for the nested-dialog fixtures."""
import argparse
import asyncio
from pathlib import Path
import shutil
import sys

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from benchmarks import core, runner

from input_observation import INIT_SCRIPT, InputObserver
from keyboard_checks import matching_keydown

CASES = {'045': 'p07.html', '046': 'p08.html'}
WIDTHS = {'desktop': {'width': 1280, 'height': 900}, 'narrow': {'width': 320, 'height': 900}}
PARENT = ['outer']
BOTH = ['outer', 'subject']
BODY = []
CYCLES = {
    '045': {'Tab': ['building', 'inner-name'] * 3, 'Shift+Tab': ['building', 'inner-name'] * 3},
    '046': {'Tab': ['building', 'inner-close', 'inner-name'] * 2,
            'Shift+Tab': ['inner-close', 'building', 'inner-name'] * 2},
}
EXTRA_FIELD_KEYS = ('ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Enter', 'Space', 'Backspace')
SNAPSHOT = """() => ({
  url: location.href,
  document_start: performance.timeOrigin,
  modals: ['outer', 'subject'].filter(id => {
    const element = document.getElementById(id);
    return !!element.getClientRects().length && getComputedStyle(element).visibility === 'visible';
  }),
  focus: document.activeElement.id || document.activeElement.localName,
  length: Object.fromEntries(['outer-name', 'inner-name', 'building'].map(id =>
    [id, document.getElementById(id).value.length]))
})"""


class Trial:
    def __init__(self, page, observer, directory, initial):
        self.page = page
        self.observer = observer
        self.directory = directory
        self.initial = initial
        self.current = initial
        self.steps = []

    async def record(self, operation, focus, modals, *, length=0, label=None):
        before = self.current
        first = len(self.observer.events)
        if 'key' in operation:
            await self.page.keyboard.press(operation['key'])
        else:
            await self.page.locator('#' + operation['mouse_target']).click(timeout=2000)
        after = await self.page.evaluate(SNAPSHOT)
        assert after['modals'] == modals and after['focus'] == focus, (operation, after)
        assert after['url'] == self.initial['url'] and after['document_start'] == self.initial['document_start']
        assert after['length'] == {id: length if id == focus else 0 for id in after['length']}, (operation, after)
        events = self.observer.events[first:]
        if 'key' in operation:
            candidates = [(i + first, event) for i, event in enumerate(events)
                          if matching_keydown(event, operation['key'])
                          and (event['target']['id'] or event['target']['tag']) == before['focus']]
        else:
            candidates = [(i + first, event) for i, event in enumerate(events)
                          if event['type'] == 'click' and event['isTrusted'] and event['is_main_frame']
                          and event['pointerType'] == 'mouse' and event['target']['id'] == operation['mouse_target']]
        (index, event), = candidates
        assert event['url'] == self.initial['url'] and not self.observer.dropped
        if self.steps:
            assert event['documentId'] == self.observer.events[self.steps[0]['event_index']]['documentId']
        step = dict(operation, label=label, event_index=index, before=before, after=after)
        if label in {'inner-open', 'after-inner-exit', 'after-outer-exit'}:
            image = label + '.png'
            await self.page.screenshot(path=str(self.directory / image), animations='disabled')
            step['image'] = image
        self.steps.append(step)
        self.current = after

    async def open_both(self):
        for key, focus, modals, label in (
            ('Tab', 'launch', BODY, None),
            ('Enter', 'outer-name', PARENT, 'outer-open'),
            ('Tab', 'inner-opener', PARENT, None),
            ('Enter', 'inner-name', BOTH, 'inner-open'),
        ):
            await self.record({'key': key}, focus, modals, label=label)

    async def close_parent(self):
        await self.record({'key': 'Escape'}, 'launch', BODY, label='after-outer-exit')
        await self.record({'key': 'Tab'}, 'outside', BODY, label='next-body-control')


async def keyboard_trial(trial, case):
    for key, destinations in CYCLES[case].items():
        for focus in destinations:
            await trial.record({'key': key}, focus, BOTH, label='tab-cycle')
    if case == '046':
        await trial.record({'key': 'Escape'}, 'inner-opener', PARENT, label='after-inner-exit')
    else:
        for focus in ('inner-name', 'building'):
            await trial.record({'key': 'Escape'}, focus, BOTH, label='inner-escape-retained')
            for key in EXTRA_FIELD_KEYS:
                await trial.record({'key': key}, focus, BOTH, length=int(key == 'Space'), label='input-field')
            key = 'Tab' if focus == 'inner-name' else 'Shift+Tab'
            next_field = 'building' if focus == 'inner-name' else 'inner-name'
            await trial.record({'key': key}, next_field, BOTH)
        await trial.record({'mouse_target': 'inner-close'}, 'inner-opener', PARENT, label='after-inner-exit')
    await trial.close_parent()


async def alternate_trial(trial, route):
    if route == 'enter-close':
        await trial.record({'key': 'Tab'}, 'building', BOTH)
        await trial.record({'key': 'Tab'}, 'inner-close', BOTH)
        await trial.record({'key': 'Enter'}, 'inner-opener', PARENT, label='after-inner-exit')
    else:
        await trial.record({'mouse_target': 'inner-close'}, 'inner-opener', PARENT, label='after-inner-exit')
    await trial.close_parent()


async def collect(browser, output, url, case, environment, route):
    context = await browser.new_context(viewport=WIDTHS[environment], locale='ja-JP', service_workers='block')
    try:
        directory = output / 'browser' / case / environment / route
        directory.mkdir(parents=True)
        observer = InputObserver()
        requests = []
        await context.expose_binding('__wcagAuditInput', observer.accept)
        await context.add_init_script(INIT_SCRIPT)

        async def only_fixture(request_route):
            request = request_route.request
            allow = request.method == 'GET' and request.url == url and request.is_navigation_request()
            requests.append(dict(url=request.url, method=request.method, allow=allow))
            if allow:
                await request_route.continue_()
            else:
                await request_route.abort()

        await context.route('**/*', only_fixture)
        page = await context.new_page()
        response = await page.goto(url, wait_until='load')
        assert response.status == 200
        before = await page.evaluate(SNAPSHOT)
        assert before['focus'] == 'body' and before['modals'] == BODY
        trial = Trial(page, observer, directory, before)
        await trial.open_both()
        if route == 'keyboard':
            await keyboard_trial(trial, case)
        else:
            await alternate_trial(trial, route)
        assert [r for r in requests if r['allow']] == [dict(url=url, method='GET', allow=True)]
        core.save(directory / 'network.json', requests)
        core.save(directory / 'input-events.json', observer.export())
        core.save(directory / 'steps.json', trial.steps)
        return dict(case=case, environment=environment, route=route, steps=len(trial.steps),
                    evidence=directory.relative_to(output).as_posix(),
                    exits=[state for state in trial.steps if state['label'] in {
                        'inner-escape-retained', 'after-inner-exit', 'after-outer-exit', 'next-body-control'}])
    finally:
        await context.close()


async def run(output, origin):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=shutil.which('chromium'))
        try:
            results = []
            for case, filename in CASES.items():
                for env in WIDTHS:
                    routes = ('keyboard',) if case == '045' else ('keyboard', 'enter-close', 'pointer-close')
                    for route in routes:
                        result = await collect(browser, output, origin + '/' + filename, case, env, route)
                        results.append(result)
                        print(case, env, route, result['steps'], flush=True)
        finally:
            await browser.close()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    public = output / 'public'
    public.mkdir(parents=True)
    for filename in CASES.values():
        shutil.copyfile(ROOT / 'benchmarks/cases/2.1.2/public' / filename, public / filename)
    core.save(output / 'plan.json', dict(
        started=core.timestamp(), environment=runner.environment(),
        public_sha256={p.name: core.file_hash(p) for p in sorted(public.iterdir())},
        widths=WIDTHS, tab_cycles=CYCLES, additional_field_keys=EXTRA_FIELD_KEYS,
        path_to_open=['Tab', 'Enter', 'Tab', 'Enter'],
        routes={'045': ['keyboard followed by mouse exit'], '046': ['keyboard', 'enter-close', 'pointer-close']},
    ))
    server = runner.server(public)
    try:
        results = asyncio.run(run(output, f'http://127.0.0.1:{server.server_port}'))
    finally:
        server.shutdown()
        server.server_close()
    core.save(output / 'observed.json', results)


if __name__ == '__main__':
    main()
