# 画面・操作の調査と残る確認

調査状態: partial
画像の選択: states
実SRの選択: off

http://127.0.0.1:34897/visual-controls.html / 43aa9d581c3c--initial--desktop
Open preferences / 画面左上、見出し下の左側の青い矩形。対応先は#preferences-trigger。
画像: reviewed / 操作: tested / 実SR: skipped
画面上は青いボタン状。DOMではdivでroleなし・tabIndex=-1。4回のTab経路には現れず、ポインターではPreferencesが開き、Escapeで閉じた。
実施した操作: 画面で操作候補を列挙した
Tab移動を照合した
ポインターで開きEscapeで閉じる操作を照合した
残る確認: 入れ子の画面と未操作の対象を追加確認する。今回の予算では全状態の網羅を確認していない。
元の調査票: interaction-reviews/d4e5a041a8a3422b9bfaf6d34bf5bc13.json

http://127.0.0.1:34897/visual-controls.html / 43aa9d581c3c--initial--desktop
Open help / Open preferencesの右にある青いボタン。
画像: reviewed / 操作: tested / 実SR: skipped
ポインターでHelpを開き、Escapeで閉じると#help-triggerへフォーカスが戻った。続くEnterで再びHelpが開いた。
実施した操作: 開く・Escape・Enterでの再開を実行した
残る確認: 入れ子の画面と未操作の対象を追加確認する。今回の予算では全状態の網羅を確認していない。
元の調査票: interaction-reviews/d4e5a041a8a3422b9bfaf6d34bf5bc13.json

http://127.0.0.1:34897/visual-controls.html / 43aa9d581c3c--initial--desktop
Related page / 青い矩形の下、左側にある下線付きのリンク。
画像: reviewed / 操作: unverified / 実SR: skipped
画像上のリンクを候補に含めた。単独ページの収集はこのリンク先へ巡回していない。
実施した操作:
残る確認: リンクの開始・遷移後の状態は、この確認では実行していない
入れ子の画面と未操作の対象を追加確認する。今回の予算では全状態の網羅を確認していない。
元の調査票: interaction-reviews/d4e5a041a8a3422b9bfaf6d34bf5bc13.json

http://127.0.0.1:34897/visual-controls.html / 43aa9d581c3c--preferences--desktop
Display name / 画面中央のPreferences内、Demoと表示された入力欄。
画像: reviewed / 操作: unverified / 実SR: skipped
画像では入力欄にフォーカス枠があり、名前と初期値を確認した。値の編集は実行していない。
実施した操作:
残る確認: 実キーで値を編集し、その後の機能を確認する
入れ子の画面と未操作の対象を追加確認する。今回の予算では全状態の網羅を確認していない。
元の調査票: interaction-reviews/d4e5a041a8a3422b9bfaf6d34bf5bc13.json

http://127.0.0.1:34897/visual-controls.html / 43aa9d581c3c--preferences--desktop
Close preferences / 入力欄の下にある青いボタン。
画像: reviewed / 操作: unverified / 実SR: skipped
Escapeによる終了は操作ログで確認したが、この閉じるボタン自体のキー操作は未実施。
実施した操作:
残る確認: 閉じるボタン自体をキーで操作する
入れ子の画面と未操作の対象を追加確認する。今回の予算では全状態の網羅を確認していない。
元の調査票: interaction-reviews/d4e5a041a8a3422b9bfaf6d34bf5bc13.json

http://127.0.0.1:34897/visual-controls.html / 43aa9d581c3c--help--desktop
More options / Helpダイアログの下側、左の青いボタン。
画像: reviewed / 操作: tested / 実SR: skipped
画像上でMore optionsを確認し、ポインターとSpaceで入れ子の状態が開いた。Escapeで#moreへ戻る動作も記録した。
実施した操作: More optionsを押す
Escapeで閉じる
Spaceで再度開く
残る確認: 入れ子の画面と未操作の対象を追加確認する。今回の予算では全状態の網羅を確認していない。
元の調査票: interaction-reviews/d4e5a041a8a3422b9bfaf6d34bf5bc13.json

http://127.0.0.1:34897/visual-controls.html / 43aa9d581c3c--help--desktop
Close help / Help内、More optionsの右の青いボタン。
画像: reviewed / 操作: unverified / 実SR: skipped
HelpのEscape終了と起点への復帰は確認したが、Close helpボタンの実行は未確認。
実施した操作:
残る確認: この閉じるボタン自体の実行を確認する
入れ子の画面と未操作の対象を追加確認する。今回の予算では全状態の網羅を確認していない。
元の調査票: interaction-reviews/d4e5a041a8a3422b9bfaf6d34bf5bc13.json

http://127.0.0.1:34897/visual-controls.html / 43aa9d581c3c--nested--desktop
 /
画像: skipped / 操作: unverified / 実SR: skipped
状態のassertとキー入力は記録したが、画像上限3枚のためこの状態の画像は取得せず、実画面を確認していない。
実施した操作:
残る確認: 入れ子の画面と未操作の対象を追加確認する。今回の予算では全状態の網羅を確認していない。
元の調査票: interaction-reviews/d4e5a041a8a3422b9bfaf6d34bf5bc13.json
