"""VEEE look: a clean product-film system. Near-white ground with a faint grid, black type in Geist, one blue for
everything that matters, Instrument Serif italic for the word the line turns on, Geist Mono for the comments in
the corners, and a 1-bit dithered mascot and 1-bit stills of the films."""
from functools import lru_cache

import skia

from engine import gfx as G
from engine.core import clamp, out_quart, out_cubic, out_back

WHITE = "#ffffff"
PAPER = "#fafafa"
GRIDLINE = "#efefef"
INK = "#0a0a0a"
BLUE = "#2361ea"
BLUE_TINT = "#f2f5fc"
BLUE_LINE = "#c9d8fb"
GREY = "#8a8a8a"
SOFT = "#a3a3a3"
LINE = "#e6e6e6"
SANS, MONO = "geist", "geist-mono"


@lru_cache(maxsize=None)
def F(fam, size, **axes):
    return G.Font(fam, size, **axes)


def sans(size, w=560):
    return F(SANS, size, wght=w)


def mono(size, w=460):
    return F(MONO, size, wght=w)


def italic(size):
    return F("serif-italic", size)


def wordmark(size):
    return F("archivo", size, wght=850, wdth=118)


def T(c, s, x, y, font, col, a=1.0, align=0.0, tracking=0.0):
    if a <= 0 or not s:
        return None
    return G.text(c, s, x, y, font, G.P(col, min(1.0, a)), align=align, tracking=tracking)


def rr(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def card(c, x, y, w, h, r=22, a=1.0, fill=WHITE, border=LINE, shadow=0.05):
    if a <= 0:
        return
    if shadow > 0:
        c.drawRRect(rr(x, y + 10, w, h, r), G.P("#000000", shadow * a, blur=24))
    c.drawRRect(rr(x, y, w, h, r), G.P(fill, a))
    if border:
        c.drawRRect(rr(x + 0.5, y + 0.5, w - 1, h - 1, r), G.P(border, a, stroke=1.4))


def pulse(t, a, b, ramp=0.05):
    """0 before a, up to 1 within ramp, held, back to 0 by b."""
    if t <= a or t >= b:
        return 0.0
    return clamp(min((t - a) / ramp, (b - t) / ramp))


def rise(c, s, x, y, font, col, t, t0, dur=0.34, dy=None, align=0.0, tracking=0.0, a=1.0):
    """A word that slides up into place and fades in, from t0."""
    u = clamp((t - t0) / dur)
    if u <= 0:
        return None
    dy = font.size * 0.32 if dy is None else dy
    return T(c, s, x, y + dy * (1 - out_quart(u)), font, col, a * clamp(u * 2.6), align, tracking)


def pop(t, t0, dur=0.3, s=1.8):
    """A scale that pops from 0 to 1 with a little overshoot, from t0."""
    u = clamp((t - t0) / dur)
    return 0.0 if u <= 0 else (out_back(u, s) if u < 1 else 1.0)


def typed(s, t, t0, cps=28.0):
    """The part of s typed by time t."""
    n = int(max(0.0, t - t0) * cps)
    return s[:n]


def hud(c, t, n, name, dark=False, a=1.0):
    """The film's corner comments: the scene on the left, the maker and the timecode (60 fps) on the right."""
    col, al = (WHITE, 0.42) if dark else (INK, 0.45)
    f = mono(21)
    T(c, f"// {n:02d} — {name}", 48, 58, f, col, al * a)
    fr = int(t * 60 + 1e-6)
    tc = f"00:00:{fr // 60:02d}:{fr % 60:02d}"
    T(c, tc, 1872, 58, f, col, al * a, align=1.0)
    T(c, "VEEE", 1872 - f.width(tc) - 24, 58, f, col, al * a, align=1.0)


def check_path(x, y, s):
    """A check mark centred on (x, y), s wide."""
    p = skia.Path()
    p.moveTo(x - 0.36 * s, y + 0.02 * s)
    p.lineTo(x - 0.1 * s, y + 0.27 * s)
    p.lineTo(x + 0.38 * s, y - 0.24 * s)
    return p


def check(c, x, y, s, col, u=1.0, stroke=None):
    """Draw a check mark, drawn on as u goes 0 -> 1."""
    if u <= 0:
        return
    p = G.P(col, 1, stroke=stroke or 0.14 * s, cap="round", join="round")
    if u < 1:
        eff = G.trim(0, out_cubic(u))
        if eff is None:                          # skia hands back nothing for a trim too short to draw
            return
        p.setPathEffect(eff)
    c.drawPath(check_path(x, y, s), p)


def play_icon(c, x, y, s, col, a=1.0):
    """A small play triangle centred on (x, y)."""
    p = skia.Path()
    p.moveTo(x - 0.38 * s, y - 0.5 * s)
    p.lineTo(x + 0.5 * s, y)
    p.lineTo(x - 0.38 * s, y + 0.5 * s)
    p.close()
    c.drawPath(p, G.P(col, a, join="round"))
