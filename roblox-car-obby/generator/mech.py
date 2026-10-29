"""The Mechanical Playground: one huge car obby across the ten course slots (OBBY1-10), each slot one or two sections
of the map. Dark steel structure, colourful road tops, hazard stripes, glowing boost strips; every section has its own
accent colour. Moving machines use the game's own systems: ObbyPropAnim rigs (hammers, crushers, wrecking balls,
fans, pistons), the clock rotor engine (bridges that turn and tilt and carry the car), sinking tiles (collapsing
road), the arcade brick walls (destructible barriers), WallRide surfaces (the loop).

Main route: the racing line. Alternate routes (high/low landings, the three-way split, the loop shortcut and bypass,
the lower bridge route, hidden passages) are laid by their own turtles and add no racing line; their jumps are still
recorded, so the validator flies them too.
"""
import math
import random
from geom import CF, deck_frame, axis_frame, look_frame, add, sub, mul, unit, cross, dot, rot_y, rot_axis, UP
from builder import G, CAR_UP, X0, Y0, ZC, mix
import route as RT
import journey as J
import rush2 as R2
import obby as O
import stages as S
import epic_marks as M
import showcase as SC
from skins import Skin, Pt, box, cyl, ball, samples
from worlds import ell, ringz
import journey_skins  # noqa: F401  (road_piece etc. on the base skin)

TAU = math.pi * 2
STEEL, STEEL_DK, STEEL_LT = (52, 56, 64), (34, 36, 42), (96, 102, 112)
HAZ_Y, HAZ_K = (255, 200, 30), (30, 30, 34)
WHITE = (240, 242, 246)

# accents per section
ACC = {"launch": (255, 140, 30), "hammer": (230, 50, 50), "highway": (40, 200, 230), "loop": (170, 80, 255),
       "crusher": (255, 205, 40), "air": (70, 220, 110), "bridge": (60, 120, 255), "wreck": (255, 90, 60),
       "cork": (255, 70, 180), "fan": (40, 230, 200), "smash": (200, 140, 70), "final": (255, 230, 90)}


def right_of(f):
    return mul(RT.left_of(f), -1)


# ===================================================================== the skin
class Machine(Skin):
    key, title, theme_name = "machine", "Mechanical Playground", "Mechanical playground"
    clock, bloom, hue, scale = 13.5, 0.5, 0.58, 1.0
    body, top, edge, padc, danger = STEEL, (255, 140, 30), HAZ_Y, (90, 220, 255), (255, 60, 40)
    body_mat, top_mat = "DiamondPlate", "SmoothPlastic"
    gate_post, gate_board, gate_text = STEEL, (24, 26, 32), HAZ_Y
    finish_cols = ((245, 245, 245), (24, 24, 28))
    light_over = {"Lt_Atmosphere_Density": 0.18, "Lt_Atmosphere_Haze": 0.6}

    def road_style(self):
        return dict(top=self.top, top_mat="SmoothPlastic", edge=HAZ_Y, edge_mat="SmoothPlastic", side=STEEL,
                    side_mat="DiamondPlate", refl=0.05, center=None)

    def road_piece(self, b, parent, fr, w, L, name):
        F = lambda p: CF(p, fr.x, fr.y, fr.z)
        o = lambda x=0.0, y=0.0, z=0.0: add(fr.p, add(add(mul(fr.x, x), mul(fr.y, y)), mul(fr.z, z)))
        Pt(b, name, F(o(y=-2.0)), (w, 4, L), self.top, "SmoothPlastic", parent, collide=True, refl=0.05)
        for k in (-1, 1):
            e = Pt(b, "HazardEdge", F(o(x=k * (w / 2 - 1.5), y=0.06)), (3, 0.12, L), HAZ_K, "SmoothPlastic", parent)
            SC.tex(b, e, "checker", tile=3.0, color=HAZ_Y)
            Pt(b, "RoadSide", F(o(x=k * (w / 2 + 0.6), y=-4.5)), (1.2, 9, L), STEEL, "DiamondPlate", parent)
        Pt(b, "SteelBelly", F(o(y=-7.5)), (w * 0.7, 3, L), STEEL_DK, "Metal", parent)
        # lane lines: dashes every 30 studs, one per lane boundary
        nl = 3 if w >= 90 else 2 if w >= 50 else 1
        for i in range(1, nl):
            x = -w / 2 + w * i / nl
            d = -L / 2 + 10
            while d < L / 2 - 6:
                Pt(b, "LaneDash", F(o(x=x, y=0.07, z=d)), (1.2, 0.14, 9), WHITE, "SmoothPlastic", parent)
                d += 30

    def under(self, b, top, w, i):
        """Steel trusses under the road: two legs, a cross beam and a diagonal, bolts."""
        if getattr(b, "no_under", False):
            return
        x, y, z = top
        for s in (-1, 1):
            cyl(b, "TrussLeg", (x, y - 46, z + s * w * 0.32), 90, 4, STEEL_DK, "Metal")
            ball(b, "Bolt", (x, y - 2, z + s * w * 0.32), 5, STEEL_LT, "Metal")
        box(b, "TrussBeam", (x, y - 30, z), (4, 4, w * 0.64), STEEL, "Metal")
        Pt(b, "TrussBrace", CF((x, y - 46, z)) * rot_axis((1, 0, 0), math.atan2(60, w * 0.64)), (3, 3, math.hypot(60, w * 0.64)),
           STEEL, "Metal", b.scenery)

    def pad_art(self, b, start, f):
        fr = deck_frame(start, f)
        for k in range(3):
            q = add(start, mul(f, -8 + k * 8))
            Pt(b, "PadChevron", CF(add(q, (0, 0.2, 0)), fr.x, fr.y, fr.z), (16, 0.2, 3), self.padc, "Neon")

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        self.road_piece(b, parent or b.roads, deck_frame((cx, y, z), (1, 0, 0)), w, L, "Deck")
        samples(b, x0, x1, y, z, w)

    def finish(self, b, x0, x1, y, z, w):
        if getattr(b, "final_slot", False):
            Skin.finish(self, b, x0, x1, y, z, w)
            finish_arch(b, (x1 - 60, y, z), (1, 0, 0), w)

    def environment(self, b):
        pass


def accent(b, col):
    b.skin.top = col


# ===================================================================== small parts
def stripe_box(b, name, cf, size, parent=None, tile=4.0, collide=False):
    """A black part with yellow hazard checks (the warning stripe look)."""
    p = Pt(b, name, cf, size, HAZ_K, "SmoothPlastic", parent if parent is not None else b.scenery, collide=collide)
    SC.tex(b, p, "checker", tile=tile, color=HAZ_Y, face=1)
    for face in (0, 2, 3, 5):
        SC.tex(b, p, "checker", tile=tile, color=HAZ_Y, face=face)
    return p


def lamp(b, p, col=(255, 60, 40), d=3.0, pulse=1.5):
    q = ball(b, "WarnLamp", p, d, col, "Neon", b.scenery)
    import rbxl
    rbxl.set_attrs(q, {"PropPulse": float(pulse)})
    return q


def arrows(r, at, col=(255, 255, 255)):
    """Big glowing continuation chevrons painted on the road just laid."""
    import parkour as V2
    b = r.b
    pts, ws, _ = r.last
    cum = [0.0]
    for a_, c_ in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))
    for d in at:
        d = min(max(d, 1), cum[-1] - 1)
        i = next(i for i in range(len(cum) - 1) if cum[i + 1] >= d)
        p = R2.lerp3(pts[i], pts[i + 1], (d - cum[i]) / max(cum[i + 1] - cum[i], 1e-6))
        f = RT.flat(sub(pts[i + 1], pts[i]))
        for k in range(2):
            V2.chevron(b, add(p, add(mul(f, k * 10), (0, 0.35, 0))), f, 22, col)


def road(r, label, L, w=None, dy=0.0, rails=True, boosts=0, every=60.0, cp=False, arrows_at=(), line=True, **kw):
    """A machine road: colourful top, hazard edges, lane dashes, guard rails, trusses; optional strip runs."""
    r.straight(label, L, dy=dy, w1=w, lead=min(30.0, L / 4), cp=cp, rails=rails, line=line, **kw)
    if boosts:
        R2.lay_strips(r, max(30.0, L * 0.1), L - 30, every=every, lanes=boosts)
    if arrows_at:
        arrows(r, arrows_at)
    return r


def gantry(b, c, f, w, h=50.0, col=STEEL, lamps=True):
    """A steel frame straddling the road at c (road top): two posts, a beam, hazard-striped plates and lamps."""
    rt = right_of(f)
    fr = deck_frame(c, f)
    for s in (-1, 1):
        q = add(c, mul(rt, s * (w / 2 + 6)))
        Pt(b, "GantryPost", CF(add(q, (0, h / 2, 0)), fr.x, fr.y, fr.z), (8, h, 8), col, "Metal", b.scenery, collide=True)
        stripe_box(b, "GantryFoot", CF(add(q, (0, 4, 0)), fr.x, fr.y, fr.z), (9, 8, 9))
        if lamps:
            lamp(b, add(q, (0, h + 3, 0)))
    Pt(b, "GantryBeam", CF(add(c, (0, h + 4, 0)), fr.x, fr.y, fr.z), (w + 24, 8, 10), col, "Metal", b.scenery)
    stripe_box(b, "GantryStripe", CF(add(c, (0, h - 0.6, 0)), fr.x, fr.y, fr.z), (w + 20, 1.2, 10.4))


def impact_zone(b, c, f, w, L):
    fr = deck_frame(c, f)
    stripe_box(b, "ImpactZone", CF(add(c, (0, 0.09, 0)), fr.x, fr.y, fr.z), (w - 6, 0.12, L), tile=6.0)


def big_gear(b, c, R, axis, col, spin=0.05, phase=0.0):
    M.gear(b, c, R, axis, col, spin=spin, phase=phase, th=12.0)


# ===================================================================== hammers (built at c heading +X across a road w wide)
def crusher_v(b, c, w, i, H=46.0, period=2.4, bl=40.0):
    """A vertical crusher: a huge steel head on a piston in a frame, slamming down onto a striped zone (CRUSHED)."""
    x, y, z = c
    rc = (x, y + H + 11, z)
    gantry(b, c, (1, 0, 0), w, h=H + 26)
    impact_zone(b, c, (1, 0, 0), w, bl)
    root = b.prop_root("Crusher")
    rig = b.rig(root, "Slide", axis_frame(rc, (0, -1, 0)), H + 1, period, phase=(i * 0.31) % 1,
                keys="0:0 0.42:0 0.5:1 0.66:1 0.95:0", name="Slam")
    Pt(b, "CrusherHead", CF(rc), (bl, 22, w + 2), STEEL, "DiamondPlate", rig, query=True, attrs={"ObbyHazard": "Crush"})
    stripe_box(b, "CrusherFace", CF(add(rc, (0, -11.3, 0))), (bl + 0.4, 0.6, w + 2.4), parent=rig)
    cyl(b, "Piston", add(rc, (0, 24, 0)), 26, 10, STEEL_LT, "Metal", rig, refl=0.3)
    for s in (-1, 1):
        cyl(b, "PistonGuide", (x + s * (bl / 2 - 4), y + H + 30, z), 40, 4, STEEL_DK, "Metal", b.scenery)


def side_hammer(b, c, w, i, period=2.6):
    """A hammer on a post at the road's edge, swinging its arm flat across the road and back (knocks you off)."""
    x, y, z = c
    s = 1 if i % 2 == 0 else -1
    post = (x, y, z + s * (w / 2 + 10))
    L = w * 0.85
    cyl(b, "HammerPost", add(post, (0, 14, 0)), 28, 12, STEEL, "Metal", b.scenery, collide=True)
    stripe_box(b, "HammerBase", CF(add(post, (0, 3, 0))), (16, 6, 16))
    root = b.prop_root("SideHammer")
    # the arm points along the road at rest; it swings in across it (about the post's vertical axis)
    rig = b.rig(root, "Hinge", axis_frame(add(post, (0, 9, 0)), (0, 1, 0)), 90.0 * s, period, phase=(i * 0.27) % 1,
                keys="0:0 0.35:0 0.5:1 0.75:1 0.95:0", name="Swing")
    arm_c = add(post, (L / 2, 9, 0))
    Pt(b, "HammerArm", CF(arm_c), (L, 4, 4), STEEL_LT, "Metal", rig)
    head = add(post, (L, 9, 0))
    Pt(b, "HammerHead", CF(head), (12, 16, 22), (200, 40, 40), "Metal", rig, query=True, attrs={"ObbyHazard": "Knock"})
    stripe_box(b, "HammerFace", CF(add(head, (6.2, 0, 0))), (0.4, 16, 22), parent=rig)


def punch(b, c, w, i, period=1.5, lane=None):
    """An overhead punch: a fast piston over one lane (CRUSHED)."""
    x, y, z = c
    k = (i % 3) - 1 if lane is None else lane
    zz = z + k * w / 3
    H = 34.0
    rc = (x, y + H + 7, zz)
    root = b.prop_root("Punch")
    rig = b.rig(root, "Slide", axis_frame(rc, (0, -1, 0)), H, period, phase=(i * 0.43) % 1,
                keys="0:0 0.5:0 0.56:1 0.66:1 0.9:0", name="Punch")
    Pt(b, "PunchFist", CF(rc), (22, 14, w / 3 - 4), (230, 60, 50), "SmoothPlastic", rig, query=True,
       attrs={"ObbyHazard": "Crush"})
    cyl(b, "PunchRod", add(rc, (0, 16, 0)), 20, 6, STEEL_LT, "Metal", rig)
    Pt(b, "PunchHousing", CF((x, y + H + 30, zz)), (28, 14, w / 3), STEEL, "Metal", b.scenery)
    impact_zone(b, (x, y, zz), (1, 0, 0), w / 3 + 4, 22)


def sweep_arm(b, c, w, i, speed=0.22):
    """A huge arm spinning flat over the road from a tower at its edge, sweeping across it once a turn."""
    x, y, z = c
    s = 1 if i % 2 == 0 else -1
    hub = (x, y + 8, z + s * (w / 2 + 12))
    cyl(b, "ArmTower", add(hub, (0, 2, 0)), 22, 18, STEEL, "Metal", b.scenery, collide=True)
    stripe_box(b, "ArmTowerBand", CF(add(hub, (0, -4, 0))), (19, 3, 19))
    root = b.prop_root("SweepArm")
    rig = b.rig(root, "Spin", axis_frame(add(hub, (0, 2, 0)), (0, 1, 0)), speed * (1 if i % 2 else -1), 4,
                phase=(i * 0.19) % 1, name="ArmSpin")
    L = w + 16
    for k in (-1, 1):
        Pt(b, "SweepBar", CF(add(hub, (k * L / 2, 3, 0))), (L, 6, 6), (255, 210, 40), "SmoothPlastic", rig, query=True,
           attrs={"ObbyHazard": "Knock"})
    cyl(b, "ArmHub", add(hub, (0, 3, 0)), 10, 14, STEEL_LT, "Metal", rig)


def spark_gear(b, c, f, side, R=60.0, col=STEEL_LT, spin=0.06):
    """An oversized gear turning beside the track."""
    big_gear(b, add(c, add(mul(right_of(f), side), (0, R * 0.6, 0))), R, f, col, spin=spin)


# ===================================================================== alternate routes
class Alt:
    """A side route: its own turtle and obby links, no racing line (its jumps are still recorded and flown)."""

    def __init__(self, main, p, f, w, B=230.0):
        self.b = main.b
        self.r = RT.Route(main.b, p, f, w)
        self.r.rng = main.rng
        self.r.X1 = main.X1
        self.o = O.Obby(self.r, B)
        self.n0 = len(self.b.path)
        self.cp0 = len(self.b.cps)

    def done(self):
        del self.b.path[self.n0:]
        return self


