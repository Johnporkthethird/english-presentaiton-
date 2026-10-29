"""Levels 1-10, version 5: tours of set pieces. Every stretch is a different place you jump onto: a laser box, a ring
of fire, stars in the sky, islands in the sea, boats, city rooftops, warp pipes, clouds, giant piano keys, a
hexagon mega ramp, a rocky downhill... joined by drops, kickers and up pads. Pieces: stages.py, obby.py, rush2.py."""
import math
from geom import CF, add, sub, mul, unit, UP
from builder import X0, Y0, ZC
import epic_marks as M
import route as RT
import rush2 as R2
import obby as O
import stages as S
from obby import Obby
from rush2_levels import shroom_cap, run, A

TAU = math.pi * 2


class Tour:
    """Lays a list of steps: stages (tuples naming a set piece) and links between them."""

    def __init__(self, r, B, rng, water=None):
        self.r, self.b, self.rng = r, r.b, rng
        self.o = Obby(r, B)
        self.seas = []      # (points of the stretch, water height) to put the sea under
        self.k = 0
        self.island_look = {}
        self.hill_look = {}

    def go(self, steps):
        o, r, rng = self.o, self.r, self.rng
        for st in steps:
            if callable(st):
                if o.need:
                    S.surface(o, "Landing", 0, r.w or 50, look=S.look_glass_floor())
                st()
                continue
            kind = st[0]
            self.k += 1
            n = "%s %d" % (kind.title(), self.k)
            if kind == "drop":
                o.drop(st[1], side=st[2] if len(st) > 2 else 0.0)
            elif kind == "kick":
                o.kick(st[1], side=st[2] if len(st) > 2 else 0.0)
            elif kind == "pad":
                o.pad(st[1], side=st[2] if len(st) > 2 else 0.0)
            elif kind == "fire":
                S.fire_ring_kick(o, st[1], side=st[2] if len(st) > 2 else 0.0)
            elif kind == "deck":
                S.surface(o, st[1], st[2], st[3], look=S.look_glass_floor(*st[4:5]), cp=True)
            elif kind == "box":
                S.laser_box(o, st[1], L=st[2], W=st[3])
            elif kind == "star":
                S.star_stage(o, st[1], R=st[2], col=st[3] if len(st) > 3 else (255, 215, 70), cp=st[4] if len(st) > 4 else False)
            elif kind == "roof":
                S.surface(o, st[1], st[2], st[3], look=S.look_roof(rng, st[4] if len(st) > 4 else Y0 - 520,
                                                                     body=rng.choice([(120, 130, 150), (170, 150, 130),
                                                                                      (90, 100, 120), (200, 190, 170)])),
                          cp=st[5] if len(st) > 5 else False)
            elif kind == "island":
                pts = S.surface(o, st[1], st[2], st[3], look=S.look_island(rng, st[4], **self.island_look),
                                cp=st[5] if len(st) > 5 else False)
                self.seas.append((pts, st[4]))
            elif kind == "boat":
                pts = S.boat(o, st[1], L=st[2], w=st[3], rng=rng, cp=st[5] if len(st) > 5 else False,
                             hull=rng.choice([(170, 60, 50), (40, 80, 150), (230, 230, 220), (60, 130, 90)]))
                self.seas.append((pts, st[4]))
            elif kind == "cloud":
                S.surface(o, st[1], st[2], st[3], look=S.look_cloud(rng), cp=st[4] if len(st) > 4 else False)
            elif kind == "pipe":
                S.surface(o, st[1], st[2], st[3], look=S.look_pipe(ground=st[4] if len(st) > 4 else None),
                          cp=st[5] if len(st) > 5 else False)
            elif kind == "piano":
                S.piano(o, st[1], L=st[2], w=st[3])
            elif kind == "hex":
                S.hex_ramp(o, st[1], roll=st[2], drop=st[3], deg=st[4], land_drop=st[5])
            elif kind == "down":
                S.downhill(o, st[1], st[2], st[3], w=st[4], rocks=st[5] if len(st) > 5 else 4, rng=rng, **self.hill_look)
        return self

    def sea(self, col=(40, 120, 200), pad=260.0, kind="Fall"):
        """One sea under every island and boat stretch (they share a height)."""
        b = self.b
        groups = {}
        for pts, y in self.seas:
            groups.setdefault(round(y, 1), []).extend(pts)
        for y, pts in groups.items():
            xs = [p[0] for p in pts]
            zs = [p[2] for p in pts]
            x0, x1 = max(min(xs) - pad, X0 + 2), min(max(xs) + pad, b.X1 - 2)
            z0, z1 = min(zs) - pad, max(zs) + pad
            S.water(b, ((x0 + x1) / 2, 0, (z0 + z1) / 2), x1 - x0, z1 - z0, y, col, kind)


