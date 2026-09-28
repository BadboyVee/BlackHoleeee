"""AGI WEEK, 4.3-7.1 s: Gemini.

The search pill on a pale blue ground, its sparkle sliding into place as the pill turns dark into Gemini's; then
the headline in Gemini's gradient, Another week closer to AGI., and a phone where the final week of September is
looking stacked: Gemini with Demis Hassabis, Muse with Mark Zuckerberg, Sonnet 5.5 with Dario and Daniela Amodei."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_expo, in_out_cubic
from . import marks as M
from .look import (WHITE, GEMINI_TEXT, T, gs, gsm, rr, blob, card, picture, ease_push)
from .score import T_SEARCH, T_MORPH, T_DARK, T_HEADLINE, T_PHONE, T_OAI

LIGHT_BG = ("#e4eaf6", "#f3f4f9")


def light_ground(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P(LIGHT_BG[0], 1, shader=G.linear_grad(0, 0, 1920, 1080, [
        LIGHT_BG[0], LIGHT_BG[1]])))
    blob(c, 260, 900, 700, "#d4e0fb", 0.8)
    blob(c, 1600, 180, 700, "#ffffff", 0.7)


# ---------------------------------------------------------------- the pill, light then dark

def search(c, t):
    """The search pill; from T_MORPH the inner pill slides right and the sparkle slides left, into Gemini's."""
    light_ground(c, t)
    s = ease_push(t, T_SEARCH, T_DARK, 0.04)
    u = in_out_cubic(clamp((t - T_MORPH) / (T_DARK - T_MORPH)))
    with G.xf(c, 960, 540, s=s):
        c.translate(-960, -540)
        card(c, 348, 348, 1224, 387, 64, "#f6f6f7", shadow=0.07, lift=24, blur=44, border=("#ffffff", 0.9, 2))
        ix, iw = lerp(387, 743, u), lerp(735, 805, u)
        card(c, ix, 387, iw, 311, 84, WHITE, shadow=0.05, lift=8, blur=22)
        M.google_g(c, 562, 541, 135)
        f = gsm(104)
        T(c, "Search", 682 + (ix - 387), 541 + f.cap / 2, f, "#1f1f1f", 1 - u)
        M.gemini(c, lerp(1341, 927, u), 541, 138, rot=90 * u)


def dark_pill(c, t, dy=0.0, a=1.0):
    """Gemini's dark pill: the G, then the sparkle and the name in the inner pill."""
    with G.xf(c, 0, dy):
        card(c, 333, 342, 1254, 393, 78, "#2a2a2c", a, shadow=0.3, lift=20, blur=40)
        card(c, 743, 378, 805, 321, 74, "#38383b", a, shadow=0.0)
        M.google_g(c, 551, 541, 135, a)
        M.gemini(c, 927, 541, 142, a)
        f = gsm(106)
        T(c, "Gemini", 1063, 541 + f.cap / 2, f, "#e8eaed", a)


def headline_lines():
    return ["Another week", "closer to AGI."]


def headline(c, t, x=104.0, y0=468.0, lh=236.0, size=218, a=1.0, reveal=None):
    """The post's first line, big, in Gemini's gradient."""
    f = gs(size)
    lines = headline_lines()
    wmax = max(f.width(s) for s in lines)
    sh = G.linear_grad(x, 0, x + wmax, 0, GEMINI_TEXT)
    for i, s in enumerate(lines):
        u = 1.0 if reveal is None else out_expo(clamp((t - reveal - 0.07 * i) / 0.4))
        if u <= 0:
            continue
        T(c, s, x, y0 + i * lh + 70 * (1 - u), f, WHITE, a * clamp(u * 1.6), shader=sh)


def dark(c, t):
    """The dark pill holds, then lifts away as the headline rises in under it."""
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#121212"))
    s = ease_push(t, T_DARK, T_PHONE, 0.035)
    lift = in_out_cubic(clamp((t - (T_HEADLINE - 0.12)) / 0.34))
    with G.xf(c, 960, 540, s=s):
        c.translate(-960, -540)
        if lift < 1:
            dark_pill(c, t, dy=-640 * lift)
        if t >= T_HEADLINE - 0.05:
            with G.xf(c, -18 * clamp((t - T_HEADLINE) / 0.8), 0):
                headline(c, t, reveal=T_HEADLINE - 0.05)


# ---------------------------------------------------------------- the phone

CARDS = [("hassabis", "Gemini", "Google DeepMind"), ("zuckerberg", "Muse", "Meta"),
         ("amodei", "Sonnet 5.5", "Anthropic")]


def phone_screen(c, t):
    """What the phone shows, in its own 900 x 1900 space."""
    c.drawRRect(rr(0, 0, 900, 1900, 118), G.P("#1b1b1e"))
    c.drawRRect(rr(3, 3, 894, 1894, 115), G.P("#4a4a50", 1, stroke=6))
    c.drawRRect(rr(26, 26, 848, 1848, 94), G.P("#0f0f11"))
    c.drawCircle(450, 92, 19, G.P("#050506"))
    c.drawCircle(450, 92, 19, G.P("#2a2a30", 1, stroke=3))
    fs = gsm(44)
    T(c, "9:30", 90, 112, fs, WHITE)
    T(c, "5G", 690, 112, fs, WHITE)
    c.drawPath(G.poly([(770, 116), (806, 116), (806, 78)]), G.P(WHITE))
    c.drawRRect(rr(822, 76, 22, 40, 5), G.P(WHITE))
    f = gs(92)
    lines = [("The final week", True), ("of September is", False), ("looking stacked.", False)]
    wmax = f.width(lines[0][0])
    sh = G.linear_grad(90, 0, 90 + wmax, 0, GEMINI_TEXT)
    for i, (s, grad) in enumerate(lines):
        T(c, s, 90, 330 + i * 108, f, WHITE if grad else "#9a9aa0", shader=sh if grad else None)
    for k, (who, title, sub) in enumerate(CARDS):
        x = 60 + k * 268
        u = out_expo(clamp((t - (T_PHONE + 0.1 + 0.07 * k)) / 0.4))
        if u <= 0:
            continue
        with G.xf(c, 0, 60 * (1 - u)):
            c.drawRRect(rr(x, 720, 250, 420, 30), G.P("#202024", u))
            T(c, title, x + 22, 790, gsm(38), WHITE, u)
            T(c, sub, x + 22, 836, gs(28), "#a8a8b0", u)
            picture(c, who, x + 16, 872, 218, 250, 20, a=u, which="crop")


def phone(c, t):
    light_ground(c, t)
    u = clamp((t - T_PHONE) / (T_OAI - T_PHONE))
    e = 0.5 - 0.5 * math.cos(math.pi * u)
    rx, ry, rz = lerp(12, 5, e), lerp(-16, -7, e), lerp(-5, -2.5, e)
    s = lerp(0.9, 0.96, e)
    with G.xf(c, 0, 0):
        c.concat(G.perspective(960, 520, rx=rx, ry=ry, rz=rz, D=2400))
        with G.xf(c, 960 - 450 * s, -30 + 40 * (1 - e), s=s):
            c.drawRRect(rr(18, 40, 900, 1900, 118), G.P("#000000", 0.35, blur=40))
            phone_screen(c, t)
