# 1ページを機械検査から始める

```sh
python3 scripts/audit.py page-audit --url https://example.com/contact --out /project/run-page --mode machine
python3 scripts/audit.py page-next --run /project/run-page --page-exact https://example.com/contact
```

page-auditは、対象URLだけで操作候補を調べ、実クリック・hover・Tab・Enter・Space・部品ごとの矢印キー等で到達した状態を収集する。状態ごとにDOM、アクセシビリティツリー、画像、実入力、axeの結果を保存する。LLMやAIサービスのAPIキーは必要ない。検証対象はテスト用環境を使い、認証が必要なら既存の設定のauth_stateを指定する。事前設定のstatesを含む設定は既存のpageで収集する。page-auditでは自動探索を使い、必要な独自シナリオをprobeで追加検査する。

操作候補はネイティブ部品・ARIA・登録されたイベント・カーソル等から抽出する。開いた後に現れた候補もキューへ追加する。外観だけで操作できそうな領域の追加確認には、保存画像と位置・候補一覧を使う。候補抽出だけで全操作を発見したことにはしない。

## モードを選んで進める

[検証モード](verification-modes.md)のmachine / ai / screen-reader / fullを`--mode`で選ぶ。設定なしの新しいpage-auditはmachine。モードで有効な検査手段と、実際に実行した結果は区別する。page-nextは利用する観点・省く観点・理由を返す。AIによる比較はスキルの実行環境、実SRは専用アダプターで実施し、このCLIだけで両方を実行済みにはしない。モード変更は別のrunとし、resumeは保存したモードを継続する。

## 収集と再開

各経路を独立したブラウザーコンテキストで再生し、互いの入力・ストレージの影響を抑える。画面の表示内容・状態属性・値・色やアウトラインの変化で状態を区別する。同じ状態へ達した経路も、入力方式の違いと実行結果を残す。モーダルのEscapeも実際に試す。

デフォルトは最大64状態、512経路、深さ8。上限や未到達は未確認として出力し、検証完了にしない。上限を広げて同じrunから続けられる。max-stepsとmax-statesは今回の追加件数ではなく累計上限。

```sh
python3 scripts/audit.py page-audit --url https://example.com/contact --out /project/run-page --resume --max-states 128 --max-steps 1000 --max-depth 12
```

探索はexploration.jsonへ保存する。再開時に過去の証拠のハッシュと探索実装の版を確認し、完了した経路と判定を保持する。探索中の状態は新しい証拠ディレクトリーへ保存し、既存の画像・判定を上書きしない。同じrunの探索を同時に2つ動かすことはできない。探索の実装が更新された場合は新しいrunを作る。画像の設定と上限は[観察設定](inspection-profiles.md)に従う。画像上限を変えて別の観察を行う場合も、新しいrunで記録する。

自動探索では、送信・保存・削除・認証情報などの操作と別ページへの移動を保留する。書き込みメソッドの通信、WebSocket、ページ外へのナビゲーションを制限する。これだけで任意の本番サイトの副作用を防げる保証にはしない。必要なフォーム送信などは、テスト環境の明示した経路で既存のprobeを使い、結果を追加する。iframe、closed shadow DOM、canvas等の内部、画像を省略した表示、深さや画面数の上限は、追加検査の対象として残す。

## 既知のキーボード操作を検査する

仕様や画面の調査から操作順と期待する画面状態を確認できたら、`init`で作った設定に`keyboard_checks`を追加し、`page-audit --config <設定>`で実行する。次の例は、Tabで「製品」へ移動してEnterで開き、「業務支援」まで進む部分を確認する。

```json
{
  "keyboard_checks": [
    {
      "id": "open-products",
      "name": "製品メニューを開いて業務支援へ進む",
      "criterion": "2.1.1",
      "steps": [
        {"key": "Tab", "focus": "#skip-link"},
        {"key": "Tab", "focus": "#products"},
        {"key": "Enter", "focus": "#products", "visible": "#products-panel"},
        {"key": "Tab", "focus": "#services"}
      ]
    }
  ]
}
```

`criterion`は2.1.1、2.1.2、2.4.3、4.1.2から選ぶ。各手順にTab、Shift+Tab、Enter、Space、Escape、上下左右の矢印キーのいずれかと、少なくとも一つの到達条件を指定する。条件には対象を一つに絞れるセレクターを使う。開いたShadow DOMでは、内側の要素を指定できる。証拠にはホストから実際のフォーカス先までを記録する。閉じたShadow DOMと、対象を宣言できないiframeは追加検査に残す。1経路は40操作までで、20経路まで指定できる。経路ごとに初期表示から始め、最初に期待と異なった操作、操作前後のフォーカス、期待結果を保存する。経路の実行は`--max-steps`の累計に含まれる。

コンボボックスでは、DOMのフォーカスが入力欄に留まったまま候補の位置が変わる。`focus`と、候補位置を表す`aria-activedescendant`の値をそれぞれ指定する。同じ方法でタブの`aria-selected`や開閉部品の`aria-expanded`も確認できる。4.1.2の経路には`attributes`条件を含め、指定したDOM属性の結果として読む。

