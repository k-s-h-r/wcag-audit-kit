"""Create review copies of three report layouts from a saved WCAG audit run."""
import argparse
from collections import Counter, defaultdict
from html import escape
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'skills/wcag-audit-kit/scripts'))

import audit
from browser_capture import normalize
import checksheet
import conformance
from page_workflow import page_result
from run_layout import href, ledger


LABELS = {'passed': '適合', 'failed': '不適合', 'inapplicable': '非適用', 'unverified': '未確認'}
PRINCIPLES = {'1': '知覚可能', '2': '操作可能', '3': '理解可能', '4': '堅牢'}


def link(url, label, *, accessible_name=None):
    name = f' aria-label="{escape(accessible_name)}"' if accessible_name else ''
    return f'<a href="{escape(url)}"{name}>{escape(label)}</a>'


def web_link(url, label):
    return link(url, label) if urlsplit(url).scheme in {'https', 'http'} else escape(label)


def fields(entries):
    return '<dl>' + ''.join(f'<dt>{escape(key)}</dt><dd>{escape(value)}</dd>' for key, value in entries) + '</dl>'


def table(caption, headings, rows):
    heads = ''.join(f'<th scope="col">{heading}</th>' for heading in headings)
    body = ''.join(f'<tr><th scope="row">{title}</th><td>{status}</td><td>{note}</td></tr>'
                   for title, status, note in rows)
    return (f'<table><caption>{caption}</caption><thead><tr>{heads}</tr></thead>'
            f'<tbody>{body}</tbody></table>')


def status(label, style):
    return f'<span class="status {style}">{escape(label)}</span>'


def conclusion(scope):
    style = {'conforms': 'passed', 'does_not_conform': 'failed', 'unverified': 'unverified'}[scope['status']]
    return status(scope['label'], style)


def standard(scope):
    return f"{scope['standard'].replace('WCAG-', 'WCAG ', 1)} {scope['level']}"


def remaining(scope):
    if not scope['remaining']:
        return ''
    items = ''.join(f'<li>{escape(reason)}</li>' for reason in scope['remaining'])
    return f'<section class="remaining"><h2>残る確認</h2><ul>{items}</ul></section>'


