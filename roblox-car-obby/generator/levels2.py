"""100 parkour levels: each with its own palette, a signature stunt, and a unique module sequence."""
import math
import random
import colorsys
import rbxl
from builder import LevelBuilder, X0, ZC, Y0, mix
import parkour as K
from parkour import St, MODULES
import landmarks

FLIGHT = ["pillars", "cube_climb", "cube_drop", "kicker", "windmill", "ring_drop"]
ROT = ["cross", "spin_bridges", "discs", "turntable", "pendulums", "windmill"]
STUNT = ["loop", "double_loop", "barrel", "wallride", "pipe", "corkscrew", "spiral", "halfpipe"]
SKILL = ["beam", "lasers", "checker", "crushers", "slide", "pistons", "doors", "tilt", "zigzag"]
GROUP = {}
for g, ks in (("flight", FLIGHT), ("rot", ROT), ("stunt", STUNT), ("skill", SKILL)):
    for k in ks:
        GROUP.setdefault(k, g)

# signature stunt -> level names (used in order as the signature comes round)
NAMES = {
    "loop": ["Loop Theory", "Full Circle", "Orbit Lane", "Halo Run"],
    "barrel": ["Barrel Roll", "Upside Drive", "Twist Avenue", "Flip Street"],
    "wallride": ["Wall Runner", "Sidewinder", "Vertical Limit", "Edge Walk"],
    "pipe": ["Glass Pipe", "Tube Rider", "Pipeline", "Inside Out"],
    "spiral": ["Spiral Tower", "Helix", "Coil Climb", "Whirlpool"],
    "corkscrew": ["Corkscrew", "Screwdriver", "Rifling", "Thread Needle"],
    "cross": ["Plus Sign", "Compass Spin", "Crossroads", "Turnstile"],
    "spin_bridges": ["Spin Cycle", "Rotor Bridges", "Clock Hands", "Propeller Pass"],
    "pendulums": ["Pendulum Swing", "Sky Swings", "Metronome", "Hanging Gardens"],
    "windmill": ["Windmill Leap", "Blade Runner", "Fan Service", "Turbine Jump"],
    "pillars": ["Pillar Bounce", "Stepping Stars", "Pogo Peaks", "Column Hop"],
    "cube_climb": ["Cube Ascent", "Block Ladder", "Stack Attack", "Sky Stairs"],
    "kicker": ["Big Air", "Launch Day", "Hoop Dreams", "Ramp Rocket"],
    "ring_drop": ["Ring Fall", "Freefall", "Plunge", "Hoop Dive"],
    "double_loop": ["Double Loop", "Figure Eight", "Twin Halo", "Loop Twice"],
    "discs": ["Disc Sweep", "Laser Plates", "Round Robin", "Saucer Hop"],
    "turntable": ["Turntable", "Vinyl Spin", "Holey Wheel", "Lazy Susan"],
    "halfpipe": ["Half Pipe", "Gully Run", "Skate Bowl", "Gutter Ball"],
    "tilt": ["Tilt Shift", "Bank Shot", "Lean In", "Slanted"],
    "zigzag": ["Zig Zag", "Lightning Path", "Switchback", "Staircase Snake"],
    "checker": ["Checkmate", "Crumble Grid", "Floor Falls", "Chessboard"],
    "slide": ["Slide Bridges", "Drawbridge", "Now You See It", "Sliding Doors"],
    "pistons": ["Piston Wave", "Heartbeat", "Equalizer", "Bass Drop"],
    "beam": ["Tightrope", "Laser Limbo", "Balance Beam", "Hop Scotch"],
    "lasers": ["Laser Rhythm", "Strobe", "Light Show", "Pulse"],
    "crushers": ["Crusher Row", "Hammer Time", "Press Pass", "Stamp Mill"],
    "doors": ["Door Dash", "Gap Finder", "Shutter Speed", "Keyhole"],
    "cube_drop": ["Cube Descent", "Down Stairs", "Avalanche Blocks", "Skydive Steps"],
}
SIG_ORDER = ["loop", "pillars", "barrel", "cross", "kicker", "wallride", "spin_bridges", "cube_climb", "pipe",
             "pendulums", "windmill", "corkscrew", "discs", "ring_drop", "spiral", "turntable", "double_loop", "tilt",
             "halfpipe", "checker", "zigzag", "slide", "pistons", "beam", "lasers", "crushers", "doors", "cube_drop"]


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return (int(r * 255), int(g * 255), int(b * 255))


STYLES = ["midnight", "pastel", "glass", "marble", "carbon", "ice", "duotone", "metal", "wood", "chrome"]


