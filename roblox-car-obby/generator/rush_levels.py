"""Ten non-stop levels, each its own shape, length and look. Beats from rush.py; landmarks from epic_marks.py."""
import math
from geom import add, sub, mul, UP
from builder import X0, Y0, ZC
import showcase as SC
import journey as J
import epic_kit as EK
import epic_marks as M
import route as RT
from rush import run, bend, kick, drops, isles, gauntlet, bomb, climb, aim

TAU = math.pi * 2


def A(u, h, v):
    return (X0 + u, Y0 + h, ZC + v)


def under(r, d=0.0):
    """A point d behind the turtle (for dressing what was just laid)."""
    return add(r.p, mul(r.f, -d))


# ===================================================================== 1. Sugar Rush: Sugar Avalanche
# Shot up onto a giant cake, then a downhill avalanche of candy jumps (a gentle S, always falling).
def sugar_rush(r, sk, rng):
    b = r.b
    run(r, "Start", 110, w=70)
    kick(r, "Cake Launch", 300, 330, rings=5, land=150, w=84)
    c = under(r, 90)
    M.cake(b, (c[0], 0, c[2]), [(150, c[1] - 260, c[1] - 140, (226, 170, 110), (255, 150, 190)),
                                 (110, c[1] - 140, c[1] - 60, (250, 236, 210), (255, 255, 255)),
                                 (70, c[1] - 60, c[1] - 8, (226, 170, 110), (120, 220, 200))], rng)
    aim(r, "Icing Bend", 1500, -380, R=120)
    kick(r, "Frosting Leap", 240, -50, rings=2, w=64)
    gauntlet(r, "Candy-Cane Sweepers", 230, [EK.ob_sweeper], every=80)
    kick(r, "Sprinkle Windmill", 270, -50, mill=True)
    aim(r, "Swirl Bend", 2900, 300, R=120)
    drops(r, "Wafer Steps", 3, step=40, cp=True)
    isles(r, "Gumdrop Hops", 4, D=170, dy=-15, s=56, side=34)
    kick(r, "Lollipop Leap", 280, -40, rings=3, cp=True)
    aim(r, "Caramel Bend", 4300, -150, R=120)
    r.local("Donut Loop", SC.m_loop, 0.6, rng)
    kick(r, "Cherry Drop", 240, -20)
    gauntlet(r, "Gumball Alley", 200, [EK.ob_bumpers], every=70)
    aim(r, "Last Bend", 5430, 0, R=120)
    kick(r, "Licorice Leap", 260, 20, rings=2)
    kick(r, "Sugar Rush Finale", 260, -10, rings=4)
    r.log("end")
    return ["Cake Launch", "Frosting Leap", "Candy-Cane Sweepers", "Sprinkle Windmill", "Wafer Steps", "Gumdrop Hops",
            "Lollipop Leap", "Donut Loop", "Cherry Drop", "Gumball Alley", "Licorice Leap", "Sugar Rush Finale"]


# ===================================================================== 2. Drive Thru: Kitchen Chaos
# Flat out across a kitchen in hard right angles: belts, presses, plate hops, a burger bounce, the frying-pan drops.
def drive_thru(r, sk, rng):
    b = r.b
    run(r, "Start", 80, w=60)
    kick(r, "Sink Jump", 240, 20, rings=2)
    r.local("Conveyor Grill", EK.a_belts_wide, 0.6, rng, W=110, n=4)
    bend(r, "Counter Corner", -90, 70, w=56, cp=True)
    gauntlet(r, "Patty Smashers", 300, [EK.ob_press], every=85)
    kick(r, "Ketchup Leap", 260, 10, rings=3)
    bend(r, "Tray Corner", 90, 70)
    plate = lambda b_, t, s_, rng_: (M.column(b_, "PlateStand", sub(t, (0, 14, 0)), t[1] - 140, 10, (220, 220, 230)),
                                     sk.burger(b_, t, s_, rng_))
    isles(r, "Burger Hops", 4, D=160, dy=12, s=60, side=40, plat=plate)
    r.local("Salt Shaker Rush", EK.a_frogger, 0.7, rng, W=170, lanes=3)
    bend(r, "Fryer Corner", 90, 70, cp=True)
    kick(r, "Bun Bounce", 200, 110, apex=170, rings=2)
    M.burger(b, (r.p[0] + 200, Y0 - 200, r.p[2]), 120, rng, k=1.2)
    gauntlet(r, "Spatula Flips", 220, [EK.ob_sweeper], every=75)
    drops(r, "Frying Pan Drops", 3, step=40, cp=True)
    bend(r, "Pantry Corner", -90, 70)
    r.local("Rolling Pin", SC.m_log, 0.7, rng)
    kick(r, "Milkshake Leap", 280, -20, rings=4, mill=True)
    r.local("Plate Spinners", SC.m_spin_bridges, 0.7, rng)
    aim(r, "Last Corner", 5310, 0, R=80)
    kick(r, "Order Up", 240, -40, rings=2)
    r.log("end")
    return ["Sink Jump", "Conveyor Grill", "Patty Smashers", "Ketchup Leap", "Burger Hops", "Salt Shaker Rush",
            "Bun Bounce", "Spatula Flips", "Frying Pan Drops", "Rolling Pin", "Milkshake Leap", "Plate Spinners"]


