"""Obby courses: short floating platforms, a jump between nearly every one, a trap or machine on nearly every one.

A course is laid by an Obby: plat() lays a platform (a boost deck: every car is held at exactly B on it, so every
jump off it is the same jump for every car), and the links between platforms throw the car to the next one:
  drop(h)   drive off the end and fall onto a lower platform
  kick(dy)  a curved kicker ramp at the end: fly to a platform at the same height, higher or lower
  pad(dy)   an up pad at the end throws the car straight up; it keeps going forward onto a higher platform
Every link can put the next platform to the left or right (side=), so the car steers in the air. Each landing is
checked from 80% of B (a driver who eased off) to B. Traps: saws, pushers, electric floors, axes, flame jets,
crushers, sweepers, spring mines, grabbing claws...
"""
import math
from geom import CF, deck_frame, axis_frame, look_frame, add, sub, mul, unit, cross, dot, UP
from builder import G, CAR_UP
import route as RT
import rush2 as R2
from skins import Pt, box, cyl, ball

TAU = math.pi * 2
SLOW = 0.8  # the slowest take-off every landing must take (a driver easing off before a lip)


def right_of(f):
    return mul(RT.left_of(f), -1)


class Obby:
    def __init__(self, r, B=230.0):
        self.r = r
        self.b = r.b
        self.B = float(B)
        self.need = 0.0  # how long the next platform must be (its landing zone)
        self.trim = None  # (landing point, heading): the next platform's line starts past it
        self.came_from = 1  # the side of the platform the last flight came in over: the flag goes on the other

    # ------------------------------------------------------------ platforms
    def plat(self, label, L, w, traps=(), cp=False, boost=True, dy=0.0):
        """A platform L long and w wide at the turtle (straight on, ramping dy). traps: [(fn, distance, kw)]."""
        r = self.r
        L = max(L, self.need)
        self.need = 0.0
        r.w = w
        n0 = len(self.b.path)
        if boost:
            R2.boost_deck(r, label, L, self.B, dy=dy, w=w)
        else:
            r.straight(label, L, dy=dy, w1=w, lead=min(20.0, L / 4))
        if cp:
            # near the start (clear of the traps further on), the flag on the side the flight in does not cross
            pts = r.last[0]
            fl = RT.flat(sub(pts[-1], pts[0]))
            q = add(pts[0], mul(fl, 16.0))
            self.b.checkpoint(q[0], q[1], q[2], w, fl, flag_side=self.came_from)
        self.came_from = 1
        if self.trim:
            tgt, f = self.trim
            self.b.path[n0:] = [p for p in self.b.path[n0:] if dot(sub(p[:3], tgt), f) > 6]
            self.trim = None
        for k, t in enumerate(traps):
            fn, d = t[0], t[1]
            kw = t[2] if len(t) > 2 else {}
            r.along(fn, [d if d > 1 else d * L], i0=k, **kw)
        return self

    # ------------------------------------------------------------ links
    def _land(self, lip, v, dy, f, side):
        """Where a flight from lip with velocity v (world) comes down at height lip.y + dy."""
        p, t = R2.fly(lip, v, lambda q: lip[1] + dy)
        return p

    def drop(self, h, side=0.0, label="Drop"):
        """Drive off the end and fall h onto the next platform (side: it is that far to the right)."""
        b, r, B = self.b, self.r, self.B
        lip, f = r.p, r.f
        T = math.sqrt(2 * h / G)
        d_hi, d_lo = B * T, SLOW * B * T
        # with a sideways offset the car flies the diagonal: the distance along f shrinks a little
        k = 1.0 / math.sqrt(1.0 + (side / max(d_hi, 1.0)) ** 2)
        start = max(10.0, d_lo * k - 34.0)
        import rush
        rush.hazard_lip(b, lip, f, r.w)
        tgt = add(lip, add(mul(f, d_hi * k), add(mul(right_of(f), side), (0, -h, 0))))
        fd = RT.flat(sub(tgt, lip))
        b.line(*lip)
        b.arc((lip[0], lip[1] + CAR_UP, lip[2]), (fd[0] * B, 0.0, fd[2] * B), until_y=tgt[1] + CAR_UP, step=0.04)
        b.jumps.append(("drop", lip, tgt, B, 0.0))
        self.need = d_hi * k - start + 90.0
        self.came_from = 1 if side >= 0 else -1
        r.p = add(lip, add(mul(f, start), add(mul(right_of(f), side * (1 + SLOW) / 2), (0, -h, 0))))
        self.trim = (tgt, f)
        return self

    def kick(self, dy=0.0, deg=None, side=0.0, label="Kick"):
        """A kicker at the platform's end throws the car onto the next platform dy higher (or lower)."""
        b, r, B = self.b, self.r, self.B
        if dy > 4:
            # (a kicker cannot throw a slower car up onto a higher platform reliably: the pad can)
            return self.pad(dy, side=side, label=label)
        deg = deg or 16.0
        base_y = r.p[1]
        lip, dvec = R2.kicker(r, label + " Kicker", deg, L=max(30.0, deg * 1.8), w=r.w, rails=False)
        f = r.f
        for _ in range(12):
            vh = [mul(dvec, B), mul(dvec, SLOW * B)]
            p_hi = self._land(lip, vh[0], base_y + dy - lip[1], f, side)
            p_lo = self._land(lip, vh[1], base_y + dy - lip[1], f, side)
            if p_lo is not None and dot(sub(p_lo, lip), f) > 60:
                break
            deg += 3.0
            dvec = (f[0] * math.cos(math.radians(deg)), math.sin(math.radians(deg)), f[2] * math.cos(math.radians(deg)))
        d_hi, d_lo = dot(sub(p_hi, lip), f), dot(sub(p_lo, lip), f)
        k = 1.0 / math.sqrt(1.0 + (side / max(d_hi, 1.0)) ** 2)
        start = max(20.0, d_lo * k - 34.0)
        top = add(lip, add(mul(f, d_hi * k), add(mul(right_of(f), side), (0, base_y + dy - lip[1], 0))))
        fd = RT.flat(sub(top, lip))
        v = (fd[0] * B * dvec_h(dvec), B * dvec[1], fd[2] * B * dvec_h(dvec))
        b.line(*lip)
        b.arc((lip[0], lip[1] + CAR_UP, lip[2]), v, until_y=top[1] + CAR_UP, step=0.04)
        b.jumps.append(("kick", lip, top, B * dvec_h(dvec), B * dvec[1]))
        self.need = d_hi * k - start + 90.0
        self.trim = (top, f)
        self.came_from = 1 if side >= 0 else -1
        r.p = add(lip, add(mul(f, start), add(mul(right_of(f), side * (1 + SLOW) / 2), (0, base_y + dy - lip[1], 0))))
        return self

    def pad_range(self, dy, apex=None):
        """(start, far) along the heading of the platform an up pad of dy would throw the car onto."""
        B = self.B
        apex = apex or max(dy + 45.0, 60.0)
        while True:
            V = math.sqrt(2 * G * apex)
            disc = math.sqrt(max(V * V - 2 * G * (dy + 4), 0.0))
            t_up = (V - disc) / G if dy > 0 else 0.0
            t_dn = (V + math.sqrt(max(V * V - 2 * G * dy, 0.0))) / G
            lo_edge = B * t_up + 24.0
            if lo_edge <= SLOW * B * t_dn - 44:
                return SLOW * B * t_dn - 48.0, B * t_dn
            apex *= 1.1

    def pad(self, dy, side=0.0, label="Pad", apex=None):
        """An up pad at the platform's end: straight up, still going forward, onto a platform dy higher."""
        b, r, B = self.b, self.r, self.B
        lip, f = r.p, r.f
        src = add(lip, mul(f, -14))
        apex = apex or max(dy + 45.0, 60.0)
        while True:
            V = math.sqrt(2 * G * apex)
            disc = math.sqrt(max(V * V - 2 * G * (dy + 4), 0.0))
            t_up = (V - disc) / G if dy > 0 else 0.0
            t_dn = (V + math.sqrt(max(V * V - 2 * G * dy, 0.0))) / G
            lo_edge = B * t_up + 24.0          # the fastest car must clear the near edge on the way up
            d_lo = SLOW * B * t_dn             # the slowest must still reach it on the way down
            kk = 1.0 / math.sqrt(1.0 + (side / max(B * t_dn, 1.0)) ** 2)
            if lo_edge <= d_lo * kk - 44:
                break
            apex *= 1.1
        RT.trim_line(b, src, f)
        b.line(*src)
        b.part("LaunchPad", look_frame((src[0], src[1] + 0.3, src[2]), f), (r.w - 2, 0.6, 26), (255, 196, 60), "Slate",
               parent=b.track, transp=1, collide=False, query=False,
               attrs={"CarLaunchPad": True, "LaunchExact": True, "LaunchVertical": float(V), "BoosterUp": True})
        b.skin.pad_art(b, src, f)
        d_hi = B * t_dn
        k = 1.0 / math.sqrt(1.0 + (side / max(d_hi, 1.0)) ** 2)
        start = max(lo_edge, d_lo * k - 34.0) - 14.0
        top = add(src, add(mul(f, d_hi * k), add(mul(right_of(f), side), (0, dy, 0))))
        fd = RT.flat(sub(top, src))
        b.arc((src[0], src[1] + CAR_UP, src[2]), (fd[0] * B, V, fd[2] * B), until_y=top[1] + CAR_UP, step=0.04)
        b.jumps.append(("oup", src, top, B, V))
        self.need = d_hi * k - start + 90.0
        self.trim = (top, f)
        self.came_from = 1 if side >= 0 else -1
        r.p = add(lip, add(mul(f, start), add(mul(right_of(f), side * (1 + SLOW) / 2), (0, dy, 0))))
        return self


