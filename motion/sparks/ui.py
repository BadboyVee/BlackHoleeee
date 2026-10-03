"""SPARKS: the little screens around the toys. Its own computer, its own browser, your apps, what it remembers,
messages, a call, code with a bug in it, feedback, a fix and its checks, a chart that reruns, a job overnight, a
question before it acts, and the rules."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, in_out_cubic, hash01
from .look import (WHITE, INK, GREY, SOFT, CARD, CARD_LINE, TERRACOTTA, MINT, BUTTER, LAVENDER, INDIGO, RED, GREEN,
                   BLUE, sans, T, rr, card, pop)


def appear(t, t0, dur=0.3):
    u = clamp((t - t0) / dur)
    return u, (out_back(u, 1.6) if u < 1 else 1.0)


def spark_glyph(c, x, y, r, col=TERRACOTTA, a=1.0, rot=0.0):
    """Claude's spark, as eight rounded rays."""
    p = G.P(col, a, stroke=r * 0.26, cap="round")
    for i in range(8):
        ang = rot + math.pi * i / 4
        L = r * (1.0 if i % 2 == 0 else 0.7)
        c.drawLine(x + math.cos(ang) * r * 0.18, y + math.sin(ang) * r * 0.18, x + math.cos(ang) * L,
                   y + math.sin(ang) * L, p)


def cursor(c, x, y, s=1.4, pressed=0.0):
    p = skia.Path()
    for px, py in [(0, 0), (0, 25), (6.5, 19.5), (11, 29.5), (15, 27.6), (10.8, 18), (19, 18)]:
        (p.moveTo if p.isEmpty() else p.lineTo)(px, py)
    p.close()
    with G.xf(c, x, y, s=s * (1 - 0.12 * pressed)):
        c.drawPath(p, G.P("#000000", 0.2, blur=3))
        c.drawPath(p, G.P(INK))
        c.drawPath(p, G.P(WHITE, 1, stroke=1.6, join="round"))


def working_pill(c, t, x, y, text="working…", a=1.0):
    f = sans(18, 600)
    w = f.width(text) + 58
    with G.layer(c, a):
        c.drawRRect(rr(x - w / 2, y - 20, w, 40, 20), G.P(INK))
        spark_glyph(c, x - w / 2 + 24, y, 9, col="#f0a37f", rot=1.2 * t)
        T(c, text, x - w / 2 + 42, y + 6, f, WHITE)


# ---------------------------------------------------------------- its own computer

def computer(c, t, t0, x, y, w=680, h=440, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, r=16, fill=WHITE)
            c.drawRRect(rr(0, 0, w, 44, 16), G.P("#f1f1f4"))
            c.drawRect(skia.Rect.MakeXYWH(0, 28, w, 16), G.P("#f1f1f4"))
            for i, col in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
                c.drawCircle(24 + i * 20, 22, 6, G.P(col))
            c.drawRect(skia.Rect.MakeXYWH(0, 44, 150, h - 44), G.P("#f7f7f9"))
            for i in range(5):
                c.drawRRect(rr(22, 72 + i * 42, 16, 16, 4), G.P([BLUE, MINT, BUTTER, LAVENDER, TERRACOTTA][i], 0.8))
                c.drawRRect(rr(48, 76 + i * 42, 70, 8, 4), G.P("#dcdce3"))
            # a document writing itself
            T(c, "Q3 plan", 180, 96, sans(26, 700), INK, tracking=-0.02)
            n = clamp((t - t0 - 0.2) / 1.2)
            lines = [0.86, 0.92, 0.7, 0.95, 0.8, 0.6, 0.88]
            shown = n * len(lines)
            for i, ln in enumerate(lines):
                f = clamp(shown - i)
                if f <= 0:
                    break
                c.drawRRect(rr(180, 124 + i * 34, (w - 220) * ln * f, 10, 5), G.P("#d6d8e2"))
            cx, cy = 180 + (w - 220) * lines[min(int(shown), len(lines) - 1)] * clamp(shown - int(shown)), \
                124 + min(int(shown), len(lines) - 1) * 34
            if n < 1 and (t * 2) % 1 < 0.6:
                c.drawRect(skia.Rect.MakeXYWH(cx + 2, cy - 6, 3, 22), G.P(TERRACOTTA))
            working_pill(c, t, w - 130, h - 40, "writing…")


