"""Makes new instances by copying the full property set of real instances already in the place."""
import os
import struct
import rbxl
from rbxl import Inst
from geom import CF

MAT = {
    "Plastic": 256, "SmoothPlastic": 272, "Neon": 288, "Wood": 512, "WoodPlanks": 528, "Marble": 784,
    "Basalt": 788, "Slate": 800, "CrackedLava": 804, "Concrete": 816, "Granite": 832, "Brick": 848,
    "Cobblestone": 880, "Rock": 896, "Sandstone": 912, "CorrodedMetal": 1040, "DiamondPlate": 1056,
    "Foil": 1072, "Metal": 1088, "Grass": 1280, "Sand": 1296, "Fabric": 1312, "Snow": 1328, "Asphalt": 1376,
    "Ice": 1536, "Glacier": 1552, "Glass": 1568, "ForceField": 1584,
}

BASEPART_CLASSES = {"Part", "WedgePart", "CornerWedgePart", "MeshPart", "UnionOperation", "TrussPart",
                    "Seat", "VehicleSeat", "SpawnLocation", "IntersectOperation", "NegateOperation"}


class Factory:
    def __init__(self, place, uid_seed=0x00A00000):
        self.place = place
        self.templates = {}
        self.uid_counter = uid_seed
        self.uid_time = None

    def find_templates(self, level_folder):
        """Pick one clean template per class from an existing level."""
        want = {"Part": "Deck", "WedgePart": "Kicker", "Model": None, "Folder": None, "Texture": None,
                "PointLight": None, "ParticleEmitter": None}
        for d in level_folder.descendants():
            if d.cls in want and d.cls not in self.templates:
                if want[d.cls] is None or d.name == want[d.cls]:
                    self.templates[d.cls] = d
        for d in self.place.all():
            if d.cls in ("SurfaceLight", "StringValue", "Attachment", "Beam") and d.cls not in self.templates:
                self.templates[d.cls] = d
        part = self.templates["Part"]
        self.uid_time = part.get("UniqueId")[4:8]

    def new_uid(self):
        self.uid_counter += 1
        return struct.pack(">I", self.uid_counter) + self.uid_time + os.urandom(8)

    def blank(self, cls):
        t = self.templates[cls]
        inst = Inst(cls, dict(t.props))
        inst.props["AttributesSerialize"] = (0x01, b"")
        if "Tags" in inst.props:
            inst.props["Tags"] = (0x01, b"")
        if "UniqueId" in inst.props:
            inst.props["UniqueId"] = (0x1F, self.new_uid())
        if "HistoryId" in inst.props:
            inst.props["HistoryId"] = (0x1F, b"\0" * 16)
        if "SourceAssetId" in inst.props:
            inst.props["SourceAssetId"] = (0x1B, -1)
        return inst

    def clone(self, src, parent=None):
        """Deep copy of a subtree with fresh unique ids; referents inside the subtree are remapped."""
        mapping = {}

        def rec(s, par):
            c = Inst(s.cls, dict(s.props), s.service)
            if "UniqueId" in c.props:
                c.props["UniqueId"] = (0x1F, self.new_uid())
            mapping[s] = c
            c.parent = par
            if par is not None:
                par.children.append(c)
            for ch in s.children:
                rec(ch, c)
            return c
        root = rec(src, parent)
        for old, new in mapping.items():
            for k, (t, v) in list(new.props.items()):
                if t == 0x13 and v is not None:
                    new.props[k] = (t, mapping.get(v))
                elif t == 0x22 and v is not None and v[0] == "obj":
                    new.props[k] = (t, ("obj", mapping.get(v[1])))
        return root


def is_basepart(inst):
    return inst.cls in BASEPART_CLASSES or ("size" in inst.props and "CFrame" in inst.props and "Anchored" in inst.props)


def transform_tree(root, T):
    """Apply a rigid transform T (CF) to every BasePart and Model pivot in the subtree."""
    for d in [root] + root.descendants():
        if is_basepart(d):
            cf = CF.from_prop(d.get("CFrame"))
            d.set("CFrame", (T * cf).to_prop())
        elif d.cls == "Model" and "WorldPivotData" in d.props:
            v = d.get("WorldPivotData")
            if v is not None:
                cfp, ok = v
                cf = CF.from_prop(cfp)
                d.set("WorldPivotData", ((T * cf).to_prop(), ok))
