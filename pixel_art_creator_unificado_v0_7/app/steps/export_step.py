
import hashlib
from pathlib import Path

import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QCheckBox, QFrame, QGridLayout,
    QScrollArea
)

from .base_step import BaseStep
from ..simplification_service import decode_png
from ..export_utils import create_export_bundle


EXPORT_ITEMS = [
    ("matrix","Matriz técnica 100×100"),
    ("preview","Preview ampliado 800×800"),
    ("grid","Imagem com grade"),
    ("pattern","Molde com códigos"),
    ("legend_png","Legenda PNG"),
    ("legend_json","Legenda JSON"),
    ("legend_csv","Legenda CSV"),
    ("legend_txt","Legenda TXT"),
]


class ExportItem(QFrame):
    def __init__(self,key,label):
        super().__init__()
        self.key=key
        self.setStyleSheet("""
            QFrame {
                background:white;
                border:1px solid #d5dbe4;
                border-radius:8px;
            }
        """)
        lay=QHBoxLayout(self)
        lay.setContentsMargins(10,8,10,8)
        self.check=QCheckBox(label)
        self.check.setChecked(True)
        lay.addWidget(self.check,1)
        self.status=QLabel("Pronto para exportar")
        self.status.setStyleSheet("color:#69717d;")
        lay.addWidget(self.status)


