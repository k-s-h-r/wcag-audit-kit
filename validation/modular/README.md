# スキル分割・観察設定・画面からの操作調査

既知の所有する試験ページで、単独ページの収集、URL候補抽出、観察の省略、画面を見た操作調査、判定の記録、報告までを確認した。未知のサイトで全操作・全基準を発見できる精度評価ではない。

[実ブラウザーの結果](result.json)、[実行したスクリプト](executed-source.py.txt)、[画像確認後の記録](review-result.json)、[HTML報告](standard/report.html)、[Excel例](report.xlsx)を保存した。各runの設定はrun.json内に凍結している。親のconfig.jsonは試験スクリプトが段階ごとに変更した入力であり、過去のrunの設定として読み替えない。

## 実際に見た画面と操作

[初期画面](standard/evidence/43aa9d581c3c--initial--desktop/page.png)では、青いOpen preferencesとOpen help、下線付きRelated pageを候補として確認した。前者をDOMと対応付けるとroleのないdiv、tabIndex=-1だった。Tabの経路では到達できず、ポインターでPreferencesが開くことを実行した。

[Preferences](standard/evidence/43aa9d581c3c--preferences--desktop/page.png)では、Display nameの入力、Demo、Close preferencesを確認した。[Help](standard/evidence/43aa9d581c3c--help--desktop/page.png)ではMore options、Close helpとフォーカス枠を確認した。HelpをEscapeで閉じると起点へ戻り、Enterで再び開いた。More optionsの入れ子も開き、Escapeで起点へ戻してSpaceで再度開いた。

入れ子状態の画像は上限で省略された。画面を見たことにはせず、調査票へ残した。入力の編集、閉じるボタン自体の起動、全分岐等も未確認を保持している。モーダル内のTab循環だけを不適合にしていない。

原典の2.1.1を読み、画像、実キーの経路、ポインターでの起動、固定した試験実装の全体と代替経路を照合して、初期状態の1件だけを不適合とした。全機能の検査は終えていないためcoverage_complete=false、残る確認を記録した。219票は未実施、操作調査はpartial、検証未完了。実SRはoffを指定しており未実施。

画像を実際に見た後の記入処理は[当時のソース](review-executed-source.py.txt)へ保存した。この記入処理を実行することは、画像を見る代わりにはならない。

## モードと上限

- configuredの単独ページは、表示されたRelated pageへ巡回しなかった。
- discoverの候補抽出は、初期画面とRelated pageの2 URLを得た。WCAG判定は行っていない。
- standardは4状態のうち3画像を保存。quickは0画像。thoroughは指定上限の2画像を保存した。
- thoroughでrequiredになった実SRも、CLIの収集だけでは実施済みにならない。画像・実SRの省略で通過を増やしていない。

再現用のブラウザー試験は`python3 tests/integration_modular.py --out <新しい出力先>`。画像の内容の確認と判定は、その出力を実際に見て別に行う。

## 報告と配布の確認

報告だけの処理は、試験ページのサーバー停止後に保存済みの証拠から実行した。Excelの操作調査8行、partial、実SR skipped、検証未完了を読み戻した。

[報告表示の確認](report-ui/results.json)では1280/320pxで操作調査の8行、文書幅、未完了表示を確認した。実画像も見て、axeの検出は各幅0。報告自身の全WCAG基準を検査した結果ではない。

単体配布と4入口の生成は単体試験で確認した。単独のwcag-pageからCLIを起動でき、共通コードと原典が揃い、検証記録を複製せず参照できることを確認した。
