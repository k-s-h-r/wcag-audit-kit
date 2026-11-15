# 修正担当向けの不適合記録

この記録は検証結果です。製品コードの変更は行っていません。

予定範囲の検査完了: いいえ
結果: 未実施 219、不適合 1
全基準と範囲の未確認は[HTMLレポート](report.html)又は[JSON](report.json)を参照してください。

## 2.1.1 キーボード

対象: http://127.0.0.1:34897/visual-controls.html / initial / desktop

再現手順:

- 実画像から操作候補を列挙した
- Tab移動と実DOMを照合した
- ポインターで起動しEscapeで終了した
- 固定した試験用実装の全体と代替起動経路を確認した

対象要素: 画面左のOpen preferences / #preferences-trigger
期待結果: Preferencesを開く機能がキーボードインターフェースでも利用できる。
観察結果: ポインターでは開くが、Tabで到達できず、キーによる起動経路・同等機能が固定試験ページに存在しない。
証拠: evidence/43aa9d581c3c--initial--desktop/page.png, evidence/43aa9d581c3c--initial--desktop/inventory.json, evidence/43aa9d581c3c--initial--desktop/keyboard.json, evidence/43aa9d581c3c--preferences--desktop/actions.json, evidence/methods/visual-controls.html

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#keyboard
このcaseの未確認: 他の操作と状態の全機能は、この基準の判定では未検証。
