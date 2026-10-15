from pathlib import Path
import hashlib

import numpy as np
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QFileDialog, QMessageBox, QCheckBox
)

from .base_step import BaseStep
from ..widgets.matrix_canvas import MatrixCanvas
from ..widgets.final_palette_panel import FinalPalettePanel
from ..matrix_service import decode_matrix_png, enlarged_preview
from ..simplification_service import (
    simplify_to_50,
    rebuild_palette_without_colors,
    encode_png,
    decode_png,
    unique_essential_colors,
)


class SimplificationStep(BaseStep):
    def __init__(self, state, workspace):
        super().__init__(
            "5. Simplificação para 50 cores",
            "Reduza somente as cores da matriz, preservando as 10.000 células e protegendo as essenciais."
        )
        self.state = state
        self.workspace = workspace

        self.source_matrix = None
        self.simplified = None
        self.palette = []
        self.essential = []

        title_widget = self.layout.itemAt(0).widget()
        desc_widget = self.layout.itemAt(1).widget()

        if title_widget:
            title_widget.setStyleSheet("font-size:20px;font-weight:700;")
            title_widget.setMaximumHeight(34)

        if desc_widget:
            desc_widget.setStyleSheet("font-size:12px;color:#5b6470;")
            desc_widget.setMaximumHeight(30)

        self.layout.setContentsMargins(14,10,14,8)
        self.layout.setSpacing(6)

        toolbar = QHBoxLayout()

        self.generate_btn = QPushButton("Gerar 50 cores")
        self.generate_btn.setToolTip(
            "Gerar ou regerar a simplificação usando a matriz 100×100 e as cores essenciais atuais"
        )

        self.rebuild_btn = QPushButton("Remover selecionadas e recriar")
        self.rebuild_btn.setToolTip(
            "Remove as cores complementares marcadas na paleta e completa novamente as 50 cores com tons mais distintos"
        )

        self.clear_selection_btn = QPushButton("Limpar seleção")
        self.clear_selection_btn.setToolTip(
            "Desmarcar as cores atualmente selecionadas para remoção"
        )

        self.grid_check = QCheckBox("Mostrar grade")
        self.grid_check.setToolTip(
            "Grade apenas visual para comparar as células. Não entra na paleta."
        )

        self.save_btn = QPushButton("Salvar matriz")
        self.save_btn.setToolTip(
            "Salvar PNG técnico 100×100 já simplificado para 50 cores"
        )

        self.preview_btn = QPushButton("Salvar preview")
        self.preview_btn.setToolTip(
            "Salvar versão ampliada 800×800 por nearest-neighbor"
        )

        toolbar.addWidget(self.generate_btn)
        toolbar.addWidget(self.rebuild_btn)
        toolbar.addWidget(self.clear_selection_btn)
        toolbar.addWidget(self.grid_check)
        toolbar.addStretch(1)
        toolbar.addWidget(self.save_btn)
        toolbar.addWidget(self.preview_btn)

        self.layout.addLayout(toolbar)

        self.info = QLabel(
            "As essenciais entram primeiro na paleta e ficam protegidas. "
            "A paleta final é exibida com cores parecidas próximas. "
            "Você pode marcar cores complementares muito parecidas para removê-las e recriar uma nova paleta de 50 cores com menos redundância. "
            "Não há dithering e nenhuma célula muda de posição."
        )
        self.info.setWordWrap(True)
        self.info.setStyleSheet("font-size:11px;color:#59616d;")
        self.layout.addWidget(self.info)

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        self.layout.addWidget(split, 1)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0,0,5,0)
        ll.setSpacing(4)

        left_title = QLabel("MATRIZ 100×100 APROVADA")
        left_title.setStyleSheet("font-size:17px;font-weight:700;")
        ll.addWidget(left_title)

        self.source_canvas = MatrixCanvas()
        ll.addWidget(self.source_canvas, 1)

        self.source_info = QLabel("")
        self.source_info.setStyleSheet("font-size:11px;color:#59616d;")
        self.source_info.setMaximumHeight(20)
        ll.addWidget(self.source_info)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(5,0,0,0)
        rl.setSpacing(4)

        right_title = QLabel("SIMPLIFICADA — 50 CORES")
        right_title.setStyleSheet("font-size:17px;font-weight:700;")
        rl.addWidget(right_title)

        self.final_canvas = MatrixCanvas()
        rl.addWidget(self.final_canvas, 1)

        self.final_info = QLabel("Simplificação ainda não gerada.")
        self.final_info.setStyleSheet("font-size:11px;color:#59616d;")
        self.final_info.setMaximumHeight(20)
        rl.addWidget(self.final_info)

        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 1)
        split.setSizes([750,750])

        self.palette_panel = FinalPalettePanel()
        self.layout.addWidget(self.palette_panel)

        self.generate_btn.clicked.connect(self.generate)
        self.rebuild_btn.clicked.connect(self.rebuild_palette)
        self.clear_selection_btn.clicked.connect(self.palette_panel.clear_selection)
        self.palette_panel.selectionChanged.connect(self._refresh_actions)
        self.grid_check.toggled.connect(self.source_canvas.set_grid)
        self.grid_check.toggled.connect(self.final_canvas.set_grid)
        self.save_btn.clicked.connect(self.save_matrix)
        self.preview_btn.clicked.connect(self.save_preview)

        self.refresh()

    def set_context(self, state, workspace):
        self.state = state
        self.workspace = workspace
        self.refresh()

    def refresh(self):
        self.source_matrix = decode_matrix_png(
            self.state.metadata.get("matrix_100x100_png")
        )

        self.source_canvas.set_array(self.source_matrix)

        if self.source_matrix is None:
            self.source_info.setText("Sem matriz 100×100 disponível.")
        else:
            unique = len(
                np.unique(
                    self.source_matrix.reshape(-1,3),
                    axis=0
                )
            )
            self.source_info.setText(
                f"100×100 • {unique:,} RGBs antes da simplificação"
            )

        current_signature = self._input_signature()

        stored_signature = self.state.metadata.get("simplification_input_signature")
        has_legacy_result = bool(
            self.state.metadata.get("simplified_50_png")
            and self.state.metadata.get("final_palette_50")
        )
        signature_matches = (stored_signature == current_signature)

        if (
            not signature_matches
            and has_legacy_result
            and not (
                isinstance(stored_signature, dict)
                and stored_signature.get("version") == 2
            )
        ):
            self.state.metadata["simplification_input_signature"] = current_signature
            signature_matches = True
            self.state.dirty = True

        if signature_matches:
            self.simplified = decode_png(
                self.state.metadata.get("simplified_50_png")
            )
            self.palette = [
                tuple(c)
                for c in self.state.metadata.get(
                    "final_palette_50",
                    []
                )
            ]
            self.essential = [
                tuple(c)
                for c in self.state.metadata.get(
                    "final_essential_colors",
                    []
                )
            ]
        else:
            self.simplified = None
            self.palette = []
            self.essential = []

        self.final_canvas.set_array(self.simplified)
        self.palette_panel.set_palette(
            self.palette,
            self.essential
        )
        self._refresh_final_info()
        self._refresh_actions()

    def _input_signature(self):
        matrix_key = self.state.metadata.get("matrix_100x100_png", "")
        matrix_digest = hashlib.sha256(
            matrix_key.encode("ascii")
        ).hexdigest()
        essential = tuple(sorted(unique_essential_colors(self.workspace)))
        return {
            "version": 2,
            "matrix_sha256": matrix_digest,
            "essential_rgbs": [list(rgb) for rgb in essential],
        }

    def _apply_result(self, simplified, palette, essential, method, removed_rgbs=None):
        self.simplified = simplified
        self.palette = list(palette)
        self.essential = list(essential)

        self.state.metadata["simplified_50_png"] = encode_png(simplified)
        self.state.metadata["final_palette_50"] = [list(c) for c in palette]
        self.state.metadata["final_essential_colors"] = [list(c) for c in essential]
        self.state.metadata["simplification_input_signature"] = self._input_signature()
        self.state.metadata["simplification_method"] = method
        self.state.metadata["simplification_removed_colors"] = [
            list(c) for c in (removed_rgbs or [])
        ]

        self.state.simplified_image_path = None
        self.state.unapprove("simplification")
        self.state.invalidate_after("simplification")
        self.state.dirty = True

        self.final_canvas.set_array(self.simplified)
        try:
            self.palette_panel.set_palette(self.palette, self.essential)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao montar paleta",
                "A imagem simplificada foi gerada, mas a paleta não pôde ser exibida.\n\n"
                + str(e)
            )
            return
        self._refresh_final_info()
        self._refresh_actions()

    def generate(self):
        if self.source_matrix is None:
            QMessageBox.information(
                self,
                "Sem matriz",
                "Gere e aprove a matriz 100×100 antes de simplificar."
            )
            return

        if not self.state.approvals.get("matrix", False):
            QMessageBox.information(
                self,
                "Matriz ainda não aprovada",
                "Aprove a etapa Matriz 100×100 antes de gerar a simplificação."
            )
            return

        essential = unique_essential_colors(self.workspace)

        if len(essential) > 50:
            QMessageBox.warning(
                self,
                "Essenciais acima do limite",
                f"Existem {len(essential)} RGBs essenciais únicos. "
                "A paleta final possui 50 cores.\n\n"
                "Volte à etapa de paletas e remova cores redundantes."
            )
            return

        try:
            simplified, palette, essential = simplify_to_50(
                self.source_matrix,
                self.workspace,
                target=50
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro na simplificação",
                str(e)
            )
            return

        self._apply_result(
            simplified,
            palette,
            essential,
            method="essential_locked_weighted_lab_farthest_no_dither"
        )

    def rebuild_palette(self):
        if self.simplified is None or self.source_matrix is None:
            QMessageBox.information(
                self,
                "Sem simplificação",
                "Gere a simplificação antes de remover cores da paleta."
            )
            return

        removed = self.palette_panel.selected_colors()
        if not removed:
            QMessageBox.information(
                self,
                "Nenhuma cor selecionada",
                "Marque na paleta as cores complementares que deseja remover e tente novamente."
            )
            return

        answer = QMessageBox.question(
            self,
            "Recriar paleta",
            f"Remover {len(removed)} cor(es) complementar(es) e recriar a paleta de 50 cores?\n\n"
            "As cores essenciais serão preservadas.",
            QMessageBox.Yes | QMessageBox.No
        )
        if answer != QMessageBox.Yes:
            return

        try:
            simplified, palette, essential = rebuild_palette_without_colors(
                self.source_matrix,
                self.workspace,
                self.palette,
                removed,
                target=50
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao recriar paleta",
                str(e)
            )
            return

        self._apply_result(
            simplified,
            palette,
            essential,
            method="essential_locked_weighted_lab_farthest_no_dither_plus_manual_palette_removal",
            removed_rgbs=removed
        )

    def _refresh_actions(self):
        has_result = self.simplified is not None
        selected = self.palette_panel.selected_count()
        self.rebuild_btn.setEnabled(has_result and selected > 0)
        self.clear_selection_btn.setEnabled(selected > 0)
        self.save_btn.setEnabled(has_result)
        self.preview_btn.setEnabled(has_result)

    def _refresh_final_info(self):
        if self.simplified is None:
            self.final_info.setText(
                "Simplificação ainda não gerada."
            )
            self._refresh_actions()
            return

        unique = len(
            np.unique(
                self.simplified.reshape(-1,3),
                axis=0
            )
        )

        essential_present = sum(
            1
            for c in self.essential
            if np.any(
                np.all(
                    self.simplified
                    == np.array(c, dtype=np.uint8),
                    axis=2
                )
            )
        )

        self.final_info.setText(
            f"100×100 • {unique} cores usadas • "
            f"{essential_present}/{len(self.essential)} essenciais presentes"
        )

        self._refresh_actions()

    def save_matrix(self):
        if self.simplified is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar matriz simplificada",
            "pixel_art_100x100_50_cores.png",
            "PNG (*.png)"
        )

        if not path:
            return

        Image.fromarray(
            self.simplified.astype(np.uint8),
            "RGB"
        ).save(path)

        self.state.simplified_image_path = path
        self.state.dirty = True

        QMessageBox.information(
            self,
            "Imagem salva",
            f"Matriz simplificada salva em:\n{path}\n\n"
            "Dimensão real: 100×100 pixels."
        )

    def save_preview(self):
        if self.simplified is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar preview simplificado",
            "pixel_art_100x100_50_cores_preview.png",
            "PNG (*.png)"
        )

        if not path:
            return

        enlarged_preview(
            self.simplified,
            800
        ).save(path)

        QMessageBox.information(
            self,
            "Preview salvo",
            path
        )

    def is_ready(self):
        if self.simplified is None:
            return False

        unique = set(
            map(
                tuple,
                self.simplified.reshape(-1,3).tolist()
            )
        )

        essential = set(
            unique_essential_colors(
                self.workspace
            )
        )

        return (
            len(unique) == 50
            and essential.issubset(unique)
        )
