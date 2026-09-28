"""THE RACE TO AGI: the broadcast kit.

A night-race TV package: wide italic type, slanted panels, team liveries, side-on cars, the start-light gantry,
team radio, race control, team-boss cards, the pit board, shift lights, a chequered flag, a track rushing at the
camera, and a lap counter that is also the week of the year. Every scene draws from here."""
import math
import os
from functools import lru_cache

import cv2
import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_expo, out_quint, in_cubic, in_out_cubic, hash01
from . import marks as M
from .look import F, FOUNDERS, PHOTOS, rr

# ---------------------------------------------------------------- colour
NIGHT = "#0a0a0f"
PANEL = "#111117"
PANEL_2 = "#1d1d26"
WHITE = "#ffffff"
GREY = "#a2a2ae"
RED = "#ff1e2d"
RED_DEEP = "#b3000f"
LAMP = "#ff2513"
YELLOW = "#ffd400"
GREEN = "#14e05e"
BLUE_LED = "#2f7bff"
CLAY = "#d97757"
IVORY = "#f0eee6"
INK = "#141413"
GEMINI = ["#4285f4", "#9b72cb", "#d96570"]
META_BLUE = "#0866ff"

# each lab is a team: its code, the model it brings, its mark, and the livery its car wears
TEAMS = {
    "anthropic": dict(code="ANT", company="ANTHROPIC", model="SONNET 5.5", mark="claude", col=CLAY, ink=IVORY,
                      body=CLAY, pod=INK, stripe=IVORY, text=IVORY, helmet=IVORY, visor=INK, wing=INK, logo=IVORY,
                      band=IVORY, dark_mark=CLAY),
    "openai": dict(code="OAI", company="OPENAI", model="NEW MODEL", model2="AGENT “O”", mark="openai",
                   col="#0d0d0d", ink=WHITE, body="#0e0e10", pod="#26262b", stripe=WHITE, text=WHITE, helmet=WHITE,
                   visor="#0d0d0d", wing="#0e0e10", logo=WHITE, band=WHITE, dark_mark=WHITE),
    "google": dict(code="GDM", company="GOOGLE DEEPMIND", model="GEMINI", mark="gemini", col="#4285f4", ink=WHITE,
                   body=WHITE, pod="gemini", stripe="gemini", text=WHITE, helmet="#4285f4", visor=INK,
                   wing="#1b2a5e", logo="gemini", band="#4285f4", dark_mark="gemini"),
    "meta": dict(code="MTA", company="META", model="MUSE", mark="meta", col=META_BLUE, ink=WHITE, body=WHITE,
                 pod="#0a1f5c", stripe=META_BLUE, text=WHITE, helmet=META_BLUE, visor=INK, wing="#0a1f5c",
                 logo=META_BLUE, band=META_BLUE, dark_mark="#3d8bff"),
    "xai": dict(code="XAI", company="xAI", model="GROK 4.8", mark="grok", col=WHITE, ink="#0d0d0f", body="#f3f3f5",
                pod="#0d0d0f", stripe="#0d0d0f", text=WHITE, helmet="#0d0d0f", visor=WHITE, wing="#0d0d0f",
                logo="#0d0d0f", band=WHITE, dark_mark=WHITE),
}

SLANT = math.tan(math.radians(12))


# ---------------------------------------------------------------- type

def wide(size, w=850):
    """The display face: Archivo italic at its widest."""
    return F("archivo-italic", size, wght=w, wdth=125)


def cond(size, w=700):
    """Labels: Archivo condensed."""
    return F("archivo", size, wght=w, wdth=75)


def cond_i(size, w=800):
    return F("archivo-italic", size, wght=w, wdth=75)


def T(c, s, x, y, font, col, a=1.0, align=0.0, tracking=0.0, shader=None, tnum=False):
    if a <= 0:
        return None
    p = G.P(col, a)
    if shader is not None:
        p.setShader(shader)
    return G.text(c, s, x, y, font, p, align=align, tracking=tracking, features={"tnum": True} if tnum else None)


def mark(c, team, x, y, size, col=None, a=1.0):
    """A team's mark; "gemini" as a colour paints the Gemini gradient."""
    col = col or TEAMS[team]["dark_mark"]
    name = TEAMS[team]["mark"]
    if col == "gemini":
        M.mark(c, name, x, y, size, a=a, shader=G.linear_grad(x - size / 2, y + size / 2, x + size / 2, y - size / 2,
                                                              GEMINI))
    else:
        M.mark(c, name, x, y, size, col, a)


def slide(c, s, x, y, font, col, t, t0, dur=0.42, a=1.0, align=0.0, tracking=0.0, t1=None, out=0.2, shader=None,
          tnum=False):
    """Text rising into place from behind its own line mask on an expo ease; it drops away again at t1."""
    if t < t0 or a <= 0:
        return
    k = 0.0
    if t1 is not None and t >= t1:
        k = in_cubic(clamp((t - t1) / out))
        if k >= 1:
            return
    run = font.shape(s, tracking, {"tnum": True} if tnum else None)
    x0 = x - run.width * align
    e = out_expo(clamp((t - t0) / dur))
    lh = font.cap + font.size * 0.3
    with G.clip_rect(c, x0 - font.size * 0.4, y - font.cap - font.size * 0.22, run.width + font.size * 0.9,
                     font.cap + font.size * 0.44):
        p = G.P(col, a)
        if shader is not None:
            p.setShader(shader)
        run.draw(c, x0, y + (1 - e) * lh + k * lh, p)


def words(c, text, x, y, font, col, t, t0, step=0.07, dur=0.32, a=1.0, tracking=0.0):
    """Words land one after another, each rising out of its own mask. Returns the line's width."""
    sp = font.width(" ", tracking)
    cx = x
    for i, w in enumerate(text.split(" ")):
        slide(c, w, cx, y, font, col, t, t0 + i * step, dur=dur, a=a, tracking=tracking)
        cx += font.width(w, tracking) + sp
    return cx - sp - x


