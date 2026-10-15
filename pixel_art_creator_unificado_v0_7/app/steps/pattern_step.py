import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)

from .base_step import BaseStep
from ..widgets.pil_preview import PilPreview
from ..simplification_service import decode_png
from ..pattern_utils import (
    build_legend, validate_matrix, render_code_pattern, render_legend
)


class PatternStep(BaseStep):
    def __init__(self, state):
        super().__init__(
            "7. Molde e legenda",
            "Gere o molde codificado e a legenda diretamente da matriz final 100×100."
        )

        self.state = state
        self.arr = None
        self.entries = []
        self.color_to_code = {}
        self.pattern_img = None
        self.legend_img = None

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

        toolbar = QHBoxLayout()

        self.generate_btn = QPushButton("Gerar molde + legenda")
        self.generate_btn.setToolTip(
            "Gerar códigos, molde com grade e legenda a partir da matriz final 100×100"
        )

        self.save_pattern_btn = QPushButton("Salvar molde")
        self.save_pattern_btn.setToolTip("Salvar PNG do molde com códigos e numeração")

        self.save_legend_btn = QPushButton("Salvar legenda PNG")
        self.save_legend_btn.setToolTip("Salvar PNG da legenda de cores")

        self.export_json_btn = QPushButton("JSON")
        self.export_csv_btn = QPushButton("CSV")
        self.export_txt_btn = QPushButton("TXT")

        toolbar.addWidget(self.generate_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.save_pattern_btn)
        toolbar.addWidget(self.save_legend_btn)
        toolbar.addWidget(QLabel("Legenda:"))
        toolbar.addWidget(self.export_json_btn)
        toolbar.addWidget(self.export_csv_btn)
        toolbar.addWidget(self.export_txt_btn)

        self.layout.addLayout(toolbar)

        self.info = QLabel(
            "Códigos: A…Z, Aa, Ab… • cada célula recebe o código da sua cor • "
            "linhas e colunas são numeradas de 1 a 100 • a legenda mostra HEX, RGB, quantidade e percentual."
        )
        self.info.setWordWrap(True)
        self.info.setStyleSheet("font-size:11px;color:#59616d;")
        self.layout.addWidget(self.info)

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        self.layout.addWidget(split, 1)

        # Left: pattern preview
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0,0,5,0)
        ll.setSpacing(4)

        title_left = QLabel("MOLDE COM CÓDIGOS")
        title_left.setStyleSheet("font-size:17px;font-weight:700;")
        ll.addWidget(title_left)

        self.preview = PilPreview("Clique em “Gerar molde + legenda”.")
        ll.addWidget(self.preview, 1)

        self.source_status = QLabel("")
        self.source_status.setStyleSheet("font-size:11px;color:#59616d;")
        self.source_status.setMaximumHeight(20)
        ll.addWidget(self.source_status)

        # Right: legend table
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(5,0,0,0)
        rl.setSpacing(4)

        title_right = QLabel("LEGENDA")
        title_right.setStyleSheet("font-size:17px;font-weight:700;")
        rl.addWidget(title_right)

        self.table = QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(
            ["Código","Cor","HEX","RGB","Células","%"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        rl.addWidget(self.table, 1)

        self.pattern_status = QLabel("Molde ainda não gerado.")
        self.pattern_status.setStyleSheet("font-size:11px;color:#59616d;")
        self.pattern_status.setMaximumHeight(20)
        rl.addWidget(self.pattern_status)

        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        split.setSizes([900,600])

        # Signals
        self.generate_btn.clicked.connect(self.generate)
        self.save_pattern_btn.clicked.connect(self.save_pattern)
        self.save_legend_btn.clicked.connect(self.save_legend)
        self.export_json_btn.clicked.connect(self.export_json)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_txt_btn.clicked.connect(self.export_txt)

        self.refresh()

    def set_context(self, state):
        self.state = state
        self.refresh()

    # ------------------------------------------------------------------
    # Source selection / signature
    # ------------------------------------------------------------------
    def _manual_source_valid(self):
        edited = self.state.metadata.get("edited_100x100_png")
        if not edited:
            return False

        simplified = self.state.metadata.get("simplified_50_png") or ""
        expected = hashlib.sha256(simplified.encode("ascii")).hexdigest()
        return (
            self.state.metadata.get("manual_source_signature") == expected
        )

    def _source_png(self):
        if self._manual_source_valid():
            return self.state.metadata.get("edited_100x100_png"), "edição manual"
        return self.state.metadata.get("simplified_50_png"), "simplificação 50 cores"

    def _source_signature(self):
        payload, _ = self._source_png()
        if not payload:
            return None
        return hashlib.sha256(payload.encode("ascii")).hexdigest()

    def refresh(self):
        payload, source_name = self._source_png()
        self.arr = decode_png(payload)

        if self.arr is None:
            self.source_status.setText("Sem matriz final 100×100 disponível.")
            self._clear_generated()
            return

        colors = len(np.unique(self.arr.reshape(-1,3), axis=0))
        self.source_status.setText(
            f"Fonte: {source_name} • 100×100 • {colors} cores"
        )

        stored_sig = self.state.metadata.get("pattern_source_signature")
        if stored_sig == self._source_signature() and self.state.metadata.get("pattern_generated"):
            self._generate_artifacts(persist=False)
        else:
            self._clear_generated()

    def _clear_generated(self):
        self.entries = []
        self.color_to_code = {}
        self.pattern_img = None
        self.legend_img = None
        self.preview.clear_preview("Clique em “Gerar molde + legenda”.")
        self.table.setRowCount(0)
        self.pattern_status.setText("Molde ainda não gerado.")
        self._refresh_actions()

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def generate(self):
        if self.arr is None:
            QMessageBox.information(
                self,
                "Sem matriz final",
                "Conclua e aprove a edição manual antes de gerar o molde."
            )
            return

        if not self.state.approvals.get("manual", False):
            QMessageBox.information(
                self,
                "Edição manual ainda não aprovada",
                "Aprove a etapa 6 antes de gerar o molde e a legenda."
            )
            return

        ok, msg = validate_matrix(self.arr)
        if not ok:
            QMessageBox.critical(self, "Matriz inválida", msg)
            return

        self._generate_artifacts(persist=True)

    def _generate_artifacts(self, persist=True):
        if self.arr is None:
            return

        self.entries, self.color_to_code = build_legend(self.arr)
        self.pattern_img = render_code_pattern(
            self.arr,
            self.color_to_code,
            cell_size=34
        )
        self.legend_img = render_legend(self.entries)

        self.populate_table()
        self.preview.set_pil(self.pattern_img)

        self.pattern_status.setText(
            f"100×100 • 10.000 células • {len(self.entries)} cores • "
            f"códigos {self.entries[0].code if self.entries else '—'}–{self.entries[-1].code if self.entries else '—'}"
        )

        if persist:
            self.state.metadata["pattern_generated"] = True
            self.state.metadata["pattern_source_signature"] = self._source_signature()
            self.state.metadata["pattern_entries"] = self._rows()
            self.state.unapprove("pattern")
            self.state.invalidate_after("pattern")
            self.state.dirty = True

        self._refresh_actions()

    def populate_table(self):
        self.table.setRowCount(len(self.entries))

        for r,e in enumerate(self.entries):
            self.table.setItem(r,0,QTableWidgetItem(e.code))

            color_item = QTableWidgetItem("")
            color_item.setBackground(QColor(*e.rgb))
            self.table.setItem(r,1,color_item)

            self.table.setItem(r,2,QTableWidgetItem(e.hex))
            self.table.setItem(r,3,QTableWidgetItem(str(e.rgb)))
            self.table.setItem(r,4,QTableWidgetItem(str(e.count)))
            self.table.setItem(r,5,QTableWidgetItem(f"{e.percent:.2f}%"))

    def _refresh_actions(self):
        ready = self.pattern_img is not None and bool(self.entries)
        for b in [
            self.save_pattern_btn,
            self.save_legend_btn,
            self.export_json_btn,
            self.export_csv_btn,
            self.export_txt_btn,
        ]:
            b.setEnabled(ready)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _ensure_generated(self):
        if self.pattern_img is None or not self.entries:
            QMessageBox.information(
                self,
                "Ainda não gerado",
                "Clique em “Gerar molde + legenda” primeiro."
            )
            return False
        return True

    def save_pattern(self):
        if not self._ensure_generated():
            return

        path,_ = QFileDialog.getSaveFileName(
            self,
            "Salvar molde",
            "molde_pixel_art_100x100.png",
            "PNG (*.png)"
        )
        if not path:
            return

        self.pattern_img.save(path)
        self.state.pattern_image_path = path
        self.state.dirty = True
        QMessageBox.information(self, "Molde salvo", path)

    def save_legend(self):
        if not self._ensure_generated():
            return

        path,_ = QFileDialog.getSaveFileName(
            self,
            "Salvar legenda",
            "legenda_cores.png",
            "PNG (*.png)"
        )
        if not path:
            return

        self.legend_img.save(path)
        self.state.metadata["legend_image_path"] = path
        self.state.dirty = True
        QMessageBox.information(self, "Legenda salva", path)

    def _rows(self):
        return [
            {
                "code":e.code,
                "hex":e.hex,
                "rgb":list(e.rgb),
                "cells":e.count,
                "percent":e.percent,
            }
            for e in self.entries
        ]

    def export_json(self):
        if not self._ensure_generated():
            return

        path,_ = QFileDialog.getSaveFileName(
            self,
            "Exportar JSON",
            "legenda_cores.json",
            "JSON (*.json)"
        )
        if not path:
            return

        Path(path).write_text(
            json.dumps(self._rows(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        QMessageBox.information(self, "JSON exportado", path)

    def export_csv(self):
        if not self._ensure_generated():
            return

        path,_ = QFileDialog.getSaveFileName(
            self,
            "Exportar CSV",
            "legenda_cores.csv",
            "CSV (*.csv)"
        )
        if not path:
            return

        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f)
            w.writerow(["code","hex","r","g","b","cells","percent"])
            for e in self.entries:
                w.writerow([
                    e.code,e.hex,*e.rgb,e.count,f"{e.percent:.6f}"
                ])

        QMessageBox.information(self, "CSV exportado", path)

    def export_txt(self):
        if not self._ensure_generated():
            return

        path,_ = QFileDialog.getSaveFileName(
            self,
            "Exportar TXT",
            "legenda_cores.txt",
            "TXT (*.txt)"
        )
        if not path:
            return

        lines=[
            "LEGENDA DE CORES",
            "="*60,
            "Matriz: 100x100",
            "Total de células: 10000",
            f"Total de cores: {len(self.entries)}",
            "",
        ]

        for e in self.entries:
            lines.append(
                f"{e.code} | {e.hex} | RGB{e.rgb} | "
                f"{e.count} células | {e.percent:.2f}%"
            )

        Path(path).write_text("\n".join(lines), encoding="utf-8")
        QMessageBox.information(self, "TXT exportado", path)

    def is_ready(self):
        return (
            self.arr is not None
            and self.arr.shape == (100,100,3)
            and self.pattern_img is not None
            and self.legend_img is not None
            and bool(self.entries)
            and self.state.metadata.get("pattern_source_signature") == self._source_signature()
        )
