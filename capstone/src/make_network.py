#!/usr/bin/env python3
"""Draw the cover picture for the part 2 deck: a dark navy background with a glowing network of
linked points on the right (a nod to cybersecurity), leaving the left side calm for the title.

Usage: python make_network.py out.jpg      (1920 x 1080 JPEG; the same picture every time)
"""
import math
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
NAVY, DEEP = (11, 37, 69), (6, 22, 43)
LINE, NODE, GLOW = (111, 168, 220), (141, 184, 232), (31, 111, 178)

rng = random.Random(7)
img = Image.new("RGB", (W, H), NAVY)
px = img.load()
# a soft diagonal gradient: darker at the bottom left
for y in range(H):
    for x in range(0, W, 4):
        t = min(1.0, max(0.0, (x / W) * 0.6 + (1 - y / H) * 0.4))
        c = tuple(int(DEEP[i] + (NAVY[i] - DEEP[i]) * t) for i in range(3))
        for dx in range(4):
            if x + dx < W:
                px[x + dx, y] = c

# points, thicker towards the right-hand side
points = []
while len(points) < 140:
    x, y = rng.uniform(0.38, 1.02) * W, rng.uniform(-0.02, 1.02) * H
    if rng.random() < (x / W - 0.3) * 1.4:
        points.append((x, y))

layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(layer)
for i, (x, y) in enumerate(points):                  # each point linked to its three nearest
    near = sorted(points, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)[1:4]
    for nx, ny in near:
        alpha = int(40 + 70 * (x / W))
        draw.line([(x, y), (nx, ny)], fill=LINE + (alpha,), width=2)
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gdraw = ImageDraw.Draw(glow)
for x, y in points:
    r = rng.choice([3, 4, 5, 7])
    draw.ellipse([x - r, y - r, x + r, y + r], fill=NODE + (220,))
    if r >= 5:
        gdraw.ellipse([x - 22, y - 22, x + 22, y + 22], fill=GLOW + (120,))
glow = glow.filter(ImageFilter.GaussianBlur(14))
# a large faint ring, centred off the right edge
ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rdraw = ImageDraw.Draw(ring)
cx, cy, rad = int(W * 0.86), int(H * 0.52), 430
for k in range(3):
    rr = rad + k * 70
    rdraw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=LINE + (34 - k * 9,), width=3)
img = img.convert("RGBA")
for over in (ring, glow, layer):
    img = Image.alpha_composite(img, over)
img.convert("RGB").save(sys.argv[1], quality=90)
print(f"wrote {sys.argv[1]}")
