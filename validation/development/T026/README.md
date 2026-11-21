# 予約手続きの入力エラーを実Orcaで確かめる

両例で、実キーを使って予約を始め、1名の入力でエラーを出し、2名に直して確認画面まで進んだ。エラー画面は画像のSHA-256まで一致した。エラーが表示されたとき、正常例でOrcaは「見学人数は2名以上を入力してください。」を発話し、問題例での発話はキー名の「space」だけだった。[採点結果](run-002/score.json) · [両例のエラー画面](run-002/error.png)

| 例 | 確認ボタンを押した後の発話 | 入力欄に戻ったときの発話 | エラー状態の検査票 | WCAG 2.2 AAの対象範囲の結論 |
| --- | --- | --- | --- | --- |
| 正常例 | 「space」「見学人数は2名以上を入力してください。」 | 入力欄の名前と役割、無効であること、エラー文 | 4.1.3 通過 | 未確認 |
| 問題例 | 「space」 | 入力欄の名前と役割、無効であること、エラー文 | 4.1.3 不適合 | 不適合。ほかの観点に未確認あり |

## エラー発生時には確認ボタンにフォーカスが残った

確認ボタンを押す前に、両例で同じボタン名と役割の発話を得た。Spaceの後もフォーカスは確認ボタンにあり、ページの移動を伴わずにエラーが表示された。正常例では `role="alert"` を指定した。問題例の通知は段落として公開され、ライブプロパティの指定がなかった。入力欄には両例とも `aria-describedby` があり、戻った際にOrcaがエラー文を読んだ。発生時の通知は各操作の3秒間の発話で判定した。[正常例の操作・発話](run-002/aa/screen-reader.json) · [問題例の操作・発話](run-002/bb/screen-reader.json) · [正常例の公開ロール](run-002/aa/accessibility-tree.json) · [問題例の公開ロール](run-002/bb/accessibility-tree.json)

入力に関する警告がフォーカスを移さずに出る場面として、選んだ4.1.3の観点を2件とも事前の期待と照合できた。判定したのは、このエラー状態と使用した支援技術に限る。入力欄に戻る操作や2名での確認到達は、エラー発生時の発話とは別の証拠として記録した。[WCAG 2.2の4.1.3](https://www.w3.org/TR/2024/REC-WCAG22-20241212/#status-messages) · [正常例の確認](run-002/aa/confirmation.png) · [問題例の確認](run-002/bb/confirmation.png)

## 検査票と不適合箇所一覧から同じエラーを追える

T021のCLIで、3ページの初期表示と人数入力ページのエラー状態を収集した。検査票 `input-error / desktop / 4.1.3` に公開アクセシビリティツリー、実Orcaの原始ログ、操作と画面の記録を付けた。問題例の不適合箇所一覧には、該当URL・状態・環境・再現手順・証拠が載る。HTML・JSON・Excelで同じ検査票IDを照合し、選んだ観点以外の確認が残ることも確かめた。[検査票ID、証拠のパス、帳票のSHA-256](run-002/reports.json)

## 実行環境と試行の記録

Debian 13.6、Linux 6.18.57、Orca 48.1、Chromium 156.0.8078.79、Playwright 1.62.0を使用した。表示領域は1280×900。OSへのパッケージ導入には書き込み権限がないため、T012で記録したDebianの31パッケージをSHA-256で照合して作業専用のルートに展開した。専用のXvfbとD-Bus、ブラウザープロファイル、Orca設定を使い、共有デスクトップにキーを送らずに操作した。Orcaが音声出力に渡したテキストを、ALSA nullの環境で採取した。音の聴取、ほかの支援技術、ほかの入力エラーは未確認。

準備試験で、T012の保存通知を確認した。最初のTabを押してもボタンにフォーカスが残らない試行と、起動後に設定時間内でOrcaの版を確認できなかった試行があった。見出しから操作を始めて現在位置の発話を確認した試行では、正常例の「保存しました」と比較用のキー名だけの発話が得られた。T026は、各ページの見出しにOrcaの実キーで移動してからTabを押した。別の検証用ルートに展開したOrca 51.1は、今回のアダプターの起動確認時間内に版ログが得られず、両例を判断保留にした。採点したのは別runで完了したOrca 48.1の試行。[保存通知の準備試験](run-002/save-notification-preflight.json)

## 再実行

新しい対照ページ、実キーの操作、採点条件を保存してから測定した。公開コミット `972d07f` は、測定前のローカルコミット `14dbd65` と同じ試験条件を含む。T022のページ、採点、証拠は元のrunにある。新しい出力先と、T012の手順に沿って用意したOrcaのパッケージルートを指定する。[公開コミット](https://github.com/k-s-h-r/wcag-audit-kit/commit/972d07f37d92d6b5b9aaaca92d4dd7c342b70771) · [対照ページ](fixture/) · [キー操作](scenario.json) · [採点条件](oracle.json) · [実Orcaの準備](../../../skills/wcag-audit-kit/references/screen-reader.md#linuxのネイティブorcaを使う)

```sh
t026_dir=$(mktemp -d)
t026_orca_root=/workspace/wcag-audit-work/evidence/vision-orca-preflight/debian13-orca48-root
env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY -u DBUS_SESSION_BUS_ADDRESS -u AT_SPI_BUS_ADDRESS \
  PYTHONDONTWRITEBYTECODE=1 python3 validation/development/T026/capture.py \
  --root "$t026_orca_root" --out "$t026_dir/native"
PYTHONDONTWRITEBYTECODE=1 python3 validation/development/T026/report.py \
  --run "$t026_dir/native" --out "$t026_dir/report"
```

元の発話ログは、正常例と問題例のそれぞれにgzipで保存した。展開したバイト列のSHA-256を、各 `screen-reader.json` の `cleanup.debug_log_sha256` と照合できる。中断した試行、すべての実画面・操作、生成帳票は `/workspace/wcag-audit-work/evidence/t026-evidence-002.tar.gz` に保存した。SHA-256は `869523d955c59887ba0944d0fffdc143715254c2d478da5fc598b91b9af0a262`。[正常例のOrcaログ](run-002/aa/orca-debug.log.gz) · [問題例のOrcaログ](run-002/bb/orca-debug.log.gz)
