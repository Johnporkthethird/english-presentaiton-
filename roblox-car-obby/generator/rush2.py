"""Fast beats (version 3): boost strip runs, curved ramps and mega jumps, bounce mushroom chains, conveyor belts, grease,
moving decks (the game's clock rotor engine carries the car), sinking tiles, tractor beams, timed laser gates.
No hoops, no loops.

Speeds come from the game's own boost rules (TorretaControlsClient): a boost strip sets a floor under the car's
speed, and a run of strips stacks to the cap of 330 studs/s, so after a strip run EVERY car leaves the lip at about
330 whatever its build, and a jump can be sized for it. Boost decks (a road whose parts carry BoostSpeed, no
stacking) give an exact lower speed the same way. In the air the car keeps its speed (it can brake or steer, never
speed up), and leaving a ramp it flies along the ramp's last slope.
"""
import math
from geom import CF, deck_frame, axis_frame, look_frame, add, sub, mul, unit, cross, dot, UP
from builder import G, CAR_UP, X0, Y0, ZC
import route as RT
import journey as J
import rbxl
from skins import Pt, box, cyl, ball

TAU = math.pi * 2
V_TOP = 330.0          # a strip run's speed (the stack cap): what every big ramp is sized for
V_SLACK = 0.9          # ...and it must also land at 90% of it (a car that only just reached the strips)
JUMP_V = 145.0         # the strongest car's own jump (Space), plus its hold
JUMP_HOLD = 15.0


def right_of(f):
    return mul(RT.left_of(f), -1)


def lerp3(a, c, t):
    return (a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t, a[2] + (c[2] - a[2]) * t)


# ===================================================================== boosts
def strip_at(b, p, f, side=0.0, speed=V_TOP):
    q = add(p, mul(right_of(f), side))
    m = b.boost(q[0], q[1], q[2], f, speed=speed)
    return m


def strips(r, label, L, dy=0.0, w=None, every=50.0, lanes=None, cp=False, rails=False, first=30.0, last=20.0,
           speed=V_TOP, **kw):
    """A straight full of boost strips (one every `every` studs, in `lanes` side by side)."""
    w0 = w or r.w
    r.straight(label, L, dy=dy, w1=w0, lead=min(30.0, L / 4), cp=cp, rails=rails, **kw)
    lay_strips(r, first, L - last, every, lanes, speed)
    return r


def lay_strips(r, d0, d1, every=50.0, lanes=None, speed=V_TOP):
    b = r.b
    pts, ws, _ = r.last
    cum = [0.0]
    for a_, c_ in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))
    d = d0
    while d <= d1 + 1e-6:
        k = max(0, min(len(pts) - 2, next((i for i in range(len(pts) - 1) if cum[i + 1] >= d), len(pts) - 2)))
        t = (d - cum[k]) / max(cum[k + 1] - cum[k], 1e-6)
        p = lerp3(pts[k], pts[k + 1], max(0.0, min(1.0, t)))
        f = unit(sub(pts[k + 1], pts[k]))
        w = ws[k]
        n = lanes or (1 if w < 56 else 2 if w < 90 else 3)
        for i in range(n):
            strip_at(b, p, f, (i - (n - 1) / 2) * 27.0, speed)
        d += every


def boost_model(b, name, speed):
    """A model whose road parts all carry BoostSpeed: a boost deck (an exact speed floor, no stacking)."""
    return b.model(name, b.roads, {"BoostSpeed": float(speed)})


# ===================================================================== flights
def fly(p, v, ground, dt=0.01, tmax=8.0):
    """Fly from p with velocity v (gravity G) until the height drops to ground(p) (a function of the point, or None
    for no ground there). Returns (point, time) or (None, None)."""
    x, y, z = p
    vx, vy, vz = v
    t = 0.0
    while t < tmax:
        t += dt
        vy -= G * dt
        x, y, z = x + vx * dt, y + vy * dt, z + vz * dt
        if vy < 0:
            g = ground((x, y, z))
            if g is not None and y <= g:
                return (x, g, z), t
    return None, None


def line_ground(pts, f, y_none_before=None):
    """Ground height along a polyline of road tops (piecewise linear in distance along f), None outside it."""
    o = pts[0]
    ds = [dot(sub(q, o), f) for q in pts]

    def g(p):
        d = dot(sub(p, o), f)
        if d < ds[0] or d > ds[-1]:
            return None
        for k in range(len(ds) - 1):
            if ds[k] <= d <= ds[k + 1]:
                t = (d - ds[k]) / max(ds[k + 1] - ds[k], 1e-6)
                return pts[k][1] + (pts[k + 1][1] - pts[k][1]) * t
        return None
    return g


# ===================================================================== ramps
def kicker(r, label, deg, L=None, w=None, rails=True, name="Ramp"):
    """A concave ramp curving up from the road to a lip pitched `deg`. Returns the lip (road top) and the unit
    direction a car leaves it in."""
    b = r.b
    w = w or r.w
    f = r.f
    a = math.radians(deg)
    L = L or max(36.0, 2.4 * deg)
    R = L / a
    n = max(8, int(L / 3))
    pts = []
    for i in range(n + 1):
        th = a * i / n
        pts.append(add(r.p, add(mul(f, R * math.sin(th)), (0, R * (1 - math.cos(th)), 0))))
    s0 = len(b.samples)
    J.lay_road(b, pts, [w] * len(pts), rails=rails, name=name)
    r.last = (pts, [w] * len(pts), None)
    r._seg(label, s0)
    lip = pts[-1]
    # the lip: a bright edge and chevrons, so it reads as a launch
    fr = deck_frame(lip, sub(pts[-1], pts[-2]))
    Pt(b, "KickerLip", CF(add(lip, mul(fr.y, 0.1)), fr.x, fr.y, fr.z), (w - 2, 0.3, 2.0), b.skin.edge, "Neon", b.scenery)
    r.p = lip
    return lip, (f[0] * math.cos(a), math.sin(a), f[2] * math.cos(a))


