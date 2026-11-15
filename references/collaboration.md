# 分担して検査し、Excelで結果を共有する

作成済みの検査票を、ページや達成基準ごとの小さいタスクに分ける。人もAIも同じcase_idを使い、担当・作業状態・メモを保存する。次のセッションでは台帳を読み、未完了の票から続ける。

## タスクを作って担当する

```sh
python3 scripts/audit.py tasks create --run /project/artifacts/wcag/run-001 --group-by page --size 20
python3 scripts/audit.py tasks list --run /project/artifacts/wcag/run-001 --limit 10
python3 scripts/audit.py tasks claim --run /project/artifacts/wcag/run-001 --id <task_id> --owner reviewer-a
python3 scripts/audit.py pending --run /project/artifacts/wcag/run-001 --task <task_id> --owner reviewer-a --limit 5
```

`--group-by criterion`なら基準別に分ける。createは、未完了で未割当の検査票だけを分割する。同じrunで再実行しても、同じ票を二重に割り当てない。既存の担当者がいるタスクは取得を止め、合意した引き継ぎだけ`claim --reassign`を使う。

`pending`で取得した票を`case`で読み、実ページで検査して`record`へ保存する。担当者名は作業の割当であり、認証やアクセス制御ではない。

直接JSONから判定する際は、caseの`assessment`を`base_assessment`へ写す。初回はnull。保存時にその版が更新されていたら記録を止める。従来のrecordとの互換性のため省略もできるが、複数の担当者がいる作業では必ず指定する。

## 閲覧用Excelを出力する

```sh
python3 scripts/audit.py excel export --run /project/artifacts/wcag/run-001 --mode report --out /project/reports/wcag-report.xlsx
```

概要、検査票、対象、観察方法、全86達成基準、人への確認、タスクのシートを出力する。検査票は出力条件に合う範囲、概要と達成基準はrun全体の集計。未実施・判断保留・人の確認待ちもそのまま表示する。reportは取り込みできない。

## 作業用Excelを編集して取り込む

```sh
python3 scripts/audit.py excel export --run /project/artifacts/wcag/run-001 --mode work --task <task_id> --out /project/reviews/task-a.xlsx
python3 scripts/audit.py excel import --run /project/artifacts/wcag/run-001 --file /project/reviews/task-a.xlsx --check
python3 scripts/audit.py excel import --run /project/artifacts/wcag/run-001 --file /project/reviews/task-a.xlsx
```

workは配布時の版をrunの`exchanges/`へ保存する。`--check`は変更を反映せず、型・証拠・競合を検査する。実際の取り込みも同じ検査を再実行する。

| シート | 編集する内容 |
| --- | --- |
| 検査票 | 担当、作業状態、メモ、判定、実施状況、観察、条件・例外・全対象の確認、残る確認、手順、検査ID、証拠、比較ページ |
| 対象 | 実際の対象、期待結果、観察、判定、証拠。対象を追加するときは検査票IDと重複しない対象番号を付ける |
| 観察方法 | その票に必要な方法のexecuted又はnot_neededと、具体的な根拠 |
| 人への確認 | 読みやすい確認票。内容を変更する場合は、検査票の「人への引き継ぎJSON」又はrecordを使う |

検査票の灰色の列は識別情報。変更・削除・追加を取り込み時に拒否する。行の並べ替えとフィルターは利用できる。一覧欄は1行1項目で入力する。人への引き継ぎと媒体の区間比較は、既存の構造を保持するJSON欄で編集する。

| 値 | 意味 |
| --- | --- |
| 作業状態todo / in_progress / blocked / done | 未着手 / 作業中 / 作業待ち / 担当作業の終了 |
| 判定not_run / passed / failed / inapplicable / cant_tell | 未実施 / 検査通過 / 不適合 / 対象外 / 判断保留 |
| 実施状況not_run / completed / blocked | 未実行 / 実行済み / 実行不能 |
| 確認フラグTRUE / FALSE | 条件・例外・全対象を実際に確認したか |

担当やメモだけを変えても、WCAGの判定は作らない。判定を変える場合は、対象・観察・期待結果・手順・証拠等も揃える。`record`と同じ検査を通すため、passedだけを選んでも合格にはならない。未記録の票や、引き継ぎが未整理の未完了票をdoneにする操作も拒否する。

## 共同編集と競合

調整担当が1つのrunを正本として管理し、タスクごとにExcelを配布する。Excel Online等を使う場合は、利用者の共有環境へ作業用xlsxを置き、編集後に保存したファイルを取り込む。このCLI自体には共同編集サービスへの接続機能はない。

別の票を変更したファイルは順に取り込める。同じ票の担当・メモ・判定が先に更新されていた場合は、取り込み全体を止めて競合するcase_idを表示する。最新のExcelを出し直し、両方の観察と証拠を確認してから再記録する。自動で勝った側へ揃えない。

同じ変更を再度取り込んでも重複記録を作らない。同じファイルの未取り込み行を後から編集して取り込むこともできる。一度取り込んだ票をさらに変更するときは、最新のExcelを出し直す。

全変更を検査してから判定の履歴を追加し、最後にplanを切り替える。切り替え前に中断した場合、参照されていない判定ファイルが残ることはある。集計はplanが指す判定だけを使う。再実行では反映済みの変更を重複して数えない。

同じホストからの記録・担当の取得・取り込みはロックで直列化する。停止したプロセスのロックはOSが解放する。複数端末でrunのJSONを直接同期する運用や、ネットワークファイルシステム上のロックには対応しない。

## 中断後に読むもの

`tasks list`で割当と件数、`pending --task ...`で次の票を読む。planと判定履歴、exchangesは実行ディレクトリーに保持する。Excelだけを残してrunを捨てると、証拠の照合や取り込みはできない。

doneは人への具体的な引き継ぎを含む担当作業の終了。人の確認待ちはpendingと検証未完了へ残る。タスクが終わったことだけで、サイト全体の適合や検証完了を宣言しない。

タスクは収集済みの検査票を分割する。URLの巡回や収集を小分けに再実行する機能ではない。収集中の中断は従来のrecoverで保存済みの証拠を復元し、未収集のページ・状態・環境を確認する。対象ビルド・設定・定義が変わった場合は新しいrunを作る。

## 出力の上限

1出力は1万票まで。大きいrunは`--task`、`--owner`、`--page`、`--criterion`、`--pending-only`で分割する。既存のxlsxを上書きせず、新しい出力先を指定する。

Excelの1セル32,767文字、行数、制御文字の制限に達したら出力を止める。長い記録はJSONを使う。サイト由来の文字列を数式として出力せず、取り込み時も数式を拒否する。
