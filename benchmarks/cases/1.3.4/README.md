# 1.3.4 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクのみを渡します。作成者による有限の対照例で、基準全体の網羅や独立した専門家による正解確認は未実施です。

## 元の代表例・操作例

幅320高さ640と幅640高さ320で操作の可否を確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | initial / 1.3.4-01 / `#subject` | failed: 縦向きで必須操作が非表示となる。本質的な向きの制約はない。 |
| c02 | [p02.html](public/p02.html) | initial / 1.3.4-01 / `#subject` | passed: 両方の向きで保存できる。 |

## 実端末の向き情報による利用制限

実端末の向き情報による利用制限。操作と観察から判定し、表示だけで完了としない。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c03 | [p03.html](public/p03.html) | after-physical-rotation / 1.3.4-02 / `#subject` | failed: 実端末の向きに対して縦向きで本質的でない保存操作を隠す。 |
| c04 | [p04.html](public/p04.html) | after-physical-rotation / 1.3.4-02 / `#subject` | passed: 実端末の向きに対して両向きで保存操作を利用できる。 |

必要な追加環境・確認：orientation-permission, physical-device-orientation

[基準の検査手順](../../../skills/wcag-audit-kit/references/criteria/1.3.4.md) / [追加パターン一覧](../../PATTERNS.md) / [素材と条件](../../MATERIALS.md)
