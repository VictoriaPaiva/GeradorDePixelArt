
import csv,json
from pathlib import Path
from PIL import Image
import numpy as np
from skimage.color import rgb2lab

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
        self.setWindowTitle("Pixel Art Palette Selector v0.6")
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
        self.pick_btn=QPushButton("Selecionar cor pela imagem")
        self.pick_btn.setCheckable(True)

        for b in [self.open_btn,self.save_area_btn,self.clear_btn,self.all_btn,self.pick_btn]:
            top.addWidget(b)

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

        self.total_counter=QLabel("Essenciais totais: 0")
        self.total_counter.setStyleSheet(
            "font-weight:700;font-size:14px;color:#1f5fae;padding:5px;"
        )
        top.addWidget(self.total_counter)

        self.export_json_btn=QPushButton("Exportar JSON")
        self.export_csv_btn=QPushButton("Exportar CSV")
        self.export_txt_btn=QPushButton("Exportar TXT")
        top.addWidget(self.export_json_btn)
        top.addWidget(self.export_csv_btn)
        top.addWidget(self.export_txt_btn)

        root.addLayout(top)

        self.info=QLabel(
            "Modo normal: desenhe regiões. Ative “Selecionar cor pela imagem” para clicar "
            "diretamente em uma cor dentro de uma área já criada."
        )
        self.info.setWordWrap(True)
        root.addWidget(self.info)

        split=QSplitter(Qt.Horizontal)
        root.addWidget(split,1)

        left=QWidget()
        ll=QVBoxLayout(left)
        title=QLabel("IMAGEM + SELEÇÃO")
        title.setStyleSheet("font-size:18px;font-weight:700;")
        ll.addWidget(title)

        self.canvas=MaskCanvas()
        ll.addWidget(self.canvas,1)

        self.stats=QLabel("Seleção atual: 0%")
        ll.addWidget(self.stats)

        right=QWidget()
        rl=QVBoxLayout(right)
        t=QLabel("ÁREAS E PALETAS")
        t.setStyleSheet("font-size:18px;font-weight:700;")
        rl.addWidget(t)

        hint=QLabel(
            "As cores essenciais de cada área ficam automaticamente no topo. "
            "Cada área possui seu próprio contador."
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

        self.open_btn.clicked.connect(self.open_image)
        self.save_area_btn.clicked.connect(self.create_area)
        self.clear_btn.clicked.connect(self.canvas.clear_working)
        self.all_btn.clicked.connect(self.canvas.select_all_working)
        self.pick_btn.toggled.connect(self.toggle_pick_mode)
        self.brush.valueChanged.connect(self.canvas.set_brush_size)
        self.erase.toggled.connect(self.canvas.set_erase)
        self.canvas.selectionChanged.connect(self.update_stats)
        self.canvas.colorClicked.connect(self.pick_color_from_image)

        self.export_json_btn.clicked.connect(self.export_json)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_txt_btn.clicked.connect(self.export_txt)

    def toggle_pick_mode(self,enabled):
        self.canvas.set_pick_mode(enabled)
        self.brush.setEnabled(not enabled)
        self.erase.setEnabled(not enabled)
        self.save_area_btn.setEnabled(not enabled)
        self.clear_btn.setEnabled(not enabled)
        self.all_btn.setEnabled(not enabled)

        if enabled:
            self.pick_btn.setText("✓ Seleção pela imagem ATIVA")
            self.info.setText(
                "Clique em uma cor dentro de uma área já criada. "
                "A cor/grupo correspondente será marcada ou desmarcada como essencial."
            )
        else:
            self.pick_btn.setText("Selecionar cor pela imagem")
            self.info.setText(
                "Modo normal: desenhe regiões. Ative “Selecionar cor pela imagem” para clicar "
                "diretamente em uma cor dentro de uma área já criada."
            )

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
        self.update_total_counter()

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
        name,ok=QInputDialog.getText(self,"Nome da área","Nome da área:",text=default)
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

        self.areas.append({
            "id":self.area_counter,
            "name":name,
            "mask":mask.copy(),
            "pixel_count":len(pixels),
            "palette":palette,
            "selected":{},
            "expanded":True,
        })

        self.canvas.clear_working()
        self.rebuild_sections()
        self.update_total_counter()

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
        self.update_total_counter()

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
        radius=max(8.0,self.threshold.value()*4.5)
        self.canvas.set_color_hover(item.rgb,area["mask"],radius)

    def toggle_area_color(self,area,item,state):
        if state:
            area["selected"][item.rgb]=item
        else:
            area["selected"].pop(item.rgb,None)

        # Rebuild so selected colors immediately move to the top.
        self.rebuild_sections()
        self.update_total_counter()

    def update_total_counter(self):
        total=sum(len(a.get("selected",{})) for a in self.areas)
        self.total_counter.setText(f"Essenciais totais: {total}")

    def _nearest_palette_item(self,area,rgb):
        palette=area.get("palette",[])
        if not palette:
            return None

        source=np.array(rgb,dtype=float).reshape(1,1,3)/255.0
        source_lab=rgb2lab(source).reshape(3)

        prgb=np.array([x.rgb for x in palette],dtype=float)/255.0
        plab=rgb2lab(prgb.reshape(1,-1,3)).reshape(-1,3)
        d=np.linalg.norm(plab-source_lab,axis=1)
        return palette[int(np.argmin(d))]

    def pick_color_from_image(self,x,y,rgb):
        # If areas overlap, prefer the most recently created one.
        matches=[]
        for area in reversed(self.areas):
            m=area["mask"]
            if 0 <= y < m.shape[0] and 0 <= x < m.shape[1] and m[y,x]:
                matches.append(area)

        if not matches:
            self.info.setText(
                f"RGB{rgb}: esse ponto não pertence a nenhuma área salva."
            )
            return

        area=matches[0]
        item=self._nearest_palette_item(area,rgb)
        if item is None:
            self.info.setText(
                f"A área “{area['name']}” não possui uma paleta calculada."
            )
            return

        already=item.rgb in area["selected"]
        if already:
            area["selected"].pop(item.rgb,None)
            action="removida das essenciais"
        else:
            area["selected"][item.rgb]=item
            action="marcada como essencial"

        self.info.setText(
            f'{area["name"]}: pixel RGB{rgb} → {item.hex} / RGB{item.rgb} {action}.'
        )

        radius=max(8.0,self.threshold.value()*4.5)
        self.canvas.set_color_hover(item.rgb,area["mask"],radius)
        self.rebuild_sections()
        self.update_total_counter()

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
        self.update_total_counter()

    def delete_area(self,area):
        ans=QMessageBox.question(
            self,"Excluir área",
            f"Excluir “{area['name']}” e toda a sua paleta?"
        )
        if ans!=QMessageBox.Yes:return
        self.areas=[a for a in self.areas if a["id"]!=area["id"]]
        self.canvas.set_hover_area_mask(None)
        self.canvas.clear_color_hover()
        self.rebuild_sections()
        self.update_total_counter()

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
            QMessageBox.information(self,"Nada selecionado",
                                    "Selecione pelo menos uma cor essencial.")
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
            w.writerow(["area","code","hex","r","g","b",
                        "count_in_area","percent_in_area","grouped_nuances"])
            for row in rows:
                r,g,b=row["rgb"]
                w.writerow([row["area"],row["code"],row["hex"],r,g,b,
                            row["count_in_area"],f'{row["percent_in_area"]:.6f}',
                            row["grouped_nuances"]])
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

        lines=["CORES ESSENCIAIS POR ÁREA","="*50,""]
        for area_name,items in grouped.items():
            lines.append(f"[{area_name}]")
            for item in items:
                r,g,b=item["rgb"]
                lines.append(f'{item["code"]} | {item["hex"]} | RGB({r}, {g}, {b})')
            lines.append("")

        with open(path,"w",encoding="utf-8") as f:
            f.write("\n".join(lines))
        QMessageBox.information(self,"Exportado",path)
