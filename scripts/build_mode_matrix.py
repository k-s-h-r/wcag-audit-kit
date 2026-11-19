#!/usr/bin/env python3
"""Render the README matrix and detailed guide from the mode checkpoint catalog."""
import json
import sys
from skill_layout import ROOT, CANONICAL
sys.path.insert(0,str(CANONICAL/'scripts'))
from verification_modes import catalog,validate_catalog,SYMBOLS,MODES,LEGEND


def render(value):
    return _render(value).replace('](references/','](skills/wcag-audit-kit/references/').replace('python3 scripts/audit.py','python3 skills/wcag-audit-kit/scripts/audit.py')

def _render(value):
    head='''## モードを選ぶ

検査は「機械チェックのみ」「AI併用」「スクリーンリーダー併用」「AI＋スクリーンリーダー」から選べます。すべてのモードで機械検査を先に行います。AIによる画像・文章の比較と、実際の読み上げは、それぞれ必要な場合だけ有効にします。

```sh
python3 scripts/audit.py page-audit --url https://example.com/contact --out /project/run-machine --mode machine
python3 scripts/audit.py page-audit --url https://example.com/contact --out /project/run-ai --mode ai
python3 scripts/audit.py page-audit --url https://example.com/contact --out /project/run-sr --mode screen-reader
python3 scripts/audit.py page-audit --url https://example.com/contact --out /project/run-full --mode full
```

- `machine`：AIで内容を判断せず、スクリーンリーダーも使いません。機械ルール・実操作・数値計測を進めます。設定なしで新しく `page-audit` を始める場合の既定で、標準の画像収集を有効にするには `--screenshots` を指定します。
- `ai`：機械検査に加え、画像の代替文・見た目・文章の目的等を、スキルを使うAIが実際の証拠と比較します。実スクリーンリーダーは使いません。
- `screen-reader`：機械検査に加え、実際のスクリーンリーダーで操作・発話を確認します。AIで画像や意味を判断しません。対応するOS・ブラウザー・支援技術と、ページ専用の操作手順が必要です。
- `full`：機械検査・AIによる内容判断・実スクリーンリーダーのすべてを使います。音声の聴取・手話・閃光分析等、現在の手段が不足する確認は残ります。

CLIはAIサービスへ接続しません。AI併用の判断はスキルの実行環境で行い、実スクリーンリーダーは専用アダプターで対象ごとの操作を実行します。モードを選ぶだけで、その確認を実施したことにはなりません。`page-next`は選択したモードで進める観点と、省く観点・理由を返します。実行方法は[モードの仕様](references/verification-modes.md)を参照してください。

## モード別に確認できること

全86達成基準を確認観点ごとの131行で掲載します。例えば画像の代替文が「存在すること」と「画像の意味を伝えること」は別の確認です。AIを使わず人が内容を比較することもできますが、表の各モードにはその人による内容判断を含めていません。

'''
    head+=LEGEND+'\n\n'
    head+='○でも対象・状態・期待値を指定して実行する必要があります。△の観点で取得した証拠だけを、基準全体の適合へ置き換えません。×の項目は検証結果の「対象外」ではなく、未確認として残します。各観点の[具体的な処理・準備・人への引き継ぎ条件](references/verification-checkpoints.md)も確認できます。\n\n'
    head+='| 達成基準・手順 | レベル | 確認すること | 機械のみ | AI併用 | SR併用 | AI＋SR | 制約・残る確認 |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n'
    for r in value['checkpoints']:
        cells=[f"[{r['criterion']} {r['title']}](references/criteria/{r['criterion']}.md)",r['level'],
               f"[{r['check']}](references/verification-checkpoints.md#{r['id'].replace('.','')})",
               *[SYMBOLS[r['support'][m]] for m in MODES],r['note']]
        head+='| '+' | '.join(cells)+' |\n'
    return head+'\n方法の実証範囲は[方法ごとの準備状況](references/method-capabilities.json)、実施済みの試験は[実証状況](references/VERIFICATION-COVERAGE.md)を参照してください。対応表と保存済みの合否は別に管理します。\n\n'

def details(value):
    ref=json.loads((CANONICAL/'distribution.json').read_text())['proof_reference']
    return _details(value).replace('](../README.md)',f'](https://github.com/k-s-h-r/wcag-audit-kit/blob/{ref}/README.md)')

def _details(value):
    text='# 確認観点ごとの処理・準備・残る判断\n\n[モードの仕様](verification-modes.md)と[READMEの対応表](../README.md)から、必要な観点を開いて使います。対応表の原本は[確認観点の定義](verification-checkpoints.json)です。記号は実施結果ではありません。\n\n'
    for r in value['checkpoints']:
        text+=f'<a id="{r["id"].replace(".", "")}"></a>\n\n## {r["id"]} {r["title"]}\n\n'
        text+=f"確認すること：{r['check']}\n\n"
        for label,key in [('プログラムの処理と限界','program'),('実行方法・必要な準備','preparation'),('AIの補助','ai'),('人の確認・準備が必要になる場合','human'),('制約','note')]:
            text+=f'{label}：{r[key]}\n\n'
        text+=f"[基準の手順](criteria/{r['criterion']}.md)\n\n"
    # Source descriptions were relative to the repository README; this guide is in references/.
    text=text.replace('](references/','](')
    return text.rstrip()+'\n'

def main():
    value=validate_catalog(catalog());path=ROOT/'README.md';text=path.read_text()
    start=text.index('## モードを選ぶ\n') if '## モードを選ぶ\n' in text else text.index('## プログラム・AI・人による検証の分担\n')
    end=text.index('## 収録した検査内容\n',start)
    path.write_text(text[:start]+render(value)+text[end:])
    (CANONICAL/'references/verification-checkpoints.md').write_text(details(value))

if __name__=='__main__':main()
