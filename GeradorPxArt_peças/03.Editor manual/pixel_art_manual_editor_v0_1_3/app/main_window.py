
import json
from pathlib import Path
import numpy as np
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QFileDialog,
    QSplitter,QScrollArea,QCheckBox,QMessageBox,QComboBox
)

from .editor_canvas import PixelCanvas
from .palette_widget import PalettePanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Art Manual Editor v0.1.3")
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
        self.save_grid_btn=QPushButton("Salvar imagem com grade")

        self.grid_check=QCheckBox("Mostrar grade")
        self.grid_check.setChecked(True)

        self.grid_mode=QComboBox()
        self.grid_mode.addItem("Grade lógica: Auto", "auto")
        self.grid_mode.addItem("Grade lógica: 50x50", 50)
        self.grid_mode.addItem("Grade lógica: 100x100", 100)
        self.grid_mode.addItem("Grade lógica: Pixels reais", "raw")

        for b in [self.open_btn,self.palette_btn,self.undo_btn,self.redo_btn,
                  self.save_btn,self.save_preview_btn,self.save_grid_btn]:
            top.addWidget(b)

        top.addWidget(self.grid_check)
        top.addWidget(self.grid_mode)
        top.addStretch(1)

        self.info=QLabel(
            "Botão esquerdo pinta a CÉLULA INTEIRA da grade lógica • "
            "botão direito funciona como conta-gotas"
        )
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
            "As cores ficam agrupadas pelos títulos do JSON (ex.: olhos, língua, coleira). "
            "Passe o mouse sobre uma cor para destacar todos os pixels correspondentes na imagem."
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
        self.save_grid_btn.clicked.connect(self.save_with_grid)
        self.grid_check.toggled.connect(self.canvas.set_grid)
        self.grid_mode.currentIndexChanged.connect(self.change_grid_mode)
        self.canvas.pixelChanged.connect(self.record_change)
        self.canvas.colorPicked.connect(self.eyedropper)
        self.palette_panel.colorSelected.connect(self.canvas.set_paint_color)
        self.palette_panel.colorHovered.connect(self.canvas.set_hover_color)
        self.palette_panel.colorHoverLeft.connect(lambda: self.canvas.set_hover_color(None))

    def change_grid_mode(self):
        val = self.grid_mode.currentData()
        self.canvas.set_logical_grid(val)
        self._refresh_status()

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
        self.grid_mode.setCurrentIndex(0)  # Auto
        self._refresh_status()

    def load_palette(self):
        path,_=QFileDialog.getOpenFileName(
            self,"Abrir paleta JSON","","JSON (*.json)"
        )
        if not path:return
        try:
            data=json.load(open(path,encoding="utf-8"))
        except Exception as e:
            QMessageBox.critical(self,"Erro",str(e));return

        # Keep entries grouped by area/title and preserve order.
        unique=[]
        seen=set()
        for row in data:
            key=(row.get("area","Sem título"), tuple(row["rgb"]))
            if key in seen:
                continue
            seen.add(key)
            unique.append(row)

        self.palette_entries=unique
        self.palette_panel.set_palette(unique)
        groups = len({row.get("area","Sem título") for row in unique})
        self.info.setText(f"Paleta carregada: {len(unique)} cores únicas em {groups} grupos")

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
        x0,y0,x1,y1 = self.canvas._logical_cell_bounds(x,y)
        self.canvas.arr[y0:y1, x0:x1] = np.array(old,dtype=np.uint8)
        self.canvas.update()
        self._recording=True
        self.redo_stack.append(change)
        self._refresh_status()

    def redo(self):
        if not self.redo_stack or self.canvas.arr is None:return
        change=self.redo_stack.pop()
        x,y,old,new=change
        self._recording=False
        x0,y0,x1,y1 = self.canvas._logical_cell_bounds(x,y)
        self.canvas.arr[y0:y1, x0:x1] = np.array(new,dtype=np.uint8)
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
        logical = self.canvas.get_logical_size()
        logical_text = f"{logical[0]}×{logical[1]}" if logical else "—"
        self.status.setText(
            f"Imagem real: {self.canvas.arr.shape[1]}×{self.canvas.arr.shape[0]} • "
            f"grade lógica: {logical_text} • "
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
        logical = self.canvas.get_logical_size()
        if logical:
            gw,gh = logical
            preview = np.zeros((gh,gw,3),dtype=np.uint8)
            for y in range(gh):
                for x in range(gw):
                    preview[y,x] = np.array(self.canvas._representative_color(x,y), dtype=np.uint8)
            im=Image.fromarray(preview)
        else:
            im=Image.fromarray(self.canvas.arr)
        scale=max(1,800//max(im.size))
        im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST).save(path)
        QMessageBox.information(self,"Salvo",path)

    def save_with_grid(self):
        if self.canvas.arr is None:
            return

        logical = self.canvas.get_logical_size()
        if not logical:
            QMessageBox.information(
                self,
                "Grade indisponível",
                "Não foi possível identificar a grade lógica da imagem."
            )
            return

        path,_=QFileDialog.getSaveFileName(
            self,
            "Salvar imagem com grade",
            "pixel_art_editada_com_grade.png",
            "PNG (*.png)"
        )
        if not path:
            return

        gw,gh = logical

        # Build a true logical matrix from the current editor state.
        matrix = np.zeros((gh,gw,3),dtype=np.uint8)
        for y in range(gh):
            for x in range(gw):
                matrix[y,x] = np.array(
                    self.canvas._representative_color(x,y),
                    dtype=np.uint8
                )

        # Export scale: make each logical pixel large enough to see the grid clearly.
        cell_size = max(6, 900 // max(gw,gh))
        grid_width = 1

        out_w = gw * cell_size + (gw + 1) * grid_width
        out_h = gh * cell_size + (gh + 1) * grid_width

        # Neutral dark grid; grid is presentation-only and is not part of the palette.
        grid_rgb = (55,55,55)
        out = np.zeros((out_h,out_w,3),dtype=np.uint8)
        out[:,:,:] = np.array(grid_rgb,dtype=np.uint8)

        for y in range(gh):
            y0 = grid_width + y * (cell_size + grid_width)
            y1 = y0 + cell_size
            for x in range(gw):
                x0 = grid_width + x * (cell_size + grid_width)
                x1 = x0 + cell_size
                out[y0:y1,x0:x1] = matrix[y,x]

        Image.fromarray(out).save(path)
        QMessageBox.information(
            self,
            "Salvo",
            f"Imagem com grade salva em:\n{path}\n\n"
            "Observação: a grade é apenas visual e não altera a paleta lógica."
        )