# ===================================================================== 3. Spore Springs: Bounce Forest
# Up and down all the way: big bounces up onto mushroom caps, dives down off them; an organic weave.
def spore_springs(r, sk, rng):
    b = r.b
    cap = lambda col: (lambda b_, t, w: M.giant_mushroom(b_, (t[0], t[1] - 300, t[2]), 290, 150, col, rng))
    run(r, "Start", 90, w=56)
    kick(r, "Spore Bounce", 200, 130, apex=210, rings=2, land_fn=cap((190, 40, 50)))
    kick(r, "Cap Dive", 260, -90)
    aim(r, "Root Bend", 1400, 330, R=120)
    kick(r, "Big Bounce", 210, 160, apex=240, rings=3, land_fn=cap((150, 60, 200)), cp=True)
    gauntlet(r, "Leaf Swings", 240, [EK.ob_swing], every=80)
    drops(r, "Toadstool Steps", 3, step=45)
    aim(r, "Fern Bend", 2900, -300, R=120)
    toad = lambda b_, t, s_, rng_: (M.column(b_, "Stalk", sub(t, (0, 10, 0)), t[1] - 220, 18, (236, 226, 200)),
                                    sk.toadstool(b_, t, s_, rng_))
    isles(r, "Toadstool Tops", 5, D=165, dy=20, s=58, side=36, plat=toad)
    kick(r, "Canopy Dive", 280, -120, rings=3, cp=True)
    r.local("Rolling Log", SC.m_log, 0.7, rng)
    aim(r, "Moss Bend", 4300, 300, R=120)
    kick(r, "Glow Bounce", 200, 140, apex=220, rings=2, land_fn=cap((60, 150, 200)))
    kick(r, "Firefly Leap", 260, -60, mill=True)
    aim(r, "Pond Bend", 5510, 0, R=120)
    bomb(r, "Vine Slide", 240, 80)
    kick(r, "Pond Jump", 240, -40, rings=3)
    r.log("end")
    return ["Spore Bounce", "Cap Dive", "Big Bounce", "Leaf Swings", "Toadstool Steps", "Toadstool Tops", "Canopy Dive",
            "Rolling Log", "Glow Bounce", "Firefly Leap", "Vine Slide", "Pond Jump"]


