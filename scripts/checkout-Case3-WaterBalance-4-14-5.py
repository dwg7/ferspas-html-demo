#!/usr/bin/env python3
"""
Case 3 (spatial ID 4-14-5) water balance checkout.

Not derived from an un-fao/FERSPAS_demo notebook. Inspired by a visualization
shared by dwg7 colleague yuiseki (2026-09-20): precipitation-minus-evapotranspiration
computed dynamically from two FAO STAC COGs, colored blue (water surplus) to red
(water deficit). This script reproduces the same substantive idea (P minus ET0)
within this repository's own publication-time-processing pattern (CLAUDE.md 4.3)
rather than yuiseki's dynamic tile-server architecture: compute once per year at
checkout time, publish a static derived COG.

- Collections: C3S AGERA5-PF-A (annual precipitation, mm/year) and
  C3S AGERA5-ET0-A (annual reference evapotranspiration via FAO Penman-Monteith,
  mm/year). Same producer family (ECMWF/Copernicus C3S AgERA5 reanalysis, 0.1
  degree grid), so no resampling/regridding is needed to combine them.
- AOI is the tile rectangle itself (z=4, x=14, y=5), same convention as
  Case2-GHG-4-14-5: a plain window crop, no cutline, no reprojection.
- Output = precipitation - reference ET0 (mm/year). Positive = water surplus
  (blue), negative = water deficit (red). This is a *reference* ET0 balance
  (FAO Penman-Monteith formula), not actual crop-specific evapotranspiration --
  it does not account for what is actually growing on the ground.
- Both source collections are CC-BY-SA-4.0 (ShareAlike): the derived output
  carries the same license, not the CC-BY-4.0 used by Case 1/Case 2.
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
CASE_DIR = REPO_ROOT / "docs" / "Case3-WaterBalance-4-14-5"
OUT_DIR = CASE_DIR / "derived"

API_ROOT = "https://data.apps.fao.org/geospatial/search/stac"
PRECIP_COLLECTION = "fao-gismgr:C3S:raster:mapsets:AGERA5-PF-A"
ET0_COLLECTION = "fao-gismgr:C3S:raster:mapsets:AGERA5-ET0-A"
# z=4, x=14, y=5 slippy-map tile bounds (EPSG:4326), same as Case2-GHG-4-14-5
BBOX = [135.0, 40.97989806962013, 157.5, 55.7765730186677]
TILE_ID = "4-14-5"
FIRST_YEAR = 1979
LAST_YEAR = 2025
OUTPUT_NODATA = -99999.0  # distinct from real P-ET0 values, which stay within roughly [-1500, 2500]


def stac_search(collection):
    body = json.dumps({
        "collections": [collection],
        "datetime": f"{FIRST_YEAR}-01-01T00:00:00Z/{LAST_YEAR}-12-31T23:59:59Z",
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


def crop_year(collection, year_features, year, tmp_path, proj_win):
    f = year_features[str(year)]
    href = f["assets"]["data"]["href"]
    ds = gdal.Translate(
        tmp_path, f"/vsicurl/{href}",
        format="GTiff", projWin=proj_win,
    )
    if ds is None:
        raise RuntimeError(f"gdal.Translate failed for {collection} {year}")
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray().astype("float64")
    nodata = band.GetNoDataValue()
    width, height, gt = ds.RasterXSize, ds.RasterYSize, ds.GetGeoTransform()
    ds = None
    return arr, nodata, href, f, (width, height, gt)


def index_by_year(features):
    out = {}
    for f in features:
        year = f["properties"]["start_datetime"][:4]
        out[year] = f
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    precip_result = stac_search(PRECIP_COLLECTION)
    et0_result = stac_search(ET0_COLLECTION)
    precip_by_year = index_by_year(precip_result.get("features", []))
    et0_by_year = index_by_year(et0_result.get("features", []))
    print(f"precipitation items: {len(precip_by_year)}, ET0 items: {len(et0_by_year)}")

    years = sorted(set(precip_by_year) & set(et0_by_year))
    print(f"years with both collections available: {years[0]}-{years[-1]} ({len(years)} years)")

    lon_min, lat_min, lon_max, lat_max = BBOX
    proj_win = [lon_min, lat_max, lon_max, lat_min]

    gdal_version = gdal.__version__
    provenance_entries = []
    timeseries = []
    tmp_p = str(OUT_DIR / "_tmp_p.tif")
    tmp_e = str(OUT_DIR / "_tmp_e.tif")

    for year in years:
        p_arr, p_nodata, p_href, p_feat, p_meta = crop_year(PRECIP_COLLECTION, precip_by_year, year, tmp_p, proj_win)
        e_arr, e_nodata, e_href, e_feat, e_meta = crop_year(ET0_COLLECTION, et0_by_year, year, tmp_e, proj_win)

        if p_meta[:2] != e_meta[:2]:
            print(f"  WARNING {year}: shape mismatch precip={p_meta[:2]} et0={e_meta[:2]}", file=sys.stderr)
            continue

        valid = (p_arr != p_nodata) & (e_arr != e_nodata)
        diff = np.full(p_arr.shape, OUTPUT_NODATA, dtype="float32")
        diff[valid] = (p_arr[valid] - e_arr[valid]).astype("float32")

        width, height, gt = p_meta
        out_path = str(OUT_DIR / f"{TILE_ID}-{year}.tif")
        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(out_path, width, height, 1, gdal.GDT_Float32, options=["COMPRESS=LZW", "TILED=YES"])
        out_ds.SetGeoTransform(gt)
        out_ds.SetProjection("EPSG:4326")
        band = out_ds.GetRasterBand(1)
        band.SetNoDataValue(OUTPUT_NODATA)
        band.WriteArray(diff)
        out_ds = None

        mean_val = float(diff[valid].mean()) if valid.any() else None
        valid_count = int(valid.sum())

        try:
            p_headers = head_headers(p_href)
            e_headers = head_headers(e_href)
        except Exception as ex:
            print(f"  HEAD failed for {year}: {ex}", file=sys.stderr)
            p_headers, e_headers = {}, {}

        checksum = sha256_file(out_path)

        provenance_entries.append({
            "year": year,
            "source": {
                "precipitation": {
                    "collection": PRECIP_COLLECTION,
                    "item_id": p_feat["id"],
                    "asset_href": p_href,
                    "license": "CC-BY-SA-4.0",
                    "source_generation": p_headers.get("x-goog-generation"),
                    "source_hash_md5_or_crc32c": p_headers.get("x-goog-hash"),
                },
                "reference_et0": {
                    "collection": ET0_COLLECTION,
                    "item_id": e_feat["id"],
                    "asset_href": e_href,
                    "license": "CC-BY-SA-4.0",
                    "source_generation": e_headers.get("x-goog-generation"),
                    "source_hash_md5_or_crc32c": e_headers.get("x-goog-hash"),
                },
            },
            "derivation": {
                "aoi_identifier": TILE_ID,
                "aoi_identifier_scheme": "slippy-map tile z-x-y (spatial ID horizontal index)",
                "aoi_bbox_epsg4326": BBOX,
                "source_crs": "EPSG:4326",
                "output_crs": "EPSG:4326",
                "operation": "rectangular window crop (no cutline, no reprojection, no resampling) then per-pixel subtraction (precipitation - reference_ET0)",
                "resampling": "none",
                "nodata_output": OUTPUT_NODATA,
                "nodata_source_precip": p_nodata,
                "nodata_source_et0": e_nodata,
                "tool": f"GDAL {gdal_version} (gdal.Translate + numpy subtraction)",
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            "output": {
                "path": f"derived/{TILE_ID}-{year}.tif",
                "width": width,
                "height": height,
                "valid_pixel_count": valid_count,
                "mean_p_minus_et0_mm": mean_val,
                "sha256": checksum,
            },
        })
        timeseries.append({"year": int(year), "mean_p_minus_et0_mm": round(mean_val, 2) if mean_val is not None else None})
        print(f"[{year}] mean P-ET0 = {mean_val:.1f} mm/year  valid_px={valid_count}/{p_arr.size}")

    for tmp in (tmp_p, tmp_e):
        try:
            Path(tmp).unlink()
        except FileNotFoundError:
            pass

    with open(OUT_DIR / f"timeseries-{TILE_ID}.json", "w") as fp:
        json.dump({
            "aoi": TILE_ID, "unit": "mm/year", "variable": "precipitation_minus_reference_et0",
            "series": timeseries,
        }, fp, indent=2, ensure_ascii=False)

    with open(OUT_DIR / f"provenance-{TILE_ID}.json", "w") as fp:
        json.dump({
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "generator": "scripts/checkout-Case3-WaterBalance-4-14-5.py",
            "stac_api": API_ROOT,
            "collections": [PRECIP_COLLECTION, ET0_COLLECTION],
            "inspiration": "https://x.com/yuiseki_/status/2101615201661731234 (dynamic P-ET tiling); this checkout reproduces the idea at publication time instead of request time, per CLAUDE.md 4.3",
            "entries": provenance_entries,
        }, fp, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(provenance_entries)} years written to {OUT_DIR}")


if __name__ == "__main__":
    main()
