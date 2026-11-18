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
RUNTIME=ROOT/'skills/wcag-audit-kit'
sys.path.insert(0,str(RUNTIME/'scripts'))
import audit
import verification_modes as modes
import state_labels
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
            state_labels.public_specs(case['states'])
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
    run=Path(run).resolve();locks=run/'.integrity-lock';locks.mkdir(exist_ok=True)
    # Evidence may arrive from independent jobs while another report is saved.
    # Use a separate lock so callers holding the ledger lock can append safely.
    with run_lock(locks):
        path=run/'integrity.json';proof=load(path) if path.exists() else {'files':{}}
        for p in paths:
            name=Path(p).resolve().relative_to(run).as_posix();h=file_hash(p)
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
            if row['checkpoint'] in job.get('acquisition_checkpoints',[]):raise ValueError('取得した証拠を保存し、取得期待を適合・不適合として取り込まない')
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


def axe_contrast_observation(node, outcome):
    """Keep axe's verdict and the measurement for one reported text target."""
    if outcome == 'cant_tell':
        return outcome, node.get('failureSummary') or 'axeがこの対象の文字コントラストを確定できなかった。'
    checks = [check.get('data') for group in ('any', 'all', 'none')
              for check in node.get(group, []) if check.get('id') == 'color-contrast']
    data = checks[0] if len(checks) == 1 and isinstance(checks[0], dict) else {}
    ratio = data.get('contrastRatio')
    minimum = data.get('expectedContrastRatio')
    fields = ('fgColor', 'bgColor', 'fontSize', 'fontWeight')
    if (type(ratio) not in (int, float) or not 1 <= ratio <= 21 or minimum not in ('3:1', '4.5:1')
            or not all(isinstance(data.get(key), str) and data[key].strip() for key in fields)):
        return 'cant_tell', 'axeの対象別の比・比較基準・色・文字サイズ又は太さの証拠が不足している。'
    # The numeric ratio in axe output is rounded down for display. Its own
    # verdict uses the unrounded value and the applicable size/weight threshold.
    observed = (f'axeの文字コントラスト比は{ratio}:1、比較基準は{minimum}。'
                f'前景 {data["fgColor"]}、背景 {data["bgColor"]}、文字 {data["fontSize"]}、'
                f'太さ {data["fontWeight"]}。')
    return outcome, observed


def program_predictions(run,job,progress):
    """Decode only observations the production pipeline actually emitted."""
    run=Path(run).resolve()
    result={}
    rule_map={'image-alt':'1.1.1-01','document-title':'2.4.2-01','color-contrast':'1.4.3-01'}
    contrast_states = {state['id'] for state in job.get('states', [])}
    for page,receipt in progress['jobs'].get(job['id'],{}).items():
        if receipt['status']!='completed':continue
        root=local(run,receipt['directory']);graph=load(root/'exploration.json')
        labels=state_labels.public_specs(job.get('states',[]))
        for node in graph.get('nodes',[]):
            proof=[(root/node['evidence_dir']/'axe.json').relative_to(run).as_posix()]
            if not node['route']:states=['initial']
            else:
                folder=root/node['evidence_dir'];state_file=folder/'state.json';transition_file=folder/'transition.json'
                if not state_file.is_file() or not transition_file.is_file():continue
                transition=load(transition_file)
                if transition.get('route')!=node['route'] or transition.get('error') or transition.get('blocked_requests') or transition.get('native_events'):continue
                states=state_labels.verified(labels,node['route'],load(state_file).get('state_labels',[]))
                proof += [p.relative_to(run).as_posix() for p in [state_file,transition_file]]
            if not states:continue
            raw=load(root/node['evidence_dir']/'axe.json')
            for state in states:
                for group,outcome in [('violations','failed'),('passes','passed'),('incomplete','cant_tell')]:
                    for rule in raw.get(group,[]):
                        point=rule_map.get(rule['id'])
                        if point not in job['checkpoints']:continue
                        if point == '1.4.3-01' and state not in contrast_states:continue
                        for target in rule.get('nodes',[]):
                            selectors=target.get('target',[])
                            if len(selectors)!=1 or not isinstance(selectors[0],str):continue
                            actual, observed = outcome, target.get('failureSummary') or target.get('html','')
                            if point == '1.4.3-01':
                                actual, observed = axe_contrast_observation(target, outcome)
                            row=dict(page=page,state=state,target=selectors[0],checkpoint=point,outcome=actual,
                                method='program',observed=observed,
                                evidence=proof,source='production axe / '+rule['id'])
                            key=observation_key(row);previous=result.get(key)
                            if previous and (previous['outcome']!=actual or previous.get('conflicting')):
                                row.update(outcome='cant_tell',conflicting=True,observed='同じ状態・対象の機械証拠が矛盾しているため確定しない。',
                                    evidence=sorted(set(previous['evidence']+proof)))
                            result[key]=row
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


