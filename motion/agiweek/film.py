"""AGI WEEK: the film, in the reference clip's design and on its sound. Wordmarks cut on the clicks with each
lab's model on top, a sparkle opens on the drop into the founders' collage, then each lab's own product in its
own colours and faces carries the week: Gemini, ChatGPT, Claude, Grok. Big week ahead."""
import skia

from engine import gfx as G
from engine.core import clamp, in_out_cubic
from engine.render import Film
from . import flash, gemini, chatgpt, claude, grok
from .score import (DURATION, SIZE, T_DROP, T_SEARCH, T_COLLAGE_OUT, T_DARK, T_PHONE, T_OAI, T_COMPOSER,
                    T_SOURCES, T_ANSWER, T_CLAUDE, T_SPARK, T_GRID, T_CANVAS, T_CLICK, T_GROK, T_LAPTOP,
                    T_HOLE)

T_THROUGH = T_DROP + 0.66         # by now the portal has opened past the corners of the frame


def white(c):
    c.drawRect(skia.Rect.MakeWH(*SIZE), G.P("#ffffff"))


class AgiWeek(Film):
    duration = DURATION
    size = SIZE

    def bg(self, t):
        return (0.0, 0.0, 0.0)

    def draw(self, c, t):
        if t < T_DROP:
            flash.flashes(c, t)
        elif t < T_THROUGH:
            flash.sparkle(c, t)
        elif t < T_SEARCH:
            flash.collage(c, t)
        elif t < T_DARK:
            gemini.search(c, t)
        elif t < T_PHONE:
            gemini.dark(c, t)
        elif t < T_OAI:
            gemini.phone(c, t)
        elif t < T_COMPOSER:
            white(c)
            chatgpt.blossom(c, t)
        elif t < T_SOURCES:
            white(c)
            chatgpt.composer(c, t)
        elif t < T_ANSWER:
            white(c)
            chatgpt.sources(c, t)
        elif t < T_CLAUDE:
            white(c)
            chatgpt.answer(c, t)
        elif t < T_SPARK:
            # ChatGPT's white softens into Claude's cream
            u = in_out_cubic(clamp((t - T_CLAUDE) / (T_SPARK - T_CLAUDE)))
            white(c)
            with G.layer(c, alpha=1 - u, blur=10 * u):
                chatgpt.answer(c, t)
            with G.layer(c, alpha=u):
                claude.spark(c, t)
        elif t < T_GRID:
            claude.spark(c, t)
        elif t < T_CANVAS:
            claude.grid(c, t)
        elif t < T_GROK:
            claude.canvas(c, t)
        else:
            grok.grok(c, t)

    def mb(self, t):
        if t < T_DROP:
            return 1                       # hard cuts on the clicks: no sub-frame may straddle two wordmarks
        if t < T_SEARCH or T_GRID <= t < T_CLICK or T_LAPTOP - 0.3 <= t < T_LAPTOP:
            return 14                      # the fast moves: the portal, the wall of canvases, the dive, the zoom
        return 6

    def shutter(self, t):
        return 0.5

    def fx(self, t):
        fx = {"grain": 0.0, "vignette": 0.0}
        if t < T_SEARCH:
            fx.update(bloom=0.28, bloom_th=0.7, bloom_r=1.2)
        if T_HOLE <= t < T_SEARCH:
            fx["zoom_blur"] = 0.05 + 0.1 * clamp((t - T_COLLAGE_OUT) / (T_SEARCH - T_COLLAGE_OUT))
        if t >= T_GROK:
            fx.update(bloom=0.12, bloom_th=0.8)
        return fx
