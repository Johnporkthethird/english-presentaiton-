"""The ten showcase levels as big 3D journeys (route.py lays them; skins.py draws them; layouts in epic_levels.py)."""
import math
import random
import rbxl
from builder import LevelBuilder, X0, ZC, Y0
import parkour3 as K
import landmarks
import route as RT


SOFT = ("Hoop", "Ring", "Updraft", "Target", "Halo", "Laser", "Glow", "Flame", "Stripe", "Lip", "Edge", "Chevron", "Arrow",
        "Beam", "Light", "Line", "Trim", "Sign", "Text", "Letter", "Pixel", "Kicker", "Sprinkle", "Sugar", "Spot", "Shine",
        "Drip", "Pearl", "Sesame", "Tick", "Hand", "Numeral", "Toe", "Eye", "Smile", "Nose", "Button", "Ghost", "Swirl",
        "Frill", "Crack", "LavaFall", "Crater", "Bow", "Cheek", "Tuft", "Cloth", "Flag", "Coin", "Leaves", "Crown", "Fruit",
        "Vine", "Moon", "Atmosphere", "Band", "Cream", "Whip", "Straw", "Stem")


def solidify(b):
    """Make the big scenery solid, so a car that strays into a landmark hits it instead of passing through. Blocks,
    cylinders, balls and wedge shells collide as they are; an ellipsoid gets an invisible ball inside it (a part with a
    sphere mesh would collide as its whole box). Thin, glowing or see-through dressing stays a ghost."""
    from factory import is_basepart, MAT
    from geom import CF
    neon = MAT["Neon"]
    n = 0
    for d in list(b.scenery.descendants()):
        if not is_basepart(d) or d.cls == "MeshPart" or d.get("CanCollide"):
            continue
        if d.get("Transparency", 0.0) > 0.3 or d.get("Material") == neon or any(k in d.name for k in SOFT):
            continue
        sz = d.get("size")
        if any(c.cls == "SpecialMesh" for c in d.children):
            if min(sz) >= 10:
                cf = CF.from_prop(d.get("CFrame"))
                k = min(sz) * 0.9
                b.part(d.name + "Solid", CF(cf.p), (k, k, k), (255, 255, 255), parent=d.parent, transp=1, collide=True,
                       shape=0)
                n += 1
            continue
        thin_ok = d.cls == "WedgePart" and min(sz) >= 0.9
        if (min(sz) < 3 and not thin_ok) or max(sz) < 10:
            continue
        d.set("CanCollide", True)
        d.set("CanQuery", True)
        n += 1
    return n


