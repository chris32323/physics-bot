"""Renders the reel: intro text -> 360° pan -> world map + timer -> zoom/answer -> end card, with AI voice."""
import math, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .config import W, H, FPS, FONT_BOLD, FONT_MEDIUM, RADIUS_KM, HFOV_DEG

_fonts = {}
def font(bold, size):
    k = (bold, int(size))
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FONT_BOLD if bold else FONT_MEDIUM, max(int(size), 1))
    return _fonts[k]

# ------------------------------------------------------------------ timeline
# The timeline is built per round from the real length of each spoken line ("Reel._plan"):
# a phase only ends after the voice has finished, so no sentence is ever cut off.
# These are the minimum durations (used when the lines are short).
MIN_INTRO = 1.0            # big "WHERE ARE WE?" title
MIN_PAN = 5                # 360° pan (whole seconds, one tick per second)
MIN_GUESS = 3              # map + countdown
MIN_CARD_HOLD = 5.0        # answer card stays at least this long
AFTER_SPEECH = 1.0         # breathing room after the last word of a round
MIN_END = 6.0              # end card "How many did you get?"
GAP = 0.35                 # silence between two lines in the same phase

PX, PY, PS = 60, 470, 960
SR = 44100

# ------------------------------------------------------------------ easing
def clamp01(t): return min(max(t, 0.0), 1.0)
def ease_io(t): return 0.5 - 0.5 * math.cos(math.pi * clamp01(t))
def ease_out(t): return 1 - (1 - clamp01(t)) ** 3
def ease_back(t):
    t = clamp01(t); c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def bounce_drop(t):
    t = clamp01(t)
    if t < 0.6: return (t / 0.6) ** 2
    u = (t - 0.6) / 0.4
    return 1 - 0.12 * math.sin(math.pi * u) * (1 - u)

# ------------------------------------------------------------------ 360° viewer (standard equirectangular panoramas)
_u = (np.arange(W, dtype=np.float32) - W / 2 + 0.5)[None, :]
_v = (np.arange(H, dtype=np.float32) - H / 2 + 0.5)[:, None]

def view(pano, yaw, pitch, hfov=math.radians(HFOV_DEG)):
    Hp, Wp = pano.shape[:2]
    f = (W / 2) / math.tan(hfov / 2)
    X = np.ones((H, W), np.float32); Y = np.broadcast_to(-_u / f, (H, W)); Z = np.broadcast_to(-_v / f, (H, W))
    cp, sp = math.cos(pitch), math.sin(pitch)
    x1 = X * cp - Z * sp; z1 = X * sp + Z * cp
    cy, sy = math.cos(yaw), math.sin(yaw)
    x2 = x1 * cy - Y * sy; y2 = x1 * sy + Y * cy
    az = -np.arctan2(y2, x2)                    # clockwise azimuth: image right = turn right
    el = np.arctan2(z1, np.hypot(x2, y2))
    mx = ((az + np.pi) / (2 * np.pi) * Wp - 0.5).astype(np.float32)
    my = ((np.pi / 2 - el) / np.pi * Hp - 0.5).astype(np.float32)
    return cv2.remap(pano, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

# ------------------------------------------------------------------ UI helpers
def pill(d, xy, text, fnt, fill=(15, 18, 28, 200), fg=(255, 255, 255), pad=(30, 14)):
    tw = d.textlength(text, font=fnt); x, y = xy
    asc, desc = fnt.getmetrics()
    box = [x - tw / 2 - pad[0], y - pad[1], x + tw / 2 + pad[0], y + asc + desc + pad[1] - 6]
    d.rounded_rectangle(box, radius=(box[3] - box[1]) / 2, fill=fill)
    d.text((x - tw / 2, y - 4), text, font=fnt, fill=fg)

def timer(d, cx, cy, remain, total, frac):
    R = 74; p = max(remain, 0) / total
    colr = (60, 200, 110) if p > 0.5 else (250, 190, 40) if p > 0.25 else (240, 70, 60)
    pulse = 1 + 0.08 * max(0, 1 - frac * 4); r = R * pulse
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(15, 18, 28, 210))
    box = [cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8]
    d.arc(box, 0, 360, fill=(255, 255, 255, 50), width=10)
    if p > 0: d.arc(box, -90, -90 + 360 * p, fill=colr + (255,), width=10)
    n = str(max(math.ceil(remain - 1e-6), 0)); f = font(True, 64 * pulse)
    d.text((cx - d.textlength(n, font=f) / 2, cy - 44 * pulse), n, font=f, fill=(255, 255, 255))

