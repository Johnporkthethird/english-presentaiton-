"""Minimal reader/writer for the Roblox binary place format (.rbxl).

Values are decoded into plain Python objects so instances can be cloned,
edited, added and removed, then written back out.
"""
import struct
import lz4.block
import zstandard

MAGIC = b"<roblox!\x89\xff\r\n\x1a\n"


# ---------------------------------------------------------------- helpers
def deinterleave(data, n, width):
    out = bytearray(n * width)
    for b in range(width):
        plane = data[b * n:(b + 1) * n]
        out[b::width] = plane
    return bytes(out)


def interleave(data, n, width):
    out = bytearray(n * width)
    for b in range(width):
        out[b * n:(b + 1) * n] = data[b::width]
    return bytes(out)


def unzz32(u):
    return (u >> 1) ^ -(u & 1)


def zz32(i):
    return ((i << 1) ^ (i >> 31)) & 0xFFFFFFFF


def unzz64(u):
    return (u >> 1) ^ -(u & 1)


def zz64(i):
    return ((i << 1) ^ (i >> 63)) & 0xFFFFFFFFFFFFFFFF


def read_i32s(buf, pos, n):
    raw = deinterleave(buf[pos:pos + 4 * n], n, 4)
    vals = [unzz32(v) for v in struct.unpack(">%dI" % n, raw)]
    return vals, pos + 4 * n


def write_i32s(vals):
    raw = struct.pack(">%dI" % len(vals), *[zz32(v) for v in vals])
    return interleave(raw, len(vals), 4)


def read_u32s(buf, pos, n):
    raw = deinterleave(buf[pos:pos + 4 * n], n, 4)
    return list(struct.unpack(">%dI" % n, raw)), pos + 4 * n


def write_u32s(vals):
    return interleave(struct.pack(">%dI" % len(vals), *vals), len(vals), 4)


def read_f32s(buf, pos, n):
    raw = deinterleave(buf[pos:pos + 4 * n], n, 4)
    us = struct.unpack(">%dI" % n, raw)
    us = [((u >> 1) | ((u & 1) << 31)) for u in us]
    return list(struct.unpack("<%df" % n, struct.pack("<%dI" % n, *us))), pos + 4 * n


def write_f32s(vals):
    us = struct.unpack("<%dI" % len(vals), struct.pack("<%df" % len(vals), *vals))
    us = [((u << 1) & 0xFFFFFFFF) | (u >> 31) for u in us]
    return interleave(struct.pack(">%dI" % len(us), *us), len(us), 4)


def read_refs(buf, pos, n):
    vals, pos = read_i32s(buf, pos, n)
    acc = 0
    out = []
    for v in vals:
        acc += v
        out.append(acc)
    return out, pos


def write_refs(refs):
    prev = 0
    deltas = []
    for r in refs:
        deltas.append(r - prev)
        prev = r
    return write_i32s(deltas)


class Reader:
    def __init__(self, buf):
        self.buf = buf
        self.pos = 0

    def u8(self):
        v = self.buf[self.pos]
        self.pos += 1
        return v

    def u16(self):
        v = struct.unpack_from("<H", self.buf, self.pos)[0]
        self.pos += 2
        return v

    def u32(self):
        v = struct.unpack_from("<I", self.buf, self.pos)[0]
        self.pos += 4
        return v

    def f32(self, n=1):
        v = struct.unpack_from("<%df" % n, self.buf, self.pos)
        self.pos += 4 * n
        return v

    def string(self):
        n = self.u32()
        v = bytes(self.buf[self.pos:self.pos + n])
        self.pos += n
        return v

    def take(self, n):
        v = bytes(self.buf[self.pos:self.pos + n])
        self.pos += n
        return v


def wstr(b):
    if isinstance(b, str):
        b = b.encode()
    return struct.pack("<I", len(b)) + b


