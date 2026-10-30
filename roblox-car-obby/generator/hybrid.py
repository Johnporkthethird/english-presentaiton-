"""Hybrid levels: the giant-object worlds of Obby 3 (giants.py) spliced into the road levels of Obby 1 and Obby 2.

Each of levels 1-20 keeps its own road stretches (speed, ramps, machines) and, between them, takes two giant-object
set pieces: a run of dinner plates, a toaster launch, a donut to drive round, a pirate cannon shot... so every level
alternates road, giant world, road, giant world, road. The pieces are compact and height-neutral (they come back
to about the height they started at), so they drop into any road level.

wear() dresses whatever the level's own skin is (the machine skin of Obby 1, the speedway skin of Obby 2) with a
giant world's surface for the stretches laid inside it, and switches the road's own supports off under the objects.
"""
import math
from contextlib import contextmanager
from geom import CF, deck_frame, axis_frame, add, sub, mul, unit, dot, rot_y, rot_axis, UP
from builder import G, CAR_UP
import route as RT
import rush2 as R2
import obby as O
import mech as MX
import epic_marks as M
import giants as GW
from giants import (ob, span, at, mix, coin, coin_row, coin_arc, slab, ghost, by_name, edges, both, lines_across, run,
                    right_of, WHITE, BLACK, GOLD, CHROME, TAU)
from skins import Pt, cyl, ball
from worlds import ringz

_MISSING = object()


@contextmanager
def wear(sk, surface=None, pad=None, plat=None, rails=None):
    """Lay the stretches inside with a giant world's surface (pad art, platforms, rail colours), and none of the
    road's own supports under them."""
    saved = {}

    def put(name, fn):
        if name not in saved:
            saved[name] = sk.__dict__.get(name, _MISSING)
        setattr(sk, name, fn)
    if surface is not None:
        put("road_piece", lambda b, parent, fr, w, L, name: surface(sk, b, parent, fr, w, L, name))
    if pad is not None:
        put("pad_art", lambda b, start, f: pad(sk, b, start, f))
    if plat is not None:
        put("plat", lambda b, top, s, rng, parent=None: plat(b, top, s, rng))
    if rails is not None:
        put("road_style", lambda: dict(top=(200, 200, 200), top_mat="SmoothPlastic", edge=rails.get("edge", GOLD),
                                       edge_mat=rails.get("edge_mat", "SmoothPlastic"), side=rails.get("side", (90, 90, 96)),
                                       side_mat=rails.get("side_mat", "SmoothPlastic"), refl=0.0, center=None))
    put("under", lambda b, top, w, i: None)
    put("supports", lambda b, x0, x1, y, z, w: None)
    try:
        yield
    finally:
        for name, v in saved.items():
            if v is _MISSING:
                delattr(sk, name)
            else:
                setattr(sk, name, v)


def obby(r, B=230.0):
    return O.Obby(r, B)


# ===================================================================== the kitchen
def k_plates(r, sk, rng):
    """Dinner plates: hop from plate to plate onto a serving tray."""
    b = r.b
    tray = slab((206, 210, 218), "Metal", th=4, refl=0.2, deco=edges((240, 242, 246), width=3.0, name="TrayRim"))
    o = obby(r)
    with wear(sk, surface=tray):
        o.plat("Tray Edge", 80, 110)
    with wear(sk, surface=ghost):
        for k, (dy, side, col) in enumerate(((-20.0, 70.0, (40, 90, 200)), (10.0, -70.0, GW.K_RED))):
            o.kick(dy=dy, side=side, label="Plate Hop %d" % (k + 1))
            o.plat("Plate %d" % (k + 1), 100, 96, cp=(k == 1))
            GW.plate(b, r, col, pattern=(k % 2 == 0))
            coin_arc(b, -1, n=4)
    with wear(sk, surface=tray):
        o.kick(dy=0.0, label="Tray Hop")
        o.plat("Serving Tray", 140, 120)
    return ["Dinner Plates"]


def k_toaster(r, sk, rng):
    """A toaster fires you up to the spice shelf, then down onto the dough where rolling pins roll across."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=slab(CHROME, "Metal", th=3, refl=0.3), pad=GW.toaster_pad):
        o.plat("Toaster Top", 120, 90)
        GW.toaster(b, r, r.f)
        o.pad(90.0, label="Toaster Launch")
    with wear(sk, surface=GW.SHELF_WOOD):
        o.plat("Spice Shelf", 220, 84, cp=True)
        p0, p1, f, L, w, _ = span(r)
        GW.legs(b, R2.lerp3(p0, p1, 0.5), f, w, L, 60, (160, 110, 66), "Wood", d=8, name="ShelfBracket")
        for k in range(6):
            s_ = 1 if k % 2 else -1
            q = add(R2.lerp3(p0, p1, 0.1 + 0.16 * k), mul(right_of(f), s_ * (w / 2 + 12)))
            cyl(b, "SpiceJar", add(q, (0, 15, 0)), 30, 16, [GW.K_RED, (120, 80, 40), (90, 160, 60)][k % 3], "Glass", b.scenery)
            cyl(b, "SpiceLid", add(q, (0, 31, 0)), 3, 17, BLACK, "SmoothPlastic", b.scenery)
        o.drop(90.0, label="Dough Drop")
    with wear(sk, surface=GW.DOUGH):
        o.plat("Dough Sheet", 360, 120, boost=False)
        r.along(GW.rolling_pin, [110, 220])
        p0, p1, f, L, w, _ = span(r)
        ob(b, "PastryBoard", sub(R2.lerp3(p0, p1, 0.5), (0, 7, 0)), f, (w + 30, 4, L + 20), GW.K_WOOD, "Wood")
    return ["Toaster Launch", "Rolling Pins"]


def k_board(r, sk, rng):
    """The chopping board: giant knives chop across it, one half always clear; then the hob's burner rings."""
    b = r.b
    with wear(sk, surface=GW.BOARD):
        run(r, "Chopping Board", 320, w=110, cp=True)
        r.along(GW.chop_knife, [100, 220])
        p0, p1, f, L, w, _ = span(r)
        ob(b, "CounterUnder", sub(R2.lerp3(p0, p1, 0.5), (0, 8, 0)), f, (w + 40, 5, L + 20), (242, 240, 234), "Marble")
        GW.cabinets(b, r)
    with wear(sk, surface=GW.STOVE):
        run(r, "Hot Hob", 300, w=110)
        r.along(GW.burner, [60, 130, 200, 260])
        p0, p1, f, L, w, _ = span(r)
        ob(b, "Oven", sub(R2.lerp3(p0, p1, 0.5), (0, 50, 0)), f, (w + 10, 84, L + 10), (40, 42, 48), "Metal")
    return ["Chopping Board", "Hot Hob"]


