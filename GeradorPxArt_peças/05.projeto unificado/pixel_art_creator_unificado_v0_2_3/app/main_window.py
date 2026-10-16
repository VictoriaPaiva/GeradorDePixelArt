
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QFileDialog, QMessageBox, QFrame
)

from .models.project_state import ProjectState, STEP_KEYS
from .steps.input_step import InputStep
from .steps.ai_step import AIStep
from .steps.placeholder_step import PlaceholderStep
from .steps.palette_step import PaletteStep
from .steps.essential_step import EssentialStep
from .models.palette_workspace import PaletteWorkspace


STEPS = [
    ("input", "1. Imagem"),
    ("ai", "2. Pixel Art IA"),
    ("palette", "3. Áreas e paletas"),
    ("essential", "4. Cores essenciais"),
    ("matrix", "5. Matriz 100×100"),
    ("simplification", "6. Simplificação 50"),
    ("manual", "7. Edição manual"),
    ("pattern", "8. Molde e legenda"),
    ("export", "9. Exportar"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.state = ProjectState()
        self.current_index = 0
        self.step_buttons = []
        self.pages = []
        self.palette_workspace = PaletteWorkspace.from_state_dict(self.state.metadata.get("palette_workspace", {}))

        self.setWindowTitle("Pixel Art Creator — Sistema Unificado v0.2.3")
        self.resize(1500, 930)

        self._build_ui()
        self._build_pages()
        self._refresh_all()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame { background:#20242b; }
            QLabel { color:white; }
            QPushButton {
                background:#343a45; color:white; border:0;
                padding:8px 12px; border-radius:6px;
            }
            QPushButton:hover { background:#444c59; }
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 10, 16, 10)

        title = QLabel("Pixel Art Creator")
        title.setStyleSheet("font-size:18px;font-weight:700;")
        hl.addWidget(title)

        self.project_label = QLabel("Novo projeto")
        self.project_label.setStyleSheet("color:#cdd3dc;")
        hl.addWidget(self.project_label)
        hl.addStretch(1)

        self.new_btn = QPushButton("Novo")
        self.open_btn = QPushButton("Abrir projeto")
        self.save_btn = QPushButton("Salvar projeto")
        hl.addWidget(self.new_btn)
        hl.addWidget(self.open_btn)
        hl.addWidget(self.save_btn)
        outer.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(0,0,0,0)
        body.setSpacing(0)

        # Sidebar
        side = QFrame()
        side.setFixedWidth(245)
        side.setStyleSheet("""
            QFrame { background:#f0f2f5; border-right:1px solid #d5dae2; }
            QPushButton {
                text-align:left; padding:11px 13px; border:0;
                background:transparent; border-radius:7px;
                color:#303641;
            }
            QPushButton:hover { background:#e3e7ed; }
            QPushButton[active="true"] {
                background:#dcecff;
                color:#125aa3;
                font-weight:700;
            }
        """)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(10, 14, 10, 14)
        sl.setSpacing(5)

        steps_title = QLabel("ETAPAS")
        steps_title.setStyleSheet("font-weight:700;color:#68707c;padding:4px;")
        sl.addWidget(steps_title)

        for idx, (_, name) in enumerate(STEPS):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked=False, i=idx: self.go_to(i))
            self.step_buttons.append(btn)
            sl.addWidget(btn)

        sl.addStretch(1)

        info = QLabel(
            "Padrões oficiais\n\n"
            "Matriz: 100×100\n"
            "Paleta final: 50 cores\n"
            "Grade: camada visual"
        )
        info.setStyleSheet(
            "color:#69717d; padding:8px; background:#e8ebef; border-radius:7px;"
        )
        sl.addWidget(info)
        body.addWidget(side)

        # Main area
        main = QWidget()
        ml = QVBoxLayout(main)
        ml.setContentsMargins(0,0,0,0)

        self.stack = QStackedWidget()
        ml.addWidget(self.stack, 1)

        footer = QFrame()
        footer.setStyleSheet("QFrame{border-top:1px solid #d8dde5;background:white;}")
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
                background:#1677d2;color:white;border:0;
                padding:9px 16px;border-radius:6px;font-weight:700;
            }
            QPushButton:hover { background:#1267b7; }
            QPushButton:disabled { background:#aeb7c2; }
        """)

        for b in [self.back_btn, self.next_btn]:
            b.setStyleSheet("""
                QPushButton {
                    padding:9px 14px;border:1px solid #cbd1d9;
                    border-radius:6px;background:white;
                }
            """)

        fl.addWidget(self.back_btn)
        fl.addWidget(self.approve_btn)
        fl.addWidget(self.next_btn)
        ml.addWidget(footer)

        body.addWidget(main, 1)
        outer.addLayout(body, 1)

        self.new_btn.clicked.connect(self.new_project)
        self.open_btn.clicked.connect(self.open_project)
        self.save_btn.clicked.connect(self.save_project)
        self.back_btn.clicked.connect(lambda: self.go_to(self.current_index - 1))
        self.next_btn.clicked.connect(self.next_step)
        self.approve_btn.clicked.connect(self.approve_current)

    def _build_pages(self):
        self.pages = [
            InputStep(self.state),
            AIStep(self.state),

            PaletteStep(self.state, self.palette_workspace),
            EssentialStep(self.state, self.palette_workspace),

            PlaceholderStep(
                "5. Matriz lógica 100×100",
                "Conversão determinística para a arquitetura oficial do projeto.",
                [
                    "Gerar exatamente 10.000 células.",
                    "Uma cor sólida por célula.",
                    "Sem interpolação.",
                    "Evitar média de cores.",
                    "Preferir RGB real da imagem.",
                    "Checkpoint de aprovação antes da simplificação."
                ]
            ),

            PlaceholderStep(
                "6. Simplificação para 50 cores",
                "Paleta final padrão aprovada nos testes.",
                [
                    "Começar pelas cores essenciais protegidas.",
                    "Completar até 50 com cores relevantes da própria imagem.",
                    "Preservar famílias cromáticas e contraste.",
                    "Sem dithering aleatório.",
                    "Detectar/evitar achatamento visual de grandes blocos quando possível.",
                    "Checkpoint de aprovação."
                ]
            ),

            PlaceholderStep(
                "7. Edição manual",
                "Será incorporado o editor manual aprovado.",
                [
                    "Reaproveitar pixel_art_manual_editor_v0_1_4.",
                    "Pintura da célula lógica inteira.",
                    "Paleta agrupada pelas áreas.",
                    "Hover das cores na imagem.",
                    "Conta-gotas.",
                    "Desfazer/refazer.",
                    "Salvar matriz técnica real 100×100.",
                    "Salvar preview e versão com grade."
                ]
            ),

            PlaceholderStep(
                "8. Molde e legenda",
                "Será incorporado o Pattern Generator aprovado.",
                [
                    "Reaproveitar pixel_art_pattern_generator_v0_1.",
                    "Gerar códigos A…Z, Aa, Ab…",
                    "Código em cada célula.",
                    "Grade.",
                    "Numeração de linhas e colunas.",
                    "Legenda com RGB, HEX, quantidade e percentual."
                ]
            ),

            PlaceholderStep(
                "9. Exportar",
                "Centralização das saídas finais do projeto.",
                [
                    "PNG técnico 100×100.",
                    "PNG ampliado.",
                    "PNG com grade.",
                    "Molde com códigos.",
                    "Legenda.",
                    "JSON, CSV e TXT.",
                    "Futuramente PDF pronto para impressão."
                ]
            ),
        ]

        for p in self.pages:
            self.stack.addWidget(p)

    def _replace_state(self, new_state):
        self.state = new_state
        self.palette_workspace = PaletteWorkspace.from_state_dict(
            self.state.metadata.get("palette_workspace", {})
        )

        self.pages[0].state = self.state
        self.pages[1].state = self.state
        self.pages[2].set_context(self.state, self.palette_workspace)
        self.pages[3].set_context(self.state, self.palette_workspace)

        self.pages[0].refresh()
        self.pages[1].refresh()
        self._refresh_all()

    def new_project(self):
        if self.state.dirty:
            answer = QMessageBox.question(
                self,
                "Novo projeto",
                "Existem alterações não salvas. Criar um novo projeto mesmo assim?",
                QMessageBox.Yes | QMessageBox.No
            )
            if answer != QMessageBox.Yes:
                return
        self._replace_state(ProjectState())
        self.go_to(0)

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir projeto", "", "Projeto Pixel Art (*.pixelart.json *.json)"
        )
        if not path:
            return
        try:
            state = ProjectState.load(path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao abrir projeto", str(e))
            return
        self._replace_state(state)
        self.go_to(0)

    def save_project(self):
        path = self.state.project_file
        if not path:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar projeto",
                "meu_projeto.pixelart.json",
                "Projeto Pixel Art (*.pixelart.json)"
            )
            if not path:
                return
            if not path.lower().endswith(".pixelart.json"):
                path += ".pixelart.json"

        try:
            self.state.save(path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar projeto", str(e))
            return

        self._refresh_header()
        QMessageBox.information(self, "Projeto salvo", f"Projeto salvo em:\n{path}")

    def go_to(self, index):
        index = max(0, min(len(STEPS)-1, index))
        self.current_index = index
        self.stack.setCurrentIndex(index)
        if index == 2:
            self.pages[2].refresh()
        elif index == 3:
            self.pages[3].refresh()
        self._refresh_all()

    def next_step(self):
        # Require approval to move forward, except final page.
        key = STEPS[self.current_index][0]
        if self.current_index < len(STEPS)-1 and not self.state.approvals.get(key, False):
            QMessageBox.information(
                self,
                "Etapa ainda não aprovada",
                "Aprove esta etapa antes de continuar.\n\n"
                "A versão final terá checkpoints exatamente para evitar que "
                "mudanças visuais avancem sem sua confirmação."
            )
            return
        self.go_to(self.current_index + 1)

    def approve_current(self):
        key = STEPS[self.current_index][0]

        # Minimal prerequisites for the two active pages.
        if key == "input" and not self.state.source_image_path:
            QMessageBox.information(self, "Sem imagem", "Selecione uma imagem primeiro.")
            return
        if key == "ai" and not self.state.ai_image_path:
            QMessageBox.information(
                self, "Sem Pixel Art",
                "Importe uma Pixel Art gerada para continuar."
            )
            return
        if key == "palette" and not self.pages[2].is_ready():
            QMessageBox.information(
                self, "Paletas incompletas",
                "Crie pelo menos uma área com paleta antes de aprovar esta etapa."
            )
            return
        if key == "essential" and self.pages[3].unique_count() == 0:
            QMessageBox.information(
                self, "Sem cores essenciais",
                "Selecione pelo menos uma cor essencial antes de aprovar esta etapa."
            )
            return

        if self.state.approvals.get(key, False):
            self.state.unapprove(key)
        else:
            self.state.approve(key)

        self._refresh_all()

    def _refresh_header(self):
        name = self.state.project_name
        if self.state.project_file:
            name = Path(self.state.project_file).stem
        marker = " *" if self.state.dirty else ""
        self.project_label.setText(name + marker)

    def _refresh_sidebar(self):
        for idx, btn in enumerate(self.step_buttons):
            key = STEPS[idx][0]
            active = idx == self.current_index
            btn.setProperty("active", active)

            approved = self.state.approvals.get(key, False)
            prefix = "✓ " if approved else ""
            btn.setText(prefix + STEPS[idx][1])

            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _refresh_footer(self):
        key = STEPS[self.current_index][0]
        approved = self.state.approvals.get(key, False)

        self.back_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(STEPS)-1)

        self.approve_btn.setText(
            "Remover aprovação" if approved else "Aprovar etapa"
        )

        self.stage_status.setText(
            "Status: APROVADA" if approved else "Status: aguardando aprovação"
        )
        self.stage_status.setStyleSheet(
            "color:#18794e;font-weight:700;" if approved
            else "color:#7a5a00;font-weight:700;"
        )

    def _refresh_all(self):
        self._refresh_header()
        self._refresh_sidebar()
        self._refresh_footer()
