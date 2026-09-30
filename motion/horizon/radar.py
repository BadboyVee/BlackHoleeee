"""HORIZON 3, Radar. On white a black lens opens between two circles: RADAR, your early-warning engine. It opens
onto the hills, where birds cross and it watches, spots, alerts. On black its icon, Searching…, and a new launch
spotted, field by field. Then the sea at sunset, a phone held up to it: New launch spotted."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_quart, in_cubic, in_out_cubic
from .look import WHITE, INK, GREY, DIM, GREEN, BLUE, sans, T, rr, blur_in, blur_out
from . import plates, marks, devices, sky
from .score import (T_EYE, T_ENGINE, T_HILLS, T_VERBS, T_ICON, T_SEARCH, T_CARD, T_SUNSET)

# ---------------------------------------------------------------- the lens

def lens_path(hw, hh, cx=960.0, cy=540.0):
    """The lens between two circles: half-width hw, half-height hh."""
    r = (hw * hw + hh * hh) / (2 * hh)
    d = r - hh
    a = skia.Path()
    a.addCircle(cx, cy - d, r)
    b = skia.Path()
    b.addCircle(cx, cy + d, r)
    return skia.Op(a, b, skia.PathOp.kIntersect_PathOp), r, d


def eye(c, t):
    tau = t - T_EYE
    u1 = out_cubic(clamp(tau / 0.45))
    u2 = out_quart(clamp((t - T_ENGINE) / 0.45))
    u3 = in_cubic(clamp((t - (T_HILLS - 0.32)) / 0.32))
    hw = lerp(lerp(160, 430, u1), 700, u2) + 900 * u3
    hh = lerp(lerp(8, 118, u1), 150, u2) + 700 * u3
    p, r, d = lens_path(hw, hh)
    # the two circles it is cut from, drawn on as hairlines
    k = clamp(tau / 0.6)
    for sgn in (-1, 1):
        arc = skia.Path()
        arc.addCircle(960, 540 + sgn * d, r)
        pp = G.P("#c9ccd4", 1, stroke=1.4)
        eff = G.trim(0, k)
        if eff is not None:
            pp.setPathEffect(eff)
            c.drawPath(arc, pp)
    c.drawPath(p, G.P(INK))
    a1 = 1 - clamp((t - (T_ENGINE - 0.12)) / 0.15)
    if a1 > 0:
        with G.layer(c, a1 * clamp((tau - 0.18) / 0.25)):
            marks.icon(c, 858, 540, 58, glow=0.0)
            c.drawLine(906, 520, 906, 560, G.P(WHITE, 0.5, stroke=1.4))
            T(c, "RADAR", 928, 548, sans(22, 600), WHITE, tracking=0.32)
    if t >= T_ENGINE:
        blur_in(c, "Your early-warning engine", 960, 554, sans(44, 400), WHITE, t, T_ENGINE + 0.08, dur=0.45,
                align=0.5)


# ---------------------------------------------------------------- watches, spots, alerts

VERBS = ["Watches", "Spots", "Alerts"]
F_VERB = sans(66, 420)


def verbs(c, t):
    tau = t - T_HILLS
    plates.day(c, t, zoom=1.14 + 0.01 * tau, cx=0.5, cy=0.44, drift=-18 * tau)
    sky.birds(c, t, T_HILLS - 1.0, n=11, x0=1700, y0=250, vx=-190, vy=-14, size=13, col="#243024")
    y = 700.0                                                      # on the green, where white reads
    cur = -1
    for i, t0 in enumerate(T_VERBS):
        if t >= t0:
            cur = i
    for i, word in enumerate(VERBS):
        t0 = T_VERBS[i]
        if t < t0:
            continue
        go = sum(out_cubic(clamp((t - tj) / 0.45)) for tj in T_VERBS[i + 1:])   # one step left per newer word
        x = 960 - 470 * go
        a = 1 - 0.65 * min(go, 1.0) - 0.35 * clamp(go - 1.0)
        if a <= 0.01:
            continue
        with G.layer(c, a, blur=5 * min(go, 1.0)):
            c.save()
            c.translate(0, 3)
            with G.layer(c, 0.35, blur=10):
                T(c, word, x, y, F_VERB, "#0e2a0a", align=0.5)
            c.restore()
            blur_in(c, word, x, y, F_VERB, WHITE, t, t0, dur=0.4, align=0.5)
    if cur >= 0:                                                   # the bar slides under the current word
        u = out_cubic(clamp((t - T_VERBS[cur]) / 0.35))
        w = F_VERB.width(VERBS[cur]) * 0.62
        c.drawRRect(rr(960 - w / 2 * u, y + 34, w * u, 6, 3), G.P(WHITE, 0.95))
    u = out_quart(clamp((t - (T_ICON - 0.3)) / 0.3))
    if u > 0:
        marks.icon(c, lerp(2100, 1790, u), 540, 110)


# ---------------------------------------------------------------- the icon, searching, the card

def radar_icon(c, t):
    tau = t - T_ICON
    u = out_quart(clamp(tau / 0.55))
    a, b = blur_out(t, T_SEARCH - 0.3, 0.3)
    if a <= 0:
        return
    with G.layer(c, a, blur=b):
        x = lerp(1790, 960, u)
        s = lerp(110, 150, u)
        marks.icon(c, x, 500, s)
        blur_in(c, "RADAR", 960, 620, sans(19, 600), "#cfd2dc", t, T_ICON + 0.3, dur=0.4, align=0.5, tracking=0.34)


def searching(c, t):
    tau = t - T_SEARCH
    if tau < 0:
        return
    a, b = blur_out(t, T_CARD - 0.25, 0.25)
    if a <= 0:
        return
    f = sans(46, 300)
    w = f.width("Searching")
    with G.layer(c, a, blur=b):
        blur_in(c, "Searching", 960 - w / 2 - 20, 556, f, "#d9d9de", t, T_SEARCH, dur=0.4)
        for i in range(3):
            g = 0.25 + 0.75 * max(0.0, math.sin(2 * math.pi * (tau * 1.4 - i * 0.18))) ** 2
            c.drawCircle(960 + w / 2 - 6 + i * 16, 552, 4.2, G.P(WHITE, g * clamp(tau / 0.3)))


FIELDS = [("Model", "Sonnet 5.5", BLUE), ("Lab", "Anthropic", None), ("Status", "Rolling out", GREEN),
          ("Routing", "from Sonnet 5", None), ("Pricing", "unchanged", None), ("Free tier", "likely", None)]


def card(c, t):
    tau = t - T_CARD
    if tau < 0:
        return
    out = clamp((t - (T_SUNSET - 0.22)) / 0.22)
    push = in_out_cubic(clamp((tau - 1.0) / 2.2))
    z = lerp(1.0, 1.28, push)
    x, y, w, h = 560.0, 170.0, 800.0, 760.0
    with G.layer(c, (1 - out) * clamp(tau / 0.3), blur=12 * out):
        with G.xf(c, 960, 540, s=z):
            c.translate(-960, -540 + 120 * push)
            c.drawRRect(rr(x, y, w, h, 24), G.P("#0f0f12"))
            c.drawRRect(rr(x + 0.5, y + 0.5, w - 1, h - 1, 24), G.P("#26262c", 1, stroke=1.4))
            marks.icon(c, x + 72, y + 74, 64, glow=0.0)
            T(c, "Radar", x + 124, y + 70, sans(24, 600), WHITE)
            T(c, "Launch intelligence", x + 124, y + 98, sans(17, 400), GREY)
            c.drawLine(x + 40, y + 140, x + w - 40, y + 140, G.P("#26262c", 1, stroke=1.4))
            blur_in(c, "NEW LAUNCH SPOTTED", x + 40, y + 196, sans(18, 650), WHITE, t, T_CARD + 0.15, dur=0.3,
                    tracking=0.24)
            fy = y + 262
            f = sans(24, 400)
            for i, (k1, v1, col) in enumerate(FIELDS):
                t0 = T_CARD + 0.35 + 0.2 * i
                u = clamp((t - t0) / 0.25)
                if u <= 0:
                    break
                T(c, k1 + ":", x + 40, fy, f, GREY, u)
                T(c, v1, x + 40 + f.width(k1 + ": "), fy, f, col or "#ececf0", u)
                fy += 50 if i != 2 else 70
            t0 = T_CARD + 0.35 + 0.2 * len(FIELDS)
            u = clamp((t - t0) / 0.3)
            if u > 0:
                T(c, "Confidence:", x + 40, fy + 20, f, GREY, u)
                c.drawRRect(rr(x + 210, fy + 6, 360, 10, 5), G.P("#26262c", u))
                c.drawRRect(rr(x + 210, fy + 6, 360 * 0.82 * out_cubic(u), 10, 5), G.P(BLUE, u))
                T(c, f"{int(82 * out_cubic(u))}%", x + 596, fy + 20, f, WHITE, u)
                T(c, "Predictions, not news. Signals from 6 sources, just now.", x + 40, y + h - 40,
                  sans(15, 400), DIM, u)


def radar_black(c, t):
    radar_icon(c, t)
    searching(c, t)
    card(c, t)


# ---------------------------------------------------------------- the sea at sunset

def sunset(c, t):
    tau = t - T_SUNSET
    plates.dusk(c, t, zoom=1.08 + 0.03 * tau, cx=0.5, cy=0.5)
    w, h = 380.0, 780.0
    rise = 60 * (1 - out_cubic(clamp(tau / 0.5)))
    with G.xf(c, 1240 + w / 2, 560 + h / 2 + rise, rot=-7):
        def screen(cc, sx, sy, sw, sh):
            cc.drawRect(skia.Rect.MakeXYWH(sx, sy, sw, sh), G.P("#101014"))
            devices.status_bar(cc, sx, sy, sw)
            cc.drawRRect(rr(sx + 14, sy + 120, sw - 28, 96, 20), G.P("#2a2a31", 0.95))
            marks.icon(cc, sx + 50, sy + 168, 38, glow=0.0)
            T(cc, "Radar", sx + 80, sy + 158, sans(16, 600), WHITE)
            T(cc, "New launch spotted: Sonnet 5.5", sx + 80, sy + 182, sans(14, 400), "#d8d8de")
        devices.phone(c, -w / 2, -h / 2, w, h, screen, shadow=0.5)
    with G.layer(c, 0.35, blur=14):
        T(c, "New launch spotted", 960, 334, sans(58, 300), "#2a0f05", align=0.5)
    blur_in(c, "New launch spotted", 960, 330, sans(58, 300), WHITE, t, T_SUNSET + 0.08, dur=0.45, align=0.5)