def k_sink(r, sk, rng):
    """Round the sink rim and a full swirl down the drain, under the faucet."""
    b = r.b
    with wear(sk, surface=GW.STEEL, rails={"edge": (230, 234, 240), "side": CHROME, "side_mat": "Metal"}):
        run(r, "Sink Rim", 160, w=90)
        r.turn("Drain Swirl", -360, 120, dy=-60, rails=True, cp=True)
        C = r.centre
        cy = r.p[1]
        cyl(b, "Drain", (C[0], cy - 30, C[2]), 4, 60, (90, 94, 102), "Metal", b.scenery)
        cyl(b, "SinkWater", (C[0], cy - 29, C[2]), 0.4, 190, (120, 200, 255), "Glass", b.scenery, transp=0.45)
        ringz(b, (C[0], cy - 28.5, C[2]), 50, (200, 240, 255), "Neon", th=0.3, name="WaterSwirl")
        cyl(b, "FaucetStem", (C[0], cy + 60, C[2]), 180, 14, CHROME, "Metal", b.scenery, refl=0.4)
        cyl(b, "FaucetArm", (C[0] + 30, cy + 150, C[2]), 60, 12, CHROME, "Metal", b.scenery, axis=(1, 0, 0), refl=0.4)
        run(r, "Drain Exit", 120, w=90)
    return ["Drain Swirl"]


def k_cake(r, sk, rng, tiers=2):
    """Launch pads up the tiers of a giant cake, candles round the top, a drop back down onto the cake board."""
    b = r.b
    o = obby(r)
    board = slab((206, 210, 218), "Metal", th=4, refl=0.2, deco=edges((240, 242, 246), width=3.0, name="TrayRim"))
    with wear(sk, surface=board):
        o.plat("Cake Board", 100, 120)
    with wear(sk, surface=ghost):
        for k, (L, w, col) in enumerate(((150, 120, (255, 182, 206)), (130, 110, (170, 110, 220)))[2 - tiers:]):
            o.pad(60.0, label="Cake Pad %d" % (k + 1))
            o.plat(("Bottom Tier", "Top Tier")[k], L, w, cp=(k == 1))
            c, R = GW.disc_obj(b, r, col, th=6.0)
            cyl(b, "CakeSponge", sub(c, (0, 31, 0)), 50, 2 * R - 4, (246, 220, 170), "SmoothPlastic", b.scenery)
            for j in range(10):
                a = TAU * j / 10
                hd = 10 + (j % 3) * 4
                cyl(b, "IcingDrip", add(c, (math.cos(a) * (R + 4), -2 - hd / 2, math.sin(a) * (R + 4))), hd, 6, col,
                    "SmoothPlastic", b.scenery)
            coin_row(b, add(c, mul(r.f, -R * 0.4)), add(c, mul(r.f, R * 0.4)), n=3)
        p0, p1, f, L, w, _ = span(r)
        top = R2.lerp3(p0, p1, 0.5)
        for j in range(6):
            a = TAU * (j + 0.5) / 6
            q = add(top, (math.cos(a) * 80, 0, math.sin(a) * 80))
            if abs(dot(sub(q, top), right_of(f))) > 50:
                cyl(b, "Candle", add(q, (0, 25, 0)), 50, 8, [GW.K_RED, GW.K_TEAL, GW.K_YEL][j % 3], "SmoothPlastic", b.scenery)
                ball(b, "CandleFlame", add(q, (0, 54, 0)), 6, (255, 200, 80), "Neon", b.scenery)
        o.drop(60.0 * tiers - 10.0, label="Cake Drop")
    with wear(sk, surface=board):
        o.plat("Cake Plate", 160, 130)
    return ["Cake Climb"]


# ===================================================================== the toybox
def t_blocks(r, sk, rng):
    """Springs up a staircase of giant ABC blocks, then off the top onto a toy track."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.TOY_SHELF):
        o.plat("Toy Shelf", 100, 110)
    with wear(sk, surface=ghost, pad=GW.spring_pad):
        for k, (col, ch) in enumerate(((GW.T_RED, "A"), (GW.T_BLUE, "B"))):
            o.pad(40.0, side=(40, -40)[k], label="Block Spring %d" % (k + 1))
            o.plat("Block %s" % ch, 100, 100, cp=(k == 0))
            GW.cube_obj(b, r, col, letter=ch)
            coin_arc(b, -1, n=4)
        o.drop(80.0, label="Block Drop")
    with wear(sk, surface=GW.TOY_TRACK, rails={"edge": (255, 190, 90), "side": GW.T_ORG}):
        o.plat("Toy Track", 200, 90)
    return ["ABC Blocks"]


def t_bricks(r, sk, rng):
    """A baseplate of toy-brick walls: smash through at speed, or steer round the solid stacks."""
    b = r.b
    with wear(sk, surface=GW.BASEPLATE):
        run(r, "Baseplate", 400, w=130, cp=True, boosts=3, every=40)
        for k, pat in enumerate(("gbb", "b.g", "bbg", ".bb")):
            GW.toy_row(r, 70 + k * 90, 130, pat)
    return ["Toy Brick Walls"]


def t_tops(r, sk, rng):
    """The play table: spinning tops whizz across it; then the toy train shuttles down its track."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.TOY_SHELF):
        o.plat("Table Edge", 80, 110)
    with wear(sk, surface=ghost):
        o.kick(dy=-10.0, label="Table Hop")
        o.plat("Play Table", 300, 140, cp=True)
        c, R = GW.disc_obj(b, r, (255, 236, 200), th=8.0, grow=1.0)
        ringz(b, add(c, (0, 0.1, 0)), R - 6, GW.T_RED, "SmoothPlastic", th=0.2, name="TableBand")
        cyl(b, "TableLeg", sub(c, (0, 70, 0)), 130, 30, GW.T_WOOD, "Wood", b.scenery)
        r.along(GW.top_slider, [80, 160, 240])
    with wear(sk, surface=slab((236, 206, 150), "Wood", th=6, side=(196, 160, 104),
                               deco=both(GW.train_grooves, edges((210, 176, 120), width=3.0, name="TrackEdge")))):
        o.kick(dy=10.0, label="Track Hop")
        o.plat("Train Track", 360, 96, boost=False)
        r.along(lambda b_, c, w, i: GW.toy_train(b_, c, w, i, L=340.0), [180])
    return ["Spinning Tops", "Toy Train"]


