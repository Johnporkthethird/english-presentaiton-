"""Geometry checks on the exported levels.

usage: python3 -I validate.py <levels dir> [ids...]
"""
import sys
import json
import math
import glob
import numpy as np

G = 196.2


class Level:
    def __init__(self, path):
        d = json.load(open(path))
        h = json.load(open(path.replace(".json", ".hidden.json")))
        self.meta = d["meta"]
        self.names = d["names"]
        P = np.array([p[1:4] for p in d["parts"]], dtype=float)
        R = np.array([p[4:13] for p in d["parts"]], dtype=float).reshape(-1, 3, 3)
        S = np.array([p[13:16] for p in d["parts"]], dtype=float)
        kind = np.array([p[0] for p in d["parts"]])
        # balls and cylinders: use their real (smaller) extents
        S = S.copy()
        S[kind == 0] = np.min(S[kind == 0], axis=1, keepdims=True) if (kind == 0).any() else S[kind == 0]
        self.P, self.R, self.S = P, R, S
        self.collide = np.array([p[21] for p in d["parts"]], dtype=bool)
        self.moving = np.array([p[19] for p in d["parts"]], dtype=bool)
        self.hazard = np.array([p[20] for p in d["parts"]], dtype=bool)
        self.name = [self.names[p[22]] for p in d["parts"]]
        self.alpha = np.array([p[18] for p in d["parts"]], dtype=float)
        self.kind = kind
        self.path = np.array(d["path"], dtype=float)
        self.hidden = h["hidden"]
        self.jumps = h["jumps"]
        self.gaps = self.meta.get("gaps", [])
        self.flags = self.meta.get("flags") or "r" * len(self.path)

    def ray(self, o, dvec, mask, tmax):
        """First hit distance along o + t*d (0<t<tmax) against boxes in mask, or None."""
        idx = np.nonzero(mask)[0]
        if len(idx) == 0:
            return None, None
        P, R, S = self.P[idx], self.R[idx], self.S[idx]
        # local = R^T (o - P)   (R rows are the matrix rows; columns are the local axes)
        lo = np.einsum("nji,nj->ni", R, o - P)
        ld = np.einsum("nji,j->ni", R, dvec)
        h = S / 2
        with np.errstate(divide="ignore", invalid="ignore"):
            t1 = (-h - lo) / ld
            t2 = (h - lo) / ld
        tmin = np.where(np.isnan(t1), -np.inf, np.minimum(t1, t2))
        tmx = np.where(np.isnan(t2), np.inf, np.maximum(t1, t2))
        # parallel axes: inside slab or not
        par = np.abs(ld) < 1e-9
        inside = np.abs(lo) <= h
        tmin = np.where(par, np.where(inside, -np.inf, np.inf), tmin)
        tmx = np.where(par, np.where(inside, np.inf, -np.inf), tmx)
        tn = tmin.max(axis=1)
        tf = tmx.min(axis=1)
        # cylinders (axis = local X): clip by the round wall as well as the end slabs
        cyl = self.kind[idx] == 2
        if cyl.any():
            r2 = (np.minimum(S[:, 1], S[:, 2]) / 2) ** 2
            a = ld[:, 1] ** 2 + ld[:, 2] ** 2
            bq = 2 * (lo[:, 1] * ld[:, 1] + lo[:, 2] * ld[:, 2])
            c = lo[:, 1] ** 2 + lo[:, 2] ** 2 - r2
            disc = bq * bq - 4 * a * c
            with np.errstate(divide="ignore", invalid="ignore"):
                sq = np.sqrt(np.maximum(disc, 0))
                c0 = np.where(a > 1e-12, (-bq - sq) / (2 * a), np.where(c <= 0, -np.inf, np.inf))
                c1 = np.where(a > 1e-12, (-bq + sq) / (2 * a), np.where(c <= 0, np.inf, -np.inf))
            c0 = np.where((a > 1e-12) & (disc < 0), np.inf, c0)
            c1 = np.where((a > 1e-12) & (disc < 0), -np.inf, c1)
            tn = np.where(cyl, np.maximum(tn, c0), tn)
            tf = np.where(cyl, np.minimum(tf, c1), tf)
        ok = (tn <= tf) & (tf >= 0) & (tn <= tmax)
        if not ok.any():
            return None, None
        tn = np.where(ok, np.maximum(tn, 0), np.inf)
        i = int(np.argmin(tn))
        return float(tn[i]), int(idx[i])


