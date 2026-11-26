from engine.style import *

TOPIC = "Escape Velocity"
TITLE = "How fast must you go to escape Earth? #physics #shorts"
DESCRIPTION = (
    "Earth's escape speed comes from an energy budget, not a boundary where gravity stops. "
    "See why mass cancels, and why real rockets need not launch at escape speed."
)
TAGS = ["physics", "escape velocity", "gravity", "energy", "space"]

EPISODE = 29

# ------------------------------------------------------------ physics
G = 6.67430e-11
EARTH_MASS = 5.972e24
EARTH_RADIUS = 6.371e6
MU = G * EARTH_MASS
ESCAPE_SPEED = math.sqrt(2 * MU / EARTH_RADIUS)
SPEED_KMS = ESCAPE_SPEED / 1000

WORDS = [
    "zero", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen",
    "fourteen", "fifteen", "sixteen", "seventeen",
    "eighteen", "nineteen",
]
SPEED_TENTHS = int(round(SPEED_KMS * 10))

FACTS = {
    "speed": f"{SPEED_KMS:.1f}",
    "speed_spoken": (
        WORDS[SPEED_TENTHS // 10]
        + " point "
        + WORDS[SPEED_TENTHS % 10]
    ),
}


# ------------------------------------------------------------ drawing helpers
def earth(c, x, y, radius, alpha=1):
    c.ball(x, y, r=radius, color=BLUE, alpha=alpha)
    c.ring(x, y, radius + 9, BLUE, lw=3, alpha=0.35 * alpha)
    # Simple stylized land patches, contained inside the disk.
    c.polygon([
        (x - radius * 0.65, y + radius * 0.30),
        (x - radius * 0.25, y + radius * 0.65),
        (x + radius * 0.04, y + radius * 0.38),
        (x - radius * 0.12, y + radius * 0.02),
        (x - radius * 0.44, y - radius * 0.08),
    ], GREEN, 0.65 * alpha)
    c.polygon([
        (x + radius * 0.12, y - radius * 0.05),
        (x + radius * 0.57, y + radius * 0.04),
        (x + radius * 0.53, y - radius * 0.38),
        (x + radius * 0.25, y - radius * 0.65),
    ], GREEN, 0.65 * alpha)


# ------------------------------------------------------------ 1 · hook
def hook(c):
    c.heading(520, 1650, "LEAVE EARTH\nFOR GOOD?", size=64)

    earth(c, 520, 900, 240)
    c.line([520, 520], [1150, 1430], PINK, lw=4,
           alpha=0.5, dash=(3, 5))
    c.arrow(650, 1190, 650, 1430, PINK, lw=7)
    c.ball(520, 1158, r=24, color=PINK)

    a = c.appear(1, 0.15, 0.6)
    c.panel(520, 650, 760, 110, edge=YELLOW, alpha=a)
    c.text(520, 650, "Space is not the finish line",
           size=36, color=YELLOW, alpha=a)

    # The initial cover remains legible while the ball begins its climb.
    launch = c.cue(1) + 0.3
    elapsed = max(0.0, c.t - launch)
    radial = (1 + 1.5 * elapsed) ** (2 / 3)
    y = 1158 + 95 * (radial - 1)
    if elapsed > 0:
        c.ball(520, min(y, 1475), r=24, color=PINK)


# ------------------------------------------------------------ 2 · weakening gravity
def weakening(c):
    earth(c, 520, 800, 155)

    c.line([520, 520], [965, 1470], PINK, lw=3,
           alpha=0.35, dash=(3, 5))

    # A radial, marginal-escape trajectory:
    # r/R = (1 + 3*tau/2)^(2/3), at a constant physical time scale.
    launch = c.cue(0) + 0.25
    animation_length = 4.0
    tau = clamp((c.t - launch) / animation_length) * 6.0
    radial = (1 + 1.5 * tau) ** (2 / 3)
    y = 800 + 155 * radial

    c.ball(520, y, r=22, color=PINK)
    gravity_length = 150 / radial ** 2
    c.arrow(570, y, 570, y - gravity_length, GREEN, lw=5)

    c.text(520, 595, "Engines off", size=34, color=MUTED,
           alpha=c.appear(0, 0.1))

    a = c.appear(1, 0.2, 0.6)
    c.text(520, 1570, "Farther away → weaker gravity",
           size=36, color=GREEN, alpha=a)

    # Snapshot force arrows make the inverse-square trend visible.
    for i, r in enumerate((1.2, 2.1, 3.5)):
        yy = 800 + 155 * r
        aa = c.appear(1, 0.3 + i * 0.3, 0.4)
        c.dot(520, yy, 9, PINK, 0.5 * aa)
        c.arrow(360, yy, 360, yy - 150 / r ** 2,
                GREEN, lw=5, alpha=aa, glow=False)

    c.text(520, 1160, r"$F_g \propto \frac{1}{r^2}$",
           size=44, color=GREEN, alpha=a)


# ------------------------------------------------------------ 3 · energy budget
def energy(c):
    a = c.appear(0, 0.1, 0.6)
    c.text(520, 1550, "Energy to coast all the way out",
           size=35, color=FG, alpha=a)

    # Move and shrink the graph before revealing the equations below it.
    compact = c.appear(1, 0.0, 0.5)
    x0, width = 160, 720
    y0 = lerp(850, 1170, compact)
    height = lerp(420, 180, compact)

    # Exact shape of the potential-energy climb, in normalized units.
    c.line([x0, x0 + width], [y0, y0], MUTED, lw=2, alpha=a)
    c.line([x0, x0], [y0, y0 + height + 50], MUTED, lw=2, alpha=a)
    c.line([x0, x0 + width], [y0 + height, y0 + height],
           YELLOW, lw=2, alpha=0.55 * a, dash=(4, 5))
    c.text(x0 + 20, y0 + height + 35, "Energy required",
           size=28, color=MUTED, ha="left", alpha=a)

    p = c.ramp(c.cue(0) + 0.3, c.cue(0) + 3.3)
    radii = np.linspace(1, 1 + 7 * p, 90)
    xs = x0 + (radii - 1) / 7 * width
    ys = y0 + height * (1 - 1 / radii)
    c.line(xs, ys, PINK, lw=6, alpha=a, glow=True)
    c.ball(float(xs[-1]), float(ys[-1]), r=16, color=PINK, alpha=a)

    c.text(520, y0 - 90, "Distance from Earth →",
           size=30, color=MUTED, alpha=a)
    c.text(520, 1460, "Finite energy, unlimited distance",
           size=34, color=YELLOW, alpha=a)

    b = c.appear(1, 0.6, 0.5)
    c.panel(520, 850, 780, 310, edge=YELLOW, alpha=b)
    c.text(520, 940, r"$\frac{1}{2}mv^2=\frac{GMm}{R}$",
           size=50, alpha=b)

    result = c.appear(1, 1.3, 0.7)
    c.text(520, 820, r"$v_{\rm esc}=\sqrt{\frac{2GM}{R}}$",
           size=52, color=YELLOW, alpha=result)
    c.text(520, 650, "Same escape speed for any object mass",
           size=31, color=PINK, alpha=result)


# ------------------------------------------------------------ 4 · real number and assumptions
def surface_test(c):
    earth(c, 520, 1110, 205)

    a = c.appear(0, 0.1, 0.7)
    c.heading(520, 1520, FACTS["speed"] + " km/s",
              size=82, color=YELLOW, alpha=a)
    c.text(520, 1410, "Earth's surface escape speed",
           size=34, alpha=a)

    b = c.appear(1, 0.1, 0.6)
    c.panel(520, 790, 800, 230, edge=MUTED, alpha=b)
    c.text(520, 855, "No atmosphere • No rotation",
           size=32, color=MUTED, alpha=b)
    c.text(520, 765, "Earth's gravity only",
           size=32, color=GREEN, alpha=b)

    d = c.appear(2, 0.1, 0.6)
    c.text(520, 610, "Coasting threshold ≠ launch requirement",
           size=30, color=YELLOW, alpha=d)


# ------------------------------------------------------------ 5 · takeaway
def outro(c):
    a = c.appear(0, 0.1, 0.6)
    c.heading(520, 1580, "ESCAPE IS AN\nENERGY BUDGET", size=60, alpha=a)

    earth(c, 330, 1080, 155)
    c.line([480, 860], [1110, 1340], PINK, lw=4,
           alpha=0.5 * a, dash=(3, 5))
    c.arrow(690, 1240, 860, 1340, PINK, lw=6, alpha=a)
    c.ball(860, 1340, r=23, color=PINK, alpha=a)

    c.text(520, 825, "Enough to coast away without returning",
           size=33, color=YELLOW, alpha=a)

    b = c.appear(1, 0.1, 0.6)
    c.panel(520, 650, 660, 120, fill=PINK, alpha=b, radius=55)
    c.text(520, 650, "Follow for more physics",
           size=38, color=FG, weight="bold", alpha=b)


# ------------------------------------------------------------ narration
SCENES = [
    Scene(hook, header=None, steps=[
        Step(
            "How fast can you leave Earth forever?",
            sfx=[("whoosh", 0.1)],
        ),
        Step(
            "Reaching space isn't enough; you need enough speed never to fall back.",
            pause=0.4,
        ),
    ]),
    Scene(weakening, header="Gravity fades", steps=[
        Step(
            "After the engines stop, Earth's gravity keeps slowing you down.",
            pause=0.6,
        ),
        Step(
            "But gravity weakens with distance, so escaping takes a finite amount of energy.",
            pause=0.5,
            sfx=[("note", 0.3, {"n": 2})],
        ),
    ]),
    Scene(energy, header="Pay the energy cost", steps=[
        Step(
            "Escape requires enough kinetic energy to climb Earth's entire gravitational energy well.",
            pause=0.7,
        ),
        Step(
            "Equating those energies gives escape speed; notice the object's mass cancels.",
            pause=0.8,
            sfx=[("chime", 1.4, {"n": 4})],
        ),
    ]),
    Scene(surface_test, header="Earth's escape speed", steps=[
        Step(
            "At Earth's surface, that's {speed_spoken} kilometers per second.",
            sub="At Earth's surface: {speed} km/s.",
            pause=0.6,
            sfx=[("chime", 0.3, {"n": 5})],
        ),
        Step(
            "This assumes no atmosphere, no planetary rotation, and only Earth's gravity.",
            pause=0.3,
        ),
        Step(
            "Real rockets thrust along the way, so this isn't a launch speed requirement.",
            pause=0.3,
        ),
    ]),
    Scene(outro, header=None, steps=[
        Step(
            "Escape speed means enough initial energy to coast away without returning.",
            pause=0.5,
        ),
        Step(
            "Follow for more physics like this.",
            pause=0.6,
            sfx=[("note", 0.15, {"n": 4})],
        ),
    ]),
]
