# Findings

事実の記録。判断・価値判断は`decisions.md`側に置く。日付は確認日。

## 2026-09-19: 参照元`un-fao/FERSPAS_demo`のCase2-GHG-BDG.ipynbを実際に確認

`gh api`でリポジトリの実ファイルを取得して確認した（これまでCLAUDE.mdの記述とyuisekiのREADME、および別Notebook事例からの類推に頼っていた部分の裏取り）。

- リポジトリには`Case1`〜`Case5`まで5つのケースがある。本リポジトリがスコープとするのは1・2のみ（既定路線通り）
- Collection: `DRAINED-AREA-CROP`、BBOX（Bangladesh）: `[87, 20, 93, 27]`、DATETIME: `1992-01-01/2022-12-31`。CLAUDE.md 11.1の「冒頭コメントは2020年までだが実際は2022年まで検索する」という記述は、実コードの`DATETIME`文字列で裏付けられた
- Notebookも`gcsfs.GCSFileSystem()`（認証済みGCSアクセス）でダウンロードしている。匿名アクセスではなく、FAO内部の実行環境を前提としている点は、別Notebook事例と共通
- `href`の正規化ロジックが`storage.cloud.google.com`・`storage.googleapis.com`の両方を`gs://`へ変換する処理を持つ。実データでこの2つのドメイン形式が混在するという、こちらの実測（`data_href`の書式がCollectionによって異なる）と一致する
- 集計は`rasterio`の`masked=True`でNoDataを除外した`band.sum()`。年はファイル名から文字列操作で抽出（`BDG`という文字列の位置を基準に5〜1文字前）
- ライセンス表記・利用規約はリポジトリに見当たらない（README.mdは1行のみ）

## 2026-09-19: DRAINED-AREA-CROPのCOG意味論（Gate 5/6）を`gdalinfo`で確認

`gdalinfo -stats "/vsicurl/https://storage.googleapis.com/fao-gismgr-faostat-data/.../FAOSTAT.DRAINED-AREA-CROP.2022.tif"`で、匿名HTTP経由のリモート読み取りにより確認（GDAL 3.13.1、ダウンロード不要）。

- CRS: EPSG:4326（地理座標系、投影なし）。全球、43200×21362px、pixel size 0.00833333°（≒1km）
- データ型: Float32、単一バンド、COGレイアウト（LZW圧縮、overview 7段）
- **NoData値は未設定**（`gdalinfo`にNoData Value行が出ない）。`STATISTICS_VALID_PERCENT=100`と整合。参照Notebookは`rasterio`の`masked=True`でNoDataマスクに依存しているが、**このファイル自体にはマスクすべきNoDataがそもそも無い**。0は「排水耕地面積0ha」を表す有効値と解釈するのが妥当（CLAUDE.md 12章の「0は有効値か」に対する暫定的な回答）
- 値域: Minimum=0.000, Maximum=81.183。赤道付近のpixel面積（0.00833333°四方 ≈ 0.861km² ≈ 86.1ha）を超えない。これは「pixel値が緯度補正済みのha面積である」という前提（Notebookの列名"Drained Crop Area (ha)"に基づく前提であり、ラスター自身のメタデータにunit tagは無い）と**矛盾しない**、という弱い裏付けにとどまる。証明ではない
- 緯度によるpixel実面積の違い（赤道と高緯度で異なる）が値に織り込み済みかどうかは、この確認だけでは分からない（CLAUDE.md 12章「latitudeによるpixel面積差は値へ織り込み済みか」は未解決のまま）
- Bangladesh（BBOX `[87,20,93,27]`）の緯度帯（低緯度）は赤道に近く、上記の緯度差問題の影響は他地域より小さいと推定される（未検証の推定）

## 2026-09-19: DRAINED-AREA-CROPのライセンスは`CC-BY-4.0`（再配布・派生物の作成が許される）

`GET /collections/fao-gismgr:FAOSTAT:raster:mapsets:DRAINED-AREA-CROP`で確認。`license: "CC-BY-4.0"`。producerは"FAO-UN-FAOSTAT"（活動データの一次情報源はUNFCCCへの各国報告、FAO-UNFCCC間のMOUに基づき配布）。

