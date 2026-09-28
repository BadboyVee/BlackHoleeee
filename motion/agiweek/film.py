"""AGI WEEK: the film. A black news desk for the open and the close; each lab in its own colours; every hand-off a
move of its own: a whip, a card that becomes the room, a circle, a slide, a split, a slash, a flash."""
import math

import skia

from .score import *   # noqa: F401,F403 - the timing sheet is the vocabulary of this file
from engine import gfx as G   # after the star import: the sheet's musical grid is also called G
from engine.core import clamp, lerp, in_out_cubic, out_cubic, whip, in_cubic
from engine.render import Film
from . import marks as M
from .look import BLACK, WHITE, CLAY
from .scenes_a import cold_open, slate, slate_dive, anthropic, APP
from .scenes_b import openai, race, xai
from .scenes_c import devday, drop, ipo, end

LIGHT = [(T_DIVE, T_RACE), (T_IPO - 0.3, T_END)]      # ivory and white: no bloom, a lighter grain


def circle_clip(c, x, y, r):
    p = skia.Path()
    p.addCircle(x, y, max(0.0, r))
    c.clipPath(p, skia.ClipOp.kIntersect, True)


def black(c, a):
    if a > 0:
        c.drawRect(skia.Rect.MakeWH(*SIZE), G.P(BLACK, a))


