from pathlib import Path

from PIL import Image

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QApplication, QPushButton, QFileDialog, QLabel, QHBoxLayout,
    QVBoxLayout, QMessageBox, QSplitter, QWidget, QPlainTextEdit,
    QFrame, QSpinBox
)

from .base_step import BaseStep
from ..widgets.image_preview import ImagePreview
from ..prompt_templates import get_prompt


class InputStep(BaseStep):
    sourceChanged = Signal(str)

    def __init__(self, state):
        super().__init__(
            "1. Prompt + base artística",
            "Monte o prompt diretamente no sistema, gere a base no ChatGPT e depois importe a imagem aprovada."
        )
        self.state = state
        self.prompt_kind = "sem_contorno"

        title_widget = self.layout.itemAt(0).widget()
        desc_widget = self.layout.itemAt(1).widget()
        if title_widget:
            title_widget.setStyleSheet("font-size:20px;font-weight:700;")
            title_widget.setMaximumHeight(34)
        if desc_widget:
            desc_widget.setStyleSheet("font-size:12px;color:#5b6470;")
            desc_widget.setMaximumHeight(34)

        self.layout.setContentsMargins(14, 10, 14, 8)
        self.layout.setSpacing(7)

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        self.layout.addWidget(split, 1)

        # LEFT: imported base artística
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 6, 0)
        ll.setSpacing(6)

        image_header = QHBoxLayout()
        image_title = QLabel("BASE ARTÍSTICA DO PROJETO")
        image_title.setStyleSheet("font-size:17px;font-weight:700;")
        image_header.addWidget(image_title)
        image_header.addStretch(1)

        self.open_btn = QPushButton("Importar base artística")
        self.replace_btn = QPushButton("Substituir")
        self.replace_btn.setEnabled(False)
        image_header.addWidget(self.open_btn)
        image_header.addWidget(self.replace_btn)
        ll.addLayout(image_header)

        self.preview = ImagePreview(
            "Importe a imagem ilustrada que servirá de base para o gráfico de ponto cruz."
        )
        ll.addWidget(self.preview, 1)

        self.info = QLabel("Aguardando base artística.")
        self.info.setStyleSheet("font-size:11px;color:#59616d;")
        self.info.setWordWrap(True)
        ll.addWidget(self.info)

        # RIGHT: systemic prompt builder
        right = QFrame()
        right.setStyleSheet("""
            QFrame {
                background:#f8fbff;
                border:1px solid #ccd8e6;
                border-radius:9px;
            }
            QLabel {
                border:none;
                background:transparent;
            }
        """)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(10, 10, 10, 10)
        rl.setSpacing(7)

        prompt_title = QLabel("PROMPT SISTÊMICO PARA GERAR NO CHATGPT")
        prompt_title.setStyleSheet(
            "font-size:16px;font-weight:700;color:#174f84;border:none;"
        )
        rl.addWidget(prompt_title)

        prompt_hint = QLabel(
            "Escolha contorno, matriz e limite de cores. O sistema monta o prompt automaticamente. "
            "Depois copie o texto, gere a imagem no ChatGPT e importe aqui a versão aprovada."
        )
        prompt_hint.setWordWrap(True)
        prompt_hint.setStyleSheet("font-size:11px;color:#59616d;border:none;")
        rl.addWidget(prompt_hint)

        # row 1: contour buttons
        prompt_buttons = QHBoxLayout()
        self.no_outline_btn = QPushButton("Sem contorno")
        self.outline_btn = QPushButton("Com contorno")
        self.copy_btn = QPushButton("Copiar prompt")
        self.no_outline_btn.setCheckable(True)
        self.outline_btn.setCheckable(True)
        prompt_buttons.addWidget(self.no_outline_btn)
        prompt_buttons.addWidget(self.outline_btn)
        prompt_buttons.addStretch(1)
        prompt_buttons.addWidget(self.copy_btn)
        rl.addLayout(prompt_buttons)

        # row 2: size and palette controls
        config = QFrame()
        config.setStyleSheet("QFrame{background:white;border:1px solid #d8e2ee;border-radius:8px;}")
        cl = QVBoxLayout(config)
        cl.setContentsMargins(9, 8, 9, 8)
        cl.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Matriz desejada:"))
        self.grid_w = QSpinBox()
        self.grid_h = QSpinBox()
        for s in (self.grid_w, self.grid_h):
            s.setRange(50, 100)
            s.setMaximumWidth(78)
        row1.addWidget(self.grid_w)
        row1.addWidget(QLabel("×"))
        row1.addWidget(self.grid_h)
        self.preset_50 = QPushButton("50×50")
        self.preset_75 = QPushButton("75×75")
        self.preset_100 = QPushButton("100×100")
        row1.addWidget(self.preset_50)
        row1.addWidget(self.preset_75)
        row1.addWidget(self.preset_100)
        row1.addStretch(1)
        cl.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Limite visual de cores:"))
        self.color_limit = QSpinBox()
        self.color_limit.setRange(8, 50)
        self.color_limit.setMaximumWidth(78)
        row2.addWidget(self.color_limit)
        row2.addStretch(1)
        self.apply_defaults_btn = QPushButton("Usar estes valores no projeto")
        row2.addWidget(self.apply_defaults_btn)
        cl.addLayout(row2)

        small = QLabel(
            "Dica: este prompt já orienta a IA pensando na futura matriz bordável. "
            "Na etapa seguinte você ainda poderá ajustar enquadramento e confirmar a grade." 
        )
        small.setWordWrap(True)
        small.setStyleSheet("font-size:10px;color:#5f6874;")
        cl.addWidget(small)
        rl.addWidget(config)

        self.prompt_box = QPlainTextEdit()
        self.prompt_box.setReadOnly(True)
        self.prompt_box.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.prompt_box.setStyleSheet("""
            QPlainTextEdit {
                background:white;
                border:1px solid #cfd6df;
                border-radius:6px;
                padding:7px;
                font-size:11px;
            }
        """)
        rl.addWidget(self.prompt_box, 1)

        self.copy_status = QLabel("")
        self.copy_status.setStyleSheet("font-size:11px;color:#18794e;border:none;")
        self.copy_status.setWordWrap(True)
        rl.addWidget(self.copy_status)

        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 1)
        split.setSizes([760, 760])

        # signals
        self.open_btn.clicked.connect(self.choose_image)
        self.replace_btn.clicked.connect(self.choose_image)
        self.no_outline_btn.clicked.connect(lambda: self.show_prompt("sem_contorno"))
        self.outline_btn.clicked.connect(lambda: self.show_prompt("com_contorno"))
        self.copy_btn.clicked.connect(self.copy_prompt)
        self.preset_50.clicked.connect(lambda: self.set_grid_preset(50, 50))
        self.preset_75.clicked.connect(lambda: self.set_grid_preset(75, 75))
        self.preset_100.clicked.connect(lambda: self.set_grid_preset(100, 100))
        self.grid_w.valueChanged.connect(self._controls_changed)
        self.grid_h.valueChanged.connect(self._controls_changed)
        self.color_limit.valueChanged.connect(self._controls_changed)
        self.apply_defaults_btn.clicked.connect(self.apply_project_defaults)

        self.refresh()

    # ------------------------------------------------------------------
    def _safe_int(self, value, default):
        try:
            return int(value)
        except Exception:
            return default

    def set_grid_preset(self, w, h):
        self.grid_w.setValue(w)
        self.grid_h.setValue(h)

    def _controls_changed(self):
        self.state.metadata["prompt_grid_width"] = self.grid_w.value()
        self.state.metadata["prompt_grid_height"] = self.grid_h.value()
        self.state.metadata["prompt_color_limit"] = self.color_limit.value()
        self.state.metadata["pixel_art_prompt_variant"] = self.prompt_kind
        self.state.dirty = True
        self._update_prompt_box()

    def _update_prompt_box(self):
        prompt = get_prompt(
            self.prompt_kind,
            self.grid_w.value(),
            self.grid_h.value(),
            self.color_limit.value(),
        )
        self.prompt_box.setPlainText(prompt)
        self.copy_status.setText("")

    def show_prompt(self, kind):
        self.prompt_kind = kind
        self.no_outline_btn.blockSignals(True)
        self.outline_btn.blockSignals(True)
        self.no_outline_btn.setChecked(kind == "sem_contorno")
        self.outline_btn.setChecked(kind == "com_contorno")
        self.no_outline_btn.blockSignals(False)
        self.outline_btn.blockSignals(False)
        self.state.metadata["pixel_art_prompt_variant"] = self.prompt_kind
        self.state.dirty = True
        self._update_prompt_box()

    def copy_prompt(self):
        text = self.prompt_box.toPlainText().strip()
        if not text:
            return
        QApplication.clipboard().setText(text)
        contour = "COM contorno" if self.prompt_kind == "com_contorno" else "SEM contorno"
        self.copy_status.setText(
            f"✓ Prompt copiado. Configuração atual: {self.grid_w.value()}×{self.grid_h.value()}, até {self.color_limit.value()} cores, {contour}."
        )

    def apply_project_defaults(self):
        self.state.metadata["grid_width"] = self.grid_w.value()
        self.state.metadata["grid_height"] = self.grid_h.value()
        self.state.matrix_size = max(self.grid_w.value(), self.grid_h.value())
        self.state.dirty = True
        self.copy_status.setText(
            f"✓ Grade padrão do projeto atualizada para {self.grid_w.value()}×{self.grid_h.value()}. A etapa 2 já abrirá com esses valores."
        )

    # ------------------------------------------------------------------
    def choose_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar base artística",
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

        self.state.unapprove("input")
        self.state.invalidate_after("input")
        self.state.source_image_path = path
        self.state.ai_image_path = path
        self.state.metadata["cross_stitch_base_source"] = "external_import"
        self.state.metadata["pixel_art_prompt_variant"] = self.prompt_kind
        self.state.metadata["prompt_grid_width"] = self.grid_w.value()
        self.state.metadata["prompt_grid_height"] = self.grid_h.value()
        self.state.metadata["prompt_color_limit"] = self.color_limit.value()
        self.state.dirty = True
        self.sourceChanged.emit(path)
        self.refresh()

    # ------------------------------------------------------------------
    def refresh(self):
        preferred = self.state.ai_image_path
        if not (preferred and Path(preferred).exists()):
            preferred = self.state.source_image_path

        saved_kind = self.state.metadata.get("pixel_art_prompt_variant", self.prompt_kind)
        if saved_kind not in {"sem_contorno", "com_contorno"}:
            saved_kind = "sem_contorno"
        self.prompt_kind = saved_kind

        gw = self._safe_int(self.state.metadata.get("prompt_grid_width", self.state.metadata.get("grid_width", 50)), 50)
        gh = self._safe_int(self.state.metadata.get("prompt_grid_height", self.state.metadata.get("grid_height", 50)), 50)
        colors = self._safe_int(self.state.metadata.get("prompt_color_limit", 50), 50)

        self.grid_w.blockSignals(True)
        self.grid_h.blockSignals(True)
        self.color_limit.blockSignals(True)
        self.grid_w.setValue(max(50, min(100, gw)))
        self.grid_h.setValue(max(50, min(100, gh)))
        self.color_limit.setValue(max(8, min(50, colors)))
        self.grid_w.blockSignals(False)
        self.grid_h.blockSignals(False)
        self.color_limit.blockSignals(False)

        self.show_prompt(self.prompt_kind)

        if preferred and Path(preferred).exists():
            self.preview.set_image(preferred)
            try:
                im = Image.open(preferred)
                self.info.setText(
                    f"{Path(preferred).name} • {im.width}×{im.height} • {im.mode} • "
                    f"base atual do projeto. Prompt configurado para {self.grid_w.value()}×{self.grid_h.value()} e até {self.color_limit.value()} cores."
                )
            except Exception:
                self.info.setText(Path(preferred).name)
            self.replace_btn.setEnabled(True)
            if self.state.source_image_path != preferred:
                self.state.source_image_path = preferred
                self.state.dirty = True
            if self.state.ai_image_path != preferred:
                self.state.ai_image_path = preferred
                self.state.dirty = True
        else:
            self.preview.clear_image(
                "Importe a imagem ilustrada que servirá de base para o gráfico de ponto cruz."
            )
            self.info.setText(
                "Aguardando base artística. Configure o prompt à direita, copie o texto, gere a imagem no ChatGPT e depois importe a versão aprovada."
            )
            self.replace_btn.setEnabled(False)
