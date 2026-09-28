"""The open, the slate and Anthropic."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, out_expo, in_out_cubic, hash01
from . import marks as M
from . import motion as V
from .look import (BRANDS, BLACK, WHITE, GREY, DIM, CLAY, IVORY, IVORY_INK, T, ui, serif, mono, rr, ground, blob,
                   stars, chip, eyebrow, cursor, press_of, panel, chevron, gemini_shader, GEMINI_GRAD, arrow_up)
from .score import (OPEN_WORDS, T_AGI, T_TICK, T_SLATE, DROP_ORDER, T_DROPS, T_STACKED, T_FAN, ROW_ORDER, T_DIVE,
                    T_ANT, T_PICKER, T_PICK, T_ANT_FOUNDERS, T_FABLE, T_OAI)

IRIDESCENT = ["#ffffff", "#c9d7ff", "#f4c6ff", "#ffd9b8", "#ffffff"]


# ---------------------------------------------------------------- the floor: a grid running toward the horizon

def floor(c, t, horizon=720, a=0.16, speed=0.9):
    if a <= 0:
        return
    vx = 960
    for k in range(14):
        z = ((k + (t * speed) % 1.0) / 14) ** 2.2
        y = horizon + (1080 - horizon) * z * 1.15
        c.drawLine(0, y, 1920, y, G.P("#9fb0ff", a * z, stroke=1 + 1.5 * z))
    for k in range(-12, 13):
        x_far = vx + k * 40
        x_near = vx + k * 260
        c.drawLine(x_far, horizon, x_near, 1080 + 200, G.P("#9fb0ff", a * 0.6, stroke=1.2))
    c.drawRect(skia.Rect.MakeLTRB(0, horizon - 2, 1920, horizon + 160),
               G.P(BLACK, 1, shader=G.linear_grad(0, horizon, 0, horizon + 160, [BLACK, BLACK], alphas=[1.0, 0.0])))


# ---------------------------------------------------------------- 1 the open

def agi_bar(c, t, y, step_t, a=1.0, weeks=18, filled=14):
    """The road to AGI: a track of weekly ticks; the fill moves one week closer at step_t."""
    if a <= 0:
        return
    x0, x1 = 410, 1510
    w = x1 - x0
    grow = out_expo(clamp(a))
    c.drawRRect(rr(x0, y - 5, w * grow, 10, 5), G.P("#1d1d22", a))
    for k in range(weeks + 1):
        x = x0 + w * k / weeks
        v = clamp(a * 1.6 - k / weeks * 0.8)
        c.drawLine(x, y + 16, x, y + 16 + 10 * v, G.P("#3a3a42", a, stroke=2))
    u = out_back(clamp((t - step_t) / 0.45), 1.8) if t >= step_t else 0.0
    fw = w * (filled + u) / weeks * grow
    c.drawRRect(rr(x0, y - 5, fw, 10, 5), G.P(WHITE, a, shader=G.linear_grad(x0, 0, x0 + fw, 0,
                                                                          ["#5b5b66", "#ffffff"])))
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    c.drawCircle(x0 + fw, y, 9, G.P(WHITE, a))
    c.drawCircle(x0 + fw, y, 22 + 8 * pulse, G.P(WHITE, 0.2 * a, blur=12))
    T(c, "AGI", x1 + 30, y + 9, mono(24, 700), WHITE, a=a, tracking=0.2)
    T(c, "NOW", x0 - 30, y + 9, mono(24, 600), DIM, a=a, align=1.0, tracking=0.2)
    if t >= step_t:
        v = clamp((t - step_t) / 0.35)
        V.burst(c, x0 + fw, y, t, step_t + 0.12, n=18, speed=520, life=0.7, size=3, seed=5, gravity=300)
        with G.xf(c, x0 + fw, y - 46 - 10 * out_cubic(v), s=0.6 + 0.4 * V.overshoot(v, 2.4)):
            chip(c, 0, 0, "+1 WEEK", WHITE, BLACK, a=v * (1 - clamp((t - step_t - 1.1) / 0.3)), size=18, align=0.5)


def cold_open(c, t):
    ground(c, BLACK)
    blob(c, 960, 520, 820, "#2a3350", 0.35 + 0.1 * math.sin(t * 2))
    stars(c, t, a=0.9)
    floor(c, t, a=0.14 * clamp(t / 0.8))
    # dateline
    k = clamp((t - 0.05) / 0.5)
    T(c, G.scramble("WEEK OF SEP 28 · 2026", k, seed=3, t=t), 120, 130, mono(22, 600), GREY, a=clamp(t / 0.2),
      tracking=0.28)
    T(c, G.scramble("AI · THIS WEEK", k, seed=4, t=t), 1800, 130, mono(22, 600), GREY, a=clamp(t / 0.2), align=1.0,
      tracking=0.28)
    V.draw_line(c, 120, 158, 420, 158, t, 0.2, "#3a3a42", 2, dur=0.8)
    V.draw_line(c, 1800, 158, 1500, 158, t, 0.2, "#3a3a42", 2, dur=0.8)
    # the headline, a word a beat, each rising out of its own mask while its weight grows
    size = 150
    f = V.vfont("inter", size, 760)
    sp = f.width(" ")
    line1 = [OPEN_WORDS[0], OPEN_WORDS[1]]
    w1 = sum(f.width(w) for _, w in line1) + sp
    x = 960 - w1 / 2
    for t0, w in line1:
        V.mask_rise(c, w, x, 440, size, WHITE, t, t0, w0=150, w1=760, tr0=0.12)
        x += f.width(w) + sp
    fa = V.vfont("inter", size, 860)
    line2 = [OPEN_WORDS[2], OPEN_WORDS[3]]
    w2 = sum(f.width(w) for _, w in line2) + sp * 2 + fa.width("AGI.")
    x = 960 - w2 / 2
    for t0, w in line2:
        V.mask_rise(c, w, x, 610, size, WHITE, t, t0, w0=150, w1=760, tr0=0.12)
        x += f.width(w) + sp
    # AGI. lands on the bar, in light: a punch, a shockwave, sparks, then a sweep of light across it
    if t >= T_AGI - 0.02:
        aw = fa.width("AGI.")
        cx = x + aw / 2
        punch = 1 + 0.22 * math.exp(-(t - T_AGI) / 0.09)
        V.shockwave(c, cx, 560, t, T_AGI, WHITE, r0=80, r1=1100, dur=0.8, width=6, a=0.8)
        V.burst(c, cx, 560, t, T_AGI, n=40, cols=(WHITE, "#c9d7ff", "#f4c6ff"), speed=1300, life=1.0, size=4,
                seed=9, gravity=260)
        sh = G.linear_grad(x - 200 + 300 * math.sin(t * 0.9), 0, x + aw + 200, 0, IRIDESCENT)

        def agi(cc):
            with G.xf(cc, cx, 560, s=punch):
                cc.translate(-cx, -560)
                V.mask_rise(cc, "AGI.", x, 610, size, WHITE, t, T_AGI, w0=300, w1=860, stagger=0.03, dur=0.5,
                            tr0=0.2, shader=sh, glow=("#aab8ff", 0.5))

        V_sweep = (t - T_AGI - 0.45) / 0.7
        G.light_sweep(c, agi, x - 250, x + aw + 250, 560, V_sweep, colors=("#ffffff",), width=140, strength=0.9)
    agi_bar(c, t, 800, T_TICK, a=clamp((t - 0.9) / 0.5))


# ---------------------------------------------------------------- 2 the slate

CARD_W, CARD_H = 340, 430


def brand_card(c, key, w, h, t, a=1.0, detail=1.0):
    """A lab's card, centred on (0, 0): the model on top, the mark in the middle, the company at the foot."""
    b = BRANDS[key]
    r = 34 * w / CARD_W
    c.drawRRect(rr(-w / 2, -h / 2 + 22, w, h, r), G.P("#000000", 0.45 * a, blur=30))
    top, bot = b["bg"]
    c.drawRRect(rr(-w / 2, -h / 2, w, h, r), G.P(top, a, shader=G.linear_grad(0, -h / 2, 0, h / 2, [top, bot])))
    if key in ("xai", "openai"):
        c.drawRRect(rr(-w / 2 + 0.7, -h / 2 + 0.7, w - 1.4, h - 1.4, r), G.P(WHITE, 0.16 * a, stroke=1.4))
    s = w / CARD_W
    ink = b["ink"]
    # the model on top
    fm = serif(66 * s, 440) if key == "anthropic" else V.vfont("inter", 58 * s, 760)
    mw = fm.width(b["model"])
    if mw > w - 56 * s:
        k = (w - 56 * s) / mw
        fm = serif(66 * s * k, 440) if key == "anthropic" else V.vfont("inter", 58 * s * k, 760)
    y_model = -h / 2 + 96 * s
    if key == "google":
        path = fm.shape(b["model"]).path(-w / 2 + 30 * s, y_model)
        c.drawPath(path, G.P(WHITE, a, shader=G.linear_grad(-w / 2, 0, w / 2, 0, GEMINI_GRAD)))
    else:
        T(c, b["model"], -w / 2 + 30 * s, y_model, fm, ink, a=a)
    if b.get("model2"):
        T(c, b["model2"], -w / 2 + 32 * s, y_model + 44 * s, ui(28 * s, 600), ink, a=a * 0.7)
    if detail > 0:
        fill = CLAY if key == "anthropic" else (ink if key != "google" else "#1f1f1f")
        chip_ink = WHITE if key in ("anthropic", "google") else top
        with G.xf(c, -w / 2 + 30 * s, -h / 2 + (160 if b.get("model2") else 136) * s, s=s):
            chip(c, 0, 0, b["status"], fill, chip_ink, a=a * detail, size=15)
    msz = 118 * s
    if key == "google":
        half = msz / 2
        M.mark(c, "gemini", 0, 40 * s, msz, a=a, shader=gemini_shader(-half, 40 * s - half, half, 40 * s + half))
    else:
        M.mark(c, b["mark"], 0, 40 * s, msz, b["mark_col"], a)
    T(c, b["company"], -w / 2 + 30 * s, h / 2 - 34 * s, ui(24 * s, 650), ink, a=a * 0.8)


