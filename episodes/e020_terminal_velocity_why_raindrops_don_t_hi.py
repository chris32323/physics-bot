from engine.style import *

TOPIC = "Terminal Velocity"
TITLE = "Why raindrops don't hit like bullets #physics #shorts"
DESCRIPTION = (
    "Air drag stops raindrops from accelerating forever. "
    "Estimate a drop's terminal speed, then see why real drops differ."
)
TAGS = ["physics", "terminal velocity", "rain", "air resistance", "science"]

# ---------------------------------------------------------------- physics
G = 9.81
RHO_WATER = 1000.0
RHO_AIR = 1.2
DIAMETER = 0.002
CD = 0.60

AREA = math.pi * DIAMETER ** 2 / 4
VOLUME = math.pi * DIAMETER ** 3 / 6
MASS = RHO_WATER * VOLUME
WEIGHT = MASS * G
VT = math.sqrt(2 * WEIGHT / (RHO_AIR * CD * AREA))
KPH = VT * 3.6

FACTS = {
    "diameter": f"{DIAMETER * 1000:.0f}",
    "mass": f"{MASS * 1e6:.1f}",
    "cd": f"{CD:.1f}",
    "speed": f"{VT:.0f}",
    "kph": f"{KPH:.0f}",
}


def falling_distance(t):
    """Quadratic drag, released from rest, neglecting buoyancy."""
    return VT ** 2 / G * math.log(math.cosh(G * t / VT))


def ellipse(c, x, y, rx, ry, color=PINK, alpha=1):
    angles = np.linspace(0, 2 * math.pi, 48)
    c.polygon(
        [(x + rx * math.cos(a), y + ry * math.sin(a)) for a in angles],
        color,
        alpha,
    )


# ---------------------------------------------------------------- 1 · hook
def hook(c):
    c.heading(510, 1630, "Why isn't rain\na bullet storm?", size=62)

    # A bright, large drop is visible immediately in the thumbnail.
    launch = c.cue(1) + 0.15
    physical_t = min(max(c.t - launch, 0), 2.0)
    y = 1260 - 24 * falling_distance(physical_t)

    for x, yy, r in [(200, 1340, 12), (850, 1160, 15), (760, 1410, 10)]:
        c.ball(x, yy, r=r, color=PINK, alpha=0.35)
    c.ball(510, y, r=84, color=PINK)
    c.arc(490, y + 15, 40, 80, 160, FG, 5, 0.5)

    a = c.appear(1, 0.15, 0.5)
    weight_length = 130
    c.arrow(510, y - 105, 510, y - 105 - weight_length, GREEN, alpha=a)
    c.text(700, y - 175, "weight", size=32, color=GREEN, alpha=a)

    # Reveal drag alongside weight during the accelerating-drop sentence.
    # Quadratic drag remains below weight as the drop accelerates,
    # approaching equality as its speed approaches terminal speed.
    drag_ratio = math.tanh(G * physical_t / VT) ** 2
    c.arrow(510, y + 100, 510, y + 100 + weight_length * drag_ratio,
            GREEN, alpha=a)
    c.text(720, y + 195, "air drag", size=32, color=GREEN, alpha=a)

    b = c.appear(2, 0.1, 0.7)
    c.panel(510, 660, 760, 110, edge=GREEN, alpha=b)
    c.text(510, 660, r"$F_{\mathrm{drag}}\propto v^2$",
           size=44, color=GREEN, alpha=b)


# ---------------------------------------------------------------- 2 · forces catch up
def balance(c):
    c.ball(510, 1150, r=70, color=PINK)

    # This is a force comparison diagram, not a time-scaled falling trajectory.
    faster = c.appear(1, 0.2, 1.2)
    balanced = c.appear(2, 0.1, 0.9)
    ratio = lerp(0.18, 0.76, faster)
    ratio = lerp(ratio, 1.0, balanced)

    weight_length = 230
    drag_length = weight_length * ratio

    c.arrow(400, 1080, 400, 1080 - weight_length, GREEN, lw=8)
    c.text(265, 855, "weight", size=32, color=GREEN)

    c.arrow(620, 1220, 620, 1220 + drag_length, GREEN, lw=8)
    c.text(765, 1350, "drag", size=32, color=GREEN)

    heading = ("Same drop, constant terminal speed" if balanced >= 1.0
               else "Same drop, increasing speed")
    c.text(510, 1550, heading, size=32, color=MUTED)

    a = c.appear(0, 0.1, 0.5)
    c.text(510, 735, "Net downward force", size=30, color=GREEN, alpha=a)
    c.line([270, 750], [655, 655], MUTED, lw=3, alpha=0.4 * a)
    c.line([270, 270 + 480 * (1 - ratio)], [655, 655],
           GREEN, lw=16, alpha=a)

    c.text(510, 1510, "", size=22)
    # Keep the panel to the right of the downward force arrow.
    c.panel(730, 970, 440, 120, edge=YELLOW, alpha=balanced)
    c.text(730, 970, "Balanced ≠ stopped", size=32,
           color=YELLOW, weight="bold", alpha=balanced)

    # Retain the force arrows while replacing only the lower caption.
    c.text(510, 595, "Still falling • constant speed", size=30,
           color=YELLOW, alpha=balanced)