def palette(level_id):
    style = STYLES[(level_id - 1) % len(STYLES)]
    h = ((level_id - 1) * 0.61803398875 + 0.07) % 1.0
    p = {"style": style, "danger": (255, 64, 64), "glass": hsv(h, 0.2, 1.0), "boost_speed": 230}
    if style == "midnight":
        p.update(body=hsv(h, 0.5, 0.11), top=hsv(h, 0.35, 0.17), edge=hsv(h, 0.85, 1), pad=hsv(h + 0.5, 0.75, 1),
                 body_mat="SmoothPlastic", top_mat="SmoothPlastic", clock=17.85, bloom=0.8)
    elif style == "pastel":
        p.update(body=hsv(h, 0.32, 0.9), top=hsv(h, 0.07, 0.99), edge=hsv(h, 0.7, 1), pad=hsv(h + 0.4, 0.6, 1),
                 body_mat="SmoothPlastic", top_mat="SmoothPlastic", clock=13.5, bloom=0.3)
    elif style == "glass":
        p.update(body=hsv(h, 0.45, 0.75), top=hsv(h, 0.12, 0.97), edge=hsv(h, 0.4, 1), pad=hsv(h + 0.5, 0.7, 1),
                 body_mat="Glass", top_mat="SmoothPlastic", body_transp=0.35, clock=16.6, bloom=0.5)
    elif style == "marble":
        p.update(body=(222, 218, 210), top=(246, 244, 238), edge=hsv(h, 0.75, 1), pad=hsv(h + 0.5, 0.65, 1),
                 body_mat="Marble", top_mat="Marble", clock=15.5, bloom=0.3)
    elif style == "carbon":
        p.update(body=(26, 26, 30), top=(40, 40, 46), edge=hsv(h, 0.9, 1), pad=hsv(h + 0.15, 0.9, 1),
                 body_mat="Slate", top_mat="SmoothPlastic", clock=17.7, bloom=0.8)
    elif style == "ice":
        p.update(body=(96, 160, 210), top=(214, 236, 250), edge=hsv(h, 0.75, 1), pad=hsv(h + 0.5, 0.7, 1),
                 body_mat="Ice", top_mat="Glacier", clock=11.0, bloom=0.4)
    elif style == "duotone":
        p.update(body=hsv(h, 0.65, 0.55), top=hsv(h + 0.08, 0.3, 0.97), edge=hsv(h + 0.5, 0.75, 1),
                 pad=hsv(h + 0.5, 0.25, 1), body_mat="SmoothPlastic", top_mat="SmoothPlastic", clock=14.5, bloom=0.35)
    elif style == "metal":
        p.update(body=(96, 100, 108), top=(150, 154, 162), edge=hsv(h, 0.9, 1), pad=hsv(h + 0.5, 0.8, 1),
                 body_mat="DiamondPlate", top_mat="Metal", clock=16.2, bloom=0.5)
    elif style == "wood":
        p.update(body=(112, 78, 52), top=(196, 156, 112), edge=hsv(h, 0.6, 1), pad=hsv(h + 0.5, 0.6, 1),
                 body_mat="WoodPlanks", top_mat="Wood", clock=16.9, bloom=0.35)
    else:  # chrome
        p.update(body=(170, 176, 186), top=(214, 219, 228), edge=hsv(h, 0.85, 1), pad=hsv(h + 0.5, 0.8, 1),
                 body_mat="Foil", top_mat="Metal", clock=14.0, bloom=0.4)
    # the shared names the builder and the old helpers expect
    p.update(road=p["top"], road_mat=p["top_mat"], accent=p["pad"], accent2=p["body"], metal=p["body"],
             deco=p["body"], key=style, hue=h)
    return p


