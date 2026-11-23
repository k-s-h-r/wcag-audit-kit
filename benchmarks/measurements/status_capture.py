"""Collect one visible status change on a replay of a benchmark-owned HTML page."""
import asyncio
import re
import shutil
from urllib.parse import urlsplit

SELECTOR = re.compile(r"#[a-zA-Z][\w-]*", re.ASCII)
STATE = re.compile(r"[a-z0-9-]+")
SNAPSHOT = r"""(element, selector) => {
    const box = element.getBoundingClientRect();
    const unique = document.querySelectorAll(selector).length === 1 && document.querySelector(selector) === element;
    const intersects = box.right > 0 && box.bottom > 0 && box.left < innerWidth && box.top < innerHeight;
    return {visible: unique && element.isConnected && !!box.width && !!box.height && intersects &&
        element.checkVisibility({opacityProperty: true, visibilityProperty: true}),
        text: element.innerText, role_attribute: element.getAttribute('role'),
        url: location.href, time_origin: String(performance.timeOrigin), sampled_at: performance.now()};
}"""


def plans(criterion, checkpoints, states):
    """Allow only ID-addressed click-to-observe plans with no expected answer."""
    result = {}
    for state in states:
        if 'status_capture' not in state:
            continue
        spec = state['status_capture']
        identifier = state['id']
        if (criterion != '4.1.3' or '4.1.3-01' not in checkpoints
                or not isinstance(identifier, str) or not STATE.fullmatch(identifier) or identifier == 'initial'
                or not isinstance(spec, dict) or set(spec) != {'action', 'target'}):
            raise ValueError('状態変化の取得には4.1.3-01の状態と操作・観測対象が必要')
        action = spec['action']
        if (not isinstance(action, dict) or set(action) != {'type', 'selector'} or action['type'] != 'click'
                or not all(isinstance(s, str) and SELECTOR.fullmatch(s) for s in (action['selector'], spec['target']))
                or action['selector'] == spec['target']):
            raise ValueError('状態変化の取得では別々のIDでクリック対象と観測対象を指定する')
        result[identifier] = spec
    return result


def fixture_url(url, page):
    parsed = urlsplit(url)
    return (parsed.scheme == 'http' and parsed.netloc == f'127.0.0.1:{parsed.port}'
            and parsed.port is not None and not parsed.query and not parsed.fragment
            and re.fullmatch(r'[a-zA-Z0-9.-]+\.html', page)
            and parsed.path == f'/4.1.3/{page}')


async def collect(url, body, binding, spec):
    """Replay exact frozen HTML. Route fulfillment requires no external requests."""
    from playwright.async_api import Error as BrowserError, async_playwright
    from input_observation import INIT_SCRIPT, InputObserver

    if not fixture_url(url, binding['page']):
        raise ValueError('状態変化の取得は問題集のローカルURLに限定する')
    data = dict(binding, url=url, spec=spec, browser=None, before=None, after=None, event=None,
                requests_blocked=[], native_events=[], not_a_screen_reader_test=True, status='not_evaluated')
    async with async_playwright() as pw:
        browser = None
        try:
            browser = await pw.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
            data['browser'] = browser.version
            context = await browser.new_context(service_workers='block', accept_downloads=False,
                                                viewport={'width': 1280, 'height': 900}, locale='ja-JP')
            observer = InputObserver(100)
            await context.expose_binding('__wcagAuditInput', observer.accept)
            await context.add_init_script(INIT_SCRIPT)
            page = await context.new_page()
            context.on('page', lambda _: data['native_events'].append('popup'))
            page.on('download', lambda _: data['native_events'].append('download'))

            async def on_dialog(dialog):
                data['native_events'].append('dialog')
                await dialog.dismiss()

            page.on('dialog', on_dialog)
            served = False

            async def route_fixture(route):
                nonlocal served
                request = route.request
                if (not served and request.url == url and request.method == 'GET'
                        and request.is_navigation_request() and request.frame == page.main_frame):
                    served = True
                    await route.fulfill(status=200, content_type='text/html; charset=utf-8', body=body)
                else:
                    data['requests_blocked'].append(dict(method=request.method, url=request.url))
                    await route.abort()

            async def block_socket(socket):
                data['requests_blocked'].append(dict(method='WebSocket', url=socket.url))
                await socket.close()

            await context.route('**/*', route_fixture)
            await context.route_web_socket('**/*', block_socket)
            await page.goto(url, wait_until='domcontentloaded', timeout=3000)
            cdp = await context.new_cdp_session(page)
            locator = page.locator(spec['target'])
            if await locator.count() != 1:
                raise ValueError('観測対象が一意でない')
            handle = await locator.element_handle(timeout=1000)

            async def snapshot():
                value = await handle.evaluate(SNAPSHOT, spec['target'])
                if value['visible'] is not True or value['url'] != url:
                    raise ValueError('同じ文書に表示された観測対象を確認できない')
                root = await cdp.send('DOM.getDocument')
                node = await cdp.send('DOM.querySelector', {'nodeId': root['root']['nodeId'], 'selector': spec['target']})
                dom = await cdp.send('DOM.describeNode', node)
                backend = dom['node']['backendNodeId']
                tree = await cdp.send('Accessibility.getPartialAXTree', {'backendNodeId': backend, 'fetchRelatives': False})
                roles = [node.get('role', {}).get('value') for node in tree['nodes']
                         if node.get('backendDOMNodeId') == backend and node.get('ignored') is False]
                repeated = await handle.evaluate(SNAPSHOT, spec['target'])
                if (len(roles) != 1 or not isinstance(roles[0], str) or not roles[0]
                        or any(repeated[key] != expected for key, expected in value.items() if key != 'sampled_at')):
                    raise ValueError('同じ要素のアクセシビリティツリーの役割を確認できない')
                return dict(value, backend_node_id=backend, ax_role=roles[0])

            data['before'] = await snapshot()
            button = page.locator(spec['action']['selector'])
            if await button.count() != 1:
                raise ValueError('クリック対象が一意でない')
            await button.evaluate('(element) => { window.__wcagExpectedPointerTarget = element }')
            await button.click(timeout=2000)
            await page.wait_for_function(
                '([element, before]) => element.isConnected && element.innerText !== before',
                arg=[handle, data['before']['text']], timeout=3000,
            )
            data['after'] = await snapshot()
            events = [event for event in observer.events if event['type'] == 'click']
            if (observer.dropped or len(events) != 1 or not trusted_click(events[0], url, spec)
                    or data['before']['backend_node_id'] != data['after']['backend_node_id']
                    or data['before']['time_origin'] != data['after']['time_origin']
                    or not data['before']['sampled_at'] <= events[0]['timestamp'] <= data['after']['sampled_at']
                    or data['before']['text'] == data['after']['text']):
                raise ValueError('実クリックと同じ対象の表示更新を確認できない')
            data['event'] = events[0]
            if data['requests_blocked'] or data['native_events']:
                raise ValueError('通信又はブラウザーの分岐を制限したため保留する')
            data['status'] = 'observed'
        except (ValueError, BrowserError) as error:
            data['reason'] = str(error).splitlines()[0]
        finally:
            if browser:
                await browser.close()
    return data


def trusted_click(event, url, spec):
    return (
        isinstance(event, dict) and event.get('type') == 'click' and event.get('isTrusted') is True
        and event.get('is_main_frame') is True and event.get('expectedTargetMatched') is True
        and event.get('url') == url and isinstance(event.get('documentId'), str) and bool(event['documentId'])
        and isinstance(event.get('target'), dict)
        and event['target'].get('id') == spec['action']['selector'][1:]
    )
