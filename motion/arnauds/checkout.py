"""The cashier: on the light-green ground a white receipt printer feeds the order out line by line, a white
payment terminal rolls the amount due, a gold card taps it, the screen goes gold and the receipt is stamped
CONFIRMED."""
import math
from functools import lru_cache

import skia

from engine import gfx as G
from engine.core import clamp, lerp, snap, whip, out_cubic, out_back, spring, hash01
from .look import (F, T, ui, rr, WHITE, INK, GOLD, GOLD_DEEP, GOLD_PALE, SHADOW, glow_rrect, glow_blob, icon_check,
                   sweep, ground)
from .score import T_CHAT, T_PRINT, T_TERMINAL, T_AMOUNT, T_CARD, T_TAP, T_STAMP

PAPER = WHITE
BODY = ["#ffffff", "#eef0ec"]      # the printer and the terminal: white plastic
DIM = "#8a8a8a"
PRINT_INK = "#16140f"
SLOT_Y = 918
SCALE, SHIFT = 1.1, 110          # the whole counter, a little closer and centred
PAPER_X, PAPER_W = 548, 430

# (kind, left, right, height): the receipt, top to bottom
LINES = [
    ("name", "Arnaud’s", "", 70),
    ("small", "813 BIENVILLE ST · NEW ORLEANS", "", 30),
    ("small", "CLASSIC CREOLE · EST. 1918", "", 34),
    ("dash", "", "", 26),
    ("row", "TONIGHT", "8:00 PM", 38),
    ("row", "TABLE FOR 2", "MAIN DINING ROOM", 38),
    ("dash", "", "", 26),
    ("head", "PRE-ORDER", "", 38),
    ("row", "1  SOUFFLÉ POTATOES", "", 36),
    ("row", "1  SHRIMP ARNAUD", "", 36),
    ("row", "1  BANANAS FOSTER", "FOR 2", 36),
    ("dash", "", "", 26),
    ("row", "NOTE", "HAPPY ANNIVERSARY", 38),
    ("dash", "", "", 26),
    ("total", "DUE NOW", "$0.00", 56),
    ("small", "PAY AT THE TABLE", "", 34),
    ("barcode", "", "", 74),
    ("small", "RES 0926 · 1918", "", 30),
    ("small", "MERCI · THANK YOU", "", 34),
]
TOP_PAD, BOTTOM_PAD = 34, 26


@lru_cache(maxsize=1)
def offsets():
    out, y = [], TOP_PAD
    for kind, a, b, h in LINES:
        out.append(y)
        y += h
    return out, y + BOTTOM_PAD


def print_time(i):
    return T_PRINT[0] + (T_PRINT[1] - T_PRINT[0]) * i / len(LINES)


def paper_len(t):
    """How much paper is out of the slot: each line feeds out over a few frames."""
    offs, total = offsets()
    L = TOP_PAD * clamp((t - T_PRINT[0] + 0.1) / 0.1)
    for i, (kind, a, b, h) in enumerate(LINES):
        L += h * snap(clamp((t - print_time(i)) / 0.09))
    if t > T_PRINT[1]:
        L += BOTTOM_PAD * snap(clamp((t - T_PRINT[1]) / 0.15))
    return L


def fm(size, w=500):
    return F("mono", size, wght=w)


