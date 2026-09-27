"""The intro: a flat-lay kitchen table in light green. Props drop onto it on the sixteenths, the headline types
itself in big white letters (Anniversary dinner / means choosing / A lot.), fruit keeps landing until the table
is crowded, then a white card drops in the middle and becomes the phone's input box."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, out_back, in_out_cubic, spring, hash01
from .look import ui, rr, WHITE, LIGHT_GREEN, GROUND, SHADOW, glow_rrect, ground
from .score import T_NAME, T_WIPE, CX

TABLE = LIGHT_GREEN
INPUT = (368, 388, 1184, 318, 46)
T_DROP = 3.0          # the white card lands


# ---------------------------------------------------------------- props, drawn top-down, centred on (0, 0)

def _grad(x0, y0, x1, y1, cols):
    return G.linear_grad(x0, y0, x1, y1, cols)


def bread(c):
    body = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-165, -98, 330, 196), 96, 96)
    c.drawRRect(body, G.P("#b8622a", 1, shader=G.radial_grad(-30, -30, 240, ["#f0a55a", "#c46a2c", "#8a3c16"],
                                                             stops=[0.0, 0.6, 1.0])))
    for x in (-78, 0, 78):
        p = skia.Path()
        p.moveTo(x - 18, -78)
        p.quadTo(x + 14, 0, x - 10, 78)
        c.drawPath(p, G.P("#f7cf8f", 0.95, stroke=18, cap="round"))
        c.drawPath(p, G.P("#fff0cc", 0.7, stroke=6, cap="round"))
    G.circle(c, -60, -52, 26, G.P("#ffffff", 0.35, blur=10))


def banana(c):
    p = skia.Path()
    p.moveTo(-160, 10)
    p.quadTo(0, -120, 158, -8)
    p.lineTo(166, 8)
    p.quadTo(0, -62, -150, 34)
    p.close()
    c.drawPath(p, G.P("#f2c230", 1, shader=_grad(0, -80, 0, 30, ["#f9d949", "#e5a820"])))
    q = skia.Path()
    q.moveTo(-140, 12)
    q.quadTo(0, -90, 150, 0)
    c.drawPath(q, G.P("#c98d18", 0.6, stroke=3))
    G.circle(c, 160, 0, 10, G.P("#5a3d1a"))
    G.circle(c, -155, 22, 8, G.P("#3a2a14"))


GILT = ["#f3dc9a", "#e3b54f", "#b8872a"]


def fork(c):
    c.drawRRect(rr(-9, -10, 18, 190, 9), G.P(GILT[1], 1, shader=_grad(-9, 0, 9, 0, GILT)))
    c.drawRRect(rr(-26, -70, 52, 70, 16), G.P(GILT[1], 1, shader=_grad(-26, 0, 26, 0, GILT)))
    for x in (-18, 0, 18):
        c.drawRRect(rr(x - 6, -118, 12, 60, 6), G.P(GILT[1], 1, shader=_grad(x - 6, 0, x + 6, 0, GILT)))


def spoon(c):
    c.drawRRect(rr(-9, -10, 18, 180, 9), G.P(GILT[1], 1, shader=_grad(-9, 0, 9, 0, GILT)))
    c.drawOval(skia.Rect.MakeXYWH(-36, -110, 72, 100), G.P(GILT[1], 1, shader=_grad(-36, 0, 36, 0, GILT)))
    c.drawOval(skia.Rect.MakeXYWH(-24, -96, 48, 72), G.P("#b8872a", 0.35))


def board(c):
    c.drawRRect(rr(-190, -250, 380, 420, 60), G.P("#ecd3a4", 1, shader=_grad(-190, -250, 190, 170,
                                                                            ["#f3e0b8", "#e2c38c"])))
    c.drawRRect(rr(-70, 150, 140, 120, 40), G.P("#e6c890"))
    G.circle(c, 0, 215, 22, G.P(TABLE))
    for k in range(7):
        y = -210 + k * 55
        p = skia.Path()
        p.moveTo(-160, y)
        p.cubicTo(-60, y + 12, 60, y - 12, 160, y + 4)
        c.drawPath(p, G.P("#cfae74", 0.35, stroke=2))


def knife(c):
    blade = skia.Path()
    blade.moveTo(-20, -210)
    blade.quadTo(40, -120, 34, 30)
    blade.lineTo(-22, 30)
    blade.close()
    c.drawPath(blade, G.P("#cfd4d9", 1, shader=_grad(-22, 0, 34, 0, ["#f4f6f8", "#aeb5bc", "#e6e9ec"])))
    c.drawLine(28, -60, 32, 26, G.P("#ffffff", 0.8, stroke=3))
    c.drawRRect(rr(-26, 26, 52, 150, 16), G.P("#151515", 1, shader=_grad(-26, 0, 26, 0, ["#2a2a2a", "#0d0d0d"])))
    for y in (60, 100, 140):
        G.circle(c, 0, y, 6, G.P("#d9dde1"))


def whisk(c):
    c.drawRRect(rr(-150, -12, 150, 24, 12), G.P("#c7cdd3", 1, shader=_grad(0, -12, 0, 12, ["#eef1f3", "#9aa2aa"])))
    for k in range(6):
        h = 12 + k * 9
        c.drawOval(skia.Rect.MakeXYWH(-10, -h, 190, 2 * h), G.P("#b9c0c7", 0.9, stroke=3))


def server(c):
    c.drawRRect(rr(-10, -20, 20, 200, 10), G.P("#c7cdd3", 1, shader=_grad(-10, 0, 10, 0, ["#eef1f3", "#8f979f"])))
    head = skia.Path()
    head.addOval(skia.Rect.MakeXYWH(-46, -120, 92, 110))
    c.drawPath(head, G.P("#c7cdd3", 1, shader=_grad(-46, 0, 46, 0, ["#f0f3f5", "#9aa2aa"])))
    G.circle(c, 0, -65, 12, G.P(TABLE))
    for k in range(7):
        x = -36 + k * 12
        c.drawRRect(rr(x - 4, -134, 8, 20, 4), G.P("#b3bac1"))


def apple(c, green=False):
    col = ["#f05a5a", "#c62432", "#7d121c"] if not green else ["#d8f07a", "#9ccc3a", "#5f8f1f"]
    c.drawCircle(0, 0, 48, G.P(col[1], 1, shader=G.radial_grad(-14, -16, 64, col, stops=[0.0, 0.55, 1.0])))
    G.circle(c, -16, -18, 12, G.P("#ffffff", 0.45, blur=5))
    c.drawLine(0, -40, 4, -58, G.P("#5a3a1a", 1, stroke=5, cap="round"))
    leaf = skia.Path()
    leaf.addOval(skia.Rect.MakeXYWH(6, -64, 28, 12))
    c.drawPath(leaf, G.P("#4f9a2a"))


def orange_half(c):
    G.circle(c, 0, 0, 50, G.P("#f28c28"))
    G.circle(c, 0, 0, 42, G.P("#ffe0a0"))
    G.circle(c, 0, 0, 38, G.P("#ffab3d"))
    for k in range(9):
        a = 2 * math.pi * k / 9
        c.drawLine(0, 0, 38 * math.cos(a), 38 * math.sin(a), G.P("#ffe8c0", 0.8, stroke=2.2))
    G.circle(c, 0, 0, 6, G.P("#fff2d6"))


def strawberry(c):
    p = skia.Path()
    p.moveTo(0, 42)
    p.cubicTo(-46, 10, -40, -34, 0, -30)
    p.cubicTo(40, -34, 46, 10, 0, 42)
    c.drawPath(p, G.P("#e2283a", 1, shader=G.radial_grad(-10, -10, 60, ["#ff5a66", "#c2142a"])))
    for k in range(10):
        x = -20 + 40 * float(hash01(k, 1))
        y = -18 + 44 * float(hash01(k, 2))
        G.circle(c, x, y, 2.2, G.P("#ffd76a"))
    c.drawPath(G.poly(G.star_points(5, 22, 8, cx=0, cy=-32)), G.P("#3f8f2a"))


def chili(c):
    p = skia.Path()
    p.moveTo(-70, 0)
    p.cubicTo(-30, -26, 40, -24, 76, 6)
    p.cubicTo(40, -6, -30, 4, -70, 0)
    c.drawPath(p, G.P("#d7261e", 1, stroke=18, cap="round", join="round"))
    c.drawLine(-70, 0, -92, -10, G.P("#3f8f2a", 1, stroke=8, cap="round"))


def bean(c):
    p = skia.Path()
    p.moveTo(-80, 0)
    p.cubicTo(-30, -18, 30, 18, 80, 0)
    c.drawPath(p, G.P("#5aa33c", 1, stroke=13, cap="round"))
    c.drawPath(p, G.P("#9ad26a", 0.8, stroke=3, cap="round"))


def tomato(c):
    c.drawCircle(0, 0, 40, G.P("#e8413a", 1, shader=G.radial_grad(-12, -12, 52, ["#ff7a6a", "#d4261e"])))
    c.drawPath(G.poly(G.star_points(5, 20, 7, cx=0, cy=0)), G.P("#3f8f2a"))


# (draw function, x, y, rotation, scale, lands at)
PROPS = [
    (bread, 170, 150, -14, 1.0, 0.0),
    (banana, 1760, 90, 12, 1.0, 0.125),
    (fork, 830, 190, 8, 1.0, 0.25),
    (spoon, 470, 330, -62, 1.0, 0.25),
    (board, 1650, 560, 32, 1.0, 0.375),
    (spoon, 1150, 340, 84, 1.0, 0.5),
    (knife, 1560, 820, -36, 1.0, 0.5),
    (banana, 60, 560, 78, 0.95, 0.625),
    (whisk, 380, 1010, -6, 1.0, 0.75),
    (server, 1130, 880, 24, 1.0, 0.875),
]
METAL = (fork, spoon, knife, whisk, server)
FRUIT = [(apple, 900, 660), (orange_half, 1690, 420), (strawberry, 700, 300), (chili, 560, 590), (tomato, 1210, 700),
         (bean, 1010, 210), (apple, 250, 880), (strawberry, 1480, 700), (orange_half, 620, 830), (chili, 1320, 520),
         (bean, 760, 960), (tomato, 430, 720), (apple, 1360, 240), (strawberry, 1050, 1000), (orange_half, 300, 420)]


def fruit_time(k):
    """The fruit keeps coming: slowly at first, then on every sixteenth when the headline says 'A lot.'"""
    if k < 5:
        return 1.0 + 0.25 * k
    return T_NAME + 0.125 * (k - 5)


def draw_fruit(c, k, fn, x, y, t, scatter):
    tk = fruit_time(k)
    if t < tk:
        return
    s = spring(t - tk, 3.2, 0.45)
    rot = float(hash01(k, 9)) * 360
    dx, dy = scatter(x, y)
    with G.layer(c, alpha=0.3, blur=8):
        with G.xf(c, x + dx + 8, y + dy + 12, rot=rot, s=max(0.0, s)):
            with G.layer(c):
                _call(fn, c, k)
                c.drawPaint(G.P(SHADOW, 1, blend=skia.BlendMode.kSrcIn))
    with G.xf(c, x + dx, y + dy, rot=rot, s=max(0.0, s)):
        _call(fn, c, k)


def _call(fn, c, k):
    if fn is apple:
        fn(c, green=(k % 3 == 1))
    else:
        fn(c)


def draw_prop(c, fn, x, y, rot, sc, tl, t, scatter):
    """A prop drops onto the table: bigger and higher with a loose shadow, then it lands and settles."""
    if t < tl - 0.2:
        return
    u = clamp((t - (tl - 0.2)) / 0.26)
    e = out_back(u, 1.6) if u < 1 else 1.0
    lift = 1 - clamp(u)
    s = sc * (1 + 0.25 * lift)
    dx, dy = scatter(x, y)
    off = 10 + 40 * lift
    with G.layer(c, alpha=0.32 * clamp(u * 2), blur=10 + 16 * lift):
        with G.xf(c, x + dx + off * 0.6, y + dy + off, rot=rot, s=s):
            _mono(c, fn)
    with G.layer(c, alpha=clamp(u * 3)):
        with G.xf(c, x + dx, y + dy - 30 * lift, rot=rot + 12 * lift, s=s * (0.95 + 0.05 * e)):
            fn(c)


def _mono(c, fn):
    """A prop's silhouette, for its shadow."""
    with G.layer(c, blend=None):
        fn(c)
        c.drawPaint(G.P(SHADOW, 1, blend=skia.BlendMode.kSrcIn))


