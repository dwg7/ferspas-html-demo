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
│   ├── Case1-ASIS-latest-Hokkaido.yaml
│   ├── Case2-GHG-BGD.yaml
│   └── Case2-GHG-Hokkaido.yaml
├── docs/
│   ├── index.html
│   ├── Case1-ASIS-latest-Italy.html
│   ├── Case1-ASIS-latest-Hokkaido.html
│   ├── Case2-GHG-BDG.html
│   ├── Case2-GHG-Hokkaido.html
│   ├── data/
│   │   ├── italy.geojson
│   │   ├── bangladesh.geojson
│   │   └── hokkaido.geojson
│   ├── assets/
│   │   └── ...
│   └── derived/
│       ├── case1-hokkaido/
│       └── case2-hokkaido/
└── docs-internal/
    ├── decisions.md
    ├── findings.md
    └── provenance-design.md
```

ディレクトリは必要になった段階で作る。空の構造を形式的に量産しない。

## 6. 命名上の注意

参照元Notebook名は`Case2-GHG-BDG.ipynb`であるため、対応するHTMLは当面`Case2-GHG-BDG.html`とする。

ただし、BangladeshのISO 3166-1 alpha-3 codeは通常`BGD`であり、参照元コード内でも境界選択には`BGD`が使われている。`BDG`は参照元ファイル名および一部出力名に残る転置とみられる。

したがって、次を分離する。

- 参照元との対応を示すファイル名: `Case2-GHG-BDG.html`
- データ、task、UI、metadataで使用する国コード: `BGD`
- UI上の名称: `Bangladesh`

将来、参照元側の命名が修正された場合は、互換URLまたはredirectを残した上で`BGD`へ統一することを検討する。

## 7. 共通アーキテクチャ

```text
Task YAML
    ↓ fetch + parse
Browser JavaScript
    ↓ fetch
FERSPAS STAC API
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

## 8. Task YAML

各HTMLのタスク定義は、原則として`tasks/`のYAMLへ分離する。

ブラウザは相対URLまたは明示されたtask URLを`fetch()`し、安全なYAMLパーサーで解析する。

YAMLは単純な構造に限定する。

- anchors、aliases、custom tagsを使わない
- executable typesを許可しない
- 複雑なmergeを使わない
- 文字列、数値、真偽値、配列、単純なobjectのみ

HTMLから`../tasks/...`を取得するとGitHub Pagesの配置や別ホストへのコピーで壊れやすい場合、公開用task YAMLを`docs/tasks/`へコピーまたは生成してよい。正本と公開物の関係をREADMEに記録する。

## 9. Case 1: ASIS latest

### 9.1 参照元

- `Case1-ASIS-latest-Italy.ipynb`
- Collection: `ASI-D`

### 9.2 起点となるタスク

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

### 9.3 Italy版

`docs/Case1-ASIS-latest-Italy.html`

第一試作として扱う。

成功条件:

- STAC APIをブラウザから検索できる
- 最新のGS1 / LC-C Itemを選択できる
- 選択理由を表示できる
- COGをブラウザで直接読める
- Italy周辺へ表示できる
- Italy境界を表示できる
- palette、NoData、CRS、provenance、制約を確認できる

物理的なcropとダウンロード用GeoTIFF生成は必須ではない。

### 9.4 Hokkaido版

`docs/Case1-ASIS-latest-Hokkaido.html`

Italy版のユーザーストーリーを北海道へ移す。

まずsource COGを直接表示できるか確認する。必要な場合は、発行時に次を生成する。

- 北海道clip
- 利用目的に適した再投影
- CORS対応COG
- 推奨paletteまたはstyle metadata
- provenance
- 派生STAC Item

Italy版とHokkaido版でHTMLロジックを複製しない。可能な限りtask YAMLとAOI資産の差として表現する。ただし、汎用化が第一試作を遅らせる場合は、Italy版の成立を優先する。

## 10. Case 2: Drained cropland area time series

### 10.1 参照元

- `Case2-GHG-BDG.ipynb`
- Collection: `DRAINED-AREA-CROP`
- 参照元の実処理期間: 1992年から2022年

参照元の冒頭コメントには2020年までとあるが、検索条件、Item一覧、集計結果は2022年まで含む。この差異を既知の事項として記録する。

### 10.2 起点となるタスク

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

### 10.3 Bangladesh版

`docs/Case2-GHG-BDG.html`

初期段階では次の三層を区別する。

1. 31年分のSTAC ItemとAssetを発見する
2. 選択年のCOGを地図表示する
3. 年別集計値を時系列で表示する

年別集計は、次の順で実装可能性を評価する。

```text
A. 参照Notebookの集計値を検証済み静的JSONとして表示
B. 一年分だけブラウザで再計算し、Notebook値と比較
C. 性能と意味が妥当なら31年分をブラウザ計算
D. 重い場合は発行時処理または限定processing serviceへ移す
```

