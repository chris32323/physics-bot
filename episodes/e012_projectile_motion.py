"""Projectile motion – which angle throws the farthest?

This file is exactly what the AI writer produces every day: narration steps
(the voice sets the timing) plus one draw function per scene.
"""
from engine.style import *

TOPIC = "Projectile Motion"
TITLE = "Which angle throws the farthest? #physics #shorts"
DESCRIPTION = ("Why 45° gives the longest throw – split the velocity, watch both motions, "
               "derive the range formula and test five angles.")
TAGS = ["physics", "projectile motion", "kinematics", "science", "math"]
TEASER = "Why doesn't the Moon fall down to Earth?"

# ---------------------------------------------------------------- physics (all numbers come from here)
V0, G_ = 20.0, 9.81


def reach(deg):
    return V0 ** 2 * math.sin(math.radians(2 * deg)) / G_


def flight_time(deg):
    return 2 * V0 * math.sin(math.radians(deg)) / G_


def pos(deg, t):
    a = math.radians(deg)
    return V0 * math.cos(a) * t, V0 * math.sin(a) * t - 0.5 * G_ * t * t


def vel(deg, t):
    a = math.radians(deg)
    return V0 * math.cos(a), V0 * math.sin(a) - G_ * t


FACTS = {"g": f"{G_:.1f}", "v0": f"{V0:.0f}", "R45": f"{reach(45):.0f}"}


# ---------------------------------------------------------------- 1 · hook
HX0, HGY, HSC = 140, 840, 19.5


def hook(c):
    c.heading(W / 2, 1500, "Which angle throws\nthe farthest?", size=64)
    c.ground(HGY)
    t0 = c.cue(0) + 0.1
    p = c.ramp(t0, t0 + 2.4)
    if p > 0:
        ts = np.linspace(0, flight_time(45) * p, 90)
        xs = [HX0 + pos(45, s)[0] * HSC for s in ts]
        ys = [HGY + pos(45, s)[1] * HSC for s in ts]
        c.line(xs, ys, color=PINK, lw=4, alpha=0.55, dash=(2, 3))
        c.ball(xs[-1], ys[-1])
    else:
        c.ball(HX0, HGY)                     # already visible in the very first frame (cover)
    vs, ve = c.voice(1)
    for i, (lab, col) in enumerate([("15°?", GREEN), ("45°?", YELLOW), ("75°?", BLUE)]):
        t = vs + i * (ve - vs) / 3
        a = c.ramp(t, t + 0.4)
        c.heading(240 + 300 * i, 680 - 20 * (1 - a), lab, size=56, color=col, alpha=a)


def hook_sounds(tm):
    vs, ve = tm.voice(1)
    return [("pop", vs + i * (ve - vs) / 3, {"n": 5 + i}) for i in range(3)]


# ---------------------------------------------------------------- 2 · split the velocity
SX0, SGY, SL, SA = 210, 880, 540, 60


def split(c):
    c.ground(SGY)
    a = math.radians(SA)
    tipx, tipy = SX0 + SL * math.cos(a), SGY + SL * math.sin(a)
    g1 = c.appear(0, 0.2, 1.0)
    c.arrow(SX0, SGY, SX0 + (tipx - SX0) * g1, SGY + (tipy - SGY) * g1, PINK, lw=7)
    c.text((SX0 + tipx) / 2 + 45, (SGY + tipy) / 2 - 10, r"$v_0$", size=46, color=PINK, alpha=c.appear(0, 0.9, 0.4))
    aa = c.appear(0, 1.4, 0.6)
    c.arc(SX0, SGY, 110, 0, SA * aa)
    c.text(SX0 + 140, SGY + 62, r"$\alpha$", size=42, color=YELLOW, alpha=aa)
    gd = c.appear(1, 0.2, 0.6)
    c.line([tipx, tipx], [SGY, tipy], color=MUTED, lw=2, alpha=0.6 * gd, dash=(4, 4))
    c.line([SX0, tipx], [tipy, tipy], color=MUTED, lw=2, alpha=0.6 * gd, dash=(4, 4))
    h = c.appear(2, 0.1, 0.9)
    c.arrow(SX0, SGY, SX0 + (tipx - SX0) * h, SGY, BLUE, lw=7)
    c.text(SX0 + (tipx - SX0) / 2 + 40, SGY - 62, r"$v_x = v_0\,\cos\alpha$", size=38, color=BLUE,
           alpha=c.appear(2, 0.6, 0.5))
    v = c.appear(3, 0.1, 0.9)
    c.arrow(SX0, SGY, SX0, SGY + (tipy - SGY) * v, ORANGE, lw=7)
    c.text(SX0 + 30, tipy + 64, r"$v_y = v_0\,\sin\alpha$", size=38, color=ORANGE, ha="left",
           alpha=c.appear(3, 0.6, 0.5))
    hl = c.pulse(c.cue(4) + 0.3, 1.6)          # "these two motions don't affect each other"
    if hl > 0:
        c.arrow(SX0, SGY, tipx, SGY, BLUE, lw=7 + 6 * hl, alpha=0.35 * hl, glow=False)
        c.arrow(SX0, SGY, SX0, tipy, ORANGE, lw=7 + 6 * hl, alpha=0.35 * hl, glow=False)
    c.ball(SX0, SGY)


