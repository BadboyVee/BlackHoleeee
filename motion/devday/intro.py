"""DevDay 2026, the opening, on white. "Introducing" lands point by point, three points follow it, and the last one
swells into the teaser's big grey face. Then the teaser's own opening, redrawn: the face pulls back and turns right
round; its eyes go * * to - * to - - to o o to > <; the purple, orange, green, dark and blue faces crowd in from
the edges, pull faces of their own, then fall into the middle one after another and burst into orange points that
land on "1 day.", join up and fill. When the bass drops out it becomes "1 day. 20+ launches."."""
import math

import numpy as np

from engine import gfx as G
from engine.core import clamp, lerp, keys, in_quad, out_cubic, in_cubic, in_expo, out_back, in_out_sine, hash01, noise1
from .look import BLACK, GREY, PURPLE, ORANGE, GREEN, DARK, BLUE
from .faces import face
from .type import word, draw_word, Build, Flight
from .score import T_OPEN, T_WORD, T_DOTS, T_SWELL, T_TURN0, T_TURN1, T_SHRINK, T_LAND, T_LINE, CX, CY

R = 330

# colour, where it sits once gathered, when it crowds in, when it is gone into the middle, and its faces:
# (time, eyes, yaw, pitch, roll) - it snaps to each new face on its beat
CAST = {
    "grey": (GREY, (960, 540), None, 4.50, [
        (T_TURN1, ("*", "*"), -0.18, -0.05, -17), (1.48, ("-", "*"), -0.10, 0.00, -12),
        (1.58, ("-", "-"), -0.05, 0.05, -6), (1.78, ("o", "o"), 0.05, 0.12, 6), (2.18, (">", "<"), 0.10, 0.45, 16),
        (2.48, ("*", "*"), 0.16, 0.15, -14), (2.98, (">", "<"), 0.06, -0.05, -11), (3.68, ("o", "o"), 0.0, 0.0, -4),
        (4.18, ("o", "o"), 0.1, 0.05, 6)]),
    "purple": (PURPLE, (340, 190), 2.72, 4.87, [
        (2.70, ("o", "o"), 0.05, 0.10, 14), (3.68, ("-", "-"), 0.05, 0.05, 12), (4.18, ("o", "o"), 0.1, 0.0, 16)]),
    "orange": (ORANGE, (1348, -60), 2.22, 4.58, [
        (2.20, ("/", "/"), -0.95, -0.55, 0), (4.10, ("/", "/"), -0.3, -0.45, 4)]),
    "green": (GREEN, (1650, 598), 2.48, 4.72, [
        (2.44, ("x", "x"), -0.3, 0.0, 10), (2.98, ("+", "+"), 0.0, 0.05, 22), (3.68, ("-", "-"), 0.0, 0.05, 10),
        (3.88, ("+", "+"), 0.0, 0.0, 18)]),
    "dark": (DARK, (410, 985), 2.43, 4.62, [
        (2.48, ("^", "^"), 0.05, 0.30, 4), (3.78, ("-", "-"), 0.0, 0.25, 0), (4.08, ("^", "^"), 0.05, 0.30, 6)]),
    "blue": (BLUE, (1235, 1180), 2.45, 4.78, [
        (2.62, ("\\", "\\"), -0.95, 0.5, 0), (4.15, (">", "<"), -0.2, 0.45, 8)]),
}
ORDER = ["grey", "purple", "orange", "green", "dark", "blue"]


def posed(poses, t, ease=0.14):
    k = 0
    for i, p in enumerate(poses):
        if t >= p[0]:
            k = i
    cur, prev = poses[k], poses[max(k - 1, 0)]
    b = out_cubic(clamp((t - cur[0]) / ease)) if k > 0 else 1.0
    return cur[1], lerp(prev[2], cur[2], b), lerp(prev[3], cur[3], b), lerp(prev[4], cur[4], b)


def shrink(t, gone):
    u = clamp((t - T_SHRINK) / (gone - T_SHRINK))
    return max(0.0, math.cos(math.pi / 2 * u)) ** 0.9


def state(name, t):
    """(x, y, r, eyes, yaw, pitch, roll, g) of one face, or None while it is off stage."""
    col, (px, py), enter, gone, poses = CAST[name]
    if t >= gone:
        return None
    s = shrink(t, gone)
    if name == "grey":
        r = 336 + 814 * math.exp(-t / 0.443) if t < 2.4 else lerp(336, 328, clamp((t - 2.4) / 1.4))
        g = lerp(0.38, 0.45, clamp(t / 1.2)) * (out_back(clamp(t / 0.14), 2.0) if t < 0.14 else 1.0)
        if t < T_TURN1:
            yaw = keys(t, [(T_TURN0, 0.0, None), (0.8, math.pi, in_quad), (T_TURN1, 2 * math.pi - 0.18, out_cubic)])
            pitch = lerp(0.2, -0.05, in_out_sine(clamp(t / T_TURN1)))
            roll = keys(t, [(0.6, 0.0, None), (T_TURN1, -17.0, in_out_sine)])
            eyes = ("*", "*")
        else:
            eyes, yaw, pitch, roll = posed(poses, t)
        m = 1.0
    else:
        if t < enter:
            return None
        d = t - enter
        m = 1 + 1.4 * math.exp(-d / 0.09) + 0.2 * math.exp(-d / 0.6)
        r, g = R, 0.45
        eyes, yaw, pitch, roll = posed(poses, t)
    wob = 7 * (1 - clamp((t - T_SHRINK) / 0.3))
    k = hash01(ORDER.index(name), 4) * 10
    x = CX + (px - CX) * m * s + wob * noise1(t * 0.8 + k, 1)
    y = CY + (py - CY) * m * s + wob * noise1(t * 0.8 + k, 2)
    return x, y, r * s, eyes, yaw, pitch, roll, g


