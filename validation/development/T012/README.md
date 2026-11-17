# T012：現在の環境での実Orca確認

起点はT007提案版081d18f。Debian 13、Linux 6.18.57、Orca 48.1（Debian 48.1-1+deb13u2）、Chromium 156.0.8078.79。Guidepupを経由しないnativeアダプター。AI推論なし。main未採用の評価記録。

setup-001/before.jsonで不足を確認し、prepare.pyで既存manifestの31配布物を取得・SHA-256照合してworkspace内へ展開した。OS本体へインストールしていない。downloads.jsonに取得元・版・ハッシュがある。実行rootは外部成果物で、再現時は新しいrootへ同じ配布物を用意する。

contrast-001は既存の4.1.3 workerで、正常対照と通知属性のない対照を実行した。どちらもcant_tell。正常例ではボタン名を取得したが通知を取得せず、もう一方ではボタン名も観察窓で取得できなかった。画面では両方の通知が表示された。strict終了2。

contrast-002は一時的にworkerの2入力をnative XTestへ変更した別run。操作の画面変化と実キーのエコーは取得できたが、選択2件は引き続きcant_tell。変更したworker原文はrun.zip内のproducersとimplementationに保存されている。改善を実証できなかったため、この製品変更は採用していない。既存のworkerと期待判定・HTMLは保持する。

diagnostic-001は既存のlive-region-variants.htmlの独立した診断。5つのボタンへTab、Spaceの計10入力を行い、全ボタンの名前とフォーカス、各表示更新を確認した。明示polite、非atomic status、明示atomicの3通知は発話を取得した。暗黙atomic statusと属性なし対照は通知発話を取得しなかった。環境全体の無発話と、実装・環境の組合せによる通知の違いを区別できた。原始ログ、画像、シナリオ、取得ページはdiagnostic-001.zipに保存し、小さい観察記録も展開している。

これはOrcaが音声合成器へ渡した発話のログで、音声の録音・聴取ではない。出力先ALSA null。画面の文字を発話したとみなしたり、暗黙roleの正常例を不適合に変更したりしていない。選択問題集の通知判定能力は未達。別の対応ブラウザー・支援技術の組合せ又は互換性の改善が必要で、T014の全実SR確認を満たさない。

再現：prepare.pyに新しい専用rootと記録先を渡す。exercise.pyに--root、未使用の--outと--recordを渡して既存workerを実行する。diagnostic.pyにrootと新しい記録先を渡すと比較ページを実操作する。Python/Playwright、システムのGI/AT-SPI、X11/XTest、D-BusとChromium等も必要で、31パッケージだけで任意のOSが再現可能とはしない。

python-tests.txtは一時的なnative入力案での225試験、final-native-request-tests.txtは元のworkerを維持した最終状態のアダプター要求4試験。両方成功。過去の保存済み判定・正解・証拠を変更していない。
