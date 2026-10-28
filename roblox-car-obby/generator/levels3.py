"""100 levels from 25 object worlds x 4 visits, each with its own layout grammar, scale and module mix."""
import math
import random
import colorsys
import rbxl
from builder import LevelBuilder, X0, ZC, Y0
import parkour as V2
import parkour3 as K
from parkour3 import MODULES, HERO
from parkour import St
from worlds import WORLDS
import landmarks

NAMES = {
    "mushroom": ["Mushroom Hop", "Spore Springs", "Toadstool Trail", "Fungi Falls"],
    "chess": ["Checkmate", "Rook Run", "Pawn Storm", "Castle Rush"],
    "dice": ["Roll the Dice", "Snake Eyes", "High Roller", "Lucky Seven"],
    "gears": ["Gearbox", "Cog Climb", "Clockwork Factory", "Sprocket Sprint"],
    "candy": ["Gumdrop Galaxy", "Lollipop Lane", "Sugar Rush", "Choco Drop"],
    "burger": ["Burger Stack", "Fast Food", "Double Cheese", "Drive Thru"],
    "islands": ["Sky Islands", "Floating Isles", "Rope Bridges", "Cliffside Hop"],
    "clouds": ["Cloud Nine", "Rainbow Road", "Silver Lining", "Stratus Sprint"],
    "crystals": ["Crystal Caves", "Basalt Steps", "Geode Jump", "Prism Pillars"],
    "planets": ["Planet Hop", "Orbit", "Gravity Well", "Moon Bounce"],
    "lily": ["Lily Pads", "Frog Leap", "Pond Skipper", "Bamboo Raft"],
    "music": ["Drum Roll", "Piano Keys", "Bass Drop", "Encore"],
    "toys": ["Brick Builder", "Toy Box", "Block Party", "Stud Run"],
    "clocks": ["Tick Tock", "Clockface", "Overtime", "Midnight Rush"],
    "snow": ["Snowflake", "Frostbite", "Blizzard", "Ice Crystal"],
    "golf": ["Hole in One", "Fairway Flight", "Par Three", "Back Nine"],
    "satellites": ["Satellite", "Space Walk", "Solar Array", "Low Orbit"],
    "circuits": ["Motherboard", "Overclock", "Short Circuit", "Microchip"],
    "ruins": ["Temple Columns", "Acropolis", "Ancient Steps", "Colosseum"],
    "ocean": ["Buoy Bounce", "Pier Pressure", "High Tide", "Harbour Hop"],
    "desert": ["Mesa Leap", "Canyon Run", "Dust Bowl", "Sandstone"],
    "volcano": ["Obsidian", "Magma Hop", "Lava Lamp", "Eruption"],
    "arcade": ["Coin Collector", "Bonus Round", "Extra Life", "High Score"],
    "bakery": ["Cake Walk", "Sweet Tiers", "Cherry On Top", "Bake Off"],
    "garden": ["Flower Power", "Petal Hop", "Bloom", "Garden Party"],
}

LAYOUTS = ["straight", "rising", "lanes", "wave", "falling", "steps"]
SCALES = [1.0, 0.85, 1.2, 0.95]
HOPS = ["hop_line", "hop_rise", "hop_fall", "hop_lanes", "hop_wave", "hop_tiny", "spiral_tower", "long_jump", "drop_shaft"]
ROT = ["rot_door", "log", "cross", "spin_bridges", "sweepers", "turntable", "windmill"]
MOVE = ["pendulums", "slide", "pistons", "crushers", "doors"]
SKILL = ["lasers", "limbo", "crumble", "conveyors", "ice_rink", "bumpers", "split", "slalom", "zigzag"]
HEROES = list(HERO)


def palette(level_id):
    world = WORLDS[(level_id - 1) % len(WORLDS)]
    v = (level_id - 1) // len(WORLDS)
    p = dict(world.palette(v))
    p.setdefault("glass", (230, 240, 255))
    p.update(road=p["top"], road_mat=p["top_mat"], accent=p["pad"], accent2=p["body"], metal=p["body"], deco=p["body"],
             key=world.key, boost_speed=230)
    p["style"] = world.key
    return world, v, p


