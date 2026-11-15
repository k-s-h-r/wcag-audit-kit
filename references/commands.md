# 実行コマンド

以下はスキルのディレクトリーを作業ディレクトリーとする例。プロジェクトの場所と混同せず、パスは実際の保存先へ置き換える。

## 1ページ又はURL一覧から始める

```sh
python3 scripts/audit.py page --url https://example.com/contact --out /project/run-contact --profile standard
python3 scripts/audit.py pages --config /project/wcag-audit.yaml --out /project/pages.json
```

pageはリンクを巡回せず、1ページの証拠と未実施票を作る。pagesは対象URLの選定だけを行う。[4つの入口](../README.md)と[観察設定](inspection-profiles.md)に沿って、収集後はページ検証スキルが実画面・操作・原典から判定する。

## 操作・状態の調査を記録する

```sh
python3 scripts/audit.py review-interactions --run /project/run-contact --file /project/interaction-review.json
```

[画面からの調査](visual-discovery.md)で、見える操作対象と開いた後の状態を確認する。各ページの現在の票はplan.jsonのinteraction_reviewsに保持する。新しい票はbase_reviewで版を照合する。

## 設定と証拠を作る

```sh
python3 scripts/audit.py doctor
python3 scripts/audit.py init --url https://example.com --config /project/wcag-audit.yaml
python3 scripts/audit.py start --config /project/wcag-audit.yaml --out /project/artifacts/wcag/run-001
```

initで作った設定は調査の初期値。サイトを調べ、必要なページ・状態・環境を追加する。startの出力先は空の場所を指定する。認証状態の相対パスは設定ファイルを基準に解決してから実行する。

startは当時の検査定義も保存する。古い実行で定義のコピーがない場合は、版が一致するうちに`python3 scripts/audit.py snapshot --run <実行先>`で保存できる。定義の更新後も保存した判定は再集計できるが、新しい定義で検査した結果とは区別する。

## 次の検査票を読む

```sh
python3 scripts/audit.py pending --run /project/artifacts/wcag/run-001 --status not_run --limit 10
python3 scripts/audit.py pending --run /project/artifacts/wcag/run-001 --criterion 2.4.11
python3 scripts/audit.py case --run /project/artifacts/wcag/run-001 --id <case_id>
```

caseの出力から本文・手順のパス、設定と本文のハッシュ、対象ページと証拠の場所を取得する。表示されたaxeの候補は、原典と実ページで確認する。

## 分担とExcel

```sh
python3 scripts/audit.py tasks create --run /project/artifacts/wcag/run-001 --group-by page --size 20
python3 scripts/audit.py tasks claim --run /project/artifacts/wcag/run-001 --id <task_id> --owner reviewer-a
python3 scripts/audit.py pending --run /project/artifacts/wcag/run-001 --task <task_id> --owner reviewer-a --limit 5
python3 scripts/audit.py excel export --run /project/artifacts/wcag/run-001 --mode report --out /project/report.xlsx
python3 scripts/audit.py excel export --run /project/artifacts/wcag/run-001 --mode work --task <task_id> --out /project/task-a.xlsx
python3 scripts/audit.py excel import --run /project/artifacts/wcag/run-001 --file /project/task-a.xlsx --check
python3 scripts/audit.py excel import --run /project/artifacts/wcag/run-001 --file /project/task-a.xlsx
```

[共同作業の手順](collaboration.md)で、取り込み可能な列、競合、再取り込み、中断後の再開を確認する。判定を直接recordする場合も`base_assessment`に読み取ったcaseのassessment（初回はnull）を指定して競合を検出する。

## 関連するACT Rulesを読む

```sh
python3 scripts/audit.py rules --criterion 1.1.1 --status approved
python3 scripts/audit.py rule --id 23a2a8
```

承認状態、適用条件、前提、基準との合否の対応を確認する。[ACT Rulesの手順](ACT.md)を参照する。

## 追加操作を行う

```sh
python3 scripts/audit.py probe --run /project/artifacts/wcag/run-001 --case <case_id> --actions /project/probe.json
```

probe.jsonの例：

```json
{
  "actions": [{"type":"press","key":"Tab"},{"type":"press","key":"Shift+Tab"}],
  "assert": [{"selector":"body","visible":true}]
}
```

実際に必要な操作と、到達した状態を特定できるassertへ変更する。probeは既知の状態への操作に続けて追加操作を行い、元の証拠を上書きしない。複雑な操作・媒体・支援技術は、利用可能な外部ツールで実施する。

```sh
python3 scripts/audit.py attach --run /project/artifacts/wcag/run-001 --case <case_id> --file /project/proof.png
```

## 数値を比較する

```sh
python3 scripts/measure.py contrast --foreground '#aaaaaa' --background '#ffffff'
python3 scripts/measure.py spacing --file /project/target-rectangles.json
```

spacing入力は`[{"id":"a","x":0,"y":0,"width":10,"height":10}, ...]`。実際の当たり判定を調べてから入力する。結果は数値・幾何の補助であり、例外や実際の見え方の判定を代替しない。

## 判定して出力する

```sh
python3 scripts/audit.py record --run /project/artifacts/wcag/run-001 --file /project/judgment.json
python3 scripts/audit.py scope-review --run /project/artifacts/wcag/run-001 --file /project/scope-review.json
python3 scripts/audit.py report --run /project/artifacts/wcag/run-001 --strict
```

strictは未実施・判断保留・未網羅・範囲確認の不足があれば終了コード2。不適合が存在するだけでは「検査未完了」にはしない。

人への引き継ぎを記録する場合は[具体的な確認票](human-review.md)を判定の`human_handoff`へ含める。`human-review.md`へ必要な環境・対象・操作・判定条件を出力する。

```sh
python3 scripts/audit.py pending --run /project/artifacts/wcag/run-001 --status human
```

全票を判定又は具体的な引き継ぎへ記録したら、AIが今回行える作業を終えて結果を渡す。人の確認待ちがある報告のstrict終了コード2は、その確認を残したことを表す。

収集中に停止した場合：

```sh
python3 scripts/audit.py recover --run /project/artifacts/wcag/run-001
```

保存済みの証拠だけから計画を復元する。未収集のページや状態は、調査して次の実行で補う。

収集開始時、各ページ・状態・環境の開始と終了、完了した操作ごとに記録を保存する。manifestは一時ファイルを完全に書いてから置き換える。強制停止でcollector_statusがrunningのまま残った場合も、収集完了とは扱わない。recoverはネットワークへ再接続せず、元の証拠を保持して検査票・報告を復元する。同じrunを再収集して上書きする機能ではない。

HTTPエラーの応答も、ブラウザーが表示した画面・DOMを保存し、http_statusを残す。認証画面やエラー画面が、依頼された状態への到達を意味するとは扱わない。必要なassertと実画面で確認する。通信そのものが失敗した場合はblockedとなる。
