"""Private test oracles, public tasks, evidence-bound predictions and regression scoring."""
from collections import Counter
from datetime import datetime,timezone
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import uuid
from urllib.parse import urlsplit,unquote

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import audit
import verification_modes as modes
from . import case_contracts


def load(path):return json.loads(Path(path).read_text())
def save(path,value):audit.save(Path(path),value)
def digest(value):return audit.digest(value)
def file_hash(path):return sha256(Path(path).read_bytes()).hexdigest()
def timestamp():return datetime.now(timezone.utc).isoformat()


def local(root,relative):
    if not isinstance(relative,str) or not relative or '\\' in relative or Path(relative).is_absolute():
        raise ValueError('相対パスを指定する')
    path=(Path(root)/relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):raise ValueError('範囲外のパス')
    return path


class Resources(HTMLParser):
    def __init__(self):super().__init__();self.paths=[];self.in_script=False
    def script_paths(self,text):
        patterns=[r"(?:window\.)?location(?:\.href)?\s*=\s*['\"]([^'\"]+)['\"]",r"(?:window\.)?location\.(?:assign|replace)\(\s*['\"]([^'\"]+)['\"]"]
        for pattern in patterns:self.paths += [v for v in re.findall(pattern,text) if not v.startswith('#')]
    def handle_endtag(self,tag):
        if tag=='script':self.in_script=False
    def handle_data(self,data):
        if self.in_script:self.script_paths(data)
    def handle_starttag(self,tag,attrs):
        if tag=='script':self.in_script=True
        for k,v in attrs:
            if k.startswith('on') and v:self.script_paths(v)
        self.paths += [v for k,v in attrs if k in {'src','href','poster'} and v and not v.startswith('#')]


def corpus(root=None):
    root=Path(root or ROOT/'benchmarks/cases').resolve();suites=[];files={}
    checkpoints={r['id']:r for r in modes.catalog()['checkpoints']}
    for manifest in sorted(root.glob('*/suite.json'),key=lambda p:tuple(map(int,p.parent.name.split('.')))):
        value=load(manifest);sc=value.get('criterion');public=manifest.parent/'public'
        if sc not in audit.CRITERIA or manifest.parent.name!=sc or value.get('schema_version')!='1':raise ValueError('基準又はsuiteの形式が不正')
        seen=set()
        for case in value.get('cases',[]):
            if not re.fullmatch(r'c[0-9]{2,}',case['id']) or case['id'] in seen:raise ValueError('ケースIDが不正又は重複')
            seen.add(case['id']);pages=case['pages'];states={s['id'] for s in case['states']}
            if not pages or len(set(pages))!=len(pages) or len(states)!=len(case['states']):raise ValueError('ページ・状態の重複又は不足')
            for page in pages:
                if not local(public,page).is_file() or not page.endswith('.html'):raise ValueError('実在するHTMLページを指定する')
            if not case['checkpoints'] or len(set(case['checkpoints']))!=len(case['checkpoints']):raise ValueError('確認観点が重複又は不足')
            if case.get('oracle_scope')!='exhaustive-for-listed-checkpoints':raise ValueError('正解の列挙範囲を明示する')
            for point in case['checkpoints']:
                if point not in checkpoints or checkpoints[point]['criterion']!=sc:raise ValueError('確認観点と達成基準が不一致')
            expected=set()
            if not case.get('expectations'):raise ValueError('正解を用意していないケースを登録しない')
            for item in case['expectations']:
                key=observation_key(item)
                if key in expected:raise ValueError('期待結果が重複')
                expected.add(key)
                if item['page'] not in pages or item['state'] not in states or item['checkpoint'] not in case['checkpoints']:
                    raise ValueError('期待結果がケースのページ・状態・観点と不一致')
                if item['expected'] not in {'passed','failed','inapplicable'} or not item['rationale'].strip():raise ValueError('正解と根拠が必要')
                if set(item['modes'])!=set(modes.MODES) or any(v not in {'evaluate','defer'} for v in item['modes'].values()):raise ValueError('モード別の評価条件が不正')
                if item['evidence_kind'] not in {'program','semantic','visual-semantic','cross-page','screen-reader'}:raise ValueError('証拠の種類が不正')
            case_contracts.validate(case)
            for point,aliases in case.get('target_aliases',{}).items():
                if point not in case['checkpoints'] or not isinstance(aliases,dict):raise ValueError('対象の別名が確認観点に対応しない')
                for alias,canonical in aliases.items():
                    if not isinstance(alias,str) or not any(e['target']==canonical and e['checkpoint']==point for e in case['expectations']):raise ValueError('対象の別名が正規の対象に対応しない')
        if not seen:raise ValueError('未整備の空suiteを実行可能として登録しない')
        for path in sorted(public.rglob('*')):
            if path.is_symlink():raise ValueError('公開ファイルにsymlinkを使わない')
            if not path.is_file():continue
            if path.suffix=='.json':raise ValueError('公開領域に正解やJSONを置かない')
            if path.suffix=='.html':
                parser=Resources();parser.feed(path.read_text())
                for reference in parser.paths:
                    parts=urlsplit(reference)
                    if parts.scheme or parts.netloc:raise ValueError('画像・音声・ページは基準内に同梱する')
                    resource=(path.parent/unquote(parts.path)).resolve()
                    if not resource.is_relative_to(public.resolve()) or not resource.is_file():raise ValueError('公開ファイルから範囲外又は欠落した資料を参照している: '+str(path)+' -> '+reference)
            files[f'{sc}/{path.relative_to(public).as_posix()}']=file_hash(path)
        suites.append(value)
    if not suites:raise ValueError('検証用のsuiteがない')
    return {'schema_version':'1','suites':suites,'public_files':files,'digest':digest({'suites':suites,'public_files':files})}


