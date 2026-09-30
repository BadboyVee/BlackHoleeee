"""VEEE 02, the work: on blue, Vee rises into the bottom left and winks while three of our own films fly in as
cards, each one playing, printed in dots: launch films (THE FRONTIER), AI news (AGI WEEK) and keynotes (DevDay
2026). On the next downbeat the blue folds away into a phone."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_back, in_out_cubic
from .look import WHITE, INK, BLUE, GREY, LINE, sans, mono, T, rr, pulse
from .dither import Clip
from .mascot import VEE, Pose
from .score import T_BLUE_FULL, T_CARDS, T_FOLD, T_PHONE_IN

CARD_W, CARD_H, CARD_R = 374.0, 470.0, 34.0
SLOTS = [(707.0, 305.0), (1101.0, 305.0), (1495.0, 305.0)]
THUMB = (20.0, 84.0, 334.0, 188.0)                  # inside the card
FLY = 0.3                                           # each card flies for this long and lands on its beat

FILMS = [
    ("launch film", "Launch films", "the frontier · 26.4 s", Clip("the-frontier", 12.7, 334, 188, cell=2, dur=1.7)),
    ("ai news", "AI news", "agi week · 20.8 s",
     Clip("agiweek", 5.8, 334, 188, cell=2, dur=0.6, invert=True, rect=(40, 60, 1840, 1035))),
    ("keynote", "Keynotes", "devday 2026 · 51.6 s",
     Clip("devday", 25.25, 334, 188, cell=2, dur=1.2, invert=True, rect=(400, 110, 1120, 630))),
]

HEAD = (410.0, 610.0)
SCALE = 1.12


def film_card(c, x, y, n, t, t_play):
    tag, title, meta, clip = FILMS[n]
    c.drawRRect(rr(x, y + 16, CARD_W, CARD_H, CARD_R), G.P("#0b2a78", 0.18, blur=26))
    c.drawRRect(rr(x, y, CARD_W, CARD_H, CARD_R), G.P(WHITE))
    T(c, f"// {tag}", x + 31, y + 56, mono(22), GREY)
    T(c, f"{n + 1:02d}", x + CARD_W - 31, y + 56, mono(22), GREY, align=1.0)
    tx, ty, tw, th = THUMB
    u = max(0.0, t - t_play)
    c.save()
    c.clipRRect(rr(x + tx, y + ty, tw, th, 16), True)
    clip.draw(c, x + tx, y + ty, u)
    c.restore()
    c.drawRRect(rr(x + tx + 0.5, y + ty + 0.5, tw - 1, th - 1, 16), G.P(LINE, 1, stroke=1.4))
    # a scrubber under it, playing
    k = clamp(u / max(clip.dur, 0.1))
    sy = y + ty + th + 26
    c.drawLine(x + tx, sy, x + tx + tw, sy, G.P(LINE, 1, stroke=4, cap="round"))
    c.drawLine(x + tx, sy, x + tx + tw * (0.08 + 0.3 * k), sy, G.P(INK, 1, stroke=4, cap="round"))
    c.drawCircle(x + tx + tw * (0.08 + 0.3 * k), sy, 8, G.P(INK))
    T(c, title, x + 31, y + 400, sans(46, 600), INK, tracking=-0.02)
    T(c, meta, x + 31, y + 440, mono(22), GREY)


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
            film_card(c, -CARD_W / 2, -CARD_H / 2, n, t, t1 - FLY)


def vee(c, t):
    u = clamp((t - T_BLUE_FULL) / 0.34)
    y = lerp(1500.0, HEAD[1], out_back(u, 1.3) if u < 1 else 1.0)
    look = (13.0, 4.0)
    for t1 in T_CARDS:                               # a glance at each card as it lands
        look = (lerp(look[0], 15.0, pulse(t, t1 - 0.1, t1 + 0.2, 0.06)), look[1])
    pose = Pose(look=look, wink=pulse(t, 2.86, 3.06, 0.04), blink=pulse(t, 3.66, 3.76, 0.03),
                tilt=3.0 * math.sin(2 * math.pi * (t - T_BLUE_FULL) / 0.973))
    VEE(c, HEAD[0], y + 5 * math.sin(2 * math.pi * (t - T_BLUE_FULL) / 0.4865), SCALE, pose)


def work(c, t):
    vee(c, t)
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
    k = lerp(1.0, 0.34, e)                          # the work, shrinking with it and fading as it goes
    a = 1 - clamp((u - 0.35) / 0.5)
    if a > 0:
        with G.layer(c, a):
            with G.xf(c, x + w * 0.5, y + h * 0.5, s=k):
                c.translate(-960, -540)
                work(c, t)
    c.restore()
    return u
