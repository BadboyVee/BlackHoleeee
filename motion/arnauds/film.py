"""ARNAUD'S: the film. Scenes are cut together with the reference's moves: a caret wipe, a zoom into the caret,
a spin-in, a lime field that opens out of a card, a vertical whip, a lime circle from a tap, a zoom into a pin."""
import math

import skia

from .score import *   # noqa: F401,F403 - the timing sheet is the vocabulary of this file
from engine import gfx as G   # after the star import: the sheet's musical grid is also called G
from engine.core import clamp, lerp, snap, whip, out_cubic, in_out_cubic, in_quart
from engine.render import Film
from . import intro as I, phone as P, words as W, cards as C, map as M
from .look import WHITE, LIME, LAVENDER, BLUE, GLOW, caret, glow_rrect, rr


def wipe(c, t, below, above):
    """The lavender caret sweeps left to right: `below` is revealed behind it, `above` stays ahead of it."""
    u = in_out_cubic(clamp((t - T_WIPE[0]) / (T_WIPE[1] - T_WIPE[0])))
    x = lerp(-80, SIZE[0] + 900, u)
    above(c, t)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(0, 0, max(0.0, x), SIZE[1]))
    c.drawRect(skia.Rect.MakeWH(*SIZE), G.P(WHITE))
    below(c, t)
    c.restore()
    caret(c, x, -20, SIZE[1] + 40, 900)


def ask_to_giant(c, t):
    """The camera dives into the caret; the lavender fills the frame and the words start."""
    u = clamp((t - T_SEND) / (T_GIANT + 0.25 - T_SEND))
    e = in_quart(u)
    cx, cy = P.typed_caret(t)
    s = 1 + 40 * e
    m = in_out_cubic(u)
    c.save()
    c.translate(lerp(cx, 960, m), lerp(cy, 540, m))
    c.scale(s, s)
    c.translate(-cx, -cy)
    P.ask(c, t)
    c.restore()
    if u > 0.7:
        k = clamp((u - 0.7) / 0.3)
        with G.layer(c, alpha=k):
            c.drawRect(skia.Rect.MakeWH(*SIZE), G.P(WHITE))
            W.giant(c, t)


def to_finding(c, t):
    """A spin and scale into the thinking card, as the reference turns into its bowl."""
    u = snap(clamp((t - T_FIND) / 0.42))
    c.save()
    c.translate(960, 540)
    c.rotate(-28 * (1 - u))
    s = lerp(1.5, 1.0, u)
    c.scale(s, s)
    c.translate(-960, -540)
    W.finding(c, t)
    c.restore()


class Arnauds(Film):
    duration = DURATION
    size = SIZE

    def bg(self, t):
        return (1.0, 1.0, 1.0)

    def draw(self, c, t):
        if t < T_WIPE[0]:
            I.intro(c, t)
        elif t < T_WIPE[1]:
            wipe(c, t, P.ask, I.intro)
        elif t < T_SEND:
            P.ask(c, t)
        elif t < T_GIANT + 0.25:
            ask_to_giant(c, t)
        elif t < T_FIND:
            W.giant(c, t)
        elif t < T_LIME:
            to_finding(c, t)
        elif t < T_TO_CHAT:
            if t < T_LIME + 0.4:
                W.finding(c, t)
            if t < T_FULL + 0.45:
                C.carousel(c, t)
            if t >= T_FULL:
                C.dining_full(c, t)
        elif t < T_TAP + 0.25:
            u = whip(clamp((t - T_TO_CHAT) / 0.36))
            if u < 1:
                c.save()
                c.translate(0, -1100 * u)
                C.dining_full(c, t)
                c.restore()
            c.save()
            c.translate(0, 1100 * (1 - u))
            P.chat(c, t)
            c.restore()
            P.finger(c, t)
        elif t < T_MAP + 0.45:
            # a lime circle blooms from the tap and the map opens inside it
            tx, ty = P.tap_point(T_TAP)
            u = clamp((t - T_TAP - 0.25) / 0.5)
            P.chat(c, t)
            P.finger(c, t)
            r = 2300 * snap(u)
            G.circle(c, tx, ty, r, G.P(LIME))
            v = clamp((t - T_TAP - 0.4) / 0.5)
            if v > 0:
                c.save()
                clip = skia.Path()
                clip.addCircle(tx, ty, 2300 * snap(v))
                c.clipPath(clip, skia.ClipOp.kIntersect, True)
                M.mapscene(c, t)
                c.restore()
        elif t < T_CRAVE:
            M.mapscene(c, t)
            k = clamp((t - (T_CRAVE - 0.3)) / 0.3)
            if k > 0:
                c.drawRect(skia.Rect.MakeWH(*SIZE), G.P(WHITE, k))
        elif t < T_END:
            W.crave(c, t)
            k = clamp((t - (T_END - 0.25)) / 0.25)
            if k > 0:
                c.drawRect(skia.Rect.MakeWH(*SIZE), G.P(WHITE, k))
        else:
            I.outro(c, t, T_END)
            f = clamp((t - T_FADE[0]) / (T_FADE[1] - T_FADE[0]))
            if t >= T_END + 1.4:
                from .look import T as txt, ui, GREY
                txt(c, "Fan-made concept · not affiliated with Arnaud’s", 960, 1030, ui(16, 500), GREY,
                    a=0.8 * clamp((t - T_END - 1.4) / 0.4), align=0.5, tracking=0.08)
            if f > 0:
                c.drawRect(skia.Rect.MakeWH(*SIZE), G.P(WHITE, f))

    def mb(self, t):
        for c0 in CUTS + [T_GIANT, T_TO_CHAT, T_LIME, T_CARDS, T_FULL]:
            if c0 - 0.05 <= t <= c0 + 0.5:
                return 12
        if T_CARDS <= t <= T_PICK:
            return 12
        if T_GIANT <= t < T_FIND:
            return 10
        return 6

    def shutter(self, t):
        return 0.6

    def fx(self, t):
        fx = {"grain": 0.014, "vignette": 0.0}
        for c0 in (T_WIPE[0] + 0.2, T_GIANT, T_FIND, T_TO_CHAT, T_MAP):
            k = t - c0
            if 0 <= k < 0.3:
                fx["chroma"] = max(fx.get("chroma", 0.0), 4.0 * (1 - k / 0.3))
        return fx
