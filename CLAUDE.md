# CLAUDE.md

> Repository: `dwg7/ferspas-html-demo`  
> Status: working design document  
> Primary language: Japanese  
> Runtime principle: static web first

## 1. このリポジトリの目的

このリポジトリは、FAO Essential Remote Sensing Data Product Portal for Agrifood Systems（FERSPAS）で公開されるSTACおよび地理空間アセットを、プログラミング環境を導入できない公務利用者がブラウザだけで利用できる形へ変換する可能性を探索する。

直接の参照元は次のリポジトリである。

- https://github.com/un-fao/FERSPAS_demo

参照元のJupyter Notebookを批判または置換することが目的ではない。Notebookは、専門家がユーザーストーリーを発見し、処理方法を試し、再現可能な手順を形成するための実験環境として尊重する。

本リポジトリの役割は、Notebookで確立されたタスクを読み解き、コードを書かない利用者でも実行・観察できる透明なWebアプリケーションへ移すことである。

> **探索は専門家の環境で行い、安定したタスクはWebで共有する。**

> **Notebookで確立された再現可能な処理を、利用者が扱える透明なWebアプリケーションへ移す。**

## 2. 背景となる制度的な制約

想定する日本政府の執務環境では、利用者がPython、Jupyter Notebook、GDAL、QGIS、任意のCLI、パッケージ管理環境などを執務PCへ自由に導入できない場合がある。

この制約を、利用者の能力不足として扱わない。利用者は分析能力を持たないのではなく、プログラミング可能な実行環境を利用できない制度的条件に置かれている。

一方、一般的なWebブラウザは利用できる可能性が高い。

したがって、本リポジトリは次のラストワンマイルを扱う。

```text
専門家がNotebookで確立したタスク
    ↓
入力、判断、処理、出力、制約を明確化
    ↓
必要に応じて地域向け派生成果を発行
    ↓
完全スタティックなWebアプリケーション
    ↓
プログラミング環境を持たない公務利用者
```

## 3. 中心的な仮説

「Jupyter NotebookでやっていることをHTMLで行う」という構想は、Notebook一般をブラウザで再実装することではない。

次の条件を満たすNotebookのユーザーストーリーを、反復可能なWebタスクへ変換する。

- 入力がSTAC、公開URL、公開アセット等で特定できる
- 選択条件が説明可能である
- 処理手順が反復可能である
- 出力が地図、チャート、表、ダウンロード可能な成果等に定型化できる
- 利用者が変更するパラメーターが限定される
- 同じタスクを複数の利用者が繰り返す価値がある
- 出所、処理、制約を記録できる

本リポジトリの中心命題は次である。

> **Userが立てられなかった問いに代わって答えを作るのではなく、問いが育つ観察を作る。**

> **面白さを先に説明し切るのではなく、Userが最初の意味ある観察へ到達できるようにする。**

## 4. 最上位の設計原則

### 4.1 Web first

利用者向けCLIを先に完成させない。第一試作からWebを主役にする。

`curl`、`jq`、modern GDAL CLI、`just`は、Web上の不明点を切開し、入力、出力、CRS、NoData、COG構造、HTTP応答等を確認するための診断器具として使用する。

### 4.2 Static by default

利用者が操作するWebアプリケーションは、原則として完全スタティックにする。

- HTML
- CSS
- browser JavaScript
- YAMLまたはJSONのtask定義
- GeoJSON等の境界
- CORS対応COG
- 集計済みJSONまたはCSV
- provenance

を静的ホスティングから提供する。

### 4.3 Processing at publication time, not request time

ブラウザに不向きな処理は、利用者の要求時に常駐サーバーで行うのではなく、原則として公開・更新工程で一度実行し、地域向けの乾いた派生成果を生成する。

```text
FAOに新しいItemが追加される
    ↓
北海道との交差を確認
    ↓
北海道分を切り出す
    ↓
必要なら再投影する
    ↓
CORS対応COG、集計JSON、provenance、STAC metadataを生成
    ↓
静的ホスティングへ公開
    ↓
ブラウザが直接参照
```

### 4.4 Processing service is permitted, but bounded

ブラウザ処理にも発行時バッチにも適さない処理が確認された場合、限定されたprocessing serviceを設けてよい。

ただし、processing serviceは次を満たすこと。

- 入力契約が明示される
- 出力契約が明示される
- STAC Item、Asset、AOI、処理方法が記録される
- UI固有のセッション状態を正本にしない
- 結果をJSON、CSV、COG等の可搬的な成果として返す
- 特定のWeb画面がなくても成果を再利用できる
- 重い処理だけに限定する
- 常時稼働する巨大な地理空間基盤へ発展させない

### 4.5 Automate, but do not hide decisions

自動検索、自動選択、自動表示を行ってよい。しかし、重要な判断を画面と成果物に残す。

- 何を検索したか
- 何件見つかったか
- どのItemを選んだか
- なぜそのItemを選んだか
- どのAssetを使用したか
- どのAOIを使用したか
- どの投影を使用したか
- どの集計規則を使用したか
- 何が未確認か
- 何を結果から主張できないか

### 4.6 Regional responsibility

藤村英範のarea of responsibilityは北海道である。

