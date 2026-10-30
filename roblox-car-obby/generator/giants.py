"""Obby 3, Giant Worlds: levels 31-40 (the game's course 4). The car is shrunk down and races across enormous things.

No ordinary roads: every driving surface is a giant object (a countertop, a plate, a toy block, a mushroom cap, a
ship's deck) and every jump goes from one object to the next. Each level is its own little world with its own
shapes, colours, light and machines, built with the game's existing systems (launch pads, bounce caps, prop rigs,
clock rotors, sinking tiles, brick walls, crane and beam rides, coins on CoinSpot parts).

How it is put together:
- The route turtle (route.py, obby.py, rush2.py) lays the line, the jumps and the checkpoints, exactly as in Obby 1
  and 2, so the validator flies every jump.
- The skin draws each stretch it lays with the current *surface* (look(): countertop, chopping board, plate, ...).
  A ghost surface is an invisible floor: the object built round it (a round plate, a mushroom cap) is the visible
  top, flush with it.
- Object art (the cabinet under a counter, the toaster round a launch pad) is built after the stretch is laid,
  from the stretch's own points (span()).
"""
import math
import random
from contextlib import contextmanager
from geom import CF, deck_frame, axis_frame, add, sub, mul, unit, cross, dot, rot_y, rot_axis, UP
from builder import G, CAR_UP, X0, Y0, ZC
import route as RT
import rush2 as R2
import obby as O
import mech as MX
import epic_marks as M
from skins import Skin, Pt, box, cyl, ball, samples
from worlds import ringz
import journey_skins  # noqa: F401  (road_piece etc. on the base skin)

TAU = math.pi * 2
WHITE, BLACK = (245, 245, 242), (24, 24, 28)
CHROME, CHROME_DK = (196, 202, 212), (120, 126, 138)
GOLD = (255, 200, 60)


# ===================================================================== geometry helpers
def right_of(f):
    return mul(RT.left_of(f), -1)


def axes(f):
    """(left, up, f) for a flat heading: a part's size is (across, up, along)."""
    f = unit((f[0], 0.0, f[2]))
    x = unit(cross(UP, f))
    return (x, cross(f, x), f)


def ob(b, name, c, f, size, col, mat="SmoothPlastic", parent=None, **kw):
    """A box at c, turned to heading f: size = (across, up, along)."""
    return Pt(b, name, CF(c, *axes(f)), size, col, mat, parent if parent is not None else b.scenery, **kw)


def F(fr, p):
    return CF(p, fr.x, fr.y, fr.z)


def off(fr, x=0.0, y=0.0, z=0.0):
    return add(fr.p, add(add(mul(fr.x, x), mul(fr.y, y)), mul(fr.z, z)))


def span(r):
    """The stretch just laid: (start, end, flat heading, plan length, width at its start, points)."""
    pts, ws, _ = r.last
    p0, p1 = pts[0], pts[-1]
    f = RT.flat(sub(p1, p0))
    L = sum(math.hypot(c[0] - a[0], c[2] - a[2]) for a, c in zip(pts, pts[1:]))
    return p0, p1, f, L, ws[0], pts


def at(r, d):
    """(point, heading) d along the stretch just laid."""
    return MX.at_road(r, d)


def mix(a, c, t):
    return tuple(int(a[i] + (c[i] - a[i]) * t) for i in range(3))


def coin(b, p):
    b.part("CoinSpot", CF(p), (2, 2, 2), (255, 206, 66), parent=b.scenery, transp=1, collide=False, query=False,
           attrs={"CoinSpot": True})


def coin_row(b, p0, p1, n=5, up=5.0):
    for k in range(n):
        q = R2.lerp3(p0, p1, (k + 0.5) / n)
        coin(b, add(q, (0, up, 0)))


def coin_arc(b, j=-1, n=6):
    """Coins along the nominal flight of the last recorded jump."""
    kind, lip, tgt, H, V = b.jumps[j]
    f = RT.flat(sub(tgt, lip))
    dy = tgt[1] - lip[1]
    T = (V + math.sqrt(max(V * V + 2 * G * dy, 0.0))) / G
    for k in range(n):
        t = T * (0.2 + 0.6 * k / max(n - 1, 1))
        coin(b, add(lip, add(mul(f, H * t), (0, V * t - G * t * t / 2 + CAR_UP + 2, 0))))


# ===================================================================== surfaces
def slab(top, mat, th=4.0, side=None, side_mat=None, refl=0.0, deco=None, transp=0.0):
    """A surface: a solid top th thick (its top is the road), optional pattern deco(sk, b, parent, fr, w, L)."""
    def draw(sk, b, parent, fr, w, L, name):
        # (the solid top is always 4 thick, as the road's mitred bend fills expect; a thicker look hangs under it)
        Pt(b, name, F(fr, off(fr, y=-2.0)), (w, 4.0, L), top, mat, parent, collide=True, refl=refl, transp=transp)
        if th > 4.0:
            Pt(b, "SlabBody", F(fr, off(fr, y=-4.0 - (th - 4.0) / 2)), (w, th - 4.0, L), side or top, side_mat or mat, parent)
        if side is not None:
            for k in (-1, 1):
                Pt(b, "SlabSide", F(fr, off(fr, x=k * (w / 2 + 0.3), y=-th / 2)), (0.6, th + 0.2, L), side,
                   side_mat or mat, parent)
        if deco:
            deco(sk, b, parent, fr, w, L)
    return draw


def by_name(table, default):
    """A surface chosen by the piece's name: a kicker is laid as "Ramp", a road as "Deck"."""
    def draw(sk, b, parent, fr, w, L, name):
        table.get(name, default)(sk, b, parent, fr, w, L, name)
    return draw


def ghost(sk, b, parent, fr, w, L, name):
    """An invisible floor: the object built round it is what you see (flush with it)."""
    Pt(b, "Floor", F(fr, off(fr, y=-1.0)), (w, 2.0, L), (255, 255, 255), "SmoothPlastic", parent, collide=True, transp=1.0)