def slam(c, s, x, y, font, col, t, t0, dur=0.55, a=1.0, align=0.0, tracking=-0.01, dist=1100.0, shader=None,
         shadow=None, t1=None):
    """Giant type arriving like a car: in from the left at speed, braking hard into place, leaning forward while it
    moves and standing up as it stops. It leaves the same way at t1."""
    if t < t0 or a <= 0:
        return
    u = clamp((t - t0) / dur)
    e = out_quint(u)
    ox = -dist * (1 - e)
    sk = -0.28 * (1 - e) ** 2 * (1 if dist > 0 else -1)
    if t1 is not None and t >= t1:
        k = in_cubic(clamp((t - t1) / 0.3))
        ox += 2600 * k
        sk -= 0.25 * k
    run = font.shape(s, tracking)
    x0 = x - run.width * align
    with G.xf(c, x0 + ox, y, skx=sk):
        if shadow is not None:
            run.draw(c, 5, 7, G.P(shadow[0], shadow[1] * a, blur=shadow[2] if len(shadow) > 2 else 6))
        p = G.P(col, a)
        if shader is not None:
            p.setShader(shader)
        run.draw(c, 0, 0, p)


# ---------------------------------------------------------------- panels

def wipe(t, t0, dur=0.34, t1=None, out=0.24):
    """(l, r): a panel wipes on from its left edge, and off towards its right edge from t1."""
    if t < t0:
        return 0.0, 0.0
    r = out_expo(clamp((t - t0) / dur))
    l = 0.0 if t1 is None or t < t1 else in_out_cubic(clamp((t - t1) / out))
    return l, r


def slab(c, x, y, w, h, col, a=1.0, l=0.0, r=1.0, lean=SLANT, shader=None):
    """A slanted panel drawn between fractions l..r of its width. Returns its path (None when empty)."""
    if r <= l or a <= 0:
        return None
    s = h * lean
    x0, x1 = x + w * l, x + w * r
    path = G.poly([(x0 + s, y), (x1 + s, y), (x1, y + h), (x0, y + h)])
    p = G.P(col, a)
    if shader is not None:
        p.setShader(shader)
    c.drawPath(path, p)
    return path


def tab(c, x, y, text, font, fill, ink, t, t0, t1=None, pad=None, h=None, a=1.0, align=0.0, tracking=0.08):
    """A slanted tab with a label, wiping on with its text sliding in behind it. (x, y): left end, vertical centre.
    Returns its width."""
    pad = font.size * 0.55 if pad is None else pad
    h = h or font.cap * 2.3
    tw = font.width(text, tracking)
    w = tw + 2 * pad + h * SLANT
    x0 = x - w * align
    l, r = wipe(t, t0, 0.3, t1)
    path = slab(c, x0, y - h / 2, w, h, fill, a, l=l, r=r)
    if path is not None:
        c.save()
        c.clipPath(path, skia.ClipOp.kIntersect, True)
        T(c, text, x0 + pad + h * SLANT * 0.5 - (1 - r) * 40, y + font.cap / 2, font, ink, a, tracking=tracking)
        c.restore()
    return w


def kerb(c, x0, x1, y, h, cols, block=64.0, offset=0.0, a=1.0):
    """A kerb: alternating blocks along a line; offset scrolls it."""
    if a <= 0:
        return
    k = math.floor((x0 - offset) / block)
    x = offset + k * block
    while x < x1:
        col = cols[int(k) % len(cols)]
        c.drawRect(skia.Rect.MakeLTRB(max(x, x0), y, min(x + block, x1), y + h), G.P(col, a))
        x += block
        k += 1


def pinstripes(c, t, col, a, gap=46.0, width=2.0, speed=30.0, x0=0.0, x1=1920.0, lean=0.6):
    """Thin diagonal lines drifting slowly across a ground."""
    if a <= 0:
        return
    off = (t * speed) % gap
    s = 1080 * lean
    x = x0 - s - gap + off
    p = G.P(col, a, stroke=width)
    while x < x1 + gap:
        c.drawLine(x + s, 0, x, 1080, p)
        x += gap


# ---------------------------------------------------------------- the car

REAR, FRONT, WHEEL_R = (176.0, -64.0), (812.0, -64.0), 64.0


@lru_cache(maxsize=None)
def _geo():
    """The car in its own space: nose to the right, 1000 long, standing on y = 0 (up is negative)."""
    body = skia.Path()
    body.moveTo(56, -36)                                   # the diffuser, low at the back
    body.lineTo(240, -22)
    body.lineTo(720, -22)                                  # the floor
    body.cubicTo(748, -24, 768, -36, 792, -42)             # up into the nose
    body.lineTo(972, -44)
    body.cubicTo(990, -45, 1000, -50, 996, -56)            # the tip
    body.cubicTo(930, -64, 780, -82, 640, -98)             # the nose rising to the cockpit
    body.lineTo(608, -102)
    body.lineTo(490, -104)                                 # the cockpit rim
    body.cubicTo(480, -126, 472, -158, 454, -170)          # the airbox
    body.cubicTo(432, -179, 404, -178, 384, -170)
    body.cubicTo(300, -142, 180, -110, 100, -90)           # the engine cover falling to the back
    body.cubicTo(76, -84, 60, -72, 56, -54)
    body.close()

    pod = skia.Path()                                      # the sidepod, where the model's name goes
    pod.moveTo(634, -26)
    pod.cubicTo(638, -58, 638, -84, 624, -95)
    pod.cubicTo(520, -99, 420, -95, 330, -80)
    pod.cubicTo(282, -70, 252, -50, 236, -26)
    pod.close()

    inlet = skia.Path()                                    # the sidepod's mouth
    inlet.moveTo(624, -92)
    inlet.cubicTo(636, -82, 637, -48, 632, -32)
    inlet.lineTo(619, -34)
    inlet.cubicTo(624, -50, 624, -80, 613, -90)
    inlet.close()

    stripe = G.poly([(1004, -63), (1004, -48), (100, -104), (100, -120)])

    endplate = skia.Path()                                 # the rear wing, side on
    endplate.moveTo(8, -200)
    endplate.lineTo(132, -210)
    endplate.lineTo(130, -152)
    endplate.cubicTo(124, -124, 108, -96, 98, -70)
    endplate.lineTo(24, -60)
    endplate.close()

    fwing = skia.Path()                                    # the front wing's elements
    fwing.addRRect(rr(862, -19, 146, 10, 5))
    fwing.addRRect(rr(878, -31, 124, 8, 4))
    fwing.addRRect(rr(896, -41, 102, 7, 3.5))
    fplate = G.poly([(942, -6), (1006, -9), (1008, -48), (950, -42)])

    halo = skia.Path()
    halo.moveTo(610, -102)
    halo.cubicTo(608, -126, 592, -144, 560, -148)
    halo.lineTo(488, -142)

    top = skia.Path()                                      # where the light catches the top of the car
    top.moveTo(994, -57)
    top.cubicTo(930, -65, 780, -83, 640, -99)
    top.moveTo(452, -171)
    top.cubicTo(432, -179, 404, -178, 384, -171)
    top.cubicTo(300, -143, 180, -111, 100, -91)

    arms = [((706, -64), (812, -64)), ((712, -34), (812, -60)), ((262, -64), (176, -64)), ((252, -32), (176, -60))]
    return dict(body=body, pod=pod, inlet=inlet, stripe=stripe, endplate=endplate, fwing=fwing, fplate=fplate,
                halo=halo, top=top, arms=arms)


