"""ARNAUD'S: the film. White day scenes, black night scenes, gold and light-green accents, cut together with its
own moves: a card dropped on a kitchen table that becomes the input box, a dive into the caret, a spin into the
bead ring, cards racing over a light-green field, a whip up to the counter, a gold circle from the tap, a zoom
into the pin."""
import skia

from .score import *   # noqa: F401,F403 - the timing sheet is the vocabulary of this file
from engine import gfx as G   # after the star import: the sheet's musical grid is also called G
from engine.core import clamp, lerp, snap, whip, in_out_cubic, in_quart
from engine.render import Film
from . import intro as I, table as TB, phone as P, words as W, cards as C, map as M, checkout as K
from .look import GOLD, CREAM, NIGHT, T as txt, ui


def ask_to_giant(c, t):
    """The camera dives into the caret; its trail fills the frame and the night of giant words begins."""
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


def checkout_tap():
    """Screen position of the tap on the terminal (the checkout is gently pushed in by then)."""
    px, py = K.tap_point()
    push = K.SCALE * (1 + 0.04 * clamp((T_TAP - T_CHAT) / 3.5))
    return 960 - K.SHIFT + (px - 960) * push, 560 + (py - 560) * push


def black(c, a):
    if a > 0:
        c.drawRect(skia.Rect.MakeWH(*SIZE), G.P(NIGHT, a))


class Arnauds(Film):
    duration = DURATION
    size = SIZE

    def bg(self, t):
        dark = T_GIANT <= t < T_FIND + 0.2 or T_TO_CHAT <= t < T_MAP + 0.4 or t >= T_CRAVE - 0.3
        return G.rgb(NIGHT) if dark else G.rgb(CREAM)

    def draw(self, c, t):
        if t < T_PHONE:
            TB.table(c, t)
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
            K.checkout(c, t)
            c.restore()
        elif t < T_MAP + 0.45:
            # a gold circle blooms from the tap and the map opens inside it
            tx, ty = checkout_tap()
            u = clamp((t - T_TAP - 0.25) / 0.5)
            K.checkout(c, t)
            G.circle(c, tx, ty, 2300 * snap(u), G.P(GOLD))
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
            black(c, clamp((t - (T_CRAVE - 0.3)) / 0.3))
        elif t < T_END:
            W.crave(c, t)
            black(c, clamp((t - (T_END - 0.25)) / 0.25))
        else:
            I.outro(c, t, T_END)
            if t >= T_END + 1.4:
                txt(c, "Fan-made concept · not affiliated with Arnaud’s", 960, 1062, ui(15, 500), "#6f6f6f",
                    a=0.8 * clamp((t - T_END - 1.4) / 0.4), align=0.5, tracking=0.08)
            black(c, clamp((t - T_FADE[0]) / (T_FADE[1] - T_FADE[0])))

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
        # the closing night gets bloom and a vignette
        night = clamp((t - T_END + 0.1) / 0.2)
        if night > 0:
            fx.update(bloom=0.5 * night, bloom_th=0.5, bloom_r=1.4, vignette=0.26 * night, grain=0.02)
        if T_GIANT + 0.2 <= t < T_FIND or T_CRAVE <= t < T_END:
            fx.update(bloom=0.35, bloom_th=0.6, vignette=0.2)
        if T_CHAT <= t < T_TAP + 0.25:
            fx.update(bloom=0.3, bloom_th=0.7, vignette=0.22)
        for c0 in (T_NAME, T_GIANT, T_FIND, T_TO_CHAT, T_MAP, T_END, T_CREDIT):
            k = t - c0
            if 0 <= k < 0.3:
                fx["chroma"] = max(fx.get("chroma", 0.0), 4.0 * (1 - k / 0.3))
        return fx
