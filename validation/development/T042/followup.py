"""Revisit the case handoff in a separate Chromium session with a narrow GET allowlist."""

import argparse
import asyncio
from importlib.metadata import version
from pathlib import Path
import shutil
import sys
from urllib.parse import urlsplit

from playwright.async_api import async_playwright

from collect import PLAN, REPO, digest, load, now, save, serve, verify_fixtures

sys.path.insert(0, str(REPO / 'skills/wcag-audit-kit/scripts'))
from input_observation import INIT_SCRIPT, InputObserver


SNAPSHOT = """({url:location.href, title:document.title,
  heading:document.querySelector('h1')?.textContent,
  time_origin:performance.timeOrigin, viewport:[innerWidth,innerHeight],
  active:{id:document.activeElement?.id,tag:document.activeElement?.localName},
  document_has_focus:document.hasFocus(), subject_count:document.querySelectorAll('#subject').length,
  body_text:document.querySelector('main')?.innerText})"""


def original_trace(area, item, url, expected_destination):
    if item is None:
        return None
    work = area / 'page/work'
    graph = load(work / 'exploration.json')
    paths = [edge['evidence_dir'] + '/keyboard-trace-stop.json' for edge in graph['edges']
             if edge['evidence_dir'] + '/keyboard-trace-stop.json' in item]
    if len(paths) != 1:
        raise ValueError('残件の元となる停止記録を識別できない')
    path, = paths
    record = load(work / path)
    attempt = record['focus_navigation']
    blocked = record['blocked_requests'][attempt['blocked_request_index']]
    if (attempt['status'] != 'blocked' or attempt['source_url'] != url
            or attempt['destination'] != expected_destination or attempt['target']['id'] != 'subject'
            or blocked['method'] != 'GET' or blocked['is_main_frame'] is not True
            or blocked['resource_type'] != 'document'):
        raise ValueError('残件の移動要求と追試の許容先を照合できない')
    return {'path': path, 'sha256': digest(work / path), 'attempt': attempt, 'blocked': blocked}


async def snapshot(page, devtools, area, name):
    result = await page.evaluate(SNAPSHOT)
    save(area / f'{name}.json', result)
    (area / f'{name}.html').write_text(await page.content(), encoding='utf-8')
    save(area / f'{name}.ax.json', await devtools.send('Accessibility.getFullAXTree'))
    await page.screenshot(path=area / f'{name}.png')
    return result


async def visit(browser, area, url, destination, viewport, settings, received):
    source = 'initial'
    routes, navigations = [], []
    start = len(received)
    context = await browser.new_context(viewport=viewport, locale='ja-JP', service_workers='block')
    try:
        page = await context.new_page()
        observer = InputObserver()
        await page.expose_binding('__wcagAuditInput', observer.accept)
        await page.add_init_script(INIT_SCRIPT)
        devtools = await context.new_cdp_session(page)
        await devtools.send('Accessibility.enable')

        async def route_request(route):
            request = route.request
            expected_url = url if source == 'initial' else destination
            main_frame = request.frame == page.main_frame
            allowed = (request.url == expected_url and request.method == 'GET'
                       and request.resource_type == 'document' and request.is_navigation_request()
                       and main_frame)
            routes.append({'at': now(), 'phase': source, 'url': request.url,
                           'method': request.method, 'type': request.resource_type,
                           'main_frame': main_frame, 'allowed': allowed})
            if allowed:
                await route.continue_()
            else:
                await route.abort('blockedbyclient')

        def navigated(frame):
            if frame == page.main_frame:
                navigations.append({'at': now(), 'url': frame.url, 'phase': source})

        page.on('framenavigated', navigated)
        await context.route('**/*', route_request)
        response = await page.goto(url, wait_until='load')
        if response is None or response.status != 200:
            raise ValueError('追試の起点文書が取得できない')
        before = await snapshot(page, devtools, area, 'before')
        if (before['url'] != url or before['subject_count'] != 1
                or before['active']['tag'] not in {'body', 'html'} or not before['document_has_focus']
                or before['viewport'] != [viewport['width'], viewport['height']] or len(page.frames) != 1):
            raise ValueError('追試の初期フォーカスや画面幅が一致しない')
        first_event = len(observer.events)
        await page.evaluate('window.__wcagStartTabFocusTrace()')
        source = 'one-tab'
        started = now()
        await page.keyboard.press(settings['key'])
        await page.wait_for_timeout(settings['observation_ms'])
        after = await snapshot(page, devtools, area, 'after')
        trace = observer.export()
        save(area / 'input-events.json', trace)
        save(area / 'browser-requests.json', routes)
        save(area / 'main-frame-documents.json', navigations)
        save(area / 'http-receipts.json', received[start:])
        return {'before': before, 'after': after, 'events': trace['events'][first_event:],
                'truncated': trace['truncated'], 'started_at': started, 'stopped_at': now()}
    finally:
        await context.close()


