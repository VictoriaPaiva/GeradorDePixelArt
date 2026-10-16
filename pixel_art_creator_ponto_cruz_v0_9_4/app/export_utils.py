from __future__ import annotations
import csv,json,re
from pathlib import Path
import numpy as np
from PIL import Image
from .pattern_utils import build_legend,render_code_pattern,render_symbol_pattern,render_legend


def sanitize_name(name):
    name=re.sub(r'[<>:"/\\|?*]+','_',str(name or 'ponto_cruz').strip())
    name=re.sub(r'\s+','_',name)
    return name.strip('._') or 'ponto_cruz'


def save_preview(arr,path,size=900):
    arr=np.asarray(arr,dtype=np.uint8)
    h,w=arr.shape[:2]
    scale=size/max(w,h)
    nw=max(1,int(round(w*scale)))
    nh=max(1,int(round(h*scale)))
    Image.fromarray(arr,'RGB').resize((nw,nh),Image.Resampling.NEAREST).save(path)


def save_grid(arr,path,cell_size=9,grid_width=1):
    arr=np.asarray(arr,dtype=np.uint8)
    h,w=arr.shape[:2]
    out=np.full((h*cell_size+(h+1)*grid_width,w*cell_size+(w+1)*grid_width,3),55,dtype=np.uint8)
    for y in range(h):
        y0=grid_width+y*(cell_size+grid_width)
        for x in range(w):
            x0=grid_width+x*(cell_size+grid_width)
            out[y0:y0+cell_size,x0:x0+cell_size]=arr[y,x]
    Image.fromarray(out,'RGB').save(path)


def rows(entries):
    return [
        {'code':e.code,'hex':e.hex,'rgb':list(e.rgb),'points':e.count,'percent':e.percent}
        for e in entries
    ]


def save_json(entries,path,w,h):
    Path(path).write_text(
        json.dumps(
            {'grid':{'width':w,'height':h,'points':w*h},'colors':rows(entries)},
            ensure_ascii=False,indent=2
        ),
        encoding='utf-8'
    )


def save_csv(entries,path):
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        wr=csv.writer(f)
        wr.writerow(['codigo','hex','r','g','b','pontos','percentual'])
        for e in entries:
            wr.writerow([e.code,e.hex,*e.rgb,e.count,f'{e.percent:.6f}'])


def save_txt(entries,path,w,h):
    lines=[
        f'GUIA DE PONTO CRUZ — {w}x{h}',
        f'Total de pontos: {w*h:,}',
        f'Cores: {len(entries)}',
        ''
    ]
    lines += [
        f'{e.code} | {e.hex} | RGB{e.rgb} | {e.count:,} pontos | {e.percent:.2f}%'
        for e in entries
    ]
    Path(path).write_text('\n'.join(lines),encoding='utf-8')


def create_export_bundle(arr,output_dir,project_name,selected_keys=None):
    arr=np.asarray(arr,dtype=np.uint8)
    if arr.ndim!=3 or arr.shape[2]!=3:
        raise ValueError('Matriz final RGB inválida.')

    h,w=arr.shape[:2]
    output_dir=Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    base=sanitize_name(project_name)

    entries,codes=build_legend(arr)
    cell=max(18,min(28,int(1900/max(h,w))))
    chart_color=render_code_pattern(arr,codes,cell_size=cell)
    chart_symbols=render_symbol_pattern(arr,codes,cell_size=cell)
    legend=render_legend(entries,w,h)

    specs=[
        ('matrix','Matriz técnica',output_dir/f'{base}_matriz_{w}x{h}.png'),
        ('preview','Preview ampliado',output_dir/f'{base}_preview.png'),
        ('grid','Imagem com grade simples',output_dir/f'{base}_com_grade.png'),
        ('pattern_color','Grade colorida com códigos',output_dir/f'{base}_grafico_colorido_{w}x{h}.png'),
        ('pattern_symbols','Grade para impressão com códigos',output_dir/f'{base}_grafico_codigos_{w}x{h}.png'),
        ('legend_png','Legenda PNG',output_dir/f'{base}_legenda.png'),
        ('legend_json','Legenda JSON',output_dir/f'{base}_legenda.json'),
        ('legend_csv','Legenda CSV',output_dir/f'{base}_legenda.csv'),
        ('legend_txt','Legenda TXT',output_dir/f'{base}_legenda.txt'),
    ]

    selected=set(selected_keys or [x[0] for x in specs])
    manifest=[]

    for key,label,path in specs:
        if key not in selected:
            continue
        if key=='matrix':
            Image.fromarray(arr,'RGB').save(path)
        elif key=='preview':
            save_preview(arr,path)
        elif key=='grid':
            save_grid(arr,path)
        elif key=='pattern_color':
            chart_color.save(path)
        elif key=='pattern_symbols':
            chart_symbols.save(path)
        elif key=='legend_png':
            legend.save(path)
        elif key=='legend_json':
            save_json(entries,path,w,h)
        elif key=='legend_csv':
            save_csv(entries,path)
        elif key=='legend_txt':
            save_txt(entries,path,w,h)
        manifest.append({'key':key,'label':label,'path':str(path.resolve())})

    mp=output_dir/f'{base}_manifesto_exportacao.json'
    mp.write_text(
        json.dumps(
            {
                'project':project_name,
                'grid':f'{w}x{h}',
                'points':w*h,
                'colors':len(entries),
                'files':manifest,
            },
            ensure_ascii=False,indent=2
        ),
        encoding='utf-8'
    )
    manifest.append({'key':'manifest','label':'Manifesto','path':str(mp.resolve())})
    return manifest
