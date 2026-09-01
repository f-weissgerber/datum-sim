"""
Einstiegspunkt für:
  python -m datum_sim
  datum-sim                   (nach pip install)
  datum-sim datei.ngc         (Datei direkt öffnen)
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat


def _configure_opengl():
    """OpenGL 3.3 Core Profile – Pflicht für ModernGL."""
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    fmt.setDepthBufferSize(24)
    fmt.setSamples(4)
    fmt.setAlphaBufferSize(8)   # nicht mehr zwingend nötig seit Corner-Fill-Lösung, aber unschädlich
    QSurfaceFormat.setDefaultFormat(fmt)


def main():
    _configure_opengl()
    app = QApplication(sys.argv)

    from datum_sim.core.perf_monitor import PerfMonitor
    #monitor = PerfMonitor(interval=2.0)
    #monitor.start()

    from datum_sim.ui.main_widget import DatumSimWidget
    win = DatumSimWidget()
    win.setWindowTitle("Datum Sim")
    win.resize(1280, 800)

    # Loading the gcode file
    print("Test", sys.argv[0])
    win.set_file("./gcode.ngc")

    win.show()
    win.set_mode("MACHINE")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()