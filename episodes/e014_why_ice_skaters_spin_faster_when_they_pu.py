from engine.style import *

TOPIC = "Angular Momentum"
TITLE = "Why pulling your arms in makes you spin faster #physics #shorts"
DESCRIPTION = (
    "Ice skaters spin faster by changing how their mass is distributed. "
    "See angular momentum conservation in action—and where the extra energy comes from."
)
TAGS = ["physics", "angular momentum", "ice skating", "rotation", "science"]
TEASER = "Why do a hammer and a feather fall equally fast on the Moon?"

# Ideal model: a fixed central inertia plus two equal point masses.
CORE_I = 1.0
HAND_MASS = 1.5
R_WIDE = 1.0
R_TIGHT = math.sqrt(1.0 / 3.0)
F_WIDE = 1.0

def inertia(r):
    return CORE_I + 2 * HAND_MASS * r * r

I_WIDE = inertia(R_WIDE)
I_TIGHT = inertia(R_TIGHT)
OMEGA_WIDE = 2 * math.pi * F_WIDE
ANGULAR_MOMENTUM = I_WIDE * OMEGA_WIDE
F_TIGHT = ANGULAR_MOMENTUM / I_TIGHT / (2 * math.pi)
ENERGY_WIDE = 0.5 * I_WIDE * OMEGA_WIDE ** 2
ENERGY_TIGHT = 0.5 * I_TIGHT * (2 * math.pi * F_TIGHT) ** 2

def spoken_integer(value):
    return ["zero", "one", "two", "three", "four", "five"][int(round(value))]

FACTS = {
    "Iwide": f"{I_WIDE:.0f}",
    "Itight": f"{I_TIGHT:.0f}",
    "fwide": f"{F_WIDE:.0f}",
    "ftight": f"{F_TIGHT:.0f}",
    "Iwide_words": spoken_integer(I_WIDE),
    "Itight_words": spoken_integer(I_TIGHT),
    "fwide_words": spoken_integer(F_WIDE),
    "ftight_words": spoken_integer(F_TIGHT),
    "energy_ratio": f"{ENERGY_TIGHT / ENERGY_WIDE:.0f}",
}


# All skaters are top-down schematics, not anatomical simulations.
def skater(c, x, y, radius, angle, scale=1.0, alpha=1.0):
    reach = 240 * radius * scale
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx

    c.ring(x, y, 260 * scale, MUTED, lw=2, alpha=0.2 * alpha)
    c.line(
        [x - reach * dx, x + reach * dx],
        [y - reach * dy, y + reach * dy],
        PINK, lw=13 * scale, alpha=alpha
    )
    c.ball(x - reach * dx, y - reach * dy, 22 * scale, PINK, alpha)
    c.ball(x + reach * dx, y + reach * dy, 22 * scale, PINK, alpha)
    c.ball(x, y, 52 * scale, PURPLE, alpha)
    c.line(
        [x - 32 * scale * px, x + 32 * scale * px],
        [y - 32 * scale * py, y + 32 * scale * py],
        FG, lw=8 * scale, alpha=alpha
    )
    c.dot(x + 21 * scale * dx, y + 21 * scale * dy,
          9 * scale, FG, alpha)


def contracting_state(c, step, duration=3.6):
    """Fixed video-to-physical clock; omega follows L/I throughout contraction."""
    start = c.cue(step)
    elapsed = max(0.0, c.t - start)
    times = np.linspace(0.0, elapsed, 100)
    p = np.clip(times / duration, 0.0, 1.0)
    smooth = p * p * (3.0 - 2.0 * p)
    radii = R_WIDE + (R_TIGHT - R_WIDE) * smooth
    omegas = ANGULAR_MOMENTUM / (CORE_I + 2 * HAND_MASS * radii ** 2)
    # Slow motion: one physical second takes four video seconds.
    angle = float(np.sum((omegas[1:] + omegas[:-1]) * np.diff(times) / 2)) / 4
    return float(radii[-1]), angle


