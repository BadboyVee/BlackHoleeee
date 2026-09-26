"""INTERFACE: a square UI micro-interaction reel, the interface behind the other two films."""
import glob
import math
import os
from contextlib import contextmanager
from functools import lru_cache

import cv2
import numpy as np
import skia

from .score import *   # noqa: F401,F403 - the timing sheet is the vocabulary of this file
from engine import gfx as G   # after the star import: the sheet's musical grid is also called G
from engine import logos as LG
from engine.core import (clamp, lerp, snap, whip, out_cubic, in_out_cubic, out_back, spring, noise1)
from engine.render import Film

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")

BG0 = "#e8e7e3"
BG1 = "#f6f5f2"
CARD = "#ffffff"
INK = "#0e0e10"
SUB = "#7a7872"
LINE = "#e4e2dd"
SOFT = "#f1f0ec"
DARK_SUB = "#9a988f"
CLAY = "#d97757"

FRAMES_DIR = os.path.join(OUT, "player_frames")


# ---------------------------------------------------------------- primitives

def rr(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def panel(c, x, y, w, h, r=32, color=CARD, a=1.0, lift=1.0):
    if lift > 0:
        c.drawRRect(rr(x, y + 18 * lift, w, h, r), G.P(INK, 0.10 * a * lift, blur=26 * lift))
        c.drawRRect(rr(x, y + 2, w, h, r), G.P(INK, 0.06 * a, blur=3))
    c.drawRRect(rr(x, y, w, h, r), G.P(color, a))


def reveal(t, win, din=0.36, dout=0.3):
    t_in, t_out = win
    u = clamp((t - t_in) / din)
    v = clamp((t - t_out) / dout)
    e = snap(u)
    alpha = u * (1 - v)
    scale = (0.94 + 0.06 * e) * (1 - 0.04 * v)
    blur = 16 * (1 - e) + 16 * v
    return alpha, scale, blur


@contextmanager
def presence(c, t, win, cx=CX, cy=CY, din=0.36, dout=0.3):
    a, s, b = reveal(t, win, din, dout)
    if a <= 0.003:
        yield False
        return
    with G.layer(c, alpha=a, blur=b if b > 0.4 else 0.0):
        with G.xf(c, cx, cy, s=s):
            c.translate(-cx, -cy)
            yield True


def F(fam, size, **ax):
    return G.Font(fam, size, **ax)


def T(c, s, x, y, font, col, a=1.0, align=0.0, tracking=0.0, tnum=False):
    return G.text(c, s, x, y, font, G.P(col, a), align=align, tracking=tracking,
                  features={"tnum": True} if tnum else None)


def icon_play(c, x, y, s, col):
    c.drawPath(G.poly([(x - s * 0.35, y - s * 0.5), (x + s * 0.55, y), (x - s * 0.35, y + s * 0.5)]), G.P(col))


def icon_pause(c, x, y, s, col):
    for dx in (-0.28, 0.28):
        c.drawRRect(rr(x + dx * s - s * 0.13, y - s * 0.46, s * 0.26, s * 0.92, s * 0.06), G.P(col))


def icon_skip(c, x, y, s, col, direction=1):
    d = direction
    c.drawPath(G.poly([(x - d * s * 0.3, y - s * 0.4), (x + d * s * 0.25, y), (x - d * s * 0.3, y + s * 0.4)]), G.P(col))
    c.drawRect(skia.Rect.MakeXYWH(x + d * s * 0.28 - s * 0.06, y - s * 0.4, s * 0.12, s * 0.8), G.P(col))


def icon_check(c, x, y, s, col, p=1.0, width=None):
    path = G.poly([(x - s * 0.42, y + s * 0.02), (x - s * 0.12, y + s * 0.32), (x + s * 0.45, y - s * 0.3)], closed=False)
    c.drawPath(path, G.P(col, 1, stroke=width or s * 0.16, cap="round", join="round", effect=G.trim(0, p)))


def icon_search(c, x, y, s, col):
    G.circle(c, x - s * 0.1, y - s * 0.1, s * 0.34, G.P(col, 1, stroke=s * 0.11))
    c.drawLine(x + s * 0.15, y + s * 0.15, x + s * 0.45, y + s * 0.45, G.P(col, 1, stroke=s * 0.11, cap="round"))


def backdrop(c):
    c.drawRect(skia.Rect.MakeWH(*SIZE), G.P(BG0))
    c.drawCircle(CX, 640, 1150, G.P(BG1, 1, shader=G.radial_grad(CX, 640, 1150, [BG1, BG0])))


# ---------------------------------------------------------------- cursor

def cursor_pos(t):
    keys = CURSOR
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
            e = in_out_cubic(u)
            d = math.hypot(x1 - x0, y1 - y0)
            arc = math.sin(math.pi * e) * min(60.0, d * 0.12)
            nx, ny = (-(y1 - y0) / d, (x1 - x0) / d) if d > 1e-6 else (0.0, 0.0)
            return x0 + (x1 - x0) * e + nx * arc, y0 + (y1 - y0) * e + ny * arc
    return keys[-1][1], keys[-1][2]


_ARROW = [(0, 0), (0, 31), (7.8, 24), (13, 35.5), (17.6, 33.4), (12.6, 22.4), (23, 22.4)]


def cursor(c, t):
    x, y = cursor_pos(t)
    press = 0.0
    for tc in CLICKS:
        if 0 <= t - tc < 0.4:
            press = max(press, math.exp(-(t - tc) / 0.07))
    held = (T_GRAB <= t <= T_DROP) or (T_SLIDE[0] <= t <= T_SLIDE[1])
    if held:
        press = max(press, 0.6)
    for tc in CLICKS:
        u = (t - tc) / 0.45
        if 0 <= u < 1:
            G.circle(c, x, y, 8 + 46 * out_cubic(u), G.P(INK, 0.22 * (1 - u), stroke=2.0))
    s = 1.35 * (1 - 0.14 * press)
    path = G.poly([(px * s, py * s) for px, py in _ARROW])
    with G.xf(c, x, y):
        with G.xf(c, 1.5, 4):
            c.drawPath(path, G.P(INK, 0.28, blur=3))
        c.drawPath(path, G.P("#ffffff", 1, stroke=4.2, join="round"))
        c.drawPath(path, G.P(INK))


# ---------------------------------------------------------------- 1 model picker

SEG_W = 290
PICK_X0 = CX - 1.5 * SEG_W
MODELS = [("Astra 6", 0), ("Gemini 3m", 1), ("Fable 5.1", 2)]


def picker(c, t):
    with presence(c, t, PICKER) as on:
        if not on:
            return
        y0, h = CY - 52, 104
        panel(c, PICK_X0 - 10, y0 - 10, 3 * SEG_W + 20, h + 20, r=62)
        centers = [PICK_X0 + SEG_W * (k + 0.5) for k in range(3)]
        u = spring(t - T_PICK, 2.3, 0.52) if t >= T_PICK else 0.0
        pos = lerp(centers[0], centers[2], u)
        stretch = 1 + 0.35 * math.sin(math.pi * clamp(u, 0, 1))
        hover = clamp((t - (T_PICK - 0.25)) / 0.15) * (1 - clamp((t - T_PICK) / 0.1))
        if hover > 0:
            c.drawRRect(rr(centers[2] - 132, y0 + 8, 264, h - 16, 44), G.P(SOFT, hover))
        sw = 264 * stretch
        c.save()
        c.clipRRect(rr(PICK_X0, y0, 3 * SEG_W, h, 52), skia.ClipOp.kIntersect, True)
        c.drawRRect(rr(pos - sw / 2, y0 + 8, sw, h - 16, 44), G.P(INK))
        c.restore()
        f = F("inter", 31, wght=600, opsz=32)
        for k, (label, idx) in enumerate(MODELS):
            cov = clamp(1 - abs(pos - centers[k]) / 150)
            col = G.mixc(INK, "#ffffff", cov)
            lw = f.width(label)
            x = centers[k] - (lw + 50) / 2
            if idx == 0:
                LG.mark(c, "openai", x + 17, CY, 34, G.P(col))
            elif idx == 1:
                LG.gemini(c, x + 17, CY, 34)
            else:
                LG.claude(c, x + 17, CY, 38, CLAY, 1.0, 1.0, rot=180 * u)
            G.text(c, label, x + 50, CY + 11, f, G.P(col))
        fm = F("mono", 16, wght=650)
        T(c, "MODEL", PICK_X0, y0 - 42, fm, SUB, tracking=0.24)
        T(c, "3 AVAILABLE", PICK_X0 + 3 * SEG_W, y0 - 42, fm, SUB, align=1.0, tracking=0.24)


# ---------------------------------------------------------------- 2 composer

GEN_BOX = (994, 834, 236, 76)
LINES = ["make a dynamic 15-second motion", "graphics video about the frontier"]


def gen_button(c, t, x, y, w, h, label_a=1.0, press=0.0):
    s = 1 - 0.06 * press
    with G.xf(c, x + w / 2, y + h / 2, s=s):
        c.drawRRect(rr(-w / 2, -h / 2, w, h, min(h, w) / 2), G.P(INK))
        if label_a > 0:
            f = F("inter", 30, wght=600, opsz=32)
            T(c, "Generate", 0, 11, f, "#ffffff", a=label_a, align=0.5)


def composer(c, t):
    with presence(c, t, COMPOSER) as on:
        if not on:
            return
        x, y, w, h = 170, 490, 1100, 460
        panel(c, x, y, w, h, r=40)
        fm = F("mono", 16, wght=650)
        T(c, "NEW FILM", x + 52, y + 64, fm, SUB, tracking=0.24)
        T(c, "1 OF 3", x + w - 52, y + 64, fm, SUB, align=1.0, tracking=0.24)
        f = F("inter", 46, wght=520, opsz=32)
        total = len(LINES[0]) + 1 + len(LINES[1])
        n = int(total * clamp((t - T_TYPE[0]) / (T_TYPE[1] - T_TYPE[0])))
        if n == 0:
            T(c, "Describe the film…", x + 52, y + 150, f, "#b3b0a9")
        l1 = LINES[0][:n]
        l2 = LINES[1][:max(0, n - len(LINES[0]) - 1)]
        T(c, l1, x + 52, y + 150, f, INK)
        T(c, l2, x + 52, y + 214, f, INK)
        cur_line = 1 if n > len(LINES[0]) else 0
        cx_ = x + 52 + f.width([l1, l2][cur_line]) + 4
        cy_ = y + 150 + 64 * cur_line
        if int(t * 2.4) % 2 == 0 or t < T_TYPE[1]:
            c.drawRect(skia.Rect.MakeXYWH(cx_, cy_ - 38, 3.5, 48), G.P(INK))
        fc = F("inter", 24, wght=560, opsz=24)
        chips = ["1920 × 1080", "60 fps", "Fable 5.1"]
        cx = x + 52
        for k, (label, tc) in enumerate(zip(chips, T_CHIPS)):
            u = spring(t - tc, 2.6, 0.5) if t >= tc else 0.0
            if u <= 0:
                continue
            lw = fc.width(label) + (40 if k == 2 else 0)
            cw = lw + 44
            with G.xf(c, cx + cw / 2, 872, s=max(0.0, u)):
                c.drawRRect(rr(-cw / 2, -27, cw, 54, 27), G.P(SOFT))
                tx = -cw / 2 + 22
                if k == 2:
                    LG.claude(c, tx + 12, 0, 26, CLAY)
                    tx += 40
                T(c, label, tx, 9, fc, INK)
            cx += cw + 14
        if t < T_GEN + 0.05:
            press = math.exp(-(t - T_GEN) / 0.07) if t >= T_GEN else 0.0
            hover = clamp((t - 3.2) / 0.15)
            gen_button(c, t, *GEN_BOX, press=press + 0.0 * hover)


# ---------------------------------------------------------------- 3 generate -> spin -> render

def morph(c, t):
    t0 = T_GEN + 0.05
    if t < t0 or t >= MORPH[1] + 0.3:
        return
    a_out = 1 - clamp((t - (MORPH[1] - 0.05)) / 0.3)
    bx, by, bw, bh = GEN_BOX
    u1 = whip(clamp((t - t0) / (T_CIRCLE - t0)))
    cx = lerp(bx + bw / 2, CX, u1)
    cy = lerp(by + bh / 2, CY, u1)
    w, h = bw, bh
    u2 = snap(clamp((t - T_CIRCLE) / 0.22))
    w, h = lerp(w, 108, u2), lerp(h, 108, u2)
    u3 = snap(clamp((t - T_EXPAND) / 0.3))
    w, h = lerp(w, 980, u3), lerp(h, 112, u3)
    with G.layer(c, alpha=a_out, blur=16 * (1 - a_out)):
        panel(c, cx - w / 2, cy - h / 2, w, h, r=h / 2, color=INK, lift=0.8)
        if u2 < 1:
            f = F("inter", 30, wght=600, opsz=32)
            T(c, "Generate", cx, cy + 11, f, "#ffffff", a=1 - u2, align=0.5)
        # the Claude spark spins while it thinks
        spin_in = snap(clamp((t - T_SPIN[0]) / 0.25))
        ix = lerp(cx, cx - w / 2 + 58, u3)
        if spin_in > 0 and t < T_DONE:
            prog = 0.35 + 0.65 * (0.5 + 0.5 * math.sin((t - T_SPIN[0]) * 9))
            LG.claude(c, ix, cy, lerp(64, 50, u3) * spin_in, "#ffffff", 1.0, prog if t < T_EXPAND else 1.0,
                      rot=(t - T_SPIN[0]) * 420)
        if u3 > 0:
            p = in_out_cubic(clamp((t - T_COUNT[0]) / (T_COUNT[1] - T_COUNT[0])))
            done = clamp((t - T_DONE) / 0.15)
            fillw = (w - 12) * lerp(p, 1.0, done)
            c.drawRRect(rr(cx - w / 2 + 6, cy - h / 2 + 6, max(h - 12, fillw), h - 12, (h - 12) / 2),
                        G.P("#ffffff", 0.12 + 0.06 * done))
            f = F("inter", 32, wght=600, opsz=32)
            fm = F("mono", 30, wght=560)
            roll = snap(done)
            with G.clip_rect(c, cx - w / 2 + 90, cy - h / 2 + 8, w - 120, h - 16):
                if roll < 1:
                    T(c, "Rendering", cx - w / 2 + 108, cy + 11 - 60 * roll, f, "#ffffff", a=u3)
                    T(c, f"{int(1584 * p):04d} / 1584", cx + w / 2 - 40, cy + 11 - 60 * roll, fm, "#ffffff", a=u3,
                      align=1.0, tnum=True)
                if roll > 0:
                    T(c, "Rendered  ·  26.4 s  ·  1,584 frames", cx - w / 2 + 108, cy + 11 + 60 * (1 - roll), f, "#ffffff")
            if done > 0:
                c.drawCircle(ix, cy, 26 * done, G.P("#ffffff"))
                icon_check(c, ix, cy + 1, 28, INK, p=done)


# ---------------------------------------------------------------- 4 player

@lru_cache(maxsize=512)
def film_frame(idx):
    p = os.path.join(FRAMES_DIR, f"f{idx:04d}.jpg")
    if not os.path.exists(p):
        return None
    return G.image_from_rgba(cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGBA))


