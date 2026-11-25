from engine.style import *

TOPIC = "Orbital Speed"
TITLE = "Why higher satellites move slower #physics #shorts"
DESCRIPTION = (
    "Higher circular orbits need less speed. Compare two Earth satellites "
    "and see how gravity sets their orbital speeds."
)
TAGS = ["physics", "satellites", "orbital speed", "gravity", "space"]

# Episode 28. Ideal circular orbits around a spherical Earth.
MU = 3.986004418e14
EARTH_RADIUS = 6_371_000.0
LOW_ALT = 400_000.0
HIGH_ALT = 35_786_000.0

LOW_RADIUS = EARTH_RADIUS + LOW_ALT
HIGH_RADIUS = EARTH_RADIUS + HIGH_ALT
LOW_SPEED = math.sqrt(MU / LOW_RADIUS)
HIGH_SPEED = math.sqrt(MU / HIGH_RADIUS)

FACTS = {
    "low_h": f"{LOW_ALT / 1000:,.0f}",
    "high_h": f"{HIGH_ALT / 1000:,.0f}",
    "low_v": f"{LOW_SPEED / 1000:.1f}",
    "high_v": f"{HIGH_SPEED / 1000:.1f}",
}


def earth(c, x, y, radius):
    c.ball(x, y, r=radius, color=BLUE)
    c.arc(x, y, radius * 0.78, 55, 155, GREEN, lw=12, alpha=0.7)
    c.arc(x, y, radius * 0.56, 220, 315, GREEN, lw=10, alpha=0.65)


def satellite(c, x, y, color, alpha=1):
    c.panel(x - 28, y, 25, 34, fill=BLUE, radius=3, lw=1, alpha=alpha)
    c.panel(x + 28, y, 25, 34, fill=BLUE, radius=3, lw=1, alpha=alpha)
    c.panel(x, y, 25, 27, fill=color, radius=5, lw=1, alpha=alpha)


def orbital_pair(c, start):
    """Both circular motions share a constant physical time scale.

    This introductory diagram uses illustrative radii, not the later
    numerical examples. Angular speed scales as radius to minus three halves.
    """
    cx, cy = 510, 1110
    inner, outer = 155.0, 345.0
    elapsed = max(0.0, c.t - start)
    omega = 0.62

    earth(c, cx, cy, 76)
    for radius, col, phase in [
        (inner, PINK, 0.65),
        (outer, PURPLE, 2.4),
    ]:
        c.ring(cx, cy, radius, col, lw=3, alpha=0.4)
        rate = omega * (inner / radius) ** 1.5
        angle = phase + rate * elapsed
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)

        trail = np.linspace(angle - min(rate * elapsed, 0.8), angle, 35)
        c.line(
            cx + radius * np.cos(trail),
            cy + radius * np.sin(trail),
            col, lw=5, alpha=0.7,
        )
        satellite(c, x, y, col)

        length = 100 * math.sqrt(inner / radius)
        c.arrow(
            x, y,
            x - length * math.sin(angle),
            y + length * math.cos(angle),
            col, lw=4, head=0.7,
        )


# ---------------------------------------------------------------- 1 · hook
def hook(c):
    c.heading(510, 1620, "HIGHER ORBIT.\nLOWER SPEED?", size=62)
    orbital_pair(c, c.cue(0))
    c.text(510, 680, "Circular orbits", size=34, color=YELLOW,
           alpha=c.appear(1))
    c.text(510, 610, "Ignore air resistance and other bodies", size=28,
           color=MUTED, alpha=c.appear(2))


# ---------------------------------------------------------------- 2 · the balance
def balance(c):
    earth(c, 260, 1070, 108)
    satellite(c, 810, 1070, PINK)

    # Explicit foreground layers keep the full radius visible over Earth.
    c.line([260, 810], [1070, 1070], MUTED, lw=2,
           alpha=0.55, dash=(4, 5), z=20)
    c.dot(260, 1070, 8, FG, 1, z=21)
    c.text(535, 1005, r"$r$", size=42, color=YELLOW)
    c.text(260, 900, "Earth’s center", size=28, color=MUTED)

    a = c.appear(0, 0.1, 0.7)
    c.arrow(790, 1100, 565, 1100, GREEN, lw=7, alpha=a)
    c.text(680, 1190, "Gravity", size=36, color=GREEN, alpha=a)

    b = c.appear(1, 0.1, 0.7)
    c.text(510, 1515, "Gravity = inward acceleration", size=34, alpha=b)
    c.text(510, 1375, r"$\frac{GM}{r^2}=\frac{v^2}{r}$",
           size=60, alpha=b)

    d = c.appear(2, 0.1, 0.7)
    c.panel(510, 730, 700, 200, edge=YELLOW, alpha=d)
    c.text(510, 745, r"$v=\sqrt{\frac{GM}{r}}$",
           size=64, color=YELLOW, alpha=d)
    c.text(510, 595, "G = gravitational constant   •   M = Earth’s mass",
           size=28, color=MUTED, alpha=d)