def lines_along(col, every, th=0.12, width=0.6, mat="SmoothPlastic", name="Seam", inset=0.0):
    """Seams running along a surface (planks, tiles)."""
    def deco(sk, b, parent, fr, w, L):
        n = int((w - 2 * inset) // every)
        for i in range(1, n + 1):
            x = -w / 2 + inset + i * every
            if abs(x) < w / 2 - 1:
                Pt(b, name, F(fr, off(fr, x=x, y=0.06)), (width, th, L), col, mat, parent)
    return deco


def lines_across(col, every, th=0.12, width=0.6, mat="SmoothPlastic", name="Seam"):
    def deco(sk, b, parent, fr, w, L):
        d = -L / 2 + every / 2
        while d < L / 2 - 1:
            Pt(b, name, F(fr, off(fr, z=d, y=0.06)), (w - 0.4, th, width), col, mat, parent)
            d += every
    return deco


def edges(col, mat="SmoothPlastic", width=1.4, name="Trim"):
    def deco(sk, b, parent, fr, w, L):
        for k in (-1, 1):
            Pt(b, name, F(fr, off(fr, x=k * (w / 2 - width / 2), y=0.07)), (width, 0.14, L), col, mat, parent)
    return deco


def both(*decos):
    def deco(sk, b, parent, fr, w, L):
        for d in decos:
            d(sk, b, parent, fr, w, L)
    return deco


# ===================================================================== the skin
class Giant(Skin):
    key, title, theme_name = "giant", "Giant Worlds", "Giant worlds"
    clock, bloom, hue, scale = 12.0, 0.4, 0.08, 1.0
    body, top, edge, padc, danger = (90, 90, 100), (230, 230, 230), GOLD, (90, 220, 255), (255, 60, 50)
    body_mat, top_mat = "SmoothPlastic", "SmoothPlastic"
    gate_post, gate_board, gate_text = (60, 60, 70), (30, 30, 36), GOLD
    finish_cols = ((245, 245, 245), (24, 24, 28))
    light_over = {}
    surface = None
    under_fn = None
    plat_fn = None
    pad_fn = None
    rail_style = None

    def road_style(self):
        s = self.rail_style or {}
        return dict(top=self.top, top_mat=self.top_mat, edge=s.get("edge", self.edge), edge_mat=s.get("edge_mat", "Neon"),
                    side=s.get("side", self.body), side_mat=s.get("side_mat", self.body_mat), refl=0.0, center=None)

    def road_piece(self, b, parent, fr, w, L, name):
        (self.surface or self.base_surface())(self, b, parent, fr, w, L, name)

    def base_surface(self):
        return slab(self.top, self.top_mat)

    def under(self, b, top, w, i):
        if self.under_fn:
            self.under_fn(self, b, top, w, i)

    def deck(self, b, x0, x1, y, z, w, parent=None):
        L, cx = x1 - x0, (x0 + x1) / 2
        self.road_piece(b, parent or b.roads, deck_frame((cx, y, z), (1, 0, 0)), w, L, "Deck")
        samples(b, x0, x1, y, z, w)
        if getattr(self, "deck_art", None):
            self.deck_art(b, (x0, y, z), (x1, y, z), w)

    def supports(self, b, x0, x1, y, z, w):
        pass

    def plat(self, b, top, s, rng, parent=None):
        if self.plat_fn:
            return self.plat_fn(self, b, top, s, rng)
        cyl(b, "Platform", sub(top, (0, 4, 0)), 8, s, self.top, self.top_mat, collide=True)
        b.samples.append((top[0], top[1], top[2], s))

    def pad_art(self, b, start, f):
        if self.pad_fn:
            return self.pad_fn(self, b, start, f)
        fr = deck_frame(add(start, (0, 0.1, 0)), f)
        for k in range(3):
            q = add(start, mul(f, -8 + k * 8))
            Pt(b, "PadChevron", CF(add(q, (0, 0.2, 0)), fr.x, fr.y, fr.z), (16, 0.2, 3), self.padc, "Neon")

    def finish(self, b, x0, x1, y, z, w):
        if getattr(b, "final_slot", False):
            Skin.finish(self, b, x0, x1, y, z, w)

    def environment(self, b):
        pass


@contextmanager
def look(sk, surface=None, under=None, plat=None, pad=None, rails=None):
    """Draw what is laid inside with this surface (and supports, platforms, pad art, rail style)."""
    old = (sk.surface, sk.under_fn, sk.plat_fn, sk.pad_fn, sk.rail_style)
    if surface is not None:
        sk.surface = surface
    if under is not None:
        sk.under_fn = under if under else None
    if plat is not None:
        sk.plat_fn = plat
    if pad is not None:
        sk.pad_fn = pad
    if rails is not None:
        sk.rail_style = rails
    try:
        yield
    finally:
        sk.surface, sk.under_fn, sk.plat_fn, sk.pad_fn, sk.rail_style = old


def stage(r, sk, title, label):
    sk.title = title
    r.b.gate_label = label


def run(r, label, L, w=None, dy=0.0, cp=False, rails=False, boosts=0, every=50.0, **kw):
    """A plain stretch (drawn with the current surface)."""
    r.straight(label, L, dy=dy, w1=w, lead=min(30.0, L / 4), cp=cp, rails=rails, **kw)
    if boosts:
        R2.lay_strips(r, max(30.0, L * 0.12), L - 30, every=every, lanes=boosts)
    return r


def end_on_line(r, label, margin=200.0):
    left = r.X1 - 110 - r.p[0] - margin
    if left > 60:
        run(r, label, left, boosts=2, every=60)


def boost_strips(r, d0, d1, every=45.0, lanes=2):
    R2.lay_strips(r, d0, d1, every=every, lanes=lanes)


# ===================================================================== shared object art
def legs(b, top, f, w, L, depth, col, mat="SmoothPlastic", d=10.0, name="Leg", inset=8.0):
    """Four legs under a rectangle (a table, a shelf, a desk) down `depth`."""
    rt = right_of(f)
    for a in (-1, 1):
        for s in (-1, 1):
            p = add(top, add(mul(f, a * (L / 2 - inset)), mul(rt, s * (w / 2 - inset))))
            cyl(b, name, sub(p, (0, depth / 2, 0)), depth, d, col, mat, b.scenery)


def disc_obj(b, r, col, mat="SmoothPlastic", th=8.0, grow=1.08, name="Disc", rim=None, rim_col=None, under=None):
    """A round object whose top is the stretch just laid (a plate, a cheese wheel, a lily pad): it covers the whole
    stretch (radius to its far corners). Returns (centre top, radius)."""
    p0, p1, f, L, w, _ = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    R = math.hypot(L / 2, w / 2) * grow
    cyl(b, "Platform", sub(c, (0, th / 2, 0)), th, 2 * R, col, mat, b.roads, collide=True)
    if rim:
        ringz(b, add(c, (0, 0.2, 0)), R - rim / 2, rim_col or col, mat, th=rim, name=name + "Rim")
    return c, R


# ===================================================================== 1. THE GIANT KITCHEN
class Kitchen(Giant):
    key, title, theme_name = "kitchen", "The Giant Kitchen", "Giant kitchen"
    clock, bloom, hue = 9.5, 0.35, 0.09
    body, top, edge, padc, danger = (52, 84, 110), (242, 240, 234), (230, 70, 60), (255, 150, 40), (255, 60, 40)
    body_mat, top_mat = "SmoothPlastic", "Marble"
    gate_post, gate_board, gate_text = (52, 84, 110), (242, 240, 234), (230, 70, 60)
    light_over = {"Lt_Atmosphere_Density": 0.18, "Lt_Atmosphere_Haze": 0.6}


K_CAB, K_CAB2 = (52, 84, 110), (70, 106, 134)
K_WOOD, K_WOOD_DK = (204, 150, 92), (150, 100, 60)
K_RED, K_TEAL, K_YEL = (230, 70, 60), (60, 190, 180), (255, 210, 70)
K_TILE = (236, 244, 246)

COUNTER = slab((242, 240, 234), "Marble", th=6, side=(210, 206, 198), deco=edges((210, 206, 198), width=2.0, name="CounterEdge"))
BOARD = slab(K_WOOD, "Wood", th=5, side=K_WOOD_DK,
             deco=both(lines_along(K_WOOD_DK, 14, name="Grain"), edges((178, 122, 72), width=5.0, name="JuiceGroove")))
SPOON = slab(CHROME, "Metal", th=3, refl=0.25, deco=edges((230, 234, 240), width=1.2, name="SpoonShine"))
STOVE = slab((30, 30, 34), "Glass", th=5, side=(60, 62, 68), refl=0.15, deco=edges((90, 92, 100), width=3.0, name="StoveTrim"))
DOUGH = slab((240, 222, 184), "SmoothPlastic", th=6, deco=None)
STEEL = slab((178, 184, 192), "Metal", th=4, refl=0.2, deco=lines_across((150, 156, 166), 18, name="SteelSeam"))
GLASS = slab((200, 236, 255), "Glass", th=2.5, transp=0.25, deco=edges((240, 250, 255), width=2.0, name="ShelfEdge"))
FRIDGE_FLOOR = slab((236, 242, 246), "SmoothPlastic", th=4, deco=lines_across((210, 220, 228), 30, name="Rib"))
SHELF_WOOD = slab((222, 178, 120), "WoodPlanks", th=5, side=(160, 110, 66))


def cabinets(b, r, h=70.0, door=40.0, side_out=0.0):
    """Base cabinets under the counter stretch just laid: a body, doors with chrome handles, a toe kick."""
    p0, p1, f, L, w, pts = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    rt = right_of(f)
    ob(b, "Cabinet", sub(c, (0, 6 + h / 2, 0)), f, (w - 8, h, L), K_CAB)
    ob(b, "ToeKick", sub(c, (0, 6 + h + 3, 0)), f, (w - 16, 6, L - 6), (30, 40, 52))
    n = max(1, int(L // door))
    for s in (-1, 1):
        for k in range(n):
            q = add(c, add(mul(f, -L / 2 + (k + 0.5) * L / n), add(mul(rt, s * (w / 2 - 3.9)), (0, -6 - h * 0.45, 0))))
            ob(b, "CabDoor", q, f, (0.4, h * 0.78, L / n - 4), K_CAB2)
            hq = add(q, add(mul(rt, s * 0.6), add(mul(f, (L / n / 2 - 6) * (1 if k % 2 else -1)), (0, h * 0.2, 0))))
            ob(b, "Handle", hq, f, (1.2, 10, 1.6), CHROME, "Metal")


def backsplash(b, r, side=-1, h=60.0, tile=10.0):
    """A tiled wall along one side of the counter, with a row of coloured accent tiles."""
    p0, p1, f, L, w, pts = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    rt = right_of(f)
    q = add(c, add(mul(rt, side * (w / 2 + 3)), (0, h / 2 - 6, 0)))
    ob(b, "Backsplash", q, f, (4, h + 6, L), K_TILE, "Marble")
    face = add(c, mul(rt, side * (w / 2 + 0.85)))
    y = 2.0
    while y < h:
        ob(b, "TileLine", add(face, (0, y, 0)), f, (0.3, 0.5, L), (190, 204, 210))
        y += tile
    d = -L / 2 + tile / 2
    k = 0
    while d < L / 2:
        ob(b, "AccentTile", add(face, add(mul(f, d), (0, 25, 0))), f, (0.35, tile - 1, tile - 1), [K_TEAL, K_RED, K_YEL][k % 3])
        d += tile * 3
        k += 1


def canister(b, p, d, h, col, label_col=WHITE):
    cyl(b, "Canister", add(p, (0, h / 2, 0)), h, d, col, "SmoothPlastic", b.scenery)
    cyl(b, "CanisterLid", add(p, (0, h + 1.5, 0)), 3, d + 1, CHROME, "Metal", b.scenery)
    cyl(b, "CanisterLabel", add(p, (0, h * 0.5, 0)), h * 0.3, d + 0.3, label_col, "SmoothPlastic", b.scenery)


def plate(b, r, col, rim_col=WHITE, pattern=None):
    """A giant plate round the stretch just laid: ceramic disc, raised-look rim ring, a painted band."""
    c, R = disc_obj(b, r, rim_col, th=6.0, name="Plate")
    cyl(b, "PlateFoot", sub(c, (0, 8, 0)), 4, R * 1.2, mix(rim_col, (0, 0, 0), 0.08), "SmoothPlastic", b.scenery)
    ringz(b, add(c, (0, 0.12, 0)), R * 0.72, col, "SmoothPlastic", th=0.2, name="PlateBand")
    ringz(b, add(c, (0, 0.12, 0)), R - 3, col, "SmoothPlastic", th=0.2, name="PlateBand")
    if pattern:
        for k in range(8):
            a = TAU * k / 8
            cyl(b, "PlateDot", add(c, (math.cos(a) * R * 0.86, 0.08, math.sin(a) * R * 0.86)), 0.15, 6, col, "SmoothPlastic",
                b.scenery)
    return c, R


def toaster(b, r, f):
    """The toaster under the last stretch (its top is the stretch, the pad fires out of the slots)."""
    p0, p1, f, L, w, pts = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    rt = right_of(f)
    H = 70.0
    ob(b, "Toaster", sub(c, (0, H / 2 + 3, 0)), f, (w + 6, H, L + 6), CHROME, "Metal", refl=0.3)
    for s in (-1, 1):
        ob(b, "ToasterBand", add(c, add(mul(rt, s * (w / 2 + 3.3)), (0, -H * 0.55, 0))), f, (0.4, 8, L + 6), BLACK)
        ob(b, "ToasterLever", add(c, add(mul(rt, s * (w / 2 + 6)), (0, -18, 0))), f, (6, 5, 14), BLACK)
        cyl(b, "ToasterDial", add(c, add(mul(rt, s * (w / 2 + 3.6)), add(mul(f, -L * 0.3), (0, -40, 0)))), 1.5, 10, K_RED,
            "SmoothPlastic", b.scenery, axis=rt)
    for a in (-1, 1):
        ob(b, "ToasterFoot", add(c, add(mul(f, a * (L / 2 - 6)), (0, -H - 5, 0))), f, (w - 10, 4, 8), BLACK)
    # the slots, glowing red-hot, run along the top
    for s in (-1, 1):
        ob(b, "ToasterSlot", add(c, add(mul(rt, s * w * 0.22), (0, 0.08, 0))), f, (w * 0.16, 0.15, L - 16), (255, 90, 30),
           "Neon")


def toaster_pad(sk, b, start, f):
    fr = deck_frame(add(start, (0, 0.1, 0)), f)
    for k in range(3):
        q = add(start, mul(f, -8 + k * 8))
        Pt(b, "PadChevron", CF(add(q, (0, 0.25, 0)), fr.x, fr.y, fr.z), (14, 0.2, 3), (255, 230, 120), "Neon")
    # a slice of toast popping up beside the launch
    for s in (-1, 1):
        q = add(start, add(mul(right_of(f), s * 40), (0, 22, 0)))
        ob(b, "ToastSlice", q, f, (3, 40, 34), (214, 150, 70))
        ob(b, "ToastCrust", add(q, (0, 20, 0)), f, (3.4, 3, 34), (140, 84, 40))


def chop_knife(b, c, w, i, period=2.6):
    """A giant chef's knife on a hinge at the board's edge: it chops down across half the board (crush) and lifts."""
    x, y, z = c
    s = 1 if i % 2 == 0 else -1
    piv = (x, y + 6, z + s * (w / 2 + 10))
    cyl(b, "KnifeBlock", add(piv, (0, -2, 0)), 16, 14, K_WOOD_DK, "Wood", b.scenery, axis=(1, 0, 0), collide=True)
    root = b.prop_root("ChopKnife")
    # at rest the blade stands straight up over its block; it chops down flat across the board and back
    rig = b.rig(root, "Hinge", axis_frame(piv, (1, 0, 0)), -90.0 * s, period, phase=(i * 0.31) % 1,
                keys="0:0 0.3:0 0.42:1 0.6:1 0.8:0", name="Chop")
    Lb = w * 0.55 + 6
    Pt(b, "KnifeBlade", CF(add(piv, (0, Lb / 2 + 4, 0))), (26, Lb, 2.0), CHROME, "Metal", rig, query=True,
       attrs={"ObbyHazard": "Crush"}, refl=0.35)
    Pt(b, "KnifeEdge", CF(add(piv, (13.2, Lb / 2 + 4, 0))), (0.6, Lb, 2.2), (255, 255, 255), "Neon", rig)
    Pt(b, "KnifeHandle", CF(add(piv, (0, 1, 0))), (12, 8, 6), BLACK, "SmoothPlastic", rig, query=True,
       attrs={"ObbyHazard": "Crush"})


def rolling_pin(b, c, w, i, period=2.6, d=16.0):
    """A rolling pin that rolls right across the dough and back (knocks you off)."""
    x, y, z = c
    z0 = (x, y + d / 2 + 0.6, z - w / 2 + 20)
    root = b.prop_root("RollingPin")
    rig = b.rig(root, "Slide", axis_frame(z0, (0, 0, 1)), w - 40, period + 0.3 * i, phase=(i * 0.43) % 1,
                keys="0:0 0.5:1 1:0", name="Roll")
    Lp = 64.0
    cyl(b, "PinBody", z0, Lp, d, (226, 180, 120), "Wood", rig, axis=(1, 0, 0), query=True, attrs={"ObbyHazard": "Knock"})
    for s in (-1, 1):
        cyl(b, "PinHandle", add(z0, (s * (Lp / 2 + 7), 0, 0)), 14, d * 0.45, K_RED, "SmoothPlastic", rig, axis=(1, 0, 0),
            query=True, attrs={"ObbyHazard": "Knock"})
        cyl(b, "PinBand", add(z0, (s * (Lp / 2 - 4), 0, 0)), 2, d + 0.4, K_RED, "SmoothPlastic", rig, axis=(1, 0, 0))


def burner(b, c, w, i, period=1.8):
    """A stove ring that heats up (red, it burns) and cools (dark, safe)."""
    x, y, z = c
    lane = (-1 if i % 2 else 1) * w * 0.22
    p = (x, y + 0.1, z + lane)
    ringz(b, p, 15, (90, 92, 100), "Metal", th=0.2, name="BurnerRingCold")
    for R in (14, 9, 4):
        ringz(b, add(p, (0, 0.05, 0)), R, (255, 70, 30), "Neon", th=0.25, name="BurnerGlow")
    Pt(b, "Burner", axis_frame(add(p, (0, 0.6, 0)), UP), (1.2, 30, 30), (255, 80, 30), "Neon", b.hazards, query=True, transp=0.35,
       shape=2,
       attrs={"ObbyHazard": "Zap", "ZapFX": True, "ZapPeriod": float(period), "ZapOn": float(period * 0.45),
              "ZapPhase": float((i * 0.37) % 1)})


def fridge(b, c0, c1, f, w, H, door_side=1):
    """A fridge lying round the shelves stretch: white walls, a lit ceiling strip, an open door at the far end."""
    rt = right_of(f)
    c = R2.lerp3(c0, c1, 0.5)
    L = math.hypot(c1[0] - c0[0], c1[2] - c0[2])
    yb = min(c0[1], c1[1]) - 10
    yt = max(c0[1], c1[1]) + H
    mid = (c[0], (yb + yt) / 2, c[2])
    Hh = yt - yb
    for s in (-1, 1):
        ob(b, "FridgeWall", add(mid, mul(rt, s * (w / 2 + 6))), f, (8, Hh, L), (246, 248, 250))
        ob(b, "FridgeLiner", add(mid, mul(rt, s * (w / 2 + 1.9))), f, (0.3, Hh - 10, L - 10), (220, 236, 246))
    ob(b, "FridgeRoof", (c[0], yt + 4, c[2]), f, (w + 20, 8, L), (246, 248, 250))
    ob(b, "FridgeLight", (c[0], yt - 0.2, c[2]), f, (w * 0.4, 0.4, L * 0.8), (230, 248, 255), "Neon")
    ob(b, "FridgeBase", (c[0], yb - 4, c[2]), f, (w + 20, 8, L), (232, 236, 240))
    # the open door, swung out at the far end, its shelves lined with bottles
    hinge = add(c1, add(mul(rt, door_side * (w / 2 + 10)), (0, 0, 0)))
    dq = add(hinge, add(mul(rt, door_side * 4), mul(f, 0)))
    dirn = rt if door_side > 0 else mul(rt, -1)
    door_c = add(add(c1, mul(rt, door_side * (w / 2 + 10))), add(mul(dirn, 0), mul(f, 40)))
    door_c = (door_c[0], mid[1], door_c[2])
    ob(b, "FridgeDoor", add(add(c1, mul(dirn, w / 2 + 50)), (0, mid[1] - c1[1], 0)), f, (80, Hh, 8), (246, 248, 250))
    for k in range(4):
        y = yb + 30 + k * (Hh - 40) / 4
        q = add(add(c1, mul(dirn, w / 2 + 50)), (0, y - c1[1], 0))
        ob(b, "DoorShelf", add(q, mul(f, -10)), f, (70, 2, 14), (200, 236, 255), "Glass", transp=0.3)
        for j in range(3):
            bq = add(q, add(mul(dirn, -20 + j * 20), add(mul(f, -10), (0, 9, 0))))
            cyl(b, "Bottle", bq, 16, 8, [K_RED, (90, 200, 90), K_YEL][j], "Glass", b.scenery)
    return yb, yt


def milk(b, base, f, s=1.0):
    ob(b, "MilkCarton", add(base, (0, 30 * s, 0)), f, (24 * s, 60 * s, 24 * s), WHITE)
    ob(b, "MilkBand", add(base, (0, 28 * s, 0)), f, (24.4 * s, 14 * s, 24.4 * s), (60, 140, 230))
    M.tri(b, "MilkRoof", add(base, (-12 * s, 60 * s, 0)), add(base, (12 * s, 60 * s, 0)), add(base, (0, 72 * s, 0)), WHITE,
          th=24 * s)


def cheese_wedge(b, base, f, s=1.0, yaw=0.0):
    a = add(base, (0, 0, 0))
    ob(b, "Cheese", add(base, (0, 12 * s, 0)), f, (30 * s, 24 * s, 40 * s), (255, 206, 70))
    for k in range(4):
        ball(b, "CheeseHole", add(base, (math.cos(k) * 10 * s, 14 * s + k * 2, math.sin(k * 2) * 10 * s)), 6 * s,
             (230, 170, 40), "SmoothPlastic", b.scenery)


def egg(b, p, d=20.0):
    ball(b, "Egg", add(p, (0, d * 0.55, 0)), d, (250, 240, 222), "SmoothPlastic", b.scenery)


def slot31(r, sk, rng):
    b = r.b
    stage(r, sk, "The Giant Kitchen", "OBBY 3 - LEVEL 1")
    # ---- the counter: marble top, navy cabinets under it, a tiled wall along the left, canisters on the right
    with look(sk, surface=COUNTER):
        run(r, "Countertop", 280, w=130, boosts=2, every=60)
        cabinets(b, r)
        backsplash(b, r, side=-1)
        p0, p1, f, L, w, _ = span(r)
        for k, (col, d) in enumerate(((K_RED, 26), (K_TEAL, 22), (K_YEL, 18))):
            canister(b, add(R2.lerp3(p0, p1, 0.25 + 0.2 * k), mul(right_of(f), w / 2 + 16 + d / 2)), d, 30 + d, col)
    # ---- the chopping board, with giant knives chopping across it (one half always clear)
    with look(sk, surface=BOARD):
        run(r, "Chopping Board", 300, w=110, cp=True)
        r.along(chop_knife, [100, 210])
        cabinets(b, r)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        ob(b, "CounterUnder", sub(c, (0, 8, 0)), f, (w + 40, 5, L + 20), (242, 240, 234), "Marble")
        for k in range(5):
            q = add(R2.lerp3(p0, p1, 0.1 + 0.2 * k), add(mul(right_of(f), (w / 2 - 14) * (1 if k % 2 else -1)), (0, 0.15, 0)))
            cyl(b, "CarrotCoin", q, 1.4, 14, (255, 140, 40), "SmoothPlastic", b.scenery)
    # ---- the spoon: drive down its handle, launch out of the bowl over the hob
    with look(sk, surface=SPOON):
        run(r, "Spoon Handle", 120, w=44)
        p0, p1, f, L, w, _ = span(r)
        ob(b, "SpoonHandleUnder", sub(R2.lerp3(p0, p1, 0.5), (0, 4, 0)), f, (w - 6, 3, L), CHROME_DK, "Metal")
        bowl0 = r.p
    with look(sk, surface=by_name({"Ramp": SPOON}, STOVE)):
        r.w = 64
        R2.ramp_jump(r, "Spoon Ramp", deg=20, drop=40, w_land=130, slope=3, land_min=320, cp=True, rails=False)
        # the bowl round the kicker: an oval dish under it
        kp = r.b.jumps[-2][1]
        bc = R2.lerp3(bowl0, kp, 0.5)
        fb = RT.flat(sub(kp, bowl0))
        Lb = math.hypot(kp[0] - bowl0[0], kp[2] - bowl0[2])
        ob(b, "SpoonBowl", sub(bc, (0, 7, 0)), fb, (84, 6, Lb + 30), CHROME, "Metal", refl=0.3)
        ob(b, "SpoonBowlRim", sub(add(bc, mul(fb, Lb / 2 + 14)), (0, 3, 0)), fb, (84, 4, 6), CHROME_DK, "Metal")
        coin_arc(b, -2, n=6)
        # the hob under the landing: black glass, four burner rings, chrome knobs
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        ob(b, "Oven", sub(c, (0, 50, 0)), f, (w + 10, 84, L + 10), (40, 42, 48), "Metal")
        ob(b, "OvenWindow", add(sub(c, (0, 56, 0)), mul(right_of(f), w / 2 + 5.3)), f, (0.4, 40, L * 0.5), (255, 140, 60),
           "Neon", transp=0.4)
        for k in range(4):
            q = add(R2.lerp3(p0, p1, 0.2 + 0.2 * k), add(mul(right_of(f), w / 2 + 6), (0, -14, 0)))
            cyl(b, "OvenKnob", q, 4, 8, CHROME, "Metal", b.scenery, axis=right_of(f))
    # ---- the hob run: rings that heat up red (they burn) and cool down; weave through the dark ones
    with look(sk, surface=STOVE):
        run(r, "Hot Hob", 320, w=110)
        r.along(burner, [60, 130, 200, 270])
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        ob(b, "Oven", sub(c, (0, 50, 0)), f, (w + 10, 84, L + 10), (40, 42, 48), "Metal")
    # ---- round the corner of the L-shaped counter
    with look(sk, surface=COUNTER):
        r.turn("Counter Corner", 90, 110)
    # ---- the dinner plates: hop from plate to plate down the table
    o = O.Obby(r, 230)
    with look(sk, surface=ghost):
        o.plat("Blue Plate", 110, 96, cp=True)
        plate(b, r, (40, 90, 200), pattern=True)
        o.kick(dy=-24, side=70, label="Plate Hop")
        o.plat("Red Plate", 100, 96)
        plate(b, r, K_RED)
        coin_arc(b, -1, n=5)
        o.kick(dy=-24, side=-70, label="Plate Hop 2")
        o.plat("Yellow Plate", 100, 96)
        plate(b, r, (230, 170, 30), pattern=True)
        o.kick(dy=10, side=0, label="Plate Hop 3")
    # ---- the toaster: its slots fire you up to the shelf
    with look(sk, surface=slab(CHROME, "Metal", th=3, refl=0.3), pad=toaster_pad):
        o.plat("Toaster Top", 120, 90)
        toaster(b, r, r.f)
        o.pad(120.0, label="Toaster Launch")
    with look(sk, surface=SHELF_WOOD):
        o.plat("Spice Shelf", 260, 84, cp=True)
        p0, p1, f, L, w, _ = span(r)
        legs(b, R2.lerp3(p0, p1, 0.5), f, w, L, 60, (160, 110, 66), "Wood", d=8, name="ShelfBracket")
        for k in range(6):
            s_ = 1 if k % 2 else -1
            q = add(R2.lerp3(p0, p1, 0.1 + 0.16 * k), mul(right_of(f), s_ * (w / 2 + 12)))
            cyl(b, "SpiceJar", add(q, (0, 15, 0)), 30, 16, [K_RED, (120, 80, 40), (90, 160, 60)][k % 3], "Glass", b.scenery)
            cyl(b, "SpiceLid", add(q, (0, 31, 0)), 3, 17, BLACK, "SmoothPlastic", b.scenery)
        o.drop(70.0, side=0.0, label="Dough Drop")
    # ---- the dough: rolling pins roll right across it
    with look(sk, surface=DOUGH):
        o.plat("Dough Sheet", 420, 120, cp=True, boost=False)
        r.along(rolling_pin, [120, 230, 330])
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        ob(b, "PastryBoard", sub(c, (0, 7, 0)), f, (w + 30, 4, L + 20), K_WOOD, "Wood")
        cabinets(b, r)
        for k in range(10):
            q = add(R2.lerp3(p0, p1, rng.random()), add(mul(right_of(f), rng.uniform(-w / 2 + 8, w / 2 - 8)), (0, 0.1, 0)))
            cyl(b, "FlourDust", q, 0.12, rng.uniform(8, 20), (255, 255, 252), "SmoothPlastic", b.scenery, transp=0.3)
    # ---- the sink: a swirl round the drain, down into the basin
    with look(sk, surface=STEEL, rails={"edge": (230, 234, 240), "edge_mat": "Metal", "side": CHROME, "side_mat": "Metal"}):
        run(r, "Sink Rim", 180, w=90)
        r.turn("Drain Swirl", -450, 120, dy=-80, rails=True, cp=True)
        C = r.centre
        cy = r.p[1]
        cyl(b, "Drain", (C[0], cy - 30, C[2]), 4, 60, (90, 94, 102), "Metal", b.scenery)
        for k in range(6):
            a = TAU * k / 6
            ob(b, "DrainSlot", (C[0] + math.cos(a) * 14, cy - 27.8, C[2] + math.sin(a) * 14), (math.cos(a), 0, math.sin(a)),
               (2.4, 0.3, 14), BLACK)
        cyl(b, "SinkWater", (C[0], cy - 29, C[2]), 0.4, 200, (120, 200, 255), "Glass", b.scenery, transp=0.45)
        ringz(b, (C[0], cy - 28.5, C[2]), 50, (200, 240, 255), "Neon", th=0.3, name="WaterSwirl")
        ringz(b, (C[0], cy - 28.5, C[2]), 80, (200, 240, 255), "Neon", th=0.3, name="WaterSwirl")
        # the faucet arching high over the drain
        tap = (C[0], cy + 150, C[2])
        cyl(b, "FaucetStem", add(C, (0, cy + 60 - C[1], 0)), 180, 14, CHROME, "Metal", b.scenery, refl=0.4)
        cyl(b, "FaucetArm", (C[0] + 30, cy + 150, C[2]), 60, 12, CHROME, "Metal", b.scenery, axis=(1, 0, 0), refl=0.4)
        cyl(b, "FaucetKnob", (C[0] - 6, cy + 120, C[2]), 8, 24, CHROME, "Metal", b.scenery, axis=(0, 0, 1), refl=0.4)
    with look(sk, surface=STEEL):
        r.straight("Drain Exit", 140, lead=20.0)
    # ---- the fridge: in through the open door, drop shelf to shelf, out at the bottom
    f = r.f
    o = O.Obby(r, 230)
    with look(sk, surface=FRIDGE_FLOOR):
        o.plat("Fridge Door", 120, 100, cp=True)
        o.pad(90.0, label="Fridge Lift")
    f0 = r.p
    with look(sk, surface=GLASS):
        o.plat("Top Shelf", 160, 110)
        p0, p1, f, L, w, _ = span(r)
        milk(b, add(R2.lerp3(p0, p1, 0.6), mul(right_of(f), w / 2 + 16)), f)
        cheese_wedge(b, add(R2.lerp3(p0, p1, 0.3), mul(right_of(f), -(w / 2 + 20))), f)
        o.drop(45.0, side=0.0, label="Shelf Drop")
        o.plat("Middle Shelf", 120, 110)
        p0, p1, f, L, w, _ = span(r)
        for k in range(4):
            egg(b, add(R2.lerp3(p0, p1, 0.2 + 0.2 * k), mul(right_of(f), w / 2 + 14)), 18)
        o.drop(45.0, side=0.0, label="Shelf Drop 2")
        o.plat("Crisper Drawer", 140, 110)
    f1 = r.p
    fridge(b, sub(f0, mul(r.f, 160)), add(f1, mul(r.f, 10)), r.f, 150, 150)
    with look(sk, surface=FRIDGE_FLOOR):
        o.drop(40.0, side=40.0, label="Out of the Fridge")
        o.plat("Fridge Mat", 0, 110)
    with look(sk, surface=COUNTER):
        r.turn("Kitchen Corner", -90, 110)
        run(r, "Island Counter", 120)
        cabinets(b, r)
    # ---- the food hops: a cheese wheel, a pancake stack, a giant cookie
    with look(sk, surface=ghost):
        o.kick(dy=0, side=-60, label="Cheese Hop")
        o.plat("Cheese Wheel", 100, 90, cp=True)
        c, R = disc_obj(b, r, (255, 206, 70), th=40.0, name="CheeseWheel")
        cyl(b, "CheeseRind", sub(c, (0, 20.4, 0)), 39.6, 2 * R - 3, (240, 170, 40), "SmoothPlastic", b.scenery)
        for k in range(7):
            a = TAU * k / 7 + 0.3
            cyl(b, "CheeseHoleTop", add(c, (math.cos(a) * R * 0.7, 0.08, math.sin(a) * R * 0.7)), 0.15, 9 + k % 3 * 3,
                (230, 170, 40), "SmoothPlastic", b.scenery)
        o.kick(dy=20, side=60, label="Pancake Hop")
        o.plat("Pancake Stack", 100, 90)
        c, R = disc_obj(b, r, (226, 166, 90), th=10.0, name="Pancake")
        for k in range(1, 5):
            cyl(b, "Pancake", sub(c, (0, 5 + k * 11, 0)), 10, 2 * R - k * 3, (226, 166, 90), "SmoothPlastic", b.scenery)
        cyl(b, "Butter", add(c, (0, 0.1, R * 0.45)), 0.2, 20, (255, 236, 140), "SmoothPlastic", b.scenery)
        ringz(b, add(c, (0, 0.1, 0)), R * 0.6, (150, 80, 20), "SmoothPlastic", th=0.2, name="SyrupDrip")
        coin_row(b, add(c, (0, 0, -R * 0.5)), add(c, (0, 0, R * 0.5)), n=4)
        o.kick(dy=-30, side=0, label="Cookie Hop")
        o.plat("Giant Cookie", 110, 96)
        c, R = disc_obj(b, r, (214, 156, 86), th=8.0, name="Cookie")
        for k in range(12):
            a = rng.random() * TAU
            rr = rng.uniform(0.2, 0.85) * R
            cyl(b, "ChocChip", add(c, (math.cos(a) * rr, 0.1, math.sin(a) * rr)), 0.2, rng.uniform(5, 9), (70, 40, 24),
                "SmoothPlastic", b.scenery)
    # ---- the fork bridge: narrow, then the serving tray home
    with look(sk, surface=SPOON):
        o.kick(dy=0, side=0, label="Fork Hop")
        o.plat("Fork Bridge", 220, 38, boost=False)
        p0, p1, f, L, w, _ = span(r)
        for k in range(4):
            q = add(p1, add(mul(right_of(f), (-1.5 + k) * 10), mul(f, 20)))
            ob(b, "ForkTine", add(q, (0, -1.5, 0)), f, (5, 3, 40), CHROME, "Metal")
    with look(sk, surface=slab((206, 210, 218), "Metal", th=4, refl=0.2, deco=edges((240, 242, 246), width=3.0, name="TrayRim"))):
        o.plat("Serving Tray", 220, 140, cp=True)
        run(r, "Cake Stand Run", 120, w=120)
    # ---- the cake: launch pads up its tiers (each a giant layer of sponge and icing), candles round the top
    o = O.Obby(r, 230)
    with look(sk, surface=ghost):
        for k, (dy, L, w, col) in enumerate(((60.0, 170, 120, (255, 182, 206)), (60.0, 150, 110, (255, 246, 236)),
                                             (60.0, 140, 100, (170, 110, 220)))):
            o.pad(dy, label="Cake Pad %d" % (k + 1))
            o.plat(("Bottom Tier", "Middle Tier", "Top Tier")[k], L, w, cp=(k == 1))
            c, R = disc_obj(b, r, col, th=6.0)
            cyl(b, "CakeSponge", sub(c, (0, 6 + 25, 0)), 50, 2 * R - 4, (246, 220, 170), "SmoothPlastic", b.scenery)
            cyl(b, "CakeIcing", sub(c, (0, 6 + 52, 0)), 4, 2 * R - 2, col, "SmoothPlastic", b.scenery)
            for j in range(10):
                a = TAU * j / 10
                q = add(c, (math.cos(a) * (R - 1), -9, math.sin(a) * (R - 1)))
                cyl(b, "IcingDrip", q, 10 + (j % 3) * 4, 6, col, "SmoothPlastic", b.scenery)
            coin_row(b, add(c, mul(r.f, -R * 0.4)), add(c, mul(r.f, R * 0.4)), n=3)
        p0, p1, f, L, w, _ = span(r)
        top = R2.lerp3(p0, p1, 0.5)
        for j in range(6):
            a = TAU * (j + 0.5) / 6
            q = add(top, (math.cos(a) * 80, 0, math.sin(a) * 80))
            if abs(dot(sub(q, top), right_of(f))) > 50:
                cyl(b, "Candle", add(q, (0, 25, 0)), 50, 8, [K_RED, K_TEAL, K_YEL][j % 3], "SmoothPlastic", b.scenery)
                ball(b, "CandleFlame", add(q, (0, 54, 0)), 6, (255, 200, 80), "Neon", b.scenery)
        ball(b, "CakeCherry", add(top, mul(right_of(f), -30)), 0.1, K_RED, "SmoothPlastic", b.scenery)
        o.drop(40.0, label="Cake Drop")
    with look(sk, surface=slab((206, 210, 218), "Metal", th=4, refl=0.2, deco=edges((240, 242, 246), width=3.0, name="TrayRim"))):
        o.plat("Cake Board", 0, 140)
        r.turn("Tray Turn", 90, 130)
    # ---- the coffee mugs: hop across the tops of three steaming mugs, stepping back towards the table
    o = O.Obby(r, 230)
    with look(sk, surface=ghost):
        for k, (dy, col) in enumerate(((-10.0, (200, 60, 60)), (10.0, (60, 140, 220)), (-10.0, (250, 250, 250)))):
            o.kick(dy=dy, side=-130, label="Mug Hop %d" % (k + 1))
            o.plat("Coffee Mug %d" % (k + 1), 100, 84, cp=(k == 1))
            c, R = disc_obj(b, r, (96, 58, 34), th=2.0, grow=1.04)
            cyl(b, "MugBody", sub(c, (0, 40, 0)), 78, 2 * R + 10, col, "SmoothPlastic", b.scenery)
            cyl(b, "MugLip", sub(c, (0, 1.4, 0)), 3, 2 * R + 10.6, mix(col, WHITE, 0.4), "SmoothPlastic", b.scenery)
            hq = add(sub(c, (0, 36, 0)), mul(right_of(r.f), -(R + 22)))
            ringz(b, hq, 20, col, "SmoothPlastic", th=8, axis=r.f, name="MugHandle")
            for j in range(3):
                ball(b, "Steam", add(c, (j * 14 - 14, 40 + j * 16, (j % 2) * 10)), 14 + j * 4, (255, 255, 255), "SmoothPlastic",
                     b.scenery, transp=0.7)
            coin_arc(b, -1, n=4)
    # ---- the dining table: a checked tablecloth home
    cloth = slab((250, 246, 240), "Fabric", th=4, deco=both(lines_along((220, 60, 60), 16, width=5.0, name="ClothCheck"),
                                                          lines_across((220, 60, 60), 16, width=5.0, name="ClothCheck")))
    with look(sk, surface=cloth):
        o.kick(dy=0.0, side=-60, label="Table Hop")
        o.plat("Dining Table", 200, 150, cp=True)
    with look(sk, surface=cloth):
        end_on_line(r, "Table Run", margin=600)
    r.log("end")
    return ["Countertop", "Chopping Board", "Spoon Ramp", "Hot Hob", "Dinner Plates", "Toaster Launch", "Spice Shelf",
            "Rolling Pins", "Drain Swirl", "Fridge Shelves", "Cheese Wheel", "Pancakes", "Cookie", "Fork Bridge"]



# ===================================================================== shared toy-world pieces
def cube_obj(b, r, col, letter=None, letter_col=WHITE, depth=None, panel=True):
    """A giant block under the stretch just laid: its top is the stretch (it covers it), letters on its sides."""
    from skins import pixel_art
    p0, p1, f, L, w, _ = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    s_ = max(L, w) + 6
    D = depth or s_
    rt = right_of(f)
    Pt(b, "Platform", CF(sub(c, (0, D / 2, 0)), *axes(f)), (s_, D, s_), col, "SmoothPlastic", b.roads, collide=True)
    edge = mix(col, BLACK, 0.25)
    for a in (-1, 1):
        for sd in (-1, 1):
            q = add(c, add(mul(f, a * s_ / 2), add(mul(rt, sd * s_ / 2), (0, -D / 2 - 0.2, 0))))
            ob(b, "BlockEdge", q, f, (3, D - 0.4, 3), edge)
    ob(b, "BlockTop", add(c, (0, 0.06, 0)), f, (s_ * 0.7, 0.12, s_ * 0.7), mix(col, WHITE, 0.3))
    if panel:
        for nrm in (rt, mul(rt, -1), f, mul(f, -1)):
            q = add(sub(c, (0, min(D, s_) / 2, 0)), mul(nrm, s_ / 2 + 0.2))
            g = f if abs(dot(nrm, f)) < 0.5 else rt
            Pt(b, "BlockPanel", CF(q, *axes(nrm)), (min(s_, D) * 0.7, min(s_, D) * 0.7, 0.3), mix(col, WHITE, 0.55),
               "SmoothPlastic", b.scenery)
            if letter:
                rows = M.FONT.get(letter, M.FONT["A"])
                pixel_art(b, add(q, mul(nrm, 0.3)), nrm, (0, 1, 0), rows, min(s_, D) * 0.09, letter_col, "SmoothPlastic",
                          b.scenery, th=0.4, name="BlockLetter")
    return c, s_


def toy_soldier(b, base, s, f, coat=(200, 30, 40)):
    """A toy soldier standing to attention (s: its height)."""
    cyl(b, "SoldierBase", add(base, (0, s * 0.03, 0)), s * 0.06, s * 0.32, (40, 120, 60), "SmoothPlastic", b.scenery)
    for sd in (-1, 1):
        ob(b, "SoldierLeg", add(base, add(mul(right_of(f), sd * s * 0.06), (0, s * 0.22, 0))), f, (s * 0.1, s * 0.34, s * 0.12),
           (30, 40, 90))
    ob(b, "SoldierCoat", add(base, (0, s * 0.53, 0)), f, (s * 0.3, s * 0.3, s * 0.18), coat)
    ob(b, "SoldierBelt", add(base, (0, s * 0.45, 0)), f, (s * 0.31, s * 0.04, s * 0.19), WHITE)
    ball(b, "SoldierHead", add(base, (0, s * 0.74, 0)), s * 0.16, (255, 214, 180), "SmoothPlastic", b.scenery)
    cyl(b, "SoldierHat", add(base, (0, s * 0.9, 0)), s * 0.2, s * 0.17, BLACK, "SmoothPlastic", b.scenery)
    cyl(b, "SoldierRifle", add(base, add(mul(right_of(f), s * 0.2), (0, s * 0.6, 0))), s * 0.45, s * 0.04, (90, 60, 40),
        "Wood", b.scenery)


def rock_bridge(r, label, L, w, col, amp_deg=10.0, period=4.0, hold=1.6, phase=0.0, art=None):
    """A plank rocking about its middle (level for a moment between tilts: cross while it is level)."""
    b = r.b
    f = r.f
    c = add(r.p, mul(f, 3 + L / 2))
    yaw = math.atan2(-f[2], f[0])
    m = R2.rotor(b, label.replace(" ", ""), CF(c) * RT.rot_y(yaw), (0, 0, 1), "rock", amp=math.radians(amp_deg),
                 period=period, ease=1.0, hold0=hold, phase=phase, near=L)
    Pt(b, "MovingDeck", CF(add(c, (0, -2, 0)), *axes(f)), (w, 4, L), col, "SmoothPlastic", m, collide=True,
       attrs={"ClockDeck": True})
    if art:
        art(b, m, c, f, L, w)
    a0, a1 = add(r.p, mul(f, 3)), add(r.p, mul(f, 3 + L))
    R2._special_line(b, a0, a1, 8)
    b.samples.append(c + (L,))
    r.p = add(a1, mul(f, 3))
    return c


# ===================================================================== 2. THE TOYBOX
T_RED, T_BLUE, T_YEL, T_GRN = (230, 50, 50), (40, 110, 230), (255, 205, 40), (60, 190, 80)
T_ORG, T_PUR, T_WOOD = (255, 130, 20), (150, 80, 220), (226, 186, 128)


class Toybox(Giant):
    key, title, theme_name = "toybox", "The Toybox", "Giant toybox"
    clock, bloom, hue = 13.0, 0.35, 0.58
    body, top, edge, padc, danger = T_BLUE, T_WOOD, T_YEL, T_YEL, (255, 60, 50)
    body_mat, top_mat = "SmoothPlastic", "WoodPlanks"
    gate_post, gate_board, gate_text = T_RED, T_BLUE, T_YEL
    light_over = {"Lt_CC_Saturation": 0.35, "Lt_Atmosphere_Density": 0.1}


TOY_SHELF = slab(T_WOOD, "WoodPlanks", th=8, side=(176, 128, 76))


def plastic(col, th=4.0):
    return slab(col, "SmoothPlastic", th=th, side=mix(col, BLACK, 0.2), deco=edges(mix(col, WHITE, 0.35), width=2.5, name="Bevel"))


def studs(col, every=18.0):
    def deco(sk, b, parent, fr, w, L):
        nx = int((w - 8) // every)
        nz = int((L - 8) // every)
        for i in range(nx):
            for j in range(nz):
                x = -((nx - 1) / 2) * every + i * every
                z = -((nz - 1) / 2) * every + j * every
                Pt(b, "Stud", CF(off(fr, x=x, y=0.06, z=z), fr.x, fr.y, fr.z) * CF((0, 0, 0), (0, 1, 0), (-1, 0, 0), (0, 0, 1)),
                   (0.12, 10, 10), col, "SmoothPlastic", parent, shape=2)
    return deco


BASEPLATE = slab(T_GRN, "SmoothPlastic", th=4, side=(40, 150, 60), deco=studs((90, 215, 110)))
TOY_TRACK = slab(T_ORG, "SmoothPlastic", th=3, side=(230, 100, 10), deco=edges((255, 190, 90), width=2.0, name="TrackStripe"))
CASTLE_TOP = slab((178, 182, 192), "SmoothPlastic", th=4, deco=lines_across((150, 154, 166), 16, name="StoneSeam"))


def train_grooves(sk, b, parent, fr, w, L):
    for k in (-1, 1):
        Pt(b, "TrackGroove", F(fr, off(fr, x=k * w * 0.22, y=0.06)), (6, 0.12, L), (170, 130, 80), "Wood", parent)


def toy_row(r, d, w, pattern, cols=(T_RED, T_BLUE, T_YEL, T_GRN)):
    """A row of toy-brick walls across the plate: 'b' smash through it at speed, 'g' a stack of solid blocks (go
    round), '.' open."""
    b = r.b
    p, f = at(r, d)
    rt = right_of(f)
    for k, ch in enumerate(pattern):
        q = add(p, mul(rt, -w / 2 + w * (k + 0.5) / 3))
        if ch == "b":
            MX.brick_wall(b, q, f, w / 3 - 4, h=26.0, kind="toy", nx=3, ny=3, cols=list(cols), mat="SmoothPlastic", depth=10)
        elif ch == "g":
            for j in range(2):
                ob(b, "ToyStack", add(q, (0, 13 + j * 26, 0)), f, (w / 3 - 6, 26, 26), cols[(k + j) % len(cols)],
                   collide=True)
                ob(b, "ToyStackStud", add(q, (0, 26.4 + j * 26, 0)), f, (w / 3 - 14, 0.8, 18), mix(cols[(k + j) % len(cols)], WHITE, 0.3))


def toy_train(b, c, w, i, L=320.0, period=4.6):
    """A wind-up toy train shuttling up and down the left groove (knocks you off): pass it on the right."""
    x, y, z = c
    lane = -w * 0.22
    p0 = (x - L / 2 + 40, y, z + lane)
    root = b.prop_root("ToyTrain")
    rig = b.rig(root, "Slide", axis_frame(p0, (1, 0, 0)), L - 80, period, phase=(i * 0.3) % 1, keys="0:0 0.5:1 1:0",
                name="Shuttle")
    hz = {"ObbyHazard": "Knock"}
    Pt(b, "TrainCab", CF(add(p0, (-10, 14, 0))), (16, 22, 24), T_RED, "SmoothPlastic", rig, query=True, attrs=hz)
    Pt(b, "TrainRoof", CF(add(p0, (-10, 26, 0))), (20, 3, 28), BLACK, "SmoothPlastic", rig)
    cyl(b, "TrainBoiler", add(p0, (8, 12, 0)), 22, 18, T_BLUE, "SmoothPlastic", rig, axis=(1, 0, 0), query=True, attrs=hz)
    cyl(b, "TrainChimney", add(p0, (14, 25, 0)), 10, 7, BLACK, "SmoothPlastic", rig)
    Pt(b, "TrainBase", CF(add(p0, (0, 4, 0))), (44, 4, 26), T_YEL, "SmoothPlastic", rig, query=True, attrs=hz)
    for k in range(3):
        for sd in (-1, 1):
            cyl(b, "TrainWheel", add(p0, (-14 + k * 14, 4, sd * 13.5)), 2, 10, BLACK, "SmoothPlastic", rig, axis=(0, 0, 1))
    for k in range(2):
        q = add(p0, (-40 - k * 36, 0, 0))
        Pt(b, "Wagon", CF(add(q, (0, 10, 0))), (30, 14, 24), [T_GRN, T_YEL][k], "SmoothPlastic", rig, query=True, attrs=hz)
        Pt(b, "WagonBase", CF(add(q, (0, 3, 0))), (32, 3, 26), BLACK, "SmoothPlastic", rig)
        ball(b, "WagonLoad", add(q, (0, 20, 0)), 12, [T_RED, T_BLUE][k], "SmoothPlastic", rig)


def top_slider(b, c, w, i, s=34.0, period=3.0):
    """A spinning top whizzing across the play table and back (knocks you off)."""
    x, y, z = c
    z0 = (x, y, z - w / 2 + 24)
    root = b.prop_root("SpinTop")
    rig = b.rig(root, "Slide", axis_frame(z0, (0, 0, 1)), w - 48, period + 0.4 * i, phase=(i * 0.37) % 1,
                keys="0:0 0.5:1 1:0", name="Whizz")
    spin = b.rig(rig, "Spin", axis_frame(z0, UP), 1.2, 1, name="TopSpin")
    cols = [(T_RED, WHITE), (T_BLUE, T_YEL), (T_PUR, T_GRN)][i % 3]
    n = 8
    for k in range(n):
        t = (k + 0.5) / n
        prof = (t / 0.55) ** 0.75 if t < 0.55 else 1 - 0.8 * ((t - 0.55) / 0.45) ** 1.5
        d = s * (0.12 + 0.8 * prof)
        cyl(b, "TopBand", add(z0, (0, 1 + s * 0.8 * t, 0)), s * 0.8 / n + 0.05, d, cols[k % 2], "SmoothPlastic", spin,
            query=True, attrs={"ObbyHazard": "Knock"})
    cyl(b, "TopHandle", add(z0, (0, s * 0.95, 0)), s * 0.3, 4, WHITE, "SmoothPlastic", spin)
    ball(b, "TopKnob", add(z0, (0, s * 1.12, 0)), 6, cols[0], "SmoothPlastic", spin)


def ball_cap(cols):
    k = [0]

    def cap(b, top, s, rng):
        """A giant bouncy ball under a flat cap (the cap is where it bounces you)."""
        col = cols[k[0] % len(cols)]
        k[0] += 1
        R = s * 0.62
        c = sub(top, (0, R + 0.6, 0))
        ball(b, "BouncyBall", c, 2 * R, col, "SmoothPlastic", b.scenery, refl=0.1)
        cyl(b, "BallStripe", c, 4, 2 * R + 0.6, WHITE, "SmoothPlastic", b.scenery, axis=(1, 0, 0))
        cyl(b, "Platform", sub(top, (0, 1.5, 0)), 3, s * 0.9, mix(col, WHITE, 0.25), "SmoothPlastic", b.roads, collide=True)
        ringz(b, add(top, (0, 0.1, 0)), s * 0.4, WHITE, "Neon", th=0.3, name="BounceGlow")
    return cap


def spring_pad(sk, b, start, f):
    """A giant coiled spring under the launch."""
    for k in range(6):
        ringz(b, add(start, (0, -6 - k * 7, 0)), 20, (200, 204, 214), "Metal", th=3.0, name="SpringCoil")
    fr = deck_frame(add(start, (0, 0.1, 0)), f)
    Pt(b, "SpringPlate", CF(add(start, (0, 0.15, 0)), fr.x, fr.y, fr.z), (40, 0.3, 30), T_YEL, "Neon")
    for k in range(3):
        q = add(start, mul(f, -8 + k * 8))
        Pt(b, "PadChevron", CF(add(q, (0, 0.35, 0)), fr.x, fr.y, fr.z), (14, 0.2, 3), WHITE, "Neon")


def castle_wall(b, r, stone=(178, 182, 192), roof=(40, 90, 200)):
    """The wall under a castle-top stretch: battlements on both sides, round towers at its ends, a gatehouse."""
    p0, p1, f, L, w, _ = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    rt = right_of(f)
    H = 110.0
    ob(b, "CastleWall", sub(c, (0, H / 2 + 4, 0)), f, (w + 6, H, L), mix(stone, BLACK, 0.08))
    n = int(L // 22)
    for sd in (-1, 1):
        for k in range(n):
            if k % 2 == 0:
                q = add(c, add(mul(f, -L / 2 + (k + 0.5) * L / n), add(mul(rt, sd * (w / 2 + 4)), (0, 6, 0))))
                ob(b, "Merlon", q, f, (6, 12, L / n - 1), stone, collide=True)
    for a in (-1, 1):
        for sd in (-1, 1):
            tq = add(c, add(mul(f, a * (L / 2 - 4)), mul(rt, sd * (w / 2 + 26))))
            cyl(b, "CastleTower", sub(tq, (0, H / 2 - 20, 0)), H + 40, 40, stone, "SmoothPlastic", b.scenery)
            M.wcone(b, "TowerRoof", add(tq, (0, 40, 0)), 40, 24, roof, n=10)
            cyl(b, "FlagPole", add(tq, (0, 92, 0)), 24, 1.4, WHITE, "SmoothPlastic", b.scenery)
            ob(b, "Flag", add(tq, add(mul(f, 6), (0, 98, 0))), f, (0.4, 8, 12), [T_RED, T_YEL][(a + sd) % 2 == 0])
    # the gatehouse over the middle of the wall walk
    for sd in (-1, 1):
        ob(b, "GatePillar", add(c, add(mul(rt, sd * (w / 2 + 10)), (0, 30, 0))), f, (14, 60, 24), stone, collide=True)
    ob(b, "GateLintel", add(c, (0, 66, 0)), f, (w + 34, 12, 26), stone)
    ob(b, "GateBanner", add(c, add(mul(f, -13.2), (0, 52, 0))), f, (w * 0.5, 16, 0.4), roof)


def slot32(r, sk, rng):
    b = r.b
    stage(r, sk, "The Toybox", "OBBY 3 - LEVEL 2")
    # ---- the toy shelf: a row of toy soldiers stands guard on both sides
    with look(sk, surface=TOY_SHELF):
        run(r, "Toy Shelf", 240, w=120, boosts=2, every=60)
        p0, p1, f, L, w, _ = span(r)
        for k in range(5):
            for sd in (-1, 1):
                toy_soldier(b, add(R2.lerp3(p0, p1, 0.1 + 0.2 * k), mul(right_of(f), sd * (w / 2 + 14))), 40, f,
                            coat=[T_RED, T_BLUE][k % 2])
        ob(b, "ShelfBoard", sub(R2.lerp3(p0, p1, 0.5), (0, 10, 0)), f, (w + 60, 4, L), (196, 150, 96), "WoodPlanks")
    # ---- the alphabet staircase: launch pads up a stack of giant letter blocks
    o = O.Obby(r, 230)
    with look(sk, surface=ghost, pad=spring_pad):
        for k, (col, ch) in enumerate(((T_RED, "A"), (T_BLUE, "B"), (T_YEL, "C"))):
            o.pad(40.0, side=(0, 50, -50)[k], label="Block Spring %d" % (k + 1))
            o.plat("Block %s" % ch, 100, 100, cp=(k == 0))
            cube_obj(b, r, col, letter=ch, letter_col=WHITE if k != 2 else T_RED)
            coin_arc(b, -1, n=4)
    # ---- round the orange toy track
    with look(sk, surface=TOY_TRACK, rails={"edge": (255, 190, 90), "edge_mat": "SmoothPlastic", "side": T_ORG,
                                            "side_mat": "SmoothPlastic"}):
        o.kick(dy=0.0, label="Track Hop")
        o.plat("Track Start", 80, 90)
        r.turn("Track Corner", 90, 120, rails=True)
        run(r, "Track Dip", 120, dy=-40, rails=True)
    # ---- the baseplate: smash through the toy-brick walls (or steer round the solid stacks)
    with look(sk, surface=BASEPLATE):
        run(r, "Baseplate", 420, w=130, cp=True, boosts=3, every=40)
        for k, pat in enumerate(("gbb", "b.g", "bbg", ".bb")):
            toy_row(r, 80 + k * 90, 130, pat)
    # ---- the toy train: it shuttles up and down the left groove
    with look(sk, surface=slab((236, 206, 150), "Wood", th=6, side=(196, 160, 104),
                               deco=both(train_grooves, edges((210, 176, 120), width=3.0, name="TrackEdge")))):
        run(r, "Train Track", 380, w=96)
        r.along(lambda b_, c, w, i: toy_train(b_, c, w, i, L=360.0), [190])
        p0, p1, f, L, w, _ = span(r)
        for k in range(2):
            c = R2.lerp3(p0, p1, 0.3 + 0.4 * k)
            for sd in (-1, 1):
                ob(b, "TunnelSide", add(c, add(mul(right_of(f), sd * (w / 2 + 8)), (0, 26, 0))), f, (10, 52, 50), T_GRN,
                   collide=True)
            ob(b, "TunnelRoof", add(c, (0, 56, 0)), f, (w + 30, 10, 50), T_RED)
        for k in range(12):
            q = add(R2.lerp3(p0, p1, (k + 0.5) / 12), (0, 0.07, 0))
            ob(b, "Sleeper", q, f, (w - 6, 0.14, 6), (190, 150, 100))
    with look(sk, surface=TOY_TRACK):
        r.turn("Track Bend", -90, 120, dy=20, rails=True)
    # ---- the play table: spinning tops whizz across it
    o = O.Obby(r, 230)
    with look(sk, surface=ghost):
        o.kick(dy=-20, label="Table Hop")
        o.plat("Play Table", 320, 140, cp=True)
        c, R = disc_obj(b, r, (255, 236, 200), th=8.0, grow=1.0)
        ringz(b, add(c, (0, 0.1, 0)), R - 6, T_RED, "SmoothPlastic", th=0.2, name="TableBand")
        cyl(b, "TableLeg", sub(c, (0, 70, 0)), 130, 30, T_WOOD, "Wood", b.scenery)
        r.along(top_slider, [90, 170, 250])
    # ---- the bouncy balls: land on each and it throws you on to the next
    with look(sk, surface=plastic(T_PUR)):
        R2.bounce_chain(r, "Bouncy Balls", [(250.0, 20.0, 40.0), (240.0, 30.0, -60.0), (250.0, 10.0, 40.0)], 230.0, s=96.0,
                        cap=ball_cap((T_RED, T_BLUE, T_YEL)), land_L=150.0, cp=True, shroom=False)
        cube_obj(b, r, T_PUR, panel=False, depth=40)
    # ---- the giant spring up to the castle
    o = O.Obby(r, 230)
    with look(sk, surface=plastic(T_GRN), pad=spring_pad):
        o.plat("Spring Base", 100, 100)
        cube_obj(b, r, T_GRN, letter="S", depth=50)
        o.pad(110.0, label="Giant Spring")
    # ---- the castle: along the battlements, through the gatehouse, off the far tower
    with look(sk, surface=CASTLE_TOP):
        o.plat("Castle Wall", 320, 76, cp=True, boost=False)
        castle_wall(b, r)
        coin_row(b, R2.lerp3(span(r)[0], span(r)[1], 0.2), R2.lerp3(span(r)[0], span(r)[1], 0.8), n=5)
        o.drop(90.0, label="Tower Drop")
    # ---- the toy car ramp: an orange track kicker over a parked toy car
    with look(sk, surface=TOY_TRACK, rails={"edge": (255, 190, 90), "edge_mat": "SmoothPlastic", "side": T_ORG,
                                            "side_mat": "SmoothPlastic"}):
        o.plat("Track Run", 160, 80)
        r.turn("Track Sweep", -90, 140, rails=True)
        R2.ramp_jump(r, "Toy Ramp", deg=22, drop=50, w_land=110, slope=3, land_min=280, cp=True, rails=True)
        lip = b.jumps[-2][1]
        f = r.f
        for k, col in enumerate((T_BLUE, T_RED)):
            car = add(lip, add(mul(f, 120 + k * 80), (0, -90, (k - 0.5) * 40)))
            ob(b, "ToyCarBody", car, f, (30, 14, 54), col)
            ob(b, "ToyCarCab", add(car, (0, 12, -4)), f, (26, 10, 26), mix(col, WHITE, 0.4))
            for a in (-1, 1):
                for sd in (-1, 1):
                    cyl(b, "ToyCarWheel", add(car, add(mul(f, a * 18), add(mul(right_of(f), sd * 15), (0, -6, 0)))), 6, 14,
                        BLACK, "SmoothPlastic", b.scenery, axis=right_of(f))
    # ---- the seesaw: wait for it to level, then cross
    with look(sk, surface=plastic(T_YEL)):
        run(r, "Seesaw Ramp", 80, w=80)

        def seesaw_art(b_, m, c, f, L, w):
            Pt(b_, "SeesawPlank", CF(add(c, (0, -6, 0)), *axes(f)), (w - 4, 8, L - 4), T_YEL, "SmoothPlastic", m)
            for a in (-1, 1):
                Pt(b_, "SeesawSeat", CF(add(c, add(mul(f, a * (L / 2 - 12)), (0, -1, 0))), *axes(f)), (w - 10, 0.4, 16), T_RED,
                   "SmoothPlastic", m)
            M.tri(b_, "Fulcrum", add(c, add(mul(right_of(f), -w / 2), (0, -70, 0))),
                  add(c, add(mul(right_of(f), w / 2), (0, -70, 0))), add(c, (0, -11, 0)), T_RED, th=40)
        rock_bridge(r, "Toy Seesaw", 220, 70, T_YEL, amp_deg=9.0, period=4.2, art=seesaw_art)
        run(r, "Seesaw Exit", 100, w=80)
    # ---- the toy chest: drive into its open lid
    with look(sk, surface=TOY_SHELF):
        r.turn("Chest Turn", 90, 130)
        run(r, "Toy Chest", 200, w=140, cp=True)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        ob(b, "ChestBox", sub(c, (0, 50, 0)), f, (w + 30, 92, L + 30), (196, 120, 60), "WoodPlanks")
        for sd in (-1, 1):
            ob(b, "ChestBand", add(c, add(mul(right_of(f), sd * (w / 2 + 15.3)), (0, -40, 0))), f, (0.6, 10, L + 30), GOLD, "Metal")
        ob(b, "ChestLid", add(c, add(mul(right_of(f), -(w / 2 + 22)), (0, 66, 0))), f, (10, 140, L + 30), (176, 104, 50),
           "WoodPlanks")
        ob(b, "ChestLock", add(c, add(mul(right_of(f), -(w / 2 + 28)), (0, 120, 0))), f, (4, 18, 14), GOLD, "Metal")
        M.teddy(b, add(c, add(mul(right_of(f), w / 2 + 50), (0, 0, 0))), 40, yaw=math.atan2(-f[2], f[0]) + math.pi / 2)
    end_on_line(r, "Chest Run", margin=600)
    r.log("end")
    return ["Toy Shelf", "Alphabet Staircase", "Toy Track", "Baseplate Walls", "Toy Train", "Spinning Tops",
            "Bouncy Balls", "Giant Spring", "Castle Wall", "Toy Ramp", "Seesaw", "Toy Chest"]



def hashf(p, k=0):
    """A repeatable 0..1 number for a point (decorations that look random but never change between builds)."""
    v = math.sin(p[0] * 12.9898 + p[2] * 78.233 + k * 37.719) * 43758.5453
    return v - math.floor(v)


def sprinkles(cols, n_per=0.004, size=(1.2, 6.0)):
    """Sprinkles scattered on a surface (flat, so the wheels roll over them)."""
    def deco(sk, b, parent, fr, w, L):
        n = max(2, int(w * L * n_per))
        for k in range(n):
            x = (hashf(fr.p, k) - 0.5) * (w - 6)
            z = (hashf(fr.p, k + 99) - 0.5) * (L - 6)
            a = hashf(fr.p, k + 7) * math.pi
            cf = CF(off(fr, x=x, y=0.06, z=z), fr.x, fr.y, fr.z) * rot_y(a)
            Pt(b, "Sprinkle", cf, (size[0], 0.12, size[1]), cols[k % len(cols)], "SmoothPlastic", parent)
    return deco


def ride(r, label, D, dy=0.0, turn=0.0, head_fn=None, rail_col=(255, 60, 200), rail_mat="Neon", land_L=220.0,
         w_land=None, cp=False, tower_col=(40, 36, 60), speed=200.0):
    """The game's magnet ride with a themed head (a claw, a hook) and its overhead rail."""
    b = r.b
    f = r.f
    p0 = r.p
    th = math.radians(turn)
    c, s_ = math.cos(th), math.sin(th)
    f2 = RT.flat((f[0] * c + f[2] * s_, 0.0, -f[0] * s_ + f[2] * c))
    mid = RT.flat(add(f, f2))
    zone = add(p0, add(mul(f, -24), (0, 9, 0)))
    A = add(p0, add(mul(f, -24), (0, 5, 0)))
    E = add(p0, add(mul(mid, D), (0, dy, 0)))
    Dp = add(E, (0, 7, 0))
    Bp = add(A, add(mul(f, D * 0.35), (0, 150, 0)))
    Cp = add(Dp, add(mul(f2, -D * 0.3), (0, 40, 0)))
    home = add(A, (0, 30, 0))
    fr = deck_frame(zone, f)
    R2.magnet_ride(b, label.replace(" ", ""), A, Bp, Cp, Dp, CF(zone, fr.x, fr.y, fr.z), (r.w - 6, 24, 44), home,
                   speed=speed, out=170.0, perp=right_of(f), head_fn=head_fn or MX.crane_head)
    ringz(b, add(add(p0, mul(f, -24)), (0, 0.3, 0)), min(r.w / 2 - 4, 22), rail_col, "Neon", th=0.4, name="RideTarget")
    pts = [R2._bez(A, Bp, Cp, Dp, k / 24) for k in range(25)]
    for p in pts:
        b.path.append((p[0], p[1] + 1, p[2], "s"))
    ty = max(p[1] for p in pts) + 90
    for i in range(len(pts) - 1):
        a_, c_ = (pts[i][0], ty, pts[i][2]), (pts[i + 1][0], ty, pts[i + 1][2])
        dd = unit(sub(c_, a_))
        Pt(b, "RideRail", CF(R2.lerp3(a_, c_, 0.5), *axes(dd)), (8, 8, math.dist(a_, c_) + 1), rail_col, rail_mat, b.scenery)
    for q in (pts[0], pts[-1]):
        rt = right_of(f)
        for k in (-1, 1):
            t = add((q[0], ty, q[2]), mul(rt, k * 60))
            cyl(b, "RideTower", (t[0], ty - 90, t[2]), 180, 10, tower_col, "Metal", b.scenery)
        Pt(b, "RideHead", CF((q[0], ty + 8, q[2]), *axes(rt)), (12, 12, 130), tower_col, "Metal", b.scenery)
    r.p = E
    r.f = f2
    if w_land:
        r.w = w_land
    r.straight(label + " Drop Zone", land_L, lead=10.0, cp=cp)
    return r


# ===================================================================== 3. THE CANDY KINGDOM
C_PINK, C_MINT, C_LAV = (255, 150, 190), (140, 230, 196), (190, 160, 255)
C_CHOC, C_CHOC_DK, C_CREAM = (112, 64, 38), (78, 42, 24), (255, 244, 226)
C_RED = (230, 40, 60)
CANDY = [(255, 90, 140), (90, 200, 255), (255, 220, 80), (140, 230, 120), (190, 120, 255)]


class Candy(Giant):
    key, title, theme_name = "candy", "The Candy Kingdom", "Candy kingdom"
    clock, bloom, hue = 16.6, 0.5, 0.93
    body, top, edge, padc, danger = C_CHOC, C_PINK, C_MINT, C_MINT, (255, 60, 90)
    gate_post, gate_board, gate_text = C_CHOC, C_PINK, WHITE
    light_over = {"Lt_Atmosphere_Density": 0.22, "Lt_Atmosphere_Haze": 1.0, "Lt_CC_Saturation": 0.3}


WAFER = slab((236, 200, 140), "SmoothPlastic", th=8, side=(210, 168, 108),
             deco=both(lines_along((206, 164, 100), 12, name="WaferGrid"), lines_across((206, 164, 100), 12, name="WaferGrid")))
ICING = slab(C_PINK, "SmoothPlastic", th=4, deco=both(sprinkles(CANDY), edges(WHITE, width=3.0, name="IcingEdge")))
CHOC_RIVER = slab((96, 54, 30), "Glass", th=4, refl=0.25, deco=edges((140, 90, 60), width=6.0, name="RiverBank"))
CANE = slab(WHITE, "SmoothPlastic", th=4, deco=lines_across(C_RED, 20, width=9.0, name="CaneStripe"))
MINT = slab(C_MINT, "SmoothPlastic", th=4, deco=both(sprinkles([WHITE, C_PINK]), edges(WHITE, width=2.0, name="MintEdge")))


def gummy_bear(b, base, s, col, yaw=0.0):
    """A translucent gummy bear standing up (s: its height)."""
    from epic_marks import ell, Local
    L = M.Local(base, yaw)

    def E(name, p, size):
        ell(b, name, L.at(p[0] * s, p[1] * s, p[2] * s), tuple(v * s for v in size), col, "Glass", parent=b.scenery)
    E("GummyBody", (0, 0.42, 0), (0.62, 0.62, 0.5))
    E("GummyHead", (0, 0.86, 0), (0.46, 0.4, 0.4))
    for sx in (-1, 1):
        E("GummyEar", (sx * 0.17, 1.04, 0), (0.15, 0.15, 0.12))
        E("GummyArm", (sx * 0.3, 0.55, -0.08), (0.18, 0.3, 0.18))
        E("GummyLeg", (sx * 0.17, 0.12, -0.05), (0.22, 0.26, 0.26))


def lolly_obj(b, r, col):
    """A giant flat lollipop: its swirled disc is the stretch, a stick goes down from it."""
    c, R = disc_obj(b, r, col, th=10.0, grow=1.02)
    for k in range(4):
        ringz(b, add(c, (0, 0.1, 0)), R * (0.2 + 0.2 * k), WHITE, "SmoothPlastic", th=0.2, name="LollySwirl")
    cyl(b, "LollyStick", sub(c, (0, 110, 0)), 200, 12, WHITE, "SmoothPlastic", b.scenery)
    cyl(b, "LollyEdge", sub(c, (0, 5, 0)), 10.2, 2 * R + 1, mix(col, BLACK, 0.12), "SmoothPlastic", b.scenery)
    return c, R


def marsh_cap(cols):
    k = [0]

    def cap(b, top, s, rng):
        col = cols[k[0] % len(cols)]
        k[0] += 1
        cyl(b, "Platform", sub(top, (0, 1.5, 0)), 3, s * 0.95, col, "SmoothPlastic", b.roads, collide=True)
        cyl(b, "Marshmallow", sub(top, (0, 32, 0)), 58, s * 0.95, col, "SmoothPlastic", b.scenery)
        cyl(b, "MarshDust", add(top, (0, 0.05, 0)), 0.1, s * 0.7, WHITE, "SmoothPlastic", b.scenery, transp=0.4)
    return cap


def jelly_cap(cols):
    k = [0]

    def cap(b, top, s, rng):
        col = cols[k[0] % len(cols)]
        k[0] += 1
        Pt(b, "Platform", CF(sub(top, (0, 1.5, 0))), (s * 0.85, 3, s * 0.85), col, "Glass", b.roads, collide=True, transp=0.2)
        Pt(b, "JellyCube", CF(sub(top, (0, 34, 0))), (s * 0.85, 62, s * 0.85), col, "Glass", b.scenery, transp=0.35)
        Pt(b, "JellyShine", CF(add(top, (0, 0.05, 0))), (s * 0.3, 0.1, s * 0.6), WHITE, "Neon", b.scenery, transp=0.5)
    return cap


def donut(b, C, R, y, tube=70.0, dough=(222, 160, 90), icing=C_PINK, n=36):
    """A giant ring donut lying flat round centre C (its top at y): baked dough tube and a drippy icing band."""
    for k in range(n):
        a0, a1 = TAU * k / n, TAU * (k + 1) / n
        p0 = (C[0] + math.cos(a0) * R, y - tube / 2, C[2] + math.sin(a0) * R)
        p1 = (C[0] + math.cos(a1) * R, y - tube / 2, C[2] + math.sin(a1) * R)
        cyl(b, "DonutDough", R2.lerp3(p0, p1, 0.5), math.dist(p0, p1) + 2, tube, dough, "SmoothPlastic", b.scenery,
            axis=unit(sub(p1, p0)))
        if k % 2 == 0:
            q = R2.lerp3(p0, p1, 0.5)
            out = unit((q[0] - C[0], 0, q[2] - C[2]))
            cyl(b, "IcingDrip", add(q, add(mul(out, tube * 0.45), (0, tube * 0.22, 0))), 18 + (k % 3) * 6, 9, icing,
                "SmoothPlastic", b.scenery)


def cupcake_obj(b, r, col, rng):
    """A cupcake whose flat frosting top is the stretch: pleated liner, sponge, a cherry beside the line."""
    p0, p1, f, L, w, _ = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    R = math.hypot(L / 2, w / 2) * 1.04
    cyl(b, "Platform", sub(c, (0, 3, 0)), 6, 2 * R, col, "SmoothPlastic", b.roads, collide=True)
    cyl(b, "Sponge", sub(c, (0, 16, 0)), 20, 2 * R * 0.96, (214, 160, 100), "SmoothPlastic", b.scenery)
    hc = 80.0
    for k in range(5):
        t = (k + 0.5) / 5
        cyl(b, "Liner", sub(c, (0, 26 + hc * t, 0)), hc / 5 + 0.05, 2 * R * (0.9 - 0.18 * t), [WHITE, C_LAV][k % 2],
            "SmoothPlastic", b.scenery)
    for k in range(int(R * 0.5)):
        a = TAU * k / int(R * 0.5)
        q = (c[0] + math.cos(a) * R * 0.86, c[1] - 26 - hc * 0.45, c[2] + math.sin(a) * R * 0.86)
        ob(b, "Pleat", q, (math.cos(a), 0, math.sin(a)), (R * 0.14, hc * 0.86, 2.0), WHITE)
    side = right_of(f)
    ball(b, "Cherry", add(c, add(mul(side, R * 0.8), (0, 10, 0))), 20, C_RED, "SmoothPlastic", b.scenery, refl=0.2)
    return c, R


def gingerbread_house(b, c, f, s):
    rt = right_of(f)
    ob(b, "GingerWall", add(c, (0, s * 0.35, 0)), f, (s, s * 0.7, s * 1.2), (176, 104, 50))
    for sd in (-1, 1):
        q = add(c, add(mul(rt, sd * s * 0.27), (0, s * 0.92, 0)))
        Pt(b, "GingerRoof", CF(q, *axes(f)) * rot_axis((0, 0, 1), -sd * 0.7), (s * 0.66, 6, s * 1.3), (130, 74, 34),
           "SmoothPlastic", b.scenery)
        Pt(b, "RoofIcing", CF(add(q, (0, 0.5, 0)), *axes(f)) * rot_axis((0, 0, 1), -sd * 0.7), (s * 0.68, 2, s * 1.32), WHITE,
           "SmoothPlastic", b.scenery)
    ob(b, "GingerDoor", add(c, add(mul(f, -s * 0.6 - 0.3), (0, s * 0.2, 0))), f, (s * 0.25, s * 0.4, 0.6), C_PINK)
    for sd in (-1, 1):
        ob(b, "GingerWindow", add(c, add(add(mul(f, -s * 0.6 - 0.3), mul(rt, sd * s * 0.3)), (0, s * 0.46, 0))), f,
           (s * 0.16, s * 0.16, 0.6), (255, 220, 120), "Neon")
    for k in range(6):
        ball(b, "Gumdrop", add(c, add(mul(f, -s * 0.62), add(mul(rt, (k - 2.5) * s * 0.18), (0, s * 0.72, 0)))), s * 0.09,
             CANDY[k % 5], "SmoothPlastic", b.scenery)


def slot33(r, sk, rng):
    b = r.b
    stage(r, sk, "The Candy Kingdom", "OBBY 3 - LEVEL 3")
    # ---- the wafer walk: candy canes and lollipops line the way in
    with look(sk, surface=WAFER):
        run(r, "Wafer Walk", 240, w=120, boosts=2, every=60)
        p0, p1, f, L, w, _ = span(r)
        for k in range(4):
            for sd in (-1, 1):
                q = add(R2.lerp3(p0, p1, 0.12 + 0.25 * k), mul(right_of(f), sd * (w / 2 + 18)))
                if (k + sd) % 2:
                    M.candy_cane(b, sub(q, (0, 0, 0)), 70, 7, yaw=math.atan2(-f[2], f[0]) + (math.pi if sd > 0 else 0))
                else:
                    M.lollipop(b, q, 50, 34, CANDY[k % 5], rng)
    # ---- the chocolate river: the current carries you, past gummy bears standing in it
    with look(sk, surface=CHOC_RIVER):
        R2.belt_road(r, "Chocolate River", 420, 60.0, direction="along", w=120, cp=True)
        p0, p1, f, L, w, _ = span(r)
        for k in range(4):
            sd = 1 if k % 2 else -1
            gummy_bear(b, add(R2.lerp3(p0, p1, 0.15 + 0.22 * k), mul(right_of(f), sd * 34)), 34, CANDY[k],
                       yaw=math.atan2(-f[2], f[0]))
        for k in range(8):
            q = add(R2.lerp3(p0, p1, (k + 0.5) / 8), add(mul(right_of(f), (hashf(p0, k) - 0.5) * 60), (0, 0.08, 0)))
            ob(b, "ChocSwirl", q, f, (10, 0.12, 30), (140, 90, 60))
        ob(b, "RiverBed", sub(R2.lerp3(p0, p1, 0.5), (0, 16, 0)), f, (w + 40, 24, L), C_CHOC_DK)
        # over the chocolate falls
        lip = r.p
        R2.drop_off(r, "Chocolate Falls", 70.0, w=120, L=260, cp=False)
        for sd in (-1, 1):
            q = add(lip, add(mul(right_of(f), sd * 50), (0, -35, 0)))
            ob(b, "ChocFall", add(q, mul(f, 4)), f, (24, 70, 2), (110, 64, 36), "Glass", transp=0.15)
        ob(b, "RiverBed", sub(R2.lerp3(span(r)[0], span(r)[1], 0.5), (0, 16, 0)), f, (w + 40, 24, span(r)[3]), C_CHOC_DK)
    # ---- the lollipops: hop across their flat swirled tops
    o = O.Obby(r, 230)
    with look(sk, surface=ghost):
        for k, (dy, side) in enumerate(((0.0, 60.0), (-20.0, -70.0), (10.0, 60.0))):
            o.kick(dy=dy, side=side, label="Lolly Hop %d" % (k + 1))
            o.plat("Lollipop %d" % (k + 1), 100, 92, cp=(k == 1))
            lolly_obj(b, r, CANDY[(k + 1) % 5])
            coin_arc(b, -1, n=4)
    # ---- round the giant donut, on its icing
    with look(sk, surface=ICING):
        o.kick(dy=0.0, label="Donut Hop")
        o.plat("Donut Icing", 60, 80)
        r.turn("Donut Ride", -270, 170, cp=True)
        donut(b, r.centre, 170, r.p[1] - 4.5, tube=80)
        cyl(b, "DonutHole", (r.centre[0], r.p[1] - 120, r.centre[2]), 4, 180, C_CHOC_DK, "Glass", b.scenery, transp=0.3)
        run(r, "Donut Exit", 80)
    # ---- the marshmallows: bounce from one to the next
    with look(sk, surface=MINT):
        R2.bounce_chain(r, "Marshmallow Bounce", [(240.0, 20.0, 50.0), (240.0, 10.0, -60.0), (240.0, -10.0, 40.0)], 230.0,
                        s=90.0, cap=marsh_cap((WHITE, C_PINK, C_MINT)), land_L=120.0, cp=True, shroom=False)
    # ---- the candy cane bridge: narrow, over the chocolate falls
    with look(sk, surface=CANE):
        run(r, "Cane Bridge Up", 120, w=44, dy=24)
        run(r, "Cane Bridge", 160, w=44)
        coin_row(b, span(r)[0], span(r)[1], n=5)
        run(r, "Cane Bridge Down", 120, w=44, dy=-24)
        for q in (span(r)[1],):
            M.candy_cane(b, add(q, mul(right_of(r.f), 30)), 60, 8)
    # ---- the chocolate bar: its squares break off and drop a moment after you touch them
    with look(sk, surface=WAFER):
        run(r, "Bar Wrapper", 60, w=120)
    R2.sink_board(r, "Chocolate Bar", 320, 120, cell=40, cols=((112, 64, 38), (98, 56, 32)),
                  mats=("SmoothPlastic", "SmoothPlastic"), delay=0.35, rate=70.0, cp=True)
    with look(sk, surface=WAFER):
        run(r, "Bar End", 80, w=120)
        r.turn("Wafer Bend", -90, 140)
    # ---- the cupcakes: launch pads up their frosting tops
    o = O.Obby(r, 230)
    with look(sk, surface=ghost):
        for k, col in enumerate((C_PINK, C_MINT, C_LAV)):
            o.pad(50.0, side=(40, -40, 30)[k], label="Cupcake Pad %d" % (k + 1))
            o.plat("Cupcake %d" % (k + 1), 110, 96, cp=(k == 1))
            cupcake_obj(b, r, col, rng)
            p0, p1, f, L, w, _ = span(r)
            coin_row(b, p0, p1, n=3)
    # ---- the jelly cubes: wobbly, bouncy, see-through
    with look(sk, surface=ICING):
        o.plat("Jelly Run", 120, 100)
        R2.bounce_chain(r, "Jelly Bounce", [(240.0, -20.0, -50.0), (240.0, -30.0, 50.0), (240.0, -40.0, 0.0)], 230.0, s=96.0,
                        cap=jelly_cap((C_RED, (90, 200, 120), (255, 170, 40))), land_L=160.0, cp=True, shroom=False)
    # ---- the gingerbread house at the end of the road
    with look(sk, surface=WAFER):
        r.turn("Gingerbread Bend", -50, 220)
        run(r, "Gingerbread Lane", 260, w=140)
        p0, p1, f, L, w, _ = span(r)
        for sd in (-1, 1):
            gingerbread_house(b, add(R2.lerp3(p0, p1, 0.5), mul(right_of(f), sd * (w / 2 + 70))), mul(right_of(f), -sd), 80)
    with look(sk, surface=WAFER):
        r.turn("Gingerbread Exit", 50, 220)
    end_on_line(r, "Candy Run", margin=500)
    r.log("end")
    return ["Wafer Walk", "Chocolate River", "Chocolate Falls", "Lollipop Hops", "Donut Ride", "Marshmallow Bounce",
            "Candy Cane Bridge", "Chocolate Bar", "Cupcake Climb", "Jelly Bounce", "Gingerbread Lane"]


# ===================================================================== 4. THE ABANDONED ARCADE
N_PINK, N_CYAN, N_YEL, N_GRN, N_PUR, N_ORG = (255, 60, 200), (40, 240, 255), (255, 230, 60), (80, 255, 120), (150, 80, 255), (255, 140, 40)
NEON = [N_PINK, N_CYAN, N_YEL, N_GRN, N_PUR, N_ORG]


class Arcade(Giant):
    key, title, theme_name = "arcade", "The Abandoned Arcade", "Abandoned arcade"
    clock, bloom, hue = 0.5, 1.1, 0.75
    body, top, edge, padc, danger = (30, 24, 52), (26, 24, 48), N_CYAN, N_PINK, (255, 50, 80)
    gate_post, gate_board, gate_text = (30, 24, 52), (16, 14, 26), N_PINK
    NEON = NEON
    light_over = {"Lt_Atmosphere_Density": 0.32, "Lt_Atmosphere_Haze": 1.4, "Lt_Lighting_Brightness": 1.6,
                  "Lt_Bloom_Intensity": 1.1, "Lt_Bloom_Threshold": 1.0}


def confetti(sk, b, parent, fr, w, L):
    n = max(3, int(w * L * 0.0025))
    for k in range(n):
        x = (hashf(fr.p, k) - 0.5) * (w - 8)
        z = (hashf(fr.p, k + 50) - 0.5) * (L - 8)
        a = hashf(fr.p, k + 3) * math.pi
        cf = CF(off(fr, x=x, y=0.06, z=z), fr.x, fr.y, fr.z) * rot_y(a)
        Pt(b, "Confetti", cf, (1.4, 0.12, 9 + 6 * hashf(fr.p, k + 9)), NEON[k % 6], "Neon", parent)


def grid_lines(col, every=20.0):
    return both(lines_along(col, every, mat="Neon", width=0.5, name="GridLine"),
                lines_across(col, every, mat="Neon", width=0.5, name="GridLine"))


CARPET = slab((26, 24, 52), "Fabric", th=4, deco=both(confetti, edges(N_CYAN, "Neon", width=1.2, name="NeonEdge")))
PANEL = slab((44, 38, 70), "SmoothPlastic", th=6, side=(30, 24, 52), deco=edges(N_PINK, "Neon", width=1.4, name="NeonEdge"))
PIXEL = slab((14, 12, 30), "SmoothPlastic", th=4, deco=both(grid_lines((60, 40, 140)), edges(N_GRN, "Neon", width=1.4,
                                                                                               name="NeonEdge")))
PINBALL = slab((44, 20, 74), "SmoothPlastic", th=4, deco=both(lines_along((90, 60, 140), 30, name="Lane"),
                                                              edges(N_YEL, "Neon", width=1.6, name="NeonEdge")))


def claw_head(b, head, home):
    """A claw-machine claw: a hub and three gold prongs."""
    cyl(b, "ClawHub", home, 10, 16, GOLD, "Metal", head, refl=0.3)
    for k in range(3):
        a = TAU * k / 3
        d = (math.cos(a), 0, math.sin(a))
        q = add(home, add(mul(d, 10), (0, -10, 0)))
        Pt(b, "ClawProng", CF(q, *axes(d)) * rot_axis((1, 0, 0), 0.4), (3, 22, 3), GOLD, "Metal", head)
    cyl(b, "ClawCable", add(home, (0, 40, 0)), 70, 1.6, (200, 200, 210), "Metal", head)
    ball(b, "ClawLight", add(home, (0, 6, 0)), 5, N_PINK, "Neon", head)


def giant_button(b, c, w, i):
    """An oversized arcade button at the edge of the panel: press it and it bounces you off (go between)."""
    x, y, z = c
    sd = 1 if i % 2 == 0 else -1
    q = (x, y, z + sd * w * 0.3)
    col = NEON[i % 6]
    cyl(b, "ButtonRing", add(q, (0, 2, 0)), 4, 34, (20, 18, 30), "SmoothPlastic", b.scenery)
    cyl(b, "ArcadeButton", add(q, (0, 6, 0)), 8, 28, col, "Neon", b.hazards, query=True, attrs={"ObbyHazard": "Knock"})


def spin_coin(b, c, w, i, d=44.0, speed=0.5):
    """A giant spinning gold coin standing on the road (knocks you away): pass it on the side it leaves open."""
    x, y, z = c
    sd = 1 if i % 2 == 0 else -1
    q = (x, y + d / 2 + 2, z + sd * w * 0.22)
    root = b.prop_root("GiantCoin")
    rig = b.rig(root, "Spin", axis_frame(q, UP), speed * sd, 1, phase=(i * 0.3) % 1, name="CoinSpin")
    cyl(b, "GiantCoin", q, 5, d, (255, 210, 40), "Metal", rig, axis=(0, 0, 1), query=True, attrs={"ObbyHazard": "Knock"},
        refl=0.3)
    cyl(b, "CoinFace", q, 5.4, d * 0.72, (255, 236, 130), "Neon", rig, axis=(0, 0, 1))
    cyl(b, "CoinStand", (x, y + 1, z + sd * w * 0.22), 2, 18, (40, 36, 60), "Metal", b.scenery)


def pixel_screen(b, c, f, w, h, rows, px_col):
    """The giant screen's bezel round a breakable wall of pixels (smash through it)."""
    rt = right_of(f)
    for sd in (-1, 1):
        ob(b, "Bezel", add(c, add(mul(rt, sd * (w / 2 + 8)), (0, h / 2, 0))), f, (16, h + 20, 14), (20, 18, 30), collide=True)
    ob(b, "BezelTop", add(c, (0, h + 10, 0)), f, (w + 32, 20, 14), (20, 18, 30))
    ob(b, "ScreenGlow", add(c, (0, h + 21, 0)), f, (w + 30, 1.2, 15), N_CYAN, "Neon")
    nx, ny = len(rows[0]), len(rows)
    cols = []
    for j in range(ny):
        for i in range(nx):
            cols.append(px_col if rows[ny - 1 - j][i] == "1" else (20, 30, 70))
    MX.brick_wall(b, c, f, w, h=h, kind="pixel", nx=nx, ny=ny, cols=cols, mat="Neon", depth=6)


def slot34(r, sk, rng):
    b = r.b
    stage(r, sk, "The Abandoned Arcade", "OBBY 3 - LEVEL 4")
    # ---- the arcade floor: rows of giant cabinets on both sides, their screens still glowing
    with look(sk, surface=CARPET):
        run(r, "Arcade Carpet", 260, w=130, boosts=2, every=60)
        p0, p1, f, L, w, _ = span(r)
        yaw = math.atan2(-f[2], f[0])
        for k in range(3):
            for sd in (-1, 1):
                q = add(R2.lerp3(p0, p1, 0.18 + 0.32 * k), mul(right_of(f), sd * (w / 2 + 40)))
                M.cabinet(b, q, 50, 110, 44, sk, yaw=yaw + (math.pi / 2 if sd < 0 else -math.pi / 2))
    # ---- up the control panel of a giant cabinet, past its buttons, off the marquee
    with look(sk, surface=PANEL):
        run(r, "Control Panel", 300, w=120, dy=40, cp=True)
        r.along(giant_button, [80, 150, 220])
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        ob(b, "CabinetBody", (c[0], p0[1] - 8 - 80, c[2]), f, (w + 20, 160, L), (30, 24, 52))
        for sd in (-1, 1):
            q = mul(right_of(f), sd * (w / 2 + 8))
            M.tri(b, "CabinetCheek", add((p0[0], p0[1] - 8, p0[2]), q), add((p1[0], p1[1] - 8, p1[2]), q),
                  add((p1[0], p0[1] - 8, p1[2]), q), (30, 24, 52), th=4)
        stick = add(R2.lerp3(p0, p1, 0.5), add(mul(right_of(f), -(w / 2 + 30)), (0, 0, 0)))
        cyl(b, "GiantJoystick", add(stick, (0, 30, 0)), 60, 8, (30, 30, 36), "SmoothPlastic", b.scenery)
        ball(b, "JoystickBall", add(stick, (0, 66, 0)), 26, N_PINK, "SmoothPlastic", b.scenery)
        run(r, "Cabinet Top", 160, w=120)
        for sd in (-1, 1):
            ob(b, "Marquee", add(R2.lerp3(span(r)[0], span(r)[1], 0.5), add(mul(right_of(f), sd * 70), (0, 30, 0))), f,
               (12, 60, 140), (30, 24, 52))
            ob(b, "MarqueeGlow", add(R2.lerp3(span(r)[0], span(r)[1], 0.5), add(mul(right_of(f), sd * 63.8), (0, 30, 0))), f,
               (0.4, 40, 120), NEON[(sd + 1) // 2], "Neon")
        R2.ramp_jump(r, "Marquee Jump", deg=18, drop=60, w_land=130, slope=3, land_min=300, cp=True, rails=False)
        coin_arc(b, -2, n=6)
    # ---- the giant keyboard: the keys sink as you drive over them, keep moving
    with look(sk, surface=PIXEL):
        run(r, "Keyboard Edge", 60, w=130)
    R2.sink_board(r, "Giant Keyboard", 360, 120, cell=40, cols=((236, 236, 244), (200, 200, 214)),
                  mats=("SmoothPlastic", "SmoothPlastic"), delay=0.3, rate=80.0, cp=True)
    with look(sk, surface=PIXEL):
        p_kb = r.p
        run(r, "Keyboard Exit", 80, w=130)
        r.turn("Neon Bend", 90, 140)
    # ---- the pixel hops: floating digital blocks
    o = O.Obby(r, 230)
    with look(sk, surface=PIXEL):
        for k, (dy, side) in enumerate(((0.0, 70.0), (-20.0, -70.0), (0.0, 70.0))):
            o.kick(dy=dy, side=side, label="Pixel Hop %d" % (k + 1))
            o.plat("Pixel Block %d" % (k + 1), 90, 90, cp=(k == 1))
            p0, p1, f, L, w, _ = span(r)
            c = R2.lerp3(p0, p1, 0.5)
            ob(b, "PixelBody", sub(c, (0, 30, 0)), f, (w, 56, L), (20, 16, 40))
            for sd in (-1, 1):
                ob(b, "PixelGlow", add(c, add(mul(right_of(f), sd * (w / 2 + 0.3)), (0, -30, 0))), f, (0.4, 50, L - 6),
                   NEON[k], "Neon")
            coin_arc(b, -1, n=4)
    # ---- the pinball table: bumpers and flippers
    import speedway as SW
    with look(sk, surface=PINBALL, rails={"edge": N_YEL, "side": (30, 24, 52), "side_mat": "SmoothPlastic"}):
        o.kick(dy=-20.0, label="Pinball Drop")
        o.plat("Pinball Table", 420, 150, cp=True)
        SW.bumper_field(r, [(90, -40), (90, 40), (170, 0), (250, -45), (250, 45)], 150, rng)
        r.along(lambda b_, c, w, i: SW.flippers(b_, c, w, i), [340])
    # ---- the coin pusher: giant spinning coins to dodge, a row of real ones to grab
    with look(sk, surface=CARPET):
        r.turn("Coin Bend", -90, 140)
        run(r, "Coin Pusher", 360, w=120, cp=True)
        r.along(spin_coin, [80, 170, 260])
        coin_row(b, span(r)[0], span(r)[1], n=8)
    # ---- the claw: it grabs the car and carries it over the gap
    with look(sk, surface=CARPET):
        run(r, "Claw Machine", 90, w=90)
        ride(r, "The Claw", 380.0, dy=-20.0, head_fn=claw_head, rail_col=N_PINK, land_L=200.0, w_land=110, cp=True)
    # ---- the big screen: smash straight through its wall of pixels
    with look(sk, surface=PIXEL):
        r.turn("Screen Bend", -45, 220)
        run(r, "Screen Run", 240, w=130, boosts=3, every=40)
        p, f = at(r, 180)
        pixel_screen(b, p, f, 110, 60, M.GHOST, N_PINK)
        run(r, "High Score", 200, w=140)
        p0, p1, f, L, w, _ = span(r)
        for k, sd in enumerate((-1, 1)):
            q = add(R2.lerp3(p0, p1, 0.5), mul(right_of(f), sd * (w / 2 + 40)))
            M.cabinet(b, q, 50, 110, 44, sk, yaw=math.atan2(-f[2], f[0]) + (math.pi / 2 if sd < 0 else -math.pi / 2))
    with look(sk, surface=PIXEL):
        r.turn("Score Bend", 45, 220)
    end_on_line(r, "Arcade Run", margin=500)
    r.log("end")
    return ["Arcade Floor", "Control Panel", "Marquee Jump", "Giant Keyboard", "Pixel Hops", "Pinball Table",
            "Coin Pusher", "The Claw", "Big Screen"]



# ===================================================================== more shared machines
def swing_bridge(r, label, L, w, col, mat="SmoothPlastic", amp_deg=8.0, period=4.2, phase=0.0, art=None):
    """A stretch rolling side to side about its centre line (it carries the car)."""
    b = r.b
    f = r.f
    c = add(r.p, mul(f, L / 2 + 2))
    yaw = math.atan2(-f[2], f[0])
    m = R2.rotor(b, label.replace(" ", ""), CF(c) * rot_y(yaw), (1, 0, 0), "swing", amp=math.radians(amp_deg),
                 period=period, phase=phase, near=L)
    Pt(b, "MovingDeck", CF(add(c, (0, -2, 0)), *axes(f)), (w, 4, L), col, mat, m, collide=True, attrs={"ClockDeck": True})
    if art:
        art(b, m, c, f, L, w)
    R2._special_line(b, r.p, add(r.p, mul(f, L + 4)), 6)
    b.samples.append(c + (w,))
    r.p = add(r.p, mul(f, L + 4))
    return c


def drum(r, label, L, R, col, mat="SmoothPlastic", speed=0.2, ridge_col=(255, 200, 0), art=None):
    """A giant drum turning about the road's own line: drive along its top, its ridges come over (jump them)."""
    b = r.b
    f = r.f
    p0 = r.p
    c = add(p0, add(mul(f, L / 2), (0, -R, 0)))
    root = b.prop_root(label.replace(" ", ""))
    rig = b.rig(root, "Spin", axis_frame(c, f), speed, 1, phase=0.0, name="DrumSpin")
    Pt(b, "MovingDeck", axis_frame(c, f), (L, 2 * R, 2 * R), col, mat, rig, collide=True, shape=2)
    for k in range(3):
        a = TAU * k / 3
        up = add(mul(right_of(f), math.sin(a)), (0, math.cos(a), 0))
        Pt(b, "Ridge", deck_frame(add(c, mul(up, R + 1.2)), f, up=up), (5, 3, L - 10), ridge_col, "SmoothPlastic", rig,
           query=True, attrs={"ObbyHazard": "Knock"})
    if art:
        art(b, rig, c, f, L, R)
    b.samples.append((c[0], p0[1], c[2], 2 * R))
    for k in range(6):
        b.line(*add(p0, mul(f, L * k / 5)))
    r.p = add(p0, mul(f, L + 2))
    return c


def sweeper(b, c, w, i, arm_fn, speed=0.24, hub_col=(60, 60, 70), tower_fn=None, hz="Knock"):
    """A long arm on a post at the road's edge sweeping half round across it and back (like a crane's jib, a robot's
    arm, a tentacle): arm_fn(b, rig, hub, L) draws the arm pointing +X from the hub."""
    x, y, z = c
    s_ = 1 if i % 2 == 0 else -1
    hub = (x, y + 8, z + s_ * (w / 2 + 12))
    if tower_fn:
        tower_fn(b, hub)
    root = b.prop_root("Sweeper")
    period = 1.0 / max(abs(speed), 0.05) * 0.9
    rig = b.rig(root, "Hinge", axis_frame(add(hub, (0, 2, 0)), (0, 1, 0)), 180.0 * s_, period, phase=(i * 0.19) % 1,
                keys="0:0 0.12:0 0.5:1 0.62:1 1:0", name="ArmSweep")
    arm_fn(b, rig, hub, w + 4)
    for d in rig.descendants():
        if d.cls in ("Part", "WedgePart") and d.name != "Pivot":
            import rbxl
            a = rbxl.attrs(d) or {}
            a["ObbyHazard"] = hz
            rbxl.set_attrs(d, a)
            d.set("CanQuery", True)


# ===================================================================== 5. THE ENCHANTED FOREST
F_MOSS, F_BARK, F_BARK_DK = (78, 140, 66), (112, 76, 48), (80, 54, 34)
F_GLOW, F_GLOW2, F_PETAL = (120, 255, 210), (200, 140, 255), (255, 130, 200)
F_LILY, F_WATER = (70, 160, 80), (70, 150, 200)


class Forest(Giant):
    key, title, theme_name = "forest", "The Enchanted Forest", "Enchanted forest"
    clock, bloom, hue = 18.4, 0.9, 0.42
    body, top, edge, padc, danger = F_BARK, F_MOSS, F_GLOW, F_GLOW, (255, 80, 140)
    gate_post, gate_board, gate_text = F_BARK_DK, (40, 60, 40), F_GLOW
    light_over = {"Lt_Atmosphere_Density": 0.34, "Lt_Atmosphere_Haze": 1.6, "Lt_Lighting_Brightness": 2.0,
                  "Lt_Bloom_Intensity": 0.9, "Lt_Bloom_Threshold": 1.05}


BARK = slab(F_BARK, "Wood", th=6, side=F_BARK_DK, deco=lines_along(F_BARK_DK, 9, width=1.0, name="BarkGrain"))
MOSS = slab(F_MOSS, "Grass", th=4, deco=edges((60, 110, 50), width=4.0, name="MossEdge"))
LEAF = slab((90, 170, 70), "SmoothPlastic", th=3, deco=both(lines_along((60, 130, 50), 1000.0), edges((120, 200, 90), width=2.0,
                                                                                                   name="LeafEdge")))
STONE = slab((130, 136, 140), "Slate", th=6, deco=edges((100, 110, 116), width=3.0, name="StoneEdge"))


def leaf_vein(sk, b, parent, fr, w, L):
    Pt(b, "LeafVein", F(fr, off(fr, y=0.07)), (2.0, 0.14, L), (190, 240, 140), "SmoothPlastic", parent)
    d = -L / 2 + 16
    k = 0
    while d < L / 2 - 10:
        for sd in (-1, 1):
            q = off(fr, x=sd * w * 0.22, y=0.07, z=d + 8)
            Pt(b, "LeafVein", CF(q, fr.x, fr.y, fr.z) * rot_y(sd * 0.6), (1.2, 0.14, w * 0.5), (170, 230, 120), "SmoothPlastic",
               parent)
        d += 28


LEAF = slab((90, 170, 70), "SmoothPlastic", th=3, deco=both(leaf_vein, edges((120, 200, 90), width=2.0, name="LeafEdge")))


def firefly(b, p, col=None):
    ball(b, "Firefly", p, 2.2, col or (255, 240, 140), "Neon", b.scenery)


def glow_plant(b, base, h, col):
    cyl(b, "GlowStem", add(base, (0, h / 2, 0)), h, 2.4, (60, 120, 70), "SmoothPlastic", b.scenery)
    ball(b, "GlowBulb", add(base, (0, h + 4, 0)), 9, col, "Neon", b.scenery)
    for k in range(3):
        a = TAU * k / 3
        Pt(b, "GlowLeaf", CF(add(base, (math.cos(a) * 5, h * 0.4, math.sin(a) * 5))) * rot_y(-a) * rot_axis((0, 0, 1), 0.6),
           (12, 0.6, 5), (80, 180, 90), "SmoothPlastic", b.scenery)


def shroom_cap(cols, rng):
    k = [0]

    def cap(b, top, s, rng_):
        col = cols[k[0] % len(cols)]
        k[0] += 1
        d = s * 1.05
        cyl(b, "Platform", sub(top, (0, 1.5, 0)), 3, d * 0.96, col, "SmoothPlastic", b.roads, collide=True)
        M.ell(b, "Cap", sub(top, (0, d * 0.16, 0)), (d, d * 0.36, d), col, parent=b.scenery)
        for j in range(8):
            a = TAU * j / 8 + 0.3
            rr = d * (0.2 + 0.18 * (j % 3))
            cyl(b, "CapSpot", add(top, (math.cos(a) * rr, 0.08, math.sin(a) * rr)), 0.15, d * 0.1, (255, 255, 240),
                "SmoothPlastic", b.scenery)
        cyl(b, "Gills", sub(top, (0, d * 0.32, 0)), 2, d * 0.9, F_GLOW, "Neon", b.scenery)
        cyl(b, "Stem", sub(top, (0, d * 0.32 + 90, 0)), 180, d * 0.28, (240, 232, 210), "SmoothPlastic", b.scenery)
    return cap


def tree_core(b, base, R):
    """A giant tree trunk the branch road spirals round, its roots and a glowing canopy high above."""
    c = (base[0], base[1], base[2])
    cyl(b, "TreeTrunk", (c[0], c[1] - 40, c[2]), 520, R * 1.1, F_BARK, "Wood", b.scenery)
    for k in range(8):
        a = TAU * k / 8
        ob(b, "BarkRidge", (c[0] + math.cos(a) * R * 0.55, c[1] - 40, c[2] + math.sin(a) * R * 0.55), (math.cos(a), 0, math.sin(a)),
           (6, 500, 10), F_BARK_DK, "Wood")
    for k in range(5):
        a = TAU * k / 5 + 0.4
        M.ell(b, "Canopy", (c[0] + math.cos(a) * 90, c[1] + 300 + (k % 2) * 30, c[2] + math.sin(a) * 90), (220, 90, 220),
              (60, 130, 70), parent=b.scenery)
    for k in range(14):
        a = TAU * k / 14
        firefly(b, (c[0] + math.cos(a) * (R * 0.9), c[1] + 60 + (k * 37) % 180, c[2] + math.sin(a) * (R * 0.9)),
                [F_GLOW, (255, 240, 140), F_GLOW2][k % 3])


def lily_obj(b, r, rng):
    c, R = disc_obj(b, r, F_LILY, th=3.0, grow=1.03)
    ob(b, "LilyNotch", add(c, add(mul(right_of(r.f), R * 0.75), (0, 0.05, 0))), right_of(r.f), (R * 0.12, 0.12, R * 0.5),
       (40, 110, 60))
    for k in range(6):
        a = TAU * k / 6
        ob(b, "LilyVein", add(c, (math.cos(a) * R * 0.45, 0.06, math.sin(a) * R * 0.45)), (math.cos(a), 0, math.sin(a)),
           (1.0, 0.12, R * 0.8), (100, 190, 100))
    cyl(b, "PondWater", sub(c, (0, 30, 0)), 1, 2 * R + 140, F_WATER, "Glass", b.scenery, transp=0.45)
    if rng.random() < 0.7:
        q = add(c, (R * 0.5, 2, -R * 0.3))
        for k in range(6):
            a = TAU * k / 6
            Pt(b, "LilyPetal", CF(add(q, (math.cos(a) * 6, 4, math.sin(a) * 6))) * rot_y(-a) * rot_axis((0, 0, 1), 0.7),
               (12, 1, 6), F_PETAL, "SmoothPlastic", b.scenery)


def flower_pad(sk, b, start, f):
    """A giant glowing flower round the launch: petals all round, a bright centre."""
    for k in range(8):
        a = TAU * k / 8
        q = add(start, (math.cos(a) * 30, -2, math.sin(a) * 30))
        Pt(b, "FlowerPetal", CF(q) * rot_y(-a), (36, 2, 18), [F_PETAL, F_GLOW2][k % 2], "SmoothPlastic", b.scenery)
    cyl(b, "FlowerCentre", add(start, (0, 0.1, 0)), 0.2, 26, (255, 220, 80), "Neon", b.scenery)
    cyl(b, "FlowerStem", add(start, (0, -100, 0)), 190, 10, (70, 140, 60), "SmoothPlastic", b.scenery)


def slot35(r, sk, rng):
    b = r.b
    stage(r, sk, "The Enchanted Forest", "OBBY 3 - LEVEL 5")
    # ---- along the top of a mossy fallen log, glowing plants and fireflies all round
    with look(sk, surface=MOSS):
        run(r, "Mossy Log", 280, w=96, boosts=2, every=60)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        cyl(b, "FallenLog", sub(c, (0, 62, 0)), L + 40, 130, F_BARK, "Wood", b.scenery, axis=f)
        cyl(b, "LogEnd", sub(add(c, mul(f, L / 2 + 20)), (0, 62, 0)), 2, 124, (200, 160, 110), "Wood", b.scenery, axis=f)
        for k in range(6):
            sd = 1 if k % 2 else -1
            glow_plant(b, add(R2.lerp3(p0, p1, 0.1 + 0.16 * k), mul(right_of(f), sd * (w / 2 + 6))), 20 + (k % 3) * 8,
                       [F_GLOW, F_GLOW2, (255, 230, 120)][k % 3])
            firefly(b, add(R2.lerp3(p0, p1, 0.15 + 0.15 * k), (sd * 40, 30 + k * 4, 0)))
    # ---- the toadstools: bounce from cap to cap
    with look(sk, surface=MOSS):
        R2.bounce_chain(r, "Toadstool Bounce", [(250.0, 30.0, 50.0), (250.0, 20.0, -60.0), (250.0, 10.0, 40.0)], 230.0, s=100.0,
                        cap=shroom_cap(((220, 50, 50), (150, 80, 220), (255, 140, 40)), rng), land_L=140.0, cp=True,
                        shroom=True)
        p0, p1, f, L, w, _ = span(r)
        cyl(b, "MossyStump", sub(R2.lerp3(p0, p1, 0.5), (0, 50, 0)), 92, max(L, w) + 10, F_BARK, "Wood", b.scenery)
    # ---- the great tree: spiral up a branch round its trunk
    with look(sk, surface=BARK, rails={"edge": F_GLOW, "edge_mat": "Neon", "side": F_BARK_DK, "side_mat": "Wood"}):
        run(r, "Root Ramp", 120, w=70)
        r.spiral("Branch Spiral", 1.0, 110, 150, w=70, side=1, core=tree_core, cp=True, rails=True)
        run(r, "Branch Tip", 120, w=64)
    # ---- the leaves: drop down from leaf to floating leaf; the last one rocks in the breeze
    o = O.Obby(r, 230)
    with look(sk, surface=LEAF):
        o.drop(50.0, side=60.0, label="Leaf Drop")
        o.plat("Big Leaf", 150, 90, cp=True)
        o.drop(50.0, side=-60.0, label="Leaf Drop 2")
        o.plat("Broad Leaf", 140, 90)
        coin_row(b, span(r)[0], span(r)[1], n=4)
    with look(sk, surface=LEAF):
        def leaf_art(b_, m, c, f, L, w):
            Pt(b_, "LeafStalk", CF(add(c, add(mul(f, -L / 2 - 20), (0, -1, 0))), *axes(f)), (3, 2, 40), (60, 120, 50),
               "SmoothPlastic", m)
            for sd in (-1, 1):
                Pt(b_, "LeafRim", CF(add(c, add(mul(right_of(f), sd * (w / 2 + 3)), (0, -2, 0))), *axes(f)), (6, 3, L * 0.9),
                   (110, 190, 80), "SmoothPlastic", m)
        swing_bridge(r, "Rocking Leaf", 220, 80, (90, 170, 70), amp_deg=7.0, period=4.6, art=leaf_art)
        run(r, "Leaf Tip", 80, w=80)
    # ---- the flowers: a glowing bloom launches you up to the lily pond
    with look(sk, surface=MOSS, pad=flower_pad):
        o = O.Obby(r, 230)
        o.plat("Flower Bed", 120, 100, cp=True)
        o.pad(70.0, label="Flower Launch")
    # ---- the lily pads: hop across the pond
    with look(sk, surface=ghost):
        o.plat("Lily Pad 1", 100, 90)
        lily_obj(b, r, rng)
        for k, (dy, side) in enumerate(((-10.0, 70.0), (-10.0, -70.0), (0.0, 70.0))):
            o.kick(dy=dy, side=side, label="Lily Hop %d" % (k + 1))
            o.plat("Lily Pad %d" % (k + 2), 100, 90, cp=(k == 1))
            lily_obj(b, r, rng)
            coin_arc(b, -1, n=4)
    # ---- the waterfall: over the edge beside the falls, onto the stepping stones
    with look(sk, surface=STONE):
        o.kick(dy=0.0, label="Stone Hop")
        o.plat("River Stone", 120, 110)
        lip = r.p
        f = r.f
        R2.drop_off(r, "Waterfall Drop", 90.0, w=110, L=300, cp=True)
        for sd in (-1, 1):
            q = add(lip, add(mul(right_of(f), sd * 75), (0, -40, 0)))
            ob(b, "Waterfall", add(q, mul(f, 10)), f, (30, 100, 3), (150, 220, 255), "Glass", transp=0.3)
            ob(b, "WaterfallGlow", add(q, mul(f, 12)), f, (24, 90, 0.4), (200, 245, 255), "Neon", transp=0.5)
        p0, p1, f2, L, w, _ = span(r)
        cyl(b, "Pool", sub(R2.lerp3(p0, p1, 0.3), (0, 6, 0)), 1, 260, F_WATER, "Glass", b.scenery, transp=0.4)
    # ---- the fairy ring: a circle of glowing mushrooms round the last glade
    with look(sk, surface=MOSS):
        run(r, "Fairy Glade", 260, w=130, cp=True)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        for k in range(10):
            a = TAU * k / 10
            q = add(c, (math.cos(a) * 150, 0, math.sin(a) * 150))
            if abs(dot(sub(q, c), right_of(f))) > w / 2 + 20:
                M.giant_mushroom(b, sub(q, (0, 4, 0)), 30 + (k % 3) * 10, 40, [(220, 50, 50), (150, 80, 220)][k % 2], rng)
        for k in range(16):
            firefly(b, add(c, ((hashf(c, k) - 0.5) * 300, 20 + hashf(c, k + 4) * 60, (hashf(c, k + 9) - 0.5) * 300)))
    end_on_line(r, "Forest Run", margin=500)
    r.log("end")
    return ["Mossy Log", "Toadstool Bounce", "Branch Spiral", "Falling Leaves", "Rocking Leaf", "Flower Launch",
            "Lily Pads", "Waterfall Drop", "Fairy Glade"]


# ===================================================================== 6. CONSTRUCTION CHAOS
K_SAFE, K_ORANGE, K_CONC, K_STEEL = (255, 200, 0), (255, 120, 20), (168, 166, 160), (70, 96, 130)


class Construction(Giant):
    key, title, theme_name = "construction", "Construction Chaos", "Construction site"
    clock, bloom, hue = 14.5, 0.35, 0.1
    body, top, edge, padc, danger = K_STEEL, K_CONC, K_SAFE, K_SAFE, (255, 60, 40)
    gate_post, gate_board, gate_text = (60, 60, 64), K_SAFE, BLACK
    light_over = {"Lt_Atmosphere_Density": 0.26, "Lt_Atmosphere_Haze": 1.4}


def hazard_edges(sk, b, parent, fr, w, L):
    for k in (-1, 1):
        e = Pt(b, "HazardEdge", F(fr, off(fr, x=k * (w / 2 - 2), y=0.06)), (4, 0.12, L), (30, 30, 30), "SmoothPlastic", parent)
        import showcase as SC
        SC.tex(b, e, "checker", tile=3.0, color=K_SAFE)


CONCRETE = slab(K_CONC, "Concrete", th=8, side=(140, 138, 132), deco=hazard_edges)
PLATE = slab((150, 156, 164), "DiamondPlate", th=4, deco=hazard_edges)
GIRDER = slab((210, 80, 40), "Metal", th=4, deco=edges((240, 120, 70), width=2.0, name="GirderEdge"))
PLANKS = slab((200, 160, 100), "WoodPlanks", th=4, deco=lines_across((150, 110, 60), 14, name="PlankGap"))


def cone(b, p):
    M.wcone(b, "TrafficCone", p, 16, 6, K_ORANGE, n=6)
    cyl(b, "ConeBand", add(p, (0, 8, 0)), 2, 7.4, WHITE, "SmoothPlastic", b.scenery)
    ob(b, "ConeBase", add(p, (0, 0.5, 0)), (1, 0, 0), (12, 1, 12), BLACK)


def girder_body(b, r, h=14.0):
    p0, p1, f, L, w, _ = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    ob(b, "GirderWeb", sub(c, (0, 4 + h / 2, 0)), f, (4, h, L), (190, 70, 36), "Metal")
    ob(b, "GirderFlange", sub(c, (0, 6 + h, 0)), f, (w, 3, L), (190, 70, 36), "Metal")
    for k in range(int(L // 30)):
        q = add(sub(c, (0, 4 + h / 2, 0)), mul(f, -L / 2 + 15 + k * 30))
        for sd in (-1, 1):
            cyl(b, "Rivet", add(q, mul(right_of(f), sd * 2.4)), 1.0, 2.4, (120, 50, 26), "Metal", b.scenery, axis=right_of(f))


def container_obj(b, r, col):
    p0, p1, f, L, w, _ = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    H = 70.0
    Pt(b, "Platform", CF(sub(c, (0, H / 2, 0)), *axes(f)), (w + 4, H, L + 4), col, "CorrodedMetal", b.roads, collide=True)
    rt = right_of(f)
    n = int(L // 8)
    for sd in (-1, 1):
        for k in range(n):
            q = add(c, add(mul(f, -L / 2 + (k + 0.5) * L / n), add(mul(rt, sd * (w / 2 + 2.3)), (0, -H / 2, 0))))
            ob(b, "Corrugation", q, f, (0.8, H - 6, 3), mix(col, BLACK, 0.2))
    for a in (-1, 1):
        ob(b, "ContainerDoor", add(c, add(mul(f, a * (L / 2 + 2.3)), (0, -H / 2, 0))), f, (w - 4, H - 6, 0.6), mix(col, BLACK, 0.15))
    for a in (-1, 1):
        for sd in (-1, 1):
            ob(b, "CornerCasting", add(c, add(mul(f, a * (L / 2 - 1)), add(mul(rt, sd * (w / 2 - 1)), (0, -1.5, 0)))), f,
               (6, 3.2, 6), (60, 60, 60))


def excavator_tower(b, hub):
    ob(b, "ExcavatorCab", add(hub, (0, -2, 0)), (1, 0, 0), (34, 30, 34), K_SAFE, collide=True)
    ob(b, "ExcavatorWindow", add(hub, (0, 4, 17.3)), (1, 0, 0), (24, 14, 0.4), (60, 80, 100), "Glass")
    ob(b, "ExcavatorTracks", add(hub, (0, -20, 0)), (1, 0, 0), (50, 10, 40), (40, 40, 40))


def excavator_arm(b, rig, hub, L):
    Pt(b, "Boom", CF(add(hub, (L * 0.45, 14, 0))), (L * 0.9, 8, 8), K_SAFE, "SmoothPlastic", rig)
    Pt(b, "Bucket", CF(add(hub, (L * 0.92, 6, 0))), (16, 16, 22), (90, 90, 96), "Metal", rig)
    for k in range(4):
        Pt(b, "BucketTooth", CF(add(hub, (L * 0.92 + 8, -2, -9 + k * 6))), (3, 6, 3), (60, 60, 64), "Metal", rig)


def scaffold(b, r, H=90.0):
    """Scaffolding round the stretch just laid: poles, cross braces, toe boards."""
    p0, p1, f, L, w, _ = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    rt = right_of(f)
    for a in range(int(L // 60) + 1):
        for sd in (-1, 1):
            q = add(R2.lerp3(p0, p1, a / max(int(L // 60), 1)), mul(rt, sd * (w / 2 + 4)))
            cyl(b, "ScaffoldPole", sub(q, (0, H / 2 - 30, 0)), H + 60, 3, (170, 176, 186), "Metal", b.scenery)
            ball(b, "Clamp", add(q, (0, 30, 0)), 4, K_SAFE, "SmoothPlastic", b.scenery)
    for sd in (-1, 1):
        ob(b, "GuardRail", add(c, add(mul(rt, sd * (w / 2 + 4)), (0, 22, 0))), f, (2, 2, L), (170, 176, 186), "Metal")
        ob(b, "ToeBoard", add(c, add(mul(rt, sd * (w / 2 + 4)), (0, 3, 0))), f, (1, 6, L), K_SAFE)
        for k in range(int(L // 60)):
            q0 = add(R2.lerp3(p0, p1, k / max(int(L // 60), 1)), add(mul(rt, sd * (w / 2 + 4.5)), (0, -H + 10, 0)))
            q1 = add(R2.lerp3(p0, p1, (k + 1) / max(int(L // 60), 1)), add(mul(rt, sd * (w / 2 + 4.5)), (0, -8, 0)))
            cyl(b, "Brace", R2.lerp3(q0, q1, 0.5), math.dist(q0, q1), 2, (170, 176, 186), "Metal", b.scenery,
                axis=unit(sub(q1, q0)))


def pipe(b, p0, f, L, R, col=(150, 148, 142), step=28.0):
    """A giant concrete pipe lying round the road: hollow ring sections, banded."""
    d = step / 2
    k = 0
    while d < L:
        c = add(p0, add(mul(f, d), (0, R - 12, 0)))
        ringz(b, c, R, col if k % 4 else mix(col, BLACK, 0.15), "Concrete", th=step + 0.2, axis=f, name="ConcretePipe")
        d += step
        k += 1


def slot36(r, sk, rng):
    b = r.b
    stage(r, sk, "Construction Chaos", "OBBY 3 - LEVEL 6")
    # ---- the site entrance: a slab of fresh concrete, cones and barriers
    with look(sk, surface=CONCRETE):
        run(r, "Site Entrance", 240, w=130, boosts=2, every=60)
        p0, p1, f, L, w, _ = span(r)
        for k in range(6):
            sd = 1 if k % 2 else -1
            cone(b, add(R2.lerp3(p0, p1, 0.1 + 0.16 * k), mul(right_of(f), sd * (w / 2 - 6))))
        ob(b, "Foundation", sub(R2.lerp3(p0, p1, 0.5), (0, 30, 0)), f, (w + 20, 44, L), (140, 138, 132), "Concrete")
    # ---- the girder: a narrow steel beam over the drop
    with look(sk, surface=GIRDER):
        run(r, "Steel Girder", 260, w=44, cp=True)
        girder_body(b, r)
        coin_row(b, span(r)[0], span(r)[1], n=5)
    # ---- the crane: its magnet lifts the car onto the container stack
    with look(sk, surface=PLATE):
        run(r, "Crane Pad", 100, w=100)
        MX.crane_transfer(r, "Tower Crane", 420.0, dy=60.0, land_L=160.0, w_land=90, cp=True)
        container_obj(b, r, (200, 60, 40))
    # ---- the containers: hop along the stack
    o = O.Obby(r, 230)
    with look(sk, surface=PLATE):
        for k, (dy, side, col) in enumerate(((-20.0, 60.0, (40, 110, 180)), (0.0, -60.0, (60, 150, 70)),
                                              (-20.0, 50.0, (230, 160, 30)))):
            o.kick(dy=dy, side=side, label="Container Hop %d" % (k + 1))
            o.plat("Container %d" % (k + 1), 130, 80, cp=(k == 1))
            container_obj(b, r, col)
            coin_arc(b, -1, n=4)
    # ---- the swinging container: ride the crane hook's load over the gap
    with look(sk, surface=PLATE):
        o.kick(dy=0.0, label="Load Hop")
        o.plat("Hook Platform", 100, 90)
        R2.pendulum_ferry(r, "Swinging Load", Lp=200.0, amp_deg=26.0, period=5.0, deck=(90.0, 70.0), col=(230, 120, 30),
                          mat="CorrodedMetal")
        run(r, "Landing Plate", 140, w=100, cp=True)
    # ---- the demolition run: wrecking balls swing across the concrete
    with look(sk, surface=CONCRETE):
        r.turn("Site Bend", 90, 140)
        run(r, "Demolition Run", 420, w=120)
        r.along(MX.ball_lane, [90])
        r.along(MX.ball_pair, [210])
        r.along(MX.ball_high, [330])
    # ---- the concrete pipe: straight through it
    with look(sk, surface=CONCRETE):
        run(r, "Pipe Run", 260, w=60, cp=True)
        pipe(b, span(r)[0], span(r)[2], 260, 56)
    # ---- the cement mixer drum: drive along its turning top, jump its blades
    with look(sk, surface=PLATE):
        run(r, "Mixer Chute", 60, w=60)

        def mixer_art(b_, rig, c, f, L, R):
            for k in range(5):
                ringz(b_, add(c, mul(f, -L / 2 + L * (k + 0.5) / 5)), R + 0.6, (230, 120, 30), "SmoothPlastic", th=4,
                      axis=f, parent=rig, name="DrumBand")
            ob(b_, "MixerChassis", sub(c, (0, R + 26, 0)), f, (90, 30, L + 60), K_SAFE)
            for a in (-1, 1):
                for sd in (-1, 1):
                    cyl(b_, "MixerWheel", add(c, add(mul(f, a * (L / 2 + 10)), add(mul(right_of(f), sd * 46), (0, -R - 40, 0)))),
                        12, 34, BLACK, "SmoothPlastic", b_.scenery, axis=right_of(f))
        drum(r, "Cement Mixer", 240, 40, (210, 210, 206), "Concrete", speed=0.18, ridge_col=K_SAFE, art=mixer_art)
        run(r, "Mixer Exit", 100, w=80)
    # ---- the scaffold: pads up its decks
    o = O.Obby(r, 230)
    with look(sk, surface=PLANKS):
        for k in range(2):
            o.pad(60.0, label="Scaffold Lift %d" % (k + 1))
            o.plat("Scaffold Deck %d" % (k + 1), 150, 80, cp=(k == 1))
            scaffold(b, r)
        r.turn("Scaffold Walk", -90, 120)
    # ---- the excavator: its arm sweeps the top floor; then smash through the brick stacks
    with look(sk, surface=CONCRETE):
        o.kick(dy=-30.0, label="Floor Hop")
        o.plat("Top Floor", 380, 120, cp=True)
        r.along(lambda b_, c, w, i: sweeper(b_, c, w, i, excavator_arm, speed=0.22, tower_fn=excavator_tower), [90, 200])
        for k, pat in enumerate(("b.b",)):
            MX.lane_row(r, 320, 120, "bbb", kind="brick")
    # ---- the haul road: a gravel conveyor, then off the back of a dump truck
    with look(sk, surface=CONCRETE):
        r.turn("Haul Road", -90, 150)
    with look(sk, surface=slab((120, 116, 110), "Slate", th=4)):
        sk.edge = K_SAFE
        R2.belt_road(r, "Gravel Conveyor", 360, 70.0, direction="along", w=90, cp=True)
        p0, p1, f, L, w, _ = span(r)
        for k in range(8):
            q = add(R2.lerp3(p0, p1, (k + 0.5) / 8), mul(right_of(f), (w / 2 + 8) * (1 if k % 2 else -1)))
            cyl(b, "ConveyorRoller", sub(q, (0, 4, 0)), 12, 8, (90, 90, 96), "Metal", b.scenery, axis=right_of(f))
        ob(b, "ConveyorFrame", sub(R2.lerp3(p0, p1, 0.5), (0, 12, 0)), f, (w + 10, 14, L), K_SAFE)
    with look(sk, surface=by_name({"Ramp": slab((230, 160, 30), "Metal", th=4)}, CONCRETE)):
        run(r, "Truck Run", 120, w=80, boosts=2, every=40)
        R2.ramp_jump(r, "Dump Truck Ramp", deg=20, drop=70, w_land=120, slope=3, land_min=300, cp=True, rails=False)
        lip = b.jumps[-2][1]
        f = r.f
        for sd in (-1, 1):
            ob(b, "TruckBedSide", add(lip, add(mul(f, -30), add(mul(right_of(f), sd * 44), (0, -8, 0)))), f, (6, 26, 70),
               (210, 140, 20))
            for a in (-1, 1):
                cyl(b, "TruckWheel", add(lip, add(mul(f, -30 + a * 26), add(mul(right_of(f), sd * 40), (0, -50, 0)))), 14, 36,
                    BLACK, "SmoothPlastic", b.scenery, axis=right_of(f))
        coin_arc(b, -2, n=6)
        r.turn("Exit Bend", 90, 150)
    end_on_line(r, "Site Run", margin=500)
    r.log("end")
    return ["Site Entrance", "Steel Girder", "Tower Crane", "Container Stack", "Swinging Load", "Wrecking Balls",
            "Concrete Pipe", "Cement Mixer", "Scaffolding", "Excavator", "Brick Smash"]


# ===================================================================== 7. THE GIANT BEDROOM
B_DESK, B_CARPET, B_SHEET = (170, 120, 80), (70, 100, 160), (240, 240, 250)
B_LAMP = (255, 220, 140)


class Bedroom(Giant):
    key, title, theme_name = "bedroom", "The Giant Bedroom", "Giant bedroom"
    clock, bloom, hue = 19.2, 0.7, 0.08
    body, top, edge, padc, danger = (120, 80, 50), B_DESK, B_LAMP, (120, 200, 255), (255, 70, 70)
    gate_post, gate_board, gate_text = (120, 80, 50), (40, 50, 90), B_LAMP
    light_over = {"Lt_Lighting_Brightness": 2.0, "Lt_Atmosphere_Density": 0.24, "Lt_Atmosphere_Haze": 1.2,
                  "Lt_Bloom_Intensity": 0.7}


DESK = slab(B_DESK, "Wood", th=8, side=(130, 88, 56), deco=lines_along((150, 104, 68), 22, width=0.8, name="Grain"))
QUILT = slab(B_SHEET, "Fabric", th=6, side=(200, 210, 230),
             deco=both(lines_along((170, 190, 230), 30, width=1.2, name="Stitch"), lines_across((170, 190, 230), 30, width=1.2,
                                                                                               name="Stitch")))
RUG = slab(B_CARPET, "Fabric", th=3, deco=both(edges((230, 200, 90), width=6.0, name="RugBorder"),
                                               edges((240, 240, 250), width=2.0, name="RugBorder")))
SHELF = slab((196, 150, 104), "WoodPlanks", th=6, side=(150, 104, 66))


def book_obj(b, r, col, h=30.0, title_col=GOLD):
    """A giant book lying flat: its cover is the stretch, pages showing on three sides."""
    p0, p1, f, L, w, _ = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    rt = right_of(f)
    Pt(b, "Platform", CF(sub(c, (0, 2, 0)), *axes(f)), (w + 6, 4, L + 6), col, "SmoothPlastic", b.roads, collide=True)
    ob(b, "Pages", sub(c, (0, 4 + h / 2, 0)), f, (w + 2, h, L + 2), (250, 246, 230))
    for k in range(int(h // 3)):
        ob(b, "PageLine", add(sub(c, (0, 5 + k * 3, 0)), mul(rt, w / 2 + 1.05)), f, (0.2, 0.3, L), (220, 214, 196))
    ob(b, "BackCover", sub(c, (0, 6 + h, 0)), f, (w + 6, 4, L + 6), col)
    ob(b, "Spine", add(sub(c, (0, h / 2 + 4, 0)), mul(rt, -(w / 2 + 4))), f, (4, h + 8, L + 6), mix(col, BLACK, 0.2))
    ob(b, "BookTitle", add(c, (0, 0.06, 0)), f, (w * 0.5, 0.12, 8), title_col)
    ob(b, "BookTitle", add(c, add(mul(f, 14), (0, 0.06, 0))), f, (w * 0.3, 0.12, 4), title_col)


def pillow_cap(cols):
    k = [0]

    def cap(b, top, s, rng):
        col = cols[k[0] % len(cols)]
        k[0] += 1
        Pt(b, "Platform", CF(sub(top, (0, 1.5, 0))), (s * 0.95, 3, s * 0.7), col, "Fabric", b.roads, collide=True)
        M.ell(b, "Pillow", sub(top, (0, 10, 0)), (s * 1.05, 24, s * 0.8), col, "Fabric", parent=b.scenery)
        ob(b, "PillowSeam", add(top, (0, 0.05, 0)), (1, 0, 0), (s * 0.95, 0.1, 1.2), mix(col, BLACK, 0.12))
    return cap


def pillow_pad(sk, b, start, f):
    M.ell(b, "LaunchPillow", sub(start, (0, 8, 0)), (60, 18, 44), (250, 220, 230), "Fabric", parent=b.scenery)
    fr = deck_frame(add(start, (0, 0.1, 0)), f)
    for k in range(3):
        q = add(start, mul(f, -8 + k * 8))
        Pt(b, "PadChevron", CF(add(q, (0, 0.3, 0)), fr.x, fr.y, fr.z), (14, 0.2, 3), (120, 200, 255), "Neon")


def lamp_art(b, lip, f):
    """A desk lamp whose shade is the kicker: its base on the desk, the bulb glowing inside."""
    base = add(lip, add(mul(f, -40), (0, -70, 0)))
    cyl(b, "LampBase", base, 6, 60, (60, 60, 70), "Metal", b.scenery)
    cyl(b, "LampArm", R2.lerp3(base, sub(lip, (0, 14, 0)), 0.5), math.dist(base, lip), 5, (200, 200, 210), "Metal", b.scenery,
        axis=unit(sub(lip, base)))
    ball(b, "LampBulb", add(lip, add(mul(f, -20), (0, -16, 0))), 16, B_LAMP, "Neon", b.scenery)


def hanger_swing(b, c, w, i, period=2.8):
    """A coat on a hanger swinging across the wardrobe (knocks you off)."""
    x, y, z = c
    piv = (x, y + 70, z)
    root = b.prop_root("Hanger")
    rig = b.rig(root, "Hinge", axis_frame(piv, (1, 0, 0)), 40.0, period, phase=(i * 0.33) % 1, keys="0:0 0.25:1 0.5:0 0.75:-1",
                name="Swing")
    cyl(b, "HangerHook", add(piv, (0, -4, 0)), 8, 1.4, (200, 200, 210), "Metal", rig)
    Pt(b, "Hanger", CF(add(piv, (0, -10, 0))), (2, 3, 30), (200, 200, 210), "Metal", rig)
    Pt(b, "Coat", CF(add(piv, (0, -36, 0))), (10, 46, 34), [(200, 60, 60), (60, 120, 200), (90, 160, 90)][i % 3], "Fabric",
       rig, query=True, attrs={"ObbyHazard": "Knock"})


def toy_car_slider(b, c, w, i, period=3.0):
    x, y, z = c
    z0 = (x, y, z - w / 2 + 20)
    root = b.prop_root("ToyCar")
    rig = b.rig(root, "Slide", axis_frame(z0, (0, 0, 1)), w - 40, period + 0.4 * i, phase=(i * 0.41) % 1,
                keys="0:0 0.5:1 1:0", name="Drive")
    col = [T_RED, T_BLUE, T_YEL][i % 3]
    Pt(b, "ToyCar", CF(add(z0, (0, 9, 0))), (40, 14, 26), col, "SmoothPlastic", rig, query=True, attrs={"ObbyHazard": "Knock"})
    Pt(b, "ToyCarCab", CF(add(z0, (-2, 19, 0))), (20, 8, 22), mix(col, WHITE, 0.4), "SmoothPlastic", rig, query=True,
       attrs={"ObbyHazard": "Knock"})
    for a in (-1, 1):
        for sd in (-1, 1):
            cyl(b, "ToyWheel", add(z0, (a * 13, 4, sd * 13)), 4, 9, BLACK, "SmoothPlastic", rig, axis=(0, 0, 1))


def slot37(r, sk, rng):
    b = r.b
    stage(r, sk, "The Giant Bedroom", "OBBY 3 - LEVEL 7")
    # ---- the desk: pencils, a mug of pens, a notebook
    with look(sk, surface=DESK):
        run(r, "Desk Top", 260, w=140, boosts=2, every=60)
        p0, p1, f, L, w, _ = span(r)
        legs(b, R2.lerp3(p0, p1, 0.5), f, w, L, 300, (130, 88, 56), "Wood", d=14, name="DeskLeg")
        for k in range(3):
            q = add(R2.lerp3(p0, p1, 0.2 + 0.3 * k), mul(right_of(f), (w / 2 - 12) * (1 if k % 2 else -1)))
            cyl(b, "Pencil", add(q, (0, 3, 0)), 80, 6, [K_YEL, T_RED, T_BLUE][k], "SmoothPlastic", b.scenery, axis=f)
        cyl(b, "PenCup", add(R2.lerp3(p0, p1, 0.6), add(mul(right_of(f), w / 2 + 20), (0, 25, 0))), 50, 30, T_BLUE,
            "SmoothPlastic", b.scenery)
    # ---- the book stairs: up a stack of giant books
    o = O.Obby(r, 180)
    with look(sk, surface=ghost):
        for k, col in enumerate(((180, 40, 50), (40, 90, 170), (40, 140, 90))):
            o.pad(36.0, side=(0, 40, -40)[k], label="Book Step %d" % (k + 1))
            o.plat("Book %d" % (k + 1), 120, 90, cp=(k == 0))
            book_obj(b, r, col)
            coin_arc(b, -1, n=3)
    # ---- the keyboard: its keys sink as you drive over them
    with look(sk, surface=slab((60, 62, 70), "SmoothPlastic", th=6)):
        o.kick(dy=-30.0, label="Keyboard Hop")
        o.plat("Keyboard Frame", 60, 130)
    R2.sink_board(r, "Keyboard Keys", 320, 120, cell=40, cols=((230, 232, 238), (200, 204, 212)),
                  mats=("SmoothPlastic", "SmoothPlastic"), delay=0.3, rate=80.0, cp=True)
    with look(sk, surface=slab((60, 62, 70), "SmoothPlastic", th=6)):
        run(r, "Spacebar", 120, w=110)
    with look(sk, surface=DESK):
        r.turn("Desk Corner", 90, 140)
    # ---- the desk lamp: its shade is the ramp that flies you onto the bed
    with look(sk, surface=by_name({"Ramp": slab(B_LAMP, "SmoothPlastic", th=3)}, QUILT)):
        r.w = 80
        R2.ramp_jump(r, "Lamp Ramp", deg=22, drop=80, w_land=150, slope=3, land_min=300, cp=True, rails=False)
        lamp_art(b, b.jumps[-2][1], r.f)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        c = (c[0], min(p0[1], p1[1]), c[2])
        ob(b, "Mattress", sub(c, (0, 24, 0)), f, (w + 30, 36, L + 40), (220, 226, 240), "Fabric")
        ob(b, "BedFrame", sub(c, (0, 52, 0)), f, (w + 50, 24, L + 60), (140, 96, 60), "Wood")
        ob(b, "Headboard", add(c, add(mul(right_of(f), -(w / 2 + 34)), (0, 30, 0))), f, (8, 120, L + 60), (140, 96, 60), "Wood")
    # ---- the pillows: bounce across them
    with look(sk, surface=QUILT):
        R2.bounce_chain(r, "Pillow Bounce", [(240.0, 0.0, 60.0), (240.0, 10.0, -60.0), (240.0, 0.0, 40.0)], 230.0, s=96.0,
                        cap=pillow_cap(((250, 220, 230), (220, 230, 255), (240, 240, 250))), land_L=160.0, cp=True,
                        shroom=False)
        ob(b, "Duvet", sub(R2.lerp3(span(r)[0], span(r)[1], 0.5), (0, 20, 0)), span(r)[2], (span(r)[4] + 30, 34, span(r)[3] + 20),
           (200, 214, 240), "Fabric")
    # ---- the pillow launch up into the wardrobe
    o = O.Obby(r, 230)
    with look(sk, surface=QUILT, pad=pillow_pad):
        o.plat("Bed End", 100, 110)
        o.pad(80.0, label="Pillow Launch")
    # ---- the wardrobe: shelf to shelf past the swinging coats
    w0 = None
    with look(sk, surface=SHELF):
        o.plat("Wardrobe Shelf", 260, 100, cp=True)
        w0 = span(r)[0]
        r.along(hanger_swing, [90, 170])
        o.drop(50.0, label="Shelf Drop")
        o.plat("Lower Shelf", 200, 100)
        w1 = r.p
        f = r.f
        rt = right_of(f)
        c = R2.lerp3(w0, w1, 0.5)
        Lw = math.hypot(w1[0] - w0[0], w1[2] - w0[2]) + 60
        for sd in (-1, 1):
            ob(b, "WardrobeSide", add(c, add(mul(rt, sd * 64), (0, 20, 0))), f, (8, 220, Lw), (150, 100, 60), "WoodPlanks")
            ob(b, "WardrobeDoor", add(c, add(mul(rt, sd * 110), (0, 20, 0))), rt, (8, 220, 90), (170, 116, 72), "WoodPlanks")
            ob(b, "DoorKnob", add(c, add(mul(rt, sd * 110), add(mul(f, 0), (0, 20, 0)))), rt, (12, 6, 6), GOLD, "Metal")
        ob(b, "WardrobeTop", add(c, (0, 132, 0)), f, (140, 8, Lw), (150, 100, 60), "WoodPlanks")
        ob(b, "HangerRail", add(w0, add(mul(f, 130), (0, 82, 0))), f, (3, 3, 260), (200, 200, 210), "Metal")
        run(r, "Wardrobe Floor", 60, w=100)
        r.turn("Wardrobe Turn", -90, 120)
    # ---- the chair: hop onto the cushion, then down to the rug
    with look(sk, surface=slab((90, 140, 200), "Fabric", th=6)):
        o.kick(dy=-20.0, side=60.0, label="Chair Hop")
        o.plat("Chair Seat", 120, 110, cp=True)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        legs(b, c, f, w, L, 160, (140, 96, 60), "Wood", d=10, name="ChairLeg")
        ob(b, "ChairBack", add(c, add(mul(right_of(f), -(w / 2 + 6)), (0, 60, 0))), f, (10, 120, L), (140, 96, 60), "Wood")
        o.drop(60.0, label="Rug Drop")
    # ---- the rug: toy cars race across it
    with look(sk, surface=RUG):
        o.plat("Bedroom Rug", 400, 140, cp=True, boost=False)
        r.along(toy_car_slider, [100, 200, 300])
        p0, p1, f, L, w, _ = span(r)
        for k in range(4):
            q = add(R2.lerp3(p0, p1, 0.15 + 0.25 * k), mul(right_of(f), (w / 2 + 40) * (1 if k % 2 else -1)))
            M.toy_block(b, q, 30, [T_RED, T_BLUE, T_YEL, T_GRN][k])
        r.turn("Rug Corner", -90, 150)
    # ---- the skateboard: off its kicked-up tail onto a stack of comic books
    with look(sk, surface=by_name({"Ramp": slab((60, 200, 120), "SmoothPlastic", th=3)}, slab((240, 220, 80), "SmoothPlastic", th=4,
                                                                                         deco=edges(T_RED, width=4.0, name="ComicEdge")))):
        run(r, "Skate Run", 140, w=80, boosts=2, every=40)
        R2.ramp_jump(r, "Skateboard Ramp", deg=20, drop=50, w_land=120, slope=3, land_min=280, cp=True, rails=False)
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
        r.turn("Comic Bend", 90, 150)
    end_on_line(r, "Bedroom Run", margin=500)
    r.log("end")
    return ["Desk Top", "Book Stairs", "Keyboard", "Lamp Ramp", "Pillow Bounce", "Pillow Launch", "Wardrobe",
            "Chair", "Toy Cars"]



# ===================================================================== 8. THE SPACE STATION
S_HULL, S_PANEL, S_DARK = (226, 230, 238), (120, 130, 146), (40, 44, 56)
S_CYAN, S_ORANGE, S_SOLAR = (0, 220, 255), (255, 140, 30), (30, 56, 140)


class Space(Giant):
    key, title, theme_name = "space", "The Space Station", "Space station"
    clock, bloom, hue = 0.0, 1.0, 0.6
    body, top, edge, padc, danger = S_DARK, S_HULL, S_CYAN, S_CYAN, (255, 60, 60)
    gate_post, gate_board, gate_text = S_PANEL, S_DARK, S_CYAN
    light_over = {"Lt_Atmosphere_Density": 0.0, "Lt_Atmosphere_Haze": 0.0, "Lt_Lighting_Brightness": 2.2,
                  "Lt_Bloom_Intensity": 1.0, "Lt_Bloom_Threshold": 1.0}


HULL = slab(S_HULL, "SmoothPlastic", th=6, side=S_PANEL,
            deco=both(lines_across((180, 186, 198), 24, name="PanelSeam"), edges(S_CYAN, "Neon", width=1.2, name="NeonEdge")))
GRATE = slab((70, 76, 90), "DiamondPlate", th=4, deco=edges(S_ORANGE, "Neon", width=1.2, name="NeonEdge"))
ROCK = slab((120, 112, 104), "Slate", th=6)


def solar_art(b, m, c, f, L, w):
    rt = right_of(f)
    for i in range(int(L // 16)):
        for j in range(int(w // 16)):
            q = add(c, add(mul(f, -L / 2 + 8 + i * 16), add(mul(rt, -w / 2 + 8 + j * 16), (0, 0.06, 0))))
            Pt(b, "SolarCell", CF(q, *axes(f)), (14.6, 0.12, 14.6), (40, 70, 170), "Glass", m, refl=0.3)
    Pt(b, "SolarSpine", CF(add(c, (0, -5, 0)), *axes(f)), (6, 6, L), (200, 204, 214), "Metal", m)


def asteroid_obj(b, r, rng):
    c, R = disc_obj(b, r, (120, 112, 104), th=4.0, grow=1.0)
    M.asteroid(b, sub(c, (0, R * 0.75, 0)), R * 1.6, rng)
    for k in range(4):
        a = TAU * k / 4 + 0.5
        cyl(b, "Crystal", add(c, (math.cos(a) * R * 0.95, 4, math.sin(a) * R * 0.95)), 14, 5, (140, 90, 255), "Neon", b.scenery)


def engine_pad(sk, b, start, f):
    """A rocket engine pointing up under the launch: a bell nozzle with a blue flame ring."""
    cyl(b, "EngineBell", sub(start, (0, 18, 0)), 30, 46, (90, 96, 110), "Metal", b.scenery, refl=0.3)
    cyl(b, "EngineThroat", sub(start, (0, 40, 0)), 16, 26, (60, 64, 76), "Metal", b.scenery)
    ringz(b, add(start, (0, 0.15, 0)), 18, (90, 200, 255), "Neon", th=0.3, name="EngineFlame")
    ringz(b, add(start, (0, 0.15, 0)), 10, (255, 255, 255), "Neon", th=0.3, name="EngineFlame")
    fr = deck_frame(add(start, (0, 0.1, 0)), f)
    for k in range(3):
        q = add(start, mul(f, -8 + k * 8))
        Pt(b, "PadChevron", CF(add(q, (0, 0.3, 0)), fr.x, fr.y, fr.z), (14, 0.2, 3), S_CYAN, "Neon")


def robot_arm(b, rig, hub, L):
    Pt(b, "ArmUpper", CF(add(hub, (L * 0.25, 10, 0))), (L * 0.5, 7, 7), (230, 234, 240), "SmoothPlastic", rig)
    ball(b, "ArmElbow", add(hub, (L * 0.5, 10, 0)), 11, S_ORANGE, "SmoothPlastic", rig)
    Pt(b, "ArmLower", CF(add(hub, (L * 0.75, 8, 0))), (L * 0.5, 6, 6), (230, 234, 240), "SmoothPlastic", rig)
    Pt(b, "ArmGripper", CF(add(hub, (L + 2, 6, 0))), (8, 10, 14), S_DARK, "Metal", rig)
    ball(b, "ArmLight", add(hub, (L * 0.5, 17, 0)), 3, (255, 60, 60), "Neon", rig)


def arm_base(b, hub):
    cyl(b, "ArmBase", add(hub, (0, -2, 0)), 20, 20, S_PANEL, "Metal", b.scenery, collide=True)
    ringz(b, add(hub, (0, -1, 0)), 11, S_CYAN, "Neon", th=0.6, name="BaseGlow")


def energy_ring(b, c, f, R, col=S_CYAN):
    ringz(b, c, R, (200, 204, 214), "Metal", th=6, axis=f, name="EnergyRing")
    ringz(b, c, R - 3, col, "Neon", th=3, axis=f, name="EnergyGlow")


def dish(b, C, R, y, f):
    """A giant satellite dish lying open-side up beside the curve, its feed horn on struts."""
    n = 14
    for k in range(n):
        a = TAU * k / n
        d = (math.cos(a), 0, math.sin(a))
        q = add(C, add(mul(d, R * 0.62), (0, y - C[1] - 14, 0)))
        Pt(b, "DishPanel", CF(q, *axes(d)) * rot_axis((1, 0, 0), -0.45), (R * 0.46, 3, R * 0.7), (230, 234, 240), "SmoothPlastic",
           b.scenery)
    cyl(b, "DishHub", (C[0], y - 40, C[2]), 20, 40, S_PANEL, "Metal", b.scenery)
    cyl(b, "DishMast", (C[0], y - 160, C[2]), 220, 18, S_PANEL, "Metal", b.scenery)


def slot38(r, sk, rng):
    b = r.b
    stage(r, sk, "The Space Station", "OBBY 3 - LEVEL 8")
    # ---- the docking bay: white hull plates, landing lights
    with look(sk, surface=HULL):
        run(r, "Docking Bay", 260, w=140, boosts=2, every=60)
        p0, p1, f, L, w, _ = span(r)
        for k in range(8):
            for sd in (-1, 1):
                ball(b, "LandingLight", add(R2.lerp3(p0, p1, (k + 0.5) / 8), add(mul(right_of(f), sd * (w / 2 - 4)), (0, 0.5, 0))),
                     3, [S_CYAN, S_ORANGE][k % 2], "Neon", b.scenery)
        ob(b, "StationModule", sub(R2.lerp3(p0, p1, 0.5), (0, 40, 0)), f, (w + 30, 70, L), S_PANEL, "Metal")
        for k in range(4):
            cyl(b, "ModuleRing", add(sub(R2.lerp3(p0, p1, 0.5), (0, 40, 0)), mul(f, -L / 2 + 30 + k * (L - 60) / 3)), 8, w + 40,
                (230, 234, 240), "SmoothPlastic", b.scenery, axis=f)
    # ---- the solar array: its panels roll side to side as the station turns
    with look(sk, surface=GRATE):
        run(r, "Array Gantry", 80, w=70)
        swing_bridge(r, "Solar Panel", 240, 80, S_SOLAR, "Glass", amp_deg=8.0, period=4.4, art=solar_art)
        run(r, "Array Joint", 40, w=70)
        swing_bridge(r, "Solar Panel 2", 240, 80, S_SOLAR, "Glass", amp_deg=8.0, period=4.4, phase=0.5, art=solar_art)
        run(r, "Array End", 80, w=80, cp=True)
    # ---- the asteroids: hop across the floating rocks
    o = O.Obby(r, 230)
    with look(sk, surface=ghost):
        for k, (dy, side) in enumerate(((-20.0, 70.0), (-10.0, -70.0), (0.0, 60.0))):
            o.kick(dy=dy, side=side, label="Asteroid Hop %d" % (k + 1))
            o.plat("Asteroid %d" % (k + 1), 100, 90, cp=(k == 1))
            asteroid_obj(b, r, rng)
            coin_arc(b, -1, n=4)
    # ---- the engine: it fires you up to the upper ring
    with look(sk, surface=HULL, pad=engine_pad):
        o.kick(dy=0.0, label="Engine Hop")
        o.plat("Engine Deck", 110, 100)
        o.pad(110.0, label="Engine Launch")
        o.plat("Upper Ring", 200, 110, cp=True)
        p0, p1, f, L, w, _ = span(r)
        r.turn("Ring Curve", 90, 150)
    # ---- through the energy rings: a ramp launch
    with look(sk, surface=HULL):
        run(r, "Ring Run", 140, w=100, boosts=3, every=35)
        R2.ramp_jump(r, "Energy Jump", deg=20, drop=70, w_land=130, slope=3, land_min=300, cp=True, rails=False)
        kind, lip, tgt, H, V = b.jumps[-2]
        fj = RT.flat(sub(tgt, lip))
        dyj = tgt[1] - lip[1]
        T = (V + math.sqrt(max(V * V + 2 * G * dyj, 0.0))) / G
        for k, t in enumerate((0.3, 0.55, 0.8)):
            tt = T * t
            q = add(lip, add(mul(fj, H * tt), (0, V * tt - G * tt * tt / 2 + CAR_UP, 0)))
            energy_ring(b, q, fj, 40 - k * 4, [S_CYAN, (180, 90, 255), S_ORANGE][k])
        coin_arc(b, -2, n=6)
    # ---- the robot arms sweep the maintenance deck
    with look(sk, surface=GRATE):
        run(r, "Maintenance Deck", 380, w=120, cp=True)
        r.along(lambda b_, c, w, i: sweeper(b_, c, w, i, robot_arm, speed=0.24, tower_fn=arm_base), [90, 200, 310])
        r.turn("Dish Curve", -90, 170, cp=True)
        dish(b, r.centre, 150, r.p[1], r.f)
    # ---- the tractor beam: a UFO carries you across the void
    with look(sk, surface=HULL):
        run(r, "Beam Pad", 100, w=90)
        R2.tractor_beam(r, "Tractor Beam", 420.0, dy=-30.0, turn=-50.0, land_L=160.0, w_land=110, cp=True)
    # ---- the spaceship wing: along the wing, off its tip to the command deck
    with look(sk, surface=by_name({"Ramp": HULL}, HULL)):
        run(r, "Ship Wing", 260, w=120)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        rt = right_of(f)
        ob(b, "ShipHull", add(c, add(mul(rt, -(w / 2 + 50)), (0, 10, 0))), f, (100, 60, L + 120), (210, 214, 224), "SmoothPlastic")
        ob(b, "ShipCockpit", add(c, add(mul(rt, -(w / 2 + 50)), add(mul(f, L / 2 + 40), (0, 40, 0)))), f, (70, 30, 50),
           (90, 200, 255), "Glass", transp=0.2)
        for k in range(3):
            cyl(b, "ShipThruster", add(c, add(mul(rt, -(w / 2 + 30 + k * 20)), add(mul(f, -L / 2 - 70), (0, 6, 0)))), 30, 18,
                S_PANEL, "Metal", b.scenery, axis=f)
            ringz(b, add(c, add(mul(rt, -(w / 2 + 30 + k * 20)), add(mul(f, -L / 2 - 86), (0, 6, 0)))), 7, S_CYAN, "Neon", th=2,
                  axis=f, name="ThrusterGlow")
        R2.ramp_jump(r, "Wingtip Launch", deg=18, drop=50, w_land=140, slope=3, land_min=280, cp=True, rails=False)
        p0, p1, f, L, w, _ = span(r)
        ob(b, "CommandDeck", sub(R2.lerp3(p0, p1, 0.5), (0, 50, 0)), f, (w + 40, 80, L), S_PANEL, "Metal")
        r.turn("Command Curve", 50, 220)
    end_on_line(r, "Station Run", margin=500)
    r.log("end")
    return ["Docking Bay", "Solar Array", "Asteroid Hops", "Engine Launch", "Energy Rings", "Robot Arms", "Satellite Dish",
            "Tractor Beam", "Wingtip Launch"]


# ===================================================================== 9. THE PIRATE SHIP
P_DECK, P_DARK, P_SAIL, P_ROPE = (156, 106, 64), (92, 60, 36), (240, 230, 204), (196, 170, 120)
P_SEA = (24, 50, 70)


class Pirate(Giant):
    key, title, theme_name = "pirate", "The Pirate Ship", "Pirate ship"
    clock, bloom, hue = 17.6, 0.45, 0.58
    body, top, edge, padc, danger = P_DARK, P_DECK, GOLD, GOLD, (255, 60, 40)
    gate_post, gate_board, gate_text = P_DARK, BLACK, GOLD
    light_over = {"Lt_Atmosphere_Density": 0.45, "Lt_Atmosphere_Haze": 2.2, "Lt_Lighting_Brightness": 1.7,
                  "Lt_Atmosphere_Color": ("Color3", 0.55, 0.6, 0.66), "Lt_CC_Saturation": -0.05, "Lt_CC_Contrast": 0.22}


DECK = slab(P_DECK, "WoodPlanks", th=6, side=P_DARK, deco=lines_along((120, 80, 46), 10, width=0.6, name="PlankSeam"))
DARK_DECK = slab((126, 86, 52), "WoodPlanks", th=6, side=P_DARK, deco=lines_along((90, 60, 36), 10, width=0.6, name="PlankSeam"))
SPAR = slab((150, 104, 60), "Wood", th=4, deco=edges(P_ROPE, width=2.0, name="RopeWrap"))


def hull(b, r, depth=70.0, flare=12.0, gun_ports=True, rails=True):
    """A ship's hull under the deck stretch just laid: dark planked sides, a gold stripe, gun ports, a railing."""
    p0, p1, f, L, w, _ = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    rt = right_of(f)
    ob(b, "Hull", sub(c, (0, depth / 2 + 6, 0)), f, (w + flare, depth, L), P_DARK, "WoodPlanks")
    for sd in (-1, 1):
        ob(b, "HullStripe", add(c, add(mul(rt, sd * ((w + flare) / 2 + 0.3)), (0, -16, 0))), f, (0.6, 4, L), GOLD)
        if gun_ports:
            for k in range(int(L // 50)):
                q = add(c, add(mul(f, -L / 2 + 25 + k * 50), add(mul(rt, sd * ((w + flare) / 2 + 0.4)), (0, -30, 0))))
                ob(b, "GunPort", q, f, (0.6, 10, 12), BLACK)
                cyl(b, "PortCannon", add(q, mul(rt, sd * 4)), 10, 5, (40, 40, 44), "Metal", b.scenery, axis=rt)
        if rails:
            ob(b, "ShipRail", add(c, add(mul(rt, sd * (w / 2 + 3)), (0, 7, 0))), f, (3, 3, L), P_DARK, collide=True)
            for k in range(int(L // 16) + 1):
                q = add(c, add(mul(f, -L / 2 + k * L / max(int(L // 16), 1)), add(mul(rt, sd * (w / 2 + 3)), (0, 3, 0))))
                ob(b, "Baluster", q, f, (2, 7, 2), P_DARK)


def sea(b, c, sx, sz, y):
    """A patch of dark stormy sea far below (on the fall line), kept inside the level's own slot."""
    x0, x1 = max(c[0] - sx / 2, X0 + 4), min(c[0] + sx / 2, b.X1 - 4)
    c = ((x0 + x1) / 2, c[1], c[2])
    sx = x1 - x0
    Pt(b, "Sea", CF((c[0], y, c[2])), (sx, 2, sz), P_SEA, "Glass", b.scenery, transp=0.15, refl=0.2)
    for k in range(10):
        q = (c[0] + (hashf(c, k) - 0.5) * sx * 0.9, y + 1.2, c[2] + (hashf(c, k + 5) - 0.5) * sz * 0.9)
        ob(b, "Whitecap", q, (1, 0, hashf(c, k + 9) - 0.5), (4, 0.3, 30 + hashf(c, k + 2) * 40), (220, 230, 236))


def mast(b, base, h, f, sails=True):
    cyl(b, "Mast", add(base, (0, h / 2, 0)), h, 12, P_DARK, "Wood", b.scenery)
    for k, (y, wd) in enumerate(((h * 0.45, 120), (h * 0.8, 90))):
        cyl(b, "Yard", add(base, (0, y, 0)), wd, 6, P_DARK, "Wood", b.scenery, axis=right_of(f))
        if sails:
            ob(b, "Sail", add(base, add(mul(f, 4), (0, y - h * 0.16, 0))), f, (wd - 10, h * 0.3, 1), P_SAIL, "Fabric")
            ob(b, "SailStripe", add(base, add(mul(f, 4.6), (0, y - h * 0.16, 0))), f, (wd - 10, 8, 0.4), (200, 40, 40))
    for sd in (-1, 1):
        q0 = add(base, (0, h * 0.85, 0))
        q1 = add(base, add(mul(right_of(f), sd * 60), (0, 0, 0)))
        cyl(b, "Rigging", R2.lerp3(q0, q1, 0.5), math.dist(q0, q1), 1.0, P_ROPE, "Fabric", b.scenery, axis=unit(sub(q1, q0)))


def barrel_roll(b, c, w, i, period=2.8, d=22.0):
    """A barrel rolling across the deck as the ship heels (knocks you off)."""
    x, y, z = c
    z0 = (x, y + d / 2 + 0.5, z - w / 2 + 16)
    root = b.prop_root("Barrel")
    rig = b.rig(root, "Slide", axis_frame(z0, (0, 0, 1)), w - 32, period + 0.3 * i, phase=(i * 0.43) % 1, keys="0:0 0.5:1 1:0",
                name="Roll")
    cyl(b, "Barrel", z0, 30, d, (150, 96, 50), "WoodPlanks", rig, axis=(1, 0, 0), query=True, attrs={"ObbyHazard": "Knock"})
    for k in (-1, 0, 1):
        cyl(b, "BarrelHoop", add(z0, (k * 11, 0, 0)), 1.6, d + 0.6, (60, 60, 64), "Metal", rig, axis=(1, 0, 0))


def cannon_pad(sk, b, start, f):
    """A great cannon under the launch: its muzzle points up the flight, smoke round the mouth."""
    ringz(b, add(start, (0, 0.2, 0)), 14, (255, 160, 40), "Neon", th=0.3, name="MuzzleFlash")
    for sd in (-1, 1):
        q = add(start, add(mul(right_of(f), sd * 74), (0, 14, 0)))
        cyl(b, "CannonBarrel", q, 56, 20, (36, 36, 40), "Metal", b.scenery, axis=unit(add(f, (0, 0.7, 0))))
        ball(b, "CannonSmoke", add(q, add(mul(f, 24), (0, 22, 0))), 18, (220, 220, 224), "SmoothPlastic", b.scenery, transp=0.6)
        for k in (-1, 1):
            cyl(b, "CannonWheel", add(q, add(mul(right_of(f), k * 12), add(mul(f, -14), (0, -8, 0)))), 5, 18, P_DARK, "Wood",
                b.scenery, axis=right_of(f))
    fr = deck_frame(add(start, (0, 0.1, 0)), f)
    for k in range(3):
        qq = add(start, mul(f, -8 + k * 8))
        Pt(b, "PadChevron", CF(add(qq, (0, 0.3, 0)), fr.x, fr.y, fr.z), (14, 0.2, 3), GOLD, "Neon")


def treasure_obj(b, r, rng):
    c, R = disc_obj(b, r, (230, 180, 50), th=6.0, grow=1.02)
    for k in range(18):
        a = hashf(c, k) * TAU
        rr = (0.25 + 0.7 * hashf(c, k + 3)) * R
        cyl(b, "GoldCoin", add(c, (math.cos(a) * rr, 0.1, math.sin(a) * rr)), 0.2, 8, (255, 214, 70), "Metal", b.scenery,
            refl=0.3)
    sd = right_of(r.f)
    q = add(c, mul(sd, R + 20))
    ob(b, "TreasureChest", add(q, (0, 10, 0)), r.f, (30, 20, 40), (140, 84, 40), "WoodPlanks")
    ob(b, "ChestLid", add(q, (0, 26, 10)), r.f, (30, 16, 4), (140, 84, 40), "WoodPlanks")
    ob(b, "ChestGold", add(q, (0, 21, 0)), r.f, (26, 2, 36), (255, 214, 70), "Neon")
    M.ell(b, "TreasureRock", sub(c, (0, 40, 0)), (2 * R + 20, 70, 2 * R + 20), (90, 84, 76), "Slate", parent=b.scenery)


def tentacle_arm(b, rig, hub, L):
    n = 7
    for k in range(n):
        t = (k + 0.5) / n
        Pt(b, "Tentacle", CF(add(hub, (L * t, 8 + math.sin(t * 3) * 4, 0))), (L / n + 2, 12 - 7 * t, 12 - 7 * t), (110, 50, 90),
           "SmoothPlastic", rig)
        if k % 2 == 0:
            cyl(b, "Sucker", add(hub, (L * t, 2.5 + math.sin(t * 3) * 4, 0)), 1, 5, (230, 170, 190), "SmoothPlastic", rig)


def tentacle_root(b, hub):
    M.ell(b, "TentacleRoot", sub(hub, (0, 10, 0)), (30, 40, 30), (110, 50, 90), parent=b.scenery)


def kraken(b, c, f, side):
    """Giant tentacles rising out of the sea beside the ship (never over the route)."""
    rt = right_of(f)
    for k in range(4):
        base = add(c, add(mul(rt, side * (150 + k * 30)), add(mul(f, -150 + k * 100), (0, -160, 0))))
        n = 10
        for j in range(n):
            t = j / n
            q = add(base, add(mul(rt, side * math.sin(t * 2.5 + k) * 30), (0, t * 220, 0)))
            ball(b, "KrakenTentacle", q, 30 - 18 * t, (110, 50, 90), "SmoothPlastic", b.scenery)
    ball(b, "KrakenEye", add(c, add(mul(rt, side * 260), (0, -120, 0))), 50, (255, 200, 60), "Neon", b.scenery)


def slot39(r, sk, rng):
    b = r.b
    stage(r, sk, "The Pirate Ship", "OBBY 3 - LEVEL 9")
    # ---- the main deck: barrels roll across as she heels in the storm
    with look(sk, surface=DECK):
        run(r, "Main Deck", 420, w=130, boosts=2, every=60)
        hull(b, r)
        r.along(barrel_roll, [140, 240, 330])
        p0, p1, f, L, w, _ = span(r)
        mast(b, add(R2.lerp3(p0, p1, 0.08), mul(right_of(f), -(w / 2 - 14))), 240, f)
        sea(b, R2.lerp3(p0, p1, 0.5), 900, 700, p0[1] - 150)
        kraken(b, R2.lerp3(p0, p1, 0.5), f, 1)
    # ---- up the rigging: launch to the crow's nest, out along the yardarm
    o = O.Obby(r, 230)
    with look(sk, surface=DECK, pad=cannon_pad):
        o.plat("Quarterdeck", 120, 110)
        hull(b, r, gun_ports=False)
        o.pad(110.0, label="Rigging Launch")
    with look(sk, surface=SPAR):
        o.plat("Crow's Nest", 110, 70, cp=True)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        cyl(b, "NestBasket", sub(c, (0, 12, 0)), 20, 100, P_DARK, "WoodPlanks", b.scenery)
        cyl(b, "MainMast", sub(c, (0, 160, 0)), 300, 16, P_DARK, "Wood", b.scenery)
        ob(b, "JollyRoger", add(c, add(mul(right_of(f), -60), (0, 50, 0))), f, (0.5, 30, 44), BLACK)
        ob(b, "SkullMark", add(c, add(mul(right_of(f), -59.6), (0, 52, 0))), f, (0.4, 10, 10), WHITE)
        o.kick(dy=0.0, label="Yard Hop")
        o.plat("Yardarm", 220, 40)
        p0, p1, f, L, w, _ = span(r)
        ob(b, "TopSail", sub(R2.lerp3(p0, p1, 0.5), (0, 60, 0)), f, (1.2, 100, L - 20), P_SAIL, "Fabric")
        coin_row(b, p0, p1, n=6)
        o.drop(70.0, label="Sail Drop")
    # ---- the cannon: fired across to the second ship
    with look(sk, surface=DARK_DECK, pad=cannon_pad):
        o.plat("Gun Deck", 160, 120, cp=True)
        hull(b, r)
        o.pad(30.0, label="Cannon Shot")
        o.plat("Second Ship", 320, 130, cp=True)
        hull(b, r)
        p0, p1, f, L, w, _ = span(r)
        mast(b, add(R2.lerp3(p0, p1, 0.6), mul(right_of(f), w / 2 - 14)), 220, f)
        sea(b, R2.lerp3(p0, p1, 0.5), 900, 700, p0[1] - 160)
        r.along(lambda b_, c, w, i: sweeper(b_, c, w, i, tentacle_arm, speed=0.2, tower_fn=tentacle_root), [170])
        r.turn("Helm Turn", 90, 150)
    # ---- the rope bridge: swaying between the ships
    with look(sk, surface=DECK):
        def rope_art(b_, m, c, f, L, w):
            for sd in (-1, 1):
                Pt(b_, "RopeRail", CF(add(c, add(mul(right_of(f), sd * (w / 2 + 2)), (0, 12, 0))), *axes(f)), (1.4, 1.4, L), P_ROPE,
                   "Fabric", m)
            for k in range(int(L // 12)):
                Pt(b_, "BridgeSlat", CF(add(c, add(mul(f, -L / 2 + 6 + k * 12), (0, 0.06, 0))), *axes(f)), (w, 0.12, 2.0),
                   P_DARK, "Wood", m)
        swing_bridge(r, "Rope Bridge", 300, 56, (150, 104, 60), "WoodPlanks", amp_deg=8.0, period=4.0, art=rope_art)
        run(r, "Bridge Landing", 80, w=80)
    # ---- the treasure: hop across floating chests of gold
    with look(sk, surface=ghost):
        for k, (dy, side) in enumerate(((-20.0, 70.0), (-10.0, -70.0), (0.0, 60.0))):
            o.kick(dy=dy, side=side, label="Treasure Hop %d" % (k + 1))
            o.plat("Treasure %d" % (k + 1), 100, 90, cp=(k == 1))
            treasure_obj(b, r, rng)
            coin_arc(b, -1, n=5)
    # ---- the stern: an anchor swings across the poop deck, the captain's wheel at the end
    with look(sk, surface=DECK):
        o.kick(dy=0.0, label="Stern Hop")
        o.plat("Poop Deck", 340, 130, cp=True, boost=False)
        hull(b, r)
        r.along(lambda b_, c, w, i: MX.wrecking_ball(b_, c, w, i, H=90.0, amp=56, period=3.2, d=30.0, col=(60, 60, 66)), [150])
        p0, p1, f, L, w, _ = span(r)
        wq = add(R2.lerp3(p0, p1, 0.85), mul(right_of(f), w / 2 + 30))
        ringz(b, add(wq, (0, 30, 0)), 22, P_DARK, "Wood", th=4, axis=right_of(f), name="ShipWheel")
        for k in range(8):
            a = TAU * k / 8
            q = add(wq, add(mul(f, math.cos(a) * 26), (0, 30 + math.sin(a) * 26, 0)))
            ball(b, "WheelHandle", q, 4, P_DARK, "Wood", b.scenery)
        sea(b, R2.lerp3(p0, p1, 0.5), 900, 700, p0[1] - 150)
        r.turn("Stern Turn", -135, 150)
    # ---- walk the plank, drop onto a raft, hop to the sandbar
    with look(sk, surface=SPAR):
        o = O.Obby(r, 230)
        o.plat("The Plank", 200, 34, boost=False)
        p0, p1, f, L, w, _ = span(r)
        coin_row(b, p0, p1, n=5)
        o.drop(60.0, label="Off the Plank")
    with look(sk, surface=DARK_DECK):
        o.plat("Shipwreck Raft", 180, 110, cp=True)
        p0, p1, f, L, w, _ = span(r)
        for k in range(5):
            cyl(b, "RaftLog", sub(add(R2.lerp3(p0, p1, 0.5), mul(right_of(f), -w / 2 + 11 + k * (w - 22) / 4)), (0, 9, 0)), L, 14,
                (110, 74, 44), "Wood", b.scenery, axis=f)
        sea(b, R2.lerp3(p0, p1, 0.5), 700, 600, p0[1] - 150)
    with look(sk, surface=slab((236, 214, 160), "Sand", th=6)):
        o.kick(dy=10.0, label="Sandbar Hop")
        o.plat("Sandbar Island", 260, 140, cp=True, boost=False)
        p0, p1, f, L, w, _ = span(r)
        c = R2.lerp3(p0, p1, 0.5)
        M.ell(b, "IslandSand", sub(c, (0, 30, 0)), (w + 120, 60, L + 80), (230, 206, 150), "Sand", parent=b.scenery)
        for sd in (-1, 1):
            q = add(c, mul(right_of(f), sd * (w / 2 + 34)))
            cyl(b, "PalmTrunk", add(q, (0, 50, 0)), 100, 9, (150, 110, 70), "Wood", b.scenery)
            for k in range(6):
                a = TAU * k / 6
                Pt(b, "PalmLeaf", CF(add(q, (math.cos(a) * 22, 98, math.sin(a) * 22))) * rot_y(-a) * rot_axis((0, 0, 1), -0.4),
                   (46, 1.2, 12), (60, 150, 60), "SmoothPlastic", b.scenery)
        sea(b, c, 900, 800, p0[1] - 150)
        r.turn("Island Turn", 45, 200)
    end_on_line(r, "Ship Run", margin=500)
    r.log("end")
    return ["Main Deck", "Rolling Barrels", "Crow's Nest", "Yardarm", "Cannon Shot", "Kraken", "Rope Bridge",
            "Treasure Hops", "Anchor Swing"]


# ===================================================================== 10. JUNKYARD GIANTS
J_RUST, J_IRON, J_TYRE = (150, 82, 40), (110, 100, 92), (30, 30, 32)


class Junkyard(Giant):
    key, title, theme_name = "junkyard", "Junkyard Giants", "Junkyard"
    clock, bloom, hue = 17.4, 0.5, 0.07
    body, top, edge, padc, danger = J_IRON, J_RUST, (255, 170, 40), (255, 170, 40), (255, 60, 40)
    gate_post, gate_board, gate_text = J_IRON, (60, 40, 30), (255, 170, 40)
    light_over = {"Lt_Atmosphere_Density": 0.32, "Lt_Atmosphere_Haze": 1.8,
                  "Lt_Atmosphere_Color": ("Color3", 0.85, 0.6, 0.42)}


SCRAP = slab(J_RUST, "CorrodedMetal", th=6, side=(110, 60, 30), deco=lines_across((120, 64, 30), 26, width=1.2, name="PlateSeam"))
IRON = slab(J_IRON, "DiamondPlate", th=4, deco=hazard_edges)
TREAD = slab(J_TYRE, "SmoothPlastic", th=4, deco=lines_across((60, 60, 64), 10, width=3.0, name="Tread"))


def tyre_cap(b, top, s, rng):
    """A giant tyre lying flat: the bounce is its hub."""
    cyl(b, "Platform", sub(top, (0, 1.5, 0)), 3, s * 0.6, (170, 174, 180), "Metal", b.roads, collide=True)
    ringz(b, sub(top, (0, 10, 0)), s * 0.56, J_TYRE, "SmoothPlastic", th=24, name="Tyre")
    for k in range(5):
        a = TAU * k / 5
        cyl(b, "WheelNut", add(top, (math.cos(a) * s * 0.12, 0.1, math.sin(a) * s * 0.12)), 0.2, 5, (90, 90, 96), "Metal",
            b.scenery)


def old_car(b, r, col):
    """A wrecked car whose crumpled roof is the stretch."""
    p0, p1, f, L, w, _ = span(r)
    c = R2.lerp3(p0, p1, 0.5)
    rt = right_of(f)
    Pt(b, "Platform", CF(sub(c, (0, 2, 0)), *axes(f)), (w + 4, 4, L + 4), mix(col, J_RUST, 0.35), "CorrodedMetal", b.roads,
       collide=True)
    ob(b, "CarCabin", sub(c, (0, 18, 0)), f, (w - 4, 30, L - 10), mix(col, BLACK, 0.2), "Metal")
    ob(b, "CarBody", sub(c, (0, 50, 0)), f, (w + 30, 36, L * 1.9), mix(col, J_RUST, 0.25), "CorrodedMetal")
    for sd in (-1, 1):
        ob(b, "CarWindow", add(c, add(mul(rt, sd * (w / 2 - 1.7)), (0, -16, 0))), f, (0.4, 18, L - 20), (60, 70, 80), "Glass")
        for a in (-1, 1):
            ringz(b, add(c, add(mul(f, a * L * 0.7), add(mul(rt, sd * (w / 2 + 15)), (0, -66, 0)))), 14, J_TYRE, "SmoothPlastic",
                  th=10, axis=rt, name="CarTyre")


def spring_pad_rust(sk, b, start, f):
    for k in range(6):
        ringz(b, add(start, (0, -6 - k * 7, 0)), 20, (120, 90, 70), "CorrodedMetal", th=3.0, name="SpringCoil")
    fr = deck_frame(add(start, (0, 0.1, 0)), f)
    for k in range(3):
        q = add(start, mul(f, -8 + k * 8))
        Pt(b, "PadChevron", CF(add(q, (0, 0.3, 0)), fr.x, fr.y, fr.z), (14, 0.2, 3), (255, 170, 40), "Neon")


def piston_pump(b, c, w, i, period=1.8):
    """Engine pistons pumping up through the block (crush): pass over one while it is down."""
    x, y, z = c
    for k, lane in enumerate((-1, 0, 1)):
        if (k + i) % 2 == 1:
            continue
        q = (x, y - 26, z + lane * w / 3)
        root = b.prop_root("Piston")
        rig = b.rig(root, "Slide", axis_frame(q, UP), 30.0, period, phase=((i + k) * 0.27) % 1, keys="0:0 0.4:0 0.5:1 0.7:1 0.8:0",
                    name="Pump")
        cyl(b, "PistonHead", q, 20, w / 3 - 8, (190, 194, 200), "Metal", rig, query=True, attrs={"ObbyHazard": "Crush"}, refl=0.3)
        cyl(b, "PistonRing", add(q, (0, 6, 0)), 2, w / 3 - 7.4, (255, 170, 40), "Neon", rig)
        ringz(b, (x, y + 0.2, z + lane * w / 3), (w / 3 - 6) / 2, (40, 40, 44), "Metal", th=0.4, name="PistonBore")


def scrap_pile(b, base, s, rng):
    for k in range(7):
        q = add(base, ((hashf(base, k) - 0.5) * s, hashf(base, k + 3) * s * 0.4, (hashf(base, k + 6) - 0.5) * s))
        Pt(b, "Scrap", CF(q) * rot_y(hashf(base, k + 9) * 3) * rot_axis((1, 0, 0), hashf(base, k + 12)),
           (s * 0.4, s * 0.12, s * 0.3), [J_RUST, J_IRON, (90, 110, 130), (160, 50, 40)][k % 4], "CorrodedMetal", b.scenery)


def slot40(r, sk, rng):
    b = r.b
    stage(r, sk, "Junkyard Giants", "OBBY 3 - LEVEL 10")
    b.final_slot = True
    # ---- the scrap ramp in: rusted plates, piles of junk on both sides
    with look(sk, surface=SCRAP):
        run(r, "Scrap Ramp", 260, w=130, boosts=2, every=60)
        p0, p1, f, L, w, _ = span(r)
        for k in range(4):
            for sd in (-1, 1):
                scrap_pile(b, add(R2.lerp3(p0, p1, 0.15 + 0.22 * k), mul(right_of(f), sd * (w / 2 + 40))), 50, rng)
        ob(b, "ScrapHeap", sub(R2.lerp3(p0, p1, 0.5), (0, 40, 0)), f, (w + 40, 70, L), (90, 70, 56), "CorrodedMetal")
    # ---- the tyre stacks: bounce off their hubs
    with look(sk, surface=TREAD):
        R2.bounce_chain(r, "Tyre Bounce", [(250.0, 20.0, 50.0), (250.0, 10.0, -60.0), (250.0, 0.0, 40.0)], 230.0, s=100.0,
                        cap=tyre_cap, land_L=140.0, cp=True, shroom=False)
    # ---- the wrecks: hop across the roofs of crushed cars
    o = O.Obby(r, 230)
    with look(sk, surface=ghost):
        for k, (dy, side, col) in enumerate(((-20.0, 60.0, (60, 110, 160)), (0.0, -60.0, (170, 50, 40)),
                                              (-10.0, 60.0, (90, 140, 80)))):
            o.kick(dy=dy, side=side, label="Wreck Hop %d" % (k + 1))
            o.plat("Wreck %d" % (k + 1), 110, 80, cp=(k == 1))
            old_car(b, r, col)
            coin_arc(b, -1, n=4)
    # ---- the magnet crane: over the crusher pit
    with look(sk, surface=IRON):
        o.kick(dy=0.0, label="Crane Hop")
        o.plat("Crane Pad", 120, 100)
        MX.crane_transfer(r, "Magnet Crane", 440.0, dy=40.0, land_L=160.0, w_land=100, cp=True)
        lip = r.p
        r.turn("Yard Bend", 90, 150)
    # ---- the engine block: pistons pump up through it
    with look(sk, surface=IRON):
        run(r, "Engine Block", 380, w=120, cp=True)
        r.along(piston_pump, [90, 180, 270])
        p0, p1, f, L, w, _ = span(r)
        ob(b, "EngineCasting", sub(R2.lerp3(p0, p1, 0.5), (0, 50, 0)), f, (w + 20, 90, L), (80, 84, 90), "Metal")
        for sd in (-1, 1):
            for k in range(4):
                cyl(b, "ExhaustPipe", add(R2.lerp3(p0, p1, 0.2 + 0.2 * k), add(mul(right_of(f), sd * (w / 2 + 14)), (0, 0, 0))),
                    40, 10, (120, 100, 90), "CorrodedMetal", b.scenery)
    # ---- the fan duct: giant fans turn in a pipe, go through between the blades
    with look(sk, surface=IRON):
        run(r, "Fan Duct", 320, w=70, cp=True)
        pipe(b, span(r)[0], span(r)[2], 320, 70, col=(120, 100, 90))
        r.along(lambda b_, c, w, i: MX.fan(b_, c, w, i, R=46.0, n=3, speed=0.22, col=(150, 140, 120)), [110, 220])
        r.turn("Duct Bend", -90, 150)
    # ---- the springs: up the scrap mountain
    o = O.Obby(r, 230)
    with look(sk, surface=SCRAP, pad=spring_pad_rust):
        for k in range(2):
            o.pad(60.0, side=(40, -40)[k], label="Spring %d" % (k + 1))
            o.plat("Scrap Ledge %d" % (k + 1), 140, 100, cp=(k == 1))
            p0, p1, f, L, w, _ = span(r)
            ob(b, "ScrapMountain", sub(R2.lerp3(p0, p1, 0.5), (0, 60, 0)), f, (w + 50, 110, L + 30), (90, 70, 56), "CorrodedMetal")
            scrap_pile(b, add(R2.lerp3(p0, p1, 0.5), mul(right_of(f), w / 2 + 30)), 40, rng)
    # ---- the claw arm on the summit, and the drop to the yard gate
    with look(sk, surface=SCRAP):
        o.kick(dy=0.0, label="Summit Hop")
        o.plat("Summit", 300, 120, cp=True, boost=False)
        r.along(lambda b_, c, w, i: sweeper(b_, c, w, i, excavator_arm, speed=0.22, tower_fn=excavator_tower), [150])
        o.drop(80.0, label="Gate Drop")
        o.plat("Yard Gate", 200, 140)
        p0, p1, f, L, w, _ = span(r)
        for sd in (-1, 1):
            ob(b, "GatePost", add(R2.lerp3(p0, p1, 0.6), add(mul(right_of(f), sd * (w / 2 + 12)), (0, 50, 0))), f, (14, 100, 14),
               J_IRON, collide=True)
        ob(b, "GateSign", add(R2.lerp3(p0, p1, 0.6), (0, 96, 0)), f, (w + 40, 18, 4), (255, 170, 40))
    end_on_line(r, "Yard Run", margin=500)
    r.log("end")
    return ["Scrap Ramp", "Tyre Bounce", "Car Wrecks", "Magnet Crane", "Engine Block", "Fan Duct", "Spring Climb",
            "Scrap Summit"]


LEVELS = {31: slot31, 32: slot32, 33: slot33, 34: slot34, 35: slot35, 36: slot36, 37: slot37, 38: slot38, 39: slot39, 40: slot40}
SKINS = {31: Kitchen, 32: Toybox, 33: Candy, 34: Arcade, 35: Forest, 36: Construction, 37: Bedroom, 38: Space, 39: Pirate,
         40: Junkyard}
