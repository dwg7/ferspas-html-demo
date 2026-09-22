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
- ~~ASI-D/MVHI-Dバケットが個人Googleアカウントで読めるか~~ → **解消済み（2026-09-19）**。hfuさん個人のアカウントで読めることを実測確認した（後述のエントリ参照）
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

## 2026-09-19: 空間IDタイル（4-14-5）版のチェックアウトを実施・動作確認

`scripts/checkout-Case2-GHG-4-14-5.py`で、slippy-map tile `z=4/x=14/y=5`（東経135.0〜157.5°、北緯40.98〜55.78°）を矩形クロップ（cutlineマスクなし、`gdal.Translate`の`projWin`のみ）して31年分チェックアウトした。

- 出力: `docs/Case2-GHG-4-14-5/derived/4-14-5-<year>.tif`（2700×1777px、31ファイル合計約4.1MB）、`timeseries-4-14-5.json`、`provenance-4-14-5.json`
- 合計値は約123,562〜131,071 ha/年。Bangladesh版と異なり1992〜1994年は同一値にならず、2002年頃から2017年頃にかけて緩やかに減少した後、2018年以降に増加へ転じるという、より複雑な推移を示す
- 境界マスクを行わないため、矩形内は全ピクセルが実データ（NoDataは一切発生しない）。地図はHokkaidoと樺太の輪郭が薄く視認でき、農地の集中箇所（Bangladesh版と同じ北海道北西部相当の位置）も確認できた
- ページ（`docs/Case2-GHG-4-14-5/index.html`）を並行処理対応のローカルサーバー（`npx http-server`）で実機確認。STAC discovery（31件）・地図表示（963ms）・時系列表示すべて正常に動作

## 2026-09-19: Case 1（ASI-D）のTier B問題、hfuさん個人のGoogle認証で解消を確認

前回「未検証」としていたASI-D/MVHI-Dバケット（`fao-gismgr-asis-data`）の認証範囲を、hfuさん自身の個人Googleアカウントで実際に検証した。

### 手順と結果

1. `https://storage.cloud.google.com/fao-gismgr-asis-data/DATA/ASIS/MAPSET/ASI-D/ASIS.ASI-D.2026-08-D2.GS1.LC-C.tif`をhfuさんの個人Googleアカウントでログイン済みのブラウザで開いたところ、**ダウンロードが成功**。取得したファイルは42,741,842バイトで、STAC側のメタデータ（`file:size`）と完全一致。`gdalinfo`で有効なCOG（`LAYOUT=COG`、EPSG:4326、NoData=255、Float32、overview 7段）であることも確認した
2. このセッションに`gcloud`（Google Cloud SDK）をインストールし、`gcloud auth application-default login`でApplication Default Credentials (ADC)を設定
3. 初回・2回目の試行は`ERROR: ...cloud-platform scope is required but not consented`で失敗。原因はOAuth同意画面で権限（スコープ）のチェックボックスを選択していなかったことだった（hfuさん本人が確認）。3回目、同意画面で明示的に選択して成功
4. `GOOGLE_APPLICATION_CREDENTIALS`環境変数でADCを指定し、GDALの`/vsigs/`（Google Cloud Storage仮想ファイルシステム）経由で`gdalinfo`を実行したところ、**ASI-Dの同じアセットを認証付きで正常に読めた**

### 含意

- Tier B（匿名読み取り拒否）は、FAO内部限定ではなく、**個人のGoogleアカウントでも読める**ことが実測で確認された（少なくともこのバケット・このアセットについて）。`allAuthenticatedUsers`相当の権限が付与されている可能性が高い
- したがって、Case 1もCase 2と同じ「発行時にhfuさんの認証でチェックアウトし、CORS対応で再配布する」パターンに乗せられる。FAO CSIとの相談を待つ必要は、少なくとも技術的な意味では無くなった
- ただし、チェックアウトスクリプトの実行には認証情報（ADC）が必要なため、Case 2のスクリプトと異なり、**hfuさんの認証済み環境（このセッションを含む、ADC設定済みの間）でしか動かない**。この制約は provenance に明記する

## 2026-09-19: `docs/Discover-4-14-5/` — GeoParquetによる「AOI×全コレクション横断発見」を実装

「一定のAOIについて、大量の組み合わせを分析して意味を引き出す」という方向性を、単一Collectionの発見方法をLive APIからGeoParquetへ置き換えるだけでなく、**Live APIでは実質不可能な横断発見**として実装した。

