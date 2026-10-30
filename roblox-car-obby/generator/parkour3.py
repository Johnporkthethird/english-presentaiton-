"""Parkour kit v3: every level has its own platform shape, width scale and layout grammar, all on a grid.

b.look = {"shape": ..., "scale": ..., "layout": ..., "lane": ...} is set by the level before modules run.
Modules start with a rest platform (checkpoint) at the state and end on solid ground heading +X.
"""
import math
from geom import CF, deck_frame, axis_frame, add, sub, mul, unit, length, cross, dot, lerp, rot_axis, rot_y, UP
from builder import THICK, G, CAR_UP, mix
from parkour import P, chevron, hoop, ribbon, spin, St, ease, ease5, bump, TAU
import parkour as V2

SHAPES = ["square", "disc", "hex", "oct", "diamond", "slats", "plus"]


def snap(v, step):
    return round(v / step) * step


# ===================================================================== shapes
def _layers(b, top, fr, parts, h, parent, name, collide, attrs):
    """parts: list of (local_rotation_yaw, sx, sz, kind) footprints that union into the shape."""
    pal = b.theme
    for i, (yaw, sx, sz, kind) in enumerate(parts):
        R = fr * rot_y(yaw)
        if kind == "cyl":
            c = sub(top, (0, h / 2, 0))
            P(b, name, axis_frame(c, UP), (h, sx, sx), pal["body"], pal["body_mat"], parent=parent, collide=collide,
              attrs=attrs if i == 0 else None, transp=pal.get("body_transp", 0.0))
            P(b, "Top", axis_frame(add(top, (0, 0.06, 0)), UP), (0.12, sx - 1.8, sx - 1.8), pal["top"], pal["top_mat"], parent=parent)
            P(b, "Rim", axis_frame(sub(top, (0, 0.5, 0)), UP), (1.0, sx + 0.8, sx + 0.8), pal["edge"], "Neon", parent=parent)
        else:
            P(b, name, CF(sub(top, mul(R.y, h / 2)), R.x, R.y, R.z), (sx, h, sz), pal["body"], pal["body_mat"], parent=parent,
              collide=collide, attrs=attrs if i == 0 else None, transp=pal.get("body_transp", 0.0))
            P(b, "Top", CF(add(top, mul(R.y, 0.06)), R.x, R.y, R.z), (sx - 1.6, 0.12, sz - 1.6), pal["top"], pal["top_mat"],
              parent=parent)
            P(b, "Rim", CF(sub(top, mul(R.y, 0.5)), R.x, R.y, R.z), (sx + 0.8, 1.0, sz + 0.8), pal["edge"], "Neon", parent=parent)


