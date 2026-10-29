"""Non-stop beats: ramp jumps, drop cascades, bounces, island hops, gauntlets, windmill leaps. Every beat starts where the
last one ended and is short (a kick is a ramp, a flight and a landing ramp), so a level is jump after jump.

All jumps are exact launch pads, fired straight along the route's heading, landing on a ramp that runs downhill under
the landing spot (the line of flight meets it softly). The kicker ramp is drawn over the pad (it never collides).
"""
import math
from geom import CF, deck_frame, axis_frame, look_frame, add, sub, mul, unit, cross, UP
from builder import G, CAR_UP, mix
import route as RT
import showcase as SC
from skins import Pt, cyl, ball
from worlds import ringz

TAU = math.pi * 2


def right_of(f):
    return mul(RT.left_of(f), -1)


# ===================================================================== art
def kicker_art(b, end, f, w, h=7.0, L=30.0):
    """A launch ramp drawn over the last L studs of road (non-colliding: the pad does the launching)."""
    sk = b.skin
    a = add(end, mul(f, -L))
    top = add(end, (0, h, 0))
    d = sub(top, a)
    fr = deck_frame(lerp3(a, top, 0.5), d)
    ln = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
    Pt(b, "Kicker", CF(add(fr.p, mul(fr.y, -1.0)), fr.x, fr.y, fr.z), (w - 4, 2, ln), sk.padc, "SmoothPlastic", b.scenery)
    for k in range(4):
        q = add(a, mul(d, (k + 0.6) / 4.6))
        Pt(b, "KickerStripe", CF(add(q, mul(fr.y, 0.06)), fr.x, fr.y, fr.z), (w - 8, 0.12, 2.4), sk.edge, "Neon", b.scenery)
    Pt(b, "KickerLip", CF(add(top, mul(fr.y, -0.5)), fr.x, fr.y, fr.z), (w - 2, 1.2, 2), sk.edge, "Neon", b.scenery)
    for s in (-1, 1):
        side = add(lerp3(a, top, 0.5), mul(fr.x, s * (w / 2 - 1)))
        Pt(b, "KickerSide", CF(add(side, (0, -h / 4, 0)), fr.x, fr.y, fr.z), (2, h / 2 + 2, ln), sk.body, sk.body_mat, b.scenery)


def lerp3(a, c, t):
    return (a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t, a[2] + (c[2] - a[2]) * t)


def target_mark(b, p, w):
    ringz(b, add(p, (0, 0.25, 0)), max(10.0, w * 0.3), b.skin.padc, "Neon", th=0.3, parent=b.scenery, name="Target")


