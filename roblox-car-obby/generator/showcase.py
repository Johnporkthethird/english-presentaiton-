"""Ten hand-built showcase levels (L001-L010).

Each level has a skin (skins.py) that draws every object in it: hop targets, decks, pads, hoops and the moving
pieces (sweepers, presses, swings, doors, belts...). The set pieces here only decide where things go and how they
move; the skin decides what they are. Every drivable top is a real collidable part at the exact height.
"""
import math
import random
import rbxl
from geom import CF, deck_frame, axis_frame, look_frame, add, sub, mul, unit, length, cross, dot, lerp, rot_y, rot_axis, UP
from builder import LevelBuilder, X0, ZC, Y0, THICK, G, CAR_UP, mix
import parkour as V2
import parkour3 as K
from parkour import St, TAU, ease, ease5, bump
import landmarks
import levels3

# texture assets already in the place (by what they show)
TEX = {"grid": 100230810419170, "checker": 118286778245825, "stone": 10025395487}


def tex(b, p, key, face=1, tile=8.0, color=(255, 255, 255), transp=0.0):
    """A tiling Texture on one face of a part (1 = top)."""
    t = b.fac.blank("Texture")
    t.set("Name", b"Texture")
    t.set("TextureContent", ("uri", b"rbxassetid://%d" % TEX[key]))
    t.set("Face", face)
    t.set("StudsPerTileU", float(tile))
    t.set("StudsPerTileV", float(tile))
    t.set("Color3", tuple(c / 255.0 for c in color))
    t.set("Transparency", float(transp))
    t.set_parent(p)
    return t


def spin(b, centre, axis, speed, phase=0.0, name="Spin"):
    root = b.prop_root(name)
    return b.rig(root, "Spin", axis_frame(centre, axis), speed, 4, phase=phase)


# ===================================================================== pads, links, rests
def pad(b, src, tgt, apex=None, rings=0):
    """Exact launch pad at src (a surface top) landing on tgt, drawn by the skin."""
    while b.path and b.path[-1][3] == "r" and b.path[-1][0] > src[0] - 1:
        b.path.pop()
    dy = tgt[1] - src[1]
    if apex is None:
        apex = max(dy, 0) + 42
    H, V, T = b.launch(src, tgt, apex=apex, visual=False)
    f = unit((tgt[0] - src[0], 0, tgt[2] - src[2]))
    b.skin.pad_art(b, src, f)
    for k in range(rings):
        t = T * (k + 1) / (rings + 1)
        p = (src[0] + f[0] * H * t, src[1] + CAR_UP + V * t - 0.5 * G * t * t, src[2] + f[2] * H * t)
        b.skin.hoop(b, p, unit((f[0] * H, V - G * t, f[2] * H)), 18)
    return H, V, T


def link(b, st, rng, dy):
    src = (st.x - 16, st.y, st.z)
    lane = b.look["lane"]
    k = round((st.z - ZC) / lane)
    if rng.random() < 0.35:
        k += rng.choice([-1, 1])
    k = max(-2, min(2, k))
    tz = ZC + k * lane
    tgt = (src[0] + 200, st.y + dy, tz)
    pad(b, src, tgt)
    st.x, st.y, st.z = tgt[0] - 22, tgt[1], tz
    b.pending_landing = True


def finale(b, st, rng, x_end, y_end, z_end):
    src = (st.x - 16, st.y, st.z)
    n = max(1, int(round((x_end - src[0]) / 200)))
    step = (x_end - src[0]) / n
    prev = src
    for i in range(1, n + 1):
        t = i / n
        if i < n:
            tgt = (prev[0] + step, K.snap(st.y + (y_end - st.y) * K.ease(t), 15), st.z + (z_end - st.z) * K.ease(t))
        else:
            tgt = (x_end, y_end, z_end)
        pad(b, prev, tgt)
        if i < n:
            b.skin.finale_plat(b, tgt, K.W(b, 54), rng)
        prev = tgt


