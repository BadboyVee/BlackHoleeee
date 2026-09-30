"""HORIZON: the film. White, then black; the hills; Scout; Radar; the sea at sunset; the mark."""
from engine.render import Film
from . import opening, scout, radar, finale
from .plates import preload
from .score import (DURATION, SIZE, T_INTRO, T_LAPTOP, T_INDEX, T_MEADOW, T_EYE, T_HILLS, T_ICON, T_SUNSET,
                    T_CROSS, T_POCKET, T_NAME, T_MARK, T_BLACK, T_PUSH)

WHITE, BLACK = (1.0, 1.0, 1.0), (0.0, 0.0, 0.0)


class Horizon(Film):
    duration = DURATION
    size = SIZE

    def __init__(self):
        preload()

    def bg(self, t):
        if t < T_INTRO:
            return WHITE
        if t < T_LAPTOP:
            return BLACK
        if T_INDEX <= t < T_MEADOW:
            return WHITE
        if T_EYE <= t < T_HILLS:
            return WHITE
        if T_CROSS <= t < T_POCKET:
            return WHITE
        return BLACK

    def draw(self, c, t):
        if t < T_INTRO:
            opening.white(c, t)
        elif t < T_LAPTOP:
            opening.black(c, t)
        elif t < T_EYE:
            scout.scout(c, t)
        elif t < T_HILLS:
            radar.eye(c, t)
        elif t < T_ICON:
            radar.verbs(c, t)
        elif t < T_SUNSET:
            radar.radar_black(c, t)
        elif t < T_CROSS:
            radar.sunset(c, t)
        elif t < T_POCKET:
            finale.crosshair(c, t)
        elif t < T_NAME:
            finale.pocket(c, t)
        elif t < T_MARK:
            finale.name(c, t)
        elif t < T_BLACK:
            finale.mark_over_hills(c, t)
        else:
            finale.end(c, t)

    def mb(self, t):
        if T_PUSH <= t < T_INDEX + 0.1:
            return 12                                # the push into the laptop's screen
        if (T_LAPTOP <= t < T_PUSH or T_HILLS <= t < T_ICON - 0.35 or T_SUNSET <= t < T_CROSS
                or T_NAME <= t < T_BLACK):
            return 5                                 # slow drifts over the plates
        return 8

    def shutter(self, t):
        return 0.5

    def fx(self, t):
        return {"grain": 0.0, "vignette": 0.0}
