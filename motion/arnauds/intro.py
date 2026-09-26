"""The intro: a chandelier draws itself in brass line and lights up bulb by bulb on the sixteenths; on the bar
its crystals fly off and settle on the outline of the name, which inks in under a light sweep."""
import math
from functools import lru_cache

import numpy as np
import skia

from engine import gfx as G
from engine.core import clamp, lerp, snap, in_out_cubic, out_cubic, hash01, noise1
from .look import (F, T, ui, serif, WHITE, INK, GREY, GLOW, GOLD, glow_blob)
from .score import T_LINES, T_BULBS, T_MORPH, T_NAME, T_INK, T_TAG, T_SWEEP, CX

BRASS = "#9a7b4c"
AXIS_X = CX
TIERS = [(318, 150, 6), (468, 300, 10), (620, 440, 14)]     # (y, radius, arms)
SPIN = 0.35                                                 # rad/s, the chandelier turns slowly
NAME = "Arnaud’s"
NAME_SIZE = 330
NAME_BASE = 640


# ---------------------------------------------------------------- the chandelier, in 3D

def _ang(k, i, t):
    n = TIERS[k][2]
    return 2 * math.pi * i / n + SPIN * t + k * 0.3


def bulb_pos(k, i, t):
    y, r, n = TIERS[k]
    a = _ang(k, i, t)
    x = AXIS_X + r * math.cos(a)
    z = math.sin(a)                      # +1 is nearest the viewer
    return x, y + r * 0.18 * z - 18, z


def bulb_time(k, i):
    """Which sixteenth lights this bulb: the tiers light top to bottom, round each ring."""
    order = sum(TIERS[j][2] for j in range(k)) + i
    total = sum(n for _, _, n in TIERS)
    return T_BULBS[min(len(T_BULBS) - 1, int(order / total * len(T_BULBS)))]


@lru_cache(maxsize=1)
def crystals():
    """Every glass piece the name will be made of: (tier, index, kind, sub)."""
    out = []
    for k, (_, _, n) in enumerate(TIERS):
        for i in range(n):
            out.append((k, i, "bulb", 0))
            for d in range(3):
                out.append((k, i, "drop", d))
            for b in range(5):
                out.append((k, i, "bead", b))
    return out


def crystal_pos(item, t):
    k, i, kind, sub = item
    x, y, z = bulb_pos(k, i, t)
    if kind == "bulb":
        return x, y - 8, z
    if kind == "drop":
        return x, y + 32 + sub * 27, z
    # beads hang in a swag between this bulb and the next
    x2, y2, z2 = bulb_pos(k, (i + 1) % TIERS[k][2], t)
    u = (sub + 1) / 6
    sag = 56 * math.sin(math.pi * u) + 12
    return lerp(x, x2, u), lerp(y, y2, u) + 22 + sag, lerp(z, z2, u)


def chandelier_lines(c, t, a):
    """Brass: the chain, the column, and an arm to every bulb."""
    if a <= 0:
        return
    p = G.P(BRASS, 0.85 * a, stroke=2.4, cap="round")
    draw = snap(clamp((t - T_LINES[0]) / (T_LINES[1] - T_LINES[0])))
    path = skia.Path()
    path.moveTo(AXIS_X, -20)
    path.lineTo(AXIS_X, 200)
    c.drawPath(path, G.P(BRASS, 0.85 * a, stroke=2.4, cap="round", effect=G.trim(0, min(1.0, draw * 2.5))))
    c.drawOval(skia.Rect.MakeXYWH(AXIS_X - 52, 200, 104, 32), G.P(BRASS, a * clamp(draw * 3 - 0.5), stroke=3.0))
    col = skia.Path()
    col.moveTo(AXIS_X, 232)
    col.lineTo(AXIS_X, 690)
    c.drawPath(col, G.P(BRASS, 0.85 * a, stroke=3.0, cap="round", effect=G.trim(0, clamp(draw * 1.6 - 0.2))))
    for k, (ty, r, n) in enumerate(TIERS):
        for i in range(n):
            x, y, z = bulb_pos(k, i, t)
            arm = skia.Path()
            arm.moveTo(AXIS_X, ty + 40)
            arm.cubicTo(lerp(AXIS_X, x, 0.35), ty + 84, lerp(AXIS_X, x, 0.8), y + 56, x, y + 12)
            local = clamp((draw - 0.15 - 0.06 * k) / 0.55)
            depth = 0.55 + 0.45 * (z + 1) / 2
            c.drawPath(arm, G.P(BRASS, 0.9 * a * depth, stroke=2.8 + 1.6 * depth, cap="round",
                                effect=G.trim(0, snap(local))))
            if local >= 1:
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 12, y - 4, 24, 20), 5, 5),
                            G.P(BRASS, a * depth, stroke=2.2))