def landing(b, a, f, w, L, col=None):
    """A reinforced landing pad (no racing line): thick steel edges, hazard lip, arrows."""
    r = RT.Route(b, a, f, w)
    r.rng = random.Random(1)
    r.straight("Alt Landing", L, lead=5.0, rails=True, line=False)
    return r


def big_ring(b, c, R, axis, col, spin=0.03):
    rig = SC.spin(b, c, axis, spin, 0.0, "RingSpin") if spin else b.scenery
    ringz(b, c, R, STEEL, "Metal", th=12.0, axis=axis, parent=rig, name="IndustrialRing")
    ringz(b, c, R - 7, col, "Neon", th=1.6, axis=axis, parent=rig, name="RingGlow")
    a = unit(axis)
    e1 = unit(cross(a, UP)) if abs(a[1]) < 0.9 else (1.0, 0.0, 0.0)
    e2 = cross(a, e1)
    for k in range(8):
        th = TAU * k / 8
        d = add(mul(e1, math.cos(th)), mul(e2, math.sin(th)))
        q = add(c, mul(d, R + 6))
        Pt(b, "RingClamp", CF(q, a, d, cross(a, d)), (16, 14, 16), HAZ_K, "Metal", rig)


def slot1(r, sk, rng):
    b = r.b
    sk.title = "Launch Runway"
    b.gate_label = "STAGE 1"
    accent(b, ACC["launch"])
    road(r, "Launch Runway", 620, w=110, boosts=3, every=50, arrows_at=(60, 300, 560))
    for d in (150, 330, 510):
        gantry(b, r.ahead(d - 620), r.f, 110, h=40)
    R2.ramp_jump(r, "Giant Ramp", deg=22, drop=60, w_land=120, slope=4, land_min=430, cp=True)
    kind, lip, tgt, H, V = [j for j in b.jumps if j[0] == "ramp"][-1]
    f = RT.flat(sub(tgt, lip))
    rt = right_of(f)
    # the suspended ring over the gap, the flight right through its middle
    t_ap = V / G
    ring_c = add(lip, add(mul(f, H * t_ap * 0.9), (0, V * V / (2 * G) * 0.8 + CAR_UP, 0)))
    big_ring(b, ring_c, 125, f, ACC["launch"], spin=0.03)
    for s in (-1, 1):
        q = add(ring_c, mul(rt, s * 175))
        cyl(b, "RingPylon", (q[0], (q[1] + Y0 - 500) / 2, q[2]), q[1] - (Y0 - 500), 22, STEEL_DK, "Metal", b.scenery)
        Pt(b, "RingArm", CF(R2.lerp3(q, add(ring_c, mul(rt, s * 131)), 0.5), *_axes(rt)), (14, 10, 44), STEEL, "Metal",
           b.scenery)
    accent(b, ACC["launch"])
    road(r, "Reconnect Straight", 420, w=120, boosts=3, every=70, arrows_at=(200,))
    main_end = r.p
    # ---- the elevated route: high and to the right, only for a car still at full speed that steers for it
    hi_y = lip[1] - 14
    def cross_y(Vs, y_rel):
        vx, vy = Vs * math.cos(math.radians(22)), Vs * math.sin(math.radians(22))
        t = (vy + math.sqrt(vy * vy + 2 * G * -y_rel)) / G
        return vx * t
    xf = cross_y(330.0, hi_y - lip[1])
    xs = cross_y(318.0, hi_y - lip[1])
    a = add(add(lip, mul(f, xs - 40)), add(mul(rt, 100), (0, hi_y - lip[1], 0)))
    al = Alt(r, a, f, 42, B=330.0)
    accent(b, (255, 210, 120))
    al.r.straight("High Line", 330, lead=5.0, rails=True, line=False)
    R2.lay_strips(al.r, 30, 300, every=60, lanes=1)
    # (only a car still at full speed makes it: flown at exactly that speed)
    b.jumps.append(("exact", lip, add(add(lip, mul(f, xf)), add(mul(rt, 100), (0, hi_y - lip[1], 0))), 330 * math.cos(math.radians(22)),
                    330 * math.sin(math.radians(22))))
    for d in (60, 200, 320):
        q = add(a, mul(f, d))
        for s in (-1, 1):
            cyl(b, "HangCable", add(q, add(mul(rt, s * 22), (0, 130, 0))), 260, 1.2, STEEL_LT, "Metal", b.scenery)
    al.o.drop(46, side=-100)
    al.done()
    # ---- the lower route: down and to the left, small hops, then up a pad back onto the straight
    lo_y = lip[1] - 120
    xs2 = cross_y(280.0, lo_y - lip[1])
    a = add(add(lip, mul(f, xs2 - 30)), add(mul(rt, -115), (0, lo_y - lip[1], 0)))
    al = Alt(r, a, f, 70, B=230.0)
    accent(b, (255, 120, 60))
    al.o.plat("Low Road", 300, 70)
    b.jumps.append(("ramp", lip, add(add(lip, mul(f, cross_y(330.0, lo_y - lip[1]))), add(mul(rt, -115), (0, lo_y - lip[1], 0))),
                    330 * math.cos(math.radians(22)), 330 * math.sin(math.radians(22))))
    al.o.drop(30)
    al.o.plat("Low Hop", 150, 40, [(O.saw, 0.5)])
    al.o.kick(0, side=0)
    al.o.plat("Low Ledge", 140, 50)
    # up onto the reconnect straight
    al.o.pad(main_end[1] - al.r.p[1], side=115)
    al.done()
    accent(b, ACC["hammer"])
    # ---- 2. the hammer corridor
    sk.title = "Launch Runway"
    road(r, "Corridor Entry", 160, w=80, cp=True, arrows_at=(80,))
    r.log("corridor")
    L = 1700.0
    road(r, "Hammer Corridor", L, w=80)
    kinds = [crusher_v, side_hammer, punch, sweep_arm, crusher_v, punch, side_hammer, sweep_arm, crusher_v, side_hammer,
             punch, crusher_v]
    at = [130 + 130 * k for k in range(len(kinds))]
    for k, (fn, d) in enumerate(zip(kinds, at)):
        r.along(fn, [d], i0=k)
    _corridor_shell(r, L, 80, rng)
    road(r, "Corridor Exit", 300, w=80, dy=60, boosts=2, every=60, cp=True)
    # ---- the corridor's second hall: an S-bend of sweeping arms and hammers, then a last row of crushers
    r.turn("Hammer Bend", 30, 360, rails=True)
    r.along(sweep_arm, [100], i0=0)
    _corridor_shell(r, 0, 80, rng)
    r.turn("Hammer Bend Swing", -60, 360, rails=True)
    r.along(side_hammer, [70], i0=1)
    r.along(punch, [150, 220], i0=0)
    r.along(sweep_arm, [300], i0=1)
    _corridor_shell(r, 0, 80, rng)
    r.turn("Hammer Bend Back", 30, 360, rails=True)
    r.along(side_hammer, [90], i0=2)
    _corridor_shell(r, 0, 80, rng)
    road(r, "Last Crushers", 280, w=80, cp=True)
    r.along(crusher_v, [90, 200], i0=5)
    _corridor_shell(r, 0, 80, rng)
    road(r, "Hammer Exit", 160, w=80, dy=15, boosts=2, every=50, arrows_at=(80,))
    r.log("end")
    return ["Launch Runway", "Giant Ramp", "High Line", "Low Road", "Hammer Corridor", "Hammer Bend"]


def _axes(z):
    z = unit(z)
    x = unit(cross(UP, z))
    return (x, cross(z, x), z)


def _corridor_shell(r, L, w, rng):
    """The corridor round the road just laid: steel ribs every 90 studs with lamps, side walls with windows,
    gears turning outside."""
    b = r.b
    pts, ws, _ = r.last
    cum = [0.0]
    for a_, c_ in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))
    d = 20.0
    k = 0
    while d < cum[-1] - 10:
        i = next(i for i in range(len(cum) - 1) if cum[i + 1] >= d)
        p = R2.lerp3(pts[i], pts[i + 1], (d - cum[i]) / max(cum[i + 1] - cum[i], 1e-6))
        f = RT.flat(sub(pts[i + 1], pts[i]))
        gantry(b, p, f, w + 16, h=78, lamps=(k % 2 == 0))
        rt = right_of(f)
        fr = deck_frame(p, f)
        for s in (-1, 1):
            q = add(p, add(mul(rt, s * (w / 2 + 26)), (0, 30, 0)))
            Pt(b, "CorridorWall", CF(q, fr.x, fr.y, fr.z), (2, 60, 80), STEEL_DK, "DiamondPlate", b.scenery)
            Pt(b, "CorridorWindow", CF(add(q, mul(rt, -s * 1.2)), fr.x, fr.y, fr.z), (0.4, 14, 50), ACC["hammer"], "Neon",
               b.scenery, transp=0.4)
        if k % 4 == 1:
            spark_gear(b, p, f, (w / 2 + 70) * (1 if k % 8 == 1 else -1), R=55, col=STEEL_LT, spin=0.08)
        d += 90.0
        k += 1


# ===================================================================== moving road sections
def tilt_deck(r, label, L, w, amp_deg=8.0, period=4.2, phase=0.0):
    """A road section rolling side to side about its centre line (it carries the car)."""
    b = r.b
    f = r.f
    c = add(r.p, mul(f, L / 2 + 2))
    yaw = math.atan2(-f[2], f[0])
    m = R2.rotor(b, label.replace(" ", ""), CF(c) * rot_y(yaw), (1, 0, 0), "swing", amp=math.radians(amp_deg),
                 period=period, phase=phase, near=L)
    fr = deck_frame(c, f)
    Pt(b, "MovingDeck", CF(add(c, (0, -2, 0)), fr.x, fr.y, fr.z), (w, 4, L), b.skin.top, "SmoothPlastic", m, collide=True,
       attrs={"ClockDeck": True})
    rt = right_of(f)
    for s in (-1, 1):
        e = Pt(b, "HazardEdge", CF(add(c, add(mul(rt, s * (w / 2 - 1.5)), (0, 0.06, 0))), fr.x, fr.y, fr.z), (3, 0.12, L), HAZ_K,
               "SmoothPlastic", m)
        SC.tex(b, e, "checker", tile=3.0, color=HAZ_Y)
        lamp(b, add(c, add(mul(rt, s * (w / 2 + 3)), add(mul(f, -L / 2), (0, 3, 0)))), col=(255, 180, 30))
    for k in (-1, 1):
        cyl(b, "TiltAxle", add(c, add(mul(f, k * (L / 2 + 1)), (0, -6, 0))), 8, 10, STEEL_LT, "Metal", b.scenery, axis=f)
        stripe_box(b, "AxleHousing", CF(add(c, add(mul(f, k * (L / 2 + 4)), (0, -14, 0))), fr.x, fr.y, fr.z), (14, 14, 8))
    for k in (-1, 1):
        q = add(c, add(mul(rt, k * w * 0.35), (0, -30, 0)))
        cyl(b, "TiltPiston", q, 50, 6, STEEL_LT, "Metal", b.scenery)
    R2._special_line(b, r.p, add(r.p, mul(f, L + 4)), 6)
    b.samples.append(c + (w,))
    r.p = add(r.p, mul(f, L + 4))
    return r


def retract_deck(r, label, L, w, period=3.4, phase=0.0, side=1):
    """A road section that slides sideways out of the way and back on a cycle: be on it while it is home."""
    b = r.b
    f = r.f
    rt = right_of(f)
    c = add(r.p, mul(f, L / 2 + 2))
    root = b.prop_root("Retract")
    rig = b.rig(root, "Slide", axis_frame(add(c, (0, -2, 0)), mul(rt, side)), w + 12, period, phase=phase,
                keys="0:0 0.55:0 0.63:1 0.82:1 0.92:0", name="Retract")
    fr = deck_frame(c, f)
    Pt(b, "RetractDeck", CF(add(c, (0, -2, 0)), fr.x, fr.y, fr.z), (w, 4, L), b.skin.top, "SmoothPlastic", rig, collide=True)
    stripe_box(b, "RetractEdge", CF(add(c, (0, 0.07, 0)), fr.x, fr.y, fr.z), (w - 4, 0.12, 6), parent=rig)
    for k in (-1, 1):
        q = add(c, add(mul(f, k * (L / 2 - 6)), mul(rt, side * (w / 2 + 30))))
        cyl(b, "RetractRam", add(q, (0, -2, 0)), 50, 6, STEEL_LT, "Metal", b.scenery, axis=rt)
        Pt(b, "RamHousing", CF(add(q, add(mul(rt, side * 26), (0, -2, 0))), fr.x, fr.y, fr.z), (14, 12, 14), STEEL, "Metal",
           b.scenery)
        lamp(b, add(c, add(mul(f, k * (L / 2 + 1)), add(mul(rt, -side * (w / 2 + 3)), (0, 3, 0)))))
    for p_ in (r.p, add(r.p, mul(f, L / 2 + 2)), add(r.p, mul(f, L + 4))):
        b.path.append((p_[0], p_[1] + CAR_UP, p_[2], "r"))
    b.samples.append(c + (w,))
    r.p = add(r.p, mul(f, L + 4))
    return r


# ===================================================================== 3. the collapsing highway
def slot2(r, sk, rng):
    b = r.b
    sk.title = "Collapsing Highway"
    b.gate_label = "STAGE 2"
    accent(b, ACC["highway"])
    road(r, "Highway On-Ramp", 300, w=80, dy=120, boosts=2, arrows_at=(150,))
    road(r, "Highway", 160, w=70, cp=True)
    tilt_deck(r, "Tilting Span", 160, 70, phase=0.0)
    road(r, "Highway Pier", 70, w=70)
    retract_deck(r, "Retracting Span", 140, 70, phase=0.2)
    road(r, "Highway Pier 2", 70, w=70)
    R2.sink_board(r, "Falling Span", 240, 70, cell=40.0, cols=(ACC["highway"], mix(ACC["highway"], (0, 0, 0), 0.4)),
                  mats=("SmoothPlastic", "SmoothPlastic"), delay=0.35, rate=90.0)
    road(r, "Highway Pier 3", 80, w=70, cp=True)
    r.turn("Highway Curve", 60, 460, rails=True)
    R2.lay_strips(r, 60, 420, every=90, lanes=2)
    tilt_deck(r, "Rolling Span", 160, 70, amp_deg=10, period=3.6, phase=0.5)
    road(r, "Junction", 160, w=200, cp=True, arrows_at=(80,))
    junction = (r.p, r.f)
    # ---- the central path: moving platforms
    R2.turnstile(r, "Spin Gate", 150, w=50, period=2.0, phase=0.0, col=STEEL)
    road(r, "Central Pier", 70, w=60)
    R2.gear_bridge(r, "Turntable", 90, 4.5, col=ACC["highway"], teeth_col=STEEL)
    road(r, "Central Pier 2", 70, w=60)
    R2.turnstile(r, "Spin Gate 2", 150, w=50, period=1.8, phase=0.3, col=STEEL)
    road(r, "Merge Deck", 520, w=200, cp=True, arrows_at=(100, 400))
    merge0 = sub(r.p, mul(r.f, 520))
    # ---- the narrow side path: faster, harder jumps (right)
    p0, f = junction
    rt = right_of(f)
    al = Alt(r, add(p0, mul(rt, 70)), f, 26, B=260.0)
    accent(b, (255, 255, 255))
    al.o.plat("Side Rail", 100, 26)
    al.o.kick(0, side=10)
    al.o.plat("Side Hop", 90, 22, [(O.saw, 0.5)])
    al.o.drop(26, side=-10)
    al.o.plat("Side Beam", 110, 18)
    gap = dot(sub(merge0, al.r.p), f)
    lo, hi = al.o.pad_range(26)
    if gap - hi > 40:
        al.o.plat("Side Run", gap - (lo + hi) / 2 - 40, 20)
    al.o.pad(26, side=-70)
    al.done()
    # ---- the lower route: down onto unstable platforms, a shortcut back up (left)
    al = Alt(r, add(p0, mul(rt, -70)), f, 60, B=230.0)
    accent(b, (255, 150, 60))
    al.o.plat("Low Lane", 60, 60)
    al.o.drop(70, side=-30)
    al.o.plat("Shaky Deck", 0, 60)
    R2.sink_board(al.r, "Shaky Tiles", 200, 60, cell=40.0, cols=((200, 120, 60), (120, 70, 40)), mats=("SmoothPlastic", "SmoothPlastic"),
                  delay=0.4, rate=80.0)
    al.o.plat("Low Ledge", 80, 60)
    gap = dot(sub(merge0, al.r.p), f)
    lo, hi = al.o.pad_range(merge0[1] - al.r.p[1])
    if gap - hi > 40:
        al.o.plat("Low Run", gap - (lo + hi) / 2 - 20, 50)
    al.o.pad(merge0[1] - al.r.p[1], side=100)
    al.done()
    accent(b, ACC["highway"])
    r.turn("Off-Ramp Curve", -120, 460, dy=-60, rails=True)
    R2.lay_strips(r, 80, 900, every=110, lanes=2)
    tilt_deck(r, "Last Tilt", 150, 70, amp_deg=8, period=3.2, phase=0.25)
    retract_deck(r, "Last Retract", 130, 70, phase=0.6, side=-1)
    road(r, "Off-Ramp", 300, w=80, dy=-60, boosts=2, cp=True)
    r.turn("Exit Curve", 60, 460, rails=True)
    # ---- back across to the centre line on a last diagonal of collapsing spans
    r.turn("Return Curve", -50, 400, rails=True)
    tilt_deck(r, "Return Tilt", 150, 70, amp_deg=9, period=3.4, phase=0.1)
    road(r, "Return Pier", 64, w=70)
    R2.sink_board(r, "Return Fall", 200, 70, cell=40.0, cols=(ACC["highway"], mix(ACC["highway"], (0, 0, 0), 0.4)),
                  mats=("SmoothPlastic", "SmoothPlastic"), delay=0.3, rate=95.0)
    road(r, "Return Pier 2", 26, w=70, cp=True)
    retract_deck(r, "Return Retract", 130, 70, phase=0.35, side=1)
    road(r, "Return Pier 3", 60, w=70)
    r.turn("Return Straighten", 50, 400, rails=True)
    R2.lay_strips(r, 60, 300, every=80, lanes=2)
    r.log("end")
    return ["Collapsing Highway", "Tilting Span", "Retracting Span", "Falling Span", "Three-Way Split"]


