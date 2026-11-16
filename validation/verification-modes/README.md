# 検証モードの選択・収集・作業指示・帳票の確認

0.7.0のmachine / ai / screen-reader / fullを、同じ所有する試験ページで実行した。これは検証方法の選択と記録・報告の試験であり、AIによる内容判断や実スクリーンリーダーの発話は今回実施していない。

## 確認結果

初回の収集は各モードとも2状態・機械検査133件。WCAGの110票はすべて未実施に保持した。機械検査の成功や対応表の○から適合判定を生成していない。

| モード | 保存した対象ページの画像 | 実スクリーンリーダーの状態 | WCAG検証完了 |
| --- | ---: | --- | --- |
| machine | 0 | 使用しない | いいえ |
| ai | 2 | 使用しない | いいえ |
| screen-reader | 0 | 未実施 | いいえ |
| full | 2 | 未実施 | いいえ |

ai / fullでは上限2枚を指定して、画像の省略と未確認も保持した。モード別の確認範囲は全86基準・131観点を含み、○・△・×と目標レベル外を表示する。対象ページの実画像と、以下の帳票画像は別の記録である。

machineの再開後は3状態になった。モードとrun.json、既存証拠16件を維持し、aiへの途中変更を拒否した。初回の数値は[summary.json](summary.json)、再開後の数値は[resume-observation.json](resume-observation.json)に分けている。ZIP内のmachineの最終帳票は再開後の結果である。

HTML・JSON・Excelで選択モードと対応範囲を照合した。Excelは先頭2シートを維持し、読み取り専用の「モード別の確認範囲」へ131行を追加した。実SRの選択だけで実施済みにせず、発話の観察記録がないものは未実施としている。

1280px・320pxで帳票を表示し、文書全体の横はみ出しなし、表へのTab到達と左右キーによるスクロール、axeのWCAG関連タグの検出0を確認した。[機械結果](checks.json)、[1280pxの帳票](mode-report-1280.png)、[320pxの帳票](mode-report-320.png)を参照できる。

Pythonの全162試験と、既存のスクリーンリーダーアダプターのNode 9試験が成功した。新しい19試験は、モードと観察設定の整合、altの存在・意味・実発話の区別、設定ファイル経由の選択、未実施の保持、スナップショット改変の拒否、旧runの維持、作業指示と帳票の対応等を含む。Nodeの試験はAPIの単体試験で、実発話の実証ではない。

## 証拠と再実行

- [Pythonの生出力](unit-python.txt)、[Nodeの生出力](unit-node.txt)、[ブラウザー試験の標準出力](browser.stdout.txt)と[標準エラー](browser.stderr.txt)。
- [proof.zip](proof.zip)に各runの設定・定義スナップショット・探索・入力・axe・画面・帳票・実行時の実装を保存した。[全内部ファイルの一覧とハッシュ](proof-inventory.json)を作り、全ファイルのバイトとCRCを照合した。
- 実行時の実装スナップショットは最終ソースとバイト単位で一致する。過去の7,185件の証拠・付属文書は変更していない。

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_screen_reader.mjs
python3 tests/verification_modes_browser.py --out /project/new-mode-validation
```

Chromium・PlaywrightとlocalhostのHTTP待受が使える環境で、空の出力先を指定する。新しい設定のinitから開始し、各モードの収集、再開、帳票の実ブラウザー確認まで行う。

AIの意味判断、実SRの起動・発話、音声・手話・閃光等の専門的な検証、任意のサイトの全状態の網羅、Microsoft Excel本体での操作・印刷は今回の試験範囲に含めていない。これらを対応表の○や試験件数から確認済みに広げない。