def initial_inventory(run, job, progress, page, frozen):
    """Resolve a complete initial capture from this job and page only."""
    def read_frozen(path):
        name = path.resolve().relative_to(run).as_posix()
        if name not in frozen:
            return None
        try:
            value = load(path)
        except (OSError, ValueError):
            return None
        return value if isinstance(value, dict) else None

    entry = progress['jobs'].get(job['id'], {}).get(page, {})
    url = job['urls'][page]
    if entry.get('status') != 'completed' or entry.get('exit_code') != 0:
        return None, []
    try:
        attempt = local(run, entry.get('directory'))
        if not attempt.is_relative_to(local(run, f'audit-runs/{job["id"]}')) or attempt.name != 'run':
            return None, []
        receipt_path = attempt.parent / 'receipt.json'
        receipt = read_frozen(receipt_path) or {}
        expected_receipt = dict(job_id=job['id'], page=page, mode=job['mode'], url=url, status='completed', exit_code=0)
        if any(receipt.get(key) != value for key, value in expected_receipt.items()):
            return None, []

        manifest_path = attempt / 'capture-manifest.json'
        manifest = read_frozen(manifest_path) or {}
        candidates = [capture for capture in manifest.get('captures', [])
                      if isinstance(capture, dict) and capture.get('url') == url and capture.get('state') == 'initial'
                      and capture.get('execution') == 'completed' and capture.get('collection_state') == 'finished']
        if len(candidates) != 1:
            return None, []
        capture = candidates[0]
        directory = local(attempt, capture['evidence_dir'])
        if not directory.is_relative_to(attempt / 'evidence') or directory == attempt / 'evidence':
            return None, []
        transition_path = directory / 'transition.json'
        transition = read_frozen(transition_path) or {}
        settling = transition.get('settling')
        if (transition.get('route') != [] or transition.get('environment') != capture['environment']
                or transition.get('error') or transition.get('blocked_requests') != [] or transition.get('native_events') != []
                or not isinstance(settling, list) or len(settling) != 1 or not isinstance(settling[0], dict)
                or settling[0].get('status') != 'quiet'):
            return None, []
        inventory_path = directory / 'inventory.json'
        inventory = read_frozen(inventory_path)
        if not inventory or inventory.get('url') != url:
            return None, []
    except (KeyError, TypeError, ValueError):
        return None, []
    return inventory, [p.relative_to(run).as_posix() for p in (inventory_path, transition_path, manifest_path, receipt_path)]


def inventory_format(node, format_name):
    svg = 'http://www.w3.org/2000/svg'
    html = 'http://www.w3.org/1999/xhtml'
    if format_name == 'inline-svg':
        return node.get('tag') == 'svg' and node.get('namespace') == svg
    if format_name == 'canvas':
        return node.get('tag') == 'canvas' and node.get('namespace') == html
    background = node.get('backgroundImage')
    return isinstance(background, str) and re.fullmatch(r'url\("[^"]+"\)', background) is not None


def css_number(value):
    # Bounding rectangles come from Chromium doubles.
    return type(value) in (int, float) and -2**53 <= value <= 2**53


def geometry_contract(contract):
    return (
        contract['checkpoint'] == '2.5.8-01' and contract['kind'] == 'geometry'
        and set(contract) == {'checkpoint', 'kind', 'targets', 'width', 'height', 'gap', 'page', 'state', 'rationale'}
        and len(contract['targets']) == 2
        and all(css_number(contract[key]) for key in ('width', 'height', 'gap'))
        and contract['width'] > 0 and contract['height'] > 0 and contract['gap'] >= 0
    )


