
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

        self.counter=QLabel(f'Selecionadas: {len(area.get("selected",{}))}')
        self.counter.setStyleSheet("font-weight:700;color:#2b7de9;border:none;")
        head.addWidget(self.counter)

        recalc=QPushButton("Recalcular paleta")
        recalc.clicked.connect(lambda:self.recalcRequested.emit(self.area))
        head.addWidget(recalc)

        delpal=QPushButton("Excluir paleta")
        delpal.clicked.connect(lambda:self.deletePaletteRequested.emit(self.area))
        head.addWidget(delpal)

        delarea=QPushButton("Excluir área")
        delarea.clicked.connect(lambda:self.deleteAreaRequested.emit(self.area))
        head.addWidget(delarea)
        root.addLayout(head)

        self.content=QWidget()
        cl=QVBoxLayout(self.content)
        cl.setContentsMargins(4,4,4,4)

        palette=area.get("palette",[])
        selected=area.get("selected",{})

        if palette:
            # Selected colors always appear first.
            selected_items=[item for item in palette if item.rgb in selected]
            other_items=[item for item in palette if item.rgb not in selected]

            if selected_items:
                selected_title=QLabel(f"★ CORES ESSENCIAIS ({len(selected_items)})")
                selected_title.setStyleSheet(
                    "font-weight:700;padding:6px;background:#eef7ff;"
                    "border:1px solid #b8d8f6;border-radius:5px;"
                )
                cl.addWidget(selected_title)
                grid_sel=QGridLayout()
                grid_sel.setSpacing(8)
                cols=4
                for i,item in enumerate(selected_items):
                    card=self._make_card(item)
                    grid_sel.addWidget(card,i//cols,i%cols)
                cl.addLayout(grid_sel)

                remaining_title=QLabel("OUTRAS CORES")
                remaining_title.setStyleSheet(
                    "font-weight:700;margin-top:6px;padding:5px;border:none;color:#555;"
                )
                cl.addWidget(remaining_title)

            grid=QGridLayout()
            grid.setSpacing(8)
            cols=4
            for i,item in enumerate(other_items):
                card=self._make_card(item)
                grid.addWidget(card,i//cols,i%cols)
            cl.addLayout(grid)

        else:
            empty=QLabel("Paleta excluída. Clique em “Recalcular paleta” para gerar novamente.")
            empty.setStyleSheet("color:#777;padding:10px;border:none;")
            cl.addWidget(empty)

        root.addWidget(self.content)
        self.content.setVisible(self.expanded)

    def _make_card(self,item):
        card=ColorCard(item)
        if item.rgb in self.area.get("selected",{}):
            card.selected=True
            card.refresh()

        card.toggled.connect(
            lambda item,state,a=self.area:self.colorToggled.emit(a,item,state)
        )
        card.hovered.connect(
            lambda item,a=self.area:self.colorHover.emit(a,item)
        )
        card.hoverLeft.connect(self.colorHoverOut.emit)
        return card

    def toggle_collapsed(self):
        self.expanded=not self.expanded
        self.area["expanded"]=self.expanded
        self.content.setVisible(self.expanded)
        self.toggle_btn.setText("▼" if self.expanded else "▶")
