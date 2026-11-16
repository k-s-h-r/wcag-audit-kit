"""Validate authored fixture probes; never use these oracle probes as an auditor."""
import argparse
import asyncio
import datetime
from pathlib import Path
import shutil
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks import core,runner


def contains_action(steps,action):
    return any(s['action']==action or contains_action(s.get('steps',[]),action) for s in steps)


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    corpus=core.corpus();jobs=[]
    for suite in corpus['suites']:
        shutil.copytree(core.ROOT/'benchmarks/cases'/suite['criterion']/'public',out/'public'/suite['criterion'])
        jobs += [(suite['criterion'],c) for c in suite['cases'] if c.get('fixture_probe')]
    server=runner.server(out/'public');base=f'http://127.0.0.1:{server.server_port}'
    results=[];trace=[];errors=[]

    async def exercise():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--mute-audio'])
            try:
                for sc,case in jobs:
                    probe=case['fixture_probe'];context=await browser.new_context(viewport={'width':1280,'height':900})
                    page=await context.new_page();case_errors=[]
                    page.on('pageerror',lambda e:case_errors.append(str(e)))
                    virtual=contains_action(probe['steps'],'tick')
                    simulated=[name for name in ['orientation','motion','text-scale'] if contains_action(probe['steps'],name)]
                    if virtual:await page.clock.install(time=datetime.datetime(2026,11,17,tzinfo=datetime.timezone.utc))
                    url=f'{base}/{sc}/{case["pages"][-1]}';await page.goto(url)

                    async def record(step):
                        for attempt in range(3):
                            try:
                                observed=await page.evaluate('''()=>{let root=document,focus=[];for(let i=0;i<12;i++){
                                  let a=root.activeElement;if(!a)break;focus.push(a.id||a.tagName);
                                  if(a.shadowRoot?.activeElement)root=a.shadowRoot;
                                  else if(a.tagName==='IFRAME'&&a.contentDocument)root=a.contentDocument;else break;
                                }return {url:location.href,focus,documentHasFocus:document.hasFocus()}}''')
                                trace.append(dict(criterion=sc,case=case['id'],action=step,observed=observed,virtual_clock=virtual));return
                            except Exception:
                                if attempt==2:raise
                                await page.wait_for_load_state('domcontentloaded')

                    async def condition(step):
                        loc=page.locator(step['selector']);count=await loc.count()
                        if 'count' in step and count!=step['count']:return False
                        if 'visible' in step and (await loc.is_visible())!=step['visible']:return False
                        if not count:return set(step).issubset({'action','selector','count','visible','timeout'})
                        if 'text' in step and await loc.inner_text()!=step['text']:return False
                        if 'attribute' in step and await loc.get_attribute(step['attribute'])!=step.get('value'):return False
                        if 'property' in step:
                            value=await loc.evaluate('(e,k)=>e[k]',step['property'])
                            if 'value' in step and value!=step['value']:return False
                            if 'minimum' in step and (value is None or value<step['minimum']):return False
                        if 'css' in step:
                            value=await loc.evaluate('(e,k)=>getComputedStyle(e).getPropertyValue(k)',step['css'])
                            if value!=step['value']:return False
                        if 'focused' in step and await loc.evaluate('(e)=>e.getRootNode().activeElement===e')!=step['focused']:return False
                        if 'overflow_y' in step and await loc.evaluate('(e)=>e.scrollHeight>e.clientHeight+1')!=step['overflow_y']:return False
                        if 'width' in step or 'height' in step:
                            rect=await loc.bounding_box()
                            if rect is None:return False
                            if any(abs(rect[k]-step[k])>.6 for k in ['width','height'] if k in step):return False
                        return True

                    async def run_steps(items):
                        for step in items:
                            action=step['action']
                            if action=='click':await page.locator(step['selector']).click()
                            elif action=='hover':await page.locator(step['selector']).hover()
                            elif action=='pointer-target':
                                # Capture the destination before moving: a negative hover popup
                                # intentionally disappears en route, so locator.hover retries forever.
                                box=await page.locator(step['selector']).bounding_box()
                                assert box is not None,step
                                await page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
                            elif action=='key':await page.keyboard.press(step['value'])
                            elif action=='fill':await page.locator(step['selector']).fill(step['value'])
                            elif action=='select':await page.locator(step['selector']).select_option(value=step['value'])
                            elif action=='tick':await page.clock.fast_forward(step['milliseconds'])
                            elif action=='repeat':
                                for _ in range(step['times']):await run_steps(step['steps'])
                            elif action=='reload':await page.reload()
                            elif action=='viewport':await page.set_viewport_size({'width':step['width'],'height':step['height']})
                            elif action=='text-scale':
                                await page.evaluate('(scale)=>document.body.style.fontSize=(18*scale)+"px"',step['scale'])
                            elif action=='orientation':
                                await page.evaluate('(angle)=>{Object.defineProperty(screen.orientation,"angle",{configurable:true,value:angle});dispatchEvent(new Event("orientationchange"))}',step['angle'])
                            elif action=='motion':
                                await page.evaluate('(x)=>{const e=new Event("devicemotion");Object.defineProperty(e,"accelerationIncludingGravity",{value:{x,y:0,z:0}});dispatchEvent(e)}',step['x'])
                            elif action=='frame-click':await page.frame_locator(step['frame']).locator(step['selector']).click()
                            elif action=='deep-focus':
                                await record(step);assert trace[-1]['observed']['focus']==step['path'],trace[-1]
                            elif action=='document-overflow':
                                assert await page.evaluate('document.documentElement.scrollWidth>innerWidth+1')==step['expected'],step
                            elif action=='window-value':assert await page.evaluate('(k)=>window[k]',step['name'])==step['value'],step
                            elif action=='url':
                                if step.get('suffix'):await page.wait_for_url('**'+step['suffix'])
                                if step.get('unchanged'):assert page.url==url,(url,page.url)
                            elif action=='occlusion':
                                visible=await page.locator(step['selector']).evaluate('''e=>{const r=e.getBoundingClientRect();return [[r.left+1,r.top+1],[r.right-1,r.top+1],[r.left+1,r.bottom-1],[r.right-1,r.bottom-1],[(r.left+r.right)/2,(r.top+r.bottom)/2]].map(([x,y])=>{const a=document.elementFromPoint(x,y);return a===e||e.contains(a)})}''')
                                value='none' if all(visible) else 'all' if not any(visible) else 'partial'
                                assert value==step['expected'],(step,visible)
                            elif action in {'check','wait'}:
                                deadline=time.monotonic()+step.get('timeout',20000 if action=='wait' else 2000)/1000
                                while not await condition(step):
                                    if time.monotonic()>deadline:raise AssertionError((sc,case['id'],step,trace[-1:] ))
                                    await asyncio.sleep(.05)
                            else:raise ValueError('Unknown fixture probe action: '+action)
                            if action!='deep-focus':await record(step)
                    try:
                        await run_steps(probe['steps'])
                        assert not case_errors,case_errors
                        results.append(dict(criterion=sc,case=case['id'],page=case['pages'][-1],pattern=case.get('pattern'),
                            status='fixture-behaviour-confirmed',virtual_clock=virtual,simulated_inputs=simulated,simulation=probe.get('simulation'),requires_environment=case.get('requires_environment',[])))
                    except Exception as error:
                        await page.screenshot(path=str(out/(sc+'-'+case['id']+'-failed.png')))
                        errors.append(dict(criterion=sc,case=case['id'],error=str(error),javascript_errors=case_errors))
                    finally:await context.close()
            finally:await browser.close()
    try:asyncio.run(exercise())
    finally:server.shutdown();server.server_close()
    core.save(out/'observed.json',dict(scope='authored fixture probes, not detector accuracy or real-device/real-time/SR confirmation',
        corpus_digest=corpus['digest'],jobs=len(jobs),results=results,trace=trace,errors=errors))
    print(f'Fixture probes: {len(results)}/{len(jobs)} confirmed; errors: {len(errors)}.')
    if errors:raise AssertionError(errors)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();main(args.out)
