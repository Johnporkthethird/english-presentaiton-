"""25 object worlds. Each gives the level its hop targets (`plat`), its long surfaces (`deck`) and its colours.

Every drivable top is a real collidable part at exactly the requested height; round or domed visuals sit on an
invisible flat collider so the car rides level.
"""
import math
import colorsys
from geom import CF, deck_frame, axis_frame, look_frame, add, sub, mul, unit, rot_y, rot_axis, UP
from builder import mix
import rbxl

TAU = math.pi * 2


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return (int(r * 255), int(g * 255), int(b * 255))


# ------------------------------------------------------------------ primitives
def part(b, name, cf, size, color, mat="SmoothPlastic", parent=None, collide=False, transp=0.0, shape=1, cls="Part"):
    return b.part(name, cf, size, color, mat, parent=parent or b.roads, collide=collide, query=collide, transp=transp,
                  shape=shape, cls=cls)


def cyl(b, name, c, h, d, color, mat="SmoothPlastic", parent=None, collide=False, axis=UP, transp=0.0):
    return part(b, name, axis_frame(c, axis), (h, d, d), color, mat, parent, collide, transp, shape=2)


def ball(b, name, c, d, color, mat="SmoothPlastic", parent=None, collide=False):
    return part(b, name, CF(c), (d, d, d), color, mat, parent, collide, shape=0)


def ell(b, name, c, size, color, mat="SmoothPlastic", parent=None, rot=None, transp=0.0):
    """An ellipsoid: a non-colliding part carrying a sphere SpecialMesh."""
    cf = CF(c) if rot is None else CF(c, rot.x, rot.y, rot.z)
    p = part(b, name, cf, size, color, mat, parent, False, transp)
    m = b.fac.blank("SpecialMesh")
    m.set("MeshType", 3)
    m.set("Scale", (1.0, 1.0, 1.0))
    m.set("Offset", (0.0, 0.0, 0.0))
    m.set_parent(p)
    return p


def mesh(b, kind, name, cf, size, color, mat="SmoothPlastic", parent=None, transp=0.0):
    src = b.fac.meshes[kind]
    m = b.fac.clone(src, parent or b.roads)
    for c in list(m.children):
        m.children.remove(c)
        c.parent = None
    m.props["AttributesSerialize"] = (0x01, b"")
    m.set("Name", name.encode())
    m.set("CFrame", cf.to_prop())
    m.set("size", tuple(float(v) for v in size))
    m.set("Color3uint8", tuple(int(v) for v in color))
    from factory import MAT
    m.set("Material", MAT[mat] if isinstance(mat, str) else mat)
    m.set("Transparency", float(transp))
    for k, v in (("CanCollide", False), ("CanQuery", False), ("CanTouch", False), ("Anchored", True), ("CastShadow", False)):
        if k in m.props:
            m.set(k, v)
    b.count += 1
    return m


def collider(b, top, sx, sz, fwd=(1, 0, 0), parent=None, round_=False, name="Floor"):
    """The invisible flat floor under a domed or round visual."""
    if round_:
        return part(b, name, axis_frame(sub(top, (0, 1.0, 0)), UP), (2, sx, sx), (255, 255, 255), parent=parent,
                    collide=True, transp=1.0, shape=2)
    fr = deck_frame(top, fwd)
    return part(b, name, CF(sub(top, (0, 1.0, 0)), fr.x, fr.y, fr.z), (sx, 2, sz), (255, 255, 255), parent=parent,
                collide=True, transp=1.0)


def sample(b, top, s):
    b.samples.append((top[0], top[1], top[2], s))


def ringz(b, c, r, color, mat="Neon", th=1.2, axis=UP, parent=None, name="Ring"):
    """A flat ring using the place's ring mesh (axis = its normal)."""
    if abs(axis[1]) > 0.9:
        cf = CF(c)
    else:
        cf = axis_frame(c, axis) * CF((0, 0, 0), (0, 1, 0), (-1, 0, 0), (0, 0, 1))
    return mesh(b, "ring", name, cf, (2 * r, th, 2 * r), color, mat, parent)


# ------------------------------------------------------------------ worlds
class World:
    key = "base"
    names = []

    def palette(self, v):
        raise NotImplementedError

    def plat(self, b, top, s, rng, parent=None):
        raise NotImplementedError

    def deck(self, b, x0, x1, y, z, w, parent=None):
        raise NotImplementedError


