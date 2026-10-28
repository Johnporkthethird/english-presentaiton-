"""LevelBuilder: turns high level course pieces (roads, gaps, pads, rigs) into place instances."""
import math
import rbxl
from geom import CF, deck_frame, look_frame, axis_frame, add, sub, mul, unit, length, cross, dot, lerp, UP, rot_y, rot_axis
from factory import MAT, transform_tree

G = 196.2
X0 = 1903.0
ZC = 24068.69921875
Y0 = 1120.0281007289886  # road top at every level join
CAR_UP = 6.0             # racing line height over the road
SPAWN_UP = 10.0          # checkpoint pose height over the road
THICK = 4.0


def hsv_col(h, s, v):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def col(c):
    return (int(max(0, min(255, c[0]))), int(max(0, min(255, c[1]))), int(max(0, min(255, c[2]))))


def mix(a, b, t):
    return col((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t))


class LevelBuilder:
    def __init__(self, fac, level, theme, rng, length_total, templates):
        self.fac = fac
        self.level = level
        self.theme = theme
        self.rng = rng
        self.L = length_total
        self.X1 = X0 + length_total
        self.tpl = templates  # cloned asset models: flag, pad, boost
        self.track = self.model("Track", level)
        self.roads = self.model("Road", level)
        self.hazards = self.model("Hazards", level)
        self.scenery = self.model("Scenery", level)
        self.path = []        # (x, y, z) racing line, already at car height
        self.samples = []     # road samples (x, ytop, z, w) for kill sheets / scenery
        self.cp_count = 0
        self.cps = []
        self.count = 0
        self.gaps = []        # (x0, x1) stretches flown over (arcs)
        self.jumps = []       # (kind, start, target, H, V) for the validator
        self.notes = []
        self.ylo, self.yhi = Y0 - 420, Y0 + 420

    # ------------------------------------------------------------ raw instances
    def model(self, name, parent, attrs=None):
        m = self.fac.blank("Model")
        m.set("Name", name.encode())
        if "PrimaryPart" in m.props:
            m.props["PrimaryPart"] = (0x13, None)
        m.props["WorldPivotData"] = (0x1E, (CF((X0, Y0, ZC)).to_prop(), True))
        if attrs:
            rbxl.set_attrs(m, attrs)
        m.set_parent(parent)
        return m

    def folder(self, name, parent):
        f = self.fac.blank("Folder")
        f.set("Name", name.encode())
        f.set_parent(parent)
        return f

    def part(self, name, cf, size, color, mat="SmoothPlastic", parent=None, transp=0.0, collide=True,
             query=None, touch=False, attrs=None, cls="Part", shape=1, shadow=False, refl=0.0):
        p = self.fac.blank(cls)
        p.set("Name", name.encode())
        p.set("CFrame", cf.to_prop())
        p.set("size", (float(size[0]), float(size[1]), float(size[2])))
        p.set("Color3uint8", col(color))
        p.set("Material", MAT[mat] if isinstance(mat, str) else mat)
        p.set("Transparency", float(transp))
        p.set("CanCollide", bool(collide))
        p.set("CanQuery", bool(collide if query is None else query))
        p.set("CanTouch", bool(touch))
        p.set("CastShadow", bool(shadow))
        p.set("Reflectance", float(refl))
        p.set("Anchored", True)
        if cls == "Part":
            p.set("shape", shape)
        if attrs:
            rbxl.set_attrs(p, attrs)
        p.set_parent(parent if parent is not None else self.scenery)
        self.count += 1
        return p

    def light(self, parent, color, brightness=2.0, rng=40.0, cls="PointLight"):
        l = self.fac.blank(cls)
        l.set("Name", cls.encode())
        l.set("Color", tuple(c / 255.0 for c in col(color)))
        l.set("Brightness", float(brightness))
        l.set("Range", float(rng))
        if "Shadows" in l.props:
            l.set("Shadows", False)
        l.set("Enabled", True)
        l.set_parent(parent)
        return l

    def texture(self, part, color, transp=0.5, tile=16.0, face=1, attrs=None):
        t = self.fac.blank("Texture")
        t.set("Color3", tuple(c / 255.0 for c in col(color)))
        t.set("Transparency", float(transp))
        t.set("StudsPerTileU", float(tile))
        t.set("StudsPerTileV", float(tile))
        t.set("Face", face)
        if attrs:
            rbxl.set_attrs(t, attrs)
        t.set_parent(part)
        return t

    # ------------------------------------------------------------ racing line
    def line(self, x, ytop, z):
        self.path.append((x, ytop + CAR_UP, z, "r"))

    def arc(self, p0, v, g=G, until_y=None, until_x=None, step=0.12):
        """Sample a ballistic arc for the racing line (p0 at car height)."""
        x, y, z = p0
        vx, vy, vz = v
        t = 0.0
        pts = []
        while t < 8:
            t += step
            px, py, pz = x + vx * t, y + vy * t - 0.5 * g * t * t, z + vz * t
            if until_x is not None and px >= until_x:
                break
            if until_y is not None and vy - g * t < 0 and py <= until_y:
                break
            pts.append((px, py, pz, "a"))
        self.path.extend(pts)
        if pts:
            self.gaps.append((x, pts[-1][0]))
        return pts[-1] if pts else p0

    # ------------------------------------------------------------ road
    def road(self, x0, x1, fy, fz, fw, step=8.0, bank=None, style=None, edge=True, rails=False,
             line=True, name="Deck", extra=None):
        """A road along x0..x1: centre (z) and top (y) are functions of x, width fw(x).
        Samples are merged into straight slabs where the direction holds."""
        th = self.theme
        style = style or {}
        n = max(1, int(math.ceil((x1 - x0) / step)))
        xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
        pts = [(x, fy(x), fz(x), fw(x)) for x in xs]
        for (x, y, z, w) in pts:
            self.samples.append((x, y, z, w))
        if line:
            last = -1e9
            for (x, y, z, w) in pts:
                if x - last >= 30 or x == pts[-1][0]:
                    self.line(x, y, z)
                    last = x
        # merge into slabs
        slabs = []
        i = 0
        while i < len(pts) - 1:
            j = i + 1
            d0 = unit(sub(pts[j][:3], pts[i][:3]))
            while j + 1 < len(pts):
                d1 = unit(sub(pts[j + 1][:3], pts[j][:3]))
                if dot(d0, d1) < 0.99995 or abs(pts[j + 1][3] - pts[i][3]) > 0.5 or (j + 1 - i) * step > 400:
                    break
                if bank and abs(bank(pts[j + 1][0]) - bank(pts[i][0])) > 0.02:
                    break
                j += 1
            slabs.append((pts[i], pts[j]))
            i = j
        out = []
        for a, b in slabs:
            pa, pb = a[:3], b[:3]
            w = (a[3] + b[3]) / 2
            seg = sub(pb, pa)
            L = length(seg)
            if L < 0.01:
                continue
            bk = bank((a[0] + b[0]) / 2) if bank else 0.0
            fr = deck_frame(lerp(pa, pb, 0.5), seg, bank=bk)
            top_mid = fr.p
            centre = sub(top_mid, mul(fr.y, THICK / 2))
            over = 1.2
            cf = CF(centre, fr.x, fr.y, fr.z)
            mat = style.get("mat", th["road_mat"])
            rc = style.get("color", th["road"])
            hue = ((a[0] + b[0]) / 2 - X0) / 420.0
            if th.get("rainbow_road") and "color" not in style:
                rc = hsv_col(hue, 0.75, 0.95)
            p = self.part(name, cf, (w, THICK, L + over), rc, mat, parent=self.roads, collide=True,
                          attrs=style.get("attrs"), refl=style.get("refl", 0.0))
            if style.get("texture", th.get("texture")):
                self.texture(p, style.get("tex_color", th["tex"]), transp=th.get("tex_transp", 0.55),
                             tile=th.get("tex_tile", 16.0), attrs=style.get("tex_attrs"))
            if edge:
                ec = style.get("edge", th["edge"])
                if th.get("rainbow_edges") and "edge" not in style:
                    ec = hsv_col(hue, 1.0, 1.0)
                for s in (-1, 1):
                    epos = add(top_mid, add(mul(fr.x, s * (w / 2 - 1.0)), mul(fr.y, 0.3)))
                    self.part("EdgeGlow", CF(epos, fr.x, fr.y, fr.z), (2.0, 0.6, L + over), ec, "Neon",
                              parent=self.roads, collide=False, query=False)
            if rails:
                rc2 = style.get("rail", th["accent"])
                for s in (-1, 1):
                    rpos = add(top_mid, add(mul(fr.x, s * (w / 2 + 1.0)), mul(fr.y, 1.5)))
                    self.part("Curb", CF(rpos, fr.x, fr.y, fr.z), (2.0, 3.0 + THICK, L + over), rc2,
                              th.get("rail_mat", "Metal"), parent=self.roads, collide=True)
            if th.get("keel"):
                kpos = sub(top_mid, mul(fr.y, THICK + 3))
                self.part("Keel", CF(kpos, fr.x, fr.y, fr.z), (w * 0.55, 6, L + over), th["keel"],
                          th.get("keel_mat", "Metal"), parent=self.roads, collide=False, query=False)
            out.append((p, fr, w, L))
            if extra:
                extra(p, fr, w, L)
        return out

    def flat(self, x0, x1, y, z, w, **kw):
        return self.road(x0, x1, lambda x: y, lambda x: z, lambda x: w, **kw)

    def slab(self, cf_top, w, L, color=None, mat=None, name="Deck", parent=None, attrs=None, edge=True,
             collide=True, transp=0.0):
        """One free slab given its top-centre frame (deck convention)."""
        th = self.theme
        centre = sub(cf_top.p, mul(cf_top.y, THICK / 2))
        p = self.part(name, CF(centre, cf_top.x, cf_top.y, cf_top.z), (w, THICK, L), color or th["road"],
                      mat or th["road_mat"], parent=parent or self.roads, collide=collide, attrs=attrs, transp=transp)
        if edge:
            for s in (-1, 1):
                epos = add(cf_top.p, add(mul(cf_top.x, s * (w / 2 - 0.7)), mul(cf_top.y, 0.25)))
                self.part("EdgeGlow", CF(epos, cf_top.x, cf_top.y, cf_top.z), (1.4, 0.5, L), th["edge"], "Neon",
                          parent=parent or self.roads, collide=False, query=False)
        return p

    # ------------------------------------------------------------ course furniture
    def checkpoint(self, x, y, z, w, fwd=(1, 0, 0)):
        self.cp_count += 1
        idx = round(0.05 * self.cp_count, 4)
        if idx >= 0.96:
            self.cp_count -= 1
            return
        f = unit((fwd[0], 0, fwd[2]))
        pose = look_frame((x, y + SPAWN_UP, z), f)
        trig = deck_frame((x, y + 30, z), f)
        self.part("CarObbyCheckpoint", trig, (max(w, 48), 60, 24), (255, 196, 60), parent=self.track,
                  transp=1, collide=False, query=True, touch=True,
                  attrs={"CheckpointCFrame": ("CFrame", pose.p, pose.rows()), "CheckpointIndex": idx})
        # the flag at the road's right edge
        flag = self.fac.clone(self.tpl["flag"], self.level)
        T = look_frame((x, y + SPAWN_UP, z), f) * self.tpl["flag_ref"].inverse()
        transform_tree(flag, T)
        a = rbxl.attrs(flag)
        a["CpIndex"] = idx
        rbxl.set_attrs(flag, a)
        self.cps.append((x, y, z, idx))

    def boost(self, x, y, z, fwd=(1, 0, 0), speed=None, length_=48.0):
        fr = deck_frame((x, y + 0.15, z), fwd)
        sp = speed or self.theme.get("boost_speed", 230)
        self.part("BoostPad", fr, (24, 0.2, length_), (163, 162, 165), "Plastic", parent=self.track, transp=1,
                  collide=False, query=False, attrs={"BoostSpeed": float(sp), "BoostStack": True})
        m = self.fac.clone(self.tpl["boost"], self.level)
        T = deck_frame((x, y, z), fwd) * self.tpl["boost_ref"].inverse()
        transform_tree(m, T)
        return m

    def launch(self, start, target, apex=None, fwd=None, pad_w=40.0, visual=True):
        """An exact launch pad at `start` (road top) landing the car at `target` (road top).
        Returns (H, V, T)."""
        dx, dz = target[0] - start[0], target[2] - start[2]
        D = math.hypot(dx, dz)
        dy = target[1] - start[1]
        if apex is None:
            apex = max(dy, 0) + max(30.0, D * 0.18)
        apex = max(apex, dy + 12)
        V = math.sqrt(2 * G * apex)
        T = (V + math.sqrt(max(V * V - 2 * G * dy, 0))) / G
        H = D / T
        f = (dx / D, 0.0, dz / D)
        lf = look_frame((start[0], start[1] + 0.3, start[2]), f)
        self.part("LaunchPad", lf, (pad_w, 0.6, 30), (255, 196, 60), "Slate", parent=self.track, transp=1,
                  collide=False, query=False,
                  attrs={"CarLaunchPad": True, "LaunchExact": True, "LaunchForward": ("Vector3",) + f,
                         "LaunchHorizontal": float(H), "LaunchVertical": float(V), "AutoJumpTarget":
                         ("Vector3", target[0], target[1], target[2]), "AutoJumpSolved": True})
        if visual:
            m = self.fac.clone(self.tpl["pad"], self.level)
            T2 = look_frame((start[0], start[1], start[2]), f) * self.tpl["pad_ref"].inverse()
            transform_tree(m, T2)
        # racing line: the arc
        self.line(start[0], start[1], start[2])
        self.arc((start[0], start[1] + CAR_UP, start[2]), (f[0] * H, V, f[2] * H), until_y=target[1] + CAR_UP)
        self.jumps.append(("pad", start, target, H, V))
        return H, V, T

    def jump_arc(self, x0, y0, z0, x1, y1, z1, v=115.0, up=140.0):
        """Racing line over a jump-key gap (the path rivals follow)."""
        D = math.hypot(x1 - x0, z1 - z0)
        dy = y1 - y0
        V = up
        disc = V * V - 2 * G * dy
        T = (V + math.sqrt(max(disc, 1))) / G
        H = D / T
        f = ((x1 - x0) / D, 0, (z1 - z0) / D)
        self.arc((x0, y0 + CAR_UP, z0), (f[0] * H, V, f[2] * H), until_y=y1 + CAR_UP)
        self.jumps.append(("key", (x0, y0, z0), (x1, y1, z1), H, V))

    # ------------------------------------------------------------ moving props (ObbyPropAnim rigs)
    def prop_root(self, name, parent=None):
        return self.model(name, parent or self.hazards, {"ObbyProp": True})

    def rig(self, root, kind, pivot_cf, amount, period, phase=0.0, keys=None, name="Rig"):
        attrs = {"PropMotion": kind, "PropAmount": float(amount), "PropPeriod": float(period), "PropPhase": float(phase)}
        if keys:
            attrs["PropKeys"] = keys
        m = self.model(name, root, attrs)
        self.part("Pivot", pivot_cf, (1, 1, 1), (255, 255, 255), parent=m, transp=1, collide=False, query=False)
        return m

    # ------------------------------------------------------------ finishing
    def kill_sheets(self):
        """Fall triggers under the whole course, in 200-stud buckets, 120 under the lowest road near."""
        if not self.samples:
            return
        xs = sorted(self.samples, key=lambda s: s[0])
        x = X0
        while x < self.X1 - 0.01:
            xb = min(x + 200, self.X1)
            near = [s for s in xs if x - 160 <= s[0] <= xb + 160]
            if near:
                ymin = min(s[1] for s in near)
                zmin = min(s[2] - s[3] / 2 for s in near) - 300
                zmax = max(s[2] + s[3] / 2 for s in near) + 300
                cf = CF(((x + xb) / 2, ymin - 130, (zmin + zmax) / 2))
                self.part("KillSheet", cf, (xb - x, 4, zmax - zmin), (98, 94, 80), parent=self.track, transp=1,
                          collide=False, query=True, touch=True, attrs={"HazardKill": True, "ObbyHazard": "Fall"})
            x = xb

    def course_path_ordered(self):
        """The racing line in travel order (loops and spirals double back in x)."""
        out, last = [], None
        for p in self.path:
            if last is not None and math.dist(p[:3], last[:3]) < 6:
                continue
            out.append(p)
            last = p
        return "|".join("%.2f,%.1f,%.1f" % p[:3] for p in out), out

    def course_path(self):
        """The racing line: road points, minus any that fall inside a flown arc (an island's far end under
        its own launch), sorted along the course."""
        pts = []
        for p in self.path:
            if p[3] == "r" and any(a + 2 < p[0] < b - 2 for a, b in self.gaps):
                continue
            pts.append(p)
        pts.sort(key=lambda p: p[0])
        out, last = [], None
        for p in pts:
            if last is not None and p[0] - last[0] < 6:
                continue
            out.append(p)
            last = p
        return "|".join("%.2f,%.1f,%.1f" % p[:3] for p in out)