def t_balls(r, sk, rng):
    """Giant bouncy balls: land on each and it throws you on to the next."""
    b = r.b
    with wear(sk, surface=GW.plastic(GW.T_PUR)):
        run(r, "Ball Pit Edge", 100, w=100, boosts=2, every=40)
        R2.bounce_chain(r, "Bouncy Balls", [(250.0, 20.0, 40.0), (240.0, 10.0, -60.0), (250.0, -20.0, 40.0)], 230.0, s=96.0,
                        cap=GW.ball_cap((GW.T_RED, GW.T_BLUE, GW.T_YEL)), land_L=150.0, cp=True, shroom=False)
        GW.cube_obj(b, r, GW.T_PUR, panel=False, depth=40)
    return ["Bouncy Balls"]


def t_seesaw(r, sk, rng):
    """A toy seesaw: wait for it to level, then cross; a toy castle's battlements after it."""
    b = r.b
    with wear(sk, surface=GW.plastic(GW.T_YEL)):
        run(r, "Seesaw Ramp", 80, w=80)

        def art(b_, m, c, f, L, w):
            Pt(b_, "SeesawPlank", CF(add(c, (0, -6, 0)), *GW.axes(f)), (w - 4, 8, L - 4), GW.T_YEL, "SmoothPlastic", m)
            for a in (-1, 1):
                Pt(b_, "SeesawSeat", CF(add(c, add(mul(f, a * (L / 2 - 12)), (0, -1, 0))), *GW.axes(f)), (w - 10, 0.4, 16),
                   GW.T_RED, "SmoothPlastic", m)
            M.tri(b_, "Fulcrum", add(c, add(mul(right_of(f), -w / 2), (0, -70, 0))),
                  add(c, add(mul(right_of(f), w / 2), (0, -70, 0))), add(c, (0, -11, 0)), GW.T_RED, th=40)
        GW.rock_bridge(r, "Toy Seesaw", 220, 70, GW.T_YEL, amp_deg=9.0, period=4.2, art=art)
        run(r, "Seesaw Exit", 60, w=80)
    with wear(sk, surface=GW.CASTLE_TOP):
        run(r, "Castle Wall", 300, w=76, cp=True)
        GW.castle_wall(b, r)
        coin_row(b, span(r)[0], span(r)[1], n=5)
    return ["Toy Seesaw", "Castle Wall"]


# ===================================================================== the candy kingdom
def c_bar(r, sk, rng):
    """A chocolate bar whose squares break off and drop a moment after you touch them."""
    with wear(sk, surface=GW.WAFER):
        run(r, "Bar Wrapper", 70, w=120)
    R2.sink_board(r, "Chocolate Bar", 320, 120, cell=40, cols=((112, 64, 38), (98, 56, 32)),
                  mats=("SmoothPlastic", "SmoothPlastic"), delay=0.35, rate=70.0, cp=True)
    with wear(sk, surface=GW.WAFER):
        run(r, "Bar End", 90, w=120)
    return ["Chocolate Bar"]


def c_lollies(r, sk, rng):
    """Hop across the flat swirled tops of giant lollipops."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.WAFER):
        o.plat("Wafer Edge", 80, 110)
    with wear(sk, surface=ghost):
        for k, (dy, side) in enumerate(((0.0, 60.0), (-10.0, -70.0))):
            o.kick(dy=dy, side=side, label="Lolly Hop %d" % (k + 1))
            o.plat("Lollipop %d" % (k + 1), 100, 92, cp=(k == 1))
            GW.lolly_obj(b, r, GW.CANDY[(k + 1) % 5])
            coin_arc(b, -1, n=4)
    with wear(sk, surface=GW.WAFER):
        o.kick(dy=0.0, label="Wafer Hop")
        o.plat("Wafer Landing", 120, 110)
    return ["Lollipop Hops"]


def c_donut(r, sk, rng):
    """Round a giant iced donut, on its sprinkled icing."""
    b = r.b
    with wear(sk, surface=GW.ICING):
        run(r, "Donut Icing", 80, w=80)
        r.turn("Donut Ride", -180, 170, cp=True)
        GW.donut(b, r.centre, 170, r.p[1] - 4.5, tube=80)
        run(r, "Donut Bridge", 60)
        r.turn("Donut Ride 2", 180, 170)
        GW.donut(b, r.centre, 170, r.p[1] - 4.5, tube=80, icing=GW.C_MINT, dough=(150, 90, 50))
        run(r, "Donut Exit", 80)
    return ["Donut Ride", "Second Donut"]


def c_marsh(r, sk, rng):
    """Marshmallow bounces, then a narrow candy-cane bridge."""
    b = r.b
    with wear(sk, surface=GW.MINT):
        run(r, "Mint Run", 100, w=90, boosts=2, every=40)
        R2.bounce_chain(r, "Marshmallow Bounce", [(240.0, 20.0, 50.0), (240.0, -20.0, -60.0)], 230.0,
                        s=90.0, cap=GW.marsh_cap((WHITE, GW.C_PINK, GW.C_MINT)), land_L=120.0, cp=True, shroom=False)
    with wear(sk, surface=GW.CANE):
        run(r, "Cane Bridge Up", 120, w=44, dy=20)
        run(r, "Cane Bridge", 140, w=44)
        coin_row(b, span(r)[0], span(r)[1], n=5)
        run(r, "Cane Bridge Down", 120, w=44, dy=-20)
    return ["Marshmallow Bounce", "Candy Cane Bridge"]


def c_cupcakes(r, sk, rng):
    """Launch pads up two cupcakes' frosting tops, then down onto a jelly-cube bounce."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.WAFER):
        o.plat("Bakery Shelf", 90, 110)
    with wear(sk, surface=ghost):
        for k, col in enumerate((GW.C_PINK, GW.C_MINT)):
            o.pad(50.0, side=(40, -40)[k], label="Cupcake Pad %d" % (k + 1))
            o.plat("Cupcake %d" % (k + 1), 110, 96, cp=(k == 1))
            GW.cupcake_obj(b, r, col, rng)
            coin_row(b, span(r)[0], span(r)[1], n=3)
        o.drop(100.0, label="Cupcake Drop")
    with wear(sk, surface=GW.ICING):
        o.plat("Frosting Run", 140, 110)
    return ["Cupcake Climb"]


def c_jelly(r, sk, rng):
    """Wobbly see-through jelly cubes to bounce across."""
    with wear(sk, surface=GW.ICING):
        run(r, "Jelly Plate", 100, w=100, boosts=2, every=40)
        R2.bounce_chain(r, "Jelly Bounce", [(240.0, 10.0, -50.0), (240.0, -10.0, 50.0)], 230.0, s=96.0,
                        cap=GW.jelly_cap((GW.C_RED, (90, 200, 120), (255, 170, 40))), land_L=140.0, cp=True, shroom=False)
    return ["Jelly Bounce"]


