# 単独ページのAA全基準と、状態更新を欠く比較ページ

一つのチェック部品だけを持つ既知の試験ページを、専用サーバーで他の教材から分離して配信した。対象範囲の調査、実操作、基準別の判断、証拠、範囲確認、報告まで通した。これは方法の校正と実行・記録の確認であり、未知のサイトに対する独立した精度評価ではない。

## 全55基準を検査したページ

[検査レポート](good-run/report.html)は、AAの55基準×初期Off・On・Offへ復帰の3状態、165件。各状態で25基準が通過、30基準が対象外となり、合計は通過75・対象外90。判断保留・未実施はなく、この固定した範囲でのstrictは終了コード0となった。AAAの31基準は目標レベル外として未検証を表示する。

[基準ごとの確認内容](good-run/evidence/criterion-review.json)には、適用条件、実際の対象、期待結果、操作、観察、証拠を記した。対象外も全ソースと全画面を調べて個別に判断した。例えば、メール通知のbooleanはメールアドレスの入力目的ではなく、チェック部品のOn/Offは保存完了等のステータスメッセージではない。

検査対象はルートのHTML文書1枚と、そのJSだけ。全ルートを定める[サーバーの原文](good-run/evidence/methods/source-scope/server.py.txt)、[HTML](good-run/evidence/methods/source-scope/index.html)、[JS](good-run/evidence/methods/source-scope/reader-controls.js)を保存した。別のfixture、実サイト、別のOS又はスキル全体の完成へ、この範囲の完了を広げない。

## 取得した実際の観察

- [39段階の操作・測定](good-run/evidence/methods/browser/observations.json)：キー操作、ポインターの保持と取消、通常クリック、実拡大110/125/150/175/200/400%、復帰、4つの文字間隔の同時上書き。各段階の画面・DOM・AX・trustedイベントも保持した。
- [実Orcaの11段階](good-run/evidence/methods/native-reader/screen-reader.json)：見出し→説明→名前・役割→checked/not checked→Offの順次読み、Tab/Shift+Tabによる離脱と復帰。[生ログ](good-run/evidence/methods/native-reader/orca-debug.log)を発話の時刻で操作へ対応付けた。出力先はALSA nullで、音の聴取を行った記録ではない。
- [向きの9段階](good-run/evidence/methods/orientation/orientation.json)：縦横primary/secondaryの4種類で、画面・API・CSSを照合し状態を保持して操作した。エミュレーションであり、実端末の回転の試験とは区別する。
- [色の測定](good-run/evidence/methods/colors.json)：黒文字と白は21:1。ネイティブ部品はcomputedStyleが同じでも、実際の塗りが通常#efefef・hover #e5e5e5・押下保持#f5f5f5へ変化した。文字や境界のないpaddingの画素を照合した最小値は16.67075583052387:1。作者の外側のフォーカス輪郭は白に対し6.551304852616529:1だった。

判定は各caseの履歴へ記録した。用いた`fixture-aa/...`等の試験IDは、この試行向けに具体化した独自手順であり、W3Cの承認済みACT Ruleを名乗るものではない。記録した[表を入力する実行原文](record-reviewed-matrix.py.txt)も保持したが、これを実サイトの結果として再利用する手順ではない。

## 状態が更新されない比較ページ

[比較ページのレポート](bad-run/report.html)では、4.1.2の3状態を不適合、残る162件を未実施として記録した。strictは終了コード2。この比較ページの全基準を検査完了とした結果ではない。[修正担当向けの報告](bad-run/issues.md)に、対象、操作、観察、期待結果と証拠を出力した。実装の修正はしていない。

[比較表](comparison.json)で、Onの実画面は正常例とバイト単位で同じだった。両ページの全3収集ともaxeの違反は0件。それでも比較ページは、表示OnのときもDOMのaria-checkedとAXのcheckedがfalseだった。

[実Orcaの8段階](bad-run/evidence/methods/native-reader/screen-reader.json)では、名前・役割・初期のnot checked・最後のOffは取得でき、環境全体の沈黙ではなかった。Off→On→Off→On→Offの両方のOnで、公開値の不一致が再現した。状態変更の発話も取得しなかったが、不適合の根拠は無発話だけでなく、実際の選択状態とプログラムで得られる値の不一致である。

## 方法側で見つけた問題

[方法の試行記録](method-controls/README.md)に、YAMLの文字列が真偽値へ変換された状態assert、スクロールの完了前の保存、読み上げ中に混ぜた入力経路、環境切替による接続失敗を保持した。ページの不適合と検査方法の失敗を区別した。

正常例の報告を1280px・320pxで確認し、165行を表示できた。axe違反0、文書の横幅はそれぞれ1280・320px。320pxでは表を1024pxのスクロール領域とした。[画面と測定](report-ui/wcag-full-fixture-report-ui.json)を保存している。レポート自体の全WCAG基準の検査を完了した意味ではない。

## 再現

専用の試験環境で、空いているポートを使う。同じポートなら保存した設定例を使える。既存の実行先は上書きしない。

```sh
python3 validation/full-fixture/good-run/evidence/methods/source-scope/server.py.txt --root validation/full-fixture/good-run/evidence/methods/source-scope --port 4320
```

別のターミナルで新しく収集する。

```sh
python3 scripts/audit.py start --config validation/full-fixture/good-config.yaml --out /tmp/new-fixture-run
```

実際のcase_idと到達状態に合わせ、保存した[Orcaの依頼](good-run/evidence/methods/native-reader/request.json)・[向きの依頼](good-run/evidence/methods/orientation/request.json)、[ブラウザー操作の実行原文](good-run/evidence/methods/browser/executed-source.py.txt)を参照して、利用できる環境で実行する。原文中の/tmpや実行ファイルの場所は開発時の配置。新しい結果は改めて実画面・全対象・原典と比較して判定する。

保存した報告の再集計は、再検査とは区別する。

```sh
python3 scripts/audit.py report --run validation/full-fixture/good-run --strict
python3 scripts/audit.py report --run validation/full-fixture/bad-run --strict
```
