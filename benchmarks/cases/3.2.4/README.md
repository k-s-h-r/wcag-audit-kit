# 3.2.4 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクだけを渡します。

| ケース | ページ | 状態・観点 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [c01/start.html](public/c01/start.html), [c01/p01.html](public/c01/p01.html) | comparison / 3.2.4-01 | failed: 同じ機能の識別名が変わる。 |
| c02 | [c02/start.html](public/c02/start.html), [c02/p02.html](public/c02/p02.html) | comparison / 3.2.4-01 | passed: 同じ機能の名前・繰返すヘルプの順序を維持する。 |

操作：start.htmlとp01/p02の繰返し部品を比較する。

作成者による対照例です。全パターンの網羅・独立した専門家による正解確認は未実施。

[基準の検査手順](../../../references/criteria/3.2.4.md) / [実行方法](../../README.md)
