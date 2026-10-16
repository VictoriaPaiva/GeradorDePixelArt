from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image
@dataclass
class ProjectState:
    source_path:Optional[Path]=None; original:Optional[Image.Image]=None; crop:Optional[Image.Image]=None
    candidates:dict[str,np.ndarray]=field(default_factory=dict); selected_method:Optional[str]=None; selected_matrix:Optional[np.ndarray]=None
    quantized_matrix:Optional[np.ndarray]=None; requested_colors:int=20; locked_colors:set=field(default_factory=set); priority_colors:dict=field(default_factory=dict)
    quant_strategy:str='balanced'; checkpoints:dict[str,object]=field(default_factory=dict)
    region_mask:np.ndarray=field(default_factory=lambda:np.zeros((50,50),dtype=np.uint8)) # 0 normal, 1 preserve, 2 simplify, 3 strong
    region_texture:np.ndarray=field(default_factory=lambda:np.zeros((50,50),dtype=np.uint8)) # 0 none, 2/3 tones
    def save_checkpoint(self,name,value):
        if isinstance(value,np.ndarray): value=value.copy()
        elif isinstance(value,Image.Image): value=value.copy()
        elif isinstance(value,(dict,set,list)): value=value.copy()
        self.checkpoints[name]=value
    def restore(self,name):
        v=self.checkpoints[name]
        if isinstance(v,np.ndarray): return v.copy()
        if isinstance(v,Image.Image): return v.copy()
        if isinstance(v,(dict,set,list)): return v.copy()
        return v
