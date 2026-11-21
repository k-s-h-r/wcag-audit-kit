# 0095 検証できるゴールに向けて開発を続ける

- 日付 2026-11-21
- 状態 Proposed

## 背景

[ADR 0022](0022-autonomous-development-workflow.md)は、通常の開発依頼で1作業単位をPR作成まで進める。VISIONを実証するには、機械検査、報告、手続きの検証、改善案の提示をつなぐ複数の作業が必要になる。

## 決定

明示された長期目標には、Codexの `/goal` と既存の `wcag-dev` を使う。Goalが持つ完了条件と、リポジトリのタスク・証拠・PRを対応付ける。最初の実証条件と起動文は[長期開発の手順](../DEVELOPMENT-GOAL.md)に記す。 [Codexの長期作業](https://learn.chatgpt.com/docs/long-running-work)

## 代替案

Claude Codeの `/loop` やCodexのスケジュールは、定期的な確認に使える。今回の継続条件は試験や実装の結果に連動するので、同じチャットのゴールを使う。[繰り返しの仕様](https://code.claude.com/docs/en/scheduled-tasks) · [スケジュールの仕様](https://learn.chatgpt.com/docs/automations)

## 影響

長期ゴールでは、PR作成後も独立して着手できる仕事を選び直す。作業と証拠は従来どおり担当タスクに残し、合流にはAGENTS.mdを適用する。

## 検証方法

通常依頼、長期ゴール、依存PRの承認待ち、実証条件をすべて満たした場合を手順に当てはめる。スキルの明示呼び出し設定、文書リンク、完了条件と担当タスクの対応を確認する。
