# 採点情報を共有ファイルに置かず、予約の手続きを調べた

作業履歴を引き継がない別エージェントに、2つの起点URL、2名の確認画面まで進むという目的、検査する観点と表示条件を渡した。対照のページはメモリー上のHTTPサーバーで配信し、検査担当の操作が終わってからソースを保存した。採点情報も操作が終わるまで共有ファイルに置かなかった。先に記録した両方のSHA-256と、保存したファイルの内容を照合した。[開始時の記録](start.json) · [対照のソース](fixture.py) · [採点情報](oracle.json)

機械検査は先に両サイトの起点と見学枠の計4 URLを収集した。見学人数をキーで変更できることを正常例で確認した。確認画面に到達するための経路と、残る観点は別エージェントが実操作で調べた。機械で照合できた項目は1/6、追加操作後は6/6だった。[機械検査と独立観察の照合](observed-score.json)

| 観察 | n2k | j6w |
| --- | --- | --- |
| 人数変更の2.1.1 | EnterとSpaceの後も1名。別の試行でマウスを使うと2名 | 入力案内を表示したあと、Shift+TabとEnterで2名 |
| 確認ボタンの2.5.3 | 表示は「確認画面に進む」、アクセシブルな名前は「詳しい情報」 | 表示とアクセシブルな名前は「確認画面に進む」 |
| 確認画面 | キーでは2名にする案内が出て進めず、マウスで確認に進んだ | 2名に直し、キーだけで確認へ進んだ。修正後も人数の案内が選択画面に残った |

Debian、Playwright 1.62.0、Chromium 156.0.8078.79の1280×900 CSS pxで実施した。操作は両例の確認画面まで。独立した応答、画面、アクセシビリティツリー、キーと遷移の原始記録96ファイルを保存した。この追試で得た名前はChromiumが公開したもので、実Orcaの入力エラー通知はT026で扱う。[原始証拠ZIP](operator-evidence.zip) · [T026](../../T026/README.md)

## 帳票の再実行

リポジトリのルートから `fixture.py` を起動し、別の端末で元のT022の帳票スクリプトを使う。確認のURLも通常のCLIへ渡し、各例の検査票と不適合箇所一覧を生成する。判定の対象は確認した操作とボタン。サイト全体の検証には各帳票に残る確認が必要となる。[登録した観察](observations.json) · [帳票の照合](reports.json)

```sh
python3 validation/development/vision/run-002/fixture.py
```

```sh
vision_process=$(mktemp -d)
python3 validation/development/T022/report.py \
  --cli skills/wcag-audit-kit/scripts/audit.py \
  --observations validation/development/vision/run-002/observations.json \
  --out "$vision_process/reports"
```