### 実測結果（AOI: tile 4-14-5、`docs/Case2-GHG-4-14-5/`と同じ）

- ブラウザ内DuckDB-Wasmで`collections.parquet`（1921件）を検索。起動2386ms、クエリ2768ms（初回、コールドスタート込み）
- **379件がAOIに交差**。うち286件は純粋な全球カバー、**93件は全球ではないのにこのAOIに関係する**collection（地域限定プロダクトがこれだけ埋もれていたということ）
- カタログ別内訳: GAEZ-V5が126件と突出。WAPOR-3（44）、C3S（23）、ASIS・FAOSTAT（各14）と続く
- `bbox`列（`STRUCT(xmin,ymin,xmax,ymax)`）だけで矩形重なり判定ができ、**空間拡張機能（spatial extension）のインストールが不要**だった（footprintが矩形として記録されているため、bbox比較がST_Intersectsと等価）。前回の実装より若干シンプルになった
- 実演: 検索ボックスに"stress"と打つと、ASI-A/ASI-D（お馴染みのASISファミリー）に加えて、**GDVIカタログの"ENV-LWS"（Level of water stress）という、これまで一度も触れていないcollection**が3件中に出てきた。これがまさに「問いが育つ観察」——単一Collectionの深掘りでは出会えない

### 技術的な感触（比較）

- Live STAC APIでこれと同じ「1921件のうちこのAOIに関係するのはどれか」を調べようとすると、collection一覧を取得した上で1921回の個別問い合わせが必要になり、実務上できない
- 一方、単発の「Collection Xの最新Itemを1件」のような検索は、今回もLive APIの方が圧倒的に軽い（前回の実測: 295 bytes vs 6MB超のwasm起動）。この非対称性は前回の結論通りで、今回の実装でも覆らなかった
- 結論: GeoParquet+DuckDBは、**個別の検索を代替する技術ではなく、Live APIには無い「横断発見」という新しい機能を追加する技術**として位置づけるのが正しい

## 2026-09-19: `items.parquet`（64万行）へのitemレベル絞り込みを実測 — collectionレベルの発見を裏付けたが、空間的な追加絞り込み効果は無かった

`duckdb` CLIをローカルにインストールし（`brew install duckdb`、v1.5.5）、`docs/Discover-4-14-5/`と同じAOI（tile 4-14-5）で`items.parquet`（639,947行）に対する実測を行った。

### 素朴な全item bboxフィルタは実質無意味

`items.parquet`全体（フィルタなし）に対しAOIとのbbox交差だけで絞ると541,674/639,947件（85%）がヒットする。ASI-D等の全球dekadalプロダクトはitem自体がほぼ全球（CLAUDE.md 7.4節既知）であるため、item全件に対する素朴な空間フィルタは「ほとんど全部当たる」だけで発見の役に立たない。

### collectionレベルのbboxフィルタは、item実データと完全に一致していた（相互検証）

`catalog, short_id`でGROUP BYし、「collectionの declared bbox がAOIと交差する」（=前述の379件）という判定を、「実際にそのcollectionのitemでAOIと交差するものが1件以上あるか」という実データと突き合わせた（全1921件横断、実行1.4秒）。

- false positive（collection bboxは交差主張だが実item は0件交差）: **`GAEZ-V5:RES01-RFM-TS`の1件のみ**。ただしこれは`item_count=0`（そもそもitemが1件も無い空collection）が原因で、AOI判定自体の誤りではない
- false negative（実itemはAOIと交差するのにcollection bboxが交差と言っていない）: **0件**
- したがって、`collections.parquet`のbbox列は、実質的にitem bboxの正確な合併（union）になっている。379件という発見結果の信頼性はこれで裏付けられた

### 379件のヒットcollectionは、item単位で見ても「全部当たるか全部外れるか」の二値だった

379件それぞれについて「全item数」と「AOIに交差するitem数」を比較したところ、**一致しないケース（部分的にしか交差しない、＝タイル/地域分割されたcollection）は0件**だった。つまりこのAOI・このデータセットの範囲では、item単位のbboxフィルタは空間的な絞り込みとして追加の情報を持たない（collectionレベルの判定だけで十分だった）。GeoParquetの「item単位でも高速に絞り込める」という強み自体は実証されたが、この用途（空間的発見）には効かなかった、という否定的だが明確な結果。

### item単位クエリの別の価値: 時間的密度とvariant構造の可視化

