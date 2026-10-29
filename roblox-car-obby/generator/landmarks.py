"""One big set piece per level and the title gate at its start. Pure scenery: nothing collides."""
import math
import rbxl
from geom import CF, deck_frame, axis_frame, look_frame, rot_y, rot_axis, add, mul, unit, UP
from builder import mix, X0, Y0, ZC
from decor import P, ring_deco, spin_deco, spike, ballcluster, hsv

TAU = math.pi * 2


def sample_at(b, x):
    best = None
    for s in b.samples:
        if best is None or abs(s[0] - x) < abs(best[0] - x):
            best = s
    return best


def sign(b, part, face, lines, color):
    """A SurfaceGui with one TextLabel per (text, top, height) line on a part's face."""
    sg = b.fac.clone(b.tpl["surfacegui"], part)
    for c in list(sg.children):
        sg.children.remove(c)
        c.parent = None
    sg.set("Face", face)
    sg.set("Name", b"TitleSign")
    sg.set("LightInfluence", 0.0)
    sg.set("Brightness", 2.5)
    sg.set("PixelsPerStud", 20.0)
    for text, top, h in lines:
        tl = b.fac.clone(b.tpl["textlabel"], sg)
        tl.set("Text", text.encode())
        tl.set("Position", (0.04, 0, top, 0))
        tl.set("Size", (0.92, 0, h, 0))
        tl.set("TextColor3", tuple(c / 255.0 for c in color))
        tl.set("TextStrokeColor3", (0.0, 0.0, 0.0))
        tl.set("TextStrokeTransparency", 0.35)
        tl.set("TextScaled", True)


def title_gate(b, level_id, title):
    th = b.theme
    x, y, z = X0 + 75, Y0, ZC
    span = 168
    for s in (-1, 1):
        P(b, "GatePillar", CF((x, y + 12, z + s * span / 2)), (10, 92, 10), th["metal"], "Metal")
        P(b, "GatePillarGlow", CF((x, y + 12, z + s * (span / 2 - 5.2))), (10.4, 92, 0.6), th["edge"], "Neon")
    beam = P(b, "GateBoard", look_frame((x, y + 50, z), (-1, 0, 0)), (span + 10, 30, 4), th["deco"], "SmoothPlastic")
    P(b, "GateTrim", CF((x, y + 65.5, z)), (5, 1.4, span + 12), th["edge"], "Neon")
    P(b, "GateTrim", CF((x, y + 34.5, z)), (5, 1.4, span + 12), th["edge"], "Neon")
    sign(b, beam, 5, [(getattr(b, "gate_label", "LEVEL %d" % level_id), 0.06, 0.3), (title.upper(), 0.36, 0.58)], th["accent"])
    sign(b, beam, 2, [(title.upper(), 0.2, 0.6)], th["edge"])


# ------------------------------------------------------------------ the set pieces
def lm_megaring(b, s, rng):
    th = b.theme
    c = (s[0], s[1] + 20, s[2])
    r = max(90, s[3] / 2 + 60)

    def build(rig):
        ring_deco(b, c, r, th["edge"], axis=(1, 0, 0), n=36, th=6, parent=rig)
        for k in range(8):
            a = TAU * k / 8
            d = (0, math.cos(a), math.sin(a))
            P(b, "RingFin", deck_frame(add(c, mul(d, r + 9)), d, up=(1, 0, 0)), (3, 14, 18), th["accent"], "Neon", parent=rig)
    spin_deco(b, c, (1, 0, 0), 0.08, build)
    ring_deco(b, c, r + 22, th["accent"], axis=(1, 0, 0), n=40, th=2.4)


def lm_cone(b, s, rng, glow=None):
    th = b.theme
    side = rng.choice([-1, 1])
    base = (s[0] + 60, s[1] - 520, s[2] + side * 430)
    h, r = 760, 300
    n = 9
    for k in range(n):
        rr = r * (1 - k / n * 0.78)
        P(b, "ConeTier", axis_frame(add(base, (0, k * h / n + h / (2 * n), 0)), UP), (h / n + 1, rr * 2, rr * 2),
          mix(th["deco"], (0, 0, 0), 0.15 * (k % 2)), th.get("rock_mat", "Slate"), shape=2)
    top = add(base, (0, h, 0))
    P(b, "ConeGlow", axis_frame(add(top, (0, 2, 0)), UP), (4, r * 0.4, r * 0.4), glow or th["edge"], "Neon", shape=2)
    for k in range(10):
        a = rng.random() * TAU
        p = add(top, (math.cos(a) * rng.uniform(0, 50), rng.uniform(20, 160), math.sin(a) * rng.uniform(0, 50)))
        P(b, "Plume", CF(p), (rng.uniform(16, 40),) * 3, glow or th["edge"], "Neon", shape=0, transp=0.35)


