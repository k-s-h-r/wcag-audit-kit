# T013：候補一覧から試験対象と動的手順を選ぶ

T006の有限サイトに、T010の似たパス/a-extraを加えた所有サイト。起点T010提案版7f2735b、main未採用。WCAG 2.2 AA、匿名、Chromium・1280×900の選定計画で、適合評価の結果ではない。

selection-001のcandidates.jsonは初期候補10URL。既知の未リンク/unlinked・/a-extraは設定から、その他は初期リンクから取得した。ledger.jsonに取得元、ページ種別、選定理由、訪問状態、監査未実施を記録した。path除外1・別origin1は対象外。404は対象に残し到達失敗とする。

/dynamicには初期状態で/hiddenへのリンクがない。Show moreを実際に押してリンクを観測し、Moreを押して/hiddenの完了表示へ到達し、戻る操作まで行った。4状態のHTMLと画像、procedure.jsonの操作・完了条件を保存した。未発見と未訪問と対象外を同じ状態にしない。

この有限サイトでは既知の11URLを全件選定し、無作為抽出は不要と判断した。handoff-config.jsonは既存configured形式として検証済みで、クエリーとハッシュを保持する。ページ担当はこのURL一覧とprocedure.jsonの両方を受け取る。URL一覧は初期表示の入力なので、展開後状態や完了の確認を省略してはいけない。認証後の画面はこのfixtureにはなく、現実のサイトの権限調査の完了は表さない。

共通headerは同じ著者が用意した同一構造だが、検証結果の共通部品への再利用はこのタスクで実装・確認していない。既存の全AA検証能力やサイト全体の適合へ主張を広げない。

再現：`python3 validation/development/T013/exercise.py --out <新しい出力先>`。driver.logとobserved.jsonに結果。T014へはscope、ledger、handoff-config、procedureの4点を渡し、URL全件の担当結果・失敗理由・全4状態と終了条件・残るAI/SR確認が揃うまで統合完了にしない。T014はT004/T011と実SRの未解決条件があるため未着手。
