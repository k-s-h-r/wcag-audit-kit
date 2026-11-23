"""Summarize and compare the grades from an ordinary URL-only run."""
from collections import Counter
from html import escape
from os.path import relpath
from pathlib import Path
from urllib.parse import quote

from benchmarks import core, url_only, url_only_machine_score


CORRECT = {'detected', 'matched'}
INCORRECT = {'false_positive', 'wrong_pass', 'wrong_control_outcome'}
IDENTITY = ('page_id', 'criterion', 'case', 'page', 'state', 'target', 'checkpoint', 'expected')
STATUS_LABEL = {
    'detected': '問題を検出', 'matched': '対照と一致', 'false_positive': '誤検出',
    'wrong_pass': '問題を通過・対象外と判定', 'wrong_control_outcome': '対照の判定が不一致',
    'observed_no_verdict': '観察済み・判定なし', 'state_or_route_unobserved': '状態・経路を未確認',
    'collection_error': '収集失敗・未実施',
}
METRICS = {
    'completed_pages': '収集が完了したページ', 'correct': '期待と一致した行', 'evaluated': '判定が出た行',
    'detected': '問題を検出した行', 'matched': '期待と一致した対照行', 'incorrect': '期待と不一致の行',
    'observed_no_verdict': '観察済み・判定なし', 'state_or_route_unobserved': '状態・経路を未確認',
    'collection_error': '収集失敗・未実施の行', 'unmatched_findings': '採点行に対応しない指摘',
}


def scorer_digest():
    runtime = core.RUNTIME / 'scripts'
    paths = [Path(module.__file__) for module in (url_only_machine_score, url_only)]
    paths += [runtime / f'{name}.py' for name in (
        'combobox', 'dialog_focus', 'keyboard_checks', 'keyboard_function', 'keyboard_trap', 'target_spacing',
    )]
    return core.digest({path.name: core.file_hash(path) for path in paths})


def summary(score):
    rows = score['rows']
    counts = Counter(row['status'] for row in rows)
    correct = sum(counts[status] for status in CORRECT)
    incorrect = sum(counts[status] for status in INCORRECT)
    return dict(rows=len(rows), completed_pages=score['completed_pages'], correct=correct, evaluated=correct + incorrect,
                detected=counts['detected'], matched=counts['matched'], incorrect=incorrect,
                **{key: counts[key] for key in ('observed_no_verdict', 'state_or_route_unobserved', 'collection_error')},
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


def table(caption, columns, rows):
    headings = ''.join(f'<th scope="col">{escape(label)}</th>' for label in columns)
    cells = ''.join('<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>' for row in rows)
    name = escape(caption, quote=True)
    return (f'<div class="scroll" role="region" aria-label="{name}" tabindex="0"><table>'
            f'<caption>{name}</caption><thead><tr>{headings}</tr></thead><tbody>{cells}</tbody></table></div>')


def render(score, run, output, json_name):
    counts = summary(score)
    comparison = score.get('comparison')
    rows = score['rows']
    failed = score['totals'].get('failed', 0)
    denominators = dict(completed_pages=score['pages'], correct=len(rows), evaluated=len(rows),
                        detected=failed, matched=len(rows) - failed)

    def display(values, key):
        return f'{values[key]} / {denominators[key]}' if key in denominators else str(values[key])

    summary_rows = []
    for key, label in METRICS.items():
        cells = [label, display(counts, key)]
        if comparison:
            baseline = comparison['baseline_summary']
            cells = [label, display(baseline, key), display(counts, key), f'{counts[key] - baseline[key]:+d}']
        summary_rows.append(cells)

    columns = ('ページ', 'ケース', '観点', '状態', '対象', '期待')

    def identity_cells(row):
        return [escape(value) for value in (f"{row['criterion']} / {row['page']} ({row['page_id']})",
                row['case'], row['checkpoint'], row['state'], row['target'],
                {'failed': '問題あり', 'passed': '問題なし', 'inapplicable': '対象外'}[row['expected']])]

    def evidence_links(row):
        items = []
        for environment, label in (('desktop', 'PC幅'), ('narrow', 'スマホ相当幅')):
            checks = row['environments'][environment]
            paths = dict.fromkeys([item['evidence'] for item in checks['verdicts']] or checks['reached'])
            for index, path in enumerate(paths, 1):
                if (source := core.local(run, path)).is_file():
                    href = quote(relpath(source, output.parent))
                    items.append(f'<a href="{href}">{label}の証拠 {index}</a>')
        return '<br>'.join(items) if items else '—'

    changes_html = ''
    changed_rows = {}
    if comparison:
        before = escape(comparison['baseline_commit'])
        after = escape(score['commit'])
        changes_html = f'<h2>前回との差</h2><p>前回 <code>{before}</code><br>今回 <code>{after}</code></p>'
        if comparison['scorer_match'] == 'unrecorded':
            changes_html += '<p>保存された採点結果に採点器の版がないため、採点器の一致は未確認です。</p>'
        current = {tuple(row[key] for key in IDENTITY): row for row in rows}
        for group, title in (('regressions', '回帰'), ('improvements', '正解に改善'), ('other_changes', 'その他の変化')):
            items = comparison[group]
            caption = f'{title} {len(items)}行'
            changes_html += f'<h3>{caption}</h3>'
            changes = []
            for item in items:
                key = tuple(item[field] for field in IDENTITY)
                changed_rows[key] = item['before']
                changes.append(identity_cells(item) + [STATUS_LABEL[item['before']], STATUS_LABEL[item['after']],
                                                       evidence_links(current[key])])
            if changes:
                changes_html += table(caption, (*columns, '前回', '今回', '証拠'), changes)

    detail_rows = []
    for row in rows:
        cells = identity_cells(row)
        if comparison:
            key = tuple(row[field] for field in IDENTITY)
            cells.append(STATUS_LABEL[changed_rows.get(key, row['status'])])
        detail_rows.append(cells + [STATUS_LABEL[row['status']], evidence_links(row)])
    summary_columns = ('指標', '前回', '今回', '増減') if comparison else ('指標', '今回')
    detail_columns = (*columns, '前回', '今回', '証拠') if comparison else (*columns, '今回', '証拠')
    return ('''<!doctype html><html lang="ja"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>URLからの機械検査ベンチマーク</title>
<style>body{font:1rem/1.6 sans-serif;color:#172334;padding:clamp(.75rem,3vw,2rem);margin:auto;max-width:80rem}
.scroll{overflow:auto;margin-block:1rem 1.5rem}table{border-collapse:collapse;width:100%;min-width:30rem}
caption{text-align:left;font-weight:bold;padding:.3rem}td,th{padding:.4rem .6rem;border:1px solid #6a788a;text-align:left;vertical-align:top}
th{background:#e9eff6}td{overflow-wrap:anywhere}a{color:#0645ad}
:focus-visible{outline:3px solid #075da8;outline-offset:-3px}code{overflow-wrap:anywhere}</style>
<main><h1>URLからの機械検査ベンチマーク</h1>'''
            f'<p>実装 <code>{escape(score["commit"])}</code> · <a href="{quote(json_name)}">採点JSON</a></p>'
            + table('集計', summary_columns, summary_rows) + changes_html
            + '<h2>全採点行</h2>' + table('期待結果と機械検査の判定', detail_columns, detail_rows) + '</main></html>\n')
