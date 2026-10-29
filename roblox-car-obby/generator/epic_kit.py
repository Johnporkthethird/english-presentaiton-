"""Set pieces for the epic levels.

ob_*: one obstacle on a road, built at c (road top) heading +X across a road of width w; Route.along turns it onto
       any road (curves, slopes and spirals included).
a_*:   big +X set pieces (arenas, fields) for Route.local; they start with a rest deck and checkpoint.
"""
import math
from geom import CF, axis_frame, deck_frame, add, sub, mul, unit, UP
from builder import THICK
import parkour3 as K
from parkour import TAU
import showcase as SC
from skins import Pt, box, cyl, ball, samples


# ===================================================================== obstacles along a road
def ob_sweeper(b, c, w, i, rng=None, low=None, speed=None):
    """A spinning bar across the road (low bars you jump in time with, high walls you slip past)."""
    rng = rng or b.rng
    low = (i % 2 == 0) if low is None else low
    sp = speed or rng.choice([-1, 1]) * rng.uniform(0.26, 0.34)
    rig = SC.spin(b, add(c, (0, 3, 0)), UP, sp, rng.random(), "Sweeper")
    b.skin.sweeper(b, rig, c, w + 2, low)


def ob_press(b, c, w, i, rng=None, H=40.0):
    rng = rng or b.rng
    x, y, z = c
    rc = (x, y + H + 9, z)
    b.skin.press_frame(b, x, y, z, w, H)
    root = b.prop_root("Crusher")
    rig = b.rig(root, "Slide", axis_frame(rc, (0, -1, 0)), H + 1, rng.uniform(2.0, 2.5), phase=(i * 0.23) % 1,
                keys="0:0 0.42:0 0.5:1 0.68:1 0.96:0", name="Press")
    b.skin.press(b, rig, rc, 28.0, w)


def ob_gate(b, c, w, i, rng=None, period=2.0, full=None):
    rng = rng or b.rng
    full = (i % 2 == 1) if full is None else full
    beams = [(3.2, 3.0)] if not full else [(4 + 7 * k, 2.2) for k in range(5)]
    attrs = {"ObbyHazard": "Zap", "ZapFX": True, "ZapPeriod": period, "ZapOn": period * 0.5, "ZapPhase": (i * 0.27) % 1}
    b.skin.gate(b, c[0], c[1], c[2], w, beams, attrs, i)


def ob_door(b, c, w, i, rng=None, hole=26.0):
    rng = rng or b.rng
    x, y, z = c
    amp = w - hole
    rz = z - w / 2 + hole / 2
    root = b.prop_root("Door")
    rig = b.rig(root, "Slide", axis_frame((x, y + 9, rz), (0, 0, 1)), amp, rng.uniform(2.6, 3.2), phase=rng.random(),
                name="DoorSlide")
    for s in (-1, 1):
        b.skin.door_panel(b, rig, (x, y, rz + s * (hole / 2 + w / 2)), w)
    b.skin.door_frame(b, x, y, z, w)


def ob_swing(b, c, w, i, rng=None, H=70.0):
    rng = rng or b.rng
    pivot = (c[0], c[1] + H, c[2])
    root = b.prop_root("Pendulum")
    rig = b.rig(root, "Hinge", axis_frame(pivot, (1, 0, 0)), rng.uniform(30, 36), rng.uniform(2.8, 3.3),
                phase=(i * 0.21) % 1, keys="0:0 0.25:1 0.5:0 0.75:-1", name="Swing")
    b.skin.swing(b, rig, c, min(w, 70.0), pivot)
    b.skin.swing_anchor(b, pivot, min(w, 70.0))


def ob_bumpers(b, c, w, i, rng=None):
    rng = rng or b.rng
    n = 2 if i % 2 else 3
    for k in range(n):
        z = c[2] + (k - (n - 1) / 2) * (w / (n + 0.6))
        b.skin.bumper(b, (c[0], c[1], z), rng)


# ===================================================================== arenas
def _deck(b, x0, x1, y, z, w):
    K.run(b, x0, x1, y, z, w)


