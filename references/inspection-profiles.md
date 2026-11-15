# 観察の深さと作業量を選ぶ

| profile | 画像 | 実スクリーンリーダー | 1回の収集での画像上限 / ページ | 用途 |
| --- | --- | --- | ---: | --- |
| quick | off | off | 0 | DOM・ツリー・キー操作等による予備確認。画面を調査済みにしない |
| standard | states | optional | 12 | 状態ごとの実画面を見て操作対象を調べる通常の入口 |
| thorough | all | required | 60 | 途中の操作・キー移動の画像と実SRも求める確認 |

screenshotsはoff / states / all。statesは各状態・環境の最終表示、allは操作前後・キー移動等も保存する。max_imagesを超えた画像は省略理由をmanifestへ残す。画像を保存したことと、AIが実際に見たことは別である。

screen_readerはoff / optional / required。収集器はDOMとAXツリーを取得するが、それは実SR確認ではない。requiredの場合はページ検証スキルがGuidepup・実Orca等で実操作・発話を確認し、操作調査票へ方法と証拠を保存する。環境がなければ未実施と必要な人への確認を残す。

```yaml
inspection:
  profile: standard
  screenshots: states
  screen_reader: optional
  max_images: 12
```

単独ページはCLIでも選べる。

```sh
python3 scripts/audit.py page --url https://example.com/contact --out /project/run-page --profile standard
python3 scripts/audit.py page --url https://example.com/contact --out /project/run-quick --profile quick
python3 scripts/audit.py page --url https://example.com/contact --out /project/run-custom --screenshots all --max-images 8 --screen-reader off
```

この上限はCLIの収集処理1回の各ページに適用する。追加probeや外部ツールの画像は別の操作になるため、AIは残る予算と必要性を確認し、保存済みの画像を再利用する。1回の応答へすべての画像を読み込まず、担当ページ・状態・対象の画像から読む。

実トークン数は画像の寸法、AIモデル、会話、実際に読み込む資料等で変わる。この設定は消費トークンや料金の保証ではない。原典を必要な基準だけ読むこと、報告だけなら再検査しないことも作業量の調整に含む。

## 省略と検証結果

画像off、上限、未到達、実SR未実施を対象外へ変えない。観察していない条件は判断保留・未確認として残す。視覚的な操作調査が未完了の新しいrunは、全体の検証完了にしない。requiredの実SRも未実施なら検証未完了を保持する。

optional又はoffで実SRを省略しても、実SRで確認したと報告しない。各基準で必要な観察を満たせる別の方法があるか、原典と実際の内容から判断する。設定名だけで全基準の合否を決めない。

旧runにはinspectionの指定がないものがある。従来の収集方法として読み取り、後から新しい観察を実施済みに変更しない。