FAOのグローバルデータを北海道について検証し、北海道だけを切り出し、必要に応じて再投影し、CORS対応COGや地域集計JSONとして提供することは、本リポジトリの重要な実装仮説である。

これは原資産を置き換えるコピーではない。目的、範囲、変換、来歴、責任境界を持つ管理された派生成果である。

### 4.7 Use data by reference, derive only with purpose

原資産を無目的に複製しない。

地域派生成果を作る場合は、次の理由を明確にする。

- 全球データが執務利用には大きすぎる
- CORSを保証する必要がある
- ブラウザから効率よく参照できるCOGが必要である
- 地域利用に適した投影が必要である
- 地域単位の集計値を事前生成する必要がある
- 執務PCに計算環境がない
- 静的配信によって保守負担を下げられる

### 4.8 Pre-harvested metadata mirrors are welcome, but stay traceable

STACメタデータそのものも、ラスターと同様に発行時収穫の対象になり得る。dwg7 colleagueのyuisekiによる`stac.yuiseki.net/fao-ferspas`（GeoParquetによるFERSPAS STAC索引）はその実例であり、詳細は7章に記録する。

pre-harvested indexを使う場合も、4.7と同じ規律を適用する。

- 正本（FERSPAS STAC API）ではなくミラーであることを明示する
- snapshot日付を記録する
- ライセンスはコレクションごとに異なるため、indexの列だけで判断せず個別に確認する

### 4.9 独自にAOIを定義する場合は、行政境界より空間ID/タイル区画を優先する

参照元Notebookが既に特定のAOI（国境等）を使っている場合は、Functional fidelity（24章）のためそのまま踏襲する。しかし、**このリポジトリが独自にAOIを定義する場面**（参照元に対応が無い地域拡張等）では、行政境界や地域概念（「北海道」「北方圏」等）を第一候補にしない。

理由は次の通り。

- 行政境界は係争地域を含みうる政治的判断を伴う
- 地域概念（「北方圏」等）で行政境界を避けたつもりでも、その概念自体の範囲・妥当性が普遍的に合意されるとは限らない
- slippy-map tile（Web Mercatorのz/x/y）は単なる座標上の数学的分割であり、地名・行政・文化的な主張を一切含まない。日本の「空間ID」ガイドライン（経産省・国交省・国土地理院ほか）が水平方向の指標として採用しているものと同じ枠組みである

したがって、独自AOIは`z-x-y`（ハイフン区切り、空間IDの水平インデックス）で識別する。実例は7章および`docs/Case2-GHG-4-14-5/`（`docs-internal/decisions.md`参照）。

この方式の既知の制約: Web Mercator/slippy-map tileは緯度85.05°付近より極側を表現できない。AOIが極域にかかる場合はこの方式を使えない。

## 5. 成果物の初期構成

公開用成果は`docs/`以下に置き、GitHub Pages等からそのまま公開できる構成にする。

```text
.
├── CLAUDE.md
├── README.md
├── diagnostics/
│   ├── Justfile
│   └── README.md
├── tasks/
│   ├── Case1-ASIS-latest-Italy.yaml
│   ├── Case1-ASIS-latest-<spatial-ID>.yaml   （Phase 4、未実装。命名は4.9節に従う）
│   ├── Case2-GHG-BDG.yaml
│   └── Case2-GHG-4-14-5.yaml
├── docs/
│   ├── index.html
│   ├── Case1-ASIS-latest-Italy/         （実装済み）
│   │   ├── index.html
│   │   ├── task.yaml
│   │   └── derived/                      （hfuさんのADCで発行時チェックアウトした派生COG）
│   ├── Case1-ASIS-latest-<spatial-ID>/   （Phase 4、未実装）
│   │   ├── index.html
│   │   ├── task.yaml
│   │   └── derived/
│   ├── Case2-GHG-BDG/
│   │   ├── index.html
│   │   ├── task.yaml
│   │   └── derived/
│   │       ├── BGD-1992.tif
│   │       ├── ...
│   │       └── timeseries-BGD.json
│   └── Case2-GHG-4-14-5/
│       ├── index.html
│       ├── task.yaml
│       └── derived/
└── docs-internal/
    ├── decisions.md
    ├── findings.md
    └── provenance-design.md
```

各Caseは`docs/<Case名>/`というディレクトリにまとめる（2026-09-19、URL設計の決定。`docs-internal/decisions.md`参照）。ページ本体(`index.html`)・task定義の公開コピー(`task.yaml`)・チェックアウトした派生データ(`derived/`)を同じ場所に置き、Caseが増えても`docs/`直下が散らからないようにする。ディレクトリ名は参照元Notebookのファイル名に対応させ（6章）、中のデータファイル名は正しい国コード等を使う。

AOI境界（GeoJSON等）は、まず対象Caseのディレクトリ内に置く。複数のCaseで同じ境界を再利用する段階になったら、共有ディレクトリへ昇格することを検討する。

ディレクトリは必要になった段階で作る。空の構造を形式的に量産しない。

## 6. 命名上の注意

参照元Notebook名は`Case2-GHG-BDG.ipynb`であるため、対応する公開ディレクトリは当面`docs/Case2-GHG-BDG/`とする。

ただし、BangladeshのISO 3166-1 alpha-3 codeは通常`BGD`であり、参照元コード内でも境界選択には`BGD`が使われている。`BDG`は参照元ファイル名および一部出力名に残る転置とみられる。

