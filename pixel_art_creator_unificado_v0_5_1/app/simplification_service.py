
from __future__ import annotations

import base64
import io
from collections import Counter
import numpy as np
from PIL import Image
from skimage.color import rgb2lab


TARGET_COLORS = 50


def _lab_colors(rgbs):
    arr = np.asarray(rgbs, dtype=np.float64).reshape(1, -1, 3) / 255.0
    return rgb2lab(arr).reshape(-1, 3)


def unique_essential_colors(workspace):
    """
    Returns unique essential RGBs preserving first appearance order.
    """
    seen = set()
    out = []
    for area in workspace.areas:
        for rgb in area.get("selected", {}).keys():
            rgb = tuple(int(v) for v in rgb)
            if rgb not in seen:
                seen.add(rgb)
                out.append(rgb)
    return out


def essential_area_masks(workspace):
    """
    Maps essential RGB -> union of the original image masks where it was selected.
    """
    result = {}
    for area in workspace.areas:
        mask = area.get("mask")
        if mask is None:
            continue
        mb = mask.astype(bool)
        for rgb in area.get("selected", {}).keys():
            rgb = tuple(int(v) for v in rgb)
            if rgb not in result:
                result[rgb] = mb.copy()
            else:
                result[rgb] |= mb
    return result


def project_mask_to_100(mask, target=100):
    """
    Project an original-image binary mask to logical target x target cells.
    A logical cell is active if ANY source mask pixel overlaps its source region.
    """
    mask = np.asarray(mask).astype(bool)
    h, w = mask.shape
    out = np.zeros((target, target), dtype=bool)

    ys = np.linspace(0, h, target + 1)
    xs = np.linspace(0, w, target + 1)

    for gy in range(target):
        y0 = int(np.floor(ys[gy]))
        y1 = int(np.floor(ys[gy + 1]))
        if y1 <= y0:
            y0 = min(h - 1, int(round((gy + 0.5) * h / target)))
            y1 = min(h, y0 + 1)

        for gx in range(target):
            x0 = int(np.floor(xs[gx]))
            x1 = int(np.floor(xs[gx + 1]))
            if x1 <= x0:
                x0 = min(w - 1, int(round((gx + 0.5) * w / target)))
                x1 = min(w, x0 + 1)

            out[gy, gx] = bool(mask[y0:y1, x0:x1].any())

    return out


def build_palette_50(matrix, essential_rgbs, target=TARGET_COLORS):
    """
    Build final palette:
    1) all unique essential RGBs, exact;
    2) complement with real RGBs from the 100x100 matrix.

    Complement colors are chosen by weighted farthest-point sampling in Lab:
    - distance from already selected palette preserves chromatic diversity;
    - frequency weighting favors visually relevant colors.
    """
    matrix = np.asarray(matrix, dtype=np.uint8)
    flat = matrix.reshape(-1, 3)

    counts = Counter(map(tuple, flat.tolist()))
    matrix_colors = list(counts.keys())

    essentials = []
    seen = set()
    for rgb in essential_rgbs:
        rgb = tuple(int(v) for v in rgb)
        if rgb not in seen:
            essentials.append(rgb)
            seen.add(rgb)

    if len(essentials) > target:
        raise ValueError(
            f"Foram selecionados {len(essentials)} RGBs essenciais únicos, "
            f"mas a paleta final permite {target}. "
            "Remova cores redundantes antes de simplificar."
        )

    selected = list(essentials)

    # If there are no selected colors yet, start from the most frequent matrix RGB.
    if not selected and matrix_colors:
        most = max(matrix_colors, key=lambda c: counts[c])
        selected.append(most)
        seen.add(most)

    candidates = [c for c in matrix_colors if c not in seen]

    if not candidates:
        return selected[:target]

    candidate_lab = _lab_colors(candidates)
    freq = np.array([counts[c] for c in candidates], dtype=np.float64)

    # Frequency multiplier is intentionally gentle so rare characteristic colors
    # can still be selected when chromatically distinct.
    freq_weight = 1.0 + np.log1p(freq)

    while len(selected) < target and candidates:
        selected_lab = _lab_colors(selected)

        # Distance from each candidate to the nearest chosen color.
        diff = candidate_lab[:, None, :] - selected_lab[None, :, :]
        d = np.sqrt(np.sum(diff * diff, axis=2))
        nearest = d.min(axis=1)

        # Prefer colors that are both distinct and represented in the matrix.
        score = nearest * freq_weight
        idx = int(np.argmax(score))

        chosen = candidates[idx]
        selected.append(chosen)
        seen.add(chosen)

        candidates.pop(idx)
        candidate_lab = np.delete(candidate_lab, idx, axis=0)
        freq_weight = np.delete(freq_weight, idx, axis=0)

    return selected[:target]


