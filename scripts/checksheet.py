"""Read-only Japanese check sheets derived from the existing assessment ledger."""
from collections import Counter, defaultdict
from html import escape
from urllib.parse import quote

from work_queue import unfinished


COLUMNS = [('criterion','達成基準'),('title','達成基準名'),('level','レベル'),
           ('checkpoint','確認観点'),('applicability','適用'),('judgment','適合'),
           ('locations','不適合箇所'),('notes','確認結果・注記'),
           ('remaining','残る確認'),('evidence','証拠・判定記録')]
FAILURE_COLUMNS = [('id','箇所ID'),('criterion','達成基準'),('checkpoint','確認観点'),
                   ('page_url','ページURL'),('state','ページ状態'),('environment','環境'),
                   ('target','対象要素・位置'),('observed','観察結果'),('expected','期待結果'),
                   ('steps','再現手順'),('remaining','同じ検査票の残る確認'),('evidence','証拠・判定記録')]
LEGEND = ('○ 適合 / × 不適合 / — 非適用 / 未確認 / 目標レベル外。適用は「あり・なし・未確認」で表示。'
          '非適用は根拠を記録した場合だけに使い、未実施と区別します。')
GUIDANCE = ('「基準全体」は出力範囲の集計です。確認観点の内訳は、対象ごとの期待結果が同じ記録をまとめます。'
            '内訳の適合は記録した対象に限り、観点や基準全体を網羅した意味にはなりません。'
            '不適合と未確認は併記します。この表だけでサイト全体の適合やJIS準拠を宣言しません。')
STATUS = {'passed':'○ 適合','failed':'× 不適合','inapplicable':'— 非適用',
          'unverified':'未確認','out_of_target_level':'目標レベル外'}
OUTCOME = {'passed':'適合','failed':'不適合','inapplicable':'非適用','cant_tell':'判断保留','not_run':'未実施'}


def unique(values):
    return list(dict.fromkeys(v for v in values if v))


def preview(values, limit=3, destination='検査票・判定記録'):
    values=unique(values)
    return '\n'.join(values[:limit]+([f'ほか{len(values)-limit}件は{destination}を参照。'] if len(values)>limit else []))


def context(case):
    return f"{case['page_url']} / {case['state']} / {case['environment']}"


def verdict(outcomes, pending=False):
    if 'failed' in outcomes:return 'failed'
    if pending or not outcomes or any(o in {'not_run','cant_tell'} for o in outcomes):return 'unverified'
    if all(o=='inapplicable' for o in outcomes):return 'inapplicable'
    return 'passed'


def applicable(outcomes, status):
    if status=='out_of_target_level':return '目標レベル外'
    if any(o in {'passed','failed'} for o in outcomes):return 'あり'
    if status=='inapplicable':return 'なし'
    return '未確認'


def scope_gaps(result, criterion, filters, manifest):
    # Tasks/owners/pending are explicitly a selection of existing cases, not an
    # assertion about absent cases or the rest of the page/site.
    if filters.get('task') or filters.get('owner') is not None or filters.get('pending'):
        return []
    def matches(url):
        if filters.get('page') and filters['page'] not in url:return False
        if filters.get('page_exact'):
            from browser_capture import normalize
            return normalize(url)==normalize(filters['page_exact'])
        return True
    page_filtered=bool(filters.get('page') or filters.get('page_exact'))
    gaps=[f"未収集：{c['url']} / {c['state']} / {c['environment']}"
          for c in result['missing_captures'] if matches(c['url'])]
    captures={c['key']:c['url'] for c in manifest.get('captures',[])}
    for case_id in result['missing_cases']:
        key,sc=case_id.rsplit('--',1)
        if sc==criterion and (not page_filtered or key not in captures or matches(captures[key])):
            gaps.append('検査票が未作成：'+case_id)
    for item in result['unvisited']:
        url=item.get('url','') if isinstance(item,dict) else item
        if matches(url):gaps.append('未訪問：'+str(url))
    if not page_filtered:
        if not result['collection_complete']:gaps.append('収集が未完了。未収集の範囲を確認する。')
        if result['declared_states_without_page']:gaps.append('対象ページがない宣言済み状態を確認する。')
    return gaps