# ===================================================================== set pieces
def m_hops(b, st, d, rng, layout="straight", n=None, s=None, plat=None):
    K.rest(b, st)
    n = n or rng.randint(3, 4)
    s = s or K.W(b, 50)
    plat = plat or b.skin.plat
    src = (st.x - 16, st.y, st.z)
    tg = K.hop_targets(b, St(src[0], src[1], src[2], 0, b.zc), rng, n, d, layout)
    for t in tg:
        pad(b, src, t)
        plat(b, t, s, rng)
        src = t
    tgt = (src[0] + 200, src[1], src[2])
    pad(b, src, tgt)
    K.landing(b, st, *tgt)


def m_tower(b, st, d, rng):
    """Hop round a themed tower, climbing a level each hop."""
    K.rest(b, st)
    R = 95.0
    c = (st.x + R + 30, st.y, st.z)
    n = 5
    src = (st.x - 16, st.y, st.z)
    b.skin.tower(b, c, st.y - 60, st.y + 40 * n + 50)
    for i in range(n):
        a = math.pi + (i + 1) * (TAU / 6)
        t = (K.snap(c[0] + R * math.cos(a), 1), st.y + 40 * (i + 1), K.snap(c[2] + R * math.sin(a), 1))
        pad(b, src, t)
        b.skin.tower_plat(b, t, K.W(b, 48), rng)
        src = t
    tgt = (src[0] + 210, src[1] - 40, st.z)
    pad(b, src, tgt)
    K.landing(b, st, *tgt)


def m_long_jump(b, st, d, rng):
    K.rest(b, st, L=110)
    b.boost(st.x - 60, st.y, st.z)
    src = (st.x - 16, st.y, st.z)
    tgt = (src[0] + K.snap(rng.uniform(350, 400), 10), st.y + K.snap(rng.uniform(-60, 15), 15), st.z)
    pad(b, src, tgt, apex=max(tgt[1] - src[1], 0) + 85, rings=4)
    K.landing(b, st, *tgt, w=K.W(b, 66))


def m_drop(b, st, d, rng):
    K.rest(b, st)
    src = (st.x - 16, st.y, st.z)
    up = K.snap(rng.uniform(120, 150), 15)
    tgt = (src[0] + 180, st.y + up, st.z)
    pad(b, src, tgt)
    w = K.W(b, 46)
    K.run(b, tgt[0] - 40, tgt[0] + 80, tgt[1], st.z, w)
    lip = tgt[0] + 80
    b.line(lip - 6, tgt[1], st.z)
    drop = up + K.snap(rng.uniform(20, 60), 15)
    for k in range(3):
        t = 0.3 + 0.28 * k
        c = (lip + 120 * t, tgt[1] + CAR_UP - 0.5 * G * t * t, st.z)
        b.skin.hoop(b, c, unit((120, -G * t, 0)), 19 + 2 * k)
    ly = tgt[1] - drop
    b.arc((lip, tgt[1] + CAR_UP, st.z), (130, 0, 0), until_y=ly + CAR_UP + 6)
    L = 260.0
    K.run(b, lip + 20, lip + 20 + L, ly, st.z, K.W(b, 72))
    b.line(lip + 20 + L - 6, ly, st.z)
    st.x, st.y = lip + 20 + L, ly


def m_sweepers(b, st, d, rng, n=3):
    K.rest(b, st)
    s = max(K.W(b, 100), 84.0)
    for i in range(n):
        K.run(b, st.x, st.x + 26, st.y, st.z, K.W(b, 30))
        c = (st.x + 24 + s / 2, st.y, st.z)
        b.skin.island(b, c, s, rng)
        low = (i % 2 == 0) if rng.random() < 0.7 else (i % 2 == 1)
        rig = spin(b, add(c, (0, 3, 0)), UP, rng.choice([-1, 1]) * (rng.uniform(0.22, 0.3) + 0.12 * d), rng.random(),
                   "Sweeper")
        b.skin.sweeper(b, rig, c, s, low)
        b.line(c[0] - s / 2, st.y, st.z)
        b.line(c[0] + s / 2, st.y, st.z)
        st.x = c[0] + s / 2
    K.run(b, st.x, st.x + 26, st.y, st.z, K.W(b, 30))
    st.x += 26
    K.run(b, st.x, st.x + 100, st.y, st.z, K.W(b, 48))
    st.x += 100


