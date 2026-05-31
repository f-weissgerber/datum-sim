from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer
from datum_sim.ui.viewport import Viewport, ToolMode, PathMode
from datum_sim.ui.overlay.settings_panel import SettingsPanel
from datum_sim.gcode.gcode_compiler import GCodeCompiler
from datum_sim.simulation.simulation_player import SimulationPlayer
from datum_sim.ui.overlay.control_hub import ControlHub
from datum_sim.ui.overlay.panels.sim_panel import SimPanel

from datum_sim.core.settings import AppSettings

class DatumSimWidget(QWidget):
    _TOOL_MAP = {
        "Endmill": ToolMode.CYLINDER,
        "Point": ToolMode.POINT,
        "None": ToolMode.NONE,
    }
    _PATH_MAP = {
        "Complete": PathMode.FULL,
        "Progressive": PathMode.PROGRESSIVE,
        "None": PathMode.NONE,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport = Viewport(self)
        self.settings = SettingsPanel(self)
        self.control_hub = ControlHub(self)
        self.compiler = GCodeCompiler()

        self._player: SimulationPlayer | None = None
        self._state = "IDLE"
        self._mode  = "SIM"
        self._clean_lines: list[str] = []

        self.settings.sim_panel.tool_mode_changed.connect(self.set_tool_mode)
        self.settings.sim_panel.path_mode_changed.connect(self.set_path_mode)

        # Timer → _tick, nicht viewport.update direkt
        self._render_timer = QTimer(self)
        self._render_timer.setInterval(16)
        self._render_timer.timeout.connect(self._tick)   # ← fix
        self._render_timer.start()

        self._connect_control_hub()
        self._layout_overlays()

    # ── Datei ─────────────────────────────────────────────────────────

    def set_file(self, path: str):
        self._load_file(path)

    def _load_file(self, path: str):
        programm      = self.compiler.load_file(path)
        self._clean_lines = programm.clean_lines
        print(self._clean_lines)
        self._player  = SimulationPlayer(programm.path)
        self.viewport.set_path(programm.path)

        s = AppSettings.instance()
        tool_mode = self._TOOL_MAP.get(s.tool_mode, ToolMode.POINT)
        path_mode = self._PATH_MAP.get(s.path_mode, PathMode.PROGRESSIVE)

        # Viewport aktualisieren
        self.set_tool_mode(tool_mode)
        self.set_path_mode(path_mode)

    # ── Maschinen-API ─────────────────────────────────────────────────

    def set_state(self, state: str):           # "IDLE" | "RUNNING" | "PAUSED"
        self._state = state

    def set_position(self, x: float, y: float, z: float):
        if self._mode == "MACHINE":
            self.viewport.set_tool_position(
                __import__('numpy').array([x, y, z], dtype='f4')
            )

    def set_line(self, line: int):
        self.viewport.set_active_line(line)

    # ── Modus ─────────────────────────────────────────────────────────

    def set_mode(self, mode: str):
        assert mode in ("SIM", "MACHINE")
        self._mode = mode
        if mode == "SIM" and self._player:
            self._player.reset()

    def set_path_mode(self, mode: PathMode):
        print("PathMode", mode)
        self._path_mode = mode
        self.viewport.set_path_mode(mode)      # einmalig setzen

    def set_tool_mode(self, mode: ToolMode):
        print("Tool mode:", mode)
        self._tool_mode = mode
        self.viewport.set_tool_mode(mode)      # einmalig setzen

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
        if self._player: self._player.reset()

    def sim_seek(self, fraction: float):
        if self._player: self._player.seek(fraction)

    def sim_set_speed(self, speed: float):
        if self._player: self._player.speed_scale = speed

    def push_machine_position(self, x: float, y: float, z: float):
        pass   # MachineAdapter folgt später

    # ── Tick – jeden Frame ────────────────────────────────────────────

    def _tick(self):
        if self._mode == "SIM":
            if self._player is None:
                self.viewport.update()
                return
            pos = self._player.tick()
            line = self._player.current_line()
            prog = self._player.progress()
            s = self._player.current_s()  # ← mm-Bogenlänge

            self.viewport.set_tool_position(pos)
            self.viewport.set_active_line(line)
            self.viewport.set_progress(s)  # ← s statt prog

            self.control_hub.set_gcode("("+str(line)+") "+self._clean_lines[line])

        self.viewport.update()

    # ── Layout ────────────────────────────────────────────────────────

    def _layout_overlays(self):
        W = self.width()
        H = self.height()

        # Viewport füllt alles
        self.viewport.setGeometry(0, 0, W, H)

        # Settings rechts oben
        sw = self.settings.width()
        self.settings.setGeometry(W - sw, 0, sw, H)

        # ControlHub unten mittig
        cw = self.control_hub.width()    # 450 (fixedSize)
        ch = self.control_hub.height()   # 100 (fixedSize)
        margin_bottom = 16
        self.control_hub.setGeometry(
            (W - cw) // 2,              # horizontal zentriert
            H - ch - margin_bottom,     # unten mit Abstand
            cw,
            ch,
        )


    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._layout_overlays()