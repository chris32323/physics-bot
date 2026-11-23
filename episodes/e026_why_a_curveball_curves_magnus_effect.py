from engine.style import *

TOPIC = "The Magnus Effect"
TITLE = "Why a curveball curves #physics #shorts"
DESCRIPTION = (
    "A spinning baseball redirects air, and the air pushes back. "
    "See the Magnus effect from above, then test an illustrative baseball calculation."
)
TAGS = ["physics", "Magnus effect", "baseball", "curveball", "fluid dynamics"]

# Illustrative baseball, not a prediction for every pitch.
RHO = 1.2
RADIUS = 0.0366
MASS = 0.145
SPEED = 35.0
CL = 0.20
INTERVAL = 0.5
AREA = math.pi * RADIUS ** 2
FORCE = 0.5 * RHO * SPEED ** 2 * AREA * CL
ACCEL = FORCE / MASS
# Approximation: constant forward speed, fixed transverse force,
# and initially zero transverse velocity.
DEFLECTION = 0.5 * ACCEL * INTERVAL ** 2

FACTS = {
    "speed": f"{SPEED:.0f}",
    "mass": f"{MASS * 1000:.0f}",
    "force": f"{FORCE:.1f}",
    "time": f"{INTERVAL:.1f}",
    "bend": f"{DEFLECTION:.2f}",
    "cl": f"{CL:.2f}",
    "rho": f"{RHO:.1f}",
    "radius_cm": f"{RADIUS * 100:.2f}",
}


def baseball(c, x, y, radius=42, angle=0, alpha=1):
    c.ball(x, y, r=radius, color=PINK, alpha=alpha)
    c.arc(x, y, radius * 0.72, angle + 30, angle + 150,
          FG, 3, alpha * 0.8)
    c.arc(x, y, radius * 0.72, angle + 210, angle + 330,
          FG, 3, alpha * 0.8)


def spin_indicator(c, x, y, radius, alpha=1):
    c.arc(x, y, radius, 15, 285, PURPLE, 5, alpha)
    theta = math.radians(285)
    ex = x + radius * math.cos(theta)
    ey = y + radius * math.sin(theta)
    c.arrow(ex - 30 * (-math.sin(theta)),
            ey - 30 * math.cos(theta),
            ex, ey, PURPLE, lw=5, alpha=alpha, head=0.7)


# ---------------------------------------------------------------- 1: hook
def hook(c):
    c.heading(520, 1640, "Why does a\ncurveball curve?", size=64)
    c.text(520, 1470, "TOP VIEW", size=27, color=MUTED)

    q = np.linspace(0, 1, 100)
    xs = 150 + 720 * q
    ys = 900 + 350 * q ** 2
    c.line(xs, ys, PINK, lw=4, alpha=0.24, dash=(3, 4))
    c.line([150, 900], [900, 900], MUTED, lw=3,
           alpha=0.4, dash=(4, 5))

    # Constant animation time scale, not eased physical motion.
    p = clamp((c.t - c.cue(0) - 0.1) / 2.5)
    visible = np.linspace(0, p, 90)
    c.line(150 + 720 * visible, 900 + 350 * visible ** 2,
           PINK, lw=6, alpha=0.95, glow=True)
    x, y = 150 + 720 * p, 900 + 350 * p ** 2
    baseball(c, x, y, 43, 240 * max(0, c.t - c.cue(0)))

    # The force indicator follows the local normal, not a fixed direction.
    tangent_x, tangent_y = 720, 700 * p
    tangent_length = math.hypot(tangent_x, tangent_y)
    nx, ny = -tangent_y / tangent_length, tangent_x / tangent_length
    a = c.appear(1, 0.1, 0.5)
    c.arrow(x + 65 * nx, y + 65 * ny,
            x + 195 * nx, y + 195 * ny, GREEN, alpha=a)
    c.text(520, 715, "Spin → airflow → sideways force",
           size=34, color=YELLOW, alpha=a)


