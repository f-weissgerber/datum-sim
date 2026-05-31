from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer
from datum_sim.ui.viewport import Viewport, ToolMode, PathMode
from datum_sim.ui.overlay.settings_panel import SettingsPanel
from datum_sim.gcode.gcode_compiler import GCodeCompiler
from datum_sim.simulation.simulation_player import SimulationPlayer
from datum_sim.ui.overlay.control_hub import ControlHub
from datum_sim.simulation.tool_database import get_tool
from datum_sim.simulation.tool_definition import ToolDefinition
from datum_sim.core.settings import AppSettings


class DatumSimWidget(QWidget):

    _TOOL_MAP = {
        "Endmill": ToolMode.CYLINDER,
        "Point":   ToolMode.POINT,
        "None":    ToolMode.NONE,
    }
    _PATH_MAP = {
        "Complete":    PathMode.FULL,
        "Progressive": PathMode.PROGRESSIVE,
        "None":        PathMode.NONE,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport    = Viewport(self)
        self.settings    = SettingsPanel(self)
        self.control_hub = ControlHub(self)
        self.compiler    = GCodeCompiler()

        self._player:               SimulationPlayer | None = None
        self._state                 = "IDLE"
        self._mode                  = "SIM"
        self._clean_lines:          list[str] = []
        self._tool_changes:         list      = []
        self._last_tool_change_idx: int       = -1
        self._path_mode             = PathMode.FULL
        self._tool_mode             = ToolMode.POINT

        self.settings.sim_panel.tool_mode_changed.connect(self.set_tool_mode)
        self.settings.sim_panel.path_mode_changed.connect(self.set_path_mode)
        self.settings.sim_panel.tool_selected.connect(self._apply_tool)

        self._render_timer = QTimer(self)
        self._render_timer.setInterval(16)
        self._render_timer.timeout.connect(self._tick)
        self._render_timer.start()

        self._connect_control_hub()
        self._layout_overlays()

    # ── Datei ─────────────────────────────────────────────────────────

    def set_file(self, path: str):
        self._load_file(path)

    def _load_file(self, path: str):
        programm = self.compiler.load_file(path)
        self._clean_lines = programm.clean_lines
        self._player = SimulationPlayer(programm.path)
        self._tool_changes = programm.tool_changes
        self._last_tool_change_idx = -1

        self.viewport.set_path(programm.path)

        # Modus ZUERST setzen – bevor set_tool_definition update() triggert
        s = AppSettings.instance()
        self.set_tool_mode(self._TOOL_MAP.get(s.tool_mode, ToolMode.CYLINDER))  # ← CYLINDER als Fallback
        self.set_path_mode(self._PATH_MAP.get(s.path_mode, PathMode.PROGRESSIVE))

        # Dann Werkzeug setzen
        if programm.tool_changes:
            first = get_tool(programm.tool_changes[0].tool_number)
            self._apply_tool(first)
        else:
            self._apply_tool(get_tool(1))

    # ── Werkzeug ──────────────────────────────────────────────────────

    def _apply_tool(self, tool: ToolDefinition | None):
        if tool is None:
            return
        self._current_tool = tool
        self.viewport.set_tool_definition(tool)
        self.settings.sim_panel.set_current_tool(tool.tool_number)

    def _check_tool_change(self, current_line: int):
        for tc in self._tool_changes:
            if tc.line_index <= current_line and tc.line_index > self._last_tool_change_idx:
                self._last_tool_change_idx = tc.line_index
                self._apply_tool(get_tool(tc.tool_number))

    # ── Maschinen-API ─────────────────────────────────────────────────

    def set_state(self, state: str):
        self._state = state

    def set_position(self, x: float, y: float, z: float):
        if self._mode == "MACHINE":
            import numpy as np
            self.viewport.set_tool_position(np.array([x, y, z], dtype='f4'))

    def set_line(self, line: int):
        self.viewport.set_active_line(line)

    # ── Modus ─────────────────────────────────────────────────────────

    def set_mode(self, mode: str):
        assert mode in ("SIM", "MACHINE")
        self._mode = mode
        if mode == "SIM" and self._player:
            self._player.reset()

    def set_path_mode(self, mode: PathMode):
        self._path_mode = mode
        self.viewport.set_path_mode(mode)
        self.settings.sim_panel.set_path_mode(mode)

    def set_tool_mode(self, mode: ToolMode):
        self._tool_mode = mode
        self.viewport.set_tool_mode(mode)
        self.settings.sim_panel.set_tool_mode(mode)

    # ── ControlHub ────────────────────────────────────────────────────

    def _connect_control_hub(self):
        self.control_hub.play_clicked.connect(self.sim_play)
        self.control_hub.pause_clicked.connect(self.sim_pause)
        self.control_hub.stop_clicked.connect(self.sim_reset)
        self.control_hub.speed_changed.connect(self.sim_set_speed)
        self.control_hub.skip_forward_clicked.connect(
            lambda: self.sim_seek(min(self._player.progress() + 0.05, 1.0))
            if self._player else None
        )
        self.control_hub.skip_backward_clicked.connect(
            lambda: self.sim_seek(max(self._player.progress() - 0.05, 0.0))
            if self._player else None
        )

    # ── Simulation ────────────────────────────────────────────────────

    def sim_play(self):
        if self._player: self._player.play()

    def sim_pause(self):
        if self._player: self._player.pause()

    def sim_reset(self):
        if self._player:
            self._player.reset()
            self._last_tool_change_idx = -1

    def sim_seek(self, fraction: float):
        if self._player: self._player.seek(fraction)

    def sim_set_speed(self, speed: float):
        if self._player: self._player.speed_scale = speed

    def push_machine_position(self, x: float, y: float, z: float):
        pass

    # ── Tick ──────────────────────────────────────────────────────────

    def _tick(self):
        if self._mode == "SIM":
            if self._player is None:
                self.viewport.update()
                return

            pos  = self._player.tick()
            line = self._player.current_line()
            s    = self._player.current_s()

            self._check_tool_change(line)

            self.viewport.set_tool_position(pos)
            self.viewport.set_active_line(line)
            self.viewport.set_progress(s)

            if self._clean_lines and 0 <= line < len(self._clean_lines):
                self.control_hub.set_gcode(f"({line}) {self._clean_lines[line]}")

        self.viewport.update()

    # ── Layout ────────────────────────────────────────────────────────

    def _layout_overlays(self):
        W, H = self.width(), self.height()
        self.viewport.setGeometry(0, 0, W, H)

        sw = self.settings.width()
        self.settings.setGeometry(W - sw, 0, sw, H)

        cw, ch = self.control_hub.width(), self.control_hub.height()
        self.control_hub.setGeometry((W - cw) // 2, H - ch - 16, cw, ch)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._layout_overlays()