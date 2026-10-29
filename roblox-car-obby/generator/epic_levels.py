"""The ten epic journeys. Coordinates: A(u, h, v) = u studs down the course from the start, h above the start
height, v to the right (+Z) of the centre line. Headings: H(deg), 0 = down the course, +90 = left, -90 = right."""
import math
from geom import add, sub, mul, unit, cross, UP
from builder import X0, Y0, ZC
import showcase as SC
import journey as J
import epic_kit as EK
import epic_marks as M
import route as RT


def A(u, h, v):
    return (X0 + u, Y0 + h, ZC + v)


def H(deg):
    a = math.radians(deg)
    return (math.cos(a), 0.0, -math.sin(a))


def rot(v, th):
    """Turn a plan vector the way Route.turn does (th > 0 = left)."""
    c, s = math.cos(th), math.sin(th)
    return (v[0] * c + v[2] * s, 0.0, -v[0] * s + v[2] * c)


def on_circle(Cc, start, th, R=None, h=None):
    """The point th (radians, > 0 left) further round centre Cc from `start`, at radius R and height h."""
    v = (start[0] - Cc[0], 0.0, start[2] - Cc[2])
    if R is not None:
        k = R / math.hypot(v[0], v[2])
        v = (v[0] * k, 0.0, v[2] * k)
    w = rot(v, th)
    return (Cc[0] + w[0], start[1] if h is None else h, Cc[2] + w[2])


def tangent(Cc, p, left=True):
    v = (p[0] - Cc[0], 0.0, p[2] - Cc[2])
    return RT.flat(cross(UP, v)) if left else RT.flat(cross(v, UP))


# ===================================================================== 1. Sugar Rush: Cake Mountain
def sugar_rush(r, sk, rng):
    b = r.b
    Cc = A(2080, 0, -930)
    tiers = [(258, Y0 - 120, Y0 + 100, (226, 170, 110), (255, 150, 190)),
             (172, Y0 + 100, Y0 + 228, (250, 236, 210), (255, 255, 255)),
             (104, Y0 + 228, Y0 + 336, (226, 170, 110), (120, 220, 200))]
    M.cake(b, Cc, tiers, rng)
    r.solid("cake", Cc, 258, Y0 - 120, Y0 + 100)
    r.solid("cake2", Cc, 172, Y0 + 100, Y0 + 228)
    r.solid("cake3", Cc, 104, Y0 + 228, Y0 + 400)

    r.straight("Sprinkle Boulevard", 170, w1=76, cp=True)
    r.turn("Sugar Bend", 42, 300, dy=10, w1=80)
    r.local("Sprinkle Stampede", EK.a_frogger, 0.5, rng, W=210, lanes=5)
    E1 = (Cc[0], Y0 + 30, Cc[2] + 340)
    r.w = 64
    r.connect("To the cake", E1, H(0), w1=54, cp=True)
    # 1. round the bottom tier, cake-knife sweepers on the ramp
    r.orbit("Icing Spiral", Cc, 285, dy=105, rails=1, cp=True)
    r.along(EK.ob_sweeper, [260, 520, 800, 1060, 1320, 1560])
    # 2. macaron towers standing on the bottom tier, climbing round it
    start = r.p
    tg = []
    for k in range(1, 6):
        tg.append(on_circle(Cc, start, math.radians(34 * k), R=214, h=r.p[1] + 26 * k))
    r.hops("Macaron Stairs", tg, plat=lambda b_, t, s, rng_: (M.column(b_, "MacaronPillar", sub(t, (0, 16, 0)), Y0 + 100, 14,
                                                                           (255, 250, 240)),
                                                              sk.macaron(b_, t, s, rng_)), s=64)
    # 3. a pad onto the candle crown: the road round the second tier
    E3 = on_circle(Cc, tg[-1], math.radians(42), R=142, h=tg[-1][1] + 14)
    src = add(tg[-1], mul(RT.flat(sub(E3, tg[-1])), 16))
    RT._pad_any(b, src, E3)
    sk.island(b, E3, 76, rng)
    r.p, r.f, r.w = E3, tangent(Cc, E3, True), 50
    r.orbit("Candle Crown", Cc, 230, dy=56, rails=1, cp=True)
    r.along(EK.ob_gate, [140, 300, 460])
    # 4. off the top of the cake, a long leap down onto the candy-cane slide
    r.straight("Cake Top", 60, w1=56)
    r.pad_jump("Cherry Leap", 360, -70, w_land=60, L_land=170, rings=4)
    r.log("leap")
    r.w = 44
    r.connect("Slide Entry", A(3020, 210, -520), H(-55), w1=44)
    r.straight("Candy-Cane Slide", 900, dy=-170, swing=70, waves=3, rails=True)
    for k in range(6):
        p = r.last[0][int(len(r.last[0]) * (k + 0.5) / 6)]
        M.candy_cane(b, (p[0] + (60 if k % 2 else -60), p[1] - 200, p[2] + (90 if k % 2 else -90)), 190, 14, yaw=k)
    r.log("slide")
    # 5. the low road: a licorice tightrope over the chocolate river, a launch up to the wafer floor
    r.turn("Fudge Bend", -35, 220, w1=60, cp=True)
    r.local("Licorice Tightrope", J.narrow, 0.5, rng, L=420, w=14, weave=36)
    r.log("rope")
    r.turn("Caramel Bend", 90, 190, w1=64)
    r.pad_jump("Gingerbread Launch", 300, 170, w_land=70, L_land=150, rings=3)
    r.local("Wafer Floor", EK.a_crumble_field, 0.6, rng, W=150, L=300)
    r.log("wafer")
    r.straight("Wafer Run", 60, w1=48)
    r.spiral("Lollipop Spiral", 1.0, -195, 120, side=1, rails=1,
             core=lambda b_, c, R: M.lollipop(b_, (c[0], c[1] - 260, c[2]), 330, 170, (255, 120, 170), rng))
    r.log("spiral")
    r.turn("Sprinkle Bend", 90, 160, w1=56)
    r.local("Donut Loop", SC.m_loop, 0.6, rng)
    r.log("loop")
    r.local("Gumdrop Bumpers", EK.a_bumper_field, 0.6, rng, W=170, L=300)
    r.log("bumpers")
    return ["Sprinkle Stampede", "Icing Spiral", "Macaron Stairs", "Candle Crown", "Cherry Leap", "Candy-Cane Slide", "Licorice Tightrope", "Gingerbread Launch", "Wafer Floor", "Lollipop Spiral", "Donut Loop", "Gumdrop Bumpers"]




