"""Selectable verification capabilities. Availability is never a WCAG verdict."""
from collections import Counter
from copy import deepcopy
from html import escape
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[1]
SYMBOLS={'yes':'○','partial':'△','no':'×'}
SR_LABELS={'recorded':'実施記録あり','partial':'一部実施','not_run':'未実施','disabled':'このモードでは使用しない'}
LEGEND='○：この確認観点の検査手段あり。△：一部の検査・証拠取得まで。×：このモードでは確認しない、又は信頼できる手段が未整備。対象ページの合否や検査済みを表す記号ではありません。'
MODES={
 'machine':{'label':'機械チェックのみ','ai':False,'screen_reader':False,'profile':'quick'},
 'ai':{'label':'AI併用','ai':True,'screen_reader':False,'profile':'standard'},
 'screen-reader':{'label':'スクリーンリーダー併用','ai':False,'screen_reader':True,'profile':'quick'},
 'full':{'label':'AI＋スクリーンリーダー','ai':True,'screen_reader':True,'profile':'thorough'},
}
COVERAGE_COLUMNS = [
    ('id', '確認観点ID'), ('criterion', '基準'), ('title', '名称'), ('level', 'レベル'),
    ('check', '確認観点'), ('machine', '機械のみ'), ('ai', 'AI併用'),
    ('screen-reader', 'SR併用'), ('full', 'AI＋SR'), ('mode', '選択モード'),
    ('selected', '選択モードの対応'), ('target_level', '目標レベル'),
    ('note', '制約'), ('preparation', '必要な準備'),
]
IMAGE_COUNTS = {'captured': '保存', 'skipped': '省略', 'error': '取得エラー', 'started': '処理中'}


def policy(value):
    if not isinstance(value,dict) or set(value)!={'mode'} or not isinstance(value['mode'],str) or value['mode'] not in MODES:
        raise ValueError('verificationはmodeのみ指定する。modeはmachine、ai、screen-reader、full')
    return {'mode':value['mode']}


def configure(config):
    """Validate explicit modes; absent modes preserve legacy configuration exactly."""
    if 'verification' not in config:return config
    from inspection import policy as inspection_policy
    config['verification']=policy(config['verification']);mode=MODES[config['verification']['mode']]
    choice={'profile':mode['profile']}
    choice.update(config.get('inspection',{}))
    # The mode controls SR use independently of the image-depth profile.
    choice.setdefault('screen_reader','required' if mode['screen_reader'] else 'off')
    p=inspection_policy(choice)
    if (p['screenshots'] == 'off') != (p['max_images'] == 0):
        raise ValueError('撮影しない場合はmax_images=0、撮影する場合はmax_imagesを1以上にする')
    expected='required' if mode['screen_reader'] else 'off'
    if p['screen_reader']!=expected:
        raise ValueError('選択モードとscreen_readerの設定が矛盾している。SR併用はrequired、それ以外はoff')
    config['inspection']=p
    return config


def select(config, name, *, profile=None, screenshots=None, screen_reader=None, max_images=None):
    """An explicit CLI mode chooses its own defaults, then applies explicit overrides."""
    mode=MODES[policy({'mode':name})['mode']]
    config['verification']={'mode':name}
    choice={'profile':profile or mode['profile'],'screen_reader':'required' if mode['screen_reader'] else 'off'}
    for key,value in [('screenshots',screenshots),('screen_reader',screen_reader),('max_images',max_images)]:
        if value is not None:choice[key]=value
    config['inspection']=choice
    return configure(config)


def catalog():
    return json.loads((ROOT/'references/verification-checkpoints.json').read_text())


def validate_catalog(value):
    import audit
    if value.get('schema_version')!='1' or not isinstance(value.get('checkpoints'),list):
        raise ValueError('モード検査定義の形式が不正')
    rows=value['checkpoints'];ids=[r['id'] for r in rows]
    if len(ids)!=len(set(ids)) or not rows:raise ValueError('モードの確認観点IDが重複又は空')
    for row in rows:
        c=audit.CRITERIA.get(row['criterion'])
        if c is None or (row['title'],row['level'])!=(c['title'],c['level']):raise ValueError('モード定義とWCAGカタログが不一致')
        if set(row['support'])!=set(MODES) or any(v not in SYMBOLS for v in row['support'].values()):raise ValueError('モード対応の記号が不正')
        if row['execution'] not in {'standard','configured','review','unavailable'}:raise ValueError('モード検査の実行方法が不正')
        if not all(isinstance(row.get(k),str) and row[k].strip() for k in ['id','check','program','preparation','ai','human','note']):
            raise ValueError('モード検査の具体的な説明が必要')
    if list(dict.fromkeys(r['criterion'] for r in rows))!=list(audit.CRITERIA):raise ValueError('モード定義に基準の漏れ・順序違い')
    return value


def snapshot(run, meta):
    """Called only for new runs, never retrofit definitions onto old results."""
    import audit
    if 'verification' not in meta['config']:return
    value=validate_catalog(catalog());meta['verification_digest']=audit.digest(value)
    audit.save(run/'verification.snapshot.json',value)


def run_catalog(run):
    import audit
    meta=audit.run_meta(run)
    if 'verification' not in meta['config']:return None
    value=audit.load(run/'verification.snapshot.json')
    if audit.digest(value)!=meta.get('verification_digest'):
        raise ValueError('保存したモード検査定義のスナップショットが変更された')
    # Use the saved version, even after the installed availability matrix changes.
    return value


