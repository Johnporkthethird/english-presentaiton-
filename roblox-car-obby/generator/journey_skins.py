"""How each theme draws the journey pieces: its road, tunnel, cave and spiral centrepiece."""
import math
import random
from geom import CF, deck_frame, axis_frame, add, sub, mul, unit, cross, rot_y, rot_axis, UP
from worlds import ell, ringz
import skins as S
from skins import Pt, box, cyl, ball, cone, hexcol

TAU = math.pi * 2
KILL = {"HazardKill": True, "ObbyHazard": "Fall"}
BURN = {"HazardKill": True, "ObbyHazard": "Burn"}


def off(fr, x=0.0, y=0.0, z=0.0):
    return add(fr.p, add(add(mul(fr.x, x), mul(fr.y, y)), mul(fr.z, z)))


def F(fr, p):
    return CF(p, fr.x, fr.y, fr.z)


# ===================================================================== defaults on the base skin
def road_style(self):
    return dict(top=self.top, top_mat=self.top_mat, edge=self.edge, edge_mat="Neon", side=self.body,
                side_mat=self.body_mat, refl=0.0, center=None)


def road_piece(self, b, parent, fr, w, L, name):
    s = self.road_style()
    Pt(b, name, F(fr, off(fr, y=-2.0)), (w, 4, L), s["top"], s["top_mat"], parent, collide=True, refl=s["refl"])
    for k in (-1, 1):
        Pt(b, "RoadEdge", F(fr, off(fr, x=k * (w / 2 - 0.8), y=0.2)), (1.6, 0.4, L), s["edge"], s["edge_mat"], parent)
        Pt(b, "RoadSide", F(fr, off(fr, x=k * (w / 2 + 0.5), y=-3.5)), (1.0, 7.0, L), s["side"], s["side_mat"], parent)
    if s.get("center"):
        Pt(b, "RoadLine", F(fr, off(fr, y=0.15)), (1.2, 0.3, L), s["center"], "SmoothPlastic", parent)


def tunnel_style(self):
    return dict(wall=self.body, wall_mat=self.body_mat, rib=self.edge, rib_mat="SmoothPlastic", glow=self.edge,
                roof_transp=0.0)


def _tunnel_shape(self, b, fr, w, L, h, col, mat, grow=0.0, collide=True, name="TunnelWall", transp=0.0):
    """Walls up to 0.7h, 45-degree shoulders, a roof: an eight-sided tunnel section."""
    o = w / 2 + 2 + grow
    for k in (-1, 1):
        Pt(b, name, F(fr, off(fr, x=k * o, y=h * 0.35)), (3 + grow, h * 0.7, L), col, mat, collide=collide, transp=transp)
        c = off(fr, x=k * (o - h * 0.15), y=h * 0.85)
        Pt(b, name, F(fr, c) * rot_axis((0, 0, 1), k * math.pi / 4), (3 + grow, h * 0.3 * 1.414 + 1.5, L), col, mat,
           transp=transp)
    Pt(b, name, F(fr, off(fr, y=h + 1.5 + grow * 0.5)), (max(4.0, 2 * o - h * 0.6), 3 + grow, L), col, mat, transp=transp)


def tunnel_piece(self, b, fr, w, L, h):
    t = self.tunnel_style()
    _tunnel_shape(self, b, fr, w, L, h, t["wall"], t["wall_mat"], transp=t.get("roof_transp", 0.0))
    for k in (-1, 1):
        Pt(b, "TunnelGlow", F(fr, off(fr, x=k * (w / 2 + 0.45), y=h * 0.3)), (0.3, 1.2, L), t["glow"], "Neon")


def tunnel_rib(self, b, fr, w, h, i):
    t = self.tunnel_style()
    col = t["rib"](i) if callable(t["rib"]) else t["rib"]
    _tunnel_shape(self, b, fr, w, 4.0, h, col, t["rib_mat"], grow=1.5, collide=False, name="TunnelRib")


def tunnel_mouth(self, b, p, w, h):
    t = self.tunnel_style()
    fr = deck_frame(p, (1, 0, 0))
    col = t["rib"](0) if callable(t["rib"]) else t["rib"]
    _tunnel_shape(self, b, fr, w, 8.0, h, col, t["rib_mat"], grow=4.0, collide=False, name="TunnelMouth")


def cave_style(self):
    return dict(rock=self.body, rock_mat=self.body_mat, floor=self.danger, floor_mat="Neon", floor_attrs=BURN,
                crystal=self.edge, glow=self.edge)


def cave_rock(self, b, top, s, rng):
    self.plat(b, top, s, rng)


