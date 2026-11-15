# 原典、参照元、ライセンス

## WCAGの要件

[WCAG 2.2の2024-12-12勧告](https://www.w3.org/TR/2024/REC-WCAG22-20241212/)のHTMLを[sources/wcag22.html](sources/wcag22.html)へ保存した。本文・例外・注記を基準ごとに抽出し、[公式解説](https://www.w3.org/WAI/WCAG22/Understanding/)を合わせて`references/sources/<基準番号>.md`へ保存している。

英語本文が要件の確認先。日本語の手順は、このスキル向けに作成した検査の進め方であり、W3Cによる承認済み試験手順ではない。原典の条件・定義・例外を短い手順で置き換えない。

日本語の基準名は、既存教材`wcag-for-beginners/data/criteria.json`から整理した名称一覧を同梱した。参照先は[WAICの翻訳](https://waic.jp/translations/WCAG22/Understanding/)。条件の判断にはW3C本文を使う。

## 公開試験手順

[W3C Techniques](https://www.w3.org/WAI/WCAG22/Techniques/)から、各基準に関連する十分な達成方法、推奨、失敗例とTestsを参照した。

個別ページの取得ではアクセス頻度制限が発生したため、[W3Cの公式リポジトリ](https://github.com/w3c/wcag)の固定コミットから一括取得した。HTMLソースの本文をテキストに変換し、基準別の関連資料へ再構成した。公開ページから取得できた資料も含む。取得元とコミット、SHA-256は[manifest](sources/manifest.json)と[repository](sources/repository.json)にある。未解決の取得失敗は0件。

[Techniquesの位置付け](https://www.w3.org/WAI/WCAG22/Understanding/understanding-techniques)に従い、十分な達成方法の未採用だけで不適合としない。複数の方法のAND/OR、技術・対象・例外、アクセシビリティサポートを確認する。

[原典と参考手順の相違](SOURCE-DISCREPANCIES.md)を別に記録する。G195のTestsと2.4.13の面積の条件が異なる箇所では、採用した勧告本文を優先し、参照した原文は変更しない。

W3Cの著作権と使用条件は、元HTMLと[ライセンス](sources/W3C-LICENSE.txt)を保持した。抽出・再配置したテキストは原文の公式文書そのものではない。公式URLを各項目へ付けた。

## ACT Rulesの本文と具体例

[W3Cの公式ACT Rulesリポジトリ](https://github.com/w3c/wcag-act-rules)のコミット`9a2d7f903357eb728a0f83f00db75d4f32417ab4`から、現行87ルールの本文と、状態・要求との対応・具体例のメタデータを取得した。全91取得ファイルについてGitのblob SHA-1とSHA-256を確認した。[取得元とハッシュ](sources/act/repository.json)、[原典のライセンス](sources/act/LICENSE.md)、[使用方法](ACT.md)を保存している。

承認済み37、提案中50、廃止7の区分を保持した。基準とのprimary/secondaryの対応と、各ルールの結果から基準へ何が言えるかを変更せず収録した。選んだ版の具体例1,177件を索引化している。廃止ルールを新しい検査へ割り当てず、別の版の例を承認済みの例として混ぜない。配布物は独自の再配置・索引であり、W3Cの公式公開サイトの代替や、スキルがACTに適合したとの宣言ではない。

## freeeの公開チェックリスト

[freeeアクセシビリティー・チェックリスト](https://a11y-guidelines.freee.co.jp/checks/checklist.html)のテキストを[sources/freee-checklist.txt](sources/freee-checklist.txt)へ収録した。

著作者はフリー株式会社。ライセンスは[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。変更はHTMLからのテキスト抽出。チェックID、対象、具体的な実施手順、自動ツールだけで確認できないケースの構成を参考にした。

[策定方針](https://a11y-guidelines.freee.co.jp/intro/intro.html)ではWCAG 2.1を基にプロダクト向けの整理を加えている。WCAG 2.2の基準別判定には、そのまま企業独自の推奨・優先度を使わず、原典との対応を確認する。各基準のTestsにはW3Cの関連資料を割り当て、freeeの一覧は具体的な実施方法を調べる追加資料として使う。

## スキルの設計

- [Google Chrome Modern Web Guidance](https://github.com/GoogleChrome/modern-web-guidance/blob/main/skills/modern-web-guidance/SKILL.md)：必要なガイドを取得し、作業後に照合する構成。
- [pstack create-verification-skill](https://github.com/cursor/plugins/blob/main/pstack/skills/create-verification-skill/SKILL.md)：アプリの起動・到達・操作・証拠取得の方法をプロジェクトから調べ、手順自体を実行して確かめる構成。
- [pstack maintain-verification-skill](https://github.com/cursor/plugins/blob/main/pstack/skills/maintain-verification-skill/SKILL.md)：説明の古さ、操作ツールの不足、製品の問題を区別する考え方。
- [ACT Rules Format](https://www.w3.org/TR/act-rules-format/)と[ACT Rules](https://www.w3.org/WAI/standards-guidelines/act/rules/)：適用条件、期待結果、具体例、検査で分かる範囲の明示。独自書式はACT準拠を宣言するものではない。
- [WCAG-EM](https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/)：評価範囲、一連の利用、評価と報告の整理。

参照元スキルのツール権限や外部への書き込み指示は引き継いでいない。

## 自動検査エンジン

[Guidepup](https://www.guidepup.dev/docs/getting-started) 0.40.0を、実スクリーンリーダーの操作・発話取得のアダプターで使用する。公式の対応表、インストールしたmanifest、capture API、発話ログ、Virtual Screen Readerとの違いを確認した。Linux 6.18の開発環境は当該版のOrcaアセット条件に一致せず、実読み上げのGuidepup試験は未実施。単体試験と非対応環境での判定の試験を、実スクリーンリーダーでの試験と区別する。

収集器は[Deque axe-core](https://github.com/dequelabs/axe-core) 4.11.0を同梱して使用する。[vendor/axe.min.js](../vendor/axe.min.js)と[MPL 2.0ライセンス](../vendor/axe-LICENSE.txt)を保持する。エンジン自体を変更していない。検出は不適合の候補、incompleteは追加判断が必要な結果として扱い、passesを基準全体の適合へ変換しない。

音声認識の調査では[Whisper.cpp](https://github.com/ggml-org/whisper.cpp) v1.9.5と[公式配布のモデル](https://huggingface.co/ggerganov/whisper.cpp)を使用した。[校正の記録](../validation/media/asr/README.md)に固定コミット・モデルのハッシュ・実出力・エンジンのMITライセンスを保存した。モデルやbuild用パッケージは同梱せず、認識結果を音声の正解又はWCAGの自動判定とはしていない。

## 更新

資料の更新時は、参照元・版・ハッシュを記録し、検査定義を再生成して確認する。旧実行の定義と異なる場合は、新しい実行先で評価する。W3Cの正誤表と最新の公開版も確認する。

```sh
python3 scripts/build_catalog.py
python3 scripts/build_act_index.py
```

ACTの索引生成では、保存した原文のハッシュ、ルールのID・状態、複合ルールの参照先、選択した版の具体例と期待値を照合する。原典を更新せずに状態や期待値だけを都合よく変更しない。