def dvec_h(d):
    return math.sqrt(d[0] ** 2 + d[2] ** 2)


# ===================================================================== traps (built at c heading +X across a road w wide)
def saw(b, c, w, i, period=2.2, d=26.0):
    """A spinning saw blade rolling from side to side across the platform (SHREDDED)."""
    x, y, z = c
    root = b.prop_root("Saw")
    z0 = z - w / 2 + d / 2 + 1
    amp = max(w - d - 2, 1.0)
    slide = b.rig(root, "Slide", axis_frame((x, y + d / 2 + 1, z0), (0, 0, 1)), amp, period, phase=(i * 0.37) % 1,
                  name="SawSlide")
    hub = (x, y + d / 2 + 1, z0)
    spin = b.rig(slide, "Spin", axis_frame(hub, (1, 0, 0)), 1.6, 1, name="SawSpin")
    cyl(b, "SawBlade", hub, 1.4, d, (190, 196, 205), "Metal", spin, query=True, attrs={"ObbyHazard": "Shred"}, refl=0.4)
    for k in range(12):
        a = TAU * k / 12
        dd = (0.0, math.cos(a), math.sin(a))
        q = add(hub, mul(dd, d / 2 + 1.2))
        Pt(b, "SawTooth", CF(q, (1, 0, 0), dd, cross((1, 0, 0), dd)), (1.2, 3.2, 3.2), (220, 225, 235), "Metal", spin)
    cyl(b, "SawHub", hub, 2.2, d * 0.28, (230, 40, 40), "Neon", spin)
    # the slot it runs in
    Pt(b, "SawSlot", CF((x, y + 0.08, z)), (3, 0.14, w - 2), (30, 30, 34), "SmoothPlastic", b.scenery)


