"""1-bit ordered dithering, the look of the film's mascot and stills: anything drawn in greys on a small offscreen
canvas comes back as black and white dots on an 8 x 8 Bayer screen, blown up with hard pixel edges."""
import os
import subprocess

import cv2
import numpy as np
import skia


_B2 = np.array([[0, 2], [3, 1]])
_B4 = np.block([[4 * _B2, 4 * _B2 + 2], [4 * _B2 + 3, 4 * _B2 + 1]])
BAYER = (np.block([[4 * _B4, 4 * _B4 + 2], [4 * _B4 + 3, 4 * _B4 + 1]]) + 0.5) / 64.0


def screen(h, w):
    return np.tile(BAYER, (h // 8 + 1, w // 8 + 1))[:h, :w]


def dither_gray(gray, alpha=None, ink=(10, 10, 10), paper=(255, 255, 255), gamma=1.0):
    """gray, alpha: float arrays in 0..1 -> an RGBA uint8 image of ink and paper dots."""
    h, w = gray.shape
    g = np.clip(gray, 0, 1) ** gamma
    on = g < screen(h, w)                      # darker than the screen: ink
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.where(on[..., None], np.array(ink, np.uint8), np.array(paper, np.uint8))
    out[..., 3] = 255 if alpha is None else np.where(alpha > 0.5, 255, 0).astype(np.uint8)
    return out


def to_image(rgba):
    return skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.ColorType.kRGBA_8888_ColorType)


NEAREST = skia.SamplingOptions(skia.FilterMode.kNearest, skia.MipmapMode.kNone)


def draw_pixels(c, img, x, y, cell):
    """Draw a dithered image with each of its pixels a cell x cell square, hard edged."""
    c.drawImageRect(img, skia.Rect.MakeXYWH(x, y, img.width() * cell, img.height() * cell), NEAREST, None)


class Layer:
    """A small offscreen canvas: draw greys into it, get dots out."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.buf = np.zeros((h, w, 4), np.uint8)
        self.surf = skia.Surface(self.buf)

    def render(self, draw, gamma=1.0):
        with self.surf as c:
            c.clear(skia.Color4f(0, 0, 0, 0))
            c.save()                                   # the surface keeps its canvas: leave no transform behind
            draw(c)
            c.restore()
        a = self.buf[..., 3].astype(np.float32) / 255.0
        rgb = self.buf[..., :3].astype(np.float32) / 255.0
        lum = rgb.mean(2) / np.maximum(a, 1e-3)            # un-premultiply
        return to_image(dither_gray(lum, a, gamma=gamma))


OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
CLIPS = []


class Clip:
    """A stretch of one of our own films (out/<film>.mp4), cropped to rect (1920 x 1080 pixels, cover-fitted),
    shrunk to one pixel per dot and printed as 1-bit dots: a still when dur is 0, otherwise a clip that plays at
    fps. Dark films can be printed inverted, ink on paper. Frames are decoded once (by ffmpeg, which seeks
    exactly), before the render forks."""

    def __init__(self, film, t0, w, h, cell=3, dur=0.0, fps=30, rect=None, invert=False, contrast=1.2, lift=0.03):
        self.film, self.t0, self.w, self.h, self.cell = film, t0, w, h, cell
        self.dur, self.fps, self.rect, self.invert = dur, fps, rect, invert
        self.contrast, self.lift = contrast, lift
        self.frames = None
        CLIPS.append(self)

    def _print(self, frame):
        """frame: a 960 x 540 BGR frame of the film (rect is in its 1920 x 1080 pixels)."""
        gw, gh = max(1, self.w // self.cell), max(1, self.h // self.cell)
        if self.rect is not None:
            x, y, w, h = (int(round(v / 2)) for v in self.rect)
            frame = frame[y:y + h, x:x + w]
        fh, fw = frame.shape[:2]
        s = max(gw / fw, gh / fh)
        rs = cv2.resize(frame, (max(gw, int(fw * s + 0.5)), max(gh, int(fh * s + 0.5))), interpolation=cv2.INTER_AREA)
        oy, ox = (rs.shape[0] - gh) // 2, (rs.shape[1] - gw) // 2
        g = cv2.cvtColor(rs[oy:oy + gh, ox:ox + gw], cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        if self.invert:
            g = 1.0 - g
        g = np.clip((g - 0.5) * self.contrast + 0.5 + self.lift, 0, 1)
        return to_image(dither_gray(g))

    def _blank(self):
        gw, gh = max(1, self.w // self.cell), max(1, self.h // self.cell)
        yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
        d = np.hypot((xx - gw / 2) / gw, (yy - gh / 2) / gh)
        return to_image(dither_gray(np.clip(0.55 + d, 0, 1)))

    def load(self):
        if self.frames is not None:
            return
        frames = []
        path = os.path.join(OUT, f"{self.film}.mp4")
        if os.path.exists(path):
            n = int(round(self.dur * self.fps)) + 1
            cmd = ["ffmpeg", "-v", "error", "-ss", f"{self.t0:.3f}", "-i", path, "-frames:v", str(n),
                   "-vf", f"fps={self.fps},scale=960:540", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
            raw = subprocess.run(cmd, capture_output=True).stdout
            size = 960 * 540 * 3
            for k in range(len(raw) // size):
                frames.append(self._print(np.frombuffer(raw[k * size:(k + 1) * size], np.uint8).reshape(540, 960, 3)))
        self.frames = frames or [self._blank()]

    def at(self, u):
        self.load()
        k = int(max(0.0, min(u, self.dur)) * self.fps + 1e-6)
        return self.frames[min(k, len(self.frames) - 1)]

    def draw(self, c, x, y, u=0.0):
        draw_pixels(c, self.at(u), x, y, self.cell)


def preload():
    for clip in CLIPS:
        clip.load()


def blob(c, cx, cy, r, edge, col, cell=4, w=1920, h=1080, inside=True):
    """A disc of col with a dithered edge: solid within r - edge, dots thinning out to r. With inside False, the
    same edge but everything outside the disc is col (a hole that closes)."""
    gw, gh = w // cell, h // cell
    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
    d = np.hypot((xx + 0.5) * cell - cx, (yy + 0.5) * cell - cy)
    v = np.clip((r - d) / max(edge, 1.0), 0, 1)               # 1 inside, 0 outside
    if not inside:
        v = 1.0 - v
    on = v > screen(gh, gw)
    rgb = np.array([int(col[i:i + 2], 16) for i in (1, 3, 5)], np.uint8)
    out = np.zeros((gh, gw, 4), np.uint8)
    out[on, :3] = rgb
    out[on, 3] = 255
    draw_pixels(c, to_image(out), 0, 0, cell)
