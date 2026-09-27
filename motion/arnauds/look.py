"""ARNAUD'S look: white, black, gold and light green. Plus photos, icons, the caret and the phone."""
import math
import os
from functools import lru_cache

import cv2
import skia

from engine import gfx as G
from engine.core import clamp

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(HERE, "..", "photos", "arnauds")

# the palette: white, black, gold and light green
WHITE = "#ffffff"
BLACK = "#0a0a0a"
GOLD = "#e3b54f"
GOLD_DEEP = "#b8872a"
GOLD_PALE = "#f3dc9a"
LIGHT_GREEN = "#bde9a0"
GREEN_MID = "#86d36a"
GOLD_INK = "#946a17"        # gold for type on the light ground
# the thinking ring's beads and coin, in vibrant takes on the palette
VIVID_GOLD = "#ffc400"
EMERALD = "#12b85a"
SHADOW = "#1d3a12"          # shadows fall dark green on the light-green ground
# one ground for the whole film: light green; white for cards, panels and the phone; black only for type
CREAM = WHITE
PAPER = WHITE
NIGHT = LIGHT_GREEN
PLUM = WHITE
FIELD = LIGHT_GREEN
GROUND = ["#d6f2bf", LIGHT_GREEN, "#9fd07d"]
# accents, all drawn from the four colours
PURPLE = GOLD_DEEP
VIOLET = GREEN_MID
GREEN = GREEN_MID
MINT = LIGHT_GREEN
AMBER = GOLD_PALE
PINK = GOLD
# type and lines
INK = BLACK
GREY = "#8a8a8a"
FAINT = "#c8c8c8"
LINE = "#ececec"
CARD = PLUM
# the signature glow: gold and white light, turning slowly around every card
GLOW = [GOLD, GOLD_PALE, WHITE, GOLD, GOLD_DEEP, WHITE, GOLD_PALE, GOLD]
MARDI = [GOLD_INK, GOLD_DEEP, GOLD, GOLD_DEEP]
# the old names, for code that still speaks them
LIME = GOLD
ORANGE = GOLD
BLUE = GOLD_DEEP
LAVENDER = GOLD_PALE


@lru_cache(maxsize=None)
def F(fam, size, **axes):
    return G.Font(fam, size, **axes)


def T(c, s, x, y, font, col, a=1.0, align=0.0, tracking=0.0, tnum=False):
    return G.text(c, s, x, y, font, G.P(col, a), align=align, tracking=tracking,
                  features={"tnum": True} if tnum else None)


def rr(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def ui(size, wght=450):
    return F("inter", size, wght=wght, opsz=min(32, max(14, size)))


def serif(size):
    return F("serif", size)


# ---------------------------------------------------------------- glow

def sweep(cx, cy, t, speed=40.0, colors=GLOW, alpha=1.0):
    m = skia.Matrix()
    m.setRotate(t * speed, cx, cy)
    return skia.GradientShader.MakeSweep(cx, cy, [G.cint(col, alpha) for col in colors], None,
                                         skia.TileMode.kClamp, 0, 360, 0, m)


def glow_rrect(c, x, y, w, h, r, t, a=1.0, spread=26.0, width=18.0, speed=40.0):
    """The reference's signature: a card edged in soft, slowly turning rainbow light."""
    if a <= 0:
        return
    p = skia.Paint(AntiAlias=True)
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(width)
    p.setShader(sweep(x + w / 2, y + h / 2, t, speed))
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, spread))
    p.setAlphaf(clamp(a))
    c.drawRRect(rr(x, y, w, h, r), p)


def glow_blob(c, x, y, r, col, a=1.0):
    c.drawCircle(x, y, r, G.P(col, a, shader=G.radial_grad(x, y, r, [col, col], alphas=[a, 0.0])))


