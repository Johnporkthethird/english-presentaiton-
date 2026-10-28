"""The obstacle library. Every section starts and ends level, heading +X, at the builder state."""
import math
from geom import CF, deck_frame, look_frame, axis_frame, add, sub, mul, unit, length, lerp, rot_axis, UP
from builder import THICK, G, CAR_UP, mix

TAU = math.pi * 2


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease5(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (6 * t - 15) + 10)


def ease5dd(t):
    """second derivative of ease5"""
    return 60 * t * (2 * t - 1) * (t - 1)


class St:
    def __init__(self, x, y, z, w, zc):
        self.x, self.y, self.z, self.w = x, y, z, w
        self.zc = zc

    def dz_pick(self, rng, lo, hi):
        mag = rng.uniform(lo, hi)
        off = self.z - self.zc
        if off > 260:
            s = -1
        elif off < -260:
            s = 1
        else:
            s = rng.choice([-1, 1])
        return s * mag


def connect(b, st, L, y1=None, z1=None, w1=None, **kw):
    y0, z0, w0, x0 = st.y, st.z, st.w, st.x
    y1 = y0 if y1 is None else y1
    z1 = z0 if z1 is None else z1
    w1 = w0 if w1 is None else w1
    b.road(x0, x0 + L, lambda x: y0 + (y1 - y0) * ease((x - x0) / L), lambda x: z0 + (z1 - z0) * ease((x - x0) / L),
           lambda x: w0 if x < x0 + L / 2 else w1, **kw)  # one clean step, not a saw-tooth taper
    st.x, st.y, st.z, st.w = x0 + L, y1, z1, w1


def lead(b, st, w=None, L=50, boost=False):
    """A short flat lead-in with the section's checkpoint (and a boost strip to carry speed in)."""
    w = w or st.w
    connect(b, st, L + (50 if boost else 0), w1=w)
    b.checkpoint(st.x - L - (50 if boost else 0) + 22, st.y, st.z, w)
    if boost:
        b.boost(st.x - 35, st.y, st.z)


def fwd_of(a, c):
    return unit((c[0] - a[0], 0, c[2] - a[2]))


def accent(b, name, cf, size, color=None, parent=None, mat="Neon", transp=0.0):
    return b.part(name, cf, size, color or b.theme["accent"], mat, parent=parent, collide=False, query=False,
                  transp=transp)


def warn_stripes(b, x, y, z, w, n=3, color=None):
    """Chevrons painted on the road just before something nasty."""
    c = color or b.theme["danger"]
    for i in range(n):
        fr = deck_frame((x + i * 7, y + 0.12, z), (1, 0, 0))
        b.part("Warn", fr, (w * 0.8, 0.2, 2.2), c, "Neon", parent=b.roads, collide=False, query=False)


# =====================================================================================
# 1. plain speed
def s_runway(b, st, d, rng):
    w = max(st.w, 54)
    lead(b, st, w)
    x0 = st.x
    connect(b, st, 160)
    for k in range(rng.randint(2, 3)):
        b.boost(x0 + 25 + k * 55, st.y, st.z)
    hill = rng.choice([0, 0, 22, -22])
    connect(b, st, rng.uniform(120, 180), y1=st.y + hill)


# 2. S bend, banked
def s_scurve(b, st, d, rng):
    w = rng.uniform(46, 58) - 10 * d
    lead(b, st, w)
    L = rng.uniform(440, 560)
    dz = st.dz_pick(rng, 160, 260)
    x0, z0, y0 = st.x, st.z, st.y
    dy = rng.uniform(-70, 60)

    def fz(x):
        return z0 + dz * ease5((x - x0) / L)

    def fy(x):
        return y0 + dy * ease5((x - x0) / L)

    def bank(x):
        k = dz * ease5dd((x - x0) / L) / (L * L)
        return max(-0.45, min(0.45, k * 110))
    b.road(x0, x0 + L, fy, fz, lambda x: w, step=10, bank=bank)
    st.x, st.z, st.y = x0 + L, z0 + dz, y0 + dy
    b.boost(st.x - 60, st.y, st.z)


# 3. zigzag of narrow beams with hard corners
def s_zigzag(b, st, d, rng):
    w = 34 - 8 * d + rng.uniform(-2, 2)
    lead(b, st, w)
    legs = rng.randint(4, 6)
    amp = rng.uniform(55, 85) + 25 * d
    pts = [(st.x, st.y, st.z)]
    side = rng.choice([-1, 1])
    zc = st.z
    y = st.y
    for i in range(legs):
        x = pts[-1][0] + rng.uniform(95, 130)
        z = zc + side * amp / 2 if i < legs - 1 else zc
        side = -side
        y = y + rng.uniform(-14, 10) if i < legs - 1 else st.y
        pts.append((x, y, z))
    for a, c in zip(pts, pts[1:]):
        f = fwd_of(a, c)
        L = math.hypot(c[0] - a[0], c[2] - a[2])
        seg = sub(c, a)
        fr = deck_frame(lerp(a, c, 0.5), seg)
        b.slab(fr, w, L + 2)
        b.line(a[0], a[1], a[2])
    for (x, y, z) in pts[1:-1]:
        fr = deck_frame((x, y, z), (1, 0, 0))
        b.slab(fr, w * 1.45, w * 1.45, color=b.theme["accent2"], edge=False)
        b.samples.append((x, y, z, w * 1.4))
    for (x, y, z) in pts:
        b.samples.append((x, y, z, w))
    st.x, st.y, st.z = pts[-1]
    st.w = w
    connect(b, st, 40)


# 4. long narrow beam that weaves
def s_beam(b, st, d, rng):
    w = 30 - 7 * d + rng.uniform(-2, 2)
    lead(b, st, w, boost=True)
    L = rng.uniform(420, 600)
    A = rng.uniform(16, 32) + 10 * d
    lam = rng.uniform(170, 260)
    Ay = rng.uniform(0, 14)
    x0, z0, y0 = st.x, st.z, st.y
    b.road(x0, x0 + L, lambda x: y0 + Ay * math.sin(TAU * (x - x0) / (lam * 1.7)) * math.sin(math.pi * (x - x0) / L),
           lambda x: z0 + A * math.sin(TAU * (x - x0) / lam) * math.sin(math.pi * (x - x0) / L),
           lambda x: w, step=8)
    st.x = x0 + L


