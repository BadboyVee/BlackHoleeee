"""The launches, each drawn in the teaser's own language: flat discs with typed-glyph eyes, white strokes, the six
colours. Every drawing gets k, the seconds since its launch landed on the beat (the second beat is k = 0.5), and
draws round (0, 0), the middle of the picture."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, in_cubic, in_quad, out_back, in_out_cubic, in_out_sine, hash01
from .look import (F, gsm, mono, rr, pop, hit, WHITE, BLACK, GREY, PURPLE, ORANGE, GREEN, BLUE, DIM, FACES, GOLD, RED,
                   G_BLUE, G_RED, G_YELLOW, G_GREEN, BUN, PATTY, SKY)
from .faces import face, eye, SPARKLE


def text(c, s, x, y, font, col, a=1.0, align=0.5, tracking=0.0):
    if a > 0:
        G.text(c, s, x, y, font, G.P(col, a), align=align, tracking=tracking, anchor="cap")


def sparkle(c, x, y, size, col=WHITE, a=1.0, rot=0.0):
    if size <= 0.5 or a <= 0:
        return
    with G.xf(c, x, y, s=size, rot=rot):
        c.drawPath(SPARKLE, G.P(col, a))


def stroke_path(c, path, col, w, a=1.0, trim=None, cap="round"):
    if trim is not None and trim <= 0.002:
        return
    p = G.P(col, a, stroke=w, cap=cap, join="round")
    if trim is not None and trim < 0.999:
        p.setPathEffect(skia.TrimPathEffect.Make(0.0, trim))
    c.drawPath(path, p)


def arrowhead(c, x, y, ang, size, col, a=1.0):
    """A filled arrowhead pointing along ang (radians)."""
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [(x + ca * size, y + sa * size),
           (x - ca * size * 0.55 - sa * size * 0.75, y - sa * size * 0.55 + ca * size * 0.75),
           (x - ca * size * 0.55 + sa * size * 0.75, y - sa * size * 0.55 - ca * size * 0.75)]
    c.drawPath(G.poly(pts), G.P(col, a))


def reset_icon(c, x, y, r, col, w, rot=0.0, a=1.0):
    """A circular arrow, the reset glyph."""
    with G.xf(c, x, y, rot=rot):
        path = skia.Path()
        path.addArc(skia.Rect.MakeLTRB(-r, -r, r, r), -60, 290)
        stroke_path(c, path, col, w, a, cap="butt")
        ang = math.radians(-60 + 290)
        ex, ey = r * math.cos(ang), r * math.sin(ang)
        arrowhead(c, ex, ey, ang + math.pi / 2, w * 1.35, col, a)


def check(c, x, y, s, col, w, u=1.0, a=1.0):
    path = skia.Path()
    path.moveTo(x - 0.42 * s, y + 0.02 * s)
    path.lineTo(x - 0.12 * s, y + 0.32 * s)
    path.lineTo(x + 0.46 * s, y - 0.3 * s)
    stroke_path(c, path, col, w, a, trim=u)


def badge(c, x, y, r, u, col=GREEN):
    """A green disc with a white tick, popping in with u."""
    s = out_back(clamp(u), 2.4) if u < 1 else 1.0
    if s <= 0:
        return
    with G.xf(c, x, y, s=s):
        c.drawCircle(0, 0, r, G.P(col))
        check(c, 0, 2, r * 1.1, WHITE, r * 0.26, u=clamp(u * 1.6))


def sold(c, k, k0, x=0.0, y=-20.0, rot=-12.0):
    """The SOLD sticker slapped on at k0."""
    u = clamp((k - k0) / 0.1)
    if u <= 0:
        return
    s = lerp(1.9, 1.0, in_cubic(u)) if u < 1 else 1.0 + 0.06 * math.exp(-(k - k0 - 0.1) / 0.06) * math.cos(
        (k - k0) * 60)
    with G.xf(c, x, y, s=s, rot=rot):
        c.drawRRect(rr(-190, -72, 380, 144, 26), G.P(BLACK, 0.35 * u, blur=18))
        c.drawRRect(rr(-180, -66, 360, 132, 24), G.P(WHITE, u))
        c.drawRRect(rr(-166, -52, 332, 104, 16), G.P(RED, u, stroke=6))
        text(c, "SOLD", 4, 0, gsm(92), RED, u, tracking=0.12)


def shake(k, k0, amp=14.0, decay=0.09):
    if k < k0:
        return 0.0, 0.0
    e = math.exp(-(k - k0) / decay) * amp
    return e * math.sin((k - k0) * 90), e * math.cos((k - k0) * 71)


def squash(k, k0, amt=0.16, freq=5.0):
    """(sx, sy) of a landing: a squash that springs back."""
    if k < k0:
        return 1.0, 1.0
    v = amt * math.exp(-(k - k0) * 9) * math.cos((k - k0) * freq * 2 * math.pi)
    return 1 + v, 1 - v


# ---------------------------------------------------------------- 1 Astra 6.1

def astra(c, k):
    tilt, rx, ry = -16.0, 330.0, 96.0
    grow = out_cubic(clamp(k / 0.35))

    def ring(front):
        with G.xf(c, 0, 0, rot=tilt):
            path = skia.Path()
            path.addArc(skia.Rect.MakeLTRB(-rx, -ry, rx, ry), 0 if front else 180, 180 * grow)
            stroke_path(c, path, WHITE, 7, 0.95)
            for j in range(3):
                th = 2 * math.pi * j / 3 + 2.4 * k + 0.6
                if (math.sin(th) > 0) != front:
                    continue
                x, y = rx * math.cos(th), ry * math.sin(th)
                sparkle(c, x, y, (46 + 10 * math.sin(th)) * grow, WHITE, rot=-tilt)

    ring(False)
    sx, sy = squash(k, 0.0, 0.12)
    face(c, 0, 0, 178, BLUE, ("*", "*"), yaw=0.12 * math.sin(2 * math.pi * k), pitch=0.08, sx=sx, sy=sy,
         eye_rot=90 * k)
    ring(True)
    s = pop(k, 0.5, 0.22)
    if s > 0:
        with G.xf(c, 175, -178, s=s, rot=8):
            c.drawRRect(rr(-86, -46, 172, 92, 46), G.P(WHITE))
            text(c, "6.1", 0, 0, gsm(58), BLACK)


# ---------------------------------------------------------------- 2 O

CURSOR = G.poly([(0, 0), (0, 36), (9, 28), (15, 42), (22, 39), (16, 25), (27, 25)])


def agent_o(c, k):
    u = out_cubic(clamp(k / 0.34))
    with G.xf(c, 0, 0, rot=-90 + 40 * k):
        path = skia.Path()
        path.addCircle(0, 0, 238)
        stroke_path(c, path, WHITE, 40, trim=u, cap="butt")
    clicked = k >= 0.5
    sx, sy = squash(k, 0.5, 0.14) if clicked else squash(k, 0.0, 0.1)
    look = lerp(-0.35, 0.3, in_out_cubic(clamp((k - 0.12) / 0.3)))
    face(c, 0, 0, 142, PURPLE, ("^", "^") if clicked else ("o", "o"), yaw=0.0 if clicked else look,
         pitch=0.12 if not clicked else 0.05, sx=sx, sy=sy)
    m = in_out_cubic(clamp((k - 0.1) / 0.36))
    cx, cy = lerp(300, 34, m), lerp(260, 36, m)
    press = 1 - 0.18 * math.exp(-max(0.0, k - 0.5) / 0.05) if clicked else 1.0
    if clicked:
        v = clamp((k - 0.5) / 0.35)
        c.drawCircle(cx, cy, 20 + 110 * out_cubic(v), G.P(WHITE, 0.9 * (1 - v), stroke=6))
    with G.xf(c, cx, cy, s=2.3 * press):
        c.drawPath(CURSOR, G.P(WHITE))
        c.drawPath(CURSOR, G.P(BLACK, 1, stroke=2.2, join="round"))


# ---------------------------------------------------------------- 3 $500 plan

def plan500(c, k):
    for j in range(8):                                   # coins burst out on the second beat
        tau = k - 0.5 - 0.015 * j
        if tau <= 0:
            continue
        vx = (hash01(j, 3) - 0.5) * 1700
        vy = -1150 - 450 * hash01(j, 4)
        x = vx * tau
        y = -80 + vy * tau + 0.5 * 4200 * tau * tau
        spin = abs(math.cos(tau * (14 + 6 * hash01(j, 5))))
        with G.xf(c, x, y, sx=max(spin, 0.15), sy=1.0):
            c.drawCircle(0, 0, 30, G.P("#e39b00"))
            c.drawCircle(0, 0, 24, G.P(GOLD))
            text(c, "$", 0, 0, gsm(34), "#b86f00")
    sx, sy = squash(k, 0.0, 0.14)
    sx2, sy2 = squash(k, 0.5, 0.1)
    face(c, 0, 20, 172, GREEN, ("$", "$"), pitch=0.1, sx=sx * sx2, sy=sy * sy2,
         roll=6 * math.sin(2 * math.pi * 1.5 * k))
    th = 34 * math.exp(-2.6 * k) * math.cos(9.5 * k) + 4 * math.sin(2 * math.pi * k)
    px, py = 128, -120
    with G.xf(c, px, py, rot=th):
        c.drawLine(0, 0, 70, 60, G.P(WHITE, 1, stroke=5, cap="round"))
        with G.xf(c, 70, 60, rot=38):
            tag = skia.Path()
            tag.moveTo(0, 0)
            tag.lineTo(48, -56)
            tag.lineTo(300, -56)
            tag.quadTo(318, -56, 318, -38)
            tag.lineTo(318, 38)
            tag.quadTo(318, 56, 300, 56)
            tag.lineTo(48, 56)
            tag.close()
            c.drawPath(tag, G.P(BLACK, 0.3, blur=12))
            c.drawPath(tag, G.P(WHITE))
            c.drawCircle(40, 0, 10, G.P(BLACK))
            text(c, "$500/mo", 186, 0, gsm(50), BLACK)


# ---------------------------------------------------------------- 4 Aeon

def lemniscate(s, a=300.0):
    d = 1 + math.sin(s) ** 2
    return a * math.cos(s) / d, a * math.sin(s) * math.cos(s) / d * 1.25


def aeon(c, k):
    u = out_cubic(clamp(k / 0.36))
    path = skia.Path()
    for i in range(241):
        x, y = lemniscate(2 * math.pi * i / 240)
        (path.moveTo if i == 0 else path.lineTo)(x, y)
    stroke_path(c, path, WHITE, 24, trim=u)
    s0 = 2 * math.pi * (0.08 + 1.05 * in_out_sine(clamp(k / 1.0)))
    for j in range(7, 0, -1):
        x, y = lemniscate(s0 - 0.13 * j)
        c.drawCircle(x, y, 13 - 1.3 * j, G.P(ORANGE, 0.9 - 0.1 * j))
    x, y = lemniscate(s0)
    x2, y2 = lemniscate(s0 + 0.02)
    roll = math.degrees(math.atan2(y2 - y, x2 - x)) * 0.35
    s = pop(k, 0.0, 0.25)
    face(c, x, y, 88 * s, ORANGE, ("-", "-") if k < 0.5 else ("n", "n"), roll=roll, pitch=0.05)


# ---------------------------------------------------------------- 5 GPT-6.1 Sol

def sol(c, k):
    for j in range(12):
        u = pop(k, 0.02 + 0.018 * j, 0.2)
        if u <= 0:
            continue
        ang = 30 * j + 18 * k
        breathe = 1 + 0.08 * hit(k, 0.5, 0.15)
        with G.xf(c, 0, 0, rot=ang):
            c.drawRRect(rr(212 * breathe, -17, 78 * u, 34, 17), G.P(ORANGE))
    face(c, 0, 0, 176 * (1 + 0.04 * hit(k, 0.5, 0.12)), GOLD, ("^", "^"), pitch=0.08,
         roll=5 * math.sin(2 * math.pi * k))
    u = clamp((k - 0.5) / 0.16)                          # shades drop on the second beat
    if u > 0:
        y = lerp(-420, -6, in_quad(u)) if u < 1 else -6 + 10 * math.exp(-(k - 0.66) * 14) * math.sin((k - 0.66) * 40)
        with G.xf(c, 0, y, rot=-4 * (1 - clamp((k - 0.66) / 0.2))):
            for sx in (-1, 1):
                lens = skia.Path()
                lens.addRRect(rr(sx * 92 - 70, -44, 140, 92, 40))
                c.drawPath(lens, G.P(BLACK))
            c.drawRect(skia.Rect.MakeLTRB(-26, -30, 26, -16), G.P(BLACK))
            c.drawRect(skia.Rect.MakeLTRB(-176, -38, -150, -24), G.P(BLACK))
            c.drawRect(skia.Rect.MakeLTRB(150, -38, 176, -24), G.P(BLACK))
            g = clamp((k - 0.7) / 0.2)
            if 0 < g < 1:
                gx = lerp(-200, 200, g)
                with G.xf(c, 0, 0):
                    clip = skia.Path()
                    clip.addRRect(rr(-162, -44, 140, 92, 40))
                    clip.addRRect(rr(22, -44, 140, 92, 40))
                    c.clipPath(clip, doAntiAlias=True)
                    c.drawLine(gx - 30, 50, gx + 30, -50, G.P(WHITE, 0.8, stroke=14))


# ---------------------------------------------------------------- 6 GPT-6.1 Luna

CRATERS = [(-70, -60, 30), (60, 40, 42), (-30, 90, 22), (95, -80, 18), (-105, 40, 16)]


def luna(c, k):
    for j in range(9):
        a = 2 * math.pi * hash01(j, 11)
        rad = 250 + 90 * hash01(j, 12)
        tw = 0.5 + 0.5 * math.sin(2 * math.pi * (1.4 * k + hash01(j, 13)))
        sparkle(c, rad * math.cos(a) * 1.25, rad * math.sin(a) * 0.9, (14 + 16 * tw) * pop(k, 0.05 * j, 0.2), WHITE,
                0.9)
    roll = 7 * math.sin(2 * math.pi * 0.7 * k)
    r = 180
    with G.xf(c, 0, 0, rot=roll):
        c.drawCircle(0, 0, r, G.P(GREY))
        for x, y, cr in CRATERS:
            c.drawCircle(x, y, cr, G.P("#c8c8c8"))
        face(c, 0, 0, r, GREY, ("-", "-"), pitch=0.02, disc=False)
        e = in_out_sine(clamp((k - 0.1) / 0.8))           # the shadow slides across: full moon to crescent
        with G.xf(c, 0, 0):
            clip = skia.Path()
            clip.addCircle(0, 0, r)
            c.clipPath(clip, doAntiAlias=True)
            c.drawCircle(lerp(r * 2.2, r * 0.62, e), -r * 0.12, r * 1.02, G.P(BLACK, 0.62))
    for j in range(3):
        tau = (k - 0.15 - 0.22 * j)
        if tau <= 0:
            continue
        v = clamp(tau / 0.7)
        x, y = 150 + 70 * j + 30 * v, -170 - 60 * j - 110 * v
        text(c, "z", x, y, gsm(46 + 18 * j), WHITE, (1 - v) * clamp(tau / 0.08))


# ---------------------------------------------------------------- 7 A Codex update? idk

def codex(c, k):
    rise = out_back(clamp((k - 0.46) / 0.16), 1.8) if k > 0.46 else 0.0
    if rise > 0:                                         # a face peeks over the window, none the wiser
        tilt = 12 * math.sin(2 * math.pi * 1.6 * (k - 0.46))
        face(c, 215, lerp(-80, -225, rise), 104, BLUE, ("?", "?"), roll=tilt, pitch=0.18)
    c.drawRRect(rr(-318, -172, 636, 344, 30), G.P("#121212"))
    c.drawRRect(rr(-318, -172, 636, 344, 30), G.P("#3a3a3a", 1, stroke=3))
    for j in range(3):
        c.drawCircle(-282 + 30 * j, -140, 9, G.P("#4a4a4a"))
    f = mono(38, 560)
    cmd = "$ codex update"
    n = int(clamp((k - 0.03) / 0.2) * len(cmd) + 0.5)
    G.text(c, cmd[:n], -270, -60, f, G.P(WHITE))
    if n < len(cmd) or (k % 0.24) < 0.14:
        cx = -270 + f.width(cmd[:n]) + 4
        c.drawRect(skia.Rect.MakeXYWH(cx, -92, 20, 40), G.P(WHITE, 0.9))
    if k > 0.24:
        fill = min(9, int(clamp((k - 0.24) / 0.26) * 9.99))
        for j in range(10):
            col = GREEN if j < fill else "#2c2c2c"
            c.drawRRect(rr(-270 + 42 * j, 0, 34, 34, 7), G.P(col))
        pct = min(99, int(clamp((k - 0.24) / 0.26) * 99))
        G.text(c, f"{pct}%", 170, 30, f, G.P(WHITE))
    if k > 0.56:
        a = clamp((k - 0.56) / 0.06)
        G.text(c, "? idk", -270, 118, f, G.P(DIM, a))


# ---------------------------------------------------------------- 8 Chat + Work merge

def merge(c, k):
    u = in_out_cubic(clamp((k - 0.06) / 0.4))
    r = 140
    if k < 0.46:
        x = lerp(280, 0, u)
        if x < r + 40:                                    # the goo between them as they meet
            v = clamp(1 - (x - r * 0.2) / (r * 0.8 + 40))
            h = r * (0.35 + 0.55 * v)
            bridge = skia.Path()
            bridge.moveTo(-x, -h)
            bridge.quadTo(0, -h * (1 - 0.8 * v) - 6, x, -h)
            bridge.lineTo(x, h)
            bridge.quadTo(0, h * (1 - 0.8 * v) + 6, -x, h)
            bridge.close()
            with G.xf(c, 0, 0):
                c.clipRect(skia.Rect.MakeLTRB(-400, -400, 0, 400))
                c.drawPath(bridge, G.P(GREEN))
            with G.xf(c, 0, 0):
                c.clipRect(skia.Rect.MakeLTRB(0, -400, 400, 400))
                c.drawPath(bridge, G.P(PURPLE))
        sx, sy = squash(k, 0.0, 0.1)
        face(c, -x, 0, r, GREEN, ("o", "o"), yaw=0.4, sx=sx, sy=sy)
        face(c, x, 0, r, PURPLE, ("o", "o"), yaw=-0.4, sx=sx, sy=sy)
        la = 1 - clamp((k - 0.2) / 0.15)
        text(c, "Chat", -x, 222, gsm(52), WHITE, la)
        text(c, "Work", x, 222, gsm(52), WHITE, la)
    else:
        s = 1 + 0.35 * out_back(clamp((k - 0.46) / 0.22), 2.0)
        R2 = r * s
        sx, sy = squash(k, 0.46, 0.18)
        with G.xf(c, 0, 0, sx=sx, sy=sy):
            with G.xf(c, 0, 0):
                c.clipRect(skia.Rect.MakeLTRB(-400, -400, 0, 400))
                c.drawCircle(0, 0, R2, G.P(GREEN))
            with G.xf(c, 0, 0):
                c.clipRect(skia.Rect.MakeLTRB(0, -400, 400, 400))
                c.drawCircle(0, 0, R2, G.P(PURPLE))
            face(c, 0, 0, R2, GREEN, ("^", "^"), pitch=0.08, disc=False)
        for j in range(10):
            v = clamp((k - 0.46) / 0.4)
            ang = 2 * math.pi * j / 10 + 0.3
            d = R2 + 30 + 170 * out_cubic(v)
            eye(c, "+", d * math.cos(ang), d * math.sin(ang), 44, 11, WHITE, 1 - v)


# ---------------------------------------------------------------- 9 OpenAI acquires Google

def google(c, k):
    dx, dy = shake(k, 0.5)
    sx, sy = squash(k, 0.0, 0.12)
    with G.xf(c, dx, dy, sx=sx, sy=sy):
        r = 182
        oval = skia.Rect.MakeLTRB(-r, -r, r, r)
        for start, col in ((180, G_BLUE), (270, G_RED), (0, G_YELLOW), (90, G_GREEN)):
            c.drawArc(oval, start, 90, True, G.P(col))
        eyes = ("o", "o") if k < 0.5 else ("O", "O")
        face(c, 0, 0, r, G_BLUE, eyes, yaw=0.2 * math.sin(2 * math.pi * 2 * k) if k < 0.5 else 0.0, pitch=0.1,
             disc=False)
    sold(c, k, 0.5, 20, 150, -10)


# ---------------------------------------------------------------- 10 OpenAI's first hardware device

def device(c, k):
    u = clamp(k / 0.2)
    y = lerp(-620, 0, in_quad(u))
    sx, sy = squash(k, 0.2, 0.16) if k >= 0.2 else (0.94, 1.06)
    w, h = 300, 360
    glow = clamp((k - 0.5) / 0.08)
    c.drawOval(skia.Rect.MakeXYWH(-170, 150, 340, 60), G.P(WHITE, 0.07 * clamp(k / 0.2), blur=24))
    with G.xf(c, 0, y, sx=sx, sy=sy, py=h / 2):
        body = rr(-w / 2, -h / 2, w, h, 150)
        c.drawRRect(body, G.P("#e9e9e9", 1, shader=G.linear_grad(0, -h / 2, 0, h / 2, ["#fbfbfb", "#cfcfcf"])))
        c.drawOval(skia.Rect.MakeXYWH(-95, -150, 120, 90), G.P(WHITE, 0.7, blur=18))
        if glow > 0:
            v = clamp((k - 0.5) / 0.45)
            for j in range(2):
                vv = clamp(v - 0.18 * j)
                if 0 < vv < 1:
                    c.drawRRect(rr(-w / 2 - 70 * vv, -h / 2 - 70 * vv, w + 140 * vv, h + 140 * vv, 150 + 70 * vv),
                                G.P(SKY, 0.9 * (1 - vv), stroke=8))
            c.drawRRect(body, G.P(SKY, 0.35 * glow * (1 - 0.6 * v), stroke=10, blur=6))
            eyes = ("-", "-") if k < 0.62 else ("o", "o")
            face(c, 0, -10, 150, GREY, eyes, g=0.3, w=0.075, disc=False, a=glow)
    if k > 0.55:                                          # it speaks
        for side in (-1, 1):
            for j in range(3):
                v = clamp((k - 0.55 - 0.08 * j) / 0.3)
                if 0 < v < 1:
                    path = skia.Path()
                    rad = 210 + 40 * j + 30 * v
                    path.addArc(skia.Rect.MakeLTRB(-rad, -rad, rad, rad), (0 if side > 0 else 180) - 28, 56)
                    stroke_path(c, path, WHITE, 10, 1 - v)


# ---------------------------------------------------------------- 11 A bunch of lil new models

LIL = [("o", "o"), ("^", "^"), ("*", "*"), ("-", "-"), ("+", "+"), ("n", "n"), (">", "<")]


def lil(c, k):
    for j in range(6):                                    # notes drift up out of them
        tau = k - 0.08 * j
        if tau <= 0:
            continue
        v = clamp(tau / 0.9)
        x = -330 + 132 * j + 40 * math.sin(tau * 7 + j)
        y = -40 - 380 * v
        f = F("dejavu-sans-bold", 64 + 10 * (j % 3))
        a = clamp(tau / 0.08) * (1 - clamp((v - 0.7) / 0.3))
        G.text(c, "♪" if j % 2 else "♫", x, y, f, G.P(WHITE, a), align=0.5)
    for j, eyes in enumerate(LIL):
        col = FACES[j % len(FACES)]
        r = 62 + 8 * (j % 3)
        ph = (2 * k - j * 0.12) % 1.0                    # a wave along the row, two hops a launch
        hop = math.sin(math.pi * ph)
        y = 150 - 150 * hop
        land = 1 - hop
        sq = 0.18 * max(0.0, land - 0.7) / 0.3
        x = -408 + 136 * j
        s = pop(k, 0.03 * j, 0.22)
        face(c, x, y - r, r * s, col, eyes, sx=1 + sq, sy=1 - sq, roll=12 * math.sin(2 * math.pi * (k + j * 0.2)),
             pitch=0.1)
        if j == 3 and s > 0:                              # the one in headphones
            band = skia.Path()
            band.addArc(skia.Rect.MakeLTRB(x - r * 1.12, y - r - r * 1.15, x + r * 1.12, y - r + r * 1.1), 190, 160)
            stroke_path(c, band, WHITE, 9)
            for side in (-1, 1):
                c.drawRRect(rr(x + side * r * 1.02 - 13, y - r - 18, 26, 44, 12), G.P(WHITE))


# ---------------------------------------------------------------- 12 Sora returns

def cloud(c, x, y, s, col=WHITE):
    with G.xf(c, x, y, s=s):
        for cx, cy, r in ((-46, 8, 40), (0, -18, 54), (48, 6, 42)):
            c.drawCircle(cx, cy, r, G.P(col))
        c.drawRRect(rr(-86, 6, 172, 44, 22), G.P(col))


def sora(c, k):
    u = out_cubic(clamp(k / 0.42))
    with G.xf(c, 0, 0, rot=150 + 70 * k):
        path = skia.Path()
        R = 318
        path.addArc(skia.Rect.MakeLTRB(-R, -R, R, R), 0, 300 * u)
        stroke_path(c, path, WHITE, 26, cap="butt")
        if u > 0.02:
            ang = math.radians(300 * u)
            arrowhead(c, R * math.cos(ang), R * math.sin(ang), ang + math.pi / 2, 38, WHITE)
    flip = out_back(clamp((k - 0.05) / 0.3), 1.6)
    with G.xf(c, 0, 0, sx=max(flip, 0.001), sy=1.0):
        card = rr(-236, -160, 472, 320, 44)
        c.drawRRect(card, G.P(BLUE, 1, shader=G.linear_grad(0, -160, 0, 160, [SKY, PURPLE])))
        with G.xf(c, 0, 0):
            c.clipRRect(card, True)
            bob = 8 * math.sin(2 * math.pi * 1.5 * k)
            cloud(c, -6, -10 + bob, 1.45)
            face(c, -6, -2 + bob, 70, WHITE, ("^", "^"), disc=False, g=0.52, w=0.12)
            prog = clamp((k - 0.2) / 0.8)
            c.drawRRect(rr(-190, 118, 380, 10, 5), G.P(WHITE, 0.35))
            c.drawRRect(rr(-190, 118, 380 * prog, 10, 5), G.P(WHITE))
            c.drawCircle(-190 + 380 * prog, 123, 13, G.P(WHITE))
    s = pop(k, 0.5, 0.2)
    if s > 0:
        with G.xf(c, 0, 0, s=s):
            c.drawCircle(0, 0, 58, G.P(WHITE))
            c.drawPath(G.poly([(-16, -26), (-16, 26), (28, 0)]), G.P(BLACK))


# ---------------------------------------------------------------- 13 Sam Altman humanoid robot

def robot(c, k):
    rise = out_back(clamp(k / 0.24), 1.5)
    y0 = lerp(480, 0, rise)
    with G.xf(c, 0, y0 - 40):
        light = "#bdbdbd"
        for sx in (-1, 1):                                # legs
            c.drawRRect(rr(sx * 55 - 26, 210, 52, 96, 22), G.P(light))
        # the arm that hangs
        c.drawLine(-112, 70, -150, 196, G.P(GREY, 1, stroke=40, cap="round"))
        c.drawCircle(-152, 204, 26, G.P(light))
        # the arm that waves
        wave = -135 + 26 * math.sin(2 * math.pi * 2.0 * k)
        a = math.radians(wave)
        ex, ey = 112 + 150 * math.cos(a), 70 + 150 * math.sin(a)
        c.drawLine(112, 70, ex, ey, G.P(GREY, 1, stroke=40, cap="round"))
        c.drawCircle(ex, ey, 30, G.P(light))
        c.drawRRect(rr(-112, 36, 224, 196, 50), G.P(GREY))
        c.drawRRect(rr(-70, 96, 140, 60, 30), G.P(WHITE))
        text(c, "SAM", 0, 126, gsm(44), BLACK, tracking=0.08)
        c.drawRect(skia.Rect.MakeXYWH(-24, -4, 48, 44), G.P(light))
        blink = hit(k, 0.5, 0.06)
        c.drawLine(0, -196, 0, -250, G.P(light, 1, stroke=10))
        on = 0.35 + 0.65 * max(hit(k, 0.0, 0.2), hit(k, 0.5, 0.2), hit(k, 0.25, 0.1), hit(k, 0.75, 0.1))
        c.drawCircle(0, -258, 20, G.P(ORANGE, 1))
        c.drawCircle(0, -258, 36, G.P(ORANGE, 0.45 * on, blur=14))
        for sx in (-1, 1):
            c.drawRRect(rr(sx * 118 - 14, -128, 28, 64, 12), G.P(light))
        eyes = ("o", "o") if k < 0.5 else ("^", "^")
        face(c, 0, -96, 112, GREY, eyes, pitch=0.06, blink=clamp(blink * 3) if k >= 0.5 else 0.0,
             roll=5 * math.sin(2 * math.pi * k))


# ---------------------------------------------------------------- 14 Greg

def greg(c, k):
    with G.xf(c, 0, -46, s=0.88):
        _greg(c, k)


def _greg(c, k):
    bob = 5 * abs(math.sin(2 * math.pi * 4 * k))
    hood = "#3a3a3a"
    c.drawRRect(rr(-270, 110, 540, 300, 150), G.P(hood))
    c.drawCircle(0, -30 + bob, 196, G.P(hood))
    face(c, 0, -26 + bob, 142, "#1b1b1b", ("^", "^") if k < 0.5 else ("*", "*"), pitch=-0.12, eye_col=WHITE)
    for j in range(16):                                   # code streams out of the laptop, either side of him
        tau = (k * 1.6 + hash01(j, 7)) % 1.0
        col = [GREEN, BLUE, PURPLE, ORANGE][j % 4]
        side = -1 if j % 2 else 1
        x = side * (250 + 110 * hash01(j, 8))
        y = 120 - 470 * tau
        w = 40 + 90 * hash01(j, 9)
        a = clamp(tau / 0.1) * (1 - clamp((tau - 0.6) / 0.4)) * clamp(k / 0.15)
        c.drawRRect(rr(x - w / 2, y - 8, w, 16, 8), G.P(col, a))
    c.drawRRect(rr(-236, 70, 472, 270, 22), G.P(GREY))
    c.drawRRect(rr(-236, 322, 472, 18, 9), G.P("#b8b8b8"))
    c.drawCircle(0, 200, 22, G.P("#c9c9c9"))
    s = pop(k, 0.08, 0.22)
    if s > 0:
        with G.xf(c, 214, -196, s=s, rot=8):
            c.drawRRect(rr(-100, -40, 200, 80, 40), G.P(WHITE))
            text(c, "GREG", 0, 0, gsm(48), BLACK, tracking=0.08)


# ---------------------------------------------------------------- 15 5 banked resets

def resets(c, k):
    full = clamp((k - 0.62) / 0.12)
    col = G.mixc(WHITE, GREEN, full)
    c.drawRRect(rr(-372, -112, 744, 224, 112), G.P(col, 1, stroke=7))
    for j in range(5):
        k0 = 0.04 + 0.095 * j
        u = clamp((k - k0) / 0.2)
        if u <= 0:
            c.drawCircle(-264 + 132 * j, 0, 50, G.P("#1e1e1e"))
            continue
        s = out_back(u, 2.2)
        spin = -360 * (1 - out_cubic(u)) + (-360 * in_out_cubic(clamp((k - 0.66) / 0.3)))
        with G.xf(c, -264 + 132 * j, 0, s=s):
            c.drawCircle(0, 0, 54, G.P(GREEN))
            reset_icon(c, 0, 0, 26, BLACK, 10, rot=spin)
    if full > 0:
        text(c, "×5", 300, -170, gsm(64), GREEN, full)


# ---------------------------------------------------------------- 16 Cancer solved

def cancer(c, k):
    n = 15
    beads = []
    for i in range(n):
        x = -336 + 672 * i / (n - 1)
        ph = 2 * math.pi * (x / 560.0) + 5.2 * k
        for strand in (0, 1):
            p = ph + math.pi * strand
            y = 118 * math.sin(p)
            z = math.cos(p)
            beads.append((z, x, y, strand, i))
        ya, yb = 118 * math.sin(ph), 118 * math.sin(ph + math.pi)
        turn = clamp((k - 0.34 - 0.18 * i / n) / 0.08)
        c.drawLine(x, ya, x, yb, G.P(G.mixc("#5a5a5a", "#1c7a3c", turn), 1, stroke=7))
    beads.sort()
    for z, x, y, strand, i in beads:
        turn = clamp((k - 0.34 - 0.18 * i / n) / 0.08)
        base = PURPLE if strand == 0 else BLUE
        col = G.mixc(base, GREEN, turn)
        r = 17 + 6 * z
        c.drawCircle(x, y, r * pop(k, 0.015 * i, 0.2), G.P(col, 0.55 + 0.45 * (z + 1) / 2))
    u = clamp((k - 0.5) / 0.16)
    if u > 0:
        s = out_back(clamp((k - 0.5) / 0.22), 2.0)
        with G.xf(c, 0, 0, s=s):
            c.drawCircle(0, 0, 120, G.P(GREEN))
            check(c, 0, 4, 160, WHITE, 26, u=u)


# ---------------------------------------------------------------- 17 OpenAI acquires McDonald's

def lettuce_path():
    p = skia.Path()
    p.moveTo(-214, 18)
    for i in range(13):
        x0 = -214 + 428 * i / 12
        p.quadTo(x0 + 428 / 24, -16 if i % 2 == 0 else 22, x0 + 428 / 12, 4)
    p.lineTo(214, 34)
    p.lineTo(-214, 34)
    p.close()
    return p


LETTUCE = lettuce_path()
SESAME = [(-80, -110, 20), (-10, -128, -10), (60, -104, 30), (-120, -62, -30), (110, -60, 15), (20, -80, 5)]


def mcd(c, k):
    def drop(k0, rest_y):
        u = clamp((k - k0) / 0.1)
        if u <= 0:
            return None
        y = lerp(rest_y - 560, rest_y, in_quad(u))
        sx, sy = squash(k, k0 + 0.1, 0.12, 6.0) if u >= 1 else (0.95, 1.05)
        return y, sx, sy

    fs = pop(k, 0.3, 0.22)
    if fs > 0:
        with G.xf(c, 318, 70, s=fs, rot=8):
            for j in range(7):
                c.drawRRect(rr(-66 + 20 * j, -150 + 26 * abs(math.sin(j * 1.7)), 16, 150, 5), G.P(GOLD))
            box = G.poly([(-86, -40), (86, -40), (70, 120), (-70, 120)])
            c.drawPath(box, G.P(RED))
    layers = [
        (0.0, 110, lambda: c.drawRRect(rr(-196, -38, 392, 76, 38), G.P(BUN))),
        (0.06, 52, lambda: c.drawRRect(rr(-208, -32, 416, 64, 30), G.P(PATTY))),
        (0.12, 14, lambda: c.drawPath(G.poly([(-216, -12), (216, -12), (206, 12), (40, 12), (0, 46), (-40, 12),
                                               (-206, 12)]), G.P(GOLD))),
        (0.18, -10, lambda: c.drawPath(LETTUCE, G.P(GREEN))),
    ]
    for k0, ry, draw in layers:
        st = drop(k0, ry)
        if st is None:
            continue
        y, sx, sy = st
        with G.xf(c, 0, y, sx=sx, sy=sy):
            draw()
    st = drop(0.24, -14)
    if st is not None:
        y, sx, sy = st
        with G.xf(c, 0, y, sx=sx, sy=sy):
            dome = skia.Path()
            dome.moveTo(-212, 0)
            dome.cubicTo(-212, -190, 212, -190, 212, 0)
            dome.close()
            c.drawPath(dome, G.P(BUN))
            for x, yy, rot in SESAME:
                with G.xf(c, x, yy, rot=rot):
                    c.drawOval(skia.Rect.MakeXYWH(-9, -5, 18, 10), G.P("#fff4dc"))
            face(c, 0, -30, 150, BUN, ("o", "o") if k < 0.5 else ("O", "O"), disc=False, pitch=0.1, g=0.4)
    sold(c, k, 0.5, -30, -170, 9)


# ---------------------------------------------------------------- 18 Agents escaped again

def escaped(c, k):
    press = hit(k, 0.02, 0.07)
    with G.xf(c, -360, 210):
        c.drawRRect(rr(-80, -56, 160, 124, 24), G.P("#9a9a9a"))
        with G.xf(c, 0, 10 * press):
            c.drawRRect(rr(-80, -66, 160, 118, 24), G.P(WHITE))
            text(c, "esc", 0, -8, gsm(50), BLACK)
    bx, by, bw, bh = -150, -20, 300, 250
    for j in range(8):                                    # they get out
        k0 = 0.16 + 0.05 * j
        tau = k - k0
        if tau <= 0:
            continue
        vx = (hash01(j, 21) - 0.5) * 1700
        vy = -1500 - 600 * hash01(j, 22)
        x = vx * tau
        y = by + vy * tau + 0.5 * 3600 * tau * tau
        r = 36 + 10 * hash01(j, 23)
        col = FACES[j % len(FACES)]
        face(c, x, y, r, col, (">", "<") if j % 2 else ("o", "o"), roll=360 * tau * (1 if vx > 0 else -1) * 0.8,
             pitch=0.1)
    c.drawRRect(rr(bx, by, bw, bh, 18), G.P("#141414"))
    c.drawRRect(rr(bx, by, bw, bh, 18), G.P(WHITE, 1, stroke=10))
    lid = -118 * out_back(clamp((k - 0.08) / 0.14), 2.2)
    with G.xf(c, bx, by, rot=lid):
        c.drawRRect(rr(-6, -12, bw + 12, 24, 12), G.P(WHITE))
    text(c, "sandbox", 0, by + bh / 2, mono(34, 560), DIM)


# ---------------------------------------------------------------- 19 Weather solved

def sun_icon(c, s):
    with G.xf(c, 0, 0, s=s):
        for j in range(8):
            with G.xf(c, 0, 0, rot=45 * j):
                c.drawRRect(rr(40, -7, 22, 14, 7), G.P(GOLD))
        c.drawCircle(0, 0, 32, G.P(GOLD))


def rain_icon(c, s):
    with G.xf(c, 0, 0, s=s):
        cloud(c, 0, -12, 0.62)
        for j in range(3):
            c.drawRRect(rr(-34 + 30 * j, 34, 10, 30, 5), G.P(SKY))


def bolt_icon(c, s):
    with G.xf(c, 0, 0, s=s):
        c.drawPath(G.poly([(8, -58), (-30, 6), (-2, 6), (-14, 58), (30, -10), (2, -10)]), G.P(GOLD))


def snow_icon(c, s):
    eye(c, "*", 0, 0, 96 * s, 12 * s, WHITE)


def weather(c, k):
    icons = [sun_icon, rain_icon, bolt_icon, snow_icon]
    for j, icon in enumerate(icons):
        ang = math.radians(-135 + 90 * j + 50 * k)
        x, y = 285 * math.cos(ang) * 1.1, 250 * math.sin(ang)
        s = pop(k, 0.03 + 0.05 * j, 0.22)
        with G.xf(c, x, y):
            icon(c, s * 1.25)
            badge(c, 50, -46, 24, clamp((k - 0.5 - 0.06 * j) / 0.18))
    sx, sy = squash(k, 0.0, 0.12)
    face(c, 0, 0, 150, BLUE, ("^", "^") if k >= 0.5 else ("o", "o"), pitch=0.08, sx=sx, sy=sy,
         yaw=0.25 * math.sin(2 * math.pi * 1.2 * k) if k < 0.5 else 0.0)


# ---------------------------------------------------------------- the list

LAUNCHES = [
    ("Astra 6.1", BLUE, astra),
    ("Agent “O”", PURPLE, agent_o),
    ("$500 plan", GREEN, plan500),
    ("Aeon", ORANGE, aeon),
    ("GPT-6.1 Sol", ORANGE, sol),
    ("GPT-6.1 Luna", BLUE, luna),
    ("A Codex update? idk", BLUE, codex),
    ("Chat + Work merge", GREEN, merge),
    ("OpenAI acquires Google", G_BLUE, google),
    ("OpenAI’s first hardware device", ORANGE, device),
    ("A bunch of lil new models", PURPLE, lil),
    ("Sora returns", BLUE, sora),
    ("Sam Altman humanoid robot", ORANGE, robot),
    ("Greg", GREEN, greg),
    ("5 banked resets", GREEN, resets),
    ("Cancer solved", GREEN, cancer),
    ("OpenAI acquires McDonald’s", RED, mcd),
    ("Agents escaped again", ORANGE, escaped),
    ("Weather solved", BLUE, weather),
]
