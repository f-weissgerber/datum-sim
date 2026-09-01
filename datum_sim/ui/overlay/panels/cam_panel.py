from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QComboBox, QCheckBox, QSlider, QFormLayout,
)
from PySide6.QtCore import Qt
from datum_sim.core.settings import AppSettings


class CamPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._s = AppSettings.instance()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # ── View ─────────────────────────────────────────────────────
        main_layout.addWidget(QLabel("View"))

        view_layout = QFormLayout()
        view_layout.setContentsMargins(0, 0, 0, 0)
        view_layout.setSpacing(8)

        self._color_box = QComboBox()
        current = self._s.bg_color
        for name, hex_val in AppSettings.BG_COLORS.items():
            self._color_box.addItem(name, hex_val)
            if hex_val == current:
                self._color_box.setCurrentText(name)
        view_layout.addRow("Background", self._color_box)

        main_layout.addLayout(view_layout)

        # Grid

        grid_layout = QFormLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(8)

        self._show_grid = self._make_checkbox("show_grid")
        grid_layout.addRow("Show Grid", self._show_grid)

        main_layout.addLayout(grid_layout)


        # ── Camera Speed ─────────────────────────────────────────────
        main_layout.addWidget(QLabel("Camera"))

        speed_layout = QFormLayout()
        speed_layout.setContentsMargins(0, 0, 0, 0)
        speed_layout.setSpacing(8)

        self._zoom_slider   = self._make_slider("zoom_speed")
        self._rotate_slider = self._make_slider("rotate_speed")
        self._pan_slider    = self._make_slider("pan_speed")

        speed_layout.addRow("Zoom",     self._zoom_slider)
        speed_layout.addRow("Rotation", self._rotate_slider)
        speed_layout.addRow("Pan",      self._pan_slider)

        main_layout.addLayout(speed_layout)

        # ── Invert ───────────────────────────────────────────────────
        main_layout.addWidget(QLabel("Invert"))

        invert_layout = QFormLayout()
        invert_layout.setContentsMargins(0, 0, 0, 0)
        invert_layout.setSpacing(8)

        self._cb_zoom     = self._make_checkbox("invert_zoom")
        self._cb_rotate_x = self._make_checkbox("invert_rotate_x")
        self._cb_rotate_y = self._make_checkbox("invert_rotate_y")
        self._cb_pan_x    = self._make_checkbox("invert_pan_x")
        self._cb_pan_y    = self._make_checkbox("invert_pan_y")

        invert_layout.addRow("Zoom",       self._cb_zoom)
        invert_layout.addRow("Rotation X", self._cb_rotate_x)
        invert_layout.addRow("Rotation Y", self._cb_rotate_y)
        invert_layout.addRow("Pan X",      self._cb_pan_x)
        invert_layout.addRow("Pan Y",      self._cb_pan_y)

        main_layout.addLayout(invert_layout)

        main_layout.addWidget(QLabel("Info Display"))
        info_layout = QFormLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)

        self._cb_gcode = QCheckBox()
        self._cb_datum = QCheckBox()
        self._cb_tool = QCheckBox()
        self._cb_feedrate = QCheckBox()

        self._cb_gcode.setChecked(self._s.show_gcode_line)
        self._cb_datum.setChecked(self._s.show_datum)
        self._cb_tool.setChecked(self._s.show_tool)
        self._cb_feedrate.setChecked(self._s.show_feedrate)

        info_layout.addRow("GCode Line", self._cb_gcode)
        info_layout.addRow("Datum", self._cb_datum)
        info_layout.addRow("Tool", self._cb_tool)
        info_layout.addRow("Feed Rate", self._cb_feedrate)
        main_layout.addLayout(info_layout)

        main_layout.addStretch()
        self.setLayout(main_layout)

        # Signals verbinden – nach Aufbau
        self._color_box.currentIndexChanged.connect(self._on_color_changed)
        self._zoom_slider.valueChanged.connect(
            lambda v: setattr(self._s, "zoom_speed", v / 10.0)
        )
        self._rotate_slider.valueChanged.connect(
            lambda v: setattr(self._s, "rotate_speed", v / 10.0)
        )
        self._pan_slider.valueChanged.connect(
            lambda v: setattr(self._s, "pan_speed", v / 10.0)
        )
        self._cb_zoom.toggled.connect(
            lambda v: setattr(self._s, "invert_zoom", v)
        )
        self._cb_rotate_x.toggled.connect(
            lambda v: setattr(self._s, "invert_rotate_x", v)
        )
        self._cb_rotate_y.toggled.connect(
            lambda v: setattr(self._s, "invert_rotate_y", v)
        )
        self._cb_pan_x.toggled.connect(
            lambda v: setattr(self._s, "invert_pan_x", v)
        )
        self._cb_pan_y.toggled.connect(
            lambda v: setattr(self._s, "invert_pan_y", v)
        )
        self._show_grid.toggled.connect(
            lambda v: setattr(self._s, "show_grid", v)
        )
        self._cb_gcode.toggled.connect(lambda v: setattr(self._s, "show_gcode_line", v))
        self._cb_datum.toggled.connect(lambda v: setattr(self._s, "show_datum", v))
        self._cb_tool.toggled.connect(lambda v: setattr(self._s, "show_tool", v))
        self._cb_feedrate.toggled.connect(lambda v: setattr(self._s, "show_feedrate", v))

    # ── Hilfsmethoden ─────────────────────────────────────────────────

    def _make_slider(self, setting: str) -> QSlider:
        slider = QSlider(Qt.Horizontal)
        slider.setRange(1, 50)
        slider.setSingleStep(1)
        slider.setValue(int(getattr(self._s, setting) * 10))
        return slider

    def _make_checkbox(self, setting: str) -> QCheckBox:
        cb = QCheckBox()
        cb.setChecked(getattr(self._s, setting))
        return cb

    def _on_color_changed(self, _):
        self._s.bg_color = self._color_box.currentData()