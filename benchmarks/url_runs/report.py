"""Summarize and compare the grades from an ordinary URL-only run."""
from collections import Counter, defaultdict
from html import escape
from os.path import relpath
from pathlib import Path
from urllib.parse import quote

from ..suite import core, layout
from . import exploration, scoring


CORRECT = {'detected', 'matched'}
INCORRECT = {'false_positive', 'wrong_pass', 'wrong_control_outcome'}
IDENTITY = ('page_id', 'criterion', 'case', 'page', 'state', 'target', 'checkpoint', 'expected')
STATUS_LABEL = {
    'detected': '問題を検出', 'false_positive': '誤検出（問題ありと判定）',
    'wrong_pass': '問題を「問題なし」か「該当なし」と誤判定',
    'wrong_control_outcome': '「問題なし」と「該当なし」を取り違え',
    'observed_no_verdict': '観察済み・確定判定なし', 'state_or_route_unobserved': '状態・経路を未確認',
    'collection_error': '収集失敗・未実施',
}
EXPECTED_LABEL = {'failed': '問題あり', 'passed': '問題なし', 'inapplicable': '該当なし'}
UNCONFIRMED = ('observed_no_verdict', 'state_or_route_unobserved', 'collection_error')
SCOPE_REASON = {
    'content_review': '画像や文言などの内容を確認',
    'screen-reader': '実際のスクリーンリーダーで確認',
    'cross-page': '複数ページを比較して確認',
    'machine_deferred': '問題集の設定で機械判定を保留',
    'acquisition': '証拠の取得を確認',
}
METRICS = {
    'completed_pages': '収集が完了したページ', 'correct': '正解した行', 'evaluated': '判定が出た行',
    'detected': '既知の問題を検出', 'matched': '問題なし・該当なしを正しく判定', 'incorrect': '誤判定の行',
    **{status: STATUS_LABEL[status] for status in UNCONFIRMED},
    'unmatched_findings': '正解と照合できない指摘',
}


def scorer_digest():
    runtime = core.RUNTIME / 'scripts'
    paths = [Path(module.__file__) for module in (scoring, exploration)]
    paths += [runtime / f'{name}.py' for name in (
        'combobox', 'dialog_focus', 'keyboard_checks', 'keyboard_function', 'keyboard_trap', 'target_spacing',
    )]
    fingerprint = core.digest({path.name: core.file_hash(path) for path in paths})
    return layout.scorer_digest('url_scorer', fingerprint)


def summary(score):
    rows = score['rows']
    counts = Counter(row['status'] for row in rows)
    correct = sum(counts[status] for status in CORRECT)
    incorrect = sum(counts[status] for status in INCORRECT)
    return dict(rows=len(rows), completed_pages=score['completed_pages'], correct=correct, evaluated=correct + incorrect,
                detected=counts['detected'], matched=counts['matched'], incorrect=incorrect,
                **{key: counts[key] for key in UNCONFIRMED},
                unmatched_findings=len(score['unmatched_findings']))


def indexed_rows(score):
    rows = {tuple(row[field] for field in IDENTITY): row['status'] for row in score['rows']}
    if len(rows) != len(score['rows']):
        raise ValueError('採点行の識別情報が重複しています')
    return rows