# 5. gap jumps (the jump key)
def s_gaps(b, st, d, rng):
    w = rng.uniform(40, 50) - 6 * d
    lead(b, st, w, boost=True)
    n = 3
    x, y, z = st.x, st.y, st.z
    connect(b, st, 50)
    warn_stripes(b, st.x - 30, st.y, st.z, w)
    x, y, z = st.x, st.y, st.z
    for i in range(n):
        gap = rng.uniform(62, 80) + 22 * d
        plat = 272 - gap + rng.uniform(0, 20)
        ny = y + rng.uniform(-16, 14) if i < n - 1 else st.y
        nz = z + rng.uniform(-4, 4) if i < n - 1 else st.z
        b.jump_arc(x, y, z, x + gap, ny, nz)
        x2 = x + gap
        b.flat(x2, x2 + plat, ny, nz, w, line=True)
        # lip lights on the take-off edge
        accent(b, "Lip", deck_frame((x2 + plat - 1.2, ny + 0.3, nz), (1, 0, 0)), (w, 0.6, 2.4), b.theme["danger"])
        x, y, z = x2 + plat, ny, nz
    st.x, st.y, st.z = x, y, z
    connect(b, st, 40, z1=st.z)


# 6. kicker ramp + big air
def s_kicker(b, st, d, rng):
    w = max(st.w, 48)
    lead(b, st, w)
    connect(b, st, 120)
    b.boost(st.x - 90, st.y, st.z)
    b.boost(st.x - 40, st.y, st.z)
    # the wedge
    rh, rl = 16.0, 50.0
    x0 = st.x
    fr = deck_frame((x0 + rl / 2, st.y + rh / 2, st.z), (1, 0, 0))
    b.part("Kicker", fr, (w, rh, rl), b.theme["accent2"], b.theme["road_mat"], parent=b.roads, cls="WedgePart")
    for s in (-1, 1):
        accent(b, "KickerEdge", deck_frame((x0 + rl / 2, st.y + rh / 2 + 0.5, st.z + s * (w / 2 - 0.8)), (rl, rh, 0)),
               (1.6, 0.8, math.hypot(rl, rh)))
    b.samples.append((x0 + rl, st.y + rh, st.z, w))
    for k in range(1, 4):
        b.line(x0 + rl * k / 4, st.y + rh * k / 4, st.z)
    gap = rng.uniform(220, 300) + 60 * d
    land_y = st.y + rng.uniform(-90, 10)
    land_z = st.z + st.dz_pick(rng, 0, 60)
    start = (x0 + rl - 6, st.y + rh, st.z)
    target = (x0 + rl + gap, land_y, land_z)
    b.launch(start, target, apex=max(40, target[1] - start[1] + 45) + 30 * d, visual=False)
    # landing: a long apron that eases to flat
    lx = target[0] - 60
    b.flat(lx, lx + 200, land_y, land_z, w + 10)
    st.x, st.y, st.z, st.w = lx + 200, land_y, land_z, w


# 7. island hopping on exact launch pads
def s_islands(b, st, d, rng):
    w = max(st.w, 46)
    lead(b, st, w)
    connect(b, st, 60)
    n = rng.randint(2, 3)
    x, y, z = st.x, st.y, st.z
    src = (x - 15, y, z)
    for i in range(n + 1):
        last = i == n
        D = rng.uniform(180, 240) + 40 * d
        ny = (y + rng.uniform(-60, 50)) if not last else y + rng.uniform(-40, 20)
        nz = st.z + st.dz_pick(rng, 0, 140) if not last else z + rng.uniform(-30, 30)
        tx = src[0] + D
        tgt = (tx, ny, nz)
        b.launch(src, tgt, apex=max(ny - src[1], 0) + rng.uniform(45, 85))
        if last:
            b.flat(tx - 50, tx + 170, ny, nz, w + 6)
            x, y, z = tx + 170, ny, nz
            break
        isl = rng.uniform(85, 105) - 10 * d
        iw = rng.uniform(46, 58) - 8 * d
        b.flat(tx - isl * 0.4, tx + isl * 0.6, ny, nz, iw)
        island_skirt(b, tx + isl * 0.1, ny, nz, isl, iw)
        src = (tx + isl * 0.45, ny, nz)
        x, y, z = tx + isl * 0.6, ny, nz
    st.x, st.y, st.z, st.w = x, y, z, w


def island_skirt(b, x, y, z, L, w):
    th = b.theme
    for k in range(3):
        s = 1 - 0.28 * (k + 1)
        b.part("Rock", CF((x, y - THICK - 6 - k * 9, z)), (L * s, 10, w * s), mix(th["deco"], (0, 0, 0), 0.25 * k),
               th.get("rock_mat", "Slate"), collide=False, query=False)
    b.part("IslandGlow", CF((x, y - THICK - 1, z)), (L + 2, 1.2, w + 2), th["edge"], "Neon", collide=False, query=False,
           transp=0.3)


# 8. drop-down stairs
def s_stairs(b, st, d, rng):
    w = rng.uniform(44, 54)
    lead(b, st, w)
    n = rng.randint(3, 4)
    x, y, z = st.x, st.y, st.z
    for i in range(n):
        drop = rng.uniform(30, 48)
        gap = rng.uniform(0, 26) + 18 * d
        L = rng.uniform(130, 165)
        nz = z + rng.uniform(-24, 24)
        nw = max(26, w - 4 * i - 6 * d)
        x2 = x + gap
        # the line: a roll off the edge
        b.arc((x, y + CAR_UP, z), (115, 0, (nz - z) * 115 / max(gap + 60, 1)), until_y=y - drop + CAR_UP)
        b.flat(x2, x2 + L, y - drop, nz, nw)
        accent(b, "StepLip", deck_frame((x2 + L - 1.5, y - drop + 0.3, nz), (1, 0, 0)), (nw, 0.6, 3), b.theme["danger"])
        x, y, z = x2 + L, y - drop, nz
    st.x, st.y, st.z, st.w = x, y, z, w
    connect(b, st, 50, w1=w)


# 9. climb: steep ramps, ledges and jump-ups
def s_climb(b, st, d, rng):
    w = rng.uniform(42, 54)
    lead(b, st, w)
    n = 2
    for i in range(n):
        b.boost(st.x + 25, st.y, st.z)
        connect(b, st, 60)
        rise = rng.uniform(36, 56)
        connect(b, st, rise / math.tan(math.radians(rng.uniform(11, 14))), y1=st.y + rise)
        connect(b, st, 50)
        if rng.random() < 0.55 + 0.3 * d:
            gap = rng.uniform(55, 75) + 20 * d
            up = rng.uniform(8, 20)
            b.jump_arc(st.x, st.y, st.z, st.x + gap, st.y + up, st.z)
            warn_stripes(b, st.x - 25, st.y, st.z, w)
            st.x += gap
            st.y += up
            b.flat(st.x, st.x + 175, st.y, st.z, w)
            st.x += 175