def lm_spire(b, s, rng):
    th = b.theme
    side = rng.choice([-1, 1])
    base = (s[0], s[1] - 400, s[2] + side * 300)
    for k in range(9):
        spike(b, add(base, (rng.uniform(-60, 60), 0, rng.uniform(-60, 60))), rng.uniform(300, 640), rng.uniform(30, 60),
              rng.choice([th["edge"], th["accent"], th["deco"]]), rng.choice(["Glass", "Neon", "Glacier"]),
              rng.uniform(-0.25, 0.25), rng.random() * 6)


def lm_tree(b, s, rng, canopy=None, dead=False):
    th = b.theme
    side = rng.choice([-1, 1])
    base = (s[0], s[1] - 420, s[2] + side * 260)
    h = 620
    P(b, "MegaTrunk", axis_frame(add(base, (0, h / 2, 0)), UP), (h, 56, 56), (80, 56, 40), "Wood", shape=2)
    top = add(base, (0, h, 0))
    if dead:
        for k in range(7):
            a = TAU * k / 7 + rng.random()
            d = unit((math.cos(a), rng.uniform(0.2, 0.9), math.sin(a)))
            L = rng.uniform(120, 220)
            P(b, "MegaBranch", deck_frame(add(top, mul(d, L / 2)), d), (12, 12, L), (60, 50, 56), "Wood")
            P(b, "Wisp", CF(add(top, mul(d, L))), (14, 14, 14), th["edge"], "Neon", shape=0, transp=0.2)
    else:
        for k in range(9):
            off = (rng.uniform(-150, 150), rng.uniform(-40, 90), rng.uniform(-150, 150))
            rr = rng.uniform(70, 130)
            P(b, "MegaCanopy", CF(add(top, off)), (rr * 2,) * 3, canopy or th["deco"], "Grass" if not canopy else "SmoothPlastic",
              shape=0)
        for k in range(14):
            a = rng.random() * TAU
            p = add(top, (math.cos(a) * 170, rng.uniform(-80, 40), math.sin(a) * 170))
            P(b, "Firefly", CF(p), (5, 5, 5), th["accent"], "Neon", shape=0)


def lm_gate(b, s, rng):
    """A colossal gateway the road runs under."""
    th = b.theme
    x, y, z = s[0], s[1], s[2]
    span = s[3] + 160
    h = 210
    for side in (-1, 1):
        base = (x, y - 300, z + side * span / 2)
        P(b, "GateTower", CF(add(base, (0, (h + 300) / 2, 0))), (46, h + 300, 46), th["deco"], th.get("rock_mat", "Slate"))
        P(b, "GateTowerTop", CF(add(base, (0, h + 320, 0))), (54, 40, 54), th["accent2"], th.get("rock_mat", "Slate"),
          cls="WedgePart")
        for k in range(5):
            P(b, "GateLight", CF(add(base, (0, 330 + k * 34, -side * 23.5))), (20, 4, 1), th["edge"], "Neon")
    P(b, "GateSpan", CF((x, y + h, z)), (40, 34, span + 46), th["deco"], th.get("rock_mat", "Slate"))
    P(b, "GateSpanGlow", CF((x - 20.4, y + h, z)), (0.6, 8, span + 20), th["edge"], "Neon")
    P(b, "GateSpanGlow", CF((x + 20.4, y + h, z)), (0.6, 8, span + 20), th["edge"], "Neon")
    P(b, "GateGem", CF((x, y + h + 30, z)) * rot_axis((1, 0, 0), math.pi / 4), (22, 22, 22), th["accent"], "Neon")


def lm_pyramid(b, s, rng):
    th = b.theme
    side = rng.choice([-1, 1])
    base = (s[0] + 80, s[1] - 380, s[2] + side * 520)
    size = 720
    for i in range(12):
        sz = size * (1 - i / 12)
        P(b, "MegaStep", CF(add(base, (0, i * size / 24 + size / 48, 0))), (sz, size / 24, sz),
          mix(th["deco"], (255, 255, 255), 0.08 * (i % 2)), th.get("rock_mat", "Sandstone"))
    P(b, "Capstone", CF(add(base, (0, size / 2 + 20, 0))), (40, 40, 40), th["edge"], "Neon")
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        P(b, "Beam", CF(add(base, (0, size / 2 + 250, 0))) * rot_y(a) * rot_axis((1, 0, 0), 0.25), (6, 500, 6),
          th["accent"], "Neon", transp=0.4)


