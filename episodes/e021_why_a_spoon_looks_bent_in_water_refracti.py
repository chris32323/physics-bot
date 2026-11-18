from engine.style import *

TOPIC = "Refraction"
TITLE = "Why does a spoon look bent in water? #physics #shorts"
DESCRIPTION = (
    "The spoon stays straight, but light changes direction at the water surface. "
    "Follow the rays to see why the submerged part appears displaced."
)
TAGS = ["physics", "refraction", "light", "optics", "science", "everyday physics"]

# ---------------------------------------------------------------- physics
N_WATER = 4.0 / 3.0
N_AIR = 1.0
ANGLE_WATER = 30.0
ANGLE_NEARBY = 32.0

SURFACE = 1170.0
SOURCE_X, SOURCE_Y = 330.0, 870.0
DEPTH = SURFACE - SOURCE_Y
RAY_TOP = 1470.0


def refracted_angle(degrees):
    return math.degrees(
        math.asin(N_WATER * math.sin(math.radians(degrees)) / N_AIR)
    )


ANGLE_AIR = refracted_angle(ANGLE_WATER)

FACTS = {
    "water_angle": f"{ANGLE_WATER:.0f}",
    "air_angle": f"{ANGLE_AIR:.0f}",
    "n_water": f"{N_WATER:.2f}",
    "n_air": f"{N_AIR:.2f}",
}


def ray_geometry(degrees):
    theta_w = math.radians(degrees)
    theta_a = math.radians(refracted_angle(degrees))
    surface_x = SOURCE_X + DEPTH * math.tan(theta_w)
    slope = math.tan(theta_a)  # horizontal distance per vertical distance
    end_x = surface_x + (RAY_TOP - SURFACE) * slope
    return surface_x, slope, end_x


RAY_A = ray_geometry(ANGLE_WATER)
RAY_B = ray_geometry(ANGLE_NEARBY)

# Intersection of backward extensions of two nearby emergent rays.
APPARENT_DEPTH = (RAY_B[0] - RAY_A[0]) / (RAY_B[1] - RAY_A[1])
APPARENT_X = RAY_A[0] - RAY_A[1] * APPARENT_DEPTH
APPARENT_Y = SURFACE - APPARENT_DEPTH


# ---------------------------------------------------------------- shared drawing
def water(c):
    c.rect(100, 690, 850, SURFACE - 690, BLUE, 0.10)
    c.line([100, 950], [SURFACE, SURFACE], BLUE, lw=4, alpha=0.8)
    c.text(875, 1230, "AIR", size=28, color=MUTED)
    c.text(850, 1105, "WATER", size=28, color=BLUE)


def spoon(c, apparent=False, alpha=1.0, color=FG):
    c.line([SOURCE_X, SOURCE_X], [1450, SURFACE],
           color, lw=17, alpha=alpha)
    bx = APPARENT_X if apparent else SOURCE_X
    by = APPARENT_Y if apparent else SOURCE_Y
    c.line([SOURCE_X, bx], [SURFACE, by + 37],
           color, lw=17, alpha=alpha)
    c.panel(bx, by, 64, 108, edge=color, fill=color,
            radius=30, lw=3, alpha=alpha)


def ray_segment(c, x0, y0, x1, y1, progress, color, alpha=1.0):
    if progress > 0:
        c.arrow(x0, y0,
                lerp(x0, x1, progress), lerp(y0, y1, progress),
                color, lw=5, alpha=alpha, head=0.8)


def full_ray(c, geometry, progress=1.0, alpha=1.0):
    sx, slope, ex = geometry
    water_progress = clamp(progress * 2)
    air_progress = clamp(progress * 2 - 1)
    ray_segment(c, SOURCE_X, SOURCE_Y, sx, SURFACE,
                water_progress, YELLOW, alpha)
    ray_segment(c, sx, SURFACE, ex, RAY_TOP,
                air_progress, YELLOW, alpha)


def eye(c, alpha=1.0):
    x = (RAY_A[2] + RAY_B[2]) / 2
    y = RAY_TOP + 22
    u = np.linspace(0, math.pi, 32)
    c.line(x + 53 * np.cos(u), y + 27 * np.sin(u),
           FG, lw=3, alpha=alpha)
    c.line(x + 53 * np.cos(u), y - 27 * np.sin(u),
           FG, lw=3, alpha=alpha)
    c.ball(x, y, r=13, color=PINK, alpha=alpha)


