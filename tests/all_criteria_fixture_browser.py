"""Check fixture integrity and a few interactive contrasts, not detector accuracy."""
import argparse
import asyncio
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks import core,runner


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    corpus=core.corpus();public=out/'public'
    for suite in corpus['suites']:
        shutil.copytree(core.ROOT/'benchmarks/cases'/suite['criterion']/'public',public/suite['criterion'])
    server=runner.server(public);base=f'http://127.0.0.1:{server.server_port}'
    checked=[];behaviours=[];errors=[]
    async def check():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--mute-audio'])
            try:
                context=await browser.new_context(permissions=['clipboard-read','clipboard-write'])
                page=await context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
                for suite in corpus['suites']:
                    for case in suite['cases']:
                        for name in case['pages']:
                            response=await page.goto(f'{base}/{suite["criterion"]}/{name}')
                            assert response.status==200
                            for e in case['expectations']:
                                if e['page']==name:
                                    count=await page.locator(e['target']).count()
                                    if not count and e['state']!='initial' and case.get('fixture_probe'):continue
                                    assert count==1,(suite['criterion'],name,e['target'])
                            for media in await page.locator('audio[src],video[src],audio:has(source),video:has(source)').all():
                                info=await media.evaluate("""async e=>{if(!e.readyState&&!e.error)await new Promise(resolve=>{e.addEventListener('loadedmetadata',resolve,{once:true});e.addEventListener('error',resolve,{once:true});setTimeout(resolve,3000)});return {source:e.currentSrc,readyState:e.readyState,error:e.error?.code??null}}""")
                                assert info['error'] is None and info['readyState']>=1,(suite['criterion'],name,info)
                            checked.append([suite['criterion'],case['id'],name])
                for i in [1,2]:
                    await page.goto(f'{base}/2.5.7/p0{i}.html')
                    if i==2:await page.get_by_role('button',name='下へ').click()
                    order=await page.locator('#subject li').all_text_contents()
                    assert order[0].startswith('資料A' if i==1 else '資料B')
                    behaviours.append({'criterion':'2.5.7','page':i,'order':order})
                    await page.goto(f'{base}/3.3.7/p0{i}.html')
                    await page.locator('#first').fill('山田');await page.get_by_role('button',name='次へ').click()
                    value=await page.locator('#subject').input_value();assert value==('' if i==1 else '山田')
                    behaviours.append({'criterion':'3.3.7','page':i,'reused':value})
                    for sc in ['3.3.8','3.3.9']:
                        await page.goto(f'{base}/{sc}/p0{i}.html')
                        await page.evaluate("navigator.clipboard.writeText('pass-example')")
                        await page.locator('#subject').focus();await page.keyboard.press('Control+v');await page.wait_for_timeout(100)
                        text=await page.locator('#subject').evaluate('(e)=>e.value??e.textContent')
                        assert text==('' if i==1 else 'pass-example'),(sc,i,text)
                        behaviours.append({'criterion':sc,'page':i,'pasted':bool(text)})
                    for sc in ['1.2.4','1.2.9']:
                        await page.goto(f'{base}/{sc}/p0{i}.html');await page.get_by_role('button',name='配信開始').click()
                        await page.wait_for_timeout(2300)
                        result=await page.locator('#subject').evaluate('(e)=>({live:e.srcObject.getAudioTracks()[0].readyState,seconds:e.currentTime})')
                        caption=await page.locator('#caption').inner_text()
                        assert result['live']=='live' and result['seconds']>0
                        assert caption==('' if i==1 else '確認音')
                        behaviours.append({'criterion':sc,'page':i,'stream':result,'caption':caption})
                assert not errors,errors
                for reference in corpus['public_files']:
                    assert (await page.request.get(base+'/'+reference)).status==200,reference
                assert (await page.request.get(base+'/1.3.1/suite.json')).status==404
                await context.close()
            finally:await browser.close()
    try:asyncio.run(check())
    finally:server.shutdown();server.server_close()
    core.save(out/'observed.json',{'scope':'authored fixture integrity, not detector accuracy','corpus_digest':corpus['digest'],
        'pages_checked':checked,'behaviours':behaviours,'javascript_errors':errors})
    print(f'Checked {len(checked)} page entries and {len(behaviours)} interactive contrasts.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();main(args.out)
