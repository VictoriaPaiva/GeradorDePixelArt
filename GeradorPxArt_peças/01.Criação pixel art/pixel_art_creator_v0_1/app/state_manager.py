from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image

@dataclass
class ProjectState:
    source_path: Optional[Path]=None
    original: Optional[Image.Image]=None
    crop: Optional[Image.Image]=None
    candidates: dict[str,np.ndarray]=field(default_factory=dict)
    selected_method: Optional[str]=None
    selected_matrix: Optional[np.ndarray]=None
    checkpoints: dict[str,object]=field(default_factory=dict)

    def save_checkpoint(self,name:str,value:object):
        if isinstance(value,np.ndarray): value=value.copy()
        elif isinstance(value,Image.Image): value=value.copy()
        self.checkpoints[name]=value

    def restore(self,name:str):
        value=self.checkpoints[name]
        if isinstance(value,np.ndarray): return value.copy()
        if isinstance(value,Image.Image): return value.copy()
        return value
