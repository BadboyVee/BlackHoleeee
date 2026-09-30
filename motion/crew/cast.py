"""The crew: five plush agents, rendered in fur with Blender (blender/plush.py) and given their faces here, so
they can look about, blink, smile and talk. Each sits on a soft shadow and squashes when it lands."""
import math
import os
from functools import lru_cache

import cv2
import numpy as np
import skia

from engine import gfx as G
from engine.core import hash01
from .look import CORAL, MINT, LAVENDER, SKY, INDIGO

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.environ.get("CREW_SPRITES", os.path.join(HERE, "..", "out", "plates", "plush"))

# name: (colour, eye height, eye spacing, eye size, mouth drop), in fractions of the sprite
CREW = {
    "fixer": (CORAL, 0.520, 0.112, 0.062, 0.092),
    "tester": (MINT, 0.540, 0.112, 0.062, 0.092),
    "reader": (LAVENDER, 0.572, 0.100, 0.052, 0.085),
    "planner": (SKY, 0.540, 0.112, 0.062, 0.092),
    "nightowl": (INDIGO, 0.560, 0.108, 0.060, 0.090),
}
ORDER = ["fixer", "tester", "reader", "planner", "nightowl"]


@lru_cache(maxsize=None)
def sprite(name):
    path = os.path.join(DIR, f"{name}.png")
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED) if os.path.exists(path) else None
    if im is None:
        return _stand_in(name)
    im = im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)
    rgb, a = im[..., 2::-1], im[..., 3:4]
    out = np.concatenate([rgb * a, a], -1)
    return skia.Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8),
                                colorType=skia.ColorType.kRGBA_8888_ColorType,
                                alphaType=skia.AlphaType.kPremul_AlphaType)


def _stand_in(name):
    n = 360
    arr = np.zeros((n, n, 4), np.uint8)
    s = skia.Surface(arr)
    col = CREW[name][0]
    with s as c:
        c.clear(skia.Color4f(0, 0, 0, 0))
        c.drawCircle(n / 2, n * 0.53, n * 0.33, G.P(col, 1, shader=G.radial_grad(n * 0.4, n * 0.4, n * 0.45,
                                                                                [G.mixc(col, "#ffffff", 0.3), col])))
    return skia.Image.fromarray(arr, colorType=skia.ColorType.kRGBA_8888_ColorType,
                                alphaType=skia.AlphaType.kPremul_AlphaType)


class Face:
    def __init__(self, look=(0.0, 0.0), blink=0.0, happy=0.0, talk=0.0, sleepy=0.0):
        self.look, self.blink, self.happy, self.talk, self.sleepy = look, blink, happy, talk, sleepy


def idle_blink(t, seed):
    """A blink every few seconds, each agent on its own clock."""
    period = 2.6 + 1.4 * hash01(seed, 5)
    ph = (t + hash01(seed, 6) * period) % period
    return max(0.0, 1 - abs(ph - 0.08) / 0.08) if ph < 0.16 else 0.0


def face(c, name, S, f):
    """The face on a sprite drawn S px wide with its top-left at the origin."""
    col, ey, dx, es, md = CREW[name]
    lx, ly = f.look
    for sx in (-1, 1):                                             # cheeks
        c.drawOval(skia.Rect.MakeXYWH(S * (0.5 + sx * (dx + 0.07)) - S * 0.045, S * (ey + md * 0.55) - S * 0.02,
                                      S * 0.09, S * 0.04), G.P("#ff7a9a", 0.32, blur=S * 0.012))
    shut = max(f.blink, f.sleepy)
    for sx in (-1, 1):
        x = S * (0.5 + sx * dx) + lx * S * 0.012
        y = S * ey + ly * S * 0.01
        w, h = S * es, S * es * 1.35
        if f.happy > 0.5:
            p = skia.Path()
            p.moveTo(x - w * 0.6, y + h * 0.15)
            p.quadTo(x, y - h * 0.55, x + w * 0.6, y + h * 0.15)
            c.drawPath(p, G.P("#111114", 1, stroke=S * 0.011, cap="round"))
        elif shut > 0.6:
            p = skia.Path()
            p.moveTo(x - w * 0.6, y)
            p.quadTo(x, y + h * 0.35, x + w * 0.6, y)
            c.drawPath(p, G.P("#111114", 1, stroke=S * 0.01, cap="round"))
        else:
            hh = h * (1 - shut)
            r = skia.Rect.MakeXYWH(x - w / 2, y - hh / 2, w, hh)
            c.drawOval(r, G.P("#0a0a0c", 1, shader=G.radial_grad(x - w * 0.15, y - hh * 0.2, max(w, hh) * 0.8,
                                                                 ["#3a3a44", "#050507"])))
            c.drawCircle(x - w * 0.18, y - hh * 0.22, w * 0.2, G.P("#ffffff", 0.95))
            c.drawCircle(x + w * 0.2, y + hh * 0.2, w * 0.08, G.P("#ffffff", 0.6))
    mx, my = S * 0.5 + lx * S * 0.008, S * (ey + md)
    if f.talk > 0.05:
        c.drawOval(skia.Rect.MakeXYWH(mx - S * 0.022, my - S * 0.012, S * 0.044, S * 0.03 * (0.5 + f.talk)),
                   G.P("#2a0f14"))
    else:
        p = skia.Path()
        p.moveTo(mx - S * 0.03, my - S * 0.004)
        p.quadTo(mx, my + S * 0.022, mx + S * 0.03, my - S * 0.004)
        c.drawPath(p, G.P("#2a0f14", 1, stroke=S * 0.008, cap="round"))


def agent(c, name, x, y, size, t=0.0, f=None, s=1.0, squash=0.0, tilt=0.0, shadow=True, a=1.0, seed=0):
    """An agent standing with its feet at (x, y), size px tall; s scales it (for popping in), squash > 0 flattens
    it as it lands, < 0 stretches it as it jumps."""
    if s <= 0.01 or a <= 0:
        return
    f = f or Face(blink=idle_blink(t, seed or hash(name) % 97))
    S = size * s
    sx, sy = 1 + 0.18 * squash, 1 - 0.18 * squash
    with G.layer(c, a):
        if shadow:
            c.drawOval(skia.Rect.MakeXYWH(x - S * 0.3, y - S * 0.035, S * 0.6, S * 0.07),
                       G.P("#1a1d2e", 0.16, blur=S * 0.03))
        with G.xf(c, x, y, sx=sx, sy=sy, rot=tilt):
            c.translate(-S / 2, -S * 0.86)                             # the sprite's feet sit at 0.86 of its height
            c.drawImageRect(sprite(name), skia.Rect.MakeWH(S, S), skia.SamplingOptions(skia.FilterMode.kLinear,
                                                                                        skia.MipmapMode.kLinear))
            face(c, name, S, f)


def hop(t, t0, period=0.62, height=0.06):
    """(lift, squash) for a little bounce in place."""
    ph = ((t - t0) % period) / period
    lift = height * math.sin(math.pi * ph)
    squash = 0.4 * max(0.0, 1 - ph / 0.12) - 0.2 * math.sin(math.pi * ph)
    return lift, squash
