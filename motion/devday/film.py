"""DevDay 2026: the film. Introducing… and the teaser's opening on white, twenty launches on black from the drop,
the official launch of AGI, and the teaser's own ending, marked fan-made and signed."""

from engine import gfx as G
from engine.core import clamp, in_cubic
from engine.render import Film
from . import intro, launches, finale
from .launches import START, PIC
from .score import DURATION, SIZE, T_OPEN, T_LIST, IRIS, T_AGI


class DevDay(Film):
    duration = DURATION
    size = SIZE

    def bg(self, t):
        return (1.0, 1.0, 1.0) if t < T_LIST else (0.0, 0.0, 0.0)

    def draw(self, c, t):
        if T_LIST - IRIS <= t < T_LIST:                  # the white opening closes on a black iris at the drop
            r = 1250 * in_cubic(clamp((t - (T_LIST - IRIS)) / IRIS))
            if r > 2:
                c.drawCircle(PIC[0], PIC[1], r, G.P("#000000"))
        if t < T_OPEN:
            intro.opening(c, t)
        elif t < START:
            intro.intro(c, t)
        elif t < T_AGI:
            launches.launches(c, t)
        else:
            finale.finale(c, t)

    def mb(self, t):
        return 8

    def shutter(self, t):
        return 0.5

    def fx(self, t):
        return {"grain": 0.0, "vignette": 0.0}
