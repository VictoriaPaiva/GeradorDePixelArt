
from collections import OrderedDict
from PySide6.QtCore import Qt,Signal
from PySide6.QtGui import QColor,QPainter,QPen
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QGridLayout

class ColorSwatch(QWidget):
    clicked=Signal(object); hovered=Signal(object); hoverLeft=Signal()
    def __init__(self,rgb,label,essential=False):
        super().__init__(); self.rgb=tuple(rgb); self.label=label; self.essential=essential; self.selected=False
        self.setFixedHeight(58); self.setMinimumWidth(170); self.setCursor(Qt.PointingHandCursor); self.setMouseTracking(True)
    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:self.clicked.emit(self.rgb)
    def enterEvent(self,e): self.hovered.emit(self.rgb); super().enterEvent(e)
    def leaveEvent(self,e): self.hoverLeft.emit(); super().leaveEvent(e)
    def paintEvent(self,e):
        p=QPainter(self); p.fillRect(self.rect().adjusted(0,0,-1,-1),QColor("#eaf4ff") if self.selected else QColor("white"))
        p.setPen(QPen(QColor("#2b7de9") if self.selected else QColor("#c9cfd7"),2 if self.selected else 1))
        p.drawRoundedRect(self.rect().adjusted(0,0,-1,-1),7,7)
        p.fillRect(8,8,42,42,QColor(*self.rgb)); p.setPen(QPen(QColor("#444"),1)); p.drawRect(8,8,42,42)
        p.setPen(QColor("#1f2329")); p.drawText(58,22,("★ " if self.essential else "")+self.label)
        p.setPen(QColor("#59616d")); p.drawText(58,43,f"RGB {self.rgb}")

class ManualPalettePanel(QWidget):
    colorSelected=Signal(object); colorHovered=Signal(object); colorHoverLeft=Signal()
    def __init__(self):
        super().__init__(); self.current=None; self.items=[]; self.layout=QVBoxLayout(self); self.layout.addStretch(1)
    def set_entries(self,entries):
        while self.layout.count():
            i=self.layout.takeAt(0); w=i.widget()
            if w:w.deleteLater()
        self.items=[]; grouped=OrderedDict()
        for e in entries: grouped.setdefault(e["group"],[]).append(e)
        for group,rows in grouped.items():
            lab=QLabel(group); lab.setStyleSheet("font-weight:700;font-size:13px;padding:5px 7px;background:#eef6ff;border:1px solid #c8ddf7;border-radius:6px;")
            self.layout.addWidget(lab)
            grid=QGridLayout(); grid.setSpacing(5)
            for i,e in enumerate(rows):
                sw=ColorSwatch(e["rgb"],e["label"],e.get("essential",False))
                sw.clicked.connect(self.select_color); sw.hovered.connect(self.colorHovered.emit); sw.hoverLeft.connect(self.colorHoverLeft.emit)
                self.items.append(sw); grid.addWidget(sw,i//2,i%2)
            self.layout.addLayout(grid)
        self.layout.addStretch(1)
        if self.current is not None:self.select_if_present(self.current)
    def select_color(self,rgb):
        self.current=tuple(rgb)
        for sw in self.items: sw.selected=(sw.rgb==self.current); sw.update()
        self.colorSelected.emit(self.current)
    def select_if_present(self,rgb):
        rgb=tuple(rgb)
        for sw in self.items:
            if sw.rgb==rgb:self.select_color(rgb); return True
        return False
