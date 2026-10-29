"""Levels 1-10, version 3: each built round its own main idea (see PLAN.md). Pieces from rush2.py."""
import math
from geom import CF, add, sub, mul, unit, UP
from builder import X0, Y0, ZC
import epic_kit as EK
import epic_marks as M
import route as RT
import rush2 as R2
from rush2 import strips, kicker, ramp_jump, drop_off, bounce_chain, belt_road, grease, boost_deck
import skins

TAU = math.pi * 2


def A(u, h, v):
    return (X0 + u, Y0 + h, ZC + v)


def run(r, label, L, w=None, dy=0.0, cp=False, **kw):
    r.straight(label, L, dy=dy, w1=w, lead=min(30.0, L / 4), cp=cp, **kw)
    return r


# ===================================================================== 1. Sugar Rush: the Mega Ramp
# Round and up a giant cake, a strip run off its top into the biggest jump in the game over a chocolate river, a
# candy-cane slalom down the runway, then a second mega ramp onto a narrow wafer runway.
def sugar_rush(r, sk, rng):
    b = r.b
    run(r, "Start", 330, w=64)
    # the cake stands inside the spiral
    C = add(r.p, mul(RT.left_of(r.f), 300))
    M.cake(b, (C[0], 0, C[2]), [(230, Y0 - 40, Y0 + 70, (226, 170, 110), (255, 150, 190)),
                                 (170, Y0 + 70, Y0 + 160, (250, 236, 210), (255, 255, 255)),
                                 (110, Y0 + 160, Y0 + 215, (226, 170, 110), (120, 220, 200))], rng)
    r.solid("cake", C, 236, Y0 - 40, Y0 + 230)
    r.allow.add(("Frosting Spiral", "cake"))
    r.spiral("Frosting Spiral", 1.0, 250.0, 300.0, w=64, side=1, cp=True, rails=True)
    strips(r, "Sprinkle Sprint", 380, w=70, cp=True, rails=True)
    run(r, "Roll-In", 300, dy=-95, rails=True)
    R2.lay_strips(r, 40, 260, every=55)
    river = {}

    def gap(b_, lip, a0, f, w):
        # the chocolate river far below the gap
        mid = R2.lerp3(lip, a0, 0.5)
        M.choc_river(b_, mid[0] - 360, mid[0] + 360, mid[2] - 160, mid[2] + 160, Y0 - 330)
        river["y"] = Y0 - 330

    ramp_jump(r, "Mega Ramp", deg=26, drop=110, w_land=84, slope=12, gap_fn=gap, cp=False)
    # the slalom: candy canes standing on the runway's downhill, a gate every 150, alternate sides
    pts, ws, _ = r.last
    run(r, "Candy Cane Slalom", 520, w=96, dy=-60, cp=True)
    sp, sw, _ = r.last
    cum = [0.0]
    for a_, c_ in zip(sp, sp[1:]):
        cum.append(cum[-1] + math.dist(a_, c_))
    # (each gate fences off 40% of the road from one edge, alternately: weave through the open 60%)
    for k, d in enumerate((120, 280, 440)):
        i = next(i for i in range(len(cum)) if cum[i] >= d)
        p = sp[i]
        f = RT.flat(sub(sp[min(i + 1, len(sp) - 1)], sp[max(i - 1, 0)]))
        sgn = 1 if k % 2 == 0 else -1
        for j in range(4):
            s = sgn * (96 / 2 - 4 - j * 11)
            q = add(p, mul(R2.right_of(f), s))
            M.candy_cane(b, q, 40 + 6 * j, 6, yaw=math.atan2(-f[2], f[0]) + math.pi / 2 * sgn)
            b.part("CaneStop", CF((q[0], q[1] + 18, q[2])), (7, 36, 7), (255, 255, 255), parent=b.scenery,
                   transp=1, collide=True)
    drop_off(r, "Gumball Drop", 70, w=80, cp=False)
    strips(r, "Licorice Climb", 520, dy=150, w=60, cp=True, rails=True)
    ramp_jump(r, "Wafer Leap", deg=18, drop=50, w_land=48, slope=8, rails=True)
    drop_off(r, "Donut Drop", 60, w=64, L=300, cp=True)
    strips(r, "Sugar High", 300, w=64)
    pal = [(255, 120, 170), (120, 220, 200), (255, 210, 90), (170, 140, 255), (255, 150, 90)]
    R2.dress(r, [(lambda b_, c, g: M.lollipop(b_, c, g.uniform(260, 380), g.uniform(110, 160), g.choice(pal), g), 80, 420),
                 (lambda b_, c, g: M.candy_cane(b_, c, g.uniform(280, 380), 26, yaw=g.random() * 6), 50, 400),
                 (lambda b_, c, g: sk.cupcake(b_, add(c, (0, 160, 0)), 150, g), 90, 260)], 18, rng)
    r.log("end")
    return ["Frosting Spiral", "Sprinkle Sprint", "Mega Ramp", "Candy Cane Slalom", "Gumball Drop", "Wafer Leap",
            "Donut Drop"]


