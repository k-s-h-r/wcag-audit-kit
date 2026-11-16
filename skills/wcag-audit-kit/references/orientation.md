# 表示の向きを調べる

1.3.4は、コンテンツが縦又は横の一方へ表示・操作を制限していないかを検査する。画面寸法による通常のレイアウト変更は、この基準が扱う向きの制限と区別する。見えない部品や横スクロールは、必要に応じて1.4.10等でも検査する。

まず実際のページの向きの制限、Screen Orientation API、CSSメディアクエリー、CSS transform、回転を求める表示等を調べる。制限がある場合も、G214のような別の向きでアクセスする操作と、本文の本質的な例外を確認する。F97・F100と関連するACTの適用条件も読む。

## ブラウザーのエミュレーションで実行する

`orientation_probe.py`は、Chromiumの画面寸法とScreen Orientation APIを明示的に設定して計測する。各段階の画面・DOM・表示テキスト・属性・入力・フォーカスを保存できる。実端末を物理的に回転した試験ではない。

シナリオは実際のcase・ページ・全対象と状態へ合わせる。例えば、向きを変える前に入力・選択し、変更後も内容と操作を利用できるかを調べる。新規に開いた画面の縦横比較だけで、途中の状態を確認済みにしない。

```json
{
  "case_id":"実際のcase_id",
  "url":"http://127.0.0.1:4317/orientation-good.html",
  "viewport":{"width":900,"height":600},
  "orientation":"landscape-primary",
  "observe":[{"selector":"#count"}],
  "actions":[
    {"type":"click","selector":"#increment","assert":[{"selector":"#count","text":"1"}]},
    {"type":"rotate","viewport":{"width":600,"height":900},"orientation":"portrait-primary","assert":[{"selector":"#task","visible":true}]},
    {"type":"click","selector":"#increment","assert":[{"selector":"#count","text":"2"}]}
  ]
}
```

```sh
python3 scripts/orientation_probe.py --request /project/orientation-request.json --out /project/artifacts/orientation-case-001
python3 scripts/audit.py attach --run /project/artifacts/wcag/run-001 --case <case_id> --file /project/artifacts/orientation-case-001/orientation.json
```

操作はrotate・click・press・fill・wait_for。対象はselector又はroleとname、必要ならframeを指定する。observeのattributesで指定属性も読める。auth_stateの相対パスはシナリオの場所から解決する。範囲外へ移動すると停止する。

向きはportrait-primary・portrait-secondary・landscape-primary・landscape-secondary。画面寸法と向きが矛盾したシナリオは拒否する。CSS表示領域、screen.width/height、screen.orientationのtype/angle、メディアクエリー、visualViewport.scaleを照合する。画像の画素寸法も表示領域と照合し、表示領域のみの画像と明記する。

## 確認範囲と残る試験

この方法で観察できるのは、検証したChromiumのエミュレーションでの著者実装の動作。端末の回転センサー、OSの回転ロック、ネイティブアプリ、全画面やPWA等の権限・機能に依存する制限を一律に再現したことにはならない。該当する実装があれば、必要な実端末・ブラウザーで追加して確かめる。ユーザー自身がOSで向きを固定することと、著者がコンテンツを制限することも区別する。

`collected`は観察の完了。画面に回転要求がある失敗例でも、その状態へ正しく到達して観察できればcollectedとなる。基準の合否は、その情報・機能の制限、代替操作、本質性を原典と照合して記録する。

[比較試験](https://github.com/k-s-h-r/wcag-audit-kit/blob/adf459777fa43ea0898a95e43edf5dbdde0684b7/validation/orientation/README.md)では、同じカウンターを両方の向きで操作できる例と、縦向きで操作全体が消えて回転を求める例を実行した。全ての実端末や全サイトへの動作保証ではない。
