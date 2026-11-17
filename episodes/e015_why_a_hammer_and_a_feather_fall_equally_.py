from engine.style import *

TOPIC = "Free Fall"
TITLE = "Why a hammer and feather tie on the Moon #physics #shorts"
DESCRIPTION = (
    "Gravity accelerates a hammer and a feather equally in a vacuum. "
    "See why air changes the race on Earth, then test a drop on the Moon."
)
TAGS = ["physics", "free fall", "Moon", "gravity", "air resistance"]
TEASER = "How does a rocket move through empty space?"

# ---------------------------------------------------------------- physics
HEIGHT = 2.0
G_MOON = 1.62
G_EARTH = 9.81
T_MOON = math.sqrt(2 * HEIGHT / G_MOON)
VT_HAMMER = 35.0
VT_FEATHER = 1.2

DIGIT_WORDS = [
    "zero", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine"
]


def spoken_decimal(value, places):
    text = f"{value:.{places}f}"
    return " ".join(
        "point" if char == "." else DIGIT_WORDS[int(char)]
        for char in text
    )


FACTS = {
    "height": f"{HEIGHT:.0f}",
    "time": f"{T_MOON:.1f}",
    "height_voice": spoken_decimal(HEIGHT, 0),
    "time_voice": spoken_decimal(T_MOON, 1),
}


def vacuum_distance(t):
    return min(HEIGHT, 0.5 * G_MOON * t * t)


def air_distance(t, terminal_speed):
    # Exact distance from rest for quadratic drag:
    # acceleration = g * (1 - v² / terminal_speed²).
    return min(
        HEIGHT,
        terminal_speed ** 2 / G_EARTH
        * math.log(math.cosh(G_EARTH * t / terminal_speed))
    )


# ---------------------------------------------------------------- reusable drawings
def hammer(c, x, y, scale=1.0, alpha=1.0):
    c.line(
        [x, x], [y - 65 * scale, y + 26 * scale],
        color=MUTED, lw=15 * scale, alpha=alpha
    )
    c.panel(
        x, y + 30 * scale, 112 * scale, 45 * scale,
        fill=PINK, alpha=alpha, radius=8 * scale, lw=0
    )


def feather(c, x, y, scale=1.0, alpha=1.0):
    c.line(
        [x - 25 * scale, x + 27 * scale],
        [y - 72 * scale, y + 70 * scale],
        color=PINK, lw=5 * scale, alpha=alpha
    )
    for u in np.linspace(0.12, 0.9, 9):
        sx = x + (-25 + 52 * u) * scale
        sy = y + (-72 + 142 * u) * scale
        width = 36 * math.sin(math.pi * u) * scale
        c.line(
            [sx - width, sx, sx + width * 0.85],
            [sy + 21 * scale, sy, sy + 4 * scale],
            color=PINK, lw=4 * scale, alpha=alpha
        )


def lunar_ground(c, y):
    c.ground(y, 85, 950)
    for x, radius in [(180, 28), (505, 42), (850, 24)]:
        c.line(
            [x - radius, x, x + radius],
            [y - 35, y - 43, y - 35],
            color=MUTED, lw=3, alpha=0.45
        )


# ---------------------------------------------------------------- 1 · hook
def hook(c):
    c.heading(520, 1630, "HAMMER = FEATHER?", size=59)
    c.text(340, 1510, "Hammer", size=32, color=PINK)
    c.text(745, 1510, "Feather", size=32, color=PINK)

    ground = 820
    start = 1370
    scale = (start - ground - 72) / HEIGHT
    launch = c.cue(1) + 0.25
    physical_time = max(0.0, c.t - launch) * T_MOON / 2.0
    y = start - vacuum_distance(physical_time) * scale

    c.line(
        [180, 900], [start, start],
        color=MUTED, lw=2, alpha=0.4, dash=(4, 5)
    )
    lunar_ground(c, ground)
    hammer(c, 340, y)
    feather(c, 745, y)

    a = c.appear(1, 0.1)
    c.text(
        520, 680, "On the Moon: no air resistance",
        size=32, color=YELLOW, alpha=a
    )


