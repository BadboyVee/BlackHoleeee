"""TOMO 04, done: the camera pulls out of Start onto Tomo's dashboard, where the day is handled. A routine is typed,
the battery counts up and the day's hours light on the beats, Tomo bobs along on duty, folding and watering are
ticked, his safety chips tick, the chores count up, and Done. is stamped across it all. Then his black visor
grows until it is all there is."""
import math

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_quart, in_cubic
from .look import (WHITE, INK, BLUE, BLUE_TINT, BLUE_LINE, GREY, LINE, GRIDLINE, sans, mono, italic, T, rr, card,
                   pulse, pop, typed, check, play_icon)
from .robot import tomo, Pose, draw_thing
from .score import (T_DASH, T_TYPE, T_SYNC, T_CHECK1, T_CHECK2, T_CHIPS, T_DONE, T_STAMP, T_BLACK, T_BLACK_FULL,
                    beat)

BRIEF = (100.0, 90.0, 560.0, 900.0)
AIR = (680.0, 90.0, 560.0, 440.0)
POWER = (1260.0, 90.0, 560.0, 440.0)
TASKS = (680.0, 550.0, 560.0, 440.0)
SAFETY = (1260.0, 550.0, 560.0, 210.0)
TODAY = (1260.0, 780.0, 560.0, 210.0)
CARDS = [BRIEF, AIR, POWER, TASKS, SAFETY, TODAY]
BUTTON = (128.0, 356.0, 504.0, 80.0)
BUTTON_C = (BUTTON[0] + BUTTON[2] / 2, BUTTON[1] + BUTTON[3] / 2)
PULL = 0.5
T_COUNT = (7.45, 8.20)
ROUTINE = "every saturday at 10"
AIR_EYES = (960.0, 300.0)


def label(c, s, x, y):
    T(c, s, x, y, mono(22), GREY)


def grid(c):
    p = G.P(GRIDLINE, 1, stroke=1.5)
    for x in (100, 660, 680, 1240, 1260, 1820):
        c.drawLine(x, -2000, x, 3000, p)
    for y in (90, 530, 550, 760, 780, 990):
        c.drawLine(-3000, y, 5000, y, p)


def chores_done(t):
    return int(round(4 * clamp((t - 7.9) / (T_CHECK2 - 7.9)) + 3 * clamp((t - T_CHECK2) / (T_DONE - T_CHECK2))))


# ---------------------------------------------------------------- laundry day

def tint_row(c, t, t0, y, name, value):
    u = clamp((t - t0) / 0.22)
    if u <= 0:
        return
    e = out_cubic(u)
    c.drawRRect(rr(116, y - 30, 528 * e, 44, 8), G.P(BLUE_TINT))
    T(c, name, 128, y, sans(26, 450), INK, clamp(u * 2))
    T(c, value, 632, y, mono(26, 500), BLUE, clamp(u * 2), align=1.0)


