from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QFileDialog,QMessageBox,QStackedWidget,QGroupBox,QSlider,QRadioButton,QButtonGroup)
from app.state_manager import ProjectState
from image_processing.core import center_square,crop_square,method_fidelity,method_details,method_pixel_art,array_to_preview

METHODS={
 'Fidelidade': method_fidelity,
 'Detalhes': method_details,
 'Pixel Art': method_pixel_art,
}

def pixmap(img:Image.Image,max_size=520):
    p=QPixmap.fromImage(ImageQt(img.convert('RGB')))
    return p.scaled(max_size,max_size,Qt.KeepAspectRatio,Qt.FastTransformation)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.state=ProjectState(); self.setWindowTitle('Pixel Art Creator — v0.1'); self.resize(1250,820)
        self.stack=QStackedWidget(); self.setCentralWidget(self.stack)
        self.build_start(); self.build_crop(); self.build_compare(); self.build_approved()

    def build_start(self):
        w=QWidget(); l=QVBoxLayout(w); l.setAlignment(Qt.AlignCenter)
        title=QLabel('PIXEL ART CREATOR'); title.setStyleSheet('font-size:30px;font-weight:700'); title.setAlignment(Qt.AlignCenter)
        sub=QLabel('Versão 0.1 — imagem → enquadramento → 3 métodos → aprovação'); sub.setAlignment(Qt.AlignCenter)
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
        w=QWidget(); l=QVBoxLayout(w); self.final_title=QLabel('<h2>Checkpoint aprovado</h2>'); self.final_view=QLabel(); self.final_view.setAlignment(Qt.AlignCenter); self.final_text=QLabel(); self.final_text.setAlignment(Qt.AlignCenter); back=QPushButton('Voltar e escolher outra versão'); back.clicked.connect(lambda:self.stack.setCurrentIndex(2)); l.addWidget(self.final_title); l.addWidget(self.final_view,1); l.addWidget(self.final_text); l.addWidget(back); self.stack.addWidget(w)

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
        self.method_widgets['Fidelidade'][1].setChecked(True)

    def approve_method(self):
        checked=self.method_group.checkedButton()
        if checked is None: QMessageBox.warning(self,'Escolha','Selecione uma versão.'); return
        name=next(n for n,(_,r) in self.method_widgets.items() if r is checked); arr=self.state.candidates[name]
        reply=QMessageBox.question(self,'Confirmar',f'Você aprova a versão “{name}” como base para as próximas etapas?',QMessageBox.Yes|QMessageBox.No)
        if reply!=QMessageBox.Yes:return
        self.state.selected_method=name; self.state.selected_matrix=arr.copy(); self.state.save_checkpoint('pixel_art',arr)
        self.final_view.setPixmap(pixmap(array_to_preview(arr,10),560)); self.final_text.setText(f'Método aprovado: {name}\nMatriz lógica: 50 × 50 = 2.500 células\nPróxima versão: simplificação e travamento de cores.')
        self.stack.setCurrentIndex(3)
