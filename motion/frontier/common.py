"""Palette, type helpers and small reusable pieces for THE FRONTIER."""
import math
from bisect import bisect_right

import skia

from engine import gfx as G
from engine import logos as LG
from engine.core import clamp, lerp, snap, out_expo, W, H, CX, CY
from .score import KICKS

INK = "#0a0a0b"
PAPER = "#f1eee7"
WHITE = "#f4f2ec"
GREEN = "#1ef2a4"      # ASTRA / OpenAI
BLUE = "#2f45ff"       # GEMINI / Google DeepMind
VIOLET = "#c9b8ff"
CLAY = "#d97757"       # FABLE / Anthropic
BOOK = "#171411"

CONTENDERS = [
    dict(name="ASTRA", ver="6", lab="OPENAI", est="2015", base="SAN FRANCISCO", color=GREEN),
    dict(name="GEMINI", ver="3m", lab="GOOGLE DEEPMIND", est="2010", base="LONDON", color=BLUE),
    dict(name="FABLE", ver="5.1", lab="ANTHROPIC", est="2021", base="SAN FRANCISCO", color=CLAY),
]


def lab_logo(c, idx, x, y, size, alpha=1.0, on_light=False, rot=0.0):
    """The lab's mark: OpenAI blossom, Google G, Anthropic A\\."""
    ink = "#141413" if on_light else WHITE
    if idx == 0:
        LG.mark(c, "openai", x, y, size, G.P(ink, alpha), rot)
    elif idx == 1:
        LG.google(c, x, y, size, alpha)
    else:
        LG.mark(c, "anthropic", x, y, size, G.P(ink if on_light else WHITE, alpha), rot)


def model_logo(c, idx, x, y, size, alpha=1.0, rot=0.0, t=0.0, progress=1.0, on_light=False):
    """The model's mark: the blossom for ASTRA, the sparkle for GEMINI, the Claude spark for FABLE."""
    if idx == 0:
        LG.mark(c, "openai", x, y, size, G.P("#141413" if on_light else WHITE, alpha), rot)
    elif idx == 1:
        LG.gemini(c, x, y, size, alpha, rot)
    else:
        LG.claude(c, x, y, size, CLAY, alpha, progress, rot, t)


def kick_env(t, decay=0.09):
    i = bisect_right(KICKS, t) - 1
    if i < 0:
        return 0.0
    return math.exp(-(t - KICKS[i]) / decay)


def fill(c, color, a=1.0):
    c.drawRect(skia.Rect.MakeWH(W, H), G.P(color, a))


def fit(text, fam, width, tracking=0.0, **axes):
    f = G.Font(fam, 100, **axes)
    w = f.width(text, tracking)
    return G.Font(fam, 100 * width / max(w, 1e-3), **axes)


def with_alpha(paint, a):
    p = skia.Paint(paint)
    p.setAlphaf(max(0.0, min(1.0, paint.getAlphaf() * a)))
    return p


def draw_glyphs(c, run, x0, y0, paints, fn=None):
    """Draw a shaped run glyph by glyph. fn(i) -> (dx, dy, sx, sy, rot, alpha); pivot is the
    glyph's baseline centre. paints is a paint or a list of per-glyph paints."""
    for i, gid, gx, adv in run.glyphs():
        dx, dy, sx, sy, rot, a = fn(i) if fn else (0, 0, 1, 1, 0, 1)
        if a <= 0.002 or sx == 0 or sy == 0:
            continue
        p = paints[i] if isinstance(paints, (list, tuple)) else paints
        if a < 1:
            p = with_alpha(p, a)
        c.save()
        c.translate(x0 + gx + adv / 2 + dx, y0 + dy)
        if rot:
            c.rotate(rot)
        if sx != 1 or sy != 1:
            c.scale(sx, sy)
        G.glyph(c, run.font, gid, -adv / 2, 0, p)
        c.restore()


def card(c, x, y, t, t0, idx, color, ink=WHITE, align=0.0, big=True):
    """The fighter card: contender number, name + version, then LAB / EST. / BASE rows,
    each decoding in on successive eighth notes after t0."""
    k = CONTENDERS[idx]
    if t < t0:
        return
    f_lab = G.Font("mono", 17, wght=720)
    f_row = G.Font("mono", 17, wght=430)
    width = 560
    xl = x - width * align
    u = clamp((t - t0) / 0.35)
    G.text(c, G.scramble(f"CONTENDER {idx + 1:02d} / 03", u, idx, t), xl, y, f_lab, G.P(color), tracking=0.18)
    yy = y + 22
    if big:
        f_name = G.Font("archivo", 76, wght=900, wdth=118)
        f_ver = G.Font("fraunces-italic", 84, wght=500, opsz=144, SOFT=50)
        a = clamp((t - t0 - 0.08) / 0.2)
        run = f_name.shape(k["name"])
        rise = 30 * (1 - snap(a))
        with G.clip_rect(c, xl - 10, yy, width + 200, 100):
            run.draw(c, xl, yy + 76 + rise, G.P(ink, a))
            G.text(c, k["ver"], xl + run.width + 18, yy + 80 + rise, f_ver, G.P(color, a))
        lg = snap(clamp((t - t0 - 0.12) / 0.3))
        if lg > 0:
            lab_logo(c, idx, xl + width - 34, yy + 46, 64 * lg, lg, on_light=(ink != WHITE), rot=-90 * (1 - lg))
        yy += 112
    ln = snap(clamp((t - t0 - 0.1) / 0.4))
    c.drawLine(xl, yy, xl + width * ln, yy, G.P(ink, 0.5, stroke=1.5))
    rows = [("LAB", k["lab"]), ("EST.", k["est"]), ("BASE", k["base"])]
    for r, (key, val) in enumerate(rows):
        tr = t0 + 0.16 + r * 0.2
        if t < tr:
            continue
        pr = clamp((t - tr) / 0.3)
        ry = yy + 40 + r * 34
        G.text(c, key, xl, ry, f_row, G.P(ink, 0.55 * pr), tracking=0.18)
        G.text(c, G.scramble(val, pr, r * 13 + idx, t), xl + 150, ry, f_lab, G.P(ink, pr), tracking=0.14)
        c.drawLine(xl, ry + 12, xl + width * snap(pr), ry + 12, G.P(ink, 0.12, stroke=1.0))