# ===================================================================== 4. the enormous loop
def giant_loop(b, st, R=100.0, w=60.0, dz=84.0):
    """A vertical loop (WallRide: the car holds the surface all the way round), shifting dz sideways so it comes out
    beside where it went in. Built along +X at st; st moves to the exit."""
    import parkour as V2
    cx, cy, z0 = st.x, st.y + R, st.z
    n = 72
    pts = []
    for i in range(n + 1):
        ph = TAU * i / n
        p = (cx + R * math.sin(ph), cy - R * math.cos(ph), z0 + dz * V2.ease5(i / n))
        pts.append((p, (-math.sin(ph), math.cos(ph), 0.0)))
    m = b.model("GiantLoop", b.roads, {"WallRide": True})
    V2.ribbon(b, pts, w, m, rails=True, color=ACC["loop"])
    for p, nrm in pts[::3]:
        b.path.append((p[0] + nrm[0] * CAR_UP, p[1] + nrm[1] * CAR_UP, p[2], "s"))
    # thick steel ring frames on both faces, lit
    for zz in (z0 - w / 2 - 6, z0 + dz + w / 2 + 6):
        ringz(b, (cx, cy, zz), R + 10, STEEL, "Metal", th=8.0, axis=(0, 0, 1), parent=b.scenery, name="LoopFrame")
        ringz(b, (cx, cy, zz), R + 15, ACC["loop"], "Neon", th=1.4, axis=(0, 0, 1), parent=b.scenery, name="LoopGlow")
    for s in (-1, 1):
        for zz in (z0 - w / 2 - 14, z0 + dz + w / 2 + 14):
            cyl(b, "LoopLeg", (cx + s * (R + 30), cy - R * 0.5 - 60, zz), R + 120, 14, STEEL_DK, "Metal", b.scenery)
    st.x = cx
    st.z = z0 + dz
    b.samples.append((cx, st.y, z0 + dz / 2, w + dz))
    return (cx, cy, z0 + dz / 2)


def _turn_disp(f, deg, R):
    """Where a turn of deg (left > 0) on radius R moves the turtle, and its new heading."""
    a = math.radians(abs(deg))
    side = RT.left_of(f) if deg > 0 else right_of(f)
    d = add(mul(f, R * math.sin(a)), mul(side, R * (1 - math.cos(a))))
    return d, _yaw(f, deg)


def _yaw(f, deg):
    a = math.radians(deg)
    # (left = -Z for +X: a left turn swings the heading from +X towards -Z)
    c, s_ = math.cos(a), math.sin(a)
    lf = RT.left_of(f)
    return unit(add(mul(f, c), mul(lf, s_)))


def slot3(r, sk, rng):
    b = r.b
    sk.title = "The Loop"
    b.gate_label = "STAGE 3"
    accent(b, ACC["loop"])
    road(r, "Loop Approach", 200, w=70, cp=True, arrows_at=(100,))
    road(r, "Fork", 140, w=240, cp=True, arrows_at=(70,))
    fork_end, f = r.p, r.f
    rt = right_of(f)
    E = 640.0
    road(r, "Acceleration Ramp", E, w=60, dy=-90, boosts=1, every=50, arrows_at=(80, 560))
    hole = {}

    def build(b_, st):
        hole["c"] = giant_loop(b_, st, R=100.0, w=60.0, dz=84.0)
    r.local("Giant Loop", build)
    hc = hole["c"]
    cx = hc[0]
    road(r, "Loop Exit Lane", 205, w=60)  # (clear of the big ring where it rises past the road level)
    PW = 400.0
    r.w = PW  # (the plaza opens out at once: a broad platform, not a widening road)
    road(r, "Loop Plaza", 420, w=PW, cp=True, arrows_at=(60, 300))
    plaza0 = sub(r.p, mul(r.f, 420))
    pz = plaza0[2]
    # ---- the bypass (left), for a car that would rather not loop: round the loop's legs and onto the plaza
    al = Alt(r, add(fork_end, mul(rt, -60)), f, 40, B=230.0)
    accent(b, (200, 160, 255))
    al.r.straight("Bypass", 60, lead=5.0, rails=True, line=False)
    al.r.turn("Bypass Out", 15, 300, rails=True, line=False)
    al.r.turn("Bypass Round", -15, 300, rails=True, line=False)
    al.r.straight("Bypass Dive", 220, dy=-90, lead=40.0, rails=True, line=False)
    al.r.straight("Bypass Run", dot(sub(plaza0, al.r.p), f), lead=5.0, rails=True, line=False)
    al.done()
    # ---- the shortcut: it stays high while the main road dives, swings left and back round onto a line at 45
    # degrees through the loop's hole, and a flat kicker throws the car right through the middle of the loop and
    # over the exit lane onto a landing pad beside the plaza
    D, Lk, deg = 150.0, 36.0, 6.0
    p0 = add(fork_end, mul(rt, -104))
    A, R1, R2_ = 45.0, 200.0, 150.0
    d1 = _turn_disp(f, A, R1)[0]
    u1 = _yaw(f, A)
    d2 = _turn_disp(u1, -(A + 45.0), R2_)[0]
    u2 = _yaw(u1, -(A + 45.0))
    n2 = right_of(u2)
    hcf = (hc[0], p0[1], hc[2])
    base = add(add(p0, d1), d2)
    s_len = -dot(sub(base, hcf), n2) / dot(u1, n2)
    at2 = add(base, mul(u1, s_len))
    Lp = -dot(sub(at2, hcf), u2) - D - Lk
    assert s_len > 20 and Lp > 60, (s_len, Lp)
    al = Alt(r, p0, f, 32, B=330.0)
    accent(b, (255, 120, 255))
    al.r.turn("Shortcut Swing", A, R1, dy=15, rails=True, line=False)
    al.r.straight("Shortcut Spur", s_len, lead=5.0, rails=True, line=False)
    al.r.turn("Shortcut Swing Back", -(A + 45.0), R2_, dy=15, rails=True, line=False)
    al.r.straight("Shortcut Run", Lp, lead=5.0, rails=True, line=False)
    R2.lay_strips(al.r, 20, Lp - 10, every=40, lanes=1)
    lip, dvec = R2.kicker(al.r, "Shortcut Kicker", deg, L=Lk, w=32, rails=False)
    off = dot(sub(lip, hcf), n2)
    assert abs(off) < 3, off
    H = 330.0 * math.cos(math.radians(deg))
    V = 330.0 * math.sin(math.radians(deg))
    # the landing pad beside the plaza (it joins the plaza's right side), and where the fastest car comes down
    lz = 200.0
    lp0 = (cx + 60.0, plaza0[1], pz - 84.0 + lz)
    landing(b, lp0, f, 120, plaza0[0] - lp0[0])
    t = (V + math.sqrt(V * V + 2 * G * (lip[1] - plaza0[1]))) / G
    top = add(add(lip, mul(u2, H * t)), (0, plaza0[1] - lip[1], 0))
    b.jumps.append(("kick", lip, top, H, V))
    import parkour as V2
    # (the flight through the hole: inside the ring for the slowest and the fastest car)
    for v in (0.8 * H, H):
        for k in range(60):
            tt = k * 0.02
            q = add(add(lip, mul(u2, v * tt)), (0, V * v / H * tt - G * tt * tt / 2 + CAR_UP, 0))
            rr = math.hypot(q[0] - cx, q[1] - hc[1])
            ph = math.atan2(q[0] - cx, -(q[1] - hc[1])) % TAU
            zr = hc[2] - 42.0 + 84.0 * V2.ease5(ph / TAU)
            assert not (abs(q[2] - zr) < 38 and rr > 84), ("hits the loop", v, rr, q[2] - zr)
    al.done()
    # ---- the lower recovery deck under the shortcut's flight: a pad throws a car that came up short back up
    al = Alt(r, (cx - 60.0, plaza0[1] - 120.0, pz - 84.0 + 260.0), f, 200, B=230.0)
    accent(b, (140, 90, 200))
    al.o.plat("Recovery Deck", 190, 200)
    al.o.pad(120.0, side=0)
    al.done()
    accent(b, ACC["loop"])
    road(r, "Loop Exit Climb", 400, w=70, dy=90, boosts=2, every=70, cp=True)
    # (back across onto the centre line: the loop moved the road over by its own width)
    r.turn("Loop Run-Out", 26, 400, rails=True)
    R2.lay_strips(r, 30, 150, every=60, lanes=2)
    r.turn("Loop Run-Out 2", -26, 400, rails=True)
    air_sequence(r, rng)
    r.log("end")
    return ["Acceleration Ramp", "Giant Loop", "Bypass", "Hole Shortcut", "Recovery Deck", "Sky Ramps", "Split Landing",
            "Hidden Ledge"]


def last_len(r):
    pts = r.last[0]
    return sum(math.dist(a_, c_) for a_, c_ in zip(pts, pts[1:]))


def air_sequence(r, rng):
    """6. The airborne ramp sequence: a ramp up onto an elevated deck, a longer gap over turning beams onto a split
    landing (the main runway or a lower deck off to the right), then the main road's beam walk while the right deck's
    precision hops lead to a hidden ledge that cuts the corner and drops back in."""
    b = r.b
    col = ACC["air"]
    accent(b, col)
    road(r, "Air Strip", 160, w=80, dy=60, boosts=3, every=35, cp=True, arrows_at=(80, 150))
    for d in (50, 120):
        gantry(b, r.ahead(d - 160), r.f, 80, h=40)
    R2.ramp_jump(r, "Sky Ramp", deg=24, drop=20, w_land=90, slope=2, land_min=280, cp=True)
    kind, lip, tgt, H, V = [j for j in b.jumps if j[0] == "ramp"][-1]
    Lr = last_len(r)
    r.along(sweep_arm, [Lr - 60], i0=0)
    road(r, "Sky Deck", 70, w=80, boosts=3, every=30, arrows_at=(40,))
    f = r.f
    rt = right_of(f)

    R2.ramp_jump(r, "Long Gap", deg=22, drop=60, w_land=70, slope=3, land_min=330, cp=True)
    kind, lip, tgt, H, V = [j for j in b.jumps if j[0] == "ramp"][-1]
    Lr = last_len(r)
    land0 = sub(r.p, mul(f, Lr))
    # ---- the main road: the beam walk, turning beams sweeping a narrower road
    road(r, "Beam Walk", 200, w=70, cp=True)
    r.along(sweep_arm, [50, 150], i0=1)
    r.along(punch, [100], i0=2)
    r.w = 160.0  # (the ring run opens out at once, so the hidden ledge's drop has the whole width to land on)
    ring_run0 = r.p
    road(r, "Ring Run", 240, w=160, dy=58, boosts=3, every=60, cp=True, arrows_at=(60, 210))
    # ---- the split landing: steer right in the air and come down on the lower deck
    dz = 120.0
    low = 30.0
    tdir = None
    for _ in range(8):
        # aim the recorded flight at the middle of the lower deck
        tgt_r = add(add(tgt, mul(rt, dz)), (0, -low - (tgt[1] - land0[1]), 0)) if tdir is None else tdir
        hv = RT.flat(sub(tgt_r, lip))
        d3 = unit((hv[0] * H, V, hv[2] * H))
        ys = land0[1] - low
        ps = [R2.fly(lip, mul(d3, v), lambda p, ys=ys: ys)[0] for v in (0.9 * math.hypot(H, V), math.hypot(H, V))]
        mid = R2.lerp3(ps[0], ps[1], 0.5)
        tdir = add(tgt_r, mul(sub(add(add(tgt, mul(rt, dz)), (0, 0, 0)), mid), 0.0))
        break
    near = min(dot(sub(q, lip), f) for q in ps)
    far = max(dot(sub(q, lip), f) for q in ps)
    side = dot(sub(ps[1], lip), rt)
    a = add(add(lip, mul(f, near - 50)), add(mul(rt, side), (0, ys - lip[1], 0)))
    al = Alt(r, a, f, 60, B=300.0)
    accent(b, (150, 255, 170))
    al.o.plat("Right Landing", far - near + 70, 60)
    b.jumps.append(("ramp", lip, ps[1], H, V))
    al.o.kick(0, side=0, label="Precision Hop")
    al.o.plat("Hidden Ledge", 0, 22)
    # the hidden ledge runs on past the beam walk, then drops back onto the ring run
    to = dot(sub(ring_run0, al.r.p), f)
    Lh = max(60.0, to)
    al.r.straight("Hidden Ledge", Lh, dy=ring_run0[1] + 90.0 - al.r.p[1], lead=60.0, rails=True, line=False)
    for d in range(40, int(Lh), 80):
        lamp(b, add(al.r.p, add(mul(f, -d), add(mul(rt, 22), (0, 3, 0)))), col=(150, 255, 170), pulse=1.0)
    al.o.drop(45.0, side=dot(sub(ring_run0, al.r.p), rt) * 0.9)
    al.done()
    accent(b, col)
    R2.ramp_jump(r, "Last Air", deg=18, drop=30, w_land=90, slope=3, land_min=260, cp=True)
    kind, lip, tgt, H, V = [j for j in b.jumps if j[0] == "ramp"][-1]