したがって、次を分離する。

- 参照元との対応を示すディレクトリ名: `docs/Case2-GHG-BDG/`
- データ、task、UI、metadataで使用する国コード: `BGD`（`derived/`内のファイル名等）
- UI上の名称: `Bangladesh`

将来、参照元側の命名が修正された場合は、互換URLまたはredirectを残した上で`BGD`へ統一することを検討する。

## 7. Yuiseki GeoParquet index: 事前収穫された静的STACメタデータ

### 7.1 これは何か

dwg7 colleagueのyuisekiが、FERSPAS STAC API（`https://data.apps.fao.org/geospatial/search/stac`）の全メタデータを収穫し、2つのGeoParquetファイルとして公開している。

- `https://stac.yuiseki.net/fao-ferspas/collections.parquet`（1,921コレクション）
- `https://stac.yuiseki.net/fao-ferspas/items.parquet`（639,947アセット、2026-09-18時点のsnapshot）
- ソース: https://github.com/yuiseki/study-un-fao-ferspas
- README: https://stac.yuiseki.net/fao-ferspas/README.md

保持するのはメタデータのみである。ラスター本体はFAOのサーバーに残り、テーブルはURLと宣言サイズを持つ（宣言サイズ合計は約21TB）。バルクダウンロードは発生しない。

### 7.2 この設計原則との一致

これは本リポジトリの4.3「Processing at publication time, not request time」および4.8と同型の実践である。相違点は対象のレイヤーだけである。本リポジトリはラスター（COG）を発行時に地域化するが、yuisekiの実践はSTACメタデータそのものを発行時に収穫し、クエリ可能な静的ファイルへ固める。

```text
FERSPAS STAC API（live、CORS未検証、POST /search必須）
    ↓ harvest（yuiseki、発行時に一度）
collections.parquet / items.parquet（静的、HTTPS配信）
    ↓ query（DuckDB、HTTP range readで部分読取。ダウンロード不要）
Item / Asset選択の材料
```

これは、バルクダウンロードや常駐サーバーを介さず、クラウドネイティブなフォーマット（COG、GeoParquet）をHTTP Range Requestで直接クエリするという、本リポジトリが目指す方向性と同じ発想の実例である。

### 7.3 Item/Asset discoveryへの適用候補

2026-09-19の実測で、FERSPAS Live STAC API自体もCORSが通ることを確認した（`docs-internal/findings.md`）。したがって「CORSが通らないからGeoParquetが必要」という理由づけは成立しない。優劣はクエリの性質に依存する。

```text
A. Live STAC API（POST /search）
   - Notebookが行う方式そのもの
   - CORS確認済み（2026-09-19）。実測295 bytesの1往復で完結
   - 単発の的を絞った検索（例: 最新1件）に向く
   - 常に最新
   - 複数コレクション横断や大量列挙にはページングが要る

B. yuiseki GeoParquet index（DuckDBでクエリ）
   - CORS確認済み（2026-09-19）
   - 複雑・横断・大量のクエリ（例: 1921コレクションのうちAOIと交差するものを一括抽出）に向く
   - 更新はsnapshot日付に依存する。取得日時をprovenanceへ記録する
```

どちらか一方を教義にしない。詳細は`docs-internal/decisions.md`「GeoParquet/DuckDBの使いどころを、発行時とブラウザ内で分離する」を参照。要点だけ記すと次のとおり。

- Case 1/2のような、答えが発行時に一度決まる固定的な問いは、`duckdb` CLIを診断/発行パイプラインで叩き、結果を静的JSONとして書き出す（4.3節）。**利用者のブラウザはduckdb-wasmをロードしない。**
- 利用者が対話的にクエリを変える場面（21章 Phase 5）に限り、ブラウザ内duckdb-wasmを検討する。Phase 1–4では不要と判断している。

### 7.4 スキーマの要点（参照用）

`collections.parquet`

- `id`はfull API id（`fao-gismgr:<CATALOG>:raster:<KIND>:<SHORT_ID>`）。`catalog`/`kind`/`short_id`は分解済み
- `dimensions`/`dimension_values`: そのコレクションがフィルタできる次元と語彙
- `item_count`: API集計エンドポイントの値と一致することが確認済み
- `license`: コレクションごとのライセンス（CC-BY-4.0、CC-BY-SA-4.0、CC-BY-NC-SA-4.0、notspecified、other-at、other-openが混在。非商用ライセンスを含むため、地域派生成果を作る前に個別に確認する）

`items.parquet`