def _paint(col, a=1.0, x0=0.0, x1=1000.0):
    if col == "gemini":
        return G.P(WHITE, a, shader=G.linear_grad(x0, 0, x1, 0, GEMINI))
    return G.P(col, a)


def wheel(c, cx, cy, r, ang, band=WHITE, text=None, a=1.0, text_col=WHITE):
    """A tyre and its wheel cover; ang (degrees) turns it. text sits on the cover, upright."""
    if a <= 0:
        return
    c.drawCircle(cx, cy, r, G.P("#111113", a))
    c.drawCircle(cx, cy, r - 2.5, G.P("#2e2e34", a, stroke=3))
    for k in range(2):
        c.drawPath(G.arc_path(cx, cy, r * 0.8, ang + k * 180 + 20, 140), G.P(band, a, stroke=r * 0.075, cap="round"))
    rim = r * 0.6
    c.drawCircle(cx, cy, rim, G.P("#26262b", a, shader=G.radial_grad(cx - rim * 0.35, cy - rim * 0.45, rim * 1.7,
                                                                     ["#56565f", "#1b1b1f"])))
    for k in range(5):
        q = math.radians(ang + k * 72)
        c.drawLine(cx + math.cos(q) * rim * 0.3, cy + math.sin(q) * rim * 0.3, cx + math.cos(q) * rim * 0.86,
                   cy + math.sin(q) * rim * 0.86, G.P("#62626c", a * 0.8, stroke=r * 0.05, cap="round"))
    c.drawCircle(cx, cy, rim * 0.2, G.P("#8a8a94", a))
    if text:
        f = wide(r * 0.42)
        c.drawCircle(cx, cy, rim * 0.96, G.P("#141417", a))
        c.drawCircle(cx, cy, rim * 0.96, G.P(band, a, stroke=2.5))
        T(c, text, cx, cy + f.cap / 2, f, text_col, a, align=0.5)


def car(c, team, x, y, s=1.0, dist=0.0, a=1.0, lift=0.0, pitch=0.0, label=None, roll=None, wheels=True,
        wheel_text=None, band=None, shadow=0.5, sweep=None):
    """A side-on race car in a team's livery, nose to the right. (x, y) is its middle, on the ground.
    dist (screen px travelled) turns the wheels. roll = (old, new, u) rolls the label's last character.
    sweep (0..1) runs a band of light over the bodywork."""
    if a <= 0:
        return
    L = TEAMS[team]
    g = _geo()
    label = L["model"] if label is None else label
    c.save()
    if a < 1:
        c.saveLayer(None, G.P(WHITE, a))
    c.translate(x, y)
    c.scale(s, s)
    c.translate(-500, 0)
    if shadow > 0:
        c.drawOval(skia.Rect.MakeLTRB(30, -12, 1010, 10), G.P("#000000", shadow, blur=14))
        for wx in (REAR[0], FRONT[0]):
            c.drawOval(skia.Rect.MakeLTRB(wx - 66, -7, wx + 66, 6), G.P("#000000", min(1.0, shadow * 1.4), blur=4))
    c.translate(0, -lift)
    if pitch:
        c.rotate(pitch, 500, -60)

    def bodywork(cc):
        cc.drawPath(g["endplate"], _paint(L["wing"]))
        cc.drawPath(g["body"], _paint(L["body"], 1.0, 60, 1000))
        cc.save()
        cc.clipPath(g["body"], skia.ClipOp.kIntersect, True)
        cc.drawPath(g["stripe"], _paint(L["stripe"], 1.0, 100, 1000))
        cc.drawPath(g["pod"], _paint(L["pod"], 1.0, 236, 640))
        shade = G.linear_grad(0, -185, 0, -18, ["#ffffff", "#ffffff", "#000000"], stops=[0.0, 0.45, 1.0],
                              alphas=[0.22, 0.0, 0.3])
        cc.drawRect(skia.Rect.MakeLTRB(0, -200, 1010, 0), G.P(WHITE, 1, shader=shade))
        cc.restore()
        cc.drawPath(g["top"], G.P(WHITE, 0.4, stroke=2.4, cap="round"))
        cc.drawPath(g["inlet"], G.P("#050506", 0.92))
        cc.drawRect(skia.Rect.MakeLTRB(236, -22, 742, -13), G.P("#0a0a0b"))
        cc.drawRRect(rr(452, -167, 11, 19, 5), G.P("#050506", 0.75))
        cc.drawCircle(540, -121, 19, _paint(L["helmet"], 1.0, 520, 560))
        cc.drawRRect(rr(541, -129, 21, 9, 4), G.P(L["visor"]))
        cc.drawPath(g["halo"], G.P("#0b0b0c", 1, stroke=7, cap="round"))
        cc.drawPath(g["fwing"], _paint(L["wing"], 1.0, 860, 1010))
        cc.drawPath(g["fplate"], _paint(L["wing"], 1.0, 940, 1010))
        # the livery's words: the model on the sidepod, the mark on the engine cover, the code on the wing
        f = wide(30)
        if roll is None:
            T(cc, label, 436, -47, f, L["text"], align=0.5)
        else:
            old, new, u = roll
            head = label[:-1]
            wh = f.width(head)
            x0 = 436 - (wh + f.width(new)) / 2
            T(cc, head, x0, -47, f, L["text"])
            _roll_char(cc, old, new, u, x0 + wh, -47, f, L["text"])
        col = L["logo"]
        if col == "gemini":
            M.mark(cc, L["mark"], 318, -118, 34, a=1.0, shader=G.linear_grad(300, -100, 336, -136, GEMINI))
        else:
            M.mark(cc, L["mark"], 318, -118, 34, col)
        T(cc, L["code"], 72, -150, wide(30), L["text"], align=0.5)

    if sweep is not None and 0 < sweep < 1:
        G.light_sweep(c, bodywork, -200, 1200, -100, sweep, colors=("#ffffff",), width=180, strength=0.55)
    else:
        bodywork(c)
    for (x0, y0), (x1, y1) in g["arms"]:
        c.drawLine(x0, y0, x1, y1, G.P("#0b0b0c", 1, stroke=4.5, cap="round"))
    if wheels:
        ang = math.degrees(dist / (WHEEL_R * max(s, 0.05)))
        for wx, wy in (REAR, FRONT):
            wheel(c, wx, wy, WHEEL_R, ang, band or L["band"], wheel_text)
    if a < 1:
        c.restore()
    c.restore()


