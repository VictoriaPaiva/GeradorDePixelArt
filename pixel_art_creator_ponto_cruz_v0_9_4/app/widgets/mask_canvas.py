
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QImage, QPainter, QColor, QPixmap, QPen
from PySide6.QtWidgets import QWidget, QSizePolicy


class MaskCanvas(QWidget):
    selectionChanged = Signal()
    colorClicked = Signal(int, int, object)

    def __init__(self):
        super().__init__()
        self.image = None
        self.arr = None
        self.working_mask = None
        self.hover_area_mask = None
        self.hover_color_rgb = None
        self.hover_color_area_mask = None
        self.hover_color_radius = 18.0

        self.brush_size = 35
        self.erase = False
        self.dragging = False
        self.pick_mode = False

        # Camera model:
        # zoom=1 shows the whole image fitted in the viewport.
        # center_image is the image coordinate shown at the viewport center.
        self.zoom = 1.0
        self.min_zoom = 1.0
        self.max_zoom = 10.0
        self.center_image = QPointF(0, 0)

        self.panning = False
        self.last_pan_pos = None

        self.setMinimumSize(280, 240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

    # ------------------------------------------------------------------
    # Image / masks
    # ------------------------------------------------------------------
    def set_image(self, pil_img: Image.Image):
        self.image = pil_img.convert("RGB")
        self.arr = np.asarray(self.image).copy()
        self.working_mask = np.zeros(
            (self.image.height, self.image.width), dtype=np.uint8
        )
        self.hover_area_mask = None
        self.clear_color_hover()
        self.reset_view()
        self.update()
        self.selectionChanged.emit()

    def set_pick_mode(self, value: bool):
        self.pick_mode = bool(value)
        self.dragging = False
        self.setCursor(Qt.CrossCursor if self.pick_mode else Qt.ArrowCursor)

    def set_hover_area_mask(self, mask):
        self.hover_area_mask = None if mask is None else mask.copy()
        self.update()

    def set_color_hover(self, rgb, area_mask, radius):
        self.hover_color_rgb = tuple(rgb)
        self.hover_color_area_mask = area_mask.copy()
        self.hover_color_radius = float(radius)
        self.update()

    def clear_color_hover(self):
        self.hover_color_rgb = None
        self.hover_color_area_mask = None
        self.update()

    def set_brush_size(self, size):
        self.brush_size = int(size)

    def set_erase(self, value):
        self.erase = bool(value)

    def clear_working(self):
        if self.working_mask is not None:
            self.working_mask[:] = 0
            self.update()
            self.selectionChanged.emit()

    def select_all_working(self):
        if self.working_mask is not None:
            self.working_mask[:] = 1
            self.update()
            self.selectionChanged.emit()

    def get_working_mask(self):
        return None if self.working_mask is None else self.working_mask.copy()

    def selected_pixels(self, mask=None):
        if self.arr is None:
            return np.empty((0, 3), dtype=np.uint8)
        m = self.working_mask if mask is None else mask
        return self.arr[m.astype(bool)]

    def working_fraction(self):
        if self.working_mask is None:
            return 0.0
        return float(self.working_mask.mean())

    # ------------------------------------------------------------------
    # Camera / zoom / pan
    # ------------------------------------------------------------------
    def _fit_scale(self):
        if self.image is None:
            return 1.0
        iw, ih = self.image.size
        if iw <= 0 or ih <= 0:
            return 1.0
        return min(self.width() / iw, self.height() / ih)

    def _scale(self):
        return self._fit_scale() * self.zoom

    def reset_view(self):
        self.zoom = 1.0
        if self.image is not None:
            self.center_image = QPointF(
                self.image.width / 2,
                self.image.height / 2
            )
        else:
            self.center_image = QPointF(0, 0)
        self.update()

    def zoom_percent(self):
        return int(round(self.zoom * 100))

    def zoom_in(self):
        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self):
        self.set_zoom(self.zoom / 1.25)

    def set_zoom(self, value, anchor_pos=None):
        if self.image is None:
            return

        old_scale = self._scale()

        # Image coordinate currently under the requested anchor.
        if anchor_pos is None:
            anchor_pos = QPointF(self.width() / 2, self.height() / 2)

        anchor_img = self._widget_to_image_float(anchor_pos)

        self.zoom = max(self.min_zoom, min(self.max_zoom, float(value)))
        new_scale = self._scale()

        if self.zoom <= 1.00001:
            self.reset_view()
            return

        if anchor_img is not None and new_scale > 0:
            # Keep anchor_img under the same screen point after zoom.
            dx_screen = anchor_pos.x() - self.width() / 2
            dy_screen = anchor_pos.y() - self.height() / 2
            self.center_image = QPointF(
                anchor_img.x() - dx_screen / new_scale,
                anchor_img.y() - dy_screen / new_scale,
            )

        self._clamp_center()
        self.update()

    def _clamp_center(self):
        if self.image is None:
            return

        iw, ih = self.image.size
        scale = self._scale()
        if scale <= 0:
            return

        half_view_w = self.width() / (2 * scale)
        half_view_h = self.height() / (2 * scale)

        # If the viewport is wider than the image on an axis, keep centered.
        if 2 * half_view_w >= iw:
            cx = iw / 2
        else:
            cx = max(half_view_w, min(iw - half_view_w, self.center_image.x()))

        if 2 * half_view_h >= ih:
            cy = ih / 2
        else:
            cy = max(half_view_h, min(ih - half_view_h, self.center_image.y()))

        self.center_image = QPointF(cx, cy)

    def _display_rect(self):
        if self.image is None:
            return None

        iw, ih = self.image.size
        scale = self._scale()
        dw = iw * scale
        dh = ih * scale

        # Image position derived from image coordinate shown at viewport center.
        x = self.width() / 2 - self.center_image.x() * scale
        y = self.height() / 2 - self.center_image.y() * scale
        return x, y, dw, dh, scale

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._clamp_center()

    def wheelEvent(self, event):
        if self.image is None:
            return
        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 1.20 if delta > 0 else (1 / 1.20)
        self.set_zoom(self.zoom * factor, event.position())
        event.accept()

    # ------------------------------------------------------------------
    # Coordinate conversion / painting
    # ------------------------------------------------------------------
    def _widget_to_image_float(self, p):
        r = self._display_rect()
        if r is None:
            return None
        x, y, dw, dh, scale = r
        if scale <= 0:
            return None
        return QPointF((p.x() - x) / scale, (p.y() - y) / scale)

    def _to_image(self, p):
        q = self._widget_to_image_float(p)
        if q is None or self.image is None:
            return None

        ix, iy = q.x(), q.y()
        if ix < 0 or iy < 0 or ix >= self.image.width or iy >= self.image.height:
            return None

        return int(ix), int(iy)

    def _paint(self, p):
        q = self._to_image(p)
        if q is None or self.working_mask is None:
            return

        ix, iy = q
        r = max(1, self.brush_size // 2)

        h, w = self.working_mask.shape
        y0 = max(0, iy-r)
        y1 = min(h, iy+r+1)
        x0 = max(0, ix-r)
        x1 = min(w, ix+r+1)

        yy, xx = np.ogrid[y0:y1, x0:x1]
        circle = (xx-ix)**2 + (yy-iy)**2 <= r*r

        region = self.working_mask[y0:y1, x0:x1]
        region[circle] = 0 if self.erase else 1

        self.update()
        self.selectionChanged.emit()

    def mousePressEvent(self, event):
        if self.image is None:
            return

        # Pan: middle mouse or Shift + left mouse.
        if event.button() == Qt.MiddleButton or (
            event.button() == Qt.LeftButton and
            (event.modifiers() & Qt.ShiftModifier)
        ):
            self.panning = True
            self.last_pan_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() != Qt.LeftButton:
            return

        if self.pick_mode:
            q = self._to_image(event.position())
            if q is not None and self.arr is not None:
                ix, iy = q
                rgb = tuple(int(v) for v in self.arr[iy, ix])
                self.colorClicked.emit(ix, iy, rgb)
            return

        self.dragging = True
        self._paint(event.position())

    def mouseMoveEvent(self, event):
        if self.panning and self.last_pan_pos is not None:
            delta = event.position() - self.last_pan_pos
            scale = self._scale()
            if scale > 0:
                # Dragging image right means camera center moves left.
                self.center_image = QPointF(
                    self.center_image.x() - delta.x() / scale,
                    self.center_image.y() - delta.y() / scale
                )
                self._clamp_center()
                self.last_pan_pos = event.position()
                self.update()
            return

        if self.dragging and not self.pick_mode:
            self._paint(event.position())

    def mouseReleaseEvent(self, event):
        if self.panning:
            self.panning = False
            self.last_pan_pos = None
            self.setCursor(Qt.CrossCursor if self.pick_mode else Qt.ArrowCursor)

        if event.button() == Qt.LeftButton:
            self.dragging = False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _overlay_pixmap(self, mask, color, alpha, dw, dh):
        overlay = np.zeros(
            (self.image.height, self.image.width, 4),
            dtype=np.uint8
        )
        overlay[..., 0] = color[0]
        overlay[..., 1] = color[1]
        overlay[..., 2] = color[2]
        overlay[..., 3] = np.where(mask > 0, alpha, 0).astype(np.uint8)

        q = QImage(
            overlay.data,
            self.image.width,
            self.image.height,
            self.image.width * 4,
            QImage.Format_RGBA8888
        )
        return QPixmap.fromImage(q.copy()).scaled(
            max(1, int(round(dw))),
            max(1, int(round(dh))),
            Qt.IgnoreAspectRatio,
            Qt.FastTransformation
        )

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(245,245,245))

        if self.image is None:
            p.drawText(self.rect(), Qt.AlignCenter, "Abra uma imagem.")
            return

        x, y, dw, dh, scale = self._display_rect()

        data = self.image.tobytes("raw", "RGB")
        q = QImage(
            data,
            self.image.width,
            self.image.height,
            self.image.width * 3,
            QImage.Format_RGB888
        )
        pix = QPixmap.fromImage(q.copy()).scaled(
            max(1, int(round(dw))),
            max(1, int(round(dh))),
            Qt.IgnoreAspectRatio,
            Qt.FastTransformation
        )
        p.drawPixmap(int(round(x)), int(round(y)), pix)

        if self.working_mask is not None and self.working_mask.any():
            p.drawPixmap(
                int(round(x)),
                int(round(y)),
                self._overlay_pixmap(
                    self.working_mask, (255,0,255), 95, dw, dh
                )
            )

        if self.hover_area_mask is not None and self.hover_area_mask.any():
            p.drawPixmap(
                int(round(x)),
                int(round(y)),
                self._overlay_pixmap(
                    self.hover_area_mask, (255,215,0), 120, dw, dh
                )
            )

        if self.hover_color_rgb is not None and self.hover_color_area_mask is not None:
            rep = np.array(self.hover_color_rgb, dtype=np.int16)
            diff = self.arr.astype(np.int16) - rep
            dist = np.sqrt((diff*diff).sum(axis=2))
            mask = (
                (dist <= self.hover_color_radius) &
                self.hover_color_area_mask.astype(bool)
            )
            if mask.any():
                p.drawPixmap(
                    int(round(x)),
                    int(round(y)),
                    self._overlay_pixmap(
                        mask.astype(np.uint8),
                        (0,255,255),
                        155,
                        dw,
                        dh
                    )
                )

        p.setPen(QPen(QColor(70,70,70), 1))
        p.drawRect(
            int(round(x)),
            int(round(y)),
            max(1, int(round(dw))-1),
            max(1, int(round(dh))-1)
        )

        # Zoom badge.
        p.setPen(QColor(30,30,30))
        p.setBrush(QColor(255,255,255,225))
        p.drawRoundedRect(10,10,66,28,7,7)
        p.drawText(
            10,10,66,28,
            Qt.AlignCenter,
            f"{self.zoom_percent()}%"
        )
