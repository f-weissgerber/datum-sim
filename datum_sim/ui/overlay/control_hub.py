import re
from pathlib import Path
from PySide6.QtWidgets import (
    QLabel, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QSlider, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui  import QFont, QIcon
from datum_sim.core.settings import AppSettings

ICONS_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"

_WCS_NAMES = {
    1: "G54", 2: "G55", 3: "G56", 4: "G57", 5: "G58",
    6: "G59", 7: "G59.1", 8: "G59.2", 9: "G59.3",
}

_LABEL_STYLE = """
    QLabel {
        background: rgba(24, 24, 26, 200);
        border: 1px solid rgba(255, 255, 255, 12%);
        border-radius: 6px;
        color: #E2E8F0;
        padding-left: 8px;
        padding-right: 8px;
        font-size: 13px;
        font-family: Consolas;
    }
"""

_BTN_STYLE = """
    QPushButton {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
    }
    QPushButton:hover {
        background: rgba(255, 255, 255, 8%);
        border: 1px solid rgba(255, 255, 255, 10%);
    }
    QPushButton:pressed {
        background: rgba(255, 255, 255, 15%);
        border: 1px solid rgba(255, 255, 255, 20%);
    }
"""


class GCodeLine(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self._colors = {
            "G": "#E06C75", "M": "#E06C75",
            "F": "#E5C07B", "S": "#C678DD",
        }

    def set_gcode(self, raw_text: str):
        def color_replacer(match):
            letter = match.group(1).upper()
            color  = self._colors.get(letter, "#E0E0E0")
            return f'<span style="color:{color};">{letter}{match.group(2)}</span>'
        text = re.sub(r'([A-Za-z])([-+]?\d*\.?\d+)', color_replacer, raw_text)
        text = re.sub(r'(\(.*?\))', r'<span style="color:#7F848E;">\1</span>', text)
        self.setText(text)


class ControlHub(QWidget):

    play_clicked          = Signal()
    pause_clicked         = Signal()
    stop_clicked          = Signal()
    skip_forward_clicked  = Signal()
    skip_backward_clicked = Signal()
    speed_changed         = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(500, 100)
        self._state = 0
        self._s     = AppSettings.instance()

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # ── Steuerleiste ──────────────────────────────────────────────
        btn_row = QHBoxLayout()

        self.btn_play_pause    = QPushButton(self)
        self.btn_stop          = QPushButton(self)
        self.btn_skip_backward = QPushButton(self)
        self.btn_skip_forward  = QPushButton(self)

        self.btn_play_pause.setIcon(   QIcon(str(ICONS_DIR / "player-play.svg")))
        self.btn_stop.setIcon(         QIcon(str(ICONS_DIR / "player-stop.svg")))
        self.btn_skip_backward.setIcon(QIcon(str(ICONS_DIR / "player-skip-back.svg")))
        self.btn_skip_forward.setIcon( QIcon(str(ICONS_DIR / "player-skip-forward.svg")))

        for btn in [self.btn_skip_backward, self.btn_play_pause,
                    self.btn_skip_forward, self.btn_stop]:
            btn.setFixedSize(40, 40)
            btn.setIconSize(QSize(24, 24))
            btn.setStyleSheet(_BTN_STYLE)
            btn_row.addWidget(btn)

        btn_row.addStretch()

        self.slider_speed = QSlider(Qt.Horizontal, self)
        self.slider_speed.setRange(0, 2000)
        self.slider_speed.setValue(100)
        self.slider_speed.setFixedWidth(150)
        self.slider_speed.setStyleSheet("""
            QSlider { background: transparent; }
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255,255,255,15%);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #E2E8F0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #E2E8F0;
                width: 12px; height: 12px;
                margin-top: -4px; margin-bottom: -4px;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover { background: #FFFFFF; }
        """)
        btn_row.addWidget(self.slider_speed)
        root.addLayout(btn_row)

        # ── Info-Zeile ────────────────────────────────────────────────
        self._info_row = QHBoxLayout()
        self._info_row.setSpacing(6)

        # Datum (WCS)
        self._datum_lbl = QLabel("G54", self)
        self._datum_lbl.setFixedWidth(54)
        self._datum_lbl.setAlignment(Qt.AlignCenter)
        self._datum_lbl.setStyleSheet(_LABEL_STYLE)

        # GCode-Zeile (expandierend)
        self._gcode_line = GCodeLine(self)
        self._gcode_line.setStyleSheet(_LABEL_STYLE)

        # Tool
        self._tool_lbl = QLabel("T1", self)
        self._tool_lbl.setFixedWidth(40)
        self._tool_lbl.setAlignment(Qt.AlignCenter)
        self._tool_lbl.setStyleSheet(_LABEL_STYLE)

        # Feedrate
        self._feed_lbl = QLabel("F  0", self)
        self._feed_lbl.setFixedWidth(90)
        self._feed_lbl.setAlignment(Qt.AlignCenter)
        self._feed_lbl.setStyleSheet(_LABEL_STYLE)

        self._info_row.addWidget(self._datum_lbl)
        self._info_row.addWidget(self._gcode_line)
        self._info_row.addWidget(self._tool_lbl)
        self._info_row.addWidget(self._feed_lbl)
        root.addLayout(self._info_row)

        # ── Sichtbarkeit aus AppSettings laden ────────────────────────
        self._datum_lbl.setVisible(self._s.show_datum)
        self._gcode_line.setVisible(self._s.show_gcode_line)
        self._tool_lbl.setVisible(self._s.show_tool)
        self._feed_lbl.setVisible(self._s.show_feedrate)

        # ── Signals verbinden ─────────────────────────────────────────
        self.btn_play_pause.clicked.connect(self._play_pause_clicked)
        self.btn_stop.clicked.connect(self._stop_clicked)
        self.btn_skip_forward.clicked.connect(self.skip_forward_clicked)
        self.btn_skip_backward.clicked.connect(self.skip_backward_clicked)
        self.slider_speed.valueChanged.connect(
            lambda v: self.speed_changed.emit(v / 100.0)
        )

        # AppSettings → Sichtbarkeit
        self._s.show_datum_changed.connect(self._datum_lbl.setVisible)
        self._s.show_gcode_line_changed.connect(self._gcode_line.setVisible)
        self._s.show_tool_changed.connect(self._tool_lbl.setVisible)
        self._s.show_feedrate_changed.connect(self._feed_lbl.setVisible)

    # ── Daten setzen ──────────────────────────────────────────────────

    def set_gcode(self, raw_text: str):
        self._gcode_line.set_gcode(raw_text)

    def set_datum(self, wcs_index: int):
        """WCS-Index 1–9 → G54–G59.3"""
        self._datum_lbl.setText(_WCS_NAMES.get(wcs_index, f"G{wcs_index}"))

    def set_tool(self, tool_number: int):
        self._tool_lbl.setText(f"T{tool_number}")

    def set_feedrate(self, feed_mm_min: float):
        """Vorschub in mm/min → kompakt anzeigen."""
        if feed_mm_min < 1.0:
            self._feed_lbl.setText("Rapid")
        else:
            self._feed_lbl.setText(f"F {int(feed_mm_min)}")

    # ── Buttons ───────────────────────────────────────────────────────

    def _play_pause_clicked(self):
        if self._state == 0:
            self.btn_play_pause.setIcon(QIcon(str(ICONS_DIR / "player-pause.svg")))
            self._state = 1
            self.play_clicked.emit()
        else:
            self.btn_play_pause.setIcon(QIcon(str(ICONS_DIR / "player-play.svg")))
            self._state = 0
            self.pause_clicked.emit()

    def _stop_clicked(self):
        self.btn_play_pause.setIcon(QIcon(str(ICONS_DIR / "player-play.svg")))
        self._state = 0
        self.stop_clicked.emit()

    def reset_play_state(self):
        """Von außen aufrufbar wenn Simulation zurückgesetzt wird."""
        self.btn_play_pause.setIcon(QIcon(str(ICONS_DIR / "player-play.svg")))
        self._state = 0