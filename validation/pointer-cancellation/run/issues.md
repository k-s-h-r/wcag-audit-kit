# 修正担当向けの不適合記録

この記録は検証結果です。製品コードの変更は行っていません。

予定範囲の検査完了: いいえ
結果: 未実施 324、検査通過 3、不適合 3
全基準と範囲の未確認は[HTMLレポート](report.html)又は[JSON](report.json)を参照してください。

## 2.5.2 ポインタのキャンセル

対象: http://127.0.0.1:4317/pointer-cancel-bad.html / initial / desktop

再現手順:

- 実画面とDOMから、このページの単一ポインターで操作する機能がLog an entryボタンのログ追加であることを確認した。
- Chromiumのマウス入力でボタンへ移動して押下し、対象へのtrusted pointerdownを確認した。
- 押下したまま取消領域へ移動して解放し、各段階の件数と解放先を記録した。
- Escape、Ctrl+Z、再読み込みでも状態を比較した。通常のクリックで機能することと、1件追加後の状態からの取消操作も検証した。
- No Down-Event、Abort or Undo、Up Reversal、Essentialを原典と照合した。UA自身の操作をページの機能として判定していない。

対象要素: #append — Log an entry（このページ唯一のポインター操作機能）
期待結果: 原典の4条件の少なくとも一つを満たし、誤ったポインター操作を防止又は所定の条件で取消・反転できる。
観察結果: 初期0件からは押下時点で1件へ増え、対象外で解放しても元に戻らず、Escape・Ctrl+Z・再読み込み後も残った。1件作成後も押下時点で2件になり取消できない。通常のログ追加で、打鍵の模倣や時刻精度が本質的な機能ではない。
証拠: evidence/a9735f8c161f--cancel-bad--desktop/actions.json, evidence/a9735f8c161f--cancel-bad--desktop/input-events.json, evidence/a9735f8c161f--cancel-bad--desktop/action-002.png, evidence/a9735f8c161f--cancel-bad--desktop/page.png, evidence/a9735f8c161f--cancel-bad--desktop/inventory.json, evidence/a9735f8c161f--commit--desktop/actions.json, evidence/a9735f8c161f--commit--desktop/input-events.json, evidence/a9735f8c161f--commit--desktop/page.png, evidence/a9735f8c161f--commit--desktop/inventory.json, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/actions.json, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/input-events.json, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/action-003.png, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/page.png, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/inventory.json, evidence/a9735f8c161f--initial--desktop/dom.html, evidence/a9735f8c161f--initial--desktop/inventory.json, evidence/attached/a9735f8c161f--initial--desktop--2.5.2/pointer-cancel-fixture.js

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#pointer-cancellation
このcaseの未確認: なし

## 2.5.2 ポインタのキャンセル

対象: http://127.0.0.1:4317/pointer-cancel-bad.html / cancel-bad / desktop

再現手順:

- 実画面とDOMから、このページの単一ポインターで操作する機能がLog an entryボタンのログ追加であることを確認した。
- Chromiumのマウス入力でボタンへ移動して押下し、対象へのtrusted pointerdownを確認した。
- 押下したまま取消領域へ移動して解放し、各段階の件数と解放先を記録した。
- Escape、Ctrl+Z、再読み込みでも状態を比較した。通常のクリックで機能することと、1件追加後の状態からの取消操作も検証した。
- No Down-Event、Abort or Undo、Up Reversal、Essentialを原典と照合した。UA自身の操作をページの機能として判定していない。

対象要素: #append — Log an entry（このページ唯一のポインター操作機能）
期待結果: 原典の4条件の少なくとも一つを満たし、誤ったポインター操作を防止又は所定の条件で取消・反転できる。
観察結果: 初期0件からは押下時点で1件へ増え、対象外で解放しても元に戻らず、Escape・Ctrl+Z・再読み込み後も残った。1件作成後も押下時点で2件になり取消できない。通常のログ追加で、打鍵の模倣や時刻精度が本質的な機能ではない。
証拠: evidence/a9735f8c161f--cancel-bad--desktop/actions.json, evidence/a9735f8c161f--cancel-bad--desktop/input-events.json, evidence/a9735f8c161f--cancel-bad--desktop/action-002.png, evidence/a9735f8c161f--cancel-bad--desktop/page.png, evidence/a9735f8c161f--cancel-bad--desktop/inventory.json, evidence/a9735f8c161f--commit--desktop/actions.json, evidence/a9735f8c161f--commit--desktop/input-events.json, evidence/a9735f8c161f--commit--desktop/page.png, evidence/a9735f8c161f--commit--desktop/inventory.json, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/actions.json, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/input-events.json, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/action-003.png, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/page.png, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/inventory.json, evidence/a9735f8c161f--cancel-bad--desktop/dom.html, evidence/a9735f8c161f--cancel-bad--desktop/inventory.json, evidence/attached/a9735f8c161f--cancel-bad--desktop--2.5.2/pointer-cancel-fixture.js

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#pointer-cancellation
このcaseの未確認: なし

## 2.5.2 ポインタのキャンセル

対象: http://127.0.0.1:4317/pointer-cancel-bad.html / commit / desktop

再現手順:

- 実画面とDOMから、このページの単一ポインターで操作する機能がLog an entryボタンのログ追加であることを確認した。
- Chromiumのマウス入力でボタンへ移動して押下し、対象へのtrusted pointerdownを確認した。
- 押下したまま取消領域へ移動して解放し、各段階の件数と解放先を記録した。
- Escape、Ctrl+Z、再読み込みでも状態を比較した。通常のクリックで機能することと、1件追加後の状態からの取消操作も検証した。
- No Down-Event、Abort or Undo、Up Reversal、Essentialを原典と照合した。UA自身の操作をページの機能として判定していない。

対象要素: #append — Log an entry（このページ唯一のポインター操作機能）
期待結果: 原典の4条件の少なくとも一つを満たし、誤ったポインター操作を防止又は所定の条件で取消・反転できる。
観察結果: 初期0件からは押下時点で1件へ増え、対象外で解放しても元に戻らず、Escape・Ctrl+Z・再読み込み後も残った。1件作成後も押下時点で2件になり取消できない。通常のログ追加で、打鍵の模倣や時刻精度が本質的な機能ではない。
証拠: evidence/a9735f8c161f--cancel-bad--desktop/actions.json, evidence/a9735f8c161f--cancel-bad--desktop/input-events.json, evidence/a9735f8c161f--cancel-bad--desktop/action-002.png, evidence/a9735f8c161f--cancel-bad--desktop/page.png, evidence/a9735f8c161f--cancel-bad--desktop/inventory.json, evidence/a9735f8c161f--commit--desktop/actions.json, evidence/a9735f8c161f--commit--desktop/input-events.json, evidence/a9735f8c161f--commit--desktop/page.png, evidence/a9735f8c161f--commit--desktop/inventory.json, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/actions.json, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/input-events.json, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/action-003.png, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/page.png, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/probe-ac5642a6/evidence/a9735f8c161f--probe--desktop/inventory.json, evidence/a9735f8c161f--commit--desktop/dom.html, evidence/a9735f8c161f--commit--desktop/inventory.json, evidence/attached/a9735f8c161f--commit--desktop--2.5.2/pointer-cancel-fixture.js

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#pointer-cancellation
このcaseの未確認: なし