def light_attrs(p):
    def c3(c):
        return ("Color3", c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)

    def hsv(h, s, v):
        r, g, b = colorsys.hsv_to_rgb(h % 1, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))
    h = p.get("hue", 0.0)
    dark = p["clock"] > 17.5 or p["clock"] < 7
    return {
        "Lt_Lighting_ClockTime": p["clock"], "Lt_Lighting_Brightness": 2.4 if dark else 3.0,
        "Lt_Lighting_Ambient": c3(hsv(h, 0.25, 0.35 if dark else 0.45)),
        "Lt_Lighting_OutdoorAmbient": c3(hsv(h, 0.2, 0.5 if dark else 0.62)),
        "Lt_Lighting_ColorShift_Top": c3(hsv(h, 0.12, 1.0)), "Lt_Lighting_ExposureCompensation": 0.05 if dark else 0.15,
        "Lt_Lighting_EnvironmentDiffuseScale": 1.0, "Lt_Lighting_EnvironmentSpecularScale": 0.6,
        "Lt_Lighting_ShadowSoftness": 0.15, "Lt_CC_TintColor": c3(hsv(h, 0.05, 1.0)), "Lt_CC_Saturation": 0.2,
        "Lt_CC_Contrast": 0.14, "Lt_CC_Brightness": 0.0, "Lt_Bloom_Intensity": p["bloom"], "Lt_Bloom_Size": 22.0,
        "Lt_Bloom_Threshold": 1.25 if dark else 1.5, "Lt_SunRays_Intensity": 0.04, "Lt_SunRays_Spread": 0.4,
        "Lt_Atmosphere_Density": 0.04, "Lt_Atmosphere_Haze": 0.2, "Lt_Atmosphere_Glare": 0.0,
        "Lt_Atmosphere_Color": c3(hsv(h, 0.15, 0.95)), "Lt_Atmosphere_Decay": c3(hsv(h, 0.3, 0.6)),
    }


def all_recipes():
    """Every level's module order, balancing use so no module is everywhere and stunts stay rare."""
    use = {k: 0 for k in MODULES}
    hero_left = dict(HERO)
    out = {}
    prev = set()
    for lid in range(1, 101):
        rng = random.Random(9000 + lid * 31)

        def pick(pool, avoid):
            cands = [k for k in pool if k not in avoid]
            rng.shuffle(cands)
            cands.sort(key=lambda k: use[k])
            k = cands[0]
            use[k] += 1
            return k
        chosen = []
        avoid = set(prev)
        hero = None
        heroes = [h for h in HEROES if hero_left[h] > 0 and h not in prev]
        if heroes and rng.random() < 0.5:
            rng.shuffle(heroes)
            heroes.sort(key=lambda h: -hero_left[h])
            hero = heroes[0]
            hero_left[hero] -= 1
            use[hero] += 1
        h1 = pick(HOPS, avoid)
        avoid.add(h1)
        h2 = pick(HOPS, avoid)
        avoid.add(h2)
        r1 = pick(ROT, avoid)
        avoid.add(r1)
        m1 = pick(MOVE, avoid)
        avoid.add(m1)
        s1 = pick(SKILL, avoid)
        avoid.add(s1)
        r2 = pick(ROT, avoid)
        avoid.add(r2)
        seq = [h1, r1, hero or pick(SKILL, avoid), m1, h2, s1, r2]
        out[lid] = seq
        prev = set(seq)
    return out


RECIPES = all_recipes()


