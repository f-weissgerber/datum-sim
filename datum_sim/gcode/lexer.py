from __future__ import annotations
import re
from dataclasses import dataclass

_TOKEN_RE = re.compile(
    r"([A-Za-z])\s*(-?\d*\.?\d+(?:e[+-]?\d+)?)",
    re.IGNORECASE
)

@dataclass(frozen=True, slots=True)
class Token:
    letter: str
    value: float

    def __repr__(self):
        return f"({self.letter}, {self.value})"

def tokenize(line: str) -> list[Token]:
    line = line.strip()

    if not line:
        return []
    if line.startswith("%"):
        return []
    if line.startswith("/"):
        return []

    line = re.sub(r"\(.*?\)", "", line)

    line = re.sub(r"\;.*","", line)

    tokens = []

    for letter, number in _TOKEN_RE.findall(line):
        tokens.append(Token(letter, float(number)))

    return tokens