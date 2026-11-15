# ポインターの操作を検証する

要素にclickハンドラーやドラッグ用の属性があることと、利用者が操作を完了・取消できることを区別する。実際の対象を列挙し、押下・移動・解放と、操作の前後の状態を記録する。

## 収集器の操作

```json
[
  {"type":"pointer_move","selector":"#append"},
  {"type":"pointer_down","selector":"#append"},
  {"type":"pointer_move","selector":"#cancel-area"},
  {"type":"pointer_up"}
]
```

pointer_moveは対象へ実際にポインターを移す。selectorの代わりにroleとnameも使用できる。pointer_downは移動せずに押す。指定した対象にtrusted pointerdownが届いたことを照合し、別の場所を押した場合は検査を止める。pointer_upは現在位置で解放する。

座標が必要な場合はpointer_moveにx・yを指定できる。位置が変わるページでは、その時点の画面・寸法から座標を調べる。対象へ入力が届かなかったことを、操作が取消された証拠にしない。

```json
{"type":"drag","selector":"#alpha","target":{"selector":"#bravo"}}
```

dragはPlaywrightのdrag_toで操作する。DOMを並べ替えて結果だけを作る方法では検証しない。各操作の到達と機能の完了を、実際の画面・結果・入力ログから確かめる。

各actionにも`assert`を指定できる。例えば並べ替えを実行して元へ戻す場合は、最初の移動後の順序と、復帰後の順序をそれぞれ確認する。最後に元の順序であることだけでは、どちらの操作も動かなかった場合を見落とす。

```json
{"type":"drag","selector":"#alpha","target":{"selector":"#bravo"},"assert":[{"selector":"#order","text":"Bravo, Alpha"}]}
```

到達条件が合わなければその収集をblockedとして止める。原典の期待と異なるページを検証する場合は、実際に発生する失敗の状態へ到達したことをassertし、WCAGの不適合は検査票へ別に記録する。

## 状態ごとの観察を記録する

状態に`observe`を指定すると、各操作の直後に対象の表示テキストを取得する。

```json
{
  "id":"cancel",
  "paths":["/example.html"],
  "actions":[
    {"type":"pointer_move","selector":"#append"},
    {"type":"pointer_down","selector":"#append"},
    {"type":"pointer_move","selector":"#cancel-area"},
    {"type":"pointer_up"}
  ],
  "observe":[{"selector":"#count"}],
  "assert":[{"selector":"#count","text":"0"}]
}
```

actions.jsonに操作時刻と実際の観察を保存する。reloadも操作として使用でき、再読み込み後に状態が残るかを確認できる。probeにもobserveを渡せる。probeは既知の状態へ到達する操作を再実行し、依頼・実行設定・元caseとの対応を保存する。

設定のassertは状態へ到達したことの確認であり、WCAGの判定ではない。意図的な失敗例で「件数1」を確認できても、それを合格にしない。基準の期待結果は検査票で別に定める。

## 入力の証拠

input-events.jsonにイベントの種類、対象、ポインター種別、座標、trusted、文書のID、時刻を保存する。別文書へ移動・再読み込みした場合も、Python側で受信済みのイベントを保持する。文字キーの内容は[character]に置き換え、入力値自体はこのログへ保存しない。

これはブラウザー自動操作の入力であり、物理マウス・タッチ端末を試験したという意味ではない。trustedだけで操作の意味や成功を確定せず、対象と状態変化を照合する。上限を超えた場合はtruncatedとdroppedを記す。欠けたログが判定に必要なら、新しいprobe等で確認する。

## 2.5.2 ポインターのキャンセル

全機能について原典の4条件を確認する。No Down-Event、Abort or Undo、Up Reversal、Essentialのうち少なくとも一つを満たすかを判定する。downイベントを使っているという理由だけで、打鍵の模倣等の本質的な例外を無視しない。UA自身の操作と、著者が実装する機能も区別する。

G212等に沿い、対象で押下してから、押したまま対象外へ移動して解放する。各段階で機能が実行されたか確認する。通常の操作で機能することも確認し、反応しない部品を「取消できた」としない。必要な取消・復元経路、押下時と解放時の結果も調べる。

同梱のpointer-cancel-good.htmlとpointer-cancel-bad.htmlは、この方法を試す比較ページ。押下・解放・件数・追加後の状態・再読み込みを実行した[校正結果](../validation/pointer-cancellation/README.md)を保存している。全基準に適合するページという意味ではない。

## 2.5.7 ドラッグ動作

ドラッグする全機能に、ドラッグせず単一ポインターで同じ結果を得る手段があるか調べる。移動先の選択、数値入力、移動ボタン等を実際に使い、元の機能と結果を比較する。キーボードの矢印キー等だけで実行できることを、この基準の合格へ変換しない。

本質的なドラッグ、UAが決め著者が変更しない機能の例外を確認する。UA標準のスクロールと、著者が独自に実装するスクロールも区別する。軌跡を要求する代替操作だけの場合は2.5.1との関係も確認する。

同梱のdrag-reorder-good.htmlとdrag-reorder-bad.htmlで、全4方向のドラッグ、矢印キー、移動ボタンのクリックを実行した[校正結果](../validation/dragging/README.md)を保存している。ドラッグとキー操作がどちらも動く失敗例を含む。
