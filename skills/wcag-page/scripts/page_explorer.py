"""Resumable single-page state exploration. Observations are never WCAG verdicts."""
import asyncio
from collections import Counter
from contextlib import suppress
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import uuid
from urllib.parse import urldefrag, urlsplit

from ledger_lock import run_lock
from browser_capture import FOCUS, INVENTORY, ROOT, SOFTWARE_COMPOSITING, capture_image, normalize, page_id
from input_observation import INIT_SCRIPT, InputObserver
import border_contrast
import disclosure_close
import dialog_focus
import focus_image_pair
import focus_occlusion
import hover_checks
import keyboard_checks
import keyboard_frames
import keyboard_function
import combobox
import operation_impact
import state_labels
import text_paint
import visual_structure

SCRIPT=(ROOT/'scripts/page_explorer.js').read_text()
RISK=re.compile(r'delete|remove|purchase|checkout|pay\b|buy\b|logout|sign.?out|submit|send\b|save\b|削除|購入|決済|支払|送信|保存|ログアウト',re.I)
TAB_UNREACHABLE = 'Tabで対象へ到達できない（120移動まで確認）'
ACTION_LABELS = {'click': 'クリック', 'hover': 'ホバー', 'fill': '入力', 'scroll': 'スクロール'}
HORIZONTAL_TAB_ARROWS = ('ArrowRight', 'ArrowLeft')


class KeyboardUnreachable(ValueError):
    pass