def soft_shadow(c, x, y, w, h, r, a=1.0, lift=1.0):
    c.drawRRect(rr(x, y + 26 * lift, w, h, r), G.P(SHADOW, 0.14 * a, blur=40 * lift))
    c.drawRRect(rr(x, y + 3, w, h, r), G.P(SHADOW, 0.08 * a, blur=5))


def ground(c, t):
    """The one ground of the whole film: light green, lit from the middle, with slow gold and white glows."""
    c.save()
    c.clipRect(skia.Rect.MakeWH(1920, 1080))       # the lighting stays inside the frame when a scene slides
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P(LIGHT_GREEN))
    c.drawCircle(960, 540, 1250, G.P(LIGHT_GREEN, 1, shader=G.radial_grad(960, 540, 1250, GROUND,
                                                                         stops=[0.0, 0.55, 1.0])))
    for k, (col, x, y, r) in enumerate(((GOLD, 200, 160, 560), (WHITE, 1720, 940, 600), (GOLD_PALE, 1780, 90, 420))):
        glow_blob(c, x + 50 * math.sin(t * 0.7 + k), y + 30 * math.cos(t * 0.6 + k), r, col, 0.2)
    c.restore()


def caret(c, x, y_top, h, a=1.0):
    """The caret: a black bar."""
    bw = max(3.0, h * 0.06)
    c.drawRect(skia.Rect.MakeXYWH(x - bw, y_top, bw, h), G.P(INK, a))


# ---------------------------------------------------------------- photos

@lru_cache(maxsize=16)
def photo_rgba(name, min_w=0):
    p = os.path.join(PHOTOS, f"{name}.jpg")
    if not os.path.exists(p):
        return None
    im = cv2.imread(p)
    if min_w and im.shape[1] < min_w:
        s = min_w / im.shape[1]
        im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        blur = cv2.GaussianBlur(im, (0, 0), 1.2)
        im = cv2.addWeighted(im, 1.5, blur, -0.5, 0)            # a gentle unsharp mask after the upscale
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGBA)


@lru_cache(maxsize=16)
def photo(name, min_w=0):
    a = photo_rgba(name, min_w)
    return None if a is None else G.image_from_rgba(a)


def draw_cover(c, name, x, y, w, h, fx=0.5, fy=0.5, zoom=1.0, alpha=1.0, min_w=0):
    """Draw a photo to cover the rect (like CSS object-fit: cover), focused on (fx, fy)."""
    img = photo(name, min_w)
    if img is None:
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), G.P("#2a2320", alpha))
        return
    iw, ih = img.width(), img.height()
    s = max(w / iw, h / ih) * zoom
    dw, dh = iw * s, ih * s
    dx = x + (w - dw) * fx
    dy = y + (h - dh) * fy
    G.draw_image(c, img, dx, dy, dw, dh, alpha=alpha)


def image_shader(name, x, y, w, h, fx=0.5, fy=0.5, zoom=1.0, min_w=0):
    img = photo(name, min_w)
    if img is None:
        return None
    iw, ih = img.width(), img.height()
    s = max(w / iw, h / ih) * zoom
    m = skia.Matrix()
    m.setScale(s, s)
    m.postTranslate(x + (w - iw * s) * fx, y + (h - ih * s) * fy)
    return img.makeShader(skia.TileMode.kClamp, skia.TileMode.kClamp,
                          skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), m)


# ---------------------------------------------------------------- icons

def stroke(col, w, a=1.0):
    return G.P(col, a, stroke=w, cap="round", join="round")


def icon_arrow(c, x, y, s, col, direction=1, a=1.0, w=None):
    d = direction
    p = stroke(col, w or s * 0.12, a)
    c.drawLine(x - d * s * 0.45, y, x + d * s * 0.45, y, p)
    c.drawPath(G.poly([(x + d * s * 0.05, y - s * 0.38), (x + d * s * 0.45, y), (x + d * s * 0.05, y + s * 0.38)],
                      closed=False), p)