def hazard_lip(b, p, f, w):
    """Black and yellow chevrons along an edge you drop off."""
    fr = deck_frame(p, f)
    n = max(2, int(w // 8))
    for k in range(n):
        q = add(p, add(mul(fr.x, (k - (n - 1) / 2) * 8), mul(f, -2)))
        Pt(b, "EdgeStripe", CF(add(q, (0, 0.08, 0)), fr.x, fr.y, fr.z), (4, 0.12, 4), (255, 210, 40) if k % 2 else (30, 30, 30),
           "SmoothPlastic", b.scenery)


# ===================================================================== beats
def run(r, label, L, w=None, dy=0.0, cp=False, **kw):
    r.straight(label, L, dy=dy, w1=w, lead=min(30.0, L / 4), cp=cp, **kw)


def bend(r, label, deg, R=90.0, w=None, dy=0.0, cp=False, **kw):
    r.turn(label, deg, R, dy=dy, w1=w, cp=cp, **kw)


# the car, as its controller drives it: take-off speeds from the slowest build to a quick one (faster cars ease off in
# the air with S, which the controller allows down to a quarter of their speed), and its own jump (Space)
V_MIN, V_MID, V_FAST = 110.0, 170.0, 230.0
JUMP_UP = 140.0


def t_down(vy, dy):
    """Time for a flight starting upward at vy to come down to dy (relative height)."""
    disc = vy * vy - 2 * G * dy
    return None if disc < 0 else (vy + math.sqrt(disc)) / G


def _arc_rings(b, src, f, H, V, rings, until_dy):
    T = t_down(V, until_dy) or 1.0
    for k in range(rings):
        t = T * (k + 1) / (rings + 1)
        p = (src[0] + f[0] * H * t, src[1] + CAR_UP + V * t - 0.5 * G * t * t, src[2] + f[2] * H * t)
        b.skin.hoop(b, p, unit((f[0] * H, V - G * t, f[2] * H)), 18)


def _deck(r, label, start, f, L, w, cp=False):
    """The landing deck: a flat road from `start` along f."""
    r.p, r.f, r.w = start, f, w
    r.straight(label, L, lead=10.0, cp=cp)


def gap(r, label, D, dy=0.0, rings=0, w=None, cp=False, mill=False, land_fn=None):
    """A gap the car clears on its own jump (Space) off a kicker ramp: no booster. The landing deck starts D past the
    lip and runs on far enough that a quick car lands on it too."""
    b = r.b
    f = r.f
    w = w or r.w
    s0 = len(b.samples)
    lip0 = r.p
    T = t_down(JUMP_UP, dy - 4.0)
    assert T and V_MIN * T >= D + 15, ("gap too long for the car's own jump", label, D, dy)
    # the kicker: a real ramp over the last 24 studs, 4 high at the lip
    kc = add(lip0, add(mul(f, -12), (0, 2.0, 0)))
    fr = deck_frame(kc, f)
    Pt(b, "Kicker", CF(kc, fr.x, fr.y, fr.z), (w - 6, 4, 24), b.skin.padc, "SmoothPlastic", b.roads, collide=True,
       cls="WedgePart")
    Pt(b, "KickerLip", CF(add(lip0, (0, 4.1, 0)), fr.x, fr.y, fr.z), (w - 6, 0.3, 1.6), b.skin.edge, "Neon", b.scenery)
    hazard_lip(b, add(lip0, mul(f, -26)), f, w)
    lip = add(lip0, (0, 4.0, 0))
    RT.trim_line(b, lip0, f)
    b.line(*lip)
    b.arc((lip[0], lip[1] + CAR_UP, lip[2]), (f[0] * V_MID, JUMP_UP, f[2] * V_MID), until_y=lip0[1] + dy + CAR_UP)
    land_t = t_down(JUMP_UP, dy - 4.0)
    tgt = add(lip0, add(mul(f, V_MID * land_t), (0, dy, 0)))
    b.jumps.append(("key", lip, tgt, V_MID, JUMP_UP))
    if rings:
        _arc_rings(b, lip, f, V_MID, JUMP_UP, rings, dy - 4.0)
    if mill:
        windmill(b, lip, tgt, b.jumps[-1])
    r._seg(label + "-air", s0)
    L = max(150.0, min(320.0, V_MID * T - D + 70))
    n0 = len(b.path)
    _deck(r, label, add(lip0, add(mul(f, D), (0, dy, 0))), f, L, w, cp)
    b.path[n0:] = [p for p in b.path[n0:] if RT.dot(sub(p[:3], tgt), f) > 4]
    target_mark(b, add(lip0, add(mul(f, D + 30), (0, dy, 0))), w)
    if land_fn:
        land_fn(b, add(lip0, add(mul(f, D + L * 0.4), (0, dy, 0))), w, f)
    return r


def booster(r, label, D, dy, rings=0, w=None, cp=False, mill=False, land_fn=None):
    """An up booster: a pad that pushes the car straight up and leaves it its own speed and heading (it steers the
    flight); the landing deck starts D ahead at dy and is long enough for a quick car."""
    b = r.b
    f = r.f
    w = w or r.w
    s0 = len(b.samples)
    src = add(r.p, mul(f, -16))
    # Every car must clear the deck's near edge on the way up (the quickest reaches it soonest) and still reach the
    # deck on the way down (the slowest falls shortest): V_FAST * t_up < D < V_MIN * t_down.
    apex = max(dy * 1.4, dy + 60.0, 50.0)
    while True:
        V = math.sqrt(2 * G * apex)
        disc = math.sqrt(max(V * V - 2 * G * dy, 0.0))
        t_up = (V - disc) / G if dy > 0 else 0.0
        t_dn = (V + disc) / G
        lo, hi = V_FAST * t_up + 20.0, V_MIN * t_dn - 30.0
        if lo <= hi:
            break
        apex *= 1.08
    D = max(lo, min(D, hi))
    T = t_dn
    RT.trim_line(b, src, f)
    b.line(*src)
    b.part("LaunchPad", look_frame((src[0], src[1] + 0.3, src[2]), f), (w - 4, 0.6, 30), (255, 196, 60), "Slate",
           parent=b.track, transp=1, collide=False, query=False,
           attrs={"CarLaunchPad": True, "LaunchExact": True, "LaunchVertical": float(V), "BoosterUp": True})
    b.skin.pad_art(b, src, f)
    # (no rings: a faint column of light over the pad shows it throws you up)
    cyl(b, "UpdraftGlow", add(src, (0, 14, 0)), 26, min(w - 8, 30), b.skin.padc, "Neon", b.scenery, transp=0.82)
    b.arc((src[0], src[1] + CAR_UP, src[2]), (f[0] * V_MID, V, f[2] * V_MID), until_y=src[1] + dy + CAR_UP)
    tgt = add(src, add(mul(f, V_MID * T), (0, dy, 0)))
    b.jumps.append(("up", src, tgt, V_MID, V))
    if rings:
        _arc_rings(b, src, f, V_MID, V, rings, dy)
    if mill:
        windmill(b, src, tgt, b.jumps[-1])
    r._seg(label + "-air", s0)
    L = max(170.0, min(380.0, V_MID * T - D + 90))
    n0 = len(b.path)
    _deck(r, label, add(src, add(mul(f, D), (0, dy, 0))), f, L, w, cp)
    b.path[n0:] = [p for p in b.path[n0:] if RT.dot(sub(p[:3], tgt), f) > 4]
    target_mark(b, add(src, add(mul(f, D + 40), (0, dy, 0))), w)
    if land_fn:
        land_fn(b, add(src, add(mul(f, D + L * 0.4), (0, dy, 0))), w, f)
    return r


def kick(r, label, D, dy, rings=0, apex=None, land=110.0, w=None, slope=0.21, cp=False, mill=False, art=True,
         land_fn=None):
    """A jump of about D forward and dy up: the car's own jump off a ramp where it can make it, else an up booster."""
    if mill:
        cp = False  # (no respawn under a windmill's blades)
    g = max(60.0, min(115.0, D - 150.0))
    T = t_down(JUMP_UP, dy - 4.0)
    if dy <= 15 and T and V_MIN * T >= g + 15:
        return gap(r, label, g, dy, rings=rings, w=w, cp=cp, mill=mill, land_fn=land_fn)
    return booster(r, label, max(70.0, D - 120.0), dy, rings=rings, w=w, cp=cp, mill=mill, land_fn=land_fn)


def windmill(b, src, tgt, jump, R=62.0, speed=0.32):
    """A spinning three-blade windmill standing beside the flight, its blades sweeping through it (time the jump)."""
    kind, s, t, H, V = jump
    f = RT.flat(sub(t, s))
    T = 0.0
    # time of the mid-flight point
    dist = math.hypot(t[0] - s[0], t[2] - s[2])
    T = dist / H * 0.5
    p = add(s, add(mul(f, H * T), (0, CAR_UP + V * T - 0.5 * G * T * T, 0)))
    hub = add(p, mul(right_of(f), R * 0.72))
    root = b.prop_root("Windmill")
    rig = b.rig(root, "Spin", axis_frame(hub, f), speed, 4, phase=0.0, name="MillSpin")
    sk = b.skin
    fr = axis_frame(hub, f)
    for k in range(3):
        a = TAU * k / 3
        d = add(mul(fr.y, math.cos(a)), mul(fr.z, math.sin(a)))
        side = cross(f, d)
        c = add(hub, mul(d, R * 0.42 + 6))
        Pt(b, "MillBlade", CF(c, f, d, side), (5, R * 0.84, 12), sk.danger, "Neon", rig, query=True,
           attrs={"ObbyHazard": "Knock"})
        Pt(b, "MillBladeTip", CF(add(hub, mul(d, R * 0.92 + 6)), f, d, side), (5.4, R * 0.16, 16), (255, 255, 255), "Neon", rig,
           query=True, attrs={"ObbyHazard": "Knock"})
        Pt(b, "MillSpar", CF(add(hub, mul(d, R * 0.42 + 6)), f, d, side), (6.4, R * 0.84, 2.4), sk.body, sk.body_mat, rig)
    cyl(b, "MillHub", hub, 10, 20, sk.body, sk.body_mat, rig, axis=f)
    ball(b, "MillCap", add(hub, mul(f, -6)), 14, sk.edge, "Neon", rig)
    cyl(b, "MillPost", add(hub, (0, -95, 0)), 180, 9, sk.body, sk.body_mat, b.scenery)
    cyl(b, "MillFoot", add(hub, (0, -186, 0)), 6, 30, sk.body, sk.body_mat, b.scenery)
    for k in range(6):
        cyl(b, "MillStripe", add(hub, (0, -30 - k * 22, 0)), 6, 9.6, (255, 210, 40) if k % 2 else (30, 30, 30), "SmoothPlastic",
            b.scenery)


def drops(r, label, n=3, step=45.0, L=150.0, w=None, cp=False):
    """A cascade: drive off each ledge and fall onto the next one, n times (each ledge long enough to land on flat out)."""
    b = r.b
    L = max(L, 210 * math.sqrt(2 * step / G) + 40)
    for i in range(n):
        lip = r.p
        f = r.f
        hazard_lip(b, lip, f, r.w)
        b.line(*lip)
        b.arc((lip[0], lip[1] + CAR_UP, lip[2]), (f[0] * 130, 0.0, f[2] * 130), until_y=lip[1] - step + CAR_UP)
        b.jumps.append(("drop", lip, add(lip, add(mul(f, 90), (0, -step, 0))), 130.0, 0.0))
        r.p = add(lip, add(mul(f, 2.0), (0, -step, 0)))
        if w:
            r.w = w
        n0 = len(b.path)
        r.straight("%s %d" % (label, i + 1), L, lead=10.0, cp=cp and i == 0)
        b.path[n0:] = [p for p in b.path[n0:] if RT.dot(sub(p[:3], lip), f) > 95]
    return r


def isles(r, label, n, D=170.0, dy=0.0, s=54.0, side=0.0, plat=None, land=None):
    """A row of stepping stones you drive straight across: level stones with hairline gaps, or falling stones that step
    down 10 at a time over short gaps (a car at speed sails each one and lands on the next)."""
    b = r.b
    f = r.f
    s = max(s, 76.0)
    down = dy < 0
    step = -10.0 if down else 0.0
    gp = 22.0 if down else 3.0
    side = min(side, 10.0)
    lft = RT.left_of(f)
    plat = plat or b.skin.plat
    s0 = len(b.samples)
    lip = r.p
    if down:
        hazard_lip(b, add(lip, mul(f, -2)), f, r.w)
    tops = []
    for k in range(n):
        off = side * (1 if k % 2 == 0 else -1) if side else 0.0
        tops.append(add(lip, add(mul(f, gp + s / 2 + k * (s + gp)), add(mul(lft, off), (0, step * (k + 1), 0)))))
    edge = lip
    for k, c in enumerate(tops):
        if down:
            b.arc((edge[0], edge[1] + CAR_UP, edge[2]), (f[0] * V_MID, 0.0, f[2] * V_MID), until_y=c[1] + CAR_UP)
            b.jumps.append(("drop", edge, c, V_MID, 0.0))
        plat(b, c, s, r.rng)
        from skins import floor as _floor
        _floor(b, c, s - 2, round_=True)  # the whole stone carries the car, whatever the skin's own top is
        b.line(*add(c, mul(f, -s * 0.3)))
        b.line(*add(c, mul(f, s * 0.3)))
        edge = add(c, mul(f, s / 2 - 2))
    r._seg(label, s0)
    start = add(edge, add(mul(f, gp + 2), (0, step, 0)))
    if down:
        b.arc((edge[0], edge[1] + CAR_UP, edge[2]), (f[0] * V_MID, 0.0, f[2] * V_MID), until_y=start[1] + CAR_UP)
        b.jumps.append(("drop", edge, add(start, mul(f, 30)), V_MID, 0.0))
    n0 = len(b.path)
    _deck(r, label + "-out", start, f, 120.0, r.w, cp=True)
    if down:
        b.path[n0:] = [p for p in b.path[n0:] if RT.dot(sub(p[:3], start), f) > 30]
    return r


def gauntlet(r, label, L, kinds, every=90.0, w=None, cp=False, **kw):
    """A short road packed with obstacles."""
    r.straight(label, L, w1=w, lead=12.0, cp=cp)
    at = []
    d = max(every * 0.7, 70.0)
    while d < L - 40:
        at.append(d)
        d += every
    for k, d in enumerate(at):
        r.along(kinds[k % len(kinds)], [d], i0=k, **kw)
    return r


def bomb(r, label, L, drop, w=None, cp=False, rails=False):
    """Bombing down a steep slope."""
    r.straight(label, L, dy=-abs(drop), w1=w, lead=20.0, cp=cp, rails=rails)
    return r


def climb(r, label, L, rise, w=None, cp=False, rails=False):
    r.straight(label, L, dy=abs(rise), w1=w, lead=20.0, cp=cp, rails=rails)
    return r


def aim(r, label, u, v, R=90.0, w=None, limit=160.0, cp=False):
    """Turn toward the point (u, v) of the level (as far as `limit` degrees)."""
    from builder import X0, ZC
    tx, tz = X0 + u, ZC + v
    want = math.atan2(-(tz - r.p[2]), tx - r.p[0])
    cur = math.atan2(-r.f[2], r.f[0])
    d = math.degrees((want - cur + math.pi) % TAU - math.pi)
    d = max(-limit, min(limit, d))
    if abs(d) > 3:
        r.turn(label, d, R, w1=w, cp=cp)
    return r