def receipt(c, t):
    L = paper_len(t)
    if L <= 1:
        return
    top = SLOT_Y - L
    x, w = PAPER_X, PAPER_W
    # paper: a soft glow, a shadow on the ground, the sheet, and a torn top edge
    glow_blob(c, x + w / 2, top + L / 2, max(w, L) * 0.75, WHITE, 0.25)
    c.drawRect(skia.Rect.MakeXYWH(x + 8, top + 12, w, L), G.P(SHADOW, 0.25, blur=18))
    edge = skia.Path()
    edge.moveTo(x, SLOT_Y)
    edge.lineTo(x, top + 8)
    n = 22
    for k in range(n + 1):
        edge.lineTo(x + w * k / n, top + (0 if k % 2 else 8))
    edge.lineTo(x + w, SLOT_Y)
    edge.close()
    c.drawPath(edge, G.P(PAPER))
    c.drawRect(skia.Rect.MakeXYWH(x, SLOT_Y - 60, w, 60),
               G.P(SHADOW, 1, shader=G.linear_grad(0, SLOT_Y - 60, 0, SLOT_Y, [SHADOW, SHADOW],
                                                    alphas=[0.0, 0.12])))
    offs, _ = offsets()
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(x, top, x + w, SLOT_Y - 2))
    lx, rx = x + 30, x + w - 30
    for i, ((kind, a, b, h), off) in enumerate(zip(LINES, offs)):
        if t < print_time(i):
            continue
        y = top + off + h * 0.72
        fresh = clamp((t - print_time(i)) / 0.12)
        ink = G.mixc("#9b9486", PRINT_INK, fresh)
        if kind == "name":
            T(c, a, x + w / 2, y + 4, F("serif", 58), ink, align=0.5)
        elif kind == "small":
            T(c, a, x + w / 2, y, fm(17, 520), ink, align=0.5, tracking=0.12)
        elif kind == "dash":
            c.drawLine(lx, y - 8, rx, y - 8, G.P(ink, 0.6, stroke=1.6, effect=G.dash(7, 6)))
        elif kind == "head":
            T(c, a, lx, y, fm(19, 760), ink, tracking=0.16)
        elif kind == "row":
            T(c, a, lx, y, fm(19, 520), ink, tracking=0.04)
            if b:
                T(c, b, rx, y, fm(19, 520), ink, align=1.0, tracking=0.04)
        elif kind == "total":
            T(c, a, lx, y + 4, fm(24, 800), ink, tracking=0.1)
            T(c, b, rx, y + 6, fm(36, 800), ink, align=1.0)
        elif kind == "barcode":
            bx = lx + 20
            k = 0
            while bx < rx - 20:
                bw = 2 + 4 * float(hash01(k, 41))
                if k % 2 == 0:
                    c.drawRect(skia.Rect.MakeXYWH(bx, y - h * 0.55, bw, h * 0.7), G.P(ink))
                bx += bw + 1.5 + 2 * float(hash01(k, 43))
                k += 1
    c.restore()
    stamp(c, t, top)


def stamp(c, t, top):
    if t < T_STAMP:
        return
    u = clamp((t - T_STAMP) / 0.18)
    s = lerp(1.8, 1.0, out_cubic(u))
    offs, _ = offsets()
    y = top + offs[9] + 18
    with G.layer(c, alpha=0.88 * clamp(u * 2)):
        with G.xf(c, PAPER_X + PAPER_W / 2 + 10, y, s=s, rot=-13):
            f = F("inter", 46, wght=860, opsz=32)
            w = f.width("CONFIRMED", 0.08) + 44
            c.drawRRect(rr(-w / 2, -40, w, 80, 12), G.P(GOLD_DEEP, 1, stroke=5))
            c.drawRRect(rr(-w / 2 + 8, -32, w - 16, 64, 8), G.P(GOLD_DEEP, 0.5, stroke=1.6))
            T(c, "CONFIRMED", 0, 17, f, GOLD_DEEP, align=0.5, tracking=0.08)


def printer(c, t):
    x, y, w = 470, 896, 586
    c.drawRRect(rr(x + 6, y + 18, w, 260, 40), G.P(SHADOW, 0.22, blur=26))
    c.drawRRect(rr(x, y, w, 260, 40), G.P(WHITE, 1, shader=G.linear_grad(0, y, 0, y + 200, BODY)))
    c.drawRRect(rr(x + 1, y + 1, w - 2, 258, 40), G.P(GOLD, 0.6, stroke=1.5))
    c.drawRRect(rr(x + 70, SLOT_Y - 4, w - 140, 9, 4), G.P("#2b2b2b"))
    busy = T_PRINT[0] <= t < T_PRINT[1] + 0.2
    blink = 1.0 if not busy else (0.4 + 0.6 * (int(t * 12) % 2))
    G.circle(c, x + w - 44, y + 62, 7, G.P(GOLD, blink))
    glow_blob(c, x + w - 44, y + 62, 26, GOLD, 0.6 * blink)
    T(c, "PRINTING" if busy else "READY", x + 44, y + 70, fm(15, 640), DIM, tracking=0.3)


# ---------------------------------------------------------------- the terminal