def build(result, catalog, *, cases=None, filters=None, manifest=None):
    """No writes, inferred passes, or changes to the machine interchange schema."""
    cases=result['cases'] if cases is None else cases
    filters=filters or {};manifest=manifest or {}
    restricted=bool(filters.get('task') or filters.get('owner') is not None or filters.get('pending'))
    ids={c['criterion'] for c in cases}
    criteria=[c for c in result['criteria'] if (not filters.get('criterion') or c['id']==filters['criterion'])
              and (not restricted or c['id'] in ids)]
    definitions={c['id']:c for c in catalog['criteria']}
    grouped=defaultdict(list)
    for case in cases:grouped[case['criterion']].append(case)
    rows=[];failures=[]
    for criterion in criteria:
        sc=criterion['id'];selected=grouped[sc];points=defaultdict(list);sc_failures=[]
        for case in selected:
            a=case['assessment_data'] or {}
            for target in a.get('targets',[]):
                points[target['expected']].append((case,target))
                if target['outcome']!='failed':continue
                ident=f'F{len(failures)+1:05d}'
                evidence=unique(target.get('evidence',[])+[case['assessment']])
                failure=dict(id=ident,criterion=sc,checkpoint=target['expected'],page_url=case['page_url'],
                    state=case['state'],environment=case['environment'],target=target['target'],
                    observed=target['observed'],expected=target['expected'],steps='\n'.join(a.get('steps_executed',[])),
                    remaining='\n'.join(a.get('remaining',[])),evidence='\n'.join(evidence),evidence_paths=evidence)
                failures.append(failure);sc_failures.append(failure)
        outcomes=[c['outcome'] for c in selected]
        gaps=scope_gaps(result,sc,filters,manifest)
        pending=[c for c in selected if unfinished(c)]
        state=('out_of_target_level' if criterion['status']=='out_of_target_level' else
               verdict(outcomes,bool(pending or gaps)))
        if state=='out_of_target_level':gaps=[];pending=[]
        remaining=[]
        for case in pending:
            a=case['assessment_data'] or {}
            reasons=a.get('remaining',[]) or [
                '未実施。対象を列挙し、条件・例外・必要な観察方法を検査する。' if not a else
                '判断・対象の網羅又は必要な観察が未完了。判定記録を確認する。']
            remaining.extend(context(case)+'：'+reason for reason in reasons)
        if not selected and state!='out_of_target_level':remaining.append('この基準の検査票・判定がありません。')
        remaining+=gaps
        evidence=unique(c['assessment'] for c in selected)
        counts=Counter(outcomes)
        notes='、'.join(f'{OUTCOME[k]} {n}票' for k,n in counts.items()) or '検査票なし'
        if pending or gaps:notes+='。未確認あり。'
        if state=='inapplicable':
            notes+='。非適用の根拠：'+preview([(c['assessment_data'] or {}).get('observed','') for c in selected],2)
        base=dict(criterion=sc,title=criterion['title'],level=criterion['level'])
        def row(checkpoint,status,values,locations,notes,remaining,evidence,kind):
            judgment=STATUS[status]
            if kind=='criterion' and status=='failed' and remaining:judgment+='\n未確認あり'
            return dict(base,checkpoint=checkpoint,status=status,kind=kind,
                applicability=applicable(values,status),judgment=judgment,
                locations=preview([f"{f['id']} {f['page_url']} / {f['state']} / {f['environment']} / {f['target']}" for f in locations],
                                  destination='不適合箇所の一覧'),failure_ids=[f['id'] for f in locations],
                notes=notes,remaining=remaining,evidence=preview(evidence),evidence_paths=evidence[:3])
        expected=definitions[sc].get('expectation','')
        notes+='\n'+expected if expected else ''
        rows.append(row('基準全体（出力範囲）',state,outcomes,sc_failures,notes,preview(remaining),evidence,'criterion'))
        # Each actual comparison is its own row, even when a criterion is only
        # partly tested. Operational recipe steps are not treated as requirements.
        for point,entries in points.items():
            values=[t['outcome'] for _,t in entries]
            status=verdict(values)
            locations=[f for f in sc_failures if f['checkpoint']==point]
            related=unique(c['assessment'] for c,_ in entries)
            observations=preview([f"{context(c)} / {t['target']}：{t['observed']}" for c,t in entries])
            note=f'記録した対象 {len(entries)}件の内訳。\n'+observations
            remainder='同じ基準に未確認あり。基準全体の行を参照。' if remaining else ''
            rows.append(row(point,status,values,locations,note,remainder,related,'checkpoint'))
    labels={'task':'タスク','owner':'担当','page':'URLに含む文字','page_exact':'対象URL','criterion':'対象基準'}
    selections=[f'{labels[k]}：{v}' for k,v in filters.items() if k in labels and v is not None]
    if filters.get('pending'):selections.append('未完了票のみ')
    scope=('選択した検査票のみ' if restricted else '選択したページの全状態・環境' if filters.get('page') or filters.get('page_exact') else 'run全体')
    scope+=f' / 目標 WCAG 2.2 {result["level"]} / {len(cases)}票'
    if selections:scope+=' / '+', '.join(selections)
    notices=[]
    if not result['scope_confirmed']:notices.append('run全体のページ・状態・適合要件の範囲は未確認です。')
    if not result['interaction_review']['complete']:notices.append('画面上の操作・状態の調査に未確認が残っています。')
    if not result['audit_complete']:notices.append('run全体の検証は完了していません。')
    return dict(rows=rows,failures=failures,scope=scope,notices=notices,legend=LEGEND,guidance=GUIDANCE)


