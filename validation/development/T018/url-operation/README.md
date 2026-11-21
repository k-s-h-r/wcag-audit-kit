# URLからアコーディオンのEnterとSpaceを比較する

統合版 `5bb4a80` の配布用 `wcag-page` を使い、同じボタンと本文がある2ページをChromium 156.0.8078.79・Playwright 1.62.0で検査した。1280×900と320×900 CSS pxのそれぞれで、対照2ページの初期PNGはバイト単位で一致した。HTMLとCSSは共通で、問題対照ではボタンのEnterとSpaceに対する既定動作を止めている。[事前に固定した条件](conditions.md) · [採点側の期待](expected.json)

対照HTML、期待した開閉結果、共通の探索条件を収集前に決めた。ツリーの対象を識別するため、対照HTMLに元からあったボタン名を、収集中に採点側の期待ファイルへ追記した。

| 実際に入力した操作 | 正常側 | 問題側 |
| --- | --- | --- |
| マウスで開く・閉じる | 開閉できた | 開閉できた |
| Enterで開く | 開いた | 同じボタンに届き、閉じたままだった |
| Spaceで開く | 通常探索で開いた | 通常探索で同じボタンに届き、閉じたままだった |
| Enterで開いたあとのTab | パネル内のリンクへ移動 | Enterで開く経路がなかった |

開閉後の本文の表示は `aria-expanded` とChromiumのアクセシビリティツリーの `expanded` に両幅で一致した。これはブラウザーが公開する展開状態の記録で、実スクリーンリーダーの発話はこの試験では扱っていない。問題側の機械行は観察した入力と閉じたままの事実を記録し、2.1.1の判定を保留した。両対照のページ全体も未確認のままだった。[簡易探索の記録](run-002/quick.json) · [通常探索の記録](run-002/full.json) · [証拠ファイル](run-002/evidence.zip)

既定の簡易探索では通常のボタンにEnterを選ぶため、この対照でSpaceは両幅とも採集されなかった。通常のCLIから `--resume --explore` を指定した別runでは、同じURLだけを渡して追加のSpaceを観察できた。探索の上限や候補を変更する実装は加えていない。

簡易探索は正常側が24ステップ、問題側が20ステップで、残ったキューは両方とも0件だった。通常探索は両方とも48ステップで、正常側に11件、問題側に4件の候補が残った。通常探索で開いた正常側は、両幅でTabが本文内のリンクへ進んだ。PC幅ではShift+Tabで開閉ボタンへ戻った。320幅での復帰と、その後にEnterで閉じる操作は今回の上限内で実施しなかった。両幅で最後までたどった別の対照は[従来のT018の記録](../README.md)にある。

別エージェントが簡易探索を別のブラウザーrunで再現した。通常探索は、収集済みの原始ファイルと報告を別の採点器で照合し、両幅でSpaceが対象に届いた入力と前後の状態を確認した。[独立した簡易探索](run-002/independent-quick.json) · [その原始証拠](run-002/independent-quick.zip) · [通常探索の独立照合](run-002/independent-full.json)

通常探索も別ポートのChromiumで両例48ステップを再実行した。両幅で実Spaceに対する表示と展開状態が一致し、Shift+Tabによる復帰はPC幅で確認した。閉じる最後のEnterは両幅とも未観察だった。採点器と99点の取得記録をまとめたZIPのSHA-256は `9f565cf8f0f6e1ceec2176f99572ac0b1591044fd843652c3e0f3fe0d3ea613f`。[独立した通常探索の結果](run-003/independent-full.json) · [原始証拠](run-003/independent-full-receipts.zip)

## 再実行

ChromiumとPlaywrightが利用できる環境で、別々の出力先を指定する。収集は公開対照のURLと共通設定だけを使う。採点は収集後に実行し、マウスのクリック、信頼されたキーダウン、前後の表示と展開状態を照合する。Spaceは探索経路の指定と、同じ試行で開閉ボタンに届いた修飾なしの文字キーを照合する。

```sh
python3 validation/development/T018/url-operation/collect.py --profile quick --out /tmp/t018-quick
python3 validation/development/T018/url-operation/score.py --run /tmp/t018-quick
python3 validation/development/T018/url-operation/collect.py --profile full --out /tmp/t018-full
python3 validation/development/T018/url-operation/score.py --run /tmp/t018-full
```

通常探索で使った上限は48ステップ、16状態、深さ4。初回の収集は、ブラウザーを並行実行したときに収集スクリプトの360秒の上限に達し、正常側は44、問題側は41ステップで中断した。元の台帳を保存し、コピーを同じURLと探索上限で再開した。証拠ZIPに初回のコマンドと再開のログを収録した。現行の収集スクリプトは、同じ探索上限に達するまでの時間に余裕を設けている。

以前の統合検証は簡易探索の深さ4でEnterによる開閉を検証し、Spaceの経路は採集していなかった。Pythonのページ検査テスト32件と配布用スキルの同期も確認した。[以前の試験条件](../README.md) · [ADR 0114](../../../../docs/adr/0114-verify-accordion-input-variants-from-urls.md)
