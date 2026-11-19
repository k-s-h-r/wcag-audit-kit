#!/usr/bin/env python3
"""Evidence-backed WCAG audit ledger. Browser collection is not a conformance verdict."""
import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import uuid
from urllib.parse import urlsplit
from handoff import validate_handoff, details as handoff_details, markdown as handoff_markdown
from ledger_lock import locked
import run_layout

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT/'references/catalog.json').read_text())
CRITERIA = {c['id']:c for c in CATALOG['criteria']}
LEVELS = {'A': {'A'}, 'AA': {'A','AA'}, 'AAA': {'A','AA','AAA'}}


def load(path):
    p = Path(path)
    if p.suffix == '.json':
        return json.loads(p.read_text())
    import yaml
    return yaml.safe_load(p.read_text())


def save(path, value):
    p = Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    tmp = p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    tmp.replace(p)


def digest(value):
    return sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def run_meta(run):
    meta=load(run/'run.json')
    if digest(meta['config'])!=meta['config_digest']:
        raise ValueError('保存した実行設定が変更された。元のrunを保持して新しいrunを開始する')
    return meta


def run_catalog(run,for_write=False):
    meta=run_meta(run);path=run/'catalog.snapshot.json'
    if for_write and 'verification' in meta['config']:
        from verification_modes import run_catalog as verification_catalog
        verification_catalog(run)
    if path.exists():
        catalog=load(path)
        if digest(catalog)!=meta['catalog_digest']:
            raise ValueError('保存した検査定義のスナップショットが変更された')
    elif meta['catalog_digest']==digest(CATALOG):
        catalog=CATALOG
    else:
        raise ValueError('当時の検査定義のスナップショットがない。元のスキル版を用意する')
    if for_write and meta['catalog_digest']!=digest(CATALOG):
        raise ValueError('検査定義が変更された。旧結果を保持して新しいrunを開始する')
    return meta,catalog


def snapshot_catalog(run):
    meta,catalog=run_catalog(run)
    path=run/'catalog.snapshot.json'
    if not path.exists():save(path,catalog)
    return {'path':str(path),'catalog_digest':meta['catalog_digest']}


def run_plan(run):
    meta=run_meta(run);plan=load(run/'plan.json')
    if plan.get('config_digest')!=meta['config_digest']:
        raise ValueError('検査計画と実行設定のハッシュが不一致')
    if plan.get('catalog_digest',meta['catalog_digest'])!=meta['catalog_digest']:
        raise ValueError('検査計画と保存した検査定義が不一致')
    ids=[c['case_id'] for c in plan['cases']]
    if len(ids)!=len(set(ids)):raise ValueError('検査計画のcase_idが重複している')
    from work_queue import validate_work
    validate_work(plan)
    return plan


def validate_config(c):
    if not isinstance(c,dict) or c.get('schema_version') != '1':
        raise ValueError('schema_versionは文字列"1"')
    if c.get('level') not in LEVELS:
        raise ValueError('levelはA、AA、AAA')
    u = urlsplit(c.get('url',''))
    if u.scheme not in {'http','https'} or not u.netloc or u.username or u.password:
        raise ValueError('認証情報を含めないhttp/https URLを指定する')
    c.setdefault('scope',{})
    s=c['scope'];s.setdefault('include',['/**']);s.setdefault('exclude',[])
    s.setdefault('seeds',['/']);s.setdefault('known_pages',[]);s.setdefault('max_pages',100)
    s.setdefault('mode','discover');s.setdefault('pages',[])
    if s['mode'] not in {'discover','configured'}:raise ValueError('scope.modeはdiscover又はconfigured')
    if not isinstance(s['pages'],list) or any(not isinstance(p,str) or not p for p in s['pages']):raise ValueError('pagesはURL又はパスの一覧')
    if s['mode']=='configured':
        if not s['pages']:raise ValueError('configuredにはpages又はpages_fileの対象一覧が必要')
        from page_catalog import configured_urls
        from browser_capture import in_scope
        for url in configured_urls(c):
            target=urlsplit(url)
            if target.username or target.password or not in_scope(url,c):raise ValueError('指定ページは認証情報を含めず対象範囲内にする')
    elif s['pages']:raise ValueError('pagesを指定するときはscope.modeをconfiguredにする')
    fragments=s.get('same_document_fragments',[])
    if not isinstance(fragments,list) or any(not isinstance(x,str) or not x or x.startswith('#') for x in fragments) or len(set(fragments))!=len(fragments):
        raise ValueError('同一文書と確認したfragment名は#を付けず重複のない文字列一覧にする')
    if fragments and len(s.get('same_document_fragment_reason','').strip())<10:
        raise ValueError('fragmentを同一文書へまとめる調査根拠が必要。ハッシュルーター等の状態を落とさない')
    if not isinstance(s['max_pages'],int) or not 1<=s['max_pages']<=5000:
        raise ValueError('max_pagesは1〜5000')
    for p in s['include']+s['seeds']+s['known_pages']:
        if not isinstance(p,str) or not p.startswith('/') or p.startswith('//'):
            raise ValueError('URLパスは/から指定する')
    for x in s['exclude']:
        if not x.get('path','').startswith('/') or not x.get('reason'):
            raise ValueError('除外にはpathとreasonが必要')
    c.setdefault('environments',[{'id':'desktop','viewport':{'width':1280,'height':900},'zoom':1}])
    c.setdefault('states',[]);c.setdefault('keyboard_steps',30)
    c.setdefault('input_event_limit',10000)
    if type(c['input_event_limit']) is not int or not 1<=c['input_event_limit']<=100000:
        raise ValueError('input_event_limitは1〜100000')
    if not isinstance(c['keyboard_steps'],int) or not 0<=c['keyboard_steps']<=500:
        raise ValueError('keyboard_stepsは0〜500')
    for group in [c['environments'],c['states']]:
        ids=[x['id'] for x in group]
        if len(ids)!=len(set(ids)) or any(not re.fullmatch(r'[a-z0-9-]+',i) for i in ids):
            raise ValueError('環境・状態IDは重複のない英小文字・数字・ハイフン')
    if any(s['id']=='initial' for s in c['states']):
        raise ValueError('initialは自動生成する予約ID')
    for env in c['environments']:
        if any(not isinstance(env['viewport'][k],int) or env['viewport'][k]<1 for k in ['width','height']):
            raise ValueError('viewportの幅と高さは正整数')
        from native_zoom import ZOOM_FACTORS
        if type(env.get('zoom',1)) not in {int,float} or env.get('zoom',1) not in ZOOM_FACTORS:
            raise ValueError('zoomは1、1.1、1.25、1.5、1.75、2、2.5、3、4。1以外はLinuxの専用X11環境で実ブラウザー拡大を行う')
    for state in c['states']:
        if not state.get('paths') or not isinstance(state.get('actions'),list):
            raise ValueError('各状態にはpathsとactionsが必要')
        if not state.get('assert'):
            raise ValueError('状態の到達確認assertが必要。操作が成功しただけで状態到達としない')
    if 'exploration_labels' in c:
        from state_labels import validate as validate_labels
        validate_labels(c['exploration_labels'])
    if 'keyboard_checks' in c:
        from keyboard_checks import validate as validate_keyboard_checks
        validate_keyboard_checks(c)
    if 'hover_checks' in c:
        from hover_checks import validate_check

        checks = c['hover_checks']
        if not isinstance(checks, list) or len(checks) > 20:
            raise ValueError('hover_checksには20経路まで指定できる')
        identifiers = set()
        for check in checks:
            validate_check(check)
            if check['id'] in identifiers:
                raise ValueError('ホバー経路には重複のないidが必要')
            identifiers.add(check['id'])
    if 'border_checks' in c:
        from border_contrast import validate

        validate(c['border_checks'])
    if 'text_contrast_checks' in c:
        from measure import validate_targets

        validate_targets(c['text_contrast_checks'], 'text_contrast_checks', '文字コントラストの測定')
    if 'visual_structure_scope' in c:
        from visual_structure import validate_scope

        validate_scope(c['visual_structure_scope'])
    if 'visual_structure_states' in c and (
            'visual_structure_scope' not in c or c['visual_structure_states'] not in ('initial', 'explored')):
        raise ValueError('visual_structure_statesを使う場合はvisual_structure_scopeを指定し、initial又はexploredを選ぶ')
    if c.get('auth_state'):
        c['auth_state']=str(Path(c['auth_state']).resolve())
    if 'inspection' in c and 'verification' not in c:
        from inspection import policy
        c['inspection']=policy(c['inspection'])
    from verification_modes import configure
    configure(c)
    return c


