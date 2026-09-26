"""THE FRONTIER: the film. Dispatches scenes by time and sets blur, post and the HUD per section."""
import glob
import math
import os

import cv2
import numpy as np

from engine import gfx as G
from engine.core import clamp, lerp, snap, in_out_cubic, noise1, W, H, FPS, CX, CY
from engine.hud import HUD
from engine.render import Film
from .common import INK, PAPER, WHITE, GREEN, BLUE, CLAY, BOOK, kick_env
from .score import (G as GR, BARS, DURATION, T_DROP_A, T_DROP_B, T_DROP_C, T_CLASH, T_BUILD, T_FINALE,
                    T_LAST, BREATH)
from . import scenes_a as A
from . import scenes_b as B
from . import scenes_c as C

SECTIONS = [(0.0, "00 — COLD OPEN"), (T_DROP_A, "01 — ASTRA 6"), (T_DROP_B, "02 — GEMINI 3M"),
            (T_DROP_C, "03 — FABLE 5.1"), (T_CLASH, "04 — THE CLASH"), (T_FINALE, "05 — THE FRONTIER")]


class Frontier(Film):
    duration = DURATION

    def __init__(self, levels_path=None, plate_dir=None):
        self.hud = HUD(GR, BARS, "THE FRONTIER", "SEASON 2026", SECTIONS, DURATION)
        self.levels = None
        if levels_path and os.path.exists(levels_path):
            self.levels = np.load(levels_path)["levels"]
        C.PLATE_DIR = plate_dir

    def bg(self, t):
        return G.rgb(INK)

    def draw(self, c, t):
        dx, dy, rot = shake(t)
        c.save()
        if dx or dy or rot:
            zoom = 1 + (abs(dx) + abs(dy)) * 2.4 / H
            c.translate(CX + dx, CY + dy)
            c.rotate(rot)
            c.scale(zoom, zoom)
            c.translate(-CX, -CY)
        self.scene(c, t)
        c.restore()
        leaks(c, t)

    def scene(self, c, t):
        if t < T_DROP_A:
            A.s_open(c, t)
        elif t < T_DROP_B:
            A.s_astra(c, t)
        elif t < T_DROP_C:
            B.s_gemini(c, t)
        elif t < T_CLASH:
            B.s_fable(c, t)
        elif t < T_FINALE:
            C.s_clash(c, t)
        else:
            C.s_finale(c, t)

    def mb(self, t):
        if A.T_ZOOM - 0.05 < t < A.T_SPHERE or A.T_WARP <= t < T_DROP_B:
            return 14
        if T_BUILD <= t < T_FINALE:
            return 6
        if T_FINALE + 0.6 < t:
            return 4
        return 10

    def hud_ink(self, t):
        if T_DROP_C <= t < T_CLASH:
            return BOOK
        if T_BUILD <= t < T_FINALE - BREATH:
            return C.build_ink(t)
        return WHITE

    def overlay(self, c, t):
        lv = None
        if self.levels is not None:
            f = min(len(self.levels) - 1, int(t * FPS))
            lv = self.levels[f]
        fade = 1.0 - clamp((t - (DURATION - 0.5)) / 0.5)
        ink = self.hud_ink(t)
        self.hud.draw(c, t, ink=ink, alpha=fade, levels=lv, accent=C.accent_at(t))
        txt = readout(t)
        if txt:
            f = G.Font("mono", 14, wght=560)
            G.text(c, txt, CX, H - 118, f, G.P(ink, 0.62 * fade), align=0.5, tracking=0.2)

    def fx(self, t):
        ke = kick_env(t)
        fx = {"grain": 0.03, "vignette": 0.26, "bloom": 0.22, "bloom_th": 0.6}
        if T_DROP_A <= t < T_DROP_B or t >= T_FINALE:
            fx["chroma"] = 2.5 * ke
        if T_DROP_C <= t < T_CLASH:
            fx.update(grain=0.026, vignette=0.14, bloom=0.0)
        if T_DROP_B <= t < T_DROP_C:
            fx.update(bloom=0.12)
        for tc, col, amt, dec in ((T_DROP_A, (0.12, 0.95, 0.64), 0.4, 0.06), (T_DROP_B, (1, 1, 1), 0.3, 0.06),
                                  (T_DROP_C, (1, 1, 1), 0.25, 0.06), (T_CLASH, (1, 1, 1), 0.4, 0.08),
                                  (T_FINALE, (1, 1, 1), 1.0, 0.22), (T_LAST, (1, 1, 1), 0.5, 0.18)):
            if tc <= t < tc + 1.2:
                fx["flash"] = max(fx.get("flash", 0), amt * math.exp(-(t - tc) / dec))
                fx["flash_color"] = col
        if T_BUILD <= t < T_FINALE:
            u = clamp((t - T_BUILD) / (T_FINALE - T_BUILD))
            fx["glitch"] = 0.08 + 0.5 * u * u
            fx["chroma"] = 2 + 10 * u * u
            fx["glitch_seed"] = int(t * 20)
        for tc in (T_DROP_B, T_DROP_C, T_CLASH):
            if tc - 1 / 30 <= t < tc + 1 / 30:
                fx["glitch"] = 0.35
                fx["glitch_seed"] = int(tc * 100)
        if t >= T_FINALE:
            fx.update(bloom=0.55, bloom_th=0.45, bloom_r=1.2, vignette=0.32, bloom_tint=(1.0, 0.8, 0.66))
            fx["exposure"] = 1.0 + 0.1 * ke
            fx.update(streaks=0.32 + 0.25 * ke, streak_th=0.5, streak_len=1.4)
        # After Effects-style finishing: radial zoom blur on the zoom-throughs, lens streaks on light
        if A.T_ZOOM < t < A.T_SPHERE:
            u = clamp((t - A.T_ZOOM) / (A.T_SPHERE - A.T_ZOOM))
            fx["zoom_blur"] = 0.22 * math.sin(math.pi * u) ** 1.5
        if A.T_SPHERE <= t < A.T_WARP:
            fx.update(streaks=0.22, streak_th=0.55, streak_len=0.9, streak_tint=(0.5, 1.0, 0.8))
        if A.T_WARP <= t < T_DROP_B:
            u = clamp((t - A.T_WARP) / (A.T_COLLAPSE - A.T_WARP))
            fx["zoom_blur"] = 0.03 + 0.14 * u * u
            fx.update(streaks=0.3, streak_th=0.55, streak_tint=(0.5, 1.0, 0.8))
        if T_FINALE <= t < T_FINALE + 0.5:
            fx["zoom_blur"] = 0.16 * math.exp(-(t - T_FINALE) / 0.12)
        return fx


