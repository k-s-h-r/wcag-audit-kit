"""Task assignments share the atomic plan pointer with assessment revisions."""
from collections import Counter
from datetime import datetime, timezone
import re
import uuid

from ledger_lock import run_lock

STATES = {'todo', 'in_progress', 'blocked', 'done'}


def unfinished(case):
    a = case.get('assessment_data')
    return (not a or case['outcome'] == 'cant_tell' or bool(a.get('remaining')) or
            a.get('coverage_complete') is not True or
            any(t.get('outcome') == 'cant_tell' for t in a.get('targets', [])))


def can_finish(case):
    return bool(case.get('assessment_data')) and (not unfinished(case) or
            bool(case['assessment_data'].get('human_handoff')))


def work(plan, create=False):
    if 'work' not in plan:
        if not create:
            return {'tasks': [], 'cases': {}}
        plan['work'] = {'schema_version': '1', 'run_id': uuid.uuid4().hex,
                        'tasks': [], 'cases': {}}
    value = plan['work']
    if value.get('schema_version') != '1':
        raise ValueError('作業台帳の版が不明')
    return value


def validate_work(plan):
    if 'work' not in plan:return
    value=work(plan)
    if not re.fullmatch(r'[0-9a-f]{32}',str(value.get('run_id',''))):
        raise ValueError('作業台帳のrun IDが不正')
    ids = {c['case_id'] for c in plan['cases']}
    assigned = []
    task_ids = []
    for task in value['tasks']:
        task_ids.append(task['id']); assigned.extend(task['case_ids'])
    if (len(task_ids) != len(set(task_ids)) or len(assigned) != len(set(assigned)) or
            not set(assigned).issubset(ids) or not set(value['cases']).issubset(ids)):
        raise ValueError('タスクの重複又は存在しない検査票がある')
    for item in value['cases'].values():
        if any(not isinstance(item.get(k),str) for k in ['owner','state','note']) or item['state'] not in STATES:
            raise ValueError('担当・作業状態・メモの形式が不正')


def task_for(plan, case_id):
    return next((t for t in work(plan)['tasks'] if case_id in t['case_ids']), None)


def assignment(plan, case_id):
    return dict(work(plan)['cases'].get(case_id, {'owner': '', 'state': 'todo', 'note': ''}))


def select(cases, plan, *, task=None, owner=None, page=None, page_exact=None, criterion=None, pending=False):
    if task:
        found = next((t for t in work(plan)['tasks'] if t['id'] == task), None)
        if found is None:
            raise ValueError('タスクIDが存在しない')
        ids = set(found['case_ids']); cases = [c for c in cases if c['case_id'] in ids]
    if owner is not None:
        cases = [c for c in cases if assignment(plan, c['case_id'])['owner'] == owner]
    if page:
        cases = [c for c in cases if page in c['page_url']]
    if page_exact:
        from browser_capture import normalize
        cases = [c for c in cases if normalize(c['page_url']) == normalize(page_exact)]
    if criterion:
        cases = [c for c in cases if c['criterion'] == criterion]
    if pending:
        cases = [c for c in cases if unfinished(c)]
    return cases


def create_tasks(run, *, group_by='page', size=20, owner='', page=None, criterion=None):
    import audit
    if group_by not in {'page', 'criterion', 'none'} or type(size) is not int or not 1 <= size <= 1000:
        raise ValueError('分割単位と1タスクの件数（1〜1000）を指定する')
    if not isinstance(owner,str):raise ValueError('担当者名は文字列にする')
    with run_lock(run):
        audit.run_catalog(run, for_write=True)
        result = audit.outcomes(run); plan = audit.run_plan(run); value = work(plan, create=True)
        allocated = {i for t in value['tasks'] for i in t['case_ids']}
        cases = select(result['cases'], plan, page=page, criterion=criterion, pending=True)
        groups = {}
        for case in cases:
            if case['case_id'] in allocated:
                continue
            key = case['page_url'] if group_by == 'page' else case['criterion'] if group_by == 'criterion' else '検査'
            groups.setdefault(key, []).append(case['case_id'])
        added = []
        for key, ids in groups.items():
            for start in range(0, len(ids), size):
                task = {'id': 'task-' + uuid.uuid4().hex[:12], 'title': key,
                        'case_ids': ids[start:start + size], 'created_at': datetime.now(timezone.utc).isoformat()}
                value['tasks'].append(task); added.append(task)
                for case_id in task['case_ids']:
                    value['cases'][case_id] = {'owner': owner, 'state': 'todo', 'note': ''}
        audit.save(run / 'plan.json', plan)
        return added


def claim(run, task_id, owner, reassign=False):
    import audit
    if not isinstance(owner, str) or not owner.strip():
        raise ValueError('担当者名が必要')
    with run_lock(run):
        audit.run_catalog(run, for_write=True)
        plan = audit.run_plan(run)
        tasks = work(plan)['tasks']; task = next((t for t in tasks if t['id'] == task_id), None)
        if task is None:
            raise ValueError('タスクIDが存在しない')
        values = {i: assignment(plan, i) for i in task['case_ids']}
        if not reassign and any(v['owner'] not in {'', owner} for v in values.values()):
            raise ValueError('別の担当者が取得済み。相談してから--reassignで引き継ぐ')
        for i, value in values.items():
            value['owner'] = owner
            if value['state'] == 'todo': value['state'] = 'in_progress'
            work(plan)['cases'][i] = value
        audit.save(run / 'plan.json', plan)
        return task


def status(run, owner=None):
    import audit
    with run_lock(run):
        result = audit.outcomes(run); plan = audit.run_plan(run); rows = []
        by_id = {c['case_id']: c for c in result['cases']}
        for task in work(plan)['tasks']:
            cases = [by_id[i] for i in task['case_ids']]
            if owner is not None and not any(assignment(plan, c['case_id'])['owner'] == owner for c in cases):
                continue
            rows.append(dict(task, owners=sorted({assignment(plan, c['case_id'])['owner'] for c in cases}),
                             counts=dict(Counter(c['outcome'] for c in cases)),
                             remaining=sum(unfinished(c) for c in cases),
                             human=sum(bool((c['assessment_data'] or {}).get('human_handoff')) for c in cases),
                             work_states=dict(Counter(assignment(plan, c['case_id'])['state'] for c in cases))))
        assigned = {i for t in work(plan)['tasks'] for i in t['case_ids']}
        return {'tasks': rows, 'total_tasks': len(rows),
                'unassigned_pending': sum(unfinished(c) and c['case_id'] not in assigned for c in result['cases']),
                'audit_complete': result['audit_complete']}
