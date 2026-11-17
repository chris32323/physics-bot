from engine.style import *

TOPIC = "Why Steel Ships Float"
TITLE = "How can a huge steel ship float? #physics #shorts"
DESCRIPTION = (
    "Steel is denser than water, but a hollow ship can still float. "
    "Watch water pressure, displaced water, and cargo explain Archimedes' principle."
)
TAGS = ["physics", "buoyancy", "Archimedes", "ships", "density", "science"]

# A simplified rectangular, watertight barge in fresh water.
RHO = 1000.0
G = 9.81
MASS = 1_000_000.0
CARGO = 250_000.0
LENGTH = 50.0
BEAM = 10.0
HULL_DEPTH = 5.0

VOLUME = MASS / RHO
LOADED_VOLUME = (MASS + CARGO) / RHO
DRAFT = VOLUME / (LENGTH * BEAM)
LOADED_DRAFT = LOADED_VOLUME / (LENGTH * BEAM)
BUOYANCY = RHO * G * VOLUME

FACTS = {
    "mass": f"{MASS / 1000:.0f}",
    "volume": f"{VOLUME:.0f}",
    "mass_label": f"{MASS / 1000:,.0f}",
    "volume_label": f"{VOLUME:,.0f}",
    "loaded_mass": f"{(MASS + CARGO) / 1000:,.0f}",
    "loaded_volume": f"{LOADED_VOLUME:,.0f}",
    "draft": f"{DRAFT:.1f}",
    "loaded_draft": f"{LOADED_DRAFT:.1f}",
    "force": f"{BUOYANCY / 1e6:.2f}",
}


def water(c, level, bottom=650):
    c.rect(80, bottom, 880, level - bottom, BLUE, 0.13)
    c.line([80, 960], [level, level], BLUE, lw=4, alpha=0.85)


def hull(c, x, bottom, width, height, air_alpha=1.0,
         displaced=0.0, waterline=None, flood=0.0):
    """Open-looking cutaway; yellow hatching marks excluded water, not flooding."""
    top = bottom + height
    left, right = x - width / 2, x + width / 2

    # Keep the watertight interior dry and dark.
    c.polygon(
        [(left, bottom), (right, bottom), (right, top), (left, top)],
        BG, 1.0
    )

    if displaced > 0 and waterline is not None:
        wet_height = max(0, min(height - 10, waterline - bottom - 8))
        inner_width = width - 16

        # Clip sparse diagonal hatch marks to the excluded-water region.
        # Unlike actual flooding, this diagram overlay has no blue fill.
        for offset in np.arange(-wet_height, inner_width, 36.0):
            start = max(0.0, -offset)
            end = min(wet_height, inner_width - offset)
            if end > start:
                c.line(
                    [left + 8 + offset + start, left + 8 + offset + end],
                    [bottom + 8 + start, bottom + 8 + end],
                    YELLOW, lw=2, alpha=0.4 * displaced
                )

        c.text(
            x, bottom + 8 + wet_height / 2,
            "Water excluded by hull",
            size=26, color=YELLOW, alpha=displaced, box=True
        )

    # Solid blue inside the hull is reserved for actual flooding.
    if flood > 0:
        wet_height = (height - 24) * flood
        c.rect(left + 12, bottom + 12, width - 24, wet_height, BLUE, 0.65)
        c.line([left + 12, right - 12],
               [bottom + 12 + wet_height] * 2, BLUE, lw=3)

    c.line(
        [left, left, right, right],
        [top, bottom, bottom, top],
        PINK, lw=9, glow=True
    )
    c.line([left, right], [top, top], PINK, lw=4, alpha=0.7)

    # Remove the label completely before rising floodwater reaches it.
    c.text(x, bottom + height * 0.62, "AIR", size=34,
           color=MUTED, alpha=air_alpha * (1 - clamp(flood / 0.5)))

    # A small bridge makes the cutaway read immediately as a ship.
    cabin_x = right - width * 0.24
    cabin_y = top + 34
    c.panel(cabin_x, cabin_y, width * 0.22, 68,
            edge=PINK, fill=PANEL, radius=8, lw=3)
    c.line([cabin_x - 22, cabin_x + 22], [cabin_y + 6] * 2,
           BLUE, lw=6)


