"""Cut the NFT characters out of their reference images.

Run with:  python3 -I tools/cutouts.py   (from unknown-general/)

Reads assets/ref/*.jpg, writes transparent PNGs to assets/cut/. Only background
pixels connected to the image border are removed, so the art itself is untouched.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
REF, OUT = ROOT / "assets" / "ref", ROOT / "assets" / "cut"


def load(name):
    return np.asarray(Image.open(REF / name).convert("RGB")).astype(np.float32) / 255.0


def hsv(a):
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    return sat, mx


def corner_mask(h, w, r):
    """True outside a rounded rectangle (the screenshot's rounded corners)."""
    y, x = np.mgrid[0:h, 0:w]
    cx = np.clip(x, r, w - 1 - r)
    cy = np.clip(y, r, h - 1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 > r * r


def border_strip(h, w, t):
    m = np.zeros((h, w), bool)
    m[:t, :] = m[-t:, :] = True
    m[:, :t] = m[:, -t:] = True
    return m


def grow_from_border(cand, seed=None):
    """Pixels of `cand` 4-connected to the border (or to `seed`)."""
    reg = np.zeros_like(cand)
    if seed is None:
        reg[0, :] = cand[0, :]; reg[-1, :] = cand[-1, :]
        reg[:, 0] = cand[:, 0]; reg[:, -1] = cand[:, -1]
    else:
        reg = seed & cand
    for _ in range(5000):
        n = reg.copy()
        n[1:, :] |= reg[:-1, :]; n[:-1, :] |= reg[1:, :]
        n[:, 1:] |= reg[:, :-1]; n[:, :-1] |= reg[:, 1:]
        n &= cand
        if (n == reg).all():
            break
        reg = n
    return reg


def dilate(m, k):
    for _ in range(k):
        n = m.copy()
        n[1:, :] |= m[:-1, :]; n[:-1, :] |= m[1:, :]
        n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
        m = n
    return m


def finish(a, bg, dist, soft0, soft1, name, crop_pad=6, keep_box=None):
    """bg: hard background mask. dist: per-pixel distance from bg colour."""
    edge = dilate(bg, 2) & ~bg
    alpha = np.ones(bg.shape, np.float32)
    alpha[bg] = 0
    alpha[edge] = np.clip((dist[edge] - soft0) / (soft1 - soft0), 0, 1)
    # bridge the single-pixel noise of JPEG grain on the fringe
    rgba = np.dstack([a, alpha])
    ys, xs = np.where(alpha > 0.02)
    y0, y1 = max(ys.min() - crop_pad, 0), min(ys.max() + crop_pad + 1, a.shape[0])
    x0, x1 = max(xs.min() - crop_pad, 0), min(xs.max() + crop_pad + 1, a.shape[1])
    if keep_box:
        x0, y0, x1, y1 = keep_box
    out = (np.clip(rgba[y0:y1, x0:x1], 0, 1) * 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(OUT / name, optimize=True)
    print(name, "crop", (x0, y0, x1, y1), "size", out.shape[1], "x", out.shape[0])
    return (x0, y0, x1, y1)


def bear():
    a = load("crowned-bear.jpg")
    h, w, _ = a.shape
    bgc = np.array([151, 154, 202]) / 255
    d = np.sqrt(((a - bgc) ** 2).sum(-1)) * 255
    rim = border_strip(h, w, 10)
    cand = (d < 34) | corner_mask(h, w, 46) | rim
    bg = grow_from_border(cand) | corner_mask(h, w, 46) | rim
    finish(a, bg, d, 30, 70, "crowned-bear.png")


def fish():
    a = load("blind-fish.jpg")
    h, w, _ = a.shape
    sat, val = hsv(a)
    rim = border_strip(h, w, 10)
    cand = ((sat < 0.07) & (val > 0.45) & (val < 0.93)) | corner_mask(h, w, 46) | rim
    bg = grow_from_border(cand) | corner_mask(h, w, 46) | rim
    # distance from the local grey for the soft edge
    grey = a.mean(-1, keepdims=True)
    d = np.sqrt(((a - grey) ** 2).sum(-1)) * 255 + np.clip(0.55 - val, 0, 1) * 400
    finish(a, bg, d, 12, 40, "blind-fish.png")


def bucket():
    """The bucket-hat NFT is cropped by its own frame (hat top, right cheek).

    The background is removed from the left side only, then the cropped edges
    are closed in the original's style: edge colours carried outward under a
    thick black outline, so the figure can stand whole in a wide shot.
    """
    from PIL import ImageDraw, ImageFilter
    a = load("bucket-hat.jpg")
    h, w, _ = a.shape
    a = a[:, : w - 16]         # drop the screenshot's right border
    h, w, _ = a.shape
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    bgc = np.array([238, 150, 148]) / 255
    d = np.sqrt(((a - bgc) ** 2).sum(-1)) * 255
    cand = (d < 52) & (r - g > 0.25)
    cm = corner_mask(h, w, 46)
    seed = np.zeros_like(cand)
    seed[:, 0] = True; seed[0, :300] = True; seed[-1, :420] = True
    bg = grow_from_border(cand | (cm & (np.arange(w)[None, :] < w / 2)), seed)
    edge = dilate(bg, 2) & ~bg
    alpha = np.ones((h, w), np.float32)
    alpha[bg] = 0
    alpha[edge] = np.clip((d[edge] - 45) / 50, 0, 1)
    alpha[cm & (np.arange(w)[None, :] >= w / 2)] = 0  # right-hand corner notches

    PT, PR, PB, S = 170, 190, 0, 3        # padding top/right, supersample
    W2, H2 = w + PR, h + PT + PB
    hat = np.array([62, 92, 222]) / 255
    face = np.array([236, 228, 212]) / 255
    shirt = np.array([244, 244, 244]) / 255

    # fill colours: the original's last column carried to the right
    fill = np.zeros((H2, W2, 3), np.float32)
    fill[PT:PT + h, :w] = a
    fill[PT:PT + h, w:] = np.median(a[:, w - 10:w - 4], 1)[:, None, :]
    fill[:PT, :] = hat
    fill[PT:PT + 60, w - 60:] = hat
    fill[PT + h - 60:PT + h, w - 60:] = shirt
    # smooth the carried columns so JPEG grain does not streak sideways
    car = Image.fromarray((fill[:, w - 12:] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
    fill[:, w - 12:] = np.asarray(car).astype(np.float32) / 255
    # the brow line at the right edge stops inside the face
    fill[PT + 600:PT + 640, w:] = face

    def mask(draw_fn):
        m = Image.new("L", (W2 * S, H2 * S), 0)
        draw_fn(ImageDraw.Draw(m), S)
        return np.asarray(m.resize((W2, H2), Image.LANCZOS)).astype(np.float32) / 255

    def ell(cx, cy, rx, ry):
        return lambda grow: lambda dr, s: dr.ellipse([(cx - rx - grow) * s, (cy - ry - grow) * s,
                                         (cx + rx + grow) * s, (cy + ry + grow) * s], fill=255)

    def poly(pts):
        return lambda grow: _poly(pts, grow)

    def _poly(pts, grow):
        def f(dr, s):
            c = np.mean(pts, 0)
            q = [((x - c[0]) * (1 + grow / 60) + c[0], (y - c[1]) * (1 + grow / 60) + c[1]) for x, y in pts]
            dr.polygon([(x * s, y * s) for x, y in q], fill=255)
        return f

    OUT_W = 26
    yellow = np.array([246, 218, 52]) / 255
    groups = [  # back-to-front; shapes in one group share an outline
        ([ell(w + 10, PT + 1080, 120, 150)], shirt),
        ([ell(w - 10, PT + 728, 92, 262)], None),                       # cheek
        ([ell(w - 30, PT + 205, 112, 252), ell(880, PT + 70, 455, 205)], hat),
        ([poly([(338, PT + 30), (440, PT + 30), (300, PT - 95)])], yellow),
    ]
    rng = np.random.default_rng(7)
    grain = rng.normal(0, 0.035, (H2, W2, 1)).astype(np.float32)
    ext = np.zeros((H2, W2, 4), np.float32)
    for shapes, col in groups:
        outer = np.zeros((H2, W2), np.float32)
        inner = np.zeros((H2, W2), np.float32)
        for sh in shapes:
            outer = np.maximum(outer, mask(sh(OUT_W)))
            inner = np.maximum(inner, mask(sh(0)))
        c = fill if col is None else np.broadcast_to(col, fill.shape)
        c = np.clip(c + grain, 0, 1)
        rgb = 0.04 * (1 - inner[..., None]) + c * inner[..., None]
        la = outer[..., None]
        ext[..., :3] = rgb * la + ext[..., :3] * (1 - la)
        ext[..., 3:4] = la + ext[..., 3:4] * (1 - la)

    # the original drawn over the extension
    orig = np.zeros((H2, W2, 4), np.float32)
    orig[PT:PT + h, :w, :3] = a
    orig[PT:PT + h, :w, 3] = alpha
    oa = orig[..., 3:4]
    prem = orig[..., :3] * oa + ext[..., :3] * (1 - oa)   # ext is premultiplied
    al = (oa + ext[..., 3:4] * (1 - oa))[..., 0]
    rgba = np.dstack([np.where(al[..., None] > 1e-3, prem / np.maximum(al[..., None], 1e-3), 0), al])
    ys, xs = np.where(al > 0.02)
    out = (np.clip(rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 0, 1) * 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(OUT / "bucket-hat.png", optimize=True)
    print("bucket-hat.png", out.shape[1], "x", out.shape[0], "origin", (-xs.min(), PT - ys.min()))


def pixel():
    """Pixel art: sample the native grid, classify each block, re-emit crisp."""
    a = load("pixel-shades.jpg")
    h, w, _ = a.shape
    # block size measured from the ray pattern (see README)
    bs = BLOCK
    gx, gy = OFFX, OFFY
    nx, ny = int((w - gx) // bs), int((h - gy) // bs)
    cols = np.zeros((ny, nx, 3), np.float32)
    for j in range(ny):
        for i in range(nx):
            cy, cx = int(gy + (j + .5) * bs), int(gx + (i + .5) * bs)
            cols[j, i] = np.median(a[cy - 6:cy + 7, cx - 6:cx + 7].reshape(-1, 3), 0)
    r, g, b = cols[..., 0], cols[..., 1], cols[..., 2]
    red = (r > 0.55) & (g < 0.45) & (b < 0.5) & (r - g > 0.3)
    white = (r > 0.93) & (g > 0.93) & (b > 0.93)
    black = (r < 0.08) & (g < 0.08) & (b < 0.08)
    cand = red | white | black
    bg = grow_from_border(cand)
    alpha = (~bg).astype(np.float32)
    ys, xs = np.where(alpha > 0)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    out = (np.dstack([cols, alpha])[y0:y1, x0:x1] * 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(OUT / "pixel-shades.png", optimize=True)
    print("pixel-shades.png native", out.shape[1], "x", out.shape[0], "grid", nx, ny)
    # the red/white rays, kept as the general's war-banner motif
    rays = np.dstack([cols, np.ones(cols.shape[:2], np.float32)])
    Image.fromarray((rays * 255).astype(np.uint8), "RGBA").save(OUT / "pixel-rays.png", optimize=True)


def green_eyes():
    """The main character: glowing green eyes, the red flame and the katana."""
    a = load("green-eyes.jpg")
    h, w, _ = a.shape
    sat, val = hsv(a)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = np.clip((g - np.maximum(r, b) - 0.06) / 0.25, 0, 1)
    redf = np.clip((r - np.maximum(g, b) - 0.12) / 0.25, 0, 1)
    bright = np.clip((val - 0.5) / 0.25, 0, 1) * (sat < 0.35)
    alpha = np.maximum.reduce([green, redf, bright])
    # keep the dark pupils/slits inside the eyes and the katana outline: dark
    # pixels close to coloured pixels are part of the drawing
    core = alpha > 0.5
    near = dilate(core, 10)
    dark = (val < 0.14) & near
    alpha = np.maximum(alpha, dark * 0.95)
    alpha *= ~corner_mask(h, w, 40)
    rgba = np.dstack([a, alpha])
    out = (np.clip(rgba, 0, 1) * 255).astype(np.uint8)
    # split into the eyes (with the red flame) and the katana with its green blade
    y, x = np.mgrid[0:h, 0:w]
    blade = (y > 745) | ((x > 1085) & (y > 690))
    for name, m in (("green-eyes-eyes.png", ~blade), ("green-eyes-katana.png", blade)):
        part = out.copy()
        part[..., 3] = (part[..., 3] * m).astype(np.uint8)
        ys, xs = np.where(part[..., 3] > 8)
        x0, y0, x1, y1 = xs.min() - 4, ys.min() - 4, xs.max() + 5, min(ys.max() + 5, h)
        Image.fromarray(part[y0:y1, x0:x1], "RGBA").save(OUT / name, optimize=True)
        print(name, "at", (int(x0), int(y0)), "size", int(x1 - x0), "x", int(y1 - y0))


BLOCK, OFFX, OFFY = 37.95, 25, 31

if __name__ == "__main__":
    which = sys.argv[1:] or ["bear", "fish", "bucket", "pixel", "green_eyes"]
    for k in which:
        globals()[k]()
