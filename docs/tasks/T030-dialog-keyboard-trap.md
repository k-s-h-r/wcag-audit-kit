# T030 ダイアログからのキー操作による離脱を調べる

状態は実装と比較試験を進行中。前提は[T018の開閉経路](T018-widget-operation-sequences.md)と[T020のURL起点の採点](T020-url-only-machine-score.md)。統合版 `5bb4a80` では、2.1.2の正常例と問題例でダイアログを開けても、離脱の判定は未確認だった。[統合版の87行](../../validation/development/vision/run-001/machine-score.json) · [Issue #69](https://github.com/k-s-h-r/wcag-audit-kit/issues/69)

## 作業と成果物

通常の `page-audit` に、キーボードだけでダイアログを開いた経路からの離脱を記録する。観察したキーで離脱できた対照と、試したキーでは同じ入力欄に留まりマウスでは離脱できた対照を、両画面幅で比較する。[ADR 0109](../adr/0109-observe-keyboard-exits-in-a-dialog.md)

## 完了条件と確認

- 既存の正常例と問題例を通常のURL入口から区別し、保存済みの操作とフォーカス、マウス対照を同じ経路から追える。
- 別のキーで閉じる例、説明がある例、操作の途中で表示やフォーカスが動く例に誤った不適合を出さない。
- T020の2.1.2の固定行で、追加できた判定と未確認を比較する。検査票で達成基準全体の確認を残す。

## 担当範囲と引き継ぎ

`codex/t030-dialog-keyboard-trap` の別worktreeで作業する。canonical の自動探索、ダイアログの観察、ページ帳票と配布用の同期、URL起点の採点を担当する。試験ごとの証拠は `validation/development/T030/` に保存する。複数のフォーカス先、複数モーダル、iframe、メニュー、コンボボックスの経路は後続で確認する。
