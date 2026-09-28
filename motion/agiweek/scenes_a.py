"""The open, the slate and Anthropic."""
import math


from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, in_out_cubic, spring, hash01
from . import marks as M
from .look import (BRANDS, BLACK, WHITE, GREY, DIM, CLAY, IVORY, IVORY_INK, F, T, ui, display, serif, mono, rr,
                   ground, blob, stars, chip, eyebrow, rise_text, portrait, cursor, press_of, panel, chevron,
                   gemini_shader, GEMINI_GRAD, arrow_up)
from .score import (OPEN_WORDS, T_AGI, T_TICK, T_SLATE, DROP_ORDER, T_DROPS, T_STACKED, T_FAN, ROW_ORDER, T_DIVE,
                    T_ANT, T_PICKER, T_PICK, T_ANT_FOUNDERS, T_FABLE, T_OAI)

# ---------------------------------------------------------------- 1 the open

IRIDESCENT = ["#ffffff", "#c9d7ff", "#f4c6ff", "#ffd9b8", "#ffffff"]


def agi_bar(c, t, y, step_t, a=1.0, weeks=18, filled=14):
    """The road to AGI: a track of weekly ticks; the fill moves one week closer at step_t."""
    if a <= 0:
        return
    x0, x1 = 410, 1510
    w = x1 - x0
    c.drawRRect(rr(x0, y - 5, w, 10, 5), G.P("#1d1d22", a))
    for k in range(weeks + 1):
        x = x0 + w * k / weeks
        c.drawLine(x, y + 16, x, y + 26, G.P("#3a3a42", a, stroke=2))
    u = out_back(clamp((t - step_t) / 0.45), 1.8) if t >= step_t else 0.0
    fw = w * (filled + u) / weeks
    c.drawRRect(rr(x0, y - 5, fw, 10, 5), G.P(WHITE, a, shader=G.linear_grad(x0, 0, x0 + fw, 0,
                                                                          ["#5b5b66", "#ffffff"])))
    c.drawCircle(x0 + fw, y, 9, G.P(WHITE, a))
    c.drawCircle(x0 + fw, y, 26, G.P(WHITE, 0.18 * a, blur=12))
    T(c, "AGI", x1 + 30, y + 9, mono(24, 700), WHITE, a=a, tracking=0.2)
    T(c, "NOW", x0 - 30, y + 9, mono(24, 600), DIM, a=a, align=1.0, tracking=0.2)
    if t >= step_t:
        v = clamp((t - step_t) / 0.35)
        with G.xf(c, x0 + fw, y - 44 - 10 * out_cubic(v)):
            chip(c, 0, 0, "+1 WEEK", WHITE, BLACK, a=v * (1 - clamp((t - step_t - 1.1) / 0.3)), size=18, align=0.5)


def cold_open(c, t):
    ground(c, BLACK)
    blob(c, 960, 520, 820, "#2a3350", 0.35 + 0.1 * math.sin(t * 2))
    stars(c, t, a=0.9)
    # dateline
    k = clamp((t - 0.05) / 0.5)
    date = G.scramble("WEEK OF SEP 28 · 2026", k, seed=3, t=t)
    T(c, date, 120, 130, mono(22, 600), GREY, a=clamp(t / 0.2), tracking=0.28)
    T(c, G.scramble("AI · THIS WEEK", k, seed=4, t=t), 1800, 130, mono(22, 600), GREY, a=clamp(t / 0.2), align=1.0,
      tracking=0.28)
    # the headline, a word a beat
    f = display(150, 760)
    line1 = [OPEN_WORDS[0], OPEN_WORDS[1]]
    line2 = [OPEN_WORDS[2], OPEN_WORDS[3]]
    sp = f.width(" ")
    w1 = sum(f.width(w) for _, w in line1) + sp
    x = 960 - w1 / 2
    for t0, w in line1:
        _word(c, w, x, 440, f, WHITE, t, t0)
        x += f.width(w) + sp
    fa = display(150, 820)
    w2 = sum(f.width(w) for _, w in line2) + sp * 2 + fa.width("AGI.")
    x = 960 - w2 / 2
    for t0, w in line2:
        _word(c, w, x, 610, f, WHITE, t, t0)
        x += f.width(w) + sp
    # AGI. lands on the bar, in light
    if t >= T_AGI - 0.02:
        u = clamp((t - T_AGI) / 0.35)
        punch = 1 + 0.25 * math.exp(-(t - T_AGI) / 0.09)
        run = fa.shape("AGI.")
        with G.xf(c, x + run.width / 2, 560, s=punch):
            path = run.path(-run.width / 2, 50)
            c.drawPath(path, G.P(WHITE, 0.55 * u, blur=30))
            sh = G.linear_grad(-run.width / 2 + 800 * math.sin(t * 0.8) * 0.2, 0, run.width / 2, 0, IRIDESCENT)
            c.drawPath(path, G.P(WHITE, u, shader=sh))
    agi_bar(c, t, 800, T_TICK, a=clamp((t - 0.9) / 0.4))