def ramp_jump(r, label, deg=22.0, drop=60.0, V=V_TOP, w_land=None, slope=10.0, L_kick=None, land_min=260.0, cp=False,
              gap_fn=None, land_fn=None, jump_ok=False, rails=True):
    """The big one: a curved kicker at full strip speed, a gap, and a long landing runway that runs downhill under
    every flight: from the slowest take-off (90% of V) to the fastest, and (if jump_ok) the fastest with Space held on
    the lip as well. Returns the landing runway's end."""
    b = r.b
    w = r.w
    w_land = w_land or w
    lip, d = kicker(r, label + " Kicker", deg, L=L_kick, w=w, rails=rails)
    f = r.f
    # flights over a flat plane `drop` below the lip, to place the runway's start
    lo = V * V_SLACK
    p_lo, _ = fly(add(lip, (0, 0, 0)), mul(d, lo), lambda p: lip[1] - drop)
    start_d = dot(sub(p_lo, lip), f) - 70.0
    # the runway: a straight that eases into a downhill of `slope` degrees, long enough for the fastest flight
    g = math.tan(math.radians(slope))
    a0 = add(lip, add(mul(f, start_d), (0, -drop, 0)))
    gr = lambda p: (a0[1] - g * max(0.0, dot(sub(p, a0), f))) if dot(sub(p, a0), f) >= 0 else None
    far = 0.0
    q, _ = fly(lip, mul(d, V), gr)
    if q is not None:
        far = dot(sub(q, a0), f)
    # with Space held on the lip as well: covered too when that is not absurdly far (else the car brakes in the air)
    qj, _ = fly(lip, add(mul(d, V), (0, JUMP_V + JUMP_HOLD * 0.6, 0)), gr)
    if qj is not None and (jump_ok or dot(sub(qj, a0), f) < 480):
        far = max(far, dot(sub(qj, a0), f))
    Lr = max(land_min, far + 160.0)
    print("   ramp %-14s lip h=%5.0f  start %4.0f  far %4.0f  runway %4.0f (drop %.0f)" % (label, lip[1] - Y0, start_d, far, Lr,
                                                                                    g * Lr * 0.82))
    s0 = len(b.samples)
    # the gap's racing line: the nominal flight (at V)
    b.line(*lip)
    b.arc((lip[0], lip[1] + CAR_UP, lip[2]), mul(d, V), until_y=None, step=0.04)
    # (cut the arc where it meets the runway)
    gr = lambda p: (a0[1] - g * max(0.0, dot(sub(p, a0), f))) if dot(sub(p, a0), f) >= 0 else None
    tgt, T = fly(lip, mul(d, V), gr)
    while b.path and b.path[-1][3] == "a" and dot(sub(b.path[-1][:3], lip), f) > dot(sub(tgt, lip), f) - 4:
        b.path.pop()
    b.jumps.append(("ramp", lip, tgt, V * math.sqrt(d[0] ** 2 + d[2] ** 2), V * d[1]))
    if True:
        tj, _ = fly(lip, add(mul(d, V), (0, JUMP_V + JUMP_HOLD * 0.6, 0)), gr)
        b.jumps.append(("ramp_hop", lip, tj or tgt, V * math.sqrt(d[0] ** 2 + d[2] ** 2), V * d[1] + JUMP_V + JUMP_HOLD * 0.6))
    if gap_fn:
        gap_fn(b, lip, a0, f, w)
    r._seg(label + "-air", s0)
    r.p, r.w = a0, w_land
    n0 = len(b.path)
    r.straight(label + " Runway", Lr, dy=-g * Lr * 0.82, lead=20.0, cp=cp)
    b.path[n0:] = [p for p in b.path[n0:] if dot(sub(p[:3], tgt), f) > 6]
    if land_fn:
        land_fn(b, a0, f, Lr, w_land)
    return r


def drop_off(r, label, step, L=None, w=None, cp=False, V=V_TOP):
    """Drive off a ledge at speed onto a lower road (long enough for a full-speed fall)."""
    b = r.b
    f = r.f
    lip = r.p
    T = math.sqrt(2 * step / G)
    land = V * T
    L = L or land + 140
    b.line(*lip)
    b.arc((lip[0], lip[1] + CAR_UP, lip[2]), (f[0] * V, 0.0, f[2] * V), until_y=lip[1] - step + CAR_UP, step=0.04)
    b.jumps.append(("drop", lip, add(lip, add(mul(f, land), (0, -step, 0))), V, 0.0))
    r.p = add(lip, add(mul(f, 2.0), (0, -step, 0)))
    if w:
        r.w = w
    n0 = len(b.path)
    r.straight(label, L, lead=10.0, cp=cp)
    b.path[n0:] = [p for p in b.path[n0:] if dot(sub(p[:3], lip), f) > V * 0.55 * T]
    return r