# ===================================================================== 2. Drive Thru: Conveyor Kitchen
# Right angles across a kitchen: a turbo belt off the counter, a greased corner, sideways belts over the sink, a
# backwards belt under the burger smashers, fry-basket drops, the express belt home.
def drive_thru(r, sk, rng):
    b = r.b
    run(r, "Start", 160, w=60)
    belt_road(r, "Turbo Belt", 420, 120, "along", w=56, cp=True, rails=True)
    drop_off(r, "Counter Drop", 60, w=72, V=430)
    # the greased corner: a slick across the turn's entry (brake before it, or slide into the rail)
    c = r.ahead(30)
    grease(b, c, r.f, 70, r.w)
    r.turn("Grease Corner", 90, 170, rails=True)
    run(r, "Sink Edge", 60, w=44, cp=True)
    for k, (d_, side) in enumerate((("right", 1), ("left", -1), ("right", 1))):
        belt_road(r, "Sideways Belt %d" % (k + 1), 150, 55, d_, w=44)
    run(r, "Drain Board", 80, w=60)
    r.turn("Tray Corner", -90, 170, rails=True, cp=True)
    belt_road(r, "Backwards Belt", 520, 110, "back", w=64, rails=True)
    R2.lay_strips(r, 30, 500, every=60)
    r.along(EK.ob_press, [150, 290, 430])
    run(r, "Fryer", 60)
    drop_off(r, "Fry Basket Drop 1", 45, w=64, L=260, V=330)
    drop_off(r, "Fry Basket Drop 2", 45, w=64, L=260, V=330, cp=True)
    r.turn("Pass Corner", -90, 200, rails=True)
    run(r, "Grill Line", 60)
    c = r.ahead(40, side=14)
    grease(b, c, r.f, 60, 30)
    belt_road(r, "Grill Belt", 360, 90, "along", w=60, rails=True)
    r.along(EK.ob_press, [120, 250])
    r.turn("Window Corner", 90, 200, rails=True, cp=True)
    belt_road(r, "Order Up Express", 520, 140, "along", w=56, rails=True)
    drop_off(r, "Dish Pit Drop", 50, w=64, L=200, V=470, cp=True)
    c = r.ahead(30, side=-12)
    grease(b, c, r.f, 60, 36)
    for k, d_ in enumerate(("left", "right", "left")):
        belt_road(r, "Dish Pit Belt %d" % (k + 1), 130, 60, d_, w=48)
    belt_road(r, "Shake Sprint", 400, 140, "along", w=56, rails=True)
    R2.dress(r, [(lambda b_, c, g: M.burger(b_, add(c, (0, 120, 0)), 120, g, k=1.3), 170, 360),
                 (lambda b_, c, g: M.milkshake(b_, c, 110, 380, g), 120, 520),
                 (lambda b_, c, g: M.fry_box(b_, c, 150, 280, g), 110, 420),
                 (lambda b_, c, g: M.ketchup(b_, c, 60, 320), 70, 380)], 14, rng)
    r.log("end")
    return ["Turbo Belt", "Counter Drop", "Grease Corner", "Sideways Belts", "Backwards Belt", "Fry Basket Drops",
            "Grill Belt", "Order Up Express", "Dish Pit"]


