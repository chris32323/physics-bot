"""Real world map (Natural Earth, public domain) rendered in Web-Mercator, plus distance helpers."""
import json, math
import numpy as np
from PIL import Image, ImageDraw
from .config import NE_DIR

R_EARTH = 6371.0
LAT_TOP, LAT_BOT = 80.0, -60.0
PASTEL = [(242, 228, 196), (226, 238, 206), (246, 216, 206), (218, 228, 244),
          (240, 236, 206), (232, 218, 238), (212, 236, 220)]


def haversine(a, b):
    (lo1, la1), (lo2, la2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2
    return 2 * R_EARTH * math.asin(math.sqrt(h))


def _load(name):
    return json.load(open(NE_DIR / name, encoding="utf-8"))["features"]


def _rings(geom):
    t = geom["type"]; c = geom["coordinates"]
    if t == "Polygon": yield from c
    elif t == "MultiPolygon":
        for p in c: yield from p
    elif t == "LineString": yield c
    elif t == "MultiLineString": yield from c


def _merc(lat):
    return np.log(np.tan(np.pi / 4 + np.radians(np.clip(lat, -85, 85)) / 2))


class WorldMap:
    def __init__(self, width_px=12000):
        self.W = width_px
        self.y0 = _merc(LAT_TOP); y1 = _merc(LAT_BOT)
        self.H = int(round((self.y0 - y1) / (2 * np.pi) * self.W))
        self.img = self._render()
        self.pyramid = [self.img]
        import cv2
        while self.pyramid[-1].shape[1] > 1500:
            self.pyramid.append(cv2.pyrDown(self.pyramid[-1]))

    def to_img(self, lon, lat):
        lon = np.asarray(lon, float); lat = np.asarray(lat, float)
        return (lon + 180) / 360 * self.W, (self.y0 - _merc(lat)) / (2 * np.pi) * self.W

    def km_per_px(self, lat):
        return 40075.0 * math.cos(math.radians(lat)) / self.W

    def _render(self):
        countries = _load("ne_50m_admin_0_countries.geojson")
        lakes = _load("ne_50m_lakes.geojson")
        rivers = _load("ne_50m_rivers_lake_centerlines.geojson")
        places = _load("ne_50m_populated_places_simple.geojson")
        img = Image.new("RGB", (self.W, self.H), (170, 211, 240)); d = ImageDraw.Draw(img)
        def pts(ring):
            a = np.asarray(ring, float); x, y = self.to_img(a[:, 0], a[:, 1]); return list(zip(x, y))
        feats = [(f, [pts(r) for r in _rings(f["geometry"])]) for f in countries
                 if f["properties"].get("ADMIN") != "Antarctica"]
        for _, rings in feats:
            for r in rings:
                if len(r) > 2: d.polygon(r, fill=(150, 196, 232), outline=(150, 196, 232), width=9)
        for f, rings in feats:
            colr = PASTEL[(f["properties"].get("MAPCOLOR7") or 1) % 7]
            for r in rings:
                if len(r) > 2: d.polygon(r, fill=colr)
        for f in lakes:
            for r in _rings(f["geometry"]):
                p = pts(r)
                if len(p) > 2: d.polygon(p, fill=(170, 211, 240), outline=(150, 196, 232), width=2)
        for f in rivers:
            if (f["properties"].get("scalerank") or 9) > 5: continue
            for r in _rings(f["geometry"]):
                p = pts(r)
                if len(p) > 1: d.line(p, fill=(160, 204, 238), width=4, joint="curve")
        for _, rings in feats:
            for r in rings:
                if len(r) > 2: d.line(r + [r[0]], fill=(176, 160, 186), width=4, joint="curve")
        self.cities = []
        for f in places:
            p = f["properties"]
            if p["pop_max"] < 1_000_000 and not (p["adm0cap"] and p["pop_max"] > 500_000): continue
            if not (LAT_BOT < p["latitude"] < LAT_TOP): continue
            x, y = self.to_img(p["longitude"], p["latitude"])
            self.cities.append((p["name"], float(x), float(y), p["pop_max"], bool(p["adm0cap"])))
        self.cities.sort(key=lambda t: -t[3])
        return np.array(img)
