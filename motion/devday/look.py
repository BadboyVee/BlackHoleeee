"""DevDay 2026 look: the teaser's own. Black ground (white for the opening), six flat colours for the faces, type
set in Geist with Geist Mono for the labels, and the accents the teaser builds its type from: orange points for the
first lines, blue for the lockup."""
from functools import lru_cache

import skia

from engine import gfx as G
from engine.core import clamp, out_back

BLACK = "#000000"
WHITE = "#ffffff"
GREY = "#dfdfdf"
PURPLE = "#8c3aef"
ORANGE = "#f26a20"
GREEN = "#11d04e"
DARK = "#262626"
BLUE = "#096bf7"
DIM = "#8a8a8a"
FAINT = "#5c5c5c"

FACES = [PURPLE, ORANGE, GREY, GREEN, DARK, BLUE]

# a few colours of the launches' own
GOLD = "#ffc21a"
RED = "#ea3b2e"
G_BLUE, G_RED, G_YELLOW, G_GREEN = "#4285f4", "#ea4335", "#fbbc05", "#34a853"
BUN = "#e9a04e"
PATTY = "#5b2e12"
SKY = "#6aa8ff"


SANS = "geist"                 # Geist for everything set in type, Geist Mono for the labels
MONO = "geist-mono"
TEXT = (("wght", 500),)
DISPLAY = (("wght", 600),)


@lru_cache(maxsize=None)
def F(fam, size, **axes):
    return G.Font(fam, size, **axes)


def gs(size, w=500):
    return F(SANS, size, wght=w)


def gsm(size):
    return F(SANS, size, wght=640)


def mono(size, w=480):
    return F(MONO, size, wght=w)


def T(c, s, x, y, font, col, a=1.0, align=0.0, tracking=0.0):
    if a <= 0 or not s:
        return None
    return G.text(c, s, x, y, font, G.P(col, a), align=align, tracking=tracking)


def rr(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def pop(t, t0, dur=0.28, s=2.2):
    """0 before t0, then an overshooting rise to 1."""
    u = clamp((t - t0) / dur)
    return 0.0 if u <= 0 else (1.0 if u >= 1 else out_back(u, s))


def hit(t, t0, decay=0.12):
    """A spike on t0 that dies away."""
    if t < t0:
        return 0.0
    import math
    return math.exp(-(t - t0) / decay)
