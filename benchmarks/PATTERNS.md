# 追加パターンの一覧

61組の追加パターンです。各ページの状態・期待結果・必要環境はsuite.jsonへ記録しています。元の代表例と3階層メニューも保持しています。

問題なしの対照も含め、適合の結論は記載した観点と条件に限ります。手話の意味は公開元の説明、音声は既知の生成元を根拠にしており、独立した専門家の確認は未実施です。仮想時計・合成センサー・文字サイズ上書きの試験を、実時間・実端末・ネイティブのズームの確認へ置き換えません。

| パターン | 基準 | ケースとページ | 必要な追加環境 |
| --- | --- | --- | --- |
| 背景画像・SVG・canvasの代替 | 1.1.1 | [c05: p05.html](cases/1.1.1/public/p05.html) / [c06: p06.html](cases/1.1.1/public/p06.html) / [c11: p11.html](cases/1.1.1/public/p11.html) | 通常のブラウザー |
| 代替説明が実SRに届くか | 1.1.1 | [c07: p07.html](cases/1.1.1/public/p07.html) / [c08: p08.html](cases/1.1.1/public/p08.html) | real-screen-reader |
| 操作後に追加される画像 | 1.1.1 | [c09: p09.html](cases/1.1.1/public/p09.html) / [c10: p10.html](cases/1.1.1/public/p10.html) | 通常のブラウザー |
| メディア代替の意味と順序 | 1.2.1 | [c03: p03.html](cases/1.2.1/public/p03.html) / [c04: p04.html](cases/1.2.1/public/p04.html) | audio-content-comparison |
| 字幕の意味・同期・音情報 | 1.2.2 | [c03: p03.html](cases/1.2.2/public/p03.html) / [c04: p04.html](cases/1.2.2/public/p04.html) / [c05: p05.html](cases/1.2.2/public/p05.html) | audio-content-comparison |
| メディア代替の意味と順序 | 1.2.3 | [c03: p03.html](cases/1.2.3/public/p03.html) / [c04: p04.html](cases/1.2.3/public/p04.html) | audio-content-comparison |
| ライブの音情報と文字代替 | 1.2.4 | [c03: p03.html](cases/1.2.4/public/p03.html) / [c04: p04.html](cases/1.2.4/public/p04.html) | audio-content-comparison |
| 音声解説の選択が実メディアを変えるか | 1.2.5 | [c03: p03.html](cases/1.2.5/public/p03.html) / [c04: p04.html](cases/1.2.5/public/p04.html) | 通常のブラウザー |
| 音声解説が重要な映像情報と合うか | 1.2.5 | [c05: p05.html](cases/1.2.5/public/p05.html) / [c06: p06.html](cases/1.2.5/public/p06.html) | audio-content-comparison |
| 実際の手話素材と発話の意味 | 1.2.6 | [c03: p03.html](cases/1.2.6/public/p03.html) / [c04: p04.html](cases/1.2.6/public/p04.html) | qualified-sign-language-comparison |
| 拡張解説の内容と映像の停止・再開 | 1.2.7 | [c03: p03.html](cases/1.2.7/public/p03.html) / [c04: p04.html](cases/1.2.7/public/p04.html) | audio-content-comparison |
| メディア代替の意味と順序 | 1.2.8 | [c03: p03.html](cases/1.2.8/public/p03.html) / [c04: p04.html](cases/1.2.8/public/p04.html) | audio-content-comparison |
| ライブの音情報と文字代替 | 1.2.9 | [c03: p03.html](cases/1.2.9/public/p03.html) / [c04: p04.html](cases/1.2.9/public/p04.html) | audio-content-comparison |
| 見た目の表とプログラムの関係 | 1.3.1 | [c03: p03.html](cases/1.3.1/public/p03.html) / [c04: p04.html](cases/1.3.1/public/p04.html) | 通常のブラウザー |
| 実SRで表の関係を使えるか | 1.3.1 | [c05: p05.html](cases/1.3.1/public/p05.html) / [c06: p06.html](cases/1.3.1/public/p06.html) | real-screen-reader |
| ラジオグループの質問と選択肢 | 1.3.1 | [c07: p07.html](cases/1.3.1/public/p07.html) / [c08: p08.html](cases/1.3.1/public/p08.html) | 通常のブラウザー |
| 表示と読み順の取得 | 1.3.2 | [c03: p03.html](cases/1.3.2/public/p03.html) / [c04: p04.html](cases/1.3.2/public/p04.html) | 通常のブラウザー |
| 実端末の向き情報による利用制限 | 1.3.4 | [c03: p03.html](cases/1.3.4/public/p03.html) / [c04: p04.html](cases/1.3.4/public/p04.html) | orientation-permission, physical-device-orientation |
| 入力目的属性と実際の質問 | 1.3.5 | [c03: p03.html](cases/1.3.5/public/p03.html) / [c04: p04.html](cases/1.3.5/public/p04.html) | 通常のブラウザー |
| 操作後のエラー表示を取得する | 1.4.1 | [c03: p03.html](cases/1.4.1/public/p03.html) / [c04: p04.html](cases/1.4.1/public/p04.html) | 通常のブラウザー |
| axeで判定できる通常文字の対照 | 1.4.3 | [c03: p03.html](cases/1.4.3/public/p03.html) / [c04: p04.html](cases/1.4.3/public/p04.html) | 通常のブラウザー |
| 無効から有効へ変わる部品のコントラスト | 1.4.3 | [c05: p05.html](cases/1.4.3/public/p05.html) / [c06: p06.html](cases/1.4.3/public/p06.html) / [c07: p07.html](cases/1.4.3/public/p07.html) | 通常のブラウザー |
| 拡大前後の取得と内容欠落 | 1.4.4 | [c03: p03.html](cases/1.4.4/public/p03.html) / [c04: p04.html](cases/1.4.4/public/p04.html) | native-browser-zoom-for-final-audit |
| 背景の文字画像と通常テキスト | 1.4.5 | [c03: p03.html](cases/1.4.5/public/p03.html) / [c04: p04.html](cases/1.4.5/public/p04.html) | 通常のブラウザー |
| 音声と背景音の20dB差 | 1.4.7 | [c03: p03.html](cases/1.4.7/public/p03.html) / [c04: p04.html](cases/1.4.7/public/p04.html) | audio-level-analysis |
| 色・幅・揃え・間隔の調整 | 1.4.8 | [c03: p03.html](cases/1.4.8/public/p03.html) / [c04: p04.html](cases/1.4.8/public/p04.html) | 通常のブラウザー |
| 狭い画面の取得と横スクロール | 1.4.10 | [c03: p03.html](cases/1.4.10/public/p03.html) / [c04: p04.html](cases/1.4.10/public/p04.html) | 通常のブラウザー |
| ホバーとフォーカスで出る内容 | 1.4.13 | [c03: p03.html](cases/1.4.13/public/p03.html) / [c04: p04.html](cases/1.4.13/public/p04.html) | 通常のブラウザー |
| Shadow DOM内の操作と状態 | 2.1.1 | [c06: p06.html](cases/2.1.1/public/p06.html) / [c07: p07.html](cases/2.1.1/public/p07.html) | 通常のブラウザー |
| タブのフォーカス・選択・パネル | 2.1.1 | [c08: p08.html](cases/2.1.1/public/p08.html) / [c09: p09.html](cases/2.1.1/public/p09.html) | 通常のブラウザー |
| 実際の階層内のフォーカス経路 | 2.1.2 | [c05: p05.html](cases/2.1.2/public/p05.html) / [c06: p06.html](cases/2.1.2/public/p06.html) | 通常のブラウザー |
| 入れ子のダイアログの離脱と復帰 | 2.1.2 | [c07: p07.html](cases/2.1.2/public/p07.html) / [c08: p08.html](cases/2.1.2/public/p08.html) | 通常のブラウザー |
| コンボボックスのポップアップ | 2.1.2 | [c09: p09.html](cases/2.1.2/public/p09.html) / [c10: p10.html](cases/2.1.2/public/p10.html) | 通常のブラウザー |
| iframe内の移動と離脱 | 2.1.2 | [c11: p11.html](cases/2.1.2/public/p11.html) / [c12: p12.html](cases/2.1.2/public/p12.html) | same-origin-frame |
| 警告からの延長と繰返し回数 | 2.2.1 | [c03: p03.html](cases/2.2.1/public/p03.html) / [c04: p04.html](cases/2.2.1/public/p04.html) | wall-clock-timing-for-final-audit |
| 告知の代わりに20時間超保持する経路 | 2.2.6 | [c03: p03.html](cases/2.2.6/public/p03.html) / [c04: p04.html](cases/2.2.6/public/p04.html) | real-time-storage-retention |
| 閃光の区間と資料の欠落 | 2.3.1 | [c03: p03.html](cases/2.3.1/public/p03.html) / [c04: p04.html](cases/2.3.1/public/p04.html) | flash-analysis-without-unsafe-preview |
| 実際の階層内のフォーカス経路 | 2.4.3 | [c05: p05.html](cases/2.4.3/public/p05.html) / [c06: p06.html](cases/2.4.3/public/p06.html) | 通常のブラウザー |
| 入れ子のダイアログの離脱と復帰 | 2.4.3 | [c07: p07.html](cases/2.4.3/public/p07.html) / [c08: p08.html](cases/2.4.3/public/p08.html) | 通常のブラウザー |
| ダイアログを閉じるボタンと次のTab | 2.4.3 | [c09: p09.html](cases/2.4.3/public/p09.html) / [c10: p10.html](cases/2.4.3/public/p10.html) | 通常のブラウザー |
| フォーカス前後の取得 | 2.4.7 | [c03: p03.html](cases/2.4.7/public/p03.html) / [c04: p04.html](cases/2.4.7/public/p04.html) | 通常のブラウザー |
| 狭い画面で隠れたメニューへのフォーカス | 2.4.7 | [c05: p05.html](cases/2.4.7/public/p05.html) / [c06: p06.html](cases/2.4.7/public/p06.html) | 通常のブラウザー |
| 表示後のバナーによる隠れ | 2.4.11 | [c03: p03.html](cases/2.4.11/public/p03.html) / [c04: p04.html](cases/2.4.11/public/p04.html) | 通常のブラウザー |
| 表示後のバナーによる隠れ | 2.4.12 | [c03: p03.html](cases/2.4.12/public/p03.html) / [c04: p04.html](cases/2.4.12/public/p04.html) | 通常のブラウザー |
| 表示文字とアクセシブル名の取得 | 2.5.3 | [c03: p03.html](cases/2.5.3/public/p03.html) / [c04: p04.html](cases/2.5.3/public/p04.html) | 通常のブラウザー |
| 実端末の動きとUI代替 | 2.5.4 | [c03: p03.html](cases/2.5.4/public/p03.html) / [c04: p04.html](cases/2.5.4/public/p04.html) | physical-device-motion, sensor-permission |
| サイズと間隔の取得 | 2.5.8 | [c03: p03.html](cases/2.5.8/public/p03.html) / [c04: p04.html](cases/2.5.8/public/p04.html) / [c05: p05.html](cases/2.5.8/public/p05.html) | 通常のブラウザー |
| 指定言語と本文の主たる言語 | 3.1.1 | [c03: p03.html](cases/3.1.1/public/p03.html) / [c04: p04.html](cases/3.1.1/public/p04.html) | 通常のブラウザー |
| 部分言語の取得と意味の判定 | 3.1.2 | [c03: p03.html](cases/3.1.2/public/p03.html) / [c04: p04.html](cases/3.1.2/public/p04.html) | 通常のブラウザー |
| 専門的な文章の補足 | 3.1.5 | [c03: p03.html](cases/3.1.5/public/p03.html) / [c04: p04.html](cases/3.1.5/public/p04.html) | reading-level-review |
| フォーカス時のURLと文脈 | 3.2.1 | [c03: p03.html](cases/3.2.1/public/p03.html) / [c04: p04.html](cases/3.2.1/public/p04.html) | 通常のブラウザー |
| 表示ラベルとアクセシブル名を別々に取得 | 3.3.2 | [c03: p03.html](cases/3.3.2/public/p03.html) / [c04: p04.html](cases/3.3.2/public/p04.html) | 通常のブラウザー |
| 認知機能テストの代替経路 | 3.3.8 | [c03: p03.html](cases/3.3.8/public/p03.html) / [c04: p04.html](cases/3.3.8/public/p04.html) | 通常のブラウザー |
| AAとAAAで異なる物体認識の例外 | 3.3.8 | [c05: p05.html](cases/3.3.8/public/p05.html) | 通常のブラウザー |
| 認知機能テストの代替経路 | 3.3.9 | [c03: p03.html](cases/3.3.9/public/p03.html) / [c04: p04.html](cases/3.3.9/public/p04.html) | 通常のブラウザー |
| AAとAAAで異なる物体認識の例外 | 3.3.9 | [c05: p05.html](cases/3.3.9/public/p05.html) | 通常のブラウザー |
| 独自部品の状態変更 | 4.1.2 | [c03: p03.html](cases/4.1.2/public/p03.html) / [c04: p04.html](cases/4.1.2/public/p04.html) | 通常のブラウザー |
| Shadow DOM内の操作と状態 | 4.1.2 | [c05: p05.html](cases/4.1.2/public/p05.html) / [c06: p06.html](cases/4.1.2/public/p06.html) | 通常のブラウザー |
| コンボボックスのポップアップ | 4.1.2 | [c07: p07.html](cases/4.1.2/public/p07.html) / [c08: p08.html](cases/4.1.2/public/p08.html) | 通常のブラウザー |
| タブのフォーカス・選択・パネル | 4.1.2 | [c09: p09.html](cases/4.1.2/public/p09.html) / [c10: p10.html](cases/4.1.2/public/p10.html) | 通常のブラウザー |
| 非同期の状態変化を取得する | 4.1.3 | [c03: p03.html](cases/4.1.3/public/p03.html) / [c04: p04.html](cases/4.1.3/public/p04.html) | real-screen-reader |
