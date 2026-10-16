from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image

@dataclass
class ProjectState:
    source_path: Optional[Path]=None; original: Optional[Image.Image]=None; crop: Optional[Image.Image]=None
    candidates: dict[str,np.ndarray]=field(default_factory=dict); selected_method: Optional[str]=None; selected_matrix: Optional[np.ndarray]=None
    quantized_matrix: Optional[np.ndarray]=None; requested_colors:int=20; locked_colors:set=field(default_factory=set); priority_colors:dict=field(default_factory=dict)
    quant_strategy:str='balanced'; checkpoints:dict[str,object]=field(default_factory=dict)
    def save_checkpoint(self,name,value):
        if isinstance(value,np.ndarray): value=value.copy()
        elif isinstance(value,Image.Image): value=value.copy()
        elif isinstance(value,(dict,set,list)): value=value.copy()
        self.checkpoints[name]=value
    def restore(self,name):
        value=self.checkpoints[name]
        if isinstance(value,np.ndarray): return value.copy()
        if isinstance(value,Image.Image): return value.copy()
        if isinstance(value,(dict,set,list)): return value.copy()
        return value