_LV = None


def film_levels():
    global _LV
    if _LV is None:
        p = os.path.join(OUT, "frontier_levels.npz")
        rms = np.load(p)["rms"] if os.path.exists(p) else np.abs(np.sin(np.linspace(0, 30, 1584)))
        _LV = rms
    return _LV


def playhead(t):
    """Seconds into THE FRONTIER that the player shows."""
    if t < T_PLAY:
        return 5.4
    if t < T_GRAB:
        return 5.4 + (t - T_PLAY)
    p0 = 5.4 + (T_GRAB - T_PLAY)
    if t < T_DROP:
        return lerp(p0, 17.9, in_out_cubic((t - T_GRAB) / (T_DROP - T_GRAB)))
    return 17.9 + (t - T_DROP)


def player(c, t):
    with presence(c, t, PLAYER) as on:
        if not on:
            return
        x, y, w, h = 200, 480, 1040, 480
        panel(c, x, y, w, h, r=44, color=INK)
        tx, ty, tw, th = x + 36, y + 36, 452, 254
        ph = playhead(t)
        img = film_frame(int(ph * 10) + 1)
        c.save()
        c.clipRRect(rr(tx, ty, tw, th, 20), skia.ClipOp.kIntersect, True)
        if img is not None:
            G.draw_image(c, img, tx, ty, tw, th)
        else:
            c.drawRect(skia.Rect.MakeXYWH(tx, ty, tw, th), G.P("#1e1e22"))
        c.restore()
        c.drawRRect(rr(tx, ty, tw, th, 20), G.P("#ffffff", 0.08, stroke=1.2))
        rx = x + 530
        T(c, "the-frontier.mp4", rx, y + 96, F("inter", 38, wght=620, opsz=32), "#ffffff")
        T(c, "26.4 s  ·  1920 × 1080  ·  60 fps", rx, y + 138, F("inter", 23, wght=480, opsz=24), DARK_SUB)
        lv = film_levels()
        n = 64
        bx0, bx1, by = rx, x + w - 44, y + 222
        prog = ph / 26.4
        for k in range(n):
            v = float(lv[int(k / n * (len(lv) - 1))])
            bh = 6 + 44 * v
            bxk = bx0 + (bx1 - bx0) * (k + 0.5) / n
            played = (k + 0.5) / n <= prog
            c.drawRRect(rr(bxk - 2.4, by - bh / 2, 4.8, bh, 2.4), G.P("#ffffff" if played else "#3a3a40"))
        hx = bx0 + (bx1 - bx0) * prog
        held = T_GRAB <= t <= T_DROP
        G.circle(c, hx, by, 11 + 4 * held, G.P("#ffffff"))
        if held:
            G.circle(c, hx, by, 24, G.P("#ffffff", 0.2))
        fm = F("mono", 21, wght=500)
        cur = int(ph)
        T(c, f"0:{cur:02d}", bx0, by + 64, fm, DARK_SUB)
        T(c, f"-0:{max(0, 26 - cur):02d}", bx1, by + 64, fm, DARK_SUB, align=1.0)
        ccx, ccy = (bx0 + bx1) / 2, y + 382
        icon_skip(c, ccx - 96, ccy, 30, "#ffffff", -1)
        icon_skip(c, ccx + 96, ccy, 30, "#ffffff", 1)
        press = math.exp(-(t - T_PLAY) / 0.07) if t >= T_PLAY else 0.0
        with G.xf(c, ccx, ccy, s=1 - 0.08 * press):
            G.circle(c, 0, 0, 40, G.P("#ffffff"))
            if t < T_PLAY:
                icon_play(c, 3, 0, 34, INK)
            else:
                icon_pause(c, 0, 0, 30, INK)


