"""HORIZON's sky: a clear blue gradient, cumulus clouds painted once from soft puffs and drifted across it, and a
few birds."""
import math
from functools import lru_cache

import cv2
import numpy as np
import skia

from engine import gfx as G
from engine.core import hash01

ZENITH, HORIZON = "#2c6fdc", "#d4e8fb"


def gradient(c, x, y, w, h, horizon_y):
    """The sky from (x, y) to horizon_y: deep blue overhead, pale at the horizon."""
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), G.P(ZENITH, 1, shader=G.linear_grad(
        0, y, 0, horizon_y, [ZENITH, "#5b94ea", HORIZON], [0.0, 0.55, 1.0])))


def _fbm(h, w, rng, octaves=5, base=4):
    """Value-noise fbm in 0..1: random grids, finer each octave, blown up smoothly and summed."""
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for k in range(octaves):
        gh, gw = base * 2 ** k + 1, int(base * 2 ** k * w / h) + 1
        g = rng.random((gh, gw)).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.5
    return np.clip(out / tot, 0, 1)


@lru_cache(maxsize=None)
def cloud(seed, w, h):
    """One cumulus, w x h, as an RGBA image: towers heaped on a flat base, their edges worn by noise, white where
    the sun catches the tops and a cool grey underneath."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h
    env = np.full((h, w), -1.0, np.float32)
    for k in range(rng.integers(8, 12)):                    # the towers: big ones in the middle, small ones about
        cx = rng.uniform(0.18, 0.82)
        big = 1 - abs(cx - 0.5) * 1.6
        cy = rng.uniform(0.42, 0.66) - 0.12 * big
        rx = rng.uniform(0.07, 0.13) + 0.10 * big
        ry = rx * w / h * rng.uniform(0.75, 1.0)
        env = np.maximum(env, 1 - ((u - cx) / rx) ** 2 - ((v - cy) / ry) ** 2)
    n = _fbm(h, w, rng)
    fine = _fbm(h, w, rng, octaves=3, base=16)
    edge = np.clip(np.minimum.reduce([u, 1 - u, v, 1 - v]) / 0.08, 0, 1)
    dens = (env + 0.6 * (n - 0.5) + 0.22 * (fine - 0.5)) * edge
    base = 0.8
    dens *= np.clip((base - v) / 0.035, 0, 1)               # a flat bottom, softly cut
    alpha = np.clip((dens - 0.05) / 0.18, 0, 1)
    light = np.clip(1.0 - 0.55 * np.clip((v - 0.3) / (base - 0.3), 0, 1) ** 1.2 + 0.16 * (fine - 0.5)
                    - 0.10 * (1 - np.clip(dens * 2.5, 0, 1)), 0, 1)
    top = np.array([1.0, 1.0, 1.0], np.float32)
    under = np.array([0.66, 0.73, 0.86], np.float32)
    rgb = under + (top - under) * light[..., None]
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(rgb * alpha[..., None] * 255, 0, 255)
    out[..., 3] = np.clip(alpha * 255, 0, 255)
    return skia.Image.fromarray(out, colorType=skia.ColorType.kRGBA_8888_ColorType,
                                alphaType=skia.AlphaType.kPremul_AlphaType)


CLOUDS = [   # (seed, x, y, width, height, drift px/s): a bank along the horizon and a few big ones above
    (3, -80, 170, 620, 300, 9.0), (8, 520, 220, 460, 230, 7.0), (13, 980, 120, 760, 380, 10.0),
    (21, 1720, 200, 560, 280, 8.0), (34, 2200, 150, 640, 320, 9.5), (5, 300, 420, 420, 150, 5.0),
    (17, 1350, 440, 380, 140, 5.5), (29, 1850, 430, 460, 160, 6.0),
]


def clouds(c, t, dx=0.0, dy=0.0, scale=1.0, a=1.0, blur=0.0):
    with G.layer(c, a, blur=blur):
        for seed, x, y, w, h, v in CLOUDS:
            img = cloud(seed, int(w), int(h))
            xx = (x - v * t + dx) * scale
            G.draw_image(c, img, xx, (y + dy) * scale, w * scale, h * scale)


def birds(c, t, t0, n=9, x0=1500.0, y0=300.0, vx=-160.0, vy=-18.0, size=14.0, col="#1d2b1e", seed=4):
    """A loose flock crossing the sky from t0, each bird's wings beating on its own clock."""
    tau = t - t0
    if tau < 0:
        return
    p = G.P(col, 0.85, stroke=size * 0.16, cap="round", join="round")
    for i in range(n):
        ox = (hash01(i, seed) - 0.5) * 420
        oy = (hash01(i, seed + 1) - 0.5) * 170
        x = x0 + ox + vx * tau * (0.9 + 0.2 * hash01(i, seed + 2))
        y = y0 + oy + vy * tau + 6 * math.sin(tau * 1.3 + i)
        s = size * (0.7 + 0.6 * hash01(i, seed + 3))
        f = math.sin(2 * math.pi * (tau * (3.2 + hash01(i, seed + 4)) + hash01(i, seed + 5)))
        w = skia.Path()
        w.moveTo(x - s, y - s * 0.35 * f)
        w.quadTo(x - s * 0.45, y - s * (0.25 + 0.35 * f), x, y)
        w.quadTo(x + s * 0.45, y - s * (0.25 + 0.35 * f), x + s, y - s * 0.35 * f)
        c.drawPath(w, p)
