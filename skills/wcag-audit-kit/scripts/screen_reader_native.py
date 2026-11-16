"""Run page-specific speech observations with native Orca, NOT Guidepup."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from urllib.parse import urlsplit

from collection_checkpoint import save_json_atomic
from browser_capture import capture_image, observe_targets
from input_observation import locator_for
from native_orca_runtime import NativeOrcaRuntime, now
from orca_log import speech_in_window


NATIVE_COMMANDS = {'nextHeading': ['h'], 'previousHeading': ['Shift_L', 'h'],
    'nextLink': ['k'], 'previousLink': ['Shift_L', 'k'],
    'nextLandmark': ['m'], 'previousLandmark': ['Shift_L', 'm'],
    'nextButton': ['b'], 'previousButton': ['Shift_L', 'b']}


def origin(url):
    if not isinstance(url, str):
        raise ValueError('http/https URLが必要')
    parts = urlsplit(url)
    if parts.scheme not in {'http', 'https'} or not parts.hostname or parts.username or parts.password:
        raise ValueError('認証情報を含まないhttp/https URLが必要')
    host = parts.hostname.lower()
    if ':' in host:
        host = '[' + host + ']'
    else:
        host = host.encode('idna').decode('ascii')
    port = parts.port
    suffix = '' if port is None or port == {'http': 80, 'https': 443}[parts.scheme] else ':' + str(port)
    return parts.scheme + '://' + host + suffix


def validate(request):
    if not isinstance(request, dict):
        raise ValueError('検査シナリオはJSONのobjectにする')
    base = origin(request.get('url'))
    allowed = request.get('allowed_origins', [base])
    if not isinstance(allowed, list) or not allowed or any(origin(url) != url for url in allowed) or base not in allowed:
        raise ValueError('検証対象のorigin一覧が必要')
    if not isinstance(request.get('case_id'), str) or not request['case_id'].strip():
        raise ValueError('case_idが必要')
    actions = request.get('actions')
    if not isinstance(actions, list) or not actions:
        raise ValueError('ページ固有のactionsが必要')
    settle = request.get('settle_ms', 1500)
    if type(settle) is not int or not 250 <= settle <= 10000:
        raise ValueError('settle_msは250〜10000の整数')
    for action in actions:
        if not isinstance(action, dict):
            raise ValueError('各操作はobjectにする')
        kind = action.get('type', '')
        if kind not in {'browser.press', 'browser.click', 'browser.fill', 'reader.press'} | {'reader.' + key for key in NATIVE_COMMANDS}:
            raise ValueError('未対応の操作: ' + str(kind))
        if kind == 'reader.press' and (not isinstance(action.get('keys'), list) or not action['keys'] or
                any(not isinstance(key, str) or not key.strip() for key in action['keys'])):
            raise ValueError('native reader.pressにはX11 keys配列が必要')
        if kind == 'browser.press' and (not isinstance(action.get('key'), str) or not action['key'].strip()):
            raise ValueError('browser.pressにはkeyが必要')
        if kind in {'browser.click', 'browser.fill'} and not (action.get('selector') or action.get('role') and action.get('name')):
            raise ValueError('対象のselector又はroleとnameが必要')
        if kind == 'browser.fill' and not isinstance(action.get('value'), str):
            raise ValueError('fillのvalueが必要')
        if 'expect_contains' in action and (not isinstance(action['expect_contains'], str) or not action['expect_contains'].strip()):
            raise ValueError('期待する発話を空にしない')
        if 'expect_not_contains' in action and (not isinstance(action['expect_not_contains'], list) or
                not action['expect_not_contains'] or any(not isinstance(value, str) or not value.strip() for value in action['expect_not_contains'])):
            raise ValueError('expect_not_containsは空でない文字列の配列にする')
    return allowed


def transcript_assertion(action, speech):
    if 'expect_contains' not in action and 'expect_not_contains' not in action:
        return 'not_requested'
    text = '\n'.join(row['phrase'] for row in speech)
    present = 'expect_contains' not in action or action['expect_contains'] in text
    absent = all(value not in text for value in action.get('expect_not_contains', []))
    return 'matched' if present and absent else 'not_matched'


async def run(args):
    request_bytes = args.request.read_bytes()
    request = json.loads(request_bytes)
    allowed = validate(request)
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    result = {'status': 'blocked', 'started_at': now(), 'case_id': request['case_id'],
              'request_sha256': hashlib.sha256(request_bytes).hexdigest(),
              'environment': {'system': platform.system(), 'kernel': platform.release()},
              'observations': [], 'wcag_judgement': None,
              'expected_note': '発話の部分一致はシナリオの観察。WCAG基準全体の合否とは別。'}
    safe = lambda action: {key: '***' if key == 'value' else value for key, value in action.items()}
    result['scenario'] = {**request, 'actions': [safe(action) for action in request['actions']]}
    runtime = NativeOrcaRuntime(args.root, output)
    browser = None
    code = 2
    try:
        result['environment'].update(await runtime.start())
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(executable_path=args.chromium, headless=False,
                args=['--no-sandbox', '--force-renderer-accessibility'], env=runtime.env)
            try:
                page = await browser.new_page(viewport=request.get('viewport', {'width': 1280, 'height': 900}),
                                               locale=request.get('locale', 'en-US'),
                                               storage_state=(str((args.request.resolve().parent / request['auth_state']).resolve())
                                                              if request.get('auth_state') else None))
                def scope():
                    if origin(page.url) not in allowed:
                        raise ValueError('検証範囲外へ移動した: ' + origin(page.url))
                await page.goto(request['url'], wait_until='domcontentloaded')
                scope()
                await page.bring_to_front()
                await asyncio.sleep(2)
                result['environment']['browser'] = 'Chromium'
                result['environment']['browser_version'] = browser.version
                await capture_image(page, output / 'before.png', full_page=True)
                for index, action in enumerate(request['actions'], 1):
                    scope()
                    focus = lambda: page.evaluate('({tag:document.activeElement?.localName,id:document.activeElement?.id,documentHasFocus:document.hasFocus()})')
                    row = {'index': index, 'action': safe(action), 'focus_before': await focus(),
                           'started_at': now()}
                    result['observations'].append(row)
                    kind = action['type']
                    if kind == 'browser.press':
                        await page.keyboard.press(action['key'])
                    elif kind == 'browser.click':
                        await locator_for(page, action).click()
                    elif kind == 'browser.fill':
                        await locator_for(page, action).fill(action['value'])
                    else:
                        keys = action['keys'] if kind == 'reader.press' else NATIVE_COMMANDS[kind.split('.')[1]]
                        runtime.press(keys)
                    await asyncio.sleep(request.get('settle_ms', 1500) / 1000)
                    row.update(finished_at=now(), focus_after=await focus(), url=page.url)
                    row['speech'] = speech_in_window(runtime.log_text(), row['started_at'], row['finished_at'])
                    row['assertion'] = transcript_assertion(action, row['speech'])
                    row['observations'] = await observe_targets(page,request.get('observe', []))
                    save_json_atomic(output / f'step-{index}.json', row)
                    save_json_atomic(output / 'screen-reader.json', result)
                    await capture_image(page, output / f'step-{index}.png', full_page=True)
                    scope()
                (output / 'page.html').write_text(await page.content())
                result['status'] = 'assertion_failed' if any(row['assertion'] == 'not_matched' for row in result['observations']) else 'collected'
                code = 1 if result['status'] == 'assertion_failed' else 0
            finally:
                await browser.close()
                browser = None
    except Exception as error:
        result['error'] = str(error)
        result['status'] = 'blocked'
        code = 2
    finally:
        result['cleanup'] = await runtime.close()
        if result['cleanup']['pty_error']:
            result['status'] = 'blocked'
            code = 2
        # Re-index the complete log, preserving the original observation windows.
        log_path = output / 'orca-debug.log'
        text = log_path.read_text(errors='replace') if log_path.exists() else ''
        for row in result['observations']:
            if 'finished_at' in row:
                row['speech'] = speech_in_window(text, row['started_at'], row['finished_at'])
                row['assertion'] = transcript_assertion(row['action'], row['speech'])
                save_json_atomic(output / f"step-{row['index']}.json", row)
        if result['status'] != 'blocked':
            result['status'] = 'assertion_failed' if any(row.get('assertion') == 'not_matched' for row in result['observations']) else 'collected'
            code = 1 if result['status'] == 'assertion_failed' else 0
        result['finished_at'] = now()
        save_json_atomic(output / 'screen-reader.json', result)
        print(json.dumps({'status': result['status'], 'error': result.get('error'), 'evidence': str(output)}, ensure_ascii=False))
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--chromium', default='/usr/bin/chromium')
    parser.add_argument('--inside-private-dbus', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if sys.platform != 'linux':
        print('ERROR: このネイティブOrcaアダプターはLinux専用', file=sys.stderr)
        return 2
    if not args.inside_private_dbus:
        return subprocess.call(['dbus-run-session', '--', sys.executable, str(Path(__file__).resolve()),
                                *sys.argv[1:], '--inside-private-dbus'])
    try:
        return asyncio.run(run(args))
    except (ValueError, FileNotFoundError) as error:
        print('ERROR:', error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
