#!/usr/bin/env python3
"""
Case 2 (spatial ID 4-14-5) local-foundation checkout.

Same STAC collection and methodology as checkout-Case2-GHG-BDG.py, but the AOI
here is a slippy-map tile (z=4, x=14, y=5) rather than a country boundary:
- No cutline/mask is used. The AOI *is* the tile's own rectangular bbox, so a
  plain window crop (gdal.Translate projWin) is enough -- no external boundary
  dataset, no polygon, and (since it's not a mask) no invented NoData pixels.
- Still no reprojection: source and output are both EPSG:4326.
"""
import json
import sys
import hashlib
import datetime
import urllib.request
from pathlib import Path

from osgeo import gdal
import numpy as np

gdal.UseExceptions()
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ferspas-html-demo-checkout/1.0"
gdal.SetConfigOption("GDAL_HTTP_USERAGENT", UA)

REPO_ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = REPO_ROOT / "docs" / "Case2-GHG-4-14-5"

API_ROOT = "https://data.apps.fao.org/geospatial/search/stac"
COLLECTION = "fao-gismgr:FAOSTAT:raster:mapsets:DRAINED-AREA-CROP"
# z=4, x=14, y=5 slippy-map tile bounds (EPSG:4326)
BBOX = [135.0, 40.97989806962013, 157.5, 55.7765730186677]
DATETIME = "1992-01-01T00:00:00Z/2022-12-31T23:59:59Z"
OUT_DIR = str(CASE_DIR / "derived")
TILE_ID = "4-14-5"

def stac_search():
    body = json.dumps({
        "collections": [COLLECTION],
        "bbox": BBOX,
        "datetime": DATETIME,
        "limit": 100,
    }).encode()
    req = urllib.request.Request(
        f"{API_ROOT}/search", data=body,
        headers={"Content-Type": "application/json", "User-Agent": UA}, method="POST"
    )
    with urllib.request.urlopen(req) as res:
        return json.load(res)

def head_headers(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as res:
        return dict(res.headers)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    result = stac_search()
    features = result.get("features", [])
    print(f"STAC search: {len(features)} items (numberMatched={result.get('numberMatched')})")
    if len(features) != 31:
        print("WARNING: expected 31 items, got", len(features), file=sys.stderr)

    features.sort(key=lambda f: f["properties"].get("start_datetime", ""))

    gdal_version = gdal.__version__
    provenance_entries = []
    timeseries = []

    lon_min, lat_min, lon_max, lat_max = BBOX
    proj_win = [lon_min, lat_max, lon_max, lat_min]  # ulx, uly, lrx, lry

    for f in features:
        year = f["properties"]["start_datetime"][:4]
        asset = f["assets"]["data"]
        href = asset["href"]
        src_url = f"/vsicurl/{href}"
        out_path = f"{OUT_DIR}/{TILE_ID}-{year}.tif"

        print(f"[{year}] source: {href}")
        try:
            src_headers = head_headers(href)
        except Exception as e:
            print(f"  HEAD failed: {e}", file=sys.stderr)
            src_headers = {}

        # Plain window crop. Same CRS in/out, no cutline: the AOI is the tile
        # rectangle itself, so every output pixel is a real source pixel.
        ds = gdal.Translate(
            out_path,
            src_url,
            format="GTiff",
            projWin=proj_win,
            creationOptions=["COMPRESS=LZW", "TILED=YES"],
        )
        if ds is None:
            print(f"  gdal.Translate failed for {year}", file=sys.stderr)
            continue
        band = ds.GetRasterBand(1)
        arr = band.ReadAsArray().astype("float64")
        total = float(arr.sum())
        pixel_count = int(arr.size)
        width, height = ds.RasterXSize, ds.RasterYSize
        ds = None

        checksum = sha256_file(out_path)

        provenance_entries.append({
            "year": year,
            "source": {
                "collection": COLLECTION,
                "item_id": f["id"],
                "gismgr_item_id": f["properties"].get("gismgr_item_id"),
                "asset_href": href,
                "asset_gs_href": asset.get("alternate", {}).get("gs", {}).get("href"),
                "license": "CC-BY-4.0",
                "source_generation": src_headers.get("x-goog-generation"),
                "source_hash_md5_or_crc32c": src_headers.get("x-goog-hash"),
            },
            "derivation": {
                "aoi_identifier": TILE_ID,
                "aoi_identifier_scheme": "slippy-map tile z-x-y (spatial ID horizontal index, no floor/altitude)",
                "aoi_bbox_epsg4326": BBOX,
                "source_crs": "EPSG:4326",
                "output_crs": "EPSG:4326",
                "operation": "rectangular window crop (no cutline, no reprojection, no resampling)",
                "resampling": "none",
                "nodata_output": None,
                "nodata_source": None,
                "tool": f"GDAL {gdal_version} (gdal.Translate)",
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            "output": {
                "path": f"derived/{TILE_ID}-{year}.tif",
                "width": width,
                "height": height,
                "pixel_count": pixel_count,
                "sum_ha": total,
                "sha256": checksum,
            },
        })
        timeseries.append({"year": int(year), "drained_area_crop_ha": round(total, 2)})
        print(f"  -> {out_path}  sum={total:.2f} ha  px={pixel_count}")

    with open(f"{OUT_DIR}/timeseries-{TILE_ID}.json", "w") as fp:
        json.dump({
            "aoi": TILE_ID, "unit": "ha", "variable": "drained_area_crop",
            "series": timeseries,
        }, fp, indent=2, ensure_ascii=False)

    with open(f"{OUT_DIR}/provenance-{TILE_ID}.json", "w") as fp:
        json.dump({
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "generator": "scripts/checkout-Case2-GHG-4-14-5.py",
            "stac_api": API_ROOT,
            "collection": COLLECTION,
            "notebook_reference": "https://github.com/un-fao/FERSPAS_demo/blob/main/Case2-GHG-BDG.ipynb (methodology reused; AOI is dwg7's own, not from the notebook)",
            "entries": provenance_entries,
        }, fp, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(provenance_entries)} files written to {OUT_DIR}")

if __name__ == "__main__":
    main()
