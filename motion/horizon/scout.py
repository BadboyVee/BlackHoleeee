"""HORIZON 2, Scout. A laptop out on the green hills shows the race behind the headlines; the camera pushes into
it, onto the Frontier Index, where a violet light passes; Scout, the agent you ask, comes up on white, then on a
phone: "what's coming this week?", thinking, and this week's read. The phone stands in a meadow, and the camera
closes in on the read: likely, next, watch, rumour."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_quart, in_cubic, in_out_cubic, out_back, hash01
from .look import (WHITE, INK, GREY, VIOLET, GOLD, GREEN, BLUE, sans, T, rr, blur_in, blur_out,
                   wrap, chip, hairline)
from . import plates, marks, devices, chat
from .score import (T_LAPTOP, T_PUSH, T_INDEX, T_SCOUT, T_PHONE, T_ASK, T_THINK, T_READ, T_MEADOW, T_CLOSE)

# ---------------------------------------------------------------- the laptop on the hills

LAP_X, LAP_Y, LAP_W = 510.0, 300.0, 900.0
LAP_SCREEN = (LAP_X + LAP_W * 0.022, LAP_Y + LAP_W * 0.022, LAP_W * 0.956, LAP_W * 0.64 - LAP_W * 0.052)
BARS = [(0.08, 0.30, GOLD), (0.14, 0.42, BLUE), (0.20, 0.36, VIOLET), (0.26, 0.55, GREEN), (0.74, 0.40, BLUE),
        (0.80, 0.62, GOLD), (0.86, 0.50, VIOLET), (0.92, 0.72, GREEN)]


def laptop_screen(c, sx, sy, sw, sh, t):
    c.drawRect(skia.Rect.MakeXYWH(sx, sy, sw, sh), G.P(WHITE))
    for i in range(1, 6):                                            # faint rules
        c.drawLine(sx, sy + sh * i / 6, sx + sw, sy + sh * i / 6, G.P("#eef0f4", 1, stroke=1))
    for i, (px, ph, col) in enumerate(BARS):
        u = out_cubic(clamp((t - (T_LAPTOP + 0.15 + 0.06 * i)) / 0.5))
        if u <= 0:
            continue
        h = sh * ph * u
        x = sx + sw * px
        c.drawRRect(rr(x - 7, sy + sh - 18 - h, 14, h, 4), G.P(col, 0.9))
        c.drawLine(x, sy + sh - 18 - h - 14 * u, x, sy + sh - 18 - h, G.P(col, 0.6, stroke=2))
    blur_in(c, "See the race behind the headlines", sx + sw / 2, sy + sh * 0.47, sans(sw * 0.036, 520), INK, t,
            T_LAPTOP + 0.2, dur=0.5, align=0.5)
    blur_in(c, "Frontier Index · live", sx + sw / 2, sy + sh * 0.47 + sw * 0.034, sans(sw * 0.02, 420), GREY, t,
            T_LAPTOP + 0.4, dur=0.5, align=0.5)


def hills_laptop(c, t):
    tau = t - T_LAPTOP
    plates.day(c, t, zoom=1.0 + 0.012 * tau, cx=0.5, cy=0.5)
    u = in_cubic(clamp((t - T_PUSH) / (T_INDEX - T_PUSH)))
    sx, sy, sw, sh = LAP_SCREEN
    z = lerp(1.0, 1920.0 / sw * 1.02, u)
    cx, cy = lerp(960, sx + sw / 2, u), lerp(540, sy + sh / 2, u)
    rise = 40 * (1 - out_cubic(clamp(tau / 0.6)))
    with G.xf(c, 960, 540, s=z):
        c.translate(-cx, -cy + rise)
        devices.laptop(c, LAP_X, LAP_Y, LAP_W, lambda cc, a, b, w, h: laptop_screen(cc, a, b, w, h, t))


# ---------------------------------------------------------------- the Frontier Index

CARD = (360.0, 190.0, 1200.0, 700.0)
SERIES = [0.22, 0.25, 0.23, 0.30, 0.34, 0.31, 0.38, 0.44, 0.41, 0.49, 0.55, 0.52, 0.60, 0.66, 0.63, 0.72, 0.78,
          0.76, 0.84, 0.90]


def index_card(c, t):
    x, y, w, h = CARD
    tau = t - T_INDEX
    c.drawRRect(rr(x, y + 16, w, h, 26), G.P("#1b2340", 0.10, blur=30))
    c.drawRRect(rr(x, y, w, h, 26), G.P(WHITE))
    c.drawRRect(rr(x + 0.5, y + 0.5, w - 1, h - 1, 26), G.P("#e6e8ef", 1, stroke=1.4))
    marks.mark(c, x + 58, y + 64, 40)
    T(c, "FRONTIER INDEX", x + 92, y + 60, sans(16, 650), INK, tracking=0.12)
    T(c, "Fable 5.1 leads", x + 92, y + 84, sans(15, 420), GREY)
    k = out_cubic(clamp(tau / 0.5))
    T(c, f"{int(1445 + 42 * k):,}", x + 44, y + 170, sans(76, 500), INK, tracking=-0.02)
    T(c, "+42 this week", x + 44, y + 206, sans(19, 520), "#1f9d55")
    for i, lab in enumerate(["1D", "1W", "1M", "1Y", "ALL"]):
        bx = x + 470 + i * 62
        if lab == "1W":
            c.drawRRect(rr(bx - 8, y + 44, 52, 30, 15), G.P("#eef1ff"))
        T(c, lab, bx + 18, y + 64, sans(14, 560), BLUE if lab == "1W" else GREY, align=0.5)
    # the chart
    cx0, cy0, cw, ch = x + 44, y + 250, 760, 360
    for i in range(5):
        c.drawLine(cx0, cy0 + ch * i / 4, cx0 + cw, cy0 + ch * i / 4, G.P("#f0f1f5", 1, stroke=1))
    p = skia.Path()
    pts = [(cx0 + cw * i / (len(SERIES) - 1), cy0 + ch * (1 - v)) for i, v in enumerate(SERIES)]
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    e = out_cubic(clamp((tau - 0.1) / 0.7))
    if e > 0:
        fill = skia.Path(p)
        fill.lineTo(pts[-1][0], cy0 + ch)
        fill.lineTo(pts[0][0], cy0 + ch)
        fill.close()
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(cx0, cy0 - 20, cx0 + cw * e, cy0 + ch))
        c.drawPath(fill, G.P(VIOLET, 1, shader=G.linear_grad(0, cy0, 0, cy0 + ch, ["#8c8cff", "#ffffff"],
                                                             alphas=[0.28, 0.0])))
        c.drawPath(p, G.P("#5b5bf0", 1, stroke=3, join="round"))
        c.restore()
    # the side column
    rows = [("Labs tracked", "14"), ("Launches this week", "5"), ("Next drop", "2d 04h")]
    for i, (k1, v1) in enumerate(rows):
        ry = y + 290 + i * 120
        a = clamp((tau - 0.15 - 0.1 * i) / 0.3)
        T(c, k1, x + 860, ry, sans(16, 420), GREY, a)
        T(c, v1, x + 860, ry + 40, sans(30, 520), INK, a)
        for j in range(6):
            bh = 8 + 26 * hash01(i * 7 + j, 3)
            c.drawRRect(rr(x + 1060 + j * 14, ry + 40 - bh, 8, bh, 2), G.P("#7c7cf6", a * (0.35 + 0.1 * j)))
    T(c, "Sonnet 5.5 · rolling out", x + 44, y + h - 34, sans(16, 460), GREY)
    T(c, "view the race ›", x + w - 44, y + h - 34, sans(16, 520), BLUE, align=1.0)


def streak(c, t, t0, y, dur=0.8):
    """A violet light passing across, like a flare on glass."""
    u = clamp((t - t0) / dur)
    if not 0 < u < 1:
        return
    x = lerp(-600, 2500, in_out_cubic(u))
    with G.layer(c, math.sin(math.pi * u)):
        c.drawOval(skia.Rect.MakeXYWH(x - 700, y - 9, 1400, 18), G.P(VIOLET, 0.55, blur=10))
        c.drawOval(skia.Rect.MakeXYWH(x - 420, y - 3, 840, 6), G.P("#c9c9ff", 0.9, blur=2))


def index(c, t):
    a, b = blur_out(t, T_SCOUT - 0.26, 0.26)
    k = 1 + 0.03 * (t - T_INDEX)
    with G.layer(c, a, blur=b):
        with G.xf(c, 960, 540, s=k):
            c.translate(-960, -540)
            index_card(c, t)
    streak(c, t, T_INDEX + 0.28, CARD[1] + CARD[3] - 70)


# ---------------------------------------------------------------- Scout, on white

def scout_icon(c, t):
    tau = t - T_SCOUT
    z = 1 + 0.05 * tau
    with G.xf(c, 960, 520, s=z):
        u = out_cubic(clamp(tau / 0.5))
        hairline(c, -1200, 0, lerp(-1200, -95, u), 0, "#c9ccd6", 1, 1.4)
        hairline(c, 95, 0, lerp(95, 1200, u), 0, "#c9ccd6", clamp(tau / 0.3), 1.4)
        dot = lerp(-700, -118, u)
        c.drawCircle(dot, 0, 7, G.P(WHITE))
        c.drawCircle(dot, 0, 7, G.P(BLUE, 1, stroke=2))
        s = out_back(clamp((tau - 0.15) / 0.4), 1.8)
        if s > 0.01:
            with G.xf(c, 0, 0, s=s):
                marks.icon(c, 0, 0, 150, shape="round", glow=0.8)
        blur_in(c, "SCOUT", 0, 132, sans(20, 600), "#6b6f7a", t, T_SCOUT + 0.35, dur=0.4, align=0.5,
                tracking=0.32)


# ---------------------------------------------------------------- the phone

def chat_screen(c, sx, sy, sw, sh, t, scroll=0.0):
    k = sw / 416
    c.drawRect(skia.Rect.MakeXYWH(sx, sy, sw, sh), G.P("#0c0c0e"))
    devices.status_bar(c, sx, sy, sw)
    hy = sy + 92 * k
    for i in range(3):
        c.drawLine(sx + 26 * k, hy - 8 * k + i * 7 * k, sx + 44 * k, hy - 8 * k + i * 7 * k,
                   G.P(WHITE, 0.8, stroke=2 * k, cap="round"))
    marks.icon(c, sx + sw / 2 - 58 * k, hy, 38 * k, shape="round", glow=0.0)
    T(c, "Horizon", sx + sw / 2 - 30 * k, hy - 2 * k, sans(18 * k, 520), WHITE)
    T(c, "Scout", sx + sw / 2 - 30 * k, hy + 17 * k, sans(13 * k, 420), GREY)
    c.drawCircle(sx + sw - 38 * k, hy, 17 * k, G.P("#1e1e22"))
    for i in (-1, 0, 1):
        c.drawCircle(sx + sw - 38 * k + i * 6 * k, hy, 1.8 * k, G.P(WHITE))
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(sx, sy + 124 * k, sx + sw, sy + sh))
    y = sy + 150 * k - scroll
    # the question
    u = clamp((t - T_ASK) / 0.3)
    if u > 0:
        f = sans(17 * k, 420)
        bw = f.width(chat.ASK) + 36 * k
        bx = sx + sw - 20 * k - bw
        with G.layer(c, clamp(u * 2)):
            c.drawRRect(rr(bx, y + 10 * k * (1 - out_cubic(u)), bw, 46 * k, 20 * k), G.P("#26262b"))
            T(c, chat.ASK, bx + 18 * k, y + 29 * k + 10 * k * (1 - out_cubic(u)), f, WHITE)
    y += 80 * k
    # Scout
    if t >= T_THINK:
        marks.icon(c, sx + 38 * k, y + 14 * k, 30 * k, shape="round", glow=0.0)
        if t < T_READ:
            f = sans(16 * k, 420)
            x = sx + 64 * k
            for i, ch in enumerate("Thinking…"):                      # a shimmer runs along it
                g = 0.45 + 0.55 * max(0.0, math.cos(2 * math.pi * ((t - T_THINK) * 1.1 - i / 12)))
                T(c, ch, x, y + 20 * k, f, WHITE, g)
                x += f.width(ch)
        else:
            u = clamp((t - T_READ) / 0.3)
            T(c, chat.TITLE, sx + 64 * k, y + 20 * k, sans(17 * k, 600), WHITE, u)
            T(c, chat.HEAT, sx + 64 * k, y + 42 * k, sans(11 * k, 600), GREY, u, tracking=0.12)
            yy = y + 72 * k
            f = sans(16 * k, 400)
            for i, (lab, fg, bg, text) in enumerate(chat.ITEMS):
                t0 = T_READ + 0.25 + 0.55 * i
                if t < t0:
                    break
                a = clamp((t - t0) / 0.25)
                chip(c, sx + 64 * k, yy + 10 * k, lab, fg, bg, size=10.5 * k, a=a)
                yy += 30 * k
                lines = wrap(text, f, sw - 90 * k)
                shown = int(max(0.0, t - t0 - 0.1) * 90)               # it types out
                for ln in lines:
                    part = ln[:max(0, shown)]
                    shown -= len(ln) + 1
                    T(c, part, sx + 64 * k, yy + 16 * k, f, "#e7e7ea", a)
                    yy += 23 * k
                yy += 16 * k
    c.restore()


PHONE_W, PHONE_H = 460.0, 940.0


def phone_scene(c, t):
    """On white: the phone slides in, the chat plays, and the camera draws in to the screen."""
    tau = t - T_PHONE
    u = out_quart(clamp(tau / 0.55))
    x = lerp(2150.0, 730.0, u)
    rot = lerp(9.0, 0.0, u)
    z = lerp(1.0, 1.28, in_out_cubic(clamp((t - (T_READ - 0.4)) / 1.8)))
    with G.xf(c, 960, 540, s=z):
        c.translate(-960, -540 + 30 * (z - 1) * 10)
        with G.xf(c, x + PHONE_W / 2, 70 + PHONE_H / 2, rot=rot):
            devices.phone(c, -PHONE_W / 2, -PHONE_H / 2, PHONE_W, PHONE_H,
                          lambda cc, a, b, w, h: chat_screen(cc, a, b, w, h, t), shadow=0.25)


# ---------------------------------------------------------------- in the meadow

FLOWERS = [   # (x, y, size, colour) in the foreground, out of focus
    (80, 1010, 70, "#ff4d3d"), (210, 960, 54, "#ffd23f"), (40, 880, 46, "#fff4e0"), (330, 1040, 62, "#ff7eb6"),
    (150, 1080, 80, "#ffd23f"), (1600, 1030, 64, "#ff4d3d"), (1760, 960, 52, "#fff4e0"), (1860, 1050, 76, "#ffd23f"),
    (1480, 1080, 58, "#ff7eb6"), (1700, 880, 40, "#ff4d3d"), (420, 1090, 44, "#fff4e0"), (1350, 1060, 40, "#ffd23f"),
]


def flower(c, x, y, s, col):
    for i in range(5):
        a = 2 * math.pi * i / 5
        c.drawOval(skia.Rect.MakeXYWH(x + math.cos(a) * s * 0.42 - s * 0.3, y + math.sin(a) * s * 0.42 - s * 0.3,
                                      s * 0.6, s * 0.6), G.P(col))
    c.drawCircle(x, y, s * 0.2, G.P("#f5b700" if col != "#ffd23f" else "#d98a00"))


def meadow_front(c, t, blur=14.0):
    with G.layer(c, 1.0, blur=blur):
        for i in range(40):                                              # grass blades
            x = hash01(i, 21) * 1920
            if 520 < x < 1400:
                continue
            h = 160 + 200 * hash01(i, 22)
            sway = 12 * math.sin(1.3 * t + i)
            p = skia.Path()
            p.moveTo(x, 1100)
            p.quadTo(x + sway * 0.5, 1100 - h * 0.5, x + sway, 1100 - h)
            c.drawPath(p, G.P("#2f7a1c", 0.9, stroke=10 + 8 * hash01(i, 23), cap="round"))
        for x, y, s, col in FLOWERS:
            flower(c, x + 6 * math.sin(0.9 * t + x), y, s, col)


def meadow(c, t):
    tau = t - T_MEADOW
    plates.day(c, t, zoom=1.35 + 0.02 * tau, cx=0.5, cy=0.62, drift=-25 * tau, soft=4.0)
    w, h = 400.0, 818.0
    x = 960 - w / 2 + 18 * math.sin(0.6 * tau)
    y = 150 - 10 * tau
    with G.xf(c, x + w / 2, y + h / 2, rot=-3 + 1.5 * tau):
        devices.phone(c, -w / 2, -h / 2, w, h, lambda cc, a, b, ww, hh: chat_screen(cc, a, b, ww, hh, t, scroll=40),
                      shadow=0.4)
    meadow_front(c, t)


# ---------------------------------------------------------------- close on the read

def close(c, t):
    tau = t - T_CLOSE
    plates.day(c, t, zoom=1.6, cx=0.5, cy=0.66, drift=-20 * tau, soft=5.0)
    w = 1180.0
    h = w * 940 / 460
    scroll = 150 * (w / 460) + 60 * tau
    x = 960 - w / 2
    y = -140.0 - 20 * tau
    devices.phone(c, x, y, w, h, lambda cc, a, b, ww, hh: chat_screen(cc, a, b, ww, hh, max(t, T_READ + 3.2),
                                                                     scroll=scroll), shadow=0.3, island=False)
    meadow_front(c, t, blur=18.0)


# ---------------------------------------------------------------- the section

def scout(c, t):
    if t < T_INDEX:
        hills_laptop(c, t)
    elif t < T_SCOUT:
        index(c, t)
    elif t < T_PHONE:
        scout_icon(c, t)
    elif t < T_MEADOW:
        phone_scene(c, t)
    elif t < T_CLOSE:
        meadow(c, t)
    else:
        close(c, t)