def html_table(columns, rows, *, failures=False):
    widths={'criterion':6,'title':11,'level':4,'checkpoint':14,'applicability':6,'judgment':8,
            'locations':22,'notes':24,'remaining':20,'evidence':18,'id':7,'page_url':22,
            'state':10,'environment':10,'target':18,'observed':24,'expected':24,'steps':24}
    cols=''.join(f'<col style="width:{widths[key]}rem">' for key,_ in columns)
    width=sum(widths[key] for key,_ in columns)
    header=''.join('<th scope="col">'+escape(label)+'</th>' for _,label in columns)
    body=[]
    for row in rows:
        cells=[]
        for key,_ in columns:
            content=escape(str(row.get(key,''))).replace('\n','<br>')
            if key=='locations' and row.get('failure_ids'):
                content+=f'<br><a href="#failure-{row["failure_ids"][0]}">不適合箇所の詳細</a>'
            if key=='evidence':
                paths=row.get('evidence_paths',[])
                content='<br>'.join(f'<a href="./{quote(p,safe="/")}">{escape(p)}</a>' for p in paths)
                if row.get('evidence') and row['evidence'].count('\n')+1>len(paths):content+='<br>他の記録は検査票の一覧を参照。'
            tag='th scope="row"' if key==('id' if failures else 'criterion') else 'td'
            cells.append(f'<{tag}>{content}</{tag.split()[0]}>')
        attributes=f' id="failure-{row["id"]}"' if failures else f' class="{row["kind"]} {row["status"]}"'
        body.append('<tr'+attributes+'>'+''.join(cells)+'</tr>')
    caption='不適合を確認したすべての対象と再現手順' if failures else '達成基準の集計と、記録した確認観点の内訳'
    return (f'<table class="checksheet-table" style="width:{width}rem;table-layout:fixed">'
            f'<caption>{caption}</caption><colgroup>{cols}</colgroup><thead><tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table>')


def render_html(model):
    notices=''.join('<li>'+escape(n)+'</li>' for n in model['notices'])
    failures=(html_table(FAILURE_COLUMNS,model['failures'],failures=True) if model['failures'] else '<p>記録された不適合箇所はありません。未確認の有無はチェックシートを参照してください。</p>')
    return (f'<h2 id="checksheet">達成基準チェックシート</h2><p>集計範囲：{escape(model["scope"])}</p>'
            f'<p>{escape(model["legend"])}</p><p>{escape(model["guidance"])}</p><ul>{notices}</ul>'
            '<div class="scroll" tabindex="0" role="region" aria-label="達成基準チェックシート">'
            +html_table(COLUMNS,model['rows'])+'</div><h2 id="failures">不適合箇所</h2>'
            '<div class="scroll" tabindex="0" role="region" aria-label="不適合箇所の一覧">'+failures+'</div>')