TX, TY, TW, TH = 1190, 214, 430, 700
SCR = (TX + 26, TY + 26, TW - 52, 440)


def tap_point(t=None):
    sx, sy, sw, sh = SCR
    return sx + sw / 2, sy + sh * 0.62


def _roll_amount(c, t, x, y, f, col):
    """The amount spins like a till before it lands on $0.00."""
    target = "$0.00"
    u = clamp((t - T_AMOUNT) / 0.7)
    run = f.shape(target, features={"tnum": True})
    for i, (gid, gx, adv) in enumerate(zip(run.gids, run.xs, run.adv)):
        ch = target[i]
        land = clamp((u - 0.12 * i) / 0.45)
        if ch in "$.":
            T(c, ch, x + gx, y, f, col, a=clamp(u * 3))
            continue
        with G.clip_rect(c, x + gx - 4, y - f.cap - 16, adv + 8, f.cap + 32):
            if land >= 1:
                T(c, ch, x + gx, y, f, col)
            else:
                spin = (t * 26 + i * 3.1) % 1.0
                d0 = str(int(t * 26 + i * 7) % 10)
                d1 = str((int(t * 26 + i * 7) + 1) % 10)
                h = f.cap * 1.6
                T(c, d0, x + gx, y - h * spin * (1 - land), f, col, a=clamp(u * 3), tnum=True)
                T(c, d1, x + gx, y + h * (1 - spin) * (1 - land), f, col, a=clamp(u * 3) * (1 - land), tnum=True)


def contactless(c, x, y, s, col, a=1.0):
    for k in range(4):
        r = s * (0.25 + 0.22 * k)
        c.drawPath(G.arc_path(x - s * 0.4, y, r, -45, 90), G.P(col, a * (1 - 0.15 * k), stroke=s * 0.08, cap="round"))


def terminal(c, t):
    u = spring(t - T_TERMINAL, 2.3, 0.6) if t >= T_TERMINAL else 0.0
    if u <= 0:
        return
    dx = 700 * (1 - u)
    with G.xf(c, dx, 0):
        glow_rrect(c, TX, TY, TW, TH, 52, t, a=0.9, spread=40, width=30, speed=55)
        c.drawRRect(rr(TX + 8, TY + 24, TW, TH, 52), G.P(SHADOW, 0.22, blur=30))
        c.drawRRect(rr(TX, TY, TW, TH, 52), G.P(WHITE, 1, shader=G.linear_grad(0, TY, 0, TY + TH, BODY)))
        c.drawRRect(rr(TX + 1, TY + 1, TW - 2, TH - 2, 52), G.P(GOLD, 0.6, stroke=1.5))
        sx, sy, sw, sh = SCR
        c.drawRRect(rr(sx, sy, sw, sh, 30), G.P("#f7f8f5"))
        c.drawRRect(rr(sx, sy, sw, sh, 30), G.P("#000000", 0.08, stroke=1.2))
        ok = snap(clamp((t - T_TAP) / 0.35))
        c.save()
        c.clipRRect(rr(sx, sy, sw, sh, 30), skia.ClipOp.kIntersect, True)
        T(c, "Arnaud’s", sx + 30, sy + 66, F("serif", 44), INK)
        T(c, "Table for 2 · 8:00 PM", sx + 32, sy + 102, ui(21, 480), DIM)
        T(c, "DUE NOW", sx + 32, sy + 176, fm(16, 700), DIM, tracking=0.24)
        if t >= T_AMOUNT:
            _roll_amount(c, t, sx + 28, sy + 282, F("inter", 104, wght=700, opsz=32), INK)
        T(c, "Your card holds the table.", sx + 32, sy + 332, ui(20, 460), DIM)
        pulse = 0.55 + 0.45 * math.sin(t * 7)
        contactless(c, sx + sw / 2 - 70, sy + 398, 40, GOLD_DEEP, pulse)
        T(c, "Tap to confirm", sx + sw / 2 - 40, sy + 406, ui(22, 600), INK)
        if ok > 0:
            px, py = tap_point()
            clip = skia.Path()
            clip.addCircle(px, py, 520 * ok)
            c.clipPath(clip, skia.ClipOp.kIntersect, True)
            c.drawRect(skia.Rect.MakeXYWH(sx, sy, sw, sh), G.P(GOLD, 1, shader=G.linear_grad(sx, sy, sx + sw, sy + sh,
                                                                                         ["#ffe08a", GOLD, "#e0a82e"])))
            G.circle(c, sx + sw / 2, sy + 170, 64, G.P(WHITE))
            icon_check(c, sx + sw / 2, sy + 174, 60, GOLD_DEEP, p=clamp((t - T_TAP - 0.1) / 0.3))
            T(c, "Confirmed", sx + sw / 2, sy + 312, ui(48, 720), INK, align=0.5)
            T(c, "See you at 8:00 PM", sx + sw / 2, sy + 356, ui(22, 500), INK, align=0.5)
        c.restore()
        # the lower body: a reader lip and a soft status light
        c.drawRRect(rr(TX + 150, TY + TH - 150, TW - 300, 10, 5), G.P("#2b2b2b", 0.8))
        T(c, "ARNAUD’S · FRENCH QUARTER", TX + TW / 2, TY + TH - 70, fm(14, 600), DIM, align=0.5,
          tracking=0.24)