def _word(c, w, x, y, f, col, t, t0, a=1.0):
    """A word lands: it rises and sharpens."""
    u = clamp((t - t0) / 0.3)
    if u <= 0 or a <= 0:
        return
    e = out_cubic(u)
    run = f.shape(w)
    run.draw(c, x, y + 40 * (1 - e), G.P(col, u * a, blur=10 * (1 - e)))


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
    if key == "anthropic":
        fm = serif(66 * s, 440)
    else:
        fm = display(58 * s, 760)
    mw = fm.width(b["model"])
    if mw > w - 56 * s:
        fm = display(58 * s * (w - 56 * s) / mw, 760) if key != "anthropic" else serif(66 * s * (w - 56 * s) / mw)
    y_model = -h / 2 + 96 * s
    if key == "google":
        path = fm.shape(b["model"]).path(-w / 2 + 30 * s, y_model)
        c.drawPath(path, G.P(WHITE, a, shader=G.linear_grad(-w / 2, 0, w / 2, 0, GEMINI_GRAD)))
    else:
        T(c, b["model"], -w / 2 + 30 * s, y_model, fm, ink, a=a)
    if b.get("model2"):
        T(c, b["model2"], -w / 2 + 32 * s, y_model + 44 * s, ui(28 * s, 600), ink, a=a * 0.7)
    # status chip
    if detail > 0:
        fill = CLAY if key == "anthropic" else (ink if key != "google" else "#1f1f1f")
        chip_ink = WHITE if key in ("anthropic", "google") else top
        with G.xf(c, -w / 2 + 30 * s, -h / 2 + (160 if b.get("model2") else 136) * s, s=s):
            chip(c, 0, 0, b["status"], fill, chip_ink, a=a * detail, size=15)
    # the mark
    msz = 118 * s
    if key == "google":
        half = msz / 2
        M.mark(c, "gemini", 0, 40 * s, msz, a=a, shader=gemini_shader(-half, 40 * s - half, half, 40 * s + half))
    else:
        M.mark(c, b["mark"], 0, 40 * s, msz, b["mark_col"], a)
    # the company
    fc = ui(24 * s, 650)
    T(c, b["company"], -w / 2 + 30 * s, h / 2 - 34 * s, fc, ink, a=a * 0.8)


def stack_pose(i):
    """Where card i settles on the stack: a little offset and turn each."""
    rot = (float(hash01(i, 7)) - 0.5) * 12
    dx = (float(hash01(i, 8)) - 0.5) * 36
    dy = -i * 6
    return 1340 + dx, 560 + dy, rot


def row_pose(key):
    i = ROW_ORDER.index(key)
    n = len(ROW_ORDER)
    w = 236
    gap = 22
    total = n * w + (n - 1) * gap
    x = 960 - total / 2 + w / 2 + i * (w + gap)
    return x, 600, 0.0, w / CARD_W


