"""Non-stop beats: ramp jumps, drop cascades, bounces, island hops, gauntlets, windmill leaps. Every beat starts where the
last one ended and is short (a kick is a ramp, a flight and a landing ramp), so a level is jump after jump.

All jumps are exact launch pads, fired straight along the route's heading, landing on a ramp that runs downhill under
the landing spot (the line of flight meets it softly). The kicker ramp is drawn over the pad (it never collides).
"""
import math
from geom import CF, deck_frame, axis_frame, add, sub, mul, unit, cross, UP
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


def kick(r, label, D, dy, rings=0, apex=None, land=110.0, w=None, slope=0.21, cp=False, mill=False, art=True,
         land_fn=None):
    """A ramp jump: pad at the end of the road, D forward and dy up, onto a downhill landing ramp."""
    b = r.b
    f = r.f
    s0 = len(b.samples)
    src = add(r.p, mul(f, -14))
    RT.trim_line(b, src, f)
    b.line(*src)
    tgt = add(src, add(mul(f, D), (0, dy, 0)))
    if art:
        kicker_art(b, r.p, f, r.w)
    if apex is None:
        apex = max(dy, 0.0) + 36 + D * 0.07
    RT._pad_any(b, src, tgt, apex, rings)
    if mill:
        windmill(b, src, tgt, b.jumps[-1])
    r._seg(label + "-air", s0)
    # the landing ramp: downhill through the target, easing out to flat
    a_, d1, d2 = 36.0, 40.0, 34.0
    s = slope

    def hh(d):
        if d <= d1:
            return -s * d
        if d <= d1 + d2:
            t = d - d1
            return -s * d1 - (s * t - s * t * t / (2 * d2))
        return -s * d1 - s * d2 / 2

    pts = []
    d = -a_
    while d <= land + 0.01:
        pts.append(add(tgt, add(mul(f, d), (0, hh(d), 0))))
        d += 6.0
    wl = w or r.w
    n0 = len(b.path)
    r._lay(label, pts, [wl] * len(pts), cp=cp)
    b.path[n0:] = [p for p in b.path[n0:] if RT.dot(sub(p[:3], tgt), f) > 4]
    target_mark(b, tgt, wl)
    if land_fn:
        land_fn(b, tgt, wl)
    return r


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


def isles(r, label, n, D=170.0, dy=0.0, s=54.0, side=0.0, plat=None, land=(190.0, 0.0, None, 130.0)):
    """Quick hops across islands (side: sideways offset alternating left and right)."""
    lft = RT.left_of(r.f)
    tg = []
    for k in range(1, n + 1):
        off = side * (1 if k % 2 else -1) if side else 0.0
        tg.append(add(r.p, add(mul(r.f, D * k - 14), add(mul(lft, off), (0, dy * k, 0)))))
    D2, dy2, w2, L2 = land
    r.hops(label, tg, plat=plat, s=s, land=(D2, dy2, w2 or r.w, L2))
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
