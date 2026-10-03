"""TOMO: the film. The hook on white, the chores on blue, the app on a phone, a whip into the dashboard, the black
card and the name."""
from engine.core import clamp
from engine.render import Film
from . import hook, work, studio, dash, outro
from .look import hud
from .robot import preload
from .score import DURATION, SIZE, T_BLUE_FULL, T_FOLD, T_WHIP, T_DASH, T_STAMP, T_BLACK_FULL, T_WHITE, T_END

PAPER = (250 / 255, 250 / 255, 250 / 255)
NIGHT = (5 / 255, 5 / 255, 7 / 255)
BLUE = (0x23 / 255, 0x61 / 255, 0xEA / 255)


class Tomo(Film):
    duration = DURATION
    size = SIZE

    def __init__(self):
        preload()                                    # read the renders once, before the render forks

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
            return NIGHT
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
        if t < T_BLUE_FULL:
            hud(c, t, 1, "hook")
        elif t < T_FOLD:
            hud(c, t, 2, "chores")
        elif t < T_DASH:
            hud(c, t, 3, "app")
        elif t < T_BLACK_FULL:
            hud(c, t, 4, "done")
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
