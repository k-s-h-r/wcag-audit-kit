"""Collect real browser evidence; never translate axe passes into WCAG conformance."""
import asyncio
import base64
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import re
import shutil
import struct
from urllib.parse import urljoin, urlsplit, urlunsplit
from collection_checkpoint import CollectionCheckpoint, save_json_atomic

ROOT = Path(__file__).resolve().parents[1]

INVENTORY = r"""() => {
 const nodes=[...document.querySelectorAll('*')], limit=15000;
 const selector=e=>{if(e.id&&document.querySelectorAll('#'+CSS.escape(e.id)).length===1)return '#'+CSS.escape(e.id);
  const out=[];for(let n=e;n&&n!==document.documentElement;n=n.parentElement){let s=n.localName;
   if(n.parentElement)s+=':nth-child('+([...n.parentElement.children].indexOf(n)+1)+')';out.unshift(s)}return 'html>'+out.join('>')};
 const list=nodes.slice(0,limit).map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();
  const labels=e.labels?[...e.labels].map(l=>l.textContent.trim()):[];
  return {selector:selector(e),tag:e.localName,id:e.id,role:e.getAttribute('role'),
   text:(e.textContent||'').trim().slice(0,800),ariaLabel:e.getAttribute('aria-label'),
   labelledby:e.getAttribute('aria-labelledby'),describedby:e.getAttribute('aria-describedby'),
   alt:e.getAttribute('alt'),src:e.getAttribute('src'),href:e.getAttribute('href'),
   type:e.getAttribute('type'),lang:e.getAttribute('lang'),autocomplete:e.getAttribute('autocomplete'),labels,
   visible:!!(r.width&&r.height&&s.visibility!=='hidden'&&s.display!=='none'),
   rect:{x:r.x,y:r.y,width:r.width,height:r.height},color:s.color,background:s.backgroundColor,
   backgroundImage:s.backgroundImage,fontSize:s.fontSize,fontWeight:s.fontWeight,
   position:s.position,tabIndex:e.tabIndex,disabled:!!e.disabled};});
 return {url:location.href,title:document.title??document.querySelector('title')?.textContent??'',
  documentElement:document.documentElement.localName,documentNamespace:document.documentElement.namespaceURI,contentType:document.contentType,
  documentTitles:[...document.querySelectorAll('title')].map(t=>({namespace:t.namespaceURI,
   parent:t.parentElement?.localName,textContent:t.textContent,
   textNodes:[...t.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).map(n=>n.data)})),
  lang:document.documentElement.getAttribute('lang')||document.documentElement.getAttribute('xml:lang')||'',
  viewport:{width:innerWidth,height:innerHeight},devicePixelRatio,
  nodeCount:nodes.length,truncated:nodes.length>limit,nodes:list,
  text:document.body?.innerText??document.documentElement.textContent,
  links:[...document.querySelectorAll('a')].map(a=>a.getAttribute('href')||a.getAttributeNS('http://www.w3.org/1999/xlink','href'))
   .filter(Boolean).map(h=>{try{return new URL(h,document.baseURI).href}catch{return null}}).filter(Boolean)};
}"""

OPEN_FOCUS_PATH = r"""(doc) => {
 let element=doc.activeElement;
 const shadowHosts=[];
 while(element?.shadowRoot?.activeElement){
  shadowHosts.push({tag:element.localName,id:element.id});
  element=element.shadowRoot.activeElement;
 }
 return {element,shadowHosts};
}"""

