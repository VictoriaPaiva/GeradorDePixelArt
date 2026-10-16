
import numpy as np
from PySide6.QtCore import Qt,Signal,QRectF,QPointF
from PySide6.QtGui import QColor,QPainter,QPen
from PySide6.QtWidgets import QWidget,QSizePolicy

class ManualEditorCanvas(QWidget):
    pixelChanged=Signal(int,int,object,object); colorPicked=Signal(object); zoomChanged=Signal(int)
    def __init__(self):
        super().__init__(); self.arr=None; self.paint_rgb=(255,255,255); self.hover_rgb=None; self.grid=True; self.dragging=False; self.last_cell=None; self.zoom=1.; self.center=QPointF(.5,.5); self.panning=False; self.last_pan=None
        self.setMinimumSize(360,340); self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding); self.setMouseTracking(True)
    def set_array(self,arr): self.arr=None if arr is None else np.asarray(arr,dtype=np.uint8).copy(); self.reset_view(); self.update()
    def get_array(self): return None if self.arr is None else self.arr.copy()
    def dims(self):
        if self.arr is None:return 0,0
        h,w=self.arr.shape[:2]; return w,h
    def set_paint_color(self,rgb): self.paint_rgb=tuple(int(v) for v in rgb)
    def set_hover_color(self,rgb): self.hover_rgb=None if rgb is None else tuple(int(v) for v in rgb); self.update()
    def set_grid(self,v): self.grid=bool(v); self.update()
    def zoom_percent(self): return int(round(self.zoom*100))
    def reset_view(self): self.zoom=1.; self.center=QPointF(.5,.5); self.zoomChanged.emit(100); self.update()
    def zoom_in(self): self.set_zoom(self.zoom*1.25)
    def zoom_out(self): self.set_zoom(self.zoom/1.25)
    def _fit_scale(self):
        w,h=self.dims(); return min(max(1,self.width()-16)/max(1,w),max(1,self.height()-16)/max(1,h))
    def _scale(self): return self._fit_scale()*self.zoom
    def _rect(self):
        if self.arr is None:return None
        w,h=self.dims(); s=self._scale(); dw=w*s; dh=h*s
        cx=self.center.x()*w; cy=self.center.y()*h
        return self.width()/2-cx*s,self.height()/2-cy*s,dw,dh,s
    def set_zoom(self,value,anchor=None):
        if self.arr is None:return
        if anchor is None:anchor=QPointF(self.width()/2,self.height()/2)
        old=self._to_float(anchor); self.zoom=max(1.,min(15.,float(value)))
        if self.zoom<=1.0001:self.reset_view(); return
        if old is not None:
            w,h=self.dims(); s=self._scale(); self.center=QPointF((old.x()-(anchor.x()-self.width()/2)/s)/w,(old.y()-(anchor.y()-self.height()/2)/s)/h); self._clamp()
        self.zoomChanged.emit(self.zoom_percent()); self.update()
    def _clamp(self): self.center=QPointF(min(1,max(0,self.center.x())),min(1,max(0,self.center.y())))
    def wheelEvent(self,e):
        d=e.angleDelta().y();
        if d:self.set_zoom(self.zoom*(1.2 if d>0 else 1/1.2),e.position())
    def _to_float(self,pos):
        r=self._rect();
        if not r:return None
        x0,y0,dw,dh,s=r; return QPointF((pos.x()-x0)/s,(pos.y()-y0)/s)
    def _to_cell(self,pos):
        q=self._to_float(pos); w,h=self.dims()
        if q is None or not(0<=q.x()<w and 0<=q.y()<h):return None
        return int(q.x()),int(q.y())
    def _paint(self,x,y):
        old=tuple(int(v) for v in self.arr[y,x]); new=self.paint_rgb
        if old==new:return
        self.arr[y,x]=np.array(new,dtype=np.uint8); self.pixelChanged.emit(x,y,old,new); self.update()
    def mousePressEvent(self,e):
        if self.arr is None:return
        if e.button()==Qt.MiddleButton or (e.button()==Qt.LeftButton and e.modifiers()&Qt.ShiftModifier): self.panning=True; self.last_pan=e.position(); return
        c=self._to_cell(e.position());
        if c is None:return
        x,y=c
        if e.button()==Qt.RightButton:self.colorPicked.emit(tuple(int(v) for v in self.arr[y,x])); return
        if e.button()==Qt.LeftButton:self.dragging=True; self.last_cell=c; self._paint(x,y)
    def mouseMoveEvent(self,e):
        if self.panning and self.last_pan is not None:
            d=e.position()-self.last_pan; w,h=self.dims(); s=self._scale(); self.center=QPointF(self.center.x()-d.x()/(s*w),self.center.y()-d.y()/(s*h)); self._clamp(); self.last_pan=e.position(); self.update(); return
        if self.dragging:
            c=self._to_cell(e.position())
            if c is not None and c!=self.last_cell:self.last_cell=c; self._paint(*c)
    def mouseReleaseEvent(self,e):
        if self.panning:self.panning=False; self.last_pan=None
        if e.button()==Qt.LeftButton:self.dragging=False; self.last_cell=None
    def paintEvent(self,e):
        p=QPainter(self); p.fillRect(self.rect(),QColor('#f5f6f8'))
        if self.arr is None:p.setPen(QColor('#68707c')); p.drawText(self.rect(),Qt.AlignCenter,'A matriz simplificada aparecerá aqui.'); return
        x0,y0,dw,dh,s=self._rect(); w,h=self.dims()
        for y in range(h):
            for x in range(w):
                rgb=[int(v) for v in self.arr[y,x]]; p.fillRect(QRectF(x0+x*s,y0+y*s,s+.15,s+.15),QColor(*rgb))
        if self.hover_rgb is not None:
            ys,xs=np.where(np.all(self.arr==np.array(self.hover_rgb,dtype=np.uint8),axis=2)); p.setPen(QPen(QColor(255,205,0,210),max(1,int(s*.12)))); p.setBrush(QColor(255,255,0,45))
            for y,x in zip(ys,xs):p.drawRect(QRectF(x0+x*s,y0+y*s,s,s))
        if self.grid and s>=3:
            p.setPen(QPen(QColor(30,30,30,90),1))
            for x in range(w+1):p.drawLine(int(x0+x*s),int(y0),int(x0+x*s),int(y0+dh))
            for y in range(h+1):p.drawLine(int(x0),int(y0+y*s),int(x0+dw),int(y0+y*s))
        p.setPen(QPen(QColor(60,60,60),1)); p.drawRect(QRectF(x0,y0,dw,dh))
