"""The phone: the ask (a glowing input you type into) and the chat where the assistant books Arnaud's."""
import math
from functools import lru_cache

import skia

from engine import gfx as G
from engine.core import clamp, lerp, snap, whip, out_cubic, in_out_cubic, spring, out_back
from .look import (F, T, ui, rr, WHITE, INK, GREY, FAINT, LINE, LIME, ORANGE, BLUE, LAVENDER, CARD, GOLD, GLOW,
                   glow_rrect, glow_blob, soft_shadow, caret, phone, status_bar, icon_arrow, icon_x, icon_plus,
                   icon_send, icon_check, icon_pin, icon_clock, icon_people, icon_star, icon_puff, icon_shrimp,
                   icon_flame, draw_cover, hand, sweep)
from .score import T_PHONE, T_TYPE, PROMPT, T_SEND, T_CHAT, T_MSG, T_TAP, T_MAP

# ---------------------------------------------------------------- the ask

PX, PY, PW, PH = 333, 150, 1254, 1300          # the phone, big and cropped, as in the reference
IX, IY, IW, IH = 368, 388, 1184, 318           # the input card


def wrap(text, font, width):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.width(test) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


@lru_cache(maxsize=1)
def prompt_lines():
    return wrap(PROMPT, ui(44, 430), IW - 210)


def typed(t):
    n = len(PROMPT)
    return int(round(n * clamp((t - T_TYPE[0]) / (T_TYPE[1] - T_TYPE[0]))))


def ask(c, t):
    """The phone rises out of a 3D tilt and settles; the prompt types itself into the glowing input."""
    u = snap(clamp((t - T_PHONE) / 0.7))
    push = 1.0 + 0.06 * in_out_cubic(clamp((t - T_TYPE[0]) / 2.0))
    c.save()
    c.concat(G.perspective(960, 520, rx=16 * (1 - u), ry=-24 * (1 - u), rz=-7 * (1 - u), D=2200))
    c.translate(960, 560)
    s = lerp(1.14, 1.0, u) * push
    c.scale(s, s)
    c.translate(-960, -560 - 70 * (1 - u))
    phone(c, PX, PY, PW, PH)
    status_bar(c, PX, PY + 40, PW)
    glow_rrect(c, IX, IY, IW, IH, 46, t, a=1.0, spread=30, width=22, speed=50)
    c.drawRRect(rr(IX, IY, IW, IH, 46), G.P(WHITE))
    icon_arrow(c, IX + 72, IY + 66, 34, INK, -1)
    icon_x(c, IX + IW - 70, IY + 66, 30, INK)
    icon_plus(c, IX + 64, IY + IH - 56, 30, INK)
    send_pr = math.exp(-(t - T_SEND) / 0.08) if t >= T_SEND else 0.0
    icon_send(c, IX + IW - 76, IY + IH - 60, 34, press=send_pr)
    f = ui(44, 430)
    n = typed(t)
    x0, y0 = IX + 104, IY + 142
    shown = n
    cx, cy = x0, y0
    for k, line in enumerate(prompt_lines()):
        part = line[:max(0, shown)]
        if part:
            T(c, part, x0, y0 + k * 58, f, INK)
        if 0 <= shown <= len(line):
            cx, cy = x0 + f.width(part) + 4, y0 + k * 58
        shown -= len(line) + 1
        if shown < 0:
            break
    typing = T_TYPE[0] <= t < T_TYPE[1]
    if t >= T_SEND:
        caret(c, cx + 6, cy - 40, 54, 70)
    else:
        caret(c, cx + 6, cy - 40, 54, 70 if typing else 30, a=1.0 if (typing or int(t * 2.4) % 2 == 0) else 0.0)
    c.restore()
    return cx, cy


# ---------------------------------------------------------------- the chat

CW = 700
CX0 = 960 - CW / 2
BUB = LIME


