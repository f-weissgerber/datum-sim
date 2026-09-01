# datum_sim/core/perf_monitor.py
import time
import os
import threading
import psutil


class PerfMonitor:
    """
    Gibt alle `interval` Sekunden eine Zeile in die Konsole aus.
    Läuft in einem eigenen Daemon-Thread – kein Qt nötig.

    Ausgabe:
    [PERF]  FPS: 58.3  |  RAM: 142 MB  |  CPU: 12.4%  |  Frame: 17.1ms
    """

    def __init__(self, interval: float = 2.0):
        self._interval   = interval
        self._running    = False
        self._thread:    threading.Thread | None = None
        self._process    = psutil.Process(os.getpid())

        # Frame-Zähler – wird von außen inkrementiert
        self._frame_count = 0
        self._frame_times: list[float] = []
        self._last_frame_t = time.perf_counter()

    # ── Aufruf pro Frame (aus paintGL oder _tick) ─────────────────────

    def tick(self):
        """Einmal pro Frame aufrufen."""
        now   = time.perf_counter()
        delta = now - self._last_frame_t
        self._last_frame_t = now
        self._frame_count += 1
        self._frame_times.append(delta)
        # Nur die letzten 120 Frames behalten
        if len(self._frame_times) > 120:
            self._frame_times.pop(0)

    # ── Hintergrund-Thread ────────────────────────────────────────────

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            time.sleep(self._interval)
            self._print()

    # datum_sim/core/perf_monitor.py

    def _print(self):
        if self._frame_times:
            avg_ms = sum(self._frame_times) / len(self._frame_times) * 1000
            fps = 1000.0 / avg_ms if avg_ms > 0 else 0.0
        else:
            avg_ms = 0.0
            fps = 0.0

        mem = self._process.memory_info()
        # private = nur dieser Prozess, entspricht Task Manager
        mem_mb = getattr(mem, 'private', mem.rss) / 1024 / 1024

        # cpu_percent durch Kernanzahl → entspricht Task Manager %
        cpu_raw = self._process.cpu_percent(interval=None)
        cpu_cores = psutil.cpu_count(logical=True) or 1
        cpu = cpu_raw / cpu_cores

        print(
            f"[PERF]  "
            f"FPS: {fps:5.1f}  |  "
            f"Frame: {avg_ms:5.1f}ms  |  "
            f"RAM: {mem_mb:6.1f} MB  |  "
            f"CPU: {cpu:5.1f}%"
        )