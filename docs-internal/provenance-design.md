# Provenance設計

CLAUDE.md 13章「Regional materialization」が求める最低限の記録項目を、実際に2つのcheckout script（`scripts/checkout-Case2-GHG-BDG.py`、`scripts/checkout-Case2-GHG-4-14-5.py`）でどう満たしているかをまとめる。新しいcheckout scriptを書くときはこの形式に合わせる。

## 実例（`docs/Case2-GHG-BDG/derived/provenance-BGD.json`）

```json
{
  "generated_at": "2026-09-19T01:31:58.327609+00:00",
  "generator": "scripts/checkout-Case2-GHG-BDG.py",
  "stac_api": "https://data.apps.fao.org/geospatial/search/stac",
  "collection": "fao-gismgr:FAOSTAT:raster:mapsets:DRAINED-AREA-CROP",
  "notebook_reference": "https://github.com/un-fao/FERSPAS_demo/blob/main/Case2-GHG-BDG.ipynb",
  "entries": [
    {
      "year": "1992",
      "source": {
        "collection": "fao-gismgr:FAOSTAT:raster:mapsets:DRAINED-AREA-CROP",
        "item_id": "fao-gismgr:FAOSTAT:raster:mapsets:DRAINED-AREA-CROP:items:FAOSTAT-DRAINED-AREA-CROP-1992",
        "gismgr_item_id": "fao-gismgr/FAOSTAT/mapsets/DRAINED-AREA-CROP/FAOSTAT.DRAINED-AREA-CROP.1992",
        "asset_href": "https://storage.googleapis.com/fao-gismgr-faostat-data/DATA/FAOSTAT/MAPSET/DRAINED-AREA-CROP/FAOSTAT.DRAINED-AREA-CROP.1992.tif",
        "asset_gs_href": "gs://fao-gismgr-faostat-data/DATA/FAOSTAT/MAPSET/DRAINED-AREA-CROP/FAOSTAT.DRAINED-AREA-CROP.1992.tif",
        "license": "CC-BY-4.0",
        "source_generation": "1750848625881416",
        "source_hash_md5_or_crc32c": "crc32c=jU2+Jw=="
      },
      "derivation": {
        "aoi_name": "Bangladesh",
        "aoi_iso3": "BGD",
        "aoi_geometry_source": "Natural Earth 10m admin-0 countries (public domain), ISO_A3=BGD",
        "source_crs": "EPSG:4326",
        "output_crs": "EPSG:4326",
        "operation": "cutline-mask-and-crop (no reprojection, no resampling)",
        "resampling": "none",
        "nodata_output": -9999,
        "nodata_source": null,
        "tool": "GDAL 3.13.1 (gdal.Warp)",
        "generated_at": "2026-09-19T01:23:38.325383+00:00"
      },
      "output": {
        "path": "derived/BGD-1992.tif",
        "width": 554,
        "height": 705,
        "valid_pixel_count": 174739,
        "sum_ha": 338844.5148791075,
        "sha256": "06e3ed811e257dff77e53126f8113af9c6b31ad5062bf89647797184077481ec"
      }
    }
  ]
}
```

## CLAUDE.md 13章の必須項目との対応

| 13章の項目 | このJSONでの場所 |
|---|---|
| source STAC API | トップレベル`stac_api` |
| source Collection | トップレベル`collection`、各entryの`source.collection` |
| source Item ID | `source.item_id`（yuisekiのGeoParquet形式）／`source.gismgr_item_id`（FAO旧ドット形式、Notebookのregexと一致） |
| source Asset href | `source.asset_href`／`source.asset_gs_href` |
| source datetime | `year`（年次データのため年のみ。dekadal等はitem_idに含む） |
| source CRS / output CRS | `derivation.source_crs`／`derivation.output_crs` |
| AOI名称・geometry source・版 | `derivation.aoi_name`／`aoi_iso3`／`aoi_geometry_source`（空間IDタイルの場合は`aoi_identifier`／`aoi_identifier_scheme`、`docs/Case2-GHG-4-14-5/derived/provenance-4-14-5.json`参照） |
| clip method / resampling method | `derivation.operation`／`derivation.resampling`（"none"は実際に補間が発生していないことを明示する値であり、省略ではない） |
| NoData handling | `derivation.nodata_output`／`nodata_source` |
| aggregation method | `output.sum_ha`を生成した計算方法は、checkout script本体（`derivation.tool`と合わせて参照） |
| pixel inclusion rule | `output.valid_pixel_count`（境界内の有効pixel数。矩形AOIの場合はマスクが無いため全pixelが該当） |
| generation time | `derivation.generated_at`（entry単位）／トップレベル`generated_at`（ファイル全体） |
| tool versions | `derivation.tool`（例: `"GDAL 3.13.1 (gdal.Warp)"`） |
| license | `source.license` |
| attribution | トップレベル`notebook_reference`、および各Caseページ本文（組織名レベルでの表示。個人の連絡先は転記しない、`findings.md`参照） |
| checksum | `output.sha256`（派生ファイル自体のハッシュ）、`source.source_generation`／`source_hash_md5_or_crc32c`（GCSオブジェクトの世代番号とハッシュ。**上流の変更検知に使う**、下記参照） |
| official / unofficial status | 現状は各Caseページのfooter（`Status: implemented`等）とtask YAMLの`status`フィールドで表現。JSON内には専用フィールドを設けていない（将来必要になれば追加） |

## 上流変更の検知（`source_generation` / `source_hash_md5_or_crc32c`）

GCSはオブジェクトが上書きされるたびに`x-goog-generation`（単調増加する世代番号）を更新する。チェックアウト時にこの値と`x-goog-hash`（crc32c/md5）をHEADリクエストだけで取得し記録しておけば、後から**ダウンロードせずに**上流が変わったかどうかを検知できる（dwg7/cafebabeの知見「上流データの固定は公式ハッシュ＋使用ファイルのsha256を記録し、不一致をテストで失敗させる」と同じ考え方）。

現状、この値を使った自動チェック（differ検知）は未実装。将来`diagnostics/Justfile`に`just check-staleness`のようなタスクを追加する候補。

## AOIの種類による違い

- **Notebookが指定する境界（国境等）を踏襲する場合**（例: Bangladesh）: `aoi_name`／`aoi_iso3`／`aoi_geometry_source`を使う。`operation`は`cutline-mask-and-crop`、境界外はNoDataでマスクされる
- **このリポジトリが独自に定義する場合**（例: 空間IDタイル、CLAUDE.md 4.9章）: `aoi_identifier`（例: `"4-14-5"`）／`aoi_identifier_scheme`を使う。AOI自体が矩形なので`operation`は`rectangular window crop`、マスクもNoDataも発生しない

いずれの場合も、**投影は行わない**（`docs-internal/decisions.md`「派生成果は再投影しない」）。`source_crs`と`output_crs`は常に一致する。
