
from PySide6.QtWidgets import QLabel, QFrame, QVBoxLayout

from .base_step import BaseStep


class PlaceholderStep(BaseStep):
    def __init__(self, title, description, planned_items):
        super().__init__(title, description)

        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: #fbfbfc;
                border: 1px solid #d8dde5;
                border-radius: 10px;
            }
        """)
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(18, 18, 18, 18)
        planned_title = QLabel("Funcionalidades que serão integradas nesta etapa")
        planned_title.setStyleSheet("font-weight:700; font-size:14px;")
        pl.addWidget(planned_title)

        for item in planned_items:
            lab = QLabel(f"• {item}")
            lab.setWordWrap(True)
            pl.addWidget(lab)

        pl.addStretch(1)
        self.layout.addWidget(panel, 1)
