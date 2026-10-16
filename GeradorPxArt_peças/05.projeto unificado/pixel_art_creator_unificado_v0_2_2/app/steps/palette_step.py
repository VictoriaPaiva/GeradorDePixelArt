
from pathlib import Path
from PIL import Image
from skimage.color import rgb2lab
import numpy as np

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QSplitter,QScrollArea,
    QSpinBox,QDoubleSpinBox,QCheckBox,QMessageBox,QInputDialog
)

from .base_step import BaseStep
from ..widgets.mask_canvas import MaskCanvas
from ..widgets.area_section import AreaSection
from ..palette_utils import grouped_colors_from_pixels


class PaletteStep(BaseStep):
    workspaceChanged = Signal()

    def __init__(self, state, workspace):
        super().__init__(
            "3. Áreas e paletas",
            "Crie regiões nomeadas sobre a Pixel Art aprovada e gere uma paleta agrupada para cada área. "
            "Nesta etapa as cores ainda não precisam ser marcadas como essenciais; isso será feito na próxima tela."
        )
        self.state = state
        self.workspace = workspace
        self.image = None

        controls=QHBoxLayout()
        self.use_btn=QPushButton("Carregar Pixel Art aprovada")
        self.save_area_btn=QPushButton("Criar área + gerar paleta")
        self.clear_btn=QPushButton("Limpar seleção atual")
        self.all_btn=QPushButton("Selecionar imagem inteira")
        for b in [self.use_btn,self.save_area_btn,self.clear_btn,self.all_btn]:
            controls.addWidget(b)

        controls.addSpacing(8)
        controls.addWidget(QLabel("Pincel:"))
        self.brush=QSpinBox()
        self.brush.setRange(3,250)
        self.brush.setValue(35)
        controls.addWidget(self.brush)

        self.erase=QCheckBox("Borracha")
        controls.addWidget(self.erase)

        controls.addSpacing(8)
        controls.addWidget(QLabel("Cores/área:"))
        self.limit=QSpinBox()
        self.limit.setRange(20,300)
        self.limit.setValue(workspace.limit)
        controls.addWidget(self.limit)

        controls.addWidget(QLabel("Similaridade:"))
        self.threshold=QDoubleSpinBox()
        self.threshold.setRange(1.0,8.0)
        self.threshold.setSingleStep(.5)
        self.threshold.setValue(workspace.threshold)
        controls.addWidget(self.threshold)
        controls.addStretch(1)
        self.layout.addLayout(controls)

        self.info=QLabel(
            "Pinte uma região na imagem, clique em “Criar área + gerar paleta” e dê um nome à área."
        )
        self.info.setWordWrap(True)
        self.layout.addWidget(self.info)

        split=QSplitter(Qt.Horizontal)
        self.layout.addWidget(split,1)

        left=QWidget()
        ll=QVBoxLayout(left)
        self.canvas=MaskCanvas()
        ll.addWidget(self.canvas,1)
        self.stats=QLabel("Seleção atual: 0%")
        ll.addWidget(self.stats)

        right=QWidget()
        rl=QVBoxLayout(right)
        h=QLabel("ÁREAS E PALETAS")
        h.setStyleSheet("font-size:18px;font-weight:700;")
        rl.addWidget(h)
        hint=QLabel("Passe o mouse sobre o título de uma área para destacar a região. "
                    "Passe o mouse sobre uma cor para localizar tons semelhantes dentro daquela área.")
        hint.setWordWrap(True)
        rl.addWidget(hint)

        self.sections_container=QWidget()
        self.sections_layout=QVBoxLayout(self.sections_container)
        scroll=QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.sections_container)
        rl.addWidget(scroll,1)

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([620,820])

        self.use_btn.clicked.connect(self.load_approved_image)
        self.save_area_btn.clicked.connect(self.create_area)
        self.clear_btn.clicked.connect(self.canvas.clear_working)
        self.all_btn.clicked.connect(self.canvas.select_all_working)
        self.brush.valueChanged.connect(self.canvas.set_brush_size)
        self.erase.toggled.connect(self.canvas.set_erase)
        self.canvas.selectionChanged.connect(self.update_stats)
        self.limit.valueChanged.connect(self.settings_changed)
        self.threshold.valueChanged.connect(self.settings_changed)

        self.refresh()

    def set_context(self,state,workspace):
        self.state=state
        self.workspace=workspace
        self.limit.setValue(workspace.limit)
        self.threshold.setValue(workspace.threshold)
        self.refresh()

    def settings_changed(self):
        self.workspace.limit=self.limit.value()
        self.workspace.threshold=self.threshold.value()
        self.sync()

    def load_approved_image(self):
        path=self.state.ai_image_path
        if not path or not Path(path).exists():
            QMessageBox.information(self,"Sem Pixel Art","A etapa 2 precisa possuir uma Pixel Art carregada.")
            return

        # If image changed, old masks no longer match reliably.
        if self.workspace.image_path and Path(self.workspace.image_path) != Path(path) and self.workspace.areas:
            ans=QMessageBox.question(
                self,"Imagem alterada",
                "A Pixel Art é diferente da usada nas áreas atuais. Limpar todas as áreas e carregar a nova imagem?"
            )
            if ans != QMessageBox.Yes:
                return
            self.workspace.clear()

        self.workspace.image_path=path
        self.image=Image.open(path).convert("RGB")
        self.canvas.set_image(self.image)
        self.rebuild_sections()
        self.update_stats()
        self.sync()

    def refresh(self):
        path=self.workspace.image_path or self.state.ai_image_path
        if path and Path(path).exists():
            try:
                self.workspace.image_path=path
                self.image=Image.open(path).convert("RGB")
                self.canvas.set_image(self.image)
            except Exception:
                self.image=None
        else:
            self.image=None
        self.rebuild_sections()
        self.update_stats()

    def sync(self):
        self.state.metadata["palette_workspace"]=self.workspace.to_state_dict()
        self.state.dirty=True
        self.state.unapprove("palette")
        self.state.unapprove("essential")
        self.state.invalidate_after("essential")
        self.workspaceChanged.emit()

    def update_stats(self):
        frac=self.canvas.working_fraction()*100
        n=len(self.canvas.selected_pixels())
        self.stats.setText(f"Seleção atual: {frac:.2f}% • {n:,} pixels")

    def create_area(self):
        if self.image is None:
            self.load_approved_image()
            if self.image is None:
                return

        mask=self.canvas.get_working_mask()
        if mask is None or not mask.any():
            QMessageBox.information(self,"Sem seleção","Pinte uma região antes de criar a área.")
            return

        self.workspace.area_counter+=1
        default=f"Área selecionada {self.workspace.area_counter}"
        name,ok=QInputDialog.getText(self,"Nome da área","Nome da área:",text=default)
        if not ok:
            self.workspace.area_counter-=1
            return
        name=name.strip() or default

        pixels=self.canvas.selected_pixels(mask)
        palette=grouped_colors_from_pixels(
            pixels,
            limit=self.limit.value(),
            delta_e_threshold=self.threshold.value()
        )

        self.workspace.areas.append({
            "id":self.workspace.area_counter,
            "name":name,
            "mask":mask.copy(),
            "pixel_count":len(pixels),
            "palette":palette,
            "selected":{},
            "expanded":True,
        })
        self.canvas.clear_working()
        self.rebuild_sections()
        self.sync()

    def recalc_area(self,area):
        pixels=self.canvas.selected_pixels(area["mask"])
        area["palette"]=grouped_colors_from_pixels(
            pixels,
            limit=self.limit.value(),
            delta_e_threshold=self.threshold.value()
        )
        new_rgbs={x.rgb for x in area["palette"]}
        area["selected"]={rgb:item for rgb,item in area["selected"].items() if rgb in new_rgbs}
        self.rebuild_sections()
        self.sync()

    def rebuild_sections(self):
        while self.sections_layout.count():
            item=self.sections_layout.takeAt(0)
            w=item.widget()
            if w:w.deleteLater()

        for area in self.workspace.areas:
            sec=AreaSection(area, selectable=False, manageable=True)
            sec.hoverIn.connect(lambda a:self.canvas.set_hover_area_mask(a["mask"]))
            sec.hoverOut.connect(lambda:self.canvas.set_hover_area_mask(None))
            sec.colorHover.connect(self.hover_color)
            sec.colorHoverOut.connect(self.canvas.clear_color_hover)
            sec.deletePaletteRequested.connect(self.delete_palette)
            sec.deleteAreaRequested.connect(self.delete_area)
            sec.recalcRequested.connect(self.recalc_area)
            self.sections_layout.addWidget(sec)

        self.sections_layout.addStretch(1)

    def hover_color(self,area,item):
        radius=max(8.0,self.threshold.value()*4.5)
        self.canvas.set_color_hover(item.rgb,area["mask"],radius)

    def delete_palette(self,area):
        ans=QMessageBox.question(
            self,"Excluir paleta",
            f"Excluir somente a paleta de “{area['name']}”?\nA região será mantida."
        )
        if ans!=QMessageBox.Yes:return
        area["palette"]=[]
        area["selected"]={}
        self.canvas.clear_color_hover()
        self.rebuild_sections()
        self.sync()

    def delete_area(self,area):
        ans=QMessageBox.question(
            self,"Excluir área",
            f"Excluir “{area['name']}” e toda a sua paleta?"
        )
        if ans!=QMessageBox.Yes:return
        self.workspace.areas=[a for a in self.workspace.areas if a["id"]!=area["id"]]
        self.canvas.set_hover_area_mask(None)
        self.canvas.clear_color_hover()
        self.rebuild_sections()
        self.sync()

    def is_ready(self):
        return bool(self.workspace.areas) and all(a.get("palette") for a in self.workspace.areas)
