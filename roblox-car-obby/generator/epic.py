"""The ten showcase levels as big 3D journeys (route.py lays them; skins.py draws them; layouts in epic_levels.py)."""
import math
import random
import rbxl
from builder import LevelBuilder, X0, ZC, Y0
import parkour3 as K
import landmarks
import route as RT


def build_level(fac, unit_, level_folder, level_id, length, templates):
    import skins
    import journey_skins  # noqa: F401
    import epic_skins  # noqa: F401
    import epic_levels
    skin = skins.SKINS[level_id]()
    pal = skin.pal()
    rng = random.Random(91000 + level_id * 1301)
    b = LevelBuilder(fac, level_folder, pal, rng, length, templates)

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
    used = epic_levels.LEVELS[level_id](r, skin, rng)
    # home: arrive on the centre line heading down the course
    end = (X1 - 110, Y0, ZC)
    if math.dist(r.p, end) > 1:
        r.connect("Final Dash", end, (1, 0, 0), w1=72)
        L = sum(math.dist(a, c) for a, c in zip(r.last[0], r.last[0][1:]))
        if L > 600:
            import epic_kit as EK
            kinds = getattr(epic_levels, "FINAL", {}).get(level_id, [EK.ob_sweeper, EK.ob_gate])
            at = [220 + 280 * k for k in range(int((L - 420) // 280) + 1)]
            for k, d in enumerate(at):
                r.along(kinds[k % len(kinds)], [d], i0=k)
    K.run(b, X1 - 110, X1, Y0, ZC, 160)
    skin.finish(b, X1 - 110, X1, Y0, ZC, 160)
    b.line(X1, Y0, ZC)
    landmarks.title_gate(b, level_id, skin.title)
    skin.environment(b)
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
