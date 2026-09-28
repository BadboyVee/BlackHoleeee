"""AGI WEEK look: the brands' own faces (Google Sans for Google, Source Serif for Claude, Inter for the rest), the
founders (their photos, the crops for cards and avatars, their names and roles as the user gave them), and the
pieces every product moment shares: soft cards, shadows, a caret, typed text, rich paragraphs."""
import math
import os
from functools import lru_cache

import cv2
import skia

from engine import gfx as G
from engine.core import clamp

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(HERE, "..", "photos", "agiweek")

WHITE = "#ffffff"
BLACK = "#000000"
CLAY = "#d97757"
CREAM = "#f4f1ea"
INK = "#141413"
GEMINI = ["#3c78f0", "#6f86f5", "#b084e0"]
GEMINI_TEXT = ["#4a7ef0", "#6f78de", "#9a6cc4", "#c2548f", "#d33a52"]

# founders: the photo, a head-and-shoulders crop for cards and a square face crop for avatars
# (x0, y0, x1, y1 in the photo), and the caption
FOUNDERS = {
    "amodei": dict(file="amodei.jpg", crop=(8, 0, 574, 390), face=(8, 0, 574, 390), name="Dario & Daniela Amodei",
                   role="Co-founders · Anthropic"),
    "altman": dict(file="altman.jpg", crop=(133, 0, 403, 300), face=(196, 18, 340, 162), name="Sam Altman",
                   role="Co-founder & CEO · OpenAI"),
    "hassabis": dict(file="hassabis.jpg", crop=(29, 0, 207, 198), face=(52, 14, 186, 148), name="Demis Hassabis",
                     role="Co-founder & CEO · Google DeepMind"),
    "zuckerberg": dict(file="zuckerberg.jpg", crop=(18, 0, 198, 200), face=(46, 0, 166, 120),
                       name="Mark Zuckerberg", role="Founder & CEO · Meta"),
    "musk": dict(file="musk.jpg", crop=(177, 20, 447, 320), face=(236, 44, 392, 200), name="Elon Musk",
                 role="Founder · xAI & SpaceX"),
}


@lru_cache(maxsize=None)
def F(fam, size, **axes):
    return G.Font(fam, size, **axes)


def gs(size):
    """Google Sans."""
    return F("gsans", size)


def gsm(size):
    """Google Sans Medium."""
    return F("gsans-medium", size)


def inter(size, w=450):
    return F("inter", size, wght=w, opsz=min(32, max(14, size)))


def serif(size, w=560):
    """Source Serif, the nearest open face to Claude's."""
    return F("source-serif", size, wght=w)


def mono(size, w=420):
    return F("mono", size, wght=w)


def T(c, s, x, y, font, col, a=1.0, align=0.0, tracking=0.0, shader=None):
    if a <= 0 or not s:
        return None
    p = G.P(col, a)
    if shader is not None:
        p.setShader(shader)
    return G.text(c, s, x, y, font, p, align=align, tracking=tracking)


def rr(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def blob(c, x, y, r, col, a=1.0):
    """A soft pool of light: col at the centre fading to nothing at r."""
    c.drawCircle(x, y, r, G.P(col, a, shader=G.radial_grad(x, y, r, [col, col], alphas=[a, 0.0])))


def card(c, x, y, w, h, r, fill=WHITE, a=1.0, border=None, shadow=0.08, lift=18.0, blur=34.0):
    """A soft UI card: a wide faint shadow, a tight contact shadow, the fill, an optional hairline."""
    if a <= 0:
        return
    if shadow > 0:
        c.drawRRect(rr(x, y + lift, w, h, r), G.P(BLACK, shadow * a, blur=blur))
        c.drawRRect(rr(x, y + 2, w, h, r), G.P(BLACK, shadow * 0.45 * a, blur=3))
    c.drawRRect(rr(x, y, w, h, r), G.P(fill, a))
    if border:
        c.drawRRect(rr(x + 0.5, y + 0.5, w - 1, h - 1, r), G.P(border[0], border[1] * a, stroke=border[2]
                                                                 if len(border) > 2 else 1.5))


def typed(text, t, t0, cps=26.0):
    """How much of text is typed by t, at cps characters a second."""
    return text[:max(0, int((t - t0) * cps))] if t >= t0 else ""


def caret(c, x, y, h, t, col, a=1.0, w=3.0):
    if a > 0 and (t * 2.2) % 1.0 < 0.6:
        c.drawRect(skia.Rect.MakeXYWH(x, y - h, w, h), G.P(col, a))


def rich(c, runs, x, y, reg, bold, col, max_w, line_h, a=1.0, upto=None, bold_col=None):
    """A paragraph of runs [(text, is_bold)], wrapped at max_w. upto clips it to its first characters (streaming).
    Returns the y of the next line."""
    words = []
    after_space = False
    for text, b in runs:
        for i, w in enumerate(text.split(" ")):
            if w == "":
                continue
            words.append((w, b, i > 0 or after_space))
        after_space = text.endswith(" ")
    cx, cy = x, y
    shown = 0
    budget = upto if upto is not None else 10 ** 9
    space = reg.width(" ")
    first = True
    for w, b, gap in words:
        f = bold if b else reg
        ww = f.width(w)
        if not first and gap:
            if cx + space + ww > x + max_w:
                cx, cy = x, cy + line_h
            else:
                cx += space
        first = False
        if shown >= budget:
            break
        part = w[:max(0, budget - shown)]
        T(c, part, cx, cy, f, (bold_col or col) if b else col, a)
        shown += len(w) + 1
        cx += ww
    return cy + line_h


@lru_cache(maxsize=None)
def photo(key, w, h, which="crop"):
    """A founder's crop scaled to cover w x h, gently sharpened. None when the photo is missing."""
    f = FOUNDERS[key]
    p = os.path.join(PHOTOS, f["file"])
    if not os.path.exists(p):
        return None
    im = cv2.imread(p)
    x0, y0, x1, y1 = f[which]
    im = im[y0:min(y1, im.shape[0]), x0:min(x1, im.shape[1])]
    s = max(w / im.shape[1], h / im.shape[0])
    nw, nh = max(w, int(round(im.shape[1] * s))), max(h, int(round(im.shape[0] * s)))
    im = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    ox = (nw - w) // 2
    im = im[0:h, ox:ox + w]
    if s > 1.2:
        blur = cv2.GaussianBlur(im, (0, 0), 1.0 + 0.35 * s)
        im = cv2.addWeighted(im, 1.4, blur, -0.4, 0)
    return G.image_from_rgba(cv2.cvtColor(im, cv2.COLOR_BGR2RGBA))


def picture(c, key, x, y, w, h, r, a=1.0, which="crop", zoom=1.0):
    """A founder's photo in a rounded frame (r = w / 2 makes an avatar)."""
    if a <= 0:
        return
    img = photo(key, int(round(w)), int(round(h)), which)
    c.save()
    c.clipRRect(rr(x, y, w, h, r), skia.ClipOp.kIntersect, True)
    if img is None:
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), G.P("#3a3a40", a))
    else:
        iw, ih = w * zoom, h * zoom
        G.draw_image(c, img, x + (w - iw) / 2, y + (h - ih) / 2, iw, ih, alpha=a)
    c.restore()


def ease_push(t, t0, t1, amount=0.05):
    """A slow push over a shot, eased at both ends: 1 -> 1 + amount."""
    u = clamp((t - t0) / max(1e-3, t1 - t0))
    return 1.0 + amount * (0.5 - 0.5 * math.cos(math.pi * u))
