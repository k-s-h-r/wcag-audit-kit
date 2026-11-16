# 2.4.5 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクだけを渡します。

| ケース | ページ | 状態・観点 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [c01/start.html](public/c01/start.html), [c01/p01.html](public/c01/p01.html) | initial / 2.4.5-01 | failed: ページ群に単一のナビ以外の探索手段がない。 |
| c02 | [c02/start.html](public/c02/start.html), [c02/p02.html](public/c02/p02.html) | initial / 2.4.5-01 | passed: ナビとサイトマップの双方から目的ページへ到達できる。 |

操作：ページ群の各ページへ到達する独立した手段を調べる。

作成者による対照例です。全パターンの網羅・独立した専門家による正解確認は未実施。

[基準の検査手順](../../../references/criteria/2.4.5.md) / [実行方法](../../README.md)
