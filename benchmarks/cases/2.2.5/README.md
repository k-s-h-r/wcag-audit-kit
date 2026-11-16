# 2.2.5 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクだけを渡します。

| ケース | ページ | 状態・観点 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | after-reauthentication / 2.2.5-01 | failed: 再認証時に下書きを失う。 |
| c02 | [p02.html](public/p02.html) | after-reauthentication / 2.2.5-01 | passed: 再認証後も下書きが残る。 |

操作：下書きを入力し、セッション切れ、再認証の順に操作する。

作成者による対照例です。全パターンの網羅・独立した専門家による正解確認は未実施。

[基準の検査手順](../../../skills/wcag-audit-kit/references/criteria/2.2.5.md) / [実行方法](../../README.md)
