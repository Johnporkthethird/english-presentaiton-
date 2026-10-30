"""Obby 2, the Extreme Speedway: levels 11-20 (the game's course 2), one continuous stunt course high in the sky.

Dark metal roads with neon orange and electric-blue edges, glowing boost strips, giant rings on the jump lines. No
background scenery: just the course in the sky. It is about speed: huge ramps, chained jumps, three-way splits,
risky shortcuts, near misses. Nothing waits: no presses, no lifts that crawl, no doors.

Main route: the racing line. Alternate routes are laid by their own turtles (mech.Alt) and add no racing line; their
jumps are recorded, so the validator flies them too. Coin clusters (parts marked CoinSpot) sit on the risky lines and
in the hard rings; the game's coin layer puts a coin on each.
"""
import math
from geom import CF, deck_frame, axis_frame, add, sub, mul, unit, cross, dot, rot_y, UP
from builder import G, CAR_UP, X0, Y0, ZC
import route as RT
import rush2 as R2
import obby as O
import mech as MX
from skins import Skin, Pt, box, cyl, ball, samples
from worlds import ringz
import journey_skins  # noqa: F401  (road_piece etc. on the base skin)

TAU = math.pi * 2
DARK, DARK2, METAL = (28, 31, 40), (18, 20, 26), (70, 76, 90)
ROAD = (34, 38, 50)
ORANGE, BLUE, WHITE = (255, 120, 20), (30, 170, 255), (240, 244, 250)
GREEN, YELLOW, RED = (60, 230, 110), (255, 210, 40), (255, 60, 50)
ROCK = [(150, 82, 52), (126, 66, 44), (170, 100, 66), (104, 56, 40)]
V_TOP = R2.V_TOP


def right_of(f):
    return mul(RT.left_of(f), -1)


def _axes(z):
    z = unit(z)
    x = unit(cross(UP, z))
    return (x, cross(z, x), z)


# ===================================================================== the skin
class Speedway(Skin):
    key, title, theme_name = "speedway", "Extreme Speedway", "Extreme speedway"
    clock, bloom, hue, scale = 17.4, 0.7, 0.06, 1.0
    body, top, edge, padc, danger = DARK, ROAD, ORANGE, BLUE, RED
    body_mat, top_mat = "Metal", "SmoothPlastic"
    gate_post, gate_board, gate_text = DARK, (16, 18, 24), ORANGE
    finish_cols = ((245, 245, 245), (20, 20, 24))
    light_over = {"Lt_Atmosphere_Density": 0.22, "Lt_Atmosphere_Haze": 0.9}
    glow = ORANGE  # the neon edge colour (orange or blue, per stage)

    def road_style(self):
        return dict(top=self.top, top_mat="SmoothPlastic", edge=self.glow, edge_mat="Neon", side=DARK, side_mat="Metal",
                    refl=0.1, center=None)

    def road_piece(self, b, parent, fr, w, L, name):
        F = lambda p: CF(p, fr.x, fr.y, fr.z)
        o = lambda x=0.0, y=0.0, z=0.0: add(fr.p, add(add(mul(fr.x, x), mul(fr.y, y)), mul(fr.z, z)))
        Pt(b, name, F(o(y=-2.0)), (w, 4, L), self.top, "SmoothPlastic", parent, collide=True, refl=0.1)
        for k in (-1, 1):
            Pt(b, "NeonEdge", F(o(x=k * (w / 2 - 1.0), y=0.06)), (1.6, 0.12, L), self.glow, "Neon", parent)
            Pt(b, "EdgeLine", F(o(x=k * (w / 2 - 4.0), y=0.06)), (0.8, 0.12, L), WHITE, "SmoothPlastic", parent)
            Pt(b, "RoadSide", F(o(x=k * (w / 2 + 0.5), y=-3.5)), (1.0, 7, L), DARK, "Metal", parent)
        Pt(b, "Belly", F(o(y=-6.0)), (w * 0.6, 2, L), DARK2, "Metal", parent)
        nl = 3 if w >= 90 else 2 if w >= 50 else 1
        for i in range(1, nl):
            x = -w / 2 + w * i / nl
            d = -L / 2 + 8
            while d < L / 2 - 6:
                Pt(b, "LaneDash", F(o(x=x, y=0.07, z=d)), (0.9, 0.14, 12), WHITE, "SmoothPlastic", parent)
                d += 34

    def under(self, b, top, w, i):
        """A slim tapered pylon under the road, with a neon band."""
        if getattr(b, "no_under", False):
            return
        x, y, z = top
        cyl(b, "Pylon", (x, y - 50, z), 92, 7, DARK, "Metal")
        cyl(b, "PylonFoot", (x, y - 120, z), 50, 4, DARK2, "Metal")
        cyl(b, "PylonBand", (x, y - 20, z), 2, 8, self.glow, "Neon")
        Pt(b, "PylonCap", CF((x, y - 6, z)), (8, 3, w * 0.5), DARK2, "Metal", b.scenery)

    def pad_art(self, b, start, f):
        fr = deck_frame(start, f)
        for k in range(3):
            q = add(start, mul(f, -8 + k * 8))
            Pt(b, "PadChevron", CF(add(q, (0, 0.2, 0)), fr.x, fr.y, fr.z), (16, 0.2, 3), BLUE, "Neon")

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        self.road_piece(b, parent or b.roads, deck_frame((cx, y, z), (1, 0, 0)), w, L, "Deck")
        samples(b, x0, x1, y, z, w)

    def finish(self, b, x0, x1, y, z, w):
        if getattr(b, "final_slot", False):
            Skin.finish(self, b, x0, x1, y, z, w)

    def environment(self, b):
        pass


def tint(b, col):
    """The stage's own colours: the course-wide orange and blue become this stage's neon and its second colour."""
    if col == ORANGE and getattr(b, "stage_glow", None):
        return b.stage_glow
    if col == BLUE and getattr(b, "stage_glow2", None):
        return b.stage_glow2
    return col


def accent(b, top=None, glow=None):
    if top is not None:
        b.skin.top = top
    if glow is not None:
        b.skin.glow = glow


# ===================================================================== shared pieces
def road(r, label, L, w=None, dy=0.0, boosts=0, every=40.0, cp=False, arrows_at=(), lines=False, **kw):
    MX.road(r, label, L, w=w, dy=dy, boosts=boosts, every=every, cp=cp, arrows_at=arrows_at, **kw)
    if lines:
        speed_lines(r)
    return r


def speed_lines(r, every=60.0):
    """Long glowing streaks beside the road just laid (the speed look)."""
    b = r.b
    pts = r.last[0]
    cum = [0.0]
    for a_, c_ in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))
    d = 20.0
    k = 0
    while d < cum[-1] - 30:
        p, f = MX.at_road(r, d)
        w = r.last[1][0]
        rt = right_of(f)
        for s_ in (-1, 1):
            q = add(p, add(mul(rt, s_ * (w / 2 + 6)), (0, 6 + (k % 3) * 5, 0)))
            Pt(b, "SpeedLine", CF(q, *_axes(f)), (0.5, 0.5, 34), [WHITE, tint(b, BLUE), b.skin.glow][k % 3], "Neon", b.scenery,
               transp=0.25)
        d += every
        k += 1


def giant_ring(b, c, R, axis, col=None, spin=0.0, th=10.0):
    """A giant floating ring: steel band, neon inner and outer glow, light clamps."""
    col = tint(b, col or b.skin.glow)
    import showcase as SC
    rig = SC.spin(b, c, axis, spin, 0.0, "RingSpin") if spin else b.scenery
    ringz(b, c, R, METAL, "Metal", th=th, axis=axis, parent=rig, name="GiantRing")
    ringz(b, c, R - th * 0.45, col, "Neon", th=th * 0.5, axis=axis, parent=rig, name="RingGlow")
    ringz(b, c, R + th * 0.4, WHITE, "Neon", th=th * 0.3, axis=axis, parent=rig, name="RingRim")
    a = unit(axis)
    e1 = unit(cross(a, UP)) if abs(a[1]) < 0.9 else (1.0, 0.0, 0.0)
    e2 = cross(a, e1)
    for k in range(6):
        t = TAU * k / 6
        d = add(mul(e1, math.cos(t)), mul(e2, math.sin(t)))
        ball(b, "RingLight", add(c, mul(d, R + th * 0.6)), th * 0.9, [tint(b, BLUE), tint(b, ORANGE)][k % 2], "Neon", rig)


def flight(lip, H, V, t):
    """Where a flight from lip at horizontal speed H along its heading (filled in by the caller) is after t."""
    return (H * t, V * t - G * t * t / 2)


def ring_on_jump(b, kind_pick=-1, frac=0.5, R=60.0, col=None, high=None, coins=False, side=0.0):
    """A giant ring on the flight of the last recorded jump of kind_pick: at frac of the flight's horizontal reach,
    centred on the nominal flight (high: raised by that much above it, a harder line; side: moved sideways)."""
    j = b.jumps[kind_pick]
    kind, lip, tgt, H, V = j
    f = RT.flat(sub(tgt, lip))
    # the nominal flight lands at tgt: solve its time, then take frac of it
    dy = tgt[1] - lip[1]
    T = (V + math.sqrt(max(V * V + 2 * G * dy, 0.0))) / G
    t = T * frac
    x, y = flight(lip, H, V, t)
    c = add(lip, add(mul(f, x), (0, y + CAR_UP + (high or 0.0), 0)))
    c = add(c, mul(right_of(f), side))
    giant_ring(b, c, R, f, col=col)
    if coins:
        coin_ring(b, c, f, R * 0.45)
    return c


def coin_spot(b, p):
    b.part("CoinSpot", CF(p), (2, 2, 2), (255, 206, 66), parent=b.scenery, transp=1, collide=False, query=False,
           attrs={"CoinSpot": True})


def coin_ring(b, c, f, R, n=6):
    """A circle of coin spots in a ring (the reward for flying through it)."""
    a = unit(f)
    e1 = unit(cross(a, UP))
    e2 = cross(a, e1)
    for k in range(n):
        t = TAU * k / n
        coin_spot(b, add(c, add(mul(e1, math.cos(t) * R), mul(e2, math.sin(t) * R))))
    coin_spot(b, c)


