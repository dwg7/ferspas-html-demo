#!/usr/bin/env python3
"""
Case 1 (spatial ID 4-14-5) local-foundation checkout.

Same collection and selection methodology as checkout-Case1-ASIS-latest-Italy.py,
but the AOI here is a slippy-map tile (z=4, x=14, y=5) rather than a country
boundary (CLAUDE.md 4.9): no cutline/mask is used, the AOI *is* the tile's own
rectangular bbox, so a plain window crop (gdal.Translate projWin) is enough --
no boundary dataset, no polygon, and no invented NoData for "outside the AOI"
(there is no outside; the whole window is the AOI). Source pixel values
(including the 251-255 sentinel codes) are preserved unchanged.

Still requires Google Application Default Credentials (ADC): the ASI-D bucket
denies anonymous reads regardless of AOI (Tier B, see docs-internal/findings.md).
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
CASE_DIR = REPO_ROOT / "docs" / "Case1-ASIS-latest-4-14-5"

API_ROOT = "https://data.apps.fao.org/geospatial/search/stac"
COLLECTION = "fao-gismgr:ASIS:raster:mapsets:ASI-D"
# z=4, x=14, y=5 slippy-map tile bounds (EPSG:4326), same as Case2-GHG-4-14-5 / Case3
BBOX = [135.0, 40.97989806962013, 157.5, 55.7765730186677]
TILE_ID = "4-14-5"
OUT_DIR = CASE_DIR / "derived"

ID_SUFFIX_RE = re.compile(r"-GS(\d)-LC-([A-Z])$")


def stac_search():
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

    out_path = str(OUT_DIR / f"{TILE_ID}-{dekad}.tif")
    lon_min, lat_min, lon_max, lat_max = BBOX
    proj_win = [lon_min, lat_max, lon_max, lat_min]  # ulx, uly, lrx, lry

    # Plain window crop. Same CRS in/out, no cutline: the AOI is the tile
    # rectangle itself, so every output pixel is a real source pixel (including
    # the 251-255 sentinel codes, unchanged).
    ds = gdal.Translate(
        out_path,
        src_url,
        format="GTiff",
        projWin=proj_win,
        creationOptions=["COMPRESS=LZW", "TILED=YES"],
    )
    if ds is None:
        raise RuntimeError("gdal.Translate failed")
    width, height = ds.RasterXSize, ds.RasterYSize
    ds = None  # flush/close

    checksum = sha256_file(out_path)
    gdal_version = gdal.__version__

    provenance = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "generator": "scripts/checkout-Case1-ASIS-latest-4-14-5.py",
        "stac_api": API_ROOT,
        "collection": COLLECTION,
        "notebook_reference": "https://github.com/un-fao/FERSPAS_demo/blob/main/Case1-ASIS-latest-Italy.ipynb (methodology reused; AOI is dwg7's own, not from the notebook)",
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
                "aoi_identifier": TILE_ID,
                "aoi_identifier_scheme": "slippy-map tile z-x-y (spatial ID horizontal index, no floor/altitude)",
                "aoi_bbox_epsg4326": BBOX,
                "source_crs": "EPSG:4326",
                "output_crs": "EPSG:4326",
                "operation": "rectangular window crop (no cutline, no reprojection, no resampling)",
                "resampling": "none",
                "nodata_output": None,
                "nodata_source": 255,
                "nodata_note": "Source sentinel codes (251-255, including 255='water/background', see docs-internal/findings.md) are preserved unchanged; there is no 'outside the AOI' region to mask since the AOI is the crop window itself.",
                "auth_note": "Anonymous reads are denied for this bucket (fao-gismgr-asis-data); this checkout requires Google Application Default Credentials (ADC).",
                "tool": f"GDAL {gdal_version} (gdal.Translate)",
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            "output": {
                "path": f"derived/{TILE_ID}-{dekad}.tif",
                "width": width,
                "height": height,
                "sha256": checksum,
            },
        }],
    }

    with open(OUT_DIR / f"provenance-{TILE_ID}.json", "w") as fp:
        json.dump(provenance, fp, indent=2, ensure_ascii=False)

    print(f"\nDone. -> {out_path}")
    print(f"provenance -> {OUT_DIR / f'provenance-{TILE_ID}.json'}")


if __name__ == "__main__":
    main()
