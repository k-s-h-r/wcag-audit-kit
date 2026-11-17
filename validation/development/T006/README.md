# T006：URL一覧化の基準値

2026-11-18。既存page_catalog.pyを変更せず、小さな専用サイトでconfigured・discoverを測った。サイトは[exercise.py](exercise.py)内のHandlerで、既存問題集を変更していない。[期待集合と範囲](plan.json)をselectorの実行前に保存した。

| 場面 | 候補 | 訪問 | 未訪問 | 失敗 |
| --- | --- | --- | --- | --- |
| [指定一覧](configured.json) | 6 | 0 | 0 | 0（ページへアクセスしない） |
| [収集・上限20](discover-full.json) | 9 | 9 | 0 | HTTP 404が1 |
| [収集・上限2](discover-limited.json) | 9 | 2 | 7 | 0（まだ失敗URLへ訪問していない） |

[実測](observed.json)にHTTPリクエストと経過時間を保存した。指定一覧は相対URLの重複を統合し、クエリー2種・ハッシュ2種を別々に保つ。指定のmissingも未訪問なのでHTTP失敗とは扱わない。

収集は全9候補を得て、404のmissingもvisited=trueだがerrorsへ残った。visitedを訪問成功として数えない。上限2ではrootとknown_pagesのunlinkedだけ訪問し、7候補を未訪問とした。範囲外originと除外パスは候補に含まれない。操作しないと現れない/hiddenは未発見であり、初期リンク収集の限界として残す。全体inventory_completeは常にfalse。

現在の出力には除外したURLの個別の理由行がない。テストの期待範囲には除外理由を置いたが、実装に記録済みとはしない。T013の選定計画ではこの不足を明示し、候補の一覧を試験対象の全件や適合へ読み替えない。

最初の試行は、この試験の入力でexcludeへ文字列を入れたため、設定検証中のTypeErrorで停止した。[誤った入力と原エラー](attempt-001-input-error/stderr.txt)を保持し、excludeを既存形式のpath・reasonへ直して別出力先で実行した。URL収集器は変更していない。

再実行は新しい保存先へ`python3 validation/development/T006/exercise.py --out artifacts/T006/urls-003`。T010にはconfiguredの6URLを実際に起動したbase URLへ置き換えて渡せる。T013には9候補・失敗・未訪問・未発見・除外理由の不足を渡す。AI判断・WCAG検査はこの測定では実施していない。
