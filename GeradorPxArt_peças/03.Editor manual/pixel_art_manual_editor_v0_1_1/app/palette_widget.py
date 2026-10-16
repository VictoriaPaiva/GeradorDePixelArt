
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QFrame,QScrollArea


class Swatch(QWidget):
    clicked=Signal(object)

    def __init__(self,rgb,label=""):
        super().__init__()
        self.rgb=tuple(rgb)
        self.label=label
        self.selected=False
        self.setFixedHeight(52)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton:
            self.clicked.emit(self.rgb)

    def paintEvent(self,event):
        p=QPainter(self)
        border=QColor(43,125,233) if self.selected else QColor(130,130,130)
        p.setPen(QPen(border,3 if self.selected else 1))
        p.setBrush(QColor(*self.rgb))
        p.drawRect(3,3,44,44)
        p.setPen(QColor(20,20,20))
        p.drawText(58,20,self.label)
        p.drawText(58,40,f"RGB {self.rgb}")


class PalettePanel(QWidget):
    colorSelected=Signal(object)

    def __init__(self):
        super().__init__()
        self.items=[]
        self.current=None
        self.layout=QVBoxLayout(self)
        self.layout.addStretch(1)

    def set_palette(self,entries):
        while self.layout.count():
            item=self.layout.takeAt(0)
            w=item.widget()
            if w:w.deleteLater()
        self.items=[]
        for entry in entries:
            rgb=tuple(entry["rgb"])
            label=f'{entry.get("code","")}  {entry.get("hex","")}'
            sw=Swatch(rgb,label)
            sw.clicked.connect(self.select_color)
            self.items.append(sw)
            self.layout.addWidget(sw)
        self.layout.addStretch(1)

    def select_color(self,rgb):
        self.current=tuple(rgb)
        for sw in self.items:
            sw.selected=(sw.rgb==self.current)
            sw.update()
        self.colorSelected.emit(self.current)

    def select_if_present(self,rgb):
        for sw in self.items:
            if sw.rgb==tuple(rgb):
                self.select_color(rgb)
                return True
        return False
