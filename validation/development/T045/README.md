# 公開・提出用のレポート試作

更新を終えた、または中断した保存済みrunを指定する。従来の形式と、台帳を `work/` に置く形式に対応する。出力先はrunとは別の新規ディレクトリーを使う。

```sh
report_preview=$(mktemp -d)
python3 validation/development/T045/render.py \
  --run validation/full-fixture/bad-run \
  --out "$report_preview/reports" \
  --title '保存済み試験のレポート案'
```

`index.html` からサイト概要、`page-*.html` の各ページの達成状況、`acr.html` のACR検討版を開ける。HTMLから根拠をたどるには、生成時の出力先と元runの相対位置を保つ。検査方法や報告日などは `--help` にある引数で指定できる。入力のない項目は「未記録」と出す。

`--pdf` を加えると `acr.pdf` も生成する。PlaywrightとChromiumが必要。Playwrightのブラウザーを使う場合は `python3 -m playwright install chromium` で準備する。インストール済みのChromeやChromiumを使う場合は `--chromium` に実行ファイルを指定する。

## 照合した結果

| 入力 | 出力で確認した内容 |
| --- | --- |
| 既存のローカル試験の正常例・問題例 | 対象範囲の適合と不適合、問題例の未実施を表示 |
| 開始画面と確認画面の合成台帳 | 開始画面は範囲の結論が未確認。確認画面で確定した2.4.2の不適合と、他の基準の未実施をサイト概要と詳細で追跡 |
| 機械検査で指摘のある合成台帳 | 対象範囲と基準は未確認。保存済みの検査票で確定した不適合は0件 |

```sh
python3 -m unittest discover -s tests -p 'test_report_prototypes.py' -v
python3 -m unittest discover -s tests -p 'test_scope_conformance.py' -v
python3 scripts/sync_skills.py --check
```

合成台帳のHTMLをChromiumで幅320pxと1280pxで表示し、サイト概要からページ別達成状況とACRを開いた。PDFは全8ページを画像へ変換し、日本語、表の見出し、改ページを目視で確認した。テキストを抽出して、達成基準番号、判定、観察結果が読めることも確認した。

Pythonの全338試験は326件成功、12件スキップ。macOSでは一時ディレクトリーの表記を `/private/tmp/` 以下にそろえて実行した。正式なACRの判定語・提出要件と、PDFの支援技術での操作は[T045](../../../docs/tasks/T045-report-prototypes.md)に引き継ぐ。