# ---------------------------------------------------------------- 2 · what air changes
def air(c):
    c.text(520, 1570, "EARTH: FALLING THROUGH AIR", size=32, color=BLUE)
    c.text(330, 1470, "Hammer", size=30, color=PINK)
    c.text(750, 1470, "Feather", size=30, color=PINK)

    ground = 820
    start = 1320
    scale = (start - ground - 72) / HEIGHT

    launch = c.cue(2) + 0.2
    physical_time = max(0.0, c.t - launch)
    yh = start - air_distance(physical_time, VT_HAMMER) * scale
    yf = start - air_distance(physical_time, VT_FEATHER) * scale

    c.ground(ground, 85, 950)

    # A sparse field of air marks establishes the medium.
    a = c.appear(0, 0.1)
    for x in (180, 500, 900):
        for y in (950, 1100, 1250, 1390):
            c.line(
                [x - 15, x + 15], [y, y],
                color=BLUE, lw=3, alpha=0.45 * a
            )

    hammer(c, 330, yh)
    feather(c, 750, yf)

    area = c.appear(1, 0.1)
    c.ring(750, yf, 92, BLUE, lw=3, alpha=0.7 * area)
    c.text(
        520, 700, "Large area, little mass",
        size=35, color=BLUE, alpha=area
    )

    # Compare equal elapsed times, not separately timed animations.
    elapsed = max(0.0, c.t - launch)
    for k in range(1, 6):
        sample_time = k * 0.3
        if elapsed >= sample_time:
            for x, terminal in [(330, VT_HAMMER), (750, VT_FEATHER)]:
                sy = start - air_distance(sample_time, terminal) * scale
                c.dot(x, sy, 6, PINK, 0.25)


# ---------------------------------------------------------------- 3 · why mass cancels
def cancellation(c):
    c.text(310, 1530, "Feather", size=32, color=PINK)
    c.text(745, 1530, "Hammer", size=32, color=PINK)
    feather(c, 310, 1390)
    hammer(c, 745, 1390)

    a = c.appear(0, 0.15, 0.7)
    c.arrow(310, 1280, 310, 1220, GREEN, lw=6, alpha=a)
    c.arrow(745, 1280, 745, 1100, GREEN, lw=8, alpha=a)
    c.text(
        520, 1010, r"$F = mg$",
        size=56, color=GREEN, alpha=a
    )

    b = c.appear(1, 0.15)
    c.text(
        520, 890, "More pull. More inertia.",
        size=39, color=FG, alpha=b
    )

    d = c.appear(2, 0.1, 0.8)
    c.panel(520, 710, 820, 170, edge=YELLOW, alpha=d)
    c.text(
        520, 710, r"$a = \frac{F}{m} = \frac{mg}{m} = g$",
        size=57, color=YELLOW, alpha=d
    )


# ---------------------------------------------------------------- 4 · numerical lunar test
def test_clock(tm):
    launch = tm.voice(0)[1]
    rate = T_MOON / 1.3
    return launch, rate


def test(c):
    c.text(
        520, 1560, "Release height: " + FACTS["height"] + " m",
        size=40, color=YELLOW
    )
    c.text(
        520, 1460, "From rest · constant lunar gravity",
        size=29, color=MUTED
    )

    ground = 800
    start = 1300
    scale = (start - ground - 72) / HEIGHT
    launch, rate = test_clock(c)
    physical_time = max(0.0, c.t - launch) * rate
    y = start - vacuum_distance(physical_time) * scale

    lunar_ground(c, ground)
    c.line(
        [150, 150], [ground + 72, start],
        color=MUTED, lw=3, alpha=0.7
    )
    for yy in (ground + 72, start):
        c.line([135, 165], [yy, yy], color=MUTED, lw=3)

    # Same-height trails, revealed by the same clock.
    for fraction in np.linspace(0.2, 0.9, 5):
        sample_time = fraction * T_MOON
        if physical_time >= sample_time:
            sy = start - vacuum_distance(sample_time) * scale
            c.dot(350, sy, 7, PINK, 0.3)
            c.dot(750, sy, 7, PINK, 0.3)

    hammer(c, 350, y)
    feather(c, 750, y)

    a = c.appear(1, 0.0)
    c.text(
        520, 660, "Both land after " + FACTS["time"] + " s",
        size=42, color=YELLOW, alpha=a
    )
    impact = launch + T_MOON / rate
    bump = c.pulse(impact, 0.8)
    for x in (350, 750):
        c.ring(x, ground + 20, 30 + 35 * bump, YELLOW, lw=3, alpha=bump)


