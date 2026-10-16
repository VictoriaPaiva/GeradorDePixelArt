
from dataclasses import dataclass
from collections import Counter
from typing import Tuple
import numpy as np
from skimage.color import rgb2lab


@dataclass(frozen=True)
class PaletteGroup:
    code: str
    rgb: Tuple[int, int, int]
    count: int
    percent: float
    member_count: int

    @property
    def hex(self):
        return "#{:02X}{:02X}{:02X}".format(*self.rgb)


def make_code(i: int) -> str:
    if i < 26:
        return chr(65+i)
    i -= 26
    return chr(65+i//26) + chr(97+i%26)


def _sat(c):
    mx, mn = max(c), min(c)
    return 0.0 if mx == 0 else (mx-mn)/mx


def _representative(members):
    rgbs=np.array([m[0] for m in members],dtype=float)
    weights=np.array([m[1] for m in members],dtype=float)
    avg=np.average(rgbs,axis=0,weights=weights)
    d2=((rgbs-avg)**2).sum(axis=1)
    return tuple(int(x) for x in rgbs[np.argmin(d2)])


def grouped_colors_from_pixels(pixels, limit=200, delta_e_threshold=4.0, max_exact_candidates=5000):
    if pixels.size == 0:
        return []

    pixels=pixels.reshape(-1,3).astype(np.uint8)
    total=len(pixels)
    counts=Counter(map(tuple,pixels.tolist()))
    unique=list(counts.keys())

    if len(unique) <= limit:
        ordered=sorted(counts.items(),key=lambda x:x[1],reverse=True)
        return [
            PaletteGroup(make_code(i),tuple(map(int,c)),n,n/total*100.0,1)
            for i,(c,n) in enumerate(ordered)
        ]

    frequent=[c for c,_ in counts.most_common(max_exact_candidates)]
    vivid=sorted(unique,key=lambda c:(_sat(c),counts[c]),reverse=True)[:1500]
    pool=list(dict.fromkeys(frequent+vivid))

    pool_rgb=np.array(pool,dtype=float)/255.0
    pool_lab=rgb2lab(pool_rgb.reshape(1,-1,3)).reshape(-1,3)

    order=sorted(range(len(pool)),key=lambda i:counts[pool[i]],reverse=True)

    groups=[]
    centroids=[]
    weights=[]

    for idx in order:
        c=pool[idx]
        lab=pool_lab[idx]
        n=counts[c]

        if not groups:
            groups.append([(c,n)])
            centroids.append(lab.copy())
            weights.append(n)
            continue

        labs=np.vstack(centroids)
        d=np.linalg.norm(labs-lab,axis=1)
        j=int(np.argmin(d))

        if d[j] <= delta_e_threshold:
            groups[j].append((c,n))
            old=weights[j]
            new=old+n
            centroids[j]=(centroids[j]*old+lab*n)/new
            weights[j]=new
        else:
            groups.append([(c,n)])
            centroids.append(lab.copy())
            weights.append(n)

    data=[]
    for members in groups:
        n=sum(v for _,v in members)
        data.append((_representative(members),n,len(members)))

    data.sort(key=lambda x:x[1],reverse=True)
    data=data[:limit]

    return [
        PaletteGroup(make_code(i),rgb,n,n/total*100.0,mcount)
        for i,(rgb,n,mcount) in enumerate(data)
    ]
