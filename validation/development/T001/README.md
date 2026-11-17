# 最初の2観点の測定計画 v1

2026-11-18。T001。起点626a230。収集・採点器、問題集、期待結果は変更しない。計画は収集前に固定し、T002とT003が別runで2回ずつ測定する。

採点側の母数は[selected-rows.csv](selected-rows.csv)の10行。タイトル2.4.2-01の3行と、image-altに対応する1.1.1-01の7行（初期5・操作後2）である。画像の空altの装飾を含む行も既存の正解どおり保持する。画像の意味・部品の名前全般、タイトルの主題は対象に含めない。[除外した判定15行](excluded-rows.csv)と[未接続の取得3行](acquisition.snapshot.json)も保持する。取得3行はCSS背景・SVG・canvas等の候補列挙で、この限定したimgの代替文ルールの一致を示すための必須条件とはしない。全体では未確認として表示する。

[実行条件](context.json)には問題集と実装の識別値、OS・Python・Playwright・Chromium、machineモード、探索上限を固定した。表示環境は各runのconfigとrun.jsonにも保存される。既存CLIの既定（最初のdesktop環境、keyboard_steps=6、max_states=8、max_steps=32、max_depth=3）を使用する。machineは画像・実SRを使わず、max_images=6はAI有効時だけ適用される未使用の予算値である。

## 実行と再実行

同じコミットの新しいworktree・ブランチをタスクごとに用意する。T002は基準2.4.2、T003は1.1.1を使う。各2回とも新規出力先へ実行し、同時の待受ポート・ブラウザーコンテキストを共有しない。

```sh
python3 benchmarks/run.py collect --mode machine --criterion 2.4.2 --out artifacts/T002/run-001
python3 benchmarks/run.py collect --mode machine --criterion 2.4.2 --out artifacts/T002/run-002
python3 benchmarks/run.py collect --mode machine --criterion 1.1.1 --out artifacts/T003/run-001
python3 benchmarks/run.py collect --mode machine --criterion 1.1.1 --out artifacts/T003/run-002
```

各コマンドをmonotonic clockで囲み経過秒と終了コードを保存する。各runの採点をstrictでも実行し、成功・未完了・不一致の終了コードを保存する。過去のreportは上書きしない。収集実装・採点実装・問題集・環境・予算が違えば比較条件の差として記録し、同条件の再実行へ混ぜない。

planの全ファイルは[checksums.json](checksums.json)で固定する。T002・T003はそのハッシュと各ファイルのハッシュを参照する。

## 検査側と採点側

検査を行うのは既存の決定的なmachine収集処理で、AIへの判断依頼やLLM API呼び出しは行わない。正解のCSV・suite・oracle・レポートを、機械検査の入力へ渡さない。収集器には公開ページと既存の設定のみを渡し、採点は証拠の取得後に既存scoreで行う。実装のスナップショット、公開ページ、worker/tasks.json、生の証拠と操作記録を保存する。

開発担当は正解を読んでいるため、その担当による画像判断を機械検査へ補完しない。現在のrunは同一OSユーザー内であり、正解をファイル権限で隔離したAI試験ではない。人やAIを検査担当に替えるときは、文脈とファイルアクセスの両方の隔離が必要で、この計画の機械測定だけを流用して隔離済みとしない。

## 集計

採点後のresult.jsonに対し、採点側だけが[summarize.py](summarize.py)を使う。これは保存済み採点行を固定CSVと突合する分析例であり、収集器や採点ルールへフィルターを追加するものではない。判定の存在しない行はactual=not_run、grade=not_evaluatedで母数へ残す。

例えば画像7行のうち初期5行が一致し、操作後2行が未出力なら、一致5／未確認2とする。未確認の問題1行は未検出で、正常1行も通過へ変換しない。報告された不適合に固定行との対応がない場合は、追加の誤検出として別に数える。

出力には選択した10行の正否・見逃し・誤検出・未確認のほか、全体のcounts、selected_checks_status、overall_status、pending_evidence_contractsを併記する。意味判断や取得未接続が残るため、限定行の一致をWCAG基準全体又はG1の達成へ直結させない。G1はT007〜T009とT008の結果を確認してから別に判断する。

AIモデル・使用トークンは「該当なし（AI推論なし）」とし、取得していないホストの使用量を0と推計しない。再実行の成績と経過時間の差を残す。実サイト・別の問題での精度は今回の基準値から主張しない。