def observation_key(item):return (item['page'],item['state'],item['target'],item['checkpoint'])


def verify(run):
    run=Path(run);meta=load(run/'run.json');proof=load(run/'integrity.json')
    for name,expected in proof['files'].items():
        path=local(run,name)
        if not path.is_file() or file_hash(path)!=expected:raise ValueError('ベンチマークの入力・証拠が変更された: '+name)
    if digest(load(run/'oracle.snapshot.json'))!=meta['oracle_digest']:raise ValueError('正解スナップショットが不一致')
    return meta,load(run/'progress.json')


def freeze(run,paths):
    from ledger_lock import run_lock
    run=Path(run);locks=run/'.integrity-lock';locks.mkdir(exist_ok=True)
    # Evidence may arrive from independent jobs while another report is saved.
    # Use a separate lock so callers holding the ledger lock can append safely.
    with run_lock(locks):
        path=run/'integrity.json';proof=load(path) if path.exists() else {'files':{}}
        for p in paths:
            name=Path(p).relative_to(run).as_posix();h=file_hash(p)
            if name in proof['files'] and proof['files'][name]!=h:raise ValueError('保存済みの証拠を置き換えない: '+name)
            proof['files'][name]=h
        save(path,proof)


def tasks(run):return load(Path(run)/'worker/tasks.json')['jobs']


def oracle_jobs(run):
    oracle=load(Path(run)/'oracle.snapshot.json')
    by_case={(s['criterion'],c['id']):c for s in oracle['suites'] for c in s['cases']}
    return {j['id']:by_case[(j['criterion'],j['case'])] for j in tasks(run)}


def evidence(run,job,paths):
    if not isinstance(paths,list) or not paths:raise ValueError('実際の証拠ファイルが必要')
    prefixes=[f'audit-runs/{job["id"]}/',f'attachments/{job["id"]}/']
    checked=[]
    for path in paths:
        p=local(run,path)
        canonical=p.relative_to(Path(run).resolve()).as_posix()
        if not p.is_file() or not any(canonical.startswith(prefix) for prefix in prefixes):raise ValueError('証拠がこのジョブに対応していない')
        checked.append({'path':canonical,'sha256':file_hash(p)})
    return checked


def speech_receipt(run,job,paths):
    for path in paths:
        if not path.endswith('.json'):continue
        try:r=load(local(run,path))
        except (ValueError,UnicodeError):continue
        if not isinstance(r,dict) or r.get('case_id')!=job['id'] or r.get('status') not in {'collected','assertion_failed'}:continue
        if r.get('scenario',{}).get('url') not in job['urls'].values():continue
        env=r.get('environment',{})
        if env.get('simulation') is not False or not (env.get('installation_verified') or env.get('installationVerified')):continue
        if not (env.get('reader') or env.get('readerName')):continue
        observations=r.get('observations',[])
        # At least one control utterance is required even for a silent negative case.
        utterances=[]
        for o in observations:
            utterances += [s.get('phrase','') for s in o.get('speech',[]) if isinstance(s,dict)]
            utterances += o.get('spokenPhrases',[])
            utterances.append((o.get('capture') or {}).get('spokenPhrase',''))
        if observations and any(isinstance(s,str) and s.strip() for s in utterances):return True
    return False