def coin_line(b, p0, p1, n=5, up=6.0):
    for k in range(n):
        q = R2.lerp3(p0, p1, (k + 0.5) / n)
        coin_spot(b, add(q, (0, up, 0)))


def coin_arc(b, lip, d, V, n=6, t0=0.15, t1=0.85, T=None):
    """Coins along a flight from lip with velocity V*d (a jump's arc)."""
    vx, vy, vz = mul(d, V)
    T = T or 2 * vy / G
    for k in range(n):
        t = T * (t0 + (t1 - t0) * k / max(n - 1, 1))
        coin_spot(b, (lip[0] + vx * t, lip[1] + vy * t - G * t * t / 2 + CAR_UP + 2, lip[2] + vz * t))


def neon_arch(b, c, f, w, col, h=40.0, label_col=None):
    """A bright arch over the road (route colours, milestones)."""
    col = tint(b, col)
    rt = right_of(f)
    fr = deck_frame(c, f)
    for s_ in (-1, 1):
        q = add(c, mul(rt, s_ * (w / 2 + 5)))
        Pt(b, "ArchPost", CF(add(q, (0, h / 2, 0)), fr.x, fr.y, fr.z), (5, h, 5), DARK, "Metal", b.scenery)
        Pt(b, "ArchPostGlow", CF(add(q, add(mul(rt, -s_ * 2.6), (0, h / 2, 0))), fr.x, fr.y, fr.z), (0.4, h - 4, 3), col,
           "Neon", b.scenery)
    Pt(b, "ArchBeam", CF(add(c, (0, h + 2, 0)), fr.x, fr.y, fr.z), (w + 16, 5, 6), DARK, "Metal", b.scenery)
    Pt(b, "ArchGlow", CF(add(c, (0, h - 0.8, 0)), fr.x, fr.y, fr.z), (w + 10, 0.6, 5), col, "Neon", b.scenery)
    # a big chevron sign pointing on
    import parkour as V2
    V2.chevron(b, add(c, (0, h + 9, 0)), f, min(26.0, w * 0.6), col)


def milestone(b, c, f, w):
    """A milestone: an orange-and-blue arch with firework lights."""
    neon_arch(b, c, f, w, ORANGE, h=48.0)
    rt = right_of(f)
    for s_ in (-1, 1):
        q = add(c, add(mul(rt, s_ * (w / 2 + 5)), (0, 54, 0)))
        for k in range(5):
            a = TAU * k / 5
            d = unit((math.cos(a) * 0.6, 1.0, math.sin(a) * 0.6))
            MX.lamp(b, add(q, mul(d, 9)), col=[ORANGE, BLUE, WHITE][k % 3], d=3.5, pulse=0.5 + 0.1 * k)


# every stage its own look: road tint, neon, and the second colour its machines wear
THEMES = {
    11: ((34, 36, 46), ORANGE, (255, 210, 120)),      # boost blast: graphite and fire orange
    12: ((24, 32, 54), BLUE, WHITE),                  # splitter: navy and electric blue
    13: ((38, 24, 52), (255, 60, 170), (90, 220, 255)),  # pinball: a purple table, magenta and cyan lights
    14: ((28, 40, 56), (40, 225, 255), WHITE),        # skyline: steel blue and cyan
    15: ((34, 28, 54), (150, 90, 255), ORANGE),       # rolling thunder: violet
    16: ((50, 34, 30), (255, 80, 30), (255, 190, 90)),  # cracking canyon: rust and lava
    17: ((26, 42, 36), (120, 255, 90), BLUE),         # mega ramp cascade: lime
    18: ((16, 16, 22), (255, 40, 60), (255, 80, 200)),  # laser slalom: black and laser red
    19: ((42, 36, 24), (255, 200, 40), ORANGE),       # speed frenzy: gold
    20: ((30, 34, 46), WHITE, ORANGE),                # grand finale: white light
}


def stage(r, sk, title, label, top, glow):
    """Name the stage and dress it in its own colours (THEMES by level; top and glow are the fallback)."""
    b = r.b
    sk.title = title
    b.gate_label = label
    t = THEMES.get(b.level_id)
    if t:
        top, glow = t[0], t[1]
        b.stage_glow2 = t[2]
    else:
        b.stage_glow2 = WHITE
    b.stage_glow = glow
    sk.edge = glow
    sk.gate_text = glow
    accent(b, top, glow)


def finish_stage(r, rng):
    """Every stage ends here (no background scenery: just the course)."""
    pass


def end_on_line(r, label, margin=180.0):
    """A boosted run straight on towards the slot's end (short: the slot is filled by the stage itself)."""
    left = r.X1 - 110 - r.p[0] - margin
    if left > 60:
        road(r, label, left, boosts=2, every=50, lines=True)


# ===================================================================== 1. the boost blast
def slot11(r, sk, rng):
    b = r.b
    stage(r, sk, "Boost Blast", "OBBY 2 - STAGE 1", ROAD, ORANGE)
    # straight into it: a wide dive onto the boost strips
    road(r, "Drop-In", 220, w=130, dy=-40, boosts=3, every=28, arrows_at=(60, 170), lines=True)
    p_side, f = r.p, r.f
    rt = right_of(f)
    R2.ramp_jump(r, "Blast Ramp", deg=24, drop=110, w_land=150, slope=3, land_min=400, cp=True)
    ring_on_jump(b, frac=0.5, R=62.0, col=ORANGE)
    ring_on_jump(b, frac=0.42, R=30.0, col=BLUE, high=70.0, coins=True)
    blast = [j for j in b.jumps if j[0] == "ramp"][-1]
    land_end = r.p
    Lr = MX.last_len(r)
    land0 = sub(land_end, mul(f, Lr))
    # ---- the side ramp: off the left edge of the dive, a steeper kicker onto a sky shortcut that skips the carve
    a = add(sub(p_side, mul(f, 140)), add(mul(rt, -100), (0, 35, 0)))
    al = MX.Alt(r, a, f, 34, B=330.0)
    accent(b, glow=BLUE)
    al.r.straight("Side Ramp Run", 140, dy=-35, lead=20.0, rails=True, line=False)
    R2.lay_strips(al.r, 10, 130, every=25, lanes=1)
    lip, d = R2.kicker(al.r, "Side Ramp", 30.0, L=40.0, w=34, rails=False)
    sky_y = land0[1] + 60
    ps = [R2.fly(lip, mul(d, v), lambda p: sky_y)[0] for v in (0.9 * V_TOP, V_TOP)]
    near = min(dot(sub(q, lip), f) for q in ps)
    far = max(dot(sub(q, lip), f) for q in ps)
    s0 = add(lip, add(mul(f, near - 60), (0, sky_y - lip[1], 0)))
    b.jumps.append(("ramp", lip, ps[1], V_TOP * math.hypot(d[0], d[2]), V_TOP * d[1]))
    coin_arc(b, lip, d, V_TOP, n=7)
    al2 = MX.Alt(r, s0, f, 50, B=300.0)
    b.no_under = True  # (the sky shortcut passes over the carve: no pylons through it)
    al2.r.straight("Sky Shortcut", far - near + 220, lead=5.0, rails=True, line=False)
    R2.lay_strips(al2.r, 40, far - near + 200, every=50, lanes=1)
    b.no_under = False
    al.done()
    accent(b, glow=b.stage_glow)
    # the carve: a banked S at full boost (the sky shortcut drops back in after it)
    r.turn("Boost Carve", 20, 420, rails=True)
    r.turn("Boost Carve 2", -40, 420, rails=True)
    R2.lay_strips(r, 30, 260, every=45, lanes=2)
    r.turn("Boost Carve 3", 20, 420, rails=True)
    r.w = 140.0
    rejoin = r.p
    road(r, "Rejoin Run", 170, w=140, boosts=3, every=40, cp=True, arrows_at=(100,), lines=True)
    up = al2.r.p[1] - rejoin[1]
    gap = dot(sub(rejoin, al2.r.p), f)
    b.no_under = True
    if gap > 240:
        al2.r.straight("Sky Shortcut Run", gap - 200, lead=5.0, rails=True, line=False)
    al2.o.plat("Sky Shortcut End", 30, 50)
    b.no_under = False
    al2.o.drop(up, side=dot(sub(rejoin, al2.r.p), rt) * 0.9)
    al2.done()
    # ---- the canyon gap
    R2.ramp_jump(r, "Canyon Gap", deg=18, drop=50, w_land=130, slope=3, land_min=300, cp=True)
    ring_on_jump(b, frac=0.55, R=52.0, col=BLUE)
    ring_on_jump(b, frac=0.6, R=26.0, col=ORANGE, side=60.0, high=30.0, coins=True)
    # ---- the boost ladder: two launch pads straight up onto higher decks, then a sky dive off the top
    o = O.Obby(r, 280)
    o.plat("Ladder Deck", 100, 90)
    for k in range(3):
        o.pad(110.0, label="Launch Pad %d" % (k + 1))
        o.plat("Ladder Deck %d" % (k + 1), 70, 90, cp=(k == 2))
    road(r, "Sky Dive Run", 100, w=110, boosts=3, every=30, arrows_at=(110,))
    R2.drop_off(r, "Sky Dive", 120.0, w=120, cp=True)
    MX.arrows(r, (60, 400))
    # ---- the last blast: a dive into the biggest ring of the stage
    road(r, "Rocket Run", 170, w=110, dy=47, boosts=3, every=26, lines=True)
    R2.ramp_jump(r, "Rocket Ramp", deg=22, drop=40, w_land=130, slope=3, land_min=320, cp=True)
    ring_on_jump(b, frac=0.5, R=70.0, col=ORANGE)
    ring_on_jump(b, frac=0.5, R=90.0, col=BLUE)
    end_on_line(r, "Blast Out")
    finish_stage(r, rng)
    r.log("end")
    return ["Drop-In", "Blast Ramp", "Side Ramp Shortcut", "Boost Carve", "Canyon Gap", "Launch Pads", "Sky Dive",
            "Rocket Ramp"]