def in_gap(x, gaps, pad=8):
    return any(a - pad <= x <= b + pad for a, b in gaps)


def check(lv):
    issues = []
    road = lv.collide.copy()
    static_solid = lv.collide & ~lv.moving & np.array([n not in ("Kicker", "TiltDeck") for n in lv.name])
    # 1. road under the line (outside flown stretches)
    missing = []
    for p, fl in zip(lv.path, lv.flags):
        if fl != "r":
            continue
        t = None
        for dx in (0.0, 3.0, -3.0):  # (a point exactly on a seam between two tiles)
            t, i = lv.ray(p + np.array([dx, 2.0, 0]), np.array([0, -1.0, 0]), road & ~lv.moving, 20)
            if t is not None:
                break
        if t is None:
            for o in ((0.0, 0.0), (3.0, 0.0), (-3.0, 0.0), (0.0, 3.0), (0.0, -3.0), (3.0, 3.0), (-3.0, -3.0)):  # (tile corners)
                t, i = lv.ray(p + np.array([o[0], 2.0, o[1]]), np.array([0, -1.0, 0]), road & lv.moving, 60)
                if t is not None:
                    break
        if t is None:
            missing.append(p)
    if missing:
        issues.append(("no road under line", len(missing), [list(np.round(m, 0)) for m in missing[:4]]))
    # 2. solid things in the way of the line (at body height)
    blocked = []
    for k, (a, b) in enumerate(zip(lv.path, lv.path[1:])):
        if "s" in lv.flags[k:k + 2] or lv.flags[k:k + 2] == "ar":
            continue
        for lift in (-2.0, 1.5):
            o = a + np.array([0, lift, 0])
            dv = b - a
            L = float(np.linalg.norm(dv))
            if L < 0.5:
                continue
            t, i = lv.ray(o, dv / L, static_solid, L)
            if t is not None:
                blocked.append((lv.name[i], list(np.round(o + dv / L * t, 0))))
                break
    if blocked:
        names = sorted(set(n for n, _ in blocked))
        issues.append(("line blocked", len(blocked), names[:6], blocked[:3]))
    # 3. jumps: fly them at a few speeds and see where they come down
    for j in lv.jumps:
        kind, s, tg, H, V = j
        if lv.meta.get("straight") and kind == "pad":
            # the pad must fire straight at its target: its LaunchForward points along the jump
            pads = [h for h in lv.hidden if h["a"].get("CarLaunchPad")]
            if pads:
                pp = min(pads, key=lambda h: (h["p"][0] - s[0]) ** 2 + (h["p"][2] - s[2]) ** 2)
                fw = np.array(pp["a"]["LaunchForward"][-3:], dtype=float)
                jv = np.array([tg[0] - s[0], 0.0, tg[2] - s[2]])
                jv /= max(np.linalg.norm(jv), 1e-6)
                if float(np.dot(fw, jv)) < 0.9995:
                    issues.append(("pad not straight", list(np.round(s, 0)), list(np.round(tg, 0))))
        s, tg = np.array(s), np.array(tg)
        f = tg - s
        f[1] = 0
        D = float(np.linalg.norm(f))
        f = f / max(D, 1e-6)
        # pad: an exact launch; up: an up booster (the car keeps its own speed: the slowest and a typical take-off);
        # key: the car's own jump; drop: rolling off an edge
        speeds = ([H] if kind in ("pad", "exact") else [110.0, 170.0] if kind in ("up", "key")
                  else [H * 0.9, H] if kind in ("ramp", "bounce", "drive") else [H] if kind == "ramp_hop"
                  else [H * 0.8, H] if kind in ("kick", "oup")
                  else [70.0, 130.0, 200.0] if kind == "drop" and H < 200 else [H * 0.8, H] if kind == "drop"
                  else [90.0, 115.0, 160.0])
        for v in speeds:
            up = (V if kind in ("pad", "exact", "up", "bounce", "ramp_hop", "drive", "oup") else V * v / H if kind in ("ramp", "kick")
                  else 0.0 if kind == "drop" else 140.0)
            pos = s + np.array([0, 3.0, 0])
            vel = f * v + np.array([0, up, 0])
            landed = None
            for step in range(600):
                dt = 0.02
                nv = vel + np.array([0, -G * dt, 0])
                npos = pos + nv * dt
                seg = npos - pos
                L = float(np.linalg.norm(seg))
                t, i = lv.ray(pos, seg / L, road, L)
                if t is not None and step > 2:
                    landed = (pos + seg / L * t, i)
                    break
                pos, vel = npos, nv
                if pos[1] < min(s[1], tg[1]) - 400:
                    break
            if landed is None and kind != "ramp_hop":  # (Space held on a lip at full speed: the driver brakes in the air)
                issues.append(("jump falls", kind, v, list(np.round(s, 0)), list(np.round(tg, 0))))
            elif landed is not None:
                lp, i = landed
                if kind == "pad" and np.linalg.norm((lp - tg)[[0, 2]]) > 45:
                    issues.append(("pad lands off target", list(np.round(lp, 0)), list(np.round(tg, 0)), lv.name[i]))
                if kind == "bounce" and np.linalg.norm((lp - tg)[[0, 2]]) > 50:
                    issues.append(("bounce lands off the cap", round(v), list(np.round(lp, 0)), list(np.round(tg, 0)), lv.name[i]))
                if kind in ("ramp", "drive", "ramp_hop", "kick", "oup", "drop") and lv.name[i] not in ("Deck", "Floor", "Platform", "Ramp", "MovingDeck", "SinkTile", "Star"):
                    issues.append(("lands on scenery", kind, round(v), list(np.round(lp, 0)), lv.name[i]))
                if lp[1] < tg[1] - 25 and kind == "key":
                    issues.append(("key jump lands low", v, list(np.round(lp, 0)), lv.name[i]))

    # 4. checkpoints
    cps = [h for h in lv.hidden if h["name"] == "CarObbyCheckpoint"]
    last = -1
    hz = [h for h in lv.hidden if "ObbyHazard" in h["a"] and h["a"]["ObbyHazard"] not in ("Fall",)]
    for c in sorted(cps, key=lambda c: c["a"]["CheckpointIndex"]):
        pose = c["a"]["CheckpointCFrame"]
        pos = np.array(pose[1]) - np.array([1903.0, 1120.0281007289886, 24068.69921875])
        if c["a"]["CheckpointIndex"] <= last:
            issues.append(("cp order", c["a"]["CheckpointIndex"]))
        last = c["a"]["CheckpointIndex"]
        t, i = lv.ray(pos, np.array([0, -1.0, 0]), road, 16)
        if t is None:
            issues.append(("cp over nothing", list(np.round(pos, 0))))
        near = (np.linalg.norm((lv.P - pos)[:, [0, 2]], axis=1) < 30) & (np.abs(lv.P[:, 1] - pos[1]) < 30) & lv.hazard
        if near.any():
            issues.append(("cp near hazard", list(np.round(pos, 0)), lv.name[int(np.nonzero(near)[0][0])]))
    # 5. kill sheets below every road they cover
    for k in [h for h in lv.hidden if h["name"] == "KillSheet"]:
        p, s = np.array(k["p"]), np.array(k["s"])
        top = p[1] + s[1] / 2
        inx = (np.abs(lv.path[:, 0] - p[0]) <= s[0] / 2) & (np.abs(lv.path[:, 2] - p[2]) <= s[2] / 2)
        if inx.any() and (lv.path[inx, 1] - top).min() < 40:
            issues.append(("kill sheet close to line", float((lv.path[inx, 1] - top).min())))
    # 6. steepness of the road slabs
    deck = np.array([n in ("Deck", "Platform", "Beam") for n in lv.name]) & lv.collide & ~lv.moving
    if deck.any():
        fwd = lv.R[deck][:, :, 2]  # local Z column = along the road
        pitch = np.degrees(np.arcsin(np.clip(np.abs(fwd[:, 1]), 0, 1)))
        if pitch.max() > 24:
            issues.append(("steep road", round(float(pitch.max()), 1)))
    # 7b. scenery the car would drive or fly straight through (decoration across the racing line)
    ghost = phase_check(lv)
    if ghost:
        issues.append(("drives through scenery", len(ghost), sorted(set(n for n, _ in ghost))[:8], ghost[:3]))
    # 7. bumps: the road height under the wheels, every 2 studs along the line, must change smoothly
    bumps = bump_check(lv)
    if bumps:
        issues.append(("bumpy road", len(bumps), bumps[:4]))
    return issues


