# WCAG検証スキル

サイトを調べ、ページ・状態・環境・達成基準ごとに実際の検査を行い、証拠付きの結果を出すAI向けスキルです。利用者がWCAGの番号や検査手順を指定する必要はありません。

開発中の1ページだけでも、サイト全体でも使えます。入口を分け、必要な段階だけを読み込む構成です。

今後の目的・現在地・次の開発作業は[開発計画](docs/ROADMAP.md)にまとめています。新しいセッションで開発を続けるときも、この文書から再開してください。

4スキルの責務と受け渡す情報、pstackから取り込む対象固有の操作手順は[設計方針](docs/SKILL-DESIGN.md)に記載しています。

| スキル | 利用する場面 |
| --- | --- |
| [wcag-page](skills/wcag-page/SKILL.md) | この1ページの画面・操作・達成基準を確認する |
| [wcag-pages](skills/wcag-pages/SKILL.md) | 対象URLを一覧から指定する、又は候補を抽出する |
| [wcag-report](skills/wcag-report/SKILL.md) | 保存済みの結果をHTML・JSON・Excelへまとめる |
| [wcag-audit-kit](skills/wcag-audit-kit/SKILL.md) | 依頼を振り分け、サイト全体をページ別タスクで進める |

AIが実行できる検査を進め、環境制約、信頼できる方法の不足、専門判断が必要な部分は、証拠と具体的な確認手順を添えて人へ引き継ぐ初版です。[86基準の実証状況](skills/wcag-audit-kit/references/VERIFICATION-COVERAGE.md)で、確認した範囲と未実証の対象を公開しています。

依頼例：

> このサイト全体をWCAG 2.2のAAで検証してください。何ができていて、何ができていないか、証拠と再現手順付きで報告してください。実装修正は行わないでください。

## スキルとして使う

`skills/`にある4つのフォルダーが、そのまま配置できるスキルです。生成コマンドは不要です。利用するAI環境のスキル登録先へ、必要なフォルダーをコピーするか、フォルダー全体へのリンクを登録してください。

- 1ページの検証：`skills/wcag-page/`だけを配置します。
- URLの選定：`skills/wcag-pages/`だけを配置します。
- 保存済み結果の報告：`skills/wcag-report/`だけを配置します。
- サイト全体の進行：4フォルダーすべてを配置します。`wcag-audit-kit`から他の3スキルを使います。

各フォルダーには`SKILL.md`、実行時の補助コード、資料、テンプレート、依存関係の一覧が入っています。登録方法や呼び出しの表記はAI環境に従います。登録後は、その環境のスキル選択機能で`wcag-page`等を選び、「このURLをWCAG 2.2 AAで検証して、Excelで報告して」と依頼します。以下のCLIコマンドを利用者が毎回入力する必要はありません。

4つとも明示呼び出し専用です。Cursor・Claude Code向けには`disable-model-invocation: true`、Codex向けには同梱の`agents/openai.yaml`へ`policy.allow_implicit_invocation: false`を設定しています。通常の開発依頼から監査を自動開始させず、`/wcag-page`又は`$wcag-page`等で選んで始めます。呼び出し表記は利用環境に従ってください。全体監査を選んだ後は、必要な子スキルのファイルを内部手順として読み進めます。

初回だけ、実行環境にPythonの依存物を導入します。配置したスキルのディレクトリーから次を実行します。この準備はAIに依頼することもできます。

