#!/usr/bin/env python3
"""Lagos 2090 - finishing pass. Turns the linear multilayer EXR frames that Cycles
writes (renders/shotN/f####.exr, Combined + Mist) into graded 1920x1080 PNG frames
(renders/final/lagos_####.png): aerial haze from the mist pass, bloom, anamorphic
streak + lens ghosts where the sun is in frame, AgX-style tone mapping, grade,
vignette, film grain, dust / pollen motes, rainbow light leaks (shot 7), Montserrat
Light credits with smooth fades, and the closing title card.

    python scripts/post.py                # all shots, all frames present
    python scripts/post.py --shot 3       # one shot
    python scripts/post.py --still 3:45 out.png   # one frame, for look-dev
"""
import argparse, math, os, sys
from pathlib import Path
from multiprocessing import Pool

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import numpy as np
import cv2
import OpenEXR
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RENDERS = ROOT / "renders"
FINAL = RENDERS / "final"
FONT = ROOT / "fonts" / "Montserrat-Light.ttf"
W, H, N = 1920, 1080, 90
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lagos.shots import SHOTS  # noqa: E402  (pure-python shot table: post params + credits)

LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


# ----------------------------------------------------------------------------- io
def read_exr(path):
    f = OpenEXR.File(str(path))
    ch = f.channels()
    rgb = mist = None
    for name, c in ch.items():
        low = name.lower()
        px = c.pixels
        if px.ndim == 3 and px.shape[2] >= 3 and ("combined" in low or low in ("rgba", "rgb")) and rgb is None:
            rgb = px[..., :3].astype(np.float32)
        elif "mist" in low:
            mist = (px[..., 0] if px.ndim == 3 else px).astype(np.float32)
    if rgb is None:  # separate R/G/B channels
        def find(s):
            for name, c in ch.items():
                if name.lower().endswith("combined." + s) or name.lower() == s:
                    return c.pixels.astype(np.float32)
        rgb = np.dstack([find("r"), find("g"), find("b")])
    if mist is None:
        mist = np.zeros(rgb.shape[:2], np.float32)
    if rgb.shape[0] != H or rgb.shape[1] != W:
        rgb = cv2.resize(rgb, (W, H), interpolation=cv2.INTER_LANCZOS4)
        mist = cv2.resize(mist, (W, H), interpolation=cv2.INTER_LINEAR)
    return np.nan_to_num(rgb, nan=0.0, posinf=50.0, neginf=0.0), np.clip(mist, 0, 1)


