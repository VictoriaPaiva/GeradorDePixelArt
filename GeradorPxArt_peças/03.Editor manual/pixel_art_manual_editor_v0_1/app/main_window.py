
import json
from pathlib import Path
import numpy as np
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QFileDialog,
    QSplitter,QScrollArea,QCheckBox,QMessageBox
)

from .editor_canvas import PixelCanvas
from .palette_widget import PalettePanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Art Manual Editor v0.1")
        self.resize(1500,950)

        self.arr=None
        self.image_path=None
        self.palette_entries=[]
        self.undo_stack=[]
        self.redo_stack=[]
        self._recording=True

        self._build()

    def _build(self):
        rootw=QWidget()
        self.setCentralWidget(rootw)
        root=QVBoxLayout(rootw)

        top=QHBoxLayout()
        self.open_btn=QPushButton("Abrir matriz PNG")
        self.palette_btn=QPushButton("Carregar paleta JSON")
        self.undo_btn=QPushButton("Desfazer")
        self.redo_btn=QPushButton("Refazer")
        self.save_btn=QPushButton("Salvar PNG")
        self.save_preview_btn=QPushButton("Salvar preview ampliado")

        self.grid_check=QCheckBox("Mostrar grade")
        self.grid_check.setChecked(True)

        for b in [self.open_btn,self.palette_btn,self.undo_btn,self.redo_btn,
                  self.save_btn,self.save_preview_btn]:
            top.addWidget(b)
        top.addWidget(self.grid_check)
        top.addStretch(1)

        self.info=QLabel("Botão esquerdo pinta • botão direito funciona como conta-gotas")
        top.addWidget(self.info)
        root.addLayout(top)

        split=QSplitter(Qt.Horizontal)
        root.addWidget(split,1)

        left=QWidget()
        ll=QVBoxLayout(left)
        self.canvas=PixelCanvas()
        ll.addWidget(self.canvas,1)
        self.status=QLabel("Nenhuma imagem carregada")
        ll.addWidget(self.status)

        right=QWidget()
        rl=QVBoxLayout(right)
        title=QLabel("PALETA PERMITIDA")
        title.setStyleSheet("font-size:18px;font-weight:700;")
        rl.addWidget(title)

        help_=QLabel(
            "Selecione uma cor e clique/arraste sobre os pixels. "
            "Somente cores desta paleta serão usadas."
        )
        help_.setWordWrap(True)
        rl.addWidget(help_)

        self.palette_panel=PalettePanel()
        scroll=QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.palette_panel)
        rl.addWidget(scroll,1)

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([1000,500])

        self.open_btn.clicked.connect(self.open_image)
        self.palette_btn.clicked.connect(self.load_palette)
        self.undo_btn.clicked.connect(self.undo)
        self.redo_btn.clicked.connect(self.redo)
        self.save_btn.clicked.connect(self.save_png)
        self.save_preview_btn.clicked.connect(self.save_preview)
        self.grid_check.toggled.connect(self.canvas.set_grid)
        self.canvas.pixelChanged.connect(self.record_change)
        self.canvas.colorPicked.connect(self.eyedropper)
        self.palette_panel.colorSelected.connect(self.canvas.set_paint_color)

    def open_image(self):
        path,_=QFileDialog.getOpenFileName(
            self,"Abrir matriz PNG","","PNG (*.png);;Imagens (*.png *.jpg *.jpeg *.webp)"
        )
        if not path:return
        try:
            im=Image.open(path).convert("RGB")
        except Exception as e:
            QMessageBox.critical(self,"Erro",str(e));return

        self.arr=np.array(im,dtype=np.uint8)
        self.image_path=path
        self.canvas.set_array(self.arr)
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.status.setText(
            f"{Path(path).name} • matriz {im.width}×{im.height} • "
            f"{len(np.unique(self.arr.reshape(-1,3),axis=0))} cores atuais"
        )

    def load_palette(self):
        path,_=QFileDialog.getOpenFileName(
            self,"Abrir paleta JSON","","JSON (*.json)"
        )
        if not path:return
        try:
            data=json.load(open(path,encoding="utf-8"))
        except Exception as e:
            QMessageBox.critical(self,"Erro",str(e));return

        unique=[]
        seen=set()
        for row in data:
            rgb=tuple(row["rgb"])
            if rgb in seen:continue
            seen.add(rgb)
            unique.append(row)

        self.palette_entries=unique
        self.palette_panel.set_palette(unique)
        self.info.setText(f"Paleta carregada: {len(unique)} cores únicas")

    def record_change(self,x,y,old,new):
        if not self._recording:return
        self.undo_stack.append((x,y,old,new))
        self.redo_stack.clear()
        self._refresh_status()

    def undo(self):
        if not self.undo_stack or self.canvas.arr is None:return
        change=self.undo_stack.pop()
        x,y,old,new=change
        self._recording=False
        self.canvas.arr[y,x]=np.array(old,dtype=np.uint8)
        self.canvas.update()
        self._recording=True
        self.redo_stack.append(change)
        self._refresh_status()

    def redo(self):
        if not self.redo_stack or self.canvas.arr is None:return
        change=self.redo_stack.pop()
        x,y,old,new=change
        self._recording=False
        self.canvas.arr[y,x]=np.array(new,dtype=np.uint8)
        self.canvas.update()
        self._recording=True
        self.undo_stack.append(change)
        self._refresh_status()

    def eyedropper(self,rgb):
        if self.palette_panel.select_if_present(rgb):
            self.info.setText(f"Conta-gotas: RGB {rgb}")
        else:
            self.info.setText(
                f"RGB {rgb} está na imagem, mas não faz parte da paleta carregada."
            )

    def _refresh_status(self):
        if self.canvas.arr is None:return
        colors=len(np.unique(self.canvas.arr.reshape(-1,3),axis=0))
        self.status.setText(
            f"Matriz {self.canvas.arr.shape[1]}×{self.canvas.arr.shape[0]} • "
            f"{colors} cores atuais • alterações registradas: {len(self.undo_stack)}"
        )

    def save_png(self):
        if self.canvas.arr is None:return
        path,_=QFileDialog.getSaveFileName(
            self,"Salvar matriz","pixel_art_editada.png","PNG (*.png)"
        )
        if not path:return
        Image.fromarray(self.canvas.arr).save(path)
        QMessageBox.information(self,"Salvo",path)

    def save_preview(self):
        if self.canvas.arr is None:return
        path,_=QFileDialog.getSaveFileName(
            self,"Salvar preview","pixel_art_editada_preview.png","PNG (*.png)"
        )
        if not path:return
        im=Image.fromarray(self.canvas.arr)
        scale=max(1,800//max(im.size))
        im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST).save(path)
        QMessageBox.information(self,"Salvo",path)