def analyze(result, routes, commits, received, plan, origin, case):
    before, after, events = (result[key] for key in ('before', 'after', 'events'))
    settings = plan['manual_input']
    tab = [row for row in events if row['type'] == 'keydown']
    focus = next((row for row in events if row['type'] == 'focus'
                  and row['target'] == {'tag': 'input', 'id': settings['target'][1:]}), None)
    if (result['truncated'] or len(tab) != settings['count'] or tab[0]['key'] != settings['key']
            or any(tab[0]['modifiers'].values()) or focus is None or events.index(tab[0]) > events.index(focus)
            or not all(row['isTrusted'] and row['is_main_frame'] and row['url'] == before['url']
                       and row['documentId'] == tab[0]['documentId'] for row in (tab[0], focus))
            or any(row['type'] in {'click', 'pointerdown', 'mousedown'} for row in events)):
        raise ValueError('操作履歴に最初の主文書で届いた実Tabとフォーカスを確認できない')
    destination = f"{origin}/{plan['destination']}"
    new_document = after['time_origin'] != before['time_origin']
    attempts = [row for row in events if row['type'] == 'navigate']
    admitted = [(row['phase'], row['url']) for row in routes if row['allowed']]
    observed = [(row['phase'], row['url']) for row in commits]
    expected = [('initial', before['url'])]
    if case == '073':
        expected.append(('one-tab', destination))
        if (len(attempts) != 1 or events.index(attempts[0]) <= events.index(focus)
                or attempts[0]['focusDispatchPhase'] != 2 or attempts[0]['documentId'] != focus['documentId']
                or attempts[0]['target'] != focus['target'] or attempts[0]['isTrusted'] is not True
                or attempts[0]['is_main_frame'] is not True or attempts[0]['sameDocument'] is not False
                or attempts[0]['destination'] != destination or not new_document
                or after['url'] != destination or after['heading'] != '利用料金の一覧'
                or before['heading'] == after['heading']):
            raise ValueError('実フォーカスと新文書のコミットを照合できない')
    elif (attempts or new_document or after['url'] != before['url']
          or after['active']['id'] != settings['target'][1:] or before['body_text'] != after['body_text']):
        raise ValueError('対照で同じ文書とフォーカスが維持されたことを確認できない')
    paths = [urlsplit(url).path for _, url in expected]
    if (admitted != expected or observed != expected
            or [row['path'] for row in received] != paths
            or any(row['method'] != 'GET' or row['status'] != 200
                   or row['host'] != urlsplit(origin).netloc
                   or row['body_sha256'] != plan['fixture_sha256'][row['path'].removeprefix('/')]
                   for row in received)):
        raise ValueError('ブラウザーの許可要求、主文書とサーバー受信が一致しない')
    return {'visited': [url for _, url in observed], 'new_document': new_document,
            'focused_target': focus['target'], 'keydown_count': len(tab),
            'server_gets': paths, 'observation_ms': settings['observation_ms']}


async def followup(run):
    if digest(run / 'plan.json') != digest(PLAN):
        raise ValueError('通常収集と追試で事前条件が一致しない')
    plan = load(run / 'plan.json')
    handoff = load(run / 'handoff.json')
    fixtures = run / 'fixtures'
    verify_fixtures(fixtures, plan)
    start_origin = handoff['073']['origin']
    parsed = urlsplit(start_origin)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not parsed.port:
        raise ValueError('追試の起点はループバックの同じHTTPポートとする')
    output = run / 'manual'
    output.mkdir(exist_ok=False)
    outcomes = {}
    with serve(fixtures, port=parsed.port) as (origin, received):
        async with async_playwright() as driver:
            browser = await driver.chromium.launch(executable_path=shutil.which('chromium'))
            try:
                for case, row in handoff.items():
                    if row['origin'] != origin or row['url'] != f"{origin}/{plan['cases'][case]}":
                        raise ValueError('通常検査の始点は事前計画と同じURLとする')
                    for env, item in row['environments'].items():
                        area = output / case / env
                        area.mkdir(parents=True)
                        report_area = run / case
                        packet = load(report_area / 'before' / f'case-{env}.json')
                        configured = load(report_area / 'page/work/run.json')['config']['environments']
                        viewport = plan['environments'][env]
                        if not any(e['id'] == env and e['viewport'] == viewport and e['zoom'] == 1 for e in configured):
                            raise ValueError('保存された検査票と追試の画面幅が異なる')
                        destination = f"{origin}/{plan['destination']}"
                        related = original_trace(report_area, item['item'], row['url'], destination)
                        save(area / 'source-case.json',
                             {'case_id': packet['case']['case_id'], 'state': packet['case']['state'],
                              'environment': env, 'page_url': row['url'], 'graph_digest': row['graph_digest'],
                              'viewport': viewport, 'original_trace': related, 'browser': browser.version,
                              'playwright': version('playwright')})
                        result = await visit(browser, area, row['url'], destination, viewport,
                                             plan['manual_input'], received)
                        summary = analyze(result, load(area / 'browser-requests.json'),
                                          load(area / 'main-frame-documents.json'),
                                          load(area / 'http-receipts.json'), plan, origin, case)
                        save(area / 'observation.json', {**summary, 'before': result['before'], 'after': result['after'],
                                                          'started_at': result['started_at'], 'stopped_at': result['stopped_at']})
                        outcomes[f'{case}/{env}'] = summary
                        print(case, env, 'follow-up observed', flush=True)
            finally:
                await browser.close()
    save(output / 'summary.json', outcomes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    asyncio.run(followup(parser.parse_args().run.resolve()))
