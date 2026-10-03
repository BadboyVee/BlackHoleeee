"""TOMO 03, the app: the blue lands in a phone, which becomes Tomo's app, today's chores ready to start. Beside it
tomo shrinks into "tomo turns chores into", then "free time,", "every day.", the last word bumping on the beats;
Tomo pops up to watch. A cursor comes in, taps Start, and the camera whips into the button."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, out_quart, in_cubic, in_out_cubic
from .look import WHITE, INK, BLUE, GREY, LINE, sans, mono, italic, wordmark, T, rr, rise, pulse, pop, play_icon
from .robot import tomo, Pose, draw_thing
from . import work
from .score import T_PHONE_IN, T_MARK, T_TURNS, T_FILM, T_BEAT, T_CURSOR, T_CLICK, T_WHIP, T_DASH, beat

BODY = (1318.0, 84.0, 464.0, 912.0, 64.0)
SX, SY, SW, SH, SR = work.SCREEN
HEADER_H = 330.0
ITEM_Y = [508.0, 658.0, 808.0]
TASKS = [("Fold laundry", "12 min · bedroom", "towels"), ("Unload dishes", "8 min · kitchen", "plates"),
         ("Water plants", "3 min · balcony", "plant")]
PILL = (1488.0, 584.0, 124.0, 38.0)
PILL_C = (PILL[0] + PILL[2] / 2, PILL[1] + PILL[3] / 2)


def bezel(c, a):
    if a <= 0:
        return
    x, y, w, h, r = BODY
    p = skia.Path()
    p.addRRect(rr(x, y, w, h, r))
    p.addRRect(rr(SX, SY, SW, SH, SR))
    p.setFillType(skia.PathFillType.kEvenOdd)
    c.drawRRect(rr(x, y + 18, w, h, r), G.P("#000000", 0.10 * a, blur=30))
    c.drawPath(p, G.P("#0c0c0c", a))
    c.drawRRect(rr(x - 6, 290, 8, 92, 3), G.P("#0c0c0c", a))
    c.drawRRect(rr(x + w - 2, 330, 8, 132, 3), G.P("#0c0c0c", a))
    c.drawRRect(rr(1496, 109, 108, 32, 16), G.P("#0c0c0c", a))


def status(c, a=1.0):
    T(c, "9:41", 1373, 136, sans(22, 600), WHITE, a)
    c.drawRRect(rr(1693, 119, 36, 17, 5), G.P(WHITE, a, stroke=2))
    c.drawRRect(rr(1697, 123, 26, 9, 2.5), G.P(WHITE, a))


def avatar(c, t, x, y, r):
    s = pop(t, T_PHONE_IN + 0.06, 0.3, 2.0)
    if s <= 0.01:
        return
    with G.xf(c, x, y, s=s):
        c.drawCircle(0, 0, r, G.P("#dfe7fb"))
        c.save()
        clip = skia.Path()
        clip.addCircle(0, 0, r)
        c.clipPath(clip, doAntiAlias=True)
        tomo(c, 0, -4, r * 5.2, Pose(look=(0.3, 0.1), wink=pulse(t, 5.9, 6.1, 0.04)))
        c.restore()
        c.drawCircle(0, 0, r, G.P(WHITE, 1, stroke=5))


def item(c, t, i, t0, pressed=0.0):
    title, meta, thing = TASKS[i]
    u = clamp((t - t0) / 0.3)
    if u <= 0:
        return
    y = ITEM_Y[i] + 30 * (1 - out_quart(u))
    with G.layer(c, clamp(u * 2.2)):
        c.drawRRect(rr(1354, y, 112, 112, 16), G.P("#f6f6f8"))
        c.save()
        c.clipRRect(rr(1354, y, 112, 112, 16), True)
        draw_thing(c, thing, 1356, y + 4, 108, 104)
        c.restore()
        c.drawRRect(rr(1354.5, y + 0.5, 111, 111, 16), G.P(LINE, 1, stroke=1.4))
        T(c, title, 1488, y + 36, sans(29, 560), INK, tracking=-0.01)
        T(c, meta, 1488, y + 66, mono(20), GREY)
        px, py, pw, ph = PILL
        py = y + 76
        with G.xf(c, px + pw / 2, py + ph / 2, s=1 - 0.08 * pressed):
            c.drawRRect(rr(-pw / 2, -ph / 2, pw, ph, ph / 2), G.P(INK))
            play_icon(c, -30, 0, 12, WHITE)
            T(c, "Start", 10, 7, sans(20, 600), WHITE, align=0.5)


def screen(c, t):
    c.save()
    c.clipRRect(rr(SX, SY, SW, SH, SR), True)
    c.drawRect(skia.Rect.MakeXYWH(SX, SY, SW, SH), G.P(BLUE))
    u = clamp((t - (T_PHONE_IN - 0.06)) / 0.3)
    top = lerp(SY + SH, SY + HEADER_H, out_cubic(u))
    c.drawRect(skia.Rect.MakeLTRB(SX, top, SX + SW, SY + SH), G.P(WHITE))
    a = clamp((t - T_PHONE_IN) / 0.12)
    c.drawRRect(rr(1352, 160, 396, 46, 23), G.P(WHITE, 0.2 * a))
    c.drawCircle(1370, 183, 5, G.P("#7dffb0", a))
    T(c, "at home · charged", 1386, 190, sans(18, 500), WHITE, 0.85 * a)
    avatar(c, t, 1550, 292, 66)
    rise(c, "Tomo", 1550, 400, sans(34, 600), WHITE, t, T_PHONE_IN + 0.12, align=0.5, a=0.95)
    rise(c, "Today", 1354, 478, sans(30, 600), INK, t, T_PHONE_IN + 0.18)
    rise(c, "3 chores", 1746, 478, mono(21), GREY, t, T_PHONE_IN + 0.2, align=1.0)
    pressed = pulse(t, T_CLICK, T_CLICK + 0.12, 0.03)
    for i in range(3):
        item(c, t, i, T_PHONE_IN + 0.24 + 0.08 * i, pressed if i == 0 else 0.0)
    c.restore()
    status(c, a)


def phone(c, t):
    if t < T_PHONE_IN:
        u = work.fold(c, t)
        bezel(c, clamp((u - 0.72) / 0.28))
    else:
        bezel(c, 1.0)
        screen(c, t)
    ring = clamp((t - T_CLICK) / 0.34)
    if 0 < ring < 1:
        c.drawCircle(PILL_C[0], PILL_C[1], 30 + 90 * out_cubic(ring), G.P(BLUE, 0.6 * (1 - ring), stroke=6))


# ---------------------------------------------------------------- the words

MARK = wordmark(120)
MARK_SMALL = 44.0
LINE_Y = 252.0
F_BIG = sans(150, 560)
F_SMALL = sans(40, 500)
TRACK = -0.03
W_FREE = F_BIG.width("free ", TRACK)
W_EVERY = F_BIG.width("every ", TRACK)
W_MARK_SMALL = MARK.width("tomo", -0.01) * MARK_SMALL / MARK.size


def words(c, t):
    u = clamp((t - T_MARK) / 0.34)
    if u > 0:
        k = clamp((t - (T_TURNS[0] - 0.16)) / 0.24)
        e = out_cubic(k)
        s = lerp(1.0, MARK_SMALL / MARK.size, e)
        y = lerp(300.0, LINE_Y + 2, e) + 40 * (1 - out_quart(u))
        with G.xf(c, 140, y, s=s):
            T(c, "tomo", 0, 0, MARK, INK, clamp(u * 2.6), tracking=-0.01)
    x = 140 + W_MARK_SMALL + 14
    rise(c, "turns chores", x, LINE_Y, F_SMALL, GREY, t, T_TURNS[0], dy=16)
    rise(c, "into", x + F_SMALL.width("turns chores "), LINE_Y, F_SMALL, GREY, t, T_TURNS[1], dy=16)
    rise(c, "free", 140, 455, F_BIG, INK, t, T_FILM[0], tracking=TRACK)
    rise(c, "time,", 140 + W_FREE, 455, F_BIG, INK, t, T_FILM[1], tracking=TRACK)
    rise(c, "every", 140, 640, F_BIG, INK, t, T_BEAT[0], tracking=TRACK)
    f = italic(200)
    xb = 140 + W_EVERY + 4
    bump = 0.0
    for k in (13, 14):
        bump = max(bump, math.exp(-max(0.0, t - beat(k)) / 0.09) if t >= beat(k) else 0.0)
    w = f.width("day.")
    with G.xf(c, xb + w / 2, 600, s=1 + 0.07 * bump):
        rise(c, "day.", -w / 2, 40, f, BLUE, t, T_BEAT[1], dy=70)


# ---------------------------------------------------------------- Tomo and the cursor

EYES = (1060.0, 800.0)


def cursor_at(t):
    u = clamp((t - T_CURSOR) / (T_CLICK - 0.05 - T_CURSOR))
    e = in_out_cubic(u)
    return lerp(1960.0, PILL_C[0] + 6, e), lerp(1120.0, PILL_C[1] + 8, e) + 40 * math.sin(math.pi * e)


def cursor(c, t):
    if t < T_CURSOR:
        return
    x, y = cursor_at(t)
    s = 1.35 * (1 - 0.12 * pulse(t, T_CLICK - 0.02, T_CLICK + 0.1, 0.03))
    p = skia.Path()
    for px, py in [(0, 0), (0, 25), (6.5, 19.5), (11, 29.5), (15, 27.6), (10.8, 18), (19, 18)]:
        (p.moveTo if p.isEmpty() else p.lineTo)(px, py)
    p.close()
    with G.xf(c, x, y, s=s):
        c.drawPath(p, G.P("#000000", 0.18, blur=3))
        c.drawPath(p, G.P(INK))
        c.drawPath(p, G.P(WHITE, 1, stroke=1.8, join="round"))


def robot(c, t):
    u = clamp((t - 4.56) / 0.36)
    if u <= 0:
        return
    y = lerp(1500.0, EYES[1], out_back(u, 1.3) if u < 1 else 1.0)
    look = (1.0, -0.2)
    if t >= T_CURSOR:
        cx, cy = cursor_at(t)
        look = (clamp((cx - EYES[0]) / 300, -1, 1), clamp((cy - EYES[1]) / 400, -1, 1))
    nod = math.exp(-((t - T_FILM[1]) % 0.4865) / 0.12) if t >= T_FILM[1] else 0.0
    pose = Pose(turn=16, look=look, blink=pulse(t, 5.42, 5.52, 0.03), tilt=-3.0 + 2.5 * nod,
                happy=pulse(t, T_BEAT[1], T_BEAT[1] + 0.4, 0.04))
    tomo(c, EYES[0], y + 8 * nod, 1000, pose)


# ---------------------------------------------------------------- the whip

def camera(t):
    u = clamp((t - T_WHIP) / (T_DASH - T_WHIP))
    e = in_cubic(u)
    return 16.0 ** e, (lerp(PILL_C[0], 960.0, e), lerp(PILL_C[1], 540.0, e))


def studio(c, t):
    z, (cx, cy) = camera(t)
    with G.xf(c, cx, cy, s=z):
        c.translate(-PILL_C[0], -PILL_C[1])
        words(c, t)
        robot(c, t)
        phone(c, t)
        cursor(c, t)
