"""Clipping audit of built levels: what moves through what, and what pokes up through the road.

usage: python3 -I audit.py <tools dir> <place.rbxl|.pkl> <level ids...>

1. moving vs static: every ObbyPropAnim rig (Hinge/Spin/Slide, nested) and clock rotor is swept through its motion
   (the game's own maths); any visible part of it that comes to overlap a static solid part it did not overlap at rest
   is reported (a hammer swinging through a post, a deck sliding through a housing).
2. through the road: static visible parts that stick up through a road surface (a pylon through the road above).
3. ghosts: big visible parts in a moving rig that neither collide nor carry a hazard (the car passes through them).
"""
import sys
sys.path.insert(0, sys.argv[1])
import math
import collections
import threading
import numpy as np
import rbxl
from geom import CF
from factory import is_basepart, MAT

sys.setrecursionlimit(1000000)
threading.stack_size(512 * 1024 * 1024)

ROAD = ("Deck", "Platform", "Ramp", "MovingDeck", "Floor", "SinkTile", "RetractDeck")
ROAD_KIT = ("NeonEdge", "EdgeLine", "RoadSide", "Belly", "LaneDash", "Rail", "RailCap", "HazardEdge", "SteelBelly", "Truss",
            "Pylon", "Bolt", "Chevron", "Strip", "Boost", "Glow", "Dash", "Edge", "Line", "Lip", "Mark", "Flag", "Checkpoint",
            "Trim", "Tile", "Belly", "Pad", "Arrow", "Target", "Finish", "Kerb", "Slab", "Mitre", "Seam", "Cap", "Grid")
TAU = math.pi * 2


def mat_of(cf):
    return np.array([[cf.x[0], cf.y[0], cf.z[0]], [cf.x[1], cf.y[1], cf.z[1]], [cf.x[2], cf.y[2], cf.z[2]]], float)


class Box:
    __slots__ = ("p", "R", "h", "name", "inst")

    def __init__(self, p, R, h, name, inst=None):
        self.p, self.R, self.h, self.name, self.inst = np.asarray(p, float), R, np.asarray(h, float), name, inst


def obb_overlap(a, b, margin=0.25):
    """Separating-axis test for two oriented boxes (shrunk by margin: touching is not overlapping)."""
    ha, hb = np.maximum(a.h - margin, 0.01), np.maximum(b.h - margin, 0.01)
    Ra, Rb = a.R, b.R
    t = b.p - a.p
    C = Ra.T @ Rb
    AC = np.abs(C) + 1e-6
    tA = Ra.T @ t
    for i in range(3):
        if abs(tA[i]) > ha[i] + (AC[i] @ hb):
            return False
    tB = Rb.T @ t
    for j in range(3):
        if abs(tB[j]) > hb[j] + (AC[:, j] @ ha):
            return False
    for i in range(3):
        for j in range(3):
            i1, i2 = (i + 1) % 3, (i + 2) % 3
            j1, j2 = (j + 1) % 3, (j + 2) % 3
            ra = ha[i1] * AC[i2, j] + ha[i2] * AC[i1, j]
            rb = hb[j1] * AC[i, j2] + hb[j2] * AC[i, j1]
            if abs(tA[i2] * C[i1, j] - tA[i1] * C[i2, j]) > ra + rb:
                return False
    return True


def ext(bx):
    return np.abs(bx.R) @ bx.h


def keys_of(s):
    if not isinstance(s, (str, bytes)):
        return None
    if isinstance(s, bytes):
        s = s.decode()
    import re
    ks = [(float(a), float(b)) for a, b in re.findall(r"([\d.]+):([\d.\-]+)", s)]
    return ks or None


def curve_values(rig):
    """The rig's 0..1 (or -1..1) values over a cycle, sampled."""
    ks = rig["keys"]
    if not ks:
        return [0.5 - 0.5 * math.cos(u * TAU) for u in np.linspace(0, 1, 13)]
    vals = set(v for _, v in ks)
    lo, hi = min(vals), max(vals)
    return list(np.linspace(lo, hi, 9))


def motion(rig, v):
    """The rig's own transform (a 4x4) at curve value v (Spin: v is the fraction of a turn)."""
    P = rig["pivot"]
    Rp = mat_of(P)
    pp = np.array(P.p)
    if rig["kind"] == "Slide":
        M = np.eye(3)
        d = Rp[:, 0] * rig["amount"] * v
        return M, d
    ang = TAU * v if rig["kind"] == "Spin" else math.radians(rig["amount"] * v)
    c, s = math.cos(ang), math.sin(ang)
    Rl = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    M = Rp @ Rl @ Rp.T
    return M, pp - M @ pp


