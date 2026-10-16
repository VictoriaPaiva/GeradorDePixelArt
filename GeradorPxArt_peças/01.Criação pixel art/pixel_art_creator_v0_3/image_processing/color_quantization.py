from __future__ import annotations
import numpy as np
from sklearn.cluster import KMeans
from skimage.color import rgb2lab,lab2rgb
from scipy.ndimage import label

def _unique_colors(matrix):
    flat=matrix.reshape(-1,3); return np.unique(flat,axis=0,return_counts=True)
def _lab(a): return rgb2lab((a/255.).reshape(1,-1,3)).reshape(-1,3)

def quantize_lab(matrix,n_colors,locked_colors=None,priority_colors=None,strategy='balanced',region_mask=None,region_texture=None,random_state=42):
    locked_colors=[tuple(map(int,c)) for c in (locked_colors or [])]; priority_colors={tuple(map(int,k)):float(v) for k,v in (priority_colors or {}).items()}
    colors,counts=_unique_colors(matrix); colors=colors.astype(np.uint8)
    if len(locked_colors)>n_colors: raise ValueError(f'Existem {len(locked_colors)} cores travadas, mas apenas {n_colors} cores finais foram solicitadas.')
    region_mask=np.zeros(matrix.shape[:2],np.uint8) if region_mask is None else region_mask
    region_texture=np.zeros(matrix.shape[:2],np.uint8) if region_texture is None else region_texture
    locked=np.array(locked_colors,np.uint8).reshape(-1,3) if locked_colors else np.empty((0,3),np.uint8); locked_set=set(locked_colors)
    free_mask=np.array([tuple(c) not in locked_set for c in colors]); free=colors[free_mask]; cnt=counts[free_mask]
    k=max(0,n_colors-len(locked))
    if k>=len(free): auto=free.copy()
    elif k:
        labs=_lab(free); weights=cnt.astype(float)
        if strategy=='dominant': weights**=1.55
        elif strategy=='rare_details': weights**=.45
        for i,c in enumerate(free):
            if tuple(c) in priority_colors: weights[i]*=priority_colors[tuple(c)]
        # Region semantics affect cluster learning: preserve areas count more; simplify areas count less.
        flat=matrix.reshape(-1,3); rm=region_mask.ravel(); lookup={tuple(c):i for i,c in enumerate(free)}
        region_factor=np.ones(len(free))
        sums=np.zeros(len(free)); nums=np.zeros(len(free))
        factors=np.choose(rm,[1.0,3.0,.55,.25])
        for c,f in zip(flat,factors):
            idx=lookup.get(tuple(c));
            if idx is not None: sums[idx]+=f; nums[idx]+=1
        nz=nums>0; region_factor[nz]=sums[nz]/nums[nz]; weights*=region_factor
        km=KMeans(k,n_init=12,random_state=random_state).fit(labs,sample_weight=weights)
        auto=np.clip(np.rint(lab2rgb(km.cluster_centers_.reshape(1,-1,3)).reshape(-1,3)*255),0,255).astype(np.uint8)
    else: auto=np.empty((0,3),np.uint8)
    palette=np.vstack([locked,auto]) if len(locked) else auto
    if not len(palette): raise ValueError('Não foi possível formar a paleta.')
    flat=matrix.reshape(-1,3); src_lab=_lab(flat); pal_lab=_lab(palette); d=((src_lab[:,None]-pal_lab[None])**2).sum(2)
    # Strong simplification biases pixels toward locally dominant palette colours.
    nearest=np.argmin(d,axis=1); out=palette[nearest].reshape(matrix.shape)
    # Exact locked source RGB remains exact.
    for c in locked_colors: out[np.all(matrix==np.array(c,np.uint8),axis=2)]=np.array(c,np.uint8)
    # Spatial cleanup only in user-selected simplify regions.
    for level,radius in ((3,2),(2,1)):
        mask=region_mask==level
        if not mask.any(): continue
        cur=out.copy()
        for y,x in zip(*np.where(mask)):
            y0=max(0,y-radius); y1=min(50,y+radius+1); x0=max(0,x-radius); x1=min(50,x+radius+1)
            vals=out[y0:y1,x0:x1].reshape(-1,3); u,n=np.unique(vals,axis=0,return_counts=True); cur[y,x]=u[np.argmax(n)]
        out=cur
    out=_texture_flat_areas(out,matrix,palette,region_texture)
    final=np.unique(out.reshape(-1,3),axis=0)
    return out,final,{'original_colors':len(colors),'final_colors':len(final),'strategy':strategy,'locked':len(locked_colors),'automatic':max(0,n_colors-len(locked_colors))}

def _texture_flat_areas(out,source,palette,texture):
    """Reintroduce controlled light/dark variation using ONLY colours already in final palette."""
    if not np.any(texture): return out
    result=out.copy(); pal_lab=_lab(palette); src_lab=_lab(source.reshape(-1,3)).reshape(50,50,3)
    for tones in (2,3):
        zone=texture==tones
        if not zone.any(): continue
        for color in np.unique(out[zone].reshape(-1,3),axis=0):
            same=np.all(out==color,axis=2)&zone; comps,num=label(same)
            base_lab=_lab(np.array(color).reshape(1,3))[0]; distances=((pal_lab-base_lab)**2).sum(1); order=np.argsort(distances)
            # candidates on darker/lighter L side, falling back to nearest palette colours
            darker=[i for i in order if pal_lab[i,0]<base_lab[0]-2]; lighter=[i for i in order if pal_lab[i,0]>base_lab[0]+2]
            choices=[]
            if darker: choices.append(palette[darker[0]])
            choices.append(np.array(color,np.uint8))
            if lighter: choices.append(palette[lighter[0]])
            if tones==2 and len(choices)>=3: choices=[choices[0],choices[-1]]
            if len(choices)<2: continue
            for comp in range(1,num+1):
                ys,xs=np.where(comps==comp)
                if len(ys)<10: continue
                L=src_lab[ys,xs,0]; qs=np.quantile(L,[.45] if tones==2 else [.33,.67])
                bins=np.digitize(L,qs)
                for j,(y,x) in enumerate(zip(ys,xs)): result[y,x]=choices[min(bins[j],len(choices)-1)]
    return result

def color_info(matrix,color):
    c=np.array(color,np.uint8); n=int(np.all(matrix==c,axis=2).sum()); return n,n/2500*100
