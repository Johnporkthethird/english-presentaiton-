"""Set-piece stages: the things you land on are the objects themselves (rooftops, islands, boats, stars, a laser box,
piano keys, warp pipes, clouds), joined by the obby links (drop, kick, pad: obby.py) and big moments (a ring of fire,
a hexagon mega ramp, a rocky downhill).

Every surface is an invisible collider ("Floor") inside a boost model, so every car crosses it at the stage speed B
and every jump off it is the same jump; the object is drawn round it.
"""
import math
from geom import CF, deck_frame, axis_frame, look_frame, add, sub, mul, unit, cross, dot, rot_y, UP
from builder import G, CAR_UP, X0, Y0, ZC, mix
import route as RT
import journey as J
import rush2 as R2
import obby as O
import epic_marks as M
from skins import Pt, box, cyl, ball
from worlds import ell, ringz

TAU = math.pi * 2


def right_of(f):
    return mul(RT.left_of(f), -1)


# ===================================================================== the surface
def surface(o, label, L, w, look=None, dy=0.0, cp=False, boost=True, step=20.0, name="Floor", parent=None):
    """A drivable top L long and w wide from the turtle along its heading (rising dy, eased), carried by an invisible
    collider; look(b, pts, f, w) draws the object it is the top of. Returns the points."""
    r, b = o.r, o.b
    L = max(L, o.need, 60.0)
    o.need = 0.0
    f = r.f
    n = max(2, int(L / step))
    prof = J.ramp_profile(n, 0.25) if dy else None
    pts = []
    for i in range(n + 1):
        t = i / n
        p = add(r.p, mul(f, L * t))
        pts.append((p[0], r.p[1] + (dy * float(prof(t)) if dy else 0.0), p[2]))
    s0 = len(b.samples)
    if parent is None:
        parent = R2.boost_model(b, label.replace(" ", ""), o.B) if boost else b.roads
    # colliders: one slab per stretch that keeps its slope
    i = 0
    while i < n:
        j = i + 1
        d0 = unit(sub(pts[j], pts[i]))
        while j < n and dot(unit(sub(pts[j + 1], pts[j])), d0) > math.cos(math.radians(0.8)):
            j += 1
        a, c = pts[i], pts[j]
        fr = deck_frame(R2.lerp3(a, c, 0.5), sub(c, a))
        Ls = math.dist(a, c)
        Pt(b, name, CF(add(fr.p, mul(fr.y, -2.0)), fr.x, fr.y, fr.z), (w, 4, Ls), (128, 128, 128), "SmoothPlastic",
           parent, collide=True, transp=1.0)
        i = j
    n0 = len(b.path)
    for k, p in enumerate(pts):
        b.samples.append(p + (w,))
        b.line(*p)
    if o.trim:
        tgt, ff = o.trim
        b.path[n0:] = [p for p in b.path[n0:] if dot(sub(p[:3], tgt), ff) > 6]
        o.trim = None
    r.last = (pts, [w] * len(pts), None)
    r._seg(label, s0)
    if cp:
        q = add(pts[0], mul(f, 16.0))
        b.checkpoint(q[0], q[1], q[2], w, f, flag_side=o.came_from)
    o.came_from = 1
    r.p, r.w = pts[-1], w
    if look:
        look(b, pts, f, w)
    return pts


