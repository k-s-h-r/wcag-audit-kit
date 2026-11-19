"""Page-scoped work packets and deterministic checks, independent of an LLM."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import uuid


def grouped_machine_issues(checks):
    groups={}
    for check in checks:
        if check['outcome'] not in {'failed','cant_tell'}:continue
        key=tuple(check[k] for k in ['criterion','checkpoint','target','observed','outcome'])
        group=groups.setdefault(key,dict(check,states=[],proof=[],capture_ids=[]))
        group['states'].append(check.get('state_label',check['capture'])+' / '+check['environment'])
        group['capture_ids'].append(check['capture'])
        if check['evidence'] not in group['proof']:group['proof'].append(check['evidence'])
    return [dict(g,count=len(g['states']),states='\n'.join(g['states']),evidence='\n'.join(g['proof']),
        outcome='問題あり（機械）' if g['outcome']=='failed' else '機械判定不能') for g in groups.values()]


def keyboard_route_result(run, edge, evidence):
    import audit
    from page_explorer import TAB_UNREACHABLE

    error = edge.get('error')
    if edge.get('blocked_requests') or edge.get('native_events'):
        return 'cant_tell', error or '通信・ページ移動の制限又はブラウザーの分岐があり、実入力の結果を確認できない。'
    if not error:
        return 'passed', '実入力を送出した。機能の完了・同等な代替経路の有無は別に確認する。'

    route = edge['route']
    step = edge.get('keyboard_unreachable_step')
    if 'keyboard_unreachable_step' not in edge and error == TAB_UNREACHABLE and (run / evidence).is_file():
        # Older receipts saved the initial wait and one wait per completed action.
        settled = audit.load(run / evidence).get('settling')
        if isinstance(settled, list):
            step = len(settled)
    if type(step) is int and 0 < step <= len(route) and route[step - 1]['type'] == 'key':
        if step == len(route):
            return 'failed', error
        return 'cant_tell', f'{step}手順目で停止したため、最後の入力は未確認。{error}'
    return 'cant_tell', f'実入力の結果を確認できない。{error}'


def machine_checks(run):
    import audit
    from page_explorer import status
    graph=status(run);_,catalog=audit.run_catalog(run)
    labels={c['selector']:c['label'] for n in graph.get('nodes',[]) for c in n.get('controls',[])}
    def scene(route):
        if not route:return '初期表示'
        names={'click':'クリック','hover':'ホバー','key':'キー','press':'キー','fill':'入力','scroll':'スクロール'}
        return ' → '.join(names[a['type']]+' '+labels.get(a.get('selector'),a.get('selector',''))+
                          (' / '+a['key'] if a.get('key') else '') for a in route)
    tags={'wcag'+c['id'].replace('.',''):c['id'] for c in catalog['criteria']}
    rows=[]
    for node in graph.get('nodes',[]):
        path=Path(node['evidence_dir'])/'axe.json'
        if not (run/path).exists():continue
        axe=audit.load(run/path)
        for group,outcome in [('violations','failed'),('passes','passed'),('incomplete','cant_tell'),('inapplicable','inapplicable')]:
            for rule in axe.get(group,[]):
                for criterion in sorted({tags[t] for t in rule.get('tags',[]) if t in tags}):
                    affected=rule.get('nodes',[])
                    rows.append(dict(criterion=criterion,checkpoint='axe / '+rule['id'],expected=rule['help'],
                        outcome=outcome,environment=node['environment'],capture=node['capture'],state_label=scene(node['route']),
                        target='\n'.join(str(n['target']) for n in affected),
                        observed='\n'.join(n.get('failureSummary') or n.get('html','') for n in affected),
                        evidence=path.as_posix(),source=rule.get('helpUrl',''),
                        note='機械ルールの結果。達成基準全体の適否とは区別する。'))
    from keyboard_checks import report_row
    for index,edge in enumerate(graph.get('edges',[])):
        if edge.get('keyboard_check'):
            path=Path(edge['evidence_dir'])/'keyboard-check.json'
            record = audit.load(run/path)
            if record['criterion'] != '2.4.7':
                rows.append(report_row(record, edge['environment'], path.as_posix()))
            continue
        if edge.get('hover_check'):
            path = Path(edge['evidence_dir'])/'hover-check.json'
            record = audit.load(run/path)
            labels_by_aspect = {'hoverable': '追加表示へポインターを移した後も表示が続く',
                                'dismissible': 'ポインターを移さずEscapeで追加表示を閉じられる',
                                'persistent': 'トリガーにポインターを置く間、指定した時間だけ追加表示が続く'}
            for item in record['observations']:
                rows.append(dict(criterion='1.4.13', checkpoint=f"ホバー経路 / {record['id']} / {item['aspect']}",
                    expected=labels_by_aspect[item['aspect']], outcome=item['outcome'], environment=edge['environment'],
                    capture='ホバー経路 '+record['id'], state_label=record['name'], target=item['target'],
                    observed=item['observed'], evidence=path.as_posix(), source='',
                    note=('指定した時間内の観察。情報が有効でなくなる条件や、他の時間・操作は追加確認。'
                          if item['aspect'] == 'persistent'
                          else '指定の操作と表示の結果。別の解除手段、例外、表示の持続時間は追加確認。')))
            continue
        if edge.get('border_check'):
            path = Path(edge['evidence_dir']) / 'border-check.json'
            record = audit.load(run/path)
            outcome = 'cant_tell'
            observed = record['observed']
            if record['status'] == 'measured':
                outcome = 'passed' if record['meets_3'] else 'failed'
                observed = (f"外枠 {record['border']} と隣接色 {record['outside']} の比は"
                            f"{record['ratio']:.4g}:1（基準 {record['minimum']}:1）。")
            rows.append(dict(criterion='1.4.11', checkpoint='境界の測定 / '+record['id'],
                expected='指定した外枠と隣接色のコントラスト比が3:1以上', outcome=outcome,
                environment=edge['environment'], capture='外枠の測定 '+record['id'], state_label=record['name'],
                target=record['target'], observed=observed, evidence=path.as_posix(), source='',
                note='指定した外枠の初期表示での測定。境界の必要性、ほかの状態と達成基準全体は追加確認。'))
            continue
        route=edge['route']
        # A key reached after pointer or scripted setup is evidence for that
        # mixed route, not for reaching the same state using only keys.
        if not route or any(step.get('type') not in {'key','press'} for step in route):continue
        action=route[-1]
        targeted=action['type']=='key'
        evidence = edge['evidence_dir'] + '/transition.json'
        outcome, observed = keyboard_route_result(run, edge, evidence)
        if outcome == 'passed' and edge.get('focus_after'):
            observed += f"入力後のフォーカスは {edge['focus_after']}。"
        if action.get('focused_only'):
            expected = '先行操作で対象にフォーカスが移った状態でキーを送出できる'
        else:
            expected = '指定した対象へTabで到達し、キーを送出できる' if targeted else '現在のフォーカスへキーを送出できる'
        rows.append(dict(criterion='2.1.1',checkpoint='実入力 / '+action.get('key',action['type']),
            expected=expected,
            outcome=outcome,
            environment=edge['environment'],capture=f'操作経路 {index+1}',state_label=scene(route),
            target=action.get('selector','') if targeted else '現在のフォーカス',
            observed=observed,evidence=evidence,source='',
            note='この入力経路の実行結果。キーボード操作の達成基準全体の判定ではない。'))
    return rows


def focus_image_evidence(run, plans):
    import audit
    from page_explorer import status

    checks = {plan['id']: plan for plan in plans if plan['criterion'] == '2.4.7'}
    if not checks:
        return []
    graph = status(run)
    rows = []
    for entry in [*graph.get('edges', []), *graph.get('queue', [])]:
        plan = checks.get(entry.get('keyboard_check'))
        if plan is None:
            continue
        receipt = {}
        evidence = ''
        reason = '指定したキー経路は探索待ちです。'
        if 'evidence_dir' in entry:
            path = Path(entry['evidence_dir']) / 'keyboard-check.json'
            evidence = path.as_posix()
            record = audit.load(run/path)
            if record['steps']:
                receipt = record['steps'][-1].get('focus_images', {})
            reason = record.get('reason') or '入力前の画像は未取得です。'
        rows.append(dict(criterion='2.4.7', name=plan['name'], target=plan['steps'][-1]['focus'],
                         environment=entry['environment'], status=receipt.get('status', 'not_run'),
                         reason=receipt.get('reason', reason), evidence=evidence,
                         before_image=receipt.get('before', {}).get('image', ''),
                         after_image=receipt.get('after', {}).get('image', '')))
    return rows


def page_result(run, url, original=None):
    import audit
    from browser_capture import normalize
    from checksheet import build
    from work_queue import unfinished
    original=original or audit.outcomes(run)
    rows=[c for c in original['cases'] if normalize(c['page_url'])==normalize(url)]
    if not rows:raise ValueError('指定ページの検査票がありません')
    meta,catalog=audit.run_catalog(run)
    model=build(original,catalog,cases=rows,filters={'page_exact':url},manifest=audit.load(run/'capture-manifest.json'))
    statuses={r['criterion']:r['status'] for r in model['rows'] if r['kind']=='criterion'}
    result=deepcopy(original);result.update(url=url,report_scope='page',cases=rows,counts=dict(Counter(c['outcome'] for c in rows)))
    result['focus_evidence'] = focus_image_evidence(run, meta['config'].get('keyboard_checks', []))
    for c in result['criteria']:
        c['counts']=dict(Counter(r['outcome'] for r in rows if r['criterion']==c['id']))
        c['status']={'passed':'passed_checks'}.get(statuses[c['id']],statuses[c['id']])
    ids={c['case_id'] for c in rows};pids={c['page_id'] for c in rows}
    result['recorded_cases']=sum(c['assessment_data'] is not None for c in rows)
    for key in ['human_review_cases','unassigned_remaining_cases']:result[key]=[i for i in result[key] if i in ids]
    for key in ['missing_captures','unvisited']:
        result[key]=[r for r in result[key] if normalize(r['url'] if isinstance(r,dict) else r)==normalize(url)]
    page_captures=[c for c in audit.load(run/'capture-manifest.json')['captures'] if c['page_id'] in pids]
    captures={c['key'] for c in page_captures}
    if 'visual_structure_evidence' in result:
        result['visual_structure_evidence'] = [item for item in result['visual_structure_evidence']
                                               if item['capture'] in captures]
    result['missing_cases']=[i for i in result['missing_cases'] if i.rsplit('--',1)[0] in captures]
    result['collection_complete']=bool(page_captures) and not result['missing_captures'] and all(c.get('collection_state','finished')=='finished' for c in page_captures)
    result['collector_status']='completed' if result['collection_complete'] else 'interrupted'
    result['declared_states_without_page']=[]
    result['observation_usage']['screenshots']=[i for i in result['observation_usage'].get('screenshots',[]) if i.get('page_id') in pids]
    review=result['interaction_review'];review['pages']={k:v for k,v in review['pages'].items() if k in pids}
    review['remaining']=[item for p in review['pages'].values() for item in p.get('remaining',[])]
    if review['required']:review['remaining']+=sorted(pids-set(review['pages']))
    review['complete']=all(p['complete'] for p in review['pages'].values()) if review['pages'] else not review['required']
    review['status']='reviewed' if review['complete'] and review['pages'] else 'partial' if review['pages'] else 'not_recorded'
    result['audit_complete']=(all(c['status'] not in {'unverified'} for c in result['criteria']) and
        not any(unfinished(c) for c in rows) and not result['missing_captures'] and not result['missing_cases'] and
        not result['unvisited'] and original['scope_confirmed'] and review['complete'] and result.get('exploration',{}).get('complete',True))
    result['conformance_claim']='この1ページの記録範囲の結果です。ページ間の一貫性や手続き全体の確認は別に示します。'
    from verification_modes import summary
    result['verification']=summary(run,result)
    return result


def next_work(run, url, limit=5):
    import audit
    from page_explorer import status
    result=page_result(run,url);graph=status(run);_,catalog=audit.run_catalog(run)
    pending=[c for c in result['cases'] if c['outcome'] in {'not_run','cant_tell'} or
             (c['assessment_data'] or {}).get('remaining') or (c['assessment_data'] or {}).get('coverage_complete') is not True]
    by_id={c['id']:c for c in catalog['criteria']}
    checks=machine_checks(run)
    mode=result.get('verification')
    packets=[];unavailable=[]
    for c in pending:
        packet=dict(c,definition=by_id[c['criterion']],
                    machine_results=[m for m in checks if m['criterion']==c['criterion'] and m['capture']==c['capture']])
        if c['criterion'] == '2.4.7':
            packet['focus_evidence'] = [item for item in result['focus_evidence'] if item['environment'] == c['environment']]
        if c['criterion'] == '1.3.1' and 'visual_structure_evidence' in result:
            packet['visual_structure_evidence'] = [item for item in result['visual_structure_evidence']
                                                   if item['capture'] == c['capture']]
        if mode:
            from verification_modes import work_checkpoint
            points=[r for r in mode['checkpoints'] if r['criterion']==c['criterion']]
            packet['verification_checkpoints']=[work_checkpoint(r,mode['mode']) for r in points if r['selected_support']!='no']
            packet['skipped_checkpoints']=[dict(id=r['id'],check=r['check'],reason=r['note']) for r in points if r['selected_support']=='no']
            if not packet['verification_checkpoints']:
                unavailable.append({'case_id':c['case_id'],'criterion':c['criterion'],'checkpoints':packet['skipped_checkpoints']});continue
        packets.append(packet)
    mode_notice={k:v for k,v in mode.items() if k!='checkpoints'} if mode else None
    return {'page':url,'audit_complete':result['audit_complete'],'verification':mode_notice,
        'exploration':{'graph_digest':graph.get('graph_digest'),'pending_routes':len(graph.get('queue',[])),'remaining':graph['remaining'],
                       'next':'page-audit --resume' if graph.get('queue') else '残る範囲の追加検査'},
        'machine_checks':dict(Counter(c['outcome'] for c in checks)),
        'remaining_cases':len(pending),'mode_actionable_cases':len(packets),'mode_unavailable_count':len(unavailable),
        'mode_unavailable_cases':unavailable[:max(1,limit)],
        'next_cases':packets[:max(1,limit)],
        'policy':('選択モードで許可した方法だけを実行する。△は確認できる部分だけを実行し、残る判断を未確認にする。AIが無効なら画像・意味をAIで判断せず、SRが無効なら起動しない。' if mode else '')+
                 '機械ルールを先に実行する。実行可能な追加検査を進め、意味・目的などの未確定部分だけを判断する。環境不足だけで人待ちにせず代替手段を調べる。'}


def resolve(run, value):
    """Evidence-backed resolution of explicit gaps, tied to this exact graph."""
    import audit
    from page_explorer import status
    from ledger_lock import run_lock
    with run_lock(run):
        raw=audit.load(run/'exploration.json');status(run)
        if value.get('graph_digest')!=audit.digest(raw):raise ValueError('探索が更新済み。最新のgraph_digestを使う')
        items=value.get('resolutions',[])
        if not isinstance(items,list):raise ValueError('resolutionsは一覧')
        names=[i.get('item') for i in items]
        if len(names)!=len(set(names)) or not set(names).issubset(raw.get('remaining',[])):raise ValueError('解消する未確認の項目が不正')
        plan=audit.run_plan(run);previous=plan.get('exploration_review');combined={}
        if previous:
            saved=audit.load(run/previous)
            if saved['graph_digest']==value['graph_digest']:
                combined={item['item']:item for item in saved.get('resolutions',[])}
        for item in items:combined[item['item']]=item
        proof={}
        for item in combined.values():
            if len(item.get('observed','').strip())<10 or not item.get('evidence'):raise ValueError('追加検査の具体的な観察と証拠が必要')
            for p in item['evidence']:
                checked=audit.evidence_item(run,p);proof[checked['path']]=checked
        saved=dict(value,resolutions=list(combined.values()),verified_evidence=list(proof.values()),previous_review=previous)
        path=run/'exploration-reviews'/(uuid.uuid4().hex+'.json');audit.save(path,saved)
        plan['exploration_review']=str(path.relative_to(run));audit.save(run/'plan.json',plan)
        return {'file':str(path),'resolved':len(items),'total_resolved':len(combined)}
