"""DevDay 2026: the film. The teaser's opening, twenty launches on the drop, the official launch of AGI, and the
teaser's own ending, marked fan-made and signed."""
from engine.render import Film
from . import intro, launches, finale
from .launches import LEAVE
from .score import DURATION, SIZE, T_LIST, T_AGI


class DevDay(Film):
    duration = DURATION
    size = SIZE

    def bg(self, t):
        return (0.0, 0.0, 0.0)

    def draw(self, c, t):
        if t < T_LIST - LEAVE:
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
