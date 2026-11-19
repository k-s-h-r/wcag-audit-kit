# 監査の設定

設定はAIが調査して作る。利用者はURLと目的を指定できればよい。既定はWCAG 2.2のAAで、AとAAの55基準を計画する。AAAを指定すれば86基準を計画する。

書式はこのスキル独自。`schema_version: "1"`を指定する。JSONとYAMLの両方を読める。例は[設定例](../assets/wcag-audit.example.yaml)。ファイル内の相対パスは、実行する前に設定ファイルのディレクトリーを基準に解決する。

| 項目 | 内容 |
| --- | --- |
| `url` | サイトの基準URL。認証情報はURLに含めない |
| `level` | `A`、`AA`、`AAA` |
| `scope.include` | `/path`又は`/path/**`。後者は自身と配下。`/**`はサイト全体 |
| `scope.mode` | discoverはリンクから候補を追う。configuredは指定URL一覧だけを使う |
| `scope.pages` | configuredで処理するURL又はURLパスの一覧。クエリー・ハッシュも区別する |
| `scope.pages_file` | 設定ファイルからの相対パス又は絶対パス。1行1URLのテキスト、JSON配列、pages出力JSONに対応 |
| `scope.exclude` | `{path, reason}`の一覧。範囲外とする根拠を記す |
| `scope.seeds` | 巡回開始のURLパス。クエリー・フラグメントを含められる |
| `scope.known_pages` | 資料等から分かった未リンクを含むURLパス |
| `scope.max_pages` | 1実行の巡回上限。超過分を未訪問として残す |
| `scope.same_document_fragments` | 同じ文書内への静的アンカーと確認したfragment名。`#`を付けず列挙する。既定はすべて保持 |
| `scope.same_document_fragment_reason` | アンカーを同じ文書へまとめるために調べた根拠。ハッシュで画面・状態が変わるルートは保持する |
| `environments` | `{id, viewport: {width,height}, zoom}`の一覧 |
| `states` | `{id, paths, actions, assert}`の一覧 |
| `auth_state` | 既存のPlaywright認証状態ファイルがある場合のパス |
| `keyboard_steps` | 収集時のTab操作回数。全機能のキー検査を代替する値ではない |
| `inspection` | [画像・実SR・画像数の選択](inspection-profiles.md)。省略は未確認として残す |

## URL一覧を指定する

大規模サイト等で対象が確定している場合はconfiguredを使う。pagesとpages_fileはどちらか一方にする。範囲外又は別オリジンのURLは指定しない。

```yaml
scope:
  mode: configured
  pages_file: ./targets.txt
  include: ["/**"]
  exclude: []
  max_pages: 100
```

configuredではseeds・known_pagesからの巡回や、表示されたリンクの追跡をしない。`start` ではmax_pagesで処理しきれなかった指定URLが未訪問へ残る。`pages` はブラウザーを開かず全指定URLを返す。`page-batch` は全指定URLを台帳に載せ、1回の処理件数を `--max-pages-this-run` で指定できる。pages_fileは読込時に一覧と元ファイルのハッシュへ解決してrunへ保存する。

discoverは既存のseeds・known_pagesから初期表示のリンクをたどる。どちらのモードも、リンクがない画面や操作後の状態まで発見した証明にはならない。

`states`は実際に調べたページの到達手順を記す。`initial`は予約名で、自動収集する。それ以外の状態には、操作後にその状態へ到達したと確認できる`assert`を必須にする。

状態への到達とWCAGの適否は分けて確認する。例えば、表示がOnへ変わったことを到達条件にし、そのときの公開された選択状態は4.1.2の期待結果と比較する。検査したいARIA値の正しさを到達条件だけにすると、表示On・ARIA falseという問題を、未到達として止めてしまう場合がある。

各actionの`assert`では、途中の段階でも表示条件を確認できる。書式は状態のassertと同じ。取消・復帰等の一連の操作では、中間結果を確認してから次へ進める。確認結果はactions.jsonのaction_assertedへ保存する。

YAMLの期待する文字列は`text: "On"`、`text: "Off"`のように引用符で囲む。このCLIのYAML読込では、引用符のないOn・Off等が真偽値へ変換され、画面の文字列と一致しなくなる場合がある。JSONでは文字列として記す。

収集器の操作は`click`、`fill`、`press`、`type`、`wait_for`、`scroll`、`text_spacing`、`reduced_motion`。typeは現在のフォーカス先へ文字をキー入力する。scrollはdelta_xとdelta_yでホイール移動量を指定する。対象には実際のCSSセレクター、又は`role`と`name`を指定する。役割が付いていないこと自体を調べる場合等は、CSSや利用可能な別の識別方法を使う。

`pointer_move`、`pointer_down`、`pointer_up`、`drag`、`reload`も使用できる。[ポインターの手順](pointer.md)を参照する。状態の`observe`には表示テキストを取得する対象の一覧を指定でき、各操作の直後の事実を記録する。基準の合否を自動判定する設定ではない。

`input_event_limit`は入力イベントの保存上限で、既定は10,000。超過はログに明記する。必要な証拠が打ち切られた場合は、短い操作に分ける等で再収集する。

`zoom`は1、1.1、1.25、1.5、1.75、2、2.5、3、4を指定できる。1以外はLinuxの専用Xvfb上でChromiumへOSのキー入力を送り、指定した倍率へ実際に拡大する。`viewport`は100%時のコンテンツ表示領域。拡大後の領域とDPRを測定して記録する。[拡大の手順](zoom.md)を参照する。依存物や画面を用意できない場合は、その収集を実行不能として残す。CSSのzoomや単なるviewport変更で代替しない。

ネイティブ拡大の環境では、状態の操作に`{"type":"zoom","factor":1.25}`等を記して、その状態を保ちながら倍率を変えられる。`factor: 1`は100%へ戻す操作。環境の初期倍率と操作後の実測値を区別する。

この設定に対象外の基準を一括で消す欄は設けていない。各ページ・状態で適用性を検査し、対象外の根拠を結果に残す。目標レベル外の基準は別に表示する。