# ---------------------------------------------------------------- 3 · two motions at once
FX0, FGY, FSC, FA = 150, 880, 22.0, 60
FT = flight_time(FA)
FLIGHT = 3.6                 # seconds of video for the whole flight
K = 9.0                      # arrow length per m/s
STROBE = [FT * k / 6 for k in range(7)]


def fxy(t):
    x, y = pos(FA, t)
    return FX0 + x * FSC, FGY + max(y, 0) * FSC


def flight(c):
    c.ground(FGY)
    track = FGY - 45
    c.line([FX0, 960], [track, track], color=BLUE, lw=2, alpha=0.25)
    c.line([70, 70], [FGY, FGY + 370], color=ORANGE, lw=2, alpha=0.25)
    ga = c.appear(0, 0.0, 0.5)
    c.arrow(930, 1520, 930, 1400, GREEN, lw=6, alpha=ga)
    c.text(978, 1462, r"$g$", size=40, color=GREEN, alpha=ga)

    launch = c.cue(0) + 0.35
    ph = clamp((c.t - launch) / FLIGHT) * FT
    flying = 0 < ph < FT
    ts = np.linspace(0, ph, 160)
    pts = [fxy(s) for s in ts]
    c.line([p[0] for p in pts], [p[1] for p in pts], color=PINK, lw=3, alpha=0.5, glow=True)

    # strobe marks + projections where the ball has already been
    for k, s in enumerate(STROBE):
        if s <= ph + 1e-9:
            x, y = fxy(s)
            c.dot(x, y, 9, PINK, 0.45, z=6)
            c.dot(x, track, 8, BLUE, 0.5)
            c.dot(70, y, 8, ORANGE, 0.5)

    # step 1: equal horizontal arrows -> constant speed
    vs, ve = c.voice(1)
    for k, s in enumerate(STROBE):
        x, y = fxy(s)
        a = c.ramp(vs + 0.6 + 0.25 * k, vs + 0.9 + 0.25 * k)
        vx, vy = vel(FA, s)
        c.arrow(x, y, x + vx * K, y, BLUE, lw=5, alpha=0.9 * a, glow=False)
        c.dot(x, track, 11, BLUE, a * c.pulse(vs + 0.6 + 0.25 * k, 0.6))
    c.text(540, track - 50, "equal spacing = constant speed", size=26, color=BLUE, alpha=c.appear(1, 2.4, 0.5))

    # step 2: vertical arrows shrink, flip -> gravity
    vs2, _ = c.voice(2)
    for k, s in enumerate(STROBE):
        x, y = fxy(s)
        a = c.ramp(vs2 + 0.6 + 0.3 * k, vs2 + 0.9 + 0.3 * k)
        vx, vy = vel(FA, s)
        c.arrow(x, y, x, y + vy * K, ORANGE, lw=5, alpha=0.9 * a, glow=False)

    # step 3: top of the arc
    ax_, ay_ = fxy(FT / 2)
    top = c.appear(3, 0.3, 0.5)
    c.ring(ax_, ay_, 30 + 12 * c.pulse(c.cue(3) + 0.3, 0.8), ORANGE, lw=3, alpha=top)
    c.text(ax_ + 70, ay_ + 64, r"$v_y = 0$", size=38, color=ORANGE, alpha=top)

    # step 4: the way down mirrors the way up
    m = c.appear(4, 0.4, 0.6)
    c.line([ax_, ax_], [FGY, ay_ - 40], color=MUTED, lw=2, alpha=0.7 * m, dash=(4, 4))
    for k in range(3):
        at = c.cue(4) + 0.8 + 0.45 * k
        for s in (STROBE[k], STROBE[6 - k]):
            x, y = fxy(s)
            c.ring(x, y, 24, YELLOW, lw=3, alpha=c.pulse(at, 0.8))

    # the moving ball with its live velocity arrows
    if flying:
        x, y = fxy(ph)
        vx, vy = vel(FA, ph)
        c.dot(x, track, 13, BLUE, 1.0, z=9)
        c.dot(70, y, 13, ORANGE, 1.0, z=9)
        c.line([x, x], [track, y], color=BLUE, lw=1.5, alpha=0.4, dash=(1, 3))
        c.line([70, x], [y, y], color=ORANGE, lw=1.5, alpha=0.4, dash=(1, 3))
        c.arrow(x, y, x + vx * K, y, BLUE, lw=6)
        c.arrow(x, y, x, y + vy * K, ORANGE, lw=6)
    x, y = fxy(ph)
    c.ball(x, y)


