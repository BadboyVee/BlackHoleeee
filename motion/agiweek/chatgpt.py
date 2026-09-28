"""AGI WEEK, 7.1-10.9 s: ChatGPT.

White, the OpenAI blossom with this week's two releases on top of it; the composer types the question, the
sources are read (Sam Altman, OpenAI DevDay), and the answer streams in: a new model and Agent "O" expected this
week, DevDay tomorrow, the most anticipated event of the week, where there could be even more. AGI?"""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_expo, out_back
from . import marks as M
from .look import (WHITE, T, inter, rr, card, typed, caret, rich, picture, ease_push)
from .score import T_OAI, T_COMPOSER, T_SEND, T_SOURCES, T_ANSWER, T_CLAUDE

INK = "#0d0d0d"
BLUE = "#2f7fe0"
QUESTION = "What is OpenAI launching this week?"


# ---------------------------------------------------------------- the blossom

def blossom(c, t):
    k = t - T_OAI
    pop = out_back(clamp(k / 0.3), 1.6)
    size = 96 * pop * (1 + 0.12 * clamp(k / 1.0))
    M.mark(c, "openai", 960, 540, max(1.0, size), INK, 1.0, rot=12 * clamp(k / 1.0))
    u = out_expo(clamp((k - 0.32) / 0.45))
    if u > 0:
        f = inter(40, 560)
        label = "New model  +  Agent “O”"
        w = f.width(label) + 72
        y = 540 - 150 - 30 * (1 - u)
        c.drawRRect(rr(960 - w / 2, y - 38, w, 76, 38), G.P("#f4f4f4", u))
        c.drawRRect(rr(960 - w / 2 + 1, y - 37, w - 2, 74, 37), G.P("#e3e3e3", u, stroke=2))
        T(c, label, 960, y + f.cap / 2, f, INK, u, align=0.5)


# ---------------------------------------------------------------- the composer

def _globe(c, x, y, r, col):
    p = G.P(col, 1, stroke=3.2)
    c.drawCircle(x, y, r, p)
    c.drawOval(skia.Rect.MakeLTRB(x - r * 0.45, y - r, x + r * 0.45, y + r), p)
    c.drawLine(x - r, y, x + r, y, p)


def composer(c, t):
    s = ease_push(t, T_COMPOSER, T_SOURCES, 0.05)
    with G.xf(c, 960, 540, s=s):
        c.translate(-960, -540)
        card(c, 150, 378, 1620, 324, 84, WHITE, shadow=0.06, lift=12, blur=34, border=("#e3e3e3", 1.0, 2))
        f = inter(42, 430)
        text = typed(QUESTION, t, T_COMPOSER + 0.05, cps=38)
        T(c, text, 221, 480, f, INK)
        if t < T_SEND:
            caret(c, 221 + f.width(text) + 4, 488, 50, t, INK)
        # the bottom row: attach, web search, the sources, the mic, send
        fp = inter(64, 300)
        T(c, "+", 241, 640, fp, INK, align=0.5)
        _globe(c, 368, 616, 20, BLUE)
        T(c, "Web search", 404, 630, inter(38, 480), BLUE)
        for k, name in enumerate(("openai", "x")):
            cx = 690 + k * 44
            c.drawCircle(cx, 616, 24, G.P("#f2f2f2"))
            c.drawCircle(cx, 616, 24, G.P("#e0e0e0", 1, stroke=2))
            M.mark(c, name, cx, 616, 26, INK)
        c.drawCircle(806, 616, 24, G.P("#f2f2f2"))
        T(c, "2", 806, 630, inter(34, 520), INK, align=0.5)
        p = G.P(INK, 1, stroke=3.4, cap="round")
        c.drawLine(848, 610, 858, 620, p)
        c.drawLine(858, 620, 868, 610, p)
        c.drawRRect(rr(1497, 592, 22, 38, 11), G.P(INK, 1, stroke=3.2))
        c.drawPath(G.arc_path(1508, 614, 20, 20, 140), G.P(INK, 1, stroke=3.2))
        c.drawLine(1508, 634, 1508, 644, p)
        press = math.exp(-max(0.0, t - T_SEND) / 0.08) if t >= T_SEND else 0.0
        r = 55 * (1 - 0.12 * press)
        c.drawCircle(1666, 616, r, G.P(INK))
        pa = G.P(WHITE, 1, stroke=5, cap="round", join="round")
        c.drawLine(1666, 636, 1666, 596, pa)
        c.drawLine(1650, 612, 1666, 596, pa)
        c.drawLine(1682, 612, 1666, 596, pa)


# ---------------------------------------------------------------- the sources

SOURCES = [("altman", "Sam Altman", "Co-founder & CEO"), ("openai", "OpenAI", "DevDay · Tomorrow")]


