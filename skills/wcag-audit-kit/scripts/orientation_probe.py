"""Observe page-specific orientation flows through explicit Chromium emulation."""
import argparse
import asyncio
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys

from browser_capture import check_state, observe_targets
from collection_checkpoint import save_json_atomic
from input_observation import INIT_SCRIPT, InputObserver, locator_for
from screen_reader_native import origin


ORIENTATIONS = {'portrait-primary': ('portraitPrimary', 0),
                'landscape-primary': ('landscapePrimary', 90),
                'portrait-secondary': ('portraitSecondary', 180),
                'landscape-secondary': ('landscapeSecondary', 270)}
METRICS = """() => ({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,
 screenWidth:screen.width,screenHeight:screen.height,type:screen.orientation.type,
 angle:screen.orientation.angle,portrait:matchMedia('(orientation:portrait)').matches,
 landscape:matchMedia('(orientation:landscape)').matches,scale:visualViewport?.scale})"""


def now():
    return datetime.now(timezone.utc).isoformat()


def valid_geometry(viewport, orientation):
    if orientation not in ORIENTATIONS:
        raise ValueError('orientationはportrait/landscape-primary/secondaryを指定する')
    if not isinstance(viewport, dict) or any(type(viewport.get(axis)) is not int or
            not 200 <= viewport[axis] <= 5000 for axis in ['width', 'height']):
        raise ValueError('viewportは200〜5000のwidth・heightの整数で指定する')
    portrait = orientation.startswith('portrait')
    if (viewport['width'] < viewport['height']) != portrait or viewport['width'] == viewport['height']:
        raise ValueError('viewportの縦横とorientationが一致していない')


def rotation_verified(metrics, viewport, orientation):
    valid_geometry(viewport, orientation)
    return (metrics['width'] == viewport['width'] and metrics['height'] == viewport['height'] and
            metrics['screenWidth'] == viewport['width'] and metrics['screenHeight'] == viewport['height'] and
            metrics['type'] == orientation and metrics['angle'] == ORIENTATIONS[orientation][1] and
            metrics['portrait'] is orientation.startswith('portrait') and
            metrics['landscape'] is orientation.startswith('landscape') and metrics['scale'] == 1)


async def rotate(page, session, viewport, orientation):
    valid_geometry(viewport, orientation)
    kind, angle = ORIENTATIONS[orientation]
    await session.send('Emulation.setDeviceMetricsOverride', {
        'width': viewport['width'], 'height': viewport['height'], 'deviceScaleFactor': 1,
        'mobile': False, 'screenWidth': viewport['width'], 'screenHeight': viewport['height'],
        'screenOrientation': {'type': kind, 'angle': angle}})
    await page.wait_for_timeout(150)
    metrics = await page.evaluate(METRICS)
    if not rotation_verified(metrics, viewport, orientation):
        raise ValueError('CSS表示領域・Screen Orientation APIと要求した向きが一致しない: ' + json.dumps(metrics))
    return metrics


async def image(page, session, path):
    result = await session.send('Page.captureScreenshot', {'format': 'png',
                                'fromSurface': True, 'captureBeyondViewport': False})
    pixels = base64.b64decode(result['data'])
    width, height = struct.unpack('>II', pixels[16:24])
    metrics = await page.evaluate(METRICS)
    if abs(width - metrics['width'] * metrics['dpr']) > 4 or abs(height - metrics['height'] * metrics['dpr']) > 4:
        raise ValueError('画像の画素寸法と実際の表示領域が一致しない')
    path.write_bytes(pixels)
    save_json_atomic(Path(str(path) + '.json'), {'pixel_width': width, 'pixel_height': height,
        'metrics': metrics, 'full_page': False, 'physical_device': False,
        'note': 'Chromiumの向きのエミュレーションの表示領域。実端末の回転やページ全体の画像ではない。'})