def m_turntable(b, st, d, rng):
    K.rest(b, st)
    R = K.snap(rng.uniform(84, 96), 2)
    c = (st.x + R, st.y, st.z)
    rig = spin(b, c, UP, (rng.uniform(0.07, 0.1) + 0.03 * d) * rng.choice([-1, 1]), rng.random(), "Turntable")
    k = 12
    holes = set(rng.sample([1, 2, 3, 4, 7, 8, 9, 10], 3 + (1 if d > 0.5 else 0)))
    b.skin.turntable(b, rig, c, R, k, holes)
    b.skin.hub(b, c, 36)
    b.samples.append((c[0], st.y, st.z, 2 * R))
    for x in (c[0] - R, c[0], c[0] + R):
        b.line(x, st.y, st.z)
    st.x = c[0] + R
    K.run(b, st.x, st.x + 100, st.y, st.z, K.W(b, 48))
    st.x += 100


def m_spin_bridges(b, st, d, rng):
    K.rest(b, st)
    Lb = K.snap(rng.uniform(98, 110), 2)
    wb = K.W(b, 34)
    speed = rng.uniform(0.045, 0.06) + 0.02 * d
    x = st.x
    for i in range(3):
        c = (x + 8 + Lb / 2, st.y, st.z)
        rig = spin(b, c, UP, speed * (1 if i % 2 == 0 else -1), (-i * (Lb + 14) / 120.0 * speed) % 1, "SpinBridge")
        b.skin.spin_deck(b, rig, c, Lb, wb)
        b.skin.spin_hub(b, c)
        b.line(c[0], st.y, st.z)
        x += Lb + 14
    st.x = x + 6
    K.run(b, st.x, st.x + 100, st.y, st.z, K.W(b, 48))
    st.x += 100


def m_cross(b, st, d, rng):
    K.rest(b, st)
    R = K.snap(rng.uniform(80, 90), 2)
    c = (st.x + R + 6, st.y, st.z)
    rig = spin(b, c, UP, (rng.uniform(0.045, 0.06) + 0.015 * d) * rng.choice([-1, 1]), rng.random(), "Cross")
    aw = K.W(b, 32)
    for k in range(4):
        a = TAU * k / 4
        f = (math.cos(a), 0, math.sin(a))
        b.skin.cross_arm(b, rig, add(c, mul(f, R / 2 + 12)), f, R - 20, aw)
    b.skin.hub(b, c, 50)
    for x in (c[0] - R, c[0], c[0] + R):
        b.line(x, st.y, st.z)
    st.x = c[0] + R + 4
    K.run(b, st.x, st.x + 100, st.y, st.z, K.W(b, 48))
    st.x += 100


def m_log(b, st, d, rng):
    w = K.W(b, 44)
    K.rest(b, st, w=w)
    r = 16.0
    L = K.snap(rng.uniform(230, 280), 10)
    c = (st.x + L / 2, st.y - r, st.z)
    rig = spin(b, c, (1, 0, 0), rng.choice([-1, 1]) * (0.22 + 0.1 * d), rng.random(), "Log")
    b.skin.log(b, rig, c, L, r)
    b.samples.append((c[0], st.y, st.z, 2 * r))
    for k in range(5):
        b.line(st.x + L * k / 4, st.y, st.z)
    st.x += L
    K.run(b, st.x, st.x + 90, st.y, st.z, w)
    st.x += 90


def m_swings(b, st, d, rng):
    K.rest(b, st)
    n = rng.randint(3, 4)
    Lp = K.snap(rng.uniform(64, 72), 2)
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
        b.skin.swing(b, rig, c, Lp, pivot)
        b.skin.swing_anchor(b, pivot, Lp)
        b.samples.append((c[0], st.y, st.z, Lp))
        b.line(c[0], st.y, st.z)
        x += Lp + 12
    st.x = x
    K.run(b, st.x, st.x + 100, st.y, st.z, K.W(b, 48))
    st.x += 100