# ---------------------------------------------------------------- 5 settings

def toggle(c, x, y, on_t, t, initially=False):
    if on_t is None:
        s = 1.0 if initially else 0.0
    else:
        s = spring(t - on_t, 2.8, 0.55) if t >= on_t else 0.0
        if initially:
            s = 1 - s
    w, h = 92, 52
    bg = G.mixc(LINE, INK, clamp(s))
    c.drawRRect(rr(x - w / 2, y - h / 2, w, h, h / 2), G.P(bg))
    kx = lerp(x - w / 2 + h / 2, x + w / 2 - h / 2, s)
    c.drawCircle(kx, y + 1.5, 21, G.P(INK, 0.18, blur=2.5))
    G.circle(c, kx, y, 21, G.P("#ffffff"))


def slider_value(t):
    if t < T_SLIDE[0]:
        return 0.35
    return lerp(0.35, 1.0, in_out_cubic(clamp((t - T_SLIDE[0]) / (T_SLIDE[1] - T_SLIDE[0]))))


def settings(c, t):
    with presence(c, t, SETTINGS) as on:
        if not on:
            return
        x, y, w, h = 270, 400, 900, 640
        panel(c, x, y, w, h, r=40)
        T(c, "Render settings", x + 50, y + 78, F("inter", 36, wght=620, opsz=32), INK)
        T(c, "THE FRONTIER", x + w - 50, y + 74, F("mono", 16, wght=650), SUB, align=1.0, tracking=0.24)
        f = F("inter", 31, wght=500, opsz=32)
        fs = F("inter", 22, wght=450, opsz=24)
        rows = [("Motion blur", "12 sub-frames per frame", None, True, 565), ("Film grain", "8 textures, per frame", T_TOG[0], False, 655),
                ("Click track", "a sound for every event", T_TOG[1], False, 745)]
        for label, hint, tt, init, yy in rows:
            T(c, label, x + 50, yy + 2, f, INK)
            T(c, hint, x + 50, yy + 34, fs, SUB)
            toggle(c, 1082, yy, tt, t, init)
            c.drawLine(x + 50, yy + 58, x + w - 50, yy + 58, G.P(LINE, 1, stroke=1.4))
        v = slider_value(t)
        names = ["low", "medium", "high", "max"]
        name = names[min(3, int(v * 3.999))]
        T(c, "Effort", x + 50, 860, f, INK)
        T(c, name, x + w - 50, 860, F("inter", 31, wght=620, opsz=32), INK, align=1.0)
        t0x, t1x, ty = x + 60, x + w - 60, 904
        c.drawRRect(rr(t0x, ty - 5, t1x - t0x, 10, 5), G.P(LINE))
        kx = lerp(t0x, t1x, v)
        c.drawRRect(rr(t0x, ty - 5, kx - t0x, 10, 5), G.P(INK))
        held = T_SLIDE[0] <= t <= T_SLIDE[1]
        c.drawCircle(kx, ty + 2, 19, G.P(INK, 0.2, blur=3))
        G.circle(c, kx, ty, 19 + 3 * held, G.P("#ffffff"))
        G.circle(c, kx, ty, 19 + 3 * held, G.P(LINE, 1, stroke=1.5))
        fm = F("mono", 15, wght=600)
        for k, nm in enumerate(names):
            T(c, nm.upper(), lerp(t0x, t1x, k / 3), ty + 52, fm, SUB, align=[0.0, 0.5, 0.5, 1.0][k], tracking=0.2)


