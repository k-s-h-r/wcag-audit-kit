"""Collect and score explicit browser measurements on frozen benchmark fixtures."""
import asyncio
from hashlib import sha256
import importlib
import mimetypes
import re
import shutil
from urllib.parse import unquote, urlsplit


METHODS = {
    '1.2.1': ('media', '01'), '1.2.2': ('media', '01'), '1.2.3': ('media', '01'),
    '1.2.5': ('media', '01'), '1.2.8': ('media', '01'), '1.4.2': ('media', '01'),
    '1.3.1': ('structure', '01'), '1.3.5': ('structure', '01'), '4.1.2': ('structure', '01'),
    '2.1.1': ('keyboard', '02'), '2.1.2': ('traps_order', '02'), '2.4.3': ('traps_order', '02'),
    '2.2.1': ('timing', '02'), '2.2.6': ('timing', '02'),
    '2.4.13': ('geometry', '01'), '2.5.8': ('geometry', '02'),
    '3.2.1': ('focus_context', '02'),
}
STATE = re.compile(r'[a-z0-9-]+')
FILE_PREFIX = 'residual-'


def method(criterion):
    return importlib.import_module(f'.residual_{METHODS[criterion][0]}', __package__)


def plans(criterion, checkpoints, states):
    result = {}
    for state in states:
        if 'residual_probe' not in state:
            continue
        spec = state['residual_probe']
        identifier = state.get('id')
        if (criterion not in METHODS or f'{criterion}-{METHODS[criterion][1]}' not in checkpoints
                or not isinstance(identifier, str) or not STATE.fullmatch(identifier)
                or not isinstance(spec, dict)):
            raise ValueError('ブラウザー計測には対応する基準・観点と有効な状態IDが必要')
        method(criterion).validate_plan(criterion, spec)
        result[identifier] = spec
    return result


def selected(job, expectation):
    """True when this expectation belongs to a public measurement in the job."""
    criterion = job['criterion']
    return (criterion in METHODS and expectation['checkpoint'] == f'{criterion}-{METHODS[criterion][1]}'
            and any(state['id'] == expectation['state'] and 'residual_probe' in state for state in job['states']))


def allowed_request(request, root, public_paths):
    url = urlsplit(request.url)
    return (request.method in {'GET', 'HEAD'} and (url.scheme, url.netloc) == (root.scheme, root.netloc)
            and unquote(url.path) in public_paths)


RANGE = re.compile(r'bytes=(\d{0,16})-(\d{0,16})')


def file_response(path, body, method, range_header):
    headers = {'content-type':mimetypes.guess_type(path)[0] or 'application/octet-stream',
               'accept-ranges':'bytes'}
    size = len(body)
    if not range_header or method == 'HEAD':
        return dict(status=200,headers=dict(headers,**{'content-length':str(size)}),
                    body=body if method == 'GET' else b'')
    match = RANGE.fullmatch(range_header)
    if match and any(match.groups()):
        start, end = match.groups()
        first = int(start) if start else max(0,size-int(end))
        last = min(size-1,int(end)) if start and end else size-1
        if first <= last:
            headers.update({'content-range':f'bytes {first}-{last}/{size}',
                            'content-length':str(last-first+1)})
            return dict(status=206,headers=headers,body=body[first:last+1])
    headers['content-range'] = f'bytes */{size}'
    return dict(status=416,headers=headers,body=b'')


async def capture(criterion, url, spec, resources):
    from playwright.async_api import Error, async_playwright

    handler = method(criterion)
    args = getattr(handler, 'launch_args', lambda criterion, spec: [])(criterion, spec)
    if any(arg != '--autoplay-policy=no-user-gesture-required' for arg in args):
        raise ValueError('許可されていないブラウザー設定')
    blocked = []
    branches = []
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox', *args])
            try:
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 900}, service_workers='block', accept_downloads=False,
                )
                context.set_default_timeout(4000)
                page = await context.new_page()
                root = urlsplit(url)

                async def route_request(route):
                    request = route.request
                    if allowed_request(request, root, resources):
                        path = unquote(urlsplit(request.url).path)
                        response = file_response(path, resources[path], request.method, request.headers.get('range'))
                        await route.fulfill(**response)
                    else:
                        blocked.append(True)
                        await route.abort()

                async def dismiss(dialog):
                    branches.append(True)
                    await dialog.dismiss()

                async def close_popup(popup):
                    branches.append(True)
                    await popup.close()

                async def close_socket(socket):
                    blocked.append(True)
                    await socket.close()

                await context.route('**/*', route_request)
                await context.route_web_socket('**/*', close_socket)
                page.on('dialog', dismiss)
                page.on('popup', close_popup)
                page.on('download', lambda _: branches.append(True))

                async def replay():
                    setup = getattr(handler, 'setup', None)
                    if setup:
                        await setup(criterion, page, spec)
                    response = await page.goto(url, wait_until='load')
                    if response is None or response.status != 200 or page.url != url:
                        raise ValueError('公開ページの初期表示を確認できない')
                    return await handler.capture(criterion, page, spec)

                observations = await asyncio.wait_for(replay(), timeout=45)
            finally:
                await browser.close()
    except (Error, TimeoutError, ValueError) as error:
        return {'status':'unconfirmed', 'reason':str(error)[:1200]}
    if blocked or branches or not isinstance(observations, dict):
        return {'status':'unconfirmed', 'reason':'許可範囲外の通信、別ウィンドウ等があるか、観測記録が不足しています。'}
    return {'status':'observed', 'observations':observations}