def m_pistons(b, st, d, rng):
    w = K.W(b, 40)
    K.rest(b, st, w=w)
    n = rng.randint(8, 10)
    bl = K.snap(rng.uniform(32, 38), 2)
    amp = rng.uniform(14, 22) + 6 * d
    period = rng.uniform(2.2, 2.8)
    for i in range(n):
        c = (st.x + bl / 2, st.y, st.z)
        root = b.prop_root("Piston")
        rig = b.rig(root, "Slide", axis_frame(c, (0, -1, 0)), amp, period, phase=(i * 0.1) % 1, name="Lift")
        b.skin.piston(b, rig, c, bl - 1.5, w, i, n)
        b.samples.append((c[0], st.y, st.z, w))
        b.line(c[0], st.y, st.z)
        st.x += bl
    K.run(b, st.x, st.x + 90, st.y, st.z, w)
    st.x += 90


def m_crushers(b, st, d, rng):
    w = K.W(b, 42)
    K.rest(b, st, w=w)
    n = rng.randint(3, 5)
    sp = K.snap(rng.uniform(72, 88), 2)
    L = n * sp + 70
    x0 = st.x
    K.run(b, x0, x0 + L, st.y, st.z, w)
    H = 40.0
    period = rng.uniform(1.9, 2.4) - 0.3 * d
    dph = rng.choice([0.16, 0.2, 0.25])
    for i in range(n):
        x = x0 + 55 + i * sp
        rc = (x, st.y + H + 9, st.z)
        b.skin.press_frame(b, x, st.y, st.z, w, H)
        root = b.prop_root("Crusher")
        rig = b.rig(root, "Slide", axis_frame(rc, (0, -1, 0)), H + 1, period, phase=(i * dph) % 1,
                    keys="0:0 0.42:0 0.5:1 0.68:1 0.96:0", name="Press")
        b.skin.press(b, rig, rc, 28.0, w)
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


def m_doors(b, st, d, rng):
    w = K.W(b, 46)
    K.rest(b, st, w=w)
    n = rng.randint(3, 4)
    sp = K.snap(rng.uniform(92, 110), 2)
    L = n * sp + 60
    x0 = st.x
    K.run(b, x0, x0 + L, st.y, st.z, w)
    hole = max(22.0, 28 - 5 * d)
    for i in range(n):
        x = x0 + 60 + i * sp
        amp = w - hole
        rz = st.z - w / 2 + hole / 2
        root = b.prop_root("Door")
        rig = b.rig(root, "Slide", axis_frame((x, st.y + 9, rz), (0, 0, 1)), amp, rng.uniform(2.6, 3.2) - 0.4 * d,
                    phase=rng.random(), name="DoorSlide")
        for s in (-1, 1):
            b.skin.door_panel(b, rig, (x, st.y, rz + s * (hole / 2 + w / 2)), w)
        b.skin.door_frame(b, x, st.y, st.z, w)
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


def m_gates(b, st, d, rng):
    w = K.W(b, 42)
    K.rest(b, st, w=w)
    n = rng.randint(5, 7)
    sp = K.snap(rng.uniform(54, 66), 2)
    L = n * sp + 60
    x0 = st.x
    K.run(b, x0, x0 + L, st.y, st.z, w)
    period = rng.uniform(1.8, 2.3)
    on = period * (0.45 + 0.1 * d)
    v = rng.uniform(100, 140)
    for i in range(n):
        x = x0 + 40 + i * sp
        ph = (-(x - x0) / v / period) % 1
        full = rng.random() < 0.5 + 0.3 * d
        beams = [(3.2, 3.0)] if not full else [(4 + 7 * k, 2.2) for k in range(5)]
        attrs = {"ObbyHazard": "Zap", "ZapFX": True, "ZapPeriod": period, "ZapOn": on, "ZapPhase": ph}
        b.skin.gate(b, x, st.y, st.z, w, beams, attrs, i)
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


def m_crumble(b, st, d, rng):
    K.rest(b, st)
    s = max(26.0, K.W(b, 30))
    n = rng.randint(13, 16)
    delay = 0.4 - 0.15 * d
    for i in range(n):
        m = b.model("CrumbleTile", b.hazards, {"ObbyCrumble": float(delay)})
        c = (st.x + i * (s - 2) + s / 2, st.y, st.z)
        b.skin.crumble_tile(b, m, c, s, i)
        b.samples.append((c[0], st.y, st.z, s))
        b.line(c[0], st.y, st.z)
    st.x += n * (s - 2)
    K.run(b, st.x, st.x + 100, st.y, st.z, K.W(b, 48))
    st.x += 100


