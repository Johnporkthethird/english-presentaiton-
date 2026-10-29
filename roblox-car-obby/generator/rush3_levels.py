"""Levels 1-10, version 4: obby courses. Short floating platforms (wide, narrow, up, down, left, right), a jump
between nearly every one, a trap or machine on nearly every one, boost decks holding the speed; each level keeps its
own main idea as its centrepiece. Pieces: obby.py (platforms, links, traps), rush2.py (the big set pieces)."""
import math
from geom import CF, add, sub, mul, unit, UP
from builder import X0, Y0, ZC
import epic_marks as M
import route as RT
import rush2 as R2
import obby as O
from obby import Obby, saw, pusher, zap_floor, axe, flames, mine, claw, crusher, sweeper, bumpers, lasers
import skins
from rush2_levels import shroom_cap, run, A

TAU = math.pi * 2


def slick(b, c, w, i):
    R2.grease(b, c, (1, 0, 0), 44, w)


def ice(b, c, w, i):
    R2.ice_patch(b, c, (1, 0, 0), 60, w)


def course(o, steps):
    """steps: ("p", label, L, w, traps, cp) platforms and ("drop", h, side) / ("kick", dy, side) / ("pad", dy, side)
    links, or callables (a set piece laid at the turtle)."""
    linked = False
    for s in steps:
        if callable(s):
            if linked:
                o.plat("Landing", 0, o.r.w)  # (a set piece starts on solid ground: land first)
            linked = False
            s()
        elif s[0] == "p":
            label, L, w = s[1], s[2], s[3]
            traps = s[4] if len(s) > 4 else ()
            cp = s[5] if len(s) > 5 else False
            o.plat(label, L, w, [(t[0], t[1]) + ((t[2],) if len(t) > 2 else ()) for t in traps], cp=cp)
            linked = False
        else:
            linked = True
        if callable(s) or s[0] == "p":
            continue
        if s[0] == "drop":
            o.drop(s[1], side=s[2] if len(s) > 2 else 0.0)
        elif s[0] == "kick":
            o.kick(s[1], side=s[2] if len(s) > 2 else 0.0)
        elif s[0] == "pad":
            o.pad(s[1], side=s[2] if len(s) > 2 else 0.0)


# ===================================================================== 1. Sugar Rush
def sugar_rush(r, sk, rng):
    b = r.b
    o = Obby(r, 230)
    run(r, "Start", 90, w=64)
    pal = [(255, 120, 170), (120, 220, 200), (255, 210, 90), (170, 140, 255), (255, 150, 90)]
    course(o, [
        ("p", "Lolly Pad", 150, 60, [], True), ("drop", 40, 45),
        ("p", "Gumdrop Deck", 150, 48, [(sweeper, 0.5)]), ("kick", 40, -50),
        ("p", "Wafer Bridge", 140, 36, [(mine, 0.5)]), ("drop", 30),
        ("p", "Licorice Beam", 190, 18), ("pad", 90, 45),
        ("p", "Cupcake Top", 150, 60, [(crusher, 0.5)], True), ("kick", 0, -45),
        ("p", "Chocolate Bar", 160, 44, [(saw, 0.5)]), ("drop", 50, 55),
        ("p", "Jelly Strip", 150, 30, [(mine, 0.4)]), ("kick", 30),
        ("p", "Candy Press", 170, 56, [(crusher, 0.35), (crusher, 0.7)], True),
    ])
    R2.strips(r, "Sugar Rush Sprint", 300, w=64)
    R2.ramp_jump(r, "Mega Ramp", deg=24, drop=100, w_land=80, slope=10, land_min=220,
                 gap_fn=lambda b_, lip, a0, f, w: M.choc_river(b_, lip[0] - 200, a0[0] + 400, lip[2] - 160, lip[2] + 160, Y0 - 330))
    course(o, [
        ("kick", 20, 50),
        ("p", "Caramel Ledge", 150, 40, [(saw, 0.5)], True), ("drop", 40, -50),
        ("p", "Sour Strip", 150, 22, [(sweeper, 0.5)]), ("pad", 70),
        ("p", "Sprinkle Top", 160, 60, [(mine, 0.3), (crusher, 0.7)]),
    ])
    R2.dress(r, [(lambda b_, c, g: M.lollipop(b_, c, g.uniform(260, 380), g.uniform(110, 160), g.choice(pal), g), 80, 420),
                 (lambda b_, c, g: M.candy_cane(b_, c, g.uniform(280, 380), 26, yaw=g.random() * 6), 50, 400),
                 (lambda b_, c, g: M.big_cupcake(b_, c, g.uniform(240, 320), g.choice(pal), g), 120, 320)], 18, rng)
    r.log("end")
    return ["Lolly Pad", "Gumdrop Deck", "Licorice Beam", "Cupcake Top", "Chocolate Bar", "Candy Press", "Mega Ramp",
            "Sour Strip"]