# ---------------------------------------------------------------- camera shake, light leaks, readouts

SHAKES = [(T_DROP_A, 16), (T_DROP_B, 12), (T_DROP_C, 8), (T_CLASH, 12), (T_FINALE, 28), (T_LAST, 14)]


def shake(t):
    dx = dy = rot = 0.0
    for t0, amp in SHAKES:
        if t0 <= t < t0 + 0.6:
            e = amp * math.exp(-(t - t0) / 0.13)
            dx += e * noise1((t - t0) * 34, t0)
            dy += e * noise1((t - t0) * 34, t0 + 5.3)
            rot += e * 0.035 * noise1((t - t0) * 20, t0 + 9.1)
    if T_DROP_A <= t < T_DROP_C or T_FINALE <= t < T_LAST:
        k = kick_env(t, 0.07)
        dx += 3.0 * k * noise1(t * 40, 2.0)
        dy += 3.0 * k * noise1(t * 40, 7.0)
    return dx, dy, rot


LEAKS = [(T_DROP_A - 0.05, 0.7, GREEN, "#b8ffe6"), (T_DROP_C - 0.3, 0.9, CLAY, "#ffd2a8"),
         (T_LAST - 0.1, 1.0, "#ffb27a", "#ffe6c9")]


def leaks(c, t):
    for t0, dur, c1, c2 in LEAKS:
        u = clamp((t - t0) / dur)
        if not 0 < u < 1:
            continue
        a = math.sin(math.pi * u) ** 1.5
        x = lerp(-500, W + 500, in_out_cubic(u))
        for (ox, oy, r, col, al) in ((0, -200, 950, c1, 0.5), (-380, 260, 700, c2, 0.35)):
            c.drawCircle(x + ox, CY + oy, r, G.P(col, 1, blend=G.SCREEN,
                         shader=G.radial_grad(x + ox, CY + oy, r, [col, "#000000"], alphas=[al * a, 0.0])))


