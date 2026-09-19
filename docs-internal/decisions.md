# Decisions

重大な設計判断の記録。事実は`findings.md`側に置く。

## 2026-09-19: GeoParquet/DuckDBの使いどころを、発行時とブラウザ内で分離する

### 背景

yuisekiのGeoParquet index（`stac.yuiseki.net/fao-ferspas`）は、DuckDB（-wasm）から複雑・横断・大量のSQLクエリを直接HTTPで実行できることを実測で確認した（`findings.md`参照）。一方で、同日の追加確認により、FERSPAS自体のライブSTAC APIもCORSが通ることが判明した。つまり「CORSが通らないからGeoParquetが必要」という当初の理由づけは誤りだった。

改めて両者を比較すると、優劣は一律ではなくクエリの性質に依存する。

- 単発の的を絞った検索（例: 「ASI-Dの最新1件」）は、Live API POST `/search`の方が軽い（実測295 bytes、1往復）。duckdb-wasmはブートに圧縮後約6.2MBかかる。
- 複雑・横断・大量のクエリ（例: 「1921コレクションのうち北海道と交差するのはどれか」「31年分の一覧」）は、GeoParquet+DuckDBの方が有利。Live API側にJOIN相当の機能はなく、ページングも必要になる。

### 決定

DuckDB/GeoParquetの利用を、**いつ実行するか**で2トラックに分ける。

1. **発行時（publication time）**: Case 1/2のような、答えが発行のタイミングで一度決まる固定的な問いには、`duckdb` CLIを`diagnostics/Justfile`から叩き、結果を小さな静的JSONとして`docs/derived/`へ書き出す。利用者のブラウザはduckdb-wasmを一切ロードせず、素の`fetch()`で済む。CDN到達性、wasmのブートコスト、政府ネットワークのallowlist懸念は発生しない。CLAUDE.md 4.3「Processing at publication time, not request time」の適用そのものである。
2. **リクエスト時（ブラウザ内duckdb-wasm）**: 利用者が対話的にクエリを変える場面（CLAUDE.md 21章 Phase 5「area selection」「time selection」等）に限って検討する。Phase 1–4の当面のスコープでは不要と判断する。

### 価値提案の言語化

「複雑・横断・大量」のクエリを存分に使えること自体は、Case 1/2という**Notebookの移植**という直近の目標には（今のところ）必須ではない。むしろその価値は、次の2つの目的のための**内部ツール**としてある。

- 私たち自身が「ナラティブの材料となるユースケース」「Userの問い」を発見するための探索手段（例: 「1921コレクションのうちHokkaidoに関係するのはどれか」「ライセンスが特殊なコレクションはどれか」といった、まだ問いになっていない問いを見つける）
- 将来、生成AIをこの探索レイヤーに組み込み、Userの次の問いを提案する仕組みへ発展させる可能性（CLAUDE.md 18章「Staccato / AI」の候補にも合致する）

これは、当面実現したい「Jupyter NotebookにおけるFERSPASの使用をブラウザへ移植する」という本筋（CLAUDE.md全体の中心命題）とは**別の、並行するトラック**として扱う。混同しない。

### ステータス

提案・採用（2026-09-19時点）。Phase 1–4の実装が進む中で、または探索用サーフェスの必要性が具体化した段階で見直す。

## 2026-09-19: 北海道向け派生COGは「選択肢」ではなく「前提」として扱う

### 背景

`items.parquet`から実際のCOG資産URLを取得し、匿名・ブラウザ相当のリクエストで検証したところ（`findings.md`参照）、次の事実が判明した。

- Case 1（ASI-D、`fao-gismgr-asis-data`バケット）: 匿名読み取りが拒否される（`storage.objects.get`が匿名に付与されていない）。`data_href`はGoogleログイン画面へリダイレクトされる。
- Case 2（DRAINED-AREA-CROP、`fao-gismgr-faostat-data`バケット）: 匿名読み取り自体は通るが、CORSヘッダーが一切付いていない。ブラウザの`fetch()`では読めない。

CLAUDE.md 4.6/4.7、9.4/10.4は「北海道向け派生COG（発行時clip + CORS対応で再ホスト）」を、Italy版で直接読みが成立した場合の追加選択肢、または北海道固有の事情（対象地域限定、再投影要否）への対応として位置づけていた。しかし今回の検証で、そもそもFAOの生バケットに対する「A. source COG direct access」という経路自体が、Case 1・Case 2のどちらの実アセットでも（理由は異なるが）成立しないことが分かった。

### 決定

「北海道向け派生COGを発行時に作る」を、Italy版がうまくいかなかった場合の代替案ではなく、**両Caseに共通する前提**として扱う。Italy版についても、同じ検証（実際のItalyのItemのCORS/認証）を先に行い、直接読みが本当に成立するかを確認してから9.3の成功条件を最終化する。