def bubble(c, x, y, w, lines, font, a=1.0, right=False, lh=36, pad=24):
    h = pad * 2 + lh * len(lines) - 8
    bx = x + (w if right else 0)
    with G.layer(c, alpha=a):
        c.drawRRect(rr(bx - (w if right else 0), y, w, h, 22), G.P(BUB))
        for k, line in enumerate(lines):
            T(c, line, bx - (w if right else 0) + pad, y + pad + 24 + k * lh, font, INK)
    return h


def _bw(lines, font, pad=24):
    return max(font.width(l) for l in lines) + pad * 2


def pop_in(t, t0):
    """Messages rise and settle, like the reference."""
    if t < t0:
        return 0.0, 30.0, 0.94
    u = clamp((t - t0) / 0.35)
    return clamp((t - t0) / 0.15), 30 * (1 - out_back(u, 1.2)), 0.94 + 0.06 * out_cubic(u)


def dish_chip(c, x, y, icon, label, a):
    f = ui(21, 560)
    w = f.width(label) + 88
    c.drawRRect(rr(x, y, w, 56, 28), G.P(CARD, a))
    icon(c, x + 32, y + 28, 30, ORANGE if icon is not icon_puff else GOLD, a)
    T(c, label, x + 58, y + 36, f, WHITE, a=a)
    return w


def restaurant_card(c, x, y, w, t, a=1.0, lift=0.0):
    h = 470
    with G.layer(c, alpha=a):
        if lift > 0:
            glow_rrect(c, x, y, w, h, 28, t, a=lift, spread=34, width=26, speed=60)
        c.drawRRect(rr(x, y, w, h, 28), G.P(CARD))
        c.save()
        c.clipRRect(rr(x, y, w, h, 28), skia.ClipOp.kIntersect, True)
        draw_cover(c, "dining", x, y, w, 300, fx=0.35, fy=0.3, zoom=1.08 + 0.04 * math.sin(t * 0.8))
        c.drawRect(skia.Rect.MakeXYWH(x, y + 180, w, 125),
                   G.P(CARD, 1, shader=G.linear_grad(0, y + 180, 0, y + 305, [CARD, CARD], alphas=[0.0, 1.0])))
        c.restore()
        # badges
        fb = ui(17, 600)
        bw = fb.width("Since 1918") + 50
        c.drawRRect(rr(x + 18, y + 18, bw, 36, 18), G.P("#000000", 0.55))
        c.drawRRect(rr(x + 18, y + 18, bw, 36, 18), G.P(GOLD, 0.9, stroke=1.4))
        icon_star(c, x + 38, y + 36, 16, GOLD)
        T(c, "Since 1918", x + 52, y + 42, fb, WHITE)
        tw = fb.width("French Quarter") + 32
        c.drawRRect(rr(x + w - 18 - tw, y + 18, tw, 36, 18), G.P("#000000", 0.55))
        T(c, "French Quarter", x + w - 18 - tw / 2, y + 42, fb, WHITE, align=0.5)
        T(c, "Arnaud’s", x + 26, y + 348, F("serif", 46), WHITE)
        T(c, "Classic Creole, chandeliers and all.", x + 26, y + 384, ui(19, 430), "#a6a6ad")
        fm = ui(17, 520)
        mx = x + 26
        for icon, label in ((icon_pin, "813 Bienville St"), (icon_clock, "8:00 pm"), (icon_people, "Table for 2")):
            icon(c, mx + 9, y + 432, 20, "#a6a6ad")
            T(c, label, mx + 26, y + 438, fm, "#d6d6db")
            mx += fm.width(label) + 62
    return h


CHAT_LINES = {
    "user": PROMPT,
    "reply": "Happy anniversary! Pizza, sushi and ramen can wait. Tonight calls for Arnaud’s: classic Creole in the "
             "French Quarter since 1918.",
    "dishes": "Order the classics: Soufflé Potatoes, Shrimp Arnaud and Bananas Foster.",
    "ask": "Want me to book a table for two at 8 pm? I can handle it.",
}