def c_river(r, sk, rng):
    """The chocolate river: its current carries you past gummy bears, then over the chocolate falls."""
    b = r.b
    with wear(sk, surface=GW.CHOC_RIVER):
        R2.belt_road(r, "Chocolate River", 380, 60.0, direction="along", w=120, cp=True)
        p0, p1, f, L, w, _ = span(r)
        for k in range(4):
            sd = 1 if k % 2 else -1
            GW.gummy_bear(b, add(R2.lerp3(p0, p1, 0.15 + 0.22 * k), mul(right_of(f), sd * 34)), 34, GW.CANDY[k],
                          yaw=math.atan2(-f[2], f[0]))
        ob(b, "RiverBed", sub(R2.lerp3(p0, p1, 0.5), (0, 16, 0)), f, (w + 40, 24, L), GW.C_CHOC_DK)
        lip = r.p
        R2.drop_off(r, "Chocolate Falls", 50.0, w=120, L=220, cp=False)
        for sd in (-1, 1):
            q = add(lip, add(mul(right_of(f), sd * 50), (0, -25, 0)))
            ob(b, "ChocFall", add(q, mul(f, 4)), f, (24, 50, 2), (110, 64, 36), "Glass", transp=0.15)
        ob(b, "RiverBed", sub(R2.lerp3(span(r)[0], span(r)[1], 0.5), (0, 16, 0)), f, (w + 40, 24, span(r)[3]), GW.C_CHOC_DK)
    return ["Chocolate River"]


# ===================================================================== the arcade
def a_keyboard(r, sk, rng):
    """A giant keyboard whose keys sink as you drive over them."""
    with wear(sk, surface=GW.PIXEL):
        run(r, "Keyboard Edge", 60, w=130)
    R2.sink_board(r, "Giant Keyboard", 320, 120, cell=40, cols=((236, 236, 244), (200, 200, 214)),
                  mats=("SmoothPlastic", "SmoothPlastic"), delay=0.3, rate=80.0, cp=True)
    with wear(sk, surface=GW.PIXEL):
        run(r, "Spacebar", 100, w=120)
    return ["Giant Keyboard"]


def a_pixels(r, sk, rng):
    """Floating glowing pixel blocks to hop across."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.PIXEL):
        o.plat("Pixel Pad", 80, 100)
        for k, (dy, side) in enumerate(((0.0, 70.0), (-10.0, -70.0))):
            o.kick(dy=dy, side=side, label="Pixel Hop %d" % (k + 1))
            o.plat("Pixel Block %d" % (k + 1), 90, 90, cp=(k == 1))
            p0, p1, f, L, w, _ = span(r)
            c = R2.lerp3(p0, p1, 0.5)
            ob(b, "PixelBody", sub(c, (0, 30, 0)), f, (w, 56, L), (20, 16, 40))
            for sd in (-1, 1):
                ob(b, "PixelGlow", add(c, add(mul(right_of(f), sd * (w / 2 + 0.3)), (0, -30, 0))), f, (0.4, 50, L - 6),
                   GW.NEON[k], "Neon")
            coin_arc(b, -1, n=4)
        o.kick(dy=0.0, label="Pixel Out")
        o.plat("Pixel Landing", 120, 110)
    return ["Pixel Hops"]


def a_screen(r, sk, rng):
    """Spinning giant coins to dodge, then smash straight through a giant screen's wall of pixels."""
    b = r.b
    with wear(sk, surface=GW.CARPET):
        run(r, "Coin Pusher", 300, w=120, cp=True)
        r.along(GW.spin_coin, [70, 160, 240])
        coin_row(b, span(r)[0], span(r)[1], n=6)
    with wear(sk, surface=GW.PIXEL):
        run(r, "Screen Run", 220, w=130, boosts=3, every=40)
        p, f = at(r, 170)
        GW.pixel_screen(b, p, f, 110, 60, M.GHOST, GW.N_PINK)
        run(r, "Screen Exit", 80, w=120)
    return ["Spinning Coins", "Pixel Screen"]


def a_claw(r, sk, rng):
    """The claw machine: it grabs the car and carries it over the gap."""
    with wear(sk, surface=GW.CARPET):
        run(r, "Claw Machine", 120, w=90)
        GW.ride(r, "The Claw", 360.0, dy=0.0, head_fn=GW.claw_head, rail_col=GW.N_PINK, land_L=180.0, w_land=110, cp=True)
    return ["The Claw"]


def a_panel(r, sk, rng):
    """Up a giant cabinet's control panel past its oversized buttons, off the marquee."""
    b = r.b
    with wear(sk, surface=GW.PANEL):
        run(r, "Control Panel", 260, w=120, dy=40, cp=True)
        r.along(GW.giant_button, [70, 140, 200])
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        ob(b, "CabinetBody", (c[0], p0[1] - 8 - 80, c[2]), f, (w + 20, 160, L), (30, 24, 52))
        R2.ramp_jump(r, "Marquee Jump", deg=16, drop=40, w_land=130, slope=3, land_min=280, cp=False, rails=False)
        coin_arc(b, -2, n=6)
    with wear(sk, surface=GW.CARPET):
        run(r, "Arcade Floor", 120, w=110)
    return ["Control Panel", "Marquee Jump"]


# ===================================================================== the enchanted forest
def f_toadstools(r, sk, rng):
    """Along a mossy log, then bounce from toadstool cap to cap."""
    b = r.b
    with wear(sk, surface=GW.MOSS):
        run(r, "Mossy Log", 220, w=96, boosts=2, every=60)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        cyl(b, "FallenLog", sub(c, (0, 62, 0)), L + 40, 130, GW.F_BARK, "Wood", b.scenery, axis=f)
        for k in range(4):
            sd = 1 if k % 2 else -1
            GW.glow_plant(b, add(R2.lerp3(p0, p1, 0.15 + 0.22 * k), mul(right_of(f), sd * (w / 2 + 6))), 20 + (k % 3) * 8,
                          [GW.F_GLOW, GW.F_GLOW2, (255, 230, 120)][k % 3])
        R2.bounce_chain(r, "Toadstool Bounce", [(250.0, 20.0, 50.0), (250.0, 0.0, -60.0), (250.0, -20.0, 40.0)], 230.0, s=100.0,
                        cap=GW.shroom_cap(((220, 50, 50), (150, 80, 220), (255, 140, 40)), rng), land_L=140.0, cp=True,
                        shroom=True)
    return ["Mossy Log", "Toadstool Bounce"]


