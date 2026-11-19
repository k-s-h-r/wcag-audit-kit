# 観察の深さと作業量を選ぶ

検証に使うAI・実スクリーンリーダーの選択は[検証モード](verification-modes.md)で行う。以下のprofileはモード未指定時の従来の既定値。モードを明示した場合、実SRはモードのrequired/offに従い、画像の深さと枚数をこの設定で調整する。

| profile | 画像 | 実スクリーンリーダー | 1回の収集での画像上限 / ページ | 用途 |
| --- | --- | --- | ---: | --- |
| quick | off | off | 0 | DOM・ツリー・キー操作等による予備確認。画面を調査済みにしない |
| standard | states | optional | 12 | 状態ごとの実画面を見て操作対象を調べる通常の入口 |
| thorough | all | required | 60 | 途中の操作・キー移動の画像と実SRも求める確認 |

標準の証拠画像は、機械のみを含むすべてのモードで選べる。

| screenshots | 保存する画像 | 既定の上限 / ページ |
| --- | --- | ---: |
| `off` | 撮影しない | 0 |
| `initial` | 操作・スクロール前に見えている範囲を、表示環境ごとに1枚 | 12 |
| `states` | 環境・状態ごとの画面。自動探索ではスクロールした範囲の画像も含む | 12 |
| `all` | 状態ごとの画像に加え、実行した探索操作の前後。設定済みの `page` では開始前と各操作後、Tab移動後も含む | 60 |

`page-audit` の既定はPC幅 (1280 CSS px) とスマホ相当の幅 (320 CSS px) なので、`initial` では通常2枚になる。`--max-images` で上限を調整できる。省略理由は収集ログに残り、取得した画像はHTMLの「画面の証拠画像」から開ける。画像をAIで確認するには、対応するモードと実際の比較が必要。

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

この上限は収集時にページごとに適用する。自動探索を再開するときは取得済みの画像も同じ上限に含める。追加probeや外部ツールの画像は別の操作になるため、AIは残る予算と必要性を確認し、保存済みの画像を再利用する。1回の応答へすべての画像を読み込まず、担当ページ・状態・対象の画像から読む。

実トークン数は画像の寸法、AIモデル、会話、実際に読み込む資料等で変わる。この設定は消費トークンや料金の保証ではない。原典を必要な基準だけ読むこと、報告だけなら再検査しないことも作業量の調整に含む。

## 省略と検証結果

画像off、上限、未到達、実SR未実施を対象外へ変えない。観察していない条件は判断保留・未確認として残す。視覚的な操作調査が未完了の新しいrunは、全体の検証完了にしない。requiredの実SRも未実施なら検証未完了を保持する。

optional又はoffで実SRを省略しても、実SRで確認したと報告しない。各基準で必要な観察を満たせる別の方法があるか、原典と実際の内容から判断する。設定名だけで全基準の合否を決めない。

旧runにはinspectionの指定がないものがある。従来の収集方法として読み取り、後から新しい観察を実施済みに変更しない。