# ===================================================================== 2. Drive Thru
def drive_thru(r, sk, rng):
    b = r.b
    o = Obby(r, 230)
    run(r, "Start", 90, w=60)
    course(o, [
        ("p", "Order Counter", 140, 56, [], True),
        lambda: R2.belt_road(r, "Turbo Belt", 200, 100, "along", w=50),
        ("p", "Hot Plate", 110, 50, [(flames, 0.5)]), ("drop", 40, 50),
        ("p", "Grill Deck", 160, 56, [(crusher, 0.3), (crusher, 0.7)]), ("kick", 30, -40),
        ("p", "Tray", 120, 40, [(slick, 0.5)], True),
        lambda: R2.belt_road(r, "Sideways Belt", 160, 60, "right", w=36),
        ("p", "Bun Bridge", 110, 30, [(pusher, 0.5)]), ("drop", 40, -50),
        ("p", "Fryer", 140, 48, [(flames, 0.35), (flames, 0.7)]), ("pad", 80, 40),
        ("p", "Shake Lid", 130, 40, [(sweeper, 0.5)], True),
        lambda: R2.belt_road(r, "Backwards Belt", 200, 90, "back", w=44),
        ("p", "Spatula", 140, 24, [(pusher, 0.5)]), ("drop", 50, 50),
        ("p", "Dish Pit", 150, 52, [(slick, 0.3), (crusher, 0.7)], True), ("kick", 20, -40),
        ("p", "Pickup Window", 160, 44, [(flames, 0.5)]), ("drop", 30),
        lambda: R2.belt_road(r, "Express Belt", 220, 120, "along", w=48),
        ("p", "Bag It", 110, 56),
    ])
    R2.dress(r, [(lambda b_, c, g: M.burger(b_, add(c, (0, 120, 0)), 120, g, k=1.3), 170, 360),
                 (lambda b_, c, g: M.milkshake(b_, c, 110, 380, g), 120, 520),
                 (lambda b_, c, g: M.fry_box(b_, c, 150, 280, g), 110, 420),
                 (lambda b_, c, g: M.ketchup(b_, c, 60, 320), 70, 380)], 14, rng)
    r.log("end")
    return ["Turbo Belt", "Grill Deck", "Sideways Belt", "Fryer", "Backwards Belt", "Spatula", "Dish Pit", "Express Belt"]


# ===================================================================== 3. Spore Springs
def spore_springs(r, sk, rng):
    b = r.b
    floor_y = Y0 - 330
    cap = shroom_cap([(200, 40, 50), (150, 70, 210), (60, 160, 210), (230, 120, 40)], floor_y)
    o = Obby(r, 260)
    run(r, "Start", 90, w=60)
    course(o, [
        ("p", "Moss Ledge", 150, 56, [], True),
        lambda: R2.bounce_chain(r, "Cap Chain", [(300, 30, 0), (300, 40, 60), (300, -20, -60)], 260, s=120, cap=cap,
                                land_L=60, w_out=50),
        ("p", "Root Bridge", 150, 26, [(sweeper, 0.5)], True), ("drop", 40, 50),
        ("p", "Bark Ledge", 140, 44, [(mine, 0.5)]), ("kick", 30, -50),
        ("p", "Fern Beam", 170, 18), ("drop", 30),
        ("p", "Spore Vent", 150, 50, [(flames, 0.5)], True),
        lambda: R2.bounce_chain(r, "Toadstool Tumble", [(290, -40, 50), (290, -40, -60), (300, 20, 40)], 260, s=110,
                                cap=cap, land_L=60, w_out=50),
        ("p", "Log Run", 160, 40, [(axe, 0.5)], True), ("kick", 40, 50),
        ("p", "Canopy", 150, 30, [(saw, 0.5)]), ("drop", 40, -40),
        lambda: R2.bounce_chain(r, "Firefly Hops", [(300, 40, -40), (300, -30, 40)], 260, s=120, cap=cap, land_L=60,
                                w_out=50),
        ("p", "Glow Pond", 140, 56, [(sweeper, 0.5)], True),
    ])
    R2.dress(r, [(lambda b_, c, g: M.giant_mushroom(b_, c, g.uniform(200, 360), g.uniform(120, 200),
                                                     g.choice([(200, 40, 50), (150, 70, 210), (60, 160, 210)]), g), 110, 420),
                 (lambda b_, c, g: M.great_tree(b_, c, 60, c[1], c[1] + g.uniform(380, 520), g, sk), 300, 760)], 16, rng,
            ground=floor_y)
    r.log("end")
    return ["Cap Chain", "Root Bridge", "Fern Beam", "Toadstool Tumble", "Log Run", "Canopy", "Firefly Hops"]


