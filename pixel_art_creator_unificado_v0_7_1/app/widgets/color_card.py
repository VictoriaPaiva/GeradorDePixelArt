
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QMouseEvent
from PySide6.QtWidgets import QFrame,QHBoxLayout,QLabel,QVBoxLayout,QWidget


class Swatch(QWidget):
    def __init__(self,rgb):
        super().__init__()
        self.rgb=rgb
        self.setFixedSize(54,54)

    def paintEvent(self,event):
        p=QPainter(self)
        p.fillRect(self.rect(),QColor(*self.rgb))
        p.setPen(QPen(QColor(40,40,40),1))
        p.drawRect(self.rect().adjusted(0,0,-1,-1))


class ColorCard(QFrame):
    toggled=Signal(object,bool)
    hovered=Signal(object)
    hoverLeft=Signal()

    def __init__(self,item, selectable=True):
        super().__init__()
        self.item=item
        self.selectable=selectable
        self.selected=False
        self.setCursor(Qt.PointingHandCursor if selectable else Qt.ArrowCursor)
        self.setMouseTracking(True)
        self.setMinimumHeight(80)

        root=QHBoxLayout(self)
        root.setContentsMargins(8,8,8,8)
        root.addWidget(Swatch(item.rgb))

        box=QVBoxLayout()
        t=QLabel(f"{item.code}   {item.hex}")
        t.setStyleSheet("font-weight:700;")
        box.addWidget(t)
        box.addWidget(QLabel(f"RGB {item.rgb}"))
        box.addWidget(QLabel(f"{item.count:,} px • {item.percent:.3f}%"))
        m=QLabel(f"{item.member_count} nuances agrupadas")
        m.setStyleSheet("color:#666;")
        box.addWidget(m)
        root.addLayout(box,1)
        self.refresh()

    def refresh(self):
        if self.selected:
            self.setStyleSheet("""
                QFrame {background:#e8f4ff;border:2px solid #2b7de9;border-radius:8px;}
                QLabel {border:none;background:transparent;}
            """)
        else:
            self.setStyleSheet("""
                QFrame {background:white;border:1px solid #ccc;border-radius:8px;}
                QFrame:hover {border:2px solid #7aaef5;}
                QLabel {border:none;background:transparent;}
            """)

    def enterEvent(self,event):
        self.hovered.emit(self.item)
        super().enterEvent(event)

    def leaveEvent(self,event):
        self.hoverLeft.emit()
        super().leaveEvent(event)

    def mousePressEvent(self,event:QMouseEvent):
        if self.selectable and event.button()==Qt.LeftButton:
            self.selected=not self.selected
            self.refresh()
            self.toggled.emit(self.item,self.selected)
        super().mousePressEvent(event)
