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


def project_mask_to_grid(mask, target_width, target_height):
    """Project original-image binary mask to the logical stitch grid."""
    mask=np.asarray(mask).astype(bool); h,w=mask.shape
    out=np.zeros((int(target_height),int(target_width)),dtype=bool)
    ys=np.linspace(0,h,int(target_height)+1); xs=np.linspace(0,w,int(target_width)+1)
    for gy in range(int(target_height)):
        y0=int(np.floor(ys[gy])); y1=int(np.floor(ys[gy+1]))
        if y1<=y0: y0=min(h-1,int(round((gy+.5)*h/target_height))); y1=min(h,y0+1)
        for gx in range(int(target_width)):
            x0=int(np.floor(xs[gx])); x1=int(np.floor(xs[gx+1]))
            if x1<=x0: x0=min(w-1,int(round((gx+.5)*w/target_width))); x1=min(w,x0+1)
            out[gy,gx]=bool(mask[y0:y1,x0:x1].any())
    return out


def project_mask_to_100(mask,target=100):
    return project_mask_to_grid(mask,target,target)

def _dedupe_rgbs(rgbs):
    seen = set()
    out = []
    for rgb in rgbs:
        rgb = tuple(int(v) for v in rgb)
        if rgb not in seen:
            seen.add(rgb)
            out.append(rgb)
    return out


def extend_palette_from_seed(matrix, seed_palette, target=TARGET_COLORS, excluded_rgbs=None):
    """
    Extend a partially defined palette until it reaches `target` colors.

    The extension uses real RGBs from the logical stitch matrix and chooses new colors
    by weighted farthest-point sampling in Lab space:
    - distance from already selected colors preserves diversity;
    - a gentle frequency weight keeps visually relevant colors competitive.
    """
    matrix = np.asarray(matrix, dtype=np.uint8)
    flat = matrix.reshape(-1, 3)

    counts = Counter(map(tuple, flat.tolist()))
    matrix_colors = list(counts.keys())

    selected = _dedupe_rgbs(seed_palette)
    seen = set(selected)
    excluded = {tuple(int(v) for v in rgb) for rgb in (excluded_rgbs or [])}

    if len(selected) > target:
        raise ValueError(
            f"A paleta-base possui {len(selected)} cores únicas, "
            f"mas o limite é {target}."
        )

    if not selected and matrix_colors:
        most = max(matrix_colors, key=lambda c: counts[c])
        selected.append(most)
        seen.add(most)

    candidates = [c for c in matrix_colors if c not in seen and c not in excluded]

    if not candidates:
        return selected[:target]

    candidate_lab = _lab_colors(candidates)
    freq = np.array([counts[c] for c in candidates], dtype=np.float64)
    freq_weight = 1.0 + np.log1p(freq)

    while len(selected) < target and candidates:
        selected_lab = _lab_colors(selected)
        diff = candidate_lab[:, None, :] - selected_lab[None, :, :]
        d = np.sqrt(np.sum(diff * diff, axis=2))
        nearest = d.min(axis=1)
        score = nearest * freq_weight
        idx = int(np.argmax(score))

        chosen = candidates[idx]
        selected.append(chosen)
        seen.add(chosen)

        candidates.pop(idx)
        candidate_lab = np.delete(candidate_lab, idx, axis=0)
        freq_weight = np.delete(freq_weight, idx, axis=0)

    return selected[:target]


def build_palette_50(matrix, essential_rgbs, target=TARGET_COLORS):
    """
    Build final palette:
    1) all unique essential RGBs, exact;
    2) complement with real RGBs from the logical stitch matrix.
    """
    essentials = _dedupe_rgbs(essential_rgbs)

    if len(essentials) > target:
        raise ValueError(
            f"Foram selecionados {len(essentials)} RGBs essenciais únicos, "
            f"mas a paleta final permite {target}. "
            "Remova cores redundantes antes de simplificar."
        )

    return extend_palette_from_seed(
        matrix,
        essentials,
        target=target
    )


def map_matrix_to_palette(matrix, palette):
    """
    Remap every source cell to nearest final-palette color in Lab.
    Geometry/cell structure does not change.
    """
    matrix = np.asarray(matrix, dtype=np.uint8)
    flat = matrix.reshape(-1, 3)

    palette = [tuple(int(v) for v in c) for c in palette]
    pal_lab = _lab_colors(palette)

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
            projected = project_mask_to_grid(mask, source.shape[1], source.shape[0]).reshape(-1)
            idxs = np.flatnonzero(projected)
            if len(idxs):
                candidate_indices = idxs

        if candidate_indices is None or len(candidate_indices) == 0:
            candidate_indices = np.arange(len(source_flat))

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