# ===================================================================== 2. Drive Thru: Kitchen Rush (zig-zag legs, a burger to climb)
def drive_thru(r, sk, rng):
    b = r.b
    BC = A(2260, -60, -120)
    top = M.burger(b, BC, 200, rng, k=1.6)
    r.solid("burger", BC, 214, BC[1], top)
    SH = A(3230, -260, -760)
    M.milkshake(b, SH, 150, 470, rng)
    r.solid("shake", SH, 152, SH[1], SH[1] + 560)
    for (u, v, hgt) in ((620, -420, 300), (1500, 1250, 260)):
        M.fry_box(b, A(u, -260, v), 150, hgt, rng)
    M.ketchup(b, A(4300, -300, 700), 60, 420)

    r.local("Drive-Thru Lane", J.tunnel_run, 0.5, rng, L=420, w=56, boosts=2)
    r.turn("Order Bend", -90, 200, w1=72, cp=True)
    r.local("Conveyor Grill", EK.a_belts_wide, 0.5, rng, W=130, n=5)
    r.w = 60
    r.straight("Patty Smashers", 380)
    r.along(EK.ob_press, [80, 190, 300])
    r.log("leg1")
    r.turn("Grill Hairpin", 180, 170, dy=70, rails=1, cp=True)
    r.log("hairpin1")
    fry = lambda b_, t, s_, rng_: (M.column(b_, "FryPillar", sub(t, (0, 12, 0)), t[1] - 240, 20, (255, 214, 90)),
                                   sk.frybox(b_, t, s_, rng_))
    tg = [r.ahead(200 * k, (40 if k % 2 else -40), 30 * k) for k in range(1, 6)]
    r.hops("Fry Forest", tg, plat=fry, s=60, land=(210, 10, 64, 150))
    r.local("Plate Spinners", EK.a_turntables, 0.6, rng, n=3, R=92)
    r.log("plates")
    r.turn("Grease Hairpin", -180, 180, dy=-60, rails=1, cp=True)
    r.log("hairpin2")
    E = (BC[0] - 300, Y0 + 20, BC[2])
    r.connect("To the burger", E, H(-90), w1=56)
    r.orbit("Burger Climb", BC, 540, dy=330, rails=1, cp=True)
    r.along(EK.ob_sweeper, [300, 650, 1000, 1350, 1700, 2050, 2400])
    r.log("burger")
    r.straight("Bun Top", 60, w1=60)
    b.skin.launcher(b, r.ahead(-16), 60)
    r.pad_jump("Spatula Catapult", 420, -60, w_land=70, L_land=170, rings=4)
    r.log("catapult")
    E2 = (SH[0], Y0 + 300, SH[2] + 250)
    r.connect("Counter Run", E2, H(0), w1=50)
    r.orbit("Milkshake Spiral", SH, 450, dy=-250, rails=1, cp=True)
    r.along(EK.ob_gate, [400, 800, 1200, 1600])
    r.log("shake")
    r.straight("Straw Run", 80, w1=60)
    r.local("Straw Tightrope", J.narrow, 0.6, rng, L=440, w=12, weave=40)
    r.turn("Napkin Bend", -60, 220, w1=70)
    r.local("Salt & Pepper Rush", EK.a_frogger, 0.7, rng, W=210, lanes=5)
    r.log("frogger")
    r.local("Rolling Pin", SC.m_log, 0.7, rng)
    return ["Drive-Thru Lane", "Conveyor Grill", "Patty Smashers", "Fry Forest", "Plate Spinners", "Burger Climb", "Spatula Catapult", "Milkshake Spiral", "Straw Tightrope", "Salt & Pepper Rush", "Rolling Pin"]


