
from __future__ import annotations

import base64
import io
import numpy as np
from PIL import Image


TARGET_SIZE = 100


def image_to_matrix_100(image: Image.Image) -> np.ndarray:
    """
    Convert an image to a true 100x100 logical matrix.

    Rules:
    - no interpolation;
    - no averaged output color;
    - each output cell receives one RGB that really exists in the
      corresponding source region;
    - representative RGB is the real source color closest to the
      per-cell RGB median.
    """
    arr = np.asarray(image.convert("RGB"), dtype=np.uint8)
    h, w = arr.shape[:2]

    out = np.zeros((TARGET_SIZE, TARGET_SIZE, 3), dtype=np.uint8)

    # Continuous cell boundaries preserve the whole source image.
    ys = np.linspace(0, h, TARGET_SIZE + 1)
    xs = np.linspace(0, w, TARGET_SIZE + 1)

    for gy in range(TARGET_SIZE):
        y0 = int(np.floor(ys[gy]))
        y1 = int(np.floor(ys[gy + 1]))

        if y1 <= y0:
            y0 = min(h - 1, int(round((gy + 0.5) * h / TARGET_SIZE)))
            y1 = min(h, y0 + 1)

        for gx in range(TARGET_SIZE):
            x0 = int(np.floor(xs[gx]))
            x1 = int(np.floor(xs[gx + 1]))

            if x1 <= x0:
                x0 = min(w - 1, int(round((gx + 0.5) * w / TARGET_SIZE)))
                x1 = min(w, x0 + 1)

            block = arr[y0:y1, x0:x1].reshape(-1, 3)

            if len(block) == 0:
                sy = min(h - 1, int((gy + 0.5) * h / TARGET_SIZE))
                sx = min(w - 1, int((gx + 0.5) * w / TARGET_SIZE))
                out[gy, gx] = arr[sy, sx]
                continue

            # Median guides the choice, but is NEVER used as an invented RGB.
            median = np.median(block.astype(np.float32), axis=0)

            # Pick an actual source pixel nearest to that median.
            diff = block.astype(np.float32) - median[None, :]
            d2 = np.sum(diff * diff, axis=1)
            out[gy, gx] = block[int(np.argmin(d2))]

    return out


def encode_matrix_png(arr: np.ndarray) -> str:
    bio = io.BytesIO()
    Image.fromarray(arr.astype(np.uint8), "RGB").save(bio, format="PNG")
    return base64.b64encode(bio.getvalue()).decode("ascii")


def decode_matrix_png(data: str | None) -> np.ndarray | None:
    if not data:
        return None
    try:
        raw = base64.b64decode(data)
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        arr = np.asarray(im, dtype=np.uint8)
        if arr.shape[:2] != (TARGET_SIZE, TARGET_SIZE):
            return None
        return arr.copy()
    except Exception:
        return None


def enlarged_preview(arr: np.ndarray, size: int = 800) -> Image.Image:
    im = Image.fromarray(arr.astype(np.uint8), "RGB")
    return im.resize((size, size), Image.Resampling.NEAREST)