# ---------------------------------------------------------------- 1: first-frame contrast
def hook(c):
    c.heading(520, 1620, "HEAVY STEEL.\nSTILL FLOATING.", size=62)

    level = 1120
    water(c, level, bottom=760)

    # The floating hull is already present in the thumbnail.
    hull(c, 685, 1020, 420, 240)
    c.text(685, 1390, "Hollow hull", size=36, color=PINK)

    # Physical motion uses a constant video-time rate, then stops.
    elapsed = max(0.0, c.t - c.cue(1) - 0.15)
    drop = min(190.0, elapsed * 105.0)
    block_y = 1150 - drop
    c.panel(230, block_y, 130, 130, edge=PINK,
            fill=PANEL, radius=8, lw=5)
    c.text(230, 1390, "Solid steel", size=34, color=PINK)
    a = c.appear(1, 0.1, 0.4)
    c.arrow(230, block_y - 80, 230, block_y - 170,
            PINK, lw=6, alpha=a)

    c.text(540, 680, "Same material. Different average density.",
           size=32, alpha=c.appear(1, 0.8, 0.6))


# ---------------------------------------------------------------- 2: pressure and Archimedes
def pressure(c):
    level = 1230
    bottom = 1000
    top = 1370

    water(c, level, bottom=930)
    displaced = c.appear(2, 0.1, 0.7)
    hull(c, 540, bottom, 460, top - bottom,
         displaced=displaced, waterline=level)

    c.text(540, 1515, "Deeper water → higher pressure",
           size=36, color=BLUE, alpha=c.appear(0))

    # Opposing horizontal pressures cancel; arrows grow with depth.
    for i, depth in enumerate((45, 120, 195)):
        y = level - depth
        length = depth * 0.40
        a = c.appear(0, 0.2 + i * 0.4, 0.45)
        c.arrow(310 - length, y, 310, y, BLUE,
                lw=5, alpha=a, glow=False)
        c.arrow(770 + length, y, 770, y, BLUE,
                lw=5, alpha=a, glow=False)

    # Show underside pressure during the first sentence.
    up = c.appear(0, 0.1, 0.6)
    for x in (410, 540, 670):
        c.arrow(x, 865, x, 990, GREEN, lw=6, alpha=up)

    # Name the resulting upward force during the second sentence.
    c.text(540, 805, "Net upward force: buoyancy",
           size=35, color=GREEN, alpha=c.appear(1, 0.1, 0.6))

    c.panel(540, 665, 800, 130, edge=YELLOW,
            alpha=displaced, radius=24)
    c.text(540, 665, r"$F_B = \rho_{\mathrm{water}}\,g\,V_{\mathrm{displaced}}$",
           size=44, color=YELLOW, alpha=displaced)

    # A dashed guide bounds the hatched water volume excluded by the hull.
    c.line([320, 760], [level, level], YELLOW, lw=3,
           alpha=0.7 * displaced, dash=(5, 5))


# ---------------------------------------------------------------- 3: equilibrium and average density
def balance(c):
    level = 1160
    water(c, level, bottom=940)
    hull(c, 530, 1030, 470, 285)

    a = c.appear(0, 0.1, 0.6)
    c.heading(530, 1515, "BUOYANCY = WEIGHT", size=48, alpha=a)

    c.arrow(170, 1000, 170, 1330, GREEN, lw=8, alpha=a)
    c.text(170, 920, r"$F_B$", size=42, color=GREEN, alpha=a)

    c.arrow(885, 1330, 885, 1000, PINK, lw=8, alpha=a)
    c.text(885, 920, r"$mg$", size=42, color=PINK, alpha=a)

    b = c.appear(1, 0.15, 0.6)
    c.ring(530, 1205, 70, YELLOW, lw=3, alpha=b)
    c.text(530, 810, "Steel + air + cargo", size=36, alpha=b)
    c.text(530, 705, r"$\rho_{\mathrm{average}} < \rho_{\mathrm{water}}$",
           size=46, color=YELLOW, alpha=b)


