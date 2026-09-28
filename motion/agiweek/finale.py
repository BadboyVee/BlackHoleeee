"""THE RACE TO AGI, bars 13-18: DevDay up next, the flag, P1, the end.

DevDay is the next session, tomorrow: the anticipation gauge climbs and the shift lights fill through the build
until the whole row flashes blue. The drop is a chequered flag asking AGI?. Anthropic crosses the line and takes P1,
staying on top, with the pit board reading IPO: NOV. Big week ahead."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_expo, hash01
from . import broadcast as B
from .look import blob
from .score import (G as GRID, T_DEV, T_BUILD, T_LEDS, T_SHIFT, T_FLAG, T_P1, T_BOARD, T_BOARD_ROWS, T_IPO,
                    T_ON_TOP, T_END)

TEAM_ROW = ["anthropic", "openai", "google", "meta", "xai"]


# ---------------------------------------------------------------- up next: DevDay

def leds(t):
    """How many shift lights are on: one each sixteenth through the build."""
    n = 0.0
    for tl in T_LEDS:
        if t >= tl:
            n += min(1.0, (t - tl) / 0.03)
    return n


def anticipation(t):
    v = 0.52 * out_cubic(clamp((t - (T_DEV + 0.3)) / 1.3))
    if t >= T_BUILD:
        v = 0.52 + 0.48 * leds(t) / 15.0
    return clamp(v)


def night_floor(c, t, dist, horizon=660.0, col="#2f7bff", a=0.4):
    """A dark floor in perspective with lines rushing at the camera."""
    fh = 700.0
    for k in range(-14, 15):
        c.drawLine(960 + k * 22, horizon, 960 + k * 300, 1080, G.P(col, a * 0.45, stroke=1.5))
    base = dist % 1.0
    for j in range(40):
        z = j + 1.0 - base
        y = horizon + fh / z
        if y > 1080 or z <= 0:
            continue
        c.drawLine(0, y, 1920, y, G.P(col, a * min(1.0, 3.0 / z), stroke=1.2 + 2.0 / z))
    c.drawRect(skia.Rect.MakeLTRB(0, horizon - 1, 1920, horizon + 70), G.P("#05060c", 1, shader=G.linear_grad(
        0, horizon, 0, horizon + 70, ["#05060c", "#05060c"], alphas=[1.0, 0.0])))


def devday(c, t):
    build = clamp((t - T_BUILD) / (T_SHIFT - T_BUILD))
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#04050b", 1, shader=G.linear_grad(0, 0, 0, 1080, [
        "#03040a", "#0b1024"])))
    blob(c, 1450, 560, 700, B.BLUE_LED, 0.16 + 0.3 * build)
    k = t - T_DEV
    night_floor(c, t, 2.0 * k + 9.0 * build * build, a=0.35 + 0.3 * build)
    flash = 1.0 if t >= T_SHIFT else 0.0
    B.shift_lights(c, 960, 208, leds(t), t, flash, a=clamp((k + 0.3) / 0.3))
    B.tab(c, 110, 338, "UP NEXT", B.cond(36, 820), B.RED, B.WHITE, t, T_DEV - 0.3, tracking=0.14)
    u = clamp((t - (T_DEV - 0.24)) / 0.3)
    if u > 0:
        B.mark(c, "openai", 350, 338, 58, col=B.WHITE, a=u)
    f = B.wide(142)
    B.slam(c, "OPENAI", 110, 492, f, B.WHITE, t, T_DEV - 0.28, dist=1300)
    B.slam(c, "DEVDAY", 110, 634, f, B.WHITE, t, T_DEV - 0.16, dist=1300)
    B.slide(c, "TOMORROW  ·  TUE 29 SEP", 116, 716, B.cond(48, 780), B.WHITE, t, T_DEV + 0.15, tracking=0.08)
    B.slide(c, "MORE ANNOUNCEMENTS & RELEASES?", 116, 772, B.cond(36, 660), B.GREY, t, T_DEV + 0.3,
            tracking=0.08)
    v = anticipation(t)
    ga = clamp((k + 0.3) / 0.4)
    value = "MAX" if t >= T_SHIFT - 0.02 else f"{int(round(v * 100))}%"
    with G.xf(c, 1450, 548, s=0.9 + 0.1 * out_cubic(ga)):
        B.gauge(c, 0, 0, 236, v, t, "ANTICIPATION", a=ga, value=value)
    B.slide(c, "THE MOST ANTICIPATED EVENT THIS WEEK", 1450, 930, B.cond(30, 720), B.WHITE, t, T_DEV + 0.5,
            align=0.5, tracking=0.12)


# ---------------------------------------------------------------- the drop: AGI?

def flag(c, t):
    k = max(0.0, t - T_FLAG)
    B.chequered(c, t, 960, 560, 2500, 1500, rot=-5.0, wind=1.0 + 0.5 * math.exp(-k / 0.4))
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#000000", 1, shader=G.radial_grad(960, 560, 1100, [
        "#000000", "#000000"], alphas=[0.0, 0.45])))
    f = B.wide(270)
    tw = f.width("AGI?")
    h, w = 330.0, tw + 190
    y0 = 395.0
    x0 = 960 - (w + h * B.SLANT) / 2
    e = out_expo(clamp(k / 0.36))
    B.slab(c, x0 + 18, y0 + 24, w, h, "#000000", 0.4 * e)
    p = B.slab(c, x0, y0, w, h, B.RED, 1.0, r=e)
    if p is not None:
        c.save()
        c.clipPath(p, skia.ClipOp.kIntersect, True)
        s = lerp(1.4, 1.0, out_expo(clamp(k / 0.5)))
        with G.xf(c, 960, y0 + h / 2, s=s):
            B.T(c, "AGI?", h * B.SLANT * 0.5 - 6, f.cap / 2, f, B.WHITE, align=0.5)
        c.restore()
    kf = k / 0.3
    if 0 <= kf < 1:
        B.slab(c, x0, y0, w, h, B.WHITE, 0.8 * (1 - kf) ** 2, r=e)


# ---------------------------------------------------------------- P1

def tape(c, t, t0, n=46, cols=(B.IVORY, B.INK, "#ffffff")):
    """Ticker tape falling through the frame."""
    k = t - t0
    if k <= 0:
        return
    for i in range(n):
        h1, h2, h3 = float(hash01(i, 1)), float(hash01(i, 2)), float(hash01(i, 3))
        x = h1 * 1960 - 20 + 40 * math.sin(k * (1.5 + h2) + i)
        y = -60 - h2 * 700 + k * (320 + 260 * h3)
        if y > 1120:
            continue
        rot = (k * (140 + 200 * h3) + 360 * h1) % 360
        flip = math.cos(k * (5 + 4 * h2) + i)
        with G.xf(c, x, y, rot=rot, sx=flip):
            c.drawRect(skia.Rect.MakeXYWH(-7, -16, 14, 32), G.P(cols[i % len(cols)], 0.9))


def p1(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P(B.CLAY, 1, shader=G.linear_grad(0, 0, 900, 1080, [
        "#e6865f", "#d97757", "#bd5a39"])))
    blob(c, 480, 560, 900, "#f6a888", 0.3)
    B.pinstripes(c, t, B.IVORY, 0.1, gap=40)
    u = clamp((t - (T_P1 + 0.12)) / 0.3)
    if u > 0:
        B.mark(c, "anthropic", 150 - 30 * (1 - out_cubic(u)), 300, 74, col=B.IVORY, a=u)
    B.slide(c, "ANTHROPIC", 214, 330, B.wide(80), B.IVORY, t, T_P1 + 0.16)
    B.slam(c, "P1", 96, 722, B.wide(430, 880), B.IVORY, t, T_P1 - 0.03, dur=0.6, dist=1400,
           shadow=("#7a2e16", 0.35, 16))
    B.slam(c, "STAYING ON TOP.", 110, 868, B.wide(78), B.INK, t, T_ON_TOP - 0.06, dist=1400)
    B.slide(c, "IPO PLANNED FOR NOVEMBER", 116, 946, B.cond(46, 780), B.IVORY, t, T_IPO, tracking=0.1)
    rows = [(T_BOARD_ROWS[0], "ANT", B.WHITE), (T_BOARD_ROWS[1], "P1", B.YELLOW),
            (T_BOARD_ROWS[2], "IPO", B.WHITE), (T_BOARD_ROWS[3], "NOV", B.YELLOW)]
    B.pit_board(c, 1370, 176, rows, t, T_BOARD, sway=1.1 * math.sin(t * 2.2))
    tape(c, t, T_P1 + 0.1)


# ---------------------------------------------------------------- the end

def end(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P(B.RED, 1, shader=G.linear_grad(0, 0, 1200, 1080, [
        "#ff2a36", "#e8101e", "#a8000d"])))
    blob(c, 960, 520, 1000, "#ff7a6a", 0.25)
    B.pinstripes(c, t, B.WHITE, 0.07, gap=40)
    B.kerb(c, 0, 1920, 0, 26, [B.WHITE, "#8e000a"], block=80, offset=-t * 420)
    B.kerb(c, 0, 1920, 1054, 26, [B.WHITE, "#8e000a"], block=80, offset=t * 420)
    f = B.wide(196)
    B.slam(c, "BIG WEEK", 960, 470, f, B.WHITE, t, T_END - 0.04, align=0.5, dist=1600, shadow=("#5a0006", 0.4, 12))
    B.slam(c, "AHEAD.", 960, 682, f, B.WHITE, t, T_END + GRID.spb - 0.04, align=0.5, dist=-1600,
           shadow=("#5a0006", 0.4, 12))
    for i, team in enumerate(TEAM_ROW):
        x = 960 + (i - 2) * 190
        u = clamp((t - (T_END + 0.62 + 0.07 * i)) / 0.3)
        if u <= 0:
            continue
        B.mark(c, team, x, 842 + 20 * (1 - out_cubic(u)), 56, col=B.WHITE, a=u)
        B.T(c, B.TEAMS[team]["code"], x, 910, B.cond(26, 760), B.WHITE, u * 0.85, align=0.5, tracking=0.16)
    B.tab(c, 960, 990, "NEXT: OPENAI DEVDAY  ·  TOMORROW", B.cond(32, 780), B.INK, B.WHITE, t, T_END + 1.05,
          align=0.5, tracking=0.1)
