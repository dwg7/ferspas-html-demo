# ferspas-html-demo

FAO FERSPASのSTAC/地理空間アセットを、プログラミング環境を持たない公務利用者がブラウザだけで利用できる形へ変換する探索。設計判断の背景は[CLAUDE.md](CLAUDE.md)を参照。

## 公開ページ

`docs/`以下がGitHub Pagesで公開される。各Caseは`docs/<Case名>/`というディレクトリにまとめ、ページ本体・task定義の公開コピー・派生データを同じ場所に置く（散らからないようにするための構成）。

- [docs/Case1-ASIS-latest-Italy/](docs/Case1-ASIS-latest-Italy/) — Case 1 (ASIS latest agricultural stress index, Italy)。Phase 3、実装済み
- [docs/Case2-GHG-BDG/](docs/Case2-GHG-BDG/) — Case 2 (Drained cropland area time series, Bangladesh)。Phase 1、実装済み
- [docs/Case2-GHG-4-14-5/](docs/Case2-GHG-4-14-5/) — Case 2の第二のAOI版（slippy-map tile 4-14-5、地名不使用）。Phase 2、実装済み
- [docs/Discover-4-14-5/](docs/Discover-4-14-5/) — Yuiseki GeoParquet indexによる横断発見の実験

各Caseディレクトリは共通して次を持つ:

  - `index.html` — ページ本体（共通デザインは`docs/assets/style.css`）
  - `task.yaml` — task定義の公開コピー
  - `derived/` — 発行時にチェックアウトした派生データ（ある場合）

ディレクトリ名は参照元Notebookのファイル名に対応させる（例: `Case2-GHG-BDG.ipynb` → `docs/Case2-GHG-BDG/`）。中のデータファイル名は正しい国コード（`BGD`等）を使う（CLAUDE.md 6章）。独自AOIには地名ではなく空間ID（CLAUDE.md 4.9章）を使う。

## Task YAMLの正本と公開物

各ページのtask定義は`tasks/*.yaml`が正本。GitHub Pagesは`docs/`以下しか配信しないため、`docs/<Case名>/task.yaml`に同内容のコピーを置き、公開ページはそちらをfetchする。正本を変更したら公開コピー側も同期すること。

## 内部文書

- [docs-internal/findings.md](docs-internal/findings.md) — 検証済みの事実
- [docs-internal/decisions.md](docs-internal/decisions.md) — 設計判断の記録
