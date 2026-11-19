"""Select URLs independently from WCAG inspection."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
from urllib.parse import urljoin, urlsplit


def configured_urls(config):
    from browser_capture import normalize
    return list(dict.fromkeys(normalize(urljoin(config['url'],p),config) for p in config['scope'].get('pages',[])))


def read_config(path):
    import audit
    path=Path(path);value=deepcopy(audit.load(path))
    for key,container in [('auth_state',value),('pages_file',value.setdefault('scope',{}))]:
        if container.get(key):
            source=Path(container[key]);source=source if source.is_absolute() else path.resolve().parent/source
            container[key]=str(source.resolve())
    source=value['scope'].get('pages_file')
    if source:
        if value['scope'].get('pages'):raise ValueError('pagesとpages_fileはどちらか一方にする')
        p=Path(source)
        if p.suffix.lower()=='.json':
            rows=json.loads(p.read_text(encoding='utf-8-sig'));rows=rows.get('pages',[]) if isinstance(rows,dict) else rows
            if not isinstance(rows,list):raise ValueError('URL一覧は配列又はpages一覧にする')
            rows=[r.get('url') if isinstance(r,dict) else r for r in rows]
        else:rows=[line.strip() for line in p.read_text(encoding='utf-8-sig').splitlines() if line.strip() and not line.lstrip().startswith('#')]
        value['scope']['pages']=rows
        from hashlib import sha256
        value['scope']['pages_source']={'path':source,'sha256':sha256(p.read_bytes()).hexdigest()}
        value['scope'].pop('pages_file',None)
    return audit.validate_config(value)


async def open_discovery_page(context, config):
    from browser_capture import in_scope

    page = await context.new_page()
    session = await context.new_cdp_session(page)
    main_frame = (await session.send('Page.getFrameTree'))['frameTree']['frame']['id']
    blocked = []

    async def check_document(event):
        request_id = {'requestId': event['requestId']}
        if event['frameId'] == main_frame and not in_scope(event['request']['url'], config):
            blocked.append(event['request']['url'])
            await session.send('Fetch.failRequest', dict(request_id, errorReason='BlockedByClient'))
        else:
            await session.send('Fetch.continueRequest', request_id)

    # Playwright routes the first URL in a redirect chain. Chromium's
    # request-stage interception also checks subsequent document hops.
    session.on('Fetch.requestPaused', check_document)
    await session.send('Fetch.enable', {'patterns': [{'resourceType': 'Document', 'requestStage': 'Request'}]})
    return page, blocked


async def select_pages(config):
    import audit
    from browser_capture import normalize,in_scope
    if config['scope']['mode']=='configured':
        return {'schema_version':'1','kind':'page-selection','mode':'configured','base_url':config['url'],
                'config_digest':audit.digest(config),'pages':[{'url':u,'source':'configured','visited':False} for u in configured_urls(config)],
                'unvisited':[],'errors':[],'inventory_complete':False,
                'notice':'指定URLの一覧。リンク抽出とページ検証は実行していない。サイト全体の網羅は別に確認する。'}
    from playwright.async_api import Error as BrowserError, async_playwright
    queue=list(dict.fromkeys(normalize(urljoin(config['url'],p),config) for p in config['scope']['seeds']+config['scope']['known_pages']))
    known={u:{'url':u,'source':'configured_start','visited':False} for u in queue if in_scope(u,config)}
    seen=set();errors=[]
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        try:
            context=await browser.new_context(storage_state=config.get('auth_state'), service_workers='block')
            page, blocked = await open_discovery_page(context, config)
            while queue and len(seen)<config['scope']['max_pages']:
                url=queue.pop(0)
                if url in seen or not in_scope(url,config):continue
                seen.add(url);known[url]['visited']=True
                blocked.clear()
                try:
                    response=await page.goto(url,wait_until='domcontentloaded',timeout=30000)
                    if blocked or not in_scope(page.url,config):raise ValueError('範囲外へのリダイレクト')
                    if response and response.status>=400:raise ValueError('HTTP '+str(response.status))
                    links = await page.locator('a[href]').evaluate_all('(items)=>items.map(a=>a.href)')
                    if blocked or not in_scope(page.url,config):raise ValueError('範囲外へのリダイレクト')
                    for link in links:
                        target=normalize(link,config)
                        if in_scope(target,config) and target not in known:
                            known[target]={'url':target,'source':url,'visited':False};queue.append(target)
                except Exception as exc:
                    errors.append({'url': url, 'error': '範囲外へのリダイレクト' if blocked else str(exc)})
                    if (blocked or isinstance(exc, BrowserError)) and queue and len(seen) < config['scope']['max_pages']:
                        # Chromium can commit an error document after goto()
                        # rejects. Keep it from interrupting the next candidate.
                        await page.close()
                        page, blocked = await open_discovery_page(context, config)
        finally:await browser.close()
    return {'schema_version':'1','kind':'page-selection','mode':'discover','base_url':config['url'],
            'config_digest':audit.digest(config),'pages':list(known.values()),
            'unvisited':[u for u in known if u not in seen],'errors':errors,'inventory_complete':False,
            'notice':'初期表示のリンクから得た候補。未リンクURL、操作後、権限別画面、全状態は別に調査する。WCAGの判定はしていない。'}