# ===================================================================== 5. the giant crusher machine
def crusher_plates(b, c, w, i, period=3.2, L=46.0, H=38.0):
    """A pair of enormous plates slamming together across the road from both sides (CRUSHED); pass while open."""
    x, y, z = c
    T = w / 2
    for s_ in (-1, 1):
        home = (x, y + H / 2 + 0.5, z + s_ * (w / 2 + T / 2 + 3))
        root = b.prop_root("CrusherPlate")
        rig = b.rig(root, "Slide", axis_frame(home, (0, 0, -s_)), w / 2 + 3, period, phase=(i * 0.29) % 1,
                    keys="0:0 0.45:0 0.53:1 0.64:1 0.9:0", name="Plate")
        Pt(b, "CrusherPlate", CF(home), (L, H, T), STEEL, "DiamondPlate", rig, query=True, attrs={"ObbyHazard": "Crush"})
        stripe_box(b, "PlateFace", CF(add(home, (0, 0, -s_ * (T / 2 + 0.3)))), (L + 0.4, H + 0.4, 0.6), parent=rig, tile=5.0)
        for k in (-1, 1):
            cyl(b, "PlateRod", add(home, (k * 12, 0, s_ * (T / 2 + 20))), 40, 7, STEEL_LT, "Metal", rig, axis=(0, 0, 1),
                refl=0.3)
        hz = (x, y + H / 2 + 2, z + s_ * (w / 2 + T + 30))
        Pt(b, "PlateHousing", CF(hz), (L + 16, H + 20, 22), STEEL_DK, "Metal", b.scenery, collide=True)
        stripe_box(b, "HousingBand", CF(add(hz, (0, H / 2 + 6, 0))), (L + 17, 3, 23))
        lamp(b, add(hz, (0, H / 2 + 12, 0)), col=(255, 200, 40), pulse=period / 2)
    impact_zone(b, c, (1, 0, 0), w, L)


def lane_walls(b, c, w, i, period=2.4, H=26.0):
    """Three lane walls rising out of the floor in turn (one lane at a time is shut)."""
    x, y, z = c
    for k in range(3):
        zz = z - w / 2 + w * (k + 0.5) / 3
        rest = (x, y - H / 2 - 4.5, zz)
        root = b.prop_root("LaneWall")
        rig = b.rig(root, "Slide", axis_frame(rest, (0, 1, 0)), H + 4.5, period, phase=(k / 3.0 + i * 0.17) % 1,
                    keys="0:0 0.5:0 0.58:1 0.82:1 0.9:0", name="Rise")
        Pt(b, "LaneWall", CF(rest), (8, H, w / 3 - 2), ACC["crusher"], "SmoothPlastic", rig, query=True,
           attrs={"ObbyHazard": "Knock"})
        stripe_box(b, "WallTop", CF(add(rest, (0, H / 2 + 0.3, 0))), (8.4, 0.6, w / 3 - 1.6), parent=rig)
        lamp(b, (x, y + 44, zz), col=(255, 60, 40), pulse=period)
    Pt(b, "WallBeam", CF((x, y + 48, z)), (6, 6, w + 30), STEEL, "Metal", b.scenery)
    for s_ in (-1, 1):
        Pt(b, "WallPost", CF((x, y + 24, z + s_ * (w / 2 + 12))), (6, 48, 6), STEEL, "Metal", b.scenery, collide=True)
    Pt(b, "WallSlot", CF((x, y + 0.08, z)), (9, 0.12, w - 6), HAZ_K, "SmoothPlastic", b.scenery)


def grinder(b, c, w, i, d=22.0):
    """A spiked drum spinning across two of the three lanes (SHREDDED): take the open lane."""
    x, y, z = c
    k = i % 3
    open_z = z - w / 2 + w * (k + 0.5) / 3
    span = w * 2 / 3 - 2
    zc = z + (w / 2 - span / 2 - 1) * (1 if k == 0 else -1) if k != 1 else None
    parts = [zc] if k != 1 else [z - w / 3, z + w / 3]
    spanv = span if k != 1 else w / 3 - 2
    for zz in parts:
        hub = (x, y + d / 2 + 0.5, zz)
        root = b.prop_root("Grinder")
        rig = b.rig(root, "Spin", axis_frame(hub, (0, 0, 1)), 1.4 * (1 if i % 2 else -1), 1, name="Grind")
        cyl(b, "GrinderDrum", hub, spanv, d, (150, 150, 160), "DiamondPlate", rig, axis=(0, 0, 1), query=True,
            attrs={"ObbyHazard": "Shred"})
        for j in range(8):
            a = TAU * j / 8
            dd = (math.cos(a), math.sin(a), 0.0)
            Pt(b, "GrinderTooth", CF(add(hub, mul(dd, d / 2 + 1.5)), dd, (0, 0, 1), cross(dd, (0, 0, 1))), (4, spanv - 2, 4),
               (230, 60, 50), "Metal", rig)
        for s_ in (-1, 1):
            Pt(b, "GrinderMount", CF(add(hub, (0, 0, s_ * (spanv / 2 + 2)))), (12, d + 6, 3), STEEL_DK, "Metal", b.scenery)
    Pt(b, "OpenLane", CF((x - 20, y + 0.1, open_z)), (14, 0.12, w / 3 - 8), (90, 255, 140), "Neon", b.scenery)


def roller_bed(b, c, w, i):
    """Rollers set flush in the conveyor, spinning (they show which way the floor pulls)."""
    x, y, z = c
    root = b.prop_root("Roller")
    for k in range(3):
        hub = (x + k * 9 - 9, y - 3.2, z)
        rig = b.rig(root, "Spin", axis_frame(hub, (0, 0, 1)), -0.8, 1, name="Roll")
        cyl(b, "Roller", hub, w - 8, 6, STEEL_LT, "Metal", rig, axis=(0, 0, 1), refl=0.3)


def hall(b, p0, p1, f, half, h, col, rng):
    """The machine's hall round the road from p0 to p1: walls with lit windows, roof girders, lamps, chains, gears."""
    rt = right_of(f)
    fr = deck_frame(p0, f)
    L = math.dist((p0[0], 0, p0[2]), (p1[0], 0, p1[2]))
    y = min(p0[1], p1[1])
    d = 0.0
    k = 0
    while d < L:
        seg = min(60.0, L - d)
        c = add(p0, mul(f, d + seg / 2))
        c = (c[0], y, c[2])
        for s_ in (-1, 1):
            q = add(c, add(mul(rt, s_ * half), (0, h / 2 - 40, 0)))
            Pt(b, "HallWall", CF(q, fr.x, fr.y, fr.z), (3, h + 80, seg), STEEL_DK, "DiamondPlate", b.scenery)
            Pt(b, "HallWindow", CF(add(q, add(mul(rt, -s_ * 1.7), (0, 30, 0))), fr.x, fr.y, fr.z), (0.4, 16, seg - 14), col,
               "Neon", b.scenery, transp=0.35)
            stripe_box(b, "HallBand", CF(add(q, add(mul(rt, -s_ * 1.8), (0, -10, 0))), fr.x, fr.y, fr.z), (0.4, 5, seg))
        if k % 1 == 0:
            g = add(c, (0, h, 0))
            Pt(b, "RoofGirder", CF(g, fr.x, fr.y, fr.z), (2 * half + 10, 10, 8), STEEL, "Metal", b.scenery)
            stripe_box(b, "GirderStripe", CF(add(g, (0, -5.4, 0)), fr.x, fr.y, fr.z), (2 * half + 6, 0.8, 8.4))
            if k % 2 == 0:
                for s_ in (-1, 1):
                    q = add(g, add(mul(rt, s_ * half * 0.5), (0, -10, 0)))
                    lamp(b, q, col=col, d=4.0, pulse=2.0 + k % 3)
                    if k % 4 == 0:
                        cyl(b, "HangChain", add(q, (0, -20, 0)), 36, 1.2, STEEL_LT, "Metal", b.scenery)
                        Pt(b, "HangHook", CF(add(q, (0, -40, 0))), (6, 6, 2), HAZ_Y, "Metal", b.scenery)
        if k % 2 == 0:
            Pt(b, "RoofSpine", CF(add(c, (0, h + 8, 0)), fr.x, fr.y, fr.z), (16, 4, seg), STEEL_DK, "Metal", b.scenery)
        if k % 5 == 2:
            s_ = 1 if k % 10 == 2 else -1
            big_gear(b, add(c, add(mul(rt, s_ * (half + 14)), (0, h * 0.45, 0))), 44, rt, STEEL_LT, spin=0.07 * s_)
        d += 60.0
        k += 1


def door_frame(b, c, f, half, h, col):
    """A huge doorway into (or out of) the machine: a stepped steel frame with a striped lintel and lamps."""
    rt = right_of(f)
    fr = deck_frame(c, f)
    for s_ in (-1, 1):
        q = add(c, add(mul(rt, s_ * (half + 6)), (0, h / 2 - 40, 0)))
        Pt(b, "DoorPillar", CF(q, fr.x, fr.y, fr.z), (16, h + 80, 20), STEEL, "Metal", b.scenery)
        stripe_box(b, "PillarStripe", CF(add(q, add(mul(rt, -s_ * 8.2), (0, 20, 0))), fr.x, fr.y, fr.z), (0.4, h + 20, 20))
    Pt(b, "DoorLintel", CF(add(c, (0, h + 10, 0)), fr.x, fr.y, fr.z), (2 * half + 44, 24, 22), STEEL, "Metal", b.scenery)
    stripe_box(b, "LintelStripe", CF(add(c, (0, h - 2.4, 0)), fr.x, fr.y, fr.z), (2 * half + 40, 0.8, 22.4))
    for k in range(5):
        lamp(b, add(c, add(mul(rt, (k - 2) * half * 0.4), (0, h + 24, 0))), col=col, d=6.0, pulse=1.0 + k * 0.2)


def slot4(r, sk, rng):
    b = r.b
    sk.title = "Crusher Works"
    b.gate_label = "STAGE 4"
    col = ACC["crusher"]
    accent(b, col)
    W = 90.0
    road(r, "Works Approach", 260, w=W, cp=True, boosts=2, every=60, arrows_at=(130,))
    p_in, f = r.p, r.f
    # ---- inside the machine
    road(r, "Crusher Plates", 380, w=W, cp=True)
    r.along(crusher_plates, [110, 210, 310], i0=0)
    road(r, "Plates Out", 60, w=W)
    road(r, "Lane Walls", 330, w=W, cp=True)
    r.along(lane_walls, [90, 170, 250], i0=0)
    retract_deck(r, "Shift Floor", 110, W, period=3.6, phase=0.1, side=1)
    road(r, "Floor Pier", 50, w=W)
    retract_deck(r, "Shift Floor 2", 110, W, period=3.6, phase=0.55, side=-1)
    road(r, "Roller Pier", 60, w=W, cp=True)
    R2.belt_road(r, "Roller Bed", 300, 45.0, direction="back", w=W)
    r.along(grinder, [70, 150, 230], i0=0)
    r.along(roller_bed, [30, 110, 190, 270], i0=0)
    road(r, "Piston Hall", 420, w=W, cp=True)
    pist = [(punch, 80, 0), (O.pusher, 140, 1), (punch, 190, 3), (crusher_v, 260, 2), (O.pusher, 320, 2), (punch, 370, 5)]
    for fn, d, k in pist:
        r.along(fn, [d], i0=k)
    p_out = r.p
    accent(b, (255, 235, 140))
    road(r, "Exit Tunnel", 240, w=80, boosts=3, every=40, arrows_at=(120, 220))
    p_tun = r.p
    hall(b, p_in, p_out, f, W / 2 + 110, 130.0, col, rng)
    door_frame(b, p_in, f, W / 2 + 110, 130.0, col)
    door_frame(b, p_out, f, W / 2 + 110, 130.0, col)
    # the exit tunnel: a tight lit tube of rings
    d = 10.0
    rt = right_of(f)
    while d < 240:
        c = add(p_out, mul(f, d))
        fr = deck_frame(c, f)
        for s_ in (-1, 1):
            Pt(b, "TunnelWall", CF(add(c, add(mul(rt, s_ * 50), (0, 22, 0))), fr.x, fr.y, fr.z), (3, 50, 18), STEEL_DK,
               "DiamondPlate", b.scenery)
        Pt(b, "TunnelRoof", CF(add(c, (0, 48, 0)), fr.x, fr.y, fr.z), (106, 3, 18), STEEL_DK, "DiamondPlate", b.scenery)
        Pt(b, "TunnelLight", CF(add(c, (0, 46.2, 0)), fr.x, fr.y, fr.z), (70, 0.4, 4), (255, 240, 180), "Neon", b.scenery)
        d += 24.0
    door_frame(b, p_tun, f, 52, 50.0, (255, 235, 140))
    accent(b, col)
    R2.ramp_jump(r, "Machine Launch", deg=20, drop=40, w_land=110, slope=4, land_min=360, cp=True)
    kind, lip, tgt, H, V = [j for j in b.jumps if j[0] == "ramp"][-1]
    road(r, "Works Run-Out", 200, w=90, boosts=2, every=60)
    # ---- the magnet crane: it picks the car up off the loading bay and swings it over the void
    road(r, "Loading Bay", 140, w=70, cp=True, arrows_at=(60,))
    crane_transfer(r, "Magnet Crane", 520, dy=40, turn=0, land_L=220, w_land=80, cp=True)
    # ---- the press line: a fast belt under a row of presses
    R2.belt_road(r, "Press Line", 580, 60.0, direction="along", w=80, cp=False)
    r.along(crusher_v, [90, 200, 310, 420, 520], i0=3)
    _corridor_shell(r, 0, 80, rng)
    road(r, "Works Exit", 200, w=80, dy=12, boosts=2, every=60, cp=True)
    r.log("end")
    return ["Crusher Plates", "Lane Walls", "Shift Floor", "Roller Bed", "Piston Hall", "Exit Tunnel", "Machine Launch",
            "Magnet Crane", "Press Line"]


def crane_head(b, head, home):
    cyl(b, "MagnetDisc", home, 6, 34, HAZ_Y, "Metal", head, refl=0.2)
    stripe_box(b, "MagnetBand", CF(add(home, (0, 3.4, 0))), (24, 1, 24), parent=head)
    Pt(b, "HookBlock", CF(add(home, (0, 12, 0))), (14, 14, 14), STEEL, "Metal", head)
    for s_ in (-1, 1):
        cyl(b, "CraneCable", add(home, (s_ * 4, 50, 0)), 70, 1.4, STEEL_LT, "Metal", head)
    for k in range(10):
        a = TAU * k / 10
        ball(b, "MagnetGlow", add(home, (math.cos(a) * 15, -3.4, math.sin(a) * 15)), 3.0, (90, 220, 255), "Neon", head)


