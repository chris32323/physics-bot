from engine.style import *

TOPIC = "Blue Skies, Red Sunsets"
TITLE = "Why blue skies turn into red sunsets #physics #shorts"
DESCRIPTION = (
    "Air scatters short wavelengths more strongly than long ones. "
    "See how the same process makes daytime skies blue and sunset sunlight red."
)
TAGS = ["physics", "Rayleigh scattering", "sky", "sunset", "light", "science"]
TEASER = "How can a huge steel ship float?"

BLUE_NM = 450.0
RED_NM = 650.0
POWER = 4
SCATTER_RATIO = (RED_NM / BLUE_NM) ** POWER
RED = "#ff4545"

FACTS = {
    "blue": f"{BLUE_NM:.0f}",
    "red": f"{RED_NM:.0f}",
    "ratio": f"{SCATTER_RATIO:.1f}",
    "power": f"{POWER:.0f}",
    "ordinal": ["zeroth", "first", "second", "third", "fourth"][POWER],
}


def sun(c, x, y, r, color=YELLOW, alpha=1):
    c.dot(x, y, r * 1.55, color, alpha * 0.07)
    c.dot(x, y, r * 1.23, color, alpha * 0.13)
    c.ball(x, y, r=r, color=color, alpha=alpha)


def observer(c, x, y, alpha=1):
    c.ring(x, y + 70, 24, FG, 4, alpha)
    c.line([x, x], [y + 44, y - 30], FG, lw=5, alpha=alpha)
    c.line([x - 30, x, x + 30], [y - 70, y - 30, y - 70],
           FG, lw=5, alpha=alpha)
    c.line([x - 34, x, x + 34], [y, y + 20, y],
           FG, lw=5, alpha=alpha)


# ---------------------------------------------------------------- 1 · hook
def hook(c):
    # A complete, readable thumbnail is present at time zero.
    c.heading(520, 1645, "BLUE SKY.", size=64, color=BLUE)
    c.heading(520, 1545, "RED SUNSET.", size=64, color=ORANGE)

    c.arc(530, 920, 395, 0, 180, BLUE, 13, 0.55)
    c.arc(530, 920, 430, 0, 180, BLUE, 4, 0.2)
    for x, y in [(260, 1170), (420, 1290), (650, 1280), (815, 1135)]:
        c.dot(x, y, 13, BLUE, 0.65)

    sun(c, 530, 970, 105, ORANGE)
    c.ground(870, 90, 970)

    a = c.appear(1, 0.1, 0.7)
    c.text(520, 700, "Same sunlight. Different paths.", size=36, alpha=a)
    colors = [PURPLE, BLUE, GREEN, YELLOW, ORANGE, PINK]
    for i, col in enumerate(colors):
        y = 795 - i * 9
        c.line([350, 690], [y, y], col, lw=5, alpha=a)


# ---------------------------------------------------------------- 2 · scattered light
def molecules(c):
    c.text(245, 1480, "SUNLIGHT", size=30, color=YELLOW)

    a = c.appear(0, 0.1, 0.6)
    for offset, col in [(-14, RED), (0, YELLOW), (14, BLUE)]:
        c.arrow(110, 1260 + offset, 490, 1260 + offset,
                col, lw=5, alpha=a, glow=False)

    c.dot(535, 1260, 55, FG, 0.06)
    c.ring(535, 1260, 32, FG, 4, a)
    c.text(535, 1390, "air molecule", size=32, alpha=a)

    # Redirected rays grow from the molecule, anchored to the first cue.
    for dx, dy in [(260, 220), (-190, -230), (285, -310)]:
        p = c.appear(0, 0.5, 1.0)
        c.arrow(535, 1260, 535 + dx * p, 1260 + dy * p,
                BLUE, lw=5, alpha=0.65 * p, glow=False)

    b = c.appear(1, 0.1, 0.7)
    c.arrow(575, 1250, 920, 1250, RED, lw=5, alpha=0.7 * b)
    c.text(760, 1160, "less redirection", size=28, color=RED, alpha=b)

    d = c.appear(2, 0.0, 0.6)
    observer(c, 825, 850, d)
    c.text(825, 700, "your eye", size=30, alpha=d)

    # A blue packet travels along the redirected ray at constant speed.
    start = c.cue(2) + 0.2
    end = max(start + 0.5, c.stop(2) - 0.25)
    p = c.lin(start, end)
    if c.t >= start:
        c.ball(lerp(535, 820, p), lerp(1260, 950, p),
               r=13, color=BLUE, alpha=d)

    c.text(390, 760, "BLUE REACHES YOU", size=30,
           color=BLUE, alpha=d)


