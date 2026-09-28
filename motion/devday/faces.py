"""The teaser's characters: a flat disc and two eyes drawn like typed glyphs (* o - > < + x ^ / \\), thick black
strokes (white on the dark face). The eyes sit on a sphere, so a face can turn its head, look up or away, and an eye
that goes round the edge thins out and disappears behind it."""
import math
from functools import lru_cache

import skia

from engine import gfx as G
from engine.core import clamp
from .look import F, BLACK, WHITE, DARK

FONT_EYES = set("$?!321zZ@#%&")


def _line(p, x0, y0, x1, y1):
    p.moveTo(x0, y0)
    p.lineTo(x1, y1)


@lru_cache(maxsize=None)
def stroke_eye(kind):
    """The glyph as a centre-line path in a unit box (strokes are applied when drawn)."""
    p = skia.Path()
    if kind == "*":
        for ang in (0, 60, 120):
            a = math.radians(ang)
            _line(p, -0.46 * math.cos(a), -0.46 * math.sin(a), 0.46 * math.cos(a), 0.46 * math.sin(a))
    elif kind == "o":
        p.addOval(skia.Rect.MakeLTRB(-0.29, -0.35, 0.29, 0.35))
    elif kind == "O":
        p.addOval(skia.Rect.MakeLTRB(-0.36, -0.42, 0.36, 0.42))
    elif kind == "-":
        _line(p, -0.33, 0.0, 0.33, 0.0)
    elif kind == "=":
        _line(p, -0.33, -0.14, 0.33, -0.14)
        _line(p, -0.33, 0.14, 0.33, 0.14)
    elif kind == ">":
        p.moveTo(-0.42, -0.38)
        p.lineTo(0.42, 0.0)
        p.lineTo(-0.42, 0.38)
    elif kind == "<":
        p.moveTo(0.42, -0.38)
        p.lineTo(-0.42, 0.0)
        p.lineTo(0.42, 0.38)
    elif kind == "+":
        _line(p, -0.36, 0.0, 0.36, 0.0)
        _line(p, 0.0, -0.36, 0.0, 0.36)
    elif kind == "x":
        _line(p, -0.3, -0.3, 0.3, 0.3)
        _line(p, -0.3, 0.3, 0.3, -0.3)
    elif kind == "^":
        p.moveTo(-0.4, 0.42)
        p.lineTo(0.0, -0.42)
        p.lineTo(0.4, 0.42)
    elif kind == "v":
        p.moveTo(-0.4, -0.42)
        p.lineTo(0.0, 0.42)
        p.lineTo(0.4, -0.42)
    elif kind == "/":
        _line(p, -0.25, 0.42, 0.25, -0.42)
    elif kind == "\\":
        _line(p, -0.25, -0.42, 0.25, 0.42)
    elif kind == "n":                                   # a happy closed eye, round
        p.addArc(skia.Rect.MakeLTRB(-0.36, -0.2, 0.36, 0.52), 195, 150)
    elif kind == "u":
        p.addArc(skia.Rect.MakeLTRB(-0.36, -0.52, 0.36, 0.2), 15, 150)
    elif kind == "|":
        _line(p, 0.0, -0.4, 0.0, 0.4)
    return p


@lru_cache(maxsize=None)
def font_eye(kind):
    """A glyph from the font, centred in a unit box, and how thick its stems already are there."""
    f = F("gsans-medium", 100)
    run = f.shape(kind)
    path = skia.Path(f.glyph_path(run.gids[0]))
    b = path.getBounds()
    h = 1.0 if kind in "$" else 0.86
    s = h / max(b.height(), 1e-3)
    m = skia.Matrix()
    m.setScale(s, s)
    m.preTranslate(-b.centerX(), -b.centerY())
    path.transform(m)
    return path, 11.0 * s                                # Google Sans Medium stems are about 11 units at 100


def heart_path():
    p = skia.Path()
    p.moveTo(0, 0.42)
    p.cubicTo(-0.55, 0.05, -0.5, -0.45, -0.22, -0.42)
    p.cubicTo(-0.08, -0.4, 0.0, -0.28, 0.0, -0.2)
    p.cubicTo(0.0, -0.28, 0.08, -0.4, 0.22, -0.42)
    p.cubicTo(0.5, -0.45, 0.55, 0.05, 0.0, 0.42)
    p.close()
    return p