# ===================================================================== 1. Stunt Show
def stunt_show(r, sk, rng):
    sk.title = "Stunt Show"
    b = r.b
    t = Tour(r, 230, rng)
    run(r, "Start", 90, w=64)
    t.go([
        ("deck", "Launch Deck", 170, 60),
        ("drop", 50),
        ("box", "Laser Box", 280, 110),
        ("fire", 0, 40),
        ("deck", "Fire Landing", 150, 56),
        ("pad", 120, -40),
        ("star", "Gold Star", 95, (255, 215, 70), True), ("drop", 40, 60),
        ("star", "Pink Star", 95, (255, 120, 190)), ("drop", 40, -60),
        ("star", "Blue Star", 95, (110, 180, 255)), ("kick", 0, 40),
        ("deck", "Stage Deck", 140, 60), ("pad", 140, 40),
        ("deck", "Tower Top", 160, 60, ),
        ("hex", "Hexagon Mega Ramp", 300, 60, 26, 80),
        ("down", "Rock Slide", 560, 90, 110, 4),
        ("fire", 0, -40),
        ("deck", "Finale Deck", 150, 60),
    ])
    r.log("end")
    return ["Laser Box", "Ring of Fire", "Star Jumps", "Hexagon Mega Ramp", "Rock Slide"]


# ===================================================================== 2. Island Hop
def island_hop(r, sk, rng):
    sk.title = "Island Hop"
    t = Tour(r, 230, rng)
    run(r, "Start", 90, w=64)
    W = Y0 - 72
    t.go([
        ("deck", "Pier", 170, 56),
        ("drop", 50, 40),
        ("island", "Palm Island", 170, 70, W, True), ("kick", 0, -50),
        ("island", "Coconut Cay", 160, 60, W), ("kick", 0, 50),
        ("island", "Shell Beach", 160, 56, W), ("kick", 0, -40),
        ("boat", "Red Boat", 170, 44, W, True), ("kick", 0, 50),
        ("boat", "Blue Boat", 170, 40, W), ("kick", 0, -50),
        ("boat", "Yacht", 190, 40, W), ("fire", 0, 40),
        ("island", "Volcano Isle", 170, 64, W, True), ("pad", 110, -40),
        ("deck", "Lighthouse Top", 150, 50), ("kick", 0, 40),
        ("island", "Last Cay", 170, 70, W - 0), ("kick", 0, -40),
        ("boat", "Ferry", 200, 50, W, True), ("pad", 100),
        ("deck", "Dock", 150, 60),
    ])
    t.sea()
    r.log("end")
    return ["Pier", "Palm Island", "Coconut Cay", "Red Boat", "Blue Boat", "Yacht", "Ring of Fire", "Lighthouse", "Ferry"]


