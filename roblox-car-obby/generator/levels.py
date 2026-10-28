"""The 100 levels: names, worlds, obstacle sequences, and the planner that fits them to each level's length."""
import math
import random
import colorsys
import rbxl
from builder import LevelBuilder, X0, ZC, Y0, mix
from sections import St, SECTIONS, LENGTHS, DY, connect
from themes import THEMES
import decor
import landmarks

THEME_ORDER = ["neon_city", "candy", "volcano", "glacier", "jungle", "desert", "space", "synthwave", "ocean", "haunted",
               "golden", "factory", "cloud", "crystal", "aurora", "toxic", "sakura", "arcade", "storm", "sunset",
               "deepsea", "mars", "royal", "matrix", "rainbow"]

# id: (title, [sections in order])  - the theme is THEME_ORDER[(id - 1) % 25]
LEVELS = {
    1: ("Neon Launch", "runway scurve gaps spinners kicker lasers banked"),
    2: ("Sugar Rush", "runway zigzag bumpers wave hills islands"),
    3: ("Magma Run", "runway lava crushers stairs kicker scurve"),
    4: ("Frostbite Pass", "runway ice gaps sweepers coaster drop"),
    5: ("Canopy Chaos", "runway beam hammers islands climb slalom"),
    6: ("Mesa Madness", "runway kicker banked pistons gaps stairs"),
    7: ("Orbit Station", "runway turntable lasers tower drop beam"),
    8: ("Outrun 84", "runway coaster doors lasers kicker zigzag"),
    9: ("Tidal Rush", "runway bridges wave scurve islands conveyor"),
    10: ("Gravecrawl", "runway crumble hammers beam windmills stairs"),
    11: ("Sun Temple", "runway climb crushers zigzag drop spinners"),
    12: ("Scrapheap Sprint", "runway conveyor pistons crushers gaps banked"),
    13: ("Cloudhopper", "runway islands beam bridges hills kicker"),
    14: ("Amethyst Depths", "runway stairs sweepers crumble coaster lasers"),
    15: ("Aurora Drift", "runway ice banked gaps windmills scurve"),
    16: ("Biohazard Bypass", "runway mud pistons lava slalom kicker"),
    17: ("Petal Storm", "runway scurve crumble hammers islands hills"),
    18: ("Pixel Panic", "runway bumpers zigzag doors wave tower"),
    19: ("Thunderhead", "runway windmills gaps lasers drop coaster"),
    20: ("Golden Coast", "runway banked kicker slalom hills bridges"),
    21: ("Abyssal Trench", "runway stairs wave sweepers turntable climb"),
    22: ("Red Planet Rally", "runway kicker islands mud crushers beam"),
    23: ("Crown Circuit", "runway doors halfpipe hammers scurve gaps"),
    24: ("Code Runner", "runway lasers zigzag crumble tower sweepers"),
    25: ("Prism Highway", "runway coaster islands spinners drop hills"),
    26: ("Midnight Grid", "runway halfpipe lasers split crushers coaster"),
    27: ("Gumdrop Gauntlet", "runway hammers crumble scurve kicker turntable"),
    28: ("Caldera Leap", "runway islands lava windmills stairs banked"),
    29: ("Avalanche Alley", "runway drop ice slalom tower beam"),
    30: ("Vine Swing", "runway split hammers gaps coaster climb"),
    31: ("Dune Drifter", "runway hills sweepers bridges kicker zigzag"),
    32: ("Zero-G Docks", "runway islands crushers wave doors drop"),
    33: ("Laser Boulevard", "runway lasers sweepers coaster lasers kicker"),
    34: ("Reef Racer", "runway beam islands bumpers stairs scurve"),
    35: ("Phantom Mile", "runway doors stairs crumble halfpipe gaps"),
    36: ("Pharaoh's Ascent", "runway tower spinners scurve pistons drop"),
    37: ("Assembly Line", "runway conveyor slalom conveyor crushers kicker"),
    38: ("Skybridge Sprint", "runway bridges hammers coaster gaps drop"),
    39: ("Geode Grinder", "runway turntable windmills beam lasers stairs"),
    40: ("Polar Express", "runway coaster ice pistons islands banked"),
    41: ("Acid Rain", "runway lava crumble doors scurve gaps"),
    42: ("Lantern Run", "runway zigzag hammers bridges tower hills"),
    43: ("Coin-Op Chaos", "runway turntable bumpers lasers kicker wave"),
    44: ("Eye of the Storm", "runway banked sweepers crushers islands drop"),
    45: ("Boulevard of Palms", "runway kicker conveyor coaster slalom split"),
    46: ("Pressure Drop", "runway drop wave crushers beam turntable"),
    47: ("Dust Devil", "runway sweepers gaps tower mud scurve"),
    48: ("Throne Room", "runway crushers zigzag doors islands hills"),
    49: ("Firewall", "runway doors lasers wave windmills drop"),
    50: ("Spectrum Spiral", "runway banked islands crumble hammers kicker"),
    51: ("Rooftop Rush", "runway gaps tower conveyor sweepers scurve"),
    52: ("Taffy Twister", "runway coaster pistons islands bumpers climb"),
    53: ("Obsidian Teeth", "runway crushers drop hammers lava banked"),
    54: ("Iceberg Hop", "runway islands ice gaps hammers wave"),
    55: ("Temple of Vines", "runway stairs bridges crushers kicker coaster"),
    56: ("Canyon Cannon", "runway kicker kicker slalom sweepers beam"),
    57: ("Nebula Run", "runway beam lasers islands turntable hills"),
    58: ("Chrome Sunset", "runway split coaster hammers crushers gaps"),
    59: ("Shipwreck Shoals", "runway wave hammers bridges stairs kicker"),
    60: ("Witching Hour", "runway windmills crumble sweepers tower scurve"),
    61: ("Gilded Gauntlet", "runway pistons doors gaps coaster drop"),
    62: ("Rust Belt", "runway crushers conveyor windmills islands hills"),
    63: ("Sky Ferry", "runway bridges bridges kicker spinners banked"),
    64: ("Shard Storm", "runway sweepers stairs lasers coaster crumble"),
    65: ("Northern Lights", "runway tower ice spinners drop zigzag"),
    66: ("Meltdown", "runway lava pistons mud crushers kicker"),
    67: ("Bamboo Rapids", "runway conveyor islands hammers hills crumble"),
    68: ("High Score", "runway wave zigzag turntable doors gaps"),
    69: ("Lightning Ladder", "runway tower windmills lasers stairs coaster"),
    70: ("Sunset Strip", "runway slalom kicker banked bridges drop"),
    71: ("Kraken's Reach", "runway hammers wave islands sweepers climb"),
    72: ("Olympus Mons", "runway climb tower kicker drop crushers"),
    73: ("Knight Run", "runway halfpipe spinners split stairs coaster"),
    74: ("Glitch Garden", "runway crumble wave lasers bumpers islands"),
    75: ("Hyperprism", "runway turntable gaps doors kicker banked"),
    76: ("Night Shift", "runway crushers zigzag sweepers drop hills"),
    77: ("Marshmallow Mayhem", "runway gaps windmills halfpipe crumble scurve"),
    78: ("Hell's Kitchen", "runway sweepers lava kicker pistons coaster"),
    79: ("Whiteout", "runway ice zigzag crushers islands stairs"),
    80: ("Temple Rush", "runway doors climb spinners bridges kicker"),
    81: ("Sandstorm Slalom", "runway slalom mud slalom drop wave"),
    82: ("Event Horizon", "runway drop islands lasers windmills beam"),
    83: ("Vaporwave Valley", "runway hills hammers turntable conveyor kicker"),
    84: ("Riptide", "runway conveyor gaps halfpipe islands banked"),
    85: ("Bone Bridge", "runway bridges hammers stairs lasers crumble"),
    86: ("Golden Ratio", "runway spinners coaster doors tower drop"),
    87: ("Steel Jaws", "runway pistons crushers pistons gaps scurve"),
    88: ("Stratosphere", "runway tower islands drop bridges hills"),
    89: ("Crystal Maze", "runway zigzag doors sweepers turntable kicker"),
    90: ("Frozen Fury", "runway hammers ice windmills gaps coaster"),
    91: ("Radioactive Rally", "runway sweepers lava bumpers tower stairs"),
    92: ("Moonlit Gardens", "runway beam crumble coaster spinners islands"),
    93: ("Bonus Stage", "runway bumpers kicker zigzag lasers wave"),
    94: ("Superstorm", "runway windmills hammers sweepers drop banked"),
    95: ("Last Exit", "runway split lasers crushers kicker hills"),
    96: ("Deep Pressure", "runway crushers turntable stairs bridges coaster"),
    97: ("Dust to Dust", "runway mud islands pistons climb drop"),
    98: ("Royal Gauntlet", "runway hammers doors spinners crushers gaps"),
    99: ("Kernel Panic", "runway lasers crumble windmills sweepers zigzag"),
    100: ("Infinity Run", "runway islands hammers lasers crushers drop coaster"),
}