- `dims`: そのファイルが固定される各カテゴリカル次元の値。`season`/`lct`/`crop`/`depth`/`stats`/`clim`/`period`/`ssp`/`tech`は個別カラムとしても持つ
- `data_href`（HTTPS）/`data_gs_href`（GCS）/`file_size`
- `gismgr_item_id`: FAOの旧ドット区切り形式（例: `fao-gismgr/ASIS/mapsets/MVHI-D/ASIS.MVHI-D.1984-01-D1.GS1.LC-C`）。**Notebookのpystac-client経由の`item.id`はこの形式と一致する**（`id`列のコロン/ハイフン区切り形式ではない）。Notebookのregexをそのまま使う場合は`gismgr_item_id`を見ること（2026-09-19、MVHI-D多年平均を扱う別Notebook事例で確認）
- `bbox`（`STRUCT(xmin, ymin, xmax, ymax)`）と`geometry`（`GEOMETRY`）を**item単位でも**持つ。ASISファミリー等のグローバルdekadalプロダクトはitem自体がほぼ全球（例: 実測でxmin=-180, ymin=-56.0, xmax=180.0, ymax=75.0）であるため、STAC検索時点でのAOI（北海道等）によるbbox絞り込みは実質無効。絞り込みは常に「対象範囲内の処理」の段階で行う（`docs-internal/findings.md`）
- `start_datetime`/`end_datetime`は`TIMESTAMP`型（epoch msの`BIGINT`ではない）
- 全アセットが`.tif`かつ`image/tiff; application=geotiff; profile=cloud-optimized`（COG）で統一されている。これは14章のCOG検証（Gate 5）の一部を既知の事実として引き継げることを意味するが、鵜呑みにせず個別アセットでの実地検証（Range Request、CRS、NoData）は省略しない

### 7.5 診断とprovenanceへの反映

- `diagnostics/Justfile`に、live API検索の代わりにyuisekiのGeoParquetをクエリする診断タスクを追加してよい（例: `just yuiseki-collections`、`just yuiseki-items`）。19章のtool listへ`duckdb`（spatial extension込み）を追加する
- yuisekiのindexを経由してItem/Assetを選んだ場合、provenance（13章）へ次を明記する
  - 収穫元: yuiseki GeoParquet index（URLとsnapshot日付）
  - Live STAC APIとの整合性を確認したか、確認した日付
  - このindexが正本（source of truth）ではなく、FERSPAS STAC APIの派生ミラーであること
- 全行で同一の値（例: media type）は列として持たず既知の事実として記録するという、yuisekiの冗長排除の考え方は、本リポジトリの集計JSONやtask YAML設計でも参考にしてよい

### 7.6 帰属

このindexはyuiseki（https://github.com/yuiseki/study-un-fao-ferspas）の成果である。本リポジトリで参照・利用する場合は出典を明記する。yuisekiのindex自体もメタデータのみを再配布しラスター本体を再配布しないという性質を、参照・派生時も維持する。

### 7.7 これは本筋ではなく、並行するトラックである

「複雑・横断・大量」のクエリが存分にできること自体は、Case 1/2という**Notebookの移植**という直近の目標には必須ではない。その価値は、次の2つの目的のための内部ツールとしてある。

- 私たち自身が「ナラティブの材料となるユースケース」「Userの問い」を発見するための探索手段
- 将来、この探索レイヤーへ生成AIを組み込み、Userの次の問いを提案する仕組みへ発展させる可能性（18章「Staccato / AI」の候補）

これは「Jupyter NotebookにおけるFERSPASの使用をブラウザへ移植する」という本筋とは別の、並行するトラックとして扱う。混同しない。詳細は`docs-internal/decisions.md`を参照。

## 8. 共通アーキテクチャ

```text
Task YAML
    ↓ fetch + parse
Browser JavaScript
    ↓ fetch
FERSPAS STAC API（live）または yuiseki GeoParquet index（7章）
    ↓
Item / Asset selection
    ↓
A. source COG direct access
または
B. regional derived COG / JSON
    ↓
browser-native visualization
    ↓
selection rationale + provenance + limitations
```

### Notebookとの対応

```text
pystac-client          → browser fetch()
Python list processing → JavaScript Array operations
rasterio display       → browser COG viewer
rasterio.mask          → visual AOI, regional derivative, or bounded processing
pandas                  → browser-side arrays / static JSON
matplotlib              → browser map and chart
Notebook cells          → visible stages, evidence, and explanations
```

NotebookのPythonコードをJavaScriptへ逐語移植しない。Notebookが実践するユーザーストーリー、判断、処理、成果をWebの構造へ翻訳する。

## 9. Task YAML

各HTMLのタスク定義は、原則として`tasks/`のYAMLへ分離する。

ブラウザは相対URLまたは明示されたtask URLを`fetch()`し、安全なYAMLパーサーで解析する。

YAMLは単純な構造に限定する。

- anchors、aliases、custom tagsを使わない
- executable typesを許可しない
- 複雑なmergeを使わない
- 文字列、数値、真偽値、配列、単純なobjectのみ

HTMLから`../tasks/...`を取得するとGitHub Pagesの配置や別ホストへのコピーで壊れやすいため、公開用task YAMLは各Caseのディレクトリ（`docs/<Case名>/task.yaml`、5章参照）へコピーし、ページは同じディレクトリ内の相対パス（`task.yaml`）でfetchする。正本（`tasks/*.yaml`）と公開物の関係はREADMEに記録する。

## 10. Case 1: ASIS latest

### 10.1 参照元

- `Case1-ASIS-latest-Italy.ipynb`
- Collection: `ASI-D`

### 10.2 起点となるタスク

```text
最近のASI-D Itemを検索
    ↓
最新time phaseを特定
    ↓
GS1 / LC-C Itemを選択
    ↓
GeoTIFF / COG Assetを選択
    ↓
対象地域で表示
```

### 10.3 Italy版（実装済み）

`docs/Case1-ASIS-latest-Italy/`

