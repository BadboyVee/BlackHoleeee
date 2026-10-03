"""TOMO 02, what he does: on blue, Tomo rises into the bottom left and winks while three chores fly in as cards,
each with the real thing on it: laundry folded, dishes put away, plants watered. On the next downbeat the blue
folds away into a phone."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_back, in_out_cubic
from .look import WHITE, INK, BLUE, GREY, sans, mono, T, rr, pulse
from .robot import tomo, Pose, draw_thing
from .score import T_BLUE_FULL, T_CARDS, T_FOLD, T_PHONE_IN

CARD_W, CARD_H, CARD_R = 374.0, 560.0, 34.0
SLOTS = [(707.0, 262.0), (1101.0, 262.0), (1495.0, 262.0)]
FLY = 0.3
CHORES = [("laundry", "Laundry", "folded in 12 min", "towels"), ("dishes", "Dishes", "washed and put away", "plates"),
          ("plants", "Plants", "watered, never missed", "plant")]
EYES = (400.0, 520.0)
SIZE = 1250.0


def chore_card(c, x, y, n):
    tag, title, meta, thing = CHORES[n]
    c.drawRRect(rr(x, y + 16, CARD_W, CARD_H, CARD_R), G.P("#0b2a78", 0.18, blur=26))
    c.drawRRect(rr(x, y, CARD_W, CARD_H, CARD_R), G.P(WHITE))
    T(c, f"// {tag}", x + 31, y + 56, mono(22), GREY)
    T(c, f"{n + 1:02d}", x + CARD_W - 31, y + 56, mono(22), GREY, align=1.0)
    draw_thing(c, thing, x + 14, y + 76, CARD_W - 28, 330)
    T(c, title, x + 31, y + 478, sans(52, 600), INK, tracking=-0.02)
    T(c, meta, x + 31, y + 520, mono(21), GREY)


def cards(c, t):
    for n, (sx, sy) in enumerate(SLOTS):
        t1 = T_CARDS[n]
        u = clamp((t - (t1 - FLY)) / FLY)
        if u <= 0:
            continue
        e = out_back(u, 1.25) if u < 1 else 1.0
        x = lerp(sx + 980, sx, e)
        y = lerp(sy + 150, sy, e)
        rot = lerp(12.0, 0.0, e)
        with G.xf(c, x + CARD_W / 2, y + CARD_H / 2, rot=rot):
            chore_card(c, -CARD_W / 2, -CARD_H / 2, n)


def robot(c, t):
    u = clamp((t - T_BLUE_FULL) / 0.34)
    y = lerp(1400.0, EYES[1], out_back(u, 1.3) if u < 1 else 1.0)
    look = (0.8, 0.2)
    for t1 in T_CARDS:
        look = (lerp(look[0], 1.0, pulse(t, t1 - 0.1, t1 + 0.2, 0.06)), look[1])
    pose = Pose(turn=16, look=look, wink=pulse(t, 2.86, 3.08, 0.04), blink=pulse(t, 3.66, 3.76, 0.03),
                tilt=2.5 * math.sin(2 * math.pi * (t - T_BLUE_FULL) / 0.973))
    tomo(c, EYES[0], y + 5 * math.sin(2 * math.pi * (t - T_BLUE_FULL) / 0.4865), SIZE, pose)


def work(c, t):
    robot(c, t)
    cards(c, t)


# ---------------------------------------------------------------- the fold into the phone

SCREEN = (1330.0, 96.0, 440.0, 888.0, 52.0)


def fold(c, t):
    """The blue, with everything on it, shrinking into the phone's screen. Returns how far it is (0..1)."""
    u = clamp((t - T_FOLD) / (T_PHONE_IN - T_FOLD))
    e = in_out_cubic(u)
    sx, sy, sw, sh, sr = SCREEN
    x, y = lerp(0, sx, e), lerp(0, sy, e)
    w, h = lerp(1920, sw, e), lerp(1080, sh, e)
    r = lerp(0, sr, e)
    c.save()
    c.clipRRect(rr(x, y, w, h, r), True)
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), G.P(BLUE))
    k = lerp(1.0, 0.34, e)
    a = 1 - clamp((u - 0.35) / 0.5)
    if a > 0:
        with G.layer(c, a):
            with G.xf(c, x + w * 0.5, y + h * 0.5, s=k):
                c.translate(-960, -540)
                work(c, t)
    c.restore()
    return u