# 10. camelback hills
def s_hills(b, st, d, rng):
    w = rng.uniform(34, 42) - 4 * d
    lead(b, st, w, boost=True)
    n = 3
    lam = rng.uniform(210, 260)
    A = min(rng.uniform(26, 34) + 8 * d, 0.38 * lam / math.pi)
    x0, y0, z0 = st.x, st.y, st.z
    L = n * lam
    wig = rng.uniform(0, 30)
    b.road(x0, x0 + L, lambda x: y0 + A * 0.5 * (1 - math.cos(TAU * (x - x0) / lam)),
           lambda x: z0 + wig * math.sin(TAU * (x - x0) / (lam * 2)), lambda x: w, step=8)
    st.x = x0 + L


# 11. banked sweepers
def s_banked(b, st, d, rng):
    w = rng.uniform(44, 54)
    lead(b, st, w, boost=True)
    legs = 2
    for i in range(legs):
        L = rng.uniform(280, 340)
        dz = st.dz_pick(rng, 170, 260)
        x0, z0, y0 = st.x, st.z, st.y
        dy = rng.uniform(-50, 40)

        def bank(x, x0=x0, L=L, dz=dz):
            return max(-0.55, min(0.55, dz * ease5dd((x - x0) / L) / (L * L) * 220))
        b.road(x0, x0 + L, lambda x, x0=x0, y0=y0, dy=dy, L=L: y0 + dy * ease5((x - x0) / L),
               lambda x, x0=x0, z0=z0, dz=dz, L=L: z0 + dz * ease5((x - x0) / L), lambda x: w, step=9, bank=bank,
               rails=(i % 2 == 0))
        st.x, st.z, st.y = x0 + L, z0 + dz, y0 + dy