def stack_pose(i):
    """Where card i settles on the stack: a little offset and turn each."""
    rot = (float(hash01(i, 7)) - 0.5) * 12
    dx = (float(hash01(i, 8)) - 0.5) * 36
    return 1340 + dx, 560 - i * 6, rot


def row_pose(key):
    i = ROW_ORDER.index(key)
    n = len(ROW_ORDER)
    w, gap = 300, 34
    total = n * w + (n - 1) * gap
    return 960 - total / 2 + w / 2 + i * (w + gap), 600, 0.0, w / CARD_W


def slate(c, t):
    ground(c, BLACK)
    blob(c, 1340, 560, 700, "#26263a", 0.35)
    stars(c, t, a=0.5, speed=0.03)
    fan = in_out_cubic(clamp((t - T_FAN) / 0.5))
    # headline
    fade = 1 - clamp((t - T_FAN + 0.1) / 0.3)
    if fade > 0:
        lift = -80 * (1 - fade)
        with G.layer(c, alpha=fade):
            line = V.typewriter("The final week of September", t, T_SLATE + 0.02, cps=60)
            T(c, line, 120, 420 + lift, ui(52, 500), GREY)
            if int(t * 4) % 2 == 0 and t < T_SLATE + 0.9:
                c.drawRect(skia.Rect.MakeXYWH(124 + ui(52, 500).width(line), 382 + lift, 4, 48), G.P(GREY))
            V.mask_rise(c, "is looking", 120, 560 + lift, 118, WHITE, t, T_SLATE + 0.45, w0=200, w1=800)
            if t >= T_STACKED:
                punch = 1 + 0.16 * math.exp(-(t - T_STACKED) / 0.1)
                with G.xf(c, 120, 690 + lift, s=punch):
                    V.mask_rise(c, "stacked.", 0, 0, 118, WHITE, t, T_STACKED, w0=300, w1=880, tr0=0.2)
    # the cards drop onto the stack, tipping flat as they fall, then fan out into a row
    for i, key in enumerate(DROP_ORDER):
        td = T_DROPS[i]
        if t < td - 0.3:
            continue
        sx, sy, srot = stack_pose(i)
        u = clamp((t - (td - 0.3)) / 0.3)
        fall = 1 - out_cubic(u) if u < 1 else 0.0
        land = t - td
        x, y = sx, sy - 950 * fall
        rot = srot + 24 * fall
        rx = 58 * fall
        squash = 0.05 * math.exp(-max(0.0, land) / 0.08) * math.cos(max(0.0, land) * 30) if land >= 0 else 0.0
        s = 1.0
        if fan > 0:
            px, py, prot, ps = row_pose(key)
            j = ROW_ORDER.index(key)
            st = in_out_cubic(clamp(fan * 1.3 - j * 0.07))
            x = lerp(x, px, st)
            y = lerp(y, py, st) - 160 * math.sin(math.pi * st)
            rot = lerp(rot, prot, st) + 8 * math.sin(math.pi * st) * (1 if j % 2 else -1)
            s = lerp(s, ps, st)
            y += V.float_y(t, j * 1.3, amp=6 * st)
        c.save()
        V.tilt(c, x, y, rx=rx)
        with G.xf(c, x, y, rot=rot, sx=s * (1 + squash), sy=s * (1 - squash)):
            brand_card(c, key, CARD_W, CARD_H, t)
            V.glint(c, rr(-CARD_W / 2, -CARD_H / 2, CARD_W, CARD_H, 34), t, td + 0.02, dur=0.6, a=0.45)
        c.restore()
    if fan > 0:
        k = clamp((t - T_FAN) / 0.5)
        T(c, G.scramble("THIS WEEK’S SLATE", k, seed=6, t=t), 960, 290, mono(24, 650), GREY, a=fan, align=0.5,
          tracking=0.3)


