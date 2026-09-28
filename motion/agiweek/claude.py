"""AGI WEEK, 10.6-14.8 s: Claude.

Cream, the spark turning in the middle; it slides aside as Claude types itself in, and Sonnet 5.5 lands on top,
expected today. A wall of canvases passes: the model card, Dario and Daniela Amodei, a Fable moment?, the IPO
planned for November, a chart of who stays on top. The camera settles on one canvas where a phone prototype is
being designed for Sonnet 5.5, zooms into the toolbar, and the cursor clicks Comment: IPO planned for November.
Staying on top."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_expo, out_back, in_out_cubic
from . import marks as M
from .look import (WHITE, CLAY, CREAM, INK, F, T, inter, serif, rr, card, picture, ease_push)
from .score import T_SPARK, T_WORDMARK, T_GRID, T_CANVAS, T_SWATCH, T_TOOLBAR, T_CLICK

SPARK = "#da7556"
PAPER = "#faf9f5"
LINE = "#e3ddd1"
MUTED = "#8b857a"


# ---------------------------------------------------------------- the spark and the name

def spark(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P(CREAM))
    f = serif(122, 560)
    word = "Claude"
    k = t - T_SPARK
    if k <= 0:
        return
    rot = 150 * k
    if t < T_WORDMARK:
        size = 84 * out_back(clamp(k / 0.3), 1.8)
        M.mark(c, "claude", 960, 540, max(1.0, size), SPARK, 1.0, rot=rot)
        return
    u = out_cubic(clamp((t - T_WORDMARK) / 0.3))
    ms = lerp(84, f.cap * 1.62, u)
    gap = f.size * 0.1
    total = f.cap * 1.62 + gap + f.width(word)
    x0 = 960 - total / 2
    sx = lerp(960, x0 + f.cap * 0.81, u)
    M.mark(c, "claude", sx, 540, ms, SPARK, 1.0, rot=rot)
    run = f.shape(word)
    tx = x0 + f.cap * 1.62 + gap
    for i, gid, gx, adv in run.glyphs():
        v = clamp((t - T_WORDMARK - 0.08 - 0.06 * i) / 0.12)
        if v <= 0:
            continue
        G.glyph(c, f, gid, tx + gx, 540 + f.cap / 2, G.P(G.mixc("#bdb8ae", INK, v), 1))
    v = out_expo(clamp((t - (T_WORDMARK + 0.36)) / 0.35))
    if v > 0:
        fm = serif(50, 520)
        label = "Sonnet 5.5"
        w = fm.width(label) + 70
        y = 540 - f.cap / 2 - 150 + 24 * (1 - v)
        c.drawRRect(rr(960 - w / 2, y, w, 84, 42), G.P(WHITE, 0.8 * v))
        c.drawRRect(rr(960 - w / 2 + 1, y + 1, w - 2, 82, 41), G.P(LINE, v, stroke=2))
        T(c, label, 960, y + 42 + fm.cap / 2, fm, INK, v, align=0.5)


# ---------------------------------------------------------------- windows

def chrome(c, x, y, w, h, title="Let's prototype…", file="Sonnet 5.5 launch.html", s=1.0):
    """A Claude window: paper, a hairline, the top bar with its tabs and buttons."""
    c.drawRRect(rr(x, y + 10 * s, w, h, 16 * s), G.P("#000000", 0.07, blur=26 * s))
    c.drawRRect(rr(x, y, w, h, 16 * s), G.P(PAPER))
    c.drawRRect(rr(x, y, w, h, 16 * s), G.P(LINE, 1, stroke=1.5 * s))
    f = inter(15 * s, 560)
    c.drawRRect(rr(x + 12 * s, y + 10 * s, 150 * s, 30 * s, 8 * s), G.P(WHITE))
    T(c, title, x + 24 * s, y + 30 * s, f, INK)
    T(c, "Project", x + 230 * s, y + 30 * s, inter(15 * s, 460), MUTED)
    c.drawRRect(rr(x + 300 * s, y + 10 * s, 190 * s, 30 * s, 8 * s), G.P(WHITE))
    T(c, file, x + 314 * s, y + 30 * s, f, INK)
    c.drawRRect(rr(x + w - 150 * s, y + 12 * s, 64 * s, 26 * s, 7 * s), G.P(WHITE))
    T(c, "Share", x + w - 140 * s, y + 30 * s, inter(13 * s, 520), INK)
    c.drawRRect(rr(x + w - 80 * s, y + 12 * s, 58 * s, 26 * s, 7 * s), G.P(INK))
    T(c, "Export", x + w - 72 * s, y + 30 * s, inter(13 * s, 560), WHITE)


def lines(c, x, y, w, n, s=1.0, col="#e6e0d4", gap=22.0):
    for i in range(n):
        ww = w * (0.55 + 0.45 * ((i * 37) % 10) / 10)
        c.drawRRect(rr(x, y + i * gap * s, ww, 9 * s, 4.5 * s), G.P(col))


def pane(c, x, y, w, h, kind, t, s=1.0):
    """One canvas on the wall."""
    chrome(c, x, y, w, h, s=s)
    lines(c, x + 20 * s, y + 70 * s, 220 * s, 10, s)
    cx, cy, cw, ch = x + 270 * s, y + 56 * s, w - 290 * s, h - 76 * s
    c.drawRRect(rr(cx, cy, cw, ch, 12 * s), G.P("#f2efe8"))
    mx, my = cx + cw / 2, cy + ch / 2
    if kind == "model":
        M.mark(c, "claude", mx, my - 90 * s, 64 * s, SPARK)
        T(c, "Sonnet 5.5", mx, my + 10 * s, serif(64 * s, 560), INK, align=0.5)
        f = inter(20 * s, 600)
        w2 = f.width("EXPECTED TODAY", 0.1) + 40 * s
        c.drawRRect(rr(mx - w2 / 2, my + 44 * s, w2, 40 * s, 20 * s), G.P(CLAY))
        T(c, "EXPECTED TODAY", mx, my + 71 * s, f, WHITE, align=0.5, tracking=0.1)
    elif kind == "founders":
        picture(c, "amodei", cx + 20 * s, cy + 20 * s, cw - 40 * s, ch - 110 * s, 12 * s)
        T(c, "Dario & Daniela Amodei", cx + 24 * s, cy + ch - 52 * s, serif(30 * s, 560), INK)
        T(c, "Co-founders · Anthropic", cx + 24 * s, cy + ch - 20 * s, inter(18 * s, 460), MUTED)
    elif kind == "quote":
        c.drawRRect(rr(cx, cy, cw, ch, 12 * s), G.P(WHITE))
        T(c, "“A Fable moment?”", mx, my + 10 * s, _italic(56 * s), INK, align=0.5)
        T(c, "SONNET 5.5 · EXPECTED TODAY", mx, my + 64 * s, inter(16 * s, 560), MUTED, align=0.5, tracking=0.14)
    elif kind == "ipo":
        c.drawRRect(rr(mx - 120 * s, my - 130 * s, 240 * s, 220 * s, 22 * s), G.P(WHITE))
        c.drawRRect(rr(mx - 120 * s, my - 130 * s, 240 * s, 64 * s, 22 * s), G.P(CLAY))
        c.drawRect(skia.Rect.MakeXYWH(mx - 120 * s, my - 96 * s, 240 * s, 30 * s), G.P(CLAY))
        T(c, "IPO", mx, my - 84 * s, inter(30 * s, 640), WHITE, align=0.5, tracking=0.1)
        T(c, "NOV", mx, my + 50 * s, serif(92 * s, 600), INK, align=0.5)
        T(c, "Planned for November", mx, my + 130 * s, inter(22 * s, 520), INK, align=0.5)
    elif kind == "chart":
        T(c, "Staying on top", cx + 30 * s, cy + 54 * s, serif(36 * s, 560), INK)
        hs = [0.95, 0.62, 0.55, 0.44, 0.38]
        for i, hh in enumerate(hs):
            bx = cx + 40 * s + i * (cw - 80 * s) / 5
            bh = (ch - 130 * s) * hh
            c.drawRRect(rr(bx, cy + ch - 30 * s - bh, (cw - 80 * s) / 5 - 18 * s, bh, 8 * s),
                        G.P(CLAY if i == 0 else "#d9d2c4"))
    elif kind == "dark":
        c.drawRRect(rr(cx, cy, cw, ch, 12 * s), G.P("#1f1e1c"))
        c.drawCircle(mx, my, 120 * s, G.P(SPARK, 0.35, blur=50 * s, blend=G.ADD))
        M.mark(c, "claude", mx, my, 150 * s, SPARK, rot=20 * t)
    elif kind == "canvas":
        k = (ch - 50 * s) / 740
        prototype(c, mx - 170 * k, cy + 25 * s, 340 * k, 740 * k, t, k)
    else:
        lines(c, cx + 30 * s, cy + 40 * s, cw - 60 * s, 12, s, "#e3ddd0", 30)


def _italic(size):
    return F("fraunces-italic", size, wght=380, opsz=144, SOFT=0, WONK=0)


WALL = [["dark", "model", "quote"], ["founders", "canvas", "chart"], ["text", "ipo", "text"]]
PW, PH, GAP = 900, 560, 44


def grid(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#ece8df"))
    u = in_out_cubic(clamp((t - T_GRID) / (T_CANVAS - T_GRID)))
    s = lerp(0.66, 1.02, u)
    ox, oy = lerp(-360, 0, u), lerp(-240, 0, u)
    with G.xf(c, 960 + ox, 540 + oy, s=s):
        for r, row in enumerate(WALL):
            for k, kind in enumerate(row):
                x = (k - 1) * (PW + GAP) - PW / 2
                y = (r - 1) * (PH + GAP) - PH / 2
                pane(c, x, y, PW, PH, kind, t)


# ---------------------------------------------------------------- the canvas

WIN = (150.0, 64.0, 1640.0, 960.0)
SWATCHES = [("Stone", "#e6e1d8"), ("Moss", "#b9c9a3"), ("Mist", "#d9d6d0"), ("Clay", "#d97757"),
            ("Dusk", "#c3b5dc"), ("Sakura", "#e8b4b8"), ("Ink", "#a9a9a9")]
TOOLS = [("Comment", 828.0, 104.0), ("Edit text", 942.0, 104.0), ("Knobs", 1056.0, 86.0), ("Draw", 1152.0, 74.0)]


def prototype(c, x, y, w, h, t, s=1.0, accent=None):
    """The phone being designed: Sonnet 5.5's launch screen."""
    c.drawRRect(rr(x, y, w, h, 40 * s), G.P("#fbfaf7"))
    c.drawRRect(rr(x, y, w, h, 40 * s), G.P("#e4dfd5", 1, stroke=2 * s))
    c.drawRRect(rr(x + w / 2 - 36 * s, y + 14 * s, 72 * s, 22 * s, 11 * s), G.P("#0c0c0c"))
    T(c, "9:41", x + 34 * s, y + 32 * s, inter(15 * s, 600), INK)
    T(c, "GOOD MORNING", x + 24 * s, y + 80 * s, inter(11 * s, 600), MUTED, tracking=0.14)
    T(c, "Sonnet 5.5", x + 24 * s, y + 116 * s, serif(30 * s, 560), INK)
    col = accent or "#ece6db"
    c.drawRRect(rr(x + 20 * s, y + 140 * s, w - 40 * s, 84 * s, 12 * s), G.P(col))
    T(c, "EXPECTED TODAY", x + 34 * s, y + 166 * s, inter(10 * s, 600), INK if not accent else WHITE,
      tracking=0.14)
    T(c, "A big step up. A Fable moment?", x + 34 * s, y + 196 * s, _italic(14 * s), INK if not accent else WHITE)
    T(c, "Continue", x + 24 * s, y + 262 * s, inter(13 * s, 600), INK)
    c.drawRRect(rr(x + 20 * s, y + 276 * s, w - 40 * s, 120 * s, 14 * s), G.P("#cfc6b6"))
    T(c, "IPO · November", x + 36 * s, y + 330 * s, inter(20 * s, 500), INK)
    T(c, "Explore", x + 24 * s, y + 432 * s, inter(13 * s, 600), INK)
    for i in range(3):
        c.drawRRect(rr(x + 20 * s + i * (w - 40 * s) / 3, y + 446 * s, (w - 40 * s) / 3 - 10 * s, 70 * s, 12 * s),
                    G.P("#f0ece4"))