def draw_crystal(c, x, y, z, kind, lit, idx, a, t):
    depth = 0.5 + 0.5 * (z + 1) / 2
    col = GLOW[idx % (len(GLOW) - 1)]
    if kind == "bulb":
        if lit > 0:
            flick = 0.85 + 0.15 * noise1(t * 6 + idx, 2.0)
            glow_blob(c, x, y, 96 * depth * lit, col, 0.6 * a * lit * flick)
            glow_blob(c, x, y, 36 * depth, "#ffe9b8", 0.95 * a * lit)
            G.circle(c, x, y, 8.5 * depth, G.P("#fffaf0", a))
            G.circle(c, x, y, 8.5 * depth, G.P(GOLD, a * (1 - lit), stroke=2.0))
            if lit > 0 and z > -0.2:
                pop = math.exp(-(t - bulb_time(0, 0)) * 0.0) * (0.6 + 0.4 * flick)
                L = 46 * depth * lit * pop
                p = G.P("#ffe2a8", 0.8 * a * lit, stroke=2.0, blur=1.0)
                c.drawLine(x - L, y, x + L, y, p)
                c.drawLine(x, y - L * 0.6, x, y + L * 0.6, p)
        else:
            G.circle(c, x, y, 6 * depth, G.P(BRASS, 0.9 * a, stroke=1.6))
    else:
        s = (9.5 if kind == "drop" else 5.5) * depth
        pts = [(x, y - s * 1.3), (x + s * 0.7, y), (x, y + s * 1.3), (x - s * 0.7, y)]
        c.drawPath(G.poly(pts), G.P(col, 0.35 * a * max(lit, 0.3)))
        c.drawPath(G.poly(pts), G.P(BRASS, 0.8 * a, stroke=1.1))
        if lit > 0:
            glow_blob(c, x, y, 28 * depth, col, 0.45 * a * lit)


# ---------------------------------------------------------------- the name

@lru_cache(maxsize=1)
def name_run():
    return serif(NAME_SIZE).shape(NAME)


@lru_cache(maxsize=1)
def name_path():
    run = name_run()
    return run.path(CX - run.width / 2, NAME_BASE)


@lru_cache(maxsize=1)
def name_points():
    """Evenly spaced points along the outline of the name, one per crystal."""
    path = name_path()
    n = len(crystals())
    meas = skia.PathMeasure(path, False)
    lens = []
    while True:
        lens.append(meas.getLength())
        if not meas.nextContour():
            break
    total = sum(lens)
    pts = []
    meas = skia.PathMeasure(path, False)
    for L in lens:
        k = max(1, int(round(n * L / total)))
        for j in range(k):
            pos, _ = meas.getPosTan(L * (j + 0.5) / k)
            pts.append((pos.fX, pos.fY))
        if not meas.nextContour():
            break
    pts = pts[:n]
    while len(pts) < n:
        pts.append(pts[len(pts) % max(1, len(pts))])
    return pts