実装・動作確認済み（2026-09-20）。

成功条件（すべて達成）:

- STAC APIをブラウザから検索できる
- 最新のGS1 / LC-C Itemを選択できる
- 選択理由を表示できる
- COGをブラウザで直接読める（発行時チェックアウトした派生成果として）
- Italy周辺へ表示できる
- Italy境界を表示できる
- palette、NoData、CRS、provenance、制約を確認できる

原資産（`fao-gismgr-asis-data`バケット）は匿名読み取りが拒否されることが確定していたため（`docs-internal/findings.md`、`docs-internal/decisions.md`）、「COGをブラウザで直接読む」は原資産への直接アクセスではなく、Case 2と同じ「発行時にhfuさんのADCでチェックアウトし、Italy国境でクロップして再配布したコピーをブラウザが読む」という構成で実現している（`scripts/checkout-Case1-ASIS-latest-Italy.py`）。物理的なcropとダウンロード用GeoTIFF生成は、この構成では前提ではなく必須になった。

### 10.4 Hokkaido版

`docs/Case1-ASIS-latest-Hokkaido/`

Italy版のユーザーストーリーを北海道へ移す。

2026-09-19時点、ASI-Dの実アセット（`fao-gismgr-asis-data`バケット）は匿名読み取りが拒否されることを確認済み（`docs-internal/decisions.md`）。したがって「まずsource COGを直接表示できるか確認する」は、確認した結果として**不可である前提**で進めてよい。発行時に次を生成する。

- 北海道clip
- 利用目的に適した再投影
- CORS対応COG
- 推奨paletteまたはstyle metadata
- provenance
- 派生STAC Item

Italy版とHokkaido版でHTMLロジックを複製しない。可能な限りtask YAMLとAOI資産の差として表現する。ただし、汎用化が第一試作を遅らせる場合は、Italy版の成立を優先する。

## 11. Case 2: Drained cropland area time series

### 11.1 参照元

- `Case2-GHG-BDG.ipynb`
- Collection: `DRAINED-AREA-CROP`
- 参照元の実処理期間: 1992年から2022年

参照元の冒頭コメントには2020年までとあるが、検索条件、Item一覧、集計結果は2022年まで含む。この差異を既知の事項として記録する。

### 11.2 起点となるタスク

```text
1992–2022のItemを検索
    ↓
各年のGeoTIFF Assetを選択
    ↓
対象地域との交差部分を得る
    ↓
対象地域内の有効pixelを合計
    ↓
年別時系列を作る
    ↓
グラフと選択年の地図を表示
```

### 11.3 Bangladesh版

`docs/Case2-GHG-BDG/`

初期段階では次の三層を区別する。

1. 31年分のSTAC ItemとAssetを発見する
2. 選択年のCOGを地図表示する（2026-09-19確認: `fao-gismgr-faostat-data`バケットは匿名読み取り自体は通るが、CORSヘッダーがないためブラウザの`fetch()`では読めない。`docs-internal/findings.md`参照。ブラウザで直接表示するには、CORS対応の再ホストが要る）
3. 年別集計値を時系列で表示する

年別集計は、次の順で実装可能性を評価する。

```text
A. 参照Notebookの集計値を検証済み静的JSONとして表示
B. 一年分だけブラウザで再計算し、Notebook値と比較
C. 性能と意味が妥当なら31年分をブラウザ計算
D. 重い場合は発行時処理または限定processing serviceへ移す
```

最初から31年分をブラウザでライブ集計しない。

### 11.4 第二のAOI版（実装済み: 空間ID `4-14-5`）

`docs/Case2-GHG-4-14-5/`

当初「Hokkaido版」として計画していたが、4.9節の決定により行政境界・地域概念を使わず、slippy-map tile（空間ID水平インデックス）`z=4/x=14/y=5`をAOIとする（`docs-internal/decisions.md`、2026-09-19）。グローバルな各年Assetから、このタイル矩形の派生成果を発行する構成を採る（原資産バケットにCORSが無いため、これは有力候補ではなく前提。`docs-internal/decisions.md`参照）。

```text
FAO global annual COGs
    ↓ publication-time processing（矩形クロップ、マスクなし、投影変換なし）
tile 4-14-5 annual COGs
    ↓
tile 4-14-5 time-series JSON
    ↓
static web application
```

ブラウザは次を行う。

- 時系列JSONを取得する
- 折れ線グラフを表示する
- 選択年のtile COGを表示する
- Item、Asset、処理方法、AOI（空間ID）、投影、NoData、集計規則を表示する
- 必要ならCOGをダウンロードできるようにする

実装・動作確認済み（`scripts/checkout-Case2-GHG-4-14-5.py`、`docs-internal/findings.md`）。

## 12. Case 2の集計意味論

Notebookの`band.sum()`をそのまま正しいものと仮定しない。

次を確認する。

- pixel値は面積haを表すか
- 面積率、割合、分類値ではないか
- scale、offsetはあるか
- NoDataは何か
- 0は有効値か
- latitudeによるpixel面積差は値へ織り込み済みか
- 合計だけで対象地域の面積が得られる製品設計か
- 境界上のpixelをどの規則で含めるか
- 各年のgrid、resolution、extentは同一か
- resamplingを行う場合、値の意味を維持できるか