def canvas_ui(c, t, commented=0.0):
    """The Claude canvas at full frame: chat on the left, the prototype, the tweaks, the toolbar."""
    x, y, w, h = WIN
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#ece8df"))
    chrome(c, x, y, w, h)
    # the chat
    T(c, "You", x + 22, y + 88, inter(16, 640), INK)
    T(c, "Prototype a launch screen for Sonnet 5.5.", x + 22, y + 112, inter(15, 430), MUTED)
    T(c, "Keep it calm, warm, and clean.", x + 22, y + 134, inter(15, 430), MUTED)
    T(c, "Claude", x + 22, y + 178, inter(16, 640), INK)
    items = ["Read, Write ×3", "Plan", "write_file", "Progress 5/5"]
    for i, it in enumerate(items):
        c.drawRRect(rr(x + 16, y + 194 + i * 40, 318, 32, 7), G.P("#efebe3"))
        T(c, it, x + 44, y + 216 + i * 40, inter(14, 480), INK)
    for i in range(5):
        c.drawRRect(rr(x + 22, y + 362 + i * 26, 14, 14, 3), G.P("#9d978c"))
        c.drawRRect(rr(x + 46, y + 366 + i * 26, 220 - (i * 23) % 70, 7, 3.5), G.P("#d7d0c3"))
    for i, it in enumerate(["launch.jsx", "card.jsx", "Verifier"]):
        c.drawRRect(rr(x + 16, y + 506 + i * 40, 318, 32, 7), G.P("#efebe3"))
        T(c, it, x + 44, y + 528 + i * 40, inter(14, 480), INK)
    c.drawRRect(rr(x + 14, y + h - 120, 322, 104, 12), G.P(WHITE))
    T(c, "Describe what you want to create…", x + 30, y + h - 84, inter(14, 430), MUTED)
    T(c, "Import", x + 150, y + h - 36, inter(14, 560), INK)
    c.drawRRect(rr(x + 262, y + h - 56, 60, 30, 7), G.P("#e9a28c"))
    T(c, "Send", x + 274, y + h - 36, inter(14, 560), WHITE)
    c.drawLine(x + 350, y + 50, x + 350, y + h, G.P(LINE, 1, stroke=1.5))
    # the toolbar
    ty = 145.0
    c.drawRect(skia.Rect.MakeLTRB(x + 351, y + 50, x + w, y + 108), G.P(WHITE))
    c.drawRRect(rr(700, ty - 18, 104, 36, 8), G.P("#e9e2d6"))
    T(c, "Tweaks", 712, ty + 6, inter(15, 560), INK)
    c.drawRRect(rr(766, ty - 11, 34, 22, 11), G.P(INK))
    c.drawCircle(789, ty, 8, G.P(WHITE))
    c.drawLine(815, ty - 14, 815, ty + 14, G.P(LINE, 1, stroke=1.5))
    for k, (label, tx, tw) in enumerate(TOOLS):
        on = commented if k == 0 else 0.0
        fill = G.mixc(WHITE, CLAY, on)
        c.drawRRect(rr(tx, ty - 18, tw, 36, 8), G.P(fill))
        c.drawRRect(rr(tx + 0.5, ty - 17.5, tw - 1, 35, 8), G.P(G.mixc(LINE, CLAY, on), 1, stroke=1.4))
        tc = G.mixc(INK, WHITE, on)
        if k == 0:
            c.drawPath(_bubble(tx + 16, ty, 8), G.P(tc, 1, stroke=1.6))
        else:
            c.drawCircle(tx + 16, ty, 6, G.P(G.mixc(MUTED, WHITE, on), 1, stroke=1.6))
        T(c, label, tx + 30, ty + 6, inter(15, 520), tc)
    T(c, "100%", 1250, ty + 6, inter(14, 480), MUTED)
    # the prototype and the tweaks
    picked = clamp((t - T_SWATCH) / 0.2)
    accent = None if picked <= 0 else G.mixc("#ece6db", CLAY, picked)
    prototype(c, 972, 236, 340, 740, t, 1.0, accent=accent)
    card(c, 1418, 190, 346, 262, 16, WHITE, shadow=0.06, lift=10, blur=24)
    T(c, "TWEAKS", 1440, 226, inter(14, 640), MUTED, tracking=0.16)
    T(c, "THEME", 1440, 262, inter(12, 640), MUTED, tracking=0.16)
    for i, (name, col) in enumerate(SWATCHES):
        sx = 1440 + i * 44
        c.drawRRect(rr(sx, 274, 36, 36, 9), G.P(col))
        if (i == 3 and picked > 0) or (i == 0 and picked <= 0):
            c.drawRRect(rr(sx - 3, 271, 42, 42, 11), G.P(INK, 1, stroke=2))
        T(c, name, sx + 18, 326, inter(9, 480), MUTED, align=0.5)
    T(c, "TYPOGRAPHY", 1440, 360, inter(12, 640), MUTED, tracking=0.16)
    for i, (lab, val) in enumerate((("Heading size", "100%"), ("Body size", "100%"))):
        T(c, lab, 1440, 392 + i * 34, inter(13, 520), INK)
        T(c, val, 1742, 392 + i * 34, inter(13, 520), INK, align=1.0)
        c.drawRRect(rr(1440, 400 + i * 34, 300, 4, 2), G.P("#e6dfd3"))
        c.drawRRect(rr(1440, 400 + i * 34, 180, 4, 2), G.P("#b6ab98"))


