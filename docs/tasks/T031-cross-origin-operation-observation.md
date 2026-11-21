# T031 操作中の別オリジンへの通信を実測する

状態は、統合版 `5bb4a80` から分岐した作業ブランチでローカル対照の計測を完了。[PR #99](https://github.com/k-s-h-r/wcag-audit-kit/pull/99)で提出。前提は[T019](T019-post-operation-rechecks.md)と[統合版の検証](../../validation/development/vision/README.md)。[Issue #82](https://github.com/k-s-h-r/wcag-audit-kit/issues/82)

[VISION](../VISION.md)の手続きを本番相当の環境へ広げるには、許可した範囲から外への通信と、通信制限で確認できなくなった動作を把握する必要がある。通常の自動探索が書き込みメソッド、WebSocket、別文書への移動をどう扱うかを出発点に、別オリジンへの読取通信が受信側に届くかを測る。

## 作業と成果物

- `127.0.0.1` の別ポートに検査対象と受信側を立てる。固定の画面を通常の `page-audit` で収集し、ボタン操作による通信を受信側の記録と探索台帳で照合する。
- 許可したローカルオリジンだけへ転送する試験用HTTPプロキシを使い、同じ検査を別runで繰り返す。状態を取得できた動作と、制限によりデータを取得できなかった動作を記録する。
- 再現スクリプトと両方の記録を `validation/development/T031/` に保存する。[ADR 0110](../adr/0110-measure-cross-origin-requests-during-operation.md)

## 完了条件と確認

- 初期画面とボタン操作で生じるリクエストを区別する。直接取得、画像、リダイレクト後の取得、POST、WebSocketを対象に、受信側に届いたかを示す。
- HTTPプロキシを使った対照では、許可先の操作中の読取を確認でき、別オリジンの受信側への到達件数と拒否の記録が分かる。
- 通信制限が検査対象の表示や機能に及ぼす影響を示す。製品の既定動作、HTTPS、ブラウザー外の通信、OSレベルの隔離に関する判断は個別に記す。

## 担当範囲と引き継ぎ

ブランチは `codex/t031-cross-origin-operation-observation`。通常の探索では、別オリジンの受信先に操作後のGETが届いた。ローカルHTTPプロキシを明示すると、実測した4種類の別オリジンへのGETの到達が0件になり、同一オリジンへの操作後のGETは両条件で受信できた。通信を制限した画面では日時を取得できなかった。[実測記録](../../validation/development/T031/README.md)

HTTPSのループバック対照でも、直接接続と `CONNECT` を制限するプロキシ経由を比較した。直接接続では別オリジンに28件のGETが届き、プロキシ経由では0件だった。両方で同一オリジンの操作後のGETが6件届き、日時を取得できない場合の表示も両幅で確認した。[PR #106](https://github.com/k-s-h-r/wcag-audit-kit/pull/106) · [HTTPSの実測と独立レビュー](../../validation/development/T031/https.md) · [ADR 0117](../adr/0117-observe-https-operation-through-connect-proxy.md)

次は、ブラウザー以外の通信を含むプロセスのネットワーク分離と、実環境で読み込みに必要なHTTPS配信先とリダイレクト先を確かめる。データを取得できなかった操作を未確認として返す条件も合わせて確認する。
