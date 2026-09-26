"""The walk to dinner: a tilted map of the French Quarter (its real street grid, simplified), a glowing route
from Canal Street down Bourbon to 813 Bienville, and a booking card that says the table is yours."""
import math
from functools import lru_cache

import numpy as np
import skia

from engine import gfx as G
from engine.core import clamp, lerp, snap, whip, out_cubic, in_out_cubic, in_out_sine, spring, hash01
from .look import (F, T, ui, rr, WHITE, INK, GREY, LIME, BLUE, GOLD, GLOW, glow_rrect, glow_blob, soft_shadow,
                   icon_check, icon_pin, sweep)
from .score import T_MAP, T_ROUTE, T_CONFIRM, T_GO, T_CRAVE, T_TAP

B = 260                     # one French Quarter block, in map pixels
LAND = "#f1eee7"
BLOCK = "#e7e3d9"
STREET = "#ffffff"
CASING = "#d9d4c8"
WATER = "#cfe2f5"
PARK = "#d5ebc6"
LABEL = "#8a857a"

# streets parallel to the river, by distance from it (in blocks)
LONG = [(0, "Decatur St"), (1, "Chartres St"), (2, "Royal St"), (3, "Bourbon St"), (4, "Dauphine St"),
        (5, "Burgundy St"), (6, "N Rampart St")]
# cross streets, counted downriver from Canal
CROSS = [(0, "Canal St"), (1, "Iberville St"), (2, "Bienville St"), (3, "Conti St"), (4, "St Louis St"),
         (5, "Toulouse St"), (6, "St Peter St"), (7, "Orleans Ave"), (8, "St Ann St"), (9, "Dumaine St")]
ARNAUDS = (2.0, 3.42)       # on Bienville, just off Bourbon
YOU = (0.0, 0.25)           # Canal Street, down by the river
ROUTE = [(0.0, 0.25), (0.0, 3.0), (2.0, 3.0), (2.0, 3.42)]
MAP_ROT = -34.0


def mp(u, v):
    """Blocks to map pixels. u runs downriver, v away from the river."""
    return u * B, -v * B


def cam(t):
    """(centre x, centre y in map px, zoom, tilt): start over Canal, follow the walker, settle on Arnaud's."""
    p = route_point(in_out_sine(clamp((t - T_GO[0]) / (T_GO[1] - T_GO[0]))))
    a = mp(0.8, 2.0)
    b = mp(*ARNAUDS)
    u0 = in_out_cubic(clamp((t - T_MAP) / 1.2))
    look = (lerp(p[0], b[0], 0.55), lerp(p[1], b[1], 0.55))
    cx = lerp(a[0], look[0], u0)
    cy = lerp(a[1], look[1], u0)
    end = in_out_cubic(clamp((t - (T_GO[1] - 0.3)) / 0.8))
    cx, cy = lerp(cx, b[0], end), lerp(cy, b[1], end)
    zoom = lerp(0.72, 0.95, in_out_sine(clamp((t - T_MAP) / 3.5)))
    zoom *= 1 + 1.8 * (clamp((t - (T_CRAVE - 0.35)) / 0.45) ** 2)
    tilt = lerp(8, 42, snap(clamp((t - T_MAP) / 0.9)))
    return cx, cy, zoom, tilt


def matrix(t):
    cx, cy, z, tilt = cam(t)
    m = G.perspective(960, 640, rx=-tilt, rz=0, D=1500)
    m.preTranslate(960, 640)
    m.preScale(z, z)
    m.preRotate(MAP_ROT + 4 * math.sin((t - T_MAP) * 0.4))
    m.preTranslate(-cx, -cy)
    return m


@lru_cache(maxsize=1)
def route_path():
    p = skia.Path()
    x, y = mp(*ROUTE[0])
    p.moveTo(x, y)
    for u, v in ROUTE[1:]:
        p.lineTo(*mp(u, v))
    return p


@lru_cache(maxsize=1)
def _measure():
    m = skia.PathMeasure(route_path(), False)
    return m.getLength()


def route_point(u):
    m = skia.PathMeasure(route_path(), False)
    pos, _ = m.getPosTan(_measure() * clamp(u))
    return pos.fX, pos.fY


@lru_cache(maxsize=1)
def buildings():
    """Little roofs inside each block, for texture."""
    out = []
    for u in range(-3, 11):
        for v in range(-1, 8):
            for k in range(6):
                h = float(hash01(u * 131 + v * 17 + k, 5))
                if h < 0.25:
                    continue
                bx = u + 0.12 + 0.76 * float(hash01(u * 7 + v * 3 + k, 11)) * 0.7
                by = v + 0.12 + 0.76 * float(hash01(u * 5 + v * 13 + k, 12)) * 0.7
                w = 0.12 + 0.2 * float(hash01(u + v + k, 13))
                hh = 0.12 + 0.2 * float(hash01(u - v + k, 14))
                out.append((bx, by, w, hh))
    return out


