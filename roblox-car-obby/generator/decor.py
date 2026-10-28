"""Scenery around the course. Nothing here collides or can be queried: it is only to look at."""
import math
import colorsys
from geom import CF, deck_frame, axis_frame, rot_y, rot_axis, add, mul, unit, UP
from builder import mix, X0, ZC

TAU = math.pi * 2


def hsv(h, s=1.0, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def P(b, name, cf, size, color, mat="SmoothPlastic", transp=0.0, shape=1, cls="Part", parent=None):
    return b.part(name, cf, size, color, mat, parent=parent, collide=False, query=False, transp=transp, shape=shape,
                  cls=cls)


def course_points(b, every):
    """Road samples roughly every `every` studs along x."""
    pts, last = [], -1e9
    for s in sorted(b.samples, key=lambda s: s[0]):
        if s[0] - last >= every:
            pts.append(s)
            last = s[0]
    return pts


def side_spot(b, s, rng, near=90, far=380, dy=(-120, 80)):
    side = rng.choice([-1, 1])
    z = s[2] + side * (s[3] / 2 + rng.uniform(near, far))
    y = s[1] + rng.uniform(*dy)
    return (s[0] + rng.uniform(-40, 40), y, z)


def ygr(rng, a, b_):
    return rng.uniform(a, b_)


# ------------------------------------------------------------------ generic pieces
def tower(b, base, w, h, color, mat, glow=None, windows=False, rng=None, cap=None):
    """A block standing on `base` (bottom centre)."""
    c = add(base, (0, h / 2, 0))
    P(b, "Tower", CF(c), (w, h, w * rng.uniform(0.7, 1.2) if rng else w), color, mat)
    if windows and glow:
        n = int(h // 26)
        for k in range(n):
            if rng.random() < 0.6:
                P(b, "Window", CF(add(base, (0, 14 + k * 26, 0))), (w + 0.6, 2.2, w * 0.4), glow, "Neon")
    if cap:
        P(b, "TowerCap", CF(add(base, (0, h + 1, 0))), (w + 2, 2, w + 2), cap, "Neon")


def spike(b, base, h, r, color, mat, tilt, yaw):
    R = rot_y(yaw) * rot_axis((1, 0, 0), tilt)
    up = R.vec((0, 1, 0))
    c = add(base, mul(up, h / 2))
    cf = CF(c, R.x, R.y, R.z)
    P(b, "Spike", cf, (r, h, r), color, mat)
    tipc = add(base, mul(up, h + r * 0.4))
    P(b, "SpikeTip", CF(tipc, R.x, R.y, R.z), (r * 0.6, r * 0.8, r * 0.6), color, mat, cls="WedgePart")


def ballcluster(b, c, r, color, mat, n, rng, transp=0.0, spread=1.0):
    for k in range(n):
        off = (rng.uniform(-r, r) * 1.6 * spread, rng.uniform(-r * 0.3, r * 0.4), rng.uniform(-r, r) * spread)
        rr = r * rng.uniform(0.6, 1.1)
        P(b, "Puff", CF(add(c, off)), (rr * 2, rr * 2, rr * 2), color, mat, transp=transp, shape=0)


def tree(b, base, h, trunk, canopy, rng, style="blob", canopy_mat="Grass"):
    P(b, "Trunk", CF(add(base, (0, h / 2, 0))), (h * 0.12, h, h * 0.12), trunk, "Wood")
    top = add(base, (0, h, 0))
    if style == "blob":
        ballcluster(b, top, h * 0.32, canopy, canopy_mat, 3, rng)
    elif style == "layers":
        for k in range(3):
            s = h * (0.7 - 0.18 * k)
            P(b, "Leaves", CF(add(top, (0, -h * 0.25 + k * h * 0.17, 0))) * rot_y(rng.random()), (s, h * 0.15, s), canopy,
              canopy_mat)
    elif style == "palm":
        for k in range(6):
            a = TAU * k / 6 + rng.random() * 0.3
            d = (math.cos(a), -0.35, math.sin(a))
            P(b, "Frond", deck_frame(add(top, mul(d, h * 0.22)), d), (h * 0.12, 1.2, h * 0.45), canopy, canopy_mat)
    elif style == "dead":
        for k in range(4):
            a = TAU * k / 4 + rng.random()
            d = unit((math.cos(a), 0.8, math.sin(a)))
            P(b, "Branch", deck_frame(add(top, mul(d, h * 0.15)), d), (1.6, 1.6, h * 0.35), trunk, "Wood")
    elif style == "cactus":
        for s in (-1, 1):
            P(b, "CactusArm", CF(add(base, (s * h * 0.15, h * 0.65, 0))), (h * 0.1, h * 0.35, h * 0.1), canopy, canopy_mat)


def ring_deco(b, c, r, color, axis=(1, 0, 0), n=16, th=3.0, parent=None):
    ax = unit(axis)
    # two perpendicular vectors in the ring plane
    a1 = unit((ax[1], -ax[0], 0)) if abs(ax[2]) < 0.9 else (1, 0, 0)
    if abs(ax[0]) > 0.9:
        a1 = (0, 1, 0)
    a2 = unit((ax[1] * a1[2] - ax[2] * a1[1], ax[2] * a1[0] - ax[0] * a1[2], ax[0] * a1[1] - ax[1] * a1[0]))
    for i in range(n):
        t = TAU * i / n
        d = add(mul(a1, math.cos(t)), mul(a2, math.sin(t)))
        tang = add(mul(a1, -math.sin(t)), mul(a2, math.cos(t)))
        P(b, "Ring", deck_frame(add(c, mul(d, r)), tang, up=d), (th, th, TAU * r / n + th * 0.5), color, "Neon",
          parent=parent)


def spin_deco(b, c, axis, speed, build):
    root = b.prop_root("SpinDeco", parent=b.scenery)
    rig = b.rig(root, "Spin", axis_frame(c, axis), speed, 4, phase=b.rng.random())
    build(rig)


# ------------------------------------------------------------------ styles
def d_skyline(b, rng, th):
    for s in course_points(b, 150):
        for side in (-1, 1):
            if rng.random() < 0.7:
                z = s[2] + side * rng.uniform(170, 520)
                h = rng.uniform(140, 520)
                h = rng.uniform(260, 700)
                base = (s[0] + rng.uniform(-50, 50), s[1] - 520, z)
                tower(b, base, rng.uniform(40, 80), h, th["deco"], "Glass", th["edge"] if rng.random() < 0.5 else th["accent"],
                      True, rng, cap=th["accent"])


def d_arches(b, rng, th):
    for s in course_points(b, 420)[1:]:
        w = s[3] + 26
        h = 34
        x, y, z = s[:3]
        c = th["accent"]
        for side in (-1, 1):
            P(b, "ArchLeg", CF((x, y + h / 2, z + side * w / 2)), (4, h, 4), th["metal"], "Metal")
        top = P(b, "ArchTop", CF((x, y + h, z)), (4, 4, w + 4), c, "Neon")
        top.props["AttributesSerialize"] = (0x01, b"")


def d_floating_cubes(b, rng, th):
    for s in course_points(b, 110):
        if rng.random() < 0.8:
            p = side_spot(b, s, rng, 60, 300, (-80, 140))
            sz = rng.uniform(8, 34)
            cf = CF(p) * rot_axis(unit((rng.random(), rng.random(), rng.random())), rng.uniform(0, 3))
            color = rng.choice([th["accent"], th["edge"], th["deco"], th["accent2"]])
            P(b, "Cube", cf, (sz, sz, sz), color, rng.choice(["Neon", "Glass", "SmoothPlastic"]), transp=rng.choice([0, 0, 0.3]))


def d_lollipops(b, rng, th):
    for s in course_points(b, 170):
        p = side_spot(b, s, rng, 60, 260, (-160, -60))
        h = rng.uniform(70, 140)
        P(b, "Stick", CF(add(p, (0, h / 2, 0))), (3, h, 3), (255, 255, 255))
        cc = hsv(rng.random(), 0.45, 1.0)
        P(b, "Candy", axis_frame(add(p, (0, h + 14, 0)), (0, 0, 1)), (8, 34, 34), cc, "SmoothPlastic", shape=2)
        P(b, "Swirl", axis_frame(add(p, (0, h + 14, 0.2 + 4)), (0, 0, 1)), (1, 22, 22), (255, 255, 255), shape=2)


def d_clouds(b, rng, th):
    for s in course_points(b, 140):
        p = side_spot(b, s, rng, 20, 380, (-190, -70))
        ballcluster(b, p, rng.uniform(16, 30), (255, 255, 255), "SmoothPlastic", rng.randint(3, 5), rng, transp=0.15)


def d_lava_sea(b, rng, th):
    for s in course_points(b, 600):
        P(b, "LavaSea", CF((s[0] + 300, s[1] - 330, s[2])), (620, 4, 1400), th["lava"], "Neon")
        P(b, "Crust", CF((s[0] + 300, s[1] - 327, s[2] + rng.uniform(-400, 400))), (rng.uniform(100, 220), 4, rng.uniform(80, 200)),
          (40, 30, 28), "Basalt")


def d_rocks(b, rng, th):
    for s in course_points(b, 130):
        p = side_spot(b, s, rng, 50, 320, (-200, -40))
        sz = rng.uniform(16, 50)
        cf = CF(p) * rot_axis(unit((rng.random(), 1, rng.random())), rng.uniform(0, 3))
        P(b, "Rock", cf, (sz, sz * 0.7, sz * 0.9), mix(th["deco"], (0, 0, 0), rng.uniform(0, 0.3)), th.get("rock_mat", "Slate"))


def d_embers(b, rng, th):
    for s in course_points(b, 90):
        p = side_spot(b, s, rng, 10, 220, (-40, 120))
        P(b, "Ember", CF(p) * rot_axis((1, 1, 0), rng.random() * 3), (2, 2, 2), th["edge"], "Neon")


def d_ice_spikes(b, rng, th):
    for s in course_points(b, 120):
        base = side_spot(b, s, rng, 40, 300, (-260, -150))
        for k in range(rng.randint(2, 4)):
            spike(b, add(base, (rng.uniform(-20, 20), 0, rng.uniform(-20, 20))), rng.uniform(60, 160), rng.uniform(10, 20),
                  rng.choice([th["deco"], th["accent"], (255, 255, 255)]), rng.choice(["Glacier", "Ice", "Glass"]),
                  rng.uniform(-0.3, 0.3), rng.random() * 6)


def d_crystals(b, rng, th):
    for s in course_points(b, 120):
        base = side_spot(b, s, rng, 40, 280, (-240, -120))
        for k in range(rng.randint(3, 5)):
            spike(b, add(base, (rng.uniform(-18, 18), 0, rng.uniform(-18, 18))), rng.uniform(50, 140), rng.uniform(8, 18),
                  rng.choice([th["deco"], th["edge"], th["accent"]]), rng.choice(["Glass", "Neon", "Glass"]),
                  rng.uniform(-0.45, 0.45), rng.random() * 6)


def d_pillars(b, rng, th):
    for s in course_points(b, 230):
        x, y, z = s[0], s[1], s[2]
        h = rng.uniform(200, 320)
        P(b, "Pillar", CF((x, y - 8 - h / 2, z)), (14, h, 14), th["metal"] if th["key"] != "glacier" else th["deco"],
          th.get("keel_mat", "Concrete"))
        P(b, "PillarBand", CF((x, y - 40, z)), (15, 2, 15), th["edge"], "Neon")


def d_trees(b, rng, th, style="blob", trunk=(90, 64, 40), canopy=None, mat="Grass"):
    for s in course_points(b, 140):
        if rng.random() < 0.85:
            p = side_spot(b, s, rng, 50, 260, (-140, -40))
            # a little floating island under it
            P(b, "Islet", CF(add(p, (0, -6, 0))), (40, 12, 40), (90, 70, 50), "Ground" if False else "Slate")
            P(b, "IsletTop", CF(add(p, (0, 0.5, 0))), (40, 1, 40), th.get("grass", (80, 140, 60)), "Grass")
            tree(b, p, rng.uniform(40, 70), trunk, canopy or th["deco"], rng, style, mat)


def d_vines(b, rng, th):
    for s in course_points(b, 160):
        p = side_spot(b, s, rng, 30, 160, (20, 90))
        L = rng.uniform(60, 140)
        P(b, "Vine", CF(add(p, (0, -L / 2, 0))), (1.2, L, 1.2), (60, 120, 40), "Grass")
        P(b, "Flower", CF(add(p, (0, -L, 0))), (5, 5, 5), th["accent"], "Neon", shape=0)


def d_mesas(b, rng, th):
    for s in course_points(b, 260):
        for side in (-1, 1):
            if rng.random() < 0.6:
                base = (s[0] + rng.uniform(-60, 60), s[1] - 320, s[2] + side * rng.uniform(200, 520))
                h = rng.uniform(220, 380)
                w = rng.uniform(80, 160)
                P(b, "Mesa", CF(add(base, (0, h / 2, 0))), (w, h, w * 0.8), th["deco"], "Sandstone")
                P(b, "MesaTop", CF(add(base, (0, h + 4, 0))), (w * 1.1, 8, w * 0.9), mix(th["deco"], (255, 255, 255), 0.2), "Sandstone")


def d_cacti(b, rng, th):
    d_trees(b, rng, th, style="cactus", trunk=(70, 130, 60), canopy=(70, 130, 60), mat="Grass")


def d_planets(b, rng, th):
    for k in range(3):
        x = X0 + rng.uniform(300, 5200)
        side = rng.choice([-1, 1])
        r = rng.uniform(120, 300)
        c = (x, 1120 + rng.uniform(80, 420), ZC + side * rng.uniform(900, 1500))
        col = hsv(rng.random(), 0.5, 0.9)
        P(b, "Planet", CF(c), (r * 2, r * 2, r * 2), col, rng.choice(["SmoothPlastic", "Slate", "Sand"]), shape=0)
        if rng.random() < 0.6:
            ring_deco(b, c, r * 1.5, th["accent"], axis=unit((rng.uniform(-0.3, 0.3), 1, rng.uniform(-0.3, 0.3))), n=28, th=6)


def d_stars(b, rng, th):
    for s in course_points(b, 60):
        p = side_spot(b, s, rng, 120, 700, (60, 400))
        sz = rng.uniform(1.5, 4)
        P(b, "Star", CF(p) * rot_axis((0, 1, 1), rng.random() * 3), (sz, sz, sz), (255, 255, 255), "Neon")


def d_trusses(b, rng, th):
    for s in course_points(b, 200):
        x, y, z = s[0], s[1], s[2]
        for side in (-1, 1):
            P(b, "Truss", CF((x, y - 10, z + side * (s[3] / 2 + 14))), (6, 6, 22), th["metal"], "DiamondPlate")
        P(b, "Strut", CF((x, y - 90, z)), (8, 160, 8), th["metal"], "Metal")
        P(b, "Beacon", CF((x, y - 10, z + (s[3] / 2 + 24))), (3, 3, 3), th["danger"], "Neon", shape=0)


def d_grid_floor(b, rng, th):
    for s in course_points(b, 640):
        y = s[1] - 280
        P(b, "GridFloor", CF((s[0] + 320, y - 2, ZC)), (640, 2, 1600), (5, 0, 15) if th["key"] != "matrix" else (0, 8, 2))
        for k in range(8):
            P(b, "GridLine", CF((s[0] + k * 80, y, ZC)), (1.6, 1, 1600), th["edge"], "Neon")
        for k in range(-10, 11):
            P(b, "GridLine", CF((s[0] + 320, y, ZC + k * 80)), (640, 1, 1.6), th["edge"], "Neon")


def d_sun_disc(b, rng, th):
    c = (X0 + 2900, 1300, ZC + 2600)
    for k in range(9):
        y = c[1] - 320 + k * 70
        half = math.sqrt(max(0, 400 ** 2 - (y - c[1]) ** 2))
        colr = mix((255, 60, 160), (255, 210, 60), k / 8)
        P(b, "SunBand", CF((c[0], y, c[2])), (half * 2, 50, 4), colr, "Neon")


def d_palms(b, rng, th):
    d_trees(b, rng, th, style="palm", trunk=(120, 90, 60), canopy=th["accent"] if th["key"] == "synthwave" else (60, 160, 70),
            mat="Neon" if th["key"] == "synthwave" else "Grass")


def d_water(b, rng, th):
    for s in course_points(b, 700):
        P(b, "Sea", CF((s[0] + 350, s[1] - 300, ZC)), (700, 2, 2400), (40, 150, 200), "Glass", transp=0.15)


def d_buoys(b, rng, th):
    for s in course_points(b, 160):
        p = side_spot(b, s, rng, 60, 300, (-300, -300))
        P(b, "Buoy", CF(add(p, (0, 6, 0))), (10, 14, 10), rng.choice([(255, 80, 60), (255, 255, 255), (255, 200, 40)]),
          "SmoothPlastic", shape=0)
        P(b, "BuoyLight", CF(add(p, (0, 15, 0))), (3, 3, 3), th["edge"], "Neon", shape=0)


def d_dead_trees(b, rng, th):
    d_trees(b, rng, th, style="dead", trunk=(50, 42, 46), canopy=(50, 42, 46), mat="Wood")


def d_tombstones(b, rng, th):
    for s in course_points(b, 120):
        p = side_spot(b, s, rng, 40, 220, (-90, -30))
        P(b, "Grave", CF(add(p, (0, 8, 0))) * rot_y(rng.uniform(-0.4, 0.4)), (10, 16, 3), (110, 110, 120), "Slate")
        P(b, "Wisp", CF(add(p, (0, 24, 0))), (3, 3, 3), th["edge"], "Neon", shape=0, transp=0.2)


def d_fog_orbs(b, rng, th):
    for s in course_points(b, 110):
        p = side_spot(b, s, rng, 30, 260, (-60, 120))
        r = rng.uniform(3, 8)
        P(b, "Orb", CF(p), (r, r, r), th["accent"], "Neon", shape=0, transp=0.3)


def d_columns(b, rng, th):
    for s in course_points(b, 170):
        for side in (-1, 1):
            if rng.random() < 0.65:
                base = (s[0] + rng.uniform(-30, 30), s[1] - 200, s[2] + side * rng.uniform(80, 220))
                h = rng.uniform(220, 300)
                P(b, "Column", axis_frame(add(base, (0, h / 2, 0)), UP), (h, 16, 16), th["deco"], "Marble", shape=2)
                P(b, "Capital", CF(add(base, (0, h + 2, 0))), (22, 4, 22), th["edge"], "Metal")


def d_pyramids(b, rng, th):
    for k in range(6):
        x = X0 + rng.uniform(200, 5300)
        side = rng.choice([-1, 1])
        base = (x, 820, ZC + side * rng.uniform(600, 1100))
        size = rng.uniform(200, 420)
        for i in range(6):
            s = size * (1 - i / 6)
            P(b, "PyramidStep", CF(add(base, (0, i * size / 12 + size / 24, 0))), (s, size / 12, s), th["deco"], "Sandstone")
        P(b, "PyramidTop", CF(add(base, (0, size / 2 + 6, 0))), (12, 12, 12), th["edge"], "Neon")


def d_girders(b, rng, th):
    for s in course_points(b, 180):
        x, y, z = s[0], s[1], s[2]
        h = rng.uniform(80, 140)
        for side in (-1, 1):
            P(b, "Girder", CF((x, y + h / 2 - 60, z + side * (s[3] / 2 + 20))), (6, h + 60, 6), (180, 140, 30), "Metal")
        P(b, "GirderTop", CF((x, y + h - 30, z)), (6, 6, s[3] + 46), (180, 140, 30), "Metal")
        P(b, "HazardLamp", CF((x, y + h - 26, z)), (4, 2, 4), th["accent"], "Neon")


def d_pipes(b, rng, th):
    for s in course_points(b, 300):
        side = rng.choice([-1, 1])
        z = s[2] + side * rng.uniform(70, 160)
        y = s[1] - rng.uniform(30, 120)
        P(b, "Pipe", axis_frame((s[0] + 150, y, z), (1, 0, 0)), (300, 10, 10), th["metal"], "Metal", shape=2)
        P(b, "PipeJoint", axis_frame((s[0] + 150, y, z), (1, 0, 0)), (6, 13, 13), th["accent"], "Metal", shape=2)


def d_smokestacks(b, rng, th):
    for s in course_points(b, 500):
        base = (s[0], s[1] - 300, s[2] + rng.choice([-1, 1]) * rng.uniform(250, 450))
        h = rng.uniform(300, 460)
        P(b, "Stack", axis_frame(add(base, (0, h / 2, 0)), UP), (h, 30, 30), (110, 60, 50), "Brick", shape=2)
        P(b, "StackBand", axis_frame(add(base, (0, h - 20, 0)), UP), (8, 32, 32), th["edge"], "Neon", shape=2)


def d_rainbow_arcs(b, rng, th):
    for s in course_points(b, 1200)[1:]:
        c = (s[0], s[1] - 60, s[2] + rng.choice([-1, 1]) * 260)
        for k in range(6):
            ring_deco(b, c, 120 + k * 6, hsv(k / 6.5, 0.8, 1), axis=(1, 0, 0), n=20, th=5)


def d_aurora(b, rng, th):
    for s in course_points(b, 90):
        for side in (-1, 1):
            z = s[2] + side * rng.uniform(350, 600)
            h = rng.uniform(80, 200)
            col = mix(th["edge"], th["accent"], rng.random())
            P(b, "Aurora", CF((s[0], s[1] + 220 + rng.uniform(-40, 40), z)), (60, h, 2), col, "Neon", transp=0.55)


def d_barrels(b, rng, th):
    for s in course_points(b, 120):
        p = side_spot(b, s, rng, 40, 220, (-120, -40))
        P(b, "Barrel", axis_frame(add(p, (0, 7, 0)), UP), (14, 10, 10), (220, 200, 0), "Metal", shape=2)
        P(b, "Goo", axis_frame(add(p, (0, 14.2, 0)), UP), (0.6, 8, 8), th["edge"], "Neon", shape=2)
        P(b, "Plate", CF(add(p, (0, -1, 0))), (30, 2, 30), th["deco"], "Concrete")


def d_sakura(b, rng, th):
    d_trees(b, rng, th, style="blob", trunk=(80, 50, 40), canopy=(255, 170, 210), mat="SmoothPlastic")


def d_lanterns(b, rng, th):
    for s in course_points(b, 110):
        for side in (-1, 1):
            p = (s[0], s[1], s[2] + side * (s[3] / 2 + 10))
            P(b, "LanternPost", CF(add(p, (0, -6, 0))), (2, 30, 2), (60, 30, 30), "Wood")
            P(b, "Lantern", CF(add(p, (0, 11, 0))), (5, 7, 5), (255, 90, 60), "Neon")


def d_petals(b, rng, th):
    for s in course_points(b, 60):
        p = side_spot(b, s, rng, 0, 200, (-20, 90))
        P(b, "Petal", CF(p) * rot_axis((1, 0.3, 0.6), rng.random() * 6), (2.5, 0.3, 1.6), (255, 190, 220), "SmoothPlastic")


def d_pixel_blocks(b, rng, th):
    for s in course_points(b, 100):
        p = side_spot(b, s, rng, 40, 300, (-100, 160))
        col = hsv(rng.random(), 0.9, 1)
        sz = rng.choice([8, 12, 16])
        for k in range(rng.randint(1, 4)):
            P(b, "Pixel", CF(add(p, (k * sz * rng.choice([0, 1]), k * sz * rng.choice([0, 1]), 0))), (sz, sz, sz), col, "Neon")


def d_storm_clouds(b, rng, th):
    for s in course_points(b, 140):
        p = side_spot(b, s, rng, 0, 400, (140, 260))
        ballcluster(b, p, rng.uniform(26, 44), (70, 74, 86), "SmoothPlastic", rng.randint(3, 5), rng, transp=0.1)


def d_bolts(b, rng, th):
    for s in course_points(b, 400):
        p = side_spot(b, s, rng, 200, 500, (150, 230))
        cur = p
        for k in range(5):
            nxt = add(cur, (rng.uniform(-25, 25), -rng.uniform(40, 70), rng.uniform(-25, 25)))
            P(b, "Bolt", deck_frame(((cur[0] + nxt[0]) / 2, (cur[1] + nxt[1]) / 2, (cur[2] + nxt[2]) / 2),
                                    (nxt[0] - cur[0], nxt[1] - cur[1], nxt[2] - cur[2])),
              (3, 3, math.dist(cur, nxt)), th["accent"], "Neon")
            cur = nxt


def d_billboards(b, rng, th):
    for s in course_points(b, 520)[1:]:
        side = rng.choice([-1, 1])
        p = (s[0], s[1], s[2] + side * (s[3] / 2 + 60))
        P(b, "BoardPost", CF(add(p, (0, -10, 0))), (4, 80, 4), th["metal"], "Metal")
        P(b, "Board", CF(add(p, (0, 40, 0))), (4, 30, 70), th["deco"], "SmoothPlastic")
        P(b, "BoardGlow", CF(add(p, (0, 40, 0))), (4.4, 26, 66), th["accent"], "Neon", transp=0.4)


def d_kelp(b, rng, th):
    for s in course_points(b, 80):
        p = side_spot(b, s, rng, 30, 240, (-260, -200))
        h = rng.uniform(100, 220)
        for k in range(5):
            P(b, "Kelp", CF(add(p, (math.sin(k) * 6, k * h / 5 + h / 10, math.cos(k * 1.3) * 6))), (4, h / 5 + 2, 2),
              (40, 140, 90), "Grass")


def d_bubbles(b, rng, th):
    for s in course_points(b, 50):
        p = side_spot(b, s, rng, 10, 250, (-100, 200))
        r = rng.uniform(2, 7)
        P(b, "Bubble", CF(p), (r, r, r), (200, 240, 255), "Glass", transp=0.5, shape=0)


def d_coral(b, rng, th):
    for s in course_points(b, 120):
        base = side_spot(b, s, rng, 40, 260, (-240, -160))
        col = rng.choice([th["accent"], (255, 140, 80), (255, 90, 160), th["edge"]])
        for k in range(rng.randint(3, 6)):
            spike(b, add(base, (rng.uniform(-14, 14), 0, rng.uniform(-14, 14))), rng.uniform(20, 60), rng.uniform(4, 8), col,
                  "SmoothPlastic", rng.uniform(-0.6, 0.6), rng.random() * 6)


def d_boulders(b, rng, th):
    for s in course_points(b, 110):
        p = side_spot(b, s, rng, 40, 380, (-200, -90))
        r = rng.uniform(14, 44)
        P(b, "Boulder", CF(p), (r * 2, r * 1.6, r * 2), mix(th["deco"], (0, 0, 0), rng.uniform(0, 0.3)), "Rock", shape=0)


def d_domes(b, rng, th):
    for k in range(5):
        x = X0 + rng.uniform(300, 5200)
        c = (x, 900, ZC + rng.choice([-1, 1]) * rng.uniform(400, 800))
        r = rng.uniform(60, 120)
        P(b, "Dome", CF(c), (r * 2, r * 2, r * 2), (200, 230, 255), "Glass", transp=0.4, shape=0)
        P(b, "DomeBase", axis_frame(add(c, (0, -4, 0)), UP), (8, r * 2.1, r * 2.1), th["metal"], "Metal", shape=2)


def d_castle_towers(b, rng, th):
    for s in course_points(b, 330):
        side = rng.choice([-1, 1])
        base = (s[0], s[1] - 260, s[2] + side * rng.uniform(150, 320))
        h = rng.uniform(260, 380)
        P(b, "Keep", axis_frame(add(base, (0, h / 2, 0)), UP), (h, 50, 50), th["deco"], "Cobblestone", shape=2)
        P(b, "Roof", CF(add(base, (0, h + 22, 0))), (54, 44, 54), th["danger"], "Slate", cls="WedgePart")
        P(b, "Flag", CF(add(base, (0, h + 60, 10))), (1, 14, 22), th["edge"], "Neon")


def d_banners(b, rng, th):
    for s in course_points(b, 130):
        for side in (-1, 1):
            p = (s[0], s[1], s[2] + side * (s[3] / 2 + 8))
            P(b, "BannerPole", CF(add(p, (0, 10, 0))), (2, 44, 2), th["metal"], "Metal")
            P(b, "Banner", CF(add(p, (0, 22, 0))), (0.6, 18, 10), th["accent2"] if side > 0 else th["road"], "Fabric")


def d_code_rain(b, rng, th):
    for s in course_points(b, 45):
        p = side_spot(b, s, rng, 60, 450, (-150, 250))
        L = rng.uniform(30, 120)
        P(b, "Code", CF(p), (1.5, L, 1.5), th["edge"], "Neon", transp=rng.uniform(0, 0.5))


def d_spin_rings(b, rng, th):
    for s in course_points(b, 700)[1:]:
        c = (s[0], s[1] + 10, s[2])
        r = s[3] / 2 + 26

        def build(rig, c=c, r=r):
            ring_deco(b, c, r, th["accent"], axis=(1, 0, 0), n=18, th=2.6, parent=rig)
        spin_deco(b, c, (1, 0, 0), 0.15 * rng.choice([-1, 1]), build)


STYLES = {
    "skyline": d_skyline, "arches": d_arches, "floating_cubes": d_floating_cubes, "lollipops": d_lollipops,
    "clouds": d_clouds, "lava_sea": d_lava_sea, "rocks": d_rocks, "embers": d_embers, "ice_spikes": d_ice_spikes,
    "pillars": d_pillars, "trees": lambda b, r, t: d_trees(b, r, t), "vines": d_vines, "mesas": d_mesas, "cacti": d_cacti,
    "planets": d_planets, "stars": d_stars, "trusses": d_trusses, "grid_floor": d_grid_floor, "sun_disc": d_sun_disc,
    "palms": d_palms, "water": d_water, "buoys": d_buoys, "dead_trees": d_dead_trees, "tombstones": d_tombstones,
    "fog_orbs": d_fog_orbs, "columns": d_columns, "pyramids": d_pyramids, "girders": d_girders, "pipes": d_pipes,
    "smokestacks": d_smokestacks, "rainbow_arcs": d_rainbow_arcs, "crystals": d_crystals, "aurora": d_aurora,
    "barrels": d_barrels, "sakura_trees": d_sakura, "lanterns": d_lanterns, "petals": d_petals,
    "pixel_blocks": d_pixel_blocks, "storm_clouds": d_storm_clouds, "bolts": d_bolts, "billboards": d_billboards,
    "kelp": d_kelp, "bubbles": d_bubbles, "coral": d_coral, "boulders": d_boulders, "domes": d_domes,
    "castle_towers": d_castle_towers, "banners": d_banners, "code_rain": d_code_rain, "spin_rings": d_spin_rings,
}