def faces(c, t):
    for name in ORDER:
        st = state(name, t)
        if st is None:
            continue
        x, y, r, eyes, yaw, pitch, roll, g = st
        face(c, x, y, r, CAST[name][0], eyes, yaw=yaw, pitch=pitch, roll=roll, g=g)


# ---------------------------------------------------------------- the points of "1 day."

DAY = word((("1 day.", BLACK),), 330, CX, 640)
DAY_BUILD = Build(T_LAND, spread=0.0, outline=0.07, fill=0.34, fill_spread=0.3, dots_off=0.42, pop=0.0)
SHARE = [("grey", 0.11), ("orange", 0.13), ("dark", 0.13), ("green", 0.17), ("blue", 0.19), ("purple", 0.27)]


def _day_flight():
    n = len(DAY.pts)
    order = np.argsort(hash01(np.arange(n), 21))
    src, t0, dur = np.zeros((n, 2)), np.zeros(n), np.zeros(n)
    at = 0
    for k, (name, share) in enumerate(SHARE):
        cnt = n - at if k == len(SHARE) - 1 else int(round(share * n))
        gone = CAST[name][3]
        for j in order[at:at + cnt]:
            h1, h2, h3 = hash01(j, 31), hash01(j, 32), hash01(j, 33)
            tr = max(gone - 0.07, 4.70) + 0.1 * h1          # the burst comes once most of them are gone
            st = state(name, min(tr, gone) - 1e-3)
            x, y, r = (st[0], st[1], st[2]) if st else (CX, CY, 0.0)
            ang = 2 * math.pi * h2
            src[j] = (x + math.cos(ang) * r * 0.6 * h3, y + math.sin(ang) * r * 0.6 * h3)
            t0[j] = tr
            dur[j] = max(0.12, min(0.34, T_LAND - 0.03 * hash01(j, 34) - tr))
        at += cnt
    return Flight(src, DAY.pts, t0, dur, "#f06a24", r0=11.0, r1=DAY.dot_r, swell=0.9, bend=0.22, seed=5)


DAY_FLIGHT = _day_flight()

LINE = word((("1 day. ", BLACK), ("20+ launches.", BLACK)), 96, CX, 575)
LINE_FIRST = 5                                          # 1 d a y . are already built
LINE_SPREAD = 0.55
LINE_BUILD = Build(T_OPEN + T_LINE + 0.02 - LINE_SPREAD * LINE.glyphs[LINE_FIRST].rank, spread=LINE_SPREAD,
                   outline=0.05,
                   fill=0.13, dots_off=0.24)


# ---------------------------------------------------------------- Introducing…

OPENER = word((("Introducing...", BLACK),), 150, CX, 594)
INTRO = word((("Introducing", BLACK),), 150, OPENER.x0, 594, align=0.0)
DOTS = [(g.path.getBounds().centerX(), g.path.getBounds().centerY(), g.path.getBounds().width() / 2)
        for g in OPENER.glyphs[-3:]]
INTRO_SPREAD = 0.45
INTRO_BUILD = Build(T_WORD, spread=INTRO_SPREAD, outline=0.05, fill=0.14, dots_off=0.26, pop=0.0)


def _intro_flight():
    n = len(INTRO.pts)
    j = np.arange(n)
    rank = INTRO.rank
    src = INTRO.pts + np.stack([(hash01(j, 91) - 0.5) * 440, (hash01(j, 92) - 0.5) * 320], 1)
    return Flight(src, INTRO.pts, T_WORD + INTRO_SPREAD * rank - 0.22, 0.22, ORANGE, r0=4.0, r1=INTRO.dot_r,
                  swell=1.0, bend=0.25, seed=13)


INTRO_FLIGHT = _intro_flight()


def opening(c, t):
    """Introducing… on white; the last point of the ellipsis swells into the teaser's face."""
    INTRO_FLIGHT.draw(c, t, only_moving=True)
    draw_word(c, INTRO, t, INTRO_BUILD, ORANGE)
    for k, ((x, y, r), t0) in enumerate(zip(DOTS, T_DOTS)):
        u = clamp((t - t0) / 0.12)
        if u <= 0:
            continue
        s = out_back(u, 2.6) if u < 1 else 1.0
        if k == 2 and t >= T_SWELL:
            v = clamp((t - T_SWELL) / (T_OPEN - T_SWELL))
            col = G.mixc(ORANGE, GREY, clamp(v / 0.3))
            e = in_cubic(v)
            c.drawCircle(lerp(x, CX, e), lerp(y, CY, e), r + (1150 - r) * in_expo(v), G.P(col))
        else:
            c.drawCircle(x, y, r * s, G.P(ORANGE))


def intro(c, t):
    """The teaser's opening, from T_OPEN up to the first launch (film time t)."""
    tau = t - T_OPEN
    if tau < T_LAND:
        faces(c, tau)
        DAY_FLIGHT.draw(c, tau, only_moving=False)
    elif tau < T_LINE:
        draw_word(c, DAY, tau, DAY_BUILD, ORANGE)
    else:
        draw_word(c, LINE, t, LINE_BUILD, ORANGE, first=LINE_FIRST)
