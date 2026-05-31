from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QCheckBox, QFrame, QSpinBox, QDoubleSpinBox, QFormLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
from datum_sim.core.settings import AppSettings
from datum_sim.ui.viewport import ToolMode, PathMode
from datum_sim.simulation.tool_database import all_tools


class SimPanel(QWidget):

    tool_mode_changed = Signal(object)   # Renderer: Point/Cylinder/None
    path_mode_changed = Signal(object)
    tool_selected     = Signal(object)   # Datenbank: echtes ToolDefinition

    _TOOL_MODES = [ToolMode.CYLINDER, ToolMode.POINT, ToolMode.NONE]
    _PATH_MODES = [PathMode.FULL, PathMode.PROGRESSIVE, PathMode.NONE]

    _TOOL_LABELS = {
        ToolMode.CYLINDER: "Endmill",
        ToolMode.POINT:    "Point",
        ToolMode.NONE:     "None",
    }
    _PATH_LABELS = {
        PathMode.FULL:        "Complete",
        PathMode.PROGRESSIVE: "Progressive",
        PathMode.NONE:        "None",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._s = AppSettings.instance()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # ── Aktives Werkzeug (Datenbank) ──────────────────────────────
        main_layout.addWidget(QLabel("Tool"))
        tool_db_layout = QFormLayout()
        tool_db_layout.setContentsMargins(0, 0, 0, 0)
        tool_db_layout.setSpacing(8)
        self._tool_db_selection = QComboBox()
        self._tools = all_tools()
        for t in self._tools:
            self._tool_db_selection.addItem(
                f"T{t.tool_number} – {t.remark} (Ø{t.diameter}mm)"
            )
        tool_db_layout.addRow("Active", self._tool_db_selection)
        main_layout.addLayout(tool_db_layout)

        # ── Darstellung (Renderer) ────────────────────────────────────
        main_layout.addWidget(QLabel("Tool Display"))
        tool_mode_layout = QFormLayout()
        tool_mode_layout.setContentsMargins(0, 0, 0, 0)
        tool_mode_layout.setSpacing(8)
        self._tool_selection = QComboBox()   # ← wieder vorhanden
        self._tool_selection.addItem("Endmill")
        self._tool_selection.addItem("Point")
        self._tool_selection.addItem("None")
        tool_mode_layout.addRow("Display", self._tool_selection)
        main_layout.addLayout(tool_mode_layout)

        # ── Pfad ─────────────────────────────────────────────────────
        main_layout.addWidget(QLabel("Path Settings"))
        path_layout = QFormLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(8)
        self._path_selection = QComboBox()
        self._path_selection.addItem("Complete")
        self._path_selection.addItem("Progressive")
        self._path_selection.addItem("None")
        path_layout.addRow("Path", self._path_selection)
        main_layout.addLayout(path_layout)

        main_layout.addStretch()
        self.setLayout(main_layout)

        # Gespeicherte Werte laden – vor connect()
        self._load_saved()

        # Signals verbinden
        self._tool_db_selection.currentIndexChanged.connect(self._on_tool_db_changed)
        self._tool_selection.currentIndexChanged.connect(self._on_tool_changed)
        self._path_selection.currentIndexChanged.connect(self._on_path_changed)

    # ── Laden ─────────────────────────────────────────────────────────

    def _load_saved(self):
        saved_tool = self._s.tool_mode   # "Endmill" / "Point" / "None"
        saved_path = self._s.path_mode

        for i in range(self._tool_selection.count()):
            if self._tool_selection.itemText(i) == saved_tool:
                self._tool_selection.setCurrentIndex(i)
                break

        for i in range(self._path_selection.count()):
            if self._path_selection.itemText(i) == saved_path:
                self._path_selection.setCurrentIndex(i)
                break

    # ── Callbacks ─────────────────────────────────────────────────────

    def _on_tool_db_changed(self, index: int):
        if 0 <= index < len(self._tools):
            self.tool_selected.emit(self._tools[index])

    def _on_tool_changed(self, index: int):
        if 0 <= index < len(self._TOOL_MODES):
            mode = self._TOOL_MODES[index]
            self._s.tool_mode = self._tool_selection.itemText(index)
            self.tool_mode_changed.emit(mode)

    def _on_path_changed(self, index: int):
        if 0 <= index < len(self._PATH_MODES):
            mode = self._PATH_MODES[index]
            self._s.path_mode = self._path_selection.itemText(index)
            self.path_mode_changed.emit(mode)

    # ── Externe Setter ────────────────────────────────────────────────

    def set_current_tool(self, tool_number: int):
        for i, t in enumerate(self._tools):
            if t.tool_number == tool_number:
                self._tool_db_selection.blockSignals(True)
                self._tool_db_selection.setCurrentIndex(i)
                self._tool_db_selection.blockSignals(False)
                break

    def set_tool_mode(self, mode: ToolMode):
        label = self._TOOL_LABELS.get(mode)
        if label is None:
            return
        index = self._tool_selection.findText(label)
        if index >= 0:
            self._tool_selection.blockSignals(True)
            self._tool_selection.setCurrentIndex(index)
            self._tool_selection.blockSignals(False)

    def set_path_mode(self, mode: PathMode):
        label = self._PATH_LABELS.get(mode)
        if label is None:
            return
        index = self._path_selection.findText(label)
        if index >= 0:
            self._path_selection.blockSignals(True)
            self._path_selection.setCurrentIndex(index)
            self._path_selection.blockSignals(False)