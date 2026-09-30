"""HORIZON 4, the end. On white, "Stay ahead of the race." in a crosshair; on black, "Right from your", and a
phone rising out of the hills with its alerts: "pocket". Then the name over the hills, the mark built over them,
and the mark alone on black, with the small print: a concept, predictions not news, made by VEEE."""
import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_quart, in_cubic, out_back
from .look import WHITE, INK, sans, T, rr, blur_in, blur_out, hairline
from . import plates, marks, devices, sky
from .score import T_CROSS, T_POCKET, T_POCKET_IMG, T_NAME, T_MARK, T_BLACK, T_NOTE, DURATION

# ---------------------------------------------------------------- the crosshair

def crosshair(c, t):
    tau = t - T_CROSS
    u = out_cubic(clamp(tau / 0.5))
    col = "#c6cad3"
    gap_x, gap_y = 210.0, 130.0
    hairline(c, 0, 544, lerp(0, 960 - gap_x, u), 544, col, 1, 1.4)
    hairline(c, 1920, 544, lerp(1920, 960 + gap_x, u), 544, col, 1, 1.4)
    hairline(c, 960, 0, 960, lerp(0, 544 - gap_y, u), col, 1, 1.4)
    hairline(c, 960, 1080, 960, lerp(1080, 544 + gap_y, u), col, 1, 1.4)
    for x, y in [(960 - gap_x, 544), (960 + gap_x, 544), (960, 544 - gap_y), (960, 544 + gap_y)]:
        if u > 0.95:
            c.drawCircle(x, y, 3.5, G.P(col))
    for i in range(-8, 9):                                          # ticks along the lines
        if i == 0:
            continue
        a = clamp(u * 2 - abs(i) / 9)
        hairline(c, 960 + i * 100, 538, 960 + i * 100, 550, col, a * (abs(i) > 2), 1.2)
    f = sans(32, 400)
    blur_in(c, "Stay ahead", 960, 530, f, INK, t, T_CROSS + 0.12, dur=0.4, align=0.5)
    blur_in(c, "of the race", 960, 572, f, INK, t, T_CROSS + 0.22, dur=0.4, align=0.5)


# ---------------------------------------------------------------- right from your pocket

NOTES = [("Radar", "New launch spotted: Sonnet 5.5", "now"), ("Scout", "Your read for this week is ready", "2m"),
         ("Radar", "DevDay starts in 2 days", "1h")]


def lock_screen(c, sx, sy, sw, sh, t):
    plates.day(c, t, zoom=2.2, cx=0.52, cy=0.46, soft=8.0)
    c.drawRect(skia.Rect.MakeXYWH(sx, sy, sw, sh), G.P("#000000", 0.18))
    devices.status_bar(c, sx, sy, sw)
    k = sw / 416
    T(c, "Thursday 1 October", sx + sw / 2, sy + 104 * k, sans(18 * k, 500), WHITE, 0.9, align=0.5)
    T(c, "9:41", sx + sw / 2, sy + 196 * k, sans(92 * k, 600), WHITE, 0.95, align=0.5, tracking=-0.02)
    y = sy + 250 * k
    for i, (app, text, when) in enumerate(NOTES):
        u = out_back(clamp((t - (T_POCKET_IMG + 0.35 + 0.42 * i)) / 0.35), 1.4)
        if u <= 0:
            continue
        yy = y + i * 86 * k
        with G.layer(c, clamp(u * 2)):
            with G.xf(c, sx + sw / 2, yy + 36 * k, s=0.9 + 0.1 * u):
                c.drawRRect(rr(-sw / 2 + 12 * k, -36 * k, sw - 24 * k, 76 * k, 20 * k), G.P("#f4f4f6", 0.78))
                marks.icon(c, -sw / 2 + 44 * k, 2 * k, 34 * k, shape="square" if app == "Radar" else "round",
                           glow=0.0)
                T(c, app, -sw / 2 + 72 * k, -6 * k, sans(15 * k, 600), INK)
                T(c, text, -sw / 2 + 72 * k, 16 * k, sans(14 * k, 400), "#2a2a2e")
                T(c, when, sw / 2 - 26 * k, -6 * k, sans(13 * k, 400), "#6a6a70", align=1.0)