def _bubble(x, y, r):
    p = skia.Path()
    p.addCircle(x, y, r)
    p.moveTo(x - r * 0.5, y + r * 0.85)
    p.lineTo(x - r * 0.95, y + r * 1.25)
    return p


def arrow(c, x, y, s=1.0, press=0.0):
    pts = [(0, 0), (0, 26), (6.5, 20), (11, 30.5), (15, 28.8), (10.6, 18.6), (19, 18.6)]
    k = 1.4 * s * (1 - 0.12 * press)
    path = G.poly([(px * k, py * k) for px, py in pts])
    with G.xf(c, x, y):
        with G.xf(c, 2, 4):
            c.drawPath(path, G.P("#000000", 0.25, blur=3))
        c.drawPath(path, G.P(WHITE, 1, stroke=4 * s, join="round"))
        c.drawPath(path, G.P(INK))


def hand(c, x, y, s=1.0, press=0.0):
    """A pointing hand, its fingertip at (x, y)."""
    k = s * (1 - 0.08 * press)
    with G.xf(c, x, y, s=k):
        p = skia.Path()
        p.moveTo(-6, 0)
        p.cubicTo(-6, -12, 10, -12, 10, 0)
        p.lineTo(10, 38)
        p.cubicTo(14, 30, 30, 30, 30, 42)
        p.cubicTo(34, 36, 48, 36, 48, 48)
        p.cubicTo(52, 42, 66, 44, 66, 56)
        p.lineTo(66, 84)
        p.cubicTo(66, 108, 52, 124, 30, 124)
        p.lineTo(18, 124)
        p.cubicTo(4, 124, -4, 116, -12, 104)
        p.lineTo(-30, 76)
        p.cubicTo(-38, 64, -24, 54, -14, 64)
        p.lineTo(-6, 72)
        p.close()
        with G.xf(c, 3, 6):
            c.drawPath(p, G.P("#000000", 0.28, blur=5))
        c.drawPath(p, G.P(WHITE))
        c.drawPath(p, G.P(INK, 1, stroke=5, join="round"))
        for dx in (22, 36, 50):
            c.drawLine(dx, 90, dx, 110, G.P(INK, 1, stroke=4, cap="round"))


