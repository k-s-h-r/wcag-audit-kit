"""Human-readable benchmark grades and empirical mode coverage, never WCAG conformance."""
from collections import Counter
from html import escape
from pathlib import Path
import uuid
from . import core

LABEL={'correct':'正解と一致','incorrect':'正解と不一致','not_evaluated':'未確認','deferred':'モードで省略',
       'passed':'この観点は問題なし','failed':'この観点に問題あり','inapplicable':'この観点の対象外','cant_tell':'判断保留','not_run':'未実施'}
COLS=[('criterion','基準'),('case','ケース'),('mode','モード'),('page','ページ'),('state','状態'),('target','対象'),('checkpoint','確認観点'),
      ('expected','正解'),('actual','検査結果'),('grade','採点'),('method','判定に用いた方法'),('observed','観察'),('rationale','正解の根拠'),('evidence','証拠')]

def write(run,result):
    from workbook import sheet
    from openpyxl import Workbook
    run=Path(run);out=run/'reports'/uuid.uuid4().hex[:12];out.mkdir(parents=True)
    core.save(out/'result.json',result)
    method_labels={'program':'機械','ai':'AI','screen-reader':'実SR'}
    rows=[]
    for r in result['rows']:
        rows.append(dict(r,**{k:LABEL.get(r[k],r[k]) for k in ['expected','actual','grade']},evidence='\n'.join(r['evidence']),mode=core.modes.MODES[r['mode']]['label'],method=method_labels.get(r['method'],'未実施')))
    book=Workbook();book.remove(book.active)
    sheet(book,'採点結果',COLS,rows,True)
    statuses={'failed':'不一致あり','incomplete':'未確認・省略あり','clear_for_selected_checks':'登録した対象観点は採点一致'}
    summary=[dict(item='採点状態',value=statuses[result['selected_checks_status']]),dict(item='全体の状態',value=statuses[result['overall_status']]),
             dict(item='注意',value=result['notice']),dict(item='問題集の版',value=result['corpus_digest']),
             dict(item='全問題の未検出数',value=result['undetected_known_failures'])]
    summary += [dict(item=LABEL.get(k,k),value=v) for k,v in result['counts'].items()]
    method_lines=[]
    for mode,counts in result['methods_by_mode'].items():
        text=core.modes.MODES[mode]['label']+'：'+'、'.join(method_labels[m]+' '+str(counts.get(m,0))+'観点' for m in method_labels)
        method_lines.append(text);summary.append(dict(item='確定結果の方法別件数',value=text))
    sheet(book,'概要',[('item','項目'),('value','内容')],summary,True)
    coverage=[]
    for c in result['criteria']:
        line=dict(c,status={'unprepared':'未整備','not_selected':'今回対象外','prepared':'問題集あり'}[c['status']])
        for mode in result['modes']:
            counts=c['counts'][mode];line[mode]=' / '.join(f'{LABEL.get(k,k)} {v}' for k,v in counts.items()) or '未実行'
        coverage.append(line)
    sheet(book,'基準とモードの実測範囲',[('criterion','基準'),('title','名称'),('level','レベル'),('status','問題集の状態'),
          *[(m,core.modes.MODES[m]['label']) for m in result['modes']]],coverage,True)
    sheet(book,'追加の誤検出',[('criterion','基準'),('mode','モード'),('page','ページ'),('target','対象'),('checkpoint','確認観点'),('observed','観察')],result['unexpected_findings'],True)
    pending=result.get('pending_evidence_contracts',[])
    pending_columns=[('criterion','基準'),('mode','モード'),('page','ページ'),('state','状態'),('checkpoint','取得する観点'),('kind','取得期待の種類'),('status','確認状態')]
    kind_labels={'inventory':'対象の列挙','focus-sequence':'フォーカス経路','viewport':'表示幅と拡大','state-capture':'操作前後の状態','timeline':'時系列の区間','language':'指定言語','accessible-name':'名前と表示ラベル','geometry':'サイズと位置'}
    pending_rows=[dict(r,kind=kind_labels.get(r['kind'],r['kind']),mode=core.modes.MODES[r['mode']]['label'],status=LABEL.get(r['status'],r['status'])) for r in pending]
    if pending:sheet(book,'取得期待の未確認',pending_columns,pending_rows,True)
    book.save(out/'result.xlsx');book.close()
    cells=[]
    for row,original in zip(rows,result['rows']):
        columns=[]
        for k,_ in COLS:
            value=('<br>'.join('<a href="../../'+escape(p,quote=True)+'">'+escape(Path(p).name)+'</a>' for p in original['evidence'])
                   if k=='evidence' else escape(str(row[k])))
            columns.append('<td>'+value+'</td>')
        cells.append('<tr>'+''.join(columns)+'</tr>')
    coverage_rows=[]
    for c in coverage:
        coverage_rows.append('<tr><th scope="row">'+escape(c['criterion'])+'</th><td>'+escape(c['title'])+'</td><td>'+escape(c['status'])+'</td>'+
            ''.join('<td>'+escape(c[m])+'</td>' for m in result['modes'])+'</tr>')
    status={'failed':'不一致あり','incomplete':'必要な確認が未実施','clear_for_selected_checks':'登録した対象観点は採点一致'}[result['selected_checks_status']]
    html='''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>基準別の検出試験</title><style>body{font:16px/1.6 sans-serif;margin:2rem;max-width:100%;}table{border-collapse:collapse;min-width:900px}td,th{border:1px solid #777;padding:.5rem;text-align:left;vertical-align:top}th{background:#edf2f6}.grades{width:2200px;min-width:2200px;table-layout:fixed}.grades td{overflow-wrap:anywhere}.scroll{overflow:auto;max-width:100%}a{color:#0645ad}:focus-visible{outline:3px solid #075da8}</style></head><body><main><h1>基準別の検出試験</h1>'''
    html+='<p>採点状態：'+escape(status)+'</p><p>'+escape(result['notice'])+'</p><p>全問題 '+str(result['total_known_failures'])+'件中、検出 '+str(result['detected_known_failures'])+'件、未検出 '+str(result['undetected_known_failures'])+'件。モードで省くものも未検出の内訳に残します。</p>'
    html+='<p>観点の状態：'+escape(' / '.join(LABEL.get(k,k)+' '+str(v) for k,v in result['counts'].items()))+'</p><p>精度の数値は評価できた観点だけが対象です。未確認・未整備を含む全WCAGの精度とは扱いません。</p>'
    html+='<p>確定結果を得た観点の方法別件数です。判断保留の試行は各行に残し、この件数には含めません。</p><ul>'+''.join('<li>'+escape(line)+'</li>' for line in method_lines)+'</ul>'
    html+='<p><a href="result.json">JSON</a> / <a href="result.xlsx">Excel</a></p><h2>観点ごとの採点</h2><div class="scroll" role="region" aria-label="観点ごとの採点" tabindex="0"><table class="grades"><colgroup>'+''.join('<col style="width:'+str(w)+'px">' for w in [70,60,140,120,140,130,120,140,140,120,100,330,330,160])+'</colgroup><caption>正解・検査結果・未確認を比較</caption><thead><tr>'+''.join('<th scope="col">'+escape(label)+'</th>' for _,label in COLS)+'</tr></thead><tbody>'+''.join(cells)+'</tbody></table></div>'
    html+='<h2>全86基準とモードの実測範囲</h2><div class="scroll" role="region" aria-label="基準とモードの実測範囲" tabindex="0"><table><caption>未整備の基準も表示</caption><thead><tr><th scope="col">基準</th><th scope="col">名称</th><th scope="col">問題集の状態</th>'+''.join('<th scope="col">'+escape(core.modes.MODES[m]['label'])+'</th>' for m in result['modes'])+'</tr></thead><tbody>'+''.join(coverage_rows)+'</tbody></table></div></main></body></html>\n'
    if result['unexpected_findings']:
        extra='<h2>正解にない追加の指摘（誤検出）</h2><ul>'+''.join('<li>'+escape(r['job_id']+' / '+r['page']+' / '+r['target']+' / '+r['observed'])+'</li>' for r in result['unexpected_findings'])+'</ul>'
        html=html.replace('</main>',extra+'</main>')
    if pending:
        pending_html='<h2>取得期待の未確認</h2><p>'+escape(result['notice_evidence'])+'</p><div class="scroll" role="region" aria-label="取得期待の未確認" tabindex="0"><table><caption>判定の適否に含めない取得確認</caption><thead><tr>'+''.join('<th scope="col">'+escape(label)+'</th>' for _,label in pending_columns)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(str(r[k]))+'</td>' for k,_ in pending_columns)+'</tr>' for r in pending_rows)+'</tbody></table></div>'
        html=html.replace('</main>',pending_html+'</main>')
    (out/'result.html').write_text(html)
    core.freeze(run,[p for p in out.iterdir() if p.is_file()])
    return {'json':str(out/'result.json'),'html':str(out/'result.html'),'excel':str(out/'result.xlsx')}
