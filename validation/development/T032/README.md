# 見学メニューから日付選択、入力修正、確認までを確かめた

閉じたメニュー、日付の空き状況、人数、確認を4ページにつないだ。両例とも12月19日は満席で、12月20日を選択できる。確認前の1名の入力エラーを直した後も、選んだ日付と2名の人数が確認画面に表示される。エラーを公開するロールだけを変えた対照を使った。[対象ページ](fixture/) · [採点条件](oracle.json)

## 検査担当へ渡した情報と機械検査の範囲

別の検査担当へ、2つの起点URLと「版画室の見学で空いている日に2名で参加する。入力エラーも確かめ、確認画面に進んで止める」という目的を渡した。公開ページをメモリー上から配信し、調査前には対照、操作条件、採点表のSHA-256を記録した。検査担当から観察結果を受け取った後、資料を保存してハッシュが一致することを確認した。確認した分離の範囲は渡した情報と資料の公開時期。ホスト側のアクセス制限は未検証。[調査前の記録](blind-start.json) · [固定した資料の照合](run-001/native-inputs.json)

通常の `page-audit` では各起点からPC幅とスマートフォン相当の幅で、Enterで閉じたメニューを開き、Tabで表示された予約入口に進めた。各12ステップの簡易探索では、単独ページのリンク先への移動が保留された。別担当は実ブラウザーでその先の日付選択、人数の訂正、確認まで進んだ。[機械と別担当の観察の比較](run-001/machine-and-operator.json) · [機械検査の原始記録](run-001/machine-evidence.zip)

## 画面と公開アクセシビリティ情報の追加観察

別担当がChromiumの1280×900 CSS pxで15キーを操作した。メニューの展開後に表示されたリンクを開き、2日の空き状況を文字で区別した。確認ボタンを押して出た案内は両例で同じで、フォーカスは確認ボタンに残った。`b7n` のツリーでは段落、`h2v` では通知が `assertive` なアラートとして公開された。各例で12画面を保存し、対応する画面が画像のSHA-256まで一致することを確認した。別担当の観察範囲は画面とブラウザーが公開する情報で、発話は次の実Orcaの計測で扱う。[別担当の所見と原始記録](run-001/operator-evidence.zip)

資料の公開後に同じ手続きをもう一度操作した。各例で主文書の `keydown` と `keyup` を計34件記録し、すべて `isTrusted: true` だった。エラー、2名の値、確認画面への遷移をそれぞれ該当イベントに対応付けた。[追試の件数](run-001/operator-trusted-replay.json) · [追試の操作と画面](run-001/operator-trusted-replay.zip)

人数を2名へ変更した直後も、両例とも先のエラーと無効状態が人数欄に残った。別担当は、最初から人数欄のそばに「2名以上」と表示し、案内を入力欄に関連付ける案を挙げた。訂正時のエラー状態と、初回入力の案内を次の改善検証に使える。[別担当の所見と画面](run-001/operator-evidence.zip)

## 実Orcaでの発話と帳票

Chromium 156.0.8078.79と実Orca 48.1を使い、専用のXvfb・D-Busセッションで19回のキー操作を記録した。画面は1280×900 CSS px。発話にはOrcaが音声出力へ渡したテキストを使い、音はALSAの `null` へ送った。操作ごとの3秒間に該当する発話を元ログから照合した。いずれも12月20日を選び、1名でエラーを出し、人数を2名に直して確認画面へ進んだ。両例のエラー画面はSHA-256まで一致した。[実測結果](run-001/native-observations.json) · [画面、実キー、発話の原始記録](run-001/native-evidence.zip)

| 例 | 確認ボタンを押した後の発話 | 入力欄へ戻ったとき | 入力エラー状態の4.1.3 | WCAG 2.2 AAの対象範囲 |
| --- | --- | --- | --- | --- |
| `h2v` | キー名 `space` と「見学人数は2名以上を入力してください。」 | 人数欄の名前、無効状態、エラー全文を発話 | 通過 | 未確認 |
| `b7n` | キー名 `space` | 人数欄の名前、無効状態、エラー全文を発話 | 不適合 | 不適合。ほかの観点には未確認が残る |

標準CLIで4ページと人数欄のエラー状態を収集した。4.1.3の検査票に実入力の証拠を付け、HTML・JSON・Excelの結論を照合した。問題例では不適合箇所一覧からHTMLの検査票へ進み、エラーの画面と発話の証拠をたどれる。最初の実行は正常対照のOrcaの版を確認できず、発話の採点を保留した。同じ資料で両例を取得できた `native-002` を採点に使った。[標準帳票の照合](run-001/reports.json) · [最初の起動結果](run-001/startup-001.json) · [アーカイブの照合](run-001/native-archive.json)

今回の範囲は一つの空き日を選ぶローカルの手続きと、指定した入力エラーの状態。別の日付、支援技術との組み合わせ、対象範囲の全達成基準は追加確認が残る。

## 再実行

通常の機械検査を試すときは、端末を1つ使ってローカルの対照を配信する。別の端末で両起点を指定して実行する。

```sh
python3 -m http.server 43933 --bind 127.0.0.1 --directory validation/development/T032/fixture
```

```sh
t032_machine=$(mktemp -d)
for t032_case in b7n h2v; do
  t032_url="http://127.0.0.1:43933/$t032_case/"
  python3 skills/wcag-audit-kit/scripts/audit.py page-audit --url "$t032_url" \
    --out "$t032_machine/$t032_case" --mode machine --screenshots initial --initial-only
  python3 skills/wcag-audit-kit/scripts/audit.py page-audit --url "$t032_url" \
    --out "$t032_machine/$t032_case" --resume --quick-explore --max-steps 12
done
```

実Orcaと帳票の手順は、T026と同じ展開済みOrca環境を使う。空きポートでローカルの対照を配信し、原始ログ、画面証拠、帳票を新しい場所へ保存する。[T026の環境準備](../T026/README.md#再実行) · [実キーのシナリオ](scenario.json)

```sh
t032_native=$(mktemp -d)
env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY -u DBUS_SESSION_BUS_ADDRESS -u AT_SPI_BUS_ADDRESS \
  python3 validation/development/T032/run.py --root /path/to/extracted-orca-root --out "$t032_native/run"
```
