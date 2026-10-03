"""TOMO 01, the hook: Tomo leans in from the right, winks and says hey; "Could use an extra hand?" builds word by
word beside him while his eyes follow it, "hand?" gets a scribble, and the blue grows out of it."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, in_cubic, in_back
from .look import WHITE, INK, BLUE, GREY, sans, mono, italic, T, rr, rise, pulse, typed
from .robot import tomo, Pose
from .score import T_WINK, T_PSST, T_LABEL, T_WORDS, T_BLUE, T_BLUE_FULL

EYES = (1560.0, 470.0)                      # where the middle of his eyes sits
SIZE = 1380.0
X0, Y1, Y2 = 140.0, 455.0, 640.0
F1 = sans(150, 560)
F2 = italic(200)
TRACK = -0.03
W_COULD = F1.width("Could ", TRACK)
W_AN = F1.width("an extra ", TRACK)
X_HAND = X0 + W_AN + 6
W_HAND = F2.width("hand?")
HAND_C = (X_HAND + W_HAND * 0.5, Y2 - 62)


def robot(c, t):
    u = clamp(t / 0.46)
    x = lerp(2150.0, EYES[0], out_back(u, 1.1) if u < 1 else 1.0)
    tilt = -12.0 * (1 - out_cubic(clamp(t / 0.62))) + 2.0 * math.sin(2 * math.pi * 0.9 * t)
    look = (-0.2, 0.0)
    if t >= T_WORDS[0] - 0.1:                                            # his eyes follow the words
        k = clamp((t - (T_WORDS[0] - 0.1)) / 0.16)
        look = (lerp(-0.2, -1.0, k), lerp(0, 0.35, k))
    pose = Pose(turn=-16 if t >= T_WORDS[0] - 0.3 else 0, look=look, wink=pulse(t, T_WINK, T_WINK + 0.22, 0.04),
                blink=pulse(t, 2.02, 2.12, 0.03), tilt=tilt)
    tomo(c, x, EYES[1] + 6 * math.sin(2 * math.pi * 1.03 * t), SIZE, pose)


def bubble(c, t):
    a, b = T_PSST
    if not a <= t < b + 0.16:
        return
    s = out_back(clamp((t - a) / 0.16), 2.0) if t < b else 1 - in_back(clamp((t - b) / 0.16), 1.6)
    if s <= 0.01:
        return
    tip = (EYES[0] - 330, EYES[1] + 110)
    with G.xf(c, tip[0], tip[1], s=s):
        w, h = 178.0, 62.0
        x, y = -w - 10, -h - 26
        c.drawRRect(rr(x, y + 6, w, h, 31), G.P("#000000", 0.06, blur=12))
        body = skia.Path()
        body.addRRect(rr(x, y, w, h, 31))
        tail = skia.Path()
        tail.moveTo(x + w - 46, y + h - 6)
        tail.quadTo(x + w - 20, y + h + 6, 0, 0)
        tail.quadTo(x + w - 24, y + h - 20, x + w - 70, y + h - 10)
        tail.close()
        body = skia.Op(body, tail, skia.PathOp.kUnion_PathOp) or body
        c.drawPath(body, G.P(WHITE))
        c.drawPath(body, G.P("#d6d6d6", 1, stroke=2))
        T(c, typed("hey!", t, a + 0.06, 24), x + 36, y + 41, mono(28, 500), INK)


def words(c, t):
    f = mono(26)
    T(c, typed("// for busy homes", t, T_LABEL, 60), X0, 278, f, GREY)
    rise(c, "Could", X0, Y1, F1, INK, t, T_WORDS[0], tracking=TRACK)
    rise(c, "use", X0 + W_COULD, Y1, F1, INK, t, T_WORDS[1], tracking=TRACK)
    rise(c, "an extra", X0, Y2, F1, INK, t, T_WORDS[2], tracking=TRACK)
    rise(c, "hand?", X_HAND, Y2, F2, BLUE, t, T_WORDS[3], dy=70)
    u = clamp((t - 1.96) / 0.2)
    if u > 0:
        p = skia.Path()
        x0, x1, y = X_HAND - 4, X_HAND + W_HAND + 8, Y2 + 30
        p.moveTo(x0, y + 4)
        p.cubicTo(x0 + 0.3 * (x1 - x0), y - 10, x0 + 0.6 * (x1 - x0), y + 8, x1, y - 8)
        c.drawPath(p, G.P(BLUE, 1, stroke=7, cap="round", effect=G.trim(0, out_cubic(u))))


def blue(c, t):
    u = clamp((t - T_BLUE) / (T_BLUE_FULL - T_BLUE))
    if u <= 0:
        return
    r = 2300 * (0.03 + 0.97 * in_cubic(u))
    c.drawCircle(HAND_C[0], HAND_C[1], r, G.P(BLUE))


def hook(c, t):
    robot(c, t)
    bubble(c, t)
    words(c, t)
    blue(c, t)
