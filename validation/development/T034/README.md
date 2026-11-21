# T034 Tabのフォーカスに伴う文書移動要求と遮断

通常の `page-audit` へ公開ページのURLだけを渡す。表示幅はPC相当1280×900とスマートフォン相当320×900 CSS px。機械モード、AAA、初期画像のみとし、初期取得の後に `--resume --quick-explore` を実行する。問題集の達成基準、想定操作、対象、期待値はCLIには渡さない。[T020の測定条件](../T020/README.md)

T020の071・072は3.1.1の回帰対照、073・074は3.2.1-02の問題例と正常例。さらに、3.2.1のc01・c02と、移動要求のきっかけを変えたループバック専用の対照を使う。書き込み先と移動先もローカルの対照ページを使う。

## 証拠の読み方

`page/work/evidence/<観察>/keyboard-trace-stop.json` の `focus_navigation` は、受け取ったTabのキー押下、フォーカス、ブラウザーの `navigate` 通知、Tabのキーアップへの添字を保存する。四つのイベントは同じディレクトリーの `input-events.json` にある。`isTrusted`、メインフレーム、移動元の文書IDとURL、フォーカス先、`focusDispatchPhase`、移動先URLを照合する。キーアップの `navigationAtKeyup` では、同じ通知が配信を終え、取り消しや中断を受けていないことを確認する。照合する文書要求は停止記録の `blocked_requests` にある。HTMLの操作経路詳細とJSONの `exploration.remaining` に、この観察と保存先が出る。

子フレームが補助観察中に見つかった場合は、停止記録に `child_frame_observed` を残す。トップの文書に通知が出ない移動経路があるため、発生元の照合は保留する。

`status: blocked` は、移動先の文書への通信を制限したことを表す。移動先を受信したかはサーバーの受信記録と照合する。3.2.1の適否には、移動先の表示やほかのフォーカス先、操作結果などの追加の確認が残る。T020の採点器と採点結果はそのまま保持する。

## 再実行

```sh
python3 validation/development/T034/run.py --out /tmp/t034-new
```

変更前を測る場合は、新しい場所に `8520421` の `benchmarks`、`skills`、`scripts` を展開し、`--repo <展開先> --expect before --case 071 --case 072 --case 073 --case 074 --case focus-c01 --case focus-c02` を指定する。出力先は毎回分ける。
