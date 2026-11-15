# 修正担当向けの不適合記録

この記録は検証結果です。製品コードの変更は行っていません。

予定範囲の検査完了: いいえ
結果: 未実施 170、検査通過 1、不適合 1
全基準と範囲の未確認は[HTMLレポート](report.html)又は[JSON](report.json)を参照してください。

## 2.3.3 インタラクションによるアニメーション

対象: http://127.0.0.1:4334/reduced-motion.html?variant=bad / initial / desktop

再現手順:

- 実際のTab/Enterで装飾の移動とCount増加を開始
- no-preferenceとreduceをChromiumでエミュレーションし、matchMediaの一致と実時間の位置・実画面を比較
- 全著者CSS/JS/UIを読み、別の無効化経路と本質的な動きの例外を照合

対象要素: button#runによる装飾の#boxの移動
期待結果: 本質的なものを除き操作起因の動きを無効にできるか
観察結果: 装飾の四角の移動はMove illustrationの実キー操作から始まり、通常設定では実時刻に応じてx座標が変わる。表示の主機能はCountの増加で、動きを止めてもCount=1として機能を保持する。reduceでもx=55→71→86.988と移動し、media queryに応答しない。全ソースとUIに別の無効化手段がなく、説明と機能から装飾の移動は本質的ではない。
証拠: evidence/b97405c438d1--initial--desktop/page.png, evidence/b97405c438d1--initial--desktop/inventory.json, evidence/b97405c438d1--initial--desktop/dom.html, evidence/b97405c438d1--initial--desktop/keyboard.json, evidence/methods/comparison.json, evidence/methods/source.html, evidence/methods/executed-source.py.txt, evidence/methods/bad-no-preference/observations.json, evidence/methods/bad-no-preference/0.png, evidence/methods/bad-no-preference/2.png, evidence/methods/bad-reduce/observations.json, evidence/methods/bad-reduce/0.png, evidence/methods/bad-reduce/2.png

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#animation-from-interactions
このcaseの未確認: なし

