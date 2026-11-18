"""Reproduce apparent paragraphs and lists with different semantics in Chromium."""
import argparse
import asyncio
import json
from pathlib import Path
import shutil
import sys

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmarks.visual_structure_probe import collect


BODY = '営業時間中にお越しの方は、最初に入口の受付までお進みください。'
ITEMS = ['受付でお名前をお伝えください。', '入館証をお受け取りください。', '廊下の案内を確認してください。']
LABEL = '来訪時のご案内'


def heading_case(ident, tag='p', aria=False, emphasis='heading', label=LABEL):
    attributes = 'role="heading" aria-level="2"' if aria else ''
    return (f'<section id="{ident}"><{tag} id="{ident}-title" class="{emphasis}" {attributes}>{label}</{tag}>'
            f'<p>{BODY}</p></section>')


def list_case(ident, kind='plain', marker='・', items=ITEMS):
    wrapper = 'ul' if kind == 'native' else 'section'
    item = 'li' if kind == 'native' else 'p'
    group_role = 'role="list"' if kind == 'aria' else ''
    item_role = 'role="listitem"' if kind == 'aria' else ''
    contents = ''.join(f'<{item} id="{ident}-{i}" {item_role}>{marker}{text}</{item}>'
                       for i, text in enumerate(items, 1))
    return f'<{wrapper} class="group" id="{ident}" {group_role}>{contents}</{wrapper}>'


async def main(out):
    if out.exists():
        raise ValueError('試験結果には新しい保存先を指定する。')
    style = """
    body { font: 16px/1.5 sans-serif; }
    main { width: min(36rem, 100%); }
    .heading { font-size: 24px; font-weight: 700; margin: 0 0 8px; }
    .lead { font-weight: 700; margin: 0 0 8px; }
    .group { list-style: none; margin: 0; padding: 0; }
    .group p, .group li { margin: 0 0 3px; }
    #generated-list p::before { content: "・"; }
    """
    cases = [
        (heading_case('paragraph-heading'), '#paragraph-heading', ['heading']),
        (heading_case('html-heading', 'h2'), '#html-heading', []),
        (heading_case('aria-heading', aria=True), '#aria-heading', []),
        (heading_case('ordinary-emphasis', emphasis='lead'), '#ordinary-emphasis', []),
        (heading_case('styled-intro', label='はじめにお読みください'), '#styled-intro', ['heading']),
        (list_case('paragraph-list'), '#paragraph-list', ['list']),
        (list_case('html-list', 'native'), '#html-list', []),
        (list_case('aria-list', 'aria'), '#aria-list', []),
        (list_case('generated-list', marker=''), '#generated-list', []),
        (list_case('dot-in-prose', marker='', items=['フランス・ドイツの入国案内'] * 3), '#dot-in-prose', []),
        (list_case('too-short', items=ITEMS[:2]), '#too-short', []),
    ]
    observed = []
    appearances = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        try:
            page = await browser.new_page(viewport={'width': 900, 'height': 540})
            for html, selector, kinds in cases:
                await page.set_content(f'<!doctype html><html lang="ja"><style>{style}</style><main>{html}</main></html>')
                appearance = await page.locator(selector).screenshot(animations='allow', caret='initial')
                appearances[selector] = appearance
                result = await collect(page, selector)
                assert [candidate['kind'] for candidate in result['candidates']] == kinds, result
                for candidate in result['candidates']:
                    assert 'outcome' not in candidate
                observed.append(result)
            for first, second in (('#paragraph-heading', '#html-heading'), ('#paragraph-heading', '#aria-heading'),
                                  ('#paragraph-list', '#html-list'), ('#paragraph-list', '#aria-list')):
                assert appearances[first] == appearances[second], (first, second)
        finally:
            await browser.close()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'observed.json').write_text(json.dumps(observed, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({row['scope']: [c['kind'] for c in row['candidates']] for row in observed}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    asyncio.run(main(parser.parse_args().out))