# ---------------------------------------------------------------- 3 · wavelength comparison
def comparison(c):
    a = c.appear(0, 0.05, 0.6)
    c.text(520, 1510, "Rayleigh scattering by air molecules",
           size=32, color=MUTED, alpha=a)
    formula = r"$\mathrm{strength}\ \propto\ \frac{1}{\lambda^{" + FACTS["power"] + r"}}$"
    c.text(520, 1400, formula, size=58, alpha=a)
    c.text(520, 1320, "λ = wavelength", size=32, color=FG, alpha=a)

    b = c.appear(1, 0.1, 0.8)
    baseline = 840
    height = 360
    c.line([180, 870], [baseline, baseline], MUTED, lw=3, alpha=b)

    c.rect(270, baseline, 155, height * b, BLUE, 0.9 * b)
    c.rect(625, baseline, 155, height / SCATTER_RATIO * b, RED, 0.9 * b)

    c.text(347, 775, FACTS["blue"] + " nm", size=34, color=BLUE, alpha=b)
    c.text(702, 775, FACTS["red"] + " nm", size=34, color=RED, alpha=b)
    c.text(347, 1250, FACTS["ratio"] + "×", size=42, color=YELLOW, alpha=b)

    d = c.appear(2, 0.1, 0.6)
    c.panel(520, 640, 820, 100, edge=PURPLE, alpha=d)
    c.text(520, 640, "Violet: more scattering, less visible", size=29,
           color=PURPLE, alpha=d)


# ---------------------------------------------------------------- 4 · the long sunset path
def sunset(c):
    a = c.appear(0, 0.05, 0.6)

    # An exaggerated atmospheric shell makes the geometric comparison clear.
    cx, cy = 800, 180
    earth_r, air_r = 900, 1050
    eye_x, eye_y = cx, cy + earth_r + 30
    xs = np.linspace(80, 960, 90)
    surface = [cy + math.sqrt(earth_r ** 2 - (x - cx) ** 2) for x in xs]
    outer = [cy + math.sqrt(air_r ** 2 - (x - cx) ** 2) for x in xs]
    shell = list(zip(xs, outer)) + list(zip(xs[::-1], surface[::-1]))
    c.polygon(shell, BLUE, 0.12 * a)
    c.line(xs, outer, BLUE, lw=5, alpha=0.8 * a)
    c.line(xs, surface, GREEN, lw=5, alpha=0.7 * a)
    c.text(430, 730, "Earth", size=30, color=GREEN, alpha=a)
    c.text(270, 950, "atmosphere", size=28, color=BLUE, alpha=a)
    c.text(520, 1580, "SAME AIR LAYER, DIFFERENT PATHS",
           size=32, color=BLUE, alpha=a)

    # Both Suns are alternative directions for the same observer.
    # The sunset Sun is level with the observer's eye, not high in the sky.
    sun(c, 140, eye_y, 43, ORANGE, a)
    c.text(185, 1245, "near horizon", size=28, color=ORANGE, alpha=a)
    sun(c, eye_x, 1400, 40, YELLOW, a)
    c.text(eye_x, 1490, "overhead", size=28, color=YELLOW, alpha=a)

    c.ring(eye_x, eye_y, 12, FG, 3, a)
    c.line([eye_x, eye_x], [eye_y - 12, eye_y - 30], FG, lw=4, alpha=a)
    c.line([eye_x - 12, eye_x, eye_x + 12],
           [eye_y - 35, eye_y - 25, eye_y - 35], FG, lw=4, alpha=a)
    c.text(eye_x, 1000, "your eye", size=28, alpha=a)

    entry_x = cx - math.sqrt(air_r ** 2 - (eye_y - cy) ** 2)
    top_y = cy + air_r
    p = c.appear(0, 0.2, 1.4)

    # Faint approach rays lie outside the atmosphere.
    c.line([190, entry_x], [eye_y, eye_y],
           YELLOW, lw=4, alpha=0.45 * a)
    c.line([eye_x, eye_x], [1350, top_y],
           YELLOW, lw=4, alpha=0.45 * a)

    # Bright sections show only the distance actually traveled through air.
    c.line([eye_x, eye_x], [top_y, lerp(top_y, eye_y, p)],
           YELLOW, lw=9, alpha=a, glow=True)
    c.line([entry_x, lerp(entry_x, eye_x, p)], [eye_y, eye_y],
           RED, lw=11, alpha=a, glow=True)
    c.text(900, 1265, "short", size=28, color=YELLOW, alpha=p)
    c.text(545, 1040, "long", size=28, color=RED, alpha=p)

    loss = c.appear(1, 0.1, 1.1)
    segments = 12
    for k in range(segments):
        u = k / segments
        v = (k + 1) / segments
        opacity = (1 - loss) * 0.8 + loss * 0.8 * math.exp(-5 * u)
        c.line([lerp(entry_x, eye_x, u), lerp(entry_x, eye_x, v)],
               [eye_y + 15, eye_y + 15],
               BLUE, lw=6, alpha=opacity * p)

    # Blue light leaves successive points of the long atmospheric path.
    for k, u in enumerate([0.18, 0.42, 0.66]):
        x = lerp(entry_x, eye_x, u)
        y = eye_y + 15
        b = c.appear(1, 0.15 + k * 0.25, 0.65)
        c.dot(x, y, 8, FG, b)
        c.arrow(x, y, x - 55 * b, y + 165 * b,
                BLUE, lw=5, alpha=b, glow=False)
        start = c.cue(1) + 0.15 + k * 0.25
        travel = c.lin(start, start + 1.1)
        if c.t >= start:
            c.ball(x - 55 * travel, y + 165 * travel,
                   r=10, color=BLUE, alpha=b * (1 - travel))

    c.text(520, 825, "less blue in the direct beam", size=30,
           color=RED, alpha=loss)

    d = c.appear(2, 0.1, 0.6)
    c.text(520, 620, "Dust and clouds modify the picture", size=29,
           color=MUTED, alpha=d)


