"""Index recorded demonstrations without treating absence or a handoff as a pass."""
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import audit


def build():
    policy=audit.load(ROOT/'references/method-capabilities.json')
    capabilities={x['method']:x for x in policy['methods']}
    required={m for c in audit.CATALOG['criteria'] for m in c['methods']}
    if set(capabilities)!=required:raise ValueError('観察方法の方針に過不足がある')
    for value in capabilities.values():
        for path in value['evidence']:
            if not (ROOT/path).is_file():raise ValueError('方法の証拠がない: '+path)
    current={c['id']:c for c in audit.CATALOG['criteria']}
    evidence={key:[] for key in current}
    runs=[]
    for meta_path in sorted((ROOT/'validation').rglob('run.json')):
        run=meta_path.parent
        if not (run/'plan.json').exists():continue
        result=audit.outcomes(run)
        _,catalog=audit.run_catalog(run)
        definitions={c['id']:c for c in catalog['criteria']}
        runs.append({'path':str(run.relative_to(ROOT)),'counts':result['counts'],
                     'audit_complete':result['audit_complete']})
        for case in result['cases']:
            record=case['assessment_data']
            if record is None:continue
            match=audit.digest(definitions[case['criterion']])==audit.digest(current[case['criterion']])
            evidence[case['criterion']].append({'run':str(run.relative_to(ROOT)),
                'case_id':case['case_id'],'assessment':str((run/case['assessment']).relative_to(ROOT)),
                'outcome':record['outcome'],'execution':record['execution'],
                'coverage_complete':record.get('coverage_complete') is True,
                'current_procedure':match,'human_handoff':bool(record.get('human_handoff'))})
    rows=[]
    labels={'both_examples':'通過例・不適合例を記録','pass_example':'通過例を記録',
        'fail_example':'不適合例を記録','absence_only':'対象外の確認のみ',
        'human_handoff':'人への引き継ぎを記録','unresolved':'判断保留の記録のみ','not_demonstrated':'実対象で未実証'}
    for criterion in audit.CATALOG['criteria']:
        ident=criterion['id'];records=evidence[ident]
        valid=[r for r in records if r['current_procedure']]
        counts=Counter(r['outcome'] for r in valid)
        handoffs=sum(r['human_handoff'] for r in valid)
        passed=any(r['outcome']=='passed' and r['execution']=='completed' and r['coverage_complete'] for r in valid)
        failed=any(r['outcome']=='failed' and r['execution']=='completed' for r in valid)
        status=('both_examples' if passed and failed else 'pass_example' if passed else 'fail_example' if failed else
                'human_handoff' if handoffs else 'unresolved' if counts['cant_tell'] else 'absence_only' if counts['inapplicable'] else 'not_demonstrated')
        for path in ['references/criteria/'+ident+'.md','references/sources/'+ident+'.md','references/tests/'+ident+'.md']:
            if not (ROOT/path).is_file():raise ValueError('基準の手順・原典・公開Testsがない: '+ident)
        rows.append({'id':ident,'title':criterion['title'],'level':criterion['level'],
            'procedure_version':criterion['procedure_version'],'procedure_documented':True,
            'demonstration':status,'current_procedure_counts':dict(counts),
            'human_handoff_cases':handoffs,'older_procedure_cases':len(records)-len(valid),
            'methods':[{key:capabilities[m][key] for key in ['method','status','limits','evidence']} for m in criterion['methods']],
            'records':records})
    output={'note':'この版の手順に一致する記録の有無。既知の例による校正を含み、基準全体・任意の対象への精度保証ではない。対象外だけの記録を実対象の通過へ数えない。',
            'method_policy_version':policy['policy_version'],'criteria':rows,'runs':runs}
    audit.save(ROOT/'validation/coverage.json',output)
    lines=['# 達成基準ごとの手順と実証状況','',output['note'],'',
        '全86基準の本文・検査手順・公開Testsを収録している。以下は基準ごとの実対象を検査した記録の一覧。',
        '未実証や部分的な方法は、対象サイトで方法を調査して試す。信頼できる観察ができない場合は[人への引き継ぎ](human-review.md)を作る。',
        '元のcase、手順の版、結果、証拠への索引は[JSON](../validation/coverage.json)に保存している。',
        'この表で基準の検査済み範囲を推測せず、各記録の具体的な対象・条件・未確認を読む。','',
        '| 基準 | レベル | 手順版 | この版での実証記録 | 人へ引継ぎ |',
        '| --- | --- | --- | --- | ---: |']
    for row in rows:
        lines.append('| ['+row['id']+' '+row['title']+'](criteria/'+row['id']+'.md) | '+row['level']+' | '+row['procedure_version']+' | '+labels[row['demonstration']]+' | '+str(row['human_handoff_cases'])+' |')
    lines += ['','## 観察方法の準備状況','',
        'boundedは限定した例での実行確認、partialは一部の観察のみ、project_verificationは対象での方法の試行が必要、humanは現在の環境では人への引き継ぎを準備する方法。いずれも対象サイトの適合判定ではない。','',
        '| 方法 | 状況 | 確認範囲と限界 |','| --- | --- | --- |']
    for m in capabilities.values():lines.append('| '+m['method']+' | '+m['status']+' | '+m['limits']+' |')
    (ROOT/'references/VERIFICATION-COVERAGE.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'criteria':len(rows),'methods':len(capabilities),'runs':len(runs),
        'demonstrations':dict(Counter(x['demonstration'] for x in rows))},ensure_ascii=False))


if __name__=='__main__':build()
