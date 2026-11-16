# 1.4.7 の検証用ページ

採点側の資料です。検査担当にはpublic内のページと生成したタスクのみを渡します。作成者による有限の対照例で、基準全体の網羅や独立した専門家による正解確認は未実施です。

## 元の代表例・操作例

音声を聞き、背景音の停止を操作する。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c01 | [p01.html](public/p01.html) | during-playback / 1.4.7-01 / `#subject` | failed: 発話に大きな持続背景音を重ね、背景音だけを停止できない。 |
| c02 | [p02.html](public/p02.html) | during-playback / 1.4.7-01 / `#subject` | passed: 背景音を独立して停止できる。20dBの経路を正解に使わない。 |

## 音声と背景音の20dB差

音声と背景音の20dB差。操作と観察から判定し、表示だけで完了としない。

| ケース | ページ | 状態・観点・対象 | 期待結果と根拠 |
| --- | --- | --- | --- |
| c03 | [p03.html](public/p03.html) | initial / 1.4.7-02 / `#subject` | failed: 20ms区間ごとの背景音は主音声より設計値10dB低い。20dBを満たさない。 |
| c04 | [p04.html](public/p04.html) | initial / 1.4.7-02 / `#subject` | passed: 20ms区間ごとの背景音は主音声より設計値30dB低い。20dBを超える。 |

必要な追加環境・確認：audio-level-analysis

[基準の検査手順](../../../skills/wcag-audit-kit/references/criteria/1.4.7.md) / [追加パターン一覧](../../PATTERNS.md) / [素材と条件](../../MATERIALS.md)
