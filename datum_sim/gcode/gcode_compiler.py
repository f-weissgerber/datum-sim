"""
Compiling piepline for the gcode

Code.ngc -> Lexer (Tokenizing) -> Parser -> Motion Planner -> Path (numpy-Array)
"""

from pathlib import Path
from dataclasses import dataclass
from datum_sim.gcode.lexer          import tokenize
from datum_sim.gcode.parser         import parse
from datum_sim.gcode.motion_planner import plan, MotionSegment
from datum_sim.gcode.path_buffer    import PathBuffer


@dataclass
class GCodeProgram:
    raw_lines: list[str]
    clean_lines: list[str]
    segments:  list[MotionSegment]
    path:      PathBuffer

class GCodeCompiler:
    def __init__(self):
        pass

    # Entry Point
    def load_file(self, path: str) -> GCodeProgram:
        raw_lines = Path(path).read_text().splitlines()

        # ALLE Zeilen tokenisieren – kein Filter hier
        tokens_per_line = [tokenize(line) for line in raw_lines]

        # clean_lines hat exakt denselben Index wie raw_lines
        clean_lines = []
        for tokens in tokens_per_line:
            if tokens:
                clean_lines.append(" ".join(f"{t.letter}{t.value:g}" for t in tokens))
            else:
                clean_lines.append("")

        commands = parse(tokens_per_line)  # Parser überspringt leere intern
        segments = plan(commands)
        buf = PathBuffer(segments)

        return GCodeProgram(
            raw_lines=raw_lines,
            clean_lines=clean_lines,
            segments=segments,
            path=buf,
        )