# 実スクリーンリーダーで検証する

読み上げの検証には、[Guidepup](https://www.guidepup.dev/docs/getting-started)の実スクリーンリーダー用APIを優先する。`@guidepup/virtual-screen-reader`の結果はユニットテストの補助として区別し、実際の読み上げを確認した証拠にはしない。

## 対応する環境を確認する

| 環境 | 実スクリーンリーダー |
| --- | --- |
| macOS | VoiceOver |
| Windows | NVDA |
| Linux | Orca |

導入時の[対応表](https://www.guidepup.dev/docs/reference/support-matrix)と、インストールした版のmanifestを確認する。OS名が対応していても、アセットの版、OS・カーネル、ランタイム、実際の起動を確認するまで利用可能としない。

```sh
npm ci --ignore-scripts
node scripts/screen_reader.mjs doctor
```

このスキルではGuidepup 0.40.0を固定している。そのmanifestのOrcaアセットはLinuxカーネル7向け。現在の開発環境の6.18は一致しないため、Guidepupによる実際のOrca検証は未実施。Dockerもホストのカーネルを共有するので、イメージを変えるだけでこの条件が解消するとは扱わない。

## 対応環境を準備する

[公式のセットアップ手順](https://www.guidepup.dev/docs/guides/machine-setup)に従い、利用する検証環境で設定とアセットのインストールを行う。

```sh
npx @guidepup/setup@0.29.3 setup
npx @guidepup/setup@0.29.3 install
```

既存の依頼で許可された範囲と、使用する専用の検証環境を確認して実施する。設定済みなら毎回やり直さない。必要な権限・環境がなければ、その条件と残る操作を記録する。版の条件を偽装したり、仮想読み上げへ黙って置き換えたりしない。

## ページ専用のシナリオを作る

[シナリオ例](../assets/screen-reader.example.json)を、そのcaseの実ページ・状態・対象に合わせて書き換える。期待値は要件と内容から先に定める。実行後に取得した発話をそのまま期待値へコピーして成功させない。

- 見出し・領域・リンク等：実際のスクリーンリーダーの移動コマンドを使い、順序・名前・役割・文脈を確かめる。
- 入力・部品：対象を読み、操作し、名前・役割・状態や値の変化を確かめる。
- 通知：`capture()`で実際の操作中の読み上げを取得し、必要な通知を受け取れるか確かめる。フォーカスの前後も記録する。

| 達成基準 | 実ページで具体化する観察例 |
| --- | --- |
| 1.1.1 非テキストコンテンツ | 対象画像へ移動して得た代替情報を、実際の画像の目的・情報と比較する。発話の有無だけで意味の一致を判定しない |
| 1.3.1 情報及び関係性 | 見出し一覧、表のセルと見出し、入力欄とラベル等、画面にある関係を対応する読み上げ・構造で取得できるか確かめる |
| 1.3.2 意味のある順序 | 実際の内容を順に読み、意味が成り立つかを画面・DOM・原典と比較する |
| 4.1.2 名前・役割・値 | 例えば配送方法の開閉部品で、表示ラベルと読まれる名前、部品の役割、開閉前後の状態、選択後の値を対応付ける |
| 4.1.3 ステータスメッセージ | 例えば保存前後を比較し、フォーカスを通知へ移さず完了の情報を取得できるか、操作中の発話とフォーカス記録で確かめる |

これは観察例であり、検査対象の限定ではない。各caseの全対象・状態・適用条件へ展開し、該当する原典と公開試験手順に沿って検証する。

読み上げは実装・ブラウザー・言語で表現が異なるため、必要な情報が含まれるかを評価する。単なる文字列一致だけで基準全体を判定しない。スクリーンリーダーのカーソルとDOMフォーカスも区別する。

`document.activeElement`は、ブラウザーのツールバー等へフォーカスが移っても以前の要素を示す場合がある。新しい観察には`documentHasFocus`も保存する。ブラウザー外の出力を対象部品の発話へ読み替えず、実際の入力経路と読み上げモードを確かめる。ネイティブOrcaでは、構造ナビゲーション後にPlaywrightのキー入力を混ぜると、DOMは変化しても期待する発話が得られない試行があった。同じページでXTestによるキー入力へ揃えた経路では、順次読みと状態変更の発話を取得できた。入力経路を変更した場合も、対象の状態と実出力を確かめてから採用する。

Guidepupの移動・操作APIはその呼び出し自体が発話を取得する。これをさらに`capture(() => reader.next())`等で包むと、内部の直列キューが待ち合う。`reader.*`は直接実行して発話ログを読み、Playwright等の外部操作だけを`capture()`で包む。

```sh
node scripts/screen_reader.mjs run --request /project/screen-reader-request.json --out /project/artifacts/speech-case-001
python3 scripts/audit.py attach --run /project/artifacts/wcag/run-001 --case <case_id> --file /project/artifacts/speech-case-001/screen-reader.json
```

必要な画面やステップごとのJSONもattachする。未対応環境や起動失敗は`blocked`として記録する。既存の証拠ディレクトリーは上書きしない。

Linuxでは、Orcaとブラウザーに同じ`DISPLAY`と`DBUS_SESSION_BUS_ADDRESS`を渡す。Guidepupが内部に作る非公開セッションの値が、呼び出し元の環境へ自動で公開されるとは扱わない。対応する専用環境では、例えば次のように一つのセッション内で実行する。`xvfb-run`、`xauth`、`dbus-run-session`等は事前に準備する。macOS・Windowsも検証用のデスクトップで対象ブラウザーを前面にする。

```sh
xvfb-run -a dbus-run-session -- node scripts/screen_reader.mjs run --request /project/screen-reader-request.json --out /project/artifacts/speech-case-001
```

既定のシナリオ範囲は最初のURLと同じorigin。認証等で別originへ移動する必要がある場合は、調査した範囲を`allowed_origins`配列へ明記する。範囲外へ移動した場合、保存済みのステップを残して停止する。

## 検証方法そのものを確かめる

同梱の`tests/fixtures/notifications.html`と`notifications-silent.html`は、保存後の見た目が同じで、後者にはライブリージョンがない比較用ページ。新しい環境では両方に同じ操作・期待値を適用し、前者の通知を取得し、後者を同じ成功にしないか確認する。ボタン名の取得も確認し、環境全体が沈黙している場合をページの問題と取り違えない。これは実行すべき試験の定義であり、対応環境で両ページの実発話を取得するまでは確認済みとしない。

名前が読めたことだけでは、ライブリージョンや開閉状態の取得まで確認済みにならない。使用する機能ごとに対照例を用意する。初回の成功後も、OS・ブラウザー・スクリーンリーダー・言語・主要な設定を変更した場合は、対応する方法を再確認する。

[通知の比較用ページ](https://github.com/k-s-h-r/wcag-audit-kit/blob/adf459777fa43ea0898a95e43edf5dbdde0684b7/tests/fixtures/live-region-variants.html)は、暗黙の役割・明示したライブリージョン・atomicの違いと、属性のない対照例を比較できる。現在のLinux環境では、Guidepupを経由せずOrca 48.1で[実操作と発話の比較](https://github.com/k-s-h-r/wcag-audit-kit/blob/adf459777fa43ea0898a95e43edf5dbdde0684b7/validation/native-orca/README.md)まで行った。対応する組合せで実行した事実を残し、別の組合せの動作保証へ広げない。

無発話の場合は、対象の状態へ到達したこと、表示された通知、フォーカス、読み上げ設定、観察時間、方法の対照試験を確認する。次にDOM・アクセシビリティAPIへの露出と、対象プロジェクトで必要なアクセシビリティサポートを調べる。特定の組合せで発話しないことだけで、基準全体の不適合を確定しない。[4.1.3の公式解説](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)は、支援技術が利用者の設定に応じて通知を遅らせたり抑制したりする場合も説明している。

通知に必要な意味を実ページで先に定める。例えば「保存しました」に加えて対象ファイル名が必要なのかを、表示内容・操作・文脈と照合する。ボタン名や以前の通知を読んだだけの結果を、今回の完了通知にしない。ログには操作・通知更新・発話の時刻と前後のフォーカスを残す。ファイルに遅れて書き込まれる形式のログを使う場合は、書き込み位置だけで操作を区切らない。

## 取得する証拠

`screen-reader.json`にはcase_id、事前に固定したシナリオのハッシュ、OS・カーネル、Guidepup・スクリーンリーダー・ブラウザーの版、操作、実際の発話、前後のフォーカス、期待値との比較を残す。途中で失敗しても保存済みのステップは残す。最後にブラウザーとスクリーンリーダーを終了する。

このアダプターのシナリオは、新しいブラウザーコンテキストでURLを開くところから始まる。監査対象のエラー・完了・ログイン後等を検証する場合は、その状態に到達する操作も含め、同じ状態に到達した証拠を付ける。初期表示の結果を別の状態の検証として流用しない。

`expect_contains`は部分一致。例えばcheckedはnot checkedやuncheckedにも含まれるため、必要な場合は`"expect_not_contains":["not checked","unchecked"]`も指定する。両アダプターで使用できる。期待する情報と実際の意味の照合、環境・観察時間・全対象の確認をこれだけで省略しない。

`collected`は収集が完了した意味。`assertion_failed`はシナリオの期待値と発話が一致しなかった意味であり、WCAG不適合を確定する前に原典と状態を確認する。`blocked`は未検証。この結果を各基準の記録へ接続し、ほかの条件・対象も調べてから判定する。

## LinuxのネイティブOrcaを使う

Guidepupのアセットの条件が合わない現在のLinuxでは、実際のOrcaを直接操作する`scripts/screen_reader_native.py`も使える。Debian 13、Orca 48.1、Chromiumで、通知・名前・チェック状態・見出し移動の[実シナリオ](https://github.com/k-s-h-r/wcag-audit-kit/blob/adf459777fa43ea0898a95e43edf5dbdde0684b7/validation/native-orca/scenarios/README.md)を確認した。VoiceOver・NVDAや別のLinuxの組合せまで確認済みとはしない。

`--root`には、Orca・Python GI/AT-SPI・Xvfb・Speech Dispatcher・espeak-ng等が既に用意されたDebianのパッケージのルートを指定する。必要な依存物がシステムに入っていれば`/`、隔離して展開した場合はそのディレクトリー。自動的にOSへインストールするコマンドではない。準備されていなければ、プロジェクトの検証環境に合わせて整備する。

[シナリオ例](../assets/screen-reader-native.example.json)を実際のcaseとページへ合わせてから実行する。

```sh
python3 scripts/screen_reader_native.py --root /tmp/wcag-at-root --request /project/native-reader-request.json --out /project/artifacts/native-speech-case-001
python3 scripts/audit.py attach --run /project/artifacts/wcag/run-001 --case <case_id> --file /project/artifacts/native-speech-case-001/screen-reader.json
```

操作は`browser.press`・`browser.click`・`browser.fill`と、`reader.nextHeading`・`previousHeading`・`nextLink`・`previousLink`・`nextLandmark`・`previousLandmark`・`nextButton`・`previousButton`。Orcaの標準の構造ナビゲーションキーを専用X11へ送る。`reader.press`で任意のキー操作を記す場合は、`"keys":["Shift_L","h"]`のようにX11のキー名を配列で指定する。[Orcaの構造ナビゲーション](https://help.gnome.org/users/orca/stable/commands_structural_navigation.html.en)に沿って、実際のモードと結果を確認する。

`observe`には、各操作後に表示テキストを取得する対象を指定する。`attributes`配列でrole・aria-checked等も同時に取得できる。`auth_state`を指定する場合、相対パスはシナリオファイルから解決する。`settle_ms`は各操作の観察時間で250〜10000ms、既定1500ms。非同期処理や長い発話に必要な時間を調べ、短い窓で得られない出力を永久的な沈黙と扱わない。

このアダプター自身が専用D-Bus・Xvfb・設定を作り、既存デスクトップへ入力せず終了する。Guidepupの版やOSの版を偽装して利用する方法ではない。`screen-reader.json`には実際のバックエンド・版・発話・状態・フォーカス・シナリオのハッシュを記す。元のOrcaログと各段階の画面もattachする。音声出力先はALSA nullであり、音の聴取や音響上の発音を調べた証拠にはしない。

同じOSアカウントで別のOrcaが動作中の場合は、既存のOrcaを維持したまま検証が中断される。検証は専用アカウントで行うか、同じアカウントの実Orca試行を順に実行する。起動できない場合は、`screen-reader.json` の結果と `orca.stdout` の起動ログを確認する。

起動オプションは指定されたOrcaの `--help` で確認し、その版が受け付けるものを使う。展開したルートにOrca用のコンパイル済みGSettingsスキーマがある場合は、専用のD-Busセッションでそのルートのデータとスキーマを使う。バージョンごとの発話やフォーカスの違いは、検証する経路と同じ操作を正常例で確かめる。
