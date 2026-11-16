# 2.5.4 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクのみを渡します。作成者による有限の対照例で、基準全体の網羅や独立した専門家による正解確認は未実施です。

## 元の代表例・操作例

端末の振動で起動する機能のUI代替と動き応答の無効化を調べる。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | after-motion / 2.5.4-01 / `#subject` | failed: 動き専用でUI代替も無効化手段もない。 |
| c02 | [p02.html](public/p02.html) | after-motion / 2.5.4-01 / `#subject` | passed: UIの同等操作があり動きの応答を無効化できる。 |

## 実端末の動きとUI代替

実端末の動きとUI代替。操作と観察から判定し、表示だけで完了としない。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c03 | [p03.html](public/p03.html) | after-device-motion / 2.5.4-02 / `#subject` | failed: 実端末の動きに対して無効化や同等のUI操作がない。 |
| c04 | [p04.html](public/p04.html) | after-device-motion / 2.5.4-02 / `#subject` | passed: 実端末の動きに対して無効化と同じ機能のボタンがある。 |

必要な追加環境・確認：physical-device-motion, sensor-permission

[基準の検査手順](../../../references/criteria/2.5.4.md) / [追加パターン一覧](../../PATTERNS.md) / [素材と条件](../../MATERIALS.md)