# ---------------------------------------------------------------- 4 · the formula
def formula(c):
    dim = 1 - 0.5 * c.appear(3, 0.0, 0.8)
    rows = [(0, 1548, r"$x(t) = v_0\,\cos\alpha \cdot t$", BLUE),
            (1, 1420, r"$y(t) = v_0\,\sin\alpha \cdot t \;-\; \frac{1}{2}\,g\,t^2$", ORANGE),
            (2, 1282, r"lands at  $t = \frac{2\,v_0\,\sin\alpha}{g}$", FG)]
    for i, y, s, col in rows:
        a = c.appear(i, 0.15, 0.6)
        c.text(W / 2 + 40 * (1 - a), y, s, size=44, color=col, alpha=a * dim)

    _, ve = c.voice(3)
    b = c.ramp(ve - 0.25, ve + 0.45)
    if b > 0:
        s = 0.96 + 0.04 * b
        c.panel(W / 2, 1085, (W - 280) * s, 240 * s, edge=YELLOW, alpha=b, glow=True)
        hl = c.pulse(c.cue(4), c.dur(4))
        if hl > 0:
            c.panel(W / 2, 1085, W - 262, 258, edge=YELLOW, fill="none", lw=10, alpha=0.25 * hl, z=4)
        c.text(W / 2, 1167, "Range", size=30, color=YELLOW, weight="bold", alpha=b, z=6)
        c.text(W / 2, 1055, r"$R = \frac{v_0^2\cdot\sin(2\alpha)}{g}$", size=58, alpha=b, z=6)

    p = c.appear(5, 0.0, 0.5)
    if p > 0:
        x0, y0, w, h = 220, 650, 640, 210
        c.line([x0, x0 + w], [y0, y0], color=MUTED, lw=2, alpha=p)
        vs, ve = c.voice(5)
        n = max(int(160 * c.ramp(vs + 0.2, ve + 0.3)), 2)
        al = np.linspace(0, 90, 160)[:n]
        c.line(x0 + al / 90 * w, y0 + np.sin(np.radians(2 * al)) * h, color=YELLOW, lw=5, alpha=p, glow=True)
        for deg in (0, 45, 90):
            c.text(x0 + deg / 90 * w, y0 - 40, f"{deg}°", size=24, color=MUTED, alpha=p)
        c.text(x0 + w + 24, y0 + 18, r"$\alpha$", size=30, color=MUTED, alpha=p)
        c.text(x0 - 22, y0 + h, r"$\sin 2\alpha$", size=26, color=YELLOW, ha="right", alpha=p)
        q = c.appear(6, 0.2, 0.4)
        c.line([x0 + w / 2] * 2, [y0, y0 + h], color=YELLOW, lw=2, alpha=q, dash=(4, 4))
        c.dot(x0 + w / 2, y0 + h, 22, YELLOW, 0.2 * q)
        c.dot(x0 + w / 2, y0 + h, 12, YELLOW, q)
        c.text(x0 + w / 2, y0 + h + 44, "Maximum at 45°", size=30, color=YELLOW, weight="bold", alpha=q)


def formula_sounds(tm):
    _, ve = tm.voice(3)
    return [("chime", ve - 0.2, {"n": 2})]


# ---------------------------------------------------------------- 5 · the proof
ANGLES = [(15, GREEN), (30, BLUE), (45, YELLOW), (60, ORANGE), (75, PINK)]
PX0, PGY, PSC = 110, 900, 21.0


