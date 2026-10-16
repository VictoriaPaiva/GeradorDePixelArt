
from collections import Counter
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class PaletteColor:
    code: str
    rgb: Tuple[int, int, int]
    count: int
    percent: float

    @property
    def hex(self) -> str:
        return "#{:02X}{:02X}{:02X}".format(*self.rgb)


def make_code(index: int) -> str:
    # A..Z, Aa..Az, Ba..Bz, ...
    if index < 26:
        return chr(65 + index)
    index -= 26
    first = chr(65 + (index // 26))
    second = chr(97 + (index % 26))
    return first + second


def top_exact_colors(image: Image.Image, limit: int = 200) -> List[PaletteColor]:
    rgb = image.convert("RGB")
    arr = np.asarray(rgb)
    pixels = arr.reshape(-1, 3)

    counts = Counter(map(tuple, pixels.tolist()))
    total = len(pixels)

    out = []
    for idx, (rgb_value, count) in enumerate(counts.most_common(limit)):
        out.append(
            PaletteColor(
                code=make_code(idx),
                rgb=tuple(int(x) for x in rgb_value),
                count=count,
                percent=(count / total) * 100.0,
            )
        )
    return out