def _icon(c, what, x, y, r):
    if what in ("altman", "amodei", "hassabis", "zuckerberg", "musk"):
        picture(c, what, x - r, y - r, 2 * r, 2 * r, r, which="face")
    else:
        M.mark(c, what, x, y, r * 1.6, INK)


def sources(c, t):
    s = ease_push(t, T_SOURCES, T_ANSWER + 0.2, 0.05)
    with G.xf(c, 960, 540, s=s):
        c.translate(-960, -540)
        f = inter(62, 430)
        head = "Reading "
        names = "Sam Altman, OpenAI"
        x = 280
        T(c, head, x, 452, f, "#9a9a9a")
        x2 = x + f.width(head)
        T(c, names, x2, 452, f, "#3a3a3a")
        # a shimmer runs along the line while it reads
        k = ((t - T_SOURCES) / 0.5) % 1.0
        sx = lerp(x - 200, x2 + f.width(names) + 200, k)
        sh = G.linear_grad(sx - 160, 0, sx + 160, 0, [WHITE, WHITE, WHITE], alphas=[0.0, 0.75, 0.0])
        T(c, head + names, x, 452, f, WHITE, shader=sh)
        p = G.P("#9a9a9a", 1, stroke=4, cap="round")
        xe = x2 + f.width(names) + 34
        c.drawLine(xe, 418, xe + 14, 434, p)
        c.drawLine(xe + 14, 434, xe, 450, p)
        for k, (icon, src, title) in enumerate(SOURCES):
            u = out_expo(clamp((t - T_SOURCES - 0.06 - 0.07 * k) / 0.35))
            if u <= 0:
                continue
            cx = 280 + k * 690
            with G.xf(c, 0, 30 * (1 - u)):
                card(c, cx, 552, 650, 258, 40, WHITE, u, shadow=0.04, lift=8, blur=20, border=("#ececec", 1.0, 2))
                _icon(c, icon, cx + 76, 628, 26)
                T(c, src, cx + 122, 642, inter(40, 430), "#6b6b6b", u)
                T(c, title, cx + 56, 730, inter(50, 460), INK, u)


# ---------------------------------------------------------------- the answer

ANSWER_1 = [("A ", False), ("new model", True), (" and ", False), ("Agent “O”", True),
            (" are expected from OpenAI this week.", False)]
ANSWER_2 = [("The week's most anticipated event. We could see ", False),
            ("even more announcements and releases.", True), (" (AGI?)", True)]
ROW = [("altman", "Sam Altman", "Co-founder & CEO"), ("openai", "OpenAI", "DevDay"), ("x", "X", "Posts")]


def answer(c, t):
    k = t - T_ANSWER
    scroll = 170 * out_cubic(clamp(k / 1.0))
    s = ease_push(t, T_ANSWER, T_CLAUDE + 0.3, 0.04)
    with G.xf(c, 960, 540, s=s):
        c.translate(-960, -540 - scroll)
        fq = inter(40, 430)
        bw = fq.width(QUESTION) + 76
        card(c, 1740 - bw, 70, bw, 92, 46, "#f3f3f3", shadow=0.0)
        T(c, QUESTION, 1740 - bw + 38, 130, fq, INK)
        T(c, "Thought for 31s", 190, 262, inter(44, 430), "#8a8a8a")
        p = G.P("#8a8a8a", 1, stroke=3.4, cap="round")
        c.drawLine(528, 238, 538, 248, p)
        c.drawLine(538, 248, 528, 258, p)
        for j, (icon, src, title) in enumerate(ROW):
            u = clamp((k - 0.05 * j) / 0.2)
            if u <= 0:
                continue
            x = 190 + j * 420
            _icon(c, icon, x + 22, 352, 18)
            T(c, src, x + 52, 364, inter(36, 430), "#6b6b6b", u)
            T(c, title, x + 6, 424, inter(42, 460), INK, u)
            if j:
                c.drawLine(x - 30, 330, x - 30, 440, G.P("#ececec", u, stroke=2))
        u = clamp((k - 0.15) / 0.2)
        if u > 0:
            x = 190 + 3 * 420
            for m, name in enumerate(("openai", "x", "claude")):
                M.mark(c, name, x + 22 + m * 40, 352, 30, INK if name != "claude" else "#d97757", u)
            T(c, "24 sources", x + 6, 424, inter(42, 460), INK, u)
        reg, bold = inter(46, 430), inter(46, 640)
        n = int(max(0.0, k - 0.1) * 240)
        y = rich(c, ANSWER_1, 190, 570, reg, bold, INK, 1520, 70, upto=n)
        n2 = n - 64
        if n2 > 0:
            T(c, "DevDay is tomorrow", 190, y + 130, inter(62, 640), INK, clamp(n2 / 8))
            rich(c, ANSWER_2, 190, y + 216, reg, bold, INK, 1520, 70, upto=max(0, n2 - 10))
