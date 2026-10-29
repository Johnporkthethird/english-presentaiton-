"""Make every race load the showcase course (levels 1-10) instead of a random ten, for testing.

usage: python3 -I test_course.py <tools dir> <in.rbxl> <out.rbxl> [course key, default course1; "random" restores]
Adds workspace attribute ObbyDefaultCourse, read by ServerScriptService.WorldRotation at every intermission.
"""
import sys
sys.path.insert(0, sys.argv[1])
import threading
import rbxl

sys.setrecursionlimit(1000000)
threading.stack_size(512 * 1024 * 1024)
OLD = b'local want = nextKey or "random"'
NEW = b'local want = nextKey or workspace:GetAttribute("ObbyDefaultCourse") or "random" -- (a dev pin, else a random ten)'


def patch(place, key):
    hits = 0
    for i in place.all():
        if i.cls == "Script" and i.name == "WorldRotation":
            src = i.get("Source")
            if NEW not in src:
                assert OLD in src, "WorldRotation changed: cannot pin the course"
                i.set("Source", src.replace(OLD, NEW))
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
    patch(p, sys.argv[4] if len(sys.argv) > 4 else "course1")
    rbxl.save(p, sys.argv[3])
    print("saved", sys.argv[3], "ObbyMix", rbxl.attrs(p.roots[0]).get("ObbyMix"), "default",
          rbxl.attrs(p.roots[0]).get("ObbyDefaultCourse"))


if __name__ == "__main__":
    t = threading.Thread(target=main)
    t.start()
    t.join()