def straight_slab(b, x0, x1, y, z, w, color, mat, h=8.0, parent=None, name="Deck", edge=None):
    c = ((x0 + x1) / 2, y - h / 2, z)
    p = part(b, name, CF(c), (x1 - x0, h, w), color, mat, parent, True)
    if edge:
        for s in (-1, 1):
            part(b, "Edge", CF(((x0 + x1) / 2, y + 0.2, z + s * (w / 2 - 0.5))), (x1 - x0, 0.42, 0.9), edge, "Neon", parent)
    for k in range(int((x1 - x0) // 40) + 1):
        sample(b, (x0 + k * 40, y, z), w)
    return p


class Mushrooms(World):
    key = "mushroom"
    caps = [(214, 46, 46), (60, 110, 230), (150, 70, 200), (240, 130, 40)]

    def palette(self, v):
        cap = self.caps[v % 4]
        return dict(body=(236, 226, 200), top=cap, edge=(255, 250, 235), pad=(255, 220, 60), danger=(255, 70, 50),
                    glass=(220, 240, 255), body_mat="SmoothPlastic", top_mat="SmoothPlastic", clock=15.5, bloom=0.3,
                    hue=colorsys.rgb_to_hsv(*(c / 255 for c in cap))[0])

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        cyl(b, "Stem", sub(top, (0, s * 0.2 + 24, 0)), 48, s * 0.3, pal["body"], parent=parent)
        ell(b, "Cap", sub(top, (0, s * 0.2, 0)), (s * 1.08, s * 0.42, s * 1.08), pal["top"], parent=parent)
        for k in range(6):
            a = TAU * k / 6 + rng.random()
            r = s * rng.uniform(0.22, 0.38)
            h = s * 0.21 * math.sqrt(max(0.0, 1 - (r / (s * 0.54)) ** 2))
            ell(b, "Spot", (top[0] + math.cos(a) * r, top[1] - s * 0.2 + h + 0.2, top[2] + math.sin(a) * r),
                (s * 0.14, s * 0.05, s * 0.14), (255, 255, 255), parent=parent)
        collider(b, top, s * 0.8, s * 0.8, round_=True, parent=parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        d = w * 0.95
        cyl(b, "Log", ((x0 + x1) / 2, y - d / 2 + 1.5, z), x1 - x0, d, (120, 84, 56), "Wood", parent, axis=(1, 0, 0))
        for k in range(int((x1 - x0) // 60) + 1):
            cyl(b, "Bark", (x0 + 20 + k * 60, y - d / 2 + 1.5, z), 3, d + 0.8, (84, 58, 38), "Wood", parent, axis=(1, 0, 0))
        for e in (x0, x1):
            cyl(b, "LogEnd", (e, y - d / 2 + 1.5, z), 0.6, d * 0.9, (214, 180, 130), "Wood", parent, axis=(1, 0, 0))
        straight_slab(b, x0, x1, y, z, w * 0.55, (255, 255, 255), "SmoothPlastic", 2, parent, name="Floor").set("Transparency", 1.0)


class Chess(World):
    key = "chess"
    sets = [((240, 240, 236), (24, 24, 28), (255, 210, 90)), ((236, 230, 220), (150, 110, 70), (255, 230, 150)),
            ((30, 30, 34), (210, 210, 220), (90, 230, 255)), ((246, 246, 250), (120, 30, 60), (255, 120, 160))]

    def palette(self, v):
        a, c, e = self.sets[v % 4]
        return dict(body=c, top=a, edge=e, pad=e, danger=(255, 60, 60), glass=(230, 230, 240), body_mat="Marble",
                    top_mat="Marble", clock=16.0, bloom=0.4, hue=0.12, white=a, black=c)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        rook = rng.random() < 0.6
        col = pal["white"] if rng.random() < 0.5 else pal["black"]
        cyl(b, "Base", sub(top, (0, 44, 0)), 6, s * 1.05, col, "Marble", parent)
        cyl(b, "BaseRing", sub(top, (0, 40, 0)), 3, s * 0.92, col, "Marble", parent)
        if rook:
            cyl(b, "Body", sub(top, (0, 22, 0)), 36, s * 0.78, col, "Marble", parent)
            cyl(b, "Crown", sub(top, (0, 3, 0)), 6, s * 0.96, col, "Marble", parent, collide=True)
            for k in range(6):
                a = TAU * k / 6
                part(b, "Merlon", CF((top[0] + math.cos(a) * s * 0.42, top[1] + 2.5, top[2] + math.sin(a) * s * 0.42)) *
                     rot_y(-a), (s * 0.12, 5, s * 0.2), col, "Marble", parent)
        else:
            ell(b, "Body", sub(top, (0, 24, 0)), (s * 0.6, 40, s * 0.6), col, "Marble", parent)
            cyl(b, "Collar", sub(top, (0, 6, 0)), 3, s * 0.75, col, "Marble", parent)
            ell(b, "Head", sub(top, (0, 1, 0)), (s * 0.9, 8, s * 0.9), col, "Marble", parent)
            collider(b, top, s * 0.85, 0, round_=True, parent=parent)
        ringz(b, sub(top, (0, 0.6, 0)), s * 0.49, pal["edge"], th=0.8, parent=parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        sq = w / 2
        n = max(1, int(round((x1 - x0) / sq)))
        q = (x1 - x0) / n
        for i in range(n):
            for j in range(2):
                col = pal["white"] if (i + j) % 2 == 0 else pal["black"]
                part(b, "Square", CF((x0 + q * (i + 0.5), y - 3, z + (j - 0.5) * sq)), (q, 6, sq), col, "Marble", parent, True)
        part(b, "BoardEdge", CF(((x0 + x1) / 2, y - 6.5, z)), (x1 - x0 + 2, 2, w + 2), pal["edge"], "Neon", parent)
        for k in range(int((x1 - x0) // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


class Dice(World):
    key = "dice"
    sets = [((246, 246, 246), (20, 20, 24), (20, 120, 70)), ((200, 30, 40), (255, 255, 255), (30, 30, 60)),
            ((40, 40, 46), (255, 210, 60), (120, 30, 40)), ((70, 140, 255), (255, 255, 255), (20, 60, 40))]

    def palette(self, v):
        die, pip, felt = self.sets[v % 4]
        return dict(body=die, top=die, edge=pip, pad=(255, 220, 80), danger=(255, 60, 60), glass=(230, 240, 255),
                    body_mat="SmoothPlastic", top_mat="SmoothPlastic", clock=17.2, bloom=0.4, hue=0.95, pip=pip, felt=felt)

    def pips(self, b, c, fr, s, n, parent):
        spots = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (-1, 1), (1, -1), (1, 1)],
                 5: [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)], 6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)]}[n]
        for u, v in spots:
            p = add(c, add(mul(fr.x, u * s * 0.27), mul(fr.z, v * s * 0.27)))
            part(b, "Pip", CF(add(p, mul(fr.y, 0.06)), fr.x, fr.y, fr.z) * CF((0, 0, 0), (0, 1, 0), (-1, 0, 0), (0, 0, 1)),
                 (0.2, s * 0.16, s * 0.16), b.theme["pip"], "SmoothPlastic", parent, shape=2)

    def plat(self, b, top, s, rng, parent=None):
        yaw = rng.choice([0.0, math.pi / 4, math.pi / 8])
        f = (math.cos(yaw), 0, math.sin(yaw))
        fr = deck_frame(top, f)
        part(b, "Die", CF(sub(top, (0, s / 2, 0)), fr.x, fr.y, fr.z), (s, s, s), b.theme["body"], "SmoothPlastic", parent, True)
        self.pips(b, top, fr, s, rng.randint(1, 6), parent)
        side = CF(sub(top, (0, s / 2, 0)), fr.x, fr.y, fr.z)
        for (ax, n) in (((1, 0, 0), rng.randint(1, 6)), ((0, 0, 1), rng.randint(1, 6))):
            c = side.point(mul(ax, s / 2))
            normal = side.vec(ax)
            nf = deck_frame(c, fr.y, up=normal) if abs(normal[1]) < 0.9 else fr
            self.pips(b, c, nf, s, n, parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        cw = w * 0.75
        n = max(1, int(round((x1 - x0) / cw)))
        q = (x1 - x0) / n
        for i in range(n):
            c = (x0 + q * (i + 0.5), y - 0.6 - (i % 2) * 0.3, z)
            part(b, "Card", CF(c), (q + 2, 1.2, w), (250, 250, 248), "SmoothPlastic", parent, True)
            red = i % 2 == 0
            part(b, "CardInset", CF(add(c, (0, 0.62, 0))), (q - 3, 0.05, w - 5), (255, 255, 255), "SmoothPlastic", parent)
            part(b, "Suit", CF(add(c, (0, 0.66, 0))) * rot_y(math.pi / 4), (w * 0.18, 0.06, w * 0.18),
                 (210, 30, 40) if red else (20, 20, 26), "SmoothPlastic", parent)
            for s in (-1, 1):
                part(b, "CardBorder", CF(add(c, (0, 0.64, s * (w / 2 - 1.2)))), (q - 1, 0.05, 0.6),
                     (210, 30, 40) if red else (20, 20, 26), "SmoothPlastic", parent)
        part(b, "Felt", CF(((x0 + x1) / 2, y - 5, z)), (x1 - x0, 6, w + 6), pal["felt"], "Fabric", parent)
        for k in range(int((x1 - x0) // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


class Gears(World):
    key = "gears"
    metals = [((200, 160, 70), (120, 90, 40)), ((170, 176, 186), (90, 96, 106)), ((200, 110, 70), (110, 60, 40)),
              ((60, 64, 72), (200, 160, 70))]

    def palette(self, v):
        a, c = self.metals[v % 4]
        return dict(body=c, top=a, edge=(255, 180, 60), pad=(90, 230, 255), danger=(255, 60, 40), glass=(220, 220, 230),
                    body_mat="Metal", top_mat="DiamondPlate", clock=16.8, bloom=0.5, hue=0.1)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        root = b.prop_root("Gear")
        rig = b.rig(root, "Spin", axis_frame(top, UP), rng.choice([-1, 1]) * rng.uniform(0.04, 0.08), 4, phase=rng.random(),
                    name="GearSpin")
        cyl(b, "GearDisc", sub(top, (0, 4, 0)), 8, s * 0.9, pal["top"], "Metal", rig, collide=True)
        n = 12
        for k in range(n):
            a = TAU * k / n
            part(b, "Tooth", CF((top[0] + math.cos(a) * s * 0.5, top[1] - 4, top[2] + math.sin(a) * s * 0.5)) * rot_y(-a),
                 (s * 0.14, 8, s * 0.13), pal["top"], "Metal", rig, True)
        cyl(b, "Hub", (top[0], top[1] + 0.05, top[2]), 0.1, s * 0.3, pal["body"], "Metal", rig)
        for k in range(5):
            a = TAU * k / 5
            cyl(b, "Hole", (top[0] + math.cos(a) * s * 0.28, top[1] + 0.06, top[2] + math.sin(a) * s * 0.28), 0.1, s * 0.12,
                pal["body"], "Metal", rig)
        cyl(b, "Axle", sub(top, (0, 30, 0)), 44, s * 0.12, pal["body"], "Metal")
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        L = x1 - x0
        cx = (x0 + x1) / 2
        part(b, "Flange", CF((cx, y - 1.5, z)), (L, 3, w), pal["top"], "DiamondPlate", parent, True)
        part(b, "Web", CF((cx, y - 10, z)), (L, 14, 3), pal["body"], "Metal", parent)
        part(b, "LowFlange", CF((cx, y - 18, z)), (L, 3, w * 0.7), pal["body"], "Metal", parent)
        for k in range(int(L // 24) + 1):
            for s in (-1, 1):
                cyl(b, "Rivet", (x0 + 6 + k * 24, y + 0.15, z + s * (w / 2 - 2.5)), 0.3, 1.6, pal["body"], "Metal", parent)
        for k in range(int(L // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


class Candy(World):
    key = "candy"

    def palette(self, v):
        h = [0.92, 0.55, 0.12, 0.78][v % 4]
        return dict(body=hsv(h, 0.45, 0.95), top=hsv(h + 0.33, 0.35, 1.0), edge=(255, 255, 255), pad=hsv(h + 0.5, 0.6, 1),
                    danger=(255, 70, 90), glass=hsv(h, 0.2, 1), body_mat="SmoothPlastic", top_mat="SmoothPlastic",
                    clock=13.5, bloom=0.35, hue=h)

    def plat(self, b, top, s, rng, parent=None):
        h = rng.random()
        if rng.random() < 0.55:
            col = hsv(h, 0.55, 1.0)
            ell(b, "Gumdrop", sub(top, (0, s * 0.42, 0)), (s * 1.05, s * 0.86, s * 1.05), col, "Glass", parent, transp=0.15)
            for k in range(10):
                a = rng.random() * TAU
                r = rng.uniform(0.1, 0.45) * s
                hh = s * 0.43 * math.sqrt(max(0.0, 1 - (r / (s * 0.525)) ** 2))
                ball(b, "Sugar", (top[0] + math.cos(a) * r, top[1] - s * 0.42 + hh + 0.3, top[2] + math.sin(a) * r), 1.6,
                     (255, 255, 255), parent=parent)
            collider(b, top, s * 0.7, 0, round_=True, parent=parent)
        else:
            cyl(b, "Stick", sub(top, (0, 34, 0)), 64, 3, (255, 255, 255), parent=parent)
            cyl(b, "Lolly", sub(top, (0, 2, 0)), 4, s, hsv(h, 0.6, 1.0), parent=parent, collide=True)
            for k in range(1, 5):
                ringz(b, (top[0], top[1] + 0.05, top[2]), s * 0.5 * k / 5, hsv(h + 0.15 * k, 0.4, 1.0), "SmoothPlastic",
                      th=0.15, parent=parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        n = max(1, int(round((x1 - x0) / 22)))
        q = (x1 - x0) / n
        for i in range(n):
            for j in (-1, 1):
                c = (x0 + q * (i + 0.5), y - 2.5, z + j * w / 4)
                part(b, "Choc", CF(c), (q - 1.6, 5, w / 2 - 1.6), (92, 56, 36), "SmoothPlastic", parent, True)
                part(b, "ChocTop", CF(add(c, (0, 2.55, 0))), (q - 4, 0.1, w / 2 - 4), (120, 76, 50), "SmoothPlastic", parent)
        part(b, "ChocBase", CF(((x0 + x1) / 2, y - 6, z)), (x1 - x0, 3, w), (70, 42, 28), "SmoothPlastic", parent, True)
        for k in range(int((x1 - x0) // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


class Burgers(World):
    key = "burger"

    def palette(self, v):
        tray = [(200, 40, 40), (40, 120, 200), (40, 160, 90), (240, 180, 40)][v % 4]
        return dict(body=tray, top=(214, 150, 70), edge=(255, 240, 200), pad=(255, 230, 80), danger=(255, 70, 40),
                    glass=(255, 240, 220), body_mat="SmoothPlastic", top_mat="SmoothPlastic", clock=14.5, bloom=0.3, hue=0.08)

    def plat(self, b, top, s, rng, parent=None):
        y = top[1]
        x, z = top[0], top[2]
        cyl(b, "BunBottom", (x, y - 26, z), 7, s * 0.9, (214, 150, 70), parent=parent)
        cyl(b, "Patty", (x, y - 19, z), 7, s * 0.98, (90, 52, 30), parent=parent)
        part(b, "Cheese", CF((x, y - 15, z)) * rot_y(math.pi / 4), (s * 0.82, 1.2, s * 0.82), (255, 200, 40), parent=parent)
        cyl(b, "Lettuce", (x, y - 13.5, z), 1.5, s * 1.04, (90, 190, 70), parent=parent)
        cyl(b, "Tomato", (x, y - 12, z), 2, s * 0.86, (220, 50, 40), parent=parent)
        ell(b, "BunTop", (x, y - 11, z), (s * 0.96, 22, s * 0.96), (214, 150, 70), parent=parent)
        for k in range(12):
            a = rng.random() * TAU
            r = rng.uniform(0.1, 0.42) * s
            hh = 11 * math.sqrt(max(0.0, 1 - (r / (s * 0.48)) ** 2))
            ell(b, "Sesame", (x + math.cos(a) * r, y - 11 + hh + 0.1, z + math.sin(a) * r), (1.6, 0.6, 1.0), (250, 240, 210),
                parent=parent, rot=rot_y(rng.random() * 3))
        collider(b, top, s * 0.75, 0, round_=True, parent=parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        straight_slab(b, x0, x1, y, z, w, pal["body"], "SmoothPlastic", 4, parent)
        for s in (-1, 1):
            part(b, "TrayRim", CF(((x0 + x1) / 2, y + 0.8, z + s * (w / 2 + 0.8))), (x1 - x0, 2.4, 1.6), mix(pal["body"], (0, 0, 0), 0.2),
                 parent=parent)
        n = int((x1 - x0) // 40)
        for k in range(n):
            part(b, "Paper", CF((x0 + 20 + k * 40, y + 0.05, z)), (30, 0.1, w * 0.7), (255, 246, 228), parent=parent)


class Islands(World):
    key = "islands"

    def palette(self, v):
        g = [(90, 170, 70), (120, 190, 80), (70, 150, 110), (150, 180, 60)][v % 4]
        return dict(body=(120, 90, 60), top=g, edge=(255, 240, 180), pad=(255, 200, 60), danger=(255, 70, 50),
                    glass=(220, 240, 255), body_mat="Slate", top_mat="Grass", clock=[11.5, 16.5, 8.5, 14][v % 4], bloom=0.3,
                    hue=0.3)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        x, y, z = top
        cyl(b, "Grass", (x, y - 1.5, z), 3, s, pal["top"], "Grass", parent, collide=True)
        cyl(b, "Dirt", (x, y - 7, z), 8, s * 0.96, (120, 84, 56), "Ground" if False else "Slate", parent)
        for k, (hh, f) in enumerate(((12, 0.8), (12, 0.55), (12, 0.3))):
            cyl(b, "Rock", (x, y - 11 - 12 * k - 6, z), hh, s * f, mix((110, 100, 92), (60, 54, 50), k / 2), "Slate", parent)
        a = rng.random() * TAU
        tx, tz = x + math.cos(a) * s * 0.36, z + math.sin(a) * s * 0.36
        cyl(b, "Trunk", (tx, y + 7, tz), 14, 2.4, (110, 76, 50), "Wood", parent)
        ell(b, "Canopy", (tx, y + 17, tz), (13, 11, 13), mix(pal["top"], (0, 60, 0), 0.3), "Grass", parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        n = max(1, int(round((x1 - x0) / 6.5)))
        q = (x1 - x0) / n
        for i in range(n):
            part(b, "Slat", CF((x0 + q * (i + 0.5), y - 0.6, z)), (q - 1.4, 1.2, w), (170, 124, 80), "WoodPlanks", parent, True)
        for s in (-1, 1):
            cyl(b, "Rope", ((x0 + x1) / 2, y + 4, z + s * (w / 2 - 0.5)), x1 - x0, 0.7, (200, 170, 120), "Fabric", parent,
                axis=(1, 0, 0))
            for k in range(int((x1 - x0) // 50) + 1):
                cyl(b, "Post", (x0 + k * 50, y + 2, z + s * (w / 2 - 0.5)), 6, 1.4, (110, 76, 50), "Wood", parent)
        for k in range(int((x1 - x0) // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


class Clouds(World):
    key = "clouds"

    def palette(self, v):
        h = [0.58, 0.85, 0.12, 0.5][v % 4]
        return dict(body=(255, 255, 255), top=(255, 255, 255), edge=hsv(h, 0.5, 1), pad=hsv(h + 0.4, 0.6, 1),
                    danger=(255, 80, 100), glass=(240, 250, 255), body_mat="SmoothPlastic", top_mat="SmoothPlastic",
                    clock=[12, 17.3, 7.5, 15][v % 4], bloom=0.45, hue=h)

    def plat(self, b, top, s, rng, parent=None):
        x, y, z = top
        ell(b, "Puff", (x, y - s * 0.18, z), (s * 0.8, s * 0.4, s * 0.8), (255, 255, 255), parent=parent)
        for k in range(6):
            a = TAU * k / 6 + rng.random() * 0.5
            r = s * rng.uniform(0.3, 0.42)
            d = s * rng.uniform(0.35, 0.5)
            ell(b, "Puff", (x + math.cos(a) * r, y - s * 0.22 - rng.uniform(0, 4), z + math.sin(a) * r), (d, d * 0.6, d),
                (250, 252, 255), parent=parent)
        collider(b, top, s * 0.78, 0, round_=True, parent=parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        cols = [(255, 70, 70), (255, 160, 50), (255, 230, 60), (80, 210, 90), (70, 150, 255), (150, 90, 230)]
        k = len(cols)
        for i, c in enumerate(cols):
            part(b, "Band", CF(((x0 + x1) / 2, y - 1.5, z - w / 2 + w * (i + 0.5) / k)), (x1 - x0, 3, w / k + 0.05), c,
                 "SmoothPlastic", parent, True)
        for e in (x0, x1):
            ell(b, "Puff", (e, y - 4, z), (w * 0.9, 14, w * 1.2), (255, 255, 255), parent=parent)
        for kk in range(int((x1 - x0) // 40) + 1):
            sample(b, (x0 + kk * 40, y, z), w)


class Crystals(World):
    key = "crystals"

    def palette(self, v):
        h = [0.75, 0.5, 0.92, 0.33][v % 4]
        return dict(body=(46, 42, 54), top=(70, 66, 80), edge=hsv(h, 0.7, 1), pad=hsv(h + 0.5, 0.7, 1), danger=(255, 60, 90),
                    glass=hsv(h, 0.3, 1), body_mat="Basalt", top_mat="Slate", clock=17.7, bloom=0.8, hue=h)

    def hexcol(self, b, top, s, h, parent, collide=True):
        for a in (0, math.pi / 3, 2 * math.pi / 3):
            part(b, "Column", CF(sub(top, (0, h / 2, 0))) * rot_y(a), (s, h, s / math.sqrt(3)), b.theme["body"], "Basalt", parent,
                 collide)
            part(b, "ColumnTop", CF(add(top, (0, 0.06, 0))) * rot_y(a), (s - 1.4, 0.12, s / math.sqrt(3) - 0.8), b.theme["top"],
                 "Slate", parent)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        self.hexcol(b, top, s, 70, parent)
        for k in range(rng.randint(2, 4)):
            a = rng.random() * TAU
            r = s * 0.8
            self.hexcol(b, (top[0] + math.cos(a) * r, top[1] - rng.uniform(10, 30), top[2] + math.sin(a) * r), s * 0.7, 60,
                        parent, collide=False)
        a = rng.random() * TAU
        g = (top[0] + math.cos(a) * s * 0.9, top[1] + 10, top[2] + math.sin(a) * s * 0.9)
        mesh(b, "gem", "Gem", CF(g) * rot_axis((1, 0.3, 0.2), rng.random() * 2), (10, 14, 10), pal["edge"], "Neon", parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        step = w * 0.86
        n = max(1, int(math.ceil((x1 - x0 - w) / step)) + 1)
        for k in range(n):
            cx = x0 + w / 2 + (x1 - x0 - w) * (k / (n - 1) if n > 1 else 0.5)
            self.hexcol(b, (cx, y, z), w, 26, parent)
            sample(b, (cx, y, z), w)


class Planets(World):
    key = "planets"

    def palette(self, v):
        h = [0.6, 0.05, 0.8, 0.45][v % 4]
        return dict(body=(40, 44, 60), top=(120, 126, 150), edge=hsv(h, 0.6, 1), pad=hsv(h + 0.5, 0.7, 1),
                    danger=(255, 70, 70), glass=hsv(h, 0.2, 1), body_mat="DiamondPlate", top_mat="Metal", clock=6.4,
                    bloom=0.9, hue=h)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        d = s * 1.3
        c = sub(top, (0, d / 2, 0))
        m = b.model("Planet", parent or b.roads, {"WallRide": True})
        h = rng.random()
        ball(b, "Planet", c, d, hsv(h, 0.45, 0.85), rng.choice(["SmoothPlastic", "Sand", "Slate"]), parent=m, collide=True)
        for k in range(2):
            ell(b, "Band", c, (d * 1.002, d * 0.12, d * 1.002), hsv(h + 0.08 * (k + 1), 0.5, 0.75), parent=m,
                rot=rot_axis((1, 0, 0), 0.0) if k == 0 else rot_axis((0, 0, 1), 0.0))
        tilt = rot_axis((1, 0, 0.3), 0.45)
        ring = mesh(b, "ring", "PlanetRing", CF(c, tilt.x, tilt.y, tilt.z), (d * 1.8, 1.2, d * 1.8), pal["edge"], "Neon", m)
        a = rng.random() * TAU
        ball(b, "Moon", add(c, (math.cos(a) * d, d * 0.2, math.sin(a) * d)), d * 0.18, (220, 220, 230), "Slate", parent=m)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        straight_slab(b, x0, x1, y, z, w, pal["top"], "DiamondPlate", 3, parent)
        for s in (-1, 1):
            part(b, "Light", CF(((x0 + x1) / 2, y + 0.3, z + s * (w / 2 - 1))), (x1 - x0, 0.5, 1), pal["edge"], "Neon", parent)
            part(b, "Truss", CF(((x0 + x1) / 2, y - 6, z + s * (w / 2 - 2))), (x1 - x0, 6, 2), pal["body"], "Metal", parent)
        for k in range(int((x1 - x0) // 30) + 1):
            part(b, "Rib", CF((x0 + k * 30, y - 6, z)), (2, 6, w - 2), pal["body"], "Metal", parent)


class LilyPond(World):
    key = "lily"

    def palette(self, v):
        g = [(70, 160, 80), (90, 180, 110), (60, 140, 100), (110, 170, 70)][v % 4]
        return dict(body=(60, 110, 70), top=g, edge=(255, 170, 210), pad=(255, 220, 80), danger=(255, 80, 80),
                    glass=(200, 240, 220), body_mat="Grass", top_mat="Grass", clock=9.5, bloom=0.35, hue=0.38)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        k = 12
        notch = rng.randrange(k)
        for i in range(k):
            if i == notch:
                continue
            a = TAU * (i + 0.5) / k
            dv = (math.cos(a), 0, math.sin(a))
            mid = add(top, mul(dv, s * 0.25))
            part(b, "Pad", deck_frame(sub(mid, (0, 1, 0)), dv), (s * math.sin(math.pi / k) * 1.04, 2, s * 0.5),
                 pal["top"], "Grass", parent, True)
            part(b, "Vein", deck_frame(add(mid, (0, 0.06, 0)), dv), (0.5, 0.1, s * 0.46), mix(pal["top"], (255, 255, 200), 0.4),
                 parent=parent)
        if rng.random() < 0.5:
            a = TAU * (notch + 6.5) / k
            fc = add(top, (math.cos(a) * s * 0.36, 2, math.sin(a) * s * 0.36))
            for j in range(8):
                pa = TAU * j / 8
                ell(b, "Petal", add(fc, (math.cos(pa) * 3, 1.5, math.sin(pa) * 3)), (7, 3, 3.4), (255, 170, 210), parent=parent,
                    rot=rot_y(-pa) * rot_axis((0, 0, 1), 0.5))
            ball(b, "Bud", add(fc, (0, 2, 0)), 3, (255, 230, 90), parent=parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        n = max(1, int(round((x1 - x0) / 5.5)))
        q = (x1 - x0) / n
        for i in range(n):
            cyl(b, "Bamboo", (x0 + q * (i + 0.5), y - q / 2, z), w, q, (196, 190, 110), "Wood", parent, collide=True,
                axis=(0, 0, 1))
        for s in (-0.3, 0.3):
            cyl(b, "Binding", ((x0 + x1) / 2, y - 0.4, z + s * w), x1 - x0, 1.2, (120, 90, 60), "Fabric", parent, axis=(1, 0, 0))
        for k in range(int((x1 - x0) // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


class Music(World):
    key = "music"

    def palette(self, v):
        shell = [(200, 30, 50), (30, 80, 200), (20, 20, 24), (230, 180, 40)][v % 4]
        return dict(body=shell, top=(246, 244, 236), edge=(255, 220, 120), pad=(120, 230, 255), danger=(255, 60, 60),
                    glass=(240, 240, 250), body_mat="SmoothPlastic", top_mat="SmoothPlastic", clock=17.8, bloom=0.7, hue=0.0)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        x, y, z = top
        cyl(b, "Skin", (x, y - 0.5, z), 1, s, (246, 244, 236), parent=parent, collide=True)
        cyl(b, "Shell", (x, y - 11, z), 20, s * 0.98, pal["body"], "Glass", parent)
        for hh in (y - 1.2, y - 20.5):
            cyl(b, "Hoop", (x, hh, z), 1.6, s + 1.0, (210, 214, 222), "Metal", parent)
        for k in range(8):
            a = TAU * k / 8
            cyl(b, "Rod", (x + math.cos(a) * (s / 2 + 0.5), y - 11, z + math.sin(a) * (s / 2 + 0.5)), 19, 0.8, (210, 214, 222),
                "Metal", parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        n = max(1, int(round((x1 - x0) / 7)))
        q = (x1 - x0) / n
        for i in range(n):
            part(b, "Key", CF((x0 + q * (i + 0.5), y - 3, z)), (q - 0.5, 6, w), (250, 250, 246), "SmoothPlastic", parent, True)
            if i % 7 not in (2, 6) and i < n - 1:
                part(b, "BlackKey", CF((x0 + q * (i + 1), y + 0.05, z - w * 0.18)), (q * 0.55, 0.1, w * 0.62), (20, 20, 24),
                     "SmoothPlastic", parent)
        part(b, "Case", CF(((x0 + x1) / 2, y - 8, z)), (x1 - x0, 6, w + 4), (20, 20, 24), "SmoothPlastic", parent)
        for k in range(int((x1 - x0) // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


class Toys(World):
    key = "toys"

    def palette(self, v):
        return dict(body=(230, 40, 40), top=(250, 210, 40), edge=(255, 255, 255), pad=(60, 200, 255), danger=(255, 60, 60),
                    glass=(240, 240, 255), body_mat="SmoothPlastic", top_mat="SmoothPlastic", clock=13.0, bloom=0.3, hue=0.0,
                    bricks=[[(230, 40, 40), (40, 110, 230), (250, 210, 40), (40, 170, 80)], [(255, 120, 180), (120, 220, 255),
                            (255, 240, 120), (180, 140, 255)], [(30, 30, 34), (240, 240, 240), (230, 40, 40), (90, 90, 96)],
                            [(255, 140, 30), (60, 200, 140), (250, 250, 250), (60, 90, 200)]][v % 4])

    def brick(self, b, top, sx, sz, h, col, parent, studs=True):
        part(b, "Brick", CF(sub(top, (0, h / 2, 0))), (sx, h, sz), col, "SmoothPlastic", parent, True)
        if studs:
            nx, nz = max(1, int(sx // 8)), max(1, int(sz // 8))
            for i in range(nx):
                for j in range(nz):
                    cyl(b, "Stud", (top[0] - sx / 2 + sx * (i + 0.5) / nx, top[1] + 0.5, top[2] - sz / 2 + sz * (j + 0.5) / nz), 1,
                        min(sx / nx, sz / nz) * 0.6, col, "SmoothPlastic", parent)

    def plat(self, b, top, s, rng, parent=None):
        col = rng.choice(b.theme["bricks"])
        self.brick(b, top, s, s, s * 0.6, col, parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        cols = b.theme["bricks"]
        n = max(1, int(round((x1 - x0) / 32)))
        q = (x1 - x0) / n
        for i in range(n):
            self.brick(b, (x0 + q * (i + 0.5), y, z), q - 0.4, w, 9, cols[i % len(cols)], parent, studs=(i % 2 == 0))
        for k in range(int((x1 - x0) // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


class Clocks(World):
    key = "clocks"

    def palette(self, v):
        face = [(246, 238, 220), (30, 30, 36), (230, 240, 250), (250, 230, 210)][v % 4]
        ink = (40, 34, 30) if v % 4 != 1 else (240, 220, 160)
        return dict(body=(200, 160, 70), top=face, edge=(255, 210, 110), pad=(90, 220, 255), danger=(255, 60, 50),
                    glass=(240, 240, 250), body_mat="Metal", top_mat="SmoothPlastic", clock=16.5, bloom=0.5, hue=0.11, ink=ink)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        x, y, z = top
        cyl(b, "Face", (x, y - 2, z), 4, s, pal["top"], parent=parent, collide=True)
        cyl(b, "Bezel", (x, y - 3, z), 5, s + 2.4, pal["body"], "Metal", parent)
        for k in range(12):
            a = TAU * k / 12
            part(b, "Mark", CF((x + math.cos(a) * s * 0.42, y + 0.05, z + math.sin(a) * s * 0.42)) * rot_y(-a),
                 (s * (0.08 if k % 3 else 0.12), 0.1, 1.2), pal["ink"], parent=parent)
        root = b.prop_root("Hands")
        rig = b.rig(root, "Spin", axis_frame((x, y + 0.2, z), UP), rng.choice([0.05, 0.08]), 4, phase=rng.random(), name="Hand")
        part(b, "Hand", CF((x + s * 0.18, y + 0.15, z)), (s * 0.38, 0.1, 1.6), pal["ink"], parent=rig)
        part(b, "HandShort", CF((x, y + 0.18, z + s * 0.12)), (1.6, 0.1, s * 0.26), pal["ink"], parent=rig)
        cyl(b, "Pin", (x, y + 0.2, z), 0.2, 3, pal["body"], "Metal", parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        straight_slab(b, x0, x1, y, z, w, pal["body"], "Metal", 4, parent)
        for s in (-1, 1):
            for k in range(int((x1 - x0) // 9)):
                part(b, "Tooth", CF((x0 + 4.5 + k * 9, y - 2, z + s * (w / 2 + 1.5))), (4.5, 4, 3), pal["body"], "Metal", parent)
        part(b, "Inlay", CF(((x0 + x1) / 2, y + 0.05, z)), (x1 - x0 - 4, 0.1, w * 0.4), pal["top"], parent=parent)


class Snow(World):
    key = "snow"

    def palette(self, v):
        h = [0.55, 0.6, 0.5, 0.7][v % 4]
        return dict(body=(170, 210, 240), top=(236, 248, 255), edge=hsv(h, 0.5, 1), pad=hsv(h + 0.5, 0.6, 1),
                    danger=(255, 70, 110), glass=(220, 240, 255), body_mat="Ice", top_mat="Glacier", clock=10.5, bloom=0.5, hue=h)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        for a in (0, math.pi / 3, 2 * math.pi / 3):
            part(b, "Core", CF(sub(top, (0, 2, 0))) * rot_y(a), (s * 0.5, 4, s * 0.5 / math.sqrt(3)), pal["top"], "Glacier",
                 parent, True)
        for k in range(6):
            a = TAU * k / 6
            f = (math.cos(a), 0, math.sin(a))
            part(b, "Arm", deck_frame(sub(add(top, mul(f, s * 0.36)), (0, 1.5, 0)), f), (s * 0.13, 3, s * 0.5), pal["body"],
                 "Ice", parent, True)
            for sgn in (-1, 1):
                g = unit(add(f, mul((-f[2], 0, f[0]), sgn * 0.9)))
                part(b, "Branch", deck_frame(sub(add(top, add(mul(f, s * 0.4), mul(g, s * 0.07))), (0, 1.4, 0)), g),
                     (s * 0.06, 2.4, s * 0.16), pal["body"], "Ice", parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        straight_slab(b, x0, x1, y, z, w, pal["top"], "Glacier", 6, parent)
        import random
        r = random.Random(int(x0 * 7 + z))
        for k in range(int((x1 - x0) // 30)):
            a = r.uniform(-0.6, 0.6)
            part(b, "Crack", CF((x0 + 15 + k * 30, y + 0.05, z + r.uniform(-w / 4, w / 4))) * rot_y(a), (14, 0.1, 0.5),
                 (255, 255, 255), parent=parent)


class Golf(World):
    key = "golf"

    def palette(self, v):
        track = [(200, 70, 60), (60, 110, 200), (40, 140, 90), (120, 70, 170)][v % 4]
        return dict(body=track, top=(90, 180, 80), edge=(255, 255, 255), pad=(255, 220, 60), danger=(255, 70, 70),
                    glass=(240, 255, 240), body_mat="SmoothPlastic", top_mat="Grass", clock=12.5, bloom=0.25, hue=0.33)

    def plat(self, b, top, s, rng, parent=None):
        x, y, z = top
        cyl(b, "Green", (x, y - 2, z), 4, s, (90, 180, 80), "Grass", parent, collide=True)
        cyl(b, "Fringe", (x, y - 2.6, z), 4, s + 6, (60, 140, 60), "Grass", parent)
        cyl(b, "Sand", (x, y - 8, z), 8, s * 0.9, (230, 210, 160), "Sand", parent)
        a = rng.random() * TAU
        hx, hz = x + math.cos(a) * s * 0.3, z + math.sin(a) * s * 0.3
        cyl(b, "Cup", (hx, y + 0.06, hz), 0.12, 3, (20, 20, 20), parent=parent)
        cyl(b, "Pin", (hx, y + 9, hz), 18, 0.5, (250, 250, 250), parent=parent)
        part(b, "Flag", CF((hx + 2.5, y + 16, hz)), (5, 3.5, 0.2), (230, 40, 40), parent=parent)
        ball(b, "GolfBall", (x - math.cos(a) * s * 0.2, y + 0.9, z - math.sin(a) * s * 0.2), 1.8, (255, 255, 255), parent=parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        straight_slab(b, x0, x1, y, z, w, pal["body"], "SmoothPlastic", 4, parent)
        for k in range(1, 4):
            part(b, "Lane", CF(((x0 + x1) / 2, y + 0.05, z - w / 2 + w * k / 4)), (x1 - x0, 0.1, 0.6), (255, 255, 255),
                 parent=parent)
        for s in (-1, 1):
            part(b, "Curb", CF(((x0 + x1) / 2, y + 0.05, z + s * (w / 2 - 0.6))), (x1 - x0, 0.12, 1.2), (255, 255, 255),
                 parent=parent)


class Satellites(World):
    key = "satellites"

    def palette(self, v):
        h = [0.6, 0.12, 0.75, 0.5][v % 4]
        return dict(body=(210, 170, 70), top=(40, 70, 140), edge=hsv(h, 0.6, 1), pad=hsv(h + 0.5, 0.7, 1),
                    danger=(255, 70, 70), glass=hsv(h, 0.2, 1), body_mat="Foil", top_mat="Glass", clock=6.5, bloom=0.8, hue=h)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        x, y, z = top
        part(b, "Core", CF((x, y - 6, z)), (s * 0.34, 12, s * 0.34), pal["body"], "Foil", parent, True)
        for sgn in (-1, 1):
            c = (x, y - 0.6, z + sgn * s * 0.34)
            part(b, "Panel", CF(c), (s * 0.7, 1.2, s * 0.34), pal["top"], "Glass", parent, True)
            for k in range(1, 4):
                part(b, "Cell", CF((x - s * 0.35 + s * 0.7 * k / 4, y + 0.05, c[2])), (0.4, 0.1, s * 0.33), pal["edge"], "Neon",
                     parent)
        ell(b, "Dish", (x, y - 16, z), (s * 0.3, 4, s * 0.3), (230, 230, 236), "SmoothPlastic", parent)
        cyl(b, "Mast", (x, y - 12, z), 6, 1, (200, 200, 210), "Metal", parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        L = x1 - x0
        cx = (x0 + x1) / 2
        mesh(b, "rounded", "Module", CF((cx, y - w * 0.17, z)), (L, w * 0.34, w * 1.05), (220, 222, 228), "SmoothPlastic", parent)
        part(b, "Floor", CF((cx, y - 1, z)), (L, 2, w * 0.8), (220, 222, 228), parent=parent, collide=True, transp=1.0)
        for s in (-1, 1):
            part(b, "Windows", CF((cx, y - w * 0.12, z + s * w * 0.52)), (L * 0.9, 2, 0.4), pal["edge"], "Neon", parent)
        for k in range(int(L // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


class Circuits(World):
    key = "circuits"

    def palette(self, v):
        board = [(20, 110, 60), (20, 50, 110), (110, 20, 50), (30, 30, 34)][v % 4]
        return dict(body=board, top=(24, 24, 28), edge=(255, 200, 60), pad=(90, 255, 200), danger=(255, 60, 60),
                    glass=(200, 255, 230), body_mat="SmoothPlastic", top_mat="SmoothPlastic", clock=17.6, bloom=0.8, hue=0.35)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        x, y, z = top
        part(b, "Chip", CF((x, y - 3, z)), (s, 6, s), (24, 24, 28), parent=parent, collide=True)
        n = max(3, int(s // 7))
        for sgn in (-1, 1):
            for k in range(n):
                off = -s / 2 + s * (k + 0.5) / n
                part(b, "Pin", CF((x + off, y - 4, z + sgn * (s / 2 + 1.5))), (1.6, 1, 3), (200, 200, 210), "Metal", parent)
                part(b, "Pin", CF((x + sgn * (s / 2 + 1.5), y - 4, z + off)), (3, 1, 1.6), (200, 200, 210), "Metal", parent)
        cyl(b, "Dot", (x - s * 0.36, y + 0.06, z - s * 0.36), 0.1, 2.4, (90, 90, 96), parent=parent)
        part(b, "Label", CF((x, y + 0.06, z)), (s * 0.5, 0.1, 1.2), (200, 200, 200), parent=parent)
        for k in range(3):
            part(b, "Trace", CF((x, y + 0.07, z - s * 0.25 + k * s * 0.25)) * rot_y(math.pi / 2 * (k % 2)), (s * 0.8, 0.1, 0.5),
                 pal["pad"], "Neon", parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        straight_slab(b, x0, x1, y, z, w, pal["body"], "SmoothPlastic", 3, parent)
        import random
        r = random.Random(int(x0 * 3 + z))
        for k in range(int((x1 - x0) // 22)):
            zz = z + r.uniform(-w / 2 + 3, w / 2 - 3)
            part(b, "Trace", CF((x0 + 11 + k * 22, y + 0.05, zz)), (18, 0.1, 0.7), pal["edge"], "Neon", parent)
            if r.random() < 0.4:
                part(b, "Resistor", CF((x0 + 11 + k * 22, y + 0.6, z + (w / 2 - 2) * r.choice([-1, 1]))), (4, 1.2, 1.4),
                     (220, 200, 160), parent=parent)


class Ruins(World):
    key = "ruins"

    def palette(self, v):
        stone = [(236, 230, 214), (214, 200, 180), (200, 206, 214), (240, 220, 200)][v % 4]
        return dict(body=stone, top=stone, edge=(255, 210, 90), pad=(90, 210, 255), danger=(255, 70, 50),
                    glass=(240, 240, 240), body_mat="Marble", top_mat="Marble", clock=17.0, bloom=0.35, hue=0.11)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        x, y, z = top
        part(b, "Capital", CF((x, y - 2.5, z)), (s, 5, s), pal["top"], "Marble", parent, True)
        part(b, "Echinus", CF((x, y - 6.5, z)), (s * 0.82, 3, s * 0.82), pal["body"], "Marble", parent)
        cyl(b, "Shaft", (x, y - 40, z), 64, s * 0.6, pal["body"], "Marble", parent)
        for k in range(10):
            a = TAU * k / 10
            part(b, "Flute", CF((x + math.cos(a) * s * 0.3, y - 40, z + math.sin(a) * s * 0.3)) * rot_y(-a), (1.2, 62, 2.4),
                 mix(pal["body"], (0, 0, 0), 0.1), "Marble", parent)
        part(b, "Plinth", CF((x, y - 74, z)), (s * 0.85, 4, s * 0.85), pal["body"], "Marble", parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        straight_slab(b, x0, x1, y, z, w, pal["top"], "Marble", 6, parent)
        for s in (-1, 1):
            for k in range(int((x1 - x0) // 6)):
                part(b, "Dentil", CF((x0 + 3 + k * 6, y - 7.5, z + s * (w / 2 - 1))), (3.2, 3, 2.2), pal["body"], "Marble", parent)


class Ocean(World):
    key = "ocean"

    def palette(self, v):
        buoy = [(220, 50, 40), (250, 200, 40), (40, 120, 220), (250, 130, 40)][v % 4]
        return dict(body=(150, 110, 76), top=(196, 160, 116), edge=(255, 255, 255), pad=(70, 230, 230), danger=(255, 70, 50),
                    glass=(200, 240, 255), body_mat="WoodPlanks", top_mat="WoodPlanks", clock=12.0, bloom=0.3, hue=0.52,
                    buoy=buoy)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        x, y, z = top
        cyl(b, "BuoyDeck", (x, y - 1, z), 2, s * 0.8, (240, 240, 240), parent=parent, collide=True)
        ell(b, "Buoy", (x, y - s * 0.25, z), (s, s * 0.55, s), pal["buoy"], parent=parent)
        cyl(b, "Band", (x, y - s * 0.25, z), s * 0.12, s * 1.005, (255, 255, 255), parent=parent)
        a = rng.random() * TAU
        lx, lz = x + math.cos(a) * s * 0.3, z + math.sin(a) * s * 0.3
        cyl(b, "LampPost", (lx, y + 5, lz), 10, 1.2, (60, 60, 66), "Metal", parent)
        ball(b, "Lamp", (lx, y + 10.5, lz), 3, (255, 240, 160), "Neon", parent)
        ringz(b, (x, y - s * 0.52, z), s * 0.36, (255, 255, 255), "SmoothPlastic", th=2.4, parent=parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        n = max(1, int(round((x1 - x0) / 5)))
        q = (x1 - x0) / n
        for i in range(n):
            part(b, "Plank", CF((x0 + q * (i + 0.5), y - 0.8, z)), (q - 0.6, 1.6, w),
                 (196, 160, 116) if i % 3 else (176, 140, 100), "WoodPlanks", parent, True)
        for k in range(int((x1 - x0) // 40) + 1):
            for s in (-1, 1):
                cyl(b, "Piling", (x0 + k * 40, y - 20, z + s * (w / 2 - 1.5)), 40, 3, (110, 80, 56), "Wood", parent)
            sample(b, (x0 + k * 40, y, z), w)
        for s in (-1, 1):
            cyl(b, "Rope", ((x0 + x1) / 2, y + 3, z + s * (w / 2 - 1.5)), x1 - x0, 0.6, (230, 210, 160), "Fabric", parent,
                axis=(1, 0, 0))


class Desert(World):
    key = "desert"

    def palette(self, v):
        return dict(body=(200, 130, 80), top=(226, 180, 120), edge=(255, 220, 140), pad=(90, 210, 255), danger=(255, 70, 50),
                    glass=(255, 240, 220), body_mat="Sandstone", top_mat="Sandstone", clock=[16.8, 13.5, 17.6, 8.0][v % 4],
                    bloom=0.3, hue=0.07)

    def plat(self, b, top, s, rng, parent=None):
        x, y, z = top
        for k, (h, f, c) in enumerate(((6, 1.0, (226, 180, 120)), (10, 0.92, (200, 130, 80)), (10, 0.82, (214, 156, 100)),
                                        (14, 0.66, (180, 110, 70)))):
            part(b, "Strata", CF((x, y - [3, 11, 21, 33][k], z)) * rot_y(k * 0.2), (s * f, h, s * f * 0.9), c, "Sandstone", parent,
                 k == 0)
        a = rng.random() * TAU
        cx_, cz_ = x + math.cos(a) * s * 0.36, z + math.sin(a) * s * 0.36
        cyl(b, "Cactus", (cx_, y + 7, cz_), 14, 3, (70, 130, 60), "Grass", parent)
        cyl(b, "CactusArm", (cx_ + 2.5, y + 9, cz_), 6, 2, (70, 130, 60), "Grass", parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        straight_slab(b, x0, x1, y, z, w, (226, 180, 120), "Sandstone", 5, parent)
        for k, c in enumerate(((200, 130, 80), (214, 156, 100), (180, 110, 70))):
            part(b, "Layer", CF(((x0 + x1) / 2, y - 8 - k * 5, z)), (x1 - x0, 5, w * (0.95 - 0.12 * k)), c, "Sandstone", parent)


class Volcano(World):
    key = "volcano"

    def palette(self, v):
        glow = [(255, 110, 20), (255, 60, 40), (255, 170, 30), (200, 60, 255)][v % 4]
        return dict(body=(30, 26, 26), top=(48, 40, 38), edge=glow, pad=(90, 220, 255), danger=(255, 230, 60),
                    glass=(255, 200, 160), body_mat="Basalt", top_mat="Basalt", clock=17.9, bloom=0.9, hue=0.05)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        x, y, z = top
        part(b, "Rock", CF((x, y - 4, z)) * rot_y(rng.random()), (s, 8, s * 0.9), pal["top"], "Basalt", parent, True)
        for k in range(3):
            r = rot_y(rng.random() * 3) * rot_axis((1, 0, 0.3), rng.uniform(0.2, 0.6))
            part(b, "Chunk", CF((x + rng.uniform(-6, 6), y - 14 - k * 6, z + rng.uniform(-6, 6)), r.x, r.y, r.z),
                 (s * (0.8 - 0.15 * k), 14, s * (0.7 - 0.12 * k)), pal["body"], "Basalt", parent)
        for k in range(4):
            a = rng.random() * TAU
            part(b, "Crack", CF((x + math.cos(a) * s * 0.2, y + 0.05, z + math.sin(a) * s * 0.2)) * rot_y(a),
                 (s * 0.35, 0.1, 0.8), pal["edge"], "Neon", parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        pal = b.theme
        n = max(1, int(round((x1 - x0) / 26)))
        q = (x1 - x0) / n
        for i in range(n):
            part(b, "Basalt", CF((x0 + q * (i + 0.5), y - 4, z)), (q - 1.2, 8, w), pal["top"], "Basalt", parent, True)
            part(b, "Seam", CF((x0 + q * (i + 1), y - 5, z)), (1.2, 8, w), pal["edge"], "Neon", parent)
        for k in range(int((x1 - x0) // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


class Arcade(World):
    key = "arcade"

    def palette(self, v):
        return dict(body=(170, 90, 40), top=(200, 120, 60), edge=(255, 230, 60), pad=(60, 220, 255), danger=(255, 50, 80),
                    glass=(240, 240, 255), body_mat="SmoothPlastic", top_mat="SmoothPlastic", clock=17.85, bloom=1.0,
                    hue=[0.12, 0.9, 0.55, 0.3][v % 4])

    def plat(self, b, top, s, rng, parent=None):
        x, y, z = top
        cyl(b, "Coin", (x, y - 2.5, z), 5, s, (255, 200, 40), "Metal", parent, collide=True)
        cyl(b, "CoinRim", (x, y - 2.5, z), 5.4, s + 1.6, (230, 160, 20), "Metal", parent)
        for k in range(5):
            a = TAU * k / 5 - math.pi / 2
            part(b, "Star", CF((x + math.cos(a) * s * 0.12, y + 0.06, z + math.sin(a) * s * 0.12)) * rot_y(-a),
                 (s * 0.3, 0.1, s * 0.08), (255, 240, 140), parent=parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        n = max(1, int(round((x1 - x0) / 16)))
        q = (x1 - x0) / n
        for i in range(n):
            for j in range(2):
                off = q / 2 if j % 2 else 0
                c = (x0 + q * (i + 0.5), y - 4, z - w / 4 + j * w / 2)
                part(b, "Brick", CF(c), (q - 1, 8, w / 2 - 1), (196, 104, 50), "SmoothPlastic", parent, True)
        part(b, "Mortar", CF(((x0 + x1) / 2, y - 4.5, z)), (x1 - x0, 7, w - 0.5), (60, 30, 20), "SmoothPlastic", parent)
        for k in range(int((x1 - x0) // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


class Bakery(World):
    key = "bakery"

    def palette(self, v):
        icing = [(255, 190, 210), (200, 230, 255), (255, 240, 200), (220, 200, 255)][v % 4]
        return dict(body=(250, 240, 230), top=icing, edge=(255, 255, 255), pad=(255, 120, 160), danger=(255, 60, 90),
                    glass=(255, 240, 250), body_mat="SmoothPlastic", top_mat="SmoothPlastic", clock=14.0, bloom=0.3, hue=0.95)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        x, y, z = top
        cyl(b, "TierTop", (x, y - 6, z), 12, s * 0.9, pal["top"], parent=parent, collide=True)
        cyl(b, "TierLow", (x, y - 20, z), 16, s * 1.15, pal["body"], parent=parent)
        for k in range(14):
            a = TAU * k / 14
            ell(b, "Drip", (x + math.cos(a) * s * 0.45, y - 2 - (k % 3) * 1.5, z + math.sin(a) * s * 0.45), (4, 6 + (k % 3) * 2, 4),
                (255, 255, 255), parent=parent)
        for k in range(5):
            a = TAU * k / 5 + 0.3
            ball(b, "Cherry", (x + math.cos(a) * s * 0.38, y + 1.8, z + math.sin(a) * s * 0.38), 3.4, (210, 20, 40), parent=parent)
        ringz(b, (x, y - 12.5, z), s * 0.56, (255, 255, 255), "SmoothPlastic", th=2, parent=parent)
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        straight_slab(b, x0, x1, y, z, w, (230, 190, 130), "SmoothPlastic", 6, parent)
        for k in range(int((x1 - x0) // 6)):
            part(b, "Grid", CF((x0 + 3 + k * 6, y + 0.05, z)), (0.6, 0.1, w - 2), (200, 150, 90), parent=parent)
        for s in (-1, 1):
            part(b, "Cream", CF(((x0 + x1) / 2, y - 3, z + s * (w / 2 + 0.3))), (x1 - x0, 2, 0.6), (255, 250, 240), parent=parent)


class Garden(World):
    key = "garden"

    def palette(self, v):
        petal = [(255, 120, 160), (255, 220, 60), (170, 120, 255), (255, 140, 60)][v % 4]
        return dict(body=(70, 140, 60), top=(255, 220, 80), edge=(255, 255, 255), pad=(90, 200, 255), danger=(255, 70, 70),
                    glass=(230, 255, 230), body_mat="Grass", top_mat="SmoothPlastic", clock=10.0, bloom=0.3, hue=0.3, petal=petal)

    def plat(self, b, top, s, rng, parent=None):
        pal = b.theme
        x, y, z = top
        cyl(b, "Centre", (x, y - 1.5, z), 3, s * 0.42, (255, 210, 60), parent=parent, collide=True)
        for k in range(8):
            a = TAU * k / 8
            ell(b, "Petal", (x + math.cos(a) * s * 0.33, y - 1.6, z + math.sin(a) * s * 0.33), (s * 0.42, 3, s * 0.2),
                pal["petal"], parent=parent, rot=rot_y(-a))
        collider(b, top, s * 0.9, 0, round_=True, parent=parent)
        cyl(b, "Stem", (x, y - 30, z), 56, 3, (70, 140, 60), "Grass", parent)
        ell(b, "Leaf", (x + 7, y - 36, z), (14, 1.6, 6), (90, 170, 70), "Grass", parent, rot=rot_axis((0, 0, 1), -0.4))
        sample(b, top, s)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L = x1 - x0
        n = max(1, int(round(L / (w * 1.6))))
        q = L / n
        for i in range(n):
            c = (x0 + q * (i + 0.5), y - 1.2, z)
            ell(b, "Leaf", c, (q * 1.1, 2.4, w * 1.05), (90, 170, 70), "Grass", parent)
            part(b, "Rib", CF(add(c, (0, 1.1, 0))), (q * 0.9, 0.2, 0.8), (150, 210, 110), parent=parent)
        part(b, "Floor", CF(((x0 + x1) / 2, y - 1, z)), (L, 2, w * 0.75), (255, 255, 255), parent=parent, collide=True,
             transp=1.0)
        for k in range(int(L // 40) + 1):
            sample(b, (x0 + k * 40, y, z), w)


WORLDS = [Mushrooms(), Chess(), Dice(), Gears(), Candy(), Burgers(), Islands(), Clouds(), Crystals(), Planets(),
          LilyPond(), Music(), Toys(), Clocks(), Snow(), Golf(), Satellites(), Circuits(), Ruins(), Ocean(), Desert(),
          Volcano(), Arcade(), Bakery(), Garden()]
