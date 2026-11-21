# アコーディオンに入り、同じボタンへ戻って閉じる

URLと共通設定を指定してから、本文を開き、Tabで進み、Shift+Tabで戻って閉じる経路を確認した。変更前はこの経路を最後まで確認できなかった。変更後は1280×900・320×900 CSS pxの両方で、開閉と実際のフォーカスを同じ操作記録から確認できた。[前後の状態と入力](run-001/observations.json)

| 対照 | Enter後 | 次のTab後 | Shift+Tabで戻ったあと |
| --- | --- | --- | --- |
| 通常の本文パネル | 開いた | 本文内の `#nested` に移った | Enterで閉じ、`#accordion` にフォーカスが残った |
| テキストだけのShadow DOM | 開いた | 本文外の `#after` に移った | Enterで閉じ、Shadow DOM内の同じボタンにフォーカスが残った |
| クリックだけで開くShadow DOM | 閉じたまま | 開いた状態を確認できず | クリックで開いた証拠と、Enterが対象に届いたときの状態を別に保存した |

透明なパネルを開く例と、`display: contents` により閉じた表示を確認できない例は、両幅で判断保留になった。ナビゲーション内の公開Shadow DOMでは通常のキー入力の記録を保ち、本文の開閉としての行を生成しなかった。記録の通過は観察した開閉とフォーカスを表す。ほかのキー・代替経路・達成基準全体の判定は引き続き確認が必要。

## 試験条件

起点は `67aa42e`。Debian、Python 3.12、Playwright 1.62.0、Chromium 156.0.8078.79。ローカルHTTPで既存の3ページを配信し、機械・AA・初期表示撮影のみで検査した。上限は48ステップ、24状態、深さ4。通常の簡易探索の深さ3では、最後のキーまで確認できない。

変更前と変更後は別のrunに収集した。通常パネルは両版とも48ステップ・12状態で、上限時に残った候補は11件から12件になった。テキストだけのShadow DOMは22から26ステップに増え、状態数は4で同じだった。クリック専用例は両版とも20ステップ・4状態だった。閉じる操作は同じ試行のShift+TabとEnterの入力ログから照合した。[入力・状態・遷移の原始ファイル162件](run-001/evidence.zip)

6ケースのブラウザー試験、3階層メニューのEscapeの独立回帰、Pythonの318テスト、配布スキルの同期を確認した。

```sh
python3 tests/accordion_keyboard_browser.py --out /tmp/t018-accordion-new
python3 tests/keyboard_close_browser.py --out /tmp/t018-menu-close-new
python3 scripts/sync_skills.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
```

[ADR 0100](../../../docs/adr/0100-follow-accordion-keyboard-return.md) · [T018](../../../docs/tasks/T018-widget-operation-sequences.md)

統合版で同じ表示の対照を使い、簡易探索と通常探索のEnter・Spaceも比較した。[URLからの入力比較と原始証拠](url-operation/README.md)