```json
{
  "key": "ArrowDown",
  "focus": "#city",
  "visible": "#options",
  "attributes": [
    {"selector": "#city", "name": "aria-expanded", "equals": "true"},
    {"selector": "#city", "name": "aria-activedescendant", "equals": "osaka"}
  ]
}
```

`attributes`の`equals`は文字列で指定する。要素が存在し、属性がなくなったことを確かめるには`null`を指定する。選択後のテキスト入力欄は`"value": {"selector": "#city", "equals": "大阪"}`で現在の値を照合できる。検査結果に観察した値が残るので、テストデータを使う。

iframeの出入りを確認するには、経路の `frame` に例として `{"selector":"#dialog-frame","url":"https://example.test/dialog.html"}` を指定する。直接の子で同じオリジンの文書を一つ宣言できる。設定の対象範囲にある実際の文書URLを指定する。

- キーを押す前のフォーカスが子文書内にある手順に `"input_frame": "#dialog-frame"` を指定する。省略時は親文書へ届いた実キーを確認する。
- キーを押した後の条件を子文書内で確認する手順に `"frame": "#dialog-frame"` を指定する。省略時は親文書の条件を確認する。子文書からEscapeで閉じて親に戻る手順なら、`input_frame` だけを指定する。
- 宣言した子文書や実際の入力先を確認できない場合は判定を保留する。別オリジン、アクセスできないsandbox、リダイレクトによる移動はこの経路の対象外。

リンクを実行する経路では、同じオリジンかつ対象範囲内の絶対URLを`destination`に指定できる。最後のEnter又はSpaceで指定した文書へのGET移動を許可し、到達したURLとその手順の表示条件を照合する。指定外への移動、リダイレクト、確認できない入力や更新は判断保留として扱う。

結果はページ別の機械検査に追加され、期待と異なる場合はHTML・Excelの「自動検出した問題」に操作と箇所が出る。例えば、Escapeだけで閉じられなかった場合は、指定した離脱経路の問題として報告する。キーボードトラップの判定には、別の離脱手段とその案内も確認する。

## 機械の結果と達成基準の判定

axeのWCAGタグ付きルールを実状態ごとに実行する。キーボードで候補へ到達できたか、操作を送出できたかも入力ログとともに残す。結果は「通過（機械）」「問題あり（機械）」「機械判定不能」「対象なし（機械）」として出力する。Tabで到達できなかったことだけで、代替操作のないキーボード不適合を確定しない。

機械検査の問題は、自動検出した問題の表から対象・状態・期待結果・観察・証拠を確認できる。機械ルールの通過だけでは、その達成基準の全条件、全対象、意味、状態を満たしたことにはならない。未判定の検査票を自動的に適合で埋めない。[ACTの判定の対応](ACT.md)と原典に従い、必要な条件を満たした証拠からrecordする。

## AI・人の判断を必要な範囲へ絞る

page-nextは、残る経路、機械結果の件数、未完了の検査票と原典・手順・その状態の機械結果を返す。まず利用可能な道具で機械検査・測定・実操作を進める。画像と代替説明の意味の対応など、自動ルールで決まらない箇所だけを内容判断へ回す。画面の観察を含め、実施した範囲を[操作調査票](visual-discovery.md)と判定へ保存する。実SRや実拡大等は既存のアダプターを使い、実施と省略を区別する。

探索中に残った項目は、追加検査の観察と証拠を用意してresolve-explorationで解消を記録できる。graph_digestはpage-nextで取得する。同じ版の項目は1件ずつ保存しても累積し、以前の解消項目を再送する必要はない。同じ項目だけを再記録しても他の項目は保持する。探索の版が変われば過去の解消記録を流用しない。キューに残った未実行の経路は、この操作では解消できない。

```json
{"graph_digest":"取得した値","resolutions":[{"item":"remainingの対象項目をそのまま指定","observed":"追加の実操作で確認した事実と範囲","evidence":["evidence/attached/対象/追加検査.json"]}]}
```

```sh
python3 scripts/audit.py resolve-exploration --run /project/run-page --file /project/resolutions.json
```

道具が使えないだけで直ちに人へ渡さず、代替手段と必要な環境を調べて実行する。人の権限や専門的な意味判断など、実際に必要な場合だけ、試した方法と具体的な残る操作を引き継ぐ。

## ページの結果を出す

```sh
python3 scripts/audit.py page-report --run /project/run-page --page-exact https://example.com/contact
```

page-auditの終了時にも同じ出力を作る。run直下のpage-識別子-report.html / .json / .xlsxがページ単位の結果。HTMLとExcelのチェックシートには、基準全体の判定、確認観点、機械検査の内訳を表示する。自動検出した問題の表は、同じ問題の状態別記録を集約し、全状態と証拠を保持する。Excelの機械検査シートには、機械結果と実入力の全記録を出す。概要・件数・検査票もそのページだけを集計する。更新時のExcelは別名で保存する。元のrun全体のreport.html等は変更しない。

この仕組みの実行成功は、機械検査と帳票作成を終えた意味。WCAG検証完了には、予定した検査票の未実施・判断保留・未網羅、探索・画面観察、必要な読み上げ等の未確認と適合要件の確認が残っていないことが必要。状態を有限個試しただけで、任意のページの全状態を網羅したとは表明しない。
