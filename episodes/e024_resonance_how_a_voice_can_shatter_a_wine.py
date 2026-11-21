from engine.style import *

TOPIC = "Resonance"
TITLE = "Can a voice really shatter a glass? #physics #shorts"
DESCRIPTION = (
    "A matching note can build a glass's vibration through resonance. "
    "An illustrative oscillator model shows why pitch, damping, and sound intensity all matter."
)
TAGS = ["physics", "resonance", "sound", "wine glass", "oscillations"]

# Illustrative linear oscillator, before fracture.
F0 = 600.0
DETUNE = 20.0
F_OFF = F0 + DETUNE
Q = 100.0
OMEGA0 = 2 * math.pi * F0
TAU = 2 * Q / OMEGA0


def response(f):
    r = f / F0
    return 1 / math.sqrt((1 - r * r) ** 2 + (r / Q) ** 2)


RATIO = response(F0) / response(F_OFF)


def spoken_integer(n):
    n = int(round(n))
    small = [
        "zero", "one", "two", "three", "four", "five", "six", "seven",
        "eight", "nine", "ten", "eleven", "twelve", "thirteen",
        "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"
    ]
    tens = ["", "", "twenty", "thirty", "forty", "fifty",
            "sixty", "seventy", "eighty", "ninety"]
    if n < 20:
        return small[n]
    if n < 100:
        return tens[n // 10] + (" " + small[n % 10] if n % 10 else "")
    return small[n // 100] + " hundred" + (
        " " + spoken_integer(n % 100) if n % 100 else ""
    )


FACTS = {
    "f": f"{F0:.0f}",
    "off": f"{F_OFF:.0f}",
    "delta": f"{DETUNE:.0f}",
    "ratio": f"{RATIO:.0f}",
    "q": f"{Q:.0f}",
    "f_words": spoken_integer(F0),
    "delta_words": spoken_integer(DETUNE),
    "ratio_words": spoken_integer(RATIO),
}


# Shared glass silhouette. Deformation is intentionally exaggerated.
def glass(c, x, rim_y, radius, height, deformation=0, alpha=1):
    stretch = 1 + deformation
    th = np.linspace(0, math.pi, 60)
    c.line(
        x + radius * stretch * np.cos(th),
        rim_y - height * np.sin(th),
        FG, lw=4, alpha=0.8 * alpha
    )
    ring = np.linspace(0, 2 * math.pi, 80)
    c.line(
        x + radius * stretch * np.cos(ring),
        rim_y + radius * 0.23 * (1 - deformation) * np.sin(ring),
        PINK, lw=5, alpha=alpha, glow=True
    )
    bottom = rim_y - height
    stem_bottom = bottom - height * 0.65
    c.line([x, x], [bottom, stem_bottom], FG, lw=5, alpha=alpha)
    c.line(
        [x - radius * 0.5, x, x + radius * 0.5],
        [stem_bottom - 15, stem_bottom, stem_bottom - 15],
        FG, lw=5, alpha=alpha
    )


def wavefronts(c, x, y, start, alpha=1):
    phase = ((max(c.t - start, 0) * 0.8) % 1)
    for k in range(3):
        radius = 36 + 42 * (k + phase)
        c.arc(x, y, radius, -38, 38, BLUE, lw=4,
              alpha=alpha * (1 - (k + phase) / 4))


# ---------------------------------------------------------------- 1: hook
def hook(c):
    c.heading(510, 1630, "Can a voice\nshatter glass?", size=64)
    phase = 2 * math.pi * 0.85 * (c.t - c.cue(0))
    glass(c, 620, 1270, 220, 255, 0.10 * math.sin(phase))
    wavefronts(c, 135, 1270, c.cue(0))
    c.text(155, 1080, "VOICE", size=30, color=BLUE, weight="bold")
    c.text(510, 695, "Motion slowed and exaggerated", size=27, color=MUTED)

    a = c.appear(1, 0.2, 0.5)
    c.panel(510, 1430, 640, 78, edge=YELLOW, alpha=a)
    c.text(510, 1430, "Pitch matters, too", size=36,
           color=YELLOW, alpha=a)


# ---------------------------------------------------------------- 2: the natural mode
def natural(c):
    cx, cy, radius = 510, 1190, 235
    phase = 2 * math.pi * 0.75 * (c.t - c.cue(0))
    a = c.appear(0, 0.2, 0.5)
    deformation = 0.13 * a * math.sin(phase)
    th = np.linspace(0, 2 * math.pi, 120)
    rr = radius * (1 + deformation * np.cos(2 * th))

    c.line(cx + radius * np.cos(th), cy + radius * np.sin(th),
           MUTED, lw=2, alpha=0.45, dash=(4, 5))
    c.line(cx + rr * np.cos(th), cy + rr * np.sin(th),
           PINK, lw=7, glow=True)
    c.text(510, 1560, "The rim, viewed from above", size=32)
    c.text(510, 790, "A natural pattern of vibration", size=30, color=PINK)

    tap = c.pulse(c.cue(0) + 0.2, 0.8)
    c.arrow(145, 1190, 240, 1190, YELLOW, lw=7, alpha=tap)
    c.ring(270, 1190, 25 + 45 * (1 - tap), YELLOW, lw=3, alpha=tap)

    b = c.appear(1, 0.15)
    c.text(510, 860, "Ringing pitch = natural frequency",
           size=32, color=YELLOW, alpha=b)

    d = c.appear(2, 0.1)
    # At resonance the drive is in phase with velocity.
    drive = math.cos(phase)
    c.arrow(120, cy, 120 - 90 * drive, cy, BLUE, lw=7, alpha=d)
    c.arrow(900, cy, 900 + 90 * drive, cy, BLUE, lw=7, alpha=d)
    c.text(510, 680, "Matching sound keeps the pushes in time",
           size=29, color=BLUE, alpha=d)


# ---------------------------------------------------------------- 3: buildup and damping
def buildup(c):
    c.text(510, 1540, "Small pushes can build big motion",
           size=36, weight="bold")

    x0, y0, width, height = 145, 880, 740, 330
    c.arrow(x0, y0, x0 + width + 20, y0, MUTED, lw=3, glow=False)
    c.arrow(x0, y0, x0, y0 + height + 70, MUTED, lw=3, glow=False)
    c.text(155, 1330, "Vibration amplitude", size=28, ha="left", color=PINK)
    c.text(830, 815, "Time", size=28, color=MUTED)

    # High-Q resonant envelope: exp(-omega0*t/(2Q)).
    # The simulation's time advances at a constant rate over the reveal.
    elapsed = max(0, c.t - c.cue(0) - 0.2)
    physical_time = min(elapsed / 3.0, 1) * 5 * TAU
    ts = np.linspace(0, physical_time, 110)
    xs = x0 + width * ts / (5 * TAU)
    ys = y0 + height * (1 - np.exp(-ts / TAU))
    c.line(xs, ys, PINK, lw=6, glow=True)
    c.dot(xs[-1], ys[-1], 11, PINK, 1)

    b = c.appear(1, 0.1)
    c.line([x0, x0 + width], [y0 + height, y0 + height],
           MUTED, lw=2, alpha=b * 0.65, dash=(5, 5))
    c.panel(510, 700, 780, 125, edge=GREEN, alpha=b)
    c.text(510, 700, "At steady vibration:\nenergy in = energy lost",
           size=29, color=GREEN, alpha=b)

    d = c.appear(2, 0.1)
    c.text(510, 1430, "The sound supplies the energy",
           size=34, color=BLUE, alpha=d)


# ---------------------------------------------------------------- 4: equal-pressure comparison
def comparison(c):
    c.text(510, 1560, "Same sound pressure", size=40, weight="bold")

    left_x, right_x, rim_y = 285, 755, 1235
    phase = 2 * math.pi * 0.8 * (c.t - c.cue(0))
    a = c.appear(0, 0.15)
    b = c.appear(1, 0.15)

    glass(c, left_x, rim_y, 137, 195,
          0.18 * math.sin(phase) * a)
    glass(c, right_x, rim_y, 137, 195,
          0.18 * math.sin(phase) / RATIO * b, alpha=b)

    c.text(left_x, 1440, FACTS["f"] + " Hz", size=44,
           color=YELLOW, alpha=a)
    c.text(left_x, 1365, "Matched", size=30, color=YELLOW, alpha=a)
    c.text(right_x, 1440, FACTS["off"] + " Hz", size=44,
           color=BLUE, alpha=b)
    c.text(right_x, 1365, "Off pitch", size=30, color=BLUE, alpha=b)

    c.text(100, 805, "Amplitude", size=28, ha="left", color=MUTED)
    c.line([140, 430], [735, 735], YELLOW, lw=18, alpha=a)
    c.line([610, 610 + 290 / RATIO], [735, 735], BLUE, lw=18, alpha=b)
    c.text(755, 805, FACTS["ratio"] + "× smaller",
           size=32, color=BLUE, alpha=b)

    d = c.appear(2, 0.1)
    for x in (left_x, right_x):
        c.arrow(x - 80, rim_y, x + 50, rim_y, BLUE, lw=6, alpha=d)
    c.text(510, 620,
           "Linear steady-state model • Q = " + FACTS["q"],
           size=25, color=MUTED)


# ---------------------------------------------------------------- 5: threshold and takeaway
def outro(c):
    c.heading(510, 1620, "Matching pitch.\nEnough vibration.", size=60)
    phase = 2 * math.pi * 0.8 * (c.t - c.cue(0))
    a = c.appear(0, 0.1)
    glass(c, 510, 1280, 195, 215, 0.14 * math.sin(phase) * a)

    # A schematic crack illustrates the material's failure threshold.
    crack = c.appear(0, 1.4, 0.7)
    c.line([600, 570, 590, 545, 565],
           [1250, 1205, 1170, 1125, 1090],
           YELLOW, lw=5, alpha=crack)
    c.text(510, 820, "Resonance builds motion", size=36,
           color=YELLOW, alpha=a)

    b = c.appear(1, 0.1)
    c.text(510, 735, "Breaking glass creates dangerous shards",
           size=29, color=MUTED, alpha=b)

    d = c.appear(2, 0.1)
    c.panel(510, 635, 620, 92, fill=PINK, alpha=d, radius=44)
    c.text(510, 635, "Follow for more physics", size=34,
           color=FG, weight="bold", alpha=d)


SCENES = [
    Scene(hook, header=None, steps=[
        Step("Can a voice really shatter a glass?",
             sfx=[("whoosh", 0.15)]),
        Step("Yes, but loudness alone is not the trick.",
             pause=0.3, sfx=[("pop", 0.2)]),
    ]),
    Scene(natural, header="Find the ringing pitch", steps=[
        Step("Tap a thin glass, and its rim vibrates at a natural frequency.",
             pause=0.4, sfx=[("note", 0.2, {"n": 5})]),
        Step("The ringing pitch reveals that frequency.",
             pause=0.3),
        Step("A matching note repeatedly pushes the rim in time with its motion.",
             pause=0.6),
    ]),
    Scene(buildup, header="Energy builds up", steps=[
        Step("Each well timed push adds energy, like pushing a swing.",
             pause=0.8),
        Step("Vibration builds until energy supplied balances energy lost through damping.",
             pause=0.5, sfx=[("note", 0.2, {"n": 3})]),
        Step("The energy comes from the sound, not from nowhere.",
             pause=0.3),
    ]),
    Scene(comparison, header="Test the pitch", steps=[
        Step("Imagine a glass ringing at {f_words} hertz.",
             sub="Imagine a glass ringing at {f} Hz.",
             pause=0.4),
        Step("In this model, {delta_words} hertz off pitch makes vibration about {ratio_words} times smaller.",
             sub="In this model, {delta} Hz off pitch makes vibration about {ratio}× smaller.",
             pause=0.8, sfx=[("chime", 0.3, {"n": 4})]),
        Step("Both notes have identical sound pressure.",
             pause=0.4),
    ]),
    Scene(outro, header=None, steps=[
        Step("Shattering needs intense, sustained vibration strong enough to create stresses that exceed the glass's strength.",
             sub="Shattering needs intense, sustained vibration strong enough to create stresses that exceed the glass's strength.",
             pause=0.4),
        Step("Only suitable glasses break, and shards make demonstrations dangerous.",
             pause=0.3),
        Step("Follow for more physics like this.",
             pause=0.7, sfx=[("chime", 0.15, {"n": 2})]),
    ]),
]