@lru_cache(maxsize=1)
def pairing():
    """Crystal i flies to target pairing()[i]; both sides sorted left to right so the flight reads as a fall."""
    items = crystals()
    src = sorted(range(len(items)), key=lambda i: crystal_pos(items[i], T_MORPH[0])[0])
    tgt = sorted(range(len(name_points())), key=lambda j: name_points()[j][0])
    out = [0] * len(items)
    for a, b in zip(src, tgt):
        out[a] = b
    return out


def morph_u(i, x_src):
    t0 = T_MORPH[0] + 0.28 * clamp((x_src - 560) / 800) + 0.06 * float(hash01(i, 3))
    return t0, t0 + 0.46


def name_fill(c, t, a=1.0, sweep_u=None):
    path = name_path()
    draw = clamp((t - T_INK[0]) / (T_INK[1] - T_INK[0]))
    if draw > 0:
        c.drawPath(path, G.P(INK, a, stroke=2.2, effect=G.trim(0, snap(draw)), join="round"))
    fill = clamp((t - T_INK[0] - 0.25) / 0.35)
    if fill > 0:
        def paint(cc):
            cc.drawPath(path, G.P(INK, a * fill))
        if sweep_u is not None and 0 < sweep_u < 1:
            run = name_run()
            G.light_sweep(c, paint, CX - run.width / 2 - 200, CX + run.width / 2 + 200, NAME_BASE - 120, sweep_u,
                          colors=GLOW[:6], width=160, angle=22.0, strength=0.9)
        else:
            paint(c)


def tagline(c, t, a=1.0):
    u = clamp((t - T_TAG) / 0.5)
    if u <= 0:
        return
    e = out_cubic(u)
    f = ui(28, 600)
    tr = lerp(0.9, 0.42, e)
    s = "EST. 1918   ·   NEW ORLEANS"
    T(c, s, CX, NAME_BASE + 110, f, INK, a=a * u, align=0.5, tracking=tr)
    w = f.width(s, tr)
    L = 120 * e
    c.drawLine(CX - w / 2 - 36 - L, NAME_BASE + 100, CX - w / 2 - 36, NAME_BASE + 100, G.P(GREY, a * u, stroke=1.6))
    c.drawLine(CX + w / 2 + 36, NAME_BASE + 100, CX + w / 2 + 36 + L, NAME_BASE + 100, G.P(GREY, a * u, stroke=1.6))


def backdrop_glow(c, t, a=1.0):
    """Big, slow, soft colour fields, the way the reference lights its white."""
    for k, (col, ox, oy, r) in enumerate(((GLOW[0], -520, -260, 520), (GLOW[4], 560, 300, 560), (GLOW[3], 480, -330, 420),
                                          (GLOW[2], -560, 330, 460))):
        x = CX + ox + 60 * math.sin(t * 0.7 + k)
        y = 540 + oy + 40 * math.cos(t * 0.6 + k * 2)
        glow_blob(c, x, y, r, col, 0.16 * a)


def intro(c, t):
    backdrop_glow(c, t)
    z = 0.93 + 0.07 * out_cubic(clamp(t / 3.6))
    z *= lerp(1.18, 1.0, snap(clamp((t - T_MORPH[0]) / 0.7)))      # close on the chandelier, then back for the name
    c.save()
    c.translate(CX, 540)
    c.scale(z, z)
    c.translate(-CX, -540)
    _intro(c, t)
    c.restore()


