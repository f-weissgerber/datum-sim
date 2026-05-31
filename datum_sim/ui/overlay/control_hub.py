import re
from pathlib import Path
from PySide6.QtWidgets import QLabel, QWidget, QToolButton, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Signal

ICONS_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"

class GCodeLine(QLabel):
    def __init__(self, parent=None, realtime: bool = False):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding))
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.setStyleSheet("""
                    QLabel {
                        background: rgba(24, 24, 26, 200);
                        border: 1px solid rgba(255, 255, 255, 12%);
                        border-radius: 6px;
                        color: #E2E8F0;
                        padding-left: 16px;
                        padding-right: 16px;
                    }
                """)

        mono_font = QFont("Consolas", 12)
        mono_font.setStyleHint(QFont.Monospace)
        self.setFont(mono_font)

        # Color Coding
        self._colors = {
            "G": "#E06C75", "M": "#E06C75",
            "F": "#E5C07B", "S": "#C678DD"
        }

    def set_gcode(self, raw_text: str):
        """Takes raw gcode line, applies color code and displays it"""
        def color_replacer(match):
            letter = match.group(1).upper()
            value = match.group(2)
            color = self._colors.get(letter, "#E0E0E0")
            return f'<span style="color: {color};">{letter}{value}</span>'

        #Commands
        formatted_text = re.sub(r'([A-Za-z])([-+]?\d*\.?\d+)', color_replacer, raw_text)
        # Comments
        formatted_text = re.sub(r'(\(.*?\))', r'<span style="color: #7F848E;">\1</span>', formatted_text)
        self.setText(formatted_text)

class ControlHub(QWidget):
    # Signals
    play_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    skip_forward_clicked = Signal()
    skip_backward_clicked = Signal()
    speed_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(450, 100)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        self.btn_layout = QHBoxLayout()
        self.btn_play_pause= QPushButton(self)
        self.btn_play_pause.setIcon(QIcon(str(ICONS_DIR / "player-play.svg")))

        self._state = 0

        #self.btn_pause = QPushButton(self)
        #self.btn_pause.setIcon(QIcon(str(ICONS_DIR / "player-pause.svg")))

        self.btn_stop = QPushButton(self)
        self.btn_stop.setIcon(QIcon(str(ICONS_DIR / "player-stop.svg")))
        self.btn_skip_backward = QPushButton(self)
        self.btn_skip_backward.setIcon(QIcon(str(ICONS_DIR / "player-skip-back.svg")))
        self.btn_skip_forward = QPushButton(self)
        self.btn_skip_forward.setIcon(QIcon(str(ICONS_DIR / "player-skip-forward.svg")))

        for btn in [self.btn_skip_backward, self.btn_play_pause, self.btn_skip_forward, self.btn_stop]:
            btn.setFixedSize(40, 40)
            btn.setIconSize(QSize(24, 24))
            btn.setStyleSheet("""
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
            """)
            self.btn_layout.addWidget(btn)

        self.btn_layout.addStretch()

        self.slider_speed = QSlider(Qt.Horizontal, self)
        self.slider_speed.setRange(0, 2000)
        self.slider_speed.setValue(100)

        self.slider_speed.setFixedWidth(150)
        self.slider_speed.setStyleSheet("""
                    QSlider {
                        background: transparent;
                    }
                    /* Die Schiene im Hintergrund */
                    QSlider::groove:horizontal {
                        height: 4px;
                        background: rgba(255, 255, 255, 15%);
                        border-radius: 2px;
                    }
                    /* Der bereits "ausgefüllte" Teil links vom Regler */
                    QSlider::sub-page:horizontal {
                        background: #E2E8F0;
                        border-radius: 2px;
                    }
                    /* Der runde Bedienknopf */
                    QSlider::handle:horizontal {
                        background: #E2E8F0;
                        width: 12px;
                        height: 12px;
                        margin-top: -4px;     /* Zentriert den Knopf auf der 4px-Schiene */
                        margin-bottom: -4px;
                        border-radius: 6px;
                    }
                    /* Dezentes Aufhellen des Knopfes beim Hovern */
                    QSlider::handle:horizontal:hover {
                        background: #FFFFFF;
                    }
                """)
        self.btn_layout.addWidget(self.slider_speed)

        self.main_layout.addLayout(self.btn_layout)

        self.gcode_line = GCodeLine(self)
        self.main_layout.addWidget(self.gcode_line)

        # Connect signals
        self.btn_play_pause.clicked.connect(self._play_pause_clicked)
        self.btn_stop.clicked.connect(self._stop_clicked)
        self.btn_skip_forward.clicked.connect(self.skip_forward_clicked)
        self.btn_skip_backward.clicked.connect(self.skip_backward_clicked)
        self.slider_speed.valueChanged.connect(
            lambda v: self.speed_changed.emit(v / 100.0)
        )

    def set_gcode(self, raw_text: str):
        self.gcode_line.set_gcode(raw_text)

    def _play_pause_clicked(self):
        if self._state == 0:
            self.btn_play_pause.setIcon(QIcon(str(ICONS_DIR / "player-pause.svg")))
            self._state = 1
            self.play_clicked.emit()
        elif self._state == 1:
            self.btn_play_pause.setIcon(QIcon(str(ICONS_DIR / "player-play.svg")))
            self._state = 0
            self.pause_clicked.emit()

    def _stop_clicked(self):
        self.btn_play_pause.setIcon(QIcon(str(ICONS_DIR / "player-play.svg")))
        self.stop_clicked.emit()
        self._state = 0

    def _on_speed_changed(self, value: int):
        speed = value / 100.0  # 1→0.01×, 100→1.0×, 1000→10.0×
        self.speed_changed.emit(speed)