# ---------------------------------------------------------------- 4: numerical test, loading, flooding
def test(c):
    level = 1190
    scale = 64.0

    loading = c.ramp(c.cue(1) + 0.2, c.cue(1) + 2.2)
    draft = lerp(DRAFT, LOADED_DRAFT, loading)

    # Once flooding begins, the cutaway fills and settles lower.
    flooding = c.ramp(c.cue(2) + 0.2, c.cue(2) + 2.3)
    bottom = level - draft * scale - flooding * 90
    height = HULL_DEPTH * scale
    top = bottom + height

    water(c, level, bottom=900)
    hull(c, 530, bottom, 600, height, flood=0.72 * flooding)

    c.text(530, 1540, "Fresh water · box-shaped hull",
           size=34, color=BLUE)

    # Cargo stays attached to the moving hull.
    cargo_a = c.appear(1, 0.0, 0.4)
    for x in (350, 445, 540):
        c.panel(x, top + 33, 78, 62, edge=YELLOW,
                fill=PANEL, radius=7, lw=3, alpha=cargo_a)

    # Values switch only after the corresponding physical motion finishes.
    # Remove these equilibrium readouts entirely before flooding starts.
    if c.t < c.cue(2):
        loaded = loading >= 0.999
        mass_text = FACTS["loaded_mass"] if loaded else FACTS["mass_label"]
        volume_text = FACTS["loaded_volume"] if loaded else FACTS["volume_label"]

        c.text(530, 835, "Total mass: " + mass_text + " tonnes",
               size=38, color=PINK)
        c.text(530, 745, "Water displaced: " + volume_text + " m³",
               size=38, color=BLUE)

    c.text(530, 635, "Flooding can exhaust reserve buoyancy",
           size=32, color=YELLOW, alpha=c.appear(2, 0.2, 0.6))


# ---------------------------------------------------------------- 5: takeaway
def outro(c):
    c.heading(530, 1610, "IT'S THE WATER\nYOU PUSH ASIDE.", size=60)

    level = 1180
    water(c, level, bottom=950)
    hull(c, 530, 1040, 540, 285,
         displaced=0.8, waterline=level)

    a = c.appear(0, 0.1, 0.7)
    c.text(530, 860, "Weight of displaced water", size=36,
           color=BLUE, alpha=a)
    c.text(530, 790, "=", size=42, color=YELLOW, alpha=a)
    c.text(530, 720, "Weight of the whole ship", size=36,
           color=PINK, alpha=a)

    follow = c.appear(1, 0.0, 0.5)
    c.panel(530, 615, 610, 78, fill=PINK, radius=39, alpha=follow)
    c.text(530, 615, "Follow for more physics", size=34,
           color=FG, weight="bold", alpha=follow)


SCENES = [
    Scene(hook, header=None, steps=[
        Step(
            "How can heavy steel float?",
            pause=0.25,
        ),
        Step(
            "Solid steel sinks, but a hollow hull makes room for air.",
            pause=0.5,
            sfx=[("whoosh", 0.15)],
        ),
    ]),
    Scene(pressure, header="Water pushes back", steps=[
        Step(
            "Water pushes harder on the bottom because pressure increases with depth.",
            pause=0.4,
        ),
        Step(
            "That pressure difference creates an upward force called buoyancy.",
            pause=0.35,
            sfx=[("note", 0.2, {"n": 2})],
        ),
        Step(
            "Archimedes says this force equals the weight of the water displaced.",
            pause=0.65,
            sfx=[("chime", 0.2, {"n": 4})],
        ),
    ]),
    Scene(balance, header="Find the balance", steps=[
        Step(
            "A floating ship settles until buoyancy balances its total weight, including cargo.",
            pause=0.45,
            sfx=[("note", 0.2, {"n": 3})],
        ),
        Step(
            "Air adds volume with little mass, lowering the ship's average density below water's.",
            pause=0.4,
        ),
    ]),
    Scene(test, header="Try the numbers", steps=[
        Step(
            "In fresh water, a {mass} tonne ship must displace {volume} cubic meters.",
            sub="In fresh water, a {mass_label}-tonne ship must displace {volume_label} m³.",
            pause=0.5,
            sfx=[("pop", 0.2)],
        ),
        Step(
            "Add cargo, and the hull sinks deeper, displacing more water.",
            pause=0.65,
            sfx=[("pop", 0.15, {"n": 2})],
        ),
        Step(
            "Flooding removes buoyant space, so the ship may sink.",
            pause=0.55,
        ),
    ]),
    Scene(outro, header=None, steps=[
        Step(
            "Floating means displaced water weighs as much as the entire ship.",
            pause=0.45,
        ),
        Step(
            "Follow for more physics like this.",
            pause=0.5,
            sfx=[("chime", 0.1, {"n": 4})],
        ),
    ]),
]
