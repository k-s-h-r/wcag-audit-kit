# ダイアログからの離脱を通常の `page-audit` で調べる

2.1.2の既存問題集をURLだけで検査する。対照は、Escapeで閉じて元のボタンへ戻る正常例と、Tab・Shift+Tab・Escapeで入力欄に留まり、閉じるボタンをマウスで使うと戻れる問題例。判定と実入力は、ダイアログの `dialog-focus.json` と `input-events.json` に保存する。[対照](../../../benchmarks/cases/2.1.2/README.md) · [T030](../../../docs/tasks/T030-dialog-keyboard-trap.md)

開く・Escapeの経路は通常の探索で実行する。追加の試行に入れる場合は、同じ入力欄でTabとShift+Tabを各2回、Escapeの再試行、矢印キー、Enter、Spaceを実行する。Spaceで空白文字が入ったあとを実際のBackspaceで確認し、元の空欄からマウス操作と比較する。通常の探索の状態・画像・axe結果は追加試行の前に保存する。

案内、複数の操作先、別文書、入力中のフォーカスや表示の変化などがある場合は、残る離脱経路を追加で確かめる。検査票では、試した経路の機械検査と達成基準全体の判定を区別する。

## 実測結果

Chromium 156.0.8078.79、Playwright 1.62.0、1280×900と320×900 CSS pxで確認した。通常の24ステップの探索で、039の正常例は両幅ともEscape後に開いたボタンに戻った。040の問題例は試したキーで同じ入力欄に留まり、閉じるボタンをマウスで使うと戻った。出力の機械検査は正常例が通過、問題例が不適合候補になった。両例の範囲全体は未確認だった。[2例の帳票と実入力](run-001/pair-evidence.zip) · [証拠リンクとハッシュ](run-001/pair.json)

問題6例と正常6例を収集した。統合版の保存済みの結果と比べると、試した離脱を確認できた正常例が1件、機械で指摘できた問題例が1件増えた。残る10例の結果は同じだった。複数階層のメニュー、入れ子のダイアログ、コンボボックス、フレームは未確認に残った。[変更後の12行](run-001/suite-score.json) · [元の87行](../vision/run-001/machine-score.json)

別エージェントが、英語・日本語の見出しでQによる離脱を案内する対照を同じ版のCLIで再測定した。両幅とも判断保留だった。通常の正常例・問題例も再測定し、開くキーが信頼されていない入力や、入力後の状態が指摘と矛盾する記録を採点から除外できることを確認した。[独立レビューの結果](run-001/independent-final-cli.json) · [採点の確認](run-001/independent-final-score.json) · [独立レビューの原始証拠](run-001/review-evidence.zip)

76ページすべてで通常のCLIを実行したところ、039・040に判定が増えた一方、064・065では閉じるボタンをEnterで押す従来の経路が上限内に入らなかった。064には、別のEscape経路から問題集の採点行に対応しない指摘が両幅で生じた。探索順を優先する対象を、フォーカスがテキスト入力欄にあり、入力欄と閉じるボタンの二つを操作候補として観察したダイアログに絞った。[途中の87行の結果](run-002/score.json) · [差分](run-002/comparison.json) · [4ページの操作と帳票](run-002/regression-evidence.zip) · [ADR 0115](../../../docs/adr/0115-limit-modal-exit-priority-to-input-dialogs.md)

## 再実行

配布用ファイルを同期し、ChromiumとPlaywrightを使える環境で、変更前と変更後を別のディレクトリーに収集する。変更前には統合版 `5bb4a80` の作業ディレクトリーを指定する。

```sh
python3 scripts/sync_skills.py --check
python3 validation/development/T030/measure.py --checkout BASE_CHECKOUT --out BEFORE_RUN
python3 validation/development/T030/measure.py --out AFTER_RUN
```

収集条件はT020と同じ `AAA`、`machine`、初期状態の撮影、簡易探索。元の問題集と通常のURL入口を使い、検査CLIに正解やセレクターを渡さず、収集後に2.1.2の行を照合する。

76ページ・87行の採点には次を使う。各版で新しい出力先を指定する。

```sh
python3 benchmarks/url_only_machine.py --out FULL_RUN --workers 6
python3 benchmarks/url_only_machine.py --out FULL_RUN --score SCORE_JSON
```
