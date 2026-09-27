"""The end, in the spot's own light: gold ribbons gather over the light-green ground, burst on the downbeat
into a white frame edged in light with the name and the address inside, then fold back into a gold orb that
signs the film: MADE BY VEEE."""
import math
from functools import lru_cache

import skia

from engine import gfx as G
from engine.core import clamp, lerp, snap, in_out_cubic, out_cubic, out_back, noise1
from .look import (F, T, ui, serif, WHITE, INK, GOLD, GOLD_DEEP, GOLD_PALE, GOLD_INK, GREEN_MID, SHADOW,
                   MARDI, glow_rrect, glow_blob, ground, rr)
from .score import T_OFF, T_CREDIT, CX

NAME = "Arnaud’s"
NAME_SIZE = 250
NAME_BASE = 590
FRAME = (CX - 660, 250, 1320, 560, 110)          # x, y, w, h, corner radius


# ---------------------------------------------------------------- light

def aurora(c, t, gather, a=1.0, t0=0.0):
    """Five ribbons of light swing in from the edges and pull together towards the centre."""
    if a <= 0:
        return
    with G.layer(c, alpha=a):
        for k, col in enumerate([GOLD_DEEP, GOLD, WHITE, GOLD_PALE, GOLD]):
            ak = k * 2 * math.pi / 5 + 0.4 + 0.25 * (t - t0)
            reach = lerp(1500, 60, gather)
            p0 = (CX + math.cos(ak) * reach * 1.3, 540 + math.sin(ak) * reach * 0.8)
            p3 = (CX + math.cos(ak + 2.4) * reach * 1.3, 540 + math.sin(ak + 2.4) * reach * 0.8)
            wob = 260 * (1 - gather) + 40
            c1 = (CX + wob * noise1(t * 0.9 + k, 1), 540 + wob * noise1(t * 0.9 + k, 2))
            c2 = (CX + wob * noise1(t * 0.9 + k, 3), 540 + wob * noise1(t * 0.9 + k, 4))
            path = skia.Path()
            path.moveTo(*p0)
            path.cubicTo(*c1, *c2, *p3)
            p = skia.Paint(AntiAlias=True)
            p.setStyle(skia.Paint.kStroke_Style)
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeWidth(lerp(150, 60, gather))
            p.setColor4f(G.c4(col, 0.5))
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, lerp(70, 30, gather)))
            c.drawPath(path, p)
            q = skia.Paint(p)
            q.setStrokeWidth(lerp(14, 6, gather))
            q.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
            q.setColor4f(G.c4(G.mixc(col, "#ffffff", 0.45), 0.7))
            c.drawPath(path, q)


def blob_path(x, y, r, t):
    p = skia.Path()
    n = 72
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        rr_ = r * (1 + 0.07 * noise1(math.cos(a) * 1.3 + t * 1.6, 5) + 0.05 * noise1(math.sin(a) * 1.7 - t * 1.2, 6))
        px, py = x + rr_ * math.cos(a), y + rr_ * math.sin(a)
        if i == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    p.close()
    return p


def orb(c, x, y, r, t, a=1.0):
    """Liquid light: a wobbling ball of gold turning inside itself."""
    if r <= 0.5 or a <= 0:
        return
    glow_blob(c, x, y, r * 3.4, WHITE, 0.45 * a)
    glow_blob(c, x + r * 0.4, y + r * 0.2, r * 2.4, GOLD, 0.35 * a)
    glow_blob(c, x - r * 0.3, y - r * 0.3, r * 2.0, GOLD_PALE, 0.3 * a)
    c.drawCircle(x, y + r * 0.3, r * 1.02, G.P(SHADOW, 0.22 * a, blur=r * 0.25))
    m = skia.Matrix()
    m.setRotate(t * 160, x, y)
    sh = skia.GradientShader.MakeSweep(x, y, [G.cint(col, a) for col in (GOLD_DEEP, GOLD, GOLD_PALE, GREEN_MID, GOLD,
                                                                          GOLD_DEEP)],
                                       None, skia.TileMode.kClamp, 0, 360, 0, m)
    p = skia.Paint(AntiAlias=True)
    p.setShader(sh)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.08))
    c.drawPath(blob_path(x, y, r, t), p)
    glow_blob(c, x - r * 0.28, y - r * 0.32, r * 0.75, "#ffffff", 0.55 * a)
    G.circle(c, x - r * 0.34, y - r * 0.4, r * 0.12, G.P("#ffffff", 0.8 * a, blur=r * 0.05))


