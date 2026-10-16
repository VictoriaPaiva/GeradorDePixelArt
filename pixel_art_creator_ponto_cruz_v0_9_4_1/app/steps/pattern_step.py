import csv,hashlib,json
from pathlib import Path
import numpy as np
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QSplitter,
    QFileDialog,QMessageBox,QTableWidget,QTableWidgetItem,QHeaderView,QComboBox
)
from .base_step import BaseStep
from ..widgets.pil_preview import PilPreview
from ..simplification_service import decode_png
from ..pattern_utils import (
    build_legend,validate_matrix,render_code_pattern,
    render_symbol_pattern,render_legend
)


class PatternStep(BaseStep):
    def __init__(self,state):
        super().__init__(
            '7. Grade e legenda',
            'Transforme a matriz final em um gráfico de ponto cruz numerado, com códigos por célula e legenda completa.'
        )
        self.state=state
        self.arr=None
        self.entries=[]
        self.color_to_code={}
        self.pattern_color=None
        self.pattern_symbols=None
        self.legend_img=None

        self.layout.setContentsMargins(14,10,14,8)
        self.layout.setSpacing(6)

        bar=QHBoxLayout()
        self.generate_btn=QPushButton('Gerar grade + legenda')
        self.view_mode=QComboBox()
        self.view_mode.addItem('Grade com cores','color')
        self.view_mode.addItem('Grade para impressão (códigos)','symbols')
        self.save_current_btn=QPushButton('Salvar grade atual')
        self.save_both_btn=QPushButton('Salvar as duas grades')
        self.save_legend_btn=QPushButton('Salvar legenda PNG')
        self.export_json_btn=QPushButton('JSON')
        self.export_csv_btn=QPushButton('CSV')
        self.export_txt_btn=QPushButton('TXT')

        bar.addWidget(self.generate_btn)
        bar.addWidget(QLabel('Visualização:'))
        bar.addWidget(self.view_mode)
        bar.addStretch(1)
        bar.addWidget(self.save_current_btn)
        bar.addWidget(self.save_both_btn)
        bar.addWidget(self.save_legend_btn)
        bar.addWidget(QLabel('Legenda:'))
        bar.addWidget(self.export_json_btn)
        bar.addWidget(self.export_csv_btn)
        bar.addWidget(self.export_txt_btn)
        self.layout.addLayout(bar)

        info=QLabel(
            'Cada célula recebe um código único de cor. A grade tem linha fina a cada ponto e linha reforçada a cada 10 pontos; '
            'as coordenadas aparecem a cada 5 pontos. A legenda informa cor, HEX/RGB e quantidade de pontos.'
        )
        info.setWordWrap(True)
        info.setStyleSheet('font-size:11px;color:#59616d;')
        self.layout.addWidget(info)

        split=QSplitter()
        self.layout.addWidget(split,1)

        left=QWidget()
        ll=QVBoxLayout(left)
        title=QLabel('GRADE DE PONTO CRUZ')
        title.setStyleSheet('font-size:17px;font-weight:700;')
        ll.addWidget(title)
        self.preview=PilPreview('Clique em Gerar grade + legenda.')
        ll.addWidget(self.preview,1)
        self.source_status=QLabel('')
        self.source_status.setWordWrap(True)
        ll.addWidget(self.source_status)

        right=QWidget()
        rl=QVBoxLayout(right)
        title=QLabel('LEGENDA')
        title.setStyleSheet('font-size:17px;font-weight:700;')
        rl.addWidget(title)
        self.table=QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(['Código','Cor','HEX','RGB','Pontos','%'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        rl.addWidget(self.table,1)
        self.pattern_status=QLabel('')
        self.pattern_status.setWordWrap(True)
        rl.addWidget(self.pattern_status)

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([920,580])

        self.generate_btn.clicked.connect(self.generate)
        self.view_mode.currentIndexChanged.connect(self._show_current)
        self.save_current_btn.clicked.connect(self.save_current)
        self.save_both_btn.clicked.connect(self.save_both)
        self.save_legend_btn.clicked.connect(self.save_legend)
        self.export_json_btn.clicked.connect(self.export_json)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_txt_btn.clicked.connect(self.export_txt)
        self.refresh()

    def set_context(self,state):
        self.state=state
        self.refresh()

    def _manual_valid(self):
        edited=self.state.metadata.get('edited_matrix_png') or self.state.metadata.get('edited_100x100_png')
        if not edited:
            return False
        simp=self.state.metadata.get('simplified_png') or self.state.metadata.get('simplified_50_png') or ''
        return self.state.metadata.get('manual_source_signature')==hashlib.sha256(simp.encode('ascii')).hexdigest()

    def _source(self):
        if self._manual_valid():
            return (
                self.state.metadata.get('edited_matrix_png') or self.state.metadata.get('edited_100x100_png'),
                'edição manual'
            )
        simp=self.state.metadata.get('simplified_png') or self.state.metadata.get('simplified_50_png')
        if simp:
            return simp,'paleta técnica'
        matrix=self.state.metadata.get('matrix_png') or self.state.metadata.get('matrix_100x100_png')
        if matrix:
            return matrix,'matriz técnica'
        return None,'indisponível'

    def _sig(self):
        raw,_=self._source()
        return hashlib.sha256((raw or '').encode('ascii')).hexdigest() if raw else None

    def _cell_size(self):
        if self.arr is None:
            return 24
        h,w=self.arr.shape[:2]
        # Saved PNG remains readable even for 100x100 without exploding file size.
        return max(18,min(28,int(1900/max(h,w))))

    def refresh(self):
        raw,name=self._source()
        self.arr=decode_png(raw)
        if self.arr is None:
            self.source_status.setText('Sem matriz final disponível.')
        else:
            h,w=self.arr.shape[:2]
            colors=len(np.unique(self.arr.reshape(-1,3),axis=0))
            self.source_status.setText(
                f'Fonte: {name} • grade {w}×{h} • {w*h:,} pontos • {colors} cores.'
            )

        if self.state.metadata.get('pattern_source_signature')==self._sig() and self.arr is not None:
            self._build_outputs()
        else:
            self.pattern_color=None
            self.pattern_symbols=None
            self.legend_img=None
            self.entries=[]
            self.table.setRowCount(0)
            self.preview.clear_preview('Clique em Gerar grade + legenda.')
            self.pattern_status.setText('Grade ainda não gerada para a matriz atual.')

        self._actions()

    def _build_outputs(self):
        self.entries,self.color_to_code=build_legend(self.arr)
        cell=self._cell_size()
        self.pattern_color=render_code_pattern(self.arr,self.color_to_code,cell_size=cell)
        self.pattern_symbols=render_symbol_pattern(self.arr,self.color_to_code,cell_size=cell)
        h,w=self.arr.shape[:2]
        self.legend_img=render_legend(self.entries,w,h)
        self._fill_table()
        self._show_current()
        self.pattern_status.setText(
            f'{w}×{h} • {w*h:,} pontos • {len(self.entries)} cores • '
            'linhas reforçadas a cada 10 pontos.'
        )

    def generate(self):
        ok,msg=validate_matrix(self.arr)
        if not ok:
            QMessageBox.information(self,'Matriz inválida',msg)
            return

        self._build_outputs()
        self.state.metadata['pattern_generated']=True
        self.state.metadata['pattern_source_signature']=self._sig()
        self.state.metadata['pattern_entries']=[
            {
                'code':e.code,
                'rgb':list(e.rgb),
                'hex':e.hex,
                'count':e.count,
                'percent':e.percent,
            }
            for e in self.entries
        ]
        self.state.metadata['pattern_code_style']='C01_sequence'
        self.state.unapprove('pattern')
        self.state.dirty=True
        self._actions()

    def _show_current(self):
        mode=self.view_mode.currentData()
        img=self.pattern_symbols if mode=='symbols' else self.pattern_color
        if img is not None:
            self.preview.set_pil(img)

    def _fill_table(self):
        self.table.setRowCount(len(self.entries))
        for r,e in enumerate(self.entries):
            vals=[e.code,'',e.hex,f'{e.rgb[0]}, {e.rgb[1]}, {e.rgb[2]}',f'{e.count:,}',f'{e.percent:.2f}%']
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v)
                self.table.setItem(r,c,item)
            self.table.item(r,1).setBackground(QColor(*e.rgb))

    def _actions(self):
        ok=self.pattern_color is not None and self.pattern_symbols is not None
        for b in [
            self.save_current_btn,self.save_both_btn,self.save_legend_btn,
            self.export_json_btn,self.export_csv_btn,self.export_txt_btn
        ]:
            b.setEnabled(ok)

    def _default_stem(self):
        if self.arr is None:
            return 'grafico_ponto_cruz'
        h,w=self.arr.shape[:2]
        return f'grafico_ponto_cruz_{w}x{h}'

    def save_current(self):
        mode=self.view_mode.currentData()
        img=self.pattern_symbols if mode=='symbols' else self.pattern_color
        if img is None:
            return
        suffix='codigos' if mode=='symbols' else 'colorido'
        path,_=QFileDialog.getSaveFileName(
            self,'Salvar grade',f'{self._default_stem()}_{suffix}.png','PNG (*.png)'
        )
        if path:
            img.save(path)
            self.state.pattern_image_path=path
            self.state.dirty=True

    def save_both(self):
        if self.pattern_color is None:
            return
        folder=QFileDialog.getExistingDirectory(self,'Escolher pasta para salvar as grades')
        if not folder:
            return
        base=Path(folder)/self._default_stem()
        color_path=Path(str(base)+'_colorido.png')
        code_path=Path(str(base)+'_codigos.png')
        self.pattern_color.save(color_path)
        self.pattern_symbols.save(code_path)
        self.state.pattern_image_path=str(color_path)
        self.state.dirty=True
        QMessageBox.information(
            self,'Grades salvas',
            f'Foram salvas duas versões:\n{color_path.name}\n{code_path.name}'
        )

    def save_legend(self):
        if self.legend_img is None:
            return
        path,_=QFileDialog.getSaveFileName(
            self,'Salvar legenda','legenda_ponto_cruz.png','PNG (*.png)'
        )
        if path:
            self.legend_img.save(path)
            self.state.metadata['legend_image_path']=path
            self.state.dirty=True

    def _rows(self):
        return [
            {
                'code':e.code,
                'hex':e.hex,
                'rgb':list(e.rgb),
                'points':e.count,
                'percent':e.percent,
            }
            for e in self.entries
        ]

    def export_json(self):
        if not self.entries:
            return
        path,_=QFileDialog.getSaveFileName(self,'Exportar JSON','legenda.json','JSON (*.json)')
        if path:
            h,w=self.arr.shape[:2]
            payload={
                'grid':{'width':w,'height':h,'points':w*h},
                'colors':self._rows(),
            }
            Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')

    def export_csv(self):
        if not self.entries:
            return
        path,_=QFileDialog.getSaveFileName(self,'Exportar CSV','legenda.csv','CSV (*.csv)')
        if path:
            with open(path,'w',newline='',encoding='utf-8-sig') as f:
                wr=csv.writer(f)
                wr.writerow(['codigo','hex','r','g','b','pontos','percentual'])
                for e in self.entries:
                    wr.writerow([e.code,e.hex,*e.rgb,e.count,f'{e.percent:.6f}'])

    def export_txt(self):
        if not self.entries:
            return
        path,_=QFileDialog.getSaveFileName(self,'Exportar TXT','legenda.txt','TXT (*.txt)')
        if path:
            h,w=self.arr.shape[:2]
            lines=[
                f'GUIA DE PONTO CRUZ — {w}×{h}',
                f'Total de pontos: {w*h:,}',
                f'Cores: {len(self.entries)}',
                '',
            ]
            lines += [
                f'{e.code} | {e.hex} | RGB{e.rgb} | {e.count:,} pontos | {e.percent:.2f}%'
                for e in self.entries
            ]
            Path(path).write_text('\n'.join(lines),encoding='utf-8')

    def is_ready(self):
        return bool(
            self.pattern_color is not None
            and self.pattern_symbols is not None
            and self.state.metadata.get('pattern_source_signature')==self._sig()
        )
