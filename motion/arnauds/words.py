"""Type as picture: the giant words (filled with the food they name), the bowl that thinks, and the closing lines."""
import math
from functools import lru_cache

import numpy as np
import skia

from engine import gfx as G
from engine.core import clamp, lerp, snap, whip, out_cubic, in_out_cubic, spring, out_back, hash01
from .look import (F, T, ui, rr, WHITE, INK, GREY, FAINT, LIME, ORANGE, BLUE, LAVENDER, GLOW, GOLD,
                   glow_rrect, glow_blob, caret, image_shader, draw_cover, sweep, photo)
from .score import (T_GIANT, WORDS, T_FIND, T_DROPS, T_RISE, T_LIME, T_CRAVE, T_ROLL, T_WAIT)

GIANT = 380
BASE = 700


# ---------------------------------------------------------------- giant words

def giant_font():
    return F("inter", GIANT, wght=520, opsz=32)


@lru_cache(maxsize=1)
def giant_layout():
    f = giant_font()
    space = f.width(" ")
    out, x = [], 0.0
    for t0, word, fill in WORDS:
        w = f.width(word)
        out.append(dict(t=t0, word=word, fill=fill, x=x, w=w))
        x += w + space
    return out


def _typed(t, t0, word):
    return int(math.ceil(len(word) * clamp((t - t0) / 0.14)))


def giant_cam(t):
    """Camera x (the left edge of the frame in line coordinates): the caret rides at ~70% of the width."""
    lay = giant_layout()
    x = -700.0
    for i, it in enumerate(lay):
        target = it["x"] + it["w"] - 1250
        u = clamp((t - it["t"] + 0.12) / 0.34)
        x = lerp(x, target, whip(u) if i else in_out_cubic(u))
    return x


def word_fill(c, it, x, y, t):
    f = giant_font()
    n = _typed(t, it["t"], it["word"])
    part = it["word"][:n]
    if not part:
        return x
    run = f.shape(part)
    path = run.path(x, y)
    kind = it["fill"]
    if kind in ("pizza", "sushi", "ramen"):
        top = y - f.cap - 40
        sh = image_shader(kind, x, top, it["w"], GIANT * 1.05, fx=0.5, fy=0.55,
                          zoom=1.0 + 0.05 * (t - it["t"]), min_w=900)
        p = skia.Paint(AntiAlias=True)
        if sh is not None:
            p.setShader(sh)
        else:
            p.setColor(G.cint(ORANGE))
        c.drawPath(path, p)
        c.drawPath(path, G.P(INK, 0.9, stroke=3.0, join="round"))
    elif kind == "glow":
        glow = skia.Paint(AntiAlias=True)
        glow.setShader(G.linear_grad(x, 0, x + it["w"], 0, GLOW[:6]))
        glow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26))
        glow.setAlphaf(0.8)
        c.drawPath(path, glow)
        p = skia.Paint(AntiAlias=True)
        p.setShader(G.linear_grad(x, 0, x + it["w"], 0, ["#c2358c", "#e8703a", "#7cc242", "#2fb07a", "#4f72e8"]))
        c.drawPath(path, p)
    else:
        c.drawPath(path, G.P(INK))
    return x + run.width


def giant(c, t):
    lay = giant_layout()
    cam = giant_cam(t)
    c.save()
    c.translate(-cam, 0)
    end_x, alive = None, None
    for it in lay:
        if t < it["t"]:
            break
        end_x = word_fill(c, it, it["x"], BASE, t)
        alive = it
    if end_x is not None:
        typing = t - alive["t"] < 0.2
        caret(c, end_x + 30, BASE - giant_font().cap - 50, GIANT * 1.02, 520 if typing else 260)
    else:
        caret(c, lay[0]["x"] + 10, BASE - giant_font().cap - 50, GIANT * 1.02, 700)
    c.restore()


# ---------------------------------------------------------------- the bowl that thinks

BOWL = (1030, 640, 250)                   # centre of the rim, radius
CHIPS = ["pizza", "sushi", "ramen"]


def bowl_tilt(t):
    return 10 * math.sin((t - T_FIND) * 2.4) - 6


