"""The sparks: five plush agents made like real toys and rendered in Blender (blender/sparks.py), each in one
sprite per expression and with its shadow on its own, so they can hop off the floor and land on it again."""
import math
import os
from functools import lru_cache

import cv2
import numpy as np
import skia

from engine import gfx as G
from engine.core import hash01
from .look import TERRACOTTA, MINT, BUTTER, LAVENDER, INDIGO

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.environ.get("SPARKS_SPRITES", os.path.join(HERE, "..", "out", "plates", "sparks"))

COLOURS = {"lead": TERRACOTTA, "builder": MINT, "talker": BUTTER, "reader": LAVENDER, "sleeper": INDIGO}
ORDER = ["builder", "talker", "lead", "reader", "sleeper"]
CLOSED = {"lead": "happy", "builder": "happy", "talker": "happy", "reader": "happy", "sleeper": "asleep"}


def _read(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED) if os.path.exists(path) else None
    if im is None:
        return None
    im = im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)
    return np.concatenate([im[..., 2::-1], im[..., 3:4]], -1)


def _image(rgba):
    return skia.Image.fromarray(np.ascontiguousarray(np.clip(rgba * 255 + 0.5, 0, 255).astype(np.uint8)),
                                colorType=skia.ColorType.kRGBA_8888_ColorType,
                                alphaType=skia.AlphaType.kPremul_AlphaType)


class Sprite:
    """A toy's picture, premultiplied, with where its feet touch the floor (as fractions of the picture)."""

    def __init__(self, rgba):
        a = rgba[..., 3]
        h, w = a.shape
        rows = np.where(a.max(1) > 0.5)[0]
        self.foot_y = (rows.max() + 1) / h if len(rows) else 0.86
        band = a[max(0, rows.max() - int(0.1 * h)):rows.max() + 1] if len(rows) else a
        cols = np.where(band.max(0) > 0.5)[0]
        self.foot_x = (cols.min() + cols.max()) / 2 / w if len(cols) else 0.5
        pre = rgba.copy()
        pre[..., :3] *= pre[..., 3:4]
        self.img = _image(pre)


def _hsv(hexcol):
    rgb = np.array([[[int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)]]], np.float32)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[0, 0]


def _body(hsv, a):
    """The fur's own hue, and a weight per pixel for how much of it is fur (not the eyes, cheeks or kit)."""
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    m = (a > 0.98) & (v > 0.15) & (s > 0.2)
    hist, edges = np.histogram(h[m], bins=72, range=(0, 360), weights=s[m])
    hue = edges[hist.argmax()] + 2.5
    dist = np.abs((h - hue + 180) % 360 - 180)
    return hue, np.clip((40 - dist) / 15, 0, 1) * np.clip((s - 0.12) / 0.15, 0, 1), m & (dist < 30)


@lru_cache(maxsize=None)
def _grade_params(name):
    """How far this toy's render sits from its colour: a hue turn, a saturation and an exposure, measured on its
    open-eyed picture so that every expression of it gets the same grade."""
    rgba = _read(os.path.join(DIR, f"{name}_open.png"))
    if rgba is None:
        return None
    hsv = cv2.cvtColor(np.ascontiguousarray(rgba[..., :3]), cv2.COLOR_RGB2HSV)
    hue, _, m = _body(hsv, rgba[..., 3])
    th, ts, tv = _hsv(COLOURS[name])
    turn = float(np.clip((th - hue + 180) % 360 - 180, -15, 15))
    sat = float(np.clip(ts / max(np.median(hsv[..., 1][m]), 1e-3), 0.9, 1.25))
    gain = float(np.clip(0.88 * tv / max(np.median(hsv[..., 2][m]), 1e-3), 1.0, 1.7))
    return turn, sat, gain