def light_frame(c, x, y, w, h, r, t, a=1.0, fill=None, fill_a=1.0, line_a=0.85):
    """The frame of light: a turning parade glow, a crisp inner line, an optional fill."""
    if a <= 0:
        return
    glow_rrect(c, x, y, w, h, r, t, a=a, spread=46, width=40, speed=70)
    glow_rrect(c, x, y, w, h, r, t + 1.3, a=0.8 * a, spread=14, width=10, speed=70)
    if fill:
        c.drawRRect(rr(x, y, w, h, r), G.P(fill, fill_a * a))
    c.drawRRect(rr(x, y, w, h, r), G.P(GOLD, line_a * a, stroke=2.2))


def pulse(t, beats=(0.95, 1.45, 1.7, 1.95), decay=0.12):
    v = 0.0
    for b in beats:
        if t >= b:
            v = max(v, math.exp(-(t - b) / decay))
    return v


# ---------------------------------------------------------------- the name

@lru_cache(maxsize=1)
def name_run():
    return serif(NAME_SIZE).shape(NAME)


def name(c, t, t0, a=1.0, sweep_t=None):
    run = name_run()
    f = serif(NAME_SIZE)
    x0 = CX - run.width / 2

    def letters(cc):
        for i, gid, gx, adv in run.glyphs():
            u = clamp((t - t0 - 0.05 * i) / 0.4)
            if u <= 0:
                continue
            e = out_cubic(u)
            with G.xf(cc, x0 + gx + adv / 2, NAME_BASE, s=0.92 + 0.08 * e):
                G.glyph(cc, f, gid, -adv / 2, 70 * (1 - e), G.P(GOLD, 0.3 * u * a, blur=18 * (1 - e) + 6))
                G.glyph(cc, f, gid, -adv / 2, 70 * (1 - e), G.P(INK, u * a))

    su = None if sweep_t is None else (t - sweep_t) / 0.7
    if su is not None and 0 < su < 1:
        G.light_sweep(c, letters, x0 - 200, x0 + run.width + 200, NAME_BASE - 100, su, colors=MARDI,
                      width=160, angle=22.0, strength=0.95)
    else:
        letters(c)


def tagline(c, t, t0, text, a=1.0, y=NAME_BASE + 104, size=30):
    u = clamp((t - t0) / 0.5)
    if u <= 0:
        return
    e = out_cubic(u)
    f = ui(size, 640)
    tr = lerp(0.8, 0.42, e) if len(text) < 40 else lerp(0.6, 0.3, e)
    T(c, text, CX, y, f, GOLD_INK, a=a * u, align=0.5, tracking=tr)


def night(c, t):
    """The end sits on the same light-green ground as the rest of the film."""
    ground(c, t)


# ---------------------------------------------------------------- the end

