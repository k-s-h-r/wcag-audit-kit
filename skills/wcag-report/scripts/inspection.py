"""Explicit observation choices; image counts are not LLM token measurements."""
from pathlib import Path

SCREENSHOT_LIMITS = {'off': 0, 'initial': 12, 'states': 12, 'all': 60}
SCREENSHOT_LABELS = {'off': '撮らない', 'initial': '初期表示だけ', 'states': '表示状態ごと', 'all': '操作途中も撮る'}

PROFILES = {
    'quick': {'screenshots':'off','screen_reader':'off','max_images':0},
    'standard': {'screenshots':'states','screen_reader':'optional','max_images':12},
    'thorough': {'screenshots':'all','screen_reader':'required','max_images':60},
}


def policy(value=None):
    if value is None:
        return {'profile':'legacy','screenshots':'all','screen_reader':'optional','max_images':None}
    if not isinstance(value,dict) or set(value)-{'profile','screenshots','screen_reader','max_images'}:
        raise ValueError('inspectionの設定項目が不正')
    name=value.get('profile','standard')
    if name not in PROFILES:raise ValueError('profileはquick、standard、thorough')
    result=dict(PROFILES[name],profile=name);result.update(value)
    if result['screenshots'] not in SCREENSHOT_LIMITS:
        raise ValueError('screenshotsはoff、initial、states、all')
    if 'max_images' not in value:
        result['max_images'] = SCREENSHOT_LIMITS[result['screenshots']]
    if result['screen_reader'] not in {'off','optional','required'}:raise ValueError('screen_readerはoff、optional、required')
    if type(result['max_images']) is not int or not 0<=result['max_images']<=10000:
        raise ValueError('max_imagesは0〜10000')
    return result


class ImageBudget:
    def __init__(self, config, run, manifest, capture):
        self.policy=policy(config.get('inspection'));self.run=Path(run);self.capture_fn=capture
        self.page='';self.environment='';self.counts={}
        self.summary={'policy':self.policy,'screenshots':[],
                      'screen_reader':{'requested':self.policy['screen_reader'],'status':'not_run'}}
        manifest['inspection']=self.summary

    async def capture_with(self, path, kind, callback, *, label=None):
        value={'path':str(Path(path).relative_to(self.run)),'page_id':self.page,'kind':kind}
        if self.environment:
            value['environment'] = self.environment
        if label:
            value['label'] = label
        setting = self.policy['screenshots']
        reason=None
        if setting=='off':reason='screenshots_off'
        elif setting=='initial' and kind!='initial':reason='initial_only'
        elif setting=='states' and kind not in {'initial','state'}:reason='states_only'
        elif self.policy['max_images'] is not None and self.counts.get(self.page,0)>=self.policy['max_images']:reason='image_limit'
        if reason:
            value.update(status='skipped',reason=reason);self.summary['screenshots'].append(value);return False
        self.counts[self.page]=self.counts.get(self.page,0)+1
        value['status']='started';self.summary['screenshots'].append(value)
        try:
            await callback();value['status']='captured';return True
        except Exception:
            value['status']='error';raise

    async def capture(self, page, path, *, kind='detail', label=None, best_effort=False, **kwargs):
        try:
            return await self.capture_with(path, kind, lambda: self.capture_fn(page, path, **kwargs), label=label)
        except Exception:
            if not best_effort:
                raise
            return False