def crane_transfer(r, label, D, dy=0.0, turn=0.0, land_L=220.0, w_land=None, cp=False):
    """The game's magnet ride as a crane: drive under the magnet, it lifts the car, carries it D across and drops it
    over the next road. An overhead girder track shows its way."""
    b = r.b
    f = r.f
    p0 = r.p
    th = math.radians(turn)
    c, s_ = math.cos(th), math.sin(th)
    f2 = RT.flat((f[0] * c + f[2] * s_, 0.0, -f[0] * s_ + f[2] * c))
    mid = RT.flat(add(f, f2))
    zone = add(p0, add(mul(f, -24), (0, 9, 0)))
    A = add(p0, add(mul(f, -24), (0, 5, 0)))
    E = add(p0, add(mul(mid, D), (0, dy, 0)))
    Dp = add(E, (0, 7, 0))
    Bp = add(A, add(mul(f, D * 0.35), (0, 150, 0)))
    Cp = add(Dp, add(mul(f2, -D * 0.3), (0, 40, 0)))
    home = add(A, (0, 30, 0))
    fr = deck_frame(zone, f)
    R2.magnet_ride(b, label.replace(" ", ""), A, Bp, Cp, Dp, CF(zone, fr.x, fr.y, fr.z), (r.w - 6, 24, 44), home,
                   speed=200.0, out=170.0, perp=right_of(f), head_fn=crane_head)
    ringz(b, add(add(p0, mul(f, -24)), (0, 0.3, 0)), min(r.w / 2 - 4, 22), (90, 220, 255), "Neon", th=0.4,
          parent=b.scenery, name="CraneTarget")
    pts = [R2._bez(A, Bp, Cp, Dp, k / 24) for k in range(25)]
    for p in pts:
        b.path.append((p[0], p[1] + 1, p[2], "s"))
    # the girder track over the ride, on two towers
    ty = max(p[1] for p in pts) + 90
    for i in range(len(pts) - 1):
        a_, c_ = (pts[i][0], ty, pts[i][2]), (pts[i + 1][0], ty, pts[i + 1][2])
        dd = unit(sub(c_, a_))
        Pt(b, "CraneGirder", CF(R2.lerp3(a_, c_, 0.5), *_axes(dd)), (10, 12, math.dist(a_, c_) + 1), HAZ_Y, "Metal", b.scenery)
    for q in (pts[0], pts[-1]):
        rt = right_of(f)
        for k in (-1, 1):
            t = add((q[0], ty, q[2]), mul(rt, k * 60))
            cyl(b, "CraneTower", (t[0], (ty + Y0 - 500) / 2, t[2]), ty - (Y0 - 500), 12, STEEL_DK, "Metal", b.scenery)
        Pt(b, "CraneHead", CF((q[0], ty + 8, q[2]), *_axes(rt)), (14, 14, 130), STEEL, "Metal", b.scenery)
    r.p = E
    r.f = f2
    if w_land:
        r.w = w_land
    r.straight(label + " Drop Zone", land_L, lead=10.0, cp=cp)
    return r


# ===================================================================== 7. the rotating bridge complex
def bridge_deck(b, m, c, f, L, w, col):
    """A moving bridge deck in rotor m: coloured top, hazard edges, steel girders under it, end lamps."""
    fr = deck_frame(c, f)
    rt = right_of(f)
    Pt(b, "MovingDeck", CF(add(c, (0, -2, 0)), fr.x, fr.y, fr.z), (w, 4, L), col, "SmoothPlastic", m, collide=True,
       attrs={"ClockDeck": True})
    for s_ in (-1, 1):
        e_ = Pt(b, "HazardEdge", CF(add(c, add(mul(rt, s_ * (w / 2 - 1.5)), (0, 0.06, 0))), fr.x, fr.y, fr.z), (3, 0.12, L),
                HAZ_K, "SmoothPlastic", m)
        SC.tex(b, e_, "checker", tile=3.0, color=HAZ_Y)
        Pt(b, "BridgeGirder", CF(add(c, add(mul(rt, s_ * (w / 2 - 6)), (0, -9, 0))), fr.x, fr.y, fr.z), (5, 10, L - 4), STEEL,
           "Metal", m)
    for k in (-1, 1):
        Pt(b, "BridgeEnd", CF(add(c, add(mul(f, k * (L / 2 - 1)), (0, 0.1, 0))), fr.x, fr.y, fr.z), (w - 6, 0.2, 2),
           (255, 255, 255), "Neon", m)
    d = -L / 2 + 30
    while d < L / 2 - 20:
        Pt(b, "LaneDash", CF(add(c, add(mul(f, d), (0, 0.07, 0))), fr.x, fr.y, fr.z), (1.2, 0.14, 9), WHITE, "SmoothPlastic", m)
        d += 30


def motor(b, c, R=26.0, h=40.0, col=STEEL):
    """A huge drive motor under a pivot: drum, cooling fins, hazard band, a lamp."""
    cyl(b, "MotorDrum", add(c, (0, -h / 2 - 6, 0)), h, 2 * R, col, "Metal", b.scenery)
    for k in range(4):
        cyl(b, "MotorFin", add(c, (0, -12 - k * 8, 0)), 2, 2 * R + 6, STEEL_DK, "Metal", b.scenery)
    stripe_box(b, "MotorBand", CF(add(c, (0, -h - 8, 0))), (2 * R + 2, 4, 2 * R + 2))
    cyl(b, "MotorShaft", add(c, (0, -h - 120, 0)), 220, R * 0.7, STEEL_DK, "Metal", b.scenery)
    lamp(b, add(c, (0, -h - 2, R + 2)), col=(255, 80, 40), pulse=1.2)


def swing_span(r, label, L, w=50.0, period=4.0, ease=1.4, phase=0.0, step=math.pi, col=None):
    """A long bridge on a central pivot that turns about its middle (half a turn, or a quarter) on a beat: lined up
    with the road between turns."""
    b = r.b
    f = r.f
    c = add(r.p, mul(f, 3 + L / 2))
    m = R2.rotor(b, label.replace(" ", ""), CF(c) * RT.rot_y(math.atan2(-f[2], f[0])), (0, 1, 0), "tick", step=step,
                 period=period, ease=ease, phase=phase, near=L)
    bridge_deck(b, m, c, f, L, w, col or b.skin.top)
    cyl(b, "PivotCap", add(c, (0, 0.3, 0)), 0.6, 18, HAZ_Y, "Neon", m)
    motor(b, add(c, (0, -12, 0)))
    a0, a1 = add(r.p, mul(f, 3)), add(r.p, mul(f, 3 + L))
    R2._special_line(b, a0, a1, 8)
    b.samples.append(c + (L,))
    r.p = add(a1, mul(f, 3))
    return c


def seesaw(r, label, L, w=60.0, amp_deg=11.0, period=4.4, ease=1.0, hold=1.8, phase=0.0, col=None):
    """A bridge rocking about its middle: level for a moment between its tilts (cross while it is level)."""
    b = r.b
    f = r.f
    c = add(r.p, mul(f, 3 + L / 2))
    yaw = math.atan2(-f[2], f[0])
    m = R2.rotor(b, label.replace(" ", ""), CF(c) * RT.rot_y(yaw), (0, 0, 1), "rock", amp=math.radians(amp_deg),
                 period=period, ease=ease, hold0=hold, phase=phase, near=L)
    bridge_deck(b, m, c, f, L, w, col or b.skin.top)
    rt = right_of(f)
    cyl(b, "SeesawAxle", add(c, (0, -8, 0)), w + 30, 12, STEEL_LT, "Metal", b.scenery, axis=rt)
    for s_ in (-1, 1):
        q = add(c, mul(rt, s_ * (w / 2 + 12)))
        Pt(b, "SeesawTower", CF(add(q, (0, -60, 0)), *_axes(f)), (14, 110, 14), STEEL_DK, "Metal", b.scenery)
        stripe_box(b, "TowerBand", CF(add(q, (0, -14, 0)), *_axes(f)), (15, 4, 15))
        lamp(b, add(q, (0, 2, 0)), col=(255, 200, 40), pulse=period / 2)
        for k in (-1, 1):
            cyl(b, "SeesawPiston", add(add(q, mul(f, k * L * 0.3)), (0, -40, 0)), 60, 6, STEEL_LT, "Metal", b.scenery)
    a0, a1 = add(r.p, mul(f, 3)), add(r.p, mul(f, 3 + L))
    R2._special_line(b, a0, a1, 8)
    b.samples.append(c + (L,))
    r.p = add(a1, mul(f, 3))
    return c


def pier(r, label, L, w=70.0, cp=False, boosts=0):
    """A short fixed road between bridges, on a big steel pier."""
    road(r, label, L, w=w, cp=cp, boosts=boosts, every=40)
    c = sub(r.p, mul(r.f, L / 2))
    Pt(r.b, "PierColumn", CF(add(c, (0, -110, 0)), *_axes(r.f)), (w * 0.6, 200, L * 0.6), STEEL_DK, "DiamondPlate",
       r.b.scenery)
    stripe_box(r.b, "PierBand", CF(add(c, (0, -24, 0)), *_axes(r.f)), (w * 0.6 + 1, 5, L * 0.6 + 1))
    return r


