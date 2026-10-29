"""Route: lays a level as a 3D journey that turns, climbs, dives and doubles back.

The turtle keeps a position (road top) and a heading in the XZ plane. Native pieces (straights, banked turns, spirals,
rollers, connectors) are laid in world space. Every older set piece (built along +X) is built in place at the turtle
and then turned rigidly to the turtle's heading, together with what it recorded (racing line, pads, checkpoints,
samples), so any obstacle can face any way. Pads keep firing straight along their own heading.
"""
import math
import numpy as np
import rbxl
from geom import CF, rot_y, add, sub, mul, unit, dot, cross, lerp, UP
from factory import transform_tree
from builder import X0, Y0, ZC, CAR_UP
import journey as J
from parkour import St

VEC_ATTRS = ("LaunchForward", "ConveyorDir")
PT_ATTRS = ("AutoJumpTarget",)
CF_ATTRS = ("CheckpointCFrame",)
MAX_GRADE = J.MAX_GRADE


def flat(v):
    return unit((v[0], 0.0, v[2]))


def left_of(f):
    return unit(cross(UP, f))


def rotate_tree(b, new, T):
    """Turn freshly built instances (and the attributes that carry world positions or directions) by T."""
    ids = set(map(id, new))
    for d in new:
        if d.parent is None or id(d.parent) not in ids:
            transform_tree(d, T)
    for d in new:
        a = rbxl.attrs(d)
        if not a:
            continue
        ch = False
        for k, v in list(a.items()):
            if k in VEC_ATTRS and isinstance(v, tuple) and v[0] == "Vector3":
                a[k] = ("Vector3",) + tuple(T.vec(v[1:4]))
                ch = True
            elif k in PT_ATTRS and isinstance(v, tuple) and v[0] == "Vector3":
                a[k] = ("Vector3",) + tuple(T.point(v[1:4]))
                ch = True
            elif k in CF_ATTRS and isinstance(v, tuple) and v[0] == "CFrame":
                cf = T * CF.from_rows(v[2], v[1])
                a[k] = ("CFrame", cf.p, cf.rows())
                ch = True
        if ch:
            rbxl.set_attrs(d, a)


def build_turned(b, fn, T):
    """Run fn() (which builds in the frame T maps from), then move everything it made, and what it recorded, by T."""
    lvl = b.level
    before = set(map(id, lvl.descendants()))
    saved, b.path = b.path, []
    m = (len(b.samples), len(b.jumps), len(b.cps))
    out = fn()
    new = [d for d in lvl.descendants() if id(d) not in before]
    rotate_tree(b, new, T)
    b.path = saved + [T.point(p[:3]) + (p[3],) for p in b.path]
    b.samples[m[0]:] = [T.point(s_[:3]) + (s_[3],) for s_ in b.samples[m[0]:]]
    b.jumps[m[1]:] = [(j[0], T.point(j[1]), T.point(j[2]), j[3], j[4]) for j in b.jumps[m[1]:]]
    b.cps[m[2]:] = [T.point(c[:3]) + (c[3],) for c in b.cps[m[2]:]]
    return out


def trim_line(b, src, f):
    """Drop racing-line road points already past a pad (src, heading f) so the line never runs backwards."""
    while b.path and b.path[-1][3] == "r" and dot(sub(b.path[-1][:3], src), f) > -1:
        b.path.pop()


