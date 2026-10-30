"""Parkour kit v2: clean objects, exact launch pads, loops, rolls, wall rides, pipes and rotating pieces.

Every module starts with a rest platform (its checkpoint) at the builder state and ends with the car on a
solid surface heading +X at the new state. Positions are road tops; the racing line is added in travel order.
"""
import math
from geom import CF, deck_frame, look_frame, axis_frame, add, sub, mul, unit, length, cross, dot, lerp, rot_axis, UP
from builder import THICK, G, CAR_UP, mix

TAU = math.pi * 2


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease5(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (6 * t - 15) + 10)


def bump(t):
    """0 -> 1 -> 0, flat at both ends"""
    return math.sin(math.pi * max(0.0, min(1.0, t))) ** 2


class St:
    def __init__(self, x, y, z, w, zc):
        self.x, self.y, self.z, self.w, self.zc = x, y, z, w, zc

    def lateral(self, rng, amp):
        """a sideways target that drifts back toward the centre line when far out"""
        off = self.z - self.zc
        lo, hi = -amp, amp
        if off > 180:
            hi = 0
        if off < -180:
            lo = 0
        return self.z + rng.uniform(lo, hi)


# ===================================================================== the parts
def P(b, name, cf, size, color, mat="SmoothPlastic", parent=None, collide=False, transp=0.0, shape=1, attrs=None,
      query=None, cls="Part"):
    return b.part(name, cf, size, color, mat, parent=parent or b.roads, collide=collide, query=query,
                  transp=transp, shape=shape, attrs=attrs, cls=cls)


def block(b, top, L, w, fwd=(1, 0, 0), h=10.0, parent=None, name="Platform", trim=True, attrs=None):
    """A clean two-tone platform: solid body, inset top plate, neon trim round the top edge."""
    pal = b.theme
    fr = deck_frame(top, fwd)
    body = CF(sub(top, mul(fr.y, h / 2)), fr.x, fr.y, fr.z)
    p = P(b, name, body, (w, h, L), pal["body"], pal["body_mat"], parent=parent, collide=True, attrs=attrs,
          transp=pal.get("body_transp", 0.0))
    P(b, "Top", CF(add(top, mul(fr.y, 0.06)), fr.x, fr.y, fr.z), (w - 1.6, 0.12, L - 1.6), pal["top"], pal["top_mat"],
      parent=parent)
    if trim:
        e = pal["edge"]
        for s in (-1, 1):
            P(b, "Trim", CF(add(top, add(mul(fr.x, s * (w / 2 - 0.45)), mul(fr.y, 0.2))), fr.x, fr.y, fr.z), (0.9, 0.42, L),
              e, "Neon", parent=parent)
            P(b, "Trim", CF(add(top, add(mul(fr.z, s * (L / 2 - 0.45)), mul(fr.y, 0.2))), fr.x, fr.y, fr.z), (w, 0.42, 0.9),
              e, "Neon", parent=parent)
        P(b, "Underglow", CF(sub(top, mul(fr.y, h + 0.3)), fr.x, fr.y, fr.z), (w * 0.7, 0.6, L * 0.7), e, "Neon",
          parent=parent, transp=0.35)
    b.samples.append((top[0], top[1], top[2], max(w, L)))
    return p


def tiles(b, x0, L, y, z, w, name="Deck"):
    """A run of separate floating tiles with small gaps (the car rolls straight over them)."""
    n = max(1, int(round(L / 52)))
    tl = L / n
    for i in range(n):
        block(b, (x0 + tl * i + tl / 2, y, z), tl - 3.0, w, h=8, name=name)


def pillar(b, top, r, h=36.0, parent=None):
    pal = b.theme
    P(b, "Pillar", axis_frame(sub(top, (0, h / 2, 0)), UP), (h, 2 * r, 2 * r), pal["body"], pal["body_mat"],
      parent=parent, collide=True, transp=pal.get("body_transp", 0.0))
    P(b, "Top", axis_frame(add(top, (0, 0.06, 0)), UP), (0.12, 2 * r - 2, 2 * r - 2), pal["top"], pal["top_mat"], parent=parent)
    P(b, "Rim", axis_frame(sub(top, (0, 0.7, 0)), UP), (1.2, 2 * r + 0.5, 2 * r + 0.5), pal["edge"], "Neon", parent=parent)
    P(b, "Tip", axis_frame(sub(top, (0, h + 0.4, 0)), UP), (0.8, r * 1.1, r * 1.1), pal["edge"], "Neon", parent=parent,
      transp=0.3)
    b.samples.append((top[0], top[1], top[2], 2 * r))


def cube(b, top, s, yaw=0.0, parent=None):
    """A floating cube, turned on its vertical axis."""
    f = (math.cos(yaw), 0, math.sin(yaw))
    block(b, top, s, s, fwd=f, h=s * 0.8, parent=parent, name="Cube")


def pad(b, start, target, apex=None, rings=0):
    """Exact launch pad at `start` (a surface top) to `target`; a clean pad graphic; optional hoops on the arc."""
    while b.path and b.path[-1][3] == "r" and b.path[-1][0] > start[0] - 1:
        b.path.pop()  # (the module's last line point lies past its own launch pad)
    H, V, T = b.launch(start, target, apex=apex, visual=False)
    pal = b.theme
    f = unit((target[0] - start[0], 0, target[2] - start[2]))
    fr = deck_frame(add(start, (0, 0.1, 0)), f)
    P(b, "PadPlate", fr, (30, 0.2, 26), mix(pal["pad"], (0, 0, 0), 0.55), "SmoothPlastic")
    for k in range(3):
        c = add(start, add(mul(f, -7 + k * 7), (0, 0.25, 0)))
        chevron(b, c, f, 14, pal["pad"])
    for s in (-1, 1):
        P(b, "PadRail", CF(add(start, add(mul(fr.x, s * 15), (0, 0.3, 0))), fr.x, fr.y, fr.z), (0.8, 0.4, 26), pal["pad"], "Neon")
    if rings:
        for k in range(rings):
            t = T * (k + 1) / (rings + 1)
            p = (start[0] + f[0] * H * t, start[1] + CAR_UP + V * t - 0.5 * G * t * t, start[2] + f[2] * H * t)
            v = (f[0] * H, V - G * t, f[2] * H)
            hoop(b, p, unit(v), 17, pal["pad"])
    return H, V, T


