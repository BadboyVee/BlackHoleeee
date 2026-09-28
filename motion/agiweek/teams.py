"""THE RACE TO AGI, bars 5-12: the teams.

Anthropic on ivory, with the paddock talk: Sonnet 5.5 expected today. OpenAI on white with two new entries, a new
model and Agent "O", and race control's note that DevDay is tomorrow. Gemini and Muse also on the grid, wheel to
wheel on a split screen. xAI in the pits: the 4.7s come off, the 4.8s go on, and it might go out this week.
Every car wears its lab's livery with its model on the sidepod; every team boss gets a card."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, out_cubic, out_expo
from . import broadcast as B
from . import motion as V
from .look import blob
from .score import (T_ANT, T_ANT_RADIO, T_ANT_LINE1, T_ANT_BOSS, T_ANT_LINE2, T_OAI, T_OAI_CAR2, T_OAI_BOSS, T_RC,
                    T_GRID2, T_STRAP, T_GDM_BOSS, T_MTA_BOSS, T_XAI, T_BOX, T_OFF, T_ON, T_JACK, T_XAI_BOSS,
                    T_LAUNCH)


def model_title(c, lines, x, y, size, col, t, t0, step=0.14, gap=None, shader=None, shadow=None):
    """The model, big, arriving like a car."""
    f = B.wide(size)
    for i, s in enumerate(lines):
        B.slam(c, s, x, y + i * (gap or size * 0.98), f, col, t, t0 + i * step, dur=0.6, dist=1200, shader=shader,
               shadow=shadow)


def company_line(c, team, x, y, col, t, t0, chip=None, chip_fill=None, chip_ink=None, size=34, mark_col=None,
                 chip_t=None):
    """The company under its model: the mark, the name, and a status tab."""
    fc = B.cond(size, 760)
    u = clamp((t - t0) / 0.3)
    if u > 0:
        B.mark(c, team, x + size * 0.55 - 20 * (1 - out_cubic(u)), y - fc.cap / 2, size * 1.15, col=mark_col, a=u)
    name = B.TEAMS[team]["company"]
    B.slide(c, name, x + size * 1.4, y, fc, col, t, t0 + 0.05, tracking=0.14)
    if chip:
        B.tab(c, x + size * 1.4 + fc.width(name, 0.14) + 28, y - fc.cap / 2, chip, B.cond(size * 0.78, 780),
              chip_fill, chip_ink, t, chip_t if chip_t is not None else t0 + 0.22, tracking=0.12)


# ---------------------------------------------------------------- Anthropic

def anthropic(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P(B.IVORY))
    blob(c, 1560, 260, 980, B.CLAY, 0.2)
    B.pinstripes(c, t, B.CLAY, 0.13, gap=42, width=2.0, x0=1080)
    c.drawRect(skia.Rect.MakeLTRB(0, 900, 1920, 1080), G.P("#e5e1d5"))
    B.kerb(c, 0, 1920, 900, 14, [B.CLAY, B.IVORY], block=72)
    x, dist, pitch = B.drive(t, T_ANT - 0.42, T_ANT + 0.5, -900, 1190, t_out=T_OAI - 0.62)
    sweep = (t - (T_ANT + 0.6)) / 0.9
    B.car(c, "anthropic", x, 900, s=0.96, dist=dist, pitch=pitch, sweep=sweep, shadow=0.35)
    model_title(c, ["SONNET 5.5"], 110, 318, 124, B.INK, t, T_ANT - 0.08)
    company_line(c, "anthropic", 116, 398, B.CLAY, t, T_ANT + 0.18, chip="EXPECTED TODAY", chip_fill=B.CLAY,
                 chip_ink=B.IVORY, mark_col=B.CLAY)
    B.radio(c, 110, 462, 840, "anthropic", "ANTHROPIC  ·  SONNET 5.5",
            [(T_ANT_LINE1, "“SONNET 5.5 EXPECTED TODAY.”", B.WHITE),
             (T_ANT_LINE2, "“BIG STEP UP. A FABLE MOMENT?”", B.CLAY)],
            t, T_ANT_RADIO, talk=(T_ANT_LINE1 - 0.05, T_ANT_LINE2 + 0.9), title="PADDOCK TALK")
    B.boss(c, "amodei", 1240, 118, 470, 324, "anthropic", t, T_ANT_BOSS, tag="TEAM BOSSES")


# ---------------------------------------------------------------- OpenAI

def openai(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#f4f4f5"))
    B.pinstripes(c, t, "#dfdfe3", 1.0, gap=38, width=1.6)
    blob(c, 700, 300, 900, "#ffffff", 0.8)
    c.drawRect(skia.Rect.MakeLTRB(0, 960, 1920, 1080), G.P("#e6e6e9"))
    B.kerb(c, 0, 1920, 960, 14, ["#0e0e10", "#ffffff"], block=72)
    c.drawLine(0, 772, 1920, 772, G.P("#d4d4d9", 1, stroke=2))
    xa, da, pa = B.drive(t, T_OAI - 0.45, T_OAI + 0.45, -800, 700, t_out=T_GRID2 - 0.66)
    B.car(c, "openai", xa, 772, s=0.64, dist=da, pitch=pa, label="NEW MODEL", shadow=0.3)
    xb, db, pb = B.drive(t, T_OAI_CAR2 - 0.4, T_OAI_CAR2 + 0.45, -800, 1230, t_out=T_GRID2 - 0.58)
    B.car(c, "openai", xb, 960, s=0.8, dist=db, pitch=pb, label="AGENT “O”", shadow=0.35,
          sweep=(t - (T_OAI_CAR2 + 0.6)) / 0.9)
    model_title(c, ["NEW MODEL"], 110, 300, 110, "#0d0d0d", t, T_OAI - 0.08)
    model_title(c, ["+ AGENT “O”"], 110, 408, 110, "#0d0d0d", t, T_OAI_CAR2 - 0.05)
    company_line(c, "openai", 116, 484, "#0d0d0d", t, T_OAI + 0.2, chip="TWO NEW ENTRIES", chip_fill="#0d0d0d",
                 chip_ink=B.WHITE, mark_col="#0d0d0d")
    B.boss(c, "altman", 1460, 124, 290, 322, "openai", t, T_OAI_BOSS)
    B.race_control(c, 110, 930, 760, "OPENAI DEVDAY: TOMORROW", t, T_RC)


# ---------------------------------------------------------------- also on the grid: Gemini, Muse

DIV = (566.0, 514.0)          # the split runs from (0, 566) to (1920, 514)


def top_half():
    return G.poly([(0, 0), (1920, 0), (1920, DIV[1]), (0, DIV[0])])


def bottom_half():
    return G.poly([(0, DIV[0]), (1920, DIV[1]), (1920, 1080), (0, 1080)])


def gemini_ground(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#0f1a4a", 1, shader=G.linear_grad(0, 0, 1920, 540, [
        "#0d1a52", "#23206a", "#3b1d6b"])))
    blob(c, 1300 + 120 * math.sin(t * 0.7), 160, 700, "#4285f4", 0.45)
    blob(c, 1750, 420, 520, "#d96570", 0.3)
    blob(c, 420, 80, 600, "#9b72cb", 0.3)
    B.pinstripes(c, t, B.WHITE, 0.05, gap=44)


def meta_ground(c, t):
    c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#0866ff", 1, shader=G.linear_grad(0, 540, 1920, 1080, [
        "#1a7dff", "#0866ff", "#0047c7"])))
    blob(c, 600 + 100 * math.sin(t * 0.6), 1000, 800, "#6fb3ff", 0.35)
    B.pinstripes(c, -t, B.WHITE, 0.06, gap=44)


def grid2_top(c, t):
    gemini_ground(c, t)
    x, dist, pitch = B.drive(t, T_GRID2 - 0.42, T_GRID2 + 0.5, -800, 1000, t_out=T_XAI - 0.62)
    B.car(c, "google", x, 488, s=0.62, dist=dist, pitch=pitch, shadow=0.45, sweep=(t - (T_GRID2 + 0.6)) / 0.9)
    model_title(c, ["GEMINI"], 110, 250, 130, B.WHITE, t, T_GRID2 - 0.08)
    company_line(c, "google", 116, 322, B.WHITE, t, T_GRID2 + 0.2, mark_col="gemini")
    B.boss(c, "hassabis", 1380, 72, 250, 278, "google", t, T_GDM_BOSS)


def grid2_bottom(c, t):
    meta_ground(c, t)
    x, dist, pitch = B.drive(t, T_GRID2 - 0.36, T_GRID2 + 0.56, -800, 1000, t_out=T_XAI - 0.58)
    B.car(c, "meta", x, 1030, s=0.62, dist=dist, pitch=pitch, shadow=0.45, sweep=(t - (T_GRID2 + 0.7)) / 0.9)
    model_title(c, ["MUSE"], 110, 790, 130, B.WHITE, t, T_GRID2 + 0.04)
    company_line(c, "meta", 116, 862, B.WHITE, t, T_GRID2 + 0.3, mark_col=B.WHITE)
    B.boss(c, "zuckerberg", 1380, 598, 250, 278, "meta", t, T_MTA_BOSS)


def grid2(c, t):
    c.save()
    c.clipPath(top_half(), skia.ClipOp.kIntersect, True)
    grid2_top(c, t)
    c.restore()
    c.save()
    c.clipPath(bottom_half(), skia.ClipOp.kIntersect, True)
    grid2_bottom(c, t)
    c.restore()
    c.drawLine(0, DIV[0], 1920, DIV[1], G.P(B.WHITE, 1, stroke=6))
    B.tab(c, 960, 540, "ALSO ON THE GRID", B.cond_i(32, 820), B.RED, B.WHITE, t, T_STRAP, align=0.5,
          tracking=0.1)


# ---------------------------------------------------------------- xAI: the pit stop

def pit_lift(t):
    """How far the jacks hold the car up."""
    if t < T_BOX + 0.06:
        return 0.0
    up = out_expo(clamp((t - T_BOX - 0.06) / 0.12))
    down = clamp((t - T_JACK) / 0.08)
    return 12.0 * up * (1 - down)


def pit_ground(c, t):
    c.drawRect(skia.Rect.MakeLTRB(0, 0, 1920, 640), G.P("#16161b", 1, shader=G.linear_grad(0, 0, 0, 640, [
        "#1e1e25", "#121217"])))
    for k in range(9):
        x = 120 + k * 240
        c.drawRect(skia.Rect.MakeLTRB(x, 150, x + 3, 640), G.P("#23232b"))
    c.drawRect(skia.Rect.MakeLTRB(0, 92, 1920, 104), G.P(B.WHITE, 0.95))
    c.drawRect(skia.Rect.MakeLTRB(0, 70, 1920, 150), G.P(B.WHITE, 0.16, blur=22))
    blob(c, 960, 110, 1200, "#dfe6ff", 0.1)
    c.drawRect(skia.Rect.MakeLTRB(0, 610, 1920, 640), G.P("#2a2a33"))
    c.drawRect(skia.Rect.MakeLTRB(0, 640, 1920, 1080), G.P("#0f0f13", 1, shader=G.linear_grad(0, 640, 0, 1080, [
        "#18181e", "#09090c"])))
    c.drawRect(skia.Rect.MakeLTRB(0, 650, 1920, 720), G.P(B.WHITE, 0.05, blur=20))
    # the pit box painted on the floor, in perspective, and the stop line
    near, far = 1010.0, 800.0
    box = G.poly([(470, far), (1550, far), (1650, near), (370, near)])
    c.drawPath(box, G.P(B.YELLOW, 0.9, stroke=9, join="round"))
    c.drawLine(1525, far, 1612, near, G.P(B.WHITE, 0.9, stroke=12))
    fb = B.wide(66)
    with G.xf(c, 960, 978, sx=1.0, sy=0.42):
        B.T(c, "X A I", 0, 0, fb, B.WHITE, 0.08, align=0.5, tracking=0.2)


def xai(c, t):
    pit_ground(c, t)
    x, dist, pitch = B.drive(t, T_XAI - 0.45, T_BOX, -900, 1010, t_out=T_LAUNCH, x_to=3300, out_dur=0.45)
    lift = pit_lift(t)
    stopped = T_BOX <= t < T_LAUNCH
    off = clamp((t - T_OFF) / 0.24)
    on = clamp((t - (T_ON - 0.2)) / 0.2)
    rolled = clamp((t - T_ON) / 0.3)
    B.car(c, "xai", x, 900, s=1.0, dist=dist, pitch=pitch if not stopped else 0.0, lift=lift, wheels=False,
          roll=("7", "8", rolled), label="GROK 4.8", sweep=(t - (T_JACK + 0.1)) / 0.9, shadow=0.55)
    spots, r = B.wheel_spots(x, 900, 1.0, lift)
    ang = math.degrees(dist / r)
    for wx, wy in spots:
        if t < T_OFF:
            B.wheel(c, wx, wy, r, ang, "#8a8a94", "4.7")
        elif t < T_ON - 0.2:
            e = out_cubic(off)
            with G.xf(c, wx, wy + 60 * e, s=1 + 0.45 * e):
                B.wheel(c, 0, 0, r, ang + 30 * e, "#8a8a94", "4.7", a=1 - off)
        else:
            e = out_expo(on)
            with G.xf(c, wx, wy + 40 * (1 - e), s=1 + 0.4 * (1 - e)):
                B.wheel(c, 0, 0, r, ang, B.RED, "4.8", a=clamp(on * 2))
    # the wheel guns: a flash at each hub as the nuts go on
    for wx, wy in spots:
        k = (t - T_ON) / 0.28
        if 0 <= k < 1:
            c.drawCircle(wx, wy, r * (0.4 + 0.8 * k), G.P(B.WHITE, 0.55 * (1 - k), blur=10, blend=G.ADD))
        V.burst(c, wx, wy, t, T_ON, n=14, cols=(B.YELLOW, B.WHITE), speed=700, life=0.4, size=3.5, seed=int(wx) % 7,
                gravity=900)
    # wheelspin smoke on the way out
    k = t - T_LAUNCH
    if 0 <= k < 0.9:
        (rx, ry), _ = spots
        for j in range(7):
            u = clamp((k - j * 0.04) / 0.8)
            if u <= 0:
                continue
            blob(c, rx - 260 * u - j * 30, ry + 20 - 90 * u, 60 + 220 * u, "#d9d9e0", 0.3 * (1 - u))
    # the story, left: GROK 4.7 rolls to 4.8
    f = B.wide(130)
    u = clamp((t - (T_XAI - 0.08)) / 0.6)
    if u > 0:
        e = 1 - (1 - u) ** 5
        with G.xf(c, -1200 * (1 - e), 0, skx=-0.28 * (1 - e) ** 2):
            B.roll_text(c, "GROK 4.", "7", "8", rolled, 110, 300, f, B.WHITE)
    company_line(c, "xai", 116, 372, B.WHITE, t, T_XAI + 0.2, chip="MIGHT DROP THIS WEEK", chip_fill=B.WHITE,
                 chip_ink="#0d0d0f", mark_col=B.WHITE, chip_t=T_ON + 0.12)
    B.tab(c, 116, 446, "AFTER 4.7’S BAD REVIEWS", B.cond(28, 780), B.RED, B.WHITE, t, T_OFF, tracking=0.1)
    # the pit clock
    if t >= T_BOX:
        l, rr_ = B.wipe(t, T_BOX, 0.3)
        p = B.slab(c, 110, 500, 360, 76, B.PANEL, 0.96, l=l, r=rr_)
        if p is not None:
            c.save()
            c.clipPath(p, skia.ClipOp.kIntersect, True)
            fl = B.cond(26, 740)
            B.T(c, "PIT STOP", 140, 538 + fl.cap / 2, fl, B.GREY, tracking=0.14)
            el = min(t, T_JACK) - T_BOX
            col = B.GREEN if t >= T_JACK else B.WHITE
            B.T(c, f"{el:.1f}s", 440, 538 + B.wide(44).cap / 2, B.wide(44), col, align=1.0, tnum=True)
            c.restore()
    B.radio(c, 1200, 150, 600, "xai", "xAI  ·  GROK", [(T_XAI + 0.02, "“BOX, BOX.”", B.WHITE)], t, T_XAI - 0.3,
            t1=T_ON + 0.25, talk=(T_XAI, T_XAI + 0.6))
    B.boss(c, "musk", 1450, 130, 290, 322, "xai", t, T_XAI_BOSS)
