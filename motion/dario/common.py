"""Palette and shared pieces for the Dario Amodei tribute."""
import math
from bisect import bisect_right

import skia

from engine import gfx as G
from engine.core import clamp, lerp, snap, out_cubic, W, H, CX, CY
from .score import KICKS

INK = "#141413"
PAPER = "#f0eee6"
PAGE = "#fbfaf6"
CLAY = "#d97757"
KRAFT = "#d4a27f"
DIM = "#8a877f"


def kick_env(t, decay=0.09):
    i = bisect_right(KICKS, t) - 1
    return math.exp(-(t - KICKS[i]) / decay) if i >= 0 else 0.0


def fill(c, color, a=1.0):
    c.drawRect(skia.Rect.MakeWH(W, H), G.P(color, a))


def blur_in(c, run, x, y, color, t, t0, stagger=0.03, dur=0.4, rise=34, blur=12, alpha=1.0, starts=None):
    """After Effects' classic per-character reveal: each glyph fades up from a blur."""
    for i, gid, gx, adv in run.glyphs():
        ti = starts[i] if starts else t0 + i * stagger
        u = clamp((t - ti) / dur)
        if u <= 0:
            continue
        e = snap(u)
        a = alpha * min(1.0, u * 1.6)
        sigma = blur * (1 - e)
        px, py = x + gx, y + rise * (1 - e)
        if sigma > 0.4:
            with G.layer(c, blur=sigma):
                G.glyph(c, run.font, gid, px, py, G.P(color, a))
        else:
            G.glyph(c, run.font, gid, px, py, G.P(color, a))


def chapter(c, t, t0, num, name, ink, acc):
    """Chapter marker under the HUD: an italic numeral, a rule that sweeps in, and the name."""
    u = clamp((t - t0) / 0.5)
    if u <= 0:
        return
    f_num = G.Font("fraunces-italic", 64, wght=400, opsz=144, SOFT=100)
    run = f_num.shape(num)
    blur_in(c, run, 88, 214, acc, t, t0, stagger=0.05, dur=0.35, rise=20, blur=8)
    w = 180 * snap(clamp((t - t0 - 0.05) / 0.45))
    c.drawLine(88 + run.width + 22, 194, 88 + run.width + 22 + w, 194, G.P(ink, 0.6, stroke=1.5))
    fm = G.Font("mono", 17, wght=700)
    G.text(c, G.scramble(name, clamp((t - t0 - 0.1) / 0.35), len(name), t), 88 + run.width + 22, 222, fm, G.P(ink, 0.9),
           tracking=0.3)


def spike_wave(dt):
    """Extracellular spike, in pixels: a sharp dip and a slower overshoot."""
    return -1.0 * math.exp(-((dt - 0.0015) / 0.0011) ** 2) + 0.38 * math.exp(-((dt - 0.0055) / 0.0028) ** 2)