CC-BY-4.0は表示（attribution）を条件に再配布・改変・再配布を許すライセンスであり、NC（非商用限定）やSA（継承）のような追加制約が無い。したがって、このcollectionをクロップして再配布する（`docs/derived/`計画）ことは、ライセンス上問題ない。attributionは組織単位（FAO/FAOSTAT、CC-BY-4.0へのリンク）で行い、collection metadataに列挙された個人の連絡先までは転記しない。

他のcollection（yuisekiのindexで確認済みの通り、CC-BY-SA-4.0・CC-BY-NC-SA-4.0等が混在）を再配布対象にする場合は、都度この確認をやり直すこと。

## 2026-09-19: `docs/Case2-GHG-BDG.html`実装中に発見した2件（Phase 1、STAC discovery実装）

### 短縮collection idはライブAPIで「エラーなく0件」になる

参照Notebookは`COLLECTIONS = "DRAINED-AREA-CROP"`という短縮idを`pystac_client`に渡している。この値をそのまま生のHTTP POST `/search`に使うと、**エラーにならず`numberMatched: 0`が返る**（400等にならないため気づきにくい）。GET `/collections`で確認したところ、正しい完全idは`fao-gismgr:FAOSTAT:raster:mapsets:DRAINED-AREA-CROP`だった（MVHI-Dで先に確認した規則性`fao-gismgr:<CATALOG>:raster:mapsets:<SHORT_ID>`と一致）。

`pystac_client`が内部で短縮idを解決しているのか、Notebook自体がこの検索で常に0件を返しているのかは未確認（Notebookの実行結果はリポジトリに含まれていないため検証できない）。ブラウザから生のSTAC APIを直接叩く実装では、**collection idは必ず完全形を使う**必要がある。

またAPIは`datetime`にRFC3339形式（`T`区切り、タイムゾーン付き）を要求する。日付のみの`"1992-01-01"`は400エラー（`invalid datetime separator`）になる。

### Case 2の単位・scale/offsetは、ラスターのメタデータではなくSTAC Itemのメタデータにあった

`gdalinfo`ではunit tagが見当たらなかったため前回「Notebookの列名からの推定にとどまる」と記録したが、実際のSTAC検索結果の`properties.cube:variables`と`assets.data.bands[0]`に明記されていた。

```
properties.cube:variables["drained-area-crop"].unit = "ha/y"
assets.data.bands[0]: { data_type: "float32", raster:scale: 1.0, raster:offset: 0.0, raster:spatial_resolution: 927.6624166662957, unit: "ha/y" }
```

CLAUDE.md 12章の「pixel値は面積haを表すか」「scale、offsetはあるか」は、これで**Notebookの列名からの推測ではなく、STAC自身のメタデータとして確認済み**に格上げできる。ただし「緯度によるpixel面積差が値へ織り込み済みか」は、`spatial_resolution`が緯度に依らない単一値（927.66m）として記載されている点から見て、未解決のまま（単一値である＝緯度補正なしの可能性を示唆するが、断定はできない）。

### 参考: `properties.datetime`はnull、`start_datetime`/`end_datetime`を使う

STAC ItemCollectionの`properties.datetime`は常に`null`。年の判定には`properties.start_datetime`（例: `"2022-01-01T00:00:00Z"`）を使う必要がある。

## 2026-09-19: yuiseki GeoParquet index、CORSとRangeは問題なし

対象: `https://stac.yuiseki.net/fao-ferspas/{collections,items}.parquet`

`curl`でOriginヘッダー付きGET/OPTIONS/Rangeリクエストを送って確認。

- `access-control-allow-origin: *`
- `access-control-expose-headers: Content-Length, Content-Range, Accept-Ranges, ETag`
- `Range: bytes=0-99`に対して`206 Partial Content`と正しい`Content-Range`を返す
- Cloudflare配信

Gate 2（STAC、代替経路B）は通過とみなす。

## 2026-09-19: duckdb-wasmで実ブラウザからの直接クエリに成功

素のHTML（サーバー処理なし、CDN経由でduckdb-wasmをESM import）から、上記2ファイルに対して以下を実行し、いずれも成功。

| クエリ | 結果 | 所要時間 |
|---|---|---|
| `collections.parquet`の件数 | 1921件 | 約2.7秒（wasm+worker初期化込み、コールドスタート） |
| `ST_Intersects`で札幌の点と交差するcollectionsを抽出 | AGERA5系など10件を正しく返した | 351ms |
| `items.parquet`(9.4MB)を`short_id/season/lct`で絞り込み | ASI-DのGS1/LC-Cを新しい順に3件取得 | 2.4秒 |

