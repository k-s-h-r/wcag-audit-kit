# 修正担当向けの不適合記録

この記録は検証結果です。製品コードの変更は行っていません。

予定範囲の検査完了: いいえ
結果: 未実施 438、検査通過 1、不適合 1
全基準と範囲の未確認は[HTMLレポート](report.html)又は[JSON](report.json)を参照してください。

## 2.5.7 ドラッグ動作

対象: http://127.0.0.1:4317/drag-reorder-bad.html / initial / desktop

再現手順:

- 初期画面とDOMの全操作を調べ、ドラッグする対象がAlpha/Bravoの2項目だけであることを確認した。
- 通常収集と追加probeで、両項目の上下4方向への実ドラッグ、入力ログ、順序の中間値、実画像を照合した。
- Tabで項目へ移動し、矢印キーで並べ替えと復帰を実行した。
- 単一ポインターの移動ボタンを4通りクリックした。失敗例では両項目をクリックし、画面・DOM・ソースで他の経路も調べた。
- 通常の著者実装の並べ替えで、ドラッグは本質的ではなく、UAが独自に決める機能の例外も該当しないと確認した。

対象要素: #alpha の並べ替え（Alpha,BravoとBravo,Alphaの両順序）
期待結果: ドラッグで得る同じ並べ替え結果を、ドラッグなしの単一ポインター操作で得られる。
観察結果: 2項目の全2順序で、Alpha/Bravoを上下へ動かす4通りのHTML5ドラッグを実際に実行し、各段階がBA→AB→BA→ABとなった。trusted dragstart/dropと実画像を照合した。Tab・ArrowDown・ArrowUpは両方のページで順序を変更した。このページにはドラッグとLIの矢印キー操作だけがあり、対象のクリックは順序を変えなかった。画面・DOM・共有ソースを調べても別の移動ボタン、移動先の選択、数値入力等がない。キーボードによる代替だけでは2.5.7の単一ポインターの条件を満たさない。
証拠: evidence/2d82c455dd61--initial--desktop/page.png, evidence/2d82c455dd61--initial--desktop/dom.html, evidence/2d82c455dd61--initial--desktop/inventory.json, evidence/2d82c455dd61--drag--desktop/action-001.png, evidence/2d82c455dd61--drag--desktop/action-002.png, evidence/2d82c455dd61--drag--desktop/actions.json, evidence/2d82c455dd61--drag--desktop/dom.html, evidence/2d82c455dd61--drag--desktop/input-events.json, evidence/2d82c455dd61--keyboard--desktop/action-001.png, evidence/2d82c455dd61--keyboard--desktop/action-002.png, evidence/2d82c455dd61--keyboard--desktop/action-003.png, evidence/2d82c455dd61--keyboard--desktop/actions.json, evidence/2d82c455dd61--keyboard--desktop/dom.html, evidence/2d82c455dd61--keyboard--desktop/input-events.json, evidence/2d82c455dd61--pointer-only-attempt--desktop/action-001.png, evidence/2d82c455dd61--pointer-only-attempt--desktop/action-002.png, evidence/2d82c455dd61--pointer-only-attempt--desktop/action-003.png, evidence/2d82c455dd61--pointer-only-attempt--desktop/actions.json, evidence/2d82c455dd61--pointer-only-attempt--desktop/dom.html, evidence/2d82c455dd61--pointer-only-attempt--desktop/input-events.json, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/action-001.png, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/action-002.png, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/action-003.png, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/action-004.png, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/actions.json, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/dom.html, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/input-events.json, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/sources/drag-reorder-bad.html, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/sources/drag-reorder.css, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/sources/drag-reorder.js

対象要素: #bravo の並べ替え（Alpha,BravoとBravo,Alphaの両順序）
期待結果: ドラッグで得る同じ並べ替え結果を、ドラッグなしの単一ポインター操作で得られる。
観察結果: 2項目の全2順序で、Alpha/Bravoを上下へ動かす4通りのHTML5ドラッグを実際に実行し、各段階がBA→AB→BA→ABとなった。trusted dragstart/dropと実画像を照合した。Tab・ArrowDown・ArrowUpは両方のページで順序を変更した。このページにはドラッグとLIの矢印キー操作だけがあり、対象のクリックは順序を変えなかった。画面・DOM・共有ソースを調べても別の移動ボタン、移動先の選択、数値入力等がない。キーボードによる代替だけでは2.5.7の単一ポインターの条件を満たさない。
証拠: evidence/2d82c455dd61--initial--desktop/page.png, evidence/2d82c455dd61--initial--desktop/dom.html, evidence/2d82c455dd61--initial--desktop/inventory.json, evidence/2d82c455dd61--drag--desktop/action-001.png, evidence/2d82c455dd61--drag--desktop/action-002.png, evidence/2d82c455dd61--drag--desktop/actions.json, evidence/2d82c455dd61--drag--desktop/dom.html, evidence/2d82c455dd61--drag--desktop/input-events.json, evidence/2d82c455dd61--keyboard--desktop/action-001.png, evidence/2d82c455dd61--keyboard--desktop/action-002.png, evidence/2d82c455dd61--keyboard--desktop/action-003.png, evidence/2d82c455dd61--keyboard--desktop/actions.json, evidence/2d82c455dd61--keyboard--desktop/dom.html, evidence/2d82c455dd61--keyboard--desktop/input-events.json, evidence/2d82c455dd61--pointer-only-attempt--desktop/action-001.png, evidence/2d82c455dd61--pointer-only-attempt--desktop/action-002.png, evidence/2d82c455dd61--pointer-only-attempt--desktop/action-003.png, evidence/2d82c455dd61--pointer-only-attempt--desktop/actions.json, evidence/2d82c455dd61--pointer-only-attempt--desktop/dom.html, evidence/2d82c455dd61--pointer-only-attempt--desktop/input-events.json, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/action-001.png, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/action-002.png, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/action-003.png, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/action-004.png, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/actions.json, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/dom.html, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/probe-04f7bb80/evidence/2d82c455dd61--probe--desktop/input-events.json, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/sources/drag-reorder-bad.html, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/sources/drag-reorder.css, evidence/attached/2d82c455dd61--initial--desktop--2.5.7/sources/drag-reorder.js

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#dragging-movements
このcaseの未確認: なし

