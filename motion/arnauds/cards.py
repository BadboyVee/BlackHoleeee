"""The carousel: a lime field of dark food cards racing past, the usual cravings, until Arnaud's lifts out."""
import math
import os
from functools import lru_cache

import cv2
import skia

from engine import gfx as G
from engine.core import clamp, lerp, snap, whip, out_cubic, in_out_cubic, out_quint, spring
from .look import (F, T, ui, rr, WHITE, INK, LIME, ORANGE, CARD, GOLD, GLOW, glow_rrect, glow_blob, draw_cover,
                   photo, PHOTOS,
                   icon_star, icon_pin, icon_clock, icon_flame, icon_people)
from .score import T_LIME, T_CARDS, T_PICK, T_FULL, T_TO_CHAT

W, H, GAP = 380, 452, 28
ROW = ["pizza", "sushi", "ramen", "pizza", "sushi", "ramen", "arnauds", "pizza", "sushi", "ramen"]
PICK = ROW.index("arnauds")
DISH = {
    "pizza": dict(title="Pepperoni Pizza", desc="Stone-baked, bubbling cheese and sweet peppers.", badge="Most Popular",
                  time="25–35 min", dist="1.4 km", price="$18", rating="4.6", fy=0.45),
    "sushi": dict(title="Salmon Maki", desc="Eight pieces, avocado and red cabbage.", badge="Fresh Today",
                  time="20–30 min", dist="2.1 km", price="$16", rating="4.7", fy=0.5),
    "ramen": dict(title="Shoyu Ramen", desc="Rich broth, soft egg, mushrooms, chashu.", badge="Cozy Pick",
                  time="30–40 min", dist="2.6 km", price="$15", rating="4.8", fy=0.45),
}


def food_card(c, kind, x, y, t, a=1.0):
    d = DISH[kind]
    with G.layer(c, alpha=a):
        c.drawRRect(rr(x, y, W, H, 24), G.P(CARD))
        c.save()
        c.clipRRect(rr(x, y, W, H, 24), skia.ClipOp.kIntersect, True)
        draw_cover(c, kind, x, y, W, 290, fy=d["fy"], min_w=600)
        c.drawRect(skia.Rect.MakeXYWH(x, y + 170, W, 125),
                   G.P(CARD, 1, shader=G.linear_grad(0, y + 170, 0, y + 295, [CARD, CARD], alphas=[0.0, 1.0])))
        c.restore()
        fb = ui(15, 600)
        bw = fb.width(d["badge"]) + 48
        c.drawRRect(rr(x + 14, y + 14, bw, 32, 16), G.P("#000000", 0.5))
        c.drawRRect(rr(x + 14, y + 14, bw, 32, 16), G.P(ORANGE, 1, stroke=1.4))
        icon_flame(c, x + 32, y + 30, 16, ORANGE)
        T(c, d["badge"], x + 46, y + 35, fb, ORANGE)
        icon_star(c, x + W - 60, y + 30, 16, "#f5c542")
        T(c, d["rating"], x + W - 48, y + 36, fb, WHITE)
        T(c, d["title"], x + 20, y + 322, ui(26, 650), WHITE)
        T(c, d["desc"], x + 20, y + 352, ui(15, 420), "#9d9da4")
        fm = ui(14, 500)
        icon_clock(c, x + 28, y + 412, 16, "#9d9da4")
        T(c, d["time"], x + 42, y + 417, fm, "#c4c4ca")
        icon_pin(c, x + 128, y + 412, 16, "#9d9da4")
        T(c, d["dist"], x + 142, y + 417, fm, "#c4c4ca")
        T(c, d["price"], x + W - 20, y + 419, ui(24, 650), LIME, align=1.0)


def arnauds_card(c, x, y, t, a=1.0, glow=0.0):
    with G.layer(c, alpha=a):
        if glow > 0:
            glow_rrect(c, x, y, W, H, 24, t, a=glow, spread=40, width=34, speed=70)
        c.drawRRect(rr(x, y, W, H, 24), G.P(CARD))
        c.save()
        c.clipRRect(rr(x, y, W, H, 24), skia.ClipOp.kIntersect, True)
        draw_cover(c, "dining", x, y, W, 290, fx=0.3, fy=0.3, zoom=1.15)
        c.drawRect(skia.Rect.MakeXYWH(x, y + 170, W, 125),
                   G.P(CARD, 1, shader=G.linear_grad(0, y + 170, 0, y + 295, [CARD, CARD], alphas=[0.0, 1.0])))
        c.restore()
        fb = ui(15, 600)
        bw = fb.width("Something special") + 50
        c.drawRRect(rr(x + 14, y + 14, bw, 32, 16), G.P("#000000", 0.5))
        c.drawRRect(rr(x + 14, y + 14, bw, 32, 16), G.P(GOLD, 1, stroke=1.4))
        icon_star(c, x + 32, y + 30, 16, GOLD)
        T(c, "Something special", x + 48, y + 35, fb, GOLD)
        T(c, "Arnaud’s", x + 20, y + 330, F("serif", 40), WHITE)
        T(c, "Classic Creole in the French Quarter", x + 20, y + 360, ui(15, 420), "#9d9da4")
        fm = ui(14, 500)
        icon_pin(c, x + 28, y + 412, 16, "#9d9da4")
        T(c, "813 Bienville St", x + 42, y + 417, fm, "#c4c4ca")
        pw = ui(18, 650).width("Book") + 36
        c.drawRRect(rr(x + W - 20 - pw, y + 394, pw, 38, 19), G.P(LIME))
        T(c, "Book", x + W - 20 - pw / 2, y + 419, ui(18, 650), INK, align=0.5)