空間的な絞り込みには効かなかった一方、collectionを1つ選んでitemを深掘りするクエリ（`catalog`/`short_id`で絞り込み、`year`別件数・`season`/`crop`/`depth`等dims列のdistinct数を集計）は実用的な速度で動く。

- ASI-D（4,268 items）: ローカルduckdbで0.52秒、ブラウザduckdb-wasmで60ms（2回目以降のクエリ、パースキャッシュ済み）
- 379件中、最大のitem数はC3S/AGERA5-RH18の17,197件。これでも数百ms〜1秒程度で収まる見込み
- この深掘りにより、「そのcollectionが実際に何年分・どんな変種（dims軸）を持つか」という、collection一覧だけでは見えない問いに答えられる。例: SPAM2020-PHYSICAL-AREAは138 item全てが1970年（代表値）でcrop次元46種、ASI-Dは1984〜2026年まで年72件ずつ均等に存在、season/lct各2種

`docs/Discover-4-14-5/`に、collection行をクリックすると上記の深掘りクエリを実行する機能を実装・動作確認した（2026-09-19）。

## 2026-09-19: DRAINED-AREA-CROPは衛星観測ではなく、国別統計（UNFCCC報告値）の空間按分だった

Case2ページの「この数値が何を意味するか」を書く過程で、Live STAC APIの`GET /collections/fao-gismgr:FAOSTAT:raster:mapsets:DRAINED-AREA-CROP`から正式な`description`と`processing:lineage`を取得して確認した。

- `description`: "The 'Greenhouse Gas (GHG) Emissions from Drained Organic Soils' dataset describes and disseminates the geospatial data from which FAOSTAT statistics on drained organic soils are derived."
- `processing:lineage`: "Activity data are sourced from the most recently available GHG National Inventories (NGHGI) or from National Communications."（＝各国がUNFCCCへ報告した国別統計が一次情報源）

「Remote Sensing Portal」という名称にもかかわらず、この特定のcollectionは**衛星による直接観測ではなく、国別統計を何らかの代理変数（耕地分布等）で空間的に按分（ダウンスケール）したもの**であることが確定した。

### 裏付け実験: 北海道の画素値を1992年と2022年で比較

`gdal.Translate`で北海道bbox（139.5–145.9°E, 41.3–45.7°N）を2時点切り出し、画素ごとの比率を計算（`/tmp/check_hokkaido_ratio.py`、python3.14+gdal）。

- 地域合計はほぼ不変（53,112ha → 52,615ha、-0.9%）
- しかし両年とも非ゼロの画素5,519個に対する比率は0.26倍〜3.8倍とバラバラ（変動係数0.30）
- 合計が動かないのに個々の画素が大きく再配分されているのは、実際の土地利用変化というより、**FAOの空間按分モデルが使う代理レイヤーの更新による再配分**である可能性が高い

### 参考: Bangladesh（国全体スケール）での変動の大きさ

`derived/timeseries-BGD.json`の実データで検証すると、31年間の典型的な年々変動は±0.2〜0.4%程度、31年間の全体変化は338,845ha→323,521ha（-4.5%）。国全体スケールでは滑らかで、ノイズより大きい実質的なトレンドと見てよい。ただし国別統計を面積按分しているだけなので、**市区町村のような細かい空間単位に分解しても、その単位で独立に観測された値にはならない**（国全体シェア×国全体トレンドを再配分しているだけの可能性が高い）。

## 2026-09-19: `collections.parquet`のbboxは、実際にはプレースホルダーの全球値であることが多い（客観性・実用性の横断調査中に発見）

「FERSPASの中で客観性・値分解能・実用性が高いcollectionは何か」をduckdb CLIで横断調査する過程で、AOI（4-14-5）に交差する379件のうち**275件（36カタログ中25カタログ）が、厳密に`bbox = (-180, -90, 180, 90)`という値**を持つことを発見した。

これは真に全球規模の製品（GAEZ-V5、C3S、CRU等）と、**実際には一国・一地域限定なのにbboxが設定されずデフォルトの全球値のままになっている製品**（例: `HIH:GAB-SCORE-CLOSED`＝ガボンの養殖適地スコア、`WATER:K2-I`＝インド・カルナータカ州の遮断蒸発量。いずれも`bbox`は文字通り`(-180,-90,180,90)`）の両方を含む。descriptionを読まない限り、bboxだけでは両者を区別できない。

`docs/Discover-4-14-5/`が報告する「286件が全球カバー」は、bbox基準としては正しいが、**その中に北海道と無関係な国別プロダクトが紛れ込んでいる**ことを意味する。「93件は全球ではないが交差」の方はこの問題の影響を受けない（真に狭いbboxを持つcollectionのみ）。