# ---------------------------------------------------------------- 3 · numerical test
def estimate(c):
    a = c.appear(0, 0.1, 0.5)
    c.text(510, 1540,
           r"$mg=\frac{1}{2}\rho_{\mathrm{air}}C_D A v_t^2$",
           size=48, alpha=a)
    c.text(510, 1435, "Spherical estimate • still air",
           size=30, color=MUTED, alpha=a)

    c.ball(275, 1200, r=78, color=PINK, alpha=a)
    c.line([197, 353], [1070, 1070], BLUE, lw=4, alpha=a)
    c.line([197, 197], [1050, 1090], BLUE, lw=3, alpha=a)
    c.line([353, 353], [1050, 1090], BLUE, lw=3, alpha=a)
    c.text(275, 1015, FACTS["diameter"] + " mm",
           size=36, color=BLUE, alpha=a)

    c.text(680, 1280, "Diameter  " + FACTS["diameter"] + " mm",
           size=32, alpha=a)
    c.text(680, 1180, "Mass  " + FACTS["mass"] + " mg",
           size=32, color=PINK, alpha=a)
    c.text(680, 1080, "Drag coefficient  " + FACTS["cd"],
           size=28, color=GREEN, alpha=a)

    b = c.appear(1, 0.2, 0.7)
    c.panel(510, 790, 760, 270, edge=YELLOW, alpha=b, glow=True)
    c.text(510, 875, "TERMINAL SPEED", size=28,
           color=YELLOW, weight="bold", alpha=b)
    c.heading(510, 785, "≈ " + FACTS["speed"] + " m/s",
              size=64, color=YELLOW, alpha=b)

    d = c.appear(2, 0.1, 0.5)
    c.text(510, 695, "≈ " + FACTS["kph"] + " km/h",
           size=36, color=YELLOW, alpha=d)


# ---------------------------------------------------------------- 4 · real drops
def real_drops(c):
    c.text(510, 1545, "Real drops change shape", size=42, weight="bold")

    a = c.appear(0, 0.15, 1.1)
    ellipse(c, 290, 1260, 66, 66, alpha=1)
    ellipse(c, 710, 1260, lerp(82, 120, a), lerp(82, 65, a), alpha=1)
    c.arrow(400, 1260, 535, 1260, MUTED, lw=4, alpha=a)
    c.text(290, 1110, "small: nearly round", size=28, color=PINK)
    c.text(710, 1110, "larger: flattened", size=28, color=PINK, alpha=a)

    # A schematic breakup, not a claim that every large drop splits identically.
    start = c.cue(0) + 1.3
    p = c.ramp(start, start + 1.2)
    c.text(510, 970, "Oversized drops can break apart",
           size=30, color=MUTED, alpha=p)

    for dx, dy, radius in [(-125, 15, 28), (-35, -65, 22),
                           (55, 45, 32), (135, -40, 24)]:
        c.ball(510 + dx * p, 820 + dy * p,
               r=lerp(18, radius, p), color=PINK, alpha=p)

    b = c.appear(1, 0.1, 0.6)
    c.text(510, 620, "Drop size + air conditions → terminal speed",
           size=29, color=YELLOW, alpha=b)


# ---------------------------------------------------------------- 5 · takeaway
def outro(c):
    c.heading(510, 1640, "Air sets a speed limit.", size=57)

    c.ball(510, 1260, r=62, color=PINK)
    a = c.appear(0, 0.1, 0.7)
    c.arrow(390, 1180, 390, 1010, GREEN, lw=7, alpha=a)
    c.arrow(630, 1340, 630, 1510, GREEN, lw=7, alpha=a)
    c.text(265, 1090, "weight", size=30, color=GREEN, alpha=a)
    c.text(765, 1420, "drag", size=30, color=GREEN, alpha=a)

    c.text(510, 920, "Tiny mass • limited speed",
           size=38, color=YELLOW, weight="bold", alpha=a)
    c.text(510, 820, r"$E_k=\frac{1}{2}mv^2$",
           size=46, color=PINK, alpha=a)

    b = c.appear(1, 0.1, 0.6)
    c.panel(510, 650, 660, 120, fill=PINK, alpha=b, radius=60)
    c.text(510, 650, "Follow for more physics", size=36,
           color=FG, weight="bold", alpha=b)


# ---------------------------------------------------------------- narration
SCENES = [
    Scene(hook, header=None, steps=[
        Step("Why isn't rain a bullet storm?"),
        Step("A falling drop gains speed, but air pushes back harder.",
             pause=0.4, sfx=[("whoosh", 0.15)]),
        Step("That upward drag grows roughly with its speed squared.",
             sub="That upward drag grows roughly with speed squared: drag ∝ v².",
             pause=0.5),
    ]),
    Scene(balance, header="Forces catch up", steps=[
        Step("Gravity pulls down with an almost constant force: its weight."),
        Step("As speed rises, drag catches up until these forces balance.",
             pause=0.7),
        Step("Acceleration stops, but the drop keeps falling at terminal velocity.",
             pause=0.7, sfx=[("chime", 0.6, {"n": 3})]),
    ]),
    Scene(estimate, header="Test a tiny drop", steps=[
        Step("Using a spherical model, let's estimate for a drop {diameter} millimeters across.",
             sub="Spherical model: a drop {diameter} mm across.",
             pause=0.3),
        Step("Equating weight and drag predicts about {speed} meters per second.",
             sub="Weight = drag → terminal speed ≈ {speed} m/s.",
             pause=0.7, sfx=[("chime", 0.5, {"n": 4})]),
        Step("That's roughly {kph} kilometers per hour, not a bullet's speed.",
             sub="That's roughly {kph} km/h, not a bullet's speed.",
             pause=0.4),
    ]),
    Scene(real_drops, header="Real rain differs", steps=[
        Step("Real raindrops deform, changing their drag, and oversized drops break apart.",
             pause=0.8),
        Step("The number varies with drop size and air conditions.",
             pause=0.3),
    ]),
    Scene(outro, header=None, steps=[
        Step("Air limits the speed, and each tiny drop carries little kinetic energy.",
             pause=0.5),
        Step("Follow for more physics like this.",
             pause=0.6, sfx=[("note", 0.15, {"n": 3})]),
    ]),
]