これに伴い、9.3「物理的なcropとダウンロード用GeoTIFF生成は必須ではない」という記述は、Italy版での実測結果が出るまで**保留（未確定）**として扱う。

### ステータス

提案（2026-09-19時点、Italy版アセットの実測待ち）。CLAUDE.md 9.3/9.4/10.3/10.4の該当箇所は、Italy側の検証が済み次第、この決定に合わせて更新する。

## 2026-09-19: 深刻なアクセス問題があるバケットは初期段階で回避し、FAOへの相談はlaunch後にまわす

### 背景

上記の検証で、ASI-D（`fao-gismgr-asis-data`）とDRAINED-AREA-CROP（`fao-gismgr-faostat-data`）は問題の性質が異なることが分かった。

- ASI-D: 匿名読み取りそのものが拒否される。ブラウザのCORS設定を直しても解決しない、より深刻な問題。私たち自身の発行パイプライン（`duckdb`/GDAL等、資格情報なし）でも読めない可能性が高い。
- DRAINED-AREA-CROP: 匿名読み取りは通る。CORSがないだけなので、私たち自身が読み取って北海道clip・CORS対応で再配布する分には、FAO側の対応を待たずに完結する。

hfuの判断: 初期段階（launchの初動）では、ASI-Dのように深刻に壊れているバケットの使用を避け、まずDRAINED-AREA-CROPのように自己完結で解決できるCaseを優先する。FAOの技術部門（CSI）へのアクセス問題の報告・相談は、launchが落ち着いてから行う。

### 決定

- 初期launchのスコープから、匿名読み取りが拒否されるバケットに依存するCase（現時点ではCase 1 / ASI-D）を実質的に後回しにする。Case 2（DRAINED-AREA-CROP）を優先して進める根拠が一つ増えた。
- FAOへの問い合わせ・相談は、hfu自身が対外コミュニケーションとして行う。Claude Codeが代行してFAOへ連絡することはしない（このリポジトリ内での記録・下書き作成までは支援できる）。
- Case 1（ASI-D）を進める場合の代替案（FAOからの正式なアクセス許可を得る、別の同等プロダクトを探す、等）は、相談が具体化してから改めて検討する。今はブロッカーとして記録するに留める。

### ステータス

採用（2026-09-19）。hfuの判断により、21章のPhase順序をCase 2優先へ並び替えた（Phase 1: Case 2 Bangladesh、Phase 2: Case 2 Hokkaido、Phase 3: Case 1 Italy〔保留〕、Phase 4: Case 1 Hokkaido〔保留〕）。Case 1の2ページはFAO CSIとの相談が進むまで着手しない。

### 追記（同日）: FAO内部の別事例への乗り換えは検討しない

FAO内部の別の実装例（Afghanistan向け、MVHI-D多年平均。人物・リポジトリ名は伏せる）を検証したところ、ASI-Dと同じ`fao-gismgr-asis-data`バケットを使っており、同じ匿名アクセス拒否にぶつかることを確認した（`findings.md`）。この事例が動くのはFAO内部のGoogle認証を使っているためであり、乗り換えても問題は解決しない。したがってCase 1の代わりにこちらへ着手する選択肢は採用しない。

一方で、この検証の過程でFAOのWMTS preview/thumbnailエンドポイントがCORSを緩く許可していることが分かった（`findings.md`）。生COGの値は読めないが、FAOがレンダリング済みのPNGを地図に載せることは今すぐ可能かもしれない。Case 1が保留の間、「値の分析はできないが地図表示だけは見せる」という縮小版が意味を持つかどうかは、Case 2の実装が一段落してから検討する（今は決定しない）。

## 2026-09-19: 派生成果のホスティング先として`depot.optgeo.org`を第一候補にする

### 背景

hfuさんから「北海道向け小領域キャッシュをCLIで作成し、`stars.optgeo.org`側に置くことでCORS/認証問題を回避できないか」という提案があった。dwg7/cafebabeと`hfu/stars`を確認したところ（`findings.md`参照）、次が分かった。

- `stars.optgeo.org`（Martin）はCOGを配信できない。設計上は対応予定だが本番には未実装で、実装されてもタイルレンダリング（見るための経路）になる可能性が高い
- 同じホストの`depot.optgeo.org`（Caddy、ポート8080）は**今すぐ使える**。`Access-Control-Allow-Origin: *`（ワイルドカード）、Rangeリクエスト対応（数十GB規模までは問題なし、私たちが扱うファイルサイズなら余裕）を確認済み

### 決定

