"""DARIO AMODEI, a tribute: dispatch, blur, post and HUD per chapter."""
import math
import os

import numpy as np

from engine import gfx as G
from engine.core import clamp, lerp, noise1, W, H, FPS, CX, CY
from engine.hud import HUD
from engine.render import Film
from .common import INK, PAPER, CLAY, KRAFT, kick_env
from .score import (G as GR, BARS, DURATION, T_PHYS, T_SAFE, T_SCALE, T_ANTH, T_GRACE, T_CENTURY, T_DOMAINS,
                    T_FIN, T_LAST, BREATH)
from . import scenes_a as A
from . import scenes_b as B

SECTIONS = [(0.0, "00 — PROLOGUE"), (T_PHYS, "01 — PHYSICS"), (T_SAFE, "02 — SAFETY"), (T_SCALE, "03 — SCALE"),
            (T_ANTH, "04 — ANTHROPIC"), (T_GRACE, "05 — LOVING GRACE"), (T_FIN, "06 — DARIO AMODEI")]
SHAKES = [(T_GRACE, 22), (T_FIN, 16), (T_LAST, 10), (T_ANTH, 8)]


class Dario(Film):
    duration = DURATION

    def __init__(self, levels_path=None, plate_dir=None):
        self.hud = HUD(GR, BARS, "DARIO AMODEI", "A TRIBUTE  ·  2026", SECTIONS, DURATION)
        self.levels = np.load(levels_path)["levels"] if levels_path and os.path.exists(levels_path) else None
        B.PLATE_DIR = plate_dir

    def bg(self, t):
        return G.rgb(INK)

    def draw(self, c, t):
        dx = dy = 0.0
        for t0, amp in SHAKES:
            if t0 <= t < t0 + 0.6:
                e = amp * math.exp(-(t - t0) / 0.13)
                dx += e * noise1((t - t0) * 30, t0)
                dy += e * noise1((t - t0) * 30, t0 + 3.3)
        c.save()
        if dx or dy:
            z = 1 + (abs(dx) + abs(dy)) * 2.4 / H
            c.translate(CX + dx, CY + dy)
            c.scale(z, z)
            c.translate(-CX, -CY)
        if t < T_PHYS:
            A.s_prologue(c, t)
        elif t < T_SAFE:
            A.s_physics(c, t)
        elif t < T_SCALE:
            A.s_safety(c, t)
        elif t < T_ANTH:
            A.s_scale(c, t)
        elif t < T_GRACE - BREATH:
            B.s_anthropic(c, t)
        elif t < T_GRACE:
            c.drawColor(G.cint("#000000"))
        elif t < T_FIN - BREATH:
            B.s_grace(c, t)
        elif t < T_FIN:
            c.drawColor(G.cint("#000000"))
        else:
            B.s_finale(c, t)
        c.restore()

    def mb(self, t):
        if T_SCALE <= t < A.PLOT_T0:
            return 6
        if T_GRACE <= t < T_CENTURY:
            return 3
        return 10

    def hud_ink(self, t):
        if T_SAFE <= t < T_SCALE or T_ANTH <= t < T_GRACE - BREATH or T_CENTURY <= t < T_DOMAINS:
            if T_ANTH <= t and t >= B.CLAUDE_T and t < T_GRACE:
                return PAPER
            return INK
        return PAPER

    def overlay(self, c, t):
        lv = self.levels[min(len(self.levels) - 1, int(t * FPS))] if self.levels is not None else None
        fade = 1.0 - clamp((t - (DURATION - 0.5)) / 0.5)
        ink = self.hud_ink(t)
        self.hud.draw(c, t, ink=ink, alpha=fade, levels=lv, accent=CLAY)
        txt = readout(t)
        if txt:
            f = G.Font("mono", 14, wght=560)
            G.text(c, txt, CX, H - 118, f, G.P(ink, 0.6 * fade), align=0.5, tracking=0.2)

    def fx(self, t):
        ke = kick_env(t)
        fx = {"grain": 0.03, "vignette": 0.26, "bloom": 0.2, "bloom_th": 0.62, "bloom_tint": (1.0, 0.82, 0.7)}
        if T_SAFE <= t < T_SCALE or T_CENTURY <= t < T_DOMAINS or T_ANTH <= t < T_GRACE:
            fx.update(bloom=0.0, vignette=0.16, grain=0.026)
        if T_GRACE <= t < T_CENTURY:
            fx.update(bloom=0.5, bloom_th=0.45, streaks=0.35 + 0.2 * ke, streak_th=0.5, streak_len=1.2,
                      streak_tint=(1.0, 0.72, 0.5), chroma=1.5 + 3 * ke)
            fx["zoom_blur"] = 0.14 * math.exp(-(t - T_GRACE) / 0.15)
        if T_DOMAINS <= t < T_FIN:
            fx.update(bloom=0.45, bloom_th=0.5)
        if t >= T_FIN:
            fx.update(bloom=0.3, bloom_th=0.55, vignette=0.3)
        for tc, amt, col in ((T_PHYS, 0.25, (1, 1, 1)), (T_SAFE, 0.2, (1, 1, 1)), (T_SCALE, 0.25, (1, 1, 1)),
                             (T_ANTH, 0.3, (1, 0.9, 0.8)), (T_GRACE, 0.9, (1, 0.9, 0.8)), (T_FIN, 0.8, (1, 1, 1)),
                             (T_LAST, 0.35, (1, 0.9, 0.8))):
            if tc <= t < tc + 1.0:
                fx["flash"] = max(fx.get("flash", 0), amt * math.exp(-(t - tc) / 0.09))
                fx["flash_color"] = col
        return fx


def readout(t):
    if t < A.COLLAPSE_T:
        n = sum(1 for s in A.SPIKES if s <= t)
        return f"EXTRACELLULAR TRACE  ·  SPIKES {n:02d}  ·  LOCKING TO THE GRID" if t > GR.at(2) else f"EXTRACELLULAR TRACE  ·  SPIKES {n:02d}"
    if T_PHYS <= t < T_SAFE:
        return "RASTER  ·  40 NEURONS  ·  2.4 S WINDOW"
    if T_SAFE <= t < T_SCALE:
        return "TYPEWRITER  ·  MARKER SWIPE  ·  5 CHECKS ON THE EIGHTHS"
    if T_SCALE <= t < A.PLOT_T0:
        steps = sum(1 for s in A.NET_STEPS if s <= t)
        width = 3 * 2 ** max(0, steps - 1)
        return f"NETWORK  ·  5 LAYERS  ·  WIDTH {width:02d}  ·  EDGES {4 * width * width:04d}"
    if A.PLOT_T0 <= t < T_ANTH:
        return "LOG–LOG  ·  20 RUNS  ·  POWER LAW  ·  EXPONENT −0.050"
    if T_ANTH <= t < B.CLAUDE_T:
        return "ODOMETER  ·  16 → 21  ·  ONE STEP PER SIXTEENTH"
    if B.CLAUDE_T <= t < T_GRACE - BREATH:
        return "WHIP PANEL  ·  CLAUDE SPARK  ·  12 RAYS"
    if T_GRACE <= t < T_CENTURY:
        return "BLENDER CYCLES  ·  12,000 RACKS  ·  LIGHT WAVE r(t)  ·  MIST PASS"
    if T_CENTURY <= t < T_DOMAINS:
        return "RULER  ·  101 TICKS  ·  SQUEEZE ×10"
    return None