# ===================================================================== bounce mushrooms
def bounce_pad(b, top, s, V, shroom=True):
    """An up-only launch over a cap: a mushroom's (the game widens it to the whole cap, BouncePad), or a square top
    (the pad covers it)."""
    k = 0.7 if shroom else 1.0
    a = {"CarLaunchPad": True, "LaunchExact": True, "LaunchVertical": float(V), "BoosterUp": True}
    if shroom:
        a["BouncePad"] = True
    b.part("LaunchPad", CF((top[0], top[1] + 0.3, top[2])), (s * k, 0.6, s * k), (255, 196, 60), "Slate",
           parent=b.track, transp=1, collide=False, query=False, attrs=a)


def bounce_chain(r, label, hops, H, s=110.0, cap=None, land_L=180.0, cp=False, w_out=None, shroom=True):
    """Mushroom caps that throw the car straight up as it lands; it keeps its own horizontal speed H (a boost deck
    before the chain sets it exactly) and steers to the next cap. The first throw is a pad at the road's end.
    hops: (D, dy, side): the next cap D ahead along the current line, dy higher, `side` to the right."""
    b = r.b
    s0 = len(b.samples)
    src = add(r.p, mul(r.f, -14))
    RT.trim_line(b, src, r.f)
    pts = [src]
    head = r.f
    for (D, dy, side) in hops:
        t = add(pts[-1], add(mul(head, D), add(mul(right_of(head), side), (0, dy, 0))))
        head = RT.flat(sub(t, pts[-1]))
        pts.append(t)
    for k in range(len(pts) - 1):
        c, n = pts[k], pts[k + 1]
        Dh = math.hypot(n[0] - c[0], n[2] - c[2])
        T = Dh / H
        V = (n[1] - c[1] + 0.5 * G * T * T) / T
        assert V > 60, ("bounce too flat", label, k, V)
        fd = RT.flat(sub(n, c))
        if k == 0:
            b.part("LaunchPad", look_frame((c[0], c[1] + 0.3, c[2]), fd), (r.w - 4, 0.6, 30), (255, 196, 60), "Slate",
                   parent=b.track, transp=1, collide=False, query=False,
                   attrs={"CarLaunchPad": True, "LaunchExact": True, "LaunchVertical": float(V), "BoosterUp": True})
            b.skin.pad_art(b, c, fd)
        else:
            bounce_pad(b, c, s, V, shroom)
        b.line(*c)
        b.arc((c[0], c[1] + CAR_UP, c[2]), (fd[0] * H, V, fd[2] * H), until_y=n[1] + CAR_UP + 2, step=0.04)
        b.jumps.append(("bounce", c, n, H, V))
    for c in pts[1:]:
        (cap or b.skin.plat)(b, c, s, r.rng)
        b.samples.append(c + (s,))
    last = pts[-1]
    hd = RT.flat(sub(last, pts[-2]))
    b.line(*last)
    r._seg(label, s0)
    r.f = hd
    r.p = add(last, mul(hd, s / 2 - 4))
    if w_out:
        r.w = w_out
    r.straight(label + " Out", land_L, lead=10.0, cp=cp)
    return pts[1:]


def boost_deck(r, label, L, speed, dy=0.0, w=None, cp=False, rails=False, turn=None, R=None, **kw):
    """A road that is all boost: every car is held at exactly `speed` (at least) while on it, and leaves at it.
    (turn: a bend of `turn` degrees at radius R instead of a straight.)"""
    b = r.b
    m = boost_model(b, label.replace(" ", ""), speed)
    if turn:
        r.turn(label, turn, R, dy=dy, w1=w, cp=cp, rails=rails, parent=m, **kw)
    else:
        r.straight(label, L, dy=dy, w1=w, lead=min(30.0, L / 4), cp=cp, rails=rails, parent=m, **kw)
    import parkour as V2
    pts, ws, _ = r.last
    cum = [0.0]
    for a_, c_ in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))
    dd = 20.0
    while dd < cum[-1] - 10:
        k = next(i for i in range(len(cum) - 1) if cum[i + 1] >= dd)
        p = lerp3(pts[k], pts[k + 1], (dd - cum[k]) / max(cum[k + 1] - cum[k], 1e-6))
        f = unit(sub(pts[k + 1], pts[k]))
        fr = deck_frame(add(p, mul(UP, 0.25)), f)
        for i in (-1, 0, 1):
            q = add(p, add(mul(right_of(RT.flat(f)), i * ws[k] / 3.2), mul(fr.y, 0.25)))
            V2.chevron(b, q, RT.flat(f), 9, b.skin.padc)
        dd += 30.0
    return r