def wheel_spots(x, y, s=1.0, lift=0.0):
    """Screen centres of a car's rear and front wheels, and their radius (for a pit crew to take them off)."""
    return [(x + (wx - 500) * s, y + (wy - lift) * s) for wx, wy in (REAR, FRONT)], WHEEL_R * s


def _roll_char(c, a_ch, b_ch, u, x, y, font, col, a=1.0):
    """One character rolling up from a_ch to b_ch as u goes 0 -> 1, clipped to its line."""
    h = font.cap * 1.5
    e = out_cubic(clamp(u))
    w = max(font.width(a_ch), font.width(b_ch))
    with G.clip_rect(c, x - 4, y - font.cap - font.size * 0.12, w + font.size * 0.4, font.cap + font.size * 0.24):
        if e < 1:
            T(c, a_ch, x, y - h * e, font, col, a)
        T(c, b_ch, x, y + h * (1 - e), font, col, a)


def roll_text(c, head, old, new, u, x, y, font, col, a=1.0, align=0.0, tracking=0.0):
    """A line whose last character rolls from old to new."""
    wh = font.width(head, tracking)
    tw = wh + font.width(new, tracking)
    x0 = x - tw * align
    T(c, head, x0, y, font, col, a, tracking=tracking)
    _roll_char(c, old, new, u, x0 + wh + font.size * tracking, y, font, col, a)


def drive(t, t_in, t_rest, x_from, x_rest, t_out=None, x_to=3000.0, out_dur=0.55):
    """(x, dist, pitch) for a car that brakes into its spot and later launches away."""
    if t < t_rest:
        u = clamp((t - t_in) / max(1e-3, t_rest - t_in))
        e = out_quint(u)
        x = lerp(x_from, x_rest, e)
        pitch = 1.1 * math.sin(math.pi * clamp((u - 0.25) / 0.75)) if u > 0.25 else 0.0     # the nose dips
    else:
        x = x_rest
        pitch = 0.0
    if t_out is not None and t >= t_out:
        u = clamp((t - t_out) / out_dur)
        x = lerp(x_rest, x_to, in_cubic(u) * 0.85 + 0.15 * u)
        pitch = -0.9 * math.sin(math.pi * min(1.0, u * 2))                                  # squat on launch
    return x, x - x_from, pitch


# ---------------------------------------------------------------- start lights

LAMP_R = 62


@lru_cache(maxsize=None)
def lamp_image(on):
    """One start light as a baked image: an LED matrix behind glass, dark or lit."""
    r = LAMP_R
    n = 2 * (r + 10)
    surf = skia.Surface(n, n)
    with surf as cc:
        cc.clear(skia.Color4f(0, 0, 0, 0))
        cc.translate(n / 2, n / 2)
        cc.drawCircle(0, 0, r + 7, G.P("#040405"))
        cc.drawCircle(0, 0, r + 7, G.P("#34343c", 1, stroke=2))
        if on:
            sh = G.radial_grad(0, 0, r, ["#fff1ea", "#ff6a48", "#f2200f", "#8e0a04"], stops=[0.0, 0.3, 0.72, 1.0])
        else:
            sh = G.radial_grad(0, -r * 0.2, r * 1.2, ["#3b0d0c", "#1e0506", "#0e0203"])
        cc.drawCircle(0, 0, r, G.P(WHITE, 1, shader=sh))
        step = 10.0
        for iy in range(-8, 9):
            for ix in range(-8, 9):
                px = ix * step + (step / 2 if iy % 2 else 0.0)
                py = iy * step * 0.866
                d = math.hypot(px, py)
                if d > r - 6:
                    continue
                if on:
                    cc.drawCircle(px, py, 3.7, G.P(G.mixc("#fff6f0", "#ff2a14", min(1.0, d / r * 1.5))))
                else:
                    cc.drawCircle(px, py, 3.4, G.P("#4a1110", 0.9))
                    cc.drawCircle(px - 0.8, py - 0.8, 1.2, G.P("#ff8870", 0.08))
        cc.drawOval(skia.Rect.MakeXYWH(-r * 0.6, -r * 0.86, r * 1.0, r * 0.5), G.P(WHITE, 0.18 if on else 0.1,
                                                                                   blur=8))
    return surf.makeImageSnapshot()


def lamp(c, x, y, k):
    """A start light at brightness k (0 dark, 1 lit)."""
    n = 2 * (LAMP_R + 10)
    G.draw_image(c, lamp_image(False), x - n / 2, y - n / 2, n, n)
    if k > 0:
        G.draw_image(c, lamp_image(True), x - n / 2, y - n / 2, n, n, alpha=min(1.0, k))


def lamp_glow(c, x, y, k):
    """The light a lit lamp throws: a halo and an anamorphic streak."""
    if k <= 0:
        return
    r = LAMP_R
    c.drawCircle(x, y, r * 2.3, G.P(LAMP, 0.3 * k, blur=44, blend=G.ADD))
    c.drawCircle(x, y, r * 1.15, G.P("#ff6a40", 0.3 * k, blur=16, blend=G.ADD))
    streak = G.linear_grad(x - 560, 0, x + 560, 0, [LAMP, "#ff7050", LAMP], alphas=[0.0, 1.0, 0.0])
    c.drawRect(skia.Rect.MakeLTRB(x - 560, y - 2.5, x + 560, y + 2.5), G.P(LAMP, 0.45 * k, shader=streak, blur=3,
                                                                           blend=G.ADD))
    wide_streak = G.linear_grad(x - 900, 0, x + 900, 0, [LAMP, LAMP, LAMP], alphas=[0.0, 1.0, 0.0])
    c.drawRect(skia.Rect.MakeLTRB(x - 900, y - 16, x + 900, y + 16), G.P(LAMP, 0.1 * k, shader=wide_streak, blur=12,
                                                                          blend=G.ADD))


