"""Rebuild all 100 obby levels in the place.

usage: python3 -I build.py <tools dir> <in.pkl> <out.rbxl> [ids...]
"""
import sys
sys.path.insert(0, sys.argv[1])
import json
import math
import pickle
import random
import threading
import rbxl
from factory import Factory, transform_tree
from geom import CF, look_frame
from builder import LevelBuilder, X0, ZC, Y0
from sections import St, SECTIONS
import levels3

sys.setrecursionlimit(1000000)
threading.stack_size(512 * 1024 * 1024)

POS_ATTR = {"CheckpointCFrame"}
import os
EXPORT = os.environ.get("EXPORT_DIR")
INDEX_ATTR = {"CheckpointIndex", "CpIndex"}


def svc(p, name):
    for r in p.roots:
        if r.cls == name:
            return r


def detach(inst):
    if inst.parent is not None:
        inst.parent.children.remove(inst)
        inst.parent = None


def measure(fac, templates, sandbox):
    """Longest x-length each section type has produced over many seeds and difficulties."""
    out = {}
    theme, _ = levels.theme_for(1)
    for key, fn in SECTIONS.items():
        mx = 0
        for s in range(40):
            rng = random.Random(s * 31 + 7)
            b = LevelBuilder(fac, sandbox, theme, rng, 99999, templates)
            st = St(X0, Y0, ZC, 60, ZC)
            fn(b, st, (s % 5) / 4.0, rng)
            mx = max(mx, st.x - X0)
            for c in list(sandbox.children):
                detach(c)
        out[key] = mx
    return out


def place_slot(fac, unit, slot, x0):
    """ObbyAssembler.place, offline: the packed course in Workspace."""
    lvl = fac.clone(unit.find("Level"))
    a = rbxl.attrs(lvl)
    dx = x0 - a["SlotX0"]
    T = CF((dx, 0, 0))
    transform_tree(lvl, T)
    for d in [lvl] + lvl.descendants():
        da = rbxl.attrs(d)
        if not da:
            continue
        ch = False
        for k, v in list(da.items()):
            if k in POS_ATTR and isinstance(v, tuple) and v[0] == "CFrame":
                da[k] = ("CFrame", (v[1][0] + dx, v[1][1], v[1][2]), v[2])
                ch = True
            elif k in INDEX_ATTR and isinstance(v, (int, float)):
                f = v - math.floor(v)
                if slot == 1:
                    f = 0.05 + f * 0.95
                da[k] = max(slot - 1, 0) + f
                ch = True
        if ch:
            rbxl.set_attrs(d, da)
    ln = rbxl.attrs(unit)["Length"]
    lvl.set("Name", ("OBBY%d" % slot).encode())
    a = rbxl.attrs(lvl)
    a.update({"ObbySlot": float(slot), "pos": float(slot), "SlotX0": float(x0), "SlotX1": float(x0 + ln),
              "StageLength": float(ln), "ObbyTheme": "pool"})
    rbxl.set_attrs(lvl, a)
    pts = []
    for q in unit.find("CoursePath").get("Value").decode().split("|"):
        x, rest = q.split(",", 1)
        pts.append("%.2f,%s" % (float(x) + dx, rest))
    return lvl, "|".join(pts), ln


def export_level(lvl, path, course, meta):
    """Compact geometry dump for the browser preview (positions relative to the level origin)."""
    from factory import is_basepart
    out = []
    names = {}
    hidden = []
    for d in lvl.descendants():
        if not is_basepart(d):
            continue
        tr = d.get("Transparency", 0.0)
        if tr >= 0.99 and d.get("CanCollide") and d.name in ("Floor",):
            tr = 1.0  # an invisible floor: kept for the validator, skipped by the viewer
        elif tr >= 0.99:
            # the invisible but important ones (triggers, volumes, pads) go to the validator only
            a = rbxl.attrs(d)
            cf = CF.from_prop(d.get("CFrame"))
            hidden.append({"name": d.name, "p": [round(cf.p[0] - X0, 1), round(cf.p[1] - Y0, 1), round(cf.p[2] - ZC, 1)],
                           "r": [round(v, 3) for v in cf.rows()], "s": [round(v, 2) for v in d.get("size")],
                           "a": {k: (list(v) if isinstance(v, tuple) else v) for k, v in a.items()}})
            continue
        cf = CF.from_prop(d.get("CFrame"))
        if d.cls == "WedgePart":
            kind = 3
        elif d.cls == "MeshPart":
            mc = d.get("MeshContent")
            uri = mc[1] if mc else b""
            kind = 5 if b"5438174455" in uri else 6 if b"1254392112" in uri else 1
        elif any(c.cls == "SpecialMesh" and c.get("MeshType") == 3 for c in d.children):
            kind = 4
        else:
            kind = {0: 0, 1: 1, 2: 2}.get(d.get("shape", 1), 1)
        moving = 0
        a = d.parent
        while a is not None and a is not lvl:
            if a.cls == "Model" and "PropMotion" in rbxl.attrs(a):
                moving = 1
                break
            a = a.parent
        hz = 1 if "ObbyHazard" in rbxl.attrs(d) else 0
        c = d.get("Color3uint8")
        r = cf.rows()
        nm = d.name
        if nm not in names:
            names[nm] = len(names)
        out.append([kind, round(cf.p[0] - X0, 1), round(cf.p[1] - Y0, 1), round(cf.p[2] - ZC, 1)] +
                   [round(v, 3) for v in r] + [round(v, 2) for v in d.get("size")] +
                   [(c[0] << 16) | (c[1] << 8) | c[2], d.get("Material"), round(tr, 2), moving, hz,
                    1 if d.get("CanCollide") else 0, names[nm]])
    pts = []
    for q in course.split("|"):
        x, y, z = (float(v) for v in q.split(","))
        pts.append([round(x - X0, 1), round(y - Y0, 1), round(z - ZC, 1)])
    with open(path, "w") as f:
        json.dump({"meta": meta, "parts": out, "path": pts, "names": list(names)}, f, separators=(",", ":"))
    with open(path.replace(".json", ".hidden.json"), "w") as f:
        json.dump({"hidden": hidden, "jumps": meta.get("jumps", [])}, f, separators=(",", ":"))


