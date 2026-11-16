#!/usr/bin/env python3
"""Build the authored-input coverage index. This does not run a WCAG detector."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks import core

REQUIRED_FAMILIES={
    'background-svg-canvas','reader-alternative','reader-structure','transcript-meaning','caption-meaning-timing',
    'live-content','description-selection','description-meaning','sign-meaning','extended-description',
    'physical-orientation','physical-motion','late-image','shadow-disclosure','nested-dialog','combobox-popup',
    'tab-panels','iframe-trap','offcanvas-hidden-focus','late-fixed-banner','colour-error-state','disabled-then-enabled',
    'target-geometry','focus-route-inventory','time-extension','long-retention','background-level',
    'cognitive-alternative','object-recognition-difference','radio-group',
}


def build():
    corpus=core.corpus();points=core.modes.catalog()['checkpoints'];coverage=core.case_contracts.coverage(corpus,points)
    suites={s['criterion']:s for s in corpus['suites']};patterns={};rows=[]
    for sc,suite in suites.items():
        for case in suite['cases']:
            if case.get('pattern'):
                value=patterns.setdefault(case['pattern'],dict(id=case['pattern'],criterion=sc,name=case['pattern_name'],cases=[]))
                value['cases'].append(dict(id=case['id'],pages=case['pages'],states=[s['id'] for s in case['states']],
                    verdicts=[dict(checkpoint=e['checkpoint'],expected=e['expected']) for e in case['expectations']],
                    acquisition=[e['checkpoint'] for e in case.get('evidence_expectations',[])],
                    requires_environment=case.get('requires_environment',[]),has_browser_probe=bool(case.get('fixture_probe'))))
    for p in points:
        refs=[]
        for case in suites[p['criterion']]['cases']:
            kinds=[]
            if any(e['checkpoint']==p['id'] for e in case['expectations']):kinds.append('verdict')
            if any(e['checkpoint']==p['id'] for e in case.get('evidence_expectations',[])):kinds.append('acquisition')
            if kinds:refs.append(dict(case=case['id'],pages=case['pages'],expectation_types=kinds))
        rows.append(dict(checkpoint=p['id'],criterion=p['criterion'],check=p['check'],cases=refs))
    families={p.split('.',3)[-1] for p in patterns}
    index=dict(schema_version='1',scope='authored test inputs; not detector success or exhaustive WCAG patterns',
        corpus_digest=corpus['digest'],summary=dict(criteria=len(suites),cases=sum(len(s['cases']) for s in suites.values()),
            page_entries=sum(len(c['pages']) for s in suites.values() for c in s['cases']),
            verdict_rows=sum(len(c['expectations']) for s in suites.values() for c in s['cases']),
            acquisition_rows=sum(len(c.get('evidence_expectations',[])) for s in suites.values() for c in s['cases']),
            verdict_checkpoints=len(coverage['verdict']),acquisition_checkpoints=len(coverage['acquisition']),
            registered_checkpoints=len(coverage['registered']),pattern_groups=len(patterns)),
        missing_checkpoints=coverage['missing'],required_families=sorted(REQUIRED_FAMILIES),
        missing_families=sorted(REQUIRED_FAMILIES-families),checkpoints=rows,patterns=list(patterns.values()))
    n=index['summary']
    lines=['# テストページの収録範囲','',
        f"全86達成基準・131確認観点にテスト入力を用意しています。{n['cases']}ケース・{n['page_entries']}ページ分の入力があり、判定の期待結果{n['verdict_rows']}行と取得の期待結果{n['acquisition_rows']}行を分けています。",'',
        f"131観点の内訳は判定{n['verdict_checkpoints']}・取得{n['acquisition_checkpoints']}です。取得する対象・読み順・寸法・状態を、適合・不適合へ読み替えません。取得期待の自動照合は未接続で、結果は未確認の別表へ残します。",'',
        'これは有限の入力と作成者による期待結果の一覧です。検出器が正解した数、全てのWCAGパターンの網羅、独立した専門家による確認を示すものではありません。','',
        '[追加パターンの一覧](PATTERNS.md) / [3階層メニューの操作手順](NESTED-NAVIGATION.md) / [機械向け一覧](fixture-index.json)','',
        '| 基準 | 対照例 | 判定の期待結果がある観点 | 取得の期待結果がある観点 | 未収録の観点 |',
        '| --- | --- | --- | --- | --- |']
    for sc,suite in suites.items():
        verdict=sorted({e['checkpoint'] for c in suite['cases'] for e in c['expectations']})
        acquisition=sorted({e['checkpoint'] for c in suite['cases'] for e in c.get('evidence_expectations',[])})
        missing=sorted({p['id'] for p in points if p['criterion']==sc}-set(verdict)-set(acquisition))
        control='問題例と問題なしの対照' if any(e['expected']=='passed' for c in suite['cases'] for e in c['expectations']) else '適合正例は未整備'
        lines.append(f'| [{sc}](cases/{sc}/README.md) | {control} | '+', '.join(verdict)+' | '+(', '.join(acquisition) or '―')+' | '+(', '.join(missing) or 'なし（観点単位）')+' |')
    matrix=['# 追加パターンの一覧','',
        f"{n['pattern_groups']}組の追加パターンです。各ページの状態・期待結果・必要環境はsuite.jsonへ記録しています。元の代表例と3階層メニューも保持しています。",'',
        '問題なしの対照も含め、適合の結論は記載した観点と条件に限ります。手話の意味は公開元の説明、音声は既知の生成元を根拠にしており、独立した専門家の確認は未実施です。仮想時計・合成センサー・文字サイズ上書きの試験を、実時間・実端末・ネイティブのズームの確認へ置き換えません。','',
        '| パターン | 基準 | ケースとページ | 必要な追加環境 |','| --- | --- | --- | --- |']
    for pattern in patterns.values():
        sc=pattern['criterion'];refs=[];env=set()
        for c in pattern['cases']:
            refs+=['['+c['id']+': '+p+'](cases/'+sc+'/public/'+p+')' for p in c['pages']]
            env.update(c['requires_environment'])
        matrix.append('| '+pattern['name']+' | '+sc+' | '+' / '.join(refs)+' | '+(', '.join(sorted(env)) or '通常のブラウザー')+' |')
    return {'fixture-index.json':json.dumps(index,ensure_ascii=False,indent=2)+'\n','COVERAGE.md':'\n'.join(lines)+'\n','PATTERNS.md':'\n'.join(matrix)+'\n'},index


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    outputs,index=build()
    if index['missing_checkpoints'] or index['missing_families']:raise SystemExit('Test input matrix is incomplete')
    for name,content in outputs.items():
        path=core.ROOT/'benchmarks'/name
        if args.check:
            if not path.exists() or path.read_text()!=content:raise SystemExit('Regenerate benchmark index: '+name)
        else:path.write_text(content)
    print(json.dumps(index['summary'],ensure_ascii=False))


if __name__=='__main__':main()