# ===================================================================== 3. Spore Springs: the Bounce Chain
# Giant mushroom caps that throw you up as you land: steer in the air onto the next one (left, right, higher,
# lower). Two chains, a root slide between them, the forest floor far below.
def shroom_cap(cols, floor_y):
    k = [0]

    def make(b, top, s, rng):
        col = cols[k[0] % len(cols)]
        k[0] += 1
        m = b.model("BounceShroom", b.scenery, {"BounceModel": True})
        keep = b.scenery
        b.scenery = m
        h = top[1] - floor_y - 0.35 * s
        M.giant_mushroom(b, (top[0], floor_y, top[2]), h, s, col, rng)
        b.scenery = keep
        skins.floor(b, top, s * 0.78, round_=True)
    return make


def spore_springs(r, sk, rng):
    b = r.b
    floor_y = Y0 - 330
    cap = shroom_cap([(200, 40, 50), (150, 70, 210), (60, 160, 210), (230, 120, 40)], floor_y)
    run(r, "Start", 120, w=60)
    boost_deck(r, "Spore Run", 340, 260, w=60, cp=True)
    bounce_chain(r, "Cap Chain", [(300, 30, 0), (300, 40, 60), (310, 10, -70), (300, -30, 50)], 260,
                 s=120, cap=cap, land_L=160, cp=True, w_out=60)
    boost_deck(r, "Root Slide", 420, 260, dy=-130, w=56, rails=True)
    bounce_chain(r, "Toadstool Tumble", [(290, -40, 40), (290, -40, -50), (300, -30, 60), (300, -40, -30)], 260,
                 s=110, cap=cap, land_L=160, cp=True, w_out=60)
    boost_deck(r, "Firefly Run", 260, 260, w=60)
    bounce_chain(r, "Firefly Hops", [(300, 50, -40), (300, 50, 40), (310, 0, 0)], 260, s=120, cap=cap, land_L=160,
                 cp=True, w_out=60)
    deco = shroom_cap([(220, 60, 60), (110, 80, 200), (60, 170, 160), (240, 160, 60)], floor_y)
    R2.dress(r, [(lambda b_, c, g: M.giant_mushroom(b_, c, g.uniform(200, 360), g.uniform(120, 200),
                                                     g.choice([(200, 40, 50), (150, 70, 210), (60, 160, 210)]), g), 110, 420),
                 (lambda b_, c, g: M.great_tree(b_, c, 60, c[1], c[1] + g.uniform(380, 520), g, sk), 300, 760)], 16, rng,
            ground=floor_y)
    r.log("end")
    return ["Spore Run", "Cap Chain", "Root Slide", "Toadstool Tumble", "Firefly Hops"]


