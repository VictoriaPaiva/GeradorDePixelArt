
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class BaseStep(QWidget):
    def __init__(self, title, description):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 20, 24, 20)
        self.layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 24px; font-weight: 700;")
        self.layout.addWidget(title_label)

        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; color: #525966;")
        self.layout.addWidget(desc)