# ===================================================================== conveyor belts and grease
def belt_road(r, label, L, speed, direction="along", w=None, cp=False, rails=False):
    """A road that is a conveyor belt: `direction` "along" (with the car), "back" (against it), "left"/"right"
    (pushing the car sideways)."""
    b = r.b
    f = r.f
    dvec = {"along": f, "back": mul(f, -1), "left": RT.left_of(f), "right": right_of(f)}[direction]
    m = b.model(label.replace(" ", ""), b.roads)
    before = set(map(id, m.descendants()))
    r.straight(label, L, w1=w, lead=min(20.0, L / 4), cp=cp, rails=rails, parent=m)
    for d in m.descendants():
        if id(d) in before or d.name != "Deck":
            continue
        a = rbxl.attrs(d) or {}
        a["Conveyor"] = float(speed)
        a["ConveyorDir"] = ("Vector3",) + tuple(float(v) for v in dvec)
        rbxl.set_attrs(d, a)
        if direction in ("along", "back"):
            import showcase as SC
            t = SC.tex(b, d, "grid", tile=10.0, color=b.skin.edge, transp=0.55)
            rbxl.set_attrs(t, {"BeltScroll": float(speed if direction == "along" else -speed)})
    # chevrons painted on, pointing the way the belt runs
    import parkour as V2
    pts, ws, _ = r.last
    cum = [0.0]
    for a_, c_ in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))
    dd = 25.0
    while dd < cum[-1] - 15:
        k = next(i for i in range(len(cum) - 1) if cum[i + 1] >= dd)
        p = lerp3(pts[k], pts[k + 1], (dd - cum[k]) / max(cum[k + 1] - cum[k], 1e-6))
        n = 1 if ws[k] < 50 else 2
        for i in range(n):
            q = add(p, add(mul(right_of(f), (i - (n - 1) / 2) * ws[k] / 2.4), (0, 0.3, 0)))
            V2.chevron(b, q, dvec, 12, b.skin.padc)
        dd += 40.0
    return r


def grease(b, c, f, L, w, name="Grease"):
    """A slick: the car keeps its momentum and the wheel barely turns it (ObbyHazard Slip)."""
    fr = deck_frame(c, f)
    Pt(b, name, CF(add(c, (0, 0.12, 0)), fr.x, fr.y, fr.z), (w, 0.2, L), (40, 34, 20), "Glass", b.scenery, refl=0.4)
    b.part("SlipZone", CF(add(c, (0, 4, 0)), fr.x, fr.y, fr.z), (w, 8, L), (40, 34, 20), parent=b.hazards, transp=1,
           collide=False, query=True, attrs={"ObbyHazard": "Slip"})


# ===================================================================== moving decks (the clock rotor engine)
_rid = [0]


def rotor(b, name, rest, axis, mode, parent=None, **spec):
    """A ClockRotor model: its parts are drawn at pose(t) * rest^-1 * built CFrame; parts marked ClockDeck carry the
    car. rest: CF (the rotor frame as built); axis: in the rest frame."""
    _rid[0] += 1
    rid = "R%d_%d" % (b.level_id, _rid[0])
    attrs = {"ClockRotor": rid, "ClockRest": ("CFrame", rest.p, rest.rows()), "ClockAxis": ("Vector3",) + tuple(axis),
             "ClockMode": mode}
    for k, v in spec.items():
        key = {"rpm": "ClockRpm", "amp": "ClockAmp", "period": "ClockPeriod", "phase": "ClockPhase", "step": "ClockStep",
               "ease": "ClockEase", "hold0": "ClockHold0", "angle0": "ClockAngle0", "near": "ClockNear"}[k]
        attrs[key] = float(v)
    if parent is not None:
        attrs["ClockParent"] = rbxl.attrs(parent)["ClockRotor"]
    m = b.model(name, b.hazards, attrs)
    return m


def deck_part(b, m, cf, size, color, mat, name="MovingDeck"):
    return Pt(b, name, cf, size, color, mat, m, collide=True, attrs={"ClockDeck": True})


def sand_field(b, name, tiles, delay=0.35, rate=70.0, depth=90.0):
    """Tiles that sink a moment after the car first touches them (ClockSand); tiles: [(cf, size, color, mat)]."""
    m = b.model(name, b.hazards, {"ClockSand": True, "SandDelay": float(delay), "SandRate": float(rate),
                                   "SandDepth": float(depth)})
    out = []
    for i, (cf, size, col, mat) in enumerate(tiles):
        out.append(Pt(b, "SinkTile", cf, size, col, mat, m, collide=True, attrs={"SandTile": float(i + 1)}))
    return m, out


# ===================================================================== tractor beams (magnet rides)
def magnet_ride(b, name, A, B, C, D, zone_c, zone_size, home, speed=150.0, out=140.0, perp=(1, 0, 0), head_fn=None):
    """The game's magnet ride: drive into the pickup zone and the car is lifted and carried along the Bezier A..D,
    then let go at D moving `out` along the path. head_fn(b, model, home) draws the head (a claw, a UFO)."""
    V3 = lambda p: ("Vector3",) + tuple(float(v) for v in p)
    m = b.model(name, b.hazards, {"MagnetRide": True, "RideA": V3(A), "RideB": V3(B), "RideC": V3(C), "RideD": V3(D),
                                   "RideSpeed": float(speed), "RideOut": float(out), "RidePerp": V3(perp),
                                   "HeadHome": V3(home)})
    b.part("MagnetPickup", zone_c if isinstance(zone_c, CF) else CF(zone_c), zone_size, (90, 200, 255), parent=m, transp=1, collide=False, query=False)
    head = b.model("MagnetHead", m)
    if head_fn:
        head_fn(b, head, home)
    return m


