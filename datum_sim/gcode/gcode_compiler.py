"""
Compiling piepline for the gcode

Code.ngc -> Lexer (Tokenizing) -> Parser -> Motion Planner -> Path (numpy-Array)
"""

from pathlib import Path
from dataclasses import dataclass
from datum_sim.gcode.lexer          import tokenize
from datum_sim.gcode.parser import parse, GCodeCommand
from datum_sim.gcode.motion_planner import plan, MotionSegment
from datum_sim.gcode.path_buffer    import PathBuffer

@dataclass
class ToolChange:
    line_index: int
    tool_number: int

@dataclass
class GCodeProgram:
    raw_lines: list[str]
    clean_lines: list[str]
    segments:  list[MotionSegment]
    path:      PathBuffer
    tool_changes: list[ToolChange]

def _extract_tool_changes(commands: list[GCodeCommand]) -> list[ToolChange]:
    changes = []
    pending_tool = None

    for cmd in commands:
        if "T" in cmd.parameters:
            pending_tool = int(cmd.parameters["T"])
        if 6 in cmd.m_codes and pending_tool is not None:
            changes.append(ToolChange(
                line_index=cmd.line_index,
                tool_number=pending_tool,
            ))
    return changes

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
        tool_changes = _extract_tool_changes(commands)

        return GCodeProgram(
            raw_lines=raw_lines,
            clean_lines=clean_lines,
            segments=segments,
            path=buf,
            tool_changes=tool_changes,
        )