def m_belts(b, st, d, rng):
    w = K.W(b, 42)
    K.rest(b, st, w=w)
    for i in range(rng.randint(4, 6)):
        L = K.snap(rng.uniform(72, 90), 2)
        side = 1 if i % 2 == 0 else -1
        sp = rng.uniform(28, 40) + 16 * d
        b.skin.belt(b, (st.x + L / 2, st.y, st.z), L - 1, w, side, sp)
        b.samples.append((st.x + L / 2, st.y, st.z, w))
        b.line(st.x + L / 2, st.y, st.z)
        st.x += L
    K.run(b, st.x, st.x + 90, st.y, st.z, w)
    st.x += 90


def m_bumpers(b, st, d, rng):
    K.rest(b, st)
    w = max(K.W(b, 86), 72.0)
    L = K.snap(rng.uniform(330, 380), 10)
    x0 = st.x
    K.run(b, x0, x0 + L, st.y, st.z, w)
    rows = int((L - 80) // 52)
    for r in range(rows):
        x = x0 + 60 + r * 52
        cols = 3 if r % 2 == 0 else 2
        for c in range(cols):
            zz = st.z + (c - (cols - 1) / 2) * (w / 3.2)
            b.skin.bumper(b, (x, st.y, zz), rng)
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L


def m_rink(b, st, d, rng):
    K.rest(b, st)
    w = max(K.W(b, 100), 82.0)
    L = K.snap(rng.uniform(320, 380), 10)
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
            b.skin.rink_tile(b, c, cell)
            b.samples.append((c[0], st.y, c[2], cell))
        jj = min(free, key=lambda j: abs(st.z - w / 2 + cell * (j + 0.5) - st.z))
        path.append((x0 + cell * (i + 0.5), st.z - w / 2 + cell * (jj + 0.5)))
    V2.P(b, "IceSlip", CF((x0 + L / 2, st.y + 2.5, st.z)), (L, 7, w), (255, 255, 255), parent=b.hazards, transp=1,
         query=True, attrs={"ObbyHazard": "Slip"})
    b.skin.rink_rim(b, x0, x0 + nx * cell, st.y, st.z, w)
    for x, z in path:
        b.line(x, st.y, z)
    st.x = x0 + nx * cell
    K.run(b, st.x, st.x + 90, st.y, st.z, K.W(b, 48))
    st.x += 90


def m_loop(b, st, d, rng):
    w = 34.0
    K.rest(b, st, w=K.W(b, 48))
    K.run(b, st.x, st.x + 100, st.y, st.z, w)
    b.boost(st.x + 40, st.y, st.z)
    b.line(st.x + 94, st.y, st.z)
    st.x += 100
    R = 54.0
    dz = w + 10
    cx, cy, z0 = st.x, st.y + R, st.z
    n = 40
    pts = []
    for i in range(n + 1):
        ph = TAU * i / n
        p = (cx + R * math.sin(ph), cy - R * math.cos(ph), z0 + dz * ease5(i / n))
        pts.append((p, (-math.sin(ph), math.cos(ph), 0.0)))
    m = b.model("Loop", b.roads, {"WallRide": True})
    b.skin.ribbon(b, pts, w, m)
    for p, nrm in pts[::3]:
        b.path.append((p[0] + nrm[0] * CAR_UP, p[1] + nrm[1] * CAR_UP, p[2], "s"))
    b.skin.loop_deco(b, (cx, cy, z0 + dz / 2), R, w)
    st.z = z0 + dz
    K.run(b, st.x, st.x + 120, st.y, st.z, w)
    b.line(st.x + 114, st.y, st.z)
    st.x += 120


def m_wallride(b, st, d, rng):
    w = 36.0
    K.rest(b, st, w=K.W(b, 48))
    K.run(b, st.x, st.x + 70, st.y, st.z, w)
    b.boost(st.x + 30, st.y, st.z)
    b.line(st.x + 64, st.y, st.z)
    st.x += 70
    first = rng.choice([-1, 1])
    for k in range(2):
        side = first * (1 if k == 0 else -1)
        L = rng.uniform(240, 290)
        x0, y0, z0 = st.x, st.y, st.z
        tilt = math.radians(rng.uniform(72, 80))
        n = 30
        pts = []
        for i in range(n + 1):
            t = i / n
            a = side * tilt * bump(t)
            pts.append(((x0 + L * t, y0 + 14 * bump(t), z0 - side * 26 * bump(t)), (0.0, math.cos(a), math.sin(a))))
        m = b.model("WallRide", b.roads, {"WallRide": True})
        b.skin.ribbon(b, pts, w, m)
        for p, nrm in pts[::3]:
            b.path.append((p[0] + nrm[0] * CAR_UP, p[1] + nrm[1] * CAR_UP, p[2] + nrm[2] * CAR_UP, "s"))
        st.x = x0 + L
        K.run(b, st.x, st.x + 44, st.y, st.z, w)
        b.line(st.x + 38, st.y, st.z)
        st.x += 44
    K.run(b, st.x, st.x + 80, st.y, st.z, K.W(b, 48))
    b.line(st.x + 74, st.y, st.z)
    st.x += 80


def m_pipe(b, st, d, rng):
    w = 30.0
    K.rest(b, st, w=K.W(b, 48))
    K.run(b, st.x, st.x + 60, st.y, st.z, w)
    b.boost(st.x + 24, st.y, st.z)
    st.x += 60
    R = 26.0
    L = K.snap(rng.uniform(360, 420), 10)
    x0, y0, z0 = st.x, st.y, st.z
    axis_y = y0 + R
    k = 16
    m = b.model("Pipe", b.roads, {"WallRide": True})
    for i in range(k):
        a = TAU * i / k
        d_out = (0.0, -math.cos(a), math.sin(a))
        nrm = (0.0, math.cos(a), -math.sin(a))
        top = (x0 + L / 2, axis_y + d_out[1] * R, z0 + d_out[2] * R)
        x = cross(nrm, (1, 0, 0))
        cf = CF(sub(top, mul(nrm, THICK / 2)), x, nrm, (1.0, 0.0, 0.0))
        b.skin.pipe_wall(b, m, cf, (TAU * R / k + 1.2, THICK, L), i, k)
    b.samples.append((x0 + L / 2, y0, z0, w))
    b.skin.pipe_rings(b, x0, L, axis_y, z0, R)
    nb = rng.randint(3, 4)
    for j in range(nb):
        xb = x0 + 70 + j * (L - 130) / max(nb - 1, 1)
        side = 1 if j % 2 == 0 else -1
        a = side * 0.5
        c = (xb, axis_y - math.cos(a) * (R - 5), z0 + math.sin(a) * (R - 5))
        b.skin.pipe_blocker(b, c, a)
    for i in range(9):
        b.line(x0 + L * i / 8, y0, z0)
    st.x = x0 + L
    K.run(b, st.x, st.x + 80, st.y, st.z, K.W(b, 48))
    b.line(st.x + 74, st.y, st.z)
    st.x += 80


MODULES = {"hops": m_hops, "tower": m_tower, "long_jump": m_long_jump, "drop": m_drop, "sweepers": m_sweepers,
           "turntable": m_turntable, "spin_bridges": m_spin_bridges, "cross": m_cross, "log": m_log, "swings": m_swings,
           "pistons": m_pistons, "crushers": m_crushers, "doors": m_doors, "gates": m_gates, "crumble": m_crumble,
           "belts": m_belts, "bumpers": m_bumpers, "rink": m_rink, "loop": m_loop, "wallride": m_wallride, "pipe": m_pipe}


# ===================================================================== the level
def build_level(fac, unit_, level_folder, level_id, length, templates):
    import skins
    skin = skins.SKINS[level_id]()
    pal = skin.pal()
    rng = random.Random(77000 + level_id * 1301)
    b = LevelBuilder(fac, level_folder, pal, rng, length, templates)

    class World:
        """What K.run / K.rest see: the skin's deck plus its supports underneath."""
        def deck(self, tb, x0, x1, y, z, w, parent=None):
            skin.deck(tb, x0, x1, y, z, w)
            skin.supports(tb, x0, x1, y, z, w)

        def plat(self, tb, top, s, rng_, parent=None):
            skin.plat(tb, top, s, rng_)

    def setup(tb):
        tb.world = World()
        tb.skin = skin
        tb.zc = ZC
        tb.look = {"shape": "square", "scale": skin.scale, "layout": "straight", "lane": 70.0 * skin.scale}
    setup(b)
    b.pieces = []
    X1 = X0 + length
    d_base = 0.3 + 0.04 * (level_id - 1)
    K.run(b, X0, X0 + 110, Y0, ZC, 144)
    b.checkpoint(X0 + 30, Y0, ZC, 144)
    b.line(X0, Y0, ZC)
    st = St(X0 + 110, Y0, ZC, 60, ZC)
    sandbox = rbxl.Inst("Folder")

    def d_now(s):
        return min(1.0, d_base + 0.2 * (s.x - X0) / length)

    def call(tb, ts, entry):
        key, label, kw = entry
        n0 = len(tb.path)
        MODULES[key](tb, ts, d_now(ts), rng, **kw)
        pts = tb.path[n0:]
        if pts:
            lo = [min(p[i] for p in pts) for i in range(3)]
            hi = [max(p[i] for p in pts) for i in range(3)]
            tb.pieces.append((label, lo, hi))

    def trial(entry, s):
        state = rng.getstate()
        tb = LevelBuilder(fac, sandbox, pal, rng, length, templates)
        setup(tb)
        tb.pieces = []
        tb.pending_landing = getattr(b, "pending_landing", False)
        ts = St(s.x, s.y, s.z, s.w, ZC)
        skin.dry = True
        try:
            call(tb, ts, entry)
        finally:
            skin.dry = False
        rng.setstate(state)
        sandbox.children.clear()
        return ts

    def reserve(s):
        return 110 + 200 + max(200 * (abs(s.y - Y0) / 70.0), 200 * abs(s.z - ZC) / 120.0)

    used = []
    for entry in list(skin.recipe) + list(skin.extra):
        t = trial(entry, st)
        if not (t.x + 40 + reserve(t) <= X1 and b.ylo - 20 <= t.y <= b.yhi + 20):
            continue
        call(b, st, entry)
        used.append(entry[1])
        dy = rng.choice([-1, 1]) * K.snap(rng.uniform(30, 60), 15)
        if st.y + dy > b.yhi or st.y + dy < b.ylo:
            dy = -dy
        if (st.x - X0) / length > 0.55:
            dy = K.snap(max(-60, min(60, (Y0 - st.y) * 0.4)), 15)
        link(b, st, rng, dy)
    if X1 - 110 - st.x < 60:
        raise RuntimeError("L%03d overran by %.0f" % (level_id, st.x - (X1 - 110)))
    if getattr(b, "pending_landing", False):
        K.run(b, st.x, st.x + 80, st.y, st.z, K.W(b, 52))
        b.line(st.x + 22, st.y, st.z)
        st.x += 80
        b.pending_landing = False
    finale(b, st, rng, X1 - 110 + 30, Y0, ZC)
    K.run(b, X1 - 110, X1, Y0, ZC, 160)
    skin.finish(b, X1 - 110, X1, Y0, ZC, 160)
    b.line(X1, Y0, ZC)
    landmarks.title_gate(b, level_id, skin.title)
    skin.environment(b)
    b.kill_sheets()
    a = rbxl.attrs(level_folder)
    for k in [k for k in a if k.startswith("Lt_")]:
        del a[k]
    a.update(skin.light())
    a["ObbyLevelTitle"] = skin.title
    a["ObbyLook"] = "sc%03d" % level_id
    rbxl.set_attrs(level_folder, a)
    ua = rbxl.attrs(unit_)
    ua["Title"] = skin.title
    rbxl.set_attrs(unit_, ua)
    return b, used, skin.title, skin.key
