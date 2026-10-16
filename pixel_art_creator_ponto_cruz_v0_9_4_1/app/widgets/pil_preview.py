from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy


class PilPreview(QLabel):
    def __init__(self, empty_text="Sem preview gerado."):
        super().__init__(empty_text)
        self._pil = None
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(360,340)
        self.setStyleSheet("background:#f5f6f8;border:1px solid #d2d6dc;")

    def set_pil(self, image):
        self._pil = None if image is None else image.copy()
        self._refresh_pixmap()

    def clear_preview(self, text="Sem preview gerado."):
        self._pil = None
        self.clear()
        self.setText(text)


    # Compatibility aliases used by generic preview widgets in other steps.
    def set_image(self, image):
        self.set_pil(image)

    def clear_image(self, text="Sem preview gerado."):
        self.clear_preview(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_pixmap()

    def _refresh_pixmap(self):
        if self._pil is None:
            return
        im=self._pil.convert("RGB")
        data=im.tobytes("raw","RGB")
        q=QImage(data,im.width,im.height,im.width*3,QImage.Format_RGB888)
        pix=QPixmap.fromImage(q.copy())
        avail=self.size()
        if avail.width()>10 and avail.height()>10:
            pix=pix.scaled(
                max(1,avail.width()-10),
                max(1,avail.height()-10),
                Qt.KeepAspectRatio,
                Qt.FastTransformation
            )
        self.setPixmap(pix)
