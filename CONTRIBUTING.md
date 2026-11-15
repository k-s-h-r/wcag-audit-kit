# 変更の進め方

今後の変更は作業ブランチで実施し、PRでレビューする。mainへ直接登録せず、依頼なしにPRをマージしない。

各変更には[ADR](docs/adr/README.md)を作成し、PRから参照する。変更の大きさに応じて簡潔に書いてよいが、背景、採用する方法、その影響、確認方法を残す。

検査の結果を変更するときは、新しい判定を追加する。過去の原始証拠、スナップショット、判定を上書きしない。既存の検証記録は当時の定義と環境での結果として保持する。

Pythonの確認：

```sh
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -p 'test_*.py'
```

スクリーンリーダーのJavaScriptアダプターを変更した場合は`npm ci`と`npm run test:screen-reader`も実行する。モックの試験と、支援技術を実際に操作した試験を区別して報告する。
