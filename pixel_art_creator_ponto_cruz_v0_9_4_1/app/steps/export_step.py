
import hashlib
from pathlib import Path
import numpy as np
from PySide6.QtWidgets import QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QFileDialog,QMessageBox,QCheckBox,QFrame,QGridLayout,QScrollArea,QWidget
from .base_step import BaseStep
from ..simplification_service import decode_png
from ..export_utils import create_export_bundle
EXPORT_ITEMS=[('matrix','Matriz técnica'),('preview','Preview ampliado'),('grid','Imagem com grade'),('pattern_color','Grade colorida com códigos'),('pattern_symbols','Grade para impressão com códigos'),('legend_png','Legenda PNG'),('legend_json','Legenda JSON'),('legend_csv','Legenda CSV'),('legend_txt','Legenda TXT')]
class ExportItem(QFrame):
    def __init__(self,key,label):
        super().__init__(); self.key=key; lay=QHBoxLayout(self); self.check=QCheckBox(label); self.check.setChecked(True); lay.addWidget(self.check,1); self.status=QLabel('Pronto'); lay.addWidget(self.status)
class ExportStep(BaseStep):
    def __init__(self,state):
        super().__init__('8. Exportar','Salve o gráfico e os arquivos técnicos em uma única pasta.'); self.state=state; self.arr=None; self.items={}; self.layout.setContentsMargins(14,10,14,8)
        top=QHBoxLayout(); self.folder_btn=QPushButton('Escolher pasta'); self.export_selected_btn=QPushButton('Exportar selecionados'); self.export_all_btn=QPushButton('Exportar tudo'); top.addWidget(self.folder_btn); top.addWidget(self.export_selected_btn); top.addWidget(self.export_all_btn); top.addStretch(1); self.layout.addLayout(top)
        self.folder_label=QLabel(''); self.source_label=QLabel(''); self.layout.addWidget(self.folder_label); self.layout.addWidget(self.source_label)
        body=QWidget(); grid=QGridLayout(body)
        for i,(k,l) in enumerate(EXPORT_ITEMS):it=ExportItem(k,l); self.items[k]=it; grid.addWidget(it,i//2,i%2)
        sc=QScrollArea(); sc.setWidgetResizable(True); sc.setWidget(body); self.layout.addWidget(sc,1); self.summary=QLabel(''); self.layout.addWidget(self.summary)
        self.folder_btn.clicked.connect(self.choose_folder); self.export_selected_btn.clicked.connect(self.export_selected); self.export_all_btn.clicked.connect(self.export_all); self.refresh()
    def set_context(self,state):self.state=state; self.refresh()
    def _simp(self):return self.state.metadata.get('simplified_png') or self.state.metadata.get('simplified_50_png')
    def _manual_valid(self):
        edit=self.state.metadata.get('edited_matrix_png') or self.state.metadata.get('edited_100x100_png');
        if not edit:return False
        return self.state.metadata.get('manual_source_signature')==hashlib.sha256((self._simp() or '').encode('ascii')).hexdigest()
    def _source(self):return ((self.state.metadata.get('edited_matrix_png') or self.state.metadata.get('edited_100x100_png')),'edição manual') if self._manual_valid() else (self._simp(),'simplificação')
    def _sig(self):raw,_=self._source(); return hashlib.sha256((raw or '').encode('ascii')).hexdigest() if raw else None
    def refresh(self):
        raw,name=self._source(); self.arr=decode_png(raw); folder=self.state.metadata.get('export_directory'); self.folder_label.setText(f'Pasta: {folder}' if folder else 'Pasta de destino ainda não selecionada.')
        if self.arr is None:self.source_label.setText('Sem matriz final.')
        else:
            h,w=self.arr.shape[:2]; self.source_label.setText(f'Fonte: {name} • {w}×{h} • {w*h:,} pontos • {len(np.unique(self.arr.reshape(-1,3),axis=0))} cores')
        man=self.state.metadata.get('export_manifest',[]); self.summary.setText(f'Última exportação: {len(man)} arquivos.' if man and self.state.metadata.get('export_source_signature')==self._sig() else 'Nenhuma exportação válida para a matriz atual.'); ready=self.arr is not None and self.state.approvals.get('pattern',False); self.export_selected_btn.setEnabled(ready); self.export_all_btn.setEnabled(ready)
    def choose_folder(self):
        p=QFileDialog.getExistingDirectory(self,'Escolher pasta',self.state.metadata.get('export_directory',''))
        if p:self.state.metadata['export_directory']=p; self.state.dirty=True; self.refresh()
    def export_selected(self):
        keys={k for k,i in self.items.items() if i.check.isChecked()}
        if not keys:QMessageBox.information(self,'Nada selecionado','Selecione ao menos um arquivo.'); return
        self._export(keys)
    def export_all(self):
        for i in self.items.values():i.check.setChecked(True)
        self._export({k for k,_ in EXPORT_ITEMS})
    def _export(self,keys):
        if self.arr is None:return
        if not self.state.approvals.get('pattern',False):QMessageBox.information(self,'Gráfico pendente','Aprove a etapa Gráfico e legenda antes de exportar.'); return
        folder=self.state.metadata.get('export_directory')
        if not folder:self.choose_folder(); folder=self.state.metadata.get('export_directory')
        if not folder:return
        try:
            name=Path(self.state.project_file).stem if self.state.project_file else self.state.project_name; man=create_export_bundle(self.arr,Path(folder),name,keys)
        except Exception as e:QMessageBox.critical(self,'Erro na exportação',str(e)); return
        self.state.metadata['export_manifest']=man; self.state.metadata['export_source_signature']=self._sig(); self.state.unapprove('export'); self.state.dirty=True; self.summary.setText(f'Exportação concluída: {len(man)} arquivos registrados.'); QMessageBox.information(self,'Exportação concluída',folder)
    def is_ready(self):return bool(self.state.metadata.get('export_manifest') and self.state.metadata.get('export_source_signature')==self._sig())
