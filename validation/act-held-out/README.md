# 期待値を伏せたACT公開例との比較

承認済みの97a4e1「Button has non-empty accessible name」と23a2a8「Image has non-empty accessible name」から、各結果2例ずつ計12例を固定seedで選んだ。モデルには公開期待値を表示せず、先に適用条件・期待結果と実DOM/AXを観察して[predictions.json](predictions.json)へ判定を記録し、その後に正解を開いて比較した。

[結果](score.json)は12/12一致、通過・不適合・適用対象外が各4例。これはこの2ルールの限定した比較であり、WCAG基準全体や任意のサイトへの精度、専門家相当のサイト監査を保証する数値ではない。

空のaltによる装飾画像、focusableな画像でrole=noneが実際にはimageとして露出する例、disabled buttonのpresentation、buttonルールから除外されるinput type=imageを区別した。属性の文字列やAX内のimage/buttonだけを数えて適用性を決めていない。

元の選択索引はW3Cリポジトリcommit `9a2d7f903357eb728a0f83f00db75d4f32417ab4`の版。取得した原HTML、静的資源、URL、SHA-256、実画面とAX、判定理由を保存した。公開期待値は[sealed-key.json](sealed-key.json)、判定後に照合したデータは[score.json](score.json)。

- 判定前の正解ファイルSHA-256：`c5df226fba3cf972c8c697fcde24e0e777cd78765bf102cc21d24932def01527`
- 正解を開く前の予測ファイルSHA-256：`e8b94c56da67ce64cdadc6be9055fdbabef23ae32a923f0f580261d367ac5fda`

最初のChromiumの直接接続は環境の証明書で失敗したため、[失敗記録](first-transport-blocked.json)を残した。次の観察ではTLSを検証した取得済みHTML・資源をバイト変更なしにブラウザーへ供給した。ブラウザーの証明書エラーを無視する設定は使っていない。これは意味・名前・適用性の試験であり、接続のセキュリティの試験ではない。

[実観察](review-observations.json)、[実画像・DOM・AX](observations-cache-002/)、[取得・供給の記録](transport.json)、[原資源のキャッシュ](cached-resources.json)を参照する。原典の権利は[W3C ACTのライセンス](../../references/sources/act/LICENSE.md)に従う。
