"""VEEE 01, the hook: Vee slides in from the right, winks and whispers psst; "Launch day coming soon?" builds word
by word beside him while he reads along, "soon?" gets a scribble, and the blue grows out of it."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, in_cubic, in_back
from .look import WHITE, INK, BLUE, GREY, sans, mono, italic, T, rr, rise, pulse, typed
from .mascot import VEE, Pose
from .score import T_WINK, T_PSST, T_LABEL, T_WORDS, T_BLUE, T_BLUE_FULL

HEAD = (1440.0, 600.0)
SCALE = 1.3
X0, Y1, Y2 = 140.0, 455.0, 640.0
F1 = sans(150, 560)
F2 = italic(200)
TRACK = -0.03
W_LAUNCH = F1.width("Launch ", TRACK)
W_COMING = F1.width("coming ", TRACK)
X_SOON = X0 + W_COMING + 6
W_SOON = F2.width("soon?")
SOON_C = (X_SOON + W_SOON * 0.5, Y2 - 62)          # the middle of "soon?", where the blue comes from


def vee(c, t):
    u = clamp(t / 0.46)
    x = lerp(1990.0, HEAD[0], out_back(u, 1.1) if u < 1 else 1.0)
    tilt = -16.0 * (1 - out_cubic(clamp(t / 0.62))) + 2.0 * math.sin(2 * math.pi * 0.9 * t)
    look = (-4.0, 0.0)
    if t >= T_WORDS[0] - 0.1:                       # he reads along
        k = clamp((t - (T_WORDS[0] - 0.1)) / 0.16)
        look = (lerp(-4, -15, k), lerp(0, 5, k))
    talk = pulse(t, T_PSST[0] + 0.02, T_PSST[0] + 0.14, 0.02) + pulse(t, T_PSST[0] + 0.2, T_PSST[0] + 0.3, 0.02)
    pose = Pose(look=look, wink=pulse(t, T_WINK, T_WINK + 0.2, 0.04), blink=pulse(t, 2.02, 2.12, 0.03),
                talk=talk, tilt=tilt)
    VEE(c, x, HEAD[1] + 6 * math.sin(2 * math.pi * 1.03 * t), SCALE, pose)


def bubble(c, t):
    """psst..., in a little bubble at his mouth."""
    a, b = T_PSST
    if not a <= t < b + 0.16:
        return
    s = out_back(clamp((t - a) / 0.16), 2.0) if t < b else 1 - in_back(clamp((t - b) / 0.16), 1.6)
    if s <= 0.01:
        return
    tip = (HEAD[0] - 292, HEAD[1] + 70)
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
        T(c, typed("psst…", t, a + 0.06, 30), x + 30, y + 41, mono(28, 500), INK)


def words(c, t):
    f = mono(26)
    T(c, typed("// for founders", t, T_LABEL, 60), X0, 278, f, GREY)
    rise(c, "Launch", X0, Y1, F1, INK, t, T_WORDS[0], tracking=TRACK)
    rise(c, "day", X0 + W_LAUNCH, Y1, F1, INK, t, T_WORDS[1], tracking=TRACK)
    rise(c, "coming", X0, Y2, F1, INK, t, T_WORDS[2], tracking=TRACK)
    rise(c, "soon?", X_SOON, Y2, F2, BLUE, t, T_WORDS[3], dy=70)
    u = clamp((t - 1.96) / 0.2)
    if u > 0:                                        # a quick scribble under it
        p = skia.Path()
        x0, x1, y = X_SOON - 4, X_SOON + W_SOON + 8, Y2 + 30
        p.moveTo(x0, y + 4)
        p.cubicTo(x0 + 0.3 * (x1 - x0), y - 10, x0 + 0.6 * (x1 - x0), y + 8, x1, y - 8)
        c.drawPath(p, G.P(BLUE, 1, stroke=7, cap="round", effect=G.trim(0, out_cubic(u))))


def blue(c, t):
    u = clamp((t - T_BLUE) / (T_BLUE_FULL - T_BLUE))
    if u <= 0:
        return
    r = 2300 * (0.03 + 0.97 * in_cubic(u))
    c.drawCircle(SOON_C[0], SOON_C[1], r, G.P(BLUE))


def hook(c, t):
    vee(c, t)
    bubble(c, t)
    words(c, t)
    blue(c, t)