# ===================================================================== 4. Checkmate: Knight Moves
# Square blocks only: L-shaped knight hops between towers of different heights, rook sliders, a crumbling board.
def checkmate(r, sk, rng):
    b = r.b
    run(r, "Start", 90, w=60)
    sq = lambda b_, t, s_, rng_: (M.column(b_, "Tower", sub(t, (0, 6, 0)), t[1] - 260, 40, sk.WHITE if int(t[0]) % 2 else sk.BLACK),
                                  sk.plat(b_, t, s_, rng_))
    # knight's L hops: two ahead, one aside, each a step higher
    lft = RT.left_of(r.f)
    tg, q = [], r.p
    for k in range(5):
        q = add(q, add(mul(r.f, 150), add(mul(lft, 75 * (1 if k % 2 == 0 else -1)), (0, 22, 0))))
        tg.append(q)
    r.hops("Knight's Tour", tg, plat=sq, s=62, land=(200, -10, 60, 120))
    bc = add(tg[2], (0, 0, 0))
    M.board(b, (bc[0], 0, bc[2]), 8, 100, Y0 - 270)
    for kind, du, dv, col in (("king", 2.6, 2.8, sk.BLACK), ("queen", -2.8, 2.2, sk.WHITE), ("rook", 3.0, -3.0, sk.WHITE),
                              ("bishop", -1.6, -3.2, sk.BLACK), ("knight", 0.4, 3.4, sk.WHITE)):
        M.chess_piece(b, kind, (bc[0] + du * 100, Y0 - 270, bc[2] + dv * 100), 110, col)
    r.local("Rook Sliders", EK.a_frogger, 0.7, rng, W=190, lanes=3,
            block=lambda b_, rig, c, s_, i: M.chess_piece(b_, "rook", (c[0], c[1] - 4, c[2]), 28, sk.WHITE if i % 2 else sk.BLACK) and None)
    bend(r, "Square Corner", 90, 60, cp=True)
    kick(r, "Bishop Leap", 240, 40, rings=2)
    gauntlet(r, "Pawn Crushers", 260, [EK.ob_press], every=85)
    bend(r, "File Corner", -90, 60)
    r.local("Crumbling Board", EK.a_crumble_field, 0.7, rng, W=120, L=240)
    kick(r, "Queen's Gambit", 280, 60, rings=3, cp=True)
    lft = RT.left_of(r.f)
    tg, q = [], r.p
    for k in range(5):
        q = add(q, add(mul(r.f, 150), add(mul(lft, 75 * (1 if k % 2 else -1)), (0, -30, 0))))
        tg.append(q)
    r.hops("Knight Descent", tg, plat=sq, s=62, land=(200, -20, 60, 120))
    bend(r, "Rank Corner", -90, 60)
    drops(r, "Castling Steps", 3, step=40, L=110)
    r.local("King's Cross", SC.m_cross, 0.7, rng)
    aim(r, "Diagonal", 5200, 0, R=80)
    kick(r, "Checkmate Jump", 280, 60, rings=4, mill=True)
    r.log("end")
    return ["Knight's Tour", "Rook Sliders", "Bishop Leap", "Pawn Crushers", "Crumbling Board", "Queen's Gambit",
            "Knight Descent", "Castling Steps", "King's Cross", "Checkmate Jump"]


# ===================================================================== 5. Tick Tock: Clock Tower Drop
# Fired to the top of a clock tower, then down round it in a square spiral of jumps.
def tick_tock(r, sk, rng):
    b = r.b
    run(r, "Start", 90, w=60)
    gp = lambda b_, t, s_, rng_: sk.gear(b_, t, s_, rng_)
    isles(r, "Gear Hops", 3, D=170, dy=15, s=62, plat=gp)
    gauntlet(r, "Pendulum Run", 230, [EK.ob_swing], every=75)
    kick(r, "Mainspring Launch", 280, 260, apex=320, rings=5, land=120, w=72, cp=True)
    # a square spiral down round the clock tower (it stands inside the square, to the left)
    side = 700.0
    T = add(r.p, add(mul(RT.left_of(r.f), side / 2), mul(r.f, side / 2 - 120)))
    b.skin.helix_core(b, (T[0], Y0 - 400, T[2]), Y0 - 400, r.p[1] + 60, 110, 40, False)
    M.clock_face(b, (T[0], 0, T[2]), 130, r.p[1] + 90, sk, rng)
    r.solid("tower", T, 130, Y0 - 400, r.p[1] + 100)
    extra = [lambda: isles(r, "Cog Hops", 3, D=160, dy=-15, s=60, plat=gp),
             lambda: gauntlet(r, "Hammer Hall", 230, [EK.ob_press], every=75),
             lambda: drops(r, "Escapement Steps", 2, step=40),
             lambda: gauntlet(r, "Chime Swings", 230, [EK.ob_swing], every=75)]
    for k in range(4):
        kick(r, "Tower Jump %d" % (k + 1), 230, -45, rings=2, mill=(k == 2))
        extra[k]()
        bend(r, "Tower Corner %d" % (k + 1), 90, 60, cp=(k % 2 == 1))
    r.local("Cog Bridges", SC.m_spin_bridges, 0.7, rng)
    aim(r, "Out of the Tower", 4200, 0, R=90)
    kick(r, "Cuckoo Leap", 260, 0, rings=3)
    gauntlet(r, "Gear Teeth", 200, [EK.ob_press], every=70)
    aim(r, "Last Corner", 5500, 0, R=90)
    kick(r, "Midnight Jump", 260, 0, rings=4)
    r.log("end")
    return ["Gear Hops", "Pendulum Run", "Mainspring Launch", "Tower Jumps", "Cog Hops", "Hammer Hall", "Escapement Steps",
            "Chime Swings", "Cog Bridges", "Cuckoo Leap", "Gear Teeth", "Midnight Jump"]


