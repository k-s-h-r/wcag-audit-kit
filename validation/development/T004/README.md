# T004：Codexの呼び出し環境の確認

2026-11-18。Codex CLI 0.167.0-alpha.4。4スキルのフロントマターとagents/openai.yamlを解析し、明示呼び出し専用設定を確認した。設定の一致はホストの選択動作の成功ではない。

独立したartifacts/host-probe-001/.agents/skills/へ4スキルをコピーした。既存の利用者設定を変更せず、`codex exec --ephemeral --json --skip-git-repo-check -s read-only -C <検証ディレクトリー>`で明示したwcag-pageの読み込みだけを試した。監査・ブラウザー・ファイル変更は指示していない。

[原エラー](T004-host-probe-001.stderr.txt)はin-process app-serverの初期化時のRead-only file system（os error 30）。終了コード1で、モデルセッションも検査も開始しなかった。[設定・入力・各場面の状態](observed.json)と[CLI版](codex-version.stdout.txt)を保存した。stdoutのJSONLは空である。

明示page、通常の開発相談から監査しないこと、単独ページで巡回しないこと、報告だけで再訪問・判定更新しないこと、全体監査から子手順を読めることは、いずれもホスト動作として未実行。現在の開発セッションがSKILL.mdを手動で読む操作を代用しない。

調査記録は完了したが呼び出し成功は未達。ホストの書き込み可能なセッション保存領域を持ち、利用者設定を変更せず新規セッションを作れる環境で再試験する。特定の設定項目を原因と断定せず、同じ起動失敗を繰り返さない。環境の設定変更・権限拡大は行っていない。T011とG2のホスト条件は未達のまま。