def brief(c, t):
    x, y, w, h = BRIEF
    card(c, x, y, w, h, r=24, shadow=0.03)
    label(c, "// laundry day", 128, 140)
    c.drawRRect(rr(128, 170, 120, 120, 18), G.P("#f6f6f8"))
    c.save()
    c.clipRRect(rr(128, 170, 120, 120, 18), True)
    draw_thing(c, "towels", 130, 176, 116, 110)
    c.restore()
    c.drawRRect(rr(128.5, 170.5, 119, 119, 18), G.P(LINE, 1, stroke=1.4))
    T(c, "Laundry", 275, 222, sans(36, 560), INK, tracking=-0.01)
    T(c, "Sat 10:00", 632, 222, mono(28, 500), INK, align=1.0)
    T(c, "bedroom · 2 loads", 275, 262, mono(22), GREY)
    c.drawLine(128, 321, 632, 321, G.P(LINE, 1, stroke=1.5))
    bx, by, bw, bh = BUTTON
    c.drawRRect(rr(bx, by, bw, bh, 14), G.P(INK))
    f = sans(32, 560)
    tw = f.width("Start now")
    play_icon(c, BUTTON_C[0] - tw / 2 - 16, BUTTON_C[1], 20, WHITE)
    T(c, "Start now", BUTTON_C[0] + 16, BUTTON_C[1] + 11, f, WHITE, align=0.5)
    fm = mono(22)
    ow = fm.width("or set a routine")
    c.drawLine(128, 482, 380 - ow / 2 - 16, 482, G.P(LINE, 1, stroke=1.5))
    c.drawLine(380 + ow / 2 + 16, 482, 632, 482, G.P(LINE, 1, stroke=1.5))
    T(c, "or set a routine", 380, 490, fm, GREY, align=0.5)
    focus = clamp((t - (T_TYPE - 0.1)) / 0.12) * (1 - clamp((t - 8.75) / 0.2))
    if focus > 0:
        c.drawRRect(rr(124, 514, 512, 84, 15), G.P(BLUE_LINE, focus, stroke=5))
    c.drawRRect(rr(128, 518, 504, 76, 12), G.P(WHITE))
    c.drawRRect(rr(128.5, 518.5, 503, 75, 12), G.P(G.mixc(LINE, BLUE, focus), 1, stroke=1.5 + focus))
    run = T(c, typed(ROUTINE, t, T_TYPE, 26), 152, 566, mono(26), INK)
    if focus > 0.5 and (t * 2.0) % 1.0 < 0.6:
        cx = 152 + (run.width if run else 0) + 4
        c.drawLine(cx, 540, cx, 574, G.P(BLUE, 1, stroke=2.5))
    T(c, "Loads", 128, 640, sans(26, 450), INK)
    T(c, "2", 632, 640, mono(26, 500), INK, align=1.0)
    tint_row(c, t, T_CHECK1, 684, "Fold & sort", "+12 min")
    tint_row(c, t, T_SYNC, 728, "Put it away", "on")
    c.drawLine(128, 761, 632, 761, G.P(LINE, 1, stroke=1.5))
    T(c, "Time back", 128, 808, sans(34, 600), INK)
    k = clamp((t - T_CHECK2) / 0.2)
    T(c, "1 h 40", 632, 808 - 14 * out_cubic(k), mono(34, 600), INK, 1 - k, align=1.0)
    T(c, "2 h 05", 632, 822 - 14 * out_cubic(k), mono(34, 600), INK, k, align=1.0)
    c.drawRRect(rr(128, 850, 504, 90, 14), G.P(BLUE))
    fb = sans(32, 560)
    done = clamp((t - T_STAMP) / 0.12)
    if done < 1:
        T(c, "Make it weekly", 380, 906, fb, WHITE, 1 - done, align=0.5)
    if done > 0:
        wd = fb.width("Weekly")
        check(c, 380 - wd / 2 - 8, 894, 30, WHITE, done, stroke=4.5)
        T(c, "Weekly", 380 + 22, 906, fb, WHITE, done, align=0.5)


# ---------------------------------------------------------------- on duty

def on_duty(c, t):
    x, y, w, h = AIR
    card(c, x, y, w, h, r=24, shadow=0.03)
    ph = (t - T_DASH) / 0.4865
    c.drawCircle(716, 133, 6, G.P("#22c55e", 0.55 + 0.45 * math.exp(-(ph % 1.0) * 2.5)))
    label(c, "// on duty", 732, 140)
    c.save()
    c.clipRRect(rr(x + 1, y + 1, w - 2, h - 2, 23), True)
    side = 1 if int(ph) % 2 == 0 else -1
    lean = side * 3.5 * (1 - math.exp(-(ph % 1.0) * 5))
    bob = 6.0 * math.exp(-(ph % 1.0) * 4)
    look = (lerp(0.0, -0.9, pulse(t, T_CHECK1 - 0.3, T_CHECK1 + 0.35, 0.08)),
            lerp(0.1, 0.8, pulse(t, T_CHECK1 - 0.3, T_CHECK1 + 0.35, 0.08)))
    pose = Pose(turn=0, look=look, tilt=lean, blink=pulse(t, 9.3, 9.4, 0.03),
                wink=pulse(t, T_STAMP + 0.05, T_STAMP + 0.32, 0.04), happy=pulse(t, T_CHECK2, T_CHECK2 + 0.4, 0.05))
    tomo(c, AIR_EYES[0], AIR_EYES[1] + bob, 760, pose)
    c.restore()


# ---------------------------------------------------------------- power

HOURS = ["8a", "10a", "12p", "2p", "4p", "6p", "8p", "10p"]
DOTS_X = [1303 + k * (1776 - 1303) / 7 for k in range(8)]
F_BIG = sans(190, 600)


def battery_icon(c, x, y, level):
    c.drawRRect(rr(x - 22, y - 12, 40, 24, 6), G.P(INK, 1, stroke=3))
    c.drawRRect(rr(x + 20, y - 5, 4, 10, 2), G.P(INK))
    c.drawRRect(rr(x - 18, y - 8, 32 * level, 16, 3), G.P("#22c55e"))