def f_tree(r, sk, rng):
    """A branch spiralling right round a giant tree (up), then off its tip down the falling leaves."""
    b = r.b
    with wear(sk, surface=GW.BARK, rails={"edge": GW.F_GLOW, "edge_mat": "Neon", "side": GW.F_BARK_DK, "side_mat": "Wood"}):
        run(r, "Root Ramp", 100, w=70)
        r.spiral("Branch Spiral", 1.0, 90, 150, w=70, side=1, core=GW.tree_core, cp=True, rails=True)
        run(r, "Branch Tip", 80, w=64)
    o = obby(r)
    with wear(sk, surface=GW.LEAF):
        o.drop(45.0, side=60.0, label="Leaf Drop")
        o.plat("Big Leaf", 140, 90)
        o.drop(45.0, side=-60.0, label="Leaf Drop 2")
        o.plat("Broad Leaf", 140, 90)
        coin_row(b, span(r)[0], span(r)[1], n=4)
    return ["Branch Spiral", "Falling Leaves"]


def f_leaves(r, sk, rng):
    """Leaves that rock in the breeze, then a glowing flower launches you over the lily pond."""
    b = r.b

    def leaf_art(b_, m, c, f, L, w):
        for sd in (-1, 1):
            Pt(b_, "LeafRim", CF(add(c, add(mul(right_of(f), sd * (w / 2 + 3)), (0, -2, 0))), *GW.axes(f)), (6, 3, L * 0.9),
               (110, 190, 80), "SmoothPlastic", m)
    with wear(sk, surface=GW.LEAF):
        run(r, "Leaf Stalk", 80, w=80)
        GW.swing_bridge(r, "Rocking Leaf", 220, 80, (90, 170, 70), amp_deg=7.0, period=4.6, art=leaf_art)
        run(r, "Leaf Joint", 40, w=80)
        GW.swing_bridge(r, "Rocking Leaf 2", 200, 80, (90, 170, 70), amp_deg=7.0, period=4.6, phase=0.5, art=leaf_art)
        run(r, "Leaf Tip", 80, w=80, cp=True)
    return ["Rocking Leaves"]


def f_lilies(r, sk, rng):
    """A flower launch, lily pads across the pond, and down beside a waterfall."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.MOSS, pad=GW.flower_pad):
        o.plat("Flower Bed", 120, 100)
        o.pad(50.0, label="Flower Launch")
    with wear(sk, surface=ghost):
        o.plat("Lily Pad 1", 100, 90, cp=True)
        GW.lily_obj(b, r, rng)
        for k, (dy, side) in enumerate(((-10.0, 70.0),)):
            o.kick(dy=dy, side=side, label="Lily Hop %d" % (k + 1))
            o.plat("Lily Pad %d" % (k + 2), 100, 90)
            GW.lily_obj(b, r, rng)
            coin_arc(b, -1, n=4)
    with wear(sk, surface=GW.STONE):
        o.kick(dy=0.0, label="Stone Hop")
        o.plat("River Stone", 110, 110)
        lip = r.p
        f = r.f
        R2.drop_off(r, "Waterfall Drop", 40.0, w=110, L=220, cp=False)
        for sd in (-1, 1):
            q = add(lip, add(mul(right_of(f), sd * 75), (0, -20, 0)))
            ob(b, "Waterfall", add(q, mul(f, 10)), f, (30, 60, 3), (150, 220, 255), "Glass", transp=0.3)
    return ["Flower Launch", "Lily Pads", "Waterfall"]


# ===================================================================== construction
def b_crane(r, sk, rng):
    """Along a narrow steel girder, then a tower crane's magnet carries the car onto a container."""
    b = r.b
    with wear(sk, surface=GW.GIRDER):
        run(r, "Steel Girder", 220, w=44, cp=True)
        GW.girder_body(b, r)
        coin_row(b, span(r)[0], span(r)[1], n=5)
    with wear(sk, surface=GW.PLATE):
        run(r, "Crane Pad", 100, w=100)
        MX.crane_transfer(r, "Tower Crane", 380.0, dy=0.0, land_L=150.0, w_land=90, cp=True)
        GW.container_obj(b, r, (200, 60, 40))
    return ["Steel Girder", "Tower Crane"]


def b_containers(r, sk, rng):
    """Hop along a stack of shipping containers, then ride the swinging load over a gap."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.PLATE):
        o.plat("Container Deck", 80, 90)
        for k, (dy, side, col) in enumerate(((-20.0, 60.0, (40, 110, 180)), (10.0, -60.0, (60, 150, 70)))):
            o.kick(dy=dy, side=side, label="Container Hop %d" % (k + 1))
            o.plat("Container %d" % (k + 1), 130, 80, cp=(k == 1))
            GW.container_obj(b, r, col)
            coin_arc(b, -1, n=4)
        o.kick(dy=0.0, label="Stack Hop")
        o.plat("Stack End", 120, 100)
    return ["Container Stack"]


def b_load(r, sk, rng):
    """Ride a crane's swinging load over a gap."""
    with wear(sk, surface=GW.PLATE):
        run(r, "Hook Platform", 120, w=90)
        R2.pendulum_ferry(r, "Swinging Load", Lp=200.0, amp_deg=26.0, period=5.0, deck=(90.0, 70.0), col=(230, 120, 30),
                          mat="CorrodedMetal")
        run(r, "Landing Plate", 120, w=100, cp=True)
    return ["Swinging Load"]


def b_mixer(r, sk, rng):
    """Through a giant concrete pipe, then along a turning cement-mixer drum (jump its blades)."""
    b = r.b
    with wear(sk, surface=GW.CONCRETE):
        run(r, "Pipe Run", 240, w=60, cp=True)
        GW.pipe(b, span(r)[0], span(r)[2], 240, 56)
    with wear(sk, surface=GW.PLATE):
        run(r, "Mixer Chute", 60, w=60)

        def mixer_art(b_, rig, c, f, L, R):
            for k in range(5):
                ringz(b_, add(c, mul(f, -L / 2 + L * (k + 0.5) / 5)), R + 0.6, (230, 120, 30), "SmoothPlastic", th=4, axis=f,
                      parent=rig, name="DrumBand")
            ob(b_, "MixerChassis", sub(c, (0, R + 40, 0)), f, (90, 24, L + 60), GW.K_SAFE)
        GW.drum(r, "Cement Mixer", 220, 40, (210, 210, 206), "Concrete", speed=0.18, ridge_col=GW.K_SAFE, art=mixer_art)
        run(r, "Mixer Exit", 100, w=80)
    return ["Concrete Pipe", "Cement Mixer"]


