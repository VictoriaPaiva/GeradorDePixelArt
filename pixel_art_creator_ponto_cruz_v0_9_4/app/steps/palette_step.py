
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.color import rgb2lab

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QScrollArea, QSpinBox, QDoubleSpinBox, QCheckBox, QMessageBox,
    QInputDialog, QFileDialog
)

from .base_step import BaseStep
from ..widgets.mask_canvas import MaskCanvas
from ..widgets.area_section import AreaSection
from ..widgets.global_essential_panel import GlobalEssentialPanel
from ..palette_utils import grouped_colors_from_pixels


class PaletteStep(BaseStep):
    workspaceChanged = Signal()

    def __init__(self, state, workspace):
        super().__init__(
            "3. Cores essenciais (opcional)",
            "Opcional: marque áreas e cores que devem ser protegidas durante a redução da paleta."
        )
        self.state = state
        self.workspace = workspace
        self.image = None

        # Compacta o cabeçalho herdado do BaseStep.
        title_widget = self.layout.itemAt(0).widget()
        desc_widget = self.layout.itemAt(1).widget()
        if title_widget:
            title_widget.setStyleSheet("font-size:20px;font-weight:700;")
            title_widget.setMaximumHeight(34)
        if desc_widget:
            desc_widget.setStyleSheet("font-size:12px;color:#5b6470;")
            desc_widget.setMaximumHeight(30)

        self.layout.setContentsMargins(14,10,14,8)
        self.layout.setSpacing(6)

        # --------------------------------------------------------------
        # Barra superior compacta
        # --------------------------------------------------------------
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.use_btn = QPushButton("Carregar imagem")
        self.save_area_btn = QPushButton("Criar área")
        self.clear_btn = QPushButton("Limpar")
        self.all_btn = QPushButton("Selecionar tudo")
        self.pick_btn = QPushButton("Selecionar cor")
        self.pick_btn.setCheckable(True)

        for b in [
            self.use_btn, self.save_area_btn, self.clear_btn,
            self.all_btn, self.pick_btn
        ]:
            toolbar.addWidget(b)

        toolbar.addSpacing(8)
        toolbar.addWidget(QLabel("Pincel"))
        self.brush = QSpinBox()
        self.brush.setRange(3,250)
        self.brush.setValue(35)
        self.brush.setMaximumWidth(78)
        toolbar.addWidget(self.brush)

        self.erase = QCheckBox("Borracha")
        toolbar.addWidget(self.erase)

        toolbar.addSpacing(8)
        toolbar.addWidget(QLabel("Cores"))
        self.limit = QSpinBox()
        self.limit.setRange(20,300)
        self.limit.setValue(workspace.limit)
        self.limit.setMaximumWidth(82)
        toolbar.addWidget(self.limit)

        toolbar.addWidget(QLabel("Similaridade"))
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(1.0,8.0)
        self.threshold.setSingleStep(.5)
        self.threshold.setValue(workspace.threshold)
        self.threshold.setMaximumWidth(88)
        toolbar.addWidget(self.threshold)

        toolbar.addStretch(1)

        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setFixedWidth(36)
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedWidth(36)
        self.fit_btn = QPushButton("Ajustar")
        toolbar.addWidget(self.zoom_out_btn)
        toolbar.addWidget(self.zoom_in_btn)
        toolbar.addWidget(self.fit_btn)

        self.layout.addLayout(toolbar)

        self.info = QLabel("")
        self.info.setStyleSheet("font-size:11px;color:#59616d;")
        self.info.setMaximumHeight(18)
        self.layout.addWidget(self.info)

        # Tooltips preservam a descrição completa sem ocupar altura.
        self.use_btn.setToolTip("Carregar Pixel Art aprovada")
        self.save_area_btn.setToolTip("Criar área + gerar paleta")
        self.clear_btn.setToolTip("Limpar seleção atual")
        self.all_btn.setToolTip("Selecionar imagem inteira")
        self.pick_btn.setToolTip(
            "Selecionar ou remover uma cor essencial clicando diretamente na imagem"
        )
        self.brush.setToolTip("Tamanho do pincel para selecionar regiões")
        self.erase.setToolTip("Apagar partes da seleção atual")
        self.limit.setToolTip("Quantidade máxima de grupos de cor por área")
        self.threshold.setToolTip("Tolerância para agrupar nuances parecidas")
        self.zoom_out_btn.setToolTip("Diminuir zoom")
        self.zoom_in_btn.setToolTip("Aumentar zoom")
        self.fit_btn.setToolTip("Mostrar a imagem inteira")

        # --------------------------------------------------------------
        # Área principal: exatamente imagem x paletas
        # --------------------------------------------------------------
        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        self.layout.addWidget(split,1)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0,0,5,0)
        ll.setSpacing(4)

        left_head = QHBoxLayout()
        image_title = QLabel("IMAGEM + SELEÇÃO")
        image_title.setStyleSheet("font-size:17px;font-weight:700;")
        left_head.addWidget(image_title)
        left_head.addStretch(1)

        self.zoom_help = QLabel("Roda: zoom • Meio/Shift+arrastar: mover")
        self.zoom_help.setStyleSheet("font-size:11px;color:#6b737d;")
        self.zoom_help.setToolTip(
            "Use a roda do mouse sobre a região desejada para ampliar. "
            "Arraste com o botão do meio ou Shift + botão esquerdo para navegar."
        )
        left_head.addWidget(self.zoom_help)
        ll.addLayout(left_head)

        self.canvas = MaskCanvas()
        ll.addWidget(self.canvas,1)

        self.stats = QLabel("Seleção atual: 0%")
        self.stats.setStyleSheet("font-size:11px;color:#59616d;")
        self.stats.setMaximumHeight(20)
        ll.addWidget(self.stats)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(5,0,0,0)
        rl.setSpacing(4)

        right_head = QHBoxLayout()
        h = QLabel("PALETAS + ESSENCIAIS")
        h.setStyleSheet("font-size:17px;font-weight:700;")
        right_head.addWidget(h)
        right_head.addStretch(1)

        export_label = QLabel("Exportar:")
        export_label.setStyleSheet("font-size:11px;color:#606873;")
        right_head.addWidget(export_label)

        self.export_json_btn = QPushButton("JSON")
        self.export_csv_btn = QPushButton("CSV")
        self.export_txt_btn = QPushButton("TXT")
        for b in [self.export_json_btn,self.export_csv_btn,self.export_txt_btn]:
            b.setMaximumWidth(58)
            right_head.addWidget(b)
        rl.addLayout(right_head)

        self.sections_container = QWidget()
        self.sections_layout = QVBoxLayout(self.sections_container)
        self.sections_layout.setContentsMargins(4,4,4,4)
        self.sections_layout.setSpacing(8)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.sections_container)
        rl.addWidget(self.scroll,1)

        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0,1)
        split.setStretchFactor(1,1)
        split.setSizes([750,750])

        # --------------------------------------------------------------
        # Signals
        # --------------------------------------------------------------
        self.use_btn.clicked.connect(self.load_approved_image)
        self.save_area_btn.clicked.connect(self.create_area)
        self.clear_btn.clicked.connect(self.canvas.clear_working)
        self.all_btn.clicked.connect(self.canvas.select_all_working)

        self.pick_btn.toggled.connect(self.toggle_pick_mode)
        self.canvas.colorClicked.connect(self.pick_color_from_image)

        self.zoom_out_btn.clicked.connect(self.canvas.zoom_out)
        self.zoom_in_btn.clicked.connect(self.canvas.zoom_in)
        self.fit_btn.clicked.connect(self.canvas.reset_view)

        self.brush.valueChanged.connect(self.canvas.set_brush_size)
        self.erase.toggled.connect(self.canvas.set_erase)
        self.canvas.selectionChanged.connect(self.update_stats)

        self.limit.valueChanged.connect(self.settings_changed)
        self.threshold.valueChanged.connect(self.settings_changed)

        self.export_json_btn.clicked.connect(self.export_json)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_txt_btn.clicked.connect(self.export_txt)

        self.refresh()

    def set_context(self, state, workspace):
        self.state = state
        self.workspace = workspace
        self.limit.setValue(workspace.limit)
        self.threshold.setValue(workspace.threshold)
        self.refresh()

    def settings_changed(self):
        self.workspace.limit = self.limit.value()
        self.workspace.threshold = self.threshold.value()
        self.sync()

    def sync(self):
        self.state.metadata["palette_workspace"] = self.workspace.to_state_dict()
        self.state.dirty = True
        self.state.unapprove("palette")

        # Áreas/paletas/essenciais influenciam a simplificação, mas NÃO alteram
        # a geometria da matriz 100×100. Portanto, uma revisão de cores não deve
        # apagar nem desaprovar uma matriz já validada.
        for key in ["simplification", "manual", "pattern", "export"]:
            self.state.unapprove(key)
        self.state.simplified_image_path = None
        self.state.edited_matrix_path = None
        self.state.pattern_image_path = None
        for key in [
            "simplified_png", "simplified_50_png", "final_palette_50",
            "final_essential_colors", "simplification_input_signature",
            "simplification_method", "simplification_removed_colors",
            "edited_matrix_png", "edited_100x100_png", "manual_source_signature",
            "pattern_generated", "pattern_source_signature", "pattern_entries",
            "export_manifest", "export_source_signature",
        ]:
            self.state.metadata.pop(key, None)

        self.workspaceChanged.emit()

    # ------------------------------------------------------------------
    # Image
    # ------------------------------------------------------------------
    def load_approved_image(self):
        path = self.state.metadata.get("chat_matrix_art_path") or self.state.ai_image_path or self.state.source_image_path
        if not path or not Path(path).exists():
            QMessageBox.information(
                self,
                "Sem base artística",
                "A etapa 1 precisa possuir uma base artística importada."
            )
            return

        if (
            self.workspace.image_path and
            Path(self.workspace.image_path) != Path(path) and
            self.workspace.areas
        ):
            ans = QMessageBox.question(
                self,
                "Imagem alterada",
                "A imagem enquadrada é diferente da usada nas áreas atuais. "
                "Limpar todas as áreas e carregar a nova imagem?"
            )
            if ans != QMessageBox.Yes:
                return
            self.workspace.clear()

        self.workspace.image_path = path
        self.image = Image.open(path).convert("RGB")
        self.canvas.set_image(self.image)
        self.rebuild_sections()
        self.update_stats()
        self.sync()

    def refresh(self):
        desired = self.state.metadata.get("chat_matrix_art_path") or self.state.ai_image_path or self.state.source_image_path
        if desired and Path(desired).exists():
            try:
                if self.workspace.image_path and Path(self.workspace.image_path) != Path(desired):
                    self.workspace.clear()
                self.workspace.image_path = desired
                self.image = Image.open(desired).convert("RGB")
                self.canvas.set_image(self.image)
            except Exception:
                self.image = None
        else:
            self.image = None

        self.rebuild_sections()
        self.update_stats()

    def update_stats(self):
        frac = self.canvas.working_fraction() * 100
        n = len(self.canvas.selected_pixels())
        self.stats.setText(
            f"Seleção atual: {frac:.2f}% • {n:,} pixels • Zoom: {self.canvas.zoom_percent()}%"
        )

    # ------------------------------------------------------------------
    # Area creation / management
    # ------------------------------------------------------------------
    def create_area(self):
        if self.image is None:
            self.load_approved_image()
            if self.image is None:
                return

        mask = self.canvas.get_working_mask()
        if mask is None or not mask.any():
            QMessageBox.information(
                self,
                "Sem seleção",
                "Pinte uma região antes de criar a área."
            )
            return

        self.workspace.area_counter += 1
        default = f"Área selecionada {self.workspace.area_counter}"
        name, ok = QInputDialog.getText(
            self,
            "Nome da área",
            "Nome da área:",
            text=default
        )
        if not ok:
            self.workspace.area_counter -= 1
            return

        name = name.strip() or default
        pixels = self.canvas.selected_pixels(mask)

        palette = grouped_colors_from_pixels(
            pixels,
            limit=self.limit.value(),
            delta_e_threshold=self.threshold.value()
        )

        self.workspace.areas.append({
            "id": self.workspace.area_counter,
            "name": name,
            "mask": mask.copy(),
            "pixel_count": len(pixels),
            "palette": palette,
            "selected": {},
            "expanded": True,
        })

        self.canvas.clear_working()
        self.rebuild_sections()
        self.sync()

    def recalc_area(self, area):
        pixels = self.canvas.selected_pixels(area["mask"])
        area["palette"] = grouped_colors_from_pixels(
            pixels,
            limit=self.limit.value(),
            delta_e_threshold=self.threshold.value()
        )

        new_rgbs = {x.rgb for x in area["palette"]}
        area["selected"] = {
            rgb:item
            for rgb,item in area.get("selected",{}).items()
            if rgb in new_rgbs
        }

        self.rebuild_sections()
        self.sync()

    def delete_palette(self, area):
        ans = QMessageBox.question(
            self,
            "Excluir paleta",
            f"Excluir somente a paleta de “{area['name']}”?\n"
            "A região será mantida."
        )
        if ans != QMessageBox.Yes:
            return

        area["palette"] = []
        area["selected"] = {}
        self.canvas.clear_color_hover()
        self.rebuild_sections()
        self.sync()

    def delete_area(self, area):
        ans = QMessageBox.question(
            self,
            "Excluir área",
            f"Excluir “{area['name']}” e toda a sua paleta?"
        )
        if ans != QMessageBox.Yes:
            return

        self.workspace.areas = [
            a for a in self.workspace.areas
            if a["id"] != area["id"]
        ]

        self.canvas.set_hover_area_mask(None)
        self.canvas.clear_color_hover()
        self.rebuild_sections()
        self.sync()

    # ------------------------------------------------------------------
    # Essential colors
    # ------------------------------------------------------------------
    def toggle_pick_mode(self, enabled):
        self.canvas.set_pick_mode(enabled)
        self.pick_btn.setText(
            "✓ Seleção por imagem"
            if enabled
            else "Selecionar cor"
        )

        if enabled:
            self.pick_btn.setToolTip(
                "Modo ativo: clique em um pixel dentro de uma área salva "
                "para marcar/desmarcar a cor correspondente como essencial"
            )
        else:
            self.pick_btn.setToolTip(
                "Selecionar ou remover uma cor essencial clicando diretamente na imagem"
            )

    def toggle_area_color(self, area, item, state):
        if state:
            area["selected"][item.rgb] = item
        else:
            area["selected"].pop(item.rgb, None)

        self.rebuild_sections()
        self.sync()

    def _nearest_palette_item(self, area, rgb):
        palette = area.get("palette", [])
        if not palette:
            return None

        source = np.array(rgb, dtype=float).reshape(1,1,3) / 255.0
        source_lab = rgb2lab(source).reshape(3)

        prgb = np.array([x.rgb for x in palette], dtype=float) / 255.0
        plab = rgb2lab(prgb.reshape(1,-1,3)).reshape(-1,3)
        d = np.linalg.norm(plab - source_lab, axis=1)

        return palette[int(np.argmin(d))]

    def pick_color_from_image(self, x, y, rgb):
        matches = []

        # Latest area wins if masks overlap.
        for area in reversed(self.workspace.areas):
            m = area["mask"]
            if (
                m is not None and
                0 <= y < m.shape[0] and
                0 <= x < m.shape[1] and
                m[y,x]
            ):
                matches.append(area)

        if not matches:
            self.info.setText(
                f"RGB{rgb}: esse ponto não pertence a nenhuma área salva."
            )
            return

        area = matches[0]
        item = self._nearest_palette_item(area, rgb)

        if item is None:
            self.info.setText(
                f"A área “{area['name']}” não possui paleta."
            )
            return

        if item.rgb in area["selected"]:
            area["selected"].pop(item.rgb, None)
            action = "removida"
        else:
            area["selected"][item.rgb] = item
            action = "marcada"

        self.info.setText(
            f'{area["name"]}: pixel RGB{rgb} → {item.hex} / RGB{item.rgb} '
            f'{action} como essencial.'
        )

        self.rebuild_sections()
        self.sync()

    def remove_global_rgb(self, rgb):
        rgb = tuple(rgb)
        removed_from = []

        for area in self.workspace.areas:
            if rgb in area.get("selected", {}):
                area["selected"].pop(rgb, None)
                removed_from.append(area["name"])

        if removed_from:
            self.info.setText(
                f'RGB{rgb} removido das cores essenciais. '
                f'Áreas afetadas: {", ".join(removed_from)}.'
            )

        self.canvas.clear_color_hover()
        self.rebuild_sections()
        self.sync()

    # ------------------------------------------------------------------
    # Hover
    # ------------------------------------------------------------------
    def hover_color(self, area, item):
        radius = max(8.0, self.threshold.value() * 4.5)
        self.canvas.set_color_hover(
            item.rgb,
            area["mask"],
            radius
        )

    def hover_global_color(self, entry):
        rgb = tuple(entry["rgb"])

        union = None
        for area in self.workspace.areas:
            if rgb in area.get("selected", {}):
                m = area["mask"].astype(bool)
                union = m.copy() if union is None else (union | m)

        if union is None:
            return

        radius = max(8.0, self.threshold.value() * 4.5)
        self.canvas.set_color_hover(
            rgb,
            union.astype(np.uint8),
            radius
        )

    # ------------------------------------------------------------------
    # UI rebuild
    # ------------------------------------------------------------------
    def rebuild_sections(self):
        while self.sections_layout.count():
            item = self.sections_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        global_panel = GlobalEssentialPanel(self.workspace)
        global_panel.removeRequested.connect(self.remove_global_rgb)
        global_panel.hovered.connect(self.hover_global_color)
        global_panel.hoverLeft.connect(self.canvas.clear_color_hover)
        self.sections_layout.addWidget(global_panel)

        areas_title = QLabel("ÁREAS E PALETAS")
        areas_title.setStyleSheet(
            "font-size:16px;font-weight:700;margin-top:8px;"
        )
        self.sections_layout.addWidget(areas_title)

        if not self.workspace.areas:
            empty = QLabel(
                "Nenhuma área criada. Selecione uma região na imagem "
                "e clique em “Criar área”."
            )
            empty.setWordWrap(True)
            empty.setStyleSheet("color:#707780;padding:8px;")
            self.sections_layout.addWidget(empty)

        for area in self.workspace.areas:
            sec = AreaSection(
                area,
                selectable=True,
                manageable=True
            )

            sec.hoverIn.connect(
                lambda a:self.canvas.set_hover_area_mask(a["mask"])
            )
            sec.hoverOut.connect(
                lambda:self.canvas.set_hover_area_mask(None)
            )

            sec.colorToggled.connect(self.toggle_area_color)
            sec.colorHover.connect(self.hover_color)
            sec.colorHoverOut.connect(self.canvas.clear_color_hover)

            sec.deletePaletteRequested.connect(self.delete_palette)
            sec.deleteAreaRequested.connect(self.delete_area)
            sec.recalcRequested.connect(self.recalc_area)

            self.sections_layout.addWidget(sec)

        self.sections_layout.addStretch(1)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _export_rows(self):
        rows = []
        for area in self.workspace.areas:
            for item in area.get("selected",{}).values():
                rows.append({
                    "area": area["name"],
                    "code": item.code,
                    "hex": item.hex,
                    "rgb": list(item.rgb),
                    "count_in_area": item.count,
                    "percent_in_area": item.percent,
                    "grouped_nuances": item.member_count,
                })
        return rows

    def _ensure_rows(self):
        rows = self._export_rows()
        if not rows:
            QMessageBox.information(
                self,
                "Nada selecionado",
                "Selecione pelo menos uma cor essencial."
            )
            return None
        return rows

    def export_json(self):
        rows = self._ensure_rows()
        if rows is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar JSON",
            "cores_essenciais.json",
            "JSON (*.json)"
        )
        if not path:
            return

        Path(path).write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        QMessageBox.information(self, "Exportado", path)

    def export_csv(self):
        rows = self._ensure_rows()
        if rows is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar CSV",
            "cores_essenciais.csv",
            "CSV (*.csv)"
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([
                "area","code","hex","r","g","b",
                "count_in_area","percent_in_area","grouped_nuances"
            ])

            for row in rows:
                r,g,b = row["rgb"]
                w.writerow([
                    row["area"], row["code"], row["hex"], r, g, b,
                    row["count_in_area"],
                    f'{row["percent_in_area"]:.6f}',
                    row["grouped_nuances"]
                ])

        QMessageBox.information(self, "Exportado", path)

    def export_txt(self):
        rows = self._ensure_rows()
        if rows is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar TXT",
            "cores_essenciais.txt",
            "TXT (*.txt)"
        )
        if not path:
            return

        grouped = {}
        for row in rows:
            grouped.setdefault(row["area"], []).append(row)

        unique = {}
        for row in rows:
            unique.setdefault(tuple(row["rgb"]), row)

        lines = [
            "CORES ESSENCIAIS POR ÁREA",
            "="*60,
            ""
        ]

        for area_name, items in grouped.items():
            lines.append(f"[{area_name}]")
            for item in items:
                r,g,b = item["rgb"]
                lines.append(
                    f'{item["code"]} | {item["hex"]} | RGB({r}, {g}, {b})'
                )
            lines.append("")

        lines += [
            "",
            "CORES ESSENCIAIS CONSOLIDADAS (RGBs ÚNICOS)",
            "="*60
        ]
        for rgb,row in unique.items():
            r,g,b = rgb
            lines.append(
                f'{row["hex"]} | RGB({r}, {g}, {b})'
            )

        Path(path).write_text(
            "\n".join(lines),
            encoding="utf-8"
        )

        QMessageBox.information(self, "Exportado", path)

    # ------------------------------------------------------------------
    # Approval helpers
    # ------------------------------------------------------------------
    def unique_count(self):
        unique = set()
        for area in self.workspace.areas:
            unique.update(area.get("selected",{}).keys())
        return len(unique)

    def is_ready(self):
        # Esta etapa é opcional no novo fluxo de ponto cruz. Se houver áreas,
        # exige apenas que suas paletas tenham sido calculadas.
        if not self.workspace.areas:
            return True
        return all(a.get("palette") for a in self.workspace.areas)
