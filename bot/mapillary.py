"""Find and download a real 360° panorama from Mapillary (images are CC BY-SA 4.0)."""
import io, random, time
import numpy as np
import requests
from PIL import Image
from .config import MAPILLARY_TOKEN, MIN_PANO_WIDTH, REQUIRE_ROAD
from .level import level_panorama
from .safety import redact
from . import vision

Image.MAX_IMAGE_PIXELS = 120_000_000      # refuse absurdly large images (decompression-bomb guard)

API = "https://graph.mapillary.com/images"
FIELDS = "id,thumb_original_url,is_pano,width,height,captured_at,computed_geometry,creator"


class NoPanorama(Exception):
    pass


def _search(lon, lat, half):
    bbox = f"{lon - half:.5f},{lat - half:.5f},{lon + half:.5f},{lat + half:.5f}"
    for attempt in range(3):
        try:
            r = requests.get(API, params=dict(access_token=MAPILLARY_TOKEN, fields=FIELDS, bbox=bbox,
                                              is_pano="true", limit=100), timeout=60)
            if r.status_code == 200:
                return r.json().get("data", [])
            print(redact(f"  mapillary HTTP {r.status_code}: {r.text[:200]}"))
        except requests.RequestException as e:
            print(redact(f"  mapillary error: {e}"))
        time.sleep(3 * (attempt + 1))
    return []


def _good(img_meta):
    w, h = img_meta.get("width") or 0, img_meta.get("height") or 0
    return (img_meta.get("is_pano") and img_meta.get("thumb_original_url")
            and w >= MIN_PANO_WIDTH and h > 0 and abs(w / h - 2.0) < 0.03)


def _detected_classes(image_id):
    """Mapillary's automatic segmentation labels for an image, e.g. 'construction--flat--road', 'nature--sky'."""
    try:
        r = requests.get(f"https://graph.mapillary.com/{image_id}/detections",
                         params=dict(access_token=MAPILLARY_TOKEN, fields="value"), timeout=60)
        if r.status_code != 200:
            return None
        return {d.get("value", "") for d in r.json().get("data", [])}
    except requests.RequestException:
        return None


def _is_outdoor(classes, need_road):
    """True = suitable outdoor scene, False = clearly not (indoors / no road), None = unknown (no detections yet)."""
    if not classes:
        return None
    sky = "nature--sky" in classes
    if not need_road:
        return sky
    road = any(c.startswith(("construction--flat--road", "marking--", "construction--flat--crosswalk")) for c in classes)
    return road and sky


# search box half-sizes in degrees: sights must be close so the landmark is actually in the picture
SEARCH = {"landmark": (0.002, 0.004, 0.008), "border": (0.002, 0.004, 0.008),
          "landscape": (0.004, 0.012, 0.03), "street": (0.01, 0.025, 0.05)}


def _sky_visible(arr):
    """Own check on the pixels: the top of an outdoor panorama is mostly sky, indoors it is a ceiling."""
    top = arr[: int(arr.shape[0] * 0.2)].astype(np.float32)
    r, g, b = top[..., 0], top[..., 1], top[..., 2]
    bright = (r + g + b) / 3
    sky_like = ((b >= r - 8) & (bright > 115)) | (bright > 195)
    return float(sky_like.mean()) > 0.45


def fetch_panorama(lon, lat, rng=None, kind="street", place=None):
    """Return (equirectangular RGB array, metadata dict). Raises NoPanorama."""
    if not MAPILLARY_TOKEN:
        raise RuntimeError("MAPILLARY_TOKEN is not set")
    rng = rng or random.Random()
    state = {"checks": 0, "fallback": None}

    def consider(got):
        """Optional AI check. Returns the panorama to use, or None to keep looking."""
        if not got:
            return None
        if not vision.ENABLED:
            return got
        if state["checks"] >= vision.MAX_CHECKS:
            return state["fallback"] or got
        state["checks"] += 1
        res = vision.check(got[0], place or "this place", kind)
        if res is None:
            return got                                   # API problem: never block the post
        got[1]["ai_check"] = res
        print(f"  {got[1]['id']}: AI check {res}")
        if not res["usable"] or res["spoiler"]:
            return None
        if kind != "street" and res["sight_visible"] is False:
            state["fallback"] = state["fallback"] or got  # usable, but the sight isn't in view: keep as plan B
            return None
        return got

    need_road = REQUIRE_ROAD and kind == "street"
    for half in SEARCH.get(kind, SEARCH["street"]):
        cands = [m for m in _search(lon, lat, half) if _good(m)]
        print(f"  bbox ±{half}°: {len(cands)} usable panoramas")
        rng.shuffle(cands)
        # sights: closest first; streets: recent, high-resolution captures first
        if kind == "street":
            cands.sort(key=lambda m: (-(m.get("width") or 0) // 1000, -(m.get("captured_at") or 0)))
        else:
            def dist(m):
                c = (m.get("computed_geometry") or {}).get("coordinates") or [lon + 1, lat + 1]
                return (c[0] - lon) ** 2 + (c[1] - lat) ** 2
            cands.sort(key=dist)
        maybes = []
        for m in cands[:15]:
            if REQUIRE_ROAD:
                ok = _is_outdoor(_detected_classes(m["id"]), need_road)
                if ok is False:
                    print(f"  {m['id']}: {'no road/sky' if need_road else 'no sky'} detected (indoors?), skipped")
                    continue
                if ok is None:
                    print(f"  {m['id']}: no Mapillary detections yet, will check the pixels instead")
                    maybes.append(m); continue
            got = consider(_download(m, lon, lat))
            if got: return got
        for m in maybes[:4]:                  # no detections yet: rely on our own sky check only
            got = consider(_download(m, lon, lat))
            if got: return got
    if state["fallback"]:
        print("  no view with the sight clearly visible - using the best usable panorama")
        return state["fallback"]
    raise NoPanorama(f"no usable outdoor 360° panorama near {lat:.4f},{lon:.4f}")


def _download(m, lon, lat):
    try:
        r = requests.get(m["thumb_original_url"], timeout=120)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception as e:
        print(redact(f"  download failed ({e}), next"))
        return None
    if im.width > 8192:
        im = im.resize((8192, 4096), Image.LANCZOS)
    arr = np.array(im)
    if arr.std() < 12:                     # blank / broken image
        print(f"  {m['id']}: image is blank or broken, skipped")
        return None
    if REQUIRE_ROAD and not _sky_visible(arr):
        print(f"  {m['id']}: no open sky at the top (probably indoors), skipped")
        return None
    arr, lv = level_panorama(arr)          # straighten a crooked camera, or skip if far too tilted
    print(f"  {m['id']}: horizon check {lv}")
    if arr is None:
        return None
    geo = (m.get("computed_geometry") or {}).get("coordinates") or [lon, lat]
    meta = dict(id=m["id"], lon=geo[0], lat=geo[1], captured_at=m.get("captured_at"),
                creator=(m.get("creator") or {}).get("username"),
                url=f"https://www.mapillary.com/app/?pKey={m['id']}", level=lv)
    print(f"  downloaded panorama {m['id']}")
    return arr, meta