# ===================================================================== 3. Spore Springs: The Great Tree (up the trunk, over the canopy)
def spore_springs(r, sk, rng):
    b = r.b
    TC = A(2500, 0, 450)
    M.great_tree(b, TC, 110, Y0 - 420, Y0 + 400, rng, sk)
    r.solid("tree", TC, 150, Y0 - 420, Y0 + 400)
    M.glow_pond(b, TC, 700, Y0 - 430)
    for (u, v, h, d, col) in ((900, -600, 260, 220, (190, 40, 50)), (1700, -800, 340, 260, (150, 60, 200)),
                              (3900, 900, 300, 240, (190, 40, 50)), (4700, -500, 220, 200, (60, 150, 200))):
        M.giant_mushroom(b, A(u, -420, v), h + 300, d, col, rng)

    r.local("Hollow Trunk", J.tunnel_run, 0.5, rng, L=440, dy=-60, w=48, boosts=2)
    r.local("Glowroot Cavern", J.cave, 0.5, rng, L=700)
    r.log("cave")
    E = (TC[0] - 260, Y0 - 50, TC[2])
    r.w = 56
    r.connect("Root Road", E, H(-90), w1=54, cp=True)
    r.orbit("Shelf-Fungus Spiral", TC, 630, dy=330, rails=1, cp=True)
    r.along(EK.ob_swing, [250, 520, 800, 1080, 1360, 1640, 1920, 2200])
    r.log("trunk")
    r.straight("Branch Walk", 140, w1=40)
    cap = lambda b_, t, s_, rng_: (M.column(b_, "CapStem", sub(t, (0, 10, 0)), t[1] - 160, 22, (236, 226, 200)),
                                   sk.toadstool(b_, t, s_, rng_))
    r.hop_arc("Canopy Caps", 6, 300, 200, dy=18, side=1, plat=cap, s=64, land=(220, -20, 56, 150))
    r.log("canopy")
    r.local("Vine Tightrope", J.narrow, 0.6, rng, L=420, w=14, weave=44)
    r.local("Rolling Log", SC.m_log, 0.6, rng)
    r.w = 50
    r.turn("Vine Bend", 90, 160, w1=50)
    r.straight("Leaf Slide", 1000, dy=-300, swing=80, waves=3, rails=True, cp=True)
    r.log("slide")
    r.turn("Moss Bend", -90, 200, w1=70)
    r.local("Spore Bumpers", EK.a_bumper_field, 0.6, rng, W=180, L=380)
    r.local("Puffball Field", EK.a_crumble_field, 0.6, rng, W=150, L=270)
    r.log("end")
    return ["Hollow Trunk", "Glowroot Cavern", "Shelf-Fungus Spiral", "Canopy Caps", "Vine Tightrope", "Rolling Log", "Leaf Slide", "Spore Bumpers", "Puffball Field"]