# ===================================================================== 6. Toy Box: Stunt Track
# An orange stunt track: boost, kickers through rings, two loops, wall rides, a tube, a crossover.
def toy_box(r, sk, rng):
    b = r.b
    blk = lambda b_, t, s_, rng_: (M.column(b_, "BlockStack", sub(t, (0, 10, 0)), t[1] - 180, 30, sk.BRICKS[int(t[2]) % 6]),
                                   sk.plat(b_, t, s_, rng_))
    run(r, "Start", 120, w=56, boosts=[40])
    kick(r, "Ramp One", 250, 30, rings=4)
    r.local("Loop One", SC.m_loop, 0.6, rng)
    kick(r, "Ramp Two", 260, 0, rings=3)
    isles(r, "Block Hops", 4, D=160, dy=10, s=56, side=30, plat=blk)
    r.local("Wall Ride", SC.m_wallride, 0.6, rng)
    kick(r, "Ramp Three", 260, 20, rings=3)
    bend(r, "Banked Hairpin", 180, 150, dy=30, rails=True, cp=True)
    r.along(EK.ob_bumpers, [160, 320])
    r.local("Track Tube", SC.m_pipe, 0.7, rng)
    kick(r, "Gap Jump", 280, -30, rings=3)
    r.local("Domino Crushers", SC.m_crushers, 0.7, rng)
    bend(r, "Banked Hairpin Two", -180, 150, dy=-20, rails=True, cp=True)
    r.along(EK.ob_bumpers, [160, 320])
    r.local("Loop Two", SC.m_loop, 0.7, rng)
    kick(r, "Block Jump", 240, 40, rings=2)
    r.local("Wall Ride Two", SC.m_wallride, 0.7, rng)
    kick(r, "Mega Ramp", 300, -40, rings=5, mill=True)
    r.local("Spinning Tops", SC.m_turntable, 0.7, rng)
    aim(r, "Last Bend", 5330, 0, R=90)
    kick(r, "Finish Ramp", 280, -20, rings=5)
    M.teddy(b, add(r.p, (-300, -330, 380)), 260)
    for k, (du, dv) in enumerate(((600, 420), (1500, -420), (2600, 500), (3400, -500))):
        for j in range(3):
            M.toy_block(b, A(du + j * 20, -330 + j * 100, dv + j * 12), 100 - j * 10, sk.BRICKS[(k + j) % 6])
    M.spinning_top(b, A(2300, -260, -520), 180, sk.BRICKS)
    M.duck(b, A(4400, -330, 560), 200)
    r.log("end")
    return ["Ramp One", "Loop One", "Ramp Two", "Block Hops", "Wall Ride", "Banked Hairpin", "Track Tube", "Gap Jump",
            "Domino Crushers", "Loop Two", "Wall Ride Two", "Mega Ramp", "Spinning Tops", "Finish Ramp"]