### 再投影時の注意

表示用COGへの再投影と、面積集計用ラスターへの再投影を安易に同一化しない。

- 連続値か分類値か
- 合計保存が必要か
- nearest、bilinear、average等のどれが妥当か
- equal-area projectionが必要か
- 元pixel値がすでに面積値なら再投影時に合計が変わらないか

を確認する。

集計は、Notebookと数値が一致するだけでなく、製品仕様上正しい必要がある。

## 13. Regional materialization

北海道向け派生成果には、最低限、次を残す。

- metadata harvest route（live STAC API / 事前収穫index。7章）
- source STAC API
- source Collection
- source Item ID
- source Asset href
- source datetime
- source CRS
- output CRS
- AOI名称
- AOI geometry source
- AOI版または取得日
- clip method
- resampling method
- NoData handling
- scale / offset handling
- aggregation method
- pixel inclusion rule
- generation time
- tool versions
- license
- attribution
- checksum
- official / unofficial status

### provenance例

```json
{
  "source": {
    "collection": "DRAINED-AREA-CROP",
    "item": "FAOSTAT.DRAINED-AREA-CROP.2022",
    "asset": "https://storage.googleapis.com/..."
  },
  "derivation": {
    "area": "Hokkaido",
    "boundary_source": "...",
    "source_crs": "...",
    "output_crs": "...",
    "operation": "clip-and-reproject",
    "resampling": "..."
  },
  "output": {
    "asset": "...cog.tif",
    "media_type": "image/tiff; application=geotiff; profile=cloud-optimized"
  }
}
```

## 14. COGとCORS

ブラウザ直接利用するCOGは、次を満たす必要がある。

- 有効なGeoTIFFである
- Cloud Optimized GeoTIFFである
- HTTP Range Requestが機能する
- CORSが許可される
- Range関連の必要なresponse headerがブラウザへ公開される
- ブラウザで安全に扱える認証条件である
- 対応可能な圧縮、データ型、CRSである

北海道向け派生COGは、これらを発行工程で保証する。

## 15. 表示技術

第一候補として、Source Cooperative `cog-viewer`が使用するDevelopment Seed系のbrowser-native raster stackを評価する。

参考にする機能:

- static, browser-only
- byte-rangeによるCOG読込み
- native tiling
- reprojection
- band inspection
- single-band / RGB
- rescale
- colormap
- NoData
- gamma
- opacity
- URLでの状態共有

第二候補として、MapLibre GL JSと`maplibre-cog-protocol`を評価する。

MapLibreを使う理由:

- AOI boundaryを重ねやすい
- STAC footprintや他のベクトル情報を重ねやすい
- 将来の地域選択や比較へ発展しやすい

MapLibreを外す理由:

- COGの投影、palette、NoData、band inspectionが別実装より難しい
- basemapが不要である
- raster観察だけなら別viewerの方が小さい

MapLibreを目的化しない。Caseごとに最小の複雑さで成立する技術を選ぶ。

ここで扱うのはラスター表示層である。Item/Asset discovery（メタデータ検索）層でduckdb-wasmを使う場合は7章を参照する。両者は別の関心事として扱い、混同しない。

## 16. チャート

Case 2の時系列表示は、軽量で透明な実装を優先する。

候補:

- native SVG
- Observable Plot
- uPlot
- Apache ECharts
- Open MCT内のtime-series view（後段）

第一試作では高度なダッシュボードを作らない。

チャートには次を対応させる。

- year
- value
- unit
- source Item
- selected year
- data quality / warning

年を選ぶと、対応するCOG、Item metadata、provenanceが同期する構成を目指す。

## 17. Open MCT

第一段階ではOpen MCTを必須にしない。

次が必要になった場合に導入を検討する。

- 複数時点の同期
- 地図と時系列の同期
- task state
- provenance
- observation history
- 複数Collectionの比較
- 複数ビューの構成

Open MCTは成果を閉じ込める実行基盤ではなく、公開された静的資産やブラウザ処理結果を時間・状態に沿って編成する表示面として扱う。

## 18. Staccato / AI

初期4ケースの成立前にStaccatoや対話AIを中心へ置かない。

固定タスクを実行した後に、AIが有効な箇所を観察する。

候補:

- Collection候補の説明
- Item variantの違いの説明
- task YAMLの生成・編集支援
- 実行計画の説明
- provenanceの要約
- 次の比較条件の提案

AIはデータ値の意味を根拠なく解釈しない。

## 19. Diagnostics

診断には原則として次を使用する。

```text
curl
jq
modern GDAL CLI
just
duckdb（spatial extension、yuiseki GeoParquet indexのクエリ用。7章）
```

Python、Rust、GoのSTAC clientを初期依存にしない。

`diagnostics/Justfile`にはロジックを大量に書かず、診断行為へ名前を付ける。

```text
just collection
just search
just item
just asset-headers
just raster-info
just verify-cog
just compare-value
just build-hokkaido
just yuiseki-collections
just yuiseki-items
```

複雑なJSON処理は必要に応じて`.jq`ファイルへ分離する。

## 20. Feasibility gates

各Caseは次を順に確認する。

### Gate 1: Task

- YAMLを静的ホスティングから取得できる
- 安全に解析できる
- 必須項目を検証できる

### Gate 2: STAC

