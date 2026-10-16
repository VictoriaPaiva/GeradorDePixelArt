from __future__ import annotations
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from sklearn.cluster import KMeans
from skimage.color import rgb2lab, lab2rgb
from skimage.filters import sobel
from skimage.segmentation import slic
from scipy.ndimage import median_filter

SIZE=50

def pil_to_rgb_array(img): return np.asarray(img.convert('RGB'),dtype=np.uint8)
def center_square(img):
    img=img.convert('RGB'); w,h=img.size; s=min(w,h); return img.crop(((w-s)//2,(h-s)//2,(w+s)//2,(h+s)//2))
def crop_square(img,cx,cy,scale=1.0):
    w,h=img.size; side=max(1,int(min(w,h)*scale)); x=int(cx*w); y=int(cy*h)
    left=max(0,min(w-side,x-side//2)); top=max(0,min(h-side,y-side//2)); return img.crop((left,top,left+side,top+side)).convert('RGB')

def _lab(rgb):
    a=np.asarray(rgb,dtype=float)/255.; return rgb2lab(a.reshape(1,-1,3)).reshape(-1,3)

def _rgb_from_lab(lab):
    return np.clip(np.rint(lab2rgb(np.asarray(lab).reshape(1,-1,3)).reshape(-1,3)*255),0,255).astype(np.uint8)

def _distinct_palette(arr,n=28,min_delta=10.0,seed=1):
    """Build a deliberately spaced palette. Nearby photographic shades do not all earn a slot."""
    flat=arr.reshape(-1,3); step=max(1,len(flat)//18000); sample=flat[::step]
    labs=_lab(sample); k=min(max(n*2,24),len(np.unique(sample,axis=0)))
    km=KMeans(k,n_init=8,random_state=seed).fit(labs)
    counts=np.bincount(km.labels_,minlength=k); order=np.argsort(counts)[::-1]
    chosen=[]
    for idx in order:
        c=km.cluster_centers_[idx]
        if not chosen or min(np.linalg.norm(c-x) for x in chosen)>=min_delta:
            chosen.append(c)
        if len(chosen)>=n: break
    # If spacing was too strict, add the most useful remaining centres.
    if len(chosen)<min(n,k):
        for idx in order:
            c=km.cluster_centers_[idx]
            if not any(np.linalg.norm(c-x)<1e-6 for x in chosen): chosen.append(c)
            if len(chosen)>=n: break
    return _rgb_from_lab(np.array(chosen))

def _map_palette(arr,palette):
    src=_lab(arr.reshape(-1,3)); pal=_lab(palette)
    labels=[]
    for i in range(0,len(src),20000):
        d=((src[i:i+20000,None]-pal[None])**2).sum(2); labels.append(np.argmin(d,1))
    return palette[np.concatenate(labels)].reshape(arr.shape)

def _planarize(arr,segments=260,compactness=11):
    """Replace photographic microtexture by coherent visual regions while keeping boundaries."""
    f=arr.astype(float)/255.
    seg=slic(f,n_segments=segments,compactness=compactness,sigma=.7,start_label=0,channel_axis=-1)
    out=np.empty_like(arr)
    for s in np.unique(seg):
        m=seg==s
        # Median is more robust than mean and avoids muddy boundary colours.
        out[m]=np.median(arr[m],axis=0).astype(np.uint8)
    return out

def _edge_map(square):
    hi=np.asarray(square.resize((SIZE,SIZE),Image.Resampling.LANCZOS).convert('L'),dtype=float)/255.
    return sobel(hi)

def _break_gradients(arr,edge,passes=1):
    """Remove one-cell shade ladders away from structural edges, creating deliberate colour planes."""
    out=arr.copy()
    for _ in range(passes):
        lab=_lab(out.reshape(-1,3)).reshape(SIZE,SIZE,3); new=out.copy()
        for y in range(SIZE):
            for x in range(SIZE):
                if edge[y,x]>.105: continue
                y0=max(0,y-1); y1=min(SIZE,y+2); x0=max(0,x-1); x1=min(SIZE,x+2)
                block=out[y0:y1,x0:x1].reshape(-1,3)
                u,c=np.unique(block,axis=0,return_counts=True); dom=u[np.argmax(c)]
                # Snap only when perceptually close: this kills subtle gradients without crossing real colour boundaries.
                d=np.linalg.norm(_lab(np.vstack([out[y,x],dom]))[0]-_lab(np.vstack([out[y,x],dom]))[1])
                if d<11: new[y,x]=dom
        out=new
    return out

def _edge_accent(arr,edge,strength=.18):
    out=arr.astype(float); threshold=np.quantile(edge,.78); m=edge>=threshold
    # Accent boundaries by darkening existing colours rather than painting a universal black outline.
    out[m]*=(1.0-strength)
    return np.clip(out,0,255).astype(np.uint8)

def method_fidelity(square):
    """Photographic pixelization: intentionally keeps local photographic information."""
    s=ImageEnhance.Contrast(square.convert('RGB')).enhance(1.04)
    return pil_to_rgb_array(s.resize((SIZE,SIZE),Image.Resampling.BOX))

def method_illustrated(square):
    """Illustrated: coherent regions + separated shades + preserved boundaries, not blur."""
    work=square.resize((260,260),Image.Resampling.LANCZOS)
    # Light denoise only; structural boundaries remain available.
    work=work.filter(ImageFilter.MedianFilter(3))
    raw=np.asarray(work,dtype=np.uint8)
    planes=_planarize(raw,segments=360,compactness=9)
    small=np.asarray(Image.fromarray(planes).resize((SIZE,SIZE),Image.Resampling.BOX),dtype=np.uint8)
    pal=_distinct_palette(small,34,min_delta=7.5,seed=13)
    out=_map_palette(small,pal)
    edge=_edge_map(square)
    out=_break_gradients(out,edge,passes=1)
    return _edge_accent(out,edge,.09)

def method_pixel_art(square):
    """Artistic pixel art: colour planes, stronger palette ramps, gradient breaks and selective edge accents."""
    work=square.resize((260,260),Image.Resampling.LANCZOS)
    work=ImageEnhance.Color(work).enhance(1.12)
    work=ImageEnhance.Contrast(work).enhance(1.10)
    raw=np.asarray(work.filter(ImageFilter.MedianFilter(3)),dtype=np.uint8)
    # Fewer/larger visual regions than illustrated mode.
    planes=_planarize(raw,segments=235,compactness=13)
    small=np.asarray(Image.fromarray(planes).resize((SIZE,SIZE),Image.Resampling.BOX),dtype=np.uint8)
    # Stronger minimum perceptual spacing produces visible shade steps instead of near-identical RGB ladders.
    pal=_distinct_palette(small,26,min_delta=11.5,seed=23)
    out=_map_palette(small,pal)
    edge=_edge_map(square)
    out=_break_gradients(out,edge,passes=2)
    out=_edge_accent(out,edge,.17)
    # One categorical cleanup pass removes isolated photographic speckles but keeps palette colours exact.
    result=out.copy()
    for y in range(1,SIZE-1):
        for x in range(1,SIZE-1):
            if edge[y,x]>.12: continue
            block=out[y-1:y+2,x-1:x+2].reshape(-1,3); u,c=np.unique(block,axis=0,return_counts=True)
            if c.max()>=5: result[y,x]=u[np.argmax(c)]
    return result

def array_to_preview(arr,scale=10):
    return Image.fromarray(arr.astype(np.uint8),'RGB').resize((arr.shape[1]*scale,arr.shape[0]*scale),Image.Resampling.NEAREST)
