"""Tomo himself: busts rendered in Blender (blender/tomo.py) in three head turns, with his eyes lit on the visor
here (blue LED pills with a glow), so they can look about, blink, wink and smile. And the things he does."""
import json
import os
from functools import lru_cache

import cv2
import numpy as np
import skia

from engine import gfx as G
from .look import LED

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.environ.get("TOMO_RENDERS", os.path.join(HERE, "..", "out", "plates", "tomo"))
TURNS = [-16, 0, 16]


def _read(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED) if os.path.exists(path) else None
    if im is None:
        return None
    im = im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)
    rgba = np.concatenate([im[..., 2::-1], im[..., 3:4]], -1)
    rgba[..., :3] *= rgba[..., 3:4]
    return rgba


def _image(rgba):
    return skia.Image.fromarray(np.ascontiguousarray(np.clip(rgba * 255 + 0.5, 0, 255).astype(np.uint8)),
                                colorType=skia.ColorType.kRGBA_8888_ColorType,
                                alphaType=skia.AlphaType.kPremul_AlphaType)


class Bust:
    def __init__(self, turn):
        rgba = _read(os.path.join(DIR, f"bust_{turn}.png"))
        meta = os.path.join(DIR, f"bust_{turn}.json")
        if rgba is None or not os.path.exists(meta):
            rgba, eyes, size = _stand_in()
        else:
            with open(meta) as fh:
                m = json.load(fh)
            size = m["size"][0]
            eyes = m["eyes"]
        self.img = _image(rgba)
        self.size = float(size)
        self.eyes = [(x / size, y / size) for x, y in eyes]            # as fractions of the picture
        self.mid = ((self.eyes[0][0] + self.eyes[1][0]) / 2, (self.eyes[0][1] + self.eyes[1][1]) / 2)
        self.gap = abs(self.eyes[1][0] - self.eyes[0][0])


def _stand_in():
    n = 600
    arr = np.zeros((n, n, 4), np.uint8)
    s = skia.Surface(arr)
    with s as c:
        c.clear(skia.Color4f(0, 0, 0, 0))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(150, 360, 300, 240), 60, 60), G.P("#e9ebef"))
        c.drawCircle(300, 250, 150, G.P("#e9ebef"))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(185, 200, 230, 100), 40, 40), G.P("#08080a"))
    return arr.astype(np.float32) / 255.0, [(255, 250), (345, 250)], n


@lru_cache(maxsize=None)
def bust(turn):
    return Bust(turn)


class Pose:
    def __init__(self, turn=0, look=(0.0, 0.0), blink=0.0, wink=0.0, happy=0.0, tilt=0.0, glow=1.0):
        self.turn, self.look, self.blink, self.wink, self.happy, self.tilt, self.glow = \
            turn, look, blink, wink, happy, tilt, glow


def eyes(c, b, S, pose):
    """The two LED eyes, in picture space scaled to S: pills that squash to a line to blink, and turn to arcs to
    smile (one of them, to wink)."""
    w, h = b.gap * S * 0.28, b.gap * S * 0.42
    lx, ly = pose.look
    for i, (ex, ey) in enumerate(b.eyes):
        x = ex * S + lx * b.gap * S * 0.18
        y = ey * S + ly * b.gap * S * 0.12
        arc = pose.happy if i == 0 else max(pose.happy, pose.wink)
        if arc > 0.5:
            p = skia.Path()
            p.moveTo(x - w * 0.7, y + h * 0.12)
            p.quadTo(x, y - h * 0.62, x + w * 0.7, y + h * 0.12)
            for blur, a, width in [(w * 0.5, 0.55, w * 0.55), (0.0, 1.0, w * 0.28)]:
                c.drawPath(p, G.P(LED, a * pose.glow, stroke=width, cap="round", blur=blur))
            continue
        hh = max(w * 0.22, h * (1 - pose.blink))
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - hh / 2, w, hh), w / 2, w / 2)
        c.drawRRect(r, G.P(LED, 0.55 * pose.glow, blur=w * 0.55))
        c.drawRRect(r, G.P(LED, pose.glow))
        core = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w * 0.28, y - hh * 0.4, w * 0.56, hh * 0.8), w * 0.28,
                                     w * 0.28)
        c.drawRRect(core, G.P("#dff0ff", 0.85 * pose.glow))


def tomo(c, x, y, size, pose=None, a=1.0):
    """Tomo with the middle of his eyes at (x, y); size is the picture's width in px."""
    pose = pose or Pose()
    b = bust(pose.turn)
    S = size
    with G.layer(c, a):
        with G.xf(c, x, y, rot=pose.tilt):
            c.translate(-b.mid[0] * S, -b.mid[1] * S)
            c.drawImageRect(b.img, skia.Rect.MakeWH(S, S), skia.SamplingOptions(skia.FilterMode.kLinear,
                                                                                skia.MipmapMode.kLinear))
            eyes(c, b, S, pose)


# ---------------------------------------------------------------- the things he does

@lru_cache(maxsize=None)
def thing(name):
    """A product render, premultiplied, its catcher shadow kept to the pool under it, cropped to its bounds."""
    rgba = _read(os.path.join(DIR, f"{name}.png"))
    if rgba is None:
        n = 400
        rgba = np.zeros((n, n, 4), np.float32)
        yy, xx = np.mgrid[0:n, 0:n]
        m = ((xx - n / 2) ** 2 + (yy - n / 2) ** 2) < (n * 0.3) ** 2
        rgba[m] = (0.85, 0.85, 0.88, 1.0)
        return _image(rgba)
    a = rgba[..., 3]
    h, w = a.shape
    solid = a > 0.95
    ys, xs = np.where(solid)
    if len(ys):
        cy, cx = ys.max(), (xs.min() + xs.max()) / 2
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.hypot((xx - cx) / (0.45 * w), (yy - cy) / (0.16 * h))
        mask = np.clip(1.3 - d, 0, 1)
        shade = ~solid
        rgba[shade] *= mask[shade][:, None]
    return _image(rgba)


def draw_thing(c, name, x, y, w, h):
    """Fit the render into the box, centred."""
    img = thing(name)
    s = min(w / img.width(), h / img.height())
    dw, dh = img.width() * s, img.height() * s
    c.drawImageRect(img, skia.Rect.MakeXYWH(x + (w - dw) / 2, y + (h - dh) / 2, dw, dh),
                    skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))


def preload():
    for t in TURNS:
        bust(t)
    for n in ("towels", "plates", "plant"):
        thing(n)