def init_config(url):
    return validate_config({'schema_version':'1','url':url,'level':'AA',
                            'scope':{'include':['/**'],'exclude':[],'seeds':['/'],'known_pages':[],'max_pages':100},
                            'environments':[{'id':'desktop','viewport':{'width':1280,'height':900},'zoom':1},
                                            {'id':'narrow','viewport':{'width':320,'height':900},'zoom':1},
                                            {'id':'zoom-200','viewport':{'width':1280,'height':900},'zoom':2},
                                            {'id':'zoom-400','viewport':{'width':1280,'height':900},'zoom':4}],
                            'states':[],'keyboard_steps':30})


@locked
def make_plan(run, manifest):
    meta,catalog=run_catalog(run)
    existing=run_plan(run) if (run/'plan.json').exists() else {'cases':[]}
    entries={x['case_id']:x for x in existing['cases']}
    for capture in manifest['captures']:
        for c in catalog['criteria']:
            if c['level'] not in LEVELS[meta['config']['level']]:
                continue
            key=capture['key']+'--'+c['id']
            entries.setdefault(key,{'case_id':key,'criterion':c['id'],'title':c['title'],
                                    'page_url':capture['url'],'page_id':capture['page_id'],
                                    'state':capture['state'],'environment':capture['environment'],
                                    'capture':capture['key'],'capture_execution':capture['execution'],
                                    'evidence_dir':capture['evidence_dir'],'methods':c['methods'],
                                    'assessment':None})
            axe_path=run/capture['evidence_dir']/'axe.json'
            if axe_path.exists():
                axe=load(axe_path);tag='wcag'+c['id'].replace('.','')
                entries[key]['automated_candidates']=[{'rule':v['id'],'help':v['help'],
                                                       'kind':kind,'nodes':v['nodes']}
                                                      for kind in ['violations','incomplete']
                                                      for v in axe.get(kind,[]) if tag in v.get('tags',[])]
    plan=dict(existing,config_digest=meta['config_digest'],catalog_digest=meta['catalog_digest'],cases=list(entries.values()))
    save(run/'plan.json',plan)
    return plan


def get_case(run, ident):
    plan=run_plan(run)
    found=[c for c in plan['cases'] if c['case_id']==ident]
    if len(found)!=1:
        raise ValueError('case_idが存在しない')
    return plan,found[0]


def evidence_item(run, path):
    root=run.resolve();p=(root/path).resolve()
    if not p.is_relative_to(root) or not p.is_file():
        raise ValueError('証拠はrun内に存在するファイルにする: '+str(path))
    return {'path':str(p.relative_to(root)),'sha256':sha256(p.read_bytes()).hexdigest()}


def prepare_record(run, judgment, plan=None):
    """Validate without changing the ledger; callers commit under the run lock."""
    meta,catalog=run_catalog(run,for_write=True)
    plan=run_plan(run) if plan is None else plan
    found=[c for c in plan['cases'] if c['case_id']==judgment['case_id']]
    if len(found)!=1:raise ValueError('case_idが存在しない')
    case=found[0]
    if 'base_assessment' in judgment and judgment['base_assessment']!=case['assessment']:
        raise ValueError('判定が更新済み。最新のcaseを読み、差分を確認してから再記録する')
    c=CRITERIA[case['criterion']]
    if judgment.get('config_digest')!=meta['config_digest'] or judgment.get('normative_sha256')!=c['normative_sha256']:
        raise ValueError('設定又は基準本文のハッシュが不一致')
    outcome=judgment.get('outcome')
    if outcome not in {'passed','failed','inapplicable','cant_tell'}:
        raise ValueError('outcomeが不正')
    if not isinstance(judgment.get('observed'),str) or len(judgment['observed'].strip())<10:
        raise ValueError('具体的に観察した事実を記録する')
    execution=judgment.get('execution')
    if execution not in {'completed','blocked','not_run'}:
        raise ValueError('executionが不正')
    if execution!='completed' and outcome!='cant_tell':
        raise ValueError('未実行・実行不能を合格等にできない')
    for field in ['conditions_reviewed','exceptions_reviewed','coverage_complete']:
        if field in judgment and type(judgment[field]) is not bool:
            raise ValueError('確認フラグはtrue又はfalseにする: '+field)
    if outcome in {'passed','inapplicable'}:
        for field in ['conditions_reviewed','exceptions_reviewed','coverage_complete']:
            if judgment.get(field) is not True:
                raise ValueError('条件・例外・対象の網羅を確認してから結果を確定する: '+field)
        if judgment.get('remaining'):
            raise ValueError('未確認が残る記録を合格・対象外にできない')
    targets=judgment.get('targets',[])
    if outcome in {'passed','failed'} and not targets:
        raise ValueError('適用対象を列挙する')
    if outcome=='inapplicable' and targets:
        raise ValueError('対象外には対象不在又は適用条件を満たさない根拠を記す')
    if outcome=='cant_tell' and not judgment.get('remaining'):
        raise ValueError('未確認は残る検査と必要な環境を記す')
    if outcome=='passed' and any(t.get('outcome')!='passed' for t in targets):
        raise ValueError('対象ごとに未確認や不適合が残る')
    if outcome=='failed' and not any(t.get('outcome')=='failed' for t in targets):
        raise ValueError('不適合となった対象と事実が必要')
    if judgment.get('coverage_complete') is True and any(t.get('outcome')=='cant_tell' for t in targets):
        raise ValueError('対象に未確認が残る記録を網羅完了にできない')
    if outcome=='failed' and judgment.get('coverage_complete') is not True and not judgment.get('remaining'):
        raise ValueError('未網羅の不適合記録には残る検査を記す')
    for t in targets:
        if not all(t.get(k) for k in ['target','observed','expected','outcome','evidence']):
            raise ValueError('各対象に識別・観察・期待結果・判定・証拠が必要')
        if t['outcome'] not in {'passed','failed','cant_tell','inapplicable'}:
            raise ValueError('対象のoutcomeが不正')
    if outcome=='passed':
        coverage=judgment.get('method_coverage',[])
        methods=[m.get('method') for m in coverage]
        if any(not isinstance(m,str) or not m.strip() for m in methods) or len(methods)!=len(set(methods)):
            raise ValueError('観察方法の名前は空や重複にしない')
        if not set(c['methods']).issubset(set(methods)):
            raise ValueError('必要な観察方法ごとに実施又は不要の根拠を記録する')
        for m in coverage:
            if m.get('status') not in {'executed','not_needed'} or len(m.get('reason','').strip())<10:
                raise ValueError('観察不能は未確認とする。不要には具体的な根拠が必要')
        if 'cross-page' in c['methods'] and len(set(judgment.get('comparison_pages',[])))<2:
            raise ValueError('ページ間比較の対象URLが不足している')
    if not judgment.get('steps_executed') or not judgment.get('tests_applied'):
        raise ValueError('実行手順と採用した検査IDが必要')
    evidence=judgment.get('evidence',[])
    if outcome in {'passed','failed','inapplicable'} and not evidence:
        raise ValueError('判定に証拠が必要')
    all_paths=evidence+[p for t in targets for p in t.get('evidence',[])]
    handoff=judgment.get('human_handoff')
    if handoff is not None:
        if outcome not in {'cant_tell','failed'} or judgment.get('coverage_complete') is not False or not judgment.get('remaining'):
            raise ValueError('人への引き継ぎは未確認として残す。合格・対象外・網羅完了にはできない')
        all_paths.extend(validate_handoff(handoff))
    if case['criterion'].startswith('1.2.'):
        from media_review import validate_review
        complete=outcome=='passed' or judgment.get('coverage_complete') is True
        for target in targets:
            review=target.get('media_review')
            if review is None and complete and target['outcome'] in {'passed','failed'}:
                raise ValueError('媒体の全対象を確定するには、各対象のmedia_reviewで比較区間を記録する')
            if review is not None:
                all_paths.extend(validate_review(review,complete=complete))
    proof=[evidence_item(run,p) for p in dict.fromkeys(all_paths)]
    # A successful record must include evidence from this capture or a case-bound attachment.
    if outcome!='cant_tell' or handoff is not None:
        own=case['evidence_dir']+'/'
        attached='evidence/attached/'+case['case_id']+'/'
        if not any(e['path'].startswith((own,attached)) for e in proof):
            raise ValueError('このページ・状態・環境の証拠を含める')
    result=dict(judgment,recorded_at=datetime.now(timezone.utc).isoformat(),verified_evidence=proof)
    return result


