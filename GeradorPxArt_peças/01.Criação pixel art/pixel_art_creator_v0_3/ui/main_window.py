from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QFileDialog,QMessageBox,QStackedWidget,QGroupBox,QSlider,QRadioButton,QButtonGroup,QSpinBox,QComboBox,QListWidget,QListWidgetItem)
from app.state_manager import ProjectState
from image_processing.core import center_square,crop_square,method_fidelity,method_illustrated,method_pixel_art,array_to_preview
from image_processing.color_quantization import quantize_lab,color_info

METHODS={
 'Fidelidade': method_fidelity,
 'Ilustrada': method_illustrated,
 'Pixel Art artística': method_pixel_art,
}

def pixmap(img:Image.Image,max_size=520):
    p=QPixmap.fromImage(ImageQt(img.convert('RGB')))
    return p.scaled(max_size,max_size,Qt.KeepAspectRatio,Qt.FastTransformation)

class PixelLabel(QLabel):
    cellClicked=Signal(int,int)
    cellDragged=Signal(int,int)
    def _cell(self,event):
        if self.pixmap() is None:return None
        pm=self.pixmap(); x0=(self.width()-pm.width())/2; y0=(self.height()-pm.height())/2
        x=event.position().x()-x0; y=event.position().y()-y0
        if 0<=x<pm.width() and 0<=y<pm.height(): return min(49,int(x/pm.width()*50)),min(49,int(y/pm.height()*50))
    def mousePressEvent(self,event):
        c=self._cell(event)
        if c:self.cellClicked.emit(*c)
        super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if event.buttons() & Qt.LeftButton:
            c=self._cell(event)
            if c:self.cellDragged.emit(*c)
        super().mouseMoveEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.state=ProjectState(); self.setWindowTitle('Pixel Art Creator — v0.3'); self.resize(1250,820)
        self.stack=QStackedWidget(); self.setCentralWidget(self.stack)
        self.build_start(); self.build_crop(); self.build_compare(); self.build_approved(); self.build_regions(); self.build_quantize()

    def build_start(self):
        w=QWidget(); l=QVBoxLayout(w); l.setAlignment(Qt.AlignCenter)
        title=QLabel('PIXEL ART CREATOR'); title.setStyleSheet('font-size:30px;font-weight:700'); title.setAlignment(Qt.AlignCenter)
        sub=QLabel('Versão 0.3 — interpretação artística + regiões + textura controlada'); sub.setAlignment(Qt.AlignCenter)
        b=QPushButton('Selecionar imagem'); b.setMinimumHeight(48); b.clicked.connect(self.open_image)
        l.addWidget(title); l.addWidget(sub); l.addSpacing(24); l.addWidget(b); self.stack.addWidget(w)

    def build_crop(self):
        w=QWidget(); l=QVBoxLayout(w); self.crop_info=QLabel(); self.crop_info.setAlignment(Qt.AlignCenter)
        self.crop_view=QLabel(); self.crop_view.setAlignment(Qt.AlignCenter); self.crop_view.setMinimumSize(500,500)
        controls=QHBoxLayout();
        self.xs=QSlider(Qt.Horizontal); self.ys=QSlider(Qt.Horizontal); self.ss=QSlider(Qt.Horizontal)
        for s in (self.xs,self.ys): s.setRange(0,100); s.setValue(50); s.valueChanged.connect(self.refresh_crop)
        self.ss.setRange(20,100); self.ss.setValue(100); self.ss.valueChanged.connect(self.refresh_crop)
        for name,s in [('Horizontal',self.xs),('Vertical',self.ys),('Zoom/área',self.ss)]:
            box=QGroupBox(name); bl=QVBoxLayout(box); bl.addWidget(s); controls.addWidget(box)
        buttons=QHBoxLayout(); c=QPushButton('Centralizar'); c.clicked.connect(self.center_crop); a=QPushButton('APROVAR ENQUADRAMENTO'); a.clicked.connect(self.approve_crop); stop=QPushButton('Encerrar'); stop.clicked.connect(self.close)
        buttons.addWidget(c); buttons.addWidget(a); buttons.addWidget(stop)
        l.addWidget(QLabel('<h2>Enquadramento 1:1</h2>')); l.addWidget(self.crop_info); l.addWidget(self.crop_view,1); l.addLayout(controls); l.addLayout(buttons); self.stack.addWidget(w)

    def build_compare(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel('<h2>Escolha o método 50 × 50</h2>'))
        row=QHBoxLayout(); self.method_group=QButtonGroup(self); self.method_widgets={}
        for i,name in enumerate(METHODS):
            box=QGroupBox(name); bl=QVBoxLayout(box); img=QLabel(); img.setAlignment(Qt.AlignCenter); radio=QRadioButton('Selecionar esta versão'); self.method_group.addButton(radio,i); bl.addWidget(img); bl.addWidget(radio); row.addWidget(box); self.method_widgets[name]=(img,radio)
        l.addLayout(row,1)
        btn=QHBoxLayout(); regen=QPushButton('Gerar novamente'); regen.clicked.connect(self.generate_candidates); back=QPushButton('Voltar ao enquadramento'); back.clicked.connect(lambda:self.stack.setCurrentIndex(1)); approve=QPushButton('APROVAR VERSÃO'); approve.clicked.connect(self.approve_method); stop=QPushButton('Encerrar'); stop.clicked.connect(self.close)
        for x in (regen,back,approve,stop): btn.addWidget(x)
        l.addLayout(btn); self.stack.addWidget(w)

    def build_approved(self):
        w=QWidget(); l=QVBoxLayout(w); self.final_title=QLabel('<h2>Checkpoint aprovado</h2>'); self.final_view=QLabel(); self.final_view.setAlignment(Qt.AlignCenter); self.final_text=QLabel(); self.final_text.setAlignment(Qt.AlignCenter); back=QPushButton('Voltar e escolher outra versão'); back.clicked.connect(lambda:self.stack.setCurrentIndex(2)); nextb=QPushButton('DEFINIR REGIÕES (OPCIONAL)'); nextb.setMinimumHeight(44); nextb.clicked.connect(self.open_regions)
        l.addWidget(self.final_title); l.addWidget(self.final_view,1); l.addWidget(self.final_text); l.addWidget(nextb); l.addWidget(back); self.stack.addWidget(w)

    def open_image(self):
        fn,_=QFileDialog.getOpenFileName(self,'Selecionar imagem','','Imagens (*.png *.jpg *.jpeg *.webp)')
        if not fn:return
        try: img=Image.open(fn).convert('RGB')
        except Exception as e: QMessageBox.critical(self,'Erro',str(e)); return
        self.state=ProjectState(source_path=Path(fn),original=img); self.state.save_checkpoint('original',img)
        self.xs.setValue(50); self.ys.setValue(50); self.ss.setValue(100); self.refresh_crop(); self.stack.setCurrentIndex(1)

    def refresh_crop(self):
        if self.state.original is None:return
        scale=self.ss.value()/100; self.state.crop=crop_square(self.state.original,self.xs.value()/100,self.ys.value()/100,scale)
        self.crop_view.setPixmap(pixmap(self.state.crop)); w,h=self.state.original.size; self.crop_info.setText(f'Original: {w} × {h} px  |  Recorte atual: {self.state.crop.width} × {self.state.crop.height} px')

    def center_crop(self): self.xs.setValue(50); self.ys.setValue(50); self.ss.setValue(100); self.refresh_crop()
    def approve_crop(self): self.state.save_checkpoint('crop',self.state.crop); self.generate_candidates(); self.stack.setCurrentIndex(2)

    def generate_candidates(self):
        crop=self.state.restore('crop') if 'crop' in self.state.checkpoints else self.state.crop
        self.state.candidates={n:f(crop) for n,f in METHODS.items()}
        for n,arr in self.state.candidates.items(): self.method_widgets[n][0].setPixmap(pixmap(array_to_preview(arr,8),400))
        self.method_widgets['Pixel Art artística'][1].setChecked(True)

    def approve_method(self):
        checked=self.method_group.checkedButton()
        if checked is None: QMessageBox.warning(self,'Escolha','Selecione uma versão.'); return
        name=next(n for n,(_,r) in self.method_widgets.items() if r is checked); arr=self.state.candidates[name]
        reply=QMessageBox.question(self,'Confirmar',f'Você aprova a versão “{name}” como base para as próximas etapas?',QMessageBox.Yes|QMessageBox.No)
        if reply!=QMessageBox.Yes:return
        self.state.selected_method=name; self.state.selected_matrix=arr.copy(); self.state.save_checkpoint('pixel_art',arr)
        self.final_view.setPixmap(pixmap(array_to_preview(arr,10),560)); self.final_text.setText(f'Método aprovado: {name}\nMatriz lógica: 50 × 50 = 2.500 células\nPróxima etapa: regiões opcionais de preservação/simplificação e textura.')
        self.stack.setCurrentIndex(3)

    def build_regions(self):
        w=QWidget(); root=QVBoxLayout(w); root.addWidget(QLabel('<h2>Regiões de tratamento — opcional</h2>'))
        info=QLabel('Pinte diretamente sobre a grade 50×50. As marcações NÃO alteram a imagem; apenas orientam a simplificação.\nPreservar = mais peso aos detalhes. Simplificar = fundir variações. Simplificar muito = massas maiores de cor.')
        info.setWordWrap(True); root.addWidget(info)
        body=QHBoxLayout(); self.region_view=PixelLabel(); self.region_view.setAlignment(Qt.AlignCenter); self.region_view.setMinimumSize(650,650); self.region_view.cellClicked.connect(self.paint_region); self.region_view.cellDragged.connect(self.paint_region); body.addWidget(self.region_view,1)
        side=QVBoxLayout(); self.region_mode=QComboBox(); self.region_mode.addItem('Normal / apagar marcação',0); self.region_mode.addItem('🔒 Preservar detalhes',1); self.region_mode.addItem('Simplificar',2); self.region_mode.addItem('Simplificar MUITO',3)
        self.texture_mode=QComboBox(); self.texture_mode.addItem('Sem textura',0); self.texture_mode.addItem('Textura com 2 tons',2); self.texture_mode.addItem('Textura com 3 tons',3)
        self.brush=QSpinBox(); self.brush.setRange(1,9); self.brush.setValue(3)
        side.addWidget(QLabel('Tratamento da região:')); side.addWidget(self.region_mode); side.addWidget(QLabel('Textura da região:')); side.addWidget(self.texture_mode); side.addWidget(QLabel('Tamanho do pincel (células):')); side.addWidget(self.brush)
        clear=QPushButton('Limpar todas as regiões'); clear.clicked.connect(self.clear_regions); side.addWidget(clear); side.addStretch(); body.addLayout(side); root.addLayout(body,1)
        self.region_info=QLabel(); self.region_info.setAlignment(Qt.AlignCenter); root.addWidget(self.region_info)
        buttons=QHBoxLayout(); approve=QPushButton('APROVAR REGIÕES E CONTINUAR'); approve.clicked.connect(self.approve_regions); skip=QPushButton('NÃO USAR REGIÕES'); skip.clicked.connect(self.skip_regions); back=QPushButton('Voltar'); back.clicked.connect(lambda:self.stack.setCurrentIndex(3))
        for b in (approve,skip,back): buttons.addWidget(b)
        root.addLayout(buttons); self.stack.addWidget(w)

    def open_regions(self):
        self.refresh_region_preview(); self.stack.setCurrentIndex(4)

    def paint_region(self,col,row):
        r=self.brush.value()//2; y0=max(0,row-r); y1=min(50,row+r+1); x0=max(0,col-r); x1=min(50,col+r+1)
        mode=self.region_mode.currentData(); tex=self.texture_mode.currentData()
        self.state.region_mask[y0:y1,x0:x1]=mode
        self.state.region_texture[y0:y1,x0:x1]=tex if mode in (2,3) else 0
        self.refresh_region_preview()

    def refresh_region_preview(self):
        if self.state.selected_matrix is None:return
        arr=self.state.selected_matrix.copy().astype(float); mask=self.state.region_mask
        # Overlay: preserve=blue-ish, simplify=yellow-ish, strong=red-ish. Only UI preview.
        overlays={1:np.array([70,140,255]),2:np.array([255,205,60]),3:np.array([255,80,80])}
        for level,c in overlays.items():
            m=mask==level; arr[m]=arr[m]*.58+c*.42
        self.region_view.setPixmap(pixmap(array_to_preview(np.clip(arr,0,255).astype(np.uint8),10),650))
        vals={i:int((mask==i).sum()) for i in range(4)}; textured=int((self.state.region_texture>0).sum())
        self.region_info.setText(f"Normal: {vals[0]} | Preservar: {vals[1]} | Simplificar: {vals[2]} | Simplificar muito: {vals[3]} | Texturizadas: {textured} células")

    def clear_regions(self):
        self.state.region_mask[:]=0; self.state.region_texture[:]=0; self.refresh_region_preview()

    def approve_regions(self):
        self.state.save_checkpoint('region_mask',self.state.region_mask); self.state.save_checkpoint('region_texture',self.state.region_texture); self.open_quantize()

    def skip_regions(self):
        self.clear_regions(); self.approve_regions()

    def build_quantize(self):
        w=QWidget(); root=QVBoxLayout(w); root.addWidget(QLabel('<h2>Simplificação perceptual de cores</h2>'))
        top=QHBoxLayout(); self.before_q=PixelLabel(); self.after_q=PixelLabel()
        for lab,title in ((self.before_q,'ANTES — clique para selecionar uma cor'),(self.after_q,'DEPOIS')):
            box=QGroupBox(title); bl=QVBoxLayout(box); lab.setAlignment(Qt.AlignCenter); lab.setMinimumSize(420,420); bl.addWidget(lab); top.addWidget(box)
        self.before_q.cellClicked.connect(self.pick_color); root.addLayout(top,1)
        controls=QHBoxLayout(); self.color_count=QSpinBox(); self.color_count.setRange(2,250); self.color_count.setValue(20)
        self.strategy=QComboBox(); self.strategy.addItem('Equilibrado','balanced'); self.strategy.addItem('Preservar cores dominantes','dominant'); self.strategy.addItem('Preservar detalhes/cores raras','rare_details')
        run=QPushButton('CALCULAR / REFazer'); run.clicked.connect(self.run_quantization)
        controls.addWidget(QLabel('Cores finais:')); controls.addWidget(self.color_count); controls.addWidget(QLabel('Estratégia:')); controls.addWidget(self.strategy); controls.addWidget(run); root.addLayout(controls)
        mid=QHBoxLayout(); self.selected_color_text=QLabel('Clique em uma célula da imagem ANTES para selecionar a cor.'); self.selected_color_text.setWordWrap(True)
        lock=QPushButton('🔒 Travar / destravar'); lock.clicked.connect(self.toggle_lock); priority=QPushButton('⭐ Priorizar / normalizar'); priority.clicked.connect(self.toggle_priority)
        mid.addWidget(self.selected_color_text,1); mid.addWidget(lock); mid.addWidget(priority); root.addLayout(mid)
        self.palette_list=QListWidget(); self.palette_list.setMaximumHeight(125); root.addWidget(self.palette_list)
        self.quant_info=QLabel(); self.quant_info.setAlignment(Qt.AlignCenter); root.addWidget(self.quant_info)
        btn=QHBoxLayout(); approve=QPushButton('APROVAR E CONTINUAR'); approve.clicked.connect(self.approve_quant); back=QPushButton('Voltar à escolha da Pixel Art'); back.clicked.connect(lambda:self.stack.setCurrentIndex(2)); stop=QPushButton('Encerrar'); stop.clicked.connect(self.close)
        for b in (approve,back,stop): btn.addWidget(b)
        root.addLayout(btn); self.stack.addWidget(w)

    def open_quantize(self):
        self.current_picked=None; self.before_q.setPixmap(pixmap(array_to_preview(self.state.selected_matrix,10),500)); self.refresh_palette_list(); self.run_quantization(); self.stack.setCurrentIndex(5)

    def pick_color(self,col,row):
        c=tuple(map(int,self.state.selected_matrix[row,col])); self.current_picked=c; count,pct=color_info(self.state.selected_matrix,c)
        flags=[]
        if c in self.state.locked_colors: flags.append('🔒 TRAVADA')
        if c in self.state.priority_colors: flags.append('⭐ PRIORITÁRIA')
        self.selected_color_text.setText(f'Linha {row+1}, coluna {col+1} | RGB {c} | #{c[0]:02X}{c[1]:02X}{c[2]:02X} | {count} células ({pct:.2f}%) | '+(' '.join(flags) if flags else 'Normal'))

    def toggle_lock(self):
        if self.current_picked is None: QMessageBox.information(self,'Seleção','Clique primeiro em uma célula da imagem ANTES.'); return
        c=self.current_picked
        if c in self.state.locked_colors: self.state.locked_colors.remove(c)
        else: self.state.locked_colors.add(c); self.state.priority_colors.pop(c,None)
        self.pick_color(0,0) if False else None; self.refresh_palette_list(); self.run_quantization()

    def toggle_priority(self):
        if self.current_picked is None: QMessageBox.information(self,'Seleção','Clique primeiro em uma célula da imagem ANTES.'); return
        c=self.current_picked
        if c in self.state.locked_colors: QMessageBox.information(self,'Cor travada','Uma cor travada já tem proteção máxima. Destrave-a antes de torná-la apenas prioritária.'); return
        if c in self.state.priority_colors: self.state.priority_colors.pop(c)
        else: self.state.priority_colors[c]=4.0
        self.refresh_palette_list(); self.run_quantization()

    def refresh_palette_list(self):
        self.palette_list.clear()
        for c in sorted(self.state.locked_colors): self.palette_list.addItem(f'🔒 #{c[0]:02X}{c[1]:02X}{c[2]:02X}  RGB {c}')
        for c in sorted(self.state.priority_colors): self.palette_list.addItem(f'⭐ #{c[0]:02X}{c[1]:02X}{c[2]:02X}  RGB {c}')
        if not self.state.locked_colors and not self.state.priority_colors: self.palette_list.addItem('Nenhuma cor protegida. Clique em um pixel da imagem ANTES para selecionar.')

    def run_quantization(self):
        if self.state.selected_matrix is None:return
        n=self.color_count.value(); strategy=self.strategy.currentData()
        try:
            result,palette,info=quantize_lab(self.state.selected_matrix,n,self.state.locked_colors,self.state.priority_colors,strategy,self.state.region_mask,self.state.region_texture)
        except ValueError as e: QMessageBox.warning(self,'Não é possível simplificar',str(e)); return
        self.state.requested_colors=n; self.state.quant_strategy=strategy; self.state.quantized_matrix=result
        self.after_q.setPixmap(pixmap(array_to_preview(result,10),500))
        self.quant_info.setText(f"Cores antes: {info['original_colors']}  |  Solicitadas: {n}  |  Efetivas: {info['final_colors']}  |  🔒 {len(self.state.locked_colors)}  |  ⭐ {len(self.state.priority_colors)}  |  Estratégia: {self.strategy.currentText()}")

    def approve_quant(self):
        if self.state.quantized_matrix is None:return
        reply=QMessageBox.question(self,'Aprovar simplificação','Você aprova esta simplificação de cores para a próxima etapa?',QMessageBox.Yes|QMessageBox.No)
        if reply!=QMessageBox.Yes:return
        self.state.save_checkpoint('quantized',self.state.quantized_matrix); self.state.save_checkpoint('locked_colors',self.state.locked_colors); self.state.save_checkpoint('priority_colors',self.state.priority_colors)
        QMessageBox.information(self,'Checkpoint salvo','Simplificação aprovada e salva como checkpoint.\n\nPróxima etapa do projeto: códigos, legenda e estatísticas da paleta.')
