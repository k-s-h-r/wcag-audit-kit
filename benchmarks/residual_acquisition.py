"""Match requested browser records without turning them into WCAG verdicts."""
from urllib.parse import urlsplit

from . import residual_evidence, residual_focus_context, residual_geometry, residual_traps_order


COMMON = {'checkpoint','kind','targets','page','state','rationale'}
FOCUS_SEQUENCE = {'2.1.2-01','2.4.3-01'}


def supported(contract):
    checkpoint = contract['checkpoint']
    if checkpoint in FOCUS_SEQUENCE and contract['kind'] == 'focus-sequence':
        return (set(contract) == COMMON | {'capture_keys'}
                and isinstance(contract['capture_keys'],list) and bool(contract['capture_keys'])
                and all(key in residual_traps_order.KEYS for key in contract['capture_keys']))
    if checkpoint == '3.2.1-01' and contract['kind'] == 'state-capture':
        return (set(contract) == COMMON | {'captures','url_changes'} and len(contract['targets']) == 1
                and contract['captures'] == ['before-focus','after-focus'] and type(contract['url_changes']) is bool)
    if checkpoint == '2.5.8-01' and contract['kind'] == 'geometry':
        return (set(contract) == COMMON | {'context','expected_height_below'} and len(contract['targets']) == 1
                and contract['context'] == 'inline-in-paragraph'
                and type(contract['expected_height_below']) in (int,float) and contract['expected_height_below'] > 0)
    return False


def focus_watch_complete(snap, targets):
    watched = snap.get('watched')
    return (isinstance(watched,dict) and set(watched) == set(targets)
            and all(isinstance(item,dict) and type(item.get('visible')) is bool
                    and 'expanded' in item and item['expanded'] in ('true','false',None) for item in watched.values()))


def match_focus(plan, data, contract, url):
    targets = contract['targets']
    routes = data.get('routes')
    if plan.get('watch') != targets or not isinstance(routes,list):
        return None
    kind = 'escape' if plan.get('kind') == 'trap' else 'order'
    matching = [route for route in routes if isinstance(route,dict) and route.get('kind') == kind
                and residual_traps_order.trusted_route(route,plan)
                and route['setup'][0]['before']['page'] == url]
    if len(matching) != 1:
        return None
    route = matching[0]
    actions = [*route['setup'], *route['steps']]
    keys = contract['capture_keys']
    start = len(actions) - len(keys)
    if (start < 0 or any(action['action'] != 'Tab' for action in actions[:start])
            or [action['action'] for action in actions[start:]] != keys
            or actions[start]['after']['focus'] != targets[0]):
        return None
    sequence = []
    for entry in actions[start:]:
        before, after = entry['before'], entry['after']
        if not all(focus_watch_complete(snap,targets) for snap in (before,after)):
            return None
        sequence.append(dict(key=entry['action'], before=before['focus'], after=after['focus'],
                             url=after['page'], watched=after['watched']))
    observed = '、'.join(f"{step['key']} {step['before'] or '文書'} → {step['after'] or '文書'}" for step in sequence)
    return dict(targets=[dict(target=target,format='focus-sequence') for target in targets],
                sequence=sequence, observed=observed+'。各操作で表示・展開状態とURLも記録した。')


def match_url(plan, data, contract, url):
    before, after = data.get('before'), data.get('after')
    destination = data.get('after_url')
    if (plan.get('target') != contract['targets'][0] or data.get('before_url') != url
            or not isinstance(before,dict) or before.get('atStart') is not True or not isinstance(after,dict)
            or type(after.get('start')) not in (int,float) or not isinstance(destination,str)
            or not residual_focus_context.trusted_focus(plan,data)):
        return None
    source, target = (urlsplit(location) for location in (url,destination))
    changed = destination != url
    if ((source.scheme,source.netloc) != (target.scheme,target.netloc)
            or changed is not contract['url_changes'] or changed != (before['start'] != after['start'])):
        return None
    observed = f"実Tabが {plan['target']} に届いた。URL {url} → {destination}。"
    return dict(targets=[dict(target=plan['target'],format='state-capture')],
                before_url=url, after_url=destination, observed=observed)


def match_inline_size(plan, data, contract):
    targets = contract['targets']
    items = data.get('items')
    if plan.get('targets') != targets or not isinstance(items,list) or data.get('unresolved') is not False:
        return None
    matches = [item for item in items if isinstance(item,dict) and item.get('id') == targets[0]]
    if (len(matches) != 1 or not residual_geometry.rect_is_valid(matches[0])
            or matches[0].get('inline_text') is not True or matches[0]['height'] >= contract['expected_height_below']):
        return None
    rect = {field:matches[0][field] for field in ('x','y','width','height')}
    return dict(targets=[dict(target=targets[0],format='css-rect',rect=rect)],
                observed=f'文章中のインラインリンクを確認した。矩形は {rect["width"]:g} × {rect["height"]:g} CSS px。')


def match(run, job, progress, contract, frozen, row):
    from . import core

    page,state = row['page'],row['state']
    plans = residual_evidence.plans(job['criterion'],job['checkpoints'],job['states'])
    plan = plans.get(state)
    if plan is None:
        return row
    try:
        attempt,receipt = core.completed_attempt(run,job,progress,page,frozen)
        if attempt is None:
            return row
        _,digest = residual_evidence.fixture_set(frozen,job['criterion'])
        measurement,path = residual_evidence.read_measurement(run,job,page,state,attempt,digest,frozen)
    except (KeyError,TypeError,ValueError):
        return row
    if measurement is None:
        return row
    proof = [item.relative_to(run).as_posix() for item in (receipt,path)]
    data = measurement.get('observations')
    verified = None
    if measurement.get('status') == 'observed' and isinstance(data,dict):
        if contract['checkpoint'] in FOCUS_SEQUENCE:
            verified = match_focus(plan,data,contract,job['urls'][page])
        elif contract['checkpoint'] == '3.2.1-01':
            verified = match_url(plan,data,contract,job['urls'][page])
        else:
            verified = match_inline_size(plan,data,contract)
    if verified is None:
        return dict(row,observed='計測した記録が指定された経路・対象・状態と一致することを確認できない。',evidence=proof)
    return dict(row,status='matched',evidence=proof,**verified)
