
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QScrollArea, QWidget, QVBoxLayout


class ImageView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.label = QLabel("Abra uma imagem para começar.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background:#f4f4f4; border:1px solid #d0d0d0;")
        self.label.setMinimumSize(360, 360)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def set_pixmap(self, pixmap: QPixmap):
        if pixmap.isNull():
            return
        target = self.label.size()
        scaled = pixmap.scaled(
            target,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        pix = self.label.pixmap()
        # main window will re-send original pixmap on resize when needed