class AgiWeek(Film):
    duration = DURATION
    size = SIZE

    def bg(self, t):
        return G.rgb(BLACK)

    def draw(self, c, t):
        if t < T_SLATE:
            # the open whips up and away into the slate
            u = whip(clamp((t - (T_SLATE - 0.22)) / 0.22))
            if u > 0:
                slate(c, t)
            c.save()
            c.translate(0, -1150 * u)
            cold_open(c, t)
            c.restore()
        elif t < T_DIVE:
            slate(c, t)
        elif t < T_ANT:
            slate_dive(c, t)
        elif t < T_OAI:
            anthropic(c, t)
            # a white circle opens from the app window into OpenAI
            u = in_out_cubic(clamp((t - (T_OAI - 0.24)) / 0.24))
            if u > 0:
                c.save()
                cx, cy = APP[0] + APP[2] / 2, APP[1] + APP[3] / 2
                circle_clip(c, cx, cy, 2300 * u)
                openai(c, t)
                c.restore()
        elif t < T_RACE:
            openai(c, t)
            u = out_cubic(clamp((t - (T_RACE - 0.2)) / 0.35))
            if u > 0:
                c.save()
                c.clipRect(skia.Rect.MakeLTRB(960 + 960 * (1 - u), 0, 1920, 1080))
                race(c, t)
                c.restore()
        elif t < T_XAI - 0.25:
            race(c, t)
        elif t < T_XAI + 0.12:
            # the two halves part and xAI is behind them
            xai(c, t)
            spread = in_cubic(clamp((t - (T_XAI - 0.25)) / 0.37))
            c.save()
            c.translate(-960 * spread, 0)
            c.clipRect(skia.Rect.MakeLTRB(0, 0, 960, 1080))
            race(c, t)
            c.restore()
            c.save()
            c.translate(960 * spread, 0)
            c.clipRect(skia.Rect.MakeLTRB(960, 0, 1920, 1080))
            race(c, t)
            c.restore()
        elif t < T_DEV:
            xai(c, t)
            u = in_out_cubic(clamp((t - (T_DEV - 0.22)) / 0.3))
            if u > 0:
                self._slash(c, t, u, devday)
        elif t < T_DEV + 0.08:
            devday(c, t)
            self._slash(c, t, 1.0, None, edge_only=clamp((T_DEV + 0.08 - t) / 0.08))
        elif t < T_DROP:
            devday(c, t)
            # the build collapses to a point just before the drop
            u = in_cubic(clamp((t - (T_DROP - 0.16)) / 0.16))
            if u > 0:
                c.drawRect(skia.Rect.MakeWH(*SIZE), G.P(WHITE, u))
        elif t < T_IPO:
            drop(c, t)
            u = in_out_cubic(clamp((t - (T_IPO - 0.24)) / 0.24))
            if u > 0:
                c.save()
                circle_clip(c, 960, 540, 1150 * u)
                ipo(c, t)
                c.restore()
                M.mark(c, "claude", 960, 540, 200 * (1 - u) + 40, CLAY, 1 - u * 0.6, rot=u * 180)
        elif t < T_END:
            ipo(c, t)
            u = in_out_cubic(clamp((t - (T_END - 0.2)) / 0.25))
            if u > 0:
                c.save()
                c.clipRect(skia.Rect.MakeLTRB(0, 1080 * (1 - u), 1920, 1080))
                end(c, t)
                c.restore()
        else:
            end(c, t)
            black(c, clamp((t - T_FADE[0]) / (T_FADE[1] - T_FADE[0])))

    def _slash(self, c, t, u, draw_next, edge_only=0.0):
        """A diagonal cut, like the stroke through the Grok mark, sweeps across and reveals the next scene."""
        ang = math.radians(-50)
        nx, ny = math.cos(ang), math.sin(ang)
        # a half-plane whose edge travels along the normal from one corner to the other
        d = lerp(-1400, 1400, u)
        px, py = 960 + nx * d, 540 + ny * d
        tx, ty = -ny, nx
        big = 4000
        p = skia.Path()
        p.moveTo(px + tx * big, py + ty * big)
        p.lineTo(px - tx * big, py - ty * big)
        p.lineTo(px - tx * big - nx * big, py - ty * big - ny * big)
        p.lineTo(px + tx * big - nx * big, py + ty * big - ny * big)
        p.close()
        if draw_next is not None:
            c.save()
            c.clipPath(p, skia.ClipOp.kIntersect, True)
            draw_next(c, t)
            c.restore()
        a = 1.0 if draw_next is not None else edge_only
        if a > 0:
            c.drawLine(px + tx * big, py + ty * big, px - tx * big, py - ty * big, G.P(WHITE, a, stroke=10, blur=2))
            c.drawLine(px + tx * big, py + ty * big, px - tx * big, py - ty * big, G.P("#9fb4ff", 0.6 * a, stroke=60,
                                                                                      blur=30))

    def mb(self, t):
        for c0 in CUTS + [T_AGI, T_FAN, T_DIVE, T_ROLL]:
            if c0 - 0.3 <= t <= c0 + 0.35:
                return 14
        if T_DROP <= t < T_DROP + 1.0:
            return 12
        return 8

    def shutter(self, t):
        return 0.55

    def fx(self, t):
        light = any(a <= t < b for a, b in LIGHT)
        if light:
            fx = {"grain": 0.018, "vignette": 0.06}
        else:
            fx = {"grain": 0.03, "vignette": 0.26, "bloom": 0.35, "bloom_th": 0.72, "bloom_r": 1.2}
        if T_RACE <= t < T_XAI:
            fx.update(grain=0.022, vignette=0.12, bloom=0.0)
        for c0, amt in ((T_AGI, 8.0), (T_SLATE, 4.0), (T_ANT, 4.0), (T_OAI, 3.0), (T_RACE, 3.0), (T_XAI, 4.0), (T_ROLL, 6.0), (T_DEV, 5.0), (T_DROP, 14.0), (T_IPO, 4.0), (T_END, 3.0)):
            k = t - c0
            if 0 <= k < 0.3:
                fx["chroma"] = max(fx.get("chroma", 0.0), amt * (1 - k / 0.3))
        k = t - T_DROP
        if 0 <= k < 0.3:
            fx["flash"] = 0.9 * (1 - k / 0.3)
            fx["glitch"] = 0.8 * (1 - k / 0.3)
        k = t - T_ROLL
        if 0 <= k < 0.15:
            fx["glitch"] = max(fx.get("glitch", 0.0), 0.5 * (1 - k / 0.15))
        if T_DIVE <= t < T_ANT:
            fx["zoom_blur"] = 0.08 * math.sin(math.pi * clamp((t - T_DIVE) / (T_ANT - T_DIVE)))
            fx["zoom_center"] = (0.12, 0.55)
        if T_DROP - 0.4 <= t < T_DROP:
            fx["zoom_blur"] = 0.12 * clamp((t - (T_DROP - 0.4)) / 0.4)
        return fx
