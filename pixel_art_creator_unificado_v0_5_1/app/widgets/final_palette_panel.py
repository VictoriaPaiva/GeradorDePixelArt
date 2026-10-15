
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame


class Swatch(QWidget):
    def __init__(self, rgb, essential=False, index=0):
        super().__init__()
        self.rgb = tuple(rgb)
        self.essential = essential
        self.index = index
        self.setFixedSize(58, 46)
        self.setToolTip(
            f"{index+1:02d} • RGB {self.rgb} • "
            + ("ESSENCIAL" if essential else "complementar")
        )

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(*self.rgb))
        p.setPen(
            QPen(
                QColor("#1677d2") if self.essential else QColor("#555"),
                3 if self.essential else 1
            )
        )
        p.drawRect(self.rect().adjusted(1,1,-2,-2))

        # tiny marker for protected essential colors
        if self.essential:
            p.setPen(QColor("white"))
            p.drawText(
                self.rect().adjusted(3,2,-3,-2),
                Qt.AlignTop | Qt.AlignRight,
                "★"
            )


class FinalPalettePanel(QFrame):
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

        root = QVBoxLayout(self)
        root.setContentsMargins(8,6,8,6)
        root.setSpacing(4)

        self.title = QLabel("PALETA FINAL")
        self.title.setStyleSheet("font-weight:700;")
        root.addWidget(self.title)

        self.row_widget = QWidget()
        self.row = QHBoxLayout(self.row_widget)
        self.row.setContentsMargins(0,0,0,0)
        self.row.setSpacing(3)
        root.addWidget(self.row_widget)

        self.summary = QLabel("")
        self.summary.setStyleSheet("font-size:11px;color:#59616d;")
        root.addWidget(self.summary)

    def set_palette(self, palette, essential):
        while self.row.count():
            item = self.row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        essential_set = {tuple(c) for c in essential}

        for i, rgb in enumerate(palette):
            self.row.addWidget(
                Swatch(
                    rgb,
                    essential=tuple(rgb) in essential_set,
                    index=i
                )
            )

        self.row.addStretch(1)

        self.summary.setText(
            f"{len(palette)} cores finais • "
            f"{len(essential_set)} essenciais protegidas (★) • "
            f"{max(0, len(palette)-len(essential_set))} complementares"
        )