# ----------------------------------------------------------------------------- optics
def smooth(x, a, b):
    t = np.clip((x - a) / (b - a + 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


def haze(rgb, mist, p):
    """Aerial perspective. mist is linear distance / 1000 m."""
    if not p:
        return rgb
    dist = mist * 1000.0
    t = 1.0 - np.exp(-np.maximum(dist - p.get("start", 0.0), 0) * p["density"])
    t = np.minimum(t, p.get("max", 0.92))[..., None]
    col = np.array(p["color"], np.float32)
    if "sun_xy" in p:  # brighten the haze towards the sun for a backlit glow
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        sx, sy = p["sun_xy"]
        r = np.hypot((xx - sx * W) / W, (yy - sy * H) / W)
        col = col[None, None, :] * (1.0 + p.get("sun_gain", 1.5) * np.exp(-(r / p.get("sun_radius", 0.35)) ** 2))[..., None]
    return rgb * (1 - t) + col * t


def bloom(rgb, strength=0.12, threshold=1.0, streak=0.0, streak_tint=(0.55, 0.75, 1.0)):
    lum = rgb @ LUMA
    hi = rgb * (np.maximum(lum - threshold, 0) / (lum + 1e-4))[..., None]
    hi = np.minimum(hi, 40.0)
    small = cv2.resize(hi, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    acc = np.zeros_like(small)
    for sigma, wgt in ((1.5, 0.45), (5, 0.3), (14, 0.17), (40, 0.08)):
        acc += cv2.GaussianBlur(small, (0, 0), sigma) * wgt
    out = rgb + cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR) * strength * 4.0
    if streak > 0:  # anamorphic horizontal streak from the very brightest pixels
        very = small * smooth(small @ LUMA, 2.0, 8.0)[..., None]
        s = cv2.GaussianBlur(very, (0, 0), sigmaX=70, sigmaY=0.8) * 1.0 + cv2.GaussianBlur(very, (0, 0), sigmaX=22, sigmaY=0.6) * 0.6
        s = cv2.resize(s, (W, H), interpolation=cv2.INTER_LINEAR)
        out += (s @ LUMA)[..., None] * np.array(streak_tint, np.float32) * streak * 6.0
    return out


def lens_ghosts(rgb, sun_xy, strength=0.25):
    """A few soft ghosts mirrored through the frame centre from the sun position."""
    sx, sy = sun_xy[0] * W, sun_xy[1] * H
    cx, cy = W / 2, H / 2
    vis = float(np.clip((rgb[int(np.clip(sy, 0, H - 1)), int(np.clip(sx, 0, W - 1))] @ LUMA) / 20.0, 0, 1)) if (0 <= sx < W and 0 <= sy < H) else 0.6
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    out = rgb.copy()
    ghosts = [(-0.35, 46, (1.0, 0.55, 0.25), 0.5, False), (-0.6, 90, (0.35, 0.8, 0.5), 0.22, True),
              (-0.9, 30, (0.5, 0.6, 1.0), 0.45, False), (-1.35, 150, (1.0, 0.45, 0.6), 0.14, True),
              (0.4, 22, (1.0, 0.8, 0.4), 0.4, False), (-1.8, 240, (0.4, 0.55, 1.0), 0.07, True)]
    for k, rad, col, a, ring in ghosts:
        gx, gy = cx + (sx - cx) * k, cy + (sy - cy) * k
        r = np.hypot(xx - gx, yy - gy) / rad
        m = np.exp(-((r - 0.85) / 0.16) ** 2) + 0.25 * (r < 0.85) if ring else np.exp(-(r ** 2) * 1.8)
        out += m[..., None] * np.array(col, np.float32) * (a * strength * vis)
    return out


# ----------------------------------------------------------------------------- tone
_AGX = np.array([[0.842479062253094, 0.0784335999999992, 0.0792237451477643],
                 [0.0423282422610123, 0.878468636469772, 0.0791661274605434],
                 [0.0423756549057051, 0.0784336, 0.879142973793104]], np.float32)
_AGX_INV = np.array([[1.19687900512017, -0.0980208811401368, -0.0990297440797205],
                     [-0.0528968517574562, 1.15190312990417, -0.0989611768448433],
                     [-0.0529716355144438, -0.0980434501171241, 1.15107367264116]], np.float32)


def agx(rgb, power=1.2, sat=1.12):
    """AgX base curve (minimal approximation) with a mild 'punchy' look. Returns
    display-referred sRGB-encoded values in 0..1."""
    v = np.maximum(rgb, 0) @ _AGX.T
    v = np.clip(np.log2(np.maximum(v, 1e-10)), -12.47393, 4.026069)
    x = (v + 12.47393) / (4.026069 + 12.47393)
    x2 = x * x; x4 = x2 * x2
    v = 15.5 * x4 * x2 - 40.14 * x4 * x + 31.96 * x4 - 6.868 * x2 * x + 0.4298 * x2 + 0.1191 * x - 0.00232
    v = np.clip(v, 0, 1)
    luma = (v @ LUMA)[..., None]
    v = np.power(v, power)
    v = luma ** power + sat * (v - luma ** power)
    v = np.clip(v @ _AGX_INV.T, 0, 1)
    # the AgX output above is a 2.2-gamma display signal; convert to the sRGB OETF
    lin = np.power(v, 2.2)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(np.maximum(lin, 1e-8), 1 / 2.4) - 0.055)


def grade(img, p):
    """Display-space grade: lift/gain, gentle split toning, saturation."""
    g = p or {}
    img = img * np.array(g.get("gain", (1, 1, 1)), np.float32)
    lum = (img @ LUMA)[..., None]
    sh = np.array(g.get("shadow_tint", (0.0, 0.012, 0.022)), np.float32)   # cool, slightly lifted shadows
    hl = np.array(g.get("highlight_tint", (0.03, 0.012, -0.02)), np.float32)  # warm highlights
    img = img + sh * (1 - lum) ** 2 + hl * lum ** 2
    c = g.get("contrast", 1.04)
    img = (img - 0.5) * c + 0.5 + g.get("lift", 0.012)
    lum = (img @ LUMA)[..., None]
    img = lum + (img - lum) * g.get("sat", 1.06)
    return np.clip(img, 0, 1)


_vig = None


def vignette(img, k=0.22):
    global _vig
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r2 = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (W / 2)) ** 2
        _vig = r2
    return img * (1.0 - k * smooth(_vig, 0.25, 1.45))[..., None]


