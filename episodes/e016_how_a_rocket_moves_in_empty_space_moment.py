from engine.style import *

TOPIC = "Rockets in Empty Space"
TITLE = "What do rockets push against in space? #physics #shorts"
DESCRIPTION = (
    "Rockets accelerate by throwing propellant backward, not by pushing against air. "
    "See Newton's third law and momentum conservation in one idealized example."
)
TAGS = ["physics", "rockets", "momentum", "Newton's third law", "space"]
TEASER = "Why is the sky blue, but sunsets red?"

# All velocities in the example use the original rest frame.
# The expelled gas is idealized as a single packet with a common velocity.
ROCKET_MASS = 900.0
GAS_MASS = 100.0
GAS_SPEED = 900.0
ROCKET_SPEED = GAS_MASS * GAS_SPEED / ROCKET_MASS
MOMENTUM = GAS_MASS * GAS_SPEED

FACTS = {
    "mr": f"{ROCKET_MASS:.0f}",
    "mg": f"{GAS_MASS:.0f}",
    "vg": f"{GAS_SPEED:.0f}",
    "vr": f"{ROCKET_SPEED:.0f}",
    "p": f"{MOMENTUM:,.0f}",
}


def rocket(c, x, y, scale=1.0, alpha=1.0):
    points = [
        (x + scale * dx, y + scale * dy)
        for dx, dy in [
            (-80, -43), (45, -43), (105, 0),
            (45, 43), (-80, 43)
        ]
    ]
    c.polygon(points, PINK, alpha)
    for sign in (-1, 1):
        c.polygon([
            (x - 65 * scale, y + sign * 33 * scale),
            (x - 98 * scale, y + sign * 75 * scale),
            (x - 15 * scale, y + sign * 43 * scale),
        ], PINK, alpha)
    c.panel(x - 90 * scale, y, 28 * scale, 58 * scale,
            fill=MUTED, alpha=alpha, radius=5)
    c.ball(x + 36 * scale, y, r=17 * scale, color=BLUE, alpha=alpha)


def gas_packet(c, x, y, scale=1.0, alpha=1.0):
    for dx, dy, radius in [
        (0, 0, 22), (-32, 29, 15), (28, 24, 17),
        (-30, -27, 18), (30, -25, 14)
    ]:
        c.dot(x + dx * scale, y + dy * scale,
              radius * scale, PURPLE, alpha)


# ---------------------------------------------------------------- 1 · hook
def hook(c):
    c.heading(520, 1620, "PUSH AGAINST\nWHAT?", size=64)
    c.text(520, 1450, "A rocket in vacuum", size=32, color=MUTED)

    # A complete, recognizable rocket and exhaust are visible on frame one.
    start = c.cue(0)
    elapsed = max(0.0, c.t - start)
    travel = min(elapsed, 5.0) * 13
    rocket(c, 625 + travel, 1140, scale=1.35)

    for k in range(9):
        phase = ((elapsed * 0.55 + k / 9.0) % 1.0)
        x = 490 + travel - 330 * phase
        spread = 18 + 75 * phase
        y = 1140 + math.sin(k * 2.4) * spread
        c.dot(x, y, 10 + 8 * phase, PURPLE, 0.9 - 0.6 * phase)

    a = c.appear(1, 0.1, 0.7)
    c.arrow(430, 920, 180, 920, BLUE, alpha=a)
    c.text(305, 850, "gas backward", size=32, color=PURPLE, alpha=a)
    c.arrow(610, 920, 850, 920, BLUE, alpha=a)
    c.text(730, 850, "rocket forward", size=32, color=PINK, alpha=a)


# ---------------------------------------------------------------- 2 · Newton's third law
def forces(c):
    rocket(c, 680, 1190, scale=1.25)
    gas_packet(c, 335, 1190, scale=1.3)
    c.text(335, 1050, "GAS", size=32, color=PURPLE)
    c.text(680, 1050, "ROCKET", size=32, color=PINK)

    a = c.appear(0, 0.1, 0.7)
    c.arrow(680, 1305, 850, 1305, GREEN, lw=8, alpha=a)
    c.text(690, 1450, "Gas pushes rocket", size=32, color=GREEN, alpha=a)

    b = c.appear(1, 0.1, 0.7)
    c.arrow(335, 1305, 165, 1305, GREEN, lw=8, alpha=b)
    c.text(310, 1535, "Rocket pushes gas", size=32, color=GREEN, alpha=b)

    d = c.appear(2, 0.1, 0.6)
    c.panel(520, 790, 800, 180, edge=GREEN, alpha=d)
    c.text(520, 835, "Equal forces. Opposite directions.", size=32,
           color=GREEN, alpha=d)
    c.text(520, 755, "Different objects.", size=38, weight="bold", alpha=d)


# ---------------------------------------------------------------- 3 · momentum
def momentum(c):
    c.text(520, 1530, "No external force", size=36, color=GREEN)
    c.text(520, 1420, r"$p_{\rm total}=\mathrm{constant}$",
           size=54, color=YELLOW, alpha=c.appear(0, 0.1))

    launch = c.cue(0) + 0.2
    elapsed = min(max(c.t - launch, 0.0), 3.0)
    gx = 430 - elapsed * 45
    rx = 610 + elapsed * 15
    gas_packet(c, gx, 1180, scale=1.25)
    rocket(c, rx, 1180, scale=1.15)

    a = c.appear(1, 0.1, 0.7)
    c.arrow(gx, 1000, gx - 150, 1000, BLUE, lw=7, alpha=a)
    c.arrow(rx, 1000, rx + 150, 1000, BLUE, lw=7, alpha=a)
    c.text(300, 910, "backward momentum", size=29, color=PURPLE, alpha=a)
    c.text(740, 910, "forward momentum", size=29, color=PINK, alpha=a)

    c.panel(520, 715, 770, 150, edge=YELLOW, alpha=a)
    c.text(520, 715, r"$m_{\rm rocket}v_{\rm rocket}=-m_{\rm gas}v_{\rm gas}$",
           size=40, alpha=a)


