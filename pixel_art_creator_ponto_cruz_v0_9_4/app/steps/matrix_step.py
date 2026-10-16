from pathlib import Path
import numpy as np
from PIL import Image
from PySide6.QtWidgets import (
    QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QSplitter,
    QFileDialog,QMessageBox,QCheckBox,QComboBox
)
from .base_step import BaseStep
from ..widgets.image_preview import ImagePreview
from ..widgets.matrix_canvas import MatrixCanvas
from ..matrix_service import (
    image_to_matrix, image_to_matrix_preserve, encode_matrix_png,
    decode_matrix_png, enlarged_preview
)


class MatrixStep(BaseStep):
    def __init__(self,state):
        super().__init__(
            '3. Normalização técnica da grade',
            'Converta a matriz artística já criada no ChatGPT para a grade exata, sem redesenhar artisticamente a imagem.'
        )
        self.state=state
        self.matrix=None
        self.layout.setContentsMargins(14,10,14,8); self.layout.setSpacing(7)

        bar=QHBoxLayout()
        self.mode=QComboBox()
        self.mode.addItem('Preservação máxima (recomendado)', 'preserve')
        self.mode.addItem('Conversão automática experimental', 'median')
        self.generate_btn=QPushButton('Normalizar para a grade exata')
        self.grid_check=QCheckBox('Mostrar grade')
        self.save_matrix_btn=QPushButton('Salvar matriz')
        self.save_preview_btn=QPushButton('Salvar preview')
        bar.addWidget(QLabel('Modo:')); bar.addWidget(self.mode); bar.addWidget(self.generate_btn); bar.addWidget(self.grid_check)
        bar.addStretch(1); bar.addWidget(self.save_matrix_btn); bar.addWidget(self.save_preview_btn)
        self.layout.addLayout(bar)

        self.method_info=QLabel('')
        self.method_info.setWordWrap(True); self.method_info.setStyleSheet('font-size:11px;color:#59616d;')
        self.layout.addWidget(self.method_info)

        split=QSplitter(); split.setChildrenCollapsible(False); self.layout.addWidget(split,1)
        left=QWidget(); ll=QVBoxLayout(left); ll.setContentsMargins(0,0,5,0)
        t=QLabel('MATRIZ ARTÍSTICA APROVADA NO CHAT'); t.setStyleSheet('font-size:17px;font-weight:700;')
        ll.addWidget(t); self.source_preview=ImagePreview('Importe a matriz artística na etapa anterior.'); ll.addWidget(self.source_preview,1)
        self.source_info=QLabel(''); self.source_info.setWordWrap(True); ll.addWidget(self.source_info)

        right=QWidget(); rl=QVBoxLayout(right); rl.setContentsMargins(5,0,0,0)
        self.matrix_title=QLabel('GRADE TÉCNICA'); self.matrix_title.setStyleSheet('font-size:17px;font-weight:700;')
        rl.addWidget(self.matrix_title); self.matrix_canvas=MatrixCanvas(); rl.addWidget(self.matrix_canvas,1)
        self.matrix_info=QLabel('Matriz ainda não normalizada.'); rl.addWidget(self.matrix_info)
        split.addWidget(left); split.addWidget(right); split.setSizes([750,750])

        self.generate_btn.clicked.connect(self.generate)
        self.grid_check.toggled.connect(self.matrix_canvas.set_grid)
        self.mode.currentIndexChanged.connect(self.mode_changed)
        self.save_matrix_btn.clicked.connect(self.save_matrix)
        self.save_preview_btn.clicked.connect(self.save_preview)
        self.refresh()

    def set_context(self,state): self.state=state; self.refresh()
    def dims(self): return int(self.state.metadata.get('grid_width',50)),int(self.state.metadata.get('grid_height',50))

    def mode_changed(self):
        self.state.metadata['matrix_normalization_mode']=self.mode.currentData()
        self.state.unapprove('matrix'); self.state.dirty=True
        self.update_method_info()

    def update_method_info(self):
        if self.mode.currentData()=='preserve':
            self.method_info.setText(
                'PRESERVAÇÃO MÁXIMA: a imagem gerada no ChatGPT já contém as decisões artísticas. '
                'O programa apenas normaliza para a quantidade exata de células usando amostragem nearest-neighbor, '
                'sem média, sem mediana local e sem tentar redesenhar olhos, focinho ou expressão.'
            )
        else:
            self.method_info.setText(
                'EXPERIMENTAL: recria cada célula escolhendo um RGB real próximo da mediana da região. '
                'Pode perder pequenos contrastes importantes e não é o fluxo principal recomendado.'
            )

    def refresh(self):
        w,h=self.dims(); path=self.state.metadata.get('chat_matrix_art_path')
        if path and Path(path).exists():
            self.source_preview.set_image(path)
            try:
                im=Image.open(path)
                self.source_info.setText(f'{Path(path).name} • {im.width}×{im.height} • alvo técnico {w}×{h}.')
            except Exception:
                self.source_info.setText(f'Alvo técnico {w}×{h}.')
        else:
            self.source_preview.clear_image('Importe a matriz artística gerada no ChatGPT na etapa anterior.')
            self.source_info.setText('')

        saved=self.state.metadata.get('matrix_normalization_mode','preserve')
        idx=self.mode.findData(saved)
        self.mode.blockSignals(True); self.mode.setCurrentIndex(max(0,idx)); self.mode.blockSignals(False)
        self.update_method_info()

        stored=self.state.metadata.get('matrix_png') or self.state.metadata.get('matrix_100x100_png')
        self.matrix=decode_matrix_png(stored,w,h) if stored else None
        self.matrix_canvas.set_array(self.matrix); self.matrix_title.setText(f'GRADE TÉCNICA {w}×{h}')
        self._info()

    def generate(self):
        if not self.state.approvals.get('matrix_art',False):
            QMessageBox.information(self,'Matriz artística não aprovada','Importe e aprove a matriz artística gerada pelo ChatGPT antes de normalizar.'); return
        path=self.state.metadata.get('chat_matrix_art_path')
        if not path or not Path(path).exists():
            QMessageBox.information(self,'Sem matriz artística','Importe o resultado gerado pelo ChatGPT na etapa anterior.'); return
        try:
            image=Image.open(path).convert('RGB'); w,h=self.dims()
            if self.mode.currentData()=='preserve':
                self.matrix=image_to_matrix_preserve(image,w,h); method='chat_art_nearest_preservation'
            else:
                self.matrix=image_to_matrix(image,w,h); method='experimental_local_median_medoid'
        except Exception as e:
            QMessageBox.critical(self,'Erro ao normalizar matriz',str(e)); return

        encoded=encode_matrix_png(self.matrix)
        self.state.metadata['matrix_png']=encoded; self.state.metadata['matrix_width']=w; self.state.metadata['matrix_height']=h
        self.state.metadata['matrix_method']=method; self.state.metadata['matrix_source_path']=path
        self.state.metadata.pop('matrix_100x100_png',None)
        self.state.matrix_image_path=None; self.state.unapprove('matrix'); self.state.invalidate_after('matrix'); self.state.dirty=True
        self.matrix_canvas.set_array(self.matrix); self._info()

    def _info(self):
        if self.matrix is None:
            self.matrix_info.setText('Grade técnica ainda não gerada.'); self.save_matrix_btn.setEnabled(False); self.save_preview_btn.setEnabled(False); return
        h,w=self.matrix.shape[:2]; unique=len(np.unique(self.matrix.reshape(-1,3),axis=0))
        method=self.state.metadata.get('matrix_method','')
        tag='preservação máxima' if 'preservation' in method else 'experimental'
        self.matrix_info.setText(f'{w}×{h} • {w*h:,} pontos • {unique:,} RGBs • modo {tag}')
        self.save_matrix_btn.setEnabled(True); self.save_preview_btn.setEnabled(True)

    def save_matrix(self):
        if self.matrix is None:return
        h,w=self.matrix.shape[:2]; path,_=QFileDialog.getSaveFileName(self,'Salvar matriz',f'guia_matriz_{w}x{h}.png','PNG (*.png)')
        if path: Image.fromarray(self.matrix,'RGB').save(path); self.state.matrix_image_path=path; self.state.dirty=True

    def save_preview(self):
        if self.matrix is None:return
        h,w=self.matrix.shape[:2]; path,_=QFileDialog.getSaveFileName(self,'Salvar preview',f'guia_matriz_{w}x{h}_preview.png','PNG (*.png)')
        if path: enlarged_preview(self.matrix,900).save(path)

    def is_ready(self):
        if self.matrix is None:return False
        w,h=self.dims(); return self.matrix.shape==(h,w,3)
