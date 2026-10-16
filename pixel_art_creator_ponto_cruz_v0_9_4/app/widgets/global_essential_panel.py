import numpy as np
from skimage.color import rgb2lab

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QGridLayout, QPushButton, QScrollArea
)


def _rgb_to_lab(rgb):
    arr = np.array(rgb, dtype=float).reshape(1, 1, 3) / 255.0
    return rgb2lab(arr).reshape(3)


def _sort_by_similarity(entries):
    """Nearest-neighbour path in Lab so similar colors appear side by side."""
    if len(entries) <= 2:
        return list(entries)

    labs = np.array([_rgb_to_lab(e["rgb"]) for e in entries])
    start = int(np.argmin(labs[:, 0]))
    remaining = set(range(len(entries)))
    order = [start]
    remaining.remove(start)
    current = start

    while remaining:
        rem = sorted(remaining)
        diff = labs[rem] - labs[current]
        d2 = np.sum(diff * diff, axis=1)
        nxt = rem[int(np.argmin(d2))]
        order.append(nxt)
        remaining.remove(nxt)
        current = nxt

    return [entries[i] for i in order]


class ColorBlock(QWidget):
    def __init__(self, rgb):
        super().__init__()
        self.rgb = tuple(rgb)
        self.setFixedHeight(38)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(*self.rgb))
        p.setPen(QPen(QColor(55, 55, 55), 1))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))


class EssentialTile(QFrame):
    removeRequested = Signal(object)
    hovered = Signal(object)
    hoverLeft = Signal()

    def __init__(self, entry, index):
        super().__init__()
        self.entry = entry
        self.setMouseTracking(True)
        self.setFixedSize(108, 98)
        self.setStyleSheet("""
            QFrame {
                background:white;
                border:1px solid #cfd5dd;
                border-radius:7px;
            }
            QFrame:hover {
                border:2px solid #2b7de9;
                background:#f8fbff;
            }
            QLabel {border:none;background:transparent;}
            QPushButton {
                border:none;
                background:#fff0f0;
                color:#9b1c1c;
                border-radius:7px;
                font-weight:700;
            }
            QPushButton:hover {background:#ffdede;}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(5, 5, 5, 5)
        root.setSpacing(3)

        top = QHBoxLayout()
        idx = QLabel(f"{index+1:02d}")
        idx.setStyleSheet("font-weight:700;color:#4d5662;")
        top.addWidget(idx)
        top.addStretch(1)
        remove = QPushButton("×")
        remove.setFixedSize(22, 22)
        remove.setToolTip("Remover esta cor do conjunto de essenciais")
        remove.clicked.connect(lambda: self.removeRequested.emit(self.entry["rgb"]))
        top.addWidget(remove)
        root.addLayout(top)

        root.addWidget(ColorBlock(entry["rgb"]))

        hx = QLabel(entry["hex"])
        hx.setAlignment(Qt.AlignCenter)
        hx.setStyleSheet("font-weight:700;")
        root.addWidget(hx)

        areas = ", ".join(entry["areas"])
        d = entry.get("nearest_delta")
        near = entry.get("nearest_hex")
        tip = [
            f"RGB {entry['rgb']}",
            f"Áreas: {areas}",
        ]
        if near and d is not None:
            tip.append(f"Cor essencial mais próxima: {near} • ΔE {d:.1f}")
            if d <= 6:
                tip.append("Muito semelhante a outra essencial; vale avaliar redundância.")
        self.setToolTip("\n".join(tip))

    def enterEvent(self, event):
        self.hovered.emit(self.entry)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hoverLeft.emit()
        super().leaveEvent(event)


class GlobalEssentialPanel(QFrame):
    removeRequested = Signal(object)
    hovered = Signal(object)
    hoverLeft = Signal()

    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace

        self.setStyleSheet("""
            GlobalEssentialPanel {
                background:#f8fbff;
                border:1px solid #afcdeb;
                border-radius:10px;
            }
        """)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(9, 9, 9, 9)
        self.root.setSpacing(5)

        title = QLabel("★ CORES ESSENCIAIS CONSOLIDADAS")
        title.setStyleSheet(
            "font-size:15px;font-weight:700;color:#155a9c;border:none;"
        )
        self.root.addWidget(title)

        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet("font-size:11px;border:none;color:#4e5966;")
        self.root.addWidget(self.summary)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setMinimumHeight(118)
        self.scroll.setMaximumHeight(232)
        self.root.addWidget(self.scroll)

        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setContentsMargins(0, 2, 0, 2)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(6)
        self.scroll.setWidget(self.grid_widget)

        self.rebuild()

    def set_workspace(self, workspace):
        self.workspace = workspace
        self.rebuild()

    def _entries(self):
        combined = {}
        selections = 0

        for area in self.workspace.areas:
            for rgb, item in area.get("selected", {}).items():
                rgb = tuple(rgb)
                selections += 1
                if rgb not in combined:
                    combined[rgb] = {
                        "rgb": rgb,
                        "hex": "#{:02X}{:02X}{:02X}".format(*rgb),
                        "areas": [],
                        "item": item,
                    }
                if area["name"] not in combined[rgb]["areas"]:
                    combined[rgb]["areas"].append(area["name"])

        entries = list(combined.values())

        if len(entries) > 1:
            labs = np.array([_rgb_to_lab(e["rgb"]) for e in entries])
            for i, e in enumerate(entries):
                d = np.linalg.norm(labs - labs[i], axis=1)
                d[i] = np.inf
                j = int(np.argmin(d))
                e["nearest_delta"] = float(d[j])
                e["nearest_hex"] = entries[j]["hex"]
        else:
            for e in entries:
                e["nearest_delta"] = None
                e["nearest_hex"] = None

        entries = _sort_by_similarity(entries)
        return entries, selections

    def rebuild(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        entries, selections = self._entries()

        very_close = sum(
            1 for e in entries
            if e.get("nearest_delta") is not None and e["nearest_delta"] <= 6
        )

        self.summary.setText(
            f"Seleções por área: {selections} • RGBs únicos: {len(entries)} • "
            f"{very_close} cor(es) com outra essencial muito próxima. "
            "As cores são ordenadas por similaridade visual; passe o mouse para ver áreas e ΔE."
        )

        if not entries:
            empty = QLabel(
                "Nenhuma cor essencial selecionada ainda. "
                "Selecione cores nas paletas das áreas abaixo."
            )
            empty.setWordWrap(True)
            empty.setStyleSheet("color:#747b84;padding:8px;border:none;")
            self.grid.addWidget(empty, 0, 0)
            return

        cols = 6
        for i, entry in enumerate(entries):
            card = EssentialTile(entry, i)
            card.removeRequested.connect(self.removeRequested.emit)
            card.hovered.connect(self.hovered.emit)
            card.hoverLeft.connect(self.hoverLeft.emit)
            self.grid.addWidget(card, i // cols, i % cols)
