"""AGI WEEK motion: the speed lines of a straight and the sparks of a wheel gun."""
import math

from engine import gfx as G
from engine.core import hash01

WHITE = "#ffffff"


def burst(c, x, y, t, t0, n=28, cols=(WHITE,), speed=900.0, life=0.9, size=5.0, seed=0, gravity=500.0,
          streak=0.035):
    """Sparks thrown out from a point: each flies, slows, falls and fades, drawn as a short streak."""
    k = t - t0
    if k < 0 or k > life * 1.3:
        return
    for i in range(n):
        ang = 2 * math.pi * float(hash01(i, seed * 3 + 1)) + 0.3 * float(hash01(i, seed + 7))
        sp = speed * (0.35 + 0.65 * float(hash01(i, seed * 5 + 2)))
        lf = life * (0.55 + 0.45 * float(hash01(i, seed * 7 + 3)))
        if k > lf:
            continue
        drag = 3.2
        d = sp * (1 - math.exp(-drag * k)) / drag
        vx, vy = math.cos(ang), math.sin(ang)
        px = x + vx * d
        py = y + vy * d + 0.5 * gravity * k * k
        v = sp * math.exp(-drag * k)
        tail = v * streak
        a = (1 - k / lf) ** 1.5
        col = cols[i % len(cols)]
        c.drawLine(px, py, px - vx * tail, py - vy * tail - gravity * k * streak,
                   G.P(col, a, stroke=size * (0.5 + 0.5 * float(hash01(i, seed + 11))), cap="round"))


def speed_lines(c, cx, cy, amt, t, col=WHITE, n=70, seed=4):
    """Radial streaks rushing out from the centre, for pushes and drops."""
    if amt <= 0.01:
        return
    for i in range(n):
        ang = 2 * math.pi * float(hash01(i, seed))
        ph = (float(hash01(i, seed + 1)) + t * (1.6 + 1.4 * float(hash01(i, seed + 2)))) % 1.0
        r0 = 200 + 1300 * ph * ph
        L = (80 + 420 * ph) * amt
        x0, y0 = cx + math.cos(ang) * r0, cy + math.sin(ang) * r0 * 0.7
        x1, y1 = cx + math.cos(ang) * (r0 + L), cy + math.sin(ang) * (r0 + L) * 0.7
        c.drawLine(x0, y0, x1, y1, G.P(col, amt * 0.55 * math.sin(math.pi * ph), stroke=1.5 + 2 * ph, cap="round"))
