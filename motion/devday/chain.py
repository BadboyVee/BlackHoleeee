"""DevDay 2026: the chain of lines. Each line is built from the points of the one before, which fly across,
change colour and join up; a section can hand its line to the next section the same way."""
import numpy as np

from .look import gs, WHITE
from .type import word, draw_word, Build, Flight, pair
from .score import CX

TITLE_Y = 905
TITLE_SIZE = 84
LEAVE = 0.10                  # a title starts giving its points back this long before the beat
SPREAD_OUT = 0.06
FLY = 0.16


def title_word(s, size=TITLE_SIZE, y=TITLE_Y):
    w = gs(size).width(s)
    if w > 1560:
        size = size * 1560 / w
    return word(((s, WHITE),), size, CX, y)


class Station:
    """One line in the chain of titles, and how its points get there from the line before: the line before starts
    giving its points back `lead` seconds before the beat, and they fly for `fly` seconds."""

    def __init__(self, T, w, accent, prev=None, fly=FLY, fill_spread=0.12, lead=LEAVE):
        self.T, self.w, self.accent, self.prev, self.lead = T, w, accent, prev, lead
        self.land = T - lead + SPREAD_OUT + fly
        self.build = Build(self.land, spread=0.0, outline=0.02, fill=0.06, fill_spread=fill_spread, dots_off=0.14,
                           pop=0.0)
        self.flight = None
        if prev is not None:
            src, dst = pair(prev.w.pts, w.pts)
            span = max(prev.w.x1 - prev.w.x0, 1.0)
            rank = np.clip((src[:, 0] - prev.w.x0) / span, 0, 1)
            self.flight = Flight(src, dst, T - lead + SPREAD_OUT * rank, fly, prev.accent, accent,
                                 r0=prev.w.dot_r, r1=w.dot_r, swell=0.7, bend=0.16, seed=int(T * 10))

    def leaving(self, T_next, lead=LEAVE):
        """This station's build, taken apart again for the next one."""
        b = self.build
        return Build(b.t_in, spread=b.spread, outline=b.outline, fill=b.fill, fill_spread=b.fill_spread,
                     dots_off=b.dots_off, pop=0.0, t_out=T_next - lead, spread_out=SPREAD_OUT)


class StartStation(Station):
    """A line built by its own section, which the chain takes over from."""

    def __init__(self, w, build, accent):
        self.T, self.w, self.accent, self.prev, self.flight, self.lead = None, w, accent, None, None, LEAVE
        self.build = build


def draw_chain(c, t, chain, a=1.0, until=None):
    """The title at time t: the line in place, or the points on their way to the next one."""
    for j in range(1, len(chain)):
        st = chain[j]
        nxt = chain[j + 1].T - chain[j + 1].lead if j + 1 < len(chain) else until
        if t < st.T - st.lead:
            continue
        if nxt is not None and t >= nxt:
            continue
        if t < st.land:
            prev = chain[j - 1]
            draw_word(c, prev.w, t, prev.leaving(st.T, st.lead), prev.accent, a=a, dots=False)
            st.flight.draw(c, t, a=a, waiting=True)
        else:
            draw_word(c, st.w, t, st.build, st.accent, a=a)
        return
