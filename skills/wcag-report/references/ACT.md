# ACT Rulesを検証に使う

ACT Rulesは、適用条件、期待結果、前提、支援状況、用語と具体例を持つ公開試験ルール。W3Cの[ACT Rules一覧](https://www.w3.org/WAI/standards-guidelines/act/rules/)と[位置付け](https://www.w3.org/WAI/standards-guidelines/act/rules/about/)に従って使う。達成基準の全条件を一つのルールで確認できるとは限らない。

## 同梱した版

W3Cの公式リポジトリのコミット`9a2d7f903357eb728a0f83f00db75d4f32417ab4`を固定した。

| 区分 | 件数 | 扱い |
| --- | ---: | --- |
| approved：承認済み | 37 | 優先して適用条件を調べる |
| proposed：提案中 | 50 | 参考にした場合は未承認の状態と版を記録する |
| deprecated：廃止 | 7 | 過去の対応のみ保持し、新しい検査の根拠にはしない |

現行87ルールの本文、条件・用語・具体例を保存した。選択した各版の具体例は計1,177件。上流の例一覧は1,211件であり、承認済みルールの新しい提案版の例等も含む。ルールIDが同じという理由だけで別の版の例を混ぜない。

HTMLだけでなくSVG・XMLの例も含む。例を実行する場合はコンテンツ型を保持する。SVGをHTMLとして読み込むと、ブラウザーがHTMLのルートを補い、適用条件自体が変わる場合がある。

出典・完全な原文のハッシュは[sources/act/repository.json](sources/act/repository.json)、ライセンスは[sources/act/LICENSE.md](sources/act/LICENSE.md)。本文にコード例を収録したが、外部の画像・音声・動画等の全アセットを同梱したわけではない。利用する例の依存物を確認し、読み込めていない媒体を対象外にしない。

## 基準から必要なルールを選ぶ

```sh
python3 scripts/audit.py rules --criterion 1.1.1
python3 scripts/audit.py rules --criterion 1.1.1 --status approved
python3 scripts/audit.py rule --id 23a2a8
```

`case`にも、対象基準に関連するルールのID・状態・合否の対応と、基準別ガイドのパスが表示される。`references/act/<基準番号>.md`から関連ルールの本文へ進む。現行ルールがない基準も明記する。ルールがないことを検査不要の根拠にしない。

## 実ページで実行する

1. 選んだルールの本文を読み、Applicability、全Expectation、Assumptions、Accessibility Support、Glossaryを確認する。複合ルールはInput Rulesも読む。
2. そのページ・状態の適用対象を全件列挙する。例のコードと似ているかだけで適用を決めない。
3. 各対象の期待結果を具体化し、必要なブラウザー・支援技術・実画面・意味等を観察する。失敗・対象外の例も見て、方法が該当ケースを区別できるか確かめる。
4. ルールID、原文のSHA-256、承認状態、対象、実操作、実際の結果、証拠を記録する。基準の`tests_applied`に使用したIDと版を含める。
5. Accessibility Requirements Mappingを読み、達成基準の残りの条件・対象を検査してから基準全体を判定する。

## ルールの合否と基準の合否を対応付ける

`passed: further testing needed`は、ルールに通っても基準に追加検査が必要という意味。`inapplicable`も、そのルールの対象不在であり、基準の対象外へ自動変換しない。

`secondary`には、その基準よりルールが厳しいことや、間接的な関連が記載される場合がある。この場合、ルールの失敗だけでWCAG不適合とは限らない。`forConformance`、failed・passed・inapplicableの対応、前提と例外を原典と照合する。

例えば、画像の名前が空でないことを確かめるルールに通っても、名前が画像の目的を説明しているかは別に確認する。HTMLのタイトルのルールがSVGに適用されなくても、そのSVGを含む評価対象についてWCAGのタイトル要件が不要になるという意味ではない。

ACT Rulesは参考資料であり、特定のルールの採用自体をWCAGの必須要件にしない。独自の方法を使う場合も、どの条件を実際に検査したかを明らかにする。