def b_scaffold(r, sk, rng):
    """Pads up the scaffolding, an excavator's arm sweeping the top deck, then down off the edge."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.PLANKS):
        o.plat("Scaffold Base", 90, 80)
        o.pad(60.0, label="Scaffold Lift")
        o.plat("Scaffold Deck", 220, 100, cp=True)
        GW.scaffold(b, r)
        o.drop(60.0, label="Scaffold Drop")
    with wear(sk, surface=GW.CONCRETE):
        o.plat("Foundation", 260, 120)
        r.along(lambda b_, c, w, i: GW.sweeper(b_, c, w, i, GW.excavator_arm, speed=0.22, tower_fn=GW.excavator_tower), [150])
    return ["Scaffolding", "Excavator"]


def b_truck(r, sk, rng):
    """A gravel conveyor carries you to a dump truck, its tipped bed the ramp."""
    b = r.b
    with wear(sk, surface=slab((120, 116, 110), "Slate", th=4)):
        R2.belt_road(r, "Gravel Conveyor", 320, 70.0, direction="along", w=90, cp=True)
        p0, p1, f, L, w, _ = span(r)
        ob(b, "ConveyorFrame", sub(R2.lerp3(p0, p1, 0.5), (0, 12, 0)), f, (w + 10, 14, L), GW.K_SAFE)
    with wear(sk, surface=by_name({"Ramp": slab((230, 160, 30), "Metal", th=4)}, GW.CONCRETE)):
        run(r, "Truck Run", 100, w=80, boosts=2, every=40)
        R2.ramp_jump(r, "Dump Truck Ramp", deg=18, drop=50, w_land=120, slope=3, land_min=260, cp=False, rails=False)
        lip = r.b.jumps[-2][1]
        f = r.f
        for sd in (-1, 1):
            ob(b, "TruckBedSide", add(lip, add(mul(f, -30), add(mul(right_of(f), sd * 44), (0, -8, 0)))), f, (6, 26, 70),
               (210, 140, 20))
        coin_arc(b, -2, n=6)
        run(r, "Gravel Yard", 120, w=110)
    return ["Gravel Conveyor", "Dump Truck Ramp"]


# ===================================================================== the bedroom
def d_books(r, sk, rng):
    """Up a staircase of giant books, then off the top onto the desk."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.DESK):
        o.plat("Desk Edge", 90, 120)
    with wear(sk, surface=ghost):
        for k, col in enumerate(((180, 40, 50), (40, 90, 170))):
            o.pad(36.0, side=(40, -40)[k], label="Book Step %d" % (k + 1))
            o.plat("Book %d" % (k + 1), 120, 90, cp=(k == 0))
            GW.book_obj(b, r, col)
            coin_arc(b, -1, n=3)
        o.drop(70.0, label="Book Drop")
    with wear(sk, surface=GW.DESK):
        o.plat("Desk Top", 160, 130)
    return ["Book Stairs"]


def d_bed(r, sk, rng):
    """A desk lamp's shade is the ramp onto the bed; pillow bounces across the duvet."""
    b = r.b
    with wear(sk, surface=by_name({"Ramp": slab(GW.B_LAMP, "SmoothPlastic", th=3)}, GW.QUILT)):
        run(r, "Lamp Run", 100, w=80, boosts=2, every=40)
        R2.ramp_jump(r, "Lamp Ramp", deg=20, drop=50, w_land=150, slope=3, land_min=260, cp=True, rails=False)
        GW.lamp_art(b, b.jumps[-2][1], r.f)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        c = (c[0], min(p0[1], p1[1]), c[2])
        ob(b, "Mattress", sub(c, (0, 24, 0)), f, (w + 30, 36, L + 40), (220, 226, 240), "Fabric")
        ob(b, "BedFrame", sub(c, (0, 52, 0)), f, (w + 50, 24, L + 60), (140, 96, 60), "Wood")
    with wear(sk, surface=GW.QUILT):
        R2.bounce_chain(r, "Pillow Bounce", [(240.0, 0.0, 60.0)], 230.0, s=96.0,
                        cap=GW.pillow_cap(((250, 220, 230), (220, 230, 255))), land_L=140.0, cp=False, shroom=False)
    return ["Lamp Ramp", "Pillow Bounce"]


def d_wardrobe(r, sk, rng):
    """Through the wardrobe past the swinging coats, then the rug where toy cars race across."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.SHELF):
        o.plat("Wardrobe Shelf", 260, 100, cp=True, boost=False)
        w0 = span(r)[0]
        r.along(GW.hanger_swing, [90, 170])
        f = r.f
        rt = right_of(f)
        c = R2.lerp3(w0, r.p, 0.5)
        for sd in (-1, 1):
            ob(b, "WardrobeSide", add(c, add(mul(rt, sd * 64), (0, 20, 0))), f, (8, 220, 280), (150, 100, 60), "WoodPlanks")
        ob(b, "WardrobeTop", add(c, (0, 132, 0)), f, (140, 8, 280), (150, 100, 60), "WoodPlanks")
        ob(b, "HangerRail", add(c, (0, 82, 0)), f, (3, 3, 260), (200, 200, 210), "Metal")
        o.drop(40.0, label="Rug Drop")
    with wear(sk, surface=GW.RUG):
        o.plat("Bedroom Rug", 340, 140, boost=False)
        r.along(GW.toy_car_slider, [90, 190, 280])
    return ["Wardrobe", "Toy Cars"]


def d_skate(r, sk, rng):
    """Off a skateboard's kicked-up tail onto a stack of comic books."""
    b = r.b
    comic = slab((240, 220, 80), "SmoothPlastic", th=4, deco=edges(GW.T_RED, width=4.0, name="ComicEdge"))
    with wear(sk, surface=by_name({"Ramp": slab((60, 200, 120), "SmoothPlastic", th=3)}, comic)):
        run(r, "Skate Run", 120, w=80, boosts=2, every=40)
        R2.ramp_jump(r, "Skateboard Ramp", deg=18, drop=40, w_land=120, slope=3, land_min=260, cp=True, rails=False)
        lip = b.jumps[-2][1]
        f = r.f
        for a in (-1, 1):
            for sd in (-1, 1):
                cyl(b, "SkateWheel", add(lip, add(mul(f, -40 + a * 30), add(mul(right_of(f), sd * 30), (0, -14, 0)))), 8, 14,
                    (250, 240, 120), "SmoothPlastic", b.scenery, axis=right_of(f))
        coin_arc(b, -2, n=6)
        p0, p1, f, L, w, _ = span(r)
        cq = R2.lerp3(p0, p1, 0.5)
        ob(b, "ComicStack", (cq[0], min(p0[1], p1[1]) - 26, cq[2]), f, (w + 10, 40, L), (250, 246, 230))
        run(r, "Comic Run", 120, w=110)
    return ["Skateboard Ramp"]