# ===================================================================== 4. Checkmate: Castle Siege (a giant board, a castle wall to climb)
def checkmate(r, sk, rng):
    b = r.b
    BCc = A(1500, -60, -650)
    M.board(b, BCc, 8, 110, Y0 - 300)
    pieces = [("king", 2.0, 2.5, sk.BLACK), ("queen", -2.5, 1.0, sk.WHITE), ("rook", 3.2, -3.0, sk.WHITE),
              ("bishop", -1.0, -3.2, sk.BLACK), ("knight", 0.5, 3.4, sk.WHITE), ("pawn", -3.3, -1.0, sk.BLACK)]
    for kind, du, dv, col in pieces:
        M.chess_piece(b, kind, (BCc[0] + du * 110, Y0 - 300, BCc[2] + dv * 110), 120, col)
    CC = A(3700, -200, 500)
    M.castle(b, CC, 600, 420, 420, rng)
    r.solid("castle", CC, 0, Y0 - 200, Y0 + 260, box=(312, 222))

    r.local("Pawn Stampede", EK.a_frogger, 0.5, rng, W=220, lanes=5,
            block=lambda b_, rig, c, s_, i: M.chess_piece(b_, "pawn", (c[0], c[1] - 4, c[2]), 30,
                                                          sk.WHITE if i % 2 else sk.BLACK) and None)
    r.turn("Board Bend", 35, 240, w1=60, cp=True)
    # knight's tour: every hop is an L (two forward, one aside), so the course zig-zags across the board
    f = r.f
    lf = RT.left_of(f)
    tg = []
    q = r.p
    for k in range(6):
        side = 1 if k % 2 == 0 else -1
        q = add(q, add(mul(f, 170), add(mul(lf, side * 85), (0, 15, 0))))
        tg.append(q)
    sq = lambda b_, t, s_, rng_: (M.column(b_, "SquarePillar", sub(t, (0, 8, 0)), t[1] - 220, 26, sk.GOLD), sk.plat(b_, t, s_, rng_))
    r.hops("Knight's Tour", tg, plat=sq, s=64, land=(220, -20, 70, 150))
    r.log("knight")
    r.turn("Queen's Bend", -35, 240, w1=90)
    r.local("Grand Board", EK.a_sweep_field, 0.6, rng, W=260, n=2, arms=4, speed=0.09)
    r.log("grand")
    E = (CC[0] - 360, Y0 - 30, CC[2] - 210)
    r.connect("Moat Road", E, H(-90), w1=56, cp=True)
    # the rampart switchbacks: zig-zag up beside the castle's west wall (each leg climbs over the one before)
    for k in range(3):
        r.straight("Rampart %d" % (k + 1), 330, dy=95, rails=1)
        r.along(EK.ob_press if k != 1 else EK.ob_door, [110, 230])
        if k < 2:
            r.turn("Rampart Turn %d" % (k + 1), -180, 64, dy=10, rails=1)
    r.log("ramparts")
    r.turn("Battlement Bend", 90, 110, w1=50)
    r.straight("Battlements", 300, w1=50)
    r.along(EK.ob_gate, [90, 200])
    r.log("battle")
    r.pad_jump("Drawbridge Leap", 380, -150, w_land=70, L_land=170, rings=4)
    r.log("leap")
    r.spiral("Tower Stair Down", 1.0, -150, 110, side=-1, w=46,
             core=lambda b_, c, R: b_.skin.helix_core(b_, c, c[1], c[1] + 150, R, 46, True))
    r.log("end")
    return ["Pawn Stampede", "Knight's Tour", "Grand Board", "Rampart Switchbacks", "Battlements", "Drawbridge Leap", "Tower Stair Down"]


