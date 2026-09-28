"""OpenAI, the race (Gemini and Muse), open source (MiniMax and Qwen) and xAI."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, out_cubic, out_back, spring, hash01
from . import marks as M
from .look import (BRANDS, BLACK, WHITE, GREY, T, ui, display, rr, ground, blob, chip, eyebrow, rise_text, portrait,
                   press_of, panel, chevron, arrow_up, download, roll_digit, gemini_shader, GEMINI_GRAD)
from .score import (T_OAI, T_OAI_TYPE, T_OAI_SEND, T_AGENT, T_OAI_FOUNDER, T_RACE, T_RACE_FOUNDERS, T_OSS, T_OSS_MODELS,
                    T_XAI, T_ROLL, T_XAI_FOUNDER)

OAI_INK = "#0d0d0d"
OAI_SUB = "#6e6e80"


# ---------------------------------------------------------------- 4 OpenAI

def openai(c, t):
    ground(c, "#ffffff", "#f3f3f5")
    blob(c, 1400, 300, 800, "#e9ecf5", 0.8)
    eyebrow(c, "openai", 120, 150, t, T_OAI + 0.05, OAI_INK, status="DEVDAY · TOMORROW", status_fill=OAI_INK,
            status_ink=WHITE, dot=WHITE, mark_col=OAI_INK)
    rise_text(c, "New model", 112, 390, display(150, 780), OAI_INK, t, T_OAI + 0.2, stagger=0.03, tracking=-0.02)
    agent_line(c, t)
    fs = ui(38, 450)
    u = clamp((t - T_OAI - 0.9) / 0.35)
    if u > 0:
        T(c, "Both expected this week.", 120, 640 + 16 * (1 - out_cubic(u)), fs, OAI_SUB, a=u)
    composer(c, t)
    agent_card(c, t)
    portrait(c, "altman", 220, 860, 200, t, T_OAI_FOUNDER, ring=OAI_INK, text_col=OAI_INK, sub_col=OAI_SUB)


def agent_line(c, t):
    t0 = T_OAI + 0.45
    f = display(110, 760)
    s = "+ Agent “O”"
    run = rise_text(c, s, 116, 530, f, OAI_INK, t, t0, stagger=0.03)
    # the O is an agent loop: an arc runs round it
    i = s.index("O", s.index("“"))
    if i < len(run.xs) and t >= t0 + 0.4:
        gx, adv = run.xs[i], run.adv[i]
        cx, cy = 116 + gx + adv / 2, 530 - f.cap / 2
        r = f.cap * 0.72
        a = clamp((t - t0 - 0.4) / 0.3)
        spin = (t - t0) * 300
        c.drawCircle(cx, cy, r, G.P(OAI_INK, 0.12 * a, stroke=6))
        arc = G.arc_path(cx, cy, r, spin, 100)
        c.drawPath(arc, G.P(OAI_INK, a, stroke=6, cap="round",
                            shader=G.linear_grad(cx - r, cy, cx + r, cy, ["#10a37f", "#4f7cff"])))
    return run


def composer(c, t):
    x, y, w, h = 990, 290, 830, 196
    u = spring(t - T_OAI - 0.3, 2.3, 0.62) if t >= T_OAI + 0.3 else 0.0
    if u <= 0:
        return
    with G.xf(c, 0, 90 * (1 - u)):
        panel(c, x, y, w, h, 34, WHITE, a=clamp(u * 2), shadow=0.1, rim=("#000000", 0.1))
        prompt = "What are you launching at DevDay?"
        k = clamp((t - T_OAI_TYPE[0]) / (T_OAI_TYPE[1] - T_OAI_TYPE[0]))
        n = int(len(prompt) * k)
        sent = t >= T_OAI_SEND
        fp = ui(30, 450)
        gone = clamp((t - T_OAI_SEND - 0.1) / 0.2)
        if n == 0 or gone >= 1:
            T(c, "Ask anything", x + 36, y + 64, fp, "#9a9aa6", a=1.0 if n == 0 else gone)
        else:
            T(c, prompt[:n], x + 36, y + 64, fp, OAI_INK, a=1 - gone)
            if not sent and int(t * 3) % 2 == 0:
                cw = fp.width(prompt[:n])
                c.drawRect(skia.Rect.MakeXYWH(x + 38 + cw, y + 36, 3, 38), G.P(OAI_INK))
        # the bottom row
        G.circle(c, x + 56, y + 146, 22, G.P("#000000", 1, stroke=1.4))
        c.drawLine(x + 48, y + 146, x + 64, y + 146, G.P(OAI_INK, 1, stroke=2.4, cap="round"))
        c.drawLine(x + 56, y + 138, x + 56, y + 154, G.P(OAI_INK, 1, stroke=2.4, cap="round"))
        fb = ui(22, 600)
        label = "New model"
        bw = fb.width(label) + 84
        c.drawRRect(rr(x + 94, y + 124, bw, 44, 22), G.P("#f1f1f3"))
        T(c, label, x + 116, y + 154, fb, OAI_INK)
        G.circle(c, x + 116 + fb.width(label) + 20, y + 146, 11, G.P(OAI_INK))
        T(c, "?", x + 116 + fb.width(label) + 20, y + 153, ui(16, 800), WHITE, align=0.5)
        chevron(c, x + 94 + bw - 20, y + 146, 12, OAI_INK)
        pr = press_of(t, [T_OAI_SEND])
        sx, sy = x + w - 60, y + 146
        with G.xf(c, sx, sy, s=1 - 0.12 * pr):
            G.circle(c, 0, 0, 26, G.P(OAI_INK if n > 0 else "#d9d9de"))
            arrow_up(c, 0, 0, 22, WHITE)


def agent_card(c, t):
    if t < T_AGENT:
        return
    x, y, w, h = 990, 526, 830, 250
    u = spring(t - T_AGENT, 2.4, 0.6)
    a = clamp((t - T_AGENT) / 0.2)
    with G.xf(c, 0, 70 * (1 - u)):
        panel(c, x, y, w, h, 30, WHITE, a=a, shadow=0.1, rim=("#000000", 0.1))
        cx, cy = x + 60, y + 62
        G.circle(c, cx, cy, 22, G.P("#0d0d0d", a, stroke=3))
        spin = (t - T_AGENT) * 360
        c.drawPath(G.arc_path(cx, cy, 22, spin, 90), G.P("#10a37f", a, stroke=5, cap="round"))
        T(c, "Agent “O”", x + 100, y + 73, ui(32, 650), OAI_INK, a=a)
        chip(c, x + 100 + ui(32, 650).width("Agent “O”") + 20, y + 62, "RUMOURED", OAI_SUB, WHITE, a=a, size=15)
        dots = "." * (int((t - T_AGENT) * 5) % 4)
        T(c, "Working" + dots, x + w - 170, y + 73, ui(24, 500), OAI_SUB, a=a)
        # skeleton lines with a shimmer running over them
        for k, lw in enumerate((0.86, 0.72, 0.54)):
            ly = y + 120 + 38 * k
            bw = (w - 120) * lw
            c.drawRRect(rr(x + 60, ly, bw, 16, 8), G.P("#ececf0", a))
            sh = ((t - T_AGENT) * 1.3 + k * 0.2) % 1.6 - 0.3
            sx = x + 60 + bw * sh
            with G.clip_rect(c, x + 60, ly, bw, 16):
                c.drawRect(skia.Rect.MakeXYWH(sx - 90, ly, 180, 16),
                           G.P(WHITE, a, shader=G.linear_grad(sx - 90, 0, sx + 90, 0,
                                                              ["#ececf0", "#ffffff", "#ececf0"])))


# ---------------------------------------------------------------- 5 also in the race: Gemini and Muse

def race(c, t):
    # left: Google DeepMind on white; right: Meta in blue
    c.drawRect(skia.Rect.MakeXYWH(0, 0, 960, 1080), G.P("#ffffff"))
    glows = (("#4285f4", 240, 260, 520), ("#9b72cb", 640, 760, 560), ("#d96570", 180, 900, 420))
    for k, (col, x, y, r) in enumerate(glows):
        blob(c, x + 40 * math.sin(t + k), y, r, col, 0.16)
    slide = out_cubic(clamp((t - T_RACE + 0.2) / 0.35))
    rx = 960 + 960 * (1 - slide)
    c.drawRect(skia.Rect.MakeXYWH(rx, 0, 960, 1080), G.P("#1a86ff", 1, shader=G.linear_grad(0, 0, 0, 1080,
                                                                                        ["#1a86ff", "#0048b8"])))
    blob(c, rx + 700, 250, 520, "#6fb6ff", 0.35)
    # the chip across the seam
    u = clamp((t - T_RACE - 0.1) / 0.3)
    if u > 0:
        with G.xf(c, 960, 120, s=0.8 + 0.2 * out_back(u, 2)):
            c.drawRRect(rr(-190, -34 + 8, 380, 68, 34), G.P("#000000", 0.18 * u, blur=14))
            chip(c, 0, 0, "ALSO IN THE RACE", "#111114", WHITE, a=u, size=24, align=0.5)
    _lab(c, t, "google", 480, T_RACE + 0.15, "#1f1f1f", "#5f6368")
    _lab(c, t, "meta", rx + 480, T_RACE + 0.3, WHITE, "#d6e6ff")
    portrait(c, "hassabis", 290, 880, 190, t, T_RACE_FOUNDERS, ring="#4285f4", text_col="#1f1f1f", sub_col="#5f6368")
    portrait(c, "zuckerberg", rx + 290, 880, 190, t, T_RACE_FOUNDERS + 0.12, ring=WHITE, text_col=WHITE,
             sub_col="#d6e6ff")


def _lab(c, t, key, cx, t0, ink, sub):
    b = BRANDS[key]
    u = clamp((t - t0) / 0.5)
    if u <= 0:
        return
    s = spring(t - t0, 2.4, 0.5)
    size = 230
    my = 340
    with G.xf(c, cx, my, s=0.4 + 0.6 * s, rot=-90 * (1 - out_cubic(u))):
        if key == "google":
            M.mark(c, "gemini", 0, 0, size, a=u, shader=gemini_shader(-size / 2, -size / 2, size / 2, size / 2))
        else:
            M.mark(c, "meta", 0, 0, size, WHITE, u)
    fm = display(170, 780)
    v = clamp((t - t0 - 0.25) / 0.4)
    if v > 0:
        run = fm.shape(b["model"])
        y = 650 + 30 * (1 - out_cubic(v))
        path = run.path(cx - run.width / 2, y)
        if key == "google":
            half = run.width / 2
            c.drawPath(path, G.P(WHITE, v, shader=G.linear_grad(cx - half, 0, cx + half, 0, GEMINI_GRAD)))
        else:
            c.drawPath(path, G.P(ink, v))
        T(c, b["company"].upper(), cx, 715, ui(24, 650), sub, a=v, align=0.5, tracking=0.2)


# ---------------------------------------------------------------- 6 open source: MiniMax M3.1 and Qwen 4

def open_source(c, t):
    slide = out_cubic(clamp((t - T_OSS + 0.2) / 0.35))
    lx = -960 * (1 - slide)
    rx = 960 + 960 * (1 - slide)
    _half(c, lx, "minimax", t)
    _half(c, rx, "qwen", t)
    u = clamp((t - T_OSS - 0.05) / 0.3)
    if u > 0:
        with G.xf(c, 960, 140, s=0.8 + 0.2 * out_back(u, 2)):
            c.drawRRect(rr(-150, -34 + 8, 300, 68, 34), G.P("#000000", 0.2 * u, blur=14))
            chip(c, 0, 0, "OPEN SOURCE", WHITE, "#111114", a=u, size=26, align=0.5)
        T(c, "Two major open-weight models", 960, 230 + 12 * (1 - out_cubic(u)), ui(36, 500), WHITE, a=u * 0.92,
          align=0.5)


def _half(c, x0, key, t):
    b = BRANDS[key]
    top, bot = b["bg"]
    c.drawRect(skia.Rect.MakeXYWH(x0, 0, 960, 1080), G.P(top, 1, shader=G.linear_grad(0, 0, 0, 1080, [top, bot])))
    # weights drifting upward
    for i in range(38):
        u = (float(hash01(i, 11 if key == "qwen" else 12)) + (t - T_OSS) * (0.08 + 0.1 * float(hash01(i, 13)))) % 1.0
        px = x0 + 40 + 880 * float(hash01(i, 14 if key == "qwen" else 15))
        py = 1100 - 1180 * u
        sz = 5 + 9 * float(hash01(i, 16))
        c.drawRRect(rr(px, py, sz, sz, 2), G.P(WHITE, 0.18 * math.sin(math.pi * u)))
    cx = x0 + 480
    t0 = T_OSS_MODELS[0 if key == "minimax" else 1]
    u = clamp((t - T_OSS - 0.1) / 0.4)
    if u > 0:
        s = spring(t - T_OSS - 0.1, 2.4, 0.5)
        M.mark(c, b["mark"], cx, 400, 150 * (0.5 + 0.5 * s), WHITE, u)
        T(c, b["company"], cx, 530, ui(34, 650), WHITE, a=u * 0.85, align=0.5)
    v = clamp((t - t0) / 0.35)
    if v > 0:
        punch = 1 + 0.18 * math.exp(-(t - t0) / 0.1)
        run = display(200, 820).shape(b["model"])
        with G.xf(c, cx, 690, s=punch):
            run.draw(c, -run.width / 2, 40 * (1 - out_cubic(v)), G.P(WHITE, v))
        cw = chip(c, cx - 26, 800, "OPEN WEIGHTS", WHITE, WHITE, a=v, outline=True, align=0.5)
        download(c, cx + cw / 2 + 10, 800, 30, WHITE, a=v, bob=4 * math.sin((t - t0) * 8))


# ---------------------------------------------------------------- 7 xAI: Grok 4.8, maybe

def xai(c, t):
    ground(c, BLACK)
    blob(c, 1450, 540, 700, "#1a1a22", 0.8)
    M.mark(c, "grok", 1500, 560, 900, WHITE, 0.05, rot=(t - T_XAI) * 6)
    eyebrow(c, "xai", 120, 150, t, T_XAI + 0.05, WHITE, status="MIGHT DROP THIS WEEK", status_fill=WHITE,
            status_ink=WHITE, outline=True)
    f = display(210, 800)
    t0 = T_XAI + 0.2
    run = rise_text(c, "Grok 4.", 112, 470, f, WHITE, t, t0, stagger=0.035)
    u = clamp((t - t0 - 0.25) / 0.4)
    if u > 0:
        x = 112 + run.width
        if t < T_ROLL:
            T(c, "7", x, 470, f, WHITE, a=u)
        else:
            k = clamp((t - T_ROLL) / 0.35)
            glitch = math.exp(-(t - T_ROLL) / 0.12)
            if glitch > 0.05:
                T(c, "8", x + 14 * glitch, 470, f, "#ff2d55", a=0.6 * glitch)
                T(c, "8", x - 14 * glitch, 470, f, "#2de2ff", a=0.6 * glitch)
            roll_digit(c, "7", "8", k, x, 470, f, WHITE)
    v = clamp((t - T_ROLL - 0.25) / 0.35)
    if v > 0:
        T(c, "Expected after 4.7’s rough reviews.", 120, 560 + 14 * (1 - out_cubic(v)), ui(38, 450), GREY, a=v)
    grok_composer(c, t)
    portrait(c, "musk", 220, 860, 200, t, T_XAI_FOUNDER, ring=WHITE, text_col=WHITE, sub_col=GREY)


def grok_composer(c, t):
    u = spring(t - T_XAI - 0.35, 2.3, 0.62) if t >= T_XAI + 0.35 else 0.0
    if u <= 0:
        return
    cx = 1405
    with G.xf(c, 0, 80 * (1 - u)):
        a = clamp(u * 2)
        M.mark(c, "grok", cx - 90, 330, 64, WHITE, a)
        T(c, "Grok", cx - 44, 352, display(64, 560), WHITE, a=a)
        x, y, w, h = 990, 420, 830, 104
        c.drawRRect(rr(x, y, w, h, h / 2), G.P("#141416", a))
        c.drawRRect(rr(x, y, w, h, h / 2), G.P("#2c2c31", a, stroke=1.6))
        prompt = "Is 4.8 dropping this week?"
        k = clamp((t - T_XAI - 0.9) / 1.0)
        n = int(len(prompt) * k)
        fp = ui(28, 450)
        if n == 0:
            T(c, "What do you want to know?", x + 44, y + 62, fp, "#6c6c74", a=a)
        else:
            T(c, prompt[:n], x + 44, y + 62, fp, WHITE, a=a)
        fb = ui(22, 600)
        c.drawRRect(rr(x + w - 230, y + 30, 110, 44, 22), G.P("#232327", a))
        T(c, "Auto", x + w - 208, y + 60, fb, WHITE, a=a)
        chevron(c, x + w - 138, y + 52, 11, WHITE, a=a)
        G.circle(c, x + w - 58, y + 52, 26, G.P(WHITE, a))
        arrow_up(c, x + w - 58, y + 52, 22, "#0b0b0c", a=a)
