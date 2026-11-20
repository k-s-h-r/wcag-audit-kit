# 基準別の問題集で検証方法を試す

既知の問題と正常な例を検査し、検出漏れ・誤検出・未確認を数えるための開発用の仕組みです。同じ問題集を使って、検証方法の変更前後とモードごとの結果を比較します。

全86基準・131確認観点の入力を用意しています。306ケース・314ページ分の入力があり、判定の期待結果329行と取得の期待結果36行を分けています。[基準ごとの一覧](COVERAGE.md)、[61組の追加パターン](PATTERNS.md)、[形式と未確認の扱い](FIXTURE-FORMAT.md)から参照できます。

131観点の内訳は判定114・取得17です。取得の期待結果には、画像の列挙・読み順・フォーカス経路・名前・寸法等を記録します。1.1.1-02の一部は初期表示の対象と形式を、2.5.8-01の一部は幅・高さ・辺間隔を実測した要素一覧に照合します。4.1.3-01の一部は、指定したローカル操作の表示とアクセシビリティツリーの役割を照合します。必要な取得期待が残れば未完了として報告します。

今回はTDDで使う入力の整備です。検証器がそれを検出できるようにする実装・精度改善は次の段階です。音声解説・手話・拡張解説にも実素材と既知の内容を使った対照を追加しました。正解は作成者が定めたもので、独立した専門家による確認や全パターンの網羅は未実施です。

## ページと正解を分ける

```text
benchmarks/cases/
  1.1.1/
    suite.json              # 採点側だけが使う正解・根拠・モード別の評価条件
    README.md
    public/
      p01.html              # 問題と正常な例を含むページ
      p02.html
      assets/chart.svg
  2.1.1/
    suite.json
    public/p01.html
    public/assets/site.css
  3.2.3/
    suite.json
    public/p01.html          # 比較するページを同じ基準内へ置く
    public/p02.html
  1.2.2/
    suite.json
    public/p01.html
    public/assets/clip.webm
    public/assets/soundtrack.wav
    public/assets/captions.vtt
```

公開するのはpublic内のページと素材だけです。URL・タイトル・コメントへ「正常」「失敗」「正解」等の答えを埋め込みません。検査担当にはworker/tasks.jsonと必要な実行証拠を渡し、suite.json、oracle.snapshot.json、採点結果を渡しません。正解を隔離して入力を分ける構成であり、同じリポジトリを読める担当者による意図的な正解参照まで防ぐものではありません。

各正解はページ・状態・対象・確認観点に対応します。基準全体の適合とは分けています。例えば2.1.1では、キーを送出できたことと機能を完了できたことを別に採点します。同じ機能を使える代替ボタンがある例も用意し、ポインター専用部品があるだけで不適合にする誤りを調べます。

代表的な対照例です。全基準は[収録範囲](COVERAGE.md)を参照してください。

| 基準 | 収録した対照例 |
| --- | --- |
| 1.1.1 | altの欠落、正しいalt、空altの装飾、画像と逆の意味のalt、開いた詳細に同等情報がある／ない |
| 1.2.2 | 字幕ボタンが実トラックを有効にする／ボタン表示だけ変わる。音声・映像・字幕を同梱 |
| 2.1.1 | ネイティブボタン、focus可能だがキーで動かないdiv、同じ機能のキーボード代替がある例 |
| 2.1.2 | 閉じる・Escapeで出られるモーダルと、Tab・Shift+Tab・Escapeで出られない例 |
| 2.4.2 | 空タイトル、主題を説明するタイトル、存在するが主題と合わないタイトル |
| 3.2.3 | 2ページでナビゲーションの相対順序が同じ／異なる例 |
| 4.1.3 | 画面の更新は同じで、statusの通知がある／ない例 |

## 階層を開いてフォーカスを確認する

[3階層のグローバルメニュー](NESTED-NAVIGATION.md)に、末端リンクまでの到達、親への復帰、深い階層のトラップ、展開時のフォーカスの飛び先を確認するページを用意しています。

## テストページを見る