def coverage(value, name, level='AAA'):
    import audit
    policy({'mode':name})
    return [dict(deepcopy(row),selected_support=row['support'][name],symbol=SYMBOLS[row['support'][name]],
                 target_level=row['level'] in audit.LEVELS[level],verification_status='not_evaluated')
            for row in value['checkpoints']]


def summary(run, result=None):
    import audit
    meta=audit.run_meta(run);value=run_catalog(run)
    if value is None:return None
    name=policy(meta['config']['verification'])['mode'];mode=MODES[name]
    rows=coverage(value,name,meta['config']['level'])
    sr_pages=(result or {}).get('interaction_review',{}).get('pages',{})
    expected={c['page_id'] for c in (result or {}).get('cases',[])}
    recorded={k for k,p in sr_pages.items() if k in expected and p['screen_reader']['status']=='reviewed'}
    sr_recorded=bool(expected) and expected.issubset(recorded)
    observations = (result or {}).get('observation_usage', {}).get('screenshots')
    image_counts = None if observations is None else dict(Counter(item['status'] for item in observations))
    checks = (result or {}).get('machine_checks')
    # Requested capability is distinct from observed output. No inferred AI usage.
    return {'mode':name,'label':mode['label'],'ai_allowed':mode['ai'],'screen_reader_required':mode['screen_reader'],
            'screen_reader_status':('recorded' if sr_recorded else 'partial' if recorded else 'not_run') if mode['screen_reader'] else 'disabled',
            'ai_usage':'not_inferred_from_mode','legend':LEGEND,'definition_digest':meta['verification_digest'],
            'counts':dict(Counter(r['selected_support'] for r in rows if r['target_level'])),
            'evidence_summary': {'machine_rows': None if checks is None else len(checks), 'images': image_counts},
            'checkpoints':rows,'notice':'対応表は実行可能な方法の範囲です。○も実行前は未確認です。×・省略・環境不足をWCAGの対象外や適合にしません。'}


def plain(value):
    return re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',str(value)).replace('`','')


def table_rows(value):
    return [dict(id=r['id'],criterion=r['criterion'],title=r['title'],level=r['level'],check=r['check'],
                 selected=r['symbol'],mode=value['label'],target_level='対象' if r['target_level'] else '目標レベル外',
                 **{m:SYMBOLS[r['support'][m]] for m in MODES},note=plain(r['note']),preparation=plain(r['preparation']))
            for r in value['checkpoints']]


def report_summary_rows(value):
    """Identical labels for the report-scope counts in HTML and Excel."""
    evidence = value.get('evidence_summary', {})
    machine = evidence.get('machine_rows')
    images = evidence.get('images')
    return [
        ('対象レベルの対応内訳', ' / '.join(f'{symbol} {value["counts"].get(key, 0)}観点'
                                      for key, symbol in SYMBOLS.items())),
        ('機械検査の記録行', '記録なし' if machine is None else f'{machine}件'),
        ('画像の取得記録', '記録なし' if images is None else ' / '.join(
            f'{label} {images.get(key, 0)}件' for key, label in IMAGE_COUNTS.items())),
        ('AIの内容判断', '実施状況は判定の記録を確認' if value['ai_allowed'] else 'このモードでは使用しない'),
        ('実スクリーンリーダーの記録', SR_LABELS[value['screen_reader_status']]),
    ]


def work_checkpoint(row, name):
    mode=MODES[name]
    item={k:row[k] for k in ['id','criterion','check','program','preparation','selected_support','symbol','note']}
    item['ai_instruction']=row['ai'] if mode['ai'] else None
    item['screen_reader_allowed']=mode['screen_reader']
    item['limit']='未実行。実行した部分の証拠を記録し、対応表の○を適合として記録しない。'
    if row['selected_support']=='partial' and not mode['ai']:
        item['limit']+='プログラムで取得・検査できた部分だけを扱い、意味・見た目の判断は未確認に残す。'
    return item


def render_html(value):
    if value is None:return ''
    rows=[]
    for row in table_rows(value):
        cells=['<th scope="row" style="white-space:nowrap">'+escape(row['id'])+'</th>']
        for key,_ in COVERAGE_COLUMNS[1:]:
            style=' style="white-space:nowrap;text-align:center"' if key in {*MODES,'selected'} else ''
            cells.append('<td'+style+'>'+escape(str(row[key]))+'</td>')
        rows.append('<tr>'+''.join(cells)+'</tr>')
    execution = ''.join('<p>'+escape(label)+'：'+escape(record)+'</p>'
                        for label, record in report_summary_rows(value))
    return ('<section aria-labelledby="verification-mode"><h2 id="verification-mode">選択した検証モード：'+escape(value['label'])+'</h2>'
            '<p>'+escape(value['legend'])+'</p><p>'+escape(value['notice'])+'</p>'+execution+
            '<div role="region" aria-label="モード別の確認範囲" tabindex="0" style="max-width:100%;overflow-x:auto"><table style="min-width:1000px"><caption>モード別の確認範囲。実行結果は達成基準チェックシートを参照</caption><thead><tr>'
            +''.join('<th scope="col" style="white-space:nowrap">'+escape(label)+'</th>' for _,label in COVERAGE_COLUMNS)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></section>')
