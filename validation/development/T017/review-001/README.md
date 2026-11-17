# PR #22：操作後の観察窓の起点

2026-11-18。ページが既に静かな場合、前のidle時間で操作後の静かな期間が満たされる不備を修正した。lastChangeと今回のstartの遅い方から150msを測る。

HTTP応答50ms後にDOMへ結果を描く所有ページで、旧実装は待機0ms・rendered=falseと再現した。修正後は新しい観察窓を待ってrendered=trueだった。[前](before-network.json)／[後](after-network.json)。これを全ネットワークの完了保証へ広げない。

コールバック引数・this・取消・継続タイマーの[契約](timer-contract.json)、[650ms画像](after-650.json)、Python209試験を確認した。元のT017の試行は変更していない。T009のsubmit/image入力のレビュー修正も提案ブランチから取り込んだ。