各基準のREADMEからpublic内のページを選びます。ローカルで表示する場合は、例えば次のように公開範囲をpublic内へ限定します。

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory benchmarks/cases/3.3.7/public
```

ブラウザーでhttp://127.0.0.1:8000/p01.htmlを開きます。p02.htmlは対照例です。suite.jsonは期待結果と根拠であり、検証器へ渡すページには含めません。画像・音声等の由来と、再現に必要な条件は[素材と条件](MATERIALS.md)を参照してください。

## 実行して、未確認も報告する

```sh
python3 benchmarks/run.py inventory
python3 benchmarks/run.py collect --mode all --out /project/bench-001
python3 benchmarks/run.py collect --mode machine --criterion 1.1.1 --out /project/bench-alt-001
```

実際のskills/wcag-audit-kit/scripts/audit.py page-auditを使い、各ページを検査します。採点にはimage-alt、document-title、実キーの到達・送出と、1.4.3-01の文字コントラストを自動で取り込みます。文字コントラストは宣言した状態と対象が一致するaxeの測定を使います。別の観点はAI・実SR・個別の機械検査を実行して結果を取り込むまで未確認です。[文字コントラストの採点条件](../docs/adr/0027-score-observed-text-contrast.md)

1.4.3-02の静的な対象は、`python3 benchmarks/run.py collect --mode ai --criterion 1.4.3 --text-paint --out <新しい保存先>`で追加測定できます。`full`でも指定でき、通常の画像上限とは別に対象ごとに7枚を使います。機械のみ・SR併用のモードでは指定できません。根拠が不足した測定は未確認です。[測定と採点の条件](../docs/adr/0035-grade-opt-in-text-paint-evidence.md)


2.4.3のダイアログ対照では、開いたボタン、閉じる実入力、閉じた直後と次のTabのフォーカスを採点します。クリック・Enter・Spaceを別々の観点として記録します。[ダイアログ対照と再実行手順](cases/2.4.3/README.md#ボタンで閉じた直後と次のtab)

正解は先にスナップショットへ固定し、ページ・画像・音声、使用する実装・スキル・検証手順の資料と実行上限、ブラウザー等の環境、原典のハッシュも記録します。実行中断後は同じ実装で再開できます。

```sh
python3 benchmarks/run.py collect --out /project/bench-001 --resume
```

完了済みページを再実行せず、未完了ページは新しいattemptへ記録します。途中の証拠・過去の試行は保持します。モード・対象・実装を変える場合は別runにします。元のページ・正解の版を変えて再開することはしません。

## AI・個別の機械検査・実SRの結果を取り込む

検査担当は[作業手順](WORKER.md)に従います。1ジョブずつ渡せます。

```sh
python3 benchmarks/run.py task --run /project/bench-001 --job ai--1.1.1--c02
python3 benchmarks/run.py serve --run /project/bench-001
```

serveは保存した公開ページだけを元と同じポートで提供します。実ページを再操作する間に起動し、作業後は終了します。AIに画像を確認させる場合も、結果のJSONを人が転記する必要はありません。担当AIが実際の証拠を確認し、以下の形式を作って取り込めます。

```json
{
  "schema_version": "1",
  "run_id": "worker/tasks.jsonのrun_id",
  "corpus_digest": "worker/tasks.jsonのcorpus_digest",
  "job_id": "ai--1.1.1--c02",
  "observations": [{
    "page": "p02.html",
    "state": "initial",
    "target": "#figure",
    "checkpoint": "1.1.1-04",
    "outcome": "cant_tell",
    "method": "ai",
    "observed": "この例は記録形式を示すもので、実際の画像の検査はまだ実施していません。",
    "evidence": []
  }]
}
```

これは正解や実測結果の例ではありません。実施した観察に置き換えます。確定する結果には、そのジョブの実証拠が必要です。画像を比較する観点は画像、複数ページの観点は全比較ページの証拠、実SRの観点は実際の発話と環境・対照確認が必要です。別ページの証拠、AXツリーだけの実SR扱い、モードで使わないAI等は拒否します。対象の別名はpublic taskのtarget_aliasesで論理部品へ揃えます。

```sh
python3 benchmarks/run.py attach --run /project/bench-001 --job ai--1.1.1--c02 --file /project/observed.png
python3 benchmarks/run.py import --run /project/bench-001 --file /project/observations.json
python3 benchmarks/run.py score --run /project/bench-001 --strict
```

判定は分割して取り込めます。同じ観点の更新は履歴を残し、別の観点を追加したときに前の結果を消しません。取り込み処理では、方法の申告、対象との対応、実在ファイルとハッシュを検証します。実行者がAIか人かまでは技術的に証明しません。

4.1.3の収録例には、ネイティブOrcaアダプターを使う専用workerがあります。各対照は新しいrunで実行します。空の領域へ「記録しました。」を出す対照は `--record-pair`、既存の「待機中」を「保存しました」に変える対照は `--save-pair` を指定します。

```sh
python3 benchmarks/run.py collect --mode screen-reader --criterion 4.1.3 --out /project/bench-status-record
python3 benchmarks/native_status.py --run /project/bench-status-record --root /project/prepared-debian-root --record-pair --import-results
```

同じモード・環境の対照例で通知、対象ボタンの発話とフォーカス、画面の更新を確認できた場合に採点します。別の対照を選んだrunでは、残る2例は未評価です。実Orcaが生成した発話ログを確認します。ライブのUnixソケットは短い一時パスで実行し、証拠はジョブ配下へバイトを変えず保存します。

## 「すべて検出」と回帰を分ける

結果は新しいreportsディレクトリへHTML・JSON・Excelで出力します。

- 問題のある正解を問題として検出したか。問題を正常とした見逃しを数えます。
- 正常な例を問題とした誤検出がないか。登録した観点の列挙範囲で、正解にない追加の問題も誤検出として報告します。
- 未実施・判断保留、モードで省いた観点を成功に数えていないか。
- 必要な観点がすべて実施され、正解と一致し、追加の誤検出がないか。

「clear_for_selected_checks」は、そのモードで評価を求める登録観点が一致した状態です。モードで省く観点が残れば全体はincompleteです。全86基準の適合や、その基準の全パターンを検証できたという意味にはしません。精度の数値は評価できた観点に限り、全問題の未検出数・未評価数も併記します。AI／実SRで確定結果を得た観点数も、実際の結果から集計します。判断保留の試行は各行に残します。

外部のAI・検査サービスを使う場合は、使用したモデル・バージョン・設定・プロンプトも観察ファイルや添付へ記録します。採点器が実行者の申告や外部サービスの同一性まで証明するわけではありません。

--strictの終了コードは、一致0、不一致・誤検出1、必要な検証の未実施2です。collectの成功は収集・記録の成功で、採点のクリアとは別です。

```sh
python3 benchmarks/run.py compare --baseline /project/old/reports/ID/result.json --current /project/new/reports/ID/result.json --out /project/diff.json
```

問題集・モード・対象・上限・環境・原典・採点器が同じ結果を比較します。検出実装が変わることは許容します。以前正しかった結果が誤りや未確認に変わった場合、新たな誤検出が増えた場合は回帰です。もともとの未確認が残るだけなら「新しい回帰なし」と報告しますが、問題集をクリアしたことにはしません。入力や採点器が違う場合は、同じ条件で再採点・再実行してから比較します。

## 問題を増やす

[追加手順と項目の説明](ADDING-CASES.md)に沿って、新しい基準のcases/番号/publicに必要なページ・素材を置き、suite.jsonに確認観点・状態・全対象の正解と根拠を記録します。正解は実装を走らせる前に定め、検出結果に合わせて書き換えません。実装の変更を試す場合は問題集を固定します。例自体を直す場合は新しい問題集の版として扱います。

根拠は基準本文・公開試験手順へ結び付けます。ACTの公開例を取り込む場合も、版・ライセンス・適用条件・ルールとWCAG基準の判定の対応を保ちます。ルール1つの成功を基準全体の適合に広げません。

この初版は同じ作成者が問題と正解を用意した回帰用の対照例です。独立した検査、未公開の例、端末・言語・実装の違いを追加するまでは、未知のサイトでの一般的な精度の保証に使いません。対象抽出と意味・機能の判定も別の観点として増やします。
