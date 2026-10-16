from __future__ import annotations
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

SIZE = 50

def pil_to_rgb_array(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert('RGB'), dtype=np.uint8)

def center_square(img: Image.Image) -> Image.Image:
    img = img.convert('RGB')
    w, h = img.size
    side = min(w, h)
    left = (w-side)//2; top=(h-side)//2
    return img.crop((left, top, left+side, top+side))

def crop_square(img: Image.Image, cx: float, cy: float, scale: float=1.0) -> Image.Image:
    w,h=img.size; side=max(1, int(min(w,h)*scale))
    x=int(cx*w); y=int(cy*h)
    left=max(0,min(w-side,x-side//2)); top=max(0,min(h-side,y-side//2))
    return img.crop((left,top,left+side,top+side)).convert('RGB')

def method_fidelity(square: Image.Image) -> np.ndarray:
    # BOX averages the source area represented by each destination cell.
    out=square.resize((SIZE,SIZE), Image.Resampling.BOX)
    return pil_to_rgb_array(out)

def method_details(square: Image.Image) -> np.ndarray:
    # Mild unsharp masking before area sampling retains boundaries without dithering.
    sharpened=square.filter(ImageFilter.UnsharpMask(radius=1.4, percent=165, threshold=3))
    out=sharpened.resize((SIZE,SIZE), Image.Resampling.LANCZOS)
    out=out.filter(ImageFilter.UnsharpMask(radius=.65, percent=125, threshold=2))
    return pil_to_rgb_array(out)

def method_pixel_art(square: Image.Image) -> np.ndarray:
    # Contrast/color shaping + median cleanup creates a more graphic low-res rendition.
    base=ImageEnhance.Contrast(square).enhance(1.12)
    base=ImageEnhance.Color(base).enhance(1.08)
    pre=base.resize((100,100), Image.Resampling.BOX).filter(ImageFilter.MedianFilter(size=3))
    out=pre.resize((SIZE,SIZE), Image.Resampling.BOX)
    return pil_to_rgb_array(out)

def array_to_preview(arr: np.ndarray, scale: int=10) -> Image.Image:
    return Image.fromarray(arr.astype(np.uint8),'RGB').resize((arr.shape[1]*scale,arr.shape[0]*scale),Image.Resampling.NEAREST)
