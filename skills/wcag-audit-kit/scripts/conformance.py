"""Draw a scope conclusion from verified records without modifying the run."""
from html import escape

from browser_capture import normalize
from page_catalog import configured_urls
from work_queue import unfinished


SCOPE_REQUIREMENTS = {
    'complete': '検証する範囲',
    'full_pages_reviewed': 'ページ全体',
    'processes_reviewed': '一連の手続き',
    'accessibility_support_reviewed': 'アクセシビリティサポート',
    'non_interference_reviewed': '非干渉',
}
LABELS = {'conforms': '適合', 'does_not_conform': '不適合', 'unverified': '未確認'}


def build(result, config, catalog, manifest, *, cases=None, filters=None):
    filters = filters or {}
    cases = result['cases'] if cases is None else cases
    scope = result.get('scope_review') or {}
    page = result['url'] if result.get('report_scope') == 'page' else filters.get('page_exact')
    url_contains = filters.get('page')
    subset_cases = bool(filters.get('criterion') or filters.get('task') or
                        filters.get('owner') is not None or filters.get('pending'))
    configured = configured_urls(config)
    captured_urls = {normalize(c['url'], config) for c in manifest['captures']}
    run_pages = dict.fromkeys(normalize(url, config) for url in configured + [p['url'] for p in manifest['pages']])
    run_pages.update((normalize(p['url'] if isinstance(p, dict) else p, config), None)
                     for p in manifest['unvisited'])
    pages = [url for url in run_pages if (not page or normalize(url) == normalize(page))
             and (not url_contains or url_contains in url)]
    kind = 'selected_cases' if subset_cases else 'page' if page else 'selected_pages' if url_contains else 'run'
    whole_run = bool(pages) and len(pages) == len(run_pages) and not subset_cases

    targets = {c['id'] for c in result['criteria'] if c['status'] != 'out_of_target_level'}
    selected = [c for c in cases if c['criterion'] in targets]
    assessments = [dict(case_id=c['case_id'], criterion=c['criterion'], url=c['page_url'], state=c['state'],
                        environment=c['environment'], record=c['assessment'],
                        evidence=[e['path'] for e in c['assessment_data']['verified_evidence']])
                   for c in selected if c['outcome'] == 'failed' and c['assessment_data']]
    pending = [c['case_id'] for c in selected if unfinished(c)]
    unverified_criteria = [c['id'] for c in result['criteria'] if c['status'] == 'unverified'] if whole_run else []
    requirements = {key: scope.get(key) is True for key in SCOPE_REQUIREMENTS}
    missing_requirements = [label for key, label in SCOPE_REQUIREMENTS.items() if not requirements[key]]
    missing_urls = [url for url in pages if url not in captured_urls]
    bad_captures = [c['key'] for c in manifest['captures'] if normalize(c['url'], config) in pages and
                    (c.get('execution') != 'completed' or (c.get('http_status') or 0) >= 400)]

    remaining = []
    if subset_cases:
        remaining.append('出力は選択した検査票です。適合を確認するには、範囲に含まれるすべての検査票が必要です。')
    elif not whole_run:
        remaining.append('出力はrunの一部です。ページ全体と一連の手続きを含む範囲はrun全体の帳票で確認してください。')
    if missing_requirements:
        remaining.append('適合要件の確認が必要です。' + '、'.join(missing_requirements) + '。')
    remaining.extend(scope.get('remaining') or [])
    for key, label in (('unvisited', '未訪問のURL'), ('missing_captures', '未収集の状態・環境'),
                       ('missing_cases', '未作成の検査票'), ('human_review_cases', '人の確認待ち')):
        if result[key]:
            remaining.append(f'{label}が{len(result[key])}件あります。')
    unapplied_states = manifest.get('declared_states_without_page', [])
    if unapplied_states:
        remaining.append(f'対象ページのない状態が{len(unapplied_states)}件あります。')
    if bad_captures:
        remaining.append(f'正常に収集できなかった状態・環境が{len(bad_captures)}件あります。')
    if missing_urls:
        remaining.append(f'収集結果がない対象URLが{len(missing_urls)}件あります。')
    if pending:
        remaining.append(f'未実施・判断保留・確認が残る検査票が{len(pending)}件あります。')
    if not result['collection_complete'] or (whole_run and manifest.get('collector_status', 'completed') != 'completed'):
        remaining.append('収集が完了していません。')
    if not result['interaction_review']['complete']:
        remaining.append('画面上の操作や状態の調査が残っています。')
    if not result['exploration']['complete']:
        remaining.append('操作経路の探索に確認が残っています。')
    if unverified_criteria and not pending:
        remaining.append(f'確認が必要な達成基準が{len(unverified_criteria)}件あります。')
    if not result['audit_complete'] and not remaining:
        remaining.append('予定していた検証が完了していません。')

    status = 'unverified'
    if assessments:
        status = 'does_not_conform'
    elif selected and not remaining and result['scope_confirmed']:
        status = 'conforms'
    return dict(status=status, label=LABELS[status], standard=catalog['standard'], level=result['level'],
                scope=dict(kind=kind, mode=config['scope'].get('mode', 'discover'), urls=pages, covers_reviewed_run=whole_run),
                scope_requirements=requirements, scope_review_record='scope-review.json' if scope else None,
                scope_review_evidence=[e['path'] for e in scope.get('verified_evidence', [])],
                failed_cases=assessments, pending_cases=pending, unverified_criteria=unverified_criteria,
                uncollected_urls=missing_urls, declared_states_without_page=unapplied_states,
                remaining=remaining)


def label(conclusion):
    standard = conclusion['standard'].replace('WCAG-', 'WCAG ', 1)
    return f"{standard} {conclusion['level']} の結論　{conclusion['label']}"


def render_html(conclusion, proof_href):
    urls = ''.join(f'<li>{escape(url)}</li>' for url in conclusion['scope']['urls'])
    reasons = ''.join(f'<li>{escape(reason)}</li>' for reason in conclusion['remaining'])
    failures = len(conclusion['failed_cases'])
    findings = f'<p><a href="#failures">不適合を確定した検査票（{failures}件）とその根拠</a></p>' if failures else ''
    record = conclusion['scope_review_record']
    review = (f'<p><a href="{escape(proof_href(record), quote=True)}">範囲と適合要件の確認記録</a></p>'
              if record else '')
    return (f'<p id="scope-conformance"><strong>{escape(label(conclusion))}</strong></p>'
            + (f'<details><summary>結論の対象URL（{len(conclusion["scope"]["urls"])}件）</summary><ul>{urls}</ul></details>'
               if urls else '')
            + findings + review
            + (f'<ul>{reasons}</ul><p><a href="#remaining">残る確認の詳細</a></p>' if reasons else ''))