# ===================================================================== looks (drawn round a surface)
def look_roof(rng, ground, body=(120, 130, 150), glass=(140, 200, 255), roof=(70, 72, 80), lit=(255, 230, 150)):
    """A building whose flat roof is the surface: windows all the way down to the street, a parapet along the sides,
    an aircon unit and a water tower off the line."""
    def draw(b, pts, f, w):
        a, c = pts[0], pts[-1]
        mid = R2.lerp3(a, c, 0.5)
        L = math.dist(a, c)
        rt = right_of(f)
        H = mid[1] - ground
        W, D = w + 8, L + 8
        fr = deck_frame(mid, f)
        P = lambda name, p, size, col, mat="SmoothPlastic", **kw: Pt(b, name, CF(p, fr.x, fr.y, fr.z), size, col, mat,
                                                                      b.scenery, **kw)
        P("Building", add(mid, (0, -H / 2 - 0.5, 0)), (W, H - 1, D), body, "Concrete")
        P("RoofTop", add(mid, (0, -0.4, 0)), (W, 0.8, D), roof, "Slate")
        # window bands on all four faces
        k = 0
        y = mid[1] - 14
        while y > ground + 10:
            for s in (-1, 1):
                q = add((mid[0], y, mid[2]), mul(rt, s * (W / 2 + 0.1)))
                P("Windows", q, (0.3, 6, D - 8), lit if (k + s) % 3 == 0 else glass, "Neon" if (k + s) % 3 == 0 else "Glass")
            for s in (-1, 1):
                q = add((mid[0], y, mid[2]), mul(f, s * (D / 2 + 0.1)))
                P("Windows", q, (W - 8, 6, 0.3), glass, "Glass")
            y -= 14
            k += 1
        for s in (-1, 1):
            P("Parapet", add(mid, add(mul(rt, s * (W / 2 - 1)), (0, 1.2, 0))), (2, 2.4, D), body, "Concrete")
        # aircon and a water tower, out at the sides
        s = 1 if rng.random() < 0.5 else -1
        q = add(add(a, mul(f, L * rng.uniform(0.3, 0.7))), mul(rt, s * (W / 2 + 14)))
        box(b, "AirCon", add(q, (0, 4, 0)), (14, 8, 10), (180, 184, 190), "Metal", b.scenery, collide=True)
        if L > 140:
            q = add(add(a, mul(f, L * 0.8)), mul(rt, -s * (W / 2 + 18)))
            for dx in (-5, 5):
                for dz in (-5, 5):
                    cyl(b, "TowerLeg", add(q, (dx, 10, dz)), 20, 1.6, (90, 70, 50), "Wood", b.scenery)
            cyl(b, "WaterTower", add(q, (0, 28, 0)), 18, 18, (140, 100, 70), "Wood", b.scenery)
            M.wcone(b, "TowerCap", add(q, (0, 37, 0)), 8, 11, (90, 90, 96), "Metal", n=8)
    return draw


def look_island(rng, water_y, sand=(236, 214, 160), grass=(110, 190, 90), rock=(150, 130, 100), palms=True):
    """A sandy island poking out of the sea, palm trees and rocks round its edge."""
    def draw(b, pts, f, w):
        a, c = pts[0], pts[-1]
        L = math.dist(a, c)
        n = max(1, int(round(L / max(w, 60))))
        for k in range(n):
            q = R2.lerp3(a, c, (k + 0.5) / n)
            R = max(L / n, w) * 0.62
            h = q[1] - water_y
            cyl(b, "IslandSand", (q[0], q[1] - 1.5, q[2]), 3, 2 * R, sand, "Sand" if sand[2] < 200 else "Ice", b.scenery)
            cyl(b, "IslandRock", (q[0], q[1] - 3 - (h + 20) / 2, q[2]), h + 20, 2 * R * 0.9, rock, "Slate", b.scenery)
            cyl(b, "IslandShore", (q[0], water_y + 0.6, q[2]), 1.2, 2 * R * 1.25, (250, 240, 200), "Sand", b.scenery)
            for j in range(rng.randint(1, 3) if palms else 0):
                ang = rng.random() * TAU
                pp = (q[0] + math.cos(ang) * R * 0.85, q[1], q[2] + math.sin(ang) * R * 0.85)
                if abs(dot(sub(pp, q), right_of(f))) < w / 2 + 8:
                    continue
                palm(b, pp, rng.uniform(40, 60), rng)
    return draw


def palm(b, base, h, rng):
    x, y, z = base
    lean = rng.uniform(-0.25, 0.25)
    for k in range(6):
        t = (k + 0.5) / 6
        cyl(b, "PalmTrunk", (x + lean * h * t, y + h * t, z), h / 6 + 0.3, 4.4 - 1.6 * t, (150, 110, 70), "Wood", b.scenery)
    top = (x + lean * h, y + h, z)
    for k in range(7):
        a = TAU * k / 7
        d = (math.cos(a), -0.35, math.sin(a))
        q = add(top, mul(d, 11))
        Pt(b, "PalmLeaf", CF(q) * rot_y(-a) * CF((0, 0, 0)), (22, 1, 6), (60, 160, 70), "Grass", b.scenery)
    for k in range(3):
        ball(b, "Coconut", add(top, (math.cos(k * 2) * 2.5, -2.5, math.sin(k * 2) * 2.5)), 3, (110, 80, 50), "Wood",
             b.scenery)


