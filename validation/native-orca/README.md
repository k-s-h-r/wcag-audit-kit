# 実際のOrcaによる通知・移動の比較

Guidepupの対応環境を用意するまでの調査として、DebianのOrcaを専用のD-Bus・Xvfb・設定ディレクトリーで起動した。OS本体へパッケージはインストールしていない。これはGuidepupの実行記録とは区別する。

環境はLinux 6.18.57、Orca 48.1-1+deb13u2、Speech Dispatcher 0.12.0-5、Chromium 156.0.8078.79。発話は実際のOrcaが音声出力へ渡したテキストをdebugログから取得した。音声出力先はALSA nullであり、音を録音・聴取した記録ではない。

## 実行した操作と観察

[比較ページ](../../tests/fixtures/live-region-variants.html)には、最初から存在する通知領域を5種類用意した。各ボタンへ実際にTabで移動して名前を取得し、Spaceで保存処理を実行した。全5件で、保存後も同じボタンにDOMフォーカスが残り、画面には対応する完了文が表示された。

| 通知領域 | 保存後の通知の発話 | 実際に取得した文 |
| --- | --- | --- |
| `p role="status"`、暗黙のatomic | 観察窓内で取得せず | — |
| `div aria-live="polite"` | 取得した | Record two saved. |
| `p role="status" aria-atomic="false"` | 取得した | Record three saved. |
| `div aria-live="polite" aria-atomic="true"` | 取得した | Record four saved. |
| 属性のない`p`、対照例 | 観察窓内で取得せず | — |

通知の観察窓は操作開始から約2秒。無発話を永久的な沈黙と扱わない。最初の通知の結果だけから、ページの4.1.3不適合や、同じ役割を使う全実装の問題を確定しない。組合せ・実装・設定の差を調査する必要がある。

続いて専用X11へXTestの`h`を入力した。実際のOrcaが「Wrapping to top.」「Live region compatibility controls heading 1」と出力し、見出しへ移動した。キーボードの文字エコー「h」と、見出しへ移動した発話を区別して記録している。見出し全件・全基準の検査ではない。

## 証拠

- [観察の対応表](run-005/comparison.json)
- [全11ステップの観察と発話](run-005/observations.json)
- [加工前のOrcaログ](run-005/orca-debug.log)
- [最後の画面](run-005/next-heading.png)、[取得したDOM](run-005/page.html)
- [取得した比較ページの原文](run-005/fixture.html)、[パッケージの版と配布物ハッシュ](run-005/package-manifest.json)
- `run-005/provenance/`：その時点の実行・入力・ログ抽出コード。後の改訂と区別するためテキストとして保存した。

ログは実行中にバッファーされる。試行004で、書き込み済みバイトの差分に前の操作の発話が混ざることが分かった。保存した005では、Orca終了後の完全なログから、各発話のUTC時刻で観察窓へ対応付けた。関連する3単体試験で、前の発話・アクセシビリティイベント・合成器ログの重複を混ぜないこと、日付をまたぐ場合、時刻の不明な入力を拒否することを確認した。

## 再実行

ページ固有の依頼で操作する`scripts/screen_reader_native.py`も追加し、[通知・移動とチェック状態のシナリオ](scenarios/README.md)を実行した。以下のreproduce.pyは、最初の5種類の比較試験を再現する診断用として保持している。

[実行スクリプト](reproduce.py)は、既に展開したDebianパッケージを指定して実行する診断用。依存物の自動取得やOSへのインストールは行わない。展開物にはOrca、PythonのGI/AT-SPI、Speech Dispatcher、espeak-ng、Xvfb等が必要。付属のmanifestは実行時の配布物の版とSHA-256を記録している。

```sh
python3 -m http.server 4317 --bind 127.0.0.1 --directory tests/fixtures
```

別のターミナルで、未使用の出力先へ実行する。

```sh
python3 validation/native-orca/reproduce.py --root /tmp/wcag-at-root --out /tmp/wcag-native-orca-new
```

スクリプトは専用のD-Bus・Xvfbを作成し、その中だけでOrcaとChromiumを動かして終了する。既存のデスクトップへキーを送らない。`observed`は観察が完了した意味で、基準の合格を生成しない。005の証拠を別サイトの判定へ流用しない。