def pin(d, x, y, color, alpha=255):
    r = 26; hy = y - 56
    d.ellipse([x - 14, y - 6, x + 14, y + 6], fill=(0, 0, 0, 70))
    d.polygon([(x - r * 0.82, hy + r * 0.55), (x + r * 0.82, hy + r * 0.55), (x, y)], fill=color + (alpha,))
    d.ellipse([x - r, hy - r, x + r, hy + r], fill=color + (alpha,), outline=(255, 255, 255, alpha), width=4)
    d.ellipse([x - 9, hy - 9, x + 9, hy + 9], fill=(255, 255, 255, alpha))

def round_label(d, rnd, total):
    pill(d, (170, 70), f"ROUND {rnd}/{total}", font(True, 34))

def caption(d, text, pos, t, t0, t1):
    if not text or pos is None or not (t0 <= t < t1): return
    a = min(1, (t - t0) / 0.15, (t1 - t) / 0.15)
    f = font(True, 38); lines = [""]
    for w_ in text.split():
        test = (lines[-1] + " " + w_).strip()
        if d.textlength(test, font=f) > 820: lines.append(w_)
        else: lines[-1] = test
    lh = 50; bh = lh * len(lines) + 34
    y0 = {"low": 1400, "top": 456 - bh, "mid": 1330}[pos]
    bw = max(d.textlength(l, font=f) for l in lines) + 140
    d.rounded_rectangle([W / 2 - bw / 2, y0, W / 2 + bw / 2, y0 + bh], radius=28, fill=(255, 255, 255, int(235 * a)))
    bx = W / 2 - bw / 2 + 36; cy = y0 + bh / 2
    for i in range(4):
        hg = 10 + 16 * abs(math.sin(t * 11 + i * 1.7))
        d.rounded_rectangle([bx + i * 13, cy - hg, bx + i * 13 + 7, cy + hg], radius=3, fill=(40, 110, 240, int(255 * a)))
    for i, l in enumerate(lines):
        d.text((W / 2 - d.textlength(l, font=f) / 2 + 30, y0 + 14 + i * lh), l, font=f, fill=(15, 18, 28, int(255 * a)))

_mask = Image.new("L", (PS, PS), 0); ImageDraw.Draw(_mask).rounded_rectangle([0, 0, PS - 1, PS - 1], radius=36, fill=255)
_shadow = Image.new("RGBA", (PS + 40, PS + 40), (0, 0, 0, 0))
ImageDraw.Draw(_shadow).rounded_rectangle([20, 26, PS + 20, PS + 26], radius=40, fill=(0, 0, 0, 120))
_shadow = _shadow.filter(ImageFilter.GaussianBlur(12))
_border = Image.new("RGBA", (PS + 12, PS + 12), (0, 0, 0, 0))
ImageDraw.Draw(_border).rounded_rectangle([0, 0, PS + 11, PS + 11], radius=42, fill=(255, 255, 255, 255))

def paste_panel(base, pim, y):
    base.alpha_composite(_shadow, (PX - 20, int(y) - 20))
    base.alpha_composite(_border, (PX - 6, int(y) - 6))
    base.paste(pim, (PX, int(y)), _mask)