def binding(job, page, state, config_digest):
    return dict(job_id=job['id'], page=page, mode=job['mode'], state=state, url=job['urls'][page],
                fixture_set=config_digest)


def fixture_set(frozen, criterion):
    from ..suite import core

    prefix = f'worker/public/{criterion}/'
    files = {name.removeprefix('worker/public'): digest for name,digest in frozen.items() if name.startswith(prefix)}
    return files,core.digest(files)


def collect(run, job, page, location):
    from ..suite import core

    declared = plans(job['criterion'], job['checkpoints'], job['states'])
    if not declared:
        return
    files,digest = fixture_set(core.load(run/'integrity.json')['files'], job['criterion'])
    resources = {}
    for name, expected in files.items():
        body = core.local(run,'worker/public'+name).read_bytes()
        if sha256(body).hexdigest() != expected:
            raise ValueError('ブラウザー計測の公開資料が変更された: '+name)
        resources[name] = body
    for state,spec in declared.items():
        result = asyncio.run(capture(job['criterion'], job['urls'][page], spec, resources))
        core.save(location/f'{FILE_PREFIX}{state}.json', dict(binding=binding(job,page,state,digest), **result))


def read_measurement(run, job, page, state, attempt, digest, frozen):
    from ..suite import core

    path = attempt.parent / f'{FILE_PREFIX}{state}.json'
    measurement = core.read_frozen(run,path,frozen) or {}
    if measurement.get('binding') == binding(job,page,state,digest):
        return measurement,path
    return None,path


def predictions(run, job, progress, frozen):
    from ..suite import core

    criterion = job['criterion']
    declared = plans(criterion, job['checkpoints'], job.get('states', []))
    if not declared:
        return {}
    handler = method(criterion)
    _,digest = fixture_set(frozen, criterion)
    rows = {}
    for page in job['pages']:
        try:
            attempt,receipt = core.completed_attempt(run, job, progress, page, frozen)
        except (TypeError, ValueError):
            continue
        if attempt is None:
            continue
        for state,spec in declared.items():
            measurement,path = read_measurement(run,job,page,state,attempt,digest,frozen)
            if not measurement:
                continue
            evidence = measurement.get('observations')
            checkpoint = f'{criterion}-{METHODS[criterion][1]}'
            if measurement.get('status') == 'observed' and isinstance(evidence,dict):
                measured_rows = handler.evaluate(criterion,spec,evidence)
            elif measurement.get('status') == 'unconfirmed' and isinstance(measurement.get('reason'),str):
                targets = spec.get('targets', [spec.get('target')])
                measured_rows = [dict(target=target, checkpoint=checkpoint, outcome='cant_tell',
                    observed=measurement['reason']) for target in targets if isinstance(target,str)] if isinstance(targets,list) else []
            else:
                continue
            for row in measured_rows:
                if (row.get('checkpoint') != checkpoint
                        or row.get('outcome') not in ('passed','failed','cant_tell')
                        or not isinstance(row.get('target'),str) or not isinstance(row.get('observed'),str)):
                    raise ValueError('ブラウザー計測の採点結果が不正')
                observation = dict(row, page=page, state=state, method='program',
                    source='fixture browser measurement', evidence=[p.relative_to(run).as_posix() for p in (receipt,path)])
                key = core.observation_key(observation)
                if key in rows:
                    raise ValueError('ブラウザー計測の採点対象が重複')
                rows[key] = observation
    return rows