# ---------------------------------------------------------------- 6 stats

FILMS = [dict(name="The Frontier", frames=1584, secs="26.4 s", bpm="150 BPM", lufs="−10 LUFS", key="frontier"),
         dict(name="Tribute", frames=1968, secs="32.8 s", bpm="120 BPM", lufs="−11 LUFS", key="dario")]


@lru_cache(maxsize=2)
def envelope(key, n=90):
    p = os.path.join(OUT, f"{key}_levels.npz")
    if os.path.exists(p):
        r = np.load(p)["rms"]
    else:
        r = np.abs(np.sin(np.linspace(0, 9, 600))) * (1 if key == "frontier" else 0.7)
    idx = np.linspace(0, len(r) - 1, n).astype(int)
    v = np.convolve(r, np.ones(40) / 40, mode="same")[idx]
    return v / (v.max() + 1e-9)


def roll_number(c, a_str, b_str, u, x, y, font, col, stagger=0.06):
    """Digits roll from a_str to b_str; each changed digit slides up out of a clip."""
    run = font.shape(b_str, features={"tnum": True})
    runa = font.shape(a_str, features={"tnum": True})
    hgt = font.cap * 1.5
    for i, (gid, gx, adv) in enumerate(zip(run.gids, run.xs, run.adv)):
        ca = a_str[i] if i < len(a_str) else " "
        cb = b_str[i]
        e = snap(clamp((u - i * stagger) / 0.5))
        with G.clip_rect(c, x + gx - 4, y - font.cap - 30, adv + 8, font.cap + 60):
            if ca == cb or e >= 1:
                G.glyph(c, font, gid, x + gx, y, G.P(col))
            else:
                if e < 1:
                    G.glyph(c, font, runa.gids[i], x + gx, y - hgt * e, G.P(col))
                G.glyph(c, font, gid, x + gx, y + hgt * (1 - e), G.P(col))
    return run.width