# ===================================================================== 3. Rooftop Run
def rooftop_run(r, sk, rng):
    sk.title = "Rooftop Run"
    t = Tour(r, 230, rng)
    run(r, "Start", 90, w=64)
    t.go([
        ("deck", "Fire Escape", 170, 56), ("pad", 60, 40),
        ("roof", "Apartment Roof", 160, 70, Y0 - 520, True), ("drop", 40, -50),
        ("roof", "Office Roof", 170, 60), ("kick", 0, 50),
        ("roof", "Hotel Roof", 150, 50), ("pad", 90, -40),
        ("roof", "Tower Roof", 180, 70, Y0 - 520, True), ("drop", 50),
        ("box", "Billboard Laser Box", 260, 100), ("kick", 0, -50),
        ("roof", "Diner Roof", 150, 44), ("drop", 40, 40),
        ("roof", "Warehouse Roof", 200, 80, Y0 - 520, True), ("pad", 140, -40),
        ("roof", "Skyscraper Roof", 200, 70),
        ("hex", "Skyscraper Ramp", 260, 60, 24, 90),
        ("roof", "Car Park Roof", 0, 90, Y0 - 520), ("kick", 0, 40),
        ("roof", "Last Roof", 160, 60, Y0 - 520, True),
    ])
    r.log("end")
    return ["Apartment Roof", "Office Roof", "Hotel Roof", "Tower Roof", "Laser Box", "Warehouse Roof",
            "Skyscraper Ramp", "Car Park Roof"]


# ===================================================================== 4. Sky Garden
def sky_garden(r, sk, rng):
    sk.title = "Sky Garden"
    t = Tour(r, 260, rng)
    floor_y = Y0 - 330
    cap = shroom_cap([(200, 40, 50), (150, 70, 210), (60, 160, 210), (230, 120, 40)], floor_y)
    run(r, "Start", 90, w=64)
    t.go([
        ("deck", "Garden Gate", 170, 56), ("pad", 80, 40),
        ("cloud", "Cloud One", 170, 70, True), ("drop", 40, -50),
        ("cloud", "Cloud Two", 160, 60), ("kick", 0, 50),
        ("cloud", "Cloud Three", 160, 56),
        lambda: R2.bounce_chain(r, "Mushroom Bounce", [(300, 30, 0), (300, 40, 60), (300, -20, -60)], 260, s=120,
                                cap=cap, land_L=60, w_out=50),
        ("cloud", "Cloud Four", 160, 60, True), ("drop", 40, 50),
        ("star", "Morning Star", 100, (255, 230, 120)), ("drop", 40, -50),
        ("star", "Evening Star", 100, (255, 150, 200)), ("kick", 0, 40),
        ("cloud", "Cloud Five", 170, 64, True), ("fire", 0, -40),
        ("cloud", "Cloud Six", 170, 70), ("drop", 40),
        ("cloud", "Last Cloud", 160, 64, True),
    ])
    r.log("end")
    return ["Clouds", "Mushroom Bounce", "Star Jumps", "Ring of Fire"]


# ===================================================================== 5. Clockwork Town
def clockwork_town(r, sk, rng):
    sk.title = "Clockwork Town"
    t = Tour(r, 220, rng)
    brass, dark = sk.BRASS, sk.DARK
    run(r, "Start", 90, w=64)
    t.go([
        ("deck", "Town Gate", 160, 56), ("pad", 70, 40),
        ("roof", "Clockmaker's Roof", 160, 60, Y0 - 420, True), ("drop", 40, -40),
        ("roof", "Bakery Roof", 150, 50, Y0 - 420),
        lambda: R2.gear_bridge(r, "Great Wheel", 100, 5.0, col=brass),
        ("deck", "Arbor", 120, 50, (60, 50, 40)),
        lambda: R2.turnstile(r, "Hour Hand", 160, w=40, period=1.8, phase=0.0, col=dark),
        ("roof", "Belfry Roof", 150, 56, Y0 - 420, True),
        lambda: R2.pendulum_ferry(r, "Pendulum Ferry", Lp=240, amp_deg=28, period=5.0, col=brass),
        ("deck", "Weight Shelf", 120, 50, (60, 50, 40)), ("drop", 40, 50),
        ("piano", "Music Box Keys", 320, 90), ("kick", 0, -40),
        ("roof", "Tower Roof", 170, 60, Y0 - 420, True),
        lambda: R2.gear_bridge(r, "Escape Wheel", 90, -7.0, col=(150, 120, 70)),
        ("deck", "Chime Deck", 140, 56, (60, 50, 40)), ("pad", 80, 40),
        ("roof", "Clock Tower Roof", 170, 60, Y0 - 420, True), ("drop", 50, -40),
        ("roof", "Inn Roof", 160, 56, Y0 - 420), ("kick", 0, 40),
        ("roof", "Midnight Roof", 160, 60, Y0 - 420, True),
    ])
    r.log("end")
    return ["Rooftops", "Great Wheel", "Hour Hand", "Pendulum Ferry", "Music Box Keys", "Escape Wheel"]


