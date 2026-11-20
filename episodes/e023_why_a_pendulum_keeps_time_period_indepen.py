from engine.style import *

TOPIC = "Pendulum Timekeeping"
TITLE = "Why different pendulum swings keep the same beat #physics #shorts"
DESCRIPTION = (
    "Why a pendulum's small swings take almost the same time, even at different amplitudes. "
    "See the restoring-force balance and test the period of a one-meter pendulum."
)
TAGS = ["physics", "pendulum", "oscillations", "timekeeping", "science"]

# ---------------------------------------------------------------- physics
EPISODE = 23
LENGTH = 1.0
GRAVITY = 9.81
PERIOD = 2 * math.pi * math.sqrt(LENGTH / GRAVITY)
AMPLITUDES = [math.radians(6), math.radians(12)]
LARGE_AMPLITUDE = math.radians(55)
DIGIT_WORDS = [
    "zero", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine"
]


def spoken_decimal(value, places):
    whole, fraction = f"{value:.{places}f}".split(".")
    return DIGIT_WORDS[int(whole)] + " point " + " ".join(
        DIGIT_WORDS[int(digit)] for digit in fraction
    )


FACTS = {
    "length": f"{LENGTH:.0f}",
    "length_say": DIGIT_WORDS[int(LENGTH)],
    "period": f"{PERIOD:.2f}",
    "period_say": spoken_decimal(PERIOD, 2),
    "gravity": f"{GRAVITY:.2f}",
}


def amplitude_period(amplitude):
    # Leading finite-amplitude corrections for an ideal simple pendulum.
    return PERIOD * (
        1 + amplitude ** 2 / 16 + 11 * amplitude ** 4 / 3072
    )


def bob_position(px, py, radius, angle):
    return px + radius * math.sin(angle), py - radius * math.cos(angle)


def pendulum(c, px, py, radius, angle, color, alpha=1):
    x, y = bob_position(px, py, radius, angle)
    c.line([px, x], [py, y], color=FG, lw=4, alpha=0.8 * alpha)
    c.dot(px, py, 9, MUTED, alpha)
    c.ball(x, y, r=27, color=color, alpha=alpha)
    return x, y


def swing_guide(c, px, py, radius, amplitude, color, alpha=0.4):
    angles = np.linspace(-amplitude, amplitude, 55)
    c.line(
        px + radius * np.sin(angles),
        py - radius * np.cos(angles),
        color=color, lw=4, alpha=alpha
    )
    c.line(
        [px, px], [py, py - radius - 48],
        color=MUTED, lw=2, alpha=0.3, dash=(4, 5)
    )


# ---------------------------------------------------------------- 1 · hook
def hook(c):
    c.heading(520, 1670, "Different swings.\nSame beat?", size=64)
    launch = c.cue(0)
    elapsed = max(0, c.t - launch)

    for index, (px, amplitude, color) in enumerate(
        zip([300, 735], AMPLITUDES, [PINK, PURPLE])
    ):
        swing_guide(c, px, 1410, 650, amplitude, color)
        phase = 2 * math.pi * elapsed / amplitude_period(amplitude)
        pendulum(c, px, 1410, 650, amplitude * math.cos(phase), color)
        c.text(
            px, 655, ["Small swing", "Wider swing"][index],
            size=33, color=color
        )

    a = c.appear(1, 0.1)
    c.text(520, 1510, "Almost equal periods", size=36, color=YELLOW, alpha=a)


