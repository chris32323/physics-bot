from engine.style import *

TOPIC = "Noise Cancellation"
TITLE = "How adding sound makes headphones quieter #physics #shorts"
DESCRIPTION = (
    "Noise-cancelling headphones create an opposing pressure pattern at your ears. "
    "See destructive interference in action—and why steady rumbles are easier to cancel."
)
TAGS = ["physics", "sound", "headphones", "noise cancellation", "interference"]

FREQUENCY = 200.0
PERIOD = 1.0 / FREQUENCY
MILLISECONDS = PERIOD * 1000.0
CYCLES = 2
ZERO = 0.0

FACTS = {
    "frequency": f"{FREQUENCY:.0f}",
    "period": f"{MILLISECONDS:.0f}",
    "zero": f"{ZERO:.0f}",
}


def wave(c, x0, x1, y, amplitude, color, reveal=1.0,
         sign=1.0, cycles=2.0, alpha=1.0, width=5):
    """A pressure-versus-time trace, revealed without changing its time scale."""
    if reveal <= 0:
        return
    u = np.linspace(0, reveal, max(2, int(150 * reveal)))
    c.line(
        x0 + (x1 - x0) * u,
        y + sign * amplitude * np.sin(2 * math.pi * cycles * u),
        color,
        lw=width,
        alpha=alpha,
        glow=True,
    )


def baseline(c, y, alpha=0.4):
    c.line([150, 930], [y, y], MUTED, lw=2, alpha=alpha, dash=(4, 5))


# ---------------------------------------------------------------- 1: hook
def hook(c):
    c.heading(540, 1640, "Add sound.\nHear less.", size=64)

    # A substantial headphone silhouette is visible in the first frame.
    c.arc(540, 1100, 280, 0, 180, MUTED, lw=22, alpha=1)
    c.panel(275, 1080, 120, 255, edge=BLUE, fill=PANEL, radius=48)
    c.panel(805, 1080, 120, 255, edge=ORANGE, fill=PANEL, radius=48)
    c.arc(540, 1090, 95, -75, 90, PINK, lw=9, alpha=1)
    c.arc(550, 1080, 45, -70, 100, PINK, lw=7, alpha=1)
    c.text(540, 885, "AT YOUR EAR", size=30, color=PINK)

    wave(c, 90, 390, 1250, 48, BLUE, cycles=1.5)
    a = c.appear(1, 0.1, 0.8)
    wave(c, 690, 990, 1250, 48, ORANGE, reveal=a, sign=-1, cycles=1.5)

    c.text(240, 1385, "Noise", size=32, color=BLUE)
    c.text(810, 1385, "Anti-noise", size=32, color=ORANGE, alpha=a)

    c.line([360, 720], [750, 750], GREEN, lw=7, alpha=a, glow=True)
    c.text(540, 670, "Less pressure variation", size=32, color=GREEN, alpha=a)


# ---------------------------------------------------------------- 2: pressure addition
def pressure(c):
    rows = [
        (0, 1440, "Incoming pressure", BLUE, 1),
        (1, 1120, "Opposite pressure", ORANGE, -1),
    ]
    for step, y, label, color, sign in rows:
        a = c.appear(step, 0.1, 0.7)
        c.text(170, y + 145, label, size=34, color=color,
               ha="left", alpha=a)
        baseline(c, y, 0.35 * a)
        wave(c, 150, 930, y, 85, color, reveal=a, sign=sign)

    # Corresponding pressure changes are highlighted at the same time coordinate.
    x_peak = 150 + (930 - 150) / (4 * CYCLES)
    h = c.appear(1, 0.6, 0.5)
    c.ring(x_peak, 1440 + 85, 22, YELLOW, lw=4, alpha=h)
    c.ring(x_peak, 1120 - 85, 22, YELLOW, lw=4, alpha=h)
    c.line([x_peak, x_peak], [1215, 1345], MUTED,
           lw=2, alpha=h, dash=(3, 5))

    a = c.appear(2, 0.1, 0.7)
    c.text(170, 925, "Sum at your ear", size=34, color=GREEN,
           ha="left", alpha=a)
    baseline(c, 790, 0.35 * a)
    c.line([150, 150 + 780 * a], [790, 790], GREEN,
           lw=7, alpha=a, glow=True)
    c.text(540, 655, "Pressure changes cancel", size=34,
           color=GREEN, alpha=a)


# ---------------------------------------------------------------- 3: the active system
def hardware(c):
    # A schematic, not a literal spatial picture of the air.
    items = [
        (0, 1460, "MICROPHONES", "Measure the noise", BLUE),
        (0, 1150, "PROCESSOR", "Predict pressure at the ear", PURPLE),
        (1, 840, "SPEAKER", "Create the opposing pattern", ORANGE),
    ]
    for step, y, title, label, color in items:
        delay = 0.1 if y != 1150 else 1.0
        a = c.appear(step, delay, 0.6)
        c.panel(540, y, 760, 200, edge=color, alpha=a)
        c.text(540, y + 40, title, size=32, color=color,
               weight="bold", alpha=a)
        c.text(540, y - 40, label, size=32, alpha=a)

    a = c.appear(0, 1.0, 0.6)
    c.arrow(540, 1345, 540, 1260, PURPLE, lw=5, alpha=a)
    b = c.appear(1, 0.1, 0.6)
    c.arrow(540, 1035, 540, 950, ORANGE, lw=5, alpha=b)

    c.text(540, 635, "Destructive interference", size=40,
           color=YELLOW, alpha=c.appear(2, 0.1, 0.6))


