"""DevDay 2026, 26.3 s to the end: the twentieth launch and the teaser's own ending. The six faces crowd back in,
count down in their eyes (3, 2, 1), fall into the middle when the bass drops out and burst into blue points that
spell AGI, which fills when the bass comes back, throwing the faces out again like confetti. On the long low note
AGI comes apart into the points of OpenAI DevDay[2026], built left to right the way the teaser builds it. Then the
note that this is a fan-made set of predictions, and the maker's mark: MADE BY VEEE."""
import math

import numpy as np

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, in_out_cubic, out_back, hash01
from .look import gs, WHITE, PURPLE, ORANGE, GREEN, BLUE, DIM, FACES, hit
from .faces import face
from .type import word, draw_word, Build, Flight, pair_index
from .intro import CAST, ORDER
from .launches import CHAIN, draw_chain, frame, PIC, LEAVE
from .score import T_AGI, T_COUNT, T_FALL, T_DECODE, T_REVEAL, T_LOCKUP, T_NOTE, T_CREDIT, CX, CY, N_LIST

GATHER_R = 118
SCALE = 0.36
GONE = {"grey": 0.40, "orange": 0.46, "dark": 0.50, "green": 0.57, "blue": 0.63, "purple": 0.70}
COUNT = [(T_COUNT, "3"), (T_COUNT + 0.5, "2"), (T_COUNT + 1.0, "1")]


def gathered(name, t):
    """(x, y, r, eyes, yaw, pitch, roll) of one face in the final gathering, or None."""
    col, (px, py), _, _, _ = CAST[name]
    j = ORDER.index(name)
    d = t - (T_AGI + 0.04 * j)
    if d < 0:
        return None
    gone = T_FALL + GONE[name]
    if t >= gone:
        return None
    m = 1 + 5.0 * math.exp(-d / 0.1) + 0.3 * math.exp(-d / 0.5)
    u = clamp((t - T_FALL) / (gone - T_FALL))
    s = max(0.0, math.cos(math.pi / 2 * u)) ** 0.9
    if name == "grey":                                  # the one in the middle pops in where it stands
        s *= out_back(clamp(d / 0.26), 2.0) if d < 0.26 else 1.0
    dx, dy = (px - CX) * SCALE, (py - CY) * SCALE
    x, y = PIC[0] + dx * m * s, PIC[1] + dy * m * s
    eyes, yaw, pitch = ("o", "o"), -clamp(dx / 260, -1, 1) * 0.45, clamp(dy / 260, -1, 1) * 0.35
    pulse = 0.0
    for tc, n in COUNT:
        if t >= tc:
            eyes, yaw, pitch = (n, n), 0.0, 0.04
            pulse = hit(t, tc, 0.1)
    roll = 8 * math.sin(2 * math.pi * (0.6 * t + j * 0.3))
    return x, y, GATHER_R * s * (1 + 0.08 * pulse), eyes, yaw, pitch, roll


def gathering(c, t):
    for name in ORDER:
        st = gathered(name, t)
        if st is None:
            continue
        x, y, r, eyes, yaw, pitch, roll = st
        face(c, x, y, r, CAST[name][0], eyes, yaw=yaw, pitch=pitch, roll=roll)


# ---------------------------------------------------------------- AGI

AGI = word((("AGI", WHITE),), 400, CX, PIC[1] + 143)
AGI_LAND = T_DECODE + 0.48
AGI_BUILD = Build(AGI_LAND, spread=0.0, outline=0.05, fill=T_REVEAL - AGI_LAND, fill_spread=0.0,
                  dots_off=T_REVEAL - AGI_LAND + 0.06, pop=0.0)


def _agi_flight():
    n = len(AGI.pts)
    j = np.arange(n)
    ang = 2 * np.pi * hash01(j, 51)
    rad = 40 * hash01(j, 52)
    src = np.stack([PIC[0] + rad * np.cos(ang), PIC[1] + rad * np.sin(ang)], 1)
    t0 = T_DECODE - 0.08 + 0.12 * hash01(j, 53)
    dur = AGI_LAND - t0 - 0.06 * hash01(j, 54)
    return Flight(src, AGI.pts, t0, dur, BLUE, r0=9.0, r1=AGI.dot_r, swell=1.1, bend=0.3, seed=7)


AGI_FLIGHT = _agi_flight()


def spray(c, t, t0, n, seed, speed=(500, 1500), life=0.6, size=(4, 10)):
    """Points thrown out from the middle that fade on the way."""
    tau = t - t0
    if not 0 <= tau < life:
        return
    v = tau / life
    for j in range(n):
        ang = 2 * math.pi * hash01(j, seed)
        sp = lerp(speed[0], speed[1], hash01(j, seed + 1))
        d = sp * tau * (1 - 0.5 * v)
        col = FACES[j % len(FACES)] if j % 3 else BLUE
        c.drawCircle(PIC[0] + d * math.cos(ang), PIC[1] + d * math.sin(ang),
                     lerp(size[0], size[1], hash01(j, seed + 2)) * (1 - v), G.P(col, 1 - v))


CONFETTI_EYES = [("o", "o"), ("^", "^"), ("*", "*"), (">", "<"), ("+", "+"), ("n", "n")]


