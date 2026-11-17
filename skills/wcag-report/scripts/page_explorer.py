"""Resumable single-page state exploration. Observations are never WCAG verdicts."""
import asyncio
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import uuid
from urllib.parse import urldefrag

from ledger_lock import run_lock
from browser_capture import FOCUS, INVENTORY, ROOT, capture_image, normalize, page_id
from input_observation import INIT_SCRIPT, InputObserver

SCRIPT=(ROOT/'scripts/page_explorer.js').read_text()
RISK=re.compile(r'delete|remove|purchase|checkout|pay\b|buy\b|logout|sign.?out|submit|send\b|save\b|削除|購入|決済|支払|送信|保存|ログアウト',re.I)


class KeyboardUnreachable(ValueError):
    pass


def fingerprint(value):
    keys=('selector','tag','role','type','formAssociated','href','label','tabIndex','haspopup')
    controls=[dict({k:c.get(k) for k in keys},events=sorted(set(c.get('events',[])))) for c in value.get('controls',[])]
    state={'nodes':value['state'],'controls':controls,'url':value.get('url'),'title':value.get('title')}
    return sha256(json.dumps(state,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def actions(control):
    """Keep different input paths even when their resulting states coincide."""
    selector=control['selector'];tag=control['tag'];role=control.get('role');kind=control.get('type') or ''
    # The DOM defaults button.type to submit even outside a form. Only an
    # explicitly observed missing form association makes that default harmless.
    submission=kind in {'submit','image'} and control.get('formAssociated') is not False
    if RISK.search(control.get('label') or '') or submission or kind in {'file','password','hidden'}:
        return [],'送信・永続変更・認証情報等の操作。テスト用経路を追加検査する。'
    if tag=='a' and control.get('href') and not control['href'].startswith('#'):
        return [],'ページ移動を伴うリンク。単独ページから自動巡回しない。'
    base={'selector':selector}
    result=[dict(base,type='click'),dict(base,type='hover')]
    if tag in {'input','textarea'} and kind not in {'checkbox','radio','button','reset'}:
        result += [dict(base,type='fill',value='audit@example.invalid' if kind=='email' else 'Accessibility audit'),
                   dict(base,type='fill',value='')]
    else:
        result += [dict(base,type='key',key=k) for k in (['ArrowDown','ArrowUp','Home','End','Enter','Escape'] if
                    tag=='select' or role in {'combobox','listbox','menu','tab','slider','treeitem'} else ['Enter','Space'])]
    return result,None


def validate_budget(states, steps, depth):
    for value,limit,name in [(states,500,'max_states'),(steps,10000,'max_steps'),(depth,30,'max_depth')]:
        if type(value) is not int or not 1<=value<=limit:raise ValueError(f'{name}は1〜{limit}の整数')


async def perform(page, action):
    target=page.locator(action['selector'])
    if action['type']=='scroll':await page.evaluate('(p)=>scrollTo(p.x,p.y)',action)
    elif action['type']=='press':await page.keyboard.press(action['key'])
    elif action['type']=='click':await target.click(timeout=1800)
    elif action['type']=='hover':await target.hover(timeout=1800)
    elif action['type']=='fill':
        await target.fill(action['value'],timeout=1800);await target.press('Tab')
    elif action['type']=='key':
        # focus() cannot make an unfocusable div keyboard reachable. Find it by
        # actual Tab traversal, then use the widget's own keys.
        reached=False
        for _ in range(120):
            if await target.evaluate('(e)=>e===e.getRootNode().activeElement'):reached=True;break
            await page.keyboard.press('Tab')
        if not reached:raise KeyboardUnreachable('Tabで対象へ到達できない（120移動まで確認）')
        await page.keyboard.press(action['key'])
    else:raise ValueError('未対応の探索操作')
    await page.wait_for_timeout(100)


def status(run):
    import audit
    path=Path(run)/'exploration.json'
    if not path.exists():return {'required':False,'complete':True,'remaining':[],'nodes':[],'edges':[]}
    value=audit.load(path)
    graph_digest=audit.digest(value)
    for item in value.get('proof',[]):
        if audit.evidence_item(Path(run),item['path'])!=item:raise ValueError('探索の証拠が変更された：'+item['path'])
    remaining=[f"探索待ち {len(value['queue'])}経路"] if value['queue'] else []
    resolved=set()
    pointer=audit.run_plan(Path(run)).get('exploration_review')
    if pointer:
        location=(Path(run)/pointer).resolve()
        if not location.is_relative_to(Path(run).resolve()):raise ValueError('追加検査はrun内に保存する')
        review=audit.load(location)
        for proof in review['verified_evidence']:
            if audit.evidence_item(Path(run),proof['path'])!=proof:raise ValueError('追加検査の証拠が変更された')
        if review['graph_digest']==graph_digest:resolved={r['item'] for r in review.get('resolutions',[])}
    remaining += [r for r in value.get('remaining',[]) if r not in resolved]
    if value.get('running'):remaining.append('探索中又は途中停止。page-audit --resumeで再開する。')
    return dict(value,graph_digest=graph_digest,required=True,complete=not remaining and bool(value['nodes']),remaining=remaining)


async def _explore(run, *, max_states=64,max_steps=512,max_depth=8):
    import audit
    from playwright.async_api import async_playwright
    validate_budget(max_states,max_steps,max_depth)
    run=Path(run);meta,_=audit.run_catalog(run,for_write=True);config=meta['config'];url=config['scope']['pages'][0]
    if config['scope'].get('mode')!='configured' or len(config['scope']['pages'])!=1:
        raise ValueError('探索はconfiguredの1ページで実行する')
    if any(env.get('zoom',1)!=1 for env in config['environments']):
        raise ValueError('自動探索の環境はzoom=1にする。実ブラウザー拡大は別のprobeで検証する')
    checkpoint=run/'exploration.json'
    if checkpoint.exists():status(run)
    implementation=sha256((SCRIPT+Path(__file__).read_text()).encode()).hexdigest()
    value=audit.load(checkpoint) if checkpoint.exists() else {'schema_version':'1','config_digest':meta['config_digest'],
        'implementation_digest':implementation,
        'queue':[{'environment':e['id'],'route':[]} for e in config['environments']],
        'nodes':[],'edges':[],'remaining':[],'proof':[],'steps':0}
    if value['config_digest']!=meta['config_digest']:raise ValueError('探索と設定の版が不一致')
    if value.get('implementation_digest')!=implementation:raise ValueError('探索の実装が変わったため新しいrunで実行する')
    # Recompute transient status rather than persisting status()'s derived fields.
    value.pop('required',None);value.pop('complete',None)
    value['remaining']=[r for r in value['remaining'] if not r.startswith(('探索待ち ','探索中又は'))]
    envs={e['id']:e for e in config['environments']};pid=page_id(url)
    manifest=audit.load(run/'capture-manifest.json') if (run/'capture-manifest.json').exists() else {
        'pages':[{'id':pid,'url':url}],'captures':[],'unvisited':[],'errors':[],'collector_status':'running',
        'declared_states_without_page':[],'not_a_screen_reader_test':True}
    if value.get('manifest'):manifest=value['manifest']
    from inspection import ImageBudget
    previous=manifest.get('inspection',{}).get('screenshots',[])
    images=ImageBudget(config,run,manifest,capture_image);images.page=pid
    images.summary['screenshots']=previous
    images.counts[pid]=sum(i['status'] in {'started','captured','error'} for i in previous)
    seen={(n['environment'],n['fingerprint']):n for n in value['nodes']}
    done={json.dumps([e['environment'],e['route']],sort_keys=True) for e in value['edges']}
    queued={json.dumps([j['environment'],j['route']],sort_keys=True) for j in value['queue']}
    value['running']=True;value['manifest']=manifest
    value['limits']={'max_states':max_states,'max_steps':max_steps,'max_depth':max_depth}
    with run_lock(run):audit.save(checkpoint,value);audit.save(run/'capture-manifest.json',manifest)
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        try:
            while value['queue'] and len(value['nodes'])<max_states and value['steps']<max_steps:
                job=value['queue'][0];env=envs[job['environment']];route=job['route']
                if len(route)>max_depth:break
                context=await browser.new_context(viewport=env['viewport'],locale=config.get('locale','ja-JP'),storage_state=config.get('auth_state'),service_workers='block',accept_downloads=False)
                observer=InputObserver(10000);blocked=[]
                await context.expose_binding('__wcagAuditInput',observer.accept)
                await context.add_init_script(INIT_SCRIPT);await context.add_init_script(SCRIPT)
                async def guard(request_route):
                    request=request_route.request
                    if request.method not in {'GET','HEAD','OPTIONS'} or (request.is_navigation_request() and urldefrag(request.url)[0]!=urldefrag(url)[0]):
                        blocked.append({'method':request.method,'url':request.url});await request_route.abort()
                    else:await request_route.continue_()
                await context.route('**/*',guard)
                await context.route_web_socket('**/*',lambda socket:socket.close())
                page=await context.new_page();error=None;data=None;unreachable=False;native_events=[]
                async def dismiss_dialog(dialog):
                    native_events.append({'type':dialog.type,'message':dialog.message,'action':'dismiss'})
                    await dialog.dismiss()
                async def close_popup(popup):
                    native_events.append({'type':'popup','url':popup.url,'action':'close'})
                    await popup.close()
                page.on('dialog',dismiss_dialog);page.on('popup',close_popup)
                page.on('download',lambda download:native_events.append({'type':'download','action':'not_accepted'}))
                attempt=uuid.uuid4().hex[:12];dest=run/'evidence'/f'{pid}--explore-{attempt}--{env["id"]}'
                dest.mkdir(parents=True)
                try:
                    response=await page.goto(url,wait_until='domcontentloaded',timeout=20000)
                    if response and response.status>=400:raise ValueError(f'HTTP {response.status}')
                    await page.wait_for_timeout(150)
                    for action in route:await perform(page,action)
                    data=await page.evaluate('() => window.__wcagExplore()')
                    inv=await page.evaluate(INVENTORY);audit.save(dest/'inventory.json',inv)
                    audit.save(dest/'state.json',data)
                    if (env['id'],fingerprint(data)) not in seen:
                        await images.capture(page,dest/'page.png',kind='state',full_page=data['scroll']['height']<=env['viewport']['height']*20)
                        # Actual scroll/tile captures reveal sticky/viewport-only content.
                        tiles=[]
                        for y in range(0,min(data['scroll']['height'],env['viewport']['height']*20),env['viewport']['height']):
                            await page.evaluate('(y)=>scrollTo(0,y)',y);await page.wait_for_timeout(40)
                            await images.capture(page,dest/f'tile-{len(tiles):03}.png',kind='state');tiles.append(y)
                        audit.save(dest/'tiles.json',{'positions':tiles,'height':data['scroll']['height'],'viewport':env['viewport']})
                        if data['scroll']['height']>env['viewport']['height']*20:value['remaining'].append(f'{env["id"]}：20画面を超える縦方向の表示を追加調査する。')
                        cdp=await context.new_cdp_session(page)
                        audit.save(dest/'accessibility-tree.json',await cdp.send('Accessibility.getFullAXTree'));await cdp.detach()
                        await page.evaluate((ROOT/'vendor/axe.min.js').read_text())
                        audit.save(dest/'axe.json',await page.evaluate("async()=>await axe.run(document,{resultTypes:['violations','incomplete','passes','inapplicable']})"))
                        if any(i['status']=='skipped' for i in images.summary['screenshots'] if i['path'].startswith(str(dest.relative_to(run)))):
                            value['remaining'].append(f'{dest.name}：画像設定又は上限で未観察の表示がある。')
                        trace=[]
                        for _ in range(min(config.get('keyboard_steps',30),120)):
                            await page.keyboard.press('Tab');trace.append(await page.evaluate(FOCUS))
                        audit.save(dest/'keyboard.json',trace)
                except Exception as exc:
                    error=str(exc);unreachable=isinstance(exc,KeyboardUnreachable)
                finally:
                    audit.save(dest/'transition.json',dict(job,error=error,blocked_requests=blocked,native_events=native_events))
                    audit.save(dest/'input-events.json',observer.export())
                    await context.close()
                proof=[audit.evidence_item(run,str(p.relative_to(run))) for p in sorted(dest.iterdir()) if p.is_file()]
                value['proof'].extend(proof)
                edge=dict(job,error=error,evidence_dir=str(dest.relative_to(run)),blocked_requests=blocked,native_events=native_events)
                value['edges'].append(edge);value['steps']+=1
                if error and not unreachable:value['remaining'].append(f'{env["id"]} / {route[-1] if route else "initial"}：{error}')
                if blocked:value['remaining'].append(f'{env["id"]}：通信又はページ移動を制限した経路がある。状態を確認する。')
                if native_events:value['remaining'].append(f'{env["id"]}：ブラウザー標準ダイアログ・別窓・ダウンロードの分岐を追加検査する。')
                if data and not error:
                    key=(env['id'],fingerprint(data));edge['fingerprint']=key[1]
                    if key not in seen:
                        state='initial' if not route else 'explore-'+attempt
                        capture_key=f'{pid}--{state}--{env["id"]}'
                        node=dict(job,fingerprint=key[1],capture=capture_key,evidence_dir=str(dest.relative_to(run)),controls=data['controls'])
                        seen[key]=node;value['nodes'].append(node)
                        manifest['captures'].append(dict(key=capture_key,page_id=pid,url=url,state=state,environment=env['id'],
                            execution='completed',collection_state='finished',evidence_dir=str(dest.relative_to(run))))
                        for feature in ['frames','canvases','closedRoots']:
                            if data[feature]:value['remaining'].append(f'{capture_key}：{feature}の内部を追加検査する。')
                        if data['modal']:
                            job_id=json.dumps([env['id'],route+[{'type':'press','selector':'body','key':'Escape'}]],sort_keys=True)
                            if job_id not in queued:
                                value['queue'].append({'environment':env['id'],'route':route+[{'type':'press','selector':'body','key':'Escape'}]});queued.add(job_id)
                        for control in data['controls']:
                            candidates,reason=actions(control)
                            if reason:
                                node.setdefault('deferred',[]).append(dict(control,reason=reason))
                                value['remaining'].append(f'{env["id"]} / {control["selector"]}：{reason}')
                            for action in candidates:
                                path=route+[action];ident=json.dumps([env['id'],path],sort_keys=True)
                                if ident in queued or ident in done:continue
                                if len(path)>30:
                                    value['remaining'].append(f'{capture_key}：深さ30を超える経路の追加検査が必要。');continue
                                value['queue'].append({'environment':env['id'],'route':path});queued.add(ident)
                        # Scrolling itself can reveal lazy content and trigger events.
                        positions=[(0,env['viewport']['height']),(0,max(0,data['scroll']['height']-env['viewport']['height'])),
                                   (max(0,data['scroll']['width']-env['viewport']['width']),0)]
                        for x,y in set(positions)-{(0,0)}:
                            if len(route)>=30:continue
                            if x==0 and data['scroll']['height']<=env['viewport']['height']:continue
                            path=route+[{'type':'scroll','selector':'body','x':x,'y':y}]
                            ident=json.dumps([env['id'],path],sort_keys=True)
                            if ident not in queued:value['queue'].append({'environment':env['id'],'route':path});queued.add(ident)
                value['queue'].pop(0);value['remaining']=list(dict.fromkeys(value['remaining']))
                value['manifest']=manifest
                with run_lock(run):
                    audit.save(checkpoint,value);audit.save(run/'capture-manifest.json',manifest)
                audit.make_plan(run,manifest)
        finally:
            await browser.close()
            value['running']=False
            manifest['collector_status']='completed' if not value['queue'] else 'interrupted'
            value['manifest']=manifest
            with run_lock(run):audit.save(checkpoint,value);audit.save(run/'capture-manifest.json',manifest)
            audit.make_plan(run,manifest)
    return status(run)


async def explore(run, **kwargs):
    from pathlib import Path
    directory=Path(run)/'.explorer-session';directory.mkdir(exist_ok=True)
    with run_lock(directory,timeout=1):
        return await _explore(Path(run),**kwargs)
