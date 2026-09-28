"""AGI WEEK, cut as THE RACE TO AGI: the film. A night-race broadcast: the start lights, then every team handed
over by a stinger of its own livery colours sweeping across the frame, a split for the two teams side by side, a
whip out of the pits, a hard cut on the drop, a car crossing the line, and a bug in the corner that never leaves."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, in_out_sine, in_out_cubic
from engine.render import Film
from . import broadcast as B
from .score import (G as GRID, DURATION, SIZE, T_LIGHTS, T_OUT, T_FLIP, T_BUG, T_ANT, T_OAI, T_GRID2, T_XAI, T_BOX,
                    T_ON, T_JACK, T_LAUNCH, T_DEV, T_BUILD, T_SHIFT, T_FLAG, T_CROSS, T_P1, T_ON_TOP, T_END,
                    T_FADE, STING, CUTS)
from .grid import gantry, gantry_rig, title
from .teams import anthropic, openai, grid2, xai, top_half, bottom_half, grid2_top, grid2_bottom, DIV
from .finale import devday, flag, p1, end

GROOVE_BARS = set(range(3, 14)) | {15, 16, 17}     # where the kick plays, so the camera can breathe with it
SECTIONS = [0.0] + CUTS + [DURATION]
LIGHT = [(T_ANT - 0.2, T_GRID2 - 0.3), (T_P1 - 0.2, T_END - 0.2)]      # ivory and white: no bloom
BANDS = {
    "anthropic": [B.INK, B.CLAY, B.IVORY],
    "openai": ["#0d0d0d", "#8b8b93", "#f4f4f5"],
    "xai": ["#f3f3f5", "#55555f", "#16161b"],
    "p1": [B.INK, B.IVORY, B.CLAY],
    "end": [B.IVORY, B.WHITE, B.RED],
    "top": ["#4285f4", "#9b72cb", "#1a1d5e"],
    "bottom": ["#0a1f5c", "#6fb3ff", "#0866ff"],
}
SHAKES = ([(tl, 2.0) for tl in T_LIGHTS] + [(T_OUT, 10.0), (T_FLIP, 4.0), (T_ANT + 0.5, 3.0), (T_BOX, 5.0),
                                             (T_ON, 4.0), (T_JACK, 3.0), (T_LAUNCH, 6.0), (T_FLAG, 11.0),
                                             (T_P1, 5.0), (T_ON_TOP, 3.0), (T_END, 5.0)])


def _edge_x(e, y):
    """The x of a sweep edge at height y: e is where it meets the bottom of the frame; it leans like the type."""
    return e + (1080 - y) * B.SLANT


def _region(e_left, e_right):
    """The slanted strip between two sweep edges (None means the frame's side)."""
    y0, y1 = -20.0, 1100.0
    xl0 = -4000.0 if e_left is None else _edge_x(e_left, y0)
    xl1 = -4000.0 if e_left is None else _edge_x(e_left, y1)
    xr0 = 6000.0 if e_right is None else _edge_x(e_right, y0)
    xr1 = 6000.0 if e_right is None else _edge_x(e_right, y1)
    return G.poly([(xl0, y0), (xr0, y0), (xr1, y1), (xl1, y1)])


def stinger(c, t, t0, cols, draw_prev, draw_next, rtl=False, dur=0.42, stagger=0.05):
    """Livery bands sweep across the frame one after another; the next scene rides in behind the last."""
    n = len(cols)
    edges = []
    for k in range(n + 1):
        u = in_out_sine(clamp((t - t0 - k * stagger) / dur))
        edges.append(lerp(2420.0, -730.0, u) if rtl else lerp(-500.0, 2420.0, u))
    if rtl:
        # edges[0] leads, on the left; the next scene is right of edges[n]
        prev = _region(None, edges[0])
        bands = [_region(edges[k], edges[k + 1]) for k in range(n)]
        nxt = _region(edges[n], None)
        full_prev = _edge_x(edges[0], 1100) >= 1920
        full_next = _edge_x(edges[n], -20) <= 0
    else:
        # edges[0] leads, on the right; the next scene is left of edges[n]
        prev = _region(edges[0], None)
        bands = [_region(edges[k + 1], edges[k]) for k in range(n)]
        nxt = _region(None, edges[n])
        full_prev = _edge_x(edges[0], -20) <= 0
        full_next = _edge_x(edges[n], 1100) >= 1920
    if full_prev:
        draw_prev(c, t)
        return
    if full_next:
        draw_next(c, t)
        return
    c.save()
    c.clipPath(prev, skia.ClipOp.kIntersect, True)
    draw_prev(c, t)
    c.restore()
    for k, reg in enumerate(bands):
        c.drawPath(reg, G.P(cols[k]))
    c.save()
    c.clipPath(nxt, skia.ClipOp.kIntersect, True)
    draw_next(c, t)
    c.restore()


def split_sting(c, t):
    """Gemini's half sweeps in from the left, Muse's from the right, wheel to wheel."""
    c.save()
    c.clipPath(top_half(), skia.ClipOp.kIntersect, True)
    stinger(c, t, T_GRID2 - STING, BANDS["top"], openai, grid2_top)
    c.restore()
    c.save()
    c.clipPath(bottom_half(), skia.ClipOp.kIntersect, True)
    stinger(c, t, T_GRID2 - STING + 0.04, BANDS["bottom"], openai, grid2_bottom, rtl=True)
    c.restore()
    a = clamp((t - (T_GRID2 - 0.15)) / 0.15)
    if a > 0:
        c.drawLine(0, DIV[0], 1920, DIV[1], G.P(B.WHITE, a, stroke=6))


class AgiWeek(Film):
    duration = DURATION
    size = SIZE

    def bg(self, t):
        return G.rgb(B.NIGHT)

    def camera(self, t):
        """(dx, dy, scale): a slow push through every section, a bump on every kick, a knock when things land,
        and an engine's shiver on the grid while the lights hold."""
        i = max(k for k, s0 in enumerate(SECTIONS[:-1]) if t >= s0)
        s0, s1 = SECTIONS[i], SECTIONS[i + 1]
        push = 0.03 * clamp((t - s0) / max(0.1, s1 - s0))
        if t < T_OUT:
            push = 0.07 * clamp((t - T_LIGHTS[0]) / (T_OUT - T_LIGHTS[0])) ** 1.6
        if T_BUILD <= t < T_FLAG:
            push += 0.06 * clamp((t - T_BUILD) / (T_FLAG - T_BUILD)) ** 2
        bump = 0.0
        if GRID.bar_of(t) in GROOVE_BARS:
            bump = 0.008 * math.exp(-((t % GRID.spb) / 0.09))
        shake = 0.0
        for t0, amp in SHAKES:
            k = t - t0
            if 0 <= k < 0.45:
                shake = max(shake, amp * math.exp(-k / 0.1))
        if T_LIGHTS[-1] <= t < T_OUT:
            shake = max(shake, 0.8 + 2.2 * clamp((t - T_LIGHTS[-1]) / (T_OUT - T_LIGHTS[-1])))
        dx = shake * math.sin(t * 97.0)
        dy = shake * math.cos(t * 83.0)
        return dx, dy, 1.0 + push + bump + shake / 900.0

    def draw(self, c, t):
        dx, dy, s = self.camera(t)
        c.save()
        c.translate(960 + dx, 540 + dy)
        c.scale(s, s)
        c.translate(-960, -540)
        self._draw(c, t)
        c.restore()

    def _draw(self, c, t):
        if t < T_OUT:
            gantry(c, t)
        elif t < T_OUT + 0.34:
            # lights out: the camera drives under the gantry and out onto the straight
            title(c, t)
            u = clamp((t - T_OUT) / 0.34)
            s = 1 + 5.5 * u ** 2.2
            with G.layer(c, alpha=1 - clamp((u - 0.45) / 0.55)):
                with G.xf(c, 960, 452 - 700 * u ** 2, s=s):
                    c.translate(-960, -452)
                    gantry_rig(c, t, labels=False)
        elif t < T_ANT - STING:
            title(c, t)
        elif t < T_ANT + 0.08:
            stinger(c, t, T_ANT - STING, BANDS["anthropic"], title, anthropic)
        elif t < T_OAI - STING:
            anthropic(c, t)
        elif t < T_OAI + 0.08:
            stinger(c, t, T_OAI - STING, BANDS["openai"], anthropic, openai)
        elif t < T_GRID2 - STING:
            openai(c, t)
        elif t < T_GRID2 + 0.12:
            split_sting(c, t)
        elif t < T_XAI - STING:
            grid2(c, t)
        elif t < T_XAI + 0.08:
            stinger(c, t, T_XAI - STING, BANDS["xai"], grid2, xai)
        elif t < T_DEV - 0.26:
            xai(c, t)
        elif t < T_DEV + 0.06:
            # a whip pan out of the pit lane with the car
            u = in_out_cubic(clamp((t - (T_DEV - 0.26)) / 0.32))
            for dx, scene in ((-1920 * u, xai), (1920 * (1 - u), devday)):
                c.save()
                c.translate(dx, 0)
                c.clipRect(skia.Rect.MakeWH(*SIZE))
                scene(c, t)
                c.restore()
        elif t < T_FLAG:
            devday(c, t)
        elif t < T_P1 - STING:
            flag(c, t)
            self._crossing(c, t)
        elif t < T_P1 + 0.08:
            stinger(c, t, T_P1 - STING, BANDS["p1"], flag, p1)
            self._crossing(c, t)
        elif t < T_END - STING:
            p1(c, t)
        elif t < T_END + 0.08:
            stinger(c, t, T_END - STING, BANDS["end"], p1, end)
        else:
            end(c, t)
            k = clamp((t - T_FADE[0]) / (T_FADE[1] - T_FADE[0]))
            if k > 0:
                c.drawRect(skia.Rect.MakeWH(*SIZE), G.P("#000000", k))

    def _crossing(self, c, t):
        """Anthropic crosses the line under the flag, just ahead of its colours."""
        u = (t - (T_CROSS - 0.42)) / 0.66
        if 0 <= u <= 1:
            x = lerp(-700, 2700, u)
            B.car(c, "anthropic", x, 1030, s=1.1, dist=x, shadow=0.0)

    def overlay(self, c, t):
        fade = 1 - clamp((t - T_FADE[0]) / 0.4)
        B.live(c, t, 0.35, a=fade)
        # the lap counter flies from the title into the corner, where the bug takes it over
        k = (t - T_BUG) / 0.38
        if 0 <= k < 1:
            dx, dy, s = self.camera(T_BUG)
            x0, y0, s0 = 960 + dx, 540 + dy + (700 - 540) * s, 0.9 * s
            x1, y1 = B.bug_lap_centre()
            e = in_out_cubic(k)
            B.lap_group(c, lerp(x0, x1, e), lerp(y0, y1, e), lerp(s0, 0.2, e), t, T_FLIP,
                        a=1 - clamp((k - 0.7) / 0.3))
        B.bug(c, t, T_BUG + 0.26, a=fade)

    def mb(self, t):
        for c0 in CUTS:
            if c0 - 0.55 <= t <= c0 + 0.3:
                return 14
        if T_LAUNCH <= t < T_DEV:
            return 14
        return 8

    def shutter(self, t):
        return 0.6

    def fx(self, t):
        light = any(a <= t < b for a, b in LIGHT)
        if light:
            fx = {"grain": 0.016, "vignette": 0.06}
        elif T_GRID2 - 0.2 <= t < T_XAI - 0.2 or t >= T_END - 0.2:
            fx = {"grain": 0.02, "vignette": 0.14, "bloom": 0.12, "bloom_th": 0.86}
        else:
            fx = {"grain": 0.03, "vignette": 0.26, "bloom": 0.42, "bloom_th": 0.62, "bloom_r": 1.3}
        if t < T_OUT + 0.3:
            fx.update(streaks=0.05, streak_th=0.75, streak_tint=(1.0, 0.3, 0.22), streak_len=1.4)
        for c0, amt in ((T_OUT, 10.0), (T_ANT, 3.0), (T_OAI, 3.0), (T_GRID2, 3.0), (T_XAI, 3.0), (T_DEV, 5.0),
                        (T_FLAG, 12.0), (T_P1, 4.0), (T_END, 4.0)):
            k = t - c0
            if 0 <= k < 0.3:
                fx["chroma"] = max(fx.get("chroma", 0.0), amt * (1 - k / 0.3))
        if T_OUT <= t < T_OUT + 0.4:
            fx["zoom_blur"] = 0.16 * (1 - (t - T_OUT) / 0.4)
            fx["zoom_center"] = (0.5, 0.42)
        k = t - T_OUT
        if 0 <= k < 0.12:
            fx["flash"] = 0.25 * (1 - k / 0.12)
        if T_SHIFT - 0.1 <= t < T_FLAG:
            fx["zoom_blur"] = 0.1 * clamp((t - (T_SHIFT - 0.1)) / 0.2)
        k = t - T_FLAG
        if 0 <= k < 0.3:
            fx["flash"] = 0.85 * (1 - k / 0.3)
        return fx
