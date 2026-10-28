"""The ten showcase themes. A skin draws every object of its level; showcase.py decides where they go.

Drivable tops are always real collidable parts at exactly the requested height (round or lumpy visuals get an
invisible flat "Floor" under them). Hazard parts carry the ObbyHazard attribute and never collide.
"""
import math
import random
from geom import CF, deck_frame, axis_frame, look_frame, add, sub, mul, unit, cross, dot, rot_y, rot_axis, UP
from builder import THICK, mix
from worlds import hsv, ell, mesh, collider, ringz
import parkour as V2
import levels3
import showcase as SC

TAU = math.pi * 2


# ===================================================================== primitives
def Pt(b, name, cf, size, color, mat="SmoothPlastic", parent=None, collide=False, transp=0.0, shape=1, refl=0.0,
       attrs=None, query=None, cls="Part"):
    if not isinstance(cf, CF):
        cf = CF(cf)
    return b.part(name, cf, size, color, mat, parent=parent if parent is not None else b.roads, collide=collide,
                  query=collide if query is None else query, transp=transp, shape=shape, attrs=attrs, cls=cls, refl=refl)


def box(b, name, c, size, color, mat="SmoothPlastic", parent=None, yaw=0.0, **kw):
    cf = CF(c) * rot_y(yaw) if yaw else CF(c)
    return Pt(b, name, cf, size, color, mat, parent, **kw)


def cyl(b, name, c, h, d, color, mat="SmoothPlastic", parent=None, axis=UP, **kw):
    return Pt(b, name, axis_frame(c, axis), (h, d, d), color, mat, parent, shape=2, **kw)


def ball(b, name, c, d, color, mat="SmoothPlastic", parent=None, **kw):
    return Pt(b, name, CF(c), (d, d, d), color, mat, parent, shape=0, **kw)


def floor(b, top, sx, sz=None, parent=None, round_=False):
    return collider(b, top, sx, sz if sz is not None else sx, parent=parent, round_=round_)


