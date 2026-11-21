# 選んだ音声解説が実際に再生されるか

「音声解説を使う」をキーボードで選ぶと、2例ともボタンは押された状態になった。受付コード7291を再生音声で伝えたのはc04だけだった。c03では選択前と同じ元動画が再生された。どちらの画面も申し込みに受付コードが必要と案内し、動画に `Access code 7291` を表示した。[c03の再生画面](run-001/c03/playing-03.0.png) · [c04の再生画面](run-001/c04/playing-03.0.png)

前回のT028では、音声を変えた動画を別々のURLで再生した。今回は既存の1.2.5問題集を使い、プレーヤーで音声解説を選んでから、その音声が再生されるまでを確かめた。T009は指定された部品のクリックとスクリプトによる再生で資源の切替を調べている。[前回のT028](../README.md) · [T009の計測範囲](../../../../docs/tasks/T009-machine-gap.md#未確認だった58観点のブラウザー計測) · [対象の問題集](../../../../benchmarks/cases/1.2.5/README.md)

## 同じ選択表示から、異なる音声が再生された

| 条件 | 選択後の押下状態 | 終端まで再生した動画 | ブラウザーで収録した音声の認識 |
| --- | --- | --- | --- |
| p04、未選択の対照 | false | `expanded-source.webm` | Press the blue button to save the document. |
| c03、p03で選択 | true | `expanded-source.webm` | Press the blue button to save the document. |
| c04、p04で選択 | true | `expanded-described.webm` | Press the blue button to save the document, and access code appears 7-2-9-1. |

Chromiumでは3条件とも0秒から6.983秒まで、シークや音量変更をせずに再生した。再生時の `currentSrc` と、ブラウザーが受信を完了したHTTP 206応答を照合した。サーバーが記録した配信区間はファイル全体を覆い、配信したバイト列のハッシュは固定した素材と一致した。2本の動画をデコードし、RGBA映像フレームごとの時刻とハッシュも一致することを確かめた。[再生、配信、音声の照合](run-001/decode/corroboration.json) · [サーバーの応答記録](run-001/server-receipts.json)

収録したブラウザーの音声トラックと、配信ファイルを別々にデコードした。Whisper.cppは、対応する2つの音声で同じ発話を認識した。独立レビューでは、c03と未選択の対照のPCMが同じバイト列であることも確認した。収録音声を配信素材と時刻合わせすると、音のある250 ms区間で相関は0.9995以上だった。c04の収録音声では、共通の発話のあと約3.14〜6.31秒に音声信号があった。この時間は音量から求めた区間で、単語の境界は示さない。[独立レビュー](run-001/independent-review.md) · [波形の比較](run-001/independent-pcm.json) · [c03の収録音声](run-001/c03/played-audio.webm) · [c04の収録音声](run-001/c04/played-audio.webm)

## 検査票に記録した範囲

c03では、選択後も申し込みに必要な受付コードを音声から得られなかった。検査票に、この事実を1.2.5の不適合として記録した。c04では `1.2.5-01` の選択と受付コードの観察結果を通過とし、基準全体は判断保留とした。どちらも別の再生環境、受付コード以外の映像情報、非言語音は確認が残る。[標準帳票の照合結果](run-001/report-checks.json) · [標準帳票と添付のZIP](run-001/standard-reports.zip)

報告には `page` で収集した同じURL・`after-select`・`desktop` のケースを使った。選択済みのボタンと動画の資源を状態の条件にした。`case`、`attach`、`record` で記録した結果を、`page-report` のJSON、HTML、Excelで照合した。

## キー入力と音声を再現する

実測前に問題集の版、対象のURLパス、比較条件、素材と認識モデルのハッシュを固定した。起点は `5bb4a808e38baa1e252b77e02e479c15e50e2626`。Chromium 156のヘッドレス環境を1280 × 900 CSS pxで使い、条件ごとに新しいブラウザーコンテキストを開いた。[固定条件](conditions.json) · [実行環境](run-001/environment.json)

選択する2例ではTabを8回送り、`音声解説を使う` にフォーカスしてEnterを押した。ページが受け取った `keydown`、ボタンの `click`、`keyup` は `isTrusted: true` だった。Shift+Tabを6回送ると、Chromiumのアクセシビリティツリーでネイティブの再生ボタン `play` にフォーカスした。未選択の対照では初期状態からTabを2回送った。再生ボタンでSpaceを押すとフォーカスした部品の名前が `pause` に変わり、`isTrusted: true` の `play`、`playing`、`ended` を記録した。ネイティブ部品へのSpaceはページのイベント監視に届かなかったため、Chromiumへのキー送出と応答も保存した。[c03の操作記録](run-001/c03/keyboard.json) · [c04の操作記録](run-001/c04/keyboard.json) · [Chromiumのキー送出と応答](run-001/decode/key-dispatch.json)

音声は、再生した動画要素のトラックを `captureStream()` で取り出して収録した。証拠の対象はブラウザーがデコードした音声トラック。スピーカーからの出力や聞き取りやすさ、発話の正確な境界は対象外とした。準備中の失敗した試行も、作業用の証拠ディレクトリに別々に保存した。

Chromium、Playwright、FFmpeg、事前校正と同じWhisper.cpp・`base.en` モデルを用意する。リポジトリのルートから次を実行する。[事前校正の手順](../../../media/README.md)

~~~bash
work=$(mktemp -d)
task=validation/development/T028/description-choice
DEBUG=pw:protocol python "$task/observe.py" --run "$work/run" 2>"$work/protocol.log"
python "$task/analyze.py" "$work/run" --protocol "$work/protocol.log" \
  --whisper /path/to/whisper-cli --model /path/to/ggml-base.en.bin
python "$task/report.py" "$work/run" --out "$work/report"
~~~
