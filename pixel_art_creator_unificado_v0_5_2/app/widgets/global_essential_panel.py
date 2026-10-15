
import math
import numpy as np
from skimage.color import rgb2lab

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QGridLayout, QPushButton
)


def _rgb_to_lab(rgb):
    arr=np.array(rgb,dtype=float).reshape(1,1,3)/255.0
    return rgb2lab(arr).reshape(3)


def _color_sort_key(rgb):
    L,a,b=_rgb_to_lab(rgb)
    chroma=(a*a+b*b)**0.5

    # Neutrals together from dark to light.
    if chroma < 10:
        return (0, L, 0)

    # Chromatic colors ordered by hue, then lightness.
    hue=(math.atan2(b,a)+2*math.pi)%(2*math.pi)
    return (1, hue, L)


class MiniSwatch(QWidget):
    def __init__(self,rgb):
        super().__init__()
        self.rgb=tuple(rgb)
        self.setFixedSize(48,48)

    def paintEvent(self,event):
        p=QPainter(self)
        p.fillRect(self.rect(),QColor(*self.rgb))
        p.setPen(QPen(QColor(45,45,45),1))
        p.drawRect(self.rect().adjusted(0,0,-1,-1))


class GlobalEssentialCard(QFrame):
    removeRequested=Signal(object)
    hovered=Signal(object)
    hoverLeft=Signal()

    def __init__(self,entry):
        super().__init__()
        self.entry=entry
        self.setMouseTracking(True)
        self.setMinimumHeight(72)
        self.setStyleSheet("""
            QFrame {
                background:white;
                border:1px solid #cfd5dd;
                border-radius:8px;
            }
            QFrame:hover {
                border:2px solid #2b7de9;
                background:#f7fbff;
            }
            QLabel {border:none;background:transparent;}
            QPushButton {
                border:1px solid #d7a2a2;
                background:#fff8f8;
                border-radius:5px;
                padding:3px 6px;
            }
            QPushButton:hover {background:#ffeaea;}
        """)

        root=QHBoxLayout(self)
        root.setContentsMargins(7,7,7,7)
        root.addWidget(MiniSwatch(entry["rgb"]))

        texts=QVBoxLayout()
        title=QLabel(f'{entry["hex"]}  •  RGB {entry["rgb"]}')
        title.setStyleSheet("font-weight:700;")
        texts.addWidget(title)

        areas=", ".join(entry["areas"])
        area_label=QLabel(f"Áreas: {areas}")
        area_label.setWordWrap(True)
        area_label.setStyleSheet("color:#59616d;")
        texts.addWidget(area_label)

        if entry.get("nearest_hex") and entry.get("nearest_delta") is not None:
            d=entry["nearest_delta"]
            near=QLabel(
                f'Cor mais próxima: {entry["nearest_hex"]}  •  ΔE {d:.1f}'
            )
            if d <= 6:
                near.setStyleSheet("color:#9a6500;font-weight:700;")
                near.setToolTip(
                    "Essa cor é muito próxima de outra cor essencial. "
                    "Vale avaliar se as duas são realmente necessárias."
                )
            else:
                near.setStyleSheet("color:#707780;")
            texts.addWidget(near)

        root.addLayout(texts,1)

        remove=QPushButton("Remover")
        remove.setToolTip(
            "Remover este RGB do conjunto de cores essenciais em todas as áreas"
        )
        remove.clicked.connect(lambda:self.removeRequested.emit(self.entry["rgb"]))
        root.addWidget(remove)

    def enterEvent(self,event):
        self.hovered.emit(self.entry)
        super().enterEvent(event)

    def leaveEvent(self,event):
        self.hoverLeft.emit()
        super().leaveEvent(event)


class GlobalEssentialPanel(QFrame):
    removeRequested=Signal(object)
    hovered=Signal(object)
    hoverLeft=Signal()

    def __init__(self,workspace):
        super().__init__()
        self.workspace=workspace

        self.setStyleSheet("""
            GlobalEssentialPanel {
                background:#f8fbff;
                border:1px solid #afcdeb;
                border-radius:10px;
            }
        """)

        self.root=QVBoxLayout(self)
        self.root.setContentsMargins(10,10,10,10)

        title=QLabel("★ CORES ESSENCIAIS CONSOLIDADAS")
        title.setStyleSheet(
            "font-size:16px;font-weight:700;color:#155a9c;border:none;"
        )
        self.root.addWidget(title)

        self.summary=QLabel()
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet("border:none;color:#4e5966;")
        self.root.addWidget(self.summary)

        self.grid_widget=QWidget()
        self.grid=QGridLayout(self.grid_widget)
        self.grid.setContentsMargins(0,4,0,0)
        self.grid.setSpacing(8)
        self.root.addWidget(self.grid_widget)

        self.rebuild()

    def set_workspace(self,workspace):
        self.workspace=workspace
        self.rebuild()

    def _entries(self):
        combined={}
        selections=0

        for area in self.workspace.areas:
            for rgb,item in area.get("selected",{}).items():
                selections += 1
                if rgb not in combined:
                    combined[rgb]={
                        "rgb":tuple(rgb),
                        "hex":"#{:02X}{:02X}{:02X}".format(*rgb),
                        "areas":[],
                        "item":item,
                    }
                combined[rgb]["areas"].append(area["name"])

        entries=list(combined.values())
        entries.sort(key=lambda e:_color_sort_key(e["rgb"]))

        if len(entries)>1:
            labs=np.array([_rgb_to_lab(e["rgb"]) for e in entries])
            for i,e in enumerate(entries):
                d=np.linalg.norm(labs-labs[i],axis=1)
                d[i]=np.inf
                j=int(np.argmin(d))
                e["nearest_delta"]=float(d[j])
                e["nearest_hex"]=entries[j]["hex"]
        else:
            for e in entries:
                e["nearest_delta"]=None
                e["nearest_hex"]=None

        return entries,selections

    def rebuild(self):
        while self.grid.count():
            item=self.grid.takeAt(0)
            w=item.widget()
            if w:
                w.deleteLater()

        entries,selections=self._entries()

        self.summary.setText(
            f"Seleções por área: {selections}  •  RGBs únicos: {len(entries)}. "
            "As cores são organizadas por proximidade visual para facilitar a revisão "
            "de tons redundantes. ΔE baixo indica cores muito semelhantes."
        )

        if not entries:
            empty=QLabel(
                "Nenhuma cor essencial selecionada ainda. "
                "Selecione cores nas paletas das áreas abaixo."
            )
            empty.setWordWrap(True)
            empty.setStyleSheet(
                "color:#747b84;padding:8px;border:none;"
            )
            self.grid.addWidget(empty,0,0)
            return

        cols=3
        for i,entry in enumerate(entries):
            card=GlobalEssentialCard(entry)
            card.removeRequested.connect(self.removeRequested.emit)
            card.hovered.connect(self.hovered.emit)
            card.hoverLeft.connect(self.hoverLeft.emit)
            self.grid.addWidget(card,i//cols,i%cols)