def main():
    with open(sys.argv[2], "rb") as f:
        place = pickle.load(f)
    only = [int(a) for a in sys.argv[4:]] or list(range(1, 101))
    ws = place.roots[0]
    ss = svc(place, "ServerStorage")
    pool = ss.find("OBBY_POOL")
    fac = Factory(place)
    L1 = pool.find("L001").find("Level")
    fac.find_templates(L1)
    # asset templates (detached clones, so clearing the levels cannot touch them)
    flag = next(c for c in L1.children if c.name == "CHECKPOINT_FLAG" and rbxl.attrs(c).get("CpIndex") == 0.05)
    pad = L1.find("UNIVERSAL_BLUE_JUMP_PAD_01")
    boost = L1.find("UniBoost_5")
    tpl = {"flag": fac.clone(flag), "pad": fac.clone(pad), "boost": fac.clone(boost)}
    sign_tl = next(i for i in place.all() if i.cls == "TextLabel" and i.parent is not None and i.parent.cls == "SurfaceGui")
    tpl["surfacegui"] = fac.clone(sign_tl.parent)
    tpl["textlabel"] = fac.clone(sign_tl)
    tpl["flag_ref"] = look_frame((1933.0, 1130.030029296875, ZC), (1, 0, 0))
    body = CF.from_prop(pad.find("UniPadBody").get("CFrame"))
    tpl["pad_ref"] = body * CF((0, -0.55 / 2, 0))
    bb = CF.from_prop(boost.find("UniBoostBody").get("CFrame"))
    tpl["boost_ref"] = bb * CF((0, -0.17, 0))

    report = []
    for lid in only:
        unit = pool.find("L%03d" % lid)
        lvl = unit.find("Level")
        for c in list(lvl.children):
            detach(c)
        length = rbxl.attrs(unit)["Length"]
        b, used, title, theme = levels3.build_level(fac, unit, lvl, lid, length, tpl)
        cpath, cpts = b.course_path_ordered()
        unit.find("CoursePath").set("Value", cpath.encode())
        n = len(lvl.descendants())
        if EXPORT:
            meta = {"id": lid, "title": title, "theme": theme, "sections": used, "length": length,
                    "light": {k: v for k, v in rbxl.attrs(lvl).items() if k.startswith("Lt_")},
                    "jumps": [[j[0], [j[1][0] - X0, j[1][1] - Y0, j[1][2] - ZC], [j[2][0] - X0, j[2][1] - Y0, j[2][2] - ZC],
                               j[3], j[4]] for j in b.jumps],
                    "gaps": [[g0 - X0, g1 - X0] for g0, g1 in b.gaps]}
            meta["flags"] = "".join(p[3] for p in cpts)
            export_level(lvl, "%s/L%03d.json" % (EXPORT, lid), cpath, meta)
        report.append({"id": lid, "title": title, "theme": theme, "sections": used, "instances": n,
                       "checkpoints": len(b.cps), "length": length})
        print("L%03d %-22s %-10s %5d inst  %2d cps  %s" % (lid, title, theme, n, len(b.cps), " ".join(used)))

    # the packed course in Workspace: OBBY1..10 = levels 1..10, laid end to end from X0
    mix = [int(s) for s in rbxl.attrs(ws)["ObbyMix"].split(",")]
    for c in list(ws.children):
        if c.name.startswith("OBBY") and rbxl.attrs(c).get("ObbySlot"):
            detach(c)
    x = rbxl.attrs(pool)["X0"]
    lines = []
    for slot, lid in enumerate(mix, 1):
        lvl, line, ln = place_slot(fac, pool.find("L%03d" % lid), slot, x)
        lvl.set_parent(ws)
        lines.append(line)
        x += ln
    last = [c for c in ws.children if c.name == "OBBY%d" % len(mix)][0]
    la = rbxl.attrs(last)
    la["StageLength"] = la["StageLength"] + rbxl.attrs(pool)["ArchRel"]
    rbxl.set_attrs(last, la)
    assert abs(x - rbxl.attrs(ws)["StadiumAtX"]) < 0.01, (x, rbxl.attrs(ws)["StadiumAtX"])
    tail = []
    for q in pool.find("StadiumTail").get("Value").decode().split("|"):
        rx, rest = q.split(",", 1)
        tail.append("%.2f,%s" % (float(rx) + x, rest))
    lines.append("|".join(tail))
    rs = ws.find("RACING_START")
    rs.find("CoursePath").set("Value", "|".join(lines).encode())

    with open(sys.argv[3] + ".report.json", "w") as f:
        json.dump(report, f, indent=1)
    rbxl.save(place, sys.argv[3])
    print("saved", sys.argv[3])


t = threading.Thread(target=main)
t.start()
t.join()
