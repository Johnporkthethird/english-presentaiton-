"""Vector / CFrame helpers (Roblox conventions: right = look x up, columns X=right, Y=up, Z=-look)."""
import math

ROT_IDS = {
    2: ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    3: ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    5: ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
    6: ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
    7: ((0, 1, 0), (1, 0, 0), (0, 0, -1)),
    9: ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
    10: ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
    12: ((0, 0, -1), (1, 0, 0), (0, -1, 0)),
    13: ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
    14: ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
    16: ((0, -1, 0), (0, 0, -1), (1, 0, 0)),
    17: ((0, 0, 1), (0, -1, 0), (1, 0, 0)),
    20: ((-1, 0, 0), (0, 1, 0), (0, 0, -1)),
    21: ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    23: ((-1, 0, 0), (0, -1, 0), (0, 0, 1)),
    24: ((-1, 0, 0), (0, 0, -1), (0, -1, 0)),
    25: ((0, 1, 0), (-1, 0, 0), (0, 0, 1)),
    27: ((0, 0, -1), (-1, 0, 0), (0, 1, 0)),
    28: ((0, -1, 0), (-1, 0, 0), (0, 0, -1)),
    30: ((0, 0, 1), (-1, 0, 0), (0, -1, 0)),
    31: ((0, 1, 0), (0, 0, -1), (-1, 0, 0)),
    32: ((0, 0, 1), (0, 1, 0), (-1, 0, 0)),
    34: ((0, -1, 0), (0, 0, 1), (-1, 0, 0)),
    35: ((0, 0, -1), (0, -1, 0), (-1, 0, 0)),
}


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def length(a):
    return math.sqrt(dot(a, a))


def unit(a):
    l = length(a)
    return (a[0] / l, a[1] / l, a[2] / l) if l > 1e-9 else (0.0, 0.0, 0.0)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


UP = (0.0, 1.0, 0.0)


class CF:
    """Rotation as three column vectors (right, up, back) + position."""
    __slots__ = ("x", "y", "z", "p")

    def __init__(self, p, x=(1, 0, 0), y=(0, 1, 0), z=(0, 0, 1)):
        self.p = tuple(float(v) for v in p)
        self.x, self.y, self.z = tuple(x), tuple(y), tuple(z)

    @staticmethod
    def from_rows(rows, p):
        r = rows
        return CF(p, (r[0], r[3], r[6]), (r[1], r[4], r[7]), (r[2], r[5], r[8]))

    @staticmethod
    def from_prop(v):
        (rid, m), p = v
        if rid == 0:
            return CF.from_rows(m, p)
        rr = ROT_IDS[rid]
        return CF.from_rows(rr[0] + rr[1] + rr[2], p)

    def rows(self):
        return (self.x[0], self.y[0], self.z[0], self.x[1], self.y[1], self.z[1], self.x[2], self.y[2], self.z[2])

    def to_prop(self):
        return ((0, tuple(float(v) for v in self.rows())), self.p)

    def vec(self, v):
        """rotate a local vector into world"""
        return (self.x[0] * v[0] + self.y[0] * v[1] + self.z[0] * v[2],
                self.x[1] * v[0] + self.y[1] * v[1] + self.z[1] * v[2],
                self.x[2] * v[0] + self.y[2] * v[1] + self.z[2] * v[2])

    def point(self, v):
        return add(self.p, self.vec(v))

    def __mul__(self, o):
        return CF(self.point(o.p), self.vec(o.x), self.vec(o.y), self.vec(o.z))

    def inverse(self):
        # transpose rotation
        x = (self.x[0], self.y[0], self.z[0])
        y = (self.x[1], self.y[1], self.z[1])
        z = (self.x[2], self.y[2], self.z[2])
        r = CF((0, 0, 0), x, y, z)
        np = r.vec(self.p)
        return CF((-np[0], -np[1], -np[2]), x, y, z)

    def offset(self, v):
        return CF(add(self.p, v), self.x, self.y, self.z)

    @property
    def look(self):
        return (-self.z[0], -self.z[1], -self.z[2])


def deck_frame(p, fwd, up=UP, bank=0.0):
    """Frame whose local Z points along fwd (the convention of the place's road slabs), Y up, X = Y x Z."""
    f = unit(fwd)
    r = unit(cross(up, f))  # X
    if length(r) < 1e-6:
        r = (0.0, 0.0, -1.0)
    u = unit(cross(f, r))
    if bank:
        c, s = math.cos(bank), math.sin(bank)
        r, u = (add(mul(r, c), mul(u, s)), add(mul(u, c), mul(r, -s)))
    return CF(p, r, u, f)


def look_frame(p, fwd, up=UP):
    """Roblox look frame: LookVector = fwd (Z column = -fwd)."""
    f = unit(fwd)
    r = unit(cross(f, up))
    if length(r) < 1e-6:
        r = (1.0, 0.0, 0.0)
    u = unit(cross(r, f))
    return CF(p, r, u, mul(f, -1))


def axis_frame(p, xaxis, hint=UP):
    """Frame whose local X axis = xaxis (cylinders, Pivot parts for PropMotion)."""
    x = unit(xaxis)
    if abs(dot(x, unit(hint))) > 0.95:
        hint = (0.0, 0.0, 1.0) if abs(x[2]) < 0.9 else (1.0, 0.0, 0.0)
    z = unit(cross(x, hint))
    y = unit(cross(z, x))
    return CF(p, x, y, z)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    # rotation about world Y by angle a (right-handed)
    return CF((0, 0, 0), (c, 0, -s), (0, 1, 0), (s, 0, c))


def rot_axis(axis, a):
    x, y, z = unit(axis)
    c, s = math.cos(a), math.sin(a)
    C = 1 - c
    m = ((c + x * x * C, x * y * C - z * s, x * z * C + y * s),
         (y * x * C + z * s, c + y * y * C, y * z * C - x * s),
         (z * x * C - y * s, z * y * C + x * s, c + z * z * C))
    return CF((0, 0, 0), (m[0][0], m[1][0], m[2][0]), (m[0][1], m[1][1], m[2][1]), (m[0][2], m[1][2], m[2][2]))
