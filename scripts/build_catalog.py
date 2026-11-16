#!/usr/bin/env python3
"""Generate per-criterion instructions from attributed sources and authored recipes."""
from pathlib import Path
from hashlib import sha256
import json

ROOT = Path(__file__).resolve().parents[1] / 'skills' / 'wcag-audit-kit'
PROCEDURE_VERSIONS = {
    **{f'1.2.{number}': '2' for number in range(1, 10)},
    '1.4.4': '2', '2.4.2': '2', '2.4.13': '2',
    **{ident: '2' for ident in ['2.2.1', '2.2.5', '2.2.6']},
    **{ident: '2' for ident in ['1.4.7', '1.4.8', '2.1.3', '2.2.3', '2.3.2', '2.4.12', '3.3.5']},
    **{ident: '3' for ident in ['1.2.1', '1.2.3', '1.2.8']},
}
SOURCE_NOTES = {
    '2.4.13': 'G195のTestsは1 CSS pxの境界相当と記述しているが、採用した勧告本文と公式解説は2 CSS pxの外周相当を要求する。G195だけで通過にせず、本文の面積、同一画素の前後3:1、例外を確認する。',
}


def build():
    recipes = {}
    for line in (ROOT / 'references/recipes.tsv').read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split('|')
        assert len(parts) == 6, parts
        ident, applies, targets, actions, expectation, methods = parts
        assert ident not in recipes
        recipes[ident] = {'applicability': applies, 'target_enumeration': targets,
                          'steps': actions.split('；'), 'expectation': expectation,
                          'methods': methods.split(',')}
    criteria = json.loads((ROOT / 'references/sources/criteria.json').read_text())
    assert set(recipes) == {c['id'] for c in criteria}
    techniques = json.loads((ROOT / 'references/sources/techniques.json').read_text())
    for c in criteria:
        c.update(recipes[c['id']])
        c.pop('understanding_text', None)
        c.pop('normative_text', None)
        c['procedure_version'] = PROCEDURE_VERSIONS.get(c['id'], '1')
        source_note = SOURCE_NOTES.get(c['id'])
        if source_note:
            c['source_note'] = source_note
        source_warning = (f'\n参照手順の注意：{source_note}\n[確認した相違と判断根拠](../SOURCE-DISCREPANCIES.md)を読む。\n'
                          if source_note else '')
        related = {u: techniques[u] for u in c['techniques'] if u in techniques}
        c['offline_techniques'] = len(related)
        steps = '\n'.join(f'{i}. {s}。' for i, s in enumerate(c['steps'], 1))
        guide = f"""# {c['id']} {c['title']} / {c['level']}

このファイルは検査の実行手順。ページを見ずにチェックを付けない。

## 本文・条件・例外を読む

最初に[この基準の本文と公式解説](../sources/{c['id']}.md)を全文読む。
英語本文が要件の根拠。この手順の短い説明だけで適合条件を増減しない。
用語の定義が判断に関わる場合は[勧告のスナップショット](../sources/wcag22.html)の定義を確認する。
{source_warning}

## このページの検査を作る

- 適用性の候補：{c['applicability']}。
- 列挙する対象：{c['target_enumeration']}。
- 観察方法：{', '.join(c['methods'])}。
- 対象のURL、表示状態、環境、全対象を識別できる実際のラベル・セレクター等を検査票へ記入する。
- 対象外の場合も、観察範囲・探した対象・不在の証拠を残す。未到達の状態は対象外にしない。

## 実行する

{steps}

判定する事項：{c['expectation']}。

具体的な道具は[観察方法の一覧](../methods.md)で確認する。

## 対象ごとに結果を残す

各対象に、実行した操作、観察した事実、期待結果との比較、結果、証拠を残す。
初期表示以外に対象がある場合は、対応する状態でも繰り返す。
原典の条件のどこまで検査できたかを明記し、未観察を合格に含めない。
実際の支援技術、専門的なメディア分析等が必要で利用できない場合は、残る操作と環境を指定して`cant_tell`を記録する。

## 具体的な公開試験手順

[この基準に関連する達成方法・失敗例のTests](../tests/{c['id']}.md)を参照する。
[ACT Rulesの対応](../act/{c['id']}.md)も調べ、承認状態・適用条件・基準との合否の対応を確認する。
十分な達成方法、推奨、失敗例を区別する。複数の代替方法をすべて必須にせず、ANDで組み合わされる条件とORの経路を原典で確認する。
適用した手順のIDと版、対象を記録する。この手順又はACTの一部ルールの通過だけで基準全体を合格にしない。
"""
        (ROOT / 'references/criteria' / (c['id'] + '.md')).write_text(guide)
        out = ROOT / 'references/tests' / (c['id'] + '.md')
        out.parent.mkdir(exist_ok=True)
        sections = [f"# {c['id']}の達成方法・失敗例\n\n出典は各項目に記載。参考資料であり、すべてを必須の実装方法として扱わない。\n"]
        if source_warning:
            sections.append(source_warning)
        for u, t in related.items():
            body = t['text']
            # Include concrete tests plus context where the source has no separate Tests section.
            fence='`'*(max([len(s) for s in __import__('re').findall(r'`+',body)]+[2])+1)
            sections.append(f"\n## {t['title']}\n\n出典: {t.get('source_url', u)}\n公開ページ: {u}\n\n{fence}text\n{body}\n{fence}\n")
        if not related:
            sections.append('対応するローカル試験手順がありません。本文と公式解説に沿って具体化し、根拠を記録してください。\n')
        out.write_text('\n'.join(sections))
    catalog = {'standard': 'WCAG-2.2', 'criteria': criteria,
               'recipe_sha256': sha256((ROOT / 'references/recipes.tsv').read_bytes()).hexdigest()}
    (ROOT / 'references/catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    print('Built', len(criteria), 'procedures and', len(criteria), 'related test documents')


if __name__ == '__main__':
    build()
