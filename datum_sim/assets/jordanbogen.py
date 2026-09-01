import matplotlib.pyplot as plt
import numpy as np

# Figure-Setup
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# ----------------------------------------------------------------
# 1. Jordan-Bogen (Offene, injektive Kurve)
# ----------------------------------------------------------------
t_arc = np.linspace(0, 1.5 * np.pi, 100)
x_arc = t_arc * np.cos(t_arc)
y_arc = t_arc * np.sin(t_arc)

ax1.plot(x_arc, y_arc, color='#1f77b4', linewidth=2.5, label='Jordan-Bogen')
# Start- und Endpunkt markieren
ax1.scatter([x_arc[0], x_arc[-1]], [y_arc[0], y_arc[-1]], color='red', s=50, zorder=5)
ax1.text(x_arc[0] + 0.1, y_arc[0], 'Start f(a)', fontsize=10, fontweight='bold')
ax1.text(x_arc[-1] - 0.6, y_arc[-1] + 0.2, 'Ende f(b)', fontsize=10, fontweight='bold')

ax1.set_title('Jordan-Bogen\n(Offen, kein Selbstdurchschnitt)', fontsize=12, pad=10)
ax1.axis('equal')
ax1.grid(True, linestyle='--', alpha=0.6)

# ----------------------------------------------------------------
# 2. Jordan-Kurve (Geschlossene, einfache Kurve)
# ----------------------------------------------------------------
t_curve = np.linspace(0, 2 * np.pi, 200)
# Eine leicht deformierte Kreisform (Amoeben-artig), um zu zeigen, dass es kein perfekter Kreis sein muss
x_curve = (2 + 0.3 * np.sin(4 * t_curve)) * np.cos(t_curve)
y_curve = (2 + 0.3 * np.sin(4 * t_curve)) * np.sin(t_curve)

ax2.plot(x_curve, y_curve, color='#2ca02c', linewidth=2.5, label='Jordan-Kurve')
# Gemeinsamen Start-/Endpunkt markieren
ax2.scatter([x_curve[0]], [y_curve[0]], color='red', s=50, zorder=5)
ax2.text(x_curve[0] + 0.1, y_curve[0] + 0.1, 'Start f(a) = Ende f(b)', fontsize=10, fontweight='bold')

# Einfärben des "Inneren" zur Demonstration des Jordanschen Kurvensatzes
ax2.fill(x_curve, y_curve, color='#2ca02c', alpha=0.1)

ax2.set_title('Jordan-Kurve\n(Geschlossen, teilt Ebene in Innen/Außen)', fontsize=12, pad=10)
ax2.axis('equal')
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.show()