def comment_card(c, t):
    """The note the click leaves: the IPO, and staying on top."""
    u = out_back(clamp((t - (T_CLICK + 0.08)) / 0.3), 1.5)
    if u <= 0:
        return
    with G.xf(c, 836, 176, s=max(0.01, u), px=0, py=0):
        card(c, 0, 0, 356, 92, 14, WHITE, shadow=0.12, lift=8, blur=18, border=(LINE, 1.0, 1.4))
        c.drawCircle(26, 30, 11, G.P(CLAY))
        T(c, "IPO planned for November.", 46, 36, inter(16, 640), INK)
        T(c, "Staying on top.", 46, 66, inter(16, 460), INK)


def canvas(c, t):
    """The canvas: a swatch is picked, then the camera dives into the toolbar and Comment is clicked."""
    commented = clamp((t - T_CLICK) / 0.08)
    z = in_out_cubic(clamp((t - T_TOOLBAR) / 0.34))
    zoom = lerp(ease_push(t, T_CANVAS, T_TOOLBAR, 0.04), 2.9, z)
    px, py = 879.0, 145.0                               # Comment, which the camera pushes toward and dives into
    sx, sy = lerp(px, 830.0, z), lerp(py, 410.0, z)
    with G.xf(c, sx, sy, s=zoom):
        c.translate(-px, -py)
        canvas_ui(c, t, commented)
        comment_card(c, t)
        # the arrow picks a swatch before the dive
        if t < T_TOOLBAR + 0.1:
            k = clamp((t - T_CANVAS) / (T_SWATCH - T_CANVAS))
            ax, ay = lerp(1300, 1590, out_cubic(k)), lerp(640, 294, out_cubic(k))
            press = math.exp(-max(0.0, t - T_SWATCH) / 0.08) if t >= T_SWATCH else 0.0
            arrow(c, ax, ay, 1.0, press)
    # the hand comes in for the click, in screen space so it stays the size a hand should be
    if t >= T_TOOLBAR + 0.2:
        k = out_cubic(clamp((t - (T_TOOLBAR + 0.2)) / (T_CLICK - T_TOOLBAR - 0.24)))
        hx, hy = lerp(1400, 850, k), lerp(1100, 425, k)
        press = math.exp(-max(0.0, t - T_CLICK) / 0.09) if t >= T_CLICK else 0.0
        hand(c, hx, hy, 1.25, press)
