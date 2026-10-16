
from pathlib import Path
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel


class ImagePreview(QLabel):
    def __init__(self, placeholder="Nenhuma imagem carregada"):
        super().__init__(placeholder)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(640, 560)
        self.setStyleSheet("""
            QLabel {
                background: #f6f7f9;
                border: 1px solid #ccd2da;
                border-radius: 10px;
                color: #68707c;
            }
        """)
        self._path = None
        self._pixmap = None

    def set_image(self, path):
        self._path = str(path)
        try:
            im = Image.open(path).convert("RGB")
            data = im.tobytes("raw", "RGB")
            q = QImage(data, im.width, im.height, im.width * 3, QImage.Format_RGB888)
            self._pixmap = QPixmap.fromImage(q.copy())
            self._apply_scaled()
            self.setToolTip(f"{Path(path).name} — {im.width}×{im.height}")
        except Exception as e:
            self._pixmap = None
            self.setText(f"Erro ao abrir imagem:\n{e}")

    def clear_image(self, text="Nenhuma imagem carregada"):
        self._path = None
        self._pixmap = None
        self.setPixmap(QPixmap())
        self.setText(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_scaled()

    def _apply_scaled(self):
        if not self._pixmap:
            return
        target = self.size()
        scaled = self._pixmap.scaled(
            max(1, target.width() - 20),
            max(1, target.height() - 20),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.setPixmap(scaled)