def slot5(r, sk, rng):
    b = r.b
    sk.title = "Bridge Works"
    b.gate_label = "STAGE 5"
    col = ACC["bridge"]
    accent(b, col)
    road(r, "Bridge Approach", 160, w=80, cp=True, boosts=2, every=40, arrows_at=(80,))
    # 1. the swing span: a long bridge that turns half round on its pivot
    swing_span(r, "Swing Span", 360, w=56, period=4.2, ease=1.5)
    pier(r, "Span Pier", 70, cp=True)
    # 2. the sectional bridge: four short sections ticking round in turn
    for k in range(4):
        R2.turnstile(r, "Section %d" % (k + 1), 120, w=50, period=2.0, ease=0.6, phase=k * 0.25, col=STEEL)
        if k < 3:
            pier(r, "Section Pier %d" % (k + 1), 30)
    pier(r, "Crossroads Pier", 110, cp=True, w=90)
    junction = (r.p, r.f)
    # 3. the crossroads turntable: lined up with the road, or a quarter turn round with the side spur
    L = 240.0
    c = swing_span(r, "Crossroads Turntable", L, w=56, period=3.2, ease=1.0, step=math.pi / 2, col=(120, 170, 255))
    f = r.f
    rt = right_of(f)
    pier(r, "Turntable Pier", 70, cp=True)
    # 4. the see-saw bridge
    seesaw(r, "See-Saw Bridge", 300, w=60, amp_deg=10, period=4.6, hold=2.0)
    pier(r, "See-Saw Pier", 150, cp=True, w=90)
    ss_mid = sub(r.p, mul(r.f, 75))
    # 5. the big bend over the gear canyon: a turntable gear, the pendulum ferry
    r.turn("Canyon Bend", 30, 500, rails=True)
    R2.lay_strips(r, 40, 220, every=60, lanes=2)
    R2.gear_bridge(r, "Gear Turntable", 110, 3.0, col=col, teeth_col=STEEL)
    pier(r, "Gear Pier", 50)
    r.turn("Canyon Bend 2", -60, 500, rails=True)
    R2.pendulum_ferry(r, "Pendulum Ferry", Lp=260.0, amp_deg=26.0, period=5.4, deck=(90.0, 70.0), col=col)
    pier(r, "Ferry Pier", 70, cp=True)
    r.turn("Canyon Bend 3", 30, 500, rails=True)
    # 6. the second swing span and the tilt gauntlet
    swing_span(r, "Swing Span 2", 300, w=56, period=3.8, ease=1.3, phase=0.5, col=(90, 150, 255))
    pier(r, "Gauntlet Pier", 90, cp=True)
    merge0 = None
    for k in range(3):
        seesaw(r, "Tilt %d" % (k + 1), 160, w=60, amp_deg=9 + k, period=3.6 + 0.3 * k, hold=1.4, phase=k * 0.33)
        if k < 2:
            pier(r, "Tilt Pier %d" % (k + 1), 30)
    PW = 420.0
    r.w = PW  # (a broad landing plaza: the side spur drives straight onto its right side)
    merge0 = r.p
    road(r, "Bridge Plaza", 170, w=PW, cp=True, boosts=3, every=50, arrows_at=(60, 150))
    r.turn("Exit Ease", 18, 600, w1=80, rails=True)
    r.turn("Exit Ease 2", -18, 600, rails=True)
    # ---- the side spur: off the turntable when it has turned a quarter round, a safer way past everything
    sp = add(c, mul(rt, L / 2 + 3))
    al = Alt(r, sp, rt, 50, B=260.0)
    accent(b, (255, 255, 255))
    al.r.straight("Side Spur", 80, lead=5.0, rails=True, line=False)
    lamp(b, add(sp, (0, 4, 0)), col=(90, 255, 140), d=5.0, pulse=0.8)
    al.r.turn("Spur Bend", 90, 220, rails=True, line=False)
    R2.lay_strips(al.r, 40, 300, every=70, lanes=1)
    # it runs along the right of the bridges, then swings in and drops onto the bridge exit
    to = dot(sub(merge0, al.r.p), f) - 2 * 340 * math.sin(math.radians(45)) - 60.0
    Ls = max(60.0, to)
    al.r.straight("Spur Run", Ls, lead=5.0, rails=True, line=False)
    # (the spur is the safer way, not an empty one: arms and punches along it, gantries over it)
    kinds = [sweep_arm, punch, side_hammer, punch]
    at = [140 + 260 * k for k in range(int((Ls - 200) // 260) + 1)]
    for k, d in enumerate(at):
        al.r.along(kinds[k % len(kinds)], [d], i0=k)
        gantry(b, al.r.ahead(d + 120 - Ls), al.r.f, 50, h=40, col=STEEL)
    al.r.turn("Spur Swing", 45, 340, rails=True, line=False)
    al.r.turn("Spur Swing Back", -45, 340, rails=True, line=False)
    al.r.straight("Spur Merge", dot(sub(merge0, al.r.p), f), lead=5.0, rails=True, line=False)
    assert abs(dot(sub(al.r.p, merge0), rt)) < PW / 2 - 30, dot(sub(al.r.p, merge0), rt)
    al.done()
    # ---- the lower route: small fast spinning platforms under the swing spans
    p0, f0 = junction
    al = Alt(r, add(p0, mul(right_of(f0), -30)), f0, 50, B=230.0)
    accent(b, (150, 200, 255))
    al.o.plat("Lower Gate", 30, 30)
    al.o.drop(80.0, side=-110)
    al.o.plat("Lower Deck", 60, 50)
    R2.gear_bridge(al.r, "Spinner", 38, 7.0, col=(150, 200, 255), teeth_col=STEEL)
    al.o.plat("Lower Hop", 50, 40)
    R2.gear_bridge(al.r, "Spinner 2", 34, -8.0, col=(150, 200, 255), teeth_col=STEEL)
    up = ss_mid[1] - al.r.p[1]
    lo, hi = al.o.pad_range(up)
    gap = dot(sub(ss_mid, al.r.p), f0)
    al.o.plat("Lower Run", max(40.0, gap - (lo + hi) / 2), 40)
    al.o.pad(up, side=dot(sub(ss_mid, al.r.p), right_of(f0)) * 0.9)
    al.done()
    accent(b, col)
    r.log("end")
    return ["Swing Span", "Sectional Bridge", "Crossroads Turntable", "Side Spur", "See-Saw Bridge", "Gear Turntable",
            "Pendulum Ferry", "Tilt Gauntlet", "Lower Spinners"]


# ===================================================================== 8. the wrecking-ball section
def wrecking_ball(b, c, w, i, H=72.0, lane=None, along=False, amp=58.0, period=3.0, phase=None, d=28.0, col=None):
    """A wrecking ball on a chain from a steel A-frame over the road. across: it sweeps the whole width; along: it
    swings down one lane, to and fro along the road. Knocks the car off."""
    x, y, z = c
    zz = z if lane is None else z + lane * w / 3
    pivot = (x, y + H, zz)
    for s_ in (-1, 1):
        for k in (-1, 1):
            # A-frame legs leaning in to the beam
            foot = (x + k * 16, y - 2, z + s_ * (w / 2 + 10))
            top = (x, y + H + 4, z + s_ * (w / 2 + 6))
            cyl(b, "FrameLeg", R2.lerp3(foot, top, 0.5), math.dist(foot, top), 5, STEEL, "Metal", b.scenery,
                axis=unit(sub(top, foot)))
        stripe_box(b, "FrameFoot", CF((x, y + 2, z + s_ * (w / 2 + 10))), (40, 4, 8))
        lamp(b, (x, y + H + 10, z + s_ * (w / 2 + 6)), col=(255, 120, 40), pulse=period / 2)
    Pt(b, "FrameBeam", CF((x, y + H + 6, z)), (8, 8, w + 24), STEEL_DK, "Metal", b.scenery)
    stripe_box(b, "BeamStripe", CF((x, y + H + 1.6, z)), (8.4, 0.8, w + 20))
    cyl(b, "PivotBlock", (x, y + H + 1, zz), 10, 10, STEEL_LT, "Metal", b.scenery, axis=(1, 0, 0) if not along else (0, 0, 1))
    root = b.prop_root("WreckingBall")
    axis = (0, 0, 1) if along else (1, 0, 0)
    ph = ((i * 0.37) % 1) if phase is None else phase
    rig = b.rig(root, "Hinge", axis_frame(pivot, axis), amp, period, phase=ph, keys="0:0 0.25:1 0.5:0 0.75:-1",
                name="Swing")
    L = H - d - 3  # (the ball's underside just clears the road at the bottom of its swing)
    n = max(4, int(L / 9))
    for k in range(n):
        q = (x, y + H - (k + 0.5) * L / n, zz)
        cyl(b, "ChainLink", q, L / n - 1.2, 2.6 if k % 2 else 1.6, STEEL_LT, "Metal", rig, axis=(0, 1, 0))
    bc = (x, y + H - L - d / 2, zz)
    ball(b, "WreckingBall", bc, d, col or STEEL_DK, "Metal", rig, query=True, attrs={"ObbyHazard": "Knock"}, refl=0.2)
    ringz(b, bc, d / 2 + 0.4, ACC["wreck"], "Neon", th=2.0, axis=axis, parent=rig, name="BallBand")
    cyl(b, "BallEye", (x, bc[1] + d / 2 + 1, zz), 4, 6, STEEL, "Metal", rig, axis=(0, 1, 0))
    impact_zone(b, (x, y, zz), (1, 0, 0), (w if not along else w / 3 + 6), 18 if not along else 60)


def ball_pair(b, c, w, i):
    """Two balls side by side swinging in opposite directions."""
    wrecking_ball(b, sub(c, (18, 0, 0)), w, i, phase=0.0, period=2.8)
    wrecking_ball(b, add(c, (18, 0, 0)), w, i, phase=0.5, period=2.8, col=(120, 40, 30))


def ball_lane(b, c, w, i):
    wrecking_ball(b, c, w, i, lane=(i % 3) - 1, along=True, amp=50, period=2.4, H=64.0, d=24.0)


def ball_high(b, c, w, i):
    """A huge ball on a long chain from a tall frame: a slow, wide sweep."""
    wrecking_ball(b, c, w, i, H=120.0, amp=40, period=4.2, d=40.0, col=(90, 30, 24))


def debris(b, c, f, w, rng, n=6):
    """Broken barriers, rubble and loose chains at the road's edges (outside the rails)."""
    rt = right_of(f)
    for k in range(n):
        s_ = rng.choice([-1, 1])
        q = add(c, add(mul(f, rng.uniform(-60, 60)), mul(rt, s_ * (w / 2 + rng.uniform(8, 26)))))
        kind = rng.random()
        yaw = rng.uniform(0, TAU)
        if kind < 0.4:
            cf = CF(add(q, (0, 3, 0))) * rot_y(yaw) * rot_axis((1, 0, 0), rng.uniform(-0.6, 0.6))
            stripe_box(b, "BrokenBarrier", cf, (rng.uniform(14, 26), 5, 3))
        elif kind < 0.75:
            box(b, "Rubble", add(q, (0, rng.uniform(1, 4), 0)), (rng.uniform(4, 9),) * 3, rng.choice([STEEL, STEEL_DK, (90, 84, 78)]),
                "Concrete", yaw=yaw)
        else:
            for j in range(5):
                cyl(b, "LooseChain", add(q, (math.cos(j) * 4, 1, math.sin(j) * 4)), 4, 1.8, STEEL_LT, "Metal", b.scenery,
                    axis=unit((math.cos(j + 1.5), 0.0, math.sin(j + 1.5))))


def hanging_chains(b, c, f, w, n=7):
    """A curtain of chains hanging beside the road from a beam (scenery)."""
    rt = right_of(f)
    for s_ in (-1, 1):
        base = add(c, mul(rt, s_ * (w / 2 + 30)))
        Pt(b, "ChainBeam", CF(add(base, (0, 80, 0)), *_axes(f)), (6, 6, 120), STEEL, "Metal", b.scenery)
        for k in range(n):
            q = add(base, add(mul(f, -55 + k * 110 / (n - 1)), (0, 80 - 20 - k % 3 * 10, 0)))
            Lc = 40 + (k % 3) * 20
            cyl(b, "HangChain", add(q, (0, 20 - Lc / 2, 0)), Lc, 1.6, STEEL_LT, "Metal", b.scenery)
            Pt(b, "ChainHook", CF(add(q, (0, 20 - Lc, 0))), (4, 4, 1.4), HAZ_Y, "Metal", b.scenery)


def dress_road(r, rng, every=140.0, chains=False):
    """Debris along the road just laid."""
    pts = r.last[0]
    cum = [0.0]
    for a_, c_ in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))
    d = every / 2
    k = 0
    while d < cum[-1]:
        i = next(i for i in range(len(cum) - 1) if cum[i + 1] >= d)
        p = R2.lerp3(pts[i], pts[i + 1], (d - cum[i]) / max(cum[i + 1] - cum[i], 1e-6))
        f = RT.flat(sub(pts[i + 1], pts[i]))
        debris(r.b, p, f, r.last[1][i], rng, n=4)
        if chains and k % 2 == 1:
            hanging_chains(r.b, p, f, r.last[1][i])
        d += every
        k += 1


def slot6(r, sk, rng):
    b = r.b
    sk.title = "Demolition Yard"
    b.gate_label = "STAGE 6"
    col = ACC["wreck"]
    accent(b, col)
    road(r, "Yard Approach", 160, w=80, cp=True, boosts=2, every=40, arrows_at=(80,))
    # 1. the wrecking row: balls of every size and swing, on an elevated road
    road(r, "Wrecking Row", 640, w=72, dy=60, cp=True)
    r.along(wrecking_ball, [90], i0=0)
    r.along(ball_lane, [190], i0=0)
    r.along(ball_high, [300], i0=1)
    r.along(ball_lane, [400], i0=2)
    r.along(wrecking_ball, [500], i0=3)
    r.along(ball_lane, [580], i0=4)
    dress_road(r, rng)
    # 2. the wrecking bend: an S through more frames
    r.turn("Wrecking Bend", 30, 460, rails=True)
    r.along(ball_lane, [110], i0=1)
    dress_road(r, rng, chains=True)
    r.turn("Wrecking Bend 2", -60, 460, rails=True)
    r.along(wrecking_ball, [90, 300], i0=2)
    r.along(ball_high, [200], i0=3)
    dress_road(r, rng)
    r.turn("Wrecking Bend 3", 30, 460, rails=True)
    r.along(ball_lane, [120], i0=5)
    # 3. the opposite pair, then the wide escape ramp
    road(r, "Pair Run", 280, w=72, dy=40, cp=True)
    r.along(ball_pair, [140], i0=0)
    dress_road(r, rng, chains=True)
    road(r, "Escape Run", 160, w=130, boosts=3, every=40, arrows_at=(80,))
    R2.ramp_jump(r, "Escape Ramp", deg=20, drop=70, w_land=140, slope=3, land_min=300, cp=True)
    # 4. the scrap heap: low balls down the lanes over a littered road
    road(r, "Scrap Heap", 420, w=90, dy=50, cp=True)
    r.along(ball_lane, [80, 170, 260, 350], i0=0)
    dress_road(r, rng, every=100, chains=True)
    road(r, "Heap Edge", 120, w=90, boosts=3, every=35)
    R2.drop_off(r, "Demolition Drop", 60.0, w=90, cp=True)
    r.along(ball_high, [230], i0=4)
    # 5. the ball run and the wrecker launch
    road(r, "Ball Run", 420, w=72, dy=51, cp=True)
    r.along(ball_pair, [100, 300], i0=1)
    r.along(wrecking_ball, [200], i0=6)
    dress_road(r, rng)
    road(r, "Launch Run", 160, w=90, boosts=3, every=40, arrows_at=(80,))
    R2.ramp_jump(r, "Wrecker Launch", deg=20, drop=60, w_land=100, slope=3, land_min=300, cp=True)
    r.log("end")
    return ["Wrecking Row", "Wrecking Bend", "Opposite Pair", "Escape Ramp", "Scrap Heap", "Demolition Drop", "Ball Run",
            "Wrecker Launch"]


# ===================================================================== 9. the high-speed corkscrew
def tunnel(b, p0, f, L, w, col, step=24.0):
    """A tight lit tube round the straight road from p0 along f: ribs, roof lights, a doorway at each end."""
    rt = right_of(f)
    d = 8.0
    while d < L:
        c = add(p0, mul(f, d))
        fr = deck_frame(c, f)
        for s_ in (-1, 1):
            Pt(b, "TunnelWall", CF(add(c, add(mul(rt, s_ * (w / 2 + 8)), (0, 22, 0))), fr.x, fr.y, fr.z), (3, 50, step * 0.75),
               STEEL_DK, "DiamondPlate", b.scenery)
            Pt(b, "TunnelStrip", CF(add(c, add(mul(rt, s_ * (w / 2 + 6.3)), (0, 10, 0))), fr.x, fr.y, fr.z), (0.4, 3, step * 0.75),
               col, "Neon", b.scenery)
        Pt(b, "TunnelRoof", CF(add(c, (0, 48, 0)), fr.x, fr.y, fr.z), (w + 22, 3, step * 0.75), STEEL_DK, "DiamondPlate",
           b.scenery)
        Pt(b, "TunnelLight", CF(add(c, (0, 46.2, 0)), fr.x, fr.y, fr.z), (w * 0.8, 0.4, 4), (255, 240, 200), "Neon", b.scenery)
        d += step
    door_frame(b, p0, f, w / 2 + 8, 50.0, col)
    door_frame(b, add(p0, mul(f, L)), f, w / 2 + 8, 50.0, col)


def hop(r, label, drop=30.0, deg=8.0, V=330.0, land_extra=60.0):
    """A little kicker at the end of a segment and a hop over a gap onto the next (lower) segment."""
    b = r.b
    lip, d = R2.kicker(r, label + " Kicker", deg, L=30.0, w=r.w, rails=False)
    f = r.f
    gr = lambda p: lip[1] - drop
    p_lo, _ = R2.fly(lip, mul(d, V * 0.9), gr)
    p_hi, _ = R2.fly(lip, mul(d, V), gr)
    start = dot(sub(p_lo, lip), f) - 50.0
    far = dot(sub(p_hi, lip), f)
    b.line(*lip)
    b.arc((lip[0], lip[1] + CAR_UP, lip[2]), mul(d, V), until_y=lip[1] - drop + CAR_UP, step=0.04)
    b.jumps.append(("ramp", lip, p_hi, V * math.hypot(d[0], d[2]), V * d[1]))
    r.p = add(lip, add(mul(f, start), (0, -drop, 0)))
    n0 = len(b.path)
    r.straight(label + " Landing", far - start + land_extra, lead=10.0)
    b.path[n0:] = [q for q in b.path[n0:] if dot(sub(q[:3], p_hi), f) > 6]
    impact_zone(b, add(lip, add(mul(f, (far + start) / 2 + 10), (0, -drop, 0))), f, r.w, far - start)
    return r


def lift_art(b, src, f, w):
    """A piston lift under a launch pad: a huge ram under the deck, hydraulic cylinders, hazard bands."""
    rt = right_of(f)
    cyl(b, "LiftRam", add(src, (0, -70, 0)), 120, 30, STEEL_LT, "Metal", b.scenery, refl=0.3)
    cyl(b, "LiftSleeve", add(src, (0, -150, 0)), 80, 44, STEEL_DK, "Metal", b.scenery)
    stripe_box(b, "LiftCollar", CF(add(src, (0, -112, 0)), *_axes(f)), (48, 6, 48))
    for s_ in (-1, 1):
        q = add(src, mul(rt, s_ * (w / 2 + 12)))
        cyl(b, "LiftCylinder", add(q, (0, 20, 0)), 46, 8, STEEL_LT, "Metal", b.scenery)
        Pt(b, "LiftCap", CF(add(q, (0, 45, 0)), *_axes(f)), (12, 4, 12), HAZ_Y, "Metal", b.scenery)
        lamp(b, add(q, (0, 49, 0)), col=(255, 200, 40), pulse=0.9)


def lifts(r, n, dy, label="Piston Lift", B=260.0):
    """n launch-pad lifts in a row, each throwing the car dy up onto the next deck."""
    b = r.b
    o = O.Obby(r, B)
    o.plat(label + " Deck", 120, 80, cp=True)
    for k in range(n):
        o.pad(dy, label="%s %d" % (label, k + 1))
        src = [j for j in b.jumps if j[0] == "oup"][-1][1]
        lift_art(b, src, r.f, 80)
        o.plat("%s Deck %d" % (label, k + 1), 140 if k < n - 1 else 120, 80, cp=(k == n - 1))
    return r


def mech_tower(b, C, y0, y1, col, rng):
    """The tower the corkscrew winds round: a stacked drum column, glowing bands, gears turning round it, pistons."""
    x, z = C[0], C[2]
    y = y0
    k = 0
    while y < y1:
        h = rng.uniform(40, 70)
        Rr = 100 if k % 2 == 0 else 86
        cyl(b, "TowerDrum", (x, y + h / 2, z), h, 2 * Rr, STEEL if k % 2 else STEEL_DK, "DiamondPlate", b.scenery)
        cyl(b, "TowerBand", (x, y + h + 1, z), 2, 2 * Rr + 4, col, "Neon", b.scenery)
        y += h + 2
        k += 1
    cyl(b, "TowerCap", (x, y1 + 20, z), 40, 140, STEEL_DK, "Metal", b.scenery)
    lamp(b, (x, y1 + 46, z), col=(255, 60, 40), d=12.0, pulse=1.0)
    for j, yy in enumerate(range(int(y0 + 300), int(y1), 150)):
        big_gear(b, (x, yy, z), 128, (0, 1, 0), STEEL_LT if j % 2 else col, spin=0.05 * (1 if j % 2 else -1))


def spokes(b, C, pts, every=90.0, R_in=100.0):
    """Beams from the tower out under the spiral road (it hangs on them instead of trusses)."""
    cum = 0.0
    nxt = 30.0
    for a_, c_ in zip(pts, pts[1:]):
        L = math.dist(a_, c_)
        while nxt <= cum + L:
            p = R2.lerp3(a_, c_, (nxt - cum) / max(L, 1e-6))
            v = (p[0] - C[0], 0.0, p[2] - C[2])
            D = math.hypot(v[0], v[2])
            u = (v[0] / D, 0.0, v[2] / D)
            q0 = (C[0] + u[0] * R_in, p[1] - 14, C[2] + u[2] * R_in)
            q1 = (p[0], p[1] - 14, p[2])
            Pt(b, "Spoke", CF(R2.lerp3(q0, q1, 0.5), *_axes(u)), (8, 10, math.dist(q0, q1)), STEEL, "Metal", b.scenery)
            stripe_box(b, "SpokeBand", CF(add(q1, (0, 0, 0)), *_axes(u)), (8.4, 10.4, 6))
            nxt += every
        cum += L


def corkscrew(r, label, arcs, deg, R, dy_arc, hop_drop, col, rng, bank=14.0):
    """A banked spiral round a tower: arcs of deg each, diving dy_arc, a hop between each two."""
    b = r.b
    b.no_under = True
    cs = []
    pts = []
    y_top = r.p[1]
    for k in range(arcs):
        r.turn("%s %d" % (label, k + 1), deg, R, dy=dy_arc, bank=bank, rails=True, cp=(k % 2 == 1))
        cs.append(r.centre)
        pts += list(r.last[0])
        R2.lay_strips(r, 60, deg * math.pi / 180 * R - 60, every=150, lanes=2)
        if k < arcs - 1:
            hop(r, "%s Hop %d" % (label, k + 1), drop=hop_drop)
            pts += list(r.last[0])
    b.no_under = False
    C = (sum(c[0] for c in cs) / len(cs), 0.0, sum(c[2] for c in cs) / len(cs))
    mech_tower(b, C, Y0 - 700, y_top + 120, col, rng)
    spokes(b, C, pts)
    return C


def slot7(r, sk, rng):
    b = r.b
    sk.title = "Corkscrew Tower"
    b.gate_label = "STAGE 7"
    col = ACC["cork"]
    accent(b, col)
    road(r, "Tower Approach", 160, w=80, cp=True, boosts=2, every=40, arrows_at=(80,))
    lifts(r, 3, 100.0)
    road(r, "Spiral Entry", 220, w=80, boosts=3, every=40, cp=True, arrows_at=(110, 200))
    corkscrew(r, "Corkscrew", 4, 180.0, 360.0, -60.0, 30.0, col, rng)
    p0, f = r.p, r.f
    road(r, "Exit Tunnel", 340, w=80, boosts=3, every=40, cp=True)
    tunnel(b, p0, f, 340, 80, col)
    # the banked slalom through gantries and arms
    r.turn("Slalom", 45, 400, bank=10, rails=True)
    r.along(sweep_arm, [160], i0=0)
    r.turn("Slalom 2", -90, 400, bank=10, rails=True, cp=True)
    r.along(punch, [120, 320], i0=1)
    r.along(sweep_arm, [450], i0=1)
    r.turn("Slalom 3", 45, 400, bank=10, rails=True)
    R2.lay_strips(r, 40, 260, every=70, lanes=2)
    lifts(r, 2, 100.0, label="Tower Lift")
    road(r, "Spiral Entry 2", 200, w=80, boosts=3, every=40, cp=True)
    corkscrew(r, "Corkscrew B", 2, 180.0, 400.0, -70.0, 30.0, (255, 160, 220), rng)
    p0, f = r.p, r.f
    road(r, "Exit Tunnel 2", 300, w=80, dy=-8, boosts=3, every=40, cp=True)
    tunnel(b, p0, f, 300, 80, (255, 160, 220))
    r.log("end")
    return ["Piston Lifts", "Corkscrew", "Spiral Hops", "Exit Tunnel", "Banked Slalom", "Corkscrew B"]


# ===================================================================== 10. the giant fan tunnel
def fan(b, c, w, i, R=60.0, n=3, speed=0.3, off=0.0, hub_h=None, col=None, ring=True):
    """A giant fan turning in the duct across the road: blades sweep down through the road (SHREDDED); go through
    between them. off moves the hub sideways, so its blades cover one side more than the other."""
    x, y, z = c
    hh = R + 1 if hub_h is None else hub_h
    hub = (x, y + hh, z + off)
    root = b.prop_root("Fan")
    rig = b.rig(root, "Spin", axis_frame(hub, (1, 0, 0)), speed * (1 if i % 2 == 0 else -1), 1, phase=(i * 0.21) % 1,
                name="FanSpin")
    for k in range(n):
        a = TAU * k / n
        d = (0.0, math.cos(a), math.sin(a))
        q = add(hub, mul(d, R / 2 + 4))
        Pt(b, "FanBlade", CF(q, (1, 0, 0), d, cross((1, 0, 0), d)), (2.4, R - 6, 10), col or (170, 178, 190), "Metal", rig,
           query=True, attrs={"ObbyHazard": "Shred"})
        Pt(b, "BladeTip", CF(add(hub, mul(d, R - 3)), (1, 0, 0), d, cross((1, 0, 0), d)), (2.8, 4, 10.4), (255, 60, 40),
           "Neon", rig)
    cyl(b, "FanHub", hub, 8, 18, STEEL_DK, "Metal", rig, axis=(1, 0, 0))
    cyl(b, "FanNose", add(hub, (-5, 0, 0)), 3, 10, ACC["fan"], "Neon", rig, axis=(1, 0, 0))
    if ring:
        Rr = max(R + 14, math.hypot(w / 2 + 8, hh) + 4)
        poly_ring(b, hub, Rr, 10.0, 8.0, STEEL, "FanHousing", y_min=y - 4)
        poly_ring(b, add(hub, (-5.2, 0, 0)), Rr - 6, 0.8, 1.2, ACC["fan"], "FanGlow", mat="Neon", y_min=y - 4)
        for s_ in (-1, 1):
            Pt(b, "FanStrut", CF((x, y + hh / 2 + 30, z + s_ * (w / 2 + 14))), (6, hh + 60, 6), STEEL, "Metal", b.scenery)
    impact_zone(b, (x, y, z), (1, 0, 0), w, 10)


def poly_ring(b, c, R, th, depth, col, name, mat="Metal", n=16, y_min=None):
    """A ring of n straight steel segments in the plane across +X (a duct frame round a fan); segments that would dip
    under y_min (into the road) are left out."""
    for k in range(n):
        a0, a1 = TAU * k / n, TAU * (k + 1) / n
        p0 = (c[0], c[1] + R * math.cos(a0), c[2] + R * math.sin(a0))
        p1 = (c[0], c[1] + R * math.cos(a1), c[2] + R * math.sin(a1))
        if y_min is not None and min(p0[1], p1[1]) - depth / 2 < y_min + 12:
            continue
        d = unit(sub(p1, p0))
        nrm = cross((1, 0, 0), d)
        Pt(b, name, CF(R2.lerp3(p0, p1, 0.5), (1, 0, 0), nrm, d), (th, depth, math.dist(p0, p1) + 1), col, mat, b.scenery)


def lane_fans(b, c, w, i):
    """Three small fans, one per lane of the split duct, each turning at its own speed."""
    x, y, z = c
    for k in range(3):
        zz = z - w / 2 + w * (k + 0.5) / 3
        fan(b, (x, y, zz), w / 3, i * 3 + k, R=20.0, n=2 + k % 2, speed=0.35 + 0.15 * ((k + i) % 3), ring=False,
            col=(200, 255, 240))
        poly_ring(b, (x, y + 21, zz), 25, 6.0, 4.0, STEEL, "LaneDuct", y_min=y + 0.5)


def shutter(b, c, w, i, period=2.6):
    """Two half-width shutters dropping from the duct roof in turn (CRUSHED under a closing one)."""
    x, y, z = c
    for k, s_ in enumerate((-1, 1)):
        rest = (x, y + 74, z + s_ * w / 4)
        root = b.prop_root("Shutter")
        rig = b.rig(root, "Slide", axis_frame(rest, (0, -1, 0)), 60.0, period, phase=(k * 0.5 + i * 0.13) % 1,
                    keys="0:0 0.45:0 0.55:1 0.75:1 0.85:0", name="Close")
        for j in range(5):
            Pt(b, "ShutterSlat", CF(add(rest, (0, -12 + j * 6, 0))), (4, 5, w / 2 - 2), STEEL_LT if j % 2 else STEEL, "Metal",
               rig, query=(j == 0), attrs={"ObbyHazard": "Crush"} if j == 0 else None)
        stripe_box(b, "ShutterEdge", CF(add(rest, (0, -15, 0))), (4.4, 1, w / 2 - 1.6), parent=rig)
        lamp(b, (x - 4, y + 96, z + s_ * w / 4), col=(255, 60, 40), pulse=period)
    Pt(b, "ShutterBox", CF((x, y + 96, z)), (12, 16, w + 10), STEEL_DK, "Metal", b.scenery)


def duct(b, p0, f, L, w, h=130.0, col=None, step=40.0):
    """A square steel duct round the straight road: walls with vent grilles, roof ribs, light strips."""
    col = col or ACC["fan"]
    rt = right_of(f)
    d = step / 2
    k = 0
    while d < L:
        c = add(p0, mul(f, d))
        fr = deck_frame(c, f)
        for s_ in (-1, 1):
            q = add(c, add(mul(rt, s_ * (w / 2 + 16)), (0, h / 2 - 10, 0)))
            Pt(b, "DuctWall", CF(q, fr.x, fr.y, fr.z), (3, h + 20, step - 2), STEEL_DK, "DiamondPlate", b.scenery)
            if k % 2 == 0:
                Pt(b, "VentGrille", CF(add(q, mul(rt, -s_ * 1.7)), fr.x, fr.y, fr.z), (0.4, 26, step * 0.6), STEEL_LT,
                   "Metal", b.scenery)
            Pt(b, "DuctLight", CF(add(c, add(mul(rt, s_ * (w / 2 + 14.2)), (0, 20, 0))), fr.x, fr.y, fr.z), (0.4, 2, step - 6),
               col, "Neon", b.scenery)
        Pt(b, "DuctRoof", CF(add(c, (0, h, 0)), fr.x, fr.y, fr.z), (w + 36, 3, step - 2), STEEL_DK, "DiamondPlate", b.scenery)
        if k % 2 == 1:
            Pt(b, "DuctRib", CF(add(c, (0, h - 4, 0)), fr.x, fr.y, fr.z), (w + 30, 6, 6), STEEL, "Metal", b.scenery)
        d += step
        k += 1
    door_frame(b, p0, f, w / 2 + 16, h, col)
    door_frame(b, add(p0, mul(f, L)), f, w / 2 + 16, h, col)


def fan_art(b, src, f, w):
    """A big fan lying in the deck under an updraft pad, spinning."""
    hub = add(src, (0, -6, 0))
    root = b.prop_root("FloorFan")
    rig = b.rig(root, "Spin", axis_frame(hub, (0, 1, 0)), 1.2, 1, name="FloorSpin")
    for k in range(4):
        a = TAU * k / 4
        d = (math.cos(a), 0.0, math.sin(a))
        Pt(b, "FloorBlade", CF(add(hub, mul(d, 14)), d, UP, cross(d, UP)), (24, 1, 8), (220, 225, 235), "Metal", rig)
    ringz(b, add(src, (0, -2, 0)), 32, STEEL, "Metal", th=4.0, axis=UP, parent=b.scenery, name="FloorFanRing")
    ringz(b, add(src, (0, 0.2, 0)), 30, ACC["fan"], "Neon", th=0.3, axis=UP, parent=b.scenery, name="UpdraftGlow")
    cyl(b, "FanDuct", add(src, (0, -60, 0)), 100, 60, STEEL_DK, "Metal", b.scenery)


def slot8(r, sk, rng):
    b = r.b
    sk.title = "Fan Tunnel"
    b.gate_label = "STAGE 8"
    col = ACC["fan"]
    accent(b, col)
    W = 90.0
    road(r, "Intake Approach", 180, w=W, cp=True, boosts=2, every=45, arrows_at=(90,))
    # 1. the first duct: four giant fans, each its own size, speed and position
    p0, f = r.p, r.f
    road(r, "Fan Duct", 540, w=W, cp=True)
    r.along(fan, [100], i0=0, n=2, speed=0.25)
    r.along(fan, [220], i0=1, n=3, speed=0.3, off=18.0)
    r.along(fan, [340], i0=2, n=3, speed=0.4, off=-18.0)
    r.along(fan, [460], i0=3, n=4, speed=0.28)
    # 2. the shutters
    road(r, "Shutter Run", 320, w=W, cp=True)
    r.along(shutter, [90, 180, 270], i0=0)
    duct(b, p0, f, 860, W, col=col)
    # 3. the split duct: three lanes, three small fans in each row
    p0 = r.p
    r.w = 150.0
    road(r, "Split Duct", 400, w=150, cp=True)
    r.along(lane_fans, [100, 200, 300], i0=0)
    for s_ in (-1, 1):
        q = add(p0, add(mul(right_of(f), s_ * 25), mul(f, 200)))
        Pt(b, "DuctDivider", CF(add(q, (0, 30, 0)), *_axes(f)), (3, 60, 320), STEEL, "DiamondPlate", b.scenery, collide=True)
        stripe_box(b, "DividerNose", CF(add(add(q, mul(f, -161)), (0, 30, 0)), *_axes(f)), (4, 60, 3), collide=True)
    duct(b, p0, f, 400, 150, col=col)
    r.w = W
    road(r, "Duct Out", 120, w=W, boosts=2, every=40)
    # 4. the pipe bend: out in the open between huge pipes
    r.turn("Pipe Bend", 30, 400, bank=8, rails=True)
    r.turn("Pipe Bend 2", -60, 400, bank=8, rails=True)
    R2.lay_strips(r, 60, 360, every=80, lanes=2)
    r.turn("Pipe Bend 3", 30, 400, bank=8, rails=True)
    # 5. the close fans: a fast run of fans close together, then out into the open air
    p0, f = r.p, r.f
    road(r, "Close Fans", 340, w=W, boosts=3, every=50, cp=True)
    r.along(fan, [60, 115, 170, 225, 280], i0=0, R=56.0, n=3, speed=0.45)
    duct(b, p0, f, 340, W, col=col)
    road(r, "Fan Exit", 120, w=W, boosts=3, every=30)
    R2.ramp_jump(r, "Open Air Jump", deg=22, drop=90, w_land=120, slope=3, land_min=360, cp=True)
    # 6. updraft fans lift the car back up
    o = O.Obby(r, 260)
    o.plat("Updraft Deck", 100, 80, cp=True)
    for k in range(2):
        o.pad(48.0, label="Updraft %d" % (k + 1))
        src = [j for j in b.jumps if j[0] == "oup"][-1][1]
        fan_art(b, src, r.f, 80)
        o.plat("Updraft Deck %d" % (k + 1), 140, 80, cp=(k == 1))
    road(r, "Vent Run", 180, w=W, boosts=2, every=60)
    r.along(fan, [100], i0=5, R=56.0, n=4, speed=0.35)
    r.log("end")
    return ["Fan Duct", "Shutters", "Split Duct", "Pipe Bend", "Close Fans", "Open Air Jump", "Updraft Fans"]


# ===================================================================== 11. the destructible zone
def at_road(r, d):
    """(point, heading) d along the road just laid."""
    pts = r.last[0]
    cum = [0.0]
    for a_, c_ in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))
    d = min(max(d, 0.5), cum[-1] - 0.5)
    i = next(i for i in range(len(cum) - 1) if cum[i + 1] >= d)
    return R2.lerp3(pts[i], pts[i + 1], (d - cum[i]) / max(cum[i + 1] - cum[i], 1e-6)), RT.flat(sub(pts[i + 1], pts[i]))


