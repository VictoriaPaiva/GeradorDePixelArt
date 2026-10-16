
import numpy as np
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class PixelCanvas(QWidget):
    pixelChanged=Signal(int,int,object,object)  # logical_x, logical_y, old_rgb, new_rgb
    colorPicked=Signal(object)

    def __init__(self):
        super().__init__()
        self.arr=None
        self.paint_rgb=(255,255,255)
        self.hover_rgb=None
        self.grid=True
        self.dragging=False
        self.last_cell=None
        self.logical_w=None
        self.logical_h=None
        self.setMinimumSize(700,700)
        self.setMouseTracking(True)

    def set_array(self,arr):
        self.arr=arr.copy()
        self._auto_detect_logical_grid()
        self.update()

    def _auto_detect_logical_grid(self):
        if self.arr is None:
            self.logical_w = None
            self.logical_h = None
            return

        h,w = self.arr.shape[:2]

        if (w,h) in [(50,50),(100,100)]:
            self.logical_w, self.logical_h = w,h
            return

        if w % 100 == 0 and h % 100 == 0:
            self.logical_w = 100
            self.logical_h = 100
            return

        if w % 50 == 0 and h % 50 == 0:
            self.logical_w = 50
            self.logical_h = 50
            return

        self.logical_w, self.logical_h = w,h

    def set_logical_grid(self, value):
        if self.arr is None:
            self.logical_w = None
            self.logical_h = None
            self.update()
            return

        h,w = self.arr.shape[:2]
        if value == "auto":
            self._auto_detect_logical_grid()
        elif value == 50:
            self.logical_w = 50
            self.logical_h = 50
        elif value == 100:
            self.logical_w = 100
            self.logical_h = 100
        else:
            self.logical_w, self.logical_h = w,h
        self.update()

    def get_logical_size(self):
        if self.arr is None:
            return None
        return self.logical_w, self.logical_h

    def set_paint_color(self,rgb):
        self.paint_rgb=tuple(int(x) for x in rgb)

    def set_hover_color(self, rgb_or_none):
        self.hover_rgb = None if rgb_or_none is None else tuple(int(x) for x in rgb_or_none)
        self.update()

    def set_grid(self,value):
        self.grid=bool(value)
        self.update()

    def _rect(self):
        if self.arr is None:return None
        gh,gw=self.logical_h,self.logical_w
        ww,wh=self.width(),self.height()
        s=min(ww/gw,wh/gh)
        dw,dh=gw*s,gh*s
        return (ww-dw)/2,(wh-dh)/2,dw,dh,s

    def _to_cell(self,pos):
        r=self._rect()
        if r is None:return None
        x0,y0,dw,dh,s=r
        if not(x0<=pos.x()<x0+dw and y0<=pos.y()<y0+dh):
            return None
        x=int((pos.x()-x0)/s)
        y=int((pos.y()-y0)/s)
        return max(0,min(self.logical_w-1,x)),max(0,min(self.logical_h-1,y))

    def _logical_cell_bounds(self, lx, ly):
        h,w = self.arr.shape[:2]
        x0 = round(lx * w / self.logical_w)
        x1 = round((lx + 1) * w / self.logical_w)
        y0 = round(ly * h / self.logical_h)
        y1 = round((ly + 1) * h / self.logical_h)

        x1 = max(x1, x0 + 1)
        y1 = max(y1, y0 + 1)
        return x0, y0, x1, y1

    def _representative_color(self, lx, ly):
        x0,y0,x1,y1 = self._logical_cell_bounds(lx,ly)
        block = self.arr[y0:y1, x0:x1]
        cy = (block.shape[0]-1)//2
        cx = (block.shape[1]-1)//2
        rgb = block[cy, cx]
        return tuple(int(v) for v in rgb)

    def _paint_cell(self,lx,ly):
        x0,y0,x1,y1 = self._logical_cell_bounds(lx,ly)
        old = self._representative_color(lx,ly)
        new = self.paint_rgb
        if old == new:
            return
        self.arr[y0:y1, x0:x1] = np.array(new,dtype=np.uint8)
        self.pixelChanged.emit(lx,ly,old,new)
        self.update()

    def mousePressEvent(self,event):
        cell=self._to_cell(event.position())
        if cell is None:return
        x,y=cell

        if event.button()==Qt.RightButton:
            self.colorPicked.emit(self._representative_color(x,y))
            return

        if event.button()==Qt.LeftButton:
            self.dragging=True
            self.last_cell=(x,y)
            self._paint_cell(x,y)

    def mouseMoveEvent(self,event):
        if not self.dragging:return
        cell=self._to_cell(event.position())
        if cell is None:return
        if cell!=self.last_cell:
            self.last_cell=cell
            self._paint_cell(*cell)

    def mouseReleaseEvent(self,event):
        if event.button()==Qt.LeftButton:
            self.dragging=False
            self.last_cell=None

    def paintEvent(self,event):
        p=QPainter(self)
        p.fillRect(self.rect(),QColor(245,245,245))
        if self.arr is None:
            p.drawText(self.rect(),Qt.AlignCenter,"Abra uma matriz PNG.")
            return

        x0,y0,dw,dh,s=self._rect()
        gh,gw=self.logical_h,self.logical_w

        # Draw each logical pixel as one solid rectangle.
        for y in range(gh):
            yy=y0+y*s
            for x in range(gw):
                xx=x0+x*s
                c=self._representative_color(x,y)
                p.fillRect(QRectF(xx,yy,s+0.2,s+0.2),QColor(int(c[0]),int(c[1]),int(c[2])))

        # Hover highlight for same-color cells
        if self.hover_rgb is not None:
            overlay_fill = QColor(255, 255, 0, 50)
            overlay_pen = QPen(QColor(255, 210, 0, 180), max(1, int(round(s*0.12))))
            p.setPen(overlay_pen)
            p.setBrush(overlay_fill)
            for y in range(gh):
                yy=y0+y*s
                for x in range(gw):
                    if self._representative_color(x,y) == self.hover_rgb:
                        xx=x0+x*s
                        p.drawRect(QRectF(xx,yy,s,s))

        if self.grid and s>=3:
            p.setPen(QPen(QColor(30,30,30,80),1))
            for x in range(gw+1):
                xx=x0+x*s
                p.drawLine(int(xx),int(y0),int(xx),int(y0+dh))
            for y in range(gh+1):
                yy=y0+y*s
                p.drawLine(int(x0),int(yy),int(x0+dw),int(yy))