# ---------------------------------------------------------------- 1 · hook
def hook(c):
    c.heading(510, 1640, "Pull in.\nSpin faster.", size=64)
    _, contraction_end = c.voice(1)
    radius, angle = contracting_state(
        c, 1, duration=max(0.1, contraction_end - c.cue(1))
    )
    initial_elapsed = max(0.0, min(c.t, c.cue(1)) - c.cue(0))
    angle += OMEGA_WIDE * initial_elapsed / 4
    skater(c, 510, 1160, radius, angle, scale=1.3)

    a = c.appear(1)
    c.arc(510, 1160, 340, 25, 305, YELLOW, lw=7, alpha=a)
    c.text(510, 715, "No push from the ice?", size=38,
           color=YELLOW, alpha=c.appear(2))
    c.text(510, 615, "Watch where the mass goes", size=30,
           color=MUTED, alpha=c.appear(3))


# ---------------------------------------------------------------- 2 · mass distribution
def distribution(c):
    c.text(510, 1540, "Same skater. Same mass.", size=42)
    angle = 0.35
    skater(c, 290, 1190, R_WIDE, angle, scale=0.75)
    skater(c, 760, 1190, R_TIGHT, angle, scale=0.75,
           alpha=c.appear(1))

    c.text(290, 900, "Spread out", size=32, color=PINK)
    c.text(760, 900, "Tucked in", size=32, color=PINK,
           alpha=c.appear(1))

    a = c.appear(2)
    c.panel(510, 735, 820, 160, edge=PURPLE, alpha=a)
    c.text(510, 770, "Rotational inertia", size=38,
           color=PURPLE, alpha=a)
    c.text(510, 705, "Mass farther out contributes more", size=29,
           alpha=a)

    b = c.appear(3)
    for x in (290, 760):
        c.dot(x, 1190, 8, YELLOW, b)
    c.text(510, 605, "Distance from the spin axis matters", size=28,
           color=YELLOW, alpha=b)


# ---------------------------------------------------------------- 3 · conservation
def conservation(c):
    c.text(510, 1545, "Angular momentum", size=42, color=YELLOW)
    c.text(510, 1435, r"$L = I\,\omega$", size=64,
           alpha=c.appear(1))

    radius, angle = contracting_state(c, 2)
    skater(c, 510, 1070, radius, angle, scale=1.0)

    a = c.appear(0)
    c.text(510, 700, "Negligible external twisting", size=31,
           color=GREEN, alpha=a)
    b = c.appear(3)
    c.text(290, 605, "I decreases", size=35, color=PURPLE, alpha=b)
    c.text(755, 605, "ω increases", size=35, color=YELLOW, alpha=b)


# ---------------------------------------------------------------- 4 · numerical test
def numbers(c):
    elapsed = max(0.0, c.t - c.cue(0))
    skater(c, 290, 1280, R_WIDE,
           OMEGA_WIDE * elapsed / 4, scale=0.72)
    skater(c, 760, 1280, R_TIGHT,
           2 * math.pi * F_TIGHT * elapsed / 4, scale=0.72)

    c.text(510, 1605, "¼-speed slow motion", size=30, color=YELLOW)
    c.text(290, 1535, "Before", size=38, color=PINK)
    c.text(760, 1535, "After", size=38, color=PINK)

    rows = [
        (0, 985, FACTS["Iwide"] + " kg·m²",
         FACTS["Itight"] + " kg·m²", PURPLE),
        (1, 865, FACTS["fwide"] + " turn/s", "", YELLOW),
        (2, 865, "", FACTS["ftight"] + " turns/s", YELLOW),
    ]
    for step, y, left, right, color in rows:
        a = c.appear(step, 0.15)
        if left:
            c.text(290, y, left, size=36, color=color, alpha=a)
        if right:
            c.text(760, y, right, size=36, color=color, alpha=a)

    a = c.appear(3)
    c.panel(510, 680, 800, 140, edge=YELLOW, alpha=a)
    c.text(510, 680, "Half the inertia → twice the speed",
           size=34, color=YELLOW, alpha=a)


