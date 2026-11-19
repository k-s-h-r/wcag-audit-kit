# 検証モードを選ぶ

モードは、今回の検証で使う手段を選ぶ設定です。全達成基準の合否は、実際に検査した結果から別に記録します。[全86基準の対応表](https://github.com/k-s-h-r/wcag-audit-kit/blob/adf459777fa43ea0898a95e43edf5dbdde0684b7/README.md)は、確認観点ごとに比較できます。

## 使う手段を指定する

- `machine`は機械ルール・実操作・数値計測を使います。AIによる画像・文章の意味の判断と、実スクリーンリーダーは省きます。標準の画像収集はoff、画像上限は0です。
- `ai`は機械検査とAIによる画像・文章・操作結果の比較を使います。スクリーンリーダーはoffです。画像は既定で状態ごと、上限12枚です。
- `screen-reader`は機械検査と実スクリーンリーダーを使います。AIによる内容判断と標準の画像収集は省きます。スクリーンリーダーの確認はrequiredです。
- `full`は機械検査・AIによる内容判断・実スクリーンリーダーを使います。画像は既定で操作途中も含め、上限60枚です。スクリーンリーダーの確認はrequiredです。

```sh
python3 scripts/audit.py page-audit --url https://example.com/contact --out /project/run-machine --mode machine
python3 scripts/audit.py page-audit --url https://example.com/contact --out /project/run-ai --mode ai
python3 scripts/audit.py page-audit --url https://example.com/contact --out /project/run-sr --mode screen-reader
python3 scripts/audit.py page-audit --url https://example.com/contact --out /project/run-full --mode full
```

新しい`page-audit`を設定なしで開始したときはmachineです。`--config`にモードがあれば、その設定を使います。CLIの`--mode`はそのモードの既定の観察設定に切り替え、明示した画像等のオプションを適用します。設定ファイルにも指定できます。

```yaml
verification:
  mode: ai
inspection:
  profile: standard
  screenshots: states
  screen_reader: "off"
  max_images: 12
```

設定ファイルの作成は`init --url <URL> --config <新しい設定> --mode <モード>`、設定済み状態の収集は`page --mode <モード>`でも指定できます。既存設定に`verification`がない場合や旧runは、従来の観察設定として扱い、後からモードを割り当てません。

## モードと画像の深さを分ける

モードはAI・実スクリーンリーダーを使うかを決めます。`--profile`・`--screenshots`・`--max-images`は画像の深さ・枚数を調整します。CLIでモードを指定した場合、実SRのrequired/offはモードに従います。例えばAI併用で画像を増やしても、実SRを起動する設定にはなりません。

```sh
python3 scripts/audit.py page-audit --url https://example.com/contact --out /project/run-ai-detail --mode ai --profile thorough --max-images 30
```

machine／screen-readerで標準の画像収集を有効にする、ai／fullで標準の画像収集をoff又は上限0にする、モードと矛盾する実SR設定を指定する場合はエラーにします。検査途中のモード変更は行わず、変更した検査は別のrunに保存します。`--resume`では保存したモードを継続し、別の`--mode`を指定すると停止します。

[1.4.11のフォーカス枠](page-audit.md#フォーカス枠と隣接色を測る)と[1.4.3の文字](page-audit.md#指定した文字のコントラストを画素で測る)は、測定を明示した場合にすべてのモードで周辺を切り出したPNGを保存します。フォーカス枠は1経路・1環境につき最大1枚、文字は1対象・1環境につき最大7枚です。RGB値の数値計測に使います。

## 各段階を実行し、実施済みと省略を分ける

1. `page-audit`が実操作・状態探索・axeを実行し、選択モードと対応表を帳票へ保存します。このCLIはAIサービスへ接続せず、スクリーンリーダーも起動しません。
2. `page-next`が、選択モードで進める確認観点と、省く観点・理由を返します。△は証拠取得・一部の検査までです。AIがoffなら画像・意味をAIで判断せず、実SRがoffなら起動しません。
3. 許可された機械検査・個別の操作・計測を進めます。AIが有効なら、スキルを使うAIが実際の画像・本文・操作結果を比較します。AIの利用実績をモード名だけから推定しません。
4. 実SRが有効なら、[対応環境とアダプター](screen-reader.md)を確認し、対象ページの操作・発話を取得します。選択しただけでは未実施です。環境不足・起動失敗・不足するシナリオを残し、ツリーや仮想読み上げで実施済みにしません。
5. 具体的な証拠を添えて既存の検査票へ記録し、`page-report`でページのHTML・JSON・Excelを更新します。×・省略・環境不足は未確認のままです。別の信頼できる手段や人の確認が必要なら、対象・理由・残る操作を引き継ぎます。

機械チェックだけをコマンドで実行する場合、AIサービスやAPIキーは不要です。AIスキルが機械検査の操作を調整する場合も、machineでは意味や見た目の判定をAIへ回しません。既存のrecordは証拠を検証する台帳であり、実行者がAIか人かを技術的に証明するものではありません。

## 対応表と結果を混同しない

- ○は、この確認観点に利用する検査手段があること。対象・条件・操作・期待値を具体化して実行する必要があります。
- △は、一部の検査・証拠取得までできること。残る判断や未実証の条件を記録します。
- ×は、そのモードでは確認しない、又は信頼できる手段が現在不足すること。WCAGの適用対象がないという意味ではありません。

[確認観点の定義](verification-checkpoints.json)を原本とし、READMEと[詳しい処理・準備](verification-checkpoints.md)を同じデータから生成します。開発時に定義を修正したら、リポジトリのルートで`python3 scripts/build_mode_matrix.py`を実行し、`python3 scripts/sync_skills.py`で配置用フォルダーへ反映します。利用者の検証操作には不要です。CLIでも基準ごとに確認できます。

```sh
python3 scripts/audit.py modes --mode ai --criterion 1.1.1
```

新しいrunには`verification.snapshot.json`とそのハッシュを保存します。将来の対応表の更新で、以前のrunの確認範囲を広げません。HTMLとExcelの「モード別の確認範囲」は検査方法の対応表であり、達成基準チェックシートの適合・不適合とは別です。JSONの`verification.checkpoints[].verification_status`も`not_evaluated`とし、対応表から合否を生成しません。

fullでも、現在の実証環境での音声の内容比較、手話、専用の閃光分析、言語別の正式な読解水準、実センサー等には不足が残ります。他ページを必要とする基準も1ページだけでは確定しません。[方法ごとの準備状況](method-capabilities.json)と各基準の手順を参照してください。