def slate_dive(c, t):
    """The Anthropic card grows to fill the frame, its spark spinning up; the others fly out past the camera."""
    u = in_out_cubic(clamp((t - T_DIVE) / (T_ANT - T_DIVE)))
    ground(c, BLACK)
    for key in ROW_ORDER:
        if key == "anthropic":
            continue
        rx, ry, _, rs = row_pose(key)
        dx = (rx - 960) * 2.4 * u
        with G.xf(c, rx + dx, ry, s=rs * (1 + 0.9 * u)):
            brand_card(c, key, CARD_W, CARD_H, t, a=1 - u)
    rx, ry, _, rs = row_pose("anthropic")
    w = lerp(CARD_W * rs, 1920, u)
    h = lerp(CARD_H * rs, 1080, u)
    x, y = lerp(rx, 960, u), lerp(ry, 540, u)
    c.drawRRect(rr(x - w / 2, y - h / 2, w, h, lerp(34 * rs, 0, u)), G.P(IVORY))
    with G.xf(c, x, y, s=lerp(rs, 3.0, u)):
        with G.layer(c, alpha=1 - u):
            brand_card(c, "anthropic", CARD_W, CARD_H, t)
    M.mark(c, "claude", x, y + 40 * rs * (1 - u), lerp(118 * rs, 520, u), CLAY, 0.9 * (1 - u) + 0.1, rot=u * 220)