技術的にはブラウザ内実行が成立することを確認した。ただしコスト（下記）とのトレードオフは別途評価する。

## 2026-09-19: duckdb-wasmのブートコスト（jsdelivr、圧縮後）

- `duckdb-eh.wasm`: 非圧縮35.6MB、`content-encoding: br`で転送時約6.2MB
- `duckdb-mvp.wasm`: 転送時約6.9MB
- jsdelivr側は`cache-control: public, max-age=31536000, immutable`。初回のみのコストで、以降はブラウザキャッシュが効く想定（ただし政府執務PCのキャッシュ運用・毎回のプロファイルクリア設定等は未確認）

## 2026-09-19: FERSPAS STAC API自体もCORSが通る（想定の訂正）

対象: `https://data.apps.fao.org/geospatial/search/stac`

- GET（ルート）: `access-control-allow-origin: *`
- `/search`へのOPTIONSプリフライト: `access-control-allow-origin: *`、`access-control-allow-methods: OPTIONS, POST, GET`、`content-type`ヘッダーを許可
- 実際のPOST（`{"collections":["ASI-D"],"limit":1}`）: `200`、`access-control-allow-origin: *`、295 bytesのGeoJSONを返した

CLAUDE.md 23章（旧22章）で「未検証」としていた項目だが、少なくとも単発のsearchについては通ることを確認した。「CORSが通らないからGeoParquetが必要」という前提は誤りだったため、GeoParquet採用の理由づけをこの事実に合わせて修正する必要がある（`decisions.md`参照）。

## 2026-09-19: yuiseki indexの一次情報源（harvestコード）は現時点で確認できない

READMEは`Built by https://github.com/yuiseki/study-un-fao-ferspas`と記載しているが、GitHub API・検索、および想定される表記ゆれ（`study-fao-ferspas`、`un-fao-ferspas`、`fao-ferspas`）のいずれでも該当リポジトリが見つからなかった（すべて404、検索結果0件）。yuiseki本人の公開リポジトリ893件を全ページ走査しても`fao`/`ferspas`を含む該当リポジトリはない。

したがって次の点は**外部から検証できない**。

- harvestが自動化されているか（cron等のGitHub Actions workflow）、一度きりの手作業か
- 「The number of rows harvested per collection equals the count the API's aggregation endpoint reports」という検証済み主張の実装
- 更新頻度・次回更新の見込み

非公開リポジトリである可能性、リポジトリ名が変わった可能性、単純な記載ミスの可能性のいずれも排除できない。hfuのグローバル指示にある「技術的な事実主張は一次情報で裏を取ってから採用する」に照らすと、現時点でこのindexの鮮度・更新体制は**未検証のまま**として扱う。Case 1のような「最新のItem」を要する用途では、この点を検証済み事実として扱わない。

## 2026-09-19: 実アセット（COG本体）のCORS/認証は、Collectionごとに異なる形で壁がある

`items.parquet`の実データで、`data_href`・`data_gs_href`を実際に取得しcurlで検証した。**Case 1とCase 2で、詰まり方がまったく違う。**

### Case 1: ASI-D（`fao-gismgr-asis-data`バケット）

`data_href`（例: `https://storage.cloud.google.com/fao-gismgr-asis-data/DATA/ASIS/MAPSET/ASI-D/ASIS.ASI-D.2026-08-D2.GS1.LC-C.tif`）に匿名GETすると、Origin有無に関わらず**302でGoogleのログイン画面（`accounts.google.com/ServiceLogin`）へリダイレクト**される。CORSヘッダーも付いていない。

`data_gs_href`（`gs://fao-gismgr-asis-data/...`）をブラウザ用に`https://storage.googleapis.com/...`へ変換して試しても、

```
403 AccessDenied
Anonymous caller does not have storage.objects.get access to the Google Cloud Storage object
```

**バケットが匿名読み取りを許可していない。** ブラウザから資格情報なしでこのCOGを直接読むことはできない。9.3節「COGをブラウザで直接読める」という成功条件は、少なくともこのバケットの現状の権限設定では成立しない。

### Case 2: DRAINED-AREA-CROP（`fao-gismgr-faostat-data`バケット）