def finding(c, t, enter=1.0):
    """.Finding something special... over a big white card whose corner glows; the three cravings drop into an
    orange bowl, and something special rises out of it."""
    # the card: only its lower right corner is on screen
    glow_rrect(c, -200, -200, 1640, 1080, 160, t, a=1.0, spread=34, width=30, speed=45)
    c.drawRRect(rr(-200, -200, 1640, 1080, 160), G.P(WHITE))
    f = ui(56, 430)
    dots = int((t - T_FIND) * 6) % 4
    T(c, ".Finding something special" + "." * dots, 90, 140, f, INK)
    bx, by, br = BOWL
    ang = bowl_tilt(t)
    # bouncing loading dots, as in the reference
    for k, (col, ph) in enumerate(((LIME, 0.0), ("#68d888", 0.33), ("#9a9aa0", 0.66))):
        u = ((t - T_FIND) * 1.6 + ph) % 1.0
        y = by - 360 + 300 * (u * u)
        x = bx - 120 + 110 * k + 30 * math.sin(t * 2 + k)
        r = 34 if k == 0 else 26
        if u < 0.9:
            glow_blob(c, x, y, r * 2.2, col, 0.35)
            G.circle(c, x, y, r * (1 - 0.3 * u), G.P(col, 0.95))
    # the cravings fall in
    for k, (name, td) in enumerate(zip(CHIPS, T_DROPS)):
        u = (t - (td - 0.4)) / 0.4
        if u < 0 or u > 1.35:
            continue
        y = lerp(by - 520, by + 40, clamp(u) ** 2)
        x = bx - 60 + 60 * k
        s = 1.0 if u < 1 else max(0.0, 1 - (u - 1) / 0.35)
        c.save()
        clip = skia.Path()
        clip.addCircle(x, y, 78 * s)
        c.clipPath(clip, skia.ClipOp.kIntersect, True)
        draw_cover(c, name, x - 80, y - 80, 160, 160, min_w=300)
        c.restore()
        G.circle(c, x, y, 78 * s, G.P(WHITE, 0.9, stroke=6))
        if 1.0 <= u < 1.35:
            v = (u - 1) / 0.35
            for j in range(10):
                a = j / 10 * math.pi * 2 + k
                rr_ = 40 + 160 * out_cubic(v)
                G.circle(c, bx - 60 + 60 * k + math.cos(a) * rr_, by - 20 - abs(math.sin(a)) * rr_ * 0.8, 9 * (1 - v),
                         G.P(GLOW[j % 7], 1 - v))
    # the bowl: an orange half disc and a chopstick
    with G.xf(c, bx, by, rot=ang):
        path = skia.Path()
        path.addArc(skia.Rect.MakeXYWH(-br, -br, 2 * br, 2 * br), 0, 180)
        path.close()
        c.drawPath(path, G.P(ORANGE))
        c.drawLine(br * 0.98, 0, br * 1.75, -br * 0.18, G.P(INK, 1, stroke=3.2, cap="round"))
        G.circle(c, br * 1.75, -br * 0.18, 9, G.P(INK))
    # something special rises
    if t >= T_RISE:
        u = clamp((t - T_RISE) / 0.5)
        e = out_cubic(u)
        sx, sy = bx, by - 60 - 360 * e
        r = 30 + 90 * e
        glow_blob(c, sx, sy, r * 3.2, GOLD, 0.55)
        for k in range(6):
            glow_blob(c, sx + 60 * math.cos(k + t * 3), sy + 60 * math.sin(k + t * 3), r * 1.6, GLOW[k], 0.35)
        pts = G.star_points(4, r, r * 0.28, rot=45 * e, cx=sx, cy=sy)
        c.drawPath(G.poly(pts), G.P(WHITE))
        c.drawPath(G.poly(pts), G.P(GOLD, 1, stroke=3))


# ---------------------------------------------------------------- closing lines

ROLL = [("pizza", "pizza"), ("sushi", "sushi"), ("ramen", "ramen"), ("something special", None)]


def crave(c, t):
    """You were craving pizza / sushi / ramen / something special. Now your table is waiting."""
    f = ui(66, 460)
    lead = "You were craving"
    lw = f.width(lead + " ")
    idx = sum(1 for tr in T_ROLL if t >= tr)
    word, chip = ROLL[idx]
    ww = f.width(word) + (92 if chip else 0)
    x0 = 960 - (lw + ww) / 2
    rise = snap(clamp((t - T_WAIT) / 0.4))
    y = 520 - 70 * rise
    # the lead, word by word, the way the reference writes it
    x = x0
    for k, wd in enumerate(lead.split(" ")):
        u = clamp((t - T_CRAVE - 0.1 * k) / 0.3)
        T(c, wd, x, y + 14 * (1 - out_cubic(u)), f, G.mixc(FAINT, INK, u), a=u)
        x += f.width(wd + " ")
    # the rolling slot
    prev_t = T_ROLL[idx - 1] if idx > 0 else T_CRAVE + 0.25
    u = clamp((t - prev_t) / 0.22)
    with G.clip_rect(c, x - 10, y - 100, 1400, 140):
        if idx > 0 and u < 1:
            pw, pc = ROLL[idx - 1]
            _slot(c, pw, pc, x, y - 110 * out_cubic(u), f, 1 - u, t)
        _slot(c, word, chip, x, y + 110 * (1 - out_cubic(u)), f, u, t)
    if t >= T_WAIT:
        g = ui(66, 460)
        words = "Now your table is waiting.".split(" ")
        total = sum(g.width(w + " ") for w in words) - g.width(" ")
        x = 960 - total / 2
        for k, wd in enumerate(words):
            v = clamp((t - T_WAIT - 0.1 - 0.12 * k) / 0.3)
            gap = 40 * (1 - out_cubic(v))
            T(c, wd, x + gap * k, y + 120, g, G.mixc(FAINT, INK, v), a=v)
            x += g.width(wd + " ")


def _slot(c, word, chip, x, y, f, a, t):
    if chip:
        c.save()
        clip = skia.Path()
        clip.addCircle(x + 36, y - 24, 36)
        c.clipPath(clip, skia.ClipOp.kIntersect, True)
        draw_cover(c, chip, x, y - 60, 72, 72, alpha=a, min_w=200)
        c.restore()
        T(c, word, x + 92, y, f, INK, a=a)
    else:
        path = f.shape(word).path(x, y)
        glow = skia.Paint(AntiAlias=True)
        glow.setShader(G.linear_grad(x, 0, x + f.width(word), 0, GLOW[:6]))
        glow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
        glow.setAlphaf(0.7 * a)
        c.drawPath(path, glow)
        p = skia.Paint(AntiAlias=True)
        p.setShader(G.linear_grad(x, 0, x + f.width(word), 0, ["#c2358c", "#e8703a", "#7cc242", "#2fb07a", "#4f72e8"]))
        p.setAlphaf(a)
        c.drawPath(path, p)
