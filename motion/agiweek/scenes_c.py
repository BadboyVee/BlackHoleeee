"""DevDay, the drop, Anthropic's IPO and the end."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_expo, in_out_cubic, in_cubic, spring, hash01
from . import marks as M
from . import motion as V
from .look import (BRANDS, BLACK, WHITE, GREY, DIM, CLAY, IVORY, IVORY_INK, T, ui, serif, mono, rr, ground, blob,
                   stars, chip, eyebrow, gemini_shader)
from .scenes_a import agi_bar
from .score import G as GRID, T_DEV, T_TOMORROW, T_BUILD, T_MYSTERY, T_DROP, T_IPO, T_RISE, T_ON_TOP, T_END, ROW_ORDER

LAB_COLS = (CLAY, WHITE, "#9b72cb", "#1a86ff", "#c9d7ff")


def beat_pulse(t, decay=0.12):
    return math.exp(-((t % GRID.spb) / decay))


# ---------------------------------------------------------------- 7 DevDay tomorrow

def devday(c, t):
    ground(c, BLACK)
    build = clamp((t - T_BUILD) / (T_DROP - T_BUILD))
    blob(c, 960, 520, 700 + 300 * build, "#243a7a", 0.35 + 0.4 * build)
    stars(c, t, a=0.6 + 0.4 * build, speed=0.05 + 0.3 * build * build)
    V.speed_lines(c, 960, 520, 0.9 * build * build, t, "#c9d7ff")
    push = 1 + 0.12 * in_cubic(build)
    c.save()
    c.translate(960, 540)
    c.scale(push, push)
    c.translate(-960, -540)
    # a ring of light that beats with the kick and tightens toward the drop
    if t >= T_DEV + 0.2:
        ra = clamp((t - T_DEV - 0.2) / 0.5)
        r = (430 - 130 * build) * (1 + 0.03 * beat_pulse(t))
        ring = skia.Path()
        ring.addArc(skia.Rect.MakeXYWH(960 - r, 520 - r, 2 * r, 2 * r), -90, 359.9)
        V.trim_stroke(c, ring, out_expo(ra), WHITE, 3 + 6 * build, a=0.25 + 0.5 * build)
        c.drawCircle(960, 520, r, G.P("#6f8cff", (0.15 + 0.35 * build) * ra, stroke=40, blur=30))
    k = clamp((t - T_DEV - 0.02) / 0.45)
    T(c, G.scramble("THE MAIN EVENT", k, seed=9, t=t), 960, 250, mono(28, 650), GREY, a=clamp((t - T_DEV) / 0.15),
      align=0.5, tracking=0.34)
    V.draw_line(c, 740, 240, 600, 240, t, T_DEV + 0.1, "#3a3a42", 2, dur=0.6)
    V.draw_line(c, 1180, 240, 1320, 240, t, T_DEV + 0.1, "#3a3a42", 2, dur=0.6)
    # the blossom draws its outline, then fills
    u = clamp((t - T_DEV - 0.1) / 0.7)
    if u > 0:
        rot = (t - T_DEV) * 14
        path = V.mark_path("openai", 960, 410, 150, rot)
        V.trim_stroke(c, path, out_cubic(u), WHITE, 3)
        fill = clamp((u - 0.55) / 0.45)
        if fill > 0:
            c.drawPath(path, G.P(WHITE, fill))

    def title(cc):
        V.mask_rise(cc, "DevDay", 960, 690, 230, WHITE, t, T_DEV + 0.35, w0=150, w1=820, stagger=0.04, align=0.5,
                    tr0=0.14, glow=("#9fb4ff", 0.35))

    G.light_sweep(c, title, 560, 1360, 600, (t - T_DEV - 1.0) / 0.7, colors=("#ffffff",), width=130, strength=0.8)
    if t >= T_TOMORROW:
        v = clamp((t - T_TOMORROW) / 0.3)
        with G.xf(c, 960, 790, s=0.5 + 0.5 * V.overshoot(v, 2.4)):
            chip(c, 0, 0, "TOMORROW", WHITE, BLACK, a=v, size=30, align=0.5, dot="#ff3b30", t=t)
        T(c, V.typewriter("TUE · SEP 29", t, T_TOMORROW + 0.15, cps=30), 960, 870, mono(26, 600), GREY, align=0.5,
          tracking=0.3)
    # the question cards fly in from behind the camera and settle into orbit
    for i, tm in enumerate(T_MYSTERY):
        if t < tm:
            continue
        w = clamp((t - tm) / 0.25)
        e = out_expo(clamp((t - tm) / 0.45))
        ang = math.radians(-150 + i * 60 + (t - T_BUILD) * 14)
        R = 600 - 50 * build
        x, y = 960 + math.cos(ang) * R, 520 + math.sin(ang) * R * 0.62
        s = lerp(2.8, 1.0, e) * (1 + 0.06 * beat_pulse(t))
        with G.xf(c, x, y, s=s, rot=(float(hash01(i, 3)) - 0.5) * 20 + 30 * (1 - e)):
            c.drawRRect(rr(-70, -88, 140, 176, 22), G.P("#101014", w))
            c.drawRRect(rr(-70, -88, 140, 176, 22), G.P(WHITE, 0.35 * w, stroke=2))
            T(c, "?", 0, 34, V.vfont("inter", 100, 800), WHITE, a=w, align=0.5)
    if t >= T_BUILD + 0.2:
        V.words_rise(c, [(T_BUILD + 0.2 + 0.05 * k, w) for k, w in
                         enumerate("Even more announcements and releases.".split(" "))], 960, 985, 34, GREY, t,
                     w0=250, w1=500, align=0.5)
    c.restore()


# ---------------------------------------------------------------- 8 the drop: (AGI?)

def drop(c, t):
    k = t - T_DROP
    invert = 1 if 0.47 <= k < 0.59 else 0          # one inversion on the off-beat; no strobing
    bg, fg = (WHITE, BLACK) if invert else (BLACK, WHITE)
    ground(c, bg)
    if not invert:
        blob(c, 960, 540, 900, "#3a2a7a", 0.5 + 0.2 * beat_pulse(t))
        stars(c, t, a=1.0, speed=0.35)
        V.speed_lines(c, 960, 540, 0.8 * math.exp(-k / 0.6) + 0.15, t, "#c9d7ff")
    V.shockwave(c, 960, 540, t, T_DROP, fg, r0=60, r1=1400, dur=0.9, width=10)
    V.shockwave(c, 960, 540, t, T_DROP + 0.47, fg, r0=60, r1=1200, dur=0.7, width=6, a=0.7)
    V.burst(c, 960, 540, t, T_DROP, n=70, cols=LAB_COLS, speed=1800, life=1.2, size=5, seed=13, gravity=300)
    # the labs orbit the question, trailing ghosts of themselves
    for i, key in enumerate(ROW_ORDER):
        b = BRANDS[key]
        col = fg if key in ("openai", "xai") else b["mark_col"] if key != "meta" else "#1a86ff"
        for g in range(3, -1, -1):
            kk = k - g * 0.025
            ang = 2 * math.pi * i / len(ROW_ORDER) + kk * 2.2
            R = 700 - 90 * math.exp(-max(0.0, kk) / 0.2)
            R *= out_expo(clamp(kk / 0.5)) if kk > 0 else 0.0
            x, y = 960 + math.cos(ang) * R, 540 + math.sin(ang) * R * 0.55
            a = 0.9 if g == 0 else 0.18 / g
            if key == "google":
                M.mark(c, "gemini", x, y, 110, a=a, shader=gemini_shader(x - 55, y - 55, x + 55, y + 55))
            else:
                M.mark(c, b["mark"], x, y, 110, col, a, rot=kk * 40)
    slam = out_expo(clamp(k / 0.35))
    s = lerp(1.9, 1.0, slam) * (1 + 0.04 * beat_pulse(t))
    shake = 12 * math.exp(-k / 0.25)
    sx, sy = shake * math.sin(k * 90), shake * math.cos(k * 77)
    f = V.vfont("inter", 420, 880)
    fp = V.vfont("inter", 420, 250)
    run = f.shape("AGI?")
    wl, wr = fp.width("("), fp.width(")")
    total = wl + run.width + wr + 40
    split = 26 * math.exp(-k / 0.18)
    with G.xf(c, 960 + sx, 540 + sy, s=s):
        x = -total / 2
        pin = 220 * (1 - V.overshoot(clamp((k - 0.05) / 0.4), 1.6))
        T(c, "(", x - pin, f.cap / 2, fp, GREY if not invert else "#6b6b6b", a=clamp(k / 0.15))
        x += wl + 20
        path = run.path(x, f.cap / 2)
        if not invert:
            c.drawPath(path, G.P("#8fa2ff", 0.6, blur=40))
        if split > 0.5:
            with G.xf(c, split, 0):
                c.drawPath(path, G.P("#ff2d55", 0.6))
            with G.xf(c, -split, 0):
                c.drawPath(path, G.P("#2de2ff", 0.6))
        c.drawPath(path, G.P(fg))
        x += run.width + 20
        T(c, ")", x + pin, f.cap / 2, fp, GREY if not invert else "#6b6b6b", a=clamp(k / 0.15))


# ---------------------------------------------------------------- 9 Anthropic's IPO: November

TOWER = ["anthropic", "openai", "google", "meta", "xai"]


def ipo(c, t):
    ground(c, IVORY)
    blob(c, 1500, 300, 900, "#ead8c4", 0.6)
    M.mark(c, "claude", 260, 900, 700, CLAY, 0.06, rot=(t - T_IPO) * 6)
    eyebrow(c, "anthropic", 120, 150, t, T_IPO + 0.05, IVORY_INK, status="IPO · PLANNED FOR NOVEMBER",
            status_fill=IVORY_INK, status_ink=WHITE, dot=CLAY)
    month_flip(c, t, 120, 240)
    if t >= T_ON_TOP:
        wd = V.mask_rise(c, "Staying on top.", 112, 780, 160, IVORY_INK, t, T_ON_TOP, fam="fraunces", w0=120,
                         w1=440, stagger=0.03, dur=0.65, tr0=0.1)
        V.draw_line(c, 118, 812, 118 + wd, 812, t, T_ON_TOP + 0.45, CLAY, 4, dur=0.6)
        V.words_rise(c, [(T_ON_TOP + 0.5 + 0.05 * k, w) for k, w in
                         enumerate("Anthropic’s IPO is planned for November.".split(" "))], 120, 880, 38, "#4a463e",
                     t, w0=250, w1=460)
    tower(c, t)


def month_flip(c, t, x, y):
    """A desk calendar: its pages flip up and over, SEP to OCT to NOV, in 3D."""
    months = ["SEP", "OCT", "NOV"]
    flips = [T_IPO + 0.35, T_IPO + 0.75]
    u = clamp((t - T_IPO - 0.1) / 0.35)
    if u <= 0:
        return
    w, h, hdr = 360, 390, 70
    s = spring(t - T_IPO - 0.1, 2.4, 0.55)
    idx = sum(1 for f in flips if t >= f)
    fm = serif(180, 460)

    def page(cc, month, a=1.0):
        cc.drawRRect(rr(0, hdr - 30, w, h - hdr + 30, 30), G.P(WHITE, a))
        T(cc, month, w / 2, 300, fm, CLAY if month == "NOV" else IVORY_INK, a=a, align=0.5)
        cc.drawLine(24, 350, w - 24, 350, G.P("#e7e2d6", a, stroke=2))

    c.save()
    c.translate(x + w / 2, y + h / 2)
    c.scale(0.7 + 0.3 * s, 0.7 + 0.3 * s)
    c.translate(-w / 2, -h / 2)
    c.drawRRect(rr(0, 18, w, h, 30), G.P("#000000", 0.14 * u, blur=26))
    page(c, months[idx], u)
    if idx > 0:
        k = clamp((t - flips[idx - 1]) / 0.3)
        if k < 1:
            # the old page swings up round its hinge and away, shading as it turns
            c.save()
            V.tilt(c, w / 2, hdr, rx=-110 * in_out_cubic(k), D=900)
            with G.clip_rect(c, -200, hdr - 40, w + 400, h):
                page(c, months[idx - 1], u)
                c.drawRRect(rr(0, hdr - 30, w, h - hdr + 30, 30), G.P("#000000", 0.25 * math.sin(math.pi * k)))
            c.restore()
    c.drawRRect(rr(0, 0, w, hdr + 10, 30), G.P(CLAY, u))
    c.drawRect(skia.Rect.MakeXYWH(0, 40, w, hdr - 30), G.P(CLAY, u))
    for rx_ in (w * 0.3, w * 0.7):
        c.drawCircle(rx_, 10, 9, G.P("#8a4a33", u))
    T(c, "2026", w / 2, 50, mono(26, 700), WHITE, a=u, align=0.5, tracking=0.3)
    c.restore()
    if t >= flips[-1] + 0.3:
        V.burst(c, x + w / 2, y + 250, t, flips[-1] + 0.3, n=26, cols=(CLAY, "#f1b99f"), speed=650, life=0.8,
                size=4, seed=41, gravity=280)
        V.shockwave(c, x + w / 2, y + h / 2, t, flips[-1] + 0.3, CLAY, r0=150, r1=520, dur=0.6, width=5, a=0.7)


def tower(c, t):
    """Five labs stacked; Anthropic climbs from the middle to the top, trailing sparks."""
    size, gap = 160, 20
    x = 1540
    y_top = 150
    rise = in_out_cubic(clamp((t - T_RISE) / 0.55))
    start = ["openai", "google", "anthropic", "meta", "xai"]
    for i, key in enumerate(start):
        t0 = T_IPO + 0.2 + 0.07 * i
        u = clamp((t - t0) / 0.3)
        if u <= 0:
            continue
        slot = lerp(i, TOWER.index(key), rise)
        y = y_top + slot * (size + gap)
        xo = -90 * math.sin(math.pi * rise) if key == "anthropic" else 0.0
        s = 0.4 + 0.6 * V.overshoot(clamp((t - t0) / 0.45), 2.0)
        with G.xf(c, x + xo + size / 2, y + size / 2, s=s):
            _tile(c, key, size, u, t, glow=key == "anthropic" and t >= T_RISE)
        if key == "anthropic" and 0 < rise < 1:
            V.burst(c, x + xo + size / 2, y + size, t, t - 0.05, n=6, cols=(CLAY, "#f1b99f"), speed=200, life=0.4,
                    size=3, seed=int(t * 60), gravity=-200)
    if t >= T_RISE + 0.45:
        v = clamp((t - T_RISE - 0.45) / 0.3)
        with G.xf(c, x - 40, y_top + size / 2, s=0.5 + 0.5 * V.overshoot(v, 2.6)):
            chip(c, 0, 0, "#1", IVORY_INK, WHITE, a=v, size=26, align=1.0)
        V.shockwave(c, x + size / 2, y_top + size / 2, t, T_RISE + 0.45, CLAY, r0=90, r1=260, dur=0.5, width=4)


def _tile(c, key, size, a, t, glow=False):
    b = BRANDS[key]
    if glow:
        c.drawRRect(rr(-size / 2 - 12, -size / 2 - 12, size + 24, size + 24, 40),
                    G.P(CLAY, (0.35 + 0.15 * math.sin(t * 5)) * a, blur=28))
    c.drawRRect(rr(-size / 2, -size / 2 + 12, size, size, 32), G.P("#000000", 0.16 * a, blur=18))
    top, bot = b["bg"]
    c.drawRRect(rr(-size / 2, -size / 2, size, size, 32), G.P(top, a, shader=G.linear_grad(0, -size / 2, 0, size / 2,
                                                                                         [top, bot])))
    if key == "google":
        M.mark(c, "gemini", 0, 0, size * 0.52, a=a, shader=gemini_shader(-40, -40, 40, 40))
    else:
        M.mark(c, b["mark"], 0, 0, size * 0.52, b["mark_col"], a)


# ---------------------------------------------------------------- 10 the end

def end(c, t):
    ground(c, BLACK)
    blob(c, 960, 520, 800, "#262a40", 0.4)
    stars(c, t, a=0.7, speed=0.04)
    size = 170
    f = V.vfont("inter", size, 800)
    words = [(T_END + 0.05, "Big"), (T_END + 0.28, "week"), (T_END + 0.52, "ahead.")]
    sp = f.width(" ")
    total = sum(f.width(w) for _, w in words) + 2 * sp

    def title(cc):
        x = 960 - total / 2
        for t0, w in words:
            V.mask_rise(cc, w, x, 470, size, WHITE, t, t0, w0=150, w1=800, tr0=0.12)
            x += f.width(w) + sp

    G.light_sweep(c, title, 960 - total / 2 - 200, 960 + total / 2 + 200, 420, (t - T_END - 1.0) / 0.8,
                  colors=("#ffffff",), width=140, strength=0.85)
    V.words_rise(c, [(T_END + 0.9 + 0.05 * k, w) for k, w in enumerate("Another week closer to AGI.".split(" "))],
                 960, 570, 44, GREY, t, w0=250, w1=500, align=0.5)
    agi_bar(c, t, 700, 1e9, a=clamp((t - T_END - 1.1) / 0.5), filled=15)
    for i, key in enumerate(ROW_ORDER):
        t0 = T_END + 1.3 + 0.08 * i
        u = clamp((t - t0) / 0.3)
        if u <= 0:
            continue
        x = 960 + (i - 2) * 150
        b = BRANDS[key]
        s = 0.3 + 0.7 * V.overshoot(clamp((t - t0) / 0.45), 2.2)
        if key == "google":
            M.mark(c, "gemini", x, 880, 58 * s, a=u, shader=gemini_shader(x - 29, 851, x + 29, 909))
        else:
            M.mark(c, b["mark"], x, 880, 58 * s, CLAY if key == "anthropic" else WHITE, u)
    T(c, "Expected releases and reports as of Sep 28, 2026 · fan-made, not affiliated with the companies shown",
      960, 1040, ui(17, 450), DIM, a=clamp((t - T_END - 1.6) / 0.4), align=0.5)
