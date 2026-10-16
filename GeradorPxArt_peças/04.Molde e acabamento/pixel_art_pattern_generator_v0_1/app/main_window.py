
import csv,json
from pathlib import Path
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage,QPixmap
from PySide6.QtWidgets import (
    QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,
    QFileDialog,QSplitter,QScrollArea,QMessageBox,QTableWidget,
    QTableWidgetItem,QHeaderView
)

from .pattern_utils import (
    build_legend,validate_matrix,render_code_pattern,render_legend
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Art Pattern Generator v0.1")
        self.resize(1550,950)

        self.arr=None
        self.image_path=None
        self.entries=[]
        self.color_to_code={}
        self.pattern_img=None
        self.legend_img=None

        self._build()

    def _build(self):
        rootw=QWidget()
        self.setCentralWidget(rootw)
        root=QVBoxLayout(rootw)

        top=QHBoxLayout()
        self.open_btn=QPushButton("Abrir imagem final")
        self.generate_btn=QPushButton("Gerar legenda + molde")
        self.save_pattern_btn=QPushButton("Salvar molde com códigos")
        self.save_legend_btn=QPushButton("Salvar legenda PNG")
        self.export_json_btn=QPushButton("Exportar JSON")
        self.export_csv_btn=QPushButton("Exportar CSV")
        self.export_txt_btn=QPushButton("Exportar TXT")

        for b in [
            self.open_btn,self.generate_btn,self.save_pattern_btn,self.save_legend_btn,
            self.export_json_btn,self.export_csv_btn,self.export_txt_btn
        ]:
            top.addWidget(b)

        top.addStretch(1)
        self.status=QLabel("Nenhuma imagem carregada")
        top.addWidget(self.status)
        root.addLayout(top)

        split=QSplitter(Qt.Horizontal)
        root.addWidget(split,1)

        # LEFT preview
        left=QWidget()
        ll=QVBoxLayout(left)
        title=QLabel("MOLDE")
        title.setStyleSheet("font-size:18px;font-weight:700;")
        ll.addWidget(title)

        self.preview=QLabel("Abra a imagem final 100×100.")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("background:#f5f5f5;border:1px solid #ccc;")
        self.preview.setMinimumSize(650,650)

        sc=QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(self.preview)
        ll.addWidget(sc,1)

        # RIGHT legend table
        right=QWidget()
        rl=QVBoxLayout(right)
        title2=QLabel("LEGENDA")
        title2.setStyleSheet("font-size:18px;font-weight:700;")
        rl.addWidget(title2)

        self.table=QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(
            ["Código","Cor","HEX","RGB","Células","%"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        rl.addWidget(self.table,1)

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([950,600])

        self.open_btn.clicked.connect(self.open_image)
        self.generate_btn.clicked.connect(self.generate)
        self.save_pattern_btn.clicked.connect(self.save_pattern)
        self.save_legend_btn.clicked.connect(self.save_legend)
        self.export_json_btn.clicked.connect(self.export_json)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_txt_btn.clicked.connect(self.export_txt)

    def open_image(self):
        path,_=QFileDialog.getOpenFileName(
            self,"Abrir imagem final","","PNG (*.png);;Imagens (*.png *.jpg *.jpeg *.webp)"
        )
        if not path:return

        try:
            im=Image.open(path).convert("RGB")
            self.arr=np.array(im,dtype=np.uint8)
            self.image_path=path
        except Exception as e:
            QMessageBox.critical(self,"Erro",str(e))
            return

        ok,msg=validate_matrix(self.arr)
        if not ok:
            QMessageBox.critical(self,"Imagem inválida",msg)
            return

        self.status.setText(
            f"{Path(path).name} • {im.width}×{im.height} • "
            f"{len(np.unique(self.arr.reshape(-1,3),axis=0))} cores"
        )
        if im.size!=(100,100):
            QMessageBox.information(self,"Atenção",msg)

        self.show_source_preview()

    def show_source_preview(self):
        if self.arr is None:return
        im=Image.fromarray(self.arr).resize((700,700),Image.Resampling.NEAREST)
        self._show_pil(im)

    def generate(self):
        if self.arr is None:
            QMessageBox.information(self,"Sem imagem","Abra uma imagem primeiro.")
            return

        self.entries,self.color_to_code=build_legend(self.arr)

        self.pattern_img=render_code_pattern(
            self.arr,self.color_to_code,cell_size=34
        )
        self.legend_img=render_legend(self.entries)

        self.populate_table()

        # Show a readable scaled preview rather than full huge pattern.
        preview=self.pattern_img.copy()
        preview.thumbnail((900,900),Image.Resampling.NEAREST)
        self._show_pil(preview)

        self.status.setText(
            f"Molde gerado • {self.arr.shape[1]}×{self.arr.shape[0]} • "
            f"{len(self.entries)} cores • {self.arr.shape[0]*self.arr.shape[1]} células"
        )

    def populate_table(self):
        self.table.setRowCount(len(self.entries))
        for r,e in enumerate(self.entries):
            self.table.setItem(r,0,QTableWidgetItem(e.code))

            color_item=QTableWidgetItem("")
            color_item.setBackground(
                __import__("PySide6").QtGui.QColor(*e.rgb)
            )
            self.table.setItem(r,1,color_item)

            self.table.setItem(r,2,QTableWidgetItem(e.hex))
            self.table.setItem(r,3,QTableWidgetItem(str(e.rgb)))
            self.table.setItem(r,4,QTableWidgetItem(str(e.count)))
            self.table.setItem(r,5,QTableWidgetItem(f"{e.percent:.2f}%"))

    def _ensure_generated(self):
        if self.pattern_img is None:
            QMessageBox.information(
                self,"Ainda não gerado",
                "Clique em “Gerar legenda + molde” primeiro."
            )
            return False
        return True

    def save_pattern(self):
        if not self._ensure_generated():return
        path,_=QFileDialog.getSaveFileName(
            self,"Salvar molde","molde_pixel_art_100x100.png","PNG (*.png)"
        )
        if not path:return
        self.pattern_img.save(path)
        QMessageBox.information(self,"Salvo",path)

    def save_legend(self):
        if not self._ensure_generated():return
        path,_=QFileDialog.getSaveFileName(
            self,"Salvar legenda","legenda_cores.png","PNG (*.png)"
        )
        if not path:return
        self.legend_img.save(path)
        QMessageBox.information(self,"Salvo",path)

    def _rows(self):
        return [
            {
                "code":e.code,
                "hex":e.hex,
                "rgb":list(e.rgb),
                "cells":e.count,
                "percent":e.percent
            }
            for e in self.entries
        ]

    def export_json(self):
        if not self._ensure_generated():return
        path,_=QFileDialog.getSaveFileName(
            self,"Exportar JSON","legenda_cores.json","JSON (*.json)"
        )
        if not path:return
        with open(path,"w",encoding="utf-8") as f:
            json.dump(self._rows(),f,ensure_ascii=False,indent=2)
        QMessageBox.information(self,"Exportado",path)

    def export_csv(self):
        if not self._ensure_generated():return
        path,_=QFileDialog.getSaveFileName(
            self,"Exportar CSV","legenda_cores.csv","CSV (*.csv)"
        )
        if not path:return
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f)
            w.writerow(["code","hex","r","g","b","cells","percent"])
            for e in self.entries:
                w.writerow([
                    e.code,e.hex,*e.rgb,e.count,f"{e.percent:.6f}"
                ])
        QMessageBox.information(self,"Exportado",path)

    def export_txt(self):
        if not self._ensure_generated():return
        path,_=QFileDialog.getSaveFileName(
            self,"Exportar TXT","legenda_cores.txt","TXT (*.txt)"
        )
        if not path:return

        lines=[
            "LEGENDA DE CORES",
            "="*60,
            f"Matriz: {self.arr.shape[1]}x{self.arr.shape[0]}",
            f"Total de células: {self.arr.shape[0]*self.arr.shape[1]}",
            f"Total de cores: {len(self.entries)}",
            ""
        ]

        for e in self.entries:
            lines.append(
                f"{e.code} | {e.hex} | RGB{e.rgb} | "
                f"{e.count} células | {e.percent:.2f}%"
            )

        with open(path,"w",encoding="utf-8") as f:
            f.write("\n".join(lines))
        QMessageBox.information(self,"Exportado",path)

    def _show_pil(self,im):
        data=im.tobytes("raw","RGB")
        q=QImage(data,im.width,im.height,im.width*3,QImage.Format_RGB888)
        pix=QPixmap.fromImage(q.copy())
        self.preview.setPixmap(pix)
        self.preview.resize(pix.size())