# ---------------------------------------------------------------- its own browser

ROWS = [("Luca · 7:30 pm", "table for two · window"), ("Nori Bar · 8:00 pm", "counter seats"),
        ("Olive & Rye · 7:45 pm", "garden table")]


def browser(c, t, t0, x, y, w=700, h=440, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, r=16, fill=WHITE)
            c.drawRRect(rr(0, 0, w, 84, 16), G.P("#f1f1f4"))
            c.drawRect(skia.Rect.MakeXYWH(0, 60, w, 24), G.P("#f1f1f4"))
            for i, col in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
                c.drawCircle(24 + i * 20, 22, 6, G.P(col))
            c.drawRRect(rr(96, 10, 170, 26, 8), G.P(WHITE))
            T(c, "Book a table", 110, 29, sans(15, 600), INK)
            c.drawRRect(rr(20, 46, w - 40, 30, 15), G.P(WHITE))
            T(c, "tables near me, friday", 44, 67, sans(16, 500), GREY)
            pick = t >= t0 + 1.05
            for i, (name, sub) in enumerate(ROWS):
                yy = 104 + i * 100
                sel = pick and i == 0
                c.drawRRect(rr(20, yy, w - 40, 86, 14), G.P("#eef4ff" if sel else CARD))
                if sel:
                    c.drawRRect(rr(20.5, yy + 0.5, w - 41, 85, 14), G.P(BLUE, 1, stroke=2))
                c.drawRRect(rr(36, yy + 14, 58, 58, 10), G.P(["#f0c9a8", "#c9dcc0", "#d9cff0"][i]))
                T(c, name, 112, yy + 38, sans(21, 650), INK)
                T(c, sub, 112, yy + 64, sans(16, 500), GREY)
                bx = w - 150
                c.drawRRect(rr(bx, yy + 24, 110, 38, 19), G.P(GREEN if sel else INK))
                T(c, "Booked" if sel else "Book", bx + 55, yy + 49, sans(16, 650), WHITE, align=0.5)
            # the cursor goes to the first Book button and clicks
            v = in_out_cubic(clamp((t - (t0 + 0.35)) / 0.65))
            pressed = clamp(1 - abs(t - (t0 + 1.02)) / 0.08)
            cursor(c, lerp(w - 20, w - 96, v), lerp(h + 30, 148, v), pressed=pressed)


# ---------------------------------------------------------------- your apps

APPS = [("mail", "#ea4335"), ("calendar", "#2f7bff"), ("docs", "#3b82f6"), ("sheets", "#22c55e"), ("files", "#f59e0b"),
        ("chat", "#8b5cf6"), ("code", "#111827"), ("design", "#ef4444"), ("tasks", "#10b981"), ("billing", "#6366f1"),
        ("video", "#0ea5e9"), ("CRM", "#f97316"), ("notes", "#eab308"), ("maps", "#14b8a6")]


def apps(c, t, t0, cx, cy, a=1.0):
    for i, (name, col) in enumerate(APPS):
        s = pop(t, t0 + 0.028 * i, 0.3, 2.4)
        if s <= 0.01:
            continue
        ang = 2 * math.pi * (i / len(APPS)) + 0.32 * (t - t0)
        rx, ry = 360 + 50 * hash01(i, 3), 225 + 40 * hash01(i, 4)
        x = cx + rx * math.cos(ang) * s
        y = cy + ry * math.sin(ang) * s + 8 * math.sin(3 * t + i)
        f = sans(20, 650)
        w = f.width(name) + 58
        with G.layer(c, a):
            with G.xf(c, x, y, s=s):
                c.drawRRect(rr(-w / 2, -26 + 6, w, 52, 16), G.P("#000000", 0.08, blur=10))
                c.drawRRect(rr(-w / 2, -26, w, 52, 16), G.P(WHITE))
                c.drawRRect(rr(-w / 2 + 10, -14, 28, 28, 8), G.P(col))
                T(c, name, -w / 2 + 46, 7, f, INK)


