# 修正担当向けの不適合記録

この記録は検証結果です。製品コードの変更は行っていません。

予定範囲の検査完了: いいえ
結果: 未実施 255、検査通過 1、不適合 2
全基準と範囲の未確認は[HTMLレポート](report.html)又は[JSON](report.json)を参照してください。

## 2.4.13 フォーカスの外観

対象: http://127.0.0.1:4325/focus-appearance.html?variant=thin / initial / desktop

再現手順:

- 全ソース・DOM・画面から操作対象と著者指定の表示を一つずつ特定
- 未フォーカスを撮影し、実キーTabで唯一の部品へ移動。フォーカスと前後の同じ位置・表示領域を照合
- 実色と位置から輪郭の全画素を特定し、sRGBで同じ画素の前後の3:1以上の面積をCSS px²で計算
- 本文・公式解説の面積と例外を照合し、測定値と実表示からこの基準だけを判定

対象要素: button#probe (Example button)
期待結果: 未フォーカスの部品の2 CSS px外周相当以上の面積で、同じ画素のフォーカス前後のコントラストが3:1以上となる。該当する原典の例外があれば確認する。
観察結果: このURLの操作部品はExample buttonの一つだけ。全HTML/CSS/JS、DOMと実画像を確認した。UA既定ではなくappearance:noneと著者指定の輪郭であり、著者が未変更のUA表示の例外を適用しない。実際のTab、documentHasFocus=true、同じ240×80の位置・DPR1・1000×700表示領域を確認した。コア収集の前後画像は別の校正実行と画素単位で同一だった。1pxの輪郭は白に対し6.5513:1で見えるが、同じ画素で3:1以上となる全領域は676 CSS px²。240×80の部品の2px外周相当1280 CSS px²を満たさず、代替の広い表示もない。線幅だけからではなく全輪郭の面積を比較した。
証拠: evidence/dc92b7131d34--initial--desktop/page.png, evidence/dc92b7131d34--initial--desktop/focus-001.png, evidence/dc92b7131d34--initial--desktop/keyboard.json, evidence/dc92b7131d34--initial--desktop/inventory.json, evidence/dc92b7131d34--initial--desktop/dom.html, evidence/dc92b7131d34--initial--desktop/input-events.json, evidence/attached/dc92b7131d34--initial--desktop--2.4.13/measurement/focus-measure.json, evidence/attached/dc92b7131d34--initial--desktop--2.4.13/measurement/request.json, evidence/attached/dc92b7131d34--initial--desktop--2.4.13/measurement/before.png, evidence/attached/dc92b7131d34--initial--desktop--2.4.13/measurement/focused.png, evidence/methods/focus-appearance/captures/thin/capture.json, evidence/methods/focus-appearance/fixture.html, evidence/methods/focus-appearance/capture-executed.py.txt, evidence/methods/focus-appearance/measure-source.py.txt

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#focus-appearance
このcaseの未確認: なし

## 2.4.13 フォーカスの外観

対象: http://127.0.0.1:4325/focus-appearance.html?variant=similar / initial / desktop

再現手順:

- 全ソース・DOM・画面から操作対象と著者指定の表示を一つずつ特定
- 未フォーカスを撮影し、実キーTabで唯一の部品へ移動。フォーカスと前後の同じ位置・表示領域を照合
- 実色と位置から輪郭の全画素を特定し、sRGBで同じ画素の前後の3:1以上の面積をCSS px²で計算
- 本文・公式解説の面積と例外を照合し、測定値と実表示からこの基準だけを判定

対象要素: button#probe (Example button)
期待結果: 未フォーカスの部品の2 CSS px外周相当以上の面積で、同じ画素のフォーカス前後のコントラストが3:1以上となる。該当する原典の例外があれば確認する。
観察結果: このURLの操作部品はExample buttonの一つだけ。全HTML/CSS/JS、DOMと実画像を確認した。UA既定ではなくappearance:noneと著者指定の輪郭であり、著者が未変更のUA表示の例外を適用しない。実際のTab、documentHasFocus=true、同じ240×80の位置・DPR1・1000×700表示領域を確認した。コア収集の前後画像は別の校正実行と画素単位で同一だった。未フォーカスでも青い4px輪郭があり、実キーTab後は#005bbaから#005cbbへ変わる。前後の同一画素は1.0134:1で、3:1以上となる面積は0 CSS px²。隣接白に対する強いコントラストを前後比較の代用にしない。
証拠: evidence/bc7a8de9e590--initial--desktop/page.png, evidence/bc7a8de9e590--initial--desktop/focus-001.png, evidence/bc7a8de9e590--initial--desktop/keyboard.json, evidence/bc7a8de9e590--initial--desktop/inventory.json, evidence/bc7a8de9e590--initial--desktop/dom.html, evidence/bc7a8de9e590--initial--desktop/input-events.json, evidence/attached/bc7a8de9e590--initial--desktop--2.4.13/measurement/focus-measure.json, evidence/attached/bc7a8de9e590--initial--desktop--2.4.13/measurement/request.json, evidence/attached/bc7a8de9e590--initial--desktop--2.4.13/measurement/before.png, evidence/attached/bc7a8de9e590--initial--desktop--2.4.13/measurement/focused.png, evidence/methods/focus-appearance/captures/similar/capture.json, evidence/methods/focus-appearance/fixture.html, evidence/methods/focus-appearance/capture-executed.py.txt, evidence/methods/focus-appearance/measure-source.py.txt

原典: https://www.w3.org/TR/2024/REC-WCAG22-20241212/#focus-appearance
このcaseの未確認: なし