PASS = ("Hoop", "Ring", "Updraft", "Target", "Halo", "Laser", "Glow", "Flame", "Stripe", "Lip", "Edge", "Chevron",
        "Pad", "Sparkle", "Sugar", "Sprinkle", "Spot", "Shine", "Arrow", "Beam", "Light", "Line", "Trim", "Sign", "Text",
        "Letter", "Pixel", "Kicker", "Floor", "Rail", "FlagCap", "Bumper")


def phase_check(lv):
    """Visible, non-colliding parts in the way of the car's body along the racing line."""
    deco = (~lv.collide) & (~lv.hazard) & (~lv.moving) & np.array(
        [not any(k in n for k in PASS) for n in lv.name])
    alpha = np.array([p for p in lv.alpha]) if hasattr(lv, "alpha") else None
    if alpha is not None:
        deco &= alpha < 0.6
    out = []
    for k, (a, b) in enumerate(zip(lv.path, lv.path[1:])):
        dv = b - a
        L = float(np.linalg.norm(dv))
        if L < 0.5:
            continue
        for lift in (-2.0, 1.0):
            o = a + np.array([0, lift, 0])
            t, i = lv.ray(o, dv / L, deco, L)
            if t is not None:
                out.append((lv.name[i], [round(float(v)) for v in o + dv / L * t]))
                break
    return out


