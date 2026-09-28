"""AGI WEEK look: black for the news desk, each lab in its own colours, founders in portrait frames.
Fonts, brands, chips, portraits, the cursor and the small pieces every scene shares."""
import math
import os
from functools import lru_cache

import cv2
import skia

from engine import gfx as G
from engine.core import clamp, out_cubic, out_back, spring, hash01
from . import marks as M

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(HERE, "..", "photos", "agiweek")

BLACK = "#050506"
INK = "#0d0d0f"
WHITE = "#ffffff"
GREY = "#8b8b93"
DIM = "#55555c"
CLAY = "#d97757"
IVORY = "#f0eee6"
IVORY_INK = "#141413"

# each lab: its card, the model on top of it, and the line that goes with it
BRANDS = {
    "anthropic": dict(company="Anthropic", mark="claude", mark_col=CLAY, bg=[IVORY, IVORY], ink=IVORY_INK,
                      model="Sonnet 5.5", model_font="fraunces", status="EXPECTED TODAY"),
    "openai": dict(company="OpenAI", mark="openai", mark_col=WHITE, bg=["#161618", "#0b0b0c"], ink=WHITE,
                   model="New model", status="DEVDAY · TOMORROW", model2="+ Agent “O”"),
    "google": dict(company="Google DeepMind", mark="gemini", mark_col="#8e75b2", bg=["#ffffff", "#eef2fb"],
                   ink="#1f1f1f", model="Gemini", status="IN THE RACE"),
    "meta": dict(company="Meta", mark="meta", mark_col=WHITE, bg=["#1a86ff", "#0052cc"], ink=WHITE,
                 model="Muse", status="IN THE RACE"),
    "minimax": dict(company="MiniMax", mark="minimax", mark_col=WHITE, bg=["#ff5a86", "#c8184d"], ink=WHITE,
                    model="M3.1", status="OPEN SOURCE"),
    "qwen": dict(company="Alibaba · Qwen", mark="qwen", mark_col=WHITE, bg=["#8f82ff", "#4a35cf"], ink=WHITE,
                 model="Qwen 4", status="OPEN SOURCE"),
    "xai": dict(company="xAI", mark="grok", mark_col=WHITE, bg=["#111113", "#050506"], ink=WHITE,
                model="Grok 4.8", status="THIS WEEK?"),
}
GEMINI_GRAD = ["#4285f4", "#9b72cb", "#d96570"]
META_GRAD = ["#0081fb", "#0064e0"]

# founders: the photo, the crop (a circle: centre and radius, or a rect), the caption
FOUNDERS = {
    "amodei": dict(file="amodei.jpg", rect=(40, 10, 580, 380), name="Dario & Daniela Amodei",
                   role="Co-founders · Anthropic"),
    "altman": dict(file="altman.jpg", circle=(285, 100, 100), name="Sam Altman", role="Co-founder & CEO · OpenAI"),
    "hassabis": dict(file="hassabis.jpg", circle=(115, 112, 84), name="Demis Hassabis",
                     role="Co-founder & CEO · Google DeepMind"),
    "zuckerberg": dict(file="zuckerberg.jpg", circle=(112, 66, 64), name="Mark Zuckerberg",
                       role="Founder & CEO · Meta"),
    "musk": dict(file="musk.jpg", circle=(300, 158, 108), name="Elon Musk", role="Founder · xAI & SpaceX"),
}


@lru_cache(maxsize=None)
def F(fam, size, **axes):
    return G.Font(fam, size, **axes)


def T(c, s, x, y, font, col, a=1.0, align=0.0, tracking=0.0):
    return G.text(c, s, x, y, font, G.P(col, a), align=align, tracking=tracking)


def ui(size, wght=500):
    return F("inter", size, wght=wght, opsz=min(32, max(14, size)))


def display(size, wght=750):
    return F("inter", size, wght=wght, opsz=32)


def serif(size, wght=420):
    return F("fraunces", size, wght=wght, opsz=144, SOFT=0, WONK=0)


def mono(size, wght=560):
    return F("mono", size, wght=wght)


def rr(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def grad_v(y0, y1, cols):
    return G.linear_grad(0, y0, 0, y1, cols)


# ---------------------------------------------------------------- the ground

def ground(c, top, bottom=None, glow=None, glow_a=0.0, t=0.0):
    """A full-frame ground: a flat colour or a vertical gradient, with an optional slow glow."""
    if bottom is None:
        c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P(top))
    else:
        c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P(top, 1, shader=grad_v(0, 1080, [top, bottom])))
    if glow and glow_a > 0:
        x = 960 + 260 * math.sin(t * 0.35)
        blob(c, x, 420, 900, glow, glow_a)