# ------------------------------------------------------------------ reel renderer
class Reel:
    """rounds: list of dicts with keys pano (RGB equirect array), lonlat, place, intro (small, big, sub),
    lines {slot: text}, credit (str)."""

    def __init__(self, world, rounds, tts=None):
        self.world = world; self.rounds = rounds; self.tts = tts
        for R in rounds:
            R["Ti"] = np.array([float(v) for v in world.to_img(*R["lonlat"])])
            R["bg"] = None
        self.clips = []          # (abs_start, samples)
        self.end_lines = {"end1": "How many did you get?"}
        self._plan()

    # ---- voice first, then the timeline is fitted around it
    def _speak(self, text):
        if not text or not self.tts: return None
        a = self.tts(text, None)
        return a if a is not None and len(a) > 0 else None

    def _plan(self):
        dur = lambda a: len(a) / SR if a is not None else 0.0
        t0 = 0.0; self.starts = []
        for R in self.rounds:
            L = {k: self._speak(R["lines"].get(k)) for k in ("intro", "pan1", "pan2", "guess", "reveal")}
            v = []                                                   # (time in round, samples)
            tl = {}
            if L["intro"] is not None: v.append((0.25, L["intro"]))
            tl["intro"] = max(MIN_INTRO, 0.25 + dur(L["intro"]) + 0.2)
            tl["pan0"] = tl["intro"]
            cur = tl["pan0"] + 0.75
            for k in ("pan1", "pan2"):
                if L[k] is not None:
                    if k == "pan2": cur = max(cur, tl["pan0"] + 2.95)
                    v.append((cur, L[k])); cur += dur(L[k]) + GAP
            tl["pan1"] = tl["pan0"] + max(MIN_PAN, math.ceil(cur - tl["pan0"] + 0.3))
            tl["slide1"] = tl["guess0"] = tl["pan1"] + 0.5
            g = MIN_GUESS
            if L["guess"] is not None:
                v.append((tl["guess0"] + 0.1, L["guess"])); g = max(g, math.ceil(dur(L["guess"]) + 0.4))
            tl["guess1"] = tl["guess0"] + g
            tl["pin"] = tl["guess1"] + 0.2; tl["circle"] = tl["pin"] + 0.25; tl["card"] = tl["pin"] + 0.7
            rev = tl["card"] + 1.02                                  # reveal starts after the chime
            if L["reveal"] is not None: v.append((rev, L["reveal"]))
            tl["dur"] = max(rev + MIN_CARD_HOLD, rev + dur(L["reveal"]) + AFTER_SPEECH)
            R["tl"] = tl
            self.starts.append(t0)
            self.clips += [(t0 + t, a) for t, a in v]
            t0 += tl["dur"]
        self.rounds_end = t0
        e = self._speak(self.end_lines["end1"])
        if e is not None: self.clips.append((t0 + 1.15, e))
        self.end_dur = max(MIN_END, 1.15 + dur(e) + 2.5)
        self.total = t0 + self.end_dur
        # guarantee: no line runs into the next phase / round
        for (s0, a), nxt in zip(self.clips, self.clips[1:] + [(self.total, None)]):
            assert s0 + len(a) / SR <= nxt[0] + 1e-6, "voice overlap"
        print("  timeline: rounds " + ", ".join(f"{R['tl']['dur']:.1f}s" for R in self.rounds)
              + f", end {self.end_dur:.1f}s, total {self.total:.1f}s")

    def _captions(self, d, abs_t):
        return                                   # no subtitle boxes: the voice speaks, the screen stays clean

    # ---- map panel
    def map_panel(self, center, vw, lat_c):
        wm = self.world; s = PS / vw; lvl = 0
        while lvl + 1 < len(wm.pyramid) and s * (2 ** (lvl + 1)) <= 1.0: lvl += 1
        a = s * (2 ** lvl)
        M = np.float32([[a, 0, PS / 2 - center[0] * s], [0, a, PS / 2 - center[1] * s]])
        img = cv2.warpAffine(wm.pyramid[lvl], M, (PS, PS), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(170, 211, 240))
        to_p = lambda q: (PS / 2 + (q[0] - center[0]) * s, PS / 2 + (q[1] - center[1]) * s)
        pim = Image.fromarray(img).convert("RGBA"); d = ImageDraw.Draw(pim)
        f = font(False, 22); boxes = []; zoomed = vw < wm.W * 0.5
        for name, x, y, pop, cap in wm.cities:
            if not zoomed and pop < 8_000_000: continue
            u, v = to_p((x, y))
            if not (30 < u < PS - 30 and 30 < v < PS - 40): continue
            tw = d.textlength(name, font=f); b = (u - tw / 2 - 6, v + 6, u + tw / 2 + 6, v + 36)
            if b[0] < 6 or b[2] > PS - 6: continue
            if any(not (b[2] < o[0] or b[0] > o[2] or b[3] < o[1] or b[1] > o[3]) for o in boxes): continue
            boxes.append(b); r = 6 if cap else 4.5
            d.ellipse([u - r, v - r, u + r, v + r], fill=(255, 255, 255), outline=(90, 90, 100), width=2)
            d.text((u - tw / 2, v + 6), name, font=f, fill=(60, 62, 72), stroke_width=3, stroke_fill=(255, 255, 255))
            if len(boxes) >= 16: break
        if zoomed:
            bar = 1000 / wm.km_per_px(lat_c) * s
            d.rectangle([24, PS - 34, 24 + bar, PS - 26], fill=(30, 30, 40))
            d.rectangle([24, PS - 46, 29, PS - 26], fill=(30, 30, 40))
            d.rectangle([19 + bar, PS - 46, 24 + bar, PS - 26], fill=(30, 30, 40))
            d.text((24, PS - 82), "1000 km", font=font(True, 26), fill=(30, 30, 40), stroke_width=3, stroke_fill=(255, 255, 255))
        return pim, to_p, s

    def _bg(self, R):
        if R["bg"] is None:
            fr = view(R["pano"], 2 * math.pi, math.radians(3))
            R["bg"] = Image.fromarray((fr * 0.55).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)).convert("RGBA")
        return R["bg"]

    # ---- frames
    def frame(self, abs_t):
        if abs_t >= self.rounds_end:
            return self.end_frame(abs_t - self.rounds_end, abs_t)
        ri = max(i for i, s0 in enumerate(self.starts) if s0 <= abs_t)
        return self.round_frame(abs_t - self.starts[ri], ri, abs_t)

    def round_frame(self, t, ri, abs_t):
        R = self.rounds[ri]; n = len(self.rounds); tl = R["tl"]
        INTRO, T_PAN0, T_PAN1, T_SLIDE1 = tl["intro"], tl["pan0"], tl["pan1"], tl["slide1"]
        T_GUESS0, T_GUESS1, T_PIN, T_CIRCLE, T_CARD = tl["guess0"], tl["guess1"], tl["pin"], tl["circle"], tl["card"]
        PAN_SECONDS, GUESS_SECONDS = T_PAN1 - T_PAN0, T_GUESS1 - T_GUESS0
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        pitch = math.radians(3 + 1.5 * math.sin(max(t, T_PAN0) * 1.3))
        if t < INTRO:                                      # static big question, from the very first frame
            out = Image.fromarray((view(R["pano"], 0.0, pitch) * 0.5).astype(np.uint8)).convert("RGBA")
            small, big, sub = R["intro"]
            f = font(True, 44); d.text((W / 2 - d.textlength(small, font=f) / 2, 860), small, font=f,
                                       fill=(255, 210, 60), stroke_width=4, stroke_fill=(15, 18, 28))
            size = 150
            while d.textlength(big, font=font(True, size)) > W - 80: size -= 4
            f = font(True, size)
            d.text((W / 2 - d.textlength(big, font=f) / 2, 925), big, font=f, fill=(255, 255, 255),
                   stroke_width=9, stroke_fill=(15, 18, 28))
            f = font(False, 40)
            d.text((W / 2 - d.textlength(sub, font=f) / 2, 945 + size * 1.25), sub, font=f, fill=(255, 255, 255),
                   stroke_width=4, stroke_fill=(15, 18, 28))
            round_label(d, ri + 1, n)
            out.alpha_composite(ov); return out.convert("RGB")
        if t < T_PAN1:                                     # 360° pan
            yaw = 2 * math.pi * ease_io((t - T_PAN0) / PAN_SECONDS)
            out = Image.fromarray(view(R["pano"], yaw, pitch)).convert("RGBA")
            timer(d, W / 2, 270, PAN_SECONDS - (t - T_PAN0), PAN_SECONDS, (t - T_PAN0) % 1)
            pill(d, (W / 2, 1760), "360°  ·  look around", font(False, 32), fill=(255, 255, 255, 60))
            self._captions(d, abs_t); round_label(d, ri + 1, n)
            out.alpha_composite(ov); return out.convert("RGB")
        # ---- map phase
        k_in = ease_out((t - T_PAN1) / (T_SLIDE1 - T_PAN1))
        if t < T_SLIDE1:
            fr = Image.fromarray(view(R["pano"], 2 * math.pi, pitch)).convert("RGBA")
            out = Image.blend(fr, self._bg(R), k_in)
        else:
            out = self._bg(R).copy()
        wm = self.world; lat = R["lonlat"][1]
        pim, to_p, s = self.map_panel(np.array([wm.W / 2, wm.H / 2]), float(wm.W), lat)   # always the whole world
        pd = ImageDraw.Draw(pim); tx, ty = to_p(R["Ti"]); red = (235, 52, 72)
        if t >= T_CIRCLE:
            k = ease_out((t - T_CIRCLE) / 0.6); rr = RADIUS_KM / wm.km_per_px(lat) * s * k
            layer = Image.new("RGBA", (PS, PS), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
            ld.ellipse([tx - rr, ty - rr, tx + rr, ty + rr], fill=red + (45,), outline=red + (220,), width=5)
            pim.alpha_composite(layer)
            if k > 0.95: pill(pd, (tx, ty + rr + 14), f"{RADIUS_KM} km", font(True, 26), fill=red + (235,))
        if t >= T_PIN:
            pin(pd, tx, ty - 260 * (1 - bounce_drop((t - T_PIN) / 0.35)), red)
        paste_panel(out, pim, PY + (H - PY) * (1 - k_in))
        if T_GUESS0 <= t < T_GUESS1:
            timer(d, W / 2, 270, T_GUESS1 - t, GUESS_SECONDS, (t - T_GUESS0) % 1)
            pill(d, (W / 2, 1500), "Lock in your guess!", font(True, 48), fill=(15, 18, 28, 210))
        if t >= T_CARD:
            k = ease_back((t - T_CARD) / 0.35); bw, bh = 900 * k, 250 * k
            d.rounded_rectangle([W / 2 - bw / 2, 1620 - bh / 2, W / 2 + bw / 2, 1620 + bh / 2], radius=40 * k,
                                fill=(255, 255, 255, 248))
            if k > 0.6:
                f0 = font(False, 32); d.text((W / 2 - d.textlength("THE ANSWER", font=f0) / 2, 1515), "THE ANSWER", font=f0, fill=red)
                size = 66
                while d.textlength(R["place"], font=font(True, size)) > 840: size -= 2
                f1 = font(True, size); d.text((W / 2 - d.textlength(R["place"], font=f1) / 2, 1555 + (66 - size) / 2),
                                              R["place"], font=f1, fill=(15, 18, 28))
                lo, la = R["lonlat"]
                sub = R.get("fact") or f"{abs(la):.2f}°{'N' if la >= 0 else 'S'}, {abs(lo):.2f}°{'E' if lo >= 0 else 'W'}"
                fs = 32
                while d.textlength(sub, font=font(False, fs)) > 840 and fs > 20: fs -= 1
                f2 = font(False, fs); d.text((W / 2 - d.textlength(sub, font=f2) / 2, 1652), sub, font=f2, fill=(110, 112, 122))
        self._captions(d, abs_t); round_label(d, ri + 1, n)
        out.alpha_composite(ov); return out.convert("RGB")

    def end_frame(self, t, abs_t):
        if not hasattr(self, "_end_bg"):
            last = self.round_frame(self.rounds[-1]["tl"]["dur"] - 0.01, len(self.rounds) - 1, -1)
            self._end_bg = last.filter(ImageFilter.GaussianBlur(14)).convert("RGBA")
        img = self._end_bg.copy(); k = ease_out(t / 0.5)
        ov = Image.new("RGBA", (W, H), (10, 12, 20, int(170 * k))); d = ImageDraw.Draw(ov)
        if t > 0.15:
            kk = ease_back((t - 0.15) / 0.4); f = font(True, 76 * kk)
            for i, line in enumerate(["How many did", "you get right?"]):
                d.text((W / 2 - d.textlength(line, font=f) / 2, 760 + i * 100), line, font=f, fill=(255, 255, 255))
        if t > 0.7:
            n = len(self.rounds)
            pill(d, (W / 2, 1080), "Comment your score: " + ", ".join(f"{i}/{n}" for i in range(n + 1)),
                 font(False, 36), fill=(15, 18, 28, 220))
            pill(d, (W / 2, 1200), "New round every day · Follow", font(True, 40), fill=(40, 110, 240, 235))
        self._captions(d, abs_t)
        img.alpha_composite(ov); return img.convert("RGB")

    # ---- audio
    def audio(self, path):
        N = int(self.total * SR); a = np.zeros(N, np.float32)
        def add(t0, sig, gain=1.0):
            i = int(t0 * SR); j = min(N, i + len(sig))
            if j > i: a[i:j] += gain * sig[: j - i]
        tt = lambda dur: np.arange(int(dur * SR)) / SR
        def tick(hi=False):
            x = tt(0.06); return 0.3 * np.sin(2 * np.pi * (1800 if hi else 1300) * x) * np.exp(-x * 70)
        def pop():
            x = tt(0.15); f = 500 + 900 * np.exp(-x * 30)
            return 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 25)
        def whoosh():
            x = tt(0.5); nn = np.convolve(np.random.default_rng(1).normal(size=len(x)), np.ones(30) / 30, "same")
            return 0.45 * nn * np.sin(np.pi * x / 0.5) ** 2
        def chime():
            out = np.zeros(int(0.9 * SR))
            for k, f in enumerate([660, 880, 1320]):
                x = tt(0.6); s = 0.22 * np.sin(2 * np.pi * f * x) * np.exp(-x * 5)
                i = int(k * 0.1 * SR); out[i:i + len(s)] += s
            return out
        speech = [(t0, t0 + len(c) / SR) for t0, c in self.clips]
        def free(t0, dur):                    # True if no voice is speaking in [t0, t0+dur]
            return all(t0 + dur < s0 - 0.08 or t0 > s1 + 0.08 for s0, s1 in speech)
        def sfx(t0, sig, gain=1.0):
            if free(t0, len(sig) / SR): add(t0, sig, gain)
            else:
                self.skipped_sfx = getattr(self, "skipped_sfx", 0) + 1
                self.skipped_at = getattr(self, "skipped_at", []) + [round(t0, 2)]
        for r, R in enumerate(self.rounds):
            b = self.starts[r]; tl = R["tl"]
            pan_s, guess_s = round(tl["pan1"] - tl["pan0"]), round(tl["guess1"] - tl["guess0"])
            sfx(b, pop()); sfx(b + tl["pan0"], whoosh())
            for k in range(pan_s): sfx(b + tl["pan0"] + k, tick(k >= pan_s - 2), 0.8)
            sfx(b + tl["pan1"], whoosh())
            for k in range(guess_s): sfx(b + tl["guess0"] + k, tick(k >= guess_s - 1), 0.8)
            sfx(b + tl["pin"] + 0.2, pop()); sfx(b + tl["card"], chime())
        sfx(self.rounds_end + 0.15, chime())
        from .audiofx import fade, polish_voice, master
        voice = np.zeros(N, np.float32)
        for t0, clip in self.clips:
            clip = fade(clip)
            i = int(t0 * SR); j = min(N, i + len(clip)); voice[i:j] += clip[: j - i]
        voice = polish_voice(voice)
        a = master(a + voice * 1.1)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((a * 32000).astype(np.int16).tobytes())

    def render(self, out_mp4, workdir):
        wav = f"{workdir}/audio.wav"; self.audio(wav)
        print(f"  voice lines: {len(self.clips)}, sound effects muted under speech: {getattr(self, 'skipped_sfx', 0)}")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart",
                              str(out_mp4)], stdin=subprocess.PIPE)
        nf = int(self.total * FPS)
        for fi in range(nf):
            p.stdin.write(np.asarray(self.frame(fi / FPS), np.uint8).tobytes())
            if fi % (FPS * 5) == 0: print(f"  frame {fi}/{nf}", flush=True)
        p.stdin.close()
        if p.wait() != 0: raise RuntimeError("ffmpeg failed")
