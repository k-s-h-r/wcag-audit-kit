# 収集途中の停止と復元

自分で起動した収集器のプロセスグループだけをSIGTERMで終了させた。最初の収集を完了し、次の状態のTab操作を保存してから、存在しない要素を待つ段階で停止した。実際の停止位置とハッシュは[観察記録](interruption-observed.json)に残した。

## 停止後に確認したこと

- 完了済みの収集1件と、実行途中の収集1件がmanifestに残った。
- 実行途中はexecution=blocked、collection_state=running。全体のcollector_status=runningも残り、収集完了と扱わなかった。
- 完了したTab操作と、そこまでの画像・入力記録を保存できた。
- 未訪問URL1件と、まだ収集していないnarrow環境の2状態を報告できた。
- recover後も、最初の収集の証拠ファイルは全て同じSHA-256だった。
- 110件の検査票を復元し、全て未実施とした。検証完了はfalse、strictは終了コード2だった。

[中断後のレポート](interrupted-run/report.html)、[収集記録](interrupted-run/capture-manifest.json)、[検査計画](interrupted-run/plan.json)を保存している。元のrunを再収集して上書きしたわけではない。

## 正常な終了との比較

別の新しいrunで、通常のページ、4回のクリックによる状態、HTTP 404応答の表示を計3件収集した。全3件がcompleted・finishedとなり、collector_status=completed、リンクの巡回終了はtrueとなった。全4操作の中間assertも成功した。

HTTP 404は状態コードを保持し、ブラウザーが表示した画面・DOM等を保存した。依頼されたコンテンツへ到達したと判定したわけではない。[正常終了のレポート](completed-run/report.html)も全165件が未実施であり、検証完了にはしていない。

追加の3単体試験では、置換時の書き込み失敗で直前の有効なJSONを保つこと、途中の収集と未訪問の記録、全検査票に結果があっても停止中のcollectorを検証完了にしないことを確認した。

再集計の例：

```sh
python3 scripts/audit.py recover --run validation/recovery/interrupted-run
python3 scripts/audit.py report --run validation/recovery/interrupted-run --strict
```

この試験ではブラウザー収集を止めた。実スクリーンリーダーや外部媒体分析の強制停止を同じ方法で検証したわけではない。
