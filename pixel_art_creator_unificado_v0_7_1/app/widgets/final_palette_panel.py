from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout,
    QScrollArea, QPushButton
)

from ..simplification_service import sort_palette_by_similarity


def _text_color(rgb):
    r, g, b = rgb
    luminance = (0.299*r + 0.587*g + 0.114*b)
    return "#111111" if luminance > 150 else "#ffffff"


class FinalPalettePanel(QFrame):
    selectionChanged = Signal()

    def __init__(self):
        super().__init__()

        self.palette = []
        self.essential = []
        self.selected_removals = set()
        self.buttons = {}

        self.setStyleSheet("""
            QFrame {
                background:#fbfcfe;
                border:1px solid #d6dce5;
                border-radius:8px;
            }
            QLabel {
                border:none;
                background:transparent;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(8,6,8,6)
        root.setSpacing(4)

        self.title = QLabel("PALETA FINAL")
        self.title.setStyleSheet("font-weight:700;")
        root.addWidget(self.title)

        self.hint = QLabel(
            "As cores aparecem agrupadas por similaridade visual. "
            "Clique nas cores complementares muito parecidas que deseja remover; "
            "as essenciais (★) permanecem protegidas."
        )
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("font-size:11px;color:#59616d;")
        root.addWidget(self.hint)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumHeight(150)
        root.addWidget(self.scroll)

        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setContentsMargins(4,4,4,4)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(6)
        self.scroll.setWidget(self.grid_widget)

        self.summary = QLabel("")
        self.summary.setStyleSheet("font-size:11px;color:#59616d;")
        root.addWidget(self.summary)

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.buttons = {}

    def _button_style(self, rgb, essential, selected):
        border = "#1677d2" if essential else "#555555"
        width = 3 if essential else 1
        if selected:
            border = "#d83b01"
            width = 4

        text = _text_color(rgb)
        return (
            "QPushButton {"
            f"background: rgb({rgb[0]}, {rgb[1]}, {rgb[2]});"
            f"color:{text};"
            f"border:{width}px solid {border};"
            "border-radius:6px;"
            "font-weight:700;"
            "padding:4px;"
            "}"
            "QPushButton:hover { border-color:#ff9f1c; }"
        )

    def set_palette(self, palette, essential):
        self.palette = [tuple(int(v) for v in c) for c in palette]
        self.essential = [tuple(int(v) for v in c) for c in essential]
        essential_set = set(self.essential)
        palette_set = set(self.palette)

        self.selected_removals = {
            rgb for rgb in self.selected_removals
            if rgb in palette_set and rgb not in essential_set
        }

        self._clear_grid()

        ordered = sort_palette_by_similarity(self.palette)
        cols = 10

        for i, rgb in enumerate(ordered):
            essential_flag = rgb in essential_set
            selected = rgb in self.selected_removals

            label = f"{'★ ' if essential_flag else ''}{i+1:02d}\n#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
            btn = QPushButton(label)
            btn.setFixedSize(92, 64)
            btn.setCheckable(not essential_flag)
            btn.setChecked(selected)
            btn.setStyleSheet(
                self._button_style(rgb, essential_flag, selected)
            )

            if essential_flag:
                btn.setToolTip(
                    f"RGB {rgb} • ESSENCIAL protegida • não pode ser removida nesta etapa"
                )
            else:
                btn.setToolTip(
                    f"RGB {rgb} • complementar • clique para marcar/desmarcar remoção"
                )
                btn.toggled.connect(
                    lambda checked, color=rgb: self._toggle_color(color, checked)
                )

            self.buttons[rgb] = btn
            self.grid.addWidget(btn, i//cols, i%cols)

        self._refresh_summary()

    def _toggle_color(self, rgb, checked):
        rgb = tuple(rgb)
        if rgb in set(self.essential):
            return

        if checked:
            self.selected_removals.add(rgb)
        else:
            self.selected_removals.discard(rgb)

        btn = self.buttons.get(rgb)
        if btn:
            btn.setStyleSheet(
                self._button_style(
                    rgb,
                    False,
                    rgb in self.selected_removals
                )
            )

        self._refresh_summary()
        self.selectionChanged.emit()

    def clear_selection(self):
        if not self.selected_removals:
            return

        self.selected_removals.clear()

        for rgb, btn in self.buttons.items():
            if rgb in set(self.essential):
                continue
            btn.blockSignals(True)
            btn.setChecked(False)
            btn.blockSignals(False)
            btn.setStyleSheet(
                self._button_style(rgb, False, False)
            )

        self._refresh_summary()
        self.selectionChanged.emit()

    def selected_colors(self):
        return [
            rgb for rgb in self.palette
            if rgb in self.selected_removals
        ]

    def selected_count(self):
        return len(self.selected_removals)

    def _refresh_summary(self):
        essential_set = set(self.essential)
        self.summary.setText(
            f"{len(self.palette)} cores finais • "
            f"{len(essential_set)} essenciais protegidas (★) • "
            f"{max(0, len(self.palette)-len(essential_set))} complementares • "
            f"{len(self.selected_removals)} marcadas para remover"
        )