# ---------------------------------------------------------------- 2 · restoring pull
def balance(c):
    pivots = [290, 730]
    radius = 590
    py = 1460

    for px, amplitude, color in zip(pivots, AMPLITUDES, [PINK, PURPLE]):
        swing_guide(c, px, py, radius, amplitude, color, alpha=0.65)
        x, y = pendulum(c, px, py, radius, amplitude, color)

        # Tangential component of gravity, pointing toward equilibrium.
        force = c.appear(0, 0.25, 0.7)
        arrow_length = 850 * math.sin(amplitude)
        dx = -math.cos(amplitude) * arrow_length * force
        dy = -math.sin(amplitude) * arrow_length * force
        if force > 0:
            c.arrow(x, y - 45, x + dx, y - 45 + dy, GREEN, lw=7)

    c.text(290, 1570, "Smaller swing", size=34, color=PINK)
    c.text(730, 1570, "Wider swing", size=34, color=PURPLE)

    a = c.appear(0, 0.5)
    c.text(290, 760, "Shorter path", size=31, alpha=a)
    c.text(730, 760, "Longer path", size=31, alpha=a)
    c.text(290, 690, "Weaker component", size=29, color=GREEN, alpha=a)
    c.text(730, 690, "Stronger component", size=29, color=GREEN, alpha=a)

    c.panel(520, 1130, 800, 150, edge=GREEN, alpha=a)
    c.text(
        520, 1165, "Restoring component of gravity",
        size=34, color=GREEN, alpha=a
    )
    b = c.appear(1, 0.15)
    c.text(
        520, 1095, "Restoring pull ∝ displacement",
        size=31, color=GREEN, alpha=b
    )
    d = c.appear(2, 0.1)
    c.text(520, 600, "Small angles: the effects balance", size=33, color=YELLOW, alpha=d)


# ---------------------------------------------------------------- 3 · the formula
def formula(c):
    a = c.appear(0, 0.1)
    px, py, radius = 335, 1510, 530
    angle = math.radians(12)
    x, y = pendulum(c, px, py, radius, angle, PINK)

    # Offset dimension line parallel to the string. Its endpoints project
    # exactly onto the pivot and the bob's center.
    nx, ny = -math.cos(angle), -math.sin(angle)
    offset = 75
    ax, ay = px + offset * nx, py + offset * ny
    bx, by = x + offset * nx, y + offset * ny
    c.line([ax, bx], [ay, by], color=YELLOW, lw=4, alpha=a)
    for ex, ey in [(ax, ay), (bx, by)]:
        c.line(
            [ex - 17 * nx, ex + 17 * nx],
            [ey - 17 * ny, ey + 17 * ny],
            color=YELLOW, lw=4, alpha=a
        )
    c.line(
        [px, ax], [py, ay],
        color=YELLOW, lw=2, alpha=0.45 * a, dash=(3, 4)
    )
    c.line(
        [x, bx], [y, by],
        color=YELLOW, lw=2, alpha=0.45 * a, dash=(3, 4)
    )
    c.text(
        (ax + bx) / 2 + 45 * nx,
        (ay + by) / 2 + 45 * ny,
        r"$L$", size=48, color=YELLOW, alpha=a
    )

    c.arrow(730, 1420, 730, 1260, GREEN, lw=7, alpha=a)
    c.text(730, 1190, r"$g$", size=46, color=GREEN, alpha=a)
    c.text(540, 890, "Length: pivot to bob’s center", size=32, color=MUTED, alpha=a)

    b = c.appear(1, 0.15, 0.65)
    c.panel(520, 735, 750, 180, edge=YELLOW, alpha=b)
    c.text(
        520, 745, r"$T \approx 2\pi\sqrt{\frac{L}{g}}$",
        size=60, color=YELLOW, alpha=b
    )
    c.text(
        520, 595, "Ideal simple pendulum • small angles",
        size=29, color=MUTED, alpha=b
    )


# ---------------------------------------------------------------- 4 · real numbers
def test(c):
    c.text(
        520, 1560,
        f"Length  {FACTS['length']} m     Period  ≈ {FACTS['period']} s",
        size=39, color=YELLOW
    )
    c.text(
        520, 1485, f"g = {FACTS['gravity']} m/s² (Earth)",
        size=32, color=GREEN
    )
    c.text(
        520, 1430, "Full period = there and back",
        size=31, color=MUTED
    )

    launch = c.cue(1) + 0.2
    # Physical time advances at one second per video second.
    elapsed = min(max(c.t - launch, 0), PERIOD)

    for px, amplitude, color in zip([300, 735], AMPLITUDES, [PINK, PURPLE]):
        swing_guide(c, px, 1390, 650, amplitude, color)
        phase = 2 * math.pi * elapsed / amplitude_period(amplitude)
        pendulum(c, px, 1390, 650, amplitude * math.cos(phase), color)

    a = c.appear(1, 0.1)
    c.text(
        520, 665, f"Elapsed  {elapsed:.2f} s",
        size=40, color=FG, alpha=a
    )
    finished = c.ramp(launch + PERIOD, launch + PERIOD + 0.35)
    c.text(
        520, 595, "Almost back together",
        size=32, color=YELLOW, alpha=finished
    )


