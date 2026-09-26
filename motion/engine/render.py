"""Frame loop: motion-blur accumulation, post, overlay, and parallel encoding with ffmpeg."""
import multiprocessing as mp
import os
import subprocess
import sys
import time

import cv2
import numpy as np
import skia

from .core import FPS, W, H
from .post import Post


class Film:
    """Base class. A film draws content at time t; the renderer handles the rest."""
    duration = 10.0

    def bg(self, t):
        return (0.0, 0.0, 0.0)

    def draw(self, c, t):
        pass

    def overlay(self, c, t):
        pass

    def mb(self, t):
        return 8

    def shutter(self, t):
        return 0.5

    def fx(self, t):
        return {}


class Renderer:
    def __init__(self, film, scale=1.0):
        self.film = film
        self.scale = scale
        fw, fh = getattr(film, "size", (W, H))
        self.w = int(round(fw * scale))
        self.h = int(round(fh * scale))
        self.buf = np.zeros((self.h, self.w, 4), np.uint8)
        self.surf = skia.Surface(self.buf)
        self.acc = np.zeros((self.h, self.w, 4), np.uint16)
        self.hbuf = np.zeros((self.h, self.w, 4), np.uint8)
        self.hsurf = skia.Surface(self.hbuf)
        self.post = Post(self.w, self.h)

    def _draw(self, t):
        t = min(max(t, 0.0), self.film.duration)   # blur subframes must not sample outside the film
        with self.surf as c:
            r, g, b = self.film.bg(t)
            c.clear(skia.Color4f(r, g, b, 1.0))
            c.save()
            c.scale(self.scale, self.scale)
            self.film.draw(c, t)
            c.restore()

    def frame(self, f, mb_cap=None):
        t = f / FPS
        n = max(1, int(self.film.mb(t)))
        if mb_cap:
            n = max(1, min(n, mb_cap))
        if n == 1:
            self._draw(t)
            img = self.buf[..., :3].astype(np.float32) * (1.0 / 255)
        else:
            sh = self.film.shutter(t)
            self.acc.fill(0)
            for i in range(n):
                ts = t + ((i + 0.5) / n - 0.5) * sh / FPS
                self._draw(ts)
                np.add(self.acc, self.buf, out=self.acc, casting="unsafe")
            img = self.acc[..., :3].astype(np.float32) * (1.0 / (255.0 * n))
        img = self.post.run(img, f, self.film.fx(t))
        with self.hsurf as c:
            c.clear(skia.Color4f(0, 0, 0, 0))
            c.save()
            c.scale(self.scale, self.scale)
            self.film.overlay(c, t)
            c.restore()
        hud = self.hbuf.astype(np.float32) * (1.0 / 255)
        a = hud[..., 3:4]
        img = hud[..., :3] + img * (1.0 - a)
        rng = np.random.default_rng(f)
        dither = rng.random(img.shape[:2], dtype=np.float32)[..., None] - 0.5
        return np.clip(img * 255.0 + 0.5 + dither, 0, 255).astype(np.uint8)


def still(film, t, path, scale=0.5, mb_cap=None):
    r = Renderer(film, scale)
    img = r.frame(int(round(t * FPS)), mb_cap)
    cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    return path


def _worker(film, scale, frames, seg, mb_cap, fps_out, counter):
    r = Renderer(film, scale)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{r.w}x{r.h}", "-r", str(fps_out), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "6", "-pix_fmt", "yuv444p", seg]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(r.frame(f, mb_cap).tobytes())
        with counter.get_lock():
            counter.value += 1
    p.stdin.close()
    p.wait()


def render(film, out, scale=1.0, workers=4, mb_cap=None, audio=None, f0=0, f1=None,
           step=1, crf=18, tmpdir=None, label="", maxrate=None, master_dir=None):
    """Render frames [f0, f1) every `step` frames, split across workers, then encode once."""
    if f1 is None:
        f1 = int(round(film.duration * FPS))
    frames = list(range(f0, f1, step))
    fps_out = FPS / step
    tmpdir = tmpdir or os.path.join(os.path.dirname(os.path.abspath(out)), ".segs")
    os.makedirs(tmpdir, exist_ok=True)
    k = max(1, min(workers, len(frames)))
    size = (len(frames) + k - 1) // k
    chunks = [frames[i * size:(i + 1) * size] for i in range(k)]
    chunks = [ch for ch in chunks if ch]
    ctx = mp.get_context("fork")
    counter = ctx.Value("i", 0)
    segs, procs = [], []
    t0 = time.time()
    for i, ch in enumerate(chunks):
        seg = os.path.join(tmpdir, f"seg{i:02d}.mkv")
        segs.append(seg)
        pr = ctx.Process(target=_worker, args=(film, scale, ch, seg, mb_cap, fps_out, counter))
        pr.start()
        procs.append(pr)
    total = len(frames)
    last = -1
    while any(p.is_alive() for p in procs):
        time.sleep(2.0)
        done = counter.value
        if done != last:
            el = time.time() - t0
            eta = el / max(done, 1) * (total - done)
            sys.stdout.write(f"\r{label} {done}/{total} frames  {el:5.0f}s elapsed  eta {eta:5.0f}s ")
            sys.stdout.flush()
            last = done
    for p in procs:
        p.join()
        if p.exitcode != 0:
            raise RuntimeError(f"render worker failed with exit code {p.exitcode}")
    print(f"\r{label} {total}/{total} frames in {time.time() - t0:.0f}s" + " " * 30)
    lst = os.path.join(tmpdir, "list.txt")
    with open(lst, "w") as fh:
        for s in segs:
            fh.write(f"file '{s}'\n")
    master = os.path.splitext(out)[0] + ".master.mkv" if master_dir is None else \
        os.path.join(master_dir, os.path.basename(os.path.splitext(out)[0]) + ".master.mkv")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", master],
                   check=True)
    for s in segs:
        os.remove(s)
    encode(master, out, audio, fps_out, crf, maxrate, f0 / FPS)
    return out


def encode(master, out, audio=None, fps_out=FPS, crf=18, maxrate=None, audio_offset=0.0):
    """Delivery encode from the near-lossless master: H.264 High, yuv420p, AAC 256k."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", master]
    if audio:
        cmd += ["-ss", f"{audio_offset:.4f}", "-i", audio]
    cmd += ["-map", "0:v:0"]
    if audio:
        cmd += ["-map", "1:a:0", "-c:a", "aac", "-b:a", "256k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-x264-params", "aq-mode=3", "-movflags", "+faststart", "-r", str(fps_out)]
    if maxrate:
        cmd += ["-maxrate", f"{maxrate}M", "-bufsize", f"{2 * maxrate}M"]
    cmd += [out]
    subprocess.run(cmd, check=True)
    return out


def contact_sheet(video, out_png, every=0.5, cols=6, width=400, start=0.0):
    fps = 1.0 / every
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", video, "-vf",
           f"fps={fps},scale={width}:-1,tile={cols}x{cols}", "-frames:v", "1", out_png]
    subprocess.run(cmd, check=True)
    return out_png