@lru_cache(maxsize=1)
def chat_layout():
    f = ui(25, 440)
    items = []
    y = 0
    lines = wrap(CHAT_LINES["user"], f, 430)
    items.append(("user", y, lines))
    y += 48 + 36 * len(lines) + 34
    lines = wrap(CHAT_LINES["reply"], f, 520)
    items.append(("reply", y, lines))
    y += 48 + 36 * len(lines) + 34
    items.append(("card", y, None))
    y += 470 + 30
    lines = wrap(CHAT_LINES["dishes"], f, 520)
    items.append(("dishes", y, lines))
    y += 48 + 36 * len(lines) + 20
    items.append(("chips", y, None))
    y += 56 * 2 + 12 + 30
    lines = wrap(CHAT_LINES["ask"], f, 520)
    items.append(("ask", y, lines))
    y += 48 + 36 * len(lines) + 22
    items.append(("buttons", y, None))
    y += 70
    return items, y


def chat_scroll(t):
    """Keep the newest message near the bottom of the frame."""
    items, _ = chat_layout()
    target = 0.0
    for (kind, y, _), tm in zip(items, T_MSG):
        h = {"card": 470, "chips": 124, "buttons": 64}.get(kind, 120)
        bottom = y + h
        u = snap(clamp((t - tm) / 0.45))
        target = max(target, (bottom - 820) * u)
    return target


BUTTON_BOOK = (CX0 + 36, 0, 250, 64)      # y filled in at draw time


def chat(c, t, glow_a=1.0):
    items, total = chat_layout()
    f = ui(25, 440)
    top = 140 - chat_scroll(t)
    # the phone column, with the reference's coloured light down both sides
    for side, cols in ((-1, [GLOW[4], GLOW[3], GLOW[2]]), (1, [GLOW[0], GLOW[6], GLOW[2]])):
        x = 960 + side * (CW / 2 + 40)
        sh = G.linear_grad(0, 0, 0, 1080, cols)
        c.drawRect(skia.Rect.MakeXYWH(x - 30, -100, 60, 1280), G.P(cols[0], 0.9 * glow_a, shader=sh, blur=38))
    c.drawRect(skia.Rect.MakeXYWH(CX0, -10, CW, 1100), G.P(WHITE))
    c.drawRect(skia.Rect.MakeXYWH(CX0, -10, CW, 1100), G.P("#000000", 0.04, stroke=1.2))
    btn_y = None
    for (kind, y, lines), tm in zip(items, T_MSG):
        a, dy, s = pop_in(t, tm)
        if a <= 0:
            continue
        yy = top + y + dy
        if kind in ("user",):
            w = _bw(lines, f)
            with G.xf(c, CX0 + CW - 36 - w / 2, yy, s=s):
                c.translate(-(CX0 + CW - 36 - w / 2), -yy)
                bubble(c, CX0 + CW - 36 - w, yy, w, lines, f, a=a)
        elif kind in ("reply", "dishes", "ask"):
            if kind == "reply" and t < tm + 0.02:
                continue
            w = _bw(lines, f)
            with G.xf(c, CX0 + 36, yy, s=s):
                c.translate(-(CX0 + 36), -yy)
                bubble(c, CX0 + 36, yy, w, lines, f, a=a)
        elif kind == "card":
            with G.xf(c, CX0 + 36 + 290, yy + 235, s=s):
                c.translate(-(CX0 + 36 + 290), -(yy + 235))
                restaurant_card(c, CX0 + 36, yy, 580, t, a=a, lift=0.6 * a)
        elif kind == "chips":
            cx = CX0 + 36
            row = [(icon_puff, "Soufflé Potatoes"), (icon_shrimp, "Shrimp Arnaud"), (icon_flame, "Bananas Foster")]
            for k, (icon, label) in enumerate(row):
                ak, dk, sk = pop_in(t, tm + 0.08 * k)
                if ak <= 0:
                    continue
                if k == 2:
                    dish_chip(c, CX0 + 36, yy + 68 + dk, icon, label, ak)
                else:
                    cx += dish_chip(c, cx, yy + dk, icon, label, ak) + 12
        elif kind == "buttons":
            btn_y = yy
            pr = math.exp(-(t - T_TAP) / 0.08) if t >= T_TAP else 0.0
            done = snap(clamp((t - T_TAP - 0.05) / 0.25))
            bx, bw, bh = CX0 + 36, 250, 64
            with G.layer(c, alpha=a):
                glow_rrect(c, bx, yy, bw, bh, bh / 2, t, a=1.0 - done, spread=12, width=10, speed=120)
                with G.xf(c, bx + bw / 2, yy + bh / 2, s=1 - 0.08 * pr):
                    c.drawRRect(rr(-bw / 2, -bh / 2, bw, bh, bh / 2), G.P(G.mixc(WHITE, LIME, done)))
                    if done > 0.5:
                        icon_check(c, -54, 0, 26, INK, p=clamp((done - 0.5) * 2))
                        T(c, "Booked", -28, 9, ui(25, 600), INK, align=0.0)
                    else:
                        T(c, "Book the table", 0, 9, ui(25, 560), INK, align=0.5)
                ow = ui(25, 560).width("More options") + 56
                c.drawRRect(rr(bx + bw + 14, yy, ow, bh, bh / 2), G.P(INK))
                T(c, "More options", bx + bw + 14 + ow / 2, yy + 41, ui(25, 560), WHITE, align=0.5)
    # the assistant typing, just before its first reply
    tr = T_MSG[1]
    if tr - 0.4 <= t < tr:
        ty = top + items[1][1]
        c.drawRRect(rr(CX0 + 36, ty, 120, 64, 22), G.P(BUB))
        for k in range(3):
            b = abs(math.sin((t - tr) * 12 + k * 0.9))
            G.circle(c, CX0 + 72 + k * 24, ty + 34 - 8 * b, 7, G.P(INK, 0.7))
    return btn_y


