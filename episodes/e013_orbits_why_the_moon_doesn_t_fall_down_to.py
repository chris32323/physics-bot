from engine.style import *

TOPIC = "Why the Moon Stays Up"
TITLE = "The Moon is falling—and keeps missing Earth #physics #shorts"
DESCRIPTION = (
    "The Moon stays in orbit because gravity bends its sideways motion into a curved path. "
    "A circular-orbit model shows how far it travels and falls in one minute."
)
TAGS = ["physics", "orbits", "Moon", "gravity", "space", "science"]
TEASER = "Why do ice skaters spin faster when they pull their arms in?"

# ---------------------------------------------------------------- physics
MU = 3.986004418e14
R = 384400e3
SPEED = math.sqrt(MU / R)
INTERVAL = 60.0
DISTANCE = SPEED * INTERVAL
ANGLE = DISTANCE / R
SAG = R * (1 - math.cos(ANGLE))

ONES = [
    "zero", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine",
]
TEENS = [
    "ten", "eleven", "twelve", "thirteen", "fourteen",
    "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
]
TENS = [
    "", "", "twenty", "thirty", "forty",
    "fifty", "sixty", "seventy", "eighty", "ninety",
]


def spoken_number(s):
    whole, dot, fraction = s.partition(".")
    n = int(whole)
    if n < 10:
        out = ONES[n]
    elif n < 20:
        out = TEENS[n - 10]
    else:
        out = TENS[n // 10]
        if n % 10:
            out += " " + ONES[n % 10]
    if dot:
        out += " point " + " ".join(ONES[int(d)] for d in fraction)
    return out


FACTS = {
    "speed": f"{SPEED / 1000:.2f}",
    "seconds": f"{INTERVAL:.0f}",
    "distance": f"{DISTANCE / 1000:.0f}",
    "sag": f"{SAG:.1f}",
}
for key in ("speed", "seconds", "distance", "sag"):
    FACTS[key + "_say"] = spoken_number(FACTS[key])


# ---------------------------------------------------------------- shared drawings
def earth(c, x, y, r, alpha=1):
    c.ring(x, y, r + 8, BLUE, lw=3, alpha=0.3 * alpha)
    c.ball(x, y, r=r, color=BLUE, alpha=alpha)
    c.polygon([
        (x - 0.65 * r, y + 0.35 * r),
        (x - 0.15 * r, y + 0.65 * r),
        (x + 0.05 * r, y + 0.2 * r),
        (x - 0.25 * r, y - 0.1 * r),
        (x - 0.5 * r, y - 0.55 * r),
    ], GREEN, 0.7 * alpha)
    c.polygon([
        (x + 0.2 * r, y - 0.1 * r),
        (x + 0.65 * r, y - 0.25 * r),
        (x + 0.35 * r, y - 0.65 * r),
    ], GREEN, 0.65 * alpha)


def orbit_path(c, x, y, radius, alpha=1):
    angles = np.linspace(0, 2 * math.pi, 110)
    c.line(
        x + radius * np.cos(angles),
        y + radius * np.sin(angles),
        MUTED, lw=3, alpha=0.55 * alpha, dash=(4, 5),
    )


def moon_xy(x, y, radius, theta):
    return x + radius * math.cos(theta), y + radius * math.sin(theta)


def local_path(p):
    # Independent horizontal and vertical magnification.
    # This is an orbital arc, NOT the surface of Earth.
    theta = 0.3 * p
    return (
        150 + 710 * math.sin(theta) / math.sin(0.3),
        1410 - 330 * (1 - math.cos(theta)) / (1 - math.cos(0.3)),
    )


# ---------------------------------------------------------------- 1: cover / hook
def hook(c):
    c.heading(510, 1640, "The Moon\nis falling.", size=64)
    x, y, radius = 490, 1110, 330
    orbit_path(c, x, y, radius)
    earth(c, x, y, 105)

    theta = 0.45 + max(0, c.t - c.cue(0)) * 0.17
    mx, my = moon_xy(x, y, radius, theta)
    c.ball(mx, my, r=30, color=PINK)

    a = c.appear(1, 0.15)
    c.arrow(
        mx - 42 * math.cos(theta), my - 42 * math.sin(theta),
        mx - 150 * math.cos(theta), my - 150 * math.sin(theta),
        GREEN, alpha=a,
    )
    b = c.appear(2, 0.15)
    c.arrow(
        mx, my,
        mx - 125 * math.sin(theta), my + 125 * math.cos(theta),
        BLUE, alpha=b,
    )
    c.text(510, 680, "FALLING + MOVING SIDEWAYS", size=32,
           color=YELLOW, alpha=b)
    c.text(510, 600, "Diagram not to scale", size=24, color=MUTED)


# ---------------------------------------------------------------- 2: gravity changes direction
def turning(c):
    x, y, radius = 490, 1120, 300
    orbit_path(c, x, y, radius)
    earth(c, x, y, 100)

    theta = 0.3 + max(0, c.t - c.cue(0)) * 0.12
    mx, my = moon_xy(x, y, radius, theta)

    a = c.appear(0, 0.1)
    c.arrow(
        mx - 40 * math.cos(theta), my - 40 * math.sin(theta),
        mx - 165 * math.cos(theta), my - 165 * math.sin(theta),
        GREEN, alpha=a,
    )
    c.text(500, 1550, "Gravity pulls inward", size=38,
           color=GREEN, alpha=a)

    b = c.appear(1, 0.1)
    c.arrow(
        mx, my,
        mx - 145 * math.sin(theta), my + 145 * math.cos(theta),
        BLUE, alpha=b,
    )
    c.text(500, 735, "Velocity points along the path", size=32,
           color=BLUE, alpha=b)

    d = c.appear(2, 0.1)
    c.ring(x, y, radius, YELLOW, lw=3, alpha=0.45 * d)
    c.text(500, 650, "Constant speed • changing direction", size=30,
           color=YELLOW, alpha=d)
    c.ball(mx, my, r=27, color=PINK)
    c.text(500, 590, "Circular model • not to scale", size=23,
           color=MUTED, alpha=c.appear(3))


# ---------------------------------------------------------------- 3: tangent versus orbit
def missing(c):
    c.text(500, 1560, "Straight ahead, without gravity", size=33,
           color=BLUE)
    c.line([150, 900], [1410, 1410], BLUE, lw=3, alpha=0.7,
           dash=(5, 5))
    c.dot(150, 1410, 10, PINK, 1)

    a = c.appear(1, 0.1, 0.7)
    ps = np.linspace(0, 1, 90)
    pts = [local_path(p) for p in ps]
    c.line([p[0] for p in pts], [p[1] for p in pts],
           PINK, lw=5, alpha=a)

    launch = c.cue(1) + 0.3
    p = clamp((c.t - launch) / 3.4)
    mx, my = local_path(p)
    c.ball(mx, my, r=25, color=PINK)

    b = c.appear(2, 0.15)
    c.arrow(150, 1300, 150, 1080, GREEN, alpha=b)
    c.text(260, 980, "Toward Earth's\ncenter", size=28,
           color=GREEN, alpha=b)
    c.text(750, 1000, "Curved orbit", size=32, color=PINK, alpha=a)

    d = c.appear(3, 0.1)
    c.panel(510, 780, 830, 130, edge=YELLOW, alpha=d)
    c.text(510, 780, "Fall inward. Keep missing.", size=40,
           color=YELLOW, alpha=d)
    c.text(510, 620, "Local view • curvature exaggerated", size=25,
           color=MUTED)


# ---------------------------------------------------------------- 4: calculated numerical example
def numbers(c):
    c.text(500, 1550, "At the Moon's average distance", size=34,
           color=MUTED)

    rows = [
        (0, 1410, "Circular speed", FACTS["speed"] + " km/s", BLUE),
        (1, 1260, "Elapsed time", FACTS["seconds"] + " s", FG),
        (2, 1110, "Along the orbit", FACTS["distance"] + " km", BLUE),
        (3, 960, "Below the tangent", FACTS["sag"] + " m", GREEN),
    ]
    for step, y, label, value, col in rows:
        a = c.appear(step, 0.1, 0.6)
        c.panel(510, y, 830, 115, edge=col, alpha=a)
        c.text(140, y, label, size=29, ha="left", alpha=a)
        c.text(885, y, value, size=37, color=col, ha="right",
               weight="bold", alpha=a)

    a = c.appear(4, 0.1)
    c.text(500, 790, "The path bends by exactly", size=33, alpha=a)
    c.text(500, 720, "the amount gravity supplies.", size=33,
           color=YELLOW, alpha=a)
    c.text(500, 610, "Circular model • rounded values", size=24,
           color=MUTED)


# ---------------------------------------------------------------- 5: remove gravity / real orbit
def reality(c):
    x, y, radius = 460, 1110, 275
    orbit_path(c, x, y, radius)
    earth(c, x, y, 88)

    hypothetical = c.cue(1) <= c.t < c.cue(2)

    if hypothetical:
        # This tangent flight exists only during the no-gravity thought experiment.
        theta = 0.55
        mx, my = moon_xy(x, y, radius, theta)
        tx, ty = -math.sin(theta), math.cos(theta)
        p = clamp((c.t - c.cue(1) - 0.2) / 3.0)
        travel = 240 * p
        a = c.appear(1, 0.1)
        c.line([mx, mx + tx * 240], [my, my + ty * 240],
               BLUE, lw=4, alpha=a, dash=(4, 4))
        c.ball(mx + tx * travel, my + ty * travel, r=27, color=PINK)

        c.text(500, 1550, "Hypothetical: no gravity", size=40,
               color=BLUE, alpha=c.appear(1))
        c.text(500, 740, "No gravity → straight-line motion", size=31,
               color=BLUE, alpha=a)
    else:
        # Restore the orbiting Moon as soon as narration returns to the real orbit.
        theta = 0.55 + max(0, c.t - c.cue(2)) * 0.12
        mx, my = moon_xy(x, y, radius, theta)
        c.ball(mx, my, r=27, color=PINK)

        c.text(500, 1550, "Gravity is still acting", size=40,
               color=GREEN, alpha=c.appear(0))

    c.text(500, 650, "Real orbit: slightly elliptical", size=30,
           color=MUTED, alpha=c.appear(2))
    c.ring(x, y, radius, GREEN, lw=4,
           alpha=0.5 * c.pulse(c.cue(3) + 0.2, 1.8))


# ---------------------------------------------------------------- 6: takeaway and tomorrow
def outro(c):
    a = c.appear(0, 0.1)
    c.heading(510, 1610, "Orbiting is\ncontinuous falling.", size=58,
              alpha=a)
    c.text(510, 1430, "Sideways motion keeps it missing.", size=32,
           color=YELLOW, alpha=a)

    b = c.appear(1, 0.1)
    c.text(510, 1220, "Tomorrow:", size=34, color=BLUE,
           weight="bold", alpha=b)
    c.heading(510, 1050, wrap(TEASER, 27), size=46, alpha=b)

    d = c.appear(2, 0.1)
    c.panel(510, 720, 780, 120, fill=PINK, alpha=d)
    c.text(510, 720, "Follow for daily physics", size=34,
           color=FG, weight="bold", alpha=d)


SCENES = [
    Scene(hook, header=None, steps=[
        Step("Why doesn't the Moon crash into Earth?",
             sfx=[("note", 0.1, {"n": 2})]),
        Step("It is falling toward Earth right now.",
             pause=0.5),
        Step("But its sideways motion keeps turning that fall into an orbit.",
             pause=0.8, sfx=[("whoosh", 0.2)]),
    ]),
    Scene(turning, header="A sideways fall", steps=[
        Step("Gravity pulls the Moon inward, toward Earth's center."),
        Step("Meanwhile, the Moon already has a large sideways velocity.",
             pause=0.5, sfx=[("whoosh", 0.15)]),
        Step("Gravity continually changes its direction, rather than stopping its motion.",
             pause=0.8),
        Step("For now, imagine a circular orbit with only Earth's gravity acting.",
             pause=0.4),
    ]),
    Scene(missing, header="Watch it miss", steps=[
        Step("Without gravity, the Moon would continue straight along this tangent."),
        Step("With gravity, its path bends inward instead.",
             pause=1.2, sfx=[("whoosh", 0.3)]),
        Step("Its sideways motion carries it around Earth as it falls.",
             pause=0.6),
        Step("At the right speed, that curve keeps its distance from Earth's center.",
             pause=0.8, sfx=[("chime", 0.2, {"n": 3})]),
    ]),
    Scene(numbers, header="Check the numbers", steps=[
        Step("That circular speed is about {speed_say} kilometers per second.",
             sub="That circular speed is about {speed} km/s."),
        Step("Let's follow the Moon for just {seconds_say} seconds.",
             sub="Let's follow the Moon for just {seconds} seconds.",
             pause=0.4),
        Step("It travels about {distance_say} kilometers along its orbit.",
             sub="It travels about {distance} km along its orbit.",
             pause=0.6),
        Step("It ends up about {sag_say} meters below the original straight tangent.",
             sub="It ends up about {sag} m below the original straight tangent.",
             pause=1.0),
        Step("That inward deflection is exactly what the circular path requires.",
             pause=0.8, sfx=[("chime", 0.2, {"n": 4})]),
    ]),
    Scene(reality, header="Not beyond gravity", steps=[
        Step("So the Moon isn't floating beyond gravity's reach."),
        Step("Remove gravity, and it flies straight instead of circling.",
             pause=1.2, sfx=[("whoosh", 0.2)]),
        Step("The real orbit is slightly elliptical, and the Sun also affects it."),
        Step("But the central idea survives all those complications.",
             pause=0.4),
    ]),
    Scene(outro, header=None, steps=[
        Step("An orbit is continuous falling, with enough sideways motion to keep missing.",
             pause=0.7),
        Step("Tomorrow: " + TEASER, pause=0.5),
        Step("Follow, so you don't miss it.",
             pause=0.8, sfx=[("chime", 0.1, {"n": 2})]),
    ]),
]
