"""Read-only Japanese check sheets derived from the existing assessment ledger."""
from collections import Counter, defaultdict
from html import escape
from urllib.parse import quote

from work_queue import unfinished


COLUMNS = [('criterion','達成基準'),('title','達成基準名'),('level','レベル'),
           ('checkpoint','確認観点'),('applicability','適用'),('judgment','適合'),
           ('locations','不適合箇所'),('notes','確認結果'),
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


AXE_LABELS = {
    'image-alt': '画像の代替テキスト',
    'role-img-alt': '画像の役割を持つ要素の名前',
    'svg-img-alt': 'SVG画像の名前',
    'color-contrast': '文字のコントラスト',
    'video-caption': '動画の字幕トラック',
    'link-in-text-block': '本文のリンクを色以外で識別できるか',
    'document-title': 'ページタイトルの有無',
    'bypass': '繰り返しを避ける手段',
    'link-name': 'リンクの名前',
    'button-name': 'ボタンの名前',
    'html-has-lang': 'ページの言語指定',
    'html-lang-valid': 'ページの言語コード',
    'meta-viewport': 'ブラウザーの拡大を制限する指定',
}


def machine_label(checkpoint):
    rule = checkpoint.removeprefix('axe / ')
    return AXE_LABELS.get(rule, checkpoint)


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


def applicable(outcomes, status, observed=False):
    if status=='out_of_target_level':return '目標レベル外'
    if observed or any(o in {'passed','failed'} for o in outcomes):return 'あり'
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
    exploration=result.get('exploration',{}).get('remaining',[])
    if result.get('report_scope')=='page' and exploration:
        gaps.append(f'操作・探索の追加確認 {len(exploration)}項目。自動探索・機械検査の表を参照。')
    else:gaps+=exploration
    return gaps


def build(result, catalog, *, cases=None, filters=None, manifest=None):
    """No writes, inferred passes, or changes to the machine interchange schema."""
    cases=result['cases'] if cases is None else cases
    filters=filters or {};manifest=manifest or {}
    if result.get('report_scope')=='page':filters=dict(page_exact=result['url'],**{k:v for k,v in filters.items() if k!='page_exact'})
    restricted=bool(filters.get('task') or filters.get('owner') is not None or filters.get('pending'))
    ids={c['criterion'] for c in cases}
    scope_captures = {c['capture'] for c in cases}
    machine_by_criterion = defaultdict(list)
    for item in result.get('machine_checks', []):
        if not item.get('page_url') or item['capture'] in scope_captures:
            machine_by_criterion[item['criterion']].append(item)
    criteria=[c for c in result['criteria'] if (not filters.get('criterion') or c['id']==filters['criterion'])
              and (not restricted or c['id'] in ids)]
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
        assessments = [c['assessment_data'] for c in selected if c['assessment_data']]
        checks = machine_by_criterion[sc]
        observed_target = any(t['outcome'] != 'inapplicable' for a in assessments if a['execution'] == 'completed'
                              for t in a.get('targets', []))
        observed_target |= any(item.get('target_count', 0) and item['outcome'] != 'inapplicable' for item in checks)
        # A measured result and a criterion verdict answer different questions.
        outcomes_by_check = defaultdict(set)
        for item in checks:
            outcomes_by_check[item['outcome']].add(item['checkpoint'])
        machine_notes = []
        for outcome, title in (('failed', '指摘あり'), ('cant_tell', '要確認'), ('passed', '通過'), ('inapplicable', '対象なし')):
            if outcomes_by_check[outcome]:
                labels = sorted(outcomes_by_check[outcome], key=lambda name: (machine_label(name) == name, name))
                names = '、'.join(machine_label(name) for name in labels[:2])
                suffix = f'、ほか{len(labels)-2}項目' if len(labels) > 2 else ''
                machine_notes.append(f'機械検査で{title}（{names}{suffix}）')
        samples = [item['observed'] for item in checks
                   if item['outcome'] == 'passed' and '測定値の最低' in item['observed']]
        if samples and not any('コントラスト比' in a['observed'] for a in assessments):
            machine_notes += samples[:1]
        state=('out_of_target_level' if criterion['status']=='out_of_target_level' else
               verdict(outcomes,bool(pending or gaps)))
        if state=='out_of_target_level':gaps=[];pending=[]
        remaining=unique(reason for a in assessments for reason in a.get('remaining', []))
        unrecorded = [c for c in pending if c['assessment_data'] is None]
        if unrecorded and (result.get('report_scope') == 'page' or filters.get('page_exact')):
            remaining.append('基準の検査は未実施。' if not assessments else '一部の表示状態・環境で判定が未記録。')
        elif unrecorded:
            remaining.extend(f'{context(c)}：基準の検査は未実施。' for c in unrecorded)
        if not selected and state!='out_of_target_level':remaining.append('この基準の検査記録がありません。')
        if pending and not remaining:
            remaining.append('検査範囲または必要な確認方法が未確定。')
        remaining+=gaps
        evidence=unique([c['assessment'] for c in selected] + [m['evidence'] for m in checks])
        observed = preview((a['observed'] for a in assessments), limit=2, destination='詳細記録')
        notes = '\n'.join(part for part in [observed, *machine_notes] if part)
        if state == 'inapplicable' and notes:
            notes='非適用の根拠：'+notes
        if state == 'failed' and pending and notes:
            notes+='。未確認あり。'
        base=dict(criterion=sc,title=criterion['title'],level=criterion['level'])
        def row(checkpoint,status,values,locations,notes,remaining,evidence,kind,observed=False):
            judgment=STATUS[status]
            if kind=='criterion' and status=='failed' and remaining:judgment+='\n未確認あり'
            return dict(base,checkpoint=checkpoint,status=status,kind=kind,
                applicability=applicable(values,status,observed),judgment=judgment,
                locations=preview([f"{f['id']} {f['page_url']} / {f['state']} / {f['environment']} / {f['target']}" for f in locations],
                                  destination='不適合箇所の一覧'),failure_ids=[f['id'] for f in locations],
                notes=notes,remaining=remaining,evidence=preview(evidence),evidence_paths=evidence[:3])
        rows.append(dict(row('基準全体',state,outcomes,sc_failures,notes,preview(remaining),evidence,'criterion',
                             observed_target), normative_url=criterion['normative_url'],
                         recorded_observation=bool(assessments), only_rule_not_applicable=bool(
                             outcomes_by_check and set(outcomes_by_check) == {'inapplicable'} and not assessments)))
        # Each actual comparison is its own row, even when a criterion is only
        # partly tested. Operational recipe steps are not treated as requirements.
        for point,entries in points.items():
            values=[t['outcome'] for _,t in entries]
            status=verdict(values)
            locations=[f for f in sc_failures if f['checkpoint']==point]
            related=unique(c['assessment'] for c,_ in entries)
            observations=preview([f"{context(c)} / {t['target']}：{t['observed']}" for c,t in entries])
            note=f'記録した対象 {len(entries)}件の内訳。\n'+observations
            remainder=''
            rows.append(row(point,status,values,locations,note,remainder,related,'checkpoint'))
        points=unique(m['checkpoint'] for m in checks)
        points.sort(key=lambda p:min({'failed':0,'cant_tell':1,'passed':2,'inapplicable':3}[m['outcome']] for m in checks if m['checkpoint']==p))
        for point in points:
            entries=[m for m in checks if m['checkpoint']==point];values=[m['outcome'] for m in entries]
            status=verdict(values);proof=unique(m['evidence'] for m in entries)
            item=row('機械検査 / '+entries[0]['expected'],status,values,[],point+'\n'+preview([m.get('state_label',m['capture'])+' / '+m['environment']+' / '+m['target']+'：'+m['observed'] for m in entries]),
                'この機械ルール以外の条件・対象は基準全体の行を参照。',proof,'checkpoint',any(m.get('target_count', 0) for m in entries))
            item['judgment']={'passed':'○ 通過（機械）','failed':'× 問題あり（機械）','inapplicable':'— 対象なし（機械）','unverified':'未確定（機械）'}[status]
            item['locations']=preview([m.get('state_label',m['capture'])+' / '+m['environment']+' / '+m['target'] for m in entries if m['outcome'] in {'failed','cant_tell'}],destination='自動検出した問題')
            item['machine_issues_link'] = bool(item['locations'])
            rows.append(item)
    labels={'task':'タスク','owner':'担当','page':'URLに含む文字','page_exact':'対象URL','criterion':'対象基準'}
    selections=[f'{labels[k]}：{v}' for k,v in filters.items() if k in labels and v is not None]
    if filters.get('pending'):selections.append('未完了票のみ')
    scope=('選択した検査票のみ' if restricted else '選択したページの全状態・環境' if filters.get('page') or filters.get('page_exact') else 'run全体')
    scope+=f' / 目標 WCAG 2.2 {result["level"]}'
    if result.get('report_scope')=='page':scope='1ページ / '+result['url']+scope[scope.index(' / 目標'):]
    if selections:scope+=' / '+', '.join(selections)
    notices=[]
    if not result['scope_confirmed']:notices.append('run全体のページ・状態・適合要件の範囲は未確認です。')
    if not result['interaction_review']['complete']:notices.append('画面上の操作・状態の調査に未確認が残っています。')
    if not result['audit_complete']:notices.append('run全体の検証は完了していません。')
    return dict(rows=rows,failures=failures,scope=scope,notices=notices,legend=LEGEND,guidance=GUIDANCE)


def html_table(columns, rows, *, failures=False, proof_href=None):
    if proof_href is None:
        proof_href = lambda path: './' + quote(path, safe='/')
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
            elif key=='locations' and row.get('machine_issues_link'):
                content+='<br><a href="#machine-results">自動検出した問題の詳細</a>'
            if key=='evidence':
                paths=row.get('evidence_paths',[])
                content='<br>'.join(f'<a href="{escape(proof_href(p), quote=True)}">{escape(p)}</a>' for p in paths)
                if row.get('evidence') and row['evidence'].count('\n')+1>len(paths):content+='<br>他の記録は検査票の一覧を参照。'
            tag='th scope="row"' if key==('id' if failures else 'criterion') else 'td'
            cells.append(f'<{tag}>{content}</{tag.split()[0]}>')
        attributes=f' id="failure-{row["id"]}"' if failures else f' class="{row["kind"]} {row["status"]}"'
        body.append('<tr'+attributes+'>'+''.join(cells)+'</tr>')
    caption='不適合を確認したすべての対象と再現手順' if failures else '達成基準の集計と、記録した確認観点の内訳'
    return (f'<table class="checksheet-table" style="width:{width}rem;table-layout:fixed">'
            f'<caption>{caption}</caption><colgroup>{cols}</colgroup><thead><tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table>')


def render_failures(model, proof_href=None):
    if proof_href is None:
        proof_href = lambda path: './' + quote(path, safe='/')
    cards = []
    for finding in model['failures']:
        proof = ' '.join(f'<a href="{escape(proof_href(p), quote=True)}">証拠 {i}</a>'
                         for i, p in enumerate(finding['evidence_paths'], 1))
        cards.append(f'<article class="finding" id="failure-{finding["id"]}">'
                     f'<h3>{escape(finding["criterion"] + " " + finding["target"])}</h3>'
                     f'<p>{escape(finding["page_url"])} · {escape(finding["state"])} · {escape(finding["environment"])}</p>'
                     f'<dl><dt>確認した問題</dt><dd>{escape(finding["observed"])}</dd>'
                     f'<dt>期待される動作</dt><dd>{escape(finding["expected"])}</dd>'
                     f'<dt>再現手順</dt><dd>{escape(finding["steps"]).replace(chr(10), "<br>")}</dd></dl><p>{proof}</p></article>')
    heading = '<h2 id="failures">修正箇所</h2>'
    if not cards:
        return heading + '<p>今回の記録で不適合が確定した箇所はありません。</p>'
    return heading + ''.join(cards)


def result_card(row, proof_href):
    url = escape(row['normative_url'], quote=True)
    title = f'<a href="{url}">{escape(row["criterion"])}</a> {escape(row["title"])}'
    scope = '対象あり · ' if row['applicability'] == 'あり' else ''
    paths = row['evidence_paths']
    proof = ''
    if paths:
        first = escape(proof_href(paths[0]), quote=True)
        proof = f'<p><a href="{first}" aria-label="{escape(row["criterion"] + "の証拠", quote=True)}">証拠を開く</a></p>'
    return (f'<article class="result"><h3>{title}</h3>'
            f'<p class="result-status">{scope}基準の判定 {escape(row["judgment"])}</p>'
            f'<p>{escape(row["notes"]).replace(chr(10), "<br>")}</p>{proof}</article>')


def render_summary(model, proof_href):
    rows = [row for row in model['rows'] if row['kind'] == 'criterion' and row['notes']
            and row['status'] != 'out_of_target_level']
    heading = '<h2 id="performed">実施結果</h2>'
    if not rows:
        return heading + '<p>観察結果の記録はまだありません。</p>'
    selected = [row for row in rows if row['recorded_observation']]
    machine = [row for row in rows if not row['recorded_observation'] and not row['only_rule_not_applicable']]
    absent = [row for row in rows if row['only_rule_not_applicable']]
    direct = selected or machine
    extra = [('機械検査のその他の結果', machine if selected else []),
             ('機械検査で対象が見つからなかった項目', absent)]
    cards = ''.join(result_card(row, proof_href) for row in direct)
    details = ''.join(f'<details><summary>{label}（{len(items)}基準）</summary>'
                      + ''.join(result_card(row, proof_href) for row in items) + '</details>'
                      for label, items in extra if items)
    return heading + cards + details


def render_remaining(model, exploration):
    planned = [r for r in model['rows'] if r['kind'] == 'criterion' and r['remaining']]
    noted = [r for r in planned if r['notes']]
    missing = len(planned) - len(noted)
    items = ''.join(f'<li><strong>{escape(r["criterion"] + " " + r["title"])}</strong>　'
                    f'{escape(r["remaining"]).replace(chr(10), "<br>")}</li>' for r in noted)
    incomplete = f'<p>観察結果の記録がない基準が {missing} 件あります。<a href="#checksheet">達成基準の一覧</a>で確認できます。</p>' if missing else ''
    routes = f'<p>自動探索に残る確認が {len(exploration)} 件あります。<a href="#exploration-details">操作経路の詳細</a>を参照してください。</p>' if exploration else ''
    heading = '<h2 id="remaining">残る確認</h2>'
    return heading + incomplete + routes + (f'<ul>{items}</ul>' if items else '')


def render_checklist(model, proof_href=None):
    return ('<details id="checksheet"><summary>達成基準チェックシート</summary>'
            f'<p>{escape(model["scope"])}</p><p>{escape(model["legend"])}</p>'
            '<div class="scroll" tabindex="0" role="region" aria-label="達成基準チェックシート">'
            + html_table(COLUMNS, model['rows'], proof_href=proof_href) + '</div></details>')


def render_html(model):
    return render_failures(model) + render_checklist(model)