def build_level(fac, unit, level_folder, level_id, length, templates):
    world, variant, pal = palette(level_id)
    title = NAMES[world.key][variant]
    seq = list(RECIPES[level_id])
    rng = random.Random(5000 + level_id * 7919)
    b = LevelBuilder(fac, level_folder, pal, rng, length, templates)
    b.world = world
    b.zc = ZC
    scale = SCALES[variant]
    b.look = {"shape": "square", "scale": scale, "layout": LAYOUTS[(level_id * 7 + variant) % len(LAYOUTS)],
              "lane": 70.0 * scale}
    X1 = X0 + length
    d_base = 0.25 + 0.55 * (level_id - 1) / 99.0
    K.run(b, X0, X0 + 110, Y0, ZC, 144)
    b.checkpoint(X0 + 30, Y0, ZC, 144)
    b.line(X0, Y0, ZC)
    st = St(X0 + 110, Y0, ZC, 60, ZC)
    sandbox = rbxl.Inst("Folder")

    def d_now(s):
        return min(1.0, d_base + 0.18 * (s.x - X0) / length)

    def trial(key, s):
        state = rng.getstate()
        tb = LevelBuilder(fac, sandbox, pal, rng, length, templates)
        tb.world, tb.zc, tb.look = world, ZC, b.look
        ts = St(s.x, s.y, s.z, s.w, ZC)
        tb.pending_landing = getattr(b, "pending_landing", False)
        MODULES[key](tb, ts, d_now(s), rng)
        rng.setstate(state)
        sandbox.children.clear()
        return ts

    def reserve(s):
        return 110 + 200 + max(200 * (abs(s.y - Y0) / 70.0), 200 * abs(s.z - ZC) / 120.0)

    used = []
    fill = [k for k in HOPS + ROT + MOVE + SKILL if k not in seq]
    rng.shuffle(fill)
    queue = list(seq)
    while True:
        key = None
        while queue:
            k = queue.pop(0)
            t = trial(k, st)
            if t.x + 40 + reserve(t) <= X1 and b.ylo - 20 <= t.y <= b.yhi + 20:
                key = k
                break
        if key is None:
            for k in list(fill):
                t = trial(k, st)
                if t.x + 40 + reserve(t) <= X1 and b.ylo - 20 <= t.y <= b.yhi + 20:
                    key = k
                    fill.remove(k)
                    break
        if key is None:
            break
        MODULES[key](b, st, d_now(st), rng)
        used.append(key)
        dy = rng.choice([-1, 1]) * K.snap(rng.uniform(30, 60), 15)
        if st.y + dy > b.yhi or st.y + dy < b.ylo:
            dy = -dy
        if (st.x - X0) / length > 0.55:
            dy = K.snap(max(-60, min(60, (Y0 - st.y) * 0.4)), 15)
        link(b, st, rng, dy)
    if X1 - 110 - st.x < 60:
        raise RuntimeError("L%03d overran by %.0f" % (level_id, st.x - (X1 - 110)))
    if getattr(b, "pending_landing", False):
        K.run(b, st.x, st.x + 80, st.y, st.z, K.W(b, 52))
        b.line(st.x + 22, st.y, st.z)
        st.x += 80
        b.pending_landing = False
    finale(b, st, rng, X1 - 110 + 30, Y0, ZC)
    K.run(b, X1 - 110, X1, Y0, ZC, 160)
    b.line(X1, Y0, ZC)
    landmarks.title_gate(b, level_id, title)
    b.kill_sheets()
    a = rbxl.attrs(level_folder)
    for k in [k for k in a if k.startswith("Lt_")]:
        del a[k]
    a.update(light_attrs(pal))
    a["ObbyLevelTitle"] = title
    a["ObbyLook"] = "ob%03d" % level_id
    rbxl.set_attrs(level_folder, a)
    ua = rbxl.attrs(unit)
    ua["Title"] = title
    rbxl.set_attrs(unit, ua)
    return b, used, title, world.key


def finale(b, st, rng, x_end, y_end, z_end):
    """World-object hops home, landing on the join deck."""
    src = (st.x - 16, st.y, st.z)
    n = max(1, int(round((x_end - src[0]) / 200)))
    step = (x_end - src[0]) / n
    prev = src
    for i in range(1, n + 1):
        t = i / n
        if i < n:
            tgt = (prev[0] + step, K.snap(st.y + (y_end - st.y) * K.ease(t), 15), st.z + (z_end - st.z) * K.ease(t))
        else:
            tgt = (x_end, y_end, z_end)
        K.pad_to(b, prev, tgt)
        if i < n:
            K.tile(b, tgt, K.W(b, 52))
        prev = tgt


def link(b, st, rng, dy):
    """A straight hop onto the next module's rest platform: same lane, or one lane over, never in between."""
    src = (st.x - 16, st.y, st.z)
    lane = b.look["lane"]
    k = round((st.z - ZC) / lane)
    if rng.random() < 0.35:
        k += rng.choice([-1, 1])
    k = max(-2, min(2, k))
    tz = ZC + k * lane
    tgt = (src[0] + 200, st.y + dy, tz)
    K.pad_to(b, src, tgt)
    st.x, st.y, st.z = tgt[0] - 22, tgt[1], tz
    b.pending_landing = True
