from engine.style import *

TOPIC = "Why the Moon Stays Up"
TITLE = "The Moon is falling—and keeps missing Earth #physics #shorts"
DESCRIPTION = (
    "The Moon stays in orbit because gravity bends its sideways motion around Earth. "
    "Calculate a circular-orbit estimate, then see where the real Moon differs."
)
TAGS = ["physics", "orbits", "Moon", "gravity", "space", "science"]
TEASER = "Why do ice skaters spin faster when they pull their arms in?"

# ---------------------------------------------------------------- physics
G = 6.67430e-11
EARTH_MASS = 5.9722e24
MOON_DISTANCE = 384400e3
MU = G * EARTH_MASS
CIRCULAR_SPEED = math.sqrt(MU / MOON_DISTANCE)
CIRCULAR_PERIOD = 2 * math.pi * MOON_DISTANCE / CIRCULAR_SPEED
DAY = 24 * 60 * 60


def spoken_integer(n):
    small = [
        "zero", "one", "two", "three", "four", "five", "six", "seven",
        "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
        "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
    ]
    tens = ["", "", "twenty", "thirty", "forty", "fifty",
            "sixty", "seventy", "eighty", "ninety"]
    n = int(n)
    if n < 20:
        return small[n]
    if n < 100:
        return tens[n // 10] + (" " + small[n % 10] if n % 10 else "")
    return small[n // 100] + " hundred" + (
        " " + spoken_integer(n % 100) if n % 100 else ""
    )


DISTANCE_THOUSANDS = round(MOON_DISTANCE / 1e6)
SPEED_ROUNDED = round(CIRCULAR_SPEED / 1000)
DAYS_ROUNDED = round(CIRCULAR_PERIOD / DAY)

FACTS = {
    "distance_say": spoken_integer(DISTANCE_THOUSANDS) + " thousand",
    "distance": f"{DISTANCE_THOUSANDS * 1000:,}",
    "speed_say": spoken_integer(SPEED_ROUNDED),
    "speed": f"{CIRCULAR_SPEED / 1000:.2f}",
    "days_say": spoken_integer(DAYS_ROUNDED),
    "days": f"{CIRCULAR_PERIOD / DAY:.1f}",
}


# ---------------------------------------------------------------- shared drawing
def earth(c, x, y, r=92, alpha=1):
    c.ring(x, y, r + 10, BLUE, lw=3, alpha=0.3 * alpha)
    c.ball(x, y, r=r, color=BLUE, alpha=alpha)
    c.arc(x - r * 0.12, y, r * 0.63, -65, 80,
          GREEN, lw=12, alpha=0.8 * alpha)
    c.arc(x + r * 0.18, y + r * 0.08, r * 0.39, 100, 245,
          GREEN, lw=9, alpha=0.7 * alpha)


def orbit_point(cx, cy, radius, angle):
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def orbit_path(c, cx, cy, radius, start, sweep, color=PINK,
               alpha=1, lw=5):
    angles = np.linspace(start, start + sweep, 100)
    c.line(cx + radius * np.cos(angles),
           cy + radius * np.sin(angles),
           color=color, lw=lw, alpha=alpha)


# ---------------------------------------------------------------- 1 · hook
def hook(c):
    cx, cy, radius = 500, 1110, 310
    c.heading(500, 1660, "FALLING…", size=64)
    c.heading(500, 1555, "but always missing", size=54, color=YELLOW)
    c.ring(cx, cy, radius, MUTED, lw=3, alpha=0.5)
    earth(c, cx, cy, 100)

    # The orbit and Moon are present in the very first frame.
    start = math.radians(35)
    elapsed = max(0, c.t - c.cue(0))
    angle = start + elapsed * 0.34
    orbit_path(c, cx, cy, radius, angle - 1.25, 1.25,
               alpha=0.85, lw=6)
    x, y = orbit_point(cx, cy, radius, angle)
    c.ball(x, y, r=29, color=PINK)

    a = c.appear(1, 0.1)
    dx, dy = cx - x, cy - y
    c.arrow(x, y, x + dx * 0.42, y + dy * 0.42,
            GREEN, alpha=a)
    c.text(500, 675, "Gravity never switches off",
           size=36, color=GREEN, alpha=a)


# ---------------------------------------------------------------- 2 · motion
def motion(c):
    cx, cy, radius = 430, 1090, 290
    c.ring(cx, cy, radius, MUTED, lw=3, alpha=0.45)
    earth(c, cx, cy, 88)

    sx, sy = cx + radius, cy
    tangent = c.appear(0, 0.2, 0.8)
    c.arrow(sx, sy, sx, sy + 350 * tangent, BLUE, lw=7)
    c.text(690, 1510, "sideways velocity", size=32,
           color=BLUE, alpha=tangent)

    # A hypothetical Moon coasts along the tangent when gravity is absent.
    coast = c.lin(c.cue(1) + 0.2, c.cue(1) + 3.4)
    ghost_y = sy + 350 * coast
    a = c.appear(1, 0.1)
    c.line([sx, sx], [sy, sy + 350], BLUE, lw=3,
           alpha=0.4 * a, dash=(5, 5))
    c.ring(sx, ghost_y, 27, BLUE, lw=4, alpha=a)
    c.text(500, 745, "Without gravity: a straight path",
           size=30, color=BLUE, alpha=a)

    g = c.appear(2, 0.2, 0.7)
    c.arrow(sx, sy, sx - 175 * g, sy, GREEN, lw=7)
    c.text(490, 930, "inward pull", size=31, color=GREEN, alpha=g)

    # One physical clock for the curved motion: constant angular speed.
    elapsed = max(0, c.t - c.cue(3) - 0.15)
    angle = min(elapsed * 0.40, 1.6)
    orbit_path(c, cx, cy, radius, 0, angle, alpha=0.95)
    x, y = orbit_point(cx, cy, radius, angle)
    c.ball(x, y, r=27)
    b = c.appear(3, 0.1)
    c.arrow(x, y, x + 115 * math.cos(angle + math.pi / 2),
            y + 115 * math.sin(angle + math.pi / 2),
            BLUE, lw=5, alpha=b)
    c.arrow(x, y, x + (cx - x) * 0.40,
            y + (cy - y) * 0.40, GREEN, lw=5, alpha=b)


# ---------------------------------------------------------------- 3 · circular physics
def physics(c):
    cx, cy, radius = 500, 1240, 235
    c.ring(cx, cy, radius, MUTED, lw=3, alpha=0.45)
    earth(c, cx, cy, 72)

    angle = 0.55 + max(0, c.t - c.cue(0)) * 0.24
    x, y = orbit_point(cx, cy, radius, angle)
    c.ball(x, y, r=24)
    a = c.appear(0, 0.1)
    c.arrow(x, y, x + (cx - x) * 0.52,
            y + (cy - y) * 0.52, GREEN, lw=6, alpha=a)

    b = c.appear(1, 0.1)
    c.arrow(x, y, x - 125 * math.sin(angle),
            y + 125 * math.cos(angle), BLUE, lw=6, alpha=b)
    c.text(500, 1580, "Change direction, not speed",
           size=37, color=BLUE, alpha=b)

    d = c.appear(2, 0.1)
    c.text(500, 910, r"$a_{\rm inward}=\frac{v^2}{r}$",
           size=53, color=GREEN, alpha=d)

    e = c.appear(3, 0.1, 0.7)
    c.panel(500, 725, 760, 200, edge=YELLOW, alpha=e)
    c.text(500, 760, r"$v=\sqrt{\frac{GM}{r}}$",
           size=58, color=YELLOW, alpha=e)
    c.text(500, 655, "M: Earth’s mass     G: gravity constant",
           size=26, color=MUTED, alpha=e)


# ---------------------------------------------------------------- 4 · numerical test
def numbers(c):
    cx, cy, radius = 500, 1280, 235
    c.ring(cx, cy, radius, MUTED, lw=3, alpha=0.6)
    earth(c, cx, cy, 65)
    c.text(500, 1590, "Circular orbit · fixed Earth",
           size=34, color=MUTED)

    # One full turn in a fixed amount of screen time, anchored to the period cue.
    launch = c.cue(3) + 0.25
    elapsed = max(0, c.t - launch)
    angle = min(elapsed / 4.0, 1.0) * 2 * math.pi
    x, y = orbit_point(cx, cy, radius, angle)
    if elapsed > 0:
        orbit_path(c, cx, cy, radius, 0, angle, YELLOW, 0.85, 5)
    c.ball(x, y, r=25)

    a = c.appear(1, 0.1)
    c.line([cx, cx + radius], [cy, cy], MUTED, lw=3,
           alpha=a, dash=(5, 5))
    rows = [
        (1, 980, "Distance from Earth’s center",
         "≈ " + FACTS["distance"] + " km", FG),
        (2, 820, "Required sideways speed",
         FACTS["speed"] + " km/s", BLUE),
        (3, 660, "Time around Earth",
         "≈ " + FACTS["days"] + " days", YELLOW),
    ]
    for cue, yy, label, value, color in rows:
        opacity = c.appear(cue, 0.1, 0.6)
        c.text(500, yy + 43, label, size=27,
               color=MUTED, alpha=opacity)
        c.text(500, yy - 55, value, size=45,
               color=color, weight="bold", alpha=opacity)


# ---------------------------------------------------------------- 5 · reality
def reality(c):
    cx, cy = 500, 1230
    a, b = 315, 270
    phase = 0.4 + max(0, c.t - c.cue(0)) * 0.27

    # Eccentric-anomaly construction with equal mean-anomaly increments:
    # solve Kepler's equation, keeping the orbital animation physically timed.
    eccentricity = math.sqrt(1 - (b / a) ** 2)
    mean_anomaly = phase
    eccentric_anomaly = mean_anomaly
    for _ in range(6):
        eccentric_anomaly -= (
            eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly)
            - mean_anomaly
        ) / (1 - eccentricity * math.cos(eccentric_anomaly))

    angles = np.linspace(0, 2 * math.pi, 120)
    c.line(cx + a * np.cos(angles), cy + b * np.sin(angles),
           PINK, lw=4, alpha=0.65)
    focus_x = cx - a * eccentricity
    earth(c, focus_x, cy, 65)
    # Earth is at the left focus; flip the usual eccentric-anomaly x coordinate.
    mx = cx - a * math.cos(eccentric_anomaly)
    my = cy + b * math.sin(eccentric_anomaly)
    c.ball(mx, my, r=24)
    c.text(500, 1590, "Ellipse exaggerated for clarity",
           size=28, color=MUTED)

    q = c.appear(1, 0.1)
    # Separate, explicitly exaggerated shared-center schematic.
    bx, by = 500, 820
    turn = max(0, c.t - c.cue(1)) * 0.6
    ex, ey = bx - 48 * math.cos(turn), by - 48 * math.sin(turn)
    lx, ly = bx + 220 * math.cos(turn), by + 220 * math.sin(turn)
    c.ring(bx, by, 48, BLUE, lw=2, alpha=0.45 * q)
    c.ring(bx, by, 220, PINK, lw=2, alpha=0.3 * q)
    c.line([ex, lx], [ey, ly], MUTED, lw=2, alpha=0.5 * q)
    earth(c, ex, ey, 30, q)
    c.ball(lx, ly, r=16, alpha=q)
    c.dot(bx, by, 8, YELLOW, q)
    c.text(500, 1110, "Shared center of mass", size=32,
           color=YELLOW, alpha=q)
    c.text(500, 580, "Motion and spacing exaggerated",
           size=25, color=MUTED, alpha=q)

    s = c.appear(2, 0.1)
    c.text(500, 1010, "The Sun also perturbs the orbit",
           size=29, color=GREEN, alpha=s)


