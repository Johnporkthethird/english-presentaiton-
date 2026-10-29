"""Plan + side view of exported levels (fast layout check). usage: planview.py <dir> <out.png> ids..."""
import sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib import cm

d, out = sys.argv[1], sys.argv[2]
ids = [int(a) for a in sys.argv[3:]]
fig, axs = plt.subplots(len(ids), 2, figsize=(22, 7 * len(ids)), gridspec_kw={"width_ratios": [3, 2]}, squeeze=False)
for row, lid in enumerate(ids):
    D = json.load(open("%s/L%03d.json" % (d, lid)))
    ax, ax2 = axs[row]
    parts = D["parts"]
    ys = np.array([p[2] for p in parts])
    norm = matplotlib.colors.Normalize(-400, 500)
    for p in sorted(parts, key=lambda p: p[2]):
        kind, x, y, z = p[0], p[1], p[2], p[3]
        R = np.array(p[4:13]).reshape(3, 3)
        S = np.array(p[13:16])
        if S[0] * S[2] < 30 and S.max() < 20:
            continue
        hx = R[:, 0] * S[0] / 2
        hz = R[:, 2] * S[2] / 2
        hy = R[:, 1] * S[1] / 2
        # project the box's footprint: the 3 axes' xz components
        ax_ = [hx, hy, hz]
        ax_.sort(key=lambda v: -np.hypot(v[0], v[2]))
        a, c = ax_[0], ax_[1]
        corners = [(x + sa * a[0] + sc * c[0], z + sa * a[2] + sc * c[2]) for sa, sc in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
        col = (1, 0.2, 0.2, 0.8) if p[20] else cm.viridis(norm(y)) if p[21] else (0.6, 0.6, 0.6, 0.25)
        ax.add_patch(Polygon(corners, closed=True, fc=col, ec="none"))
    P = np.array(D["path"])
    ax.plot(P[:, 0], P[:, 2], "-", color="k", lw=0.8)
    ax.plot(P[0, 0], P[0, 2], "go", ms=10)
    ax.plot(P[-1, 0], P[-1, 2], "rs", ms=10)
    for lab, lo, hi in D["meta"].get("pieces", []):
        ax.text((lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2, lab, fontsize=8, ha="center")
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_title("L%03d %s  plan (x right, z down)" % (lid, D["meta"]["title"]))
    ax.axvline(0, color="r", lw=0.5)
    ax.axvline(D["meta"]["length"], color="r", lw=0.5)
    ax.autoscale()
    # height along the course
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    ax2.plot(s, P[:, 1], "-")
    ax2.set_title("height along the course (%.0f studs driven)" % s[-1])
    ax2.grid(True)
plt.tight_layout()
plt.savefig(out, dpi=55)
