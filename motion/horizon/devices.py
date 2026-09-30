"""HORIZON's devices: a phone in dark titanium and a laptop seen from the front, each with a screen that any scene
can draw into."""
import skia

from engine import gfx as G
from .look import rr, WHITE, T, sans

PHONE_R, PHONE_BEZEL = 68.0, 12.0


def phone(c, x, y, w, h, screen, a=1.0, shadow=0.35, island=True):
    """A phone with its top-left at (x, y); screen(c, sx, sy, sw, sh) draws the screen's contents, clipped to it."""
    r = PHONE_R * w / 440
    b = PHONE_BEZEL * w / 440
    with G.layer(c, a):
        if shadow > 0:
            c.drawRRect(rr(x + w * 0.04, y + h * 0.03, w, h, r), G.P("#000000", shadow, blur=w * 0.08))
        c.drawRRect(rr(x, y, w, h, r), G.P("#1b1b1e", 1, shader=G.linear_grad(x, y, x + w, y + h,
                                                                             ["#5a5a60", "#1b1b1e", "#3a3a40"],
                                                                             [0.0, 0.5, 1.0])))
        c.drawRRect(rr(x + 2.5, y + 2.5, w - 5, h - 5, r - 2.5), G.P("#050506"))
        sx, sy, sw, sh = x + b, y + b, w - 2 * b, h - 2 * b
        c.save()
        c.clipRRect(rr(sx, sy, sw, sh, r - b), True)
        screen(c, sx, sy, sw, sh)
        c.restore()
        if island:
            iw, ih = sw * 0.27, sw * 0.075
            c.drawRRect(rr(sx + (sw - iw) / 2, sy + sw * 0.03, iw, ih, ih / 2), G.P("#000000"))


def status_bar(c, sx, sy, sw, col=WHITE, a=1.0):
    k = sw / 416
    T(c, "9:41", sx + 36 * k, sy + 38 * k, sans(17 * k, 600), col, a)
    bx = sx + sw - 64 * k
    c.drawRRect(rr(bx, sy + 26 * k, 27 * k, 13 * k, 4 * k), G.P(col, a, stroke=1.6 * k))
    c.drawRRect(rr(bx + 2.5 * k, sy + 28.5 * k, 19 * k, 8 * k, 2 * k), G.P(col, a))
    for i in range(4):                                             # signal
        hh = (4 + 3 * i) * k
        c.drawRRect(rr(bx - 34 * k + i * 6 * k, sy + 38 * k - hh, 4 * k, hh, 1 * k), G.P(col, a))


def laptop(c, x, y, w, screen, a=1.0, base=True):
    """A laptop from the front: its lid w wide with its top-left at (x, y), the deck below it."""
    h = w * 0.64
    r = w * 0.022
    with G.layer(c, a):
        c.drawRRect(rr(x - w * 0.02, y + h * 0.05, w * 1.04, h, r), G.P("#000000", 0.28, blur=w * 0.035))
        c.drawRRect(rr(x, y, w, h, r), G.P("#b9bac0", 1, shader=G.linear_grad(x, y, x, y + h,
                                                                            ["#d6d7dc", "#a9aab0"])))
        c.drawRRect(rr(x + 3, y + 3, w - 6, h - 6, r - 2), G.P("#0a0a0b"))
        bz = w * 0.022
        sx, sy, sw, sh = x + bz, y + bz, w - 2 * bz, h - 2 * bz - w * 0.008
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(sx, sy, sw, sh))
        screen(c, sx, sy, sw, sh)
        c.restore()
        c.drawRRect(rr(x + w / 2 - w * 0.045, y + 1, w * 0.09, bz * 0.8, bz * 0.3), G.P("#0a0a0b"))   # the notch
        if base:
            p = skia.Path()
            d = w * 0.05
            p.moveTo(x - d * 0.4, y + h)
            p.lineTo(x + w + d * 0.4, y + h)
            p.lineTo(x + w + d, y + h + w * 0.035)
            p.lineTo(x - d, y + h + w * 0.035)
            p.close()
            c.drawPath(p, G.P("#c7c8cd", 1, shader=G.linear_grad(0, y + h, 0, y + h + w * 0.035,
                                                                  ["#e4e5e9", "#9d9ea4"])))
            c.drawRRect(rr(x + w / 2 - w * 0.07, y + h, w * 0.14, w * 0.007, w * 0.003), G.P("#8e8f95"))