# ===================================================================== 6. Pipe Dream
def pipe_dream(r, sk, rng):
    sk.title = "Pipe Dream"
    t = Tour(r, 230, rng)
    g = Y0 - 400
    run(r, "Start", 90, w=64)
    t.go([
        ("deck", "Start Block", 170, 56), ("kick", 0, 40),
        ("pipe", "Pipe One", 120, 70, g, True), ("pad", 70, -40),
        ("pipe", "Pipe Two", 120, 70, g), ("pad", 70, 40),
        ("pipe", "Pipe Three", 120, 70, g), ("drop", 50, -40),
        ("pipe", "Pipe Four", 120, 70, g, True), ("drop", 40),
        ("piano", "Piano Keys", 360, 90), ("fire", 0, 40),
        ("deck", "Coin Block", 150, 56, (200, 140, 40)), ("pad", 110, -40),
        ("star", "Power Star", 100, (255, 220, 60), True), ("drop", 50, 50),
        ("box", "Bonus Box", 260, 100), ("kick", 0, -40),
        ("pipe", "Pipe Five", 120, 70, g, True), ("drop", 40, 40),
        ("pipe", "Last Pipe", 140, 80, g),
    ])
    r.log("end")
    return ["Warp Pipes", "Piano Keys", "Ring of Fire", "Power Star", "Bonus Box"]


# ===================================================================== 7. Orbit
def orbit(r, sk, rng):
    sk.title = "Orbit"
    t = Tour(r, 240, rng)
    t.hill_look = dict(col=(110, 110, 120), top=(170, 170, 180), boulder=(90, 90, 100))
    run(r, "Start", 90, w=64)
    t.go([
        ("deck", "Launch Pad", 170, 60, (30, 34, 46)), ("pad", 120, 40),
        ("star", "North Star", 100, (255, 240, 160), True), ("drop", 40, -50),
        ("star", "Red Giant", 100, (255, 110, 90)), ("kick", 0, 40),
        ("deck", "Beam Dock", 140, 50, (30, 34, 46)),
        lambda: R2.tractor_beam(r, "Tractor Beam", 520, dy=40, w_land=50, land_L=60),
        ("box", "Space Station", 260, 100), ("pad", 60, -40),
        ("hex", "Comet Ramp", 240, 60, 26, 90),
        ("down", "Moon Surface", 360, 50, 110, 3), ("kick", 0, 40),
        ("deck", "Last Dock", 140, 60, (30, 34, 46)),
        lambda: R2.tractor_beam(r, "Wormhole Beam", 420, dy=20, w_land=56, land_L=60),
        ("deck", "Home Dock", 140, 60, (30, 34, 46)),
    ])
    r.log("end")
    return ["Star Jumps", "Tractor Beam", "Space Station", "Comet Ramp", "Moon Surface", "Wormhole Beam"]


