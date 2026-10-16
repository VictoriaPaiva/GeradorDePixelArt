from pathlib import Path

from PIL import Image
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QMessageBox,
    QPlainTextEdit, QPushButton, QSpinBox, QSplitter, QVBoxLayout, QWidget
)

from .base_step import BaseStep
from ..prompt_templates import build_matrix_refinement_prompt
from ..widgets.image_preview import ImagePreview


class MatrixArtStep(BaseStep):
    matrixArtChanged = Signal(str)

    def __init__(self, state):
        super().__init__(
            "2. Matriz artística via Chat",
            "Use o ChatGPT para redesenhar a base já aprovada pensando especificamente na matriz final; depois importe aqui o resultado."
        )
        self.state = state
        self.outline = False
        self.layout.setContentsMargins(14, 10, 14, 8)
        self.layout.setSpacing(7)

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        self.layout.addWidget(split, 1)

        # LEFT: prompt + controls
        left = QFrame()
        left.setStyleSheet("QFrame{background:#f8fbff;border:1px solid #ccd8e6;border-radius:9px;} QLabel{border:none;}")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(10, 10, 10, 10)
        ll.setSpacing(7)

        title = QLabel("PROMPT DE REDESENHO PARA A MATRIZ")
        title.setStyleSheet("font-size:16px;font-weight:700;color:#174f84;border:none;")
        ll.addWidget(title)

        hint = QLabel(
            "Esta etapa é artística e acontece no ChatGPT. O sistema não deve criar a versão 50×50/100×100 por redução mecânica. "
            "Ele apenas normalizará tecnicamente a imagem aprovada na próxima etapa."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size:11px;color:#59616d;border:none;")
        ll.addWidget(hint)

        row = QHBoxLayout()
        row.addWidget(QLabel("Matriz:"))
        self.w = QSpinBox(); self.h = QSpinBox()
        for s in (self.w, self.h):
            s.setRange(50, 100); s.setMaximumWidth(76)
        row.addWidget(self.w); row.addWidget(QLabel("×")); row.addWidget(self.h)
        self.p50 = QPushButton("50×50"); self.p75 = QPushButton("75×75"); self.p100 = QPushButton("100×100")
        row.addWidget(self.p50); row.addWidget(self.p75); row.addWidget(self.p100)
        row.addSpacing(10)
        row.addWidget(QLabel("Cores:"))
        self.colors = QSpinBox(); self.colors.setRange(8, 50); self.colors.setMaximumWidth(70)
        row.addWidget(self.colors); row.addStretch(1)
        ll.addLayout(row)

        row2 = QHBoxLayout()
        self.no_outline = QPushButton("Sem contorno"); self.with_outline = QPushButton("Com contorno")
        self.no_outline.setCheckable(True); self.with_outline.setCheckable(True)
        self.copy_btn = QPushButton("Copiar prompt")
        self.save_prompt_btn = QPushButton("Salvar prompt TXT")
        row2.addWidget(self.no_outline); row2.addWidget(self.with_outline); row2.addStretch(1)
        row2.addWidget(self.copy_btn); row2.addWidget(self.save_prompt_btn)
        ll.addLayout(row2)

        self.prompt_box = QPlainTextEdit(); self.prompt_box.setReadOnly(True)
        self.prompt_box.setStyleSheet("QPlainTextEdit{background:white;border:1px solid #cfd6df;border-radius:6px;padding:7px;font-size:11px;}")
        ll.addWidget(self.prompt_box, 1)
        self.copy_status = QLabel(""); self.copy_status.setWordWrap(True)
        self.copy_status.setStyleSheet("font-size:11px;color:#18794e;border:none;")
        ll.addWidget(self.copy_status)

        # RIGHT: imported Chat result
        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(6,0,0,0); rl.setSpacing(6)
        rh = QHBoxLayout(); rt = QLabel("MATRIZ ARTÍSTICA GERADA NO CHAT")
        rt.setStyleSheet("font-size:16px;font-weight:700;"); rh.addWidget(rt); rh.addStretch(1)
        self.import_btn = QPushButton("Importar resultado do Chat")
        self.replace_btn = QPushButton("Substituir")
        rh.addWidget(self.import_btn); rh.addWidget(self.replace_btn); rl.addLayout(rh)
        self.preview = ImagePreview("Gere a matriz artística no ChatGPT e importe aqui o resultado aprovado.")
        rl.addWidget(self.preview, 1)
        self.info = QLabel(""); self.info.setWordWrap(True); self.info.setStyleSheet("font-size:11px;color:#59616d;")
        rl.addWidget(self.info)

        split.addWidget(left); split.addWidget(right); split.setSizes([760,760])

        self.p50.clicked.connect(lambda:self.set_preset(50,50)); self.p75.clicked.connect(lambda:self.set_preset(75,75)); self.p100.clicked.connect(lambda:self.set_preset(100,100))
        self.w.valueChanged.connect(self.controls_changed); self.h.valueChanged.connect(self.controls_changed); self.colors.valueChanged.connect(self.controls_changed)
        self.no_outline.clicked.connect(lambda:self.set_outline(False)); self.with_outline.clicked.connect(lambda:self.set_outline(True))
        self.copy_btn.clicked.connect(self.copy_prompt); self.save_prompt_btn.clicked.connect(self.save_prompt)
        self.import_btn.clicked.connect(self.import_result); self.replace_btn.clicked.connect(self.import_result)
        self.refresh()

    def set_context(self, state):
        self.state = state; self.refresh()

    def set_preset(self, w, h):
        self.w.setValue(w); self.h.setValue(h)

    def set_outline(self, value):
        self.outline = bool(value); self.controls_changed()

    def controls_changed(self):
        self.no_outline.blockSignals(True); self.with_outline.blockSignals(True)
        self.no_outline.setChecked(not self.outline); self.with_outline.setChecked(self.outline)
        self.no_outline.blockSignals(False); self.with_outline.blockSignals(False)
        self.state.metadata['grid_width'] = self.w.value(); self.state.metadata['grid_height'] = self.h.value()
        self.state.metadata['palette_target'] = self.colors.value(); self.state.palette_target = self.colors.value()
        self.state.metadata['matrix_prompt_outline'] = self.outline
        self.state.matrix_size = max(self.w.value(), self.h.value())
        self.state.dirty = True
        self.update_prompt()

    def update_prompt(self):
        text = build_matrix_refinement_prompt(self.w.value(), self.h.value(), self.colors.value(), self.outline)
        self.prompt_box.setPlainText(text)
        self.state.metadata['chat_matrix_prompt'] = text
        self.copy_status.setText('')

    def copy_prompt(self):
        QApplication.clipboard().setText(self.prompt_box.toPlainText())
        self.copy_status.setText(f"✓ Prompt {self.w.value()}×{self.h.value()} copiado. Gere a nova versão no ChatGPT e importe o resultado à direita.")

    def save_prompt(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Salvar prompt', f'prompt_matriz_{self.w.value()}x{self.h.value()}.txt', 'Texto (*.txt)')
        if path:
            Path(path).write_text(self.prompt_box.toPlainText(), encoding='utf-8')

    def import_result(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Importar matriz artística do Chat', '', 'Imagens (*.png *.jpg *.jpeg *.webp *.bmp)')
        if not path: return
        try:
            im = Image.open(path); im.verify()
        except Exception as e:
            QMessageBox.critical(self, 'Imagem inválida', str(e)); return
        self.state.metadata['chat_matrix_art_path'] = path
        self.state.metadata['chat_matrix_art_origin'] = f'chat_{self.w.value()}x{self.h.value()}'
        self.state.unapprove('matrix_art'); self.state.invalidate_after('matrix_art'); self.state.dirty = True
        self.matrixArtChanged.emit(path); self.refresh()

    def refresh(self):
        w = int(self.state.metadata.get('grid_width', self.state.metadata.get('prompt_grid_width', 50)))
        h = int(self.state.metadata.get('grid_height', self.state.metadata.get('prompt_grid_height', 50)))
        c = int(self.state.metadata.get('palette_target', self.state.metadata.get('prompt_color_limit', 50)))
        self.outline = bool(self.state.metadata.get('matrix_prompt_outline', False))
        for widget, value in ((self.w,w),(self.h,h),(self.colors,c)):
            widget.blockSignals(True); widget.setValue(value); widget.blockSignals(False)
        self.no_outline.setChecked(not self.outline); self.with_outline.setChecked(self.outline); self.update_prompt()
        path = self.state.metadata.get('chat_matrix_art_path')
        if path and Path(path).exists():
            self.preview.set_image(path); self.replace_btn.setEnabled(True)
            try:
                im = Image.open(path)
                self.info.setText(f"{Path(path).name} • {im.width}×{im.height} • declarada como matriz artística para {w}×{h}. A próxima etapa fará apenas normalização técnica.")
            except Exception:
                self.info.setText(Path(path).name)
        else:
            self.preview.clear_image('Gere a matriz artística no ChatGPT e importe aqui o resultado aprovado.')
            self.replace_btn.setEnabled(False)
            self.info.setText(f"Aguardando resultado do Chat para {w}×{h}.")

    def is_ready(self):
        p = self.state.metadata.get('chat_matrix_art_path')
        return bool(p and Path(p).exists())