# ---------------------------------------------------------------- 4 · numerical test
def numbers(c):
    c.text(520, 1540, "Idealized gas packet", size=34, color=MUTED)
    c.text(280, 1410, FACTS["mg"] + " kg gas",
           size=36, color=PURPLE)
    c.text(760, 1410, FACTS["mr"] + " kg rocket",
           size=36, color=PINK)

    # Both displacements use one constant time scale.
    # Their ratio is the physical speed ratio, not an eased interpolation.
    launch = c.cue(1) + 0.15
    duration = max(c.stop(1) - launch, 0.5)
    elapsed = min(max(c.t - launch, 0.0), duration)
    pixels_per_meter = 360.0 / (GAS_SPEED * duration)
    gx = 480 - GAS_SPEED * elapsed * pixels_per_meter
    rx = 650 + ROCKET_SPEED * elapsed * pixels_per_meter
    gas_packet(c, gx, 1190, scale=1.05)
    rocket(c, rx, 1190, scale=1.1)

    a = c.appear(1, 0.1, 0.5)
    c.text(520, 1030, "Original rest frame", size=30, color=MUTED, alpha=a)
    c.text(520, 930, "Gas:  −" + FACTS["vg"] + " m/s",
           size=42, color=PURPLE, alpha=a)

    b = c.appear(2, 0.1, 0.6)
    c.text(520, 820, "Rocket:  +" + FACTS["vr"] + " m/s",
           size=44, color=YELLOW, alpha=b)
    c.panel(520, 655, 820, 140, edge=YELLOW, alpha=b)
    c.text(520, 655,
           FACTS["mr"] + " × " + FACTS["vr"] + " = "
           + FACTS["mg"] + " × " + FACTS["vg"],
           size=40, alpha=b)


# ---------------------------------------------------------------- 5 · takeaway and teaser
def outro(c):
    a = c.appear(0, 0.0, 0.5)
    c.heading(520, 1600, "PROPELLANT,\nNOT AIR.", size=64, alpha=a)
    rocket(c, 670, 1320, scale=1.0, alpha=a)
    gas_packet(c, 300, 1320, scale=1.0, alpha=a)
    c.arrow(440, 1320, 360, 1320, BLUE, alpha=a)
    c.arrow(810, 1320, 900, 1320, BLUE, alpha=a)

    b = c.appear(1, 0.1, 0.6)
    c.text(520, 1110, "Tomorrow:", size=34, color=BLUE,
           weight="bold", alpha=b)
    c.heading(520, 960, "Why is the sky blue,\nbut sunsets red?",
              size=48, alpha=b)

    d = c.appear(2, 0.0, 0.5)
    c.panel(520, 680, 740, 130, fill=PINK, alpha=d, radius=55)
    c.text(520, 680, "Follow for daily physics", size=34,
           color=FG, weight="bold", alpha=d)


SCENES = [
    Scene(hook, header=None, steps=[
        Step("What do rockets push against?", pause=0.3),
        Step("Not space: they throw hot gas backward.",
             pause=0.7, sfx=[("whoosh", 0.1)]),
    ]),
    Scene(forces, header="Action and reaction", steps=[
        Step("Inside the engine, expanding gas pushes on the rocket.",
             pause=0.3),
        Step("The rocket pushes equally hard on gas, in the opposite direction.",
             pause=0.5, sfx=[("note", 0.2, {"n": 3})]),
        Step("These forces act on different objects, so they cannot cancel.",
             pause=0.4),
    ]),
    Scene(momentum, header="Momentum is shared", steps=[
        Step("With no external force, their total momentum stays constant.",
             pause=0.5),
        Step("Starting from rest, forward rocket momentum balances backward gas momentum.",
             pause=0.6, sfx=[("chime", 0.3, {"n": 4})]),
    ]),
    Scene(numbers, header="Try real numbers", steps=[
        Step("Imagine {mr} kilograms of rocket and {mg} kilograms of expelled gas.",
             sub="Imagine {mr} kg of rocket and {mg} kg of expelled gas.",
             pause=0.3),
        Step("In the starting frame, gas travels backward at {vg} meters per second.",
             sub="In the starting frame, gas travels backward at {vg} m/s.",
             pause=0.7, sfx=[("whoosh", 0.15)]),
        Step("The rocket must move forward at {vr} meters per second.",
             sub="The rocket must move forward at {vr} m/s.",
             pause=0.7, sfx=[("chime", 0.2, {"n": 5})]),
    ]),
    Scene(outro, header=None, steps=[
        Step("Rockets need propellant to accelerate, not air to push against.",
             pause=0.3),
        Step("Tomorrow: " + TEASER, pause=0.3),
        Step("Follow, so you don't miss it.",
             pause=0.5, sfx=[("note", 0.1, {"n": 4})]),
    ]),
]
