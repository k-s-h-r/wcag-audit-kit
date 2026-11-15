# 検証方法の失敗と修正

ここには方法の問題を調べた部分的な診断記録を保存した。対象のWCAG不適合又は完成した監査の代わりに使わない。元のURL・観察時刻を保持し、専用サイトの成功した実行へ書き換えていない。

- [YAMLの状態assert](yaml-text-as-boolean/request.yaml)：引用符のないOn/Offが真偽値となり、画面文字列と一致しなかった。[当時の収集記録](yaml-text-as-boolean/capture-manifest.json)に2状態のblockedと期待値Trueを保持した。これは方法の否定例の抜粋で、当時の全監査ディレクトリーではない。後の依頼では文字列を引用符で囲んだ。
- [スクロール完了前](scroll-before-settled/reflow-end.json)：キー操作後すぐの保存では、Home/PageDownのscrollYが0のまま、Endでも途中の122.75だった。以後は500ms待って実測し、0/196.75/243.25となることを確認した。ラベルがEndというだけで終端を見たことにしない。
- [入力経路を混ぜた読み上げ](mixed-key-input/screen-reader.json)：XTestの順次読みでは内容を取得したが、その後のPlaywrightのキー操作ではDOMの状態だけが変わり、必要な状態の発話を得られなかった。以後、当該シナリオのキーをXTestへ揃えて再確認した。DOMのactiveElementに加えてdocumentHasFocusも記録し、実際のブラウザーUIへの移動と区別するようにした。
- [サーバー接続の失敗](interrupted-server/screen-reader.json)：環境切替で試験用サーバーが終了した試行。読み上げは接続reset、向きは接続refusedとしてblockedになった。保存した既存データを確認し、自分のサーバーを再起動した後、新しい実行先で再試行した。ページの不適合には数えていない。