def compare(baseline, current):
    for field in ('corpus_digest', 'environment', 'initial_args', 'explore_args', 'workers', 'pages'):
        if baseline[field] != current[field]:
            raise ValueError(f'比較条件が異なります（{field}）')
    same_scorer = bool(baseline.get('scorer_digest') and current.get('scorer_digest'))
    if same_scorer and baseline['scorer_digest'] != current['scorer_digest']:
        raise ValueError('採点器が異なります。同じ採点器で両方の収集を採点してください')

    def limits(score):
        return {tuple(sorted(row['limits'].items())) for row in score['receipts'] if 'limits' in row}

    old_limits, new_limits = limits(baseline), limits(current)
    if old_limits and new_limits and old_limits != new_limits:
        raise ValueError('探索上限が異なります')
    before, after = indexed_rows(baseline), indexed_rows(current)
    if before.keys() != after.keys():
        raise ValueError('比較対象の採点行が異なります')
    changes = dict(regressions=[], improvements=[], other_changes=[])
    for key, status in after.items():
        old = before[key]
        if old == status:
            continue
        if (old in CORRECT or (status in INCORRECT and old not in INCORRECT)
                or status == 'collection_error'
                or (old == 'observed_no_verdict' and status == 'state_or_route_unobserved')):
            group = 'regressions'
        elif status in CORRECT:
            group = 'improvements'
        else:
            group = 'other_changes'
        changes[group].append(dict(zip(IDENTITY, key), before=old, after=status))
    return dict(baseline_commit=baseline['commit'], scorer_match='same' if same_scorer else 'unrecorded',
                baseline_summary=summary(baseline), **changes)