`data_href`は最初から`https://storage.googleapis.com/...`形式。匿名GET/Rangeともに`200`/`206`で**中身は読める**（`file_size`と一致するバイト数、`Accept-Ranges: bytes`、正しい`Content-Range`）。

しかし、レスポンスに**`Access-Control-Allow-Origin`ヘッダーが一切付いていない**（`vary: Origin`はあるが実際のACAOがない）。`curl`はCORSを見ないので読めてしまうが、**ブラウザの`fetch()`はこのレスポンスをJSに渡さない**（CORSエラーになる）。つまりcurlで「読める」ことと、ブラウザのCOGビューアで「読める」ことは別の問題であり、こちらは後者で詰まる。

### 含意

FAOの生バケットへブラウザから直接アクセスする経路（9.3/9.4、10.3/10.4が前提にしていた「A. source COG direct access」）は、Case 1・Case 2のどちらの実アセットでも、異なる理由で現状は成立しない。4.6/4.7・9.4/10.4で候補としていた「北海道向け派生COG（発行時にclipし、CORS対応で再ホスト）」は、望ましい選択肢の一つではなく、**現状ではほぼ必須の経路**である可能性が高い。Italy版（9.3）についても同様の検証が必要（未実施）。

## 2026-09-19: FAO内部の別Notebook事例（MVHI-D多年平均）も同じ壁にぶつかる（乗り換えでは解決しない）

FAO内部の別の実装例として提示されたNotebook（Afghanistan向け、MVHI-D多年平均を計算するもの。人物・リポジトリ名はここでは伏せる）を取得し、中身を確認した。

- 使用Collection: `MVHI-D`（正式ID: `fao-gismgr:ASIS:raster:mapsets:MVHI-D`）。ASI-Dと同じ「ASIS」プロダクトファミリー
- 決定的なコード: `gcs = gcsfs.GCSFileSystem(token="google_default")` — **FAOの認証済みGoogleアカウント（Application Default Credentials）でGCSに接続している**。匿名アクセスではない。実行パスもFAO内部のGCP VMを前提とした構成

実際にSTAC APIから最新のMVHI-D Itemを取得し、アセットURLを検証した。

```
data asset: https://storage.cloud.google.com/fao-gismgr-asis-data/DATA/ASIS/MAPSET/MVHI-D/...tif
→ 302でGoogleログイン画面へリダイレクト（Case 1のASI-Dとまったく同じバケット・同じ挙動）
```

**この事例が動くのはFAO内部の認証を使っているからであり、匿名ブラウザアクセスとは前提が異なる。** この例に乗り換えても、CORS/アクセス問題は解決しない。

## 2026-09-19: FAOのWMTS preview/thumbnailエンドポイントはCORSが緩い（部分的な代替経路）

上記の検証中に、STAC Itemの`preview`/`thumbnail`アセット（`data.apps.fao.org/map/wmts/wmts?...`、STAC APIと同じホスト）を試したところ、生COGとは異なる結果になった。

- 実際にGETするとPNG画像（500×500、RGBA）が返る
- `access-control-allow-origin`が**送信したOriginをそのまま反射する**。正規のOrigin（`https://dwg7.github.io`）だけでなく、でたらめな`https://example.invalid`でも同様に許可された。事実上、オリジンを問わず読める設定
- ASI-D・MVHI-Dいずれの`layer=`パラメータでも同様に機能した

ただし制約がある。

- `request=GetPreview`は固定サイズ（今回は500×500）の**全範囲1枚絵**であり、ズーム可能なXYZ/WMTSタイル配信（`GetTile`）に対応しているかは別途確認が必要
- 色はFAO側のpaletteで焼き込み済み。値ベースの分析（Case 2の合計等）には使えない。「地図に載せる」用途限定

「生COGは読めないが、FAOがレンダリング済みのPNGは読める」という構図。yuisekiのREADMEにある「previewとthumbnailは地図表示には十分」という記述と符合する。

## 2026-09-19: WMTSタイル配信の深掘り（部分的に確認、未完）

FAOのWMTSエンドポイント（`data.apps.fao.org/map/wmts/wmts`）について、`GetPreview`以外の挙動を追加確認した。

