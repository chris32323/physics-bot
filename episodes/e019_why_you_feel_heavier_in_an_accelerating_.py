from engine.style import *

TOPIC = "Elevator Weight"
TITLE = "Why elevators make you feel heavier #physics #shorts"
DESCRIPTION = (
    "Your mass stays the same, but an accelerating elevator changes the floor's push. "
    "See what a scale actually measures."
)
TAGS = ["physics", "apparent weight", "elevator", "Newton's laws", "forces"]

# ---------------------------------------------------------------- physics
MASS = 50.0
GRAVITY = 9.8
ACCEL = 2.0
WEIGHT = MASS * GRAVITY
NORMAL_UP = MASS * (GRAVITY + ACCEL)
NORMAL_DOWN = MASS * (GRAVITY - ACCEL)


def spoken_integer(value):
    n = int(round(value))
    small = [
        "zero", "one", "two", "three", "four", "five", "six",
        "seven", "eight", "nine", "ten", "eleven", "twelve",
        "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen",
    ]
    tens = [
        "", "", "twenty", "thirty", "forty",
        "fifty", "sixty", "seventy", "eighty", "ninety",
    ]
    if n < 20:
        return small[n]
    if n < 100:
        return tens[n // 10] + (" " + small[n % 10] if n % 10 else "")
    return (
        small[n // 100] + " hundred"
        + (" " + spoken_integer(n % 100) if n % 100 else "")
    )


FACTS = {
    "mass": f"{MASS:.0f}",
    "g": f"{GRAVITY:.1f}",
    "accel": f"{ACCEL:.0f}",
    "weight": f"{WEIGHT:.0f}",
    "up": f"{NORMAL_UP:.0f}",
    "down": f"{NORMAL_DOWN:.0f}",
    "mass_words": spoken_integer(MASS),
    "accel_words": spoken_integer(ACCEL),
    "weight_words": spoken_integer(WEIGHT),
    "up_words": spoken_integer(NORMAL_UP),
    "down_words": spoken_integer(NORMAL_DOWN),
}


# ---------------------------------------------------------------- shared drawings
def rider(c, x, floor, alpha=1):
    c.line([x, x], [floor + 75, floor + 250],
           color=PINK, lw=15, alpha=alpha)
    c.line([x - 65, x, x + 65],
           [floor, floor + 95, floor],
           color=PINK, lw=14, alpha=alpha)
    c.line([x - 65, x, x + 65],
           [floor + 160, floor + 220, floor + 160],
           color=PINK, lw=12, alpha=alpha)
    c.ball(x, floor + 305, r=43, color=PINK, alpha=alpha)


def force_diagram(c, normal, show_normal=1, show_gravity=1):
    floor = 930
    c.ground(floor, 160, 920)
    c.panel(520, floor + 12, 240, 34, edge=MUTED, radius=10)
    rider(c, 520, floor + 30)

    # Common pixels-per-newton scale: arrow lengths can be compared directly.
    scale = 0.54
    origin = 1130
    c.arrow(290, origin, 290, origin + normal * scale,
            ORANGE, lw=9, alpha=show_normal)
    c.text(290, 1550, "Floor push", size=32,
           color=ORANGE, alpha=show_normal)
    c.text(290, 1495, r"$N$", size=42,
           color=ORANGE, alpha=show_normal)

    c.arrow(765, origin, 765, origin - WEIGHT * scale,
            GREEN, lw=9, alpha=show_gravity)
    c.text(765, 790, "Gravity", size=32,
           color=GREEN, alpha=show_gravity)
    c.text(765, 730, r"$mg$", size=42,
           color=GREEN, alpha=show_gravity)


# ---------------------------------------------------------------- 1 · hook
def hook(c):
    c.heading(520, 1640, "Why feel heavier?", size=62)

    # The cabin, rider, acceleration arrow and bright scale are present
    # in the first frame, before any animation begins.
    shift = 45 * c.appear(0, 0.1, 1.6)
    floor = 860 + shift
    c.panel(520, 1135 + shift, 700, 630, edge=MUTED, lw=5)
    c.line([185, 855], [floor - 35, floor - 35], color=MUTED, lw=6)
    c.panel(490, floor, 300, 70, edge=YELLOW, radius=15)
    rider(c, 490, floor + 40)

    c.arrow(800, 1030 + shift, 800, 1310 + shift, YELLOW, lw=9)
    c.text(800, 1370 + shift, r"$a$", size=44, color=YELLOW)

    c.panel(520, 675, 570, 130, edge=YELLOW, glow=True)
    c.text(520, 675, FACTS["up"] + " N", size=60, color=YELLOW,
           weight="bold")

    a = c.appear(1, 0.15)
    c.text(520, 1545, "Same mass. Stronger push.", size=34,
           color=PINK, alpha=a)


# ---------------------------------------------------------------- 2 · what the scale measures
def scale_reading(c):
    n = c.appear(0, 0.1, 0.8)
    g = c.appear(1, 0.1, 0.8)
    force_diagram(c, WEIGHT, n, g)
    c.panel(520, 630, 700, 100, edge=ORANGE, alpha=n)
    c.text(520, 630, "Scale reading = floor push", size=36,
           color=ORANGE, alpha=n)


# ---------------------------------------------------------------- 3 · the imbalance
def acceleration(c):
    grow = c.appear(0, 0.1, 1.0)
    normal = lerp(WEIGHT, NORMAL_UP, grow)
    force_diagram(c, normal)

    a = c.appear(0, 0.4, 0.6)
    c.arrow(520, 1350, 520, 1500, YELLOW, lw=7, alpha=a)
    c.text(520, 1625, "Accelerating up", size=30,
           color=YELLOW, alpha=a)

    b = c.appear(1, 0.1, 0.7)
    c.panel(520, 630, 700, 110, edge=YELLOW, alpha=b)
    c.text(520, 630, r"$N - mg = ma$", size=54,
           color=YELLOW, alpha=b)


# ---------------------------------------------------------------- 4 · real numbers
def comparison(c):
    c.text(520, 1560,
           "Rider: " + FACTS["mass"] + " kg    |    g = " + FACTS["g"] + " m/s²",
           size=34, color=MUTED)

    rows = [
        (0, 1340, "No acceleration", FACTS["weight"], FG, 0),
        (1, 1080, "Accelerating up", FACTS["up"], ORANGE, 1),
        (2, 820, "Accelerating down", FACTS["down"], BLUE, -1),
    ]
    for step, y, label, value, color, direction in rows:
        a = c.appear(step, 0.1, 0.65)
        c.panel(520, y, 790, 210, edge=color, alpha=a)
        c.text(200, y + 52, label, size=34, color=color,
               ha="left", alpha=a)
        c.text(200, y - 35, value + " N", size=56, color=color,
               ha="left", weight="bold", alpha=a)

        if direction:
            c.arrow(825, y - 48 * direction,
                    825, y + 48 * direction,
                    color, lw=7, alpha=a)
            c.text(660, y - 35,
                   FACTS["accel"] + " m/s²",
                   size=30, color=color, alpha=a)
        else:
            c.text(730, y - 35, r"$N = mg$", size=36,
                   color=color, alpha=a)

    c.text(520, 615, "Gravity stays the same in every case.", size=30,
           color=GREEN, alpha=c.appear(0, 0.6))


# ---------------------------------------------------------------- 5 · takeaway
def outro(c):
    c.heading(520, 1640, "Acceleration matters.", size=57)
    c.text(520, 1540, "Not which way you're traveling.", size=36,
           color=MUTED)

    # Constant-speed motion: linear travel, not an eased acceleration.
    start = c.cue(0)
    end = max(c.stop(0), start + 0.1)
    travel = 80 * c.lin(start, end)
    floor = 960 + travel
    c.panel(470, 1130 + travel, 570, 510, edge=MUTED)
    rider(c, 470, floor)
    c.panel(470, floor - 30, 260, 66, edge=YELLOW, radius=12)
    c.text(470, floor - 30, FACTS["weight"] + " N",
           size=38, color=YELLOW, weight="bold")

    c.arrow(830, 1110, 830, 1340, BLUE, lw=7)
    c.text(830, 1400, "Velocity", size=30, color=BLUE)
    c.text(520, 800, "Constant speed → normal reading", size=34,
           color=YELLOW, alpha=c.appear(0, 0.3))

    a = c.appear(1, 0.1, 0.6)
    c.panel(520, 650, 630, 120, fill=PINK, alpha=a, radius=55)
    c.text(520, 650, "Follow for more physics", size=36,
           color=FG, weight="bold", alpha=a)


# ---------------------------------------------------------------- narration
SCENES = [
    Scene(hook, header=None, steps=[
        Step(
            "Why do you feel heavier when an elevator accelerates upward?",
            pause=0.3,
            sfx=[("whoosh", 0.1)],
        ),
        Step(
            "During upward acceleration, your mass stays unchanged, but the floor pushes harder against your feet.",
            pause=0.4,
        ),
    ]),
    Scene(scale_reading, header="What scales measure", steps=[
        Step(
            "A scale measures that upward push, called the normal force, not gravity directly.",
            pause=0.5,
            sfx=[("note", 0.2, {"n": 2})],
        ),
        Step(
            "Gravity pulls down; the floor pushes up.",
            pause=0.6,
        ),
    ]),
    Scene(acceleration, header="An unbalanced push", steps=[
        Step(
            "To accelerate upward, the upward push must exceed your weight.",
            pause=0.7,
            sfx=[("whoosh", 0.1)],
        ),
        Step(
            "Newton's law says normal force minus weight equals mass times acceleration.",
            sub="Newton's law: N − mg = ma.",
            pause=0.6,
            sfx=[("note", 0.3, {"n": 4})],
        ),
    ]),
    Scene(comparison, header="Test the numbers", steps=[
        Step(
            "For a {mass_words} kilogram rider, gravity pulls down with {weight_words} newtons.",
            sub="For a {mass} kg rider, gravity pulls down with {weight} N.",
            pause=0.4,
        ),
        Step(
            "Accelerating upward at {accel_words} meters per second squared raises the scale reading to {up_words} newtons.",
            sub="Accelerating upward at {accel} m/s² raises the scale reading to {up} N.",
            pause=0.7,
            sfx=[("pop", 0.2, {"n": 6})],
        ),
        Step(
            "Downward acceleration instead lowers it to {down_words} newtons.",
            sub="Downward acceleration instead lowers it to {down} N.",
            pause=0.7,
            sfx=[("pop", 0.2, {"n": 2})],
        ),
    ]),
    Scene(outro, header=None, steps=[
        Step(
            "It's acceleration, not travel direction: constant speed feels normal, even going up.",
            pause=0.6,
        ),
        Step(
            "Follow for more physics like this.",
            pause=0.8,
            sfx=[("chime", 0.1, {"n": 4})],
        ),
    ]),
]