def build_level(fac, unit_, level_folder, level_id, length, templates):
    import skins
    import journey_skins  # noqa: F401
    import epic_skins  # noqa: F401
    import rush_levels as old_levels
    import rush3_levels
    epic_levels = rush3_levels if level_id in rush3_levels.LEVELS else old_levels
    new = epic_levels is rush3_levels
    skin = skins.SKINS[level_id]()
    pal = skin.pal()
    rng = random.Random(91000 + level_id * 1301)
    b = LevelBuilder(fac, level_folder, pal, rng, length, templates)
    b.level_id = level_id

    class World:
        def deck(self, tb, x0, x1, y, z, w, parent=None):
            skin.deck(tb, x0, x1, y, z, w)
            skin.supports(tb, x0, x1, y, z, w)

        def plat(self, tb, top, s, rng_, parent=None):
            skin.plat(tb, top, s, rng_)

    b.world = World()
    b.skin = skin
    b.zc = ZC
    b.look = {"shape": "square", "scale": skin.scale, "layout": "straight", "lane": 70.0 * skin.scale}
    b.pieces = []
    b.cp_step = 0.025
    b.ylo, b.yhi = Y0 - 460, Y0 + 560
    X1 = X0 + length
    # the start grid
    K.run(b, X0, X0 + 110, Y0, ZC, 144)
    b.checkpoint(X0 + 30, Y0, ZC, 144)
    b.line(X0, Y0, ZC)
    r = RT.Route(b, (X0 + 110, Y0, ZC), (1, 0, 0), 64)
    r.rng = rng
    r.X1 = X1
    import os
    r.defer_dress = []
    if os.environ.get("GALLERY") and level_id == 1:
        import gallery
        used = gallery.build(r, skin, rng)
    else:
        used = epic_levels.LEVELS[level_id](r, skin, rng)
    # home: arrive on the centre line heading down the course
    end = (X1 - 110, Y0, ZC)
    import rush
    k = 0
    import rush2
    import obby as OB
    while new and X1 - 110 - r.p[0] > 900 and k < 6 and not os.environ.get("GALLERY"):
        # keep the obby going all the way home: aim at the finish (gently), a platform with a trap, a jump
        rush.aim(r, "Home Bend %d" % (k + 1), length - 110, 0.0, R=300, limit=50)
        o = OB.Obby(r, 230)
        traps = [OB.saw, OB.crusher, OB.sweeper, OB.pusher, OB.axe, OB.mine]
        o.plat("Home Deck %d" % (k + 1), 150, [50, 36, 24][k % 3], [(traps[(k + level_id) % 6], 0.5)], cp=(k % 2 == 0))
        dh = Y0 - r.p[1]
        if dh > 30:
            o.pad(min(dh, 120.0), side=(-40 if k % 2 else 40))
        else:
            o.drop(max(30.0, min(60.0, -dh)), side=(40 if k % 2 else -40))
        o.plat("Home Landing %d" % (k + 1), 0, 50)
        k += 1
    while not new and X1 - 110 - r.p[0] > 760 and k < 6 and not os.environ.get("GALLERY"):
        # keep the beats coming all the way home: aim at the finish and jump again
        rush.aim(r, "Home Bend %d" % (k + 1), length - 110, 0.0, R=100, limit=60)
        dy = max(-60.0, min(60.0, (Y0 - r.p[1]) * 0.6))
        rush.kick(r, "Home Jump %d" % (k + 1), 250, dy, rings=2 + k % 3, mill=(k % 3 == 1))
        if X1 - 110 - r.p[0] > 900:
            rush.gauntlet(r, "Home Run %d" % (k + 1), 180, epic_levels.FINAL[level_id][k % 2:] + epic_levels.FINAL[level_id][:k % 2],
                          every=70)
        k += 1
    if not os.environ.get("GALLERY"):
        # too little room left to roll back to the finish height: step down (or boost up) first
        import journey as J
        dh = Y0 - r.p[1]
        need = abs(dh) * 1.32 / (J.MAX_GRADE * 0.95) + 120
        if math.dist(r.p, end) < need and abs(dh) > 8:
            if dh < 0:
                n = int(math.ceil(-dh / 40.0))
                rush.drops(r, "Home Steps", n, step=-dh / n)
            else:
                rush.booster(r, "Home Boost", 160, dh)
    if math.dist(r.p, end) > 1:
        r.connect("Final Dash", end, (1, 0, 0), w1=72)
        L = sum(math.dist(a, c) for a, c in zip(r.last[0], r.last[0][1:]))
        if new and L > 300:
            rush2.lay_strips(r, 60, L - 160, every=90)
        if L > 600 and not new:
            import epic_kit as EK
            kinds = getattr(epic_levels, "FINAL", {}).get(level_id, [EK.ob_sweeper, EK.ob_gate])
            at = [220 + 280 * k for k in range(int((L - 420) // 280) + 1)]
            for k, d in enumerate(at):
                r.along(kinds[k % len(kinds)], [d], i0=k)
    K.run(b, X1 - 110, X1, Y0, ZC, 160)
    skin.finish(b, X1 - 110, X1, Y0, ZC, 160)
    jobs, r.defer_dress = r.defer_dress, None
    for job in jobs:
        rush2.dress(r, *job)
    b.line(X1, Y0, ZC)
    landmarks.title_gate(b, level_id, skin.title)
    skin.environment(b)
    solidify(b)
    RT.kill_sheets(b)
    b.route = r
    for o in RT.overlaps(r):
        print("   OVERLAP", o)
    bad = RT.bounds(b)
    if bad:
        print("   OUT OF BOX", len(bad), bad[:5])
    a = rbxl.attrs(level_folder)
    for k in [k for k in a if k.startswith("Lt_")]:
        del a[k]
    a.update(skin.light())
    a["ObbyLevelTitle"] = skin.title
    a["ObbyLook"] = "sc%03d" % level_id
    rbxl.set_attrs(level_folder, a)
    ua = rbxl.attrs(unit_)
    ua["Title"] = skin.title
    rbxl.set_attrs(unit_, ua)
    return b, used, skin.title, skin.key