# ===================================================================== a board that falls away under you
def sink_board(r, label, L, W, cell=40.0, cols=((242, 238, 228), (34, 32, 38)), mats=("Marble", "Marble"),
               delay=0.3, rate=80.0, depth=120.0, sliders=(), slide_period=2.8, slider_fn=None, cp=False):
    """A wide floor of tiles that drop a moment after you touch them (stop and you go with them), with blocks
    sliding across it (sliders: distances along it)."""
    b = r.b
    f = r.f
    rt = right_of(f)
    s0 = len(b.samples)
    nL = int(round(L / cell))
    nW = int(round(W / cell))
    tiles = []
    fr = deck_frame(r.p, f)
    for i in range(nL):
        for j in range(nW):
            c = add(r.p, add(mul(f, (i + 0.5) * cell), mul(rt, (j - (nW - 1) / 2) * cell)))
            k = (i + j) % 2
            tiles.append((CF(add(c, (0, -3, 0)), fr.x, fr.y, fr.z), (cell - 0.3, 6, cell - 0.3), cols[k], mats[k]))
    sand_field(b, label.replace(" ", ""), tiles, delay=delay, rate=rate, depth=depth)
    for i in range(nL + 1):
        p = add(r.p, mul(f, i * cell))
        b.samples.append(p + (W,))
        if i % 1 == 0:
            b.line(*p)
    for k, d in enumerate(sliders):
        c = add(r.p, mul(f, d))
        amp = W - 48
        z0 = add(c, mul(rt, -W / 2 + 24))
        root = b.prop_root("Rook")
        rig = b.rig(root, "Slide", axis_frame(add(z0, (0, 9, 0)), rt), amp, slide_period + 0.3 * k, phase=(k * 0.37) % 1,
                    name="RookSlide")
        fr2 = deck_frame(z0, f)
        Pt(b, "Slider", CF(add(z0, (0, 9, 0)), fr2.x, fr2.y, fr2.z), (40, 18, 40), b.skin.body, b.skin.body_mat, rig,
           query=True, attrs={"ObbyHazard": "Knock"})
        if slider_fn:
            slider_fn(b, rig, add(z0, (0, 18, 0)), k)
    r._seg(label, s0)
    r.p = add(r.p, mul(f, nL * cell))
    r.w = W
    return r


# ===================================================================== clockwork rides (rotor decks that carry the car)
def _special_line(b, a, c, n=6):
    """Racing line over a moving deck (flag s: the validator does not look for fixed road under it)."""
    for k in range(n + 1):
        p = lerp3(a, c, k / n)
        b.path.append((p[0], p[1] + CAR_UP, p[2], "s"))


def gear_bridge(r, label, R, rpm, gap=3.0, col=(196, 160, 80), mat="Metal", teeth_col=None):
    """A huge gear lying flat, spinning: drive straight across it while it carries you sideways (steer against it)."""
    b = r.b
    f = r.f
    c = add(r.p, mul(f, gap + R))
    m = rotor(b, label.replace(" ", ""), CF(c), (0, 1, 0), "spin", rpm=rpm, near=R + 60)
    Pt(b, "MovingDeck", axis_frame(add(c, (0, -3, 0)), UP), (6, 2 * R, 2 * R), col, mat, m, collide=True, shape=2,
       attrs={"ClockDeck": True})
    n = max(12, int(TAU * R / 26))
    tc = teeth_col or col
    for k in range(n):
        a = TAU * k / n
        d = (math.cos(a), 0.0, math.sin(a))
        q = add(c, add(mul(d, R + 5), (0, -8, 0)))
        Pt(b, "GearTooth", CF(q, d, UP, (-d[2], 0, d[0])), (10, 4, 12), tc, mat, m)
    cyl(b, "GearHub", add(c, (0, 0.2, 0)), 0.4, R * 0.3, b.skin.edge, "Neon", m)
    for k in range(6):
        a = TAU * k / 6
        d = (math.cos(a), 0.0, math.sin(a))
        fr = CF(add(c, add(mul(d, R * 0.58), (0, 0.15, 0))), d, UP, (-d[2], 0, d[0]))
        Pt(b, "GearSpoke", fr, (R * 0.6, 0.3, 6), b.skin.edge, "Neon", m)
    cyl(b, "GearAxle", add(c, (0, -120, 0)), 230, 24, (90, 80, 70), "Metal", b.scenery)
    a0, a1 = add(r.p, mul(f, gap)), add(r.p, mul(f, gap + 2 * R))
    _special_line(b, a0, a1, 8)
    b.samples.append(c + (2 * R,))
    r.p = add(a1, mul(f, gap))
    return r


def turnstile(r, label, L, w=40.0, period=1.8, ease=0.5, gap=3.0, col=(40, 36, 32), mat="Metal", phase=0.0):
    """A bridge on a pivot that ticks round a quarter turn at a time: lined up with the road every other tick
    (cross while it is), sideways in between."""
    b = r.b
    f = r.f
    c = add(r.p, mul(f, gap + L / 2))
    m = rotor(b, label.replace(" ", ""), CF(c) * RT.rot_y(math.atan2(-f[2], f[0])), (0, 1, 0), "tick", step=math.pi / 2,
              period=period, ease=ease, phase=phase, near=L)
    fr = deck_frame(c, f)
    Pt(b, "MovingDeck", CF(add(c, (0, -2, 0)), fr.x, fr.y, fr.z), (w, 4, L), col, mat, m, collide=True,
       attrs={"ClockDeck": True})
    Pt(b, "HandTip", CF(add(c, add(mul(f, L / 2 - 6), (0, 0.2, 0))), fr.x, fr.y, fr.z), (w * 0.6, 0.3, 10), b.skin.edge,
       "Neon", m)
    cyl(b, "HandPin", add(c, (0, 0.4, 0)), 0.6, w * 0.8, b.skin.edge, "Neon", m)
    cyl(b, "HandAxle", add(c, (0, -90, 0)), 176, 14, (90, 80, 70), "Metal", b.scenery)
    a0, a1 = add(r.p, mul(f, gap)), add(r.p, mul(f, gap + L))
    _special_line(b, a0, a1, 6)
    b.samples.append(c + (L,))
    r.p = add(a1, mul(f, gap))
    return r