def slate(c, t):
    ground(c, BLACK)
    blob(c, 1340, 560, 700, "#26263a", 0.35)
    stars(c, t, a=0.5, speed=0.03)
    # headline
    fade = 1 - clamp((t - T_FAN + 0.1) / 0.3)
    if fade > 0:
        lift = 60 * (1 - fade)
        k = clamp((t - T_SLATE - 0.05) / 0.4)
        T(c, "The final week of September", 120, 420 - lift, ui(52, 500), GREY, a=fade * k)
        f2 = display(118, 800)
        _word(c, "is looking", 120, 560 - lift, f2, WHITE, t, T_SLATE + 0.45, a=fade)
        if t >= T_STACKED:
            u = clamp((t - T_STACKED) / 0.3)
            punch = 1 + 0.2 * math.exp(-(t - T_STACKED) / 0.1)
            run = f2.shape("stacked.")
            with G.xf(c, 120 + run.width / 2, 650 - lift, s=punch):
                run.draw(c, -run.width / 2, 40 + 36 * (1 - out_cubic(u)), G.P(WHITE, u * fade))
    # the cards
    fan = in_out_cubic(clamp((t - T_FAN) / 0.45))
    for i, key in enumerate(DROP_ORDER):
        td = T_DROPS[i]
        if t < td - 0.28:
            continue
        sx, sy, srot = stack_pose(i)
        u = clamp((t - (td - 0.28)) / 0.28)
        fall = 1 - out_cubic(u) if u < 1 else 0.0
        land = spring(t - td, 3.0, 0.45) if t >= td else 0.0
        x = sx
        y = sy - 900 * fall
        rot = srot + 20 * fall
        s = 1.0 + 0.04 * (1 - land) if t >= td else 1.08
        if fan > 0:
            rx, ry, rrot, rs = row_pose(key)
            stagger = clamp(fan * 1.25 - ROW_ORDER.index(key) * 0.04)
            x, y = lerp(x, rx, stagger), lerp(y, ry, stagger)
            rot = lerp(rot, rrot, stagger)
            s = lerp(s, rs, stagger)
        with G.xf(c, x, y, rot=rot, s=s):
            brand_card(c, key, CARD_W, CARD_H, t, a=1.0)
    if fan > 0:
        T(c, "THIS WEEK’S SLATE", 960, 290, mono(24, 650), GREY, a=fan, align=0.5, tracking=0.3)


def slate_dive(c, t):
    """The Anthropic card grows to fill the frame; the others fly out."""
    u = in_out_cubic(clamp((t - T_DIVE) / (T_ANT - T_DIVE)))
    ground(c, BLACK)
    for key in ROW_ORDER:
        rx, ry, rrot, rs = row_pose(key)
        if key == "anthropic":
            continue
        dx = (rx - 960) * 2.2 * u
        with G.xf(c, rx + dx, ry, s=rs * (1 + 0.6 * u)):
            brand_card(c, key, CARD_W, CARD_H, t, a=1 - u)
    rx, ry, _, rs = row_pose("anthropic")
    w = lerp(CARD_W * rs, 1920, u)
    h = lerp(CARD_H * rs, 1080, u)
    x = lerp(rx, 960, u)
    y = lerp(ry, 540, u)
    c.drawRRect(rr(x - w / 2, y - h / 2, w, h, lerp(34 * rs, 0, u)), G.P(IVORY))
    with G.xf(c, x, y, s=lerp(rs, 3.0, u)):
        with G.layer(c, alpha=1 - u):
            brand_card(c, "anthropic", CARD_W, CARD_H, t)


# ---------------------------------------------------------------- 3 Anthropic

PICK_ROWS = [("Fable 5.1", "Our most capable model"), ("Opus 5.5", "Deep work, long tasks"),
             ("Sonnet 5.5", "Expected today"), ("Sonnet 5", "Smart, efficient, everyday"),
             ("Haiku 4.5", "Fastest")]
APP = (1060, 200, 760, 540)


def anthropic(c, t):
    ground(c, IVORY)
    blob(c, 1500, 900, 900, "#e8d9c6", 0.6)
    # the spark watermark, turning slowly
    M.mark(c, "claude", 1620, 930, 620, CLAY, 0.07, rot=(t - T_ANT) * 8)
    eyebrow(c, "anthropic", 120, 150, t, T_ANT + 0.05, IVORY_INK, status="EXPECTED TODAY", status_fill=CLAY,
            status_ink=WHITE, dot=WHITE)
    rise_text(c, "Sonnet 5.5", 112, 460, serif(188, 430), IVORY_INK, t, T_ANT + 0.2, stagger=0.04)
    fs = ui(40, 450)
    words = "A big step up from the current model.".split(" ")
    x = 120
    for k, w in enumerate(words):
        u = clamp((t - T_ANT - 0.7 - 0.05 * k) / 0.3)
        if u > 0:
            T(c, w, x, 560 + 20 * (1 - out_cubic(u)), fs, "#3d3a33", a=u)
        x += fs.width(w + " ")
    if t >= T_FABLE:
        rise_text(c, "A Fable moment?", 120, 640, F("fraunces-italic", 60, wght=420, opsz=144, SOFT=0, WONK=1),
                  CLAY, t, T_FABLE, stagger=0.02, dur=0.35)
    claude_app(c, t)
    portrait(c, "amodei", 330, 830, 420, t, T_ANT_FOUNDERS, ring=CLAY, text_col=IVORY_INK, rect_h=250)


