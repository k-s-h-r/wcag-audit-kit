# T021 対象範囲の結論を帳票で照合した記録

保存済みの検査票から、HTML・JSON・Excelに同じ適合・不適合・未確認の結論が出るか確かめた。対象は、保存済みのローカル試験ページ2例と、あらかじめ結果を固定した合成台帳。各runの目標レベルと検証範囲は、元の記録を引き継いだ。 [集計結果とファイルのハッシュ](run-005/result.json)

| 台帳 | 対象 | 確認した結論 | `report --strict` |
| --- | --- | --- | --- |
| 正常例 | AA。単独ページの初期表示、On、Offに復帰した状態 | 適合。通過75件、非適用90件 | 0 |
| 問題例 | AA。正常例と同じ3状態 | 不適合。4.1.2の3件に証拠があり、残る162件は未実施 | 2 |
| 合成台帳 | A。単独ページの初期表示 | 未確認。機械候補があり、確定した不適合は0件 | 2 |

正常例と問題例には、当時の実ブラウザーと実Orcaの証拠がある。新しい実行先に台帳をコピーして帳票を再出力し、判定・原始証拠を含む入力ファイルのSHA-256が再出力前後で一致した。今回の報告ではページを再訪問していない。 [AAの試験記録](../../full-fixture/README.md)

不適合には、検査票のID・URL・状態・環境と判定記録へのパスが付く。例えば問題例の4.1.2は、「不適合箇所」から再現手順と操作後の観察に進める。JSONの `scope_conformance.failed_cases` には、同じ3件の検査票と証拠の相対パスがある。

回帰試験では、2ページの開始画面・確認画面を用意した。開始画面だけの帳票では手続きの全体を確認できないため未確認を表示し、確認画面の帳票ではタイトルの不適合と残る確認を表示した。両ページの帳票には、手続きの未確認と、確認画面で確定した不適合の両方が載る。対象ページのない状態が記録に残る場合、単独ページの帳票と直接出力したExcelの結論はいずれも未確認だった。 [CLIを通した回帰試験](../../../tests/test_scope_conformance.py)

## 再現方法

Python 3.12.14のDebian環境で実施した。台帳は必ず新しい実行先へコピーする。

```sh
python3 -m unittest discover -s tests -p 'test_scope_conformance.py' -v
python3 scripts/sync_skills.py --check

t021_replay_dir=$(mktemp -d)
cp -a validation/full-fixture/good-run "$t021_replay_dir/good"
python3 skills/wcag-report/scripts/audit.py report --run "$t021_replay_dir/good" --strict
python3 skills/wcag-report/scripts/audit.py excel export --run "$t021_replay_dir/good" \
  --mode report --out "$t021_replay_dir/good/report.xlsx"
```

## 別のCodex文脈で最終回答と帳票を照合

独立したCodexの文脈に、配布用 `wcag-report` と入力台帳のコピー3件を渡した。期待する結論は知らせなかった。検査役が報告コマンドを実行し、最終回答で案内したHTMLのパス、各帳票の適合・不適合・未確認、残る確認を照合した。HTMLの相対リンク先も存在を確認した。 [最終回答と帳票の照合](run-003/host-answer.json)

Codex CLI 0.167.0-alpha.4を一時セッションで起動したところ、読み取り専用ファイルシステムでapp-serverの初期化が止まった。SQLiteとログを作業先に変更しても、`installation_id` を書き込み用に開く箇所で同じエラーが発生した。このCLIでのスキル発見と最終回答は未実施。 [起動ログの要点](run-003/host-startup.json) · [T004の実行条件](../../../docs/tasks/T004-codex-invocation.md)