def record_review(run,value):
    from ledger_lock import run_lock
    run=Path(run)
    with run_lock(run):
        meta,progress=verify(run)
        if value.get('schema_version')!='1' or value.get('run_id')!=meta['run_id'] or value.get('corpus_digest')!=meta['corpus_digest']:
            raise ValueError('検証run又は問題集の版が不一致')
        jobs={j['id']:j for j in tasks(run)};job=jobs.get(value.get('job_id'))
        if job is None:raise ValueError('ジョブが存在しない')
        seen=set();observations=value.get('observations',[])
        if not isinstance(observations,list) or not observations:raise ValueError('観察結果がない')
        for row in observations:
            row['target']=job.get('target_aliases',{}).get(row['checkpoint'],{}).get(row['target'],row['target'])
            key=observation_key(row)
            if key in seen or row['page'] not in job['pages'] or row['state'] not in {s['id'] for s in job['states']} or row['checkpoint'] not in job['checkpoints']:
                raise ValueError('観察がページ・状態・確認観点に対応しない、又は重複')
            seen.add(key)
            if row['outcome'] not in {'passed','failed','inapplicable','cant_tell','not_run'}:raise ValueError('判定の値が不正')
            if row['checkpoint'] in job.get('acquisition_checkpoints',[]):raise ValueError('取得期待の照合は未接続です。取得した証拠を保存し、適合・不適合として取り込まない')
            method=row.get('method');mode=modes.MODES[job['mode']]
            if method not in {'program','ai','screen-reader'} or (method=='ai' and not mode['ai']) or (method=='screen-reader' and not mode['screen_reader']):raise ValueError('選択モードで使用しない判定方法')
            if not isinstance(row.get('observed'),str) or len(row['observed'].strip())<10:raise ValueError('具体的な観察が必要')
            if row['outcome'] in {'not_run','cant_tell'}:
                row['verified_evidence']=evidence(run,job,row['evidence']) if row.get('evidence') else []
                continue
            row['verified_evidence']=evidence(run,job,row.get('evidence'))
            point=next(r for r in meta['mode_catalog']['checkpoints'] if r['id']==row['checkpoint'])
            # Availability is an independent guard, not the source of an expected answer.
            if point['support'][job['mode']]=='no':raise ValueError('このモードで確認できない観点を確定しない')
            requirements=job.get('evidence_requirements',{}).get(row['checkpoint'],{})
            if requirements.get('image') and not any(Path(p).suffix.lower() in {'.png','.jpg','.jpeg','.webp'} for p in row['evidence']):
                raise ValueError('実際に確認した画像の証拠が必要')
            if requirements.get('speech') and method!='screen-reader':raise ValueError('この観点には実SRの方法が必要')
            if method=='screen-reader' and not speech_receipt(run,job,row['evidence']):raise ValueError('実SRと対照の発話が必要。AXツリーでは代用しない')
            if requirements.get('comparison'):
                receipts=progress['jobs'].get(job['id'],{})
                for page in job['pages']:
                    prefix=receipts.get(page,{}).get('directory','')
                    if not prefix or not any(p.startswith(prefix+'/') for p in row['evidence']):raise ValueError('比較する全ページの証拠が必要')
        saved=dict(value,recorded_at=timestamp())
        path=run/'reviews'/(uuid.uuid4().hex+'.json');save(path,saved)
        freeze(run,[path,*[local(run,e['path']) for r in observations for e in r['verified_evidence']]])
        index=load(run/'review-index.json') if (run/'review-index.json').exists() else {'entries':[]}
        index['entries'].append(path.relative_to(run).as_posix());save(run/'review-index.json',index)
        return {'review':path.relative_to(run).as_posix(),'observations':len(observations)}


