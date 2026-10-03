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


def _warp(h, w, rng, amp):
    """A smooth random displacement field, for billows that are not round."""
    dx = (_fbm(h, w, rng, octaves=3, base=3) - 0.5) * amp
    dy = (_fbm(h, w, rng, octaves=3, base=3) - 0.5) * amp
    return dx, dy


@lru_cache(maxsize=None)
def cloud(seed, w, h):
    """One cumulus, w x h, as an RGBA image. Its density is a heap of billows on a flat base, warped and worn by
    noise; it is lit from the sun up and to the left by marching through its own density (so its tops glow and its
    folds and underside fall into cool shadow), with a silver lining where it is thin."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h
    dx, dy = _warp(h, w, rng, 0.08)
    uw, vw = u + dx, v + dy
    env = np.full((h, w), -1.0, np.float32)
    towers = []
    for k in range(rng.integers(5, 8)):                               # the main towers, taller in the middle
        cx = rng.uniform(0.18, 0.82)
        big = 1 - abs(cx - 0.5) * 1.5
        rx = rng.uniform(0.07, 0.11) + 0.1 * big
        top = 0.62 - (0.18 + 0.3 * big) * rng.uniform(0.7, 1.0)
        towers.append((cx, rx, top))
        cy = (top + 0.7) / 2
        ry = (0.7 - top) / 2 + 0.04
        env = np.maximum(env, 1 - ((uw - cx) / rx) ** 2 - ((vw - cy) / ry) ** 2)
    for cx, rx, top in towers:                                        # cauliflower billows round their tops
        for j in range(rng.integers(4, 7)):
            a = rng.uniform(-2.6, -0.5)
            bx = cx + math.cos(a) * rx * 0.85
            by = top + 0.1 + math.sin(a) * 0.12
            br = rx * rng.uniform(0.3, 0.5)
            env = np.maximum(env, 1 - ((uw - bx) / br) ** 2 - ((vw - by) / (br * w / h * 0.9)) ** 2)
    n = _fbm(h, w, rng, octaves=6, base=4)
    fine = _fbm(h, w, rng, octaves=4, base=28)
    edge = np.clip(np.minimum.reduce([u, 1 - u, v, 1 - v]) / 0.07, 0, 1)
    base = 0.76
    dens = (env + 0.55 * (n - 0.5) + 0.45 * (fine - 0.5) * np.clip(1.2 - env, 0, 1)) * edge
    dens *= np.clip((base - vw) / 0.035, 0, 1)
    dens = np.clip(dens, 0, None)
    depth = np.zeros_like(dens)
    sx, sy = -0.5, -0.9
    step = max(2, int(0.01 * w))
    for i in range(1, 16):
        ox, oy = int(round(sx * step * i)), int(round(sy * step * i))
        sh = np.roll(np.roll(dens, -oy, axis=0), -ox, axis=1)
        depth += sh * (1.0 - i / 18)
    light = np.exp(-0.3 * depth)
    ambient = 0.62 + 0.38 * np.clip(1 - vw / base, 0, 1)
    alpha = np.clip(dens / 0.18, 0, 1) ** 1.1
    lit = np.array([1.0, 1.0, 0.985], np.float32)
    shade = np.array([0.60, 0.67, 0.79], np.float32)
    k = np.clip(0.35 + 0.9 * light * ambient, 0, 1)[..., None]
    rgb = shade + (lit - shade) * k
    rim = np.clip(1 - alpha, 0, 1) * np.clip(light, 0, 1)
    rgb = np.clip(rgb + 0.1 * rim[..., None], 0, 1)
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