def brick_wall(b, c, f, w, h=24.0, kind="crate", speed=150.0, respawn=6.0, nx=None, ny=None):
    """A wall the game's arcade script smashes when a car hits it fast enough (bricks fly off and come back a few
    seconds later). c: the bottom centre on the road; f: the way the car comes."""
    import rbxl
    fr = deck_frame(c, f)
    m = b.model("BrickWall", b.hazards, {"ArcadeM": "bricks", "BrickSpeed": float(speed), "BrickRespawn": float(respawn),
                                         "BrickFace": ("CFrame", fr.p, fr.rows()), "BrickW": float(w), "BrickH": float(h)})
    rt = right_of(f)
    if kind == "crate":
        nx = nx or max(1, int(round(w / 12)))
        ny = ny or 2
        cols = [(196, 140, 70), (170, 116, 56)]
        mat = "WoodPlanks"
    else:
        nx = nx or max(2, int(round(w / 8)))
        ny = ny or 4
        cols = [(170, 72, 52), (150, 60, 44), (190, 90, 66)]
        mat = "Brick"
    bw, bh = w / nx, h / ny
    for j in range(ny):
        for i in range(nx):
            sh = (bw / 2 if (kind != "crate" and j % 2) else 0.0)
            x = -w / 2 + bw * (i + 0.5) + sh
            if x > w / 2 - bw * 0.25:
                continue
            q = add(c, add(mul(rt, -x), (0, bh * (j + 0.5), 0)))
            Pt(b, "Brick", CF(q, fr.x, fr.y, fr.z), (bw - 0.4, bh - 0.4, 6 if kind != "crate" else bw - 1), cols[(i + j) % len(cols)],
               mat, m, collide=True, attrs={"Brick": True})
    return m