対応: collectionを実際の候補として扱う前に、`title`/`description`が特定の国・地域名を含んでいないか目視確認する必要がある。bbox列だけを信じてはならない。

## 2026-09-19: FERSPAS 1921コレクションのうち、客観性・値分解能・実用性の観点でAOI(4-14-5)に関係する候補をCLIで横断評価

`collections.parquet`の`description`/`unit`/`class_count`/`item_count`/`update_frequency`列を使い、AOIに交差する379件（36カタログ）についてカタログ代表列を読み比べた（duckdb CLI、上記bboxプレースホルダー問題を踏まえ、国名を明記したカタログ・collectionは評価対象から除外）。

評価軸: 客観性（衛星観測等の直接測定か、統計の按分・モデル出力か）、値分解能（連続値か分類値か、空間・時間解像度）、実用性（北海道の農政・防災等に直接使えるか）。

| Collection | 客観性の根拠 | 値分解能 | 実用性 |
|---|---|---|---|
| ASIS `ASI-D` | 衛星ベース農業干ばつ監視（NDVI/LST由来）。既に本リポジトリで実証済み | %、10日おき、1984〜2026年、4,268件 | 高（作物ストレス監視） |
| C3S `LCCS` | ESA CCI由来の土地被覆分類（衛星ベース、国際的に確立） | 22クラス、年次、数十年分 | 高（土地利用の基礎図） |
| CHIRPS `EWX-GP-A` | 衛星+地上観測局のブレンド降水量 | mm、5km、3,282件 | 高。ただし実務上の有効範囲は南北50°まで（北海道41〜45°Nは範囲内） |
| AQUASTAT `ARDT` / CRU `PET-A` | CRU気候データの物理式（決定論的） | 粗い（10分角≈18km） | 中（水収支の補助指標） |
| GAEZ-V5 `RES02-YLD` | 農業気候ポテンシャル収量モデル（観測ではないが手法は公開） | 10km、13,568件 | 中〜高（モデル出力である旨の明示が必須） |
| WorldPop `WPOP-GLOBAL2-D` | 衛星居住地レイヤー+国勢調査のハイブリッド | 年次2015-2030 | 中 |

暫定結論: **ASIS(`ASI-D`)を次の深掘り候補とする**。衛星ベースで客観性が高く、10日おきという高い時間分解能を持ち、既に本リポジトリで技術的に触れている。

ステータス: 評価完了。ASI-Dの探索的深掘りへ進む（`docs-internal/decisions.md`参照）。

## 2026-09-19: ASI-Dを探索的に深掘り — 客観性は裏付けられたが、値の粒度と欠測パターンに要注意点あり

`GET /collections/fao-gismgr:ASIS:raster:mapsets:ASI-D`で正式なdescription・band・cube:dimensions・supplemental_informationを取得し、さらに実際の画素値（hfuさんのADC経由、`/vsigs/`）で検証した。

### 客観性: 裏付けられた

descriptionによれば、ASIはVHI（Vegetation Health Index、NDVI+地表面温度由来の衛星指標）を時間・空間の2段階で集計したもの。「アドミニストレーティブエリア内で、VHI<35%となる耕地pixelの割合」という記述があり、**行政単位ごとに一枚岩の値になっている可能性**を懸念して実測で検証した。

実測（2026-08-D2、GS1/LC-C、Hokkaidoのbbox 139.5–145.9°E, 41.3–45.7°Nをクロップ）:
- 粗いASCIIマップで可視化した結果、値の変化は行政界のような直線的境界ではなく、**農地の自然な輪郭に沿った有機的なパターン**だった（`/tmp/check_asis_viz.py`）
- したがって、descriptionの「administrative area」という表現は集計の一段階を指すに過ぎず、**配布されるラスター自体は行政単位の一枚岩ではない**と判断してよい

### 値の粒度: 0.5%刻み、24種類のみ（Hokkaido全体で）

実データの値域は0〜40（%）、0.5刻みで24種類の値のみが出現した。連続値というより、何らかの窓（moving window）内でのカウント/N×100という計算による量子化と推定される（未確認。ASIS公式ドキュメントでの確認が必要）。「1kmグリッド」という名目解像度より、実質的な情報の粒度は粗い可能性がある。

### 欠測・マスクパターン

