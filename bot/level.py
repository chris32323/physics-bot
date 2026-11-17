"""Detect and correct a tilted 360° panorama (camera not mounted level).

Idea: in a level equirectangular panorama, vertical things in the world (poles, building edges,
door frames, tree trunks) are perfectly vertical lines in the image, and the horizon is a straight
line through the middle. If the camera was tilted, these lines bend and lean. We try small
corrective rotations of the sphere and keep the one where edges line up best with the vertical.
"""
import math
import numpy as np
import cv2

MAX_TILT_DEG = 10.0       # beyond this we don't trust the camera: skip the panorama
MIN_FIX_DEG = 0.8         # smaller tilts are not visible, leave the image untouched
MIN_GAIN = 0.04           # the correction must improve the score by at least 4 % to be applied


def _rot(roll_deg, pitch_deg):
    r, p = math.radians(roll_deg), math.radians(pitch_deg)
    Rx = np.array([[1, 0, 0], [0, math.cos(r), -math.sin(r)], [0, math.sin(r), math.cos(r)]], np.float32)
    Ry = np.array([[math.cos(p), 0, math.sin(p)], [0, 1, 0], [-math.sin(p), 0, math.cos(p)]], np.float32)
    return Rx @ Ry


_grid_cache = {}
def _dirs(w, h):
    k = (w, h)
    if k not in _grid_cache:
        lon = ((np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi)[None, :]
        lat = (np.pi / 2 - (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi)[:, None]
        cl = np.cos(lat)
        _grid_cache[k] = np.stack(np.broadcast_arrays(cl * np.cos(lon), cl * np.sin(lon), np.sin(lat)), -1)
    return _grid_cache[k]


def rotate(img, roll_deg, pitch_deg, out_w=None, out_h=None):
    """Return the panorama as seen after rotating the sphere (roll about forward axis, pitch about side axis)."""
    h, w = img.shape[:2]
    out_w = out_w or w; out_h = out_h or h
    d = _dirs(out_w, out_h) @ _rot(roll_deg, pitch_deg).T
    lon = np.arctan2(d[..., 1], d[..., 0]); lat = np.arcsin(np.clip(d[..., 2], -1, 1))
    mx = ((lon + np.pi) / (2 * np.pi) * w - 0.5).astype(np.float32)
    my = ((np.pi / 2 - lat) / np.pi * h - 0.5).astype(np.float32)
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def _score(gray_small):
    """Share of strong edge energy that is exactly vertical (plus horizontal right at the horizon)."""
    h, w = gray_small.shape
    band = gray_small[int(h * 0.22): int(h * 0.78)].astype(np.float32)
    gx = cv2.Sobel(band, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(band, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.hypot(gx, gy)
    thr = np.percentile(mag, 85)
    strong = mag > thr
    if not strong.any():
        return 0.0
    vert = np.abs(gy) < np.abs(gx) * 0.035                     # edge within ~2° of vertical
    s = float(mag[strong & vert].sum())
    bh = band.shape[0]; mid = slice(int(bh * 0.44), int(bh * 0.56))    # horizon strip
    horiz = np.abs(gx[mid]) < np.abs(gy[mid]) * 0.035
    s += 0.5 * float(mag[mid][strong[mid] & horiz].sum())
    return s / float(mag[strong].sum())


def estimate_tilt(img):
    """Return (roll, pitch, gain): the correction in degrees and how much it improves straightness."""
    small = cv2.resize(img, (1024, 512), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    base = _score(gray)
    best = (0.0, 0.0, base)
    def search(rs, ps):
        nonlocal best
        for r in rs:
            for p in ps:
                sc = _score(rotate(gray, r, p))
                if sc > best[2] + 1e-6:
                    best = (r, p, sc)
    search(np.arange(-12, 12.1, 2.0), np.arange(-12, 12.1, 2.0))
    r0, p0 = best[0], best[1]
    search(np.arange(r0 - 1.5, r0 + 1.51, 0.5), np.arange(p0 - 1.5, p0 + 1.51, 0.5))
    r0, p0 = best[0], best[1]
    search(np.arange(r0 - 0.4, r0 + 0.41, 0.2), np.arange(p0 - 0.4, p0 + 0.41, 0.2))
    gain = (best[2] - base) / max(base, 1e-6)
    return float(best[0]), float(best[1]), float(gain)


def level_panorama(img):
    """Return (levelled image, info) or (None, info) if the panorama is too crooked to use."""
    roll, pitch, gain = estimate_tilt(img)
    tilt = math.hypot(roll, pitch)
    info = dict(roll=round(roll, 1), pitch=round(pitch, 1), gain=round(gain, 3))
    if tilt > MAX_TILT_DEG and gain > MIN_GAIN:
        info["action"] = "rejected (too tilted)"
        return None, info
    if tilt < MIN_FIX_DEG or gain < MIN_GAIN:
        info["action"] = "level, unchanged"
        return img, info
    info["action"] = "straightened"
    return rotate(img, roll, pitch), info
