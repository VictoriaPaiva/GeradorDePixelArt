from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget, QSizePolicy


class ImagePreview(QWidget):
    """Preview que sempre mostra a imagem INTEIRA, sem recorte."""

    def __init__(self, placeholder="Nenhuma imagem carregada"):
        super().__init__()
        self.placeholder = placeholder
        self._path = None
        self._pixmap = None
        self.setMinimumSize(420, 320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background:#f6f7f9;")

    def set_image(self, path):
        self._path = str(path)
        try:
            im = Image.open(path).convert("RGB")
            data = im.tobytes("raw", "RGB")
            q = QImage(data, im.width, im.height, im.width * 3, QImage.Format_RGB888)
            self._pixmap = QPixmap.fromImage(q.copy())
            self.setToolTip(f"{Path(path).name} — {im.width}×{im.height}")
            self.update()
        except Exception as e:
            self._pixmap = None
            self.placeholder = f"Erro ao abrir imagem:\n{e}"
            self.update()

    def clear_image(self, text="Nenhuma imagem carregada"):
        self._path = None
        self._pixmap = None
        self.placeholder = text
        self.setToolTip("")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.fillRect(self.rect(), QColor("#f6f7f9"))
        painter.setPen(QPen(QColor("#ccd2da"), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 10, 10)

        if not self._pixmap or self._pixmap.isNull():
            painter.setPen(QColor("#68707c"))
            painter.drawText(
                self.rect().adjusted(20, 20, -20, -20),
                Qt.AlignCenter | Qt.TextWordWrap,
                self.placeholder,
            )
            return

        margin = 14
        target = self.rect().adjusted(margin, margin, -margin, -margin)
        scaled = self._pixmap.scaled(
            target.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        x = target.x() + (target.width() - scaled.width()) // 2
        y = target.y() + (target.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