# ---------------------------------------------------------------- 2: air and spin
def airflow(c):
    cx, cy = 555, 1130
    c.text(520, 1550, "TOP VIEW • moving with the ball",
           size=29, color=MUTED)

    a = c.appear(0, 0.1, 0.6)
    c.arrow(690, 1430, 900, 1430, BLUE, alpha=a)
    c.text(580, 1430, "Ball travels", size=30, color=BLUE,
           ha="right", alpha=a)
    spin_indicator(c, cx, cy, 112, a)
    baseball(c, cx, cy, 68,
             angle=130 * max(0, c.t - c.cue(0)))
    # Clear strip below the streamlines and above the viscosity label.
    c.text(555, 870, "Counterclockwise spin",
           size=30, color=PURPLE, alpha=a)

    b = c.appear(1, 0.1, 0.8)
    c.ring(cx, cy, 83, PURPLE, lw=12, alpha=0.2 * b)
    c.text(520, 800, "Viscosity couples surface and air",
           size=30, color=FG, alpha=b)

    # Air comes from the right in the ball's frame.
    # The wake leaves toward the lower left: downward air momentum.
    p = c.lin(c.cue(2) + 0.15, c.cue(2) + 2.55)
    for offset in (-125, 125):
        u = np.linspace(0, max(p, 0.001), 65)
        xx = 930 - 760 * u
        yy = cy + offset - 130 * np.maximum((u - 0.52) / 0.48, 0) ** 1.3
        c.line(xx, yy, BLUE, lw=5, alpha=0.85 * c.appear(2),
               glow=True)
        if p > 0.04:
            c.arrow(xx[-2], yy[-2], xx[-1], yy[-1],
                    BLUE, lw=5, alpha=c.appear(2), head=0.8)

    d = c.appear(2, 1.8, 0.5)
    c.arrow(175, 1060, 120, 880, BLUE, alpha=d)
    c.text(240, 680, "Air deflected down", size=29,
           color=BLUE, ha="left", alpha=d)
    c.arrow(cx, cy + 140, cx, cy + 260, GREEN, alpha=d)
    c.text(700, 1355, "Force on ball", size=29,
           color=GREEN, alpha=d)


# ---------------------------------------------------------------- 3: force changes direction
def force_view(c):
    c.heading(520, 1515, "The Magnus force", size=56,
              alpha=c.appear(0))

    x, y = 450, 1090
    c.arrow(x, y, 830, y, BLUE, lw=7,
            alpha=c.appear(0, 0.1))
    c.text(800, 1020, "Velocity", size=32, color=BLUE,
           alpha=c.appear(0, 0.3))

    c.arrow(x, y, x, 1400, GREEN, lw=7,
            alpha=c.appear(0, 0.25))
    c.text(310, 1340, "Sideways\nforce", size=32, color=GREEN,
           alpha=c.appear(0, 0.45))
    spin_indicator(c, x, y, 88, c.appear(0))
    baseball(c, x, y, 47,
             angle=140 * max(0, c.t - c.cue(0)))

    p = c.lin(c.cue(1) + 0.2, c.cue(1) + 2.5)
    u = np.linspace(0, max(p, 0.001), 80)
    c.line(x + 390 * u, y + 240 * u ** 2,
           PINK, lw=5, alpha=c.appear(1), dash=(3, 3))
    a = c.appear(1, 0.5)
    c.panel(520, 765, 790, 145, edge=GREEN, alpha=a)
    c.text(520, 765, "A sideways push bends the path",
           size=35, color=FG, alpha=a)


# ---------------------------------------------------------------- 4: numerical illustration
def numbers(c):
    a = c.appear(0)
    c.text(520, 1595, "ILLUSTRATIVE BASEBALL", size=28,
           color=MUTED, alpha=a)
    c.text(520, 1520,
           f"Speed  {FACTS['speed']} m/s     Mass  {FACTS['mass']} g",
           size=34, alpha=a)
    c.text(520, 1450,
           f"Assumed lift coefficient Cₗ = {FACTS['cl']} • ρ = {FACTS['rho']} kg/m³",
           size=26, color=MUTED, alpha=a)
    c.text(520, 1380,
           f"A = cross-sectional area • radius = {FACTS['radius_cm']} cm",
           size=28, color=MUTED, alpha=a)

    b = c.appear(1, 0.1)
    c.text(520, 1290, r"$F_M=\frac{1}{2}\rho v^2 A C_L$",
           size=46, color=GREEN, alpha=b)
    c.text(520, 1205,
           f"Sideways force ≈ {FACTS['force']} N",
           size=39, color=GREEN, alpha=b)

    # Graph of transverse displacement, not a distorted flight trajectory.
    x0, y0, gw, gh = 180, 820, 660, 220
    d = c.appear(2)
    c.text(520, 1125, "Sideways displacement versus time",
           size=28, color=MUTED, alpha=d)
    c.arrow(x0, y0, x0 + gw + 30, y0, MUTED,
            lw=3, alpha=d, head=0.6)
    c.arrow(x0, y0, x0, y0 + gh + 20, MUTED,
            lw=3, alpha=d, head=0.6)

    physical_time = clamp((c.t - c.cue(2) - 0.2) / 2.5) * INTERVAL
    ts = np.linspace(0, physical_time, 80)
    yy = 0.5 * ACCEL * ts ** 2
    xx = x0 + gw * ts / INTERVAL
    gy = y0 + gh * yy / DEFLECTION
    c.line(xx, gy, YELLOW, lw=5, alpha=d, glow=True)
    c.ball(xx[-1], gy[-1], r=13, color=YELLOW, alpha=d)

    c.text(x0 + gw, y0 - 48, f"{FACTS['time']} s",
           size=29, color=MUTED, alpha=d)
    e = c.appear(2, 2.45, 0.5)
    c.text(680, 1010, f"{FACTS['bend']} m",
           size=40, color=YELLOW, alpha=e)

    # Keep the approximation visible throughout the calculation.
    c.text(520, 710,
           "Approx. constant forward speed • constant transverse force",
           size=24, color=MUTED, alpha=a)
    c.text(520, 665, "Initially no sideways velocity",
           size=26, color=MUTED, alpha=a)
    c.text(520, 595, r"$y=\frac{1}{2}\,\frac{F_M}{m}\,t^2$",
           size=39, color=FG, alpha=d)


