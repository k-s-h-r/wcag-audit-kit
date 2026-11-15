# ACTのタイトル検査を公開例で校正する

W3Cの承認済みルール2779a5（タイトルの有無）とc4a8a4（主題・目的の説明）を、選択した版の18例で確認した。HTMLの16例、SVGの2例を実際にChromiumで開き、DOMを取得した。目的の説明を調べるHTMLの6例とSVGの画面を実際に見た。

観察結果は18例すべて公開期待値と一致した。**公開期待値を参照して方法を校正した結果であり、独立した精度評価、全87ルールの実行、全WCAG基準の検証を示すものではない。**

HTMLのタイトルに関して、実際の内容と基準を照合した11件を台帳へ記録した。通過3件・不適合8件で、残る979件は未実施。SVGのACT上の適用対象外を、WCAG基準自体の対象外へ変換していない。

[HTML収集・基準別レポート](run-html/report.html) / [SVGの取得結果](run-svg/capture-manifest.json) / [ルール別の観察と証拠ハッシュ](observations.json)

SVGの最初の画像取得はタイムアウトした。失敗した記録を保持し、表示領域をCDPで取得する方法へ修正して2例だけを再収集した。応答はimage/svg+xml、ルートはSVG名前空間のsvgのまま保存した。

## 例ごとの結果

