"""HORIZON 1, the opening. On white a pen draws a flourish that runs off into a line and leaves "The frontier moves
every week." behind it; black bands sweep over "See it before it ships."; on black, Introducing, bars that rise
into a grid of tiles, the mark and its name, "Your AI-race intelligence, for founders and builders." zooming out of
its first word, a chart of the frontier, and a curve that sweeps up and out."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_quart, in_out_cubic, in_cubic, smoothstep, hash01
from .look import WHITE, INK, GREY, VIOLET, sans, mono, T, blur_in, blur_out, words_line
from . import marks
from .score import (T_STROKE, T_WORDS, T_BANDS, T_INTRO, T_BARS, T_GRID, T_TAG, T_TAG_SET, T_CHART, T_CURVE,
                    T_LAPTOP)

# ---------------------------------------------------------------- 1 the pen, on white

PEN = skia.Path()
PEN.moveTo(-150, 860)
PEN.cubicTo(150, 660, 250, 300, 520, 320)
PEN.cubicTo(780, 340, 730, 640, 560, 612)
PEN.cubicTo(410, 590, 460, 420, 630, 460)
PEN.cubicTo(780, 500, 820, 566, 1020, 566)
PEN.lineTo(2300, 566)
_M = skia.PathMeasure(PEN, False)
PEN_LEN = _M.getLength()


def pen_tip(e):
    pos, _ = _M.getPosTan(PEN_LEN * min(max(e, 0.0), 1.0))
    return pos.x(), pos.y()


def pen(c, t):
    a, b = T_STROKE
    u = clamp((t - a) / (b - a))
    if u <= 0:
        return
    head = in_out_cubic(u) * 0.92 + 0.08 * u
    tail = clamp((t - 1.55) / 0.95)
    tail = in_cubic(tail) * 1.02
    k = smoothstep(0.9, 2.3, t)                               # the camera pulls back as the line runs out
    z = lerp(2.7, 1.0, out_cubic(k))
    tx, ty = pen_tip(head)
    cx, cy = lerp(tx, 960, out_cubic(k)), lerp(ty, 566, out_cubic(k))
    width = lerp(9.0, 3.0, k)
    col = G.mixc(INK, "#bdbdbd", k)
    if tail >= head:
        return
    with G.xf(c, 960, 540, s=z):
        c.translate(-cx, -cy)
        p = G.P(col, 1, stroke=width, cap="round", join="round")
        eff = G.trim(min(tail, head), head)
        if eff is None:
            return
        p.setPathEffect(eff)
        c.drawPath(PEN, p)


def line1(c, t):
    f = sans(46, 300)
    words_line(c, t, [("The", None, None), ("frontier", None, None), ("moves", None, None),
                      ("every", None, None), ("week.", None, None)], 960, 556, f, "#161616", times=T_WORDS,
               dur=0.42, blur=10.0)


# ---------------------------------------------------------------- the bands

def bands(c, t):
    """Four black bands with slanted ends slide in from the right, one after another, until they cover it all."""
    h = 300.0
    slant = 180.0
    for i in range(4):
        u = clamp((t - (T_BANDS + 0.09 * i)) / 0.62)
        if u <= 0:
            continue
        e = out_quart(u)
        y0 = -60 + i * (h - 20)
        x0 = lerp(2300 + i * 120, -400, e)
        p = skia.Path()
        p.moveTo(x0 + slant, y0)
        p.lineTo(x0 + 3200, y0)
        p.lineTo(x0 + 3200 - slant, y0 + h)
        p.lineTo(x0, y0 + h)
        p.close()
        c.drawPath(p, G.P(INK))


def line2(c, t):
    """See it before it ships.: ink on the white, white on the black, as the bands go over it."""
    f = sans(46, 300)
    with G.layer(c, 1.0, blend=G.DIFF):
        words_line(c, t, [("See", None, None), ("it", None, None), ("before", None, None), ("it", None, None),
                          ("ships.", sans(46, 300), None)], 960, 556, f, WHITE,
                   times=[T_BANDS - 0.02 + 0.05 * i for i in range(5)], dur=0.3, blur=6.0)


def white(c, t):
    """0 to 4.57 s, on white."""
    if t < T_BANDS - 0.1:
        pen(c, t)
        line1(c, t)
    else:
        bands(c, t)
        line2(c, t)


# ---------------------------------------------------------------- 2 Introducing, the grid, the mark

def introducing(c, t):
    a, b = blur_out(t, T_BARS + 0.05, 0.4)
    if a <= 0:
        return
    with G.layer(c, a, blur=b):
        blur_in(c, "Introducing", 960, 578, sans(112, 300), WHITE, t, T_INTRO + 0.02, dur=0.55, align=0.5,
                blur=22.0, tracking=-0.01)


def bars(c, t):
    u = clamp((t - T_BARS) / 0.55)
    if u <= 0:
        return
    fade = 1 - clamp((t - (T_GRID + 0.1)) / 0.4)
    if fade <= 0:
        return
    hs = [0.18, 0.3, 0.46, 0.62, 0.46, 0.3, 0.18]
    for i, hh in enumerate(hs):
        v = out_cubic(clamp((t - (T_BARS + 0.04 * abs(i - 3))) / 0.5))
        x = 960 + (i - 3) * 114 - 55
        top = 1080 - 1080 * hh * v
        c.drawRect(skia.Rect.MakeLTRB(x, top, x + 110, 1080), G.P("#161618", fade, shader=G.linear_grad(
            0, top, 0, 1080, ["#1d1d20", "#0b0b0c"])))


TILE = 108.0


def grid(c, t, a=1.0):
    """The tiles: they come up in a scatter, and a few keep brightening and fading."""
    if a <= 0:
        return
    cols, rows = 18, 10
    ox, oy = (1920 - cols * TILE) / 2, (1080 - rows * TILE) / 2
    for j in range(rows):
        for i in range(cols):
            n = j * cols + i
            u = clamp((t - (T_GRID - 0.1 + 0.5 * hash01(n, 11))) / 0.3)
            if u <= 0:
                continue
            base = 0.035 + 0.035 * hash01(n, 12)
            pulse = 0.05 * max(0.0, math.sin(2 * math.pi * (0.35 * t + hash01(n, 13)))) ** 6
            g = base + pulse
            c.drawRect(skia.Rect.MakeXYWH(ox + i * TILE + 1, oy + j * TILE + 1, TILE - 2, TILE - 2),
                       G.P((g, g, g * 1.08), u * a))


def logo(c, t):
    out = clamp((t - (T_TAG - 0.12)) / 0.2)
    if out >= 1:
        return
    with G.layer(c, 1 - out, blur=10 * out):
        marks.lockup(c, 960, 578, 86, t=t, t0=T_GRID + 0.12)


# ---------------------------------------------------------------- Your AI-race intelligence

TAG1 = "Your AI-race intelligence"
TAG2 = "for founders and builders"
F_TAG = sans(60, 300)


def tagline(c, t):
    u = clamp((t - T_TAG) / (T_TAG_SET - T_TAG))
    if u <= 0:
        return
    out = clamp((t - (T_CHART - 0.15)) / 0.25)
    if out >= 1:
        return
    e = out_quart(u)
    w1 = F_TAG.width(TAG1)
    x0 = 960 - w1 / 2
    anchor = (x0 + F_TAG.width("Yo"), 520)                    # the zoom starts deep inside "Your"
    z = lerp(9.0, 1.0, e)
    col = G.mixc("#9a9a9a", WHITE, e)
    with G.layer(c, (1 - out) * clamp(u * 4), blur=10 * out):
        with G.xf(c, 960, 540, s=z):
            c.translate(-lerp(anchor[0], 960, e), -lerp(anchor[1], 540, e))
            T(c, TAG1, x0, 548, F_TAG, col)
        blur_in(c, TAG2, 960, 628, F_TAG, WHITE, t, T_TAG_SET - 0.1, dur=0.45, align=0.5)


# ---------------------------------------------------------------- the chart and the curve

CHART = [(0.00, 0.12), (0.08, 0.20), (0.16, 0.16), (0.25, 0.31), (0.33, 0.27), (0.42, 0.42), (0.50, 0.37),
         (0.58, 0.52), (0.67, 0.49), (0.75, 0.66), (0.83, 0.60), (0.92, 0.80), (1.00, 0.76)]
LABELS = {3: "CHAT", 5: "CODE", 7: "AGENTS", 9: "COMPUTER USE", 11: "ROBOTS?"}
CH = (560.0, 380.0, 800.0, 360.0)                            # x, y, w, h


def chart(c, t):
    u = clamp((t - T_CHART) / 0.95)
    if u <= 0:
        return
    out = clamp((t - (T_CURVE + 0.25)) / 0.3)
    if out >= 1:
        return
    x, y, w, h = CH
    a = 1 - out
    c.drawLine(x, y, x, y + h, G.P(GREY, 0.8 * a * clamp(u * 5), stroke=1.4))
    c.drawLine(x, y + h, x + w * clamp(u * 3), y + h, G.P(GREY, 0.8 * a, stroke=1.4))
    p = skia.Path()
    pts = [(x + px * w, y + h - py * h) for px, py in CHART]
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    e = out_cubic(u)
    pp = G.P(WHITE, a, stroke=2.2, join="round")
    eff = G.trim(0, e)
    if eff is not None:
        pp.setPathEffect(eff)
        c.drawPath(p, pp)
    m = skia.PathMeasure(p, False)
    pos, _ = m.getPosTan(m.getLength() * e)
    c.drawCircle(pos.x(), pos.y(), 9, G.P(VIOLET, 0.4 * a, blur=8))
    c.drawCircle(pos.x(), pos.y(), 3.5, G.P(WHITE, a))
    f = mono(14, 500)
    for i, name in LABELS.items():
        if e * (len(CHART) - 1) >= i:
            k = clamp((e * (len(CHART) - 1) - i) / 0.6)
            px, py = pts[i]
            T(c, name, px, py - 16 - 8 * (1 - k), f, GREY, a * k, align=0.5, tracking=0.08)


CURVE = skia.Path()
CURVE.moveTo(-120, 1180)
CURVE.cubicTo(700, 1100, 1250, 780, 1500, 320)
CURVE.cubicTo(1600, 130, 1680, -40, 1720, -160)


def curve(c, t):
    u = clamp((t - T_CURVE) / 0.55)
    if u <= 0:
        return
    e = out_cubic(u)
    z = lerp(1.0, 1.35, in_cubic(clamp((t - T_CURVE - 0.3) / (T_LAPTOP - T_CURVE - 0.3))))
    with G.xf(c, 960, 540, s=z):
        c.translate(-960, -540)
        for wdt, al, bl in [(26, 0.18, 18), (8, 0.5, 4), (3.2, 1.0, 0)]:
            p = G.P(WHITE if bl == 0 else VIOLET, al, stroke=wdt, cap="round", blur=bl)
            eff = G.trim(0, e)
            if eff is not None:
                p.setPathEffect(eff)
                c.drawPath(CURVE, p)


def black(c, t):
    """4.57 to 13.14 s, on black."""
    if t < T_GRID + 0.6:
        introducing(c, t)
        bars(c, t)
    if t >= T_GRID - 0.1:
        g = 1 - clamp((t - (T_CHART - 0.2)) / 0.4)
        grid(c, t, g * (0.55 if t >= T_TAG else 1.0))
    if T_GRID <= t < T_TAG + 0.1:
        logo(c, t)
    if T_TAG <= t < T_CHART + 0.1:
        tagline(c, t)
    if t >= T_CHART:
        chart(c, t)
        curve(c, t)
