from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout,
    QScrollArea
)

from ..simplification_service import sort_palette_by_similarity


class Swatch(QWidget):
    clicked = Signal(object)

    def __init__(self, rgb, essential=False, index=0):
        super().__init__()
        self.rgb = tuple(rgb)
        self.essential = bool(essential)
        self.index = index
        self.marked = False
        self.setFixedSize(82, 62)
        self.setCursor(Qt.PointingHandCursor if not self.essential else Qt.ArrowCursor)
        self._refresh_tooltip()

    def _refresh_tooltip(self):
        role = "ESSENCIAL (protegida)" if self.essential else "complementar"
        TEMP
        self.setToolTip(
            f"{self.index+1:02d} • RGB {self.rgb} • {role}{action}"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.essential:
            self.clicked.emit(self.rgb)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect().adjusted(3, 3, -3, -15), QColor(*self.rgb))

        border = QColor("#1677d2") if self.essential else QColor("#555")
        width = 3 if self.essential else 1
        if self.marked:
            border = QColor("#d83b01")
            width = 3

        p.setPen(QPen(border, width))
        p.drawRect(self.rect().adjusted(3, 3, -4, -16))

        if self.essential:
            p.setPen(QColor("white"))
            p.drawText(
                self.rect().adjusted(6, 6, -6, -18),
                Qt.AlignTop | Qt.AlignRight,
                "★"
            )

        if self.marked:
            p.setPen(QColor("white"))
            p.drawText(
                self.rect().adjusted(6, 6, -6, -18),
                Qt.AlignTop | Qt.AlignLeft,
                "×"
            )

        p.setPen(QColor("#1f2329"))
        p.drawText(
            self.rect().adjusted(0, 46, 0, 0),
            Qt.AlignHCenter | Qt.AlignTop,
            f"{self.index+1:02d}"
        )


class FinalPalettePanel(QFrame):
    selectionChanged = Signal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background:#fbfcfe;
                border:1px solid #d6dce5;
                border-radius:8px;
            }
            QLabel {
                border:none;
                background:transparent;
            }
        """)

        self.palette = []
        self.essential = []
        self.selected_removals = set()
        self.swatches = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(8,6,8,6)
        root.setSpacing(4)

        self.title = QLabel("PALETA FINAL")
        self.title.setStyleSheet("font-weight:700;")
        root.addWidget(self.title)

        self.hint = QLabel(
            "As cores são exibidas em ordem de similaridade. "
            "Clique nas cores complementares que deseja remover para recriar "
            "uma paleta menos redundante."
        )
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("font-size:11px;color:#59616d;")
        root.addWidget(self.hint)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(self.scroll)

        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setContentsMargins(0,0,0,0)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(6)
        self.scroll.setWidget(self.grid_widget)

        self.summary = QLabel("")
        self.summary.setStyleSheet("font-size:11px;color:#59616d;")
        root.addWidget(self.summary)

    def set_palette(self, palette, essential):
        self.palette = [tuple(c) for c in palette]
        self.essential = [tuple(c) for c in essential]
        essential_set = set(self.essential)

        keep = set(self.palette)
        self.selected_removals = {
            tuple(c) for c in self.selected_removals if tuple(c) in keep and tuple(c) not in essential_set
        }

        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.swatches = {}
        ordered = sort_palette_by_similarity(self.palette)
        cols = 10

        for i, rgb in enumerate(ordered):
            sw = Swatch(
                rgb,
                essential=tuple(rgb) in essential_set,
                index=i
            )
            sw.marked = tuple(rgb) in self.selected_removals
            sw.clicked.connect(self.toggle_removal)
            self.swatches[tuple(rgb)] = sw
            self.grid.addWidget(sw, i // cols, i % cols)

        self._refresh_summary()

    def toggle_removal(self, rgb):
        rgb = tuple(rgb)
        if rgb in set(self.essential):
            return
        if rgb in self.selected_removals:
            self.selected_removals.remove(rgb)
        else:
            self.selected_removals.add(rgb)
        if rgb in self.swatches:
            self.swatches[rgb].marked = rgb in self.selected_removals
            self.swatches[rgb].update()
        self._refresh_summary()
        self.selectionChanged.emit()

    def clear_selection(self):
        if not self.selected_removals:
            return
        self.selected_removals.clear()
        for sw in self.swatches.values():
            sw.marked = False
            sw.update()
        self._refresh_summary()
        self.selectionChanged.emit()

    def selected_colors(self):
        return [rgb for rgb in self.palette if tuple(rgb) in self.selected_removals]

    def selected_count(self):
        return len(self.selected_removals)

    def _refresh_summary(self):
        essential_set = {tuple(c) for c in self.essential}
        self.summary.setText(
            f"{len(self.palette)} cores finais • "
            f"{len(essential_set)} essenciais protegidas (★) • "
            f"{max(0, len(self.palette)-len(essential_set))} complementares • "
            f"{len(self.selected_removals)} marcadas para remover"
        )