async def run(args):
    request_bytes = args.request.read_bytes()
    request = json.loads(request_bytes)
    if not isinstance(request, dict) or not isinstance(request.get('case_id'), str) or not request['case_id'].strip():
        raise ValueError('case_idを含む検査シナリオが必要')
    allowed = request.get('allowed_origins', [origin(request['url'])])
    if not isinstance(allowed, list) or any(origin(value) != value for value in allowed) or origin(request['url']) not in allowed:
        raise ValueError('対象のallowed_originsを指定する')
    valid_geometry(request['viewport'], request['orientation'])
    for action in request.get('actions', []):
        if action.get('type') not in {'rotate', 'click', 'press', 'fill', 'wait_for'}:
            raise ValueError('未対応の操作')
        if action['type'] == 'rotate':
            valid_geometry(action['viewport'], action['orientation'])
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    result = {'case_id': request['case_id'], 'status': 'blocked', 'started_at': now(),
        'request_sha256': hashlib.sha256(request_bytes).hexdigest(), 'steps': [],
        'environment': {'backend': 'Chromium CDP device metrics / screen orientation emulation',
                        'physical_device': False, 'simulation': True}, 'wcag_judgement': None}
    result['scenario'] = {**request, 'actions': [{key: '***' if key == 'value' else value
                              for key, value in action.items()} for action in request.get('actions', [])]}
    observer = InputObserver()
    code = 2
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
            try:
                context = await browser.new_context(no_viewport=True, locale=request.get('locale', 'en-US'),
                    storage_state=(str((args.request.resolve().parent / request['auth_state']).resolve())
                                   if request.get('auth_state') else None))
                await context.expose_binding('__wcagAuditInput', observer.accept)
                await context.add_init_script(INIT_SCRIPT)
                page = await context.new_page()
                session = await context.new_cdp_session(page)
                await rotate(page, session, request['viewport'], request['orientation'])
                response = await page.goto(request['url'], wait_until='domcontentloaded')
                if response:
                    result['http_status'] = response.status
                result['environment']['browser_version'] = browser.version

                def scope():
                    if origin(page.url) not in allowed:
                        raise ValueError('検証範囲外へ移動した')

                async def capture(index, action, began):
                    scope()
                    row = {'index': index, 'action': {key: '***' if key == 'value' else value for key, value in action.items()},
                        'started_at': began, 'observed_at': now(), 'url': page.url,
                        'metrics': await page.evaluate(METRICS),
                        'focus': await page.evaluate('({tag:document.activeElement?.localName,id:document.activeElement?.id,documentHasFocus:document.hasFocus()})'),
                        'observations': await observe_targets(page, request.get('observe', []))}
                    result['steps'].append(row)
                    await image(page, session, output / f'step-{index}.png')
                    (output / f'step-{index}.html').write_text(await page.content())
                    if action.get('assert'):
                        row['state_asserted'] = False
                        await check_state(page, action['assert'])
                        row['state_asserted'] = True
                    save_json_atomic(output / 'orientation.json', result)
                    save_json_atomic(output / 'input-events.json', observer.export())

                await capture(0, {'type': 'initial', 'assert': request.get('assert', [])}, now())
                for index, action in enumerate(request.get('actions', []), 1):
                    began = now()
                    if action['type'] == 'rotate':
                        await rotate(page, session, action['viewport'], action['orientation'])
                    elif action['type'] == 'press':
                        await page.keyboard.press(action['key'])
                    elif action['type'] == 'click':
                        await locator_for(page, action).click()
                    elif action['type'] == 'fill':
                        await locator_for(page, action).fill(action['value'])
                    elif action['type'] == 'wait_for':
                        await locator_for(page, action).wait_for(state=action.get('state', 'visible'))
                    await page.wait_for_timeout(100)
                    await capture(index, action, began)
                result['status'] = 'collected'
                code = 0
            finally:
                await browser.close()
    except Exception as error:
        result['status'] = 'blocked'
        result['error'] = str(error)
        code = 2
    finally:
        result['finished_at'] = now()
        save_json_atomic(output / 'orientation.json', result)
        save_json_atomic(output / 'input-events.json', observer.export())
        print(json.dumps({'status': result['status'], 'error': result.get('error'), 'evidence': str(output)}, ensure_ascii=False))
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        return asyncio.run(run(args))
    except (ValueError, KeyError, FileNotFoundError) as error:
        print('ERROR:', error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