# ---------------------------------------------------------------- model
class Inst:
    __slots__ = ("cls", "props", "parent", "children", "service", "ref")

    def __init__(self, cls, props=None, service=False):
        self.cls = cls
        self.props = props if props is not None else {}  # name -> (type, value)
        self.parent = None
        self.children = []
        self.service = service
        self.ref = None

    # convenience
    @property
    def name(self):
        p = self.props.get("Name")
        return p[1].decode("utf-8", "replace") if p else self.cls

    def get(self, key, default=None):
        p = self.props.get(key)
        return p[1] if p else default

    def set(self, key, value, typ=None):
        if typ is None:
            typ = self.props[key][0]
        self.props[key] = (typ, value)

    def set_parent(self, parent):
        if self.parent is not None:
            self.parent.children.remove(self)
        self.parent = parent
        if parent is not None:
            parent.children.append(self)

    def find(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None

    def descendants(self):
        out = []
        stack = list(reversed(self.children))
        while stack:
            c = stack.pop()
            out.append(c)
            stack.extend(reversed(c.children))
        return out

    def path(self):
        parts = []
        i = self
        while i is not None:
            parts.append(i.name)
            i = i.parent
        return ".".join(reversed(parts))

    def __repr__(self):
        return "<%s %s>" % (self.cls, self.name)


class Place:
    def __init__(self):
        self.meta = []
        self.sstr = []  # list of (hash, bytes)
        self.roots = []
        self.extra_chunks = []  # unknown chunk (name, data) pairs, kept as-is

    def all(self):
        out = []
        for r in self.roots:
            out.append(r)
            out.extend(r.descendants())
        return out


# ---------------------------------------------------------------- property codecs
def decode_prop(typ, buf, n, sstr):
    r = Reader(buf)
    p = 0
    if typ in (0x01, 0x1D):
        return [r.string() for _ in range(n)]
    if typ == 0x02:
        return [b != 0 for b in buf[:n]]
    if typ == 0x03:
        return read_i32s(buf, 0, n)[0]
    if typ == 0x04:
        return read_f32s(buf, 0, n)[0]
    if typ == 0x05:
        return list(struct.unpack_from("<%dd" % n, buf, 0))
    if typ == 0x06:
        s, p = read_f32s(buf, 0, n)
        o, p = read_i32s(buf, p, n)
        return list(zip(s, o))
    if typ == 0x07:
        sx, p = read_f32s(buf, 0, n)
        sy, p = read_f32s(buf, p, n)
        ox, p = read_i32s(buf, p, n)
        oy, p = read_i32s(buf, p, n)
        return list(zip(sx, ox, sy, oy))
    if typ == 0x08:
        return [struct.unpack_from("<6f", buf, i * 24) for i in range(n)]
    if typ in (0x09, 0x0A):
        return list(buf[:n])
    if typ in (0x0B, 0x12, 0x1C):
        return read_u32s(buf, 0, n)[0]
    if typ == 0x0C:
        a, p = read_f32s(buf, 0, n)
        b, p = read_f32s(buf, p, n)
        c, p = read_f32s(buf, p, n)
        return list(zip(a, b, c))
    if typ == 0x0D:
        a, p = read_f32s(buf, 0, n)
        b, p = read_f32s(buf, p, n)
        return list(zip(a, b))
    if typ == 0x0E:
        a, p = read_f32s(buf, 0, n)
        b, p = read_f32s(buf, p, n)
        c, p = read_f32s(buf, p, n)
        return list(zip(a, b, c))
    if typ == 0x10:
        rots = []
        for _ in range(n):
            rid = r.u8()
            if rid == 0:
                rots.append((0, r.f32(9)))
            else:
                rots.append((rid, None))
        a, p = read_f32s(buf, r.pos, n)
        b, p = read_f32s(buf, p, n)
        c, p = read_f32s(buf, p, n)
        return [(rots[i], (a[i], b[i], c[i])) for i in range(n)]
    if typ == 0x13:
        return read_refs(buf, 0, n)[0]
    if typ == 0x14:
        return [struct.unpack_from("<3h", buf, i * 6) for i in range(n)]
    if typ == 0x15:
        out = []
        for _ in range(n):
            k = r.u32()
            out.append([r.f32(3) for _ in range(k)])
        return out
    if typ == 0x16:
        out = []
        for _ in range(n):
            k = r.u32()
            out.append([r.f32(5) for _ in range(k)])
        return out
    if typ == 0x17:
        return [struct.unpack_from("<2f", buf, i * 8) for i in range(n)]
    if typ == 0x18:
        a, p = read_f32s(buf, 0, n)
        b, p = read_f32s(buf, p, n)
        c, p = read_f32s(buf, p, n)
        d, p = read_f32s(buf, p, n)
        return list(zip(a, b, c, d))
    if typ == 0x19:
        out = []
        for _ in range(n):
            flag = r.u8()
            if flag == 0:
                out.append((0, ()))
            elif flag == 1:
                out.append((1, r.f32(5)))
            elif flag == 3:
                out.append((3, r.f32(6)))
            else:
                raise ValueError("phys flag %d" % flag)
        return out
    if typ == 0x1A:
        return list(zip(buf[0:n], buf[n:2 * n], buf[2 * n:3 * n]))
    if typ == 0x1B:
        raw = deinterleave(buf[:8 * n], n, 8)
        return [unzz64(v) for v in struct.unpack(">%dQ" % n, raw)]
    if typ == 0x1E:
        assert buf[0] == 0x10
        sub = decode_prop(0x10, buf[1:], n, sstr)
        cflen = len(encode_prop(0x10, sub))
        q = 1 + cflen
        assert buf[q] == 0x02
        bools = [b != 0 for b in buf[q + 1:q + 1 + n]]
        return list(zip(sub, bools))
    if typ == 0x1F:
        raw = deinterleave(buf[:16 * n], n, 16)
        return [raw[i * 16:(i + 1) * 16] for i in range(n)]
    if typ == 0x20:
        out = []
        for _ in range(n):
            fam = r.string()
            w = r.u16()
            st = r.u8()
            cid = r.string()
            out.append((fam, w, st, cid))
        return out
    if typ == 0x21:
        raw = deinterleave(buf[:8 * n], n, 8)
        return list(struct.unpack(">%dQ" % n, raw))
    if typ == 0x22:
        kinds, p = read_i32s(buf, 0, n)
        r.pos = p
        uris = [r.string() for _ in range(r.u32())]
        k = r.u32()
        objs, p = read_refs(buf, r.pos, k)
        r.pos = p
        if r.u32() != 0:
            raise NotImplementedError("external content")
        ui = oi = 0
        out = []
        for kd in kinds:
            if kd == 0:
                out.append(None)
            elif kd == 1:
                out.append(("uri", uris[ui])); ui += 1
            elif kd == 2:
                out.append(("obj", objs[oi])); oi += 1
            else:
                raise NotImplementedError("content kind %d" % kd)
        return out
    raise NotImplementedError("type 0x%02x" % typ)


def encode_prop(typ, vals):
    n = len(vals)
    if typ in (0x01, 0x1D):
        return b"".join(wstr(v) for v in vals)
    if typ == 0x02:
        return bytes(1 if v else 0 for v in vals)
    if typ == 0x03:
        return write_i32s(vals)
    if typ == 0x04:
        return write_f32s(vals)
    if typ == 0x05:
        return struct.pack("<%dd" % n, *vals)
    if typ == 0x06:
        return write_f32s([v[0] for v in vals]) + write_i32s([v[1] for v in vals])
    if typ == 0x07:
        return (write_f32s([v[0] for v in vals]) + write_f32s([v[2] for v in vals]) +
                write_i32s([v[1] for v in vals]) + write_i32s([v[3] for v in vals]))
    if typ == 0x08:
        return b"".join(struct.pack("<6f", *v) for v in vals)
    if typ in (0x09, 0x0A):
        return bytes(vals)
    if typ in (0x0B, 0x12, 0x1C):
        return write_u32s(vals)
    if typ in (0x0C, 0x0E):
        return write_f32s([v[0] for v in vals]) + write_f32s([v[1] for v in vals]) + write_f32s([v[2] for v in vals])
    if typ == 0x0D:
        return write_f32s([v[0] for v in vals]) + write_f32s([v[1] for v in vals])
    if typ == 0x10:
        out = bytearray()
        for (rid, m), _ in vals:
            out.append(rid)
            if rid == 0:
                out += struct.pack("<9f", *m)
        out += write_f32s([v[1][0] for v in vals])
        out += write_f32s([v[1][1] for v in vals])
        out += write_f32s([v[1][2] for v in vals])
        return bytes(out)
    if typ == 0x13:
        return write_refs(vals)
    if typ == 0x14:
        return b"".join(struct.pack("<3h", *v) for v in vals)
    if typ == 0x15:
        return b"".join(struct.pack("<I", len(v)) + b"".join(struct.pack("<3f", *k) for k in v) for v in vals)
    if typ == 0x16:
        return b"".join(struct.pack("<I", len(v)) + b"".join(struct.pack("<5f", *k) for k in v) for v in vals)
    if typ == 0x17:
        return b"".join(struct.pack("<2f", *v) for v in vals)
    if typ == 0x18:
        return b"".join(write_f32s([v[i] for v in vals]) for i in range(4))
    if typ == 0x19:
        out = bytearray()
        for flag, fs in vals:
            out.append(flag)
            if fs:
                out += struct.pack("<%df" % len(fs), *fs)
        return bytes(out)
    if typ == 0x1A:
        return bytes(v[0] for v in vals) + bytes(v[1] for v in vals) + bytes(v[2] for v in vals)
    if typ == 0x1B:
        return interleave(struct.pack(">%dQ" % n, *[zz64(v) for v in vals]), n, 8)
    if typ == 0x1E:
        return b"\x10" + encode_prop(0x10, [v[0] for v in vals]) + b"\x02" + bytes(1 if v[1] else 0 for v in vals)
    if typ == 0x1F:
        return interleave(b"".join(vals), n, 16)
    if typ == 0x20:
        return b"".join(wstr(f) + struct.pack("<HB", w, s) + wstr(c) for f, w, s, c in vals)
    if typ == 0x21:
        return interleave(struct.pack(">%dQ" % n, *vals), n, 8)
    if typ == 0x22:
        kinds, uris, objs = [], [], []
        for v in vals:
            if v is None:
                kinds.append(0)
            elif v[0] == "uri":
                kinds.append(1); uris.append(v[1])
            else:
                kinds.append(2); objs.append(v[1])
        return (write_i32s(kinds) + struct.pack("<I", len(uris)) + b"".join(wstr(u) for u in uris) +
                struct.pack("<I", len(objs)) + write_refs(objs) + struct.pack("<I", 0))
    raise NotImplementedError("type 0x%02x" % typ)


class Raw:
    """Undecodable property column for a class, kept byte-for-byte."""
    def __init__(self, typ, data):
        self.typ = typ
        self.data = data


# ---------------------------------------------------------------- read
def decompress(comp, ulen, data):
    if comp == 0:
        return data
    if data[:4] == b"\x28\xb5\x2f\xfd":
        return zstandard.ZstdDecompressor().decompress(data, max_output_size=ulen)
    return lz4.block.decompress(data, uncompressed_size=ulen)


def load(path):
    with open(path, "rb") as f:
        buf = f.read()
    assert buf[:14] == MAGIC, "not a binary place"
    version, ncls, ninst = struct.unpack_from("<Hii", buf, 14)
    pos = 32
    place = Place()
    classes = {}  # id -> (name, refs, service)
    props = {}  # id -> list of (propname, typ, data)
    prnt = None
    while pos < len(buf):
        name = buf[pos:pos + 4]
        comp, ulen, _ = struct.unpack_from("<III", buf, pos + 4)
        pos += 16
        clen = comp if comp else ulen
        data = decompress(comp, ulen, buf[pos:pos + clen])
        pos += clen
        if name == b"META":
            r = Reader(data)
            for _ in range(r.u32()):
                place.meta.append((r.string(), r.string()))
        elif name == b"SSTR":
            r = Reader(data)
            r.u32()
            for _ in range(r.u32()):
                place.sstr.append((r.take(16), r.string()))
        elif name == b"INST":
            r = Reader(data)
            cid = r.u32()
            cname = r.string().decode()
            fmt = r.u8()
            n = r.u32()
            refs, p = read_refs(data, r.pos, n)
            classes[cid] = (cname, refs, fmt == 1)
        elif name == b"PROP":
            r = Reader(data)
            cid = r.u32()
            pname = r.string().decode()
            typ = r.u8()
            props.setdefault(cid, []).append((pname, typ, data[r.pos:]))
        elif name == b"PRNT":
            r = Reader(data)
            r.u8()
            n = r.u32()
            child, p = read_refs(data, r.pos, n)
            parent, p = read_refs(data, p, n)
            prnt = (child, parent)
        elif name == b"END\x00":
            break
        else:
            place.extra_chunks.append((name, data))

    by_ref = {}
    for cid, (cname, refs, svc) in classes.items():
        insts = [Inst(cname, service=svc) for _ in refs]
        for ref, inst in zip(refs, insts):
            by_ref[ref] = inst
        for pname, typ, data in props.get(cid, []):
            try:
                vals = decode_prop(typ, data, len(refs), place.sstr)
            except NotImplementedError:
                raw = Raw(typ, data)
                for inst in insts:
                    inst.props[pname] = (typ, raw)
                continue
            for inst, v in zip(insts, vals):
                inst.props[pname] = (typ, v)
    # resolve referent properties
    for inst in by_ref.values():
        for k, (typ, v) in list(inst.props.items()):
            if typ == 0x13:
                inst.props[k] = (typ, by_ref.get(v))
            elif typ == 0x22 and v is not None and v[0] == "obj":
                inst.props[k] = (typ, ("obj", by_ref.get(v[1])))
    # hierarchy, in PRNT order (preserves sibling order)
    for c, p in zip(*prnt):
        ch = by_ref[c]
        if p == -1:
            place.roots.append(ch)
        else:
            ch.parent = by_ref[p]
            by_ref[p].children.append(ch)
    return place


# ---------------------------------------------------------------- write
def chunk(name, data, compress=True):
    if compress and len(data) > 0:
        comp = lz4.block.compress(data, store_size=False)
        return name + struct.pack("<III", len(comp), len(data), 0) + comp
    return name + struct.pack("<III", 0, len(data), 0) + data


def save(place, path):
    insts = place.all()
    for i, inst in enumerate(insts):
        inst.ref = i
    by_class = {}
    for inst in insts:
        by_class.setdefault(inst.cls, []).append(inst)
    cnames = sorted(by_class)
    out = bytearray(MAGIC)
    out += struct.pack("<Hii", 0, len(cnames), len(insts)) + b"\0" * 8
    if place.meta:
        out += chunk(b"META", struct.pack("<I", len(place.meta)) + b"".join(wstr(k) + wstr(v) for k, v in place.meta), False)
    if place.sstr:
        out += chunk(b"SSTR", struct.pack("<II", 0, len(place.sstr)) + b"".join(h + wstr(s) for h, s in place.sstr))
    for cid, cname in enumerate(cnames):
        group = by_class[cname]
        svc = any(i.service for i in group)
        data = struct.pack("<I", cid) + wstr(cname) + bytes([1 if svc else 0]) + struct.pack("<I", len(group))
        data += write_refs([i.ref for i in group])
        if svc:
            data += b"\x01" * len(group)
        out += chunk(b"INST", data)
    for cid, cname in enumerate(cnames):
        group = by_class[cname]
        names = []
        for i in group:
            for k in i.props:
                if k not in names:
                    names.append(k)
        for pname in names:
            typs = {i.props[pname][0] for i in group if pname in i.props}
            assert len(typs) == 1, (cname, pname, typs)
            typ = typs.pop()
            missing = [i for i in group if pname not in i.props]
            if missing:
                raise ValueError("%s.%s missing on %d instance(s), e.g. %s" % (cname, pname, len(missing), missing[0].path()))
            vals = [i.props[pname][1] for i in group]
            if isinstance(vals[0], Raw):
                if not all(v is vals[0] for v in vals) or len(group) != vals[0].n if hasattr(vals[0], "n") else False:
                    pass
                body = vals[0].data
            else:
                if typ == 0x13:
                    vals = [v.ref if v is not None else -1 for v in vals]
                elif typ == 0x22:
                    vals = [("obj", v[1].ref if v[1] is not None else -1) if v is not None and v[0] == "obj" else v for v in vals]
                body = encode_prop(typ, vals)
            out += chunk(b"PROP", struct.pack("<I", cid) + wstr(pname) + bytes([typ]) + body)
    child, parent = [], []
    for inst in insts:
        child.append(inst.ref)
        parent.append(inst.parent.ref if inst.parent is not None else -1)
    out += chunk(b"PRNT", b"\x00" + struct.pack("<I", len(insts)) + write_refs(child) + write_refs(parent))
    out += chunk(b"END\x00", b"</roblox>", False)
    with open(path, "wb") as f:
        f.write(out)


# ---------------------------------------------------------------- attributes
def decode_attrs(b):
    out = {}
    if not b:
        return out
    r = Reader(b)
    for _ in range(r.u32()):
        k = r.string().decode()
        t = r.u8()
        if t == 0x02:
            v = r.string().decode("utf-8", "replace")
        elif t == 0x03:
            v = bool(r.u8())
        elif t == 0x05:
            v = r.f32()[0]
        elif t == 0x06:
            v = struct.unpack_from("<d", r.buf, r.pos)[0]; r.pos += 8
        elif t == 0x09:
            v = ("UDim", r.f32()[0], struct.unpack_from("<i", r.buf, r.pos)[0]); r.pos += 4
        elif t == 0x0A:
            a = r.f32()[0]; o1 = struct.unpack_from("<i", r.buf, r.pos)[0]; r.pos += 4
            c = r.f32()[0]; o2 = struct.unpack_from("<i", r.buf, r.pos)[0]; r.pos += 4
            v = ("UDim2", a, o1, c, o2)
        elif t == 0x0E:
            v = ("BrickColor", r.u32())
        elif t == 0x0F:
            v = ("Color3",) + r.f32(3)
        elif t == 0x10:
            v = ("Vector2",) + r.f32(2)
        elif t == 0x11:
            v = ("Vector3",) + r.f32(3)
        elif t == 0x14:
            pos = r.f32(3)
            rid = r.u8()
            rot = r.f32(9) if rid == 0 else rid
            v = ("CFrame", pos, rot)
        elif t == 0x17:
            v = ("NumberSequence", [r.f32(3) for _ in range(r.u32())])
        elif t == 0x19:
            v = ("ColorSequence", [r.f32(5) for _ in range(r.u32())])
        elif t == 0x1B:
            v = ("NumberRange",) + r.f32(2)
        elif t == 0x1C:
            v = ("Rect",) + r.f32(4)
        elif t == 0x21:
            w = r.u16(); st = r.u8(); fam = r.string(); cid = r.string()
            v = ("Font", w, st, fam, cid)
        else:
            raise ValueError("attr type 0x%02x for %s" % (t, k))
        out[k] = v
    return out


def encode_attrs(d):
    out = bytearray(struct.pack("<I", len(d)))
    for k, v in d.items():
        out += wstr(k)
        if isinstance(v, bool):
            out += b"\x03" + bytes([1 if v else 0])
        elif isinstance(v, (int, float)):
            out += b"\x06" + struct.pack("<d", v)
        elif isinstance(v, str):
            out += b"\x02" + wstr(v.encode())
        elif v[0] == "Vector3":
            out += b"\x11" + struct.pack("<3f", *v[1:])
        elif v[0] == "Vector2":
            out += b"\x10" + struct.pack("<2f", *v[1:])
        elif v[0] == "Color3":
            out += b"\x0F" + struct.pack("<3f", *v[1:])
        elif v[0] == "NumberRange":
            out += b"\x1B" + struct.pack("<2f", *v[1:])
        elif v[0] == "CFrame":
            out += b"\x14" + struct.pack("<3f", *v[1])
            if isinstance(v[2], int):
                out += bytes([v[2]])
            else:
                out += b"\x00" + struct.pack("<9f", *v[2])
        else:
            raise ValueError("cannot encode attr %r" % (v,))
    return bytes(out)


def attrs(inst):
    return decode_attrs(inst.get("AttributesSerialize", b""))


def set_attrs(inst, d):
    inst.props["AttributesSerialize"] = (0x01, encode_attrs(d))
