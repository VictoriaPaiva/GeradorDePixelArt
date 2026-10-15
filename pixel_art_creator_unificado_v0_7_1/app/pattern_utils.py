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
    # A..Z, Aa..Az, Ba..Bz...
    if index < 26:
        return chr(65+index)
    index -= 26
    return chr(65 + index//26) + chr(97 + index%26)


def build_legend(arr:np.ndarray):
    flat=[tuple(map(int,x)) for x in arr.reshape(-1,3)]
    counts=Counter(flat)
    total=len(flat)

    # Approved behavior: stable frequency-descending legend.
    ordered=sorted(counts.items(), key=lambda x:x[1], reverse=True)

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
        return False, "Nenhuma matriz disponível."
    if arr.ndim != 3 or arr.shape[2] != 3:
        return False, "A imagem precisa estar em RGB."
    h,w=arr.shape[:2]
    if h != 100 or w != 100:
        return False, f"A matriz precisa ser 100×100; recebida {w}×{h}."
    return True, "Matriz 100×100 válida."


def render_code_pattern(arr, color_to_code, cell_size=34, margin_left=70, margin_top=70):
    h,w=arr.shape[:2]

    out_w=margin_left+w*cell_size+20
    out_h=margin_top+h*cell_size+20

    img=Image.new("RGB",(out_w,out_h),"white")
    d=ImageDraw.Draw(img)

    font=ImageFont.load_default()
    font_small=ImageFont.load_default()

    # Column labels
    for x in range(w):
        label=str(x+1)
        px=margin_left+x*cell_size+cell_size//2
        bbox=d.textbbox((0,0),label,font=font_small)
        tw=bbox[2]-bbox[0]
        d.text((px-tw/2, margin_top-22), label, fill="black", font=font_small)

    # Row labels
    for y in range(h):
        label=str(y+1)
        py=margin_top+y*cell_size+cell_size//2
        bbox=d.textbbox((0,0),label,font=font_small)
        tw=bbox[2]-bbox[0]
        th=bbox[3]-bbox[1]
        d.text((margin_left-12-tw, py-th/2), label, fill="black", font=font_small)

    # Cells
    for y in range(h):
        for x in range(w):
            rgb=tuple(map(int,arr[y,x]))
            code=color_to_code[rgb]
            x0=margin_left+x*cell_size
            y0=margin_top+y*cell_size
            x1=x0+cell_size
            y1=y0+cell_size

            d.rectangle((x0,y0,x1,y1), fill=rgb, outline=(45,45,45), width=1)

            lum=0.2126*rgb[0]+0.7152*rgb[1]+0.0722*rgb[2]
            tc="black" if lum>145 else "white"

            bbox=d.textbbox((0,0),code,font=font)
            tw=bbox[2]-bbox[0]
            th=bbox[3]-bbox[1]
            d.text(
                (x0+(cell_size-tw)/2, y0+(cell_size-th)/2-1),
                code, fill=tc, font=font
            )

    return img


def render_legend(entries, columns=3, item_w=360, item_h=78, margin=25):
    rows=(len(entries)+columns-1)//columns
    width=margin*2+columns*item_w
    height=margin*2+rows*item_h+55

    img=Image.new("RGB",(width,height),"white")
    d=ImageDraw.Draw(img)
    font=ImageFont.load_default()

    d.text((margin,15),"LEGENDA DE CORES",fill="black",font=font)

    for i,e in enumerate(entries):
        col=i%columns
        row=i//columns
        x=margin+col*item_w
        y=55+row*item_h

        d.rectangle((x,y,x+54,y+54),fill=e.rgb,outline="black")
        d.text((x+68,y+2),f"{e.code}   {e.hex}",fill="black",font=font)
        d.text((x+68,y+20),f"RGB {e.rgb}",fill="black",font=font)
        d.text((x+68,y+38),f"{e.count} células  •  {e.percent:.2f}%",fill="black",font=font)

    return img
