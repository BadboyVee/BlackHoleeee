"""DevDay, the drop, Anthropic's IPO and the end."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, in_out_cubic, in_cubic, spring, hash01
from . import marks as M
from .look import (BRANDS, BLACK, WHITE, GREY, DIM, CLAY, IVORY, IVORY_INK, T, ui, display, serif, mono, rr, ground,
                   blob, stars, chip, eyebrow, rise_text, gemini_shader)
from .scenes_a import agi_bar, _word
from .score import T_DEV, T_TOMORROW, T_BUILD, T_MYSTERY, T_DROP, T_IPO, T_RISE, T_ON_TOP, T_END, ROW_ORDER

# ---------------------------------------------------------------- 8 DevDay tomorrow


def devday(c, t):
    ground(c, BLACK)
    build = clamp((t - T_BUILD) / (T_DROP - T_BUILD))
    blob(c, 960, 520, 700 + 300 * build, "#243a7a", 0.35 + 0.4 * build)
    stars(c, t, a=0.6 + 0.4 * build, speed=0.05 + 0.25 * build * build)
    push = 1 + 0.12 * in_cubic(build)
    c.save()
    c.translate(960, 540)
    c.scale(push, push)
    c.translate(-960, -540)
    # a ring of light that tightens as the drop nears
    if build > 0:
        r = 420 - 120 * build
        c.drawCircle(960, 520, r, G.P(WHITE, 0.25 + 0.5 * build, stroke=3 + 6 * build, blur=6 * (1 - build) + 2))
        c.drawCircle(960, 520, r, G.P("#6f8cff", 0.4 * build, stroke=40, blur=30))
    k = clamp((t - T_DEV - 0.02) / 0.45)
    T(c, G.scramble("THE MAIN EVENT", k, seed=9, t=t), 960, 250, mono(28, 650), GREY, a=clamp((t - T_DEV) / 0.15),
      align=0.5, tracking=0.34)
    u = clamp((t - T_DEV - 0.12) / 0.5)
    if u > 0:
        s = spring(t - T_DEV - 0.12, 2.2, 0.55)
        M.mark(c, "openai", 960, 410, 150 * (0.6 + 0.4 * s), WHITE, u, rot=-120 * (1 - out_cubic(u)) + (t - T_DEV) * 12)
    rise_text(c, "DevDay", 960, 690, display(230, 800), WHITE, t, T_DEV + 0.35, stagger=0.04, align=0.5)
    if t >= T_TOMORROW:
        v = clamp((t - T_TOMORROW) / 0.3)
        with G.xf(c, 960, 790, s=0.7 + 0.3 * out_back(v, 2.2)):
            chip(c, 0, 0, "TOMORROW", WHITE, BLACK, a=v, size=30, align=0.5, dot="#ff3b30", t=t)
        T(c, "TUE · SEP 29", 960, 870, mono(26, 600), GREY, a=v, align=0.5, tracking=0.3)
    # the mystery drops: more announcements, more releases
    for i, tm in enumerate(T_MYSTERY):
        if t < tm:
            continue
        w = clamp((t - tm) / 0.3)
        ang = math.radians(-150 + i * 60 + (t - T_BUILD) * 12)
        R = 600 - 40 * build
        x, y = 960 + math.cos(ang) * R, 520 + math.sin(ang) * R * 0.62
        s = spring(t - tm, 3.0, 0.5)
        with G.xf(c, x, y, s=0.5 + 0.5 * s, rot=(float(hash01(i, 3)) - 0.5) * 20):
            c.drawRRect(rr(-70, -88, 140, 176, 22), G.P("#101014", w))
            c.drawRRect(rr(-70, -88, 140, 176, 22), G.P(WHITE, 0.35 * w, stroke=2))
            T(c, "?", 0, 34, display(100, 800), WHITE, a=w, align=0.5)
    if t >= T_BUILD + 0.2:
        v = clamp((t - T_BUILD - 0.2) / 0.3)
        T(c, "Even more announcements and releases.", 960, 980, ui(34, 500), GREY, a=v, align=0.5)
    c.restore()


# ---------------------------------------------------------------- 9 the drop: (AGI?)

def drop(c, t):
    k = t - T_DROP
    invert = 1 if 0.47 <= k < 0.59 else 0          # one inversion on the off-beat; no strobing
    bg, fg = (WHITE, BLACK) if invert else (BLACK, WHITE)
    ground(c, bg)
    if not invert:
        blob(c, 960, 540, 900, "#3a2a7a", 0.5)
        stars(c, t, a=1.0, speed=0.35)
    # the labs orbit the question
    for i, key in enumerate(ROW_ORDER):
        ang = 2 * math.pi * i / len(ROW_ORDER) + k * 2.2
        R = 700 - 90 * math.exp(-k / 0.2)
        x, y = 960 + math.cos(ang) * R, 540 + math.sin(ang) * R * 0.55
        b = BRANDS[key]
        col = fg if key in ("openai", "xai") else b["mark_col"] if key != "meta" else "#1a86ff"
        if key == "google":
            M.mark(c, "gemini", x, y, 110, a=0.9, shader=gemini_shader(x - 55, y - 55, x + 55, y + 55))
        else:
            M.mark(c, b["mark"], x, y, 110, col, 0.9, rot=k * 40)
    punch = 1 + 0.35 * math.exp(-k / 0.12)
    shake = 10 * math.exp(-k / 0.25)
    sx = shake * math.sin(k * 90)
    sy = shake * math.cos(k * 77)
    f = display(420, 880)
    fp = display(420, 300)
    run = f.shape("AGI?")
    wl, wr = fp.width("("), fp.width(")")
    total = wl + run.width + wr + 40
    with G.xf(c, 960 + sx, 540 + sy, s=punch):
        x = -total / 2
        T(c, "(", x, f.cap / 2, fp, GREY if not invert else "#6b6b6b")
        x += wl + 20
        path = run.path(x, f.cap / 2)
        if not invert:
            c.drawPath(path, G.P("#8fa2ff", 0.6, blur=40))
        c.drawPath(path, G.P(fg))
        x += run.width + 20
        T(c, ")", x, f.cap / 2, fp, GREY if not invert else "#6b6b6b")


# ---------------------------------------------------------------- 10 Anthropic's IPO: November

TOWER = ["anthropic", "openai", "google", "meta", "xai"]


def ipo(c, t):
    ground(c, IVORY)
    blob(c, 1500, 300, 900, "#ead8c4", 0.6)
    M.mark(c, "claude", 260, 900, 700, CLAY, 0.06, rot=(t - T_IPO) * 6)
    eyebrow(c, "anthropic", 120, 150, t, T_IPO + 0.05, IVORY_INK, status="IPO · PLANNED FOR NOVEMBER",
            status_fill=IVORY_INK, status_ink=WHITE, dot=CLAY)
    month_flip(c, t, 120, 240)
    if t >= T_ON_TOP:
        rise_text(c, "Staying on top.", 112, 780, serif(160, 440), IVORY_INK, t, T_ON_TOP, stagger=0.035)
        v = clamp((t - T_ON_TOP - 0.4) / 0.35)
        if v > 0:
            T(c, "Anthropic’s IPO is planned for November.", 120, 860 + 14 * (1 - out_cubic(v)), ui(38, 450),
              "#4a463e", a=v)
    tower(c, t)


def month_flip(c, t, x, y):
    """A desk calendar flipping SEP, OCT, NOV."""
    months = ["SEP", "OCT", "NOV"]
    flips = [T_IPO + 0.35, T_IPO + 0.75]
    u = clamp((t - T_IPO - 0.1) / 0.35)
    if u <= 0:
        return
    w, h = 360, 390
    s = spring(t - T_IPO - 0.1, 2.4, 0.55)
    with G.xf(c, x + w / 2, y + h / 2, s=0.7 + 0.3 * s):
        c.translate(-w / 2, -h / 2)
        c.drawRRect(rr(0, 18, w, h, 30), G.P("#000000", 0.14 * u, blur=26))
        c.drawRRect(rr(0, 0, w, h, 30), G.P(WHITE, u))
        c.drawRRect(rr(0, 0, w, 70, 30), G.P(CLAY, u))
        c.drawRect(skia.Rect.MakeXYWH(0, 40, w, 30), G.P(CLAY, u))
        T(c, "2026", w / 2, 48, mono(26, 700), WHITE, a=u, align=0.5, tracking=0.3)
        idx = sum(1 for f in flips if t >= f)
        cur = months[idx]
        prev = months[idx - 1] if idx > 0 else None
        fm = serif(180, 460)
        if prev is not None:
            k = clamp((t - flips[idx - 1]) / 0.22)
            if k < 1:
                # the old page folds away over the top
                with G.xf(c, w / 2, 70, sy=1 - k):
                    T(c, prev, 0, 230, fm, IVORY_INK, a=u * (1 - k), align=0.5)
                with G.xf(c, w / 2, 70, sy=k):
                    T(c, cur, 0, 230, fm, IVORY_INK if cur != "NOV" else CLAY, a=u * k, align=0.5)
            else:
                T(c, cur, w / 2, 300, fm, IVORY_INK if cur != "NOV" else CLAY, a=u, align=0.5)
        else:
            T(c, cur, w / 2, 300, fm, IVORY_INK, a=u, align=0.5)
        c.drawLine(24, 350, w - 24, 350, G.P("#e7e2d6", u, stroke=2))


def tower(c, t):
    """Five labs stacked; Anthropic climbs from the middle to the top."""
    size, gap = 160, 20
    x = 1540
    y_top = 150
    rise = in_out_cubic(clamp((t - T_RISE) / 0.55))
    start = ["openai", "google", "anthropic", "meta", "xai"]
    for i, key in enumerate(start):
        u = clamp((t - T_IPO - 0.2 - 0.06 * i) / 0.4)
        if u <= 0:
            continue
        slot0 = i
        slot1 = TOWER.index(key)
        slot = lerp(slot0, slot1, rise)
        y = y_top + slot * (size + gap)
        xo = 0.0
        if key == "anthropic":
            xo = -70 * math.sin(math.pi * rise)
        s = spring(t - T_IPO - 0.2 - 0.06 * i, 2.6, 0.55)
        with G.xf(c, x + xo + size / 2, y + size / 2, s=0.7 + 0.3 * s):
            _tile(c, key, size, u, t, glow=key == "anthropic" and t >= T_RISE)
    if t >= T_RISE + 0.4:
        v = clamp((t - T_RISE - 0.4) / 0.3)
        with G.xf(c, x - 40, y_top + size / 2):
            chip(c, 0, 0, "#1", IVORY_INK, WHITE, a=v, size=24, align=1.0)


def _tile(c, key, size, a, t, glow=False):
    b = BRANDS[key]
    if glow:
        c.drawRRect(rr(-size / 2 - 10, -size / 2 - 10, size + 20, size + 20, 38), G.P(CLAY, 0.45 * a, blur=26))
    c.drawRRect(rr(-size / 2, -size / 2 + 12, size, size, 32), G.P("#000000", 0.16 * a, blur=18))
    top, bot = b["bg"]
    c.drawRRect(rr(-size / 2, -size / 2, size, size, 32), G.P(top, a, shader=G.linear_grad(0, -size / 2, 0, size / 2,
                                                                                         [top, bot])))
    if key == "google":
        M.mark(c, "gemini", 0, 0, size * 0.52, a=a, shader=gemini_shader(-40, -40, 40, 40))
    else:
        M.mark(c, b["mark"], 0, 0, size * 0.52, b["mark_col"], a)


# ---------------------------------------------------------------- 11 the end

def end(c, t):
    ground(c, BLACK)
    blob(c, 960, 520, 800, "#262a40", 0.4)
    stars(c, t, a=0.7, speed=0.04)
    f = display(170, 800)
    words = [(T_END + 0.05, "Big"), (T_END + 0.28, "week"), (T_END + 0.52, "ahead.")]
    sp = f.width(" ")
    total = sum(f.width(w) for _, w in words) + 2 * sp
    x = 960 - total / 2
    for t0, w in words:
        _word(c, w, x, 470, f, WHITE, t, t0)
        x += f.width(w) + sp
    v = clamp((t - T_END - 0.9) / 0.4)
    if v > 0:
        T(c, "Another week closer to AGI.", 960, 570 + 12 * (1 - out_cubic(v)), ui(44, 500), GREY, a=v, align=0.5)
    agi_bar(c, t, 700, 1e9, a=clamp((t - T_END - 1.1) / 0.4), filled=15)
    for i, key in enumerate(ROW_ORDER):
        u = clamp((t - T_END - 1.3 - 0.07 * i) / 0.3)
        if u <= 0:
            continue
        x = 960 + (i - 2) * 150
        b = BRANDS[key]
        if key == "google":
            M.mark(c, "gemini", x, 880, 58, a=u, shader=gemini_shader(x - 29, 851, x + 29, 909))
        else:
            M.mark(c, b["mark"], x, 880 + 16 * (1 - out_cubic(u)), 58, WHITE if key not in ("anthropic",) else CLAY, u)
    T(c, "Expected releases and reports as of Sep 28, 2026 · fan-made, not affiliated with the companies shown",
      960, 1040, ui(17, 450), DIM, a=clamp((t - T_END - 1.6) / 0.4), align=0.5)