# ===================================================================== the space station
def s_solar(r, sk, rng):
    """Solar panels that roll side to side, then asteroid hops."""
    b = r.b
    with wear(sk, surface=GW.GRATE):
        run(r, "Array Gantry", 80, w=70)
        GW.swing_bridge(r, "Solar Panel", 220, 80, GW.S_SOLAR, "Glass", amp_deg=8.0, period=4.4, art=GW.solar_art)
        run(r, "Array Joint", 40, w=70)
        GW.swing_bridge(r, "Solar Panel 2", 220, 80, GW.S_SOLAR, "Glass", amp_deg=8.0, period=4.4, phase=0.5, art=GW.solar_art)
        run(r, "Array End", 80, w=80, cp=True)
    return ["Solar Panels"]


def s_asteroids(r, sk, rng):
    """Three asteroids to hop, crystals on their rims."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.GRATE):
        o.plat("Airlock", 80, 100)
    with wear(sk, surface=ghost):
        for k, (dy, side) in enumerate(((-20.0, 70.0), (10.0, -70.0))):
            o.kick(dy=dy, side=side, label="Asteroid Hop %d" % (k + 1))
            o.plat("Asteroid %d" % (k + 1), 100, 90, cp=(k == 1))
            GW.asteroid_obj(b, r, rng)
            coin_arc(b, -1, n=4)
    with wear(sk, surface=GW.HULL):
        o.kick(dy=0.0, label="Dock Hop")
        o.plat("Docking Ring", 120, 110)
    return ["Asteroid Hops"]


def s_engine(r, sk, rng):
    """A rocket engine fires you up, then a jump off the upper ring through glowing energy rings."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.HULL, pad=GW.engine_pad):
        o.plat("Engine Deck", 110, 100)
        o.pad(80.0, label="Engine Launch")
        o.plat("Upper Ring", 140, 110, cp=True)
        R2.ramp_jump(r, "Energy Jump", deg=16, drop=90, w_land=130, slope=3, land_min=280, cp=False, rails=False)
        kind, lip, tgt, H, V = b.jumps[-2]
        fj = RT.flat(sub(tgt, lip))
        T = (V + math.sqrt(max(V * V + 2 * G * (tgt[1] - lip[1]), 0.0))) / G
        for k, t in enumerate((0.35, 0.7)):
            tt = T * t
            q = add(lip, add(mul(fj, H * tt), (0, V * tt - G * tt * tt / 2 + CAR_UP, 0)))
            GW.energy_ring(b, q, fj, 40 - k * 4, [GW.S_CYAN, GW.S_ORANGE][k])
        coin_arc(b, -2, n=6)
        run(r, "Ring Deck", 120, w=110)
    return ["Engine Launch", "Energy Rings"]


def s_arms(r, sk, rng):
    """Robot arms sweep the maintenance deck."""
    with wear(sk, surface=GW.GRATE):
        run(r, "Maintenance Deck", 360, w=120, cp=True)
        r.along(lambda b_, c, w, i: GW.sweeper(b_, c, w, i, GW.robot_arm, speed=0.24, tower_fn=GW.arm_base), [90, 190, 290])
    return ["Robot Arms"]


def s_beam(r, sk, rng):
    """A UFO's tractor beam carries you across the void."""
    with wear(sk, surface=GW.HULL):
        run(r, "Beam Pad", 120, w=90)
        R2.tractor_beam(r, "Tractor Beam", 380.0, dy=0.0, land_L=160.0, w_land=110, cp=True)
    return ["Tractor Beam"]


# ===================================================================== the pirate ship
def p_barrels(r, sk, rng):
    """A ship's main deck: barrels roll across it as she heels, a mast and the stormy sea below."""
    b = r.b
    with wear(sk, surface=GW.DECK):
        run(r, "Main Deck", 380, w=130, cp=True)
        GW.hull(b, r)
        r.along(GW.barrel_roll, [110, 210, 300])
        p0, p1, f, L, w, _ = span(r)
        GW.mast(b, add(R2.lerp3(p0, p1, 0.06), mul(right_of(f), -(w / 2 - 14))), 220, f)
        GW.sea(b, R2.lerp3(p0, p1, 0.5), 800, 600, p0[1] - 150)
    return ["Rolling Barrels"]


def p_rigging(r, sk, rng):
    """A cannon fires you up to the crow's nest, out along the yardarm, down onto the deck."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.DECK, pad=GW.cannon_pad):
        o.plat("Quarterdeck", 120, 110)
        GW.hull(b, r, gun_ports=False)
        o.pad(80.0, label="Rigging Launch")
    with wear(sk, surface=GW.SPAR):
        o.plat("Crow's Nest", 110, 70, cp=True)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        cyl(b, "NestBasket", sub(c, (0, 12, 0)), 20, 100, GW.P_DARK, "WoodPlanks", b.scenery)
        cyl(b, "MainMast", sub(c, (0, 160, 0)), 300, 16, GW.P_DARK, "Wood", b.scenery)
        ob(b, "JollyRoger", add(c, add(mul(right_of(f), -60), (0, 50, 0))), f, (0.5, 30, 44), BLACK)
        o.kick(dy=0.0, label="Yard Hop")
        o.plat("Yardarm", 200, 40)
        coin_row(b, span(r)[0], span(r)[1], n=6)
        o.drop(80.0, label="Sail Drop")
    with wear(sk, surface=GW.DARK_DECK):
        o.plat("Gun Deck", 140, 120)
        GW.hull(b, r)
    return ["Crow's Nest", "Yardarm"]


def p_cannon(r, sk, rng):
    """A cannon shot across to a second ship, where a kraken's tentacle sweeps the deck."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.DARK_DECK, pad=GW.cannon_pad):
        o.plat("Gun Deck", 140, 120)
        GW.hull(b, r)
        o.pad(30.0, label="Cannon Shot")
        o.plat("Second Ship", 300, 130, cp=True)
        GW.hull(b, r)
        p0, p1, f, L, w, _ = span(r)
        GW.mast(b, add(R2.lerp3(p0, p1, 0.92), mul(right_of(f), w / 2 - 14)), 200, f)
        GW.sea(b, R2.lerp3(p0, p1, 0.5), 800, 600, p0[1] - 160)
        GW.kraken(b, R2.lerp3(p0, p1, 0.5), f, 1)
        r.along(lambda b_, c, w, i: GW.sweeper(b_, c, w, i, GW.tentacle_arm, speed=0.2, tower_fn=GW.tentacle_root), [160])
        o.drop(30.0, label="Ship Drop")
        o.plat("Lower Deck", 120, 110)
    return ["Cannon Shot", "Kraken"]