def test_sounds(tm):
    launch = tm.cue(1) + 0.2
    return [
        ("whoosh", launch, {}),
        ("chime", launch + PERIOD, {"n": 4}),
    ]


# ---------------------------------------------------------------- 5 · takeaway
def outro(c):
    c.heading(520, 1635, "Same beat.\nChanging speed.", size=62)

    # Show a genuinely large swing first, with its longer physical period.
    # At the small-swing cue, change examples with a short crossfade rather
    # than implying that friction instantly removes most of the amplitude.
    elapsed = max(c.t - c.cue(0), 0)
    transition = c.appear(1, 0.0, 0.6)
    large_period = amplitude_period(LARGE_AMPLITUDE)
    large_angle = LARGE_AMPLITUDE * math.cos(
        2 * math.pi * elapsed / large_period
    )

    if transition < 1:
        swing_guide(
            c, 520, 1420, 480, LARGE_AMPLITUDE, PINK,
            alpha=0.4 * (1 - transition)
        )
        pendulum(
            c, 520, 1420, 480, large_angle, PINK,
            alpha=1 - transition
        )

    small_elapsed = max(c.t - c.cue(1), 0)
    amplitude = AMPLITUDES[1] * math.exp(-0.025 * small_elapsed)
    small_angle = amplitude * math.cos(
        2 * math.pi * small_elapsed / amplitude_period(AMPLITUDES[1])
    )
    if transition > 0:
        swing_guide(
            c, 520, 1420, 480, AMPLITUDES[1], PINK,
            alpha=0.4 * transition
        )
        pendulum(
            c, 520, 1420, 480, small_angle, PINK,
            alpha=transition
        )

    a = c.appear(0, 0.1)
    c.text(
        520, 835, "Large swings: longer periods",
        size=32, color=MUTED, alpha=a
    )
    b = c.appear(1, 0.1)
    c.text(
        520, 745, "Small swings: nearly constant period",
        size=34, color=YELLOW, alpha=b
    )

    d = c.appear(2, 0.1)
    c.panel(520, 615, 620, 95, fill=PINK, alpha=d, radius=45)
    c.text(
        520, 615, "Follow for more physics",
        size=36, color=FG, weight="bold", alpha=d
    )


# ---------------------------------------------------------------- narration
SCENES = [
    Scene(hook, header=None, steps=[
        Step(
            "Why do unequal swings keep time?",
            sfx=[("note", 0.1, {"n": 3})]
        ),
        Step(
            "Within small angles, a wider swing takes almost the same time.",
            pause=0.7
        ),
    ]),
    Scene(balance, header="Distance versus pull", steps=[
        Step(
            "A wider swing travels farther, but the component of gravity pulling it back is stronger.",
            pause=0.5,
            sfx=[("whoosh", 0.3)]
        ),
        Step(
            "For small angles, the restoring pull grows almost in proportion to displacement.",
            pause=0.5,
            sfx=[("pop", 0.2, {"n": 2})]
        ),
        Step(
            "That balance makes the rhythm nearly independent of swing size.",
            pause=0.4
        ),
    ]),
    Scene(formula, header="What sets the period?", steps=[
        Step(
            "The period depends mainly on pendulum length and local gravity.",
            pause=0.3
        ),
        Step(
            "T equals two pi times the square root of length over g.",
            sub="T ≈ 2π√(L/g), for small swings.",
            pause=0.7,
            sfx=[("chime", 0.3, {"n": 4})]
        ),
    ]),
    Scene(test, header="Try a real length", sounds=test_sounds, steps=[
        Step(
            "For a {length_say} meter pendulum, a full period, there and back, takes about {period_say} seconds.",
            sub="For a {length} m pendulum, a full period—there and back—takes about {period} s.",
            pause=0.3
        ),
        Step(
            "Start both together, and their small swings stay nearly in step.",
            pause=0.8
        ),
    ]),
    Scene(outro, header=None, steps=[
        Step(
            "Large swings take longer, and friction gradually drains energy.",
            pause=0.3
        ),
        Step(
            "Small swings keep a steady beat, not a constant speed.",
            pause=0.5
        ),
        Step(
            "Follow for more physics like this.",
            pause=0.6,
            sfx=[("chime", 0.1, {"n": 3})]
        ),
    ]),
]
