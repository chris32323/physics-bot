"""House style + drawing API for episodes.

An episode file does `from engine.style import *`, defines FACTS and SCENES,
and every scene has a draw(c) function. `c` is a Canvas: it knows the current
time inside the scene (c.t), when each narration step starts (c.cue(i)),
and has drawing helpers that already use the channel's look.

Coordinates: a 1080 x 1920 portrait canvas, origin bottom-left, y up.
"""
import math
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np
from matplotlib.patches import FancyArrowPatch, Circle, Arc, FancyBboxPatch, Rectangle, Polygon

__all__ = [
    "W", "H", "BG", "FG", "MUTED", "BLUE", "ORANGE", "PINK", "GREEN", "YELLOW", "PURPLE", "PANEL",
    "CONTENT_TOP", "CONTENT_BOTTOM", "Scene", "Step", "ease", "clamp", "lerp", "wrap", "np", "math",
]

# ---------------------------------------------------------------- canvas + colours
W, H = 1080, 1920
BG = "#0e1124"
FG = "#f2f4ff"
MUTED = "#8a90b8"
BLUE = "#4cc9f0"      # horizontal / x quantities
ORANGE = "#ff9f1c"    # vertical / y quantities
PINK = "#f72585"      # the main object
GREEN = "#80ed99"     # forces, gravity
YELLOW = "#ffd60a"    # key results
PURPLE = "#b388ff"    # extra category
PANEL = "#1b2040"
PANEL_EDGE = "#2e3566"
HEAD_FONT = "Inter Display"

# ---------------------------------------------------------------- layout zones
CONTENT_TOP = 1650      # content must stay below the header
CONTENT_BOTTOM = 570    # ... and above the subtitles
SUB_Y = 468             # subtitle centre
SUB_ZONE = (392, 548)   # reserved for subtitles
UI_BOTTOM = 380         # platform UI (caption, buttons) covers y < 380


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


def lerp(a, b, u):
    return a + (b - a) * u


def wrap(text, width=22):
    """Break a sentence into lines of at most `width` characters."""
    import textwrap
    return "\n".join(textwrap.wrap(text, width))


# ---------------------------------------------------------------- episode structure
@dataclass
class Step:
    """One narration sentence and the visual idea that goes with it."""
    say: str = ""                       # read by the voice; {name} is filled from FACTS
    sub: Optional[str] = None           # subtitle text if it should differ (e.g. with v₀, α, ²)
    pause: float = 0.0                  # extra seconds after the sentence for the animation
    min: float = 0.0                    # minimum length of this step in seconds
    sfx: list = field(default_factory=list)   # [("whoosh", 0.1), ("pop", 0.4, {"n": 2})]


@dataclass
class Scene:
    draw: Callable
    steps: list
    header: Optional[str] = None        # numbered header, e.g. "Split the velocity"
    lead: Optional[float] = None        # quiet time before the first sentence (default from config)
    tail: Optional[float] = None        # hold after the last step (default from config)
    sounds: Optional[Callable] = None   # optional: sounds(tm) -> [(name, t_in_scene, opts), ...]


# ---------------------------------------------------------------- timing helpers
class Timing:
    """Time helpers for one scene (also passed to Scene.sounds)."""

    def __init__(self, t, info):
        self.t = t
        self.T = info["duration"]
        self._cues = info["cues"]
        self._durs = info["durs"]
        self._voice = info["voice"]

    def cue(self, i):
        """Start of step i (seconds since scene start)."""
        return self._cues[i]

    def dur(self, i):
        """Length of step i including its pause."""
        return self._durs[i]

    def stop(self, i):
        return self._cues[i] + self._durs[i]

    def voice(self, i):
        """(start, end) of the spoken sentence of step i."""
        v = self._voice[i]
        return (v[0], v[1]) if v else (self._cues[i], self._cues[i])

    def ramp(self, a, b):
        """Eased 0 -> 1 between scene times a and b."""
        if b <= a:
            return float(self.t >= a)
        return ease((self.t - a) / (b - a))

    def lin(self, a, b):
        """Linear 0 -> 1 between scene times a and b."""
        if b <= a:
            return float(self.t >= a)
        return clamp((self.t - a) / (b - a))

    def appear(self, i, delay=0.0, length=0.5):
        """Eased 0 -> 1 starting at step i (+delay)."""
        a = self.cue(i) + delay
        return self.ramp(a, a + length)

    def pulse(self, at, length=0.7):
        """0 -> 1 -> 0 bump starting at time `at` (for highlights)."""
        u = (self.t - at) / length
        return math.sin(math.pi * u) if 0 <= u <= 1 else 0.0

    def during(self, i):
        return self.cue(i) <= self.t < self.stop(i)


