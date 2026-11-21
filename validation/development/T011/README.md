# グラフの値と、開いた代替情報の値を照合した

同じ画像を持つ2ページを公開し、検査役にURLと先行の機械検査だけを渡した。Codexの別エージェントは図を画像として観察し、3か月の訪問回数と減少傾向を記録してから、詳細の表を開いた。画像取得、読み取りの記録、表を開く操作、応答の順に保存した。期待値は公開ページの対照を作るときに決め、採点資料への転記は観察終了後に行った。[画像の読み取り](run-chart-001/visual-reading.md) · [操作ログ](run-chart-001/observations.json) · [検査役の応答原文](run-chart-001/response.txt) · [採点資料](run-chart-001/oracle.json)

| 例 | 図の4・5・6月 | 表の4・5・6月 | 図の代替情報 | 装飾 | 1.1.1の帳票 |
| --- | --- | --- | --- | --- | --- |
| k4 | 92・61・44 | 92・79・44 | 不適合 | 通過 | 不適合 |
| m7 | 92・61・44 | 92・61・44 | 通過 | 通過 | 未確認 |

図の単位は訪問回数。代替文は4月から6月の減少と表の位置を伝える。どちらもTabで「Show data table」に移動し、Enterで表を開いた。開閉部品のひし形には空の `alt` があり、部品のアクセシブルな名前と展開状態はそのまま取得できた。機械のaxe `image-alt` は両例で通過した。[展開画面 k4](run-chart-001/k4-details-open.png) · [展開画面 m7](run-chart-001/m7-details-open.png) · [公開アクセシビリティツリー k4](run-chart-001/k4-details-open.ax.json) · [公開アクセシビリティツリー m7](run-chart-001/m7-details-open.ax.json)

測定はChromium 156.0.8078.79、1280×900 CSS px。画像取得から応答保存まで約91秒だった。このホストでは検査役のモデル識別子、トークン数、費用を取得できなかった。発話と他の表示幅は未確認。

## 再実行

Chromiumを使用できるリポジトリの実行環境で、別の端末にfixtureを配信する。

```sh
python3 -m http.server 43828 --bind 127.0.0.1 --directory validation/development/T011/fixture
```

新しい出力先を作って収集する。保存済みの独立観察を添付するには、URLと表示幅に加え、初期画像のハッシュも一致する必要がある。描画環境を変えた場合は、その環境で独立観察を取り直す。

保存した元runから試す場合は、ZIPを新しいディレクトリーに展開し、`k4` と `m7` がある場所を `--source` へ渡す。[元の機械run 194ファイル](run-chart-001/machine-runs.zip)

```sh
audit=skills/wcag-audit-kit/scripts/audit.py
source_runs=$(mktemp -d)
for example in k4 m7; do
  url=http://127.0.0.1:43828/$example/
  python3 "$audit" page-audit --url "$url" --out "$source_runs/$example" \
    --mode ai --level AA --screenshots states --max-images 4 --initial-only
  python3 "$audit" page-audit --url "$url" --out "$source_runs/$example" \
    --resume --quick-explore
done
python3 validation/development/T011/record-figure-observations.py \
  --cli "$audit" --source "$source_runs" --out "$source_runs-reports" \
  --evidence validation/development/T011/run-chart-001
```

確認スクリプトは、画像の読み取り記録と期待値、表の値、信頼できるキーイベントの順序、収集時のURLと表示幅を照合する。元runからコピーした検査票に `attach` と `record` で結果を登録し、`page-report` でHTML・JSON・Excelを出す。原本は各例で97ファイルすべてが同じハッシュだった。新しい収集では帳票に含まれる時刻やパスによってハッシュが変わる。原文中の先行検査へのリンクは、観察時の作業ディレクトリーを示す。[画像の取得条件](run-chart-001/image-captures.json) · [検査票への反映記録](run-chart-001/receipts.json)

観察を取り直すときは、図から読んだ内容を記録してから操作し、期待値を見る前に代替文と表の一致を判断する。手順の背景はT011で扱う。[T011](../../../docs/tasks/T011-ai-residual-review.md)
