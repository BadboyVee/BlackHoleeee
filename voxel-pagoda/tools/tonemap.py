#!/usr/bin/env python3
"""Turn the path tracer's linear float32 frame into a PNG/JPEG.

    python3 tools/tonemap.py frame.f32 3840 2160 render-4k.png [exposure]

Exposure, then the Khronos PBR Neutral tone curve (it leaves colours alone until they get
close to white, which keeps the vermilion and the blossoms honest), then sRGB.
The viewer in index.html applies the same curve.
"""
import sys
import numpy as np
from PIL import Image


def pbr_neutral(c):
    start, desat = 0.8 - 0.04, 0.15
    x = c.min(axis=-1, keepdims=True)
    offset = np.where(x < 0.08, x - 6.25 * x * x, 0.04)
    c = c - offset
    peak = c.max(axis=-1, keepdims=True)
    d = 1.0 - start
    new_peak = 1.0 - d * d / (np.maximum(peak, start) + d - start)
    scaled = c * (new_peak / np.maximum(peak, 1e-6))
    g = 1.0 - 1.0 / (desat * (peak - new_peak) + 1.0)
    out = scaled * (1 - g) + new_peak * g
    return np.where(peak < start, c, out)


def to_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def main():
    src, w, h, dst = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    exposure = float(sys.argv[5]) if len(sys.argv) > 5 else 0.62
    img = np.fromfile(src, dtype=np.float32, count=w * h * 3).reshape(h, w, 3).astype(np.float32)
    img = pbr_neutral(img * exposure)
    out = (to_srgb(img) * 255.0 + 0.5).astype(np.uint8)
    im = Image.fromarray(out, 'RGB')
    if dst.lower().endswith(('.jpg', '.jpeg')):
        im.save(dst, quality=93, subsampling=0, optimize=True)
    else:
        im.save(dst, optimize=True)


if __name__ == '__main__':
    main()