def cave_shell(self, b, x0, x1, y0, z, w, h, depth):
    c = self.cave_style()
    rng = random.Random(int(x0))
    L = x1 - x0
    cx = (x0 + x1) / 2
    fy = y0 - depth
    Pt(b, "CaveFloor", ((cx, fy, z)), (L, 3, w), c["floor"], c["floor_mat"], b.hazards, query=True, attrs=c["floor_attrs"])
    top = y0 + h
    H = top - fy + 10
    for k in (-1, 1):
        Pt(b, "CaveWall", ((cx, fy + H / 2 - 5, z + k * (w / 2 + 4))), (L, H, 8), c["rock"], c["rock_mat"])
        xx = x0 + rng.uniform(0, 30)
        while xx < x1:
            sz = rng.uniform(16, 34)
            r = rot_axis(unit((rng.random(), rng.random(), rng.random())), rng.random() * 3)
            yy = rng.uniform(fy, top)
            Pt(b, "Boulder", CF((xx, yy, z + k * (w / 2 - sz * 0.25)), r.x, r.y, r.z), (sz, sz * 0.8, sz * 0.7), c["rock"],
               c["rock_mat"])
            if rng.random() < 0.35:
                hexcol(b, "Crystal", (xx + 6, yy + sz * 0.6, z + k * (w / 2 - sz * 0.5)), 5, 14, c["crystal"], "Neon",
                       collide=False)
            xx += rng.uniform(26, 44)
    # the roof, with two skylights rimmed in crystal
    gaps = [(x0 + L * 0.3, 70.0), (x0 + L * 0.7, 70.0)]
    edges = [x0] + [g for gx, gw in gaps for g in (gx - gw / 2, gx + gw / 2)] + [x1]
    for a_, c_ in zip(edges[::2], edges[1::2]):
        Pt(b, "CaveRoof", (((a_ + c_) / 2, top + 4, z)), (c_ - a_, 8, w + 16), c["rock"], c["rock_mat"])
    for gx, gw in gaps:
        for k in (-1, 1):
            Pt(b, "CaveRoof", ((gx, top + 4, z + k * (w / 4 + 14))), (gw, 8, w / 2 - 12), c["rock"], c["rock_mat"])
            Pt(b, "SkylightRim", ((gx + k * gw / 2, top + 8.4, z)), (2, 1.2, 40), c["glow"], "Neon")
        Pt(b, "SkylightRim", ((gx, top + 8.4, z - 20)), (gw, 1.2, 2), c["glow"], "Neon")
        Pt(b, "SkylightRim", ((gx, top + 8.4, z + 20)), (gw, 1.2, 2), c["glow"], "Neon")
    # outside: a craggy mountain with peaks, so it reads as a place you drive into
    for k in (-1, 1):
        xx = x0 - 10
        while xx < x1 + 10:
            sz = rng.uniform(40, 75)
            r = rot_axis(unit((rng.random(), rng.random() + 0.5, rng.random())), rng.random() * 2)
            Pt(b, "Crag", CF((xx, fy + rng.uniform(0.2, 0.9) * H, z + k * (w / 2 + 8 + sz * 0.3)), r.x, r.y, r.z),
               (sz, sz * 0.9, sz * 0.6), c["rock"], c["rock_mat"])
            xx += rng.uniform(40, 60)
    peaks = max(3, int(L // 170))
    for i in range(peaks):
        px = x0 + L * (i + 0.5) / peaks
        if any(abs(px - gx) < gw for gx, gw in gaps):
            px += 90
        ph = rng.uniform(70, 150)
        zz = z + rng.uniform(-w / 4, w / 4)
        hexcol(b, "Peak", (px, top + 8 + ph * 0.35, zz), rng.uniform(70, 110), ph * 0.35, c["rock"], c["rock_mat"], collide=False)
        cone(b, "Peak", (px, top + 8 + ph * 0.35, zz), ph * 0.65, rng.uniform(60, 90), c["rock"], c["rock_mat"], n=5)
    xx = x0 + 20
    while xx < x1 - 10:
        for _ in range(2):
            zz = z + rng.uniform(-w / 2 + 8, w / 2 - 8)
            ln = rng.uniform(12, 36) if abs(zz - z) > 30 else rng.uniform(8, 22)
            cone(b, "Stalactite", (xx + rng.uniform(-10, 10), top, zz), ln, rng.uniform(6, 12), c["rock"], c["rock_mat"],
                 n=4, down=True)
        xx += rng.uniform(34, 52)
    for e in (x0, x1):  # end walls with a doorway for the road
        for k in (-1, 1):
            Pt(b, "CaveEnd", ((e, fy + H / 2 - 5, z + k * (w / 4 + 20))), (8, H, w / 2 - 40), c["rock"], c["rock_mat"])
        Pt(b, "CaveEnd", ((e, (y0 + 55 + top) / 2, z)), (8, top - y0 - 55, 80), c["rock"], c["rock_mat"])
        Pt(b, "CaveEnd", ((e, (fy + y0 - 14) / 2, z)), (8, y0 - 14 - fy, 80), c["rock"], c["rock_mat"])
        Pt(b, "CaveDoorGlow", ((e, y0 + 54, z)), (9, 1.2, 82), c["glow"], "Neon")
    for k in range(int(L // 90)):
        Pt(b, "FloorGlow", ((x0 + 45 + k * 90, fy + 1.8, z + rng.uniform(-w / 3, w / 3))), (30, 0.4, 18), c["glow"], "Neon",
           transp=0.3)


def helix_core(self, b, c, y_lo, y_hi, R, w, inside):
    x, y0, z = c
    d = max(12.0, 2 * (R - w / 2 - 14))
    cyl(b, "Core", (x, (y_lo + y_hi) / 2 - 20, z), y_hi - y_lo + 80, min(d, 60), self.body, self.body_mat)
    if inside:
        n = 20
        Ro = R + w / 2 + 6
        for k in range(n):
            a = TAU * (k + 0.5) / n
            p = (x + Ro * math.cos(a), (y_lo + y_hi) / 2 + 10, z + Ro * math.sin(a))
            Pt(b, "TowerWall", CF(p) * rot_y(-a), (6, y_hi - y_lo + 110, TAU * Ro / n + 1), self.body, self.body_mat)


def launcher(self, b, p, w):
    """A glowing launch arch over a big launch pad (nothing on it collides)."""
    x, y, z = p
    s = self.road_style()
    for k in (-1, 1):
        Pt(b, "LaunchPost", ((x, y + 18, z + k * (w / 2 + 3))), (5, 36, 5), s["side"], s["side_mat"])
        Pt(b, "LaunchGlow", ((x - 2.6, y + 18, z + k * (w / 2 + 3))), (0.4, 32, 1.4), s["edge"], "Neon")
    Pt(b, "LaunchBeam", ((x, y + 37.5, z)), (6, 4, w + 12), s["side"], s["side_mat"])
    Pt(b, "LaunchBeamGlow", ((x - 3.2, y + 37.5, z)), (0.4, 1.4, w + 10), s["edge"], "Neon")


for name, fn in list(globals().items()):
    if name in ("launcher", "road_style", "road_piece", "tunnel_style", "tunnel_piece", "tunnel_rib", "tunnel_mouth", "cave_style",
                "cave_rock", "cave_shell", "helix_core"):
        setattr(S.Skin, name, fn)


def style(cls, **methods):
    for k, v in methods.items():
        setattr(cls, k, v)


# ===================================================================== the ten themes
# 1. Sugar Rush: frosting roads, candy-cane tubes, a chocolate cave, a giant candy-cane pole
def _candy_core(self, b, c, y_lo, y_hi, R, w, inside):
    x, y0, z = c
    y = y_lo - 40
    k = 0
    while y < y_hi + 30:
        cyl(b, "CanePole", (x, y + 6, z), 12.1, 26, (225, 30, 50) if k % 2 else (255, 255, 255))
        y += 12
        k += 1
    for j in range(1, 9):
        a = math.pi * j / 8
        ball(b, "CaneHook", (x + math.sin(a) * 30, y + 6 + (1 - math.cos(a)) * 30, z), 27, (225, 30, 50) if j % 2 else (255, 255, 255))


style(S.SugarRush,
      road_style=lambda self: dict(top=(255, 168, 204), top_mat="SmoothPlastic", edge=(255, 255, 255), edge_mat="SmoothPlastic",
                                   side=(88, 52, 34), side_mat="SmoothPlastic", refl=0.05, center=None),
      tunnel_style=lambda self: dict(wall=(255, 250, 252), wall_mat="SmoothPlastic", rib=lambda i: (225, 30, 50) if i % 2 else (120, 225, 200),
                                     rib_mat="SmoothPlastic", glow=(255, 150, 200), roof_transp=0.0),
      cave_style=lambda self: dict(rock=(74, 42, 28), rock_mat="SmoothPlastic", floor=(110, 64, 40), floor_mat="SmoothPlastic",
                                   floor_attrs=KILL, crystal=(255, 150, 210), glow=(255, 190, 230)),
      helix_core=_candy_core)


# 2. Drive Thru: asphalt with a yellow line, a drive-thru building, an oven, a milkshake
def _diner_core(self, b, c, y_lo, y_hi, R, w, inside):
    self.tower(b, (c[0], y_lo, c[2]), y_lo - 40, y_hi + 40)


style(S.DriveThru,
      road_style=lambda self: dict(top=(46, 46, 52), top_mat="Asphalt", edge=(255, 255, 255), edge_mat="SmoothPlastic",
                                   side=(205, 30, 42), side_mat="SmoothPlastic", refl=0.0, center=(255, 205, 40)),
      tunnel_style=lambda self: dict(wall=(205, 30, 42), wall_mat="SmoothPlastic", rib=(214, 220, 230), rib_mat="Metal",
                                     glow=(255, 90, 90), roof_transp=0.0),
      cave_style=lambda self: dict(rock=(60, 60, 66), rock_mat="DiamondPlate", floor=(255, 110, 30), floor_mat="Neon",
                                   floor_attrs=BURN, crystal=(255, 200, 60), glow=(255, 140, 40)),
      helix_core=_diner_core)


# 3. Spore Springs: moss roads, hollow logs, a glowing root cave over a glowing pond, a giant mushroom
def _spore_core(self, b, c, y_lo, y_hi, R, w, inside):
    self.tower(b, (c[0], y_lo, c[2]), y_lo - 50, y_hi + 60)


style(S.SporeSprings,
      road_style=lambda self: dict(top=(84, 140, 58), top_mat="Grass", edge=(120, 255, 210), edge_mat="Neon",
                                   side=(104, 72, 48), side_mat="Wood", refl=0.0, center=None),
      tunnel_style=lambda self: dict(wall=(104, 72, 48), wall_mat="Wood", rib=(74, 50, 34), rib_mat="Wood",
                                     glow=(120, 255, 210), roof_transp=0.0),
      cave_style=lambda self: dict(rock=(58, 44, 40), rock_mat="Slate", floor=(60, 200, 190), floor_mat="Neon",
                                   floor_attrs=KILL, crystal=(190, 130, 255), glow=(120, 255, 210)),
      helix_core=_spore_core)


# 4. Checkmate: marble roads, a castle corridor, a dungeon, the inside of a castle tower
def _chess_core(self, b, c, y_lo, y_hi, R, w, inside):
    x, y0, z = c
    n = 20
    Ro = R + w / 2 + 6
    H = y_hi - y_lo + 70
    for k in range(n):
        a = TAU * (k + 0.5) / n
        p = (x + Ro * math.cos(a), y_lo - 20 + H / 2, z + Ro * math.sin(a))
        Pt(b, "TowerWall", CF(p) * rot_y(-a), (8, H, TAU * Ro / n + 1), (160, 158, 150), "Cobblestone")
        if k % 2 == 0:
            Pt(b, "Merlon", CF((p[0], y_lo - 20 + H + 4, p[2])) * rot_y(-a), (8, 8, TAU * Ro / n * 0.6), (160, 158, 150),
               "Cobblestone")
    cyl(b, "TowerCore", (x, (y_lo + y_hi) / 2, z), y_hi - y_lo + 40, max(12.0, 2 * (R - w / 2 - 16)), self.WHITE, "Marble")
    ringz(b, (x, y_hi + 20, z), R - w / 2 - 10, self.GOLD, "Metal", th=2.0)


style(S.Checkmate,
      road_style=lambda self: dict(top=(242, 238, 228), top_mat="Marble", edge=(232, 190, 90), edge_mat="Metal",
                                   side=(92, 56, 32), side_mat="Wood", refl=0.05, center=None),
      tunnel_style=lambda self: dict(wall=(150, 148, 140), wall_mat="Cobblestone", rib=(90, 88, 84), rib_mat="Cobblestone",
                                     glow=(255, 160, 60), roof_transp=0.0),
      cave_style=lambda self: dict(rock=(110, 108, 104), rock_mat="Cobblestone", floor=(12, 10, 16), floor_mat="SmoothPlastic",
                                   floor_attrs=KILL, crystal=(255, 160, 60), glow=(255, 170, 70)),
      helix_core=_chess_core)


# 5. Tick Tock: brass roads, a gear tunnel, the inside of the mechanism, stacked turning gears
def _clock_core(self, b, c, y_lo, y_hi, R, w, inside):
    x, y0, z = c
    cyl(b, "Axle", (x, (y_lo + y_hi) / 2, z), y_hi - y_lo + 80, 10, self.DARK, "Metal")
    y = y_lo
    k = 0
    rng = random.Random(int(x))
    while y < y_hi + 20:
        top = (x, y, z)
        d = 2 * (R - w / 2 - 12)
        root = b.prop_root("CoreGear")
        rig = b.rig(root, "Spin", axis_frame(top, UP), (1 if k % 2 else -1) * 0.05, 4, phase=rng.random(), name="GearSpin")
        col = self.BRASS if k % 2 else self.COPPER
        cyl(b, "CoreGear", top, 6, d, col, "Metal", rig)
        for j in range(16):
            a = TAU * j / 16
            Pt(b, "Tooth", CF((x + math.cos(a) * d / 2, y, z + math.sin(a) * d / 2)) * rot_y(-a), (6, 6, 6), col, "Metal", rig)
        y += 55
        k += 1


style(S.TickTock,
      road_style=lambda self: dict(top=(206, 164, 74), top_mat="Metal", edge=(190, 112, 64), edge_mat="Metal",
                                   side=(52, 42, 36), side_mat="Metal", refl=0.15, center=None),
      tunnel_style=lambda self: dict(wall=(60, 52, 46), wall_mat="DiamondPlate", rib=(206, 164, 74), rib_mat="Metal",
                                     glow=(255, 190, 90), roof_transp=0.0),
      cave_style=lambda self: dict(rock=(70, 60, 52), rock_mat="Metal", floor=(20, 16, 14), floor_mat="SmoothPlastic",
                                   floor_attrs=KILL, crystal=(255, 200, 110), glow=(255, 190, 90)),
      helix_core=_clock_core)


# 6. Toy Box: an orange toy race track, a cardboard tunnel, the inside of the toy box, a ring-stacker toy
def _toy_core(self, b, c, y_lo, y_hi, R, w, inside):
    x, y0, z = c
    cyl(b, "Peg", (x, (y_lo + y_hi) / 2, z), y_hi - y_lo + 60, 12, (240, 240, 240))
    y = y_lo - 20
    k = 0
    while y < y_hi + 20:
        ringz(b, (x, y, z), max(14.0, R - w / 2 - 14 - k * 2), self.BRICKS[k % len(self.BRICKS)], "SmoothPlastic", th=12.0)
        y += 14
        k += 1


style(S.ToyBox,
      road_style=lambda self: dict(top=(255, 122, 24), top_mat="SmoothPlastic", edge=(255, 214, 40), edge_mat="SmoothPlastic",
                                   side=(230, 90, 10), side_mat="SmoothPlastic", refl=0.08, center=None),
      tunnel_style=lambda self: dict(wall=(196, 156, 104), wall_mat="SmoothPlastic", rib=lambda i: S.ToyBox.BRICKS[i % 6],
                                     rib_mat="SmoothPlastic", glow=(255, 255, 255), roof_transp=0.0),
      cave_style=lambda self: dict(rock=(232, 200, 150), rock_mat="Wood", floor=(60, 150, 255), floor_mat="SmoothPlastic",
                                   floor_attrs=KILL, crystal=(255, 80, 80), glow=(255, 230, 120)),
      helix_core=_toy_core)


# 7. Orbit: station plating, a corridor, a hollow asteroid, a rocket
def _space_core(self, b, c, y_lo, y_hi, R, w, inside):
    x, y0, z = c
    H = y_hi - y_lo + 60
    cyl(b, "Rocket", (x, y_lo - 20 + H / 2, z), H, 30, (235, 238, 245), "SmoothPlastic")
    cone(b, "RocketNose", (x, y_lo - 20 + H, z), 40, 30, (220, 40, 50), n=6)
    for k in range(4):
        a = TAU * k / 4
        Pt(b, "Fin", CF((x + math.cos(a) * 20, y_lo, z + math.sin(a) * 20)) * rot_y(-a), (14, 34, 2), (220, 40, 50))
    cyl(b, "Exhaust", (x, y_lo - 30, z), 8, 20, self.edge, "Neon")


style(S.Orbit,
      road_style=lambda self: dict(top=(92, 98, 116), top_mat="DiamondPlate", edge=(90, 220, 255), edge_mat="Neon",
                                   side=(40, 44, 58), side_mat="Metal", refl=0.1, center=None),
      tunnel_style=lambda self: dict(wall=(70, 76, 92), wall_mat="Metal", rib=(40, 44, 58), rib_mat="Metal",
                                     glow=(90, 220, 255), roof_transp=0.0),
      cave_style=lambda self: dict(rock=(96, 92, 90), rock_mat="Slate", floor=(6, 6, 14), floor_mat="SmoothPlastic",
                                   floor_attrs=KILL, crystal=(160, 110, 255), glow=(90, 220, 255)),
      helix_core=_space_core)


# 8. Eruption: basalt roads with lava edges, a lava tube, a magma chamber, an obsidian spire
def _lava_core(self, b, c, y_lo, y_hi, R, w, inside):
    x, y0, z = c
    hexcol(b, "Spire", (x, y_hi + 30, z), max(20.0, 2 * (R - w / 2 - 14)), y_hi - y_lo + 90, self.body, "Basalt",
           collide=False)
    for k in range(int((y_hi - y_lo) // 50) + 1):
        hexcol(b, "LavaVein", (x, y_lo + k * 50, z), max(20.0, 2 * (R - w / 2 - 14)) + 0.8, 2, self.LAVA, "CrackedLava",
               collide=False)


style(S.Eruption,
      road_style=lambda self: dict(top=(54, 46, 44), top_mat="Basalt", edge=(255, 110, 20), edge_mat="CrackedLava",
                                   side=(32, 28, 28), side_mat="Basalt", refl=0.0, center=None),
      tunnel_style=lambda self: dict(wall=(40, 34, 32), wall_mat="Basalt", rib=(255, 110, 20), rib_mat="CrackedLava",
                                     glow=(255, 120, 30), roof_transp=0.0),
      cave_style=lambda self: dict(rock=(40, 34, 32), rock_mat="Basalt", floor=(255, 100, 20), floor_mat="Neon",
                                   floor_attrs=BURN, crystal=(255, 170, 40), glow=(255, 120, 30)),
      helix_core=_lava_core)


# 9. Frostbite: glacier roads, an ice tunnel, an ice cavern over black water, an ice spire
def _ice_core(self, b, c, y_lo, y_hi, R, w, inside):
    x, y0, z = c
    hexcol(b, "IceSpire", (x, y_hi + 40, z), max(20.0, 2 * (R - w / 2 - 14)), y_hi - y_lo + 100, self.ICE, "Ice",
           collide=False)
    cone(b, "SpireTip", (x, y_hi + 40, z), 50, max(20.0, 2 * (R - w / 2 - 14)), self.ICE, "Ice", n=5)


style(S.Frostbite,
      road_style=lambda self: dict(top=(196, 226, 248), top_mat="Glacier", edge=(246, 250, 255), edge_mat="Snow",
                                   side=(120, 180, 232), side_mat="Ice", refl=0.05, center=None),
      tunnel_style=lambda self: dict(wall=(150, 205, 245), wall_mat="Ice", rib=(246, 250, 255), rib_mat="Snow",
                                     glow=(120, 220, 255), roof_transp=0.15),
      cave_style=lambda self: dict(rock=(150, 200, 240), rock_mat="Ice", floor=(16, 30, 54), floor_mat="SmoothPlastic",
                                   floor_attrs=KILL, crystal=(160, 240, 255), glow=(120, 220, 255)),
      helix_core=_ice_core)


# 10. High Score: neon-grid roads, a wormhole of neon rings, the inside of the cabinet, a giant joystick
def _arcade_core(self, b, c, y_lo, y_hi, R, w, inside):
    x, y0, z = c
    cyl(b, "Stick", (x, (y_lo + y_hi) / 2, z), y_hi - y_lo + 40, 14, (30, 30, 40))
    ball(b, "StickBall", (x, y_hi + 34, z), 40, (255, 50, 80))
    for k in range(int((y_hi - y_lo) // 40) + 1):
        ringz(b, (x, y_lo + k * 40, z), 9, self.NEON[k % 6], "Neon", th=2.0)


def _arcade_road(self, b, parent, fr, w, L, name):
    p = S.Skin.road_piece(self, b, parent, fr, w, L, name)
    return p


style(S.HighScore,
      road_style=lambda self: dict(top=(22, 20, 36), top_mat="SmoothPlastic", edge=(255, 60, 200), edge_mat="Neon",
                                   side=(60, 230, 255), side_mat="Neon", refl=0.15, center=None),
      tunnel_style=lambda self: dict(wall=(18, 16, 30), wall_mat="SmoothPlastic", rib=lambda i: S.HighScore.NEON[i % 6],
                                     rib_mat="Neon", glow=(60, 230, 255), roof_transp=0.0),
      cave_style=lambda self: dict(rock=(20, 60, 40), rock_mat="SmoothPlastic", floor=(10, 8, 20), floor_mat="SmoothPlastic",
                                   floor_attrs=KILL, crystal=(60, 255, 140), glow=(60, 230, 255)),
      helix_core=_arcade_core)


# ===================================================================== the ten journeys
# (key, label, settings). "_link": False = the next piece carries straight on by road instead of a pad hop.
S.SugarRush.recipe = [
    ("helix", "Candy-cane spiral climb", {"dy": 190.0, "_link": False}),
    ("tunnel", "Candy-cane tube dive", {"L": 520.0, "dy": -110.0, "boosts": 3}),
    ("hops", "Gumdrop hops", {"layout": "wave", "n": 3}),
    ("sweepers", "Candy-cane sweepers", {}),
    ("launch_up", "Cake-top launch", {"dy": 170.0, "_link": False}),
    ("narrow", "Licorice tightrope", {"L": 340.0, "w": 14.0}),
    ("cliff", "Whipped-cream dive", {"dy": 150.0}),
    ("loop", "Frosted donut loop", {}),
    ("crumble", "Chocolate crumble", {}),
]
S.SugarRush.extra = [("turntable", "Lollipop turntable", {}), ("belts", "Licorice conveyors", {})]

S.DriveThru.recipe = [
    ("tunnel", "Drive-thru lane", {"L": 520.0, "boosts": 3, "_link": False}),
    ("ramp", "Ketchup ramp down", {"dy": -150.0, "w0": 56.0, "w1": 34.0, "dz": 60.0}),
    ("hops", "Burger & fries hops", {"layout": "steps", "n": 3}),
    ("launch_up", "Spatula catapult", {"dy": 180.0, "_link": False}),
    ("narrow", "Straw bridge", {"L": 360.0, "w": 12.0}),
    ("helix", "Milkshake spiral down", {"dy": -190.0}),
    ("gates", "Ketchup & mustard gates", {}),
    ("log", "Rolling pickle", {}),
    ("crushers", "Burger presses", {}),
]
S.DriveThru.extra = [("belts", "Grill conveyors", {}), ("swings", "Swinging spatulas", {})]

S.SporeSprings.recipe = [
    ("cliff", "Hollow-trunk dive", {"dy": 160.0, "_link": False}),
    ("cave", "Glowroot cavern", {}),
    ("ramp", "Vine climb", {"dy": 150.0, "dz": -70.0, "w0": 44.0, "w1": 30.0}),
    ("swings", "Swinging leaves", {}),
    ("launch_up", "Mushroom bounce", {"dy": 170.0}),
    ("hops", "Toadstool tops", {"layout": "falling", "n": 3}),
    ("pipe", "Hollow log", {}),
    ("bumpers", "Puffball field", {}),
]
S.SporeSprings.extra = [("spin_bridges", "Spinning bark bridges", {})]

S.Checkmate.recipe = [
    ("tunnel", "Castle gate", {"L": 480.0, "boosts": 2, "_link": False}),
    ("helix", "Tower stair climb", {"dy": 230.0, "inside": True}),
    ("hops", "Rook leaps from the battlements", {"layout": "falling", "n": 3}),
    ("ramp", "Great board slide", {"dy": -170.0, "w0": 90.0, "w1": 56.0}),
    ("crushers", "Pawn crushers", {}),
    ("cross", "Rotating chessboard", {}),
    ("cave", "Dungeon pit", {}),
    ("sweepers", "Sceptre sweepers", {}),
]
S.Checkmate.extra = [("doors", "Sliding castle walls", {})]

S.TickTock.recipe = [
    ("helix", "Clock tower climb", {"dy": 240.0, "inside": True, "_link": False}),
    ("narrow", "Minute-hand walk", {"L": 380.0, "w": 16.0}),
    ("cliff", "Pendulum shaft drop", {"dy": 170.0}),
    ("swings", "Brass pendulums", {}),
    ("tunnel", "Gear tunnel", {"L": 460.0, "dy": 70.0, "boosts": 3}),
    ("sweepers", "Clock-hand sweepers", {}),
    ("pistons", "Gear-tooth pistons", {}),
    ("spin_bridges", "Cog bridges", {}),
]
S.TickTock.extra = [("hops", "Gear hops", {"layout": "falling"})]

S.ToyBox.recipe = [
    ("slide", "Race-track slide", {"dy": -170.0, "L": 780.0, "_link": False}),
    ("loop", "Track loop", {}),
    ("launch_up", "Spring launcher", {"dy": 200.0}),
    ("hops", "Alphabet block steps", {"layout": "steps", "n": 3}),
    ("ramp", "Playground slide", {"dy": -150.0, "w0": 40.0, "w1": 60.0, "dz": -60.0}),
    ("bumpers", "Spinning tops", {}),
    ("crumble", "Domino path", {}),
    ("swings", "Toy swings", {}),
]
S.ToyBox.extra = [("doors", "Sliding brick walls", {})]

S.Orbit.recipe = [
    ("tunnel", "Launch tube", {"L": 620.0, "dy": 160.0, "boosts": 4, "_link": False}),
    ("hops", "Zero-g planet hops", {"layout": "wave", "n": 3}),
    ("long_jump", "Moonshot", {}),
    ("tunnel", "Station corridor", {"L": 420.0, "boosts": 1}),
    ("bumpers", "Asteroid field", {}),
    ("loop", "Ring loop", {"_link": False}),
    ("ramp", "Re-entry dive", {"dy": -200.0, "w0": 40.0, "w1": 60.0}),
    ("spin_bridges", "Satellite bridges", {}),
]
S.Orbit.extra = [("drop", "Meteor drop", {})]

S.Eruption.recipe = [
    ("ramp", "Canyon descent", {"dy": -170.0, "dz": 70.0, "w0": 44.0, "w1": 32.0, "_link": False}),
    ("narrow", "Obsidian ledge", {"L": 360.0, "w": 16.0}),
    ("launch_up", "Geyser blast", {"dy": 200.0}),
    ("hops", "Obsidian descent", {"layout": "falling", "n": 3}),
    ("gates", "Lava geysers", {}),
    ("crumble", "Crumbling crust", {}),
    ("slide", "Lava-tube slide", {"dy": -150.0, "L": 700.0}),
    ("sweepers", "Flame sweepers", {}),
    ("pistons", "Magma pistons", {}),
]
S.Eruption.extra = [("drop", "Caldera drop", {})]

S.Frostbite.recipe = [
    ("slide", "Bobsled run", {"dy": -190.0, "L": 820.0, "_link": False}),
    ("long_jump", "Ski jump", {}),
    ("cave", "Ice cavern", {}),
    ("rink", "Frozen lake", {}),
    ("crushers", "Icicle crushers", {}),
    ("ramp", "Glacier climb", {"dy": 160.0, "w0": 44.0, "w1": 30.0}),
    ("wallride", "Glacier wall ride", {}),
    ("bumpers", "Snowman slalom", {}),
]
S.Frostbite.extra = [("spin_bridges", "Snowflake bridges", {})]

S.HighScore.recipe = [
    ("tunnel", "Wormhole", {"L": 600.0, "dy": -130.0, "boosts": 4, "_link": False}),
    ("bumpers", "Pinball bumpers", {}),
    ("launch_up", "Plunger launch", {"dy": 200.0}),
    ("hops", "Coin climb", {"layout": "rising", "n": 3}),
    ("narrow", "Pixel tightrope", {"L": 340.0, "w": 14.0}),
    ("gates", "Laser rhythm", {}),
    ("loop", "Neon loop", {}),
    ("pistons", "Equaliser bars", {}),
    ("doors", "Invader walls", {}),
]
S.HighScore.extra = [("crumble", "Pixel path", {})]



# ===================================================================== themed launchers
def _cake_launcher(self, b, p, w):
    x, y, z = p
    for k, (r, col) in enumerate(((w * 0.75, (255, 238, 244)), (w * 0.6, (255, 168, 204)), (w * 0.45, (255, 238, 244)))):
        for s in (-1, 1):
            cyl(b, "CakeTier", (x, y + 6 + k * 10, z + s * (w / 2 + r * 0.5 + 4)), 10, r, col)
    cupcake_top = (x, y + 38, z + w / 2 + w * 0.4)
    ball(b, "Cherry", cupcake_top, 10, (210, 20, 40))


def _spatula_launcher(self, b, p, w):
    x, y, z = p
    Pt(b, "SpatulaBlade", CF((x - 6, y + 0.6, z)) * rot_axis((0, 0, 1), 0.12), (30, 0.6, w * 0.8), (200, 205, 212), "Metal",
       refl=0.25)
    Pt(b, "SpatulaHandle", CF((x - 40, y + 6, z)) * rot_axis((0, 0, 1), 0.12), (50, 4, 4), (40, 40, 44))
    for k in (-1, 1):
        cyl(b, "Hinge", (x - 22, y + 2, z + k * (w * 0.4)), 6, 6, (214, 220, 230), "Metal", axis=(0, 0, 1))


def _mushroom_launcher(self, b, p, w):
    x, y, z = p
    for k in (-1, 1):
        zz = z + k * (w / 2 + 16)
        cyl(b, "BounceStem", (x, y + 8, zz), 16, 10, (236, 226, 200))
        ell(b, "BounceCap", (x, y + 20, zz), (34, 16, 34), (90, 60, 170))
        for j in range(5):
            a = TAU * j / 5
            ell(b, "BounceSpot", (x + math.cos(a) * 9, y + 26, zz + math.sin(a) * 9), (6, 2, 6), (120, 255, 210), "Neon")


def _spring_launcher(self, b, p, w):
    x, y, z = p
    for k in (-1, 1):
        zz = z + k * (w / 2 + 10)
        for j in range(8):
            ringz(b, (x, y + 3 + j * 4, zz), 7, (200, 200, 210), "Metal", th=1.2, name="Coil")
        cyl(b, "SpringCap", (x, y + 35, zz), 3, 18, self.BRICKS[(k + 1) // 2 * 2])


def _geyser_launcher(self, b, p, w):
    x, y, z = p
    for k in (-1, 1):
        cone(b, "GeyserVent", (x, y - 2, z + k * (w / 2 + 10)), 16, 22, self.body, "Basalt", n=4)
        cyl(b, "GeyserJet", (x, y + 40, z + k * (w / 2 + 10)), 80, 8, self.LAVA2, "Neon", transp=0.35)


def _plunger_launcher(self, b, p, w):
    x, y, z = p
    cyl(b, "Plunger", (x - 30, y + 6, z), 40, 10, (210, 214, 224), "Metal", axis=(1, 0, 0), refl=0.4)
    ball(b, "PlungerKnob", (x - 52, y + 6, z), 16, (255, 50, 80))
    for j in range(5):
        ringz(b, (x - 30 + j * 6, y + 6, z), 7, self.NEON[j], "Neon", th=1.0, axis=(1, 0, 0), name="PlungerCoil")


S.SugarRush.launcher = _cake_launcher
S.DriveThru.launcher = _spatula_launcher
S.SporeSprings.launcher = _mushroom_launcher
S.ToyBox.launcher = _spring_launcher
S.Eruption.launcher = _geyser_launcher
S.HighScore.launcher = _plunger_launcher
