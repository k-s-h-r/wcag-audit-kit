# 3階層のグローバルメニューを試す

第1階層の「製品」を開き、第2階層の「業務支援」を開くと、第3階層のリンク「見積管理」「契約管理」が現れます。開く操作2回とリンクの実行1回で、3階層目の目的ページへ進む構成です。

| 確認すること | 正常な対照 | 問題例 | 問題の内容 |
| --- | --- | --- | --- |
| 2.1.1：階層を開いてリンク先へ進む | [p04.html](cases/2.1.1/public/p04.html) | [p05.html](cases/2.1.1/public/p05.html) | 第2階層の開閉部品がクリック専用。Enter・Spaceでは開かず、ポインターなら進める |
| 2.1.2：深い階層から抜ける | [p03.html](cases/2.1.2/public/p03.html) | [p04.html](cases/2.1.2/public/p04.html) | 第3階層でTab・Shift+Tabが循環し、Escape・Enter・Spaceでも離脱できない。閉じるボタンはポインターだけで利用できる |
| 2.4.3：展開後の移動順を保つ | [p03.html](cases/2.4.3/public/p03.html) | [p04.html](cases/2.4.3/public/p04.html) | 第3階層を開いた直後、メニューを飛び越えて本文の「資料請求」へフォーカスが飛ぶ |

## ブラウザーで開く

例えば2.1.1のディレクトリを公開します。

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory benchmarks/cases/2.1.1/public
```

http://127.0.0.1:8000/p04.htmlが正常な対照、p05.htmlが問題例です。他の基準を見る場合はdirectoryを2.1.2又は2.4.3のpublicに変更します。画像やスクリプト等はそれぞれのpublic内で完結し、採点側のsuite.jsonは公開しません。

## 正常な対照でたどる経路

1. 初期表示からTabで「製品」へ移動し、Enterで第2階層を開く。
2. Tabで「業務支援」へ移動し、Enterで第3階層を開く。
3. Tabで「見積管理」、さらにTabで「契約管理」、Shift+Tabで「見積管理」へ戻る。
4. Escapeで第3階層を閉じ、「業務支援」へフォーカスを戻す。
5. もう一度Escapeで第2階層を閉じ、「製品」へ戻す。
6. Tabで「サポート」、次に本文の「資料請求」へ進める。Shift+Tabで戻ることも確認する。
7. 開き直して第3階層の「見積管理」でEnterを押すと、destination.htmlへ移動し、見積管理の見出しが表示される。

ネイティブボタンはSpaceでも開閉できます。ここでは通常のnavと開閉ボタンを使うため、ARIA menubarの矢印キー操作を要件にはしていません。階層数3は今回の再現条件です。

各ケースの期待結果は「階層が表示された」「対象にフォーカスが移った」「リンク先へ移動した」「親や後続操作へ戻れた」を操作経路として確認します。初期状態でTabを回すだけでは、隠れた階層は確認できません。表示されたことと、キーだけで到達できたことも分けます。

`tests/nested_navigation_browser.py`は、テスト入力を直接操作して正常例と問題例の動作を確認します。`tests/keyboard_checks_browser.py`は、同じ6ページを`page-audit`の指定経路で検査し、機械検査とページ別帳票を照合します。

```sh
python3 tests/keyboard_checks_browser.py --out /project/new-keyboard-regression
```

検査した経路は開閉、親へ戻る操作、TabとShift+Tabによる離脱、展開後のフォーカス移動、末端リンクへの到達です。任意のメニューを検査する場合は、対象と期待する状態に合わせて経路を設定します。[設定手順](../skills/wcag-audit-kit/references/page-audit.md#既知のキーボード操作を検査する)
