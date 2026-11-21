# 工作室の見学予約で、キーだけで人数を選べるようにする

キーボードだけで見学予約を進めると、人数を増やせず、確認画面の手前で止まった。人数を増やす部品と、確認ボタンのアクセシブルな名前を変更し、同じキー入力で比較した。

## 人数を増やす操作で止まる

開始リンクをTabとEnterで開き、Tabで「人数を増やす」に移動した。Enterを押しても1名のままで、「予約内容を確認する」を押すと2名以上を選ぶよう案内された。T022の問題例ではSpaceでも1名のままで、同じ部品をクリックすると2名になった。その後、TabとEnterで確認画面に進めた。確認ボタンの表示は「予約内容を確認する」、ブラウザーが公開する名前は「詳細を見る」だった。 [T022の操作と証拠](../T022/README.md#問題例ではキーで増員できなかった)

## 試作では同じ6回のキー入力で確認画面に着いた

増員には `<button type="button">` を使い、既存のクリック処理で人数を変える。確認ボタンから「詳細を見る」の `aria-label` を外し、画面の「予約内容を確認する」を名前に使う。

| 確認項目 | 変更前 | 試作 |
| --- | --- | --- |
| Tab → Enterを3回 | 人数は1名のまま。2名以上を選ぶ案内で止まった | 人数が2名に変わり、確認画面に日付と人数が表示された |
| 確認ボタンをフォーカスしたときの名前 | 詳細を見る | 予約内容を確認する |

Chromium 156.0.8078.79、1280×900で確認した。別の試行でも、試作の増員ボタンはEnterとSpaceでそれぞれ人数を変更できた。支援技術の発話、別の表示幅やブラウザー、実際の利用者による操作は未確認。

[比較の操作記録](run-002/result.json) · [変更前の画面](run-002/before.png) · [試作の確認画面](run-002/after.png)

[変更前のアクセシビリティツリー](run-002/before-review-name.txt) · [試作のアクセシビリティツリー](run-002/after-review-name.txt)

## 読み手が変更と確認手順を説明できた

別のエージェントに点検レポートの本文を読んでもらった。キーボード利用者が増員で止まること、標準ボタンへの変更と `aria-label` の削除、TabとEnterを3回押して確認画面に進み、ボタン名を表示と照合する手順を説明できた。ほかの手続きでも使うには、改善案の効果を確かめる観察項目と、読み手による理解の確認を増やす。

## WCAG検査票と併用する

同じ経路のWCAG検査票には、キーボード操作の2.1.1と、表示ラベルと名前の2.5.3の不適合がある。復元した試験ページの一方に改善案を適用して比較した。元の操作記録のSHA-256は今回の実測値と検査票の添付記録で一致する。

[T022の検査票と不適合箇所の照合](../T022/run-001/score.json) · [T022の操作記録](../T022/run-001/observations.json)

## 同じ試験を再実行する

リポジトリのルートで、T022の問題例 `rb` を2組コピーする。一方の人数選択ページだけを `public/after/visit.html` で置き換える。共通の `site.css` は両方の親ディレクトリーに置く。`button` と `[role=button]` に同じ装飾を使い、どちらもフォーカス位置が分かるようにする。 [改善試作のHTML](public/after/visit.html) · [共通のCSS](../T022/fixture/site.css)

```sh
t023_public=$(mktemp -d)
t023_fixture=validation/development/T022/fixture
cp -R "$t023_fixture/rb" "$t023_public/before"
cp -R "$t023_fixture/rb" "$t023_public/after"
cp "$t023_fixture/site.css" "$t023_public/site.css"
cp validation/development/T023/public/after/visit.html "$t023_public/after/visit.html"
python3 -m http.server 43823 --bind 127.0.0.1 --directory "$t023_public"
```

別の端末で、Playwrightと `/usr/bin/chromium` が使える環境から実行する。

```sh
t023_evidence=$(mktemp -d)
python3 validation/development/T023/measure.py \
  --origin http://127.0.0.1:43823 --out "$t023_evidence/run" \
  --original validation/development/T022/run-001/observations.json
```