# ===================================================================== 5. Tick Tock: The Grand Clock (round the face, through the works)
def tick_tock(r, sk, rng):
    b = r.b
    FC = A(2300, 240, -650)
    M.clock_face(b, FC, 520, FC[1] - 6, sk, rng)
    r.solid("face", FC, 470, FC[1] - 80, FC[1] - 4)
    for (u, h, v, R, ax, sp) in ((1100, -150, 300, 160, (0, 0, 1), 0.03), (3600, -80, 420, 220, (1, 0, 0), -0.02),
                                 (4600, 60, -500, 180, (0, 0, 1), 0.025), (2300, 0, -650, 300, UP, 0.0)):
        M.gear(b, A(u, h, v), R, ax, sk.BRASS if R % 2 else sk.COPPER, spin=sp, th=16)
    gearp = lambda b_, t, s_, rng_: sk.gear(b_, t, s_, rng_)
    tg = [r.ahead(190 * k, 0, 32 * k) for k in range(1, 5)]
    r.hops("Gear Steps", tg, plat=gearp, s=64, land=(210, 20, 60, 150))
    r.log("gears")
    r.local("Escapement", EK.a_piston_sea, 0.6, rng, W=160, L=320)
    r.log("pistons")
    E = (FC[0], FC[1], FC[2] + 470)
    r.connect("Up to the face", E, H(0), w1=56, cp=True)
    # round the rim of the face, the giant hands sweeping over it
    root = b.prop_root("MinuteHand")
    rig = b.rig(root, "Spin", M.axis_frame((FC[0], FC[1] + 3, FC[2]), UP), 0.035, 4, name="Hand")
    M.Pt(b, "MinuteHand", M.CF((FC[0] + 215, FC[1] - 3.5, FC[2])), (430, 2, 26), sk.INK, "Metal", rig)
    M.Pt(b, "MinuteTip", M.CF((FC[0] + 470, FC[1] + 3.4, FC[2])), (72, 3.2, 10), sk.danger, "Neon", rig, query=True,
         attrs={"ObbyHazard": "Burn"})
    M.Pt(b, "MinuteRiser", M.CF((FC[0] + 432, FC[1], FC[2])), (4, 7, 10), sk.INK, "Metal", rig)
    for lab in ("Up to the face", "Clock Rim", "Twelve O'Clock"):
        r.allow.add((lab, "face"))
    rig2 = b.rig(b.prop_root("HourHand"), "Spin", M.axis_frame((FC[0], FC[1] - 4, FC[2]), UP), -0.06, 4, phase=0.4,
                 name="Hand")
    M.Pt(b, "HourHand", M.CF((FC[0] - 150, FC[1] - 4, FC[2])), (300, 2, 40), sk.INK, "Metal", rig2)
    M.C(b, "HandsPin", (FC[0], FC[1] + 10, FC[2]), 12, 50, sk.BRASS, "Metal")
    r.orbit("Clock Rim", FC, 360, dy=40, rails=1)
    r.along(EK.ob_sweeper, [500, 1150, 1800], low=True)
    r.log("rim")
    r.straight("Twelve O'Clock", 80, w1=56)
    r.pad_jump("Cuckoo Leap", 360, -140, w_land=64, L_land=170, rings=3)
    r.log("leap")
    r.local("Pendulum Hall", SC.m_swings, 0.7, rng)
    r.turn("Mainspring Bend", -40, 200, w1=50, cp=True)
    r.spiral("Mainspring Spiral", 1.0, -110, 120, side=-1, w=48,
             core=lambda b_, c, R: b_.skin.helix_core(b_, c, c[1], c[1] + 110, R, 48, False))
    r.log("spring")
    r.local("Cog Bridges", SC.m_spin_bridges, 0.7, rng)
    r.local("Gear Teeth", SC.m_pistons, 0.7, rng)
    r.log("teeth")
    r.turn("Balance Bend", 80, 200, w1=60)
    r.local("Balance Wheel", EK.a_sweep_field, 0.7, rng, W=230, n=2, arms=3, speed=0.1)
    r.log("end")
    return ["Gear Steps", "Escapement", "Clock Rim", "Cuckoo Leap", "Pendulum Hall", "Mainspring Spiral", "Cog Bridges", "Gear Teeth", "Balance Wheel"]


