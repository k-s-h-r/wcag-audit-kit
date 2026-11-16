# 1.4.13 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクのみを渡します。作成者による有限の対照例で、基準全体の網羅や独立した専門家による正解確認は未実施です。

## 元の代表例・操作例

ボタンへhover/focusし追加内容へポインター移動、Escapeで消去する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | after-open / 1.4.13-02 / `#subject` | failed: 追加内容がボタンから離れると消え、フォーカスでも表示できない。 |
| c02 | [p02.html](public/p02.html) | after-open / 1.4.13-02 / `#subject` | passed: 追加内容上へ移動でき、Escapeでも消せる。 |

## ホバーとフォーカスで出る内容

料金ボタンへポインターを重ね、追加内容上へ移動する。離れた後はキーでフォーカスし、Escapeで消去する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c03 | [p03.html](public/p03.html) | after-trigger / 1.4.13-02 / `#subject` | failed: 追加内容がポインターを外すと消え、キーのフォーカスでは表示されない。 |
| c03 | [p03.html](public/p03.html) | after-trigger / 1.4.13-01 | 取得期待。適合・不適合とは別。追加内容がポインターを外すと消え、キーのフォーカスでは表示されない。 |
| c04 | [p04.html](public/p04.html) | after-trigger / 1.4.13-02 / `#subject` | passed: 追加内容がフォーカスでも表示され、上へ移動でき、Escapeで消せる。 |
| c04 | [p04.html](public/p04.html) | after-trigger / 1.4.13-01 | 取得期待。適合・不適合とは別。追加内容がフォーカスでも表示され、上へ移動でき、Escapeで消せる。 |

[基準の検査手順](../../../skills/wcag-audit-kit/references/criteria/1.4.13.md) / [追加パターン一覧](../../PATTERNS.md) / [素材と条件](../../MATERIALS.md)
