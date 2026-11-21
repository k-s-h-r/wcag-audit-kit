# 再生した媒体の字幕・書き起こし・音声解説を比べる

同じ短い動画を使い、事前に選んだ7件を照合した。原本の音声から得た案内文と、3ページで実際に出た字幕を比べた。書き起こしと音声解説では、画面の「Saved」を伝える例と省く例を区別できた。判定範囲はこの7件の観察に限る。[採点・時刻・媒体のハッシュ](run-002/observed.json)

## 同じ音声で、字幕の文と表示された時刻が異なった

3ページで共通のWebMを再生し、配信されたバイト列のSHA-256を確認した。FFmpegで16 kHz・モノラル・PCM16にデコードした音声をWhisper.cppの `base.en` で認識し、`press the blue button to save the document` を得た。CaptionsとPlayをクリックし、1.2、2.5、5.7秒の映像フレームで有効な字幕と、画像取得前後の字幕が一致することを確認した。[原本WebM](../../media/source/clip.webm) · [同じSHA-256のデコードWAV](../../media/asr/tiny-en/source-audio16k.wav) · [音声認識の原始JSON](run-002/audio/source.json) · [WCAG 2.2の1.2.2](https://www.w3.org/TR/2024/REC-WCAG22-20241212/#captions-prerecorded)

| ページ | 1.2秒・2.5秒の字幕 | 5.7秒の字幕 |
| --- | --- | --- |
| 意図した文 | Press the blue button to save the document. | Confirmation tone |
| 異なる文 | Press the red button to delete the document. | Confirmation tone |
| 後から表示 | 字幕表示なし | 案内文とConfirmation tone |

1.2秒と2.5秒に表示された文では、原本の `blue` と `save` に対して、異なる例が `red` と `delete` を示した。後から表示する例は両時刻で字幕を表示せず、5.7秒に案内文を確認音の字幕と同時に表示した。表の時刻は動画のフレーム時刻。例えば意図した文の2.5秒の画像は、実際には2.595〜2.728秒に取得した。その間も字幕は同じ文だった。別の担当者が9枚の画像を視認し、プレーヤーが取得した字幕と照合した。[意図した文の画像](run-002/good/caption-2.png) · [異なる文の画像](run-002/wrong-text/caption-2.png) · [後から表示する例の2.5秒](run-002/late/caption-2.png) · [同じ例の5.7秒](run-002/late/caption-3.png) · [画像の独立確認](run-002/independent-review.md)

## 書き起こしと音声解説で「Saved」が伝わるかを比較した

書き起こしの2ページでは、どちらも5.7秒の映像に「Saved」が表示された。片方にある `The screen says Saved.` はその表示を伝える。もう片方の書き起こしは案内文と確認音の記述までだった。比較スクリプトは保存したHTMLの本文を調べ、別の担当者が画像で文の表示を確認した。この比較は、1.2.3のメディア代替で必要になる視覚情報のうち、この1件を扱う。[表示を含む書き起こし](run-002/transcript-a/caption-1.png) · [表示を省く書き起こし](run-002/transcript-b/caption-1.png) · [WCAG 2.2の1.2.3](https://www.w3.org/TR/2024/REC-WCAG22-20241212/#audio-description-or-media-alternative-prerecorded)

音声解説の比較では、元の最後の画面を8秒まで延ばした。この映像を2例に使い、片方の音声に5.8秒から `The document has been saved.` を加えた。ブラウザーが記録した再生の終端は両方とも8.015秒。実画面に「Saved」が表示され、両WebMのデコード済みRGBA映像のSHA-256は一致した。保存完了の文は追加例の音声認識出力にあった。5.8〜7.8秒のPCM振幅のRMSは、最大振幅を1として追加例が0.16867、比較例が0.00000322だった。1.2.5のうち、保存完了を音声で伝えるかを比較した。[追加例の実画面](run-002/description-a/caption-2.png) · [比較例の実画面](run-002/description-b/caption-2.png) · [追加例の音声認識](run-002/audio/description-a.json) · [比較例の音声認識](run-002/audio/description-b.json) · [WCAG 2.2の1.2.5](https://www.w3.org/TR/2024/REC-WCAG22-20241212/#audio-description-prerecorded)

別の担当者が5.8〜7.8秒のデコード音声を切り出して再認識した。追加例からは保存完了の文、比較例からは `[BLANK_AUDIO]` を取得した。両例のRGBA 240フレームを時刻付きで照合し、両方の出力が一致した。試験では別URLの音声を比較した。プレーヤー内の音声解説トラック切り替えは対象外。[独立したデコードと再認識](run-002/independent-audio/verification.json) · [追加例のWebM](run-002/media/description-a.webm) · [比較例のWebM](run-002/media/description-b.webm) · [追加例のWAV](run-002/audio/description-a.wav) · [比較例のWAV](run-002/audio/description-b.wav)

## 方法と判定範囲

原本は1人分の合成音声を含む7秒の試験素材。字幕の比較は選んだ案内文と表示時刻を扱う。発話の開始・終了境界、話者ラベル、確認音の意味への対応、全区間の情報の網羅は別途確認が必要。原本の音声認識区間は0〜3秒で、追加説明の出力は動画の終端8秒を越える5〜9秒だった。これらの区間は認識器の出力値として保存した。既存の校正では、同じモデルが無音から `You` と出力した試行もある。[試験範囲と採点条件](scope.json) · [既存の校正の結果](../../media/asr/README.md)

範囲と比較条件は `b8d4d2d` で実行前に固定した。最初の取得では、2.5秒を指定した画像の取得開始が2.781秒となり、取得時刻の確認で中断した。次のrunでは、指定時刻に近い実フレームの字幕と、画像取得前後の字幕が一致するかを確認した。3本の音声は再度デコードし、WAVのSHA-256と認識コマンドの引数が一致したため、最初に取得した認識出力を用いた。画像、プレーヤーの操作、フレームの記録は次のrunで取得した。動画の欠落フレーム数は各プレーヤー記録にある。[各ページの取得記録](run-002/observed.json) · [原本の認識コマンド](run-002/commands/source-whisper.json) · [出力を再利用したときの照合](run-002/commands/source-whisper-reuse.json) · [生成・デコード・認識のコマンド](run-002/commands/)

## 再実行

Debian 13.6、FFmpeg 7.1.5、Playwright 1.62.0、Chromium 156.0.8078.79を使用した。音声合成にはFFmpegの `flite` フィルターを使った。Whisper.cppはソースのcommit `d1be6fde11ac6e0407606b4e42fe72d34add8037` のCPUビルド。`base.en` のSHA-256は `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`。英語、4 threadsで実行し、認識のためのプロンプトは指定していない。[モデルの配布元とハッシュ](../../media/asr/base-model.json)

```sh
t028_runtime=/workspace/wcag-audit-work/evidence/vision-media-preflight
t028_dir=$(mktemp -d)
PYTHONDONTWRITEBYTECODE=1 python3 validation/development/T028/observe.py \
  --whisper-source "$t028_runtime/whisper" \
  --whisper-cli "$t028_runtime/build/bin/whisper-cli" \
  --model "$t028_runtime/ggml-base.en.bin" --out "$t028_dir/run"
```

生成した配信動画、デコードしたWAV、全取得画像とログ、実コマンドの引数と出力は `/workspace/wcag-audit-work/evidence/t028-evidence-002.tar.gz` にある。SHA-256は `f46b44d3e52bf38bcbc06e4f04201481251af6881f2bf4f41278790c0c1cea70`。
