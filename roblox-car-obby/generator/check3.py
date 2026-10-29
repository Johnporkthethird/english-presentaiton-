"""Checks on the delivered place: ids, the pinned course, and every new mechanic wired as the game's scripts expect."""
import sys; sys.path.insert(0, sys.argv[1])
import rbxl, collections, threading, math
from geom import CF
from factory import is_basepart
sys.setrecursionlimit(1000000)
threading.stack_size(512 * 1024 * 1024)


def go():
    p = rbxl.load(sys.argv[2])
    allx = p.all()
    uids = collections.Counter(i.get("UniqueId") for i in allx if "UniqueId" in i.props)
    print("instances", len(allx), "duplicate UniqueIds", sum(c - 1 for u, c in uids.items() if c > 1))
    ws = p.roots[0]
    print("ObbyDefaultCourse", rbxl.attrs(ws).get("ObbyDefaultCourse"), "ObbyMix", rbxl.attrs(ws).get("ObbyMix"))
    asm = [i for i in allx if i.cls == "ModuleScript" and i.name == "ObbyAssembler"]
    print("assembler moves ClockRest + BrickFace:", all(b"ClockRest = true" in i.get("Source") and b"BrickFace = true" in i.get("Source") for i in asm), len(asm))
    for c in sorted([c for c in ws.children if c.name.startswith("OBBY")], key=lambda c: rbxl.attrs(c).get("ObbySlot", 0)):
        a = rbxl.attrs(c)
        ds = c.descendants()
        n = collections.Counter()
        worst = 0.0
        for d in ds:
            da = rbxl.attrs(d) or {}
            if d.cls == "Model" and "ClockRotor" in da:
                n["rotor"] += 1
                rest = da["ClockRest"][1]
                ps = [CF.from_prop(q.get("CFrame")).p for q in d.descendants() if is_basepart(q)]
                if ps and da.get("ClockMode") != "hang":
                    worst = max(worst, min(math.dist(rest, q) for q in ps))
                elif ps:
                    worst = max(worst, min(math.dist(rest, q) for q in ps))
            if d.cls == "Model" and da.get("MagnetRide"):
                n["beam"] += 1
                zone = d.find("MagnetPickup")
                zp = CF.from_prop(zone.get("CFrame")).p
                A = da["RideA"][1:4]
                worst = max(worst, math.dist(zp, A) - 8)
            if d.cls == "Model" and da.get("ArcadeM") == "bricks":
                n["brickwall"] += 1
                face = da["BrickFace"][1]
                ps = [CF.from_prop(q.get("CFrame")).p for q in d.descendants() if is_basepart(q)]
                worst = max(worst, min(math.dist(face, q) for q in ps) - da["BrickW"] / 2 - da["BrickH"])
            if d.cls == "Model" and da.get("ClockSand"):
                n["sinkboard"] += 1
            if d.cls == "Model" and da.get("BounceModel"):
                n["shroom"] += 1
            if d.cls == "Model" and "BoostSpeed" in da:
                n["boostdeck"] += 1
            if is_basepart(d) and "Conveyor" in da:
                n["belt"] += 1
            if is_basepart(d) and da.get("BoostStack"):
                n["strip"] += 1
            if is_basepart(d) and da.get("CarLaunchPad"):
                n["pad"] += 1
                if "LaunchForward" in da:
                    n["pad_forward"] += 1
            if is_basepart(d) and da.get("ObbyHazard") == "Slip":
                n["slick"] += 1
            if is_basepart(d) and (("Hoop" in d.name) or ("Loop" in d.name)):
                n["HOOP/LOOP"] += 1
        print("%-6s slot %s x %.0f  %s  worst rest/zone offset %.1f" % (c.name, a.get("ObbySlot"), a.get("SlotX0", 0),
                                                                  dict(n), worst))


t = threading.Thread(target=go)
t.start()
t.join()
