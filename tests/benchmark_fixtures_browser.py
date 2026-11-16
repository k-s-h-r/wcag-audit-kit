"""Sanity-check the authored fixture behaviours separately from detector scoring."""
import argparse
import asyncio
from pathlib import Path
import sys
import threading
from functools import partial
from http.server import ThreadingHTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks import core,runner


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    # Expose the same public-only layout used by the benchmark collector.
    import shutil
    public=out/'public'
    for directory in (core.ROOT/'benchmarks/cases').iterdir():
        if directory.is_dir():shutil.copytree(directory/'public',public/directory.name)
    http=runner.server(public);base=f'http://127.0.0.1:{http.server_port}';observed=[]
    async def check():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
            try:
                page=await browser.new_page(viewport={'width':1280,'height':900})
                for i in [1,2,3]:
                    url=f'{base}/2.1.1/p0{i}.html';await page.goto(url);await page.locator('#control').click()
                    assert await page.locator('#counter').inner_text()=='1'
                    await page.goto(url)
                    for _ in range(12):
                        await page.keyboard.press('Tab')
                        if await page.locator('#control').evaluate('(e)=>e===document.activeElement'):break
                    assert await page.locator('#control').evaluate('(e)=>e===document.activeElement')
                    await page.keyboard.press('Enter');count=await page.locator('#counter').inner_text()
                    assert count==('0' if i==2 else '1'),count
                    observed.append({'criterion':'2.1.1','page':f'p0{i}.html','pointer_value':'1','keyboard_value':count})
                for i in [1,2]:
                    await page.goto(f'{base}/2.1.2/p0{i}.html');await page.locator('#open').click()
                    await page.keyboard.press('Tab');await page.keyboard.press('Shift+Tab');await page.keyboard.press('Escape')
                    visible=await page.locator('#panel').is_visible();assert visible==(i==2)
                    observed.append({'criterion':'2.1.2','page':f'p0{i}.html','visible_after_escape':visible})
                menus=[]
                for i in range(1,5):
                    await page.goto(f'{base}/3.2.3/p0{i}.html');menus.append(await page.locator('#menu a').all_text_contents())
                assert menus[0]==menus[1] and menus[2]!=menus[3]
                observed.append({'criterion':'3.2.3','menus':menus})
                for i in [1,2]:
                    await page.goto(f'{base}/1.2.2/p0{i}.html');await page.locator('#captions').click();await page.locator('#play').click()
                    await page.wait_for_timeout(1200)
                    track=await page.locator('#media').evaluate('(v)=>({mode:v.textTracks[0].mode,cues:[...v.textTracks[0].activeCues||[]].map(c=>c.text),time:v.currentTime})')
                    assert track['time']>0 and track['mode']==('showing' if i==1 else 'hidden')
                    # Hidden tracks still expose activeCues; only showing draws captions.
                    assert track['cues']
                    await page.screenshot(path=str(out/f'captions-{i}.png'))
                    observed.append({'criterion':'1.2.2','page':f'p0{i}.html','track':track})
                for i in [1,2]:
                    await page.goto(f'{base}/4.1.3/p0{i}.html');await page.locator('#record').click()
                    assert await page.locator('#notice').inner_text()=='記録しました。'
                    role=await page.locator('#notice').get_attribute('role');assert role==('status' if i==1 else None)
                    observed.append({'criterion':'4.1.3','page':f'p0{i}.html','role':role,'scope':'DOM sanity only; actual speech not inferred'})
                await page.goto(f'{base}/1.1.1/p02.html');await page.screenshot(path=str(out/'non-text.png'),full_page=True)
                assert (await page.request.get(base+'/1.1.1/suite.json')).status==404
                assert (await page.request.get(base+'/../oracle.snapshot.json')).status==404
                assert (await page.request.get(base+'/')).status==404
            finally:await browser.close()
    try:
        asyncio.run(check());core.save(out/'observed.json',{'scope':'fixture sanity, not detector accuracy','observed':observed,'oracle_not_served':True})
        print('Fixture behaviours and public-only serving checked.')
    finally:http.shutdown();http.server_close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args();main(args.out)