def a_sweep_field(b, st, d, rng, W=230.0, n=2, arms=2, speed=0.12):
    """Huge discs, each swept by a giant slow rotor with arms low and high."""
    K.rest(b, st, w=min(W * 0.45, 90.0))
    for i in range(n):
        _deck(b, st.x, st.x + 30, st.y, st.z, 60)
        c = (st.x + 26 + W / 2, st.y, st.z)
        b.skin.island(b, c, W, rng)
        rig = SC.spin(b, add(c, (0, 3, 0)), UP, (1 if i % 2 == 0 else -1) * (speed + 0.03 * d), rng.random(), "Rotor")
        for k in range(arms):
            a = TAU * k / arms
            f = (math.cos(a), 0.0, math.sin(a))
            arm_c = add(c, mul(f, W / 4 + 6))
            low = (k + i) % 2 == 0
            fr = CF(arm_c, (f[0], 0, f[2]), (0, 1, 0), (-f[2], 0, f[0]))
            if low:
                Pt(b, "RotorBar", fr.offset((0, 3.4, 0)), (W / 2 - 18, 3.2, 3.0), b.skin.danger, "Neon", rig,
                   query=True, attrs={"ObbyHazard": "Burn"})
            else:
                Pt(b, "RotorWall", fr.offset((0, 8, 0)), (W / 2 - 18, 16, 4), b.skin.danger, "Neon", rig, query=True,
                   attrs={"ObbyHazard": "Knock"})
        b.skin.hub(b, c, 30)
        b.line(c[0] - W / 2, st.y, st.z)
        b.line(c[0] - W / 4, st.y, st.z + W / 4)
        b.line(c[0], st.y, st.z + W / 3)
        b.line(c[0] + W / 4, st.y, st.z + W / 4)
        b.line(c[0] + W / 2, st.y, st.z)
        st.x = c[0] + W / 2
    _deck(b, st.x, st.x + 30, st.y, st.z, 60)
    st.x += 30
    _deck(b, st.x, st.x + 90, st.y, st.z, 64)
    b.line(st.x + 84, st.y, st.z)
    st.x += 90


def a_frogger(b, st, d, rng, W=200.0, lanes=5, block=None):
    """A very wide road crossed by big blocks sliding side to side, each lane on its own beat."""
    K.rest(b, st, w=90)
    lane = 64.0
    L = lanes * lane + 60
    x0 = st.x
    _deck(b, x0, x0 + L, st.y, st.z, W)
    for i in range(lanes):
        x = x0 + 40 + lane * (i + 0.5)
        bl = 46.0
        amp = W - bl - 4
        z0 = st.z - W / 2 + bl / 2 + 2
        root = b.prop_root("Slider")
        rig = b.rig(root, "Slide", axis_frame((x, st.y + 9, z0), (0, 0, 1)), amp, rng.uniform(2.6, 3.8) - 0.4 * d,
                    phase=rng.random(), name="Slide")
        (block or _slider_block)(b, rig, (x, st.y, z0), bl, i)
        b.line(x, st.y, st.z)
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L
    st.w = W


def _slider_block(b, rig, c, s, i):
    sk = b.skin
    Pt(b, "Slider", CF(add(c, (0, 9, 0))), (40, 18, s), sk.body, sk.body_mat, rig, query=True,
       attrs={"ObbyHazard": "Knock"})
    Pt(b, "SliderTrim", CF(add(c, (0, 18.2, 0))), (41, 0.6, s + 1), sk.edge, "Neon", rig)