def draw_map(c, t):
    c.drawRect(skia.Rect.MakeXYWH(-4000, -4000, 8000, 8000), G.P(LAND))
    # the river and the riverfront
    x0, y0 = mp(-3, -0.35)
    c.drawRect(skia.Rect.MakeLTRB(-4000, y0, 4000, 4000), G.P(WATER))
    c.drawRect(skia.Rect.MakeLTRB(-4000, y0 - 6, 4000, y0), G.P("#b7d3ee"))
    px0, py0 = mp(1.0, -0.33)
    px1, py1 = mp(5.8, -0.05)
    c.drawRect(skia.Rect.MakeLTRB(px0, py1, px1, py0), G.P(PARK))
    # blocks and roofs
    for bx, by, w, h in buildings():
        x, y = mp(bx, by + h)
        c.drawRect(skia.Rect.MakeXYWH(x, y, w * B, h * B), G.P(BLOCK))
    js0, js1 = mp(6.0, 1.0), mp(8.0, 0.0)
    c.drawRect(skia.Rect.MakeLTRB(js0[0] + 20, js0[1] + 20, js1[0] - 20, js1[1] - 20), G.P(PARK))
    # streets: casing, then the white road
    for width, col in ((58, CASING), (50, STREET)):
        for v, name in LONG:
            wv = width * (1.7 if name == "N Rampart St" else 1.0)
            a, b = mp(-3, v), mp(10.5, v)
            c.drawLine(a[0], a[1], b[0], b[1], G.P(col, 1, stroke=wv))
        for u, name in CROSS:
            wu = width * (2.2 if name == "Canal St" else 1.0)
            a, b = mp(u, -0.2), mp(u, 7.2)
            c.drawLine(a[0], a[1], b[0], b[1], G.P(col, 1, stroke=wu, cap="round"))
    # the Arnaud's block glows warm
    ab0, ab1 = mp(1.08, 3.92), mp(1.92, 3.08)
    c.drawRect(skia.Rect.MakeLTRB(ab0[0], ab0[1], ab1[0], ab1[1]), G.P("#f6d9a8", 0.8))


def labels(c, t, m):
    """Street names ride the map but stay upright to the street direction, like a real map."""
    f = ui(21, 560)
    for v, name in LONG:
        x, y = mp(4.5 if v != 3 else 1.0, v)
        with G.xf(c, x, y):
            T(c, name.upper(), 0, 8, f, LABEL, align=0.5, tracking=0.18)
    for u, name in CROSS:
        x, y = mp(u, 1.5 if u != 2 else 4.6)
        with G.xf(c, x, y, rot=-90):
            T(c, name.upper(), 0, 8, f if name != "Canal St" else ui(26, 650), LABEL, align=0.5, tracking=0.18)
    x, y = mp(7.0, 0.5)
    T(c, "JACKSON SQUARE", x, y + 8, ui(18, 600), "#6f8f5c", align=0.5, tracking=0.2)
    x, y = mp(3.5, -1.1)
    T(c, "MISSISSIPPI RIVER", x, y, ui(34, 600), "#7da2c9", align=0.5, tracking=0.5)
    x, y = mp(6.5, 5.5)
    T(c, "FRENCH QUARTER", x, y, ui(46, 700), "#b9b3a5", align=0.5, tracking=0.5)


def route(c, t):
    p = in_out_cubic(clamp((t - T_ROUTE[0]) / (T_ROUTE[1] - T_ROUTE[0])))
    if p <= 0:
        return
    path = route_path()
    a0, a1 = mp(*ROUTE[0]), mp(*ROUTE[-1])
    shader = G.linear_grad(a0[0], a0[1], a1[0], a1[1], ["#e858a8", "#fb8f5a", "#c8f868", "#68d888", "#4f72e8"])
    glow = skia.Paint(AntiAlias=True)
    glow.setStyle(skia.Paint.kStroke_Style)
    glow.setStrokeWidth(46)
    glow.setStrokeCap(skia.Paint.kRound_Cap)
    glow.setStrokeJoin(skia.Paint.kRound_Join)
    glow.setShader(shader)
    glow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22))
    eff = G.trim(0, p)
    if eff is not None:
        glow.setPathEffect(eff)
    glow.setAlphaf(0.75)
    c.drawPath(path, glow)
    line = skia.Paint(AntiAlias=True)
    line.setStyle(skia.Paint.kStroke_Style)
    line.setStrokeWidth(16)
    line.setStrokeCap(skia.Paint.kRound_Cap)
    line.setStrokeJoin(skia.Paint.kRound_Join)
    line.setShader(shader)
    if eff is not None:
        line.setPathEffect(eff)
    c.drawPath(path, line)


