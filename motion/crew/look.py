"""CLAUDE CODE look: white, one heavy tight grotesk for the lines (Inter, black weight), small grey captions,
light grey cards with soft shadows, and the crew's own colours."""
from functools import lru_cache

import skia

from engine import gfx as G
from engine.core import clamp, out_cubic, out_back

WHITE = "#ffffff"
INK = "#0d0d0f"
GREY = "#8b8b93"
SOFT = "#b5b5bc"
CARD = "#f6f6f8"
CARD_LINE = "#ececf0"
CORAL = "#e0785a"
MINT = "#3ec995"
LAVENDER = "#a78bfa"
SKY = "#3b9bff"
INDIGO = "#5a5fd6"
RED = "#ff4d4f"
GREEN = "#22c55e"
BLUE = "#2f7bff"


@lru_cache(maxsize=None)
def F(fam, size, **axes):
    return G.Font(fam, size, **axes)


def heavy(size):
    return F("inter", size, wght=800)


def sans(size, w=500):
    return F("inter", size, wght=w)


def mono(size, w=460):
    return F("mono", size, wght=w)


def T(c, s, x, y, font, col, a=1.0, align=0.0, tracking=0.0):
    if a <= 0 or not s:
        return None
    return G.text(c, s, x, y, font, G.P(col, min(1.0, a)), align=align, tracking=tracking)


def rr(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def card(c, x, y, w, h, r=18, a=1.0, fill=CARD):
    if a <= 0:
        return
    c.drawRRect(rr(x, y + 10, w, h, r), G.P("#1b1d2a", 0.07 * a, blur=22))
    c.drawRRect(rr(x, y, w, h, r), G.P(fill, a))
    c.drawRRect(rr(x + 0.5, y + 0.5, w - 1, h - 1, r), G.P(CARD_LINE, a, stroke=1.2))


def line(c, t, s, t0, y=640, size=74, col=INK, out=None, x=960):
    """A big line that springs up into place from t0 (and drops away from out)."""
    u = clamp((t - t0) / 0.32)
    if u <= 0:
        return
    k = out_back(u, 1.8) if u < 1 else 1.0
    a = clamp(u * 3)
    if out is not None:
        v = clamp((t - out) / 0.18)
        a *= 1 - v
        k *= 1 - 0.1 * v
    if a <= 0:
        return
    f = heavy(size)
    with G.xf(c, x, y - size * 0.35, s=0.6 + 0.4 * k):
        T(c, s, 0, size * 0.35 + 18 * (1 - min(k, 1.0)), f, col, a, align=0.5, tracking=-0.045)


def caption(c, t, s, t0, y, out=None, size=26, col=GREY):
    u = clamp((t - t0) / 0.3)
    if u <= 0:
        return
    a = clamp(u * 2)
    if out is not None:
        a *= 1 - clamp((t - out) / 0.2)
    T(c, s, 960, y + 8 * (1 - out_cubic(u)), sans(size, 500), col, a, align=0.5, tracking=-0.01)


def pop(t, t0, dur=0.34, s=2.2):
    u = clamp((t - t0) / dur)
    return 0.0 if u <= 0 else (out_back(u, s) if u < 1 else 1.0)