# ===================================================================== 4. Checkmate: the Falling Board
# Knight's jumps between towers (each one an L: you turn in the air onto the next), a board whose squares drop
# the moment you have passed, rooks sliding across it, and a sprint over a board falling away behind you.
def checkmate(r, sk, rng):
    b = r.b

    def tower(b_, top, s, rng_):
        M.column(b_, "Tower", sub(top, (0, 6, 0)), Y0 - 420, s * 0.9, sk.WHITE if int(top[0] // 7) % 2 else sk.BLACK)
        sk.island(b_, top, s, rng_)
        skins.floor(b_, top, s * 0.9)

    rook = lambda b_, rig, c, k: M.chess_piece(b_, "rook", c, 30, sk.WHITE if k % 2 else sk.BLACK, parent=rig)
    run(r, "Start", 120, w=64)
    boost_deck(r, "Pawn Push", 260, 200, w=60, cp=True)
    bounce_chain(r, "Knight's Tour", [(230, 30, 100), (230, 30, -100), (230, 30, 100), (240, 20, -90)], 200, s=96,
                 cap=tower, land_L=120, cp=True, w_out=64, shroom=False)
    run(r, "Rank Down", 260, dy=-70, w=96)
    R2.sink_board(r, "Rook Rush", 480, 160, sliders=(120, 240, 360), slider_fn=rook)
    run(r, "Castle Gate", 120, w=72, cp=True)
    r.turn("Castle Corner", 90, 260, rails=True)
    boost_deck(r, "Bishop Run", 240, 200, w=60)
    bounce_chain(r, "Knight Descent", [(230, -40, -100), (230, -40, 100), (230, -40, -100), (230, -30, 100)], 200,
                 s=96, cap=tower, land_L=120, cp=True, w_out=64, shroom=False)
    r.turn("File Corner", -90, 300, rails=True)
    strips(r, "Endgame Sprint", 200, w=80, cp=True)
    R2.sink_board(r, "Collapsing Board", 640, 80, delay=0.12, rate=120)
    run(r, "Checkmate", 120, w=72)
    boost_deck(r, "Queen's Charge", 220, 200, w=60)
    bounce_chain(r, "Queen's Gambit", [(230, 40, 90), (230, 40, -90), (240, 0, 0)], 200, s=96, cap=tower, land_L=140,
                 cp=True, w_out=64, shroom=False)
    # the board below, the pieces standing on it
    bc = A(2600, -420, -400)
    M.board(b, (bc[0], 0, bc[2]), 10, 220, Y0 - 420)
    for kind, du, dv, col in (("king", 3.6, 2.8, sk.BLACK), ("queen", -3.8, 2.2, sk.WHITE), ("bishop", 3.0, -3.6, sk.WHITE),
                              ("knight", -2.6, -3.2, sk.BLACK), ("pawn", 1.4, 3.6, sk.WHITE), ("pawn", -1.0, -3.8, sk.BLACK)):
        M.chess_piece(b, kind, (bc[0] + du * 220, Y0 - 420, bc[2] + dv * 220), 260, col)
    R2.dress(r, [(lambda b_, c, g: M.castle(b_, c, 260, 200, 260, g), 190, 380),
                 (lambda b_, c, g: M.chess_piece(b_, g.choice(["rook", "bishop", "pawn", "knight"]), c, 200,
                                                  g.choice([sk.WHITE, sk.BLACK])), 80, 420)], 10, rng, ground=Y0 - 420)
    r.log("end")
    return ["Pawn Push", "Knight's Tour", "Rook Rush", "Knight Descent", "Endgame Sprint", "Collapsing Board",
            "Queen's Gambit"]


# ===================================================================== 5. Tick Tock: Inside the Clock
# The clock's own works carry you: giant gears spinning under the wheels, the hands ticking round as bridges
# (cross while they line up), pendulums ferrying you over the drop; then round and up the tower and off the top.
def tick_tock(r, sk, rng):
    b = r.b
    brass, dark = sk.BRASS, sk.DARK
    run(r, "Start", 120, w=64)
    strips(r, "Mainspring Sprint", 300, w=64, cp=True)
    run(r, "Escapement", 100)
    R2.gear_bridge(r, "Great Wheel", 110, 5.0, col=brass)
    run(r, "Arbor", 60, w=56)
    R2.gear_bridge(r, "Crown Wheel", 90, -7.0, col=(150, 120, 70))
    run(r, "Balance", 120, w=56, cp=True)
    R2.turnstile(r, "Hour Hand", 170, w=44, period=1.8, phase=0.0, col=dark)
    run(r, "Dial Gap", 50, w=50)
    R2.turnstile(r, "Minute Hand", 170, w=44, period=1.8, phase=-0.5, col=dark)
    run(r, "Pendulum Gallery", 100, w=70, cp=True)
    R2.pendulum_ferry(r, "Pendulum Ferry", Lp=240, amp_deg=28, period=5.0, col=brass)
    run(r, "Weight Shelf", 70, w=70)
    R2.pendulum_ferry(r, "Second Pendulum", Lp=260, amp_deg=30, period=5.6, phase=0.5, col=brass)
    run(r, "Bell Loft", 140, w=64, cp=True)
    C = add(r.p, mul(RT.left_of(r.f), 280))
    M.clock_tower(b, (C[0], Y0 - 420, C[2]), 200, r.p[1] + 330, sk, rng)
    r.solid("tower", C, 150, Y0 - 420, r.p[1] + 600)
    r.spiral("Tower Climb", 1.0, 220.0, 280.0, w=60, side=1, rails=True)
    R2.lay_strips(r, 200, 1650, every=150)
    strips(r, "Midnight Sprint", 320, w=64, cp=True, rails=True)
    ramp_jump(r, "Midnight Leap", deg=24, drop=160, w_land=80, slope=12)
    run(r, "Escapement Wheel", 80, w=56, cp=True)
    R2.gear_bridge(r, "Escape Wheel", 100, 8.0, col=(176, 140, 70))
    run(r, "Last Arbor", 60, w=56)
    R2.turnstile(r, "Second Hand", 160, w=44, period=1.4, ease=0.4, col=dark)
    strips(r, "Chime Sprint", 260, w=64)
    R2.dress(r, [(lambda b_, c, g: M.gear(b_, add(c, (0, 330, 0)), g.uniform(110, 170), g.choice([(1, 0, 0), (0, 0, 1)]),
                                          g.choice([brass, (150, 120, 70), (190, 112, 64)]), spin=g.choice([-0.06, 0.05, 0.08])), 180, 520)],
            10, rng)
    r.log("end")
    return ["Mainspring Sprint", "Great Wheel", "Crown Wheel", "Hour Hand", "Minute Hand", "Pendulum Ferry",
            "Tower Climb", "Midnight Leap", "Escape Wheel", "Second Hand"]


# ===================================================================== 6. Toy Box: Slot-Car Speedway
# A narrow orange race track with rails: strips on every straight, big sweepers taken flat out, a figure of eight
# that crosses over itself on a bridge, a chicane, two track-gap jumps, toy-block crushers.
def toy_box(r, sk, rng):
    b = r.b
    w = 46
    run(r, "Start", 100, w=60)
    strips(r, "Grid Launch", 520, w=w, cp=True, rails=True)
    r.log("a")
    r.turn("Big Sweeper", -270, 300, dy=70, rails=True)
    r.log("b")
    run(r, "Crossover Bridge", 330, rails=True)
    r.allow.add(("Crossover Bridge", "Grid Launch"))
    run(r, "Bridge Down", 280, dy=-70, rails=True, cp=True)
    r.log("c")
    r.turn("Hairpin", -90, 300, rails=True)
    r.log("d")
    strips(r, "Back Straight", 420, w=w, rails=True)
    ramp_jump(r, "Track Gap", deg=12, drop=24, slope=4, land_min=200, w_land=w)
    r.turn("Chicane In", -28, 320, rails=True)
    r.turn("Chicane Out", 28, 320, rails=True, cp=True)
    r.log("e")
    run(r, "Crusher Alley", 380, w=56, rails=True)
    r.along(EK.ob_press, [110, 220, 330])
    strips(r, "Pit Straight", 360, w=w, rails=True, cp=True)
    ramp_jump(r, "Double Gap", deg=14, drop=30, slope=5, land_min=220, w_land=w)
    r.turn("Last Sweeper", 50, 420, rails=True)
    r.turn("Last Sweeper Out", -50, 420, rails=True, cp=True)
    strips(r, "Final Lap", 360, w=w, rails=True)
    ramp_jump(r, "Finish Gap", deg=12, drop=24, slope=4, land_min=200, w_land=w)
    R2.dress(r, [(lambda b_, c, g: [M.toy_block(b_, (c[0] + j * 20, c[1] + j * 100, c[2] + j * 12), 100 - j * 10,
                                                 sk.BRICKS[(j + int(c[0])) % 6], yaw=0.3 * j) for j in range(3)], 90, 300),
                 (lambda b_, c, g: M.teddy(b_, c, 300, yaw=g.random() * 6), 170, 560),
                 (lambda b_, c, g: M.duck(b_, c, 240, yaw=g.random() * 6), 150, 300),
                 (lambda b_, c, g: M.spinning_top(b_, c, 200, sk.BRICKS), 110, 260)], 14, rng)
    r.log("end")
    return ["Grid Launch", "Big Sweeper", "Crossover Bridge", "Hairpin", "Back Straight", "Track Gap", "Chicane",
            "Crusher Alley", "Pit Straight", "Double Gap", "Final Lap"]


# ===================================================================== 7. Orbit: Tractor Beams
# UFOs grab the car and carry it across empty space; a launch-pad mega leap with long hang time; an asteroid belt
# you thread at full speed; a ring road round a ringed planet; a comet leap home.
def orbit(r, sk, rng):
    b = r.b
    run(r, "Start", 120, w=70)
    strips(r, "Countdown", 300, w=70, cp=True)
    ramp_jump(r, "Liftoff", deg=30, drop=60, w_land=90, slope=8, cp=True)
    M.planet(b, add(r.p, (0, -330, 260)), 200, (210, 120, 80), (240, 180, 120), rng, moons=2)
    R2.tractor_beam(r, "Tractor Beam", 560, dy=40, cp=True, w_land=80)
    run(r, "Moon Base", 140, w=90)
    # the asteroid belt: rocks to thread at full speed, a row every 110 with a clear lane through each
    strips(r, "Asteroid Belt", 600, w=150, cp=True, first=20, last=500, every=40)
    pts, ws, _ = r.last
    f = r.f
    o = pts[0]
    gaps = [-40, 30, -10, 45, -35]
    for k in range(5):
        d = 110 + 100 * k
        base = add(o, mul(f, d))
        for x in range(-60, 61, 30):
            if abs(x - gaps[k]) < 40:
                continue
            c = add(base, add(mul(R2.right_of(f), x + rng.uniform(-3, 3)), (0, 13, 0)))
            M.asteroid(b, c, 24, rng)
    # the racing line threads the gaps
    inside = lambda p: (p[3] == "r" and 60 < RT.dot(sub(p[:3], o), f) < 580
                        and abs(RT.dot(sub(p[:3], o), R2.right_of(f))) < 80)
    i0 = next(i for i, p in enumerate(b.path) if inside(p))
    rest = [p for p in b.path[i0:] if not inside(p)]
    thread = []
    for k, g in enumerate(gaps):
        for dd in (-25, 0, 25):
            q = add(o, add(mul(f, 110 + 100 * k + dd), mul(R2.right_of(f), g)))
            thread.append((q[0], q[1] + R2.CAR_UP, q[2], "r"))
    b.path[:] = b.path[:i0] + thread + rest
    R2.tractor_beam(r, "Wormhole Beam", 600, dy=30, turn=45, cp=True, w_land=80, land_L=180)
    C = add(r.p, mul(R2.right_of(r.f), 420))
    M.planet(b, add(C, (0, -60, 0)), 220, (90, 140, 220), (200, 230, 255), rng, ring=(280, 0.25, (220, 200, 255)))
    r.solid("ringed", C, 300, r.p[1] - 320, r.p[1] + 200)
    r.turn("Ring Road", -60, 420, w1=70, rails=True, cp=True)
    R2.lay_strips(r, 60, 420, every=120)
    strips(r, "Comet Run", 160, w=70)
    ramp_jump(r, "Comet Leap", deg=24, drop=40, w_land=84, slope=5)
    R2.dress(r, [(lambda b_, c, g: M.planet(b_, add(c, (0, 200, 0)), g.uniform(90, 160),
                                            g.choice([(210, 120, 80), (90, 200, 160), (200, 90, 160), (230, 200, 110)]),
                                            (240, 230, 220), g, moons=g.choice([0, 1, 2])), 190, 380),
                 (lambda b_, c, g: M.asteroid(b_, add(c, (0, g.uniform(180, 330), 0)), g.uniform(40, 80), g), 60, 380)],
            16, rng)
    r.log("end")
    return ["Liftoff", "Tractor Beam", "Asteroid Belt", "Wormhole Beam", "Ring Road", "Comet Leap"]


# ===================================================================== 8. Eruption: Down the Volcano
# Round and down inside the crater, into a lava tube with the roof overhead and jets across it, over causeways the
# lava surges across, then a geyser blasts you up and out over the rim, and an ash slide home.
def eruption(r, sk, rng):
    b = r.b
    import rush
    run(r, "Start", 120, w=64)
    strips(r, "Rim Run", 300, w=64, cp=True)
    C = add(r.p, mul(RT.left_of(r.f), 300))
    R2.crater(b, C, 380, r.p[1] - 330, r.p[1] + 60, rng, gap=RT.flat(sub(r.p, C)), gap_deg=55)
    r.solid("crater", C, 0.0, 0, 0)
    r.spiral("Crater Spiral", 1.0, -230.0, 300.0, w=60, side=1, rails=True, cp=False)
    run(r, "Crater Floor", 100, w=60, cp=True)
    r.straight("Lava Tube", 520, dy=-40, w1=56, lead=30.0, tunnel=46)
    r.along(EK.ob_gate, [140, 280, 420], period=1.6)
    run(r, "Tube Mouth", 80, w=60, cp=True)
    R2.lava_surge(r, "Lava Causeway", 260, w=50, period=3.6, phase=0.0)
    run(r, "Basalt Island", 70, w=70)
    R2.lava_surge(r, "Second Causeway", 260, w=50, period=3.6, phase=0.5)
    run(r, "Vent", 120, w=70, cp=True)
    rush.booster(r, "Geyser Blast", 260, 280, w=70)
    strips(r, "Ash Slide", 600, dy=-150, w=64, rails=True, cp=True)
    ramp_jump(r, "Last Eruption", deg=22, drop=60, w_land=72, slope=6)
    run(r, "Cinder Flats", 80, w=64, cp=True)
    R2.lava_surge(r, "Third Causeway", 220, w=48, period=3.0, phase=0.25)
    strips(r, "Obsidian Run", 300, w=64)
    R2.dress(r, [(lambda b_, c, g: M.obsidian_spire(b_, c, g.uniform(260, 420), g.uniform(50, 90), sk), 70, 420)], 16, rng)
    r.log("end")
    return ["Rim Run", "Crater Spiral", "Lava Tube", "Lava Causeway", "Geyser Blast", "Ash Slide", "Last Eruption",
            "Third Causeway"]


# ===================================================================== 9. Frostbite: Downhill Ski Run
# The chairlift throws you to the summit, then it is downhill all the way: a black run, hairpins, black ice, two ski
# jumps onto steep landing hills, snowballs rolling across the gully, a frozen lake at the bottom.
def frostbite(r, sk, rng):
    b = r.b
    import rush

    def ice(L, w, t=0.5):
        pts = r.last[0]
        R2.ice_patch(b, R2.lerp3(pts[0], pts[-1], t), unit(sub(pts[-1], pts[0])), L, w)

    run(r, "Start", 120, w=70)
    rush.booster(r, "Chairlift", 300, 420, w=80)
    run(r, "Summit", 80, w=80, cp=True)
    strips(r, "Black Run", 480, dy=-120, w=72, rails=True, every=70)
    r.turn("Top Hairpin", -90, 380, dy=-30, rails=True, cp=True)
    run(r, "Glacier", 300, dy=-30, w=72)
    ice(120, 72, 0.45)
    strips(r, "In-Run", 240, dy=-40, w=64, every=60)
    ramp_jump(r, "Ski Jump", deg=10, drop=40, w_land=84, slope=10, cp=True)
    r.turn("Switchback", 180, 380, dy=-30, rails=True, cp=True)
    run(r, "Avalanche Gully", 420, dy=-40, w=84)
    R2.rollers(r, [110, 230, 350])
    strips(r, "Second In-Run", 260, dy=-40, w=64, every=60)
    ramp_jump(r, "Big Air", deg=12, drop=50, w_land=84, slope=10)
    r.turn("Bottom Bend", -90, 400, rails=True, cp=True)
    run(r, "Frozen Lake", 320, w=96)
    ice(240, 96, 0.5)
    strips(r, "Ski Cross", 420, w=72, rails=True, cp=True)
    R2.rollers(r, [150, 280], d=30, period=2.4)
    R2.dress(r, [(lambda b_, c, g: M.mountain(b_, c, g.uniform(380, 520), g.uniform(700, 900), g, sk), 520, 900)], 2, rng,
            near=700, far=1100, ground=Y0 - 700)
    R2.dress(r, [(lambda b_, c, g: M.pine(b_, c, g.uniform(150, 240), g), 40, 240)], 30, rng, near=120, far=500)
    r.log("end")
    return ["Chairlift", "Black Run", "Hairpin", "Black Ice", "Ski Jump", "Avalanche Gully", "Big Air", "Frozen Lake",
            "Ski Cross"]


# ===================================================================== 10. High Score: Arcade Rhythm
# A narrow neon track in a square wave. Boost decks hold you at exactly 260 while laser gates flash on a beat timed
# to that speed: hit the first gate's gap and you clear the whole row. Pinball bumpers, ghosts across the lanes,
# then the high-score jump.
def high_score(r, sk, rng):
    b = r.b
    V = 260.0
    run(r, "Start", 100, w=44)
    boost_deck(r, "Beat Lane", 560, V, w=40, rails=True, cp=True)
    R2.beat_gates(r, [150, 250, 350, 450, 530], V)
    boost_deck(r, "Wave Up", 0, V, turn=90, R=300, rails=True)
    boost_deck(r, "Combo Lane", 420, V, w=40, rails=True, cp=True)
    R2.beat_gates(r, [120, 200, 280, 360], V, period=1.0, on=0.4)
    boost_deck(r, "Wave Down", 0, V, turn=-90, R=300, rails=True)
    run(r, "Pinball Table", 420, w=120, cp=True)
    r.along(EK.ob_bumpers, [100, 200, 300])
    r.turn("Flipper Bend", -90, 300, w1=60, rails=True)
    run(r, "Ghost Alley", 440, w=64, cp=True)
    R2.rollers(r, [100, 200, 300, 380], d=26, period=2.2, col=sk.NEON[1])
    r.turn("Maze Corner", 90, 300, rails=True)
    strips(r, "Power Pellet", 300, w=48, cp=True, rails=True)
    ramp_jump(r, "High Score", deg=20, drop=70, w_land=60, slope=6)
    boost_deck(r, "Bonus Round", 420, V, w=40, rails=True, cp=True)
    R2.beat_gates(r, [110, 170, 230, 290, 350], V, period=0.9, on=0.36)
    run(r, "Game Over", 120, w=56)
    R2.dress(r, [(lambda b_, c, g: M.cabinet(b_, c, 400, 600, 200, sk, yaw=g.random() * 6), 260, 620),
                 (lambda b_, c, g: M.coin(b_, add(c, (0, g.uniform(200, 380), 0)), 110), 60, 440),
                 (lambda b_, c, g: M.ghost(b_, add(c, (0, g.uniform(160, 320), 0)), 13, g.choice(sk.NEON)), 90, 420)],
            14, rng)
    r.log("end")
    return ["Beat Lane", "Combo Lane", "Pinball Table", "Ghost Alley", "Power Pellet", "High Score", "Bonus Round"]


LEVELS = {1: sugar_rush, 2: drive_thru, 3: spore_springs, 4: checkmate, 5: tick_tock, 6: toy_box, 7: orbit, 8: eruption, 9: frostbite,
          10: high_score}
FINAL = {i: [EK.ob_gate] for i in range(1, 11)}