# ---------------------------------------------------------------- 5 · energy
def energy(c):
    c.text(510, 1540, "Where does the energy come from?", size=38)
    radius, angle = contracting_state(c, 1)
    skater(c, 510, 1180, radius, angle, scale=0.9)

    a = c.appear(1)
    # Internal muscle forces act at the hands, radially toward the spin axis.
    reach = 240 * radius * 0.9
    dx, dy = math.cos(angle), math.sin(angle)
    arrow_length = 65
    for side in (-1, 1):
        c.arrow(
            510 + side * reach * dx,
            1180 + side * reach * dy,
            510 + side * (reach - arrow_length) * dx,
            1180 + side * (reach - arrow_length) * dy,
            GREEN, lw=7, alpha=a
        )
    c.text(510, 870, "Internal muscle forces do work", size=34,
           color=GREEN, alpha=a)

    b = c.appear(2)
    c.text(510, 750, r"$K_{\rm rot}=\frac{L^2}{2I}$",
           size=54, color=YELLOW, alpha=b)
    if c.t < c.cue(3):
        c.text(510, 620, "Angular momentum stays; rotational energy grows",
               size=28, alpha=b)
    else:
        c.text(510, 620,
               "With friction, angular momentum\nis only approximately conserved.",
               size=28, alpha=c.appear(3))


# ---------------------------------------------------------------- 6 · takeaway
def outro(c):
    a = c.appear(0)
    c.heading(510, 1590, "Mass inward.\nSpin faster.", size=60, alpha=a)
    c.text(510, 1420, "When external torque is negligible", size=29,
           color=GREEN, alpha=a)

    b = c.appear(1)
    c.text(510, 1240, "Tomorrow:", size=34, color=BLUE, alpha=b)
    c.heading(510, 1060, wrap(TEASER, 27), size=45, alpha=b)

    d = c.appear(2)
    c.panel(510, 710, 770, 120, fill=PINK, radius=55, alpha=d)
    c.text(510, 710, "Follow for daily physics", size=34,
           color=FG, weight="bold", alpha=d)


SCENES = [
    Scene(hook, header=None, steps=[
        Step("Why do tucked skaters spin faster?",
             sfx=[("whoosh", 0.1)]),
        Step("They pull their arms inward, and their rotation speeds up.", pause=0.7),
        Step("But they are not getting another push from the ice.", pause=0.4),
        Step("The secret is how their mass is arranged."),
    ]),
    Scene(distribution, header="Where the mass sits", steps=[
        Step("Imagine watching the same skater from directly above."),
        Step("Their mass stays the same when their arms move inward.", pause=0.5),
        Step("But their rotational inertia gets smaller, making their spin easier to change.",
             pause=0.5, sfx=[("note", 0.2, {"n": 2})]),
        Step("Mass farther from the spin axis contributes more to rotational inertia.", pause=0.6),
    ]),
    Scene(conservation, header="What stays constant?", steps=[
        Step("Assume external twisting forces are negligible, so angular momentum stays constant."),
        Step("Angular momentum equals rotational inertia times angular speed.",
             sub="Angular momentum: L = Iω",
             sfx=[("note", 0.2, {"n": 4})]),
        Step("Watch the arms move inward while that product stays unchanged.",
             pause=1.2, sfx=[("whoosh", 0.2)]),
        Step("Smaller inertia must therefore mean faster rotation.", pause=0.8),
    ]),
    Scene(numbers, header="Test the trade", steps=[
        Step("Suppose our simplified skater reduces inertia from {Iwide_words} to {Itight_words} kilogram meters squared.",
             sub="Suppose inertia falls from {Iwide} to {Itight} kg·m².", pause=0.6),
        Step("They initially complete {fwide_words} turn per second.",
             sub="Initially: {fwide} turn/s.", pause=0.5),
        Step("Conservation then requires {ftight_words} turns per second.",
             sub="Afterward: {ftight} turns/s.", pause=1.0,
             sfx=[("chime", 0.2, {"n": 5})]),
        Step("Halving rotational inertia doubles angular speed in this idealized example.", pause=0.7),
    ]),
    Scene(energy, header="Who pays for speed?", steps=[
        Step("Faster rotation also means more rotational kinetic energy here."),
        Step("The skater supplies that energy by doing work with their muscles.",
             pause=0.7),
        Step("At fixed angular momentum, rotational energy increases as inertia decreases.",
             sub="At fixed L: Kᵣₒₜ = L² / (2I)", pause=0.7),
        Step("Real ice adds friction, so angular momentum is only approximately conserved."),
    ]),
    Scene(outro, header=None, steps=[
        Step("So pulling mass inward increases spin speed when external torque is negligible.",
             pause=0.5),
        Step("Tomorrow: " + TEASER, pause=0.6),
        Step("Follow, so you don't miss it.",
             pause=0.8, sfx=[("chime", 0.1, {"n": 3})]),
    ]),
]