class ExportStep(BaseStep):
    def __init__(self,state):
        super().__init__(
            "8. Central de exportação",
            "Reúna e salve os arquivos finais do projeto em uma única pasta."
        )
        self.state=state
        self.arr=None
        self.items={}

        title_widget=self.layout.itemAt(0).widget()
        desc_widget=self.layout.itemAt(1).widget()
        if title_widget:
            title_widget.setStyleSheet("font-size:20px;font-weight:700;")
            title_widget.setMaximumHeight(34)
        if desc_widget:
            desc_widget.setStyleSheet("font-size:12px;color:#5b6470;")
            desc_widget.setMaximumHeight(30)

        self.layout.setContentsMargins(14,10,14,8)
        self.layout.setSpacing(7)

        top=QHBoxLayout()
        self.folder_btn=QPushButton("Escolher pasta")
        self.export_selected_btn=QPushButton("Exportar selecionados")
        self.export_all_btn=QPushButton("Exportar tudo")
        self.select_all_btn=QPushButton("Selecionar tudo")
        self.clear_btn=QPushButton("Limpar seleção")

        top.addWidget(self.folder_btn)
        top.addWidget(self.export_selected_btn)
        top.addWidget(self.export_all_btn)
        top.addStretch(1)
        top.addWidget(self.select_all_btn)
        top.addWidget(self.clear_btn)
        self.layout.addLayout(top)

        self.folder_label=QLabel("Pasta de destino: ainda não selecionada.")
        self.folder_label.setStyleSheet("font-size:11px;color:#59616d;")
        self.folder_label.setWordWrap(True)
        self.layout.addWidget(self.folder_label)

        self.source_label=QLabel("")
        self.source_label.setStyleSheet("font-size:11px;color:#59616d;")
        self.layout.addWidget(self.source_label)

        scroll=QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.layout.addWidget(scroll,1)

        body=QWidget()
        grid=QGridLayout(body)
        grid.setContentsMargins(2,2,2,2)
        grid.setSpacing(8)

        for i,(key,label) in enumerate(EXPORT_ITEMS):
            item=ExportItem(key,label)
            self.items[key]=item
            grid.addWidget(item,i//2,i%2)

        grid.setRowStretch((len(EXPORT_ITEMS)+1)//2,1)
        scroll.setWidget(body)

        self.summary=QLabel("Nenhuma exportação realizada nesta etapa.")
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet(
            "padding:10px;background:#f4f7fb;border:1px solid #d9e0e8;border-radius:8px;"
        )
        self.layout.addWidget(self.summary)

        self.folder_btn.clicked.connect(self.choose_folder)
        self.export_selected_btn.clicked.connect(self.export_selected)
        self.export_all_btn.clicked.connect(self.export_all)
        self.select_all_btn.clicked.connect(lambda:self.set_all(True))
        self.clear_btn.clicked.connect(lambda:self.set_all(False))

        self.refresh()

    def set_context(self,state):
        self.state=state
        self.refresh()

    def _manual_source_valid(self):
        edited=self.state.metadata.get("edited_100x100_png")
        if not edited:
            return False
        simplified=self.state.metadata.get("simplified_50_png") or ""
        expected=hashlib.sha256(simplified.encode("ascii")).hexdigest()
        return self.state.metadata.get("manual_source_signature")==expected

    def _source_png(self):
        if self._manual_source_valid():
            return self.state.metadata.get("edited_100x100_png"),"edição manual"
        return self.state.metadata.get("simplified_50_png"),"simplificação 50 cores"

    def _source_signature(self):
        payload,_=self._source_png()
        if not payload:
            return None
        return hashlib.sha256(payload.encode("ascii")).hexdigest()

    def refresh(self):
        payload,source_name=self._source_png()
        self.arr=decode_png(payload)

        if self.arr is None:
            self.source_label.setText("Sem matriz final 100×100 disponível.")
        else:
            colors=len(np.unique(self.arr.reshape(-1,3),axis=0))
            self.source_label.setText(
                f"Fonte atual: {source_name} • 100×100 • {colors} cores"
            )

        folder=self.state.metadata.get("export_directory")
        if folder:
            self.folder_label.setText(f"Pasta de destino: {folder}")
        else:
            self.folder_label.setText("Pasta de destino: ainda não selecionada.")

        manifest=self.state.metadata.get("export_manifest",[])
        source_sig=self.state.metadata.get("export_source_signature")
        current_sig=self._source_signature()

        if manifest and source_sig==current_sig:
            self.summary.setText(
                f"Última exportação válida: {len(manifest)} arquivo(s) registrados."
            )
        elif manifest:
            self.summary.setText(
                "A matriz final mudou desde a última exportação. Gere novamente os arquivos finais."
            )
        else:
            self.summary.setText("Nenhuma exportação realizada nesta etapa.")

        self._refresh_actions()

    def _refresh_actions(self):
        ready=(
            self.arr is not None
            and self.state.approvals.get("pattern",False)
        )
        self.export_selected_btn.setEnabled(ready)
        self.export_all_btn.setEnabled(ready)

    def choose_folder(self):
        start=self.state.metadata.get("export_directory","")
        path=QFileDialog.getExistingDirectory(
            self,
            "Escolher pasta de exportação",
            start
        )
        if not path:
            return
        self.state.metadata["export_directory"]=path
        self.state.dirty=True
        self.folder_label.setText(f"Pasta de destino: {path}")

    def set_all(self,value):
        for item in self.items.values():
            item.check.setChecked(bool(value))

    def _ensure_folder(self):
        folder=self.state.metadata.get("export_directory")
        if folder:
            return folder
        self.choose_folder()
        return self.state.metadata.get("export_directory")

    def _selected_keys(self):
        return {
            key
            for key,item in self.items.items()
            if item.check.isChecked()
        }

    def export_selected(self):
        keys=self._selected_keys()
        if not keys:
            QMessageBox.information(
                self,
                "Nada selecionado",
                "Selecione pelo menos um arquivo para exportar."
            )
            return
        self._export(keys)

    def export_all(self):
        self.set_all(True)
        self._export({key for key,_ in EXPORT_ITEMS})

    def _export(self,keys):
        if self.arr is None:
            QMessageBox.information(
                self,
                "Sem matriz final",
                "Conclua as etapas anteriores antes de exportar."
            )
            return

        if not self.state.approvals.get("pattern",False):
            QMessageBox.information(
                self,
                "Molde ainda não aprovado",
                "Aprove a etapa Molde e Legenda antes da exportação final."
            )
            return

        folder=self._ensure_folder()
        if not folder:
            return

        try:
            project_name=(
                Path(self.state.project_file).stem
                if self.state.project_file
                else self.state.project_name
            )
            manifest=create_export_bundle(
                self.arr,
                Path(folder),
                project_name,
                selected_keys=keys,
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro na exportação",
                str(e)
            )
            return

        self.state.metadata["export_manifest"]=manifest
        self.state.metadata["export_source_signature"]=self._source_signature()
        self.state.metadata["export_directory"]=str(folder)
        self.state.unapprove("export")
        self.state.dirty=True

        exported_keys={row["key"] for row in manifest}

        for key,item in self.items.items():
            if key in exported_keys:
                item.status.setText("Exportado")
                item.status.setStyleSheet("color:#18794e;font-weight:700;")
            else:
                item.status.setText("Não exportado")
                item.status.setStyleSheet("color:#69717d;")

        self.summary.setText(
            f"Exportação concluída em:\n{folder}\n"
            f"{len(manifest)} arquivo(s) registrados, incluindo o manifesto."
        )

        QMessageBox.information(
            self,
            "Exportação concluída",
            f"Arquivos salvos em:\n{folder}"
        )

    def is_ready(self):
        manifest=self.state.metadata.get("export_manifest",[])
        return bool(
            manifest
            and self.state.metadata.get("export_source_signature")
            == self._source_signature()
        )