def fingerprint(value):
    keys=('selector','tag','role','type','formAssociated','href','label','tabIndex','haspopup','horizontalTab')
    controls=[dict({k:c.get(k) for k in keys},events=sorted(set(c.get('events',[])))) for c in value.get('controls',[])]
    state={'nodes':value['state'],'controls':controls,'url':value.get('url'),'title':value.get('title')}
    if references := value.get('operation_reference_inputs'):
        state['reference_inputs'] = references
    if shape := value.get('visual_structure_shape'):
        state['visual_structure_shape'] = shape
    if focused_tab := value.get('focused_horizontal_tab'):
        state['focused_horizontal_tab'] = focused_tab
    return sha256(json.dumps(state,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def actions(control, focused_tab=None):
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
    if role == 'tab' and control.get('horizontalTab'):
        if control['tabIndex'] < 0:
            if selector != focused_tab:
                return result, None
            base['focused_only'] = True
        keys = (*HORIZONTAL_TAB_ARROWS, 'Enter', 'Space', 'ArrowDown', 'ArrowUp', 'Home', 'End', 'Escape')
        result.extend(dict(base, type='key', key=key) for key in keys)
    elif tag in {'input','textarea'} and kind not in {'checkbox','radio','button','reset','submit','image'}:
        if combobox.editable(control):
            result.insert(0, dict(base, type='key', key='ArrowDown'))
        result += [dict(base,type='fill',value='audit@example.invalid' if kind=='email' else 'Accessibility audit'),
                   dict(base,type='fill',value='')]
    else:
        result += [dict(base,type='key',key=k) for k in (['ArrowDown','ArrowUp','Home','End','Enter','Escape'] if
                    tag=='select' or role in {'combobox','listbox','menu','tab','slider','treeitem'} else ['Enter','Space'])]
    return result,None


def validate_budget(states, steps, depth):
    for value,limit,name in [(states,500,'max_states'),(steps,10000,'max_steps'),(depth,30,'max_depth')]:
        if type(value) is not int or not 1<=value<=limit:raise ValueError(f'{name}は1〜{limit}の整数')


KEY_STATE = r'''element => {
    const details = element.parentElement;
    return {
        connected: element.isConnected,
        document: performance.timeOrigin,
        state: {
            open: element.matches('summary') && details?.matches('details') ? details.open : null,
            expanded: element.getAttribute('aria-expanded'),
            pressed: element.getAttribute('aria-pressed'),
            checked: element.matches('input[type=checkbox], input[type=radio]')
                ? element.checked : element.getAttribute('aria-checked'),
            selected: element.getAttribute('aria-selected'),
            selectedIndex: element.matches('select') ? element.selectedIndex : null,
        }
    };
}'''


def is_telemetry(request, page_url):
    if request.method != 'POST' or request.is_navigation_request() or request.resource_type not in {'ping', 'fetch', 'xhr'}:
        return False
    target = urlsplit(request.url)
    page = urlsplit(page_url)
    analytics_hosts = {'www.google-analytics.com', 'www.google.com'}
    return (target.scheme == 'https' and target.netloc in analytics_hosts and target.path == '/g/collect'
            or (target.scheme, target.netloc) == (page.scheme, page.netloc) and target.path == '/cdn-cgi/rum')


async def press_observed_key(page, target, action, observer, effect, *, function_result=None, toggle=None):
    from playwright.async_api import Error as BrowserError

    handle = None
    before = None
    with suppress(BrowserError):
        handle = await target.element_handle(timeout=1000)
        if handle is not None:
            await handle.evaluate('(e) => { window.__wcagExpectedInputTarget = e; }')
            before = await handle.evaluate(KEY_STATE)
            if function_result is not None:
                function_result['before'] = await handle.evaluate('(e) => window.__wcagFunctionOutput("before", e)')
            if toggle is not None:
                disclosure = await handle.evaluate('(e) => window.__wcagDisclosure(e, false)')
                if disclosure and disclosure['content_toggle']:
                    toggle.update(before=disclosure, after=None)
    first_event = len(observer.events)
    try:
        await page.keyboard.press(action['key'])
        wait = await page.evaluate('() => window.__wcagWaitForUpdates()')
        if toggle:
            with suppress(BrowserError):
                toggle['after'] = await handle.evaluate('(e) => window.__wcagDisclosure(e, false)')
        if handle is not None and before and wait['status'] == 'quiet':
            with suppress(BrowserError):
                after = await handle.evaluate(KEY_STATE)
                if before['connected'] and after['connected'] and before['document'] == after['document']:
                    event_index = next((index for index in range(first_event, len(observer.events))
                        if observer.events[index].get('expectedTargetMatched') is True
                        and keyboard_checks.matching_keydown(observer.events[index], action['key'])), None)
                    if event_index is not None:
                        effect.update(event_index=event_index, before=before['state'], after=after['state'])
        return wait
    finally:
        if handle is not None:
            with suppress(BrowserError):
                await handle.evaluate('() => { window.__wcagExpectedInputTarget = null; }')
            with suppress(BrowserError):
                await handle.dispose()


async def perform(page, action, *, observer=None, key_effect=None, function_result=None, toggle=None):
    target=page.locator(action['selector'])
    if action['type']=='scroll':await page.evaluate('(p)=>scrollTo(p.x,p.y)',action)
    elif action['type']=='press':await page.keyboard.press(action['key'])
    elif action['type']=='click':
        if function_result is not None:
            function_result['before'] = await target.evaluate('''(e) => {
                window.__wcagExpectedInputTarget = e;
                return window.__wcagFunctionOutput("before", e);
            }''', timeout=1800)
        await target.click(timeout=1800)
    elif action['type']=='hover':await target.hover(timeout=1800)
    elif action['type']=='fill':
        await target.fill(action['value'],timeout=1800);await target.press('Tab')
    elif action['type']=='key':
        # focus() cannot make an unfocusable div keyboard reachable. Find it by
        # actual Tab traversal, then use the widget's own keys.
        reached=False
        for _ in range(120):
            if await target.evaluate('(e)=>e===e.getRootNode().activeElement'):reached=True;break
            if action.get('focused_only'):
                raise ValueError('再生した経路で次のキー操作に必要なフォーカスを確認できない')
            await page.keyboard.press('Tab')
        if not reached:raise KeyboardUnreachable(TAB_UNREACHABLE)
        if key_effect is not None:
            return await press_observed_key(page, target, action, observer, key_effect,
                                            function_result=function_result, toggle=toggle)
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


async def observe_scroll_and_tab(page, dest, data, env, images, label, limit, blocked, native_events, remaining):
    import audit

    # Actual scroll/tile captures reveal sticky/viewport-only content.
    tiles = []
    if images.policy['screenshots'] != 'initial':
        for y in range(0,min(data['scroll']['height'],env['viewport']['height']*20),env['viewport']['height']):
            await page.evaluate('(y)=>scrollTo(0,y)',y);await page.wait_for_timeout(40)
            await images.capture(page, dest/f'tile-{len(tiles):03}.png', kind='state', label=label)
            tiles.append(y)
    audit.save(dest/'tiles.json',{'positions':tiles,'height':data['scroll']['height'],'viewport':env['viewport']})
    if images.policy['screenshots'] != 'initial' and data['scroll']['height'] > env['viewport']['height'] * 20:
        remaining.append(f'{env["id"]}：21画面目以降はスクロール後の表示を追加調査する。')
    if any(i['status']=='skipped' for i in images.summary['screenshots'] if i['path'].startswith(str(dest.relative_to(images.run))+'/')):
        remaining.append(f'{dest.name}：画像設定又は上限で未観察の表示がある。')
    trace_stop = await record_tab_trace(page, dest, limit, blocked, native_events)
    if trace_stop:
        evidence = (dest/'keyboard-trace-stop.json').relative_to(images.run).as_posix()
        remaining.append(f'{dest.name}：補助のTab観察は{trace_stop["step"]}回目で中断。'
                                  f'以降は未確認（証拠: {evidence}）。')


QUICK_PENDING_PER_ENVIRONMENT = 12
HOVER_EVENTS = {'mouseover', 'mouseenter', 'mousemove', 'mouseout', 'mouseleave',
                'pointerover', 'pointerenter', 'pointermove', 'pointerout', 'pointerleave'}


def quick_candidates(control, candidates, focused_tab):
    hover = control.get('haspopup') not in (None, '', 'false') or HOVER_EVENTS.intersection(control['events'])
    tab_index = control.get('tabIndex')
    keyboard = (tab_index is not None and tab_index >= 0) or control['selector'] == focused_tab
    preferred_key = 'Space' if control['type'] in {'checkbox', 'radio'} or control['role'] in {
        'checkbox', 'radio', 'switch'
    } else 'Enter'
    for action in candidates:
        if action['type'] == 'hover' and not hover:
            continue
        if action['type'] == 'key':
            if not keyboard:
                continue
            key = action['key']
            if key in {'Enter', 'Space'} and key != preferred_key and not control.get('horizontalTab'):
                continue
        yield action


def control_signature(control):
    return {key: item for key, item in control.items() if key != 'rect'}


def disclosure_candidate(control):
    return (control['tag'] == 'summary' or control['expanded'] is not None
            or control['role'] in {'combobox', 'tab', 'menuitem', 'treeitem'}
            or control['haspopup'] not in (None, '', 'false'))


def keyboard_opening(effect):
    if not effect:
        return False
    before, after = effect['before'], effect['after']
    return ((before['expanded'], after['expanded']) == ('false', 'true')
            or before['open'] is False and after['open'] is True)


def keyboard_opening_key(edge):
    return edge['environment'], edge['fingerprint'], edge['route'][-1]['selector'], edge['focus_after']


def queue_state_actions(value, node, data, env, queued, done, *, quick=False, parent=None, max_depth=30,
                        keyboard_continuation=False, repeated_state=False, combo_record=None,
                        content_keyboard_opening=False):
    route = node['route']
    capture_key = node['capture']
    env_id = env['id']
    focused_tab = data.get('focused_horizontal_tab')
    always_observe = {route[-1]['selector'], focused_tab} if route else set()
    previous_controls = {control['selector']: control_signature(control) for control in (parent or {}).get('controls', [])}
    omitted = Counter(value.get('omitted_candidates', {}))
    pending = sum(job['environment'] == env_id and bool(job['route']) and job['route'] != route
                  for job in value['queue'])

    def enqueue(action, *, dialog_focus=None, newly_available=False, keyboard_followup=False, combo_open=False, combo_panel=None):
        nonlocal pending
        path = route + [action]
        ident = json.dumps([env_id, path], sort_keys=True)
        if ident in queued or ident in done:
            return
        if len(path) > (max_depth if quick else 30):
            if quick:
                omitted['depth'] += 1
            else:
                value['remaining'].append(f'{capture_key}：深さ30を超える経路の追加検査が必要。')
            return
        if quick and pending >= QUICK_PENDING_PER_ENVIRONMENT and dialog_focus != 'escape':
            omitted['frontier'] += 1
            return
        job = {'environment': env_id, 'route': path}
        if dialog_focus:
            job['dialog_focus'] = dialog_focus
        if newly_available:
            job['newly_available'] = True
        if keyboard_followup:
            job['keyboard_followup'] = True
        if combo_open or combo_panel is not None:
            job['combobox_check'] = True
            job['combobox_panel'] = combo_panel
        value['queue'].append(job)
        queued.add(ident)
        pending += 1

    if combo_record and combo_record.get('followups'):
        opener = route[-1]['selector']
        for key in combo_record['followups']:
            action = {'type': 'key', 'selector': opener, 'key': key, 'focused_only': True}
            enqueue(action, keyboard_followup=True, combo_panel=combo_record['after']['panel_id'])

    if data['modal'] and not repeated_state:
        enqueue({'type': 'press', 'selector': 'body', 'key': 'Escape'}, dialog_focus='escape')
    if keyboard_continuation and content_keyboard_opening:
        enqueue({'type': 'press', 'selector': 'body', 'key': 'Tab'}, keyboard_followup=True)
    controls = data['controls']
    initial_output = quick and not route and keyboard_function.numeric_output(data)
    companion_keys = []
    if quick or keyboard_continuation:
        controls = sorted(controls, key=lambda control: (
            control['selector'] in previous_controls, not disclosure_candidate(control)))
    for control in controls:
        selector = control['selector']
        new_opener = selector not in previous_controls and disclosure_candidate(control)
        if repeated_state and not new_opener:
            continue
        candidates, reason = actions(control, focused_tab)
        if quick and selector not in always_observe and previous_controls.get(selector) == control_signature(control):
            omitted['unchanged_control'] += len(candidates)
            continue
        if reason:
            node.setdefault('deferred', []).append(dict(control, reason=reason))
            value['remaining'].append(f'{env_id} / {selector}：{reason}')
        if quick:
            selected = list(quick_candidates(control, candidates, focused_tab))
            companions = []
            if initial_output and selector != focused_tab:
                # The companion activation key can be the only route to the same result.
                already_selected = {action['key'] for action in selected if action['type'] == 'key'}
                if already_selected.intersection(keyboard_function.ACTIVATION_KEYS):
                    companions = [action for action in candidates
                                  if action.get('key') in keyboard_function.ACTIVATION_KEYS - already_selected]
                    companion_keys.extend(companions)
            omitted['input_variations'] += len(candidates) - len(selected) - len(companions)
            candidates = selected
        newly_available = quick and bool(route) and selector not in previous_controls
        for action in candidates:
            followup = keyboard_continuation and new_opener and action['type'] == 'key'
            combo_open = combobox.editable(control) and action.get('key') == 'ArrowDown'
            if (repeated_state and not followup) or (combo_open and selector in previous_controls):
                continue
            phase = 'button' if control.get('buttonInModal') and dialog_focus.activation(action) else None
            enqueue(action, dialog_focus=phase, newly_available=newly_available,
                    keyboard_followup=followup or combo_open, combo_open=combo_open)

    if keyboard_continuation and not content_keyboard_opening:
        enqueue({'type': 'press', 'selector': 'body', 'key': 'Tab'}, keyboard_followup=True)

    for action in companion_keys:
        enqueue(action)

    # A real scroll can reveal lazy content even if the initial screenshot was full-page.
    positions = {(0, env['viewport']['height']),
                 (0, max(0, data['scroll']['height'] - env['viewport']['height'])),
                 (max(0, data['scroll']['width'] - env['viewport']['width']), 0)}
    if not repeated_state and (not quick or not route):
        for x, y in sorted(positions - {(0, 0)}):
            if x or data['scroll']['height'] > env['viewport']['height']:
                enqueue({'type': 'scroll', 'selector': 'body', 'x': x, 'y': y})
    if quick:
        value['omitted_candidates'] = {key: count for key, count in omitted.items() if count}



def queue_disclosure_close(value, edge, observation, queued, done, *, quick, max_depth):
    action = {'type': 'press', 'selector': 'body', 'key': 'Escape'}
    metadata = dict(disclosure_opener=observation['opener'], disclosure_panel=observation['panel'])
    queue_disclosure_step(value, edge, action, metadata, queued, done, quick=quick, max_depth=max_depth)


def queue_disclosure_step(value, edge, action, metadata, queued, done, *, quick, max_depth, extra_steps=0):
    path = edge['route'] + [action]
    env = edge['environment']
    ident = json.dumps([env, path], sort_keys=True)
    if ident in queued or ident in done:
        return
    if len(path) + extra_steps > (max_depth if quick else 30):
        if quick:
            omitted = value.setdefault('omitted_candidates', {})
            omitted['depth'] = omitted.get('depth', 0) + 1
        else:
            value['remaining'].append(f"{env}：深さ30を超える {action['key']} の追加検査が必要。")
        return
    if quick:
        pending = sum(job['environment'] == env and bool(job['route']) and job['route'] != edge['route']
                      for job in value['queue'])
        if pending >= QUICK_PENDING_PER_ENVIRONMENT:
            omitted = value.setdefault('omitted_candidates', {})
            omitted['frontier'] = omitted.get('frontier', 0) + 1
            return
    value['queue'].append(dict(environment=env, route=path, keyboard_followup=True, **metadata))
    queued.add(ident)


def status(run):
    import audit
    path=Path(run)/'exploration.json'
    if not path.exists():return {'required':False,'complete':True,'remaining':[],'nodes':[],'edges':[]}
    value=audit.load(path)
    graph_digest=audit.digest(value)
    for item in value.get('proof',[]):
        if audit.evidence_item(Path(run),item['path'])!=item:raise ValueError('探索の証拠が変更された：'+item['path'])
    if value.get('deferred'):
        remaining = ['操作探索は未実施。必要なときに追加で開始できる。']
        if value['queue']:
            remaining.append(f"初期状態の収集待ち {len(value['queue'])}環境")
    else:
        remaining = [f"探索待ち {len(value['queue'])}経路"] if value['queue'] else []
    resolved=set()
    pointer=audit.run_plan(Path(run)).get('exploration_review')
    if pointer:
        location=(Path(run)/pointer).resolve()
        if not location.is_relative_to(Path(run).resolve()):raise ValueError('追加検査はrun内に保存する')
        review=audit.load(location)
        for proof in review['verified_evidence']:
            if audit.evidence_item(Path(run),proof['path'])!=proof:raise ValueError('追加検査の証拠が変更された')
        if review['graph_digest']==graph_digest:resolved={r['item'] for r in review.get('resolutions',[])}
    if omitted := sum(value.get('omitted_candidates', {}).values()):
        remaining.append(f'簡易探索で省略した操作候補は{omitted}件。必要な操作は個別に確認する。')
    remaining += [r for r in value.get('remaining',[]) if r not in resolved]
    if value.get('running'):
        resume_option = ' --initial-only' if value.get('deferred') else ''
        remaining.append(f'探索中又は途中停止。page-audit --resume{resume_option}で再開する。')
    return dict(value,graph_digest=graph_digest,required=True,complete=not remaining and bool(value['nodes']),remaining=remaining)


async def _explore(run, *, max_states=None, max_steps=None, max_depth=None, initial_only=False,
                   start_exploration=False, quick_explore=False):
    import audit
    from playwright.async_api import async_playwright
    run=Path(run);meta,_=audit.run_catalog(run,for_write=True);config=meta['config'];url=config['scope']['pages'][0]
    if config['scope'].get('mode')!='configured' or len(config['scope']['pages'])!=1:
        raise ValueError('探索はconfiguredの1ページで実行する')
    if any(env.get('zoom',1)!=1 for env in config['environments']):
        raise ValueError('自動探索の環境はzoom=1にする。実ブラウザー拡大は別のprobeで検証する')
    checkpoint=run/'exploration.json'
    if checkpoint.exists():status(run)
    checks={check['id']:check for check in keyboard_checks.validate(config)}
    hover_paths = {check['id']: check for check in config.get('hover_checks', [])}
    border_paths = {check['id']: check for check in config.get('border_checks', [])}
    text_paths = {check['id']: check for check in config.get('text_contrast_checks', [])}
    visual_scope = config.get('visual_structure_scope')
    observe_explored_structure = config.get('visual_structure_states') == 'explored'
    sources = [Path(path).read_text() for path in (
        __file__, combobox.__file__, keyboard_checks.__file__, keyboard_frames.__file__, keyboard_function.__file__,
        hover_checks.__file__, dialog_focus.__file__,
        focus_occlusion.__file__, focus_image_pair.__file__, border_contrast.__file__, text_paint.__file__,
        visual_structure.__file__, operation_impact.__file__, disclosure_close.__file__, ROOT/'vendor/axe.min.js')]
    implementation = sha256((SCRIPT + FOCUS + INVENTORY + INIT_SCRIPT + ''.join(sources)).encode()).hexdigest()
    initial_jobs = [{'environment': env['id'], 'route': []} for env in config['environments']]
    declared_jobs = {'keyboard_check': checks, 'hover_check': hover_paths,
                     'border_check': border_paths, 'text_check': text_paths}
    full_jobs = []
    for initial in initial_jobs:
        full_jobs.append(initial)
        for field, checks_by_id in declared_jobs.items():
            full_jobs.extend(dict(initial, **{field: check_id}) for check_id in checks_by_id)
    value=audit.load(checkpoint) if checkpoint.exists() else {'schema_version':'1','config_digest':meta['config_digest'],
        'implementation_digest':implementation,
        'queue': initial_jobs if initial_only else full_jobs, 'deferred': initial_only,
        'nodes':[],'edges':[],'remaining':[],'proof':[],'steps':0}
    if value['config_digest']!=meta['config_digest']:raise ValueError('探索と設定の版が不一致')
    if value.get('implementation_digest')!=implementation:raise ValueError('探索の実装が変わったため新しいrunで実行する')
    if initial_only and not value.get('deferred'):
        raise ValueError('操作探索を開始済みのrunでは初期状態だけの収集に戻せない')
    if value.get('deferred') and not (initial_only or start_exploration):
        raise ValueError('操作探索を開始するには --resume --explore を指定する')
    if quick_explore and checkpoint.exists() and not (value.get('deferred') or value.get('quick_explore')):
        raise ValueError('通常の操作探索を開始済みのrunでは簡易探索に切り替えられない')
    quick = value.get('quick_explore', False) or quick_explore
    value['quick_explore'] = quick
    if max_states is None:
        max_states = 16 if quick else 64
    if max_steps is None:
        max_steps = 24 if quick else 512
    if max_depth is None:
        max_depth = 3 if quick else 8
    validate_budget(max_states, max_steps, max_depth)
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
    captured_routes = {json.dumps([node['environment'], node['route']], sort_keys=True): node for node in value['nodes']}
    for edge in value['edges']:
        if prior := seen.get((edge['environment'], edge.get('fingerprint'))):
            captured_routes.setdefault(json.dumps([edge['environment'], edge['route']], sort_keys=True), prior)
    keyboard_openings = {keyboard_opening_key(edge) for edge in value['edges'] if edge.get('continued_keyboard_opening')}
    operation_counts = Counter(edge['environment'] for edge in value['edges'] if edge['route'])
    done={json.dumps([e['environment'],e['route']],sort_keys=True) for e in value['edges']}
    queued={json.dumps([j['environment'],j['route']],sort_keys=True) for j in value['queue']}
    if value.get('deferred') and start_exploration:
        observed = {node['environment']: node for node in value['nodes']}
        value['queue'] = [
            dict(job, initial_input=True) if job['environment'] in observed and job in initial_jobs else job
            for job in full_jobs
        ]
        queued = {json.dumps([job['environment'], job['route']], sort_keys=True) for job in value['queue']}
        for env_name, node in observed.items():
            data = audit.load(run / node['evidence_dir'] / 'state.json')
            queue_state_actions(value, node, data, envs[env_name], queued, done, quick=quick, max_depth=max_depth)
        value['deferred'] = False
    value['running']=True;value['manifest']=manifest
    value['limits']={'max_states':max_states,'max_steps':max_steps,'max_depth':max_depth}
    with run_lock(run):audit.save(checkpoint,value);audit.save(run/'capture-manifest.json',manifest)
    async with async_playwright() as pw:
        browser_args = ['--no-sandbox']
        if images.policy['screenshots'] != 'off':
            browser_args.append(SOFTWARE_COMPOSITING)
        if text_paths:
            browser_args.append('--force-color-profile=srgb')
        browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=browser_args)
        try:
            while value['queue'] and value['steps']<max_steps:
                if (quick and value['queue'][0]['route']
                        and value['queue'][0].get('dialog_focus') not in {'escape', 'tab'}):
                    # Keep both viewports represented before pursuing more paths in either.
                    index = min(range(len(value['queue'])), key=lambda i: (
                        bool(value['queue'][i]['route']),
                        operation_counts[value['queue'][i]['environment']],
                        not value['queue'][i].get('keyboard_followup'),
                        not value['queue'][i].get('newly_available'),
                        len(value['queue'][i]['route']),
                    ))
                    value['queue'].insert(0, value['queue'].pop(index))
                job=value['queue'][0];env=envs[job['environment']];route=job['route']
                images.environment = env['id']
                action_label = None
                if route:
                    last = route[-1]
                    operation = last.get('key') or ACTION_LABELS[last['type']]
                    target = last['selector']
                    action_label = f'{operation}（{target}）' if target != 'body' else operation
                check=checks.get(job.get('keyboard_check'))
                hover=hover_paths.get(job.get('hover_check'))
                border=border_paths.get(job.get('border_check'))
                text_check = text_paths.get(job.get('text_check'))
                initial_input = job.get('initial_input')
                declared = check or hover or border or text_check
                if not (declared or initial_input) and (len(value['nodes'])>=max_states or len(route)>max_depth):break
                check_record=dict(id=check['id'], name=check['name'], criterion=check['criterion'],
                                  outcome='cant_tell', steps=[]) if check else None
                if check and check['criterion'] in keyboard_checks.VISUAL_CONDITIONS:
                    check_record['target'] = check['steps'][-1]['focus']
                hover_record = dict(id=hover['id'], name=hover['name'], trigger=hover['trigger'], popup=hover['popup'],
                                    steps=[], observations=[]) if hover else None
                border_record = dict(border, status='cant_tell', observed='測定に必要な画像を確認できない。') if border else None
                text_record = dict(text_check, status='hold', observed='測定に必要な状態を確認できない。') if text_check else None
                allowed_navigation={urldefrag(normalize(url))[0]}
                context=await browser.new_context(viewport=env['viewport'],locale=config.get('locale','ja-JP'),storage_state=config.get('auth_state'),service_workers='block',accept_downloads=False)
                observer=InputObserver(10000);blocked=[]
                await context.expose_binding('__wcagAuditInput',observer.accept)
                await context.add_init_script(INIT_SCRIPT);await context.add_init_script(SCRIPT)
                freeze_requests = False
                async def guard(request_route):
                    request=request_route.request
                    navigation=request.is_navigation_request()
                    allowed_method=request.method in {'GET','HEAD','OPTIONS'}
                    allowed_document=urldefrag(normalize(request.url))[0] in allowed_navigation
                    if freeze_requests or not allowed_method or (navigation and not declared and not allowed_document):
                        blocked.append({'method': request.method, 'url': request.url,
                                        'telemetry': not freeze_requests and is_telemetry(request, url)})
                        await request_route.abort()
                    elif declared and navigation:
                        # Playwright does not dispatch route handlers for every HTTP redirect.
                        # Fetch only the permitted document and refuse redirect responses.
                        await keyboard_checks.load_document(request_route, page, blocked, allowed_navigation, frame_scope)
                    else:
                        await request_route.continue_()
                await context.route('**/*',guard)
                await context.route_web_socket('**/*',lambda socket:socket.close())
                page=await context.new_page()
                dialog_observation = None
                if phase := job.get('dialog_focus'):
                    dialog_observation = dialog_focus.DialogFocus(page, observer, route, phase)
                if text_check:
                    await page.add_init_script(f'({text_paint.LOAD_OBSERVER})()')
                frame_scope=keyboard_frames.FrameScope(page, check.get('frame') if check else None)
                error=None;data=None;native_events=[];settling=[]
                action_index = unreachable_step = None
                combo_record = dict(key=route[-1]['key'], before=None, after=None) if job.get('combobox_check') else None
                key_effect = {}
                function_result = None
                before_operation = None
                impact = None
                disclosure_at_tab = None
                toggle_record = {}
                return_record = None
                toggle_target = job.get('toggle_return')
                toggle_close = job.get('toggle_close', False)
                close_record = {'before': None, 'after': None} if job.get('disclosure_opener') else None
                escape_input = False
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
                image_pair = None
                focus_outline = None
                structure_observation = None
                if check and check['criterion'] == '2.4.7':
                    image_pair = focus_image_pair.FocusImagePair(page.main_frame, check_record['target'], images, dest)
                if check and check['criterion'] == '1.4.11':
                    focus_outline = border_contrast.FocusOutline(page, check_record['target'], run, dest/'focus-outline.png')
                try:
                    response=await page.goto(url,wait_until='domcontentloaded',timeout=20000)
                    if response and response.status>=400:raise ValueError(f'HTTP {response.status}')
                    if page.url.startswith('chrome-error:'):
                        raise ValueError('Chromiumのエラー画面を検査範囲から除外した。')
                    settling.append(await page.evaluate('() => window.__wcagWaitForUpdates()'))
                    if declared:
                        if settling[-1]['status'] != 'quiet':
                            raise ValueError('初期表示の更新が観察範囲に収まらない')

                        def interrupted():
                            return bool(blocked or native_events)

                        if hover:
                            await hover_checks.run_path(page, hover, observer, interrupted, hover_record)
                        elif border:
                            if interrupted():
                                raise ValueError('通信・ページ移動の制限又はブラウザーの分岐で測定を中断した')
                            border_record.update(await border_contrast.observe(page, border['target'], images, dest/'border-viewport.png'))
                        elif text_check:
                            freeze_requests = True
                            if not interrupted():
                                text_record.update(await text_paint.observe(page, text_check, dest, interrupted))
                        else:
                            await keyboard_checks.run_path(page, check, allowed_navigation, check_record, observer,
                                                           interrupted, frame_scope, image_pair=image_pair,
                                                           focus_outline=focus_outline)
                            if check_record['steps']:
                                measurement = check_record['steps'][-1].get('occlusion')
                                if measurement and not interrupted():
                                    screenshot = dest/'focused-viewport.png'
                                    try:
                                        captured = await images.capture(page, screenshot, kind='detail')
                                    except Exception as exc:
                                        measurement['image_error'] = str(exc)
                                    else:
                                        if captured:
                                            measurement['image'] = screenshot.name
                    elif initial_input:
                        current = await page.evaluate('() => window.__wcagExplore()')
                        await observe_scroll_and_tab(page, dest, current, env, images, None,
                            min(config.get('keyboard_steps', 30), 120), blocked, native_events, value['remaining'])
                    else:
                        for action_index, action in enumerate(route, 1):
                            capture_action = (
                                images.policy['screenshots'] == 'all' and action_index == len(route)
                                and not blocked and not native_events
                            )
                            if dialog_observation:
                                if phase == 'tab' and (blocked or native_events or any(
                                        wait['status'] != 'quiet' for wait in settling)):
                                    raise ValueError('ダイアログを調べる経路で通信制限又は表示の更新が続いた。')
                                await dialog_observation.before(action_index, action)
                            if capture_action:
                                await images.capture(page, dest/'action-before.png', kind='action-before',
                                                     label=action_label, best_effort=True)
                            observe_combo = combo_record is not None and action_index == len(route)
                            if observe_combo:
                                before_combo = await combobox.observe(page, action['selector'])
                                combo_record['before'] = before_combo
                                if job['combobox_panel'] is not None and (
                                    not before_combo or not before_combo['visible'] or not before_combo['focused']
                                    or before_combo['panel_id'] != job['combobox_panel']
                                ):
                                    raise ValueError('キー入力の前に同じコンボボックスの候補を再現できない。')
                            if quick and action_index == len(route):
                                before_operation, document_start = await page.evaluate("""() => {
                                    const before = window.__wcagExplore('before');
                                    window.__wcagBeginOperation();
                                    return [before, performance.timeOrigin];
                                }""")
                                operation_impact.compact(before_operation)
                                if (len(route) == 1 and keyboard_function.activation(action)
                                        and (result_output := keyboard_function.numeric_output(before_operation))):
                                    function_result = dict(start=fingerprint(before_operation),
                                                           initial_value=result_output['value'].strip(),
                                                           first_event=len(observer.events))
                            closing = close_record is not None and action_index == len(route)
                            if closing:
                                before = await disclosure_close.observe(page, job['disclosure_opener'], expect_input=True)
                                close_record['before'] = before
                                if not disclosure_close.ready(before) or before['panel'] != job['disclosure_panel']:
                                    raise ValueError('Escapeの前に同じ領域内のフォーカスを再現できない。')
                                first_escape_event = len(observer.events)
                            observe_key = (action_index == len(route) and action['type'] == 'key'
                                           and (observe_combo or all(step['type'] in {'key', 'press'} for step in route)))
                            returning = toggle_target and action_index == len(route) - int(toggle_close)
                            if returning:
                                before = await disclosure_close.observe(page, toggle_target['opener'], expect_input=True)
                                return_record = {'before': before, 'after': None, 'event_index': None}
                                first_return_event = len(observer.events)
                            if toggle_close and action_index == len(route):
                                before = await disclosure_close.observe(page, toggle_target['opener'])
                                if (not disclosure_close.same_panel(return_record['after'], before)
                                        or not disclosure_close.content_open(before)
                                        or before['focus'] != toggle_target['opener']):
                                    raise ValueError('閉じるキーの前に同じ開閉ボタンと領域を確認できない。')
                            observe_toggle = observe_key and action['key'] in {'Enter', 'Space'}
                            settling.append(await perform(page, action, observer=observer,
                                                         key_effect=key_effect if observe_key else None,
                                                         function_result=function_result,
                                                         toggle=toggle_record if observe_toggle else None))
                            if function_result is not None and function_result.get('before'):
                                function_result['after'] = await page.evaluate('() => window.__wcagFunctionOutput("after")')
                            if returning:
                                await page.evaluate('() => { window.__wcagExpectedInputTarget = null; }')
                                return_record['after'] = await disclosure_close.observe(page, toggle_target['opener'])
                                return_record['event_index'] = next((index for index in range(first_return_event, len(observer.events))
                                    if observer.events[index].get('expectedTargetMatched') is True
                                    and keyboard_checks.matching_keydown(observer.events[index], 'Shift+Tab')), None)
                                if toggle_close and (observer.dropped or not disclosure_close.returned_to_opener(
                                        return_record, toggle_target)):
                                    raise ValueError('Shift+Tabで同じ開閉ボタンへ戻れたことを確認できない。')
                            if closing:
                                await page.evaluate('() => { window.__wcagExpectedInputTarget = null; }')
                                close_record['after'] = await disclosure_close.observe(page, job['disclosure_opener'])
                                escape_input = any(event.get('expectedTargetMatched') is True
                                                   and keyboard_checks.matching_keydown(event, 'Escape')
                                                   for event in observer.events[first_escape_event:])
                            if dialog_observation:
                                await dialog_observation.after(action_index, action)
                            if observe_combo:
                                combo_record['after'] = await combobox.observe(page, action['selector'])
                            if capture_action and not blocked and not native_events:
                                await images.capture(page, dest/'action-after.png', kind='action-after',
                                                     label=action_label, best_effort=True)
                        if page.url.startswith('chrome-error:'):
                            raise ValueError('Chromiumのエラー画面を検査範囲から除外した。')
                        label_observations=await state_labels.observe(page,route,labels)
                        matched_labels=state_labels.verified(labels,route,label_observations)
                        if before_operation is not None:
                            data, mutations, after_start = await page.evaluate("""() =>
                                [window.__wcagExplore(true), window.__wcagOperationMutations(), performance.timeOrigin]
                            """)
                            operation_impact.compact(data)
                            impact = operation_impact.difference(before_operation, data, route[-1], mutations,
                                                                 new_document=document_start != after_start)
                        else:
                            data = await page.evaluate('() => window.__wcagExplore(true)')
                            operation_impact.compact(data)
                        if (job.get('keyboard_followup') and len(route) >= 2 and route[-1]['type'] == 'press'
                                and route[-1]['key'] == 'Tab' and route[-2]['type'] == 'key'):
                            disclosure_at_tab = await disclosure_close.observe(page, route[-2]['selector'])
                        data['observation_wait']=settling
                        data['state_labels']=label_observations
                        inv=await page.evaluate(INVENTORY);audit.save(dest/'inventory.json',inv)
                        capture_structure = visual_scope and (not route or observe_explored_structure)
                        prepared_structure = None
                        structure_deadline = None
                        if capture_structure:
                            if blocked or native_events:
                                prepared_structure = visual_structure.not_observed(
                                    visual_scope, '制限した通信・ページ移動又はブラウザーの分岐がある。')
                            elif urldefrag(normalize(page.url))[0] not in allowed_navigation:
                                prepared_structure = visual_structure.not_observed(
                                    visual_scope, '観察時のURLが指定したURLと一致しない。')
                            elif any(wait['status'] != 'quiet' for wait in settling):
                                prepared_structure = visual_structure.not_observed(
                                    visual_scope, '表示の更新が観察範囲に収まらない。')
                            elif observe_explored_structure:
                                structure_deadline = asyncio.get_running_loop().time() + visual_structure.OBSERVATION_SECONDS
                                prepared_structure = await visual_structure.snapshot(page, visual_scope, deadline=structure_deadline)
                                shape = visual_structure.candidate_shape(prepared_structure)
                                if shape:
                                    data['visual_structure_shape'] = shape
                        audit.save(dest/'state.json',data)
                        state_key = (env['id'], fingerprint(data))
                        if impact is not None and state_key in seen and not matched_labels:
                            impact['axe'] = {'mode': 'same_state', 'baseline': seen[state_key]['evidence_dir'] + '/axe.json'}
                        if state_key not in seen or matched_labels:
                            if capture_structure:
                                structure_observation = await visual_structure.observe(
                                    page, visual_scope, prepared_structure, deadline=structure_deadline)
                            # Capture the audited state before diagnostic scrolling changes the DOM.
                            cdp=await context.new_cdp_session(page)
                            audit.save(dest/'accessibility-tree.json',await cdp.send('Accessibility.getFullAXTree'));await cdp.detach()
                            await page.evaluate((ROOT/'vendor/axe.min.js').read_text())
                            baseline = None
                            reused = {}
                            if (impact is not None and not blocked and not native_events
                                    and all(wait['status'] == 'quiet' for wait in settling)
                                    and operation_impact.can_reuse(before_operation, data, impact)):
                                baseline = captured_routes.get(json.dumps([env['id'], route[:-1]], sort_keys=True))
                                if baseline is not None:
                                    prior_dir = run / baseline['evidence_dir']
                                    reused = operation_impact.reusable_nodes(
                                        before_operation, data, audit.load(prior_dir/'state.json'),
                                        audit.load(prior_dir/'axe.json'), impact)
                            results, axe_scope = await operation_impact.run_axe(page, data, reused)
                            audit.save(dest/'axe.json', results)
                            if impact is not None:
                                impact['axe'] = axe_scope
                                if axe_scope['mode'] == 'mixed':
                                    axe_scope['baseline'] = baseline['evidence_dir'] + '/axe.json'
                            if matched_labels:
                                current_observations = await state_labels.observe(page, route, labels)
                                still_matched = state_labels.verified(labels, route, current_observations)
                                data['state_labels'] = [record for record in label_observations
                                                        if not record['matched'] or record['id'] in still_matched]
                                audit.save(dest/'state.json', data)
                            full_page = not route or data['scroll']['height'] <= env['viewport']['height'] * 20
                            await images.capture(page, dest/'page.png', kind='state' if route else 'initial',
                                                 label=action_label, full_page=full_page)
                            if not initial_only:
                                await observe_scroll_and_tab(page, dest, data, env, images, action_label,
                                    min(config.get('keyboard_steps', 30), 120), blocked, native_events, value['remaining'])
                except KeyboardUnreachable as exc:
                    error = str(exc)
                    unreachable_step = action_index
                except Exception as exc:
                    error = str(exc) or type(exc).__name__
                finally:
                    interrupted_reason = error or ('制限した通信・ページ移動又はブラウザーの分岐がある。' if blocked or native_events else None)
                    if check_record is not None:
                        if interrupted_reason:
                            check_record.update(outcome='cant_tell', reason=interrupted_reason)
                        if image_pair is not None:
                            if check_record['outcome'] != 'passed':
                                image_pair.invalidate(check_record['reason'])
                            await image_pair.close()
                        if focus_outline is not None:
                            await focus_outline.close()
                        audit.save(dest/'keyboard-check.json',check_record)
                    if hover_record is not None:
                        if interrupted_reason:
                            hover_checks.invalidate(hover_record, hover, interrupted_reason)
                        audit.save(dest/'hover-check.json', hover_record)
                    if border_record is not None:
                        if interrupted_reason:
                            border_record.update(status='cant_tell', observed=interrupted_reason)
                        audit.save(dest/'border-check.json', border_record)
                    if text_record is not None:
                        if interrupted_reason:
                            if text_record.get('reason') != 'resource_request_blocked':
                                text_record.update(status='hold', reason='measurement_interrupted', observed=interrupted_reason)
                            for field in ('ratio', 'threshold', 'threshold_met'):
                                text_record.pop(field, None)
                        audit.save(dest/'text-contrast.json', text_record)
                    if dialog_observation:
                        if interrupted_reason:
                            dialog_observation.invalidate(interrupted_reason)
                        elif any(wait['status'] != 'quiet' for wait in settling):
                            dialog_observation.invalidate('キー入力後の表示更新が観察範囲に収まらない。')
                        audit.save(dest/dialog_focus.EVIDENCE_FILE, dialog_observation.record)
                    if structure_observation is not None or (visual_scope and not (declared or route)):
                        if interrupted_reason:
                            structure_observation = visual_structure.not_observed(visual_scope, interrupted_reason)
                        if structure_observation is not None:
                            audit.save(dest/visual_structure.EVIDENCE_FILE, structure_observation)
                    edge = dict(job, error=error, blocked_requests=blocked, native_events=native_events)
                    if key_effect:
                        edge['key_effect'] = key_effect
                    if function_result is not None:
                        keyboard_function.finish(function_result, route[0], key_effect, observer, settling,
                                                 interrupted_reason)
                        edge['function_result'] = function_result
                    opened_with_key = not combo_record and keyboard_opening(key_effect)
                    quiet_key_route = (not error and not native_events
                                       and all(request.get('telemetry') is True for request in blocked)
                                       and all(wait['status'] == 'quiet' for wait in settling))
                    if data and route and (
                        (opened_with_key or job.get('keyboard_followup')) and quiet_key_route
                        or route[-1].get('key') in HORIZONTAL_TAB_ARROWS and not interrupted_reason
                    ):
                        edge['focus_after'] = data.get('deep_focus', data['focus']['selector'])
                    if close_record is not None:
                        disclosure_close.finish(close_record, quiet_key_route and escape_input)
                        edge['disclosure_close'] = close_record
                    if toggle_record:
                        edge['disclosure_toggle'] = disclosure_close.toggle_result(
                            toggle_record['before'], toggle_record['after'], quiet_key_route and bool(key_effect)
                            and not observer.dropped)
                    if return_record is not None:
                        edge['disclosure_return'] = return_record
                    if unreachable_step is not None:
                        edge['keyboard_unreachable_step'] = unreachable_step
                    if combo_record is not None:
                        combobox.finish(combo_record, quiet_key_route and bool(key_effect))
                        edge['combobox'] = combo_record
                    if impact is not None:
                        if error and 'axe' not in impact:
                            impact['axe'] = {'mode': 'not_observed'}
                        audit.save(dest/'operation-impact.json', impact)
                    audit.save(dest/'transition.json', dict(edge, settling=settling))
                    audit.save(dest/'input-events.json',observer.export())
                    await context.close()
                proof=[audit.evidence_item(run,str(p.relative_to(run))) for p in sorted(dest.iterdir()) if p.is_file()]
                value['proof'].extend(proof)
                edge['evidence_dir'] = str(dest.relative_to(run))
                if check and check_record['outcome']=='cant_tell':
                    value['remaining'].append(f"{env['id']} / キーボード経路 {check['name']}：{check_record['reason']}")
                if image_pair is not None and check_record['outcome'] == 'passed':
                    receipt = image_pair.receipt
                    if receipt['status'] != 'captured':
                        value['remaining'].append(f"{env['id']} / フォーカスの画像 {check['name']}：{receipt['reason']}")
                if hover:
                    for observation in hover_record['observations']:
                        if observation['outcome'] == 'cant_tell':
                            value['remaining'].append(f"{env['id']} / ホバー経路 {hover['name']} / "
                                                      f"{observation['aspect']}：{observation['observed']}")
                if border and border_record['status'] != 'measured':
                    value['remaining'].append(f"{env['id']} / 外枠の測定 {border['name']}：{border_record['observed']}")
                if text_check and text_record['status'] != 'measured':
                    value['remaining'].append(f"{env['id']} / 文字の測定 {text_check['name']}：{text_record['observed']}")
                if dialog_observation and dialog_observation.record['status'] == 'unconfirmed':
                    value['remaining'].append(f"{dest.name} / ダイアログのフォーカス：{dialog_observation.record['reason']}")
                if (dialog_observation and dialog_observation.record['phase'] != 'tab'
                        and dialog_observation.record['status'] == 'closed'):
                    path = route + [{'type': 'press', 'selector': 'body', 'key': 'Tab'}]
                    ident = json.dumps([env['id'], path], sort_keys=True)
                    if quick and len(path) > max_depth:
                        omitted = value.setdefault('omitted_candidates', {})
                        omitted['depth'] = omitted.get('depth', 0) + 1
                    elif len(path) > 30:
                        value['remaining'].append(f'{dest.name}：閉じた後のTabは深さ30の上限で未実施。')
                    elif ident not in queued and ident not in done:
                        followup = dict(environment=env['id'], route=path, dialog_focus='tab')
                        if len(path) <= max_depth:
                            value['queue'].insert(1, followup)
                        else:
                            value['queue'].append(followup)
                        queued.add(ident)
                if (quiet_key_route and disclosure_close.content_open(disclosure_at_tab)
                        and disclosure_at_tab['focus'] != disclosure_at_tab['opener']
                        and route[-2]['key'] in {'Enter', 'Space'}):
                    target = dict(opener=disclosure_at_tab['opener'], panel=disclosure_at_tab['panel'],
                                  focus=disclosure_at_tab['focus'], key=route[-2]['key'])
                    action = {'type': 'press', 'selector': 'body', 'key': 'Shift+Tab'}
                    queue_disclosure_step(value, edge, action, {'toggle_return': target}, queued, done,
                                          quick=quick, max_depth=max_depth, extra_steps=1)
                if quiet_key_route and disclosure_close.ready(disclosure_at_tab):
                    queue_disclosure_close(value, edge, disclosure_at_tab, queued, done,
                                           quick=quick, max_depth=max_depth)
                if (quiet_key_route and return_record is not None and not toggle_close and not observer.dropped
                        and disclosure_close.returned_to_opener(return_record, toggle_target)):
                    action = dict(type='key', selector=toggle_target['opener'], key=toggle_target['key'], focused_only=True)
                    metadata = dict(toggle_return=toggle_target, toggle_close=True)
                    queue_disclosure_step(value, edge, action, metadata, queued, done, quick=quick, max_depth=max_depth)
                value['edges'].append(edge);value['steps']+=1
                if route:
                    operation_counts[env['id']] += 1
                if error and unreachable_step != len(route) and not declared:
                    value['remaining'].append(f'{env["id"]} / {route[-1] if route else "initial"}：{error}')
                if any(request.get('telemetry') is not True for request in blocked):
                    value['remaining'].append(f'{env["id"]}：通信又はページ移動を制限した経路がある。状態を確認する。')
                if native_events:value['remaining'].append(f'{env["id"]}：ブラウザー標準ダイアログ・別窓・ダウンロードの分岐を追加検査する。')
                if any(wait['status']!='quiet' for wait in settling):
                    value['remaining'].append(f'{env["id"]}：DOMと短いタイマーの観察上限又は未観測のコールバックが残る。全非同期完了ではない。')
                if data and not error:
                    edge['fingerprint'] = state_key[1]
                    matched_labels=state_labels.verified(labels,route,data.get('state_labels',[]))
                    parent = captured_routes.get(json.dumps([env['id'], route[:-1]], sort_keys=True)) if route else None
                    keyboard_continuation = False
                    if parent is not None and opened_with_key and quiet_key_route:
                        opening = keyboard_opening_key(edge)
                        if opening not in keyboard_openings:
                            keyboard_openings.add(opening)
                            edge['continued_keyboard_opening'] = True
                            keyboard_continuation = True
                    new_capture = state_key not in seen or matched_labels
                    if new_capture:
                        state='initial' if not route else 'explore-'+attempt
                        capture_key=f'{pid}--{state}--{env["id"]}'
                        node=dict(job,fingerprint=state_key[1],capture=capture_key,evidence_dir=str(dest.relative_to(run)),controls=data['controls'],state_labels=matched_labels)
                        seen[state_key]=node;value['nodes'].append(node)
                        manifest['captures'].append(dict(key=capture_key,page_id=pid,url=url,state=state,environment=env['id'],
                            execution='completed',collection_state='finished',evidence_dir=str(dest.relative_to(run))))
                        for feature in ['frames','canvases','closedRoots']:
                            if data[feature]:value['remaining'].append(f'{capture_key}：{feature}の内部を追加検査する。')
                    node = seen[state_key]
                    if not initial_only and (new_capture or keyboard_continuation or
                                             combo_record and combo_record.get('followups')):
                        route_node = node if new_capture else dict(node, route=route)
                        queue_state_actions(value, route_node, data, env, queued, done,
                                            quick=quick, parent=parent, max_depth=max_depth,
                                            keyboard_continuation=keyboard_continuation, repeated_state=not new_capture,
                                            combo_record=combo_record, content_keyboard_opening=(
                                                edge.get('disclosure_toggle', {}).get('status') == 'opened'))
                    captured_routes[json.dumps([env['id'], route], sort_keys=True)] = node
                value['queue'].pop(0);value['remaining']=list(dict.fromkeys(value['remaining']))
                value['manifest']=manifest
                with run_lock(run):
                    audit.save(checkpoint,value);audit.save(run/'capture-manifest.json',manifest)
                audit.make_plan(run,manifest)
        finally:
            await browser.close()
            found={label for node in value['nodes'] for label in node.get('state_labels',[])}
            if not initial_only:
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