- `GetCapabilities`は**KVPの大文字小文字・パラメータを変えても一貫して応答しない**。1回目はCloudflare 524（オリジンタイムアウト、約100秒相当）、2回目は`curl --max-time 90`でも接続完了せず（`HTTP 000`）。このエンドポイントの`GetCapabilities`は現状壊れているか、極端に重いと判断してよい
- `GetTile`（標準WMTS KVP: `service=WMTS&request=GetTile&layer=...&tilematrixset=EPSG:4326&tilematrix=2&tilerow=1&tilecol=2&format=image/png`）は`400`。エラーメッセージが具体的で有用: `{"detail":"Missing 'GetTile' parameters: {'version'}"}` → `version`パラメータを追加すると次は`{'version', 'style'}`が必要と言われた。つまり**`GetTile`自体は実装されている**が、正しいパラメータ一式（少なくとも`version`、`style`）が必要で、今回はそこまで詰め切れなかった

結論: 「ズーム可能なタイル配信」への対応可否は**まだ確定できない**。`GetCapabilities`に頼らず、`version=1.0.0`や`style=default`等の一般的なWMTS既定値を総当たりで試せば`GetTile`が成功する可能性は高いが、次回への持ち越しとする。`GetPreview`（全範囲1枚絵、CORS良好）は確認済みの代替として使える。

## 2026-09-19: Case 1/2/12のItem選択ロジックを、生データに触れずメタデータのみで再現（寸止めモード）

yuisekiのGeoParquet indexに対するDuckDBクエリだけで、3つのNotebook/HTMLケースの「Item選択」ロジックをすべて再現・検証した。ラスターは一切取得していない。

### items.parquetの実スキーマ（未記載だった点の訂正）

`DESCRIBE`で確認したところ、`items.parquet`は7章で書いた列に加えて次を持つ。

- `start_datetime`/`end_datetime`は最初から`TIMESTAMP`型（epoch msの`BIGINT`ではない）。`strftime()`がそのまま使える
- `bbox STRUCT(xmin, ymin, xmax, ymax)`と`geometry GEOMETRY`を**item単位でも**持つ（7.4節では「collections.parquetのみ」と誤って読める書き方をしていたため、9章の実装時に参照すること）
- `gismgr_item_id`はFAOの旧ドット区切り形式（例: `fao-gismgr/ASIS/mapsets/MVHI-D/ASIS.MVHI-D.1984-01-D1.GS1.LC-C`）。上記Notebook事例のregex（`item.id`に対して`^ASIS\.MVHI-D\.(\d{4})-...`）は、pystac-clientの`item.id`＝この`gismgr_item_id`と同じ形式に一致する。yuisekiの`id`列（`fao-gismgr:...:items:ASIS-MVHI-D-...`、コロン/ハイフン区切り）とは別物なので、Notebookのregexをそのまま移植する場合は`gismgr_item_id`を見る

### Case 1（ASI-D）: 「最新のGS1/LC-C Item」

```sql
SELECT id, start_datetime, data_href FROM items
WHERE short_id='ASI-D' AND season='GS1' AND lct='LC-C'
ORDER BY start_datetime DESC LIMIT 1
```

→ `ASIS-ASI-D-2026-08-D2-GS1-LC-C`（前回の実測と一致）。61ms。同日には`GS1/GS2 × LC-C/LC-G`の4組み合わせが揃って存在することも確認した。

### Case 2（DRAINED-AREA-CROP）: 「1992–2022の年別Item」

```sql
SELECT count(*), min(start_datetime), max(start_datetime) FROM items
WHERE short_id='DRAINED-AREA-CROP'
```

→ **31件、1992-01-01から2022-01-01まで、欠年なし**。CLAUDE.md 11.1に書いた「Notebook冒頭コメントは2020年までだが実際は2022年まで」という記述の年range自体は、この結果で裏付けられた。

### Case 12（FAO内部別事例、MVHI-D）: 「dekad-phase × season × LC-Cで年をグルーピングし多年平均」