# ---------------------------------------------------------------- the headline

PHRASES = [("Anniversary dinner", 0.2, 1.05, 132), ("means choosing", 1.12, 1.85, 132),
           ("A lot.", T_NAME, T_DROP, 230)]
STAGGER, OUT = 0.02, 0.15


def headline(c, t):
    for text, t0, t1, size in PHRASES:
        if not (t0 <= t < t1 + OUT):
            continue
        f = ui(size, 800)
        run = f.shape(text, -0.01)
        x0 = CX - run.width / 2
        y = 575 if size < 200 else 610
        out = clamp((t - t1) / OUT)
        for i, gid, gx, adv in run.glyphs():
            u = clamp((t - t0 - STAGGER * i) / 0.18)
            if u <= 0:
                continue
            e = out_back(u, 2.0)
            a = u * (1 - out)
            punch = 1.0
            if size >= 200:
                punch = 1 + 0.35 * math.exp(-(t - t0) / 0.08)
            with G.xf(c, x0 + gx + adv / 2, y, s=(0.5 + 0.5 * e) * punch):
                G.glyph(c, f, gid, -adv / 2, 12 - 40 * out, G.P(SHADOW, 0.42 * a, blur=16))
                G.glyph(c, f, gid, -adv / 2, 4 - 40 * out, G.P(SHADOW, 0.28 * a, blur=3))
                G.glyph(c, f, gid, -adv / 2, -40 * out, G.P(WHITE, a))