def confetti(c, t):
    tau = t - T_REVEAL
    if tau < 0:
        return
    for j in range(34):
        ang = -math.pi / 2 + (hash01(j, 61) - 0.5) * 2.8
        sp = 700 + 1000 * hash01(j, 62)
        vx, vy = sp * math.cos(ang) * 1.3, sp * math.sin(ang)
        drag = (1 - math.exp(-tau * 2.2)) / 2.2             # they are thrown out, then drift down
        x = PIC[0] + vx * drag
        y = PIC[1] + vy * drag + 0.5 * 700 * tau * tau
        if y > 1300:
            continue
        r = 18 + 22 * hash01(j, 63)
        face(c, x, y, r * clamp(tau / 0.08), FACES[j % len(FACES)], CONFETTI_EYES[j % len(CONFETTI_EYES)],
             roll=(hash01(j, 64) - 0.5) * 900 * tau, pitch=0.1)


def agi(c, t):
    if t < T_DECODE - 0.08:
        return
    spray(c, t, T_DECODE - 0.06, 36, 71, speed=(700, 1900), life=0.55)
    if t < AGI_LAND:
        AGI_FLIGHT.draw(c, t)
        return
    s = 1 + 0.12 * hit(t, T_REVEAL, 0.12) if t >= T_REVEAL else 1.0
    with G.xf(c, PIC[0], PIC[1], s=s):
        c.translate(-PIC[0], -PIC[1])
        draw_word(c, AGI, t, AGI_BUILD, BLUE)
    if t >= T_REVEAL:
        v = clamp((t - T_REVEAL) / 0.5)
        if v < 1:
            c.drawCircle(PIC[0], PIC[1], 200 + 900 * out_cubic(v), G.P(WHITE, 0.8 * (1 - v), stroke=10 * (1 - v) + 2))
        spray(c, t, T_REVEAL, 44, 81, speed=(900, 2200), life=0.7, size=(5, 12))


# ---------------------------------------------------------------- the teaser's own ending

LOCK_Y = 575
LOCK = word((("OpenAI ", WHITE), ("DevDay", GREEN), ("[", WHITE), ("2026", PURPLE), ("]", WHITE)), 96, CX, LOCK_Y,
            gaps=((1, 10.0), (2, 16.0), (3, 16.0)))
LOCK_FLY = 0.3
LOCK_LAND = T_LOCKUP + LOCK_FLY - 0.02
LOCK_SPREAD = 0.55
LOCK_BUILD = Build(LOCK_LAND, spread=LOCK_SPREAD, outline=0.04, fill=0.12, dots_off=0.22, pop=0.0)
TITLE_AGI = CHAIN[-1]


def _lock_flight():
    src = np.concatenate([AGI.pts, TITLE_AGI.w.pts])
    i, j = pair_index(src, LOCK.pts)
    rank = np.array([LOCK.glyphs[g].rank for g in LOCK.owner[j]])
    t0 = LOCK_LAND + LOCK_SPREAD * rank - LOCK_FLY
    return Flight(src[i], LOCK.pts[j], t0, LOCK_FLY, BLUE, r0=np.where(i < len(AGI.pts), AGI.dot_r, TITLE_AGI.w.dot_r),
                  r1=LOCK.dot_r, swell=0.6, bend=0.2, seed=9)


LOCK_FLIGHT = _lock_flight()
AGI_OUT = Build(AGI_BUILD.t_in, spread=0.0, outline=AGI_BUILD.outline, fill=AGI_BUILD.fill, fill_spread=0.0,
                dots_off=AGI_BUILD.dots_off, pop=0.0, t_out=T_LOCKUP - 0.02, spread_out=0.0)
NOTE = word((("Fan-made predictions. Not affiliated with OpenAI.", DIM),), 30, CX, LOCK_Y + 78)
NOTE_BUILD = Build(T_NOTE, spread=0.45, outline=0.03, fill=0.1, dots_off=0.18)
VEEE = word((("VEEE", WHITE),), 170, CX, 840, fam="archivo", axes=(("wght", 850), ("wdth", 118)))
VEEE_BUILD = Build(T_CREDIT + 0.2, spread=0.3, outline=0.05, fill=0.16, dots_off=0.26)
LIFT = 170.0


def ending(c, t):
    lift = LIFT * in_out_cubic(clamp((t - T_CREDIT) / 0.5))
    with G.xf(c, 0, -lift):
        draw_word(c, LOCK, t, LOCK_BUILD, BLUE)
        draw_word(c, NOTE, t, NOTE_BUILD, ORANGE)
    if t >= T_CREDIT:
        u = clamp((t - T_CREDIT - 0.1) / 0.35)
        G.text(c, "MADE BY", CX, 650 + 18 * (1 - out_cubic(u)), gs(28), G.P(DIM, u), align=0.5, tracking=0.3)
        draw_word(c, VEEE, t, VEEE_BUILD, ORANGE)


# ---------------------------------------------------------------- 26.3 s to the end

def finale(c, t):
    if t < T_LOCKUP:
        gathering(c, t)
        confetti(c, t)
        agi(c, t)
        draw_chain(c, t, CHAIN, until=T_LOCKUP + LEAVE)       # the last title holds until the low note
        frame(c, t, n=N_LIST + 1, t_n=T_AGI)
        return
    # the long low note: everything becomes the lockup
    confetti(c, t)
    fade = clamp((t - T_LOCKUP) / 0.25)
    frame(c, t, n=N_LIST + 1, t_n=T_AGI, a=1 - fade)
    if t < LOCK_LAND + LOCK_SPREAD:
        draw_word(c, AGI, t, AGI_OUT, BLUE, dots=False)
        draw_word(c, TITLE_AGI.w, t, TITLE_AGI.leaving(T_LOCKUP - 0.02 + LEAVE), BLUE, dots=False)
        LOCK_FLIGHT.draw(c, t, waiting=True, only_moving=True)
    ending(c, t)