def look_star(col=(255, 215, 70), glow=(255, 250, 200)):
    """A five-pointed star floating in the sky, one point straight ahead (the surface runs notch to tip)."""
    def draw(b, pts, f, w):
        pass  # (the star itself is the collider: see star_stage)
    return draw


def look_cloud(rng):
    def draw(b, pts, f, w):
        a, c = pts[0], pts[-1]
        L = math.dist(a, c)
        n = max(3, int(L / 26))
        rt = right_of(f)
        for k in range(n):
            q = R2.lerp3(a, c, (k + 0.5) / n)
            for s in (-1, 0, 1):
                d = rng.uniform(26, 40)
                p = add(add(q, mul(rt, s * w * 0.35)), (rng.uniform(-6, 6), -d * 0.32, rng.uniform(-6, 6)))
                ell(b, "Cloud", p, (d * 1.3, d * 0.7, d * 1.3), (250, 252, 255), "SmoothPlastic", b.scenery)
        ell(b, "CloudTop", add(R2.lerp3(a, c, 0.5), (0, -1.0, 0)), (w + 10, 2.4, L + 10), (255, 255, 255), "SmoothPlastic",
            b.scenery)
    return draw


def look_pipe(col=(40, 170, 70), rim=(70, 210, 100), ground=None):
    """A giant green warp pipe whose rim is the surface."""
    def draw(b, pts, f, w):
        a, c = pts[0], pts[-1]
        q = R2.lerp3(a, c, 0.5)
        L = math.dist(a, c)
        D = max(L, w) + 6
        g = ground if ground is not None else q[1] - 300
        cyl(b, "PipeBody", (q[0], (q[1] - 8 + g) / 2, q[2]), q[1] - 8 - g, D - 10, col, "SmoothPlastic", b.scenery)
        cyl(b, "PipeRim", (q[0], q[1] - 5, q[2]), 10, D + 4, rim, "SmoothPlastic", b.scenery)
        cyl(b, "PipeTop", (q[0], q[1] - 0.3, q[2]), 0.6, D, (30, 120, 50), "SmoothPlastic", b.scenery)
        cyl(b, "PipeHole", (q[0], q[1] - 0.1, q[2]), 0.4, D * 0.5, (10, 30, 14), "SmoothPlastic", b.scenery)
        for k in range(8):
            ang = TAU * k / 8
            cyl(b, "PipeShine", (q[0] + math.cos(ang) * (D / 2 - 4), (q[1] - 8 + g) / 2, q[2] + math.sin(ang) * (D / 2 - 4)),
                q[1] - 8 - g, 1.2, mix(col, (255, 255, 255), 0.3), "SmoothPlastic", b.scenery) if k == 1 else None
    return draw


def look_rock_slope(rng, col=(120, 110, 96), top=(110, 150, 80)):
    """A rocky hillside: a broad rough slope with boulders banked along both edges."""
    def draw(b, pts, f, w):
        rt = right_of(f)
        for i in range(len(pts) - 1):
            a, c = pts[i], pts[i + 1]
            fr = deck_frame(R2.lerp3(a, c, 0.5), sub(c, a))
            Ls = math.dist(a, c)
            Pt(b, "Hillside", CF(add(fr.p, mul(fr.y, -3.0)), fr.x, fr.y, fr.z), (w + 30, 6, Ls + 0.6), col, "Slate", b.scenery)
            Pt(b, "Grass", CF(add(fr.p, mul(fr.y, -0.05)), fr.x, fr.y, fr.z), (w, 0.2, Ls + 0.6), top,
               "Snow" if top[2] > 200 else "Grass",
               b.scenery)
            for s in (-1, 1):
                if rng.random() < 0.7:
                    d = rng.uniform(14, 26)
                    ell(b, "EdgeRock", add(add(fr.p, mul(rt, s * (w / 2 + 10 + d * 0.3))), (0, d * 0.25, 0)),
                        (d * 1.3, d, d * 1.1), mix(col, (60, 56, 50), rng.random() * 0.5), "Slate", b.scenery)
    return draw


