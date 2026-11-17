"""Frame drawing (chrome, subtitles, fades), automatic layout check, stills and the 4K60 renderer."""
import importlib.util
import json
import logging
import os
import subprocess
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle

from . import style as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
logging.getLogger("matplotlib.mathtext").setLevel(logging.ERROR)


# ---------------------------------------------------------------- fonts + episodes
def _has_font(family):
    try:
        font_manager.findfont(font_manager.FontProperties(family=family), fallback_to_default=False)
        return True
    except Exception:
        return False


def setup_fonts():
    inter = _has_font("Inter")
    if inter:
        plt.rcParams.update({
            "font.family": ["Inter", "DejaVu Sans"], "font.weight": "medium",
            "mathtext.fontset": "custom", "mathtext.rm": "Inter:medium", "mathtext.it": "Inter:medium:italic",
            "mathtext.bf": "Inter:bold", "mathtext.sf": "Inter:medium", "mathtext.fallback": "stixsans",
        })
    else:
        plt.rcParams.update({"font.family": ["DejaVu Sans"], "mathtext.fontset": "dejavusans"})
    if not _has_font(S.HEAD_FONT):
        S.HEAD_FONT = "Inter" if inter else "DejaVu Sans"
    return inter


def load_episode(path):
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    name = "episode_" + os.path.splitext(os.path.basename(path))[0].replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- renderer
class Renderer:
    def __init__(self, episode, timeline, meta, scale=2.0):
        setup_fonts()
        self.ep, self.tl, self.meta, self.scale = episode, timeline, meta, scale
        self.fig = plt.figure(figsize=(S.W / 100, S.H / 100), dpi=100 * scale)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.grid = [[(x, 0), (x, S.H)] for x in range(0, S.W + 1, 90)] + \
                    [[(0, y), (S.W, y)] for y in range(0, S.H + 1, 90)]
        n, self.numbers = 0, []
        for sc in episode.SCENES:
            if sc.header:
                n += 1
            self.numbers.append(n if sc.header else None)
        topic = meta.get("topic", "")
        self.topic = topic if len(topic) <= 30 else topic[:29] + "…"

    def scene_at(self, g):
        for i, s in enumerate(self.tl["scenes"]):
            if g < s["start"] + s["duration"]:
                return i
        return len(self.tl["scenes"]) - 1

    def draw(self, g):
        ax = self.ax
        ax.cla()
        ax.set_xlim(0, S.W)
        ax.set_ylim(0, S.H)
        ax.axis("off")
        si = self.scene_at(g)
        info = self.tl["scenes"][si]
        t = g - info["start"]
        c = S.Canvas(ax, t, info)
        c.scene_index = si
        ax.add_patch(Rectangle((0, 0), S.W, S.H, color=S.BG, zorder=-10))
        ax.add_collection(LineCollection(self.grid, colors="#ffffff", alpha=0.03, linewidths=1, zorder=-9))
        self._chrome(c, g, si)
        self.ep.SCENES[si].draw(c)
        self._subtitle(c, g)
        self._fade(si, t, info["duration"])
        return c

    def _chrome(self, c, g, si):
        m = self.meta
        c.text(70, 1832, m.get("channel", ""), size=21, color=S.BLUE, weight="bold", ha="left", kind="chrome")
        c.text(S.W - 70, 1832, f"Day {m.get('day', 1)} · {self.topic}", size=20, color=S.MUTED, ha="right",
               kind="chrome")
        prog = S.clamp(g / self.tl["total"])
        c.line([70, S.W - 70], [1790, 1790], color="#ffffff", lw=3, alpha=0.12)
        if prog > 0.002:
            c.line([70, 70 + (S.W - 140) * prog], [1790, 1790], color=S.BLUE, lw=3, alpha=0.9)
        header = self.ep.SCENES[si].header
        if header:
            a = c.ramp(0.1, 0.6)
            dy = 20 * (1 - a)
            c.dot(103, 1700 - dy, r=31, color=S.BLUE, alpha=a, z=5)
            c.text(103, 1700 - dy, str(self.numbers[si]), size=27, color=S.BG, weight="bold",
                   va="center_baseline", alpha=a, z=6, kind="chrome")
            c.text(155, 1700 - dy, header, size=40, weight="bold", font=S.HEAD_FONT, ha="left",
                   va="center_baseline", alpha=a, kind="chrome")

    def _subtitle(self, c, g):
        if not self.meta.get("subtitles", True):
            return
        for a, b, text in self.tl["subs"]:
            if a - 0.05 <= g < b:
                al = S.clamp((g - a + 0.05) / 0.12) * S.clamp((b - g) / 0.12)
                if al > 0.01:
                    art = self.ax.text(S.W / 2, S.SUB_Y, text, color="#ffffff", fontsize=31, fontweight="semibold",
                                       ha="center", va="center", alpha=al, zorder=30, linespacing=1.25,
                                       bbox=dict(boxstyle="round,pad=0.5,rounding_size=0.5", fc="#04050c",
                                                 ec="none", alpha=0.62 * al))
                    c.texts.append((art, "subtitle", None))
                break

    def _fade(self, si, t, dur):
        n = len(self.tl["scenes"])
        fin = 0.0 if si == 0 else 0.3
        fout = 0.9 if si == n - 1 else 0.3
        a = 0.0
        if fin and t < fin:
            a = 1 - t / fin
        if t > dur - fout:
            a = max(a, (t - (dur - fout)) / fout)
        if a > 0:
            self.ax.add_patch(Rectangle((0, 0), S.W, S.H, color="#000000", alpha=min(a, 1.0), zorder=100))


