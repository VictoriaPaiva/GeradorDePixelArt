
import hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QSplitter,
    QScrollArea,QCheckBox,QFileDialog,QMessageBox
)
from .base_step import BaseStep
from ..widgets.manual_editor_canvas import ManualEditorCanvas
from ..widgets.manual_palette_panel import ManualPalettePanel
from ..simplification_service import decode_png, encode_png

class ManualEditorStep(BaseStep):
    def __init__(self,state,workspace):
        super().__init__("6. Edição manual","Ajuste células pontuais usando somente as cores da paleta final.")
        self.state=state; self.workspace=workspace; self.source=None
        self.undo_stack=[]; self.redo_stack=[]; self._recording=True

        t=self.layout.itemAt(0).widget(); d=self.layout.itemAt(1).widget()
        if t: t.setStyleSheet("font-size:20px;font-weight:700;"); t.setMaximumHeight(34)
        if d: d.setStyleSheet("font-size:12px;color:#5b6470;"); d.setMaximumHeight(30)
        self.layout.setContentsMargins(14,10,14,8); self.layout.setSpacing(6)

        bar=QHBoxLayout()
        self.undo_btn=QPushButton("Desfazer"); self.redo_btn=QPushButton("Refazer")
        self.grid_check=QCheckBox("Mostrar grade"); self.grid_check.setChecked(True)
        self.zoom_out_btn=QPushButton("−")
        self.zoom_out_btn.setFixedWidth(36)
        self.zoom_in_btn=QPushButton("+")
        self.zoom_in_btn.setFixedWidth(36)
        self.fit_btn=QPushButton("Ajustar")
        self.reset_btn=QPushButton("Restaurar simplificada")
        self.save_btn=QPushButton("Salvar matriz"); self.preview_btn=QPushButton("Salvar preview"); self.grid_save_btn=QPushButton("Salvar com grade")
        for b,tip in [
            (self.undo_btn,"Desfazer a última alteração"),(self.redo_btn,"Refazer a última alteração"),
            (self.reset_btn,"Descartar edições e voltar à versão simplificada aprovada"),
            (self.zoom_out_btn,"Diminuir zoom"),
            (self.zoom_in_btn,"Aumentar zoom"),
            (self.fit_btn,"Mostrar a matriz inteira"),
            (self.save_btn,"Salvar PNG técnico real 100×100"),(self.preview_btn,"Salvar preview ampliado sem grade"),
            (self.grid_save_btn,"Salvar versão ampliada com grade visual")
        ]: b.setToolTip(tip)
        for w in [self.undo_btn,self.redo_btn,self.grid_check,self.zoom_out_btn,self.zoom_in_btn,self.fit_btn,self.reset_btn]: bar.addWidget(w)
        bar.addStretch(1)
        for w in [self.save_btn,self.preview_btn,self.grid_save_btn]: bar.addWidget(w)
        self.layout.addLayout(bar)

        self.info=QLabel("Clique esquerdo pinta a célula inteira • Arraste pinta várias • Clique direito = conta-gotas • Roda do mouse = zoom • Botão do meio ou Shift+arrastar = mover • Hover na paleta destaca a cor.")
        self.info.setStyleSheet("font-size:11px;color:#59616d;"); self.info.setWordWrap(True); self.layout.addWidget(self.info)

        split=QSplitter(Qt.Horizontal); split.setChildrenCollapsible(False); self.layout.addWidget(split,1)

        left=QWidget(); ll=QVBoxLayout(left); ll.setContentsMargins(0,0,5,0); ll.setSpacing(4)
        lt=QLabel("EDIÇÃO DA MATRIZ 100×100"); lt.setStyleSheet("font-size:17px;font-weight:700;"); ll.addWidget(lt)
        self.canvas=ManualEditorCanvas(); ll.addWidget(self.canvas,1)
        self.status=QLabel(""); self.status.setStyleSheet("font-size:11px;color:#59616d;"); self.status.setMaximumHeight(20); ll.addWidget(self.status)

        right=QWidget(); rl=QVBoxLayout(right); rl.setContentsMargins(5,0,0,0); rl.setSpacing(4)
        rt=QLabel("PALETA PERMITIDA — 50 CORES"); rt.setStyleSheet("font-size:17px;font-weight:700;"); rl.addWidget(rt)
        hint=QLabel("★ = essencial. Essenciais ficam agrupadas pelas áreas de origem; as demais em “Outras cores da paleta final”.")
        hint.setStyleSheet("font-size:11px;color:#59616d;"); hint.setWordWrap(True); rl.addWidget(hint)
        self.palette_panel=ManualPalettePanel()
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(self.palette_panel); rl.addWidget(scroll,1)

        split.addWidget(left); split.addWidget(right); split.setStretchFactor(0,3); split.setStretchFactor(1,2); split.setSizes([900,600])

        self.undo_btn.clicked.connect(self.undo); self.redo_btn.clicked.connect(self.redo)
        self.grid_check.toggled.connect(self.canvas.set_grid)
        self.zoom_out_btn.clicked.connect(self.canvas.zoom_out)
        self.zoom_in_btn.clicked.connect(self.canvas.zoom_in)
        self.fit_btn.clicked.connect(self.canvas.reset_view)
        self.canvas.zoomChanged.connect(lambda _value:self._refresh_status())
        self.reset_btn.clicked.connect(self.reset_to_simplified)
        self.save_btn.clicked.connect(self.save_matrix); self.preview_btn.clicked.connect(self.save_preview); self.grid_save_btn.clicked.connect(self.save_with_grid)
        self.canvas.pixelChanged.connect(self.record_change); self.canvas.colorPicked.connect(self.eyedropper)
        self.palette_panel.colorSelected.connect(self.canvas.set_paint_color)
        self.palette_panel.colorHovered.connect(self.canvas.set_hover_color)
        self.palette_panel.colorHoverLeft.connect(lambda:self.canvas.set_hover_color(None))
        self.refresh()

    def set_context(self,state,workspace):
        self.state=state; self.workspace=workspace; self.refresh()

    def _simplified_png(self): return self.state.metadata.get("simplified_50_png")
    def _source_signature(self):
        return hashlib.sha256((self._simplified_png() or "").encode("ascii")).hexdigest()

    def refresh(self):
        simplified=decode_png(self._simplified_png()); self.source=simplified
        if simplified is None:
            self.canvas.set_array(None); self.palette_panel.set_entries([]); self.status.setText("Sem imagem simplificada disponível."); return
        stored=None
        if self.state.metadata.get("manual_source_signature")==self._source_signature():
            stored=decode_png(self.state.metadata.get("edited_100x100_png"))
        self.canvas.set_array(stored if stored is not None else simplified)
        self.undo_stack.clear(); self.redo_stack.clear()
        entries=self._build_palette_entries(); self.palette_panel.set_entries(entries)
        if self.palette_panel.current is None and entries:self.palette_panel.select_color(entries[0]["rgb"])
        self._refresh_status()

    def _persist(self):
        arr=self.canvas.get_array()
        if arr is None:return
        self.state.metadata["edited_100x100_png"]=encode_png(arr)
        self.state.metadata["manual_source_signature"]=self._source_signature()
        self.state.edited_matrix_path=None
        self.state.unapprove("manual"); self.state.invalidate_after("manual"); self.state.dirty=True

    def _build_palette_entries(self):
        final=[tuple(int(v) for v in rgb) for rgb in self.state.metadata.get("final_palette_50",[])]
        essential={tuple(int(v) for v in rgb) for rgb in self.state.metadata.get("final_essential_colors",[])}
        palette_set=set(final); entries=[]; used=set()
        for area in self.workspace.areas:
            area_rgbs=[tuple(rgb) for rgb in area.get("selected",{}).keys() if tuple(rgb) in palette_set]
            for rgb in [c for c in final if c in area_rgbs]:
                entries.append({"group":area["name"],"rgb":rgb,"label":self._label(rgb,final),"essential":True}); used.add(rgb)
        for rgb in [c for c in final if c not in used]:
            entries.append({"group":"Outras cores da paleta final","rgb":rgb,"label":self._label(rgb,final),"essential":rgb in essential})
        return entries

    def _label(self,rgb,palette):
        idx=palette.index(rgb)+1 if rgb in palette else 0
        hx="#{:02X}{:02X}{:02X}".format(*rgb)
        return f"{idx:02d}  {hx}" if idx else hx

    def record_change(self,x,y,old,new):
        if not self._recording:return
        self.undo_stack.append((x,y,old,new)); self.redo_stack.clear(); self._persist(); self._refresh_status()

    def undo(self):
        if not self.undo_stack or self.canvas.arr is None:return
        x,y,old,new=self.undo_stack.pop(); self._recording=False
        self.canvas.arr[y,x]=np.array(old,dtype=np.uint8); self.canvas.update(); self._recording=True
        self.redo_stack.append((x,y,old,new)); self._persist(); self._refresh_status()

    def redo(self):
        if not self.redo_stack or self.canvas.arr is None:return
        x,y,old,new=self.redo_stack.pop(); self._recording=False
        self.canvas.arr[y,x]=np.array(new,dtype=np.uint8); self.canvas.update(); self._recording=True
        self.undo_stack.append((x,y,old,new)); self._persist(); self._refresh_status()

    def eyedropper(self,rgb):
        if self.palette_panel.select_if_present(rgb): self.info.setText(f"Conta-gotas: RGB {rgb} selecionado.")
        else: self.info.setText(f"RGB {rgb} existe na imagem, mas não consta na paleta final.")

    def reset_to_simplified(self):
        if self.source is None:return
        ans=QMessageBox.question(self,"Restaurar versão simplificada","Descartar todas as edições manuais atuais?",QMessageBox.Yes|QMessageBox.No)
        if ans!=QMessageBox.Yes:return
        self.canvas.set_array(self.source); self.undo_stack.clear(); self.redo_stack.clear()
        self.state.metadata.pop("edited_100x100_png",None); self.state.metadata.pop("manual_source_signature",None)
        self.state.edited_matrix_path=None; self.state.unapprove("manual"); self.state.invalidate_after("manual"); self.state.dirty=True
        self._refresh_status()

    def save_matrix(self):
        arr=self.canvas.get_array()
        if arr is None:return
        path,_=QFileDialog.getSaveFileName(self,"Salvar matriz editada","pixel_art_editada_100x100.png","PNG (*.png)")
        if not path:return
        Image.fromarray(arr,"RGB").save(path); self.state.edited_matrix_path=path; self.state.dirty=True
        QMessageBox.information(self,"Matriz salva",f"Matriz editada salva em:\n{path}\n\nDimensão real: 100×100 pixels.")

    def save_preview(self):
        arr=self.canvas.get_array()
        if arr is None:return
        path,_=QFileDialog.getSaveFileName(self,"Salvar preview","pixel_art_editada_preview.png","PNG (*.png)")
        if not path:return
        Image.fromarray(arr,"RGB").resize((800,800),Image.Resampling.NEAREST).save(path); QMessageBox.information(self,"Preview salvo",path)

    def save_with_grid(self):
        arr=self.canvas.get_array()
        if arr is None:return
        path,_=QFileDialog.getSaveFileName(self,"Salvar imagem com grade","pixel_art_editada_com_grade.png","PNG (*.png)")
        if not path:return
        cell=9; gw=1; size=100*cell+101*gw
        out=np.zeros((size,size,3),dtype=np.uint8); out[:,:,:]=np.array((55,55,55),dtype=np.uint8)
        for y in range(100):
            y0=gw+y*(cell+gw)
            for x in range(100):
                x0=gw+x*(cell+gw); out[y0:y0+cell,x0:x0+cell]=arr[y,x]
        Image.fromarray(out,"RGB").save(path); QMessageBox.information(self,"Imagem com grade salva",path)

    def _refresh_status(self):
        arr=self.canvas.get_array()
        if arr is None:self.status.setText("Sem matriz para editar."); return
        colors=len(np.unique(arr.reshape(-1,3),axis=0))
        self.status.setText(f"100×100 • {colors} cores usadas • zoom {self.canvas.zoom_percent()}% • {len(self.undo_stack)} alterações disponíveis para desfazer")

    def is_ready(self):
        arr=self.canvas.get_array()
        if arr is None:return False
        allowed={tuple(int(v) for v in rgb) for rgb in self.state.metadata.get("final_palette_50",[])}
        used=set(map(tuple,arr.reshape(-1,3).tolist()))
        return arr.shape==(100,100,3) and used.issubset(allowed)