# ===================================================================== 2. the split-second splitter
def lane_block(b, c, f, w, lane, col=RED, h=10.0):
    """A low glowing barrier closing one lane (lane -1 left, 0 centre, 1 right) of a road w wide."""
    rt = right_of(f)
    q = add(c, mul(rt, lane * w / 3))
    fr = deck_frame(q, f)
    Pt(b, "LaneBarrier", CF(add(q, (0, h / 2, 0)), fr.x, fr.y, fr.z), (w / 3 - 4, h, 4), DARK, "Metal", b.scenery,
       collide=True)
    Pt(b, "BarrierGlow", CF(add(q, (0, h + 0.4, 0)), fr.x, fr.y, fr.z), (w / 3 - 4, 0.8, 4.4), col, "Neon", b.scenery)
    Pt(b, "BarrierFace", CF(add(q, add(mul(f, -2.3), (0, h / 2, 0))), fr.x, fr.y, fr.z), (w / 3 - 6, h - 3, 0.4), col, "Neon",
       b.scenery, transp=0.3)


def slot12(r, sk, rng):
    b = r.b
    stage(r, sk, "Splitter", "OBBY 2 - STAGE 2", ROAD, BLUE)
    road(r, "Splitter Approach", 180, w=110, boosts=3, every=30, arrows_at=(90,), lines=True)
    r.w = 380.0
    road(r, "Split Plaza", 140, w=380, cp=True)
    p0, f = r.p, r.f
    rt = right_of(f)
    for side, col in ((-130, GREEN), (0, YELLOW), (130, RED)):
        neon_arch(b, add(sub(p0, mul(f, 20)), mul(rt, side)), f, 70 if side else 60, col, h=34)
    # ---- the middle line (the racing line): fast, closely spaced jumps
    accent(b, glow=YELLOW)
    o = O.Obby(r, 280)
    o.plat("Hop Deck", 60, 60)
    o.kick(0, side=0, label="Hop 1")
    o.plat("Hop Deck 1", 60, 56)
    o.kick(0, side=24, label="Hop 2")
    o.plat("Hop Deck 2", 60, 52)
    o.drop(30, side=-24, label="Hop 3")
    o.plat("Hop Deck 3", 60, 52, cp=True)
    o.pad(36, label="Hop 4")
    o.plat("Hop Deck 4", 60, 56)
    o.kick(0, side=-20, label="Hop 5")
    o.plat("Hop Deck 5", 60, 56)
    o.drop(36, side=20, label="Hop 6")
    o.plat("Hop Landing", 40, 70)
    accent(b, glow=b.stage_glow)
    r.w = 380.0
    merge0 = r.p
    road(r, "Merge Plaza", 160, w=380, cp=True, boosts=3, every=40, arrows_at=(80,))
    after0 = r.p
    # ---- what comes after the merge (laid now, so the risky route knows where to come down)
    r.w = 170.0
    road(r, "Merge Run", 240, w=170, dy=40, boosts=3, every=40, lines=True)
    # ---- the safe route (left): wide, gentle, one small drop
    al = MX.Alt(r, add(p0, mul(rt, -130)), f, 70, B=240.0)
    accent(b, glow=GREEN)
    al.r.turn("Safe Swing", -12, 700, rails=True, line=False)
    al.r.turn("Safe Swing 2", 12, 700, rails=True, line=False)
    R2.lay_strips(al.r, 40, 260, every=70, lanes=2)
    to = dot(sub(merge0, al.r.p), f)
    dyy = merge0[1] - al.r.p[1]
    al.r.straight("Safe Run", to, dy=dyy, lead=60.0, rails=True, line=False)
    al.done()
    # ---- the risky route (right): narrow ramps, giant gaps, and it comes down past the merge
    al = MX.Alt(r, add(p0, mul(rt, 130)), f, 26, B=330.0)
    accent(b, glow=RED)
    al.o.plat("Risk Lane", 50, 26)
    al.o.kick(0, label="Risk Gap")
    al.o.plat("Risk Beam", 50, 20)
    al.o.kick(0, side=-10, label="Risk Gap 2")
    p_r = al.r.p
    coin_line(b, p_r, add(p_r, mul(f, 50)), n=3)
    al.o.plat("Risk Beam 2", 50, 20)
    al.o.kick(0, side=10, label="Risk Gap 3")
    al.o.plat("Risk Runway", 0, 26)
    up_y = after0[1] + 60 - al.r.p[1]
    to = dot(sub(after0, al.r.p), f) - 60
    al.r.straight("Risk Rail", max(60.0, to), dy=up_y, lead=40.0, rails=True, line=False)
    R2.lay_strips(al.r, 20, max(60.0, to) - 20, every=60, lanes=1)
    al.o.plat("Risk End", 30, 26)
    al.o.drop(60.0, side=dot(sub(after0, al.r.p), right_of(f)) * 0.9)
    al.done()
    accent(b, glow=b.stage_glow)
    # ---- the crossover: the road splits again round a giant pylon; the high way crosses over the low way
    r.w = 200.0
    road(r, "Crossover Fork", 100, w=200, cp=True)
    fork, f = r.p, r.f
    r.w = 60.0
    q0 = r.p
    r.turn("Low Way", 22, 420, rails=True)
    r.turn("Low Way 2", -44, 420, rails=True)
    R2.lay_strips(r, 30, 300, every=60, lanes=2)
    r.turn("Low Way 3", 22, 420, rails=True)
    r.w = 200.0
    join = r.p
    road(r, "Crossover Join", 120, w=200, boosts=3, every=40, cp=True)
    # the high way: mirrored, up and over the low way where they cross
    al = MX.Alt(r, add(fork, mul(rt, 60)), f, 50, B=280.0)
    accent(b, glow=ORANGE)
    b.no_under = True
    al.r.turn("High Way", -22, 420, dy=40, rails=True, line=False)
    al.r.turn("High Way 2", 44, 420, rails=True, line=False)
    al.r.turn("High Way 3", -22, 420, dy=-30, rails=True, line=False)
    b.no_under = False
    al.r.straight("High Way End", dot(sub(join, al.r.p), f), dy=join[1] - al.r.p[1], lead=40.0, rails=True, line=False)
    al.done()
    big = add(add(fork, mul(f, 2 * 420 * math.sin(math.radians(22)) * 1.0)), (0, -260, 0))
    cyl(b, "CrossPylon", big, 380, 40, DARK, "Metal", b.scenery)
    cyl(b, "CrossPylonGlow", add(big, (0, 150, 0)), 6, 44, ORANGE, "Neon", b.scenery)
    accent(b, glow=b.stage_glow)
    # ---- the lane dash: barriers close one side lane at a time, the centre stays open
    road(r, "Lane Dash", 420, w=120, dy=54, boosts=3, every=45, cp=False, lines=True)
    for k, d in enumerate((70, 150, 230, 310, 390)):
        p, ff = MX.at_road(r, d)
        lane_block(b, p, ff, 120, -1 if k % 2 == 0 else 1)
    # ---- the commit jump: three lanes of landing, a ring over each
    road(r, "Commit Run", 120, w=120, boosts=3, every=30, arrows_at=(60,))
    R2.ramp_jump(r, "Commit Jump", deg=22, drop=60, w_land=160, slope=3, land_min=320, cp=True)
    ring_on_jump(b, frac=0.5, R=58.0, col=BLUE)
    ring_on_jump(b, frac=0.5, R=28.0, col=RED, side=70.0, high=25.0, coins=True)
    ring_on_jump(b, frac=0.5, R=28.0, col=GREEN, side=-70.0, high=25.0, coins=True)
    end_on_line(r, "Splitter Out")
    finish_stage(r, rng)
    r.log("end")
    return ["Three-Way Split", "Hop Line", "Safe Route", "Risky Route", "Crossover", "Lane Dash", "Commit Jump"]


# ===================================================================== 3. the giant pinball run
def pop_bumper(b, c, d=22.0, col=None):
    """A padded pinball bumper on the road: touch it and it bounces you away."""
    col = tint(b, col or ORANGE)
    cyl(b, "PopBumper", add(c, (0, 6, 0)), 12, d, WHITE, "SmoothPlastic", b.hazards, query=True,
        attrs={"ObbyHazard": "Knock"})
    cyl(b, "BumperRing", add(c, (0, 6, 0)), 3, d + 1.4, METAL, "Metal", b.scenery, refl=0.4)
    cyl(b, "BumperBand", add(c, (0, 9.6, 0)), 1.4, d + 0.6, col, "Neon", b.scenery)
    cyl(b, "BumperCap", add(c, (0, 12.4, 0)), 1.2, d * 0.8, col, "Neon", b.scenery)
    ball(b, "BumperDome", add(c, (0, 13.2, 0)), d * 0.45, WHITE, "Glass", b.scenery, transp=0.2)
    cyl(b, "BumperSkirt", add(c, (0, 1.2, 0)), 2.4, d + 4, col, "Neon", b.scenery)
    cyl(b, "BumperBase", add(c, (0, 0.3, 0)), 0.6, d + 8, DARK, "Metal", b.scenery)
    for k in range(4):
        a = TAU * k / 4 + 0.4
        ball(b, "BumperStud", add(c, (math.cos(a) * (d / 2 + 3), 1.6, math.sin(a) * (d / 2 + 3))), 2.0, METAL, "Metal",
             b.scenery)


def bumper_field(r, spots, w, rng):
    """Bumpers on the road just laid at (distance, lateral) spots, kept clear of the racing line in the middle."""
    for k, (d, lat) in enumerate(spots):
        lat = max(-(w / 2 - 34), min(w / 2 - 34, lat))  # (off the slingshot banks at the edges)
        p, f = MX.at_road(r, d)
        pop_bumper(r.b, add(p, mul(right_of(f), lat)), d=rng.uniform(18, 26), col=[ORANGE, BLUE, WHITE][k % 3])