def icon_x(c, x, y, s, col, a=1.0):
    p = stroke(col, s * 0.12, a)
    c.drawLine(x - s * 0.35, y - s * 0.35, x + s * 0.35, y + s * 0.35, p)
    c.drawLine(x - s * 0.35, y + s * 0.35, x + s * 0.35, y - s * 0.35, p)


def icon_plus(c, x, y, s, col, a=1.0):
    p = stroke(col, s * 0.12, a)
    c.drawLine(x - s * 0.4, y, x + s * 0.4, y, p)
    c.drawLine(x, y - s * 0.4, x, y + s * 0.4, p)


def icon_check(c, x, y, s, col, p=1.0, a=1.0, w=None):
    path = G.poly([(x - s * 0.42, y + s * 0.02), (x - s * 0.12, y + s * 0.32), (x + s * 0.45, y - s * 0.3)], closed=False)
    c.drawPath(path, G.P(col, a, stroke=w or s * 0.16, cap="round", join="round", effect=G.trim(0, p)))


def icon_star(c, x, y, s, col, a=1.0):
    c.drawPath(G.poly(G.star_points(5, s * 0.5, s * 0.22, cx=x, cy=y)), G.P(col, a))


def icon_pin(c, x, y, s, col, a=1.0, hole=None):
    path = skia.Path()
    path.addCircle(x, y - s * 0.18, s * 0.34)
    path.moveTo(x - s * 0.3, y - s * 0.02)
    path.lineTo(x, y + s * 0.5)
    path.lineTo(x + s * 0.3, y - s * 0.02)
    path.close()
    c.drawPath(path, G.P(col, a))
    if hole:
        G.circle(c, x, y - s * 0.18, s * 0.13, G.P(hole, a))


def icon_clock(c, x, y, s, col, a=1.0):
    G.circle(c, x, y, s * 0.42, stroke(col, s * 0.1, a))
    p = stroke(col, s * 0.1, a)
    c.drawLine(x, y, x, y - s * 0.24, p)
    c.drawLine(x, y, x + s * 0.18, y + s * 0.08, p)


def icon_people(c, x, y, s, col, a=1.0):
    for dx, k in ((-0.2, 0.85), (0.22, 1.0)):
        G.circle(c, x + dx * s, y - s * 0.18 * k, s * 0.17 * k, G.P(col, a))
        c.drawPath(G.arc_path(x + dx * s, y + s * 0.38, s * 0.3 * k, 180, 180), G.P(col, a))


def icon_send(c, x, y, r, a=1.0, press=0.0):
    with G.xf(c, x, y, s=1 - 0.1 * press):
        c.drawCircle(0, 0, r, G.P(BLACK, a))
        icon_arrow(c, 0, 0, r * 1.05, GOLD, 1, a)


def icon_flame(c, x, y, s, col, a=1.0):
    p = skia.Path()
    p.moveTo(x, y - s * 0.5)
    p.cubicTo(x + s * 0.45, y - s * 0.1, x + s * 0.4, y + s * 0.45, x, y + s * 0.5)
    p.cubicTo(x - s * 0.4, y + s * 0.45, x - s * 0.45, y + s * 0.05, x - s * 0.12, y - s * 0.2)
    p.cubicTo(x - s * 0.05, y, x + s * 0.05, y - s * 0.25, x, y - s * 0.5)
    c.drawPath(p, G.P(col, a))


def icon_shrimp(c, x, y, s, col, a=1.0):
    c.drawPath(G.arc_path(x, y, s * 0.36, 200, 250), stroke(col, s * 0.2, a))
    for k in range(3):
        ang = math.radians(250 + k * 50)
        c.drawLine(x + math.cos(ang) * s * 0.24, y + math.sin(ang) * s * 0.24,
                   x + math.cos(ang) * s * 0.48, y + math.sin(ang) * s * 0.48, stroke(col, s * 0.06, a))