| ルール・例 | 公開期待値 | 実際の結果 | 観察・証拠 |
| --- | --- | --- | --- |
| 2779a5 / 7f9f315b5041 | 通過 | 通過 | 最初のHTML titleに、Unicode White_Space以外の文字を持つテキストノードがある。 [画面](evidence/2779a5/7f9f315b5041f3726662bf269613c43678af99d4.html/page.png)・[DOM情報](evidence/2779a5/7f9f315b5041f3726662bf269613c43678af99d4.html/inventory.json) |
| 2779a5 / 64771c390e57 | 通過 | 通過 | 最初のHTML titleに、Unicode White_Space以外の文字を持つテキストノードがある。 [画面](evidence/2779a5/64771c390e57375a822a7223362ea7bb859c0a96.html/page.png)・[DOM情報](evidence/2779a5/64771c390e57375a822a7223362ea7bb859c0a96.html/inventory.json) |
| 2779a5 / 6b3d2e2147cf | 通過 | 通過 | 最初のHTML titleに、Unicode White_Space以外の文字を持つテキストノードがある。 [画面](evidence/2779a5/6b3d2e2147cfc618b744f2dabfaf2e66327055d7.html/page.png)・[DOM情報](evidence/2779a5/6b3d2e2147cfc618b744f2dabfaf2e66327055d7.html/inventory.json) |
| 2779a5 / efa1e0438bb5 | 通過 | 通過 | 最初のHTML titleに、Unicode White_Space以外の文字を持つテキストノードがある。 [画面](evidence/2779a5/efa1e0438bb515332ec6b4d943044c336ca77fab.html/page.png)・[DOM情報](evidence/2779a5/efa1e0438bb515332ec6b4d943044c336ca77fab.html/inventory.json) |
| 2779a5 / 0ad882dffaf6 | 通過 | 通過 | 最初のHTML titleに、Unicode White_Space以外の文字を持つテキストノードがある。 [画面](evidence/2779a5/0ad882dffaf6edd16058119e1c513b4746b0ac27.html/page.png)・[DOM情報](evidence/2779a5/0ad882dffaf6edd16058119e1c513b4746b0ac27.html/inventory.json) |
| 2779a5 / 820fb18c9bb2 | 失敗 | 失敗 | 最初のHTML titleが不在、又はそのテキストノードが空・空白のみ。後続のtitleで置き換えない。 [画面](evidence/2779a5/820fb18c9bb20fb1a940a0806a87c6f6e468bb5b.html/page.png)・[DOM情報](evidence/2779a5/820fb18c9bb20fb1a940a0806a87c6f6e468bb5b.html/inventory.json) |
| 2779a5 / 314d991fa532 | 失敗 | 失敗 | 最初のHTML titleが不在、又はそのテキストノードが空・空白のみ。後続のtitleで置き換えない。 [画面](evidence/2779a5/314d991fa5328e41f8a806bfbac84d748b41f7ed.html/page.png)・[DOM情報](evidence/2779a5/314d991fa5328e41f8a806bfbac84d748b41f7ed.html/inventory.json) |
| 2779a5 / 5fd6fda771cf | 失敗 | 失敗 | 最初のHTML titleが不在、又はそのテキストノードが空・空白のみ。後続のtitleで置き換えない。 [画面](evidence/2779a5/5fd6fda771cf8810eef5166464622d6979e0406e.html/page.png)・[DOM情報](evidence/2779a5/5fd6fda771cf8810eef5166464622d6979e0406e.html/inventory.json) |
| 2779a5 / a14968698b0e | 失敗 | 失敗 | 最初のHTML titleが不在、又はそのテキストノードが空・空白のみ。後続のtitleで置き換えない。 [画面](evidence/2779a5/a14968698b0e95b6624f187d4538e320e4fa8952.html/page.png)・[DOM情報](evidence/2779a5/a14968698b0e95b6624f187d4538e320e4fa8952.html/inventory.json) |
| 2779a5 / 4eeff9c95f15 | 失敗 | 失敗 | 最初のHTML titleが不在、又はそのテキストノードが空・空白のみ。後続のtitleで置き換えない。 [画面](evidence/2779a5/4eeff9c95f15e90ca5abc972079112d1ea5c3d51.html/page.png)・[DOM情報](evidence/2779a5/4eeff9c95f15e90ca5abc972079112d1ea5c3d51.html/inventory.json) |
| 2779a5 / ecc29b73e37b | 適用対象外 | 適用対象外 | 実際の応答はimage/svg+xmlで、ルートはSVG名前空間のsvg。HTML文書を対象にするこのACTルールの適用条件を満たさない。WCAG基準自体の対象外とは判定しない。 [画面](evidence/2779a5/ecc29b73e37b6a125b3fd9767068dcaa368d467a.svg/page.png)・[DOM情報](evidence/2779a5/ecc29b73e37b6a125b3fd9767068dcaa368d467a.svg/inventory.json) |
| c4a8a4 / c19c231ab517 | 通過 | 通過 | 本文がクレメンタインの収穫時期を説明し、題名がその主題を示している。 [画面](evidence/c4a8a4/c19c231ab5175fb62b6a74b998aec0dd965c25c5.html/page.png)・[DOM情報](evidence/c4a8a4/c19c231ab5175fb62b6a74b998aec0dd965c25c5.html/inventory.json) |
| c4a8a4 / 107a5e462b4a | 通過 | 通過 | 最初の題名は本文のクレメンタインの収穫時期と一致する。2番目のtitleをブラウザーは題名として使っていない。 [画面](evidence/c4a8a4/107a5e462b4ad6dd297742a2a177e24d32d27c26.html/page.png)・[DOM情報](evidence/c4a8a4/107a5e462b4ad6dd297742a2a177e24d32d27c26.html/inventory.json) |
| c4a8a4 / 2f9709573bf0 | 通過 | 通過 | body内のtitleをブラウザーが題名として取得しており、本文の収穫時期を説明している。配置だけで不適合にしない。 [画面](evidence/c4a8a4/2f9709573bf080a0feccfb2fd4b4a657383ef235.html/page.png)・[DOM情報](evidence/c4a8a4/2f9709573bf080a0feccfb2fd4b4a657383ef235.html/inventory.json) |
| c4a8a4 / 2c1397032aad | 失敗 | 失敗 | 題名はリンゴの収穫時期だが、本文はクレメンタインの収穫時期。対象の果物が異なり、ページの主題を説明していない。 [画面](evidence/c4a8a4/2c1397032aad720fe43dee2be0d326be56957320.html/page.png)・[DOM情報](evidence/c4a8a4/2c1397032aad720fe43dee2be0d326be56957320.html/inventory.json) |
| c4a8a4 / 1844d7bce889 | 失敗 | 失敗 | ブラウザーが使う最初の題名は本文の主題を示していない。2番目の適切なtitleは題名として使われない。 [画面](evidence/c4a8a4/1844d7bce889d85a80b620468baa804eab3ff2c8.html/page.png)・[DOM情報](evidence/c4a8a4/1844d7bce889d85a80b620468baa804eab3ff2c8.html/inventory.json) |
| c4a8a4 / 4c72b3b9b06b | 失敗 | 失敗 | 実画面は大学サイトでのaccessibilityの検索結果。題名の大学名だけでは、検索結果という現在の目的を説明していない。 [画面](evidence/c4a8a4/4c72b3b9b06bf1edc3c959070731b65871ee0c8f.html/page.png)・[DOM情報](evidence/c4a8a4/4c72b3b9b06bf1edc3c959070731b65871ee0c8f.html/inventory.json) |
| c4a8a4 / 85469fd266d3 | 適用対象外 | 適用対象外 | 実際の応答はimage/svg+xmlで、ルートはSVG名前空間のsvg。HTML文書を対象にするこのACTルールの適用条件を満たさない。WCAG基準自体の対象外とは判定しない。 [画面](evidence/c4a8a4/85469fd266d3e8706f551dcd65261709311123d0.svg/page.png)・[DOM情報](evidence/c4a8a4/85469fd266d3e8706f551dcd65261709311123d0.svg/inventory.json) |

## 再現に使った原典

[ルールの使用方法](../../references/ACT.md)、[2779a5](../../references/sources/act/rules/2779a5.md)、[c4a8a4](../../references/sources/act/rules/c4a8a4.md)、[試験ページの出典](../../tests/fixtures/ACT-title-sources.json)を保存している。

収集先をコピーしたレポートは相対パスを保っている。スキルのルートから再生成できる。未実施が残るためstrictの終了コードは2。

```sh
python3 scripts/audit.py report --run validation/act-title/run-html --strict
```