# ---------------------------------------------------------------- the track

def track(c, t, dist, horizon=460.0, a=1.0, hc=1.5, half=5.2, f=950.0, sky=("#050509", "#140a10"),
          asphalt=("#1b1b21", "#101014"), kerbs=(RED, WHITE), lights=True, grid_boxes=False, lines_every=24.0):
    """A night straight seen from the car: sky, floodlights, asphalt, kerbs streaming past on both sides.
    dist is how far the camera has driven (metres)."""
    if a <= 0:
        return
    cx = 960.0
    if sky is not None:
        c.drawRect(skia.Rect.MakeLTRB(0, 0, 1920, horizon + 2), G.P(sky[0], a, shader=G.linear_grad(
            0, 0, 0, horizon, [sky[0], sky[1]])))
    if lights:
        for i in range(9):
            lx = 80 + i * 225 + 40 * math.sin(i * 2.3)
            ly = horizon - 60 - 50 * float(hash01(i, 3))
            c.drawCircle(lx, ly, 70, G.P("#ffd9b0", 0.08 * a, blur=40, blend=G.ADD))
            c.drawCircle(lx, ly, 4, G.P("#fff4e0", 0.9 * a))
            c.drawLine(lx, ly + 4, lx, horizon, G.P("#2a2a33", a, stroke=2))

    def proj(X, Z):
        return cx + f * X / Z, horizon + f * hc / Z

    z_near = f * hc / (1080 - horizon) * 0.8
    z_far = 900.0
    c.drawRect(skia.Rect.MakeLTRB(0, horizon, 1920, 1080), G.P("#09090c", a))          # the run-off, both sides
    p = G.poly([proj(-half * 3, z_far), proj(half * 3, z_far), proj(half * 3, z_near), proj(-half * 3, z_near)])
    c.drawPath(p, G.P(asphalt[0], a, shader=G.linear_grad(0, horizon, 0, 1080, [asphalt[1], asphalt[0]])))
    # the kerbs: 3 m blocks, both sides, streaming past
    blk = 3.0
    k0 = math.floor(dist / blk)
    for side in (-1, 1):
        xa, xb = side * half, side * (half + 1.3)
        for k in range(k0, k0 + 150):
            z0 = k * blk - dist
            z1 = z0 + blk
            if z1 <= z_near * 0.8:
                continue
            z0 = max(z0, z_near * 0.8)
            col = kerbs[k % 2]
            pa, pb = proj(xa, z0), proj(xb, z0)
            pc, pd = proj(xb, z1), proj(xa, z1)
            c.drawPath(G.poly([pa, pb, pc, pd]), G.P(col, a * (0.9 if col == WHITE else 1.0)))
        # the white line inside the kerb
        q = G.poly([proj(side * (half - 0.25), z_near * 0.8), proj(side * half, z_near * 0.8),
                    proj(side * half, z_far), proj(side * (half - 0.25), z_far)])
        c.drawPath(q, G.P(WHITE, a * 0.85))
    # lines across the track
    k0 = math.floor(dist / lines_every)
    for k in range(k0, k0 + 40):
        z0 = k * lines_every - dist
        if z0 <= z_near * 0.8:
            continue
        z1 = z0 + 0.5
        if grid_boxes:
            for side in (-1, 1):
                xa, xb = side * 0.6, side * (half - 0.9)
                c.drawPath(G.poly([proj(xa, z0), proj(xb, z0), proj(xb, z1), proj(xa, z1)]), G.P(WHITE, a * 0.8))
        else:
            c.drawPath(G.poly([proj(-half, z0), proj(half, z0), proj(half, z1), proj(-half, z1)]),
                       G.P(WHITE, a * 0.35))
    # the far end melts into the dark
    haze = sky[1] if sky is not None else asphalt[1]
    c.drawRect(skia.Rect.MakeLTRB(0, horizon - 2, 1920, horizon + 60), G.P(haze, a, shader=G.linear_grad(
        0, horizon, 0, horizon + 60, [haze, haze], alphas=[1.0, 0.0])))


# ---------------------------------------------------------------- team radio, race control

def waveform(c, x, y, w, h, t, level, col, n=26, a=1.0):
    bw = w / n
    for i in range(n):
        v = level * (0.25 + 0.75 * abs(math.sin(t * 11.0 + i * 0.9) * math.sin(t * 6.3 + i * 0.37)))
        bh = h * max(0.1, v)
        c.drawRRect(rr(x + i * bw + bw * 0.22, y - bh / 2, bw * 0.56, bh, bw * 0.28), G.P(col, a))


def radio(c, x, y, w, team, who, lines, t, t0, t1=None, a=1.0, talk=None, title="TEAM RADIO"):
    """A radio graphic: a dark panel with the team's edge, whose channel it is, a live waveform, and the words in
    quotes landing word by word. lines: [(t_line, text, colour)]. talk: (t_start, t_end) of the speech."""
    if t < t0:
        return
    col = TEAMS[team]["col"]
    ink = TEAMS[team]["ink"]
    lh = 60
    h = radio_height(len(lines))
    l, r = wipe(t, t0, 0.36, t1)
    path = slab(c, x, y, w, h, PANEL, a * 0.96, l=l, r=r, lean=0.0)
    if path is None:
        return
    slab(c, x, y, 12, h, col, a, l=0, r=1 if r > 0.05 else 0, lean=0.0)
    c.save()
    c.clipPath(path, skia.ClipOp.kIntersect, True)
    tw = tab(c, x + 30, y + 40, title, cond(26, 760), col, ink, t, t0 + 0.08, tracking=0.1)
    slide(c, who, x + 30 + tw + 18, y + 49, cond(26, 640), GREY, t, t0 + 0.14, tracking=0.08)
    lvl = 0.0
    if talk is not None:
        lvl = clamp((t - talk[0]) / 0.1) * (1 - clamp((t - talk[1]) / 0.2))
    waveform(c, x + w - 230, y + 40, 190, 34, t, 0.2 + 0.8 * lvl, col, a=a * clamp((t - t0 - 0.1) / 0.2))
    fq = cond_i(50, 800)
    for i, (tl, text, tc) in enumerate(lines):
        words(c, text, x + 34, y + 128 + i * lh, fq, tc, t, tl, step=0.075, a=a, tracking=0.01)
    c.restore()


def radio_height(n_lines):
    return 86 + 60 * n_lines


