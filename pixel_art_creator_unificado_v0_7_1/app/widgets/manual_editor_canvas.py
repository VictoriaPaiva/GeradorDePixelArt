
import numpy as np

from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QSizePolicy


class ManualEditorCanvas(QWidget):
    pixelChanged = Signal(int, int, object, object)
    colorPicked = Signal(object)
    zoomChanged = Signal(int)

    def __init__(self):
        super().__init__()

        self.arr = None
        self.paint_rgb = (255,255,255)
        self.hover_rgb = None
        self.grid = True

        self.dragging = False
        self.last_cell = None

        # Camera. zoom=1 means the complete 100x100 matrix fitted to the viewport.
        self.zoom = 1.0
        self.min_zoom = 1.0
        self.max_zoom = 12.0
        self.center_cell = QPointF(50.0, 50.0)

        self.panning = False
        self.last_pan_pos = None

        self.setMinimumSize(360,340)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    # ------------------------------------------------------------------
    # Matrix
    # ------------------------------------------------------------------
    def set_array(self, arr):
        if arr is None:
            self.arr = None
        else:
            a = np.asarray(arr, dtype=np.uint8)
            if a.shape != (100,100,3):
                raise ValueError(
                    f"Esperado 100×100 RGB; recebido {a.shape}"
                )
            self.arr = a.copy()

        self.reset_view()
        self.update()

    def get_array(self):
        return None if self.arr is None else self.arr.copy()

    def set_paint_color(self, rgb):
        self.paint_rgb = tuple(int(v) for v in rgb)

    def set_hover_color(self, rgb):
        self.hover_rgb = (
            None
            if rgb is None
            else tuple(int(v) for v in rgb)
        )
        self.update()

    def set_grid(self, value):
        self.grid = bool(value)
        self.update()

    # ------------------------------------------------------------------
    # Camera / zoom / pan
    # ------------------------------------------------------------------
    def _fit_scale(self):
        margin = 8
        return min(
            max(1, self.width()-2*margin) / 100,
            max(1, self.height()-2*margin) / 100
        )

    def _scale(self):
        return self._fit_scale() * self.zoom

    def zoom_percent(self):
        return int(round(self.zoom * 100))

    def reset_view(self):
        self.zoom = 1.0
        self.center_cell = QPointF(50.0, 50.0)
        self.zoomChanged.emit(self.zoom_percent())
        self.update()

    def zoom_in(self):
        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self):
        self.set_zoom(self.zoom / 1.25)

    def set_zoom(self, value, anchor_pos=None):
        if self.arr is None:
            return

        if anchor_pos is None:
            anchor_pos = QPointF(
                self.width()/2,
                self.height()/2
            )

        anchor_cell = self._widget_to_cell_float(
            anchor_pos
        )

        self.zoom = max(
            self.min_zoom,
            min(self.max_zoom, float(value))
        )

        if self.zoom <= 1.00001:
            self.reset_view()
            return

        new_scale = self._scale()

        if (
            anchor_cell is not None
            and new_scale > 0
        ):
            dx = (
                anchor_pos.x()
                - self.width()/2
            )
            dy = (
                anchor_pos.y()
                - self.height()/2
            )

            self.center_cell = QPointF(
                anchor_cell.x()
                - dx/new_scale,
                anchor_cell.y()
                - dy/new_scale
            )

        self._clamp_center()
        self.zoomChanged.emit(
            self.zoom_percent()
        )
        self.update()

    def _clamp_center(self):
        if self.arr is None:
            return

        scale = self._scale()
        if scale <= 0:
            return

        half_w = self.width() / (2*scale)
        half_h = self.height() / (2*scale)

        if 2*half_w >= 100:
            cx = 50.0
        else:
            cx = max(
                half_w,
                min(100-half_w, self.center_cell.x())
            )

        if 2*half_h >= 100:
            cy = 50.0
        else:
            cy = max(
                half_h,
                min(100-half_h, self.center_cell.y())
            )

        self.center_cell = QPointF(cx,cy)

    def _rect(self):
        if self.arr is None:
            return None

        scale = self._scale()
        dw = 100*scale
        dh = 100*scale

        x0 = (
            self.width()/2
            - self.center_cell.x()*scale
        )
        y0 = (
            self.height()/2
            - self.center_cell.y()*scale
        )

        return x0,y0,dw,dh,scale

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._clamp_center()

    def wheelEvent(self, event):
        if self.arr is None:
            return

        delta = event.angleDelta().y()
        if delta == 0:
            return

        factor = (
            1.20
            if delta > 0
            else 1/1.20
        )

        self.set_zoom(
            self.zoom*factor,
            event.position()
        )
        event.accept()

    # ------------------------------------------------------------------
    # Coordinate mapping / painting
    # ------------------------------------------------------------------
    def _widget_to_cell_float(self, pos):
        r = self._rect()
        if r is None:
            return None

        x0,y0,dw,dh,s = r

        if s <= 0:
            return None

        return QPointF(
            (pos.x()-x0)/s,
            (pos.y()-y0)/s
        )

    def _to_cell(self, pos):
        q = self._widget_to_cell_float(pos)
        if q is None:
            return None

        x,y = q.x(),q.y()

        if (
            x < 0 or y < 0
            or x >= 100 or y >= 100
        ):
            return None

        return int(x),int(y)

    def _paint(self, x, y):
        old = tuple(
            int(v)
            for v in self.arr[y,x]
        )
        new = self.paint_rgb

        if old == new:
            return

        self.arr[y,x] = np.array(
            new,
            dtype=np.uint8
        )

        self.pixelChanged.emit(
            x,y,old,new
        )

        self.update()

    def mousePressEvent(self, event):
        if self.arr is None:
            return

        # Pan with middle mouse, or Shift + left mouse.
        if (
            event.button() == Qt.MiddleButton
            or (
                event.button() == Qt.LeftButton
                and (
                    event.modifiers()
                    & Qt.ShiftModifier
                )
            )
        ):
            self.panning = True
            self.last_pan_pos = event.position()
            self.setCursor(
                Qt.ClosedHandCursor
            )
            event.accept()
            return

        c = self._to_cell(
            event.position()
        )

        if c is None:
            return

        x,y = c

        if event.button() == Qt.RightButton:
            self.colorPicked.emit(
                tuple(
                    int(v)
                    for v in self.arr[y,x]
                )
            )
            return

        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_cell = c
            self._paint(x,y)

    def mouseMoveEvent(self, event):
        if (
            self.panning
            and self.last_pan_pos is not None
        ):
            delta = (
                event.position()
                - self.last_pan_pos
            )

            scale = self._scale()

            if scale > 0:
                self.center_cell = QPointF(
                    self.center_cell.x()
                    - delta.x()/scale,
                    self.center_cell.y()
                    - delta.y()/scale
                )
                self._clamp_center()
                self.last_pan_pos = (
                    event.position()
                )
                self.update()
            return

        if not self.dragging:
            return

        c = self._to_cell(
            event.position()
        )

        if (
            c is not None
            and c != self.last_cell
        ):
            self.last_cell = c
            self._paint(*c)

    def mouseReleaseEvent(self, event):
        if self.panning:
            self.panning = False
            self.last_pan_pos = None
            self.setCursor(
                Qt.ArrowCursor
            )

        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.last_cell = None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(
            self.rect(),
            QColor("#f5f6f8")
        )

        if self.arr is None:
            p.setPen(
                QColor("#68707c")
            )
            p.drawText(
                self.rect(),
                Qt.AlignCenter,
                "A imagem simplificada aprovada será carregada aqui."
            )
            return

        x0,y0,dw,dh,s = self._rect()

        for y in range(100):
            yy = y0+y*s

            for x in range(100):
                xx = x0+x*s

                r,g,b = [
                    int(v)
                    for v in self.arr[y,x]
                ]

                p.fillRect(
                    QRectF(
                        xx,
                        yy,
                        s+0.15,
                        s+0.15
                    ),
                    QColor(r,g,b)
                )

        if self.hover_rgb is not None:
            target = np.array(
                self.hover_rgb,
                dtype=np.uint8
            )

            ys,xs = np.where(
                np.all(
                    self.arr == target,
                    axis=2
                )
            )

            p.setPen(
                QPen(
                    QColor(255,205,0,205),
                    max(
                        1,
                        int(round(s*0.12))
                    )
                )
            )
            p.setBrush(
                QColor(255,255,0,55)
            )

            for y,x in zip(ys,xs):
                p.drawRect(
                    QRectF(
                        x0+x*s,
                        y0+y*s,
                        s,
                        s
                    )
                )

        if self.grid and s >= 3:
            p.setPen(
                QPen(
                    QColor(30,30,30,85),
                    1
                )
            )

            for x in range(101):
                xx = x0+x*s
                p.drawLine(
                    int(xx),
                    int(y0),
                    int(xx),
                    int(y0+dh)
                )

            for y in range(101):
                yy = y0+y*s
                p.drawLine(
                    int(x0),
                    int(yy),
                    int(x0+dw),
                    int(yy)
                )

        p.setPen(
            QPen(
                QColor(60,60,60),
                1
            )
        )
        p.drawRect(
            QRectF(
                x0,
                y0,
                dw,
                dh
            )
        )

        # Zoom badge
        p.setPen(
            QColor("#222")
        )
        p.setBrush(
            QColor(
                255,255,255,225
            )
        )
        p.drawRoundedRect(
            10,10,66,28,7,7
        )
        p.drawText(
            10,10,66,28,
            Qt.AlignCenter,
            f"{self.zoom_percent()}%"
        )
