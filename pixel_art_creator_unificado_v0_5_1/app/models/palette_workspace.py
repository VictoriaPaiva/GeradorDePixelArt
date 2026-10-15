
from dataclasses import dataclass
from typing import Tuple
import base64, zlib
import numpy as np


@dataclass(frozen=True)
class PaletteGroup:
    code: str
    rgb: Tuple[int, int, int]
    count: int
    percent: float
    member_count: int

    @property
    def hex(self):
        return "#{:02X}{:02X}{:02X}".format(*self.rgb)

    def to_dict(self):
        return {
            "code": self.code,
            "rgb": list(self.rgb),
            "count": self.count,
            "percent": self.percent,
            "member_count": self.member_count,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            code=d["code"],
            rgb=tuple(d["rgb"]),
            count=int(d["count"]),
            percent=float(d["percent"]),
            member_count=int(d.get("member_count", 1)),
        )


def encode_mask(mask):
    arr = np.asarray(mask, dtype=np.uint8)
    packed = np.packbits(arr.reshape(-1))
    raw = zlib.compress(packed.tobytes(), 9)
    return {
        "shape": list(arr.shape),
        "data": base64.b64encode(raw).decode("ascii"),
    }


def decode_mask(payload):
    if not payload:
        return None
    shape = tuple(payload["shape"])
    raw = zlib.decompress(base64.b64decode(payload["data"]))
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8))
    size = int(np.prod(shape))
    return bits[:size].reshape(shape).astype(np.uint8)


class PaletteWorkspace:
    def __init__(self):
        self.image_path = None
        self.areas = []
        self.area_counter = 0
        self.limit = 200
        self.threshold = 4.0

    def clear(self):
        self.image_path = None
        self.areas = []
        self.area_counter = 0

    def to_state_dict(self):
        areas = []
        for area in self.areas:
            selected_rgbs = [list(rgb) for rgb in area.get("selected", {}).keys()]
            areas.append({
                "id": area["id"],
                "name": area["name"],
                "pixel_count": area.get("pixel_count", 0),
                "expanded": area.get("expanded", True),
                "mask": encode_mask(area["mask"]),
                "palette": [p.to_dict() for p in area.get("palette", [])],
                "selected_rgbs": selected_rgbs,
            })
        return {
            "image_path": self.image_path,
            "area_counter": self.area_counter,
            "limit": self.limit,
            "threshold": self.threshold,
            "areas": areas,
        }

    @classmethod
    def from_state_dict(cls, data):
        obj = cls()
        if not data:
            return obj
        obj.image_path = data.get("image_path")
        obj.area_counter = int(data.get("area_counter", 0))
        obj.limit = int(data.get("limit", 200))
        obj.threshold = float(data.get("threshold", 4.0))
        for a in data.get("areas", []):
            palette = [PaletteGroup.from_dict(p) for p in a.get("palette", [])]
            by_rgb = {p.rgb: p for p in palette}
            selected = {}
            for rgb in a.get("selected_rgbs", []):
                key = tuple(rgb)
                if key in by_rgb:
                    selected[key] = by_rgb[key]
            obj.areas.append({
                "id": int(a["id"]),
                "name": a["name"],
                "pixel_count": int(a.get("pixel_count", 0)),
                "expanded": bool(a.get("expanded", True)),
                "mask": decode_mask(a.get("mask")),
                "palette": palette,
                "selected": selected,
            })
        return obj