def program_predictions(run,job,progress):
    """Decode only observations the production pipeline actually emitted."""
    run=Path(run).resolve()
    result={}
    rule_map={'image-alt':'1.1.1-01','document-title':'2.4.2-01'}
    for page,receipt in progress['jobs'].get(job['id'],{}).items():
        if receipt['status']!='completed':continue
        root=local(run,receipt['directory']);graph=load(root/'exploration.json')
        initial=[n for n in graph.get('nodes',[]) if not n['route']]
        for node in initial:
            raw=load(root/node['evidence_dir']/'axe.json')
            for group,outcome in [('violations','failed'),('passes','passed'),('incomplete','cant_tell')]:
                for rule in raw.get(group,[]):
                    point=rule_map.get(rule['id'])
                    if point not in job['checkpoints']:continue
                    for target in rule.get('nodes',[]):
                        selectors=target.get('target',[])
                        if len(selectors)!=1 or not isinstance(selectors[0],str):continue
                        row=dict(page=page,state='initial',target=selectors[0],checkpoint=point,outcome=outcome,
                            method='program',observed=target.get('failureSummary') or target.get('html',''),
                            evidence=[(root/node['evidence_dir']/'axe.json').relative_to(run).as_posix()],source='production axe / '+rule['id'])
                        result[observation_key(row)]=row
        if '2.1.1-01' in job['checkpoints']:
            grouped={}
            for edge in graph.get('edges',[]):
                route=edge['route']
                if len(route)!=1 or route[0].get('type')!='key':continue
                a=route[0];target=a['selector'];error=edge.get('error')
                outcome='cant_tell' if edge.get('blocked_requests') or edge.get('native_events') else 'failed' if error else 'passed'
                row=dict(page=page,state='initial',target=target,checkpoint='2.1.1-01',outcome=outcome,method='program',
                    observed=error or '実キーで対象へ到達し入力を送出した。機能の実行は別の観点。',
                    evidence=[(root/edge['evidence_dir']/'transition.json').relative_to(run).as_posix()],source='production key dispatch')
                grouped.setdefault(target,[]).append(row)
            for target,items in grouped.items():
                chosen=next((r for r in items if r['outcome']=='passed'),items[0]);result[observation_key(chosen)]=chosen
    return result


