# 音声認識の校正

音声入力が非対応の環境で、発話の比較を補助できるかを調べた。Whisper.cpp v1.9.5のソースを変更せずCPU向けにbuildし、公式のtiny.en・base.enモデルを使った。正解文を認識時のプロンプトへ入れず、通常の英語・4 threadsの設定で実行した。

既知の合成音声を使う方法の校正であり、未知の話者や実サイトに対する独立した精度評価ではない。

| 入力 | 方法 | 実際の文字起こし |
| --- | --- | --- |
| 元の7秒動画の音声 | tiny.en | Press the boomer to save the document. |
| 同じ音声 | base.en | press the blue button to save the document |
| red・deleteへ変えた別の合成発話 | base.en | press the red button to delete the document |
| 7秒の中に確認音だけ | base.en | 空 |
| 7秒のデジタル無音 | base.en | You |

base.enは2つの短い発話の重要語を区別した一方、無音から存在しない語も出力した。無音の原本は16kHz・mono・PCM16・7秒で、[全PCMバイトが0であることも確認](source-checks.json)した。tiny.enの結果を正解へ修正せず保存した。どちらも出力文字列を音声の正解と見なさない。[比較とファイルのSHA-256](comparison.json)、[元音声のbase.enの結果](base-en/transcript.json)、[無音の結果](base-controls/silence/transcript.json)を参照する。

元音声のbase.enの区間は0〜3秒だった。生成器が音声ファイルを配置した区間は0.5〜3.484127秒であり、認識区間とは異なる。配置区間には音声ファイル内の無音も含まれ、どちらも語単位の実発話境界を測定したものではない。認識の区間をそのまま同期の合否へ使わない。音だけの例が空文字だったことも、必要な非言語音がない、又は字幕化が不要という意味ではない。

音声の聴取、話者・音の意味の確認、全区間の字幕の比較を、この校正だけで確認済みにしていない。既存の1.2.2の判断保留と未確認区間はそのまま保持した。

## 再現に必要なもの

- [エンジンの公式ソース](https://github.com/ggml-org/whisper.cpp/tree/d1be6fde11ac6e0407606b4e42fe72d34add8037)：v1.9.5、commit d1be6fde11ac6e0407606b4e42fe72d34add8037。[buildの記録](engine-build.json)と[MITライセンス](engine-LICENSE.txt)を保存した。
- [公式モデル配布](https://huggingface.co/ggerganov/whisper.cpp)：[base.en](base-model.json)と[tiny.en](tiny-model.json)のURL・実バイト数・SHA-1・SHA-256を保存した。モデルとbuild用ツールは同梱していない。
- 元の[動画](../source/clip.webm)、音声の16kHz・mono・PCM16への変換結果、各実行の完全なJSON/text/stdout/stderr。元の音声もmonoだった。
- 別発話・確認音・無音の原本WAV、[実際に実行したソース](controls-executed.py.txt)、[コマンドと出力](base-controls/provenance.json)。ソース内の/tmpは開発時の配置であり、再現時には準備した実行ファイルとモデルの場所へ合わせる。

発話を変えた対照例はPCM16へ直接生成しており、元動画のOpusを経由した経路とは異なる。この比較で音声圧縮への頑健性は評価していない。言語、話者、固有名詞、音質、無音、音楽・効果音等に応じて方法を確かめ、認識が不確かな部分は内容の判断保留として残す。