- Collectionを取得できる
- `/search`へPOSTできる
- CORSが成立する
- Item一覧を取得できる
- （代替経路）yuiseki GeoParquet indexでCORSと必要なクエリが成立する（7章）

### Gate 3: Selection

- Notebookと同じItemを選べる
- 選択理由を説明できる
- Item ID依存等の暫定条件を表示できる

### Gate 4: Asset

- 適切なGeoTIFF Assetを識別できる
- href、type、rolesを表示できる
- 認証とアクセス条件を確認できる

### Gate 5: COG

- COGである
- Range Requestが機能する
- CORSが成立する
- CRS、NoData、bands、value rangeを読める

### Gate 6: Semantics

- 値の意味が分かる
- paletteまたは集計規則が妥当である
- 未確認事項を明示できる

### Gate 7: Browser task

- 対象Userがプログラミング環境なしで実行・観察できる
- 何を見ているか説明できる
- 出所、処理、制約を確認できる

### Gate 8: Reproducibility

- task、Item、Asset、処理、結果が記録される
- Web画面がなくても元資産と派生成果を追跡できる

## 21. 実装順序

2026-09-19時点、Case 1（ASI-D、`fao-gismgr-asis-data`バケット）は匿名読み取りが拒否されることを確認済みで、FAO CSIへの相談が必要（`docs-internal/decisions.md`）。相談はlaunchが落ち着いてから行う方針のため、Case 2を先に進める。

### Phase 1: Case 2 Bangladesh

1. 1992–2022 Item discovery
2. 年一覧
3. 一年分のCOG表示
4. Notebookの集計値を静的JSONで表示
5. 一年分のbrowser-side集計を試す
6. Notebook値と比較
7. 31年分の実行方式を判断

### Phase 2: Case 2 spatial ID 4-14-5（実装済み）

1. ~~北海道で製品利用が意味を持つか確認~~ → 行政境界を使わず、slippy-map tile `4-14-5`をAOIとする方針に変更（4.9節）
2. 年別tile COGを発行
3. 年別集計JSONを発行
4. static chart and map
5. provenance and limitations

すべて実装・動作確認済み（`docs/Case2-GHG-4-14-5/`、`docs-internal/findings.md`）。

### Phase 3: Case 1 Italy（実装済み）

2026-09-19、hfuさん個人のGoogle認証（Application Default Credentials）でASI-Dバケットが読めることを確認した（`docs-internal/findings.md`）。匿名アクセスは相変わらず拒否されるが、Case 2と同様「hfuさんの認証で発行時チェックアウトし、CORS対応で再配布する」パターンに乗せられるため、FAO CSIとの相談を待たずに着手できた。

1. task YAML
2. page shell
3. browser STAC search
4. Item selection
5. Asset selection
6. COG rendering（発行時チェックアウトした派生成果を使う。9.3の「直接読み」前提は不成立と確定）
7. Italy boundary
8. provenance and limitations

すべて実装・動作確認済み（`docs/Case1-ASIS-latest-Italy/`、`scripts/checkout-Case1-ASIS-latest-Italy.py`、2026-09-20）。ただしチェックアウトの実行にはhfuさんの認証（ADC）が必要という制約が伴うため、Case 2と異なり任意のlocal foundationが単独で再現できるわけではない。

### Phase 4: Case 1 第二のAOI版（着手可能、命名は4.9節に従う）

Case 2と同様、「Hokkaido」ではなく空間ID/タイル区画で命名する（4.9節）。

1. AOI差替え
2. source COG direct rendering
3. 必要なら北海道向けCOG生成
4. CRSとpalette検証
5. provenance

### Phase 5: Extension

実際のUser journeyから必要性が確認されたものだけを追加する。

- area selection
- time selection
- comparison
- palette control
- permalink
- downloadable task
- Open MCT
- Staccato / AI
- bounded processing service

## 22. Claude Codeの役割

Claude Codeは共同設計者・実装者として次を守る。

1. この`CLAUDE.md`を設計上の判断軸として扱う
2. 参照元Notebookを一次のユーザーストーリーとして読む
3. Notebookの処理を批判するより、判断、摩擦、意味を抽出する
4. 最初から汎用STAC Browserを作らない
5. 最初からframeworkを大規模導入しない
6. Runtimeを完全スタティックに保つ
7. Processingを追加する場合は発行時処理を優先する
8. Processing serviceを追加する場合は入出力と責任境界を明示する
9. Pythonを初期依存に追加しない
10. CORS、Range、COG、CRS、NoData、palette、集計意味論を個別に検証する
11. 自動選択の理由を隠さない
12. 事実、仮説、暫定実装、価値判断を分離する
13. 外部資産のライセンスとattributionを確認する
14. 北海道向け派生成果とFAO原資産の関係を追跡可能にする
15. 重要な判断を`docs-internal/decisions.md`へ記録する
16. Userの次の問いを生む観察を優先する
17. UIの完成度より、機能、意味、再現性を優先する
18. yuisekiのGeoParquet indexのような事前収穫metadata mirrorは、正本ではなくミラーとして扱い、snapshot日付を記録する（4.8、7章）

## 23. Claude Codeが最初に行うこと

実装前に次を調査・報告する。

