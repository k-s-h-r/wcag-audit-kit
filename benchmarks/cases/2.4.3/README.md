# 2.4.3 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクのみを渡します。作成者による有限の対照例で、基準全体の網羅や独立した専門家による正解確認は未実施です。

## 元の代表例・操作例

入力画面を開き、直後のフォーカスが入力画面の操作へ続くか確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | after-open / 2.4.3-02 / `#subject` | failed: モーダルを開いた直後に、支援技術から隠される背景の別操作へフォーカスを移し、表示中の入力画面から操作順を外す。 |
| c02 | [p02.html](public/p02.html) | after-open / 2.4.3-02 / `#subject` | passed: 入力画面を開いた直後に、その画面の氏名入力へフォーカスを移す。 |
| c03 | [p03.html](public/p03.html) | third-level-open / 2.4.3-02 / `#level3-panel` | passed: 第3階層を展開してもフォーカスは開閉ボタンに残り、次のTabで見積管理へ移る。Escapeで開閉ボタンへ戻れる。 |
| c04 | [p04.html](public/p04.html) | third-level-open / 2.4.3-02 / `#level3-panel` | failed: 第3階層を開いた直後に、メニューを飛び越えて本文の資料請求#afterへフォーカスを移す。開いた階層の操作から順序を外す。 |

## 実際の階層内のフォーカス経路

製品、業務支援をキーで開いて末端リンクへ移動し、各段階のフォーカス・展開状態・URLを記録する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c05 | [p05.html](public/p05.html) | third-level / 2.4.3-02 / `#level3-panel` | failed: 3階層の循環又は本文への飛びを含む。 |
| c05 | [p05.html](public/p05.html) | third-level / 2.4.3-01 | 取得期待。適合・不適合とは別。3階層の循環又は本文への飛びを含む。 |
| c06 | [p06.html](public/p06.html) | third-level / 2.4.3-02 / `#level3-panel` | passed: 3階層の到達・復帰の順番を保つ。 |
| c06 | [p06.html](public/p06.html) | third-level / 2.4.3-01 | 取得期待。適合・不適合とは別。3階層の到達・復帰の順番を保つ。 |

## 入れ子のダイアログの離脱と復帰

予約を編集、住所の詳細の順に開き、内側でTab・Shift+Tab・Escapeを試す。閉じた後の親・本文へのフォーカスも確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c07 | [p07.html](public/p07.html) | inner-dialog / 2.4.3-02 / `#subject` | failed: 内側を閉じるとEscapeで閉じられない、又は外側を飛び越えて本文へフォーカスが移る。 |
| c08 | [p08.html](public/p08.html) | inner-dialog / 2.4.3-02 / `#subject` | passed: 内側を閉じると外側の開閉ボタンへ戻り、さらに外側を閉じて起点へ戻れる。 |

## ボタンで閉じた直後と次のTab

「予約内容を開く」から単一のダイアログを開き、「閉じる」をクリック・Enter・Spaceで操作します。入力ごとに閉じた直後と次のTabの位置を採点します。

| ケース | 入力 | 期待結果 |
| --- | --- | --- |
| c09 [p09.html](public/p09.html) | クリック・Enter・Space | 文書にフォーカスが戻り、次のTabで開き元より前の案内へ移る。 |
| c10 [p10.html](public/p10.html) | クリック・Enter・Space | 開き元にフォーカスが戻り、次のTabで次の案内へ移る。 |

```sh
python3 benchmarks/run.py collect --mode machine --criterion 2.4.3 --out /project/bench-focus-order-001
```

採点には、指定した経路での開く入力・閉じる入力・Tabと、同じ文書のフォーカスを記録した証拠を使います。入れ子のダイアログや、別の要素へ意図的に移る経路の適切さは追加確認です。

[3階層メニューの詳しい操作](../../NESTED-NAVIGATION.md)

[基準の検査手順](../../../skills/wcag-audit-kit/references/criteria/2.4.3.md) / [追加パターン一覧](../../PATTERNS.md) / [素材と条件](../../MATERIALS.md)
