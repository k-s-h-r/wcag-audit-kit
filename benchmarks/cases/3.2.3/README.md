# 3.2.3 の検証用ページ

このディレクトリのREADMEとsuite.jsonは採点側の資料です。検査担当へ渡すページ・素材はpublic内だけです。

| ケース | ページ | 状態 | 確認観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html)、[p02.html](public/p02.html) | comparison | 3.2.3-01 / `#menu` | 問題なし：2ページでメニューの相対順序が一致する。 |
| c02 | [p03.html](public/p03.html)、[p04.html](public/p04.html) | comparison | 3.2.3-01 / `#menu` | 問題あり：2ページ目で手続きとヘルプの相対順序が逆転する。 |

期待結果は作成者が定めた確認観点の対照例です。基準全体の網羅や、独立した専門家による正解の確認は表していません。モードごとの評価条件はsuite.jsonに記録し、実際に検証できた範囲は実行後の採点結果に表示します。

[検査手順](../../../skills/wcag-audit-kit/references/criteria/3.2.3.md) / [実行方法](../../README.md) / [ケースの追加](../../ADDING-CASES.md)
