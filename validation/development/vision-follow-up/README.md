# 追加した検査を同じ版で照合する

先に五つの変更を個別に実測した。ここでは同じ配布版に置き、操作、帳票、機械採点を通常の入口から調べる。元の試験範囲と証拠は各PRに置く。[T037](../../../docs/tasks/T037-verify-combined-vision-workflows.md)

| 範囲 | 起点のコミット | 個別の実測 |
| --- | --- | --- |
| ダイアログからのキー操作による離脱 | `9fcaa0d` | [T030 #100](https://github.com/k-s-h-r/wcag-audit-kit/pull/100) |
| 離脱証拠を開いた状態の検査票に表示 | `8f61988` | [T033 #102](https://github.com/k-s-h-r/wcag-audit-kit/pull/102) |
| Tab観察と文書移動の遮断 | `0012022` | [T034 #104](https://github.com/k-s-h-r/wcag-audit-kit/pull/104) |
| `aria-controls` の参照先の再検査 | `b91eb2c` | [T019 #107](https://github.com/k-s-h-r/wcag-audit-kit/pull/107) |
| 静的なボタン二つの寸法と間隔 | `7d2f5b1` | [T035 #108](https://github.com/k-s-h-r/wcag-audit-kit/pull/108) |
| 離脱を採点するときの証拠照合 | `f68e51d` | [T039 #110](https://github.com/k-s-h-r/wcag-audit-kit/pull/110) |

## 事前に固定した試験

問題集の76ページ・87行を、統合版と同じAAA、機械モード、両画面幅、初期調査から24ステップの簡易探索で収集する。結果と証拠は、変更前の[統合版](../vision/run-001/machine-score.json)と[離脱修正版](../T030/run-003/score.json)へ対応付ける。039・040の離脱、068・069の寸法・間隔で新たな結果を期待する。064・065の閉じるボタンの経路、採点行に対応しなかった指摘、その他の行を比較する。

離脱証拠は簡易探索を始める前と後に `page-next` で確認する。073の補助Tabでは文書移動の要求と遮断を結び付け、3.2.1が未確認のままかを確認する。参照の追加と除去は同じ表示・操作の全文書検査と照合する。これらの試験は独立したループバック受信先とrunで行う。

## 同じ版で照合した帳票と再検査

ブラウザーで使用した実装は `89fc5dcc8a3b0b48f7c9e9175ff3cd68cda87840`。Pythonテスト328件と配布スキル4組の同期が通過した。

別エージェントが039・040を新しいrunで簡易探索した。探索前の `page-next` には簡易探索を再開する案内があり、探索後は両幅の開いた状態が、該当する実操作の証拠とともに先頭に出た。039はEscapeで外に戻り、040は試したキーで同じ入力欄に留まりマウスで離脱した。両方の検査票は、達成基準の判定を未実施のまま記録した。[独立した再実行](run-001/independent-review.md) · [入力・状態・帳票](run-001/independent-evidence.zip)

同じエージェントが073を両幅で再実行し、最初のTab、`#subject` のフォーカス、イベント中の文書移動の要求、キーアップ、同じ移動先の通信遮断を照合した。サーバーは移動先への要求を受信しなかった。HTML・JSON・`page-next` は遮断を示し、移動先と3.2.1は未確認に残った。[独立確認の項目](run-001/independent.json)

参照先の追加・除去・同じIDの移動は、それぞれ両幅で簡易探索と全文書検査のaxeのルール・分類・対象が一致した。追加は通過、除去は違反へ変わり、同じIDの移動は初期状態の通過を参照した。[操作後の再検査](run-001/reference-results.json) · [検査前後の原始証拠と帳票](run-001/reference-evidence.zip)

## 76ページ・87行の結果

76ページすべてで初期調査と簡易探索が完了した。問題の検出は先の統合版の9/39から12/39へ、対照の一致は16/48から19/48へ増えた。離脱で039・040の2行、寸法・間隔で068・069の4行が変わった。従来の閉じるボタンの経路と、採点行に対応しなかった14件の指摘は一致した。8ページのZIPから該当する行と参照先を再度採点できた。[全87行](run-001/machine-score.json) · [変更前との差](run-001/comparison.json) · [8ページの操作と帳票](run-001/benchmark-evidence.zip)

ブラウザー収集後に、T039の証拠照合を採点器に加えた。実装 `e04cb5ca7e36248a6cfa71adfe346223dd6e6f9e` で同じ収集を採点し、全87行と出力JSONがバイト単位で一致した。別エージェントが040のコピーのPC幅で、壊れた遷移だけを保留してスマートフォン相当幅の判定を維持することも確認した。この版でPythonテスト329件と配布の同期が通過した。[再採点の出力と証拠のハッシュ](run-001/rescoring.json) · [T039の変更](https://github.com/k-s-h-r/wcag-audit-kit/pull/110)

測定範囲は固定した対照、画面幅、操作に限る。画面全体の適合に残る観点は、通常の検査票から確認できる。

## 再実行

ChromiumとPlaywrightを使用し、収集と採点に新しい出力先を指定する。独立レビューのZIPには公開対照、実行した引数、操作と帳票を収録した。

```sh
python3 scripts/sync_skills.py --check
python3 -m unittest discover -s tests
python3 benchmarks/url_only_machine.py --out FULL_RUN --workers 6
python3 benchmarks/url_only_machine.py --out FULL_RUN --score SCORE_JSON
```
