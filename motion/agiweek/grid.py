"""THE RACE TO AGI, bars 1-4: the start-light gantry and the title.

Five labs hang on the gantry, a column of lights each, the model above the company. The lights come on one a beat,
hold, and go out on the drop; the camera drives under the gantry onto a night straight where ANOTHER WEEK /
CLOSER TO AGI. arrives at speed, and the lap counter, which is the week of the year, ticks from 39 to 40."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_expo, out_back
from . import broadcast as B
from . import motion as V
from .look import blob
from .score import (LIGHT_ORDER, T_LIGHTS, T_CAPTION, T_STACKED, T_OUT, T_LINE1, T_LINE2, T_AGI_BOX, T_LAP, T_FLIP,
                    T_BUG)

PODS = [960 + (i - 2) * 300 for i in range(5)]
POD_TOP, POD_W, POD_H = 172, 214, 336
LAMP_Y = (262, 422)
HORIZON = 720
LIGHTS_OFF = 0.1            # the lights go out a breath before the drop: six frames of dark, then go
MODELS = {"meta": ["MUSE"], "google": ["GEMINI"], "xai": ["GROK 4.8"], "openai": ["NEW MODEL", "+ AGENT “O”"],
          "anthropic": ["SONNET 5.5"]}


def level(t, i):
    """How lit column i is: an LED snaps on with a small overshoot; at lights out everything dies at once."""
    t0 = T_LIGHTS[i]
    if t < t0:
        return 0.0
    if t >= T_OUT - LIGHTS_OFF:
        return max(0.0, 1.0 - (t - (T_OUT - LIGHTS_OFF)) / 0.03) * 0.5
    k = t - t0
    return min(1.0, k / 0.018) * (1.0 + 0.4 * math.exp(-k / 0.07))


def lit(t):
    return sum(min(1.0, level(t, i)) for i in range(5))


def gantry(c, t):
    gantry_ground(c, t)
    gantry_rig(c, t)


def gantry_ground(c, t):
    n = lit(t)
    # the night, warming red as the lights come on
    c.drawRect(skia.Rect.MakeLTRB(0, 0, 1920, HORIZON + 4), G.P("#040407", shader=G.linear_grad(
        0, 0, 0, HORIZON, ["#030305", "#0b0910"])))
    blob(c, 960, 360, 1150, B.LAMP, 0.045 * n)
    # the grid, wet, under the gantry
    B.track(c, t, 6.0, horizon=HORIZON, hc=1.3, half=6.0, f=1000.0, sky=None, lights=False, grid_boxes=True,
            lines_every=8.0, asphalt=("#141419", "#0b0b0f"))
    for i, x in enumerate(PODS):
        k = min(1.0, level(t, i))
        if k > 0:
            sh = G.linear_grad(0, HORIZON + 10, 0, 1080, [B.LAMP, B.LAMP], alphas=[0.34 * k, 0.0])
            c.drawRect(skia.Rect.MakeLTRB(x - 46, HORIZON + 10, x + 46, 1080), G.P(B.LAMP, 1, shader=sh, blur=18,
                                                                                   blend=G.ADD))
    # haze drifting through the red
    for j in range(5):
        hx = (j * 470 + t * (30 + 12 * j)) % 2400 - 240
        blob(c, hx, 640 + 40 * math.sin(j * 1.7), 380, "#ff3a2a", 0.022 * n)


def gantry_rig(c, t, labels=True):
    # the rig: a truss across the top, two legs, five pods hanging from it
    c.drawRect(skia.Rect.MakeLTRB(0, 112, 1920, 172), G.P("#131318"))
    c.drawRect(skia.Rect.MakeLTRB(0, 112, 1920, 116), G.P("#3b3b46"))
    lattice = G.P("#24242d", 1, stroke=3)
    for k in range(38):
        x = k * 52
        c.drawLine(x, 120, x + 26, 166, lattice)
        c.drawLine(x + 26, 166, x + 52, 120, lattice)
    for x in (110, 1810):
        c.drawRect(skia.Rect.MakeLTRB(x - 20, 0, x + 20, 172), G.P("#131318"))
        c.drawRect(skia.Rect.MakeLTRB(x - 20, 0, x - 16, 172), G.P("#34343e"))
    for i, x in enumerate(PODS):
        k = level(t, i)
        c.drawRRect(B.rr(x - POD_W / 2 + 8, POD_TOP + 14, POD_W, POD_H, 26), G.P("#000000", 0.5, blur=14))
        c.drawRRect(B.rr(x - POD_W / 2, POD_TOP, POD_W, POD_H, 26), G.P("#101014", 1, shader=G.linear_grad(
            x - POD_W / 2, 0, x + POD_W / 2, 0, ["#1d1d24", "#0c0c10", "#17171d"])))
        c.drawRRect(B.rr(x - POD_W / 2, POD_TOP, POD_W, POD_H, 26), G.P("#33333d", 1, stroke=2))
        for ly in LAMP_Y:
            B.lamp(c, x, ly, min(1.0, k))
            c.drawPath(G.arc_path(x, ly, B.LAMP_R + 17, 196, 148), G.P("#060608", 1, stroke=15, cap="round"))
    for i, x in enumerate(PODS):
        k = level(t, i)
        for ly in LAMP_Y:
            B.lamp_glow(c, x, ly, k)
    if not labels:
        return
    # under each column: the model on top, the company under it
    for i, team in enumerate(LIGHT_ORDER):
        t0 = T_LIGHTS[i]
        x = PODS[i]
        a = 1.0 if t < T_OUT else max(0.0, 1.0 - (t - T_OUT) / 0.2)
        fm = B.cond_i(46, 820)
        lines = MODELS[team]
        for j, s in enumerate(lines):
            y = 612 - (len(lines) - 1 - j) * 50
            B.slide(c, s, x, y, fm, B.WHITE, t, t0 + 0.03 * j, dur=0.34, align=0.5, a=a)
        fc = B.cond(24, 700)
        name = B.TEAMS[team]["company"]
        w = fc.width(name, 0.12) + 36
        u = clamp((t - t0 - 0.06) / 0.25)
        if u > 0:
            B.mark(c, team, x - w / 2 + 12, 652, 26, a=a * u)
        B.slide(c, name, x - w / 2 + 36, 661, fc, B.GREY, t, t0 + 0.08, dur=0.34, a=a, tracking=0.12)
    # the line underneath: the final week of September is looking stacked
    a = 1.0 if t < T_OUT else 0.0
    B.slide(c, "THE FINAL WEEK OF SEPTEMBER", 960, 892, B.cond(34, 700), B.WHITE, t, T_CAPTION, dur=0.5,
            align=0.5, tracking=0.28, a=0.85 * a)
    B.slide(c, "IS LOOKING STACKED.", 960, 1000, B.wide(76), B.WHITE, t, T_STACKED, dur=0.45, align=0.5, a=a)


def title_layout():
    f = B.wide(124)
    return f, 430.0, 590.0


def title(c, t):
    k = max(0.0, t - T_OUT)
    dist = 30 + 58 * k + 18 * k * k
    B.track(c, t, dist, horizon=452)
    V.speed_lines(c, 960, 452, 0.35 + 0.65 * math.exp(-k / 0.7), t, n=70)
    f, y1, y2 = title_layout()
    # after the lap counter lands, the title steps up and back
    m = out_expo(clamp((t - T_LAP) / 0.45))
    s = lerp(1.0, 0.72, m)
    dy = lerp(0.0, -170.0, m)
    shadow = ("#000000", 0.55, 10)
    with G.xf(c, 960, 510 + dy, s=s):
        c.translate(-960, -510)
        B.slam(c, "ANOTHER WEEK", 960, y1, f, B.WHITE, t, T_LINE1 + 0.02, dur=0.6, align=0.5, dist=1500,
               shadow=shadow)
        line = "CLOSER TO AGI."
        run = f.shape(line, -0.01)
        head = f.width("CLOSER TO ", -0.01)
        x0 = 960 - run.width / 2
        # AGI. gets a red box of its own, a beat later
        u = clamp((t - T_AGI_BOX) / 0.3)
        if u > 0:
            e = out_expo(u)
            bx, bw = x0 + head - 34, run.width - head + 64
            bh = f.cap * 1.62
            B.slab(c, bx, y2 - f.cap - (bh - f.cap) / 2, bw, bh, B.RED, 1.0, r=e)
            kf = (t - T_AGI_BOX) / 0.25
            if 0 <= kf < 1:
                B.slab(c, bx, y2 - f.cap - (bh - f.cap) / 2, bw, bh, B.WHITE, 0.7 * (1 - kf) ** 2, r=e)
        B.slam(c, line, 960, y2, f, B.WHITE, t, T_LINE2 + 0.02, dur=0.6, align=0.5, dist=-1500, shadow=shadow)
    # the lap: this race's laps are the weeks of the year
    if T_LAP <= t < T_BUG:
        u = clamp((t - T_LAP) / 0.4)
        B.lap_group(c, 960, 700, lerp(0.55, 0.9, out_back(u, 1.6)), t, T_FLIP, a=clamp(u * 3))
    B.tab(c, 960, 872, "WEEK 40  ·  SEP 28 – OCT 4", B.cond(30, 700), B.PANEL, B.WHITE, t, T_LAP + 0.22,
          align=0.5, tracking=0.16)