# ---------------------------------------------------------------- 5 · takeaway and tomorrow
def outro(c):
    a = c.appear(0, 0.05, 0.6)
    c.heading(520, 1630, "SAME SCATTERING.", size=54, alpha=a)
    c.heading(520, 1510, "Blue sky.", size=58, color=BLUE, alpha=a)
    c.heading(520, 1420, "Red sunset.", size=58, color=ORANGE, alpha=a)

    b = c.appear(1, 0.1, 0.6)
    c.text(520, 1220, "Tomorrow:", size=32, color=YELLOW, alpha=b)
    c.heading(520, 1090, wrap(TEASER, 25), size=46, alpha=b)

    # A simple ship silhouette previews the next episode.
    c.polygon([(330, 900), (730, 900), (665, 835), (395, 835)],
              MUTED, b)
    c.rect(460, 900, 160, 65, MUTED, b)
    c.line([230, 810, 850], [835, 835, 835], BLUE, lw=5, alpha=b)

    d = c.appear(2, 0.05, 0.6)
    c.panel(520, 660, 700, 110, fill=PINK, alpha=d)
    c.text(520, 660, "Follow for daily physics", size=32,
           color=FG, weight="bold", alpha=d)


SCENES = [
    Scene(hook, header=None, steps=[
        Step("Why does the Sun turn red?"),
        Step("Sunlight contains many colors, but air redirects them unequally.",
             pause=0.3, sfx=[("note", 0.2, {"n": 3})]),
    ]),
    Scene(molecules, header="Light takes a detour", steps=[
        Step("Air molecules scatter light, sending it in new directions.",
             pause=0.4, sfx=[("pop", 0.4, {"n": 2})]),
        Step("Shorter wavelengths scatter much more strongly than longer wavelengths.",
             pause=0.3),
        Step("That scattered blue light reaches you from across the sky.",
             pause=0.6, sfx=[("note", 0.2, {"n": 5})]),
    ]),
    Scene(comparison, header="How much stronger?", steps=[
        Step("For Rayleigh scattering by air molecules, strength scales inversely with wavelength to the {ordinal} power.",
             sub="Rayleigh scattering by air molecules: strength ∝ 1 / λ^{power}",
             pause=0.3),
        Step("Compare {blue} and {red} nanometers: blue scatters about {ratio} times as strongly.",
             sub="{blue} nm versus {red} nm: blue scatters about {ratio}× as strongly.",
             pause=0.6, sfx=[("chime", 0.7, {"n": 4})]),
        Step("Violet scatters more, but our eyes and sunlight favor blue.",
             pause=0.3),
    ]),
    Scene(sunset, header="More air, redder Sun", steps=[
        Step("At sunset, sunlight crosses much more air.",
             pause=0.5, sfx=[("whoosh", 0.2)]),
        Step("More blue leaves the direct beam, making the Sun look orange or red.",
             pause=0.7),
        Step("Dust and clouds can change the colors too.",
             pause=0.2),
    ]),
    Scene(outro, header=None, steps=[
        Step("Same scattering, blue skies and red sunsets.",
             pause=0.3),
        Step("Tomorrow: " + TEASER, pause=0.3),
        Step("Follow, so you don't miss it.",
             pause=0.5, sfx=[("chime", 0.1, {"n": 3})]),
    ]),
]