FOCUS = r"""(followOpenShadow=false) => {
 const focusPath=followOpenShadow ? ("""+OPEN_FOCUS_PATH+r""")(document) : {element:document.activeElement};
 const e=focusPath.element;if(!e)return null;const r=e.getBoundingClientRect();
 const hits=r.width&&r.height?document.elementsFromPoint(r.x+r.width/2,r.y+r.height/2).slice(0,5).map(n=>({tag:n.localName,id:n.id})):[];
 return {tag:e.localName,id:e.id,documentHasFocus:document.hasFocus(),text:(e.innerText||'').slice(0,160),name:e.getAttribute('aria-label'),
 ...(followOpenShadow ? {shadowHosts:focusPath.shadowHosts} : {}),
 rect:{x:r.x,y:r.y,width:r.width,height:r.height},centerHitStack:hits,
 note:'矩形や中心点の重なりだけで隠れ・フォーカスの可視性を判定しない'};}"""


async def capture_image(page,path,full_page=False,native_zoom=False):
    root=await page.evaluate('() => ({name:document.documentElement.localName,namespace:document.documentElement.namespaceURI})')
    html_document=root['name']=='html' and root['namespace']=='http://www.w3.org/1999/xhtml'
    if not native_zoom and html_document:
        await page.screenshot(path=str(path),full_page=full_page)
        return
    # Avoid CSS-sized clips for native zoom and full-page sizing for SVG/XML.
    session=await page.context.new_cdp_session(page)
    try:
        data=await session.send('Page.captureScreenshot',{
            'format':'png','fromSurface':not native_zoom,'captureBeyondViewport':False})
        pixels=base64.b64decode(data['data'])
        width,height=struct.unpack('>II',pixels[16:24])
        metrics=await page.evaluate('() => ({width:innerWidth,height:innerHeight,dpr:devicePixelRatio})')
        if any(abs(observed-metrics[axis]*metrics['dpr'])>4 for axis,observed in [('width',width),('height',height)]):
            raise RuntimeError('画像寸法と実表示領域が一致しない')
        Path(path).write_bytes(pixels)
        Path(str(path)+'.json').write_text(json.dumps({'captured':'visible browser content in native pixels',
            'full_page':False,'full_page_requested':full_page,'native_zoom':native_zoom,'document_root':root,
            'pixel_width':width,'pixel_height':height,'metrics':metrics,
            'note':'この画像は表示領域のみ。未表示の内容はスクロール等の追加操作で確認する'},ensure_ascii=False,indent=2))
    finally:
        await session.detach()


