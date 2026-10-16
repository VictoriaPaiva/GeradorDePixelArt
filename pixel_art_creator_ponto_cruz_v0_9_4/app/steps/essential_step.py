
import csv, json
from pathlib import Path
from PIL import Image
import numpy as np
from skimage.color import rgb2lab

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QSplitter,QScrollArea,
    QMessageBox,QFileDialog
)

from .base_step import BaseStep
from ..widgets.mask_canvas import MaskCanvas
from ..widgets.area_section import AreaSection


class EssentialStep(BaseStep):
    workspaceChanged=Signal()

    def __init__(self,state,workspace):
        super().__init__(
            "4. Cores essenciais",
            "Marque as cores que precisam ser protegidas na simplificação para 50 cores. "
            "A mesma cor RGB selecionada em áreas diferentes conta apenas uma vez no total de RGBs únicos."
        )
        self.state=state
        self.workspace=workspace
        self.image=None

        top=QHBoxLayout()
        self.pick_btn=QPushButton("Selecionar cor pela imagem")
        self.zoom_out_btn=QPushButton("−")
        self.zoom_out_btn.setFixedWidth(36)
        self.zoom_in_btn=QPushButton("+")
        self.zoom_in_btn.setFixedWidth(36)
        self.fit_btn=QPushButton("Ajustar")
        self.pick_btn.setCheckable(True)
        top.addWidget(self.pick_btn)
        top.addWidget(self.zoom_out_btn)
        top.addWidget(self.zoom_in_btn)
        top.addWidget(self.fit_btn)

        self.pick_btn.setToolTip("Selecionar cor diretamente pela imagem")
        self.zoom_out_btn.setToolTip("Diminuir zoom")
        self.zoom_in_btn.setToolTip("Aumentar zoom")
        self.fit_btn.setToolTip("Ajustar imagem inteira à área disponível")

        self.total_counter=QLabel("")
        self.total_counter.setStyleSheet("font-weight:700;font-size:14px;color:#1f5fae;padding:5px;")
        top.addWidget(self.total_counter)
        top.addStretch(1)

        self.export_json_btn=QPushButton("Exportar JSON")
        self.export_csv_btn=QPushButton("Exportar CSV")
        self.export_txt_btn=QPushButton("Exportar TXT")
        for b in [self.export_json_btn,self.export_csv_btn,self.export_txt_btn]:
            top.addWidget(b)
        self.layout.addLayout(top)

        self.info=QLabel(
            "Clique nos cartões para marcar/desmarcar. Ou ative a seleção pela imagem e clique "
            "diretamente em um ponto pertencente a uma área criada."
        )
        self.info.setWordWrap(True)
        self.layout.addWidget(self.info)

        split=QSplitter(Qt.Horizontal)
        self.layout.addWidget(split,1)

        left=QWidget()
        ll=QVBoxLayout(left)
        self.canvas=MaskCanvas()
        ll.addWidget(self.canvas,1)

        right=QWidget()
        rl=QVBoxLayout(right)
        title=QLabel("CORES ESSENCIAIS POR ÁREA")
        title.setStyleSheet("font-size:18px;font-weight:700;")
        rl.addWidget(title)

        self.sections_container=QWidget()
        self.sections_layout=QVBoxLayout(self.sections_container)
        scroll=QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.sections_container)
        rl.addWidget(scroll,1)

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([620,820])

        self.pick_btn.toggled.connect(self.toggle_pick_mode)
        self.zoom_out_btn.clicked.connect(self.canvas.zoom_out)
        self.zoom_in_btn.clicked.connect(self.canvas.zoom_in)
        self.fit_btn.clicked.connect(self.canvas.reset_view)
        self.canvas.colorClicked.connect(self.pick_color_from_image)
        self.export_json_btn.clicked.connect(self.export_json)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_txt_btn.clicked.connect(self.export_txt)

        self.refresh()

    def set_context(self,state,workspace):
        self.state=state
        self.workspace=workspace
        self.refresh()

    def refresh(self):
        path=self.workspace.image_path or self.state.metadata.get("chat_matrix_art_path") or self.state.ai_image_path
        if path and Path(path).exists():
            self.image=Image.open(path).convert("RGB")
            self.canvas.set_image(self.image)
        else:
            self.image=None
        self.rebuild_sections()
        self.update_total_counter()

    def toggle_pick_mode(self,enabled):
        self.canvas.set_pick_mode(enabled)
        if enabled:
            self.pick_btn.setText("✓ Seleção pela imagem ATIVA")
            self.info.setText("Clique em uma cor dentro de uma área salva para alternar sua seleção essencial.")
        else:
            self.pick_btn.setText("Selecionar cor pela imagem")
            self.info.setText("Clique nos cartões para marcar/desmarcar ou use a seleção direta pela imagem.")

    def sync(self):
        self.state.metadata["palette_workspace"]=self.workspace.to_state_dict()
        self.state.dirty=True
        self.state.unapprove("essential")
        self.state.invalidate_after("essential")
        self.workspaceChanged.emit()

    def rebuild_sections(self):
        while self.sections_layout.count():
            item=self.sections_layout.takeAt(0)
            w=item.widget()
            if w:w.deleteLater()

        for area in self.workspace.areas:
            sec=AreaSection(area, selectable=True, manageable=False)
            sec.hoverIn.connect(lambda a:self.canvas.set_hover_area_mask(a["mask"]))
            sec.hoverOut.connect(lambda:self.canvas.set_hover_area_mask(None))
            sec.colorToggled.connect(self.toggle_area_color)
            sec.colorHover.connect(self.hover_color)
            sec.colorHoverOut.connect(self.canvas.clear_color_hover)
            self.sections_layout.addWidget(sec)
        self.sections_layout.addStretch(1)

    def hover_color(self,area,item):
        radius=max(8.0,self.workspace.threshold*4.5)
        self.canvas.set_color_hover(item.rgb,area["mask"],radius)

    def toggle_area_color(self,area,item,state):
        if state:
            area["selected"][item.rgb]=item
        else:
            area["selected"].pop(item.rgb,None)
        self.rebuild_sections()
        self.update_total_counter()
        self.sync()

    def update_total_counter(self):
        unique=set()
        selections=0
        for area in self.workspace.areas:
            selected=area.get("selected",{})
            selections += len(selected)
            unique.update(selected.keys())
        self.total_counter.setText(
            f"Seleções por área: {selections}  •  RGBs únicos: {len(unique)}"
        )

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
        matches=[]
        for area in reversed(self.workspace.areas):
            m=area["mask"]
            if m is not None and 0 <= y < m.shape[0] and 0 <= x < m.shape[1] and m[y,x]:
                matches.append(area)
        if not matches:
            self.info.setText(f"RGB{rgb}: esse ponto não pertence a nenhuma área salva.")
            return

        area=matches[0]
        item=self._nearest_palette_item(area,rgb)
        if item is None:
            self.info.setText(f"A área “{area['name']}” não possui paleta.")
            return

        if item.rgb in area["selected"]:
            area["selected"].pop(item.rgb,None)
            action="removida"
        else:
            area["selected"][item.rgb]=item
            action="marcada"

        self.info.setText(
            f'{area["name"]}: pixel RGB{rgb} → {item.hex} / RGB{item.rgb} {action} como essencial.'
        )
        radius=max(8.0,self.workspace.threshold*4.5)
        self.canvas.set_color_hover(item.rgb,area["mask"],radius)
        self.rebuild_sections()
        self.update_total_counter()
        self.sync()

    def _export_rows(self):
        rows=[]
        for area in self.workspace.areas:
            for item in area.get("selected",{}).values():
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
            QMessageBox.information(self,"Nada selecionado","Selecione pelo menos uma cor essencial.")
            return None
        return rows

    def export_json(self):
        rows=self._ensure_rows()
        if rows is None:return
        path,_=QFileDialog.getSaveFileName(self,"Exportar JSON","cores_essenciais.json","JSON (*.json)")
        if not path:return
        Path(path).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
        QMessageBox.information(self,"Exportado",path)

    def export_csv(self):
        rows=self._ensure_rows()
        if rows is None:return
        path,_=QFileDialog.getSaveFileName(self,"Exportar CSV","cores_essenciais.csv","CSV (*.csv)")
        if not path:return
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f)
            w.writerow(["area","code","hex","r","g","b","count_in_area","percent_in_area","grouped_nuances"])
            for row in rows:
                r,g,b=row["rgb"]
                w.writerow([row["area"],row["code"],row["hex"],r,g,b,row["count_in_area"],
                            f'{row["percent_in_area"]:.6f}',row["grouped_nuances"]])
        QMessageBox.information(self,"Exportado",path)

    def export_txt(self):
        rows=self._ensure_rows()
        if rows is None:return
        path,_=QFileDialog.getSaveFileName(self,"Exportar TXT","cores_essenciais.txt","TXT (*.txt)")
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
        Path(path).write_text("\n".join(lines),encoding="utf-8")
        QMessageBox.information(self,"Exportado",path)

    def unique_count(self):
        unique=set()
        for area in self.workspace.areas:
            unique.update(area.get("selected",{}).keys())
        return len(unique)
