"""Label discovered routes using public operations and observable conditions.

These labels never authorize operations or encode accessibility verdicts.
"""
import re


def validate(labels):
    if not isinstance(labels,list):raise ValueError('exploration_labelsは配列')
    seen=set()
    for label in labels:
        name=label.get('id') if isinstance(label,dict) else None
        if not isinstance(name,str) or not re.fullmatch(r'[a-z0-9-]+',name) or name=='initial' or name in seen:
            raise ValueError('探索ラベルは重複のない状態ID')
        seen.add(name)
        actions=label.get('actions');checks=label.get('assert')
        if not isinstance(actions,list) or not 1<=len(actions)<=30 or not isinstance(checks,list) or not checks:
            raise ValueError('探索ラベルには操作経路と到達条件が必要')
        for action in actions:
            if not isinstance(action,dict) or action.get('type') not in {'click','hover','key','fill','press','scroll'} or not isinstance(action.get('selector'),str) or not action['selector']:
                raise ValueError('探索ラベルの操作経路が不正')
        for check in checks:
            if not isinstance(check,dict) or not set(check)<={'selector','count','visible'} or not isinstance(check.get('selector'),str) or not check['selector'] or not ({'count','visible'} & set(check)):
                raise ValueError('到達条件はselectorとcount又はvisible')
            if 'count' in check and (type(check['count']) is not int or check['count']<0):raise ValueError('countは0以上の整数')
            if 'visible' in check and type(check['visible']) is not bool:raise ValueError('visibleは真偽値')
    return labels


def public_specs(states):
    result=[]
    for state in states:
        # Legacy action hints lack observable assertions and remain unlabelled.
        if 'assert' in state:
            result.append({k:state.get(k) for k in ['id','actions','assert']})
    return validate(result)


def conditions_match(checks,observed):
    if not isinstance(observed,list) or len(checks)!=len(observed):return False
    for check,value in zip(checks,observed):
        if not isinstance(value,dict) or value.get('selector')!=check['selector'] or type(value.get('count')) is not int:return False
        if 'visible' in check and type(value.get('visible')) is not bool:return False
        if any(value.get(k)!=check[k] for k in ['count','visible'] if k in check):return False
    return True


async def observe(page,route,labels):
    result=[]
    for label in labels:
        if label['actions']!=route:continue
        checks=[]
        for check in label['assert']:
            target=page.locator(check['selector']);count=await target.count()
            # Match visible against one unambiguous element, as in configured
            # state assertions. A plural match cannot silently select a member.
            visible=await target.is_visible() if count==1 else False if count==0 else None
            checks.append(dict(selector=check['selector'],count=count,visible=visible))
        result.append(dict(id=label['id'],actions=route,assertions=checks,matched=conditions_match(label['assert'],checks)))
    return result


def verified(labels,route,records):
    if not isinstance(records,list):return []
    result=[]
    for label in labels:
        if label['actions']!=route:continue
        for row in records:
            if isinstance(row,dict) and row.get('id')==label['id'] and row.get('actions')==route and row.get('matched') is True and conditions_match(label['assert'],row.get('assertions')):
                result.append(label['id']);break
    return result