def pusher(b, c, w, i, period=1.8):
    """A piston that punches across the platform from one side: be past it or get shoved off the edge."""
    x, y, z = c
    s = 1 if i % 2 == 0 else -1
    L = 30.0
    root = b.prop_root("Pusher")
    home = (x, y + 9, z - s * (w / 2 + L / 2 + 1))
    rig = b.rig(root, "Slide", axis_frame(home, (0, 0, s)), w * 0.75, period, phase=(i * 0.29) % 1,
                keys="0:0 0.45:0 0.55:1 0.7:1 0.95:0", name="Punch")
    sk = b.skin
    Pt(b, "PusherBlock", CF(home), (34, 18, L), sk.danger, "SmoothPlastic", rig, query=True, attrs={"ObbyHazard": "Knock"})
    Pt(b, "PusherFace", CF(add(home, (0, 0, s * (L / 2 + 0.3)))), (36, 20, 0.6), (255, 220, 60), "Neon", rig)
    Pt(b, "PusherHousing", CF((x, y + 10, z - s * (w / 2 + L + 6))), (40, 24, 16), sk.body, sk.body_mat, b.scenery,
       collide=True)


def zap_floor(b, c, w, i, L=36.0, period=1.6, on=0.6, phase=None):
    """An electric floor: lethal while it crackles (FRIED). Cross between the pulses."""
    x, y, z = c
    ph = (i * 0.31) % 1 if phase is None else phase
    a = {"ObbyHazard": "Zap", "ZapFX": True, "ZapPeriod": float(period), "ZapOn": float(on), "ZapPhase": float(ph)}
    Pt(b, "ZapGrid", CF((x, y + 0.15, z)), (L, 0.2, w), (90, 200, 255), "Neon", b.hazards, query=False, attrs=dict(a))
    b.part("ZapZone", CF((x, y + 4, z)), (L, 8, w), (90, 200, 255), parent=b.hazards, transp=1, collide=False,
           query=True, attrs=a)
    for s in (-1, 1):
        cyl(b, "ZapPylon", (x, y + 10, z + s * (w / 2 + 3)), 20, 4, (60, 60, 70), "Metal", b.scenery, collide=True)
        ball(b, "ZapOrb", (x, y + 21, z + s * (w / 2 + 3)), 6, (90, 200, 255), "Neon", b.scenery)
    for k in range(int(L // 6)):
        Pt(b, "ZapLine", CF((x - L / 2 + 3 + k * 6, y + 0.3, z)), (0.6, 0.1, w - 2), (230, 250, 255), "Neon", b.scenery)


def axe(b, c, w, i, H=60.0, period=2.6):
    """A giant axe swinging across the platform (SHREDDED)."""
    x, y, z = c
    pivot = (x, y + H, z)
    root = b.prop_root("Axe")
    rig = b.rig(root, "Hinge", axis_frame(pivot, (1, 0, 0)), 60, period, phase=(i * 0.23) % 1,
                keys="0:0 0.25:1 0.5:0 0.75:-1", name="AxeSwing")
    sk = b.skin
    cyl(b, "AxeShaft", (x, y + H / 2 + 6, z), H - 10, 3, (110, 80, 50), "Wood", rig, axis=(0, 1, 0))
    cyl(b, "AxeBlade", (x, y + 13, z), 2, 24, (200, 205, 215), "Metal", rig, axis=(1, 0, 0), query=True,
        attrs={"ObbyHazard": "Shred"}, refl=0.4)
    cyl(b, "AxeEdge", (x, y + 13, z), 1.4, 26.5, (255, 70, 60), "Neon", rig, axis=(1, 0, 0))
    cyl(b, "AxeHub", (x, y + 13, z), 3, 7, (60, 60, 66), "Metal", rig, axis=(1, 0, 0))
    for s in (-1, 1):
        cyl(b, "AxePost", (x, y + H / 2, z + s * (w / 2 + 4)), H + 6, 5, sk.body, sk.body_mat, b.scenery, collide=True)
    Pt(b, "AxeBeam", CF((x, y + H + 2, z)), (6, 6, w + 14), sk.body, sk.body_mat, b.scenery)


def flames(b, c, w, i, period=1.4, on=0.55, n=3):
    """Flame jets bursting out of floor vents across the platform on a beat (FRIED while they burn)."""
    x, y, z = c
    a = {"ObbyHazard": "Zap", "ZapFX": True, "ZapPeriod": float(period), "ZapOn": float(on),
         "ZapPhase": float((i * 0.41) % 1)}
    for k in range(n):
        zz = z - w / 2 + w * (k + 0.5) / n
        Pt(b, "Vent", CF((x, y + 0.1, zz)), (10, 0.3, w / n - 2), (40, 36, 34), "Metal", b.scenery)
        for j, (h, d) in enumerate(((10, 9), (22, 6.5), (32, 3.5))):
            cyl(b, "Flame", (x, y + h - 4, zz), 10, d, (255, 140 - j * 40, 30), "Neon", b.hazards, query=False,
                attrs=dict(a), axis=(0, 1, 0))
    b.part("FlameZone", CF((x, y + 14, z)), (10, 28, w), (255, 120, 30), parent=b.hazards, transp=1, collide=False,
           query=True, attrs=a)


def mine(b, c, w, i, n=3):
    """Spring mines: drive over one and it throws you sky-high (and maybe off the edge)."""
    x, y, z = c
    for k in range(n):
        zz = z - w / 2 + w * (k + 0.5) / n + (6 if i % 2 else -6)
        cyl(b, "MineBase", (x, y + 1, zz), 2, 10, (50, 50, 56), "Metal", b.scenery)
        cyl(b, "MineCap", (x, y + 2.4, zz), 1.2, 7, (255, 60, 60), "Neon", b.hazards, query=True,
            attrs={"ObbyHazard": "Bounce"})


def claw(b, c, w, i, H=50.0, period=2.4):
    """A grabbing claw that drops onto the platform and snatches whatever is under it (CAUGHT)."""
    x, y, z = c
    rc = (x, y + H, z)
    b.skin.press_frame(b, x, y, z, w, H) if hasattr(b.skin, "press_frame") else None
    root = b.prop_root("Claw")
    rig = b.rig(root, "Slide", axis_frame(rc, (0, -1, 0)), H - 8, period, phase=(i * 0.27) % 1,
                keys="0:0 0.45:0 0.55:1 0.7:1 0.95:0", name="ClawDrop")
    cyl(b, "ClawHub", rc, 8, 14, (200, 200, 210), "Metal", rig, axis=(0, 1, 0))
    for k in range(3):
        a = TAU * k / 3
        d = (math.cos(a), 0.0, math.sin(a))
        Pt(b, "ClawFinger", CF(add(rc, add(mul(d, 9), (0, -9, 0)))), (4, 16, 4), (220, 220, 230), "Metal", rig)
    Pt(b, "ClawGrab", CF(add(rc, (0, -12, 0))), (24, 10, w * 0.7), (255, 80, 80), "Neon", rig, query=True, transp=0.7,
       attrs={"ObbyHazard": "Grab"})


def crusher(b, c, w, i, **kw):
    import epic_kit as EK
    EK.ob_press(b, c, w, i, **kw)


def sweeper(b, c, w, i, **kw):
    import epic_kit as EK
    EK.ob_sweeper(b, c, w, i, **kw)


def bumpers(b, c, w, i, **kw):
    import epic_kit as EK
    EK.ob_bumpers(b, c, w, i, **kw)


def lasers(b, c, w, i, period=1.6, **kw):
    import epic_kit as EK
    EK.ob_gate(b, c, w, i, period=period, **kw)
