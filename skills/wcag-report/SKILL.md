---
name: wcag-report
description: 保存済みのWCAG検証台帳をHTML・JSON・Excelへまとめる。単独ページにもサイト全体にも使う。判定・証拠の対応を確認し、未実施、未探索、観察の省略、人への確認を保持する。報告だけの依頼では再訪問・再検査を始めない。
metadata:
  version: "0.5.0"
---

# 保存済みの結果を報告する

入力は正本のrunと出力形式。ページ担当者の結果は同じrunへ保存してから集計する。独立したrun、異なるビルド、設定、基準版を暗黙に合算しない。

## 実行ルート

このSKILL.mdの場所から上位へ探し、`scripts/audit.py`と`references/catalog.json`があるディレクトリーを使う。単体配布ではこのスキルのディレクトリーが実行ルート。

## 集計する

```sh
python3 scripts/audit.py report --run <run> --strict
python3 scripts/audit.py excel export --run <run> --mode report --out <新しいreport.xlsx>
```

report.html、report.json、issues.md、human-review.md、interaction-review.mdを確認する。Excelは[閲覧用と作業用](../../references/collaboration.md)を区別する。作業用を受け取った場合は、事前確認と取り込みを済ませてから集計する。

報告依頼だけならブラウザーや実SRを起動しない。証拠の消失・改変、設定・基準版・caseの不一致を検出したら、結果を作り直して隠さず、問題を報告する。

## 利用者へ伝える

- 対象ページ・状態・環境・レベルと、今回の集計範囲。
- 具体的な不適合、再現手順、期待結果、参照する証拠。
- 未実施、判断保留、未探索の操作・状態、人に必要な確認。
- 画像・実SRの選択と実施状況、画像上限、異なる深さの検査が含まれること。
- 検証完了とWCAG適合の区別。作業タスクのdoneだけを完了条件にしない。

strictの終了コード2は検証未完了を表す。省略・未探索を通過に変えて終了コードを消さない。資料の用意や画像の保存だけを、内容の確認済みへ変えない。