def outro(c, t, t0):
    """The orb comes back, bursts on the downbeat into the frame, the name and the address."""
    night(c, t)
    k = t - t0
    gather = in_out_cubic(clamp((k + 0.35) / 0.4))
    aurora(c, t, gather, a=clamp(1 - k / 0.5), t0=t0)
    if k < 0.05:
        orb(c, CX, 530, 118 * (1 + 0.2 * pulse(t, (t0 - 0.25,))), t)
    off = clamp((t - T_OFF) / 0.28)
    fx, fy, fw, fh, fr = FRAME
    u = clamp(k / 0.5)
    e = out_back(u, 1.3) if u < 1 else 1.0
    size = 236
    w, h = lerp(size, fw, e), lerp(size, fh, e)
    r = lerp(size / 2, fr, clamp(e))
    # at T_OFF the frame folds back into an orb that drifts to the maker's mark
    oe = snap(off)
    w, h = lerp(w, 236, oe), lerp(h, 236, oe)
    r = lerp(r, 118, oe)
    x, y = CX - w / 2, lerp(fy, 530 - 118, oe) if e >= 1 else 530 - h / 2
    if e < 1:
        y = 530 - h / 2 + lerp(0, fy + fh / 2 - 530, clamp(e))
    if off < 1:
        if 0 <= k < 0.6:
            v = k / 0.6
            G.circle(c, CX, 530, 120 + 900 * out_cubic(v), G.P(WHITE, 0.7 * (1 - v), stroke=6 * (1 - v) + 1, blur=4))
        c.drawRRect(rr(x + 10, y + 30, w, h, r), G.P(SHADOW, 0.18 * (1 - off), blur=40))
        light_frame(c, x, y, w, h, r, t, a=1.0 - off, fill=WHITE, fill_a=1.0)
        fade = 1 - off
        name(c, t, t0 + 0.08, a=fade, sweep_t=t0 + 1.0)
        tagline(c, t, t0 + 0.55, "813 BIENVILLE ST   ·   FRENCH QUARTER   ·   NEW ORLEANS", a=fade, size=26)
        us = clamp((t - t0 - 0.9) / 0.5) * fade
        if us > 0:
            T(c, "Tonight, something special.", CX, fy + fh + 110, F("serif-italic", 48), INK, a=us, align=0.5)
    if off > 0:
        credit(c, t)


def credit(c, t):
    """The frame folds into an orb, the orb becomes the maker's mark: MADE BY VEEE."""
    off = snap(clamp((t - T_OFF) / 0.28))
    move = in_out_cubic(clamp((t - T_CREDIT) / 0.45))
    ox = lerp(CX, CX - 470, move)
    oy = 540
    r = lerp(118, 96, move) * (1 + 0.12 * pulse(t, (T_CREDIT,), 0.15))
    orb(c, ox, oy, r * off, t)
    u = clamp((t - T_CREDIT - 0.15) / 0.5)
    if u <= 0:
        return
    e = out_cubic(u)
    fm = ui(34, 700)
    T(c, "MADE BY", CX - 330, oy - 70 + 20 * (1 - e), fm, GOLD_INK, a=u, tracking=0.5)
    fv = F("archivo", 250, wght=850, wdth=118)
    run = fv.shape("VEEE")
    x0 = CX - 340
    base = oy + 120

    def word(cc):
        for i, gid, gx, adv in run.glyphs():
            v = clamp((t - T_CREDIT - 0.2 - 0.07 * i) / 0.35)
            if v <= 0:
                continue
            ev = out_back(v, 1.4)
            p = skia.Paint(AntiAlias=True)
            ox = gx + adv / 2          # the gradient spans the whole word, in this glyph's own coordinates
            p.setShader(G.linear_grad(-ox, 0, run.width - ox, 0, MARDI))
            p.setAlphaf(clamp(v))
            with G.xf(cc, x0 + gx + adv / 2, base, s=ev):
                G.glyph(cc, fv, gid, -adv / 2, 14, G.P(SHADOW, 0.3 * clamp(v), blur=18))
                G.glyph(cc, fv, gid, -adv / 2, 0, G.P(WHITE, 0.6 * clamp(v), blur=22))
                G.glyph(cc, fv, gid, -adv / 2, 0, p)

    su = (t - T_CREDIT - 0.9) / 0.8
    if 0 < su < 1:
        G.light_sweep(c, word, x0 - 200, x0 + run.width + 200, base - 100, su, colors=("#ffffff",), width=140,
                      angle=22.0, strength=0.7)
    else:
        word(c)