# ---------------------------------------------------------------- 6 · outro
def outro(c):
    c.heading(500, 1640, "An orbit is", size=55)
    c.heading(500, 1540, "continuous falling", size=59, color=YELLOW)

    cx, cy, radius = 500, 1250, 170
    earth(c, cx, cy, 60)
    c.ring(cx, cy, radius, MUTED, lw=3, alpha=0.45)
    angle = 0.3 + max(0, c.t - c.cue(0)) * 0.45
    x, y = orbit_point(cx, cy, radius, angle)
    orbit_path(c, cx, cy, radius, angle - 0.9, 0.9, PINK, 0.8)
    c.ball(x, y, r=23)
    c.arrow(x, y, x + (cx - x) * 0.45,
            y + (cy - y) * 0.45, GREEN, lw=5)

    a = c.appear(1, 0.1)
    c.text(500, 1020, "Tomorrow:", size=32,
           color=BLUE, weight="bold", alpha=a)
    c.heading(500, 820, wrap(TEASER, 29), size=43, alpha=a)

    b = c.appear(2, 0.1)
    c.panel(500, 620, 710, 92, fill=PINK, radius=40, alpha=b)
    c.text(500, 620, "Follow for daily physics", size=32,
           color=FG, weight="bold", alpha=b)


# ---------------------------------------------------------------- narration
SCENES = [
    Scene(hook, header=None, steps=[
        Step("Why doesn't the Moon crash into Earth?",
             sfx=[("whoosh", 0.1)]),
        Step("It actually is falling toward Earth, every moment of every orbit.",
             pause=0.7),
        Step("But its sideways motion keeps carrying it past the ground.",
             pause=1.0),
    ]),
    Scene(motion, header="Falling sideways", steps=[
        Step("The Moon already has sideways velocity; gravity did not need to launch it."),
        Step("Without gravity, it would keep moving along a straight line.",
             pause=1.0, sfx=[("whoosh", 0.2)]),
        Step("Instead, Earth's gravity pulls inward, continuously bending that path.",
             pause=0.6),
        Step("With the right sideways speed, the curved path goes all the way around Earth.",
             pause=1.4),
    ]),
    Scene(physics, header="What gravity changes", steps=[
        Step("Falling means accelerating toward Earth, not necessarily getting closer to its center.",
             pause=0.5),
        Step("In a circular orbit, gravity changes the velocity's direction without changing its speed.",
             pause=0.7),
        Step("The required inward acceleration is speed squared divided by orbital radius.",
             sub="Required inward acceleration: a = v² / r.",
             pause=0.7, sfx=[("note", 0.2, {"n": 2})]),
        Step("Matching that acceleration to Earth's gravity gives the circular orbital speed.",
             sub="Match gravity to circular acceleration: v = √(GM/r).",
             pause=0.9, sfx=[("chime", 0.3, {"n": 4})]),
    ]),
    Scene(numbers, header="Test the Moon", steps=[
        Step("Let's estimate, treating Earth as fixed and the orbit as circular."),
        Step("The Moon's average distance from Earth's center is about {distance_say} kilometers.",
             sub="Average distance from Earth’s center: ≈ {distance} km.",
             pause=0.6),
        Step("At that distance, the required speed is about {speed_say} kilometer per second.",
             sub="Circular-orbit speed: {speed} km/s.",
             pause=0.7, sfx=[("note", 0.2, {"n": 3})]),
        Step("Divide the orbit's circumference by that speed: roughly {days_say} days for a complete trip.",
             sub="Orbital period: 2πr / v ≈ {days} days.",
             pause=1.5, sfx=[("chime", 0.3, {"n": 4})]),
    ]),
    Scene(reality, header="The real lunar orbit", steps=[
        Step("The real orbit is slightly elliptical, so the Moon's distance and speed both change.",
             pause=0.9),
        Step("Earth also moves: both bodies orbit their shared center of mass.",
             pause=1.0),
        Step("The Sun adds further complications, but continuous gravitational falling remains the central idea.",
             pause=0.6),
    ]),
    Scene(outro, header=None, steps=[
        Step("The Moon stays up by falling inward while moving sideways: it keeps missing Earth.",
             pause=0.7),
        Step("Tomorrow: " + TEASER, pause=0.4),
        Step("Follow, so you don't miss it.",
             pause=0.8, sfx=[("chime", 0.1, {"n": 2})]),
    ]),
]