Hokkaidoのbbox全体（353,974px）のうち、実際の数値（0〜100）を持つpixelは52,837px（15%）のみ。残りはセンチネル値:
- 255: 227,000px（64%） — 水域（海）
- 254: 70,416px（20%） — 非農地/非草地としてマスク
- 251〜253: 少数 — 季節外・データ不足等

これは「Hokkaidoの大半が海」という地理的事実と整合するが、**時系列を作る場合は季節・作期（GS1/GS2）・土地被覆（LC-C/LC-G）の組み合わせ次第で有効pixel数が大きく変動する**ことを意味する。単純に「北海道の平均ASI」を出すと、対象期間や作期の選び方次第で意味が変わりうる。

### メタデータの矛盾（要注意）

STACの`classification:classes`（251=off_season, 252=no_data, 253=no_seasonality, 254=no_cropland_or_no_grassland, nodata=255）と、`supplemental_information`の自由記述（255=water, 254=masked, 253=no season, 252=insufficient data, 251=incomplete season）が、**同じコード値に対して異なる説明**を与えている。両者はおおむね近い意味だが、正式なnodata値が255なのか252なのかで解釈が割れる余地がある。実務上は「0〜100の範囲外は全てセンチネル値として除外する」という扱いで十分だが、正確な意味づけが必要な場合はFAO GIEWSへの確認が要る。

### 暫定評価

DRAINED-AREA-CROP（国別統計の空間按分）と異なり、ASI-Dは**実際に細かい空間情報を持つ、客観性の高いデータ**と判断できる。ただし「1kmグリッド」という名目解像度をそのまま「1km単位で意味のある情報」と読み替えるのは早計で、実質的な粒度（0.5%刻み、window集計）を踏まえた上で使う必要がある。季節・作期・土地被覆の3次元（GS1/GS2×LC-C/LC-G）をどう扱うかも、Case実装前に決める必要がある。

## 2026-09-20: ASIS（VCI/TCI/VHI/MVHI/ASI）を実際に使っている人・機関の調査

ASI-Dの計算方法（NDVI由来のVCI、地表面温度由来のTCI、その合成であるVHI、作期加重平均のMVHI、閾値通過率のASI）を理解した上で、「この指標系は誰が、どのような立場で使っているのか」を調べた（general-purposeサブエージェントによるWeb調査、2026-09-20）。特定の機関・専門職・国の取り組みを優劣で評価する意図はなく、事実関係の把握を目的とする。確度は元の調査での区分（裏付けあり／推測だが妥当／根拠見つからず）をそのまま引き継ぐ。

### 実際の利用者層（裏付けあり）

VCI/VHI/ASIのようなKogan法由来の指標は、FAO GIEWS自身に加え、NOAA STAR（Koganの原型を今も公開）、EUのJRC（ASAPという類似指標）で運用されている。GEOGLAM Crop Monitorは、USDA・NASA・FEWS NET等およそ44の国別パートナー（**日本もその一つ**）が合議で作る月次コンセンサスレポートであり、個別の指標手法の上位に位置する集約機関として機能している。

これらの実際の利用者は、圃場の生産者や普及指導員というよりも、**国際機関・各国政府の早期警戒業務にあたる分析担当者**であるという構図が見えた。

### 日本国内の状況（裏付けあり）

日本の「作況指数」は、農林水産省が実際に圃場を無作為抽出し収穫・調製して算出する**実地調査に基づく統計**であり、衛星由来のデータとは別系統である。農研機構等による衛星リモートセンシングの研究（例: 北海道米のタンパク含有量マッピング）は別途進んでいるが、公式統計への組み込みは確認できなかった。JAや民間（Sagri等の事業者を含む）による衛星活用事例も見つかったが、いずれもNDVIを直接使うもので、Kogan法のVCI/TCI/VHIという合成手法を採用している例は見つからなかった。

### 手法上の位置づけ（裏付けあり）

VHI/ASIはFAOの運用上の標準として定着している一方、研究の最前線は土壌水分・蒸発散に基づくESI（Evaporative Stress Index）や太陽誘起蛍光（SIF）など、より早期に生理的ストレスを検知する手法へ移っている。成熟し安定した手法ではあるが、最新の研究動向そのものではない。

### 市場との関係（裏付けあり、間接的な傍証）

