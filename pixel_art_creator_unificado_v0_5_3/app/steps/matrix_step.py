
from pathlib import Path

import numpy as np
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QFileDialog, QMessageBox, QCheckBox, QFrame
)

from .base_step import BaseStep
from ..widgets.image_preview import ImagePreview
from ..widgets.matrix_canvas import MatrixCanvas
from ..matrix_service import (
    image_to_matrix_100,
    encode_matrix_png,
    decode_matrix_png,
    enlarged_preview,
)


class MatrixStep(BaseStep):
    def __init__(self, state):
        super().__init__(
            "4. Matriz lógica 100×100",
            "Converta a Pixel Art aprovada em 10.000 células reais antes de alterar a paleta de cores."
        )
        self.state = state
        self.matrix = None

        # Compact heading like the approved palette screen.
        title_widget = self.layout.itemAt(0).widget()
        desc_widget = self.layout.itemAt(1).widget()
        if title_widget:
            title_widget.setStyleSheet("font-size:20px;font-weight:700;")
            title_widget.setMaximumHeight(34)
        if desc_widget:
            desc_widget.setStyleSheet("font-size:12px;color:#5b6470;")
            desc_widget.setMaximumHeight(30)

        self.layout.setContentsMargins(14,10,14,8)
        self.layout.setSpacing(7)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(7)

        self.generate_btn = QPushButton("Gerar matriz 100×100")
        self.generate_btn.setToolTip(
            "Gerar ou regerar a matriz técnica 100×100 usando a Pixel Art aprovada"
        )

        self.grid_check = QCheckBox("Mostrar grade")
        self.grid_check.setToolTip(
            "Mostrar divisórias apenas no preview. A grade não altera os RGBs da matriz."
        )

        self.save_matrix_btn = QPushButton("Salvar matriz")
        self.save_matrix_btn.setToolTip(
            "Salvar PNG técnico real 100×100 — arquivo recomendado para etapas posteriores"
        )

        self.save_preview_btn = QPushButton("Salvar preview")
        self.save_preview_btn.setToolTip(
            "Salvar uma versão ampliada por nearest-neighbor para visualização"
        )

        toolbar.addWidget(self.generate_btn)
        toolbar.addWidget(self.grid_check)
        toolbar.addStretch(1)
        toolbar.addWidget(self.save_matrix_btn)
        toolbar.addWidget(self.save_preview_btn)

        self.layout.addLayout(toolbar)

        self.method_info = QLabel(
            "Método: cada célula usa um RGB real existente na sua região de origem, "
            "escolhido pela proximidade com a mediana local. Sem interpolação e sem cor média inventada."
        )
        self.method_info.setWordWrap(True)
        self.method_info.setStyleSheet(
            "font-size:11px;color:#59616d;"
        )
        self.layout.addWidget(self.method_info)

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        self.layout.addWidget(split, 1)

        # Source
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0,0,5,0)
        ll.setSpacing(4)

        source_title = QLabel("PIXEL ART APROVADA")
        source_title.setStyleSheet("font-size:17px;font-weight:700;")
        ll.addWidget(source_title)

        self.source_preview = ImagePreview(
            "A Pixel Art aprovada será exibida aqui."
        )
        self.source_preview.setMinimumSize(320, 320)
        ll.addWidget(self.source_preview, 1)

        self.source_info = QLabel("")
        self.source_info.setStyleSheet("font-size:11px;color:#59616d;")
        self.source_info.setMaximumHeight(20)
        ll.addWidget(self.source_info)

        # Matrix
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(5,0,0,0)
        rl.setSpacing(4)

        matrix_title = QLabel("MATRIZ 100×100")
        matrix_title.setStyleSheet("font-size:17px;font-weight:700;")
        rl.addWidget(matrix_title)

        self.matrix_canvas = MatrixCanvas()
        rl.addWidget(self.matrix_canvas, 1)

        self.matrix_info = QLabel("Matriz ainda não gerada.")
        self.matrix_info.setStyleSheet("font-size:11px;color:#59616d;")
        self.matrix_info.setMaximumHeight(20)
        rl.addWidget(self.matrix_info)

        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 1)
        split.setSizes([750, 750])

        self.generate_btn.clicked.connect(self.generate)
        self.grid_check.toggled.connect(self.matrix_canvas.set_grid)
        self.save_matrix_btn.clicked.connect(self.save_matrix)
        self.save_preview_btn.clicked.connect(self.save_preview)

        self.refresh()

    def set_context(self, state):
        self.state = state
        self.refresh()

    def refresh(self):
        source = self.state.ai_image_path

        if source and Path(source).exists():
            self.source_preview.set_image(source)
            try:
                im = Image.open(source)
                self.source_info.setText(
                    f"{Path(source).name} • {im.width}×{im.height}"
                )
            except Exception:
                self.source_info.setText(Path(source).name)
        else:
            self.source_preview.clear_image(
                "A Pixel Art aprovada será exibida aqui."
            )
            self.source_info.setText("Sem Pixel Art aprovada.")

        stored_source = self.state.metadata.get("matrix_source_path")
        stored_png = self.state.metadata.get("matrix_100x100_png")

        # Do not reuse a matrix if its source image changed.
        if (
            stored_png and
            stored_source and
            source and
            str(Path(stored_source)) == str(Path(source))
        ):
            self.matrix = decode_matrix_png(stored_png)
        else:
            self.matrix = None

        self.matrix_canvas.set_array(self.matrix)
        self._refresh_matrix_info()

    def generate(self):
        source = self.state.ai_image_path

        if not source or not Path(source).exists():
            QMessageBox.information(
                self,
                "Sem Pixel Art",
                "A etapa 2 precisa possuir uma Pixel Art carregada e aprovada."
            )
            return

        try:
            image = Image.open(source).convert("RGB")
            self.matrix = image_to_matrix_100(image)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao gerar matriz",
                str(e)
            )
            return

        self.state.metadata["matrix_100x100_png"] = encode_matrix_png(
            self.matrix
        )
        self.state.metadata["matrix_source_path"] = source
        self.state.metadata["matrix_method"] = (
            "real_rgb_nearest_local_median"
        )

        self.state.matrix_image_path = None
        self.state.unapprove("matrix")
        self.state.invalidate_after("matrix")
        self.state.dirty = True

        self.matrix_canvas.set_array(self.matrix)
        self._refresh_matrix_info()

    def _refresh_matrix_info(self):
        if self.matrix is None:
            self.matrix_info.setText("Matriz ainda não gerada.")
            self.save_matrix_btn.setEnabled(False)
            self.save_preview_btn.setEnabled(False)
            return

        unique = len(
            np.unique(
                self.matrix.reshape(-1,3),
                axis=0
            )
        )

        self.matrix_info.setText(
            f"100×100 • 10.000 células • {unique:,} RGBs atuais "
            "(a simplificação para 50 cores acontece na próxima etapa)"
        )

        self.save_matrix_btn.setEnabled(True)
        self.save_preview_btn.setEnabled(True)

    def save_matrix(self):
        if self.matrix is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar matriz técnica",
            "pixel_art_matriz_100x100.png",
            "PNG (*.png)"
        )

        if not path:
            return

        Image.fromarray(
            self.matrix.astype(np.uint8),
            "RGB"
        ).save(path)

        self.state.matrix_image_path = path
        self.state.dirty = True

        QMessageBox.information(
            self,
            "Matriz salva",
            f"Matriz técnica salva em:\n{path}\n\n"
            "Dimensão real: 100×100 pixels."
        )

    def save_preview(self):
        if self.matrix is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar preview ampliado",
            "pixel_art_matriz_100x100_preview.png",
            "PNG (*.png)"
        )

        if not path:
            return

        enlarged_preview(
            self.matrix,
            800
        ).save(path)

        QMessageBox.information(
            self,
            "Preview salvo",
            path
        )

    def is_ready(self):
        return (
            self.matrix is not None
            and self.matrix.shape == (100,100,3)
            and self.state.metadata.get("matrix_source_path")
            == self.state.ai_image_path
        )
