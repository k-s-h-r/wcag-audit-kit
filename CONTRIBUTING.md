# 変更の進め方

今後の変更は作業ブランチで実施し、PRでレビューする。mainへ直接登録せず、依頼なしにPRをマージしない。

着手前に[開発計画](docs/ROADMAP.md)の現在地と「次の作業」を確認する。変更によって計画の状態が変わる場合は、同じPRで完了根拠・未確認事項・次の作業を更新する。

各変更には[ADR](docs/adr/README.md)を作成し、PRから参照する。変更の大きさに応じて簡潔に書いてよいが、背景、採用する方法、その影響、確認方法を残す。

検査の結果を変更するときは、新しい判定を追加する。過去の原始証拠、スナップショット、判定を上書きしない。既存の検証記録は当時の定義と環境での結果として保持する。

Pythonの確認：

```sh
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -p 'test_*.py'
```

スクリーンリーダーのJavaScriptアダプターを変更した場合は`npm ci`と`npm run test:screen-reader`も実行する。モックの試験と、支援技術を実際に操作した試験を区別して報告する。

## ディレクトリー構成とスキルの保守

`skills/`の各フォルダーは配置用の完成したスキル。実行時に必要な`scripts/`、`references/`、`assets/`、`vendor/`と依存関係の一覧を含める。リポジトリのルートにはREADME、開発用`scripts/`、`tests/`、`docs/`、保存済みの`validation/`を置く。ルートにSKILL.mdは置かない。

共通の実行コードと資料は`skills/wcag-audit-kit/`を編集元とする。各スキル固有の指示は、そのスキルのSKILL.mdで編集する。共通部分を変更したら、開発者が次を実行し、各フォルダーの更新も同じPRへ含める。

```sh
python3 scripts/sync_skills.py
python3 scripts/sync_skills.py --check
```

同期は配置先に依存するリンク書き換えや利用者向けの生成処理を行わず、編集元の共通リソースを他の3スキルへコピーする。`--check`は書き込まず、欠落・内容の相違・余分な実行リソースがあれば終了コード1を返す。利用者はこのコマンドを実行しない。各フォルダーを直接コピーして使える状態をコミットする。

資料の再構築にはルートの`scripts/build_catalog.py`、`scripts/build_act_index.py`、`scripts/build_mode_matrix.py`を使う。出力先は編集元スキル。構築後に同期と確認を実行する。`scripts/build_coverage.py`は保存済みの実証記録を参照する開発用処理で、既存記録の扱いはAGENTS.mdに従う。

```sh
python3 /path/to/skill-creator/scripts/quick_validate.py skills/wcag-audit-kit
python3 -m unittest discover -s tests -p 'test_*.py'
npm run test:screen-reader
```

`quick_validate.py`のパスは利用環境のskill-creatorに合わせる。他の3スキルも同様に確認する。独立配置の試験は、リポジトリ外へ各フォルダーをコピーし、別の作業ディレクトリーからCLIと帳票を実行する。保存済みの判定・スナップショット・原始証拠は移動や書き換えの対象にしない。
