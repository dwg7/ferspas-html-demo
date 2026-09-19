#!/usr/bin/env python3
"""
Case 2 (Bangladesh) local-foundation checkout:
- Query the live FERSPAS STAC API for all DRAINED-AREA-CROP items intersecting Bangladesh's bbox.
- For each year, crop (no reprojection: same CRS in/out, cutline mask only) to the real
  Bangladesh boundary polygon, streamed directly from the source COG via /vsicurl/.
- Compute the sum of valid (non-NoData) pixels within the AOI (replicates the reference
  notebook's rasterio.mask() + band.sum(masked=True) logic, using GDAL instead).
- Record per-file provenance (source href, generation/hash, tool versions, checksum of output).
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
gdal.SetConfigOption("GDAL_HTTP_USERAGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ferspas-html-demo-checkout/1.0")

REPO_ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = REPO_ROOT / "docs" / "Case2-GHG-BDG"

API_ROOT = "https://data.apps.fao.org/geospatial/search/stac"
COLLECTION = "fao-gismgr:FAOSTAT:raster:mapsets:DRAINED-AREA-CROP"
BBOX = [87, 20, 93, 27]
DATETIME = "1992-01-01T00:00:00Z/2022-12-31T23:59:59Z"
AOI_GEOJSON = str(CASE_DIR / "aoi-BGD.geojson")
OUT_DIR = str(CASE_DIR / "derived")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ferspas-html-demo-checkout/1.0"

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

    for f in features:
        year = f["properties"]["start_datetime"][:4]
        asset = f["assets"]["data"]
        href = asset["href"]
        src_url = f"/vsicurl/{href}"
        out_path = f"{OUT_DIR}/BGD-{year}.tif"

        print(f"[{year}] source: {href}")
        try:
            src_headers = head_headers(href)
        except Exception as e:
            print(f"  HEAD failed: {e}", file=sys.stderr)
            src_headers = {}

        # Crop via cutline to the real Bangladesh polygon. Same CRS in/out (EPSG:4326 -> EPSG:4326),
        # so this is a geometric mask+crop only -- no resampling, no reprojection.
        ds = gdal.Warp(
            out_path,
            src_url,
            format="GTiff",
            cutlineDSName=AOI_GEOJSON,
            cropToCutline=True,
            dstNodata=-9999,
            creationOptions=["COMPRESS=LZW", "TILED=YES"],
        )
        if ds is None:
            print(f"  gdal.Warp failed for {year}", file=sys.stderr)
            continue
        band = ds.GetRasterBand(1)
        arr = band.ReadAsArray().astype("float64")
        nodata = band.GetNoDataValue()
        valid = arr != nodata
        total = float(arr[valid].sum())
        valid_count = int(valid.sum())
        width, height = ds.RasterXSize, ds.RasterYSize
        ds = None  # flush/close

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
                "aoi_name": "Bangladesh",
                "aoi_iso3": "BGD",
                "aoi_geometry_source": "Natural Earth 10m admin-0 countries (public domain), ISO_A3=BGD",
                "source_crs": "EPSG:4326",
                "output_crs": "EPSG:4326",
                "operation": "cutline-mask-and-crop (no reprojection, no resampling)",
                "resampling": "none",
                "nodata_output": -9999,
                "nodata_source": None,
                "tool": f"GDAL {gdal_version} (gdal.Warp)",
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            "output": {
                "path": f"derived/BGD-{year}.tif",
                "width": width,
                "height": height,
                "valid_pixel_count": valid_count,
                "sum_ha": total,
                "sha256": checksum,
            },
        })
        timeseries.append({"year": int(year), "drained_area_crop_ha": round(total, 2)})
        print(f"  -> {out_path}  sum={total:.2f} ha  valid_px={valid_count}")

    with open(f"{OUT_DIR}/timeseries-BGD.json", "w") as fp:
        json.dump({
            "aoi": "BGD", "unit": "ha", "variable": "drained_area_crop",
            "series": timeseries,
        }, fp, indent=2, ensure_ascii=False)

    with open(f"{OUT_DIR}/provenance-BGD.json", "w") as fp:
        json.dump({
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "generator": "scripts/checkout-Case2-GHG-BDG.py",
            "stac_api": API_ROOT,
            "collection": COLLECTION,
            "notebook_reference": "https://github.com/un-fao/FERSPAS_demo/blob/main/Case2-GHG-BDG.ipynb",
            "entries": provenance_entries,
        }, fp, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(provenance_entries)} files written to {OUT_DIR}")

if __name__ == "__main__":
    main()
