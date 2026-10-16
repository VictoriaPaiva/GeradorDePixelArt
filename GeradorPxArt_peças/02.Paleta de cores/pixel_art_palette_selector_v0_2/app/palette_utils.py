
from dataclasses import dataclass
from collections import Counter
from typing import List, Tuple, Dict
import numpy as np
from PIL import Image
from skimage.color import rgb2lab


@dataclass(frozen=True)
class PaletteGroup:
    code: str
    rgb: Tuple[int, int, int]
    count: int
    percent: float
    member_count: int
    min_rgb: Tuple[int, int, int]
    max_rgb: Tuple[int, int, int]

    @property
    def hex(self) -> str:
        return "#{:02X}{:02X}{:02X}".format(*self.rgb)


def make_code(index: int) -> str:
    if index < 26:
        return chr(65 + index)
    index -= 26
    return chr(65 + (index // 26)) + chr(97 + (index % 26))


def _weighted_representative(members):
    # Members: [(rgb_tuple, count), ...]
    rgbs = np.array([m[0] for m in members], dtype=np.float64)
    weights = np.array([m[1] for m in members], dtype=np.float64)
    avg = np.average(rgbs, axis=0, weights=weights)

    # Use an ACTUAL RGB that exists in the image, nearest to weighted average.
    d2 = ((rgbs - avg) ** 2).sum(axis=1)
    return tuple(int(x) for x in rgbs[np.argmin(d2)])


def grouped_predominant_colors(
    image: Image.Image,
    limit: int = 200,
    delta_e_threshold: float = 4.0,
    max_exact_candidates: int = 4500,
) -> List[PaletteGroup]:
    """
    1) Counts exact RGBs.
    2) Keeps a broad candidate set (frequent + saturated colors).
    3) Converts candidates to Lab.
    4) Greedily merges only colors within a small Delta-E-like Lab distance.
    5) Sums frequencies per group and returns the 200 most predominant groups.

    The representative RGB is always a real RGB present in the source image.
    """
    rgb = image.convert("RGB")
    arr = np.asarray(rgb)
    pixels = arr.reshape(-1, 3)
    total = len(pixels)

    counts = Counter(map(tuple, pixels.tolist()))
    unique = list(counts.keys())

    if len(unique) <= limit:
        ordered = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [
            PaletteGroup(
                code=make_code(i),
                rgb=tuple(map(int, c)),
                count=n,
                percent=(n / total) * 100.0,
                member_count=1,
                min_rgb=tuple(map(int, c)),
                max_rgb=tuple(map(int, c)),
            )
            for i, (c, n) in enumerate(ordered[:limit])
        ]

    # Broad candidate pool.
    frequent = [c for c, _ in counts.most_common(max_exact_candidates)]

    # Ensure vivid colors are represented even when they occupy small areas.
    def saturation(c):
        mx, mn = max(c), min(c)
        return 0 if mx == 0 else (mx - mn) / mx

    vivid = sorted(
        unique,
        key=lambda c: (saturation(c), counts[c]),
        reverse=True
    )[:1200]

    pool = list(dict.fromkeys(frequent + vivid))
    pool_rgb = np.array(pool, dtype=np.float64) / 255.0
    pool_lab = rgb2lab(pool_rgb.reshape(1, -1, 3)).reshape(-1, 3)

    # Sort by frequency. Strong colors seed groups first.
    order = np.argsort([-counts[c] for c in pool])

    groups = []
    group_labs = []

    for idx in order:
        c = pool[idx]
        lab = pool_lab[idx]
        n = counts[c]

        if not groups:
            groups.append([(c, n)])
            group_labs.append(lab.copy())
            continue

        labs = np.vstack(group_labs)
        # CIE76 Euclidean Lab distance. Low thresholds approximate "very similar".
        distances = np.linalg.norm(labs - lab, axis=1)
        j = int(np.argmin(distances))

        if distances[j] <= delta_e_threshold:
            groups[j].append((c, n))
            # Update group centroid weighted by pixel counts.
            old_weight = sum(x[1] for x in groups[j][:-1])
            new_weight = old_weight + n
            group_labs[j] = (group_labs[j] * old_weight + lab * n) / new_weight
        else:
            groups.append([(c, n)])
            group_labs.append(lab.copy())

    group_data = []
    for members in groups:
        group_count = sum(n for _, n in members)
        rep = _weighted_representative(members)
        rgbs = np.array([m[0] for m in members], dtype=int)
        group_data.append(
            dict(
                rgb=rep,
                count=group_count,
                member_count=len(members),
                min_rgb=tuple(map(int, rgbs.min(axis=0))),
                max_rgb=tuple(map(int, rgbs.max(axis=0))),
            )
        )

    group_data.sort(key=lambda x: x["count"], reverse=True)
    group_data = group_data[:limit]

    return [
        PaletteGroup(
            code=make_code(i),
            rgb=g["rgb"],
            count=g["count"],
            percent=(g["count"] / total) * 100.0,
            member_count=g["member_count"],
            min_rgb=g["min_rgb"],
            max_rgb=g["max_rgb"],
        )
        for i, g in enumerate(group_data)
    ]