def a_piston_sea(b, st, d, rng, W=160.0, L=360.0, cell=40.0, amp=26.0):
    """A field of pistons rising and falling in a rolling wave (the road itself moves)."""
    K.rest(b, st, w=min(W, 90.0))
    nx, nz = int(L // cell), int(W // cell)
    if nz % 2 == 0:
        nz += 1  # an odd count, so a column of pistons runs down the middle
    W = nz * cell
    x0 = st.x
    period = rng.uniform(2.6, 3.2)
    for i in range(nx):
        for j in range(nz):
            c = (x0 + cell * (i + 0.5), st.y, st.z - W / 2 + cell * (j + 0.5))
            root = b.prop_root("Piston")
            rig = b.rig(root, "Slide", axis_frame(c, (0, -1, 0)), amp, period, phase=((i * 0.12 + j * 0.07) % 1),
                        name="Lift")
            b.skin.piston(b, rig, c, cell - 1.0, cell - 1.0, i * nz + j, nx * nz)
            b.samples.append((c[0], st.y, c[2], cell))
        b.line(x0 + cell * (i + 0.5), st.y, st.z)
    st.x = x0 + nx * cell
    _deck(b, st.x, st.x + 90, st.y, st.z, 64)
    b.line(st.x + 84, st.y, st.z)
    st.x += 90


def a_crumble_field(b, st, d, rng, W=150.0, L=330.0, cell=30.0):
    """A wide floor of crumbling tiles with holes already in it."""
    K.rest(b, st, w=min(W, 90.0))
    nx, nz = int(L // cell), int(W // cell)
    x0 = st.x
    delay = 0.45 - 0.15 * d
    holes = set()
    for i in range(1, nx - 1):
        for j in range(nz):
            if rng.random() < 0.18:
                holes.add((i, j))
    mid = nz // 2
    for i in range(nx):
        holes.discard((i, mid))
        for j in range(nz):
            if (i, j) in holes:
                continue
            m = b.model("CrumbleTile", b.hazards, {"ObbyCrumble": float(delay)})
            c = (x0 + cell * (i + 0.5), st.y, st.z - W / 2 + cell * (j + 0.5))
            b.skin.crumble_tile(b, m, c, cell - 0.3, i + j)
            b.samples.append((c[0], st.y, c[2], cell))
        b.line(x0 + cell * (i + 0.5), st.y, st.z - W / 2 + cell * (mid + 0.5))
    st.x = x0 + nx * cell
    st.z = st.z - W / 2 + cell * (mid + 0.5)
    _deck(b, st.x, st.x + 90, st.y, st.z, 64)
    b.line(st.x + 84, st.y, st.z)
    st.x += 90


def a_bumper_field(b, st, d, rng, W=170.0, L=420.0):
    K.rest(b, st, w=90)
    x0 = st.x
    _deck(b, x0, x0 + L, st.y, st.z, W)
    rows = int((L - 80) // 56)
    for r in range(rows):
        x = x0 + 60 + r * 56
        cols = 4 if r % 2 == 0 else 3
        for c in range(cols):
            zz = st.z + (c - (cols - 1) / 2) * (W / (cols + 0.4))
            b.skin.bumper(b, (x, st.y, zz), rng)
    b.line(x0 + L - 6, st.y, st.z)
    st.x = x0 + L
    st.w = W


def a_turntables(b, st, d, rng, n=3, R=96.0):
    """Big spinning discs with holes, end to end."""
    K.rest(b, st)
    for i in range(n):
        c = (st.x + R, st.y, st.z)
        rig = SC.spin(b, c, UP, (rng.uniform(0.07, 0.1) + 0.03 * d) * (1 if i % 2 == 0 else -1), rng.random(), "Turntable")
        holes = set(rng.sample([1, 2, 3, 4, 7, 8, 9, 10], 3))
        b.skin.turntable(b, rig, c, R, 12, holes)
        b.skin.hub(b, c, 36)
        b.samples.append((c[0], st.y, st.z, 2 * R))
        for x in (c[0] - R, c[0], c[0] + R):
            b.line(x, st.y, st.z)
        st.x = c[0] + R
        if i < n - 1:
            _deck(b, st.x, st.x + 24, st.y, st.z, 40)
            st.x += 24
    _deck(b, st.x, st.x + 90, st.y, st.z, 60)
    b.line(st.x + 84, st.y, st.z)
    st.x += 90


def a_belts_wide(b, st, d, rng, W=120.0, n=5):
    """Wide conveyor lanes pushing alternately left and right, toward a drop at either side."""
    K.rest(b, st, w=90)
    for i in range(n):
        L = 70.0
        side = 1 if i % 2 == 0 else -1
        b.skin.belt(b, (st.x + L / 2, st.y, st.z), L - 1, W, side, rng.uniform(34, 46) + 14 * d)
        b.samples.append((st.x + L / 2, st.y, st.z, W))
        b.line(st.x + L / 2, st.y, st.z)
        st.x += L
    _deck(b, st.x, st.x + 90, st.y, st.z, 64)
    b.line(st.x + 84, st.y, st.z)
    st.x += 90
