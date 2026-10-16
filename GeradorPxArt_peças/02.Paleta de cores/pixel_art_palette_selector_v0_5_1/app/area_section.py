
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QWidget,QGridLayout
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
                font-size:16px;font-weight:700;padding:8px 10px;
                background:#eef6ff;border:1px solid #b9d7f7;border-radius:6px;
            }
            QLabel:hover {
                background:#fff4bf;border:1px solid #e0b800;
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
    colorHover=Signal(object,object)
    colorHoverOut=Signal()
    deletePaletteRequested=Signal(object)
    deleteAreaRequested=Signal(object)
    recalcRequested=Signal(object)

    def __init__(self,area):
        super().__init__()
        self.area=area
        self.cards={}
        self.expanded=area.get("expanded",True)

        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("QFrame{background:white;border:1px solid #d8d8d8;border-radius:8px;}")

        root=QVBoxLayout(self)

        head=QHBoxLayout()

        self.toggle_btn=QPushButton("▼" if self.expanded else "▶")
        self.toggle_btn.setFixedWidth(34)
        self.toggle_btn.clicked.connect(self.toggle_collapsed)
        head.addWidget(self.toggle_btn)

        self.title=HoverTitle(area["name"])
        self.title.entered.connect(lambda:self.hoverIn.emit(self.area))
        self.title.left.connect(self.hoverOut.emit)
        head.addWidget(self.title,1)

        self.recalc_btn=QPushButton("Recalcular paleta")
        self.recalc_btn.clicked.connect(lambda:self.recalcRequested.emit(self.area))
        head.addWidget(self.recalc_btn)

        self.delete_palette_btn=QPushButton("Excluir paleta")
        self.delete_palette_btn.clicked.connect(lambda:self.deletePaletteRequested.emit(self.area))
        head.addWidget(self.delete_palette_btn)

        self.delete_area_btn=QPushButton("Excluir área")
        self.delete_area_btn.clicked.connect(lambda:self.deleteAreaRequested.emit(self.area))
        head.addWidget(self.delete_area_btn)

        root.addLayout(head)

        self.content=QWidget()
        content_l=QVBoxLayout(self.content)
        content_l.setContentsMargins(4,4,4,4)

        meta=QLabel(
            f'{area["pixel_count"]:,} pixels na área • '
            f'{len(area.get("palette",[]))} cores/grupos exibidos • '
            f'{len(area.get("selected",{}))} essenciais'
        )
        meta.setStyleSheet("color:#666;border:none;")
        content_l.addWidget(meta)

        if area.get("palette"):
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
                card.hovered.connect(
                    lambda item,a=self.area:self.colorHover.emit(a,item)
                )
                card.hoverLeft.connect(self.colorHoverOut.emit)

                self.cards[item.rgb]=card
                grid.addWidget(card,i//cols,i%cols)
            content_l.addLayout(grid)
        else:
            empty=QLabel("Paleta excluída. Clique em “Recalcular paleta” para gerar novamente.")
            empty.setStyleSheet("color:#777;padding:10px;border:none;")
            content_l.addWidget(empty)

        root.addWidget(self.content)
        self.content.setVisible(self.expanded)

    def toggle_collapsed(self):
        self.expanded=not self.expanded
        self.area["expanded"]=self.expanded
        self.content.setVisible(self.expanded)
        self.toggle_btn.setText("▼" if self.expanded else "▶")
