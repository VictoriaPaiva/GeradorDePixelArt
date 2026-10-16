
import csv
import json
from pathlib import Path
import numpy as np
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSlider, QSpinBox,
    QSplitter, QVBoxLayout, QWidget
)

from .palette_utils import grouped_predominant_colors, PaletteGroup
from .color_card import ColorCard


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Art Palette Selector v0.2")
        self.resize(1550, 920)

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

        top = QHBoxLayout()
        self.btn_open = QPushButton("Abrir imagem")
        self.btn_recalc = QPushButton("Recalcular paleta")
        self.btn_json = QPushButton("Exportar seleção JSON")
        self.btn_csv = QPushButton("Exportar seleção CSV")
        self.btn_clear = QPushButton("Limpar seleção")

        self.btn_open.clicked.connect(self.open_image)
        self.btn_recalc.clicked.connect(self.recalculate)
        self.btn_json.clicked.connect(self.export_json)
        self.btn_csv.clicked.connect(self.export_csv)
        self.btn_clear.clicked.connect(self.clear_selection)

        for b in [self.btn_open, self.btn_recalc, self.btn_json, self.btn_csv, self.btn_clear]:
            top.addWidget(b)

        top.addSpacing(12)
        top.addWidget(QLabel("Quantidade:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(20, 300)
        self.limit_spin.setValue(200)
        top.addWidget(self.limit_spin)

        top.addSpacing(12)
        top.addWidget(QLabel("Agrupamento de similares:"))
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(10, 80)  # 1.0 to 8.0
        self.threshold_slider.setValue(40)
        self.threshold_slider.setFixedWidth(180)
        self.threshold_slider.valueChanged.connect(self._threshold_changed)
        top.addWidget(self.threshold_slider)
        self.threshold_label = QLabel("4.0")
        top.addWidget(self.threshold_label)

        top.addStretch(1)
        self.status = QLabel("Nenhuma imagem carregada")
        top.addWidget(self.status)
        root.addLayout(top)

        help_text = QLabel(
            "Agrupamento baixo = apenas nuances quase idênticas são fundidas. "
            "Agrupamento alto = mais nuances são tratadas como a mesma cor. "
            "A cor exibida em cada cartão é um RGB real que existe na imagem."
        )
        help_text.setWordWrap(True)
        root.addWidget(help_text)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        # LEFT: image
        left = QWidget()
        left_l = QVBoxLayout(left)
        self.image_title = QLabel("IMAGEM ORIGINAL")
        self.image_title.setStyleSheet("font-size:18px;font-weight:700;")
        left_l.addWidget(self.image_title)

        self.image_label = QLabel("Abra uma imagem.")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background:#f4f4f4;border:1px solid #ccc;")
        self.image_label.setMinimumSize(450, 450)
        image_scroll = QScrollArea()
        image_scroll.setWidgetResizable(True)
        image_scroll.setWidget(self.image_label)
        left_l.addWidget(image_scroll, 1)

        self.active_label = QLabel("Cor ativa: nenhuma")
        left_l.addWidget(self.active_label)

        self.btn_highlight = QPushButton("Destacar cor ativa")
        self.btn_original = QPushButton("Mostrar imagem normal")
        self.btn_highlight.clicked.connect(self.highlight_active)
        self.btn_original.clicked.connect(self.show_original)
        row = QHBoxLayout()
        row.addWidget(self.btn_highlight)
        row.addWidget(self.btn_original)
        left_l.addLayout(row)

        # RIGHT: palette
        right = QWidget()
        right_l = QVBoxLayout(right)
        head = QHBoxLayout()
        title = QLabel("200 CORES PREDOMINANTES APÓS AGRUPAR NUANCES MUITO SIMILARES")
        title.setStyleSheet("font-size:18px;font-weight:700;")
        head.addWidget(title)
        head.addStretch(1)
        self.selected_label = QLabel("Selecionadas: 0")
        head.addWidget(self.selected_label)
        right_l.addLayout(head)

        note = QLabel(
            "Clique para marcar/desmarcar como essencial. "
            "Duplo clique define a cor ativa e destaca sua região na imagem."
        )
        note.setWordWrap(True)
        right_l.addWidget(note)

        self.palette_container = QWidget()
        self.grid = QGridLayout(self.palette_container)
        self.grid.setSpacing(8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.palette_container)
        right_l.addWidget(scroll, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([650, 900])

    def _threshold_changed(self, value):
        self.threshold_label.setText(f"{value/10:.1f}")

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir imagem", "", "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not path:
            return
        try:
            self.image_path = path
            self.pil_image = Image.open(path).convert("RGB")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
            return

        self.original_qpixmap = self._pil_to_pixmap(self.pil_image)
        self.show_original()
        self.recalculate()

    def recalculate(self):
        if self.pil_image is None:
            return

        self.status.setText("Calculando paleta...")
        self.selected.clear()
        self.active_color = None
        self.update_selected_label()

        limit = self.limit_spin.value()
        threshold = self.threshold_slider.value() / 10.0

        try:
            self.palette = grouped_predominant_colors(
                self.pil_image,
                limit=limit,
                delta_e_threshold=threshold
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro no cálculo", str(e))
            self.status.setText("Erro")
            return

        self.populate()
        self.status.setText(
            f"{Path(self.image_path).name} • {self.pil_image.width}×{self.pil_image.height} • "
            f"{len(self.palette)} grupos exibidos • tolerância {threshold:.1f}"
        )

    def populate(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.cards.clear()
        cols = 4
        for i, item in enumerate(self.palette):
            card = ColorCard(item)
            card.toggled.connect(self.on_toggle)
            card.activated.connect(self.on_activate)
            self.cards[item.rgb] = card
            self.grid.addWidget(card, i // cols, i % cols)

    def on_toggle(self, item: PaletteGroup, selected: bool):
        if selected:
            self.selected[item.rgb] = item
        else:
            self.selected.pop(item.rgb, None)
        self.update_selected_label()

    def on_activate(self, item: PaletteGroup):
        self.active_color = item
        self.active_label.setText(
            f"Cor ativa: {item.code} • {item.hex} • RGB {item.rgb} • "
            f"{item.member_count} nuances agrupadas"
        )
        self.highlight_active()

    def clear_selection(self):
        self.selected.clear()
        for c in self.cards.values():
            c.selected = False
            c.update_style()
        self.update_selected_label()

    def update_selected_label(self):
        self.selected_label.setText(f"Selecionadas: {len(self.selected)}")

    def show_original(self):
        if self.original_qpixmap:
            self._show_pixmap(self.original_qpixmap)

    def highlight_active(self):
        if self.pil_image is None or self.active_color is None:
            return

        arr = np.array(self.pil_image)
        rep = np.array(self.active_color.rgb, dtype=np.int16)

        # Highlight pixels perceptually close in RGB to representative.
        # This is intentionally only a visualization aid; it does not alter the image data.
        diff = arr.astype(np.int16) - rep
        dist = np.sqrt((diff * diff).sum(axis=2))
        radius = max(6.0, self.threshold_slider.value() / 10.0 * 4.5)
        mask = dist <= radius

        out = arr.astype(np.float32)
        out[~mask] *= 0.22
        out = np.clip(out, 0, 255).astype(np.uint8)
        out[mask] = np.array([255, 0, 255], dtype=np.uint8)

        self._show_pixmap(self._pil_to_pixmap(Image.fromarray(out)))

    def export_json(self):
        if not self.selected:
            QMessageBox.information(self, "Nada selecionado", "Selecione pelo menos uma cor.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar seleção", "cores_essenciais.json", "JSON (*.json)"
        )
        if not path:
            return
        data = [
            {
                "code": i.code,
                "hex": i.hex,
                "rgb": list(i.rgb),
                "count": i.count,
                "percent": i.percent,
                "grouped_nuances": i.member_count,
            }
            for i in self.selected.values()
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        QMessageBox.information(self, "Exportado", path)

    def export_csv(self):
        if not self.selected:
            QMessageBox.information(self, "Nada selecionado", "Selecione pelo menos uma cor.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar seleção", "cores_essenciais.csv", "CSV (*.csv)"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["code","hex","r","g","b","count","percent","grouped_nuances"])
            for i in self.selected.values():
                w.writerow([
                    i.code, i.hex, *i.rgb, i.count,
                    f"{i.percent:.6f}", i.member_count
                ])
        QMessageBox.information(self, "Exportado", path)

    def _pil_to_pixmap(self, image):
        image = image.convert("RGB")
        data = image.tobytes("raw", "RGB")
        q = QImage(data, image.width, image.height, image.width*3, QImage.Format_RGB888)
        return QPixmap.fromImage(q.copy())

    def _show_pixmap(self, pixmap):
        target = self.image_label.size()
        scaled = pixmap.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