def grain(img, gframe, amount=0.017):
    rng = np.random.default_rng(90210 + gframe)
    n = rng.standard_normal((H, W)).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), 0.7) * 1.9
    lum = img @ LUMA
    w = 0.35 + 0.65 * (1 - np.abs(lum * 2 - 1))          # strongest in the mid-tones
    chroma = rng.standard_normal((H // 2, W // 2, 3)).astype(np.float32)
    chroma = cv2.resize(chroma, (W, H), interpolation=cv2.INTER_LINEAR) * 0.25
    return np.clip(img + (n[..., None] + chroma) * (amount * w)[..., None], 0, 1)


# ----------------------------------------------------------------------------- particles
def motes(rgb, f, p):
    """Dust / pollen: pseudo-3D drifting specks, additive in linear light, brighter where
    the plate is bright behind them (they catch the same light)."""
    rng = np.random.default_rng(p.get("seed", 7))
    n = p.get("count", 140)
    base = rng.random((n, 6)).astype(np.float32)
    t = f / 24.0
    layer = np.zeros((H, W), np.float32)
    plate = cv2.GaussianBlur(cv2.resize(rgb @ LUMA, (W // 8, H // 8)), (0, 0), 6)
    for i in range(n):
        depth = 0.25 + base[i, 2] * 0.75                    # 0.25 near (big, soft) .. 1 far (small)
        speed = p.get("speed", 1.0) / depth
        x = (base[i, 0] + (0.012 * math.sin(t * 0.7 + base[i, 3] * 6.28) + p.get("drift", (0.006, -0.004))[0] * t) * speed) % 1.0
        y = (base[i, 1] + (0.010 * math.sin(t * 0.9 + base[i, 4] * 6.28) + p.get("drift", (0.006, -0.004))[1] * t) * speed) % 1.0
        px, py = x * W, y * H
        rad = p.get("size", 2.2) / depth * (0.6 + 0.8 * base[i, 5])
        tw = 0.55 + 0.45 * math.sin(t * (1.5 + 3 * base[i, 3]) + base[i, 4] * 6.28)   # twinkle as they turn
        lum = float(plate[min(H // 8 - 1, int(py / 8)), min(W // 8 - 1, int(px / 8))])
        a = p.get("gain", 0.5) * tw * (0.15 + min(lum, 3.0)) / (1.0 + rad * rad * 0.12)
        r = int(rad * 3) + 2
        x0, x1, y0, y1 = int(px) - r, int(px) + r + 1, int(py) - r, int(py) + r + 1
        if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
            continue
        gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        layer[y0:y1, x0:x1] += a * np.exp(-((gx - px) ** 2 + (gy - py) ** 2) / (2 * (rad * 0.6) ** 2))
    if "mask_sun" in p:  # concentrate motes in the light shaft region
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        sx, sy, rr = p["mask_sun"]
        layer *= 0.25 + 0.75 * np.exp(-(np.hypot(xx - sx * W, yy - sy * H) / (rr * W)) ** 2)
    return rgb + layer[..., None] * np.array(p.get("color", (1.0, 0.85, 0.6)), np.float32)


def light_leaks(img, f, strength=0.55):
    """Rainbow light leaks washing across the lens (display space, screen blend)."""
    t = f / 24.0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / W, yy / H
    out = np.zeros((H, W, 3), np.float32)
    # a diagonal spectral band that sweeps across, plus two soft warm blooms from the edges
    ang = 0.55
    s = (u * math.cos(ang) + v * math.sin(ang))
    centre = -0.25 + 0.42 * t + 0.05 * math.sin(t * 1.3)
    d = (s - centre) / 0.34
    env = np.exp(-(d ** 2) * 2.2) * (0.55 + 0.45 * np.sin(v * 3.0 + t * 0.8))
    hue = np.clip(d * 0.5 + 0.5, 0, 1)                       # red -> violet across the band
    hsv = np.dstack([hue * 150, np.full_like(hue, 0.78), np.ones_like(hue)]).astype(np.float32)
    band = cv2.cvtColor(hsv.astype(np.float32) * np.array([1, 1, 1], np.float32), cv2.COLOR_HSV2RGB)
    out += band * env[..., None] * 0.75
    for (ex, ey, col, ph, rad) in ((1.08, 0.2, (1.0, 0.5, 0.2), 0.0, 0.5), (-0.1, 0.85, (1.0, 0.25, 0.45), 2.1, 0.45),
                                   (0.5, -0.2, (1.0, 0.8, 0.3), 4.0, 0.4)):
        px = ex + 0.1 * math.sin(t * 0.9 + ph)
        py = ey + 0.08 * math.cos(t * 0.7 + ph)
        a = 0.5 + 0.5 * math.sin(t * 1.1 + ph)
        out += np.exp(-(((u - px) ** 2 + ((v - py) * H / W) ** 2) / (rad ** 2)))[..., None] * np.array(col, np.float32) * a * 0.6
    out = cv2.GaussianBlur(out, (0, 0), 25) * strength
    return 1 - (1 - img) * (1 - np.clip(out, 0, 1))


# ----------------------------------------------------------------------------- titles
_text_cache = {}


def text_layer(text, size, tracking=0.32, y_frac=0.86, sub=None):
    """Crisp tracked Montserrat Light, rendered 3x and Lanczos-downsampled. Returns
    (alpha HxW, shadow HxW)."""
    key = (text, size, tracking, y_frac, sub)
    if key in _text_cache:
        return _text_cache[key]
    S = 3
    im = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(im)

    def draw_line(s, px, yc, track):
        font = ImageFont.truetype(str(FONT), px * S)
        adv = [d.textlength(ch, font=font) for ch in s]
        total = sum(adv) + track * px * S * (len(s) - 1)
        x = (W * S - total) / 2
        asc, desc = font.getmetrics()
        for ch, a in zip(s, adv):
            d.text((x, yc * S - (asc + desc) / 2), ch, font=font, fill=255)
            x += a + track * px * S

    draw_line(text, size, H * y_frac, tracking)
    if sub:
        draw_line(sub[0], sub[1], H * y_frac + size * 1.25, sub[2])
    a = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255.0
    sh = cv2.GaussianBlur(a, (0, 0), 9) * 0.9 + cv2.GaussianBlur(a, (0, 0), 2.2) * 0.5
    _text_cache[key] = (a, np.clip(sh, 0, 1))
    return _text_cache[key]


def fade_curve(f, fin, fout, n=N, ramp=16):
    """Smooth fade in starting at frame fin, out ending at fout."""
    a = smooth(np.float32(f), fin, fin + ramp)
    if fout is not None:
        a *= 1.0 - smooth(np.float32(f), fout - ramp, fout)
    return float(a)


def overlay_text(img, layer, alpha, color=(1, 1, 1), shadow=0.55):
    a, sh = layer
    img = img * (1 - sh[..., None] * shadow * alpha)
    return img * (1 - a[..., None] * alpha) + np.array(color, np.float32) * a[..., None] * alpha


# ----------------------------------------------------------------------------- pipeline
_frame_cache = {}


def load_frame(shot, f):
    key = (shot, f)
    if key not in _frame_cache:
        if len(_frame_cache) > 14:
            for k in sorted(_frame_cache, key=lambda k: abs(k[1] - f))[14:]:
                del _frame_cache[k]
        _frame_cache[key] = read_exr(RENDERS / f"shot{shot}" / f"f{f:04d}.exr")
    return _frame_cache[key]


def temporal(shot, f, p):
    """Temporal bilateral filter for a locked-off camera: pixels that do not change between
    neighbouring frames are averaged over the window (removes low-sample denoiser shimmer);
    pixels that move keep their own frame."""
    rgb, mist = load_frame(shot, f)
    R = p.get("radius", 5)
    if R <= 0:
        return rgb, mist
    tau, sig_t = p.get("tau", 0.22), p.get("sigma_t", 3.5)
    acc = rgb.copy(); wsum = np.ones(rgb.shape[:2], np.float32)
    for g in range(f - R, f + R + 1):
        if g == f or g < 1 or g > N or not (RENDERS / f"shot{shot}" / f"f{g:04d}.exr").exists():
            continue
        other = load_frame(shot, g)[0]
        d = np.abs(other - rgb).max(axis=2) / (0.5 * (other + rgb).max(axis=2) + 0.03)
        d = cv2.GaussianBlur(d, (0, 0), 1.2)
        w = np.exp(-(d / tau) ** 2) * math.exp(-((g - f) / sig_t) ** 2)
        acc += other * w[..., None]; wsum += w
    return acc / wsum[..., None], mist


def process(shot, f, exr=None, out=None):
    cfg = SHOTS[shot]
    p = cfg.get("post", {})
    if exr is None:
        rgb, mist = temporal(shot, f, p.get("temporal", {}))
    else:
        rgb, mist = read_exr(exr)
    rgb = rgb * (2.0 ** p.get("exposure", 0.0))
    rgb = haze(rgb, mist, p.get("haze"))
    if p.get("motes"):
        rgb = motes(rgb, f, p["motes"])
    rgb = bloom(rgb, p.get("bloom", 0.12), p.get("bloom_threshold", 1.0), p.get("streak", 0.0))
    if p.get("ghosts"):
        rgb = lens_ghosts(rgb, p["ghosts"]["sun_xy"], p["ghosts"].get("strength", 0.25))
    img = agx(rgb, p.get("agx_power", 1.2), p.get("agx_sat", 1.12))
    img = grade(img, p.get("grade"))
    img = vignette(img, p.get("vignette", 0.22))
    if p.get("leaks"):
        img = light_leaks(img, f, p["leaks"])
    gframe = (shot - 1) * N + f
    img = grain(img, gframe, p.get("grain", 0.017))
    # closing title card (shot 8): fade the picture down, bring the title up
    tc = cfg.get("title_card")
    if tc:
        k = float(smooth(np.float32(f), tc["start"], tc["start"] + tc.get("ramp", 14)))
        img = img * (1 - k) + np.array(tc.get("bg", (0.012, 0.014, 0.016)), np.float32) * k
        ta = float(smooth(np.float32(f), tc["start"] + 6, tc["start"] + 20))
        img = overlay_text(img, text_layer(tc["text"], tc.get("size", 58), tc.get("tracking", 0.28), 0.5, tc.get("sub")), ta, shadow=0.0)
    cr = cfg.get("credit")
    if cr:
        a = fade_curve(f, cr.get("in", 14), cr.get("out", 82))
        if a > 0:
            lines = cr["lines"]
            img = overlay_text(img, text_layer(lines[0], cr.get("size", 30), cr.get("tracking", 0.42), cr.get("y", 0.845),
                                               (lines[1], cr.get("size2", 17), 0.62) if len(lines) > 1 else None), a)
    img8 = (np.clip(img, 0, 1) * 255.0 + 0.5).astype(np.uint8)
    if out is None:
        FINAL.mkdir(parents=True, exist_ok=True)
        out = FINAL / f"lagos_{(shot - 1) * N + f:04d}.png"
    cv2.imwrite(str(out), cv2.cvtColor(img8, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return str(out)


def _job(a):
    try:
        return process(*a)
    except Exception as e:  # noqa
        return f"FAIL {a}: {e!r}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", type=int, action="append")
    ap.add_argument("--still", nargs=2, metavar=("SHOT:FRAME", "OUT"))
    ap.add_argument("--exr")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    if a.still:
        s, f = map(int, a.still[0].split(":"))
        print(process(s, f, a.exr, a.still[1]))
        return
    jobs = []
    for s in (a.shot or sorted(SHOTS)):
        for f in range(1, N + 1):
            if (RENDERS / f"shot{s}" / f"f{f:04d}.exr").exists():
                jobs.append((s, f))
    with Pool(a.jobs) as pool:   # contiguous chunks so each worker reuses its frame cache
        bad = [r for r in pool.imap_unordered(_job, jobs, chunksize=max(1, len(jobs) // (a.jobs * 2))) if r.startswith("FAIL")]
    print(f"post: {len(jobs) - len(bad)} frames written, {len(bad)} failed")
    for b in bad[:10]:
        print(b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