# ---------------------------------------------------------------- 1 · hook
def hook(c):
    c.heading(520, 1665, "Why does water\nbend a spoon?", size=62)
    water(c)

    # The apparent kink is already visible in the thumbnail.
    spoon(c, apparent=True, color=PINK)
    reveal = c.appear(1, 0.2, 0.7)
    c.line([SOURCE_X, SOURCE_X], [SURFACE, SOURCE_Y],
           MUTED, lw=8, alpha=0.55 * reveal, dash=(5, 5))
    c.panel(SOURCE_X, SOURCE_Y, 64, 108,
            edge=MUTED, fill=PANEL, alpha=0.55 * reveal, radius=30)
    c.text(630, 825, "Still straight", size=36,
           color=FG, alpha=reveal)
    c.text(525, 630, "Flat surface • glass ignored", size=26,
           color=MUTED, alpha=reveal)


# ---------------------------------------------------------------- 2 · direction changes
def bending(c):
    water(c)
    c.ball(SOURCE_X, SOURCE_Y, r=19, color=PINK)

    sx, slope, ex = RAY_A
    a = c.appear(0, 0.2, 0.5)
    c.text(500, 1570, "Light slows down in water", size=38, alpha=a)

    # Two straight segments, each at a constant screen speed.
    start = c.cue(1) + 0.2
    in_end = start + 1.1
    out_end = in_end + 1.1
    p_in = c.lin(start, in_end)
    p_out = c.lin(in_end, out_end)
    ray_segment(c, SOURCE_X, SOURCE_Y, sx, SURFACE, p_in, YELLOW)
    ray_segment(c, sx, SURFACE, ex, RAY_TOP, p_out, YELLOW)

    if c.t >= start:
        if c.t < in_end:
            x = lerp(SOURCE_X, sx, p_in)
            y = lerp(SOURCE_Y, SURFACE, p_in)
        else:
            x = lerp(sx, ex, p_out)
            y = lerp(SURFACE, RAY_TOP, p_out)
        c.ball(x, y, r=12, color=YELLOW)

    normal = c.appear(1, 0.0, 0.5)
    c.line([sx, sx], [900, 1500], MUTED, lw=3,
           alpha=normal, dash=(5, 5))
    c.arc(sx, SURFACE, 120, 90 - ANGLE_AIR, 90,
          YELLOW, lw=4, alpha=c.appear(1, 1.4, 0.5))

    label = c.appear(2, 0.1, 0.5)
    c.text(sx - 28, 1455, "normal", size=30,
           color=MUTED, ha="right", alpha=label)
    c.line([sx, sx + 27, sx + 27],
           [SURFACE + 27, SURFACE + 27, SURFACE],
           MUTED, lw=2, alpha=label)
    c.text(520, 750, "Angles are measured from the normal",
           size=30, color=MUTED, alpha=label)


# ---------------------------------------------------------------- 3 · apparent position
def backward(c):
    water(c)
    spoon(c, alpha=0.25, color=MUTED)

    for geometry in (RAY_A, RAY_B):
        full_ray(c, geometry, alpha=0.85)
    eye(c)

    p = c.ramp(c.cue(0) + 0.4, c.cue(0) + 2.4)
    for sx, slope, ex in (RAY_A, RAY_B):
        c.line(
            [sx, lerp(sx, APPARENT_X, p)],
            [SURFACE, lerp(SURFACE, APPARENT_Y, p)],
            PINK, lw=4, alpha=0.85, dash=(4, 4)
        )

    c.text(520, 1585, "Trace the arriving rays backward",
           size=36, alpha=c.appear(0, 0.1))

    image = c.appear(1, 0.2, 0.7)
    spoon(c, apparent=True, alpha=image, color=PINK)
    c.ring(APPARENT_X, APPARENT_Y, 66, PINK, lw=3, alpha=image)
    c.text(690, 990, "Apparent position", size=32,
           color=PINK, alpha=image)
    c.text(680, 765, "Actual position", size=32,
           color=MUTED, alpha=image)
    c.line([600, SOURCE_X + 45], [820, SOURCE_Y],
           MUTED, lw=2, alpha=image)
    c.arrow(235, SOURCE_Y, 235, APPARENT_Y,
            PINK, lw=4, alpha=image, glow=False)
    c.text(520, 645, "The submerged image is displaced",
           size=32, color=PINK, alpha=image)


