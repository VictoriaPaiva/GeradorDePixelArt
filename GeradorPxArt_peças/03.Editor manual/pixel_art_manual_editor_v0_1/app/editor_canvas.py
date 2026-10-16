
import numpy as np
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class PixelCanvas(QWidget):
    pixelChanged=Signal(int,int,object,object)  # x,y,old,new
    colorPicked=Signal(object)

    def __init__(self):
        super().__init__()
        self.arr=None
        self.paint_rgb=(255,255,255)
        self.grid=True
        self.dragging=False
        self.last_cell=None
        self.setMinimumSize(700,700)
        self.setMouseTracking(True)

    def set_array(self,arr):
        self.arr=arr.copy()
        self.update()

    def set_paint_color(self,rgb):
        self.paint_rgb=tuple(int(x) for x in rgb)

    def set_grid(self,value):
        self.grid=bool(value)
        self.update()

    def _rect(self):
        if self.arr is None:return None
        h,w=self.arr.shape[:2]
        ww,wh=self.width(),self.height()
        s=min(ww/w,wh/h)
        dw,dh=w*s,h*s
        return (ww-dw)/2,(wh-dh)/2,dw,dh,s

    def _to_cell(self,pos):
        r=self._rect()
        if r is None:return None
        x0,y0,dw,dh,s=r
        if not(x0<=pos.x()<x0+dw and y0<=pos.y()<y0+dh):
            return None
        x=int((pos.x()-x0)/s)
        y=int((pos.y()-y0)/s)
        h,w=self.arr.shape[:2]
        return max(0,min(w-1,x)),max(0,min(h-1,y))

    def _paint_cell(self,x,y):
        old=tuple(int(v) for v in self.arr[y,x])
        new=self.paint_rgb
        if old==new:return
        self.arr[y,x]=np.array(new,dtype=np.uint8)
        self.pixelChanged.emit(x,y,old,new)
        self.update()

    def mousePressEvent(self,event):
        cell=self._to_cell(event.position())
        if cell is None:return
        x,y=cell

        if event.button()==Qt.RightButton:
            self.colorPicked.emit(tuple(int(v) for v in self.arr[y,x]))
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
        h,w=self.arr.shape[:2]

        # Draw each logical pixel as a solid rectangle.
        for y in range(h):
            yy=y0+y*s
            for x in range(w):
                xx=x0+x*s
                c=self.arr[y,x]
                p.fillRect(QRectF(xx,yy,s+0.2,s+0.2),QColor(int(c[0]),int(c[1]),int(c[2])))

        if self.grid and s>=3:
            p.setPen(QPen(QColor(30,30,30,80),1))
            for x in range(w+1):
                xx=x0+x*s
                p.drawLine(int(xx),int(y0),int(xx),int(y0+dh))
            for y in range(h+1):
                yy=y0+y*s
                p.drawLine(int(x0),int(yy),int(x0+dw),int(yy))
