"""Journey pieces: themed roads that climb, dive, bend and change width; spiral ramps; tunnels; caves; big launches
and big drops. Every piece starts and ends on solid ground heading +X (so the straight launch pads still work), and
every road keeps to a drivable slope.
"""
import math
from geom import CF, deck_frame, axis_frame, add, sub, mul, unit, length, cross, dot, lerp, UP, rot_y, rot_axis
from builder import THICK, G, CAR_UP
import parkour3 as K
from parkour import St, TAU, ease, ease5
import showcase as SC

MAX_GRADE = math.tan(math.radians(19.5))


# ===================================================================== curves
def catmull(ctrl, step=6.0):
    """A smooth curve through the control points, sampled about every `step` studs."""
    P = [ctrl[0]] + [tuple(c) for c in ctrl] + [ctrl[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(1, int(math.dist(p1, p2) / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(3)))
    out.append(tuple(ctrl[-1]))
    return out


def grade_ok(pts):
    for a, c in zip(pts, pts[1:]):
        h = math.hypot(c[0] - a[0], c[2] - a[2])
        if h > 0.5 and abs(c[1] - a[1]) / h > MAX_GRADE + 1e-3:
            return False
    return True


def ease_s(t):
    return t * t * (3 - 2 * t)


# ===================================================================== laying a road
def lay_road(b, pts, widths, rails=False, tunnel=None, bank=None, name="Deck", line=True, boosts=(), parent=None):
    """Lay the skin's road along dense points (road tops). widths: one per point. tunnel: wall height or None.
    bank(i) -> radians. boosts: distances along the road for boost strips."""
    sk = b.skin
    parent = parent or b.roads
    n = len(pts)
    widths = [round(w_ / 4.0) * 4.0 for w_ in widths]  # widths change in 4-stud steps, so slabs stay long
    slabs = []
    i = 0
    while i < n - 1:
        j = i + 1
        f0 = unit(sub(pts[j], pts[i]))
        while j + 1 < n:
            f1 = unit(sub(pts[j + 1], pts[j]))
            if (dot(f0, f1) < math.cos(math.radians(1.2)) or widths[j + 1] != widths[i]
                    or math.dist(pts[i], pts[j + 1]) > 120
                    or (bank and abs(bank(j + 1) - bank(i)) > 0.01)):
                break
            j += 1
        slabs.append((i, j))
        i = j
    dist = 0.0
    next_rib = 0.0
    next_light = 20.0
    cum = [0.0]
    for a, c in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, c))
    # bends are mitred: each slab stops where its inner edge meets the next one's, so no two road tops ever overlap
    # (overlaps flicker, and lifting one to stop the flicker leaves a ledge); the wedge left open on the outside of the
    # bend is filled flush with a triangle
    dirs = [unit(sub(pts[j], pts[i])) for (i, j) in slabs]
    trim_a = [0.0] * len(slabs)
    trim_b = [0.0] * len(slabs)
    for si in range(len(slabs) - 1):
        fa, fb = dirs[si], dirs[si + 1]
        pa_, pb_ = unit((fa[0], 0.0, fa[2])), unit((fb[0], 0.0, fb[2]))
        lft = (pa_[2], 0.0, -pa_[0])  # cross(UP, f): the left of the slab
        th = math.atan2(dot(pb_, lft), dot(pb_, pa_))
        if abs(th) < math.radians(0.3) or (bank and (abs(bank(slabs[si][1])) > 1e-4)):
            continue
        t = math.tan(abs(th) / 2)
        la = math.dist(pts[slabs[si][0]], pts[slabs[si][1]])
        lb = math.dist(pts[slabs[si + 1][0]], pts[slabs[si + 1][1]])
        trim_b[si] = min(widths[slabs[si][0]] / 2 * t, 0.45 * la)
        trim_a[si + 1] = min(widths[slabs[si + 1][0]] / 2 * t, 0.45 * lb)
    for si, (i, j) in enumerate(slabs):
        pa, pb = pts[i], pts[j]
        L = math.dist(pa, pb)
        if L < 0.05:
            continue
        w = widths[i]
        f = unit(sub(pb, pa))
        a_ext, b_ext = -trim_a[si], -trim_b[si]
        mid = add(lerp(pa, pb, 0.5), mul(f, (b_ext - a_ext) / 2))
        L = L + a_ext + b_ext
        bk = bank((i + j) // 2) if bank else 0.0
        fr = deck_frame(mid, f, bank=bk)
        sk.road_piece(b, parent, fr, w, L, name)
        if rails:
            for s in ((-1, 1) if rails is True else (rails,)):
                # mitred at both ends: each rail runs from the bisector of the bend behind to the one ahead, so
                # rails round a curve meet edge to edge instead of leaving gaps outside and overlaps inside
                off = s * (w / 2 + 0.8)
                ra = _rail_end(pts[i], dirs[si - 1] if si > 0 else None, dirs[si], off)
                rb = _rail_end(pts[j], dirs[si], dirs[si + 1] if si + 1 < len(slabs) else None, off)
                ra = add(ra, mul(fr.y, 0.0))
                d_ = sub(rb, ra)
                Lr = math.sqrt(d_[0] ** 2 + d_[1] ** 2 + d_[2] ** 2)
                if Lr > 0.2:
                    rf = deck_frame(lerp(ra, rb, 0.5), d_, bank=bk)
                    SC_P(b, "Rail", CF(add(rf.p, mul(rf.y, 1.6)), rf.x, rf.y, rf.z),
                         (1.4, 4.4, Lr + 0.6), sk.road_style()["side"], sk.road_style()["side_mat"], parent, collide=True)
                    SC_P(b, "RailCap", CF(add(rf.p, mul(rf.y, 3.95)), rf.x, rf.y, rf.z),
                         (1.8, 0.4, Lr + 0.6), sk.road_style()["edge"], sk.road_style()["edge_mat"], parent)
        if tunnel:
            sk.tunnel_piece(b, fr, w, L, tunnel)
        if trim_b[si] > 0 and si + 1 < len(slabs):
            _mitre_fill(b, parent, pts[j], f, dirs[si + 1], trim_b[si], trim_a[si + 1], w, widths[slabs[si + 1][0]], name)
        for t in (0.0, 0.5, 1.0):
            p = lerp(pa, pb, t)
            b.samples.append((p[0], p[1], p[2], w))
    if tunnel:
        # ribs and lights at even spacing along the whole road
        d = 16.0
        while d < cum[-1] - 8:
            k = max(0, min(n - 2, next(ii for ii in range(n - 1) if cum[ii + 1] >= d)))
            fr = deck_frame(pts[k], sub(pts[k + 1], pts[k]))
            sk.tunnel_rib(b, fr, widths[k], tunnel, int(d // 40))
            d += 40.0
    # the theme's supports hanging under the road
    d = 70.0
    i_ = 0
    while d < cum[-1] - 40:
        k = max(0, min(n - 2, next(ii for ii in range(n - 1) if cum[ii + 1] >= d)))
        p = pts[k]
        sk.under(b, (p[0], p[1] - 6, p[2]), widths[k], i_)
        i_ += 1
        d += 170.0
    for bd in boosts:
        k = max(0, min(n - 2, next((ii for ii in range(n - 1) if cum[ii + 1] >= bd), n - 2)))
        f = unit(sub(pts[k + 1], pts[k]))
        b.boost(pts[k][0], pts[k][1], pts[k][2], f)
    if line:
        last = -1e9
        for k, p in enumerate(pts):
            if cum[k] - last >= 22 or k == n - 1:
                b.line(p[0], p[1], p[2])
                last = cum[k]


def _rail_end(v, fa, fb, off):
    """Where a rail `off` to the right of the road's centre line meets the bisector at vertex v between the slab
    directions fa and fb (either may be None: a plain end)."""
    def rgt(f):
        h = unit((f[0], 0.0, f[2]))
        return (-h[2], 0.0, h[0])
    if fa is None or fb is None:
        return add(v, mul(rgt(fa or fb), off))
    ra, rb = rgt(fa), rgt(fb)
    n = unit(add(ra, rb))
    c = max(0.3, dot(n, ra))
    return add(v, mul(n, off / c))


def _mitre_fill(b, parent, v, fa, fb, ea, eb, wa, wb, name):
    """The flush triangle that closes the outside of a mitred bend between two road slabs."""
    import epic_marks as M
    fra, frb = deck_frame(v, fa), deck_frame(v, fb)
    s_in = 1.0 if dot(unit((fb[0], 0.0, fb[2])), fra.x) > 0 else -1.0
    ae = sub(v, mul(fa, ea))
    bs = add(v, mul(fb, eb))
    inner = add(ae, mul(fra.x, s_in * wa / 2))
    a_out = sub(ae, mul(fra.x, s_in * wa / 2))
    b_out = sub(bs, mul(frb.x, s_in * wb / 2))
    st = b.skin.road_style()
    M.tri(b, name, inner, a_out, b_out, st["top"], st["top_mat"], parent, th=2.0, inward=sub(v, (0, 6, 0)), collide=True)
    M.tri(b, "RoadSide", a_out, b_out, sub(b_out, (0, 7.0, 0)), st["side"], st["side_mat"], parent, th=1.0, inward=v)
    M.tri(b, "RoadSide", a_out, sub(a_out, (0, 7.0, 0)), sub(b_out, (0, 7.0, 0)), st["side"], st["side_mat"], parent, th=1.0,
          inward=v)


def SC_P(b, name, cf, size, color, mat="SmoothPlastic", parent=None, collide=False, transp=0.0, shape=1, attrs=None,
         query=None):
    return b.part(name, cf, size, color, mat, parent=parent if parent is not None else b.roads, collide=collide,
                  query=collide if query is None else query, transp=transp, shape=shape, attrs=attrs)


def road(b, st, ctrl, w0, w1=None, **kw):
    """A themed road from the state through control points (x, y, z road tops); ends heading +X at the last point."""
    w1 = w0 if w1 is None else w1
    pts = catmull([(st.x, st.y, st.z)] + list(ctrl))
    assert grade_ok(pts), ("road too steep", ctrl)
    n = len(pts)
    widths = [w0 + (w1 - w0) * ease_s(i / max(n - 1, 1)) for i in range(n)]
    lay_road(b, pts, widths, **kw)
    st.x, st.y, st.z = pts[-1]
    st.w = w1
    return pts


def profile(b, st, L, dy=0.0, dz=0.0, w0=None, w1=None, swing=0.0, waves=0, lead=40.0, **kw):
    """A road of length L along +X: flat for `lead` at each end, a smooth climb/dive of dy and sideways shift of dz in
    between, plus an optional snake of `swing` studs with `waves` bends. Ends heading +X."""
    w0 = w0 or K.W(b, 44)
    w1 = w1 or w0
    x0, y0, z0 = st.x, st.y, st.z
    n = max(8, int(L / 6))
    prof = ramp_profile(n)
    pts, widths = [], []
    for i in range(n + 1):
        t = i / n
        u = min(1.0, max(0.0, (t * L - lead) / max(L - 2 * lead, 1)))
        e = float(prof(u))
        sz = swing * math.sin(math.pi * waves * u) * math.sin(math.pi * u) if waves else 0.0
        pts.append((x0 + L * t, y0 + dy * e, z0 + dz * e + sz))
        widths.append(w0 + (w1 - w0) * e)
    assert grade_ok(pts), ("road too steep", L, dy)
    lay_road(b, pts, widths, **kw)
    st.x, st.y, st.z = pts[-1]
    st.w = w1
    return pts


def ramp_profile(n, a=0.22):
    """0 -> 1 with an even slope in the middle and smooth starts and stops (steepest point = mean / (1 - a))."""
    us = [k / 400 for k in range(401)]
    v = []
    for u in us:
        r = min(u / a, (1 - u) / a, 1.0)
        v.append(r * r * (3 - 2 * r))
    cum = [0.0]
    for k in range(1, 401):
        cum.append(cum[-1] + (v[k] + v[k - 1]) / 2)
    tot = cum[-1]

    def f(u):
        k = min(399, int(u * 400))
        t = u * 400 - k
        return (cum[k] * (1 - t) + cum[k + 1] * t) / tot
    return f


def length_for(dy, L=None, lead=40.0):
    """A length that keeps a climb of dy within the drivable slope (the steepest point is about 1.3x the mean)."""
    need = abs(dy) * 1.32 / (MAX_GRADE * 0.95) + 2 * lead
    return max(L or 0.0, need)


# ===================================================================== scenes
def ramp(b, st, d, rng, dy=-120, L=None, w0=None, w1=None, dz=0.0, tunnel=None, boosts=0, rails=False):
    """A long themed ramp up or down (with an optional sideways S), flat at both ends."""
    w0 = w0 or K.W(b, 44)
    w1 = w1 or w0
    K.rest(b, st, L=80, w=w0)
    L = length_for(dy, L or 300.0)
    profile(b, st, L, dy, dz, w0, w1, tunnel=tunnel, rails=rails, boosts=[L * (k + 1) / (boosts + 1) for k in range(boosts)])


def helix(b, st, d, rng, dy=200.0, turns=1, R=None, w=None, inside=False):
    """A spiral ramp round the skin's centrepiece (or up the inside of its tower), one or more turns."""
    w = w or K.W(b, 40)
    R = R or max(95.0, abs(dy) / turns / (TAU * MAX_GRADE * 0.8))
    K.rest(b, st, L=90, w=w + 8)
    cx, cz = st.x, st.z + R
    y0 = st.y
    n = int(48 * turns)
    pts = []
    for i in range(n + 1):
        th = TAU * turns * i / n
        pts.append((cx + R * math.sin(th), y0 + dy * i / n, cz - R * math.cos(th)))
    assert grade_ok(pts), ("helix too steep", dy, turns, R)
    bank = lambda i: math.radians(9)  # lean in toward the core
    b.skin.helix_core(b, (cx, y0, cz), min(y0, y0 + dy), max(y0, y0 + dy), R, w, inside)
    lay_road(b, pts, [w] * len(pts), rails=1, bank=bank)
    st.y = y0 + dy
    st.x, st.z = cx, cz - R
    K.run(b, st.x, st.x + 70, st.y, st.z, w)
    b.line(st.x + 64, st.y, st.z)
    st.x += 70


def tunnel_run(b, st, d, rng, L=480.0, dy=0.0, w=None, h=None, boosts=2, dz=0.0, hazards=None):
    """A road through the skin's tunnel, with boost strips (and optionally a hazard inside)."""
    w = w or K.W(b, 40)
    h = h or 30.0
    K.rest(b, st, L=80, w=w + 8)
    x, y, z = st.x, st.y, st.z
    L = length_for(dy, L, lead=30.0)
    b.skin.tunnel_mouth(b, (x, y, z), w, h)
    profile(b, st, L, dy, dz, w, w, lead=30.0, tunnel=h, boosts=[L * (k + 1) / (boosts + 1) for k in range(boosts)])
    b.skin.tunnel_mouth(b, (st.x, st.y, st.z), w, h)
    if hazards:
        hazards(b, x, st.x, y, z, w, h)


def cave(b, st, d, rng, L=720.0, w=170.0, h=135.0, depth=95.0, hop=None):
    """A big themed cave: in through a ledge, hop across rocks over its deadly floor, out through the far wall."""
    sk = b.skin
    K.rest(b, st, L=90, w=K.W(b, 48))
    x0, y0, z = st.x - 90, st.y, st.z
    x1 = x0 + L
    src = (st.x - 16, y0, z)
    xs = []
    x = src[0]
    while True:
        x += rng.choice([165, 180, 195])
        if x > x1 - 170:
            break
        xs.append(x)
    hop = hop or sk.cave_rock
    prev = src
    for k, x in enumerate(xs):
        yy = y0 + K.snap(rng.choice([-30, -15, 0, 15, 30, 45]), 15) if k else y0
        t = (x, yy, z)
        SC.pad(b, prev, t)
        hop(b, t, K.W(b, 46), rng)
        prev = t
    tgt = (x1 - 60, y0, z)
    SC.pad(b, prev, tgt)
    K.landing(b, st, *tgt, L=150)
    # the room round it
    sk.cave_shell(b, x0, max(x1 + 30, st.x), y0, z, w, h, depth)


def launch_up(b, st, d, rng, dy=180.0, D=240.0, w=None):
    """A huge pad launch up onto high ground."""
    K.rest(b, st, L=100)
    b.boost(st.x - 55, st.y, st.z)
    src = (st.x - 16, st.y, st.z)
    tgt = (src[0] + D, st.y + dy, st.z)
    b.skin.launcher(b, src, K.W(b, 48))
    SC.pad(b, src, tgt, rings=3)
    K.landing(b, st, *tgt, L=160, w=w or K.W(b, 60))


def cliff_drop(b, st, d, rng, dy=150.0, w=None):
    """Drive off the edge and fall a long way onto a big landing (long enough for any speed)."""
    w = w or K.W(b, 46)
    K.rest(b, st, L=80, w=w)
    K.run(b, st.x, st.x + 60, st.y, st.z, w)
    lip = st.x + 60
    b.line(lip - 6, st.y, st.z)
    ly = st.y - dy
    b.arc((lip, st.y + CAR_UP, st.z), (130, 0, 0), until_y=ly + CAR_UP + 6)
    for k in range(3):
        t = 0.3 + 0.3 * k
        b.skin.hoop(b, (lip + 130 * t, st.y + CAR_UP - 0.5 * G * t * t, st.z), unit((130, -G * t, 0)), 20 + 2 * k)
    L = 420.0
    K.run(b, lip + 20, lip + 20 + L, ly, st.z, K.W(b, 80))
    b.line(lip + 20 + L - 6, ly, st.z)
    st.x, st.y = lip + 20 + L, ly


def narrow(b, st, d, rng, L=360.0, w=14.0, weave=40.0):
    """A thin beam that weaves side to side."""
    K.rest(b, st, L=80)
    x, y, z = st.x, st.y, st.z
    ctrl = [(x + 40, y, z), (x + L * 0.3, y, z + weave), (x + L * 0.6, y, z - weave), (x + L - 40, y, z), (x + L, y, z)]
    road(b, st, ctrl, K.W(b, 40), w)
    x, y, z = st.x, st.y, st.z
    road(b, st, [(x + 60, y, z), (x + 90, y, z)], w, K.W(b, 44))


def slide(b, st, d, rng, dy=-160.0, L=760.0, w=None, swing=60.0):
    """A banked, walled slide that snakes down a long way."""
    w = w or K.W(b, 36)
    K.rest(b, st, L=80, w=w + 8)
    L = length_for(dy, L)
    pts = profile(b, st, L, dy, 0.0, w, w, swing=swing, waves=4, rails=True, bank=None)
    return pts


def to_lane(b, st, z_target, L=220.0):
    """A gentle S back into a lane (no pad ever fires sideways)."""
    if abs(st.z - z_target) < 0.01:
        return
    x, y = st.x, st.y
    road(b, st, [(x + 40, y, st.z), (x + L - 40, y, z_target), (x + L, y, z_target)], st.w or K.W(b, 44))
