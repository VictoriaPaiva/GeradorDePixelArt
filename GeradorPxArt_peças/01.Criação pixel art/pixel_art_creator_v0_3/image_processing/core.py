from __future__ import annotations
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from sklearn.cluster import KMeans
from skimage.color import rgb2lab, lab2rgb
from skimage.filters import sobel

SIZE=50

def pil_to_rgb_array(img): return np.asarray(img.convert('RGB'),dtype=np.uint8)
def center_square(img):
    img=img.convert('RGB'); w,h=img.size; s=min(w,h); return img.crop(((w-s)//2,(h-s)//2,(w+s)//2,(h+s)//2))
def crop_square(img,cx,cy,scale=1.0):
    w,h=img.size; side=max(1,int(min(w,h)*scale)); x=int(cx*w); y=int(cy*h)
    left=max(0,min(w-side,x-side//2)); top=max(0,min(h-side,y-side//2)); return img.crop((left,top,left+side,top+side)).convert('RGB')

def method_fidelity(square):
    return pil_to_rgb_array(square.resize((SIZE,SIZE),Image.Resampling.BOX))

def _graphic_palette(img,n=28,seed=11):
    arr=np.asarray(img.convert('RGB'),dtype=np.uint8); flat=arr.reshape(-1,3)
    # sample keeps this fast even for large photos
    step=max(1,len(flat)//18000); sample=flat[::step]
    lab=rgb2lab((sample/255.).reshape(1,-1,3)).reshape(-1,3)
    k=min(n,len(np.unique(sample,axis=0))); km=KMeans(k,n_init=5,random_state=seed).fit(lab)
    all_lab=rgb2lab((flat/255.).reshape(1,-1,3)).reshape(-1,3)
    # chunk nearest centres
    labels=[]
    for i in range(0,len(all_lab),50000):
        d=((all_lab[i:i+50000,None]-km.cluster_centers_[None])**2).sum(2); labels.append(np.argmin(d,1))
    centers=np.clip(np.rint(lab2rgb(km.cluster_centers_.reshape(1,-1,3)).reshape(-1,3)*255),0,255).astype(np.uint8)
    return Image.fromarray(centers[np.concatenate(labels)].reshape(arr.shape),'RGB')

def method_illustrated(square):
    # Flatten photographic micro-texture first, then posterize into deliberate colour masses.
    s=square.resize((300,300),Image.Resampling.LANCZOS).filter(ImageFilter.MedianFilter(7))
    s=ImageEnhance.Contrast(s).enhance(1.10); s=ImageEnhance.Color(s).enhance(1.08)
    poster=_graphic_palette(s,32,13)
    low=poster.resize((SIZE,SIZE),Image.Resampling.BOX).filter(ImageFilter.MedianFilter(3))
    return pil_to_rgb_array(low)

def method_pixel_art(square):
    # Artistic interpretation: stronger flattening + limited pre-palette + edge-aware contrast.
    s=square.resize((240,240),Image.Resampling.LANCZOS).filter(ImageFilter.MedianFilter(9))
    s=ImageEnhance.Contrast(s).enhance(1.20); s=ImageEnhance.Color(s).enhance(1.13)
    poster=_graphic_palette(s,22,23)
    base=np.asarray(poster.resize((SIZE,SIZE),Image.Resampling.BOX),dtype=np.uint8)
    gray=np.asarray(ImageOps.grayscale(s).resize((SIZE,SIZE),Image.Resampling.BOX),dtype=float)/255
    edges=sobel(gray); strong=edges>np.quantile(edges,.80)
    # Darken important boundaries slightly; this reads as drawn contours without adding antialiasing.
    out=base.astype(float); out[strong]*=.76
    out=np.clip(out,0,255).astype(np.uint8)
    return np.asarray(Image.fromarray(out).filter(ImageFilter.MedianFilter(3)),dtype=np.uint8)

def array_to_preview(arr,scale=10):
    return Image.fromarray(arr.astype(np.uint8),'RGB').resize((arr.shape[1]*scale,arr.shape[0]*scale),Image.Resampling.NEAREST)
