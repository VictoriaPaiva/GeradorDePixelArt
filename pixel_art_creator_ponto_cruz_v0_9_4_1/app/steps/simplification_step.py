
import hashlib
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QSplitter,QFileDialog,QMessageBox,QCheckBox,QSpinBox
from .base_step import BaseStep
from ..widgets.matrix_canvas import MatrixCanvas
from ..widgets.final_palette_panel import FinalPalettePanel
from ..matrix_service import decode_matrix_png,enlarged_preview
from ..simplification_service import simplify_to_50,rebuild_palette_without_colors,encode_png,decode_png,unique_essential_colors

class SimplificationStep(BaseStep):
    def __init__(self,state,workspace):
        super().__init__('5. Paleta técnica','Analise a paleta da matriz gerada pelo Chat. Se ela já estiver dentro do limite, preserve-a; use a simplificação local apenas como opção experimental.')
        self.state=state; self.workspace=workspace; self.source_matrix=None; self.simplified=None; self.palette=[]; self.essential=[]
        self.layout.setContentsMargins(14,10,14,8); self.layout.setSpacing(6)
        bar=QHBoxLayout(); bar.addWidget(QLabel('Limite de cores:')); self.target=QSpinBox(); self.target.setRange(2,50); self.target.setValue(int(state.metadata.get('palette_target',50))); bar.addWidget(self.target)
        self.keep_btn=QPushButton('Usar paleta atual'); self.generate_btn=QPushButton('Simplificação local experimental'); self.rebuild_btn=QPushButton('Aplicar remoção'); self.clear_selection_btn=QPushButton('Limpar seleção'); self.grid_check=QCheckBox('Mostrar grade'); self.save_btn=QPushButton('Salvar matriz'); self.preview_btn=QPushButton('Salvar preview')
        for w in [self.keep_btn,self.generate_btn,self.rebuild_btn,self.clear_selection_btn,self.grid_check]:bar.addWidget(w)
        bar.addStretch(1); bar.addWidget(self.save_btn); bar.addWidget(self.preview_btn); self.layout.addLayout(bar)
        info=QLabel('Fluxo recomendado: se a matriz criada via Chat já estiver dentro do limite, use a paleta atual sem remapear as cores. A simplificação local fica disponível apenas como alternativa experimental. Remover uma cor não cria outra no lugar.'); info.setWordWrap(True); info.setStyleSheet('font-size:11px;color:#59616d;'); self.layout.addWidget(info)
        split=QSplitter(Qt.Horizontal); self.layout.addWidget(split,1)
        left=QWidget(); ll=QVBoxLayout(left); lt=QLabel('MATRIZ DE PONTOS'); lt.setStyleSheet('font-size:17px;font-weight:700;'); ll.addWidget(lt); self.source_canvas=MatrixCanvas(); ll.addWidget(self.source_canvas,1); self.source_info=QLabel(''); ll.addWidget(self.source_info)
        right=QWidget(); rl=QVBoxLayout(right); rt=QLabel('SIMPLIFICADA'); rt.setStyleSheet('font-size:17px;font-weight:700;'); rl.addWidget(rt); self.final_canvas=MatrixCanvas(); rl.addWidget(self.final_canvas,1); self.final_info=QLabel(''); rl.addWidget(self.final_info)
        split.addWidget(left); split.addWidget(right); split.setSizes([750,750])
        self.palette_panel=FinalPalettePanel(); self.layout.addWidget(self.palette_panel)
        self.keep_btn.clicked.connect(self.keep_current_palette); self.generate_btn.clicked.connect(self.generate); self.rebuild_btn.clicked.connect(self.rebuild_palette); self.clear_selection_btn.clicked.connect(self.palette_panel.clear_selection); self.palette_panel.selectionChanged.connect(self._refresh_actions); self.grid_check.toggled.connect(self.source_canvas.set_grid); self.grid_check.toggled.connect(self.final_canvas.set_grid); self.save_btn.clicked.connect(self.save_matrix); self.preview_btn.clicked.connect(self.save_preview); self.target.valueChanged.connect(self._target_changed)
        self.refresh()
    def set_context(self,state,workspace): self.state=state; self.workspace=workspace; self.refresh()
    def dims(self): return int(self.state.metadata.get('grid_width',50)),int(self.state.metadata.get('grid_height',50))
    def _target_changed(self,v): self.state.metadata['palette_target']=int(v); self.state.palette_target=int(v); self.state.unapprove('simplification'); self.state.dirty=True
    def _matrix_payload(self): return self.state.metadata.get('matrix_png') or self.state.metadata.get('matrix_100x100_png')
    def _input_signature(self):
        raw=self._matrix_payload() or ''; ess=tuple(sorted(unique_essential_colors(self.workspace)))
        return {'version':3,'matrix_sha256':hashlib.sha256(raw.encode('ascii')).hexdigest(),'essential_rgbs':[list(x) for x in ess],'target':self.target.value()}
    def refresh(self):
        w,h=self.dims(); self.target.blockSignals(True); self.target.setValue(int(self.state.metadata.get('palette_target',self.state.palette_target or 50))); self.target.blockSignals(False)
        self.source_matrix=decode_matrix_png(self._matrix_payload(),w,h); self.source_canvas.set_array(self.source_matrix)
        if self.source_matrix is None:self.source_info.setText('Sem matriz bordável disponível.')
        else:self.source_info.setText(f'{w}×{h} • {w*h:,} pontos • {len(np.unique(self.source_matrix.reshape(-1,3),axis=0)):,} RGBs')
        if self.state.metadata.get('simplification_input_signature')==self._input_signature():
            self.simplified=decode_png(self.state.metadata.get('simplified_png') or self.state.metadata.get('simplified_50_png'),w,h); self.palette=[tuple(c) for c in self.state.metadata.get('final_palette_50',[])]; self.essential=[tuple(c) for c in self.state.metadata.get('final_essential_colors',[])]
        else:self.simplified=None; self.palette=[]; self.essential=[]
        self.final_canvas.set_array(self.simplified); self.palette_panel.set_palette(self.palette,self.essential); self._refresh_info(); self._refresh_actions()
    def _store(self,simplified,palette,essential,method,removed=None):
        self.simplified=simplified; self.palette=list(palette); self.essential=list(essential); enc=encode_png(simplified)
        self.state.metadata['simplified_png']=enc; self.state.metadata['final_palette_50']=[list(c) for c in palette]; self.state.metadata['final_essential_colors']=[list(c) for c in essential]; self.state.metadata['simplification_input_signature']=self._input_signature(); self.state.metadata['simplification_method']=method; self.state.metadata['simplification_removed_colors']=[list(c) for c in (removed or [])]; self.state.metadata.pop('simplified_50_png',None)
        self.state.simplified_image_path=None; self.state.unapprove('simplification'); self.state.invalidate_after('simplification'); self.state.dirty=True; self.final_canvas.set_array(simplified); self.palette_panel.set_palette(self.palette,self.essential); self._refresh_info(); self._refresh_actions()
    def keep_current_palette(self):
        if self.source_matrix is None or not self.state.approvals.get('matrix',False):
            QMessageBox.information(self,'Matriz pendente','Gere e aprove a grade técnica antes de analisar a paleta.'); return
        unique, counts = np.unique(self.source_matrix.reshape(-1,3), axis=0, return_counts=True)
        target=self.target.value()
        if len(unique)>target:
            QMessageBox.warning(
                self,'Paleta acima do limite',
                f'A matriz possui {len(unique)} cores únicas, acima do limite de {target}.\n\n'
                'Recomendação: volte à etapa 2 e peça ao ChatGPT uma nova matriz artística com paleta mais enxuta. '
                'Se preferir, use a simplificação local experimental nesta tela.'
            ); return
        order=np.argsort(-counts)
        palette=[tuple(int(v) for v in unique[i]) for i in order]
        essentials=unique_essential_colors(self.workspace)
        essential_set=set(essentials)
        used=set(palette)
        missing=essential_set-used
        if missing:
            QMessageBox.warning(self,'Essenciais ausentes','Algumas cores marcadas como essenciais não aparecem na matriz atual. Revise as essenciais antes de continuar.'); return
        self._store(self.source_matrix.copy(),palette,essentials,'chat_palette_preserved_no_remap')

    def generate(self):
        if self.source_matrix is None or not self.state.approvals.get('matrix',False): QMessageBox.information(self,'Matriz pendente','Gere e aprove a grade técnica antes de simplificar.'); return
        ess=unique_essential_colors(self.workspace); target=self.target.value()
        if len(ess)>target: QMessageBox.warning(self,'Essenciais acima do limite',f'Existem {len(ess)} cores essenciais para um limite de {target}. Remova essenciais ou aumente o limite.'); return
        try:simp,pal,ess=simplify_to_50(self.source_matrix,self.workspace,target=target)
        except Exception as e: QMessageBox.critical(self,'Erro na simplificação',str(e)); return
        self._store(simp,pal,ess,'experimental_local_lab_simplification')
    def rebuild_palette(self):
        rem=self.palette_panel.selected_colors()
        if not rem:return
        try:simp,pal,ess=rebuild_palette_without_colors(self.source_matrix,self.workspace,self.palette,rem,target=self.target.value())
        except Exception as e: QMessageBox.critical(self,'Erro ao remover cores',str(e)); return
        self._store(simp,pal,ess,'manual_palette_reduction_without_refill',rem)
    def _refresh_info(self):
        if self.simplified is None:self.final_info.setText('Simplificação ainda não gerada.'); return
        h,w=self.simplified.shape[:2]; n=len(np.unique(self.simplified.reshape(-1,3),axis=0)); self.final_info.setText(f'{w}×{h} • {w*h:,} pontos • {n} cores usadas')
    def _refresh_actions(self):
        ok=self.simplified is not None; sel=self.palette_panel.selected_count(); self.keep_btn.setEnabled(self.source_matrix is not None); self.rebuild_btn.setEnabled(ok and sel>0); self.clear_selection_btn.setEnabled(sel>0); self.save_btn.setEnabled(ok); self.preview_btn.setEnabled(ok)
    def save_matrix(self):
        if self.simplified is None:return
        h,w=self.simplified.shape[:2]; path,_=QFileDialog.getSaveFileName(self,'Salvar matriz simplificada',f'guia_{w}x{h}_simplificado.png','PNG (*.png)')
        if path: Image.fromarray(self.simplified,'RGB').save(path); self.state.simplified_image_path=path; self.state.dirty=True
    def save_preview(self):
        if self.simplified is None:return
        h,w=self.simplified.shape[:2]; path,_=QFileDialog.getSaveFileName(self,'Salvar preview',f'guia_{w}x{h}_preview.png','PNG (*.png)')
        if path: enlarged_preview(self.simplified,900).save(path)
    def is_ready(self):
        if self.simplified is None:return False
        used=set(map(tuple,self.simplified.reshape(-1,3).tolist())); ess=set(unique_essential_colors(self.workspace)); return 1<=len(used)<=self.target.value() and ess.issubset(used)
