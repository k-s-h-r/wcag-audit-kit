"""Exercise the observer with real Escape on small variations of the published fixture."""
import argparse
import asyncio
from pathlib import Path
import shutil
import sys

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from benchmarks import core, runner
from dialog_focus import SNAPSHOT, DialogFocus
from input_observation import INIT_SCRIPT, InputObserver
from keyboard_checks import matching_keydown

ESCAPE = {'type': 'press', 'selector': 'body', 'key': 'Escape'}
ROUTE = [{'type': 'key', 'selector': '#launch', 'key': 'Enter'},
         {'type': 'key', 'selector': '#inner-opener', 'key': 'Enter'}, ESCAPE]
CASES = {
    'both-closed': ('subject.hidden=true;outer.hidden=true;launch.focus();', [], '#launch'),
    'replaced-child': ('const replacement=subject.cloneNode(true);replacement.hidden=true;'
                       'subject.replaceWith(replacement);opener.focus();', ['#outer'], '#inner-opener'),
    'new-nonmodal': ('closeInner();const other=document.createElement("div");'
                     'other.setAttribute("role","dialog");other.textContent="別の操作";outer.append(other);',
                     ['#outer'], '#inner-opener'),
    'new-shadow-dialog': ('closeInner();const host=document.createElement("div");outer.append(host);'
                          'const other=document.createElement("div");other.setAttribute("role","dialog");'
                          'other.setAttribute("aria-modal","true");other.setAttribute("aria-label","新しいダイアログ");'
                          'other.textContent="別の操作";host.attachShadow({mode:"open"}).append(other);',
                          ['#outer'], '#inner-opener'),
    'new-role-token-dialog': ('closeInner();const other=document.createElement("div");'
                              'other.setAttribute("role","dialog alertdialog");other.setAttribute("aria-modal","true");'
                              'other.setAttribute("aria-label","新しいダイアログ");other.textContent="別の操作";outer.append(other);',
                              ['#outer'], '#inner-opener'),
    'new-display-contents-dialog': ('closeInner();const other=document.createElement("div");'
                                    'other.setAttribute("role","dialog");other.setAttribute("aria-modal","true");'
                                    'other.setAttribute("aria-label","新しいダイアログ");other.style.display="contents";'
                                    'const contents=document.createElement("div");contents.style.position="fixed";'
                                    'contents.textContent="別の操作";other.append(contents);outer.append(other);',
                                    ['#outer'], '#inner-opener'),
    'outside-focus': ('closeInner();outside.focus();', ['#outer'], '#outside'),
    'siblings': ('closeInner();', ['#outer'], '#inner-opener'),
}
WIDTHS = {'desktop': dict(width=1280, height=900), 'narrow': dict(width=320, height=900)}


def copy_controls(public):
    source = (ROOT/'benchmarks/cases/2.1.2/public/p08.html').read_text()
    old = 'e.preventDefault();closeInner();return'
    assert source.count(old) == 1
    for case, (reaction, _, _) in CASES.items():
        copy = source.replace(old, 'e.preventDefault();'+reaction+'return')
        if case == 'siblings':
            setup = (';document.body.append(subject);subject.onkeydown=e=>{'
                     'if(e.key==="Escape"){e.preventDefault();closeInner()}};')
            copy = copy.replace('</script>', setup+'</script>')
        (public/(case+'.html')).write_text(copy, encoding='utf-8')


async def check(browser, out, url, case, width):
    context = await browser.new_context(viewport=WIDTHS[width], locale='ja-JP', service_workers='block')
    observer = InputObserver()
    try:
        await context.expose_binding('__wcagAuditInput', observer.accept)
        await context.add_init_script(INIT_SCRIPT)
        await context.add_init_script(path=ROOT/'skills/wcag-audit-kit/scripts/page_explorer.js')

        async def guard(route):
            if route.request.url == url and route.request.method == 'GET':
                await route.continue_()
            else:
                await route.abort()

        await context.route('**/*', guard)
        page = await context.new_page()
        await page.goto(url)
        for key in ('Tab', 'Enter', 'Tab', 'Enter'):
            await page.keyboard.press(key)
        audit = DialogFocus(page, observer, ROUTE, 'escape')
        assert (await page.evaluate(SNAPSHOT))['focus'] == '#inner-name'
        await audit.before(3, ESCAPE)
        await page.keyboard.press('Escape')
        settled = await page.evaluate('() => window.__wcagWaitForUpdates()')
        await audit.after(3, ESCAPE)
        before = audit.record['before_escape']
        after = audit.record['after_escape']
        _, modals, focus = CASES[case]
        assert settled['status'] == 'quiet' and not observer.dropped
        assert before['modals'] == ['#outer', '#subject'] and before['focus'] == '#inner-name'
        assert after['modals'] == modals and after['focus'] == focus and after['url'] == before['url']
        event = observer.events[audit.record['escape_event_index'] - 1]
        assert matching_keydown(event, 'Escape') and event['target']['id'] == 'inner-name'
        if case == 'outside-focus':
            result = audit.nested_observation
            assert result and result['status'] == 'child_closed' and result['focus_layer'] == 'outside'
        else:
            assert audit.nested_observation is None
        assert audit.record['status'] == 'unconfirmed'
        directory = out/case/width
        directory.mkdir(parents=True)
        core.save(directory/'input-events.json', observer.export())
        core.save(directory/'observed.json', dict(legacy=audit.record, nested=audit.nested_observation))
        if case in {'new-shadow-dialog', 'new-role-token-dialog', 'new-display-contents-dialog'}:
            session = await context.new_cdp_session(page)
            tree = await session.send('Accessibility.getFullAXTree')
            await session.detach()
            assert any(item.get('role', {}).get('value') == 'dialog'
                       and item.get('name', {}).get('value') == '新しいダイアログ'
                       and not item['ignored'] for item in tree['nodes'])
            core.save(directory/'accessibility-tree.json', tree)
        print(case,width,after['modals'],after['focus'],bool(audit.nested_observation),flush=True)
    finally:
        await context.close()


async def run(out, origin):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=shutil.which('chromium'))
        try:
            for case in CASES:
                for width in WIDTHS:
                    await check(browser, out, origin+'/'+case+'.html', case, width)
        finally:
            await browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    out = parser.parse_args().out.resolve()
    public = out/'public'
    public.mkdir(parents=True)
    copy_controls(public)
    core.save(out/'plan.json', dict(fixtures={p.name: core.file_hash(p) for p in sorted(public.iterdir())},
                                   environment=runner.environment(), expectation=CASES, widths=WIDTHS))
    server = runner.server(public)
    try:
        asyncio.run(run(out, f'http://127.0.0.1:{server.server_port}'))
    finally:
        server.shutdown()
        server.server_close()