def chevron(b, c, f, size, color, parent=None):
    left = unit((f[2], 0, -f[0]))
    for s in (-1, 1):
        arm = unit(add(f, mul(left, s)))
        p = add(c, mul(arm, -size * 0.25))
        P(b, "Chevron", deck_frame(p, arm), (1.6, 0.2, size * 0.62), color, "Neon", parent=parent)


def hoop(b, c, axis, r, color, n=16, th=1.8, parent=None):
    ax = unit(axis)
    a1 = unit(cross(ax, UP)) if abs(ax[1]) < 0.95 else (1, 0, 0)
    a2 = unit(cross(a1, ax))
    for i in range(n):
        t = TAU * i / n
        d = add(mul(a1, math.cos(t)), mul(a2, math.sin(t)))
        tang = add(mul(a1, -math.sin(t)), mul(a2, math.cos(t)))
        P(b, "Hoop", deck_frame(add(c, mul(d, r)), tang, up=d), (th, th, TAU * r / n + th * 0.6), color, "Neon",
          parent=parent)


def ribbon(b, pts, w, model, rails=False, edge=True, name="Deck", color=None, step_merge=True):
    """A driving surface along points [(p, n)] (p = road top, n = surface normal). Returns nothing."""
    pal = b.theme
    import rbxl
    if rbxl.attrs(model).get("WallRide"):
        name = "RideDeck"
    for (p0, n0), (p1, n1) in zip(pts, pts[1:]):
        seg = sub(p1, p0)
        L = length(seg)
        if L < 0.05:
            continue
        f = unit(seg)
        up = unit(add(n0, n1))
        up = unit(sub(up, mul(f, dot(up, f))))
        x = cross(up, f)
        mid = lerp(p0, p1, 0.5)
        th = 8.0 if name == "RideDeck" else THICK  # (a loop or wall ride: thick enough that a fast car never tunnels)
        cf = CF(sub(mid, mul(up, th / 2)), x, up, f)
        P(b, name, cf, (w, th, L + 1.0), color or pal["top"], pal["top_mat"], parent=model, collide=True)
        if edge:
            for s in (-1, 1):
                P(b, "Edge", CF(add(mid, add(mul(x, s * (w / 2 - 0.6)), mul(up, 0.25))), x, up, f), (1.2, 0.5, L + 1.0),
                  pal["edge"], "Neon", parent=model)
        if rails:
            for s in (-1, 1):
                P(b, "Rail", CF(add(mid, add(mul(x, s * (w / 2 + 1)), mul(up, 1.4))), x, up, f), (2, 2.8 + THICK, L + 1.0),
                  pal["body"], pal["body_mat"], parent=model, collide=True)
        if n0[1] > 0.6:
            b.samples.append((mid[0], mid[1], mid[2], w))


