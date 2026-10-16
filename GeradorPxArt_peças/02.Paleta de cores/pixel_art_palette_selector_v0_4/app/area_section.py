
from PySide6.QtCore import Signal, QEvent
from PySide6.QtWidgets import (
    QWidget,QVBoxLayout,QLabel,QGridLayout,QFrame,QHBoxLayout,QPushButton
)
from .color_card import ColorCard


class HoverTitle(QLabel):
    entered=Signal()
    left=Signal()

    def __init__(self,text):
        super().__init__(text)
        self.setMouseTracking(True)
        self.setStyleSheet("""
            QLabel {
                font-size:16px;
                font-weight:700;
                padding:8px 10px;
                background:#eef6ff;
                border:1px solid #b9d7f7;
                border-radius:6px;
            }
            QLabel:hover {
                background:#fff4bf;
                border:1px solid #e0b800;
            }
        """)

    def enterEvent(self,event):
        self.entered.emit()
        super().enterEvent(event)

    def leaveEvent(self,event):
        self.left.emit()
        super().leaveEvent(event)


class AreaSection(QFrame):
    hoverIn=Signal(object)
    hoverOut=Signal()
    colorToggled=Signal(object,object,bool)
    removeRequested=Signal(object)

    def __init__(self,area):
        super().__init__()
        self.area=area
        self.cards={}
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("QFrame{background:white;border:1px solid #d8d8d8;border-radius:8px;}")

        root=QVBoxLayout(self)
        head=QHBoxLayout()
        self.title=HoverTitle(area["name"])
        self.title.entered.connect(lambda:self.hoverIn.emit(self.area))
        self.title.left.connect(self.hoverOut.emit)
        head.addWidget(self.title,1)

        remove=QPushButton("Excluir área")
        remove.clicked.connect(lambda:self.removeRequested.emit(self.area))
        head.addWidget(remove)
        root.addLayout(head)

        meta=QLabel(
            f'{area["pixel_count"]:,} pixels selecionados • '
            f'{len(area["palette"])} cores/grupos exibidos'
        )
        meta.setStyleSheet("color:#666;border:none;")
        root.addWidget(meta)

        grid=QGridLayout()
        grid.setSpacing(8)
        cols=4
        for i,item in enumerate(area["palette"]):
            card=ColorCard(item)
            if item.rgb in area["selected"]:
                card.selected=True
                card.refresh()
            card.toggled.connect(
                lambda item,state,a=self.area:self.colorToggled.emit(a,item,state)
            )
            self.cards[item.rgb]=card
            grid.addWidget(card,i//cols,i%cols)

        root.addLayout(grid)