def proof_clock(tm):
    """Launch after sentence 0; the 45° ball lands just as sentence 1 starts."""
    launch = tm.voice(0)[1] + 0.15
    rate = flight_time(45) / (tm.cue(1) + 0.25 - launch)      # physical seconds per video second
    return launch, rate


def proof(c):
    c.ground(PGY, 70, W - 70)
    for m in range(0, 45, 10):
        c.line([PX0 + m * PSC] * 2, [PGY, PGY - 15], color=MUTED, lw=2, alpha=0.6)
        c.text(PX0 + m * PSC, PGY - 46, f"{m} m", size=20, color=MUTED)
    vs, ve = c.voice(0)
    for i, (deg, col) in enumerate(ANGLES):
        t = vs + 0.4 + i * 0.3
        c.heading(130 + i * 205, 1580, f"{deg}°", size=40, color=col, alpha=c.ramp(t, t + 0.35))

    launch, rate = proof_clock(c)
    ph = max(c.t - launch, 0) * rate
    landed = {}
    for deg, col in ANGLES:
        T = flight_time(deg)
        ts = np.linspace(0, min(ph, T), 120)
        xs = [PX0 + pos(deg, s)[0] * PSC for s in ts]
        ys = [PGY + max(pos(deg, s)[1], 0) * PSC for s in ts]
        if ph > 0:
            if deg == 45:
                c.line(xs, ys, col, lw=6, alpha=0.95, glow=True, z=6)
            else:
                c.line(xs, ys, col, lw=3.5, alpha=0.75)
        if ph < T:
            c.ball(xs[-1], ys[-1], r=13, color=col)
        else:
            landed[deg] = (xs[-1], col, (ph - T) / rate)

    rows = {15: (300, 790), 30: (300, 730), 45: (300, 670), 60: (760, 790), 75: (760, 730)}
    pair_30 = c.pulse(c.cue(2) + 0.4, 1.4)
    pair_15 = c.pulse(c.cue(3) + 0.4, 1.4)
    for deg, (lx, col, since) in landed.items():
        fresh = max(0.0, 1 - since / 0.5)
        if fresh > 0:
            c.dot(lx, PGY, 10 + 30 * (1 - fresh), col, 0.35 * fresh, z=11)
        c.dot(lx, PGY, 10, col, 1.0, z=12)
        hl = pair_30 if deg in (30, 60) else pair_15 if deg in (15, 75) else 0.0
        x, y = rows[deg]
        if hl > 0:
            c.panel(x, y, 330, 54, fill=col, alpha=0.18 * hl, radius=27, z=4)
        c.text(x, y, f"{deg}°  →  {reach(deg):.1f} m", size=30, color=col, alpha=min(since / 0.3, 1),
               weight="bold" if deg == 45 or hl > 0.3 else "medium")
    if 45 in landed:
        c.text(landed[45][0], PGY + 64, "★", size=40, color=YELLOW, alpha=min(landed[45][2] / 0.3, 1),
               font="DejaVu Sans")
    c.ring(PX0 + reach(30) * PSC, PGY, 34, YELLOW, lw=4, alpha=pair_30)
    c.ring(PX0 + reach(15) * PSC, PGY, 34, YELLOW, lw=4, alpha=pair_15)


def proof_sounds(tm):
    launch, rate = proof_clock(tm)
    notes = {15: 0, 75: 0, 30: 2, 60: 2, 45: 3}            # equal range = equal note
    out = [("whoosh", launch, {})]
    for deg, n in notes.items():
        t = launch + flight_time(deg) / rate
        out.append(("land", t, {"n": n}))
        if deg == 45:
            out.append(("chime", t + 0.05, {"n": 3}))
    return out


# ---------------------------------------------------------------- 6 · outro
def outro(c):
    a = c.appear(0, 0.1)
    c.text(W / 2, 1565, "Remember", size=36, color=YELLOW, weight="bold", alpha=a)
    c.heading(W / 2, 1445, "45° = maximum range", size=52, alpha=a)
    c.text(W / 2, 1350, "(real balls with air drag: a bit less)", size=26, color=MUTED, alpha=c.appear(1, 0.2))
    d = c.appear(2, 0.1)
    c.text(W / 2, 1112, "Tomorrow:", size=32, color=BLUE, weight="bold", alpha=d)
    c.heading(W / 2, 990, wrap(TEASER, 22), size=48, alpha=d)
    e = c.appear(3, 0.0, 0.6)
    if e > 0:
        s = 0.9 + 0.1 * e
        c.panel(W / 2, 720, 660 * s, 120 * s, fill=PINK, alpha=e, radius=60)
        c.text(W / 2, 720, "Follow for daily physics", size=29, color="white", weight="bold",
               va="center_baseline", alpha=e, z=6)


