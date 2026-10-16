
from pathlib import Path
from PIL import Image

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QPushButton, QFileDialog, QLabel, QHBoxLayout, QMessageBox
)

from .base_step import BaseStep
from ..widgets.image_preview import ImagePreview


class AIStep(BaseStep):
    imageChanged = Signal(str)

    def __init__(self, state):
        super().__init__(
            "2. Pixel Art via IA",
            "Nesta primeira versão estrutural, a integração direta com IA ainda não foi "
            "conectada. Para testar o restante do fluxo, carregue aqui uma Pixel Art já gerada. "
            "Na integração final esta tela terá Gerar novamente / Aprovar."
        )
        self.state = state

        row = QHBoxLayout()
        self.import_btn = QPushButton("Importar Pixel Art gerada")
        row.addWidget(self.import_btn)
        row.addStretch(1)
        self.layout.addLayout(row)

        self.preview = ImagePreview("Nenhuma Pixel Art importada")
        self.layout.addWidget(self.preview, 1)

        self.info = QLabel("Etapa preparada para receber o serviço de IA.")
        self.info.setStyleSheet("color:#59616d;")
        self.layout.addWidget(self.info)

        self.import_btn.clicked.connect(self.choose_image)
        self.refresh()

    def choose_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Pixel Art", "",
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

        self.state.ai_image_path = path
        self.state.unapprove("ai")
        self.state.invalidate_after("ai")
        self.state.dirty = True
        self.imageChanged.emit(path)
        self.refresh()

    def refresh(self):
        path = self.state.ai_image_path
        if path and Path(path).exists():
            self.preview.set_image(path)
            self.info.setText(f"Pixel Art carregada: {Path(path).name}")
        else:
            self.preview.clear_image("Nenhuma Pixel Art importada")
            self.info.setText("Etapa preparada para receber o serviço de IA.")
