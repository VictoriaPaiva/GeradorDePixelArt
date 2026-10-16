
import hashlib
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QSplitter,QScrollArea,QCheckBox,QFileDialog,QMessageBox
from .base_step import BaseStep
from ..widgets.manual_editor_canvas import ManualEditorCanvas
from ..widgets.manual_palette_panel import ManualPalettePanel
from ..simplification_service import decode_png,encode_png
from ..matrix_service import enlarged_preview

class ManualEditorStep(BaseStep):
    def __init__(self,state,workspace):
        super().__init__('6. Edição manual','Corrija pontos individuais usando somente as cores finais da paleta.')
        self.state=state; self.workspace=workspace; self.source=None; self.undo_stack=[]; self.redo_stack=[]; self._recording=True
        self.layout.setContentsMargins(14,10,14,8); self.layout.setSpacing(6)
        bar=QHBoxLayout(); self.undo_btn=QPushButton('Desfazer'); self.redo_btn=QPushButton('Refazer'); self.grid_check=QCheckBox('Mostrar grade'); self.grid_check.setChecked(True); self.zoom_out=QPushButton('−'); self.zoom_in=QPushButton('+'); self.fit=QPushButton('Ajustar'); self.reset_btn=QPushButton('Restaurar simplificada'); self.save_btn=QPushButton('Salvar matriz'); self.preview_btn=QPushButton('Salvar preview')
        for w in [self.undo_btn,self.redo_btn,self.grid_check,self.zoom_out,self.zoom_in,self.fit,self.reset_btn]:bar.addWidget(w)
        bar.addStretch(1); bar.addWidget(self.save_btn); bar.addWidget(self.preview_btn); self.layout.addLayout(bar)
        info=QLabel('Clique pinta um ponto inteiro • arraste pinta vários • botão direito = conta-gotas • roda = zoom • Shift+arrastar = mover.'); info.setStyleSheet('font-size:11px;color:#59616d;'); self.layout.addWidget(info)
        split=QSplitter(Qt.Horizontal); self.layout.addWidget(split,1)
        left=QWidget(); ll=QVBoxLayout(left); self.title=QLabel('EDIÇÃO'); self.title.setStyleSheet('font-size:17px;font-weight:700;'); ll.addWidget(self.title); self.canvas=ManualEditorCanvas(); ll.addWidget(self.canvas,1); self.status=QLabel(''); ll.addWidget(self.status)
        right=QWidget(); rl=QVBoxLayout(right); t=QLabel('PALETA PERMITIDA'); t.setStyleSheet('font-size:17px;font-weight:700;'); rl.addWidget(t); self.palette_panel=ManualPalettePanel(); sc=QScrollArea(); sc.setWidgetResizable(True); sc.setWidget(self.palette_panel); rl.addWidget(sc,1); split.addWidget(left); split.addWidget(right); split.setSizes([900,600])
        self.undo_btn.clicked.connect(self.undo); self.redo_btn.clicked.connect(self.redo); self.grid_check.toggled.connect(self.canvas.set_grid); self.zoom_out.clicked.connect(self.canvas.zoom_out); self.zoom_in.clicked.connect(self.canvas.zoom_in); self.fit.clicked.connect(self.canvas.reset_view); self.reset_btn.clicked.connect(self.reset_to_simplified); self.save_btn.clicked.connect(self.save_matrix); self.preview_btn.clicked.connect(self.save_preview); self.canvas.pixelChanged.connect(self.record_change); self.canvas.colorPicked.connect(self.eyedropper); self.palette_panel.colorSelected.connect(self.canvas.set_paint_color); self.palette_panel.colorHovered.connect(self.canvas.set_hover_color); self.palette_panel.colorHoverLeft.connect(lambda:self.canvas.set_hover_color(None)); self.canvas.zoomChanged.connect(lambda _:self._status())
        self.refresh()
    def set_context(self,state,workspace):self.state=state; self.workspace=workspace; self.refresh()
    def _simp_payload(self):return self.state.metadata.get('simplified_png') or self.state.metadata.get('simplified_50_png')
    def _sig(self):return hashlib.sha256((self._simp_payload() or '').encode('ascii')).hexdigest()
    def refresh(self):
        simp=decode_png(self._simp_payload()); self.source=simp
        if simp is None:self.canvas.set_array(None); self.palette_panel.set_entries([]); self.status.setText('Sem simplificação disponível.'); return
        stored=None
        if self.state.metadata.get('manual_source_signature')==self._sig():stored=decode_png(self.state.metadata.get('edited_matrix_png') or self.state.metadata.get('edited_100x100_png'))
        self.canvas.set_array(stored if stored is not None else simp); self.undo_stack.clear(); self.redo_stack.clear(); entries=self._entries(); self.palette_panel.set_entries(entries)
        if entries and self.palette_panel.current is None:self.palette_panel.select_color(entries[0]['rgb'])
        h,w=simp.shape[:2]; self.title.setText(f'EDIÇÃO {w}×{h}'); self._status()
    def _entries(self):
        final=[tuple(c) for c in self.state.metadata.get('final_palette_50',[])]; ess={tuple(c) for c in self.state.metadata.get('final_essential_colors',[])}
        return [{'group':'Cores finais','rgb':rgb,'label':f'{i+1:02d}  #{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}','essential':rgb in ess} for i,rgb in enumerate(final)]
    def _persist(self):
        arr=self.canvas.get_array();
        if arr is None:return
        self.state.metadata['edited_matrix_png']=encode_png(arr); self.state.metadata['manual_source_signature']=self._sig(); self.state.metadata.pop('edited_100x100_png',None); self.state.edited_matrix_path=None; self.state.unapprove('manual'); self.state.invalidate_after('manual'); self.state.dirty=True
    def record_change(self,x,y,old,new):
        if not self._recording:return
        self.undo_stack.append((x,y,old,new)); self.redo_stack.clear(); self._persist(); self._status()
    def undo(self):
        if not self.undo_stack or self.canvas.arr is None:return
        x,y,old,new=self.undo_stack.pop(); self.canvas.arr[y,x]=np.array(old,dtype=np.uint8); self.canvas.update(); self.redo_stack.append((x,y,old,new)); self._persist(); self._status()
    def redo(self):
        if not self.redo_stack or self.canvas.arr is None:return
        x,y,old,new=self.redo_stack.pop(); self.canvas.arr[y,x]=np.array(new,dtype=np.uint8); self.canvas.update(); self.undo_stack.append((x,y,old,new)); self._persist(); self._status()
    def eyedropper(self,rgb): self.palette_panel.select_if_present(rgb)
    def reset_to_simplified(self):
        if self.source is None:return
        self.canvas.set_array(self.source); self.state.metadata.pop('edited_matrix_png',None); self.state.metadata.pop('edited_100x100_png',None); self.state.metadata.pop('manual_source_signature',None); self.state.unapprove('manual'); self.state.invalidate_after('manual'); self.state.dirty=True; self._status()
    def save_matrix(self):
        arr=self.canvas.get_array();
        if arr is None:return
        h,w=arr.shape[:2]; path,_=QFileDialog.getSaveFileName(self,'Salvar matriz editada',f'guia_editado_{w}x{h}.png','PNG (*.png)')
        if path:Image.fromarray(arr,'RGB').save(path); self.state.edited_matrix_path=path; self.state.dirty=True
    def save_preview(self):
        arr=self.canvas.get_array();
        if arr is None:return
        h,w=arr.shape[:2]; path,_=QFileDialog.getSaveFileName(self,'Salvar preview',f'guia_editado_{w}x{h}_preview.png','PNG (*.png)')
        if path:enlarged_preview(arr,900).save(path)
    def _status(self):
        arr=self.canvas.get_array();
        if arr is None:return
        h,w=arr.shape[:2]; n=len(np.unique(arr.reshape(-1,3),axis=0)); self.status.setText(f'{w}×{h} • {w*h:,} pontos • {n} cores • zoom {self.canvas.zoom_percent()}%')
    def is_ready(self):
        arr=self.canvas.get_array();
        if arr is None:return False
        allowed={tuple(c) for c in self.state.metadata.get('final_palette_50',[])}; used=set(map(tuple,arr.reshape(-1,3).tolist())); return used.issubset(allowed)
