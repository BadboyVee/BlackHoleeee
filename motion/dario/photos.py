"""Optional photographs for the tribute.

Drop files into motion/photos/ and re-render:
    dario.jpg          a portrait of Dario Amodei (finale switches to a portrait layout)
    anthropic-hq.jpg   Anthropic's office / HQ (appears as a card in chapter 04)
    credit.txt         one line of photo credit, printed small in the finale

Nothing is invented: without the files the film renders its typographic layout.
"""
import os
from functools import lru_cache

import cv2
import numpy as np

from engine import gfx as G

PHOTO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "photos")


def _find(name):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = os.path.join(PHOTO_DIR, name + ext)
        if os.path.exists(p):
            return p
    return None


def available(name):
    return _find(name) is not None


@lru_cache(maxsize=8)
def duotone(name, w, h, dark, light, focus_y=0.4):
    """Cover-crop the photo to w×h and map its luminance onto a two-colour ramp, with a gentle S-curve."""
    p = _find(name)
    if p is None:
        return None
    img = cv2.imread(p, cv2.IMREAD_COLOR)
    ih, iw = img.shape[:2]
    s = max(w / iw, h / ih)
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_LANCZOS4
    img = cv2.resize(img, (int(iw * s + 0.5), int(ih * s + 0.5)), interpolation=interp)
    ih, iw = img.shape[:2]
    x0 = (iw - w) // 2
    y0 = int(np.clip((ih - h) * focus_y, 0, ih - h))
    img = img[y0:y0 + h, x0:x0 + w]
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    lo, hi = np.percentile(lum, 1.5), np.percentile(lum, 98.5)
    lum = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1)
    lum = lum * lum * (3 - 2 * lum)
    d = np.array(G.rgb(dark), np.float32)
    l_ = np.array(G.rgb(light), np.float32)
    rgb = d + (l_ - d) * lum[..., None]
    rgba = np.concatenate([rgb, np.ones((h, w, 1), np.float32)], axis=2)
    return G.image_from_rgba((rgba * 255 + 0.5).astype(np.uint8))


def aspect(name):
    p = _find(name)
    if p is None:
        return None
    h, w = cv2.imread(p, cv2.IMREAD_COLOR).shape[:2]
    return w / h


def credit():
    p = os.path.join(PHOTO_DIR, "credit.txt")
    if os.path.exists(p):
        with open(p) as fh:
            return fh.read().strip().upper()
    return None
