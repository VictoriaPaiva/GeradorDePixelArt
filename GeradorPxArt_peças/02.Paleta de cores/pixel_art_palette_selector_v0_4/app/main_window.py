
import csv,json
from pathlib import Path
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,
    QFileDialog,QSplitter,QScrollArea,QSpinBox,QDoubleSpinBox,
    QCheckBox,QMessageBox,QInputDialog
)

from .mask_canvas import MaskCanvas
from .palette_utils import grouped_colors_from_pixels
from .area_section import AreaSection


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Art Palette Selector v0.4 — Áreas nomeadas")
        self.resize(1650,980)

        self.image=None
        self.image_path=None
        self.areas=[]
        self.area_counter=0

        self._build()

    def _build(self):
        rootw=QWidget()
        self.setCentralWidget(rootw)
        root=QVBoxLayout(rootw)

        top=QHBoxLayout()
        self.open_btn=QPushButton("Abrir imagem")
        self.save_area_btn=QPushButton("Criar área + gerar paleta")
        self.clear_btn=QPushButton("Limpar seleção atual")
        self.all_btn=QPushButton("Selecionar imagem inteira")
        self.export_btn=QPushButton("Exportar todas as cores essenciais")

        top.addWidget(self.open_btn)
        top.addWidget(self.save_area_btn)
        top.addWidget(self.clear_btn)
        top.addWidget(self.all_btn)

        top.addSpacing(12)
        top.addWidget(QLabel("Pincel:"))
        self.brush=QSpinBox()
        self.brush.setRange(3,250)
        self.brush.setValue(35)
        top.addWidget(self.brush)

        self.erase=QCheckBox("Borracha")
        top.addWidget(self.erase)

        top.addSpacing(12)
        top.addWidget(QLabel("Cores por área:"))
        self.limit=QSpinBox()
        self.limit.setRange(20,300)
        self.limit.setValue(200)
        top.addWidget(self.limit)

        top.addWidget(QLabel("Similaridade:"))
        self.threshold=QDoubleSpinBox()
        self.threshold.setRange(1.0,8.0)
        self.threshold.setSingleStep(.5)
        self.threshold.setValue(4.0)
        top.addWidget(self.threshold)

        top.addSpacing(12)
        top.addWidget(self.export_btn)
        top.addStretch(1)
        root.addLayout(top)

        info=QLabel(
            "Pinte uma região em magenta e clique em 'Criar área + gerar paleta'. "
            "Cada área ficará salva com nome próprio. Passe o mouse sobre o título da área "
            "para destacar na imagem exatamente a região correspondente."
        )
        info.setWordWrap(True)
        root.addWidget(info)

        split=QSplitter(Qt.Horizontal)
        root.addWidget(split,1)

        # LEFT
        left=QWidget()
        ll=QVBoxLayout(left)
        title=QLabel("IMAGEM + ÁREAS")
        title.setStyleSheet("font-size:18px;font-weight:700;")
        ll.addWidget(title)

        self.canvas=MaskCanvas()
        ll.addWidget(self.canvas,1)

        self.stats=QLabel("Seleção atual: 0%")
        ll.addWidget(self.stats)

        # RIGHT
        right=QWidget()
        rl=QVBoxLayout(right)
        t=QLabel("ÁREAS SELECIONADAS E SUAS PALETAS")
        t.setStyleSheet("font-size:18px;font-weight:700;")
        rl.addWidget(t)

        hint=QLabel(
            "As paletas ficam agrupadas por área. O título funciona como um inspetor: "
            "ao passar o mouse sobre ele, a região correspondente é destacada na imagem."
        )
        hint.setWordWrap(True)
        rl.addWidget(hint)

        self.sections_container=QWidget()
        self.sections_layout=QVBoxLayout(self.sections_container)
        self.sections_layout.setSpacing(12)
        self.sections_layout.addStretch(1)

        scroll=QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.sections_container)
        rl.addWidget(scroll,1)

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([720,930])

        self.open_btn.clicked.connect(self.open_image)
        self.save_area_btn.clicked.connect(self.create_area)
        self.clear_btn.clicked.connect(self.canvas.clear_working)
        self.all_btn.clicked.connect(self.canvas.select_all_working)
        self.brush.valueChanged.connect(self.canvas.set_brush_size)
        self.erase.toggled.connect(self.canvas.set_erase)
        self.canvas.selectionChanged.connect(self.update_stats)
        self.export_btn.clicked.connect(self.export_all_selected)

    def open_image(self):
        path,_=QFileDialog.getOpenFileName(
            self,"Abrir imagem","","Imagens (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not path:return

        try:
            self.image=Image.open(path).convert("RGB")
            self.image_path=path
        except Exception as e:
            QMessageBox.critical(self,"Erro",str(e))
            return

        self.areas=[]
        self.area_counter=0
        self.canvas.set_image(self.image)
        self.rebuild_sections()
        self.update_stats()

    def update_stats(self):
        frac=self.canvas.working_fraction()*100
        n=len(self.canvas.selected_pixels())
        self.stats.setText(f"Seleção atual: {frac:.2f}% • {n:,} pixels")

    def create_area(self):
        if self.image is None:
            QMessageBox.information(self,"Sem imagem","Abra uma imagem primeiro.")
            return

        mask=self.canvas.get_working_mask()
        if mask is None or not mask.any():
            QMessageBox.information(self,"Sem seleção","Pinte uma região antes de criar a área.")
            return

        self.area_counter+=1
        default=f"Área selecionada {self.area_counter}"
        name,ok=QInputDialog.getText(
            self,"Nome da área",
            "Nome da área:",
            text=default
        )
        if not ok:
            self.area_counter-=1
            return
        name=name.strip() or default

        pixels=self.canvas.selected_pixels(mask)
        palette=grouped_colors_from_pixels(
            pixels,
            limit=self.limit.value(),
            delta_e_threshold=self.threshold.value()
        )

        area={
            "id":self.area_counter,
            "name":name,
            "mask":mask.copy(),
            "pixel_count":len(pixels),
            "palette":palette,
            "selected":{}
        }
        self.areas.append(area)

        self.canvas.clear_working()
        self.canvas.set_saved_masks([a["mask"] for a in self.areas])
        self.rebuild_sections()

    def rebuild_sections(self):
        # remove all widgets before stretch
        while self.sections_layout.count():
            item=self.sections_layout.takeAt(0)
            w=item.widget()
            if w:w.deleteLater()

        for area in self.areas:
            sec=AreaSection(area)
            sec.hoverIn.connect(self.hover_area)
            sec.hoverOut.connect(lambda:self.canvas.set_hover_mask(None))
            sec.colorToggled.connect(self.toggle_area_color)
            sec.removeRequested.connect(self.remove_area)
            self.sections_layout.addWidget(sec)

        self.sections_layout.addStretch(1)

    def hover_area(self,area):
        self.canvas.set_hover_mask(area["mask"])

    def toggle_area_color(self,area,item,state):
        if state:
            area["selected"][item.rgb]=item
        else:
            area["selected"].pop(item.rgb,None)

    def remove_area(self,area):
        self.areas=[a for a in self.areas if a["id"]!=area["id"]]
        self.canvas.set_hover_mask(None)
        self.canvas.set_saved_masks([a["mask"] for a in self.areas])
        self.rebuild_sections()

    def export_all_selected(self):
        rows=[]
        for area in self.areas:
            for item in area["selected"].values():
                rows.append({
                    "area":area["name"],
                    "code":item.code,
                    "hex":item.hex,
                    "rgb":list(item.rgb),
                    "count_in_area":item.count,
                    "percent_in_area":item.percent,
                    "grouped_nuances":item.member_count
                })

        if not rows:
            QMessageBox.information(
                self,"Nada selecionado",
                "Selecione pelo menos uma cor essencial em alguma área."
            )
            return

        path,_=QFileDialog.getSaveFileName(
            self,"Exportar seleção","cores_essenciais_por_area.json","JSON (*.json)"
        )
        if not path:return

        with open(path,"w",encoding="utf-8") as f:
            json.dump(rows,f,ensure_ascii=False,indent=2)

        QMessageBox.information(self,"Exportado",path)