# ---------------------------------------------------------------- learns how you work

MEMORY = ["what you care about", "how you write", "when to ping you"]


def memory(c, t, t0, times, x, y, w=560, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    h = 96 + 66 * len(MEMORY)
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            spark_glyph(c, 38, 44, 12, rot=0.3)
            T(c, "Memory", 62, 52, sans(24, 700), INK, tracking=-0.02)
            T(c, "about you", w - 30, 52, sans(17, 500), SOFT, align=1.0)
            for i, (item, ti) in enumerate(zip(MEMORY, times)):
                v, kk = appear(t, ti, 0.28)
                if v <= 0:
                    continue
                yy = 88 + i * 66
                with G.layer(c, clamp(v * 2)):
                    c.drawRRect(rr(20, yy, w - 40, 52, 12), G.P(CARD))
                    c.drawCircle(46, yy + 26, 11 * kk, G.P(LAVENDER))
                    p = skia.Path()
                    p.moveTo(40, yy + 26)
                    p.lineTo(44.5, yy + 30.5)
                    p.lineTo(52, yy + 21)
                    c.drawPath(p, G.P(WHITE, 1, stroke=3, cap="round", join="round"))
                    T(c, item, 70, yy + 34, sans(22, 500), INK)


# ---------------------------------------------------------------- message it, or just talk

def bubble(c, t, t0, x, y, s, typing=False, a=1.0):
    k = pop(t, t0, 0.3, 2.4)
    if k <= 0.01:
        return
    f = sans(22, 600)
    w = (f.width(s) if not typing else 44) + 44
    h = 54
    with G.layer(c, a):
        with G.xf(c, x, y, s=k):
            c.drawRRect(rr(-w / 2, -h / 2 + 8, w, h, 20), G.P("#000000", 0.07, blur=12))
            c.drawRRect(rr(-w / 2, -h / 2, w, h, 20), G.P(WHITE))
            c.drawRRect(rr(-w / 2 + 0.5, -h / 2 + 0.5, w - 1, h - 1, 20), G.P(CARD_LINE, 1, stroke=1.2))
            if typing:
                for i in range(3):
                    g = 0.3 + 0.7 * max(0.0, math.sin(2 * math.pi * (1.6 * (t - t0) - i * 0.2)))
                    c.drawCircle(-14 + i * 14, 0, 5, G.P("#6b6b76", g))
            else:
                T(c, s, 0, 8, f, INK, align=0.5)


def call(c, t, t0, cx, cy, r=175):
    """A call ringing: a ring round the toy, ripples, a green handset, a voice."""
    if t < t0:
        return
    tau = t - t0
    k = pop(t, t0, 0.35, 2.2)
    c.drawCircle(cx, cy, r * k, G.P("#f5b700", 0.95, stroke=6))
    for i in range(3):
        v = ((tau * 0.9) + i / 3) % 1.0
        c.drawCircle(cx, cy, r * (1 + 0.55 * v), G.P("#f5b700", 0.45 * (1 - v), stroke=3))
    s = pop(t, t0 + 0.15, 0.3, 2.6)
    if s > 0.01:
        with G.xf(c, cx, cy - r - 8, s=s):
            c.drawCircle(0, 0, 30, G.P(GREEN))
            p = skia.Path()                                          # a handset
            p.moveTo(-12, -6)
            p.quadTo(-12, 10, 6, 13)
            c.drawPath(p, G.P(WHITE, 1, stroke=6, cap="round"))
    # the voice, a few bars
    for i in range(9):
        h = 8 + 26 * abs(math.sin(9 * tau + i * 0.8)) * hash01(i, 7)
        x = cx - 64 + i * 16
        c.drawRRect(rr(x - 4, cy + r + 34 - h / 2, 8, h, 4), G.P("#f5b700", 0.9))


# ---------------------------------------------------------------- a bug, on it

CODE = [(0, 0.34, RED), (1, 0.52, None), (1, 0.44, None), (2, 0.30, RED), (2, 0.58, None), (1, 0.40, None),
        (0, 0.22, RED), (1, 0.50, None), (1, 0.36, None)]


def code_card(c, x, y, w=620, h=440, a=1.0, glow=0.0):
    card(c, x, y, w, h, fill=WHITE, a=a)
    for i, (d, ln, col) in enumerate(CODE):
        yy = y + 50 + i * 42
        c.drawRRect(rr(x + 30, yy, 26, 10, 5), G.P("#ff9ab0" if col else "#ffc9d6", a))
        c.drawRRect(rr(x + 70 + d * 30, yy, w * ln, 10, 5), G.P("#d8dae3", a))
    if glow > 0:
        c.drawRRect(rr(x, y, w, h, 18), G.P(GREEN, 0.9 * glow, stroke=3))


def bug(c, x, y, s, t, squash=0.0, a=1.0):
    """A small red beetle, legs going."""
    if a <= 0:
        return
    with G.layer(c, a):
        with G.xf(c, x, y, sx=s * (1 + 0.5 * squash), sy=s * (1 - 0.7 * squash)):
            for i in range(3):
                for sx in (-1, 1):
                    ph = math.sin(2 * math.pi * (6 * t + i * 0.33 + (0.5 if sx > 0 else 0)))
                    p = skia.Path()
                    p.moveTo(sx * 6, -6 + i * 7)
                    p.lineTo(sx * 16, -9 + i * 8 + 3 * ph)
                    p.lineTo(sx * 21, -2 + i * 8 + 3 * ph)
                    c.drawPath(p, G.P("#7a1010", 1, stroke=2.4, cap="round", join="round"))
            c.drawOval(skia.Rect.MakeXYWH(-11, -14, 22, 30), G.P(RED, 1, shader=G.radial_grad(-4, -6, 22,
                                                                                             ["#ff8a80", RED, "#b3161b"])))
            c.drawLine(0, -12, 0, 15, G.P("#7a1010", 0.8, stroke=1.6))
            c.drawCircle(0, -17, 7, G.P("#3a0a0a"))
            for sx in (-1, 1):
                c.drawLine(sx * 3, -22, sx * 9, -30, G.P("#3a0a0a", 1, stroke=2, cap="round"))
            for (dx, dy) in [(-5, -3), (5, 2), (-4, 8)]:
                c.drawCircle(dx, dy, 2.4, G.P("#3a0a0a", 0.7))


def check_badge(c, x, y, r, s=1.0, col=GREEN):
    if s <= 0.01:
        return
    with G.xf(c, x, y, s=s):
        c.drawCircle(0, 0, r, G.P(col))
        p = skia.Path()
        p.moveTo(-r * 0.42, 0)
        p.lineTo(-r * 0.1, r * 0.32)
        p.lineTo(r * 0.45, -r * 0.3)
        c.drawPath(p, G.P(WHITE, 1, stroke=r * 0.22, cap="round", join="round"))


# ---------------------------------------------------------------- feedback, tested fixes

REVIEWS = [(5, "love the new export"), (3, "login sometimes hangs"), (4, "please add dark mode")]


def stars(c, x, y, n, size=16):
    for i in range(5):
        p = skia.Path()
        for j in range(10):
            ang = -math.pi / 2 + math.pi * j / 5
            r = size * (0.5 if j % 2 == 0 else 0.22)
            (p.moveTo if j == 0 else p.lineTo)(x + i * size * 1.15 + math.cos(ang) * r, y + math.sin(ang) * r)
        p.close()
        c.drawPath(p, G.P("#f5a524" if i < n else "#dcdce3"))


def feedback(c, t, t0, x, y, a=1.0):
    for i, (n, s) in enumerate(REVIEWS):
        u, k = appear(t, t0 + 0.12 * i)
        if u <= 0:
            continue
        yy = y + i * 118
        with G.layer(c, a * clamp(u * 2)):
            with G.xf(c, x + 230, yy + 46, s=0.85 + 0.15 * k):
                c.translate(-230, -46)
                card(c, 0, 0, 460, 92, fill=WHITE)
                stars(c, 30, 32, n)
                T(c, s, 30, 70, sans(21, 520), INK)


CHECKS = ["login no longer hangs", "export keeps your layout", "dark mode, everywhere"]


def fixes(c, t, t0, x, y, checked_from=None, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    w, h = 540, 330
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            p = skia.Path()
            p.moveTo(34, 30)
            p.lineTo(34, 58)
            p.moveTo(34, 44)
            p.quadTo(52, 44, 52, 30)
            c.drawPath(p, G.P(TERRACOTTA, 1, stroke=3, cap="round"))
            c.drawCircle(34, 30, 4, G.P(TERRACOTTA))
            c.drawCircle(52, 30, 4, G.P(TERRACOTTA))
            T(c, "fix #214", 70, 52, sans(26, 700), INK, tracking=-0.02)
            T(c, "from this week's feedback", 70, 80, sans(17, 500), GREY)
            for i, s in enumerate(CHECKS):
                yy = 118 + i * 64
                c.drawRRect(rr(20, yy, w - 40, 50, 12), G.P(CARD))
                done = checked_from is not None and t >= checked_from + 0.28 * i
                if done:
                    check_badge(c, 46, yy + 25, 12, pop(t, checked_from + 0.28 * i, 0.25, 2.6))
                else:
                    c.drawCircle(46, yy + 25, 11, G.P("#c9ccd8", 1, stroke=2))
                T(c, s, 70, yy + 33, sans(21, 500), INK if done else GREY)


# ---------------------------------------------------------------- new numbers, it reruns itself

BARS = [0.38, 0.52, 0.46, 0.64, 0.58, 0.74]
NEW = 0.92


def chart(c, t, t0, x, y, rerun=None, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    w, h = 620, 400
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            T(c, "Weekly sales", 30, 52, sans(24, 700), INK, tracking=-0.02)
            f = sans(16, 650)
            if rerun is not None and t >= rerun:
                label, col = "updated just now", GREEN
            else:
                label, col = "new data", LAVENDER
            bw = f.width(label) + 28
            c.drawRRect(rr(w - 30 - bw, 28, bw, 32, 16), G.P(col, 0.14))
            T(c, label, w - 30 - bw / 2, 50, f, col, align=0.5)
            base = 350
            for i, v in enumerate(BARS + [NEW]):
                grow = out_cubic(clamp((t - t0 - 0.05 * i) / 0.4))
                if i == len(BARS):                                     # the new week's bar arrives late
                    grow = out_back(clamp((t - (t0 + 0.6)) / 0.4), 1.6)
                if rerun is not None and t >= rerun:                  # the rerun sweeps them all again
                    grow *= 0.35 + 0.65 * out_cubic(clamp((t - rerun - 0.04 * i) / 0.35))
                bh = 250 * v * grow
                c.drawRRect(rr(40 + i * 80, base - bh, 50, bh, 8),
                            G.P(LAVENDER if i < len(BARS) else "#7c5cf0", 0.9))
            if rerun is not None and t >= rerun:
                ang = 4 * (t - rerun)
                with G.xf(c, w - 60 - bw, 44, rot=math.degrees(ang)):
                    arc = skia.Path()
                    arc.addArc(skia.Rect.MakeXYWH(-9, -9, 18, 18), 30, 280)
                    c.drawPath(arc, G.P(GREEN, 1, stroke=2.5, cap="round"))


# ---------------------------------------------------------------- while you sleep

def moon(c, x, y, r, a=1.0):
    p = skia.Path()
    p.addCircle(x, y, r)
    q = skia.Path()
    q.addCircle(x + r * 0.45, y - r * 0.3, r * 0.85)
    c.drawPath(skia.Op(p, q, skia.PathOp.kDifference_PathOp), G.P("#1a1a22", a))


def sun(c, x, y, r, t, a=1.0):
    c.drawCircle(x, y, r * 0.5, G.P("#ffb020", a))
    for i in range(8):
        ang = 2 * math.pi * i / 8 + 0.4 * t
        c.drawLine(x + math.cos(ang) * r * 0.72, y + math.sin(ang) * r * 0.72, x + math.cos(ang) * r,
                   y + math.sin(ang) * r, G.P("#ffb020", a, stroke=r * 0.14, cap="round"))


def job(c, t, t0, x, y, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    w, h = 580, 200
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            T(c, "Weekly report", 30, 56, sans(24, 700), INK, tracking=-0.02)
            n = min(18, int(4 + 14 * clamp((t - t0) / 1.2)))
            T(c, f"{n} of 18 sections", w - 30, 56, sans(18, 520), GREY, align=1.0)
            c.drawRRect(rr(30, 104, w - 60, 14, 7), G.P("#ececf0"))
            c.drawRRect(rr(30, 104, (w - 60) * n / 18, 14, 7), G.P(INDIGO))
            T(c, "ready in your inbox by 7:00", 30, 160, sans(18, 500), GREY)


# ---------------------------------------------------------------- it asks first, the rules

def approval(c, t, t0, click, x, y, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    w, h = 560, 240
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            spark_glyph(c, 40, 50, 12, rot=0.3)
            T(c, "Send the report to your team?", 64, 58, sans(24, 700), INK, tracking=-0.02)
            T(c, "12 people · #weekly", 64, 90, sans(18, 500), GREY)
            pressed = clamp(1 - abs(t - click) / 0.08) if t >= click - 0.08 else 0.0
            done = t >= click + 0.05
            with G.xf(c, 30 + 90, 176, s=1 - 0.06 * pressed):
                c.drawRRect(rr(-90, -26, 180, 52, 26), G.P(GREEN if done else INK))
                T(c, "Sent" if done else "Approve", 0, 8, sans(21, 650), WHITE, align=0.5)
            c.drawRRect(rr(230, 150, 150, 52, 26), G.P(CARD))
            T(c, "Not now", 305, 184, sans(21, 650), INK, align=0.5)
            if t >= click - 0.9:
                v = out_cubic(clamp((t - (click - 0.9)) / 0.8))
                cursor(c, lerp(w + 80, 128, v), lerp(h + 60, 186, v), pressed=pressed)


RULE_ROWS = [("allow", "read your calendar", GREEN, True), ("ask first", "send an email", BLUE, True),
             ("never", "move money", RED, False)]


def rules(c, t, t0, x, y, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    w, h = 600, 290
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            T(c, "your rules", 30, 50, sans(19, 650), GREY, tracking=0.02)
            for i, (kind, rule, col, on) in enumerate(RULE_ROWS):
                yy = 76 + i * 66
                c.drawRRect(rr(20, yy, w - 40, 54, 14), G.P(CARD))
                T(c, kind, 44, yy + 35, sans(22, 700), col)
                T(c, rule, 180, yy + 35, sans(21, 500), INK)
                v = clamp((t - (t0 + 0.35 + 0.22 * i)) / 0.18)
                v = v if on else 0.0
                tx = w - 92
                c.drawRRect(rr(tx, yy + 13, 56, 28, 14), G.P(G.mixc("#d6d8e0", col, v)))
                c.drawCircle(tx + 14 + 28 * out_cubic(v), yy + 27, 11, G.P(WHITE))