def document(title, subject, body, *, nav='', draft='レポート試作', subject_url=None):
    css = Path(__file__).with_name('report.css').read_text(encoding='utf-8')
    subject_html = web_link(subject_url, subject) if subject_url else escape(subject)
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} | {escape(subject)}</title><style>{css}</style></head>
<body><main><header>{nav}<p class="draft">{draft}</p><h1>{escape(title)}</h1>
<p class="subject">{subject_html}</p></header>{body}</main></body></html>\n'''


def criterion_rows(result, catalog, manifest):
    model = checksheet.build(result, catalog, manifest=manifest)
    findings = defaultdict(list)
    for item in model['failures']:
        findings[item['criterion']].append(f"{item['target']}（{item['observed']}）")
    return [dict(row, finding=checksheet.preview(findings[row['criterion']])) for row in model['rows']
            if row['kind'] == 'criterion' and row['status'] in LABELS]


def counts(rows):
    totals = Counter(row['status'] for row in rows)
    return '、'.join(f'{name} {totals[key]}件' for key, name in LABELS.items())


def criterion_name(row):
    return web_link(row['normative_url'], f"{row['criterion']} {row['title']}")


def judgment(row):
    value = LABELS[row['status']]
    if row['status'] == 'failed' and row['remaining']:
        value += '（未確認あり）'
    return status(value, row['status'])


def notes(row, run, file):
    text = '\n'.join(part for part in (row['finding'], row['notes'], row['remaining']) if part)
    links = []
    for raw in row['evidence_paths']:
        path = (run / raw).resolve()
        if path.is_relative_to(run) and path.is_file():
            links.append(link(href(file, path), f"{row['criterion']} の記録 {len(links) + 1}"))
    return (f'<div class="remarks">{escape(text or "記録なし")}</div>'
            + (f'<div class="proof screen-only">{" · ".join(links)}</div>' if links else ''))


def overview(title, scope, pages, metadata, has_pdf):
    nav = link('acr.html', 'ACR検討版')
    if has_pdf:
        nav += link('acr.pdf', 'ACR検討版 PDF')
    body = '<h2>検査概要</h2>' + fields([
        ('対象範囲の結論', scope['label']), ('目標', standard(scope)),
        ('検査期間', metadata.audit_period), ('報告日', metadata.report_date), ('検査方法', metadata.methods),
        ('範囲の補足', metadata.scope_note),
    ])
    rows = [(web_link(url, url), conclusion(page_scope),
             link(file, '達成状況を見る', accessible_name=f'達成状況を見る（{url}）') + '<br>' + counts(criteria)
             if file else '保存済みの検査票なし')
            for url, page_scope, file, criteria in pages]
    body += '<h2>対象ページ</h2>'
    body += table('ページ別の結果', ('対象URL', '範囲の結論', '達成基準の内訳'), rows) if rows else '<p>対象URLの記録なし</p>'
    return document('サイト検査結果の概要', title, body + remaining(scope),
                    nav=f'<nav class="screen-only" aria-label="関連レポート">{nav}</nav>')


def page_report(url, scope, rows, run, file):
    body = (f'<h2>検査概要</h2><p>{escape(standard(scope))} '
            f'{conclusion(scope)}</p><p>{escape(counts(rows))}</p>' + remaining(scope))
    body += '<h2>達成基準ごとの結果</h2>'
    for number, principle in PRINCIPLES.items():
        entries = [(criterion_name(row), judgment(row), notes(row, run, file))
                   for row in rows if row['criterion'].split('.')[0] == number]
        if entries:
            body += table(principle, ('達成基準', '判定', '確認結果・根拠'), entries)
    return document('ページ別 WCAG 達成状況', url, body, subject_url=url,
                    nav='<nav aria-label="関連レポート"><a href="index.html">サイト検査結果の概要</a></nav>')


def acr_report(title, scope, rows, run, file, metadata, has_pdf):
    body = '<h2>評価の概要</h2>' + fields([
        ('製品・版', metadata.product_version), ('報告日', metadata.report_date),
        ('連絡先', metadata.contact), ('評価方法', metadata.methods), ('検査期間', metadata.audit_period),
        ('対象規格・レベル', standard(scope)), ('範囲の補足', metadata.scope_note),
    ])
    urls = ''.join(f'<li>{web_link(url, url)}</li>' for url in scope['scope']['urls'])
    body += f'<h2>評価対象URL</h2><ul>{urls}</ul>' if urls else '<h2>評価対象URL</h2><p>記録なし</p>'
    body += remaining(scope) + '<h2>達成基準と評価の理由</h2>'
    for level in ('A', 'AA', 'AAA'):
        entries = [(criterion_name(row), judgment(row), notes(row, run, file))
                   for row in rows if row['level'] == level]
        if entries:
            body += table(f'レベル {level}', ('達成基準', '検査票の判定', '補足・説明'), entries)
    nav = link('index.html', 'サイト検査結果の概要')
    if has_pdf:
        nav += link('acr.pdf', 'PDFを開く')
    return document('アクセシビリティ適合レポート', title, body,
                    nav=f'<nav class="screen-only" aria-label="関連レポート">{nav}</nav>',
                    draft='ACR検討版 · 提出形式と判定語は要確認')


def print_pdf(html, chromium):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=chromium)
        page = browser.new_page()
        page.set_content(html)
        page.evaluate('document.fonts.ready')
        return page.pdf(prefer_css_page_size=True, print_background=True, tagged=True, outline=True)


def render(source, out, metadata, *, pdf=False, chromium=None):
    source = source.resolve()
    run = ledger(source).resolve()
    out = out.resolve()
    if out.is_relative_to(source) or out.is_relative_to(run) or out.exists():
        raise ValueError('保存済みrunの外に、新しい出力先を指定してください。')
    result = audit.outcomes(run)
    meta, catalog = audit.run_catalog(run)
    manifest = audit.load(run / 'capture-manifest.json')
    scope = conformance.build(result, meta['config'], catalog, manifest)
    title = metadata.title or result['url']
    cases_by_url = {normalize(case['page_url']) for case in result['cases']}
    output = {}
    pages = []
    for index, url in enumerate(scope['scope']['urls'], 1):
        if normalize(url) not in cases_by_url:
            pages.append((url, {'status': 'unverified', 'label': '未確認'}, None, []))
            continue
        page = page_result(run, url, result)
        page_scope = conformance.build(page, meta['config'], catalog, manifest)
        rows = criterion_rows(page, catalog, manifest)
        name = f'page-{index}.html'
        output[name] = page_report(url, page_scope, rows, run, out / name)
        pages.append((url, page_scope, name, rows))
    output['index.html'] = overview(title, scope, pages, metadata, pdf)
    output['acr.html'] = acr_report(title, scope, criterion_rows(result, catalog, manifest), run,
                                    out / 'acr.html', metadata, pdf)
    pdf_data = print_pdf(output['acr.html'], chromium) if pdf else None
    out.mkdir(parents=True)
    for name, html in output.items():
        (out / name).write_text(html, encoding='utf-8')
    if pdf_data:
        (out / 'acr.pdf').write_bytes(pdf_data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--pdf', action='store_true')
    parser.add_argument('--chromium', type=Path, help='PDFに既存のChromium系ブラウザーを使う場合の実行ファイル')
    parser.add_argument('--title')
    for field in ('product-version', 'report-date', 'audit-period', 'contact', 'methods', 'scope-note'):
        parser.add_argument('--' + field, default='未記録')
    args = parser.parse_args()
    try:
        render(args.run, args.out, args, pdf=args.pdf, chromium=args.chromium)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(args.out.resolve() / 'index.html')


if __name__ == '__main__':
    main()
