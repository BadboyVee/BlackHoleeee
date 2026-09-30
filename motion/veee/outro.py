"""VEEE 05 and the end. On black: "You launch." and "We make it move.", the last word sliding in as it says, Vee
watching from the corner. White spills out of "move." and the wordmark drops in letter by letter; Vee climbs up
behind it and winks, over the line "Launch films for the frontier.", a Start a film button and the small print."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, in_cubic
from .look import WHITE, INK, BLUE, GREY, SOFT, sans, mono, italic, wordmark, T, rr, rise, pulse, pop, typed
from .dither import blob
from .mascot import VEE, Pose
from .score import T_BLACK_FULL, T_YOU, T_WHITE, T_END, T_PEEK, T_TAG, T_BUTTON, T_STATS

X0 = 128.0
Y1, Y2 = 460.0, 730.0
F_YOU = sans(200, 560)
F_LAUNCH = italic(270)
F_WE = sans(150, 560)
F_MOVE = italic(210)
TRACK = -0.03
X_LAUNCH = X0 + F_YOU.width("You ", TRACK)
X_MAKE = X0 + F_WE.width("We ", TRACK)
X_MOVE = X_MAKE + F_WE.width("make it ", TRACK)
W_MOVE = F_MOVE.width("move.")
MOVE_C = (X_MOVE + W_MOVE / 2, Y2 - 60)
HEAD = (1690.0, 610.0)


def move_x(t):
    """The last word comes in from Vee's side, overshoots, and settles."""
    u = clamp((t - T_YOU[4]) / 0.42)
    return lerp(X_MOVE + 320, X_MOVE, out_back(u, 1.6) if u < 1 else 1.0), u


def black(c, t):
    rise(c, "You", X0, Y1, F_YOU, WHITE, t, T_YOU[0], tracking=TRACK)
    rise(c, "launch.", X_LAUNCH, Y1, F_LAUNCH, WHITE, t, T_YOU[1], dy=90)
    rise(c, "We", X0, Y2, F_WE, SOFT, t, T_YOU[2], tracking=TRACK)
    rise(c, "make it", X_MAKE, Y2, F_WE, SOFT, t, T_YOU[3], tracking=TRACK)
    # Vee, bottom right, reading along; he hops when the last word moves in
    u = clamp((t - T_BLACK_FULL) / 0.36)
    hop = -36 * math.sin(math.pi * clamp((t - T_YOU[4]) / 0.3)) if t >= T_YOU[4] else 0.0
    y = lerp(1500.0, HEAD[1], out_back(u, 1.3) if u < 1 else 1.0) + hop
    look = (-15.0, -3.0) if t < T_YOU[2] - 0.1 else (-15.0, 5.0)
    pose = Pose(look=look, tilt=-5.0 + 3.0 * math.sin(2 * math.pi * (t - T_BLACK_FULL) / 0.973),
                blink=pulse(t, 12.0, 12.1, 0.03), talk=pulse(t, T_YOU[4], T_YOU[4] + 0.14, 0.03))
    VEE(c, HEAD[0], y, 1.0, pose)
    x, v = move_x(t)
    if v > 0:
        # the word moves in, and it keeps moving a little
        T(c, "move.", x, Y2, F_MOVE, WHITE, clamp(v * 3))
    w = clamp((t - T_WHITE) / (T_END - T_WHITE))
    if w > 0:                                         # the white spills out of "move."
        blob(c, MOVE_C[0], MOVE_C[1], 30 + 2400 * in_cubic(w), 150, WHITE)
        T(c, "move.", x, Y2, F_MOVE, BLUE)


# ---------------------------------------------------------------- the end

MARK = wordmark(280)
MARK_Y = 690.0
MARK_TR = 0.02
MARK_W = MARK.width("VEEE", MARK_TR)
MARK_X0 = 960 - MARK_W / 2
LETTERS = [(ch, MARK_X0 + x) for (_, _, x, _), ch in zip(MARK.shape("VEEE", MARK_TR).glyphs(), "VEEE")]
PEEK_Y = (840.0, 356.0)
CLIP_Y = MARK_Y - MARK.cap + 14


def end(c, t):
    # "move." goes as the letters come
    x, _ = move_x(t)
    g = clamp((t - T_END) / 0.2)
    if g < 1:
        with G.xf(c, MOVE_C[0], MOVE_C[1], s=1 - 0.4 * g):
            T(c, "move.", x - MOVE_C[0], Y2 - MOVE_C[1], F_MOVE, BLUE, 1 - g)
    # Vee climbs up behind the wordmark
    u = clamp((t - T_PEEK) / 0.38)
    if u > 0:
        y = lerp(PEEK_Y[0], PEEK_Y[1], out_back(u, 1.4) if u < 1 else 1.0)
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(0, 0, 1920, CLIP_Y))
        pose = Pose(look=(lerp(0.0, -6.0, u), 6.0), wink=pulse(t, 14.52, 14.74, 0.04),
                    tilt=4.0 * math.sin(2 * math.pi * (t - T_PEEK) / 1.946))
        VEE(c, 960, y, 0.62, pose)
        c.restore()
    for i, (ch, lx) in enumerate(LETTERS):
        v = clamp((t - (T_END + 0.02 + 0.07 * i)) / 0.36)
        if v <= 0:
            continue
        e = out_back(v, 1.7) if v < 1 else 1.0
        dy = -300 * (1 - e)
        rot = (8.0 if i % 2 else -8.0) * (1 - out_cubic(v))
        w = MARK.width(ch)
        with G.xf(c, lx + w / 2, MARK_Y + dy, rot=rot):
            T(c, ch, -w / 2, 0, MARK, INK, clamp(v * 4))
    # the line, the button, the small print
    ft = sans(52, 450)
    fi = italic(62)
    a, b = "Launch films for the ", "frontier."
    wa, wb = ft.width(a), fi.width(b)
    x0 = 960 - (wa + wb) / 2
    rise(c, a.strip(), x0, 794, ft, "#6b6b6b", t, T_TAG, dy=20)
    rise(c, b, x0 + wa, 794, fi, INK, t, T_TAG + 0.12, dy=20)
    fb = sans(32, 560)
    fm = mono(28)
    bw = fb.width("Start a film") + 80
    mw = fm.width("made by veee")
    bx = 960 - (bw + 30 + mw) / 2
    s = pop(t, T_BUTTON, 0.3, 2.0)
    if s > 0.01:
        with G.xf(c, bx + bw / 2, 884, s=s):
            c.drawRRect(rr(-bw / 2, -36, bw, 72, 36), G.P(BLUE))
            T(c, "Start a film", 0, 11, fb, WHITE, align=0.5)
    T(c, typed("made by veee", t, T_BUTTON + 0.08, 50), bx + bw + 30, 894, fm, "#6b6b6b")
    small = "6 films  ·  60 fps  ·  every frame is code"
    fs = mono(25)
    T(c, typed(small, t, T_STATS, 120), 960 - fs.width(small) / 2, 1010, fs, GREY)
