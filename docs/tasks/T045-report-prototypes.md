# T045 保存済みrunから公開・提出用のレポートを試作する

状態は比較用の試作。保存済みの結論と基準ごとの判定を読む処理は[T021](T021-scope-conformance-report.md)と[T008](T008-machine-report.md)を使う。成果物は、同じrunを対象にサイト概要、ページ別達成状況、ACR検討版を見比べられる出力。各様式の構成を見直したあと、同じ条件で比較できた項目を共通化する。[ADR 0132](../adr/0132-prototype-public-report-layouts.md)

## 検討すること

| 試作 | 確認したいこと | 参考例 |
| --- | --- | --- |
| サイト検査結果の概要 | 検査期間、範囲、方法を読み、各ページの結果と残る確認に進めるか | [検査証明書](https://www.liberogic.jp/accessibility_report/) |
| ページ別 WCAG 達成状況 | URLとレベルが明確で、基準ごとの判定と根拠を見つけられるか | [WCAG達成状況レポート](https://www.liberogic.jp/lp/accessibility/accessibility_report/accessibility_lp/) |
| ACR検討版 | 製品・版、評価条件、基準別の補足が伝わるか。PDFでも表と説明を読めるか | [ACRのHTML](https://www.liberogic.jp/lp/accessibility/accessibility_report/vpat/) · [公式テンプレートを使ったPDFの例](https://www.liberogic.jp/lp/accessibility/accessibility_report/pdf/vpat-acr-iti.pdf) |

## 完了根拠と次の作業

合成台帳からの出力で、手続きの未確認、ページ固有の不適合、機械検査だけの候補を照合した。入力内の証拠と判定の一致、HTMLの相対リンク、保存先がすでに存在する場合の拒否を回帰試験で確認した。[再現方法と表示の記録](../../validation/development/T045/README.md)

次は、提出先と公開先に必要な記載項目を同じrunで確かめる。正式なACRは、使用するITIテンプレートの版、判定語、未評価の扱いを確認してから試す。検査証明書に必要な発行主体と確認手順、PDFの読み上げ順・見出し・表の関連付けも別に確認する。サイト概要からページ別結果へ進む構成を使い、統合版で共有する項目を決める。