def pendulum_ferry(r, label, Lp=240.0, amp_deg=28.0, period=5.0, deck=(90.0, 70.0), phase=0.0, col=(196, 160, 80),
                   mat="Metal"):
    """A giant pendulum with a level deck at its foot, swinging along the road: wait for it at the near end of its
    swing, ride it over the gap, drive off at the far end."""
    b = r.b
    f = r.f
    A = math.radians(amp_deg)
    dl, dw = deck
    # the road's end is level with the deck at the near end of its swing
    near_c = add(r.p, mul(f, 2 + dl / 2))
    pivot = add(near_c, add(mul(f, Lp * math.sin(A)), (0, Lp * math.cos(A), 0)))
    bottom = sub(pivot, (0, Lp, 0))
    rt = right_of(f)
    # swing about the right axis: positive angle swings the foot ... (either way: the amp is symmetric)
    yaw = math.atan2(-f[2], f[0])
    rest = CF(pivot) * RT.rot_y(yaw)
    arm = rotor(b, label.replace(" ", "") + "Arm", rest, (0, 0, 1), "swing", amp=A, period=period, phase=phase,
                near=Lp + 80)
    fr = deck_frame(bottom, f)
    for s_ in (-1, 1):
        q = add(lerp3(pivot, bottom, 0.5), mul(rt, s_ * (dw / 2 - 4)))
        cyl(b, "PendulumRod", q, Lp - 6, 5, col, mat, arm)
    Pt(b, "PendulumBar", CF(add(bottom, (0, 6, 0)), fr.x, fr.y, fr.z), (dw, 4, 8), col, mat, arm)
    cyl(b, "PendulumPivot", pivot, dw + 30, 16, (60, 50, 40), "Metal", b.scenery, axis=rt)
    for s_ in (-1, 1):
        cyl(b, "PendulumPost", add(pivot, add(mul(rt, s_ * (dw / 2 + 15)), (0, -Lp * 0.6, 0))), Lp * 1.2 + 16, 12,
            (60, 50, 40), "Metal", b.scenery)
    dk = rotor(b, label.replace(" ", "") + "Deck", CF(bottom), (0, 1, 0), "hang", parent=arm, near=dl)
    Pt(b, "MovingDeck", CF(add(bottom, (0, -2.5, 0)), fr.x, fr.y, fr.z), (dw, 5, dl), col, mat, dk, collide=True,
       attrs={"ClockDeck": True})
    for k in (-1, 1):
        Pt(b, "DeckEdge", CF(add(bottom, add(mul(f, k * (dl / 2 - 1)), (0, 0.15, 0))), fr.x, fr.y, fr.z), (dw, 0.3, 2),
           b.skin.edge, "Neon", dk)
    far_c = add(pivot, add(mul(f, Lp * math.sin(A)), (0, -Lp * math.cos(A), 0)))
    _special_line(b, near_c, bottom, 4)
    _special_line(b, bottom, far_c, 4)
    b.samples.append(bottom + (dl,))
    r.p = add(far_c, mul(f, dl / 2 + 2))
    return r


# ===================================================================== the tractor beam
def _bez(A, B, C, D, t):
    u = 1 - t
    return tuple(A[i] * u * u * u + B[i] * 3 * u * u * t + C[i] * 3 * u * t * t + D[i] * t * t * t for i in range(3))


def ufo(b, head, home, col=(150, 160, 180), glow=(90, 255, 160)):
    cyl(b, "UfoHull", home, 6, 46, col, "Metal", head, refl=0.3)
    cyl(b, "UfoRim", add(home, (0, -1, 0)), 3, 52, (90, 96, 110), "Metal", head)
    ball(b, "UfoDome", add(home, (0, 5, 0)), 22, (170, 230, 255), "Glass", head, transp=0.3)
    for k in range(10):
        a = TAU * k / 10
        ball(b, "MagnetGlow", add(home, (math.cos(a) * 24, -1, math.sin(a) * 24)), 3.4, glow, "Neon", head)
    cyl(b, "TractorBeam", add(home, (0, -14, 0)), 22, 26, glow, "Neon", head, transp=0.75)


def tractor_beam(r, label, D, dy=0.0, turn=0.0, speed=210.0, out=170.0, land_L=260.0, w_land=None, cp=False):
    """Drive under the UFO at the road's end: it grabs the car, carries it D across the void (rising over the middle,
    turning `turn` degrees) and lets it go just over the next road."""
    b = r.b
    f = r.f
    th = math.radians(turn)
    c, s_ = math.cos(th), math.sin(th)
    f2 = RT.flat((f[0] * c + f[2] * s_, 0.0, -f[0] * s_ + f[2] * c))
    mid = RT.flat(add(f, f2))
    zone = add(r.p, add(mul(f, -24), (0, 9, 0)))
    A = add(r.p, add(mul(f, -24), (0, 5, 0)))
    E = add(r.p, add(mul(mid, D), (0, dy, 0)))
    Dp = add(E, (0, 7, 0))
    Bp = add(A, add(mul(f, D * 0.35), (0, 150, 0)))
    Cp = add(Dp, add(mul(f2, -D * 0.3), (0, 40, 0)))
    home = add(A, (0, 30, 0))
    fr = deck_frame(zone, f)
    m = magnet_ride(b, label.replace(" ", ""), A, Bp, Cp, Dp, CF(zone, fr.x, fr.y, fr.z), (r.w - 6, 24, 44), home,
                    speed=speed, out=out, perp=right_of(f), head_fn=lambda b_, h, p: ufo(b_, h, p))
    # where to drive: a glowing target on the road under the UFO
    from worlds import ringz
    ringz(b, add(add(r.p, mul(f, -24)), (0, 0.3, 0)), min(r.w / 2 - 4, 22), (90, 255, 160), "Neon", th=0.4,
          parent=b.scenery, name="BeamTarget")
    pts = [_bez(A, Bp, Cp, Dp, k / 24) for k in range(25)]
    for p in pts:
        b.path.append((p[0], p[1] + 1, p[2], "s"))
    r.p = E
    r.f = f2
    if w_land:
        r.w = w_land
    r.straight(label + " Drop Zone", land_L, lead=10.0, cp=cp)
    return r