def p_treasure(r, sk, rng):
    """A swaying rope bridge, then hop across floating chests of gold."""
    b = r.b

    def rope_art(b_, m, c, f, L, w):
        for sd in (-1, 1):
            Pt(b_, "RopeRail", CF(add(c, add(mul(right_of(f), sd * (w / 2 + 2)), (0, 12, 0))), *GW.axes(f)), (1.4, 1.4, L),
               GW.P_ROPE, "Fabric", m)
    with wear(sk, surface=GW.DECK):
        run(r, "Bridge Post", 80, w=80)
        GW.swing_bridge(r, "Rope Bridge", 260, 56, (150, 104, 60), "WoodPlanks", amp_deg=8.0, period=4.0, art=rope_art)
        run(r, "Bridge Landing", 80, w=80, cp=True)
    o = obby(r)
    with wear(sk, surface=ghost):
        for k, (dy, side) in enumerate(((-20.0, 70.0), (0.0, -70.0))):
            o.kick(dy=dy, side=side, label="Treasure Hop %d" % (k + 1))
            o.plat("Treasure %d" % (k + 1), 100, 90)
            GW.treasure_obj(b, r, rng)
            coin_arc(b, -1, n=5)
    with wear(sk, surface=GW.DECK):
        o.kick(dy=0.0, label="Dock Hop")
        o.plat("Dock", 120, 110)
    return ["Rope Bridge", "Treasure Hops"]


# ===================================================================== the junkyard
def j_tyres(r, sk, rng):
    """Bounce off the hubs of giant tyres lying flat."""
    with wear(sk, surface=GW.TREAD):
        run(r, "Tyre Stack", 100, w=100, boosts=2, every=40)
        R2.bounce_chain(r, "Tyre Bounce", [(250.0, 20.0, 50.0), (250.0, 0.0, -60.0), (250.0, -20.0, 40.0)], 230.0, s=100.0,
                        cap=GW.tyre_cap, land_L=140.0, cp=True, shroom=False)
    return ["Tyre Bounce"]


def j_wrecks(r, sk, rng):
    """Hop across the crumpled roofs of crushed cars."""
    b = r.b
    o = obby(r)
    with wear(sk, surface=GW.SCRAP):
        o.plat("Scrap Edge", 80, 110)
    with wear(sk, surface=ghost):
        for k, (dy, side, col) in enumerate(((-20.0, 60.0, (60, 110, 160)), (10.0, -60.0, (170, 50, 40)))):
            o.kick(dy=dy, side=side, label="Wreck Hop %d" % (k + 1))
            o.plat("Wreck %d" % (k + 1), 110, 80, cp=(k == 1))
            GW.old_car(b, r, col)
            coin_arc(b, -1, n=4)
    with wear(sk, surface=GW.SCRAP):
        o.kick(dy=0.0, label="Scrap Hop")
        o.plat("Scrap Landing", 120, 110)
    return ["Car Wrecks"]


def j_engine(r, sk, rng):
    """Oil drums roll across a giant engine block; then through a duct of giant fans."""
    b = r.b
    with wear(sk, surface=GW.IRON):
        run(r, "Engine Block", 320, w=120, cp=True)
        r.along(GW.oil_drum, [80, 170, 250])
        p0, p1, f, L, w, _ = span(r)
        ob(b, "EngineCasting", sub(R2.lerp3(p0, p1, 0.5), (0, 50, 0)), f, (w + 20, 90, L), (80, 84, 90), "Metal")
        run(r, "Fan Duct", 280, w=70)
        GW.pipe(b, span(r)[0], span(r)[2], 280, 70, col=(120, 100, 90))
        r.along(lambda b_, c, w, i: MX.fan(b_, c, w, i, R=46.0, n=3, speed=0.22, col=(150, 140, 120)), [100, 200])
    return ["Engine Block", "Fan Duct"]


def j_magnet(r, sk, rng):
    """A junkyard magnet crane lifts the car over the crusher."""
    with wear(sk, surface=GW.IRON):
        run(r, "Crusher Edge", 120, w=100)
        MX.crane_transfer(r, "Junk Magnet", 380.0, dy=0.0, land_L=160.0, w_land=100, cp=True)
    return ["Magnet Crane"]


PIECES = {
    "k_plates": k_plates, "k_cake_s": lambda r, sk, rng: k_cake(r, sk, rng, tiers=1), "k_toaster": k_toaster, "k_board": k_board, "k_sink": k_sink, "k_cake": k_cake,
    "t_blocks": t_blocks, "t_bricks": t_bricks, "t_tops": t_tops, "t_balls": t_balls, "t_seesaw": t_seesaw,
    "c_bar": c_bar, "c_lollies": c_lollies, "c_donut": c_donut, "c_marsh": c_marsh, "c_cupcakes": c_cupcakes,
    "c_river": c_river, "c_jelly": c_jelly, "b_load": b_load, "a_keyboard": a_keyboard, "a_pixels": a_pixels, "a_screen": a_screen, "a_claw": a_claw,
    "a_panel": a_panel, "f_toadstools": f_toadstools, "f_tree": f_tree, "f_leaves": f_leaves, "f_lilies": f_lilies,
    "b_crane": b_crane, "b_containers": b_containers, "b_mixer": b_mixer, "b_scaffold": b_scaffold, "b_truck": b_truck,
    "d_books": d_books, "d_bed": d_bed, "d_wardrobe": d_wardrobe, "d_skate": d_skate, "s_solar": s_solar,
    "s_asteroids": s_asteroids, "s_engine": s_engine, "s_arms": s_arms, "s_beam": s_beam, "p_barrels": p_barrels,
    "p_rigging": p_rigging, "p_cannon": p_cannon, "p_treasure": p_treasure, "j_tyres": j_tyres, "j_wrecks": j_wrecks,
    "j_engine": j_engine, "j_magnet": j_magnet,
}


def piece(r, sk, rng, key):
    """Lay giant-world set piece `key` from the turtle on; returns its section names."""
    return PIECES[key](r, sk, rng)


def test_slot(r, sk, rng, keys):
    """(development) a road level made only of host road stretches and the given pieces."""
    names = []
    MX.road(r, "Test Start", 120, w=110, boosts=2)
    for k in keys:
        names += piece(r, sk, rng, k)
        MX.road(r, "Test Link %s" % k, 80, w=100, rails=False)
    return names


def mix_in(r, sk, rng, key, w=100.0, link=100.0):
    """A giant-world piece in a road level, and a short stretch of the level's own road after it (easing to the
    road width w that comes next)."""
    names = piece(r, sk, rng, key)
    r.straight("%s Link" % key, link, w1=w, lead=min(30.0, link / 3), rails=False)
    return names
