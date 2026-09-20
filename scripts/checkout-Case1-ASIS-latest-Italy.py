#!/usr/bin/env python3
"""
Case 1 (Italy) local-foundation checkout:
- Query the live FERSPAS STAC API for recent ASI-D items intersecting Italy's bbox.
- Select the latest time phase, then the GS1 (growing season 1) / LC-C (cropland) variant,
  reproducing the reference notebook's selection logic.
- Crop (no reprojection: same CRS in/out, cutline mask only) to the real Italy boundary
  polygon, streamed directly from the source COG via authenticated /vsigs/ (the ASI-D bucket
  denies anonymous reads; requires Google Application Default Credentials, see
  docs-internal/findings.md and docs-internal/decisions.md, 2026-09-19).
- Record provenance (source href, generation/hash, tool versions, checksum of output).

This is a single-snapshot Case (latest available dekad), not a time series: no sum/aggregate
is computed, matching the reference notebook's own scope (map display only).
"""
import json
import re
import sys
import hashlib
import datetime
import urllib.request
from pathlib import Path

from osgeo import gdal

gdal.UseExceptions()
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ferspas-html-demo-checkout/1.0"
gdal.SetConfigOption("GDAL_HTTP_USERAGENT", UA)

REPO_ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = REPO_ROOT / "docs" / "Case1-ASIS-latest-Italy"

API_ROOT = "https://data.apps.fao.org/geospatial/search/stac"
COLLECTION = "fao-gismgr:ASIS:raster:mapsets:ASI-D"
BBOX = [6, 36, 20, 48]  # Italy, WGS84 (same values as the reference notebook)
# a wide recent window, not a specific date: ASIS updates every dekad, so "recent" is
# used to reliably catch the latest published dekad regardless of when this script runs.
DATETIME = "now-90d/2999-12-31T00:00:00Z"
AOI_GEOJSON = str(CASE_DIR / "aoi-ITA.geojson")
OUT_DIR = CASE_DIR / "derived"

ID_SUFFIX_RE = re.compile(r"-GS(\d)-LC-([A-Z])$")


def stac_search():
    # the live API does not support "now-90d" relative syntax; compute an absolute date.
    start = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=90)).strftime("%Y-%m-%dT00:00:00Z")
    body = json.dumps({
        "collections": [COLLECTION],
        "bbox": BBOX,
        "datetime": f"{start}/2999-12-31T00:00:00Z",
        "limit": 100,
    }).encode()
    req = urllib.request.Request(
        f"{API_ROOT}/search", data=body,
        headers={"Content-Type": "application/json", "User-Agent": UA}, method="POST"
    )
    with urllib.request.urlopen(req) as res:
        return json.load(res)


def select_latest_gs1_lc_c(features):
    if not features:
        raise RuntimeError("no items returned from STAC search")
    latest_dt = max(f["properties"]["start_datetime"] for f in features)
    candidates = [f for f in features if f["properties"]["start_datetime"] == latest_dt]
    for f in candidates:
        m = ID_SUFFIX_RE.search(f["id"])
        if m and m.group(1) == "1" and m.group(2) == "C":
            return f
    raise RuntimeError(f"no GS1/LC-C item found among latest-dekad candidates: {[f['id'] for f in candidates]}")


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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = stac_search()
    features = result.get("features", [])
    print(f"STAC search: {len(features)} items (numberMatched={result.get('numberMatched')})")

    item = select_latest_gs1_lc_c(features)
    dekad = item["properties"]["start_datetime"][:10]
    print(f"selected: {item['id']}  (start_datetime={dekad})")

    asset = item["assets"]["data"]
    href = asset["href"]
    gs_href = asset.get("alternate", {}).get("gs", {}).get("href")
    if not gs_href:
        raise RuntimeError("no gs:// alternate href found; cannot use authenticated /vsigs/ access")
    src_url = "/vsigs/" + gs_href[len("gs://"):]

    try:
        src_headers = head_headers(href)
    except Exception as e:
        print(f"  HEAD failed (expected: anonymous HEAD is denied for this bucket): {e}", file=sys.stderr)
        src_headers = {}

    out_path = str(OUT_DIR / f"ITA-{dekad}.tif")

    # Crop via cutline to the real Italy polygon. Same CRS in/out (EPSG:4326 -> EPSG:4326),
    # so this is a geometric mask+crop only -- no resampling, no reprojection. dstNodata=-1
    # is used only for pixels outside the AOI; it does not overwrite the source's own
    # in-band sentinel codes (251-255), which are preserved as-is for pixels inside Italy.
    ds = gdal.Warp(
        out_path,
        src_url,
        format="GTiff",
        cutlineDSName=AOI_GEOJSON,
        cropToCutline=True,
        dstNodata=-1,
        creationOptions=["COMPRESS=LZW", "TILED=YES"],
    )
    if ds is None:
        raise RuntimeError("gdal.Warp failed")
    width, height = ds.RasterXSize, ds.RasterYSize
    ds = None  # flush/close

    checksum = sha256_file(out_path)
    gdal_version = gdal.__version__

    provenance = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "generator": "scripts/checkout-Case1-ASIS-latest-Italy.py",
        "stac_api": API_ROOT,
        "collection": COLLECTION,
        "notebook_reference": "https://github.com/un-fao/FERSPAS_demo/blob/main/Case1-ASIS-latest-Italy.ipynb",
        "entries": [{
            "dekad": dekad,
            "source": {
                "collection": COLLECTION,
                "item_id": item["id"],
                "gismgr_item_id": item["properties"].get("gismgr_item_id"),
                "asset_href": href,
                "asset_gs_href": gs_href,
                "license": "CC-BY-4.0",
                "source_generation": src_headers.get("x-goog-generation"),
                "source_hash_md5_or_crc32c": src_headers.get("x-goog-hash"),
            },
            "derivation": {
                "aoi_name": "Italy",
                "aoi_iso3": "ITA",
                "aoi_geometry_source": "Natural Earth 10m admin-0 countries (public domain), ISO_A3=ITA",
                "source_crs": "EPSG:4326",
                "output_crs": "EPSG:4326",
                "operation": "cutline-mask-and-crop (no reprojection, no resampling)",
                "resampling": "none",
                "nodata_output": -1,
                "nodata_source": 255,
                "nodata_note": (
                    "Source NoData (255) is also used in-band as a 'water/background' "
                    "classification code (see docs-internal/findings.md, metadata "
                    "inconsistency between classification:classes and "
                    "supplemental_information for codes 251-255). This checkout does not "
                    "alter source pixel values inside the AOI; -1 is used only for pixels "
                    "outside Italy introduced by the cutline, to avoid conflating the two."
                ),
                "auth_note": "Anonymous reads are denied for this bucket (fao-gismgr-asis-data); this checkout requires Google Application Default Credentials (ADC).",
                "tool": f"GDAL {gdal_version} (gdal.Warp)",
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            "output": {
                "path": f"derived/ITA-{dekad}.tif",
                "width": width,
                "height": height,
                "sha256": checksum,
            },
        }],
    }

    with open(OUT_DIR / "provenance-ITA.json", "w") as fp:
        json.dump(provenance, fp, indent=2, ensure_ascii=False)

    print(f"\nDone. -> {out_path}")
    print(f"provenance -> {OUT_DIR / 'provenance-ITA.json'}")


if __name__ == "__main__":
    main()
