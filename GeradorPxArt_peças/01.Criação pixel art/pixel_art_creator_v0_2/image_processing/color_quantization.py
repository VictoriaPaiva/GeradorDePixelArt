from __future__ import annotations
import numpy as np
from sklearn.cluster import KMeans
from skimage.color import rgb2lab, lab2rgb


def _unique_colors(matrix):
    flat=matrix.reshape(-1,3)
    colors, counts=np.unique(flat,axis=0,return_counts=True)
    return colors.astype(np.uint8), counts


def quantize_lab(matrix:np.ndarray,n_colors:int,locked_colors=None,priority_colors=None,strategy='balanced',random_state=42):
    locked_colors=[tuple(map(int,c)) for c in (locked_colors or [])]
    priority_colors={tuple(map(int,k)):float(v) for k,v in (priority_colors or {}).items()}
    colors,counts=_unique_colors(matrix)
    if n_colors<1: raise ValueError('A quantidade de cores deve ser pelo menos 1.')
    if len(locked_colors)>n_colors: raise ValueError(f'Existem {len(locked_colors)} cores travadas, mas apenas {n_colors} cores finais foram solicitadas.')
    if n_colors>=len(colors):
        palette=colors.copy(); return matrix.copy(),palette,{'original_colors':len(colors),'final_colors':len(colors),'strategy':strategy}

    locked=np.array(locked_colors,dtype=np.uint8).reshape(-1,3) if locked_colors else np.empty((0,3),dtype=np.uint8)
    locked_set=set(locked_colors)
    free_mask=np.array([tuple(c) not in locked_set for c in colors])
    free_colors=colors[free_mask]; free_counts=counts[free_mask]
    k=n_colors-len(locked)
    if k<=0:
        auto=np.empty((0,3),dtype=np.uint8)
    else:
        lab=rgb2lab((free_colors/255.0).reshape(1,-1,3)).reshape(-1,3)
        weights=free_counts.astype(float)
        if strategy=='dominant': weights=np.power(weights,1.55)
        elif strategy=='rare_details': weights=np.power(weights,.45)
        for i,c in enumerate(free_colors):
            if tuple(c) in priority_colors: weights[i]*=max(1.0,priority_colors[tuple(c)])
        km=KMeans(n_clusters=k,n_init=12,random_state=random_state)
        km.fit(lab,sample_weight=weights)
        auto=np.clip(np.rint(lab2rgb(km.cluster_centers_.reshape(1,-1,3)).reshape(-1,3)*255),0,255).astype(np.uint8)
    palette=np.vstack([locked,auto]) if len(locked) else auto

    flat=matrix.reshape(-1,3); out=np.empty_like(flat)
    # Locked source colors stay exactly unchanged.
    for c in locked_colors:
        mask=np.all(flat==np.array(c,dtype=np.uint8),axis=1); out[mask]=np.array(c,dtype=np.uint8)
    unlocked_mask=np.ones(len(flat),dtype=bool)
    for c in locked_colors: unlocked_mask &= ~np.all(flat==np.array(c,dtype=np.uint8),axis=1)
    if unlocked_mask.any():
        src_lab=rgb2lab((flat[unlocked_mask]/255.0).reshape(1,-1,3)).reshape(-1,3)
        pal_lab=rgb2lab((palette/255.0).reshape(1,-1,3)).reshape(-1,3)
        dist=((src_lab[:,None,:]-pal_lab[None,:,:])**2).sum(axis=2)
        out[unlocked_mask]=palette[np.argmin(dist,axis=1)]
    result=out.reshape(matrix.shape)
    final_palette=np.unique(result.reshape(-1,3),axis=0)
    return result,final_palette,{'original_colors':len(colors),'final_colors':len(final_palette),'strategy':strategy,'locked':len(locked_colors),'automatic':max(0,n_colors-len(locked_colors))}


def color_info(matrix,color):
    c=np.array(color,dtype=np.uint8); count=int(np.all(matrix==c,axis=2).sum())
    return count, count/2500*100