def road(b, st, L, y1=None, z1=None, w=None, boost=False):
    """A plain straight-ish link (eased), as a ribbon."""
    y0, z0, x0 = st.y, st.z, st.x
    y1 = y0 if y1 is None else y1
    z1 = z0 if z1 is None else z1
    w = w or st.w
    n = max(1, int(L // 12)) if (abs(y1 - y0) > 1 or abs(z1 - z0) > 1) else 1
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(((x0 + L * t, y0 + (y1 - y0) * ease(t), z0 + (z1 - z0) * ease(t)), UP))
    ribbon(b, pts, w, b.model("Link", b.roads))
    for p, _ in pts[:: max(1, n // 4)] + [pts[-1]]:
        b.line(p[0], p[1], p[2])
    if boost:
        b.boost(x0 + min(40, L / 2), y0, z0)
    st.x, st.y, st.z, st.w = x0 + L, y1, z1, w


def rest(b, st, L=72, w=50, boost=False):
    """The module's checkpoint platform."""
    arrived = getattr(b, "pending_landing", False)
    b.pending_landing = False
    top = (st.x + L / 2, st.y, st.z)
    block(b, top, L, w, h=12)
    b.checkpoint(st.x + 18, st.y, st.z, w)
    if not arrived:
        b.line(st.x, st.y, st.z)
    b.line(st.x + L, st.y, st.z)
    if boost:
        b.boost(st.x + L - 30, st.y, st.z)
    st.x += L
    st.w = w


def landing(b, st, tx, ty, tz, L=150, w=52):
    """A long platform the last jump of a module comes down on (target at ~30%)."""
    x0 = tx - L * 0.3
    block(b, (x0 + L / 2, ty, tz), L, w, h=12)
    b.line(x0 + L * 0.3, ty, tz)
    b.line(x0 + L, ty, tz)
    st.x, st.y, st.z, st.w = x0 + L, ty, tz, w


def spin(b, centre, axis, speed, phase=0.0, name="Spin"):
    root = b.prop_root(name)
    return b.rig(root, "Spin", axis_frame(centre, axis), speed, 4, phase=phase)


# ===================================================================== modules
def m_pillar_hops(b, st, d, rng):
    """Bounce from pillar top to pillar top on exact pads, up and down."""
    rest(b, st)
    n = rng.randint(3, 5)
    src = (st.x - 16, st.y, st.z)
    y0 = st.y
    for i in range(n):
        D = rng.uniform(165, 215) + 25 * d
        ty = max(y0 - 140, min(y0 + 160, src[1] + rng.uniform(-55, 60)))
        tz = st.lateral(rng, 60) if i < n - 1 else src[2]
        st.z = tz
        tgt = (src[0] + math.sqrt(max(D * D - (tz - src[2]) ** 2, 100)), ty, tz)
        pad(b, src, tgt, apex=max(ty - src[1], 0) + rng.uniform(38, 58))
        pillar(b, tgt, rng.uniform(24, 29) - 3 * d, h=rng.uniform(28, 48))
        src = tgt
    D = rng.uniform(180, 220)
    tgt = (src[0] + D, src[1] + rng.uniform(-40, 20), src[2])
    pad(b, src, tgt, apex=max(tgt[1] - src[1], 0) + 45)
    landing(b, st, *tgt)


def m_cube_climb(b, st, d, rng, up=True):
    """A staircase of floating turned cubes, climbed (or dropped) on pads."""
    rest(b, st)
    n = rng.randint(3, 4)
    src = (st.x - 16, st.y, st.z)
    for i in range(n):
        D = rng.uniform(150, 190)
        dy = rng.uniform(45, 70) * (1 if up else -1)
        tz = src[2] + rng.uniform(-50, 50)
        tgt = (src[0] + D, src[1] + dy, tz)
        pad(b, src, tgt, apex=max(dy, 0) + rng.uniform(30, 45))
        cube(b, tgt, rng.uniform(46, 54) - 4 * d, yaw=rng.choice([0.0, math.pi / 4, math.pi / 8]))
        src = tgt
    tgt = (src[0] + 190, src[1] + (10 if up else -30), src[2])
    pad(b, src, tgt, apex=max(tgt[1] - src[1], 0) + 40)
    landing(b, st, *tgt)


def m_cube_drop(b, st, d, rng):
    m_cube_climb(b, st, d, rng, up=False)


def m_loop(b, st, d, rng, double=False):
    """Loop-de-loop. The ring shifts sideways one lane per turn so you come out beside where you went in."""
    w = 32.0
    rest(b, st, w=44)
    road(b, st, 90, w=w, boost=True)
    turns = [1] if not double else [1, -1]
    for k, sgn in enumerate(turns):
        R = rng.uniform(46, 58)
        dz = sgn * (w + 8)
        cx, cy, z0 = st.x, st.y + R, st.z
        n = 40
        pts = []
        for i in range(n + 1):
            ph = TAU * i / n
            p = (cx + R * math.sin(ph), cy - R * math.cos(ph), z0 + dz * ease5(i / n))
            nrm = (-math.sin(ph), math.cos(ph), 0.0)
            pts.append((p, nrm))
        m = b.model("Loop", b.roads, {"WallRide": True})
        ribbon(b, pts, w, m, color=mix(b.theme["top"], b.theme["edge"], 0.12))
        for p, nrm in pts[::3]:
            b.path.append((p[0] + nrm[0] * CAR_UP, p[1] + nrm[1] * CAR_UP, p[2], "s"))
        # the halo round the outside of the ring
        hoop(b, (cx, cy, z0 + dz / 2), (0, 0, 1), R + 7, b.theme["edge"], n=28, th=1.4)
        st.z = z0 + dz
        road(b, st, 70 if k < len(turns) - 1 else 110, w=w)


def m_double_loop(b, st, d, rng):
    m_loop(b, st, d, rng, double=True)


def m_barrel_roll(b, st, d, rng):
    """A road that twists a full turn around itself - you drive it upside down for a moment."""
    w = rng.uniform(34, 40)
    rest(b, st, w=46)
    road(b, st, 70, w=w, boost=True)
    L = rng.uniform(340, 420)
    x0, y0, z0 = st.x, st.y, st.z
    lift = rng.uniform(20, 45)
    sense = rng.choice([-1, 1])
    n = 48
    pts = []
    for i in range(n + 1):
        t = i / n
        a = sense * TAU * ease5(t)
        p = (x0 + L * t, y0 + lift * bump(t), z0)
        nrm = (0.0, math.cos(a), math.sin(a))
        pts.append((p, nrm))
    m = b.model("BarrelRoll", b.roads, {"WallRide": True})
    ribbon(b, pts, w, m)
    for p, nrm in pts[::4]:
        b.path.append((p[0] + nrm[0] * CAR_UP, p[1] + nrm[1] * CAR_UP, p[2] + nrm[2] * CAR_UP, "s"))
    st.x = x0 + L
    road(b, st, 90)


def m_wall_ride(b, st, d, rng):
    """The floor runs out and the road stands up on its side over the void - twice, left then right."""
    w = 36.0
    rest(b, st, w=46)
    road(b, st, 60, w=w, boost=True)
    first = rng.choice([-1, 1])
    for k in range(2):
        side = first * (1 if k == 0 else -1)
        L = rng.uniform(240, 300)
        x0, y0, z0 = st.x, st.y, st.z
        tilt = math.radians(rng.uniform(72, 82))
        n = 30
        pts = []
        for i in range(n + 1):
            t = i / n
            a = side * tilt * bump(t)
            p = (x0 + L * t, y0 + 14 * bump(t), z0 - side * 26 * bump(t))
            pts.append((p, (0.0, math.cos(a), math.sin(a))))
        m = b.model("WallRide", b.roads, {"WallRide": True})
        ribbon(b, pts, w, m)
        for p, nrm in pts[::3]:
            b.path.append((p[0] + nrm[0] * CAR_UP, p[1] + nrm[1] * CAR_UP, p[2] + nrm[2] * CAR_UP, "s"))
        st.x = x0 + L
        road(b, st, 40)
    road(b, st, 60)


def m_pipe(b, st, d, rng):
    """A full glass pipe: blocks on the floor push you up the walls; a bar may spin round inside."""
    w = 30.0
    rest(b, st, w=46)
    road(b, st, 50, w=w, boost=True)
    R = 26.0
    L = rng.uniform(360, 440)
    x0, y0, z0 = st.x, st.y, st.z
    axis_y = y0 + R
    k = 16
    m = b.model("Pipe", b.roads, {"WallRide": True})
    pal = b.theme
    for i in range(k):
        a = TAU * i / k  # 0 = floor
        d_out = (0.0, -math.cos(a), math.sin(a))
        nrm = (0.0, math.cos(a), -math.sin(a))
        top = (x0 + L / 2, axis_y + d_out[1] * R, z0 + d_out[2] * R)
        x = cross(nrm, (1, 0, 0))
        cf = CF(sub(top, mul(nrm, THICK / 2)), x, nrm, (1.0, 0.0, 0.0))
        P(b, "PipeWall", cf, (TAU * R / k + 1.2, THICK, L), pal["top"] if i in (0, 1, k - 1) else pal["glass"],
          "Glass" if i not in (0, 1, k - 1) else pal["top_mat"], parent=m, collide=True,
          transp=0.0 if i in (0, 1, k - 1) else 0.45)
    b.samples.append((x0 + L / 2, y0, z0, w))
    for r in range(int(L // 45) + 1):
        hoop(b, (x0 + r * L / int(L // 45), axis_y, z0), (1, 0, 0), R + 2.5, pal["edge"], n=20, th=1.2)
    # floor blockers, alternating sides: go round them on the wall
    nb = rng.randint(3, 4)
    for j in range(nb):
        xb = x0 + 70 + j * (L - 130) / max(nb - 1, 1)
        side = 1 if j % 2 == 0 else -1
        a = side * 0.5
        c = (xb, axis_y - math.cos(a) * (R - 5), z0 + math.sin(a) * (R - 5))
        P(b, "Blocker", CF(c) * rot_axis((1, 0, 0), -a), (10, 10, 26), pal["danger"], "Neon", parent=b.hazards,
          query=True, attrs={"ObbyHazard": "Knock"})
    if d > 0.45:
        xb = x0 + L * 0.5 + 30
        rig = spin(b, (xb, axis_y, z0), (1, 0, 0), rng.choice([-1, 1]) * (0.18 + 0.12 * d), rng.random(), "PipeSpinner")
        P(b, "SpinBar", CF((xb, axis_y - R / 2, z0)), (4, R - 3, 4), pal["danger"], "Neon", parent=rig, query=True,
          attrs={"ObbyHazard": "Crush"})
    for i in range(0, 9):
        b.line(x0 + L * i / 8, y0, z0)
    st.x = x0 + L
    road(b, st, 70)


def m_spiral(b, st, d, rng):
    """One full turn of a banked spiral round a glowing column, climbing or diving."""
    w = 38.0
    rest(b, st, w=46)
    r = rng.uniform(115, 135)
    rise = rng.choice([-1, 1]) * rng.uniform(70, 100)
    if st.y + rise < b.ylo:
        rise = abs(rise)
    if st.y + rise > b.yhi:
        rise = -abs(rise)
    cx, cz = st.x, st.z + r
    y0 = st.y
    n = 64
    bank = math.radians(14)
    pts = []
    for i in range(n + 1):
        th = TAU * i / n
        p = (cx + r * math.sin(th), y0 + rise * ease(i / n), cz - r * math.cos(th))
        inward = (-math.sin(th), 0.0, math.cos(th))
        nrm = unit(add(mul(UP, math.cos(bank)), mul(inward, math.sin(bank))))
        pts.append((p, nrm))
    m = b.model("Spiral", b.roads)
    ribbon(b, pts, w, m, rails=True)
    for p, _ in pts[::4]:
        b.line(p[0], p[1], p[2])
    pal = b.theme
    lo, hi = min(y0, y0 + rise) - 60, max(y0, y0 + rise) + 60
    P(b, "Column", axis_frame((cx, (lo + hi) / 2, cz), UP), (hi - lo, 30, 30), pal["edge"], "Neon", transp=0.15)
    st.y = y0 + rise
    road(b, st, 70)


def m_spin_bridges(b, st, d, rng):
    """Bars spinning flat over a gap: cross when each one lines up with you."""
    rest(b, st, w=40)
    n = 3
    Lb = rng.uniform(96, 110)
    wb = 34.0
    speed = rng.uniform(0.045, 0.06) + 0.02 * d
    period = 1 / speed
    x = st.x
    for i in range(n):
        c = (x + 8 + Lb / 2, st.y, st.z)
        phase = (-i * (Lb + 14) / 120.0 / period) % 1
        rig = spin(b, c, UP, speed * (1 if i % 2 == 0 else -1), phase, "SpinBridge")
        block(b, c, Lb, wb, parent=rig, name="SpinDeck")
        P(b, "Hub", axis_frame(sub(c, (0, 6, 0)), UP), (12, 22, 22), b.theme["edge"], "Neon")
        b.line(c[0], st.y, st.z)
        x += Lb + 14
    b.samples.append((x, st.y, st.z, 40))
    st.x = x + 6
    block(b, (st.x + 50, st.y, st.z), 100, 44, h=12)
    st.x += 100


def m_cross(b, st, d, rng):
    """A giant plus-shaped bridge turning over the void; wait on the hub for the next arm."""
    rest(b, st, w=40)
    R = rng.uniform(78, 90)
    c = (st.x + R + 6, st.y, st.z)
    speed = rng.uniform(0.045, 0.06) + 0.015 * d
    rig = spin(b, c, UP, speed * rng.choice([-1, 1]), rng.random(), "Cross")
    for k in range(4):
        a = TAU * k / 4
        f = (math.cos(a), 0, math.sin(a))
        block(b, add(c, mul(f, R / 2 + 12)), R - 20, 30, fwd=f, parent=rig, name="Arm", trim=True)
    pillar(b, c, 24, h=20)
    b.line(c[0] - R, st.y, st.z)
    b.line(c[0], st.y, st.z)
    b.line(c[0] + R, st.y, st.z)
    st.x = c[0] + R + 4
    block(b, (st.x + 55, st.y, st.z), 110, 44, h=12)
    st.x += 110


def m_spinner_discs(b, st, d, rng):
    """Round islands, each with a bar sweeping across it - jump the low ones."""
    rest(b, st, w=40)
    n = 3
    for i in range(n):
        r = rng.uniform(46, 54)
        c = (st.x + 30 + r, st.y, st.z)
        block(b, (st.x + 15, st.y, st.z), 32, 26, h=8, name="Bridge")
        pillar(b, c, r, h=18)
        low = rng.random() < 0.6
        rig = spin(b, add(c, (0, 3, 0)), UP, rng.choice([-1, 1]) * (rng.uniform(0.22, 0.32) + 0.12 * d), rng.random(), "Sweeper")
        if low:
            P(b, "SweepLaser", CF(add(c, (0, 3.2, 0))), (2 * r - 4, 3, 2.4), b.theme["danger"], "Neon", parent=rig,
              query=True, attrs={"ObbyHazard": "Burn"})
        else:
            P(b, "SweepWall", CF(add(c, (0, 7, 0))), (2 * r - 4, 14, 3), b.theme["danger"], "Neon", parent=rig,
              query=True, transp=0.15, attrs={"ObbyHazard": "Knock"})
        P(b, "SweepHub", axis_frame(add(c, (0, 5, 0)), UP), (10, 8, 8), b.theme["edge"], "Neon", parent=rig)
        b.line(c[0] - r, st.y, st.z)
        b.line(c[0] + r, st.y, st.z)
        st.x = c[0] + r
    block(b, (st.x + 15, st.y, st.z), 32, 26, h=8, name="Bridge")
    st.x += 30
    block(b, (st.x + 50, st.y, st.z), 100, 44, h=12)
    st.x += 100


def m_windmill_launch(b, st, d, rng):
    """Launch through a turning windmill - time your run-up."""
    rest(b, st, L=110, w=44)
    src = (st.x - 16, st.y, st.z)
    D = rng.uniform(270, 320)
    tgt = (src[0] + D, st.y + rng.uniform(-40, 10), st.z)
    H, V, T = pad(b, src, tgt, apex=rng.uniform(45, 60))
    t = T * 0.45
    fx = src[0] + H * t
    fy = src[1] + CAR_UP + V * t - 0.5 * G * t * t
    hub = (fx, fy + 34, st.z)
    blades = rng.choice([3, 4])
    rig = spin(b, hub, (1, 0, 0), rng.choice([-1, 1]) * (0.1 + 0.06 * d), rng.random(), "Windmill")
    for k in range(blades):
        a = TAU * k / blades
        dv = (0, math.cos(a), math.sin(a))
        P(b, "Blade", deck_frame(add(hub, mul(dv, 34)), dv, up=(1, 0, 0)), (10, 5, 56), b.theme["danger"], "Neon",
          parent=rig, query=True, attrs={"ObbyHazard": "Crush"})
    P(b, "MillHub", axis_frame(hub, (1, 0, 0)), (8, 16, 16), b.theme["edge"], "Neon", parent=rig)
    hoop(b, hub, (1, 0, 0), 64, b.theme["edge"], n=32, th=1.6)
    landing(b, st, *tgt, L=170)


def m_pendulums(b, st, d, rng):
    """Platforms hanging from the sky, swinging side to side: cross while they line up."""
    rest(b, st, w=40)
    n = rng.randint(3, 4)
    Lp = rng.uniform(64, 74)
    H = 70.0
    theta = rng.uniform(28, 36) + 6 * d
    period = rng.uniform(2.8, 3.4)
    x = st.x
    for i in range(n):
        c = (x + 6 + Lp / 2, st.y, st.z)
        pivot = (c[0], st.y + H, st.z)
        root = b.prop_root("Pendulum")
        rig = b.rig(root, "Hinge", axis_frame(pivot, (1, 0, 0)), theta, period, phase=(i * 0.18) % 1,
                    keys="0:0 0.25:1 0.5:0 0.75:-1", name="Swing")
        block(b, c, Lp, 34, parent=rig, name="SwingDeck")
        for s in (-1, 1):
            a = add(c, (s * (Lp / 2 - 4), 0, 0))
            P(b, "Cable", CF((a[0], (a[1] + pivot[1]) / 2, st.z)), (0.8, H, 0.8), b.theme["edge"], "Neon", parent=rig)
        P(b, "Anchor", CF(pivot), (Lp, 3, 3), b.theme["body"], b.theme["body_mat"])
        b.line(c[0], st.y, st.z)
        x += Lp + 12
    st.x = x
    block(b, (st.x + 55, st.y, st.z), 110, 44, h=12)
    st.x += 110


def m_kicker(b, st, d, rng):
    """Boost, ramp, and a huge exact flight through hoops."""
    rest(b, st, L=60, w=46)
    road(b, st, 120, w=46)
    b.boost(st.x - 100, st.y, st.z)
    b.boost(st.x - 45, st.y, st.z)
    rh, rl = 14.0, 46.0
    fr = deck_frame((st.x + rl / 2, st.y + rh / 2, st.z), (1, 0, 0))
    P(b, "Kicker", fr, (46, rh, rl), b.theme["top"], b.theme["top_mat"], collide=True, cls="WedgePart")
    for s in (-1, 1):
        P(b, "KickerEdge", deck_frame((st.x + rl / 2, st.y + rh / 2 + 0.4, st.z + s * 22.6), (rl, rh, 0)),
          (1.0, 0.6, math.hypot(rl, rh)), b.theme["edge"], "Neon")
    for k in range(1, 4):
        b.line(st.x + rl * k / 4, st.y + rh * k / 4, st.z)
    src = (st.x + rl - 5, st.y + rh, st.z)
    D = rng.uniform(320, 400)
    tgt = (src[0] + D, st.y + rng.uniform(-90, 0), st.z + rng.uniform(-40, 40))
    pad(b, src, tgt, apex=max(tgt[1] - src[1], 0) + rng.uniform(60, 90), rings=3)
    landing(b, st, *tgt, L=180)


def m_beam_sweep(b, st, d, rng):
    """A long narrow beam with low lasers sweeping across it: jump them."""
    w = rng.uniform(24, 28) - 3 * d
    rest(b, st, w=40)
    L = rng.uniform(460, 540)
    x0 = st.x
    block(b, (x0 + L / 2, st.y, st.z), L, w, h=8, name="Beam")
    b.line(x0, st.y, st.z)
    n = rng.randint(3, 4)
    for i in range(n):
        x = x0 + 90 + i * (L - 200) / max(n - 1, 1)
        side = 1 if i % 2 == 0 else -1
        hub = (x, st.y + 3, st.z + side * (w / 2 + 10))
        P(b, "SweepPost", axis_frame(add(hub, (0, 2, 0)), UP), (14, 10, 10), b.theme["body"], b.theme["body_mat"], collide=True)
        rig = spin(b, hub, UP, rng.choice([-1, 1]) * (0.3 + 0.15 * d), rng.random(), "BeamSweep")
        Rr = w + 14
        P(b, "SweepLaser", deck_frame(add(hub, (0, 0.4, -side * Rr / 2)), (0, 0, -side)), (2, 3, Rr), b.theme["danger"],
          "Neon", parent=rig, query=True, attrs={"ObbyHazard": "Burn"})
        b.line(x, st.y, st.z)
    b.line(x0 + L, st.y, st.z)
    st.x = x0 + L
    st.w = w


def m_lasers(b, st, d, rng):
    """Clean gate frames, lasers blinking in a wave you can ride at the right speed."""
    w = 40.0
    rest(b, st, w=44)
    n = rng.randint(5, 7)
    sp = rng.uniform(52, 66)
    L = n * sp + 60
    x0 = st.x
    tiles(b, x0, L, st.y, st.z, w)
    period = rng.uniform(1.8, 2.3)
    on = period * (0.45 + 0.1 * d)
    v = rng.uniform(100, 140)
    for i in range(n):
        x = x0 + 40 + i * sp
        ph = (-(x - x0) / v / period) % 1
        full = rng.random() < 0.5 + 0.3 * d
        for s in (-1, 1):
            P(b, "GatePost", CF((x, st.y + 18, st.z + s * (w / 2 + 2))), (3, 36, 3), b.theme["body"], b.theme["body_mat"], collide=True)
        P(b, "GateTop", CF((x, st.y + 36.5, st.z)), (3, 1.5, w + 7), b.theme["edge"], "Neon")
        beams = [(3.2, 3.0)] if not full else [(4 + 7 * k, 2.2) for k in range(5)]
        for (hy, th) in beams:
            P(b, "Laser", CF((x, st.y + hy, st.z)), (1.2, th, w + 2), b.theme["danger"], "Neon", parent=b.hazards,
              query=True, transp=0.1, attrs={"ObbyHazard": "Zap", "ZapFX": True, "ZapPeriod": period, "ZapOn": on,
                                             "ZapPhase": ph})
    b.line(x0, st.y, st.z)
    b.line(x0 + L, st.y, st.z)
    st.x = x0 + L


def m_checker_crumble(b, st, d, rng):
    """Checkerboard tiles that fall away under you; keep moving."""
    rest(b, st, w=44)
    tl = 22.0
    cols = 2
    n = rng.randint(14, 18)
    delay = 0.4 - 0.15 * d
    z0 = st.z
    for i in range(n):
        zc = z0 + 14 * math.sin(i * 0.55)
        for c in range(cols):
            zz = zc + (c - 0.5) * tl
            m = b.model("CrumbleTile", b.hazards, {"ObbyCrumble": float(delay)})
            top = (st.x + i * tl + tl / 2, st.y, zz)
            fr = deck_frame(top, (1, 0, 0))
            colr = b.theme["top"] if (i + c) % 2 == 0 else b.theme["body"]
            P(b, "Tile", CF(sub(top, (0, 3, 0))), (tl - 0.8, 6, tl - 0.8), colr, b.theme["top_mat"], parent=m, collide=True)
            P(b, "TileGlow", CF(add(top, (0, 0.12, 0))), (tl - 4, 0.2, tl - 4), b.theme["edge"], "Neon", parent=m,
              transp=0.6 if (i + c) % 2 else 0.85)
        b.samples.append((st.x + i * tl, st.y, zc, 2 * tl))
        b.line(st.x + i * tl + tl / 2, st.y, zc + 5)
    st.x += n * tl
    st.z = z0
    block(b, (st.x + 50, st.y, st.z), 100, 44, h=12)
    st.x += 100


def m_crushers(b, st, d, rng):
    """A bridge under slamming presses."""
    w = 40.0
    rest(b, st, w=44)
    n = rng.randint(3, 5)
    sp = rng.uniform(70, 88)
    L = n * sp + 70
    x0 = st.x
    tiles(b, x0, L, st.y, st.z, w)
    H = 40.0
    period = rng.uniform(1.9, 2.4) - 0.3 * d
    dph = rng.choice([0.16, 0.2, 0.25])
    for i in range(n):
        x = x0 + 55 + i * sp
        bl = rng.uniform(26, 32)
        rest_c = (x, st.y + H + 9, st.z)
        for s in (-1, 1):
            P(b, "PressRail", CF((x, st.y + H / 2 + 12, st.z + s * (w / 2 + 3))), (4, H + 26, 4), b.theme["body"],
              b.theme["body_mat"], collide=True)
        P(b, "PressCap", CF((x, st.y + H + 25, st.z)), (bl + 6, 4, w + 10), b.theme["edge"], "Neon")
        root = b.prop_root("Crusher")
        rig = b.rig(root, "Slide", axis_frame(rest_c, (0, -1, 0)), H + 1, period, phase=(i * dph) % 1,
                    keys="0:0 0.42:0 0.5:1 0.68:1 0.96:0", name="Press")
        P(b, "Press", CF(rest_c), (bl, 18, w + 4), b.theme["body"], "Metal", parent=rig, query=True,
          attrs={"ObbyHazard": "Crush"})
        P(b, "PressEdge", CF(add(rest_c, (0, -9.2, 0))), (bl + 0.4, 0.6, w + 4.4), b.theme["danger"], "Neon", parent=rig)
    b.line(x0, st.y, st.z)
    b.line(x0 + L, st.y, st.z)
    st.x = x0 + L


def m_slide_bridges(b, st, d, rng):
    """Gaps bridged by slabs that slide in and out from the side."""
    w = 40.0
    rest(b, st, w=44)
    n = rng.randint(2, 3)
    for i in range(n):
        gap = rng.uniform(64, 80)
        side = rng.choice([-1, 1])
        c = (st.x + gap / 2, st.y, st.z)
        root = b.prop_root("SlideBridge")
        rig = b.rig(root, "Slide", axis_frame(c, (0, 0, side)), w + 10, rng.uniform(2.8, 3.4) - 0.5 * d,
                    phase=rng.random(), keys="0:0 0.45:0 0.55:1 0.9:1", name="Slide")
        block(b, c, gap + 2, w, parent=rig, name="BridgeDeck")
        b.line(st.x, st.y, st.z)
        b.line(st.x + gap, st.y, st.z)
        st.x += gap
        block(b, (st.x + 45, st.y, st.z), 90, w, h=10)
        st.x += 90


def m_piston_wave(b, st, d, rng):
    """Blocks rising and falling in a travelling wave."""
    w = 40.0
    rest(b, st, w=44)
    n = rng.randint(8, 10)
    bl = rng.uniform(32, 38)
    amp = rng.uniform(14, 22) + 6 * d
    period = rng.uniform(2.2, 2.8)
    for i in range(n):
        c = (st.x + bl / 2, st.y, st.z)
        root = b.prop_root("Piston")
        rig = b.rig(root, "Slide", axis_frame(c, (0, -1, 0)), amp, period, phase=(i * 0.1) % 1, name="Lift")
        block(b, c, bl - 1.5, w, parent=rig, name="PistonDeck", h=40)
        b.line(c[0], st.y, st.z)
        st.x += bl
    block(b, (st.x + 45, st.y, st.z), 90, 44, h=12)
    st.x += 90


def m_turntable(b, st, d, rng):
    """A spinning disc with holes in it."""
    R = rng.uniform(80, 95)
    rest(b, st, w=44)
    c = (st.x + R, st.y, st.z)
    rig = spin(b, c, UP, (rng.uniform(0.07, 0.1) + 0.03 * d) * rng.choice([-1, 1]), rng.random(), "Turntable")
    k = 12
    holes = set(rng.sample([1, 2, 3, 4, 7, 8, 9, 10], 3 + (1 if d > 0.5 else 0)))
    pal = b.theme
    for i in range(k):
        if i in holes:
            continue
        a = TAU * (i + 0.5) / k
        dv = (math.cos(a), 0, math.sin(a))
        mid = add(c, mul(dv, R / 2 + 5.5))
        P(b, "Sector", deck_frame(sub(mid, (0, THICK / 2, 0)), dv), (2 * R * math.sin(math.pi / k) + 1, THICK, R - 21),
          pal["top"] if i % 2 else pal["body"], pal["top_mat"], parent=rig, collide=True)
        P(b, "SectorRim", deck_frame(add(c, add(mul(dv, R - 6), (0, 0.3, 0))), (-dv[2], 0, dv[0])),
          (1.4, 0.5, 2 * R * math.sin(math.pi / k)), pal["edge"], "Neon", parent=rig)
    pillar(b, c, 18, h=10)
    b.samples.append((c[0], st.y, st.z, 2 * R))
    for x in (c[0] - R, c[0], c[0] + R):
        b.line(x, st.y, st.z)
    st.x = c[0] + R
    block(b, (st.x + 50, st.y, st.z), 100, 44, h=12)
    st.x += 100


def m_zigzag_steps(b, st, d, rng):
    """Narrow beams in a zigzag, each a step lower or higher, with sharp corners."""
    w = 30 - 5 * d
    rest(b, st, w=40)
    legs = rng.randint(4, 5)
    pts = [(st.x, st.y, st.z)]
    side = rng.choice([-1, 1])
    for i in range(legs):
        x = pts[-1][0] + rng.uniform(100, 125)
        z = st.z + side * rng.uniform(40, 60) if i < legs - 1 else st.z
        side = -side
        y = pts[-1][1]
        pts.append((x, y, z))
    for a, c in zip(pts, pts[1:]):
        f = unit((c[0] - a[0], 0, c[2] - a[2]))
        L = math.hypot(c[0] - a[0], c[2] - a[2])
        block(b, ((a[0] + c[0]) / 2, a[1], (a[2] + c[2]) / 2), L + 2, w, fwd=f, h=8, name="Beam")
        b.line(a[0], a[1], a[2])
        b.line(c[0] - f[0] * 4, a[1], c[2] - f[2] * 4)
    for (x, y, z), prev in zip(pts[1:], pts[:-1]):
        # the corner pad, a step down onto the next level
        block(b, (x, y, z), w * 1.4, w * 1.4, h=8, name="Corner")
    st.x, st.y, st.z = pts[-1]
    block(b, (st.x + 50, st.y, st.z), 100, 44, h=12)
    st.x += 100


def m_doors(b, st, d, rng):
    """Walls sliding across the bridge with a gap that moves."""
    w = 46.0
    rest(b, st, w=46)
    n = rng.randint(3, 4)
    sp = rng.uniform(90, 110)
    L = n * sp + 60
    x0 = st.x
    tiles(b, x0, L, st.y, st.z, w)
    hole = 28 - 5 * d
    for i in range(n):
        x = x0 + 60 + i * sp
        amp = w - hole
        rz = st.z - w / 2 + hole / 2
        root = b.prop_root("Door")
        rig = b.rig(root, "Slide", axis_frame((x, st.y + 9, rz), (0, 0, 1)), amp, rng.uniform(2.6, 3.2) - 0.4 * d,
                    phase=rng.random(), name="DoorSlide")
        for s in (-1, 1):
            P(b, "DoorPanel", CF((x, st.y + 9, rz + s * (hole / 2 + w / 2))), (5, 18, w), b.theme["danger"], "Neon",
              parent=rig, query=True, transp=0.3, attrs={"ObbyHazard": "Knock"})
        P(b, "DoorFrame", CF((x, st.y + 20, st.z)), (6, 2, w + 8), b.theme["edge"], "Neon")
    b.line(x0, st.y, st.z)
    b.line(x0 + L, st.y, st.z)
    st.x = x0 + L


def m_ring_drop(b, st, d, rng):
    """Pad up to a high ledge, then drive off it and fall through hoops onto a curling ramp."""
    rest(b, st, w=46)
    src = (st.x - 16, st.y, st.z)
    up = rng.uniform(110, 150)
    tgt = (src[0] + 180, st.y + up, st.z)
    pad(b, src, tgt, apex=up + 35)
    x0 = tgt[0] - 40
    block(b, (x0 + 60, tgt[1], st.z), 120, 46, h=14)
    b.line(x0 + 120, tgt[1], st.z)
    lip = x0 + 120
    b.boost(lip - 40, tgt[1], st.z)
    # the fall: rings along a 150-stud/s roll-off
    for k in range(3):
        t = 0.35 + 0.3 * k
        c = (lip + 150 * t, tgt[1] + CAR_UP - 0.5 * G * t * t, st.z)
        hoop(b, c, unit((150, -G * t, 0)), 20 + 3 * k, b.theme["pad"])
    # a long dive ramp that curls back to level
    y_top = tgt[1] - up * 0.55
    L = 300.0
    n = 24
    pts = []
    for i in range(n + 1):
        t = i / n
        x = lip + 25 + L * t
        y = y_top - (up * 0.45 + 20) * ease(t)
        pts.append(((x, y, st.z), UP))
    fixed = []
    for i, (p, _) in enumerate(pts):
        if 0 < i < n:
            f = unit(sub(pts[i + 1][0], pts[i - 1][0]))
        else:
            f = unit(sub(pts[min(i + 1, n)][0], pts[max(i - 1, 0)][0]))
        fixed.append((p, unit((-f[1], f[0], 0.0))))
    ribbon(b, fixed, 52, b.model("DiveRamp", b.roads))
    b.arc((lip, tgt[1] + CAR_UP, st.z), (150, 0, 0), until_y=pts[n // 2][0][1] + CAR_UP + 12)
    for p, _ in fixed[n // 2::3]:
        b.line(p[0], p[1], p[2])
    st.x, st.y = lip + 25 + L, pts[-1][0][1]
    road(b, st, 60, w=46)


def m_tilt_runs(b, st, d, rng):
    """Short platforms banked hard left, right, left: a slalom in the air."""
    rest(b, st, w=44)
    n = rng.randint(4, 6)
    for i in range(n):
        L = rng.uniform(70, 85)
        side = 1 if i % 2 == 0 else -1
        bank = side * math.radians(rng.uniform(16, 22) + 5 * d)
        z = st.z + side * rng.uniform(5, 11)
        c = (st.x + 6 + L / 2, st.y + rng.uniform(-6, 6), z)
        fr = deck_frame(c, (1, 0, 0), bank=bank)
        P(b, "TiltDeck", CF(sub(c, mul(fr.y, 4)), fr.x, fr.y, fr.z), (34, 8, L), b.theme["top"], b.theme["top_mat"], collide=True)
        for s in (-1, 1):
            P(b, "Trim", CF(add(c, add(mul(fr.x, s * 16.5), mul(fr.y, 0.2))), fr.x, fr.y, fr.z), (1, 0.42, L),
              b.theme["edge"], "Neon")
        b.samples.append((c[0], c[1], c[2], 34))
        b.line(c[0] - L / 2 + 8, c[1], c[2])
        b.line(c[0] + L / 2 - 8, c[1], c[2])
        st.x += L + 6
        st.y = c[1]
    st.z = st.z
    block(b, (st.x + 50, st.y, st.z), 100, 44, h=12)
    st.x += 100


def m_corkscrew(b, st, d, rng):
    """Drive round the inside of an invisible tube: a full corkscrew around a glowing rod."""
    w = 32.0
    rest(b, st, w=44)
    road(b, st, 60, w=w, boost=True)
    R = rng.uniform(34, 42)
    L = rng.uniform(380, 460)
    x0, y0, z0 = st.x, st.y, st.z
    cy = y0 + R
    sense = rng.choice([-1, 1])
    n = 56
    pts = []
    for i in range(n + 1):
        t = i / n
        a = sense * TAU * ease5(t)
        p = (x0 + L * t, cy - R * math.cos(a), z0 + R * math.sin(a))
        nrm = (0.0, math.cos(a), -math.sin(a))
        pts.append((p, nrm))
    m = b.model("Corkscrew", b.roads, {"WallRide": True})
    ribbon(b, pts, w, m)
    for p, nrm in pts[::4]:
        b.path.append((p[0] + nrm[0] * CAR_UP, p[1] + nrm[1] * CAR_UP, p[2] + nrm[2] * CAR_UP, "s"))
    P(b, "Rod", axis_frame((x0 + L / 2, cy, z0), (1, 0, 0)), (L * 0.9, 5, 5), b.theme["edge"], "Neon")
    st.x = x0 + L
    road(b, st, 90)


def m_halfpipe(b, st, d, rng):
    """A half-pipe gully: blockers on the floor send you up the walls."""
    floor = 24.0
    rest(b, st, w=60)
    L = rng.uniform(380, 460)
    x0, y0, z0 = st.x, st.y, st.z
    walls = [(12.0, math.radians(26)), (12.0, math.radians(44)), (12.0, math.radians(58))]
    m = b.model("HalfPipe", b.roads, {"WallRide": True})
    ribbon(b, [((x0, y0, z0), UP), ((x0 + L, y0, z0), UP)], floor, m, edge=False)
    for side in (-1, 1):
        q, h = floor / 2, 0.0
        for (sw, a) in walls:
            cq = q + math.cos(a) * sw / 2
            ch = h + math.sin(a) * sw / 2
            nrm = (0.0, math.cos(a), side * math.sin(a))
            zz = z0 - side * cq
            ribbon(b, [((x0, y0 + ch, zz), nrm), ((x0 + L, y0 + ch, zz), nrm)], sw + 0.6, m, edge=False,
                   color=mix(b.theme["top"], b.theme["body"], 0.3))
            q += math.cos(a) * sw
            h += math.sin(a) * sw
        P(b, "Lip", CF((x0 + L / 2, y0 + h + 0.4, z0 - side * (q + 0.4))), (L, 1, 1.4), b.theme["edge"], "Neon")
    nb = int(L // 85)
    for i in range(nb):
        x = x0 + 70 + i * (L - 110) / max(nb - 1, 1)
        side = 1 if i % 2 == 0 else -1
        P(b, "Blocker", CF((x, y0 + 5, z0 - side * 8)), (10, 10, 30), b.theme["danger"], "Neon", parent=b.hazards,
          query=True, attrs={"ObbyHazard": "Knock"})
    b.samples.append((x0 + L / 2, y0, z0, 60))
    for i in range(7):
        b.line(x0 + L * i / 6, y0, z0)
    st.x = x0 + L
    block(b, (st.x + 45, st.y, st.z), 90, 46, h=12)
    st.x += 90


MODULES = {
    "pillars": m_pillar_hops, "cube_climb": m_cube_climb, "cube_drop": m_cube_drop, "loop": m_loop,
    "double_loop": m_double_loop, "barrel": m_barrel_roll, "wallride": m_wall_ride, "pipe": m_pipe,
    "spiral": m_spiral, "spin_bridges": m_spin_bridges, "cross": m_cross, "discs": m_spinner_discs,
    "windmill": m_windmill_launch, "pendulums": m_pendulums, "kicker": m_kicker, "beam": m_beam_sweep,
    "lasers": m_lasers, "checker": m_checker_crumble, "crushers": m_crushers, "slide": m_slide_bridges,
    "pistons": m_piston_wave, "turntable": m_turntable, "zigzag": m_zigzag_steps, "doors": m_doors,
    "ring_drop": m_ring_drop, "tilt": m_tilt_runs, "corkscrew": m_corkscrew, "halfpipe": m_halfpipe,
}


def link(b, st, rng, dy):
    """Hop from the end of one module onto the next module's rest platform, changing height."""
    src = (st.x - 16, st.y, st.z)
    D = rng.uniform(170, 215)
    ty = st.y + dy
    tz = st.lateral(rng, 50)
    tgt = (src[0] + D, ty, tz)
    pad(b, src, tgt, apex=max(dy, 0) + rng.uniform(35, 55))
    st.x, st.y, st.z = tgt[0] - 22, ty, tz
    b.pending_landing = True


def finale(b, st, rng, x_end, y_end, z_end):
    """Pillar hops home: from the last module to the join deck at the level's end (landing at x_end)."""
    if getattr(b, "pending_landing", False):
        block(b, (st.x + 40, st.y, st.z), 80, 50, h=12)
        b.line(st.x + 22, st.y, st.z)
        st.x += 80
        b.pending_landing = False
    src = (st.x - 16, st.y, st.z)
    R = x_end - src[0]
    n = max(1, int(round(R / 200)))
    for i in range(1, n + 1):
        t = i / n
        tx = src[0] + (x_end - src[0]) / n if i == 1 else prev[0] + (x_end - src[0]) / n
        ty = st.y + (y_end - st.y) * ease(t) if i < n else y_end
        tz = st.z + (z_end - st.z) * ease(t) if i < n else z_end
        if i < n:
            ty += rng.uniform(-25, 25)
        tgt = (tx, ty, tz)
        start = src if i == 1 else prev
        pad(b, start, tgt, apex=max(ty - start[1], 0) + rng.uniform(35, 50))
        if i < n:
            pillar(b, tgt, rng.uniform(25, 29), h=rng.uniform(26, 40))
        prev = tgt