# ===================================================================== 7. Orbit: Moon Jumps
# Few, huge, floaty leaps between planets and asteroids, through long rows of rings.
def orbit(r, sk, rng):
    b = r.b
    run(r, "Start", 120, w=70, boosts=[50])
    kick(r, "Liftoff", 420, 120, apex=260, rings=6, land=140, w=80)
    M.planet(b, add(r.p, (-60, -190, 0)), 150, (210, 120, 80), (240, 180, 120), rng, moons=2)
    aim(r, "Orbit Bend", 1400, -500, R=140)
    kick(r, "Mars Hop", 440, -20, apex=200, rings=6, land=140, cp=True)
    rock = lambda b_, t, s_, rng_: (M.asteroid(b_, sub(t, (0, s_ * 0.35, 0)), s_ * 0.9, rng_), sk.plat(b_, t, s_, rng_))
    aim(r, "Belt Bend", 2600, -600, R=140)
    isles(r, "Asteroid Field", 4, D=220, dy=10, s=60, side=50, plat=rock, land=(260, 0, 70, 130))
    aim(r, "Ring Bend", 3500, 200, R=140)
    kick(r, "Ring World", 460, 40, apex=220, rings=7, land=150, w=80, cp=True)
    M.planet(b, add(r.p, (-80, -230, 300)), 180, (90, 140, 220), (200, 230, 255), rng, ring=(300, 0.3, (220, 200, 255)))
    r.local("Zero-G Tube", SC.m_pipe, 0.7, rng)
    aim(r, "Gravity Bend", 4600, 0, R=140)
    kick(r, "Comet Leap", 440, -80, apex=180, rings=6, mill=True)
    r.local("Station Spin", EK.a_turntables, 0.7, rng, n=2, R=96)
    r.log("end")
    return ["Liftoff", "Mars Hop", "Asteroid Field", "Ring World", "Zero-G Tube", "Comet Leap", "Station Spin"]


# ===================================================================== 8. Eruption: Meltdown
# Down, down, down: drop after drop into the lava canyon, the floor crumbling, then a geyser blasts you out.
def eruption(r, sk, rng):
    b = r.b
    run(r, "Start", 90, w=60)
    drops(r, "Crater Steps", 4, step=40, cp=True)
    kick(r, "Ash Leap", 240, -40, rings=2)
    aim(r, "Lava Bend", 1700, 500, R=110)
    r.local("Crumbling Crust", EK.a_crumble_field, 0.7, rng, W=120, L=240)
    drops(r, "Basalt Steps", 3, step=45)
    stone = lambda b_, t, s_, rng_: (M.obsidian_spire(b_, (t[0], t[1] - 262, t[2]), 250, s_ * 0.7, sk, tip=False),
                                     sk.plat(b_, t, s_, rng_))
    aim(r, "Canyon Bend", 2900, -200, R=110)
    isles(r, "Obsidian Stones", 4, D=170, dy=-12, s=56, side=36, plat=stone)
    gauntlet(r, "Lava Jets", 240, [EK.ob_gate], every=60, cp=True)
    M.canyon(b, r.last[0], 60, 200, rng, sk, r.p[1] - 110)
    kick(r, "Geyser Blast", 220, 220, apex=290, rings=4, land=130)
    b.skin.launcher(b, r.p, 60)
    r.local("Lava Pistons", EK.a_piston_sea, 0.7, rng, W=120, L=200)
    aim(r, "Caldera Bend", 4400, 200, R=110)
    kick(r, "Magma Windmill", 270, 80, mill=True, cp=True)
    aim(r, "Last Bend", 5330, 0, R=110)
    kick(r, "Last Eruption", 260, 80, rings=3)
    r.log("end")
    return ["Crater Steps", "Ash Leap", "Crumbling Crust", "Basalt Steps", "Obsidian Stones", "Lava Jets", "Geyser Blast",
            "Lava Pistons", "Magma Windmill", "Last Eruption"]