def power(c, t):
    x, y, w, h = POWER
    card(c, x, y, w, h, r=24, shadow=0.03)
    label(c, "// power", 1288, 140)
    u = clamp((t - T_COUNT[0]) / (T_COUNT[1] - T_COUNT[0]))
    n = int(round(87 * out_cubic(u)))
    battery_icon(c, 1770, 134, n / 100)
    G.text(c, f"{n}", 1286, 345, F_BIG, G.P(INK), features={"tnum": True})
    T(c, "%", 1286 + F_BIG.width(f"{n}", features={"tnum": True}) + 14, 345, sans(60, 450), GREY)
    y0 = 440
    c.drawLine(DOTS_X[0], y0, DOTS_X[-1], y0, G.P(LINE, 1, stroke=3))
    lit = -1
    for k in range(8):
        if t >= beat(14 + k):
            lit = k
    if lit >= 0:
        xe = DOTS_X[lit]
        if lit < 7:
            xe += (DOTS_X[lit + 1] - DOTS_X[lit]) * clamp((t - beat(14 + lit)) / 0.4865)
        c.drawLine(DOTS_X[0], y0, xe, y0, G.P(BLUE, 1, stroke=3))
    for k in range(8):
        r = 11.0
        if k <= lit:
            r += 7.0 * math.exp(-max(0.0, t - beat(14 + k)) / 0.1)
            c.drawCircle(DOTS_X[k], y0, r, G.P(BLUE))
        else:
            c.drawCircle(DOTS_X[k], y0, r, G.P(WHITE))
            c.drawCircle(DOTS_X[k], y0, r, G.P("#cfcfcf", 1, stroke=2))
        T(c, HOURS[k], DOTS_X[k], 486, mono(19), GREY, align=0.5)


# ---------------------------------------------------------------- tasks

def checkbox(c, x, y, t0, t):
    u = clamp((t - t0) / 0.16)
    s = 1 + 0.18 * math.sin(math.pi * u) if 0 < u < 1 else 1.0
    with G.xf(c, x + 19, y + 19, s=s):
        if u <= 0:
            c.drawRRect(rr(-19, -19, 38, 38, 9), G.P(WHITE))
            c.drawRRect(rr(-18, -18, 36, 36, 8), G.P("#c8c8c8", 1, stroke=2))
        else:
            c.drawRRect(rr(-19, -19, 38, 38, 9), G.P(BLUE))
            check(c, 0, 0, 24, WHITE, clamp(u * 1.4), stroke=4)


def option(c, t, box, t0):
    x, y, w, h = box
    u = clamp((t - t0) / 0.14)
    c.drawRRect(rr(x, y, w, h, 16), G.P(G.mixc(WHITE, BLUE_TINT, u)))
    c.drawRRect(rr(x + 0.5, y + 0.5, w - 1, h - 1, 16), G.P(G.mixc(LINE, BLUE, u), 1, stroke=1.5 + u))


def tasks(c, t):
    x, y, w, h = TASKS
    card(c, x, y, w, h, r=24, shadow=0.03)
    label(c, "// chores", 708, 600)
    option(c, t, (708, 634, 504, 150), T_CHECK1)
    c.drawRRect(rr(726, 652, 114, 114, 12), G.P("#f6f6f8"))
    draw_thing(c, "towels", 728, 660, 110, 100)
    T(c, "Fold the laundry", 860, 696, sans(32, 560), INK, tracking=-0.01)
    T(c, "sorted by who it belongs to", 860, 731, sans(22, 450), GREY)
    T(c, "+12 min", 860, 767, sans(30, 600), BLUE)
    checkbox(c, 1152, 690, T_CHECK1, t)
    option(c, t, (708, 804, 504, 110), T_CHECK2)
    c.drawRRect(rr(726, 822, 74, 74, 12), G.P("#f6f6f8"))
    draw_thing(c, "plant", 728, 824, 70, 70)
    T(c, "Water the plants", 820, 853, sans(30, 560), INK, tracking=-0.01)
    T(c, "+3 min", 820, 888, sans(22, 450), GREY)
    checkbox(c, 1152, 840, T_CHECK2, t)


# ---------------------------------------------------------------- safety, today

CHIPS = ["soft-touch", "kid-safe", "38 dB"]


