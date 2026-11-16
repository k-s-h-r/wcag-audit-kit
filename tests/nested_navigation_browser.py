"""Exercise the three-level fixture with real keys; not an audit detector."""
import argparse
import asyncio
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks import core,runner


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    for sc in ['2.1.1','2.1.2','2.4.3']:
        shutil.copytree(core.ROOT/'benchmarks/cases'/sc/'public',out/'public'/sc)
    server=runner.server(out/'public');base=f'http://127.0.0.1:{server.server_port}'
    trace=[];results=[];errors=[]
    async def exercise():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
            try:
                page=await browser.new_page(viewport={'width':1280,'height':900})
                page.on('pageerror',lambda e:errors.append(str(e)))
                async def record(action):
                    row=await page.evaluate('''()=>({url:location.href,focus:document.activeElement.id||document.activeElement.tagName,
                        documentHasFocus:document.hasFocus(),rootExpanded:document.querySelector('#level1')?.getAttribute('aria-expanded')??null,
                        childExpanded:document.querySelector('#level2')?.getAttribute('aria-expanded')??null,
                        secondVisible:document.querySelector('#level2-panel')?.hidden===false,
                        thirdVisible:document.querySelector('#level3-panel')?.hidden===false})''')
                    trace.append(dict(action=action,**row));return row
                async def key(name,focus=None):
                    await page.keyboard.press(name);row=await record(name)
                    if focus:assert row['focus']==focus,(name,focus,row)
                    return row
                async def open_path(sc,name):
                    await page.goto(f'{base}/{sc}/{name}');await record('load')
                    await key('Tab','before');await key('Tab','level1');await key('Enter','level1')
                    assert await page.locator('#level2-panel').is_visible()
                    assert not await page.locator('#level3-panel').is_visible()
                    await key('Tab','level2');return await key('Enter')
                async def activate_leaf(method):
                    async with page.expect_navigation(wait_until='domcontentloaded'):
                        if method=='keyboard':await page.keyboard.press('Enter')
                        else:await page.locator('#leaf').click()
                    assert page.url.endswith('/destination.html')
                    assert await page.locator('h1').inner_text()=='見積管理'
                    await record(method+' leaf activation: destination reached')

                for sc,name in [('2.1.1','p04.html'),('2.1.2','p03.html'),('2.4.3','p03.html')]:
                    row=await open_path(sc,name);assert row['focus']=='level2' and row['thirdVisible']
                    await key('Tab','leaf');await key('Tab','other-leaf');await key('Shift+Tab','leaf')
                    await page.screenshot(path=str(out/(sc+'-third-level.png')))
                    row=await key('Escape','level2');assert not row['thirdVisible'] and row['rootExpanded']=='true'
                    row=await key('Escape','level1');assert not row['secondVisible'] and row['rootExpanded']=='false'
                    await key('Tab','help');await key('Tab','after')
                    await key('Shift+Tab','help');await key('Shift+Tab','level1')
                    await key('Space','level1');await key('Tab','level2');await key('Space','level2');await key('Tab','leaf')
                    await activate_leaf('keyboard')
                    results.append(dict(criterion=sc,page=name,fixture='keyboard route, reverse route and destination confirmed'))

                row=await open_path('2.1.1','p05.html');assert row['focus']=='level2' and not row['thirdVisible']
                row=await key('Space','level2');assert not row['thirdVisible']
                await page.locator('#level2').click();row=await record('pointer opens level 2');assert row['thirdVisible']
                await activate_leaf('pointer')
                results.append(dict(criterion='2.1.1',page='p05.html',fixture='keyboard stops at level 2; pointer reaches destination'))

                row=await open_path('2.1.2','p04.html');assert row['thirdVisible']
                await key('Tab','leaf');await key('Tab','other-leaf');await key('Shift+Tab','leaf')
                for name in ['Escape','Enter','Space']:
                    row=await key(name,'leaf');assert row['thirdVisible'] and page.url.endswith('/p04.html')
                for expected in ['other-leaf','leaf']*3:await key('Tab',expected)
                for expected in ['other-leaf','leaf']*2:await key('Shift+Tab',expected)
                await page.screenshot(path=str(out/'trap-third-level.png'))
                await page.locator('#close').click();row=await record('pointer closes trapped panel')
                assert row['focus']=='level1' and not row['thirdVisible']
                await key('Tab','help');await key('Tab','after')
                results.append(dict(criterion='2.1.2',page='p04.html',fixture='third-level trap and pointer-only escape confirmed'))

                row=await open_path('2.4.3','p04.html')
                assert row['thirdVisible'] and row['focus']=='after'
                await page.screenshot(path=str(out/'focus-jump.png'))
                await activate_leaf('pointer')
                results.append(dict(criterion='2.4.3',page='p04.html',fixture='third level opens but focus jumps beyond navigation'))
                assert not errors,errors
            finally:await browser.close()
    try:asyncio.run(exercise())
    finally:server.shutdown();server.server_close()
    core.save(out/'observed.json',dict(scope='fixture behaviour, not detector accuracy',corpus_digest=core.corpus()['digest'],results=results,trace=trace,javascript_errors=errors))
    print(f'Confirmed {len(results)} fixture routes and {len(trace)} actual key/action observations.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();main(args.out)
