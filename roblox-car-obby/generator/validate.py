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
            t, i = lv.ray(p + np.array([0, 2.0, 0]), np.array([0, -1.0, 0]), road & lv.moving, 60)
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
        s, tg = np.array(s), np.array(tg)
        f = tg - s
        f[1] = 0
        D = float(np.linalg.norm(f))
        f = f / max(D, 1e-6)
        speeds = [H] if kind == "pad" else [90.0, 115.0, 160.0]
        for v in speeds:
            up = V if kind == "pad" else 140.0
            pos = s + np.array([0, 3.0, 0])
            vel = f * v + np.array([0, up, 0])
            landed = None
            for step in range(200):
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
                if pos[1] < min(s[1], tg[1]) - 150:
                    break
            if landed is None:
                issues.append(("jump falls", kind, v, list(np.round(s, 0)), list(np.round(tg, 0))))
            else:
                lp, i = landed
                if kind == "pad" and np.linalg.norm((lp - tg)[[0, 2]]) > 45:
                    issues.append(("pad lands off target", list(np.round(lp, 0)), list(np.round(tg, 0)), lv.name[i]))
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
        near = (np.linalg.norm((lv.P - pos)[:, [0, 2]], axis=1) < 30) & lv.hazard
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
    return issues


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
