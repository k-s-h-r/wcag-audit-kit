# 1.2.7 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクのみを渡します。作成者による有限の対照例で、基準全体の網羅や独立した専門家による正解確認は未実施です。

## 元の代表例・操作例

音声と映像を比較し、代替の利用条件と例外を確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | initial / 1.2.7-01 / `#subject` | failed: 継続する音声に割り込めず、重要な映像情報の拡張解説もない。 |
| c02 | [p02.html](public/p02.html) | initial / 1.2.7-01 / `#subject` | inapplicable: 対象となる同期メディアがないため非適用。 |

## 拡張解説の内容と映像の停止・再開

解説付きで再生し、映像が止まる区間・拡張解説・映像の再開を確認する。解説と受付コードの内容も比較する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c03 | [p03.html](public/p03.html) | after-extension / 1.2.7-02 / `#subject` | failed: 拡張する時間は確保するが、解説の先頭の桁が9で、画面の7と異なる。 |
| c03 | [p03.html](public/p03.html) | after-extension / 1.2.7-01 / `#subject` | passed: 映像を止めて拡張解説を再生し、解説終了後に映像を再開できる。 |
| c04 | [p04.html](public/p04.html) | after-extension / 1.2.7-02 / `#subject` | passed: 拡張する時間は確保するが、解説が画面の20桁の受付コードと一致する。 |
| c04 | [p04.html](public/p04.html) | after-extension / 1.2.7-01 / `#subject` | passed: 映像を止めて拡張解説を再生し、解説終了後に映像を再開できる。 |

必要な追加環境・確認：audio-content-comparison

[基準の検査手順](../../../references/criteria/1.2.7.md) / [追加パターン一覧](../../PATTERNS.md) / [素材と条件](../../MATERIALS.md)