# ---------------------------------------------------------------- scenes
SCENES = [
    Scene(hook, header=None, sounds=hook_sounds, steps=[
        Step("Which angle throws a ball the farthest?", sfx=[("whoosh", 0.1), ("land", 2.5, {"n": 1})]),
        Step("Fifteen degrees? Forty-five? Seventy-five?", sub="15°? 45°? 75°?", pause=0.2),
        Step("The answer fits into one short formula. Let's build it.", pause=0.3),
    ]),
    Scene(split, header="Split the velocity", steps=[
        Step("Every throw starts with one speed, v zero, at an angle alpha.",
             sub="Every throw starts with one speed, v₀, at an angle α.", sfx=[("note", 0.25, {"n": 0})]),
        Step("We can split it into two parts:", pause=0.2),
        Step("a horizontal part, v zero cosine alpha,", sub="a horizontal part, v₀ · cos α,",
             sfx=[("note", 0.15, {"n": 2})]),
        Step("and a vertical part, v zero sine alpha.", sub="and a vertical part, v₀ · sin α.",
             sfx=[("note", 0.15, {"n": 3})]),
        Step("The trick: these two motions don't affect each other.", pause=0.6, sfx=[("pop", 0.3, {"n": 5})]),
    ]),
    Scene(flight, header="Two motions at once", steps=[
        Step("Now watch the flight.", pause=2.4, sfx=[("whoosh", 0.35), ("land", 3.95, {"n": 1})]),
        Step("Sideways, nothing pushes the ball, so its horizontal speed never changes.", pause=0.6),
        Step("Upward, gravity slows it down, by {g} meters per second, every second.",
             sub="Upward, gravity slows it down: {g} m/s every second.", pause=0.8),
        Step("At the very top, the vertical speed is zero.", pause=0.3, sfx=[("note", 0.3, {"n": 4})]),
        Step("Then gravity pulls it back, and the way down mirrors the way up.", pause=0.8),
    ]),
    Scene(formula, header="The formula", sounds=formula_sounds, steps=[
        Step("Sideways, the distance just grows with time.", sfx=[("note", 0.15, {"n": 0})]),
        Step("Upward, gravity takes away one half g t squared.", sub="Upward, gravity takes away ½ g t².",
             sfx=[("note", 0.15, {"n": 1})]),
        Step("So the ball is back down after two v zero sine alpha, over g.",
             sub="So the ball is back down after 2 v₀ sin α / g.", pause=0.3, sfx=[("note", 0.15, {"n": 2})]),
        Step("Put that time into x, and you get the range:", pause=0.2),
        Step("v zero squared, times sine of two alpha, over g.", sub="v₀² · sin(2α) / g", pause=0.6),
        Step("And sine of two alpha is biggest when two alpha is ninety degrees,",
             sub="And sin(2α) is biggest when 2α is 90°,", pause=0.3),
        Step("so alpha is forty-five degrees.", sub="so α is 45°.", pause=0.8, sfx=[("chime", 0.25, {"n": 4})]),
    ]),
    Scene(proof, header="The proof", sounds=proof_sounds, steps=[
        Step("Let's test it: five throws, same speed, different angles.", pause=2.3),
        Step("Forty-five degrees flies the farthest: about {R45} meters.", pause=0.4),
        Step("And look: thirty and sixty degrees land in exactly the same spot.", pause=0.6),
        Step("Fifteen and seventy-five, too. Angles that add up to ninety always tie.", pause=0.8),
    ]),
    Scene(outro, header=None, steps=[
        Step("So remember: forty-five degrees gives the maximum range.", sub="So remember: 45° gives the maximum range."),
        Step("With air resistance, the best angle is a little lower.", pause=0.3),
        Step("Tomorrow: " + TEASER[0].lower() + TEASER[1:], pause=0.3),
        Step("Follow, so you don't miss it.", pause=0.8, sfx=[("chime", 0.05, {"n": 2})]),
    ]),
]