def claude_app(c, t):
    x, y, w, h = APP
    u = spring(t - T_ANT - 0.25, 2.2, 0.62) if t >= T_ANT + 0.25 else 0.0
    if u <= 0:
        return
    with G.xf(c, x + w / 2, y + h / 2 + 120 * (1 - u), s=0.94 + 0.06 * u):
        c.translate(-(x + w / 2), -(y + h / 2))
        panel(c, x, y, w, h, 30, WHITE, a=clamp(u * 2), shadow=0.14)
        # top bar
        M.mark(c, "claude", x + 52, y + 50, 30, CLAY)
        T(c, "Claude", x + 78, y + 61, serif(34, 480), IVORY_INK)
        picked = t >= T_PICK
        label = "Sonnet 5.5" if picked else "Sonnet 5"
        fb = ui(24, 600)
        bw = fb.width(label) + 70
        bx = x + w - 40 - bw
        c.drawRRect(rr(bx, y + 28, bw, 46, 14), G.P("#f3f1ea" if not picked else "#fbe9e1"))
        T(c, label, bx + 20, y + 59, fb, IVORY_INK if not picked else CLAY)
        chevron(c, bx + bw - 26, y + 51, 14, IVORY_INK)
        # the greeting and the composer
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
        # the dropdown
        op = clamp((t - T_PICKER) / 0.2) * (1 - clamp((t - T_PICK - 0.15) / 0.2))
        if op > 0:
            mx, my, mw = x + w - 380, y + 88, 340
            mh = 60 + 64 * len(PICK_ROWS)
            e = out_back(op, 1.5)
            with G.xf(c, mx + mw, my, s=0.9 + 0.1 * e):
                c.translate(-(mx + mw), -my)
                panel(c, mx, my, mw, mh, 20, WHITE, a=op, shadow=0.18, rim=("#000000", 0.08))
                T(c, "MODELS", mx + 24, my + 40, mono(16, 700), "#9b978c", a=op, tracking=0.2)
                hover = 2 if t >= T_PICKER + 0.3 else -1
                for k, (name, desc) in enumerate(PICK_ROWS):
                    ry = my + 60 + 64 * k
                    if k == hover:
                        c.drawRRect(rr(mx + 10, ry, mw - 20, 58, 12), G.P("#f5efe7", op))
                    T(c, name, mx + 26, ry + 28, ui(24, 620), IVORY_INK, a=op)
                    T(c, desc, mx + 26, ry + 50, ui(16, 450), "#8e8a80", a=op)
                    if name == "Sonnet 5.5":
                        chip(c, mx + 30 + ui(24, 620).width(name) + 12, ry + 20, "NEW", CLAY, WHITE, a=op, size=13)
    # the cursor comes in, finds the new model, clicks
    if T_ANT + 0.6 <= t < T_OAI - 0.3:
        row = y + 88 + 60 + 64 * 2         # the Sonnet 5.5 row in the menu
        path = [(T_ANT + 0.6, (1900, 1000)), (T_PICKER - 0.05, (x + w - 140, y + 55)),
                (T_PICKER + 0.45, (x + w - 260, row + 30)), (T_PICK + 0.4, (x + w - 250, row + 32)),
                (T_PICK + 1.2, (x + w - 60, y + 480))]
        px, py = _along(path, t)
        cursor(c, px, py, press=press_of(t, [T_PICKER, T_PICK]), clicks=(T_PICKER, T_PICK), t=t,
               a=clamp((t - T_ANT - 0.6) / 0.2) * (1 - clamp((t - T_PICK - 1.0) / 0.3)))


def _along(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
        if t <= t1:
            u = in_out_cubic(clamp((t - t0) / max(1e-6, t1 - t0)))
            return lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)
    return keys[-1][1]
