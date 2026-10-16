
from pathlib import Path
from PIL import Image

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QPushButton, QFileDialog, QLabel, QHBoxLayout, QMessageBox
)

from .base_step import BaseStep
from ..widgets.image_preview import ImagePreview


class InputStep(BaseStep):
    sourceChanged = Signal(str)

    def __init__(self, state):
        super().__init__(
            "1. Imagem de entrada",
            "Selecione a imagem original que será usada como referência. "
            "O arquivo original não é modificado."
        )
        self.state = state

        row = QHBoxLayout()
        self.open_btn = QPushButton("Selecionar imagem")
        self.replace_btn = QPushButton("Substituir imagem")
        self.replace_btn.setEnabled(False)
        row.addWidget(self.open_btn)
        row.addWidget(self.replace_btn)
        row.addStretch(1)
        self.layout.addLayout(row)

        self.preview = ImagePreview()
        self.layout.addWidget(self.preview, 1)

        self.info = QLabel("Aguardando imagem.")
        self.info.setStyleSheet("color:#59616d;")
        self.layout.addWidget(self.info)

        self.open_btn.clicked.connect(self.choose_image)
        self.replace_btn.clicked.connect(self.choose_image)

        self.refresh()

    def choose_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar imagem de referência",
            "",
            "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not path:
            return

        try:
            im = Image.open(path)
            im.verify()
        except Exception as e:
            QMessageBox.critical(self, "Imagem inválida", str(e))
            return

        self.state.source_image_path = path
        self.state.unapprove("input")
        self.state.invalidate_after("input")
        self.state.dirty = True
        self.sourceChanged.emit(path)
        self.refresh()

    def refresh(self):
        path = self.state.source_image_path
        if path and Path(path).exists():
            self.preview.set_image(path)
            try:
                im = Image.open(path)
                self.info.setText(
                    f"{Path(path).name} • {im.width}×{im.height} • "
                    f"{im.mode}"
                )
            except Exception:
                self.info.setText(Path(path).name)
            self.replace_btn.setEnabled(True)
        else:
            self.preview.clear_image()
            self.info.setText("Aguardando imagem.")
            self.replace_btn.setEnabled(False)