def flag_icon(c, x, y, s, col, t=0.0, a=1.0):
    """A small flag on its pole, waving."""
    c.drawLine(x, y - s * 0.55, x, y + s * 0.55, G.P("#d8d8de", a, stroke=s * 0.1, cap="round"))
    p = skia.Path()
    w = s * 0.9
    ph = t * 8.0
    p.moveTo(x, y - s * 0.52)
    p.cubicTo(x + w * 0.35, y - s * 0.52 - s * 0.12 * math.sin(ph), x + w * 0.65, y - s * 0.52 + s * 0.12 * math.sin(ph),
              x + w, y - s * 0.52)
    p.lineTo(x + w, y)
    p.cubicTo(x + w * 0.65, y + s * 0.12 * math.sin(ph), x + w * 0.35, y - s * 0.12 * math.sin(ph), x, y)
    p.close()
    c.drawPath(p, G.P(col, a))


def race_control(c, x, y, w, msg, t, t0, t1=None, a=1.0):
    """RACE CONTROL: a yellow flag, the header, the message."""
    if t < t0:
        return
    hh, mh = 46, 74
    l, r = wipe(t, t0, 0.34, t1)
    path = slab(c, x, y, w * 0.52, hh, "#1c1c22", a, l=l, r=r)
    if path is not None:
        c.save()
        c.clipPath(path, skia.ClipOp.kIntersect, True)
        flag_icon(c, x + 34, y + hh / 2, 26, YELLOW, t, a)
        T(c, "RACE CONTROL", x + 70 - (1 - r) * 40, y + hh / 2 + cond(26).cap / 2, cond(26, 760), WHITE, a,
          tracking=0.1)
        c.restore()
    l2, r2 = wipe(t, t0 + 0.1, 0.36, t1)
    path = slab(c, x - hh * SLANT, y + hh, w, mh, WHITE, a, l=l2, r=r2)
    if path is not None:
        c.save()
        c.clipPath(path, skia.ClipOp.kIntersect, True)
        slab(c, x - hh * SLANT, y + hh, 12, mh, YELLOW, a)
        fm = wide(34)
        slide(c, msg, x + 20, y + hh + mh / 2 + fm.cap / 2, fm, INK, t, t0 + 0.2, a=a)
        c.restore()


# ---------------------------------------------------------------- team bosses

@lru_cache(maxsize=None)
def card_image(key, w, h):
    """The founder's crop, scaled to cover w x h and gently sharpened."""
    p = os.path.join(PHOTOS, FOUNDERS[key]["file"])
    if not os.path.exists(p):
        return None
    im = cv2.imread(p)
    x0, y0, x1, y1 = FOUNDERS[key]["crop"]
    im = im[y0:min(y1, im.shape[0]), x0:min(x1, im.shape[1])]
    s = max(w / im.shape[1], h / im.shape[0])
    nw, nh = int(round(im.shape[1] * s)), int(round(im.shape[0] * s))
    im = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    ox, oy = (nw - w) // 2, 0
    im = im[oy:oy + h, ox:ox + w]
    if s > 1.2:
        blur = cv2.GaussianBlur(im, (0, 0), 1.0 + 0.4 * s)
        im = cv2.addWeighted(im, 1.45, blur, -0.45, 0)
    return G.image_from_rgba(cv2.cvtColor(im, cv2.COLOR_BGR2RGBA))


def boss(c, key, x, y, w, h, team, t, t0, t1=None, a=1.0, tag="TEAM BOSS"):
    """A team-boss card: the photo in a slanted frame with the team's edge, then the name and the role under it."""
    if t < t0 or a <= 0:
        return
    f = FOUNDERS[key]
    col = TEAMS[team]["col"]
    ink = TEAMS[team]["ink"]
    l, r = wipe(t, t0, 0.5, t1)
    frame = slab(c, x, y, w, h, "#1a1a20", a, l=l, r=r)
    if frame is not None:
        img = card_image(key, int(w + h * SLANT) + 2, int(h))
        c.save()
        c.clipPath(frame, skia.ClipOp.kIntersect, True)
        if img is not None:
            kb = lerp(1.14, 1.0, out_cubic(clamp((t - t0) / 1.8)))
            e = out_expo(clamp((t - t0) / 0.6))
            iw, ih = img.width() * kb, img.height() * kb
            G.draw_image(c, img, x + (w + h * SLANT - iw) / 2, y + h - ih + 60 * (1 - e), iw, ih, alpha=a)
        # a little shade at the foot so the name bars sit on it
        c.drawRect(skia.Rect.MakeXYWH(x, y + h * 0.6, w + h * SLANT, h * 0.4), G.P("#000000", 1, shader=G.linear_grad(
            0, y + h * 0.6, 0, y + h, ["#000000", "#000000"], alphas=[0.0, 0.45 * a])))
        c.restore()
        slab(c, x - 16, y, 12, h, col, a, l=0, r=1 if r > 0.1 else 0)
    tab(c, x + h * SLANT + 14, y + 26, tag, cond(22, 760), col, ink, t, t0 + 0.2, t1=t1, tracking=0.12)
    fn = wide(30)
    name = f["name"].upper()
    nw = fn.width(name) + 44
    l2, r2 = wipe(t, t0 + 0.22, 0.4, t1)
    bar = slab(c, x - 34, y + h + 10, nw, 58, "#101014", a, l=l2, r=r2)
    if bar is not None:
        c.save()
        c.clipPath(bar, skia.ClipOp.kIntersect, True)
        T(c, name, x - 34 + 22 + 58 * SLANT - (1 - r2) * 50, y + h + 10 + 29 + fn.cap / 2, fn, WHITE, a)
        c.restore()
    fr = cond(23, 680)
    role = f["role"].upper()
    rw = fr.width(role, 0.08) + 36
    l3, r3 = wipe(t, t0 + 0.34, 0.4, t1)
    bar = slab(c, x - 46, y + h + 68, rw, 40, col, a, l=l3, r=r3)
    if bar is not None:
        c.save()
        c.clipPath(bar, skia.ClipOp.kIntersect, True)
        T(c, role, x - 46 + 18 + 40 * SLANT - (1 - r3) * 40, y + h + 68 + 20 + fr.cap / 2, fr, ink, a, tracking=0.08)
        c.restore()


# ---------------------------------------------------------------- lap counter, bug

