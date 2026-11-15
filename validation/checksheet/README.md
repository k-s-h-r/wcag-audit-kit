# 人向けチェックシートの確認

確認日：2026-11-15。機能の表示と既存台帳からの集計を確認したもので、サイトや全基準の検証を新たに完了した記録ではない。

## 自動試験

`python3 -m unittest discover -s tests -p 'test_*.py'`で119試験が成功した。新しい13試験は`tests/test_checksheet.py`にある。[実行ログ](tests.txt)を保存した。

1.1.1で適合する情報画像と不適合な操作部品を持つ合成記録を使い、2つの確認観点、全体の不適合、未確認の併記、URL・状態・環境・対象・期待結果・証拠の対応を確認した。合成記録は表示の試験データであり、実ページの検証結果としては扱わない。

非適用と未実施、目標レベル外、未収集・未作成票、複数ページの分離、タスクの選択、多数の不適合箇所の全件保持を試験した。HTMLの文字列のエスケープと証拠URLの符号化、Excelの数式化防止、セル制限、固定見出し・印刷設定・内部リンクも確認した。workの人向けシートの編集が判定に取り込まれないこと、既存の作業用Excelの往復・競合試験が通ることも確認した。

## 2,200票の再出力

`validation/site-acceptance/run`をリポジトリ外の一時ディレクトリーへコピーし、そのコピーへ`report`と`excel export --mode report`を実行した。原本の判定・定義・証拠・過去の出力は変更していない。[集計の照合結果](site-checks.json)を保存した。

- 通過1,342、非適用762、判断保留80、不適合16。人の確認待ち80。検証未完了。
- 人向けチェックシートは86基準＋45観点＝131行。不適合箇所は16件すべて保持。
- 基準全体は、適合34、非適用10、未確認10、不適合1、目標レベル外31。
- Excelを読み戻し、人向け2シートの全セルをHTMLと共通の表示モデルと照合。シート内リンクが不適合箇所の正しい行を指すことも確認。
- 変更前の証拠ハッシュ一覧7,161件を全件照合し、不一致0。

## ブラウザー表示

Chromium 156とPlaywright 1.62で生成済みのHTMLをlocalhostから表示し、合成データの1280px・320pxと、2,200票の1280pxを確認した。文書全体には横方向のはみ出しがなく、表の中をスクロールできる。不適合の詳細リンクから対象行へ移動できた。axeのWCAG A・AA関連タグで検出0。[ブラウザー確認結果](browser-checks.json)を保存した。

- [合成データ・1280px](point-demo-1280.png)：1.1.1の複数観点と適否・未確認の併存。
- [合成データ・320px](point-demo-320.png)：狭い画面の文書と表内の横スクロール。
- [保存済み2,200票・1280px](site-1280.png)：元の判定から生成したチェックシート。

## 再現と未確認事項

```sh
python3 -m unittest discover -s tests -p 'test_checksheet.py' -v
cp -R validation/site-acceptance/run /tmp/wcag-checksheet-run
python3 scripts/audit.py report --run /tmp/wcag-checksheet-run
python3 scripts/audit.py excel export --run /tmp/wcag-checksheet-run --mode report --out /tmp/wcag-checksheet.xlsx
```

新しいコピー先と出力先を使う。既知の試験ページの保存済み記録を集計したもので、今回新しいサイト監査やスクリーンリーダー試験を行ったものではない。axe検出0はレポート自体のWCAG適合を証明しない。Microsoft Excel/Excel Onlineの画面での操作・共同編集・実際の印刷は未検証。観点は保存済みの期待結果に基づくため、未記録の観点を自動で網羅する機能ではない。
