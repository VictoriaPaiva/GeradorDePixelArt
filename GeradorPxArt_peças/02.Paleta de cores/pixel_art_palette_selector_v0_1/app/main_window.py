
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSplitter, QVBoxLayout, QWidget
)

from .palette_utils import top_exact_colors, PaletteColor
from .color_card import ColorCard
from .image_view import ImageView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Art Palette Selector v0.1")
        self.resize(1500, 900)

        self.image_path = None
        self.pil_image = None
        self.original_qpixmap = None
        self.palette = []
        self.selected = {}
        self.cards = {}
        self.active_color = None

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        self.btn_open = QPushButton("Abrir imagem")
        self.btn_export_json = QPushButton("Exportar selecionadas (JSON)")
        self.btn_export_csv = QPushButton("Exportar selecionadas (CSV)")
        self.btn_highlight = QPushButton("Destacar cor ativa")
        self.btn_clear_highlight = QPushButton("Limpar destaque")
        self.btn_clear_selected = QPushButton("Limpar seleção")

        self.btn_open.clicked.connect(self.open_image)
        self.btn_export_json.clicked.connect(self.export_json)
        self.btn_export_csv.clicked.connect(self.export_csv)
        self.btn_highlight.clicked.connect(self.highlight_active)
        self.btn_clear_highlight.clicked.connect(self.show_original)
        self.btn_clear_selected.clicked.connect(self.clear_selection)

        for b in [
            self.btn_open, self.btn_export_json, self.btn_export_csv,
            self.btn_highlight, self.btn_clear_highlight, self.btn_clear_selected
        ]:
            toolbar.addWidget(b)

        toolbar.addStretch(1)
        self.status_label = QLabel("Nenhuma imagem carregada")
        toolbar.addWidget(self.status_label)
        root.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        # LEFT
        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.image_title = QLabel("IMAGEM ORIGINAL")
        self.image_title.setStyleSheet("font-size:18px;font-weight:700;")
        left_layout.addWidget(self.image_title)
        self.image_view = ImageView()
        left_layout.addWidget(self.image_view, 1)
        self.active_label = QLabel("Cor ativa: nenhuma")
        self.active_label.setStyleSheet("font-size:14px;")
        left_layout.addWidget(self.active_label)

        # RIGHT
        right = QWidget()
        right_layout = QVBoxLayout(right)
        header = QHBoxLayout()
        title = QLabel("PALETA — 200 CORES RGB MAIS PREDOMINANTES")
        title.setStyleSheet("font-size:18px;font-weight:700;")
        header.addWidget(title)
        header.addStretch(1)
        self.selected_label = QLabel("Selecionadas: 0")
        header.addWidget(self.selected_label)
        right_layout.addLayout(header)

        help_label = QLabel(
            "Clique em um cartão para selecionar/desselecionar. "
            "Dê duplo clique para tornar a cor ativa e destacar sua localização na imagem."
        )
        help_label.setWordWrap(True)
        right_layout.addWidget(help_label)

        self.palette_container = QWidget()
        self.palette_grid = QGridLayout(self.palette_container)
        self.palette_grid.setSpacing(8)
        self.palette_grid.setContentsMargins(4, 4, 4, 4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.palette_container)
        right_layout.addWidget(scroll, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([620, 880])

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir imagem",
            "",
            "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not path:
            return

        try:
            self.image_path = path
            self.pil_image = Image.open(path).convert("RGB")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir a imagem:\n{e}")
            return

        self.original_qpixmap = self._pil_to_qpixmap(self.pil_image)
        self.show_original()

        self.palette = top_exact_colors(self.pil_image, 200)
        self.selected.clear()
        self.active_color = None
        self.populate_palette()

        self.status_label.setText(
            f"{Path(path).name}  •  {self.pil_image.width}×{self.pil_image.height}  •  "
            f"{len(self.palette)} cores exibidas"
        )
        self.active_label.setText("Cor ativa: nenhuma")
        self.update_selected_label()

    def populate_palette(self):
        while self.palette_grid.count():
            item = self.palette_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.cards.clear()

        # 4 columns works well on typical desktop widths.
        cols = 4
        for i, item in enumerate(self.palette):
            card = ColorCard(item)
            card.toggled.connect(self.on_color_toggled)
            card.activated.connect(self.on_color_activated)
            self.cards[item.rgb] = card
            self.palette_grid.addWidget(card, i // cols, i % cols)

        self.palette_grid.setRowStretch((len(self.palette) + cols - 1) // cols, 1)

    def on_color_toggled(self, item: PaletteColor, is_selected: bool):
        if is_selected:
            self.selected[item.rgb] = item
        else:
            self.selected.pop(item.rgb, None)
        self.update_selected_label()

    def on_color_activated(self, item: PaletteColor):
        self.active_color = item
        self.active_label.setText(
            f"Cor ativa: {item.code} • {item.hex} • RGB {item.rgb} • "
            f"{item.count:,} px ({item.percent:.3f}%)"
        )
        self.highlight_active()

    def update_selected_label(self):
        self.selected_label.setText(f"Selecionadas: {len(self.selected)}")

    def clear_selection(self):
        self.selected.clear()
        for card in self.cards.values():
            card.selected = False
            card.update_style()
        self.update_selected_label()

    def show_original(self):
        if self.original_qpixmap:
            self.image_view.set_pixmap(self.original_qpixmap)

    def highlight_active(self):
        if self.pil_image is None or self.active_color is None:
            return

        arr = np.array(self.pil_image)
        rgb = np.array(self.active_color.rgb, dtype=np.uint8)

        mask = np.all(arr == rgb, axis=2)

        # Darken everything not matching the active exact RGB.
        out = arr.astype(np.float32)
        out[~mask] *= 0.25

        # Matching pixels remain unchanged and get a magenta edge-ish boost around them.
        out = np.clip(out, 0, 255).astype(np.uint8)

        # Add high-contrast magenta overlay to matching pixels so tiny occurrences are visible.
        overlay = out.copy()
        overlay[mask] = np.array([255, 0, 255], dtype=np.uint8)

        pix = self._pil_to_qpixmap(Image.fromarray(overlay))
        self.image_view.set_pixmap(pix)

    def export_json(self):
        if not self.selected:
            QMessageBox.information(self, "Nada selecionado", "Selecione pelo menos uma cor.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar seleção",
            "cores_essenciais.json",
            "JSON (*.json)"
        )
        if not path:
            return

        data = [
            {
                "code": item.code,
                "hex": item.hex,
                "rgb": list(item.rgb),
                "count": item.count,
                "percent": item.percent,
            }
            for item in self.selected.values()
        ]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        QMessageBox.information(self, "Exportado", f"Arquivo salvo:\n{path}")

    def export_csv(self):
        if not self.selected:
            QMessageBox.information(self, "Nada selecionado", "Selecione pelo menos uma cor.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar seleção",
            "cores_essenciais.csv",
            "CSV (*.csv)"
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["code", "hex", "r", "g", "b", "count", "percent"])
            for item in self.selected.values():
                writer.writerow([
                    item.code, item.hex,
                    item.rgb[0], item.rgb[1], item.rgb[2],
                    item.count, f"{item.percent:.6f}"
                ])

        QMessageBox.information(self, "Exportado", f"Arquivo salvo:\n{path}")

    def _pil_to_qpixmap(self, image: Image.Image) -> QPixmap:
        rgb = image.convert("RGB")
        data = rgb.tobytes("raw", "RGB")
        qimg = QImage(data, rgb.width, rgb.height, rgb.width * 3, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg.copy())