def pocket(c, t):
    f = sans(62, 300)
    if t < T_POCKET_IMG:
        w = f.width("Right from your")
        x0 = 960 - w / 2
        blur_in(c, "Right", x0, 560, f, WHITE, t, T_POCKET, dur=0.35)
        blur_in(c, "from your", x0 + f.width("Right "), 560, f, WHITE, t, T_POCKET + 0.53, dur=0.35)
        return
    tau = t - T_POCKET_IMG
    a, b = blur_out(t, T_NAME - 0.2, 0.2)
    with G.layer(c, a, blur=b):
        with G.layer(c, clamp(tau / 0.2)):
            plates.day(c, t, zoom=1.25 + 0.02 * tau, cx=0.5, cy=0.5, drift=-15 * tau)
            c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#000000", 0.16))
        up = out_quart(clamp(tau / 0.45))
        w = f.width("Right from your pocket")
        x0 = 960 - w / 2
        y = lerp(560, 250, up)
        with G.layer(c, 0.3, blur=12):
            T(c, "Right from your pocket", x0, y + 3, f, "#06200a")
        T(c, "Right from your", x0, y, f, WHITE)
        blur_in(c, "pocket", x0 + f.width("Right from your "), y, f, WHITE, t, T_POCKET_IMG + 0.05, dur=0.4)
        pw, ph = 420.0, 860.0
        rise = out_cubic(clamp((tau - 0.1) / 0.6))
        py = lerp(1150, 360, rise)
        devices.phone(c, 960 - pw / 2, py, pw, ph, lambda cc, a1, b1, w1, h1: lock_screen(cc, a1, b1, w1, h1, t),
                      shadow=0.45)


def name(c, t):
    tau = t - T_NAME
    plates.day(c, t, zoom=1.0 + 0.012 * tau, cx=0.5, cy=0.5)
    sky.birds(c, t, T_NAME - 0.5, n=7, x0=300, y0=230, vx=150, vy=-10, size=12, col="#243024", seed=9)
    a, b = blur_out(t, T_MARK - 0.2, 0.2)
    with G.layer(c, a, blur=b):
        with G.layer(c, 0.28, blur=16):
            marks.wordmark(c, 960, 604, 190, col="#0a2a08")
        with G.layer(c, clamp(tau / 0.4), blur=14 * (1 - out_cubic(clamp(tau / 0.45)))):
            marks.wordmark(c, 960, 600, 190)


def mark_over_hills(c, t):
    tau = t - T_MARK
    plates.day(c, t, zoom=1.03 + 0.02 * tau, cx=0.5, cy=0.5)
    dim = clamp(tau / 0.5) * 0.45
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#000000", dim))
    out = in_cubic(clamp((t - (T_BLACK - 0.35)) / 0.35))
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#000000", out))
    marks.mark(c, 960, 560, 300, t=t, t0=T_MARK + 0.05)


def end(c, t):
    tau = t - T_BLACK
    s = lerp(300, 170, out_quart(clamp(tau / 0.8)))
    marks.mark(c, 960, 548 - 30 * out_quart(clamp(tau / 0.8)), s)
    f = sans(19, 400)
    note = "A concept film  ·  predictions, not news  ·  not affiliated with any lab named"
    blur_in(c, note, 960, 1006, f, "#85858c", t, T_NOTE, dur=0.6, align=0.5, tracking=0.02)
    blur_in(c, "MADE BY VEEE", 960, 700, sans(17, 600), "#9a9aa1", t, T_NOTE + 0.4, dur=0.6, align=0.5,
            tracking=0.4)
    fade = clamp((t - (DURATION - 0.7)) / 0.7)
    if fade > 0:
        c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#000000", fade))