def lm_beacon(b, s, rng):
    """A lighthouse / tesla tower with stacked light rings."""
    th = b.theme
    side = rng.choice([-1, 1])
    base = (s[0], s[1] - 360, s[2] + side * 240)
    h = 560
    P(b, "BeaconShaft", axis_frame(add(base, (0, h / 2, 0)), UP), (h, 50, 50), th["metal"], "Metal", shape=2)
    for k in range(7):
        c = add(base, (0, 120 + k * 64, 0))
        ring_deco(b, c, 38, th["edge"] if k % 2 else th["accent"], axis=(0, 1, 0), n=18, th=4)
    top = add(base, (0, h + 20, 0))
    P(b, "BeaconHead", CF(top), (60, 60, 60), th["accent"], "Neon", shape=0, transp=0.15)

    def build(rig):
        for k in range(2):
            a = math.pi * k
            d = (math.cos(a), 0, math.sin(a))
            P(b, "BeaconRay", deck_frame(add(top, mul(d, 180)), d), (6, 6, 300), th["edge"], "Neon", parent=rig, transp=0.45)
    spin_deco(b, top, UP, 0.12, build)


def lm_donut(b, s, rng):
    th = b.theme
    side = rng.choice([-1, 1])
    c = (s[0], s[1] + 120, s[2] + side * 330)
    for k in range(5):
        ring_deco(b, c, 150 + k * 9, hsv(k / 5.0, 0.55, 1.0), axis=(0, 0, 1), n=40, th=12)
    for k in range(30):
        a = rng.random() * TAU
        p = add(c, (math.cos(a) * 168, math.sin(a) * 168, rng.uniform(-14, 14)))
        P(b, "Sprinkle", CF(p) * rot_axis((1, 1, 0), rng.random() * 3), (2, 2, 10), hsv(rng.random(), 0.7, 1), "Neon")


def lm_planet(b, s, rng):
    th = b.theme
    side = rng.choice([-1, 1])
    c = (s[0] + 200, s[1] + 250, s[2] + side * 900)
    r = 380
    P(b, "GiantPlanet", CF(c), (r * 2,) * 3, th["accent2"], "SmoothPlastic", shape=0)
    for k in range(3):
        ring_deco(b, c, r * (1.35 + 0.12 * k), th["edge"] if k != 1 else th["accent"], axis=unit((0.25, 1, 0.15)), n=48, th=10)


LANDMARKS = {
    "neon_city": lm_megaring, "candy": lm_donut, "volcano": lambda b, s, r: lm_cone(b, s, r, (255, 110, 20)),
    "glacier": lm_spire, "jungle": lm_tree, "desert": lm_pyramid, "space": lm_planet, "synthwave": lm_megaring,
    "ocean": lm_beacon, "haunted": lambda b, s, r: lm_tree(b, s, r, dead=True), "golden": lm_pyramid,
    "factory": lm_beacon, "cloud": lm_gate, "crystal": lm_spire, "aurora": lm_spire,
    "toxic": lambda b, s, r: lm_cone(b, s, r, (150, 255, 0)), "sakura": lambda b, s, r: lm_tree(b, s, r, (255, 170, 210)),
    "arcade": lm_megaring, "storm": lm_beacon, "sunset": lm_gate, "deepsea": lm_beacon,
    "mars": lambda b, s, r: lm_cone(b, s, r, (255, 150, 60)), "royal": lm_gate, "matrix": lm_megaring, "rainbow": lm_donut,
}
# the other three visits to a world get a different set piece
ALT = [lm_gate, lm_planet, lm_megaring, lm_spire, lm_beacon, lm_donut]


def landmark(b, theme_key, variant, rng):
    xs = sorted(s[0] for s in b.samples)
    x = X0 + b.L * rng.uniform(0.42, 0.58)
    s = sample_at(b, x)
    fn = LANDMARKS[theme_key] if variant == 0 else ALT[(sum(map(ord, theme_key)) + variant) % len(ALT)]
    fn(b, s, rng)
    # and a second, smaller echo near the end on the other worlds' visits
    if variant >= 2:
        s2 = sample_at(b, X0 + b.L * 0.82)
        lm_megaring(b, s2, rng)
