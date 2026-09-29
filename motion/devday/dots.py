"""DevDay 2026: Dots, OpenAI's agent bot, a Muse Agent and Grokbot competitor. The user's sheet of its looks,
redrawn and brought to life: nine light tiles, each with its own eyes (round shades, sleepy lids, a monocle,
sparkles, round specs, shiny eyes, wayfarers, plain ovals, googly eyes), pop in across the grid on the groove and
keep moving; twice on the beat every tile flips to the next look. The 78's points fly in to build "Dots", and its
points fly on into the first launch."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, out_back, in_back, hash01
from .look import WHITE, DIM, ORANGE, MONO, DISPLAY
from .faces import SPARKLE
from .type import word, draw_word, Build
from .chain import Station, StartStation, draw_chain
from .world import W78, B78
from .score import T_BOT, T_LIST

TILE = 220.0
GAP = 26.0
GRID = (1358.0, 540.0)
TILE_TOP, TILE_BOTTOM = "#e6e7eb", "#d0d1d6"
INK = "#1c1c1e"
SHINE = "#f4f7f4"
T_FLIPS = (T_BOT + 2.0, T_BOT + 3.0)           # the second bar's downbeat, and its third beat
T_FOLD = T_LIST - 0.38


# ---------------------------------------------------------------- the nine looks, drawn round the tile's middle

def round_shades(c, S, k):
    for sx in (-1, 1):
        c.drawCircle(sx * 0.19 * S, 0, 0.135 * S, G.P(INK))
        c.drawOval(skia.Rect.MakeXYWH(sx * 0.19 * S - 0.085 * S, -0.09 * S, 0.07 * S, 0.045 * S), G.P(WHITE, 0.14))
    br = skia.Path()
    br.moveTo(-0.058 * S, -0.012 * S)
    br.cubicTo(-0.04 * S, -0.012 * S, -0.036 * S, -0.062 * S, 0, -0.062 * S)
    br.cubicTo(0.036 * S, -0.062 * S, 0.04 * S, -0.012 * S, 0.058 * S, -0.012 * S)
    c.drawPath(br, G.P(INK, 1, stroke=0.016 * S, cap="round"))
    g = ((k + 0.3) % 1.4) / 0.35                       # a glint crosses a lens now and then
    if 0 < g < 1:
        c.save()
        clip = skia.Path()
        clip.addCircle(-0.19 * S, 0, 0.135 * S)
        c.clipPath(clip, doAntiAlias=True)
        x = -0.19 * S + (g - 0.5) * 0.4 * S
        c.drawLine(x - 0.05 * S, 0.14 * S, x + 0.05 * S, -0.14 * S, G.P(WHITE, 0.55, stroke=0.035 * S))
        c.restore()


def sleepy(c, S, k):
    droop = 0.5 + 0.5 * math.sin(2 * math.pi * 0.8 * k)
    for sx in (-1, 1):
        x0 = sx * 0.2 * S
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0 + 0.012 * S - 0.037 * S, -0.035 * S, 0.074 * S,
                                                             (0.085 + 0.025 * droop) * S), 0.037 * S, 0.037 * S),
                    G.P(INK))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0 - 0.15 * S, -0.075 * S, 0.3 * S, 0.062 * S),
                                          0.031 * S, 0.031 * S), G.P(INK))


def monocle(c, S, k):
    with G.xf(c, -0.03 * S, -0.32 * S, rot=6 * math.sin(2 * math.pi * 0.9 * k)):
        c.translate(0.03 * S, 0.32 * S)
        c.drawCircle(-0.03 * S, -0.1 * S, 0.2 * S, G.P(INK, 1, stroke=0.03 * S))
        arc = skia.Path()
        arc.addArc(skia.Rect.MakeXYWH(-0.2 * S, -0.27 * S, 0.34 * S, 0.34 * S), 200, 50)
        c.drawPath(arc, G.P(WHITE, 0.25, stroke=0.01 * S, cap="round"))
        s = skia.Path()
        wob = 0.02 * S * math.sin(2 * math.pi * 1.3 * k)
        s.moveTo(0.13 * S, 0.035 * S)
        s.cubicTo(0.17 * S + wob, 0.16 * S, 0.2 * S - wob, 0.3 * S, 0.36 * S, 0.31 * S)
        c.drawPath(s, G.P(INK, 1, stroke=0.024 * S, cap="round"))


def sparkle(c, S, k):
    for sx in (-1, 1):
        x0 = sx * 0.18 * S
        c.drawOval(skia.Rect.MakeXYWH(x0 - 0.1 * S, -0.17 * S, 0.2 * S, 0.34 * S), G.P(INK))
        tw = 1 + 0.18 * math.sin(2 * math.pi * (2 * k + 0.25 * sx))
        with G.xf(c, x0 - 0.02 * S, -0.05 * S, s=0.13 * S * tw, rot=12 * math.sin(2 * math.pi * k)):
            c.drawPath(SPARKLE, G.P(WHITE))
        c.drawCircle(x0 + 0.05 * S, 0.075 * S, 0.022 * S, G.P(WHITE))


def specs(c, S, k):
    b = 0.012 * S * math.sin(2 * math.pi * 2 * k)
    p = G.P(INK, 1, stroke=0.022 * S, cap="round")
    for sx in (-1, 1):
        c.drawOval(skia.Rect.MakeXYWH(sx * 0.12 * S - 0.088 * S, b - 0.125 * S, 0.176 * S, 0.25 * S), p)
        c.drawLine(sx * 0.208 * S, b, sx * 0.25 * S, b, p)


def shiny(c, S, k):
    look = 0.025 * S * math.sin(2 * math.pi * 0.8 * k)
    for sx in (-1, 1):
        x0 = sx * 0.18 * S + look
        c.drawCircle(x0, 0, 0.125 * S, G.P(INK))
        c.drawCircle(x0 - 0.04 * S, -0.045 * S, 0.036 * S, G.P(SHINE))


def wayfarer(c, S, k):
    p = skia.Path()
    p.moveTo(-0.30 * S, -0.075 * S)
    p.lineTo(0.30 * S, -0.075 * S)
    p.lineTo(0.295 * S, -0.03 * S)
    p.cubicTo(0.29 * S, 0.05 * S, 0.22 * S, 0.095 * S, 0.14 * S, 0.085 * S)
    p.cubicTo(0.08 * S, 0.075 * S, 0.06 * S, 0.02 * S, 0.055 * S, -0.012 * S)
    p.lineTo(-0.055 * S, -0.012 * S)
    p.cubicTo(-0.06 * S, 0.02 * S, -0.08 * S, 0.075 * S, -0.14 * S, 0.085 * S)
    p.cubicTo(-0.22 * S, 0.095 * S, -0.29 * S, 0.05 * S, -0.295 * S, -0.03 * S)
    p.close()
    c.drawPath(p, G.P(INK))
    g = ((k + 0.9) % 1.5) / 0.4
    if 0 < g < 1:
        c.save()
        c.clipPath(p, doAntiAlias=True)
        x = (g - 0.5) * 0.8 * S
        c.drawLine(x - 0.05 * S, 0.12 * S, x + 0.05 * S, -0.12 * S, G.P(WHITE, 0.45, stroke=0.04 * S))
        c.restore()


def oval(c, S, k):
    ph = (k % 1.1) / 1.1
    blink = 1 - 0.9 * math.sin(math.pi * clamp((ph - 0.8) / 0.14)) if ph > 0.8 else 1.0
    for sx in (-1, 1):
        c.drawOval(skia.Rect.MakeXYWH(sx * 0.19 * S - 0.08 * S, -0.14 * S * blink, 0.16 * S, 0.28 * S * blink),
                   G.P(INK))


def googly(c, S, k):
    for sx in (-1, 1):
        x0 = sx * 0.18 * S
        c.drawCircle(x0, 0, 0.13 * S, G.P("#fbfbfb"))
        c.drawCircle(x0, 0, 0.13 * S, G.P("#c9cacf", 1, stroke=0.012 * S))
        dx = 0.035 * S * math.sin(2 * math.pi * 1.7 * k + sx)
        dy = 0.03 * S * math.cos(2 * math.pi * 2.3 * k + 0.5 * sx) + 0.015 * S
        c.drawCircle(x0 + dx - 0.01 * S, dy, 0.078 * S, G.P(INK))
        c.drawCircle(x0 + dx - 0.035 * S, dy - 0.025 * S, 0.024 * S, G.P(WHITE))


LOOKS = [round_shades, sleepy, monocle, sparkle, specs, shiny, wayfarer, oval, googly]


# ---------------------------------------------------------------- the tiles

def tile(c, x, y, S, look, k, sx=1.0, s=1.0):
    if s <= 0.01 or sx <= 0.01:
        return
    with G.xf(c, x, y, sx=s * sx, sy=s):
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-S / 2, -S / 2, S, S), 0.2 * S, 0.2 * S)
        c.drawRRect(r, G.P(TILE_TOP, 1, shader=G.linear_grad(0, -S / 2, 0, S / 2, [TILE_TOP, TILE_BOTTOM])))
        LOOKS[look % len(LOOKS)](c, S, k)


def tiles(c, t):
    for n in range(9):
        row, col = divmod(n, 3)
        x = GRID[0] + (col - 1) * (TILE + GAP)
        y = GRID[1] + (row - 1) * (TILE + GAP) + 4 * math.sin(2 * math.pi * (t - T_BOT) + hash01(n, 3) * 6)
        u = clamp((t - (T_BOT + 0.04 + 0.055 * n)) / 0.22)
        if u <= 0:
            continue
        s = out_back(u, 2.2) if u < 1 else 1.0
        fold = clamp((t - (T_FOLD + 0.025 * n)) / 0.2)
        if fold > 0:
            s *= 1 - in_back(fold, 2.0)
        look, sx = n, 1.0
        for j, tf in enumerate(T_FLIPS):                  # flip to the next look on the beat
            v = clamp((t - (tf + 0.025 * n)) / 0.18)
            if v >= 0.5:
                look = n + j + 1
            if 0 < v < 1:
                sx = abs(math.cos(math.pi * v))
        tile(c, x, y, TILE, look, t - T_BOT + 0.37 * n, sx=sx, s=s)


# ---------------------------------------------------------------- the words

LABEL = word((("OPENAI’S AGENT BOT", DIM),), 30, 150, 336, align=0.0, fam=MONO, axes=(("wght", 500),),
             tracking=0.14)
DOTS = word((("Dots", WHITE),), 300, 138, 640, align=0.0, axes=DISPLAY)
SUB = word((("A Muse Agent & Grokbot competitor", "#bdbdbd"),), 40, 150, 734, align=0.0)
B_LABEL = Build(T_BOT + 0.1, spread=0.3, outline=0.03, fill=0.1, dots_off=0.18, t_out=T_FOLD, vanish=0.14)
B_SUB = Build(T_BOT + 0.55, spread=0.35, outline=0.03, fill=0.1, dots_off=0.18, t_out=T_FOLD + 0.02, vanish=0.14)

_FROM_78 = StartStation(W78, B78, ORANGE)
DOTS_STATION = Station(T_BOT, DOTS, ORANGE, _FROM_78, lead=0.16, fly=0.3, fill_spread=0.25)
MINI = [_FROM_78, DOTS_STATION]
START = DOTS_STATION.T - DOTS_STATION.lead      # when the 78 starts handing its points over


def dots(c, t, with_word=True):
    tiles(c, t)
    draw_word(c, LABEL, t, B_LABEL, ORANGE)
    draw_word(c, SUB, t, B_SUB, ORANGE)
    if with_word:
        draw_chain(c, t, MINI)
