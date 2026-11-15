# 修正担当向けの不適合記録

この記録は検証結果です。製品コードの変更は行っていません。

予定範囲の検査完了: いいえ
結果: 検査通過 1342、対象外 762、判断保留 80、不適合 16
全基準と範囲の未確認は[HTMLレポート](report.html)又は[JSON](report.json)を参照してください。

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/ / initial / desktop

再現手順:

- 対象http://127.0.0.1:4330/と、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/ への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/eed089bd8f88--initial--desktop/page.png, evidence/eed089bd8f88--initial--desktop/inventory.json, evidence/eed089bd8f88--initial--desktop/dom.html, evidence/eed089bd8f88--initial--desktop/accessibility-tree.json, evidence/eed089bd8f88--initial--desktop/actions.json, evidence/eed089bd8f88--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/ / anonymous / desktop

再現手順:

- 対象http://127.0.0.1:4330/と、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/ への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/eed089bd8f88--anonymous--desktop/page.png, evidence/eed089bd8f88--anonymous--desktop/inventory.json, evidence/eed089bd8f88--anonymous--desktop/dom.html, evidence/eed089bd8f88--anonymous--desktop/accessibility-tree.json, evidence/eed089bd8f88--anonymous--desktop/actions.json, evidence/eed089bd8f88--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/ / dialog-open / desktop

再現手順:

- 対象http://127.0.0.1:4330/と、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/ への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/eed089bd8f88--dialog-open--desktop/page.png, evidence/eed089bd8f88--dialog-open--desktop/inventory.json, evidence/eed089bd8f88--dialog-open--desktop/dom.html, evidence/eed089bd8f88--dialog-open--desktop/accessibility-tree.json, evidence/eed089bd8f88--dialog-open--desktop/actions.json, evidence/eed089bd8f88--dialog-open--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/ / dialog-closed / desktop

再現手順:

- 対象http://127.0.0.1:4330/と、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/ への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/eed089bd8f88--dialog-closed--desktop/page.png, evidence/eed089bd8f88--dialog-closed--desktop/inventory.json, evidence/eed089bd8f88--dialog-closed--desktop/dom.html, evidence/eed089bd8f88--dialog-closed--desktop/accessibility-tree.json, evidence/eed089bd8f88--dialog-closed--desktop/actions.json, evidence/eed089bd8f88--dialog-closed--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/ / initial / narrow

再現手順:

- 対象http://127.0.0.1:4330/と、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/ への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/eed089bd8f88--initial--narrow/page.png, evidence/eed089bd8f88--initial--narrow/inventory.json, evidence/eed089bd8f88--initial--narrow/dom.html, evidence/eed089bd8f88--initial--narrow/accessibility-tree.json, evidence/eed089bd8f88--initial--narrow/actions.json, evidence/eed089bd8f88--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/ / anonymous / narrow

再現手順:

- 対象http://127.0.0.1:4330/と、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/ への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/eed089bd8f88--anonymous--narrow/page.png, evidence/eed089bd8f88--anonymous--narrow/inventory.json, evidence/eed089bd8f88--anonymous--narrow/dom.html, evidence/eed089bd8f88--anonymous--narrow/accessibility-tree.json, evidence/eed089bd8f88--anonymous--narrow/actions.json, evidence/eed089bd8f88--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/ / dialog-open / narrow

再現手順:

- 対象http://127.0.0.1:4330/と、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/ への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/eed089bd8f88--dialog-open--narrow/page.png, evidence/eed089bd8f88--dialog-open--narrow/inventory.json, evidence/eed089bd8f88--dialog-open--narrow/dom.html, evidence/eed089bd8f88--dialog-open--narrow/accessibility-tree.json, evidence/eed089bd8f88--dialog-open--narrow/actions.json, evidence/eed089bd8f88--dialog-open--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/ / dialog-closed / narrow

再現手順:

- 対象http://127.0.0.1:4330/と、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/ への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/eed089bd8f88--dialog-closed--narrow/page.png, evidence/eed089bd8f88--dialog-closed--narrow/inventory.json, evidence/eed089bd8f88--dialog-closed--narrow/dom.html, evidence/eed089bd8f88--dialog-closed--narrow/accessibility-tree.json, evidence/eed089bd8f88--dialog-closed--narrow/actions.json, evidence/eed089bd8f88--dialog-closed--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/media / initial / desktop

再現手順:

- 対象http://127.0.0.1:4330/mediaと、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/media への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/media / anonymous / desktop

再現手順:

- 対象http://127.0.0.1:4330/mediaと、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/media への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/media / captions-on / desktop

再現手順:

- 対象http://127.0.0.1:4330/mediaと、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/media への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/media / video-ended / desktop

再現手順:

- 対象http://127.0.0.1:4330/mediaと、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/media への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/media / initial / narrow

再現手順:

- 対象http://127.0.0.1:4330/mediaと、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/media への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/media / anonymous / narrow

再現手順:

- 対象http://127.0.0.1:4330/mediaと、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/media への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/media / captions-on / narrow

再現手順:

- 対象http://127.0.0.1:4330/mediaと、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/media への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

## 2.4.5 複数の手段

対象: http://127.0.0.1:4330/media / video-ended / narrow

再現手順:

- 対象http://127.0.0.1:4330/mediaと、Home/Profile/Media/Help/Loginの全5文書・匿名状態を訪問した。
- 共通nav、本文、footerのリンクと行先を一覧化し、この対象を探す別経路を全実装と比較した。
- 検索、利用者向けサイトマップ、本文の関連リンク等の有無を確認した。XMLサイトマップにはUIからの入口がない。
- この対象へは共通navだけから到達でき、特定の手続きの結果・必須段階だけのページではないことを本文の例外に照合した。

対象要素: http://127.0.0.1:4330/media への到達経路（nav[aria-label="Main"]、全5文書の本文・footerのリンク）
期待結果: 例外以外でページを見つける複数の手段があるか
観察結果: このURLへのUI上の経路は共通navの一つだけ。別の検索・サイトマップ・本文の関連リンクからの経路はない。手続きの結果又は必須の段階の例外には該当しない。
証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#multiple-ways
このcaseの未確認: なし

