
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

from .pattern_utils import build_legend, render_code_pattern, render_legend


def sanitize_name(name: str) -> str:
    name=(name or "pixel_art").strip()
    name=re.sub(r'[<>:"/\\|?*]+', "_", name)
    name=re.sub(r"\s+", "_", name)
    return name.strip("._") or "pixel_art"


def save_preview(arr: np.ndarray, path: Path, size: int = 800):
    Image.fromarray(np.asarray(arr,dtype=np.uint8),"RGB").resize(
        (size,size), Image.Resampling.NEAREST
    ).save(path)


def save_grid(arr: np.ndarray, path: Path, cell_size: int = 9, grid_width: int = 1):
    arr=np.asarray(arr,dtype=np.uint8)
    h,w=arr.shape[:2]
    out_w=w*cell_size+(w+1)*grid_width
    out_h=h*cell_size+(h+1)*grid_width
    out=np.zeros((out_h,out_w,3),dtype=np.uint8)
    out[:,:,:]=np.array((55,55,55),dtype=np.uint8)

    for y in range(h):
        y0=grid_width+y*(cell_size+grid_width)
        for x in range(w):
            x0=grid_width+x*(cell_size+grid_width)
            out[y0:y0+cell_size,x0:x0+cell_size]=arr[y,x]

    Image.fromarray(out,"RGB").save(path)


def legend_rows(entries):
    return [
        {
            "code":e.code,
            "hex":e.hex,
            "rgb":list(e.rgb),
            "cells":e.count,
            "percent":e.percent,
        }
        for e in entries
    ]


def save_legend_json(entries, path: Path):
    path.write_text(
        json.dumps(legend_rows(entries),ensure_ascii=False,indent=2),
        encoding="utf-8"
    )


def save_legend_csv(entries, path: Path):
    with open(path,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f)
        w.writerow(["code","hex","r","g","b","cells","percent"])
        for e in entries:
            w.writerow([
                e.code,e.hex,*e.rgb,e.count,f"{e.percent:.6f}"
            ])


def save_legend_txt(entries, path: Path):
    lines=[
        "LEGENDA DE CORES",
        "="*60,
        "Matriz: 100x100",
        "Total de células: 10000",
        f"Total de cores: {len(entries)}",
        "",
    ]
    for e in entries:
        lines.append(
            f"{e.code} | {e.hex} | RGB{e.rgb} | "
            f"{e.count} células | {e.percent:.2f}%"
        )
    path.write_text("\n".join(lines),encoding="utf-8")


def create_export_bundle(
    arr: np.ndarray,
    output_dir: Path,
    project_name: str,
    selected_keys: set[str] | None = None,
):
    """
    Export the current final 100x100 matrix and related deliverables.

    Returns manifest rows with key, label and absolute path.
    """
    arr=np.asarray(arr,dtype=np.uint8)
    if arr.shape!=(100,100,3):
        raise ValueError(f"Matriz final inválida: {arr.shape}. Esperado 100×100 RGB.")

    output_dir=Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    base=sanitize_name(project_name)

    entries,color_to_code=build_legend(arr)
    pattern=render_code_pattern(arr,color_to_code,cell_size=34)
    legend=render_legend(entries)

    specs=[
        ("matrix","Matriz técnica 100×100",output_dir/f"{base}_matriz_100x100.png"),
        ("preview","Preview ampliado",output_dir/f"{base}_preview_800x800.png"),
        ("grid","Imagem com grade",output_dir/f"{base}_com_grade.png"),
        ("pattern","Molde com códigos",output_dir/f"{base}_molde_codificado.png"),
        ("legend_png","Legenda PNG",output_dir/f"{base}_legenda.png"),
        ("legend_json","Legenda JSON",output_dir/f"{base}_legenda.json"),
        ("legend_csv","Legenda CSV",output_dir/f"{base}_legenda.csv"),
        ("legend_txt","Legenda TXT",output_dir/f"{base}_legenda.txt"),
    ]

    selected_keys=set(selected_keys or [k for k,_,_ in specs])
    manifest=[]

    for key,label,path in specs:
        if key not in selected_keys:
            continue

        if key=="matrix":
            Image.fromarray(arr,"RGB").save(path)
        elif key=="preview":
            save_preview(arr,path)
        elif key=="grid":
            save_grid(arr,path)
        elif key=="pattern":
            pattern.save(path)
        elif key=="legend_png":
            legend.save(path)
        elif key=="legend_json":
            save_legend_json(entries,path)
        elif key=="legend_csv":
            save_legend_csv(entries,path)
        elif key=="legend_txt":
            save_legend_txt(entries,path)

        manifest.append({
            "key":key,
            "label":label,
            "path":str(path.resolve()),
        })

    manifest_path=output_dir/f"{base}_manifesto_exportacao.json"
    manifest_path.write_text(
        json.dumps(
            {
                "project":project_name,
                "matrix_size":"100x100",
                "colors":len(entries),
                "files":manifest,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8"
    )

    manifest.append({
        "key":"manifest",
        "label":"Manifesto da exportação",
        "path":str(manifest_path.resolve()),
    })

    return manifest
