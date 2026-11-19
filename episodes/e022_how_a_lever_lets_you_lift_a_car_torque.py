from engine.style import *

TOPIC = "Levers and Torque"
TITLE = "How a lever lets you lift a car #physics #shorts"
DESCRIPTION = (
    "A long lever can lift a heavy load with less force—but there's a trade. "
    "See how torque balances, and why a lever never multiplies energy."
)
TAGS = ["physics", "torque", "lever", "simple machines", "physics every day"]

# All example quantities are calculated here.
LOAD = 4000.0
LOAD_ARM = 0.2
EFFORT_ARM = 2.0
RATIO = EFFORT_ARM / LOAD_ARM
EFFORT = LOAD * LOAD_ARM / EFFORT_ARM


def whole_words(n):
    n = int(n)
    small = [
        "zero", "one", "two", "three", "four", "five", "six",
        "seven", "eight", "nine", "ten", "eleven", "twelve",
        "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen"
    ]
    tens = [
        "", "", "twenty", "thirty", "forty", "fifty",
        "sixty", "seventy", "eighty", "ninety"
    ]
    if n < 20:
        return small[n]
    if n < 100:
        return tens[n // 10] + (" " + small[n % 10] if n % 10 else "")
    if n < 1000:
        return small[n // 100] + " hundred" + (
            " " + whole_words(n % 100) if n % 100 else ""
        )
    return whole_words(n // 1000) + " thousand" + (
        " " + whole_words(n % 1000) if n % 1000 else ""
    )


def spoken_decimal(value):
    text = f"{value:.1f}"
    left, right = text.split(".")
    return whole_words(int(left)) + " point " + " ".join(
        whole_words(int(d)) for d in right
    )


FACTS = {
    "load": f"{LOAD:,.0f}",
    "short": f"{LOAD_ARM:.1f}",
    "long": f"{EFFORT_ARM:.0f}",
    "push": f"{EFFORT:.0f}",
    "ratio": f"{RATIO:.0f}",
    "load_say": whole_words(LOAD),
    "short_say": spoken_decimal(LOAD_ARM),
    "long_say": whole_words(EFFORT_ARM),
    "push_say": whole_words(EFFORT),
    "ratio_say": whole_words(RATIO),
}

# Diagram geometry preserves the example's arm ratio.
PX, PY = 660, 1010
LEFT = 550
RIGHT = LEFT / RATIO


def car(c, lift=0.0, alpha=1.0):
    """One end rises; the far wheel remains on its support."""
    near = PX + RIGHT
    far = 915

    def point(x, y):
        return (x, y + lift * (far - x) / (far - near))

    c.polygon(
        [point(675, 1060), point(700, 1120), point(755, 1120),
         point(790, 1180), point(855, 1180), point(895, 1120),
         point(940, 1105), point(940, 1060)],
        PINK, alpha
    )
    c.polygon(
        [point(790, 1130), point(807, 1165),
         point(848, 1165), point(875, 1130)],
        BG, alpha
    )
    for x in (near, far):
        wx, wy = point(x, 1040)
        c.ball(wx, wy, r=30, color=MUTED, alpha=alpha)
        c.dot(wx, wy, 13, BG, alpha)
    c.line([870, 965], [1010, 1010], MUTED, lw=5, alpha=alpha)


def machine(c, angle=0.0, show_car=True):
    lx = PX - LEFT * math.cos(angle)
    ly = PY - LEFT * math.sin(angle)
    rx = PX + RIGHT * math.cos(angle)
    ry = PY + RIGHT * math.sin(angle)
    c.polygon([(PX - 48, PY - 100), (PX + 48, PY - 100),
               (PX, PY - 10)], GREEN, 1)
    c.line([lx, rx], [ly, ry], FG, lw=13)
    c.dot(PX, PY, 12, YELLOW, 1)
    if show_car:
        car(c, ry - PY)
    return lx, ly, rx, ry


# ---------------------------------------------------------- 1: hook
def hook(c):
    c.heading(510, 1630, "Lift a car\nwith a bar?", size=64)
    angle = 0.18 * c.ramp(c.cue(1) + 0.2, c.cue(1) + 2.7)
    lx, ly, rx, ry = machine(c, angle)
    c.arrow(lx, ly + 230, lx, ly + 35, GREEN, lw=9)
    c.text(300, 1280, "YOUR PUSH", size=32, color=GREEN)
    a = c.appear(1, 0.3)
    c.text(470, 690, "Less force. More movement.", size=38,
           color=YELLOW, alpha=a)


# ---------------------------------------------------------- 2: turning effect
def torque(c):
    machine(c, show_car=False)
    a = c.appear(0, 0.1)
    c.text(PX, 815, "FULCRUM", size=32, color=GREEN, alpha=a)
    c.line([PX, PX], [850, 895], GREEN, lw=3, alpha=a)

    b = c.appear(1, 0.1)
    c.arrow(110, 1350, 110, 1050, GREEN, lw=8, alpha=b)
    c.arc(PX, PY, 145, 105, 230, YELLOW, lw=6, alpha=b)
    c.text(510, 1510, r"$\tau = F\,d_\perp$", size=62,
           color=YELLOW, alpha=b)
    c.text(510, 1410, "torque = force × distance", size=32, alpha=b)

    # Show the distance as it is defined, not in the following sentence.
    d = c.appear(1, 0.1, 0.8)
    c.line([110, 110], [930, 1380], GREEN, lw=2,
           alpha=0.6 * d, dash=(4, 4))
    c.line([PX, PX], [950, PY], BLUE, lw=3,
           alpha=0.8 * d, dash=(4, 4))
    c.line([110, PX], [950, 950], BLUE, lw=5, alpha=d)
    for x in (110, PX):
        c.line([x, x], [932, 968], BLUE, lw=4, alpha=d)
    c.line([110, 130, 130], [970, 970, 950],
           BLUE, lw=3, alpha=d)
    c.text(385, 895, r"$d_\perp$", size=42, color=BLUE, alpha=d)

    c.text(385, 735, "Farther from pivot → more torque", size=32,
           color=BLUE, alpha=c.appear(2, 0.1, 0.8))


# ---------------------------------------------------------- 3: numerical example
def numbers(c):
    machine(c)
    a = c.appear(0, 0.1)
    c.arrow(PX + RIGHT, 1400, PX + RIGHT, 1210,
            GREEN, lw=8, alpha=a)
    c.text(710, 1480, FACTS["load"] + " N", size=45,
           color=GREEN, alpha=a)

    b = c.appear(1, 0.1)
    c.line([110, PX], [880, 880], BLUE, lw=5, alpha=b)
    for x in (110, PX):
        c.line([x, x], [863, 897], BLUE, lw=3, alpha=b)
    c.text(350, 825, FACTS["long"] + " m", size=36,
           color=BLUE, alpha=b)

    # The short arm gets its own clear label block.
    c.line([PX, PX + RIGHT], [950, 950], ORANGE, lw=5, alpha=b)
    c.line([PX + RIGHT, 815], [950, 865], ORANGE, lw=2, alpha=b)
    c.text(825, 815, FACTS["short"] + " m", size=36,
           color=ORANGE, alpha=b)

    d = c.appear(2, 0.15)
    c.arrow(110, 1360, 110, 1050, GREEN, lw=8, alpha=d)
    c.text(245, 1440, FACTS["push"] + " N", size=48,
           color=YELLOW, alpha=d)
    c.panel(510, 660, 850, 120, edge=YELLOW, alpha=d)
    equation = (
        FACTS["push"] + r"$\,\mathrm{N}\times$" +
        FACTS["long"] + r"$\,\mathrm{m} = $" +
        FACTS["load"] + r"$\,\mathrm{N}\times$" +
        FACTS["short"] + r"$\,\mathrm{m}$"
    )
    c.text(510, 660, equation, size=34, alpha=d)


# ---------------------------------------------------------- 4: conservation of work
def trade(c):
    c.text(510, 1530, "THE TRADE", size=40, color=YELLOW, weight="bold")
    c.text(290, 1400, "YOUR END", size=32, color=GREEN)
    c.text(760, 1400, "CAR END", size=32, color=PINK)

    # Both travel lengths share a single scale and constant rate.
    p = c.lin(c.cue(0) + 0.25, c.cue(0) + 3.25)
    big_travel = 420
    small_travel = big_travel / RATIO
    left_start, left_end = 1280, 1280 - big_travel
    right_start, right_end = 1080, 1080 + small_travel
    left_y = left_start - big_travel * p
    right_y = right_start + small_travel * p
    a = c.appear(0, 0.0, 0.3)

    # A shared marker key makes the small upward displacement unambiguous.
    c.ring(375, 1330, 9, MUTED, lw=3, alpha=a)
    c.text(405, 1330, "Start", size=26, color=MUTED, ha="left", alpha=a)
    c.dot(565, 1330, 8, MUTED, a)
    c.text(595, 1330, "End", size=26, color=MUTED, ha="left", alpha=a)

    # Offset displacement brackets cannot be hidden by the moving markers.
    for x, bx, start, end, col in [
        (290, 200, left_start, left_end, GREEN),
        (760, 840, right_start, right_end, PINK),
    ]:
        c.line([x, x], [start, end], col, lw=3, alpha=0.35)
        c.line([x, bx], [start, start], col, lw=2, alpha=0.6 * a,
               dash=(3, 3))
        c.line([x, bx], [end, end], col, lw=2, alpha=0.6 * a,
               dash=(3, 3))
        c.line([bx, bx], [start, end], col, lw=4, alpha=a)
        for y in (start, end):
            c.line([bx - 12, bx + 12], [y, y], col, lw=4, alpha=a)
        c.ring(x, start, 10, col, lw=3, alpha=a)
        c.dot(x, end, 8, col, a)

    c.text(140, (left_start + left_end) / 2,
           FACTS["ratio"] + "d", size=36, color=GREEN, alpha=a)
    c.text(875, (right_start + right_end) / 2,
           "d", size=36, color=PINK, ha="left", alpha=a)

    # Direction arrows sit away from the markers, including the short rise.
    c.arrow(340, 1190, 340, 960, GREEN, lw=5, alpha=a, head=0.7)
    c.arrow(700, right_start, 700, right_end,
            PINK, lw=4, alpha=a, head=0.5)
    c.ball(290, left_y, r=16, color=GREEN)
    c.ball(760, right_y, r=10, color=PINK)
    c.text(490, 1190, "×" + FACTS["ratio"], size=54,
           color=YELLOW, alpha=c.appear(0, 0.5))

    b = c.appear(1, 0.1)
    c.panel(510, 730, 850, 150, edge=YELLOW, alpha=b)
    c.text(510, 755, r"$W_{\mathrm{in}} = W_{\mathrm{out}}$",
           size=48, color=YELLOW, alpha=b)
    c.text(510, 695, "Ideal rigid, weightless lever; no friction",
           size=27, color=MUTED, alpha=b)

    d = c.appear(2, 0.1)
    c.text(510, 610, "Real levers: bending, weight, friction", size=28,
           color=MUTED, alpha=d)


# ---------------------------------------------------------- 5: takeaway
def outro(c):
    c.heading(510, 1570, "More force.\nNot more energy.", size=62)
    a = c.appear(0, 0.15)
    machine(c, 0.12)
    c.text(380, 790, r"$F_{\mathrm{effort}}d_{\mathrm{effort}}"
           r"=F_{\mathrm{load}}d_{\mathrm{load}}$",
           size=40, color=YELLOW, alpha=a)
    b = c.appear(1, 0.1)
    c.panel(510, 640, 650, 110, fill=PINK, alpha=b, radius=50)
    c.text(510, 640, "Follow for more physics", size=36,
           color=FG, weight="bold", alpha=b)


SCENES = [
    Scene(hook, header=None, steps=[
        Step("Can a bar really lift a car?"),
        Step("Yes, by trading a longer movement for less force.",
             pause=0.6, sfx=[("whoosh", 0.2)]),
    ]),
    Scene(torque, header="The turning effect", steps=[
        Step("The fulcrum is the pivot around which the bar turns.",
             sfx=[("pop", 0.15)]),
        Step("Torque equals force times the perpendicular distance from pivot to force line.",
             sub="Torque: τ = F d⊥", pause=0.4),
        Step("Push farther away, and the same force produces more torque.",
             pause=0.5),
    ]),
    Scene(numbers, header="Balance the torques", steps=[
        Step("Suppose lifting one end requires {load_say} newtons.",
             sub="Suppose lifting one end requires {load} N."),
        Step("Place it {short_say} meters from the pivot, pushing {long_say} meters away.",
             sub="Load arm: {short} m. Effort arm: {long} m.", pause=0.5),
        Step("Balancing torques requires only {push_say} newtons of push.",
             sub="Balancing torques requires only {push} N of push.",
             pause=0.6, sfx=[("chime", 0.2, {"n": 4})]),
    ]),
    Scene(trade, header="Nothing comes free", steps=[
        Step("But your end moves {ratio_say} times farther than the lifted end of the car.",
             sub="But your end moves {ratio} times farther than the lifted end of the car.",
             pause=0.8, sfx=[("whoosh", 0.25)]),
        Step("Ideally, equal work goes in and comes out.", pause=0.4),
        Step("Real levers bend, have weight, and lose energy through friction."),
    ]),
    Scene(outro, header=None, steps=[
        Step("A lever multiplies force, not energy.", pause=0.5),
        Step("Follow for more physics like this.",
             pause=0.7, sfx=[("chime", 0.1, {"n": 4})]),
    ]),
]
