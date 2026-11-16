# 1.1.1 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクのみを渡します。作成者による有限の対照例で、基準全体の網羅や独立した専門家による正解確認は未実施です。

## 元の代表例・操作例

初期表示を確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | initial / 1.1.1-01 / `#figure` | failed: 情報を伝えるimgにaltや他の代替名がない。 |
| c01 | [p01.html](public/p01.html) | initial / 1.1.1-01 / `#summary` | passed: imgにaltがある。有無の確認だけを採点する。 |
| c01 | [p01.html](public/p01.html) | initial / 1.1.1-01 / `#marker` | passed: 装飾の印に空altを設定している。空文字を欠落と同一視しない。 |
| c02 | [p02.html](public/p02.html) | initial / 1.1.1-01 / `#figure` | passed: altは存在する。意味の誤りを属性の欠落として扱わない。 |
| c02 | [p02.html](public/p02.html) | initial / 1.1.1-01 / `#summary` | passed: altは存在する。 |
| c02 | [p02.html](public/p02.html) | initial / 1.1.1-04 / `#figure` | failed: 画像は100万円から50万円へ減っているが、altが逆方向の変化を説明している。 |
| c02 | [p02.html](public/p02.html) | initial / 1.1.1-04 / `#summary` | passed: 画像の数値と増減を正しく説明している。 |
| c03 | [p03.html](public/p03.html) | opened / 1.1.1-04 / `#figure` | passed: 開いた詳細に元の数値と同じ情報がある。 |
| c04 | [p04.html](public/p04.html) | opened / 1.1.1-04 / `#figure` | failed: 詳細を開いても画像の数値を得られない。 |

## 背景画像・SVG・canvasの代替

背景画像、inline SVG、canvas、装飾のSVGを区別し、それぞれの目的・情報と代替内容を確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c05 | [p05.html](public/p05.html) | initial / 1.1.1-04 / `#background-chart` | failed: 3種類の図が半減を伝える。画像として識別する名前・代替内容がない。 |
| c05 | [p05.html](public/p05.html) | initial / 1.1.1-04 / `#inline-chart` | failed: 3種類の図が半減を伝える。画像として識別する名前・代替内容がない。 |
| c05 | [p05.html](public/p05.html) | initial / 1.1.1-04 / `#canvas-chart` | failed: 3種類の図が半減を伝える。画像として識別する名前・代替内容がない。 |
| c05 | [p05.html](public/p05.html) | initial / 1.1.1-02 | 取得期待。適合・不適合とは別。3種類の図が半減を伝える。画像として識別する名前・代替内容がない。 |
| c06 | [p06.html](public/p06.html) | initial / 1.1.1-04 / `#background-chart` | passed: 3種類の図が半減を伝える。同等の代替名がある。 |
| c06 | [p06.html](public/p06.html) | initial / 1.1.1-04 / `#inline-chart` | passed: 3種類の図が半減を伝える。同等の代替名がある。 |
| c06 | [p06.html](public/p06.html) | initial / 1.1.1-04 / `#canvas-chart` | passed: 3種類の図が半減を伝える。同等の代替名がある。 |
| c06 | [p06.html](public/p06.html) | initial / 1.1.1-02 | 取得期待。適合・不適合とは別。3種類の図が半減を伝える。同等の代替名がある。 |
| c11 | [p11.html](public/p11.html) | initial / 1.1.1-04 / `#subject` | passed: SVGは同じボタンの保存という表示ラベルを重複する装飾。別の名前を要求して誤検出しない。 |
| c11 | [p11.html](public/p11.html) | initial / 1.1.1-02 | 取得期待。適合・不適合とは別。SVGは同じボタンの保存という表示ラベルを重複する装飾。別の名前を要求して誤検出しない。 |

## 代替説明が実SRに届くか

画像の代替を実際のスクリーンリーダーで利用できるか確認する。AXの取得だけで実発話を確認済みにしない。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c07 | [p07.html](public/p07.html) | initial / 1.1.1-03 / `#subject` | failed: 画像と代替をAXから隠し、他の等価な説明がない。 |
| c08 | [p08.html](public/p08.html) | initial / 1.1.1-03 / `#subject` | passed: 必要な代替が実SRへ提供される構造である。実発話での照合が必要。 |

必要な追加環境・確認：real-screen-reader

## 操作後に追加される画像

図表を読み込むボタンを押して追加表示を待ち、初期表示にない画像と代替を確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c09 | [p09.html](public/p09.html) | after-load / 1.1.1-01 / `#subject` | failed: 初期状態にない画像が追加され、代替文がない。初期表示だけの検査では見落とす。 |
| c10 | [p10.html](public/p10.html) | after-load / 1.1.1-01 / `#subject` | passed: 初期状態にない画像が追加され、代替文も設定される。 |

[基準の検査手順](../../../skills/wcag-audit-kit/references/criteria/1.1.1.md) / [追加パターン一覧](../../PATTERNS.md) / [素材と条件](../../MATERIALS.md)