def lap_group(c, x, y, s, t, t_flip, a=1.0, red=RED):
    """LAP 39/??? rolling to 40: the lap of this race is the week of the year. Centred on (x, y) at scale s."""
    if a <= 0 or s <= 0.01:
        return
    fl, fd, fq = cond(70, 760), wide(190, 880), cond(96, 760)
    wl, wd, wq = fl.width("LAP", 0.06), fd.width("40", features={"tnum": True}), fq.width("/???")
    gap = 26
    total = wl + gap + wd + 10 + wq
    pad_x, h = 70, 250
    w = total + 2 * pad_x
    with G.xf(c, x, y, s=s):
        slab(c, -w / 2, -h / 2, w, h, red, a)
        x0 = -total / 2 + h * SLANT * 0.5
        base = fd.cap / 2
        T(c, "LAP", x0, base, fl, WHITE, a * 0.85, tracking=0.06)
        u = clamp((t - t_flip) / 0.32)
        xd = x0 + wl + gap
        if u <= 0:
            T(c, "39", xd, base, fd, WHITE, a, tnum=True)
        else:
            w3 = fd.width("3", features={"tnum": True})
            _roll_char(c, "3", "4", u, xd, base, fd, WHITE, a)
            _roll_char(c, "9", "0", clamp(u * 1.15 - 0.1), xd + w3, base, fd, WHITE, a)
        T(c, "/???", xd + wd + 10, base, fq, WHITE, a * 0.6)
        k = (t - t_flip) / 0.35
        if 0 <= k < 1:
            slab(c, -w / 2, -h / 2, w, h, WHITE, a * 0.6 * (1 - k) ** 2)


BUG_X, BUG_Y, BUG_H = 54.0, 44.0, 50.0


def bug_width():
    f1 = cond_i(27, 820)
    return f1.width("THE RACE TO AGI", 0.04) + 36 + BUG_H * SLANT


def bug_lap_width():
    fl, fd = cond(22, 700), wide(30, 860)
    return fl.width("LAP", 0.1) + 12 + fd.width("40", features={"tnum": True}) + 8 + fl.width("/???") + 40


def bug_lap_centre():
    """Where the bug's LAP 40/??? sits, for the big counter to fly into."""
    return BUG_X + bug_width() - 2 + (bug_lap_width() + BUG_H * SLANT) / 2, BUG_Y + BUG_H / 2


def bug(c, t, t0, a=1.0):
    """The broadcast bug, top left: the show, the lap (= week 40 of the year), and the dates."""
    if t < t0 or a <= 0:
        return
    x, y, h = BUG_X, BUG_Y, BUG_H
    f1 = cond_i(27, 820)
    w1 = bug_width()
    l, r = wipe(t, t0, 0.34)
    p = slab(c, x, y, w1, h, RED, a, l=l, r=r)
    if p is not None:
        c.save()
        c.clipPath(p, skia.ClipOp.kIntersect, True)
        T(c, "THE RACE TO AGI", x + 18 + h * SLANT * 0.5 - (1 - r) * 30, y + h / 2 + f1.cap / 2, f1, WHITE, a,
          tracking=0.04)
        c.restore()
    fl, fd = cond(22, 700), wide(30, 860)
    w2 = bug_lap_width()
    l, r = wipe(t, t0 + 0.08, 0.34)
    p = slab(c, x + w1 - 2, y, w2, h, PANEL, a * 0.94, l=l, r=r)
    if p is not None:
        c.save()
        c.clipPath(p, skia.ClipOp.kIntersect, True)
        xx = x + w1 + 16 + h * SLANT * 0.5 - (1 - r) * 30
        T(c, "LAP", xx, y + h / 2 + fl.cap / 2, fl, GREY, a, tracking=0.1)
        xx += fl.width("LAP", 0.1) + 12
        T(c, "40", xx, y + h / 2 + fd.cap / 2, fd, WHITE, a, tnum=True)
        xx += fd.width("40", features={"tnum": True}) + 8
        T(c, "/???", xx, y + h / 2 + fl.cap / 2, fl, GREY, a)
        c.restore()
    fw = cond(20, 640)
    l, r = wipe(t, t0 + 0.16, 0.34)
    p = slab(c, x - h * SLANT * 0.62, y + h + 6, w1 + w2 - 40, 32, PANEL, a * 0.9, l=l, r=r)
    if p is not None:
        c.save()
        c.clipPath(p, skia.ClipOp.kIntersect, True)
        T(c, "WEEK 40  ·  SEP 28 – OCT 4", x + 12 - (1 - r) * 30, y + h + 6 + 16 + fw.cap / 2, fw, WHITE, a * 0.85,
          tracking=0.12)
        c.restore()


def live(c, t, t0, a=1.0):
    """LIVE, top right, the dot breathing."""
    if t < t0 or a <= 0:
        return
    f = cond(24, 760)
    w = f.width("LIVE", 0.14) + 74
    x = 1920 - 54 - w
    y, h = BUG_Y, BUG_H
    l, r = wipe(t, t0, 0.34)
    p = slab(c, x, y, w, h, PANEL, a * 0.94, l=l, r=r)
    if p is None:
        return
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    pulse = 0.5 + 0.5 * math.cos(t * 5.0)
    c.drawCircle(x + 32, y + h / 2, 8, G.P(RED, a * (0.55 + 0.45 * pulse)))
    c.drawCircle(x + 32, y + h / 2, 8 + 7 * (1 - pulse), G.P(RED, a * 0.3 * pulse))
    T(c, "LIVE", x + 50, y + h / 2 + f.cap / 2, f, WHITE, a, tracking=0.14)
    c.restore()


# ---------------------------------------------------------------- shift lights, gauge

LED_COLS = [GREEN] * 5 + [RED] * 5 + [BLUE_LED] * 5


def shift_lights(c, cx, cy, lit, t, flash=0.0, a=1.0, spacing=70.0, r=21.0):
    """Fifteen LEDs over a carbon bar: five green, five red, five blue. `lit` of them are on (the last one partly);
    `flash` blinks the whole row blue: shift."""
    if a <= 0:
        return
    w = spacing * 15 + 70
    c.drawRRect(rr(cx - w / 2, cy - 44, w, 88, 14), G.P("#0c0c10", a * 0.96))
    c.drawRRect(rr(cx - w / 2, cy - 44, w, 88, 14), G.P("#2c2c36", a, stroke=2))
    blink = flash > 0 and math.sin(t * 2 * math.pi * 8.0) > -0.2
    for i in range(15):
        x = cx + (i - 7) * spacing
        on = clamp(lit - i)
        col = LED_COLS[i]
        if flash > 0:
            col, on = BLUE_LED, (1.0 if blink else 0.15) * flash
        c.drawCircle(x, cy, r + 5, G.P("#030304", a))
        c.drawCircle(x, cy, r, G.P(G.mixc(col, "#000000", 0.82), a))
        if on > 0:
            c.drawCircle(x, cy, r * 2.3, G.P(col, 0.4 * on * a, blur=18, blend=G.ADD))
            c.drawCircle(x, cy, r, G.P(col, a * on, shader=G.radial_grad(x - r * 0.25, cy - r * 0.3, r * 1.2,
                                                                         ["#ffffff", col, col], stops=[0.0, 0.45, 1.0])))