# ===================================================================== 6. Toy Box: Playroom Grand Prix (a race track that loops over itself)
def toy_box(r, sk, rng):
    b = r.b
    M.teddy(b, A(2300, -380, 1000), 300)
    M.duck(b, A(4300, -380, -800), 220)
    M.spinning_top(b, A(1500, -300, -700), 200, sk.BRICKS)
    for k, (u, v) in enumerate(((900, 900), (3300, -900), (4800, 800))):
        for j in range(3):
            M.toy_block(b, A(u + j * 25, -380 + j * 110, v + j * 15), 110 - j * 10, sk.BRICKS[(k + j) % 6])
    r.w = 70
    r.straight("Starting Straight", 480, w1=70, boosts=[160], cp=True)
    r.turn("Big Banked Loop", 270, 250, dy=90, rails=True)
    r.along(EK.ob_bumpers, [300, 650, 1000])
    r.log("loop1")
    r.straight("Crossover Bridge", 620, dy=10)
    r.log("cross")
    r.local("Track Loop", SC.m_loop, 0.6, rng)
    r.turn("Kerb Bend", 90, 220, w1=56)
    r.local("Wall Ride", SC.m_wallride, 0.6, rng)
    r.log("bend")
    r.local("Block Tower", SC.m_tower, 0.6, rng)
    r.local("Spring Launcher", J.launch_up, 0.6, rng, dy=150, D=260)
    r.log("spring")
    r.local("Domino Run", SC.m_crushers, 0.7, rng)
    r.turn("Rainbow Bend", 70, 240, w1=50, rails=True)
    r.straight("Playground Slide", 1000, dy=-240, swing=60, waves=3, rails=True, cp=True)
    r.log("slide")
    r.turn("Toy Train Bend", -80, 220, w1=70)
    r.local("Toy Train Crossing", EK.a_frogger, 0.7, rng, W=200, lanes=4)
    r.local("Toy Bumpers", EK.a_bumper_field, 0.6, rng, W=160, L=320)
    r.log("end")
    return ["Big Banked Loop", "Crossover Bridge", "Track Loop", "Wall Ride", "Block Tower", "Spring Launcher", "Domino Run", "Playground Slide", "Toy Train Crossing", "Toy Bumpers"]


# ===================================================================== 7. Orbit: Planet Hopper (ring roads round planets, hops between them)
def orbit(r, sk, rng):
    b = r.b
    P1 = A(1450, 0, -520)
    M.planet(b, P1, 170, (210, 120, 80), (240, 180, 120), rng, moons=2)
    r.solid("p1", P1, 175, P1[1] - 175, P1[1] + 175)
    P2 = A(3000, 230, 560)
    M.planet(b, P2, 190, (90, 140, 220), (200, 230, 255), rng, ring=(330, 0.3, (220, 200, 255)))
    r.solid("p2", P2, 195, P2[1] - 195, P2[1] + 195)
    M.planet(b, A(4500, -330, -900), 260, (120, 200, 160), (220, 255, 230), rng, moons=3)
    M.station(b, A(4300, 330, 700), 160, sk)

    r.local("Launch Tube", J.tunnel_run, 0.5, rng, L=420, dy=60, w=48, boosts=3)
    E = (P1[0], Y0 + 60, P1[2] + 260)
    r.connect("To Mars", E, H(0), w1=52, cp=True)
    r.orbit("Mars Ring", P1, 360, dy=100, rails=1)
    r.along(EK.ob_gate, [300, 700, 1100, 1450])
    r.log("mars")
    r.straight("Slingshot Ramp", 80, w1=60)
    r.pad_jump("Slingshot", 400, 50, w_land=64, L_land=170, rings=5)
    r.log("sling")
    E2 = (P2[0] - 300, P2[1] - 40, P2[2])
    r.connect("To Neptune", E2, H(-90), w1=50)
    rock = lambda b_, t, s_, rng_: (M.asteroid(b_, sub(t, (0, s_ * 0.3, 0)), s_ * 0.9, rng_), sk.plat(b_, t, s_, rng_))
    r.hop_arc("Ring Shards", 6, 300, 180, dy=12, side=1, plat=rock, s=60, land=(220, -30, 60, 150))
    r.log("ring")
    r.straight("Comet Dive", 520, dy=-200, rails=True, w1=52)
    r.turn("Station Approach", -90, 220, w1=56, cp=True)
    r.local("Station Spin", EK.a_turntables, 0.7, rng, n=2, R=100)
    r.local("Zero-G Tube", SC.m_pipe, 0.7, rng)
    r.local("Ring Loop", SC.m_loop, 0.7, rng)
    r.log("end")
    return ["Launch Tube", "Mars Ring", "Slingshot", "Ring Shards", "Comet Dive", "Station Spin", "Zero-G Tube", "Ring Loop"]