def card(c, t):
    """A gold metal card flies in, taps, and leaves."""
    if t < T_CARD:
        return
    u = clamp((t - T_CARD) / (T_TAP - T_CARD))
    e = out_back(u, 1.1) if u < 1 else 1.0
    px, py = tap_point()
    x = lerp(2150, px + 30, e)
    y = lerp(1300, py - 10, e)
    rot = lerp(-38, -9, e)
    s = lerp(1.25, 1.0, e)
    back = clamp((t - T_TAP - 0.12) / 0.45)
    if back > 0:
        b = whip(back)
        x += 900 * b
        y += 420 * b
        rot += 25 * b
    press = math.exp(-(t - T_TAP) / 0.06) if t >= T_TAP else 0.0
    w, h = 360, 227
    with G.xf(c, x, y, rot=rot, s=s * (1 - 0.05 * press)):
        c.drawRRect(rr(-w / 2 + 10, -h / 2 + 22, w, h, 22), G.P(SHADOW, 0.35, blur=24))
        c.drawRRect(rr(-w / 2, -h / 2, w, h, 22), G.P(GOLD, 1, shader=G.linear_grad(-w / 2, -h / 2, w / 2, h / 2,
                                                                                  [GOLD_PALE, GOLD, GOLD_DEEP])))
        # an iridescent sheen slides across the metal
        sh = sweep(0, 0, t, speed=120, alpha=0.35)
        p = skia.Paint(AntiAlias=True)
        p.setShader(sh)
        p.setBlendMode(skia.BlendMode.kScreen)
        c.save()
        c.clipRRect(rr(-w / 2, -h / 2, w, h, 22), skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), p)
        c.restore()
        c.drawRRect(rr(-w / 2 + 0.5, -h / 2 + 0.5, w - 1, h - 1, 22), G.P(WHITE, 0.5, stroke=1.2))
        c.drawRRect(rr(-w / 2 + 30, -26, 56, 42, 8), G.P(WHITE, 0.9))
        for k in range(3):
            c.drawLine(-w / 2 + 30, -12 + k * 12, -w / 2 + 86, -12 + k * 12, G.P(GOLD_DEEP, 0.6, stroke=1.2))
        contactless(c, w / 2 - 44, -h / 2 + 46, 34, WHITE, 0.9)
        T(c, "•••• 1918", -w / 2 + 30, h / 2 - 34, fm(24, 600), WHITE, tracking=0.12)
    if t >= T_TAP:
        for k in range(3):
            v = (t - T_TAP - 0.08 * k) / 0.6
            if 0 <= v < 1:
                G.circle(c, px, py, 40 + 320 * out_cubic(v), G.P(GOLD_DEEP, 0.7 * (1 - v), stroke=4))


def checkout(c, t):
    ground(c, t)
    push = SCALE * (1 + 0.04 * clamp((t - T_CHAT) / 3.5))
    c.save()
    c.translate(960 - SHIFT, 560)
    c.scale(push, push)
    c.translate(-960, -560)
    receipt(c, t)
    printer(c, t)
    terminal(c, t)
    card(c, t)
    c.restore()
