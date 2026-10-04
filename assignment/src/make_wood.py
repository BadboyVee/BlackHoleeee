#!/usr/bin/env python3
"""Draw the wood background used by the PZ-style slides: warm orange-brown wood with grain
running across the slide, like the wood design of the PZ Nigeria Limited deck.

Usage: python make_wood.py wood.jpg
"""
import sys

import numpy as np
from PIL import Image

W, H = 1920, 1080                                 # 16:9, the slide's shape
rng = np.random.default_rng(2026)


def noise(step_y, step_x):
    """Smooth random noise in -0.5..0.5: coarse random values, smoothly enlarged."""
    small = rng.random((H // step_y + 2, W // step_x + 2))
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    return np.asarray(img, dtype=float) / 255 - 0.5


y = np.arange(H, dtype=float)[:, None]
u = y + noise(90, 480) * 120 + noise(30, 160) * 18             # grain lines, gently wavy
rings = (u / 46.0) % 1.0
rings = 1 - np.abs(rings - 0.5) * 2                              # soft bands
fibres = noise(2, 90)                                            # fine streaks along the grain
patches = noise(270, 640)                                        # large light and dark areas
t = np.clip(0.42 * rings + 0.38 * (fibres + 0.5) + 0.45 * patches + 0.12, 0, 1)

dark = np.array([112, 60, 26], dtype=float)                      # 703C1A
light = np.array([196, 124, 62], dtype=float)                    # C47C3E
rgb = dark + (light - dark) * t[..., None]
Image.fromarray(rgb.clip(0, 255).astype(np.uint8)).save(sys.argv[1], quality=86)
print(f"wrote {sys.argv[1]}")
