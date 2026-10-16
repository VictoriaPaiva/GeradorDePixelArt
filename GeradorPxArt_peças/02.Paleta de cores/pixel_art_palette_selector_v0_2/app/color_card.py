
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from .palette_utils import PaletteGroup


class Swatch(QWidget):
    def __init__(self, rgb, parent=None):
        super().__init__(parent)
        self.rgb = rgb
        self.setFixedSize(56, 56)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(*self.rgb))
        p.setPen(QPen(QColor(45, 45, 45), 1))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))


class ColorCard(QFrame):
    toggled = Signal(object, bool)
    activated = Signal(object)

    def __init__(self, item: PaletteGroup, parent=None):
        super().__init__(parent)
        self.item = item
        self.selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(82)

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)
        root.addWidget(Swatch(item.rgb))

        box = QVBoxLayout()
        box.setSpacing(1)

        title = QLabel(f"{item.code}   {item.hex}")
        title.setStyleSheet("font-weight:700;")
        rgb = QLabel(f"RGB {item.rgb}")
        stats = QLabel(f"{item.count:,} px • {item.percent:.3f}%")
        merged = QLabel(f"{item.member_count} nuances agrupadas")
        merged.setStyleSheet("color:#666;")

        box.addWidget(title)
        box.addWidget(rgb)
        box.addWidget(stats)
        box.addWidget(merged)
        root.addLayout(box, 1)
        self.update_style()

    def update_style(self):
        if self.selected:
            self.setStyleSheet("""
                QFrame { background:#e8f4ff; border:2px solid #2b7de9; border-radius:8px; }
                QLabel { border:none; background:transparent; }
            """)
        else:
            self.setStyleSheet("""
                QFrame { background:white; border:1px solid #cfcfcf; border-radius:8px; }
                QFrame:hover { border:2px solid #7aaef5; }
                QLabel { border:none; background:transparent; }
            """)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.selected = not self.selected
            self.update_style()
            self.toggled.emit(self.item, self.selected)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.activated.emit(self.item)
        super().mouseDoubleClickEvent(event)
