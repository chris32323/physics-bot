from engine.style import *

TOPIC = "The Doppler Effect"
TITLE = "Why a passing siren changes pitch #physics #shorts"
DESCRIPTION = (
    "A moving siren crowds sound waves ahead and spreads them behind. "
    "See why a stationary listener hears a changing pitch."
)
TAGS = ["physics", "Doppler effect", "sound", "waves", "siren"]

EPISODE = 25
AIR_TEMPERATURE = 20.0
SOUND_SPEED = 343.0
SOURCE_SPEED = 30.0
TONE = 600.0
APPROACH = TONE * SOUND_SPEED / (SOUND_SPEED - SOURCE_SPEED)
RECEDE = TONE * SOUND_SPEED / (SOUND_SPEED + SOURCE_SPEED)


def spoken_integer(value):
    n = int(round(value))
    small = [
        "zero", "one", "two", "three", "four", "five", "six",
        "seven", "eight", "nine", "ten", "eleven", "twelve",
        "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen"
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
    "episode": f"{EPISODE:.0f}",
    "temperature": f"{AIR_TEMPERATURE:.0f}",
    "tone": f"{TONE:.0f}",
    "speed": f"{SOURCE_SPEED:.0f}",
    "sound": f"{SOUND_SPEED:.0f}",
    "up": f"{APPROACH:.0f}",
    "down": f"{RECEDE:.0f}",
    "temperature_words": spoken_integer(AIR_TEMPERATURE),
    "tone_words": spoken_integer(TONE),
    "speed_words": spoken_integer(SOURCE_SPEED),
    "sound_words": spoken_integer(SOUND_SPEED),
    "up_words": spoken_integer(APPROACH),
    "down_words": spoken_integer(RECEDE),
}


# Schematic geometry: source speed is exaggerated for visible spacing.
# Each ring remains centered where the source emitted it.
WAVE_C = 200.0
WAVE_V = 90.0
WAVE_INTERVAL = 0.22
WAVE_END = 2.2
WAVE_X = 310.0
WAVE_Y = 1140.0


def wave_picture(c, physical_time, scale=1.0):
    for k in range(11):
        emitted = k * WAVE_INTERVAL
        age = physical_time - emitted
        if age > 0:
            c.ring(
                510 + (WAVE_X + WAVE_V * emitted - 510) * scale,
                WAVE_Y,
                WAVE_C * age * scale, FG, lw=3, alpha=0.38
            )

    x = 510 + (WAVE_X + WAVE_V * physical_time - 510) * scale
    c.panel(x, WAVE_Y, 100, 64, edge=PINK, fill=PANEL, radius=18)
    c.ball(x, WAVE_Y + 39, r=19, color=PINK)
    c.arrow(x - 45, WAVE_Y - 85, x + 90, WAVE_Y - 85, PINK, lw=5)


# ---------------------------------------------------------------- 1 · hook
def hook(c):
    c.heading(510, 1660, "Why does the\npitch drop?", size=64)
    wave_picture(c, WAVE_END)
    c.text(220, 780, "SPREAD OUT", size=31, color=PURPLE, weight="bold")
    c.text(770, 780, "CROWDED", size=31, color=BLUE, weight="bold")
    c.text(510, 660, "Same siren. Different pitch.", size=35,
           alpha=c.appear(1, 0.1))
    c.text(510, 900, "Schematic • spacing exaggerated", size=24, color=MUTED)


# ---------------------------------------------------------------- 2 · moving source
def waves(c):
    launch = c.cue(0) + 0.2
    # Constant physical-time scale, followed by a deliberate freeze-frame.
    physical_time = min(max((c.t - launch) * 0.55, 0.0), WAVE_END)
    # Keep the largest ring below both explanatory labels.
    wave_picture(c, physical_time, scale=0.68)

    c.text(510, 1580, "Each ring is one wavefront", size=36)
    c.text(510, 1495, "Schematic • spacing exaggerated",
           size=24, color=MUTED)

    a = c.appear(1, 0.1, 0.6)
    c.text(225, 800, "Farther apart", size=32, color=PURPLE, alpha=a)
    c.text(770, 800, "Closer together", size=32, color=BLUE, alpha=a)
    c.arrow(180, 870, 320, 870, PURPLE, lw=4, alpha=a)
    c.arrow(730, 870, 790, 870, BLUE, lw=4, alpha=a)

    b = c.appear(2, 0.15, 0.6)
    c.panel(510, 675, 820, 110, edge=YELLOW, alpha=b)
    c.text(510, 675, "More arrivals per second\n= higher pitch",
           size=30, color=YELLOW, alpha=b)