def look_boat(rng, hull=(170, 60, 50), deck=(170, 130, 90), parent=None):
    """A boat: hull, bow and stern, deck planks, a mast with a sail off to one side."""
    def draw(b, pts, f, w):
        a, c = pts[0], pts[-1]
        L = math.dist(a, c)
        mid = R2.lerp3(a, c, 0.5)
        fr = deck_frame(mid, f)
        rt = right_of(f)
        par = parent or b.scenery
        P = lambda name, p, size, col, mat="SmoothPlastic", **kw: Pt(b, name, CF(p, fr.x, fr.y, fr.z), size, col, mat,
                                                                      par, **kw)
        P("Hull", add(mid, (0, -9, 0)), (w + 6, 16, L), hull, "Wood")
        P("Deckboards", add(mid, (0, -0.3, 0)), (w, 0.6, L), deck, "WoodPlanks")
        for s in (-1, 1):
            P("Gunwale", add(mid, add(mul(rt, s * (w / 2 + 2)), (0, 1.2, 0))), (2, 3, L), (240, 240, 230), "Wood")
        # bow: a wedge pointing forward, below deck height so the car drives off over it
        bow = add(c, add(mul(f, 14), (0, -9, 0)))
        Pt(b, "Bow", CF(bow, fr.x, fr.y, fr.z) * CF((0, 0, 0)), (w + 6, 16, 28), hull, "Wood", par, cls="WedgePart")
        P("Stern", add(a, add(mul(f, -4), (0, -7, 0))), (w + 6, 20, 8), mix(hull, (0, 0, 0), 0.2), "Wood")
        s = 1 if rng.random() < 0.5 else -1
        m = add(mid, mul(rt, s * (w / 2 + 6)))
        cyl(b, "Mast", add(m, (0, 26, 0)), 52, 2.4, (120, 90, 60), "Wood", par)
        P("Sail", add(m, add(mul(rt, s * 1.2), (0, 30, 0))), (0.4, 36, L * 0.4), (250, 250, 240), "Fabric")
        P("Flag", add(m, (0, 54, 0)), (0.3, 6, 10), (220, 40, 40), "Fabric")
        P("Waterline", add(mid, (0, -14, 0)), (w + 6.4, 2, L + 0.4), (240, 240, 230), "SmoothPlastic")
    return draw


