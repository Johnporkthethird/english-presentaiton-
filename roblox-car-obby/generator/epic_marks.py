"""Giant landmarks the epic levels climb, circle, dive through and jump between. Scenery only (never collides), so a
fall always ends at the kill sheet; whatever is driven on is laid by the route."""
import math
import random
from geom import CF, axis_frame, deck_frame, add, sub, mul, unit, cross, rot_y, UP
from builder import mix
from skins import Pt, box, cyl, ball, cone, hexcol, pixel_art, FONT
from geom import rot_axis
from worlds import ell, ringz

TAU = math.pi * 2


def P(b, name, cf, size, color, mat="SmoothPlastic", **kw):
    return Pt(b, name, cf, size, color, mat, parent=b.scenery, **kw)


def C(b, name, c, h, d, color, mat="SmoothPlastic", axis=UP, **kw):
    return cyl(b, name, c, h, d, color, mat, b.scenery, axis=axis, **kw)


def B(b, name, c, d, color, mat="SmoothPlastic", **kw):
    return ball(b, name, c, d, color, mat, b.scenery, **kw)


def ring_of(n, R, a0=0.0):
    return [(math.cos(a0 + TAU * k / n) * R, math.sin(a0 + TAU * k / n) * R, a0 + TAU * k / n) for k in range(n)]


class Local:
    """A prop's own frame (yaw about Y; the prop's front is its -Z), to place parts by local offsets."""
    def __init__(self, c, yaw=0.0):
        self.cf = CF(c) * rot_y(yaw)

    def at(self, x, y, z):
        return self.cf.point((x, y, z))

    def rot(self, *extra):
        r = CF((0, 0, 0), self.cf.x, self.cf.y, self.cf.z)
        for e in extra:
            r = r * e
        return r

    def cf_at(self, x, y, z, *extra):
        r = self.rot(*extra)
        return CF(self.at(x, y, z), r.x, r.y, r.z)


def tri(b, name, a, b_, c, color, mat="SmoothPlastic", parent=None, th=1.0, inward=None, collide=False):
    """A flat triangle from two wedges (the usual Roblox way). inward: a point on the solid side, so the triangle's
    thickness goes that way and its face lies exactly on the plane through a, b_, c."""
    ab, ac, bc = sub(b_, a), sub(c, a), sub(c, b_)
    abd, acd, bcd = dot3(ab, ab), dot3(ac, ac), dot3(bc, bc)
    if abd > acd and abd > bcd:
        c, a = a, c
    elif acd > bcd and acd > abd:
        a, b_ = b_, a
    ab, ac, bc = sub(b_, a), sub(c, a), sub(c, b_)
    right = unit(cross(ac, ab))
    up = unit(cross(bc, right))
    back = unit(bc)
    height = abs(dot3(ab, up))
    if height < 0.05:
        return
    off = (0.0, 0.0, 0.0)
    if inward is not None:
        g = mul(add(add(a, b_), c), 1 / 3)
        sgn = 1.0 if dot3(sub(inward, g), right) > 0 else -1.0
        off = mul(right, sgn * th / 2)
    parent = parent if parent is not None else b.scenery
    p1 = add(mul(add(a, b_), 0.5), off)
    Pt(b, name, CF(p1, right, up, back), (th, height, abs(dot3(ab, back))), color, mat, parent, cls="WedgePart",
       collide=collide)
    p2 = add(mul(add(a, c), 0.5), off)
    Pt(b, name, CF(p2, mul(right, -1), up, mul(back, -1)), (th, height, abs(dot3(ac, back))), color, mat, parent,
       cls="WedgePart", collide=collide)


def dot3(a, c):
    return a[0] * c[0] + a[1] * c[1] + a[2] * c[2]


def wcone(b, name, base, h, r, color, mat="SmoothPlastic", n=8, rot=0.0, parent=None, cap=True):
    """A smooth faceted cone (an n-sided pyramid) from triangles: base centre, height, base radius."""
    apex = add(base, (0, h, 0))
    ring = [add(base, (math.cos(rot + TAU * k / n) * r, 0, math.sin(rot + TAU * k / n) * r)) for k in range(n)]
    mid = add(base, (0, h * 0.3, 0))
    for k in range(n):
        tri(b, name, apex, ring[k], ring[(k + 1) % n], color, mat, parent, th=1.0, inward=mid)


def column(b, name, top, ylo, d, color, mat="SmoothPlastic"):
    """A round pillar from ylo up to top."""
    h = top[1] - ylo
    if h > 1:
        C(b, name, (top[0], ylo + h / 2, top[2]), h, d, color, mat)


# ===================================================================== 1. Sugar Rush
def cake(b, c, tiers, rng):
    """A tiered party cake: tiers = [(R, ybottom, ytop, sponge, icing)], centre c (plan)."""
    x, z = c[0], c[2]
    PAST = [(255, 140, 185), (120, 220, 200), (255, 215, 110), (170, 150, 255), (255, 170, 120)]
    y0 = tiers[0][1]
    C(b, "CakeStand", (x, y0 - 6, z), 12, 2 * tiers[0][0] + 70, (235, 235, 245), "Glass", refl=0.2)
    C(b, "CakeStandFoot", (x, y0 - 70, z), 120, 80, (235, 235, 245), "Glass", refl=0.2)
    C(b, "CakeStandBase", (x, y0 - 134, z), 10, 240, (235, 235, 245), "Glass", refl=0.2)
    for ti, (R, ylo, yhi, sponge, icing) in enumerate(tiers):
        H = yhi - ylo
        C(b, "Sponge", (x, (ylo + yhi) / 2 - 3, z), H - 6, 2 * R, sponge, "Sand")
        C(b, "Icing", (x, yhi - 3, z), 6, 2 * R + 4, icing)
        # cream layers showing through the sides
        for k in range(1, 3):
            C(b, "Cream", (x, ylo + H * k / 3, z), 5, 2 * R + 1.2, (255, 250, 240))
        # icing drips
        n = int(TAU * R / 16)
        for k in range(n):
            a = TAU * (k + 0.5) / n
            L = 8 + 18 * ((k * 37) % 7) / 6
            p = (x + math.cos(a) * (R + 1.2), yhi - 3 - L / 2, z + math.sin(a) * (R + 1.2))
            C(b, "Drip", p, L, 9, icing)
            B(b, "DripEnd", (p[0], p[1] - L / 2, p[2]), 9, icing)
        # a string of sugar pearls round the foot of the tier
        n = int(TAU * R / 10)
        for k in range(n):
            a = TAU * k / n
            B(b, "Pearl", (x + math.cos(a) * (R + 2), ylo + 3, z + math.sin(a) * (R + 2)), 8,
              PAST[k % 5] if ti % 2 == 0 else (255, 255, 255), "SmoothPlastic", refl=0.15)
        # sprinkles on the top ring
        inner = tiers[ti + 1][0] if ti + 1 < len(tiers) else 0.0
        for k in range(int(R * 0.5)):
            a = rng.random() * TAU
            r = rng.uniform(inner + 6, R - 6)
            box(b, "Sprinkle", (x + math.cos(a) * r, yhi + 0.4, z + math.sin(a) * r), (7, 1.4, 1.8), rng.choice(PAST),
                parent=b.scenery, yaw=rng.random() * 3)
    # candles on the top tier, and the cherry
    R, ylo, yhi = tiers[-1][0], tiers[-1][1], tiers[-1][2]
    for (dx, dz, a) in ring_of(6, R * 0.62, 0.3):
        col = PAST[int(a * 3) % 5]
        p = (x + dx, yhi + 30, z + dz)
        C(b, "Candle", p, 60, 12, col)
        for k in range(5):
            C(b, "CandleStripe", (p[0], yhi + 6 + k * 12, p[2]), 3, 12.4, (255, 255, 255))
        ell(b, "Flame", (p[0], yhi + 68, p[2]), (8, 16, 8), (255, 200, 80), "Neon", parent=b.scenery)
        ell(b, "FlameCore", (p[0], yhi + 66, p[2]), (4, 8, 4), (255, 255, 220), "Neon", parent=b.scenery)
    B(b, "Cherry", (x, yhi + 26, z), 52, (210, 20, 40), "SmoothPlastic", refl=0.25)
    C(b, "CherryStem", (x + 8, yhi + 64, z), 40, 3, (80, 140, 40), axis=unit((0.4, 1, 0)))
    C(b, "Whip", (x, yhi + 4, z), 8, 70, (255, 255, 255))
    C(b, "Whip", (x, yhi + 10, z), 6, 52, (255, 255, 255))