- `season × lct`の4組み合わせ（GS1/GS2 × LC-C/LC-G）は**すべて1535件で完全に一致**（1984-01-01〜2026-08-11）。欠損組み合わせなし
- GS1×LC-Cを月-dekadのphase（例: `01-D1`）でグルーピングすると、**36フェーズすべてが存在し、`01-D1`〜`08-D2`は43年分、`08-D3`〜`12-D3`は42年分**（2026年がまだ8月D2までしか到達していないための差で、説明がつく欠け方であり、データ欠損ではない）
- Item自体のbboxは`xmin=-180, ymin=-56.0, xmax=180.0, ymax=75.0`と**ほぼ全球**。上記Notebook事例が指定していた`BBOX=[60, 29, 75, 39]`（アフガニスタン）は、STAC検索の時点では実質的に何も絞り込んでいない（どのItemも全球なのでbbox交差判定は常に真）。実際のアフガニスタンへの絞り込みは、ダウンロード後の`rasterio.mask`でローカルに行われている

この最後の点は北海道版にも直接効く。ASISファミリーのようなグローバルdekadalプロダクトでは、**Item発見の段階でAOI（北海道）によって絞り込む必要はなく、絞り込みは常に「対象範囲内の処理」の段階で行う**、というCase 1 Hokkaido（10.4）の設計判断を裏付ける根拠になった。

## 2026-09-19: `stars.optgeo.org`エコシステムの現状（dwg7/cafebabe横断知見より）

hfu個人のグローバル指示にある「複数プロジェクトに横断する技術的知見はdwg7/cafebabeにある」に従い、`gh`でdwg7/cafebabeと`hfu/stars`を直接読んで確認した（cafebabeの稼働セッションは見当たらなかったため、リポジトリを直接読む方の手順）。

### `stars.optgeo.org`は外部ではなくhfuさん自身のインフラ

`hfu/stars`リポジトリの「タイルサーバー（stars.optgeo.org）のゲートキーパー」。Raspberry Pi 4上でMartin（タイルサーバー）+ cloudflared（Cloudflareトンネル）を動かす。`stars-fd`というセッションがゲートキーパー役。

### Martin自体はCOGを配信できない（設計上は対応、本番は未対応）

`hfu/stars`の`README.md`/`docs/KNOWN_FACTS.md`/`docs/COG_COMPATIBILITY_NOTES.md`を確認したところ、次が明記されている（2026-08-28〜2026-09-15の複数時点で確認済みとされる一次情報）。

- MartinのCOGサポートは`unstable-cog`という非デフォルトのCargo featureで、**本番のMartinバイナリ（v1.14.0）には組み込まれていない**。「バージョンを上げてもCOGサポートは有効にならない」と明記
- 実際、`abidjan.tif`というCOGファイルが「デプロイされていない、本番MartinにCOGサポートがまだないため」とKNOWN_FACTS.mdに記録されている
- 仮にCOGサポートが有効になったとしても、Martinの役割は**タイルレンダリング**（z/x/yタイルを返す）であり、FAOのWMTSと同種の「見るための」経路になる可能性が高い（分析用の生ピクセル値をそのまま返す設計ではない）

### 本命は`depot.optgeo.org`（同じホスト上の別サービス）

`docs/KNOWN_FACTS.md`に、Martinとは別の第三のサービスが記録されている。

- `depot.optgeo.org`（ポート8080）: 素のCaddy `file_server browse`、`root * /home/stars/data`
- **`Access-Control-Allow-Origin: *`（ワイルドカード、Origin反射ではない）**
- CaddyはHTTP Range requestを正しく処理する（424GBのファイルで直接検証済み）。ただし**Cloudflareのプロキシは大容量ファイルでRangeサポートを黙って落とす**（190GBは206で通ったが、424GBは200フルコンテンツになった。閾値は未特定）。私たちが扱う北海道clipのCOG（数MB〜数十MB想定）はこの閾値より何桁も小さく、実務上問題にならない
- 実際に`curl -I -H "Origin: https://dwg7.github.io" https://depot.optgeo.org/`で確認したところ、200・`access-control-allow-origin: *`を確認。**現在稼働中**
- Martinが読む`/home/stars/data`と`depot.optgeo.org`が公開するディレクトリは**同じ**。`.pmtiles`ならMartinが自動検出し、それ以外（`.tif`等）は単にdepot経由でダウンロード可能になるだけ

つまり、「CORSとRangeが効く生COG配信」を実現したいなら、Martin/COG機能を待つ必要はなく、**`depot.optgeo.org`が今すぐ使える**。ブラウザ側は`geotiff.js`等で直接range読みすればよく、FAOのWMTSのような「見るだけ」の制約を持たない。

