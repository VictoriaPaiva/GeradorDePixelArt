
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QFileDialog, QMessageBox, QFrame
)

from .models.project_state import ProjectState
from .steps.input_step import InputStep
from .steps.matrix_art_step import MatrixArtStep
from .steps.placeholder_step import PlaceholderStep
from .steps.palette_step import PaletteStep
from .steps.matrix_step import MatrixStep
from .steps.simplification_step import SimplificationStep
from .steps.manual_editor_step import ManualEditorStep
from .steps.pattern_step import PatternStep
from .steps.export_step import ExportStep
from .models.palette_workspace import PaletteWorkspace


STEPS = [
    ("input", "1. Base artística + prompt inicial"),
    ("matrix_art", "2. Matriz artística via Chat"),
    ("matrix", "3. Normalização técnica"),
    ("palette", "4. Cores essenciais (opcional)"),
    ("simplification", "5. Paleta técnica"),
    ("manual", "6. Edição manual"),
    ("pattern", "7. Grade e legenda"),
    ("export", "8. Exportar"),
]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.state = ProjectState()
        self.current_index = 0
        self.step_buttons = []
        self.pages = []

        self.palette_workspace = PaletteWorkspace.from_state_dict(
            self.state.metadata.get("palette_workspace", {})
        )

        self.sidebar_expanded = True

        self.setWindowTitle(
            "Guia de Ponto Cruz — v0.9.4"
        )
        self.resize(1500, 930)

        self._build_ui()
        self._build_pages()
        self._refresh_all()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(0,0,0,0)
        outer.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {background:#20242b;}
            QLabel {color:white;}
            QPushButton {
                background:#343a45;
                color:white;
                border:0;
                padding:8px 12px;
                border-radius:6px;
            }
            QPushButton:hover {background:#444c59;}
        """)

        hl = QHBoxLayout(header)
        hl.setContentsMargins(12,10,16,10)

        self.sidebar_btn = QPushButton("☰")
        self.sidebar_btn.setFixedWidth(42)
        self.sidebar_btn.setToolTip("Recolher menu lateral")
        hl.addWidget(self.sidebar_btn)

        title = QLabel("Guia de Ponto Cruz")
        title.setStyleSheet(
            "font-size:18px;font-weight:700;"
        )
        hl.addWidget(title)

        self.project_label = QLabel("Novo projeto")
        self.project_label.setStyleSheet(
            "color:#cdd3dc;"
        )
        hl.addWidget(self.project_label)
        hl.addStretch(1)

        self.new_btn = QPushButton("Novo")
        self.open_btn = QPushButton("Abrir projeto")
        self.save_btn = QPushButton("Salvar projeto")

        self.new_btn.setToolTip("Criar um novo projeto")
        self.open_btn.setToolTip("Abrir um projeto salvo")
        self.save_btn.setToolTip("Salvar o projeto atual")

        hl.addWidget(self.new_btn)
        hl.addWidget(self.open_btn)
        hl.addWidget(self.save_btn)

        outer.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(0,0,0,0)
        body.setSpacing(0)

        # Sidebar
        self.side = QFrame()
        self.side.setFixedWidth(245)
        self.side.setStyleSheet("""
            QFrame {
                background:#f0f2f5;
                border-right:1px solid #d5dae2;
            }
            QPushButton {
                text-align:left;
                padding:11px 13px;
                border:0;
                background:transparent;
                border-radius:7px;
                color:#303641;
            }
            QPushButton:hover {
                background:#e3e7ed;
            }
            QPushButton[active="true"] {
                background:#dcecff;
                color:#125aa3;
                font-weight:700;
            }
        """)

        sl = QVBoxLayout(self.side)
        sl.setContentsMargins(10,14,10,14)
        sl.setSpacing(5)

        self.steps_title = QLabel("ETAPAS")
        self.steps_title.setStyleSheet(
            "font-weight:700;color:#68707c;padding:4px;"
        )
        sl.addWidget(self.steps_title)

        for idx, (_, name) in enumerate(STEPS):
            btn = QPushButton(name)
            btn.setToolTip(name)
            btn.clicked.connect(
                lambda checked=False, i=idx:self.go_to(i)
            )
            self.step_buttons.append(btn)
            sl.addWidget(btn)

        sl.addStretch(1)

        self.sidebar_info = QLabel(
            "Fluxo híbrido v0.9.4\n\n"
            "Etapas artísticas via Chat\n"
            "Grade técnica: 50–100\n"
            "Paleta: até 50 cores"
        )
        self.sidebar_info.setStyleSheet(
            "color:#69717d;"
            "padding:8px;"
            "background:#e8ebef;"
            "border-radius:7px;"
        )
        sl.addWidget(self.sidebar_info)

        body.addWidget(self.side)

        # Main area
        main = QWidget()
        ml = QVBoxLayout(main)
        ml.setContentsMargins(0,0,0,0)

        self.stack = QStackedWidget()
        ml.addWidget(self.stack,1)

        footer = QFrame()
        footer.setStyleSheet(
            "QFrame {"
            "border-top:1px solid #d8dde5;"
            "background:white;"
            "}"
        )

        fl = QHBoxLayout(footer)
        fl.setContentsMargins(18,10,18,10)

        self.stage_status = QLabel("")
        fl.addWidget(self.stage_status)
        fl.addStretch(1)

        self.back_btn = QPushButton("← Voltar")
        self.approve_btn = QPushButton("Aprovar etapa")
        self.next_btn = QPushButton("Próximo →")

        self.approve_btn.setStyleSheet("""
            QPushButton {
                background:#1677d2;
                color:white;
                border:0;
                padding:9px 16px;
                border-radius:6px;
                font-weight:700;
            }
            QPushButton:hover {background:#1267b7;}
            QPushButton:disabled {background:#aeb7c2;}
        """)

        for b in [self.back_btn,self.next_btn]:
            b.setStyleSheet("""
                QPushButton {
                    padding:9px 14px;
                    border:1px solid #cbd1d9;
                    border-radius:6px;
                    background:white;
                }
            """)

        fl.addWidget(self.back_btn)
        fl.addWidget(self.approve_btn)
        fl.addWidget(self.next_btn)

        ml.addWidget(footer)

        body.addWidget(main,1)
        outer.addLayout(body,1)

        # Signals
        self.sidebar_btn.clicked.connect(self.toggle_sidebar)
        self.new_btn.clicked.connect(self.new_project)
        self.open_btn.clicked.connect(self.open_project)
        self.save_btn.clicked.connect(self.save_project)

        self.back_btn.clicked.connect(
            lambda:self.go_to(self.current_index-1)
        )
        self.next_btn.clicked.connect(self.next_step)
        self.approve_btn.clicked.connect(self.approve_current)

    def _build_pages(self):
        self.pages = [
            InputStep(self.state),
            MatrixArtStep(self.state),
            MatrixStep(self.state),
            PaletteStep(self.state, self.palette_workspace),
            SimplificationStep(self.state, self.palette_workspace),
            ManualEditorStep(self.state, self.palette_workspace),
            PatternStep(self.state),
            ExportStep(self.state),
        ]

        for page in self.pages:
            self.stack.addWidget(page)

        self.pages[0].sourceChanged.connect(self._input_source_changed)
        self.pages[1].matrixArtChanged.connect(self._matrix_art_changed)

    def _input_source_changed(self, _path):
        self.palette_workspace = PaletteWorkspace()
        self.state.metadata.pop("palette_workspace", None)
        self.pages[3].set_context(self.state, self.palette_workspace)
        self.pages[4].set_context(self.state, self.palette_workspace)
        self.pages[5].set_context(self.state, self.palette_workspace)
        self._refresh_all()

    def _matrix_art_changed(self, _path):
        self.palette_workspace = PaletteWorkspace()
        self.state.metadata.pop("palette_workspace", None)
        self.pages[3].set_context(self.state, self.palette_workspace)
        self.pages[4].set_context(self.state, self.palette_workspace)
        self.pages[5].set_context(self.state, self.palette_workspace)
        self._refresh_all()

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------
    def toggle_sidebar(self):
        self.sidebar_expanded = not self.sidebar_expanded

        if self.sidebar_expanded:
            self.side.setFixedWidth(245)
            self.steps_title.show()
            self.sidebar_info.show()
            self.sidebar_btn.setToolTip("Recolher menu lateral")
        else:
            self.side.setFixedWidth(62)
            self.steps_title.hide()
            self.sidebar_info.hide()
            self.sidebar_btn.setToolTip("Expandir menu lateral")

        self._refresh_sidebar()

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    def _replace_state(self,new_state):
        self.state = new_state

        self.palette_workspace = PaletteWorkspace.from_state_dict(
            self.state.metadata.get(
                "palette_workspace",
                {}
            )
        )

        self.pages[0].state = self.state
        self.pages[1].set_context(self.state)
        self.pages[2].set_context(self.state)
        self.pages[3].set_context(self.state, self.palette_workspace)
        self.pages[4].set_context(self.state, self.palette_workspace)
        self.pages[5].set_context(self.state, self.palette_workspace)
        self.pages[6].set_context(self.state)
        self.pages[7].set_context(self.state)

        self.pages[0].refresh()
        self.pages[1].refresh()
        self.pages[2].refresh()
        self.pages[3].refresh()

        self._refresh_all()

    def new_project(self):
        if self.state.dirty:
            answer = QMessageBox.question(
                self,
                "Novo projeto",
                "Existem alterações não salvas. "
                "Criar um novo projeto mesmo assim?",
                QMessageBox.Yes | QMessageBox.No
            )
            if answer != QMessageBox.Yes:
                return

        self._replace_state(ProjectState())
        self.go_to(0)

    def open_project(self):
        path,_ = QFileDialog.getOpenFileName(
            self,
            "Abrir projeto",
            "",
            "Projeto Guia de Ponto Cruz (*.pixelart.json *.json)"
        )

        if not path:
            return

        try:
            state = ProjectState.load(path)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao abrir projeto",
                str(e)
            )
            return

        self._replace_state(state)
        self.go_to(0)

    def save_project(self):
        # Ensure palette workspace is persisted before saving.
        self.state.metadata["palette_workspace"] = (
            self.palette_workspace.to_state_dict()
        )

        path = self.state.project_file

        if not path:
            path,_ = QFileDialog.getSaveFileName(
                self,
                "Salvar projeto",
                "meu_projeto.pixelart.json",
                "Projeto Guia de Ponto Cruz (*.pixelart.json)"
            )

            if not path:
                return

            if not path.lower().endswith(
                ".pixelart.json"
            ):
                path += ".pixelart.json"

        try:
            self.state.save(path)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao salvar projeto",
                str(e)
            )
            return

        self._refresh_header()

        QMessageBox.information(
            self,
            "Projeto salvo",
            f"Projeto salvo em:\n{path}"
        )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def go_to(self,index):
        index = max(
            0,
            min(len(STEPS)-1,index)
        )

        self.current_index = index
        self.stack.setCurrentIndex(index)

        if 0 <= index < len(self.pages):
            page=self.pages[index]
            if hasattr(page,"refresh"):
                page.refresh()

        self._refresh_all()

    def next_step(self):
        key = STEPS[self.current_index][0]

        if (
            self.current_index < len(STEPS)-1 and
            not self.state.approvals.get(
                key,
                False
            )
        ):
            QMessageBox.information(
                self,
                "Etapa ainda não aprovada",
                "Aprove esta etapa antes de continuar.\n\n"
                "Os checkpoints impedem que mudanças visuais avancem "
                "sem sua confirmação."
            )
            return

        self.go_to(
            self.current_index+1
        )

    def approve_current(self):
        key = STEPS[self.current_index][0]

        if (
            key == "input" and
            not self.state.source_image_path
        ):
            QMessageBox.information(
                self,
                "Sem imagem",
                "Importe a base artística primeiro."
            )
            return

        if (
            key == "matrix_art" and
            not self.pages[1].is_ready()
        ):
            QMessageBox.information(
                self,
                "Matriz artística não importada",
                "Copie o prompt, gere a matriz artística no ChatGPT e importe o resultado aprovado antes de continuar."
            )
            return

        if (
            key == "matrix" and
            not self.pages[2].is_ready()
        ):
            QMessageBox.information(
                self,
                "Grade técnica ainda não gerada",
                "Normalize tecnicamente a matriz artística para a grade exata antes de aprovar."
            )
            return

        if (
            key == "palette" and
            not self.pages[3].is_ready()
        ):
            QMessageBox.information(
                self,
                "Áreas incompletas",
                "Recalcule as paletas das áreas existentes ou apague as áreas incompletas. "
                "Esta etapa pode ficar sem áreas, pois as cores essenciais são opcionais."
            )
            return

        if (
            key == "simplification" and
            not self.pages[4].is_ready()
        ):
            QMessageBox.information(
                self,
                "Paleta técnica incompleta",
                "Use a paleta atual quando ela já estiver dentro do limite ou execute a simplificação local experimental."
            )
            return

        if (
            key == "manual" and
            not self.pages[5].is_ready()
        ):
            QMessageBox.information(
                self,
                "Edição manual inválida",
                "A matriz precisa manter as dimensões escolhidas e usar somente cores da paleta final."
            )
            return

        if (
            key == "pattern" and
            not self.pages[6].is_ready()
        ):
            QMessageBox.information(
                self,
                "Molde ainda não gerado",
                "Gere o molde e a legenda antes de aprovar esta etapa."
            )
            return

        if (
            key == "export" and
            not self.pages[7].is_ready()
        ):
            QMessageBox.information(
                self,
                "Exportação ainda não concluída",
                "Exporte pelo menos um conjunto válido de arquivos finais antes de aprovar."
            )
            return

        if self.state.approvals.get(
            key,
            False
        ):
            self.state.unapprove(key)
        else:
            self.state.approve(key)

        self._refresh_all()

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
    def _refresh_header(self):
        name = self.state.project_name

        if self.state.project_file:
            name = Path(
                self.state.project_file
            ).stem

        marker = (
            " *"
            if self.state.dirty
            else ""
        )

        self.project_label.setText(
            name+marker
        )

    def _refresh_sidebar(self):
        for idx,btn in enumerate(
            self.step_buttons
        ):
            key = STEPS[idx][0]
            name = STEPS[idx][1]
            approved = self.state.approvals.get(
                key,
                False
            )

            btn.setProperty(
                "active",
                idx == self.current_index
            )

            if self.sidebar_expanded:
                prefix = (
                    "✓ "
                    if approved
                    else ""
                )
                btn.setText(
                    prefix+name
                )
                btn.setToolTip(name)
                btn.setStyleSheet("")
            else:
                number = str(idx+1)
                btn.setText(
                    f"✓{number}"
                    if approved
                    else number
                )
                btn.setToolTip(name)
                btn.setStyleSheet(
                    "text-align:center;"
                )

            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _refresh_footer(self):
        key = STEPS[self.current_index][0]
        approved = self.state.approvals.get(
            key,
            False
        )

        self.back_btn.setEnabled(
            self.current_index>0
        )

        self.next_btn.setEnabled(
            self.current_index<len(STEPS)-1
        )

        self.approve_btn.setText(
            "Remover aprovação"
            if approved
            else "Aprovar etapa"
        )

        self.stage_status.setText(
            "Status: APROVADA"
            if approved
            else "Status: aguardando aprovação"
        )

        self.stage_status.setStyleSheet(
            "color:#18794e;font-weight:700;"
            if approved
            else "color:#7a5a00;font-weight:700;"
        )

    def _refresh_all(self):
        self._refresh_header()
        self._refresh_sidebar()
        self._refresh_footer()
