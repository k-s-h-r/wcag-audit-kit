# ダイアログからの離脱を通常の `page-audit` で調べる

2.1.2の既存問題集をURLだけで検査する。対照は、Escapeで閉じて元のボタンへ戻る正常例と、Tab・Shift+Tab・Escapeで入力欄に留まり、閉じるボタンをマウスで使うと戻れる問題例。判定と実入力は、ダイアログの `dialog-focus.json` と `input-events.json` に保存する。[対照](../../../benchmarks/cases/2.1.2/README.md) · [T030](../../../docs/tasks/T030-dialog-keyboard-trap.md)

開く・Escapeの経路は通常の探索で実行する。追加の試行に入れる場合は、同じ入力欄でTabとShift+Tabを各2回、Escapeの再試行、矢印キー、Enter、Spaceを実行する。Spaceで空白文字が入ったあとを実際のBackspaceで確認し、元の空欄からマウス操作と比較する。通常の探索の状態・画像・axe結果は追加試行の前に保存する。

案内、複数の操作先、別文書、入力中のフォーカスや表示の変化などがある場合は、残る離脱経路を追加で確かめる。検査票では、試した経路の機械検査と達成基準全体の判定を区別する。

## 再実行

配布用ファイルを同期し、ChromiumとPlaywrightを使える環境で、変更前と変更後を別のディレクトリーに収集する。変更前には統合版 `5bb4a80` の作業ディレクトリーを指定する。

```sh
python3 scripts/sync_skills.py --check
python3 validation/development/T030/measure.py --checkout BASE_CHECKOUT --out BEFORE_RUN
python3 validation/development/T030/measure.py --out AFTER_RUN
```

収集条件はT020と同じ `AAA`、`machine`、初期状態の撮影、簡易探索。元の問題集と通常のURL入口を使い、検査CLIに正解やセレクターを渡さず、収集後に2.1.2の行を照合する。