# ---------------------------------------------------------------- 4: numerical example
def test(c):
    a = c.appear(0, 0.1, 0.6)
    c.text(540, 1555, FACTS["frequency"] + " Hz hum",
           size=44, color=BLUE, weight="bold", alpha=a)
    c.text(540, 1465, "Pressure at the ear over time",
           size=30, color=MUTED, alpha=a)

    y, amp = 1190, 130
    baseline(c, y, 0.4 * a)
    reveal = c.ramp(c.cue(0) + 0.3, c.cue(0) + 2.2)
    wave(c, 150, 930, y, amp, BLUE, reveal=reveal, cycles=CYCLES)

    # One full cycle on the horizontal time axis.
    x0 = 150
    x1 = x0 + 780 / CYCLES
    bracket = c.appear(0, 1.6, 0.5)
    c.line([x0, x1], [945, 945], FG, lw=3, alpha=bracket)
    for x in (x0, x1):
        c.line([x, x], [930, 960], FG, lw=3, alpha=bracket)
    c.text((x0 + x1) / 2, 880, FACTS["period"] + " ms per cycle",
           size=32, alpha=bracket)

    b = c.appear(1, 0.1, 1.0)
    wave(c, 150, 930, y, amp, ORANGE,
         reveal=b, sign=-1, cycles=CYCLES)
    c.text(540, 1370, "Noise + matched anti-noise",
           size=32, color=ORANGE, alpha=b)

    # Peak and trough coincide in time, rather than being spatially separated.
    xp = x0 + 780 / (4 * CYCLES)
    c.line([xp, xp], [y - amp, y + amp], YELLOW,
           lw=2, alpha=b, dash=(3, 4))
    c.ring(xp, y + amp, 20, YELLOW, lw=3, alpha=b)
    c.ring(xp, y - amp, 20, YELLOW, lw=3, alpha=b)

    s = c.appear(1, 1.0, 0.7)
    c.line([150, 150 + 780 * s], [700, 700], GREEN,
           lw=7, alpha=s, glow=True)
    c.text(540, 615, "Ideal sum: " + FACTS["zero"] + " pressure change",
           size=32, color=GREEN, alpha=s)


# ---------------------------------------------------------------- 5: limits and takeaway
def outro(c):
    c.heading(540, 1630, "Best against\nsteady rumbles", size=60)

    a = c.appear(0, 0.1, 0.6)
    c.text(540, 1410, "Real cancellation is imperfect", size=34,
           color=MUTED, alpha=a)

    # Residual sound remains: practical ANC is not perfect silence.
    baseline(c, 1210, 0.35)
    wave(c, 150, 930, 1210, 90, BLUE, alpha=0.28)
    b = c.appear(1, 0.1, 0.9)
    wave(c, 150, 930, 1210, 90 * (1 - 0.82 * b), PINK)
    c.text(540, 1040, "Active: opposing sound", size=36,
           color=ORANGE, alpha=b)
    c.text(540, 950, "Passive: sound-blocking cups", size=36,
           color=BLUE, alpha=b)

    f = c.appear(2, 0.0, 0.6)
    c.panel(540, 730, 690, 130, fill=PINK, alpha=f, radius=55)
    c.text(540, 730, "Follow for more physics", size=38,
           color=FG, weight="bold", alpha=f)


SCENES = [
    Scene(hook, header=None, steps=[
        Step(
            "Can adding sound make your world quieter?",
            pause=0.2,
        ),
        Step(
            "These headphones fight incoming noise with another sound.",
            pause=0.5,
            sfx=[("whoosh", 0.1)],
        ),
    ]),
    Scene(pressure, header="Pressure adds up", steps=[
        Step(
            "Sound makes air pressure rise and fall around its resting value.",
            pause=0.5,
        ),
        Step(
            "Match a pressure rise with an equal pressure drop.",
            pause=0.6,
            sfx=[("note", 0.2, {"n": 3})],
        ),
        Step(
            "At your ear, those pressure changes add to zero.",
            pause=0.6,
            sfx=[("chime", 0.4, {"n": 3})],
        ),
    ]),
    Scene(hardware, header="Inside the headphones", steps=[
        Step(
            "Microphones measure noise, and electronics estimate the unwanted pressure at your ear.",
            pause=0.2,
        ),
        Step(
            "The speaker creates an opposite pressure pattern, timed to arrive there together.",
            pause=0.4,
            sfx=[("pop", 0.2)],
        ),
        Step(
            "This is destructive interference, not a wall blocking sound.",
            pause=0.3,
        ),
    ]),
    Scene(test, header="Match the timing", steps=[
        Step(
            "For a {frequency} hertz hum, each cycle lasts {period} milliseconds.",
            sub="For a {frequency} Hz hum, each cycle lasts {period} ms.",
            pause=0.7,
        ),
        Step(
            "The cancelling wave flips the pressure pattern, lining peaks up with troughs.",
            pause=0.8,
            sfx=[("chime", 1.1, {"n": 4})],
        ),
    ]),
    Scene(outro, header=None, steps=[
        Step(
            "Real headphones cannot match every sound perfectly, especially sudden or rapidly changing noise.",
            pause=0.2,
        ),
        Step(
            "They work best on steady low rumbles, alongside the cups physically blocking sound.",
            pause=0.4,
        ),
        Step(
            "Follow for more physics like this.",
            pause=0.8,
            sfx=[("chime", 0.1, {"n": 2})],
        ),
    ]),
]
