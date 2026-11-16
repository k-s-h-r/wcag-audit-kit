# 2.1.2 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクのみを渡します。作成者による有限の対照例で、基準全体の網羅や独立した専門家による正解確認は未実施です。

## 元の代表例・操作例

確認画面を開き、Tab/Shift+Tab/Escapeと閉じる操作で離脱できるか確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | opened / 2.1.2-02 / `#panel` | passed: 閉じる又はEscapeで離脱できる正常なモーダル。 |
| c02 | [p02.html](public/p02.html) | opened / 2.1.2-02 / `#panel` | failed: Tab/Shift+Tab/Escapeで入力欄から離れられず、閉じる操作へも到達できない。 |
| c03 | [p03.html](public/p03.html) | third-level-open / 2.1.2-02 / `#level3-panel` | passed: 第3階層からEscapeで第2階層の開閉ボタンへ戻り、さらにEscapeで第1階層へ戻れる。Tabでも後続の操作へ移動できる。 |
| c04 | [p04.html](public/p04.html) | third-level-open / 2.1.2-02 / `#level3-panel` | failed: 第3階層でTab・Shift+Tabがリンク2個の間を循環し、Escape・Enter・Spaceでも離脱できない。閉じるボタンはポインターだけで利用できる。 |

## 実際の階層内のフォーカス経路

製品、業務支援をキーで開いて末端リンクへ移動し、各段階のフォーカス・展開状態・URLを記録する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c05 | [p05.html](public/p05.html) | third-level / 2.1.2-02 / `#level3-panel` | failed: 3階層の循環又は本文への飛びを含む。 |
| c05 | [p05.html](public/p05.html) | third-level / 2.1.2-01 | 取得期待。適合・不適合とは別。3階層の循環又は本文への飛びを含む。 |
| c06 | [p06.html](public/p06.html) | third-level / 2.1.2-02 / `#level3-panel` | passed: 3階層の到達・復帰の順番を保つ。 |
| c06 | [p06.html](public/p06.html) | third-level / 2.1.2-01 | 取得期待。適合・不適合とは別。3階層の到達・復帰の順番を保つ。 |

## 入れ子のダイアログの離脱と復帰

予約を編集、住所の詳細の順に開き、内側でTab・Shift+Tab・Escapeを試す。閉じた後の親・本文へのフォーカスも確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c07 | [p07.html](public/p07.html) | inner-dialog / 2.1.2-02 / `#subject` | failed: 内側を閉じるとEscapeで閉じられない、又は外側を飛び越えて本文へフォーカスが移る。 |
| c08 | [p08.html](public/p08.html) | inner-dialog / 2.1.2-02 / `#subject` | passed: 内側を閉じると外側の開閉ボタンへ戻り、さらに外側を閉じて起点へ戻れる。 |

## コンボボックスのポップアップ

都市入力へキーで移動し、ArrowDownで候補を開く。選択・Escapeによる取消・Tabによる離脱と支援技術へ伝わる状態を確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c09 | [p09.html](public/p09.html) | combo-open / 2.1.2-02 / `#subject` | failed: ポップアップでキーを閉じ込める、又は展開・候補の状態が支援技術に伝わらない。 |
| c10 | [p10.html](public/p10.html) | combo-open / 2.1.2-02 / `#subject` | passed: ポップアップで展開・候補を識別でき、EscapeとTabで離脱できる。 |

## iframe内の移動と離脱

埋込みの編集を開き、iframe内の入力でTab・Shift+Tab・Escapeを試す。親文書と子文書のフォーカスを分けて記録する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c11 | [p11.html](public/p11.html) | frame-open / 2.1.2-02 / `#subject` | failed: iframe内でTabが循環し、Escapeでも親へ戻れない。 |
| c12 | [p12.html](public/p12.html) | frame-open / 2.1.2-02 / `#subject` | passed: iframe内でEscapeから親文書の起点へ戻れる。 |

必要な追加環境・確認：same-origin-frame

[3階層メニューの詳しい操作](../../NESTED-NAVIGATION.md)

[基準の検査手順](../../../skills/wcag-audit-kit/references/criteria/2.1.2.md) / [追加パターン一覧](../../PATTERNS.md) / [素材と条件](../../MATERIALS.md)
