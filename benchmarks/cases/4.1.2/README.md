# 4.1.2 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクのみを渡します。作成者による有限の対照例で、基準全体の網羅や独立した専門家による正解確認は未実施です。

## 元の代表例・操作例

展開ボタンの名前・役割と開閉後の状態を取得する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | after-open / 4.1.2-01 / `#subject` | failed: 独自部品にボタンの役割や展開状態の通知がない。 |
| c02 | [p02.html](public/p02.html) | after-open / 4.1.2-01 / `#subject` | passed: ボタンの名前・役割・展開状態とその変更がある。 |

## 独自部品の状態変更

独自部品の状態変更。操作と観察から判定し、表示だけで完了としない。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c03 | [p03.html](public/p03.html) | after-activate / 4.1.2-02 / `#subject` | failed: 表示上の有効状態とaria-checked=falseのままで支援技術へ変更が伝わらない。 |
| c04 | [p04.html](public/p04.html) | after-activate / 4.1.2-02 / `#subject` | passed: 表示上の有効状態とaria-checkedが同じ値へ変わる。 |

## Shadow DOM内の操作と状態

初期表示からTabでShadow DOM内の詳細へ進み、Enterで開く。内部のフォーカスと開閉状態を記録する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c05 | [p05.html](public/p05.html) | shadow-open / 4.1.2-02 / `#inner-action` | failed: Shadow DOM内でクリックだけで開く、又は展開状態が更新されない。 |
| c06 | [p06.html](public/p06.html) | shadow-open / 4.1.2-02 / `#inner-action` | passed: Shadow DOM内でキーによる開閉と展開状態の変更を提供する。 |

## コンボボックスのポップアップ

都市入力へキーで移動し、ArrowDownで候補を開く。選択・Escapeによる取消・Tabによる離脱と支援技術へ伝わる状態を確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c07 | [p07.html](public/p07.html) | combo-open / 4.1.2-02 / `#subject` | failed: ポップアップでキーを閉じ込める、又は展開・候補の状態が支援技術に伝わらない。 |
| c08 | [p08.html](public/p08.html) | combo-open / 4.1.2-02 / `#subject` | passed: ポップアップで展開・候補を識別でき、EscapeとTabで離脱できる。 |

## タブのフォーカス・選択・パネル

概要タブからArrowRightで料金タブへ移動してEnterを押し、フォーカス・パネル・選択状態を確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c09 | [p09.html](public/p09.html) | second-tab / 4.1.2-02 / `#tab-b` | failed: 次のタブへ移動した後にキーでパネルを開けない、又は選択状態が更新されない。 |
| c10 | [p10.html](public/p10.html) | second-tab / 4.1.2-02 / `#tab-b` | passed: 次のタブへ移動した後に料金パネルと選択状態を利用できる。 |

[基準の検査手順](../../../references/criteria/4.1.2.md) / [追加パターン一覧](../../PATTERNS.md) / [素材と条件](../../MATERIALS.md)