北海道向け派生COG（13章/`docs-internal/decisions.md`の既存決定）のホスティング先として、`docs/derived/`（GitHub Pages）に加えて**`depot.optgeo.org`を候補に加える**。以下を確認してから最終判断する。

- `docs/`（GitHub Pages）自体が実際にRangeリクエストに対応するか（cafebabeの`patterns/large-data-pitfalls.md`に「`raw.githubusercontent.com`は`accept-ranges`ヘッダーを返すが実際はRangeに応答しない」という既知の落とし穴が記録されている。GitHub Pages本体は未検証で、同じ問題を持つ可能性がある）
- `/home/stars/data`への書き込み経路（gatekeeper〔`stars-fd`〕へのPR経由か、既存の信頼済みアクセスがあるか）
- `dwg7/ferspas57`との関係（同じくASIS/ASI-D系を扱っている可能性があり、重複または連携の余地がある）

いずれの場合も、**FAOの原資産を私たちが取得できることが前提**であり、ホスティング先の選定はその次の問題である。Case 2（DRAINED-AREA-CROP）は原資産が匿名で取得できるため、このホスティング先の選定はすぐに意味を持つ。Case 1（ASI-D）は、Google認証の範囲（下記決定）が解決するまでは、ホスティング先を選んでも取得元がない。

### ステータス

調査中（2026-09-19）。GitHub Pages Range対応の実測と、`depot.optgeo.org`への実際の書き込み経路確認が次のアクション。

## 2026-09-19: ASI-D/MVHI-Dバケットの認証範囲は未検証。hfuさん自身のGoogle認証での確認を依頼

### 背景

hfuさんから「FAO内部の別事例が使っている`token="google_default"`は、FAO限定の認証なのか、それとも(Google Cloud Public Datasetsのような枠組みで)個人のGoogleアカウントでも読めるのではないか」という指摘があった。これは正しい着眼点で、匿名（`allUsers`）には拒否されることは確認済みだが、`allAuthenticatedUsers`（Googleアカウントさえあれば良い）なのか、FAO内部の特定グループ限定なのかは、実際に認証済みリクエストを送らないと区別できない。

このサンドボックス環境には`gcloud`/`gsutil`が無く、hfuさん個人のGoogle認証情報も持っていない（持つべきでもない）。したがってClaude自身では検証できない。

### 決定

次のいずれかをhfuさん自身に依頼する。

1. hfuさん自身の端末で`gcloud auth login`済みの状態から`gsutil cat gs://fao-gismgr-asis-data/DATA/ASIS/MAPSET/ASI-D/ASIS.ASI-D.2026-08-D2.GS1.LC-C.tif | head -c 100`のような読み取りを試す
2. または、hfuさん自身のブラウザ（個人Googleアカウントでログイン済み）で`https://storage.cloud.google.com/fao-gismgr-asis-data/DATA/ASIS/MAPSET/ASI-D/ASIS.ASI-D.2026-08-D2.GS1.LC-C.tif`を開き、ダウンロードされるか「アクセスをリクエスト」画面になるかを見る

この結果次第で、Case 1の扱いが大きく変わる。

- **`allAuthenticatedUsers`で読める場合**: hfuさん自身の認証で発行時パイプラインを回せる。FAO CSIとの相談を待たずに、Case 1もCase 2と同じ「発行時に取得・clip・再配布」パターンに乗せられる。21章のPhase順序・保留判断を見直す材料になる
- **FAO内部限定の場合**: 従来通りFAO CSIとの相談待ちのまま

### ステータス

hfuさんの確認待ち（2026-09-19）。結果が出るまで、Case 1は「保留」のまま据え置く。

## 2026-09-19: 派生成果は再投影しない。表示側の再投影機能に任せる

### 背景

DRAINED-AREA-CROPの原資産はEPSG:4326（地理座標系、投影なし）。派生成果を作る際、Web Mercatorへ投影してしまうか、WGS84のまま持つか、という選択があった。

リモートセンシングの原則として「投影変換のたびに値が劣化する」がある。WGS84→Web Mercatorは経度方向（X）が線形写像で劣化が少ないが、緯度方向（Y）は非線形写像で実際に再サンプリングが発生する。またWeb Mercatorは緯度±85.05°までしか定義できないが、原資産は±89.0083°まで値を持つため、全球で変換すると極域データを失う。

### 決定

派生成果（`docs/<Case>/derived/`）は**投影しない**。原資産と同じCRS（EPSG:4326）のままAOIでクロップするだけにする（同一CRS内のクロップは幾何学的な切り出しであり、補間を伴わない）。表示時の再投影は、その場でWebGL等により行うビューア（CLAUDE.md 15章の候補、Source Cooperative系`cog-viewer`等）に任せる。これにより、保存データは常にソースと1ビットも変わらない値を保ち、「表示のための劣化」はレンダリング時に使い捨てで発生するだけで、成果物として保存されない。

