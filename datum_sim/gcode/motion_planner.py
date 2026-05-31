from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from datum_sim.gcode.parser import GCodeCommand

#----------------------------------------------
# Segment types
#----------------------------------------------

@dataclass
class LinearSegment:
    line_index:     int
    start:          np.ndarray
    end:            np.ndarray
    feed_rate:      float
    is_rapid:       bool

@dataclass
class ArcSegment:
    line_index:     int
    start:          np.ndarray
    end:            np.ndarray
    center:         np.ndarray
    radius:         float
    clockwise:      bool        # G2 or G3
    feed_rate:      float

@dataclass
class HelixSegment:
    line_index:     int
    start:          np.ndarray
    end:            np.ndarray
    center:         np.ndarray
    radius:         float
    pitch:          float
    clockwise:      bool
    feed_rate:      float

MotionSegment = LinearSegment | ArcSegment | HelixSegment

#----------------------------------------------
# Modal State (Context for the gcode)
# Why: Whats the feedrate, G0 or G1, etc.
#----------------------------------------------

class ModalState:
    def __init__(self):
        self.motion:   int = 0                     # Active Motion (G0, G1, G2, G3)
        self.absolute:  bool = True                 # G90 (True) or G91 (False)
        self.feed_rate: float = 0.0
        self.position:  np.ndarray = np.zeros(3)

    def resolve_target(self, parameters: dict[str, float]) -> np.ndarray:
        target = self.position.copy()
        for i, axis in enumerate("XYZ"):
            if axis in parameters:
                if self.absolute:
                    target[i] = parameters[axis]
                else:
                    target[i] = self.position[i] + parameters[axis]

        return target

#----------------------------------------------
# Planner
#----------------------------------------------

def plan(commands: list[GCodeCommand]) -> list[MotionSegment]:
    modal = ModalState()
    segments = []

    for cmd in commands:

        # Set/Refresh the current modal state
        """
        class GCodeCommand:
            line_index: int
            g_codes:    list[int]           = field(default_factory=list)
            m_codes:    list[int]           = field(default_factory=list)
            parameters: dict[str, float]    = field(default_factory=dict)
        """
        for g in cmd.g_codes:
            if g in (0,1,2,3):  modal.motion = g
            elif g == 90:       modal.absolute = True
            elif g == 91:       modal.absolute = False

        if "F" in cmd.parameters:
            modal.feed_rate = cmd.parameters["F"]


        has_motion  = any(k in cmd.parameters for k in "XYZ")
        has_arc     = any(k in cmd.parameters for k in ("I", "J", "K"))
        if not has_motion and not has_arc:
            continue

        prev = modal.position.copy()
        target = modal.resolve_target(cmd.parameters)

        seg = _build_segment(cmd, modal, prev, target)
        if seg is not None:
            segments.append(seg)

        modal.position = target

    return segments

def _build_segment(cmd: GCodeCommand, modal, prev, target) -> MotionSegment | None:
    if modal.motion in (0, 1):
        return LinearSegment(line_index=cmd.line_index,
                           start=prev,
                           end=target,
                           feed_rate=modal.feed_rate,
                           is_rapid= (modal.motion == 0)
        )
    if modal.motion in (2, 3):
        return _build_arc_or_helix(cmd, modal, prev, target)

    return None

def _build_arc_or_helix(cmd: GCodeCommand, modal, prev, target) -> ArcSegment | HelixSegment | None:
    params = cmd.parameters

    # Extract the parameters
    i = params.get("I", 0.0)
    j = params.get("J", 0.0)
    k = params.get("K", 0.0)

    center = prev.copy()
    center[0] += i
    center[1] += j
    center[2] += k

    # Calculate the radius
    r_vec = prev - center
    radius = float(np.linalg.norm(r_vec[:2]))

    clockwise = (modal.motion == 2)
    z_delta = float(target[2] - prev[2])

    if abs(z_delta) < 1e-9:
        return ArcSegment(
            start=prev,
            end=target,
            center=center,
            radius=radius,
            clockwise=clockwise,
            feed_rate=modal.feed_rate,
            line_index= cmd.line_index,
        )
    else:
        a_start = np.arctan2(prev[1] - center[1], prev[0] - center[0])
        a_end = np.arctan2(target[1] - center[1], target[0] - center[0])

        if clockwise:
            if a_end >= a_start: a_end -= 2 * np.pi
        else:
            if a_end <= a_start: a_end += 2 * np.pi

        total_angle = abs(a_end - a_start)
        revolutions = total_angle / (2 * np.pi)
        pitch = z_delta / revolutions if revolutions > 1e-9 else 0.0

        return HelixSegment(
            start=prev, end=target, center=center,
            radius=radius, clockwise=clockwise,
            feed_rate=modal.feed_rate,
            pitch=pitch,
            line_index=cmd.line_index,
        )