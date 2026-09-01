# datum_sim/tools/tool_mesh.py
from __future__ import annotations
import numpy as np
from datum_sim.simulation.tool_definition import ToolDefinition, ToolType


def build_tool_mesh(
        tool: ToolDefinition,
        segments: int = 64,  # <-- Erhöht von 32 auf 64 für perfekte Rundung
        z_steps: int = 128,  # <-- Erhöht von 48 auf 128 für feine Z-Auflösung (Kugelkopf!)
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:  # <-- Gibt jetzt auch Colors zurück
    """
    Solid of Revolution aus profile_radius_at(z).
    Gibt (vertices, normals, colors) zurück, alle als float32 Arrays.
    """
    # Wenn es ein Kugelkopf oder Torusfräser ist, spendieren wir dynamisch mehr Z-Schritte,
    # damit die Krümmung an der Spitze extrem smooth gerendert wird.
    if tool.tool_type in (ToolType.BALL_ENDMILL, ToolType.BULL_ENDMILL):
        z_steps = max(z_steps, 256)
        segments = max(segments, 64)

    angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    z_vals = np.linspace(0.0, tool.total_length, z_steps)
    radii = np.array([tool.profile_radius_at(z) for z in z_vals])

    verts: list = []
    norms: list = []
    colors: list = []

    # Farbdefinitionen
    COLOR_CUTTING = [1.0, 0.84, 0.0]  # Aggressives Schneiden-Rot
    COLOR_SHANK = [0.5, 0.5, 0.5]  # Neutrales Schaft-Grau

    # ── Mantel ───────────────────────────────────────────────────────
    for k in range(len(z_vals) - 1):
        z0, z1 = z_vals[k], z_vals[k + 1]
        r0, r1 = radii[k], radii[k + 1]
        dz = z1 - z0

        # Bestimmen, ob diese Z-Schicht zur Schneide gehört
        # Wir prüfen die Mitte der aktuellen Schicht
        if (z0 + z1) / 2.0 <= tool.cutting_length:
            layer_color = COLOR_CUTTING
        else:
            layer_color = COLOR_SHANK

        for j in range(segments):
            a0 = angles[j]
            a1 = angles[(j + 1) % segments]
            c0, s0 = np.cos(a0), np.sin(a0)
            c1, s1 = np.cos(a1), np.sin(a1)

            p = [
                [r0 * c0, r0 * s0, z0], [r0 * c1, r0 * s1, z0],
                [r1 * c0, r1 * s0, z1], [r1 * c1, r1 * s1, z1],
            ]

            # Kegelmantel-Normale: radial + dz-Anteil
            dr = r0 - r1
            nz = dr / max(np.sqrt(dr ** 2 + dz ** 2), 1e-9)
            nr = dz / max(np.sqrt(dr ** 2 + dz ** 2), 1e-9)
            n = [[c0 * nr, s0 * nr, nz], [c1 * nr, s1 * nr, nz]]

            # Geometrie & Normalen hinzufügen (2 Dreiecke = 6 Vertices)
            verts += [p[0], p[1], p[2], p[1], p[3], p[2]]
            norms += [n[0], n[1], n[0], n[1], n[1], n[0]]

            # Farbe für alle 6 Vertices der Triangles hinzufügen
            colors += [layer_color] * 6

    # ── Spitze / Boden ───────────────────────────────────────────────
    # Da die Spitze bei z=0 liegt, ist sie logischerweise immer Schneide
    r_tip = radii[0]
    if r_tip < 0.05:
        tip = [0.0, 0.0, 0.0]
        r1 = radii[1]
        z1 = z_vals[1]
        for j in range(segments):
            a0, a1 = angles[j], angles[(j + 1) % segments]
            verts += [tip,
                      [r1 * np.cos(a0), r1 * np.sin(a0), z1],
                      [r1 * np.cos(a1), r1 * np.sin(a1), z1]]
            norms += [[0, 0, -1]] * 3
            colors += [COLOR_CUTTING] * 3
    else:
        for j in range(segments):
            a0, a1 = angles[j], angles[(j + 1) % segments]
            verts += [[0, 0, 0],
                      [r_tip * np.cos(a0), r_tip * np.sin(a0), 0],
                      [r_tip * np.cos(a1), r_tip * np.sin(a1), 0]]
            norms += [[0, 0, -1]] * 3
            colors += [COLOR_CUTTING] * 3

    # ── Deckfläche ───────────────────────────────────────────────────
    # Die Deckfläche ist ganz oben am Schaftende, also Schaft-Grau
    r_top = radii[-1]
    z_top = z_vals[-1]
    for j in range(segments):
        a0, a1 = angles[j], angles[(j + 1) % segments]
        verts += [[0, 0, z_top],
                  [r_top * np.cos(a0), r_top * np.sin(a0), z_top],
                  [r_top * np.cos(a1), r_top * np.sin(a1), z_top]]
        norms += [[0, 0, 1]] * 3
        colors += [COLOR_SHANK] * 3

    return (
        np.array(verts, dtype='f4'),
        np.array(norms, dtype='f4'),
        np.array(colors, dtype='f4')
    )