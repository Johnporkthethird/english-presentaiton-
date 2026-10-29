"""Pin the races to the built courses instead of a random ten: by default Obby 1 (course1, levels 1-10, packed in the
place) and Obby 2 (course2, levels 11-20) take turns, one race each.

usage: python3 -I test_course.py <tools dir> <in.rbxl> <out.rbxl> [course keys, default "course2,course1"; "random" restores]
Adds workspace attribute ObbyDefaultCourse, read by ServerScriptService.WorldRotation at every intermission: one key, or
a comma list taking turns (the next after the course now loaded).
"""
import sys
sys.path.insert(0, sys.argv[1])
import threading
import rbxl

sys.setrecursionlimit(1000000)
threading.stack_size(512 * 1024 * 1024)
OLD = b'local want = nextKey or "random"'
PIN1 = b'local want = nextKey or workspace:GetAttribute("ObbyDefaultCourse") or "random" -- (a dev pin, else a random ten)'
NEW = (b'local want = nextKey or (function() local pin = workspace:GetAttribute("ObbyDefaultCourse") if not pin then return nil end '
       b'local keys = string.split(pin, ",") local i = table.find(keys, workspace:GetAttribute("ObbyWorldKey") or "") or 0 '
       b'return keys[i % #keys + 1] end)() or "random" -- (a dev pin - a list of keys takes turns -, else a random ten)')


def patch(place, key):
    hits = 0
    for i in place.all():
        if i.cls == "Script" and i.name == "WorldRotation":
            src = i.get("Source")
            if NEW not in src:
                old = PIN1 if PIN1 in src else OLD
                assert old in src, "WorldRotation changed: cannot pin the course"
                i.set("Source", src.replace(old, NEW))
            hits += 1
    assert hits == 1, hits
    ws = place.roots[0]
    a = rbxl.attrs(ws)
    if key == "random":
        a.pop("ObbyDefaultCourse", None)
    else:
        a["ObbyDefaultCourse"] = key
    rbxl.set_attrs(ws, a)


def main():
    p = rbxl.load(sys.argv[2])
    patch(p, sys.argv[4] if len(sys.argv) > 4 else "course2,course1")
    rbxl.save(p, sys.argv[3])
    print("saved", sys.argv[3], "ObbyMix", rbxl.attrs(p.roots[0]).get("ObbyMix"), "default",
          rbxl.attrs(p.roots[0]).get("ObbyDefaultCourse"))


if __name__ == "__main__":
    t = threading.Thread(target=main)
    t.start()
    t.join()