def aligned_gap(first, second):
    # The contract supplies a single edge gap. Restrict it to aligned rows or
    # columns so corners, diagonal distances, and overlap are unambiguous.
    for axis, span, cross, cross_span in (
        ('x', 'width', 'y', 'height'), ('y', 'height', 'x', 'width'),
    ):
        if first[cross] != second[cross] or first[cross_span] != second[cross_span]:
            continue
        start, end = sorted((first, second), key=lambda rect: rect[axis])
        gap = end[axis] - (start[axis] + start[span])
        if gap >= 0:
            return gap, '水平' if axis == 'x' else '垂直'
    return None


def geometry_acquisition(row, contract, nodes, proof):
    fields = ('x', 'y', 'width', 'height')
    measured = []
    for selector in contract['targets']:
        candidates = [node for node in nodes if node.get('selector') == selector]
        if len(candidates) != 1 or candidates[0].get('visible') is not True:
            return dict(row, observed=f'要素一覧で表示された対象 {selector} を一つに絞れない。', evidence=proof)
        rect = candidates[0].get('rect')
        if (not isinstance(rect, dict) or not all(css_number(rect.get(key)) for key in fields)
                or rect['width'] <= 0 or rect['height'] <= 0):
            return dict(row, observed=f'対象 {selector} の矩形を測定できない。', evidence=proof)
        measured.append(dict(target=selector, format='css-rect', rect={key: rect[key] for key in fields}))
    first, second = (item['rect'] for item in measured)
    distance = aligned_gap(first, second)
    if distance is None:
        return dict(row, observed='同じ行又は列に並ぶ、重ならない2つの矩形を確認できない。', evidence=proof)
    gap, direction = distance
    sizes = '、'.join(f'{item["target"]} {item["rect"]["width"]:g} × {item["rect"]["height"]:g}'
                        for item in measured)
    observation = f'矩形 {sizes}。{direction}の辺間隔 {gap:g} CSS px。'
    if gap != contract['gap'] or any(
        (rect['width'], rect['height']) != (contract['width'], contract['height']) for rect in (first, second)
    ):
        wanted = f'期待した両対象の寸法 {contract["width"]:g} × {contract["height"]:g}、辺間隔 {contract["gap"]:g} CSS px。'
        return dict(row, observed=observation + wanted, evidence=proof)
    return dict(row, status='matched', targets=measured, gap=gap, observed=observation, evidence=proof)


def acquisition_result(run, job, progress, contract, frozen, support):
    row = dict(job_id=job['id'], criterion=job['criterion'], mode=job['mode'], page=contract['page'],
               state=contract['state'], checkpoint=contract['checkpoint'], kind=contract['kind'],
               status='deferred' if support == 'no' else 'not_evaluated')
    targets, formats = contract['targets'], contract.get('formats')
    if support == 'no' or row['state'] != 'initial' or not targets or len(set(targets)) != len(targets):
        return row
    geometry = geometry_contract(contract)
    image = (
        row['checkpoint'] == '1.1.1-02' and row['kind'] == 'inventory'
        and set(contract) == {'checkpoint', 'kind', 'targets', 'formats', 'page', 'state', 'rationale'}
        and isinstance(formats, list) and len(formats) == len(targets)
        and all(fmt in ('css-background', 'inline-svg', 'canvas') for fmt in formats)
    )
    if not (geometry or image):
        return row
    inv, proof = initial_inventory(run, job, progress, row['page'], frozen)
    if inv is None:
        return dict(row, observed='同じページの初期状態に対応する保存済み証拠を確認できない。')
    nodes = inv.get('nodes')
    if (inv.get('truncated') is not False or not isinstance(nodes, list) or inv.get('nodeCount') != len(nodes)
            or any(not isinstance(node, dict) for node in nodes)):
        return dict(row, observed='上限や欠落のため完全な要素一覧を確認できない。', evidence=proof)
    if geometry:
        return geometry_acquisition(row, contract, nodes, proof)
    expected = list(zip(targets, formats))
    matched = []
    for target, format_name in expected:
        candidates = [node for node in nodes if node.get('selector') == target]
        if (len(candidates) == 1 and candidates[0].get('visible') is True
                and isinstance(candidates[0].get('tag'), str) and isinstance(candidates[0].get('namespace'), str)
                and inventory_format(candidates[0], format_name)):
            node = candidates[0]
            matched.append(dict(target=target, format=format_name, tag=node['tag'], namespace=node.get('namespace'),
                                background_image=node.get('backgroundImage')))
    if len(matched) < len(expected):
        found = {item['target'] for item in matched}
        missing = '、'.join(f'{target} ({fmt})' for target, fmt in expected if target not in found)
        return dict(row, observed='対象の特定、表示又は形式を確認できない: ' + missing, evidence=proof)
    return dict(row, status='matched', targets=matched, evidence=proof,
                observed='初期状態の要素一覧で全対象と形式を確認した。')