def light_attrs(p, rng):
    def c3(c):
        return ("Color3", c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    h = p["hue"]
    dark = p["style"] in ("midnight", "carbon")
    return {
        "Lt_Lighting_ClockTime": p["clock"],
        "Lt_Lighting_Brightness": 2.4 if dark else 3.0,
        "Lt_Lighting_Ambient": c3(hsv(h, 0.25, 0.35 if dark else 0.45)),
        "Lt_Lighting_OutdoorAmbient": c3(hsv(h, 0.2, 0.5 if dark else 0.62)),
        "Lt_Lighting_ColorShift_Top": c3(hsv(h, 0.12, 1.0)),
        "Lt_Lighting_ExposureCompensation": 0.05 if dark else 0.15,
        "Lt_Lighting_EnvironmentDiffuseScale": 1.0,
        "Lt_Lighting_EnvironmentSpecularScale": 0.6,
        "Lt_Lighting_ShadowSoftness": 0.15,
        "Lt_CC_TintColor": c3(hsv(h, 0.06, 1.0)),
        "Lt_CC_Saturation": 0.18,
        "Lt_CC_Contrast": 0.14,
        "Lt_CC_Brightness": 0.0,
        "Lt_Bloom_Intensity": p["bloom"],
        "Lt_Bloom_Size": 22.0,
        "Lt_Bloom_Threshold": 1.25 if dark else 1.5,
        "Lt_SunRays_Intensity": 0.04,
        "Lt_SunRays_Spread": 0.4,
        "Lt_Atmosphere_Density": 0.04,
        "Lt_Atmosphere_Haze": 0.2,
        "Lt_Atmosphere_Glare": 0.0,
        "Lt_Atmosphere_Color": c3(hsv(h, 0.15, 0.95)),
        "Lt_Atmosphere_Decay": c3(hsv(h, 0.3, 0.6)),
    }


def recipe(level_id):
    """The signature twice, and one flight, one rotating and one stunt module around it, all distinct."""
    sig = SIG_ORDER[(level_id - 1) % len(SIG_ORDER)]
    visit = (level_id - 1) // len(SIG_ORDER)
    title = NAMES[sig][visit % len(NAMES[sig])]
    rng = random.Random(77 + level_id * 1013)
    used = {sig}
    picks = []
    for pool, gname in ((FLIGHT, "flight"), (ROT, "rot"), (STUNT, "stunt"), (SKILL, "skill")):
        if GROUP[sig] == gname:
            continue
        k = rng.choice([x for x in pool if x not in used])
        used.add(k)
        picks.append(k)
    extra = rng.choice([x for x in FLIGHT + ROT + STUNT + SKILL if x not in used])
    used.add(extra)
    picks.append(extra)
    rng.shuffle(picks)
    seq = [picks[0], sig] + picks[1:3] + [sig] + picks[3:]
    return title, sig, seq


def build_level(fac, unit, level_folder, level_id, length, templates):
    title, sig, seq = recipe(level_id)
    pal = palette(level_id)
    rng = random.Random(5000 + level_id * 7919)
    b = LevelBuilder(fac, level_folder, pal, rng, length, templates)
    X1 = X0 + length
    d_base = 0.25 + 0.55 * (level_id - 1) / 99.0
    # the join: a wide clean start deck with the title sign
    K.block(b, (X0 + 55, Y0, ZC), 110, 144, h=14)
    b.checkpoint(X0 + 30, Y0, ZC, 144)
    b.line(X0, Y0, ZC)
    st = St(X0 + 110, Y0, ZC, 60, ZC)
    sandbox = rbxl.Inst("Folder")

    def d_now(s):
        return min(1.0, d_base + 0.18 * (s.x - X0) / length)

    def trial(key, s):
        state = rng.getstate()
        tb = LevelBuilder(fac, sandbox, pal, rng, length, templates)
        ts = St(s.x, s.y, s.z, s.w, ZC)
        MODULES[key](tb, ts, d_now(s), rng)
        rng.setstate(state)
        sandbox.children.clear()
        return ts

    def reserve(s):
        # the finale hops: one per ~200 studs, each can change height ~70 and side ~120
        return 110 + 200 + max(200 * (abs(s.y - Y0) / 70.0), 200 * abs(s.z - ZC) / 120.0)

    used = []
    queue = list(seq)
    fill = [k for k in SKILL + ROT if k not in seq]
    rng.shuffle(fill)
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
                if t.x + 40 + reserve(t) <= X1:
                    key = k
                    fill.remove(k)
                    break
        if key is None:
            break
        MODULES[key](b, st, d_now(st), rng)
        used.append(key)
        # hop to the next module, up or down a level
        dy = rng.choice([-1, 1]) * rng.uniform(25, 70)
        if st.y + dy > b.yhi or st.y + dy < b.ylo:
            dy = -dy
        if (st.x - X0) / length > 0.55:
            dy = max(-70, min(70, (Y0 - st.y) * 0.4))
        K.link(b, st, rng, dy)
    # home: pillar hops back to the join height and centre line, landing on the wide join deck
    if X1 - 110 - st.x < 60:
        raise RuntimeError("L%03d overran by %.0f" % (level_id, st.x - (X1 - 110)))
    K.finale(b, st, rng, X1 - 110 + 30, Y0, ZC)
    K.block(b, (X1 - 55, Y0, ZC), 110, 160, h=14)
    b.line(X1, Y0, ZC)
    landmarks.title_gate(b, level_id, title)
    b.kill_sheets()
    a = rbxl.attrs(level_folder)
    for k in [k for k in a if k.startswith("Lt_")]:
        del a[k]
    a.update(light_attrs(pal, rng))
    a["ObbyLevelTitle"] = title
    a["ObbyLook"] = "pk%03d" % level_id
    rbxl.set_attrs(level_folder, a)
    ua = rbxl.attrs(unit)
    ua["Title"] = title
    rbxl.set_attrs(unit, ua)
    return b, used, title, pal["style"]