米国農務省のWASDE（作物需給報告）は、過去の情報漏洩事案を背景に、発表前の物理的隔離・通信遮断という厳格な管理体制を敷いている。一方、FAO GIEWS/ASISの公開には、これに類する管理体制は確認できなかった（通常のウェブ公開のみ）。この違いは、ASIS系の指標が市場へ与える影響の度合いについて、間接的な手がかりになりうる。なお、これとは別に、商業衛星ベンダーがNDVI由来の予測情報を投資家向けに提供する動きも確認されており、こちらは別の文脈として区別する必要がある。

### 林業との対比（裏付けあり）

隣接領域として林業の衛星活用を調べたところ、Global Forest Watchの伐採検知アラートは、複数国の行政機関へ配信され取り締まりにも使われるなど、農業分野のVHI/ASIより統合が進み、社会的な影響も大きい事例として確認できた。専門家と実務者の間の緊張関係を示す具体的な事例は見つからなかった（調査が及ばなかった可能性もある）。

### 訂正: モンゴルの家畜リモートセンシングに関する記憶

事前に共有されていた「モンゴルで家畜を衛星で数えようとしたところ、関係者に警戒された」というエピソードについて調査したところ、モンゴルの家畜保険制度は衛星NDVIではなく政府の家畜センサス（1920年代から実施）に基づくものであることが分かった。NDVIに基づく家畜保険はケニアの事例に近い。モンゴルで実際に確認されている懸念は、保険という仕組み自体が「災害への賭け」のように感じられることや、伝統的な相互扶助の仕組みを代替してしまうことへの懸念であり、衛星による監視そのものへの警戒とは異なる可能性が高い。記憶に基づく引用は、時間が経つと別の事例と混同されうるという一例として記録しておく。

### この調査を踏まえた探索の位置づけ

この調査の目的は、日本の農業水準を引き上げることではない。**グローバルな早期警戒システム（FAO ASIS）が、担当区域（北海道）という、独自の統計・流通インフラを既に持つ場で何を意味し、何を意味しないかを検証すること**である。今後のCase設計は、この枠組みを踏まえて行う（`docs-internal/decisions.md`参照）。

## 2026-09-21: 降水量・基準蒸発量（C3S AgERA5）の候補調査

Case 3（水収支）実装に向けて、`collections.parquet`を降水量・蒸発量関連キーワードで検索した（duckdb CLI）。

- FAO `WATER`カタログには、特定の流域向けに完成品の「Precipitation minus (actual) evapotranspiration」コレクションが既に存在する（`MNG1-P-ET`セレンゲ川/モンゴル、`NIGER-P-ET`、`NILE-P-ET`、`PHL1-P-ET`ミンダナオ、`TER-P-ET`チグリス・ユーフラテス）。いずれも実座標（プレースホルダーではない）で、日本を含む流域は無い
- グローバルカバーの候補として、C3Sカタログの`AGERA5-PF-A`（降水量、mm/year、0.1度格子、年次、1979–2025年、47件）と`AGERA5-ET0-A`（基準蒸発量、同格子・同期間）を選定した。同じECMWF/Copernicus気候変動サービスのAgERA5再解析シリーズであり、格子・期間が完全に一致するため、組み合わせに再投影・リサンプリングが不要
- `AGERA5-ET0-A`の算出方法はFAO Penman-Monteith法（FAO Irrigation and Drainage Paper 56）。国際標準の決定論的な式であり、産出元も含めFAO自身（FAO-UN Land and Water Division-AQUASTAT、ECMWF/C3Sとの共同）
- 4-14-5タイルのbboxで実際にクロップして検証（2026-09-21）: 両コレクションとも実データを確認（降水量最大2211mm/年、基準蒸発量最大1012mm/年、いずれも物理的に妥当な値）。プレースホルダーbboxではなく本物の全球カバー
- 原資産バケット（`fao-gismgr-c3s-data`、Google Cloud Storage）は、Case 2のDRAINED-AREA-CROPと同じ「匿名読み取り可・CORSヘッダー無し」（Tier A）だった。ASI-Dのような認証（ADC）は不要
- ライセンスは両コレクションとも`CC-BY-SA-4.0`（継承あり）。これまでのCase 1・Case 2で確認していた`CC-BY-4.0`とは異なる条件で、派生成果も同ライセンスを継承する必要がある

## 2026-09-21/22: Yuiseki `ferspas-udf`（unopengis/7#1013）を実地調査

Yuisekiが公開した動的タイルサーバー（<https://ferspas-udf.yuiseki.net/>、コード: <https://github.com/yuiseki/poc-cng-ferspas-udf>）を、READMEの通読と実際のviewer操作（`water-balance`のタイル`4/14/5`を含む）で調査した。