# ===================================================================== lava
def lava_surge(r, label, L, w=None, low=-10.0, high=12.0, period=4.0, phase=0.0, up_frac=0.4, cp=False):
    """A low causeway over a lava lake that surges: every `period` s the lava rises over the road for a moment
    (cross between surges)."""
    b = r.b
    w = w or r.w
    f = r.f
    r.straight(label, L, w1=w, lead=10.0, cp=cp)
    c = add(r.p, mul(f, -L / 2))
    fr = deck_frame(c, f)
    root = b.prop_root("LavaSurge")
    amp = high - low
    # 0 = low for most of the cycle, a quick swell up and back down
    k0 = (1 - up_frac) / 2
    rig = b.rig(root, "Slide", axis_frame(add(c, (0, low, 0)), (0, 1, 0)), amp, period, phase=phase,
                keys="0:0 %.2f:0 %.2f:1 %.2f:1 %.2f:0" % (k0, k0 + 0.12, 1 - k0 - 0.12, 1 - k0), name="Surge")
    lava = getattr(b.skin, "LAVA", (255, 110, 20))
    Pt(b, "LavaSurge", CF(add(c, (0, low - 1.5, 0)), fr.x, fr.y, fr.z), (w + 120, 3, L + 40), lava, "Neon", rig,
       query=True, attrs={"ObbyHazard": "Burn"})
    Pt(b, "LavaCrust", CF(add(c, (0, low - 3.4, 0)), fr.x, fr.y, fr.z), (w + 124, 1, L + 44), (120, 40, 10), "Basalt", rig)
    # the lake it surges from
    Pt(b, "LavaLake", CF(add(c, (0, low - 4, 0)), fr.x, fr.y, fr.z), (w + 200, 2, L + 120), lava, "Neon", b.hazards,
       query=True, attrs={"ObbyHazard": "Burn"})
    return r


def crater(b, C, R, y_floor, y_rim, rng, rock=(40, 34, 32), glow=(255, 120, 30), gap=None, gap_deg=50.0):
    """The inside of a volcano: a ring of craggy basalt walls round centre C from y_floor up to y_rim, broken open
    toward direction `gap` (where the road comes in and goes out)."""
    n = int(TAU * R / 46)
    for k in range(n):
        a = TAU * (k + rng.random() * 0.3) / n
        d = (math.cos(a), 0.0, math.sin(a))
        if gap is not None and dot(d, gap) > math.cos(math.radians(gap_deg)):
            continue
        rr = R + rng.uniform(0, 40)
        h = (y_rim - y_floor) * rng.uniform(0.75, 1.05)
        sz = rng.uniform(60, 90)
        c = (C[0] + d[0] * rr, y_floor + h / 2, C[2] + d[2] * rr)
        Pt(b, "CraterWall", CF(c, d, UP, (-d[2], 0, d[0])), (sz * 0.7, h, sz), rock, "Basalt", b.scenery)
        if rng.random() < 0.4:
            Pt(b, "LavaVein", CF(add(c, mul(d, -sz * 0.36)), d, UP, (-d[2], 0, d[0])), (1, h * 0.8, 3), glow, "Neon",
               b.scenery)
    cyl(b, "CraterPool", (C[0], y_floor, C[2]), 4, 2 * R + 40, glow, "Neon", b.hazards, query=True,
        attrs={"ObbyHazard": "Burn"})


# ===================================================================== snow and ice
def ice_patch(b, c, f, L, w):
    """Black ice: the car slides (ObbyHazard Slip)."""
    fr = deck_frame(c, f)
    Pt(b, "IcePatch", CF(add(c, (0, 0.12, 0)), fr.x, fr.y, fr.z), (w, 0.2, L), (200, 235, 255), "Ice", b.scenery,
       refl=0.3, transp=0.15)
    b.part("SlipZone", CF(add(c, (0, 4, 0)), fr.x, fr.y, fr.z), (w, 8, L), (200, 235, 255), parent=b.hazards, transp=1,
           collide=False, query=True, attrs={"ObbyHazard": "Slip"})


def rollers(r, at, d=28.0, period=2.6, col=(245, 250, 255)):
    """Big snowballs rolling back and forth across the road just laid (at: distances along it)."""
    b = r.b
    pts, ws, _ = r.last
    cum = [0.0]
    for a_, c_ in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))
    for k, dd in enumerate(at):
        i = next(i for i in range(len(cum) - 1) if cum[i + 1] >= dd)
        p = lerp3(pts[i], pts[i + 1], (dd - cum[i]) / max(cum[i + 1] - cum[i], 1e-6))
        f = RT.flat(sub(pts[i + 1], pts[i]))
        w = ws[i]
        rt = right_of(f)
        z0 = add(p, add(mul(rt, -w / 2 + d / 2 + 1), (0, d / 2, 0)))
        root = b.prop_root("Snowball")
        rig = b.rig(root, "Slide", axis_frame(z0, rt), w - d - 2, period + 0.35 * k, phase=(k * 0.41) % 1,
                    name="Roll")
        ball(b, "Snowball", z0, d, col, "Snow", rig, query=True, attrs={"ObbyHazard": "Knock"})
        ball(b, "SnowballLump", add(z0, (2, d * 0.32, 3)), d * 0.5, col, "Snow", rig)
    return r