# ---------------------------------------------------------------- 3 Anthropic

PICK_ROWS = [("Fable 5.1", "Our most capable model"), ("Opus 5.5", "Deep work, long tasks"),
             ("Sonnet 5.5", "Expected today"), ("Sonnet 5", "Smart, efficient, everyday"),
             ("Haiku 4.5", "Fastest")]
APP = (1060, 200, 760, 540)


def anthropic(c, t):
    ground(c, IVORY)
    blob(c, 1500, 900, 900, "#e8d9c6", 0.6)
    M.mark(c, "claude", 1620, 930, 620, CLAY, 0.07, rot=(t - T_ANT) * 8)
    eyebrow(c, "anthropic", 120, 150, t, T_ANT + 0.05, IVORY_INK, status="EXPECTED TODAY", status_fill=CLAY,
            status_ink=WHITE, dot=WHITE)

    def hero(cc):
        V.mask_rise(cc, "Sonnet 5.5", 112, 460, 188, IVORY_INK, t, T_ANT + 0.2, fam="fraunces", w0=120, w1=440,
                    stagger=0.035, dur=0.7, tr0=0.1)

    G.light_sweep(c, hero, 60, 1000, 400, (t - T_ANT - 1.05) / 0.8, colors=("#f1b99f", CLAY, "#f1b99f"), width=150,
                  strength=0.85)
    words = [(T_ANT + 0.7 + 0.06 * k, w) for k, w in enumerate("A big step up from the current model.".split(" "))]
    V.words_rise(c, words, 120, 560, 40, "#3d3a33", t, w0=250, w1=460)
    if t >= T_FABLE:
        wf = V.mask_rise(c, "A Fable moment?", 120, 645, 60, CLAY, t, T_FABLE, fam="fraunces-italic", w0=200,
                         w1=440, stagger=0.02, dur=0.45)
        V.draw_line(c, 122, 668, 122 + wf, 668, t, T_FABLE + 0.35, CLAY, 3, dur=0.5)
    claude_app(c, t)
    V.founder(c, "amodei", 330, 830, 420, t, T_ANT_FOUNDERS, ring=CLAY, text_col=IVORY_INK, rect_h=250)


