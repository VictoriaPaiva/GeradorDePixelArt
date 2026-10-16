
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt,Signal
from PySide6.QtGui import QImage,QPainter,QColor,QPixmap,QPen,QCursor
from PySide6.QtWidgets import QWidget


class MaskCanvas(QWidget):
    selectionChanged=Signal()
    colorClicked=Signal(int,int,object)  # x, y, rgb tuple

    def __init__(self):
        super().__init__()
        self.image=None
        self.arr=None
        self.working_mask=None
        self.hover_area_mask=None
        self.hover_color_rgb=None
        self.hover_color_area_mask=None
        self.hover_color_radius=18.0
        self.brush_size=35
        self.erase=False
        self.dragging=False
        self.pick_mode=False
        self.setMinimumSize(520,520)

    def set_image(self,pil_img:Image.Image):
        self.image=pil_img.convert("RGB")
        self.arr=np.asarray(self.image).copy()
        self.working_mask=np.zeros((self.image.height,self.image.width),dtype=np.uint8)
        self.hover_area_mask=None
        self.clear_color_hover()
        self.update()

    def set_pick_mode(self,value:bool):
        self.pick_mode=bool(value)
        self.dragging=False
        self.setCursor(Qt.CrossCursor if self.pick_mode else Qt.ArrowCursor)

    def set_hover_area_mask(self,mask):
        self.hover_area_mask=None if mask is None else mask.copy()
        self.update()

    def set_color_hover(self,rgb,area_mask,radius):
        self.hover_color_rgb=tuple(rgb)
        self.hover_color_area_mask=area_mask.copy()
        self.hover_color_radius=float(radius)
        self.update()

    def clear_color_hover(self):
        self.hover_color_rgb=None
        self.hover_color_area_mask=None
        self.update()

    def set_brush_size(self,size):
        self.brush_size=int(size)

    def set_erase(self,value):
        self.erase=bool(value)

    def clear_working(self):
        if self.working_mask is not None:
            self.working_mask[:]=0
            self.update()
            self.selectionChanged.emit()

    def select_all_working(self):
        if self.working_mask is not None:
            self.working_mask[:]=1
            self.update()
            self.selectionChanged.emit()

    def get_working_mask(self):
        return None if self.working_mask is None else self.working_mask.copy()

    def selected_pixels(self,mask=None):
        if self.arr is None:
            return np.empty((0,3),dtype=np.uint8)
        m=self.working_mask if mask is None else mask
        return self.arr[m.astype(bool)]

    def working_fraction(self):
        if self.working_mask is None:
            return 0.0
        return float(self.working_mask.mean())

    def _rect(self):
        if self.image is None:return None
        iw,ih=self.image.size
        ww,wh=self.width(),self.height()
        s=min(ww/iw,wh/ih)
        dw,dh=iw*s,ih*s
        return (ww-dw)/2,(wh-dh)/2,dw,dh,s

    def _to_image(self,p):
        r=self._rect()
        if r is None:return None
        x,y,dw,dh,s=r
        if not(x<=p.x()<=x+dw and y<=p.y()<=y+dh):return None
        ix=int((p.x()-x)/s)
        iy=int((p.y()-y)/s)
        ix=max(0,min(self.image.width-1,ix))
        iy=max(0,min(self.image.height-1,iy))
        return ix,iy

    def _paint(self,p):
        q=self._to_image(p)
        if q is None or self.working_mask is None:return
        ix,iy=q
        r=max(1,self.brush_size//2)
        yy,xx=np.ogrid[:self.working_mask.shape[0],:self.working_mask.shape[1]]
        circle=(xx-ix)**2+(yy-iy)**2<=r*r
        self.working_mask[circle]=0 if self.erase else 1
        self.update()
        self.selectionChanged.emit()

    def mousePressEvent(self,event):
        if event.button()!=Qt.LeftButton:
            return
        if self.pick_mode:
            q=self._to_image(event.position().toPoint())
            if q is not None and self.arr is not None:
                ix,iy=q
                rgb=tuple(int(v) for v in self.arr[iy,ix])
                self.colorClicked.emit(ix,iy,rgb)
            return
        self.dragging=True
        self._paint(event.position().toPoint())

    def mouseMoveEvent(self,event):
        if self.dragging and not self.pick_mode:
            self._paint(event.position().toPoint())

    def mouseReleaseEvent(self,event):
        if event.button()==Qt.LeftButton:
            self.dragging=False

    def _overlay_pixmap(self,mask,color,alpha,dw,dh):
        overlay=np.zeros((self.image.height,self.image.width,4),dtype=np.uint8)
        overlay[...,0]=color[0]
        overlay[...,1]=color[1]
        overlay[...,2]=color[2]
        overlay[...,3]=np.where(mask>0,alpha,0).astype(np.uint8)
        q=QImage(overlay.data,self.image.width,self.image.height,self.image.width*4,QImage.Format_RGBA8888)
        return QPixmap.fromImage(q.copy()).scaled(int(dw),int(dh),Qt.IgnoreAspectRatio,Qt.FastTransformation)

    def paintEvent(self,event):
        p=QPainter(self)
        p.fillRect(self.rect(),QColor(245,245,245))
        if self.image is None:
            p.drawText(self.rect(),Qt.AlignCenter,"Abra uma imagem.")
            return

        x,y,dw,dh,s=self._rect()
        data=self.image.tobytes("raw","RGB")
        q=QImage(data,self.image.width,self.image.height,self.image.width*3,QImage.Format_RGB888)
        pix=QPixmap.fromImage(q.copy()).scaled(int(dw),int(dh),Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
        p.drawPixmap(int(x),int(y),pix)

        if self.working_mask is not None and self.working_mask.any():
            p.drawPixmap(int(x),int(y),self._overlay_pixmap(self.working_mask,(255,0,255),95,dw,dh))

        if self.hover_area_mask is not None and self.hover_area_mask.any():
            p.drawPixmap(int(x),int(y),self._overlay_pixmap(self.hover_area_mask,(255,215,0),120,dw,dh))

        if self.hover_color_rgb is not None and self.hover_color_area_mask is not None:
            rep=np.array(self.hover_color_rgb,dtype=np.int16)
            diff=self.arr.astype(np.int16)-rep
            dist=np.sqrt((diff*diff).sum(axis=2))
            mask=(dist<=self.hover_color_radius) & self.hover_color_area_mask.astype(bool)
            if mask.any():
                p.drawPixmap(int(x),int(y),self._overlay_pixmap(mask.astype(np.uint8),(0,255,255),155,dw,dh))

        p.setPen(QPen(QColor(70,70,70),1))
        p.drawRect(int(x),int(y),int(dw)-1,int(dh)-1)