def tile(b, top, s, fwd=(1, 0, 0), h=10.0, parent=None, name="Platform", collide=True, shape=None, attrs=None):
    """One platform about `s` across: the level's own world object, or a plain shape when it rides on a rig."""
    if getattr(b, "world", None) is not None and parent is None and shape is None:
        b.world.plat(b, top, s, b.rng)
        return
    shape = shape or b.look["shape"]
    fr = deck_frame(top, fwd)
    if shape == "square":
        parts = [(0, s, s, "box")]
    elif shape == "disc":
        parts = [(0, s, s, "cyl")]
    elif shape == "hex":
        parts = [(a, s, s / math.sqrt(3), "box") for a in (0, math.pi / 3, 2 * math.pi / 3)]
    elif shape == "oct":
        q = s * 0.92
        parts = [(0, q, q, "box"), (math.pi / 4, q, q, "box")]
    elif shape == "diamond":
        q = s / math.sqrt(2) * 1.05
        parts = [(math.pi / 4, q, q, "box")]
    elif shape == "plus":
        parts = [(0, s, s * 0.46, "box"), (math.pi / 2, s, s * 0.46, "box")]
    else:  # slats: planks across the way you drive
        n = max(3, int(s // 9))
        pitch = s / n
        for k in range(n):
            c = add(top, mul(fr.z, -s / 2 + pitch * (k + 0.5)))
            _layers(b, c, fr, [(0, s, pitch - 2.0, "box")], h, parent, name, collide, attrs if k == 0 else None)
        b.samples.append((top[0], top[1], top[2], s))
        return
    _layers(b, top, fr, parts, h, parent, name, collide, attrs)
    b.samples.append((top[0], top[1], top[2], s))


def run(b, x0, x1, y, z, w, h=10.0, name="Deck", parent=None, shape=None):
    """Solid ground from x0 to x1: the level's world deck, or a chain of plain shapes."""
    if getattr(b, "world", None) is not None and parent is None and shape is None:
        b.world.deck(b, x0, x1, y, z, w)
        # one smooth invisible floor flush with the top, so seams between slats, keys or bricks never catch a wheel
        P(b, "Floor", CF(((x0 + x1) / 2, y - 1.0, z)), (x1 - x0, 2, w * 0.8), (255, 255, 255), parent=b.roads,
          collide=True, transp=1.0)
        return
    shape = shape or b.look["shape"]
    L = x1 - x0
    if shape == "square":
        V2.block(b, ((x0 + x1) / 2, y, z), L, w, h=h, parent=parent, name=name)
        return
    if shape == "slats":
        n = max(1, int(round(L / 9)))
        pitch = L / n
        fr = deck_frame((x0, y, z), (1, 0, 0))
        for k in range(n):
            c = (x0 + pitch * (k + 0.5), y, z)
            _layers(b, c, fr, [(0, w, pitch - 2.0, "box")], h, parent, name, True, None)
        for k in range(0, n, max(1, n // 6)):
            b.samples.append((x0 + pitch * k, y, z, w))
        return
    step = w * 0.78
    n = max(1, int(math.ceil((L - w) / step)) + 1)
    for k in range(n):
        cx = x0 + w / 2 + (L - w) * (k / (n - 1) if n > 1 else 0.5)
        tile(b, (cx, y, z), w, h=h, parent=parent, name=name, shape=shape)


def W(b, base):
    """A width in this level's scale, kept on a 2-stud grid."""
    return max(18.0, snap(base * b.look["scale"], 2))


def rest(b, st, L=None, w=None):
    arrived = getattr(b, "pending_landing", False)
    b.pending_landing = False
    w = w or W(b, 52)
    L = L or max(70.0, w * 1.2)
    run(b, st.x, st.x + L, st.y, st.z, w, h=12)
    b.checkpoint(st.x + 18, st.y, st.z, w)
    if not arrived:
        b.line(st.x, st.y, st.z)
    b.line(st.x + L - 6, st.y, st.z)
    st.x += L
    st.w = w


def landing(b, st, tx, ty, tz, L=None, w=None):
    w = w or W(b, 56)
    L = L or max(130.0, w * 2.2)
    x0 = tx - L * 0.3
    run(b, x0, x0 + L, ty, tz, w, h=12)
    b.line(x0 + L - 6, ty, tz)
    st.x, st.y, st.z, st.w = x0 + L, ty, tz, w


def lane_z(b, st, k):
    return b.zc + k * b.look["lane"]


# ===================================================================== hop chains (the level's layout grammar)
def hop_targets(b, st, rng, n, d, layout=None):
    """Grid-snapped targets for a chain of pad hops, following the level's layout grammar."""
    layout = layout or b.look["layout"]
    out = []
    x, y = st.x, st.y
    lane0 = round((st.z - b.zc) / b.look["lane"])
    spacing = snap(rng.choice([180, 195, 210]) + 20 * d, 5)
    for i in range(n):
        x += spacing
        if layout == "straight":
            yy, k = y, lane0
        elif layout == "rising":
            yy, k = y + 45 * (i + 1), lane0
        elif layout == "falling":
            yy, k = y - 45 * (i + 1), lane0
        elif layout == "lanes":
            yy, k = y, (lane0 + (1 if i % 2 == 0 else -1)) if abs(lane0) < 2 else (lane0 - (1 if lane0 > 0 else -1) * (i % 2 == 0))
        elif layout == "wave":
            yy, k = y + 45 * math.sin((i + 1) * math.pi / 2), lane0
        else:  # "steps": up two, down one
            yy, k = y + (45 if i % 3 != 2 else -45) * 1.0, lane0
            y = yy - 45 * (i + 1) if False else y
        yy = max(b.ylo + 40, min(b.yhi - 40, snap(yy, 15)))
        out.append((x, yy, b.zc + k * b.look["lane"]))
    return out


def m_hops(b, st, d, rng, layout=None, n=None, s=None):
    rest(b, st)
    n = n or rng.randint(3, 5)
    s = s or W(b, 50)
    src = (st.x - 16, st.y, st.z)
    tg = hop_targets(b, St(src[0], src[1], src[2], 0, b.zc), rng, n, d, layout)
    for t in tg:
        pad_to(b, src, t)
        tile(b, t, s, h=rng.choice([14, 22, 30]))
        src = t
    D = 200
    tgt = (src[0] + D, src[1], src[2])
    pad_to(b, src, tgt)
    landing(b, st, *tgt)


def pad_to(b, src, tgt, rings=0):
    dy = tgt[1] - src[1]
    return V2.pad(b, src, tgt, apex=max(dy, 0) + 42, rings=rings)


def m_hop_line(b, st, d, rng):
    m_hops(b, st, d, rng, layout="straight", n=rng.randint(4, 5))


def m_hop_rise(b, st, d, rng):
    m_hops(b, st, d, rng, layout="rising", n=rng.randint(3, 4))


def m_hop_fall(b, st, d, rng):
    m_hops(b, st, d, rng, layout="falling", n=rng.randint(3, 4))


def m_hop_lanes(b, st, d, rng):
    m_hops(b, st, d, rng, layout="lanes", n=rng.randint(4, 5))


def m_hop_wave(b, st, d, rng):
    m_hops(b, st, d, rng, layout="wave", n=4)


def m_hop_tiny(b, st, d, rng):
    """Small targets: the shape at its smallest."""
    m_hops(b, st, d, rng, layout=None, n=4, s=max(30.0, W(b, 38) - 8 * d))


def m_spiral_tower(b, st, d, rng):
    """Hop round a glowing tower, climbing a level each hop."""
    rest(b, st)
    R = 95.0
    c = (st.x + R + 30, st.y, st.z)
    n = 5
    src = (st.x - 16, st.y, st.z)
    pal = b.theme
    top_y = st.y + 40 * n
    P(b, "Tower", axis_frame((c[0], (st.y - 60 + top_y + 40) / 2, c[2]), UP), (top_y - st.y + 100, 34, 34), pal["body"],
      pal["body_mat"], collide=True)
    P(b, "TowerBand", axis_frame((c[0], top_y + 10, c[2]), UP), (3, 36, 36), pal["edge"], "Neon")
    for i in range(n):
        a = math.pi + (i + 1) * (TAU / 6)
        t = (c[0] + R * math.cos(a), st.y + 40 * (i + 1), c[2] + R * math.sin(a))
        t = (snap(t[0], 1), t[1], snap(t[2], 1))
        pad_to(b, src, t)
        tile(b, t, W(b, 48), h=14)
        src = t
    tgt = (src[0] + 210, src[1] - 40, st.z)
    pad_to(b, src, tgt)
    landing(b, st, *tgt)


def m_long_jump(b, st, d, rng):
    """One huge flight through a line of hoops onto a wide pad."""
    rest(b, st, L=110)
    b.boost(st.x - 60, st.y, st.z)
    src = (st.x - 16, st.y, st.z)
    tgt = (src[0] + snap(rng.uniform(340, 400), 10), st.y + snap(rng.uniform(-60, 30), 15), st.z)
    V2.pad(b, src, tgt, apex=max(tgt[1] - src[1], 0) + 80, rings=4)
    landing(b, st, *tgt, w=W(b, 64))


def m_drop_shaft(b, st, d, rng):
    """Pad up onto a high ledge, then drive off and drop straight down through hoops onto a big pad."""
    rest(b, st)
    src = (st.x - 16, st.y, st.z)
    up = snap(rng.uniform(120, 150), 15)
    tgt = (src[0] + 180, st.y + up, st.z)
    pad_to(b, src, tgt)
    w = W(b, 46)
    run(b, tgt[0] - 40, tgt[0] + 80, tgt[1], st.z, w, h=14)
    lip = tgt[0] + 80
    b.line(lip - 6, tgt[1], st.z)
    drop = up + snap(rng.uniform(20, 60), 15)
    for k in range(3):
        t = 0.3 + 0.28 * k
        c = (lip + 120 * t, tgt[1] + CAR_UP - 0.5 * G * t * t, st.z)
        hoop(b, c, unit((120, -G * t, 0)), 18 + 2 * k, b.theme["pad"])
    ly = tgt[1] - drop
    b.arc((lip, tgt[1] + CAR_UP, st.z), (130, 0, 0), until_y=ly + CAR_UP + 6)
    L = 260.0
    run(b, lip + 20, lip + 20 + L, ly, st.z, W(b, 70), h=14)
    b.line(lip + 20 + L - 6, ly, st.z)
    st.x, st.y = lip + 20 + L, ly


# ===================================================================== rotating pieces
def m_rot_door(b, st, d, rng):
    """Walls that turn across the deck with one gap in them: drive through the gap when it reaches the bottom."""
    w = W(b, 46)
    rest(b, st, w=w)
    n = rng.randint(2, 3)
    L = n * 130 + 60
    x0 = st.x
    run(b, x0, x0 + L, st.y, st.z, w)
    R = w / 2 + 16
    for i in range(n):
        x = x0 + 80 + i * 130
        hub = (x, st.y + R + 1.5, st.z)  # the blades' corners clear the deck (they used to turn through it)
        rig = spin(b, hub, (1, 0, 0), rng.choice([-1, 1]) * (0.16 + 0.08 * d), rng.random(), "RotDoor")
        k = 10
        gap = rng.randrange(k)
        for j in range(k):
            if j == gap:
                continue
            a = TAU * (j + 0.5) / k
            dv = (0, math.cos(a), math.sin(a))
            P(b, "DoorBlade", deck_frame(add(hub, mul(dv, R / 2)), dv, up=(1, 0, 0)),
              (2 * (R / 2 + 2) * math.sin(math.pi / k) * 1.9, 3, R - 6), b.theme["danger"], "Neon", parent=rig, query=True,
              transp=0.25, attrs={"ObbyHazard": "Knock"})
        P(b, "DoorHub", axis_frame(hub, (1, 0, 0)), (4, 10, 10), b.theme["edge"], "Neon", parent=rig)
        hoop(b, hub, (1, 0, 0), R + 0.6, b.theme["edge"], n=24, th=1.4)
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


def m_log(b, st, d, rng):
    """A spinning log for a bridge: its ridges come over the top - jump them."""
    w = W(b, 44)
    rest(b, st, w=w)
    r = 16.0
    L = snap(rng.uniform(220, 280), 10)
    axis_y = st.y - r
    c = (st.x + L / 2, axis_y, st.z)
    rig = spin(b, c, (1, 0, 0), rng.choice([-1, 1]) * (0.22 + 0.1 * d), rng.random(), "Log")
    pal = b.theme
    P(b, "Log", axis_frame(c, (1, 0, 0)), (L, 2 * r, 2 * r), pal["top"], pal["top_mat"], parent=rig, collide=True, shape=2)
    for k in range(3):
        a = TAU * k / 3
        dv = (0, math.cos(a), math.sin(a))
        P(b, "Ridge", deck_frame(add(c, mul(dv, r + 1.2)), (1, 0, 0), up=dv), (5, 3, L - 10), pal["danger"], "Neon",
          parent=rig, query=True, attrs={"ObbyHazard": "Knock"})
    for x in (st.x, st.x + L):
        P(b, "LogCap", axis_frame((x, axis_y, st.z), (1, 0, 0)), (2, 2 * r + 3, 2 * r + 3), pal["edge"], "Neon")
    b.samples.append((c[0], st.y, st.z, 2 * r))
    for k in range(5):
        b.line(st.x + L * k / 4, st.y, st.z)
    st.x += L
    run(b, st.x, st.x + 90, st.y, st.z, w, h=12)
    st.x += 90


def m_cross(b, st, d, rng):
    rest(b, st)
    R = snap(rng.uniform(78, 90), 2)
    c = (st.x + R + 6, st.y, st.z)
    rig = spin(b, c, UP, (rng.uniform(0.045, 0.06) + 0.015 * d) * rng.choice([-1, 1]), rng.random(), "Cross")
    aw = W(b, 32)
    for k in range(4):
        a = TAU * k / 4
        f = (math.cos(a), 0, math.sin(a))
        V2.block(b, add(c, mul(f, R / 2 + 12)), R - 20, aw, fwd=f, parent=rig, name="Arm")
    tile(b, c, 30, h=20)  # (inside the arms' sweep: they start 22 out)
    for x in (c[0] - R, c[0], c[0] + R):
        b.line(x, st.y, st.z)
    st.x = c[0] + R + 4
    run(b, st.x, st.x + 100, st.y, st.z, W(b, 46), h=12)
    st.x += 100


def m_spin_bridges(b, st, d, rng):
    rest(b, st)
    n = 3
    Lb = snap(rng.uniform(96, 110), 2)
    wb = W(b, 34)
    speed = rng.uniform(0.045, 0.06) + 0.02 * d
    x = st.x
    for i in range(n):
        c = (x + 8 + Lb / 2, st.y, st.z)
        rig = spin(b, c, UP, speed * (1 if i % 2 == 0 else -1), (-i * (Lb + 14) / 120.0 * speed) % 1, "SpinBridge")
        V2.block(b, c, Lb, wb, parent=rig, name="SpinDeck")
        P(b, "Hub", axis_frame(sub(c, (0, 6, 0)), UP), (12, 22, 22), b.theme["edge"], "Neon")
        b.line(c[0], st.y, st.z)
        x += Lb + 14
    st.x = x + 6
    run(b, st.x, st.x + 100, st.y, st.z, W(b, 46), h=12)
    st.x += 100


def m_sweepers(b, st, d, rng):
    """Islands of the level's shape, each with a bar sweeping across: jump the low ones."""
    rest(b, st)
    n = 3
    s = max(W(b, 100), 80.0)
    for i in range(n):
        c = (st.x + 24 + s / 2, st.y, st.z)
        run(b, st.x, st.x + 26, st.y, st.z, W(b, 28), h=8, shape="square")
        tile(b, c, s, h=18)
        low = rng.random() < 0.6
        rig = spin(b, add(c, (0, 3, 0)), UP, rng.choice([-1, 1]) * (rng.uniform(0.22, 0.32) + 0.12 * d), rng.random(), "Sweeper")
        if low:
            P(b, "SweepLaser", CF(add(c, (0, 3.2, 0))), (s - 6, 3, 2.4), b.theme["danger"], "Neon", parent=rig, query=True,
              attrs={"ObbyHazard": "Burn"})
        else:
            P(b, "SweepWall", CF(add(c, (0, 7, 0))), (s - 6, 14, 3), b.theme["danger"], "Neon", parent=rig, query=True,
              transp=0.15, attrs={"ObbyHazard": "Knock"})
        b.line(c[0] - s / 2, st.y, st.z)
        b.line(c[0] + s / 2, st.y, st.z)
        st.x = c[0] + s / 2
    run(b, st.x, st.x + 26, st.y, st.z, W(b, 28), h=8, shape="square")
    st.x += 26
    run(b, st.x, st.x + 100, st.y, st.z, W(b, 46), h=12)
    st.x += 100


def m_turntable(b, st, d, rng):
    rest(b, st)
    V2.m_turntable.__wrapped__(b, st, d, rng) if hasattr(V2.m_turntable, "__wrapped__") else _turntable_body(b, st, d, rng)


def _turntable_body(b, st, d, rng):
    R = snap(rng.uniform(80, 95), 2)
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
    tile(b, c, 22, h=10)  # (inside the sectors' sweep: they start 16 out)
    b.samples.append((c[0], st.y, st.z, 2 * R))
    for x in (c[0] - R, c[0], c[0] + R):
        b.line(x, st.y, st.z)
    st.x = c[0] + R
    run(b, st.x, st.x + 100, st.y, st.z, W(b, 46), h=12)
    st.x += 100


def m_windmill(b, st, d, rng):
    rest(b, st, L=110)
    src = (st.x - 16, st.y, st.z)
    tgt = (src[0] + snap(rng.uniform(270, 320), 10), st.y + snap(rng.uniform(-45, 15), 15), st.z)
    H, V, T = V2.pad(b, src, tgt, apex=55)
    t = T * 0.45
    hub = (src[0] + H * t, src[1] + CAR_UP + V * t - 0.5 * G * t * t + 34, st.z)
    rig = spin(b, hub, (1, 0, 0), rng.choice([-1, 1]) * (0.1 + 0.06 * d), rng.random(), "Windmill")
    blades = rng.choice([3, 4])
    for k in range(blades):
        a = TAU * k / blades
        dv = (0, math.cos(a), math.sin(a))
        P(b, "Blade", deck_frame(add(hub, mul(dv, 34)), dv, up=(1, 0, 0)), (10, 5, 56), b.theme["danger"], "Neon",
          parent=rig, query=True, attrs={"ObbyHazard": "Crush"})
    P(b, "MillHub", axis_frame(hub, (1, 0, 0)), (8, 16, 16), b.theme["edge"], "Neon", parent=rig)
    hoop(b, hub, (1, 0, 0), 64, b.theme["edge"], n=32, th=1.6)
    landing(b, st, *tgt)


# ===================================================================== moving pieces
def m_pendulums(b, st, d, rng):
    rest(b, st)
    n = rng.randint(3, 4)
    Lp = snap(rng.uniform(64, 74), 2)
    H = 70.0
    theta = rng.uniform(28, 34) + 6 * d
    period = rng.uniform(2.8, 3.4)
    x = st.x
    for i in range(n):
        c = (x + 6 + Lp / 2, st.y, st.z)
        pivot = (c[0], st.y + H, st.z)
        root = b.prop_root("Pendulum")
        rig = b.rig(root, "Hinge", axis_frame(pivot, (1, 0, 0)), theta, period, phase=(i * 0.18) % 1,
                    keys="0:0 0.25:1 0.5:0 0.75:-1", name="Swing")
        tile(b, c, Lp, h=8, parent=rig, name="SwingDeck")
        for s in (-1, 1):
            P(b, "Cable", CF((c[0] + s * (Lp / 2 - 6), (c[1] + pivot[1]) / 2, st.z)), (0.8, H, 0.8), b.theme["edge"], "Neon",
              parent=rig)
        P(b, "Anchor", CF(pivot), (Lp, 3, 3), b.theme["body"], b.theme["body_mat"])
        b.line(c[0], st.y, st.z)
        x += Lp + 12
    st.x = x
    run(b, st.x, st.x + 100, st.y, st.z, W(b, 46), h=12)
    st.x += 100


def m_slide(b, st, d, rng):
    w = W(b, 40)
    rest(b, st, w=w)
    for i in range(rng.randint(2, 3)):
        gap = snap(rng.uniform(64, 80), 2)
        side = rng.choice([-1, 1])
        c = (st.x + gap / 2, st.y, st.z)
        root = b.prop_root("SlideBridge")
        rig = b.rig(root, "Slide", axis_frame(c, (0, 0, side)), w + 10, rng.uniform(2.8, 3.4) - 0.5 * d,
                    phase=rng.random(), keys="0:0 0.45:0 0.55:1 0.9:1", name="Slide")
        V2.block(b, c, gap + 2, w, parent=rig, name="BridgeDeck")
        b.line(st.x + gap, st.y, st.z)
        st.x += gap
        run(b, st.x, st.x + 90, st.y, st.z, w, h=10)
        st.x += 90
        b.line(st.x - 6, st.y, st.z)


def m_pistons(b, st, d, rng):
    w = W(b, 40)
    rest(b, st, w=w)
    n = rng.randint(8, 10)
    bl = snap(rng.uniform(32, 38), 2)
    amp = rng.uniform(14, 22) + 6 * d
    period = rng.uniform(2.2, 2.8)
    for i in range(n):
        c = (st.x + bl / 2, st.y, st.z)
        root = b.prop_root("Piston")
        rig = b.rig(root, "Slide", axis_frame(c, (0, -1, 0)), amp, period, phase=(i * 0.1) % 1, name="Lift")
        V2.block(b, c, bl - 1.5, w, parent=rig, name="PistonDeck", h=40)
        b.line(c[0], st.y, st.z)
        st.x += bl
    run(b, st.x, st.x + 90, st.y, st.z, w, h=12)
    st.x += 90


def m_crushers(b, st, d, rng):
    w = W(b, 40)
    rest(b, st, w=w)
    n = rng.randint(3, 5)
    sp = snap(rng.uniform(70, 88), 2)
    L = n * sp + 70
    x0 = st.x
    run(b, x0, x0 + L, st.y, st.z, w)
    H = 40.0
    period = rng.uniform(1.9, 2.4) - 0.3 * d
    dph = rng.choice([0.16, 0.2, 0.25])
    for i in range(n):
        x = x0 + 55 + i * sp
        bl = 28.0
        rc = (x, st.y + H + 9, st.z)
        for s in (-1, 1):
            P(b, "PressRail", CF((x, st.y + H / 2 + 12, st.z + s * (w / 2 + 3))), (4, H + 26, 4), b.theme["body"],
              b.theme["body_mat"], collide=True)
        P(b, "PressCap", CF((x, st.y + H + 25, st.z)), (bl + 6, 4, w + 10), b.theme["edge"], "Neon")
        root = b.prop_root("Crusher")
        rig = b.rig(root, "Slide", axis_frame(rc, (0, -1, 0)), H + 1, period, phase=(i * dph) % 1,
                    keys="0:0 0.42:0 0.5:1 0.68:1 0.96:0", name="Press")
        P(b, "Press", CF(rc), (bl, 18, w + 4), b.theme["body"], "Metal", parent=rig, query=True, attrs={"ObbyHazard": "Crush"})
        P(b, "PressEdge", CF(add(rc, (0, -9.2, 0))), (bl + 0.4, 0.6, w + 4.4), b.theme["danger"], "Neon", parent=rig)
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


def m_doors(b, st, d, rng):
    w = W(b, 46)
    rest(b, st, w=w)
    n = rng.randint(3, 4)
    sp = snap(rng.uniform(90, 110), 2)
    L = n * sp + 60
    x0 = st.x
    run(b, x0, x0 + L, st.y, st.z, w)
    hole = max(22.0, 28 - 5 * d)
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
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


# ===================================================================== skill pieces
def m_lasers(b, st, d, rng):
    w = W(b, 40)
    rest(b, st, w=w)
    n = rng.randint(5, 7)
    sp = snap(rng.uniform(52, 66), 2)
    L = n * sp + 60
    x0 = st.x
    run(b, x0, x0 + L, st.y, st.z, w)
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
            P(b, "Laser", CF((x, st.y + hy, st.z)), (1.2, th, w + 2), b.theme["danger"], "Neon", parent=b.hazards, query=True,
              transp=0.1, attrs={"ObbyHazard": "Zap", "ZapFX": True, "ZapPeriod": period, "ZapOn": on, "ZapPhase": ph})
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


def m_limbo(b, st, d, rng):
    """A long beam with low lasers sweeping round: jump them."""
    w = max(20.0, W(b, 26) - 3 * d)
    rest(b, st)
    L = snap(rng.uniform(460, 540), 10)
    x0 = st.x
    run(b, x0, x0 + L, st.y, st.z, w, h=8, shape="square")
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
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


def m_crumble(b, st, d, rng):
    """A path of small tiles that fall away under you, in the level's shape."""
    rest(b, st)
    s = max(26.0, W(b, 30))
    n = rng.randint(12, 16)
    delay = 0.4 - 0.15 * d
    for i in range(n):
        m = b.model("CrumbleTile", b.hazards, {"ObbyCrumble": float(delay)})
        c = (st.x + i * (s - 2) + s / 2, st.y, st.z)
        tile(b, c, s, h=6, parent=m, name="Tile")
        b.line(c[0], st.y, st.z)
    st.x += n * (s - 2)
    run(b, st.x, st.x + 100, st.y, st.z, W(b, 46), h=12)
    st.x += 100


def m_conveyors(b, st, d, rng):
    """Belts that shove you sideways, alternating, on a deck with no rails."""
    w = W(b, 40)
    rest(b, st, w=w)
    for i in range(rng.randint(4, 6)):
        L = snap(rng.uniform(70, 90), 2)
        side = 1 if i % 2 == 0 else -1
        sp = rng.uniform(28, 40) + 16 * d
        V2.block(b, (st.x + L / 2, st.y, st.z), L - 1, w, name="Belt",
                 attrs={"Conveyor": float(sp), "ConveyorDir": ("Vector3", 0.0, 0.0, float(side))})
        for k in range(2):
            chevron(b, (st.x + L * (0.3 + 0.4 * k), st.y + 0.3, st.z), (0, 0, side), 12, b.theme["pad"])
        b.line(st.x + L / 2, st.y, st.z)
        st.x += L
    run(b, st.x, st.x + 90, st.y, st.z, w, h=12)
    st.x += 90


def m_ice_rink(b, st, d, rng):
    """A wide slippery deck with holes cut in it: slide round them."""
    rest(b, st)
    w = max(W(b, 100), 82.0)
    L = snap(rng.uniform(320, 380), 10)
    x0 = st.x
    cell = 40.0
    nx, nz = int(L // cell), int(w // cell)
    holes = set()
    for i in range(1, nx - 1):
        if i % 2 == 1:
            holes.add((i, rng.randrange(nz)))
    path = []
    for i in range(nx):
        free = [j for j in range(nz) if (i, j) not in holes]
        for j in range(nz):
            if (i, j) in holes:
                continue
            c = (x0 + cell * (i + 0.5), st.y, st.z - w / 2 + cell * (j + 0.5))
            V2.block(b, c, cell - 1, cell - 1, h=8, name="Ice")
        jj = min(free, key=lambda j: abs(st.z - w / 2 + cell * (j + 0.5) - st.z))
        path.append((x0 + cell * (i + 0.5), st.z - w / 2 + cell * (jj + 0.5)))
    P(b, "IceSlip", CF((x0 + L / 2, st.y + 2.5, st.z)), (L, 7, w), (255, 255, 255), parent=b.hazards, transp=1, query=True,
      attrs={"ObbyHazard": "Slip"})
    for x, z in path:
        b.line(x, st.y, z)
    st.x = x0 + nx * cell
    run(b, st.x, st.x + 90, st.y, st.z, W(b, 46), h=12)
    st.x += 90


def m_bumpers(b, st, d, rng):
    """A wide plate full of bumpers that throw you around."""
    rest(b, st)
    w = max(W(b, 84), 70.0)
    L = snap(rng.uniform(320, 380), 10)
    x0 = st.x
    run(b, x0, x0 + L, st.y, st.z, w)
    rows = int((L - 80) // 52)
    for r in range(rows):
        x = x0 + 60 + r * 52
        cols = 3 if r % 2 == 0 else 2
        for c in range(cols):
            zz = st.z + (c - (cols - 1) / 2) * (w / 3.2)
            P(b, "Bumper", axis_frame((x, st.y + 5, zz), UP), (10, 16, 16), b.theme["danger"], "Neon", parent=b.hazards,
              query=True, shape=2, attrs={"ObbyHazard": "Knock"})
            P(b, "BumperCap", axis_frame((x, st.y + 10.4, zz), UP), (0.8, 18, 18), b.theme["pad"], "Neon", shape=2)
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


def m_split(b, st, d, rng):
    """Two lanes side by side: crushers on one, lasers on the other. Pick one."""
    rest(b, st)
    w = W(b, 32)
    L = snap(rng.uniform(380, 440), 10)
    x0 = st.x
    off = w / 2 + 14
    for s in (-1, 1):
        run(b, x0, x0 + L, st.y, st.z + s * off, w)
    run(b, x0, x0 + 40, st.y, st.z, 2 * off + w, shape="square")
    run(b, x0 + L - 40, x0 + L, st.y, st.z, 2 * off + w, shape="square")
    period = rng.uniform(1.9, 2.3)
    for i in range(4):
        x = x0 + 80 + i * (L - 140) / 3
        # left: presses
        rc = (x, st.y + 49, st.z - off)
        root = b.prop_root("Crusher")
        rig = b.rig(root, "Slide", axis_frame(rc, (0, -1, 0)), 41, period, phase=(i * 0.22) % 1,
                    keys="0:0 0.42:0 0.5:1 0.68:1 0.96:0", name="Press")
        P(b, "Press", CF(rc), (24, 18, w + 2), b.theme["body"], "Metal", parent=rig, query=True, attrs={"ObbyHazard": "Crush"})
        P(b, "PressEdge", CF(add(rc, (0, -9.2, 0))), (24.4, 0.6, w + 2.4), b.theme["danger"], "Neon", parent=rig)
        # right: a laser gate
        P(b, "Laser", CF((x, st.y + 3.2, st.z + off)), (1.2, 3, w + 2), b.theme["danger"], "Neon", parent=b.hazards, query=True,
          transp=0.1, attrs={"ObbyHazard": "Zap", "ZapFX": True, "ZapPeriod": period, "ZapOn": period * 0.5,
                             "ZapPhase": (i * 0.27) % 1})
        P(b, "GateTop", CF((x, st.y + 30, st.z + off)), (3, 1.5, w + 4), b.theme["edge"], "Neon")
    b.line(x0 + 20, st.y, st.z)
    b.line(x0 + 60, st.y, st.z + off)
    b.line(x0 + L - 60, st.y, st.z + off)
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


def m_slalom(b, st, d, rng):
    """Posts in a tight weave on a wide deck."""
    rest(b, st)
    w = max(W(b, 64), 56.0)
    n = rng.randint(5, 7)
    sp = snap(rng.uniform(62, 74) - 8 * d, 2)
    L = n * sp + 70
    x0 = st.x
    run(b, x0, x0 + L, st.y, st.z, w)
    for i in range(n):
        x = x0 + 50 + i * sp
        side = 1 if i % 2 == 0 else -1
        bw = w * 0.6
        zz = st.z + side * (w / 2 - bw / 2)
        P(b, "Gate", CF((x, st.y + 7, zz)), (8, 14, bw), b.theme["body"], b.theme["body_mat"], parent=b.hazards, collide=True)
        P(b, "GateGlow", CF((x, st.y + 14.3, zz)), (8.4, 0.6, bw), b.theme["danger"], "Neon")
        b.line(x, st.y, st.z - side * bw / 2)
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


def m_zigzag(b, st, d, rng):
    """Sharp corners on a narrow path, on the lane grid."""
    w = max(22.0, W(b, 30) - 4 * d)
    rest(b, st)
    legs = 4
    pts = [(st.x, st.y, st.z)]
    lane = b.look["lane"]
    for i in range(legs):
        x = pts[-1][0] + 110
        z = st.z + (lane * 0.7 if i % 2 == 0 else -lane * 0.7) if i < legs - 1 else st.z
        pts.append((x, st.y, z))
    for a, c in zip(pts, pts[1:]):
        f = unit((c[0] - a[0], 0, c[2] - a[2]))
        Ln = math.hypot(c[0] - a[0], c[2] - a[2])
        V2.block(b, ((a[0] + c[0]) / 2, a[1], (a[2] + c[2]) / 2), Ln + 2, w, fwd=f, h=8, name="Beam")
        b.line(a[0], a[1], a[2])
    for (x, y, z) in pts[1:]:
        tile(b, (x, y, z), w * 1.5, h=8, name="Corner")
    st.x, st.y, st.z = pts[-1]
    run(b, st.x, st.x + 100, st.y, st.z, W(b, 46), h=12)
    st.x += 100


# ===================================================================== hero stunts (each capped to a few levels)
def m_loop(b, st, d, rng):
    V2.m_loop(b, st, d, rng)


def m_double_loop(b, st, d, rng):
    V2.m_double_loop(b, st, d, rng)


MODULES = {
    # hops (the shape and layout of the level make these look different everywhere)
    "hop_line": m_hop_line, "hop_rise": m_hop_rise, "hop_fall": m_hop_fall, "hop_lanes": m_hop_lanes,
    "hop_wave": m_hop_wave, "hop_tiny": m_hop_tiny, "spiral_tower": m_spiral_tower, "long_jump": m_long_jump,
    "drop_shaft": m_drop_shaft,
    # rotating
    "rot_door": m_rot_door, "log": m_log, "cross": m_cross, "spin_bridges": m_spin_bridges, "sweepers": m_sweepers,
    "turntable": lambda b, st, d, rng: (rest(b, st), _turntable_body(b, st, d, rng)), "windmill": m_windmill,
    # moving
    "pendulums": m_pendulums, "slide": m_slide, "pistons": m_pistons, "crushers": m_crushers, "doors": m_doors,
    # skill
    "lasers": m_lasers, "limbo": m_limbo, "crumble": m_crumble, "conveyors": m_conveyors, "ice_rink": m_ice_rink,
    "bumpers": m_bumpers, "split": m_split, "slalom": m_slalom, "zigzag": m_zigzag,
    # hero stunts
    "loop": m_loop, "double_loop": m_double_loop, "barrel": V2.m_barrel_roll, "wallride": V2.m_wall_ride,
    "pipe": V2.m_pipe, "corkscrew": V2.m_corkscrew, "spiral": V2.m_spiral, "halfpipe": V2.m_halfpipe,
    "kicker": V2.m_kicker, "tilt": V2.m_tilt_runs,
}
HERO = {"loop": 7, "double_loop": 4, "barrel": 4, "wallride": 4, "pipe": 5, "corkscrew": 3, "spiral": 4, "halfpipe": 3,
        "kicker": 6, "tilt": 3}