# ---------------------------------------------------------------- 3 · computed comparison
def comparison(c):
    c.text(510, 1530, "Emitted tone: " + FACTS["tone"] + " Hz",
           size=42, color=PINK)
    c.text(510, 1430, "Stationary listener", size=30, color=MUTED)

    a = c.appear(1, 0.0, 0.5)
    c.text(510, 1340, "Siren speed: " + FACTS["speed"] + " m/s",
           size=32, alpha=a)

    cards = [
        (1, 295, BLUE, "APPROACHING",
         r"$f_{\rm heard}=f\,\frac{c}{c-v_s}$", FACTS["up"]),
        (2, 745, PURPLE, "RECEDING",
         r"$f_{\rm heard}=f\,\frac{c}{c+v_s}$", FACTS["down"]),
    ]
    for step, x, color, label, formula, value in cards:
        b = c.appear(step, 0.15, 0.6)
        c.panel(x, 1050, 410, 440, edge=color, alpha=b)
        c.text(x, 1210, label, size=29, color=color, weight="bold", alpha=b)
        c.text(x, 1080, formula, size=38, alpha=b)
        c.heading(x, 930, value + " Hz", size=54, color=YELLOW, alpha=b)

    c.text(510, 725, "c = sound speed   •   vₛ = source speed",
           size=27, color=MUTED, alpha=a)
    c.text(510, 640, "Motion directly toward or away",
           size=27, color=MUTED, alpha=a)


# ---------------------------------------------------------------- 4 · assumptions and real life
def conditions(c):
    c.heading(510, 1530, "Sound moves through air", size=48)
    c.text(510, 1410, "≈ " + FACTS["sound"] + " m/s", size=54, color=GREEN)
    c.text(510, 1335, "Still air at about " + FACTS["temperature"] + "°C",
           size=28, color=MUTED)

    # Stationary markers represent the stationary air.
    for row in range(5):
        for col in range(9):
            c.dot(190 + col * 80, 910 + row * 70, 4, MUTED, 0.55)

    start = c.cue(0) + 0.15
    p = min(max((c.t - start) / 2.0, 0.0), 1.0)
    c.ring(510, 1050, 230 * p + 1, GREEN, lw=4, alpha=0.7)
    c.ball(510, 1050, r=22, color=PINK)

    b = c.appear(1, 0.1, 0.6)
    c.panel(510, 710, 850, 150, edge=PINK, alpha=b)
    c.text(510, 710, "Real sirens can change their own tone",
           size=32, color=PINK, alpha=b)


# ---------------------------------------------------------------- 5 · takeaway
def outro(c):
    c.heading(510, 1650, "Motion changes\narrival rate", size=60)

    c.panel(510, 1280, 820, 180, edge=BLUE)
    c.arrow(155, 1280, 255, 1280, BLUE, lw=7)
    c.text(310, 1280, "Approaching: higher pitch",
           size=28, color=BLUE, weight="bold", ha="left")

    c.panel(510, 1030, 820, 180, edge=PURPLE)
    c.arrow(255, 1030, 155, 1030, PURPLE, lw=7)
    c.text(310, 1030, "Receding: lower pitch",
           size=28, color=PURPLE, weight="bold", ha="left")

    b = c.appear(1, 0.1, 0.5)
    c.panel(510, 735, 650, 140, fill=PINK, alpha=b, radius=60)
    c.text(510, 735, "Follow for more physics",
           size=38, color=FG, weight="bold", alpha=b)


SCENES = [
    Scene(hook, header=None, steps=[
        Step("Why does a passing siren change pitch?", pause=0.3),
        Step("Its motion changes what reaches you, even with a steady tone.",
             pause=0.4),
    ]),
    Scene(waves, header="Watch the wavefronts", steps=[
        Step("Sound travels through still air as expanding waves.",
             pause=1.0, sfx=[("whoosh", 0.2)]),
        Step("The moving siren crowds wavefronts ahead and spreads them behind.",
             pause=0.6),
        Step("More wavefronts arriving each second means higher pitch.",
             pause=0.5, sfx=[("note", 0.2, {"n": 6})]),
    ]),
    Scene(comparison, header="Test the pitch", steps=[
        Step("Take a steady {tone_words} hertz siren and a stationary listener.",
             sub="Take a steady {tone} Hz siren and a stationary listener."),
        Step("Approaching at {speed_words} meters per second, it sounds about {up_words} hertz.",
             sub="Approaching at {speed} m/s: about {up} Hz.",
             pause=0.7, sfx=[("note", 0.3, {"n": 6})]),
        Step("Receding at that speed, it sounds about {down_words} hertz.",
             sub="Receding at the same speed: about {down} Hz.",
             pause=0.7, sfx=[("note", 0.3, {"n": 2})]),
    ]),
    Scene(conditions, header="The assumptions", steps=[
        Step("In still air at about {temperature_words} degrees Celsius, sound travels at approximately {sound_words} meters per second.",
             sub="In still air at about {temperature}°C, sound travels at approximately {sound} m/s.",
             pause=0.4),
        Step("Real sirens also change their own tone.",
             pause=0.3),
    ]),
    Scene(outro, header=None, steps=[
        Step("Approaching means higher pitch; moving away means lower pitch.",
             pause=0.5, sfx=[("chime", 0.15, {"n": 3})]),
        Step("Follow for more physics.", pause=0.8),
    ]),
]
