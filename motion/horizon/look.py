"""HORIZON look: black and white, a thin Inter for everything said, one sunrise gold for the brand, a violet light
streak for moments of insight, and two painted-in-Blender plates (green hills under a blue sky, the sea at
sunset) graded vivid and clean."""
from functools import lru_cache

import skia

from engine import gfx as G
from engine.core import clamp, out_cubic

WHITE = "#ffffff"
BLACK = "#000000"
INK = "#0b0b0c"
GREY = "#8e8e93"
DIM = "#5c5c62"
PANEL = "#141416"
PANEL2 = "#1c1c1f"
LINE = "#2a2a2e"
GOLD = "#ffb23e"
GOLD2 = "#ff7a2f"
VIOLET = "#8c8cff"
GREEN = "#34c759"
RED = "#ff453a"
BLUE = "#3d8bff"
SANS = "inter"


@lru_cache(maxsize=None)
def F(fam, size, **axes):
    return G.Font(fam, size, **axes)


def sans(size, w=300):
    return F(SANS, size, wght=w)


def mono(size, w=420):
    return F("mono", size, wght=w)


def italic(size):
    return F("serif-italic", size)


def T(c, s, x, y, font, col, a=1.0, align=0.0, tracking=0.0):
    if a <= 0 or not s:
        return None
    return G.text(c, s, x, y, font, G.P(col, min(1.0, a)), align=align, tracking=tracking)


def rr(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def blur_in(c, s, x, y, font, col, t, t0, dur=0.45, align=0.0, tracking=0.0, blur=14.0, dy=0.0, a=1.0):
    """A word that comes into focus: fades up out of a blur, drifting dy into place."""
    u = clamp((t - t0) / dur)
    if u <= 0:
        return None
    e = out_cubic(u)
    b = blur * (1 - e)
    with G.layer(c, a * clamp(u * 1.8), blur=b):
        return T(c, s, x, y + dy * (1 - e), font, col, 1.0, align, tracking)


def blur_out(t, t0, dur=0.35):
    """(alpha, blur) for something going out of focus from t0."""
    u = clamp((t - t0) / dur)
    return 1 - u, 18 * u


def words_line(c, t, parts, cx, y, font, col, gap=None, times=None, dur=0.4, blur=12.0):
    """A centred line whose words come into focus one by one: parts are (word, font or None, colour or None)."""
    fonts = [p[1] or font for p in parts]
    sp = font.width(" ") if gap is None else gap
    widths = [f.width(p[0]) for p, f in zip(parts, fonts)]
    total = sum(widths) + sp * (len(parts) - 1)
    x = cx - total / 2
    for i, (p, f, w) in enumerate(zip(parts, fonts, widths)):
        t0 = times[i] if times else 0.0
        blur_in(c, p[0], x, y, f, p[2] or col, t, t0, dur=dur, blur=blur)
        x += w + sp
    return total


def hairline(c, x0, y0, x1, y1, col=WHITE, a=1.0, w=1.2):
    c.drawLine(x0, y0, x1, y1, G.P(col, a, stroke=w))


def wrap(s, font, width):
    """Split s into lines no wider than width."""
    lines, cur = [], ""
    for w in s.split():
        nxt = (cur + " " + w).strip()
        if cur and font.width(nxt) > width:
            lines.append(cur)
            cur = w
        else:
            cur = nxt
    if cur:
        lines.append(cur)
    return lines


def chip(c, x, y, s, fg, bg, size=13, a=1.0):
    """A small caps label in a rounded pill, its left edge at x and its middle at y. Returns its width."""
    f = F(SANS, size, wght=650)
    w = f.width(s, 0.08) + size * 1.4
    h = size * 1.9
    c.drawRRect(rr(x, y - h / 2, w, h, h / 2), G.P(bg, a))
    T(c, s, x + size * 0.7, y + size * 0.36, f, fg, a, tracking=0.08)
    return w