def bump_check(lv, step=2.0, tol=0.5):
    solid = lv.collide & ~lv.moving & np.array([n != "Kicker" for n in lv.name])  # (a ramp wedge, not a box)
    idx_all = np.nonzero(solid)[0]
    # world AABBs of the solid parts
    ext = np.einsum("nij,nj->ni", np.abs(lv.R[idx_all]), lv.S[idx_all] / 2)
    lo, hi = lv.P[idx_all] - ext, lv.P[idx_all] + ext
    out = []
    run = {}
    prev_f = None
    for k in range(len(lv.path) - 1):
        if lv.flags[k] != "r" or lv.flags[k + 1] != "r":
            run = {}
            continue
        a, b = lv.path[k], lv.path[k + 1]
        d = b - a
        L = float(np.hypot(d[0], d[2]))
        if L < 0.5 or L > 40:
            run = {}
            continue
        f = np.array([d[0] / L, 0, d[2] / L])
        if prev_f is not None and float(np.dot(prev_f, f)) < math.cos(math.radians(8)):
            run = {}  # (a corner in the line swings the side rays round: not a bump in the road)
        prev_f = f
        rgt = np.array([-f[2], 0, f[0]])
        bl = np.minimum(a, b) - 12
        bh = np.maximum(a, b) + 12
        bl[1] -= 30
        near = idx_all[np.all((hi >= bl) & (lo <= bh), axis=1)]
        if not len(near):
            run = {}
            continue
        mask = np.zeros(len(lv.P), bool)
        mask[near] = True
        n = max(1, int(L // step))
        for i in range(n):
            t = i / n
            p = a + d * t
            for off in (-4.0, 0.0, 4.0):
                h = None
                for e in (-0.3, 0.0, 0.3):  # the highest of three close rays: a hairline seam is not a bump
                    o = p + rgt * off + f * e + np.array([0, 2.0, 0])
                    hit, _ = lv.ray(o, np.array([0, -1.0, 0]), mask, 20)
                    if hit is not None:
                        h = o[1] - hit if h is None else max(h, o[1] - hit)
                key = off
                seq = run.setdefault(key, [])
                seq.append(h)
                if len(seq) >= 3 and None not in seq[-3:]:
                    dd = seq[-1] - 2 * seq[-2] + seq[-3]
                    if abs(dd) > tol:
                        out.append((round(float(abs(dd)), 2), [round(float(v)) for v in p]))
                if len(seq) > 3:
                    del seq[0]
    return out


if __name__ == "__main__":
    d = sys.argv[1]
    ids = [int(a) for a in sys.argv[2:]]
    files = sorted(glob.glob(d + "/L[0-9][0-9][0-9].json"))
    total = 0
    for f in files:
        lid = int(f[-8:-5])
        if ids and lid not in ids:
            continue
        lv = Level(f)
        iss = check(lv)
        total += len(iss)
        print("L%03d %-22s %d issue(s)" % (lid, lv.meta["title"], len(iss)))
        for i in iss[:12]:
            print("    ", i)
    print("total issues:", total)