# ===================================================================== 8. Eruption
def eruption(r, sk, rng):
    sk.title = "Eruption"
    t = Tour(r, 230, rng)
    t.hill_look = dict(col=(50, 40, 38), top=(70, 50, 44), boulder=(40, 32, 30))
    t.island_look = dict(sand=(60, 48, 44), rock=(40, 32, 30), palms=False)
    run(r, "Start", 90, w=64)
    L = Y0 - 260
    t.go([
        ("deck", "Crater Rim", 170, 56, (40, 32, 30)),
        ("down", "Ash Slope", 480, 100, 110, 4), ("fire", -30, 40),
        ("island", "Basalt Isle", 170, 70, L - 22, True), ("kick", 0, -50),
        ("island", "Cinder Isle", 160, 60, L - 22), ("fire", 0, 50),
        ("island", "Magma Isle", 160, 56, L - 22, True), ("kick", 0, -40),
        ("island", "Obsidian Isle", 170, 64, L - 22),
        lambda: R2.lava_surge(r, "Lava Causeway", 220, w=40, period=3.2, phase=0.0),
        ("deck", "Vent", 140, 56, (40, 32, 30)), ("pad", 160, 40),
        ("deck", "Geyser Top", 150, 50, (40, 32, 30), ), ("fire", -20, -40),
        ("deck", "Cinder Ledge", 150, 60, (40, 32, 30)),
        ("down", "Lava Slide", 380, 80, 100, 3), ("kick", -20, 40),
        ("island", "Last Isle", 170, 64, L - 22 - 100 + 0, True), ("fire", 0, -40),
        ("deck", "Last Ledge", 150, 60, (40, 32, 30)),
    ])
    t.sea(col=(255, 110, 20), kind="Burn")
    r.log("end")
    return ["Ash Slope", "Rings of Fire", "Lava Islands", "Lava Causeway", "Geyser"]


# ===================================================================== 9. Frostbite
def frostbite(r, sk, rng):
    sk.title = "Frostbite"
    t = Tour(r, 230, rng)
    t.hill_look = dict(col=(200, 210, 225), top=(240, 246, 255), boulder=(170, 185, 205))
    t.island_look = dict(sand=(225, 240, 255), rock=(170, 200, 230), palms=False)
    import rush
    run(r, "Start", 90, w=64)
    rush.booster(r, "Chairlift", 300, 300, w=70)
    W = Y0 + 300 - 360
    t.go([
        ("deck", "Summit", 170, 60, (230, 240, 250)),
        ("down", "Black Run", 520, 140, 110, 4),
        ("hex", "Ski Jump", 200, 40, 22, 70),
        ("island", "Ice Floe", 0, 70, W, True), ("kick", 0, 50),
        ("island", "Iceberg", 160, 60, W), ("kick", 0, -50),
        ("boat", "Ice Breaker", 190, 44, W, True), ("kick", 0, 40),
        ("island", "Glacier Isle", 170, 64, W),
        ("down", "Avalanche Run", 420, 60, 110, 3),
        ("fire", 0, -40),
        ("deck", "Ski Lodge", 160, 60, (230, 240, 250)),
    ])
    t.sea(col=(170, 210, 240))
    r.log("end")
    return ["Black Run", "Ski Jump", "Ice Floes", "Ice Breaker", "Avalanche Run"]


# ===================================================================== 10. High Score
def high_score(r, sk, rng):
    sk.title = "High Score"
    t = Tour(r, 260, rng)
    g = Y0 - 400
    run(r, "Start", 90, w=60)
    t.go([
        ("deck", "Insert Coin", 170, 56, (20, 20, 30)), ("drop", 50),
        ("box", "Laser Maze", 280, 100), ("kick", 0, 40),
        ("piano", "Neon Keys", 320, 80), ("pad", 90, -40),
        ("star", "Bonus Star", 100, (120, 255, 240), True), ("drop", 40, 50),
        ("pipe", "Warp Pipe", 120, 70, g), ("pad", 70, -40),
        ("pipe", "Warp Pipe Two", 120, 70, g), ("fire", 0, 40),
        ("deck", "Combo Deck", 150, 56, (20, 20, 30)), ("drop", 50, -40),
        ("box", "Boss Box", 300, 110), ("kick", 0, 40),
        ("deck", "Game Over", 150, 60, (20, 20, 30)),
    ])
    r.log("end")
    return ["Laser Maze", "Neon Keys", "Bonus Star", "Warp Pipes", "Ring of Fire", "Boss Box"]


LEVELS = {1: stunt_show, 2: island_hop, 3: rooftop_run, 4: sky_garden, 5: clockwork_town, 6: pipe_dream, 7: orbit,
          8: eruption, 9: frostbite, 10: high_score}
FINAL = {}
