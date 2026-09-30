"""HORIZON's plates: the hills and the sunset rendered with Blender (blender/hills.py), graded here, vivid and
clean. The hills come with their sky left clear, so the film's own sky and clouds show through. Without the
renders, a painted stand-in keeps the film whole."""
import os
from functools import lru_cache

import cv2
import numpy as np
import skia

from engine import gfx as G
from . import sky

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.environ.get("HORIZON_PLATES", os.path.join(HERE, "..", "out", "plates", "horizon"))
PW, PH = 2304, 1296                     # the plates are 1.2 x the frame, for the camera moves
HORIZON_Y = 470.0                       # where the sky meets the hills in plate pixels (for the sky's gradient)


def _image(rgba):
    return skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.ColorType.kRGBA_8888_ColorType,
                                alphaType=skia.AlphaType.kPremul_AlphaType)


def _grade_green(rgb):
    """Lush: greens pushed toward a sunlit yellow-green and saturated, a gentle S-curve on the values."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    green = np.clip(1 - np.abs(h - 100) / 50, 0, 1)
    s = np.clip(s * (1 + 1.15 * green), 0, 1)
    h = h - 12 * green
    v = np.clip((v - 0.5) * 1.22 + 0.5 + 0.035, 0, 1)
    return cv2.cvtColor(np.stack([h, s, v], -1), cv2.COLOR_HSV2RGB)


def _read(name):
    path = os.path.join(DIR, name)
    if not os.path.exists(path):
        return None
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    im = cv2.resize(im, (PW, PH), interpolation=cv2.INTER_AREA)
    scale = 65535.0 if im.dtype == np.uint16 else 255.0
    im = im.astype(np.float32) / scale
    if im.shape[2] == 3:
        im = np.concatenate([im, np.ones_like(im[..., :1])], -1)
    return np.concatenate([im[..., 2::-1], im[..., 3:]], -1)          # BGRA -> RGBA


@lru_cache(maxsize=None)
def hills():
    """The hills, graded, sky clear (premultiplied RGBA image)."""
    im = _read("hills.png")
    if im is None:
        return _painted_hills()
    rgb = _grade_green(np.clip(im[..., :3], 0, 1))
    a = im[..., 3:4]
    out = np.concatenate([rgb * a, a], -1)
    return _image(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8))


@lru_cache(maxsize=None)
def sunset():
    im = _read("sunset.png")
    if im is None:
        return _painted_sunset()
    rgb = np.clip(im[..., :3], 0, 1)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.12, 0, 1)
    hsv[..., 2] = np.clip((hsv[..., 2] - 0.5) * 1.1 + 0.5, 0, 1)
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    out = np.concatenate([rgb, np.ones_like(rgb[..., :1])], -1)
    return _image(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8))


def _painted_hills():
    """A stand-in when the render is missing: three soft green rises."""
    arr = np.zeros((PH, PW, 4), np.uint8)
    surf = skia.Surface(arr)
    with surf as c:
        c.clear(skia.Color4f(0, 0, 0, 0))
        for k, (y, col0, col1) in enumerate([(560, "#9fcf6a", "#6aa83a"), (700, "#7fc24a", "#3f8a22"),
                                             (860, "#6cb83a", "#2f7a18")]):
            p = skia.Path()
            p.moveTo(0, PH)
            for x in range(0, PW + 64, 64):
                p.lineTo(x, y - 60 * np.sin(x / (380 + 90 * k) + k * 1.7) - 30 * np.sin(x / 170 + k))
            p.lineTo(PW, PH)
            p.close()
            c.drawPath(p, G.P(col0, 1, shader=G.linear_grad(0, y - 90, 0, PH, [col0, col1])))
    return _image(arr)


def _painted_sunset():
    arr = np.zeros((PH, PW, 4), np.uint8)
    surf = skia.Surface(arr)
    with surf as c:
        c.drawRect(skia.Rect.MakeWH(PW, PH * 0.52), G.P("#ff8a3d", 1, shader=G.linear_grad(
            0, 0, 0, PH * 0.52, ["#2a2350", "#b85a6a", "#ff9a3c"])))
        c.drawRect(skia.Rect.MakeLTRB(0, PH * 0.52, PW, PH), G.P("#3a2320", 1, shader=G.linear_grad(
            0, PH * 0.52, 0, PH, ["#9a5a3a", "#1a1216"])))
        c.drawCircle(PW / 2, PH * 0.47, 60, G.P("#fff0c8"))
    return _image(arr)


def _day_content(c, t):
    sky.gradient(c, -200, -400, PW + 400, PH + 400, HORIZON_Y)
    sky.clouds(c, t, dy=-30)
    c.drawImageRect(hills(), skia.Rect.MakeWH(PW, PH), skia.SamplingOptions(skia.FilterMode.kLinear))


@lru_cache(maxsize=None)
def day_soft(radius):
    """The whole day plate, sky and clouds included, out of focus, made once: for the shots with something sharp
    in front of it."""
    pad = int(radius * 3)
    arr = np.zeros((PH + 2 * pad, PW + 2 * pad, 4), np.uint8)
    surf = skia.Surface(arr)
    with surf as c:
        c.clear(skia.Color4f(0, 0, 0, 1))
        c.translate(pad, pad)
        c.drawRect(skia.Rect.MakeLTRB(-pad, -pad, PW + pad, PH + pad), G.P("#3d7a22"))
        _day_content(c, 0.0)
    img = cv2.GaussianBlur(arr, (0, 0), radius)[pad:pad + PH, pad:pad + PW].copy()
    img[..., 3] = 255
    return _image(img)


def day(c, t, zoom=1.0, cx=0.5, cy=0.5, cloud_t=None, drift=0.0, soft=0.0):
    """The hills under the sky with its clouds, filling the frame: zoom 1 shows the whole plate's width scaled
    to the frame; (cx, cy) is the plate point (0..1) held at the frame's centre. soft: out of focus by that
    radius (in plate pixels)."""
    k = 1920.0 / PW * zoom
    ox = 960 - cx * PW * k + drift
    oy = 540 - cy * PH * k
    with G.xf(c, ox, oy, s=k):
        if soft > 0:
            c.drawImageRect(day_soft(soft), skia.Rect.MakeWH(PW, PH), skia.SamplingOptions(skia.FilterMode.kLinear))
        else:
            _day_content(c, cloud_t if cloud_t is not None else t)


def dusk(c, t, zoom=1.0, cx=0.5, cy=0.5):
    k = 1920.0 / PW * zoom
    with G.xf(c, 960 - cx * PW * k, 540 - cy * PH * k, s=k):
        c.drawImageRect(sunset(), skia.Rect.MakeWH(PW, PH), skia.SamplingOptions(skia.FilterMode.kLinear))


def preload():
    hills()
    sunset()
    for r in SOFT:
        day_soft(r)


SOFT = (4.0, 5.0, 8.0)