def look_glass_floor(col=(30, 32, 40), grid=(90, 220, 255)):
    def draw(b, pts, f, w):
        a, c = pts[0], pts[-1]
        mid = R2.lerp3(a, c, 0.5)
        L = math.dist(a, c)
        fr = deck_frame(mid, f)
        Pt(b, "BoxFloor", CF(add(mid, (0, -1, 0)), fr.x, fr.y, fr.z), (w, 2, L), col, "SmoothPlastic", b.scenery)
        rt = right_of(f)
        for k in range(1, int(L // 20)):
            Pt(b, "GridLine", CF(add(add(a, mul(f, k * 20)), (0, 0.06, 0)), fr.x, fr.y, fr.z), (w, 0.1, 0.5), grid, "Neon",
               b.scenery)
        for k in range(1, int(w // 20)):
            Pt(b, "GridLine", CF(add(add(mid, mul(rt, -w / 2 + k * 20)), (0, 0.06, 0)), fr.x, fr.y, fr.z), (0.5, 0.1, L), grid,
               "Neon", b.scenery)
    return draw


# ===================================================================== stages
def water(b, c, size_x, size_z, y, col=(40, 120, 200), kind="Fall"):
    """The sea (or a lava lake): falling in is the end (FELL, or MELTED)."""
    Pt(b, "Sea", CF((c[0], y - 1, c[2])), (size_x, 2, size_z), col, "Glass" if kind == "Fall" else "Neon", b.scenery,
       transp=0.15 if kind == "Fall" else 0.0, refl=0.3 if kind == "Fall" else 0.0)
    b.part("SeaKill", CF((c[0], y - 6, c[2])), (size_x, 10, size_z), col, parent=b.hazards, transp=1, collide=False,
           query=True, attrs={"ObbyHazard": kind, "HazardKill": True})


def laser_box(o, label, L=280.0, W=110.0, wall=28.0, beams=3, period=1.4, cp=True):
    """A hollow box you fall into over its low back wall: glass sides, a doorway out the front, lasers sweeping
    across the floor on a beat (FRIED) in between."""
    b, r = o.b, o.r
    f = r.f
    rt = right_of(f)
    dropped_in = o.trim is not None  # (a jump lands in it: it gets its low back wall; driven into, it is open)
    pts = surface(o, label, L, W, look=look_glass_floor(), cp=cp)
    a, c = pts[0], pts[-1]
    mid = R2.lerp3(a, c, 0.5)
    fr = deck_frame(mid, f)
    Lb = math.dist(a, c)
    frame = (255, 60, 120)
    P = lambda name, p, size, col, mat="SmoothPlastic", **kw: Pt(b, name, CF(p, fr.x, fr.y, fr.z), size, col, mat,
                                                                  b.scenery, **kw)
    for s in (-1, 1):
        P("BoxWall", add(mid, add(mul(rt, s * (W / 2 + 1)), (0, wall / 2, 0))), (2, wall, Lb), (150, 200, 255), "Glass",
          transp=0.55, collide=True)
        P("BoxFrame", add(mid, add(mul(rt, s * (W / 2 + 1)), (0, wall + 0.6, 0))), (3, 1.2, Lb + 2), frame, "Neon")
    # the low back wall (the car drops in over it) and the front wall with a doorway
    if dropped_in:
        P("BoxBack", add(a, add(mul(f, -1), (0, 3, 0))), (W + 4, 6, 2), (150, 200, 255), "Glass", transp=0.55)
    door = W * 0.6
    for s in (-1, 1):
        q = add(c, add(mul(f, 1), add(mul(rt, s * (door / 2 + (W - door) / 4)), (0, wall / 2, 0))))
        P("BoxFront", q, ((W - door) / 2 + 2, wall, 2), (150, 200, 255), "Glass", transp=0.55, collide=True)
    P("DoorTop", add(c, add(mul(f, 1), (0, wall + 0.6, 0))), (W + 4, 1.2, 3), frame, "Neon")
    # lasers across the floor, flashing on a beat timed to the stage speed (a car at B through the first gap
    # clears them all)
    at = [Lb * (k + 1) / (beams + 1) for k in range(beams)]
    R2.beat_gates(r, at, o.B, period=period, on=period * 0.4)
    return pts


def fire_ring_kick(o, dy=0.0, side=0.0, R=26.0):
    """A kicker that throws the car through a ring of fire (MELTED if you clip it)."""
    b, r, B = o.b, o.r, o.B
    o.kick(dy, side=side, label="Fire Kick", deg=26.0)
    lip, top = None, None
    kind, lip, top, H, V = b.jumps[-1]
    f = RT.flat(sub(top, lip))
    # where the fastest and the slowest flights are closest in height, a little way out: the ring goes there
    best = None
    want = math.dist(lip, top) * 0.35
    for x in range(40, int(math.dist(lip, top) * 0.7), 4):
        tf = x / H
        ts = x / (H * O.SLOW)
        yf = V * tf - 0.5 * G * tf * tf
        ys = V * O.SLOW * ts - 0.5 * G * ts * ts
        if abs(yf - ys) < 2 * R - 22 and (best is None or abs(x - want) < abs(best[0] - want)):
            best = (x, (yf + ys) / 2)
    if best is None:
        return
    x, yc = best
    c = add(lip, add(mul(f, x), (0, yc + CAR_UP, 0)))
    t = x / H
    d = unit((f[0] * H, V - G * t, f[2] * H))
    fr = axis_frame(c, d)
    n = 22
    for k in range(n):
        a = TAU * k / n
        q = add(c, add(mul(fr.y, math.cos(a) * R), mul(fr.z, math.sin(a) * R)))
        ball(b, "FireRing", q, 9, (255, 120 + (k % 3) * 40, 30), "Neon", b.hazards, query=True,
             attrs={"ObbyHazard": "Burn"})
        ball(b, "FireGlow", add(q, mul(sub(q, c), 0.12)), 6, (255, 220, 120), "Neon", b.scenery, transp=0.3)
    ringz(b, c, R, (90, 60, 50), "Metal", th=2.5, axis=d, parent=b.scenery, name="RingFrame")


def star_stage(o, label, R=95.0, col=(255, 215, 70), cp=False):
    """A five-pointed star floating in the sky: you land on it and drive off its front point."""
    b, r = o.b, o.r
    f = r.f
    R = max(R, o.need / 1.4)
    L = R * 1.4
    # the star's centre: a third of the way along the drive (back notch to front tip)
    rt = right_of(f)
    c0 = add(r.p, mul(f, L - R))
    pts = surface(o, label, L, 30.0, cp=cp)
    m = b.model(label.replace(" ", ""), b.roads, {"BoostSpeed": float(o.B)})
    ri = R * 0.42
    tips, notches = [], []
    for k in range(5):
        a = TAU * k / 5
        d = add(mul(f, math.cos(a)), mul(rt, math.sin(a)))
        tips.append(add(c0, mul(d, R)))
        a2 = a + TAU / 10
        d2 = add(mul(f, math.cos(a2)), mul(rt, math.sin(a2)))
        notches.append(add(c0, mul(d2, ri)))
    below = add(c0, (0, -10, 0))
    glow = mix(col, (255, 255, 255), 0.5)
    for k in range(5):
        M.tri(b, "Star", tips[k], notches[k], c0, col, "SmoothPlastic", m, th=6.0, inward=below, collide=True)
        M.tri(b, "Star", tips[k], notches[k - 1], c0, mix(col, (255, 140, 0), 0.25), "SmoothPlastic", m, th=6.0,
              inward=below, collide=True)
        for (p, q) in ((tips[k], notches[k]), (tips[k], notches[k - 1])):
            dd = sub(q, p)
            Ld = math.sqrt(dot(dd, dd))
            Pt(b, "StarEdge", CF(add(R2.lerp3(p, q, 0.5), (0, 0.3, 0)), *_flat_axes(dd)), (1.2, 0.4, Ld), glow, "Neon",
               b.scenery)
    ball(b, "StarCore", add(c0, (0, -26, 0)), R * 0.22, mix(col, (255, 180, 40), 0.4), "Neon", b.scenery, transp=0.4)
    return pts


def _flat_axes(d):
    z = unit((d[0], 0.0, d[2]))
    x = (z[2], 0.0, -z[0])
    return (x, (0.0, 1.0, 0.0), z)


def hex_ramp(o, label, roll=300.0, drop=90.0, deg=26.0, w=60.0, land_drop=110.0, slope=12.0, gap_fn=None):
    """The hexagon mega ramp: a strip run down a half-hexagon channel that curves up into a big launch, a long
    landing runway below."""
    b, r = o.b, o.r
    f = r.f
    rt = right_of(f)
    r.w = w
    p0 = r.p
    R2.strips(r, label + " Run", roll, dy=-drop, w=w, every=45)
    pts_run = r.last[0]
    lip_before = r.p
    s0 = len(b.jumps)
    R2.ramp_jump(r, label, deg=deg, drop=land_drop, w_land=w + 20, slope=slope, land_min=240, gap_fn=gap_fn)
    # the channel: slanted hexagon walls along the run and the kicker
    kp = [j for j in b.jumps[s0:] if j[0] == "ramp"]
    lip = kp[0][1] if kp else lip_before
    path = list(pts_run) + [lip]
    col, edge = (60, 64, 80), (90, 220, 255)
    for i in range(0, len(path) - 1, 2):
        a, c = path[i], path[min(i + 2, len(path) - 1)]
        if math.dist(a, c) < 1:
            continue
        fr = deck_frame(R2.lerp3(a, c, 0.5), sub(c, a))
        Ls = math.dist(a, c)
        for s in (-1, 1):
            # a wall flaring out at 30 degrees from vertical from the road edge: half a hexagon
            up = unit(add(mul(fr.y, math.cos(math.radians(30))), mul(fr.x, s * math.sin(math.radians(30)))))
            xa = unit(cross(up, fr.z))
            q = add(fr.p, add(mul(fr.x, s * (w / 2 + 1)), mul(up, 13)))
            Pt(b, "HexWall", CF(q, xa, up, fr.z), (2, 26, Ls + 0.5), col, "Metal", b.scenery)
            Pt(b, "HexEdge", CF(add(q, mul(up, 13.2)), xa, up, fr.z), (2.4, 0.8, Ls + 0.5), edge, "Neon", b.scenery)
    return r


def downhill(o, label, L, drop, w=110.0, rocks=4, rng=None, cp=True, col=(120, 110, 96), top=(110, 150, 80),
             boulder=(110, 100, 90)):
    """A rocky hillside to bomb down with boost strips and boulders to dodge (a lane through every row)."""
    b, r = o.b, o.r
    rng = rng or r.rng
    n_before = len(b.path)
    pts = surface(o, label, L, w, dy=-drop, look=look_rock_slope(rng, col, top), cp=cp, step=12.0)
    f = r.f
    rt = right_of(f)
    R2.lay_strips(r, 30, L - 30, every=70, lanes=2)
    # boulder rows, each with one clear lane, and the racing line through the lanes
    cum = [0.0]
    for a_, c_ in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))
    rows = [L * (k + 1) / (rocks + 1) for k in range(rocks)]
    lanes = []
    for k, d in enumerate(rows):
        i = next(i for i in range(len(cum) - 1) if cum[i + 1] >= d)
        p = R2.lerp3(pts[i], pts[i + 1], (d - cum[i]) / max(cum[i + 1] - cum[i], 1e-6))
        gap = rng.uniform(-w / 2 + 26, w / 2 - 26)
        lanes.append((d, gap, p))
        x = -w / 2 + 12
        while x < w / 2 - 8:
            if abs(x - gap) > 26:
                s = rng.uniform(16, 22)
                c = add(add(p, mul(rt, x)), (0, s * 0.42, 0))
                ell(b, "Boulder", c, (s * 1.2, s, s * 1.1), boulder, "Slate", b.scenery)
                b.part("BoulderSolid", CF(c), (s * 0.85, s * 0.85, s * 0.85), (110, 100, 90), parent=b.scenery,
                       transp=1, collide=True, shape=0)
            x += 22
    # the racing line: in through the start, through each row's lane, out at the end
    seg = [p_ for p_ in b.path[n_before:]]
    new = [seg[0]]
    for (d, gap, p) in lanes:
        for dd in (-22, 0, 22):
            i = next(i for i in range(len(cum) - 1) if cum[i + 1] >= d + dd)
            q = R2.lerp3(pts[i], pts[i + 1], (d + dd - cum[i]) / max(cum[i + 1] - cum[i], 1e-6))
            q = add(q, mul(rt, gap))
            new.append((q[0], q[1] + CAR_UP, q[2], "r"))
    new += [p_ for p_ in seg if dot(sub(p_[:3], pts[0]), f) > rows[-1] + 30]
    b.path[n_before:] = new
    return pts


def piano(o, label, L=360.0, w=90.0, cp=True):
    """Giant piano keys that sink a moment after you touch them: keep moving."""
    b, r = o.b, o.r
    if o.need:
        surface(o, label + " Landing", 0, w, look=look_glass_floor((240, 240, 240), (30, 30, 30)), cp=cp)
    R2.sink_board(r, label, L, w, cell=30.0, cols=((250, 250, 248), (24, 24, 28)), mats=("SmoothPlastic", "SmoothPlastic"),
                  delay=0.18, rate=110.0)
    return r


# ===================================================================== boats
def boat(o, label, L=170.0, w=44.0, rng=None, bob=2.5, period=3.0, cp=False, hull=(170, 60, 50)):
    """A boat on the water, bobbing: you land on its deck and drive off over its bow."""
    b, r = o.b, o.r
    rng = rng or r.rng
    L = max(L, o.need)
    root = b.prop_root("Boat")
    mid = add(r.p, add(mul(r.f, L / 2), (0, -bob, 0)))
    rig = b.rig(root, "Slide", axis_frame(mid, (0, 1, 0)), 2 * bob, period, phase=rng.random(), name="Bob")
    a = rbxl_attrs(rig)
    a["BoostSpeed"] = float(o.B)
    rbxl_set(rig, a)
    return surface(o, label, L, w, look=look_boat(rng, hull=hull, parent=rig), cp=cp, parent=rig)


def rbxl_attrs(i):
    import rbxl
    return rbxl.attrs(i) or {}


def rbxl_set(i, a):
    import rbxl
    rbxl.set_attrs(i, a)
