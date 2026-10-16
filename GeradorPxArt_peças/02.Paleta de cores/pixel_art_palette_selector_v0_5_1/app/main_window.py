
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
        self.setWindowTitle("Pixel Art Palette Selector v0.5")
        self.resize(1700,1000)

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

        top.addWidget(self.open_btn)
        top.addWidget(self.save_area_btn)
        top.addWidget(self.clear_btn)
        top.addWidget(self.all_btn)

        top.addSpacing(10)
        top.addWidget(QLabel("Pincel:"))
        self.brush=QSpinBox()
        self.brush.setRange(3,250)
        self.brush.setValue(35)
        top.addWidget(self.brush)

        self.erase=QCheckBox("Borracha")
        top.addWidget(self.erase)

        top.addSpacing(10)
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

        top.addStretch(1)

        self.export_json_btn=QPushButton("Exportar JSON")
        self.export_csv_btn=QPushButton("Exportar CSV")
        self.export_txt_btn=QPushButton("Exportar TXT")
        top.addWidget(self.export_json_btn)
        top.addWidget(self.export_csv_btn)
        top.addWidget(self.export_txt_btn)

        root.addLayout(top)

        info=QLabel(
            "Após salvar uma área, o magenta desaparece e a imagem volta às cores originais. "
            "Passe o mouse sobre o título da área para destacá-la; passe o mouse sobre uma cor "
            "da paleta para iluminar os pixels correspondentes."
        )
        info.setWordWrap(True)
        root.addWidget(info)

        split=QSplitter()
        split.setOrientation(Qt.Horizontal)
        root.addWidget(split,1)

        # LEFT
        left=QWidget()
        ll=QVBoxLayout(left)
        title=QLabel("IMAGEM + SELEÇÃO")
        title.setStyleSheet("font-size:18px;font-weight:700;")
        ll.addWidget(title)

        self.canvas=MaskCanvas()
        ll.addWidget(self.canvas,1)

        self.stats=QLabel("Seleção atual: 0%")
        ll.addWidget(self.stats)

        # RIGHT
        right=QWidget()
        rl=QVBoxLayout(right)
        t=QLabel("ÁREAS E PALETAS")
        t.setStyleSheet("font-size:18px;font-weight:700;")
        rl.addWidget(t)

        hint=QLabel(
            "Use ▶/▼ para recolher ou abrir a paleta de cada área. "
            "Excluir paleta mantém a região; Excluir área remove tudo."
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
        split.setSizes([740,960])

        # connections
        self.open_btn.clicked.connect(self.open_image)
        self.save_area_btn.clicked.connect(self.create_area)
        self.clear_btn.clicked.connect(self.canvas.clear_working)
        self.all_btn.clicked.connect(self.canvas.select_all_working)
        self.brush.valueChanged.connect(self.canvas.set_brush_size)
        self.erase.toggled.connect(self.canvas.set_erase)
        self.canvas.selectionChanged.connect(self.update_stats)

        self.export_json_btn.clicked.connect(self.export_json)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_txt_btn.clicked.connect(self.export_txt)

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
            self,"Nome da área","Nome da área:",text=default
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
            "selected":{},
            "expanded":True,
        }
        self.areas.append(area)

        # Important UX change: saved selection loses magenta immediately.
        self.canvas.clear_working()
        self.rebuild_sections()

    def recalc_area(self,area):
        pixels=self.canvas.selected_pixels(area["mask"])
        area["palette"]=grouped_colors_from_pixels(
            pixels,
            limit=self.limit.value(),
            delta_e_threshold=self.threshold.value()
        )
        # Keep selected only if the representative still exists.
        new_rgbs={x.rgb for x in area["palette"]}
        area["selected"]={
            rgb:item for rgb,item in area["selected"].items() if rgb in new_rgbs
        }
        self.rebuild_sections()

    def rebuild_sections(self):
        while self.sections_layout.count():
            item=self.sections_layout.takeAt(0)
            w=item.widget()
            if w:w.deleteLater()

        for area in self.areas:
            sec=AreaSection(area)
            sec.hoverIn.connect(lambda a:self.canvas.set_hover_area_mask(a["mask"]))
            sec.hoverOut.connect(lambda:self.canvas.set_hover_area_mask(None))

            sec.colorToggled.connect(self.toggle_area_color)
            sec.colorHover.connect(self.hover_color)
            sec.colorHoverOut.connect(self.canvas.clear_color_hover)

            sec.deletePaletteRequested.connect(self.delete_palette)
            sec.deleteAreaRequested.connect(self.delete_area)
            sec.recalcRequested.connect(self.recalc_area)

            self.sections_layout.addWidget(sec)

        self.sections_layout.addStretch(1)

    def hover_color(self,area,item):
        # RGB-radius linked loosely to perceptual grouping control.
        radius=max(8.0,self.threshold.value()*4.5)
        self.canvas.set_color_hover(item.rgb,area["mask"],radius)

    def toggle_area_color(self,area,item,state):
        if state:
            area["selected"][item.rgb]=item
        else:
            area["selected"].pop(item.rgb,None)

    def delete_palette(self,area):
        answer=QMessageBox.question(
            self,
            "Excluir paleta",
            f"Excluir somente a paleta de “{area['name']}”?\n"
            "A região/máscara será mantida para você poder recalcular depois.",
        )
        if answer != QMessageBox.Yes:
            return
        area["palette"]=[]
        area["selected"]={}
        self.canvas.clear_color_hover()
        self.rebuild_sections()

    def delete_area(self,area):
        answer=QMessageBox.question(
            self,
            "Excluir área",
            f"Excluir “{area['name']}” e toda a sua paleta?",
        )
        if answer != QMessageBox.Yes:
            return
        self.areas=[a for a in self.areas if a["id"]!=area["id"]]
        self.canvas.set_hover_area_mask(None)
        self.canvas.clear_color_hover()
        self.rebuild_sections()

    def _export_rows(self):
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
                    "grouped_nuances":item.member_count,
                })
        return rows

    def _ensure_rows(self):
        rows=self._export_rows()
        if not rows:
            QMessageBox.information(
                self,"Nada selecionado",
                "Selecione pelo menos uma cor essencial em alguma área."
            )
            return None
        return rows

    def export_json(self):
        rows=self._ensure_rows()
        if rows is None:return
        path,_=QFileDialog.getSaveFileName(
            self,"Exportar JSON","cores_essenciais.json","JSON (*.json)"
        )
        if not path:return
        with open(path,"w",encoding="utf-8") as f:
            json.dump(rows,f,ensure_ascii=False,indent=2)
        QMessageBox.information(self,"Exportado",path)

    def export_csv(self):
        rows=self._ensure_rows()
        if rows is None:return
        path,_=QFileDialog.getSaveFileName(
            self,"Exportar CSV","cores_essenciais.csv","CSV (*.csv)"
        )
        if not path:return
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f)
            w.writerow([
                "area","code","hex","r","g","b",
                "count_in_area","percent_in_area","grouped_nuances"
            ])
            for row in rows:
                r,g,b=row["rgb"]
                w.writerow([
                    row["area"],row["code"],row["hex"],r,g,b,
                    row["count_in_area"],f'{row["percent_in_area"]:.6f}',
                    row["grouped_nuances"]
                ])
        QMessageBox.information(self,"Exportado",path)

    def export_txt(self):
        rows=self._ensure_rows()
        if rows is None:return
        path,_=QFileDialog.getSaveFileName(
            self,"Exportar TXT","cores_essenciais.txt","TXT (*.txt)"
        )
        if not path:return

        grouped={}
        for row in rows:
            grouped.setdefault(row["area"],[]).append(row)

        lines=[]
        lines.append("CORES ESSENCIAIS POR ÁREA")
        lines.append("="*50)
        lines.append("")

        for area_name,items in grouped.items():
            lines.append(f"[{area_name}]")
            for item in items:
                r,g,b=item["rgb"]
                lines.append(
                    f'{item["code"]} | {item["hex"]} | RGB({r}, {g}, {b})'
                )
            lines.append("")

        with open(path,"w",encoding="utf-8") as f:
            f.write("\n".join(lines))

        QMessageBox.information(self,"Exportado",path)
