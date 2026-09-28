"""AGI WEEK, 0-4.3 s: the wordmarks, the sparkle, the collage.

On black, the labs' wordmarks cut on every click of the intro, each with the model it brings this week on top.
The last one, Gemini, shrinks away; on the drop a white sparkle with an iridescent rim grows out of the dark, opens
from its middle like a portal, and the camera flies through into a collage of the week: the founders' photos, the
models' cards, glossy shapes in the dark."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic
from . import marks as M
from .look import WHITE, T, gs, gsm, inter, serif, rr, blob, card, picture
from .score import FLASH, T_SHRINK, T_DROP, T_HOLE, T_COLLAGE_OUT, T_SEARCH

# the wordmark on each click, and the model it brings this week (None: the wordmark is the model)
SEQUENCE = [("openai", "New model"), ("claude", "Sonnet 5.5"), ("gemini", None), ("grok", "4.8"),
            ("anthropic", "Sonnet 5.5"), ("meta", "Muse"), ("openai", "Agent “O”"), ("grok", "4.8"),
            ("google", "Gemini"), ("claude", "Sonnet 5.5"), ("gemini", None)]
SPARK = "#da7556"


def _lockup(brand):
    """(mark drawer, mark size, text, font, gap, text colour) for a wordmark at its flash size."""
    if brand == "openai":
        f = inter(150, 620)
        return ("openai", f.cap * 1.5, "OpenAI", f, f.size * 0.2)
    if brand == "claude":
        f = serif(170, 560)
        return ("claude", f.cap * 1.55, "Claude", f, f.size * 0.12)
    if brand == "gemini":
        f = gsm(160)
        return ("gemini", f.cap * 1.3, "Gemini", f, f.size * 0.16)
    if brand == "grok":
        f = gsm(160)
        return ("grok", f.cap * 1.75, "Grok", f, f.size * 0.14)
    if brand == "meta":
        f = gsm(160)
        return ("meta", f.cap * 1.95, "Meta", f, f.size * 0.14)
    if brand == "anthropic":
        return (None, 0, "ANTHROPIC", inter(118, 520), 0)
    if brand == "google":
        return (None, 0, "Google", gs(190), 0)
    raise KeyError(brand)


def _draw_mark(c, name, x, y, size, a):
    if name == "openai":
        M.mark(c, "openai", x, y, size, WHITE, a)
    elif name == "claude":
        M.mark(c, "claude", x, y, size, SPARK, a)
    elif name == "gemini":
        M.gemini(c, x, y, size, a)
    elif name == "grok":
        M.grok(c, x, y, size, WHITE, a)
    elif name == "meta":
        M.meta(c, x, y, size, a)


def wordmark(c, brand, cx, cy, a=1.0, model=None):
    """A lab's wordmark centred on (cx, cy): its mark, its name in its own face; the model on top in a pill."""
    name, ms, text, f, gap = _lockup(brand)
    tracking = 0.06 if brand == "anthropic" else 0.0
    tw = f.width(text, tracking)
    mw = 0.0
    if name == "meta":
        mw = ms
    elif name:
        mw = ms * (0.95 if name != "grok" else 1.0)
    total = mw + (gap if name else 0) + tw
    x0 = cx - total / 2
    if name:
        _draw_mark(c, name, x0 + mw / 2, cy, ms, a)
    base = cy + f.cap / 2
    tx = x0 + mw + (gap if name else 0)
    if brand == "google":
        cols = [M.G_BLUE, M.G_RED, M.G_YELLOW, M.G_BLUE, M.G_GREEN, M.G_RED]
        run = f.shape(text)
        for i, gid, gx, adv in run.glyphs():
            G.glyph(c, f, gid, tx + gx, base, G.P(cols[i % len(cols)], a))
    else:
        T(c, text, tx, base, f, WHITE, a, tracking=tracking)
    if model:
        fm = gsm(66) if brand in ("gemini", "grok", "meta", "google") else (serif(72, 540) if brand == "claude"
                                                                              else inter(64, 560))
        pw = fm.width(model) + 84
        ph = 108
        py = cy - f.cap / 2 - 64 - ph
        c.drawRRect(rr(cx - pw / 2, py, pw, ph, ph / 2), G.P(WHITE, 0.13 * a))
        c.drawRRect(rr(cx - pw / 2 + 1, py + 1, pw - 2, ph - 2, ph / 2 - 1), G.P(WHITE, 0.34 * a, stroke=2.5))
        T(c, model, cx, py + ph / 2 + fm.cap / 2, fm, WHITE, a, align=0.5)


def flashes(c, t):
    """The wordmark for the click we are on; the last shrinks away before the drop."""
    i = max(k for k, t0 in enumerate(FLASH) if t >= t0)
    brand, model = SEQUENCE[i]
    if i < len(FLASH) - 1:
        wordmark(c, brand, 960, 540, model=model)
        return
    u = clamp((t - T_SHRINK) / (T_DROP - 0.04 - T_SHRINK))
    e = out_cubic(u)
    s = lerp(1.0, 0.5, e)
    with G.xf(c, 960, 540 + 90 * e, s=s):
        wordmark(c, brand, 0, 0, a=1 - clamp((u - 0.7) / 0.3), model=model)


# ---------------------------------------------------------------- the sparkle and the portal

