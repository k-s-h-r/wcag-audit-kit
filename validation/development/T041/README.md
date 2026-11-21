# T041 次の空きまでのキー入力と実Orca発話

ローカルの版画室見学カレンダーで、2026年12月14日の初期表示から同じ最初の空き12月19日までの操作を比べた。日付・空き状況・翌日ボタン・表示更新は共通。c4pだけに「次の空き」を加えた。試験対象は最初の空きの確認まで。[点検結果](review.md) · [T041](../../../docs/tasks/T041-review-next-availability.md)

## 事前固定と独立操作

公開したのは2つの入口と共通のJavaScript・CSS。2026年11月21日11:08:26 UTCに対照ファイル、実Orcaの操作、期待する到達条件のSHA-256を固定した。独立担当には2つのURLと、初期状態から最初に見学できる日をキーだけで確認する課題を渡した。公開サーバーへの `/oracle.json` と `/scenario.json` の要求は404で、そのファイルは担当への依頼に含めなかった。独立観察の最初のページ取得は11:09台UTCで、先行の観察結果を受け取った後に固定資料を再現用に同梱した。[固定記録](freeze.json) · [独立操作の所見](run-001/independent-operator.txt)

独立操作ではケースごとに新しいChromiumプロセスとプロファイルを使った。ブラウザーが受け取ったTab・Enterの `keydown` に `isTrusted=true` が記録された。画面、DOM、公開アクセシビリティツリー、フォーカスを保存した。両例の空き表示に共通の `status`、`live=polite`、`atomic=true` が公開された。

## 実Orcaと通常CLI

Orca 48.1とChromium 156.0.8078.79を、ケースごとに専用Xvfb、D-Bus、ブラウザープロファイルで起動した。1280×900、日本語ロケール。Orcaの見出しキーで共通の見出しを確認した後、X11でTabとSpaceを送った。ALSA nullでOrcaが出力したテキストを、各操作の3秒以上の観察窓で原始ログと照合した。音の聴こえ方は未確認。比較した発話は日付と空き状況の組で、キー名、ボタンの発話、開始時の見出しは別に記録した。[操作と発話の集計](run-001/observations.json)

別のrunで、二つのURLを標準の `page-audit --level AA --mode machine --screenshots initial --initial-only` にかけた。両ページで初期画面を取得し、検査票の範囲結論は未確認だった。機械検査結果には両ページとも通過34件と対象外98件、達成基準の検査票には未実施110件がある。[通常CLIの対象と帳票](run-001/machine.json)

## 検証原本

別のレビュアーが事前ハッシュ、独立操作の9件の実入力、Orcaの11操作と原始発話、通常CLIの検査票を照合した。ZIPは147点を原本とバイト単位で照合済み。`operator/` に独立操作のキー受信と画面・DOM・アクセシビリティツリー、`native/` にOrcaの要求と原始ログ、`machine/` に通常CLIの帳票と検査証拠を収録した。SHA-256は `9323716e31f6ecfe564e129bdecece82705614cf120084659c9cd24b0e773674`。[検証原本](run-001/proof.zip) · [独立照合の記録](run-001/independent-review.json)

## 再実行

[T026](../T026/README.md#再実行)と同じ方法でOrcaのパッケージを展開し、リポジトリルートから別々の新しい出力先を指定する。最初のコマンドは各ケースを順に操作する。次のコマンドは通常CLIでその初期画面の検査票を出力する。

```sh
t041_orca_root=/workspace/wcag-audit-work/evidence/vision-orca-preflight/debian13-orca48-root
env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY -u DBUS_SESSION_BUS_ADDRESS -u AT_SPI_BUS_ADDRESS \
  PYTHONDONTWRITEBYTECODE=1 python3 validation/development/T041/measure_calendar.py \
  --root "$t041_orca_root" --out /tmp/t041-native-new
PYTHONDONTWRITEBYTECODE=1 python3 validation/development/T041/collect_machine.py \
  --out /tmp/t041-machine-new
```

対照と出力の関係は [ADR 0125](../../../docs/adr/0125-measure-next-availability-in-a-calendar-review.md) に記録した。
