"""Export a page-specific companion to the original machine audit report."""

from html import escape
from os.path import relpath
from pathlib import Path
from urllib.parse import quote


def evidence_cell(page, batch, directory):
    if 'evidence' not in page:
        return '証拠なし'
    source = batch / page['evidence']
    if (not source.is_relative_to(batch) or source.resolve() != source or not source.is_file()):
        raise ValueError('測定の証拠をバッチ内に確認できない')
    link = escape(quote(Path(relpath(source, directory)).as_posix()), quote=True)
    checksum = escape(page['sha256'])
    return f'<a href="{link}">axeの証拠</a><br><code>{checksum}</code>'


def reference_rows(comparison, url):
    groups = comparison['groups']
    matching_groups = [group for group in groups for page in group['pages'] if page['url'] == url]
    matching_unavailable = [page for page in comparison['unavailable'] if page['url'] == url]
    if len(matching_groups) + len(matching_unavailable) != 1:
        raise ValueError('バッチ内のページURLを一つに絞れない')

    current = matching_groups[0] if matching_groups else None
    rows = []
    for group in groups:
        observation = group['observation']
        measure = next(check['data'] for check in observation['node']['any']
                       if check['id'] == comparison['rule'])
        result = {'passes': '通過（axe）', 'violations': '問題あり（axe）'}[observation['bucket']]
        details = (f'{result} {measure["contrastRatio"]}:1（比較基準 {measure["expectedContrastRatio"]}）'
                   f'。前景 {measure["fgColor"]}、背景 {measure["bgColor"]}、'
                   f'文字サイズ {measure["fontSize"]}、太さ {measure["fontWeight"]}。')
        for page in group['pages']:
            if page['url'] == url:
                order, relation = 0, 'このページ'
            elif group is current:
                order, relation = 1, '同じ測定'
            else:
                order, relation = 2, '異なる測定' if current else '別のページで測定'
            rows.append((order, relation, page, details))

    for page in comparison['unavailable']:
        status = {'pending': '未着手', 'interrupted': '中断', 'failed': '収集失敗', 'completed': '測定を確認できず'}
        details = f'{status[page["status"]]}。{page["reason"]}'
        order, relation = (0, 'このページ') if page['url'] == url else (3, '比較できず')
        rows.append((order, relation, page, details))
    return sorted(rows, key=lambda row: row[0])


def export_page_html(batch, comparison, *, url, out):
    """Write a fresh reference without modifying the batch or original reports."""
    batch = Path(batch).resolve()
    out = Path(out)
    out = out.parent.resolve() / out.name
    if out.is_relative_to(batch):
        raise ValueError('比較元とは別の保存先にHTMLを出力する')

    rows = []
    for _, relation, page, details in reference_rows(comparison, url):
        proof = evidence_cell(page, batch, out.parent)
        rows.append(f'<tr><th scope="row">{escape(page["url"])}</th><td>{relation}</td>'
                    f'<td>{escape(details)}</td><td>{proof}</td></tr>')
    with out.open('x', encoding='utf-8') as report:
        report.write(f'''<!doctype html>
<html lang="ja">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>共通部品の文字コントラスト測定</title>
<style>
body {{ margin: 1rem; color: #222; background: white; font: 1rem/1.5 sans-serif; overflow-wrap: anywhere; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ text-align: left; vertical-align: top; border: 1px solid #aaa; padding: .5rem; overflow-wrap: anywhere; }}
thead {{ background: #eee; }}
</style>
<main>
<h1>共通部品の文字コントラスト測定</h1>
<dl>
<dt>ページ</dt><dd>{escape(url)}</dd>
<dt>対象要素</dt><dd><code>{escape(comparison["target"])}</code></dd>
<dt>環境</dt><dd>{escape(comparison["environment"])}</dd>
<dt>表示状態</dt><dd>初期表示</dd>
</dl>
<p>{escape(comparison["notice"])}</p>
<table>
<caption>同じ対象の測定と参照先</caption>
<thead><tr><th scope="col">ページ</th><th scope="col">このページとの比較</th>
<th scope="col">測定結果・理由</th><th scope="col">証拠とハッシュ</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</main>
</html>
''')
    return out