# ===================================================================== 9. Frostbite: Avalanche Run
# Straight down a mountain: steep ski slopes broken by ski jumps, a slalom, an icy lake, an avalanche.
def frostbite(r, sk, rng):
    b = r.b
    run(r, "Start", 100, w=70)
    kick(r, "Chairlift Launch", 320, 330, apex=400, rings=5, land=140, w=80)
    M.mountain(b, add(r.p, (300, -760, -700)), 520, 880, rng, sk)
    for k in range(10):
        M.pine(b, add(r.p, (rng.uniform(200, 2600), -360 - rng.uniform(0, 300), rng.choice([-1, 1]) * rng.uniform(250, 500))),
               rng.uniform(140, 220), rng)
    bomb(r, "Black Run", 300, 90, w=70, rails=True)
    kick(r, "Ski Jump", 300, -70, rings=3, cp=True)
    gauntlet(r, "Slalom", 260, [EK.ob_gate], every=65)
    bomb(r, "Mogul Slope", 260, 80)
    kick(r, "Big Air", 320, -60, rings=4, mill=True)
    r.local("Frozen Lake", SC.m_rink, 0.7, rng)
    kick(r, "Icicle Leap", 260, 0, rings=2, cp=True)
    r.local("Avalanche", EK.a_frogger, 0.7, rng, W=180, lanes=3)
    aim(r, "Last Bend", 5330, 0, R=120)
    kick(r, "Last Ski Jump", 300, -30, rings=4)
    r.log("end")
    return ["Chairlift Launch", "Black Run", "Ski Jump", "Slalom", "Mogul Slope", "Big Air", "Frozen Lake",
            "Icicle Leap", "Avalanche", "Last Ski Jump"]


# ===================================================================== 10. High Score: Rhythm Rush
# Rapid-fire short hops on a narrow neon track in a square wave, laser gates in between: hop, hop, hop.
def high_score(r, sk, rng):
    b = r.b
    M.cabinet(b, A(2700, -400, -900), 560, 720, 280, sk)
    for k in range(7):
        M.coin(b, A(600 + k * 700, 140 + 50 * (k % 3), (-1) ** k * 700), 110)
        M.ghost(b, A(900 + k * 640, 80, (-1) ** (k + 1) * 820), 13, sk.NEON[k % 6])
    run(r, "Start", 80, w=40)
    for k in range(4):
        kick(r, "Beat %d" % (k + 1), 150, 15 if k % 2 == 0 else -15, land=70, w=40, apex=40)
    bend(r, "Square Wave 1", 90, 50, w=40, cp=True)
    gauntlet(r, "Laser Rhythm", 200, [EK.ob_gate], every=50)
    bend(r, "Square Wave 2", -90, 50)
    for k in range(4):
        kick(r, "Combo %d" % (k + 1), 160, 20 if k % 2 == 0 else -10, land=70, apex=45, rings=1)
    bend(r, "Square Wave 3", -90, 50, cp=True)
    pix = lambda b_, t, s_, rng_: (M.column(b_, "PixelPillar", sub(t, (0, 8, 0)), t[1] - 200, 26, sk.NEON[int(t[0]) % 6]),
                                   sk.plat(b_, t, s_, rng_))
    isles(r, "Pixel Hops", 5, D=140, dy=12, s=44, side=24, plat=pix, land=(170, 0, 40, 100))
    bend(r, "Square Wave 4", 90, 50)
    r.local("Pinball Bumpers", EK.a_bumper_field, 0.8, rng, W=150, L=240)
    kick(r, "Power Up", 220, 80, rings=3, cp=True)
    for k in range(4):
        kick(r, "Bonus %d" % (k + 1), 150, -20, land=70, apex=45)
    r.local("Neon Loop", SC.m_loop, 0.8, rng)
    aim(r, "Last Wave", 5330, 0, R=60)
    kick(r, "High Score", 260, -40, rings=5, mill=True)
    r.log("end")
    return ["Beats", "Laser Rhythm", "Combos", "Pixel Hops", "Pinball Bumpers", "Power Up", "Bonus Hops", "Neon Loop",
            "High Score"]


LEVELS = {1: sugar_rush, 2: drive_thru, 3: spore_springs, 4: checkmate, 5: tick_tock, 6: toy_box, 7: orbit,
          8: eruption, 9: frostbite, 10: high_score}
FINAL = {1: [EK.ob_sweeper, EK.ob_bumpers], 2: [EK.ob_press, EK.ob_sweeper], 3: [EK.ob_swing, EK.ob_bumpers],
         4: [EK.ob_press, EK.ob_door], 5: [EK.ob_swing, EK.ob_press], 6: [EK.ob_bumpers, EK.ob_door],
         7: [EK.ob_gate, EK.ob_sweeper], 8: [EK.ob_gate, EK.ob_press], 9: [EK.ob_gate, EK.ob_sweeper],
         10: [EK.ob_gate, EK.ob_door]}
