# Profile demoの対象固有の手順 v1

2026-11-18、実行確認済みの範囲は以下の1経路。対象はtests/fixtures/audit_site_server.pyとaudit-site/。実装版はobserved.jsonのsource_sha256で固定する。ソースで読んだAPI・DOM・入力条件と、実ブラウザーで観察した結果は下記で分ける。

## 起動・準備

`python3 validation/development/T005/exercise.py --out artifacts/T005/route-002`を新しい出力先で実行する。専用のThreadingHTTPServerを127.0.0.1の空きポートへ起動し、GET /loginの200応答を準備完了とする。ブラウザーはChromium・新しいコンテキスト・1280×900。既存の利用者セッション、外部サービス、他の担当の待受ポートを使わない。

テスト用アカウントはfixtureのHelpとAPIで公開されたdemo@example.test／Test-password-42!。実アカウントではない。認証トークンを証拠へ保存せず、このプロセスのテスト用メモリーだけを使う。sourceを読み、/api/login・/api/profile・/api/logoutがローカルのみで処理されることを確認した。

## 到達・操作・観測する終状態

1. /profileへ未認証で入り、#signed-outの案内と、編集フォームがないことを確認する。
2. /loginで#login-emailと#passwordを埋め、#sign-inを押す。#login-statusにSigned in. Continue to profile.が表示されるまで待つ。
3. /profileを開き、#name=T005 Example、#email=t005@example.testを入力し、#reviewを押す。#review-panelの内容を確認する。
4. #backで編集へ戻り、入力値を保持していることを確認する。#reviewを再度押す。
5. #confirmを押し、#completion、#saved-name、#saved-emailがAPIの保存した値を表示するまで待つ。スクリーンショットとDOMの文字・フォーカスを保存する。
6. #sign-outを押し、#signed-outの表示と編集フォームがない状態へ戻る。新しいコンテキストを作り直す場合も未認証から始める。

実測では6段階の観察と17リクエストを記録した。POSTの成功と画面の完了表示は機能の観測であり、通知の実発話・キーボードの全経路・WCAG適合を意味しない。

## 復帰・証拠・後片付け

sourceの推測だけで結果を確定せず、observed.jsonの操作・URL・画面文字・実際のフォーカスを参照する。リクエストにはmethod・path・statusだけを記録し、cookieやパスワードを保存しない。画像はsaved.pngとsigned-out.png。

失敗時もfinallyでブラウザーとサーバーを閉じ、テスト用SESSIONSを消去する。サーバー停止後、元の待受ポートへ接続できないことと、画像・observed.jsonが残ることを確認する。既存出力先は再利用せず別のroute番号でやり直す。

手順と画面が合わない場合はビルドハッシュとselectorを照合する。起動不能なら環境、HTTP失敗なら準備・機能、終状態が不明なら未確認として記録する。実SR・拡大・媒体等の方法はこの経路では未実行。T011・T012へこの短い操作経路を渡せるが、AI判断や発話の観測はそれぞれ新規runで行う。