# ===================================================================== laser gates on a beat
def beat_gates(r, at, V, period=1.2, on=0.45, phase0=0.0, full=True):
    """Laser gates across the road just laid, flashing on a beat that travels down the road at V: a car moving at
    exactly V (a boost deck holds it there) that passes the first gate while it is off passes them all."""
    b = r.b
    pts, ws, _ = r.last
    cum = [0.0]
    for a_, c_ in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))

    def gate(b_, c, w, i, ph=0.0):
        beams = [(4 + 7 * k, 2.2) for k in range(5)] if full else [(3.2, 3.0)]
        attrs = {"ObbyHazard": "Zap", "ZapFX": True, "ZapPeriod": float(period), "ZapOn": float(on), "ZapPhase": float(ph)}
        b_.skin.gate(b_, c[0], c[1], c[2], w, beams, attrs, i)

    for k, d in enumerate(at):
        ph = (phase0 - (d - at[0]) / (V * period)) % 1.0
        r.along(lambda b_, c, w, i, ph=ph: gate(b_, c, w, i, ph), [d], i0=k)
    return r


# ===================================================================== scenery round a level
def dress(r, makers, n, rng, near=200.0, far=620.0, ground=None, tries=400):
    """Stand n landmarks round the route: makers = [(fn(b, base, rng), radius, height)]. Each is built, measured
    (its real box), and kept only if it is clear of every road and every flight (racing line) it could touch, of
    the other landmarks, and inside the level's box; otherwise it is taken down and another spot tried.
    ground: the height they stand on (default: 260 under the lowest road)."""
    if getattr(r, "defer_dress", None) is not None:
        # (the level's home stretch is not laid yet: dress once it is)
        r.defer_dress.append((makers, n, rng, near, far, ground, tries))
        return []
    import numpy as np
    from factory import is_basepart
    b = r.b
    lvl = b.level
    S = np.array([s_[:4] for s_ in b.samples], dtype=float)
    Pp = np.array([p[:3] for p in b.path], dtype=float)
    g = ground if ground is not None else float(S[:, 1].min()) - 260.0
    placed = []
    k = 0
    for _ in range(tries):
        if k >= n:
            break
        fn, rad, H = makers[k % len(makers)]
        i = rng.randrange(len(S))
        a = rng.random() * TAU
        d = rng.uniform(near, far) + rad
        x, z = S[i, 0] + math.cos(a) * d, S[i, 2] + math.sin(a) * d
        if x - rad < X0 + 10 or x + rad > b.X1 - 10:
            continue
        if any(math.hypot(x - px, z - pz) < rad + pr + 30 for px, pz, pr in placed):
            continue
        before = set(map(id, lvl.descendants()))
        fn(b, (x, g, z), rng)
        new = [d_ for d_ in lvl.descendants() if id(d_) not in before]
        boxes = []
        for d_ in new:
            if not is_basepart(d_):
                continue
            cf = CF.from_prop(d_.get("CFrame"))
            sz = d_.get("size")
            e = [abs(cf.x[j]) * sz[0] / 2 + abs(cf.y[j]) * sz[1] / 2 + abs(cf.z[j]) * sz[2] / 2 for j in range(3)]
            boxes.append((cf.p[0] - e[0], cf.p[1] - e[1], cf.p[2] - e[2], cf.p[0] + e[0], cf.p[1] + e[1], cf.p[2] + e[2]))
        ok = bool(boxes)
        if ok:
            B = np.array(boxes)
            lo, hi = B[:, :3].min(axis=0), B[:, 3:].max(axis=0)
            ok = lo[0] > X0 + 3 and hi[0] < b.X1 - 3
        if ok:
            # every part's box, grown by a margin, against the roads (their half width) and the racing line
            for bx in B:
                m = 30.0
                near_s = ((S[:, 0] + S[:, 3] / 2 + m > bx[0]) & (S[:, 0] - S[:, 3] / 2 - m < bx[3]) &
                          (S[:, 2] + S[:, 3] / 2 + m > bx[2]) & (S[:, 2] - S[:, 3] / 2 - m < bx[5]) &
                          (S[:, 1] + 40 > bx[1]) & (S[:, 1] - 40 < bx[4]))
                near_p = ((Pp[:, 0] + m > bx[0]) & (Pp[:, 0] - m < bx[3]) & (Pp[:, 2] + m > bx[2]) &
                          (Pp[:, 2] - m < bx[5]) & (Pp[:, 1] + 30 > bx[1]) & (Pp[:, 1] - 30 < bx[4]))
                if near_s.any() or near_p.any():
                    ok = False
                    break
        if not ok:
            ids = set(map(id, new))
            for d_ in new:
                if d_.parent is not None and id(d_.parent) not in ids:
                    d_.parent.children.remove(d_)
                    d_.parent = None
            continue
        placed.append((x, z, rad))
        k += 1
    return placed
