"""Removes z-fighting: visible faces of different parts that lie in the same plane and overlap.

For every such pair one face has to win. The winner is the decoration over the structure (a non-colliding part over a
colliding one), otherwise the smaller face. The winning face is pushed out of the plane by extending its part, so the
opposite face of that part stays where it was and nothing slides sideways.
"""
import math
from collections import defaultdict
from geom import CF
from factory import is_basepart

GAP = 0.15        # how far apart two parallel faces must be to render cleanly
NEAR = 0.12       # faces closer than this are fighting
PLAIN = {256, 272, 288}  # untextured materials: identical colours there cannot flicker


def _faces(p):
    """(normal, centre, u, v, hu, hv, axis, sign) for each flat face of a block or the caps of a cylinder."""
    cf = CF.from_prop(p.get("CFrame"))
    sx, sy, sz = p.get("size")
    cols = (cf.x, cf.y, cf.z)
    half = (sx / 2, sy / 2, sz / 2)
    shape = p.get("shape", 1) if p.cls == "Part" else 1
    out = []
    if shape == 0:
        return out
    axes = (0,) if shape == 2 else (0, 1, 2)
    for k in axes:
        for s in (-1, 1):
            n = tuple(s * c for c in cols[k])
            c = tuple(cf.p[i] + n[i] * half[k] for i in range(3))
            a, b2 = [j for j in range(3) if j != k]
            if shape == 2:
                r = min(sy, sz) / 2 * 0.886  # a cap as the square of the same area
                out.append((n, c, cols[1], cols[2], r, r, k, s))
            else:
                out.append((n, c, cols[a], cols[b2], half[a], half[b2], k, s))
    return out


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _overlap(f, g, sliver=0.1):
    """Do two coplanar rectangles overlap by more than a sliver? (separating axes)"""
    d = tuple(g[1][i] - f[1][i] for i in range(3))
    for ax in (f[2], f[3], g[2], g[3]):
        ra = f[4] * abs(_dot(f[2], ax)) + f[5] * abs(_dot(f[3], ax))
        rb = g[4] * abs(_dot(g[2], ax)) + g[5] * abs(_dot(g[3], ax))
        if abs(_dot(d, ax)) >= ra + rb - sliver:
            return False
    return True


def _candidates(root):
    out = []
    for d in root.descendants():
        if not is_basepart(d) or d.cls not in ("Part",):
            continue
        if d.get("Transparency", 0.0) >= 0.99:
            continue
        if any(c.cls == "SpecialMesh" for c in d.children):
            continue  # an ellipsoid: its box faces are not drawn
        out.append(d)
    return out


def conflicts(root, sliver=0.1):
    parts = _candidates(root)
    buckets = defaultdict(list)
    for p in parts:
        for f in _faces(p):
            n = f[0]
            key = (round(n[0], 2), round(n[1], 2), round(n[2], 2))
            off = _dot(n, f[1])
            buckets[key].append((off, p, f))
    found = []
    for key, items in buckets.items():
        items.sort(key=lambda t: t[0])
        for i in range(len(items)):
            oi, pi, fi = items[i]
            j = i + 1
            while j < len(items) and items[j][0] - oi < NEAR:
                oj, pj, fj = items[j]
                j += 1
                if pj is pi:
                    continue
                if _dot(fi[0], fj[0]) < 0.9999:
                    continue
                if (pi.get("Material") in PLAIN and pj.get("Material") in PLAIN
                        and pi.get("Color3uint8") == pj.get("Color3uint8")):
                    continue
                if _overlap(fi, fj, sliver):
                    found.append(((oi, pi, fi), (oj, pj, fj)))
    return found


def _area(f):
    return f[4] * f[5]


def _extend(p, f, delta):
    """Push face f of part p outward by delta (grow the part along that axis, keep the opposite face)."""
    k, s = f[6], f[7]
    size = list(p.get("size"))
    size[k] += delta
    p.set("size", tuple(float(v) for v in size))
    cf = CF.from_prop(p.get("CFrame"))
    shift = tuple(f[0][i] * delta / 2 for i in range(3))
    p.set("CFrame", CF(tuple(cf.p[i] + shift[i] for i in range(3)), cf.x, cf.y, cf.z).to_prop())


def fix(root, passes=60):
    """Resolve every fight. Returns (fights found at the start, fights left)."""
    first = None
    for _ in range(passes):
        found = conflicts(root, 0.02)
        if first is None:
            first = len(found)
        if not found:
            return first, 0
        need = {}
        for (oa, pa, fa), (ob, pb, fb) in found:
            ca, cb = bool(pa.get("CanCollide")), bool(pb.get("CanCollide"))
            if ca != cb:
                front = (ob, pb, fb) if ca else (oa, pa, fa)
                back = (oa, pa, fa) if ca else (ob, pb, fb)
            else:
                front, back = ((oa, pa, fa), (ob, pb, fb)) if _area(fa) <= _area(fb) else ((ob, pb, fb), (oa, pa, fa))
            delta = GAP - (front[0] - back[0])
            if delta <= 0:
                continue
            key = (id(front[1]), front[2][6], front[2][7])
            if key not in need or need[key][2] < delta:
                need[key] = (front[1], front[2], delta)
        for p, f, delta in need.values():
            _extend(p, f, delta)
    return first, len(conflicts(root, 0.02))