def score(run):
    run=Path(run);meta,progress=verify(run);oracles=oracle_jobs(run);jobs=tasks(run);reviews={}
    index=load(run/'review-index.json') if (run/'review-index.json').exists() else {'entries':[]}
    for name in index['entries']:
        value=load(local(run,name));target=reviews.setdefault(value['job_id'],{})
        for row in value['observations']:target[observation_key(row)]=row
    rows=[];extras=[];pending_evidence=[];matched_evidence=[]
    frozen=load(run/'integrity.json')['files']
    for job in jobs:
        predicted=program_predictions(run,job,progress);predicted.update(reviews.get(job['id'],{}))
        for contract in oracles[job['id']].get('evidence_expectations',[]):
            point=next(p for p in meta['mode_catalog']['checkpoints'] if p['id']==contract['checkpoint'])
            acquisition = acquisition_result(run.resolve(), job, progress, contract, frozen, point['support'][job['mode']])
            (matched_evidence if acquisition['status'] == 'matched' else pending_evidence).append(acquisition)
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
        scorer_digest=digest({"core":file_hash(Path(__file__)),"state_labels":file_hash(Path(state_labels.__file__))}),created_at=timestamp(),selected_checks_status=status,
        overall_status='failed' if status=='failed' else 'incomplete' if grade_counts['not_evaluated'] or grade_counts['deferred'] or pending_evidence else status,
        counts=dict(grade_counts),confusion=dict(confusion),precision_on_evaluated=precision,recall_on_evaluated=recall,
        methods_by_mode={m:dict(Counter(r['method'] for r in rows if r['mode']==m and r['grade'] in {'correct','incorrect'})) for m in meta['modes']},
        detected_known_failures=detected,total_known_failures=total_failures,undetected_known_failures=total_failures-detected,
        rows=rows,unexpected_findings=extras,criteria=all_criteria,pending_evidence_contracts=pending_evidence,
        matched_evidence_contracts=matched_evidence,
        notice_evidence='取得の一致・未確認を別表に記録します。必要な取得期待が残る実行は未完了とします。取得の一致は達成基準の適合判定に含めません。',
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

    def acquisitions(report):
        rows = report.get('matched_evidence_contracts', []) + report.get('pending_evidence_contracts', [])
        return {(r['job_id'], r['page'], r['state'], r['checkpoint'], r['kind']): r['status'] for r in rows}

    old_acquisitions, new_acquisitions = acquisitions(baseline), acquisitions(current)
    if old_acquisitions.keys() != new_acquisitions.keys():
        raise ValueError('比較対象の取得期待が異なる')
    for key, before_status in old_acquisitions.items():
        after_status = new_acquisitions[key]
        change = dict(key=list(key), kind='acquisition', before=before_status, after=after_status)
        if before_status == 'matched' and after_status != 'matched':
            regressions.append(change)
        elif before_status != 'matched' and after_status == 'matched':
            improvements.append(change)
    return dict(status='regressions' if regressions else 'no_regressions',regressions=regressions,improvements=improvements,
                current_quality=current['overall_status'],notice='新しい劣化がないことと、問題集を全て確認できたことは別です。')