def screen_overlays(c, t, m):
    # "you": a blue dot walking the route
    u = in_out_sine(clamp((t - T_GO[0]) / (T_GO[1] - T_GO[0])))
    x, y = route_point(u)
    p = m.mapXY(x, y)
    pulse = (t * 1.4) % 1.0
    G.circle(c, p.fX, p.fY, 22 + 60 * pulse, G.P(BLUE, 0.35 * (1 - pulse)))
    G.circle(c, p.fX, p.fY, 22, G.P(WHITE))
    G.circle(c, p.fX, p.fY, 15, G.P(BLUE))
    # the Arnaud's pin
    ax, ay = mp(*ARNAUDS)
    q = m.mapXY(ax, ay)
    s = spring(t - (T_MAP + 0.35), 2.4, 0.5) if t >= T_MAP + 0.35 else 0.0
    if s > 0:
        glow_blob(c, q.fX, q.fY - 70, 170 * s, GOLD, 0.45)
        with G.xf(c, q.fX, q.fY, s=s):
            c.drawOval(skia.Rect.MakeXYWH(-26, -9, 52, 18), G.P("#000000", 0.18, blur=4))
            icon_pin(c, 0, -62, 120, INK)
            G.circle(c, 0, -84, 30, G.P(WHITE))
            T(c, "A", 0, -71, F("serif", 40), INK, align=0.5)
            # label card
            f = F("serif", 40)
            w = max(f.width("Arnaud’s"), ui(20, 500).width("813 Bienville St")) + 56
            x0 = 58
            soft_shadow(c, x0, -150, w, 104, 22, 1.0, 0.6)
            c.drawRRect(rr(x0, -150, w, 104, 22), G.P(WHITE))
            T(c, "Arnaud’s", x0 + 28, -98, f, INK)
            T(c, "813 Bienville St", x0 + 28, -66, ui(20, 500), GREY)


def booking_card(c, t):
    """Screen-space: the confirmation, pinned to the top of the frame."""
    s = spring(t - (T_MAP + 0.2), 2.2, 0.62) if t >= T_MAP + 0.2 else 0.0
    if s <= 0:
        return
    w, h = 820, 150
    x, y = 960 - w / 2, lerp(-200, 56, s)
    glow_rrect(c, x, y, w, h, 40, t, a=1.0, spread=26, width=20, speed=60)
    soft_shadow(c, x, y, w, h, 40, 1.0, 0.8)
    c.drawRRect(rr(x, y, w, h, 40), G.P(WHITE))
    G.circle(c, x + 80, y + h / 2, 42, G.P(LIME))
    icon_check(c, x + 80, y + h / 2 + 2, 40, INK, p=snap(clamp((t - T_MAP - 0.4) / 0.35)))
    T(c, "Table for 2 at Arnaud’s", x + 148, y + 68, ui(36, 650), INK)
    T(c, "Tonight · 8:00 pm · 813 Bienville St, New Orleans", x + 148, y + 110, ui(24, 460), GREY)
    # the walk, counting down as the dot moves
    u = clamp((t - T_GO[0]) / (T_GO[1] - T_GO[0]))
    mins = max(0, int(math.ceil(7 * (1 - u))))
    label = f"{mins} min walk" if mins > 0 else "You’re here"
    cw = ui(28, 620).width(label) + 110
    cy = 1080 - 150
    k = clamp((t - T_ROUTE[0]) / 0.3)
    if k > 0:
        with G.layer(c, alpha=k):
            soft_shadow(c, 70, cy, cw, 86, 43, 1.0, 0.6)
            c.drawRRect(rr(70, cy, cw, 86, 43), G.P(INK if mins > 0 else LIME))
            G.circle(c, 70 + 48, cy + 43, 18, G.P(BLUE if mins > 0 else INK))
            T(c, label, 70 + 82, cy + 53, ui(28, 620), WHITE if mins > 0 else INK)


def mapscene(c, t):
    m = matrix(t)
    c.save()
    c.concat(m)
    draw_map(c, t)
    labels(c, t, m)
    route(c, t)
    c.restore()
    screen_overlays(c, t, m)
    booking_card(c, t)