### アーキテクチャの要点

- FastAPI + rio-tiler + DuckDBで構成され、`GET /tiles/{short_id}/{time}/{z}/{x}/{y}.png`と`GET /analysis/{id}/{time}/{z}/{x}/{y}.png`という、時刻をURLパスに含む2種のエンドポイントを持つ。タイルは要求時に都度計算され、事前生成は無い
- 起動時にDuckDBで`items.parquet`（yuisekiのGeoParquet index、7章参照）を1回クエリし、`時刻→COG href`の辞書をメモリに持つ。これにより「このタイルはどのCOGか」の解決がHTTP往復ではなく辞書引きになる
- 「named analysis」という単位: `src/ferspas_tile/functions/{id}.py`が1ファイル=1関数として登録され、ファイル名がidと一致しないとロード時に失敗する。手動registration不要
- 実装済みのanalysis: `water-balance`（PF-M, ET0-M）、`aridity`（同じ2変数の比）、`gdd`（TMAX/TMIN月平均から生育度日）、`diurnal-range`（TMAX-TMIN）、`change`（前年同月比のPF-M）、`growing-conditions`（Liebigの最小律で温度・水分スコアの悪い方を採用）
- **日次ではなく月次のAgERA5を使う設計判断**: 日次は降水の有無だけを反映しノイズが大きく（aridity比が単日ではほぼ全部赤になった、との記述）、年次では月の長さの違い（2月と7月）を無視してしまう。年次を採用した本リポジトリのCase 3とは異なる判断
- 配色は「diverging（RdBu、中立値の宣言必須・表示範囲は中立値に対して対称でなければならない）」と「sequential（viridis）」の2種類のみに限定し、コンストラクタとテストで強制している。生collectionのタイル（`/tiles/...`）はFERSPAS自身が`renders`ブロックで公開する配色をそのまま使う——本リポジトリがCase 1でASI-D公式SLD配色を採用したのと同じ発想
- `growing-conditions`は「FAO/IIASAのAgro-Ecological Zones（GAEZ）のLength of Growing Period概念の簡易版であり、GAEZの公式回答は同じカタログの`RES01-LGD`（日/年）にある」と明記している。自作の指標を権威化せず、公式値の並置先を示している

### 本リポジトリの発見との一致点

- **ASIS全体・RDMS全体・SEAPの一部（639,947アセット中20,163）が`storage.cloud.google.com`の匿名アクセス拒否パターンにより配信不可能**であることを、本リポジトリのASI-D個別検証（`fao-gismgr-asis-data`バケット）とは独立に、より広い範囲で確認している。`/collections`エンドポイントはこれらを一覧から意図的に除外している（隠さず「配信できない」という事実自体を見せる設計）
- 全AgERA5系変数（PF/ET0/TMAX/TMIN等）は同じ0.1度・EPSG:4326グリッドであることを「built前に検証済み」と明記——本リポジトリがCase 3実装前に4-14-5タイルで実測確認したことと同じ確認を、より広い変数群に対して行っている

### エンジニアリング上の知見（今後processing serviceを検討する際の参考）

- 未調整のGDALでは256×256タイル1枚が5〜28秒、`GDAL_DISABLE_READDIR_ON_OPEN`・HTTP/2多重化・レンジ結合・VSIキャッシュ適用後は1〜2秒（キャッシュ済みなら実質無料）
- DuckDB接続をスレッド間で共有すると、並行クエリが無言で0行を返す不具合があった（「データが無い404」に見えるが実際は接続の競合）。クエリごとに専用cursorを使うよう修正
- タイルキャッシュはバイト数上限（既定512MB）でLRU退避、ファイル数やTTLベースではない。実測: 200KB上限で8タイル要求時、4回の退避を経てディスク使用量195,825バイトに収束したことを検証済み

## 2026-09-22: Yuiseki意味検索（unopengis/7#1014）を実地調査

<https://stac.yuiseki.net/fao-ferspas/search/>を実際に操作した。DuckDB-Wasm＋ブラウザ内埋め込みモデル（"Downloading the model..."という初回ロード表示あり）で完結し、「Nothing is sent anywhere」とページ自身が明記する設計。ソースコードは未公開（2026-09-22時点）。