def blob(c, x, y, r, col, a=1.0):
    c.drawCircle(x, y, r, G.P(col, a, shader=G.radial_grad(x, y, r, [col, col], alphas=[a, 0.0])))


def stars(c, t, a=1.0, n=140, speed=0.05, col=WHITE):
    """A slow field of points drifting toward the camera, for depth on the black."""
    if a <= 0:
        return
    for i in range(n):
        u = (float(hash01(i, 1)) + t * speed * (0.4 + float(hash01(i, 5)))) % 1.0
        ang = 2 * math.pi * float(hash01(i, 2))
        d = 80 + 1100 * u * u
        x, y = 960 + math.cos(ang) * d * 1.3, 540 + math.sin(ang) * d
        r = 0.6 + 2.2 * u
        c.drawCircle(x, y, r, G.P(col, a * 0.55 * u * (1 - u) * 4 * (0.4 + 0.6 * float(hash01(i, 3)))))


# ---------------------------------------------------------------- pieces

def chip(c, x, y, text, fill, ink, a=1.0, size=22, dot=None, t=0.0, outline=False, align=0.0):
    """A status pill: optional pulsing dot, tracked caps. Returns its width."""
    f = ui(size, 650)
    tw = f.width(text, 0.12)
    pad = size * 0.9
    dw = size * 1.1 if dot else 0.0
    w = tw + 2 * pad + dw
    h = size * 2.0
    x0 = x - w * align
    if outline:
        c.drawRRect(rr(x0, y - h / 2, w, h, h / 2), G.P(fill, a, stroke=2))
    else:
        c.drawRRect(rr(x0, y - h / 2, w, h, h / 2), G.P(fill, a))
    if dot:
        pulse = 0.5 + 0.5 * math.sin(t * 7)
        G.circle(c, x0 + pad + size * 0.3, y, size * 0.28, G.P(dot, a))
        G.circle(c, x0 + pad + size * 0.3, y, size * (0.28 + 0.35 * pulse), G.P(dot, a * 0.35 * (1 - pulse)))
    T(c, text, x0 + pad + dw, y + f.cap / 2, f, ink, a=a, tracking=0.12)
    return w


def eyebrow(c, brand, x, y, t, t0, ink, status=None, status_fill=None, status_ink=None, dot=None, mark_col=None,
            outline=False):
    """Mark + company name + a status chip, sliding in from the left."""
    b = BRANDS[brand]
    u = clamp((t - t0) / 0.4)
    if u <= 0:
        return
    e = out_cubic(u)
    xo = -40 * (1 - e)
    if brand == "google":
        M.mark(c, "gemini", x + 22 + xo, y, 40, a=u, shader=gemini_shader(x + xo, y - 20, x + 44 + xo, y + 20))
    else:
        M.mark(c, b["mark"], x + 22 + xo, y, 40, mark_col or b["mark_col"], u)
    f = ui(26, 650)
    name = b["company"].upper()
    T(c, name, x + 60 + xo, y + f.cap / 2, f, ink, a=u, tracking=0.16)
    if status:
        v = clamp((t - t0 - 0.18) / 0.3)
        if v > 0:
            sx = x + 60 + f.width(name, 0.16) + 28 + xo
            with G.xf(c, sx, y, s=0.8 + 0.2 * out_back(v, 2.0)):
                chip(c, 0, 0, status, status_fill or ink, status_ink or WHITE, a=v, dot=dot, t=t, outline=outline)


def gemini_shader(x0, y0, x1, y1):
    return G.linear_grad(x0, y1, x1, y0, GEMINI_GRAD)


def rise_text(c, s, x, y, font, col, t, t0, stagger=0.035, dur=0.45, a=1.0, align=0.0, tracking=0.0,
              blur_in=True, shader=None):
    """Letters rise into place one by one, blurring in; returns the run."""
    run = font.shape(s, tracking)
    x0 = x - run.width * align
    for i, gid, gx, adv in run.glyphs():
        u = clamp((t - t0 - stagger * i) / dur)
        if u <= 0:
            continue
        e = out_cubic(u)
        p = G.P(col, a * u, blur=(1 - e) * 10 if blur_in else 0)
        if shader is not None:
            p.setShader(shader)
            p.setAlphaf(a * u)
        G.glyph(c, font, gid, x0 + gx, y + font.size * 0.35 * (1 - e), p)
    return run