# ---------------------------------------------------------------- 5: takeaway
def outro(c):
    c.heading(520, 1600, "Spin redirects air.\nAir pushes back.",
              size=60, alpha=c.appear(1))

    a = c.appear(0)
    c.text(520, 1400, "Real pitches also involve",
           size=31, color=MUTED, alpha=a)
    c.text(520, 1330, "seams • drag • gravity",
           size=34, color=MUTED, alpha=a)

    baseball(c, 520, 1060, 65,
             angle=140 * max(0, c.t - c.cue(0)))
    b = c.appear(1, 0.1)
    c.arrow(520, 1150, 520, 1260, GREEN, alpha=b)
    c.arrow(400, 1060, 260, 960, BLUE, alpha=b)
    c.arrow(640, 1060, 780, 960, BLUE, alpha=b)
    c.text(520, 850, "THE MAGNUS EFFECT",
           size=37, color=YELLOW, alpha=b)

    f = c.appear(2, 0.1)
    c.panel(520, 675, 660, 125, fill=PINK, alpha=f, radius=55)
    c.text(520, 675, "Follow for more physics",
           size=36, color=FG, weight="bold", alpha=f)


SCENES = [
    Scene(hook, header=None, steps=[
        Step("How can a pitch bend in midair?",
             pause=0.6, sfx=[("whoosh", 0.1)]),
        Step("Spin makes the surrounding air push sideways.",
             pause=0.4),
    ]),
    Scene(airflow, header="Spin redirects air", steps=[
        Step("From above, watch a ball spinning counterclockwise while traveling to the right.",
             pause=0.4),
        Step("Viscosity lets its spinning surface influence the nearby air.",
             pause=0.3, sfx=[("note", 0.2, {"n": 2})]),
        Step("The resulting airflow is deflected downward, so the ball feels an upward force.",
             pause=0.8, sfx=[("whoosh", 0.2)]),
    ]),
    Scene(force_view, header="A sideways push", steps=[
        Step("That sideways push is called the Magnus force.",
             pause=0.3, sfx=[("note", 0.3, {"n": 4})]),
        Step("It changes the ball's direction rather than its speed; drag can slow it down.",
             pause=0.7),
    ]),
    Scene(numbers, header="Test some numbers", steps=[
        Step("For this example, assume approximately constant forward speed and a constant transverse force, starting with no sideways velocity.",
             pause=0.3),
        Step("At {speed} meters per second, a plausible sideways force is about {force} newtons.",
             sub="At {speed} m/s, a plausible sideways force is about {force} N.",
             pause=0.4),
        Step("Over {time} seconds, that produces about {bend} meters of sideways deflection.",
             sub="Over {time} s, that produces about {bend} m of sideways deflection.",
             pause=0.9, sfx=[("chime", 2.7, {"n": 5})]),
    ]),
    Scene(outro, header=None, steps=[
        Step("Real pitches also depend on seams, drag, and gravity.",
             pause=0.2),
        Step("A curveball curves because spinning surfaces redirect air, and the air pushes back.",
             pause=0.5),
        Step("Follow for more physics like this.",
             pause=0.7, sfx=[("chime", 0.15, {"n": 3})]),
    ]),
]