class Route:
    def __init__(self, b, p, f=(1.0, 0.0, 0.0), w=60.0):
        self.b = b
        self.p = tuple(p)
        self.f = flat(f)
        self.w = float(w)
        self.segs = []      # (label, sample index from, to)
        self.solids = []    # (label, centre, radius, ylo, yhi) landmarks the road must not run into
        self.allow = set()  # pairs of labels allowed to come close (a road through its own landmark)
        self.cp_every = 0.0

    # ------------------------------------------------------------ bookkeeping
    def _seg(self, label, s0):
        self.segs.append((label, s0, len(self.b.samples)))
        b = self.b
        if hasattr(b, "pieces"):
            pts = [s[:3] for s in b.samples[s0:]]
            if pts:
                lo = [min(p[i] for p in pts) for i in range(3)]
                hi = [max(p[i] for p in pts) for i in range(3)]
                b.pieces.append((label, lo, hi))

    def yaw(self):
        return math.atan2(-self.f[2], self.f[0])

    def frame(self):
        return CF(self.p) * rot_y(self.yaw())

    def ahead(self, d, side=0.0, up=0.0):
        """A point d ahead of the turtle, `side` to the right, `up` above."""
        r = mul(left_of(self.f), -1)
        return add(self.p, add(mul(self.f, d), add(mul(r, side), (0, up, 0))))

    def log(self, tag=""):
        a = math.degrees(math.atan2(-self.f[2], self.f[0]))
        print("   @%-14s u=%6.0f h=%5.0f v=%6.0f  heading %4.0f  w=%.0f" % (tag, self.p[0] - X0, self.p[1] - Y0,
                                                                         self.p[2] - ZC, a, self.w))
        return self

    def solid(self, label, c, r, ylo, yhi, box=None):
        """A landmark the road must keep clear of: a round one (radius r) or a box (box = (half x, half z))."""
        self.solids.append((label, tuple(c), float(r), float(ylo), float(yhi), box))

    # ------------------------------------------------------------ an older +X set piece, turned to the heading
    def local(self, label, fn, *a, **kw):
        b = self.b
        s0 = len(b.samples)
        st = St(self.p[0], self.p[1], self.p[2], self.w, self.p[2])
        old_zc = getattr(b, "zc", ZC)
        b.zc = self.p[2]
        T = CF(self.p) * rot_y(self.yaw()) * CF(mul(self.p, -1))
        build_turned(b, lambda: fn(b, st, *a, **kw), T)
        b.zc = old_zc
        self.p = T.point((st.x, st.y, st.z))
        self.w = st.w or self.w
        self._seg(label, s0)
        return self

    def along(self, fn, at, i0=0, **kw):
        """Obstacles along the road just laid: fn(b, c, w, i, **kw) builds one at c heading +X (c is the road top);
        it is then turned to the road there (heading, slope and bank)."""
        from geom import deck_frame
        b = self.b
        pts, ws, bank = self.last
        cum = [0.0]
        for a_, c_ in zip(pts, pts[1:]):
            cum.append(cum[-1] + math.dist(a_, c_))
        for i, d in enumerate(at):
            k = max(0, min(len(pts) - 2, next((ii for ii in range(len(pts) - 1) if cum[ii + 1] >= d), len(pts) - 2)))
            t = (d - cum[k]) / max(cum[k + 1] - cum[k], 1e-6)
            c = lerp(pts[k], pts[k + 1], max(0.0, min(1.0, t)))
            fr = deck_frame(c, sub(pts[k + 1], pts[k]), bank=bank(k) if bank else 0.0)
            right = mul(fr.x, -1)
            T = CF(c, fr.z, fr.y, right) * CF((0, 0, 0))
            w = ws[k]
            build_turned(b, lambda: fn(b, (0.0, 0.0, 0.0), w, i0 + i, **kw), T)
        return self

    # ------------------------------------------------------------ native roads
    def _lay(self, label, pts, widths, cp=False, **kw):
        b = self.b
        s0 = len(b.samples)
        if cp:
            f = flat(sub(pts[min(4, len(pts) - 1)], pts[0]))
            q = add(pts[0], mul(f, 14))
            b.checkpoint(q[0], pts[0][1], q[2], widths[0], f)
        J.lay_road(b, pts, widths, **kw)
        self.last = (pts, widths, kw.get("bank"))
        self._seg(label, s0)
        self.p = tuple(pts[-1])
        self.w = widths[-1]
        return self

    def straight(self, label, L, dy=0.0, w1=None, lead=30.0, swing=0.0, waves=0, cp=False, **kw):
        """A straight (or snaking) road along the heading, with a smooth climb or dive of dy."""
        w0 = self.w
        w1 = w0 if w1 is None else w1
        if dy:
            L = J.length_for(dy, L, lead)
        n = max(8, int(L / 6))
        prof = J.ramp_profile(n)
        r = mul(left_of(self.f), -1)
        pts, ws = [], []
        for i in range(n + 1):
            t = i / n
            u = min(1.0, max(0.0, (t * L - lead) / max(L - 2 * lead, 1)))
            e = float(prof(u))
            sz = swing * math.sin(math.pi * waves * u) * math.sin(math.pi * u) if waves else 0.0
            p = add(self.p, add(mul(self.f, L * t), mul(r, sz)))
            pts.append((p[0], self.p[1] + dy * e, p[2]))
            ws.append(w0 + (w1 - w0) * J.ease_s(u))
        assert J.grade_ok(pts), ("too steep", label, L, dy)
        return self._lay(label, pts, ws, cp=cp, **kw)

    def turn(self, label, deg, R, dy=0.0, w1=None, bank=None, cp=False, R1=None, **kw):
        """A banked arc: deg > 0 turns left, deg < 0 right. Climbs or dives dy along it (smoothly)."""
        w0 = self.w
        w1 = w0 if w1 is None else w1
        a = math.radians(deg)
        if R1 is None:
            R = max(R, max(w0, w1) / 2 + 14)  # never tighter than the road is wide (it would fold over itself)
        R1 = R if R1 is None else R1
        arc = abs(a) * (R + R1) / 2
        lft = left_of(self.f)
        sgn = 1.0 if a > 0 else -1.0
        C = add(self.p, mul(lft, sgn * R))
        n = max(8, int(arc / 6))
        prof = J.ramp_profile(n, 0.15)
        pts, ws = [], []
        for i in range(n + 1):
            t = i / n
            th = a * t
            # rotate (p - C) about Y by th (positive = left)
            v = sub(self.p, C)
            c, s = math.cos(th), math.sin(th)
            k_ = (R + (R1 - R) * J.ease_s(t)) / R
            vx, vz = (v[0] * c + v[2] * s) * k_, (-v[0] * s + v[2] * c) * k_
            pts.append((C[0] + vx, self.p[1] + dy * float(prof(t)), C[2] + vz))
            ws.append(w0 + (w1 - w0) * J.ease_s(t))
        assert J.grade_ok(pts), ("turn too steep", label, deg, R, dy)
        if bank is None:
            bank = 0.0  # flat by default: a bank that changes from slab to slab leaves ledges under the wheels
        bk = math.radians(bank) * (-sgn)
        nn = len(pts)
        # ease the bank in and out over a long stretch, in steps small enough that the wheels never feel them
        ramp = max(1, min(nn // 3, int(abs(bk) / 0.008) + 1))
        fb = lambda i: bk * J.ease_s(min(1.0, i / ramp, (nn - 1 - i) / ramp))
        self._lay(label, pts, ws, cp=cp, bank=fb if bank else None, **kw)
        if abs(R1 - R) < 1e-6:
            c, s = math.cos(a), math.sin(a)
            f = self.f
            self.f = flat((f[0] * c + f[2] * s, 0.0, -f[0] * s + f[2] * c))
        else:
            self.f = flat(sub(pts[-1], pts[-2]))
        self.centre = C
        return self

    def orbit(self, label, C, deg, dy=0.0, R1=None, w1=None, bank=None, cp=False, **kw):
        """Carry on round centre C (plan) for deg (> 0 left), easing the radius to R1 and climbing dy."""
        R0 = math.hypot(self.p[0] - C[0], self.p[2] - C[2])
        v = (self.p[0] - C[0], 0.0, self.p[2] - C[2])
        sgn = 1.0 if deg > 0 else -1.0
        # the heading must be (about) the tangent for that way round
        tan = flat(cross(UP, v)) if sgn > 0 else flat(cross(v, UP))
        assert dot(tan, self.f) > 0.97, ("orbit: not heading round", label, dot(tan, self.f))
        self.f = tan
        out = self.turn(label, deg, R0, dy=dy, w1=w1, bank=bank, cp=cp, R1=R1 if R1 is not None else R0, **kw)
        return out

    def roller(self, label, L, amp, n, w1=None, cp=False, **kw):
        """Rolling hills: n humps of height amp (each within the drivable slope)."""
        w0 = self.w
        w1 = w0 if w1 is None else w1
        k = max(8, int(L / 5))
        pts, ws = [], []
        for i in range(k + 1):
            t = i / k
            p = add(self.p, mul(self.f, L * t))
            y = self.p[1] + amp * 0.5 * (1 - math.cos(2 * math.pi * n * t))
            pts.append((p[0], y, p[2]))
            ws.append(w0 + (w1 - w0) * J.ease_s(t))
        assert J.grade_ok(pts), ("rollers too steep", label, L, amp, n)
        return self._lay(label, pts, ws, cp=cp, **kw)

    def connect(self, label, p1, f1, w1=None, lead=40.0, cp=False, k=None, **kw):
        """A smooth road from here to p1 arriving along heading f1 (cubic Hermite in plan, eased height)."""
        w0 = self.w
        w1 = w0 if w1 is None else w1
        f1 = flat(f1)
        p0 = self.p
        D = math.hypot(p1[0] - p0[0], p1[2] - p0[2])
        k = k or D * 0.9
        m0, m1 = mul(self.f, k), mul(f1, k)
        n = max(16, int(D / 5))
        prof = J.ramp_profile(n, 0.2)
        raw = []
        for i in range(n + 1):
            t = i / n
            h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
            x = h00 * p0[0] + h10 * m0[0] + h01 * p1[0] + h11 * m1[0]
            z = h00 * p0[2] + h10 * m0[2] + h01 * p1[2] + h11 * m1[2]
            raw.append((x, z))
        cum = [0.0]
        for a_, c_ in zip(raw, raw[1:]):
            cum.append(cum[-1] + math.dist(a_, c_))
        tot = cum[-1]
        pts, ws = [], []
        for (x, z), c_ in zip(raw, cum):
            u = min(1.0, max(0.0, (c_ - lead) / max(tot - 2 * lead, 1)))
            pts.append((x, p0[1] + (p1[1] - p0[1]) * float(prof(u)), z))
            ws.append(w0 + (w1 - w0) * J.ease_s(c_ / tot))
        assert J.grade_ok(pts), ("connect too steep", label, p0, p1)
        self._lay(label, pts, ws, cp=cp, **kw)
        self.f = f1
        return self

    def spiral(self, label, turns, dy, R, w=None, side=1, core=None, cp=False, **kw):
        """A spiral of `turns` round a centre beside the turtle (side +1 left, -1 right)."""
        if w:
            self.w = w
        lft = left_of(self.f)
        C = add(self.p, mul(lft, side * R))
        if core:
            core(self.b, (C[0], min(self.p[1], self.p[1] + dy), C[2]), R)
        return self.turn(label, side * 360.0 * turns, R, dy, cp=cp, **kw)

    def pad_jump(self, label, D, dy, w_land=60.0, L_land=160.0, rings=0, apex=None, cp=True, src=None, **kw):
        """A straight pad launch along the heading onto a landing road (the pad sits 16 short of the road's end)."""
        b = self.b
        s0 = len(b.samples)
        src = src or add(self.p, mul(self.f, -16))
        tgt = add(src, add(mul(self.f, D), (0, dy, 0)))
        trim_line(b, src, self.f)
        b.line(*src)
        _pad_any(b, src, tgt, apex, rings)
        self._seg(label + "-air", s0)
        self.p = add(tgt, mul(self.f, -L_land * 0.3))
        self.w = w_land
        n0 = len(b.path)
        out = self.straight(label + "-land", L_land, cp=cp, **kw)
        # the landing road's first line points lie under the end of the arc: keep only those past the target
        b.path[n0:] = [p for p in b.path[n0:] if dot(sub(p[:3], tgt), self.f) > 4]
        return out

    def hops(self, label, targets, plat=None, s=56.0, land=None, cp=True):
        """Pad hops through platform tops `targets` (each pad fires straight at the next one); `land`: a final
        (D, dy, w, L) pad onto a landing road along the last hop's heading, else the turtle stops on the last top."""
        b = self.b
        s0 = len(b.samples)
        plat = plat or b.skin.plat
        src = add(self.p, mul(self.f, -16))
        trim_line(b, src, self.f)
        b.line(*src)
        for k, t in enumerate(targets):
            _pad_any(b, src, t)
            plat(b, t, s, self.rng)
            f = flat(sub(t, src))
            nxt = targets[k + 1] if k + 1 < len(targets) else None
            if nxt is not None:
                src = add(t, mul(flat(sub(nxt, t)), min(16.0, s / 2 - 12)))
            else:
                src = add(t, mul(f, min(16.0, s / 2 - 12)))
            self.f = f if nxt is None else flat(sub(nxt, t))
        self._seg(label, s0)
        self.p = targets[-1]
        if land:
            D, dy, w, L = land
            self.pad_jump(label + "-out", D, dy, w_land=w, L_land=L, src=src)
        return self

    def hop_arc(self, label, n, R, deg, dy=0.0, side=1, plat=None, s=56.0, land=None, core=None):
        """Hops round an arc of radius R (deg in total, side +1 left / -1 right), climbing dy at each hop."""
        lft = left_of(self.f)
        C = add(self.p, mul(lft, side * R))
        v = sub(self.p, C)
        tg = []
        for k in range(1, n + 1):
            th = math.radians(deg) * k / n * side
            c, s_ = math.cos(th), math.sin(th)
            tg.append((C[0] + v[0] * c + v[2] * s_, self.p[1] + dy * k, C[2] - v[0] * s_ + v[2] * c))
        if core:
            core(self.b, (C[0], self.p[1], C[2]), R)
        self.centre = C
        return self.hops(label, tg, plat=plat, s=s, land=land)


def _pad_any(b, src, tgt, apex=None, rings=0):
    """SC.pad, for any heading: the pad fires straight at the target."""
    import showcase as SC
    f = flat(sub(tgt, src))
    D = math.hypot(tgt[0] - src[0], tgt[2] - src[2])
    loc = (src[0] + D, tgt[1], src[2])
    T = CF(src) * rot_y(math.atan2(-f[2], f[0])) * CF(mul(src, -1))
    return build_turned(b, lambda: SC.pad(b, src, loc, apex=apex, rings=rings), T)


# ===================================================================== checks
def overlaps(route, clear=34.0, gap_seg=2):
    """Pairs of route segments (and landmarks) that crowd each other: closer in plan than their half widths plus a
    margin while less than `clear` apart in height."""
    b = route.b
    out = []
    S = np.array([s[:4] for s in b.samples], dtype=float) if b.samples else np.zeros((0, 4))
    segs = route.segs
    for i in range(len(segs)):
        li, a0, a1 = segs[i]
        A = S[a0:a1]
        if not len(A):
            continue
        for j in range(i + gap_seg + 1, len(segs)):
            lj, b0, b1 = segs[j]
            B = S[b0:b1]
            if not len(B):
                continue
            if (li, lj) in route.allow or (lj, li) in route.allow:
                continue
            d = np.hypot(A[:, None, 0] - B[None, :, 0], A[:, None, 2] - B[None, :, 2])
            need = (A[:, None, 3] + B[None, :, 3]) / 2 + 12
            dy = np.abs(A[:, None, 1] - B[None, :, 1])
            bad = (d < need) & (dy < clear)
            if bad.any():
                k = np.argwhere(bad)[0]
                out.append((li, lj, [round(v) for v in A[k[0], :3]]))
    for (lab, c, r, ylo, yhi, box) in route.solids:
        for li, a0, a1 in segs:
            if (li, lab) in route.allow or (lab, li) in route.allow:
                continue
            A = S[a0:a1]
            if not len(A):
                continue
            if box:
                dx = np.maximum(np.abs(A[:, 0] - c[0]) - box[0], 0)
                dz = np.maximum(np.abs(A[:, 2] - c[2]) - box[1], 0)
                d = np.hypot(dx, dz) - A[:, 3] / 2 - r
            else:
                d = np.hypot(A[:, 0] - c[0], A[:, 2] - c[2]) - A[:, 3] / 2
            bad = (d < r + 6) & (A[:, 1] > ylo - 30) & (A[:, 1] < yhi + 30)
            if bad.any():
                out.append((li, lab, [round(v) for v in A[np.argmax(bad), :3]]))
    return out


def bounds(b, margin=10.0):
    """Parts reaching outside the level's own X box (the next level starts there)."""
    from factory import is_basepart
    bad = []
    for d in b.level.descendants():
        if not is_basepart(d):
            continue
        cf = CF.from_prop(d.get("CFrame"))
        s = d.get("size")
        ext = abs(cf.x[0]) * s[0] / 2 + abs(cf.y[0]) * s[1] / 2 + abs(cf.z[0]) * s[2] / 2
        if cf.p[0] - ext < X0 - 3 or cf.p[0] + ext > b.X1 + 3:
            bad.append((d.name, round(cf.p[0] - ext - X0), round(cf.p[0] + ext - X0)))
    return bad


def kill_sheets(b, cell=240.0, reach=300.0, below=130.0):
    """Fall triggers on a grid in plan, each under the lowest road within `reach` of it."""
    S = np.array([s[:3] for s in b.samples], dtype=float)
    if not len(S):
        return
    x0, x1 = X0, b.X1
    z0, z1 = S[:, 2].min() - reach, S[:, 2].max() + reach
    nx = int(math.ceil((x1 - x0) / cell))
    nz = int(math.ceil((z1 - z0) / cell))
    for i in range(nx):
        xa, xb = x0 + i * cell, min(x1, x0 + (i + 1) * cell)
        for j in range(nz):
            za, zb = z0 + j * cell, z0 + (j + 1) * cell
            cx, cz = (xa + xb) / 2, (za + zb) / 2
            dx = np.maximum(np.abs(S[:, 0] - cx) - (xb - xa) / 2, 0)
            dz = np.maximum(np.abs(S[:, 2] - cz) - cell / 2, 0)
            near = np.hypot(dx, dz) < reach
            if not near.any():
                continue
            y = S[near, 1].min() - below
            b.part("KillSheet", CF((cx, y, cz)), (xb - xa, 4, cell), (98, 94, 80), parent=b.track, transp=1,
                   collide=False, query=True, touch=True, attrs={"HazardKill": True, "ObbyHazard": "Fall"})
