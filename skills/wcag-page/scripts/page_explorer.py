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
import keyboard_checks
import keyboard_frames
import state_labels

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
    if tag in {'input','textarea'} and kind not in {'checkbox','radio','button','reset','submit','image'}:
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
    return await page.evaluate('() => window.__wcagWaitForUpdates()')


async def record_tab_trace(page, dest, limit, blocked, native_events):
    """Save partial Tab observations separately from the completed state capture."""
    import audit
    from playwright.async_api import Error as BrowserError

    trace = []
    stop = None
    for step in range(1, limit + 1):
        before_blocked, before_native = len(blocked), len(native_events)
        error = None
        try:
            await page.keyboard.press('Tab')
            observation = await page.evaluate(FOCUS)
        except BrowserError as exc:
            error = str(exc)
        blocked_during_step = blocked[before_blocked:]
        native_during_step = native_events[before_native:]
        if error or blocked_during_step or native_during_step:
            stop = {'step': step, 'key': 'Tab', 'error': error,
                    'blocked_requests': blocked_during_step, 'native_events': native_during_step}
            audit.save(dest/'keyboard-trace-stop.json', stop)
            break
        trace.append(observation)
    audit.save(dest/'keyboard.json', trace)
    return stop


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
    checks={check['id']:check for check in keyboard_checks.validate(config)}
    implementation=sha256((SCRIPT+FOCUS+Path(__file__).read_text()+Path(keyboard_checks.__file__).read_text()+Path(keyboard_frames.__file__).read_text()).encode()).hexdigest()
    initial_jobs=[]
    for env in config['environments']:
        initial={'environment':env['id'],'route':[]}
        initial_jobs.append(initial)
        initial_jobs.extend(dict(initial, keyboard_check=check_id) for check_id in checks)
    value=audit.load(checkpoint) if checkpoint.exists() else {'schema_version':'1','config_digest':meta['config_digest'],
        'implementation_digest':implementation,
        'queue':initial_jobs,
        'nodes':[],'edges':[],'remaining':[],'proof':[],'steps':0}
    if value['config_digest']!=meta['config_digest']:raise ValueError('探索と設定の版が不一致')
    if value.get('implementation_digest')!=implementation:raise ValueError('探索の実装が変わったため新しいrunで実行する')
    # Recompute transient status rather than persisting status()'s derived fields.
    value.pop('required',None);value.pop('complete',None)
    value['remaining']=[r for r in value['remaining'] if not r.startswith(('探索待ち ','探索中又は','未到達の指定状態：'))]
    labels=state_labels.validate(config.get('exploration_labels',[]))
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
            while value['queue'] and value['steps']<max_steps:
                job=value['queue'][0];env=envs[job['environment']];route=job['route']
                check=checks.get(job.get('keyboard_check'))
                if not check and (len(value['nodes'])>=max_states or len(route)>max_depth):break
                check_record=dict(id=check['id'], name=check['name'], criterion=check['criterion'],
                                  outcome='cant_tell', steps=[]) if check else None
                allowed_navigation={urldefrag(normalize(url))[0]}
                context=await browser.new_context(viewport=env['viewport'],locale=config.get('locale','ja-JP'),storage_state=config.get('auth_state'),service_workers='block',accept_downloads=False)
                observer=InputObserver(10000);blocked=[]
                await context.expose_binding('__wcagAuditInput',observer.accept)
                await context.add_init_script(INIT_SCRIPT);await context.add_init_script(SCRIPT)
                async def guard(request_route):
                    request=request_route.request
                    navigation=request.is_navigation_request()
                    allowed_method=request.method in {'GET','HEAD','OPTIONS'}
                    allowed_document=urldefrag(normalize(request.url))[0] in allowed_navigation
                    if not allowed_method or (navigation and not check and not allowed_document):
                        blocked.append({'method':request.method,'url':request.url})
                        await request_route.abort()
                    elif check and navigation:
                        # Playwright does not dispatch route handlers for every HTTP redirect.
                        # Fetch only the permitted document and refuse redirect responses.
                        await keyboard_checks.load_document(request_route, page, blocked, allowed_navigation, frame_scope)
                    else:
                        await request_route.continue_()
                await context.route('**/*',guard)
                await context.route_web_socket('**/*',lambda socket:socket.close())
                page=await context.new_page()
                frame_scope=keyboard_frames.FrameScope(page, check.get('frame') if check else None)
                error=None;data=None;unreachable=False;native_events=[];settling=[]
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
                    settling.append(await page.evaluate('() => window.__wcagWaitForUpdates()'))
                    if check:
                        if settling[-1]['status'] != 'quiet':
                            raise ValueError('初期表示の更新が観察範囲に収まらない')
                        await keyboard_checks.run_path(page, check, allowed_navigation, check_record, observer,
                                                       lambda: bool(blocked or native_events), frame_scope)
                    else:
                        for action in route:settling.append(await perform(page,action))
                        label_observations=await state_labels.observe(page,route,labels)
                        matched_labels=state_labels.verified(labels,route,label_observations)
                        data=await page.evaluate('() => window.__wcagExplore()')
                        data['observation_wait']=settling
                        data['state_labels']=label_observations
                        inv=await page.evaluate(INVENTORY);audit.save(dest/'inventory.json',inv)
                        audit.save(dest/'state.json',data)
                        if (env['id'],fingerprint(data)) not in seen or matched_labels:
                            # Capture the audited state before diagnostic scrolling changes the DOM.
                            cdp=await context.new_cdp_session(page)
                            audit.save(dest/'accessibility-tree.json',await cdp.send('Accessibility.getFullAXTree'));await cdp.detach()
                            await page.evaluate((ROOT/'vendor/axe.min.js').read_text())
                            audit.save(dest/'axe.json',await page.evaluate("async()=>await axe.run(document,{resultTypes:['violations','incomplete','passes','inapplicable']})"))
                            if matched_labels:
                                current_observations = await state_labels.observe(page, route, labels)
                                still_matched = state_labels.verified(labels, route, current_observations)
                                data['state_labels'] = [record for record in label_observations
                                                        if not record['matched'] or record['id'] in still_matched]
                                audit.save(dest/'state.json', data)
                            await images.capture(page,dest/'page.png',kind='state',full_page=data['scroll']['height']<=env['viewport']['height']*20)
                            # Actual scroll/tile captures reveal sticky/viewport-only content.
                            tiles=[]
                            for y in range(0,min(data['scroll']['height'],env['viewport']['height']*20),env['viewport']['height']):
                                await page.evaluate('(y)=>scrollTo(0,y)',y);await page.wait_for_timeout(40)
                                await images.capture(page,dest/f'tile-{len(tiles):03}.png',kind='state');tiles.append(y)
                            audit.save(dest/'tiles.json',{'positions':tiles,'height':data['scroll']['height'],'viewport':env['viewport']})
                            if data['scroll']['height']>env['viewport']['height']*20:value['remaining'].append(f'{env["id"]}：20画面を超える縦方向の表示を追加調査する。')
                            if any(i['status']=='skipped' for i in images.summary['screenshots'] if i['path'].startswith(str(dest.relative_to(run)))):
                                value['remaining'].append(f'{dest.name}：画像設定又は上限で未観察の表示がある。')
                            trace_stop = await record_tab_trace(page, dest, min(config.get('keyboard_steps',30),120),
                                                                blocked, native_events)
                            if trace_stop:
                                evidence = (dest/'keyboard-trace-stop.json').relative_to(run).as_posix()
                                value['remaining'].append(f'{dest.name}：補助のTab観察は{trace_stop["step"]}回目で中断。'
                                                          f'以降は未確認（証拠: {evidence}）。')
                except Exception as exc:
                    error=str(exc);unreachable=isinstance(exc,KeyboardUnreachable)
                finally:
                    if check_record is not None:
                        if error or blocked or native_events:
                            check_record.update(outcome='cant_tell', reason=error or '制限した通信・ページ移動又はブラウザーの分岐がある。')
                        audit.save(dest/'keyboard-check.json',check_record)
                    audit.save(dest/'transition.json',dict(job,error=error,blocked_requests=blocked,native_events=native_events,settling=settling))
                    audit.save(dest/'input-events.json',observer.export())
                    await context.close()
                proof=[audit.evidence_item(run,str(p.relative_to(run))) for p in sorted(dest.iterdir()) if p.is_file()]
                value['proof'].extend(proof)
                edge=dict(job,error=error,evidence_dir=str(dest.relative_to(run)),blocked_requests=blocked,native_events=native_events)
                if check:
                    edge['keyboard_check']=check['id']
                    if check_record['outcome']=='cant_tell':
                        value['remaining'].append(f"{env['id']} / キーボード経路 {check['name']}：{check_record['reason']}")
                value['edges'].append(edge);value['steps']+=1
                if error and not unreachable and not check:value['remaining'].append(f'{env["id"]} / {route[-1] if route else "initial"}：{error}')
                if blocked:value['remaining'].append(f'{env["id"]}：通信又はページ移動を制限した経路がある。状態を確認する。')
                if native_events:value['remaining'].append(f'{env["id"]}：ブラウザー標準ダイアログ・別窓・ダウンロードの分岐を追加検査する。')
                if any(wait['status']!='quiet' for wait in settling):
                    value['remaining'].append(f'{env["id"]}：DOMと短いタイマーの観察上限又は未観測のコールバックが残る。全非同期完了ではない。')
                if data and not error:
                    key=(env['id'],fingerprint(data));edge['fingerprint']=key[1]
                    matched_labels=state_labels.verified(labels,route,data.get('state_labels',[]))
                    if key not in seen or matched_labels:
                        state='initial' if not route else 'explore-'+attempt
                        capture_key=f'{pid}--{state}--{env["id"]}'
                        node=dict(job,fingerprint=key[1],capture=capture_key,evidence_dir=str(dest.relative_to(run)),controls=data['controls'],state_labels=matched_labels)
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
            found={label for node in value['nodes'] for label in node.get('state_labels',[])}
            value['remaining'] += ['未到達の指定状態：'+label['id'] for label in labels if label['id'] not in found]
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
