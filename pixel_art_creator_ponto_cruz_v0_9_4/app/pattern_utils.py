from dataclasses import dataclass
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class LegendEntry:
    index: int
    code: str
    rgb: tuple
    count: int
    percent: float

    @property
    def hex(self):
        return "#{:02X}{:02X}{:02X}".format(*self.rgb)


def make_code(index:int)->str:
    # C01..C99: compact, stable and easy to read in a chart.
    return f"C{index+1:02d}"


def build_legend(arr:np.ndarray):
    flat=[tuple(map(int,x)) for x in arr.reshape(-1,3)]
    counts=Counter(flat)
    total=len(flat)

    # Stable legend: most-used colors first; RGB is deterministic tie-breaker.
    ordered=sorted(counts.items(), key=lambda x:(-x[1], x[0]))

    entries=[]
    color_to_code={}
    for i,(rgb,count) in enumerate(ordered):
        code=make_code(i)
        entry=LegendEntry(
            index=i,
            code=code,
            rgb=rgb,
            count=count,
            percent=count/total*100.0,
        )
        entries.append(entry)
        color_to_code[rgb]=code

    return entries,color_to_code


def validate_matrix(arr):
    if arr is None:
        return False,"Nenhuma matriz disponível."
    if arr.ndim!=3 or arr.shape[2]!=3:
        return False,"A imagem precisa estar em RGB."
    h,w=arr.shape[:2]
    if not(50<=w<=100 and 50<=h<=100):
        return False,f"A grade deve ter entre 50 e 100 linhas/colunas; recebida {w}×{h}."
    colors=len(np.unique(arr.reshape(-1,3),axis=0))
    if colors>50:
        return False,f"A matriz possui {colors} cores. Reduza para até 50 antes de gerar a legenda."
    return True,f"Matriz {w}×{h} válida com {colors} cores."


def _font_for_cell(cell_size):
    # Default font is universally available. Codes are compact enough for >=18px cells.
    return ImageFont.load_default()


def _coord_positions(length):
    vals={1,length}
    for v in range(5,length+1,5):
        vals.add(v)
    return sorted(vals)


def render_cross_stitch_chart(
    arr,
    color_to_code,
    cell_size=24,
    colored=False,
    major_every=10,
):
    """Render a printable cross-stitch chart.

    colored=False -> white cells + black codes (printer-friendly)
    colored=True  -> actual cell color + contrasting code
    """
    arr=np.asarray(arr,dtype=np.uint8)
    h,w=arr.shape[:2]
    margin_left=62
    margin_top=62
    margin_right=24
    margin_bottom=24
    out_w=margin_left+w*cell_size+margin_right
    out_h=margin_top+h*cell_size+margin_bottom
    img=Image.new("RGB",(out_w,out_h),"white")
    d=ImageDraw.Draw(img)
    font=_font_for_cell(cell_size)
    coord_font=ImageFont.load_default()

    # Coordinate labels every 5 stitches + first/last.
    for x1 in _coord_positions(w):
        x=x1-1
        px=margin_left+x*cell_size+cell_size//2
        label=str(x1)
        bbox=d.textbbox((0,0),label,font=coord_font)
        tw=bbox[2]-bbox[0]
        d.text((px-tw/2, margin_top-24),label,fill="black",font=coord_font)

    for y1 in _coord_positions(h):
        y=y1-1
        py=margin_top+y*cell_size+cell_size//2
        label=str(y1)
        bbox=d.textbbox((0,0),label,font=coord_font)
        tw=bbox[2]-bbox[0]
        th=bbox[3]-bbox[1]
        d.text((margin_left-12-tw,py-th/2),label,fill="black",font=coord_font)

    # Cell fills + codes.
    for y in range(h):
        for x in range(w):
            rgb=tuple(map(int,arr[y,x]))
            code=color_to_code[rgb]
            x0=margin_left+x*cell_size
            y0=margin_top+y*cell_size
            x1=x0+cell_size
            y1=y0+cell_size
            fill=rgb if colored else (255,255,255)
            d.rectangle((x0,y0,x1,y1),fill=fill)

            if colored:
                lum=0.2126*rgb[0]+0.7152*rgb[1]+0.0722*rgb[2]
                tc="black" if lum>145 else "white"
            else:
                tc="black"

            bbox=d.textbbox((0,0),code,font=font)
            tw=bbox[2]-bbox[0]
            th=bbox[3]-bbox[1]
            # On small cells, codes can be a touch dense, but remain legible in saved PNG zoom.
            d.text((x0+(cell_size-tw)/2,y0+(cell_size-th)/2-1),code,fill=tc,font=font)

    # Grid drawn after content: thin every stitch, thick every 10 stitches.
    x_start=margin_left
    y_start=margin_top
    x_end=margin_left+w*cell_size
    y_end=margin_top+h*cell_size

    for x in range(w+1):
        px=x_start+x*cell_size
        width=3 if x%major_every==0 else 1
        shade=(20,20,20) if width>1 else (150,150,150)
        d.line((px,y_start,px,y_end),fill=shade,width=width)

    for y in range(h+1):
        py=y_start+y*cell_size
        width=3 if y%major_every==0 else 1
        shade=(20,20,20) if width>1 else (150,150,150)
        d.line((x_start,py,x_end,py),fill=shade,width=width)

    return img


def render_code_pattern(arr, color_to_code, cell_size=24, **kwargs):
    # Backward-compatible alias: colored chart.
    return render_cross_stitch_chart(
        arr,color_to_code,cell_size=cell_size,colored=True,
        major_every=kwargs.get("major_every",10)
    )


def render_symbol_pattern(arr, color_to_code, cell_size=24):
    return render_cross_stitch_chart(
        arr,color_to_code,cell_size=cell_size,colored=False,major_every=10
    )


def render_legend(entries, grid_width=None, grid_height=None, columns=2, item_w=500, item_h=82, margin=28):
    rows=(len(entries)+columns-1)//columns
    summary_h=84
    width=margin*2+columns*item_w
    height=margin*2+summary_h+rows*item_h

    img=Image.new("RGB",(width,height),"white")
    d=ImageDraw.Draw(img)
    font=ImageFont.load_default()

    d.text((margin,16),"LEGENDA - GUIA DE PONTO CRUZ",fill="black",font=font)
    y=36
    if grid_width and grid_height:
        d.text((margin,y),f"Grade: {grid_width}x{grid_height}  |  Total de pontos: {grid_width*grid_height:,}",fill="black",font=font)
        y+=18
    d.text((margin,y),f"Cores usadas: {len(entries)}",fill="black",font=font)

    base_y=margin+summary_h
    for i,e in enumerate(entries):
        col=i%columns
        row=i//columns
        x=margin+col*item_w
        y=base_y+row*item_h

        d.rectangle((x,y,x+58,y+58),fill=e.rgb,outline="black",width=1)
        d.text((x+72,y+1),f"{e.code}   {e.hex}",fill="black",font=font)
        d.text((x+72,y+21),f"RGB {e.rgb}",fill="black",font=font)
        d.text((x+72,y+41),f"{e.count:,} pontos  |  {e.percent:.2f}%",fill="black",font=font)

    return img
