"""VEEE 04, rendered: the camera pulls out of the black button onto the studio's dashboard, where the whole job is
handled. The brief is typed, the tempo counts up to 123 BPM and its dots light on the beats, Vee dances on air,
the cut on every beat is ticked, then the vertical cut, the render farm's chips tick, the frames count up, and
Rendered. is stamped across it all. Then the black spills out of Vee's beanie."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_quart, in_cubic
from .look import (WHITE, INK, BLUE, BLUE_TINT, BLUE_LINE, GREY, LINE, GRIDLINE, sans, mono, italic, T, rr, card,
                   pulse, pop, typed, check, play_icon)
from .dither import Clip, blob
from .mascot import VEE, VEE_FINE, Pose
from .score import (T_DASH, T_TYPE, T_SYNC, T_CHECK1, T_CHECK2, T_CHIPS, T_DONE, T_STAMP, T_BLACK, T_BLACK_FULL,
                    beat)

BRIEF = (100.0, 90.0, 560.0, 900.0)
AIR = (680.0, 90.0, 560.0, 440.0)
TEMPO = (1260.0, 90.0, 560.0, 440.0)
CUTS = (680.0, 550.0, 560.0, 440.0)
DELIVERY = (1260.0, 550.0, 560.0, 210.0)
RENDER = (1260.0, 780.0, 560.0, 210.0)
CARDS = [BRIEF, AIR, TEMPO, CUTS, DELIVERY, RENDER]
BUTTON = (128.0, 356.0, 504.0, 80.0)
BUTTON_C = (BUTTON[0] + BUTTON[2] / 2, BUTTON[1] + BUTTON[3] / 2)
PULL = 0.5                                          # how long the camera takes to pull out
T_R0 = 7.90                                         # the render starts
T_COUNT = (7.45, 8.20)                              # the tempo counts up
BRIEF_TEXT = "a 15 s spot, on the beat"
CUT_THUMB = Clip("devday", 15.6, 114, 114, invert=True, rect=(90, 290, 540, 540))


def label(c, s, x, y):
    T(c, s, x, y, mono(22), GREY)


def grid(c):
    p = G.P(GRIDLINE, 1, stroke=1.5)
    for x in (100, 660, 680, 1240, 1260, 1820):
        c.drawLine(x, -2000, x, 3000, p)
    for y in (90, 530, 550, 760, 780, 990):
        c.drawLine(-3000, y, 5000, y, p)


def frames_done(t):
    """Frames rendered by t: the spot's 900, then the vertical cut's 900 once it is ticked."""
    return (900 * clamp((t - T_R0) / (T_CHECK2 - T_R0)) +
            900 * clamp((t - T_CHECK2) / (T_DONE - T_CHECK2)))


def total(t):
    return 1800 if t >= T_CHECK2 else 900


# ---------------------------------------------------------------- the brief

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
    label(c, "// brief", 128, 140)
    c.drawRRect(rr(128, 170, 120, 120, 18), G.P(WHITE))
    c.save()
    c.clipRRect(rr(128, 170, 120, 120, 18), True)
    VEE_FINE(c, 188, 236, 0.25, Pose(look=(5.0, 2.0), blink=pulse(t, 8.9, 9.0, 0.03)))   # the spot's star
    c.restore()
    c.drawRRect(rr(128.5, 170.5, 119, 119, 18), G.P(LINE, 1, stroke=1.4))
    T(c, "Launch spot", 275, 222, sans(36, 560), INK, tracking=-0.01)
    T(c, "15.0 s", 632, 222, mono(30, 500), INK, align=1.0)
    T(c, "made to your track", 275, 262, mono(22), GREY)
    c.drawLine(128, 321, 632, 321, G.P(LINE, 1, stroke=1.5))
    # the black button the camera came out of
    bx, by, bw, bh = BUTTON
    c.drawRRect(rr(bx, by, bw, bh, 14), G.P(INK))
    f = sans(32, 560)
    tw = f.width("Make it move")
    play_icon(c, BUTTON_C[0] - tw / 2 - 16, BUTTON_C[1], 20, WHITE)
    T(c, "Make it move", BUTTON_C[0] + 16, BUTTON_C[1] + 11, f, WHITE, align=0.5)
    # or send a brief
    fm = mono(22)
    ow = fm.width("or send a brief")
    c.drawLine(128, 482, 380 - ow / 2 - 16, 482, G.P(LINE, 1, stroke=1.5))
    c.drawLine(380 + ow / 2 + 16, 482, 632, 482, G.P(LINE, 1, stroke=1.5))
    T(c, "or send a brief", 380, 490, fm, GREY, align=0.5)
    focus = clamp((t - (T_TYPE - 0.1)) / 0.12) * (1 - clamp((t - 8.75) / 0.2))
    if focus > 0:
        c.drawRRect(rr(124, 514, 512, 84, 15), G.P(BLUE_LINE, focus, stroke=5))
    c.drawRRect(rr(128, 518, 504, 76, 12), G.P(WHITE))
    c.drawRRect(rr(128.5, 518.5, 503, 75, 12), G.P(G.mixc(LINE, BLUE, focus), 1, stroke=1.5 + focus))
    s = typed(BRIEF_TEXT, t, T_TYPE, 28)
    run = T(c, s, 152, 566, mono(26), INK)
    if focus > 0.5 and (t * 2.0) % 1.0 < 0.6:
        cx = 152 + (run.width if run else 0) + 4
        c.drawLine(cx, 540, cx, 574, G.P(BLUE, 1, stroke=2.5))
    # the rows
    T(c, "Resolution", 128, 640, sans(26, 450), INK)
    T(c, "1920 × 1080", 632, 640, mono(26, 500), INK, align=1.0)
    tint_row(c, t, T_CHECK1, 684, "Cuts on the beat", "+24")
    tint_row(c, t, T_SYNC, 728, "Sound · 123 BPM", "synced")
    c.drawLine(128, 761, 632, 761, G.P(LINE, 1, stroke=1.5))
    T(c, "Frames", 128, 808, sans(34, 600), INK)
    k = clamp((t - T_CHECK2) / 0.2)
    T(c, "900", 632, 808 - 14 * out_cubic(k), mono(34, 600), INK, 1 - k, align=1.0)
    T(c, "1,800", 632, 822 - 14 * out_cubic(k), mono(34, 600), INK, k, align=1.0)
    # the render button
    c.drawRRect(rr(128, 850, 504, 90, 14), G.P(BLUE))
    fb = sans(32, 560)
    done = clamp((t - T_STAMP) / 0.12)
    if done < 1:
        n = "1,800" if t >= T_CHECK2 else "900"
        T(c, f"Render {n} frames", 380, 906, fb, WHITE, 1 - done, align=0.5)
    if done > 0:
        wd = fb.width("Done")
        check(c, 380 - wd / 2 - 8, 894, 30, WHITE, done, stroke=4.5)
        T(c, "Done", 380 + 22, 906, fb, WHITE, done, align=0.5)


# ---------------------------------------------------------------- on air

def on_air(c, t):
    x, y, w, h = AIR
    card(c, x, y, w, h, r=24, shadow=0.03)
    ph = (t - T_DASH) / 0.4865
    c.drawCircle(716, 133, 6, G.P(BLUE, 0.55 + 0.45 * math.exp(-(ph % 1.0) * 2.5)))
    label(c, "// on air", 732, 140)
    c.save()
    c.clipRRect(rr(x + 1, y + 1, w - 2, h - 2, 23), True)
    side = 1 if int(ph) % 2 == 0 else -1               # he dances: a lean to one side on each beat
    lean = side * 5.0 * (1 - math.exp(-(ph % 1.0) * 5))
    bob = 7.0 * math.exp(-(ph % 1.0) * 4)
    look = (4.0, 2.0)
    look = (lerp(look[0], -12.0, pulse(t, T_CHECK1 - 0.3, T_CHECK1 + 0.35, 0.08)),
            lerp(look[1], 9.0, pulse(t, T_CHECK1 - 0.3, T_CHECK1 + 0.35, 0.08)))
    pose = Pose(look=look, tilt=lean, blink=pulse(t, 9.3, 9.4, 0.03), wink=pulse(t, T_STAMP + 0.05, T_STAMP + 0.3, 0.04),
                talk=pulse(t, T_CHECK2, T_CHECK2 + 0.12, 0.03))
    VEE(c, 960, 336 + bob, 0.64, pose)
    c.restore()


# ---------------------------------------------------------------- tempo

DOTS_X = [1303 + k * (1776 - 1303) / 7 for k in range(8)]


def metronome(c, t, x, y):
    body = skia.Path()
    body.moveTo(x - 15, y + 17)
    body.lineTo(x - 7, y - 17)
    body.lineTo(x + 7, y - 17)
    body.lineTo(x + 15, y + 17)
    body.close()
    c.drawPath(body, G.P(INK, 1, stroke=3.5, join="round"))
    th = math.radians(28) * math.cos(math.pi * (t - T_DASH) / 0.4865)
    c.drawLine(x, y + 10, x + 22 * math.sin(th), y + 10 - 22 * math.cos(th), G.P(INK, 1, stroke=3.5, cap="round"))


def tempo(c, t):
    x, y, w, h = TEMPO
    card(c, x, y, w, h, r=24, shadow=0.03)
    label(c, "// tempo", 1288, 140)
    m = 1 - pop(t, T_STAMP + 0.06 + 0.035 * 2, 0.26, 2.2)       # its badge takes the metronome's place
    if m > 0.01:
        with G.xf(c, 1774, 134, s=m):
            metronome(c, t, 0, 0)
    u = clamp((t - T_COUNT[0]) / (T_COUNT[1] - T_COUNT[0]))
    n = int(round(123 * out_cubic(u)))
    fb = F_BIG
    G.text(c, f"{n}", 1286, 345, fb, G.P(INK), features={"tnum": True})
    T(c, "BPM", 1286 + fb.width("123", features={"tnum": True}) + 22, 345, sans(46, 450), GREY)
    y0 = 440
    c.drawLine(DOTS_X[0], y0, DOTS_X[-1], y0, G.P(LINE, 1, stroke=3))
    lit = -1
    for k in range(8):
        if t >= beat(14 + k):
            lit = k
    if lit >= 0:                                     # the line runs on to the next dot through each beat
        xe = DOTS_X[lit]
        if lit < 7:
            xe += (DOTS_X[lit + 1] - DOTS_X[lit]) * clamp((t - beat(14 + lit)) / 0.4865)
        c.drawLine(DOTS_X[0], y0, xe, y0, G.P(BLUE, 1, stroke=3))
    for k in range(8):
        on = k <= lit
        r = 11.0
        if on:
            r += 7.0 * math.exp(-max(0.0, t - beat(14 + k)) / 0.1)
            c.drawCircle(DOTS_X[k], y0, r, G.P(BLUE))
        else:
            c.drawCircle(DOTS_X[k], y0, r, G.P(WHITE))
            c.drawCircle(DOTS_X[k], y0, r, G.P("#cfcfcf", 1, stroke=2))
        T(c, str(k % 4 + 1), DOTS_X[k], 486, mono(20), GREY, align=0.5)


F_BIG = sans(190, 600)


# ---------------------------------------------------------------- cuts

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


def cuts(c, t):
    x, y, w, h = CUTS
    card(c, x, y, w, h, r=24, shadow=0.03)
    label(c, "// cuts", 708, 600)
    option(c, t, (708, 634, 504, 150), T_CHECK1)
    c.drawRRect(rr(726, 652, 114, 114, 12), G.P(WHITE))
    c.save()
    c.clipRRect(rr(726, 652, 114, 114, 12), True)
    CUT_THUMB.draw(c, 726, 652)
    c.restore()
    c.drawRRect(rr(726.5, 652.5, 113, 113, 12), G.P(LINE, 1, stroke=1.2))
    T(c, "Cut on every beat", 860, 696, sans(32, 560), INK, tracking=-0.01)
    T(c, "24 cuts, one track", 860, 731, sans(23, 450), GREY)
    T(c, "+24", 860, 767, sans(30, 600), BLUE)
    checkbox(c, 1152, 690, T_CHECK1, t)
    option(c, t, (708, 804, 504, 110), T_CHECK2)
    c.drawRRect(rr(726, 822, 74, 74, 12), G.P("#f3f3f3"))
    T(c, "9:16", 763, 867, mono(22, 500), INK, align=0.5)
    T(c, "Vertical cut", 820, 853, sans(30, 560), INK, tracking=-0.01)
    T(c, "+1 film", 820, 888, sans(23, 450), GREY)
    checkbox(c, 1152, 840, T_CHECK2, t)


# ---------------------------------------------------------------- delivery and render

CHIPS = ["1080p", "60 fps", "MP4"]


def delivery(c, t):
    x, y, w, h = DELIVERY
    card(c, x, y, w, h, r=24, shadow=0.03)
    label(c, "// delivery", 1288, 600)
    T(c, "We are your render farm.", 1288, 650, sans(30, 500), INK, tracking=-0.01)
    f = mono(24, 500)
    cx = 1290.0
    for i, s in enumerate(CHIPS):
        cw = f.width(s) + 70
        c.drawRRect(rr(cx, 680, cw, 50, 25), G.P(WHITE))
        c.drawRRect(rr(cx + 0.5, 680.5, cw - 1, 49, 25), G.P(LINE, 1, stroke=1.5))
        T(c, s, cx + 20, 713, f, INK)
        check(c, cx + cw - 28, 705, 20, BLUE, clamp((t - (T_CHIPS + 0.14 * i)) / 0.16), stroke=3.5)
        cx += cw + 12


def render_card(c, t):
    x, y, w, h = RENDER
    card(c, x, y, w, h, r=24, shadow=0.03)
    label(c, "// render", 1288, 830)
    T(c, "4 cores · 60 fps", 1738, 830, mono(21), GREY, align=1.0)
    n = int(frames_done(t))
    run = G.text(c, f"{n:,}", 1288, 902, mono(46, 500), G.P(INK), features={"tnum": True})
    T(c, f"/ {total(t):,} frames", 1288 + run.width + 14, 902, mono(24), GREY)
    k = n / total(t)
    c.drawRRect(rr(1288, 930, 504, 12, 6), G.P("#efefef"))
    if k > 0:
        c.drawRRect(rr(1288, 930, max(12.0, 504 * k), 12, 6), G.P(BLUE))
    d = clamp((t - T_DONE) / 0.16)
    if d > 0:
        check(c, 1700, 893, 24, BLUE, d, stroke=4)
        T(c, "done", 1792, 902, mono(24, 500), BLUE, d, align=1.0)


# ---------------------------------------------------------------- Rendered.

STAMP_C = (980.0, 700.0)


def stamp(c, t):
    u = clamp((t - T_STAMP) / 0.13)
    if u <= 0:
        return
    s = lerp(3.4, 1.0, out_cubic(u))
    f = italic(150)
    tw = f.width("Rendered.")
    w, h = tw + 84, 176.0
    with G.xf(c, STAMP_C[0], STAMP_C[1], s=s, rot=-7.0):
        with G.layer(c, lerp(0.35, 1.0, u)):
            c.drawRRect(rr(-w / 2, -h / 2, w, h, 26), G.P("#eef3fd", 0.9))
            c.drawRRect(rr(-w / 2, -h / 2, w, h, 26), G.P(BLUE, 1, stroke=6))
            c.drawRRect(rr(-w / 2 + 12, -h / 2 + 12, w - 24, h - 24, 18), G.P(BLUE, 0.35, stroke=2))
            T(c, "Rendered.", 0, 50, f, BLUE, align=0.5)
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
    if t >= T_STAMP + 0.12:                          # the stamp lands with a thud
        d = t - T_STAMP - 0.12
        shake = 7.0 * math.exp(-d / 0.08) * math.sin(2 * math.pi * 18 * d)
    return 4.2 ** (1 - e), (lerp(960.0, BUTTON_C[0], e), lerp(540.0, BUTTON_C[1], e) + shake)


def dash(c, t):
    z, (cx, cy) = camera(t)
    with G.xf(c, cx, cy, s=z):
        c.translate(-BUTTON_C[0], -BUTTON_C[1])
        grid(c)
        brief(c, t)
        on_air(c, t)
        tempo(c, t)
        cuts(c, t)
        delivery(c, t)
        render_card(c, t)
        badges(c, t)
        stamp(c, t)
    u = clamp((t - T_BLACK) / (T_BLACK_FULL + 0.02 - T_BLACK))
    if u > 0:                                        # the black spills out of his beanie
        blob(c, 960, 250, 40 + 2400 * in_cubic(u), 170, INK)