def validate_review(run, value):
    """Validate a human/AI visual survey, not the meaning of an image."""
    import audit
    if not isinstance(value,dict):raise ValueError('操作調査票はJSONオブジェクトにする')
    def strings(value,label):
        if not isinstance(value,list) or any(not isinstance(s,str) or not s.strip() for s in value):
            raise ValueError(label+'は空でない文字列の一覧にする')
        return value
    def observed(value):return isinstance(value,str) and len(value.strip())>=10
    meta,_=audit.run_catalog(run)
    if value.get('config_digest')!=meta['config_digest']:raise ValueError('操作調査票の設定ハッシュが不一致')
    manifest=audit.load(run/'capture-manifest.json');captures={c['key']:c for c in manifest['captures']}
    page_id=value.get('page_id')
    if page_id not in {p['id'] for p in manifest['pages']}:raise ValueError('操作調査票のpage_idが存在しない')
    captures={k:c for k,c in captures.items() if c['page_id']==page_id}
    entries=value.get('captures',[])
    if not isinstance(entries,list) or any(not isinstance(e,dict) for e in entries):raise ValueError('capturesはオブジェクトの一覧にする')
    keys=[e['key'] for e in entries]
    if len(keys)!=len(set(keys)) or not set(keys).issubset(captures):raise ValueError('操作調査票の収集IDが重複又は範囲外')
    paths=[];remaining=[];handoffs=[]
    for entry in entries:
        visual=entry.get('visual',{})
        if not isinstance(visual,dict) or visual.get('status') not in {'reviewed','partial','skipped'} or not observed(visual.get('observed')):
            raise ValueError('画面を実際に見た範囲又は省略の具体的な理由が必要')
        if type(entry.get('states_complete')) is not bool:raise ValueError('states_completeは真偽値')
        evidence=strings(visual.get('evidence',[]),'画像の証拠');paths.extend(evidence)
        if visual['status']=='reviewed' and not any(Path(p).suffix.lower() in {'.png','.jpg','.jpeg','.webp'} for p in evidence):
            raise ValueError('画面確認には実際に観察した画像の証拠が必要')
        own=captures[entry['key']]['evidence_dir']+'/'
        if visual['status']=='reviewed' and not any(p.startswith(own) or p.startswith('evidence/attached/'+entry['key']+'--') for p in evidence):
            raise ValueError('この状態・環境に対応する画像を指定する')
        controls=entry.get('controls',[])
        if not isinstance(controls,list) or any(not isinstance(c,dict) for c in controls):raise ValueError('controlsはオブジェクトの一覧にする')
        strings(entry.get('remaining',[]),'状態の残る確認')
        ids=[c.get('id') for c in controls]
        if any(not isinstance(i,str) or not i for i in ids) or len(ids)!=len(set(ids)):
            raise ValueError('操作対象IDは空でなく重複しないものにする')
        for control in controls:
            if not all(isinstance(control.get(k),str) and control[k].strip() for k in ['label','location','observed']):raise ValueError('見た目のラベル・位置・観察が必要')
            status=control.get('status')
            if status not in {'tested','unverified','human'}:raise ValueError('操作対象の状態が不正')
            paths.extend(strings(control.get('evidence',[]),'操作の証拠'))
            strings(control.get('steps',[]),'実際の操作');strings(control.get('remaining',[]),'対象の残る確認')
            if status=='tested' and (not control.get('steps') or not control.get('evidence')):
                raise ValueError('操作済みには実際の操作と証拠が必要')
            if status!='tested':
                if not control.get('remaining'):raise ValueError('未探索の対象には残る操作を記す')
                remaining.append(entry['key']+'/'+control['id'])
                if status=='human':handoffs.append(entry['key']+'/'+control['id'])
        if entry['states_complete'] and (visual['status']!='reviewed' or any(c['status']!='tested' or c.get('remaining') for c in controls) or entry.get('remaining')):
            raise ValueError('未観察・未探索がある状態を調査完了にできない')
        if not entry['states_complete']:
            if not entry.get('remaining'):raise ValueError('操作調査が未完了なら残る範囲・必要な確認を記す')
            remaining.append(entry['key'])
    remaining.extend(sorted(set(captures)-set(keys)))
    sr=value.get('screen_reader',{})
    if not isinstance(sr,dict) or sr.get('status') not in {'reviewed','partial','skipped'} or not observed(sr.get('observed')):
        raise ValueError('実スクリーンリーダー確認の実施又は省略の記録が必要')
    paths.extend(strings(sr.get('evidence',[]),'実SRの証拠'))
    if sr['status']=='reviewed' and (sr.get('source') not in {'guidepup','native-orca','manual'} or not sr.get('evidence')):
        raise ValueError('実際の読み上げ方法と証拠が必要。ツリーだけを実SR確認にしない')
    requested=policy(meta['config'].get('inspection'))['screen_reader']
    if requested=='required' and sr['status']!='reviewed':remaining.append('screen_reader')
    return {'complete':bool(captures) and not remaining,'remaining':remaining,'human_controls':handoffs,
            'verified_evidence':[audit.evidence_item(run,p) for p in dict.fromkeys(paths)]}


def review_status(run):
    import audit
    meta,_=audit.run_catalog(run)
    required=bool(meta['config'].get('inspection'))
    pointers=audit.run_plan(run).get('interaction_reviews',{})
    if not pointers:return {'required':required,'complete':not required,'status':'not_recorded','remaining':[],'pages':{}}
    manifest=audit.load(run/'capture-manifest.json')
    if not isinstance(pointers,dict) or not set(pointers).issubset({p['id'] for p in manifest['pages']}):
        raise ValueError('操作調査票のページ対応が不正')
    pages={};remaining=[]
    for page in manifest['pages']:
        ident=page['id']
        if ident not in pointers:remaining.append(ident);continue
        path=(run/pointers[ident]).resolve()
        if not path.is_relative_to(run.resolve()):raise ValueError('操作調査票はrun内に保存する')
        value=audit.load(path);checked=validate_review(run,value)
        if value['page_id']!=ident or checked['verified_evidence']!=value.get('verified_evidence'):
            raise ValueError('操作調査票の対応又は画像・操作証拠が変更された')
        pages[ident]=dict(checked,screen_reader=value['screen_reader'],path=pointers[ident],
                          captures=value['captures'],url=page['url'])
        remaining.extend(checked['remaining'])
    complete=bool(pages) and not remaining
    return {'required':required,'complete':complete,'status':'reviewed' if complete else 'partial','remaining':remaining,'pages':pages}


def report_rows(result):
    rows=[]
    for page_id,page in result['interaction_review'].get('pages',{}).items():
        for capture in page['captures']:
            for control in capture.get('controls',[]) or [{}]:
                rows.append({'page_id':page_id,'url':page['url'],'capture':capture['key'],
                    'visual':capture['visual']['status'],'label':control.get('label',''),
                    'location':control.get('location',''),'status':control.get('status','unverified'),
                    'observed':control.get('observed',capture['visual']['observed']),
                    'steps':'\n'.join(control.get('steps',[])),
                    'remaining':'\n'.join(control.get('remaining',[])+capture.get('remaining',[])),
                    'screen_reader':page['screen_reader']['status'],'source_review':page['path']})
    return rows