def sling_banks(r, w, every=140.0, L=110.0):
    """Slingshot banks: sloped strips along both edges of the road just laid that turn a car back into the field."""
    b = r.b
    pts = r.last[0]
    tot = sum(math.dist(a_, c_) for a_, c_ in zip(pts, pts[1:]))
    d = 60.0
    while d < tot - 60:
        p, f = MX.at_road(r, d)
        rt = right_of(f)
        for s_ in (-1, 1):
            q = add(p, add(mul(rt, s_ * (w / 2 - 12)), (0, 2.0, 0)))
            x_, y_, z_ = _axes(f)
            ang = math.radians(16) * s_
            yy = add(mul(y_, math.cos(ang)), mul(x_, -math.sin(ang)))
            xx = cross(yy, z_)
            Pt(b, "Ramp", CF(q, xx, yy, z_), (22, 4, L), DARK, "Metal", b.scenery, collide=True)
            Pt(b, "SlingGlow", CF(add(q, mul(yy, 2.1)), xx, yy, z_), (20, 0.2, L - 6), tint(b, [ORANGE, BLUE][int(d) // 140 % 2]),
               "Neon", b.scenery)
        d += every


def spinner(b, c, w, i, R=None, n=3, speed=0.16, side=1):
    """A big spinning star at the road's edge; its arms sweep across the road (gaps between them)."""
    x, y, z = c
    R = R or w * 0.75
    hub = (x, y + 9, z + side * (w / 2 - 6))  # (arms clear the rails as they sweep out over the edge)
    root = b.prop_root("Spinner")
    rig = b.rig(root, "Spin", axis_frame(hub, (0, 1, 0)), speed * (1 if i % 2 else -1), 1, phase=(i * 0.31) % 1,
                name="StarSpin")
    for k in range(n):
        a = TAU * k / n
        d = (math.cos(a), 0.0, math.sin(a))
        q = add(hub, mul(d, R / 2))
        Pt(b, "SpinnerArm", CF(q, cross(UP, d), UP, d), (6, 8, R), WHITE, "SmoothPlastic", rig, query=True,
           attrs={"ObbyHazard": "Knock"})
        Pt(b, "SpinnerStripe", CF(add(q, (0, 4.2, 0)), cross(UP, d), UP, d), (6.4, 0.4, R - 4), tint(b, [ORANGE, BLUE][k % 2]),
           "Neon", rig)
        ball(b, "SpinnerTip", add(hub, mul(d, R - 2)), 5, tint(b, BLUE), "Neon", rig)
    cyl(b, "SpinnerHub", hub, 12, 18, DARK, "Metal", rig, query=True, attrs={"ObbyHazard": "Knock"})
    cyl(b, "HubGlow", add(hub, (0, 6.2, 0)), 0.6, 14, tint(b, ORANGE), "Neon", rig)


def flippers(b, c, w, i, L=None, period=2.2):
    """A pair of flippers at the road's edges swinging in toward the middle in turn (squeeze between them)."""
    x, y, z = c
    L = L or w * 0.36
    for k, s_ in enumerate((-1, 1)):
        post = (x, y + 7, z + s_ * (w / 2 - 6))
        root = b.prop_root("Flipper")
        rig = b.rig(root, "Hinge", axis_frame(post, (0, 1, 0)), -50.0 * s_, period, phase=(k * 0.5 + i * 0.17) % 1,
                    keys="0:0 0.4:0 0.5:1 0.65:1 0.85:0", name="Flip")
        tip = add(post, (L * math.cos(math.radians(25)), 0, -s_ * L * math.sin(math.radians(25))))
        d = unit(sub(tip, post))
        Pt(b, "FlipperArm", CF(R2.lerp3(post, tip, 0.5), cross(UP, d), UP, d), (7, 7, L), WHITE, "SmoothPlastic", rig, query=True,
           attrs={"ObbyHazard": "Knock"})
        Pt(b, "FlipperGlow", CF(add(R2.lerp3(post, tip, 0.5), (0, 3.6, 0)), cross(UP, d), UP, d), (7.4, 0.3, L - 2),
           tint(b, [ORANGE, BLUE][k]), "Neon", rig)
        cyl(b, "FlipperPost", add(post, (0, -1, 0)), 14, 12, DARK, "Metal", b.scenery)


def slot13(r, sk, rng):
    b = r.b
    stage(r, sk, "Pinball Run", "OBBY 2 - STAGE 3", ROAD, ORANGE)
    # 1. the plunger: a narrow lane packed with strips, fired up onto the playfield
    road(r, "Plunger Lane", 200, w=40, boosts=1, every=20, arrows_at=(100,), lines=True)
    for d in (40, 120):
        MX.lamp(b, r.ahead(d - 200, side=-24, up=6), col=ORANGE, d=4.0, pulse=0.6)
        MX.lamp(b, r.ahead(d - 200, side=24, up=6), col=BLUE, d=4.0, pulse=0.6)
    R2.ramp_jump(r, "Plunger", deg=20, drop=30, w_land=200, slope=2, land_min=280, cp=True)
    ring_on_jump(b, frac=0.5, R=44.0, col=WHITE)
    # 2. the playfield: pop bumpers clear of the middle, slingshot banks on the edges
    road(r, "Playfield", 440, w=200, dy=-30, cp=False)
    bumper_field(r, [(50, -60), (80, 55), (130, -30), (160, 75), (200, 34), (240, -70), (280, -38), (310, 60),
                     (350, 30), (390, -55), (420, 70)], 200, rng)
    sling_banks(r, 200)
    # 3. spinners and flippers
    road(r, "Spinner Alley", 300, w=120, cp=True)
    r.along(spinner, [100], i0=0, side=1, R=78.0)
    r.along(spinner, [195], i0=1, side=-1, R=78.0)
    r.along(flippers, [288], i0=0)
    # 4. ramp shots: angled ramps fling the car left and right between raised platforms
    o = O.Obby(r, 290)
    o.plat("Shot Deck", 60, 70)
    o.kick(0, side=60, deg=18, label="Ramp Shot 1")
    o.plat("Shot Deck 1", 60, 64, cp=True)
    o.pad(50, side=-60, label="Ramp Shot 2")
    o.plat("Shot Deck 2", 60, 64)
    o.kick(0, side=60, deg=18, label="Ramp Shot 3")
    o.plat("Shot Deck 3", 60, 64)
    o.pad(50, side=-60, label="Ramp Shot 4")
    o.plat("Shot Deck 4", 90, 80, cp=True)
    # 5. the bumper bend: a banked curve, bumpers on the outside, a spinner at the apex
    r.w = 130.0
    r.turn("Bumper Bend", 28, 350, bank=10, rails=True)
    bumper_field(r, [(50, 45), (120, 50)], 130, rng)
    r.turn("Bumper Bend 2", -56, 350, bank=10, rails=True)
    bumper_field(r, [(70, -48), (170, -50), (270, -46)], 130, rng)
    R2.lay_strips(r, 40, 300, every=60, lanes=1)
    r.turn("Bumper Bend 3", 28, 350, bank=10, rails=True)
    # 6. the jackpot: a ramp shot into the jackpot ring
    road(r, "Jackpot Run", 140, w=110, boosts=3, every=30, arrows_at=(70,), lines=True)
    R2.ramp_jump(r, "Jackpot Ramp", deg=24, drop=40, w_land=150, slope=2, land_min=280, cp=True)
    ring_on_jump(b, frac=0.5, R=60.0, col=ORANGE)
    ring_on_jump(b, frac=0.45, R=26.0, col=BLUE, high=45.0, coins=True)
    # 7. the drain: the field narrows between bumpers into the outlane
    road(r, "Drain", 240, w=110, cp=False)
    bumper_field(r, [(45, -36), (95, 38), (145, -36), (195, 38)], 110, rng)
    sling_banks(r, 110, every=120, L=90)
    end_on_line(r, "Pinball Out")
    finish_stage(r, rng)
    r.log("end")
    return ["Plunger", "Playfield", "Spinners", "Flippers", "Ramp Shots", "Bumper Bend", "Jackpot", "Drain"]


# ===================================================================== 4. the skyline leap
def sky_tower(b, base, top_y, R, col, rng, collide=True, spire=True):
    """A giant futuristic tower: stacked drums, neon bands, lit window rings, a lit crown."""
    col = tint(b, col)
    x, y0, z = base
    y = y0
    k = 0
    while y < top_y:
        h = min(rng.uniform(60, 110), top_y - y)
        rr = R * (1.0 if k % 2 == 0 else 0.86)
        cyl(b, "TowerDrum", (x, y + h / 2, z), h, 2 * rr, DARK if k % 2 else DARK2, "Metal", b.scenery, collide=collide)
        cyl(b, "TowerBand", (x, y + h - 1, z), 2, 2 * rr + 2, [col, WHITE][k % 2], "Neon", b.scenery, collide=False)
        if h > 40:
            cyl(b, "TowerWindows", (x, y + h * 0.5, z), h * 0.3, 2 * rr + 0.6, tint(b, BLUE), "Glass", b.scenery,
                collide=False, transp=0.35)
        y += h
        k += 1
    if spire:
        cyl(b, "TowerCrown", (x, top_y + 6, z), 12, 2 * R * 0.7, col, "Neon", b.scenery, collide=False)
        cyl(b, "TowerSpire", (x, top_y + 40, z), 60, 6, METAL, "Metal", b.scenery, collide=False)
        MX.lamp(b, (x, top_y + 72, z), col=RED, d=6.0, pulse=1.0)
    else:
        cyl(b, "TowerCrown", (x, top_y + 1, z), 2, 2 * R + 2, col, "Neon", b.scenery, collide=False)


def slot14(r, sk, rng):
    b = r.b
    stage(r, sk, "Skyline Leap", "OBBY 2 - STAGE 4", ROAD, BLUE)
    road(r, "Skyline Approach", 140, w=140, boosts=3, every=35, arrows_at=(70,), lines=True)
    # 1. the tower slalom: giant towers stand in the road; the middle stays open, squeeze past them
    road(r, "Tower Slalom", 340, w=150, cp=True)
    for k, d in enumerate((60, 140, 220, 300)):
        p, f = MX.at_road(r, d)
        q = add(p, mul(right_of(f), (1 if k % 2 == 0 else -1) * 48))
        sky_tower(b, (q[0], p[1], q[2]), p[1] + 220 + 60 * (k % 2), 18, [ORANGE, BLUE][k % 2], rng)
        cyl(b, "TowerRoot", (q[0], p[1] - 4.2 - 90, q[2]), 180, 32, DARK2, "Metal", b.scenery)
    # 2. up: two launch pads onto the skyline deck
    o = O.Obby(r, 280)
    o.plat("Launch Deck", 90, 100)
    o.pad(130.0, label="Sky Launch 1")
    o.plat("Sky Deck 1", 80, 100, cp=True)
    o.pad(130.0, label="Sky Launch 2")
    o.plat("Skyline Deck", 120, 120, cp=True)
    deck_end, f = r.p, r.f
    rt = right_of(f)
    # 3. the leap: a steep ramp across the whole canyon, rings over the flight
    r.w = 110.0
    road(r, "Leap Run", 160, w=110, boosts=3, every=26, arrows_at=(80, 150), lines=True)
    R2.ramp_jump(r, "Skyline Ramp", deg=28, drop=250, w_land=220, slope=3, land_min=440, cp=True)
    leap = b.jumps[-2] if b.jumps[-1][0] == "ramp_hop" else b.jumps[-1]
    ring_on_jump(b, kind_pick=b.jumps.index(leap), frac=0.3, R=70.0, col=BLUE)
    ring_on_jump(b, kind_pick=b.jumps.index(leap), frac=0.62, R=80.0, col=ORANGE)
    ring_on_jump(b, kind_pick=b.jumps.index(leap), frac=0.45, R=30.0, col=WHITE, high=90.0, coins=True)
    ring_on_jump(b, kind_pick=b.jumps.index(leap), frac=0.8, R=28.0, col=RED, side=-70.0, high=20.0, coins=True)
    Lr = MX.last_len(r)
    land0 = sub(r.p, mul(f, Lr))
    # 4. the needle gap: off the right side of the skyline deck, a flat fast kicker threads between two towers
    a = add(deck_end, mul(rt, 85))
    al = MX.Alt(r, a, f, 30, B=330.0)
    accent(b, glow=RED)
    al.r.straight("Needle Run", 200, lead=5.0, rails=True, line=False)
    R2.lay_strips(al.r, 10, 190, every=22, lanes=1)
    lip, d = R2.kicker(al.r, "Needle Kicker", 16.0, L=36.0, w=30, rails=False)
    land_y = land0[1] - 0.03 * Lr
    ps = [R2.fly(lip, mul(d, v), lambda p: land_y)[0] for v in (0.9 * V_TOP, V_TOP)]
    b.jumps.append(("ramp", lip, ps[1], V_TOP * math.hypot(d[0], d[2]), V_TOP * d[1]))
    coin_arc(b, lip, d, V_TOP, n=6, t0=0.2, t1=0.7)
    # the two towers the flight threads, 44 apart, halfway
    mid, _ = R2.fly(lip, mul(d, V_TOP * 0.95), lambda p: lip[1] - 60)
    for s_ in (-1, 1):
        q = add(mid, mul(rt, s_ * 40))
        sky_tower(b, (q[0], Y0 - 700, q[2]), lip[1] + 160, 16, RED, rng)
    al.done()
    # where the needle lands: far down the landing runway, on its right half
    accent(b, glow=b.stage_glow)
    # 5. the skyline bend round a tower, then rooftop hops
    r.w = 120.0
    r.turn("Skyline Bend", 30, 330, bank=10, rails=True)
    r.turn("Skyline Bend 2", -60, 330, bank=10, rails=True)
    R2.lay_strips(r, 40, 340, every=60, lanes=2)
    r.turn("Skyline Bend 3", 30, 330, bank=10, rails=True)
    road(r, "Rooftop Run", 100, w=100, boosts=3, every=30)
    for k in range(3):
        MX.hop(r, "Rooftop Hop %d" % (k + 1), drop=15.0 + 5 * k, deg=10.0)
        p = r.p
        sky_tower(b, (p[0] - 40, Y0 - 700, p[2]), p[1] - 14, 34, [ORANGE, BLUE, WHITE][k], rng, collide=False, spire=False)
    # 6. the run-out, back up to the canyon road
    road(r, "Skyline Run-Out", 260, w=110, dy=45, boosts=3, every=35, cp=True, lines=True)
    end_on_line(r, "Skyline Out")
    finish_stage(r, rng)
    r.log("end")
    return ["Tower Slalom", "Sky Launch", "Skyline Ramp", "Needle Gap", "Skyline Bend", "Rooftop Hops"]


# ===================================================================== 5. rolling thunder
def gate_ring(b, c, f, R, y_min, col, roll=0.0, n=20):
    """A giant ring standing round the road (you drive through it), rolled roll radians about the road; built of
    straight segments, none of them under y_min + 12 (the road and the car)."""
    rt = right_of(f)
    for k in range(n):
        a0, a1 = TAU * k / n + roll, TAU * (k + 1) / n + roll
        p0 = add(c, add(mul(rt, R * math.sin(a0)), (0, R * math.cos(a0), 0)))
        p1 = add(c, add(mul(rt, R * math.sin(a1)), (0, R * math.cos(a1), 0)))
        if min(p0[1], p1[1]) < y_min + 14:
            continue
        d = unit(sub(p1, p0))
        nrm = unit(cross(f, d))
        q = R2.lerp3(p0, p1, 0.5)
        Pt(b, "GateRing", CF(q, f, nrm, d), (8, 10, math.dist(p0, p1) + 1.5), DARK, "Metal", b.scenery)
        Pt(b, "GateRingGlow", CF(add(q, mul(nrm, -5.2)), f, nrm, d), (6, 0.4, math.dist(p0, p1) + 1.5), tint(b, col) if k % 2 else WHITE,
           "Neon", b.scenery)


def line_marks(r, every=14.0, col=None):
    """Coloured dashes down the racing line of the road just laid (the fastest line)."""
    b = r.b
    col = tint(b, col or b.skin.glow)
    pts = r.last[0]
    tot = sum(math.dist(a_, c_) for a_, c_ in zip(pts, pts[1:]))
    d = 10.0
    while d < tot - 10:
        p, f = MX.at_road(r, d)
        Pt(b, "LineMark", CF(add(p, (0, 0.09, 0)), *_axes(f)), (2.2, 0.14, 7), col, "Neon", b.scenery)
        d += every


def slot15(r, sk, rng):
    b = r.b
    stage(r, sk, "Rolling Thunder", "OBBY 2 - STAGE 5", ROAD, ORANGE)
    road(r, "Thunder Approach", 140, w=110, boosts=3, every=30, arrows_at=(70,), lines=True)
    # 1. the barrel gates: giant rings round the road, each rolled further, like a barrel roll frozen in steel
    road(r, "Barrel Gates", 460, w=100, boosts=3, every=60, cp=True)
    for k, d in enumerate((60, 160, 260, 360, 440)):
        p, f = MX.at_road(r, d)
        gate_ring(b, add(p, (0, 30, 0)), f, 78, p[1], [ORANGE, BLUE][k % 2], roll=k * 0.35)
    line_marks(r)
    # 2. the sweepers: big banked turns, the racing line painted on
    r.w = 110.0
    r.turn("Sweeper", 50, 420, bank=16, rails=True, cp=True)
    line_marks(r, col=BLUE)
    r.turn("Sweeper 2", -100, 420, bank=16, rails=True)
    line_marks(r, col=ORANGE)
    R2.lay_strips(r, 60, 640, every=90, lanes=2)
    r.turn("Sweeper 3", 50, 420, bank=16, rails=True)
    line_marks(r, col=BLUE)
    # 3. the thunder bowl: once round a giant spinning ring, climbing, and over your own way in
    road(r, "Bowl Entry", 100, w=110, boosts=3, every=30, cp=True)
    b.no_under = True
    R = 300.0
    r.turn("Thunder Bowl", 330, R, dy=128, bank=14, rails=True)
    C = r.centre
    line_marks(r, col=WHITE)
    R2.lay_strips(r, 80, 1600, every=120, lanes=2)
    b.no_under = False
    r.turn("Bowl Exit", 30, R, bank=8, rails=True)
    giant_ring(b, (C[0], r.p[1] + 120, C[2]), 120, (1, 0, 0), col=ORANGE, spin=0.05, th=16.0)
    giant_ring(b, (C[0], r.p[1] + 120, C[2]), 90, (0, 0, 1), col=BLUE, spin=-0.04, th=12.0)
    cyl(b, "BowlMast", (C[0], (r.p[1] + Y0 - 900) / 2, C[2]), r.p[1] - (Y0 - 900), 30, DARK, "Metal", b.scenery)
    # 4. the high platforms, linked by short hops
    road(r, "Platform Run", 80, w=100, boosts=3, every=26)
    for k in range(3):
        MX.hop(r, "Platform Hop %d" % (k + 1), drop=18.0, deg=10.0 + 2 * k, land_extra=40.0)
    # 5. the roll ramp: off a curved ramp through a ring
    road(r, "Roll Run", 120, w=110, boosts=3, every=28, arrows_at=(60,), lines=True)
    R2.ramp_jump(r, "Roll Ramp", deg=22, drop=40, w_land=140, slope=3, land_min=300, cp=True)
    ring_on_jump(b, frac=0.5, R=56.0, col=ORANGE)
    ring_on_jump(b, frac=0.5, R=24.0, col=BLUE, side=50.0, high=30.0, coins=True)
    # 6. the downhill burst
    road(r, "Downhill Burst", 320, w=110, dy=-40, boosts=3, every=30, cp=True, lines=True)
    line_marks(r)
    end_on_line(r, "Thunder Out")
    finish_stage(r, rng)
    r.log("end")
    return ["Barrel Gates", "Sweepers", "Thunder Bowl", "High Platforms", "Roll Ramp", "Downhill Burst"]


# ===================================================================== 6. the cracking canyon
CRACK = ((112, 64, 46), (60, 38, 32))


def crack_span(r, label, L, W, delay=0.3, rate=95.0, cell=40.0, cp=False):
    """Road that cracks up and drops away a moment after you drive on it (it is back a few seconds later)."""
    R2.sink_board(r, label, L, W, cell=cell, cols=CRACK, mats=("Slate", "Slate"), delay=delay, rate=rate, cp=cp)
    # glowing cracks between the tiles: they show which road is going to go
    pts = r.last[0] if r.last else None
    p1 = r.p
    f = r.f
    p0 = sub(p1, mul(f, L))
    rt = right_of(f)
    n = int(round(L / cell))
    for i in range(1, n):
        q = add(p0, add(mul(f, i * cell), (0, 0.05, 0)))
        Pt(r.b, "CrackGlow", CF(q, *_axes(f)), (W - 4, 0.1, 0.8), tint(r.b, ORANGE), "Neon", r.b.scenery)
    for s_ in (-1, 1):
        Pt(r.b, "CrackEdge", CF(add(R2.lerp3(p0, p1, 0.5), add(mul(rt, s_ * (W / 2 + 1)), (0, -1, 0))), *_axes(f)),
           (2, 4, L), tint(r.b, ORANGE), "Neon", r.b.scenery)
    return r


def mesa(b, top, w, L, f, rng):
    """A rock mesa under a landing, its top just under the road."""
    for k in range(3):
        s = 1.0 - 0.18 * k
        h = 120 + k * 110
        box(b, "Mesa", add(top, (0, -14 - h / 2 - k * 70, 0)), (L * s, h, w * s * 1.1), ROCK[k % len(ROCK)], "Sandstone",
            yaw=math.atan2(-f[2], f[0]) + rng.uniform(-0.08, 0.08))


def slot16(r, sk, rng):
    b = r.b
    stage(r, sk, "Cracking Canyon", "OBBY 2 - STAGE 6", ROAD, ORANGE)
    road(r, "Canyon Approach", 140, w=100, dy=30, boosts=3, every=30, arrows_at=(70,), lines=True)
    # 1. cracking road and tilting spans: keep moving
    crack_span(r, "Cracking Road", 320, 100, delay=0.35, cp=True)
    road(r, "Rock Pier", 60, w=100)
    MX.tilt_deck(r, "Tilting Span", 160, 90, amp_deg=10, period=3.4)
    road(r, "Rock Pier 2", 60, w=100, cp=True)
    MX.tilt_deck(r, "Tilting Span 2", 160, 90, amp_deg=12, period=3.0, phase=0.5)
    road(r, "Rock Pier 3", 60, w=100)
    crack_span(r, "Cracking Road 2", 240, 100, delay=0.28)
    # 2. mesa hops: jump from mesa to mesa
    road(r, "Mesa Run", 100, w=100, dy=25, boosts=3, every=26, cp=True)
    for k in range(3):
        MX.hop(r, "Mesa Hop %d" % (k + 1), drop=20.0, deg=11.0, land_extra=50.0)
        p, ff = MX.at_road(r, 40)
        mesa(b, p, 100, 120, ff, rng)
    # 3. the breakaway bridge: a long bridge that falls apart right behind you; or the ledges below it
    r.w = 200.0
    road(r, "Bridge Head", 100, w=200, cp=True, arrows_at=(50,))
    head, f = r.p, r.f
    rt = right_of(f)
    r.w = 80.0
    crack_span(r, "Breakaway Bridge", 720, 80, delay=0.18, rate=140.0)
    for d in range(40, 720, 120):
        for s_ in (-1, 1):
            cyl(b, "BridgeCable", add(add(head, mul(f, d)), add(mul(rt, s_ * 46), (0, 62, 0))), 120, 1.2, METAL, "Metal",
                b.scenery)
    for d in (0, 720):
        for s_ in (-1, 1):
            q = add(add(head, mul(f, d)), mul(rt, s_ * 112))
            cyl(b, "BridgeTower", add(q, (0, -60, 0)), 300, 12, DARK, "Metal", b.scenery)
            MX.lamp(b, add(q, (0, 92, 0)), col=ORANGE, d=5.0, pulse=0.8)
    r.w = 200.0
    merge = r.p
    road(r, "Bridge Tail", 220, w=200, boosts=3, every=40, cp=True)
    # the ledge route: down onto stable ledges along the canyon side, hop along them, pad back up to the tail
    al = MX.Alt(r, add(head, mul(rt, 70)), f, 50, B=260.0)
    accent(b, glow=BLUE)
    al.o.plat("Ledge Lip", 30, 50)
    al.o.drop(60.0, side=50)
    al.o.plat("Ledge", 140, 60)
    p, ff = MX.at_road(al.r, 70)
    mesa(b, p, 60, 140, ff, rng)
    al.o.kick(0, side=0, label="Ledge Hop")
    al.o.plat("Ledge 2", 0, 60)
    up = merge[1] - al.r.p[1]
    lo, hi = al.o.pad_range(up)
    gap = dot(sub(add(merge, mul(f, 80)), al.r.p), f)
    al.o.plat("Ledge Run", max(40.0, gap - (lo + hi) / 2), 60)
    al.o.pad(up, side=dot(sub(merge, al.r.p), rt) * 0.9)
    al.done()
    accent(b, glow=b.stage_glow)
    # 4. the crumbling launch: cracking road straight onto a big jump over the canyon
    crack_span(r, "Crumbling Run", 200, 110, delay=0.3)
    road(r, "Launch Plate", 100, w=110, boosts=3, every=24, arrows_at=(60,))
    R2.ramp_jump(r, "Canyon Cross", deg=22, drop=60, w_land=140, slope=3, land_min=300, cp=True)
    ring_on_jump(b, frac=0.5, R=56.0, col=ORANGE)
    ring_on_jump(b, frac=0.5, R=24.0, col=BLUE, high=40.0, side=-40.0, coins=True)
    # 5. the last crack-up, out onto a boosted run
    crack_span(r, "Last Crack", 240, 110, delay=0.25)
    road(r, "Canyon Exit", 200, w=110, dy=60, boosts=3, every=40, cp=True, lines=True)
    end_on_line(r, "Canyon Out")
    finish_stage(r, rng)
    r.log("end")
    return ["Cracking Road", "Tilting Spans", "Mesa Hops", "Breakaway Bridge", "Ledge Route", "Canyon Cross", "Last Crack"]


# ===================================================================== 7. the mega ramp cascade
def last_ramp(b):
    return [j for j in b.jumps if j[0] == "ramp"][-1]


def cascade_jump(r, label, deg, drop, w_land, land_min, col, rings=1, coins=True):
    """A launch, a ring (or two) over the flight, and strips on the back of the landing to carry the speed on."""
    b = r.b
    R2.ramp_jump(r, label, deg=deg, drop=drop, w_land=w_land, slope=3, land_min=land_min, cp=True)
    ring_on_jump(b, kind_pick=b.jumps.index(last_ramp(b)), frac=0.5, R=60.0 + drop * 0.1, col=col)
    if rings > 1:
        ring_on_jump(b, kind_pick=b.jumps.index(last_ramp(b)), frac=0.25, R=50.0, col=WHITE)
    if coins:
        ring_on_jump(b, kind_pick=b.jumps.index(last_ramp(b)), frac=0.6, R=24.0, col=RED, high=50.0, coins=True)
    Lr = MX.last_len(r)
    R2.lay_strips(r, Lr - 150, Lr - 10, every=35, lanes=3)
    return Lr


def slot17(r, sk, rng):
    b = r.b
    stage(r, sk, "Mega Ramp Cascade", "OBBY 2 - STAGE 7", ROAD, BLUE)
    road(r, "Cascade Approach", 110, w=120, boosts=3, every=26, arrows_at=(70,), lines=True)
    # land, accelerate, launch again
    cascade_jump(r, "Cascade 1", 24, 10, 130, 300, BLUE)
    f = r.f
    rt = right_of(f)
    p_alt = sub(r.p, mul(f, 120))
    Lr2 = cascade_jump(r, "Cascade 2", 22, 80, 160, 400, ORANGE, rings=2)
    land2_end = r.p
    land2_0 = sub(land2_end, mul(f, Lr2))
    # the expert line: off the right of Cascade 2's run-up, a steeper ramp onto a high rail, back down at its end
    al = MX.Alt(r, add(p_alt, mul(rt, 70)), f, 30, B=330.0)
    accent(b, glow=RED)
    al.r.straight("Expert Run", 100, lead=5.0, rails=True, line=False)
    R2.lay_strips(al.r, 10, 90, every=22, lanes=1)
    lip, d = R2.kicker(al.r, "Expert Ramp", 32.0, L=44.0, w=30, rails=False)
    rail_y = land2_0[1] + 70
    ps = [R2.fly(lip, mul(d, v), lambda p: rail_y)[0] for v in (0.9 * V_TOP, V_TOP)]
    near = min(dot(sub(q, lip), f) for q in ps)
    far = max(dot(sub(q, lip), f) for q in ps)
    b.jumps.append(("ramp", lip, ps[1], V_TOP * math.hypot(d[0], d[2]), V_TOP * d[1]))
    coin_arc(b, lip, d, V_TOP, n=7)
    al2 = MX.Alt(r, add(lip, add(mul(f, near - 60), (0, rail_y - lip[1], 0))), f, 40, B=300.0)
    b.no_under = True
    to = dot(sub(land2_end, al2.r.p), f) - 230
    al2.r.straight("Expert Rail", max(far - near + 120, to), lead=5.0, rails=True, line=False)
    R2.lay_strips(al2.r, 30, max(far - near + 120, to) - 20, every=50, lanes=1)
    al2.o.plat("Expert End", 20, 40)
    b.no_under = False
    al2.o.drop(al2.r.p[1] - (land2_end[1] + 3), side=dot(sub(land2_end, al2.r.p), rt) * 0.9)
    al2.done()
    al.done()
    accent(b, glow=b.stage_glow)
    # the curved road on from the landing, straight into the pads
    r.w = 120.0
    r.turn("Cascade Curve", 20, 420, bank=12, rails=True)
    r.turn("Cascade Curve 2", -40, 420, bank=12, rails=True)
    R2.lay_strips(r, 30, 260, every=40, lanes=3)
    r.turn("Cascade Curve 3", 20, 420, bank=12, rails=True)
    # two pads straight up to the mega deck
    o = O.Obby(r, 300)
    o.plat("Pad Deck", 60, 100)
    o.pad(118.0, label="Cascade Pad 1")
    o.plat("Pad Deck 1", 60, 110, cp=True)
    o.pad(118.0, label="Cascade Pad 2")
    o.plat("Mega Deck", 80, 140, cp=True)
    # the biggest launch of the cascade
    road(r, "Mega Run", 100, w=140, boosts=3, every=22, arrows_at=(50, 95), lines=True)
    cascade_jump(r, "Mega Launch", 30, 140, 200, 340, ORANGE, rings=2)
    end_on_line(r, "Cascade Out")
    finish_stage(r, rng)
    r.log("end")
    return ["Cascade 1", "Cascade 2", "Expert Line", "Cascade Curve", "Cascade Pads", "Mega Launch"]


# ===================================================================== 8. the laser slalom
LASER = (255, 40, 60)
ALWAYS = {"ObbyHazard": "Zap", "ZapPeriod": 1000.0, "ZapOn": 2000.0, "ZapPhase": 0.0}


def laser_sheet(b, c, f, L, h=10.0, col=LASER, attrs=None, parent=None, z0=0.6):
    """A wall of laser beams across part of the road: c is the middle of its foot, L its length across the road.
    Kills on touch (FRIED) while it is on."""
    rt = right_of(f)
    fr = deck_frame(c, f)
    a = dict(attrs or ALWAYS)
    parent = parent if parent is not None else b.hazards
    for k in range(4):
        y = z0 + 1.0 + k * (h - 2) / 3
        Pt(b, "LaserBeam", CF(add(c, (0, y, 0)), fr.x, fr.y, fr.z), (L, 0.5, 0.5), col, "Neon", parent, transp=0.15,
           attrs=dict(a, ZapFX=True) if "ZapPeriod" in a and a["ZapPeriod"] < 100 else None)
    b.part("LaserZone", CF(add(c, (0, h / 2 + z0, 0)), fr.x, fr.y, fr.z), (L, h, 3), col, parent=parent, transp=1,
           collide=False, query=True, attrs=a)


def emitter(b, p, h=14.0, col=LASER):
    cyl(b, "Emitter", add(p, (0, h / 2, 0)), h, 4, DARK, "Metal", b.scenery)
    ball(b, "EmitterEye", add(p, (0, h + 1, 0)), 3.2, col, "Neon", b.scenery)


def laser_fence(r, d, w, gap=46.0, off=0.0, slot=None):
    """A fixed laser fence across the road with a wide opening (off: where it is) and, if slot, a narrow risky slot
    in one of the side sheets (coins in it)."""
    b = r.b
    p, f = MX.at_road(r, d)
    rt = right_of(f)
    lo, hi = off - gap / 2, off + gap / 2
    pieces = [(-w / 2 + 3, lo), (hi, w / 2 - 3)]
    if slot is not None:
        a, b_ = pieces[0 if slot < 0 else 1]
        mid = (a + b_) / 2
        pieces = [pc for pc in pieces if pc != (a, b_)] + [(a, mid - 6), (mid + 6, b_)]
        for k in range(3):
            coin_spot(b, add(p, add(mul(rt, mid), add(mul(f, -12 + 12 * k), (0, 4, 0)))))
    for a, c in pieces:
        if c - a < 2:
            continue
        laser_sheet(b, add(p, mul(rt, (a + c) / 2)), f, c - a)
        emitter(b, add(p, mul(rt, a)))
        emitter(b, add(p, mul(rt, c)))


def laser_sweeper(b, c, w, i, period=2.6):
    """A laser sheet half the road wide sliding from side to side on an overhead track (one half is always clear)."""
    x, y, z = c
    rest = (x, y, z - w / 4)
    root = b.prop_root("LaserSweep")
    rig = b.rig(root, "Slide", axis_frame(add(rest, (0, 6, 0)), (0, 0, 1)), w / 2, period, phase=(i * 0.37) % 1,
                keys="0:0 0.4:0 0.5:1 0.9:1 1:0", name="Sweep")
    laser_sheet(b, rest, (1, 0, 0), w / 2 - 2, h=12.0, parent=rig)
    Pt(b, "SweepHead", CF(add(rest, (0, 34, 0))), (6, 4, w / 2), DARK, "Metal", rig)
    Pt(b, "SweepTrack", CF((x, y + 38, z)), (8, 3, w + 30), DARK, "Metal", b.scenery)
    for s_ in (-1, 1):
        Pt(b, "TrackPost", CF((x, y + 19, z + s_ * (w / 2 + 12))), (5, 38, 5), DARK, "Metal", b.scenery)
        ball(b, "WarnLight", (x, y + 41, z + s_ * (w / 2 + 12)), 4, LASER, "Neon", b.scenery)


def pulse_gate(b, c, w, i, period=2.2):
    """Two half-width laser gates pulsing in turn (each on for under half the beat): one half is always open."""
    x, y, z = c
    for k, s_ in enumerate((-1, 1)):
        q = (x, y, z + s_ * w / 4)
        a = {"ObbyHazard": "Zap", "ZapPeriod": float(period), "ZapOn": float(period * 0.42), "ZapPhase": float((k * 0.5 + i * 0.13) % 1)}
        laser_sheet(b, q, (1, 0, 0), w / 2 - 2, h=14.0, attrs=a, col=(255, 80, 200))
    for zz in (-w / 2 - 3, w / 2 + 3):
        emitter(b, (x, y, z + zz), h=18.0, col=(255, 80, 200))
    Pt(b, "GateTop", CF((x, y + 19, z)), (4, 2, w + 10), DARK, "Metal", b.scenery)


def laser_rotor(b, c, w, i, speed=0.18):
    """Two laser arms spinning flat over the road from a hub at its edge."""
    x, y, z = c
    s_ = 1 if i % 2 == 0 else -1
    hub = (x, y, z + s_ * (w / 2 + 6))
    root = b.prop_root("LaserRotor")
    rig = b.rig(root, "Spin", axis_frame(add(hub, (0, 3, 0)), (0, 1, 0)), speed * s_, 1, phase=(i * 0.29) % 1, name="Rotor")
    for k in (-1, 1):
        q = add(hub, (k * (w * 0.45), 0, 0))
        laser_sheet(b, q, (0, 0, 1), w * 0.9, h=8.0, parent=rig)
    cyl(b, "RotorHub", add(hub, (0, 6, 0)), 12, 14, DARK, "Metal", b.scenery)
    ball(b, "RotorEye", add(hub, (0, 13, 0)), 6, LASER, "Neon", b.scenery)


def slot18(r, sk, rng):
    b = r.b
    stage(r, sk, "Laser Slalom", "OBBY 2 - STAGE 8", ROAD, BLUE)
    W = 120.0
    road(r, "Laser Approach", 140, w=W, boosts=3, every=30, arrows_at=(70,), lines=True)
    # 1. laser fences: weave through the wide openings, or thread the narrow slots for coins
    road(r, "Laser Fences", 560, w=W, cp=True)
    R2.lay_strips(r, 20, 540, every=60, lanes=1)
    for k, d in enumerate((80, 180, 280, 380, 480)):
        laser_fence(r, d, W, gap=48.0, off=(12.0 if k % 2 == 0 else -12.0), slot=(1 if k % 2 == 0 else -1))
    # 2. laser hurdles: little kickers over low beams
    road(r, "Hurdle Run", 80, w=W, boosts=3, every=26)
    for k in range(3):
        MX.hop(r, "Laser Hurdle %d" % (k + 1), drop=10.0, deg=10.0, land_extra=30.0)
        # the low beam across the gap the car jumps
        j = last_ramp(b)
        lip, tgt = j[1], j[2]
        mid = R2.lerp3(lip, tgt, 0.35)
        f = RT.flat(sub(tgt, lip))
        laser_sheet(b, (mid[0], lip[1] - 12, mid[2]), f, W - 4, h=6.0)
    # 3. sweeping beams: each one covers half the road and slides across
    road(r, "Sweeper Run", 460, w=W, dy=36, cp=True)
    R2.lay_strips(r, 20, 440, every=70, lanes=1)
    r.along(laser_sweeper, [90, 220, 350], i0=0)
    # 4. the laser bend: a banked bend between emitter towers
    r.turn("Laser Bend", 30, 400, bank=12, rails=True)
    r.turn("Laser Bend 2", -60, 400, bank=12, rails=True)
    R2.lay_strips(r, 30, 380, every=60, lanes=2)
    for d in (80, 220, 360):
        p, ff = MX.at_road(r, d)
        for s_ in (-1, 1):
            emitter(b, add(p, mul(right_of(ff), s_ * (W / 2 + 10))), h=40.0, col=BLUE)
    r.turn("Laser Bend 3", 30, 400, bank=12, rails=True)
    # 5. pulse gates: each half lights up in turn
    road(r, "Pulse Gates", 420, w=W, cp=True)
    R2.lay_strips(r, 20, 400, every=70, lanes=1)
    r.along(pulse_gate, [90, 210, 330], i0=0)
    # 6. the laser rotors
    road(r, "Rotor Run", 340, w=W, dy=30, cp=True)
    r.along(laser_rotor, [100, 250], i0=0)
    # 7. the prism jump: through a ring of light
    road(r, "Prism Run", 120, w=W, boosts=3, every=26, arrows_at=(60,), lines=True)
    R2.ramp_jump(r, "Prism Jump", deg=22, drop=40, w_land=140, slope=3, land_min=300, cp=True)
    ring_on_jump(b, frac=0.5, R=56.0, col=LASER)
    ring_on_jump(b, frac=0.5, R=24.0, col=BLUE, high=40.0, coins=True)
    end_on_line(r, "Laser Out")
    finish_stage(r, rng)
    r.log("end")
    return ["Laser Fences", "Laser Hurdles", "Sweeping Beams", "Laser Bend", "Pulse Gates", "Laser Rotors", "Prism Jump"]


# ===================================================================== 9. the final speed frenzy
def bollards(r, side_of_turn, w, every=40.0, col=None):
    """Glowing bollards along the inside edge of the turn just laid (the line to clip)."""
    b = r.b
    pts = r.last[0]
    tot = sum(math.dist(a_, c_) for a_, c_ in zip(pts, pts[1:]))
    d = 20.0
    k = 0
    while d < tot - 20:
        p, f = MX.at_road(r, d)
        q = add(p, mul(right_of(f), side_of_turn * (w / 2 + 3)))
        cyl(b, "Bollard", add(q, (0, 4, 0)), 8, 4, DARK, "Metal", b.scenery)
        cyl(b, "BollardGlow", add(q, (0, 8.4, 0)), 1, 4.4, col or [ORANGE, WHITE][k % 2], "Neon", b.scenery)
        d += every
        k += 1


def chicane(r, label, deg, R, w, first=1):
    """Left-right-left (or the other way) at full speed, bollards on the inside of every bend."""
    s_ = first
    r.turn(label, s_ * deg, R, bank=10, w1=w, rails=True)
    bollards(r, -s_, w)
    r.turn(label + " 2", -s_ * 2 * deg, R, bank=10, rails=True)
    bollards(r, s_, w)
    R2.lay_strips(r, 40, 2 * deg * math.pi / 180 * R - 40, every=60, lanes=2)
    r.turn(label + " 3", s_ * deg, R, bank=10, rails=True)
    bollards(r, -s_, w)


def slot19(r, sk, rng):
    b = r.b
    stage(r, sk, "Speed Frenzy", "OBBY 2 - STAGE 9", ROAD, ORANGE)
    W = 110.0
    # 1. the boost runway
    road(r, "Frenzy Runway", 280, w=W, boosts=3, every=24, cp=False, arrows_at=(60, 260), lines=True)
    for d in (80, 200):
        neon_arch(b, r.ahead(d - 280), r.f, W, [ORANGE, BLUE][d // 100 % 2], h=36)
    # 2. the left-right steering challenge
    chicane(r, "Frenzy Chicane", 32, 300, 90, first=1)
    road(r, "Chicane Link", 80, w=90, boosts=3, every=26, cp=True)
    chicane(r, "Frenzy Chicane B", 32, 300, 90, first=-1)
    # 3. bigger and bigger gaps
    road(r, "Gap Run", 100, w=W, boosts=3, every=24, lines=True)
    MX.hop(r, "Gap 1", drop=16.0, deg=10.0, land_extra=60.0)
    R2.lay_strips(r, 10, 100, every=24, lanes=3)
    R2.ramp_jump(r, "Gap 2", deg=16, drop=40, w_land=W, slope=2, land_min=260, cp=True)
    ring_on_jump(b, frac=0.5, R=40.0, col=BLUE)
    Lr = MX.last_len(r)
    R2.lay_strips(r, Lr - 120, Lr - 10, every=26, lanes=3)
    R2.ramp_jump(r, "Gap 3", deg=22, drop=70, w_land=130, slope=2, land_min=300, cp=True)
    ring_on_jump(b, frac=0.5, R=56.0, col=ORANGE)
    ring_on_jump(b, frac=0.55, R=24.0, col=WHITE, high=50.0, coins=True)
    # 4. the medley: a bumper field, a laser fence, cracking road - everything at once
    road(r, "Frenzy Medley", 420, w=130, dy=60, cp=True)
    R2.lay_strips(r, 20, 400, every=60, lanes=1)
    bumper_field(r, [(60, -40), (90, 45), (150, -50), (200, 38)], 130, rng)
    laser_fence(r, 280, 130, gap=50.0, off=10.0, slot=-1)
    laser_fence(r, 370, 130, gap=50.0, off=-10.0, slot=1)
    crack_span(r, "Frenzy Crack", 240, 110, delay=0.25)
    road(r, "Frenzy Sprint", 200, w=W, dy=66, boosts=3, every=30, cp=True, lines=True)
    chicane(r, "Last Chicane", 26, 340, 90, first=1)
    end_on_line(r, "Frenzy Out")
    finish_stage(r, rng)
    r.log("end")
    return ["Boost Runway", "Chicanes", "Growing Gaps", "Frenzy Medley", "Last Chicane"]


def finish_ring(b, c, f, w):
    """The finish: a giant glowing ring standing over the line, fireworks either side."""
    gate_ring(b, add(c, (0, 40, 0)), f, w / 2 + 50, c[1], ORANGE, n=28)
    gate_ring(b, add(c, add(mul(f, 8), (0, 40, 0))), f, w / 2 + 40, c[1], BLUE, n=28)
    rt = right_of(f)
    for s_ in (-1, 1):
        for j in range(3):
            q = add(c, add(mul(rt, s_ * (w / 2 + 30 + j * 26)), (0, 0, 0)))
            cyl(b, "FireworkPole", add(q, (0, 30 + j * 12, 0)), 60 + j * 24, 3, DARK, "Metal", b.scenery)
            for k in range(6):
                a = TAU * k / 6
                d = unit((math.cos(a) * 0.6, 1.0, math.sin(a) * 0.6))
                MX.lamp(b, add(add(q, (0, 64 + j * 24, 0)), mul(d, 10)), col=[ORANGE, BLUE, WHITE, RED][(k + j) % 4], d=4.0,
                        pulse=0.4 + 0.07 * k)


def slot20(r, sk, rng):
    b = r.b
    stage(r, sk, "Grand Finale", "OBBY 2 - FINAL", ROAD, BLUE)
    b.final_slot = True
    W = 110.0
    road(r, "Finale Runway", 160, w=W, boosts=3, every=26, arrows_at=(80,), lines=True)
    milestone(b, r.ahead(-130), r.f, W)
    # 1. the reprise: the best of the speedway, back to back
    road(r, "Reprise Field", 300, w=130, cp=True)
    R2.lay_strips(r, 20, 280, every=70, lanes=1)
    bumper_field(r, [(45, -45), (80, 40), (120, -35), (160, 50)], 130, rng)
    r.along(spinner, [255], i0=5, side=1, speed=0.2, R=70.0)
    road(r, "Reprise Hop Run", 90, w=W, boosts=3, every=26)
    for k in range(2):
        MX.hop(r, "Reprise Hop %d" % (k + 1), drop=16.0, deg=11.0, land_extra=50.0)
    road(r, "Reprise Gates", 260, w=100, dy=32, boosts=3, every=50, cp=True)
    for k, d in enumerate((50, 130, 210)):
        p, ff = MX.at_road(r, d)
        gate_ring(b, add(p, (0, 30, 0)), ff, 76, p[1], [BLUE, ORANGE][k % 2], roll=k * 0.4)
    road(r, "Reprise Ramp Run", 100, w=W, boosts=3, every=24, arrows_at=(50,), lines=True)
    R2.ramp_jump(r, "Reprise Ramp", deg=18, drop=40, w_land=120, slope=2, land_min=280, cp=True)
    ring_on_jump(b, frac=0.5, R=48.0, col=BLUE)
    road(r, "Reprise Climb", 160, w=W, dy=36, boosts=3, every=30, lines=True)
    # 2. the collapsing bridge: one last commitment
    r.w = 90.0
    crack_span(r, "Collapsing Bridge", 520, 90, delay=0.18, rate=150.0)
    p_end, f = r.p, r.f
    for d in range(30, 520, 110):
        for s_ in (-1, 1):
            q = add(sub(p_end, mul(f, 520 - d)), mul(right_of(f), s_ * 52))
            cyl(b, "BridgeCable", add(q, (0, 50, 0)), 100, 1.2, METAL, "Metal", b.scenery)
    road(r, "Bridge End", 120, w=120, boosts=3, every=30, cp=True)
    # 3. up to the launch deck, a weave through pulsing lasers on the way
    o = O.Obby(r, 300)
    o.plat("Launch Pad Deck", 60, 110)
    o.pad(110.0, label="Finale Pad")
    o.plat("Finale Deck", 100, 140, cp=True)
    road(r, "Pulse Run", 200, w=140, boosts=2, every=60)
    r.along(pulse_gate, [70, 150], i0=4, period=2.0)
    # 4. the final jump, framed by the giant ring, onto the huge finish platform
    road(r, "Final Run", 160, w=140, boosts=3, every=22, arrows_at=(60, 150), lines=True)
    accent(b, top=(214, 220, 232), glow=ORANGE)  # (the finish platform: bright white, unmistakably the end)
    R2.ramp_jump(r, "Final Jump", deg=24, drop=110, w_land=240, slope=2, land_min=400, cp=True)
    ring_on_jump(b, frac=0.5, R=110.0, col=ORANGE)
    ring_on_jump(b, frac=0.5, R=135.0, col=BLUE)
    ring_on_jump(b, frac=0.32, R=30.0, col=WHITE, high=60.0, coins=True)
    ring_on_jump(b, frac=0.68, R=30.0, col=RED, high=60.0, coins=True)
    # the finish platform: huge, bright, lit all round
    Lr = MX.last_len(r)
    for d in range(40, int(Lr), 70):
        p, ff = MX.at_road(r, d)
        for s_ in (-1, 1):
            q = add(p, mul(right_of(ff), s_ * 126))
            cyl(b, "LightMast", add(q, (0, 20, 0)), 40, 3, DARK, "Metal", b.scenery)
            ball(b, "MastLight", add(q, (0, 42, 0)), 5, [ORANGE, BLUE][(d // 70) % 2], "Neon", b.scenery)
    MX.arrows(r, (120, 240, 360), col=ORANGE)
    road(r, "Victory Run", 60, w=200)
    finish_ring(b, add(r.p, mul(r.f, max(40.0, r.X1 - 60 - r.p[0]))), (1, 0, 0), 200)
    finish_stage(r, rng)
    r.log("end")
    return ["Reprise", "Collapsing Bridge", "Finale Pad", "Pulse Run", "Final Jump", "Finish Platform", "Finish Ring"]


LEVELS = {11: slot11, 12: slot12, 13: slot13, 14: slot14, 15: slot15, 16: slot16, 17: slot17, 18: slot18, 19: slot19, 20: slot20}
