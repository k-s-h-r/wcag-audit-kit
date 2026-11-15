# 修正担当向けの不適合記録

この記録は検証結果です。製品コードの変更は行っていません。

予定範囲の検査完了: いいえ
結果: 未実施 164、検査通過 3、対象外 1、不適合 4
全基準と範囲の未確認は[HTMLレポート](report.html)又は[JSON](report.json)を参照してください。

## 2.2.1 タイミング調整可能

対象: http://127.0.0.1:4326/timing.html?variant=bad / initial / desktop

再現手順:

- 全クライアントとサーバーのソースを読み、時間制限・活動・保存・失効・例外の対象を列挙
- 実際にサインインして4種の値を入力し、警告・延長・無操作失効を実時間で観察
- 期限後の保存とサーバー401を確認し、再認証後の元データと活動の継続・完了を比較
- 基準ごとに期間告知、時間依存、延長経路、保持の適用条件を分けて判定

対象要素: Demo session and draft form (#title, #notes, #category, #urgent)
期待結果: 各時間制限で、本文の無効化・調整・延長のいずれか又は根拠のある例外を満たす。延長経路なら少なくとも20秒と10回を確かめる。
観察結果: 既定6秒のサーバー無操作制限がある。警告から失効観察まで約2.001秒で、実際に延長できる回数も1回だけ。画面の無効化は非表示でサーバーもbadではoffを認めず、調整機能もない。全ソースから代替の適合経路がないことを確認した。通常の下書き入力であり、リアルタイム・本質的な制限・20時間超の例外には該当しない。
証拠: evidence/attached/9957e43aff2e--initial--desktop--2.2.1/case-binding.json, evidence/9957e43aff2e--initial--desktop/page.png, evidence/9957e43aff2e--initial--desktop/dom.html, evidence/9957e43aff2e--initial--desktop/inventory.json, evidence/9957e43aff2e--initial--desktop/axe.json, evidence/methods/timing/timing.html, evidence/methods/timing/timing_server.py, evidence/methods/timing/capture-executed.py.txt, evidence/methods/timing/source-hashes.json, evidence/methods/timing/comparison.json, evidence/methods/timing/results.json, evidence/methods/timing/bad-extend/observations.json, evidence/methods/timing/bad-extend/00-before-sign-in.png, evidence/methods/timing/bad-extend/01-draft-entered.png, evidence/methods/timing/bad-extend/02-warning-1.png, evidence/methods/timing/bad-extend/03-extension-1.png, evidence/methods/timing/bad-extend/04-expired.png, evidence/methods/timing/bad-extend/05-server-rejected-expired-save.png, evidence/methods/timing/bad-extend/06-reauthenticated.png

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#timing-adjustable
このcaseの未確認: なし

## 2.2.3 タイミング非依存

対象: http://127.0.0.1:4326/timing.html?variant=bad / initial / desktop

再現手順:

- 全クライアントとサーバーのソースを読み、時間制限・活動・保存・失効・例外の対象を列挙
- 実際にサインインして4種の値を入力し、警告・延長・無操作失効を実時間で観察
- 期限後の保存とサーバー401を確認し、再認証後の元データと活動の継続・完了を比較
- 基準ごとに期間告知、時間依存、延長経路、保持の適用条件を分けて判定

対象要素: Demo session and draft form (#title, #notes, #category, #urgent)
期待結果: 非インタラクティブな同期メディア又は定義上のリアルタイムイベント以外では、時間が活動の本質的な部分にならず、時間をかけても活動を完了できる。
観察結果: 全ソースと操作から、下書きの活動には必ず6秒の無操作制限があり、無効化や時間に依存しない経路がない。サーバーは失効した保存を401で拒否し、画面の4値を消去する。非インタラクティブな同期メディア又は定義上のリアルタイムイベントではない。Aの本質性や20時間超等の例外は適用していない。
証拠: evidence/attached/9957e43aff2e--initial--desktop--2.2.3/case-binding.json, evidence/9957e43aff2e--initial--desktop/page.png, evidence/9957e43aff2e--initial--desktop/dom.html, evidence/9957e43aff2e--initial--desktop/inventory.json, evidence/9957e43aff2e--initial--desktop/axe.json, evidence/methods/timing/timing.html, evidence/methods/timing/timing_server.py, evidence/methods/timing/capture-executed.py.txt, evidence/methods/timing/source-hashes.json, evidence/methods/timing/comparison.json, evidence/methods/timing/results.json, evidence/methods/timing/bad-extend/observations.json, evidence/methods/timing/bad-extend/00-before-sign-in.png, evidence/methods/timing/bad-extend/01-draft-entered.png, evidence/methods/timing/bad-extend/02-warning-1.png, evidence/methods/timing/bad-extend/03-extension-1.png, evidence/methods/timing/bad-extend/04-expired.png, evidence/methods/timing/bad-extend/05-server-rejected-expired-save.png, evidence/methods/timing/bad-extend/06-reauthenticated.png

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#no-timing
このcaseの未確認: なし

## 2.2.5 再認証

対象: http://127.0.0.1:4326/timing.html?variant=bad / initial / desktop

再現手順:

- 全クライアントとサーバーのソースを読み、時間制限・活動・保存・失効・例外の対象を列挙
- 実際にサインインして4種の値を入力し、警告・延長・無操作失効を実時間で観察
- 期限後の保存とサーバー401を確認し、再認証後の元データと活動の継続・完了を比較
- 基準ごとに期間告知、時間依存、延長経路、保持の適用条件を分けて判定

対象要素: Demo session and draft form (#title, #notes, #category, #urgent)
期待結果: 認証失効後に再認証しても元のデータと追加変更を失わず、活動を継続・完了できる。
観察結果: 同じ4値を入力して実際の無操作失効を待った。失効時にform.resetで全4値が初期値へ戻り、期限後のSaveはサーバーの401で拒否された。実際に再認証してもタイトル・本文は空、CategoryはDraft、Urgent=falseのままで、元の活動データを使って完了できなかった。再入力を元データの保持と数えていない。
証拠: evidence/attached/9957e43aff2e--initial--desktop--2.2.5/case-binding.json, evidence/9957e43aff2e--initial--desktop/page.png, evidence/9957e43aff2e--initial--desktop/dom.html, evidence/9957e43aff2e--initial--desktop/inventory.json, evidence/9957e43aff2e--initial--desktop/axe.json, evidence/methods/timing/timing.html, evidence/methods/timing/timing_server.py, evidence/methods/timing/capture-executed.py.txt, evidence/methods/timing/source-hashes.json, evidence/methods/timing/comparison.json, evidence/methods/timing/results.json, evidence/methods/timing/bad-extend/observations.json, evidence/methods/timing/bad-extend/00-before-sign-in.png, evidence/methods/timing/bad-extend/01-draft-entered.png, evidence/methods/timing/bad-extend/02-warning-1.png, evidence/methods/timing/bad-extend/03-extension-1.png, evidence/methods/timing/bad-extend/04-expired.png, evidence/methods/timing/bad-extend/05-server-rejected-expired-save.png, evidence/methods/timing/bad-extend/06-reauthenticated.png

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#re-authenticating
このcaseの未確認: なし

## 2.2.6 タイムアウト

対象: http://127.0.0.1:4326/timing.html?variant=bad / initial / desktop

再現手順:

- 全クライアントとサーバーのソースを読み、時間制限・活動・保存・失効・例外の対象を列挙
- 実際にサインインして4種の値を入力し、警告・延長・無操作失効を実時間で観察
- 期限後の保存とサーバー401を確認し、再認証後の元データと活動の継続・完了を比較
- 基準ごとに期間告知、時間依存、延長経路、保持の適用条件を分けて判定

対象要素: Demo session and draft form (#title, #notes, #category, #urgent)
期待結果: 無操作でデータを失う場合、その無操作時間が利用者へ告知されるか、無操作でも20時間超保存される。
観察結果: このページは6秒の無操作セッション失効で、入力した4値を全て初期化する。活動開始時の説明はSign in to edit a draft.だけで、無操作時間を伝えず、直前警告にも期間の記述がない。失効・401・再認証後の空データを実際に確認し、全ソースで20時間超の保存又は別の復元がないことを確認した。
証拠: evidence/attached/9957e43aff2e--initial--desktop--2.2.6/case-binding.json, evidence/9957e43aff2e--initial--desktop/page.png, evidence/9957e43aff2e--initial--desktop/dom.html, evidence/9957e43aff2e--initial--desktop/inventory.json, evidence/9957e43aff2e--initial--desktop/axe.json, evidence/methods/timing/timing.html, evidence/methods/timing/timing_server.py, evidence/methods/timing/capture-executed.py.txt, evidence/methods/timing/source-hashes.json, evidence/methods/timing/comparison.json, evidence/methods/timing/results.json, evidence/methods/timing/bad-extend/observations.json, evidence/methods/timing/bad-extend/00-before-sign-in.png, evidence/methods/timing/bad-extend/01-draft-entered.png, evidence/methods/timing/bad-extend/02-warning-1.png, evidence/methods/timing/bad-extend/03-extension-1.png, evidence/methods/timing/bad-extend/04-expired.png, evidence/methods/timing/bad-extend/05-server-rejected-expired-save.png, evidence/methods/timing/bad-extend/06-reauthenticated.png

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#timeouts
このcaseの未確認: なし