def table(caption, columns, rows, *, row_headings=False):
    headings = ''.join(f'<th scope="col">{escape(label)}</th>' for label in columns)
    body = []
    for row in rows:
        first, *rest = row
        label = f'<th scope="row">{first}</th>' if row_headings else f'<td>{first}</td>'
        body.append('<tr>' + label + ''.join(f'<td>{cell}</td>' for cell in rest) + '</tr>')
    name = escape(caption, quote=True)
    return (f'<div class="scroll" role="region" aria-label="{name}" tabindex="0"><table>'
            f'<caption>{name}</caption><thead><tr>{headings}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


def status_label(row, status):
    if status == 'matched':
        return f'{EXPECTED_LABEL[row["expected"]]}と正しく判定'
    return STATUS_LABEL[status]


def fraction(value, total):
    return f'{value} / {total}' if total else '—'


def overview(score, counts):
    problems = Counter(row['status'] for row in score['rows'] if row['expected'] == 'failed')
    controls = Counter(row['status'] for row in score['rows'] if row['expected'] != 'failed')
    known, comparison_cases = sum(problems.values()), sum(controls.values())
    total = counts['rows']
    unconfirmed = total - counts['evaluated']
    indicators = (
        ('既知の問題の検出率', problems['detected'], known),
        ('全採点行の正解率', counts['correct'], total),
        ('確定判定が出た割合', counts['evaluated'], total),
    )
    cards = []
    for label, value, denominator in indicators:
        percent = f'{value / denominator:.1%}' if denominator else '—'
        quantity = f'<span>{fraction(value, denominator)}件</span>' if denominator else ''
        cards.append(f'<div><dt>{label}</dt><dd><strong>{percent}</strong>{quantity}</dd></div>')
    breakdown = [
        ('正解', problems['detected'], controls['matched']),
        (STATUS_LABEL['false_positive'], '—', controls['false_positive']),
        (STATUS_LABEL['wrong_pass'], problems['wrong_pass'], '—'),
        (STATUS_LABEL['wrong_control_outcome'], '—', controls['wrong_control_outcome']),
        *((STATUS_LABEL[key], problems[key], controls[key]) for key in UNCONFIRMED),
    ]
    return (f'<p>既知の問題{known}件のうち{problems["detected"]}件を検出しました。'
            f'検出できなかった問題は{known - problems["detected"]}件です。'
            f'全{total}件のうち{unconfirmed}件は確定判定が出ませんでした。</p>'
            f'<dl class="indicators">{"".join(cards)}</dl>'
            '<h2 id="breakdown">何を検出し、何が残ったか</h2>'
            + table('期待結果ごとの内訳', ('採点結果', f'問題ありを期待（{known}件）',
                    f'問題なし・該当なしを期待（{comparison_cases}件）'),
                    ([str(cell) for cell in row] for row in breakdown), row_headings=True)
            + '<p>正解は、問題を検出するか、問題なし・該当なしを期待どおりに判定した行です。'
              '割合の分母には未確認の行も含めます。1行は、ページ内の特定の状態・要素・検査観点の組み合わせです。</p>'
              '<p>「観察済み・確定判定なし」は、状態の観察や一部の判定の記録はあるものの、採点に必要な判定が'
              'そろわなかった行です。「状態・経路を未確認」は、採点に使える観察や判定が記録されなかった行です。</p>')


def corpus_scope(digest):
    # Older runs still render when the checkout no longer contains their corpus.
    try:
        corpus = core.corpus()
    except (OSError, ValueError):
        return None
    if corpus['digest'] != digest:
        return None
    scopes = {}
    for suite in corpus['suites']:
        pages = {page: set() for case in suite['cases'] for page in case['pages']}
        for case in suite['cases']:
            for row in case['expectations']:
                group = core.verification_group(row)
                if group != 'machine_target':
                    pages[row['page']].add((row['checkpoint'], group))
            for row in case.get('evidence_expectations', []):
                pages[row['page']].add((row['checkpoint'], 'acquisition'))
        scopes[suite['criterion']] = dict(sorted(pages.items()))
    return scopes


def scope_table(criterion, scope, rows, checkpoints):
    scored = defaultdict(Counter)
    for row in rows:
        scored[row['page']][row['checkpoint']] += 1
    page_rows = []
    for page, exceptions in scope.items():
        points = scored.get(page)
        included = []
        for point, count in sorted((points or {}).items()):
            rule = scoring.AXE_RULES.get(point)
            description = f'axe / {rule}' if rule else checkpoints.get(point, '')
            included.append(f'{escape(point)}（{count}件） {escape(description)}')
        omitted = '<br>'.join(f'{escape(point)} {SCOPE_REASON[group]}' for point, group in sorted(exceptions))
        page_rows.append((escape(page), '<br>'.join(included) or '採点対象の行なし', omitted or '—'))
    return table(f'{criterion} のページ別採点範囲', ('ページ', '今回採点した観点', '今回の採点に含めない観点'),
                 page_rows, row_headings=True)


def render(score, run, output, json_name):
    counts = summary(score)
    comparison = score.get('comparison')
    rows = score['rows']
    columns = ('ページ', 'ケース', '観点', '状態', '対象', '期待結果')
    by_criterion = defaultdict(list)
    for row in rows:
        by_criterion[row['criterion']].append(row)

    def identity_cells(row):
        return [escape(value) for value in (f"{row['page']} ({row['page_id']})", row['case'], row['checkpoint'],
                row['state'], row['target'], EXPECTED_LABEL[row['expected']])]

    def evidence_link(path, label):
        source = core.local(run, path)
        if source.is_file():
            href = quote(relpath(source, output.parent))
            return f'<a href="{href}">{label}</a>'
        return ''

    def evidence_links(row):
        items = []
        for environment, label in (('desktop', 'PC幅'), ('narrow', 'スマホ相当幅')):
            checks = row['environments'][environment]
            paths = dict.fromkeys([item['evidence'] for item in checks['verdicts']] or checks['reached'])
            for index, path in enumerate(paths, 1):
                if link := evidence_link(path, f'{label}の証拠 {index}'):
                    items.append(link)
        return '<br>'.join(items) if items else '—'

    changes_html = ''
    changed_rows = {}
    if comparison:
        before = escape(comparison['baseline_commit'])
        after = escape(score['commit'])
        changes_html = f'<h2 id="comparison">前回との差</h2><p>前回 <code>{before}</code><br>今回 <code>{after}</code></p>'
        if comparison['scorer_match'] == 'unrecorded':
            changes_html += '<p>保存された採点結果に採点器の版がないため、採点器の一致は未確認です。</p>'
        failed = score['totals'].get('failed', 0)
        denominators = dict(completed_pages=score['pages'], correct=len(rows), evaluated=len(rows),
                            detected=failed, matched=len(rows) - failed)

        def display(values, key):
            return fraction(values[key], denominators[key]) if key in denominators else str(values[key])

        baseline = comparison['baseline_summary']
        changes_html += table('前回と今回の集計', ('指標', '前回', '今回', '増減'), (
            (label, display(baseline, key), display(counts, key), f'{counts[key] - baseline[key]:+d}')
            for key, label in METRICS.items()), row_headings=True)
        current = {tuple(row[key] for key in IDENTITY): row for row in rows}
        for group, title in (('regressions', '回帰'), ('improvements', '正解に改善'), ('other_changes', 'その他の変化')):
            items = comparison[group]
            caption = f'{title} {len(items)}行'
            changes_html += f'<h3>{caption}</h3>'
            changes = []
            for item in items:
                key = tuple(item[field] for field in IDENTITY)
                changed_rows[key] = item['before']
                changes.append([escape(item['criterion']), *identity_cells(item), status_label(item, item['before']),
                                status_label(item, item['after']), evidence_links(current[key])])
            if changes:
                changes_html += table(caption, ('達成基準', *columns, '前回', '今回', '証拠'), changes)

    scopes = corpus_scope(score['corpus_digest'])
    checkpoints = {item['id']: item['check'] for item in core.modes.catalog()['checkpoints']} if scopes else {}

    criterion_overview, criterion_details = [], []
    for criterion, group in by_criterion.items():
        cid = escape(criterion)
        title = escape(core.audit.CRITERIA.get(criterion, {}).get('title', ''))
        pages = len({row['page_id'] for row in group})
        problem_count = sum(row['expected'] == 'failed' for row in group)
        statuses = Counter(row['status'] for row in group)
        scope = (scopes or {}).get(criterion)
        page_count = f'{pages} / {len(scope)}' if scope else str(pages)
        criterion_overview.append((f'<a href="#rows-{cid}">{cid} {title}</a>', page_count,
                                   fraction(statuses['detected'], problem_count),
                                   fraction(statuses['matched'], len(group) - problem_count),
                                   str(sum(statuses[key] for key in INCORRECT)),
                                   str(sum(statuses[key] for key in UNCONFIRMED))))
        detail_rows = []
        for row in group:
            cells = identity_cells(row)
            if comparison:
                key = tuple(row[field] for field in IDENTITY)
                cells.append(status_label(row, changed_rows.get(key, row['status'])))
            detail_rows.append(cells + [status_label(row, row['status']), evidence_links(row)])
        detail_columns = (*columns, '前回', '今回の判定', '証拠') if comparison else (*columns, '今回の判定', '証拠')
        criterion_details.append(f'<details><summary>{cid} {title}（{len(group)}件）</summary>'
                                 f'<div id="rows-{cid}" tabindex="-1">'
                                 + (scope_table(criterion, scope, group, checkpoints) if scope else '')
                                 + table(f'{criterion} の採点行', detail_columns, detail_rows, row_headings=True)
                                 + '</div></details>')

    if scopes:
        total_pages = sum(map(len, scopes.values()))
        scope_note = (f'問題集に登録された{total_pages}ページのうち、'
                      f'機械判定で採点する観点がある{score["pages"]}ページを収集対象にしました。'
                      '各達成基準のリンクから、採点した観点と、採点に含めなかったページや観点を確認できます。')
        others = ''.join(f'<details><summary>{escape(criterion)} {escape(core.audit.CRITERIA[criterion]["title"])}</summary>'
                         + scope_table(criterion, scope, [], checkpoints) + '</details>'
                         for criterion, scope in scopes.items() if criterion not in by_criterion)
        if others:
            criterion_details.append('<details><summary>採点対象のページがない達成基準</summary>' + others + '</details>')
    else:
        scope_note = '収集時と同じ版の問題集を参照できないため、採点対象に入らなかったページや観点は確認できません。'
    criterion_html = table('達成基準ごとの成績', ('達成基準', '採点対象 / 問題集のページ数' if scopes else '採点対象ページ数',
                           '検出 / 既知の問題', '正解 / 問題なし・該当なし', '誤判定', '確定判定なし'),
                           criterion_overview, row_headings=True)

    page_names = {row['page_id']: f"{row['criterion']} / {row['page']} ({row['page_id']})" for row in rows}
    extras = score['unmatched_findings']
    extra_html = ''
    if extras:
        extra_rows = [(escape(page_names.get(item['page_id'], item['page_id'])), escape(item['criterion']),
                       'PC幅' if item['environment'] == 'desktop' else 'スマホ相当幅',
                       escape(item['state']), escape(item['target']), escape(item['checkpoint']),
                       evidence_link(item['evidence'], '証拠') or '—') for item in extras]
        extra_html = ('<p>これらの指摘には、同じ観点・対象・状態の採点結果を対応付けられませんでした。'
                      '同じ要素への指摘も、画面幅や操作経路ごとに数えています。正誤は確認できていません。</p>'
                      + table('正解と照合できない指摘', ('ページ', '指摘の達成基準', '画面幅', '状態', '対象', 'ルール', '証拠'),
                              extra_rows, row_headings=True))
    comparison_nav = '<a href="#comparison">前回との差</a>' if comparison else ''
    return ('''<!doctype html><html lang="ja"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>URLからの機械検査ベンチマーク</title>
<style>
body{font:1rem/1.65 system-ui,sans-serif;color:#172334;padding:clamp(.75rem,3vw,2rem);margin:auto;max-width:76rem}
h1{font-size:clamp(1.5rem,3vw,2.25rem);line-height:1.3;margin-top:.6em}h2{margin-top:1.7em}
p{max-width:75ch}a{color:#0645ad}nav{display:flex;flex-wrap:wrap;gap:.4rem 1.2rem;margin-block:1rem}
.indicators{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,14rem),1fr));gap:1rem}
.indicators div{background:#eff5fa;border-top:3px solid #315a7c;border-radius:.25rem;padding:.8rem 1rem}
.indicators dd{margin:0;display:flex;align-items:baseline;flex-wrap:wrap;gap:.2rem .55rem}
.indicators strong{font-size:1.75rem}.indicators span{color:#344b61}
.scroll{overflow:auto;margin-block:.75rem 1.5rem}table{border-collapse:collapse;width:100%;min-width:28rem}
#breakdown + .scroll table{min-width:0}
caption{text-align:left;font-weight:600;padding:.3rem 0}td,th{padding:.45rem .6rem;border:1px solid #8a99a9;text-align:left;vertical-align:top}
th{background:#e9eff6}th[scope=row]{background:#f5f8fb}td,th,code{overflow-wrap:anywhere}
details{border:1px solid #8a99a9;border-radius:.25rem;margin-block:.5rem;padding:.3rem .65rem}
summary{font-weight:600;cursor:pointer;padding:.25rem 0}
:focus-visible{outline:3px solid #075da8;outline-offset:-3px}
</style>
<main><h1>URLからの機械検査ベンチマーク</h1>'''
            '<p>URLだけを渡した機械検査が、問題集に登録された期待結果をどこまで再現できたかを示します。</p>'
            + overview(score, counts)
            + f'<nav aria-label="レポート内"><a href="#criteria">達成基準ごとの成績と範囲</a>'
              f'<a href="#rows">全採点行</a><a href="#findings">正解と照合できない指摘</a>{comparison_nav}</nav>'
            + '<h2 id="criteria">達成基準ごとの成績と範囲</h2>'
            + f'<p>{scope_note} 収集完了は{score["completed_pages"]} / {score["pages"]}ページです。</p>'
            + criterion_html + changes_html + '<h2 id="rows">全採点行</h2>' + ''.join(criterion_details)
            + f'<h2 id="findings">正解と照合できない指摘 {len(extras)}件</h2>' + extra_html
            + f'<p>収集時の実装 <code>{escape(score["commit"])}</code> · <a href="{quote(json_name)}">採点JSON</a></p>'
            '</main></html>\n')
