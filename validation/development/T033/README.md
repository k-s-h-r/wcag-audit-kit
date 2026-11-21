# 初期の検査票からダイアログの離脱証拠へ進む

2.1.2の正常例と問題例を、配布用の `wcag-page` が持つ通常のCLIで検査した。Chromium 156.0.8078.79、Playwright 1.62.0、1280×900と320×900 CSS pxを使った。初期表示だけを収集すると、最初の `page-next` は簡易探索の開始を案内した。同じrunで簡易探索を再開すると、どちらの例でも既定5件の先頭に、PC幅とスマートフォン相当幅のダイアログを開いた状態の検査票が出た。元の操作経路、保存した実入力、開いた状態の照合記録を検査票からたどれる。[T033](../../../docs/tasks/T033-operation-evidence-in-next-cases.md) · [対象ページ](../../../benchmarks/cases/2.1.2/README.md)

| ページ | 初期調査後の離脱証拠付き検査票 | 簡易探索後の離脱証拠付き検査票 | 試した操作の結果 |
| --- | ---: | ---: | --- |
| `p01.html` | 0 | 2 | 両幅でEscapeで離脱 |
| `p02.html` | 0 | 2 | 両幅で試したキーでは入力欄に留まり、マウスで離脱 |

4件の機械結果が得られた後も、各検査票の判定は `not_run`、ページ全体の検査完了は `false` だった。T030版の `page-next` は同じ新しいrunで機械結果を同じ件数で集計し、既定5件に離脱の記録を表示しなかった。操作直前の状態を記録していないT030の既存run（039・040）は、新旧のCLIで出力全体が一致した。[新しいrunの出力](run-002/summary.json) · [039の比較](run-002/legacy-039.json) · [040の比較](run-002/legacy-040.json)

別エージェントが、同じURLに戻るたびにダイアログの見出しを変える対照を実ブラウザーで検査した。実際にEscapeで離脱できた結果は両幅で機械結果に残った。Escape直前の見出しが保存済み表示と異なるため、両幅で検査票との関連付けを保留した。固定表示の対照を派生コピーにし、両幅の操作証拠の参照先を入れ替えた場合、入力が主文書から届いた記録を片方だけ欠いた場合、保存キャプチャーの最終URLを片方だけ変えた場合も確認した。[独立レビューの計測](run-002/independent.json) · [操作と状態の原始証拠](run-002/evidence.zip)

## 再実行

ChromiumとPlaywrightを使える環境で、出力先に新しいディレクトリーを指定して実行する。比較する場合は、`--baseline-cli` にT030版 `8520421` の `skills/wcag-page/scripts/audit.py` を渡す。

```sh
python3 scripts/sync_skills.py --check
python3 validation/development/T033/verify.py --out /tmp/t033-new-run
```

`verify.py` は既存の対照をループバックで配信する。受け取ったURLだけを `page-audit --initial-only --mode machine --screenshots initial` に渡し、`page-next`、`page-audit --resume --quick-explore`、`page-next` の順で同じrunを使う。機械結果、検査票、状態の証拠を保存する。証拠ZIPにはこの比較に使ったファイルを抜き出して収録した。再開には収集したrun一式を使う。

今回の関連付けは初期の検査票から案内される簡易探索を対象とした。明示的な全探索や、視覚構造の追加情報まで含めた指紋が一致しない場合も、従来の機械結果を集計と帳票から読める。
