# 2.1.1 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクのみを渡します。作成者による有限の対照例で、基準全体の網羅や独立した専門家による正解確認は未実施です。

## 元の代表例・操作例

ポインター操作とキー操作で、数量変更の機能を最初から最後まで比較する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | initial / 2.1.1-01 / `#control` | passed: Tabで対象へ移動し、実キーを送出できる。 |
| c01 | [p01.html](public/p01.html) | initial / 2.1.1-02 / `#control` | passed: キーボードで数量を変更できる。重複したポインター専用部品の存在だけで失敗にしない。 |
| c02 | [p02.html](public/p02.html) | initial / 2.1.1-01 / `#control` | passed: Tabで対象へ移動し、実キーを送出できる。 |
| c02 | [p02.html](public/p02.html) | initial / 2.1.1-02 / `#control` | failed: focus可能でキーを送出できても、Enter/Spaceで数量が変わらない。 |
| c03 | [p03.html](public/p03.html) | initial / 2.1.1-02 / `#feature` | passed: キーボードで数量を変更できる。重複したポインター専用部品の存在だけで失敗にしない。 |
| c04 | [p04.html](public/p04.html) | keyboard-route / 2.1.1-02 / `#navigation` | passed: 2回の展開と第3階層リンクの実行をキーだけで行い、見積管理のページへ移動できる。 |
| c05 | [p05.html](public/p05.html) | keyboard-route / 2.1.1-02 / `#navigation` | failed: 第1階層は開くが、#level2はクリック専用のdivでEnter・Spaceに応答しない。ポインターでは第3階層のリンクへ進める。 |

## Shadow DOM内の操作と状態

初期表示からTabでShadow DOM内の詳細へ進み、Enterで開く。内部のフォーカスと開閉状態を記録する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c06 | [p06.html](public/p06.html) | shadow-open / 2.1.1-02 / `#inner-action` | failed: Shadow DOM内でクリックだけで開く、又は展開状態が更新されない。 |
| c07 | [p07.html](public/p07.html) | shadow-open / 2.1.1-02 / `#inner-action` | passed: Shadow DOM内でキーによる開閉と展開状態の変更を提供する。 |

## タブのフォーカス・選択・パネル

概要タブからArrowRightで料金タブへ移動してEnterを押し、フォーカス・パネル・選択状態を確認する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c08 | [p08.html](public/p08.html) | second-tab / 2.1.1-02 / `#tab-b` | failed: 次のタブへ移動した後にキーでパネルを開けない、又は選択状態が更新されない。 |
| c09 | [p09.html](public/p09.html) | second-tab / 2.1.1-02 / `#tab-b` | passed: 次のタブへ移動した後に料金パネルと選択状態を利用できる。 |

[3階層メニューの詳しい操作](../../NESTED-NAVIGATION.md)

[基準の検査手順](../../../references/criteria/2.1.1.md) / [追加パターン一覧](../../PATTERNS.md) / [素材と条件](../../MATERIALS.md)