def stats(c, t):
    with presence(c, t, STATS) as on:
        if not on:
            return
        x, y, w, h = 220, 360, 1000, 720
        panel(c, x, y, w, h, r=44)
        sx, sy, sw, sh = x + 50, y + 50, 470, 68
        c.drawRRect(rr(sx, sy, sw, sh, sh / 2), G.P(SOFT))
        u = spring(t - T_SWITCH, 2.4, 0.55) if t >= T_SWITCH else 0.0
        selx = lerp(sx + 6, sx + sw / 2, u)
        c.drawRRect(rr(selx, sy + 8, sw / 2 - 6, sh - 16, (sh - 16) / 2), G.P(INK, 0.08, blur=6))
        c.drawRRect(rr(selx, sy + 6, sw / 2 - 6, sh - 12, (sh - 12) / 2), G.P("#ffffff"))
        fseg = F("inter", 25, wght=600, opsz=24)
        for k, film in enumerate(FILMS):
            cov = clamp(1 - abs(u - k))
            T(c, film["name"], sx + sw / 4 + k * sw / 2, sy + sh / 2 + 9, fseg, G.mixc(SUB, INK, cov), align=0.5)
        rollu = clamp((t - T_SWITCH - 0.05) / 0.6)
        fb = F("inter", 150, wght=640, opsz=32)
        a_s, b_s = f"{FILMS[0]['frames']:,}", f"{FILMS[1]['frames']:,}"
        wnum = roll_number(c, a_s, b_s if rollu > 0 else a_s, rollu, x + 46, y + 300, fb, INK)
        T(c, "frames", x + 46 + wnum + 18, y + 300, F("inter", 34, wght=500, opsz=32), SUB)
        fv = F("inter", 32, wght=620, opsz=32)
        fl = F("mono", 15, wght=650)
        for k, (key, lab) in enumerate((("secs", "LENGTH"), ("bpm", "TEMPO"), ("lufs", "LOUDNESS"))):
            cx0 = x + 50 + k * 250
            v0, v1 = FILMS[0][key], FILMS[1][key]
            e = snap(clamp((t - T_SWITCH - 0.1 - 0.06 * k) / 0.35))
            with G.clip_rect(c, cx0 - 4, y + 330, 240, 60):
                T(c, v0, cx0, y + 372 - 50 * e, fv, INK)
                T(c, v1, cx0, y + 372 + 50 * (1 - e), fv, INK)
            T(c, lab, cx0, y + 402, fl, SUB, tracking=0.22)
        cx0, cx1, cy0, cy1 = x + 50, x + w - 50, y + 450, y + h - 50
        env = envelope("frontier") * (1 - snap(rollu)) + envelope("dario") * snap(rollu)
        xs = np.linspace(cx0, cx1, len(env))
        ys = cy1 - (cy1 - cy0) * (0.08 + 0.85 * env)
        path = skia.Path()
        path.addPoly([skia.Point(float(a), float(b)) for a, b in zip(xs, ys)], False)
        area = skia.Path(path)
        area.lineTo(cx1, cy1)
        area.lineTo(cx0, cy1)
        area.close()
        c.drawPath(area, G.P(INK, 1, shader=G.linear_grad(0, cy0, 0, cy1, [INK, INK], alphas=[0.10, 0.0])))
        c.drawPath(path, G.P(INK, 1, stroke=3.2, join="round"))
        c.drawLine(cx0, cy1, cx1, cy1, G.P(LINE, 1, stroke=1.5))
        hv = clamp((t - T_HOVER[0]) / 0.15) * (1 - clamp((t - T_HOVER[1]) / 0.15))
        if hv > 0:
            mx, _ = cursor_pos(t)
            k = int(np.clip((mx - cx0) / (cx1 - cx0) * (len(env) - 1), 0, len(env) - 1))
            px, py = xs[k], ys[k]
            c.drawLine(px, cy0, px, cy1, G.P(INK, 0.3 * hv, stroke=1.4, effect=G.dash(5, 6)))
            G.circle(c, px, py, 9 * hv, G.P(INK))
            G.circle(c, px, py, 5 * hv, G.P("#ffffff"))
            secs = k / (len(env) - 1) * (26.4 if rollu < 0.5 else 32.8)
            label = f"LOUDNESS  ·  0:{int(secs):02d}"
            fm = F("mono", 18, wght=650)
            lw = fm.width(label, 0.16) + 36
            c.drawRRect(rr(px - lw / 2, py - 74, lw, 46, 23), G.P(INK, hv))
            T(c, label, px, py - 43, fm, "#ffffff", a=hv, align=0.5, tracking=0.16)