def commit_records(run, plan, results, work_updates=None):
    """Append immutable revisions, then atomically publish all plan pointers."""
    from work_queue import assignment, can_finish
    cases={c['case_id']:c for c in plan['cases']}
    for result in results:
        case=cases[result['case_id']]
        path='assessments/'+case['case_id']+'--'+uuid.uuid4().hex[:12]+'.json'
        save(run/path,result)
        case['assessment']=path
        if case['case_id'] in plan.get('work',{}).get('cases',{}):
            value=assignment(plan,case['case_id'])
            value['state']='done' if can_finish(dict(case,outcome=result['outcome'],assessment_data=result)) else 'blocked'
            plan['work']['cases'][case['case_id']]=value
    if work_updates:
        plan['work']['cases'].update(work_updates)
    save(run/'plan.json',plan)


@locked
def record(run, judgment):
    plan=run_plan(run)
    result=prepare_record(run,judgment,plan)
    commit_records(run,plan,[result])
    return result


@locked
def record_interactions(run, value):
    from inspection import validate_review
    if not isinstance(value,dict):raise ValueError('操作調査票はJSONオブジェクトにする')
    run_catalog(run,for_write=True);plan=run_plan(run)
    pointers=plan.setdefault('interaction_reviews',{})
    if 'base_review' not in value or value['base_review']!=pointers.get(value.get('page_id')):
        raise ValueError('最新の操作調査票の版をbase_reviewへ指定する。初回はnull')
    checked=validate_review(run,value)
    path='interaction-reviews/'+uuid.uuid4().hex+'.json'
    save(run/path,dict(value,verified_evidence=checked['verified_evidence']))
    pointers[value['page_id']]=path;save(run/'plan.json',plan)
    return checked


def validate_scope_review(run,value,for_write=True):
    meta,_=run_catalog(run,for_write=for_write)
    if value.get('config_digest')!=meta['config_digest']:raise ValueError('設定ハッシュが不一致')
    for field in ['complete','processes_reviewed','full_pages_reviewed','accessibility_support_reviewed','non_interference_reviewed']:
        if type(value.get(field)) is not bool:raise ValueError('範囲確認のフラグはtrue又はfalseにする: '+field)
    if value['complete'] and value.get('remaining'):raise ValueError('未確認が残る範囲を完了にできない')
    if not value.get('sources') or not isinstance(value.get('observed'),str) or len(value['observed'].strip())<10 or not value.get('evidence'):
        raise ValueError('範囲確認には調査した資料・具体的な観察・証拠が必要')
    return dict(value,verified_evidence=[evidence_item(run,e) for e in value['evidence']])


def outcomes(run):
    meta,catalog=run_catalog(run);plan=run_plan(run);rows=[]
    criteria={c['id']:c for c in catalog['criteria']}
    for case in plan['cases']:
        if case['criterion'] not in criteria:raise ValueError('保存した定義にない基準が検査計画に含まれる')
        a=load(run/case['assessment']) if case['assessment'] else None
        if a:
            if (a['case_id']!=case['case_id'] or a['config_digest']!=meta['config_digest'] or
                a['normative_sha256']!=criteria[case['criterion']]['normative_sha256']):
                raise ValueError('保存した判定と検査票・設定・基準本文の対応が不一致')
            if a.get('human_handoff') is not None:
                if a['outcome'] not in {'cant_tell','failed'} or a.get('coverage_complete') is not False or not a.get('remaining'):
                    raise ValueError('保存した人への引き継ぎと未確認の状態が不一致')
                paths=validate_handoff(a['human_handoff'])
                if not set(paths).issubset({e['path'] for e in a['verified_evidence']}):
                    raise ValueError('人への引き継ぎの証拠が判定時の記録にない')
            for e in a['verified_evidence']:
                if evidence_item(run,e['path'])['sha256']!=e['sha256']:
                    raise ValueError('保存後に証拠が消失・変更された: '+e['path'])
        rows.append(dict(case,outcome=a['outcome'] if a else 'not_run',assessment_data=a))
    stats=Counter(r['outcome'] for r in rows)
    manifest=load(run/'capture-manifest.json')
    scope=load(run/'scope-review.json') if (run/'scope-review.json').exists() else None
    if scope:
        checked=validate_scope_review(run,scope,for_write=False)
        if checked['verified_evidence']!=scope.get('verified_evidence'):
            raise ValueError('範囲確認の証拠・記録が変更された')
    inventory_ok=bool(scope and all(scope.get(field) is True for field in
        ['complete','processes_reviewed','full_pages_reviewed','accessibility_support_reviewed','non_interference_reviewed'])
        and not scope.get('remaining'))
    incomplete=[r for r in rows if r['assessment_data'] and
                (r['assessment_data'].get('remaining') or r['assessment_data'].get('coverage_complete') is not True or
                 any(t.get('outcome')=='cant_tell' for t in r['assessment_data'].get('targets',[])))]
    expected_captures=[]
    actual_captures={(c['url'],c['state'],c['environment']) for c in manifest['captures']}
    for page in manifest['pages']:
        states=['initial']+[s['id'] for s in meta['config'].get('states',[]) if urlsplit(page['url']).path in s['paths']]
        for env in meta['config']['environments']:
            for state in states:
                if (page['url'],state,env['id']) not in actual_captures:
                    expected_captures.append({'url':page['url'],'state':state,'environment':env['id']})
    expected_cases={capture['key']+'--'+c['id'] for capture in manifest['captures']
                    for c in catalog['criteria'] if c['level'] in LEVELS[meta['config']['level']]}
    missing_cases=sorted(expected_cases-{c['case_id'] for c in rows})
    human_cases=[r for r in rows if r['assessment_data'] and r['assessment_data'].get('human_handoff')]
    handoff_ids={r['case_id'] for r in human_cases}
    incomplete_ids={r['case_id'] for r in incomplete}
    unassigned=[r['case_id'] for r in rows if (r['outcome']=='cant_tell' or r['case_id'] in incomplete_ids) and r['case_id'] not in handoff_ids]
    collection_complete=manifest.get('collector_status','completed')=='completed'
    complete=(bool(rows) and not stats['not_run'] and not stats['cant_tell'] and not incomplete and inventory_ok and
              not manifest['unvisited'] and not manifest.get('declared_states_without_page') and
              not expected_captures and not missing_cases and collection_complete)
    per_criterion=[]
    for c in catalog['criteria']:
        cases=[r for r in rows if r['criterion']==c['id']]
        cs=Counter(r['outcome'] for r in cases)
        status=('out_of_target_level' if c['level'] not in LEVELS[meta['config']['level']] else 'unverified' if not cases else 'failed' if cs['failed'] else
                'unverified' if cs['not_run'] or cs['cant_tell'] or not collection_complete or expected_captures or any(x.endswith('--'+c['id']) for x in missing_cases) else
                'inapplicable' if cs['inapplicable']==len(cases) else 'passed_checks')
        per_criterion.append({'id':c['id'],'title':c['title'],'level':c['level'],'normative_url':c['normative_url'],
                              'procedure_version':c['procedure_version'],'status':status,'counts':dict(cs)})
    from inspection import review_status,policy
    interactions=review_status(run)
    complete=complete and interactions['complete']
    from page_explorer import status as exploration_status
    exploration=exploration_status(run)
    complete=complete and exploration['complete']
    from page_workflow import machine_checks
    automated=machine_checks(run, manifest)
    result={'level':meta['config']['level'],'url':meta['config']['url'],'audit_complete':complete,
            'conformance_claim':'この結果は記録した検査範囲についての報告です。未実施・判断保留は適合と判定していません。',
            'scope_confirmed':inventory_ok,'scope_review':scope,'unvisited':manifest['unvisited'],
            'collector_status':manifest.get('collector_status','legacy_unspecified'),
            'collection_complete':collection_complete,
            'catalog_digest':meta['catalog_digest'],'definitions_match_installed':meta['catalog_digest']==digest(CATALOG),
            'missing_captures':expected_captures,'missing_cases':missing_cases,
            'declared_states_without_page':manifest.get('declared_states_without_page',[]),
            'recorded_cases':sum(r['assessment_data'] is not None for r in rows),
            'human_review_cases':[r['case_id'] for r in human_cases],
            'unassigned_remaining_cases':unassigned,
            'inspection_policy':policy(meta['config'].get('inspection')),'interaction_review':interactions,
            'observation_usage':manifest.get('inspection',{}),
            'exploration':{k:exploration[k] for k in ['required','complete','remaining']},
            'machine_checks':automated,'counts':dict(stats),'criteria':per_criterion,'cases':rows}
    if 'visual_structure_scope' in meta['config']:
        from visual_structure import report_evidence

        result['visual_structure_evidence'] = report_evidence(run, exploration)
    from verification_modes import summary as verification_summary
    result['verification']=verification_summary(run,result)
    return result