FILLERS = ["slalom", "turntable", "beam", "bumpers", "wave", "runway"]


def light_attrs(theme, rng, variant):
    L = theme["light"]

    def c3(c):
        return ("Color3", c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    clock = L["clock"] + [0, -1.2, 0.8, -0.5][variant] * (1 if L["clock"] < 17 else -0.3)
    clock = max(6.3, min(17.95, clock))
    tint = L["tint"]
    if variant:
        h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in tint))
        r, g, bl = colorsys.hsv_to_rgb((h + 0.04 * variant) % 1, min(1, s * (1 + 0.15 * variant)), v)
        tint = (int(r * 255), int(g * 255), int(bl * 255))
    return {
        "Lt_Lighting_ClockTime": clock,
        "Lt_Lighting_Ambient": c3(L["ambient"]),
        "Lt_Lighting_OutdoorAmbient": c3(L["outdoor"]),
        "Lt_Lighting_ColorShift_Top": c3(L["shift"]),
        "Lt_Lighting_Brightness": 2.6 + 0.4 * rng.random(),
        "Lt_Lighting_ExposureCompensation": 0.1 + L["bright"],
        "Lt_Lighting_EnvironmentDiffuseScale": 1.0,
        "Lt_Lighting_EnvironmentSpecularScale": 0.45,
        "Lt_Lighting_ShadowSoftness": 0.2,
        "Lt_CC_TintColor": c3(tint),
        "Lt_CC_Saturation": L["sat"],
        "Lt_CC_Contrast": L["contrast"],
        "Lt_CC_Brightness": L["bright"],
        "Lt_Bloom_Intensity": L["bloom"],
        "Lt_Bloom_Size": 24.0,
        "Lt_Bloom_Threshold": 1.2 if L["bloom"] > 0.7 else 1.45,
        "Lt_SunRays_Intensity": 0.06,
        "Lt_SunRays_Spread": 0.5,
        "Lt_Atmosphere_Density": L["density"],
        "Lt_Atmosphere_Color": c3(L["atmo"]),
        "Lt_Atmosphere_Decay": c3(mix(L["atmo"], (0, 0, 0), 0.4)),
        "Lt_Atmosphere_Haze": 0.4,
        "Lt_Atmosphere_Glare": 0.0,
    }


