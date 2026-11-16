# 1.2.6 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクのみを渡します。作成者による有限の対照例で、基準全体の網羅や独立した専門家による正解確認は未実施です。

## 元の代表例・操作例

音声と映像を比較し、代替の利用条件と例外を確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | initial / 1.2.6-01 / `#subject` | failed: 収録済みの発話の手話通訳がない。 |
| c02 | [p02.html](public/p02.html) | initial / 1.2.6-01 / `#subject` | inapplicable: 対象となる同期メディアがないため非適用。 |

## 実際の手話素材と発話の意味

再生ボタンで発話とASL映像を同時に再生し、元の発話の情報を手話でも得られるか比較する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c03 | [p03.html](public/p03.html) | initial / 1.2.6-02 / `#subject` | failed: 出典がHelloとするASL素材にGoodbyeの発話を組み合わせ、意味が一致しない。 |
| c03 | [p03.html](public/p03.html) | initial / 1.2.6-01 / `#subject` | passed: 実際のASL動画を提供し、音声と同時に再生できる。 |
| c04 | [p04.html](public/p04.html) | initial / 1.2.6-02 / `#subject` | passed: 出典がHelloとするASL素材にHelloの発話を組み合わせる。 |
| c04 | [p04.html](public/p04.html) | initial / 1.2.6-01 / `#subject` | passed: 実際のASL動画を提供し、音声と同時に再生できる。 |

必要な追加環境・確認：qualified-sign-language-comparison

[基準の検査手順](../../../references/criteria/1.2.6.md) / [追加パターン一覧](../../PATTERNS.md) / [素材と条件](../../MATERIALS.md)
