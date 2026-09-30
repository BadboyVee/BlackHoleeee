"""HORIZON's mark and its agents' icons. The mark is a half sun on three horizon lines, each shorter than the one
above, as a sunrise lies on the sea; Scout's icon is it in a round glossy button, Radar's in a rounded square."""
import skia

from engine import gfx as G
from engine.core import clamp, out_cubic, out_back
from .look import WHITE, GOLD, GOLD2, VIOLET, T, rr, sans

BARS = [(8, 58, 84), (20, 72, 60), (32, 86, 36)]     # (x, y, width) in a 100-unit box; 8 units thick


def mark(c, x, y, size, t=None, t0=0.0, sun=GOLD, bars=WHITE, a=1.0):
    """The mark centred on (x, y), size units across. With t, it builds from t0: the lines slide in from the left
    one after another, then the sun rises from behind the top one."""
    k = size / 100.0
    with G.xf(c, x - 50 * k, y - 60 * k, s=k):
        with G.layer(c, a):
            for i, (bx, by, bw) in enumerate(BARS):
                u = 1.0 if t is None else clamp((t - (t0 + 0.07 * i)) / 0.32)
                if u <= 0:
                    continue
                e = out_cubic(u)
                w = bw * e
                c.drawRRect(rr(bx + (bw - w) * 0.5 - 30 * (1 - e), by, w, 8, 4), G.P(bars, clamp(u * 2)))
            u = 1.0 if t is None else clamp((t - (t0 + 0.22)) / 0.45)
            if u > 0:
                rise = 30 * (1 - out_back(u, 1.6))
                c.save()
                c.clipRect(skia.Rect.MakeLTRB(-50, -50, 150, 55))
                disc = skia.Path()
                disc.addCircle(50, 50 + rise, 26)
                g = G.linear_grad(50, 24, 50, 54, [GOLD, GOLD2])
                c.drawPath(disc, G.P(sun, 1, shader=g))
                c.restore()


def wordmark(c, x, y, size, col=WHITE, a=1.0, align=0.5):
    return T(c, "Horizon", x, y, sans(size, 560), col, a, align=align, tracking=-0.02)


def lockup(c, x, y, size, t=None, t0=0.0, a=1.0):
    """The mark and the name side by side, centred on (x, y); size is the name's cap size in px."""
    f = sans(size, 560)
    w = f.width("Horizon", -0.02)
    m = size * 1.25
    gap = size * 0.28
    total = m + gap + w
    x0 = x - total / 2
    mark(c, x0 + m / 2, y - size * 0.36, m, t=t, t0=t0, a=a)
    if t is None:
        wordmark(c, x0 + m + gap, y, size, a=a, align=0.0)
    else:
        from .look import blur_in
        with G.layer(c, a):
            blur_in(c, "Horizon", x0 + m + gap, y, f, WHITE, t, t0 + 0.3, dur=0.5, tracking=-0.02)


def icon(c, x, y, size, shape="square", a=1.0, glow=1.0):
    """An agent's app icon: glossy near-black, a violet-blue rim light, the mark in the middle."""
    r = size * (0.5 if shape == "round" else 0.23)
    with G.layer(c, a):
        body = rr(x - size / 2, y - size / 2, size, size, r)
        if glow > 0:
            c.drawRRect(rr(x - size / 2, y - size / 2 + size * 0.06, size, size, r),
                        G.P(VIOLET, 0.35 * glow, blur=size * 0.18))
        c.drawRRect(body, G.P("#101014", 1, shader=G.linear_grad(x, y - size / 2, x, y + size / 2,
                                                                 ["#2a2a33", "#0b0b0e"])))
        c.save()
        c.clipRRect(body, True)
        c.drawOval(skia.Rect.MakeXYWH(x - size * 0.7, y - size * 1.05, size * 1.4, size * 0.9),
                   G.P(WHITE, 0.08))                                   # the gloss
        c.restore()
        c.drawRRect(rr(x - size / 2 + 1.5, y - size / 2 + 1.5, size - 3, size - 3, r - 1.5),
                    G.P("#7d86ff", 0.9, stroke=max(2.0, size * 0.035),
                        shader=G.linear_grad(x - size / 2, y - size / 2, x + size / 2, y + size / 2,
                                             ["#c9ceff", "#5d6bff", "#1c1f3a"])))
        mark(c, x, y + size * 0.05, size * 0.62)