def safety(c, t):
    x, y, w, h = SAFETY
    card(c, x, y, w, h, r=24, shadow=0.03)
    label(c, "// safety", 1288, 600)
    T(c, "Built for homes, not factories.", 1288, 650, sans(28, 500), INK, tracking=-0.01)
    f = mono(22, 500)
    cx = 1290.0
    for i, s in enumerate(CHIPS):
        cw = f.width(s) + 66
        c.drawRRect(rr(cx, 680, cw, 50, 25), G.P(WHITE))
        c.drawRRect(rr(cx + 0.5, 680.5, cw - 1, 49, 25), G.P(LINE, 1, stroke=1.5))
        T(c, s, cx + 20, 713, f, INK)
        check(c, cx + cw - 26, 705, 20, BLUE, clamp((t - (T_CHIPS + 0.14 * i)) / 0.16), stroke=3.5)
        cx += cw + 12


def today(c, t):
    x, y, w, h = TODAY
    card(c, x, y, w, h, r=24, shadow=0.03)
    label(c, "// today", 1288, 830)
    T(c, "saturday", 1738, 830, mono(21), GREY, align=1.0)
    n = chores_done(t)
    run = G.text(c, f"{n}", 1288, 902, mono(46, 500), G.P(INK), features={"tnum": True})
    T(c, "/ 7 chores done", 1288 + run.width + 14, 902, mono(24), GREY)
    c.drawRRect(rr(1288, 930, 504, 12, 6), G.P("#efefef"))
    if n > 0:
        c.drawRRect(rr(1288, 930, max(12.0, 504 * n / 7), 12, 6), G.P(BLUE))
    d = clamp((t - T_DONE) / 0.16)
    if d > 0:
        check(c, 1700, 893, 24, BLUE, d, stroke=4)
        T(c, "all done", 1792, 902, mono(24, 500), BLUE, d, align=1.0)


# ---------------------------------------------------------------- Done.

STAMP_C = (980.0, 700.0)


def stamp(c, t):
    u = clamp((t - T_STAMP) / 0.13)
    if u <= 0:
        return
    s = lerp(3.4, 1.0, out_cubic(u))
    f = italic(170)
    tw = f.width("Done.")
    w, h = tw + 110, 190.0
    with G.xf(c, STAMP_C[0], STAMP_C[1], s=s, rot=-7.0):
        with G.layer(c, lerp(0.35, 1.0, u)):
            c.drawRRect(rr(-w / 2, -h / 2, w, h, 28), G.P("#eef3fd", 0.9))
            c.drawRRect(rr(-w / 2, -h / 2, w, h, 28), G.P(BLUE, 1, stroke=6))
            c.drawRRect(rr(-w / 2 + 12, -h / 2 + 12, w - 24, h - 24, 20), G.P(BLUE, 0.35, stroke=2))
            T(c, "Done.", 0, 56, f, BLUE, align=0.5)
    v = clamp((t - T_STAMP - 0.1) / 0.55)
    if 0 < v < 1:
        c.drawCircle(STAMP_C[0], STAMP_C[1], 300 + 700 * out_cubic(v), G.P(BLUE, 0.45 * (1 - v), stroke=3))


def badges(c, t):
    for i, (x, y, w, h) in enumerate(CARDS):
        s = pop(t, T_STAMP + 0.06 + 0.035 * i, 0.26, 2.2)
        if s <= 0.01:
            continue
        with G.xf(c, x + w - 40, y + 42, s=s):
            c.drawCircle(0, 0, 16, G.P(BLUE))
            check(c, 0, 0, 17, WHITE, 1.0, stroke=3.2)


# ---------------------------------------------------------------- the scene

def camera(t):
    u = clamp((t - T_DASH) / PULL)
    e = out_quart(u)
    shake = 0.0
    if t >= T_STAMP + 0.12:
        d = t - T_STAMP - 0.12
        shake = 7.0 * math.exp(-d / 0.08) * math.sin(2 * math.pi * 18 * d)
    return 4.2 ** (1 - e), (lerp(960.0, BUTTON_C[0], e), lerp(540.0, BUTTON_C[1], e) + shake)


def dash(c, t):
    z, (cx, cy) = camera(t)
    with G.xf(c, cx, cy, s=z):
        c.translate(-BUTTON_C[0], -BUTTON_C[1])
        grid(c)
        brief(c, t)
        on_duty(c, t)
        power(c, t)
        tasks(c, t)
        safety(c, t)
        today(c, t)
        badges(c, t)
        stamp(c, t)
    u = clamp((t - T_BLACK) / (T_BLACK_FULL + 0.02 - T_BLACK))
    if u > 0:                                                        # his black visor grows to fill it all
        r = 90 + 2400 * in_cubic(u)
        c.drawRRect(rr(AIR_EYES[0] - r * 1.6, AIR_EYES[1] - r * 0.9, r * 3.2, r * 1.8, r * 0.8), G.P("#050507"))
