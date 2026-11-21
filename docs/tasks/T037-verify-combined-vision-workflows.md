# T037 追加した検査と検査票の根拠を同じ版で照合する

状態は、試験用の組み合わせで代表例の通常CLIと独立レビューを完了し、76ページ・87行で問題12/39行の検出と対照19/48行の一致を確認した。その後、関連する30件のPRを同じPRにまとめ、入れ子のダイアログの操作も含めて再検証した。[PR #111](https://github.com/k-s-h-r/wcag-audit-kit/pull/111) · [統合版の結果](../../validation/development/vision-follow-up/README.md)

## 作業と成果物

T030を起点に、ダイアログの離脱証拠を表示するT033、遮断した文書移動を記録するT034、ARIA参照の変化を再検査するT019、ボタンの間隔を測るT035の実装を合わせた。配布ファイルを同期し、固定した問題集と各変更の代表例を通常のCLIで再測定した。収集後にT039を採点器に加え、同じ入力から同じ出力を得た。[ADR 0121](../adr/0121-verify-follow-up-workflows-together.md) · [実装の起点と試験条件](../../validation/development/vision-follow-up/README.md)

## 完了条件

- 同じ76ページ・87行を両画面幅で採点する。統合前に確認した離脱と間隔、従来の閉じるボタンの経路、ほかの採点結果と未対応の指摘を照合する。
- 同じスキルで、開いた状態の検査票に証拠が出ること、文書移動の遮断と未確認が同時に報告されること、参照先の追加・除去と全文書検査が一致することを確認する。
- 配布の同期、単体テスト、別エージェントによる操作と帳票の照合を記録する。元の個別試験と組み合わせ後の試験の実装版と結果をそれぞれ参照できる。

## 担当範囲

`codex/vision-followup-verification` の別worktreeとループバック対照を使う。個別のPRの証拠を参照し、組み合わせ後の原始記録は新しいrunに保存する。

mainに取り込む版は `codex/merge-vision-prs` の別worktreeで照合した。元のPRのコミットをすべて含め、個別の実測記録と、組み合わせ後の採点を参照できる。[ADR 0128](../adr/0128-merge-the-vision-pull-requests-together.md) · [統合時の試験](../../validation/development/vision-follow-up/README.md#mainへの統合)