# ===================================================================== 8. Eruption: Lava Canyon (switchbacks down into a canyon, out on a geyser)
def eruption(r, sk, rng):
    b = r.b
    r.w = 64
    r.straight("Canyon Rim", 200, w1=64, cp=True)
    r.turn("Rim Bend", 90, 200)
    r.straight("Switchback 1", 520, dy=-110, rails=1)
    r.along(EK.ob_sweeper, [260])
    r.turn("Hairpin 1", -180, 120, dy=-20, rails=1)
    r.straight("Switchback 2", 520, dy=-110, rails=1)
    r.along(EK.ob_press, [160, 330])
    r.turn("Hairpin 2", 180, 120, dy=-20, rails=1)
    r.straight("Switchback 3", 420, dy=-80, rails=1)
    r.log("down")
    r.turn("Canyon Floor Bend", -90, 220, w1=60, cp=True)
    r.straight("Lava River Road", 760, swing=140, waves=3)
    r.along(EK.ob_gate, [150, 330, 510])
    M.canyon(b, r.last[0], 70, 260, rng, sk, r.p[1] - 120)
    r.log("river")
    stone = lambda b_, t, s_, rng_: (M.obsidian_spire(b_, (t[0], t[1] - 262, t[2]), 250, s_ * 0.7, sk, tip=False), sk.plat(b_, t, s_, rng_))
    r.hop_arc("Obsidian Stones", 5, 300, 90, dy=12, side=-1, plat=stone, s=60, land=(210, 0, 60, 150))
    r.log("stones")
    r.local("Magma Chamber", J.cave, 0.6, rng, L=700)
    r.log("cave")
    r.turn("Ash Bend", 90, 200, w1=60)
    r.local("Crumbling Crust", EK.a_crumble_field, 0.7, rng, W=150, L=300)
    r.local("Geyser Blast", J.launch_up, 0.7, rng, dy=230, D=260)
    r.log("geyser")
    r.local("Lava Pistons", EK.a_piston_sea, 0.7, rng, W=120, L=280)
    r.local("Lava Fall", J.cliff_drop, 0.7, rng, dy=140)
    r.log("end")
    return ["Canyon Switchbacks", "Lava River Road", "Obsidian Stones", "Magma Chamber", "Crumbling Crust", "Geyser Blast", "Lava Pistons", "Lava Fall"]


# ===================================================================== 9. Frostbite: Summit Run (up the spire, hairpins down the mountain)
def frostbite(r, sk, rng):
    b = r.b
    MC = A(1350, -420, -1180)
    M.mountain(b, MC, 470, 900, rng, sk)
    r.solid("mountain", MC, 480, Y0 - 420, Y0 + 480)
    for k in range(14):
        a = rng.random() * TAU
        d = rng.uniform(650, 950)
        M.pine(b, (MC[0] + math.cos(a) * d, Y0 - 380, MC[2] + math.sin(a) * d), rng.uniform(140, 240), rng)
    SP = A(900, 0, 520)
    r.straight("Base Camp", 200, w1=64, cp=True)
    r.turn("Lift Bend", -60, 220)
    E = (SP[0], Y0 + 10, SP[2] - 200)
    r.connect("To the spire", E, H(0), w1=52)
    r.orbit("Ice Spire Climb", SP, -630, dy=360, rails=1, cp=True)
    b.skin.helix_core(b, (SP[0], Y0, SP[2]), Y0, Y0 + 370, 200, 52, False)
    r.along(EK.ob_sweeper, [300, 650, 1000, 1350, 1700, 2050])
    r.log("spire")
    r.straight("Summit Ramp", 60, w1=60)
    r.pad_jump("Ski Jump", 400, -110, w_land=72, L_land=180, rings=4)
    r.log("ski")
    for k in range(4):
        r.straight("Mountain Pass %d" % (k + 1), 380, dy=-70, rails=1)
        r.along([EK.ob_press, EK.ob_swing, EK.ob_sweeper, EK.ob_gate][k], [120, 260])
        if k < 3:
            r.turn("Hairpin %d" % (k + 1), -180 if k % 2 == 0 else 180, 110, dy=-15, rails=1)
    r.log("pass")
    r.turn("Glacier Bend", 90, 200, w1=56, cp=True)
    r.local("Ice Cavern", J.cave, 0.7, rng, L=700)
    r.log("cave")
    r.local("Frozen Lake", SC.m_rink, 0.7, rng)
    r.local("Avalanche", EK.a_frogger, 0.7, rng, W=200, lanes=4)
    r.log("aval")
    r.local("Icicle Crushers", SC.m_crushers, 0.7, rng)
    r.log("end")
    return ["Ice Spire Climb", "Ski Jump", "Mountain Pass Hairpins", "Ice Cavern", "Frozen Lake", "Avalanche", "Icicle Crushers"]