async def capture_zoom_step(page,dest,prefix,percent,metrics,stage,images=None):
    image=dest/f'{prefix}-{percent}.png'
    if images:await images.capture(page,image,native_zoom=True)
    else:await capture_image(page,image,native_zoom=True)
    inv=await page.evaluate(INVENTORY)
    (dest/f'{prefix}-{percent}-inventory.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2))
    (dest/f'{prefix}-{percent}-stage.json').write_text(json.dumps({'percent':percent,
        'metrics':metrics,'stage':stage,'note':'この時点の表示。全機能の操作を確認した意味ではない'},ensure_ascii=False,indent=2))


async def check_state(page,assertions):
    for assertion in assertions:
        loc=page.get_by_role(assertion['role'],name=assertion['name'],exact=True) if 'role' in assertion else page.locator(assertion['selector'])
        expected_visible=assertion.get('visible',True)
        if type(expected_visible) is not bool:raise ValueError('assertのvisibleはtrue又はfalseにする')
        if await loc.is_visible()!=expected_visible:
            raise ValueError('状態の表示条件と一致しない: '+str(assertion))
        if 'text' in assertion and await loc.inner_text()!=assertion['text']:
            raise ValueError('期待するテキストと一致しない: '+str(assertion))


async def observe_targets(page,targets):
    from input_observation import locator_for
    result=[]
    for target in targets:
        locator=locator_for(page,target)
        observation={'target':target,'text':await locator.inner_text()}
        if target.get('attributes'):
            observation['attributes']={name:await locator.get_attribute(name) for name in target['attributes']}
        result.append(observation)
    return result


def normalize(url,config=None):
    u = urlsplit(url)
    fragments=config.get('scope',{}).get('same_document_fragments',[]) if config else []
    return urlunsplit((u.scheme, u.netloc, u.path or '/', u.query, '' if u.fragment in fragments else u.fragment))


def in_scope(url, config):
    base, target = urlsplit(config['url']), urlsplit(url)
    if (base.scheme, base.netloc) != (target.scheme, target.netloc):
        return False
    path = target.path or '/'
    def match(pattern):
        if pattern == '/**':
            return True
        if pattern.endswith('/**'):
            p = pattern[:-3]
            return path == p or path.startswith(p + '/')
        return path == pattern
    included = any(match(p) for p in config['scope']['include'])
    excluded = any(match(p['path']) for p in config['scope'].get('exclude', []))
    return included and not excluded


def page_id(url):
    return sha256(url.encode()).hexdigest()[:12]


async def collect(config, run_dir):
    from playwright.async_api import async_playwright
    run_dir = Path(run_dir)
    manifest = {'pages': [], 'unvisited': [], 'errors': [], 'discovered': [],'document_aliases':[],
                'captures': [], 'not_a_screen_reader_test': True}
    from inspection import ImageBudget
    images=ImageBudget(config,run_dir,manifest,capture_image)
    configured=config['scope'].get('mode','discover')=='configured'
    if configured:
        from page_catalog import configured_urls
        queue=configured_urls(config)
    else:
        queue = [normalize(urljoin(config['url'], p),config) for p in config['scope'].get('seeds', ['/'])]
        queue += [normalize(urljoin(config['url'], p),config) for p in config['scope'].get('known_pages', [])]
    queue = list(dict.fromkeys(queue))
    seen = set()
    known = set(queue)
    with CollectionCheckpoint(config, run_dir, manifest, queue, seen, known, in_scope) as checkpoint:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
            try:
                for url_index in range(config['scope']['max_pages']):
                    if not queue:
                        break
                    url = queue.pop(0)
                    if url in seen or not in_scope(url, config):
                        continue
                    seen.add(url)
                    pid = page_id(url)
                    images.page=pid
                    manifest['pages'].append({'id': pid, 'url': url})
                    states = [{'id': 'initial', 'actions': []}] + [s for s in config.get('states', []) if urlsplit(url).path in s['paths']]
                    for env in config['environments']:
                        for state in states:
                            key = f"{pid}--{state['id']}--{env['id']}"
                            dest = run_dir / 'evidence' / key
                            dest.mkdir(parents=True, exist_ok=True)
                            capture = {'key': key, 'page_id': pid, 'url': url, 'state': state['id'],
                                       'environment': env['id'], 'execution': 'blocked',
                                       'collection_state': 'running',
                                       'evidence_dir': str(dest.relative_to(run_dir))}
                            manifest['captures'].append(capture)
                            checkpoint.save()
                            context = None
                            capture_browser = browser
                            native_display = None
                            from input_observation import InputObserver,INIT_SCRIPT,pointer_action
                            observer=InputObserver(config.get('input_event_limit',10000))
                            actions = []
                            logs = []
                            try:
                                native_zoom = env.get('zoom', 1) != 1
                                if native_zoom:
                                    from native_zoom import NativeDisplay, apply_zoom
                                    native_display=NativeDisplay(dest,width=max(1600,env['viewport']['width']+64),
                                        height=max(1200,env['viewport']['height']+200)).start()
                                    capture_browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),
                                        headless=False,args=['--no-sandbox'],env=native_display.env)
                                context_options={'no_viewport':True} if native_zoom else {'viewport':env['viewport']}
                                context = await capture_browser.new_context(**context_options,locale=config.get('locale','ja-JP'),
                                                                            storage_state=config.get('auth_state'))
                                await context.expose_binding('__wcagAuditInput',observer.accept)
                                await context.add_init_script(INIT_SCRIPT)
                                page = await context.new_page()
                                page.on('console', lambda msg: logs.append({'type':msg.type,'text':msg.text}))
                                response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                                await page.wait_for_timeout(150)
                                if response:
                                    capture['http_status']=response.status
                                    if response.status>=400:
                                        capture['http_notice']='HTTPエラー応答の表示を収集。依頼されたページ・状態に到達したか別に確認する。'
                                if not in_scope(page.url, config):
                                    raise ValueError('対象範囲外へのリダイレクト: '+page.url)
                                if native_zoom:
                                    async def zoom_step(percent,metrics):
                                        await capture_zoom_step(page,dest,'native-zoom',percent,metrics,'before configured state actions',images)
                                    zoom_result=await apply_zoom(page,native_display,env['zoom'],env['viewport'],on_step=zoom_step)
                                    (dest/'native-zoom.json').write_text(json.dumps(zoom_result,ensure_ascii=False,indent=2))
                                    capture['native_zoom']=zoom_result
                                    capture['images_are_viewport_only']=True
                                    if shutil.which('ffmpeg'):
                                        try:await images.capture_with(dest/'native-desktop.png','detail',lambda:native_display.screenshot(dest/'native-desktop.png'))
                                        except Exception as exc:(dest/'native-desktop-error.txt').write_text(str(exc))
                                await images.capture(page,dest/'00-before.png',full_page=True,native_zoom=native_zoom)
                                for i, action in enumerate(state['actions'], 1):
                                    action_started=datetime.now(timezone.utc).isoformat()
                                    if action['type'] == 'press':
                                        await page.keyboard.press(action['key'])
                                    elif action['type'] == 'type':
                                        await page.keyboard.type(action['value'])
                                    elif action['type'] == 'text_spacing':
                                        await page.add_style_tag(content='*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}')
                                    elif action['type'] == 'reduced_motion':
                                        await page.emulate_media(reduced_motion='reduce')
                                    elif action['type'] == 'scroll':
                                        await page.mouse.wheel(action.get('delta_x',0),action.get('delta_y',0))
                                    elif action['type'] in {'pointer_move','pointer_down','pointer_up','drag'}:
                                        await pointer_action(page,action,observer)
                                    elif action['type'] == 'reload':
                                        await page.reload(wait_until='domcontentloaded')
                                    elif action['type'] == 'zoom':
                                        if not native_display:raise ValueError('zoom操作はネイティブ拡大の環境で実行する')
                                        async def zoom_action_step(percent,metrics):
                                            await capture_zoom_step(page,dest,f'action-{i:03}-zoom',percent,metrics,'during configured state actions',images)
                                        zoom_action=await apply_zoom(page,native_display,action['factor'],env['viewport'],on_step=zoom_action_step)
                                        (dest/f'action-{i:03}-zoom.json').write_text(json.dumps(zoom_action,ensure_ascii=False,indent=2))
                                    else:
                                        loc = page.get_by_role(action['role'], name=action['name'], exact=True) if 'role' in action else page.locator(action['selector'])
                                        if action['type'] == 'click':
                                            await loc.click()
                                        elif action['type'] == 'fill':
                                            await loc.fill(action['value'])
                                        elif action['type'] == 'wait_for':
                                            await loc.wait_for(state=action.get('state', 'visible'))
                                        else:
                                            raise ValueError('未対応の操作: '+str(action['type']))
                                    await page.wait_for_timeout(100)
                                    if not in_scope(page.url, config):
                                        raise ValueError('操作で対象範囲外へ移動した: '+page.url)
                                    actions.append({'index':i,'action':{k:('***' if k=='value' else v) for k,v in action.items()},
                                                    'url':page.url,'focus':await page.evaluate(FOCUS),
                                                    'started_at':action_started,'observed_at':datetime.now(timezone.utc).isoformat(),
                                                    'observations':await observe_targets(page,state.get('observe',[]))})
                                    await images.capture(page,dest/f'action-{i:03}.png',full_page=True,native_zoom=native_zoom)
                                    if action.get('assert'):
                                        actions[-1]['action_asserted']=False
                                        await check_state(page,action['assert'])
                                        actions[-1]['action_asserted']=True
                                    save_json_atomic(dest/'actions.json', actions)
                                    save_json_atomic(dest/'console.json', logs)
                                    save_json_atomic(dest/'input-events.json', observer.export())
                                if state.get('assert'):
                                    await check_state(page,state['assert'])
                                inv = await page.evaluate(INVENTORY)
                                await images.capture(page,dest/'page.png',kind='state',full_page=True,native_zoom=native_zoom)
                                (dest/'dom.html').write_text(await page.content())
                                (dest/'inventory.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2))
                                cdp = await context.new_cdp_session(page)
                                ax = await cdp.send('Accessibility.getFullAXTree')
                                (dest/'accessibility-tree.json').write_text(json.dumps(ax,ensure_ascii=False,indent=2))
                                axe={'violations':[],'incomplete':[]}
                                try:
                                    await page.evaluate((ROOT/'vendor/axe.min.js').read_text())
                                    axe = await page.evaluate("async()=>await axe.run(document,{resultTypes:['violations','incomplete','passes','inapplicable']})")
                                    (dest/'axe.json').write_text(json.dumps(axe,ensure_ascii=False,indent=2))
                                except Exception as exc:
                                    (dest/'axe-error.txt').write_text(str(exc))
                                    capture['axe_error']=str(exc)
                                focus_trace = []
                                for i in range(config.get('keyboard_steps', 30)):
                                    await page.keyboard.press('Tab')
                                    await page.wait_for_timeout(30)
                                    focus = await page.evaluate(FOCUS)
                                    focus_trace.append({'index':i+1,'key':'Tab','url':page.url,'focus':focus})
                                    if config.get('focus_screenshots', True):
                                        await images.capture(page,dest/f'focus-{i+1:03}.png',native_zoom=native_zoom)
                                save_json_atomic(dest/'actions.json', actions)
                                (dest/'keyboard.json').write_text(json.dumps(focus_trace,ensure_ascii=False,indent=2))
                                save_json_atomic(dest/'console.json', logs)
                                save_json_atomic(dest/'input-events.json', observer.export())
                                capture.update(execution='completed',final_url=inv['url'],title=inv['title'],
                                               node_count=inv['nodeCount'],inventory_truncated=inv['truncated'],
                                               input_events_truncated=bool(observer.dropped),input_events=len(observer.events),
                                               browser_version=capture_browser.version,observed_at=datetime.now(timezone.utc).isoformat(),
                                               axe_candidates=len(axe['violations']),axe_incomplete=len(axe['incomplete']))
                                if state['id'] == 'initial' and not configured:
                                    for link in inv['links']:
                                        normalized = normalize(link,config)
                                        if normalized!=normalize(link):
                                            alias={'url':normalize(link),'document_url':normalized,'discovered_from':url}
                                            if alias not in manifest['document_aliases']:manifest['document_aliases'].append(alias)
                                        if in_scope(normalized,config) and normalized not in known:
                                            known.add(normalized);queue.append(normalized)
                            except Exception as exc:
                                capture['error'] = str(exc)
                                (dest/'error.txt').write_text(str(exc))
                                manifest['errors'].append({'capture':key,'error':str(exc)})
                            finally:
                                save_json_atomic(dest/'actions.json', actions)
                                save_json_atomic(dest/'console.json', logs)
                                save_json_atomic(dest/'input-events.json', observer.export())
                                try:
                                    if context:await context.close()
                                finally:
                                    try:
                                        if capture_browser is not browser:await capture_browser.close()
                                    finally:
                                        if native_display:native_display.close()
                                capture['collection_state']='finished'
                                checkpoint.save()
                    checkpoint.save()
                    print('Captured',url,flush=True)
            finally:
                await browser.close()
    return manifest