def candy_cane(b, base, h, d, lean=0.0, yaw=0.0):
    """A standing candy cane: striped pole with a hook."""
    x, y, z = base
    n = int(h // (d * 0.9))
    for k in range(n):
        C(b, "CanePole", (x, y + d * 0.9 * (k + 0.5), z), d * 0.9 + 0.05, d, (225, 30, 50) if k % 2 else (255, 255, 255))
    top = (x, y + n * d * 0.9, z)
    R = d * 1.6
    f = (math.cos(yaw), 0.0, -math.sin(yaw))
    for k in range(1, 10):
        a = math.pi * k / 9
        q = add(top, add(mul(f, R - R * math.cos(a)), (0, R * math.sin(a), 0)))
        B(b, "CaneHook", q, d * 1.04, (225, 30, 50) if k % 2 else (255, 255, 255))


def big_cupcake(b, base, h, col, rng, liner=(255, 255, 255)):
    """A standing cupcake landmark: a tapered pleated paper case, a domed sponge top, three swirls of frosting,
    sprinkles and a cherry. base = bottom centre, h = total height."""
    x, y, z = base
    R = h * 0.36
    hc = h * 0.42
    n = 6
    for k in range(n):
        t = (k + 0.5) / n
        C(b, "Liner", (x, y + hc * t, z), hc / n + 0.05, 2 * R * (0.78 + 0.22 * t), liner)
    m = 20
    for k in range(m):
        a = TAU * k / m
        rr = R * 0.9
        P(b, "Pleat", CF((x + math.cos(a) * rr, y + hc / 2, z + math.sin(a) * rr)) * rot_y(-a), (2.6, hc, R * 0.16), col)
    C(b, "CakeTop", (x, y + hc + 6, z), 12, 2 * R * 1.04, (214, 160, 100))
    for i, (dy, k_) in enumerate(((0.10, 1.0), (0.22, 0.78), (0.33, 0.52))):
        ell(b, "Frosting", (x, y + hc + h * dy, z), (2 * R * k_, h * 0.16, 2 * R * k_),
            mix(col, (255, 255, 255), 0.45 + 0.12 * i), parent=b.scenery)
    B(b, "Cherry", (x, y + hc + h * 0.47, z), h * 0.11, (210, 20, 40), refl=0.2)
    C(b, "CherryStem", (x + 3, y + hc + h * 0.55, z), h * 0.08, 1.6, (90, 140, 40))
    for k in range(30):
        a = rng.random() * TAU
        e = rng.uniform(0.15, 0.95)
        rr = R * 0.98 * e
        yy = y + hc + h * (0.10 + 0.2 * (1 - e))
        P(b, "Sprinkle", CF((x + math.cos(a) * rr, yy + h * 0.06, z + math.sin(a) * rr)) * rot_y(rng.random() * 3),
          (h * 0.04, 1.2, h * 0.012), rng.choice([(255, 90, 140), (90, 200, 255), (255, 220, 80), (140, 230, 120)]))


def lollipop(b, base, h, d, col, rng):
    x, y, z = base
    C(b, "LollyStick", (x, y + h / 2, z), h, d * 0.07 + 2, (255, 255, 255))
    top = (x, y + h + d / 2, z)
    C(b, "Lolly", top, d * 0.22, d, col, "SmoothPlastic", axis=(0, 0, 1), refl=0.15)
    for k in range(3):
        ringz(b, add(top, (0, 0, d * 0.11 + 0.2)), d * (0.15 + 0.12 * k), (255, 255, 255), "SmoothPlastic", th=0.4,
              axis=(0, 0, 1), parent=b.scenery, name="Swirl")


def choc_river(b, x0, x1, z0, z1, y):
    """A wide river of melted chocolate far below (deadly to land in: it sits on the kill sheet's level)."""
    P(b, "ChocRiver", CF(((x0 + x1) / 2, y, (z0 + z1) / 2)), (x1 - x0, 4, z1 - z0), (92, 52, 30), "Glass", refl=0.2)
    for k in range(int((x1 - x0) // 120)):
        xx = x0 + 60 + k * 120
        ell(b, "Swirl", (xx, y + 2.2, (z0 + z1) / 2 + ((k * 53) % 90 - 45)), (60, 1, 18), (122, 78, 50), parent=b.scenery)


# ===================================================================== 2. Drive Thru
def burger(b, c, R, rng, k=1.0):
    """A giant burger standing on its plate: c = bottom centre; k stretches the layers. Returns its top height."""
    x, y, z = c
    C(b, "Plate", (x, y - 4, z), 8, 2 * R + 120, (250, 250, 250), "SmoothPlastic", refl=0.1)
    C(b, "PlateRim", (x, y - 1, z), 4, 2 * R + 126, (205, 30, 42))
    yy = y
    h = 48 * k
    C(b, "BunBase", (x, yy + h / 2, z), h, 2 * R, (214, 150, 70), "Sand")
    yy += h
    for layer in range(2):
        h = (44 if layer == 0 else 34) * k
        C(b, "Patty", (x, yy + h / 2, z), h, 2 * R + 14, (92, 50, 30), "Slate")
        n = int(TAU * R / 18)
        for q in range(n):
            a = TAU * q / n
            B(b, "PattyLump", (x + math.cos(a) * (R + 6), yy + h / 2 + ((q * 7) % 5 - 2) * 3, z + math.sin(a) * (R + 6)),
              min(22, h * 0.8), (80, 44, 26), "Slate")
        yy += h
        if layer == 0:
            P(b, "Cheese", CF((x, yy + 3, z)) * rot_y(0.4), (2 * R + 10, 6, 2 * R + 10), (255, 196, 40))
            for q in range(4):
                a = -0.4 + TAU * q / 4 + math.pi / 4
                P(b, "CheeseDrip", CF((x + math.cos(a) * (R + 22), yy - 14, z + math.sin(a) * (R + 22))) * rot_y(-a),
                  (8, 40, 24), (255, 196, 40))
            yy += 6
            n = int(TAU * R / 22)
            C(b, "Lettuce", (x, yy + 4, z), 8, 2 * R + 20, (100, 200, 60))
            for q in range(n):
                a = TAU * q / n
                ell(b, "LettuceFrill", (x + math.cos(a) * (R + 14), yy + 2, z + math.sin(a) * (R + 14)), (34, 14, 34),
                    (120, 215, 70), parent=b.scenery)
            yy += 8
            h = 12 * k
            for (dx, dz, a) in ring_of(5, R * 0.55, 0.2):
                C(b, "Tomato", (x + dx, yy + h / 2, z + dz), h, R * 0.75, (225, 45, 40))
            yy += h
    ell(b, "BunTop", (x, yy, z), (2 * R + 4, R * 1.25 * k, 2 * R + 4), (222, 150, 64), parent=b.scenery)
    for q in range(60):
        a = rng.random() * TAU
        rr = rng.uniform(0.1, 0.85) * R
        hh = R * 0.62 * k * math.sqrt(max(0.0, 1 - (rr / R) ** 2))
        ell(b, "Sesame", (x + math.cos(a) * rr, yy + hh, z + math.sin(a) * rr), (8, 3, 4), (255, 245, 220),
            parent=b.scenery, rot=CF((0, 0, 0)) * rot_y(rng.random() * 3))
    return yy + R * 0.62 * k


def milkshake(b, c, R, H, rng):
    """A tall striped milkshake cup with a mountain of cream, a cherry and a bendy straw."""
    x, y, z = c
    n = 8
    for k in range(n):
        rr = R * (0.78 + 0.22 * k / (n - 1))
        C(b, "Cup", (x, y + H * (k + 0.5) / n, z), H / n + 0.1, 2 * rr, (255, 255, 255) if k % 2 else (255, 140, 180),
          "Glass", transp=0.08, refl=0.1)
    C(b, "Shake", (x, y + H - 6, z), 12, 2 * R - 4, (255, 190, 210))
    for i, (dy, k) in enumerate(((10, 1.0), (40, 0.78), (66, 0.54), (86, 0.3))):
        ell(b, "Cream", (x, y + H + dy, z), (2 * R * k, 50, 2 * R * k), (255, 252, 246), parent=b.scenery)
    B(b, "Cherry", (x, y + H + 112, z), 36, (210, 20, 40), refl=0.25)
    C(b, "Straw", (x + R * 0.45, y + H + 60, z - R * 0.2), 260, 18, (205, 30, 42), axis=unit((0.25, 1, 0.1)))
    for k in range(10):
        t = (k + 0.5) / 10
        p = (x + R * 0.45 + 0.25 * (t - 0.5) * 250, y + H + 60 + (t - 0.5) * 250, z - R * 0.2 + 0.1 * (t - 0.5) * 250)
        C(b, "StrawStripe", p, 8, 18.6, (255, 255, 255), axis=unit((0.25, 1, 0.1)))


def fry_box(b, c, w, H, rng):
    x, y, z = c
    P(b, "FryBox", CF((x, y + H / 2, z)), (w, H, w * 0.6), (205, 30, 42))
    P(b, "FryBand", CF((x, y + H * 0.55, z)), (w + 0.6, H * 0.18, w * 0.6 + 0.6), (255, 205, 40))
    for k in range(18):
        fx = x + rng.uniform(-0.42, 0.42) * w
        fz = z + rng.uniform(-0.22, 0.22) * w
        L = rng.uniform(0.5, 1.0) * H
        tilt = unit((rng.uniform(-0.2, 0.2), 1, rng.uniform(-0.2, 0.2)))
        P(b, "Fry", axis_frame((fx, y + H + L * 0.3, fz), tilt), (L, 9, 9), (255, 214, 90))


def ketchup(b, c, R, H):
    x, y, z = c
    C(b, "Bottle", (x, y + H / 2, z), H, 2 * R, (210, 20, 30), refl=0.15)
    C(b, "Label", (x, y + H * 0.45, z), H * 0.3, 2 * R + 0.6, (255, 255, 255))
    C(b, "Neck", (x, y + H + R * 0.4, z), R * 0.8, R * 1.2, (210, 20, 30))
    C(b, "Cap", (x, y + H + R * 0.95, z), R * 0.4, R * 1.0, (255, 255, 255))


# ===================================================================== 3. Spore Springs
def great_tree(b, c, R, ylo, yhi, rng, sk):
    """A colossal tree: buttress roots, a ridged trunk, branches and glowing mushroom shelves, a canopy of caps."""
    x, z = c[0], c[2]
    H = yhi - ylo
    n = 10
    for k in range(n):
        rr = R * (1.25 - 0.4 * k / n)
        C(b, "Trunk", (x, ylo + H * (k + 0.5) / n, z), H / n + 0.2, 2 * rr, sk.BARK, "Wood")
    for k in range(16):
        a = TAU * k / 16
        rr = R * 1.05
        P(b, "Bark", CF((x + math.cos(a) * rr, ylo + H * 0.45, z + math.sin(a) * rr)) * rot_y(-a), (10, H * 0.9, 18),
          sk.BARK_DK, "Wood")
    for k in range(7):
        a = TAU * k / 7 + 0.3
        d = (math.cos(a), -0.55, math.sin(a))
        p = (x + math.cos(a) * R * 1.5, ylo + 30, z + math.sin(a) * R * 1.5)
        C(b, "Root", p, R * 1.4, R * 0.42, sk.BARK, "Wood", axis=unit(d))
    for k in range(6):
        a = TAU * k / 6 + 0.7
        yb = ylo + H * (0.62 + 0.06 * (k % 3))
        d = unit((math.cos(a), 0.55, math.sin(a)))
        L = R * 2.4
        p = (x + d[0] * (R + L / 2), yb + d[1] * (L / 2), z + d[2] * (R + L / 2))
        C(b, "Branch", p, L, R * 0.36, sk.BARK, "Wood", axis=d)
        tip = (x + d[0] * (R + L), yb + d[1] * L, z + d[2] * (R + L))
        ell(b, "Leaves", add(tip, (0, 30, 0)), (190, 110, 190), (70, 150, 60), "Grass", parent=b.scenery)
        ell(b, "Leaves", add(tip, (40, 70, -30)), (130, 80, 130), (90, 175, 70), "Grass", parent=b.scenery)
    # the crown: a dome of leaves with glowing fruit
    ell(b, "Crown", (x, yhi + 70, z), (R * 5.2, 190, R * 5.2), (60, 140, 55), "Grass", parent=b.scenery)
    ell(b, "Crown", (x, yhi + 150, z), (R * 3.2, 150, R * 3.2), (80, 165, 65), "Grass", parent=b.scenery)
    for k in range(26):
        a = rng.random() * TAU
        rr = rng.uniform(0.3, 1.0) * R * 2.5
        B(b, "GlowFruit", (x + math.cos(a) * rr, yhi + 40 + rng.uniform(0, 80), z + math.sin(a) * rr), 12,
          rng.choice(sk.GLOW), "Neon")
    # glowing vines down the trunk
    for k in range(10):
        a = TAU * k / 10 + 0.15
        L = rng.uniform(0.25, 0.5) * H
        p = (x + math.cos(a) * (R * 1.1 + 4), yhi - L / 2 - 20, z + math.sin(a) * (R * 1.1 + 4))
        C(b, "Vine", p, L, 3, rng.choice(sk.GLOW), "Neon")


def giant_mushroom(b, base, h, d, cap, rng, glow=(120, 255, 210)):
    """A giant toadstool: bulbed, tapering stem, a frilled skirt, a domed spotted cap glowing underneath."""
    x, y, z = base
    stem = (240, 232, 210)
    ell(b, "StemBulb", (x, y + d * 0.1, z), (d * 0.44, d * 0.28, d * 0.44), stem, parent=b.scenery)
    n = 6
    for k in range(n):
        t = (k + 0.5) / n
        C(b, "Stem", (x, y + h * t, z), h / n + 0.05, d * (0.32 - 0.1 * t), mix(stem, (210, 196, 170), 0.3 * (k % 2)))
    C(b, "Skirt", (x, y + h * 0.74, z), 4, d * 0.4, (250, 244, 228))
    for k in range(12):
        a = TAU * k / 12
        ell(b, "SkirtFrill", (x + math.cos(a) * d * 0.19, y + h * 0.74 - 6, z + math.sin(a) * d * 0.19), (d * 0.1, 12, d * 0.1),
            (250, 244, 228), parent=b.scenery)
    C(b, "Gills", (x, y + h + 1, z), 2, d * 0.92, glow, "Neon")
    ell(b, "Cap", (x, y + h + d * 0.12, z), (d, d * 0.46, d), cap, parent=b.scenery)
    ell(b, "CapShine", (x - d * 0.12, y + h + d * 0.3, z - d * 0.1), (d * 0.3, d * 0.08, d * 0.22),
        mix(cap, (255, 255, 255), 0.35), parent=b.scenery)
    for k in range(12):
        a = rng.random() * TAU
        rr = rng.uniform(0.08, 0.4) * d
        hh = d * 0.23 * math.sqrt(max(0.0, 1 - (rr / (d * 0.5)) ** 2))
        sz = rng.uniform(0.08, 0.13) * d
        ell(b, "Spot", (x + math.cos(a) * rr, y + h + d * 0.12 + hh, z + math.sin(a) * rr), (sz, d * 0.035, sz),
            (255, 255, 240), parent=b.scenery)


def glow_pond(b, c, R, y, col=(60, 200, 190)):
    C(b, "Pond", (c[0], y, c[2]), 4, 2 * R, col, "Neon", transp=0.25)
    for k in range(6):
        ringz(b, (c[0], y + 2.2, c[2]), R * (0.3 + 0.12 * k), (190, 130, 255), "Neon", th=0.6, parent=b.scenery)


# ===================================================================== 4. Checkmate
def chess_piece(b, kind, base, s, col, trim=(232, 190, 90), parent=None):
    """A giant chess piece, s = its base diameter (parent: a rig, to make it move)."""
    keep = b.scenery
    if parent is not None:
        b.scenery = parent
    try:
        return _chess_piece(b, kind, base, s, col, trim)
    finally:
        b.scenery = keep


def _chess_piece(b, kind, base, s, col, trim=(232, 190, 90)):
    """A giant chess piece, s = its base diameter."""
    x, y, z = base
    mat = "Marble" if col[0] > 128 else "SmoothPlastic"
    C(b, "PieceBase", (x, y + s * 0.08, z), s * 0.16, s, col, mat)
    C(b, "PieceTrim", (x, y + s * 0.17, z), s * 0.04, s * 0.92, trim, "Metal")
    C(b, "PieceFoot", (x, y + s * 0.26, z), s * 0.16, s * 0.8, col, mat)
    if kind == "pawn":
        C(b, "Body", (x, y + s * 0.62, z), s * 0.6, s * 0.42, col, mat)
        C(b, "Collar", (x, y + s * 0.94, z), s * 0.06, s * 0.62, col, mat)
        B(b, "Head", (x, y + s * 1.2, z), s * 0.52, col, mat)
        return y + s * 1.46
    if kind == "rook":
        C(b, "Body", (x, y + s * 0.8, z), s * 1.0, s * 0.62, col, mat)
        C(b, "Crown", (x, y + s * 1.38, z), s * 0.2, s * 0.8, col, mat)
        for (dx, dz, a) in ring_of(6, s * 0.33):
            P(b, "Merlon", CF((x + dx, y + s * 1.56, z + dz)) * rot_y(-a), (s * 0.14, s * 0.18, s * 0.2), col, mat)
        return y + s * 1.64
    if kind == "bishop":
        C(b, "Body", (x, y + s * 0.85, z), s * 1.1, s * 0.4, col, mat)
        ell(b, "Mitre", (x, y + s * 1.6, z), (s * 0.5, s * 0.75, s * 0.5), col, mat, parent=b.scenery)
        B(b, "Tip", (x, y + s * 2.02, z), s * 0.14, col, mat)
        return y + s * 2.1
    if kind == "knight":
        C(b, "Body", (x, y + s * 0.5, z), s * 0.36, s * 0.56, col, mat)
        P(b, "Neck", CF((x - s * 0.04, y + s * 0.92, z)) * rot_axis((0, 0, 1), 0.28), (s * 0.34, s * 0.7, s * 0.4), col, mat)
        P(b, "HeadK", CF((x + s * 0.2, y + s * 1.3, z)) * rot_axis((0, 0, 1), -0.42), (s * 0.62, s * 0.3, s * 0.36), col, mat)
        ell(b, "Muzzle", (x + s * 0.44, y + s * 1.13, z), (s * 0.28, s * 0.24, s * 0.32), col, mat, parent=b.scenery)
        ell(b, "Nostril", (x + s * 0.56, y + s * 1.12, z), (s * 0.04, s * 0.06, s * 0.2), mix(col, (0, 0, 0), 0.4), parent=b.scenery)
        for sz in (-1, 1):
            P(b, "Ear", CF((x - s * 0.02, y + s * 1.55, z + sz * s * 0.1)) * rot_axis((0, 0, 1), 0.2), (s * 0.08, s * 0.2, s * 0.08), col, mat)
            ball(b, "KnightEye", (x + s * 0.22, y + s * 1.38, z + sz * s * 0.18), s * 0.07, trim, "Metal", b.scenery)
        for k in range(6):
            t = k / 5
            ball(b, "Mane", (x - s * 0.24 + s * 0.12 * t, y + s * 0.72 + s * 0.78 * t, z), s * 0.13, trim, "Metal", b.scenery)
        return y + s * 1.62
    if kind in ("queen", "king"):
        C(b, "Body", (x, y + s * 1.0, z), s * 1.4, s * 0.44, col, mat)
        C(b, "Collar", (x, y + s * 1.72, z), s * 0.08, s * 0.64, trim, "Metal")
        ell(b, "Head", (x, y + s * 1.95, z), (s * 0.56, s * 0.4, s * 0.56), col, mat, parent=b.scenery)
        if kind == "queen":
            for (dx, dz, a) in ring_of(8, s * 0.24):
                B(b, "CrownBall", (x + dx, y + s * 2.18, z + dz), s * 0.09, trim, "Metal")
            return y + s * 2.25
        P(b, "Cross", CF((x, y + s * 2.4, z)), (s * 0.08, s * 0.45, s * 0.08), trim, "Metal")
        P(b, "Cross", CF((x, y + s * 2.48, z)), (s * 0.3, s * 0.08, s * 0.08), trim, "Metal")
        return y + s * 2.62


def castle(b, c, W, D, H, rng, stone=(170, 166, 158), roof=(40, 60, 140)):
    """A castle keep: four walls with battlements and arrow slits, round corner towers with pointed roofs."""
    x, y, z = c
    for (dx, dz, L, axis) in ((0, -D / 2, W, 0), (0, D / 2, W, 0), (-W / 2, 0, D, 1), (W / 2, 0, D, 1)):
        sx, sz = (L, 18) if axis == 0 else (18, L)
        P(b, "Wall", CF((x + dx, y + H / 2, z + dz)), (sx, H, sz), stone, "Cobblestone")
        n = int(L // 26)
        for k in range(n):
            t = -L / 2 + 13 + k * 26
            q = (x + dx + (t if axis == 0 else 0), y + H + 6, z + dz + (t if axis == 1 else 0))
            if k % 2 == 0:
                P(b, "Merlon", CF(q), (14 if axis == 0 else 20, 12, 20 if axis == 0 else 14), stone, "Cobblestone")
            else:
                s_ = (x + dx + (t if axis == 0 else (9.2 if dx > 0 else -9.2)), y + H * 0.62,
                      z + dz + (t if axis == 1 else (9.2 if dz > 0 else -9.2)))
                P(b, "Slit", CF(s_), (3 if axis == 0 else 1, 22, 1 if axis == 0 else 3), (20, 18, 24))
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = (x + sx * W / 2, y, z + sz * D / 2)
            C(b, "Tower", (p[0], y + (H + 70) / 2, p[2]), H + 70, 70, stone, "Cobblestone")
            C(b, "TowerRim", (p[0], y + H + 72, p[2]), 6, 78, mix(stone, (0, 0, 0), 0.15), "Cobblestone")
            cone(b, "Roof", (p[0], y + H + 74, p[2]), 90, 82, roof, "SmoothPlastic", parent=b.scenery, n=7)
            P(b, "Flag", CF((p[0] + 14, y + H + 176, p[2])), (26, 16, 1), (232, 190, 90))
            C(b, "FlagPole", (p[0], y + H + 172, p[2]), 30, 2, (60, 50, 40))


def board(b, c, n, cell, y, col_a=(242, 238, 228), col_b=(34, 32, 38), frame=(92, 56, 32)):
    x0, z0 = c[0] - n * cell / 2, c[2] - n * cell / 2
    P(b, "BoardFrame", CF((c[0], y - 5, c[2])), (n * cell + 40, 10, n * cell + 40), frame, "Wood")
    for i in range(n):
        for j in range(n):
            P(b, "Square", CF((x0 + cell * (i + 0.5), y + 0.5, z0 + cell * (j + 0.5))), (cell, 1, cell),
              col_a if (i + j) % 2 == 0 else col_b, "Marble" if (i + j) % 2 == 0 else "SmoothPlastic")


# ===================================================================== 5. Tick Tock
def clock_face(b, c, R, y, sk, rng):
    """A colossal clock lying face up: c = centre, y = its face height."""
    x, z = c[0], c[2]
    C(b, "ClockCase", (x, y - 30, z), 56, 2 * R + 60, sk.DARK, "Metal")
    C(b, "Bezel", (x, y - 1, z), 4, 2 * R + 46, sk.BRASS, "Metal", refl=0.2)
    C(b, "Face", (x, y - 1.5, z), 4, 2 * R - 40, sk.FACE)
    for k in range(60):
        a = TAU * k / 60
        L = 30 if k % 5 == 0 else 12
        P(b, "Tick", CF((x + math.cos(a) * (R - 40 - L / 2), y + 0.6, z + math.sin(a) * (R - 40 - L / 2))) * rot_y(-a),
          (L, 0.4, 6 if k % 5 == 0 else 3), sk.INK)
    # roman-ish numerals: bars
    for k in range(12):
        a = TAU * k / 12
        p = (x + math.cos(a) * (R - 120), y + 0.6, z + math.sin(a) * (R - 120))
        nb = (k % 4) + 1
        for j in range(nb):
            P(b, "Numeral", CF(add(p, (math.cos(a + math.pi / 2) * (j - (nb - 1) / 2) * 12, 0,
                                      math.sin(a + math.pi / 2) * (j - (nb - 1) / 2) * 12))) * rot_y(-a),
              (40, 0.4, 6), sk.INK)
    for k in range(24):
        a = TAU * k / 24
        P(b, "CaseRib", CF((x + math.cos(a) * (R + 30), y - 30, z + math.sin(a) * (R + 30))) * rot_y(-a), (6, 56, 16),
          sk.BRASS, "Metal")


def gear(b, c, R, axis, col, mat="Metal", teeth=None, spin=0.0, phase=0.0, th=10.0):
    """A big gear (optionally turning)."""
    parent = b.scenery
    if spin:
        root = b.prop_root("BigGear")
        parent = b.rig(root, "Spin", axis_frame(c, axis), spin, 4, phase=phase, name="GearSpin")
    fr = axis_frame(c, axis)
    cyl(b, "Gear", c, th, 2 * R, col, mat, parent, axis=axis)
    cyl(b, "GearHub", c, th + 4, R * 0.35, mix(col, (0, 0, 0), 0.35), mat, parent, axis=axis)
    n = teeth or max(8, int(TAU * R / 22))
    for k in range(n):
        a = TAU * k / n
        d = add(mul(fr.y, math.cos(a)), mul(fr.z, math.sin(a)))
        p = add(c, mul(d, R + 5))
        Pt(b, "Tooth", CF(p, fr.x, d, cross(fr.x, d)), (th, 12, 12), col, mat, parent)
    for k in range(5):
        a = TAU * k / 5
        d = add(mul(fr.y, math.cos(a)), mul(fr.z, math.sin(a)))
        Pt(b, "Spoke", CF(add(c, mul(d, R * 0.55)), fr.x, d, cross(fr.x, d)), (th + 1, R * 0.6, R * 0.12),
           mix(col, (0, 0, 0), 0.2), mat, parent)


# ===================================================================== 6. Toy Box
def toy_block(b, c, s, col, letter_col=(255, 255, 255), letter=None, yaw=0.0):
    """A wooden alphabet block: bevelled edges, a raised panel and a letter on every side."""
    L = Local((c[0], c[1] + s / 2, c[2]), yaw)
    edge = mix(col, (0, 0, 0), 0.25)
    P(b, "ToyBlock", L.cf_at(0, 0, 0), (s * 0.94, s * 0.94, s * 0.94), col, refl=0.05)
    h = s * 0.47
    for ax in range(3):
        for u in (-1, 1):
            for v in (-1, 1):
                p = [0.0, 0.0, 0.0]
                others = [i for i in range(3) if i != ax]
                p[others[0]], p[others[1]] = u * h, v * h
                size = [s * 0.08] * 3
                size[ax] = s * 0.94 + (0.02 if ax == 0 else 0.0)
                P(b, "BlockEdge", L.cf_at(*p), tuple(size), edge)
    letters = "ABCDEXYZ123"
    rng_l = int(abs(c[0] * 7 + c[2] * 3)) % len(letters)
    for k, (nx, nz) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
        n = (nx, 0, nz)
        P(b, "BlockPanel", L.cf_at(nx * (s * 0.47 + 0.15), 0, nz * (s * 0.47 + 0.15)),
          (s * 0.66 if nz else 0.3, s * 0.66, 0.3 if nz else s * 0.66), mix(col, (255, 255, 255), 0.55))
        ch = letter or letters[(rng_l + k) % len(letters)]
        rows = FONT.get(ch, FONT["A"])
        nrm = L.cf.vec(n)
        pixel_art(b, L.at(nx * (s * 0.47 + 0.3), 0, nz * (s * 0.47 + 0.3)), nrm, (0, 1, 0), rows, s * 0.1, letter_col,
                  "SmoothPlastic", b.scenery, th=0.4, name="BlockLetter")


def teddy(b, c, s, col=(190, 130, 80), yaw=0.0):
    """A sitting teddy bear (s = about half its height), facing its -Z."""
    L = Local(c, yaw)
    lt = mix(col, (255, 238, 214), 0.5)
    dk = (36, 24, 20)

    def E(name, p, size, color, rot=(), mat="Fabric"):
        ell(b, name, L.at(p[0] * s, p[1] * s, p[2] * s), tuple(v * s for v in size), color, mat, parent=b.scenery,
            rot=L.rot(*rot))

    E("TeddyBody", (0, 0.62, 0), (0.98, 1.08, 0.86), col)
    E("TeddyBelly", (0, 0.58, -0.33), (0.58, 0.72, 0.24), lt)
    E("TeddyHead", (0, 1.42, -0.02), (0.82, 0.74, 0.74), col)
    E("TeddyMuzzle", (0, 1.31, -0.33), (0.38, 0.27, 0.24), lt)
    E("TeddyNose", (0, 1.38, -0.445), (0.15, 0.1, 0.08), dk, mat="SmoothPlastic")
    for sx in (-1, 1):
        E("TeddySmile", (sx * 0.05, 1.255, -0.435), (0.09, 0.02, 0.025), dk, (rot_axis((0, 0, 1), sx * 0.45),), "SmoothPlastic")
        E("TeddyEye", (sx * 0.155, 1.53, -0.33), (0.1, 0.12, 0.07), dk, mat="SmoothPlastic")
        E("TeddyEyeShine", (sx * 0.155 + 0.028, 1.56, -0.362), (0.03, 0.03, 0.012), (255, 255, 255), mat="Neon")
        E("TeddyEar", (sx * 0.3, 1.77, 0.0), (0.3, 0.3, 0.17), col)
        E("TeddyEarInner", (sx * 0.3, 1.76, -0.072), (0.17, 0.17, 0.05), lt)
        E("TeddyArm", (sx * 0.52, 0.82, -0.12), (0.3, 0.64, 0.3), col, (rot_axis((0, 0, 1), sx * 0.45), rot_axis((1, 0, 0), -0.3)))
        E("TeddyPaw", (sx * 0.655, 0.545, -0.22), (0.22, 0.22, 0.1), lt, (rot_axis((0, 0, 1), sx * 0.45),))
        E("TeddyLeg", (sx * 0.3, 0.19, -0.34), (0.38, 0.34, 0.6), col)
        E("TeddyFoot", (sx * 0.3, 0.2, -0.635), (0.29, 0.31, 0.06), lt)
        for k in range(3):
            E("TeddyToe", (sx * 0.3 + (k - 1) * 0.08, 0.31, -0.66), (0.06, 0.06, 0.02), mix(lt, dk, 0.25))
        E("TeddyBow", (sx * 0.11, 1.06, -0.335), (0.2, 0.14, 0.07), (225, 40, 60), (rot_axis((0, 0, 1), sx * 0.3),), "SmoothPlastic")
    E("TeddyBowKnot", (0, 1.06, -0.36), (0.08, 0.09, 0.06), (180, 20, 40), mat="SmoothPlastic")


def spinning_top(b, c, s, cols):
    """A striped spinning top on its point (s = its height), turning."""
    x, y, z = c
    root = b.prop_root("Top")
    rig = b.rig(root, "Spin", axis_frame((x, y, z), UP), 0.4, 4, name="TopSpin")
    n = 18
    y0, H = y + 0.1 * s, 0.82 * s
    for k in range(n):
        t = (k + 0.5) / n
        prof = (t / 0.55) ** 0.75 if t < 0.55 else 1 - 0.8 * ((t - 0.55) / 0.45) ** 1.5
        d = s * (0.05 + 0.8 * prof)
        cyl(b, "TopBand", (x, y0 + H * t, z), H / n + 0.05, d, cols[(k // 2) % len(cols)], "SmoothPlastic", rig, refl=0.08)
    cyl(b, "TopRim", (x, y0 + H * 0.55, z), 0.03 * s, s * 0.88, (255, 255, 255), "SmoothPlastic", rig)
    cone(b, "TopTip", (x, y0, z), 0.1 * s, 0.07 * s, (200, 200, 210), "Metal", rig, n=4, down=True)
    cyl(b, "TopHandle", (x, y0 + H + 0.14 * s, z), 0.28 * s, 0.08 * s, (245, 245, 245), "SmoothPlastic", rig)
    ball(b, "TopKnob", (x, y0 + H + 0.3 * s, z), 0.13 * s, cols[0], "SmoothPlastic", rig)


def duck(b, c, s, yaw=0.0):
    """A rubber duck (s = its body length), facing its -Z."""
    L = Local(c, yaw)
    Y, O, O2, dk = (255, 214, 40), (255, 130, 20), (230, 100, 10), (24, 20, 20)

    def E(name, p, size, color, rot=(), mat="SmoothPlastic"):
        ell(b, name, L.at(p[0] * s, p[1] * s, p[2] * s), tuple(v * s for v in size), color, mat, parent=b.scenery,
            rot=L.rot(*rot), )

    E("DuckBody", (0, 0.36, 0.05), (0.88, 0.62, 1.25), Y)
    E("DuckChest", (0, 0.46, -0.36), (0.78, 0.58, 0.62), Y)
    E("DuckTail", (0, 0.6, 0.55), (0.46, 0.32, 0.4), Y, (rot_axis((1, 0, 0), -0.7),))
    E("DuckHead", (0, 0.98, -0.36), (0.64, 0.62, 0.6), Y)
    E("DuckTuft", (0, 1.31, -0.33), (0.07, 0.2, 0.12), Y, (rot_axis((1, 0, 0), 0.4),))
    E("DuckBeak", (0, 0.94, -0.7), (0.38, 0.12, 0.34), O)
    E("DuckBeakLow", (0, 0.88, -0.66), (0.3, 0.08, 0.26), O2)
    for sx in (-1, 1):
        E("DuckEye", (sx * 0.16, 1.08, -0.6), (0.1, 0.13, 0.06), dk)
        E("DuckEyeShine", (sx * 0.16 + 0.025, 1.12, -0.625), (0.03, 0.035, 0.012), (255, 255, 255), mat="Neon")
        E("DuckWing", (sx * 0.43, 0.48, 0.08), (0.16, 0.36, 0.64), (245, 196, 30), (rot_axis((0, 0, 1), sx * 0.22),))
        E("DuckCheek", (sx * 0.22, 0.94, -0.52), (0.12, 0.08, 0.06), (255, 150, 120))


# ===================================================================== 7. Orbit
def planet(b, c, R, col, band, rng, ring=None, moons=0):
    x, y, z = c
    B(b, "Planet", c, 2 * R, col, "SmoothPlastic")
    B(b, "Atmosphere", c, 2 * R + 14, mix(col, (255, 255, 255), 0.4), "Glass", transp=0.75)
    for k in range(5):
        hh = R * (-0.6 + 0.3 * k)
        rr = math.sqrt(max(R * R - hh * hh, 1.0))
        ringz(b, (x, y + hh, z), rr + 0.4, band if k % 2 else mix(col, band, 0.5), "SmoothPlastic", th=R * 0.12,
              parent=b.scenery, name="Band")
    if ring:
        rr, tilt, rc = ring
        ax = unit((math.sin(tilt), math.cos(tilt), 0.2))
        for k in range(3):
            ringz(b, c, rr + k * 14, mix(rc, (255, 255, 255), 0.2 * k), "Glass", th=1.0, axis=ax, parent=b.scenery,
                  name="PlanetRing")
    for k in range(moons):
        a = rng.random() * TAU
        d = R * rng.uniform(1.7, 2.4)
        B(b, "Moon", (x + math.cos(a) * d, y + rng.uniform(-0.4, 0.6) * R, z + math.sin(a) * d), R * rng.uniform(0.18, 0.3),
          (200, 200, 210), "Slate")


def asteroid(b, c, s, rng, col=(110, 104, 100)):
    for k in range(5):
        a, e = rng.random() * TAU, rng.uniform(-0.6, 0.9)
        d = (math.cos(a) * math.cos(e), math.sin(e), math.sin(a) * math.cos(e))
        ell(b, "Crater", add(c, mul(d, s * 0.4)), (s * 0.22, s * 0.22, s * 0.06), mix(col, (0, 0, 0), 0.45), "Slate",
            parent=b.scenery, rot=axis_frame((0, 0, 0), d) * CF((0, 0, 0), (0, 0, 1), (0, 1, 0), (-1, 0, 0)))
    for k in range(3):
        o = (rng.uniform(-0.25, 0.25) * s, rng.uniform(-0.2, 0.2) * s, rng.uniform(-0.25, 0.25) * s)
        ell(b, "Asteroid", add(c, o), (s * rng.uniform(0.6, 1.0), s * rng.uniform(0.5, 0.8), s * rng.uniform(0.6, 1.0)),
            mix(col, (0, 0, 0), rng.uniform(0, 0.3)), "Slate", parent=b.scenery, rot=CF((0, 0, 0)) * rot_y(rng.random() * 3))


def station(b, c, R, sk):
    x, y, z = c
    ringz(b, c, R, sk.top, "DiamondPlate", th=30.0, parent=b.scenery, name="StationRing")
    ringz(b, add(c, (0, 16, 0)), R - 4, sk.edge, "Neon", th=1.0, parent=b.scenery, name="StationGlow")
    C(b, "StationHub", c, 60, R * 0.4, sk.body, "Metal")
    for k in range(4):
        a = TAU * k / 4
        P(b, "Spoke", CF((x + math.cos(a) * R / 2, y, z + math.sin(a) * R / 2)) * rot_y(-a), (R, 10, 10), sk.top, "Metal")
    for s in (-1, 1):
        P(b, "SolarPanel", CF((x, y + s * 50, z)) * rot_y(0.3), (R * 1.6, 2, 60), (40, 70, 160), "Glass", refl=0.3)


# ===================================================================== 8. Eruption
def canyon(b, pts, half, depth, rng, sk, lava_y):
    """Canyon walls on both sides of a road polyline: stacked, banded rock mesas (dark basalt, rust, ochre) with glowing
    cracks and the odd lava fall, over a lava river."""
    bands = [(58, 40, 36), (120, 58, 36), (150, 92, 50), (84, 52, 40), (40, 32, 30)]
    road_y = pts[0][1]
    for i in range(0, len(pts) - 1, 5):
        a, c_ = pts[i], pts[min(i + 5, len(pts) - 1)]
        f = unit((c_[0] - a[0], 0, c_[2] - a[2]))
        if f == (0.0, 0.0, 0.0):
            continue
        L = math.dist((a[0], 0, a[2]), (c_[0], 0, c_[2])) + 24
        mid = ((a[0] + c_[0]) / 2, 0, (a[2] + c_[2]) / 2)
        right = (-f[2], 0, f[0])
        P(b, "LavaRiver", CF((mid[0], lava_y, mid[2]), (f[0], 0, f[2]), (0, 1, 0), (-f[2], 0, f[0])), (L, 3, half * 1.6),
          sk.LAVA, "Neon")
        for s_ in (-1, 1):
            top = road_y + rng.uniform(-40, 70)
            off = half + rng.uniform(30, 60)
            base = add(mid, mul(right, s_ * off))
            y = lava_y - 10
            k = 0
            width = rng.uniform(70, 110)
            while y < top:
                h = min(rng.uniform(26, 44), top - y + 1)
                wdt = width * (1 - 0.06 * k)
                yaw = rng.uniform(-0.12, 0.12)
                q = add(base, mul(right, s_ * k * 3))
                P(b, "Mesa", CF((q[0], y + h / 2, q[2])) * rot_y(math.atan2(-f[2], f[0]) + yaw), (L + rng.uniform(0, 30), h, wdt),
                  bands[(k + i) % len(bands)], "Basalt" if k % 2 else "Rock")
                y += h
                k += 1
            if rng.random() < 0.3:
                q = add(base, mul(right, -s_ * (width / 2 - 2)))
                P(b, "LavaFall", CF((q[0], (lava_y + top) / 2, q[2])) * rot_y(math.atan2(-f[2], f[0])),
                  (rng.uniform(10, 22), top - lava_y, 2.5), sk.LAVA2, "Neon")
            if rng.random() < 0.5:
                q = add(base, mul(right, -s_ * (width / 2 - 1)))
                P(b, "Crack", CF((q[0], top - rng.uniform(20, 60), q[2])) * rot_y(math.atan2(-f[2], f[0]) + rng.uniform(-0.4, 0.4)),
                  (rng.uniform(30, 60), 1.5, 2), sk.LAVA, "Neon")


def obsidian_spire(b, c, h, d, sk, tip=True):
    x, y, z = c
    hexcol(b, "Spire", (x, y + h, z), d, h, sk.body, "Basalt", collide=False)
    if tip:
        cone(b, "SpireTip", (x, y + h, z), d * 1.4, d, sk.body, "Basalt", parent=b.scenery, n=5)
    for k in range(3):
        hexcol(b, "LavaVein", (x, y + h * (0.3 + 0.25 * k), z), d + 0.8, 2, sk.LAVA, "CrackedLava", collide=False)


# ===================================================================== 9. Frostbite
def mountain(b, c, R, H, rng, sk):
    """A snowy massif: a faceted main peak and shoulder peaks, snow caps set at a twist so their edges break jagged
    across the rock, boulders round the foot."""
    x, y, z = c
    rock, rock2 = (112, 122, 138), (96, 104, 120)

    def peak(px, pz, R_, H_, k0):
        n = 9
        rot = rng.random()
        wcone(b, "Rock", (px, y, pz), H_, R_, rock if k0 % 2 == 0 else rock2, "Slate", n=n, rot=rot)
        f = rng.uniform(0.4, 0.5)
        wcone(b, "Snow", (px, y + H_ * (1 - f) - 2, pz), H_ * f + 4, R_ * f * 1.08 + 3, sk.SNOW, "Snow", n=n,
              rot=rot + math.pi / n)

    peak(x, z, R, H, 0)
    for k in range(4):
        a = TAU * k / 4 + rng.uniform(-0.3, 0.3)
        d = R * rng.uniform(0.55, 0.75)
        peak(x + math.cos(a) * d, z + math.sin(a) * d, R * rng.uniform(0.45, 0.6), H * rng.uniform(0.45, 0.65), k + 1)
    for k in range(18):
        a = rng.random() * TAU
        d = R * rng.uniform(0.85, 1.1)
        ell(b, "Boulder", (x + math.cos(a) * d, y + rng.uniform(10, 40), z + math.sin(a) * d),
            (rng.uniform(60, 140), rng.uniform(40, 90), rng.uniform(60, 140)), rock2, "Slate", parent=b.scenery,
            rot=CF((0, 0, 0)) * rot_y(rng.random() * 3))


def pine(b, base, h, rng):
    """A snowy pine: four faceted tiers, each with snow on its shoulders."""
    x, y, z = base
    C(b, "PineTrunk", (x, y + h * 0.1, z), h * 0.2, h * 0.07, (96, 64, 42), "Wood")
    rot = rng.random()
    for k in range(4):
        y0 = y + h * (0.14 + 0.19 * k)
        r = h * (0.31 - 0.06 * k)
        wcone(b, "Pine", (x, y0, z), h * 0.36, r, (34 + 6 * k, 96 + 8 * k, 66), "Grass", n=8, rot=rot + 0.3 * k)
        wcone(b, "PineSnow", (x, y0 + h * 0.36 * 0.55, z), h * 0.36 * 0.45 + 1.5, r * 0.45 + 1.5, (246, 250, 255), "Snow", n=8,
              rot=rot + 0.3 * k + math.pi / 8)

# ===================================================================== 10. High Score
def cabinet(b, c, W, H, D, sk, yaw=0.0):
    """A classic arcade cabinet facing its -Z: tilted screen with a ghost, lit marquee, joystick and buttons."""
    L = Local(c, yaw)
    body, trim = (30, 24, 52), sk.NEON[0]
    P(b, "CabinetBase", L.cf_at(0, H * 0.22, 0), (W, H * 0.44, D), body)
    P(b, "CabinetTop", L.cf_at(0, H * 0.72, D * 0.12), (W, H * 0.56, D * 0.76), body)
    P(b, "ControlPanel", L.cf_at(0, H * 0.47, -D * 0.52, rot_axis((1, 0, 0), 0.28)), (W * 0.98, H * 0.05, D * 0.32), (44, 38, 70))
    P(b, "ScreenBezel", L.cf_at(0, H * 0.7, -D * 0.27, rot_axis((1, 0, 0), -0.12)), (W * 0.86, H * 0.38, 2), (16, 14, 26))
    P(b, "Screen", L.cf_at(0, H * 0.7, -D * 0.27 - 1.2, rot_axis((1, 0, 0), -0.12)), (W * 0.74, H * 0.3, 0.6), (14, 40, 70), "Neon")
    nrm = L.cf.vec((0, math.sin(0.12), -math.cos(0.12)))
    pixel_art(b, L.at(0, H * 0.7, -D * 0.27 - 1.6), nrm, L.cf.vec((0, math.cos(0.12), math.sin(0.12))), GHOST, W * 0.035,
              sk.NEON[0], "Neon", b.scenery, th=0.4, name="ScreenGhost")
    P(b, "Marquee", L.cf_at(0, H * 0.96, D * 0.08), (W * 1.04, H * 0.1, D * 0.86), body)
    P(b, "MarqueeGlow", L.cf_at(0, H * 0.96, -D * 0.35 - 0.4), (W * 0.94, H * 0.07, 0.6), trim, "Neon")
    stick = L.at(-W * 0.22, H * 0.5, -D * 0.55)
    cyl(b, "Joystick", add(stick, (0, H * 0.04, 0)), H * 0.08, W * 0.025, (30, 30, 36), "SmoothPlastic", b.scenery)
    ball(b, "JoystickBall", add(stick, (0, H * 0.09, 0)), W * 0.06, sk.NEON[4], "SmoothPlastic", b.scenery)
    for k in range(4):
        q = L.at(W * (0.02 + k * 0.1), H * 0.495, -D * 0.55)
        cyl(b, "Button", q, H * 0.02, W * 0.05, sk.NEON[k + 1], "Neon", b.scenery)
    P(b, "CoinDoor", L.cf_at(0, H * 0.18, -D / 2 - 0.4), (W * 0.3, H * 0.16, 0.8), (50, 44, 80))
    for k in (-1, 1):
        P(b, "CoinSlot", L.cf_at(k * W * 0.07, H * 0.2, -D / 2 - 0.9), (W * 0.05, H * 0.03, 0.4), (255, 80, 60), "Neon")
    for sx in (-1, 1):
        P(b, "SideStripe", L.cf_at(sx * (W / 2 + 0.4), H * 0.55, 0), (0.6, H * 0.08, D * 0.9), sk.NEON[1], "Neon")
        P(b, "SideStripe2", L.cf_at(sx * (W / 2 + 0.4), H * 0.42, 0), (0.6, H * 0.03, D * 0.9), sk.NEON[2], "Neon")


def coin(b, c, d, axis=(0, 0, 1)):
    cyl(b, "Coin", c, d * 0.12, d, (255, 210, 40), "Metal", b.scenery, axis=axis, refl=0.3)
    cyl(b, "CoinRim", c, d * 0.14, d * 0.78, (255, 230, 120), "Neon", b.scenery, axis=axis)


GHOST = ["0011100", "0111110", "1101011", "1111111", "1111111", "1010101"]


def ghost(b, c, px, col, normal=(0, 0, -1)):
    from skins import pixel_art
    pixel_art(b, c, normal, (0, 1, 0), GHOST, px, col, "Neon", parent=b.scenery, th=2.0, name="Ghost")


def clock_tower(b, base, W, top_y, sk, rng):
    """A tall clock tower: panelled shaft with brass pilasters and bands, four clock faces, a stepped roof and spire.
    base = bottom centre; the clock faces sit just under top_y."""
    x, y, z = base
    H = top_y - y
    wood, brass, dark = (92, 58, 40), sk.BRASS, sk.DARK
    P(b, "TowerShaft", CF((x, y + H / 2, z)), (W, H, W), wood, "Wood")
    for sx in (-1, 1):
        for sz in (-1, 1):
            P(b, "Pilaster", CF((x + sx * W / 2, y + H / 2, z + sz * W / 2)), (W * 0.12, H, W * 0.12), brass, "Metal")
    k = 1
    while k * 80 < H - W:
        P(b, "TowerBand", CF((x, y + k * 80, z)), (W + 2, 4, W + 2), brass, "Metal")
        k += 1
    # the clock storey
    cy = top_y - W * 0.55
    P(b, "ClockStorey", CF((x, cy, z)), (W * 1.12, W * 1.1, W * 1.12), dark, "Wood")
    for k in range(4):
        a = TAU * k / 4
        n = (math.cos(a), 0.0, math.sin(a))
        fc = (x + n[0] * (W * 0.56 + 1.5), cy, z + n[2] * (W * 0.56 + 1.5))
        cyl(b, "ClockBezel", fc, 2.0, W * 0.92, brass, "Metal", b.scenery, axis=n)
        cyl(b, "ClockFace", add(fc, mul(n, 1.3)), 0.6, W * 0.8, sk.FACE, "SmoothPlastic", b.scenery, axis=n)
        fr = axis_frame(fc, n)
        for t in range(12):
            th = TAU * t / 12
            d = add(mul(fr.y, math.cos(th)), mul(fr.z, math.sin(th)))
            q = add(add(fc, mul(n, 1.8)), mul(d, W * 0.33))
            Pt(b, "ClockTick", CF(q, n, d, cross(n, d)), (0.4, W * (0.07 if t % 3 == 0 else 0.04), W * 0.025), sk.INK,
               "SmoothPlastic", b.scenery)
        for (L_, w_, th) in ((W * 0.3, W * 0.03, 0.9 + k), (W * 0.2, W * 0.045, 2.6 + k * 0.7)):
            d = add(mul(fr.y, math.cos(th)), mul(fr.z, math.sin(th)))
            q = add(add(fc, mul(n, 2.2)), mul(d, L_ / 2))
            Pt(b, "ClockHand", CF(q, n, d, cross(n, d)), (0.4, L_, w_), sk.INK, "SmoothPlastic", b.scenery)
        ball(b, "ClockPin", add(fc, mul(n, 2.4)), W * 0.05, brass, "Metal", b.scenery)
    # stepped roof and spire
    ry = cy + W * 0.55
    for k in range(6):
        w_ = W * (1.2 - 0.18 * k)
        P(b, "TowerRoof", CF((x, ry + 7 + k * 14, z)), (w_, 14, w_), (60, 70, 110) if k % 2 == 0 else (70, 82, 126), "Slate")
    cyl(b, "Spire", (x, ry + 100 + 30, z), 60, 6, brass, "Metal", b.scenery)
    ball(b, "SpireBall", (x, ry + 165, z), 14, brass, "Metal", b.scenery)