def icon_puff(c, x, y, s, col, a=1.0):
    """A soufflé potato: a small puffed pillow."""
    path = skia.Path()
    path.addOval(skia.Rect.MakeXYWH(x - s * 0.46, y - s * 0.26, s * 0.92, s * 0.52))
    c.drawPath(path, G.P(col, a))
    c.drawPath(G.arc_path(x, y + s * 0.02, s * 0.3, 200, 140), stroke(CARD, s * 0.06, a))


# ---------------------------------------------------------------- cursor (a pointing hand, like the reference)

_HAND = ("M9 2.5c1.1 0 2 .9 2 2v6.2l.9-.3c1-.3 2.1.2 2.4 1.2l.1.3.8-.2c1-.3 2 .3 2.3 1.3l.1.2.7-.1c1.1-.2 2.1.5 2.3 "
         "1.6l.5 3.2c.4 2.6-.5 5.2-2.4 7l-.6.6H9.7l-4.1-5.6c-.6-.9-.4-2.1.5-2.7.8-.6 1.9-.5 2.6.2L7 17V4.5c0-1.1.9-2 2-2z")


@lru_cache(maxsize=1)
def hand_path():
    return G.svg_path(_HAND)


def hand(c, x, y, s=2.2, press=0.0, a=1.0):
    """Tip of the index finger at (x, y)."""
    with G.layer(c, alpha=a):
        with G.xf(c, x, y, s=s * (1 - 0.12 * press)):
            c.translate(-9, -2.5)
            with G.xf(c, 0.6, 1.4):
                c.drawPath(hand_path(), G.P("#000000", 0.25, blur=1.2))
            c.drawPath(hand_path(), G.P(WHITE))
            c.drawPath(hand_path(), G.P(INK, 1, stroke=1.3, join="round"))


# ---------------------------------------------------------------- the phone

def status_bar(c, x, y, w, a=1.0, col=INK):
    T(c, "9:30", x + 96, y + 70, ui(46, 700), col, a=a)
    bx = x + w - 150
    for k in range(4):
        h = 14 + k * 8
        c.drawRRect(rr(bx - 150 + k * 16, y + 70 - h, 10, h, 2), G.P(col, a))
    for k, r in enumerate((30, 20, 10)):
        c.drawPath(G.arc_path(bx - 55, y + 70, r, 225, 90), stroke(col, 6, a))
    G.circle(c, bx - 55, y + 68, 3.5, G.P(col, a))
    c.drawRRect(rr(bx - 12, y + 40, 70, 34, 9), G.P(col, a, stroke=4))
    c.drawRRect(rr(bx - 7, y + 45, 60, 24, 5), G.P(col, a))
    c.drawRRect(rr(bx + 60, y + 50, 6, 14, 2), G.P(col, a))


def phone(c, x, y, w, h, a=1.0, r=96):
    soft_shadow(c, x, y, w, h, r, a, lift=1.3)
    c.drawRRect(rr(x, y, w, h, r), G.P(PAPER, a))
    c.drawRRect(rr(x + 0.5, y + 0.5, w - 1, h - 1, r), G.P("#000000", 0.06 * a, stroke=1.2))


def veee_orb(c, x, y, r, t=0.0, a=1.0):
    """The concierge's mark: a small orb of the parade colours, slowly turning."""
    m = skia.Matrix()
    m.setRotate(t * 90, x, y)
    sh = skia.GradientShader.MakeSweep(x, y, [G.cint(col, a) for col in (VIOLET, PINK, GOLD, GREEN, VIOLET)], None,
                                       skia.TileMode.kClamp, 0, 360, 0, m)
    p = skia.Paint(AntiAlias=True)
    p.setShader(sh)
    c.drawCircle(x, y, r, p)
    c.drawCircle(x - r * 0.3, y - r * 0.32, r * 0.32, G.P(WHITE, 0.55 * a, blur=r * 0.25))