# 12. half-pipe with blockers
def s_halfpipe(b, st, d, rng):
    floor = 26.0
    lead(b, st, 60)
    L = rng.uniform(420, 560)
    x0, y0, z0 = st.x, st.y, st.z
    wall = [(12.0, math.radians(24)), (12.0, math.radians(40)), (12.0, math.radians(52))]
    b.road(x0, x0 + L, lambda x: y0, lambda x: z0, lambda x: floor, step=400)
    for side in (-1, 1):  # deck X is -Z: side +1 = deck-left = world -Z
        q, h = floor / 2, 0.0
        for (sw, a) in wall:
            cq = q + math.cos(a) * sw / 2
            ch = h + math.sin(a) * sw / 2
            zz = z0 - side * cq
            b.road(x0, x0 + L, lambda x, ch=ch: y0 + ch, lambda x, zz=zz: zz, lambda x: sw + 0.6, step=400,
                   bank=lambda x, a=a, side=side: side * a, line=False, edge=False,
                   style={"color": mix(b.theme["road"], b.theme["accent2"], 0.25)})
            q += math.cos(a) * sw
            h += math.sin(a) * sw
        accent(b, "PipeLip", CF((x0 + L / 2, y0 + h + 0.6, z0 - side * (q + 0.5))), (L, 1.2, 1.4), b.theme["edge"])
    # blockers on the floor and the low wall, alternating sides
    n = int(L // 95)
    for i in range(n):
        x = x0 + 70 + i * (L - 100) / max(n - 1, 1)
        side = 1 if i % 2 == 0 else -1
        zz = z0 - side * 10
        b.part("Blocker", CF((x, y0 + 5, zz)), (10, 10, 34), b.theme["danger"], "Neon", parent=b.hazards,
               collide=False, query=True, attrs={"ObbyHazard": "Knock"})
    st.x = x0 + L
    st.w = 60
    connect(b, st, 40, w1=50)


# 13. spinning bars
def s_spinners(b, st, d, rng):
    w = rng.uniform(70, 86)
    lead(b, st, w)
    n = rng.randint(3, 4)
    gapx = rng.uniform(105, 135)
    L = n * gapx + 40
    x0 = st.x
    connect(b, st, L)
    kind = "Crush" if d > 0.55 else "Knock"
    for i in range(n):
        x = x0 + 60 + i * gapx
        root = b.prop_root("Spinner")
        speed = (rng.uniform(0.22, 0.34) + 0.12 * d) * (1 if i % 2 == 0 else -1)
        rig = b.rig(root, "Spin", axis_frame((x, st.y + 4, st.z), UP), speed, 4, phase=rng.random())
        arms = rng.choice([2, 3])
        R = w / 2 + 2
        for k in range(arms):
            a = TAU * k / arms
            dvec = (math.cos(a), 0, math.sin(a))
            c = add((x, st.y + 4.5, st.z), mul(dvec, R / 2 + 3))
            fr = deck_frame(c, dvec)
            b.part("SpinBar", fr, (3.5, 6, R - 6), b.theme["danger"], "Neon", parent=rig, collide=False, query=True,
                   attrs={"ObbyHazard": kind})
        b.part("Hub", axis_frame((x, st.y + 6, st.z), UP), (12, 12, 12), b.theme["metal"], "Metal", parent=rig,
               collide=False, query=True, shape=2, attrs={"ObbyHazard": kind})


# 14. pendulum hammers
def s_hammers(b, st, d, rng):
    w = rng.uniform(40, 48)
    lead(b, st, w)
    n = rng.randint(3, 5)
    sp = rng.uniform(85, 110)
    L = n * sp + 60
    x0 = st.x
    connect(b, st, L)
    H = 64.0
    theta = math.radians(rng.uniform(50, 62))
    period = rng.uniform(2.6, 3.3) - 0.5 * d
    kind = "Crush" if d > 0.6 else "Knock"
    for i in range(n):
        x = x0 + 60 + i * sp
        pivot = (x, st.y + H, st.z)
        # frame beam overhead
        for s in (-1, 1):
            b.part("HammerPost", CF((x, st.y + H / 2, st.z + s * (w / 2 + 6))), (5, H + 8, 5), b.theme["metal"], "Metal",
                   collide=True)
        b.part("HammerBeam", CF((x, st.y + H + 4, st.z)), (6, 6, w + 18), b.theme["metal"], "Metal", collide=False)
        root = b.prop_root("Hammer")
        rig = b.rig(root, "Hinge", axis_frame(pivot, (1, 0, 0)), -2 * math.degrees(theta), period,
                    phase=(i * rng.choice([0.25, 0.5, 0.33])) % 1, name="Swing")
        R = rot_axis((1, 0, 0), theta)
        arm_c = R.vec((0, -(H - 14) / 2, 0))
        head_c = R.vec((0, -(H - 9), 0))
        b.part("Arm", CF(add(pivot, arm_c), R.x, R.y, R.z), (2.5, H - 14, 2.5), b.theme["metal"], "Metal", parent=rig,
               collide=False)
        b.part("Head", CF(add(pivot, head_c), R.x, R.y, R.z), (16, 14, 26), b.theme["danger"], b.theme.get("hazard_mat", "Metal"),
               parent=rig, collide=False, query=True, attrs={"ObbyHazard": kind})


# 15. side pushers
def s_pistons(b, st, d, rng):
    w = rng.uniform(36, 44)
    lead(b, st, w)
    n = rng.randint(4, 6)
    sp = rng.uniform(70, 90)
    L = n * sp + 60
    x0 = st.x
    connect(b, st, L, edge=True)
    period = rng.uniform(2.2, 2.8) - 0.4 * d
    for i in range(n):
        x = x0 + 50 + i * sp
        side = 1 if i % 2 == 0 else -1
        depth = w * 0.75
        rest = (x, st.y + 8, st.z + side * (w / 2 + depth / 2 + 1))
        root = b.prop_root("Pusher")
        rig = b.rig(root, "Slide", axis_frame(rest, (0, 0, -side)), depth + 2, period, phase=(i * 0.21) % 1,
                    keys="0:0 0.35:0 0.45:1 0.62:1 0.92:0", name="Ram")
        b.part("Ram", CF(rest), (26, 14, depth), b.theme["danger"], b.theme.get("hazard_mat", "Metal"), parent=rig,
               collide=False, query=True, attrs={"ObbyHazard": "Knock"})
        b.part("RamFace", CF(add(rest, (0, 0, -side * (depth / 2 + 0.3)))), (26.4, 14.4, 0.6), b.theme["edge"], "Neon",
               parent=rig, collide=False, query=False)
        b.part("RamHousing", CF(add(rest, (0, 0, side * (depth / 2 + 4)))), (32, 22, 8), b.theme["metal"], "Metal",
               collide=False)


# 16. crushers from above
def s_crushers(b, st, d, rng):
    w = rng.uniform(40, 48)
    lead(b, st, w)
    n = rng.randint(3, 5)
    sp = rng.uniform(70, 95)
    L = n * sp + 70
    x0 = st.x
    connect(b, st, L)
    H = 42.0
    period = rng.uniform(2.0, 2.6) - 0.3 * d
    dph = rng.choice([0.16, 0.2, 0.25])
    for i in range(n):
        x = x0 + 60 + i * sp
        blen = rng.uniform(26, 34)
        rest = (x, st.y + H + 9, st.z)
        for s in (-1, 1):
            b.part("CrusherRail", CF((x, st.y + H / 2 + 10, st.z + s * (w / 2 + 4))), (4, H + 30, 4), b.theme["metal"],
                   "Metal", collide=True)
        b.part("CrusherTop", CF((x, st.y + H + 34, st.z)), (blen + 6, 6, w + 14), b.theme["metal"], "Metal", collide=False)
        root = b.prop_root("Crusher")
        rig = b.rig(root, "Slide", axis_frame(rest, (0, -1, 0)), H + 1, period, phase=(i * dph) % 1,
                    keys="0:0 0.42:0 0.5:1 0.68:1 0.96:0", name="Press")
        b.part("Press", CF(rest), (blen, 18, w + 6), b.theme["metal"], "DiamondPlate", parent=rig, collide=False,
               query=True, attrs={"ObbyHazard": "Crush"})
        b.part("PressGlow", CF(add(rest, (0, -9.2, 0))), (blen + 0.4, 0.6, w + 6.4), b.theme["danger"], "Neon",
               parent=rig, collide=False, query=False)


# 17. timed laser gates
def s_lasers(b, st, d, rng):
    w = rng.uniform(40, 50)
    lead(b, st, w)
    n = rng.randint(5, 7)
    sp = rng.uniform(55, 75)
    L = n * sp + 60
    x0 = st.x
    connect(b, st, L)
    period = rng.uniform(1.8, 2.4)
    on = period * (0.42 + 0.12 * d)
    v = rng.uniform(95, 150)
    for i in range(n):
        x = x0 + 50 + i * sp
        phase = (-(x - x0) / v / period) % 1  # the open window travels at v: ride it
        full = rng.random() < 0.45 + 0.3 * d
        for s in (-1, 1):
            b.part("LaserPost", CF((x, st.y + 20, st.z + s * (w / 2 + 3))), (4, 40, 4), b.theme["metal"], "Metal",
                   collide=True)
            b.part("Emitter", CF((x, st.y + 20, st.z + s * (w / 2 + 0.6))), (2, 38, 1), b.theme["danger"], "Neon",
                   collide=False, query=False, transp=0.2)
        beams = [(3.2, 3.0)] if not full else [(4 + 7 * k, 2.2) for k in range(5)]
        for (hy, th) in beams:
            b.part("Laser", CF((x, st.y + hy, st.z)), (1.6, th, w + 4), b.theme["danger"], "Neon", parent=b.hazards,
                   collide=False, query=True, transp=0.15,
                   attrs={"ObbyHazard": "Zap", "ZapFX": True, "ZapPeriod": period, "ZapOn": on, "ZapPhase": phase})


# 18. sweeping floor lasers (jump them or time them)
def s_sweepers(b, st, d, rng):
    w = rng.uniform(48, 58)
    lead(b, st, w)
    n = rng.randint(3, 4)
    sp = rng.uniform(120, 150)
    L = n * sp + 40
    x0 = st.x
    connect(b, st, L)
    for i in range(n):
        x = x0 + 70 + i * sp
        side = 1 if i % 2 == 0 else -1
        hub = (x, st.y, st.z + side * (w / 2 + 8))
        b.part("SweepHub", axis_frame(add(hub, (0, 5, 0)), UP), (10, 14, 14), b.theme["metal"], "Metal", collide=True, shape=2)
        root = b.prop_root("Sweeper")
        speed = (rng.uniform(0.28, 0.4) + 0.12 * d) * rng.choice([-1, 1])
        rig = b.rig(root, "Spin", axis_frame(add(hub, (0, 3, 0)), UP), speed, 4, phase=rng.random())
        R = w + 12
        fr = deck_frame(add(hub, (0, 3.2, -side * R / 2)), (0, 0, -side))
        b.part("SweepBeam", fr, (1.8, 3.2, R), b.theme["danger"], "Neon", parent=rig, collide=False, query=True,
               transp=0.1, attrs={"ObbyHazard": "Burn"})


# 19. crumbling floor
def s_crumble(b, st, d, rng):
    w = rng.uniform(34, 42)
    lead(b, st, w, boost=True)
    n = rng.randint(12, 15)
    tl = rng.uniform(34, 40)
    x, y, z = st.x, st.y, st.z
    delay = 0.42 - 0.18 * d
    zs = z
    gap_at = rng.randint(3, max(3, n - 8)) if d > 0.3 else -1
    for i in range(n):
        if i == gap_at:
            g = rng.uniform(30, 45)
            b.jump_arc(x, y, zs, x + g, y, zs)
            x += g
        zs = z + (9 * math.sin(i * 0.9) if abs(i - gap_at) > 2 else 0)
        m = b.model("CrumbleTile", b.hazards, {"ObbyCrumble": float(delay)})
        fr = deck_frame((x + tl / 2, y, zs), (1, 0, 0))
        b.slab(fr, w, tl - 1.0, color=mix(b.theme["road"], b.theme["accent2"], 0.35 if i % 2 else 0.15), parent=m)
        b.samples.append((x + tl / 2, y, zs, w))
        b.line(x + tl / 2, y, zs)
        x += tl
    st.x, st.y, st.z = x, y, z
    connect(b, st, 40)


# 20. sideways conveyor belts
def s_conveyor(b, st, d, rng):
    w = rng.uniform(36, 42)
    lead(b, st, w)
    n = rng.randint(4, 6)
    x = st.x
    for i in range(n):
        L = rng.uniform(70, 95)
        sp = rng.uniform(28, 40) + 18 * d
        side = 1 if i % 2 == 0 else -1
        dirv = (0.0, 0.0, float(side))
        out = b.road(x, x + L, lambda xx: st.y, lambda xx: st.z, lambda xx: w, step=400,
                     style={"color": b.theme["belt"], "mat": "DiamondPlate",
                            "attrs": {"Conveyor": float(sp), "ConveyorDir": ("Vector3",) + dirv}})
        # chevrons pointing the way the belt pushes
        for k in range(3):
            ax = x + 15 + k * (L - 30) / 2
            for off in (-10, 0, 10):
                chevron(b, (ax, st.y + 0.15, st.z + side * off), (0, 0, side), 8, b.theme["accent"])
        x += L
    st.x = x


# 21. ice
def s_ice(b, st, d, rng):
    w = rng.uniform(44, 52)
    lead(b, st, w)
    L = rng.uniform(460, 600)
    x0, z0, y0 = st.x, st.z, st.y
    A = rng.uniform(40, 70)
    lam = rng.uniform(260, 340)
    fz = lambda x: z0 + A * math.sin(TAU * (x - x0) / lam) * math.sin(math.pi * (x - x0) / L)
    fy = lambda x: y0 - 30 * ease((x - x0) / L)
    b.road(x0, x0 + L, fy, fz, lambda x: w, step=10,
           style={"color": (200, 235, 255), "mat": "Ice", "edge": (120, 220, 255), "refl": 0.15})
    # the slip volume, in pieces along the bends
    n = int(L // 40)
    for i in range(n):
        xa = x0 + i * L / n
        xb = xa + L / n
        za, zb = fz(xa), fz(xb)
        ya, yb = fy(xa), fy(xb)
        fr = deck_frame(((xa + xb) / 2, (ya + yb) / 2 + 2.5, (za + zb) / 2), (xb - xa, yb - ya, zb - za))
        b.part("IceSlip", fr, (w, 7, math.hypot(xb - xa, zb - za) + 1), (255, 255, 255), parent=b.hazards, transp=1,
               collide=False, query=True, attrs={"ObbyHazard": "Slip"})
    st.x, st.y = x0 + L, y0 - 30


# 22. pinball bumpers
def s_bumpers(b, st, d, rng):
    w = rng.uniform(76, 92)
    lead(b, st, w)
    L = rng.uniform(380, 480)
    x0 = st.x
    connect(b, st, L)
    rows = int((L - 80) // 52)
    for r in range(rows):
        x = x0 + 60 + r * 52
        cols = 4 if r % 2 == 0 else 3
        for c in range(cols):
            if rng.random() < 0.25:
                continue
            zz = st.z - w / 2 + (c + (0.5 if r % 2 == 0 else 1.0)) * w / (cols + (0 if r % 2 == 0 else 1)) + rng.uniform(-6, 6)
            rad = rng.uniform(7, 10)
            b.part("Bumper", axis_frame((x, st.y + 5, zz), UP), (10, rad * 2, rad * 2), b.theme["danger"], "Neon",
                   parent=b.hazards, collide=False, query=True, shape=2, attrs={"ObbyHazard": "Knock"})
            b.part("BumperCap", axis_frame((x, st.y + 10.4, zz), UP), (0.8, rad * 2 + 2, rad * 2 + 2), b.theme["accent"],
                   "Neon", collide=False, query=False, shape=2)


# 23. retracting bridges
def s_bridges(b, st, d, rng):
    w = rng.uniform(40, 48)
    lead(b, st, w)
    n = rng.randint(2, 4)
    x = st.x
    for i in range(n):
        b.flat(x, x + 90, st.y, st.z, w)
        x += 90
        gap = rng.uniform(70, 90)
        side = rng.choice([-1, 1])
        rest = (x + gap / 2, st.y - THICK / 2, st.z)
        root = b.prop_root("Bridge")
        period = rng.uniform(3.0, 3.8) - 0.6 * d
        rig = b.rig(root, "Slide", axis_frame(rest, (0, 0, side)), w + 8, period, phase=rng.random(),
                    keys="0:0 0.45:0 0.55:1 0.9:1", name="Slide")
        b.part("BridgeDeck", CF(rest), (gap + 2, THICK, w), b.theme["accent2"], b.theme["road_mat"], parent=rig,
               collide=True)
        b.part("BridgeGlow", CF(add(rest, (0, 2.3, 0))), (gap + 2.2, 0.5, w * 0.3), b.theme["edge"], "Neon", parent=rig,
               collide=False, query=False)
        b.samples.append((x + gap / 2, st.y, st.z, w))
        b.line(x, st.y, st.z)
        b.line(x + gap, st.y, st.z)
        warn_stripes(b, x - 26, st.y, st.z, w)
        x += gap
    st.x = x
    connect(b, st, 70)


# 24. the wave road: blocks that ride up and down
def s_wave(b, st, d, rng):
    w = rng.uniform(40, 48)
    lead(b, st, w)
    n = rng.randint(8, 11)
    bl = rng.uniform(34, 42)
    amp = rng.uniform(14, 24) + 8 * d
    period = rng.uniform(2.2, 3.0)
    x = st.x
    for i in range(n):
        rest = (x + bl / 2, st.y - THICK / 2, st.z)
        root = b.prop_root("Piston")
        rig = b.rig(root, "Slide", axis_frame(rest, (0, -1, 0)), amp, period, phase=(i * 0.11) % 1, name="Lift")
        b.part("PistonDeck", CF(rest), (bl - 2, THICK, w), mix(b.theme["road"], b.theme["accent2"], (i % 2) * 0.4),
               b.theme["road_mat"], parent=rig, collide=True)
        b.part("PistonGlow", CF(add(rest, (bl / 2 - 1.2, 2.2, 0))), (1.6, 0.5, w), b.theme["edge"], "Neon", parent=rig,
               collide=False, query=False)
        b.part("PistonShaft", CF(add(rest, (0, -30, 0))), (bl * 0.5, 56, w * 0.5), b.theme["metal"], "Metal",
               parent=rig, collide=False, query=False)
        b.samples.append((x + bl / 2, st.y - amp, st.z, w))
        b.line(x + bl / 2, st.y, st.z)
        x += bl
    st.x = x
    connect(b, st, 50)


# 25. the turntable with holes
def s_turntable(b, st, d, rng):
    R = rng.uniform(80, 100)
    lead(b, st, 44)
    connect(b, st, 30)
    c = (st.x + R, st.y, st.z)
    root = b.prop_root("Turntable")
    rig = b.rig(root, "Spin", axis_frame(c, UP), (rng.uniform(0.07, 0.1) + 0.04 * d) * rng.choice([-1, 1]), 4,
                phase=rng.random())
    k = 12
    holes = set(rng.sample([1, 2, 3, 4, 7, 8, 9, 10], 3 + (1 if d > 0.5 else 0)))
    for i in range(k):
        if i in holes:
            continue
        a = TAU * (i + 0.5) / k
        dv = (math.cos(a), 0, math.sin(a))
        mid = add(c, mul(dv, R / 2 + 6))
        fr = deck_frame(add(mid, (0, -THICK / 2, 0)), dv)
        b.part("Sector", fr, (2 * R * math.sin(math.pi / k) + 1, THICK, R - 12),
               mix(b.theme["road"], b.theme["accent2"], 0.3 * (i % 2)), b.theme["road_mat"], parent=rig, collide=True)
        rim = add(c, mul(dv, R - 1))
        b.part("SectorRim", deck_frame(add(rim, (0, 0.3, 0)), (-dv[2], 0, dv[0])), (2, 0.6, 2 * R * math.sin(math.pi / k)),
               b.theme["edge"], "Neon", parent=rig, collide=False, query=False)
    b.part("Hub", axis_frame(add(c, (0, -THICK / 2, 0)), UP), (THICK, 26, 26), b.theme["accent"], "Neon", collide=True, shape=2)
    for xx in (c[0] - R / 2, c[0] + R / 2):
        b.samples.append((xx, st.y, st.z, 2 * R))
    b.line(c[0] - R, st.y, st.z)
    b.line(c[0], st.y, st.z)
    b.line(c[0] + R, st.y, st.z)
    b.part("TableSkirt", axis_frame(add(c, (0, -14, 0)), UP), (8, 2 * R + 6, 2 * R + 6), b.theme["metal"], "Metal",
           collide=False, query=False, shape=2)
    st.x = c[0] + R
    connect(b, st, 50)


# 26. windmills across the road
def s_windmills(b, st, d, rng):
    w = rng.uniform(40, 46)
    lead(b, st, w)
    n = rng.randint(2, 3)
    sp = rng.uniform(140, 170)
    L = n * sp + 40
    x0 = st.x
    connect(b, st, L)
    for i in range(n):
        x = x0 + 80 + i * sp
        Rb = 46.0
        hub = (x, st.y + Rb + 2, st.z)
        for s in (-1, 1):
            b.part("MillTower", CF((x + 10, st.y + Rb / 2, st.z + s * (w / 2 + 8))), (6, Rb + 6, 6), b.theme["metal"],
                   "Metal", collide=True)
        b.part("MillAxle", axis_frame((x + 10, hub[1], st.z), (0, 0, 1)), (w + 22, 5, 5), b.theme["metal"], "Metal",
               collide=False, shape=2)
        root = b.prop_root("Windmill")
        rig = b.rig(root, "Spin", axis_frame(hub, (1, 0, 0)), (rng.uniform(0.18, 0.26) + 0.08 * d) * rng.choice([-1, 1]),
                    4, phase=rng.random())
        blades = rng.choice([3, 4])
        for k in range(blades):
            a = TAU * k / blades
            dv = (0, math.cos(a), math.sin(a))
            cen = add(hub, mul(dv, Rb / 2 + 2))
            fr = deck_frame(cen, dv, up=(1, 0, 0))
            b.part("Blade", fr, (8, 4, Rb - 2), b.theme["danger"], "Neon", parent=rig, collide=False, query=True,
                   attrs={"ObbyHazard": "Crush"})
        b.part("MillHub", axis_frame(hub, (1, 0, 0)), (6, 12, 12), b.theme["accent"], "Metal", parent=rig, collide=False,
               shape=2)


# 27. the floor is lava: stepping stones
def s_lava(b, st, d, rng):
    w = 44
    lead(b, st, w)
    connect(b, st, 30)
    L = rng.uniform(420, 540)
    x0, y0, z0 = st.x, st.y, st.z
    lava_top = y0 - 6
    span = 150
    b.part("LavaPool", CF((x0 + L / 2, lava_top - 2, z0)), (L, 4, span), b.theme.get("lava", (255, 90, 20)), "Neon",
           collide=False, query=False)
    b.part("LavaHeat", CF((x0 + L / 2, lava_top + 1.5, z0)), (L, 3, span), (255, 120, 40), parent=b.hazards,
           transp=1, collide=False, query=True, attrs={"ObbyHazard": "Burn"})
    sw = rng.uniform(28, 34) - 5 * d
    stone = {"color": b.theme.get("stone", (60, 52, 50)), "mat": "Basalt"}
    A = rng.uniform(26, 40)
    lam = rng.uniform(150, 210)
    gx = [x0 + L * 0.42]

    def fz(x):
        # straight (and on the centre line) for a stretch either side of each jump
        env = min([1.0] + [ease((g - 110 - x) / 90) if x < g else ease((x - g - 300) / 90) for g in gx])
        return z0 + A * math.sin(TAU * (x - x0) / lam) * env
    x = x0
    for k, g0 in enumerate(gx + [x0 + L]):
        b.road(x, g0, lambda xx: y0, fz, lambda xx: sw, step=8, style=stone)
        b.part("Causeway", CF(((x + g0) / 2, lava_top - 3, z0)), (g0 - x, 6, 2 * A + sw), (36, 30, 28), "Basalt",
               collide=False, query=False, transp=0.0)
        if g0 < x0 + L:
            g = rng.uniform(60, 75) + 15 * d
            b.jump_arc(g0, y0, fz(g0), g0 + g, y0, fz(g0 + g))
            warn_stripes(b, g0 - 24, y0, fz(g0 - 20), sw)
            x = g0 + g
    b.flat(x0 + L, x0 + L + 40, y0, fz(x0 + L), 40)
    st.x, st.z = x0 + L + 40, fz(x0 + L)
    connect(b, st, 60, z1=z0)


# 28. split route
def s_split(b, st, d, rng):
    w = 50
    lead(b, st, w)
    off = rng.uniform(80, 110)
    L = rng.uniform(620, 720)
    x0, y0, z0 = st.x, st.y, st.z
    side = rng.choice([-1, 1])
    # fast route: narrow, boosts, two gaps
    za = z0 + side * off
    fork = 120
    b.road(x0, x0 + fork, lambda x: y0, lambda x: z0 + side * off * ease((x - x0) / fork), lambda x: 24, step=10)
    b.road(x0, x0 + fork, lambda x: y0, lambda x: z0 - side * off * ease((x - x0) / fork), lambda x: 44, step=10,
           line=False)
    xa = x0 + fork
    seg = (L - 2 * fork) / 3
    gx = xa + 90
    b.flat(xa, gx, y0, za, 24)
    b.boost(xa + 30, y0, za)
    gap = 70 + 20 * d
    b.jump_arc(gx, y0, za, gx + gap, y0, za)
    b.flat(gx + gap, x0 + L - fork, y0, za, 22)
    # safe route: wide, slalom blocks
    zb = z0 - side * off
    b.flat(xa, x0 + L - fork, y0, zb, 44, line=False)
    k = int((L - 2 * fork) // 70)
    for i in range(k):
        bz = zb + (12 if i % 2 == 0 else -12)
        b.part("Block", CF((xa + 40 + i * 70, y0 + 6, bz)), (10, 12, 22), b.theme["danger"], "Neon", parent=b.hazards,
               collide=False, query=True, attrs={"ObbyHazard": "Knock"})
    b.road(x0 + L - fork, x0 + L, lambda x: y0, lambda x: za + (z0 - za) * ease((x - (x0 + L - fork)) / fork),
           lambda x: 24, step=10)
    b.road(x0 + L - fork, x0 + L, lambda x: y0, lambda x: zb + (z0 - zb) * ease((x - (x0 + L - fork)) / fork),
           lambda x: 44, step=10, line=False)
    sign_x = x0 + 40
    b.part("SplitSign", CF((sign_x, y0 + 30, z0)), (2, 14, 60), b.theme["accent"], "Neon", collide=False, query=False)
    st.x = x0 + L
    connect(b, st, 40)


# 29. the big drop
def s_drop(b, st, d, rng):
    w = max(st.w, 48)
    lead(b, st, w)
    connect(b, st, 60)
    b.boost(st.x - 40, st.y, st.z)
    H = rng.uniform(110, 160)
    x0, y0, z0 = st.x, st.y, st.z
    accent(b, "DropLip", deck_frame((x0 - 1.5, y0 + 0.3, z0), (1, 0, 0)), (w, 0.6, 3), b.theme["danger"])
    # ballistic roll-off at 115 / 230 lands between these
    land0 = x0 + 25
    slope = math.radians(20)
    rampL = 280
    ramp_end_y = y0 - H - 20
    b.road(land0, land0 + rampL, lambda x: (y0 - H + 60) - (x - land0) * math.tan(slope) * (1 - 0.5 * ease((x - land0) / rampL)),
           lambda x: z0, lambda x: w + 16, step=12, line=False)
    yend = (y0 - H + 60) - rampL * math.tan(slope) * 0.5
    b.arc((x0, y0 + CAR_UP, z0), (150, 0, 0), until_y=yend + 40)
    for k in range(3):
        t = 0.45 + 0.3 * k
        ring(b, (x0 + 150 * t, y0 + CAR_UP - 0.5 * G * t * t, z0), 24 + 4 * k)
    st.x, st.y = land0 + rampL, yend
    connect(b, st, 60)


def chevron(b, c, dirv, size, color, parent=None):
    f = unit(dirv)
    left = unit((f[2], 0, -f[0]))
    for s in (-1, 1):
        arm = unit(add(mul(f, -1), mul(left, s)))
        p = add(c, mul(arm, size * 0.35))
        b.part("Chevron", deck_frame(p, arm), (1.8, 0.2, size * 0.75), color, "Neon", parent=parent or b.roads,
               collide=False, query=False)


def ring(b, c, r, color=None, n=14, axis=(1, 0, 0), parent=None):
    color = color or b.theme["accent"]
    for i in range(n):
        a = TAU * i / n
        dv = (0, math.cos(a), math.sin(a))
        p = add(c, mul(dv, r))
        tang = (0, -math.sin(a), math.cos(a))
        b.part("RingSeg", deck_frame(p, tang, up=dv), (2.4, 2.4, TAU * r / n + 1), color, "Neon", parent=parent,
               collide=False, query=False)


# 30. ladder of launch pads up a tower
def s_tower(b, st, d, rng):
    w = max(st.w, 46)
    lead(b, st, w)
    connect(b, st, 50)
    n = 3
    src = (st.x - 15, st.y, st.z)
    y, z = st.y, st.z
    for i in range(n):
        up = rng.uniform(45, 65) + 12 * d
        D = rng.uniform(140, 175)
        nz = z + rng.uniform(-50, 50)
        tgt = (src[0] + D, y + up, nz)
        b.launch(src, tgt, apex=up + rng.uniform(30, 45))
        ledge = rng.uniform(75, 95)
        b.flat(tgt[0] - 35, tgt[0] + ledge, tgt[1], nz, 48)
        b.part("TowerBody", CF((tgt[0] + ledge / 2 - 17, tgt[1] - 60, nz)), (ledge + 30, 112, 40), b.theme["deco"],
               b.theme.get("rock_mat", "Slate"), collide=False, query=False)
        src = (tgt[0] + ledge - 20, tgt[1], nz)
        y, z = tgt[1], nz
    st.x, st.y, st.z = src[0] + 20, y, z
    connect(b, st, 40)


# 31. slalom gates (solid walls)
def s_slalom(b, st, d, rng):
    w = rng.uniform(60, 70)
    lead(b, st, w)
    n = rng.randint(5, 7)
    sp = rng.uniform(62, 78) - 8 * d
    L = n * sp + 70
    x0 = st.x
    connect(b, st, L, line=False)
    b.line(x0, st.y, st.z)
    for i in range(n):
        x = x0 + 50 + i * sp
        side = 1 if i % 2 == 0 else -1
        bw = w * (0.58 + 0.08 * d)
        zz = st.z + side * (w / 2 - bw / 2)
        b.line(x, st.y, st.z - side * bw / 2)  # the middle of the opening
        b.part("Gate", CF((x, st.y + 7, zz)), (8, 14, bw), b.theme["metal"], "Metal", parent=b.hazards, collide=True)
        b.part("GateGlow", CF((x, st.y + 14.3, zz)), (8.4, 0.6, bw), b.theme["danger"], "Neon", collide=False, query=False)
    b.line(x0 + L, st.y, st.z)


# 32. 3D rollercoaster ribbon
def s_coaster(b, st, d, rng):
    w = rng.uniform(36, 44) - 4 * d
    lead(b, st, w, boost=True)
    L = rng.uniform(480, 600)
    x0, y0, z0 = st.x, st.y, st.z
    Az = rng.uniform(50, 80)
    lz = rng.uniform(260, 340)
    ly = rng.uniform(280, 360)
    Ay = min(rng.uniform(16, 24), 0.36 * ly / TAU)
    env = lambda x: math.sin(math.pi * (x - x0) / L)
    fz = lambda x: z0 + Az * math.sin(TAU * (x - x0) / lz) * env(x)
    fy = lambda x: y0 + Ay * math.sin(TAU * (x - x0) / ly) * env(x)

    def bank(x):
        h = 4.0
        zpp = (fz(x + h) - 2 * fz(x) + fz(x - h)) / (h * h)
        return max(-0.5, min(0.5, zpp * 160))
    b.road(x0, x0 + L, fy, fz, lambda x: w, step=8, bank=bank)
    st.x = x0 + L


# 33. sliding doors
def s_doors(b, st, d, rng):
    w = rng.uniform(46, 54)
    lead(b, st, w)
    n = rng.randint(3, 5)
    sp = rng.uniform(85, 110)
    L = n * sp + 60
    x0 = st.x
    connect(b, st, L, rails=True)
    hole = 30 - 6 * d
    for i in range(n):
        x = x0 + 60 + i * sp
        root = b.prop_root("Door")
        amp = w - hole
        rest_z = st.z - w / 2 + hole / 2
        period = rng.uniform(2.6, 3.4) - 0.4 * d
        rig = b.rig(root, "Slide", axis_frame((x, st.y + 10, rest_z), (0, 0, 1)), amp, period, phase=rng.random(),
                    name="DoorSlide")
        # the wall is two panels either side of the hole, travelling together
        left_w = w
        b.part("DoorPanel", CF((x, st.y + 10, rest_z - hole / 2 - left_w / 2)), (6, 20, left_w), b.theme["danger"], "Neon",
               parent=rig, collide=False, query=True, transp=0.25, attrs={"ObbyHazard": "Knock"})
        b.part("DoorPanel", CF((x, st.y + 10, rest_z + hole / 2 + left_w / 2)), (6, 20, left_w), b.theme["danger"], "Neon",
               parent=rig, collide=False, query=True, transp=0.25, attrs={"ObbyHazard": "Knock"})
        b.part("DoorFrame", CF((x, st.y + 22, st.z)), (8, 4, w + 10), b.theme["metal"], "Metal", collide=False)


# 34. mud bog: slow patches on a narrow winding road
def s_mud(b, st, d, rng):
    w = rng.uniform(48, 56)
    lead(b, st, w)
    L = rng.uniform(380, 480)
    x0, z0, y0 = st.x, st.z, st.y
    fz = lambda x: z0 + 30 * math.sin(TAU * (x - x0) / 240) * math.sin(math.pi * (x - x0) / L)
    b.road(x0, x0 + L, lambda x: y0, fz, lambda x: w, step=10)
    k = int(L // 60)
    for i in range(k):
        x = x0 + 50 + i * 60
        side = rng.choice([-1, 1])
        zz = fz(x) + side * rng.uniform(4, w / 2 - 12)
        b.part("Mud", CF((x, y0 + 0.1, zz)), (36, 0.4, 22), b.theme.get("mud", (92, 64, 40)), "Sand", collide=False,
               query=False)
        b.part("MudGrip", CF((x, y0 + 3, zz)), (34, 6, 20), (0, 0, 0), parent=b.hazards, transp=1, collide=False,
               query=True, attrs={"ObbyHazard": "Slow"})
    b.boost(x0 + L - 40, y0, z0)
    st.x = x0 + L


SECTIONS = {
    "runway": s_runway, "scurve": s_scurve, "zigzag": s_zigzag, "beam": s_beam, "gaps": s_gaps, "kicker": s_kicker,
    "islands": s_islands, "stairs": s_stairs, "climb": s_climb, "hills": s_hills, "banked": s_banked,
    "halfpipe": s_halfpipe, "spinners": s_spinners, "hammers": s_hammers, "pistons": s_pistons,
    "crushers": s_crushers, "lasers": s_lasers, "sweepers": s_sweepers, "crumble": s_crumble,
    "conveyor": s_conveyor, "ice": s_ice, "bumpers": s_bumpers, "bridges": s_bridges, "wave": s_wave,
    "turntable": s_turntable, "windmills": s_windmills, "lava": s_lava, "split": s_split, "drop": s_drop,
    "tower": s_tower, "slalom": s_slalom, "coaster": s_coaster, "doors": s_doors, "mud": s_mud,
}

# rough x-length of each, for planning (lead-in included)
LENGTHS = {
    "runway": 330, "scurve": 680, "zigzag": 720, "beam": 570, "gaps": 900, "kicker": 680, "islands": 1150,
    "stairs": 850, "climb": 700, "hills": 950, "banked": 1060, "halfpipe": 590, "spinners": 560, "hammers": 560,
    "pistons": 560, "crushers": 500, "lasers": 500, "sweepers": 560, "crumble": 600, "conveyor": 550,
    "ice": 590, "bumpers": 490, "bridges": 520, "wave": 510, "turntable": 330, "windmills": 520, "lava": 580,
    "split": 690, "drop": 600, "tower": 770, "slalom": 540, "coaster": 700, "doors": 550, "mud": 490,
}
# typical height change, used by the planner to keep the course in its band
DY = {"stairs": -190, "climb": 160, "drop": -290, "tower": 280, "ice": -30, "kicker": -40}