# ---------------------------------------------------------------- 4 · numerical test
def snell(c):
    water(c)
    sx, slope, ex = RAY_A
    full_ray(c, RAY_A, alpha=0.9)
    c.ball(SOURCE_X, SOURCE_Y, r=17, color=PINK)
    c.line([sx, sx], [900, 1500], MUTED, lw=3,
           alpha=0.7, dash=(5, 5))

    formula = c.appear(0, 0.1, 0.6)
    c.text(520, 1580,
           r"$n_{\mathrm{water}}\sin\theta_{\mathrm{water}}"
           r"=n_{\mathrm{air}}\sin\theta_{\mathrm{air}}$",
           size=39, alpha=formula)

    angles = c.appear(1, 0.1, 0.6)
    c.arc(sx, SURFACE, 110, 270 - ANGLE_WATER, 270,
          BLUE, lw=4, alpha=angles)
    c.arc(sx, SURFACE, 120, 90 - ANGLE_AIR, 90,
          YELLOW, lw=4, alpha=angles)
    c.text(425, 1020, FACTS["water_angle"] + "°",
           size=38, color=BLUE, alpha=angles)
    c.text(580, 1350, "≈ " + FACTS["air_angle"] + "°",
           size=38, color=YELLOW, alpha=angles)

    c.text(520, 770,
           "Water  n ≈ " + FACTS["n_water"] +
           "     Air  n ≈ " + FACTS["n_air"],
           size=32, color=FG, alpha=formula)
    c.text(520, 660, "Refractive index varies with color",
           size=29, color=MUTED, alpha=c.appear(2, 0.1))


# ---------------------------------------------------------------- 5 · takeaway
def outro(c):
    c.heading(520, 1660, "Straight spoon.\nBent light.", size=64)
    water(c)
    spoon(c, apparent=True, color=PINK)

    ghost = c.appear(0, 0.1, 0.7)
    c.line([SOURCE_X, SOURCE_X], [SURFACE, SOURCE_Y],
           MUTED, lw=8, alpha=0.5 * ghost, dash=(5, 5))
    c.panel(SOURCE_X, SOURCE_Y, 64, 108,
            edge=MUTED, fill=PANEL, alpha=0.5 * ghost, radius=30)

    follow = c.appear(1, 0.1, 0.5)
    c.panel(555, 720, 660, 112, edge=PINK, alpha=follow, radius=50)
    c.text(555, 720, "Follow for more physics",
           size=36, color=FG, weight="bold", alpha=follow)


# ---------------------------------------------------------------- narration
SCENES = [
    Scene(hook, header=None, steps=[
        Step(
            "Why does water bend a spoon?",
            pause=0.3,
        ),
        Step(
            "At a flat water surface, light changes direction, not the spoon.",
            pause=0.4,
            sfx=[("note", 0.3, {"n": 2})],
        ),
    ]),
    Scene(bending, header="At the surface", steps=[
        Step(
            "Light travels more slowly in water than in air.",
            pause=0.2,
        ),
        Step(
            "Leaving water at an angle, it bends away from the normal.",
            pause=0.7,
            sfx=[("whoosh", 0.2)],
        ),
        Step(
            "The normal is an imaginary line perpendicular to the surface.",
            pause=0.3,
        ),
    ]),
    Scene(backward, header="Your brain's shortcut", steps=[
        Step(
            "Your brain traces that arriving light backward in a straight line.",
            pause=0.8,
            sfx=[("whoosh", 0.4)],
        ),
        Step(
            "So the submerged part appears shifted upward, creating the kink.",
            pause=0.6,
            sfx=[("pop", 0.4, {"n": 4})],
        ),
    ]),
    Scene(snell, header="Test the angles", steps=[
        Step(
            "Snell's law connects the angles through each material's refractive index.",
            pause=0.3,
        ),
        Step(
            "From water to air, {water_angle} degrees becomes about {air_angle} degrees.",
            sub="From water to air, {water_angle}° becomes about {air_angle}°.",
            pause=0.8,
            sfx=[("chime", 0.4, {"n": 4})],
        ),
        Step(
            "These values are approximate, and vary slightly with the light's color.",
            pause=0.2,
        ),
    ]),
    Scene(outro, header=None, steps=[
        Step(
            "The spoon is straight; the light's path bends, changing where the spoon appears.",
            pause=0.4,
        ),
        Step(
            "Follow for more physics like this.",
            pause=0.7,
            sfx=[("chime", 0.15, {"n": 2})],
        ),
    ]),
]