def tap_point(t):
    """Where the finger lands on "Book the table"."""
    items, _ = chat_layout()
    y = [yy for kind, yy, _ in items if kind == "buttons"][0]
    return CX0 + 36 + 150, 140 - chat_scroll(t) + y + 40


def finger(c, t):
    if not T_MSG[-1] + 0.1 <= t < T_MAP + 0.1:
        return
    tx, ty = tap_point(T_TAP)
    u = in_out_cubic(clamp((t - (T_TAP - 0.55)) / 0.5))
    x = lerp(tx + 360, tx, u)
    y = lerp(ty + 300, ty, u) + 60 * math.sin(math.pi * u) * -0.5
    pr = math.exp(-(t - T_TAP) / 0.09) if t >= T_TAP else 0.0
    a = clamp((t - T_MSG[-1] - 0.1) / 0.2) * (1 - clamp((t - T_TAP - 0.3) / 0.2))
    hand(c, x, y, s=2.6, press=pr, a=a)
    if t >= T_TAP:
        v = (t - T_TAP) / 0.5
        if v < 1:
            G.circle(c, tx, ty, 10 + 70 * out_cubic(v), G.P(INK, 0.35 * (1 - v), stroke=3))


def caret_local(t):
    f = ui(44, 430)
    shown = typed(t)
    x0, y0 = IX + 104, IY + 142
    cx, cy = x0, y0
    for k, line in enumerate(prompt_lines()):
        part = line[:max(0, shown)]
        if 0 <= shown <= len(line):
            cx, cy = x0 + f.width(part) + 4, y0 + k * 58
        shown -= len(line) + 1
        if shown < 0:
            break
    return cx, cy


def typed_caret(t):
    """The caret block's centre on screen (the phone has settled by the time anyone asks)."""
    cx, cy = caret_local(t)
    s = 1.0 + 0.06 * in_out_cubic(clamp((t - T_TYPE[0]) / 2.0))
    x, y = cx + 6 - 35, cy - 13
    return 960 + (x - 960) * s, 560 + (y - 560) * s
