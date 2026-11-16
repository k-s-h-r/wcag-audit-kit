# 検証用のケースを追加する

検証方法を開発・保守する人向けの手順です。ページと正解を先に用意してから検出器を実行します。既存の例では[2.4.2](cases/2.4.2/suite.json)が小さく、[3.2.3](cases/3.2.3/suite.json)は複数ページ、[1.1.1](cases/1.1.1/suite.json)は操作後の状態を扱っています。

1. `cases/達成基準番号/public/`へHTMLと素材を置きます。外部サイトへ依存させず、問題のある例と正常な例を用意します。
2. 同じ基準の`suite.json`へ、ケース・確認観点・期待結果・根拠を記録します。検査担当へ渡す資料は`public/`と、実行時に生成するタスクだけです。
3. 初期表示に加え、必要な操作後の状態も指定します。モーダルを開く、字幕を有効にするなど、検査する状態へ到達する方法を書きます。
4. 正解を固定してから収集・採点します。採点結果を見て、正解を検出器に合わせる変更はしません。

## suite.jsonの項目

| 項目 | 記録する内容 |
| --- | --- |
| `schema_version` / `version` | 形式の版と、その基準の問題集の版。初版はどちらも`"1"` |
| `criterion` | ディレクトリ名と同じ達成基準番号 |
| `review` / `sources` / `scope` | 正解の確認者、WCAG本文や試験手順の出典、問題集で扱う範囲。作成者のみの確認なら`author-defined` |
| `cases[].id` / `pages` | `c01`等の中立なIDと、`public/`からのページの相対パス。比較するページは1ケースにまとめる |
| `checkpoints` | [確認観点の定義](../references/verification-checkpoints.json)にあるID。基準全体の合否に広げない |
| `states` | 状態のID、到達方法、確認する内容。`actions`は担当向けの操作情報であり、収集器が必ずその状態を探索できたという意味ではない |
| `oracle_scope` | `exhaustive-for-listed-checkpoints`。指定観点について、そのケース内の対象と正解を列挙したことを示す |
| `expectations` | 下表の単位で正解を記録。同じ基準に複数の対象・状態・確認観点があれば行を増やす |
| `target_aliases` | 細部の指摘を同じ論理部品へ対応させる公開情報。例：字幕ボタンの指摘を動画へまとめる |

## 期待結果の1行

| 項目 | 記録する内容 |
| --- | --- |
| `page` / `state` / `target` / `checkpoint` | どのページの、どの状態・対象・確認観点か。この組み合わせで採点する |
| `expected` | `passed`、`failed`、`inapplicable`。その観点について定めた正解 |
| `rationale` | 正解の根拠。属性の有無、機能の動作、意味の一致など、何を確かめた正解なのかを書く |
| `modes` | 4モードそれぞれで`evaluate`又は`defer`。評価を求める観点が未実施なら未確認。省いた観点も合格に数えない |
| `evidence_kind` | `program`、`semantic`、`visual-semantic`、`cross-page`、`screen-reader`。画像・全比較ページ・実SRの証拠が必要な観点を指定する |

例えば`1.1.1-01`のaltの有無と、`1.1.1-04`の画像と代替内容の意味の一致は別の行です。altが存在するだけで後者を通過にしません。`2.1.1-01`の実キーの到達・送出と、`2.1.1-02`の機能の完了も分けます。

登録した観点について、正解にない追加の不適合指摘は誤検出として数えます。正常な対象も確認し、同等な代替操作などの例外も含めてから、列挙済みと宣言してください。対象を調べきれていないケースを、網羅済みの正解として使わないでください。

## 追加後に実行する

```sh
python3 benchmarks/run.py inventory
python3 -m unittest discover -s tests -p test_benchmarks.py
python3 tests/benchmark_fixtures_browser.py --out /project/fixture-check-new
python3 benchmarks/run.py collect --mode all --criterion 2.4.2 --out /project/benchmark-new
```

最後の基準番号は追加した基準に置き換えます。ケース数を固定した構造試験と、`benchmark_fixtures_browser.py`の動作確認も更新します。ページの動作確認は、検出器が問題を検出できたかの試験とは分けて記録します。

問題集を変えると全体のハッシュが変わります。変更前後の検出方法を比較する場合は、同じ問題集の版を両方に使います。例や正解自体の修正は、新しい版と根拠を残してから再実行します。