- キーワードモードは通常の全文検索（BM25様のスコアリング、"rainfall"で25件0.1秒）
- 意味検索モードで"not enough rain for crops to grow"（どのcollectionのtitle/descriptionとも文字列一致しない言い回し）を検索したところ、GAEZ-V5の作物収量制約要因（`RES02-FC2`水分制約、`RES02-WDE`作物水分不足等）が類似度0.87〜0.89で上位に返った。**文字列一致では見つからない、意味に基づく発見が実際に機能していることを確認した**
- 索引は`search.parquet`（0.23MB、`collections.parquet`とは別に意味検索用に作られた軽量index）

この確認は、本リポジトリのDiscover-4-14-5ページが抱える「キーワード完全一致でしか絞り込めない」という限界に対する、将来の改善候補として意味を持つ（ソース公開後に検討）。

## 2026-09-22: unopengis/7#1011へ、これまでの実証結果と摩擦をコメント投稿

`dwg7 の Claude Code`として、issue #1011（本リポジトリのプロジェクト追跡issue）へ、実証できたこと（Case 1〜3、Discover-4-14-5、GAEZ由来のENV-LWS発見）と、見つかった摩擦（短縮id無言0件、ASIS等の認証壁、bboxプレースホルダー、sentinel値矛盾、ライセンス多様性）をまとめて投稿した。Yuisekiの`ferspas-udf`との独立した一致点（ASIS配信不可の確認）を明記し、批判ではなく実証の文脈で摩擦を共有する構成にした。

投稿: <https://github.com/UNopenGIS/7/issues/1011#issuecomment-5770035912>（2026-09-22）

## 2026-09-22: Case 3の「小さな宿題」2件の実測結果

Yuisekiの`ferspas-udf`の設計判断から学んだ2つの宿題（`docs-internal/decisions.md`参照）を実測した。

### 月次と年次の比較（時間粒度の見直し検討）

4-14-5タイルの2025年について、月次collection（`AGERA5-PF-M`/`AGERA5-ET0-M`）を12ヶ月分クロップし、月別P-ET0（タイル内平均）を計算した。

```
月      降水量   基準蒸発量  P-ET0
2025-01   47.4    11.0    36.4
2025-02   46.5    15.5    31.0
2025-03   61.8    28.4    33.4
2025-04   70.2    48.2    22.0
2025-05   91.6    73.4    18.2
2025-06   91.1    90.6     0.5
2025-07  127.7    97.9    29.8
2025-08  141.6    80.1    61.5
2025-09  104.2    63.4    40.8
2025-10   71.0    42.0    29.0
2025-11   73.4    21.8    51.6
2025-12   85.6    13.5    72.1
```

- **月次合計(426.3mm)は、Case 3が発行時に計算した2025年の年次値(426.3mm)と完全に一致**。年次collection（`AGERA5-PF-A`/`AGERA5-ET0-A`）と月次collectionの内部整合性が取れていることの裏付けになった
- **月ごとの値は0.5mm(6月)〜72.1mm(12月)まで大きく変動しており、年次集計はこの季節内の形状を完全に均している**。ただし2025年はタイル平均で見る限り全月が黒字（符号の反転は無かった）
- 地点（画素）単位では、夏に赤字・冬に黒字といった季節内の符号反転がタイル平均に隠れて見えなくなっている可能性があり、これは未検証のまま残る

### GAEZ公式「生育期間日数」との定性的な突き合わせ

`GAEZ-V5:RES01-LGD`（Total number of growing period days、2001-2020年平均、CC-BY-4.0、単位: 日、格子は1/12度≈0.0833度でAgERA5の0.1度とは異なる）を4-14-5タイルでクロップし（実測: 62〜246日、平均158日、n=11,132/48,330）、Case 3の47年平均P-ETラスターと並べて可視化した。

- 両方とも**南に行くほど値が高くなる（北海道内陸部は低く、沿岸・南部で高い）という、定性的に整合するパターン**を確認した
- 画素単位の正確な相関計算は行っていない（2つのデータセットの格子が異なるため、比較にはリサンプリングが必要）。今回は視覚的な整合性確認に留めた

### 判断

いずれも「小さな宿題」として実測はしたが、Case 3の実装を直ちに変更する動機にはならないと判断した。年次時系列（47年の基準値・逸脱・トレンド）は年次粒度だからこそ管理可能な形で成立しており、月次への全面移行は別の設計（47年×12ヶ月分の派生ファイル管理）を要する、より大きな作業になる。月次で見える季節内変動は、Case 3の限界として明記するに留める（`docs/Case3-WaterBalance-4-14-5/`のprovenance欄）。GAEZとの突き合わせも、正確な相関ではなく定性的な整合確認として記録するに留める。