def _grade(rgba, name):
    """Clean and vivid: the fur brought to its colour, lifted to its brightness with a soft shoulder so the lit
    tips never clip, the dark eyes left dark."""
    prm = _grade_params(name)
    if prm is None:
        return rgba
    turn, sat, gain = prm
    hsv = cv2.cvtColor(np.ascontiguousarray(rgba[..., :3]), cv2.COLOR_RGB2HSV)
    _, w, _ = _body(hsv, rgba[..., 3])
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    h = (h + turn * w) % 360
    s = np.clip(s * (1 + (sat - 1) * w), 0, 1)
    x = v * gain
    knee = 0.78
    v = np.where(x < knee, x, knee + (1 - knee) * (1 - np.exp(-(x - knee) / (1 - knee))))
    out = rgba.copy()
    out[..., :3] = cv2.cvtColor(np.stack([h, s, v], -1).astype(np.float32), cv2.COLOR_HSV2RGB)
    return out


@lru_cache(maxsize=None)
def sprite(name, variant="open"):
    rgba = _read(os.path.join(DIR, f"{name}_{variant}.png"))
    if rgba is None:
        return Sprite(_stand_in(name))
    return Sprite(_grade(rgba, name))


@lru_cache(maxsize=None)
def shadow(name):
    """The toy's shadow only, masked to the pool under it (the catcher's far floor faded out)."""
    rgba = _read(os.path.join(DIR, f"{name}_shadow.png"))
    if rgba is None:
        return None
    a = rgba[..., 3]
    h, w = a.shape
    wgt = a ** 6
    cy = float((wgt.sum(1) * np.arange(h)).sum() / max(wgt.sum(), 1e-6))
    cx = float((wgt.sum(0) * np.arange(w)).sum() / max(wgt.sum(), 1e-6))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot((xx - cx) / (0.42 * w), (yy - cy) / (0.12 * h))
    mask = np.clip(1.4 - d, 0, 1) ** 1.5
    out = np.zeros_like(rgba)
    out[..., 3] = a * mask
    return _image(out)


def _stand_in(name):
    n = 360
    arr = np.zeros((n, n, 4), np.uint8)
    s = skia.Surface(arr)
    col = COLOURS[name]
    with s as c:
        c.clear(skia.Color4f(0, 0, 0, 0))
        c.drawCircle(n / 2, n * 0.55, n * 0.3, G.P(col))
    return arr.astype(np.float32) / 255.0


def agent(c, name, x, y, size, t=0.0, variant="open", s=1.0, lift=0.0, squash=0.0, tilt=0.0, shadow_a=1.0,
          a=1.0):
    """A toy with its feet at (x, y - lift), its picture size px square, its shadow staying on the floor at y.
    s scales it (for popping in); squash > 0 flattens it as it lands, < 0 stretches it as it jumps."""
    if s <= 0.01 or a <= 0:
        return
    S = size * s
    sp = sprite(name, variant)
    with G.layer(c, a):
        sh = shadow(name)
        if sh is not None and shadow_a > 0:
            k = 1.0 / (1.0 + 2.5 * lift / max(size, 1))
            with G.layer(c, shadow_a * k):
                with G.xf(c, x, y, s=k):
                    c.drawImageRect(sh, skia.Rect.MakeXYWH(-S * sp.foot_x, -S * sp.foot_y, S, S),
                                    skia.SamplingOptions(skia.FilterMode.kLinear))
        sx, sy = 1 + 0.16 * squash, 1 - 0.16 * squash
        with G.xf(c, x, y - lift, sx=sx, sy=sy, rot=tilt):
            c.drawImageRect(sp.img, skia.Rect.MakeXYWH(-S * sp.foot_x, -S * sp.foot_y, S, S),
                            skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))


def hop(t, t0, period=0.62, height=0.06):
    """(lift as a fraction of size, squash) for a little bounce in place."""
    ph = ((t - t0) % period) / period
    lift = height * math.sin(math.pi * ph)
    squash = 0.4 * max(0.0, 1 - ph / 0.12) - 0.2 * math.sin(math.pi * ph)
    return lift, squash


def blinking(t, seed):
    """For the toys that can shut their eyes: now and then, for a moment, they do (a slow, happy blink)."""
    period = 3.1 + 1.6 * hash01(seed, 5)
    ph = (t + hash01(seed, 6) * period) % period
    return ph < 0.14