最初から31年分をブラウザでライブ集計しない。

### 10.4 Hokkaido版

`docs/Case2-GHG-Hokkaido.html`

北海道版では、グローバルな各年Assetから北海道向けの派生成果を発行する構成を有力候補とする。

```text
FAO global annual COGs
    ↓ publication-time processing
Hokkaido annual COGs
    ↓
Hokkaido time-series JSON
    ↓
static web application
```

ブラウザは次を行う。

- 時系列JSONを取得する
- 折れ線グラフを表示する
- 選択年の北海道COGを表示する
- Item、Asset、処理方法、境界、投影、NoData、集計規則を表示する
- 必要ならCOGをダウンロードできるようにする

## 11. Case 2の集計意味論

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

## 12. Regional materialization

北海道向け派生成果には、最低限、次を残す。

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

## 13. COGとCORS

ブラウザ直接利用するCOGは、次を満たす必要がある。

- 有効なGeoTIFFである
- Cloud Optimized GeoTIFFである
- HTTP Range Requestが機能する
- CORSが許可される
- Range関連の必要なresponse headerがブラウザへ公開される
- ブラウザで安全に扱える認証条件である
- 対応可能な圧縮、データ型、CRSである

北海道向け派生COGは、これらを発行工程で保証する。

## 14. 表示技術

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

## 15. チャート

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

## 16. Open MCT

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

## 17. Staccato / AI

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

## 18. Diagnostics

診断には原則として次を使用する。

```text
curl
jq
modern GDAL CLI
just
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
```

複雑なJSON処理は必要に応じて`.jq`ファイルへ分離する。

## 19. Feasibility gates

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

## 20. 実装順序

### Phase 1: Case 1 Italy

1. task YAML
2. page shell
3. browser STAC search
4. Item selection
5. Asset selection
6. COG rendering
7. Italy boundary
8. provenance and limitations

### Phase 2: Case 1 Hokkaido

1. AOI差替え
2. source COG direct rendering
3. 必要なら北海道向けCOG生成
4. CRSとpalette検証
5. provenance

### Phase 3: Case 2 Bangladesh

1. 1992–2022 Item discovery
2. 年一覧
3. 一年分のCOG表示
4. Notebookの集計値を静的JSONで表示
5. 一年分のbrowser-side集計を試す
6. Notebook値と比較
7. 31年分の実行方式を判断

### Phase 4: Case 2 Hokkaido

1. 北海道で製品利用が意味を持つか確認
2. 年別北海道COGを発行
3. 年別集計JSONを発行
4. static chart and map
5. provenance and limitations

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

## 21. Claude Codeの役割

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

## 22. Claude Codeが最初に行うこと

実装前に次を調査・報告する。

1. 参照元`FERSPAS_demo`のCase 1とCase 2の現在内容
2. FERSPAS STAC APIのCORS
3. 使用AssetのCORSとRange Request
4. AssetのCOG適合性
5. AssetのCRS、NoData、bands、value range
6. ASI-DのGS、LC、time phase、paletteの意味
7. DRAINED-AREA-CROPのpixel値と単位の意味
8. Case 2の`band.sum()`の妥当性
9. Italy / Bangladeshのbrowser-native feasibility
10. Hokkaido向けmaterializationの必要性
11. Source Cooperative / Development Seed方式の適用可能性
12. MapLibre方式の適用可能性
13. 最小の技術構成

調査後に、小さなcommit sequenceを提案する。実装は承認を待たず、明らかに安全な第一歩から進めてよいが、重大なアーキテクチャ変更は`docs-internal/decisions.md`へ記録する。

## 23. 禁止する短絡

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

## 24. 成功の評価軸

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

## 25. 第一段階の成功条件

次の4ページが`docs/`で公開される。

```text
Case1-ASIS-latest-Italy.html
Case1-ASIS-latest-Hokkaido.html
Case2-GHG-BDG.html
Case2-GHG-Hokkaido.html
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

## 26. 中心フレーズ

> **Experts explore in notebooks. Users repeat trusted tasks on the web.**

> **Turn reproducible notebook workflows into accessible, transparent web applications.**

> **Automate the task, but keep every important decision visible.**

> **Build regional derivatives with purpose, provenance and responsibility.**

> **Static where possible. Processing where necessary. Portable results always.**

日本語:

> **専門家はNotebookで探索する。利用者は検証されたタスクをWebで反復する。**

> **Notebookで確立された再現可能な処理を、利用者が扱える透明なWebアプリケーションへ移す。**

> **タスクは自動化する。しかし、重要な判断を隠さない。**

> **地域派生成果は、目的、来歴、責任を持って作る。**

> **可能な限り静的にする。必要な部分だけ処理する。成果は常に持ち運べる形で残す。**
