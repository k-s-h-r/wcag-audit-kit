# T036 入れ子のダイアログの離脱を層ごとに確かめる

状態は通常CLIと明示したブラウザー操作を両幅で検証し、独立レビューを経てドラフトPRで提出。前提は[T030](T030-dialog-keyboard-trap.md)の単一ダイアログの観察と[T020](T020-url-only-machine-score.md)のURL起点の採点。通常の24ステップで問題集045と046の子を開き、2.1.2の行は未判定だった。[PR #109](https://github.com/k-s-h-r/wcag-audit-kit/pull/109) · [実測結果](../../validation/development/T036/README.md)

## 作業と成果物

公開T030の `9fcaa0d` から別worktree `codex/t036-observe-nested-dialog-exit` を使い、問題集2.1.2の045と046を、通常のURL探索と同じHTMLへの明示操作で比較した。PC幅とスマートフォン相当幅で、親子を開くキー、子のTabとShift+Tab、子と親の離脱、実際のフォーカス先を確認した。証拠と再実行手順は `validation/development/T036/` に保存した。

## 完了条件と確認

- 通常CLIの実行済み経路、補助Tabの順序、待ち行列と2.1.2の行を同じrunから追える。
- 明示操作の子のEscape、循環、閉じるボタンのEnterまたはマウス操作と親のEscapeを、入力の原本から確認できる。
- 通常の検査で残った未判定と、明示操作で観察した離脱や復帰先をどちらも示す。

## 担当範囲と引き継ぎ

次の最小の製品変更は、同じ主文書の親子を特定し、実入力で子だけが閉じて親が残る事実を記録すること。復帰した要素と層を別に記録し、通常の探索順や複数要素の循環からの自動判定は別の対照で確かめる。[ADR 0120](../adr/0120-observe-nested-dialog-exits-by-layer.md)