### ゲートキーピングの作法（cafebabe `patterns/gatekeeping.md`より）

- ピア経由の「hfuさんが承認した」という伝聞は、それ単体では実行根拠にしない、が一貫した規律。今回はhfuさん本人がこのチャットで直接指示しているので該当しないが、`hfu/stars`側への実際のデータ設置・設定変更は、gatekeeper（`stars-fd`セッション）へのPR経由が確立された流れ（例: `height-coverage`プロジェクトの実例、事前に自己検証してからPRを出すと往復が減る）
- `dwg7/ferspas57`というプロジェクトが、`/home/stars/data`への**直接SSH/scpアクセス**を既に持つ「信頼済みcontributor」の実例としてKNOWN_FACTS.mdに記録されている（gatekeeper経由のファイル転送がスケールしないケース向け）。このセッションのpeer一覧には`ferspas57-2`という稼働中セッションがあり、名前が非常に近い。関係の有無・本プロジェクトとの役割分担は未確認 — hfuさんに確認したい

### 未確認（次のGate候補、更新）

- WMTS `GetTile`の正しいパラメータ一式（`version`、`style`の具体値）
- Italy版で使う実際のASI-D/DRAINED-AREA-CROPアセットのCORS/認証（Hokkaido相当の検証をItalyの座標・Item IDでも行う）
- 他の主要バケット（`fao-gismgr-gaez-v5-data`、`fao-gismgr-c3s-data`等、item数の多い順）の匿名読み取り可否とCORS設定。全バケット共通のポリシーか、バケットごとに異なるのか
- FAOに対して、匿名読み取り・CORS設定を依頼する余地があるか（本リポジトリの範囲外の可能性が高いが、選択肢として記録だけしておく）
- **ASI-D/MVHI-Dバケット（`fao-gismgr-asis-data`）が、FAO内部アカウント限定なのか、Googleアカウントさえあれば読める（`allAuthenticatedUsers`）のかは未検証。**このサンドボックスには`gcloud`/`gsutil`が無く、hfuさん個人のGoogle認証も持っていないため、Claude自身では検証できない。hfuさん自身の端末で`gcloud auth login`済みの状態から読み取りを試す、またはhfuさん自身のブラウザ（ログイン済み）で`https://storage.cloud.google.com/fao-gismgr-asis-data/...`を開く、のいずれかで確認可能
- `dwg7/ferspas57`とこのプロジェクトの関係
- `/home/stars/data`への書き込み方法（gatekeeper経由PR／既存の信頼済みアクセスの有無）

## 2026-09-19: Bangladesh 31年分のチェックアウトを実施（local foundationモデルの最小PoC完成）

`scripts/checkout-Case2-GHG-BDG.py`で、STAC検索→実Bangladesh国境（Natural Earth 10m admin-0、Public Domain）でのcutlineクロップ（投影変換なし）→合計値計算、を31年分すべて実行した。

- 出力: `docs/Case2-GHG-BDG/derived/BGD-<year>.tif`（COG、31ファイル合計約1.8MB）、`timeseries-BGD.json`、`provenance-BGD.json`
- 合計値は323,520〜339,783 ha/年の範囲。1992〜1994年は完全に同一の値（338844.51 ha）——原資産側の特性とみられる（活動量データの後方補完等）が未確認
- 各ファイルのvalid pixel数は174,739で全年一致（同一グリッド、CLAUDE.md 12章の懸念は解消）
- ページ（`docs/Case2-GHG-BDG/index.html`）から`geotiff.js`でこの派生COGを直接読み、canvasへ着色表示、時系列はSVGで描画。実機で動作確認済み（Bangladeshの国土形状が正しく表示され、北西部に排水耕地が集中している様子が見える）

### ローカル検証時の落とし穴: Python `http.server`は同時リクエストで取りこぼす

`geotiff.js`はCOG読み取りのために複数のHTTPリクエストを発行する。Pythonの`python3 -m http.server`（シングルスレッド）でテストすると、年を切り替えるたびに`Request failed`が断続的に発生した。Node製の`http-server`（並行処理対応）に切り替えると同じ操作が安定して成功した。**これはローカル検証環境固有の問題であり、GitHub Pages等の本番CDNでは発生しないと考えられる**が、今後同種のページをローカルでテストする際は`python3 -m http.server`ではなく並行処理対応のサーバーを使うこと。