def _intro(c, t):
    items = crystals()
    targets = name_points()
    pair = pairing()
    lines_a = 1 - clamp((t - T_MORPH[0]) / 0.45)
    chandelier_lines(c, t, lines_a)
    order = sorted(range(len(items)), key=lambda i: crystal_pos(items[i], min(t, T_MORPH[0]))[2])
    for i in order:
        k, idx, kind, sub = items[i]
        lit = clamp((t - bulb_time(k, idx)) / 0.12)
        if t < T_LINES[0] + 0.1 * k:
            continue
        x0, y0, z0 = crystal_pos(items[i], min(t, T_MORPH[0]))
        t0, t1 = morph_u(i, x0)
        if t < t0:
            show = clamp((t - (T_LINES[0] + 0.25 + 0.08 * k)) / 0.3)
            draw_crystal(c, x0, y0, z0, kind, lit, i, show, t)
            continue
        tx, ty = targets[pair[i]]
        u = in_out_cubic(clamp((t - t0) / (t1 - t0)))
        # a curved flight: out and around, then onto the letter
        mx = lerp(x0, tx, 0.5) + 220 * (float(hash01(i, 7)) - 0.5)
        my = lerp(y0, ty, 0.5) - 120 * float(hash01(i, 9))
        x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * mx + u * u * tx
        y = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * my + u * u * ty
        settle = clamp((t - t1) / 0.6)
        a = 1 - settle * 0.9
        if a <= 0.02:
            continue
        col = GLOW[i % (len(GLOW) - 1)]
        glow_blob(c, x, y, 26 * (1 - 0.5 * settle), col, 0.55 * a)
        G.circle(c, x, y, 3.2 + 1.5 * (1 - u), G.P("#fffaf0" if kind == "bulb" else col, a))
    su = (t - T_SWEEP) / 0.7
    name_fill(c, t, sweep_u=su)
    tagline(c, t)


# ---------------------------------------------------------------- the end: the name again, with its halo

def outro(c, t, t0):
    backdrop_glow(c, t, a=1.2)
    run = name_run()
    f = serif(NAME_SIZE)
    x0 = CX - run.width / 2
    base = NAME_BASE - 40
    # a ring of crystals gathers into a halo around the name, like a chandelier seen side on
    n = 120
    gather = out_cubic(clamp((t - t0) / 0.9))
    for i in range(n):
        a = 2 * math.pi * i / n + 0.35 * (t - t0)
        rx, ry = 820, 190
        hx, hy = CX + rx * math.cos(a), base - 110 + ry * math.sin(a)
        sx = CX + 1400 * (float(hash01(i, 21)) - 0.5) * 1.6
        sy = 540 + 900 * (float(hash01(i, 22)) - 0.5)
        x, y = lerp(sx, hx, gather), lerp(sy, hy, gather)
        depth = 0.55 + 0.45 * (math.sin(a) + 1) / 2
        tw = 0.6 + 0.4 * math.sin(t * 7 + i * 1.7)
        col = GLOW[i % (len(GLOW) - 1)]
        glow_blob(c, x, y, 24 * depth, col, 0.5 * tw * gather)
        G.circle(c, x, y, 3.2 * depth, G.P("#fffaf0" if i % 3 else col, 0.95 * gather))
    # the letters rise in one by one
    def letters(cc):
        for i, gid, gx, adv in run.glyphs():
            u = clamp((t - t0 - 0.25 - 0.05 * i) / 0.45)
            if u <= 0:
                continue
            e = out_cubic(u)
            with G.xf(cc, x0 + gx + adv / 2, base, s=0.9 + 0.1 * e):
                G.glyph(cc, f, gid, -adv / 2, 60 * (1 - e), G.P(INK, u))
    su = (t - t0 - 1.1) / 0.8
    if 0 < su < 1:
        G.light_sweep(c, letters, x0 - 200, x0 + run.width + 200, base - 120, su, colors=GLOW[:6], width=170,
                      angle=22.0, strength=0.9)
    else:
        letters(c)
    ut = clamp((t - t0 - 0.8) / 0.5)
    if ut > 0:
        ft = ui(26, 600)
        tr = lerp(0.8, 0.4, out_cubic(ut))
        T(c, "813 BIENVILLE ST   ·   FRENCH QUARTER   ·   NEW ORLEANS", CX, base + 100, ft, INK, a=ut, align=0.5,
          tracking=tr)
    us = clamp((t - t0 - 1.1) / 0.5)
    if us > 0:
        T(c, "Since 1918. Tonight, something special.", CX, base + 160, F("serif-italic", 40), GREY, a=us, align=0.5)
