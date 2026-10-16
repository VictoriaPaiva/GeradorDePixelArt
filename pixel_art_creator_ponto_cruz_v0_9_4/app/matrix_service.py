
from __future__ import annotations
import base64,io
import numpy as np
from PIL import Image


def image_to_matrix(image:Image.Image, width:int, height:int)->np.ndarray:
    """Convert image to exact logical grid. One solid real source RGB per cell."""
    arr=np.asarray(image.convert('RGB'),dtype=np.uint8); h,w=arr.shape[:2]
    width=int(width); height=int(height)
    if width<1 or height<1: raise ValueError('Dimensões inválidas.')
    out=np.zeros((height,width,3),dtype=np.uint8)
    ys=np.linspace(0,h,height+1); xs=np.linspace(0,w,width+1)
    for gy in range(height):
        y0=int(np.floor(ys[gy])); y1=int(np.floor(ys[gy+1]))
        if y1<=y0: y0=min(h-1,int(round((gy+.5)*h/height))); y1=min(h,y0+1)
        for gx in range(width):
            x0=int(np.floor(xs[gx])); x1=int(np.floor(xs[gx+1]))
            if x1<=x0: x0=min(w-1,int(round((gx+.5)*w/width))); x1=min(w,x0+1)
            block=arr[y0:y1,x0:x1].reshape(-1,3)
            if len(block)==0:
                out[gy,gx]=arr[min(h-1,int((gy+.5)*h/height)),min(w-1,int((gx+.5)*w/width))]; continue
            median=np.median(block.astype(np.float32),axis=0)
            d=block.astype(np.float32)-median[None,:]
            out[gy,gx]=block[int(np.argmin(np.sum(d*d,axis=1)))]
    return out



def image_to_matrix_preserve(image: Image.Image, width: int, height: int) -> np.ndarray:
    """Technical normalization for a Chat-generated matrix-ready artwork.

    This intentionally does no local median/averaging. The already-designed
    artwork is resized with nearest-neighbor sampling only, so the app does not
    reinterpret focal details artistically.
    """
    width=int(width); height=int(height)
    if width<1 or height<1:
        raise ValueError('Dimensões inválidas.')
    im=image.convert('RGB')
    if im.size==(width,height):
        return np.asarray(im,dtype=np.uint8).copy()
    normalized=im.resize((width,height), Image.Resampling.NEAREST)
    return np.asarray(normalized,dtype=np.uint8).copy()

def image_to_matrix_100(image): return image_to_matrix(image,100,100)

def encode_matrix_png(arr):
    bio=io.BytesIO(); Image.fromarray(np.asarray(arr,dtype=np.uint8),'RGB').save(bio,format='PNG')
    return base64.b64encode(bio.getvalue()).decode('ascii')

def decode_matrix_png(data, expected_width=None, expected_height=None):
    if not data:return None
    try:
        im=Image.open(io.BytesIO(base64.b64decode(data))).convert('RGB'); arr=np.asarray(im,dtype=np.uint8)
        if expected_width is not None and arr.shape[1]!=int(expected_width): return None
        if expected_height is not None and arr.shape[0]!=int(expected_height): return None
        return arr.copy()
    except Exception:return None

def enlarged_preview(arr,size=800):
    arr=np.asarray(arr,dtype=np.uint8); h,w=arr.shape[:2]
    scale=size/max(w,h); nw=max(1,int(round(w*scale))); nh=max(1,int(round(h*scale)))
    return Image.fromarray(arr,'RGB').resize((nw,nh),Image.Resampling.NEAREST)