def samples(b, x0, x1, y, z, w):
    n = max(1, int((x1 - x0) // 30))
    for k in range(n + 1):
        b.samples.append((x0 + (x1 - x0) * k / n, y, z, w))


def cone(b, name, base, h, d, color, mat="SmoothPlastic", parent=None, n=5, down=False, **kw):
    """A cone from stacked cylinders: base centre `base`, pointing up (or down)."""
    for i in range(n):
        t0 = i / n
        dd = d * (1 - (i + 0.5) / n) + 0.4
        yy = h * (t0 + 0.5 / n)
        c = sub(base, (0, yy, 0)) if down else add(base, (0, yy, 0))
        cyl(b, name, c, h / n + 0.05, dd, color, mat, parent, **kw)


def hexcol(b, name, top, s, h, color, mat, parent=None, collide=True):
    for i, a in enumerate((0, math.pi / 3, 2 * math.pi / 3)):
        Pt(b, name, CF(sub(top, (0, h / 2, 0))) * rot_y(a), (s, h, s / math.sqrt(3)), color, mat, parent,
           collide=collide and i == 0, query=collide)


FONT = {
    "A": ["01110", "10001", "11111", "10001", "10001"],
    "B": ["11110", "10001", "11110", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "11110", "10000", "11111"],
    "X": ["10001", "01010", "00100", "01010", "10001"],
    "Y": ["10001", "01010", "00100", "00100", "00100"],
    "Z": ["11111", "00010", "00100", "01000", "11111"],
    "1": ["00100", "01100", "00100", "00100", "01110"],
    "2": ["11110", "00001", "01110", "10000", "11111"],
    "3": ["11110", "00001", "01110", "00001", "11110"],
    "heart": ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"],
    "star": ["0001000", "0011100", "1111111", "0111110", "0110110", "1100011"],
    "alien": ["00100000100", "00010001000", "00111111100", "01101110110", "11111111111", "10111111101",
              "10100000101", "00011011000"],
    "arrow": ["00100", "00110", "11111", "00110", "00100"],
}


def pixel_art(b, centre, normal, up, rows, px, color, mat="SmoothPlastic", parent=None, th=0.3, name="Pixel"):
    """Pixel art on a face: `normal` points out of the face, `up` is the art's up direction in the face."""
    n = unit(normal)
    v = unit(up)
    u = cross(mul(n, -1), v)
    z = cross(u, n)
    R, C = len(rows), len(rows[0])
    for i, row in enumerate(rows):
        j = 0
        while j < C:
            if row[j] != "1":
                j += 1
                continue
            j1 = j
            while j1 + 1 < C and row[j1 + 1] == "1":
                j1 += 1
            cc = (j + j1) / 2 - (C - 1) / 2
            p = add(centre, add(add(mul(u, cc * px), mul(v, ((R - 1) / 2 - i) * px)), mul(n, th / 2)))
            Pt(b, name, CF(p, u, n, z), ((j1 - j + 1) * px, th, px), color, mat, parent)
            j = j1 + 1


# ===================================================================== the base skin
class Skin:
    key = "base"
    theme_name = "Showcase"
    title = "Showcase"
    clock, bloom, hue, scale = 14.0, 0.4, 0.0, 1.0
    body, top, edge, padc, danger = (60, 60, 70), (200, 200, 210), (255, 255, 255), (90, 220, 255), (255, 60, 60)
    glass = (230, 240, 255)
    body_mat, top_mat = "SmoothPlastic", "SmoothPlastic"
    gate_post, gate_board, gate_text = (60, 60, 70), (30, 30, 36), (255, 220, 80)
    finish_cols = ((245, 245, 245), (24, 24, 28))
    hoop_mat = "Neon"
    recipe, extra = [], []
    light_over = {}
    dry = False

    def pal(self):
        p = dict(body=self.body, top=self.top, edge=self.edge, pad=self.padc, danger=self.danger, glass=self.glass,
                 body_mat=self.body_mat, top_mat=self.top_mat, clock=self.clock, bloom=self.bloom, hue=self.hue)
        p.update(road=self.top, road_mat=self.top_mat, accent=self.gate_text, accent2=self.body, metal=self.gate_post,
                 deco=self.gate_board, key=self.key, boost_speed=230, style=self.key)
        return p

    def light(self):
        a = levels3.light_attrs(self.pal())
        a.update(self.light_over)
        return a

    # ------------------------------------------------------------ surfaces
    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        Pt(b, "Deck", ((cx, y - 4, z)), (L, 8, w), self.top, self.top_mat, collide=True)
        for s in (-1, 1):
            Pt(b, "Trim", ((cx, y + 0.15, z + s * (w / 2 - 0.6))), (L, 0.3, 1.2), self.edge, "Neon")
        samples(b, x0, x1, y, z, w)

    def supports(self, b, x0, x1, y, z, w):
        """Themed structure hanging under a deck, one every ~150 studs."""
        L = x1 - x0
        if L < 50:
            return
        n = max(1, int(round(L / 150)))
        for i in range(n):
            self.under(b, (x0 + L * (i + 0.5) / n, y - 6, z), w, i)

    def under(self, b, top, w, i):
        cone(b, "Support", top, 50, w * 0.4, self.body, self.body_mat, n=4, down=True)

    def plat(self, b, top, s, rng, parent=None):
        cyl(b, "Platform", sub(top, (0, 6, 0)), 12, s, self.top, self.top_mat, collide=True)
        cyl(b, "Rim", sub(top, (0, 0.6, 0)), 1.2, s + 1, self.edge, "Neon")
        b.samples.append((top[0], top[1], top[2], s))

    def island(self, b, c, s, rng):
        self.plat(b, c, s, rng)

    def tower_plat(self, b, top, s, rng):
        self.plat(b, top, s, rng)

    def finale_plat(self, b, top, s, rng):
        self.plat(b, top, s, rng)

    def hub(self, b, c, d):
        cyl(b, "Hub", sub(c, (0, 5, 0)), 10, d, self.top, self.top_mat, collide=True)
        cyl(b, "HubRim", sub(c, (0, 0.5, 0)), 1.0, d + 1, self.edge, "Neon")

    # ------------------------------------------------------------ pads and hoops
    def pad_art(self, b, start, f):
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        Pt(b, "PadPlate", fr, (30, 0.2, 26), mix(self.padc, (0, 0, 0), 0.6))
        for k in range(3):
            c = add(start, add(mul(f, -7 + k * 7), (0, 0.25, 0)))
            V2.chevron(b, c, f, 14, self.padc)
        for s in (-1, 1):
            Pt(b, "PadRail", CF(add(start, add(mul(fr.x, s * 15), (0, 0.3, 0))), fr.x, fr.y, fr.z), (0.8, 0.4, 26),
               self.padc, "Neon")

    def hoop(self, b, c, axis, r):
        ringz(b, c, r, self.padc, self.hoop_mat, th=2.0, axis=axis, name="Hoop")

    # ------------------------------------------------------------ moving pieces
    def sweeper(self, b, rig, c, s, low):
        if low:
            Pt(b, "SweepBar", (add(c, (0, 3.2, 0))), (s - 6, 3, 2.4), self.danger, "Neon", rig, query=True,
               attrs={"ObbyHazard": "Burn"})
        else:
            Pt(b, "SweepWall", (add(c, (0, 7, 0))), (s - 6, 14, 3), self.danger, "Neon", rig, query=True,
               attrs={"ObbyHazard": "Knock"})

    def turntable(self, b, rig, c, R, k, holes):
        for i in range(k):
            if i in holes:
                continue
            a = TAU * (i + 0.5) / k
            dv = (math.cos(a), 0, math.sin(a))
            mid = add(c, mul(dv, R / 2 + 8))
            Pt(b, "Sector", deck_frame(sub(mid, (0, THICK / 2, 0)), dv), (2 * R * math.sin(math.pi / k) + 1, THICK, R - 16),
               self.top if i % 2 else self.body, self.top_mat, rig, collide=True)

    def spin_deck(self, b, rig, c, L, w):
        Pt(b, "SpinDeck", (sub(c, (0, 3, 0))), (L, 6, w), self.top, self.top_mat, rig, collide=True)
        for s in (-1, 1):
            Pt(b, "Trim", (add(c, (0, 0.15, s * (w / 2 - 0.6)))), (L, 0.3, 1.2), self.edge, "Neon", rig)

    def spin_hub(self, b, c):
        cyl(b, "Hub", sub(c, (0, 12, 0)), 12, 22, self.body, self.body_mat)

    def cross_arm(self, b, rig, c, f, L, w):
        fr = deck_frame(c, f)
        Pt(b, "Arm", CF(sub(c, (0, 4, 0)), fr.x, fr.y, fr.z), (w, 8, L), self.top, self.top_mat, rig, collide=True)

    def log(self, b, rig, c, L, r):
        cyl(b, "Log", c, L, 2 * r, self.top, self.top_mat, rig, axis=(1, 0, 0), collide=True)
        for k in range(3):
            a = TAU * k / 3
            dv = (0, math.cos(a), math.sin(a))
            Pt(b, "Ridge", deck_frame(add(c, mul(dv, r + 1.2)), (1, 0, 0), up=dv), (5, 3, L - 10), self.danger, "Neon",
               rig, query=True, attrs={"ObbyHazard": "Knock"})

    def swing(self, b, rig, c, L, pivot):
        Pt(b, "SwingDeck", (sub(c, (0, 3, 0))), (L, 6, L), self.top, self.top_mat, rig, collide=True)
        for s in (-1, 1):
            a = (c[0], c[1], c[2] + s * (L / 2 - 3))
            self.rope(b, rig, a, (pivot[0], pivot[1], pivot[2] + s * (L / 2 - 3)), self.edge, "Neon", 0.8)

    def rope(self, b, rig, a, p, color, mat, d):
        mid = mul(add(a, p), 0.5)
        ax = unit(sub(p, a))
        cyl(b, "Rope", mid, math.dist(a, p), d, color, mat, rig, axis=ax)

    def swing_anchor(self, b, pivot, L):
        Pt(b, "Anchor", (pivot), (6, 3, L), self.body, self.body_mat)

    def piston(self, b, rig, c, bl, w, i, n):
        Pt(b, "PistonDeck", (sub(c, (0, 20, 0))), (bl, 40, w), self.top, self.top_mat, rig, collide=True)

    def press_frame(self, b, x, y, z, w, H):
        for s in (-1, 1):
            Pt(b, "PressRail", ((x, y + H / 2 + 12, z + s * (w / 2 + 3))), (4, H + 26, 4), self.body, self.body_mat, collide=True)
        Pt(b, "PressCap", ((x, y + H + 25, z)), (34, 4, w + 10), self.body, self.body_mat)

    def press(self, b, rig, rc, bl, w):
        Pt(b, "Press", rc, (bl, 18, w + 4), self.body, "Metal", rig, query=True, attrs={"ObbyHazard": "Crush"})
        Pt(b, "PressEdge", (add(rc, (0, -9.2, 0))), (bl + 0.4, 0.6, w + 4.4), self.danger, "Neon", rig)

    def door_panel(self, b, rig, c, w):
        Pt(b, "DoorPanel", (add(c, (0, 9, 0))), (5, 18, w), self.danger, "Neon", rig, query=True, transp=0.3,
           attrs={"ObbyHazard": "Knock"})

    def door_frame(self, b, x, y, z, w):
        Pt(b, "DoorFrame", ((x, y + 20, z)), (6, 2, w + 8), self.edge, "Neon")

    def gate(self, b, x, y, z, w, beams, attrs, i):
        for s in (-1, 1):
            Pt(b, "GatePost", ((x, y + 18, z + s * (w / 2 + 2))), (3, 36, 3), self.body, self.body_mat, collide=True)
        Pt(b, "GateTop", ((x, y + 36.5, z)), (3, 1.5, w + 7), self.edge, "Neon")
        self.beams(b, x, y, z, w, beams, attrs, self.danger)

    def beams(self, b, x, y, z, w, beams, attrs, color):
        for (hy, th) in beams:
            Pt(b, "Laser", ((x, y + hy, z)), (1.2, th, w + 2), color, "Neon", b.hazards, query=True, transp=0.1,
               attrs=attrs)

    def crumble_tile(self, b, m, c, s, i):
        Pt(b, "Tile", (sub(c, (0, 3, 0))), (s, 6, s), self.top, self.top_mat, m, collide=True)

    def belt(self, b, c, L, w, side, sp):
        Pt(b, "Belt", (sub(c, (0, 4, 0))), (L, 8, w), self.body, self.body_mat, collide=True,
           attrs={"Conveyor": float(sp), "ConveyorDir": ("Vector3", 0.0, 0.0, float(side))})
        for k in range(2):
            V2.chevron(b, (c[0] - L / 2 + L * (0.3 + 0.4 * k), c[1] + 0.3, c[2]), (0, 0, side), 12, self.padc)

    def bumper(self, b, c, rng):
        cyl(b, "Bumper", add(c, (0, 5, 0)), 10, 16, self.danger, "Neon", b.hazards, query=True,
            attrs={"ObbyHazard": "Knock"})

    def rink_tile(self, b, c, cell):
        Pt(b, "Ice", (sub(c, (0, 4, 0))), (cell - 1, 8, cell - 1), (200, 230, 255), "Ice", collide=True, refl=0.1)

    def rink_rim(self, b, x0, x1, y, z, w):
        pass

    # ------------------------------------------------------------ stunts
    def ribbon(self, b, pts, w, m):
        V2.ribbon(b, pts, w, m, color=self.top)

    def loop_deco(self, b, c, R, w):
        ringz(b, c, R + 9, self.edge, "Neon", th=2.0, axis=(0, 0, 1), name="Halo")

    def pipe_wall(self, b, m, cf, size, i, k):
        floor_ = i in (0, 1, k - 1)
        Pt(b, "PipeWall", cf, size, self.top if floor_ else self.glass, self.top_mat if floor_ else "Glass", m,
           collide=True, transp=0.0 if floor_ else 0.45)

    def pipe_rings(self, b, x0, L, ay, z, R):
        n = int(L // 45)
        for r in range(n + 1):
            ringz(b, (x0 + r * L / n, ay, z), R + 2.5, self.edge, "Neon", th=2.0, axis=(1, 0, 0), name="PipeRing")

    def pipe_blocker(self, b, c, a):
        Pt(b, "Blocker", CF(c) * rot_axis((1, 0, 0), -a), (10, 10, 26), self.danger, "Neon", b.hazards, query=True,
           attrs={"ObbyHazard": "Knock"})

    def tower(self, b, c, ylo, yhi):
        cyl(b, "Tower", (c[0], (ylo + yhi) / 2, c[2]), yhi - ylo, 34, self.body, self.body_mat, collide=True)

    # ------------------------------------------------------------ level dressing
    def finish(self, b, x0, x1, y, z, w):
        """A chequered strip across the join deck."""
        q = 8.0
        n = int(w // q)
        for row in range(2):
            for j in range(n):
                col = self.finish_cols[(row + j) % 2]
                Pt(b, "FinishSquare", ((x1 - 46 + row * q, y + 0.04, z - n * q / 2 + q * (j + 0.5))), (q, 0.08, q), col)

    def environment(self, b):
        pass


# ===================================================================== 1. Sugar Rush (candy)
class SugarRush(Skin):
    theme_name = "Candy land"
    key, title = "candy", "Sugar Rush"
    clock, bloom, hue, scale = 14.2, 0.3, 0.93, 1.0
    body, top, edge, padc, danger = (255, 150, 190), (255, 238, 244), (255, 255, 255), (80, 225, 200), (235, 40, 70)
    gate_post, gate_board, gate_text = (255, 255, 255), (255, 120, 170), (255, 255, 255)
    finish_cols = ((255, 255, 255), (255, 110, 160))
    CHOC, CHOC_LT, PINK, MINT = (88, 52, 34), (122, 78, 50), (255, 140, 185), (120, 230, 200)
    PASTEL = [(255, 140, 185), (120, 220, 200), (255, 215, 110), (170, 150, 255), (255, 170, 120)]
    recipe = [("hops", "Gumdrop climb", {"layout": "rising", "n": 3}), ("sweepers", "Candy-cane sweepers", {}),
              ("turntable", "Lollipop turntable", {}), ("loop", "Frosted donut loop", {}),
              ("belts", "Licorice conveyors", {}), ("crumble", "Chocolate crumble", {}),
              ("hops", "Cupcake wave", {"layout": "wave", "plat": None})]
    extra = [("hops", "Macaron hops", {"layout": "straight"})]
    light_over = {"Lt_Atmosphere_Color": ("Color3", 1.0, 0.86, 0.92), "Lt_CC_Saturation": 0.28}

    def __init__(self):
        self.recipe = [(k, l, dict(kw, plat=self.cupcake) if "plat" in kw else kw) for k, l, kw in self.recipe]
        self.extra = [(k, l, dict(kw, plat=self.macaron)) for k, l, kw in self.extra]

    def under(self, b, top, w, i):
        """A striped candy stick with a gumdrop on its end."""
        x, y, z = top
        for k in range(10):
            cyl(b, "CandyStick", (x, y - 3 - k * 6, z), 6.05, 7, (255, 255, 255) if k % 2 else self.PASTEL[i % 5])
        ell(b, "StickDrop", (x, y - 66, z), (16, 13, 16), self.PASTEL[(i + 2) % 5], "Glass", transp=0.1)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        Pt(b, "ChocBase", ((cx, y - 5.5, z)), (L, 3, w), self.CHOC, collide=True)
        n = max(1, int(round(L / 20)))
        q = L / n
        for i in range(n):
            for j in (-1, 1):
                c = (x0 + q * (i + 0.5), y - 2, z + j * w / 4)
                Pt(b, "Choc", (c), (q - 2.2, 4, w / 2 - 2.2), self.CHOC, refl=0.04)
                Pt(b, "ChocShine", (add(c, (0, 2.02, 0))), (q - 5, 0.05, w / 2 - 5), self.CHOC_LT)
        # the foil wrapper on the underside and the strawberry icing dripping off both edges
        Pt(b, "Wrapper", ((cx, y - 8.5, z)), (L, 5, w + 1.4), (240, 70, 130), "Foil", refl=0.1)
        Pt(b, "WrapperFoil", ((cx, y - 6.2, z)), (L, 0.6, w + 1.6), (235, 205, 130), "Foil", refl=0.2)
        for s in (-1, 1):
            Pt(b, "Icing", ((cx, y + 0.1, z + s * (w / 2 - 1.2))), (L, 0.5, 2.6), self.PINK)
            k = 0
            xx = x0 + 6
            while xx < x1 - 4:
                hgt = 3.5 + 2.5 * ((k * 7) % 3) / 2
                ell(b, "Drip", (xx, y - hgt / 2 + 0.2, z + s * (w / 2 + 0.2)), (4.2, hgt + 1.5, 1.6), self.PINK)
                k += 1
                xx += 13
        samples(b, x0, x1, y, z, w)

    def gumdrop(self, b, top, s, rng):
        col = rng.choice(self.PASTEL)
        ell(b, "Gumdrop", sub(top, (0, s * 0.42, 0)), (s * 1.05, s * 0.86, s * 1.05), col, "Glass", transp=0.12)
        ell(b, "GumdropCore", sub(top, (0, s * 0.44, 0)), (s * 0.8, s * 0.7, s * 0.8), mix(col, (255, 255, 255), 0.25))
        for k in range(14):
            a = rng.random() * TAU
            r = rng.uniform(0.08, 0.46) * s
            hh = s * 0.43 * math.sqrt(max(0.0, 1 - (r / (s * 0.525)) ** 2))
            ball(b, "Sugar", (top[0] + math.cos(a) * r, top[1] - s * 0.42 + hh + 0.2, top[2] + math.sin(a) * r), 1.4,
                 (255, 255, 255), "Glass")
        floor(b, top, s * 0.72, round_=True)
        b.samples.append((top[0], top[1], top[2], s))

    def cupcake(self, b, top, s, rng, parent=None):
        x, y, z = top
        col = rng.choice(self.PASTEL)
        cyl(b, "Liner", (x, y - 15, z), 18, s * 0.78, (250, 250, 250))
        for k in range(18):
            a = TAU * k / 18
            box(b, "Pleat", (x + math.cos(a) * s * 0.39, y - 15, z + math.sin(a) * s * 0.39), (2.0, 18, s * 0.12),
                col, yaw=-a)
        cyl(b, "Cake", (x, y - 5, z), 4, s * 0.86, (214, 160, 100))
        for i, (dy, dd) in enumerate(((-2.2, 1.0), (-0.9, 0.86), (0.0, 0.7))):
            cyl(b, "Frosting", (x, y + dy - 0.6, z), 1.6, s * dd, mix(col, (255, 255, 255), 0.55 + 0.1 * i), collide=(i == 0))
        for k in range(16):
            a = rng.random() * TAU
            r = rng.uniform(0.1, 0.4) * s
            box(b, "Sprinkle", (x + math.cos(a) * r, y + 0.1, z + math.sin(a) * r), (2.2, 0.3, 0.7),
                rng.choice(self.PASTEL), yaw=rng.random() * 3)
        floor(b, top, s * 0.8, round_=True)
        b.samples.append((x, y, z, s))

    def macaron(self, b, top, s, rng, parent=None):
        x, y, z = top
        col = rng.choice(self.PASTEL)
        ell(b, "Shell", (x, y - 4, z), (s, 8, s), col)
        cyl(b, "Foot", (x, y - 8.5, z), 2, s * 0.98, mix(col, (255, 255, 255), 0.35), "Sand")
        cyl(b, "Cream", (x, y - 11, z), 3, s * 0.9, (255, 250, 240))
        cyl(b, "Foot", (x, y - 13.5, z), 2, s * 0.98, mix(col, (255, 255, 255), 0.35), "Sand")
        ell(b, "Shell", (x, y - 16, z), (s, 6, s), col)
        floor(b, top, s * 0.8, round_=True)
        b.samples.append((x, y, z, s))

    def plat(self, b, top, s, rng, parent=None):
        self.gumdrop(b, top, s, rng)

    def finale_plat(self, b, top, s, rng):
        self.cupcake(b, top, s, rng)

    def tower_plat(self, b, top, s, rng):
        self.macaron(b, top, s, rng)

    def island(self, b, c, s, rng):
        """A giant chocolate-chip cookie."""
        x, y, z = c
        cyl(b, "Cookie", (x, y - 4, z), 8, s, (206, 150, 86), "Sand", collide=True)
        cyl(b, "CookieEdge", (x, y - 4, z), 6, s + 2, (180, 120, 64), "Sand")
        for k in range(18):
            a = rng.random() * TAU
            r = rng.uniform(0.08, 0.44) * s
            ell(b, "Chip", (x + math.cos(a) * r, y + 0.1, z + math.sin(a) * r), (4.5, 1.2, 4.5), self.CHOC)
        b.samples.append((x, y, z, s))

    def hub(self, b, c, d):
        cyl(b, "Hub", sub(c, (0, 4, 0)), 8, d, (255, 255, 255), collide=True)
        for k in range(1, 4):
            ringz(b, (c[0], c[1] + 0.05, c[2]), d * 0.5 * k / 4, self.PASTEL[k], "SmoothPlastic", th=0.2)

    def sweeper(self, b, rig, c, s, low):
        """A candy cane: red stick with white bands, hooked at one end."""
        h = 3.4 if low else 7.5
        d = 3.0 if low else 7.0
        p = add(c, (0, h, 0))
        cyl(b, "Cane", p, s - 8, d, (225, 30, 50), "SmoothPlastic", rig, axis=(1, 0, 0), query=True, refl=0.08,
            attrs={"ObbyHazard": "Burn" if low else "Knock"})
        n = int((s - 8) // 6)
        for k in range(n):
            cyl(b, "CaneStripe", add(p, (-(s - 8) / 2 + 3 + k * 6, 0, 0)), 2.4, d + 0.25, (255, 255, 255), "SmoothPlastic",
                rig, axis=unit((1, 0.35, 0)))
        end = add(p, ((s - 8) / 2, 0, 0))
        for k in range(1, 7):
            a = math.pi * k / 6
            q = add(end, (math.sin(a) * d * 1.6, d * 1.6 - math.cos(a) * d * 1.6, 0))
            ball(b, "CaneHook", q, d * 1.02, (225, 30, 50) if k % 2 else (255, 255, 255), "SmoothPlastic", rig)

    def turntable(self, b, rig, c, R, k, holes):
        """A swirl lollipop: alternating pastel sectors, a stick hanging under it."""
        for i in range(k):
            if i in holes:
                continue
            a = TAU * (i + 0.5) / k
            dv = (math.cos(a), 0, math.sin(a))
            mid = add(c, mul(dv, R / 2 + 8))
            col = self.PASTEL[i % len(self.PASTEL)]
            Pt(b, "Sector", deck_frame(sub(mid, (0, 2.5, 0)), dv), (2 * R * math.sin(math.pi / k) + 1, 5, R - 16), col,
               "SmoothPlastic", rig, collide=True, refl=0.12)
            Pt(b, "SectorSwirl", deck_frame(add(mid, (0, 0.04, 0)), dv) * rot_y(0.5),
               (2.5, 0.08, R - 22), (255, 255, 255), "SmoothPlastic", rig)
        cyl(b, "Stick", sub(c, (0, 60, 0)), 110, 6, (255, 255, 255), "SmoothPlastic")
        ringz(b, sub(c, (0, 0.5, 0)), R + 0.6, (255, 255, 255), "SmoothPlastic", th=4.0, parent=rig, name="LollyRim")

    def belt(self, b, c, L, w, side, sp):
        Pt(b, "Belt", (sub(c, (0, 3, 0))), (L, 6, w), (34, 22, 28), "SmoothPlastic", collide=True, refl=0.12,
           attrs={"Conveyor": float(sp), "ConveyorDir": ("Vector3", 0.0, 0.0, float(side))})
        for s in (-1, 1):
            cyl(b, "Licorice", (c[0], c[1] - 1.5, c[2] + s * (w / 2 + 2)), L, 4.5, (200, 25, 45), axis=(1, 0, 0), refl=0.1)
            for k in range(int(L // 8)):
                cyl(b, "Twist", (c[0] - L / 2 + 4 + k * 8, c[1] - 1.5, c[2] + s * (w / 2 + 2)), 1.0, 4.9, (150, 15, 30),
                    axis=unit((1, 0.6, 0)))
        for k in range(3):
            V2.chevron(b, (c[0] - L / 2 + L * (0.2 + 0.3 * k), c[1] + 0.05, c[2]), (0, 0, side), 12, (255, 255, 255))
        for ch in b.roads.children[-6:]:
            if ch.name == "Chevron":
                ch.set("Material", 272)

    def crumble_tile(self, b, m, c, s, i):
        col = self.CHOC if i % 2 == 0 else (240, 228, 205)
        Pt(b, "Tile", (sub(c, (0, 2.5, 0))), (s - 1, 5, s - 1), col, "SmoothPlastic", m, collide=True, refl=0.05)
        Pt(b, "TileShine", (add(c, (0, 0.03, 0))), (s - 5, 0.06, s - 5), mix(col, (255, 255, 255), 0.18), "SmoothPlastic", m)

    def pad_art(self, b, start, f):
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        Pt(b, "PadPlate", fr, (30, 0.2, 26), (255, 255, 255))
        for k in range(5):
            Pt(b, "PadStripe", fr * CF((-12 + k * 6, 0.06, 0)) * rot_y(0.5), (2.2, 0.1, 26), (255, 120, 170))
        for k in range(3):
            V2.chevron(b, add(start, add(mul(f, -7 + k * 7), (0, 0.25, 0))), f, 14, self.padc)

    def hoop(self, b, c, axis, r):
        ringz(b, c, r, (255, 120, 175), "SmoothPlastic", th=4.0, axis=axis, name="Hoop")
        ringz(b, c, r - 1.4, (255, 255, 255), "Neon", th=1.0, axis=axis, name="HoopGlow")

    def ribbon(self, b, pts, w, m):
        V2.ribbon(b, pts, w, m, color=(255, 160, 200))

    def loop_deco(self, b, c, R, w):
        """A giant frosted donut round the loop: a ring of round dough segments, pink icing on the front."""
        Rc, rt = R + 17, 11.0
        n = 30
        rng = random.Random(int(c[0]))
        for k in range(n):
            a = TAU * (k + 0.5) / n
            p = (c[0] + Rc * math.cos(a), c[1] + Rc * math.sin(a), c[2])
            tang = (-math.sin(a), math.cos(a), 0.0)
            seg = TAU * Rc / n + 1.2
            cyl(b, "Donut", p, seg, 2 * rt, (214, 150, 80), "Sand", axis=tang)
            cyl(b, "Icing", add(p, (0, 0, 2.6)), seg, 2 * rt - 1.0, (255, 140, 190), axis=tang)
        for k in range(70):
            a = rng.random() * TAU
            ph = rng.uniform(-1.0, 1.0)
            rr = Rc + (rt - 0.2) * math.sin(ph)
            p = (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a), c[2] + 2.6 + (rt - 0.5) * math.cos(ph))
            box(b, "Sprinkle", p, (3.2, 0.9, 0.9), rng.choice(self.PASTEL[1:] + [(255, 255, 255)]), yaw=rng.random() * 3)


# ===================================================================== 2. Drive Thru (diner)
class DriveThru(Skin):
    theme_name = "50s diner"
    key, title = "diner", "Drive Thru"
    clock, bloom, hue, scale = 15.6, 0.35, 0.02, 1.0
    body, top, edge, padc, danger = (205, 30, 42), (246, 246, 242), (214, 220, 230), (255, 200, 40), (230, 40, 30)
    gate_post, gate_board, gate_text = (214, 220, 230), (205, 30, 42), (255, 220, 70)
    CHROME, RED, BLACK = (214, 220, 230), (205, 30, 42), (28, 28, 32)
    recipe = [("hops", "Burger & fries hops", {"layout": "lanes", "n": 3}), ("gates", "Ketchup & mustard gates", {}),
              ("log", "Rolling pickle", {}), ("swings", "Swinging spatulas", {}), ("crushers", "Burger presses", {}),
              ("tower", "Milkshake tower", {}), ("belts", "Grill conveyors", {})]
    extra = [("hops", "Fry box hops", {"layout": "straight"})]

    def under(self, b, top, w, i):
        """A chrome diner-table pedestal."""
        x, y, z = top
        cyl(b, "Pedestal", (x, y - 30, z), 56, 5, self.CHROME, "Metal", refl=0.35)
        cyl(b, "PedestalCollar", (x, y - 3, z), 4, 12, self.CHROME, "Metal", refl=0.35)
        cone(b, "PedestalFoot", (x, y - 62, z), 6, 26, self.CHROME, "Metal", n=3, refl=0.35)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        Pt(b, "Deck", ((cx, y - 0.5, z)), (L, 1, w), (246, 246, 242), "SmoothPlastic", collide=True, refl=0.06)
        q = w / 4
        n = max(1, int(round(L / q)))
        qx = L / n
        for i in range(n):
            for j in range(4):
                if (i + j) % 2:
                    Pt(b, "Tile", ((x0 + qx * (i + 0.5), y + 0.01, z - w / 2 + q * (j + 0.5))), (qx, 0.04, q), self.BLACK,
                       refl=0.06)
        Pt(b, "Vinyl", ((cx, y - 4.5, z)), (L, 7, w + 0.6), self.RED, "Fabric")
        for s in (-1, 1):
            Pt(b, "Chrome", ((cx, y - 0.8, z + s * (w / 2 + 0.6))), (L, 1.8, 1.4), self.CHROME, "Metal", refl=0.35)
            Pt(b, "Chrome", ((cx, y - 7.6, z + s * (w / 2 + 0.4))), (L, 1.0, 1.0), self.CHROME, "Metal", refl=0.35)
        samples(b, x0, x1, y, z, w)

    def burger(self, b, top, s, rng):
        x, y, z = top
        cyl(b, "BunBottom", (x, y - 27, z), 6, s * 0.9, (205, 140, 62))
        cyl(b, "Patty", (x, y - 21.5, z), 6, s * 0.98, (84, 48, 28), "Sand")
        for k in range(4):
            a = TAU * k / 4 + 0.4
            Pt(b, "CheeseDrip", CF((x + math.cos(a) * s * 0.47, y - 19.5, z + math.sin(a) * s * 0.47)) * rot_y(-a),
               (1.0, 5, s * 0.2), (255, 196, 30))
        Pt(b, "Cheese", CF((x, y - 18, z)) * rot_y(math.pi / 4), (s * 0.84, 1.2, s * 0.84), (255, 200, 40))
        for k in range(14):
            a = TAU * k / 14
            ell(b, "Lettuce", (x + math.cos(a) * s * 0.48, y - 16.5, z + math.sin(a) * s * 0.48), (s * 0.3, 1.8, s * 0.16),
                (100, 200, 70), rot=rot_y(-a))
        cyl(b, "Tomato", (x, y - 15, z), 2, s * 0.88, (225, 50, 40))
        ell(b, "BunTop", (x, y - 13, z), (s * 0.98, 26, s * 0.98), (210, 145, 66))
        for k in range(16):
            a = rng.random() * TAU
            r = rng.uniform(0.08, 0.42) * s
            hh = 13 * math.sqrt(max(0.0, 1 - (r / (s * 0.49)) ** 2))
            ell(b, "Sesame", (x + math.cos(a) * r, y - 13 + hh + 0.1, z + math.sin(a) * r), (1.6, 0.6, 1.0),
                (250, 240, 210), rot=rot_y(rng.random() * 3))
        floor(b, top, s * 0.72, round_=True)
        b.samples.append(top + (s,))

    def frybox(self, b, top, s, rng):
        x, y, z = top
        Pt(b, "FryBox", ((x, y - 14, z)), (s * 0.8, 24, s * 0.6), self.RED, collide=True)
        Pt(b, "FryBoxBand", ((x, y - 22, z)), (s * 0.82, 3, s * 0.62), (255, 210, 60))
        for i in range(int(s * 0.8 // 3.2)):
            for j in range(int(s * 0.6 // 3.2)):
                e = ((i * 7 + j * 3) % 5) * 0.2
                Pt(b, "Fry", ((x - s * 0.4 + 1.6 + i * 3.2, y - 3 + e / 2, z - s * 0.3 + 1.6 + j * 3.2)),
                   (2.4, 6 + e, 2.4), (250, 205, 90) if (i + j) % 3 else (235, 180, 70), "Sand")
        floor(b, top, s * 0.8, s * 0.6)
        b.samples.append(top + (s * 0.6,))

    def plat(self, b, top, s, rng, parent=None):
        (self.burger if rng.random() < 0.6 else self.frybox)(b, top, s, rng)

    def pad_art(self, b, start, f):
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        Pt(b, "PadPlate", fr, (30, 0.2, 26), self.RED, "SmoothPlastic")
        Pt(b, "PadPaper", fr * CF((0, 0.05, 0)), (24, 0.1, 22), (255, 246, 228))
        for k in range(3):
            V2.chevron(b, add(start, add(mul(f, -7 + k * 7), (0, 0.3, 0))), f, 14, self.padc)

    def hoop(self, b, c, axis, r):
        """Onion rings."""
        ringz(b, c, r, (214, 150, 60), "Sand", th=5.0, axis=axis, name="OnionRing")
        ringz(b, c, r - 1.5, (240, 200, 120), "SmoothPlastic", th=3.0, axis=axis, name="OnionRingIn")

    def gate(self, b, x, y, z, w, beams, attrs, i):
        """A ketchup bottle on one side, mustard on the other, squirting across the lane."""
        sauce = (220, 30, 30) if i % 2 == 0 else (255, 205, 30)
        for s, col in ((-1, (210, 25, 30)), (1, (255, 200, 30))):
            bx = (x, y, z + s * (w / 2 + 5))
            cyl(b, "Bottle", add(bx, (0, 15, 0)), 30, 9, col, collide=True, refl=0.1)
            cyl(b, "Shoulder", add(bx, (0, 31.5, 0)), 3, 7, col)
            cyl(b, "Cap", add(bx, (0, 34.5, 0)), 3, 5, (250, 250, 250))
            cone(b, "Nozzle", add(bx, (0, 36, 0)), 4, 3, (250, 250, 250), n=3)
            Pt(b, "Label", ((x, y + 15, z + s * (w / 2 + 0.45))), (6.5, 9, 0.1), (255, 255, 255))
        self.beams(b, x, y, z, w, beams, attrs, sauce)

    def log(self, b, rig, c, L, r):
        """A pickle."""
        green, dark = (110, 160, 50), (70, 112, 30)
        cyl(b, "Pickle", c, L, 2 * r, green, "SmoothPlastic", rig, axis=(1, 0, 0), collide=True, refl=0.06)
        for e in (-1, 1):
            ell(b, "PickleEnd", add(c, (e * L / 2, 0, 0)), (12, 2 * r, 2 * r), green, parent=rig)
        rng = random.Random(int(c[0]))
        for k in range(40):
            a = rng.random() * TAU
            dv = (0, math.cos(a), math.sin(a))
            ell(b, "Wart", add(add(c, (rng.uniform(-L / 2 + 8, L / 2 - 8), 0, 0)), mul(dv, r)), (3, 1.6, 3), dark,
                parent=rig, rot=deck_frame((0, 0, 0), (1, 0, 0), up=dv))
        for k in range(3):
            a = TAU * k / 3
            dv = (0, math.cos(a), math.sin(a))
            Pt(b, "Ridge", deck_frame(add(c, mul(dv, r + 1.2)), (1, 0, 0), up=dv), (5, 3, L - 10), dark, "SmoothPlastic",
               rig, query=True, attrs={"ObbyHazard": "Knock"})

    def swing(self, b, rig, c, L, pivot):
        """A spatula hanging by its handle."""
        Pt(b, "SwingDeck", (sub(c, (0, 1.2, 0))), (L, 2.4, L * 0.9), (200, 205, 212), "Metal", rig, collide=True, refl=0.25)
        for k in range(4):
            Pt(b, "Slot", (add(c, (-L * 0.3 + k * L * 0.2, 0.03, 0))), (2.0, 0.06, L * 0.55), (70, 72, 78), parent=rig)
        a = (c[0], c[1] + 2, c[2] - L * 0.45)
        neck = (c[0], c[1] + 10, c[2] - L * 0.45 - 4)
        self.rope(b, rig, a, neck, (200, 205, 212), "Metal", 3.0)
        self.rope(b, rig, neck, pivot, (40, 40, 44), "SmoothPlastic", 4.0)
        ball(b, "HandleEnd", pivot, 5, (40, 40, 44), parent=rig)

    def swing_anchor(self, b, pivot, L):
        cyl(b, "Rail", pivot, L + 10, 3, self.CHROME, "Metal", axis=(1, 0, 0), refl=0.35)
        for s in (-1, 1):
            ball(b, "RailCap", add(pivot, (s * (L / 2 + 5), 0, 0)), 5, self.RED)

    def tower(self, b, c, ylo, yhi):
        """A giant strawberry milkshake."""
        x, z = c[0], c[2]
        H = yhi - ylo
        cyl(b, "Foot", (x, ylo + 3, z), 6, 34, (230, 236, 245), "Glass", transp=0.3)
        cyl(b, "Stem", (x, ylo + 20, z), 30, 10, (230, 236, 245), "Glass", transp=0.3)
        cup0 = ylo + 34
        cupH = H - 70
        for k in range(6):
            t = (k + 0.5) / 6
            cyl(b, "Cup", (x, cup0 + cupH * t, z), cupH / 6 + 0.1, 30 + 14 * t, (230, 240, 250), "Glass", transp=0.55,
                collide=(k == 0))
            cyl(b, "Shake", (x, cup0 + cupH * t, z), cupH / 6 + 0.1, 27 + 14 * t, (255, 160, 190))
        for k, (dy, dd) in enumerate(((4, 46), (12, 38), (19, 28), (25, 18))):
            ell(b, "Cream", (x, cup0 + cupH + dy, z), (dd, 12, dd), (255, 252, 246))
        ball(b, "Cherry", (x, cup0 + cupH + 35, z), 10, (210, 20, 40), refl=0.2)
        a = (x + 6, cup0 + cupH - 30, z + 4)
        p = (x + 18, cup0 + cupH + 50, z + 10)
        ax = unit(sub(p, a))
        Ls = math.dist(a, p)
        for k in range(10):
            cyl(b, "Straw", add(a, mul(ax, Ls * (k + 0.5) / 10)), Ls / 10 + 0.05, 4,
                (230, 30, 50) if k % 2 else (255, 255, 255), axis=ax)

    def tower_plat(self, b, top, s, rng):
        self.burger(b, top, s, rng)

    def belt(self, b, c, L, w, side, sp):
        """A grill belt: dark bars over a glow."""
        Pt(b, "Belt", (sub(c, (0, 3, 0))), (L, 6, w), (46, 46, 50), "Metal", collide=True,
           attrs={"Conveyor": float(sp), "ConveyorDir": ("Vector3", 0.0, 0.0, float(side))})
        for k in range(int(L // 5)):
            Pt(b, "GrillBar", ((c[0] - L / 2 + 2.5 + k * 5, c[1] + 0.05, c[2])), (1.2, 0.1, w - 2), (20, 20, 22), "Metal")
        Pt(b, "Glow", (sub(c, (0, 6.5, 0))), (L * 0.9, 1, w * 0.8), (255, 120, 30), "Neon", transp=0.2)
        for k in range(2):
            V2.chevron(b, (c[0] - L / 2 + L * (0.3 + 0.4 * k), c[1] + 0.3, c[2]), (0, 0, side), 12, self.padc)
        for s in (-1, 1):
            Pt(b, "Chrome", ((c[0], c[1] - 1, c[2] + s * (w / 2 + 0.6))), (L, 2, 1.2), self.CHROME, "Metal", refl=0.35)

    def press_frame(self, b, x, y, z, w, H):
        for s in (-1, 1):
            cyl(b, "PressRail", (x, y + H / 2 + 12, z + s * (w / 2 + 3)), H + 26, 4, self.CHROME, "Metal", collide=True,
                refl=0.35)
        Pt(b, "PressCap", ((x, y + H + 25, z)), (34, 5, w + 12), self.RED)
        Pt(b, "PressCapTrim", ((x, y + H + 22.4, z)), (34.4, 0.6, w + 12.4), self.CHROME, "Metal", refl=0.35)

    def press(self, b, rig, rc, bl, w):
        Pt(b, "Press", rc, (bl, 18, w + 4), (58, 58, 62), "Metal", rig, query=True, attrs={"ObbyHazard": "Crush"})
        for k in range(5):
            Pt(b, "GrillMark", (add(rc, (-bl / 2 + 4 + k * (bl - 8) / 4, -9.05, 0))), (1.4, 0.1, w + 2), (24, 24, 26),
               parent=rig)
        cyl(b, "Handle", add(rc, (0, 11, 0)), 4, 6, self.RED, parent=rig)
        Pt(b, "PressEdge", (add(rc, (0, -8.6, 0))), (bl + 0.4, 0.8, w + 4.4), (255, 120, 30), "Neon", rig)


# ===================================================================== 3. Spore Springs (glowing mushroom forest at dusk)
class SporeSprings(Skin):
    theme_name = "Glowing mushroom forest"
    key, title = "mushroom", "Spore Springs"
    clock, bloom, hue, scale = 18.4, 0.85, 0.78, 1.0
    body, top, edge, padc, danger = (236, 226, 200), (190, 40, 50), (120, 255, 210), (190, 130, 255), (255, 90, 60)
    gate_post, gate_board, gate_text = (110, 76, 50), (60, 40, 30), (150, 255, 210)
    BARK, BARK_DK, WOOD, MOSS = (104, 72, 48), (74, 50, 34), (205, 165, 110), (84, 140, 58)
    GLOW = [(120, 255, 210), (190, 130, 255), (110, 200, 255)]
    recipe = [("hops", "Toadstool hops", {"layout": "straight", "n": 3}), ("pipe", "Hollow log", {}),
              ("swings", "Swinging leaves", {}), ("tower", "Giant mushroom climb", {}),
              ("drop", "Spore-ring drop", {}), ("bumpers", "Puffball field", {}),
              ("spin_bridges", "Spinning bark bridges", {})]
    extra = [("hops", "Toadstool wave", {"layout": "wave"})]
    light_over = {"Lt_Atmosphere_Color": ("Color3", 0.62, 0.5, 0.82), "Lt_Lighting_Brightness": 2.2}

    def under(self, b, top, w, i):
        """Roots and glowing vines hanging off the log."""
        x, y, z = top
        for k, (dz, ln) in enumerate(((-w * 0.25, 34), (0, 52), (w * 0.22, 26))):
            cyl(b, "Vine", (x + k * 4 - 4, y - w * 0.4 - ln / 2, z + dz), ln, 1.4, (60, 100, 44))
            ball(b, "VineBulb", (x + k * 4 - 4, y - w * 0.4 - ln, z + dz), 3.2, self.GLOW[(i + k) % 3], "Neon")

    def deck(self, b, x0, x1, y, z, w, parent=None):
        """A mossy fallen log."""
        L, cx = x1 - x0, (x0 + x1) / 2
        d = w * 0.95
        cy = y - d / 2 + 0.3
        cyl(b, "Log", (cx, cy, z), L, d, self.BARK, "Wood", axis=(1, 0, 0))
        Pt(b, "Moss", ((cx, y + 0.05, z)), (L, 0.5, w * 0.62), self.MOSS, "Grass")
        for k in range(int(L // 36) + 1):
            cyl(b, "BarkRing", (x0 + 14 + k * 36, cy, z), 2.4, d + 0.8, self.BARK_DK, "Wood", axis=(1, 0, 0))
        for e in (x0, x1):
            cyl(b, "LogEnd", (e, cy, z), 0.8, d * 0.94, self.WOOD, "Wood", axis=(1, 0, 0))
            for r in (0.7, 0.45, 0.2):
                ringz(b, (e + (0.45 if e == x1 else -0.45), cy, z), d * r * 0.5, self.BARK, "Wood", th=0.4, axis=(1, 0, 0))
        k = 0
        xx = x0 + 22
        while xx < x1 - 10:
            s = 1 if k % 2 == 0 else -1
            col = self.GLOW[k % 3]
            for j in range(3):
                mx = xx + (j - 1) * 3.5
                my = cy + d * 0.18 - j * 1.5
                mz = z + s * (d * 0.47 + 0.5)
                cyl(b, "GlowStem", (mx, my, mz), 4, 1.2, (230, 230, 220))
                ell(b, "GlowCap", (mx, my + 2.4, mz), (4 - j * 0.6, 1.8, 4 - j * 0.6), col, "Neon")
            k += 1
            xx += 47
        samples(b, x0, x1, y, z, w)

    def toadstool(self, b, top, s, rng, parent=None):
        x, y, z = top
        glow = rng.random() < 0.35
        cap = rng.choice([(200, 36, 46), (220, 70, 40)]) if not glow else (70, 60, 150)
        cyl(b, "Stem", (x, y - s * 0.22 - 22, z), 44, s * 0.28, self.body)
        cyl(b, "Skirt", (x, y - s * 0.22 - 8, z), 2.5, s * 0.36, (250, 244, 228))
        cyl(b, "Gills", (x, y - s * 0.21, z), 1.0, s * 0.92, (240, 220, 190))
        ringz(b, (x, y - s * 0.22, z), s * 0.47, self.GLOW[rng.randrange(3)], "Neon", th=0.8, name="GillGlow")
        ell(b, "Cap", (x, y - s * 0.2, z), (s * 1.08, s * 0.42, s * 1.08), cap)
        for k in range(7):
            a = TAU * k / 7 + rng.random()
            r = s * rng.uniform(0.18, 0.4)
            h = s * 0.21 * math.sqrt(max(0.0, 1 - (r / (s * 0.54)) ** 2))
            ell(b, "Spot", (x + math.cos(a) * r, y - s * 0.2 + h + 0.15, z + math.sin(a) * r),
                (s * 0.13, s * 0.05, s * 0.13), (255, 255, 255) if not glow else self.GLOW[k % 3], "Neon" if glow else "SmoothPlastic")
        floor(b, top, s * 0.8, round_=True)
        b.samples.append(top + (s,))

    def plat(self, b, top, s, rng, parent=None):
        self.toadstool(b, top, s, rng)

    def hoop(self, b, c, axis, r):
        ringz(b, c, r, (140, 255, 200), "Neon", th=1.4, axis=axis, name="SporeRing")
        ax = unit(axis)
        a1 = unit(cross(ax, UP)) if abs(ax[1]) < 0.95 else (1, 0, 0)
        a2 = unit(cross(a1, ax))
        for k in range(8):
            t = TAU * k / 8
            ball(b, "Spore", add(c, add(mul(a1, math.cos(t) * r), mul(a2, math.sin(t) * r))), 2.6, self.GLOW[k % 3], "Neon")

    def pad_art(self, b, start, f):
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        cyl(b, "PadMoss", add(start, (0, 0.1, 0)), 0.2, 30, (60, 110, 46), "Grass")
        for k in range(3):
            V2.chevron(b, add(start, add(mul(f, -7 + k * 7), (0, 0.3, 0))), f, 14, self.padc)

    def pipe_wall(self, b, m, cf, size, i, k):
        top_ = i in (7, 8, 9)
        Pt(b, "PipeWall", cf, size, (150, 230, 190) if top_ else self.BARK, "Glass" if top_ else "Wood", m, collide=True,
           transp=0.6 if top_ else 0.0)

    def pipe_rings(self, b, x0, L, ay, z, R):
        n = int(L // 40)
        for r in range(n + 1):
            ringz(b, (x0 + r * L / n, ay, z), R + 4, self.BARK_DK, "Wood", th=4.0, axis=(1, 0, 0), name="BarkRing")
            ringz(b, (x0 + r * L / n, ay, z), R - 0.6, self.GLOW[r % 3], "Neon", th=0.6, axis=(1, 0, 0), name="GlowRing")
        for e in (x0, x0 + L):
            ringz(b, (e, ay, z), R + 2, self.WOOD, "Wood", th=1.0, axis=(1, 0, 0), name="LogRim")

    def pipe_blocker(self, b, c, a):
        Pt(b, "Blocker", CF(c) * rot_axis((1, 0, 0), -a), (10, 8, 22), (236, 226, 200), "SmoothPlastic", b.hazards,
           query=True, attrs={"ObbyHazard": "Knock"})
        up = (0, math.cos(a), -math.sin(a))
        ell(b, "BlockerCap", add(c, mul(up, 5)), (14, 5, 26), (70, 60, 150), rot=rot_axis((1, 0, 0), -a))

    def swing(self, b, rig, c, L, pivot):
        """A leaf on two vines."""
        Pt(b, "Floor", (sub(c, (0, 1, 0))), (L, 2, L * 0.8), (255, 255, 255), parent=rig, collide=True, transp=1.0)
        ell(b, "Leaf", sub(c, (0, 0.6, 0)), (L * 1.2, 1.6, L * 0.95), (70, 150, 60), parent=rig)
        Pt(b, "Midrib", (add(c, (0, 0.25, 0))), (L * 1.1, 0.3, 1.2), (150, 210, 110), parent=rig)
        for k in range(4):
            for s in (-1, 1):
                Pt(b, "Vein", CF(add(c, (-L * 0.32 + k * L * 0.2, 0.22, s * L * 0.16))) * rot_y(s * 0.6), (0.6, 0.2, L * 0.34),
                   (120, 190, 90), parent=rig)
        for s in (-1, 1):
            self.rope(b, rig, (c[0], c[1], c[2] + s * L * 0.4), (pivot[0], pivot[1], pivot[2] + s * 4), (60, 110, 40),
                      "SmoothPlastic", 1.4)

    def swing_anchor(self, b, pivot, L):
        cyl(b, "Branch", pivot, L + 24, 7, self.BARK, "Wood", axis=(1, 0, 0))
        for k in (-1, 1):
            ell(b, "BranchLeaf", add(pivot, (k * (L / 2 + 6), 3, 0)), (10, 2, 6), (80, 160, 70), rot=rot_y(0.5 * k))

    def tower(self, b, c, ylo, yhi):
        x, z = c[0], c[2]
        cyl(b, "Tower", (x, (ylo + yhi) / 2 - 10, z), yhi - ylo - 20, 32, self.body, collide=True)
        for k in range(6):
            cyl(b, "StemBand", (x, ylo + 30 + k * (yhi - ylo - 60) / 5, z), 2, 33, (250, 244, 228))
        cyl(b, "Gills", (x, yhi - 12, z), 2, 120, (240, 220, 190))
        ringz(b, (x, yhi - 13, z), 60, (190, 130, 255), "Neon", th=1.4, name="GillGlow")
        ell(b, "Cap", (x, yhi, z), (128, 50, 128), (90, 60, 170))
        for k in range(12):
            a = TAU * k / 12
            ell(b, "CapSpot", (x + math.cos(a) * 38, yhi + 14, z + math.sin(a) * 38), (12, 5, 12), self.GLOW[k % 3], "Neon")

    def bumper(self, b, c, rng):
        d = rng.uniform(14, 18)
        ball(b, "Puffball", add(c, (0, d / 2 - 1, 0)), d, (240, 232, 214), "SmoothPlastic", b.hazards, query=True,
             attrs={"ObbyHazard": "Knock"})
        for k in range(6):
            a = rng.random() * TAU
            ball(b, "Wart", add(c, (math.cos(a) * d * 0.3, d * 0.85, math.sin(a) * d * 0.3)), 1.6, (210, 196, 170))
        ringz(b, add(c, (0, 0.2, 0)), d * 0.6, self.GLOW[rng.randrange(3)], "Neon", th=0.5)

    def spin_deck(self, b, rig, c, L, w):
        Pt(b, "SpinDeck", (sub(c, (0, 3, 0))), (L, 6, w), self.WOOD, "WoodPlanks", rig, collide=True)
        Pt(b, "Moss", (add(c, (0, 0.04, 0))), (L - 4, 0.1, w * 0.4), self.MOSS, "Grass", rig)
        for s in (-1, 1):
            Pt(b, "Bark", (add(c, (0, -2, s * (w / 2 + 0.6)))), (L, 6, 1.4), self.BARK, "Wood", rig)

    def spin_hub(self, b, c):
        cyl(b, "Stump", sub(c, (0, 16, 0)), 24, 22, self.BARK, "Wood")
        for r in (0.4, 0.25):
            ringz(b, sub(c, (0, 3.9, 0)), 22 * r, self.BARK_DK, "Wood", th=0.3)


# ===================================================================== 4. Checkmate (chess)
class Checkmate(Skin):
    theme_name = "Chess board"
    key, title = "chess", "Checkmate"
    clock, bloom, hue, scale = 16.9, 0.35, 0.1, 0.95
    WHITE, BLACK, GOLD, WOOD = (242, 238, 228), (34, 32, 38), (232, 190, 90), (92, 56, 32)
    body, top, edge, padc, danger = (34, 32, 38), (242, 238, 228), (232, 190, 90), (232, 190, 90), (220, 50, 60)
    gate_post, gate_board, gate_text = (242, 238, 228), (34, 32, 38), (232, 190, 90)
    recipe = [("hops", "Rook hops", {"layout": "straight", "n": 3}), ("doors", "Sliding castle walls", {}),
              ("crushers", "Pawn crushers", {}), ("cross", "Rotating chessboard", {}),
              ("sweepers", "Sceptre sweepers", {}), ("hops", "Knight jumps", {"layout": "lanes"})]
    extra = [("hops", "Pawn steps", {"layout": "falling"})]
    hoop_mat = "Metal"

    def under(self, b, top, w, i):
        x, y, z = top
        cyl(b, "Column", (x, y - 36, z), 60, 9, self.WHITE, "Marble")
        cyl(b, "ColumnCap", (x, y - 5, z), 4, 14, self.WHITE, "Marble")
        ringz(b, (x, y - 7.2, z), 7, self.GOLD, "Metal", th=0.6)
        cyl(b, "ColumnFoot", (x, y - 67, z), 4, 13, self.WHITE, "Marble")

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        Pt(b, "Board", ((cx, y - 3, z)), (L, 6, w), self.WHITE, "Marble", collide=True)
        q = w / 4
        n = max(1, int(round(L / q)))
        qx = L / n
        for i in range(n):
            for j in range(4):
                if (i + j) % 2:
                    Pt(b, "Square", ((x0 + qx * (i + 0.5), y + 0.02, z - w / 2 + q * (j + 0.5))), (qx, 0.06, q), self.BLACK,
                       "Marble")
        for s in (-1, 1):
            Pt(b, "Frame", ((cx, y - 3.2, z + s * (w / 2 + 1.6))), (L, 7, 3.2), self.WOOD, "Wood")
            Pt(b, "Inlay", ((cx, y + 0.32, z + s * (w / 2 + 1.6))), (L, 0.1, 0.9), self.GOLD, "Metal", refl=0.3)
        samples(b, x0, x1, y, z, w)

    def rook(self, b, top, s, rng, col=None):
        x, y, z = top
        col = col or (self.WHITE if rng.random() < 0.5 else self.BLACK)
        cyl(b, "Base", (x, y - 46, z), 6, s * 1.08, col, "Marble")
        cyl(b, "BaseRing", (x, y - 42, z), 3, s * 0.96, col, "Marble")
        ringz(b, (x, y - 40.4, z), s * 0.46, self.GOLD, "Metal", th=0.8)
        cyl(b, "Body", (x, y - 28, z), 22, s * 0.74, col, "Marble")
        cyl(b, "BodyTop", (x, y - 13, z), 8, s * 0.8, col, "Marble")
        cyl(b, "Crown", (x, y - 4, z), 8, s * 0.98, col, "Marble", collide=True)
        for k in range(8):
            a = TAU * k / 8
            Pt(b, "Merlon", CF((x + math.cos(a) * s * 0.44, y + 2, z + math.sin(a) * s * 0.44)) * rot_y(-a),
               (s * 0.1, 4, s * 0.2), col, "Marble")
        ringz(b, (x, y - 8.3, z), s * 0.5, self.GOLD, "Metal", th=0.8)
        b.samples.append(top + (s,))

    def pawn(self, b, top, s, rng):
        x, y, z = top
        col = self.WHITE if rng.random() < 0.5 else self.BLACK
        cyl(b, "Base", (x, y - 40, z), 6, s * 1.05, col, "Marble")
        ell(b, "Body", (x, y - 22, z), (s * 0.6, 34, s * 0.6), col, "Marble")
        cyl(b, "Collar", (x, y - 7, z), 3, s * 0.8, col, "Marble")
        ell(b, "Head", (x, y - 1.5, z), (s * 0.92, 6, s * 0.92), col, "Marble")
        ringz(b, (x, y - 5.5, z), s * 0.4, self.GOLD, "Metal", th=0.8)
        floor(b, top, s * 0.8, round_=True)
        b.samples.append(top + (s,))

    def plat(self, b, top, s, rng, parent=None):
        self.rook(b, top, s, rng)

    def tower_plat(self, b, top, s, rng):
        self.pawn(b, top, s, rng)

    def finale_plat(self, b, top, s, rng):
        self.pawn(b, top, s, rng)

    def island(self, b, c, s, rng):
        x, y, z = c
        cyl(b, "Table", (x, y - 3, z), 6, s, self.WHITE, "Marble", collide=True)
        cyl(b, "TableRim", (x, y - 3.2, z), 5.6, s + 3, self.WOOD, "Wood")
        q = s / 7
        for i in range(7):
            for j in range(7):
                px, pz = (i - 3) * q, (j - 3) * q
                if (i + j) % 2 and math.hypot(px, pz) < s / 2 - q * 0.75:
                    Pt(b, "Square", ((x + px, y + 0.02, z + pz)), (q, 0.06, q), self.BLACK, "Marble")
        b.samples.append(c + (s,))

    def hub(self, b, c, d):
        cyl(b, "Dais", sub(c, (0, 4, 0)), 8, d, self.BLACK, "Marble", collide=True)
        ringz(b, add(c, (0, 0.05, 0)), d * 0.42, self.GOLD, "Metal", th=0.3)

    def sweeper(self, b, rig, c, s, low):
        h = 3.4 if low else 7.0
        d = 3.0 if low else 9.0
        p = add(c, (0, h, 0))
        if low:
            cyl(b, "Sceptre", p, s - 8, d, self.GOLD, "Metal", rig, axis=(1, 0, 0), query=True, refl=0.3,
                attrs={"ObbyHazard": "Burn"})
        else:
            Pt(b, "SweepWall", p, (s - 8, 14, 4), self.BLACK, "Marble", rig, query=True, attrs={"ObbyHazard": "Knock"})
            Pt(b, "SweepTrim", (add(p, (0, 7.2, 0))), (s - 8, 0.6, 4.4), self.GOLD, "Metal", rig)
        for e in (-1, 1):
            ball(b, "Orb", add(p, (e * (s - 8) / 2, 0, 0)), d * 1.6, self.GOLD, "Metal", rig, refl=0.3)

    def door_panel(self, b, rig, c, w):
        Pt(b, "DoorPanel", (add(c, (0, 10, 0))), (6, 20, w), (150, 148, 140), "Cobblestone", rig, query=True,
           attrs={"ObbyHazard": "Knock"})
        n = int(w // 6)
        for k in range(n):
            if k % 2 == 0:
                Pt(b, "Merlon", (add(c, (0, 22, -w / 2 + 3 + k * 6))), (6, 4, 5), (150, 148, 140), "Cobblestone", rig)

    def door_frame(self, b, x, y, z, w):
        for s in (-1, 1):
            cyl(b, "Tower", (x, y + 15, z + s * (w / 2 + 5)), 30, 9, (160, 158, 150), "Cobblestone", collide=True)
            cone(b, "Roof", (x, y + 30, z + s * (w / 2 + 5)), 10, 11, (40, 60, 140), n=4)
        Pt(b, "Lintel", ((x, y + 28, z)), (7, 3, w + 6), (160, 158, 150), "Cobblestone")

    def press_frame(self, b, x, y, z, w, H):
        for s in (-1, 1):
            cyl(b, "Column", (x, y + H / 2 + 12, z + s * (w / 2 + 4)), H + 26, 5, self.WHITE, "Marble", collide=True)
            cyl(b, "ColumnCap", (x, y + H + 24, z + s * (w / 2 + 4)), 2, 8, self.GOLD, "Metal")
        Pt(b, "Beam", ((x, y + H + 26.5, z)), (32, 4, w + 14), self.BLACK, "Marble")

    def press(self, b, rig, rc, bl, w):
        """An upside-down pawn that stamps."""
        Pt(b, "Press", rc, (bl, 18, w + 4), self.BLACK, "Marble", rig, query=True, attrs={"ObbyHazard": "Crush"})
        Pt(b, "PressEdge", (add(rc, (0, -9.1, 0))), (bl + 0.4, 0.6, w + 4.4), self.GOLD, "Metal", rig)
        ell(b, "PawnBody", add(rc, (0, 16, 0)), (bl * 0.7, 18, bl * 0.7), self.BLACK, "Marble", rig)
        ball(b, "PawnHead", add(rc, (0, 28, 0)), bl * 0.55, self.BLACK, "Marble", rig)

    def cross_arm(self, b, rig, c, f, L, w):
        fr = deck_frame(c, f)
        Pt(b, "Arm", CF(sub(c, (0, 3, 0)), fr.x, fr.y, fr.z), (w, 6, L), self.WHITE, "Marble", rig, collide=True)
        n = max(2, int(round(L / (w / 2))))
        q = L / n
        for i in range(n):
            for j in range(2):
                if (i + j) % 2:
                    p = add(c, add(mul(fr.z, -L / 2 + q * (i + 0.5)), mul(fr.x, (j - 0.5) * w / 2)))
                    Pt(b, "Square", CF(add(p, (0, 0.03, 0)), fr.x, fr.y, fr.z), (w / 2, 0.06, q), self.BLACK, "Marble", rig)
        for s in (-1, 1):
            Pt(b, "Inlay", CF(add(c, add(mul(fr.x, s * (w / 2 + 0.3)), (0, -0.4, 0))), fr.x, fr.y, fr.z), (0.6, 1.2, L),
               self.GOLD, "Metal", rig)

    def pad_art(self, b, start, f):
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        Pt(b, "PadPlate", fr, (30, 0.2, 26), self.BLACK, "Marble")
        for k in range(3):
            V2.chevron(b, add(start, add(mul(f, -7 + k * 7), (0, 0.3, 0))), f, 14, self.GOLD)

    def hoop(self, b, c, axis, r):
        ringz(b, c, r, self.GOLD, "Metal", th=3.0, axis=axis, name="Hoop")

    def finish(self, b, x0, x1, y, z, w):
        Skin.finish(self, b, x0, x1, y, z, w)
        # the king, watching over the end of the board
        x, zz = x1 - 50, z + w / 2 + 34
        cyl(b, "KingBase", (x, y - 2, zz), 8, 40, self.BLACK, "Marble")
        cyl(b, "KingBase2", (x, y + 4, zz), 4, 34, self.BLACK, "Marble")
        cyl(b, "KingBody", (x, y + 30, zz), 50, 20, self.BLACK, "Marble")
        cyl(b, "KingCollar", (x, y + 56, zz), 4, 28, self.BLACK, "Marble")
        ringz(b, (x, y + 58.2, zz), 14, self.GOLD, "Metal", th=1.0)
        ell(b, "KingHead", (x, y + 66, zz), (26, 16, 26), self.BLACK, "Marble")
        Pt(b, "Cross", ((x, y + 82, zz)), (4, 18, 4), self.GOLD, "Metal", refl=0.3)
        Pt(b, "Cross", ((x, y + 85, zz)), (4, 4, 12), self.GOLD, "Metal", refl=0.3)


# ===================================================================== 5. Tick Tock (clockwork)
class TickTock(Skin):
    theme_name = "Clockwork"
    key, title = "clocks", "Tick Tock"
    clock, bloom, hue, scale = 17.3, 0.5, 0.09, 1.0
    BRASS, COPPER, DARK, FACE, INK = (206, 164, 74), (190, 112, 64), (52, 42, 36), (246, 238, 220), (36, 30, 26)
    body, top, edge, padc, danger = (52, 42, 36), (206, 164, 74), (255, 214, 120), (90, 220, 255), (240, 60, 40)
    gate_post, gate_board, gate_text = (206, 164, 74), (52, 42, 36), (255, 220, 140)
    hoop_mat = "Metal"
    recipe = [("hops", "Gear climb", {"layout": "rising", "n": 3}), ("sweepers", "Clock-hand sweepers", {}),
              ("swings", "Brass pendulums", {}), ("tower", "Clock tower", {}), ("pistons", "Gear-tooth pistons", {}),
              ("spin_bridges", "Cog bridges", {}), ("hops", "Gear descent", {"layout": "falling"})]
    extra = [("hops", "Clock faces", {"layout": "straight"})]

    def under(self, b, top, w, i):
        x, y, z = top
        cyl(b, "Pipe", (x, y - 34, z), 60, 5, self.COPPER, "Metal", refl=0.2)
        cyl(b, "Gear", (x, y - 30, z), 3, 22, self.BRASS, "Metal", axis=(0, 0, 1), refl=0.2)
        for k in range(10):
            a = TAU * k / 10
            Pt(b, "Tooth", CF((x + math.cos(a) * 11.5, y - 30 + math.sin(a) * 11.5, z)) * rot_axis((0, 0, 1), a), (3, 3, 3), self.BRASS, "Metal")
        cyl(b, "GearHub", (x, y - 30, z), 3.4, 6, self.DARK, "Metal", axis=(0, 0, 1))
        ball(b, "PipeEnd", (x, y - 65, z), 7, self.BRASS, "Metal")

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        Pt(b, "Deck", ((cx, y - 2, z)), (L, 4, w), self.BRASS, "Metal", collide=True, refl=0.15)
        Pt(b, "Plate", ((cx, y + 0.03, z)), (L - 2, 0.06, w * 0.46), (120, 96, 50), "DiamondPlate")
        for s in (-1, 1):
            for k in range(int(L // 9)):
                Pt(b, "Tooth", ((x0 + 4.5 + k * 9, y - 2, z + s * (w / 2 + 1.5))), (4.5, 4, 3), self.BRASS, "Metal")
            cyl(b, "Pipe", (cx, y - 6, z + s * (w / 2 - 3)), L, 3.2, self.COPPER, "Metal", axis=(1, 0, 0), refl=0.2)
            for k in range(int(L // 16) + 1):
                cyl(b, "Rivet", (x0 + 4 + k * 16, y + 0.1, z + s * (w / 2 - 3)), 0.3, 1.8, self.COPPER, "Metal")
        Pt(b, "Under", ((cx, y - 7, z)), (L, 6, w * 0.6), self.DARK, "Metal")
        samples(b, x0, x1, y, z, w)

    def gear(self, b, top, s, rng, spinning=True):
        x, y, z = top
        parent = None
        if spinning:
            root = b.prop_root("Gear")
            parent = b.rig(root, "Spin", axis_frame(top, UP), rng.choice([-1, 1]) * rng.uniform(0.04, 0.07), 4,
                           phase=rng.random(), name="GearSpin")
        col = rng.choice([self.BRASS, self.COPPER])
        cyl(b, "GearDisc", (x, y - 3, z), 6, s * 0.9, col, "Metal", parent, collide=True, refl=0.15)
        n = 14
        for k in range(n):
            a = TAU * k / n
            Pt(b, "Tooth", CF((x + math.cos(a) * s * 0.5, y - 3, z + math.sin(a) * s * 0.5)) * rot_y(-a),
               (s * 0.13, 6, s * 0.11), col, "Metal", parent, collide=True)
        ringz(b, (x, y + 0.05, z), s * 0.36, self.DARK, "Metal", th=0.1, parent=parent)
        for k in range(6):
            a = TAU * k / 6
            cyl(b, "Hole", (x + math.cos(a) * s * 0.26, y + 0.04, z + math.sin(a) * s * 0.26), 0.1, s * 0.13, self.DARK,
                "Metal", parent)
        cyl(b, "Hub", (x, y + 0.06, z), 0.12, s * 0.16, self.DARK, "Metal", parent)
        cyl(b, "Axle", (x, y - 26, z), 40, s * 0.1, self.DARK, "Metal")
        b.samples.append(top + (s,))

    def clockface(self, b, c, s, rng, collide=True):
        x, y, z = c
        cyl(b, "Face", (x, y - 2, z), 4, s, self.FACE, "SmoothPlastic", collide=collide)
        cyl(b, "Bezel", (x, y - 2.2, z), 4.4, s + 3, self.BRASS, "Metal", refl=0.2)
        for k in range(12):
            a = TAU * k / 12
            Pt(b, "Mark", CF((x + math.cos(a) * s * 0.42, y + 0.05, z + math.sin(a) * s * 0.42)) * rot_y(-a),
               (s * (0.06 if k % 3 else 0.11), 0.1, 1.4 if k % 3 else 2.4), self.INK)
        ringz(b, (x, y + 0.05, z), s * 0.47, self.INK, th=0.1)
        cyl(b, "Pin", (x, y + 0.2, z), 0.4, 3.4, self.BRASS, "Metal")
        b.samples.append(c + (s,))

    def plat(self, b, top, s, rng, parent=None):
        self.gear(b, top, s, rng)

    def finale_plat(self, b, top, s, rng):
        self.clockface(b, top, s, rng)

    def island(self, b, c, s, rng):
        self.clockface(b, c, s, rng)

    def hub(self, b, c, d):
        self.clockface(b, c, d, None)

    def sweeper(self, b, rig, c, s, low):
        if low:
            p = add(c, (0, 3.2, 0))
            Pt(b, "SecondHand", p, (s - 8, 2.4, 1.6), (220, 40, 40), "Metal", rig, query=True,
               attrs={"ObbyHazard": "Burn"})
            cyl(b, "Counter", add(p, (-(s - 8) / 2 + 3, 0, 0)), 2.4, 5, (220, 40, 40), "Metal", rig)
        else:
            p = add(c, (0, 6.5, 0))
            Pt(b, "MinuteHand", p, (s - 12, 12, 2.6), self.INK, "Metal", rig, query=True, attrs={"ObbyHazard": "Knock"})
            Pt(b, "HandTip", CF(add(p, ((s - 12) / 2 + 2, 0, 0))) * rot_axis((0, 0, 1), math.pi / 4), (8, 8, 2.6), self.INK,
               "Metal", rig)
            Pt(b, "HandTip", CF(add(p, (-(s - 12) / 2 - 2, 0, 0))) * rot_axis((0, 0, 1), math.pi / 4), (8, 8, 2.6), self.INK,
               "Metal", rig)
            Pt(b, "HandInlay", (add(p, (0, 0, 1.35))), (s - 20, 3, 0.1), self.BRASS, "Metal", rig)

    def swing(self, b, rig, c, L, pivot):
        Pt(b, "SwingDeck", (sub(c, (0, 1.5, 0))), (L, 3, L), self.BRASS, "Metal", rig, collide=True, refl=0.2)
        Pt(b, "Plate", (add(c, (0, 0.03, 0))), (L - 6, 0.06, L - 6), (120, 96, 50), "DiamondPlate", rig)
        for s in (-1, 1):
            self.rope(b, rig, (c[0], c[1], c[2] + s * (L / 2 - 2)), (pivot[0], pivot[1], pivot[2] + s * 6), self.BRASS,
                      "Metal", 2.2)
        cyl(b, "Bob", sub(c, (0, 12, 0)), 4, L * 0.7, self.BRASS, "Metal", rig, axis=(0, 0, 1), refl=0.25)
        cyl(b, "BobInlay", sub(c, (0, 12, 0)), 4.4, L * 0.45, self.COPPER, "Metal", rig, axis=(0, 0, 1))

    def swing_anchor(self, b, pivot, L):
        cyl(b, "Axle", pivot, L + 12, 4, self.DARK, "Metal", axis=(1, 0, 0))
        cyl(b, "AxleGear", pivot, 3, 16, self.BRASS, "Metal", axis=(1, 0, 0))

    def tower(self, b, c, ylo, yhi):
        x, z = c[0], c[2]
        top = yhi - 50
        Pt(b, "Tower", ((x, (ylo + top) / 2, z)), (36, top - ylo, 36), (150, 82, 60), "Brick", collide=True)
        for k in range(int((top - ylo) // 40)):
            Pt(b, "Band", ((x, ylo + 20 + k * 40, z)), (37, 2, 37), (200, 190, 170), "Concrete")
        Pt(b, "ClockRoom", ((x, top + 18, z)), (42, 36, 42), (120, 66, 48), "Brick")
        for f in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
            fc = add((x, top + 18, z), mul(f, 21.2))
            cyl(b, "TowerFace", fc, 0.6, 30, self.FACE, axis=f)
            ringz(b, fc, 15.5, self.BRASS, "Metal", th=1.2, axis=f)
            up = UP
            side = cross(f, up)
            Pt(b, "TowerHand", CF(add(fc, add(mul(up, 5), mul(f, 0.5))), side, f, up), (1.4, 0.4, 11), self.INK)
            Pt(b, "TowerHand", CF(add(fc, add(mul(side, 4), mul(f, 0.6))), up, f, mul(side, -1)), (1.4, 0.4, 8), self.INK)
        for k in range(5):
            w_ = 44 - k * 9
            Pt(b, "Roof", ((x, top + 37 + k * 5, z)), (w_, 5, w_), (60, 70, 90), "Slate")
        Pt(b, "Spire", ((x, top + 70, z)), (2, 16, 2), self.BRASS, "Metal", refl=0.3)

    def tower_plat(self, b, top, s, rng):
        self.gear(b, top, s, rng)

    def piston(self, b, rig, c, bl, w, i, n):
        col = self.BRASS if i % 2 == 0 else self.COPPER
        Pt(b, "PistonDeck", (sub(c, (0, 20, 0))), (bl, 40, w), col, "Metal", rig, collide=True, refl=0.15)
        Pt(b, "Plate", (add(c, (0, 0.03, 0))), (bl - 3, 0.06, w - 4), (120, 96, 50), "DiamondPlate", rig)
        for s in (-1, 1):
            for k in range(int(w // 6)):
                Pt(b, "Tooth", (add(c, (s * (bl / 2 + 1), -2, -w / 2 + 3 + k * 6))), (2, 4, 3), col, "Metal", rig)

    def spin_deck(self, b, rig, c, L, w):
        Pt(b, "SpinDeck", (sub(c, (0, 2, 0))), (L, 4, w), self.BRASS, "Metal", rig, collide=True, refl=0.15)
        Pt(b, "Plate", (add(c, (0, 0.03, 0))), (L - 4, 0.06, w * 0.5), (120, 96, 50), "DiamondPlate", rig)
        for e in (-1, 1):
            cyl(b, "EndGear", add(c, (e * L / 2, -2, 0)), 4.2, w * 0.9, self.COPPER, "Metal", rig)

    def spin_hub(self, b, c):
        x, y, z = c
        cyl(b, "HubGear", (x, y - 8, z), 6, 40, self.COPPER, "Metal")
        for k in range(16):
            a = TAU * k / 16
            Pt(b, "Tooth", CF((x + math.cos(a) * 21, y - 8, z + math.sin(a) * 21)) * rot_y(-a), (4, 6, 4), self.COPPER, "Metal")
        cyl(b, "Axle", (x, y - 34, z), 46, 6, self.DARK, "Metal")

    def pad_art(self, b, start, f):
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        Pt(b, "PadPlate", fr, (30, 0.2, 26), self.DARK, "Metal")
        for k in range(3):
            V2.chevron(b, add(start, add(mul(f, -7 + k * 7), (0, 0.3, 0))), f, 14, self.padc)

    def hoop(self, b, c, axis, r):
        ringz(b, c, r, self.BRASS, "Metal", th=3.0, axis=axis, name="Hoop")
        ringz(b, c, r - 1.6, (255, 200, 110), "Neon", th=0.8, axis=axis, name="HoopGlow")


# ===================================================================== 6. Toy Box
class ToyBox(Skin):
    theme_name = "Toy box"
    key, title = "toys", "Toy Box"
    clock, bloom, hue, scale = 12.8, 0.25, 0.6, 0.9
    body, top, edge, padc, danger = (230, 40, 40), (250, 210, 40), (255, 255, 255), (60, 200, 255), (255, 60, 60)
    gate_post, gate_board, gate_text = (40, 110, 230), (250, 210, 40), (230, 40, 40)
    BRICKS = [(230, 40, 40), (40, 110, 230), (250, 205, 30), (40, 170, 80), (255, 130, 30), (150, 80, 220)]
    WOOD = (232, 200, 150)
    recipe = [("hops", "Alphabet block steps", {"layout": "steps", "n": 3}), ("bumpers", "Spinning tops", {}),
              ("crumble", "Domino path", {}), ("swings", "Toy swings", {}), ("long_jump", "Hula-hoop leap", {}),
              ("doors", "Sliding brick walls", {}), ("hops", "Brick lanes", {"layout": "lanes"})]
    extra = [("hops", "Block hops", {"layout": "straight"})]

    def brick(self, b, top, sx, sz, h, col, parent=None, studs=True, collide=True):
        Pt(b, "Brick", (sub(top, (0, h / 2, 0))), (sx, h, sz), col, "SmoothPlastic", parent, collide=collide, refl=0.06)
        if studs:
            nx, nz = max(1, int(sx // 8)), max(1, int(sz // 8))
            for i in range(nx):
                for j in range(nz):
                    cyl(b, "Stud", (top[0] - sx / 2 + sx * (i + 0.5) / nx, top[1] + 0.5, top[2] - sz / 2 + sz * (j + 0.5) / nz), 1,
                        min(sx / nx, sz / nz) * 0.6, col, "SmoothPlastic", parent, refl=0.06)

    def under(self, b, top, w, i):
        """A stack of bricks."""
        x, y, z = top
        for k in range(6):
            self.brick(b, (x, y - 3 - k * 9.6, z), 12, 12, 9.6, self.BRICKS[(i + k) % len(self.BRICKS)], studs=False, collide=False)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        n = max(1, int(round((x1 - x0) / 32)))
        q = (x1 - x0) / n
        for i in range(n):
            self.brick(b, (x0 + q * (i + 0.5), y, z), q - 0.4, w, 9, self.BRICKS[(i + int(x0 // 7)) % len(self.BRICKS)],
                       studs=(i % 3 == 1))
        samples(b, x0, x1, y, z, w)

    def abc(self, b, top, s, rng):
        """A wooden alphabet block with a coloured letter on every face."""
        x, y, z = top
        h = s * 0.8
        c = (x, y - h / 2, z)
        Pt(b, "Block", c, (s, h, s), self.WOOD, "Wood", collide=True)
        letters = "ABCDEXYZ123"
        for f in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0)):
            col = rng.choice(self.BRICKS)
            ext = h if f[1] else s
            fc = add(c, (f[0] * s / 2, f[1] * h / 2, f[2] * s / 2))
            if f[1]:
                Pt(b, "Panel", (add(fc, (0, 0.05, 0))), (s - 4, 0.1, s - 4), mix(col, (255, 255, 255), 0.75))
                pixel_art(b, add(fc, (0, 0.1, 0)), UP, (1, 0, 0), FONT[rng.choice(letters)], (s - 8) / 5, col, th=0.12)
            else:
                side = cross(f, UP)
                Pt(b, "Panel", CF(add(fc, mul(f, 0.05)), side, UP, cross(side, UP)), (s - 4, h - 4, 0.1),
                   mix(col, (255, 255, 255), 0.75))
                pixel_art(b, add(fc, mul(f, 0.1)), f, UP, FONT[rng.choice(letters)], (min(s, h) - 8) / 5, col, th=0.3)
        b.samples.append(top + (s,))

    def plat(self, b, top, s, rng, parent=None):
        self.abc(b, top, s, rng)

    def finale_plat(self, b, top, s, rng):
        self.brick(b, top, s, s, s * 0.6, rng.choice(self.BRICKS))
        b.samples.append(top + (s,))

    def bumper(self, b, c, rng):
        """A spinning top."""
        root = b.prop_root("SpinningTop")
        rig = b.rig(root, "Spin", axis_frame(c, UP), rng.choice([-1, 1]) * 0.5, 4, phase=rng.random(), name="TopSpin")
        col = rng.choice(self.BRICKS)
        cyl(b, "Bumper", add(c, (0, 7, 0)), 4, 17, col, "SmoothPlastic", rig, query=True, refl=0.08,
            attrs={"ObbyHazard": "Knock"})
        cone(b, "TopCone", add(c, (0, 5, 0)), 5, 16, mix(col, (255, 255, 255), 0.3), parent=rig, n=4, down=True)
        cone(b, "TopDome", add(c, (0, 9, 0)), 4, 15, mix(col, (0, 0, 0), 0.2), parent=rig, n=3)
        for k in range(4):
            a = TAU * k / 4
            Pt(b, "Stripe", CF(add(c, (math.cos(a) * 6, 7, math.sin(a) * 6))) * rot_y(-a), (2, 4.2, 4), (255, 255, 255), parent=rig)
        cyl(b, "Handle", add(c, (0, 14, 0)), 6, 2.4, (240, 240, 240), parent=rig)

    def crumble_tile(self, b, m, c, s, i):
        """A domino lying flat."""
        Pt(b, "Tile", (sub(c, (0, 2.5, 0))), (s - 1, 5, s - 1), (24, 24, 28), "SmoothPlastic", m, collide=True, refl=0.1)
        Pt(b, "DominoLine", (add(c, (0, 0.03, 0))), (1.0, 0.06, s - 6), (250, 250, 250), parent=m)
        spots = {0: [], 1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)],
                 4: [(-1, -1), (-1, 1), (1, -1), (1, 1)], 5: [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)],
                 6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)]}
        for half, nn in ((-1, (i * 3) % 7), (1, (i * 5 + 2) % 7)):
            hc = add(c, (half * (s - 1) / 4, 0.04, 0))
            for u, v in spots[nn]:
                cyl(b, "Pip", add(hc, (u * s * 0.12, 0, v * s * 0.25)), 0.08, s * 0.1, (250, 250, 250), parent=m)

    def swing(self, b, rig, c, L, pivot):
        Pt(b, "SwingDeck", (sub(c, (0, 2, 0))), (L, 4, L * 0.9), self.WOOD, "Wood", rig, collide=True)
        for s in (-1, 1):
            Pt(b, "SeatEdge", (add(c, (0, -0.5, s * (L * 0.45 + 0.8)))), (L, 4, 1.6), self.BRICKS[1], parent=rig)
            self.rope(b, rig, (c[0] - L * 0.35, c[1], c[2] + s * L * 0.42), (pivot[0] - L * 0.35, pivot[1], pivot[2] + s * 4),
                      (240, 230, 200), "Fabric", 1.0)
            self.rope(b, rig, (c[0] + L * 0.35, c[1], c[2] + s * L * 0.42), (pivot[0] + L * 0.35, pivot[1], pivot[2] + s * 4),
                      (240, 230, 200), "Fabric", 1.0)

    def swing_anchor(self, b, pivot, L):
        cyl(b, "Bar", pivot, L + 10, 4, self.BRICKS[0], axis=(1, 0, 0), refl=0.06)
        for s in (-1, 1):
            ball(b, "BarEnd", add(pivot, (s * (L / 2 + 5), 0, 0)), 6, self.BRICKS[2])

    def hoop(self, b, c, axis, r):
        self._h = getattr(self, "_h", 0) + 1
        ringz(b, c, r, self.BRICKS[self._h % len(self.BRICKS)], "SmoothPlastic", th=4.0, axis=axis, name="HulaHoop")

    def door_panel(self, b, rig, c, w):
        col = self.BRICKS[int(abs(c[2]) * 7) % len(self.BRICKS)]
        Pt(b, "DoorPanel", (add(c, (0, 9, 0))), (8, 18, w), col, "SmoothPlastic", rig, query=True, refl=0.06,
           attrs={"ObbyHazard": "Knock"})
        for k in range(int(w // 8)):
            cyl(b, "Stud", add(c, (0, 18.5, -w / 2 + 4 + k * 8)), 1, 4.8, col, parent=rig)

    def door_frame(self, b, x, y, z, w):
        for s in (-1, 1):
            self.brick(b, (x, y + 24, z + s * (w / 2 + 5)), 10, 10, 24, self.BRICKS[3], collide=True)
        self.brick(b, (x, y + 28, z), 10, w + 20, 4, self.BRICKS[2], collide=False)

    def pad_art(self, b, start, f):
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        Pt(b, "PadPlate", fr, (30, 0.2, 26), (255, 255, 255))
        pixel_art(b, add(start, (0, 0.2, 0)), UP, f, FONT["arrow"], 4.0, self.padc, th=0.1)


# ===================================================================== 7. Orbit (space)
class Orbit(Skin):
    theme_name = "Outer space"
    key, title = "space", "Orbit"
    clock, bloom, hue, scale = 0.2, 1.0, 0.62, 1.05
    body, top, edge, padc, danger = (40, 44, 58), (92, 98, 116), (90, 220, 255), (255, 170, 60), (255, 70, 90)
    glass = (150, 200, 255)
    body_mat, top_mat = "Metal", "DiamondPlate"
    gate_post, gate_board, gate_text = (92, 98, 116), (24, 26, 36), (90, 220, 255)
    finish_cols = ((235, 240, 250), (30, 34, 46))
    recipe = [("hops", "Planet hops", {"layout": "wave", "n": 3}), ("spin_bridges", "Satellite bridges", {}),
              ("bumpers", "Asteroid field", {}), ("loop", "Ring loop", {}), ("long_jump", "Moonshot", {}),
              ("drop", "Meteor drop", {}), ("hops", "Planet descent", {"layout": "falling"})]
    extra = [("hops", "Planet line", {"layout": "straight"})]
    light_over = {"Lt_Lighting_Ambient": ("Color3", 0.32, 0.34, 0.45), "Lt_Lighting_OutdoorAmbient": ("Color3", 0.42, 0.44, 0.58),
                  "Lt_Atmosphere_Density": 0.0, "Lt_Atmosphere_Haze": 0.0}

    def under(self, b, top, w, i):
        """A truss pylon with a thruster."""
        x, y, z = top
        for s in (-1, 1):
            Pt(b, "Pylon", ((x + s * 4, y - 26, z)), (1.6, 44, 1.6), self.body, "Metal")
        for k in range(5):
            Pt(b, "PylonBrace", CF((x, y - 10 - k * 8, z)) * rot_axis((0, 0, 1), 0.8 if k % 2 else -0.8), (1, 11, 1), self.body, "Metal")
        cone(b, "Thruster", (x, y - 48, z), 10, 12, (60, 64, 80), "Metal", n=3)
        cyl(b, "ThrusterGlow", (x, y - 49, z), 1, 9, self.edge, "Neon")

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        Pt(b, "Deck", ((cx, y - 1.5, z)), (L, 3, w), self.top, "DiamondPlate", collide=True)
        for s in (-1, 1):
            Pt(b, "EdgeLight", ((cx, y + 0.2, z + s * (w / 2 - 1))), (L, 0.4, 1.0), self.edge, "Neon")
            Pt(b, "Truss", ((cx, y - 7, z + s * (w / 2 - 2))), (L, 2, 2), self.body, "Metal")
        Pt(b, "Spine", ((cx, y - 7, z)), (L, 3, 3), self.body, "Metal")
        for k in range(int(L // 24) + 1):
            xx = x0 + k * 24
            Pt(b, "Rib", ((xx, y - 5, z)), (1.6, 4, w - 2), self.body, "Metal")
            Pt(b, "Brace", CF((xx + 12, y - 6.5, z)) * rot_y(0.8), (1, 1, w * 0.9), self.body, "Metal")
            ball(b, "Beacon", (xx, y - 9, z), 1.2, (255, 80, 80) if k % 2 else self.edge, "Neon")
        samples(b, x0, x1, y, z, w)

    def planet(self, b, top, s, rng):
        d = s * 1.3
        c = sub(top, (0, d / 2, 0))
        m = b.model("Planet", b.roads, {"WallRide": True})
        h = rng.random()
        mat = rng.choice(["SmoothPlastic", "Sand", "Slate", "Marble"])
        ball(b, "Planet", c, d, hsv(h, 0.5, 0.85), mat, m, collide=True)
        for k in range(3):
            ell(b, "Band", add(c, (0, (k - 1) * d * 0.18, 0)), (d * 1.004, d * 0.07, d * 1.004), hsv(h + 0.06 * (k + 1), 0.55, 0.7),
                mat, m)
        ball(b, "Atmosphere", c, d * 1.06, hsv(h, 0.4, 1.0), "ForceField", m, transp=0.55)
        if rng.random() < 0.6:
            tilt = rot_axis((1, 0, 0.3), 0.4)
            mesh(b, "ring", "PlanetRing", CF(c, tilt.x, tilt.y, tilt.z), (d * 1.9, 1.0, d * 1.9), hsv(h + 0.1, 0.3, 1.0),
                 "Neon", m)
        a = rng.random() * TAU
        ball(b, "Moon", add(c, (math.cos(a) * d * 0.95, d * 0.15, math.sin(a) * d * 0.95)), d * 0.16, (210, 210, 220), "Slate", m)
        b.samples.append(top + (s,))

    def plat(self, b, top, s, rng, parent=None):
        self.planet(b, top, s, rng)

    def finale_plat(self, b, top, s, rng):
        self.planet(b, top, s, rng)

    def spin_deck(self, b, rig, c, L, w):
        """A solar panel wing."""
        Pt(b, "SpinDeck", (sub(c, (0, 1, 0))), (L, 2, w), (30, 50, 110), "Glass", rig, collide=True, refl=0.25)
        for k in range(int(L // 8) + 1):
            Pt(b, "Cell", (add(c, (-L / 2 + k * L / int(L // 8), 0.03, 0))), (0.5, 0.06, w), (190, 196, 210), "Metal", rig)
        Pt(b, "Cell", (add(c, (0, 0.03, 0))), (L, 0.06, 0.5), (190, 196, 210), "Metal", rig)
        for s in (-1, 1):
            Pt(b, "Frame", (add(c, (0, -0.5, s * (w / 2 + 0.5)))), (L, 2, 1), (190, 196, 210), "Metal", rig)

    def spin_hub(self, b, c):
        x, y, z = c
        Pt(b, "SatBody", ((x, y - 10, z)), (16, 14, 16), (220, 180, 70), "Foil", refl=0.2)
        cyl(b, "Dish", (x, y - 21, z), 3, 18, (230, 232, 240), "Metal")
        cyl(b, "Antenna", (x, y - 30, z), 14, 1, (200, 200, 210), "Metal")
        ball(b, "Blink", (x, y - 37, z), 2, (255, 70, 70), "Neon")

    def bumper(self, b, c, rng):
        """An asteroid."""
        d = rng.uniform(13, 18)
        r = rot_axis(unit((rng.random(), rng.random(), rng.random())), rng.random() * 3)
        Pt(b, "Asteroid", CF(add(c, (0, d / 2 - 1, 0)), r.x, r.y, r.z), (d, d * 0.8, d * 0.9), (110, 104, 100), "Slate",
           b.hazards, query=True, attrs={"ObbyHazard": "Knock"})
        for k in range(3):
            r2 = rot_axis(unit((rng.random(), rng.random(), rng.random())), rng.random() * 3)
            Pt(b, "Rock", CF(add(c, (rng.uniform(-4, 4), d * rng.uniform(0.3, 0.8), rng.uniform(-4, 4))), r2.x, r2.y, r2.z),
               (d * 0.5, d * 0.45, d * 0.55), (90, 86, 84), "Slate")
        ringz(b, add(c, (0, 0.2, 0)), d * 0.7, (255, 120, 60), "Neon", th=0.5)

    def ribbon(self, b, pts, w, m):
        V2.ribbon(b, pts, w, m, color=(70, 76, 96))

    def loop_deco(self, b, c, R, w):
        ball(b, "LoopPlanet", c, 34, (90, 150, 230), "SmoothPlastic")
        ball(b, "LoopAtmo", c, 37, (140, 200, 255), "ForceField", transp=0.5)
        for k, (rr, col) in enumerate(((R + 10, (90, 220, 255)), (R + 16, (200, 140, 255)), (R + 22, (255, 170, 60)))):
            ringz(b, c, rr, col, "Neon", th=1.4, axis=(0, 0, 1), name="OrbitRing")

    def hoop(self, b, c, axis, r):
        ringz(b, c, r, self.padc, "Neon", th=1.6, axis=axis, name="Hoop")
        ringz(b, c, r + 2.4, (255, 90, 40), "Neon", th=0.6, axis=axis, name="HoopOuter")

    def pad_art(self, b, start, f):
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        Pt(b, "PadPlate", fr, (30, 0.2, 26), (24, 26, 36), "Metal")
        for k in range(3):
            V2.chevron(b, add(start, add(mul(f, -7 + k * 7), (0, 0.3, 0))), f, 14, self.padc)
        for s in (-1, 1):
            Pt(b, "PadRail", CF(add(start, add(mul(fr.x, s * 15), (0, 0.3, 0))), fr.x, fr.y, fr.z), (0.8, 0.4, 26),
               self.edge, "Neon")


# ===================================================================== 8. Eruption (volcano)
class Eruption(Skin):
    theme_name = "Volcano"
    key, title = "volcano", "Eruption"
    clock, bloom, hue, scale = 18.1, 0.9, 0.04, 1.0
    body, top, edge, padc, danger = (32, 28, 28), (54, 46, 44), (255, 120, 30), (90, 220, 255), (255, 150, 30)
    body_mat, top_mat = "Basalt", "Basalt"
    gate_post, gate_board, gate_text = (54, 46, 44), (32, 28, 28), (255, 160, 60)
    finish_cols = ((240, 236, 230), (30, 26, 26))
    LAVA, LAVA2 = (255, 110, 20), (255, 190, 40)
    recipe = [("hops", "Obsidian descent", {"layout": "falling", "n": 3}), ("gates", "Lava geysers", {}),
              ("crumble", "Crumbling crust", {}), ("sweepers", "Flame sweepers", {}), ("pistons", "Magma pistons", {}),
              ("drop", "Caldera drop", {}), ("hops", "Obsidian climb", {"layout": "rising"})]
    extra = [("hops", "Basalt hops", {"layout": "straight"})]
    light_over = {"Lt_Atmosphere_Color": ("Color3", 0.75, 0.42, 0.3), "Lt_Atmosphere_Density": 0.12,
                  "Lt_Atmosphere_Haze": 1.4}

    def under(self, b, top, w, i):
        """A basalt stalactite dripping lava."""
        x, y, z = top
        hexcol(b, "Stalactite", (x, y - 4, z), w * 0.5, 16, self.body, "Basalt", collide=False)
        cone(b, "Stalactite", (x, y - 20, z), 46, w * 0.45, self.body, "Basalt", n=5, down=True)
        cone(b, "LavaDrip", (x + 2, y - 62, z), 10, 3, self.LAVA, "Neon", n=3, down=True)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        n = max(1, int(round(L / 24)))
        q = L / n
        for i in range(n):
            Pt(b, "Basalt", ((x0 + q * (i + 0.5), y - 4, z)), (q - 1.4, 8, w), self.top, "Basalt", collide=True)
            Pt(b, "Seam", ((x0 + q * (i + 1), y - 4.6, z)), (1.4, 8, w - 1), self.LAVA, "CrackedLava")
        for s in (-1, 1):
            Pt(b, "Crust", ((cx, y - 5, z + s * (w / 2 + 1))), (L, 10, 2.4), self.body, "Basalt")
            Pt(b, "LavaEdge", ((cx, y - 9.6, z + s * (w / 2 + 1))), (L, 1.2, 2.6), self.LAVA, "Neon")
        Pt(b, "Root", ((cx, y - 12, z)), (L, 6, w * 0.7), self.body, "Basalt")
        samples(b, x0, x1, y, z, w)

    def obsidian(self, b, top, s, rng):
        x, y, z = top
        h = rng.choice([20, 28, 36])
        hexcol(b, "Column", top, s, h, self.top, "Basalt")
        hexcol(b, "ObsidianTop", add(top, (0, 0.06, 0)), s - 3, 0.12, (20, 16, 24), "Glass", collide=False)
        hexcol(b, "LavaBand", sub(top, (0, h * 0.6, 0)), s + 0.6, 2, self.LAVA, "CrackedLava", collide=False)
        for k in range(3):
            a = rng.random() * TAU
            cone(b, "Drip", (x + math.cos(a) * s * 0.3, y - h, z + math.sin(a) * s * 0.3), rng.uniform(6, 12), 4, self.LAVA,
                 "Neon", n=3, down=True)
        b.samples.append(top + (s,))

    def plat(self, b, top, s, rng, parent=None):
        self.obsidian(b, top, s, rng)

    def island(self, b, c, s, rng):
        x, y, z = c
        cyl(b, "Island", (x, y - 4, z), 8, s, self.top, "Basalt", collide=True)
        ringz(b, (x, y - 3, z), s / 2 + 0.6, self.LAVA, "CrackedLava", th=6.0)
        cone(b, "Under", (x, y - 8, z), 30, s * 0.9, self.body, "Basalt", n=4, down=True)
        b.samples.append(c + (s,))

    def hub(self, b, c, d):
        cyl(b, "Hub", sub(c, (0, 4, 0)), 8, d, self.top, "Basalt", collide=True)

    def gate(self, b, x, y, z, w, beams, attrs, i):
        """Vents on both sides; lava sprays across the deck."""
        for s in (-1, 1):
            p = (x, y, z + s * (w / 2 + 4))
            cone(b, "Vent", sub(p, (0, 2, 0)), 14, 14, self.body, "Basalt", n=4)
            cyl(b, "VentGlow", add(p, (0, 12.2, 0)), 0.4, 5, self.LAVA2, "Neon")
            Pt(b, "VentRock", (add(p, (0, 6, 0))), (6, 16, 6), self.top, "Basalt", collide=True)
        self.beams(b, x, y, z, w, beams, attrs, self.LAVA if i % 2 else self.LAVA2)

    def crumble_tile(self, b, m, c, s, i):
        Pt(b, "Tile", (sub(c, (0, 3, 0))), (s - 1, 6, s - 1), self.top, "Basalt", m, collide=True)
        Pt(b, "Cracks", (add(c, (0, 0.03, 0))), (s - 4, 0.06, s - 4), self.LAVA, "CrackedLava", m)

    def sweeper(self, b, rig, c, s, low):
        if low:
            p = add(c, (0, 3.2, 0))
            Pt(b, "FlameBar", p, (s - 6, 3, 2.4), self.LAVA, "Neon", rig, query=True, attrs={"ObbyHazard": "Burn"})
            Pt(b, "FlameCore", p, (s - 6.4, 1.6, 1.0), self.LAVA2, "Neon", rig)
        else:
            p = add(c, (0, 7, 0))
            Pt(b, "FlameWall", p, (s - 6, 14, 3), self.LAVA, "Neon", rig, query=True, transp=0.15,
               attrs={"ObbyHazard": "Knock"})
            Pt(b, "FlameCore", p, (s - 7, 9, 1.2), self.LAVA2, "Neon", rig)
        Pt(b, "Spout", (add(c, (0, 5, 0))), (7, 10, 7), self.body, "Basalt", rig)

    def piston(self, b, rig, c, bl, w, i, n):
        Pt(b, "PistonDeck", (sub(c, (0, 20, 0))), (bl, 40, w), self.top, "Basalt", rig, collide=True)
        Pt(b, "Glow", (sub(c, (0, 1.2, 0))), (bl + 0.4, 1.2, w + 0.4), self.LAVA, "CrackedLava", rig)
        Pt(b, "Magma", (sub(c, (0, 18, 0))), (bl + 0.2, 3, w + 0.2), self.LAVA, "Neon", rig)

    def hoop(self, b, c, axis, r):
        ringz(b, c, r, self.LAVA, "Neon", th=2.2, axis=axis, name="FireRing")
        ringz(b, c, r + 2, self.LAVA2, "Neon", th=0.8, axis=axis, name="FireRingOuter")

    def pad_art(self, b, start, f):
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        Pt(b, "PadPlate", fr, (30, 0.2, 26), (24, 20, 20), "Basalt")
        for k in range(3):
            V2.chevron(b, add(start, add(mul(f, -7 + k * 7), (0, 0.3, 0))), f, 14, self.padc)

    def environment(self, b):
        """A lava sea far under the course: dark crust with glowing cracks over a dim glow."""
        y = min(s[1] for s in b.samples) - 260
        x0 = b.X1 - b.L
        n = int(math.ceil(b.L / 2000.0))
        for i in range(n):
            xa, xb = x0 + b.L * i / n, x0 + b.L * (i + 1) / n
            Pt(b, "LavaGlow", (((xa + xb) / 2, y - 3, b.zc)), (xb - xa + 2, 2, 2048), (150, 40, 12), "Neon", b.scenery)
            Pt(b, "LavaCrust", (((xa + xb) / 2, y, b.zc)), (xb - xa + 2, 2, 2048), (70, 34, 24), "CrackedLava", b.scenery,
               transp=0.25)


# ===================================================================== 9. Frostbite (ice)
class Frostbite(Skin):
    theme_name = "Ice and snow"
    key, title = "snow", "Frostbite"
    clock, bloom, hue, scale = 10.6, 0.3, 0.56, 1.0
    light_over = {"Lt_Lighting_ExposureCompensation": -0.1, "Lt_Atmosphere_Color": ("Color3", 0.72, 0.84, 0.96)}
    body, top, edge, padc, danger = (110, 170, 225), (196, 226, 248), (90, 200, 255), (255, 110, 190), (255, 80, 120)
    body_mat, top_mat = "Ice", "Glacier"
    gate_post, gate_board, gate_text = (232, 246, 255), (60, 120, 190), (255, 255, 255)
    finish_cols = ((255, 255, 255), (60, 120, 190))
    ICE, SNOW = (120, 180, 232), (246, 250, 255)
    recipe = [("hops", "Snowflake hops", {"layout": "straight", "n": 3}), ("rink", "Ice rink", {}),
              ("crushers", "Icicle crushers", {}), ("wallride", "Glacier wall ride", {}),
              ("spin_bridges", "Snowflake bridges", {}), ("bumpers", "Snowman slalom", {}),
              ("hops", "Snowflake wave", {"layout": "wave"})]
    extra = [("hops", "Ice hops", {"layout": "falling"})]

    def under(self, b, top, w, i):
        """A cluster of big icicles."""
        x, y, z = top
        for k, (dx, dz, ln, d) in enumerate(((0, 0, 50, 14), (-8, w * 0.22, 30, 9), (7, -w * 0.2, 38, 10), (10, w * 0.1, 22, 7))):
            cone(b, "Icicle", (x + dx, y - 2, z + dz), ln, d, self.ICE, "Ice", n=5, down=True, transp=0.1)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        Pt(b, "Deck", ((cx, y - 2, z)), (L, 4, w), self.top, "Glacier", collide=True)
        Pt(b, "IceBody", ((cx, y - 8, z)), (L, 8, w - 2), self.ICE, "Ice", transp=0.25)
        rng = random.Random(int(x0 * 3 + z))
        for s in (-1, 1):
            xx = x0 + rng.uniform(4, 12)
            while xx < x1 - 6:
                ln = rng.uniform(10, 18)
                ell(b, "SnowBank", (xx, y - 0.8, z + s * (w / 2 + 0.5)), (ln, 4, 5), self.SNOW, "Snow")
                cone(b, "Icicle", (xx + rng.uniform(-3, 3), y - 4, z + s * (w / 2 - 1.5)), rng.uniform(5, 10), 2.2, self.ICE,
                     "Ice", n=3, down=True)
                xx += ln * 0.8 + rng.uniform(2, 6)
        samples(b, x0, x1, y, z, w)

    def flake(self, b, top, s, rng, parent=None, collide=True):
        x, y, z = top
        for a in (0, math.pi / 3, 2 * math.pi / 3):
            Pt(b, "Core", CF(sub(top, (0, 2, 0))) * rot_y(a), (s * 0.5, 4, s * 0.5 / math.sqrt(3)), self.top, "Glacier",
               parent, collide=collide)
        for k in range(6):
            a = TAU * k / 6
            f = (math.cos(a), 0, math.sin(a))
            Pt(b, "Arm", deck_frame(sub(add(top, mul(f, s * 0.36)), (0, 1.6, 0)), f), (s * 0.14, 3.2, s * 0.5), self.ICE,
               "Ice", parent, collide=collide, refl=0.1)
            for t in (0.25, 0.4):
                for sg in (-1, 1):
                    g = unit(add(f, mul((-f[2], 0, f[0]), sg * 0.9)))
                    Pt(b, "Branch", deck_frame(sub(add(top, add(mul(f, s * t), mul(g, s * 0.06))), (0, 1.5, 0)), g),
                       (s * 0.06, 2.6, s * 0.14), self.ICE, "Ice", parent)
            ball(b, "Tip", sub(add(top, mul(f, s * 0.6)), (0, 1.6, 0)), 3, (255, 255, 255), "Neon", parent)

    def plat(self, b, top, s, rng, parent=None):
        self.flake(b, top, s, rng)
        hexcol(b, "IceColumn", sub(top, (0, 4, 0)), s * 0.3, 30, self.ICE, "Ice", collide=False)
        b.samples.append(top + (s,))

    def rink_tile(self, b, c, cell):
        Pt(b, "Ice", (sub(c, (0, 3, 0))), (cell - 0.6, 6, cell - 0.6), (150, 205, 245), "Ice", collide=True, refl=0.15)

    def rink_rim(self, b, x0, x1, y, z, w):
        for s in (-1, 1):
            xx = x0
            while xx < x1:
                ell(b, "SnowBank", (xx + 9, y + 0.5, z + s * (w / 2 + 3)), (20, 6, 7), self.SNOW, "Snow")
                xx += 16
        for k in range(int((x1 - x0) // 80) + 1):
            for s in (-1, 1):
                p = (x0 + k * 80, y, z + s * (w / 2 + 5))
                cyl(b, "FlagPole", add(p, (0, 8, 0)), 16, 0.6, (240, 240, 240))
                Pt(b, "Flag", (add(p, (2.5, 14, 0))), (5, 3.5, 0.2), self.padc if k % 2 else (90, 200, 255))

    def press_frame(self, b, x, y, z, w, H):
        for s in (-1, 1):
            hexcol(b, "IcePillar", (x, y + H + 26, z + s * (w / 2 + 4)), 7, H + 26, self.ICE, "Ice")
            ell(b, "SnowCap", (x, y + H + 27, z + s * (w / 2 + 4)), (10, 4, 10), self.SNOW, "Snow")
        Pt(b, "Beam", ((x, y + H + 26, z)), (32, 4, w + 14), self.top, "Glacier")
        ell(b, "SnowCap", (x, y + H + 28.5, z), (30, 3, w + 12), self.SNOW, "Snow")

    def press(self, b, rig, rc, bl, w):
        Pt(b, "Press", rc, (bl, 18, w + 4), self.ICE, "Ice", rig, query=True, transp=0.1, refl=0.1,
           attrs={"ObbyHazard": "Crush"})
        rng = random.Random(int(rc[0]))
        for k in range(10):
            p = add(rc, (rng.uniform(-bl / 2 + 3, bl / 2 - 3), -9, rng.uniform(-w / 2, w / 2)))
            cone(b, "Icicle", p, rng.uniform(4, 8), 3.4, (225, 245, 255), "Ice", rig, n=3, down=True)

    def ribbon(self, b, pts, w, m):
        V2.ribbon(b, pts, w, m, color=(170, 215, 245))

    def spin_deck(self, b, rig, c, L, w):
        Pt(b, "SpinDeck", (sub(c, (0, 2, 0))), (L, 4, w), self.top, "Glacier", rig, collide=True)
        Pt(b, "IceUnder", (sub(c, (0, 5, 0))), (L - 2, 3, w - 2), self.ICE, "Ice", rig, transp=0.2)

    def spin_hub(self, b, c):
        self.flake(b, sub(c, (0, 9, 0)), 40, None, collide=False)

    def bumper(self, b, c, rng):
        """A snowman."""
        x, y, z = c
        ball(b, "Snowman", (x, y + 7, z), 15, self.SNOW, "Snow", b.hazards, query=True, attrs={"ObbyHazard": "Knock"})
        ball(b, "SnowMid", (x, y + 17, z), 11, self.SNOW, "Snow")
        ball(b, "SnowHead", (x, y + 25, z), 8, self.SNOW, "Snow")
        cyl(b, "Carrot", (x - 5.6, y + 25, z), 4, 1.4, (255, 130, 30), axis=(1, 0, 0))
        cyl(b, "CarrotTip", (x - 7.8, y + 25, z), 1.2, 0.7, (255, 130, 30), axis=(1, 0, 0))
        for k in range(3):
            ball(b, "Coal", (x - 5.3, y + 15 + k * 2.6, z), 1.2, (30, 30, 34))
        cyl(b, "HatBrim", (x, y + 29, z), 0.8, 10, (30, 30, 34))
        cyl(b, "Hat", (x, y + 32, z), 6, 6.5, (30, 30, 34))
        cyl(b, "HatBand", (x, y + 30, z), 1.2, 6.8, (220, 40, 60))
        Pt(b, "Scarf", ((x, y + 21.5, z)), (10, 2, 10), (220, 40, 60), "Fabric")

    def pad_art(self, b, start, f):
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        Pt(b, "PadPlate", fr, (30, 0.2, 26), (60, 120, 190), "Ice")
        for k in range(3):
            V2.chevron(b, add(start, add(mul(f, -7 + k * 7), (0, 0.3, 0))), f, 14, self.padc)

    def hoop(self, b, c, axis, r):
        ringz(b, c, r, (200, 235, 255), "Ice", th=3.0, axis=axis, name="IceRing")
        ringz(b, c, r - 1.4, (255, 255, 255), "Neon", th=0.8, axis=axis, name="IceRingGlow")


# ===================================================================== 10. High Score (arcade)
class HighScore(Skin):
    theme_name = "Neon arcade"
    key, title = "arcade", "High Score"
    clock, bloom, hue, scale = 21.5, 1.2, 0.85, 0.95
    body, top, edge, padc, danger = (26, 22, 44), (22, 20, 36), (255, 60, 200), (60, 230, 255), (255, 50, 80)
    gate_post, gate_board, gate_text = (26, 22, 44), (16, 14, 28), (255, 230, 60)
    finish_cols = ((255, 255, 255), (20, 18, 30))
    NEON = [(255, 60, 200), (60, 230, 255), (255, 230, 60), (90, 255, 120), (255, 120, 40), (170, 90, 255)]
    recipe = [("hops", "Coin lanes", {"layout": "lanes", "n": 3}), ("bumpers", "Pinball bumpers", {}),
              ("gates", "Laser rhythm", {}), ("crumble", "Pixel path", {}), ("loop", "Neon loop", {}),
              ("pistons", "Equaliser bars", {}), ("doors", "Invader walls", {})]
    extra = [("hops", "Coin hops", {"layout": "straight"})]
    light_over = {"Lt_Lighting_Ambient": ("Color3", 0.3, 0.26, 0.42), "Lt_Lighting_OutdoorAmbient": ("Color3", 0.38, 0.32, 0.52)}

    def under(self, b, top, w, i):
        x, y, z = top
        Pt(b, "Column", ((x, y - 30, z)), (8, 52, 8), self.body)
        for k in range(4):
            Pt(b, "ColumnRing", ((x, y - 12 - k * 11, z)), (8.6, 1.2, 8.6), self.NEON[(i + k) % 6], "Neon")

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        p = Pt(b, "Deck", ((cx, y - 2, z)), (L, 4, w), self.top, "SmoothPlastic", collide=True, refl=0.15)
        SC.tex(b, p, "grid", face=1, tile=8.0, color=(255, 80, 220), transp=0.3)
        for s in (-1, 1):
            Pt(b, "EdgeNeon", ((cx, y + 0.15, z + s * (w / 2 - 0.6))), (L, 0.3, 1.2), self.NEON[1 if s > 0 else 0], "Neon")
            Pt(b, "Side", ((cx, y - 4, z + s * (w / 2 + 0.3))), (L, 8, 0.6), self.body, "SmoothPlastic")
            Pt(b, "SideNeon", ((cx, y - 6, z + s * (w / 2 + 0.65))), (L, 0.6, 0.2), self.NEON[2], "Neon")
        samples(b, x0, x1, y, z, w)

    def coin(self, b, top, s, rng):
        x, y, z = top
        cyl(b, "Coin", (x, y - 3, z), 6, s, (255, 196, 40), "SmoothPlastic", collide=True, refl=0.15)
        cyl(b, "CoinRim", (x, y - 3, z), 6.4, s + 1.8, (235, 150, 20), "SmoothPlastic", refl=0.15)
        pixel_art(b, (x, y + 0.02, z), UP, (1, 0, 0), FONT["star"], s * 0.09, (255, 245, 170), "Neon", th=0.12)
        ringz(b, (x, y - 8, z), s * 0.45, self.NEON[rng.randrange(6)], "Neon", th=1.0)
        b.samples.append(top + (s,))

    def heart(self, b, top, s, rng):
        x, y, z = top
        h = s * 0.7
        Pt(b, "Block", ((x, y - h / 2, z)), (s, h, s), (30, 26, 50), "SmoothPlastic", collide=True, refl=0.1)
        col = self.NEON[rng.randrange(6)]
        for f in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
            pixel_art(b, add((x, y - h / 2, z), mul(f, s / 2)), f, UP, FONT["heart"], h / 8, col, "Neon", th=0.3)
        pixel_art(b, (x, y + 0.02, z), UP, (1, 0, 0), FONT["heart"], s / 9, col, "Neon", th=0.1)
        b.samples.append(top + (s,))

    def plat(self, b, top, s, rng, parent=None):
        self.coin(b, top, s, rng)

    def finale_plat(self, b, top, s, rng):
        self.heart(b, top, s, rng)

    def bumper(self, b, c, rng):
        """A pinball bumper."""
        x, y, z = c
        col = self.NEON[rng.randrange(6)]
        cyl(b, "BumperBase", (x, y + 1, z), 2, 18, (210, 214, 224), "Metal", refl=0.4)
        cyl(b, "Bumper", (x, y + 6, z), 8, 15, col, "SmoothPlastic", b.hazards, query=True, refl=0.1,
            attrs={"ObbyHazard": "Knock"})
        cyl(b, "BumperRing", (x, y + 6, z), 2, 16.4, col, "Neon")
        cyl(b, "BumperCap", (x, y + 10.4, z), 1, 17, (240, 240, 250), "SmoothPlastic")
        cyl(b, "BumperLight", (x, y + 11, z), 0.4, 8, (255, 255, 255), "Neon")

    def gate(self, b, x, y, z, w, beams, attrs, i):
        col = self.NEON[i % 2]
        for s in (-1, 1):
            Pt(b, "Cabinet", ((x, y + 16, z + s * (w / 2 + 5))), (8, 32, 8), (24, 20, 40), collide=True)
            Pt(b, "Screen", ((x, y + 22, z + s * (w / 2 + 0.9))), (6, 8, 0.2), col, "Neon", transp=0.2)
            Pt(b, "Marquee", ((x, y + 30, z + s * (w / 2 + 0.9))), (7, 2, 0.2), self.NEON[2], "Neon")
        self.beams(b, x, y, z, w, beams, attrs, col)

    def crumble_tile(self, b, m, c, s, i):
        col = self.NEON[i % 6]
        Pt(b, "Tile", (sub(c, (0, 2.5, 0))), (s - 1.5, 5, s - 1.5), mix(col, (0, 0, 0), 0.65), "SmoothPlastic", m,
           collide=True, refl=0.1)
        Pt(b, "TileFace", (add(c, (0, 0.02, 0))), (s - 6, 0.04, s - 6), mix(col, (0, 0, 0), 0.35), "SmoothPlastic", m)
        for s_ in (-1, 1):
            Pt(b, "TileGlow", (add(c, (0, 0.06, s_ * (s / 2 - 2)))), (s - 2, 0.12, 0.8), col, "Neon", m)
            Pt(b, "TileGlow", (add(c, (s_ * (s / 2 - 2), 0.06, 0))), (0.8, 0.12, s - 2), col, "Neon", m)

    def ribbon(self, b, pts, w, m):
        V2.ribbon(b, pts, w, m, color=(30, 26, 52))

    def loop_deco(self, b, c, R, w):
        for k, col in enumerate((self.NEON[0], self.NEON[1], self.NEON[2])):
            ringz(b, (c[0], c[1], c[2] + (k - 1) * (w / 2 + 6)), R + 8 + k * 4, col, "Neon", th=1.4, axis=(0, 0, 1),
                  name="NeonRing")

    def piston(self, b, rig, c, bl, w, i, n):
        t = i / max(n - 1, 1)
        col = self.NEON[3] if t < 0.4 else (self.NEON[2] if t < 0.75 else (255, 60, 60))
        Pt(b, "PistonDeck", (sub(c, (0, 20, 0))), (bl, 40, w), (24, 20, 40), "SmoothPlastic", rig, collide=True)
        Pt(b, "Level", (sub(c, (0, 1.2, 0))), (bl + 0.3, 2.4, w + 0.3), col, "Neon", rig)
        for k in range(1, 6):
            Pt(b, "Segment", (sub(c, (0, 1.2 + k * 5, 0))), (bl + 0.3, 2.4, w + 0.3), mix(col, (0, 0, 0), 0.25 + 0.1 * k),
               "Neon", rig, transp=0.1 * k)

    def door_panel(self, b, rig, c, w):
        Pt(b, "DoorPanel", (add(c, (0, 9, 0))), (4, 18, w), (24, 20, 40), "SmoothPlastic", rig, query=True,
           attrs={"ObbyHazard": "Knock"})
        col = self.NEON[int(abs(c[2])) % 6]
        for f in ((-1, 0, 0), (1, 0, 0)):
            pixel_art(b, add(add(c, (0, 9, 0)), mul(f, 2.0)), f, UP, FONT["alien"], 1.5, col, "Neon", rig, th=0.2)

    def door_frame(self, b, x, y, z, w):
        Pt(b, "DoorFrame", ((x, y + 20, z)), (4, 1.2, w + 8), self.NEON[2], "Neon")

    def pad_art(self, b, start, f):
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        Pt(b, "PadPlate", fr, (30, 0.2, 26), (16, 14, 28))
        pixel_art(b, add(start, (0, 0.2, 0)), UP, f, FONT["arrow"], 4.0, self.padc, "Neon", th=0.1)

    def hoop(self, b, c, axis, r):
        self._h = getattr(self, "_h", 0) + 1
        ringz(b, c, r, self.NEON[self._h % 6], "Neon", th=1.6, axis=axis, name="Hoop")


SKINS = {1: SugarRush, 2: DriveThru, 3: SporeSprings, 4: Checkmate, 5: TickTock, 6: ToyBox, 7: Orbit, 8: Eruption,
         9: Frostbite, 10: HighScore}
