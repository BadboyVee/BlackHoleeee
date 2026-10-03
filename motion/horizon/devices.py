"""HORIZON's devices: a phone in black titanium and a laptop in aluminium, rendered from the front with Blender
(blender/devices.py) with their screens cut out, so any scene can draw into the screen and the real hardware is
laid over it, with a faint sheen on the glass. Without the renders, drawn stand-ins keep the film whole."""
import json
import os
from functools import lru_cache

import cv2
import numpy as np
import skia

from engine import gfx as G
from .look import rr, WHITE, T, sans

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.environ.get("HORIZON_PLATES", os.path.join(HERE, "..", "out", "plates", "horizon"))
PHONE_R, PHONE_BEZEL = 68.0, 12.0
SAMPLING = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


@lru_cache(maxsize=None)
def _render(name):
    """A device's render, premultiplied, and the rectangles measured in it; None without it."""
    png, js = os.path.join(DIR, f"{name}.png"), os.path.join(DIR, f"{name}.json")
    if not (os.path.exists(png) and os.path.exists(js)):
        return None
    im = cv2.imread(png, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    im = im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)
    rgb, a = im[..., 2::-1], im[..., 3:4]
    pre = np.concatenate([rgb * a, a], -1)
    img = skia.Image.fromarray(np.ascontiguousarray(np.clip(pre * 255 + 0.5, 0, 255).astype(np.uint8)),
                               colorType=skia.ColorType.kRGBA_8888_ColorType,
                               alphaType=skia.AlphaType.kPremul_AlphaType).withDefaultMipmaps()
    with open(js) as f:
        return img, json.load(f)


def _lay(c, real, key, x, y, w, h):
    """Lay a render over the frame so that its measured rectangle `key` covers (x, y, w, h)."""
    img, meta = real
    bx, by, bw, bh = meta[key]
    kx, ky = w / bw, h / bh
    W, H = meta["size"]
    c.drawImageRect(img, skia.Rect.MakeXYWH(x - bx * kx, y - by * ky, W * kx, H * ky), SAMPLING)


def _sheen(c, sx, sy, sw, sh, r, a=1.0):
    """Light on the glass: a soft diagonal sweep from the top left, gone before the middle."""
    c.save()
    c.clipRRect(rr(sx, sy, sw, sh, r), True)
    c.drawRect(skia.Rect.MakeXYWH(sx, sy, sw, sh), G.P(WHITE, 0.07 * a, shader=G.linear_grad(
        sx, sy, sx + sw * 0.7, sy + sh * 0.45, ["#ffffff", "#ffffff"], [0.0, 1.0], alphas=[1.0, 0.0])))
    c.restore()


def phone(c, x, y, w, h, screen, a=1.0, shadow=0.35, island=True):
    """A phone with its top-left at (x, y); screen(c, sx, sy, sw, sh) draws the screen's contents, clipped to it."""
    r = PHONE_R * w / 440
    b = PHONE_BEZEL * w / 440
    real = _render("phone")
    with G.layer(c, a):
        if shadow > 0:
            c.drawRRect(rr(x + w * 0.04, y + h * 0.03, w, h, r), G.P("#000000", shadow, blur=w * 0.08))
        sx, sy, sw, sh = x + b, y + b, w - 2 * b, h - 2 * b
        if real is None:
            c.drawRRect(rr(x, y, w, h, r), G.P("#1b1b1e", 1, shader=G.linear_grad(
                x, y, x + w, y + h, ["#5a5a60", "#1b1b1e", "#3a3a40"], [0.0, 0.5, 1.0])))
            c.drawRRect(rr(x + 2.5, y + 2.5, w - 5, h - 5, r - 2.5), G.P("#050506"))
        c.save()
        c.clipRRect(rr(sx - 1, sy - 1, sw + 2, sh + 2, r - b + 1), True)     # the frame's own edge covers the seam
        screen(c, sx, sy, sw, sh)
        c.restore()
        if real is not None:
            _sheen(c, sx, sy, sw, sh, r - b)
            _lay(c, real, "body", x, y, w, h)
        if island:
            iw, ih = sw * 0.27, sw * 0.075
            c.drawRRect(rr(sx + (sw - iw) / 2, sy + sw * 0.03, iw, ih, ih / 2), G.P("#000000"))


def status_bar(c, sx, sy, sw, col=WHITE, a=1.0):
    k = sw / 416
    T(c, "9:41", sx + 36 * k, sy + 38 * k, sans(17 * k, 600), col, a)
    bx = sx + sw - 64 * k
    c.drawRRect(rr(bx, sy + 26 * k, 27 * k, 13 * k, 4 * k), G.P(col, a, stroke=1.6 * k))
    c.drawRRect(rr(bx + 2.5 * k, sy + 28.5 * k, 19 * k, 8 * k, 2 * k), G.P(col, a))
    for i in range(4):                                             # signal
        hh = (4 + 3 * i) * k
        c.drawRRect(rr(bx - 34 * k + i * 6 * k, sy + 38 * k - hh, 4 * k, hh, 1 * k), G.P(col, a))


def laptop(c, x, y, w, screen, a=1.0, base=True):
    """A laptop from the front: its lid w wide with its top-left at (x, y), the deck below it."""
    h = w * 0.64
    r = w * 0.022
    real = _render("laptop")
    with G.layer(c, a):
        c.drawRRect(rr(x - w * 0.02, y + h * 0.05, w * 1.04, h, r), G.P("#000000", 0.28, blur=w * 0.035))
        if real is None:
            c.drawRRect(rr(x, y, w, h, r), G.P("#b9bac0", 1, shader=G.linear_grad(x, y, x, y + h,
                                                                                ["#d6d7dc", "#a9aab0"])))
            c.drawRRect(rr(x + 3, y + 3, w - 6, h - 6, r - 2), G.P("#0a0a0b"))
        bz = w * 0.022
        sx, sy, sw, sh = x + bz, y + bz, w - 2 * bz, h - 2 * bz - w * 0.008
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(sx - 1, sy - 1, sw + 2, sh + 2))
        screen(c, sx, sy, sw, sh)
        c.restore()
        if real is not None:
            _sheen(c, sx, sy, sw, sh, 2.0, 0.8)
            _lay(c, real, "lid", x, y, w, h)
        c.drawRRect(rr(x + w / 2 - w * 0.045, y + 1, w * 0.09, bz * 0.8, bz * 0.3), G.P("#0a0a0b"))   # the notch
        if base and real is None:
            p = skia.Path()
            d = w * 0.05
            p.moveTo(x - d * 0.4, y + h)
            p.lineTo(x + w + d * 0.4, y + h)
            p.lineTo(x + w + d, y + h + w * 0.035)
            p.lineTo(x - d, y + h + w * 0.035)
            p.close()
            c.drawPath(p, G.P("#c7c8cd", 1, shader=G.linear_grad(0, y + h, 0, y + h + w * 0.035,
                                                                  ["#e4e5e9", "#9d9ea4"])))
            c.drawRRect(rr(x + w / 2 - w * 0.07, y + h, w * 0.14, w * 0.007, w * 0.003), G.P("#8e8f95"))


def preload():
    _render("phone")
    _render("laptop")