# ---------------------------------------------------------------- 3 · real numbers
def comparison(c):
    rows = [
        (0, 1480, LOW_SPEED, PINK, FACTS["low_h"], FACTS["low_v"]),
        (1, 1230, HIGH_SPEED, PURPLE, FACTS["high_h"], FACTS["high_v"]),
    ]
    for step, y, speed, col, altitude, value in rows:
        a = c.appear(step, 0.1, 0.6)
        c.panel(510, y - 15, 820, 210, edge=col, alpha=a)
        c.text(150, y + 45, f"{altitude} km above Earth",
               size=34, color=col, ha="left", alpha=a)
        c.text(865, y - 25, f"{value} km/s",
               size=40, ha="right", color=FG, alpha=a)
        progress = c.ramp(c.cue(step) + 0.2, c.cue(step) + 1.7)
        c.line(
            [155, 155 + 470 * speed / LOW_SPEED * progress],
            [y - 70, y - 70], col, lw=12, alpha=a,
        )

    a = c.appear(2, 0.1, 0.7)
    earth(c, 250, 820, 90)
    satellite(c, 820, 820, PINK, alpha=a)
    # Draw the entire center-to-satellite arrow above the Earth graphic.
    c.arrow(250, 820, 785, 820, YELLOW, lw=4, alpha=a, z=20)
    c.dot(250, 820, 8, FG, a, z=21)
    c.text(535, 910, r"$r$", size=46, color=YELLOW, alpha=a)
    c.text(250, 670, "Center", size=30, color=FG, alpha=a)
    c.text(620, 670, "Not altitude", size=30, color=MUTED, alpha=a)


# ---------------------------------------------------------------- 4 · takeaway
def outro(c):
    c.heading(510, 1650, "WEAKER GRAVITY.\nLESS SPEED.", size=60)
    orbital_pair(c, c.cue(0))

    a = c.appear(1, 0.1, 0.5)
    c.panel(510, 640, 680, 115, fill=PINK, radius=55, alpha=a)
    c.text(510, 640, "Follow for more physics", size=38,
           color=FG, weight="bold", alpha=a)


SCENES = [
    Scene(hook, header=None, steps=[
        Step(
            "Why do higher satellites move slower?",
            pause=0.4,
            sfx=[("whoosh", 0.1)],
        ),
        Step(
            "For circular orbits, weaker gravity demands less speed, not more.",
            pause=0.5,
        ),
        Step(
            "Let's compare satellites orbiting Earth, ignoring air resistance and other bodies.",
            pause=0.3,
        ),
    ]),
    Scene(balance, header="Gravity sets the speed", steps=[
        Step(
            "Gravity supplies the inward acceleration needed to keep a satellite turning.",
            pause=0.4,
            sfx=[("note", 0.2, {"n": 2})],
        ),
        Step(
            "Set gravity equal to speed squared divided by distance from Earth's center.",
            sub="GM/r² = v²/r, where r is measured from Earth’s center.",
            pause=0.6,
        ),
        Step(
            "That gives orbital speed: the square root of G M divided by r.",
            sub="Circular orbital speed: v = √(GM/r).",
            pause=0.8,
            sfx=[("chime", 0.3, {"n": 4})],
        ),
    ]),
    Scene(comparison, header="Test with Earth", steps=[
        Step(
            "At {low_h} kilometers above Earth, circular orbital speed is about {low_v} kilometers per second.",
            sub="{low_h} km altitude → circular speed ≈ {low_v} km/s.",
            pause=0.6,
            sfx=[("pop", 0.2, {"n": 5})],
        ),
        Step(
            "At {high_h} kilometers up, it drops to about {high_v} kilometers per second.",
            sub="{high_h} km altitude → circular speed ≈ {high_v} km/s.",
            pause=0.6,
            sfx=[("pop", 0.2, {"n": 2})],
        ),
        Step(
            "Remember, r measures from Earth's center, not its surface.",
            sub="r is distance from Earth’s center, not altitude.",
            pause=0.5,
        ),
    ]),
    Scene(outro, header=None, steps=[
        Step(
            "Higher circular orbits need less speed because gravity weakens with distance.",
            pause=0.5,
        ),
        Step(
            "Follow for more physics like this.",
            pause=0.6,
            sfx=[("chime", 0.1, {"n": 4})],
        ),
    ]),
]