# ---------------------------------------------------------------- drawing canvas
class Canvas(Timing):
    def __init__(self, ax, t, info):
        super().__init__(t, info)
        self.ax = ax
        self.texts = []          # (artist, kind) – used by the automatic layout check

    # ---- text -------------------------------------------------------------
    def text(self, x, y, s, size=34, color=FG, weight="medium", ha="center", va="center", alpha=1.0,
             font=None, z=10, linespacing=1.3, box=False, kind="content"):
        """Any text. Math works with $...$, e.g. r"$v_0\\,\\cos\\alpha$"."""
        if alpha <= 0.003:
            return None
        kw = {}
        if font:
            kw["fontfamily"] = font
        if box:
            kw["bbox"] = dict(boxstyle="round,pad=0.7,rounding_size=0.6", fc=PANEL, ec=PANEL_EDGE, lw=2,
                              alpha=0.95 * alpha)
        art = self.ax.text(x, y, s, color=color, fontsize=size, fontweight=weight, ha=ha, va=va, alpha=alpha,
                           zorder=z, linespacing=linespacing, **kw)
        f = sys._getframe(1)
        while f is not None and f.f_code.co_filename == __file__:
            f = f.f_back
        self.texts.append((art, kind, f.f_lineno if f is not None else None))
        return art

    def heading(self, x, y, s, size=60, color=FG, alpha=1.0, ha="center", va="center", z=10):
        """Big display headline (bold display font)."""
        return self.text(x, y, s, size=size, color=color, weight="bold", ha=ha, va=va, alpha=alpha,
                         font=HEAD_FONT, z=z, linespacing=1.18)

    def statement(self, s, t0, t1=None, y=660, size=32, color=FG):
        """Key sentence in a panel. Fades in at scene time t0 (and out at t1)."""
        a = self.ramp(t0, t0 + 0.5)
        if t1 is not None:
            a *= 1 - self.ramp(t1, t1 + 0.35)
        if a > 0.01:
            self.text(W / 2, y - 14 * (1 - a), s, size=size, color=color, alpha=a, z=20, box=True)

    # ---- shapes -----------------------------------------------------------
    def line(self, xs, ys, color=FG, lw=3, alpha=1.0, glow=False, dash=None, z=5):
        xs, ys = np.asarray(xs, float), np.asarray(ys, float)
        if alpha <= 0.003 or len(xs) < 2:
            return
        if glow:
            self.ax.plot(xs, ys, color=color, lw=lw * 4.0, alpha=0.07 * alpha, solid_capstyle="round", zorder=z)
            self.ax.plot(xs, ys, color=color, lw=lw * 2.2, alpha=0.15 * alpha, solid_capstyle="round", zorder=z)
        kw = dict(dashes=dash, dash_capstyle="round") if dash else {}
        self.ax.plot(xs, ys, color=color, lw=lw, alpha=alpha, solid_capstyle="round", zorder=z, **kw)

    def ground(self, y, x0=80, x1=1000, alpha=0.6):
        self.line([x0, x1], [y, y], color=MUTED, lw=3, alpha=alpha)

    def arrow(self, x0, y0, x1, y1, color=FG, lw=6, alpha=1.0, glow=True, z=8, head=1.0):
        if alpha <= 0.003 or math.hypot(x1 - x0, y1 - y0) < 4:
            return
        style = f"-|>,head_length={18 * head:.1f},head_width={10 * head:.1f}"
        if glow:
            self.ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, color=color, lw=lw * 2.6,
                                              alpha=0.15 * alpha, zorder=z, shrinkA=0, shrinkB=0))
        self.ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, color=color, lw=lw, alpha=alpha,
                                          zorder=z, shrinkA=0, shrinkB=0, joinstyle="round", capstyle="round"))

    def ball(self, x, y, r=20, color=PINK, alpha=1.0, z=10):
        if alpha <= 0.003:
            return
        ax = self.ax
        ax.add_patch(Circle((x, y), r + 16, color=color, alpha=0.08 * alpha, zorder=z))
        ax.add_patch(Circle((x, y), r + 8, color=color, alpha=0.18 * alpha, zorder=z))
        ax.add_patch(Circle((x, y), r, color=color, alpha=alpha, zorder=z + 1))
        ax.add_patch(Circle((x - r * 0.32, y + r * 0.32), r * 0.32, color="white", alpha=0.35 * alpha, zorder=z + 2))

    def dot(self, x, y, r=8, color=FG, alpha=1.0, z=9):
        if alpha > 0.003:
            self.ax.add_patch(Circle((x, y), r, color=color, alpha=alpha, zorder=z))

    def ring(self, x, y, r, color=YELLOW, lw=3, alpha=1.0, z=9):
        if alpha > 0.003:
            self.ax.add_patch(Circle((x, y), r, fill=False, ec=color, lw=lw, alpha=alpha, zorder=z))

    def arc(self, x, y, r, theta1, theta2, color=YELLOW, lw=4, alpha=1.0, z=7):
        if alpha > 0.003 and theta2 > theta1:
            self.ax.add_patch(Arc((x, y), 2 * r, 2 * r, theta1=theta1, theta2=theta2, color=color, lw=lw,
                                  alpha=alpha, zorder=z))

    def panel(self, x, y, w, h, edge=None, fill=PANEL, alpha=1.0, radius=30, lw=4, glow=False, z=5):
        """Rounded rectangle centred at (x, y)."""
        if alpha <= 0.003:
            return
        if glow and edge:
            self.ax.add_patch(FancyBboxPatch((x - w / 2 - 8, y - h / 2 - 8), w + 16, h + 16,
                                             boxstyle=f"round,pad=0,rounding_size={radius + 8}", fc=edge,
                                             ec="none", alpha=0.08 * alpha, zorder=z - 1))
        self.ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                                         fc=fill, ec=edge or "none", lw=lw if edge else 0, alpha=alpha, zorder=z))

    def polygon(self, pts, color=FG, alpha=1.0, z=5):
        if alpha > 0.003:
            self.ax.add_patch(Polygon(pts, closed=True, color=color, alpha=alpha, zorder=z))

    def rect(self, x, y, w, h, color=FG, alpha=1.0, z=5):
        """Plain rectangle with lower-left corner (x, y)."""
        if alpha > 0.003:
            self.ax.add_patch(Rectangle((x, y), w, h, color=color, alpha=alpha, zorder=z))
