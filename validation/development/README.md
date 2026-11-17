# 開発測定の記録と再実行

T001等のディレクトリーは実行時の原文・原始証拠・採点の保存先です。各ディレクトリーのmeasure.py等は過去に実行したソースのスナップショットです。保存済みの記録先を対象に再実行しないでください。特に旧T002/T003のmeasure.pyは記録先が固定されているため、再実行には使用しません。

T002/T003の基準値を同じ旧実装・問題集・環境で再測定する場合は、現在の入口measure-baseline-v2.pyに、両方とも未使用の--recordsと--artifactsを指定します。既存のどちらかを指定した場合、収集前・書き込み前に終了します。T001のdigestを検証するため、実装が変わった作業ブランチからの測定は拒否します。以後の改善版は各タスクの新規runの方法を使います。

例（T002、同じ旧実装版のcheckoutから実行）：

```sh
python3 validation/development/measure-baseline-v2.py --repo . --task T002 --criterion 2.4.2 --records validation/development/T002-rerun-001 --artifacts artifacts/T002-rerun-001
```

--records/--artifactsは毎回未使用の名前にします。現在の実装へ古い証拠を移して上書き採点しません。

訂正：T002のstrict終了値は2回とも0です。選択した3行が完了したことを示し、全体の適合確認はincompleteです。T003は2回とも2です。過去の説明文の誤記は原始証拠を変更せず、この記録とADR 0036で訂正します。
