
import numpy as np

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QSizePolicy


class MatrixCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.arr = None
        self.show_grid = False
        self.setMinimumSize(360, 340)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_array(self, arr):
        self.arr = None if arr is None else np.asarray(arr, dtype=np.uint8).copy()
        self.update()

    def set_grid(self, enabled):
        self.show_grid = bool(enabled)
        self.update()

    def _geometry(self):
        if self.arr is None:
            return None
        h, w = self.arr.shape[:2]
        margin = 10
        aw = max(1, self.width() - margin * 2)
        ah = max(1, self.height() - margin * 2)
        s = min(aw / w, ah / h)
        dw, dh = w * s, h * s
        x0 = (self.width() - dw) / 2
        y0 = (self.height() - dh) / 2
        return x0, y0, dw, dh, s

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#f5f6f8"))

        if self.arr is None:
            p.setPen(QColor("#68707c"))
            p.drawText(
                self.rect(),
                Qt.AlignCenter,
                "Gere a matriz 100×100 para visualizar."
            )
            return

        x0, y0, dw, dh, s = self._geometry()
        h, w = self.arr.shape[:2]

        # Draw true logical cells without smoothing/interpolation.
        for y in range(h):
            yy = y0 + y * s
            for x in range(w):
                xx = x0 + x * s
                r, g, b = [int(v) for v in self.arr[y, x]]
                p.fillRect(
                    QRectF(xx, yy, s + 0.15, s + 0.15),
                    QColor(r, g, b)
                )

        p.setPen(QPen(QColor(60, 60, 60), 1))
        p.drawRect(QRectF(x0, y0, dw, dh))

        # Visual grid only. It is never written into the matrix.
        if self.show_grid and s >= 3:
            p.setPen(QPen(QColor(30, 30, 30, 95), 1))
            for x in range(w + 1):
                xx = x0 + x * s
                p.drawLine(int(xx), int(y0), int(xx), int(y0 + dh))
            for y in range(h + 1):
                yy = y0 + y * s
                p.drawLine(int(x0), int(yy), int(x0 + dw), int(yy))