# ===================================================================== 10. High Score: Arcade Cabinet (a neon maze of right angles)
def high_score(r, sk, rng):
    b = r.b
    M.cabinet(b, A(2600, -380, -1000), 600, 760, 300, sk)
    for k in range(6):
        M.coin(b, A(800 + k * 700, 200 + 60 * (k % 3), (-1) ** k * 900), 120)
        M.ghost(b, A(1200 + k * 650, 120, (-1) ** (k + 1) * 1000), 14, sk.NEON[k % 6])
    r.local("Coin Slot", J.tunnel_run, 0.5, rng, L=380, w=44, boosts=2)
    # the maze: tight right angles, ghosts patrolling the straights
    turns = [-90, 90, 90, -90, -90, 90]
    for k, t in enumerate(turns):
        r.straight("Maze %d" % (k + 1), 260 if k % 2 == 0 else 200, w1=44)
        if k % 2 == 0:
            r.along(EK.ob_door, [130])
        r.turn("Corner %d" % (k + 1), t, 70, rails=True)
    r.log("maze")
    r.local("Pinball Table", EK.a_bumper_field, 0.7, rng, W=200, L=420)
    r.log("pinball")
    r.local("Plunger Launch", J.launch_up, 0.7, rng, dy=200, D=260)
    tet = lambda b_, t, s_, rng_: (M.column(b_, "TetrisPillar", sub(t, (0, 8, 0)), t[1] - 200, 30, sk.NEON[int(t[0]) % 6]),
                                   sk.plat(b_, t, s_, rng_))
    tg = [r.ahead(190 * k, (60 if k % 2 else -60), 25 * k) for k in range(1, 6)]
    r.hops("Tetris Stack", tg, plat=tet, s=60, land=(210, 0, 60, 150))
    r.log("tetris")
    r.local("Neon Loop", SC.m_loop, 0.7, rng)
    r.turn("Joystick Bend", 90, 160, w1=46)
    r.spiral("Joystick Spiral", 1.0, -230, 130, side=1, w=46,
             core=lambda b_, c, R: b_.skin.helix_core(b_, c, c[1] - 230, c[1], R, 46, False))
    r.log("joy")
    r.local("Laser Grid", SC.m_gates, 0.8, rng)
    r.log("end")
    return ["Coin Slot", "Pac-Maze", "Pinball Table", "Plunger Launch", "Tetris Stack", "Neon Loop", "Joystick Spiral", "Laser Grid"]


TAU = math.pi * 2
FINAL = {1: [EK.ob_sweeper, EK.ob_bumpers], 2: [EK.ob_press, EK.ob_sweeper], 3: [EK.ob_swing, EK.ob_bumpers],
         4: [EK.ob_press, EK.ob_door], 5: [EK.ob_sweeper, EK.ob_press], 6: [EK.ob_bumpers, EK.ob_door],
         7: [EK.ob_gate, EK.ob_sweeper], 8: [EK.ob_press, EK.ob_gate], 9: [EK.ob_swing, EK.ob_sweeper],
         10: [EK.ob_gate, EK.ob_door]}
LEVELS = {1: sugar_rush, 2: drive_thru, 3: spore_springs, 4: checkmate, 5: tick_tock, 6: toy_box, 7: orbit,
          8: eruption, 9: frostbite, 10: high_score}