# ---------------------------------------------------------------- the table

def table(c, t):
    """Everything on the table, and the way out: the card lands, the props fly off, the card stays."""
    m = in_out_cubic(clamp((t - T_WIPE[0]) / (T_WIPE[1] - T_WIPE[0])))
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P(TABLE))
    c.drawCircle(CX, 540, 1250, G.P(TABLE, 1, shader=G.radial_grad(CX, 540, 1250, GROUND, stops=[0.0, 0.55, 1.0])))
    zoom = 1.0 + 0.05 * clamp(t / 3.4)

    def scatter(x, y):
        # on the way out every prop flies away from the centre
        if m <= 0:
            return 0.0, 0.0
        dx, dy = x - CX, y - 540
        d = math.hypot(dx, dy) + 1e-6
        return dx / d * 1400 * m * m, dy / d * 1400 * m * m

    c.save()
    c.translate(CX, 540)
    c.scale(zoom, zoom)
    c.translate(-CX, -540)
    for fn, x, y, rot, sc, tl in PROPS:
        draw_prop(c, fn, x, y, rot, sc, tl, t, scatter)
    for k, (fn, x, y) in enumerate(FRUIT):
        draw_fruit(c, k, fn, x, y, t, scatter)
    c.restore()
    if m < 1:
        with G.layer(c, alpha=1 - m):
            headline(c, t)
    # the white card drops onto the table where the phone's input box will be
    ix, iy, iw, ih, ir = INPUT
    if t >= T_DROP:
        u = clamp((t - T_DROP) / 0.3)
        e = out_back(u, 1.3) if u < 1 else 1.0
        s = 1.35 - 0.35 * e
        with G.xf(c, ix + iw / 2, iy + ih / 2, s=s):
            c.translate(-(ix + iw / 2), -(iy + ih / 2))
            a = clamp(u * 6)
            c.drawRRect(rr(ix + 14, iy + 30 * (1 - e) + 26, iw, ih, ir), G.P(SHADOW, 0.3 * a, blur=24 + 20 * (1 - e)))
            glow_rrect(c, ix, iy, iw, ih, ir, t, a=a, spread=30, width=22, speed=50)
            c.drawRRect(rr(ix, iy, iw, ih, ir), G.P(WHITE, a))
    # the props fly off and the ground of the app settles in behind them
    if m > 0:
        with G.layer(c, alpha=m):
            ground(c, t)
            ix, iy, iw, ih, ir = INPUT
            glow_rrect(c, ix, iy, iw, ih, ir, t, a=1.0, spread=30, width=22, speed=50)
            c.drawRRect(rr(ix, iy, iw, ih, ir), G.P(WHITE))
