from datum_sim.gcode.lexer import Token
from dataclasses import dataclass, field

@dataclass
class GCodeCommand:
    line_index: int
    g_codes:    list[int]           = field(default_factory=list)
    m_codes:    list[int]           = field(default_factory=list)
    parameters: dict[str, float]    = field(default_factory=dict)

def parse(tokens_per_line: list[list[Token]]) -> list[GCodeCommand]:
    commands = []

    for index, raw in enumerate(tokens_per_line):
        if not raw:
            continue
        cmd = GCodeCommand(line_index=index)

        for t in raw:
            if t.letter == 'G':
                cmd.g_codes.append(int(t.value))
            elif t.letter == 'M':
                cmd.m_codes.append(int(t.value))
            else:
                cmd.parameters[t.letter] = t.value

        commands.append(cmd)

    return commands
