# T038 実Escapeで子のダイアログが閉じる観察

公開T036の `098ec3dad318a5b8392b7e08205dfc89224a5551` を起点に、公式045（`p07.html`）と046（`p08.html`）を確かめた。全測定でブラウザーは一つずつ起動し、同梱のHTMLをループバックで配信した。[T038](../../../docs/tasks/T038-record-nested-child-dismissal.md)

## 変更前の経路と記録

通常の初期取得と `page-audit --resume --quick-explore --max-steps 64` を使用した。AAA・機械モード・初期画像のみ、16状態、深さ3を既定のまま用いた。T036では24手に残った「親クリック → 子クリック → Escape」が両ページとも45・46手目に実行された。ブラウザー由来のEscapeが両幅で主文書の `#inner-name` に届いた。

045では `#outer` と `#subject` が表示されたままで、フォーカスも `#inner-name` に留まった。046では `#outer` だけが表示されたままで、親の `#inner-opener` にフォーカスが移った。旧観察は両方とも一層の条件を満たさず `unconfirmed` で、2.1.2と2.4.3の適否は未確認だった。

045では46手を保存して待ち行列が空になった後、収集用スクリプトのプロセス上限240秒に達した。原本を別の場所に複製し、旧版の `page-report` で帳票を生成した。探索台帳のバイトは保存した原本と一致した。変更後の収集では外側のプロセス上限を600秒にした。

## 変更後の通常CLIと帳票

実装 `2225c0b` の `run-007-updated` では、各ページの初期取得と探索が終了し、46手で待ち行列を消化した。変更前と経路順が一致し、各ページ552件の機械検査の基準、結果、対象、環境、経路名と観察文も一致した。45・46手目に届いたEscapeから、次の観察を両画面幅で保存した。

| ページ | 開閉の観察 | Escape後のフォーカス先と層 |
| --- | --- | --- |
| 045 | 親と子が開いたまま | `#inner-name`、子の内部 |
| 046 | 子が閉じ、同じ親が開いたまま | `#inner-opener`、親の内部 |

JSONの `exploration.dialog_observations` は、開閉とフォーカスの生証拠 `nested-dialog.json` および実際に届いたEscapeの `input-events.json` を参照する。添字は0始まり。HTMLの「詳細と元データ」にある「画面・操作の調査記録」には両方のリンクを、Excelの「操作調査」の「元の調査票」には開閉とフォーカスの記録へのリンクを付けた。両ページの2.1.2と2.4.3は未確認。観察は機械検査の判定から独立して表示する。

## 観察を保留する対照

`run-006-boundaries` は、046をもとにEscape後の動作やダイアログの配置を変えた8対照を両画面幅で試した。TabとEnterで両方のダイアログを開いて実Escapeを送る別ブラウザー試験で、入力と観察の境界を確かめた。

| Escape後の状態 | 観察 |
| --- | --- |
| 親子が同時に閉じる、同じIDの要素で子を置き換える、親子が兄弟の関係にある | 入れ子の開閉の観察を保留 |
| 別のダイアログが現れる | 非モーダル、開いたShadow DOM、複数のroleトークン、自身に矩形のない `display: contents` のすべてで保留 |
| 同じ親を残して子だけを閉じ、フォーカスを親の外に移す | 子が閉じたことと、親の外の `#outside` に移ったことを別々に記録 |

開いたShadow DOM、複数のroleトークン、自身に矩形のない `display: contents` の3対照では、新しいダイアログをChromiumのアクセシビリティツリーでも確認した。観察先を親の内部と決めつけず、外へ移る場合も移動先と層を保存する。適否の判断は追加確認に残る。[ADR 0122](../../../docs/adr/0122-record-escape-in-a-nested-dialog.md)

## 回帰と独立レビュー

通常の24手で一層のダイアログを再測定した。039のキーボード離脱は両幅で合格、040は両幅で不合格で、どちらにも入れ子用の観察は出なかった。旧版の046と039を現行の `page-report` で再生成すると、JSONとHTMLはバイト単位で一致し、Excelの表示値とリンクも一致した。既存の台帳ファイルは全件同じハッシュだった。対象の単体テスト58件も通過した。

別のレビュアーがループバックの別ポートで通常CLIの2例と境界16条件を再測定し、原本、JSON・HTML・Excelから証拠への参照と両達成基準の未確認を照合した。保存した原本187点のZIPには初期の帳票再生成記録、変更前後の比較、単層回帰、独立レビューの結果が入っている。SHA-256は `ac56f52e9776a520feb9cf5de47de45153858683a385461857107bbb15cfcc7e`。[原本と照合結果](proof.zip)

## 再実行

毎回異なる出力先を指定し、次を順番に実行する。

```sh
python3 validation/development/T038/boundaries.py --out /tmp/t038-boundaries-new
python3 validation/development/T038/collect.py --out /tmp/t038-nested-new
python3 validation/development/T038/verify.py /tmp/t038-nested-new --version updated
python3 validation/development/T038/collect.py --out /tmp/t038-single-new --steps 24 --case 039 --case 040
python3 validation/development/T038/verify.py /tmp/t038-single-new --version single
```

変更前を再測定するときは、起点の別worktreeへ `collect.py` と `verify.py` を同じ相対パスに置く。別の出力先で通常の64ステップを収集し、`--version baseline` で照合する。