1. 参照元`FERSPAS_demo`のCase 1とCase 2の現在内容
2. ~~FERSPAS STAC APIのCORS~~ → 2026-09-19確認済み。GET/OPTIONS/POST `/search`いずれも`access-control-allow-origin: *`（`docs-internal/findings.md`）
3. ~~使用AssetのCORSとRange Request~~ → 2026-09-19確認済み。ASI-D（`fao-gismgr-asis-data`）は匿名読み取り自体が拒否される（Googleログインへリダイレクト）。DRAINED-AREA-CROP（`fao-gismgr-faostat-data`）は匿名読み取りは通るがCORSヘッダーがない。いずれもブラウザから直接は読めない（`docs-internal/findings.md`）
4. AssetのCOG適合性
5. AssetのCRS、NoData、bands、value range
6. ASI-DのGS、LC、time phase、paletteの意味
7. DRAINED-AREA-CROPのpixel値と単位の意味
8. Case 2の`band.sum()`の妥当性
9. Italy / Bangladeshのbrowser-native feasibility
10. Hokkaido向けmaterializationの必要性
11. Source Cooperative / Development Seed方式の適用可能性
12. MapLibre方式の適用可能性
13. yuiseki GeoParquet index（stac.yuiseki.net/fao-ferspas）のCORS、snapshot鮮度、live STAC APIとの数値整合性
14. 最小の技術構成

調査後に、小さなcommit sequenceを提案する。実装は承認を待たず、明らかに安全な第一歩から進めてよいが、重大なアーキテクチャ変更は`docs-internal/decisions.md`へ記録する。

## 24. 禁止する短絡

### Notebook一般を置き換えようとする

Notebookは探索と方法開発に優れる。本リポジトリは成熟したタスクの配備を扱う。

### 見栄えのよいViewerだけを作る

選択、処理、来歴、制約が見えなければ実用品とは評価しない。

### 北海道向けコピーを無目的に作る

地域派生成果には目的、来歴、更新、責任境界が必要である。

### 再投影すれば自動的に正しくなると考える

表示と集計で必要な投影・resamplingは異なり得る。

### Notebookと同じ数値なら正しいと考える

製品仕様上の意味を確認する。

### CORS問題を無言でproxyへ逃がす

中継の存在と理由を表示する。

### Browser-onlyを教義にする

ブラウザに不向きな処理には発行時処理または限定serviceを用いる。ただし静的成果を優先する。

### 利用者へプログラミング環境の導入を要求する

本リポジトリの主要Userはブラウザだけで利用できることを前提とする。

### Pre-harvested indexを無条件に正本と扱う

yuisekiのGeoParquet indexはsnapshot時点のミラーである。snapshot日付、Live APIとの整合性、コレクションごとのライセンスを確認せずに正本（FERSPAS STAC API）と同一視しない。

## 25. 成功の評価軸

### Functional fidelity

Notebookと同じ入力、選択、AOI、処理規則に基づく結果を再現できる。

### Semantic fidelity

値、単位、NoData、境界、集計、投影の意味が維持される。

### Operational usability

対象Userがプログラミング環境なしで利用できる。

### Reproducibility

task、Item、Asset、処理、tool version、結果、provenanceが記録される。

### Sustainability

特定のUIやprocessing serviceが停止しても、元資産、派生成果、task、provenanceを再利用できる。

## 26. 第一段階の成功条件

最終的に次の4ページが`docs/`で公開される。Case2系（Bangladesh／spatial ID 4-14-5）とCase1-Italyの3ページは**実装・公開済み**（GitHub Pages、`docs-internal/decisions.md`）。Case1第二のAOI版はPhase 4として今後実装する。

```text
Case1-ASIS-latest-Italy/        （Phase 3、実装済み）
Case1-ASIS-latest-第二のAOI/     （着手可能、Phase 4）
Case2-GHG-BDG/                  （Phase 1、実装済み）
Case2-GHG-4-14-5/               （Phase 2、実装済み）
```

各ページは、少なくとも次を満たす。

- 対応するtask定義を読む
- FERSPASのCollection、Item、Assetとの関係を示す
- 地図または時系列の主要結果を表示する
- 何を自動選択したかを示す
- provenanceとlimitationsを示す
- sourceとderived assetを区別する
- Userが何を見ているか説明できる
- 次に発するべき問いが見える

## 27. 中心フレーズ

> **Experts explore in notebooks. Users repeat trusted tasks on the web.**

> **Turn reproducible notebook workflows into accessible, transparent web applications.**

> **Automate the task, but keep every important decision visible.**

> **Build regional derivatives with purpose, provenance and responsibility.**

> **Static where possible. Processing where necessary. Portable results always.**

> **Cloud-native formats, queried directly — not downloaded in bulk, not served through a server we run.**

日本語:

> **専門家はNotebookで探索する。利用者は検証されたタスクをWebで反復する。**

> **Notebookで確立された再現可能な処理を、利用者が扱える透明なWebアプリケーションへ移す。**

> **タスクは自動化する。しかし、重要な判断を隠さない。**

> **地域派生成果は、目的、来歴、責任を持って作る。**

> **可能な限り静的にする。必要な部分だけ処理する。成果は常に持ち運べる形で残す。**

> **クラウドネイティブな形式を、直接クエリする。まとめてダウンロードせず、自前のサーバーも介さない。**
