"""TOMO 05 and the end. On black: "You rest." and "Tomo does the rest.", the last word sliding in, Tomo glowing in
the corner. White opens out of his eyes and the name drops in letter by letter; Tomo rises behind it and winks,
over "The home robot that helps.", a Reserve button and the small print."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, in_cubic
from .look import WHITE, INK, BLUE, GREY, SOFT, sans, mono, italic, wordmark, T, rr, rise, pulse, pop, typed
from .robot import tomo, Pose
from .score import T_BLACK_FULL, T_YOU, T_WHITE, T_END, T_PEEK, T_TAG, T_BUTTON, T_STATS

X0 = 128.0
Y1, Y2 = 460.0, 730.0
F_YOU = sans(200, 560)
F_REST = italic(270)
F_TOMO = sans(150, 560)
F_REST2 = italic(210)
TRACK = -0.03
X_REST = X0 + F_YOU.width("You ", TRACK)
X_DOES = X0 + F_TOMO.width("Tomo ", TRACK)
X_REST2 = X_DOES + F_TOMO.width("does the ", TRACK)
EYES = (1600.0, 610.0)


def rest_x(t):
    u = clamp((t - T_YOU[4]) / 0.42)
    return lerp(X_REST2 + 320, X_REST2, out_back(u, 1.6) if u < 1 else 1.0), u


def black(c, t):
    rise(c, "You", X0, Y1, F_YOU, WHITE, t, T_YOU[0], tracking=TRACK)
    rise(c, "rest.", X_REST, Y1, F_REST, WHITE, t, T_YOU[1], dy=90)
    rise(c, "Tomo", X0, Y2, F_TOMO, SOFT, t, T_YOU[2], tracking=TRACK)
    rise(c, "does the", X_DOES, Y2, F_TOMO, SOFT, t, T_YOU[3], tracking=TRACK)
    u = clamp((t - T_BLACK_FULL) / 0.36)
    hop = -30 * math.sin(math.pi * clamp((t - T_YOU[4]) / 0.3)) if t >= T_YOU[4] else 0.0
    y = lerp(1500.0, EYES[1], out_back(u, 1.3) if u < 1 else 1.0) + hop
    pose = Pose(turn=-16, look=(-1.0, -0.2) if t < T_YOU[2] - 0.1 else (-1.0, 0.5),
                tilt=-3.0 + 2.5 * math.sin(2 * math.pi * (t - T_BLACK_FULL) / 0.973),
                blink=pulse(t, 12.0, 12.1, 0.03), happy=pulse(t, T_YOU[4], T_YOU[4] + 0.5, 0.05))
    tomo(c, EYES[0], y, 1250, pose)
    x, v = rest_x(t)
    if v > 0:
        T(c, "rest.", x, Y2, F_REST2, WHITE, clamp(v * 3))
    w = clamp((t - T_WHITE) / (T_END - T_WHITE))
    if w > 0:                                                         # the white opens out of his eyes
        r = 20 + 2500 * in_cubic(w)
        c.drawCircle(EYES[0] - 20, EYES[1], r, G.P("#f7f9ff"))


# ---------------------------------------------------------------- the end

MARK = wordmark(330)
MARK_Y = 700.0
MARK_TR = -0.01
MARK_W = MARK.width("tomo", MARK_TR)
MARK_X0 = 960 - MARK_W / 2
LETTERS = [(ch, MARK_X0 + x) for (_, _, x, _), ch in zip(MARK.shape("tomo", MARK_TR).glyphs(), "tomo")]
PEEK = (760.0, 305.0)
CLIP_Y = MARK_Y - MARK.xh + 18


def end(c, t):
    u = clamp((t - T_PEEK) / 0.38)
    if u > 0:
        y = lerp(PEEK[0], PEEK[1], out_back(u, 1.4) if u < 1 else 1.0)
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(0, 0, 1920, CLIP_Y))
        pose = Pose(turn=0, look=(0.0, 0.4), wink=pulse(t, 14.52, 14.76, 0.04),
                    tilt=3.0 * math.sin(2 * math.pi * (t - T_PEEK) / 1.946))
        tomo(c, 960, y, 820, pose)
        c.restore()
    for i, (ch, lx) in enumerate(LETTERS):
        v = clamp((t - (T_END + 0.02 + 0.07 * i)) / 0.36)
        if v <= 0:
            continue
        e = out_back(v, 1.7) if v < 1 else 1.0
        dy = -320 * (1 - e)
        rot = (8.0 if i % 2 else -8.0) * (1 - out_cubic(v))
        w = MARK.width(ch)
        with G.xf(c, lx + w / 2, MARK_Y + dy, rot=rot):
            T(c, ch, -w / 2, 0, MARK, INK, clamp(v * 4))
    ft = sans(50, 450)
    fi = italic(62)
    a, b = "The home robot that ", "helps."
    wa, wb = ft.width(a), fi.width(b)
    x0 = 960 - (wa + wb) / 2
    rise(c, a.strip(), x0, 800, ft, "#6b6b6b", t, T_TAG, dy=20)
    rise(c, b, x0 + wa, 800, fi, INK, t, T_TAG + 0.12, dy=20)
    fb = sans(32, 560)
    fm = mono(28)
    bw = fb.width("Reserve yours") + 80
    mw = fm.width("ships 2027")
    bx = 960 - (bw + 30 + mw) / 2
    s = pop(t, T_BUTTON, 0.3, 2.0)
    if s > 0.01:
        with G.xf(c, bx + bw / 2, 888, s=s):
            c.drawRRect(rr(-bw / 2, -36, bw, 72, 36), G.P(BLUE))
            T(c, "Reserve yours", 0, 11, fb, WHITE, align=0.5)
    T(c, typed("ships 2027", t, T_BUTTON + 0.08, 50), bx + bw + 30, 898, fm, "#6b6b6b")
    small = "5 ft 2 in  ·  8 h on a charge  ·  learns your home in a day"
    fs = mono(24)
    T(c, typed(small, t, T_STATS, 120), 960 - fs.width(small) / 2, 1010, fs, GREY)