def reinforced_gate(b, c, f, w, h=26.0):
    """A steel gate that does not break: go round it."""
    fr = deck_frame(c, f)
    Pt(b, "ReinforcedGate", CF(add(c, (0, h / 2, 0)), fr.x, fr.y, fr.z), (w, h, 4), STEEL_LT, "DiamondPlate", b.scenery, collide=True)
    stripe_box(b, "GateStripe", CF(add(c, (0, h + 1, 0)), fr.x, fr.y, fr.z), (w + 0.4, 2, 4.4), collide=True)
    rt = right_of(f)
    for s_ in (-1, 1):
        Pt(b, "GateBolt", CF(add(c, add(mul(rt, s_ * (w / 2 - 3)), (0, h / 2, 0))), fr.x, fr.y, fr.z), (3, h, 5), STEEL_DK, "Metal",
           b.scenery, collide=True)


def lane_row(r, d, w, pattern, kind="crate"):
    """A row across the road: per lane 'b' a breakable wall, 'g' a reinforced gate, '.' open."""
    p, f = at_road(r, d)
    rt = right_of(f)
    for k, ch in enumerate(pattern):
        q = add(p, mul(rt, -w / 2 + w * (k + 0.5) / 3))
        if ch == "b":
            brick_wall(r.b, q, f, w / 3 - 2, kind=kind)
        elif ch == "g":
            reinforced_gate(r.b, q, f, w / 3 - 2)
    for s_ in (-1, 1):
        cyl(r.b, "RowPost", add(p, add(mul(rt, s_ * (w / 2 + 4)), (0, 16, 0))), 32, 4, STEEL, "Metal", r.b.scenery)
    lamp(r.b, add(p, add(mul(rt, -w / 2 - 4), (0, 34, 0))), col=(255, 160, 40))


def crate_stacks(b, c, f, w, rng, n=4):
    """Stacks of crates and barrels beside the road (outside the rails)."""
    rt = right_of(f)
    for k in range(n):
        s_ = rng.choice([-1, 1])
        q = add(c, add(mul(f, rng.uniform(-70, 70)), mul(rt, s_ * (w / 2 + rng.uniform(10, 30)))))
        for j in range(rng.randint(1, 3)):
            if rng.random() < 0.6:
                box(b, "Crate", add(q, (rng.uniform(-2, 2), 5 + j * 10, rng.uniform(-2, 2))), (10, 10, 10),
                    rng.choice([(196, 140, 70), (170, 116, 56)]), "WoodPlanks", yaw=rng.uniform(0, 1))
            else:
                cyl(b, "Barrel", add(q, (0, 6 + j * 12, 0)), 12, 8, rng.choice([(200, 60, 40), (60, 120, 200), HAZ_Y]), "Metal")


def slot9(r, sk, rng):
    b = r.b
    sk.title = "Smash Yard"
    b.gate_label = "STAGE 9"
    col = ACC["smash"]
    accent(b, col)
    W = 90.0
    road(r, "Smash Approach", 200, w=W, cp=True, boosts=3, every=40, arrows_at=(100,))
    # 1. crate alley: crates in some lanes, reinforced gates in others (smash a crate, dodge a gate)
    road(r, "Crate Alley", 560, w=W, cp=True)
    R2.lay_strips(r, 20, 540, every=45, lanes=3)
    for d, pat in ((100, "gb b"), (200, "bbg"), (300, "bbb"), (400, "gbg"), (500, "bbb")):
        lane_row(r, d, W, pat.replace(" ", "."))
    for d in (60, 260, 460):
        p, f = at_road(r, d)
        crate_stacks(b, p, f, W, rng)
    # 2. the barricade run: full-width brick walls
    road(r, "Barricade Run", 480, w=W, dy=40, cp=True)
    R2.lay_strips(r, 20, 460, every=40, lanes=3)
    for d in (130, 270, 410):
        p, f = at_road(r, d)
        brick_wall(b, p, f, W - 4, h=28.0, kind="brick")
        for s_ in (-1, 1):
            Pt(b, "BarricadePost", CF(add(p, add(mul(right_of(f), s_ * (W / 2 + 3)), (0, 18, 0))), *_axes(f)), (6, 36, 6), STEEL,
               "Metal", b.scenery)
    # 3. the fork: the open way bends round to the right; the cracked wall on the left hides the straight shortcut
    road(r, "Smash Fork", 120, w=240, cp=True, arrows_at=())
    fork_end, f = r.p, r.f
    rt = right_of(f)
    r.w = 60.0
    R = 350.0
    r.turn("Detour", -60, R, rails=True)
    R2.lay_strips(r, 40, 330, every=60, lanes=2)
    road(r, "Detour Run", 200, w=60)
    r.along(punch, [100], i0=0)
    r.turn("Detour Turn", 120, R, rails=True, cp=True)
    r.along(sweep_arm, [200, 520], i0=0)
    road(r, "Detour Run 2", 200, w=60)
    r.along(punch, [100], i0=2)
    r.turn("Detour Back", -60, R, rails=True)
    for d in (0.2, 0.5, 0.8):
        p, ff = at_road(r, d * 360)
        crate_stacks(b, p, ff, 60, rng, n=3)
    r.w = 240.0
    merge0 = r.p
    road(r, "Merge Deck", 160, w=240, cp=True, boosts=3, every=40, arrows_at=(80,))
    # the shortcut, straight on behind the cracked wall
    a = add(fork_end, mul(rt, -80))
    al = Alt(r, a, f, 50, B=260.0)
    accent(b, (230, 200, 160))
    brick_wall(b, add(a, mul(f, 4)), f, 46, h=30.0, kind="brick", speed=140.0)
    for k in range(3):
        lamp(b, add(a, add(mul(rt, -12 + 12 * k), (0, 34, 0))), col=(90, 255, 140), d=4.0, pulse=0.7)
    al.r.straight("Hidden Shortcut", dot(sub(merge0, a), f), lead=5.0, rails=True, line=False)
    R2.lay_strips(al.r, 40, dot(sub(merge0, a), f) - 40, every=80, lanes=1)
    al.done()
    accent(b, col)
    # 4. the wall gauntlet: brick walls between punching pistons
    r.w = W
    road(r, "Wall Gauntlet", 480, w=W, dy=25, cp=True)
    R2.lay_strips(r, 20, 460, every=45, lanes=3)
    for d in (90, 250, 410):
        p, ff = at_road(r, d)
        brick_wall(b, p, ff, W - 4, h=28.0, kind="brick")
    r.along(punch, [170, 330], i0=1)
    # 5. reinforced maze: weave between the gates
    road(r, "Reinforced Maze", 420, w=W, cp=True)
    R2.lay_strips(r, 20, 400, every=50, lanes=3)
    for d, pat in ((80, "gbg"), (170, "bbg"), (260, "gbg"), (350, "gbb")):
        lane_row(r, d, W, pat, kind="brick")
    road(r, "Launch Run", 160, w=W, boosts=3, every=35, arrows_at=(80,))
    R2.ramp_jump(r, "Smash Launch", deg=20, drop=60, w_land=110, slope=3, land_min=320, cp=True)
    p, ff = at_road(r, 250)
    brick_wall(b, p, ff, 106, h=26.0, kind="crate", nx=9)
    # 6. the debris field: crate walls to smash on the way out
    road(r, "Debris Field", 320, w=110, boosts=3, every=40, cp=True)
    for d in (80, 170):
        p, ff = at_road(r, d)
        brick_wall(b, p, ff, 106, h=26.0, kind="crate", nx=9)
        crate_stacks(b, p, ff, 110, rng)
    r.log("end")
    return ["Crate Alley", "Barricade Run", "Hidden Shortcut", "Detour", "Wall Gauntlet", "Reinforced Maze", "Smash Launch"]


# ===================================================================== 12. the final gauntlet and the finish
def finish_arch(b, c, f, w):
    """The finish: a huge steel arch over the line, chasing lights, turning gears, beacons and fireworks."""
    rt = right_of(f)
    H = 150.0
    span = w + 70
    fr = deck_frame(c, f)
    for s_ in (-1, 1):
        q = add(c, mul(rt, s_ * span / 2))
        Pt(b, "ArchPillar", CF(add(q, (0, H / 2 - 30, 0)), fr.x, fr.y, fr.z), (22, H + 60, 30), STEEL, "DiamondPlate", b.scenery,
           collide=True)
        stripe_box(b, "PillarStripe", CF(add(q, (0, 12, 0)), fr.x, fr.y, fr.z), (22.6, 24, 30.6), collide=True)
        for k in range(8):
            lamp(b, add(q, add(mul(rt, -s_ * 11.6), (0, 20 + k * 16, 0))), col=[(255, 230, 90), (255, 90, 60)][k % 2], d=5.0,
                 pulse=0.5 + 0.08 * k)
        big_gear(b, add(q, (0, H + 26, 0)), 34, f, ACC["final"], spin=0.12 * s_)
        cyl(b, "Beacon", add(q, (0, H + 70, 0)), 10, 10, (255, 230, 90), "Neon", b.scenery)
        for k in range(6):
            a = TAU * k / 6
            d = unit((math.cos(a) * 0.5, 1.0, math.sin(a) * 0.5))
            ball(b, "Firework", add(add(q, (0, H + 90, 0)), mul(d, 26)), 5, [(255, 80, 80), (80, 200, 255), (255, 230, 90)][k % 3],
                 "Neon", b.scenery)
    top = add(c, (0, H, 0))
    Pt(b, "ArchBeam", CF(top, fr.x, fr.y, fr.z), (span + 22, 26, 30), STEEL_DK, "Metal", b.scenery)
    stripe_box(b, "ArchStripe", CF(add(top, (0, -13.4, 0)), fr.x, fr.y, fr.z), (span + 18, 1, 30.4))
    Pt(b, "ArchSign", CF(add(top, add(mul(f, -15.4), (0, 0, 0))), fr.x, fr.y, fr.z), (span * 0.7, 18, 0.6), ACC["final"], "Neon",
       b.scenery)
    n = 16
    for k in range(n):
        q = add(top, add(mul(rt, -span / 2 + span * (k + 0.5) / n), (0, -16, 0)))
        lamp(b, q, col=[(255, 230, 90), (255, 255, 255), (255, 90, 60)][k % 3], d=4.0, pulse=0.4 + 0.05 * (k % 5))
    # chequered banners hanging from the beam
    for s_ in (-1, 1):
        q = add(top, add(mul(rt, s_ * span * 0.3), (0, -40, 0)))
        stripe_box(b, "Banner", CF(q, fr.x, fr.y, fr.z), (22, 50, 0.6), tile=5.0)


def medley(b, c, w, i):
    """One of every machine on the course, in turn: the final exam."""
    fns = [crusher_v, side_hammer, sweep_arm, punch, wrecking_ball, crusher_v]
    fns[i % len(fns)](b, c, w, i)


def slot10(r, sk, rng):
    b = r.b
    sk.title = "Final Gauntlet"
    b.gate_label = "STAGE 10"
    b.final_slot = True
    col = ACC["final"]
    accent(b, col)
    W = 80.0
    road(r, "Gauntlet Approach", 160, w=W, cp=True, boosts=2, every=40, arrows_at=(80,))
    # 1. the collapsing straight
    R2.sink_board(r, "Collapsing Straight", 280, W, cell=40.0, cols=(col, mix(col, (0, 0, 0), 0.45)),
                  mats=("SmoothPlastic", "SmoothPlastic"), delay=0.3, rate=95.0)
    road(r, "Collapse Pier", 60, w=W)
    tilt_deck(r, "Final Tilt", 150, W, amp_deg=9, period=3.4)
    road(r, "Collapse Pier 2", 60, w=W, cp=True)
    retract_deck(r, "Final Retract", 130, W, phase=0.3)
    road(r, "Collapse Pier 3", 50, w=W)
    R2.sink_board(r, "Collapsing Straight 2", 200, W, cell=40.0, cols=(col, mix(col, (0, 0, 0), 0.45)),
                  mats=("SmoothPlastic", "SmoothPlastic"), delay=0.28, rate=100.0)
    # 2. the hammer medley
    road(r, "Hammer Medley", 720, w=W, dy=50, cp=True)
    for k, d in enumerate((90, 200, 310, 420, 530, 640)):
        r.along(medley, [d], i0=k)
    _corridor_shell(r, 0, W, rng)
    # 3. the rotating bridges
    road(r, "Bridge Pier", 80, w=W, cp=True)
    swing_span(r, "Final Swing", 280, w=56, period=3.6, ease=1.2)
    pier(r, "Final Pier", 60, w=W)
    seesaw(r, "Final See-Saw", 220, w=60, amp_deg=10, period=4.0, hold=1.8)
    pier(r, "Final Pier 2", 70, w=W, cp=True)
    # 4. the narrow jumps
    o = O.Obby(r, 260)
    o.plat("Narrow Deck", 80, 40)
    o.kick(0, label="Narrow Jump")
    o.plat("Narrow Beam", 90, 20)
    o.kick(0, label="Narrow Jump 2")
    o.plat("Narrow Landing", 60, 50, cp=True)
    road(r, "Last Plates", 260, w=W)
    r.along(crusher_plates, [90, 190], i0=2)
    # 5. the boost run to the giant ramp
    r.w = 110.0
    road(r, "Final Boost", 420, w=110, dy=60, boosts=3, every=35, cp=True, arrows_at=(100, 300, 400))
    for d in (60, 200, 340):
        gantry(b, r.ahead(d - 420), r.f, 110, h=46)
    R2.ramp_jump(r, "Final Ramp", deg=26, drop=110, w_land=160, slope=3, land_min=360, cp=True)
    kind, lip, tgt, H, V = [j for j in b.jumps if j[0] == "ramp"][-1]
    f = r.f
    land_end = r.p
    Lr = last_len(r)
    land0 = sub(land_end, mul(f, Lr))
    # ---- the lower recovery route: a deck under the flight catches a short jump; a pad throws it back up
    rec_y = land0[1] - 120.0
    a = add(lip, add(mul(f, 140.0), (0, rec_y - lip[1], 0)))
    al = Alt(r, a, f, 160, B=230.0)
    accent(b, (255, 200, 120))
    al.o.plat("Recovery Deck", 200, 160)
    up = land0[1] - 0.03 * 200 - al.r.p[1]
    lo, hi = al.o.pad_range(up)
    tgt_d = dot(sub(add(land0, mul(f, Lr * 0.6)), al.r.p), f)
    al.o.plat("Recovery Run", max(40.0, tgt_d - (lo + hi) / 2), 120)
    al.o.pad(up, side=0)
    al.done()
    accent(b, col)
    road(r, "Victory Lane", 300, w=140, boosts=2, every=50)
    for d in (40, 120, 200, 280):
        gantry(b, r.ahead(d - 300), r.f, 140, h=50)
        for s_ in (-1, 1):
            q = r.ahead(d - 300, side=s_ * 82)
            cyl(b, "VictoryPole", add(q, (0, 30, 0)), 60, 3, STEEL_LT, "Metal", b.scenery)
            ball(b, "Firework", add(q, (0, 64, 0)), 7, [(255, 80, 80), (80, 200, 255), (255, 230, 90)][(d // 80) % 3], "Neon",
                 b.scenery)
    r.log("end")
    return ["Collapsing Straight", "Hammer Medley", "Final Swing", "Final See-Saw", "Narrow Jumps", "Final Boost",
            "Final Ramp", "Recovery Deck", "Finish Arch"]


LEVELS = {1: slot1, 2: slot2, 3: slot3, 4: slot4, 5: slot5, 6: slot6, 7: slot7, 8: slot8, 9: slot9, 10: slot10}
FINAL = {}