def row_origin(t):
    """x of the first card: the row races in from the right and brakes so Arnaud's stops dead centre."""
    x_start = 1980.0
    x_end = 960 - (PICK * (W + GAP) + W / 2)
    u = clamp((t - T_CARDS) / (T_PICK - T_CARDS))
    return lerp(x_start, x_end, out_quint(u))


def carousel(c, t):
    # the lime field opens out of a small card in the middle of the frame
    u = snap(clamp((t - T_LIME) / 0.36))
    w, h = lerp(150, 1960, u), lerp(110, 1120, u)
    c.drawRRect(rr(960 - w / 2, 560 - h / 2, w, h, lerp(18, 0, u)), G.P(LIME))
    if u < 0.4:
        # the tiny card inside, as in the reference
        food_card_mini(c, 960, 560, 1 - u / 0.4)
    ox = row_origin(t)
    lift = spring(t - T_PICK, 2.2, 0.55) if t >= T_PICK else 0.0
    y0 = 540 - H / 2
    for i, kind in enumerate(ROW):
        x = ox + i * (W + GAP)
        if x > 1960 or x + W < -40:
            continue
        if i == PICK:
            continue
        dim = 1 - 0.55 * clamp(lift)
        food_card(c, kind, x, y0 + 40 * clamp(lift), t, a=dim)
    x = ox + PICK * (W + GAP)
    s = 1 + 0.2 * lift
    with G.xf(c, x + W / 2, y0 + H / 2 - 70 * lift, s=s):
        arnauds_card(c, -W / 2, -H / 2, t, glow=clamp(lift))


def food_card_mini(c, x, y, a):
    c.drawRRect(rr(x - 34, y - 38, 68, 76, 8), G.P(CARD, a))
    c.save()
    c.clipRRect(rr(x - 34, y - 38, 68, 76, 8), skia.ClipOp.kIntersect, True)
    draw_cover(c, "ramen", x - 34, y - 38, 68, 46, alpha=a)
    c.restore()


@lru_cache(maxsize=1)
def dining_lights():
    """The chandelier bulbs in the dining-room photo: (x, y, size) in photo pixels, brightest first."""
    p = os.path.join(PHOTOS, "dining.jpg")
    if not os.path.exists(p):
        return []
    g = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(g, 238, 255, cv2.THRESH_BINARY)
    n, _, stats, cent = cv2.connectedComponentsWithStats(th)
    pts = [(float(cx), float(cy), int(st[4])) for (cx, cy), st in zip(cent[1:], stats[1:]) if st[4] >= 4]
    pts.sort(key=lambda q: -q[2])
    return pts[:80]


def dining_full(c, t):
    """Arnaud's card opens to fill the frame: the grand dining room, its chandeliers glinting on the beat."""
    x_card = row_origin(t) + PICK * (W + GAP) + W / 2
    lift = spring(t - T_PICK, 2.2, 0.55) if t >= T_PICK else 0.0
    s_card = 1 + 0.2 * lift
    cx0, cy0 = x_card, 540 - 70 * lift
    u = snap(clamp((t - T_FULL) / 0.4))
    w = lerp(W * s_card, 1920, u)
    h = lerp(290 * s_card, 1080, u)
    x = lerp(cx0 - W * s_card / 2, 0, u)
    y = lerp(cy0 - H * s_card / 2, 0, u)
    r = lerp(24, 0, u)
    c.save()
    c.clipRRect(rr(x, y, w, h, r), skia.ClipOp.kIntersect, True)
    push = 1.0 + 0.07 * clamp((t - T_FULL) / 1.2)
    img = photo("dining", 1500)
    iw, ih = (img.width(), img.height()) if img is not None else (1500, 1000)
    sc = max(w / iw, h / ih) * push
    dx = x + (w - iw * sc) * 0.42
    dy = y + (h - ih * sc) * 0.3
    if img is not None:
        G.draw_image(c, img, dx, dy, iw * sc, ih * sc)
    # the bulbs glint: photo coordinates mapped through the same cover transform
    k = iw / 678.0
    for i, (px, py, size) in enumerate(dining_lights()):
        sx, sy = dx + px * k * sc, dy + py * k * sc
        tw = 0.55 + 0.45 * math.sin(t * (5 + (i % 7)) + i * 1.3)
        rad = (8 + 4.5 * math.sqrt(size)) * sc / 2.8
        glow_blob(c, sx, sy, rad * 3.2, "#ffd28a", 0.5 * tw * u)
        glow_blob(c, sx, sy, rad * 1.2, "#fff6e6", 0.9 * tw * u)
        if i < 14:
            L = rad * (5 + 3 * tw)
            p = G.P("#fff3dc", 0.55 * tw * u, stroke=2.2, blur=1.2)
            c.drawLine(sx - L, sy, sx + L, sy, p)
            c.drawLine(sx, sy - L * 0.7, sx, sy + L * 0.7, p)
    # a warm grade and the title
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), G.P("#000000", 1, shader=G.linear_grad(0, y + h * 0.45, 0, y + h,
               ["#000000", "#000000"], alphas=[0.0, 0.72 * u])))
    a = clamp((t - T_FULL - 0.3) / 0.35)
    if a > 0:
        e = out_cubic(a)
        T(c, "Arnaud’s", 120, 900 + 40 * (1 - e), F("serif", 190), WHITE, a=a)
        T(c, "CLASSIC CREOLE   ·   FRENCH QUARTER   ·   SINCE 1918", 128, 972 + 30 * (1 - e), ui(26, 600), WHITE,
          a=0.85 * a, tracking=0.3)
    c.restore()
    if u > 0:
        glow_rrect(c, x + 10, y + 10, w - 20, h - 20, 40, t, a=0.8 * u, spread=40, width=30, speed=60)