def test_sounds(tm):
    launch, rate = test_clock(tm)
    return [
        ("whoosh", launch, {}),
        ("land", launch + T_MOON / rate, {"n": 3}),
        ("chime", tm.cue(1) + 0.1, {"n": 3}),
    ]


# ---------------------------------------------------------------- 5 · takeaway and tomorrow
def outro(c):
    a = c.appear(0, 0.05)
    c.heading(
        520, 1620, "Same gravity.\nSame acceleration.",
        size=58, alpha=a
    )
    hammer(c, 350, 1370, alpha=a)
    feather(c, 710, 1370, alpha=a)
    c.text(520, 1220, "In a vacuum", size=36, color=YELLOW, alpha=a)

    b = c.appear(1, 0.1)
    c.text(
        520, 1110, "Tomorrow:",
        size=32, color=BLUE, weight="bold", alpha=b
    )
    c.heading(520, 960, wrap(TEASER, 25), size=48, alpha=b)

    d = c.appear(2, 0.0)
    c.panel(520, 680, 720, 120, fill=PINK, alpha=d, radius=55)
    c.text(
        520, 680, "Follow for daily physics",
        size=33, color=FG, weight="bold", alpha=d
    )


# ---------------------------------------------------------------- scenes
SCENES = [
    Scene(hook, header=None, steps=[
        Step(
            "Can a feather tie a hammer?",
            sfx=[("pop", 0.1, {"n": 3})]
        ),
        Step(
            "On the Moon, they fall together when released from rest.",
            pause=0.5
        ),
    ]),
    Scene(air, header="Air changes the race", steps=[
        Step("On Earth, air pushes against objects moving through it."),
        Step(
            "A feather has lots of area for very little mass.",
            pause=0.3,
            sfx=[("note", 0.15, {"n": 2})]
        ),
        Step(
            "So air resistance slows its fall much more than the hammer's.",
            pause=0.8,
            sfx=[("whoosh", 0.2)]
        ),
    ]),
    Scene(cancellation, header="Why mass cancels", steps=[
        Step(
            "Without air, gravity pulls harder on the more massive hammer.",
            pause=0.2
        ),
        Step(
            "But that extra mass also makes it harder to accelerate.",
            pause=0.3
        ),
        Step(
            "Divide gravitational force by mass, and the mass cancels.",
            pause=0.8,
            sfx=[("chime", 0.5, {"n": 4})]
        ),
    ]),
    Scene(test, header="Test it on the Moon", sounds=test_sounds, steps=[
        Step(
            "Assuming constant lunar gravity, drop both from {height_voice} meters.",
            sub="Assuming constant lunar gravity, drop both from {height} meters.",
            pause=1.5
        ),
        Step(
            "They land together after about {time_voice} seconds, with no air resistance.",
            sub="They land together after about {time} seconds, with no air resistance.",
            pause=0.6
        ),
    ]),
    Scene(outro, header=None, steps=[
        Step(
            "In a vacuum, free fall doesn't depend on mass.",
            pause=0.3
        ),
        Step("Tomorrow: " + TEASER, pause=0.3),
        Step(
            "Follow, so you don't miss it.",
            pause=0.5,
            sfx=[("chime", 0.1, {"n": 2})]
        ),
    ]),
]