def rig_states(chain):
    """Transforms (M, d) for the chain (outer rig first) over its motion: a grid of sampled values."""
    states = [(np.eye(3), np.zeros(3))]
    for rig in chain:
        if not rig["amount"]:
            continue  # (a rig stopped by clear_sweeps)
        vs = list(np.linspace(0, 1, 17))[:-1] if rig["kind"] == "Spin" else curve_values(rig)
        new = []
        for M0, d0 in states:
            for v in vs:
                M1, d1 = motion(rig, v)
                new.append((M0 @ M1, M0 @ d1 + d0))
        states = new if len(new) <= 300 else new[:: max(1, len(new) // 300)]
    return states


CLASH, ROOTS, PARTS, HIT = set(), {}, [], []


def audit_level(lvl, lid, only_roots=None):
    parts = PARTS
    parts.clear()
    for d in lvl.descendants():
        if not is_basepart(d):
            continue
        cf = CF.from_prop(d.get("CFrame"))
        sz = d.get("size")
        a = rbxl.attrs(d) or {}
        # where it hangs: the chain of rigs, a clock rotor, a sand board, a brick wall
        chain, rotor, other, root = [], None, False, None
        node = d.parent
        while node is not None and node is not lvl:
            na = rbxl.attrs(node) or {}
            if node.cls == "Model" and na.get("ObbyProp"):
                root = node
            if node.cls == "Model" and "PropMotion" in na:
                pv = node.find("Pivot")
                if pv is not None:
                    chain.insert(0, {"kind": na["PropMotion"], "amount": float(na.get("PropAmount", 0)),
                                     "keys": keys_of(na.get("PropKeys")), "pivot": CF.from_prop(pv.get("CFrame")),
                                     "id": id(node), "name": node.name, "node": node})
            if node.cls == "Model" and "ClockRotor" in na:
                rotor = na
            if node.cls == "Model" and any(k in na for k in ("ClockSand", "ArcadeM")):
                other = True
            node = node.parent
        tr = d.get("Transparency", 0.0)
        h = np.array(sz, float) / 2
        shape = d.get("shape", 1)
        if shape == 2:  # a cylinder (axis along X): its box's corners reach past it; use a box of about its size
            h[1] *= 0.86
            h[2] *= 0.86
        elif shape == 0:
            h *= 0.8
        mesh = d.cls == "MeshPart" or any(c.cls == "SpecialMesh" for c in d.children)
        parts.append(dict(box=Box(cf.p, mat_of(cf), h, d.name, d), mesh=mesh, collide=bool(d.get("CanCollide")),
                          hazard="ObbyHazard" in a, vis=tr < 0.5 and d.name != "Pivot", chain=chain, rotor=rotor,
                          other=other, neon=d.get("Material") == MAT["Neon"], size=sz, root=root,
                          kind=a.get("ObbyHazard")))
    static = [p for p in parts if not p["chain"] and not p["rotor"] and not p["other"] and p["collide"] and p["vis"]]
    sp = np.array([p["box"].p for p in static]) if static else np.zeros((0, 3))
    se = np.array([ext(p["box"]) for p in static]) if static else np.zeros((0, 3))
    hits = collections.Counter()
    where = {}
    # 1. moving rigs swept through their motion
    by_chain = collections.defaultdict(list)
    for p in parts:
        if p["chain"] and p["vis"] and min(p["size"]) >= 0.8:
            if only_roots is not None and id(p["root"]) not in only_roots:
                continue
            by_chain[tuple(r["id"] for r in p["chain"])].append(p)
    for key, ps in by_chain.items():
        chain = ps[0]["chain"]
        states = rig_states(chain)
        for p in ps:
            b0 = p["box"]
            if len(chain) == 1 and chain[0]["kind"] == "Spin" and b0.inst.get("shape", 1) == 2:
                ax = chain[0]["pivot"]
                ax = np.array(ax.x, float)
                if abs(float(b0.R[:, 0] @ ax)) > 0.999 and np.linalg.norm(np.cross(b0.p - np.array(chain[0]["pivot"].p), ax)) < 1.0:
                    continue
            # what it already overlaps at rest (joints, housings by design)
            lo, hi = b0.p - ext(b0) - 1, b0.p + ext(b0) + 1
            near0 = np.nonzero(np.all((sp + se >= lo) & (sp - se <= hi), axis=1))[0] if len(sp) else []
            rest = set(i for i in near0 if obb_overlap(b0, static[i]["box"]))
            for M, dd in states:
                bx = Box(M @ b0.p + dd, M @ b0.R, b0.h, b0.name)
                e = ext(bx)
                lo, hi = bx.p - e, bx.p + e
                near = np.nonzero(np.all((sp + se >= lo) & (sp - se <= hi), axis=1))[0] if len(sp) else []
                for i in near:
                    if i in rest:
                        continue
                    if obb_overlap(bx, static[i]["box"], margin=0.6):
                        k = ("moves through", chain[-1]["name"], p["box"].name, static[i]["box"].name)
                        HIT.append((static[i]["box"].inst, chain, p["root"]))
                        CLASH.add(id(p["root"])) if p["root"] is not None else None
                        ROOTS[id(p["root"])] = p["root"]
                        if k not in where:
                            where[k] = [round(v - o, 0) for v, o in zip(bx.p, (1903.0, 1120.028, 24068.699))]
                        hits[k] += 1
                        rest.add(i)
    # 2. clock rotors: decks turning or rocking into fixed things
    rot = collections.defaultdict(list)
    for p in parts:
        if p["rotor"] and p["vis"] and min(p["size"]) >= 0.8:
            rot[p["rotor"]["ClockRotor"]].append(p)
    for rid, ps in rot.items():
        ra = ps[0]["rotor"]
        mode = ra.get("ClockMode")
        if mode in ("hang", "fixed"):
            continue
        rest_cf = CF.from_prop((0, tuple(ra["ClockRest"][2])), ) if False else None
        r_p = np.array(ra["ClockRest"][1], float)
        r_R = np.array(ra["ClockRest"][2], float).reshape(3, 3)
        ax_l = np.array(ra["ClockAxis"][1:4], float)
        ax = r_R @ ax_l
        ax /= np.linalg.norm(ax)
        amp = float(ra.get("ClockAmp", 0.0))
        angs = (list(np.linspace(0, TAU, 25)) if mode in ("spin", "tick", "flip") else list(np.linspace(-amp, amp, 11)))
        K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
        for p in ps:
            b0 = p["box"]
            # a disc turning on its own axis sweeps nothing new (its box would)
            if p["box"].inst.get("shape", 1) == 2 and abs(float(b0.R[:, 0] @ ax)) > 0.999 \
                    and np.linalg.norm(np.cross(b0.p - r_p, ax)) < 1.0:
                continue
            lo, hi = b0.p - ext(b0) - 1, b0.p + ext(b0) + 1
            near0 = np.nonzero(np.all((sp + se >= lo) & (sp - se <= hi), axis=1))[0] if len(sp) else []
            rest = set(i for i in near0 if obb_overlap(b0, static[i]["box"]))
            for a in angs:
                M = np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * (K @ K)
                bx = Box(M @ (b0.p - r_p) + r_p, M @ b0.R, b0.h, b0.name)
                e = ext(bx)
                near = np.nonzero(np.all((sp + se >= bx.p - e) & (sp - se <= bx.p + e), axis=1))[0] if len(sp) else []
                for i in near:
                    if i in rest:
                        continue
                    if obb_overlap(bx, static[i]["box"], margin=0.6):
                        k = ("rotor sweeps through", rid, p["box"].name, static[i]["box"].name)
                        HIT.append((static[i]["box"].inst, None, None))
                        if k not in where:
                            where[k] = [round(v - o, 0) for v, o in zip(bx.p, (1903.0, 1120.028, 24068.699))]
                        hits[k] += 1
                        rest.add(i)
    # 3. static scenery through a road surface
    roads = [p for p in static if any(p["box"].name == n for n in ROAD)]
    deco = [p for p in parts if not p["chain"] and not p["rotor"] and p["vis"] and not p["hazard"] and not p["mesh"]
            and not any(k in p["box"].name for k in ROAD_KIT) and p["box"].name not in ROAD]
    if roads and deco:
        rp = np.array([p["box"].p for p in roads])
        re_ = np.array([ext(p["box"]) for p in roads])
        for p in deco:
            b = p["box"]
            e = ext(b)
            near = np.nonzero(np.all((rp + re_ >= b.p - e) & (rp - re_ <= b.p + e), axis=1))[0]
            for i in near:
                rb = roads[i]["box"]
                # the road's top face: the part must reach well above it (it pokes up through the road)
                top = rb.p + rb.R[:, 1] * rb.h[1]
                if (b.p + e)[1] < top[1] + 1.0 or (b.p - e)[1] > top[1] - 0.5:
                    continue
                if obb_overlap(b, rb, margin=0.6):
                    k = ("pokes up through road", b.name, rb.name)
                    if k not in where:
                        where[k] = [round(v - o, 0) for v, o in zip(b.p, (1903.0, 1120.028, 24068.699))]
                    hits[k] += 1
    # 4. ghosts in moving rigs: big visible parts of a dangerous machine that neither collide nor hurt
    hurts = set(id(p["root"]) for p in parts if p["root"] is not None and p["hazard"])
    for p in parts:
        if p["chain"] and p["vis"] and not p["hazard"] and not p["collide"] and not p["neon"] and min(p["size"]) >= 2.5 \
                and max(p["size"]) >= 6 and id(p["root"]) in hurts:
            k = ("ghost in a moving rig", p["chain"][-1]["name"], p["box"].name)
            hits[k] += 1
            where.setdefault(k, [round(v - o, 0) for v, o in zip(p["box"].p, (1903.0, 1120.028, 24068.699))])
    return hits, where


def tidy(lvl, detach):
    """After a level is built: (1) every visible piece of a moving machine that has a hazard hurts like the machine
    (no ghost arms, hubs or chains to drive through); (2) a purely decorative spinner or swinger that still sweeps
    through something solid is taken out. Returns (pieces made hazardous, decorations removed)."""
    import collections as C
    parts = []
    CLASH.clear()
    ROOTS.clear()
    audit_level(lvl, 0, only_roots=set())
    parts = list(PARTS)
    by_root = C.defaultdict(list)
    for p in parts:
        if p["root"] is not None:
            by_root[id(p["root"])].append(p)
    n_hz = 0
    decor = set()
    for rid, ps in by_root.items():
        kinds = C.Counter(p["kind"] for p in ps if p["kind"])
        if not kinds:
            if not any(p["collide"] for p in ps):
                decor.add(rid)
            continue
        kind = kinds.most_common(1)[0][0]
        for p in ps:
            if p["chain"] and p["vis"] and not p["kind"] and not p["collide"] and not p["neon"] and min(p["size"]) >= 0.8:
                inst = p["box"].inst
                a = rbxl.attrs(inst) or {}
                a["ObbyHazard"] = kind
                rbxl.set_attrs(inst, a)
                inst.set("CanQuery", True)
                n_hz += 1
    CLASH.clear()
    audit_level(lvl, 0, only_roots=decor)
    n_rm = 0
    for rid in list(CLASH):
        if rid in decor and ROOTS.get(rid) is not None:
            detach(ROOTS[rid])
            n_rm += 1
    return n_hz, n_rm


def clear_sweeps(lvl, cpts, detach, big=60.0):
    """Take out the fixed scenery a moving machine turns, swings or slides through (a post beside a turntable, a
    wall a door blade passes through). Never the road: a part with the racing line on or just above it, a part with
    attributes (checkpoints, hazards, spots) and big structure stay; a harmless machine (a gear platform turning for
    show) that turns through road is stopped instead. Returns (parts removed, rigs stopped, clashes left)."""
    CLASH.clear()
    ROOTS.clear()
    HIT.clear()
    audit_level(lvl, 0)
    pts = np.array([q[:3] for q in cpts], float) if cpts else np.zeros((0, 3))
    hurts = set(id(p["root"]) for p in PARTS if p["root"] is not None and p["hazard"])
    gone, kept, stopped, seen = [], [], [], set()
    for inst, chain, root in HIT:
        if inst is None or id(inst) in seen or inst.parent is None:
            continue
        cf = CF.from_prop(inst.get("CFrame"))
        bx = Box(cf.p, mat_of(cf), np.array(inst.get("size"), float) / 2 + np.array([2.0, 6.0, 2.0]), inst.name)
        on_line = False
        if len(pts):
            loc = (pts - bx.p) @ bx.R
            on_line = bool(np.any(np.all(np.abs(loc) <= bx.h, axis=1)))
        if on_line or rbxl.attrs(inst) or max(inst.get("size")) > big or any(n in inst.name for n in ROAD):
            if chain and root is not None and id(root) not in hurts:
                for r in chain:
                    a = rbxl.attrs(r["node"]) or {}
                    if a.get("PropAmount"):
                        a["PropAmount"] = 0.0
                        rbxl.set_attrs(r["node"], a)
                        stopped.append(r["name"])
                continue
            seen.add(id(inst))
            kept.append(inst.name)
            continue
        seen.add(id(inst))
        detach(inst)
        gone.append(inst.name)
    return gone, stopped, kept


def ray_obb(o, d, bx, tmax):
    """Distance along the ray o + t d (0 < t < tmax) to where it enters box bx, or None."""
    lo_ = bx.R.T @ (o - bx.p)
    ld = bx.R.T @ d
    t0, t1 = 0.0, tmax
    for k in range(3):
        if abs(ld[k]) < 1e-9:
            if abs(lo_[k]) > bx.h[k]:
                return None
            continue
        a = (-bx.h[k] - lo_[k]) / ld[k]
        c = (bx.h[k] - lo_[k]) / ld[k]
        if a > c:
            a, c = c, a
        t0, t1 = max(t0, a), min(t1, c)
        if t0 > t1:
            return None
    return t0


def clear_line(lvl, cpts, detach):
    """Take out the decoration across the racing line: a visible part that does not collide and is not a hazard,
    in the way of the car's body (the validator's own test), is removed. Returns the names removed."""
    import validate
    from factory import is_basepart
    cand = []
    for d in lvl.descendants():
        if not is_basepart(d) or d.get("CanCollide") or d.get("Transparency", 0.0) >= 0.6:
            continue
        a = rbxl.attrs(d) or {}
        if "ObbyHazard" in a or any(k in d.name for k in validate.PASS):
            continue
        node, moving = d.parent, False
        while node is not None and node is not lvl:
            na = rbxl.attrs(node) or {}
            if node.cls == "Model" and any(k in na for k in ("PropMotion", "ClockRotor", "ClockSand", "ArcadeM")):
                moving = True
                break
            node = node.parent
        if moving:
            continue
        cf = CF.from_prop(d.get("CFrame"))
        sz = list(d.get("size"))
        kind = d.get("shape", 1)
        if kind in (0, 2) or any(c.cls == "SpecialMesh" for c in d.children):
            m = min(sz)
            sz = [m if kind == 0 else v for v in sz]
        cand.append(Box(cf.p, mat_of(cf), np.array(sz) / 2, d.name, d))
    if not cand:
        return []
    cp = np.array([c.p for c in cand])
    ce = np.array([ext(c) for c in cand])
    gone = []
    pts = [np.array(q[:3], float) for q in cpts]
    for a, b in zip(pts, pts[1:]):
        dv = b - a
        L = float(np.linalg.norm(dv))
        if L < 0.5:
            continue
        lo, hi = np.minimum(a, b) - 4, np.maximum(a, b) + 4
        near = np.nonzero(np.all((cp + ce >= lo) & (cp - ce <= hi), axis=1))[0]
        for i in near:
            c = cand[i]
            if c.inst is None:
                continue
            for lift in (-2.0, 1.0):
                o = a + np.array([0, lift, 0])
                if ray_obb(o, dv / L, c, L) is not None:
                    gone.append(c.name)
                    detach(c.inst)
                    c.inst = None
                    break
    return gone


def main():
    path = sys.argv[2]
    if path.endswith(".pkl"):
        import cache
        p = cache.load(path)
    else:
        p = rbxl.load(path)
    pool = [i for i in p.all() if i.name == "OBBY_POOL"][0]
    ids = [int(a) for a in sys.argv[3:]]
    total = 0
    for lid in ids:
        unit = pool.find("L%03d" % lid)
        hits, where = audit_level(unit.find("Level"), lid)
        total += len(hits)
        print("L%03d %d kinds" % (lid, len(hits)))
        for k, n in sorted(hits.items(), key=lambda kv: (kv[0][0], -kv[1])):
            print("    %-24s %-26s %-18s %-18s x%-3d %s" % (k[0], k[1], k[2], k[3] if len(k) > 3 else "", n, where[k]))
    print("total kinds:", total)


if __name__ == "__main__":
    t = threading.Thread(target=main)
    t.start()
    t.join()