集計（`band.sum()`相当）は、この投影しないコピーに対して直接行う。

### ステータス

採用（2026-09-19）。

## 2026-09-19: FAO / local foundation / User という3層モデルの検証

### 背景

hfuさんから、次のような概念モデルの提示があった（登場する固有の組織名はこの検討限りの理解用の例えであり、リポジトリには一般化した形でのみ残す）。

```
FAO（発行元） → local foundation（area of responsibilityごとにクラウドネイティブ形式でチェックアウトし、
                CORSを含め完全にケアして再配布する主体） → User（ブラウザのみで消費）
```

local foundationはFAOを置き換えるものではなく、FAOが将来この機能を自ら吸収する自由を持つ、という前提つき。

### 検証結果

- FAO層のアセットアクセスは一様ではなく、**Tier A（匿名で読めるがCORSが無いだけ。例: DRAINED-AREA-CROP）**と**Tier B（匿名読み取り自体が拒否される。例: ASI-D/MVHI-D）**に分かれる。Tier Aはlocal foundationが単独でチェックアウトできるが、Tier BはFAOとの協力（資格情報の提供等）が無いと成立しない。このモデルは「FAOと無関係に成立する」わけではなく、Tier Bでは必ずFAOとの関係を要する
- local foundation層の要件（クラウドネイティブなままチェックアウト、CORSの完全ケア、再投影しない、ライセンス遵守、更新検知）は、`docs/Case2-GHG-BDG/`で実際に組み立てているパターンと一致する。DRAINED-AREA-CROPは`CC-BY-4.0`で再配布可能なことも確認済み（`findings.md`）
- YuisekiのGeoParquet技術は、モデルの成立要件ではなく、複雑・横断・大量クエリが必要になった場合の強化オプションという位置づけ
- 「FAOが吸収する自由を持つ」という前提は、CLAUDE.md 25章のSustainability評価軸と整合する。local foundationは恒久的な代替ではなく、FAO自身の改善でいつでも不要になってよい、捨てられる前提の橋渡しとして設計する

### 決定

`docs/Case2-GHG-BDG/`（Tier Aの実例）を、このモデルの最小concept PoCと位置づけて完成させる。北海道／北方圏という実際のarea of responsibility、YuisekiのGeoParquet層、Tier B（ASI-D）問題の解決、複数Case/AOIへの一般化は、いずれもこのPoCの必須要件ではなく後回しにする。

### ステータス

採用（2026-09-19）。**PoC完成（2026-09-19）**: Bangladesh 31年分のチェックアウト・クロップ・集計・ページへの接続まで実装し、実機で動作確認済み（`findings.md`）。Tier Aについてはモデルが3層すべて実証された。次のarea of responsibility（北海道／北方圏、空間ID区画）への適用、Tier B（ASI-D）の扱いは、いずれも別トラックとして今後判断する。

## 2026-09-19: 公開ページはCaseごとにディレクトリを切る（`docs/<Case名>/`）

### 背景

今後、複数のCase・複数の試行コンテンツを`docs/`へ追加していく。フラットに`docs/Case2-GHG-BDG.html`のようなファイルを並べると、派生データ（年別ファイル等）の置き場と合わせて散らかる懸念があった。

### 決定

各Caseを`docs/<Case名>/`というディレクトリにまとめる。

```
docs/Case2-GHG-BDG/
  index.html   … ページ本体
  task.yaml    … task定義の公開コピー（正本は tasks/Case2-GHG-BDG.yaml）
  derived/     … チェックアウトした派生データ
```

- ディレクトリ名は参照元Notebookのファイル名に対応させる（6章の既存規則、traceability優先）。中のデータファイル名は正しい国コード等（`BGD`）を使う
- GitHub Pagesは`docs/<Case名>/`への訪問を自動的に`index.html`へ解決するため、URLは`.../Case2-GHG-BDG/`という綺麗な形になる
- AOI境界等の共有アセットは、まず対象Caseのディレクトリ内に置く。複数Caseで再利用する段階になったら共有ディレクトリへ昇格する

実際に`docs/Case2-GHG-BDG.html`→`docs/Case2-GHG-BDG/index.html`、`docs/tasks/Case2-GHG-BDG.yaml`→`docs/Case2-GHG-BDG/task.yaml`への移行を行い、ローカルサーバーで動作確認済み（31件のSTAC discoveryが引き続き成功）。CLAUDE.md 5章・8章・6章の該当箇所も更新した。

### ステータス

採用・実施済み（2026-09-19）。