def theme_for(level_id):
    base = dict(THEMES[THEME_ORDER[(level_id - 1) % 25]])
    variant = (level_id - 1) // 25
    if variant:
        # second, third, fourth visit to a world: swap the glow colours around and change the scenery mix
        if variant == 1:
            base["edge"], base["accent"] = base["accent"], base["edge"]
        elif variant == 2:
            h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in base["edge"]))
            r, g, b = colorsys.hsv_to_rgb((h + 0.5) % 1, s, v)
            base["edge"] = (int(r * 255), int(g * 255), int(b * 255))
        elif variant == 3:
            base["accent2"], base["danger"] = base["danger"], base["accent2"]
            base["danger"] = (255, 50, 70)
        dec = list(base["decor"])
        extra = ["spin_rings", "floating_cubes", "pillars", "stars"][variant]
        dec = dec[variant % len(dec):] + dec[:variant % len(dec)]
        if extra not in dec:
            dec = dec[:2] + [extra]
        base["decor"] = dec
    else:
        base["decor"] = list(base["decor"])
    return base, variant


def plan(level_id):
    title, seq = LEVELS[level_id]
    return title, seq.split()


def build_level(fac, unit, level_folder, level_id, length, templates, max_len):
    title, seq = plan(level_id)
    theme, variant = theme_for(level_id)
    rng = random.Random(1000 + level_id * 7919)
    b = LevelBuilder(fac, level_folder, theme, rng, length, templates)
    X1 = X0 + length
    d_base = 0.25 + 0.55 * (level_id - 1) / 99.0
    # the join: wide deck, checkpoint, then narrow to racing width
    b.flat(X0, X0 + 110, Y0, ZC, 144, edge=True)
    b.checkpoint(X0 + 30, Y0, ZC, 144)
    st = St(X0 + 110, Y0, ZC, 144, ZC)
    connect(b, st, 70, w1=60)
    END_RESERVE = 330
    sandbox = rbxl.Inst("Folder")

    def d_now(s):
        return min(1.0, d_base + 0.18 * (s.x - X0) / length)

    def trial(key, s, d):
        """Dry-run a section with the same random stream to learn its exact length and exit height."""
        state = rng.getstate()
        tb = LevelBuilder(fac, sandbox, theme, rng, length, templates)
        ts = St(s.x, s.y, s.z, s.w, ZC)
        SECTIONS[key](tb, ts, d, rng)
        rng.setstate(state)
        sandbox.children.clear()
        return ts.x - s.x, ts.y
    used = []
    i = 0
    fill_i = 0

    def band(key, s):
        """Where the section should start (height) so it stays in the band and heads home late on."""
        _, ya = trial(key, s, d_now(s))
        dy = ya - s.y
        lo, hi = Y0 - 430, Y0 + 340
        want = s.y
        if s.y + dy < lo:
            want = lo - dy + 20
        elif s.y + dy > hi:
            want = hi - dy - 20
        if (s.x - X0) / length > 0.5:  # start heading home
            want = want + (Y0 - (want + dy)) * 0.5
        Lc = max(60, abs(want - s.y) / 0.25) if abs(want - s.y) > 5 else 0
        s2 = St(s.x + Lc, want, s.z, s.w, ZC)
        need, ya2 = trial(key, s2, d_now(s2))
        total = Lc + need + 80
        reserve = 100 + max(END_RESERVE, (abs(ya2 - Y0) + 30) / 0.25, (abs(s.z - ZC) + 60) / 0.6)
        return want, Lc, total, reserve

    while True:
        if i < len(seq):
            key = seq[i]
        else:
            key = None
            for _ in range(len(FILLERS)):
                k = FILLERS[(fill_i + level_id) % len(FILLERS)]
                fill_i += 1
                if k not in used[-2:]:
                    key = k
                    break
        if key is None:
            break
        want, Lc, total, reserve = band(key, st)
        if st.x + total + reserve > X1:
            if i < len(seq):
                i += 1  # skip a long one that will not fit, try the next
                continue
            # fillers: the shortest that still fits
            fits = []
            for k in FILLERS:
                if k in used:
                    continue
                w2, L2, t2, r2 = band(k, st)
                if st.x + t2 + r2 <= X1:
                    fits.append((t2, k))
            if not fits:
                break
            key = min(fits)[1]
            want, Lc, total, reserve = band(key, st)
        if Lc:
            connect(b, st, Lc, y1=want)
        SECTIONS[key](b, st, d_now(st), rng)
        used.append(key)
        i += 1
        # a short breather: a little sideways and up/down drift so the course never reads as a straight line
        zt = st.z + rng.uniform(-32, 32)
        zt = max(ZC - 380, min(ZC + 380, zt))
        yt = st.y + rng.uniform(-18, 18)
        connect(b, st, rng.uniform(65, 80), y1=yt, z1=zt, w1=max(st.w, 44))
    # home stretch: back to the join height and the centre line, then the wide join deck
    rest = X1 - 100 - st.x
    if rest < 60:
        raise RuntimeError("L%03d overran: %.0f" % (level_id, rest))
    b.checkpoint(st.x + 20, st.y, st.z, max(st.w, 60)) if rest > 400 else None
    connect(b, st, rest, y1=Y0, z1=ZC, w1=100)
    b.flat(st.x, X1, Y0, ZC, 160)
    st.x = X1
    # scenery: the world's decor, its set piece, the title gate
    for style in theme["decor"]:
        decor.STYLES[style](b, rng, theme)
    landmarks.landmark(b, theme["key"], variant, rng)
    landmarks.title_gate(b, level_id, title)
    b.kill_sheets()
    # level attributes
    a = rbxl.attrs(level_folder)
    for k in [k for k in a if k.startswith("Lt_")]:
        del a[k]
    a.update(light_attrs(theme, rng, variant))
    a["ObbyLevelTitle"] = title
    a["ObbyLook"] = "nx%03d" % level_id
    rbxl.set_attrs(level_folder, a)
    ua = rbxl.attrs(unit)
    ua["Title"] = title
    rbxl.set_attrs(unit, ua)
    return b, used, title, theme["key"]
