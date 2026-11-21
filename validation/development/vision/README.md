# VISIONの統合検証

同じ作業ブランチにURL探索、実操作、範囲の結論と帳票、点検、複数ページの修正前後比較を取り込んだ。対照は各試験の記録にあり、対象のURL・状態・達成基準・実行環境を確認できる。PRの採用状況は各リンクから確認できる。[VISION](../../../docs/VISION.md) · [統合版のADR](../../../docs/adr/0108-run-vision-acceptance-on-an-integrated-revision.md)

| VISIONの項目 | 確認したこと | 根拠 |
| --- | --- | --- |
| 起点URLからページと手続きを見つける | 予約の2例で入口から操作し、追加操作で見つけた確認URLも機械検査に戻した。選んだ6観点を照合した | [T022](../T022/README.md) · [PR #88](https://github.com/k-s-h-r/wcag-audit-kit/pull/88) |
| キー操作で何が起きたかを確かめる | 数量変更ではクリックとEnter・Spaceの結果を2幅で比較した。開く・本文を通る・戻って閉じる経路と、操作後の全体再検査との一致も確認した | [T024](../T024/README.md) · [T018](../T018/README.md) · [T019](../T019/README.md) |
| 適合の結論と二つの成果物 | 事前に固定した適合・不適合・未確認を検査票と不適合一覧に照合した。予約の問題例では一覧から該当ページ・状態・操作と証拠をたどれた | [T021](../T021/README.md) · [T022](../T022/README.md) · [PR #86](https://github.com/k-s-h-r/wcag-audit-kit/pull/86) |
| 改善に使う点検 | 予約の増員と確認ボタン名を調べ、改善後に同じ出発点から確認へ進む操作を比較した。点検は保存済みの証拠とURLの2通りから依頼できた | [T023](../T023/README.md) · [T027](../T027/README.md) · [独立観察の記録](run-001/t027-independent.zip) |
| AIによる図の確認と、根拠不足を埋める追加操作 | 機械の代替文の検査が通った2例で、別のAIが先に図を読み、キーで開いた表と照合した。問題例は5月の値が異なり、通常の報告に不適合を記録した | [T011](../T011/README.md) · [PR #95](https://github.com/k-s-h-r/wcag-audit-kit/pull/95) |
| 字幕・書き起こし・音声解説 | 実再生の字幕3件、画面の保存完了を伝える書き起こし2件、同じ映像の音声解説2件を照合した。対象の文・表示時刻・画面の事実から7件を区別した | [T028](../T028/README.md) · [PR #96](https://github.com/k-s-h-r/wcag-audit-kit/pull/96) |
| 入力エラーからの回復と実スクリーンリーダー | 実キーで両例の同じエラー画面に到達し、修正して確認へ進んだ。発生時の発話がOrca 48.1で異なることを確認し、4.1.3の証拠を帳票に添付した | [T026](../T026/README.md) · [PR #94](https://github.com/k-s-h-r/wcag-audit-kit/pull/94) |
| 修正前後と影響ページを照合 | 同じリンクがある6ページで解消・新規・継続を各1件、証拠を確認できないページを3件表示した。通常の `page-audit` からも、同じ転送後のページでコントラストの改善を2幅で照合した | [T025](../T025/README.md) · [PR #93](https://github.com/k-s-h-r/wcag-audit-kit/pull/93) |

## 同じ版で再実行した検査

Debian、Python 3.12.14、Playwright 1.62.0、Chromium 156.0.8078.79を使用した。実Orcaの試験は、操作・発話の原本を読み、帳票を統合版で再生成した。

単体テスト324件と配布スキルの同期確認が通った。ブラウザーで数量変更3例と開閉6例を2幅で再測定し、操作後の再検査は4種類×2幅で全体検査と一致した。別エージェントも、同じEnterの操作に開閉と数量変化の両方の根拠が付くことを確かめた。手続きの帳票4件では、HTML・JSON・Excelと不適合一覧から32件の証拠を確認した。[統合runの結果とハッシュ](run-001/summary.json)

```sh
python3 scripts/sync_skills.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/keyboard_function_browser.py --out /tmp/vision-key-functions
python3 tests/accordion_keyboard_browser.py --out /tmp/vision-accordion
python3 tests/operation_impact_browser.py --out /tmp/vision-operation-impact
python3 validation/development/T025/verify.py --out /tmp/vision-compare
python3 validation/development/T025/verify.py --page-audit --out /tmp/vision-page-compare
```

同じ手続きの帳票の再生成は、T022とT026の再実行手順を用いる。図の試験は公開済みの機械runを展開すると、同じ初期画像・観察・判定を通常のCLIで照合できる。[T022の再実行](../T022/README.md#再実行) · [T026の再実行](../T026/README.md#再実行) · [T011の再実行](../T011/README.md#再実行)

試験ごとに範囲は異なる。予約の業務は確認画面まで。対象サイト全体の適合を示すには帳票に残った確認が必要で、他の支援技術やサイトで同じ結果になるかは個別に調べる。