# ===================================================================== 4. Checkmate
def checkmate(r, sk, rng):
    b = r.b

    def tower(b_, top, s, rng_):
        M.column(b_, "Tower", sub(top, (0, 6, 0)), Y0 - 420, s * 0.9, sk.WHITE if int(top[0] // 7) % 2 else sk.BLACK)
        sk.island(b_, top, s, rng_)
        skins.floor(b_, top, s * 0.9)

    rook = lambda b_, rig, c, k: M.chess_piece(b_, "rook", c, 30, sk.WHITE if k % 2 else sk.BLACK, parent=rig)
    o = Obby(r, 200)
    run(r, "Start", 90, w=64)
    course(o, [
        ("p", "Pawn Rank", 140, 60, [], True),
        lambda: R2.bounce_chain(r, "Knight's Tour", [(230, 30, 100), (230, 30, -100), (230, 20, 90)], 200, s=96,
                                cap=tower, land_L=60, w_out=56, shroom=False),
        ("p", "Bishop Diagonal", 150, 40, [(crusher, 0.5)], True), ("drop", 40, 40),
        ("p", "Rook File", 140, 24, [(pusher, 0.5)]), ("kick", 0, -40),
        lambda: R2.sink_board(r, "Falling Board", 320, 120, sliders=(100, 220), slider_fn=rook),
        ("p", "Castle Gate", 120, 56, [(crusher, 0.5)], True), ("drop", 40, -50),
        ("p", "Queen's Line", 160, 30, [(saw, 0.5)]), ("pad", 90, 40),
        lambda: R2.bounce_chain(r, "Knight Descent", [(230, -40, -100), (230, -40, 100), (230, -20, -80)], 200, s=96,
                                cap=tower, land_L=60, w_out=56, shroom=False),
        ("p", "Endgame", 140, 44, [(axe, 0.5)], True),
        lambda: R2.sink_board(r, "Collapsing Board", 400, 64, delay=0.12, rate=120),
        ("p", "Checkmate", 120, 60, [(crusher, 0.5)]),
    ])
    bc = A(2600, -420, -400)
    M.board(b, (bc[0], 0, bc[2]), 10, 220, Y0 - 420)
    for kind, du, dv, col in (("king", 3.6, 2.8, sk.BLACK), ("queen", -3.8, 2.2, sk.WHITE), ("bishop", 3.0, -3.6, sk.WHITE),
                              ("knight", -2.6, -3.2, sk.BLACK), ("pawn", 1.4, 3.6, sk.WHITE), ("pawn", -1.0, -3.8, sk.BLACK)):
        M.chess_piece(b, kind, (bc[0] + du * 220, Y0 - 420, bc[2] + dv * 220), 260, col)
    R2.dress(r, [(lambda b_, c, g: M.castle(b_, c, 260, 200, 260, g), 190, 380)], 6, rng, ground=Y0 - 420)
    r.log("end")
    return ["Knight's Tour", "Rook File", "Falling Board", "Queen's Line", "Knight Descent", "Collapsing Board"]


# ===================================================================== 5. Tick Tock
def tick_tock(r, sk, rng):
    b = r.b
    brass, dark = sk.BRASS, sk.DARK
    o = Obby(r, 220)
    run(r, "Start", 90, w=64)
    course(o, [
        ("p", "Mainspring", 140, 56, [], True), ("kick", 20, 40),
        ("p", "Ratchet", 140, 40, [(crusher, 0.5)]),
        lambda: R2.gear_bridge(r, "Great Wheel", 100, 5.0, col=brass),
        ("p", "Arbor", 120, 30, [(axe, 0.5)], True), ("drop", 40, -40),
        ("p", "Escapement", 140, 44, [(saw, 0.5)]),
        lambda: R2.turnstile(r, "Hour Hand", 160, w=40, period=1.8, phase=0.0, col=dark),
        ("p", "Dial Rim", 130, 24, [(pusher, 0.5)], True), ("pad", 90, 40),
        ("p", "Bell Deck", 140, 56, [(crusher, 0.35), (crusher, 0.7)]),
        lambda: R2.pendulum_ferry(r, "Pendulum Ferry", Lp=240, amp_deg=28, period=5.0, col=brass),
        ("p", "Weight Shelf", 120, 44, [(axe, 0.5)], True), ("kick", 0, -50),
        lambda: R2.gear_bridge(r, "Crown Wheel", 90, -7.0, col=(150, 120, 70)),
        ("p", "Cog Beam", 160, 18), ("drop", 40, 40),
        lambda: R2.turnstile(r, "Minute Hand", 160, w=40, period=1.6, phase=0.3, col=dark),
        ("p", "Chime Ledge", 140, 50, [(saw, 0.5)], True), ("kick", 20),
        ("p", "Midnight", 120, 56),
    ])
    C = add(r.p, mul(RT.left_of(r.f), 900))
    M.clock_tower(b, (C[0], Y0 - 420, C[2]), 220, Y0 + 300, sk, rng)
    R2.dress(r, [(lambda b_, c, g: M.gear(b_, add(c, (0, 330, 0)), g.uniform(110, 170), g.choice([(1, 0, 0), (0, 0, 1)]),
                                          g.choice([brass, (150, 120, 70), (190, 112, 64)]), spin=g.choice([-0.06, 0.05, 0.08])),
                  180, 520)], 10, rng)
    r.log("end")
    return ["Great Wheel", "Arbor", "Hour Hand", "Pendulum Ferry", "Crown Wheel", "Cog Beam", "Minute Hand"]


# ===================================================================== 6. Toy Box: the Kicker Chain
def toy_box(r, sk, rng):
    b = r.b
    o = Obby(r, 240)
    run(r, "Start", 90, w=60)
    course(o, [
        ("p", "Toy Shelf", 140, 56, [], True), ("kick", 30, 50),
        ("p", "Block A", 120, 40), ("kick", 20, -60),
        ("p", "Block B", 120, 36, [(sweeper, 0.5)]), ("kick", -20, 60),
        ("p", "Block C", 130, 40, [(crusher, 0.5)], True), ("drop", 40),
        ("p", "Domino Line", 180, 24, [(pusher, 0.3), (pusher, 0.7)]), ("pad", 100, -40),
        ("p", "Train Top", 140, 30, [(saw, 0.5)], True), ("kick", 0, 50),
        ("p", "Race Ramp", 120, 44), ("kick", 30, -50),
        ("p", "Jack Box", 140, 50, [(mine, 0.5)]), ("kick", -30, 40),
        ("p", "Crayon Beam", 170, 16, [], True), ("drop", 40, -40),
        ("p", "Robot Arms", 150, 50, [(axe, 0.35), (axe, 0.7)]), ("kick", 20, 50),
        ("p", "Marble Run", 140, 36, [(bumpers, 0.5)], True), ("kick", -20),
        ("p", "Toy Chest", 140, 60),
    ])
    R2.dress(r, [(lambda b_, c, g: [M.toy_block(b_, (c[0] + j * 20, c[1] + j * 100, c[2] + j * 12), 100 - j * 10,
                                                 sk.BRICKS[(j + int(c[0])) % 6], yaw=0.3 * j) for j in range(3)], 90, 300),
                 (lambda b_, c, g: M.teddy(b_, c, 300, yaw=g.random() * 6), 170, 560),
                 (lambda b_, c, g: M.duck(b_, c, 240, yaw=g.random() * 6), 150, 300),
                 (lambda b_, c, g: M.spinning_top(b_, c, 200, sk.BRICKS), 110, 260)], 14, rng)
    r.log("end")
    return ["Kicker Chain", "Domino Line", "Train Top", "Jack Box", "Crayon Beam", "Robot Arms", "Marble Run"]


# ===================================================================== 7. Orbit
def orbit(r, sk, rng):
    b = r.b
    o = Obby(r, 240)
    run(r, "Start", 90, w=70)
    rock = lambda b_, c, w, i: M.asteroid(b_, add(c, (0, 14, (w / 2 - 14) * (1 if i % 2 else -1))), 20, b_.rng)
    course(o, [
        ("p", "Launch Pad", 140, 60, [], True), ("pad", 120, 50),
        ("p", "Moon Rock", 140, 40, [(zap_floor, 0.5)]), ("kick", 0, -50),
        ("p", "Satellite", 130, 30, [(saw, 0.5)], True),
        lambda: R2.tractor_beam(r, "Tractor Beam", 520, dy=40, w_land=50, land_L=60),
        ("p", "Beam Dock", 140, 50, [(lasers, 0.5)], True), ("drop", 40, 50),
        ("p", "Asteroid Belt", 180, 80, [(rock, 0.3), (rock, 0.6)]), ("kick", 30, -60),
        ("p", "Solar Panel", 160, 20), ("drop", 40),
        ("p", "Airlock", 140, 50, [(zap_floor, 0.35), (zap_floor, 0.7)], True),
        lambda: R2.tractor_beam(r, "Wormhole Beam", 560, dy=-40, turn=30, w_land=50, land_L=60),
        ("p", "Wormhole Exit", 140, 44, [(pusher, 0.5)], True), ("pad", 80, -40),
        ("p", "Ring Shard", 150, 26, [(saw, 0.5)]), ("drop", 60, 40),
        ("p", "Docking Bay", 140, 60),
    ])
    R2.dress(r, [(lambda b_, c, g: M.planet(b_, add(c, (0, 200, 0)), g.uniform(90, 160),
                                            g.choice([(210, 120, 80), (90, 200, 160), (200, 90, 160), (230, 200, 110)]),
                                            (240, 230, 220), g, moons=g.choice([0, 1, 2])), 190, 380),
                 (lambda b_, c, g: M.asteroid(b_, add(c, (0, g.uniform(180, 330), 0)), g.uniform(40, 80), g), 60, 380)],
            16, rng)
    r.log("end")
    return ["Launch Pad", "Moon Rock", "Tractor Beam", "Asteroid Belt", "Solar Panel", "Wormhole Beam", "Ring Shard"]


# ===================================================================== 8. Eruption
def eruption(r, sk, rng):
    b = r.b
    o = Obby(r, 230)
    run(r, "Start", 90, w=64)
    course(o, [
        ("p", "Crater Rim", 140, 56, [], True), ("drop", 50, 40),
        ("p", "Ash Ledge", 140, 40, [(flames, 0.5)]), ("drop", 50, -50),
        ("p", "Basalt Step", 130, 30, [(crusher, 0.5)]), ("drop", 50, 40),
        ("p", "Magma Vent", 150, 50, [(flames, 0.3), (flames, 0.7)], True),
        lambda: R2.lava_surge(r, "Lava Causeway", 220, w=40, period=3.2, phase=0.0),
        ("p", "Obsidian Beam", 170, 18), ("kick", 0, -40),
        ("p", "Cinder Deck", 140, 50, [(saw, 0.5)], True),
        lambda: R2.lava_surge(r, "Second Causeway", 220, w=36, period=3.0, phase=0.5),
        ("p", "Geyser", 120, 56, [], True), ("pad", 160, 40),
        ("p", "Rim Again", 140, 40, [(axe, 0.5)]), ("kick", -30, -50),
        ("p", "Smoke Stack", 140, 26, [(flames, 0.5)], True), ("drop", 40, 40),
        ("p", "Last Vent", 140, 56, [(crusher, 0.5)]),
    ])
    R2.dress(r, [(lambda b_, c, g: M.obsidian_spire(b_, c, g.uniform(260, 420), g.uniform(50, 90), sk), 70, 420)], 16, rng)
    r.log("end")
    return ["Crater Rim", "Basalt Step", "Magma Vent", "Lava Causeway", "Obsidian Beam", "Geyser", "Smoke Stack"]


# ===================================================================== 9. Frostbite
def frostbite(r, sk, rng):
    b = r.b
    import rush
    o = Obby(r, 230)
    run(r, "Start", 90, w=70)
    rush.booster(r, "Chairlift", 300, 300, w=70)
    course(o, [
        ("p", "Summit", 140, 60, [], True), ("drop", 40, 50),
        ("p", "Black Ice", 160, 44, [(ice, 0.5)]), ("kick", -30, -50),
        ("p", "Ski Jump", 140, 36, [(sweeper, 0.5)], True), ("drop", 50),
        ("p", "Mogul Beam", 170, 18), ("drop", 40, 40),
        ("p", "Avalanche", 200, 56, [], True),
        lambda: R2.rollers(r, [70, 140], d=26, period=2.2),
        ("kick", -20, -50),
        ("p", "Ice Cave", 150, 40, [(axe, 0.5)]), ("drop", 40, 40),
        ("p", "Frozen Lake", 170, 60, [(ice, 0.35), (mine, 0.75)], True), ("kick", -30, -40),
        ("p", "Glacier Edge", 150, 24, [(pusher, 0.5)]), ("drop", 40),
        ("p", "Ski Lodge", 140, 56),
    ])
    R2.dress(r, [(lambda b_, c, g: M.mountain(b_, c, g.uniform(380, 520), g.uniform(700, 900), g, sk), 520, 900)], 2, rng,
            near=700, far=1100, ground=Y0 - 700)
    R2.dress(r, [(lambda b_, c, g: M.pine(b_, c, g.uniform(150, 240), g), 40, 240)], 30, rng, near=120, far=500)
    r.log("end")
    return ["Chairlift", "Black Ice", "Ski Jump", "Mogul Beam", "Avalanche", "Ice Cave", "Frozen Lake", "Glacier Edge"]


# ===================================================================== 10. High Score
def high_score(r, sk, rng):
    b = r.b
    V = 260.0
    o = Obby(r, V)
    run(r, "Start", 90, w=50)

    def beat_plat(label, L, w, at, period=1.2, on=0.45, cp=False):
        o.plat(label, L, w, cp=cp)
        R2.beat_gates(r, at, V, period=period, on=on)

    course(o, [
        lambda: beat_plat("Level 1", 260, 40, [80, 150, 220], cp=True), ("kick", 20, 50),
        ("p", "Claw Machine", 140, 44, [(claw, 0.5)]), ("drop", 40, -50),
        ("p", "Pinball", 150, 60, [(bumpers, 0.35), (bumpers, 0.7)], True), ("kick", 30, 40),
        ("p", "Pixel Beam", 170, 16), ("drop", 40),
        lambda: beat_plat("Level 2", 240, 36, [70, 130, 190], period=1.0, on=0.4, cp=True), ("pad", 90, -40),
        ("p", "Ghost House", 180, 56, [], False),
        lambda: R2.rollers(r, [60, 120], d=24, period=2.0, col=sk.NEON[1]),
        ("kick", 0, 50),
        ("p", "Zap Grid", 150, 40, [(zap_floor, 0.35), (zap_floor, 0.7)], True), ("drop", 40, -40),
        ("p", "Claw Row", 160, 44, [(claw, 0.35), (claw, 0.7)]), ("kick", 20),
        lambda: beat_plat("Bonus Round", 220, 32, [60, 110, 160], period=0.9, on=0.36, cp=True),
    ])
    R2.dress(r, [(lambda b_, c, g: M.cabinet(b_, c, 400, 600, 200, sk, yaw=g.random() * 6), 260, 620),
                 (lambda b_, c, g: M.coin(b_, add(c, (0, g.uniform(200, 380), 0)), 110), 60, 440),
                 (lambda b_, c, g: M.ghost(b_, add(c, (0, g.uniform(160, 320), 0)), 13, g.choice(sk.NEON)), 90, 420)],
            14, rng)
    r.log("end")
    return ["Beat Gates", "Claw Machine", "Pinball", "Pixel Beam", "Ghost House", "Zap Grid", "Claw Row", "Bonus Round"]


LEVELS = {1: sugar_rush, 2: drive_thru, 3: spore_springs, 4: checkmate, 5: tick_tock, 6: toy_box, 7: orbit, 8: eruption,
          9: frostbite, 10: high_score}
FINAL = {}