def word_in(c, words, x, y, font, col, t, gap=None, a=1.0, align=0.0):
    """Words land one at a time: (t0, word) pairs on one line."""
    space = font.width(" ")
    total = sum(font.width(w) for _, w in words) + space * (len(words) - 1)
    cx = x - total * align
    for t0, w in words:
        u = clamp((t - t0) / 0.3)
        if u > 0:
            e = out_cubic(u)
            T(c, w, cx, y + 36 * (1 - e), font, col, a=a * u)
        cx += font.width(w) + space


# ---------------------------------------------------------------- portraits

@lru_cache(maxsize=None)
def portrait_image(key, px):
    """The founder's photo cropped (circle crops become squares) and resized to px wide, gently sharpened."""
    f = FOUNDERS[key]
    p = os.path.join(PHOTOS, f["file"])
    if not os.path.exists(p):
        return None
    im = cv2.imread(p)
    if "circle" in f:
        cx, cy, r = f["circle"]
        x0, y0 = max(0, cx - r), max(0, cy - r)
        im = im[y0:cy + r, x0:cx + r]
    else:
        x0, y0, x1, y1 = f["rect"]
        im = im[y0:y1, x0:x1]
    s = px / im.shape[1]
    im = cv2.resize(im, (px, int(round(im.shape[0] * s))), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    if s > 1.2:
        blur = cv2.GaussianBlur(im, (0, 0), 1.0 + 0.4 * s)
        im = cv2.addWeighted(im, 1.45, blur, -0.45, 0)
    return G.image_from_rgba(cv2.cvtColor(im, cv2.COLOR_BGR2RGBA))


def portrait(c, key, x, y, size, t, t0, ring=WHITE, text_col=WHITE, sub_col=None, side="right", a=1.0,
             rect_h=None):
    """A founder: the photo in a ringed circle (or a rounded rect for a pair), then name and role beside it.
    (x, y) is the centre of the photo."""
    f = FOUNDERS[key]
    u = clamp((t - t0) / 0.5)
    if u <= 0 or a <= 0:
        return
    s = spring(t - t0, 2.6, 0.55)
    e = out_cubic(u)
    img = portrait_image(key, int(size * 2))
    with G.layer(c, alpha=a * clamp(u * 2.5)):
        with G.xf(c, x, y, s=0.6 + 0.4 * s):
            if "circle" in f:
                r = size / 2
                c.drawCircle(0, 10, r, G.P("#000000", 0.35, blur=18))
                c.save()
                clip = skia.Path()
                clip.addCircle(0, 0, r)
                c.clipPath(clip, skia.ClipOp.kIntersect, True)
                if img is not None:
                    G.draw_image(c, img, -r, -r, size, size * img.height() / img.width())
                else:
                    c.drawCircle(0, 0, r, G.P("#2a2a30"))
                c.restore()
                ring_path = G.arc_path(0, 0, r + 6, -90, 360 * e)
                c.drawPath(ring_path, G.P(ring, 1, stroke=4, cap="round"))
            else:
                w = size
                h = rect_h or size * 0.66
                c.drawRRect(rr(-w / 2, -h / 2 + 12, w, h, 28), G.P("#000000", 0.28, blur=22))
                c.save()
                c.clipRRect(rr(-w / 2, -h / 2, w, h, 28), skia.ClipOp.kIntersect, True)
                if img is not None:
                    ih = w * img.height() / img.width()
                    G.draw_image(c, img, -w / 2, -ih / 2, w, ih)
                c.restore()
                c.drawRRect(rr(-w / 2 - 5, -h / 2 - 5, w + 10, h + 10, 32), G.P(ring, e, stroke=4))
    # the caption
    v = clamp((t - t0 - 0.2) / 0.4)
    if v > 0:
        ev = out_cubic(v)
        fn, fr = ui(34, 680), ui(22, 500)
        if "circle" in f:
            half = size / 2 + 34
            tx = x + half if side == "right" else x - half
            al = 0.0 if side == "right" else 1.0
            ty = y
        else:
            tx, al = x - size / 2, 0.0
            ty = y + (rect_h or size * 0.66) / 2 + 58
        T(c, f["name"], tx + (20 * (1 - ev) if al == 0 else -20 * (1 - ev)), ty + 4, fn, text_col, a=a * v, align=al)
        T(c, f["role"], tx + (20 * (1 - ev) if al == 0 else -20 * (1 - ev)), ty + 40, fr, sub_col or text_col,
          a=a * v * 0.72, align=al, tracking=0.02)


# ---------------------------------------------------------------- the cursor

_ARROW = [(0, 0), (0, 26), (6.5, 20), (11, 30.5), (15, 28.8), (10.6, 18.6), (19, 18.6)]


def cursor(c, x, y, press=0.0, a=1.0, body=INK, edge=WHITE, clicks=(), t=0.0):
    if a <= 0:
        return
    for tc in clicks:
        u = (t - tc) / 0.45
        if 0 <= u < 1:
            G.circle(c, x, y, 8 + 46 * out_cubic(u), G.P(body, 0.3 * (1 - u) * a, stroke=2.2))
    s = 1.5 * (1 - 0.14 * press)
    path = G.poly([(px * s, py * s) for px, py in _ARROW])
    with G.layer(c, alpha=a):
        with G.xf(c, x, y):
            with G.xf(c, 1.5, 4):
                c.drawPath(path, G.P("#000000", 0.28, blur=3))
            c.drawPath(path, G.P(edge, 1, stroke=4.2, join="round"))
            c.drawPath(path, G.P(body))


def press_of(t, times, tau=0.07):
    p = 0.0
    for tc in times:
        if t >= tc:
            p = max(p, math.exp(-(t - tc) / tau))
    return p


def panel(c, x, y, w, h, r=28, fill=WHITE, a=1.0, shadow=0.12, rim=None):
    if shadow > 0:
        c.drawRRect(rr(x, y + 24, w, h, r), G.P("#000000", shadow * a, blur=36))
        c.drawRRect(rr(x, y + 3, w, h, r), G.P("#000000", shadow * 0.5 * a, blur=4))
    c.drawRRect(rr(x, y, w, h, r), G.P(fill, a))
    if rim:
        c.drawRRect(rr(x + 0.5, y + 0.5, w - 1, h - 1, r), G.P(rim[0], rim[1] * a, stroke=1.4))


def chevron(c, x, y, s, col, a=1.0, rot=0.0):
    p = skia.Path()
    p.moveTo(-s * 0.5, -s * 0.25)
    p.lineTo(0, s * 0.25)
    p.lineTo(s * 0.5, -s * 0.25)
    with G.xf(c, x, y, rot=rot):
        c.drawPath(p, G.P(col, a, stroke=s * 0.18, cap="round", join="round"))


def arrow_up(c, x, y, s, col, a=1.0):
    p = skia.Path()
    p.moveTo(x, y + s * 0.45)
    p.lineTo(x, y - s * 0.45)
    p.moveTo(x - s * 0.38, y - s * 0.08)
    p.lineTo(x, y - s * 0.45)
    p.lineTo(x + s * 0.38, y - s * 0.08)
    c.drawPath(p, G.P(col, a, stroke=s * 0.16, cap="round", join="round"))


def download(c, x, y, s, col, a=1.0, bob=0.0):
    p = skia.Path()
    yy = y + bob
    p.moveTo(x, yy - s * 0.45)
    p.lineTo(x, yy + s * 0.2)
    p.moveTo(x - s * 0.32, yy - s * 0.08)
    p.lineTo(x, yy + s * 0.22)
    p.lineTo(x + s * 0.32, yy - s * 0.08)
    p.moveTo(x - s * 0.45, y + s * 0.45)
    p.lineTo(x + s * 0.45, y + s * 0.45)
    c.drawPath(p, G.P(col, a, stroke=s * 0.13, cap="round", join="round"))


def roll_digit(c, a_ch, b_ch, u, x, y, font, col, a=1.0):
    """One character rolling up from a_ch to b_ch as u goes 0 -> 1, clipped to its line."""
    h = font.size * 1.1
    e = out_back(clamp(u), 1.4) if u < 1 else 1.0
    with G.clip_rect(c, x - 10, y - font.cap - font.size * 0.15, font.width(max(a_ch, b_ch, key=font.width)) + 30,
                     font.cap + font.size * 0.4):
        if e < 1:
            T(c, a_ch, x, y - h * e, font, col, a=a)
        T(c, b_ch, x, y + h * (1 - e), font, col, a=a)