# ---------------------------------------------------------------- automatic layout check
def _boxes(r, c):
    rend = r.fig.canvas.get_renderer()
    out = []
    for art, kind, line in c.texts:
        a = art.get_alpha()
        if a is not None and a < 0.6:
            continue
        patch = art.get_bbox_patch()
        bb = (patch if patch is not None else art).get_window_extent(rend)
        x0, y0, x1, y1 = bb.x0 / r.scale, bb.y0 / r.scale, bb.x1 / r.scale, bb.y1 / r.scale
        if patch is None:                     # ignore the empty line spacing above/below the glyphs
            pad = (y1 - y0) * 0.12
            y0, y1 = y0 + pad, y1 - pad
        out.append((kind, art.get_text().replace("\n", " "), (x0, y0, x1, y1), line))
    return out


def _overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    area = lambda r: max((r[2] - r[0]) * (r[3] - r[1]), 1.0)
    return w * h / min(area(a), area(b))


def _src(line):
    return f" [episode line {line}]" if line else ""


def check_frame(r, c, g):
    r.fig.canvas.draw()
    boxes = _boxes(r, c)
    si = c.scene_index
    sc = r.ep.SCENES[si]
    where = f"scene {si + 1} ({sc.header or ('intro' if si == 0 else 'outro')}) at {c.t:.1f}s"
    issues = []
    content = [b for b in boxes if b[0] == "content"]
    has_sub = any(b[0] == "subtitle" for b in boxes)
    top = 1665 if sc.header else 1772
    for i, (_, txt, bb, line) in enumerate(content):
        if bb[0] < 25 or bb[2] > S.W - 25:
            issues.append(f"{where}: text '{txt}'{_src(line)} is cut off at the left/right edge "
                          f"(x {bb[0]:.0f}–{bb[2]:.0f}, allowed 25–{S.W - 25})")
        if bb[1] < S.UI_BOTTOM:
            issues.append(f"{where}: text '{txt}'{_src(line)} reaches into the bottom zone (y<{S.UI_BOTTOM}) "
                          f"that TikTok/Instagram cover with their own UI")
        if has_sub and bb[1] < S.SUB_ZONE[1] and bb[3] > S.SUB_ZONE[0]:
            issues.append(f"{where}: text '{txt}'{_src(line)} overlaps the subtitle area "
                          f"(text y {bb[1]:.0f}–{bb[3]:.0f}, keep it above y={S.SUB_ZONE[1] + 20})")
        if bb[3] > top:
            issues.append(f"{where}: text '{txt}'{_src(line)} overlaps the header/top bar "
                          f"(text top y={bb[3]:.0f}, keep content below y={top - 15})")
        for _, txt2, bb2, line2 in content[i + 1:]:
            ov = _overlap(bb, bb2)
            if ov > 0.12:
                upper, lower = (bb, bb2) if bb[3] >= bb2[3] else (bb2, bb)
                gap = upper[1] - lower[3]                 # negative = they overlap vertically
                need = 22 - gap
                issues.append(
                    f"{where}: text '{txt}'{_src(line)} (y {bb[1]:.0f}–{bb[3]:.0f}) overlaps text '{txt2}'{_src(line2)} "
                    f"(y {bb2[1]:.0f}–{bb2[3]:.0f}), overlap {ov:.0%}. Fix: increase their vertical distance by "
                    f"at least {need:.0f} units, or fade the earlier one out before the later one appears "
                    f"at the same place, or use a smaller font.")
    return issues


def sample_times(tl):
    """A few moments per scene where everything of a step is visible (not inside fades)."""
    times = []
    for s in tl["scenes"]:
        for cue, dur in zip(s["cues"], s["durs"]):
            times.append(s["start"] + cue + 0.85 * dur)
        times.append(s["start"] + s["duration"] - 0.45)
    return times


def layout_check(episode, tl, meta, scale=0.5):
    r = Renderer(episode, tl, meta, scale)
    issues = []
    for g in sample_times(tl):
        c = r.draw(g)
        issues += check_frame(r, c, g)
    plt.close(r.fig)
    seen, out = set(), []
    for i in issues:                      # de-duplicate repeated findings
        key = i.split(": ", 1)[1]
        if key not in seen:
            seen.add(key)
            out.append(i)
    return out