def focus_evidence_html(run, evidence, directory):
    from workbook import (FOCUS_EVIDENCE_COLUMNS, FOCUS_EVIDENCE_FILES, FOCUS_EVIDENCE_STATUSES,
                          FOCUS_EVIDENCE_TITLE, evidence_link)

    rows = []
    for row in evidence:
        cells = []
        for key, _ in FOCUS_EVIDENCE_COLUMNS:
            value = FOCUS_EVIDENCE_STATUSES.get(row[key], row[key]) if key == 'status' else row[key]
            display = escape(value)
            if key in FOCUS_EVIDENCE_FILES:
                target = evidence_link(run, value, directory)
                if target:
                    display = f'<a href="{escape(target)}">{display}</a>'
            cells.append(f'<td>{display}</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    headers = ''.join(f'<th scope="col">{label}</th>' for _, label in FOCUS_EVIDENCE_COLUMNS)
    return (
        f'<h2 id="focus-image-evidence">{FOCUS_EVIDENCE_TITLE}</h2>'
        '<p>取得状態は画像を保存できた範囲を示します。達成基準の判定には画面の確認が必要です。</p>'
        '<div class="scroll" tabindex="0" role="region" aria-labelledby="focus-image-evidence">'
        f'<table><thead><tr>{headers}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    )


def visual_structure_html(run, rows, directory):
    from visual_structure import REPORT_COLUMNS, REPORT_TITLE, display_rows
    from workbook import evidence_link

    items = []
    for row in display_rows(rows):
        relative_path = evidence_link(run, row['evidence'], directory)
        cells = [f'<td>{escape(row.get(key, ""))}</td>' for key, _ in REPORT_COLUMNS if key != 'evidence']
        proof = f'<a href="{escape(relative_path, quote=True)}">元の証拠</a>' if relative_path else '未取得'
        items.append('<tr>' + ''.join(cells) + f'<td>{proof}</td></tr>')
    headers = ''.join(f'<th scope="col">{label}</th>' for _, label in REPORT_COLUMNS)
    return (f'<h2 id="visual-structure-evidence">{REPORT_TITLE}（1.3.1）</h2>'
            '<p>候補の意味と、必要な構造が支援技術に伝わるかを確認してください。達成基準の判定は検査票に記録します。</p>'
            f'<div class="scroll" tabindex="0" role="region" aria-label="{REPORT_TITLE}">'
            f'<table><caption>{REPORT_TITLE}</caption><thead><tr>{headers}</tr></thead>'
            f'<tbody>{"".join(items)}</tbody></table></div>')


def single_report_page(run):
    if not run_layout.organized(run):
        return None
    from page_catalog import configured_urls

    config = run_meta(run)['config']
    pages = configured_urls(config) if config['scope']['mode'] == 'configured' else []
    return pages[0] if len(pages) == 1 else None


def report_paths(run, page_url=None):
    from browser_capture import normalize, page_id

    single = single_report_page(run)
    if page_url and single and normalize(page_url) == normalize(single):
        return run_layout.report_files(run, single=True)
    return run_layout.report_files(run, page_id(page_url) if page_url else None)


@locked
def report(run, *, page_url=None):
    return render_reports(run, page_url=page_url)


def render_reports(run, *, page_url=None):
    from page_workflow import page_result
    import checksheet

    single_page = single_report_page(run)
    result = outcomes(run)
    if not page_url and single_page and result['cases']:
        page_url = single_page
    if page_url:
        result = page_result(run, page_url, result)
    files = report_paths(run, page_url)
    files.html.parent.mkdir(parents=True, exist_ok=True)
    files.issues.parent.mkdir(parents=True, exist_ok=True)
    result['evidence_base'] = run_layout.href(files.json, run)
    save(files.json, result)

    def proof_href(path):
        target = run_layout.href(files.html, run / path)
        return target if target.startswith('../') else './' + target

    def link(path, label):
        return f'<a href="{escape(run_layout.href(files.html, path), quote=True)}">{escape(label)}</a>'

    _, catalog = run_catalog(run)
    manifest = load(run / 'capture-manifest.json')
    human_model = checksheet.build(result, catalog, manifest=manifest)
    scope = 'ページ' if page_url else '検査範囲'
    selected_keys = {case['capture'] for case in result['cases']}
    selected = [c for c in manifest['captures'] if not page_url or c['key'] in selected_keys]
    environment_names = {e['id']: f"{e['viewport']['width']}×{e['viewport']['height']} CSS px"
                         for e in run_meta(run)['config']['environments']}
    environments = '、'.join(dict.fromkeys(environment_names.get(c['environment'], c['environment']) for c in selected))
    mode = result.get('verification', {}).get('label') if result.get('verification') else None
    complete = '検証完了' if result['audit_complete'] else '検証未完了'
    labels={'passed':'検査通過','failed':'不適合','inapplicable':'対象外','cant_tell':'判断保留','not_run':'未実施'}
    rows=[]
    for c in result['cases']:
        a=c['assessment_data'];ev=[]
        if a:
            ev=[link(run / item['path'], f'証拠 {i}') for i, item in enumerate(a['verified_evidence'], 1)]
        observed=a['observed'] if a else 'まだ実ページの検査結果が記録されていません。'
        remaining=' / '.join(a.get('remaining',[])) if a else '基準の本文と検査手順を読み、対象を列挙して実行する。'
        media_details=[]
        if a and a.get('human_handoff'):
            media_details.append(handoff_details(a['human_handoff']))
        for target in a.get('targets',[]) if a else []:
            review=target.get('media_review')
            if not isinstance(review,dict) or not isinstance(review.get('intervals'),list):continue
            entries=[]
            for interval in review['intervals'][:20]:
                state='比較済み' if interval.get('status')=='reviewed' else '未確認'
                text=interval.get('observed',interval.get('reason',''))
                expected=f'<br>期待結果：{escape(str(interval["expected"]))}' if interval.get('expected') else ''
                entries.append(f'<li>{escape(str(interval.get("start")))}–{escape(str(interval.get("end")))}秒：{state}。'
                    f'{escape(str(text))}{expected}</li>')
            limit_notice='先頭20件まで表示。' if len(review['intervals'])>20 else ''
            media_details.append(f'<details><summary>{escape(str(target["target"]))}：媒体の比較区間 {len(review["intervals"])}件</summary>'
                f'<p>{escape(str(review.get("comparison","")))}</p><p>期待結果：{escape(str(target.get("expected","")))}</p><ul>{"".join(entries)}</ul>'
                f'<p>{limit_notice}{link(run / c["assessment"], "全区間の比較記録")}</p></details>')
        rows.append(f'<tr><th scope="row">{escape(c["criterion"])} {escape(c["title"])}</th>'
                    f'<td>{escape(c["page_url"])}<br>{escape(c["state"])} / {escape(c["environment"])}</td>'
                    f'<td>{labels[c["outcome"]]}</td><td>{escape(observed)}<br>{escape(remaining)}{"".join(media_details)}</td><td>{"<br>".join(ev)}</td></tr>')
    summary='、'.join(f'{labels[k]} {v}' for k,v in result['counts'].items())
    inventory='確認済み' if result['scope_confirmed'] else '未確認。未リンクページ、権限別画面、状態と手続きの範囲確認が必要です。'
    if not result['scope_confirmed'] and result.get('scope_review'):
        value=result['scope_review']
        names={'complete':'範囲・適合要件の総合確認','processes_reviewed':'一連の手続き','full_pages_reviewed':'ページ全体',
               'accessibility_support_reviewed':'アクセシビリティサポート','non_interference_reviewed':'非干渉'}
        inventory='未確認：'+'、'.join(label for key,label in names.items() if value.get(key) is not True)+'。'
        if value.get('remaining'):inventory+='残る確認：'+' / '.join(value['remaining'])
    definition_notice=('現在の検査手順と同じ定義を使用しています。' if result['definitions_match_installed'] else
                       '検査手順の更新前の記録です。当時の定義で再集計しました。新しい手順での検査結果ではありません。')
    definition_link = link(run / 'catalog.snapshot.json', '保存した検査定義') if (run / 'catalog.snapshot.json').exists() else '定義のコピーなし'
    collection_notice={'completed':'予定した収集の試行を終了', 'running':'収集中、又は収集の途中で停止',
        'interrupted':'収集の途中で停止', 'legacy_unspecified':'当時の収集記録を使用'}[result['collector_status']]
    from inspection import report_rows
    observations=report_rows(result)
    observation_rows=''.join('<tr>'+''.join('<td>'+escape(str(value))+'</td>' for value in
        [o['url'],o['capture'],o['label'],o['visual'],o['status'],o['observed'],o['remaining'],o['screen_reader']])+'</tr>' for o in observations)
    from inspection import SCREENSHOT_LABELS
    images = [item for item in result['observation_usage'].get('screenshots', []) if item['status'] == 'captured']
    image_setting = SCREENSHOT_LABELS[result['inspection_policy']['screenshots']]
    image_details = ''
    if images:
        image_labels = {'initial': '初期表示', 'state': '表示状態', 'action-before': '操作前',
                        'action-after': '操作後', 'focus': 'フォーカス', 'detail': '操作の証拠'}
        image_links = []
        for item in images:
            environment = item.get('environment')
            when = image_labels.get(item.get('kind'), '画面の証拠')
            if item.get('label'):
                when += ' · ' + item['label']
            if environment:
                when += ' · ' + environment_names.get(environment, environment)
            path = run / item['path']
            image_links.append('<li>' + link(path, f'{when}（{path.name}）') + '</li>')
        image_details = (f'<details id="evidence-images"><summary>画面の証拠画像（{len(images)}枚）</summary>'
                         '<ul>' + ''.join(image_links) + '</ul></details>')
    reader_labels = {'reviewed': '実施', 'partial': '一部実施', 'skipped': '未実施'}
    readers = '、'.join(sorted({reader_labels[p['screen_reader']['status']]
                               for p in result['interaction_review'].get('pages', {}).values()})) or '記録なし'
    machine_rows=[]
    from page_workflow import grouped_machine_issues
    for check in grouped_machine_issues(result['machine_checks']):
        machine_rows.append('<tr>'+''.join('<td>'+escape(str(check[k])).replace('\n','<br>')+'</td>' for k in
            ['criterion','expected','states','target','observed','outcome'])+
            '<td>'+'<br>'.join(link(run / path, f'証拠 {i}') for i, path in enumerate(check['proof'], 1))+'</td></tr>')
    machine_findings = (
        '<details id="machine-results" open><summary>自動検出した問題・要確認 '
        f'{len(machine_rows)} 件</summary>'
        '<div class="scroll" tabindex="0" role="region" aria-label="自動検出した問題">'
        '<table><caption>機械検査で追加確認が必要になった箇所</caption><thead><tr>'
        + ''.join(f'<th scope="col">{label}</th>' for label in ['基準','検査','状態・経路','対象','観察','機械結果','証拠'])
        + '</tr></thead><tbody>' + ''.join(machine_rows) + '</tbody></table></div></details>'
        if machine_rows else '<p id="machine-results">記録された機械検査の指摘・要確認は0件です。</p>'
        if result['machine_checks'] else '<p id="machine-results">機械検査の結果は収集されていません。</p>'
    )
    measurements_html = ''
    for kind, criterion, label, caption in (
        ('text_contrast', '1.4.3', '文字のコントラスト', '指定した初期表示の文字色と背景色の測定'),
        ('focus_outline', '1.4.11', 'フォーカス枠のコントラスト', '指定した状態でのフォーカス枠と隣接色の測定'),
        ('dialog_focus', '2.4.3', 'ダイアログを閉じた後のフォーカス', '実Escapeと次のTabで観測したフォーカス'),
    ):
        measurements = [row for row in result['machine_checks'] if kind in row]
        if not measurements:
            continue
        labels = {'passed': '通過（機械）', 'failed': '問題あり（機械）', 'cant_tell': '機械判定不能'}
        rows = []
        for row in measurements:
            cells = [row['state_label'] + ' / ' + row['environment'], row['target'], row['observed'], labels[row['outcome']]]
            links = link(run / row["evidence"], "操作・測定ログ")
            image = row[kind].get('source')
            if image:
                links += " / " + link(run / image, "測定画像")
            rows.append('<tr>'+''.join(f'<td>{escape(value)}</td>' for value in cells)+f'<td>{links}</td></tr>')
        measurements_html += (f'<details><summary>{criterion} {label}</summary>'
            f'<div class="scroll" tabindex="0" role="region" aria-label="{label}">'
            f'<table><caption>{caption}</caption><thead><tr>'
            '<th scope="col">状態・経路</th><th scope="col">対象</th><th scope="col">観察</th>'
            '<th scope="col">機械結果</th><th scope="col">証拠</th></tr></thead><tbody>'
            + ''.join(rows) + '</tbody></table></div></details>')
    focus_evidence = result.get('focus_evidence', [])
    evidence_nav = '<li><a href="#evidence-images">画面の証拠画像</a></li>' if images else ''
    if focus_evidence:
        evidence_nav += '<li><a href="#focus-image-evidence">フォーカスの画像証拠</a></li>'
        measurements_html += focus_evidence_html(run, focus_evidence, files.html.parent)
    if result.get('visual_structure_evidence'):
        evidence_nav += '<li><a href="#visual-structure-evidence">視覚構造の証拠</a></li>'
        measurements_html += visual_structure_html(run, result['visual_structure_evidence'], files.html.parent)

    from verification_modes import render_html as verification_html
    mode_details = verification_html(result.get('verification'))
    if mode_details:
        mode_details = '<details><summary>検査モードの仕様</summary>' + mode_details + '</details>'
    exploration = result['exploration']['remaining']
    exploration_details = (
        '<details id="exploration-details"><summary>自動探索で残った操作・状態</summary><ul>'
        + ''.join(f'<li>{escape(item)}</li>' for item in exploration) + '</ul></details>'
        if exploration else ''
    )
    scope_heading = 'ページ検証の概要' if page_url else '検査範囲の概要'
    css = """
      html { color-scheme: light; }
      body { font: 1rem/1.65 system-ui, sans-serif; color: #202830; background: #fff; margin: 0; }
      main { box-sizing: border-box; width: min(100%, 74rem); margin: auto; padding: clamp(1rem, 4vw, 3rem); }
      h1, h2, h3 { line-height: 1.3; }
      h1 { margin: 0 0 .45rem; }
      h2 { margin: 0 0 .9rem; }
      header p, article p { margin: .4rem 0; }
      a { color: #00529b; text-underline-offset: .15em; }
      :focus-visible { outline: 3px solid #00529b; outline-offset: 3px; }
      section { margin: 2.4rem 0; }
      section + section { border-top: 1px solid #bac7d2; padding-top: 1.5rem; }
      nav ul { display: flex; flex-wrap: wrap; gap: .35rem 1.2rem; padding: 0; list-style: none; }
      .scope, .result, .finding { border-radius: .5rem; padding: .85rem 1rem; margin: .75rem 0; }
      .scope { background: #edf3f7; }
      .result, .finding { border: 1px solid #bac7d2; }
      .finding { border-inline-start: .3rem solid #a33125; }
      .result h3, .finding h3 { margin: 0 0 .55rem; }
      .result-status { font-weight: 650; }
      dt { font-weight: 650; }
      dd { margin: 0 0 .65rem; }
      details { padding: .65rem 0; border-bottom: 1px solid #bac7d2; }
      summary { width: fit-content; cursor: pointer; font-weight: 650; }
      table { border-collapse: collapse; min-width: 52rem; }
      td, th { border: 1px solid #bac7d2; padding: .55rem; vertical-align: top; text-align: left; }
      .scroll { overflow: auto; max-width: 100%; }
      caption { text-align: left; }
      th, td, p, li, dd, h3 { overflow-wrap: anywhere; }
      .criterion { font-weight: 650; background: #edf3f7; }
      @media print {
        .scroll { overflow: visible; }
        table { min-width: 0; width: 100% !important; }
        .checksheet-table col { width: auto !important; }
        tr, article { break-inside: avoid; }
      }
    """
    page = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>WCAG 2.2 {escape(result['level'])} {scope}の検証結果</title><style>{css}</style></head><body>
<main><header><h1>WCAG 2.2 {escape(result['level'])} {scope}の検証結果</h1>
<p>{escape(result['url'])}</p></header>
<div class="scope" role="region" aria-label="{scope_heading}">
<p><strong>{complete}</strong>{f' · {escape(mode)}' if mode else ''}</p>
<p>{len(selected)} 件の表示状態・環境を収集。{escape(environments)}</p>
</div>
<nav aria-label="レポート内の移動"><ul>
<li><a href="#failures">修正箇所</a></li><li><a href="#performed">実施結果</a></li>
<li><a href="#remaining">残る確認</a></li><li><a href="#details">詳細と元データ</a></li>
{evidence_nav}</ul></nav>
<section>{checksheet.render_failures(human_model, proof_href)}{machine_findings}</section>
<section>{checksheet.render_summary(human_model, proof_href)}{image_details}{measurements_html}</section>
<section>{checksheet.render_remaining(human_model, exploration)}{exploration_details}
<p>標準の証拠画像 {escape(image_setting)} · 保存 {len(images)} 枚。実スクリーンリーダーの記録 {escape(readers)}。</p>
<p>ページ・状態・適合要件の範囲 {escape(inventory)}</p>
<p>{link(files.handoff, '人に引き継ぐ確認')} · {link(files.interactions, '操作調査の記録')}</p></section>
<section><h2 id="details">詳細と元データ</h2>
{checksheet.render_checklist(human_model, proof_href)}
<details><summary>実施環境・集計条件</summary><p>{escape(collection_notice)}。</p>
<p>未訪問URL {len(result['unvisited'])} 件、未収集のページ・状態・環境 {len(result['missing_captures'])} 件。</p>
<p>{escape(definition_notice)} {definition_link}</p></details>
<details><summary>画面・操作の調査記録</summary>
<div class="scroll" tabindex="0" role="region" aria-label="操作調査の表"><table>
<thead><tr><th scope="col">ページ</th><th scope="col">状態・環境</th><th scope="col">操作対象</th><th scope="col">画像確認</th>
<th scope="col">操作確認</th><th scope="col">観察</th><th scope="col">残る確認</th><th scope="col">実SR</th></tr></thead>
<tbody>{observation_rows}</tbody></table></div></details>
<details><summary>ページ・状態・環境・基準ごとの検査票</summary>
<div class="scroll" tabindex="0" role="region" aria-label="検査結果の表"><table><caption>観察結果と証拠</caption>
<thead><tr><th scope="col">基準</th><th scope="col">対象</th><th scope="col">結果</th>
<th scope="col">観察・残る確認</th><th scope="col">証拠</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></details>
{mode_details}
<p>{link(files.issues, '不適合の詳細')} · {link(files.json, '処理用JSON')} · {link(run / 'capture-manifest.json', '収集ログの索引')}</p>
</section></main></body></html>
"""
    files.html.write_text(page)
    issues=['# 修正担当向けの不適合記録','', 'この記録は検証結果です。製品コードの変更は行っていません。','',
            '予定範囲の検査完了: '+('はい' if result['audit_complete'] else 'いいえ'),
            '結果: '+summary,
            '全基準と範囲の未確認は[HTMLレポート](report.html)又は[JSON](report.json)を参照してください。','']
    for c in result['cases']:
        a=c['assessment_data']
        if not a or a['outcome']!='failed':continue
        issues += [f"## {c['criterion']} {c['title']}", '', f"対象: {c['page_url']} / {c['state']} / {c['environment']}",
                   '', '再現手順:', '', *[f'- {s}' for s in a['steps_executed']], '']
        for t in a['targets']:
            if t['outcome']!='failed':continue
            issues += [f"対象要素: {t['target']}", f"期待結果: {t['expected']}",f"観察結果: {t['observed']}",
                       '証拠: '+', '.join(t['evidence']), '']
        source=next(x['normative_url'] for x in result['criteria'] if x['id']==c['criterion'])
        issues += ['原典: '+source,'このcaseの未確認: '+(', '.join(a.get('remaining',[])) or 'なし'), '']
    issue_text='\n'.join(issues).rstrip()+'\n'
    for path in (files.html, files.json):
        issue_text = issue_text.replace(f']({path.name})', f']({run_layout.href(files.issues, path)})')
    if not run_layout.organized(run) and page_url:
        for name, path in [('report.html', files.html), ('report.json', files.json)]:
            issue_text = issue_text.replace(f']({name})', f']({path.name})')
    files.issues.write_text(issue_text)
    files.handoff.write_text(handoff_markdown([c for c in result['cases']
        if c['assessment_data'] and c['assessment_data'].get('human_handoff')],
        proof_href=lambda path: run_layout.href(files.handoff, run / path),
        report_href=run_layout.href(files.handoff, files.json)))
    notes=['# 画面・操作の調査と残る確認','',
           '調査状態: '+result['interaction_review']['status'],
           '画像の選択: '+result['inspection_policy']['screenshots'],
           '実SRの選択: '+result['inspection_policy']['screen_reader'],'']
    for o in observations:
        notes += [o['url']+' / '+o['capture'],o['label']+' / '+o['location'],
                  '画像: '+o['visual']+' / 操作: '+o['status']+' / 実SR: '+o['screen_reader'],
                  o['observed'],'実施した操作: '+o['steps'],'残る確認: '+o['remaining'],
                  '元の調査票: '+o['source_review'],'']
    files.interactions.write_text('\n'.join(line.rstrip() for line in notes).rstrip()+'\n')
    print(json.dumps({k:result[k] for k in ['audit_complete','scope_confirmed','counts']},ensure_ascii=False))
    return result


@locked
def write_page_reports(run, url):
    import workbook

    files = report_paths(run, url)
    path = files.excel
    if run_layout.organized(run):
        workbook.export(run, path, page_exact=url, page_view=True, replace=True, acquire_lock=False)
    else:
        if path.exists():
            path = path.with_name(path.stem + '-' + uuid.uuid4().hex[:8] + path.suffix)
        workbook.export(run, path, page_exact=url, page_view=True, acquire_lock=False)
    render_reports(run, page_url=url)
    return {'html': str(files.html), 'json': str(files.json), 'excel': str(path)}


def refresh_report(run):
    page_url = single_report_page(run)
    if page_url and run_plan(run)['cases']:
        files = write_page_reports(run, page_url)
        return load(files['json'])
    return report(run)


def run_page_audit(run,args):
    from page_explorer import explore
    from shlex import join
    from verification_modes import run_catalog as verification_catalog
    verification_catalog(run)
    if run_meta(run)['config'].get('states'):
        raise ValueError('事前設定statesの収集にはpageを使う。page-auditは自動探索、追加シナリオはprobeで検査する')
    value=asyncio.run(explore(run,max_states=args.max_states,max_steps=args.max_steps,max_depth=args.max_depth))
    if not run_plan(run)['cases']:
        print(json.dumps({'exploration':value['remaining'],'error':'収集に成功した状態がありません'},ensure_ascii=False));return 2
    files=write_page_reports(run,args.url)
    print(json.dumps(dict(files,explored_states=len(value['nodes']),pending_routes=len(value['queue']),
                         next_command=join(['python3','scripts/audit.py','page-next','--run',args.out,'--page-exact',args.url])),ensure_ascii=False))
    return 0


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('init');p.add_argument('--url',required=True);p.add_argument('--config',required=True)
    p.add_argument('--profile',choices=['quick','standard','thorough'])
    from verification_modes import MODES
    p.add_argument('--mode',choices=list(MODES),default='machine')
    p=sub.add_parser('modes');p.add_argument('--mode',choices=list(MODES),default='machine');p.add_argument('--criterion',choices=list(CRITERIA))
    sub.add_parser('doctor')
    p=sub.add_parser('rules');p.add_argument('--criterion',choices=list(CRITERIA))
    p.add_argument('--status',choices=['active','approved','proposed','deprecated','all'],default='active')
    p=sub.add_parser('rule');p.add_argument('--id',required=True)
    p=sub.add_parser('start');p.add_argument('--config',required=True);p.add_argument('--out',required=True)
    p=sub.add_parser('pages');p.add_argument('--config',required=True);p.add_argument('--out',required=True)
    p=sub.add_parser('page-batch');p.add_argument('--config',required=True);p.add_argument('--out',required=True)
    p.add_argument('--resume',action='store_true')
    p.add_argument('--max-pages-this-run',type=int)
    p = sub.add_parser('shared-contrast', help='ページ別の機械検査にある同じコントラスト観察をまとめる')
    p.add_argument('--batch', required=True, type=Path)
    p.add_argument('--target', required=True)
    p.add_argument('--environment', required=True)
    p.add_argument('--page-exact', help='HTML参照に表示するバッチ内のURL')
    p.add_argument('--out', type=Path, help='ページ別の参照HTMLを新規出力する')
    from inspection import SCREENSHOT_LIMITS
    for name in ['page','page-audit']:
        p=sub.add_parser(name);p.add_argument('--url',required=True);p.add_argument('--out',required=True);p.add_argument('--config')
        p.add_argument('--level',choices=list(LEVELS));p.add_argument('--profile',choices=['quick','standard','thorough'])
        p.add_argument('--screenshots', choices=SCREENSHOT_LIMITS);p.add_argument('--screen-reader',choices=['off','optional','required'])
        p.add_argument('--max-images',type=int)
        p.add_argument('--mode',choices=list(MODES))
        if name=='page-audit':
            p.add_argument('--resume',action='store_true')
            p.add_argument('--max-states',type=int,default=64);p.add_argument('--max-steps',type=int,default=512);p.add_argument('--max-depth',type=int,default=8)
    p=sub.add_parser('tasks');actions=p.add_subparsers(dest='task_action',required=True)
    for action in ['create','list','claim']:
        q=actions.add_parser(action);q.add_argument('--run',required=True)
        q.add_argument('--owner',required=action=='claim')
        if action=='create':
            q.add_argument('--group-by',choices=['page','criterion','none'],default='page')
            q.add_argument('--size',type=int,default=20);q.add_argument('--page');q.add_argument('--criterion')
        if action=='claim':q.add_argument('--id',required=True);q.add_argument('--reassign',action='store_true')
        if action=='list':q.add_argument('--limit',type=int,default=20)
    p=sub.add_parser('excel');actions=p.add_subparsers(dest='excel_action',required=True)
    for action in ['export','import']:
        q=actions.add_parser(action);q.add_argument('--run',required=True)
        if action=='export':
            q.add_argument('--out',required=True);q.add_argument('--mode',choices=['report','work'],default='report')
            q.add_argument('--task');q.add_argument('--owner');q.add_argument('--page');q.add_argument('--page-exact');q.add_argument('--criterion')
            q.add_argument('--pending-only',action='store_true')
        else:q.add_argument('--file',required=True);q.add_argument('--check',action='store_true')
    for name in ['pending','case','record','report','attach','scope-review','recover','probe','snapshot','review-interactions','page-next','page-report','resolve-exploration']:
        p=sub.add_parser(name);p.add_argument('--run',required=True)
        if name in {'page-next','page-report'}:p.add_argument('--page-exact',required=True)
        if name=='resolve-exploration':p.add_argument('--file',required=True)
        if name=='case':p.add_argument('--id',required=True)
        if name=='pending':
            p.add_argument('--criterion');p.add_argument('--page');p.add_argument('--limit',type=int,default=20)
            p.add_argument('--page-exact')
            p.add_argument('--task');p.add_argument('--owner')
            p.add_argument('--status',choices=['not_run','cant_tell','human','all'],default='all')
        if name in {'record','scope-review','review-interactions'}:p.add_argument('--file',required=True)
        if name=='attach':p.add_argument('--case',required=True);p.add_argument('--file',required=True)
        if name=='probe':p.add_argument('--case',required=True);p.add_argument('--actions',required=True)
        if name=='report':p.add_argument('--strict',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.command=='modes':
            from verification_modes import catalog,validate_catalog,coverage,LEGEND
            value=validate_catalog(catalog())
            rows=coverage(value,args.mode or 'machine')
            if args.criterion:rows=[r for r in rows if r['criterion']==args.criterion]
            print(json.dumps({'modes':MODES,'legend':LEGEND,'selected_mode':args.mode,'checkpoints':rows},ensure_ascii=False,indent=2));return 0
        if args.command=='doctor':
            from native_zoom import capabilities
            print(json.dumps({'python':sys.version.split()[0], 'playwright':bool(importlib.util.find_spec('playwright')),
                              'chromium':shutil.which('chromium'),'axe':(ROOT/'vendor/axe.min.js').exists(),
                              'screen_reader':shutil.which('orca'), 'real_browser_zoom':capabilities(),
                              'note':'ブラウザー収集の可用性であり、WCAG全検査の実行可能性を保証しない'},ensure_ascii=False,indent=2));return 0
        if args.command in {'rules','rule'}:
            data=load(ROOT/'references/act-rules.json');rules=data['rules']
            if args.command=='rule':
                found=[r for r in rules if r['id']==args.id]
                if not found:raise ValueError('ACTルールIDが存在しない')
                print(json.dumps(found[0],ensure_ascii=False,indent=2));return 0
            if args.criterion:rules=[r for r in rules if any(c['criterion']==args.criterion for c in r['criteria'])]
            rules=[r for r in rules if args.status=='all' or (r['status']!='deprecated' if args.status=='active' else r['status']==args.status)]
            print(json.dumps({'source_commit':data['source_commit'],'count':len(rules),
                'rules':[{k:r[k] for k in ['id','title','status','type','criteria','source']} for r in rules]},ensure_ascii=False,indent=2));return 0
        if args.command=='init':
            p=Path(args.config)
            if p.exists():raise ValueError('既存設定を上書きしない')
            from verification_modes import select
            config=select(init_config(args.url),args.mode,profile=args.profile)
            config['environments']=[e for e in config['environments'] if e.get('zoom',1)==1]
            save(p,config);print(p);return 0
        if args.command == 'page-batch':
            from page_batch import run as run_batch
            code, summary = run_batch(args.config, args.out, resume=args.resume,
                                      limit=args.max_pages_this_run, audit_page=main)
            print(json.dumps(summary, ensure_ascii=False))
            return code
        if args.command == 'shared-contrast':
            from shared_contrast import compare

            if (args.page_exact is None) != (args.out is None):
                raise ValueError('--page-exactと--outを一緒に指定する')
            result = compare(args.batch, target=args.target, environment=args.environment)
            if args.out is not None:
                from shared_contrast_report import export_page_html
                path = export_page_html(args.batch, result, url=args.page_exact, out=args.out)
                result = {'html': str(path)}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command in {'start','pages','page','page-audit'}:
            from page_catalog import read_config,select_pages
            if args.command in {'page','page-audit'}:
                from inspection import policy
                if args.config:config=read_config(args.config)
                elif args.command=='page-audit' and args.resume:config=json.loads(json.dumps(run_meta(run_layout.ledger(args.out))['config']))
                else:config=init_config(args.url)
                if (urlsplit(config['url']).scheme,urlsplit(config['url']).netloc)!=(urlsplit(args.url).scheme,urlsplit(args.url).netloc):
                    raise ValueError('設定と単独ページのオリジンが異なる')
                if not args.config:
                    config['environments']=[e for e in config['environments'] if e.get('zoom',1)==1]
                config['scope'].update(mode='configured',pages=[args.url],max_pages=1)
                selected_mode=args.mode or ('machine' if args.command=='page-audit' and not args.config and not args.resume else None)
                if not selected_mode and args.profile and config.get('verification'):
                    selected_mode=config['verification']['mode']
                if selected_mode:
                    from verification_modes import select
                    select(config,selected_mode,profile=args.profile,screenshots=args.screenshots,
                           screen_reader=args.screen_reader,max_images=args.max_images)
                else:
                    choice={'profile':args.profile} if args.profile else dict(config.get('inspection',{'profile':'standard'}))
                    if args.screenshots is not None and args.screenshots != choice.get('screenshots'):
                        choice.pop('max_images', None)
                    for key in ['screenshots','screen_reader','max_images']:
                        value=getattr(args,key)
                        if value is not None:choice[key]=value
                    config['inspection']=policy(choice)
                if args.level:config['level']=args.level
                config=validate_config(config)
            else:config=read_config(args.config)
            for key in ('keyboard_checks', 'hover_checks', 'border_checks', 'text_contrast_checks'):
                if config.get(key) and args.command != 'page-audit':
                    raise ValueError(f'{key}はpage-auditで実行する')
            if 'visual_structure_scope' in config and args.command not in {'page-audit', 'pages'}:
                raise ValueError('visual_structure_scopeの候補収集はpage-auditで実行する')
            if args.command=='pages':
                out=Path(args.out)
                if out.exists():raise ValueError('既存のURL一覧を上書きしない')
                value=asyncio.run(select_pages(config));save(out,value)
                print(json.dumps({'file':str(out),'mode':value['mode'],'pages':len(value['pages']),'unvisited':len(value['unvisited']),'errors':len(value['errors']),'wcag_inspection_executed':False},ensure_ascii=False));return 0
            if args.command=='page-audit' and args.resume:
                run = run_layout.ledger(args.out)
                meta=run_meta(run)
                if meta['config']['scope']['pages']!=[args.url]:raise ValueError('再開先のページURLが異なる')
                if args.config and digest(config)!=meta['config_digest']:raise ValueError('再開では設定を変更しない。変更した検査は新しいrunへ保存する')
                if args.level is not None and args.level != meta['config']['level']:
                    raise ValueError('再開では適合レベルを変更しない。新しいrunを作る')
                for option in ['screenshots','screen_reader','max_images','profile']:
                    requested=getattr(args,option)
                    if requested is not None and requested!=meta['config']['inspection'][option]:
                        raise ValueError('再開では観察設定を変更しない。新しいrunを作る')
                if args.mode is not None and args.mode!=meta['config'].get('verification',{}).get('mode'):
                    raise ValueError('再開では検証モードを変更しない。新しいrunを作る')
                return run_page_audit(run,args)
            run = run_layout.create(args.out)
            meta={'created_at':datetime.now(timezone.utc).isoformat(),'config':config,
                  'config_digest':digest(config),'catalog_digest':digest(CATALOG)}
            from verification_modes import snapshot as snapshot_verification
            snapshot_verification(run,meta)
            save(run/'run.json',meta)
            snapshot_catalog(run)
            if args.command=='page-audit':
                make_plan(run,{'captures':[]});return run_page_audit(run,args)
            from browser_capture import collect
            manifest = asyncio.run(collect(config, run))
            plan = make_plan(run, manifest)
            if args.command == 'page' and plan['cases']:
                print(json.dumps(write_page_reports(run, args.url), ensure_ascii=False))
            else:
                report(run)
            return 0
        run = run_layout.ledger(args.run)
        if args.command in {'page-next','page-report','resolve-exploration'}:
            from page_workflow import next_work,resolve
            if args.command=='resolve-exploration':value=resolve(run,load(args.file))
            elif args.command=='page-next':value=next_work(run,args.page_exact)
            else:
                value=write_page_reports(run,args.page_exact)
            print(json.dumps(value,ensure_ascii=False,indent=2));return 0
        if args.command=='review-interactions':
            print(json.dumps(record_interactions(run,load(args.file)),ensure_ascii=False,indent=2));return 0
        if args.command=='tasks':
            import work_queue
            if args.task_action=='create':
                value=work_queue.create_tasks(run,group_by=args.group_by,size=args.size,owner=args.owner or '',page=args.page,criterion=args.criterion)
                value={'created':len(value),'tasks':value}
            elif args.task_action=='claim':value=work_queue.claim(run,args.id,args.owner,args.reassign)
            else:
                value=work_queue.status(run,args.owner);value['tasks']=value['tasks'][:max(1,args.limit)]
            print(json.dumps(value,ensure_ascii=False,indent=2));return 0
        if args.command=='excel':
            import workbook
            if args.excel_action=='export':
                value=workbook.export(run,Path(args.out),mode=args.mode,task=args.task,owner=args.owner,
                                      page=args.page,page_exact=args.page_exact,criterion=args.criterion,pending=args.pending_only)
            else:value=workbook.import_book(run,Path(args.file),check=args.check)
            print(json.dumps(value,ensure_ascii=False,indent=2));return 0
        if args.command=='snapshot':
            print(json.dumps(snapshot_catalog(run),ensure_ascii=False));return 0
        if args.command=='recover':
            manifest=load(run/'capture-manifest.json');make_plan(run,manifest)
            refresh_report(run)
            return 0
        if args.command=='pending':
            import work_queue
            result=outcomes(run)
            pending=[c for c in result['cases'] if c['outcome'] in {'not_run','cant_tell'} or
                     (c['assessment_data'] and (c['assessment_data'].get('remaining') or c['assessment_data'].get('coverage_complete') is not True or
                      any(t.get('outcome')=='cant_tell' for t in c['assessment_data'].get('targets',[]))))]
            pending.sort(key=lambda c:c['outcome']!='not_run')
            if args.criterion:pending=[c for c in pending if c['criterion']==args.criterion]
            if args.page:pending=[c for c in pending if args.page in c['page_url']]
            if args.status=='human':pending=[c for c in pending if c['assessment_data'] and c['assessment_data'].get('human_handoff')]
            elif args.status!='all':pending=[c for c in pending if c['outcome']==args.status]
            plan=run_plan(run);pending=work_queue.select(pending,plan,task=args.task,owner=args.owner,page_exact=args.page_exact)
            print(json.dumps({'total':len(pending),'cases':[{'case_id':c['case_id'],'criterion':c['criterion'],'url':c['page_url'],'state':c['state'],
                               'environment':c['environment'],'methods':c['methods'],'status':c['outcome'],
                               'task':(work_queue.task_for(plan,c['case_id']) or {}).get('id'),
                               'work':work_queue.assignment(plan,c['case_id']),
                               'human_review_required':bool(c['assessment_data'] and c['assessment_data'].get('human_handoff'))}
                              for c in pending[:max(1,args.limit)]]},ensure_ascii=False,indent=2));return 0
        if args.command=='case':
            meta,catalog=run_catalog(run);_,case=get_case(run,args.id)
            c=next(c for c in catalog['criteria'] if c['id']==case['criterion'])
            current_criterion=CRITERIA.get(c['id'])
            same_criterion=current_criterion is not None and digest(c)==digest(current_criterion)
            act=load(ROOT/'references/act-rules.json')
            related=[{'id':r['id'],'title':r['title'],'status':r['status'],
                      'relationship':next(x['mapping'] for x in r['criteria'] if x['criterion']==c['id'])}
                     for r in act['rules'] if r['status']!='deprecated' and any(x['criterion']==c['id'] for x in r['criteria'])]
            print(json.dumps({'case':case,'criterion':c,'config_digest':meta['config_digest'],
                              'interaction_review':run_plan(run).get('interaction_reviews',{}).get(case['page_id']),
                              'definitions_match_installed':meta['catalog_digest']==digest(CATALOG),
                              'catalog_snapshot':str(run/'catalog.snapshot.json') if (run/'catalog.snapshot.json').exists() else None,
                              'evidence_base':str(run),
                              'reference_notice':'現在のスキルの参考資料。保存した定義が異なる場合は、その版の手順を確認する。新しい定義での判定は新しいrunで行う。',
                              'guide':str(ROOT/'references/criteria'/(c['id']+'.md')) if same_criterion else None,
                              'source':str(ROOT/'references/sources'/(c['id']+'.md')),
                              'public_tests':str(ROOT/'references/tests'/(c['id']+'.md')),
                              'act_guidance':str(ROOT/'references/act'/(c['id']+'.md')),
                              'act_source_commit':act['source_commit'],'act_rules':related},ensure_ascii=False,indent=2));return 0
        if args.command=='record':
            record(run,load(args.file));print('Recorded');return 0
        if args.command=='attach':
            run_catalog(run,for_write=True)
            _,case=get_case(run,args.case);src=Path(args.file)
            dest=run/'evidence/attached'/case['case_id']/(uuid.uuid4().hex[:8]+'-'+src.name)
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
            print(dest.relative_to(run));return 0
        if args.command=='probe':
            meta,_=run_catalog(run,for_write=True)
            _,case=get_case(run,args.case);config=json.loads(json.dumps(meta['config']))
            u=urlsplit(case['page_url']);path=u.path+('?' + u.query if u.query else '')+('#' + u.fragment if u.fragment else '')
            config['scope'].update(mode='configured',pages=[path],seeds=[path],known_pages=[],max_pages=1)
            config['environments']=[e for e in config['environments'] if e['id']==case['environment']]
            prior=next((s['actions'] for s in config.get('states',[]) if s['id']==case['state']),[])
            value=load(args.actions)
            config['states']=[{'id':'probe','paths':[u.path or '/'],'actions':prior+value['actions'],
                              'observe':value.get('observe',[]),'assert':value['assert']}]
            dest=run/'evidence/attached'/case['case_id']/('probe-'+uuid.uuid4().hex[:8]);dest.mkdir(parents=True)
            save(dest/'probe-request.json',value)
            save(dest/'probe-config.json',config)
            save(dest/'probe-origin.json',{'parent_case_id':case['case_id'],'parent_config_digest':meta['config_digest'],
                'catalog_digest':meta['catalog_digest'],'request_digest':digest(value),'replayed_state':case['state']})
            if args.command=='page-audit':
                make_plan(run,{'captures':[]});return run_page_audit(run,args)
            from browser_capture import collect
            asyncio.run(collect(config,dest));print(dest.relative_to(run));return 0
        if args.command=='scope-review':
            value=validate_scope_review(run,load(args.file))
            save(run/'scope-review.json',value);return 0
        if args.command=='report':
            result = refresh_report(run)
            return 0 if not args.strict or result['audit_complete'] else 2
    except (ValueError,KeyError,OSError,ImportError) as exc:
        print('ERROR:',str(exc),file=sys.stderr);return 1


if __name__=='__main__':
    raise SystemExit(main())
