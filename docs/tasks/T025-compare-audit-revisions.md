# T025 修正前後の検査票をページごとに比べる

状態は実装とローカル検証を完了し、PRを作成済み。[PR #93](https://github.com/k-s-h-r/wcag-audit-kit/pull/93)

前提は [T013](T013-site-selection.md) で確認したページごとの共通部品の検査。

共通部品の表示はページのCSSや状態で変わる。修正前後に同じ観点を調べ、共通部品を載せた各ページで何が解消し、何が残ったかを確認できるようにする。[VISION](../VISION.md#直したあとにもう一度使いたい) · [Issue #4](https://github.com/k-s-h-r/wcag-audit-kit/issues/4)

## 作業と成果物

`compare-reports` で二つの報告JSONを読み、同じページ・状態・環境・達成基準の同じ観測対象を照合する。比較結果はJSONと、指定に応じて元の帳票と証拠にリンクするHTMLに出力する。[利用手順](../../skills/wcag-audit-kit/references/commands.md#修正前後の検査票を比べる) · [ADR 0102](../adr/0102-compare-recorded-audit-revisions.md)

## 完了条件と確認

- 共通リンクを載せた複数ページで、解消・新規・継続・未確認を区別できる。
- 修正後に判定を記録しなかったページ、HTTPエラーのページ、検査範囲から外れたページは未確認と出る。
- 前後の証拠にリンクし、原本の判定と証拠は比較後も同じハッシュを持つ。

Chromiumの6ページで確認した。文字コントラストの解消・新規・継続が1ページずつあり、残る3ページは未確認だった。[再実行と観察記録](../../validation/development/T025/README.md)

通常の `page-audit` から作った前後の帳票でも解消を確認した。片方にブラウザーの版や実際のURLの記録がない場合は未確認になった。[1ページ検査の比較](../../validation/development/T025/run-003/summary.json)

## 担当範囲と引き継ぎ

起点は `67aa42e`、担当ブランチは `codex/t025-compare-audit-revisions`。実装は `revision_comparison.py` とCLIの登録に置く。記録は `validation/development/T025/` に保存した。

確認した範囲は、ローカルの匿名ページの初期状態と1.4.3の1対象。別ブラウザーや実スクリーンリーダーの運用には、同じ状態と環境を確認できる証拠が要る。認証があるrunや自動探索で見つけた状態を比較する要件は、再現に使える情報を確かめてから決める。