def stills(episode, tl, meta, times, out_dir, scale=0.5, labels=False):
    os.makedirs(out_dir, exist_ok=True)
    r = Renderer(episode, tl, meta, scale)
    paths = []
    for k, g in enumerate(times):
        c = r.draw(g)
        if labels:      # time stamp in the empty bottom zone – only for the review sheets
            r.ax.text(40, 90, f"{g:5.1f} s  ·  scene {c.scene_index + 1}", color="#ffffff", fontsize=30,
                      alpha=0.85, zorder=200)
        p = os.path.join(out_dir, f"still_{k:02d}_{g:06.2f}s.png")
        r.fig.savefig(p, dpi=100 * scale)
        paths.append(p)
    plt.close(r.fig)
    return paths


def dry_run(episode, tl, meta, step=0.2):
    """Calls every draw function across the whole video and reports crashes with the line number."""
    import traceback
    r = Renderer(episode, tl, meta, 0.25)
    problems, g = [], 0.0
    while g < tl["total"]:
        try:
            r.draw(g)
        except Exception as e:
            si = r.scene_at(g)
            where = ""
            src = os.path.abspath(getattr(episode, "__file__", "") or "")
            for fr in reversed(traceback.extract_tb(e.__traceback__)):
                if os.path.abspath(fr.filename) == src:
                    where = f" (line {fr.lineno}: {fr.line})"
                    break
            problems.append(f"scene {si + 1} crashes at {g - tl['scenes'][si]['start']:.2f}s: "
                            f"{type(e).__name__}: {e}{where}")
            g = tl["scenes"][si]["start"] + tl["scenes"][si]["duration"]
            continue
        g += step
    plt.close(r.fig)
    return problems


def contact_sheet(paths, out, cols=4):
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), (14, 17, 36))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(out)
    return out


# ---------------------------------------------------------------- video
def _encoder(w, h, fps, crf, out):
    return ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}",
            "-r", str(fps), "-i", "-",
            "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-tune", "animation", "-crf", str(crf),
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", out]


def render_chunk(ep_path, tl_path, meta_path, a, b, out, scale, fps, crf):
    ep = load_episode(ep_path)
    tl = json.load(open(tl_path))
    meta = json.load(open(meta_path))
    r = Renderer(ep, tl, meta, scale)
    w, h = int(round(S.W * scale)), int(round(S.H * scale))
    tmp = out[:-4] + ".part.mp4"
    p = subprocess.Popen(_encoder(w, h, fps, crf, tmp), stdin=subprocess.PIPE)
    for f in range(a, b):
        r.draw(f / fps)
        r.fig.canvas.draw()
        p.stdin.write(r.fig.canvas.buffer_rgba())
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit(f"encoder failed for {out}")
    os.replace(tmp, out)


def render_video(ep_path, tl_path, meta_path, out, scale=2.0, fps=60, crf=14, workers=0, log=print):
    tl = json.load(open(tl_path))
    n = int(round(tl["total"] * fps))
    workers = workers or os.cpu_count() or 2
    parts = max(2 * workers, 2)
    bounds = [n * i // parts for i in range(parts + 1)]
    work = os.path.join(os.path.dirname(out), "chunks")
    os.makedirs(work, exist_ok=True)
    files = [os.path.join(work, f"chunk_{i:03d}.mp4") for i in range(parts)]
    jobs = [(i, bounds[i], bounds[i + 1]) for i in range(parts)]
    running, t0 = [], time.time()
    while jobs or running:
        while jobs and len(running) < workers:
            i, a, b = jobs.pop(0)
            cmd = [sys.executable, "-m", "engine.render", "chunk", os.path.abspath(ep_path), os.path.abspath(tl_path),
                   os.path.abspath(meta_path), str(a), str(b), os.path.abspath(files[i]), str(scale), str(fps), str(crf)]
            running.append((i, subprocess.Popen(cmd, cwd=ROOT)))
        time.sleep(0.5)
        for item in list(running):
            i, p = item
            if p.poll() is not None:
                running.remove(item)
                if p.returncode != 0:
                    for _, q in running:
                        q.kill()
                    raise RuntimeError(f"render chunk {i} failed")
                log(f"  chunk {i + 1}/{parts} fertig ({time.time() - t0:.0f}s)")
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as fh:
        fh.writelines("file '" + os.path.abspath(f).replace("\\", "/") + "'\n" for f in files)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out],
                   check=True)
    return out


def mux(video, audio, out):
    tmp = out[:-4] + ".part.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", tmp],
                   check=True)
    os.replace(tmp, out)
    return out


def downscale(src, out, crf=16):
    tmp = out[:-4] + ".part.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
                    "-vf", "scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int",
                    "-c:v", "libx264", "-preset", "veryfast", "-tune", "animation", "-crf", str(crf),
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
                    "-c:a", "copy", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)
    return out


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "chunk":
    _, _, ep, tlp, mp, a, b, out, scale, fps, crf = sys.argv
    render_chunk(ep, tlp, mp, int(a), int(b), out, float(scale), int(fps), int(crf))
