# ferspas-html-demo

FAO FERSPASのSTAC/地理空間アセットを、プログラミング環境を持たない公務利用者がブラウザだけで利用できる形へ変換する探索。設計判断の背景は[CLAUDE.md](CLAUDE.md)を参照。

## 公開ページ

`docs/`以下がGitHub Pagesで公開される。

- [docs/Case2-GHG-BDG.html](docs/Case2-GHG-BDG.html) — Case 2 (Drained cropland area time series, Bangladesh)。Phase 1、実装中

## Task YAMLの正本と公開物

各ページのtask定義は`tasks/*.yaml`が正本。GitHub Pagesは`docs/`以下しか配信しないため、`docs/tasks/`に同内容のコピーを置き、公開ページはそちらをfetchする。正本を変更したら`docs/tasks/`側も同期すること。

## 内部文書

- [docs-internal/findings.md](docs-internal/findings.md) — 検証済みの事実
- [docs-internal/decisions.md](docs-internal/decisions.md) — 設計判断の記録
