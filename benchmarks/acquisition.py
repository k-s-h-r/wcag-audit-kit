"""One acquisition contract, independently of WCAG verdicts."""
from pathlib import Path

METHOD='visible-css-url-svg-canvas-v1'
FORMATS={'css-background','inline-svg','canvas'}


def assess(run,job,progress,contract):
    from . import core
    if contract['checkpoint']!='1.1.1-02' or contract['kind']!='inventory' or contract['state']!='initial':return None
    result=dict(status='not_evaluated',evidence=[],expected_targets=contract['targets'],actual_targets=[],
        observed='対応する完全な候補一覧の証拠がありません。',method=METHOD)
    receipt=progress['jobs'].get(job['id'],{}).get(contract['page'],{})
    if receipt.get('status')!='completed':return result
    root=core.local(run,receipt['directory']);graph=core.load(root/'exploration.json')
    nodes=[n for n in graph.get('nodes',[]) if not n['route']]
    if len(nodes)!=1:return dict(result,observed='対象状態の証拠が一意ではありません。')
    path=core.local(root,nodes[0]['evidence_dir']+'/state.json')
    if not path.is_file():return result
    value=core.load(path);coverage=value.get('candidate_collection');items=value.get('visual_candidates')
    result['evidence']=[path.relative_to(Path(run).resolve()).as_posix()]
    if not isinstance(coverage,dict) or coverage.get('method')!=METHOD or coverage.get('complete') is not True or not isinstance(items,list):return result
    actual={}
    for item in items:
        if not isinstance(item,dict) or not isinstance(item.get('selector'),str) or not item['selector'] or item['selector'] in actual or not isinstance(item.get('formats'),list) or not item['formats'] or any(not isinstance(f,str) or f not in FORMATS for f in item['formats']):
            return dict(result,observed='候補一覧の形式又は対象の一意性が不正です。')
        actual[item['selector']]=item['formats']
    result['actual_targets']=sorted(actual)
    unsupported=set(contract)-{'checkpoint','kind','targets','formats','page','state','rationale','empty_is_expected'}
    if unsupported:return dict(result,observed='未対応の取得条件：'+', '.join(sorted(unsupported))+'。候補の目的等をこの機械照合で確定しない。')
    targets=contract['targets'];formats=contract.get('formats')
    if formats is None:return dict(result,observed='対応形式を指定した取得条件がないため、候補一覧の全条件を確定しない。')
    if (not isinstance(formats,list) or len(formats)!=len(targets) or any(not isinstance(f,str) or f not in FORMATS for f in formats)):
        return dict(result,observed='この照合方法で扱えない形式の期待結果です。')
    missing=sorted(set(targets)-set(actual));unexpected=sorted(set(actual)-set(targets))
    wrong_formats=[target for target,fmt in zip(targets,formats or []) if target in actual and fmt not in actual[target]]
    return dict(result,status='mismatch' if missing or unexpected or wrong_formats else 'matched',actual_targets=sorted(actual),
        missing=missing,unexpected=unexpected,wrong_formats=wrong_formats,
        observed='候補の対象・対応形式を照合した。意味・装飾の目的・代替の適否は判定していない。',
        supported_fields=['targets','formats'])