def sparkle_path(k=0.28):
    p = skia.Path()
    p.moveTo(0, -0.5)
    p.quadTo(k * 0.25, -k * 0.25, 0.5, 0)
    p.quadTo(k * 0.25, k * 0.25, 0, 0.5)
    p.quadTo(-k * 0.25, k * 0.25, -0.5, 0)
    p.quadTo(-k * 0.25, -k * 0.25, 0, -0.5)
    p.close()
    return p


HEART = heart_path()
SPARKLE = sparkle_path()


def eye(c, kind, x, y, g, w, col, a=1.0, sx=1.0, sy=1.0, rot=0.0):
    """One glyph eye of size g and stroke w centred at (x, y)."""
    if a <= 0 or g <= 0.5 or sx <= 0.01 or sy <= 0.01:
        return
    c.save()
    c.translate(x, y)
    if rot:
        c.rotate(rot)
    c.scale(g * sx, g * sy)
    lw = w / g
    if kind in FONT_EYES:
        path, stem = font_eye(kind)
        p = G.P(col, a)
        extra = lw - stem
        if extra > 0:
            p.setStyle(skia.Paint.kStrokeAndFill_Style)
            p.setStrokeWidth(extra)
            p.setStrokeJoin(skia.Paint.kRound_Join)
        c.drawPath(path, p)
    elif kind == ".":
        c.drawCircle(0, 0, 0.16, G.P(col, a))
    elif kind == "♥":
        c.drawPath(HEART, G.P(col, a))
    elif kind == "✦":
        c.drawPath(SPARKLE, G.P(col, a))
    else:
        p = G.P(col, a, stroke=lw)
        p.setStrokeJoin(skia.Paint.kMiter_Join)
        p.setStrokeMiter(6.0)
        c.drawPath(stroke_eye(kind), p)
    c.restore()


def eye_colour(col):
    return WHITE if col == DARK else BLACK


def face(c, x, y, r, col, eyes=("o", "o"), yaw=0.0, pitch=0.0, roll=0.0, eye_col=None, a=1.0, sx=1.0, sy=1.0,
         sep=0.52, lat=-0.03, g=0.45, w=0.085, blink=0.0, mouth=None, eye_rot=0.0, disc=True, clip=True):
    """A face of radius r at (x, y). yaw turns the head (radians, + to the viewer's right), pitch tilts it up,
    roll leans it (degrees). blink squashes the eyes shut."""
    if a <= 0 or r <= 0.5:
        return
    c.save()
    c.translate(x, y)
    if roll:
        c.rotate(roll)
    if sx != 1.0 or sy != 1.0:
        c.scale(sx, sy)
    if disc:
        c.drawCircle(0, 0, r, G.P(col, a))
    ec = eye_col or eye_colour(col)
    if clip:
        cp = skia.Path()
        cp.addCircle(0, 0, r * 0.995)
        c.clipPath(cp, doAntiAlias=True)
    for side, kind in ((-1, eyes[0]), (1, eyes[1])):
        if not kind:
            continue
        lon = side * sep + yaw
        la = lat + pitch
        depth = math.cos(lon) * math.cos(la)
        if depth <= 0.02:
            continue
        ex = r * math.sin(lon) * math.cos(la)
        ey = -r * math.sin(la)
        fs = clamp(math.cos(lon) * 1.15)
        eye(c, kind, ex, ey, g * r, w * r, ec, a * clamp((fs - 0.12) / 0.25), sx=fs, sy=math.cos(la) * (1 - 0.88 * blink),
            rot=eye_rot * side)
    if mouth:
        la = lat + pitch - 0.5
        lon = yaw
        depth = math.cos(lon) * math.cos(la)
        if depth > 0.02:
            eye(c, mouth, r * math.sin(lon) * math.cos(la), -r * math.sin(la), g * r * 0.8, w * r, ec,
                a * clamp(depth * 6), sx=clamp(math.cos(lon) * 1.15), sy=math.cos(la))
    c.restore()
