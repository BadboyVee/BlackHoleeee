"""AGI WEEK, 14.8-20.8 s: Grok, and the end.

On black the Grok wordmark comes up out of the dark with 4.8 on top of it, the input bar takes the question
(is Grok 4.8 dropping this week?), a laptop shows the whole week in a terminal, and Grok answers: 4.8 might drop,
expected after 4.7's bad reviews; Sonnet 5.5 today, DevDay tomorrow, the IPO planned for November; with Elon
Musk's card beside it. Then everything goes dark: Big week ahead., signed MADE BY VEEE."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_expo, out_back, in_out_cubic
from . import marks as M
from .look import WHITE, F, T, gs, gsm, inter, mono, rr, typed, caret, rich, picture, ease_push, blob
from .score import T_GROK, T_INPUT, T_LAPTOP, T_ANSWER2, T_OUT, T_END, T_CREDIT, DURATION

QUESTION = "is Grok 4.8 dropping this week?"


def lockup(c, cx, cy, s=1.0, a=1.0, col=WHITE):
    """The Grok wordmark: the mark and the name."""
    f = gsm(150 * s)
    ms = f.cap * 1.75
    gap = f.size * 0.14
    total = ms + gap + f.width("Grok")
    x0 = cx - total / 2
    M.grok(c, x0 + ms / 2, cy, ms, col, a)
    T(c, "Grok", x0 + ms + gap, cy + f.cap / 2, f, col, a)
    return f


def pill(c, cx, y, label, a=1.0):
    fm = gsm(46)
    w = fm.width(label) + 64
    c.drawRRect(rr(cx - w / 2, y, w, 80, 40), G.P(WHITE, 0.1 * a))
    c.drawRRect(rr(cx - w / 2 + 1, y + 1, w - 2, 78, 39), G.P(WHITE, 0.28 * a, stroke=2))
    T(c, label, cx, y + 40 + fm.cap / 2, fm, WHITE, 0.92 * a, align=0.5)


def input_bar(c, x, y, w, h, t, text="", placeholder=True, a=1.0):
    c.drawRRect(rr(x, y, w, h, h / 2), G.P("#1b1b1d", a))
    c.drawRRect(rr(x + 1, y + 1, w - 2, h - 2, h / 2 - 1), G.P("#2c2c30", a, stroke=2))
    cy = y + h / 2
    p = G.P(WHITE, a, stroke=4, cap="round")
    c.drawLine(x + 58, cy - 16, x + 58, cy + 16, p)
    c.drawLine(x + 42, cy, x + 74, cy, p)
    f = gs(h * 0.34)
    if text:
        T(c, text, x + 118, cy + f.cap / 2, f, "#d6d6d8", a)
    elif placeholder:
        T(c, "Ask anything or type @ to search your apps", x + 118, cy + f.cap / 2, f, "#77777c", a)
    fa = gsm(h * 0.25)
    T(c, "Auto", x + w - 330, cy + fa.cap / 2, fa, WHITE, 0.9 * a)
    c.drawCircle(x + w - 240, cy, h * 0.1, G.P(WHITE, 0.8 * a, stroke=2.5))
    c.drawCircle(x + w - 240, cy, h * 0.035, G.P(WHITE, 0.8 * a))
    pc = G.P(WHITE, 0.7 * a, stroke=3, cap="round")
    c.drawLine(x + w - 206, cy - 4, x + w - 198, cy + 4, pc)
    c.drawLine(x + w - 198, cy + 4, x + w - 190, cy - 4, pc)
    c.drawRRect(rr(x + w - 158, cy - 18, 16, 28, 8), G.P(WHITE, 0.8 * a, stroke=2.6))
    c.drawPath(G.arc_path(x + w - 150, cy - 2, 15, 20, 140), G.P(WHITE, 0.8 * a, stroke=2.6))
    r = h * 0.36
    bx = x + w - h / 2 - 6
    c.drawCircle(bx, cy, r, G.P(WHITE, a))
    for i, hh in enumerate((0.35, 0.7, 1.0, 0.6, 0.3)):
        lvl = hh * (0.7 + 0.3 * math.sin(t * 9 + i))
        c.drawLine(bx - 16 + i * 8, cy - r * 0.45 * lvl, bx - 16 + i * 8, cy + r * 0.45 * lvl,
                   G.P("#111111", a, stroke=4, cap="round"))


# ---------------------------------------------------------------- the wordmark, then the question

def wordmark_and_input(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#000000"))
    k = t - T_GROK
    up = out_cubic(clamp((t - T_INPUT) / 0.4))
    grey = clamp(k / 0.6)
    col = G.mixc("#3a3a3a", WHITE, grey)
    s = lerp(0.96, 1.0, out_cubic(clamp(k / 0.8)))
    zoom = 1.0
    if t >= T_INPUT:
        zoom = lerp(1.0, 1.32, out_cubic(clamp((t - T_INPUT - 0.2) / 0.8)))
    with G.xf(c, 660, 540, s=zoom):
        c.translate(-660, -540)
        lockup(c, 960, lerp(540, 300, up), s * lerp(1.0, 0.8, up), 1.0, col)
        v = out_expo(clamp((t - (T_GROK + 0.5)) / 0.35))
        if v > 0 and up < 1:
            pill(c, 960, lerp(540, 300, up) - 210 + 20 * (1 - v), "4.8 · this week?", v * (1 - up))
        if t >= T_INPUT:
            a = clamp((t - T_INPUT) / 0.2)
            text = typed("@X " + QUESTION, t, T_INPUT + 0.12, cps=56)
            input_bar(c, 185, 466 + 30 * (1 - a), 1550, 132, t, text, True, a)
            if text:
                f = gs(132 * 0.34)
                tw = f.width(text)
                if len(text) >= len("@X " + QUESTION):
                    M.mark(c, "x", 185 + 118 + tw + 34, 532, 30, WHITE, a)
                caret(c, 185 + 118 + tw + 6, 550, 42, t, WHITE, a)


# ---------------------------------------------------------------- the week, in a terminal

ROWS = [("Sonnet 5.5", "expected today · a Fable moment?"), ("New OpenAI model", "+ Agent “O”"),
        ("OpenAI DevDay", "tomorrow · (AGI?)"), ("Grok 4.8", "might drop · after 4.7’s bad reviews"),
        ("Anthropic IPO", "planned for November")]


def laptop(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#2a2a2c", 1, shader=G.linear_grad(0, 0, 0, 1080, [
        "#57575b", "#2b2b2e", "#161618"])))
    blob(c, 960, 120, 900, "#8a8a90", 0.25)
    s = ease_push(t, T_LAPTOP, T_ANSWER2, 0.07)
    with G.xf(c, 960, 520, s=s):
        c.translate(-960, -520)
        c.concat(G.perspective(960, 480, rx=6, ry=0, D=2600))
        c.drawRRect(rr(290, 46, 1340, 830, 30), G.P("#000000", 0.45, blur=40))
        c.drawRRect(rr(300, 40, 1320, 820, 28), G.P("#0b0b0c"))
        c.drawRRect(rr(300, 40, 1320, 820, 28), G.P("#3a3a3e", 1, stroke=3))
        c.drawRRect(rr(330, 70, 1260, 760, 10), G.P("#141416"))
        c.drawPath(G.poly([(240, 870), (1680, 870), (1760, 930), (160, 930)]), G.P("#3b3b3f"))
        c.drawRect(skia.Rect.MakeLTRB(160, 930, 1760, 944), G.P("#232326"))
        f = mono(24, 420)
        fb = mono(24, 620)
        T(c, "●", 370, 126, f, "#7ee787")
        T(c, "grok  ·  this week in AI", 400, 126, f, "#9a9aa0")
        T(c, "week 40", 1550, 126, f, "#9a9aa0", align=1.0)
        c.drawLine(360, 150, 1560, 150, G.P("#2e2e33", 1, stroke=2))
        T(c, "What's coming this week?", 370, 214, fb, WHITE)
        k = t - T_LAPTOP
        sel = min(3, int(max(0.0, k - 0.18) / 0.14))
        for i, (name, note) in enumerate(ROWS):
            y = 290 + i * 70
            u = clamp((k - 0.05 * i) / 0.18)
            if u <= 0:
                continue
            if i == sel:
                c.drawRRect(rr(360, y - 44, 1200, 62, 8), G.P("#26262a", u))
                T(c, "▶", 372, y, f, WHITE, u)
            col = WHITE if i == sel else "#a8a8ae"
            T(c, f"{i + 1}", 410, y, f, "#6f6f76", u)
            T(c, name, 460, y, fb if i == sel else f, col, u)
            T(c, note, 800, y, f, col, u)
        T(c, "↑/↓ navigate  ·  enter select  ·  esc cancel", 370, 700, f, "#6f6f76")
        c.drawRect(skia.Rect.MakeLTRB(330, 70, 1590, 830), G.P(WHITE, 1, shader=G.linear_grad(
            330, 70, 1590, 830, [WHITE, WHITE], alphas=[0.05, 0.0])))


# ---------------------------------------------------------------- the answer

ANSWER = [[("Grok 4.8 might drop this week,", True)],
          [("expected after ", False), ("4.7’s bad reviews.", True)],
          [("1) ", False), ("Sonnet 5.5", True), (": expected today", False)],
          [("2) ", False), ("OpenAI DevDay", True), (": tomorrow (AGI?)", False)],
          [("3) ", False), ("Anthropic IPO", True), (": planned for November", False)]]


def answer(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#000000"))
    s = ease_push(t, T_ANSWER2, T_OUT + 0.3, 0.04)
    k = t - T_ANSWER2
    with G.xf(c, 960, 540, s=s):
        c.translate(-960, -540)
        lockup(c, 960, 150, 0.52)
        input_bar(c, 200, 238, 1520, 100, t, "", placeholder=False)
        fq = gs(36)
        bw = fq.width(QUESTION) + 120
        c.drawRRect(rr(1700 - bw, 380, bw, 76, 38), G.P("#1c1c1e"))
        c.drawRRect(rr(1700 - bw + 1, 381, bw - 2, 74, 37), G.P("#2c2c30", 1, stroke=2))
        M.mark(c, "x", 1700 - bw + 44, 418, 28, WHITE)
        T(c, QUESTION, 1700 - bw + 76, 418 + fq.cap / 2, fq, "#e8e8ea")
        fg = gs(30)
        c.drawCircle(300, 510, 9, G.P("#8a8a90", 1, stroke=2.4))
        c.drawLine(296, 524, 304, 524, G.P("#8a8a90", 1, stroke=2.4))
        T(c, "Thought for 6s", 322, 510 + fg.cap / 2, fg, "#8a8a90")
        reg, bold = gs(40), gsm(40)
        for i, line in enumerate(ANSWER):
            u = out_expo(clamp((k - 0.12 - 0.09 * i) / 0.25))
            if u <= 0:
                break
            rich(c, line, 290, 590 + 58 * i + 16 * (1 - u), reg, bold, WHITE, 1000, 58, a=u)
        v = out_expo(clamp((k - 0.3) / 0.45))
        if v > 0:
            with G.xf(c, 0, 40 * (1 - v)):
                c.drawRRect(rr(1360, 552, 330, 380, 22), G.P("#000000", 0.5 * v, blur=20))
                picture(c, "musk", 1360, 540, 330, 330, 22, a=v)
                T(c, "Elon Musk", 1364, 912, gsm(34), WHITE, v)
                T(c, "Founder · xAI & SpaceX", 1364, 952, gs(26), "#9a9aa0", v)


def end(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#000000"))
    u = out_expo(clamp((t - T_END) / 0.5))
    if u <= 0:
        return
    f = gsm(128)
    s = lerp(0.94, 1.0, u) + 0.02 * clamp((t - T_END) / (DURATION - T_END))
    up = in_out_cubic(clamp((t - T_CREDIT) / 0.45))
    with G.xf(c, 960, lerp(540, 430, up), s=s):
        T(c, "Big week ahead.", 0, f.cap / 2 + 30 * (1 - u), f, WHITE, u, align=0.5)
    credit(c, t)


def credit(c, t):
    """The maker's mark, as it signs every film of Veee's: MADE BY in small tracked caps, then VEEE, each letter
    popping in, and a band of light across it."""
    v = clamp((t - T_CREDIT - 0.12) / 0.4)
    if v <= 0:
        return
    fm = inter(30, 620)
    T(c, "MADE BY", 960, 612 + 16 * (1 - out_cubic(v)), fm, "#8e8e93", v, align=0.5, tracking=0.5)
    fv = F("archivo", 150, wght=850, wdth=118)
    run = fv.shape("VEEE")
    x0 = 960 - run.width / 2
    base = 790

    def word(cc):
        for i, gid, gx, adv in run.glyphs():
            k = clamp((t - T_CREDIT - 0.2 - 0.07 * i) / 0.35)
            if k <= 0:
                continue
            with G.xf(cc, x0 + gx + adv / 2, base, s=out_back(k, 1.4)):
                G.glyph(cc, fv, gid, -adv / 2, 0, G.P(WHITE, 0.35 * k, blur=18))
                G.glyph(cc, fv, gid, -adv / 2, 0, G.P(WHITE, k))

    su = (t - T_CREDIT - 0.6) / 0.7
    if 0 < su < 1:
        G.light_sweep(c, word, x0 - 200, x0 + run.width + 200, base - 60, su, colors=("#9fb4ff", "#ffffff"),
                      width=150, angle=22.0, strength=0.8)
    else:
        word(c)


def grok(c, t):
    if t < T_LAPTOP:
        wordmark_and_input(c, t)
    elif t < T_ANSWER2:
        laptop(c, t)
    elif t < T_END:
        answer(c, t)
        k = clamp((t - T_OUT) / (T_END - 0.08 - T_OUT))
        if k > 0:
            c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#000000", k))
    else:
        end(c, t)
