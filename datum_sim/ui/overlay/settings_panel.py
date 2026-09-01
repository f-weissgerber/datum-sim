from pathlib import Path
from datum_sim.ui.overlay.panels.cam_panel import CamPanel
from datum_sim.ui.overlay.panels.sim_panel import SimPanel

from PySide6.QtWidgets import (
    QWidget, QFrame, QToolButton, QStackedWidget, QVBoxLayout
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import PySide6.QtSvg

# ── Breiten ───────────────────────────────────────────────────────────────────
STRIP_W  = 48    # Tab-Button-Leiste
PANEL_W  = 280   # Ausfahrender Inhalt

ICONS_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"

# ── Styles ────────────────────────────────────────────────────────────────────
# Fade-Breite (20px) relativ zur Strip-Breite als Gradient-Stop ausgedrückt,
# da qlineargradient-Stops nur 0..1 statt absoluter Pixelwerte kennen.
_STRIP_FADE_STOP = f"{10 / STRIP_W:.4f}"

_STRIP_STYLE_CLOSED = f"""
    QWidget {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(30, 30, 30, 0),
            stop:{_STRIP_FADE_STOP} rgba(30, 30, 30, 220),
            stop:1 rgba(30, 30, 30, 220)
        );
        border-top-right-radius: 12px;
        border-bottom-right-radius: 12px;
    }}
"""

_STRIP_STYLE_OPEN = f"""
    QWidget {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(30, 30, 30, 0),
            stop:{_STRIP_FADE_STOP} rgba(30, 30, 30, 220),
            stop:1 rgba(30, 30, 30, 220)
        );
    }}
"""

_PANEL_STYLE = """
    QFrame {
        background: rgba(30, 30, 30, 220);
        border-left: 1px solid rgba(255,255,255,30);
        border-top-right-radius: 12px;
        border-bottom-right-radius: 12px;
    }
"""


class SettingsPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(STRIP_W)

        self._active     = -1
        self._panel_open = False

        # ── Tab-Button-Leiste ─────────────────────────────────────────────────
        self._strip = QWidget(self)
        self._strip.setFixedWidth(STRIP_W)
        self._strip.setStyleSheet(_STRIP_STYLE_CLOSED)

        self._strip_layout = QVBoxLayout(self._strip)
        self._strip_layout.setContentsMargins(4, 8, 4, 8)
        self._strip_layout.setSpacing(4)
        self._strip_layout.setAlignment(Qt.AlignTop)

        # ── Inhalts-Panel ─────────────────────────────────────────────────────
        self._panel = QFrame(self)
        self._panel.setFixedWidth(PANEL_W)
        self._panel.setStyleSheet(_PANEL_STYLE)
        self._panel.hide()

        self._stack = QStackedWidget(self._panel)
        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(self._stack)

        self._tabs: list[QToolButton] = []
        self._add_tab(str(ICONS_DIR / "scan-cube.svg"), "Simulation")
        self._add_tab(str(ICONS_DIR / "view-360.svg"), "Viewport")

        self._strip_layout.addStretch()

        self._sim_panel = SimPanel(self)
        self._cam_panel = CamPanel(self)

        self.set_tab_content(0, self._sim_panel)
        self.set_tab_content(1, self._cam_panel)


    @property
    def sim_panel(self) -> SimPanel:
        return self._sim_panel

    @property
    def cam_panel(self) -> CamPanel:
        return self._cam_panel

    # ── Tab hinzufügen ────────────────────────────────────────────────────────

    def _add_tab(self, icon_path: str, tooltip: str):
        index = len(self._tabs)

        btn = QToolButton(self._strip)
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(24, 24))
        btn.setToolTip(tooltip)
        btn.setFixedSize(40, 40)
        btn.setCheckable(True)
        btn.clicked.connect(lambda _=False, i=index: self._on_tab_clicked(i))

        self._strip_layout.insertWidget(index, btn)
        self._tabs.append(btn)

        self._stack.addWidget(QWidget())

    def set_tab_content(self, index: int, widget: QWidget):
        """Inhalts-Widget für einen Tab nachträglich setzen."""
        old = self._stack.widget(index)
        self._stack.removeWidget(old)
        old.deleteLater()
        self._stack.insertWidget(index, widget)

    def _on_tab_clicked(self, index: int):
        if self._panel_open and self._active == index:
            self._close_panel()
        else:
            self._active = index
            self._stack.setCurrentIndex(index)
            for i, btn in enumerate(self._tabs):
                btn.setChecked(i == index)
            if not self._panel_open:
                self._open_panel()

    def _open_panel(self):
        self._panel_open = True
        self._strip.setStyleSheet(_STRIP_STYLE_OPEN)
        self.setFixedWidth(STRIP_W + PANEL_W)
        self._panel.show()
        self._relayout()
        if self.parent():
            self.parent()._layout_overlays()

    def _close_panel(self):
        self._panel_open = False
        self._active     = -1
        for btn in self._tabs:
            btn.setChecked(False)
        self._panel.hide()
        self._strip.setStyleSheet(_STRIP_STYLE_CLOSED)
        self.setFixedWidth(STRIP_W)
        if self.parent():
            self.parent()._layout_overlays()

    def _relayout(self):
        h = self.height()
        self._strip.setGeometry(0, 0, STRIP_W, h)
        if self._panel_open:
            self._panel.setGeometry(STRIP_W, 0, PANEL_W, h)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._relayout()