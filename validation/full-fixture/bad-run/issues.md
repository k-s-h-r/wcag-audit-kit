# 修正担当向けの不適合記録

この記録は検証結果です。製品コードの変更は行っていません。

予定範囲の検査完了: いいえ
結果: 未実施 162、不適合 3
全基準と範囲の未確認は[HTMLレポート](report.html)又は[JSON](report.json)を参照してください。

## 4.1.2 名前 (name)・役割 (role)・値 (value)

対象: http://127.0.0.1:4322/ / initial / desktop

再現手順:

- URLを開き、実OrcaでCtrl+Home、Down、Downにより見出し・説明・部品の名前と役割を取得
- XTestのSpaceでOnにし、表示・aria-checked・AX checked・発話を比較
- SpaceでOffへ戻し、さらにOn→Offを繰り返し同じ不一致を再確認
- 全HTML・JSを読み、同じ部品の表示更新と公開状態の更新の欠落を対応付ける

対象要素: button#email-switch[role=checkbox]
期待結果: 利用者がOnへ切り替えたら公開されたcheckboxのcheckedもtrueとなり、Offへ戻せばfalseとなる。名前・役割に加え、実際の選択状態とその変更を支援技術が取得できる。
観察結果: このcaseはinitial、表示はOff。唯一の部品の名前Email notificationsとcheckboxの役割は取得できるが、表示Onのときもaria-checkedとAXのcheckedがfalseのまま。実Orcaの初期の名前・役割・not checkedは取得できたため、環境全体の沈黙ではない。XTestのSpaceによるOff→On→Off→On→Offで、Onの2回とも公開状態はfalse、発話はキーのechoだけで選択状態の変更を取得しなかった。無発話だけでなく、実表示と公開値の不一致を根拠に4.1.2の不適合とした。部品はこれ一つで、全選択値と復帰後の再操作を検査した。
証拠: evidence/methods/source-scope/index.html, evidence/methods/source-scope/reader-controls.js, evidence/methods/source-scope/server.py.txt, evidence/methods/native-reader/screen-reader.json, evidence/methods/native-reader/orca-debug.log, evidence/methods/native-reader/request.json, evidence/methods/native-reader/step-3.png, evidence/methods/native-reader/step-4.png, evidence/methods/native-reader/step-6.png, evidence/c8bf6e1d450e--initial--desktop/dom.html, evidence/c8bf6e1d450e--initial--desktop/inventory.json, evidence/c8bf6e1d450e--initial--desktop/page.png, evidence/c8bf6e1d450e--initial--desktop/accessibility-tree.json, evidence/c8bf6e1d450e--initial--desktop/actions.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#name-role-value
このcaseの未確認: なし

## 4.1.2 名前 (name)・役割 (role)・値 (value)

対象: http://127.0.0.1:4322/ / enabled / desktop

再現手順:

- URLを開き、実OrcaでCtrl+Home、Down、Downにより見出し・説明・部品の名前と役割を取得
- XTestのSpaceでOnにし、表示・aria-checked・AX checked・発話を比較
- SpaceでOffへ戻し、さらにOn→Offを繰り返し同じ不一致を再確認
- 全HTML・JSを読み、同じ部品の表示更新と公開状態の更新の欠落を対応付ける

対象要素: button#email-switch[role=checkbox]
期待結果: 利用者がOnへ切り替えたら公開されたcheckboxのcheckedもtrueとなり、Offへ戻せばfalseとなる。名前・役割に加え、実際の選択状態とその変更を支援技術が取得できる。
観察結果: このcaseはenabled、表示はOn。唯一の部品の名前Email notificationsとcheckboxの役割は取得できるが、表示Onのときもaria-checkedとAXのcheckedがfalseのまま。実Orcaの初期の名前・役割・not checkedは取得できたため、環境全体の沈黙ではない。XTestのSpaceによるOff→On→Off→On→Offで、Onの2回とも公開状態はfalse、発話はキーのechoだけで選択状態の変更を取得しなかった。無発話だけでなく、実表示と公開値の不一致を根拠に4.1.2の不適合とした。部品はこれ一つで、全選択値と復帰後の再操作を検査した。
証拠: evidence/methods/source-scope/index.html, evidence/methods/source-scope/reader-controls.js, evidence/methods/source-scope/server.py.txt, evidence/methods/native-reader/screen-reader.json, evidence/methods/native-reader/orca-debug.log, evidence/methods/native-reader/request.json, evidence/methods/native-reader/step-3.png, evidence/methods/native-reader/step-4.png, evidence/methods/native-reader/step-6.png, evidence/c8bf6e1d450e--enabled--desktop/dom.html, evidence/c8bf6e1d450e--enabled--desktop/inventory.json, evidence/c8bf6e1d450e--enabled--desktop/page.png, evidence/c8bf6e1d450e--enabled--desktop/accessibility-tree.json, evidence/c8bf6e1d450e--enabled--desktop/actions.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#name-role-value
このcaseの未確認: なし

## 4.1.2 名前 (name)・役割 (role)・値 (value)

対象: http://127.0.0.1:4322/ / disabled-again / desktop

再現手順:

- URLを開き、実OrcaでCtrl+Home、Down、Downにより見出し・説明・部品の名前と役割を取得
- XTestのSpaceでOnにし、表示・aria-checked・AX checked・発話を比較
- SpaceでOffへ戻し、さらにOn→Offを繰り返し同じ不一致を再確認
- 全HTML・JSを読み、同じ部品の表示更新と公開状態の更新の欠落を対応付ける

対象要素: button#email-switch[role=checkbox]
期待結果: 利用者がOnへ切り替えたら公開されたcheckboxのcheckedもtrueとなり、Offへ戻せばfalseとなる。名前・役割に加え、実際の選択状態とその変更を支援技術が取得できる。
観察結果: このcaseはdisabled-again、表示はOff。唯一の部品の名前Email notificationsとcheckboxの役割は取得できるが、表示Onのときもaria-checkedとAXのcheckedがfalseのまま。実Orcaの初期の名前・役割・not checkedは取得できたため、環境全体の沈黙ではない。XTestのSpaceによるOff→On→Off→On→Offで、Onの2回とも公開状態はfalse、発話はキーのechoだけで選択状態の変更を取得しなかった。無発話だけでなく、実表示と公開値の不一致を根拠に4.1.2の不適合とした。部品はこれ一つで、全選択値と復帰後の再操作を検査した。
証拠: evidence/methods/source-scope/index.html, evidence/methods/source-scope/reader-controls.js, evidence/methods/source-scope/server.py.txt, evidence/methods/native-reader/screen-reader.json, evidence/methods/native-reader/orca-debug.log, evidence/methods/native-reader/request.json, evidence/methods/native-reader/step-3.png, evidence/methods/native-reader/step-4.png, evidence/methods/native-reader/step-6.png, evidence/c8bf6e1d450e--disabled-again--desktop/dom.html, evidence/c8bf6e1d450e--disabled-again--desktop/inventory.json, evidence/c8bf6e1d450e--disabled-again--desktop/page.png, evidence/c8bf6e1d450e--disabled-again--desktop/accessibility-tree.json, evidence/c8bf6e1d450e--disabled-again--desktop/actions.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#name-role-value
このcaseの未確認: なし