def gauge(c, cx, cy, R, v, t, label, a=1.0, value=None):
    """An arc gauge, 240 degrees, filling green to red to blue as v goes 0 -> 1, with its needle."""
    if a <= 0:
        return
    start, sweep = 150.0, 240.0
    c.drawPath(G.arc_path(cx, cy, R, start, sweep), G.P("#1a1a24", a, stroke=34, cap="butt"))
    for k in range(25):
        q = math.radians(start + sweep * k / 24)
        r0 = R - 36 if k % 4 == 0 else R - 28
        c.drawLine(cx + math.cos(q) * r0, cy + math.sin(q) * r0, cx + math.cos(q) * (R - 20),
                   cy + math.sin(q) * (R - 20), G.P(WHITE, a * (0.7 if k % 4 == 0 else 0.3), stroke=3))
    if v > 0:
        # the sweep runs 0..sweep degrees, turned to start where the arc does (sweeps cannot cross 360)
        sh = skia.GradientShader.MakeSweep(cx, cy, [G.cint(GREEN), G.cint(GREEN), G.cint(RED), G.cint(BLUE_LED),
                                                    G.cint(BLUE_LED)], [0.0, 0.42, 0.72, 0.9, 1.0],
                                           skia.TileMode.kClamp, 0.0, sweep, 0,
                                           skia.Matrix.RotateDeg(start, skia.Point(cx, cy)))
        arc = G.arc_path(cx, cy, R, start, sweep * clamp(v))
        c.drawPath(arc, G.P(WHITE, a, stroke=34, shader=sh))
        c.drawPath(arc, G.P(WHITE, a * 0.35, stroke=60, shader=sh, blur=18, blend=G.ADD))
    q = math.radians(start + sweep * clamp(v) + 1.5 * math.sin(t * 60) * clamp(v - 0.9) * 10)
    c.drawLine(cx, cy, cx + math.cos(q) * (R - 50), cy + math.sin(q) * (R - 50), G.P(WHITE, a, stroke=6, cap="round"))
    c.drawCircle(cx, cy, 16, G.P(WHITE, a))
    c.drawCircle(cx, cy, 7, G.P(RED, a))
    fl = cond(28, 720)
    T(c, label, cx, cy + R * 0.62, fl, GREY, a, align=0.5, tracking=0.16)
    if value is not None:
        fv = wide(58)
        T(c, value, cx, cy + R * 0.62 + 70, fv, WHITE, a, align=0.5)


# ---------------------------------------------------------------- the pit board

def pit_board(c, x, y, rows, t, t0, a=1.0, sway=0.0):
    """The board a team hangs over the pit wall for its driver: rows of big letters that clack in one by one.
    rows: [(t_row, text, colour)]. (x, y) is the board's top left once it is up."""
    if t < t0 or a <= 0:
        return
    w, rh = 400, 124
    h = len(rows) * rh + 48
    e = out_expo(clamp((t - t0) / 0.6))
    oy = (1 - e) * 1100
    with G.xf(c, x + w / 2, y + h + 700 + oy, rot=sway):
        c.drawRect(skia.Rect.MakeLTRB(-9, -700, 9, 400), G.P("#8f9098", a, shader=G.linear_grad(-9, 0, 9, 0, [
            "#5d5e66", "#c8c9d0", "#6a6b73"])))
        bx, by = -w / 2, -700 - h
        c.drawRRect(rr(bx + 10, by + 18, w, h, 12), G.P("#000000", 0.45 * a, blur=16))
        c.drawRRect(rr(bx, by, w, h, 12), G.P("#0b0b0d", a))
        c.drawRRect(rr(bx + 12, by + 12, w - 24, h - 24, 6), G.P("#e8e8ec", a, stroke=5))
        f = cond(112, 820)
        for i, (tr, text, col) in enumerate(rows):
            k = clamp((t - tr) / 0.14)
            if k <= 0:
                continue
            cy = by + 24 + rh * i + rh / 2
            with G.xf(c, 0, cy, sy=max(0.02, out_cubic(k))):
                T(c, text, 0, f.cap / 2, f, col, a, align=0.5, tracking=0.04)


# ---------------------------------------------------------------- the chequered flag

def chequered(c, t, cx, cy, w, h, n=12, m=8, rot=-4.0, a=1.0, wind=1.0, sub=3):
    """A chequered flag in the wind: squares on a travelling wave, each piece shaded by the fold it sits on."""
    if a <= 0:
        return
    N, Mm = n * sub, m * sub
    pts = []
    for j in range(Mm + 1):
        row = []
        v = j / Mm
        for i in range(N + 1):
            u = i / N
            ph = 7.5 * u - 8.5 * t + 1.6 * v
            amp = wind * (0.015 + 0.085 * u) * h
            px = (u - 0.5) * w - amp * 0.4 * (1 - math.cos(ph))
            py = (v - 0.5) * h + amp * math.sin(ph)
            row.append((px, py, math.cos(ph) * (0.25 + 0.75 * u)))
        pts.append(row)
    with G.xf(c, cx, cy, rot=rot):
        for j in range(Mm):
            for i in range(N):
                p00, p10, p11, p01 = pts[j][i], pts[j][i + 1], pts[j + 1][i + 1], pts[j + 1][i]
                sh = (p00[2] + p10[2] + p11[2] + p01[2]) / 4
                white = ((i // sub) + (j // sub)) % 2 == 0
                lum = (0.82 + 0.16 * sh) if white else (0.07 + 0.08 * (sh + 1) / 2)
                path = G.poly([p00[:2], p10[:2], p11[:2], p01[:2]])
                col = (lum, lum, lum)
                c.drawPath(path, G.P(col, a))
                c.drawPath(path, G.P(col, a, stroke=1.2))