def claude_app(c, t):
    x, y, w, h = APP
    u = V.swing_in(t, T_ANT + 0.25, 2.0, 0.6)
    if u <= 0:
        return
    cx, cy = x + w / 2, y + h / 2
    c.save()
    V.tilt(c, cx, cy, rx=10 * (1 - u), ry=-34 * (1 - u))
    with G.xf(c, cx, cy + 140 * (1 - u) + V.float_y(t, 0.5, 4), s=0.92 + 0.08 * u):
        c.translate(-cx, -cy)
        panel(c, x, y, w, h, 30, WHITE, a=clamp(u * 2), shadow=0.14)
        M.mark(c, "claude", x + 52, y + 50, 30, CLAY, rot=(t - T_ANT) * 20)
        T(c, "Claude", x + 78, y + 61, serif(34, 480), IVORY_INK)
        # the picker: its label rolls to the new model and the pill resizes to fit
        fb = ui(24, 600)
        k = clamp((t - T_PICK) / 0.35)
        e = out_expo(k)
        bw = lerp(fb.width("Sonnet 5") + 70, fb.width("Sonnet 5.5") + 70, e)
        bx = x + w - 40 - bw
        c.drawRRect(rr(bx, y + 28, bw, 46, 14), G.P(G.mixc("#f3f1ea", "#fbe9e1", e)))
        with G.clip_rect(c, bx, y + 28, bw, 46):
            if k < 1:
                T(c, "Sonnet 5", bx + 20, y + 59 - 40 * e, fb, IVORY_INK, a=1 - e)
            if k > 0:
                T(c, "Sonnet 5.5", bx + 20, y + 59 + 40 * (1 - e), fb, CLAY)
        chevron(c, bx + bw - 26, y + 51, 14, IVORY_INK, rot=180 * clamp((t - T_PICKER) / 0.2) *
                (1 - clamp((t - T_PICK) / 0.2)))
        V.burst(c, bx + bw / 2, y + 51, t, T_PICK + 0.05, n=16, cols=(CLAY, "#f1b99f"), speed=420, life=0.6, size=3,
                seed=21, gravity=200)
        fg = serif(44, 420)
        greet = "How can I help you today?"
        gw = fg.width(greet) + 58
        gx = x + (w - gw) / 2
        M.mark(c, "claude", gx + 20, y + 214, 40, CLAY, rot=(t - T_ANT) * 30)
        T(c, greet, gx + 58, y + 229, fg, IVORY_INK)
        c.drawRRect(rr(x + 50, y + 300, w - 100, 150, 24), G.P("#faf9f5"))
        c.drawRRect(rr(x + 50, y + 300, w - 100, 150, 24), G.P("#e6e2d8", 1, stroke=1.4))
        T(c, "Reply to Claude…", x + 80, y + 352, ui(24, 450), "#a19d92")
        c.drawRRect(rr(x + w - 110, y + 390, 44, 44, 12), G.P(CLAY))
        arrow_up(c, x + w - 88, y + 412, 22, WHITE)
        # the menu drops open, rows arriving one after another; the highlight follows the pointer down
        op = clamp((t - T_PICKER) / 0.18) * (1 - clamp((t - T_PICK - 0.12) / 0.2))
        if op > 0:
            mx, my, mw = x + w - 380, y + 88, 340
            mh = 60 + 64 * len(PICK_ROWS)
            grow = out_expo(clamp((t - T_PICKER) / 0.35))
            close = clamp((t - T_PICK - 0.12) / 0.2)
            with G.xf(c, mx + mw, my, sx=1.0, sy=max(0.02, grow * (1 - 0.6 * close))):
                c.translate(-(mx + mw), -my)
                panel(c, mx, my, mw, mh, 20, WHITE, a=op, shadow=0.18, rim=("#000000", 0.08))
                T(c, "MODELS", mx + 24, my + 40, mono(16, 700), "#9b978c", a=op, tracking=0.2)
                hv = clamp((t - T_PICKER - 0.15) / 0.5)
                hy = my + 60 + 64 * 2 * in_out_cubic(hv)
                if hv > 0:
                    c.drawRRect(rr(mx + 10, hy, mw - 20, 58, 12), G.P("#f5efe7" if t < T_PICK else "#fbe3d7", op))
                for k2, (name, desc) in enumerate(PICK_ROWS):
                    rv = out_cubic(clamp((t - T_PICKER - 0.04 * k2) / 0.25))
                    ry = my + 60 + 64 * k2 + 14 * (1 - rv)
                    T(c, name, mx + 26, ry + 28, ui(24, 620), IVORY_INK, a=op * rv)
                    T(c, desc, mx + 26, ry + 50, ui(16, 450), "#8e8a80", a=op * rv)
                    if name == "Sonnet 5.5":
                        with G.xf(c, mx + 30 + ui(24, 620).width(name) + 12, ry + 20, s=0.8 + 0.2 * V.overshoot(rv)):
                            chip(c, 0, 0, "NEW", CLAY, WHITE, a=op * rv, size=13)
    c.restore()
    # the pointer arcs in, finds the new model, clicks
    if T_ANT + 0.6 <= t < T_OAI - 0.3:
        row = y + 88 + 60 + 64 * 2
        path = [(T_ANT + 0.6, (1900, 1000)), (T_PICKER - 0.05, (x + w - 140, y + 55)),
                (T_PICKER + 0.45, (x + w - 260, row + 30)), (T_PICK + 0.4, (x + w - 250, row + 32)),
                (T_PICK + 1.2, (x + w - 60, y + 480))]
        px, py = _along(path, t)
        cursor(c, px, py, press=press_of(t, [T_PICKER, T_PICK]), clicks=(T_PICKER, T_PICK), t=t,
               a=clamp((t - T_ANT - 0.6) / 0.2) * (1 - clamp((t - T_PICK - 1.0) / 0.3)))


def _along(keys, t, bend=0.18):
    """A pointer path through keyframes: eased per leg, bowed into a gentle arc like a hand moving a mouse."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
        if t <= t1:
            u = in_out_cubic(clamp((t - t0) / max(1e-6, t1 - t0)))
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            arc = math.sin(math.pi * u) * bend
            return lerp(p0[0], p1[0], u) - dy * arc, lerp(p0[1], p1[1], u) + dx * arc
    return keys[-1][1]
