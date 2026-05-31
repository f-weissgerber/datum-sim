# datum_sim/gcode/sim_player.py
import time
import numpy as np
from datum_sim.gcode.path_buffer import PathBuffer

class SimulationPlayer:

    def __init__(self, path: PathBuffer):
        self._path       = path
        self._s          = 0.0
        self._running    = False
        self._last_t     = None
        self.speed_scale = 1.0

    def play(self):
        self._running = True
        self._last_t  = time.perf_counter()

    def pause(self):
        self._running = False

    def reset(self):
        self._running = False
        self._s       = 0.0

    def seek(self, fraction: float):
        self._s = float(np.clip(fraction, 0.0, 1.0)) * self._path.total_length

    def current_s(self) -> float:
        """Current arc-length for Viewport.set_progress()."""
        return self._s

    def tick(self) -> np.ndarray:
        now = time.perf_counter()
        if self._running and self._last_t is not None:
            dt   = now - self._last_t
            feed = self._path.feed_at(self._s)
            if feed < 1e-6:
                feed = 1000.0                    # G0 Rapid

            self._s += (feed / 60.0) * dt * self.speed_scale
            self._s  = min(self._s, self._path.total_length)

            if self._s >= self._path.total_length:
                self._running = False

        self._last_t = now
        return self._path.position_at(self._s)

    def current_position(self) -> np.ndarray:
        return self._path.position_at(self._s)

    def current_line(self) -> int:
        return self._path.line_at(self._s)

    def progress(self) -> float:
        if self._path.total_length < 1e-9:
            return 0.0
        return self._s / self._path.total_length