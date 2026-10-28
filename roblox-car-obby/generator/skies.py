"""Paints the ten showcase skyboxes as six cube faces each (bk, dn, ft, lf, rt, up).

Each face is painted with its own clouds, nebula and stars, and only the last few degrees at every face border fade into
the sky's average colour at that height. So every border depends on height alone and matches every other border:
whichever way Roblox orders, rotates or mirrors the faces, no seam shows. (The arcade grid is a real plane under the
camera, so it lines up across faces by itself.)

usage: python3 skies.py <outdir> [size] [ids...]
"""
import sys
import os
import math
import numpy as np
from PIL import Image

FACES = {  # name: (forward, right, up) for a camera inside the cube
    "ft": ((0, 0, -1), (1, 0, 0), (0, 1, 0)),
    "bk": ((0, 0, 1), (-1, 0, 0), (0, 1, 0)),
    "rt": ((1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "lf": ((-1, 0, 0), (0, 0, -1), (0, 1, 0)),
    "up": ((0, 1, 0), (1, 0, 0), (0, 0, 1)),
    "dn": ((0, -1, 0), (1, 0, 0), (0, 0, -1)),
}


def directions(n):
    out = {}
    s = (np.arange(n) + 0.5) / n * 2 - 1
    u, v = np.meshgrid(s, -s)
    for name, (f, r, up) in FACES.items():
        f, r, up = (np.array(a, dtype=np.float64) for a in (f, r, up))
        d = f[None, None, :] + u[..., None] * r[None, None, :] + v[..., None] * up[None, None, :]
        d /= np.linalg.norm(d, axis=-1, keepdims=True)
        out[name] = d
    return out


# ------------------------------------------------------------------ noise
def _hash(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(p, seed=0):
    """3D value noise, p[..., 3]."""
    i = np.floor(p).astype(np.int64)
    f = p - i
    f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * (f[..., 2] if dz else 1 - f[..., 2])
                out = out + w * _hash(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, seed)
    return out


def fbm(p, octaves=5, seed=0, lac=2.03, gain=0.5):
    a, s, norm = 0.5, 0.0, 0.0
    for k in range(octaves):
        s = s + a * vnoise(p, seed + k * 17)
        norm += a
        p = p * lac
        a *= gain
    return s / norm


def fold(d):
    """Fold a direction into 0 <= z <= x (one eighth of the horizon): the cube's symmetry."""
    x, y, z = np.abs(d[..., 0]), d[..., 1], np.abs(d[..., 2])
    hi, lo = np.maximum(x, z), np.minimum(x, z)
    return np.stack([hi, y, lo], -1)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def ramp(e, stops):
    """Colour by elevation (degrees) through (elev, '#rrggbb') stops."""
    out = np.zeros(e.shape + (3,))
    es = [s[0] for s in stops]
    cs = [hexc(s[1]) for s in stops]
    out[:] = cs[0]
    for (e0, c0), (e1, c1) in zip(zip(es, cs), zip(es[1:], cs[1:])):
        t = smooth(e0, e1, e)
        m = e >= e0
        out = np.where(m[..., None], c0 * (1 - t[..., None]) + c1 * t[..., None], out)
    return out


def mix(a, b, t):
    t = np.asarray(t)[..., None] if np.ndim(t) else t
    return a * (1 - t) + b * t


# ------------------------------------------------------------------ building blocks (unfolded directions)
def elev(d):
    return np.degrees(np.arcsin(np.clip(d[..., 1], -1, 1)))


_W = None  # the face-border weight of the directions being painted (1 inside a face, 0 on its border)


def edge():
    return 1.0 if _W is None else _W


def field(fn, d):
    """A noise field fn(direction) that, near any face border, turns into its own mirror image across that border
    (the cube-symmetric version), so the border looks the same whichever way the faces are put together."""
    if _W is None:
        return fn(d)
    return fn(d) * _W + fn(fold(d)) * (1 - _W)


def clouds(d, e, lo, hi, scale, cover, seed, flat=3.0, soft=0.18, warp=0.6):
    """Cloud density in an elevation band; `flat` squashes the noise into horizontal streaks. Clouds thin out to nothing
    toward a face border, so every border is clear sky."""
    def noise(dd):
        q = np.stack([dd[..., 0] * scale, dd[..., 1] * scale * flat, dd[..., 2] * scale], -1)
        w = fbm(q * 0.5 + 11.3, 3, seed + 5)
        return fbm(q + warp * w[..., None], 5, seed)
    n = field(noise, d)
    band = smooth(lo, lo + (hi - lo) * 0.3, e) * (1 - smooth(hi - (hi - lo) * 0.3, hi, e))
    return np.clip((n - (1 - cover)) / soft, 0, 1) * band


def sea(d, scale, cover, seed, soft=0.2):
    """A cloud sea under the horizon (on a plane below the camera)."""
    cover = cover * (0.6 + 0.4 * edge())  # thinner toward the borders, where it turns mirror-symmetric
    y = np.minimum(d[..., 1], -1e-3)
    r = np.sqrt(d[..., 0] ** 2 + d[..., 2] ** 2) / -y

    def noise(dd):
        yy = np.minimum(dd[..., 1], -1e-3)
        p = np.stack([dd[..., 0] / -yy * scale, dd[..., 2] / -yy * scale, np.full_like(yy, seed * 0.1)], -1)
        w = fbm(p * 0.4, 3, seed + 9)
        return fbm(p + 0.8 * w[..., None], 5, seed)
    n = field(noise, d)
    fade = 1 - smooth(4.0, 14.0, r)
    return np.clip((n - (1 - cover)) / soft, 0, 1) * fade * (d[..., 1] < 0)


def stars(d, density, seed, size=1.0, tint=None):
    """Point stars on a fine grid of directions."""
    g = 260.0 / size
    q = np.floor(d * g)
    qi = q.astype(np.int64)
    h = _hash(qi[..., 0], qi[..., 1], qi[..., 2], seed)
    fr = d * g - q - 0.5
    dist = np.sqrt((fr ** 2).sum(-1))
    lit_ = (h > 1 - density) * np.clip(1 - dist / 0.32, 0, 1) ** 1.5
    bright = _hash(qi[..., 0] + 7, qi[..., 1], qi[..., 2], seed) ** 3
    a = np.abs(d)
    border = 1 - (np.sort(a, -1)[..., :2] / a.max(-1)[..., None]).max(-1)
    v = lit_ * (0.35 + 1.4 * bright) * smooth(0.012, 0.03, border)  # no star sits across a face edge
    col = np.ones(d.shape)
    if tint is not None:
        k = _hash(qi[..., 0], qi[..., 1] + 3, qi[..., 2], seed)
        col = mix(np.ones(d.shape), np.array(tint), (k > 0.6) * 0.6)
    return v[..., None] * col


def lit(c, k):
    return mix(c * 0, c, k)


# ------------------------------------------------------------------ the ten skies: fn(d, e) -> (colour, seam-safe extra or None)
def sky_candy(d, e):
    c = ramp(e, [(-90, "#d9a6e6"), (-25, "#f2bde3"), (-3, "#ffd3e6"), (3, "#ffd6ea"), (14, "#f3cdf6"), (40, "#c4c8ff"),
                 (90, "#9ab8ff")])
    c = c + hexc("#fff0f6") * 0.12 * np.exp(-(e / 4.0) ** 2)[..., None]
    cl = clouds(d, e, 1, 34, 3.0, 0.5, 3, flat=2.2, soft=0.1)
    top = smooth(1, 34, e)
    ccol = mix(hexc("#ff9fcb"), hexc("#fff3fa"), np.clip(cl * 1.2, 0, 1) * 0.6 + top * 0.4)
    c = mix(c, ccol, cl * 0.95)
    cl2 = clouds(d, e, 8, 30, 2.4, 0.42, 4, flat=2.0, soft=0.1)
    c = mix(c, mix(hexc("#a9d8ff"), hexc("#e8f6ff"), cl2), cl2 * 0.7)
    sc = sea(d, 0.6, 0.6, 5, soft=0.12)
    c = mix(c, mix(hexc("#ffb8da"), hexc("#fff2f8"), sc), sc * 0.95)
    c = c + stars(d, 0.004, 11, 1.4, (1.0, 0.8, 0.95)) * 0.5 * (e > 10)[..., None]
    return c, None


def sky_diner(d, e):
    c = ramp(e, [(-90, "#86a7c9"), (-10, "#b9cfe4"), (0, "#f7e7cf"), (8, "#cfe3f6"), (35, "#6aa6ec"), (90, "#2f72d8")])
    cl = clouds(d, e, 2, 38, 3.2, 0.5, 21, flat=1.6, soft=0.1)
    c = mix(c, mix(hexc("#c9d6e8"), hexc("#ffffff"), np.clip(cl * 1.5, 0, 1)), cl * 0.97)
    sc = sea(d, 0.5, 0.52, 23, soft=0.12)
    c = mix(c, mix(hexc("#d9e4f2"), hexc("#ffffff"), sc), sc * 0.9)
    return c, None


def sky_spores(d, e):
    c = ramp(e, [(-90, "#14102e"), (-15, "#2c1d4f"), (-2, "#7a3a6e"), (2, "#ff8a6a"), (8, "#e0628a"), (22, "#7b3d9e"),
                 (50, "#2a1d66"), (90, "#120f3a")])
    c = c + hexc("#ff9a70") * 0.35 * np.exp(-((e - 3) / 6.0) ** 2)[..., None]
    cl = clouds(d, e, 3, 28, 2.6, 0.45, 31, flat=3.5, soft=0.2)
    c = mix(c, mix(hexc("#ff9f8a"), hexc("#6b3f9a"), smooth(3, 28, e)), cl * 0.75)
    c = c + stars(d, 0.02, 33, 1.0) * smooth(20, 60, e)[..., None] * 0.9
    c = c + stars(d, 0.006, 35, 2.2, (0.5, 1.0, 0.8)) * np.array([0.55, 1.0, 0.85]) * 0.8 * (e > -20)[..., None]
    return c, None


def sky_chess(d, e):
    c = ramp(e, [(-90, "#8d8aa0"), (-8, "#c4b8ad"), (0, "#f6d39a"), (6, "#f6dcb4"), (25, "#a3b5d6"), (90, "#4766b0")])
    c = c + hexc("#ffcf80") * 0.2 * np.exp(-((e - 2) / 7.0) ** 2)[..., None]
    cl = clouds(d, e, 5, 55, 2.2, 0.45, 41, flat=7.0, soft=0.3, warp=1.2)  # long cirrus streaks
    c = mix(c, mix(hexc("#ffd8a8"), hexc("#fff6ea"), smooth(5, 55, e)), cl * 0.7)
    return c, None


def sky_clock(d, e):
    c = ramp(e, [(-90, "#4a4038"), (-10, "#8a6a4a"), (0, "#f4b46a"), (7, "#e8a868"), (28, "#6e8798"), (90, "#2f4f66")])
    c = c + hexc("#ffb060") * 0.35 * np.exp(-((e - 1) / 6.0) ** 2)[..., None]
    smoke = clouds(d, e, -4, 16, 3.0, 0.55, 51, flat=2.0, soft=0.35)
    c = mix(c, hexc("#b08060"), smoke * 0.45)
    cl = clouds(d, e, 10, 55, 2.4, 0.45, 53, flat=5.0, soft=0.2)
    c = mix(c, mix(hexc("#f0b070"), hexc("#e2d2bc"), smooth(10, 55, e)), cl * 0.7)
    return c, None


def sky_toys(d, e):
    c = ramp(e, [(-90, "#9fc8ff"), (-6, "#d6ecff"), (1, "#e6f6ff"), (12, "#9fd2ff"), (45, "#3f96ff"), (90, "#1c6cf0")])
    cl = clouds(d, e, 3, 38, 3.6, 0.47, 61, flat=1.4, soft=0.04)  # crisp cartoon puffs
    shade = smooth(-0.2, 0.6, fbm(d * 9.0, 3, 62) - 0.2 + smooth(3, 38, e) * 0.4)
    c = mix(c, mix(hexc("#cfe0fb"), hexc("#ffffff"), shade), cl)
    sc = sea(d, 0.55, 0.55, 63, soft=0.04)
    c = mix(c, hexc("#ffffff"), sc * 0.97)
    return c, None


def sky_space(d, e):
    c = ramp(e, [(-90, "#020309"), (90, "#03040c")])
    def warped(dd):
        return dd * 2.4 + 0.9 * fbm(dd * 1.4 + 2.0, 4, 70)[..., None]
    n1 = field(lambda dd: fbm(warped(dd) + 3.1, 6, 71), d)
    n2 = field(lambda dd: fbm(warped(dd) * 1.6 + 8.3, 6, 73), d)
    neb = np.clip((n1 - 0.46) * 2.4, 0, 1) ** 1.5
    neb2 = np.clip((n2 - 0.5) * 2.6, 0, 1) ** 1.7
    c = c + hexc("#7a2fe8") * 0.6 * neb[..., None] + hexc("#20c8e0") * 0.45 * neb2[..., None]
    c = c + hexc("#ff4fb0") * 0.5 * (neb * neb2)[..., None]
    galaxy = field(lambda dd: np.exp(-((dd[..., 0] * 0.5 + dd[..., 1] * 0.8 - dd[..., 2] * 0.3) / 0.22) ** 2)
                   * fbm(dd * 7.0, 5, 75), d)
    c = c + hexc("#d9d0ff") * 0.35 * galaxy[..., None]
    c = c + stars(d, 0.07, 77, 0.8, (0.7, 0.85, 1.0)) * 1.1
    c = c + stars(d, 0.012, 79, 1.7, (1.0, 0.85, 0.7)) * 1.3
    return c, None


def sky_volcano(d, e):
    c = ramp(e, [(-90, "#2a0a06"), (-20, "#5a160a"), (-2, "#c8381a"), (2, "#ff6a28"), (10, "#a8322a"), (30, "#4a1a20"),
                 (90, "#1c0c12")])
    c = c + hexc("#ff5a1e") * 0.55 * np.exp(-(e / 7.0) ** 2)[..., None]
    ash = clouds(d, e, 1, 65, 2.6, 0.58, 81, flat=2.0, soft=0.3, warp=1.0)
    under = 1 - smooth(1, 40, e)
    c = mix(c, mix(hexc("#2a1416"), hexc("#b8482a"), under), ash * 0.85)
    below = sea(d, 0.5, 0.7, 83, soft=0.35)
    c = mix(c, hexc("#ff7a2a"), below * 0.35)
    c = c + stars(d, 0.008, 85, 1.3, (1.0, 0.5, 0.2)) * np.array([1.0, 0.55, 0.2]) * 1.2
    return c, None


def sky_ice(d, e):
    c = ramp(e, [(-90, "#b8d8f0"), (-6, "#dff1fb"), (1, "#f2fbff"), (10, "#bfe3fa"), (40, "#5aa2e6"), (90, "#2f6fc8")])
    cl = clouds(d, e, 4, 60, 2.0, 0.42, 95, flat=8.0, soft=0.28, warp=1.4)  # icy cirrus
    c = mix(c, hexc("#ffffff"), cl * 0.75)
    sc = sea(d, 0.45, 0.6, 97, soft=0.18)
    c = mix(c, hexc("#ffffff"), sc * 0.85)
    c = c + stars(d, 0.006, 99, 1.2, (0.7, 0.95, 1.0)) * 0.45 * (e > 0)[..., None]  # diamond dust
    return c, None


def sky_arcade(d, e):
    c = ramp(e, [(-90, "#0a0418"), (-3, "#2a0a3a"), (0, "#ff3aa8"), (3, "#ff7a3a"), (8, "#c0307a"), (25, "#3a0a5a"),
                 (90, "#0c0420")])
    c = c + hexc("#ff4fc0") * 0.45 * np.exp(-((e - 1) / 5.0) ** 2)[..., None]
    c = c + stars(d, 0.03, 101, 1.0, (1.0, 0.6, 1.0)) * smooth(6, 30, e)[..., None]
    cl = clouds(d, e, 3, 22, 2.6, 0.4, 103, flat=6.0, soft=0.2)
    c = mix(c, hexc("#ff6ab0"), cl * 0.35)
    # the neon grid floor: a real plane, so it lines up across every face by itself
    y = np.minimum(d[..., 1], -1e-3)
    px, pz = d[..., 0] / -y, d[..., 2] / -y
    gx = np.abs(px * 1.5 - np.round(px * 1.5))
    gz = np.abs(pz * 1.5 - np.round(pz * 1.5))
    w = 0.02 + 0.004 / (-y)
    line = np.clip(1 - np.minimum(gx, gz) / w, 0, 1) * (d[..., 1] < 0) * (1 - smooth(-2, -0.5, e))
    grid = hexc("#ff3ad8") * 0.9 * (line * np.clip(1 - np.sqrt(px * px + pz * pz) / 40, 0, 1))[..., None]
    return c, grid


def edge_weight(d, width=0.14):
    """1 inside a cube face, 0 on its border (faded over `width` of the half-face)."""
    a = np.abs(d)
    m = a.max(-1)
    u = np.sort(a, -1)[..., :2] / m[..., None]  # the two minor coordinates on the major face
    return smooth(0.0, width, 1 - u.max(-1))


def mean_by_elevation(fn, rows=360, cols=240):
    """The sky's average colour at each elevation (what a face border fades to)."""
    lat = np.radians(np.linspace(-90, 90, rows))
    lon = np.linspace(0, 2 * np.pi, cols, endpoint=False)
    LA, LO = np.meshgrid(lat, lon, indexing="ij")
    d = np.stack([np.cos(LA) * np.cos(LO), np.sin(LA), np.cos(LA) * np.sin(LO)], -1)
    c, _ = fn(d, elev(d))
    return np.degrees(lat), c.mean(1)


def evaluate(fn, d, table=None):
    global _W
    _W = edge_weight(d, 0.3)
    try:
        c, safe = fn(d, elev(d))
    finally:
        _W = None
    return c if safe is None else c + safe


SKIES = {1: ("sugar_rush", sky_candy), 2: ("drive_thru", sky_diner), 3: ("spore_springs", sky_spores),
         4: ("checkmate", sky_chess), 5: ("tick_tock", sky_clock), 6: ("toy_box", sky_toys), 7: ("orbit", sky_space),
         8: ("eruption", sky_volcano), 9: ("frostbite", sky_ice), 10: ("high_score", sky_arcade)}


def render(lid, outdir, n):
    name, fn = SKIES[lid]
    folder = os.path.join(outdir, "L%02d_%s" % (lid, name))
    os.makedirs(folder, exist_ok=True)
    for face, d in directions(n).items():
        c = evaluate(fn, d)
        c = c + (np.random.default_rng(lid * 7 + len(face)).random(c.shape) - 0.5) / 255.0  # dither: no banding
        Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8)).save(os.path.join(folder, "%s.png" % face), optimize=True)
    return folder


if __name__ == "__main__":
    out = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    ids = [int(a) for a in sys.argv[3:]] or list(SKIES)
    for lid in ids:
        render(lid, out, n)
        print("sky", lid, SKIES[lid][0])
