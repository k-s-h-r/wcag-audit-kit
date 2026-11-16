# 1.1.1 の検証用ページ

このディレクトリのREADMEとsuite.jsonは採点側の資料です。検査担当へ渡すページ・素材はpublic内だけです。

| ケース | ページ | 状態 | 確認観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | initial | 1.1.1-01 / `#figure` | 問題あり：情報を伝えるimgにaltや他の代替名がない。 |
| c01 | [p01.html](public/p01.html) | initial | 1.1.1-01 / `#summary` | 問題なし：imgにaltがある。有無の確認だけを採点する。 |
| c01 | [p01.html](public/p01.html) | initial | 1.1.1-01 / `#marker` | 問題なし：装飾の印に空altを設定している。空文字を欠落と同一視しない。 |
| c02 | [p02.html](public/p02.html) | initial | 1.1.1-01 / `#figure` | 問題なし：altは存在する。意味の誤りを属性の欠落として扱わない。 |
| c02 | [p02.html](public/p02.html) | initial | 1.1.1-01 / `#summary` | 問題なし：altは存在する。 |
| c02 | [p02.html](public/p02.html) | initial | 1.1.1-04 / `#figure` | 問題あり：画像は100万円から50万円へ減っているが、altが逆方向の変化を説明している。 |
| c02 | [p02.html](public/p02.html) | initial | 1.1.1-04 / `#summary` | 問題なし：画像の数値と増減を正しく説明している。 |
| c03 | [p03.html](public/p03.html) | opened | 1.1.1-04 / `#figure` | 問題なし：開いた詳細に元の数値と同じ情報がある。 |
| c04 | [p04.html](public/p04.html) | opened | 1.1.1-04 / `#figure` | 問題あり：詳細を開いても画像の数値を得られない。 |

期待結果は作成者が定めた確認観点の対照例です。基準全体の網羅や、独立した専門家による正解の確認は表していません。モードごとの評価条件はsuite.jsonに記録し、実際に検証できた範囲は実行後の採点結果に表示します。

[検査手順](../../../references/criteria/1.1.1.md) / [実行方法](../../README.md) / [ケースの追加](../../ADDING-CASES.md)