def readout(t):
    """Live technical annotations, the reel's footnotes."""
    spb = GR.spb
    if t < GR.at(2, 3):
        i = max([k for k, (tw, _) in enumerate(A.WORDS) if tw <= t] or [0])
        wd = lerp(72, 125, snap(clamp((t - A.WORDS[i][0]) / 0.3)))
        return f"KINETIC TYPE  ·  WDTH {wd:05.1f}  ·  WORD {i + 1}/6  ·  ECHO 0.32 S"
    if t < T_DROP_A - BREATH:
        p = snap(clamp((t - GR.at(2, 3) - 0.1) / 0.35))
        return f"CONSTELLATION  ·  3 NODES  ·  TRIM PATH {p:.2f}"
    if T_DROP_A <= t < A.T_ZOOM:
        wr = clamp((t - GR.at(3, 3)) / 0.45)
        return f"DROP × 5  ·  STAGGER 1/16  ·  SQUASH 0.76  ·  WRITE-ON {wr:.2f}"
    if A.T_ZOOM <= t < A.T_SPHERE:
        z = clamp((t - A.T_ZOOM) / 0.36)
        return f"ZOOM THROUGH THE COUNTER  ·  SCALE ×{1 + 69 * (2 ** (10 * z - 10) if z > 0 else 0):05.1f}"
    if A.T_SPHERE <= t < A.T_WARP:
        deg = math.degrees(0.42 * (t - A.T_ZOOM) + 0.4) % 360
        nl = int(len(A.LINKS) * clamp((t - A.T_SPHERE + 0.2) / 1.2))
        return f"STARS 900  ·  LINKS {nl:03d}  ·  FOV 40°  ·  ROT.Y {deg:05.1f}°"
    if A.T_WARP <= t < A.T_COLLAPSE + 0.25:
        u = clamp((t - A.T_WARP) / (A.T_COLLAPSE - A.T_WARP))
        return f"WARP {6 + 70 * u:04.1f} U/S  ·  STREAKS 650  ·  TYPE TUNNEL × 5"
    if T_DROP_B <= t < B.T_HELIX:
        return f"TWIN ORBIT  ·  PERIOD {2 * spb:.2f} S  ·  TRAIL 14  ·  DEPTH SORTED"
    if B.T_HELIX <= t < B.T_SPLIT:
        return f"DOUBLE HELIX  ·  NODES 248  ·  PHASE {((t - B.T_HELIX) * 2.8) % 6.283:04.2f} RAD"
    if B.T_SPLIT <= t < B.T_WIPE:
        return "MARQUEE ±1100 PX/S  ·  HALVES SWAP EVERY BEAT"
    if T_DROP_C <= t < B.T_TYPE:
        return "SPLIT-FLAP × 5  ·  20 FLIPS/S  ·  LOCK ON THE 1/16"
    if B.T_TYPE <= t < B.T_BOOK:
        n = int(len(B.STORY) * clamp((t - B.T_TYPE - 0.02) / 0.62))
        return f"TYPEWRITER  ·  {n:02d}/{len(B.STORY)} GLYPHS"
    if B.T_BOOK <= t < B.T_RIBBON:
        return "PAGE CURL  ·  κ = −1.3 · SIN θ  ·  4 FLIPS ON THE BEAT"
    if B.T_RIBBON <= t < T_CLASH - 0.4:
        return f"TEXT RING  ·  {len(B.RIB_TEXT)} GLYPHS  ·  R 2.05  ·  BACK HALF MIRRORED"
    if T_FINALE + 0.3 <= t < GR.at(15):
        return "BLENDER CYCLES  ·  150 FRAMES  ·  OIDN DENOISE  ·  AGX PUNCHY"
    return None