def sparkle(c, t):
    """On the drop: a white sparkle with an iridescent rim grows out of the dark and opens into the collage."""
    k = max(0.0, t - T_DROP)
    size = 280 * math.exp(k * 5.2)
    rot = -8 + 36 * k
    star = M.mark_path("gemini", 960, 540, size, rot)
    hu = clamp((t - T_HOLE) / 0.3)
    ring = star
    if hu > 0:
        hole = M.mark_path("gemini", 960, 540, size * 0.97 * hu ** 1.25, rot)
        c.save()
        c.clipPath(hole, skia.ClipOp.kIntersect, True)
        collage(c, t)
        c.restore()
        ring = skia.Op(star, hole, skia.PathOp.kDifference_PathOp) or star
    sh = G.radial_grad(960, 540, size * 0.5, ["#ffffff", "#f3f5fb", "#cfd6ea"], stops=[0.0, 0.6, 1.0])
    rim = size * 0.018
    with G.layer(c):
        c.drawPath(ring, G.P(WHITE, 1, shader=sh))
        # the rim: cyan on one side, violet on the other, like light split by glass
        for col, dx in (("#48c7ff", -1.0), ("#a86bff", 1.0)):
            with G.xf(c, dx * rim * 0.6, -dx * rim * 0.3):
                c.drawPath(star, G.P(col, 0.85, stroke=rim, blur=rim * 0.7, blend=G.SCREEN))
    c.drawPath(star, G.P("#7f8cff", 0.35, stroke=rim * 3, blur=rim * 3, blend=G.ADD))


# ---------------------------------------------------------------- the collage

def _tiles():
    """The collage in 3D: (kind, what, x, y, z at T_HOLE, w, h)."""
    photos = [("photo", "amodei", -520, -250, 1250, 520, 356), ("photo", "altman", 560, -300, 1500, 300, 340),
              ("photo", "hassabis", -700, 260, 1700, 290, 330), ("photo", "zuckerberg", 640, 300, 1950, 290, 330),
              ("photo", "musk", 60, -420, 2250, 290, 330), ("photo", "altman", -260, 360, 2700, 250, 290),
              ("photo", "amodei", 480, 60, 3000, 430, 294), ("photo", "musk", -560, -60, 3300, 270, 310),
              ("photo", "hassabis", 280, -380, 3500, 260, 300), ("photo", "zuckerberg", -140, 420, 3800, 260, 300)]
    models = [("model", ("claude", "Sonnet 5.5"), 220, 250, 1400, 380, 132),
              ("model", ("openai", "New model"), -300, 20, 1850, 380, 132),
              ("model", ("openai", "Agent “O”"), 760, -40, 2400, 380, 132),
              ("model", ("grok", "Grok 4.8"), -760, -380, 2600, 380, 132),
              ("model", ("meta", "Muse"), 120, 150, 2900, 330, 132),
              ("model", ("gemini", "Gemini"), -420, -300, 3150, 360, 132),
              ("model", ("claude", "Sonnet 5.5"), 620, 380, 3600, 380, 132)]
    shapes = [("sphere", "#6d7cff", -880, -40, 1600, 120, 120), ("sphere", "#b46cff", 860, 180, 2200, 90, 90),
              ("sphere", "#3fa7ff", -240, -460, 2800, 80, 80), ("star", None, 380, -160, 1800, 90, 90),
              ("star", None, -600, 420, 2500, 70, 70), ("sphere", "#ff8fb1", 300, 470, 3100, 70, 70),
              ("star", None, 700, -420, 3400, 60, 60), ("sphere", "#8f7bff", -900, 250, 3700, 100, 100)]
    return photos + models + shapes


TILES = _tiles()
SPEED = 3000.0
FOCAL = 950.0


def collage(c, t):
    """The camera flies forward through the week's faces and models."""
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#06060a"))
    blob(c, 700, 420, 900, "#2b3a8f", 0.35)
    blob(c, 1300, 700, 800, "#5a2f8f", 0.3)
    dz = SPEED * (t - T_HOLE)
    items = []
    for kind, what, x, y, z0, w, h in TILES:
        z = z0 - dz
        if z < 90:
            continue
        items.append((z, kind, what, x, y, w, h))
    for z, kind, what, x, y, w, h in sorted(items, reverse=True):
        s = FOCAL / z
        px, py = 960 + x * s, 540 + y * s
        a = clamp((3900 - z) / 700)                     # things come out of the dark
        if a <= 0:
            continue
        with G.xf(c, px, py, s=s):
            if kind == "photo":
                c.drawRRect(rr(-w / 2, -h / 2 + 16, w, h, 26), G.P("#000000", 0.5 * a, blur=24))
                picture(c, what, -w / 2, -h / 2, w, h, 26, a=a)
            elif kind == "model":
                brand, label = what
                card(c, -w / 2, -h / 2, w, h, 30, "#16161b", a, border=("#ffffff", 0.12, 2), shadow=0.4)
                _draw_mark(c, brand, -w / 2 + 70, 0, 62, a)
                T(c, label, -w / 2 + 122, gsm(46).cap / 2, gsm(46), WHITE, a)
            elif kind == "sphere":
                r = w / 2
                c.drawCircle(0, 0, r, G.P(what, a, shader=G.radial_grad(-r * 0.35, -r * 0.4, r * 1.5, [
                    "#ffffff", what, "#1a1440"], stops=[0.0, 0.35, 1.0])))
            elif kind == "star":
                c.drawCircle(0, 0, w, G.P("#9fb4ff", 0.35 * a, blur=w * 0.5, blend=G.ADD))
                M.mark(c, "gemini", 0, 0, w, WHITE, a)
    # the flight ends in a blur of light
    u = clamp((t - T_COLLAGE_OUT) / (T_SEARCH - T_COLLAGE_OUT))
    if u > 0:
        c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#eef1f8", u ** 1.5))