def map_matrix_to_palette(matrix, palette):
    """
    Remap every 100x100 source cell to nearest final-palette color in Lab.
    Geometry/cell structure does not change.
    """
    matrix = np.asarray(matrix, dtype=np.uint8)
    flat = matrix.reshape(-1, 3)

    palette = [tuple(int(v) for v in c) for c in palette]
    pal_lab = _lab_colors(palette)

    # Work by unique source RGB for efficiency and deterministic mapping.
    unique, inverse = np.unique(flat, axis=0, return_inverse=True)
    u_lab = _lab_colors(unique)

    diff = u_lab[:, None, :] - pal_lab[None, :, :]
    d2 = np.sum(diff * diff, axis=2)
    nearest = np.argmin(d2, axis=1)

    mapped_unique = np.asarray([palette[i] for i in nearest], dtype=np.uint8)
    mapped = mapped_unique[inverse].reshape(matrix.shape)
    return mapped


def force_essential_usage(
    simplified,
    source_matrix,
    essential_rgbs,
    rgb_to_original_mask,
):
    """
    Essential RGBs must not merely exist in the palette; they should appear in
    the simplified matrix.

    If an essential RGB is not naturally used after nearest-color mapping:
    - prefer a logical cell projected from the area(s) where that RGB was selected;
    - among those cells, choose the source-matrix RGB nearest to the essential RGB;
    - fall back to the globally nearest cell.
    """
    out = np.asarray(simplified, dtype=np.uint8).copy()
    source = np.asarray(source_matrix, dtype=np.uint8)

    used = set(map(tuple, out.reshape(-1, 3).tolist()))
    reserved = set()

    source_flat = source.reshape(-1, 3)
    source_lab = _lab_colors(source_flat)

    for rgb in essential_rgbs:
        rgb = tuple(int(v) for v in rgb)
        if rgb in used:
            continue

        essential_lab = _lab_colors([rgb])[0]

        mask = rgb_to_original_mask.get(rgb)
        candidate_indices = None

        if mask is not None:
            projected = project_mask_to_100(mask).reshape(-1)
            idxs = np.flatnonzero(projected)
            if len(idxs):
                candidate_indices = idxs

        if candidate_indices is None or len(candidate_indices) == 0:
            candidate_indices = np.arange(len(source_flat))

        # Avoid overwriting cells already reserved for another forced essential
        # whenever there is another suitable cell available.
        available = np.array(
            [i for i in candidate_indices if int(i) not in reserved],
            dtype=int
        )
        if len(available):
            candidate_indices = available

        d = source_lab[candidate_indices] - essential_lab[None, :]
        d2 = np.sum(d * d, axis=1)
        chosen_flat = int(candidate_indices[int(np.argmin(d2))])

        y, x = divmod(chosen_flat, source.shape[1])
        out[y, x] = np.array(rgb, dtype=np.uint8)
        reserved.add(chosen_flat)
        used.add(rgb)

    return out


def simplify_to_50(matrix, workspace, target=TARGET_COLORS):
    essential = unique_essential_colors(workspace)
    masks = essential_area_masks(workspace)

    palette = build_palette_50(matrix, essential, target=target)
    simplified = map_matrix_to_palette(matrix, palette)
    simplified = force_essential_usage(
        simplified,
        matrix,
        essential,
        masks
    )

    # Palette colors chosen from matrix should naturally appear because the exact
    # source RGB maps to itself. Essentials not present in the matrix were forced.
    final_unique = set(map(tuple, simplified.reshape(-1, 3).tolist()))

    # In rare tie/degenerate cases, guarantee every palette color is represented.
    # Complement colors are real source colors, so place them back at a source cell
    # that originally had the exact RGB.
    reserved = set()
    flat_source = matrix.reshape(-1, 3)
    flat_out = simplified.reshape(-1, 3)

    for rgb in palette:
        rgb = tuple(rgb)
        if rgb in final_unique:
            continue
        exact = np.flatnonzero(np.all(flat_source == np.array(rgb), axis=1))
        if len(exact):
            idx = next((int(i) for i in exact if int(i) not in reserved), int(exact[0]))
            flat_out[idx] = np.array(rgb, dtype=np.uint8)
            reserved.add(idx)
            final_unique.add(rgb)

    simplified = flat_out.reshape(matrix.shape)
    return simplified, palette, essential


def encode_png(arr):
    bio = io.BytesIO()
    Image.fromarray(np.asarray(arr, dtype=np.uint8), "RGB").save(
        bio, format="PNG"
    )
    return base64.b64encode(bio.getvalue()).decode("ascii")


def decode_png(data):
    if not data:
        return None
    try:
        raw = base64.b64decode(data)
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        arr = np.asarray(im, dtype=np.uint8)
        if arr.shape[:2] != (100, 100):
            return None
        return arr.copy()
    except Exception:
        return None
