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
    if c.get('auth_state'):
        c['auth_state']=str(Path(c['auth_state']).resolve())
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
    return {'level':meta['config']['level'],'url':meta['config']['url'],'audit_complete':complete,
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
            'counts':dict(stats),'criteria':per_criterion,'cases':rows}


@locked
def report(run):
    result=outcomes(run);save(run/'report.json',result)
    labels={'passed':'検査通過','failed':'不適合','inapplicable':'対象外','cant_tell':'判断保留','not_run':'未実施'}
    rows=[]
    for c in result['cases']:
        a=c['assessment_data'];ev=[]
        if a:
            ev=[f'<a href="{escape(e["path"],quote=True)}">{escape(e["path"])}</a>' for e in a['verified_evidence']]
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
                f'<p>{limit_notice}<a href="{escape(c["assessment"],quote=True)}">全区間の比較記録</a></p></details>')
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
    excluded=[c for c in result['criteria'] if c['status']=='out_of_target_level']
    status_labels={'out_of_target_level':'目標レベル外（未検証）','failed':'不適合あり','unverified':'未確認',
                   'inapplicable':'対象外','passed_checks':'記録した検査は通過'}
    by_criterion=''.join(f'<li>{escape(c["id"])} {escape(c["title"])}（{c["level"]}）：{status_labels[c["status"]]}</li>' for c in result['criteria'])
    definition_notice=('現在の検査手順と同じ定義を使用しています。' if result['definitions_match_installed'] else
                       '検査手順の更新前の記録です。当時の定義で再集計しました。新しい手順での検査結果ではありません。')
    definition_link='<a href="catalog.snapshot.json">保存した検査定義</a>' if (run/'catalog.snapshot.json').exists() else 'この旧実行には定義のコピーがありません。'
    collection_notice={'completed':'予定した収集の試行を終了', 'running':'収集中、又は収集の途中で停止',
        'interrupted':'収集の途中で停止', 'legacy_unspecified':'当時の収集記録を使用'}[result['collector_status']]
    page=f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>WCAG検証結果 — {escape(result['url'])}</title><style>body{{font:1rem/1.7 system-ui;margin:2rem;max-width:100rem;color:#202020;background:#fff}}table{{border-collapse:collapse;min-width:64rem}}td,th{{border:1px solid #666;padding:.6rem;vertical-align:top;text-align:left;overflow-wrap:anywhere}}a{{color:#00529b}}:focus-visible{{outline:3px solid #000;outline-offset:3px}}.scroll{{overflow:auto;max-width:100%}}pre{{white-space:pre-wrap}}</style></head><body>
<main><h1>WCAG {result['level']} 検証結果</h1><p>対象：{escape(result['url'])}</p><p>{escape(summary)}</p>
<p>予定範囲の検査完了：{'はい' if result['audit_complete'] else 'いいえ'}</p><p>サイト・状態・適合要件の範囲確認：{escape(inventory)}</p>
<p>判定・引き継ぎの記録：{result['recorded_cases']} / {len(result['cases'])}。人による確認待ち：{len(result['human_review_cases'])}。<a href="human-review.md">対象と具体的な確認手順</a>。引き継ぎ先が未整理の判断保留・未網羅：{len(result['unassigned_remaining_cases'])}。</p>
<p>ブラウザー証拠の収集：{escape(collection_notice)}。</p>
<p>未訪問URL：{len(result['unvisited'])}。目標レベル外の基準：{len(excluded)}。</p>
<p>未収集のページ・状態・環境：{len(result['missing_captures'])}。計画にない検査票：{len(result['missing_cases'])}。</p>
<details><summary>使用した検査定義</summary><p>{escape(definition_notice)}</p><p>定義ID：<code style="overflow-wrap:anywhere">{escape(result['catalog_digest'])}</code></p><p>{definition_link}</p></details>
<p>{escape(result['conformance_claim'])}</p><details><summary>全86基準の状況</summary><ul>{by_criterion}</ul></details>
<h2>ページ・状態・環境・基準ごとの結果</h2><div class="scroll" tabindex="0" role="region" aria-label="検査結果の表"><table><caption>具体的な観察結果と証拠。未実施は通過数に含めません。</caption>
<thead><tr><th scope="col">基準</th><th scope="col">対象</th><th scope="col">結果</th><th scope="col">観察・残る確認</th><th scope="col">証拠</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p>修正担当向け：<a href="issues.md">不適合の再現と期待結果</a>。機械処理用：<a href="report.json">report.json</a>。元の収集記録：<a href="capture-manifest.json">capture-manifest.json</a>。</p></main></body></html>'''
    (run/'report.html').write_text(page)
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
    (run/'issues.md').write_text('\n'.join(issues)+'\n')
    (run/'human-review.md').write_text(handoff_markdown([c for c in result['cases']
        if c['assessment_data'] and c['assessment_data'].get('human_handoff')]))
    print(json.dumps({k:result[k] for k in ['audit_complete','scope_confirmed','counts']},ensure_ascii=False))
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('init');p.add_argument('--url',required=True);p.add_argument('--config',required=True)
    sub.add_parser('doctor')
    p=sub.add_parser('rules');p.add_argument('--criterion',choices=list(CRITERIA))
    p.add_argument('--status',choices=['active','approved','proposed','deprecated','all'],default='active')
    p=sub.add_parser('rule');p.add_argument('--id',required=True)
    p=sub.add_parser('start');p.add_argument('--config',required=True);p.add_argument('--out',required=True)
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
            q.add_argument('--task');q.add_argument('--owner');q.add_argument('--page');q.add_argument('--criterion')
            q.add_argument('--pending-only',action='store_true')
        else:q.add_argument('--file',required=True);q.add_argument('--check',action='store_true')
    for name in ['pending','case','record','report','attach','scope-review','recover','probe','snapshot']:
        p=sub.add_parser(name);p.add_argument('--run',required=True)
        if name=='case':p.add_argument('--id',required=True)
        if name=='pending':
            p.add_argument('--criterion');p.add_argument('--page');p.add_argument('--limit',type=int,default=20)
            p.add_argument('--task');p.add_argument('--owner')
            p.add_argument('--status',choices=['not_run','cant_tell','human','all'],default='all')
        if name in {'record','scope-review'}:p.add_argument('--file',required=True)
        if name=='attach':p.add_argument('--case',required=True);p.add_argument('--file',required=True)
        if name=='probe':p.add_argument('--case',required=True);p.add_argument('--actions',required=True)
        if name=='report':p.add_argument('--strict',action='store_true')
    args=parser.parse_args(argv)
    try:
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
            save(p,init_config(args.url));print(p);return 0
        if args.command=='start':
            raw=load(args.config)
            if raw.get('auth_state') and not Path(raw['auth_state']).is_absolute():
                raw['auth_state']=str(Path(args.config).resolve().parent/raw['auth_state'])
            config=validate_config(raw);run=Path(args.out)
            if run.exists() and any(run.iterdir()):raise ValueError('出力先は空にする。既存結果はpending/reportで再開する')
            run.mkdir(parents=True,exist_ok=True)
            save(run/'run.json',{'created_at':datetime.now(timezone.utc).isoformat(),'config':config,
                                 'config_digest':digest(config),'catalog_digest':digest(CATALOG)})
            snapshot_catalog(run)
            from browser_capture import collect
            manifest=asyncio.run(collect(config,run));make_plan(run,manifest);report(run);return 0
        run=Path(args.run)
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
                                      page=args.page,criterion=args.criterion,pending=args.pending_only)
            else:value=workbook.import_book(run,Path(args.file),check=args.check)
            print(json.dumps(value,ensure_ascii=False,indent=2));return 0
        if args.command=='snapshot':
            print(json.dumps(snapshot_catalog(run),ensure_ascii=False));return 0
        if args.command=='recover':
            manifest=load(run/'capture-manifest.json');make_plan(run,manifest);report(run);return 0
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
            plan=run_plan(run);pending=work_queue.select(pending,plan,task=args.task,owner=args.owner)
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
                              'definitions_match_installed':meta['catalog_digest']==digest(CATALOG),
                              'catalog_snapshot':str(run/'catalog.snapshot.json') if (run/'catalog.snapshot.json').exists() else None,
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
            config['scope'].update(seeds=[path],known_pages=[],max_pages=1)
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
            from browser_capture import collect
            asyncio.run(collect(config,dest));print(dest.relative_to(run));return 0
        if args.command=='scope-review':
            value=validate_scope_review(run,load(args.file))
            save(run/'scope-review.json',value);return 0
        if args.command=='report':
            r=report(run);return 0 if not args.strict or r['audit_complete'] else 2
    except (ValueError,KeyError,OSError,ImportError) as exc:
        print('ERROR:',str(exc),file=sys.stderr);return 1


if __name__=='__main__':
    raise SystemExit(main())
