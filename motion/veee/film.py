"""VEEE: the film. The hook on white, the work on blue, the studio on a phone, a whip into the render dashboard,
the black card and the wordmark."""
from engine.core import clamp
from engine.render import Film
from . import hook, work, studio, dash, outro
from .look import hud
from .dither import preload
from .score import DURATION, SIZE, T_BLUE_FULL, T_FOLD, T_WHIP, T_DASH, T_STAMP, T_BLACK_FULL, T_WHITE, T_END

PAPER = (250 / 255, 250 / 255, 250 / 255)
INK = (10 / 255, 10 / 255, 10 / 255)
BLUE = (0x23 / 255, 0x61 / 255, 0xEA / 255)


class Veee(Film):
    duration = DURATION
    size = SIZE

    def __init__(self):
        preload()                                    # decode the film clips once, before the render forks

    def bg(self, t):
        if t < T_BLUE_FULL:
            return (1.0, 1.0, 1.0)
        if t < T_FOLD:
            return BLUE
        if t < T_DASH:
            return (1.0, 1.0, 1.0)
        if t < T_BLACK_FULL:
            return PAPER
        if t < T_END:
            return INK
        return (1.0, 1.0, 1.0)

    def draw(self, c, t):
        if t < T_BLUE_FULL:
            hook.hook(c, t)
        elif t < T_FOLD:
            work.work(c, t)
        elif t < T_DASH:
            studio.studio(c, t)
        elif t < T_BLACK_FULL:
            dash.dash(c, t)
        elif t < T_END:
            outro.black(c, t)
        else:
            outro.end(c, t)

    def overlay(self, c, t):
        """The corner comments, drawn once a frame over the motion blur so the running timecode stays sharp."""
        if t < T_BLUE_FULL:
            hud(c, t, 1, "hook")
        elif t < T_FOLD:
            hud(c, t, 2, "the work")
        elif t < T_DASH:
            hud(c, t, 3, "studio")
        elif t < T_BLACK_FULL:
            hud(c, t, 4, "rendered")
        elif t < T_END:
            hud(c, t, 5, "you", dark=True, a=1 - clamp((t - T_WHITE) / 0.12))

    def mb(self, t):
        if T_WHIP - 0.02 <= t < T_DASH + dash.PULL:
            return 16
        if T_STAMP - 0.02 <= t < T_STAMP + 0.2:
            return 12
        return 8

    def shutter(self, t):
        if T_WHIP <= t < T_DASH + 0.2:
            return 1.0
        return 0.5

    def fx(self, t):
        return {"grain": 0.0, "vignette": 0.0}