def _guarantee_palette_usage(simplified, source_matrix, palette):
    final_unique = set(map(tuple, simplified.reshape(-1, 3).tolist()))
    reserved = set()
    flat_source = source_matrix.reshape(-1, 3)
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

    return flat_out.reshape(source_matrix.shape)


def build_simplified_image(matrix, workspace, palette):
    essential = unique_essential_colors(workspace)
    masks = essential_area_masks(workspace)
    simplified = map_matrix_to_palette(matrix, palette)
    simplified = force_essential_usage(
        simplified,
        matrix,
        essential,
        masks
    )
    simplified = _guarantee_palette_usage(
        simplified,
        np.asarray(matrix, dtype=np.uint8),
        palette
    )
    return simplified, essential


def simplify_to_50(matrix, workspace, target=TARGET_COLORS):
    essential = unique_essential_colors(workspace)
    palette = build_palette_50(matrix, essential, target=target)
    simplified, essential = build_simplified_image(matrix, workspace, palette)
    return simplified, palette, essential


def rebuild_palette_without_colors(
    matrix,
    workspace,
    current_palette,
    removed_rgbs,
    target=TARGET_COLORS,
):
    """
    Remove selected non-essential colors from the current palette and rebuilds
    the simplified image using ONLY the remaining palette colors.

    Important:
    - essential colors remain protected;
    - the palette is NOT completed back to `target`;
    - the final image may therefore use fewer than 50 colors.
    """
    essential = unique_essential_colors(workspace)
    essential_set = {tuple(c) for c in essential}
    removed = {tuple(int(v) for v in rgb) for rgb in removed_rgbs}

    blocked = removed & essential_set
    if blocked:
        raise ValueError(
            "Cores essenciais não podem ser removidas nesta etapa: "
            + ", ".join(str(c) for c in sorted(blocked))
        )

    palette = [
        tuple(int(v) for v in rgb)
        for rgb in current_palette
        if tuple(int(v) for v in rgb) not in removed
    ]

    # Garantia adicional: mantém as essenciais no começo, mesmo em projetos antigos.
    palette = _dedupe_rgbs(list(essential) + palette)

    if not palette:
        raise ValueError(
            "A paleta restante ficou vazia. Preserve pelo menos uma cor."
        )

    if len(palette) > target:
        raise ValueError(
            "A quantidade de cores preservadas é maior que o limite final."
        )

    simplified, essential = build_simplified_image(matrix, workspace, palette)
    return simplified, palette, essential


def sort_palette_by_similarity(palette):
    """
    Order palette colors so visually similar colors appear near each other.
    This is used for presentation only.
    """
    colors = _dedupe_rgbs(palette)
    if len(colors) <= 2:
        return colors

    lab = _lab_colors(colors)

    # Start with the darkest / least saturated-ish point for a stable chain.
    start = int(np.argmin(lab[:, 0]))
    remaining = set(range(len(colors)))
    order = [start]
    remaining.remove(start)
    current = start

    while remaining:
        rem = sorted(remaining)
        diff = lab[rem] - lab[current]
        d2 = np.sum(diff * diff, axis=1)
        nxt = rem[int(np.argmin(d2))]
        order.append(nxt)
        remaining.remove(nxt)
        current = nxt

    return [colors[i] for i in order]


def encode_png(arr):
    bio = io.BytesIO()
    Image.fromarray(np.asarray(arr, dtype=np.uint8), "RGB").save(
        bio, format="PNG"
    )
    return base64.b64encode(bio.getvalue()).decode("ascii")


def decode_png(data, expected_width=None, expected_height=None):
    if not data:
        return None
    try:
        raw=base64.b64decode(data)
        im=Image.open(io.BytesIO(raw)).convert("RGB")
        arr=np.asarray(im,dtype=np.uint8)
        if expected_width is not None and arr.shape[1]!=int(expected_width): return None
        if expected_height is not None and arr.shape[0]!=int(expected_height): return None
        return arr.copy()
    except Exception:
        return None