# ---------------------------------------------------------------- 7 command palette

RESULTS = [("Ship both films", "⏎"), ("Export ProRes 4444", "⌘E"), ("Open the Blender plates", "⌘B")]


def palette(c, t):
    if t < PALETTE[0] or t >= T_ENTER + 0.12:
        return
    with presence(c, t, (PALETTE[0], 99)) as on:
        if not on:
            return
        x, y, w, h = 270, 380, 900, 540
        panel(c, x, y, w, h, r=36)
        icon_search(c, x + 60, y + 72, 34, SUB)
        n = sum(1 for k in T_KEYS if k <= t)
        f = F("inter", 38, wght=500, opsz=32)
        if n == 0:
            T(c, "Type a command", x + 104, y + 86, f, "#b3b0a9")
        else:
            T(c, "ship"[:n], x + 104, y + 86, f, INK)
        cxp = x + 104 + (f.width("ship"[:n]) if n else 0) + 3
        if int(t * 2.4) % 2 == 0 or (T_KEYS[0] <= t < T_KEYS[-1] + 0.2):
            c.drawRect(skia.Rect.MakeXYWH(cxp, y + 52, 3.5, 44), G.P(INK))
        c.drawRRect(rr(x + w - 110, y + 50, 64, 42, 10), G.P(SOFT))
        T(c, "⌘K", x + w - 78, y + 79, F("dejavu-sans-bold", 20), SUB, align=0.5)
        c.drawLine(x, y + 130, x + w, y + 130, G.P(LINE, 1, stroke=1.5))
        fr = F("inter", 31, wght=520, opsz=32)
        fh = F("dejavu-sans-bold", 22)
        for k, (label, hint) in enumerate(RESULTS):
            a = clamp((t - T_KEYS[0] - 0.05 - k * 0.06) / 0.2)
            if a <= 0:
                continue
            ry = y + 160 + k * 112
            sel = k == 0 and n >= 2
            press = clamp((t - T_ENTER) / 0.06)
            if sel:
                c.drawRRect(rr(x + 20, ry, w - 40, 96, 22), G.P(G.mixc(SOFT, INK, press), a))
            col = G.mixc(INK, "#ffffff", press if sel else 0.0)
            c.drawRRect(rr(x + 44, ry + 24, 48, 48, 12), G.P("#ffffff" if sel else SOFT, a))
            if k == 0:
                icon_play(c, x + 69, ry + 48, 22, INK)
            elif k == 1:
                c.drawRect(skia.Rect.MakeXYWH(x + 57, ry + 38, 24, 20), G.P(INK, a, stroke=3))
            else:
                LG.claude(c, x + 68, ry + 48, 28, CLAY, a)
            T(c, label, x + 116, ry + 60 + 12 * (1 - snap(a)), fr, col, a=a)
            T(c, hint, x + w - 50, ry + 58, fh, G.mixc(SUB, "#ffffff", press if sel else 0.0), a=a, align=1.0)


