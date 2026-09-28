"""DevDay 2026, 7.3-26.3 s: the launches, two to a bar. Each picture pops in on its beat and is swallowed on the
next; each title is built from the points of the one before, which fly across, change colour and join up, the
way the teaser builds "20+ launches.". A counter keeps score at the top, and the corner says what this is: a
fan-made set of predictions."""
import math

import numpy as np

from engine import gfx as G
from engine.core import clamp, in_cubic, out_cubic, hash01
from .look import gs, WHITE, PURPLE, ORANGE, BLUE, DIM, pop
from .items import LAUNCHES
from .type import word, draw_word, Build, Flight, pair
from .intro import LINE, LINE_BUILD
from .score import T_LIST, N_LIST, t_item, T_AGI, CX

PIC = (960.0, 470.0)          # the middle of the picture
TITLE_Y = 905
TITLE_SIZE = 84
LEAVE = 0.10                  # a title starts giving its points back this long before the beat
SPREAD_OUT = 0.06
FLY = 0.16
LANDED = LEAVE - SPREAD_OUT - FLY   # (negative) the new title's points have all landed at T - LANDED


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


class LineStation(Station):
    """The teaser's line, already built when the list takes it over."""

    def __init__(self):
        self.T, self.w, self.accent, self.prev, self.flight, self.lead = None, LINE, ORANGE, None, None, LEAVE
        self.build = LINE_BUILD


AGI_TITLE = "Official launch of"


def make_chain():
    chain = [LineStation()]
    for i, (title, accent, _) in enumerate(LAUNCHES):
        # the white line comes apart early, before the iris closes over it
        lead, fly = (0.22, 0.28) if i == 0 else (LEAVE, FLY)
        chain.append(Station(t_item(i), title_word(title), accent, chain[-1], fly=fly, lead=lead))
    chain.append(Station(T_AGI, title_word(AGI_TITLE), BLUE, chain[-1]))
    return chain


CHAIN = make_chain()
START = CHAIN[1].T - CHAIN[1].lead          # when the list takes the line over from the opening


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


# ---------------------------------------------------------------- the pictures

def burst(c, k, col, n=12, reach=330.0):
    if not 0 <= k < 0.34:
        return
    v = k / 0.34
    for j in range(n):
        ang = 2 * math.pi * (j + hash01(j, 41) * 0.6) / n
        d = 150 + reach * out_cubic(v) * (0.7 + 0.5 * hash01(j, 42))
        c.drawCircle(PIC[0] + d * math.cos(ang), PIC[1] + d * math.sin(ang), (5 + 5 * hash01(j, 43)) * (1 - v),
                     G.P(col, 1 - v * v))


def picture(c, t):
    i = int((t - T_LIST) // 1.0)
    if not 0 <= i < N_LIST:
        return
    k = t - t_item(i)
    _, accent, fn = LAUNCHES[i]
    burst(c, k, accent)
    s = pop(k, 0.0, 0.26, 2.0) * (1 - in_cubic(clamp((k - 0.9) / 0.1)))
    if s <= 0.002:
        return
    with G.xf(c, PIC[0], PIC[1], s=s):
        fn(c, k)


# ---------------------------------------------------------------- what frames the list

HEADER = word((("1 day. 20+ launches.", WHITE),), 36, 84, 108, align=0.0)
HEADER_BUILD = Build(T_LIST + 0.05, spread=0.3, outline=0.03, fill=0.1, dots_off=0.18)
FOOTER = word((("Fan-made predictions · not affiliated with OpenAI", DIM),), 26, 84, 1010, align=0.0)
FOOTER_BUILD = Build(T_LIST + 0.3, spread=0.5, outline=0.03, fill=0.1, dots_off=0.18)


def counter_word(n):
    return word((("[", WHITE), (f"{n:02d}", PURPLE), ("/20", DIM), ("]", WHITE)), 36, 1836, 108, align=1.0,
                gaps=((0, 7.0), (2, 7.0)))


def frame(c, t, n=None, t_n=None, a=1.0):
    """Header, counter and the fan-made line. n is the number on the counter, t_n when it last changed."""
    if a <= 0 or t < T_LIST:
        return
    draw_word(c, HEADER, t, HEADER_BUILD, ORANGE, a=a)
    draw_word(c, FOOTER, t, FOOTER_BUILD, ORANGE, a=a)
    if n is None:
        i = int((t - T_LIST) // 1.0)
        n, t_n = min(i, N_LIST - 1) + 1, t_item(min(i, N_LIST - 1))
    w = counter_word(n)
    draw_word(c, w, t, Build(t_n, spread=0.12, outline=0.02, fill=0.06, dots_off=0.12), ORANGE, a=a,
              first=1, last=3)


def launches(c, t):
    picture(c, t)
    draw_chain(c, t, CHAIN)
    frame(c, t)