def score(run):
    run=Path(run);meta,progress=verify(run);oracles=oracle_jobs(run);jobs=tasks(run);reviews={}
    index=load(run/'review-index.json') if (run/'review-index.json').exists() else {'entries':[]}
    for name in index['entries']:
        value=load(local(run,name));target=reviews.setdefault(value['job_id'],{})
        for row in value['observations']:target[observation_key(row)]=row
    rows=[];extras=[];pending_evidence=[]
    for job in jobs:
        predicted=program_predictions(run,job,progress);predicted.update(reviews.get(job['id'],{}))
        for contract in oracles[job['id']].get('evidence_expectations',[]):
            point=next(p for p in meta['mode_catalog']['checkpoints'] if p['id']==contract['checkpoint'])
            pending_evidence.append(dict(job_id=job['id'],criterion=job['criterion'],mode=job['mode'],page=contract['page'],state=contract['state'],checkpoint=contract['checkpoint'],kind=contract['kind'],status='deferred' if point['support'][job['mode']]=='no' else 'not_evaluated'))
        expected=oracles[job['id']]['expectations'];known={observation_key(e) for e in expected}
        for e in expected:
            key=observation_key(e);actual=predicted.get(key);outcome=actual['outcome'] if actual else 'not_run'
            evaluated=outcome in {'passed','failed','inapplicable'};needed=e['modes'][job['mode']]=='evaluate'
            grade=('correct' if outcome==e['expected'] else 'incorrect') if evaluated else 'not_evaluated' if needed else 'deferred'
            confusion=''
            if evaluated:
                confusion=('TP' if outcome=='failed' else 'FN') if e['expected']=='failed' else 'FP' if outcome=='failed' else 'TN'
            rows.append(dict(job_id=job['id'],criterion=job['criterion'],case=job['case'],mode=job['mode'],
                **{k:e[k] for k in ['page','state','target','checkpoint','expected']},actual=outcome,grade=grade,
                required=needed,confusion=confusion,rationale=e['rationale'],observed=(actual or {}).get('observed','この観点の確定結果がまだ記録されていません。'),
                evidence=(actual or {}).get('evidence',[]),method=(actual or {}).get('method',''),
                source=(actual or {}).get('source',(actual or {}).get('method',''))))
        for key,prediction in predicted.items():
            if key not in known and prediction['outcome']=='failed':
                extras.append(dict(job_id=job['id'],criterion=job['criterion'],mode=job['mode'],**prediction))
    grade_counts=Counter(r['grade'] for r in rows);confusion=Counter(r['confusion'] for r in rows if r['confusion'])
    confusion['FP']+=len(extras)
    all_criteria=[]
    for c in meta['criteria_catalog']:
        selected=[r for r in rows if r['criterion']==c['id']]
        all_criteria.append(dict(criterion=c['id'],title=c['title'],level=c['level'],
            status='unprepared' if c['id'] not in {s['criterion'] for s in load(run/'oracle.snapshot.json')['suites']} else 'not_selected' if not selected else 'prepared',
            expected_observations=len(selected),evaluated=sum(r['grade'] in {'correct','incorrect'} for r in selected),
            counts={mode:dict(Counter(r['grade'] for r in selected if r['mode']==mode)) for mode in meta['modes']}))
    detected=sum(r['expected']=='failed' and r['actual']=='failed' for r in rows)
    total_failures=sum(r['expected']=='failed' for r in rows)
    precision=confusion['TP']/(confusion['TP']+confusion['FP']) if confusion['TP']+confusion['FP'] else None
    recall=confusion['TP']/(confusion['TP']+confusion['FN']) if confusion['TP']+confusion['FN'] else None
    status='failed' if grade_counts['incorrect'] or extras else 'incomplete' if grade_counts['not_evaluated'] or any(c['status']=='not_evaluated' for c in pending_evidence) else 'clear_for_selected_checks'
    return dict(schema_version='1',run_id=meta['run_id'],corpus_digest=meta['corpus_digest'],modes=meta['modes'],
        selection=meta['selection'],configuration=meta['configuration'],implementation_digest=meta['implementation_digest'],
        environment=meta.get('environment',{}),standard=meta.get('standard','WCAG-2.2'),normative_hashes=meta.get('normative_hashes',{}),
        scorer_digest=file_hash(Path(__file__)),created_at=timestamp(),selected_checks_status=status,
        overall_status='failed' if status=='failed' else 'incomplete' if grade_counts['not_evaluated'] or grade_counts['deferred'] or pending_evidence else status,
        counts=dict(grade_counts),confusion=dict(confusion),precision_on_evaluated=precision,recall_on_evaluated=recall,
        methods_by_mode={m:dict(Counter(r['method'] for r in rows if r['mode']==m and r['grade'] in {'correct','incorrect'})) for m in meta['modes']},
        detected_known_failures=detected,total_known_failures=total_failures,undetected_known_failures=total_failures-detected,
        rows=rows,unexpected_findings=extras,criteria=all_criteria,pending_evidence_contracts=pending_evidence,
        notice_evidence='取得期待の照合は未接続です。別表の未確認を適合・不適合の件数へ混ぜず、必要な取得期待が残る実行は未完了とします。',
        notice='作成者が定めた有限の確認観点の採点です。独立した専門家による正解確認は未実施です。未実施・モードによる省略・未整備の基準を成功に数えません。検出率は評価できた範囲と全問題の未検出数を併記します。')


def compare(baseline,current):
    for field in ['schema_version','corpus_digest','modes','selection','configuration','scorer_digest','environment','standard','normative_hashes']:
        if baseline.get(field)!=current.get(field):raise ValueError('比較条件が異なる: '+field+'。同じ問題集・モード・設定・採点器で比較する')
    before={ (r['job_id'],*observation_key(r)):r for r in baseline['rows']}
    after={ (r['job_id'],*observation_key(r)):r for r in current['rows']}
    if before.keys()!=after.keys():raise ValueError('比較対象の確認観点が異なる')
    regressions=[];improvements=[]
    for key,old in before.items():
        new=after[key]
        if old['grade']=='correct' and new['grade']!='correct':regressions.append(dict(key=list(key),before=old['actual'],after=new['actual']))
        elif old['grade']!='correct' and new['grade']=='correct':improvements.append(dict(key=list(key),before=old['actual'],after=new['actual']))
        elif old['grade']!='incorrect' and new['grade']=='incorrect':regressions.append(dict(key=list(key),before=old['actual'],after=new['actual']))
    old_extras={(r['job_id'],*observation_key(r)) for r in baseline['unexpected_findings']}
    for r in current['unexpected_findings']:
        if (r['job_id'],*observation_key(r)) not in old_extras:regressions.append(dict(key=[r['job_id'],*observation_key(r)],before='no_false_positive',after='failed'))
    return dict(status='regressions' if regressions else 'no_regressions',regressions=regressions,improvements=improvements,
                current_quality=current['overall_status'],notice='新しい劣化がないことと、問題集を全て確認できたことは別です。')
