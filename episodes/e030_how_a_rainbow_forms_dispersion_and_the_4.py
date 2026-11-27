from engine.style import *

TOPIC = "How Rainbows Form"
TITLE = "Why rainbows appear at 42 degrees #physics #shorts"
DESCRIPTION = (
    "Sunlight bends, reflects, and separates inside raindrops. "
    "Discover why the primary rainbow forms around the direction opposite the Sun."
)
TAGS = ["physics", "rainbow", "dispersion", "optics", "refraction"]

# Water indices representative of red and violet visible light.
N_RED = 1.331
N_VIOLET = 1.343


def rainbow_geometry(n):
    # Stationary primary-rainbow angle:
    # theta = 4r - 2i, with sin(i) = n sin(r).
    i = math.asin(math.sqrt((4.0 - n * n) / 3.0))
    r = math.asin(math.sin(i) / n)
    return i, r, 4.0 * r - 2.0 * i


INCIDENT, REFRACTED, THETA = rainbow_geometry(N_RED)
ANGLE = math.degrees(THETA)


def integer_words(value):
    value = int(round(value))
    tens = ["", "", "twenty", "thirty", "forty", "fifty",
            "sixty", "seventy", "eighty", "ninety"]
    units = ["", "one", "two", "three", "four", "five",
             "six", "seven", "eight", "nine"]
    return tens[value // 10] + (" " + units[value % 10] if value % 10 else "")


FACTS = {
    "angle": f"{ANGLE:.0f}",
    "angle_words": integer_words(ANGLE),
    "index": f"{N_RED:.3f}",
    "violet_angle": f"{math.degrees(rainbow_geometry(N_VIOLET)[2]):.1f}",
}

SPECTRUM = [PINK, ORANGE, YELLOW, GREEN, BLUE, PURPLE]


def draw_rainbow(c, x, y, radius, start, end, alpha=1, width=10):
    for k, color in enumerate(SPECTRUM):
        c.arc(x, y, radius - k * 14, start, end,
              color, width, alpha)


def trace_ray(n, incident=None):
    """Primary ray through a unit circular drop; incident direction is +x."""
    i = INCIDENT if incident is None else incident
    r = math.asin(math.sin(i) / n)
    entry = np.array([-math.cos(i), math.sin(i)])
    inside = np.array([math.cos(i - r), -math.sin(i - r)])
    bounce = entry - 2 * np.dot(entry, inside) * inside
    reflected = inside - 2 * np.dot(inside, bounce) * bounce
    exit_point = bounce - 2 * np.dot(bounce, reflected) * reflected
    tangent = n * (reflected - np.dot(reflected, exit_point) * exit_point)
    outward = tangent + math.sqrt(max(0, 1 - np.dot(tangent, tangent))) * exit_point
    return entry, bounce, exit_point, outward


def segment(c, p, q, progress, color, lw=5, alpha=1):
    tip = p + (q - p) * progress
    c.line([p[0], tip[0]], [p[1], tip[1]],
           color=color, lw=lw, alpha=alpha, glow=True)


# ---------------------------------------------------------------- hook
def hook(c):
    c.heading(520, 1640, "Why this shape?", size=64)
    draw_rainbow(c, 520, 1010, 380, 0, 180, width=13)
    c.ground(990, 100, 950)
    c.ball(520, 1070, r=20, color=FG)
    c.line([520, 520], [1045, 995], color=FG, lw=7)
    c.text(520, 690, "The primary rainbow", size=32, color=YELLOW)

    a = c.appear(1, 0.15, 0.6)
    c.text(520, 770, "Sunlight → droplets → your eyes",
           size=34, alpha=a)

    # Spatially separated drops send representative colors toward the eye.
    for band, degrees in [(0, 35), (2, 90), (5, 145)]:
        theta = math.radians(degrees)
        radius = 380 - band * 14
        drop = np.array([
            520 + radius * math.cos(theta),
            1010 + radius * math.sin(theta),
        ])
        eye = np.array([520.0, 1070.0])
        direction = (eye - drop) / np.linalg.norm(eye - drop)
        start = drop + 25 * direction
        end = eye - 28 * direction
        c.ring(drop[0], drop[1], 25, BLUE, lw=3, alpha=a)
        c.arrow(start[0], start[1], end[0], end[1],
                SPECTRUM[band], lw=3, alpha=a, glow=False, head=0.6)


# ---------------------------------------------------------------- ray tracing
def droplet(c):
    center = np.array([545.0, 1210.0])
    radius = 235.0

    c.dot(center[0], center[1], radius, BLUE, 0.08)
    c.ring(center[0], center[1], radius, BLUE, lw=4, alpha=0.8)

    red = trace_ray(N_RED)
    entry = center + radius * red[0]
    source = np.array([80.0, entry[1]])
    c.arrow(source[0], source[1], entry[0], entry[1],
            FG, lw=6, head=0.7)
    c.text(205, 1505, "SUNLIGHT", size=28, color=FG)

    a0 = c.appear(0, 0.2, 1.0)
    a1 = c.appear(1, 0.15, 1.0)
    a2 = c.appear(2, 0.15, 1.2)

    # Keep outgoing ray endpoints above the explanatory rows.
    for n, color in [(N_RED, PINK), (N_VIOLET, PURPLE)]:
        p, q, r, direction = trace_ray(n)
        p, q, r = [center + radius * point for point in (p, q, r)]
        end = r + 160 * direction
        segment(c, p, q, a0, color, lw=5)
        segment(c, q, r, a1, color, lw=5, alpha=a1)
        segment(c, r, end, a2, color, lw=5, alpha=a2)
        c.ring(q[0], q[1], 17, color, lw=2,
               alpha=0.65 * c.pulse(c.cue(1) + 0.5, 1.2))

    rows = [
        (0, 805, "ENTER: colors bend differently", BLUE),
        (1, 725, "REFLECT: light turns back", GREEN),
        (2, 645, "EXIT: colors separate further", PURPLE),
    ]
    for step, y, label, color in rows:
        c.text(520, y, label, size=32, color=color,
               alpha=c.appear(step, 0.25, 0.5))


# ---------------------------------------------------------------- angle
def angle(c):
    ox, oy = 240, 1010
    length = 710
    dx = ox + length * math.cos(THETA)
    dy = oy + length * math.sin(THETA)

    c.ball(ox, oy, r=23, color=FG)
    c.text(ox, oy - 65, "YOUR EYE", size=27)

    c.arrow(ox + 40, oy, 945, oy, MUTED, lw=3,
            alpha=0.75, glow=False)
    c.text(650, oy - 65, "Opposite the Sun", size=30, color=MUTED)

    # Sun lies behind the observer.
    c.ball(100, oy, r=30, color=YELLOW)
    c.text(105, oy + 75, "SUN", size=26, color=YELLOW)

    a = c.appear(0, 0.15, 0.8)
    c.line([ox, dx], [oy, dy], color=PINK, lw=4, alpha=a)
    c.ring(dx, dy, 25, BLUE, lw=3, alpha=a)
    c.arrow(dx - 65 * math.cos(THETA),
            dy - 65 * math.sin(THETA),
            ox + 150 * math.cos(THETA),
            oy + 150 * math.sin(THETA),
            PINK, lw=6, alpha=a)

    c.arc(ox, oy, 180, 0, math.degrees(THETA),
          YELLOW, lw=4, alpha=a)
    c.text(475, 1100, FACTS["angle"] + "°",
           size=56, color=YELLOW, alpha=a)

    c.text(520, 1555, "Water, red light: n = " + FACTS["index"],
           size=34, color=PINK, alpha=a)

    crowd = c.appear(2, 0.1, 0.9)
    b = c.appear(1, 0.15, 0.6) * (1 - crowd)
    c.text(520, 790, "Angle from the antisolar direction",
           size=31, color=FG, alpha=b)

    # Magnified drop: parallel sunlight enters at distinct heights.
    # After refraction and reflection, outgoing directions bunch near
    # the stationary rainbow angle, rather than incident rays converging.
    center = np.array([580.0, 800.0])
    radius = 115.0
    c.dot(center[0], center[1], radius, BLUE, 0.08 * crowd)
    c.ring(center[0], center[1], radius, BLUE, lw=3, alpha=crowd)

    for offset in [-0.25, 0.0, 0.25]:
        p, q, r, direction = trace_ray(N_RED, INCIDENT + offset)
        p, q, r = [center + radius * point for point in (p, q, r)]
        c.arrow(100, p[1], p[0], p[1],
                FG, lw=2, alpha=0.8 * crowd, glow=False, head=0.55)
        segment(c, p, q, 1, PINK, lw=2, alpha=0.65 * crowd)
        segment(c, q, r, 1, PINK, lw=2, alpha=0.65 * crowd)
        end = r + 100 * direction
        c.arrow(r[0], r[1], end[0], end[1],
                PINK, lw=3, alpha=crowd, glow=False, head=0.6)

    c.text(245, 725, "Parallel sunlight",
           size=27, color=FG, alpha=crowd)
    c.text(520, 590, "Crowded outgoing directions → bright edge",
           size=29, color=YELLOW, alpha=crowd)


# ---------------------------------------------------------------- circular geometry
def circle(c):
    cx, cy, radius = 520, 1080, 350
    horizon = 1180
    c.text(520, 1570, "Looking away from the Sun", size=35)

    a = c.appear(0, 0.1, 1.0)
    draw_rainbow(c, cx, cy, radius, 0, 360, alpha=a, width=10)
    c.dot(cx, cy, 12, YELLOW, a)
    c.line([cx, cx + 245], [cy, cy + 245],
           color=MUTED, lw=2, alpha=a, dash=(4, 5))
    c.text(570, 1280, FACTS["angle"] + "°",
           size=40, color=YELLOW, alpha=a)
    c.text(cx, cy - 65, "Shadow's direction",
           size=30, alpha=a)

    # An opaque foreground rises into place above every rainbow layer.
    # With the Sun above the horizon, the antisolar center is below it:
    # the remaining visible bow is therefore less than a semicircle.
    ground = c.appear(1, 0.2, 1.1)
    if ground > 0:
        bottom = 570
        top = bottom + (horizon - bottom) * ground
        c.panel(520, (bottom + top) / 2, 910, top - bottom,
                fill=PANEL, alpha=1, radius=0, lw=0, z=20)
        c.line([65, 975], [top, top],
               color=MUTED, lw=4, alpha=ground, z=21)

    # This label is below even the unmasked circle, clear of every arc.
    c.text(520, 650, "The ground blocks the lower view",
           size=32, color=MUTED, alpha=ground, z=22)


# ---------------------------------------------------------------- takeaway
def outro(c):
    c.heading(520, 1650, "A circle of color", size=60)
    draw_rainbow(c, 520, 1070, 350, 0, 180, width=13)

    a = c.appear(0, 0.1, 0.6)
    c.text(520, 1500, "Red outside · violet inside",
           size=34, alpha=a)
    c.text(520, 940, "Different colors, different droplets",
           size=33, alpha=c.appear(1, 0.1, 0.6))

    f = c.appear(2, 0.1, 0.5)
    c.panel(520, 720, 680, 125, edge=PINK, alpha=f)
    c.text(520, 720, "Follow for more physics",
           size=38, weight="bold", alpha=f)


SCENES = [
    Scene(hook, header=None, steps=[
        Step("Why does every rainbow curve the same way?"),
        Step("Each raindrop sorts sunlight by color, then sends it back toward you.",
             pause=0.3, sfx=[("pop", 0.2)]),
    ]),
    Scene(droplet, header="Inside a raindrop", steps=[
        Step("Entering water, sunlight bends, and violet bends more than red.",
             pause=0.5, sfx=[("whoosh", 0.2)]),
        Step("The light reflects once inside the drop.",
             pause=0.5, sfx=[("note", 0.3, {"n": 3})]),
        Step("Leaving water, it bends again, separating the colors further.",
             pause=0.6),
    ]),
    Scene(angle, header="Why this angle?", steps=[
        Step("Using water's refractive index, red light peaks at about {angle_words} degrees.",
             sub="Using water's refractive index, red light peaks at about {angle}°.",
             pause=0.5, sfx=[("chime", 0.5, {"n": 4})]),
        Step("That angle is measured from the direction opposite the Sun.",
             pause=0.3),
        Step("Rays entering different parts of a drop emerge near the same angle.",
             pause=0.6),
    ]),
    Scene(circle, header="Why an arc?", steps=[
        Step("With the Sun behind you, matching droplets trace a circle around your shadow's direction.",
             pause=0.7),
        Step("The ground usually hides the bottom, leaving an arc.",
             pause=0.6, sfx=[("note", 0.3, {"n": 2})]),
    ]),
    Scene(outro, header=None, steps=[
        Step("Red forms the outside edge; violet sits inside.",
             pause=0.3),
        Step("Different colors reach your eyes from different droplets.",
             pause=0.3),
        Step("Follow for more physics like this.",
             pause=0.7, sfx=[("chime", 0.1, {"n": 5})]),
    ]),
]
