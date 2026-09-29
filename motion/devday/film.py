"""DevDay 2026: the film. Introducing… and the teaser's opening on white; on the drop, black: the OpenAI team, the
developers from 78 countries, Dots (OpenAI's agent bot), twenty launches, the official launch of AGI, and the
teaser's own ending, marked fan-made and signed."""
from engine import gfx as G
from engine.core import clamp, in_cubic
from engine.render import Film
from . import intro, team, world, dots, launches, finale
from .launches import PIC
from .score import DURATION, SIZE, T_OPEN, T_DROP, IRIS, T_WORLD, T_BOT, T_LIST, T_AGI

TEAM_START = team.CHAIN[1].T - team.CHAIN[1].lead      # the white line starts coming apart for the team


class DevDay(Film):
    duration = DURATION
    size = SIZE

    def bg(self, t):
        return (1.0, 1.0, 1.0) if t < T_DROP else (0.0, 0.0, 0.0)

    def draw(self, c, t):
        if T_DROP - IRIS <= t < T_DROP:                  # the white opening closes on a black iris at the drop
            r = 1250 * in_cubic(clamp((t - (T_DROP - IRIS)) / IRIS))
            if r > 2:
                c.drawCircle(PIC[0], PIC[1], r, G.P("#000000"))
        if t < T_OPEN:
            intro.opening(c, t)
        elif t < TEAM_START:
            intro.intro(c, t)
        elif t < T_WORLD:
            team.team(c, t)
        else:
            if t < T_BOT:
                world.world(c, t, with_78=t < dots.START)
            if dots.START <= t < T_LIST:
                dots.dots(c, t, with_word=t < launches.START)
            if t >= T_AGI:
                finale.finale(c, t)
            elif t >= launches.START:
                launches.launches(c, t)

    def mb(self, t):
        return 8

    def shutter(self, t):
        return 0.5

    def fx(self, t):
        return {"grain": 0.0, "vignette": 0.0}