```sh
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

追加の画像計測には同梱の`requirements-analysis.txt`、Guidepupを使う場合は同梱の`package.json`と`package-lock.json`を使います。実スクリーンリーダーのOS設定や実ブラウザー拡大等は、必要な方法の資料で対応条件を確認します。

AIはスキルの指示を読み、必要な補助コードを使って操作・計測・記録・Excel出力を行います。画面や内容の意味判断は、AIが有効な検証モードで証拠と比較して行います。共通コードと資料の同期は開発者の作業であり、利用者の導入手順には含めません。[開発手順](CONTRIBUTING.md)を参照してください。

## CLIを直接使う場合

以下はリポジトリのルートから補助CLIを直接実行する例です。AIからスキルを呼び出す通常の利用と、補助CLIだけを実行する利用を区別します。

```sh
python3 skills/wcag-audit-kit/scripts/audit.py page-audit --url https://example.com/contact --out /project/run-contact --mode machine
```

この入口は指定URLだけで開閉・選択・入れ子などの状態を探索し、実クリック・キー操作と各状態のaxeを実行します。探索・機械検査・ページ別HTML・JSON・Excelの出力にAIサービスやAPIキーは必要ありません。途中で止めたキューは再開できます。[1ページの実行手順](skills/wcag-audit-kit/references/page-audit.md)を参照してください。

操作順と到達条件が分かっているメニューでは、`keyboard_checks`を設定して再現できます。期待どおりに開かない、次の項目へ移れない、閉じたあとに親へ戻れない場合、食い違ったキーとフォーカスをページ別帳票に出します。[キーボード経路の設定例](skills/wcag-audit-kit/references/page-audit.md#既知のキーボード操作を検査する)

機械結果と、達成基準全体の適否は区別します。自動ルールで決まらない意味や目的、未探索の内容、必要な実SR等は追加検査に残します。`page-next`で次の票と機械結果・手順を取得し、利用できる道具から確認を進めます。`page-report`でそのページだけの結果を更新できます。既存の`page`は事前設定の状態を収集する入口として保持します。

検証に使う手段は[モード](skills/wcag-audit-kit/references/verification-modes.md)、画像の深さ・枚数は[観察設定](skills/wcag-audit-kit/references/inspection-profiles.md)で選べます。モードで使わない手段、画像の省略・上限・未探索は未確認として残します。トークン数や料金を保証する設定とは区別します。

サイト全体では1つのrunを正本とし、同じwcag-pageでページ別タスクを検査します。集計はその正本をwcag-reportへ渡します。

以前の`wcag-skills-draft`とZIPは変更していません。これは別のスキルです。旧下書きの設定とは書式が異なり、設定の自動移行はしません。

## モードを選ぶ

検査は「機械チェックのみ」「AI併用」「スクリーンリーダー併用」「AI＋スクリーンリーダー」から選べます。すべてのモードで機械検査を先に行います。AIによる画像・文章の比較と、実際の読み上げは、それぞれ必要な場合だけ有効にします。

```sh
python3 skills/wcag-audit-kit/scripts/audit.py page-audit --url https://example.com/contact --out /project/run-machine --mode machine
python3 skills/wcag-audit-kit/scripts/audit.py page-audit --url https://example.com/contact --out /project/run-ai --mode ai
python3 skills/wcag-audit-kit/scripts/audit.py page-audit --url https://example.com/contact --out /project/run-sr --mode screen-reader
python3 skills/wcag-audit-kit/scripts/audit.py page-audit --url https://example.com/contact --out /project/run-full --mode full
```

- `machine`：AIで内容を判断せず、スクリーンリーダーも使いません。画像の収集は省き、機械ルール・実操作・数値計測を進めます。設定なしで新しく`page-audit`を始める場合の既定です。
- `ai`：機械検査に加え、画像の代替文・見た目・文章の目的等を、スキルを使うAIが実際の証拠と比較します。実スクリーンリーダーは使いません。
- `screen-reader`：機械検査に加え、実際のスクリーンリーダーで操作・発話を確認します。AIで画像や意味を判断しません。対応するOS・ブラウザー・支援技術と、ページ専用の操作手順が必要です。
- `full`：機械検査・AIによる内容判断・実スクリーンリーダーのすべてを使います。音声の聴取・手話・閃光分析等、現在の手段が不足する確認は残ります。

CLIはAIサービスへ接続しません。AI併用の判断はスキルの実行環境で行い、実スクリーンリーダーは専用アダプターで対象ごとの操作を実行します。モードを選ぶだけで、その確認を実施したことにはなりません。`page-next`は選択したモードで進める観点と、省く観点・理由を返します。実行方法は[モードの仕様](skills/wcag-audit-kit/references/verification-modes.md)を参照してください。

## モード別に確認できること

全86達成基準を確認観点ごとの131行で掲載します。例えば画像の代替文が「存在すること」と「画像の意味を伝えること」は別の確認です。AIを使わず人が内容を比較することもできますが、表の各モードにはその人による内容判断を含めていません。

○：この確認観点の検査手段あり。△：一部の検査・証拠取得まで。×：このモードでは確認しない、又は信頼できる手段が未整備。対象ページの合否や検査済みを表す記号ではありません。

○でも対象・状態・期待値を指定して実行する必要があります。△の観点で取得した証拠だけを、基準全体の適合へ置き換えません。×の項目は検証結果の「対象外」ではなく、未確認として残します。各観点の[具体的な処理・準備・人への引き継ぎ条件](skills/wcag-audit-kit/references/verification-checkpoints.md)も確認できます。

| 達成基準・手順 | レベル | 確認すること | 機械のみ | AI併用 | SR併用 | AI＋SR | 制約・残る確認 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [1.1.1 非テキストコンテンツ](skills/wcag-audit-kit/references/criteria/1.1.1.md) | A | [画像や操作部品に設定された代替文・読み上げ用の名前を確認する。](skills/wcag-audit-kit/references/verification-checkpoints.md#111-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.1.1 非テキストコンテンツ](skills/wcag-audit-kit/references/criteria/1.1.1.md) | A | [背景画像・SVG・図表なども検査対象に含まれているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#111-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.1.1 非テキストコンテンツ](skills/wcag-audit-kit/references/criteria/1.1.1.md) | A | [必要な代替説明を、実際のスクリーンリーダーで利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#111-03) | × | × | ○ | ○ | 実際のスクリーンリーダーの環境と対象ごとの操作が必要。ツリーの取得では代用しない。 |
| [1.1.1 非テキストコンテンツ](skills/wcag-audit-kit/references/criteria/1.1.1.md) | A | [代替文や別の説明が、画像の目的・情報を伝えているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#111-04) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.2.1 音声のみ及び映像のみ (収録済)](skills/wcag-audit-kit/references/criteria/1.2.1.md) | A | [収録済みの音声のみ・映像のみのコンテンツと、代替の提供経路を確認する。](skills/wcag-audit-kit/references/verification-checkpoints.md#121-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.2.1 音声のみ及び映像のみ (収録済)](skills/wcag-audit-kit/references/criteria/1.2.1.md) | A | [代替が元の情報・順序・操作結果を伝えるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#121-02) | △ | △ | △ | △ | 一部だけ実証、又は条件を網羅する方法が不足。全対象・全条件を確認済みにしない。 全区間の映像・音声・代替を比較できるよう保存する。意味の一致の自動判定はない。 |
| [1.2.2 キャプション (収録済)](skills/wcag-audit-kit/references/criteria/1.2.2.md) | A | [字幕を選んで表示でき、再生時刻と対応付けられるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#122-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.2.2 キャプション (収録済)](skills/wcag-audit-kit/references/criteria/1.2.2.md) | A | [発話・話者・意味のある音が、同期した字幕で伝わるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#122-02) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 現在の実証環境では、人が音声と字幕を全区間で比較する。 |
| [1.2.3 音声解説、又はメディアに対する代替 (収録済)](skills/wcag-audit-kit/references/criteria/1.2.3.md) | A | [音声解説又は文章による代替へ到達し、利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#123-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.2.3 音声解説、又はメディアに対する代替 (収録済)](skills/wcag-audit-kit/references/criteria/1.2.3.md) | A | [代替で必要な映像・音声情報を得られるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#123-02) | △ | △ | △ | △ | 一部だけ実証、又は条件を網羅する方法が不足。全対象・全条件を確認済みにしない。 全区間と代替の内容を比較資料にする。元音声との意味の一致の自動判定はない。 |
| [1.2.4 キャプション (ライブ)](skills/wcag-audit-kit/references/criteria/1.2.4.md) | AA | [実際のライブ配信で字幕を表示できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#124-01) | △ | △ | △ | △ | 一部だけ実証、又は条件を網羅する方法が不足。全対象・全条件を確認済みにしない。 ライブ中の字幕表示・時刻・確認した時間帯を記録する。 |
| [1.2.4 キャプション (ライブ)](skills/wcag-audit-kit/references/criteria/1.2.4.md) | AA | [ライブの音声情報が字幕で伝わるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#124-02) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 現在の実証環境では、人が配信中の音声と字幕を比較する。 |
| [1.2.5 音声解説 (収録済)](skills/wcag-audit-kit/references/criteria/1.2.5.md) | AA | [音声解説を選び、全区間で再生できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#125-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.2.5 音声解説 (収録済)](skills/wcag-audit-kit/references/criteria/1.2.5.md) | AA | [元音声にない重要な映像情報が、音声解説で伝わるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#125-02) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 現在は人が元音声・映像・音声解説の情報を比較する。 |
| [1.2.6 手話 (収録済)](skills/wcag-audit-kit/references/criteria/1.2.6.md) | AAA | [手話映像が提供され、利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#126-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.2.6 手話 (収録済)](skills/wcag-audit-kit/references/criteria/1.2.6.md) | AAA | [手話が元の音声情報を伝えているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#126-02) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 同等性を確認できる別の手段がない場合、対象言語の手話を理解する担当が全区間を比較する。 |
| [1.2.7 拡張音声解説 (収録済)](skills/wcag-audit-kit/references/criteria/1.2.7.md) | AAA | [必要な箇所で映像を止め、拡張した音声解説を再生できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#127-01) | △ | △ | △ | △ | 一部だけ実証、又は条件を網羅する方法が不足。全対象・全条件を確認済みにしない。 解説時の一時停止・延長と全区間の再生を記録する。 |
| [1.2.7 拡張音声解説 (収録済)](skills/wcag-audit-kit/references/criteria/1.2.7.md) | AAA | [拡張した解説で必要な映像情報を得られるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#127-02) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 現在は人が解説音声を聴取し、映像情報が十分伝わるか確認する。 |
| [1.2.8 メディアに対する代替 (収録済)](skills/wcag-audit-kit/references/criteria/1.2.8.md) | AAA | [文章によるメディアの代替に到達し、利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#128-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.2.8 メディアに対する代替 (収録済)](skills/wcag-audit-kit/references/criteria/1.2.8.md) | AAA | [文章代替が全情報・順序・操作結果を伝えるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#128-02) | △ | △ | △ | △ | 一部だけ実証、又は条件を網羅する方法が不足。全対象・全条件を確認済みにしない。 全区間と文章代替を比較資料にする。情報の完全な一致の自動判定はない。 |
| [1.2.9 音声のみ (ライブ)](skills/wcag-audit-kit/references/criteria/1.2.9.md) | AAA | [ライブ音声の代替が、実際の配信中に利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#129-01) | △ | △ | △ | △ | 一部だけ実証、又は条件を網羅する方法が不足。全対象・全条件を確認済みにしない。 配信と代替の提供経路・表示時刻・確認した時間帯を記録する。 |
| [1.2.9 音声のみ (ライブ)](skills/wcag-audit-kit/references/criteria/1.2.9.md) | AAA | [代替がライブ音声の情報を伝えるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#129-02) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 現在の実証環境では、人が配信中の音声と代替の内容を比較する。 |
| [1.3.1 情報及び関係性](skills/wcag-audit-kit/references/criteria/1.3.1.md) | A | [見出し・表・入力欄などの構造や関連付けが実装されているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#131-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.3.1 情報及び関係性](skills/wcag-audit-kit/references/criteria/1.3.1.md) | A | [画面で分かる構造・関係が、プログラム又は文章でも分かるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#131-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.3.1 情報及び関係性](skills/wcag-audit-kit/references/criteria/1.3.1.md) | A | [必要な構造・関係を、実際のスクリーンリーダーで利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#131-03) | × | × | ○ | ○ | 実際のスクリーンリーダーの環境と対象ごとの操作が必要。ツリーの取得では代用しない。 |
| [1.3.2 意味のあるシーケンス](skills/wcag-audit-kit/references/criteria/1.3.2.md) | A | [ブラウザーが支援技術へ伝える読み順を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#132-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.3.2 意味のあるシーケンス](skills/wcag-audit-kit/references/criteria/1.3.2.md) | A | [意味が保たれる順序で読み進められるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#132-02) | × | △ | △ | ○ | 実際の読み上げと、画面・文脈の意味の比較の両方が必要。 |
| [1.3.3 感覚的な特徴](skills/wcag-audit-kit/references/criteria/1.3.3.md) | A | [指示が形・色・位置・方向・音だけに依存していないか。](skills/wcag-audit-kit/references/verification-checkpoints.md#133-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.3.4 表示の向き](skills/wcag-audit-kit/references/criteria/1.3.4.md) | AA | [縦向き・横向きの両方で表示・操作できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#134-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.3.4 表示の向き](skills/wcag-audit-kit/references/criteria/1.3.4.md) | AA | [実端末のセンサーやOSの向き固定が関わる制限も確認する。](skills/wcag-audit-kit/references/verification-checkpoints.md#134-02) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 物理センサー・OSの向き固定が関わり、必要な実端末を利用できないとき。 |
| [1.3.5 入力目的の特定](skills/wcag-audit-kit/references/criteria/1.3.5.md) | AA | [入力目的を表す属性が正しく記述されているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#135-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.3.5 入力目的の特定](skills/wcag-audit-kit/references/criteria/1.3.5.md) | AA | [指定した入力目的が、実際に集める利用者情報と合うか。](skills/wcag-audit-kit/references/verification-checkpoints.md#135-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.3.6 目的の特定](skills/wcag-audit-kit/references/criteria/1.3.6.md) | AAA | [部品・アイコン・領域の目的をプログラムで識別できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#136-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.4.1 色の使用](skills/wcag-audit-kit/references/criteria/1.4.1.md) | A | [色による情報の候補と各状態の表示を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#141-01) | × | ○ | × | ○ | 画像を保存する観点。画像を使うAI／fullモードで収集する。保存しただけでは画面の内容を検証したことにはならない。 |
| [1.4.1 色の使用](skills/wcag-audit-kit/references/criteria/1.4.1.md) | A | [必須・エラー・グラフ等の情報が、色以外でも伝わるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#141-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.4.2 音声の制御](skills/wcag-audit-kit/references/criteria/1.4.2.md) | A | [3秒を超える自動再生音声に、必要な制御があるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#142-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.4.3 コントラスト (最低限)](skills/wcag-audit-kit/references/criteria/1.4.3.md) | AA | [文字コントラストについて、axeが判定できる対象を検査する。](skills/wcag-audit-kit/references/verification-checkpoints.md#143-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.4.3 コントラスト (最低限)](skills/wcag-audit-kit/references/criteria/1.4.3.md) | AA | [文字と実際の背景のコントラストが、適用される比を満たすか。](skills/wcag-audit-kit/references/verification-checkpoints.md#143-02) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.4.4 テキストのサイズ変更](skills/wcag-audit-kit/references/criteria/1.4.4.md) | AA | [200%まで実際に文字を拡大できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#144-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.4.4 テキストのサイズ変更](skills/wcag-audit-kit/references/criteria/1.4.4.md) | AA | [拡大後も内容・機能を失わず利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#144-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.4.5 文字画像](skills/wcag-audit-kit/references/criteria/1.4.5.md) | AA | [文字を含む画像の候補を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#145-01) | × | ○ | × | ○ | 画像を保存する観点。画像を使うAI／fullモードで収集する。保存しただけでは画面の内容を検証したことにはならない。 |
| [1.4.5 文字画像](skills/wcag-audit-kit/references/criteria/1.4.5.md) | AA | [文字画像への依存がなく、例外を使う場合は条件を満たすか。](skills/wcag-audit-kit/references/verification-checkpoints.md#145-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.4.6 コントラスト (高度)](skills/wcag-audit-kit/references/criteria/1.4.6.md) | AAA | [AAAの文字コントラスト比を満たすか。](skills/wcag-audit-kit/references/verification-checkpoints.md#146-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [1.4.7 小さな背景音、又は背景音なし](skills/wcag-audit-kit/references/criteria/1.4.7.md) | AAA | [背景音がない、又は背景音を止める仕組みがあるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#147-01) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 現在は聴取と、必要に応じ分離音源・音響分析が必要。混合音全体の平均値で20dB差を確定しない。 |
| [1.4.7 小さな背景音、又は背景音なし](skills/wcag-audit-kit/references/criteria/1.4.7.md) | AAA | [20dB差の経路を使う場合、主音声と背景音の差を満たすか。](skills/wcag-audit-kit/references/verification-checkpoints.md#147-02) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 現在は聴取と、必要に応じ分離音源・音響分析が必要。混合音全体の平均値で20dB差を確定しない。 |
| [1.4.8 視覚的提示](skills/wcag-audit-kit/references/criteria/1.4.8.md) | AAA | [利用者が色・行幅・揃え・間隔を必要な条件に調整できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#148-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.4.8 視覚的提示](skills/wcag-audit-kit/references/criteria/1.4.8.md) | AAA | [200%拡大後に、1行を読むための横スクロールが不要か。](skills/wcag-audit-kit/references/verification-checkpoints.md#148-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.4.9 文字画像 (例外なし)](skills/wcag-audit-kit/references/criteria/1.4.9.md) | AAA | [文字画像が、AAAで許される装飾・本質的な表示等に限られるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#149-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.4.10 リフロー](skills/wcag-audit-kit/references/criteria/1.4.10.md) | AA | [指定した表示幅で画面とスクロールの状態を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#1410-01) | × | ○ | × | ○ | 画像を保存する観点。画像を使うAI／fullモードで収集する。保存しただけでは画面の内容を検証したことにはならない。 |
| [1.4.10 リフロー](skills/wcag-audit-kit/references/criteria/1.4.10.md) | AA | [必要な狭い表示領域でも内容・機能を失わず利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#1410-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.4.11 非テキストのコントラスト](skills/wcag-audit-kit/references/criteria/1.4.11.md) | AA | [部品の識別・状態・図形に必要な情報が、隣接色と3:1以上か。](skills/wcag-audit-kit/references/verification-checkpoints.md#1411-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.4.12 テキストの間隔](skills/wcag-audit-kit/references/criteria/1.4.12.md) | AA | [文字間隔等を基準の値に変更しても、内容・機能を失わないか。](skills/wcag-audit-kit/references/verification-checkpoints.md#1412-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [1.4.13 ホバー又はフォーカスで表示されるコンテンツ](skills/wcag-audit-kit/references/criteria/1.4.13.md) | AA | [ポインターを重ねた後・フォーカス後に出る内容を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#1413-01) | × | ○ | × | ○ | 画像を保存する観点。画像を使うAI／fullモードで収集する。保存しただけでは画面の内容を検証したことにはならない。 |
| [1.4.13 ホバー又はフォーカスで表示されるコンテンツ](skills/wcag-audit-kit/references/criteria/1.4.13.md) | AA | [表示された追加内容を消せる・上へ移動できる・必要な間表示できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#1413-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.1.1 キーボード](skills/wcag-audit-kit/references/criteria/2.1.1.md) | A | [抽出した操作候補へ、キーで到達・操作できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#211-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [2.1.1 キーボード](skills/wcag-audit-kit/references/criteria/2.1.1.md) | A | [画面にある各機能を、キーボードで開始から完了まで利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#211-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.1.2 キーボードトラップなし](skills/wcag-audit-kit/references/criteria/2.1.2.md) | A | [基本のキー操作でフォーカスがどこへ移るか。](skills/wcag-audit-kit/references/verification-checkpoints.md#212-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [2.1.2 キーボードトラップなし](skills/wcag-audit-kit/references/criteria/2.1.2.md) | A | [開いたダイアログや入れ子の部品から、キーボードで離脱できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#212-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.1.3 キーボード (例外なし)](skills/wcag-audit-kit/references/criteria/2.1.3.md) | AAA | [軌跡依存も含め、すべての機能をキーボードで利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#213-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.1.4 文字キーのショートカット](skills/wcag-audit-kit/references/criteria/2.1.4.md) | A | [文字だけのショートカットを無効化・再割当できるか、対象内だけで動くか。](skills/wcag-audit-kit/references/verification-checkpoints.md#214-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.2.1 タイミング調整可能](skills/wcag-audit-kit/references/criteria/2.2.1.md) | A | [時間制限を無効化又は調整する方法で、活動を続けられるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#221-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.2.1 タイミング調整可能](skills/wcag-audit-kit/references/criteria/2.2.1.md) | A | [延長する方法を採用した場合、警告と繰り返し延長の条件を満たすか。](skills/wcag-audit-kit/references/verification-checkpoints.md#221-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.2.2 一時停止、停止、非表示](skills/wcag-audit-kit/references/criteria/2.2.2.md) | A | [動きや自動更新を、一時停止・停止・非表示・頻度調整できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#222-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.2.3 タイミング非依存](skills/wcag-audit-kit/references/criteria/2.2.3.md) | AAA | [許される例外以外で、時間内の応答を活動の条件にしていないか。](skills/wcag-audit-kit/references/verification-checkpoints.md#223-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.2.4 割り込み](skills/wcag-audit-kit/references/criteria/2.2.4.md) | AAA | [緊急以外の割り込みを、延期又は抑制できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#224-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.2.5 再認証](skills/wcag-audit-kit/references/criteria/2.2.5.md) | AAA | [再認証後もデータ・変更を失わず、活動を継続・完了できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#225-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.2.6 タイムアウト](skills/wcag-audit-kit/references/criteria/2.2.6.md) | AAA | [データ損失までの無操作時間が、利用者へ伝わるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#226-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.2.6 タイムアウト](skills/wcag-audit-kit/references/criteria/2.2.6.md) | AAA | [告知の代わりに長期保存の条件を使う場合、20時間超の保持を確認できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#226-02) | △ | △ | △ | △ | 一部だけ実証、又は条件を網羅する方法が不足。全対象・全条件を確認済みにしない。 長期間の保存を別の試験として観察する。短い待機結果だけでは確定できない。 |
| [2.3.1 3 回の閃光、又は閾値以下](skills/wcag-audit-kit/references/criteria/2.3.1.md) | A | [閃光の発生区間を抜けなく分析できる資料を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#231-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [2.3.1 3 回の閃光、又は閾値以下](skills/wcag-audit-kit/references/criteria/2.3.1.md) | A | [閃光の回数又は一般・赤色閃光の閾値を満たすか。](skills/wcag-audit-kit/references/verification-checkpoints.md#231-02) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 信頼できる専用分析器を用意できなければ、分析できる専門担当へ引き継ぐ。 |
| [2.3.2 3 回の閃光](skills/wcag-audit-kit/references/criteria/2.3.2.md) | AAA | [1秒間の閃光が3回を超えないか。](skills/wcag-audit-kit/references/verification-checkpoints.md#232-01) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 信頼できる専用分析器を用意できなければ、分析できる専門担当へ引き継ぐ。 |
| [2.3.3 インタラクションによるアニメーション](skills/wcag-audit-kit/references/criteria/2.3.3.md) | AAA | [操作による動きを無効にでき、情報・機能を保てるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#233-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.4.1 ブロックスキップ](skills/wcag-audit-kit/references/criteria/2.4.1.md) | A | [繰り返すブロックを飛ばす手段が利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#241-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.4.2 ページタイトル](skills/wcag-audit-kit/references/criteria/2.4.2.md) | A | [ページタイトルが設定されているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#242-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [2.4.2 ページタイトル](skills/wcag-audit-kit/references/criteria/2.4.2.md) | A | [タイトルがこのページの主題・目的を説明しているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#242-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.4.3 フォーカス順序](skills/wcag-audit-kit/references/criteria/2.4.3.md) | A | [標準探索でのTab順と、操作後のフォーカス位置を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#243-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [2.4.3 フォーカス順序](skills/wcag-audit-kit/references/criteria/2.4.3.md) | A | [各状態で意味と操作を保つ順序になっているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#243-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.4.4 リンクの目的 (コンテキスト内)](skills/wcag-audit-kit/references/criteria/2.4.4.md) | A | [リンクの文言と許される文脈から、目的を特定できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#244-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.4.5 複数の手段](skills/wcag-audit-kit/references/criteria/2.4.5.md) | AA | [ページを見つける複数の手段があるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#245-01) | △ | △ | △ | △ | 他ページ・手続き・サイト構成の情報が必要。1ページだけの検査では確定できない。 |
| [2.4.6 見出し及びラベル](skills/wcag-audit-kit/references/criteria/2.4.6.md) | AA | [見出し・ラベルが、その部分や操作の主題・目的を説明しているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#246-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.4.7 フォーカスの可視化](skills/wcag-audit-kit/references/criteria/2.4.7.md) | AA | [標準のキー移動後に、画面がどう表示されるか取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#247-01) | × | ○ | × | ○ | 画像を保存する観点。画像を使うAI／fullモードで収集する。保存しただけでは画面の内容を検証したことにはならない。 |
| [2.4.7 フォーカスの可視化](skills/wcag-audit-kit/references/criteria/2.4.7.md) | AA | [すべての操作部品・サブ部品で、フォーカス位置が見えるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#247-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.4.8 現在位置](skills/wcag-audit-kit/references/criteria/2.4.8.md) | AAA | [サイト内の現在位置を示す情報があるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#248-01) | △ | △ | △ | △ | 他ページ・手続き・サイト構成の情報が必要。1ページだけの検査では確定できない。 |
| [2.4.9 リンクの目的 (リンクのみ)](skills/wcag-audit-kit/references/criteria/2.4.9.md) | AAA | [リンク単独で目的を識別する仕組みがあるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#249-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.4.10 セクション見出し](skills/wcag-audit-kit/references/criteria/2.4.10.md) | AAA | [内容がセクション見出しで整理されているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#2410-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.4.11 隠されないフォーカス (最低限)](skills/wcag-audit-kit/references/criteria/2.4.11.md) | AA | [作者が配置した内容により、フォーカス部品全体が隠れないか。](skills/wcag-audit-kit/references/verification-checkpoints.md#2411-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.4.12 隠されないフォーカス (高度)](skills/wcag-audit-kit/references/criteria/2.4.12.md) | AAA | [作者が配置した内容により、フォーカス部品の一部も隠れないか。](skills/wcag-audit-kit/references/verification-checkpoints.md#2412-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.4.13 フォーカスの外観](skills/wcag-audit-kit/references/criteria/2.4.13.md) | AAA | [フォーカス表示が、前後のコントラストと必要な面積を満たすか。](skills/wcag-audit-kit/references/verification-checkpoints.md#2413-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [2.5.1 ポインタのジェスチャ](skills/wcag-audit-kit/references/criteria/2.5.1.md) | A | [複数点・軌跡依存の操作を、単純な単一ポインター操作でも行えるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#251-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.5.2 ポインタのキャンセル](skills/wcag-audit-kit/references/criteria/2.5.2.md) | A | [誤って押したときに取消・元に戻す等の条件を満たすか。](skills/wcag-audit-kit/references/verification-checkpoints.md#252-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.5.3 ラベルを含む名前 (name)](skills/wcag-audit-kit/references/criteria/2.5.3.md) | A | [部品の見えるラベルと、読み上げ用の名前を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#253-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [2.5.3 ラベルを含む名前 (name)](skills/wcag-audit-kit/references/criteria/2.5.3.md) | A | [見えるラベルの文字が、読み上げ用の名前に含まれるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#253-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.5.4 動きによる起動](skills/wcag-audit-kit/references/criteria/2.5.4.md) | A | [動きで起動する機能をUIでも使え、必要な動き応答を無効化できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#254-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.5.4 動きによる起動](skills/wcag-audit-kit/references/criteria/2.5.4.md) | A | [実際の動き・センサー・カメラの条件でも確認できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#254-02) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 物理的な動き・カメラ・センサーが関わり、対応実機を利用できないとき。 |
| [2.5.5 ターゲットのサイズ (高度)](skills/wcag-audit-kit/references/criteria/2.5.5.md) | AAA | [実際に押せる範囲が44×44 CSS px以上か、AAAの例外を満たすか。](skills/wcag-audit-kit/references/verification-checkpoints.md#255-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.5.6 入力メカニズムの共存](skills/wcag-audit-kit/references/criteria/2.5.6.md) | AAA | [利用可能な入力方式を切り替えて、機能を利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#256-01) | △ | △ | △ | △ | 一部だけ実証、又は条件を網羅する方法が不足。全対象・全条件を確認済みにしない。 キー・マウス・タッチを切り替えて同じ機能を実行し、結果を記録する。 |
| [2.5.7 ドラッグ動作](skills/wcag-audit-kit/references/criteria/2.5.7.md) | AA | [ドラッグせず、単一ポインターで同じ機能を利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#257-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [2.5.8 ターゲットのサイズ (最低限)](skills/wcag-audit-kit/references/criteria/2.5.8.md) | AA | [操作対象の大きさと位置を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#258-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [2.5.8 ターゲットのサイズ (最低限)](skills/wcag-audit-kit/references/criteria/2.5.8.md) | AA | [24×24 CSS px以上か、小さい場合に間隔等の例外を満たすか。](skills/wcag-audit-kit/references/verification-checkpoints.md#258-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.1.1 ページの言語](skills/wcag-audit-kit/references/criteria/3.1.1.md) | A | [ページの言語が、正しい形式で指定されているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#311-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [3.1.1 ページの言語](skills/wcag-audit-kit/references/criteria/3.1.1.md) | A | [指定した言語が、ページの主たる言語と一致するか。](skills/wcag-audit-kit/references/verification-checkpoints.md#311-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.1.2 一部分の言語](skills/wcag-audit-kit/references/criteria/3.1.2.md) | AA | [部分ごとに指定された言語を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#312-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [3.1.2 一部分の言語](skills/wcag-audit-kit/references/criteria/3.1.2.md) | AA | [異なる言語の箇所を識別でき、実際の言語と指定が合うか。](skills/wcag-audit-kit/references/verification-checkpoints.md#312-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.1.3 一般的ではない用語](skills/wcag-audit-kit/references/criteria/3.1.3.md) | AAA | [一般的でない用語・慣用句の意味を知る仕組みがあるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#313-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.1.4 略語](skills/wcag-audit-kit/references/criteria/3.1.4.md) | AAA | [略語の意味を知る仕組みがあるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#314-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.1.5 読解レベル](skills/wcag-audit-kit/references/criteria/3.1.5.md) | AAA | [必要な補足・易しい版へ到達できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#315-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [3.1.5 読解レベル](skills/wcag-audit-kit/references/criteria/3.1.5.md) | AAA | [前期中等教育を超える読解力が必要な場合、補足等が十分か。](skills/wcag-audit-kit/references/verification-checkpoints.md#315-02) | × | × | × | × | 現行の実証環境では、この確認を確定できる手段が不足。専門環境・専門担当等が必要。 検証済みの言語別評価方法がなければ、教育段階・補足の十分性を判断できる担当が必要。 |
| [3.1.6 発音](skills/wcag-audit-kit/references/criteria/3.1.6.md) | AAA | [発音が分からないと意味が曖昧になる語に、発音を知る仕組みがあるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#316-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.2.1 フォーカス時](skills/wcag-audit-kit/references/criteria/3.2.1.md) | A | [フォーカス時の画面・URL等の変化を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#321-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [3.2.1 フォーカス時](skills/wcag-audit-kit/references/criteria/3.2.1.md) | A | [フォーカスを受けるだけで、利用者の文脈が変わっていないか。](skills/wcag-audit-kit/references/verification-checkpoints.md#321-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.2.2 入力時](skills/wcag-audit-kit/references/criteria/3.2.2.md) | A | [入力値の変更で文脈が変わる場合、事前に説明されているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#322-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.2.3 一貫したナビゲーション](skills/wcag-audit-kit/references/criteria/3.2.3.md) | AA | [複数ページで繰り返すナビゲーションの相対順序が一貫しているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#323-01) | △ | △ | △ | △ | 他ページ・手続き・サイト構成の情報が必要。1ページだけの検査では確定できない。 |
| [3.2.4 一貫した識別性](skills/wcag-audit-kit/references/criteria/3.2.4.md) | AA | [複数ページで同じ機能を一貫して識別できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#324-01) | △ | △ | △ | △ | 他ページ・手続き・サイト構成の情報が必要。1ページだけの検査では確定できない。 |
| [3.2.5 要求による変化](skills/wcag-audit-kit/references/criteria/3.2.5.md) | AAA | [文脈の変化が利用者の要求で起こるか、無効化できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#325-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.2.6 一貫したヘルプ](skills/wcag-audit-kit/references/criteria/3.2.6.md) | A | [繰り返し提供するヘルプ手段の相対順序が一貫しているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#326-01) | △ | △ | △ | △ | 他ページ・手続き・サイト構成の情報が必要。1ページだけの検査では確定できない。 |
| [3.3.1 エラーの特定](skills/wcag-audit-kit/references/criteria/3.3.1.md) | A | [入力エラーの項目を特定し、内容を文章で説明しているか。](skills/wcag-audit-kit/references/verification-checkpoints.md#331-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.3.2 ラベル又は説明](skills/wcag-audit-kit/references/criteria/3.3.2.md) | A | [入力欄のラベル・読み上げ用の名前・画面を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#332-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [3.3.2 ラベル又は説明](skills/wcag-audit-kit/references/criteria/3.3.2.md) | A | [利用者に必要なラベル・入力説明が表示されるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#332-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.3.3 エラー修正の提案](skills/wcag-audit-kit/references/criteria/3.3.3.md) | AA | [修正方法が分かるエラーに、適切な修正案があるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#333-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.3.4 誤り防止 (法的、金融、データ)](skills/wcag-audit-kit/references/criteria/3.3.4.md) | AA | [法的・金融・データ等の対象操作に、誤りを防ぐ方法があるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#334-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.3.5 ヘルプ](skills/wcag-audit-kit/references/criteria/3.3.5.md) | AAA | [入力の文脈に応じたヘルプを利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#335-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.3.6 誤り防止 (すべて)](skills/wcag-audit-kit/references/criteria/3.3.6.md) | AAA | [AAAの対象となるすべての送信に、誤りを防ぐ方法があるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#336-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.3.7 冗長な入力項目](skills/wcag-audit-kit/references/criteria/3.3.7.md) | A | [同じ手続きの中で、既に入力した情報を再利用できるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#337-01) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.3.8 アクセシブルな認証 (最低限)](skills/wcag-audit-kit/references/criteria/3.3.8.md) | AA | [認証で貼り付け・自動入力等の支援を実際に使えるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#338-01) | △ | △ | △ | △ | 一部だけ実証、又は条件を網羅する方法が不足。全対象・全条件を確認済みにしない。 実クリップボードからの貼り付け等を試す。第三者パスワードマネージャー・全方式は未実証。 |
| [3.3.8 アクセシブルな認証 (最低限)](skills/wcag-audit-kit/references/criteria/3.3.8.md) | AA | [認知機能テストがある場合、AAで許される代替・支援・例外があるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#338-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [3.3.9 アクセシブルな認証 (高度)](skills/wcag-audit-kit/references/criteria/3.3.9.md) | AAA | [AAAの認証でも貼り付け・自動入力・代替認証を使えるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#339-01) | △ | △ | △ | △ | 一部だけ実証、又は条件を網羅する方法が不足。全対象・全条件を確認済みにしない。 実際の貼り付け・自動入力・代替経路を試す。第三者マネージャー等は対象での実証が必要。 |
| [3.3.9 アクセシブルな認証 (高度)](skills/wcag-audit-kit/references/criteria/3.3.9.md) | AAA | [認知機能テストがある場合、AAAの代替・支援の条件を満たすか。](skills/wcag-audit-kit/references/verification-checkpoints.md#339-02) | △ | ○ | △ | ○ | 機械のみ・SRのみでは証拠取得や一部検査まで。画像・文章・操作結果の意味はAI又は人が比較する。 |
| [4.1.2 名前 (name)・役割 (role)・値 (value)](skills/wcag-audit-kit/references/criteria/4.1.2.md) | A | [部品の名前・役割・状態と、操作後の変化を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#412-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [4.1.2 名前 (name)・役割 (role)・値 (value)](skills/wcag-audit-kit/references/criteria/4.1.2.md) | A | [すべての独自部品の名前・役割・設定可能な状態・変更が伝わるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#412-02) | × | △ | △ | ○ | 実際の読み上げと、画面・文脈の意味の比較の両方が必要。 |
| [4.1.3 ステータスメッセージ](skills/wcag-audit-kit/references/criteria/4.1.3.md) | AA | [更新後に支援技術へ渡される情報を取得する。](skills/wcag-audit-kit/references/verification-checkpoints.md#413-01) | ○ | ○ | ○ | ○ | 対象・操作・期待値を指定した機械検査又は証拠取得。内容の意味の判断は含まない。 |
| [4.1.3 ステータスメッセージ](skills/wcag-audit-kit/references/criteria/4.1.3.md) | AA | [対象のステータスメッセージが、フォーカスを動かさず支援技術へ伝わるか。](skills/wcag-audit-kit/references/verification-checkpoints.md#413-02) | × | × | ○ | ○ | 実際のスクリーンリーダーの環境と対象ごとの操作が必要。ツリーの取得では代用しない。 |

方法の実証範囲は[方法ごとの準備状況](skills/wcag-audit-kit/references/method-capabilities.json)、実施済みの試験は[実証状況](skills/wcag-audit-kit/references/VERIFICATION-COVERAGE.md)を参照してください。対応表と保存済みの合否は別に管理します。

## 収録した検査内容

- 全86基準の適用条件、列挙する対象、具体的な操作、判定事項、観察方法。
- W3C勧告の本文・定義と、基準別の公式解説86件。
- W3Cの達成方法・失敗例526件。各基準に関係する公開試験手順を別ファイルで参照できる。
- ACT Rulesの現行87ルールと、その版に対応する具体例1,177件の索引。承認状態と、ルールから基準への判定の対応を保持している。
- freeeの公開チェックリストのテキスト版と、使用時の位置付け。
- 実行用CLI、ブラウザー収集器、数値計算の補助、検査票と報告のひな型。
- 実際の読み上げ、拡大、ポインター、向き、媒体の観察用の補助。媒体では未確認の区間を残し、全区間の比較に抜けがある確定記録を拒否する。

AAを目標にするとAとAAの55基準を検査します。AAAなら86基準です。目標レベル外の基準も、未検証であることを報告に残します。削除された4.1.1は対象にしません。

[原典とライセンス](skills/wcag-audit-kit/references/SOURCES.md)、[検査定義の索引](skills/wcag-audit-kit/references/INDEX.md)、[試験記録](VALIDATION.md)を確認できます。

## 分担・中断・再開とExcel出力

検査票をページ又は基準ごとに小さいタスクへ分割し、担当・作業状態・メモを保存できます。次回は同じタスクの未完了票から続けます。Excelは閲覧用と作業用を用意し、担当・メモ・判定の編集を証拠付きで取り込めます。同じ票への更新が競合したら取り込み全体を止めます。

```sh
python3 skills/wcag-audit-kit/scripts/audit.py tasks create --run /project/artifacts/wcag/run-001 --group-by page --size 20
python3 skills/wcag-audit-kit/scripts/audit.py tasks list --run /project/artifacts/wcag/run-001
python3 skills/wcag-audit-kit/scripts/audit.py excel export --run /project/artifacts/wcag/run-001 --mode report --out /project/wcag-report.xlsx
```

[共同作業の手順](skills/wcag-audit-kit/references/collaboration.md)には、担当の取得、タスク別の作業用Excel、取り込みの事前確認、競合の解消、中断後の再開を記しています。対象・証拠等を省いて判定だけを合格にする操作は拒否します。タスク分割は収集済みの検査票が対象です。

HTMLとExcelには、人向けの[達成基準チェックシート](skills/wcag-audit-kit/references/checksheet.md)を出力します。1.1.1などの基準ごとに行を用意し、確認観点が複数あれば内訳の行を追加します。適用・適合・未確認と、不適合のURL・状態・対象要素・再現手順・証拠を確認できます。Excelの先頭2シートは閲覧用です。作業結果を取り込む場合は、従来の検査票・対象・観察方法シートを使います。

今後の変更はPRと[ADR](docs/adr/README.md)で記録します。[変更の進め方](CONTRIBUTING.md)を参照してください。

開発時に実行した[検証の証拠とレポート](validation/README.md)も保存しています。未確認が残る報告例も含み、スキル全体の検証完了を示すものではありません。

[単独ページの通し検査](validation/full-fixture/README.md)では、AAの55基準を3状態で検査し、通過75・対象外90として、その固定した範囲の検査を完了しました。状態更新を欠く比較ページの4.1.2は不適合として報告しました。これは既知の小さい試験ページでの確認であり、未知のサイトに対する独立した精度評価は残っています。

[原典との照合による手順の改訂](validation/procedure-review/README.md)では、AAA全31基準と関連する定義等を確認し、媒体の代替を含む10手順を更新しました。過去の検査結果は、当時の定義と共に保持しています。

[フォーカス表示の校正](validation/focus-appearance/README.md)では、同じ画素の前後の比と面積を実測し、面積不足と、隣接色との比だけでは分からない前後の変化不足を区別しました。[測定補助の使い方](skills/wcag-audit-kit/references/focus-appearance.md)には適用範囲と追加依存物を記しています。

[時間制限と再認証の校正](validation/timing/README.md)では、実時間で10回の延長と警告時間、制限の無効化、再認証後のデータ保持・保存完了を比較しました。[時間制限の手順](skills/wcag-audit-kit/references/timing.md)で、期限や保存期間の記述だけから通過にしない方法を確認できます。

[複数ページの通し検証](validation/site-acceptance/README.md)では、5ページ・20状態・2表示幅の2,200票すべてに、判定又は具体的な人への引き継ぎを記録しました。通過1,342・対象外762・不適合16・人による確認待ち80、未実施0です。人の確認が残るため、このサイトのWCAG適合・検証完了は宣言していません。

[正解を伏せた公開例との比較](validation/act-held-out/README.md)では、ACTの2ルール・12例を実DOM/AXから判定し、公開期待値と12例すべてが一致しました。これはその2ルールの限定した比較で、全WCAG又は専門家によるサイト監査と同等の精度を示す数値ではありません。

## 検証方法の精度と回帰を試す

[基準別の問題集](benchmarks/README.md)では、1.1.1・2.1.1等のディレクトリへHTML・画像・音声と正解をまとめています。問題と正常な例、操作後の状態、複数ページを比較し、モード別の検出漏れ・誤検出・未確認をHTML・JSON・Excelへ出力します。検査担当へ正解は渡さず、実際の検証パイプラインの結果を採点します。

```sh
python3 benchmarks/run.py collect --mode all --out /project/benchmark-001
python3 benchmarks/run.py score --run /project/benchmark-001 --strict
```

全86達成基準・131確認観点に入力を用意しています。304ケース・312ページ分の入力に、判定の期待結果323行と取得の期待結果36行を収録しています。[基準ごとの一覧](benchmarks/COVERAGE.md)と[60組の追加パターン](benchmarks/PATTERNS.md)から参照できます。判定114観点と取得17観点を分け、取得期待の照合は未接続・未確認として残します。検出器が正解できるようにする実装は次の段階です。前回と同じ問題集・条件で比較し、以前検出したものの見逃しや新しい誤検出を回帰として報告できます。

## 実行環境

CLIにはPython 3.10以降、PyYAML、Playwright、Chromiumが必要です。既存環境があればそれを使います。

```sh
python3 -m pip install -r requirements.txt
python3 skills/wcag-audit-kit/scripts/audit.py doctor
```

Chromiumがなければ、利用環境に従いPlaywrightのChromium等を準備します。実際のスクリーンリーダー、実ブラウザーの拡大、動画・音声・閃光の分析等は、[観察方法の一覧](skills/wcag-audit-kit/references/methods.md)に従って必要な環境を調べます。

CLIはAIの判断に必要な証拠と検査票を用意します。CLIを1回実行しただけでは監査は完了しません。スキルを使うAIが各検査票の対象を確認し、実際に操作・観察して結果を記録します。

実スクリーンリーダー用には[GuidepupとネイティブOrcaのアダプター](skills/wcag-audit-kit/references/screen-reader.md)を用意しています。Guidepupは配置したスキルのディレクトリーで`npm ci --ignore-scripts`でライブラリーを用意し、`npm run screen-reader:doctor`で対応条件を確認します。現在のLinuxでは、Orcaを直接起動する別の実バックエンドでも、通知・名前・チェック状態・見出し移動を確認しました。利用した手段と実際に確認した範囲を記録し、取得できない発話を仮想読み上げへ置き換えて確認済みにはしません。

[Guidepupを使う設計と実験の要点](GUIDEPUP-NOTES.md)では、達成基準と実ページからシナリオを具体化する流れと、見た目が同じで読み上げに伝わる状態が異なる例を説明しています。

[実ブラウザーの拡大](skills/wcag-audit-kit/references/zoom.md)は、Linuxの専用X11環境で実行できます。200%・400%に加えて中間倍率も操作し、実測値、各段階の画面・DOM、操作結果を残します。用意した画像だけで全機能の検証を済ませず、各状態で操作して確認します。

## 出力するもの

| ファイル | 内容 |
| --- | --- |
| `report.html` | 達成基準・確認観点ごとのチェックシート、不適合箇所、ページ・状態・環境別の検査票 |
| Excel（出力先を指定） | 先頭に人向けチェックシート・不適合箇所、後ろに検査票・対象等の詳細シート |
| `report.json` | 全検査の結果、証拠、未実施・判断保留を含むデータ |
| `issues.md` | 修正担当向けの対象要素、再現手順、期待結果、観察結果 |
| `human-review.md` | 人に必要な知識・環境、試した方法、対象ごとの残る操作・判定条件・証拠 |
| `evidence/` | 画面、DOM、ツリー、操作ログ、測定結果等 |
| `assessments/` | 判定の履歴。新しい判定で過去の記録を削除しない |
| `verification.snapshot.json` | モードを指定したrunの確認観点・対応表。当時の版とハッシュを保持する |
| `catalog.snapshot.json` | 当時の検査定義。スキル更新後も、旧判定を当時の定義で再集計するために保持する |

検査の通過、不適合、対象外、判断保留、未実施を分けます。未確認の残るレポートには検証未完了を表示します。収集器の結果からサイト全体の適合を自動で宣言する機能はありません。

人への引き継ぎは[取り決め](skills/wcag-audit-kit/references/human-review.md)に従い、未確認として残します。全票に判定又は具体的な引き継ぎを記録し、範囲と残る適合要件を報告できた時点で、AIが今回行える作業を終えて結果を渡します。

## 最初の試行

[実行コマンド](skills/wcag-audit-kit/references/commands.md)の手順で、試験用サイトを監査できます。試験用サイトは意図的な不適合を含みます。実サイトで使う場合は、実際のページと状態の調査から始めてください。

スキルの記述と、現在の環境で実行できた検査の範囲は分けています。[試験記録](VALIDATION.md)に、確認済みの動作と、まだ評価していない範囲を記載しています。
