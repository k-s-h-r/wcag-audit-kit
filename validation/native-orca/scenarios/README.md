# ページ固有のシナリオによる実発話の校正

`screen_reader_native.py`で、専用D-Bus・Xvfb・Debian Orca 48.1を起動し、ページ固有の操作と期待値を渡した。Guidepupとは別の実バックエンド。Orcaのプログラムは変更していない。

## 通知と移動

[4ステップの結果](navigation-and-notification/screen-reader.json)では、Tabで2つの保存ボタンへ移動し、名前を取得した。次にSpaceで保存し「Record two saved.」の発話を取得、Orcaのhで次の「Nonatomic status heading 2」へ移動した。全4期待値が一致した。通知時のフォーカスも保存ボタンのままだった。

## 見た目とチェック状態

[正常例](state-good/screen-reader.json)と[失敗例](state-bad/screen-reader.json)で同じ操作を行った。両ページのボタン名・初期の役割と状態を取得できた。Space後も同じボタンにフォーカスが残り、見た目はOn、もう一度SpaceでOffになった。

| 状態 | 正常例のaria-checked／発話 | 失敗例のaria-checked／発話 |
| --- | --- | --- |
| 初期 | false／Email notifications check box not checked. | false／同じ初期発話 |
| Onへ操作後 | true／checked | falseのまま／観察窓内に状態変更の発話なし |
| Offへ操作後 | false／not checked | falseのまま／観察窓内に状態変更の発話なし |

操作後の実画面、表示テキスト、role・aria-checkedの実測値、発話、前後のフォーカスを対応付けた。両方の見た目がOnとなる[正常例の画面](state-good/step-2.png)と[失敗例の画面](state-bad/step-2.png)も保存している。単なる名前の存在確認だけでは、状態の問題を確認できない。

正常例はcollected・終了コード0。失敗例は状態の期待値が不一致となりassertion_failed・終了コード1。どちらも環境の起動失敗としてblockedにはしていない。これらは比較方法の校正であり、WCAG基準全体の合否を自動生成していない。元の依頼と観察は[対応表](comparison.json)にある。

## 保存した証拠

各実行先にrequest.json、screen-reader.json、各stepのJSONと画面、Orcaの生ログ、パッケージの版・配布物のハッシュを保存した。依頼と生ログのSHA-256が一致することも確認した。観察窓は約1.8秒であり、それより長い非同期処理の試験を代表しない。

最初の版確認で二つ目のOrcaを起動する方法は、この環境で失敗した。その後は、起動したOrca自身が生ログに記録する実際の版を取得した。生ログは専用PTYを経由して取得し、発話自身のUTC時刻で操作へ対応付ける。最終結果では完全なログから再照合する。

実際に確認した機能は、名前・役割・チェック状態、通知、hによる見出し移動。全ての構造ナビゲーションコマンド、表、複雑なアプリケーション、他言語・他のOSをこの3例だけで確認済みとしない。