# ---------------------------------------------------------------- 8 end pill

def end(c, t):
    if t < END[0]:
        return
    x0, y0, w0, h0 = 290, 540, 860, 96
    u = whip(clamp((t - END[0]) / 0.36))
    w, h = lerp(w0, 620, u), lerp(h0, 108, u)
    cx, cy = lerp(x0 + w0 / 2, CX, u), lerp(y0 + h0 / 2, CY, u)
    out = clamp((t - (DURATION - 0.7)) / 0.6)
    with G.layer(c, alpha=1 - out, blur=14 * out):
        panel(c, cx - w / 2, cy - h / 2, w, h, r=h / 2, color=INK, lift=0.9)
        ca = snap(clamp((t - END[0] - 0.25) / 0.3))
        if ca > 0:
            ix = cx - w / 2 + 62
            c.drawCircle(ix, cy, 25 * ca, G.P("#ffffff"))
            icon_check(c, ix, cy + 1, 26, INK, p=ca)
            T(c, "Every frame is code", ix + 48, cy + 12, F("inter", 34, wght=600, opsz=32), "#ffffff", a=ca)
        la = clamp((t - END[0] - 0.9) / 0.4)
        if la > 0:
            fm = F("mono", 17, wght=650)
            T(c, "THE FRONTIER  ·  DARIO AMODEI  ·  INTERFACE", CX, cy + 130, fm, SUB, a=la, align=0.5, tracking=0.26)
            fd = F("mono", 12, wght=500)
            T(c, "FAN-MADE · NOT AFFILIATED WITH OPENAI, GOOGLE OR ANTHROPIC", CX, SIZE[1] - 60, fd, SUB, a=0.7 * la,
              align=0.5, tracking=0.2)


# ---------------------------------------------------------------- the film

class Interface(Film):
    duration = DURATION
    size = SIZE

    def bg(self, t):
        return G.rgb(BG0)

    def draw(self, c, t):
        backdrop(c)
        picker(c, t)
        composer(c, t)
        morph(c, t)
        player(c, t)
        settings(c, t)
        stats(c, t)
        palette(c, t)
        end(c, t)
        cursor(c, t)

    def mb(self, t):
        return 8

    def fx(self, t):
        return {"grain": 0.012, "vignette": 0.06, "bloom": 0.0}
